"""
ATEMS System Health & Self-Test
GET /api/system/health returns self_test; POST run-tests triggers full suite.
"""
import os
import sys
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Cache for self-test results (avoid running on every health check)
_self_test_cache = {
    "results": None,
    "timestamp": None,
    "cache_duration": 60,
}

_http_tests_run = False
_http_tests_results = None


def _run_internal_self_tests(app):
    """Run internal self-tests (direct checks, no HTTP). Returns health/self_test dict."""
    from selftest.startup import run_startup_selftests
    passed, failed, results = run_startup_selftests(app=app, logger=None)
    total = passed + failed
    timings = {}
    for r in results:
        timings[r["name"].lower().replace(" ", "_")] = r.get("duration_ms", 0)
    total_ms = sum(timings.values())
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "success_rate": (passed / total * 100) if total > 0 else 0,
        "all_passed": failed == 0,
        "results": [
            {
                "name": r["name"],
                "passed": r.get("passed", False),
                "duration_ms": r.get("duration_ms", 0),
                "error": r.get("error"),
            }
            for r in results
        ],
        "timings": {
            "total_duration_ms": total_ms,
            "total_duration_s": total_ms / 1000,
            "test_timings": timings,
        },
    }


def _check_frontend_api_base_url(project_root: Path):
    """
    Fail if frontend defaults to localhost:8000 (causes screen-not-updating when
    deployed or when API runs on another port). Use same-origin '' or VITE_API_URL instead.
    Scans frontend/src for .ts, .tsx, .js, .jsx.
    """
    frontend_src = project_root / "frontend" / "src"
    if not frontend_src.exists():
        return True, None
    bad = "localhost:8000"
    for ext in ("*.ts", "*.tsx", "*.js", "*.jsx"):
        for path in frontend_src.rglob(ext):
            try:
                text = path.read_text(encoding="utf-8")
                if bad in text:
                    return False, f"Frontend has localhost:8000 in {path.relative_to(project_root)}; use same-origin '' or VITE_API_URL so UI works on subdomain"
            except Exception as e:
                return False, str(e)[:80]
    return True, None


def _run_http_self_tests():
    """Run HTTP-based self-tests (hit our own API)."""
    try:
        import requests
    except ImportError:
        return None
    base_url = os.getenv("API_URL", "http://127.0.0.1:5000")
    if not base_url.startswith("http"):
        base_url = f"http://{base_url}"
    base_url = base_url.rstrip("/")
    timeout = 5

    results = []
    passed = failed = 0
    timings = {}
    project_root = Path(__file__).resolve().parent.parent

    # Frontend API base URL (no hardcoded localhost:8000)
    t0 = time.time()
    ok, err = _check_frontend_api_base_url(project_root)
    elapsed = (time.time() - t0) * 1000
    timings["frontend_api_base_url"] = elapsed
    results.append({"name": "Frontend API base URL", "passed": ok, "duration_ms": elapsed, "error": None if ok else (err or "bad default")})
    passed += 1 if ok else 0
    failed += 0 if ok else 1

    # API Health (public, no auth)
    t0 = time.time()
    try:
        r = requests.get(f"{base_url}/api/health", timeout=timeout)
        elapsed = (time.time() - t0) * 1000
        timings["api_health"] = elapsed
        ok = r.status_code == 200 and r.json().get("status") == "healthy"
        results.append({"name": "API Health", "passed": ok, "duration_ms": elapsed, "error": None if ok else f"Status {r.status_code}"})
        passed += 1 if ok else 0
        failed += 0 if ok else 1
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        timings["api_health"] = elapsed
        results.append({"name": "API Health", "passed": False, "duration_ms": elapsed, "error": str(e)[:80]})
        failed += 1

    # API Stats route exists (may 302/401 if no session - route exists is enough)
    t0 = time.time()
    try:
        r = requests.get(f"{base_url}/api/stats", timeout=timeout, allow_redirects=False)
        elapsed = (time.time() - t0) * 1000
        timings["api_stats"] = elapsed
        # 200 = ok, 302 = redirect to login, 401 = unauth - all mean route exists
        ok = r.status_code in (200, 302, 401)
        results.append({"name": "API Stats Route", "passed": ok, "duration_ms": elapsed, "error": None if ok else f"Status {r.status_code}"})
        passed += 1 if ok else 0
        failed += 0 if ok else 1
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        timings["api_stats"] = elapsed
        results.append({"name": "API Stats Route", "passed": False, "duration_ms": elapsed, "error": str(e)[:80]})
        failed += 1

    total = passed + failed
    total_ms = sum(timings.values())
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "success_rate": (passed / total * 100) if total > 0 else 0,
        "all_passed": failed == 0,
        "results": results,
        "timings": {
            "total_duration_ms": total_ms,
            "total_duration_s": total_ms / 1000,
            "test_timings": timings,
        },
    }


