"""
Access-control tests for Flask-Admin (/admin) and login hardening
(security review 2026-09-25, findings #1 and #2).
"""
import pytest

import routes
from extensions import db
from models.user import User

ADMIN_URLS = [
    "/admin/",
    "/admin/user/",
    "/admin/user/new/",
    "/admin/tools/",
    "/admin/tools/new/",
    "/admin/checkouthistory/",
    "/admin/checkin/",
    "/admin/checkout/",
    "/admin/notify/",
]


def _make_user(username, password, role="user", badge="B0"):
    u = User(
        first_name=username.capitalize(),
        last_name="Test",
        username=username,
        email=f"{username}@example.com",
        badge_id=badge,
        phone=("555" + badge.rjust(7, "0"))[-10:],
        department="ATEMS",
        supervisor_username="admin",
        supervisor_email="admin@example.com",
        supervisor_phone="5550000000",
        role=role,
    )
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def no_env_users(monkeypatch):
    """Start every test with no env-based users loaded."""
    for var in ("ADMIN_USERNAME", "ADMIN_PASSWORD", "USER_USERNAME", "USER_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(routes, "_ENV_USERS", {})
    monkeypatch.setattr(routes, "_ENV_USERS_LOADED", False)
    return monkeypatch


class TestAdminRequiresAdminLogin:
    @pytest.mark.parametrize("url", ADMIN_URLS)
    def test_anonymous_redirected_to_login(self, client, db_session, url):
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 302
        assert "login" in (r.location or "").lower()

    def test_anonymous_cannot_create_user(self, client, db_session):
        r = client.post("/admin/user/new/", data={"username": "intruder", "password": "x"}, follow_redirects=False)
        assert r.status_code == 302
        assert User.query.filter_by(username="intruder").first() is None

    @pytest.mark.parametrize("url", ADMIN_URLS)
    def test_non_admin_redirected(self, client, db_session, seed_user, url):
        username, _, password = seed_user
        client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 302
        assert "dashboard" in (r.location or "").lower()

    @pytest.mark.parametrize("url", ["/admin/user/", "/admin/tools/", "/admin/checkouthistory/", "/admin/user/new/"])
    def test_admin_allowed(self, client, db_session, no_env_users, url):
        _make_user("boss", "Adm1n-Test-Passphrase", role="admin", badge="ADM1")
        client.post("/login", data={"username": "boss", "password": "Adm1n-Test-Passphrase"}, follow_redirects=True)
        r = client.get(url)
        assert r.status_code == 200

    def test_user_form_hides_password_hash(self, client, db_session, no_env_users):
        _make_user("boss", "Adm1n-Test-Passphrase", role="admin", badge="ADM1")
        client.post("/login", data={"username": "boss", "password": "Adm1n-Test-Passphrase"}, follow_redirects=True)
        body = client.get("/admin/user/new/").get_data(as_text=True)
        assert 'name="password"' in body
        assert "password_hash" not in body


class TestNoDefaultCredentials:
    @pytest.mark.parametrize("username,password", [("admin", "admin123"), ("user", "user123")])
    def test_former_defaults_do_not_log_in(self, client, db_session, no_env_users, username, password):
        client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
        assert client.get("/dashboard", follow_redirects=False).status_code == 302
        # and no account was auto-created
        assert User.query.filter_by(username=username).first() is None

    def test_existing_row_with_default_password_is_refused(self, client, db_session, no_env_users):
        _make_user("admin", "admin123", role="admin", badge="ADM1")
        client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
        assert client.get("/dashboard", follow_redirects=False).status_code == 302

    def test_env_admin_login_works(self, client, db_session, no_env_users):
        no_env_users.setenv("ADMIN_USERNAME", "envadmin")
        no_env_users.setenv("ADMIN_PASSWORD", "Env-Adm1n-Test-Passphrase")
        client.post("/login", data={"username": "envadmin", "password": "Env-Adm1n-Test-Passphrase"}, follow_redirects=True)
        assert client.get("/dashboard", follow_redirects=False).status_code == 200
        assert client.get("/admin/user/", follow_redirects=False).status_code == 200

    def test_env_login_with_default_password_ignored(self, client, db_session, no_env_users):
        no_env_users.setenv("ADMIN_USERNAME", "envadmin")
        no_env_users.setenv("ADMIN_PASSWORD", "admin123")
        client.post("/login", data={"username": "envadmin", "password": "admin123"}, follow_redirects=True)
        assert client.get("/dashboard", follow_redirects=False).status_code == 302
        assert User.query.filter_by(username="envadmin").first() is None
