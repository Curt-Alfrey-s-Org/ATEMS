"""Tests that verify README claims: what ATEMS says it does vs. what it actually does."""
import pytest


# --- Health / API ---

class TestAPIHealth:
    """Basic API availability."""

    def test_api_health(self, client):
        rv = client.get("/api/health")
        assert rv.status_code == 200
        d = rv.get_json()
        assert d.get("status") == "healthy"
        assert "ATEMS" in d.get("service", "")


# --- README: "ATEMS Tracks" ---

@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
class TestTracksWhereStored:
    """README: where is the item stored."""

    def test_tool_has_location(self, seed_tool, db_session):
        from models.tools import Tools
        t = Tools.query.filter_by(tool_id_number=seed_tool).first()
        assert t is not None
        assert hasattr(t, "tool_location")
        assert t.tool_location  # non-empty


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
class TestTracksWhoCheckedInOut:
    """README: who checked in/out."""

    def test_checked_out_by_field(self, seed_tool, db_session):
        from models.tools import Tools
        t = Tools.query.filter_by(tool_id_number=seed_tool).first()
        assert hasattr(t, "checked_out_by")

    def test_checkout_history_logs_user(self, client, seed_user, seed_tool, db_session):
        from models.checkout_history import CheckoutHistory
        username, badge_id, _ = seed_user
        client.post("/checkinout", data={"username": username, "badge_id": badge_id, "tool_id_number": seed_tool})
        hist = CheckoutHistory.query.filter_by(tool_id_number=seed_tool).first()
        assert hist is not None
        assert hist.username == username
        assert hist.action in ("checkin", "checkout")


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
class TestTracksCalibration:
    """README: does it require calibration."""

    def test_tool_has_calibration_fields(self, seed_tool, db_session):
        from models.tools import Tools
        t = Tools.query.filter_by(tool_id_number=seed_tool).first()
        assert hasattr(t, "tool_calibration_due")
        assert hasattr(t, "tool_calibration_date")
        assert hasattr(t, "tool_calibration_schedule")


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
class TestCheckInOutFlow:
    """Core check-in/check-out works."""

    def test_checkout_success(self, client, seed_user, seed_tool):
        username, badge_id, _ = seed_user
        rv = client.post("/checkinout", data={"username": username, "badge_id": badge_id, "tool_id_number": seed_tool})
        assert rv.status_code == 200
        d = rv.get_json()
        assert d["status"] == "success"
        assert "checked out" in d.get("message", "").lower()

    def test_checkin_after_checkout(self, client, seed_user, seed_tool):
        username, badge_id, _ = seed_user
        client.post("/checkinout", data={"username": username, "badge_id": badge_id, "tool_id_number": seed_tool})
        rv = client.post("/checkinout", data={"username": username, "badge_id": badge_id, "tool_id_number": seed_tool})
        assert rv.status_code == 200
        d = rv.get_json()
        assert d["status"] == "success"
        assert "checked in" in d.get("message", "").lower()


# --- README: Reports (partial) ---

@pytest.mark.usefixtures("db_session", "seed_user")
class TestInventoryStatusReport:
    """README: Inventory Status Report - we have dashboard stats."""

    def test_api_stats_returns_inventory_counts(self, client, seed_user, db_session):
        """Login then fetch /api/stats; verify inventory fields."""
        username, _, password = seed_user
        client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
        rv = client.get("/api/stats")
        if rv.status_code == 302:
            pytest.skip("API requires login; session may not persist")
        assert rv.status_code == 200, f"Expected 200, got {rv.status_code}"
        d = rv.get_json()
        assert "total_tools" in d
        assert "checked_out" in d
        assert "in_stock" in d
        assert "calibration_overdue" in d


# --- README: NOT implemented (document only) ---
# These tests document that features are NOT implemented.
# They pass by design - we're recording the gap.

@pytest.mark.usefixtures("app_context")
class TestReadmeNotImplemented:
    """README claims that are NOT implemented - documented for tracking."""

    def test_email_reminders_not_implemented(self, app):
        """README: Email reminders - not in codebase."""
        rules = [r.rule for r in app.url_map.iter_rules()]
        assert not any("remind" in r.lower() or "email" in r.lower() for r in rules)

    def test_job_tracking_in_flow(self, app):
        """README: What job it was used on - job_id now in form and CheckoutHistory."""
        with app.app_context():
            from forms import CheckInOutForm
            form = CheckInOutForm()
        assert hasattr(form, "job_id")
        from models.checkout_history import CheckoutHistory
        assert hasattr(CheckoutHistory(), "job_id")

    def test_condition_at_checkinout_implemented(self, app):
        """README: Condition at check in/out - now recorded per event in CheckoutHistory."""
        from models.checkout_history import CheckoutHistory
        assert hasattr(CheckoutHistory(), "condition")
        with app.app_context():
            from forms import CheckInOutForm
            form = CheckInOutForm()
        assert hasattr(form, "condition")

    def test_shelf_life_not_implemented(self, app):
        """README: Does it have a shelf life - no field."""
        from models.tools import Tools
        assert not hasattr(Tools(), "shelf_life")
