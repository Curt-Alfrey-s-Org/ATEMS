"""
Regression tests for review 2026-09-26 (round 2):
- CSV tool import used a non-existent codec ("utf-8-skip") and always failed
- import_tools_rows reported rolled-back rows as created/updated
- env-created users overflowed user.badge_id (VARCHAR(10)) and reused one phone
- calibration reminder e-mail HTML did not escape tool fields; SMTP had no timeout
- /api/logs read the whole log file per request; log/report pages rendered
  DB/log values with innerHTML (stored XSS)
- dashboard calibration buckets compared raw strings, so MM/DD/YYYY dates landed
  in the wrong bucket
"""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import routes
from extensions import db
from models.tools import Tools
from models.user import User

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def no_env_users(monkeypatch):
    for var in ("ADMIN_USERNAME", "ADMIN_PASSWORD", "USER_USERNAME", "USER_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(routes, "_ENV_USERS", {})
    monkeypatch.setattr(routes, "_ENV_USERS_LOADED", False)
    return monkeypatch


# --- CSV import --------------------------------------------------------------

def test_csv_import_parses():
    from utils.import_tools import parse_and_validate_tools

    valid, errors = parse_and_validate_tools(b"tool_id_number,tool_name\nA-1,Hammer\n", "tools.csv")
    assert errors == []
    assert [r["tool_id_number"] for r in valid] == ["A-1"]


def test_csv_import_strips_excel_bom():
    from utils.import_tools import parse_and_validate_tools

    valid, errors = parse_and_validate_tools("\ufefftool_id_number,tool_name\nA-2,Wrench\n".encode("utf-8"), "t.csv")
    assert errors == []
    assert valid[0]["tool_name"] == "Wrench"


def test_import_tools_endpoint_csv(client, db_session, seed_user):
    import io

    username, _, password = seed_user
    client.post("/login", data={"username": username, "password": password})
    r = client.post(
        "/api/import/tools",
        data={"file": (io.BytesIO(b"tool_id_number,tool_name\nCSV-1,Saw\n"), "tools.csv")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["created"] == 1
    assert Tools.query.filter_by(tool_id_number="CSV-1").first() is not None


def test_import_rows_commit_failure_reports_zero(app_context, db_session, monkeypatch):
    from utils import import_tools

    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(db.session, "commit", boom)
    created, updated, errors = import_tools.import_tools_rows([{
        "tool_id_number": "X-1", "tool_name": "X", "tool_location": "N/A", "tool_status": "In Stock",
        "tool_calibration_due": "N/A", "tool_calibration_date": "N/A",
        "tool_calibration_cert": "N/A", "tool_calibration_schedule": "N/A", "category": None,
    }])
    assert (created, updated) == (0, 0)
    assert any("Commit failed" in e["message"] for e in errors)


# --- env-created users -------------------------------------------------------

def test_env_user_badge_and_phone_fit_columns(client, db_session, no_env_users):
    no_env_users.setenv("ADMIN_USERNAME", "site_administrator")
    no_env_users.setenv("ADMIN_PASSWORD", "Env-Adm1n-Test-Passphrase")
    no_env_users.setenv("USER_USERNAME", "floor_operator")
    no_env_users.setenv("USER_PASSWORD", "Env-Us3r-Test-Passphrase")
    for name, pw in (("site_administrator", "Env-Adm1n-Test-Passphrase"),
                     ("floor_operator", "Env-Us3r-Test-Passphrase")):
        client.post("/login", data={"username": name, "password": pw})
        assert client.get("/dashboard", follow_redirects=False).status_code == 200
        client.get("/logout")
    users = User.query.filter(User.username.in_(["site_administrator", "floor_operator"])).all()
    assert len(users) == 2
    for u in users:
        assert len(u.badge_id) <= 10 and u.badge_id.isalnum()
        assert len(u.phone) == 10 and u.phone.isdigit()
    assert users[0].phone != users[1].phone
    assert users[0].badge_id != users[1].badge_id


# --- calibration reminders ---------------------------------------------------

def test_reminder_html_escapes_tool_fields():
    from utils.calibration_reminders import build_email_body

    row = {"tool_id_number": "T-1", "tool_name": "<script>x</script>", "tool_calibration_due": "2020-01-01"}
    plain, html = build_email_body([row], [], "http://example.test")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<script>x</script>" in plain  # plain text part is not HTML


def test_reminder_smtp_uses_timeout_and_closes(app, app_context, db_session, monkeypatch):
    import smtplib
    from utils import calibration_reminders

    calls = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            calls["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            calls["closed"] = True
            return False

        def starttls(self):
            raise smtplib.SMTPException("tls failed")

    db.session.add(Tools(tool_id_number="CAL-1", tool_name="Gauge", tool_location="A", tool_status="In Stock",
                         tool_calibration_due="2000-01-01", tool_calibration_date="N/A",
                         tool_calibration_cert="N/A", tool_calibration_schedule="N/A"))
    db.session.commit()
    monkeypatch.setenv("MAIL_SERVER", "mail.invalid")
    monkeypatch.setenv("CALIBRATION_REMIND_TO", "ops@example.com")
    monkeypatch.setattr(calibration_reminders.smtplib, "SMTP", FakeSMTP)
    result = calibration_reminders.send_calibration_reminders(app=app)
    assert result["sent"] is False
    assert calls["timeout"] and calls["timeout"] > 0
    assert calls.get("closed") is True


# --- logs / XSS --------------------------------------------------------------

def test_api_logs_returns_tail_only(client, db_session, seed_user, monkeypatch, tmp_path):
    import os

    log = tmp_path / "atems.log"
    log.write_text("".join(f"2026-01-01 00:00:00,000 - x - INFO - line {i}\n" for i in range(5000)))
    real_join = os.path.join

    def fake_join(*parts):
        if parts and parts[-1] == "atems.log":
            return str(log)
        return real_join(*parts)

    monkeypatch.setattr(routes.os.path, "join", fake_join)
    username, _, password = seed_user
    client.post("/login", data={"username": username, "password": password})
    data = client.get("/api/logs?limit=10").get_json()
    assert data["count"] == 10
    assert data["logs"][-1]["message"] == "line 4999"


@pytest.mark.parametrize("template,needle", [
    ("templates/logs.html", "escHtml(log.message)"),
    ("templates/reports.html", "escHtml(e.job_id"),
    ("templates/reports.html", "escHtml(e.username"),
    ("templates/import.html", "escHtml(r.tool_name"),
])
def test_templates_escape_dynamic_html(template, needle):
    assert needle in (REPO_ROOT / template).read_text()


def test_checkinout_js_uses_textcontent():
    js = (REPO_ROOT / "static/styles/js/checkinout.js").read_text()
    assert "box.textContent" in js
    assert '+ text + "</div>"' not in js


# --- dashboard calibration buckets -------------------------------------------

def test_dashboard_buckets_non_iso_dates(client, db_session, seed_user, monkeypatch):
    captured = {}
    real_render = routes.render_template

    def spy(name, **ctx):
        if name == "dashboard.html":
            captured.update(ctx)
        return real_render(name, **ctx)

    monkeypatch.setattr(routes, "render_template", spy)
    in_10_days = (datetime.utcnow() + timedelta(days=10)).strftime("%m/%d/%Y")
    db.session.add(Tools(tool_id_number="CAL-US", tool_name="Gauge", tool_location="A", tool_status="In Stock",
                         tool_calibration_due=in_10_days, tool_calibration_date="N/A",
                         tool_calibration_cert="N/A", tool_calibration_schedule="N/A"))
    db.session.add(Tools(tool_id_number="CAL-TXT", tool_name="Gauge2", tool_location="A", tool_status="In Stock",
                         tool_calibration_due="see binder", tool_calibration_date="N/A",
                         tool_calibration_cert="N/A", tool_calibration_schedule="N/A"))
    db.session.commit()
    username, _, password = seed_user
    client.post("/login", data={"username": username, "password": password})
    assert client.get("/dashboard").status_code == 200
    buckets = {b["label"]: b["count"] for b in captured["calibration_summary"]}
    assert buckets["Due in 30 days"] == 1
    assert buckets["Due in 90+ days"] == 0
