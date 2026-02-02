"""Pytest fixtures for ATEMS tests."""
import os
import pytest
from atems import create_app
from extensions import db
from models.user import User
from models.tools import Tools


@pytest.fixture
def app():
    """Create app with test config."""
    os.environ.setdefault(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:////tmp/atems_test.db",
    )
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    return app


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Application context."""
    with app.app_context():
        yield


@pytest.fixture
def db_session(app, app_context):
    """Create tables and yield session; tear down after test."""
    db.drop_all()
    db.create_all()
    yield db
    db.drop_all()


@pytest.fixture
def seed_user(app_context, db_session):
    """Create test user. Returns (username, badge_id, password)."""
    u = User(
        first_name="Test",
        last_name="User",
        username="testuser",
        email="test@example.com",
        badge_id="TST001",
        phone="5551234567",
        department="ATEMS",
        supervisor_username="admin",
        supervisor_email="admin@example.com",
        supervisor_phone="5550000000",
    )
    u.set_password("testpass")
    db.session.add(u)
    db.session.commit()
    return "testuser", "TST001", "testpass"


@pytest.fixture
def seed_tool(app_context, db_session):
    """Create one test tool. Returns tool_id_number."""
    t = Tools(
        tool_id_number="CONS-HAM-001",
        tool_name="Claw Hammer",
        tool_location="A1-01",
        tool_status="In Stock",
        tool_calibration_due="N/A",
        tool_calibration_date="N/A",
        tool_calibration_cert="N/A",
        tool_calibration_schedule="N/A",
    )
    db.session.add(t)
    db.session.commit()
    return "CONS-HAM-001"
