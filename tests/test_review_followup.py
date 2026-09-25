"""
Tests for the 2026-09-25 review follow-up (Medium/Low findings):
- open redirect via /login?next=...
- /api/user-by-badge requires login
- /api/checkinout requires login, is JSON-only (CSRF) and works with CSRF enabled
- selftest run-tests fallback never touches the live database
"""
import pytest

import routes
from routes import _safe_next_url


# ---------------------------------------------------------------------------
# Open redirect: only same-site relative paths are accepted for `next`
# ---------------------------------------------------------------------------

UNSAFE_NEXT = [
    "https://evil.example",
    "http://evil.example/dashboard",
    "//evil.example",
    "//evil.example/dashboard",
    "///evil.example",
    "/\\evil.example",
    "\\\\evil.example",
    "\\/evil.example",
    "/\t/evil.example",
    "/\n/evil.example",
    " //evil.example",
    "javascript:alert(1)",
    "evil.example",
    "dashboard",
    "https:/evil.example",
    "",
    None,
]

SAFE_NEXT = ["/dashboard", "/reports?type=usage&x=1", "/atems/app/tools", "/"]


@pytest.mark.parametrize("target", UNSAFE_NEXT)
def test_safe_next_url_rejects_offsite(target):
    assert _safe_next_url(target) is None


@pytest.mark.parametrize("target", SAFE_NEXT)
def test_safe_next_url_allows_relative_paths(target):
    assert _safe_next_url(target) == target


@pytest.mark.usefixtures("db_session", "seed_user")
@pytest.mark.parametrize("target", [t for t in UNSAFE_NEXT if t])
def test_db_login_ignores_offsite_next(client, seed_user, target):
    username, _, password = seed_user
    r = client.post(
        "/login",
        query_string={"next": target},
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert r.location == "/dashboard"


@pytest.mark.usefixtures("db_session", "seed_user")
def test_db_login_keeps_relative_next(client, seed_user):
    username, _, password = seed_user
    r = client.post(
        "/login",
        query_string={"next": "/reports?type=usage"},
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert r.location == "/reports?type=usage"


@pytest.fixture
def env_admin(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "envadmin")
    monkeypatch.setenv("ADMIN_PASSWORD", "Env-Admin-Test-Passphrase-1")
    monkeypatch.setattr(routes, "_ENV_USERS_LOADED", False)
    yield "envadmin", "Env-Admin-Test-Passphrase-1"
    routes._ENV_USERS_LOADED = False


@pytest.mark.usefixtures("db_session")
@pytest.mark.parametrize("target", ["https://evil.example", "//evil.example", "/\\evil.example"])
def test_env_login_ignores_offsite_next(client, env_admin, target):
    username, password = env_admin
    r = client.post(
        "/login",
        query_string={"next": target},
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert r.location == "/dashboard"


@pytest.mark.usefixtures("db_session")
def test_env_login_keeps_relative_next(client, env_admin):
    username, password = env_admin
    r = client.post(
        "/login",
        query_string={"next": "/settings"},
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert r.location == "/settings"


# ---------------------------------------------------------------------------
# Endpoint auth
# ---------------------------------------------------------------------------

def _login(client, seed_user):
    username, _, password = seed_user
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code == 302


@pytest.mark.usefixtures("db_session", "seed_user")
def test_user_by_badge_anonymous_does_not_leak_username(client, seed_user):
    _, badge_id, _ = seed_user
    r = client.get("/api/user-by-badge", query_string={"badge_id": badge_id}, follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.location
    assert b"testuser" not in r.data


@pytest.mark.usefixtures("db_session", "seed_user")
def test_user_by_badge_logged_in_returns_username(client, seed_user):
    _login(client, seed_user)
    _, badge_id, _ = seed_user
    r = client.get("/api/user-by-badge", query_string={"badge_id": badge_id})
    assert r.status_code == 200
    assert r.get_json() == {"username": "testuser"}


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
def test_api_checkinout_anonymous_rejected(client, seed_user, seed_tool):
    username, badge_id, _ = seed_user
    r = client.post(
        "/api/checkinout",
        json={"username": username, "badge_id": badge_id, "tool_id_number": seed_tool},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "/login" in r.location
    from models.tools import Tools
    assert Tools.query.filter_by(tool_id_number=seed_tool).first().checked_out_by is None


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
@pytest.mark.parametrize("content_type", ["application/x-www-form-urlencoded", "multipart/form-data", "text/plain"])
def test_api_checkinout_rejects_non_json_bodies(client, seed_user, seed_tool, content_type):
    """Cross-site HTML forms can only send these content types; they must be refused (CSRF)."""
    _login(client, seed_user)
    username, badge_id, _ = seed_user
    fields = {"username": username, "badge_id": badge_id, "tool_id_number": seed_tool}
    if content_type == "text/plain":
        r = client.post("/api/checkinout", data='{"username": "x"}', content_type=content_type)
    else:
        r = client.post("/api/checkinout", data=fields, content_type=content_type)
    assert r.status_code == 415
    assert r.get_json()["status"] == "error"
    from models.tools import Tools
    assert Tools.query.filter_by(tool_id_number=seed_tool).first().checked_out_by is None


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
def test_api_checkinout_json_works_with_csrf_enabled(app, client, seed_user, seed_tool):
    """Regression: with Flask-WTF CSRF on (production default) JSON clients used to get 400."""
    app.config["WTF_CSRF_ENABLED"] = True
    _login(client, seed_user)
    username, badge_id, _ = seed_user
    r = client.post(
        "/api/checkinout",
        json={"username": username, "badge_id": badge_id, "tool_id_number": seed_tool,
              "return_by": "2030-01-31", "condition": "Good"},
    )
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert data["status"] == "success"
    assert data["action"] == "checkout"
    from models.checkout_history import CheckoutHistory
    hist = CheckoutHistory.query.filter_by(tool_id_number=seed_tool, action="checkout").first()
    assert hist.return_by is not None and hist.return_by.year == 2030
    assert hist.condition == "Good"


@pytest.mark.usefixtures("db_session", "seed_user")
def test_api_checkinout_rejects_non_object_json(client, seed_user):
    _login(client, seed_user)
    r = client.post("/api/checkinout", json=["not", "an", "object"])
    assert r.status_code == 400
    assert r.get_json()["status"] == "error"


def test_session_cookie_is_samesite_lax(app):
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


# ---------------------------------------------------------------------------
# Self-test: run-tests must never point pytest at the live database
# ---------------------------------------------------------------------------

def test_selftest_subprocess_env_uses_throwaway_sqlite(monkeypatch):
    from selftest.system import _selftest_subprocess_env
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "postgresql://live-db-host/atems")
    monkeypatch.setenv("ENVIRONMENT", "production")
    env = _selftest_subprocess_env()
    assert env["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///")
    assert "live-db-host" not in env["SQLALCHEMY_DATABASE_URI"]
    assert env["ENVIRONMENT"] == "test"


@pytest.mark.usefixtures("db_session")
def test_run_full_selftest_falls_back_when_suite_missing(app, monkeypatch, tmp_path):
    """In the Docker image tests/ and run_selftest.sh are absent: run startup checks only."""
    import selftest.system as system
    monkeypatch.setattr(system, "PROJECT_ROOT", tmp_path)
    result = system.run_full_selftest(app=app)
    assert result["mode"] == "startup-only"
    assert result["total"] >= 1
    assert "output" in result
