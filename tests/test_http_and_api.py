"""
HTTP and API endpoint tests for ATEMS.
Covers page routes (GET) and REST API endpoints (public and auth-required).
"""
import pytest


class TestHttpPages:
    """HTTP page routes: GET returns expected status and content."""

    def test_index_anonymous_returns_200_splash(self, client):
        """GET / returns 200 with splash/login when not logged in."""
        r = client.get("/", follow_redirects=False)
        assert r.status_code == 200
        assert b"login" in r.data.lower() or b"splash" in r.data.lower() or b"sign" in r.data.lower()

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_index_authenticated_redirects_to_dashboard(self, client, seed_user):
        """GET / redirects to dashboard when logged in."""
        username, _, password = seed_user
        client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
        r = client.get("/", follow_redirects=False)
        assert r.status_code in (200, 302)
        if r.status_code == 302:
            assert "dashboard" in (r.location or "").lower() or (r.location or "").endswith("/dashboard")
        else:
            assert b"dashboard" in r.data.lower() or b"tool" in r.data.lower()

    def test_splash_returns_200(self, client):
        """GET /splash returns 200."""
        r = client.get("/splash")
        assert r.status_code == 200

    def test_login_get_returns_200(self, client):
        """GET /login returns 200."""
        r = client.get("/login")
        assert r.status_code == 200
        assert b"login" in r.data.lower() or b"username" in r.data.lower()

    def test_dashboard_anonymous_redirects_to_login(self, client):
        """GET /dashboard when not logged in returns 302 to login."""
        r = client.get("/dashboard", follow_redirects=False)
        assert r.status_code == 302
        assert "login" in (r.location or "").lower()

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_dashboard_authenticated_returns_200(self, client, seed_user):
        """GET /dashboard when logged in returns 200."""
        username, _, password = seed_user
        client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
        r = client.get("/dashboard")
        assert r.status_code == 200
        assert b"dashboard" in r.data.lower() or b"tool" in r.data.lower()

    def test_checkinout_get_returns_200(self, client):
        """GET /checkinout returns 200 (form page)."""
        r = client.get("/checkinout")
        assert r.status_code == 200
        assert b"check" in r.data.lower() or b"tool" in r.data.lower()

    def test_selftest_anonymous_redirects(self, client):
        """GET /selftest when not logged in redirects."""
        r = client.get("/selftest", follow_redirects=False)
        assert r.status_code == 302

    def test_logs_anonymous_redirects(self, client):
        """GET /logs when not logged in redirects."""
        r = client.get("/logs", follow_redirects=False)
        assert r.status_code == 302

    def test_settings_anonymous_redirects(self, client):
        """GET /settings when not logged in redirects."""
        r = client.get("/settings", follow_redirects=False)
        assert r.status_code == 302

    def test_reports_anonymous_redirects(self, client):
        """GET /reports when not logged in redirects."""
        r = client.get("/reports", follow_redirects=False)
        assert r.status_code == 302

    def test_import_anonymous_redirects(self, client):
        """GET /import when not logged in redirects."""
        r = client.get("/import", follow_redirects=False)
        assert r.status_code == 302

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_reports_authenticated_returns_200(self, client, seed_user):
        """GET /reports when logged in returns 200."""
        username, _, password = seed_user
        client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
        r = client.get("/reports")
        assert r.status_code == 200

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_import_authenticated_returns_200(self, client, seed_user):
        """GET /import when logged in returns 200."""
        username, _, password = seed_user
        client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
        r = client.get("/import")
        assert r.status_code == 200


class TestApiPublic:
    """Public API endpoints (no login required)."""

    def test_api_health_returns_200_and_healthy(self, client):
        """GET /api/health returns 200 with status=healthy."""
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.get_json()
        assert data is not None
        assert data.get("status") == "healthy"
        assert data.get("service") == "ATEMS"

    def test_api_user_by_badge_no_param_returns_200(self, client):
        """GET /api/user-by-badge with no param returns 200, username null."""
        r = client.get("/api/user-by-badge")
        assert r.status_code == 200
        data = r.get_json()
        assert data is not None
        assert "username" in data
        assert data["username"] is None

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_api_user_by_badge_with_badge_returns_username(self, client, seed_user):
        """GET /api/user-by-badge?badge_id=X returns username when user exists."""
        _, badge_id, _ = seed_user
        r = client.get("/api/user-by-badge", query_string={"badge_id": badge_id})
        assert r.status_code == 200
        data = r.get_json()
        assert data is not None
        assert data.get("username") == "testuser"

    @pytest.mark.usefixtures("db_session")
    def test_api_user_by_badge_unknown_returns_null(self, client):
        """GET /api/user-by-badge?badge_id=UNKNOWN returns username null."""
        r = client.get("/api/user-by-badge", query_string={"badge_id": "UNKNOWN99"})
        assert r.status_code == 200
        data = r.get_json()
        assert data is not None
        assert data.get("username") is None


