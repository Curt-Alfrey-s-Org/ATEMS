# Improvements informed by rankings-bot

Small, architecture-appropriate changes (Flask + SPA) — **not** a full Prometheus/Grafana stack (ATEMS is a single-app deployment; use existing self-test and logs).

| Area | Change |
|------|--------|
| **API errors** | `utils/api_error_handlers.py`: JSON bodies for `/api/*` on 404/500 and DB errors; `X-Request-ID` on requests/responses for log correlation (similar idea to rankings-bot’s `request_id` on errors). |
| **Health** | `GET /api/health` runs a lightweight `SELECT 1`; returns `status` `healthy` or `degraded`, plus `database` `ok` / `unavailable`, always HTTP 200 for probes (aligns with “probe-friendly” health from rankings-bot). |
| **Docker** | `atems-api` healthcheck calls `/api/health` via Python (slim image has no `curl`). Gunicorn `CMD` targets `atems:app` (module-level WSGI app). |
| **Frontend client** | Sends `X-Request-ID` per request; **timeout was already 10s** — no duplicate timeout work. |

**Skipped (by design):** FastAPI-style global exception middleware (different framework); full observability stack; duplicate axios timeout.
