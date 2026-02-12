# Gunicorn config — bind 0.0.0.0 for reverse proxy (Nginx) reachability
# Multiple workers improve throughput (parallel request handling).
# With PostgreSQL, we can use multiple workers safely (no "database is locked" issues).
import os

bind = "0.0.0.0:5000"

# WEB_CONCURRENCY (Heroku-style) or GUNICORN_WORKERS; default 4 for PostgreSQL
# For SQLite, use 1 worker to avoid locking issues
# For PostgreSQL, use 2-4+ workers based on CPU cores
db_uri = os.environ.get("SQLALCHEMY_DATABASE_URI", "")
if "sqlite" in db_uri.lower():
    default_workers = "1"  # SQLite: single worker to prevent locking
else:
    default_workers = "4"  # PostgreSQL/MySQL: multiple workers

workers = int(os.environ.get("WEB_CONCURRENCY") or os.environ.get("GUNICORN_WORKERS") or default_workers)
timeout = 120

# Preload app so workers fork after loading (faster startup, less memory per worker)
# Safe with PostgreSQL; avoid with SQLite
preload = False if "sqlite" in db_uri.lower() else True

# Worker class - sync is default, use gevent for async if needed
worker_class = "sync"

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"
