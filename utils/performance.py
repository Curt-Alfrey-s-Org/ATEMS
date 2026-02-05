# performance.py - Timestamps, timing, parallel execution, and bulk query helpers for ATEMS

import os
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Thread pool for parallel dashboard queries (I/O-bound). Reused across requests.
_dashboard_executor = None
_dashboard_executor_lock = threading.Lock()
MAX_PARALLEL_WORKERS = min(8, (os.cpu_count() or 4) + 2)  # Cap for DB connection sanity

# Log request timing only when duration exceeds this (ms). Set to 0 to log every request.
PERF_LOG_THRESHOLD_MS = float(__import__("os").environ.get("ATEMS_PERF_LOG_THRESHOLD_MS", "0"))


def get_request_timing_middleware(wsgi_app, log_threshold_ms=None):
    """WSGI middleware that logs [PERF] timestamp path method duration_ms for each request."""
    threshold = log_threshold_ms if log_threshold_ms is not None else PERF_LOG_THRESHOLD_MS

    def middleware(environ, start_response):
        start = time.perf_counter()
        start_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        def custom_start_response(status, headers, exc_info=None):
            duration_ms = (time.perf_counter() - start) * 1000
            path = environ.get("PATH_INFO", "")
            method = environ.get("REQUEST_METHOD", "")
            if threshold == 0 or duration_ms >= threshold:
                logger.info(
                    "[PERF] %s %s %s %.2fms",
                    start_ts,
                    method,
                    path,
                    duration_ms,
                    extra={"perf_duration_ms": duration_ms, "perf_path": path, "perf_method": method},
                )
            return start_response(status, headers, exc_info)

        return wsgi_app(environ, custom_start_response)

    return middleware


def _get_executor():
    """Lazy singleton ThreadPoolExecutor for parallel dashboard queries."""
    global _dashboard_executor
    with _dashboard_executor_lock:
        if _dashboard_executor is None:
            _dashboard_executor = ThreadPoolExecutor(
                max_workers=MAX_PARALLEL_WORKERS,
                thread_name_prefix="atems_dashboard",
            )
        return _dashboard_executor


def run_in_parallel(app, callables_list):
    """
    Run no-arg callables in parallel threads, each with app.app_context().
    callables_list: list of callables (e.g. lambda: query()). Each runs in a thread with app context.
    Returns list of results in same order. Exceptions are propagated.
    """
    def run_one(fn):
        with app.app_context():
            return fn()

    executor = _get_executor()
    futures = [executor.submit(run_one, c) for c in callables_list]
    return [f.result() for f in futures]


def get_overdue_returns_bulk(tools_out, now_dt, Tools, CheckoutHistory):
    """
    Build overdue-returns list in one query instead of N+1.
    tools_out: list of Tools instances that are checked out.
    now_dt: datetime (timezone-naive or aware) to compare return_by against.
    Returns list of dicts: tool_id_number, tool_name, username (checked_out_by), return_by (datetime).
    """
    if not tools_out:
        return []
    tool_ids = [t.tool_id_number for t in tools_out]
    # Single query: all checkouts for these tools, newest first
    rows = (
        CheckoutHistory.query.filter(
            CheckoutHistory.tool_id_number.in_(tool_ids),
            CheckoutHistory.action == "checkout",
        )
        .order_by(CheckoutHistory.event_time.desc())
        .all()
    )
    # Keep only latest checkout per tool
    latest_per_tool = {}
    for r in rows:
        if r.tool_id_number not in latest_per_tool:
            latest_per_tool[r.tool_id_number] = r
    # Build tool_id -> Tool for name/username
    tools_by_id = {t.tool_id_number: t for t in tools_out}
    overdue = []
    for tool_id, last_checkout in latest_per_tool.items():
        if not last_checkout.return_by or last_checkout.return_by >= now_dt:
            continue
        t = tools_by_id.get(tool_id)
        overdue.append({
            "tool_id_number": tool_id,
            "tool_name": (t.tool_name or "") if t else "",
            "username": (t.checked_out_by or "") if t else "",
            "return_by": last_checkout.return_by,
        })
    return overdue
