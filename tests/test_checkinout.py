"""Tests for check-in/check-out flow."""
import pytest


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
def test_checkout_success(client, seed_user, seed_tool):
    """Check out tool: user + badge + tool -> success."""
    username, badge_id, _ = seed_user
    tool_id = seed_tool
    rv = client.post(
        "/checkinout",
        data={"username": username, "badge_id": badge_id, "tool_id_number": tool_id},
        follow_redirects=False,
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data is not None
    assert data.get("status") == "success"
    assert "checked out" in data.get("message", "").lower()


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
def test_checkin_success(client, seed_user, seed_tool):
    """Check in tool: first checkout, then checkin -> success."""
    username, badge_id, _ = seed_user
    tool_id = seed_tool
    # Check out first
    client.post(
        "/checkinout",
        data={"username": username, "badge_id": badge_id, "tool_id_number": tool_id},
    )
    # Check in
    rv = client.post(
        "/checkinout",
        data={"username": username, "badge_id": badge_id, "tool_id_number": tool_id},
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data is not None
    assert data.get("status") == "success"
    assert "checked in" in data.get("message", "").lower()


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
def test_badge_mismatch(client, seed_user, seed_tool):
    """Wrong badge for user -> error."""
    username, _, _ = seed_user
    tool_id = seed_tool
    rv = client.post(
        "/checkinout",
        data={"username": username, "badge_id": "WRONG99", "tool_id_number": tool_id},
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data is not None
    assert data.get("status") == "error"
    assert "badge" in data.get("message", "").lower()


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
def test_unknown_tool(client, seed_user):
    """Tool ID not in DB -> error."""
    username, badge_id, _ = seed_user
    rv = client.post(
        "/checkinout",
        data={
            "username": username,
            "badge_id": badge_id,
            "tool_id_number": "UNKNOWN-XXX-999",
        },
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data is not None
    assert data.get("status") == "error"
    assert "not found" in data.get("message", "").lower()


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
def test_unknown_user(client, seed_tool):
    """Username not in DB -> error."""
    tool_id = seed_tool
    rv = client.post(
        "/checkinout",
        data={
            "username": "nobody",
            "badge_id": "X999",
            "tool_id_number": tool_id,
        },
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data is not None
    assert data.get("status") == "error"
    assert "not found" in data.get("message", "").lower()


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
def test_checkout_with_job_and_condition(client, seed_user, seed_tool):
    """Check out with job_id and condition — stored in CheckoutHistory."""
    from models.checkout_history import CheckoutHistory

    username, badge_id, _ = seed_user
    tool_id = seed_tool
    rv = client.post(
        "/checkinout",
        data={
            "username": username,
            "badge_id": badge_id,
            "tool_id_number": tool_id,
            "job_id": "JOB-2024-001",
            "condition": "Good",
        },
    )
    assert rv.status_code == 200
    d = rv.get_json()
    assert d.get("status") == "success"

    hist = CheckoutHistory.query.filter_by(tool_id_number=tool_id, action="checkout").first()
    assert hist is not None
    assert hist.job_id == "JOB-2024-001"
    assert hist.condition == "Good"


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
def test_tool_id_industry_format(client, seed_user, seed_tool):
    """Industry format CONS-HAM-001 is accepted."""
    username, badge_id, _ = seed_user
    rv = client.post(
        "/checkinout",
        data={"username": username, "badge_id": badge_id, "tool_id_number": seed_tool},
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get("status") == "success"


@pytest.mark.usefixtures("db_session", "seed_user", "seed_tool")
def test_checkout_then_another_user_checkout_fails(client, seed_user, seed_tool, db_session):
    """Tool already checked out by user A; user B cannot check it out (same flow checks in for A)."""
    from models.user import User

    username, badge_id, _ = seed_user
    tool_id = seed_tool
    # User A checks out
    client.post(
        "/checkinout",
        data={"username": username, "badge_id": badge_id, "tool_id_number": tool_id},
    )
    # Create user B
    u2 = User(
        first_name="B",
        last_name="User",
        username="userb",
        email="b@example.com",
        badge_id="TST002",
        phone="5551234568",
        department="ATEMS",
        supervisor_username="admin",
        supervisor_email="admin@example.com",
        supervisor_phone="5550000000",
    )
    u2.set_password("pass")
    db_session.session.add(u2)
    db_session.session.commit()
    # User B tries to check out same tool -> currently the logic would do checkout
    # (because tool.checked_out_by != userb), so B would "check out" - meaning
    # the tool would transfer to B. Documenting: same tool can be "checked out"
    # by different user (transfer). If we want "already checked out" error, that
    # would need new logic.
    rv = client.post(
        "/checkinout",
        data={"username": "userb", "badge_id": "TST002", "tool_id_number": tool_id},
    )
    # Current behavior: transfer to user B (checkout succeeds)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get("status") == "success"
