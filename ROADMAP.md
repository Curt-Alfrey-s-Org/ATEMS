# ATEMS — Analysis & Roadmap

**Repository:** [Curt-Alfrey-s-Org/ATEMS](https://github.com/Curt-Alfrey-s-Org/ATEMS)  
**Stack:** Flask 3.1, SQLAlchemy 2.0, Flask-Admin 2.0, Flask-Login, Bootstrap, Jinja2  
**Status:** Early development — core features working, Phase 1 complete

---

## Next step: post-merge host steps from the 2026-09-26 review (PR #40 fixes, PR #41 deps)

Open for review, not merged: [#40](https://github.com/Curt-Alfrey-s-Org/ATEMS/pull/40) (fixes, `fix/review-2026-09-26`) and [#41](https://github.com/Curt-Alfrey-s-Org/ATEMS/pull/41) (deps, `deps/update-2026-09-26`). The host steps for both PRs are here; this section is committed on the #40 branch. Nothing new is required in `.env`, and there are no files to back up.

Host: `.103`, `/home/n4s1/atems`, compose service `atems-api`. [REPO_HOST_MAPPING.md](https://github.com/Curt-Alfrey-s-Org/contracts-bot/blob/main/docs/REPO_HOST_MAPPING.md) says ATEMS moved there from `.105` on 2026-07-06, and `/home/ansible/atems` on `.105` is a backup clone. The 2026-09-25 section below still says `.105`.

**Merge order:** the PRs share no files, so either order works. Recommended: #40 first, because the #41 PostgreSQL test run needs #40's conftest fix (otherwise 5 env-login tests fail). Both rebuild the same image, so if both are merged, deploy once.

### Before pulling
- [ ] Power on VM .103 first (it is currently powered off).
- [ ] Nothing to back up.

### After merging PR #40
- [ ] `cd /home/n4s1/atems && git pull`
- [ ] Optional `.env` setting: `MAIL_TIMEOUT_SECONDS` (SMTP timeout; default 30).
- [ ] `docker compose up -d --build atems-api` (ships the template, JS and Python changes).
- [ ] Verify:
  - A CSV import preview works on `/import`, including an Excel CSV with a BOM.
  - Env login works with an `ADMIN_USERNAME` longer than 6 characters.
  - On `/logs`, a failed login with username `<b>x</b>` shows as text, not bold.
  - The reports page renders.
- [ ] Env-login accounts that already exist keep their old badge/phone. Only newly auto-created env users get the new format.
- [ ] Tests (GitHub Actions isn't running): `pytest`. Expect 204 passed.

### After merging PR #41
- [ ] If you build from the wheel cache, it must hold the new wheels: `ls build-contexts/wheels-bots | grep -E 'cryptography-50.0.1|pillow-12.3.0'`. Otherwise pip must be able to reach PyPI.
- [ ] `git pull && docker compose up -d --build atems-api` (ships the new wheels and the rebuilt `static/app/` SPA).
- [ ] Verify:
  - `docker compose exec atems-api python -c "import cryptography, PIL; print(cryptography.__version__, PIL.__version__)"` should print `50.0.1 12.3.0`.
  - `/app` loads.
- [ ] Non-Docker deploys only: `pip install -r requirements.txt`, then `cd frontend && npm ci && npm run build` (or `scripts/build_on_server.sh`).

### Decisions for you
- [ ] **Tool transfer on checkout** (`routes.py` `_checkinout_logic`). When user B checks out a tool held by A, it silently moves to B and no check-in is written for A. Block this, or log an implicit check-in?
- [ ] **Admin-only gating.** Any logged-in user can bulk import or overwrite tools (`/api/import/tools`), read the full app log (`/api/logs`), and trigger reminder e-mails (`/api/calibration-reminders/send`). Make these admin-only?
- [ ] Mixed clocks: check-in/out uses local time and overdue checks use UTC. There's no effect in the UTC container.
- [ ] `atems.log` has no rotation (`RotatingFileHandler`, or stdout only?).
- [ ] Majors not applied (#41):
  - react-router-dom 7 (fixes 2 moderate advisories; needs a router migration)
  - React 19, vite 8, Tailwind 4, TypeScript 7
  - reportlab 5
  - SQLAlchemy 2.1 (would need psycopg 3 or `postgresql+psycopg2://` URLs)

---

## Next step: post-merge host steps from the 2026-09-25 security review

Merged 2026-09-25: [#36](https://github.com/Curt-Alfrey-s-Org/ATEMS/pull/36) (lock down `/admin`, no default credentials), [#37](https://github.com/Curt-Alfrey-s-Org/ATEMS/pull/37) (open redirect, badge/check-in API auth + CSRF, `selftest/` in image, `deploy.sh` fails loudly), [#38](https://github.com/Curt-Alfrey-s-Org/ATEMS/pull/38) (admin-only run-tests, deploy scripts fail on build/rsync/migration errors). Feature work stays deferred (below); these are the steps for the next pull/redeploy of the running `.105` stack. Placeholders only; real values go in `.env`. See README → "Security & required environment".

- [ ] **Set in `.env` before redeploying** (compose/app refuse to start without them): `POSTGRES_PASSWORD`, `SECRET_KEY`, `ADMIN_USERNAME` / `ADMIN_PASSWORD` (strong; required if the users table is empty; also a break-glass admin login). Optional: `ADMIN_EMAIL`, `USER_USERNAME` / `USER_PASSWORD`, `SESSION_COOKIE_SAMESITE` (default `Lax`). Local dev/scripts: `ENVIRONMENT=development` (production is the default). `.env.example` has placeholders. (#36, #37)
- [ ] **Rotate the Postgres `atems_user` password** (the old compose fallback is in git history): new `POSTGRES_PASSWORD` in `.env` **and** inside Postgres, `ALTER USER atems_user WITH PASSWORD '<new>';` (the image only applies the variable on first init). (#36)
- [ ] **Accounts on known default passwords are now refused at login** (incl. the auto-created `admin` / `user` rows and the 200 seeded fake users): reset real accounts under `/admin` → Users, delete unused demo/fake accounts. If the only admin is affected: set `ADMIN_USERNAME=admin` + a strong `ADMIN_PASSWORD`, redeploy, log in with it, reset the DB password, then optionally remove `ADMIN_PASSWORD` from the env. (#36)
- [ ] **Postgres is now bound to `127.0.0.1:5436`:** anything connecting from another LAN host needs an SSH tunnel or must run on the host; firewall-check that the old `0.0.0.0:5436` exposure is closed. (#36)
- [ ] **Rebuild the image** so `selftest/` is included: `./deploy_atems_postgres.sh` (or `docker compose build atems-api`). Step 3 now really runs migrations: a `create_all()` DB matching the models is stamped at `head` automatically; if it stops with "schema differs from the models", inspect the diff, then migrate by hand or `docker compose exec -e FLASK_APP=atems:app atems-api flask db stamp <revision>` and re-run. (#37, #38)
- [ ] **systemd/venv deploys:** `scripts/deploy.sh` now fails instead of continuing; if `flask db upgrade` fails on a `create_all()` DB, check the schema, then `FLASK_APP=atems.py flask db stamp head` once. Needs Node ≥18/npm (or `SKIP_FRONTEND=1`); `scripts/deploy-to-server.sh` needs npm when `frontend/` exists (or `SKIP_FRONTEND_BUILD=1`). (#37, #38)
- [ ] **Clients:** `/api/checkinout` scan-gun/mobile clients must `POST /login` (`username`, `password`), keep the session cookie and send `Content-Type: application/json`. A badge-scan kiosk browser needs a logged-in low-privilege `user` account. Only `admin` role can run the full suite from `/selftest`. (#37, #38)
- [ ] **Public demo site:** the old demo logins no longer work; if a demo login is wanted, create a `user`-role account (`USER_USERNAME` / `USER_PASSWORD`). Never publish an admin password. (#36)
- [ ] **Smoke:** anonymous `/admin/` redirects to `/login`; admin login works; `/api/system/health` reports the self-test instead of erroring. (#36, #37)
- [ ] **Tests:** GitHub Actions is disabled; run `pytest tests/` locally (Postgres CI matrix not run). (#36–#38)

Open / deferred:

- [ ] The anonymous `/checkinout` HTML form still accepts username + badge without login (kiosk design, left as is). (#37)

---

## STATUS: DEFERRED

**DEFERRED — on hold until priority repos (rankings-bot, market-pie5-bot, alfa-ai, monitoring, USPBF, victron-ble2mqtt-integration, watauga-perch) reach production. Decision date: 2026-06-09.**

No feature work, refactors, or deploys on this repo until the priority repos above are in production. The sections below capture state as of the deferral date so nothing is lost.

### Current-state snapshot (2026-06-09)

- **Stack:** Flask 3.1 + SQLAlchemy 2.0 + Flask-Admin + Flask-Login + Jinja2 templates, gunicorn, PostgreSQL 16 (migrated Feb 2026, SQLite fallback retained), Alembic/Flask-Migrate, React + Vite frontend scaffold served at `/app`, Docker Compose. Assigned port: `127.0.0.1:5000:5000` (immutable).
- **Deployment state:** **Running** — `atems-api` (healthy, `127.0.0.1:5000->5000`) and `atems-postgres` (healthy, `0.0.0.0:5436->5432`) up on `.105`. Do not touch while deferred.
- **Completeness:** Phase 1 (runnable) and Phase 2 (core tool crib) essentially done; Postgres migration complete. Demo data seeded: 50K tools, 203 users, checkout history. Splash screen, log viewer, settings presets, draggable dashboard widgets, JSON API (`/api/health`, `/api/stats`, `/api/tools`, `/api/checkinout`), and 7+ pytest tests in place. Phases 3–6 (calibration, reporting, automation, modularization) not started; website deployment (§11) incomplete.

### Deferred backlog (do not lose)

1. **Deployment & fixes (was current priority):** deploy to website via `web-sites-server/` (nginx-atems.conf, atems.service, DEPLOY_NOW.md); debug deployed env; fix HTTP/HTTPS redirect & header issues; fix API connectivity/CORS/base-URL in production (§11).
2. **Phase 3 — calibration & compliance:** due-date logic + reminders, calibration vendor model, NIST-style record fields, calibration history report.
3. **Phase 4 — reporting:** usage, calibration, user activity, inventory reports; PDF export via reportlab; optional Excel. (Templates currently reference non-existent report routes.)
4. **Phase 5 — automation:** email reminders for overdue tools and calibration due; barcode scan REST endpoint; mobile-friendly check-in/out.
5. **PLAN_TOMORROW.md items:** barcode/QR scan at checkout; calibration-due email reminders; "return by" date on checkout + overdue-returns list/reminders.
6. **Phase 7–9 frontend:** draggable widgets polish, advanced log viewer in React, settings presets, WebSocket real-time updates, connection status indicator, error boundaries, React Query/Zustand, code splitting, path aliases, custom hooks.
7. **Option B — mount frontend** from host so website edits don't require image rebuilds (Rankings-Bot `docs/DOCKER_BASE_AND_SMALL_EDITS.md`).
8. **Phase 6 — modularization:** module interface, industry-agnostic core, example modules.
9. **Tech debt:** `models/tool_cat.py` (move to scripts/ or remove), duplicate alembic in requirements.txt, `User.phone unique=True` reconsideration, templates referencing missing report routes.
10. **AI inline doc references** (rankings-bot pattern — see section below).
11. **Research + audit subagent pass** (alfa-ai `docs/audit/` pattern — see section below).

### Resume checklist (when work restarts)

- [ ] Re-verify dependency currency: `requirements.txt` (Flask, SQLAlchemy, Flask-Admin, Flask-Login, gunicorn, psycopg2-binary, reportlab) and `frontend/package.json` — check deprecations and CVEs.
- [ ] Re-read official docs for the exact stack versions before changing code (workspace rule: manuals first) — Flask-Admin 2.x and SQLAlchemy 2.x both moved fast recently.
- [ ] Re-run the test suite (`./run_atems_tests.sh` / pytest) and the self-test (`run_selftest.sh`); confirm migrations apply against the running Postgres.
- [ ] Verify port/network constants unchanged: `127.0.0.1:5000:5000`, `tunnel_network`, atems-postgres on 5436.
- [ ] Re-check WHATS_NEXT.md and PLAN_TOMORROW.md against this backlog and consolidate — three planning docs drift apart while deferred.
- [ ] Run the research + audit subagent pass before resuming feature work (per section below).

---

## Backlog — AI inline doc references (apply later)

Mirror **rankings-bot** (Flask/Jinja here, same idea): `../rankings-bot/docs/AI_INLINE_DOC_REF_PROCESS.md` — hub docs + file-header pointers for auth (`Flask-Login`), models/migrations, and deploy.

---

## Current Priority

- [ ] **Deployment & fixes** — Deploy to website; debug; fix HTTP and API connectivity in production. Then start Phase 7 (React frontend migration).

---

## 1. Executive Summary

ATEMS (Automated Tool and Equipment Management System) is inventory control software for tool rooms, warehouses, and supply chain operations. The project uses a modular vision: a shared core with plug-in modules for different industries.

**Current state:** The Flask app structure exists with User and Tools models, Flask-Admin, and some check-in/check-out UI, but the app does not run end-to-end due to missing dependencies, broken imports, and incomplete routes.

---

## 2. Architecture Overview

```
ATEMS/
├── atems.py          # App factory, requires SQLALCHEMY_DATABASE_URI + SECRET_KEY
├── extensions.py     # DB, LoginManager, Admin, Migrate
├── routes.py         # Blueprint: /, /login, /logout, /checkinout
├── forms.py          # CheckInForm, CheckOutForm, CheckInOutForm
├── models/
│   ├── user.py       # User (badge_id, department, password hashing)
│   ├── tools.py      # Tools (calibration, location, checked_out_by)
│   ├── checkin.py    # Flask-Admin CheckinView
│   ├── checkout.py   # Flask-Admin CheckoutView
│   ├── notify.py     # NotificationsView
│   └── tool_cat.py   # Broken CLI script (not imported)
├── templates/        # common, home, login, checkinout, admin/*, reports, docs
├── static/           # images, styles, styles/js/*
├── scripts/          # seed_user.py, seed_tools.py (TBD)
├── migrations/       # Alembic with versions
└── (future) frontend/ # React + Vite + Tailwind
```

---

## 3. Critical Bugs & Blockers

### P0 — App Will Not Start or Run

| Issue | Location | Fix |
|-------|----------|-----|
| `routes` never imported | atems.py | Add `import routes` after app creation |
| `CheckInOutForm` missing | forms.py | Define `CheckInOutForm` with username, badge_id, tool_id_number |
| `checked_out_by` missing on Tools | models/tools.py | Add `checked_out_by = db.Column(db.String(128), nullable=True)` |
| `python-dotenv` not in requirements | requirements.txt | Add `python-dotenv` |
| No `.env` or `.env.example` | project root | Add `.env.example` with SQLALCHEMY_DATABASE_URI, SECRET_KEY |
| `login_manager.login_view = 'auth.login'` but no auth blueprint | extensions.py | Implement auth blueprint or use existing route name |

### P1 — Broken UI / Templates

| Issue | Location | Fix |
|-------|----------|-----|
| `checkinout.html` referenced but missing | routes.py | Create template or switch to checkin/checkout pages |
| `common.html` used by home/login but only in admin/ | templates | Add `templates/common.html` or fix extends path |
| `url_for('static', filename='checkinout.js')` wrong path | checkin.html, checkout.html | Use `styles/js/checkinout.js` |
| checkin.html missing username, badge_id | checkin.html | Add fields to match CheckInOutForm and checkinout.js |
| checkout.html uses username_or_badge_id; backend expects username + badge_id | checkout.html, routes | Align form fields and route logic |

### P2 — Data & Logic

| Issue | Location | Fix |
|-------|----------|-----|
| `tool_cat.py` in models — imports Tools/db without importing | models/tool_cat.py | Move to scripts/, fix imports, or remove |
| No migration versions | migrations/versions | Run `flask db migrate` after model fixes |
| User.phone `unique=True` may be too strict | models/user.py | Consider nullable or non-unique for flexibility |
| Duplicate alembic in requirements | requirements.txt | Remove duplicate |

---

## 4. Feature Gap vs. README

README promises:

| Feature | Status |
|---------|--------|
| Automated email reminders | Not implemented |
| Barcode/RFID tracking | Not implemented |
| Track: storage, who, job, duration, condition, calibration, shelf life | Partial (storage, calibration fields exist; job, condition, shelf life missing) |
| Calibration vendors, NIST compliance | Not implemented |
| Reports: Usage, Calibration, User Activity, Inventory, Custom | Templates reference non-existent routes |
| PDF/Excel export | reportlab present; no report endpoints |
| Auth (login) | Referenced in templates; no auth blueprint |

---

## 5. Roadmap

### Phase 1 — Make It Runnable (1–2 weeks) ✅ DONE

- [x] Add `python-dotenv` and `.env.example`
- [x] Implement `CheckInOutForm`, add `checked_out_by` to Tools
- [x] Register routes via blueprint in `atems.py`
- [x] Add `templates/common.html` for home/login
- [x] Fix static path for `checkinout.js`
- [x] Add auth (login/logout) and User password hashing
- [x] Create `checkinout.html`
- [x] Add `Flask-Admin` to requirements
- [x] Add `vatems/` to `.gitignore`
- [x] Run `flask db migrate` + `flask db upgrade`
- [x] Seed script for test user (`scripts/seed_user.py`)
- [ ] Remove/fix `tool_cat.py` (low priority — not imported)

### Phase 2 — Core Tool Crib (2–3 weeks)

- [x] Full check-in/check-out workflow with job/project field
- [x] Tool condition at check-in/check-out
- [x] Basic dashboard: tools out, overdue, due for calibration
- [x] Tool categories (category field, backfilled from tool_id_number)
- [ ] User management via Flask-Admin (already partially there)

### Phase 3 — Calibration & Compliance (2–3 weeks)

- [ ] Calibration due-date logic and reminders
- [ ] Calibration vendor model and linking
- [ ] NIST-style record-keeping fields
- [ ] Calibration history report

### Phase 4 — Reporting (2–3 weeks)

- [ ] Tool usage history report
- [ ] Calibration history report
- [ ] User activity report
- [ ] Inventory status report
- [ ] PDF export via reportlab
- [ ] (Optional) Excel export

### Phase 5 — Automation & Integrations (3–4 weeks)

- [ ] Email reminders for overdue tools
- [ ] Email reminders for calibration due
- [ ] Barcode scan integration (REST endpoint for scan-gun/app)
- [ ] Mobile-friendly check-in/check-out

### Phase 6 — Modularization (ongoing)

- [ ] Define module interface (base + plug-ins)
- [ ] Extract industry-agnostic core
- [ ] Example modules: aviation, manufacturing, retail, farming

### Phase 6.5 — PostgreSQL Migration ✅ COMPLETE (Feb 2026)

**Status:** Complete — ATEMS migrated from SQLite to PostgreSQL for production use.

**What was done:**
- [x] Created `docker-compose.yml` with PostgreSQL service (port 5436)
- [x] Added `init-db.sql` for database initialization with extensions
- [x] Updated `requirements.txt` with `psycopg2-binary>=2.9.9`
- [x] Updated `.env` and `.env.example` with PostgreSQL configuration
- [x] Enhanced `extensions.py` with database-aware connection pooling:
  - PostgreSQL: QueuePool with pool_size=10, max_overflow=20, pool_pre_ping=True
  - SQLite: StaticPool with pool_size=1 (fallback for development)
- [x] Updated `gunicorn.conf.py` to use 4 workers with PostgreSQL (1 for SQLite)
- [x] Verified model compatibility (all Flask-SQLAlchemy models work with PostgreSQL)

**Database Details:**
- **Service:** atems-postgres (PostgreSQL 16 Alpine)
- **Port:** 5436 (external) → 5432 (internal)
- **Database:** atems
- **User:** atems_user
- **Network:** tunnel_network (shared with other bots)

**Environment Variables:**
```env
DATABASE_URL=postgresql://atems_user:password@atems-postgres:5432/atems
SQLALCHEMY_DATABASE_URI=postgresql://atems_user:password@atems-postgres:5432/atems
POSTGRES_DB=atems
POSTGRES_USER=atems_user
POSTGRES_PASSWORD=your_secure_password
```

**Deployment:**
```bash
cd /home/ansible/atems
docker-compose up -d atems-postgres  # Start PostgreSQL
docker-compose up -d atems-api       # Start ATEMS with PostgreSQL
# Run migrations if needed:
docker-compose exec atems-api flask db upgrade
```

**Benefits:**
- ✅ Multi-worker gunicorn support (4 workers, up from 1)
- ✅ No "database is locked" errors
- ✅ Better concurrent user support
- ✅ Production-ready connection pooling
- ✅ Consistent with other bots (contracts-bot, credit-check-bot, market-pie5-bot)

### Tomorrow (Feb 2026)

- [ ] **Option B: Mount frontend (no image rebuild for website edits)** — When running in Docker, mount built frontend from host instead of copying into image. Website-only edits = build + restart container — no image rebuild. See Rankings-Bot `docs/DOCKER_BASE_AND_SMALL_EDITS.md`. Rankings Bot already uses this.

---

## 6. Quick Start (After Phase 1)

```bash
cd ATEMS
python -m venv .venv && source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
cp .env.example .env
# Edit .env: SQLALCHEMY_DATABASE_URI, SECRET_KEY (or use defaults)
export FLASK_APP=atems:create_app
flask db upgrade
python scripts/seed_user.py   # creates admin / admin123
python atems.py
```

Then open http://127.0.0.1:5000 — login with `admin` / `admin123`, use Admin for tools/users, and `/checkinout` for check-in/check-out.

---

## 7. Modern Frontend (React SPA)

Integrate a modern SPA frontend with shared core patterns (health, self-test, settings, logs).

### 7.1 Components

| Component | Target | ATEMS Equivalent |
|-----------|--------------|------------------|
| **Frontend** | React + Vite + TypeScript | Replace Flask/Jinja templates with SPA |
| **Styling** | Tailwind CSS, dark theme, CSS variables | Match: dark sidebar, stat cards, modern layout |
| **Layout** | Sidebar nav, collapsible, avatar | Tools, Check-in/out, Admin, Reports, Settings |
| **Stats** | StatCard, StatsOverview, charts | Tools checked out, overdue, calibration due, total inventory |
| **Dashboard** | DraggableDashboard, widgets | Tool crib stats, recent check-ins, calibration alerts |
| **API** | FastAPI, REST + WebSocket | Add REST API to Flask (or FastAPI proxy) for SPA |
| **State** | React Query, useBotStatus | useToolStatus, useInventoryStats |
| **Testing** | Startup self-tests, pytest backend | Add startup checks, pytest for check-in/out |
| **UX** | Splash screen, video/image bg, connection status | Optional splash; connection status for API |
| **Errors** | ErrorBoundary, NetworkErrorHandler, PageErrorFallback | Same patterns for tool/inventory errors |

### 7.2 Architecture Options

**Option A — React SPA + Flask API (recommended):**
- Add Flask REST endpoints (`/api/tools`, `/api/checkinout`, `/api/stats`)
- Build React frontend in `ATEMS/frontend/`
- Serve built React from Flask static or reverse proxy
- Dark theme, sidebar, StatCards for inventory metrics

**Option B — Keep Flask templates, upgrade styling:**
- Port Tailwind + dark theme into Jinja base template
- Add StatCard-style sections to dashboard
- Simpler but less interactive than SPA

### 7.3 Visual Targets

- **Colors:** Dark theme (`--background`, `--foreground`, `--card`, `--primary`)
- **Cards:** `bg-card/60 border border-border/50 rounded-lg` with hover states
- **Sidebar:** Fixed left, `w-64` open, icon + label nav items
- **StatCard:** Title (muted), value (bold 2xl), optional change % (green/red)
- **Grid layout:** `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4`

---

## 8. Test Data: Top 10 Industries + Hand/Power Tools

Seed tools from major tool-using industries to find bugs during check-in/check-out testing.

### 8.1 Industries & Representative Tools

| Industry | Hand Tools | Power Tools |
|----------|------------|-------------|
| **1. Construction** | Hammer, tape measure, framing square, chisel, level, pry bar, utility knife | Cordless drill, circular saw, reciprocating saw, impact driver |
| **2. Manufacturing** | Calipers, wrench set, screwdriver set, files, punches | Drill press, bench grinder, belt sander, band saw |
| **3. Automotive** | Socket set, torque wrench, oil filter wrench, brake bleeder | Impact wrench, angle grinder, polisher |
| **4. Oil & Gas** | Pipe wrench, tubing cutter, thread gauge | Pneumatic drill, hydraulic torque wrench |
| **5. Aerospace** | Precision screwdriver, torque driver, rivet gun | Precision drill, deburring tool |
| **6. Electrical/Utilities** | Wire strippers, multimeter, voltage tester, fish tape | Hole saw kit, cable crimper |
| **7. Plumbing/HVAC** | Pipe cutter, basin wrench, tube bender | Drain snake, pipe threader |
| **8. Agriculture** | Pruning shears, fencing pliers, post driver | Chainsaw, brush cutter, auger |
| **9. Mining** | Rock pick, sledgehammer, crowbar | Jackleg drill, roof bolter |
| **10. Healthcare (Med Devices)** | Surgical instrument set, calibration gauge | Sterilization equipment, power drill (OR) |

### 8.2 Seed Script Scope

- **`scripts/seed_tools.py`** — Add 80–100 tools across all 10 industries
- Tool ID format: `{INDUSTRY}-{TYPE}-{NUM}` (e.g. `CONS-HAMMER-001`, `AUTO-DRILL-002`)
- Required fields: `tool_id_number`, `tool_name`, `tool_location`, `tool_status`, `tool_calibration_due`, etc.
- Include calibrated tools (multimeters, torque wrenches) and non-calibrated (hammers, screwdrivers)
- Store location as bin/shelf (e.g. `A1-02`, `B3-15`)

### 8.3 Test Scenarios (Find Bugs)

1. **Check-out:** User + badge + tool → tool marked checked out, `checked_out_by` set
2. **Check-in:** Same user returns tool → `checked_out_by` cleared, `checkin_time` updated
3. **Badge mismatch:** Wrong badge for user → error, no state change
4. **Unknown tool:** Tool ID not in DB → error, no crash
5. **Unknown user:** Username not in DB → error
6. **Double check-out:** Same user checks out already-checked-out tool → handle gracefully
7. **Calibrated tool checkout:** Ensure calibration due date visible in UI
8. **Bulk operations:** Many tools checked out/in sequence (performance, race conditions)
9. **Tool ID formats:** 8-char validator may reject `CONS-HAMMER-001` — relax or document format
10. **Concurrent users:** Two users check in/out different tools at once

---

## 9. Bugs to Fix (From Testing)

*Add items here as tests reveal issues.*

| Bug | Location | Description | Status |
|-----|----------|-------------|--------|
| Tool ID validator | forms.py `validate_tool_id` | Requires 8 chars; industry format `XXX-XXXXX-NNN` — relax | ✅ Fixed: 1-64 chars, alphanumeric + hyphens |
| CheckInOutForm tool_id | forms.py | Inconsistent validator | ✅ Fixed: added validate_tool_id |
| POST validation → HTML | routes.py checkinout | When form invalid on POST, returned HTML; JS expects JSON | ✅ Fixed: return JSON 400 with errors |

---

## 10. Modern Frontend Features

Features to add for a consistent, modern ATEMS UI:

### High Priority (Phase 7 - Modern Frontend)
- [x] **React + TypeScript + Vite Frontend** - Scaffold: frontend/ with Dashboard, StatCards, Sidebar; served at /app
- [ ] **Draggable Dashboard Widgets** - Allow users to customize dashboard layout (like DraggableDashboard.tsx)
- [ ] **Advanced Log Viewer** - Multi-filter, sortable, auto-refresh with view presets
- [ ] **Settings Presets** - One-click preset configurations for different use cases
- [ ] **Real-time Updates** - WebSocket support for live tool status updates
- [ ] **Connection Status Indicator** - Show API connection health
- [ ] **Advanced Settings Page** - Categorized settings with tooltips and validation

### Medium Priority (Phase 8 - Enhanced UX)
- [ ] **Performance Charts** - SVG-based charts for usage trends, calibration schedules
- [ ] **Background Customization** - Custom backgrounds, avatars for personalization
- [ ] **Error Boundaries** - React error boundaries for graceful error handling
- [ ] **Network Error Handler** - Retry logic and offline mode support
- [ ] **Mobile Navigation** - Collapsible, touch-friendly navigation
- [ ] **React Query Integration** - Smart caching and auto-refresh for data
- [ ] **Zustand State Management** - Global state for tool status, user preferences

### Low Priority (Phase 9 - Advanced Features)
- [ ] **Decision Report System** - Adapt for tool usage decision tracking
- [ ] **Testing Framework** - Test runner and patterns for frontend/API
- [ ] **Code Splitting** - Lazy-loaded pages for faster initial load
- [ ] **Path Aliases** - TypeScript path aliases (`@/` for `src/`)
- [ ] **Custom Hooks** - Reusable hooks (useToolStatus, useInventoryStats, useWebSocket)

---

## 11. Deployment & Fixes

- [x] **Deploy prep** — gunicorn in requirements; ProxyFix for https behind Nginx; deploy.sh script; fix systemd Type
- [ ] **Deploy to website** — web-sites-server/ (nginx-atems.conf, atems.service, DEPLOY_NOW.md, deploy-to-server.sh)
- [ ] **Debug** — Run and fix issues in deployed or target environment
- [ ] **Fix HTTP** — Resolve HTTP/HTTPS, redirects, headers, or mixed-content issues
- [ ] **Fix API** — Resolve API connectivity, CORS, base URL, or endpoint issues in production

---

## 12. Suggested Next Steps

1. ~~Create **`scripts/seed_tools.py`** with tools from top 10 industries.~~ ✅ Done (50,000 tools)
2. ~~Add **pytest tests** for check-in/check-out using seeded data.~~ ✅ Done (7 tests)
3. ~~Add **API routes** for tools, stats, checkinout (JSON) for future SPA.~~ ✅ Done (`/api/health`, `/api/stats`, `/api/tools`, `/api/checkinout`)
4. ~~Professional splash screen and demo site setup~~ ✅ Done (splash.html, 50K tools, demo accounts)
5. **Deployment & Fixes** — Deploy to website; debug; fix HTTP and API (see §11)
6. **Start Phase 7** — Plan React frontend migration
7. **Port Draggable Dashboard** — Implement widget-based dashboard with localStorage persistence
8. **Add Advanced Log Viewer** — Multi-filter log viewer with view presets
9. **Implement Settings Presets** — Tool crib configurations (Small Shop, Large Factory, etc.)

---

## Features & Improvements (backlog)

| Area | Item |
|------|------|
| Frontend | Draggable dashboard widgets; advanced log viewer; settings presets |
| UX | Real-time WebSocket updates; connection status indicator |
| Ops | Option B: mount frontend (no image rebuild); deploy to website |
| Data | Remove/fix `tool_cat.py` (low priority) |

### Tech Debt

- `tool_cat.py` in models — move to scripts/ or remove
- Duplicate alembic in requirements.txt
- User.phone `unique=True` — consider nullable for flexibility
- Templates reference non-existent report routes

---

## Next step (planned): research + audit subagent pass

Run the two-stage subagent workflow developed in `alfa-ai/docs/audit/` during the May 2026 ALFa AI architectural audit. The pattern surfaced 64 findings (17 Critical) on alfa-ai; we want the same coverage on every active repo before resuming feature work.

1. **Research Agent** — gathers OFFICIAL upstream docs for every technology this repo uses (versions, security posture, best practices, deprecations). Writes per-component facts + an audit checklist to `docs/audit/research/<component>.md` and a master `docs/audit/research/INDEX.md`.
2. **Audit Agent** — reads the research files, audits this repo against the embedded checklists + cross-cutting checks (internal-doc consistency, stale references, security-currency vs published CVEs, cluster-rules compliance). Writes findings + a severity-ranked remediation backlog to `docs/audit/audit-findings.md`.

Both passes are read-only on the host stack — they only write into the new `docs/audit/` directory. Remediation is gated on explicit per-finding approval.

**Reference workflow:**
- Pattern: `/home/ansible/alfa-ai/docs/audit/`
- Research output format: `/home/ansible/alfa-ai/docs/audit/research/INDEX.md`
- Audit output format: `/home/ansible/alfa-ai/docs/audit/audit-findings.md`

Added 2026-05-13 after the alfa-ai audit proved the pattern at scale.

---

## References

- [docs/USAF_TOOL_ACCOUNTABILITY_RESEARCH.md](docs/USAF_TOOL_ACCOUNTABILITY_RESEARCH.md) — USAF tool accountability
- [docs/AFI_21_101_COMPLIANCE.md](docs/AFI_21_101_COMPLIANCE.md) — AFI 21-101 compliance
- [docs/ATEMS_IMPROVEMENTS.md](docs/ATEMS_IMPROVEMENTS.md) — Improvement ideas
- [docs/ATEMS_TEST_REPORT.md](docs/ATEMS_TEST_REPORT.md) — Test report
- Rankings-Bot `docs/DOCKER_BASE_AND_SMALL_EDITS.md` — Option B mount frontend
