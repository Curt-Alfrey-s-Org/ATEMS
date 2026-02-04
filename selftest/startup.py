"""
ATEMS Startup Self-Tests
Runs at app init and via run_selftest.sh - catches errors before they appear in logs.
Adapted from Rankings-Bot startup self-tests.
"""
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CRITICAL_MODULES = ["routes.py", "atems.py", "forms.py", "models/__init__.py"]


def run_startup_selftests(app=None, logger=None):
    """
    Run startup self-tests. Returns (passed, failed, results).
    If logger is provided, logs [SELFTEST] lines for review.
    """
    results = []
    passed = failed = 0

    def log(msg):
        if logger:
            logger.info(msg)
        else:
            print(msg)

    # 1. Python syntax check
    t0 = time.time()
    try:
        errors = []
        for mod in CRITICAL_MODULES:
            p = PROJECT_ROOT / mod
            if p.exists():
                r = subprocess.run(
                    ["python3", "-m", "py_compile", str(p)],
                    capture_output=True, text=True, timeout=5, cwd=str(PROJECT_ROOT)
                )
                if r.returncode != 0:
                    errors.append(f"{mod}: {r.stderr[:80]}")
        elapsed = (time.time() - t0) * 1000
        if errors:
            results.append({"name": "Python Syntax Check", "passed": False, "duration_ms": elapsed, "error": "; ".join(errors[:2])})
            failed += 1
            log(f"[SELFTEST] ✗ Python Syntax Check ({elapsed:.0f}ms): {errors[0]}")
        else:
            results.append({"name": "Python Syntax Check", "passed": True, "duration_ms": elapsed})
            passed += 1
            log(f"[SELFTEST] ✓ Python Syntax Check ({elapsed:.0f}ms)")
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        results.append({"name": "Python Syntax Check", "passed": False, "duration_ms": elapsed, "error": str(e)[:80]})
        failed += 1
        log(f"[SELFTEST] ✗ Python Syntax Check ({elapsed:.0f}ms): {e}")

    # 2. Module imports (when app provided, we already passed; else create_app)
    t0 = time.time()
    try:
        if app is not None:
            elapsed = (time.time() - t0) * 1000
            results.append({"name": "Module Imports", "passed": True, "duration_ms": elapsed})
            passed += 1
            log(f"[SELFTEST] ✓ Module Imports ({elapsed:.0f}ms)")
        else:
            from atems import create_app
            _ = create_app()
            elapsed = (time.time() - t0) * 1000
            results.append({"name": "Module Imports", "passed": True, "duration_ms": elapsed})
            passed += 1
            log(f"[SELFTEST] ✓ Module Imports ({elapsed:.0f}ms)")
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        results.append({"name": "Module Imports", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
        log(f"[SELFTEST] ✗ Module Imports ({elapsed:.0f}ms): {e}")

    # 3. Models available
    t0 = time.time()
    try:
        from models import User, Tools, CheckoutHistory
        assert User is not None and Tools is not None and CheckoutHistory is not None
        elapsed = (time.time() - t0) * 1000
        results.append({"name": "Models", "passed": True, "duration_ms": elapsed})
        passed += 1
        log(f"[SELFTEST] ✓ Models ({elapsed:.0f}ms)")
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        results.append({"name": "Models", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
        log(f"[SELFTEST] ✗ Models ({elapsed:.0f}ms): {e}")

    # 4. Calibration utils
    t0 = time.time()
    try:
        from utils.calibration import parse_calibration_due, is_calibration_overdue
        assert parse_calibration_due("2025-01-15") is not None
        assert parse_calibration_due("N/A") is None
        elapsed = (time.time() - t0) * 1000
        results.append({"name": "Calibration Utils", "passed": True, "duration_ms": elapsed})
        passed += 1
        log(f"[SELFTEST] ✓ Calibration Utils ({elapsed:.0f}ms)")
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        results.append({"name": "Calibration Utils", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
        log(f"[SELFTEST] ✗ Calibration Utils ({elapsed:.0f}ms): {e}")

    # 5. App routes
    t0 = time.time()
    try:
        if app is None:
            from atems import create_app
            app = create_app()
        rules = [r.rule for r in app.url_map.iter_rules()]
        needed = ["/", "login", "checkinout", "api/health", "dashboard"]
        found = sum(1 for n in needed if any(n in r for r in rules))
        if found >= 4:
            elapsed = (time.time() - t0) * 1000
            results.append({"name": "App Routes", "passed": True, "duration_ms": elapsed})
            passed += 1
            log(f"[SELFTEST] ✓ App Routes ({elapsed:.0f}ms)")
        else:
            raise Exception(f"Expected routes not found (got {found}/5)")
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        results.append({"name": "App Routes", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
        log(f"[SELFTEST] ✗ App Routes ({elapsed:.0f}ms): {e}")

    # 6. Database (with app context)
    t0 = time.time()
    try:
        if app is None:
            from atems import create_app
            app = create_app()
        with app.app_context():
            from extensions import db
            from sqlalchemy import inspect
            insp = inspect(db.engine)
            tables = insp.get_table_names()
        elapsed = (time.time() - t0) * 1000
        if tables:
            results.append({"name": "Database", "passed": True, "duration_ms": elapsed})
            passed += 1
            log(f"[SELFTEST] ✓ Database ({elapsed:.0f}ms) - {len(tables)} tables")
        else:
            results.append({"name": "Database", "passed": False, "duration_ms": elapsed, "error": "No tables found"})
            failed += 1
            log(f"[SELFTEST] ✗ Database ({elapsed:.0f}ms): No tables")
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        results.append({"name": "Database", "passed": False, "duration_ms": elapsed, "error": str(e)[:80]})
        failed += 1
        log(f"[SELFTEST] ✗ Database ({elapsed:.0f}ms): {e}")

    total = passed + failed
    if failed == 0:
        log(f"[SELFTEST] ✓ Startup self-tests passed: {passed}/{total}")
    else:
        log(f"[SELFTEST] ⚠ Startup self-tests: {passed}/{total} passed, {failed} failed")
        for r in results:
            if not r.get("passed") and r.get("error"):
                log(f"[SELFTEST] ✗ {r['name']}: {r['error']}")

    return passed, failed, results
