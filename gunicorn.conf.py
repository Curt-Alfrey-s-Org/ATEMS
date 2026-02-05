# Gunicorn config — ensures bind 0.0.0.0 for Traefik/Docker reachability
# Multiple workers improve throughput (parallel request handling). Quality unchanged.
import os

bind = "0.0.0.0:5000"
# WEB_CONCURRENCY (Heroku-style) or GUNICORN_WORKERS; default 4. Use 1–2 for SQLite to avoid "database is locked".
workers = int(os.environ.get("WEB_CONCURRENCY") or os.environ.get("GUNICORN_WORKERS") or "4")
timeout = 120
# Preload app so workers fork after loading (faster startup, less memory per worker)
preload = False  # Set True if not using --reload and DB supports concurrent connections
