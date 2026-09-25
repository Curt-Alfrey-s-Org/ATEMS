"""
Tests for the deferred items from review 2026-09-25:
- POST /api/system/run-tests (full suite, up to 10 min) is admin-only
- scripts/deploy-to-server.sh stops on frontend build / rsync errors
- deploy_atems_postgres.sh step 3 fails when the migration fails
"""
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

import routes
from extensions import db
from models.user import User

REPO_ROOT = Path(__file__).resolve().parent.parent
BASH = shutil.which("bash")


# ---------------------------------------------------------------------------
# /api/system/run-tests is admin-only
# ---------------------------------------------------------------------------

def _make_admin(username="boss", password="Adm1n-Test-Passphrase"):
    u = User(
        first_name="Boss",
        last_name="Test",
        username=username,
        email=f"{username}@example.com",
        badge_id="ADM1",
        phone="5550000001",
        department="ATEMS",
        supervisor_username="admin",
        supervisor_email="admin@example.com",
        supervisor_phone="5550000000",
        role="admin",
    )
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return username, password


@pytest.fixture
def no_env_users(monkeypatch):
    for var in ("ADMIN_USERNAME", "ADMIN_PASSWORD", "USER_USERNAME", "USER_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(routes, "_ENV_USERS", {})
    monkeypatch.setattr(routes, "_ENV_USERS_LOADED", False)


@pytest.fixture
def fake_suite(monkeypatch):
    """Replace the real (slow) full-suite runner and record calls."""
    import selftest.system

    calls = []

    def _fake_run_full_selftest(app=None):
        calls.append(app)
        return {"success": True, "total": 1, "passed": 1, "failed": 0, "warnings": 0}

    monkeypatch.setattr(selftest.system, "run_full_selftest", _fake_run_full_selftest)
    return calls


def test_run_tests_anonymous_rejected(client, db_session, fake_suite):
    r = client.post("/api/system/run-tests", json={})
    assert r.status_code in (302, 401)
    assert fake_suite == []


def test_run_tests_non_admin_forbidden(client, db_session, seed_user, no_env_users, fake_suite):
    username, _, password = seed_user
    client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
    r = client.post("/api/system/run-tests", json={})
    assert r.status_code == 403
    data = r.get_json()
    assert data["success"] is False
    assert "admin" in data["error"].lower()
    assert fake_suite == [], "full suite must not start for non-admins"


def test_run_tests_admin_allowed(client, db_session, no_env_users, fake_suite):
    username, password = _make_admin()
    client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
    r = client.post("/api/system/run-tests", json={})
    assert r.status_code == 200
    assert r.get_json()["success"] is True
    assert len(fake_suite) == 1


def test_selftest_page_disables_run_button_for_non_admin(client, db_session, seed_user, no_env_users):
    username, _, password = seed_user
    client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
    html = client.get("/selftest").get_data(as_text=True)
    assert 'id="run-tests-btn"' in html
    assert "Only administrators can run the full test suite." in html


def test_selftest_page_enables_run_button_for_admin(client, db_session, no_env_users):
    username, password = _make_admin()
    client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
    html = client.get("/selftest").get_data(as_text=True)
    assert 'id="run-tests-btn"' in html
    assert "Only administrators can run the full test suite." not in html


# ---------------------------------------------------------------------------
# Deploy scripts: run them against fake npm / rsync / docker binaries
# ---------------------------------------------------------------------------

pytestmark_bash = pytest.mark.skipif(BASH is None, reason="bash not available")


def _write_exe(path: Path, body: str):
    path.write_text("#!/bin/bash\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _base_path_env(bin_dir: Path):
    # Keep coreutils etc. but put the fakes first.
    env = {k: v for k, v in os.environ.items() if not k.startswith(("ADMIN_", "POSTGRES_"))}
    env["PATH"] = f"{bin_dir}{os.pathsep}/usr/bin{os.pathsep}/bin"
    return env


@pytest.fixture
def deploy_to_server_tree(tmp_path):
    root = tmp_path / "app"
    (root / "scripts").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "scripts" / "deploy-to-server.sh", root / "scripts" / "deploy-to-server.sh")
    (root / "frontend").mkdir()
    (root / "frontend" / "package.json").write_text("{}\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    return root, bin_dir


def _run_deploy_to_server(root, bin_dir, *args, extra_env=None):
    env = _base_path_env(bin_dir)
    env.update(extra_env or {})
    return subprocess.run(
        [BASH, str(root / "scripts" / "deploy-to-server.sh"), *args],
        cwd=root, env=env, capture_output=True, text=True, timeout=60,
    )


@pytestmark_bash
def test_deploy_to_server_stops_when_frontend_build_fails(deploy_to_server_tree):
    root, bin_dir = deploy_to_server_tree
    _write_exe(bin_dir / "npm", 'if [ "$1" = "run" ]; then echo "vite: boom" >&2; exit 2; fi\nexit 0\n')
    _write_exe(bin_dir / "rsync", 'echo RSYNC_CALLED; exit 0\n')
    r = _run_deploy_to_server(root, bin_dir, "user@host")
    assert r.returncode != 0
    assert "vite: boom" in r.stderr, "npm error output must not be hidden"
    assert "frontend build failed" in r.stderr.lower()
    assert "RSYNC_CALLED" not in r.stdout, "must not sync after a failed build"


@pytestmark_bash
def test_deploy_to_server_stops_when_npm_missing(deploy_to_server_tree):
    root, bin_dir = deploy_to_server_tree
    # PATH with only the utilities the script needs, so no npm can be found.
    for tool in ("dirname",):
        (bin_dir / tool).symlink_to(shutil.which(tool))
    r = _run_deploy_to_server(root, bin_dir, extra_env={"PATH": str(bin_dir)})
    assert r.returncode != 0
    assert "npm is not installed" in r.stderr


@pytestmark_bash
def test_deploy_to_server_skip_frontend_build_opt_in(deploy_to_server_tree):
    root, bin_dir = deploy_to_server_tree
    r = _run_deploy_to_server(root, bin_dir, extra_env={"SKIP_FRONTEND_BUILD": "1"})
    assert r.returncode == 0, r.stderr
    assert "skipping frontend build" in r.stdout


@pytestmark_bash
def test_deploy_to_server_propagates_rsync_failure(deploy_to_server_tree):
    root, bin_dir = deploy_to_server_tree
    _write_exe(bin_dir / "npm", "exit 0\n")
    _write_exe(bin_dir / "rsync", 'echo "rsync: connection refused" >&2; exit 23\n')
    r = _run_deploy_to_server(root, bin_dir, "user@host")
    assert r.returncode == 23
    assert "rsync: connection refused" in r.stderr, "rsync error output must not be hidden"
    assert "Next on server" not in r.stdout


@pytestmark_bash
def test_deploy_to_server_success(deploy_to_server_tree):
    root, bin_dir = deploy_to_server_tree
    _write_exe(bin_dir / "npm", "exit 0\n")
    _write_exe(bin_dir / "rsync", "exit 0\n")
    r = _run_deploy_to_server(root, bin_dir, "user@host")
    assert r.returncode == 0, r.stderr
    assert "Next on server" in r.stdout


# Fake `docker`: `docker compose version` succeeds; `compose ... exec ... python -`
# exits with $FAKE_DB_STATE; `flask db upgrade` exits with $FAKE_UPGRADE_RC; every
# call is logged to $FAKE_DOCKER_LOG.
FAKE_DOCKER = r'''
echo "$*" >> "$FAKE_DOCKER_LOG"
case "$*" in
  *" exec "*" python -"*) cat >/dev/null; exit "${FAKE_DB_STATE:-0}" ;;
  *"flask db upgrade"*) exit "${FAKE_UPGRADE_RC:-0}" ;;
  *"flask db stamp head"*) exit "${FAKE_STAMP_RC:-0}" ;;
esac
exit 0
'''


@pytest.fixture
def postgres_deploy_tree(tmp_path):
    root = tmp_path / "app"
    (root / "scripts").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "deploy_atems_postgres.sh", root / "deploy_atems_postgres.sh")
    shutil.copy(REPO_ROOT / "scripts" / "export_compose_uid_gid.sh", root / "scripts" / "export_compose_uid_gid.sh")
    # Throwaway placeholder env file so the script does not prompt.
    (root / ".env").write_text("PLACEHOLDER_ONLY=1\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_exe(bin_dir / "docker", FAKE_DOCKER)
    return root, bin_dir, tmp_path / "docker.log"


def _run_postgres_deploy(root, bin_dir, log, **fake):
    env = _base_path_env(bin_dir)
    env["FAKE_DOCKER_LOG"] = str(log)
    env["ALFA_AI_ROOT"] = str(root / "no-such-alfa-ai")
    env.update({k: str(v) for k, v in fake.items()})
    r = subprocess.run(
        [BASH, str(root / "deploy_atems_postgres.sh")],
        cwd=root, env=env, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
    )
    calls = log.read_text() if log.exists() else ""
    return r, calls


@pytestmark_bash
def test_postgres_deploy_fails_on_failed_migration(postgres_deploy_tree):
    root, bin_dir, log = postgres_deploy_tree
    r, calls = _run_postgres_deploy(root, bin_dir, log, FAKE_UPGRADE_RC=1)
    assert r.returncode != 0
    assert "migration" in r.stdout.lower() and "failed" in r.stdout.lower()
    assert "Deployment Complete" not in r.stdout
    assert "FLASK_APP=atems:app" in calls


@pytestmark_bash
def test_postgres_deploy_succeeds_when_migration_succeeds(postgres_deploy_tree):
    root, bin_dir, log = postgres_deploy_tree
    r, calls = _run_postgres_deploy(root, bin_dir, log)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "flask db upgrade" in calls
    assert "flask db stamp" not in calls
    assert "Deployment Complete" in r.stdout


@pytestmark_bash
def test_postgres_deploy_stamps_fresh_create_all_schema(postgres_deploy_tree):
    root, bin_dir, log = postgres_deploy_tree
    r, calls = _run_postgres_deploy(root, bin_dir, log, FAKE_DB_STATE=10)
    assert r.returncode == 0, r.stdout + r.stderr
    assert calls.index("flask db stamp head") < calls.index("flask db upgrade")


@pytestmark_bash
def test_postgres_deploy_refuses_unversioned_mismatched_schema(postgres_deploy_tree):
    root, bin_dir, log = postgres_deploy_tree
    r, calls = _run_postgres_deploy(root, bin_dir, log, FAKE_DB_STATE=2)
    assert r.returncode != 0
    assert "flask db upgrade" not in calls
    assert "flask db stamp" not in calls
    assert "Deployment Complete" not in r.stdout


@pytestmark_bash
def test_postgres_deploy_fails_when_stamp_fails(postgres_deploy_tree):
    root, bin_dir, log = postgres_deploy_tree
    r, calls = _run_postgres_deploy(root, bin_dir, log, FAKE_DB_STATE=10, FAKE_STAMP_RC=1)
    assert r.returncode != 0
    assert "flask db upgrade" not in calls