def _log_selftest_run(returncode, stdout, stderr, duration_s, timeout_s):
    """Log full self-test run. Write debug file on failure."""
    status = "PASS" if returncode == 0 else "FAIL"
    logger.info(f"[SELFTEST] Run completed: {status} (returncode={returncode}) in {duration_s:.2f}s")
    if returncode != 0 or (stderr and stderr.strip()):
        debug_path = PROJECT_ROOT / "selftest_debug.log"
        try:
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(f"# Self-test run (returncode={returncode}, duration={duration_s:.2f}s)\n")
                f.write("# Analyze this file for failures.\n\n")
                if stdout:
                    f.write("=== STDOUT ===\n")
                    f.write(stdout)
                    if not stdout.endswith("\n"):
                        f.write("\n")
                if stderr:
                    f.write("\n=== STDERR ===\n")
                    f.write(stderr)
            logger.info(f"[SELFTEST] Debug log written to {debug_path}")
        except Exception as e:
            logger.warning(f"[SELFTEST] Could not write debug log: {e}")


def get_system_health(app):
    """Get system health with self_test. Uses cache."""
    global _self_test_cache, _http_tests_run, _http_tests_results

    now = time.time()
    if (
        _self_test_cache["results"] is not None
        and _self_test_cache["timestamp"] is not None
        and (now - _self_test_cache["timestamp"]) < _self_test_cache["cache_duration"]
    ):
        test_results = _self_test_cache["results"]
    else:
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

        t0 = time.time()
        internal = _run_internal_self_tests(app)

        # Try HTTP tests once (API may not be ready immediately)
        global _http_tests_results, _http_tests_run
        if not _http_tests_run:
            try:
                http_res = _run_http_self_tests()
                if http_res:
                    _http_tests_results = http_res
                    _http_tests_run = True
                    logger.info("HTTP self-tests completed")
            except Exception as e:
                logger.debug(f"HTTP self-tests not ready: {e}")

        test_results = _http_tests_results if _http_tests_results else internal
        test_elapsed = time.time() - t0
        _self_test_cache["results"] = test_results
        _self_test_cache["timestamp"] = now
        logger.info(f"Self-test completed in {test_elapsed:.2f}s, cached for {_self_test_cache['cache_duration']}s")

    return {
        "status": "healthy" if test_results["all_passed"] else "degraded",
        "self_test": {
            "passed": test_results["all_passed"],
            "total": test_results["total"],
            "passed_count": test_results["passed"],
            "failed_count": test_results["failed"],
            "success_rate": test_results["success_rate"],
            "results": test_results["results"],
            "timings": test_results.get("timings", {}),
        },
        "system": {
            "platform": os.name,
            "python_version": sys.version.split()[0],
        },
    }


def run_full_selftest():
    """Run full self-test suite (run_selftest.sh). Returns dict for API response."""
    import subprocess
    from datetime import datetime

    global _self_test_cache, _http_tests_run, _http_tests_results
    _self_test_cache["results"] = None
    _self_test_cache["timestamp"] = None
    _http_tests_run = False
    _http_tests_results = None

    script = PROJECT_ROOT / "run_selftest.sh"
    timeout = int(os.getenv("RUN_TESTS_TIMEOUT_SECONDS", "120"))
    timeout = max(60, min(timeout, 600))

    start = time.time()
    try:
        result = subprocess.run(
            ["bash", str(script)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_ROOT),
        )
        elapsed = time.time() - start
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        _log_selftest_run(result.returncode, stdout, stderr, elapsed, timeout)

        # Parse pytest output: "25 passed" or "20 passed, 5 failed"
        passed = failed = total = 0
        for line in stdout.split("\n"):
            if " passed" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "passed" and i > 0:
                        try:
                            passed = int(parts[i - 1])
                            break
                        except ValueError:
                            pass
            if " failed" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "failed" and i > 0:
                        try:
                            failed = int(parts[i - 1])
                            break
                        except ValueError:
                            pass
        total = passed + failed if (passed or failed) else 0

        failed_tests = []
        for line in stdout.split("\n"):
            if "FAILED" in line and "::" in line:
                # pytest format: tests/test_x.py::TestClass::test_name FAILED
                name = line.split("FAILED")[0].strip()
                if name:
                    failed_tests.append({"name": name, "passed": False})

        return {
            "success": result.returncode == 0,
            "total": total or (passed + failed),
            "passed": passed,
            "failed": failed,
            "warnings": 0,
            "duration_s": round(elapsed, 2),
            "failed_tests": failed_tests,
            "output": stdout[-3000:] if len(stdout) > 3000 else stdout,
            "stderr": stderr[-1000:] if len(stderr) > 1000 else stderr,
            "timestamp": datetime.now().isoformat(),
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Test suite timed out after {timeout}s.",
            "duration_s": timeout,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error running self-tests: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
