#!/usr/bin/env python3
"""
Exercise all ATEMS features and monitor logs.
Uses Flask test client - no server needed. Logs go to atems.log.
"""
import os
import sys

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:////tmp/atems_feature_test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atems import create_app
from extensions import db

app = create_app()
app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()
results = []


def test(name, fn):
    try:
        fn()
        results.append(("✓", name))
        return True
    except Exception as e:
        results.append(("✗", name, str(e)))
        return False


def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg)
    return True


def run():
    with app.app_context():
        db.create_all()
        from models.user import User
        from models.tools import Tools
        if not User.query.filter_by(username="admin").first():
            u = User(first_name="Admin", last_name="User", username="admin", email="admin@example.com",
                     badge_id="ADMIN001", phone="5550000000", department="ATEMS", supervisor_username="admin",
                     supervisor_email="admin@example.com", supervisor_phone="5550000000")
            u.set_password("admin123")
            db.session.add(u)
            db.session.commit()
        if not Tools.query.filter_by(tool_id_number="FEAT-TEST-001").first():
            t = Tools(tool_id_number="FEAT-TEST-001", tool_name="Feature Test Tool", tool_location="A1-01",
                     tool_status="In Stock", tool_calibration_due="N/A", tool_calibration_date="N/A",
                     tool_calibration_cert="N/A", tool_calibration_schedule="N/A")
            db.session.add(t)
            db.session.commit()

    print("\n=== ATEMS Feature Test ===\n")

    test("GET /api/health", lambda: assert_true(client.get("/api/health").status_code == 200 and client.get("/api/health").get_json().get("status") == "healthy"))
    test("GET /", lambda: assert_true(client.get("/", follow_redirects=False).status_code in (200, 302)))
    test("GET /login", lambda: assert_true(client.get("/login").status_code == 200))
    test("POST /login", lambda: assert_true(client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True).status_code == 200))
    test("GET /dashboard", lambda: assert_true(client.get("/dashboard").status_code == 200))
    test("GET /checkinout", lambda: assert_true(client.get("/checkinout").status_code == 200))

    def do_checkout():
        r = client.post("/checkinout", data={
            "username": "admin", "badge_id": "ADMIN001", "tool_id_number": "FEAT-TEST-001",
            "job_id": "JOB-001", "condition": "Good",
        })
        assert_true(r.status_code == 200 and r.get_json().get("status") == "success")
    test("POST /checkinout checkout (with job+condition)", do_checkout)

    def do_checkin():
        r = client.post("/checkinout", data={"username": "admin", "badge_id": "ADMIN001", "tool_id_number": "FEAT-TEST-001"})
        assert_true(r.status_code == 200 and r.get_json().get("status") == "success")
    test("POST /checkinout checkin", do_checkin)

    test("GET /api/stats", lambda: assert_true(client.get("/api/stats").status_code == 200))
    test("GET /api/tools", lambda: assert_true(client.get("/api/tools").status_code == 200))
    test("GET /api/history", lambda: assert_true(client.get("/api/history").status_code == 200))

    def do_api_checkinout():
        r = client.post("/api/checkinout", json={"username": "admin", "badge_id": "ADMIN001", "tool_id_number": "FEAT-TEST-001"})
        assert_true(r.status_code == 200 and r.get_json().get("status") == "success")
    test("POST /api/checkinout", do_api_checkinout)

    test("GET /selftest", lambda: assert_true(client.get("/selftest").status_code == 200))
    test("GET /api/system/health", lambda: assert_true((r := client.get("/api/system/health")).status_code == 200 and "self_test" in r.get_json()))
    test("POST /checkinout invalid 400", lambda: assert_true(client.post("/checkinout", data={"username": "", "badge_id": "", "tool_id_number": ""}).status_code == 400))
    test("POST /checkinout unknown user", lambda: assert_true((r := client.post("/checkinout", data={"username": "nobody", "badge_id": "999", "tool_id_number": "FEAT-TEST-001"})).status_code == 200 and r.get_json().get("status") == "error"))
    test("GET /logout", lambda: assert_true(client.get("/logout", follow_redirects=True).status_code == 200))

    print("\n--- Results ---")
    passed = sum(1 for r in results if r[0] == "✓")
    for r in results:
        print(f"  {r[0]} {r[1]}" + (f": {r[2]}" if len(r) > 2 else ""))
    print(f"\n{passed}/{len(results)} passed")
    return passed == len(results)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
