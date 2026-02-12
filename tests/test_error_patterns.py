"""
Error Pattern Tests - ATEMS
Tests for common error patterns found in logs. Ensures errors are caught by selftest.
Error-pattern tests for ATEMS API.
"""
import pytest


class TestFormValidationErrors:
    """Form validation should return 400 with message - logged as warning in routes."""

    @pytest.mark.usefixtures("db_session")
    def test_empty_form_returns_400(self, client):
        """Empty POST to checkinout should return 400 (form validation failed)."""
        r = client.post(
                "/checkinout",
                data={"username": "", "badge_id": "", "tool_id_number": ""},
                content_type="application/x-www-form-urlencoded",
            )
        assert r.status_code == 400
        data = r.get_json()
        assert data is not None
        assert data.get("status") == "error"
        assert "message" in data

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_invalid_tool_id_returns_400(self, client, seed_user):
        """Invalid tool ID format should return 400."""
        username, badge_id, _ = seed_user
        r = client.post(
                "/checkinout",
                data={
                    "username": username,
                    "badge_id": badge_id,
                    "tool_id_number": "",  # empty = invalid
                },
                content_type="application/x-www-form-urlencoded",
            )
        assert r.status_code == 400
        data = r.get_json()
        assert data is not None
        assert data.get("status") == "error"


class TestSystemHealthIntegration:
    """System health / selftest API."""

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_system_health_requires_login(self, client):
        """System health returns 401/302 when not logged in."""
        r = client.get("/api/system/health")
        assert r.status_code in (302, 401)

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_system_health_returns_self_test_when_logged_in(self, client, seed_user):
        """When logged in, GET /api/system/health returns self_test structure."""
        username, _, password = seed_user
        client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
        r = client.get("/api/system/health")
        assert r.status_code == 200
        d = r.get_json()
        assert "self_test" in d
        st = d["self_test"]
        assert "passed" in st
        assert "total" in st
        assert "passed_count" in st
        assert "results" in st
        assert isinstance(st["results"], list)

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_run_tests_requires_login(self, client):
        """POST run-tests returns 401/302 when not logged in."""
        r = client.post("/api/system/run-tests", json={})
        assert r.status_code in (302, 401)


class TestApiErrorResponses:
    """API should return consistent error structure."""

    def test_api_health_structure(self, client):
        """API health returns status, service, version."""
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.get_json()
        assert data.get("status") == "healthy"
        assert data.get("service") == "ATEMS"
        assert "version" in data

    @pytest.mark.usefixtures("db_session", "seed_tool")
    def test_unknown_user_returns_error_message(self, client, seed_tool):
        """Unknown user should return error status and message (not 500)."""
        tool_id = seed_tool
        r = client.post(
                "/checkinout",
                data={
                    "username": "nonexistent_user_xyz",
                    "badge_id": "99999",
                    "tool_id_number": tool_id,
                },
                content_type="application/x-www-form-urlencoded",
            )
        assert r.status_code == 200  # form returns 200 with status=error in body
        data = r.get_json()
        assert data.get("status") == "error"
        assert "not found" in data.get("message", "").lower() or "user" in data.get("message", "").lower()

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_unknown_tool_returns_error_message(self, client, seed_user):
        """Unknown tool should return error status and message."""
        username, badge_id, _ = seed_user
        r = client.post(
                "/checkinout",
                data={
                    "username": username,
                    "badge_id": badge_id,
                    "tool_id_number": "NONEXISTENT-TOOL",
                },
                content_type="application/x-www-form-urlencoded",
            )
        data = r.get_json()
        assert data.get("status") == "error"
        assert "not found" in data.get("message", "").lower() or "tool" in data.get("message", "").lower()


class TestDatabaseErrorHandling:
    """Database errors should be handled (logged, not crash)."""

    @pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
    def test_checkinout_commits_successfully(self, client, seed_user, seed_tool):
        """Successful checkout should not raise; DB commit succeeds."""
        username, badge_id, _ = seed_user
        tool_id = seed_tool
        r = client.post(
                "/checkinout",
                data={
                    "username": username,
                    "badge_id": badge_id,
                    "tool_id_number": tool_id,
                },
                content_type="application/x-www-form-urlencoded",
            )
        assert r.status_code == 200
        data = r.get_json()
        assert data.get("status") == "success"


class TestLogsAndSettings:
    """Logs and Settings pages require login and return valid content."""

    def test_logs_requires_login(self, client):
        """Logs page returns 302 when not logged in."""
        r = client.get("/logs", follow_redirects=False)
        assert r.status_code == 302

    def test_settings_requires_login(self, client):
        """Settings page returns 302 when not logged in."""
        r = client.get("/settings", follow_redirects=False)
        assert r.status_code == 302

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_logs_returns_200_when_logged_in(self, client, seed_user):
        """Logs page returns 200 when logged in."""
        username, _, password = seed_user
        client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
        r = client.get("/logs")
        assert r.status_code == 200
        assert b"Log" in r.data or b"log" in r.data

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_settings_returns_200_when_logged_in(self, client, seed_user):
        """Settings page returns 200 when logged in."""
        username, _, password = seed_user
        client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
        r = client.get("/settings")
        assert r.status_code == 200
        assert b"Settings" in r.data or b"Presets" in r.data

    @pytest.mark.usefixtures("db_session", "seed_user")
    def test_api_logs_returns_json_when_logged_in(self, client, seed_user):
        """API logs returns JSON with logs and count."""
        username, _, password = seed_user
        client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
        r = client.get("/api/logs?limit=10")
        assert r.status_code == 200
        data = r.get_json()
        assert "logs" in data
        assert "count" in data
        assert isinstance(data["logs"], list)
        assert isinstance(data["count"], int)
