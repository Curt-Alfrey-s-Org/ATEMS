#!/usr/bin/env python3
"""Startup tests for ATEMS - quick validation that system is ready."""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class StartupTest:
    """Startup validation tests."""

    def __init__(self):
        self.results = []

    def run_all(self):
        """Run all startup tests."""
        print("\n" + "=" * 60)
        print("ATEMS Startup Tests")
        print("=" * 60)

        passed = failed = 0

        # Test 1: Module imports
        start = time.time()
        try:
            from atems import create_app
            app = create_app()
            duration = (time.time() - start) * 1000
            print(f"  ✓ Module imports ({duration:.0f}ms)")
            self.results.append({"name": "Module Imports", "passed": True, "duration_ms": duration})
            passed += 1
        except Exception as e:
            duration = (time.time() - start) * 1000
            print(f"  ✗ Module imports ({duration:.0f}ms): {e}")
            self.results.append({"name": "Module Imports", "passed": False, "duration_ms": duration, "error": str(e)})
            failed += 1

        # Test 2: Models
        start = time.time()
        try:
            from models import User, Tools, CheckoutHistory
            assert User is not None and Tools is not None and CheckoutHistory is not None
            duration = (time.time() - start) * 1000
            print(f"  ✓ Models (User, Tools, CheckoutHistory) ({duration:.0f}ms)")
            self.results.append({"name": "Models", "passed": True, "duration_ms": duration})
            passed += 1
        except Exception as e:
            duration = (time.time() - start) * 1000
            print(f"  ✗ Models ({duration:.0f}ms): {e}")
            self.results.append({"name": "Models", "passed": False, "duration_ms": duration, "error": str(e)})
            failed += 1

        # Test 3: Calibration utils
        start = time.time()
        try:
            from utils.calibration import parse_calibration_due, is_calibration_overdue
            assert parse_calibration_due("2025-01-15") is not None
            assert parse_calibration_due("N/A") is None
            duration = (time.time() - start) * 1000
            print(f"  ✓ Calibration utils ({duration:.0f}ms)")
            self.results.append({"name": "Calibration Utils", "passed": True, "duration_ms": duration})
            passed += 1
        except Exception as e:
            duration = (time.time() - start) * 1000
            print(f"  ✗ Calibration utils ({duration:.0f}ms): {e}")
            self.results.append({"name": "Calibration Utils", "passed": False, "duration_ms": duration, "error": str(e)})
            failed += 1

        # Test 4: App routes
        start = time.time()
        try:
            from atems import create_app
            app = create_app()
            rules = [r.rule for r in app.url_map.iter_rules()]
            assert "/" in rules or any("/" in r for r in rules)
            assert "/login" in rules or any("login" in r for r in rules)
            assert "/checkinout" in rules or any("checkinout" in r for r in rules)
            duration = (time.time() - start) * 1000
            print(f"  ✓ App routes ({duration:.0f}ms)")
            self.results.append({"name": "App Routes", "passed": True, "duration_ms": duration})
            passed += 1
        except Exception as e:
            duration = (time.time() - start) * 1000
            print(f"  ✗ App routes ({duration:.0f}ms): {e}")
            self.results.append({"name": "App Routes", "passed": False, "duration_ms": duration, "error": str(e)})
            failed += 1

        total = passed + failed
        print("\n" + "=" * 60)
        print(f"Results: {passed}/{total} passed")
        print("=" * 60)

        return {"passed": passed, "failed": failed, "total": total, "results": self.results}


if __name__ == "__main__":
    tester = StartupTest()
    results = tester.run_all()
    sys.exit(0 if results["failed"] == 0 else 1)