class TestApiAuthRequired:
    """API endpoints that require login (302/401 when anonymous, 200 when auth)."""

    def _login(self, client, seed_user):
        username, _, password = seed_user
        client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

    def test_api_stats_anonymous_redirects(self, client):
        """GET /api/stats when not logged in redirects."""
        r = client.get("/api/stats", follow_redirects=False)
        assert r.status_code == 302

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_api_stats_authenticated_returns_200(self, client, seed_user):
        """GET /api/stats when logged in returns 200 and counts."""
        self._login(client, seed_user)
        r = client.get("/api/stats")
        assert r.status_code == 200
        data = r.get_json()
        assert "total_tools" in data
        assert "checked_out" in data
        assert "in_stock" in data

    def test_api_history_anonymous_redirects(self, client):
        """GET /api/history when not logged in redirects."""
        r = client.get("/api/history", follow_redirects=False)
        assert r.status_code == 302

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_api_history_authenticated_returns_200(self, client, seed_user):
        """GET /api/history when logged in returns 200 and events list."""
        self._login(client, seed_user)
        r = client.get("/api/history")
        assert r.status_code == 200
        data = r.get_json()
        assert "events" in data
        assert isinstance(data["events"], list)

    def test_api_tools_anonymous_redirects(self, client):
        """GET /api/tools when not logged in redirects."""
        r = client.get("/api/tools", follow_redirects=False)
        assert r.status_code == 302

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_api_tools_authenticated_returns_200(self, client, seed_user):
        """GET /api/tools when logged in returns 200 and tools list."""
        self._login(client, seed_user)
        r = client.get("/api/tools")
        assert r.status_code == 200
        data = r.get_json()
        assert "tools" in data
        assert isinstance(data["tools"], list)

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_api_reports_usage_authenticated_returns_200(self, client, seed_user):
        """GET /api/reports/usage when logged in returns 200."""
        self._login(client, seed_user)
        r = client.get("/api/reports/usage")
        assert r.status_code == 200
        data = r.get_json()
        assert "events" in data
        assert "count" in data

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_api_reports_calibration_authenticated_returns_200(self, client, seed_user):
        """GET /api/reports/calibration when logged in returns 200."""
        self._login(client, seed_user)
        r = client.get("/api/reports/calibration")
        assert r.status_code == 200
        data = r.get_json()
        assert "overdue" in data
        assert "due_soon" in data

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_api_reports_overdue_returns_authenticated_returns_200(self, client, seed_user):
        """GET /api/reports/overdue-returns when logged in returns 200."""
        self._login(client, seed_user)
        r = client.get("/api/reports/overdue-returns")
        assert r.status_code == 200
        data = r.get_json()
        assert "overdue" in data
        assert "count" in data

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_api_reports_inventory_authenticated_returns_200(self, client, seed_user):
        """GET /api/reports/inventory when logged in returns 200."""
        self._login(client, seed_user)
        r = client.get("/api/reports/inventory")
        assert r.status_code == 200
        data = r.get_json()
        assert "total" in data
        assert "by_category" in data

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_api_calibration_reminders_status_authenticated_returns_200(self, client, seed_user):
        """GET /api/calibration-reminders/status when logged in returns 200."""
        self._login(client, seed_user)
        r = client.get("/api/calibration-reminders/status")
        assert r.status_code == 200
        data = r.get_json()
        assert "mail_configured" in data
        assert "overdue_count" in data


class TestApiCheckinoutJson:
    """POST /api/checkinout (JSON API for scan-gun/mobile)."""

    @pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
    def test_api_checkinout_json_checkout_success(self, client, seed_user, seed_tool):
        """POST /api/checkinout with valid JSON checkout returns 200 and success."""
        username, badge_id, _ = seed_user
        tool_id = seed_tool
        r = client.post(
            "/api/checkinout",
            json={
                "username": username,
                "badge_id": badge_id,
                "tool_id_number": tool_id,
            },
            content_type="application/json",
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data.get("status") == "success"
        assert "checked out" in (data.get("message") or "").lower()
        assert data.get("action") == "checkout"

    @pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
    def test_api_checkinout_json_checkin_success(self, client, seed_user, seed_tool):
        """POST /api/checkinout with valid JSON checkin (after checkout) returns 200."""
        username, badge_id, _ = seed_user
        tool_id = seed_tool
        client.post(
            "/api/checkinout",
            json={"username": username, "badge_id": badge_id, "tool_id_number": tool_id},
            content_type="application/json",
        )
        r = client.post(
            "/api/checkinout",
            json={"username": username, "badge_id": badge_id, "tool_id_number": tool_id},
            content_type="application/json",
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data.get("status") == "success"
        assert "checked in" in (data.get("message") or "").lower()
        assert data.get("action") == "checkin"

    @pytest.mark.usefixtures("db_session")
    def test_api_checkinout_json_empty_returns_400(self, client):
        """POST /api/checkinout with empty/invalid JSON returns 400."""
        r = client.post(
            "/api/checkinout",
            json={},
            content_type="application/json",
        )
        assert r.status_code == 400
        data = r.get_json()
        assert data is not None
        assert data.get("status") == "error"
        assert "message" in data

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_api_checkinout_json_missing_tool_returns_400(self, client, seed_user):
        """POST /api/checkinout with missing tool_id_number returns 400."""
        username, badge_id, _ = seed_user
        r = client.post(
            "/api/checkinout",
            json={"username": username, "badge_id": badge_id, "tool_id_number": ""},
            content_type="application/json",
        )
        assert r.status_code == 400
        data = r.get_json()
        assert data.get("status") == "error"
