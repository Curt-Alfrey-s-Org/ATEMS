# ATEMS — Automated Tool & Equipment Management System

Inventory control software for tool rooms, warehouses, and supply chain operations.

**Workspace:** [All bots overview](../docs/BOTS_OVERVIEW.md) · [Quick reference](../docs/QUICK_REFERENCE.md)

## Shared dependency cache

This repo pulls pip and npm deps through the server-wide cache at **`/srv/dep-cache`** so containers and host builds don't redownload packages between rebuilds. `Dockerfile` uses BuildKit cache mounts with shared id `bots-pip`; `scripts/build_on_server.sh` points npm at `/srv/dep-cache/npm`. Manage with `/srv/dep-cache/bin/dep-cache {status,prune --older-than 30d,clear}`. Details: `/srv/dep-cache/README.md`.

## Production Ports (Server)

See `/home/ansible/.github/PORT_ASSIGNMENTS.md` for the canonical list.

- **API host binding:** `127.0.0.1:5000`
- **Database host binding:** `5436:5432`

**Login:** Root `/` shows a splash screen with login. There are **no default credentials**. The first admin comes from `ADMIN_USERNAME` / `ADMIN_PASSWORD` (see [Security & required environment](#security--required-environment)). To create demo users, run `ADMIN_PASSWORD=... USER_PASSWORD=... python scripts/seed_demo_users.py`.

---

## Quick Start (Docker + PostgreSQL)

**Recommended for production:**

```bash
cd /home/ansible/atems

# 1. Configure environment
cp .env.example .env
nano .env  # Set POSTGRES_PASSWORD, SECRET_KEY and ADMIN_PASSWORD (required, no defaults)

# 2. Deploy with script
./deploy_atems_postgres.sh

# 3. Access ATEMS
# http://localhost:5000
# Login: ADMIN_USERNAME / ADMIN_PASSWORD from .env
```

**Database:** PostgreSQL 16 (port 5436, bound to 127.0.0.1) · See [POSTGRESQL_MIGRATION.md](POSTGRESQL_MIGRATION.md)

---

## Security & required environment

As of the 2026-09-25 security review, ATEMS ships with **no default credentials**.

| Variable | Required | Purpose |
|----------|----------|---------|
| `SECRET_KEY` | yes | Flask session signing key. The app refuses to start without it. |
| `SQLALCHEMY_DATABASE_URI` | yes (non-Docker) | Database URL. Docker Compose builds it from `POSTGRES_PASSWORD`. |
| `POSTGRES_PASSWORD` | yes (Docker) | Postgres password. `docker compose` refuses to start if it is unset or empty. There is no fallback value. |
| `ADMIN_PASSWORD` | on first boot | Creates the first admin when the users table is empty. In production, startup **fails** with a clear error if it is missing. Known defaults such as `admin123` are rejected. |
| `ADMIN_USERNAME` / `ADMIN_EMAIL` | no | Username and email for that first admin (default `admin` / `admin@example.com`). |
| `USER_USERNAME` / `USER_PASSWORD` | no | Optional env-based login with the `user` role. |
| `ENVIRONMENT` | no | Defaults to production. Set `development` (or `test`) locally and in CI so an empty DB can start without `ADMIN_PASSWORD`. |

Login behaviour:
- `admin/admin123` and `user/user123` no longer exist as built-in logins. Env-based logins exist only for `ADMIN_*` / `USER_*` pairs you set.
- Known default passwords (`admin123`, `user123`, `demo123`, `changeme123`, ...) are **refused at login**, even for existing accounts. Anyone still using one must have it reset. An admin can do that under `/admin` → Users, which now has a write-only password field.
- `/admin` (Flask-Admin: users, tools, history, check-in/out, notifications) requires a logged-in user with role `admin`. Anonymous users are redirected to `/login`, and non-admins to `/dashboard`.
- When `ADMIN_USERNAME`/`ADMIN_PASSWORD` are set in the environment, they work as a login for that account. Setting `ADMIN_USERNAME=admin` plus a strong `ADMIN_PASSWORD` is how to regain access if the only admin still has a default password.
- The Postgres port is published on `127.0.0.1:5436` only (host-local).

Follow-up hardening (review 2026-09-25, Medium/Low findings):
- **Login redirect:** `/login?next=...` only follows same-site relative paths (e.g. `/reports`). Absolute or scheme-relative URLs (`https://...`, `//host`, `/\host`) are ignored and you land on `/dashboard`.
- **`/api/user-by-badge` requires login.** The check-in/out page still works anonymously, but scanning a badge only auto-fills the username when the browser is logged in (e.g. a tool-crib kiosk account with role `user`). Otherwise type the username.
- **`/api/checkinout` requires login and a JSON body** (`Content-Type: application/json`); other content types get `415`. This is the CSRF defence for that endpoint (cross-site forms cannot send JSON). JSON clients no longer fail with "The CSRF token is missing." Scan-gun/mobile clients must log in via `POST /login` first and reuse the session cookie. The HTML form at `/checkinout` is unchanged.
- The session cookie is now `SameSite=Lax` (override with `SESSION_COOKIE_SAMESITE` only if you know you need to).
- **Docker image now includes `selftest/`**, so `/api/system/health` and the startup self-tests work in the container. In the image, "Run tests" runs the startup self-tests only (the pytest suite is never shipped). On a checkout, "Run tests" runs `run_selftest.sh` against a throwaway SQLite file, never the live database. Self-test failures at startup are logged at ERROR level.
- **`scripts/deploy.sh` fails loudly** (`set -euo pipefail`): a failed `git pull --ff-only`, `pip install`, `flask db upgrade` or frontend build stops the deploy with a non-zero exit code. The frontend is built with full `npm ci` (vite is a devDependency). Opt-outs: `SKIP_GIT_PULL=1`, `SKIP_MIGRATIONS=1`, `SKIP_FRONTEND=1`. If `flask db upgrade` fails on a database that was created by `db.create_all()` and never migrated, check the schema matches the models, then run `FLASK_APP=atems.py flask db stamp head` once.

Deferred items (review 2026-09-25, final pass):
- **"Run Full Test Suite" is admin-only.** `POST /api/system/run-tests` can run for up to 10 minutes, so it now returns `403` for logged-in users without role `admin` (anonymous users are still sent to login). The button on `/selftest` is disabled for non-admins. `GET /api/system/health` is unchanged (any logged-in user).
- **`scripts/deploy-to-server.sh` fails loudly** (`set -euo pipefail`): a missing `npm`, a failed `npm ci` / `npm run build`, or a failed `rsync` stops the script with a non-zero exit code and shows the tool's own error output (nothing is sent to `/dev/null` any more). Nothing is synced after a failed build. Opt-out: `SKIP_FRONTEND_BUILD=1` deploys without building the frontend.
- **`deploy_atems_postgres.sh` step 3 fails on a failed migration.** It runs `flask db upgrade` with `FLASK_APP=atems:app` (before, the missing `FLASK_APP` and a failed upgrade were both hidden behind a "Note"). A brand-new database, where the app's startup `db.create_all()` already built every table, is detected: if its schema matches the models exactly it is stamped at `head` once, then upgraded. An unversioned database whose schema differs from the models stops the deploy with the list of differences. Check the schema, then migrate it by hand or run `flask db stamp <revision>`.

Upgrading an existing deployment: see the "Operator actions" list in the PR `fix/security-review-2026-09-25`. In short: set a strong `POSTGRES_PASSWORD`, `SECRET_KEY` and `ADMIN_PASSWORD` in `.env`, redeploy, then reset any account that still uses a default password.

---

## Deployment

Files for deploying ATEMS to https://alfaquantumdynamics.com/app/atems.

| File | Purpose |
|------|---------|
| `deploy_atems_postgres.sh` | **Quick Start** — Deploy ATEMS with PostgreSQL (Docker) |
| `docker-compose.yml` | Docker services: PostgreSQL + ATEMS API |
| `POSTGRESQL_MIGRATION.md` | PostgreSQL migration guide (SQLite → PostgreSQL) |
| `RUN_ON_SERVER.md` | **Systemd** — Run ATEMS directly on server 105 |
| `NGINX_DEPLOYMENT.md` | Nginx reverse proxy setup (current standard) |
| `web-sites-server/nginx-atems.conf` | Nginx site config (copy to /etc/nginx/sites-available/atems) |
| `web-sites-server/atems.service` | systemd unit for gunicorn |
| `DEPLOY_NOW.md` | Step-by-step deploy instructions |
| `PORT_INFO.md` | Port mapping and arch |

See **RUN_ON_SERVER.md** for the full setup. **docs/ATEMS_TEST_REPORT.md** for test and splash login details. **docs/USER_GUIDE.md** for quick start, login, reports, and deployment.

**Ops / reliability:** API JSON errors and `X-Request-ID` for `/api/*`, DB-aware `/api/health`, and Docker healthcheck details are summarized in [IMPROVEMENTS_FROM_RANKINGS.md](IMPROVEMENTS_FROM_RANKINGS.md) (patterns aligned with rankings-bot where applicable).
