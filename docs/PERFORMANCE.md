# ATEMS Performance

Performance is improved by **running more instances** (multiple Gunicorn workers) and **parallel work per request** (dashboard queries in threads). Quality is unchanged.

## 1. Multiple Gunicorn workers (process-level concurrency)

- **Default:** 4 workers (was 2).
- **Env:** `WEB_CONCURRENCY` or `GUNICORN_WORKERS` (e.g. `GUNICORN_WORKERS=8`).
- **Effect:** More concurrent requests; throughput improves without changing behavior.
- **SQLite:** Use 1–2 workers to avoid "database is locked" (e.g. `GUNICORN_WORKERS=1`).
- **MySQL/Postgres:** Use 4+ workers; pool size is per-process (see `extensions.py`).

Example (systemd override or env file):

```bash
export GUNICORN_WORKERS=8
# or in atems.service: Environment="GUNICORN_WORKERS=8"
```

## 2. Parallel dashboard queries (per-request concurrency)

- **Default:** On (`ATEMS_DASHBOARD_PARALLEL=1`).
- **Env:** `ATEMS_DASHBOARD_PARALLEL=0` to disable (sequential queries).
- **Effect:** Six independent query groups run in parallel; dashboard latency ≈ max(query times) instead of sum.
- **Quality:** Same data; only execution order and timing change.

## 3. Request timing (monitoring)

- **Log:** Each request logs `[PERF] <timestamp> <METHOD> <path> <duration_ms>ms` to `atems.log`.
- **Filter:** Logs UI → preset "Performance (timestamps)" or `grep '[PERF]' atems.log`.
- **Threshold:** `ATEMS_PERF_LOG_THRESHOLD_MS=100` logs only requests ≥ 100 ms (reduces log volume).

## 4. Overdue-returns (N+1 removed)

- Overdue-returns use a single bulk query instead of one query per checked-out tool (dashboard, API, export).
