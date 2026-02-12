# ATEMS User Guide

Quick reference for running and using ATEMS (Automated Tool & Equipment Management System).

---

## Quick start (local)

1. **Environment** — Copy `.env.example` to `.env` and set at least:
   - `SQLALCHEMY_DATABASE_URI` (e.g. `sqlite:///atems.db` or MySQL URL)
   - `SECRET_KEY` (random string for sessions)
2. **Dependencies** — `pip install -r requirements.txt`
3. **Database** — Run migrations: `flask db upgrade` (or create DB and run migrations)
4. **Demo users** (optional) — `python scripts/seed_demo_users.py`
5. **Run** — `python atems.py` or `gunicorn -c gunicorn.conf.py atems:create_app()`
6. **Open** — http://localhost:5000 (or port from gunicorn)

---

## Login

- **Root** `/` — Splash screen with login.
- **Default credentials** — user/user123, admin/admin123 (after seeding demo users).
- **Production** — Set real users/passwords or integrate with your auth.

---

## Main features

| Area | Description |
|------|-------------|
| **Dashboard** | Tool overview, check-in/check-out. |
| **Check-in / Check-out** | Record who has which tool; optional return-by. |
| **Reports** | Usage, calibration, overdue returns, inventory (with export CSV/PDF/Excel). |
| **Import** | Bulk import tools (and optionally users) from CSV or Excel. |
| **Settings** | App and user preferences. |
| **Admin** | User and tool management (admin role). |

---

## Reports and export

- **Usage** — Checkout history with date range and limit.
- **Calibration** — Tools due or overdue for calibration.
- **Overdue returns** — Tools not returned by due date.
- **Inventory** — Tools by status and category. Use as **Master Inventory List (MIL)** for AFI 21-101 / CTK.
- **Export** — Use report type and format (CSV, PDF, Excel) from the reports UI or API (`/api/reports/export?type=...&format=...`).

## AFI 21-101 / CTK (Air Force tool accountability)

ATEMS can support Air Force CTK (Consolidated Tool Kit) requirements under AFI 21-101. See **docs/AFI_21_101_COMPLIANCE.md** for the compliance matrix, CTK Custodian role, and how to use the Inventory report as your Master Inventory List (MIL).

---

## API (high level)

- **Health** — GET `/` or app root.
- **Reports** — GET `/api/reports/usage`, `/api/reports/calibration`, `/api/reports/overdue-returns`, `/api/reports/inventory`.
- **Export** — GET `/api/reports/export?type=usage|calibration|overdue-returns|inventory&format=csv|pdf|xlsx`.
- **Import** — POST `/api/import/preview`, POST `/api/import/tools` (auth required).
- **Calibration reminders** — Configure and run per your docs (e.g. cron + script).

---

## Deployment

- **Port** — Default 5000 (see `PORT_INFO.md`).
- **Reverse proxy** — Traefik config: `traefik-atems.yml`; see `TRAEFIK_ATEMS.md`, `RUN_ON_SERVER.md`, `DEPLOY_NOW.md`.
- **Service** — `atems.service` (systemd) for gunicorn.

---

## Testing

- **Startup self-tests** — `python tests/startup_test.py` or `./run_selftest.sh`
- **Full test suite** — `pytest tests/ -v` or `./run_tests.sh`
- **CI** — `.github/workflows/tests.yml` and `lint.yml` run on push/PR.

---

## Workspace docs

- [All bots overview](../docs/BOTS_OVERVIEW.md)
- [Quick reference (ports, URLs)](../docs/QUICK_REFERENCE.md)
- [Deployment checklist](../docs/DEPLOYMENT_CHECKLIST.md)
