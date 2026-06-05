# ALFa AI Integration Plan — atems

> Doc-first, single best path. **Flask** application (not FastAPI). Stages are sequential; do not start Stage N+1 until Stage N exits cleanly.
>
> **URL convention:** atems runs on `.105`. The ALFa AI brain runs on `.111`. All LiteLLM / orchestrator calls from `atems-api` container and host shell target `192.168.0.111`. The in-Docker DNS name `alfa-ai-litellm:4000` is **only** resolvable from inside `.111`'s Compose network — do not use it from `.105`. See [/home/ansible/.cursor/plans/ALFA_AI_INTEGRATION_PLAN_HOST_105.md](/home/ansible/.cursor/plans/ALFA_AI_INTEGRATION_PLAN_HOST_105.md) §1 and §6.

---

## 0. Authoritative References

### ALFa AI (read-only, `/home/ansible/alfa-ai`)

1. `alfa-ai/docs/CURRENT_CAPABILITIES_AND_USE_CASES.md`
2. `alfa-ai/docs/ARCHITECTURE_SPEC.md`
3. `alfa-ai/docs/PORT_ASSIGNMENTS.md`
4. `alfa-ai/docs/COLLABORATION_RUNTIME.md`
5. `alfa-ai/docs/EVALUATION_FRAMEWORK.md`
6. `alfa-ai/docs/DATA_QUEUE_MODEL.md`
7. `alfa-ai/docs/DEPLOYMENT_BASELINE.md`
8. `alfa-ai/docs/ROADMAP.md`
9. `alfa-ai/docs/MILESTONE_BACKLOG.md`
10. `alfa-ai/docs/ADMIN_HEALTH_WEB_WORKFLOW.md`
11. `alfa-ai/deploy/litellm_config.yaml` — model alias SSoT
12. `/home/ansible/.cursor/plans/ALFA_AI_INTEGRATION_PLAN_HOST_105.md` — host service contract (§1, §6)

### Structural template + proven HTTP client (adapt to Flask/sync)

13. `contracts-bot/.cursor/plans/ALFA_AI_INTEGRATION_PLAN.md` — section layout
14. `credit-check-bot/.cursor/plans/ALFA_AI_INTEGRATION_PLAN.md` — PII redaction discipline
15. `auth-service/.cursor/plans/ALFA_AI_INTEGRATION_PLAN.md` — admin-only monitor + redaction-leak tests
16. `rankings-bot/api/services/litellm_client.py` — port logic to sync `requests` (not async httpx)
17. `rankings-bot/alembic/versions/050_ollama_activity_log.py` — telemetry DDL
18. `rankings-bot/docs/ALFA_AI_HOW_TO_USE.md` — operator guide template

### atems repo (discovered 2026-05-23)

19. `atems/README.md` — mission, ports, Docker quick start
20. `atems/CONTRIBUTING.md` — dev workflow
21. `atems/atems.py` — application factory, blueprint registration, default admin bootstrap (lines 16–125)
22. `atems/routes.py` — all HTTP routes (lines 74–1063)
23. `atems/extensions.py` — Flask-Login, Flask-Admin, Flask-Migrate, SQLAlchemy pool config
24. `atems/models/user.py` — User PII fields, roles (`admin`, `user`, `ctk_custodian`)
25. `atems/models/tools.py`, `atems/models/checkout_history.py` — domain models
26. `atems/migrations/versions/` — Flask-Migrate (6 revisions; latest adds `return_by`)
27. `atems/docker-compose.yml` — `127.0.0.1:5000:5000`, `tunnel_network`, `atems-postgres`
28. `atems/Dockerfile`, `atems/gunicorn.conf.py` — gunicorn sync workers, `0.0.0.0:5000` in container
29. `atems/atems.service`, `atems/web-sites-server/atems.service` — systemd alternative
30. `atems/frontend/` — Vite/React SPA (partial; `/app` route only)
31. `atems/templates/base.html` — primary Jinja2 shell (slate-900 / sky-400 theme)
32. `atems/docs/USER_GUIDE.md`, `atems/docs/AFI_21_101_COMPLIANCE.md`
33. `atems/PORT_INFO.md`, `atems/DEPLOY_NOW.md`, `atems/RUN_ON_SERVER.md`
34. `atems/conftest.py`, `atems/tests/` — pytest layout
35. `/home/ansible/docs/ALFA_AI_HOST_105_USAGE.md` — host operator guide

### Workspace rules

36. `/home/ansible/.cursorrules` — port 5000, `tunnel_network`, loopback binding
37. `/home/ansible/.cursor/rules/port-assignment-rules.mdc`
38. `/home/ansible/.cursor/rules/deployment-process-ownership.mdc`
39. `/home/ansible/.cursor/rules/recommendation-sequencing.mdc`
40. `/home/ansible/AGENTS.md`

### Industry standards

- [Flask 3.x deployment](https://flask.palletsprojects.com/en/stable/deploying/) — gunicorn as WSGI server; sync workers
- [Flask Application Factory](https://flask.palletsprojects.com/en/stable/patterns/appfactories/) — `create_app()` in `atems.py`
- [gunicorn deployment](https://docs.gunicorn.org/en/stable/deploy.html) — sync `worker_class` (already set in `gunicorn.conf.py:25`)
- [Flask-Login](https://flask-login.readthedocs.io/) — session auth via `@login_required`
- [LiteLLM proxy quick start](https://docs.litellm.ai/docs/proxy/quick_start)
- [requests sessions](https://requests.readthedocs.io/en/latest/user/advanced/) — sync HTTP client (already in `requirements.txt:44`)
- [Twelve-Factor App](https://12factor.net/) — config via env; single process owner

---

## 1. Service Contract (immutable, from host plan §1 + atems discovery)

### Brain endpoints (hosted on `.111`, consumed from `.105`)

| Surface | URL from `atems-api` container on `.105` | URL from `.105` host shell |
|---------|------------------------------------------|----------------------------|
| LiteLLM proxy | `http://192.168.0.111:8413` | `http://192.168.0.111:8413` |
| ALFa orchestrator API | `http://192.168.0.111:8420` | `http://192.168.0.111:8420` |
| Operator console (browser) | `http://192.168.0.111:8420/operator/` | same |

**Do not** call `http://127.0.0.1:8413` or `:8420` from `.105`. **Do not** use `http://alfa-ai-litellm:4000` from atems on `.105`.

### atems local contract (discovered)

| Item | Value | Notes |
|------|-------|-------|
| Host port | **`127.0.0.1:5000:5000`** | Correct in `docker-compose.yml:67-68`; canonical per `.cursorrules` and `alfa-ai/docs/PORT_ASSIGNMENTS.md:9` |
| Container bind | `0.0.0.0:5000` | `gunicorn.conf.py:6`; required per `.cursorrules` Rule 4 |
| Docker network | `tunnel_network` (external) + `atems-network` (postgres) | Brain reached via LAN IP, not Docker DNS |
| Database | **PostgreSQL 16** (production Docker, port `5436:5432`) | `docker-compose.yml:16-46`; SQLite supported for dev/tests (`conftest.py:15`) |
| nginx / tunnel | Proxies to `127.0.0.1:5000` | Public: `https://atems.alfaquantumdynamics.com` |
| Telemetry table | `ollama_activity_log` | New table in `atems` Postgres DB (`atems-postgres`) |
| Health | `GET /api/health` | `routes.py:405-423`; always 200, DB-aware |

**Model aliases (SSoT: `alfa-ai/deploy/litellm_config.yaml`):**

| Use in atems | Alias | Trust zone |
|--------------|-------|------------|
| Signed-in Ask AI (dock) | `app-chat` | `app_authenticated` |
| Admin log triage / explain | `code` | `internal` |
| Agentic digest jobs | `agent` | `internal` |
| RAG embeddings (Stage 5) | `embed` / `nomic-embed-text` | `internal` |
| **Forbidden in MVP** | `public-chat` | — (no public demo) |

Trust zones for atems MVP: **`app_authenticated`** and **`internal`** only. No `public_web`.

**ALFa AI cluster contract (from host plan §6):** paste unchanged — brain on `.111`, LiteLLM at `http://192.168.0.111:8413`, orchestrator at `http://192.168.0.111:8420`, telemetry in `ollama_activity_log` with `metadata.trust_zone`.

---

## 2. Integration Surfaces

### Archetype decision

**Primary: contracts-bot `app_authenticated` Ask AI dock.** atems is a signed-in workforce app (Flask-Login sessions) with domain Q&A on inventory, calibration, and reports — same trust model as contracts-bot.

**Secondary discipline: credit-check-bot PII redaction + auth-service redaction-leak tests.** User records carry email, phone, badge, supervisor/manager contacts (`models/user.py:15-28`). Redact before any LLM prompt or log persist; never index raw `users` rows in RAG.

**Not auth-service-only** (AI is not limited to admin — custodians and users benefit from in-app help). **Not market-pie5-bot disclaimer archetype** (no public marketing chat surface).

---

### 2.1 Runtime — in-app Ask AI (Jinja2 dock + JSON API)

**Single approach:** Signed-in users ask domain questions via `POST /api/ai/ask` → `services/ai_narrative_llm.py` → sync `requests.Session` → LiteLLM `app-chat` at `http://192.168.0.111:8413`. UI is a **Jinja2 partial** included from `templates/base.html` (not htmx — not in deps; not React dock on primary pages).

**Allowed pages (register page context in template `{% block ai_page_context %}`):**

| Page | Route | Context bundle (redacted) |
|------|-------|---------------------------|
| **Dashboard** | `/dashboard` (`routes.py:100-217`) | Stat counts, calibration summary buckets, overdue return count — no full user rows |
| **Reports** | `/reports` (`routes.py:466-470`) | Report type hints, aggregate calibration/overdue counts |
| **Settings** | `/settings` (`routes.py:459-463`) | Mail/calibration reminder config flags only (no SMTP passwords) |

**Excluded until auth hardened:** `/checkinout`, `/api/checkinout`, `/api/user-by-badge` — these routes are **not** `@login_required` today (`routes.py:377, 1012, 1024`) for kiosk/scan-gun flows; do not attach Ask AI there.

**Depends on:** `@login_required` + Flask-Login session, `LITELLM_ENABLED=true`, `ollama_activity_log`, `services/atems_pii_redaction.py`.

**Cost:** ~500–2000 tokens per question (`app-chat`); ~5–25 s latency per `alfa-ai/docs/ROADMAP.md`.

---

### 2.2 Runtime — RAG over atems domain docs (not live user rows)

**Single approach:** Offline indexer embeds static docs + schema descriptions via LiteLLM `embed`; inject top-k into Ask AI system prompt via `build_atems_ask_ai_context()`.

**Index allow list:**

| Source | Fields | Exclude |
|--------|--------|---------|
| `docs/USER_GUIDE.md`, `docs/AFI_21_101_COMPLIANCE.md` | Section text | — |
| `docs/AFI_21_101_COMPLIANCE.md` compliance matrix | Requirement rows | — |
| `models/tools.py` column docstrings / field names | Schema only | Runtime values |
| `models/checkout_history.py` | Field semantics | Usernames at index time |
| Tool status enums | `column_choices` in `tools.py:44` | — |
| Calibration helpers | `utils/calibration.py` logic descriptions | — |

**Never index:** `users` table, live `checkout_history` rows with usernames, import CSV contents, `atems.log` raw lines with emails.

**Depends on:** `scripts/rag/index_atems_corpus.py`, `services/atems_rag.py`, redaction in `services/atems_pii_redaction.py`.

---

### 2.3 Runtime — agentic jobs via ALFa orchestrator

**Single approach:** Sync `requests` client → `POST http://192.168.0.111:8420/api/runs` with `ALFA_AI_API_TOKEN`; orchestrator uses `agent` alias.

**Concrete atems jobs:**

1. **Weekly calibration digest** — Input: SQL aggregates from `Tools` (overdue/due-30/60/90 counts by category). Output: markdown email body for CTK custodian. Role: `doc_maker`.
2. **Overdue returns summary** — Input: bulk overdue query (same as `api_reports_overdue_returns`, `routes.py:641-659`) with usernames replaced by counts per department. Output: supervisor memo. Role: `researcher` → `doc_maker`.
3. **Inventory audit checklist** — Input: MIL export schema + inventory stats (`api_reports_inventory`, `routes.py:662-687`). Output: AFI 21-101 gap checklist. Role: `doc_maker`.

**Scheduling:** Admin-triggered from Settings or systemd timer on `.105`; never on check-in/out hot path.

---

### 2.4 Runtime — admin assistant (AI Monitor + log triage)

**Single approach:**

- **AI Monitor:** Admin-only (`User.is_admin()`, `models/user.py:43-45`) — new `/settings/ai-monitor` Jinja page + `GET /api/admin/ai/monitor`.
- **Admin explain:** `POST /api/admin/ai/explain` — `internal` trust zone, model `code`, context = last N `atems.log` lines + `/api/health` snapshot (extend health in Stage 1).
- **Flask-Admin** (`admin.index` in `templates/base.html:52`) remains separate; AI Monitor is a first-class Settings sub-page.

**Depends on:** `ollama_activity_log`, admin session, redaction pipeline.

---

### 2.5 Dev-time — AGENTS.md + `.cursor/rules/alfa-ai-usage.mdc`

**Single approach:** Document Flask-specific patterns: sync `requests` client, `@login_required` gates, PII deny list (emails, phones, badge IDs in prompts), brain URLs, pointer to `docs/ALFA_AI_HOW_TO_USE.md`.

---

### 2.6 Dev-time — codegen scripts

**Single approach:** `scripts/codegen/` calling LiteLLM `code` via LAN URL:

| Script | Output |
|--------|--------|
| `scripts/codegen/generate_flask_route_stub.py` | Blueprint route + WTForms stub |
| `scripts/codegen/generate_pytest_stub.py` | pytest file for a route module |
| `scripts/codegen/generate_atems_model_docs.py` | Markdown from `models/*.py` |

---

### 2.7 Dev-time — CI PR triage

**Single approach:** `.github/workflows/ai-pr-triage.yml` — LiteLLM `code` reviews diff; strip emails, phone patterns, `SECRET_KEY`, `POSTGRES_PASSWORD`, bcrypt hashes. Self-hosted runner on `.105` with LAN access to `.111:8413`.

---

### 2.8 Future fine-tune capture (opt-in, redacted)

**Single approach:** `ALFA_FINETUNE_CAPTURE_ENABLED=false` (default). Mirror `ollama_activity_log` shape in `ai_finetune_capture`. **Never capture** user table rows, import file bytes, or checkout history with identifiable usernames. Export via `scripts/export_finetune_shard.py` with fail-closed email/phone regex scan (pattern from auth-service plan §6).

---

## 3. Concrete File-Level Plan

### Flask-specific implementation choices (locked)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| HTTP client | **sync `requests.Session`** | Already in `requirements.txt:44`; gunicorn uses sync workers (`gunicorn.conf.py:25`); avoids Flask 2.x async view complexity with SQLAlchemy sync sessions |
| Blueprint layout | `blueprints/ai.py` (`ai_bp`, url_prefix `/api/ai`) + `blueprints/admin_ai.py` (`admin_ai_bp`, url_prefix `/api/admin/ai`) | Keeps `routes.py` from growing further; register in `create_app()` after `routes.bp` |
| Activity log | Flask-SQLAlchemy model `OllamaActivityLog` + Flask-Migrate revision | Same columns as `rankings-bot/alembic/versions/050_ollama_activity_log.py:22-36` |
| UI | Jinja2 partial `templates/partials/ai_dock.html` + `static/js/ai_dock.js` | Primary UX is Jinja (`templates/base.html`); React `/app` gets dock in Stage 3b only |
| Auth guard | `@login_required` + helper `require_admin()` in `utils/auth_helpers.py` | Matches Flask-Login patterns in `extensions.py:66-68` |

### File table

| Target path | Action | Source pattern | Description |
|-------------|--------|----------------|-------------|
| `services/litellm_client.py` | NEW | `rankings-bot/api/services/litellm_client.py` | Sync `requests.Session`; trust-zone keys; default `LITELLM_BASE_URL=http://192.168.0.111:8413` |
| `services/ollama_activity_log.py` | NEW | rankings-bot | `log_ollama_activity()` writing Flask-SQLAlchemy model |
| `models/ollama_activity_log.py` | NEW | rankings-bot migration | SQLAlchemy model matching DDL |
| `services/atems_pii_redaction.py` | NEW | credit-check-bot redaction pattern | Strip email, phone, badge_id, supervisor contacts before LLM/log |
| `services/ai_narrative_llm.py` | NEW | rankings-bot (sync port) | Route completions through LiteLLM or graceful error |
| `services/atems_ask_ai_context.py` | NEW | rankings-bot `ask_ai_context.py` | Page-specific redacted bundles |
| `services/atems_rag.py` | NEW (Stage 5) | credit-check-bot RAG | Retrieve doc chunks |
| `services/alfa_orchestrator_client.py` | NEW (Stage 6) | contracts-bot plan | `/api/runs` via `requests` |
| `blueprints/ai.py` | NEW | — | `POST /api/ai/ask`, `GET /api/ai/health` |
| `blueprints/admin_ai.py` | NEW | auth-service admin pattern | Monitor + explain routes |
| `utils/auth_helpers.py` | NEW | — | `require_admin()` decorator |
| `atems.py` | EDIT | existing | Register blueprints; optional `LITELLM_*` config load |
| `routes.py` | EDIT | existing | Extend `/api/health` → `/api/health/detailed` with LiteLLM probe (or add in blueprint) |
| `migrations/versions/xxx_ollama_activity_log.py` | NEW | `050_ollama_activity_log.py` | Telemetry table |
| `templates/partials/ai_dock.html` | NEW | contracts-bot dock UX (Jinja port) | Fixed bottom panel; slate/sky theme matching `base.html:9` |
| `static/js/ai_dock.js` | NEW | — | `fetch('/api/ai/ask')` with CSRF token |
| `templates/base.html` | EDIT | existing | `{% include 'partials/ai_dock.html' %}` when authenticated |
| `templates/dashboard.html` | EDIT | existing | Set `ai_page_context` block |
| `templates/reports.html` | EDIT | existing | Set `ai_page_context` block |
| `templates/settings.html` | EDIT | existing | Admin AI Monitor link + context block |
| `templates/settings_ai_monitor.html` | NEW | rankings-bot monitor (Jinja) | Admin-only table |
| `frontend/src/components/AiDock.tsx` | NEW (Stage 3b) | rankings-bot | React `/app` only |
| `tests/test_ai_trust_boundary.py` | NEW | rankings-bot + auth-service | Auth + redaction-leak tests |
| `tests/test_litellm_health.py` | NEW | — | Health detailed includes litellm |
| `tests/test_atems_pii_redaction.py` | NEW | credit-check-bot | Email/phone/badge stripped |
| `.env.example` | EDIT | rankings-bot LiteLLM block | `LITELLM_*`, `ALFA_AI_*` |
| `docker-compose.yml` | EDIT | existing | Pass `LITELLM_*` env to `atems-api` |
| `docs/ALFA_AI_HOW_TO_USE.md` | NEW | Deliverable B | Operator guide |
| `docs/ALFA_AI_TRUST_ZONES_AND_ROLLOUT.md` | NEW | rankings-bot (atems-tailored) | Trust zone checklist |
| `.cursor/plans/ALFA_AI_INTEGRATION_PLAN.md` | NEW | this document | |
| `.cursor/rules/alfa-ai-usage.mdc` | NEW | — | Cursor guardrails |
| `AGENTS.md` | NEW | `/home/ansible/AGENTS.md` | Repo agent instructions |
| `scripts/rag/index_atems_corpus.py` | NEW (Stage 5) | — | Doc indexer |
| `scripts/codegen/*.py` | NEW (Stage 7) | contracts-bot | Dev generators |
| `.github/workflows/ai-pr-triage.yml` | NEW (Stage 7) | — | PR triage |
| `scripts/export_finetune_shard.py` | NEW (Stage 8) | — | JSONL export |

**Already present (reuse):**

- Flask-Login session auth (`extensions.py:58-68`, `routes.py:230-301`)
- `/api/health` with DB ping (`routes.py:405-423`)
- `utils/api_error_handlers.py` — `X-Request-ID` for `/api/*`
- `requests` dependency (`requirements.txt:44`)

**Gaps (no AI today):**

- Zero LiteLLM/LLM application code (grep confirmed — only hub/docs references)
- No `/api/health/detailed`
- No admin role guard on import/send routes (all `@login_required` only — any logged-in user can import; note in Stage 2 security hardening)
- `PORT_INFO.md` documents systemd; `README.md` recommends Docker — ownership drift

---

## 4. Staged Rollout

### Stage 0 — Preflight + single-owner verification (no AI code)

**Prerequisites:** Brain up on `.111`; UFW allows `.105 → .111:8413,8420`; `tunnel_network` exists.

**Operator preflight (on `.105`):**

```bash
docker network inspect tunnel_network
curl -fsS http://192.168.0.111:8413/health/liveliness
curl -fsS http://192.168.0.111:8420/health
curl -fsS http://192.168.0.111:8413/v1/chat/completions \
  -H "Authorization: Bearer ${LITELLM_API_KEY:?set LITELLM_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"app-chat","messages":[{"role":"user","content":"Say OK"}]}'
sudo lsof -ti :5000 || true
systemctl is-active atems 2>/dev/null || echo "atems.service not active"
docker ps --format '{{.Names}}\t{{.Status}}' | grep atems-api || true
```

**Single-owner check:** Exactly **one** process must own port 5000 ([deployment-process-ownership.mdc](/home/ansible/.cursor/rules/deployment-process-ownership.mdc)). Production on `.105` = **Docker Compose `atems-api`** (`deploy_atems_postgres.sh`). If `atems.service` is enabled, disable it before Compose deploy.

**Exit criteria:** Brain curls 200; port 5000 owned by `atems-api` container OR intentionally by systemd (not both); `app-chat` returns text.

---

### Stage 1 — LiteLLM client + activity log + detailed health

**Prerequisites:** Stage 0 green.

**Files:** NEW `services/litellm_client.py`, `models/ollama_activity_log.py`, `services/ollama_activity_log.py`, migration; EDIT `docker-compose.yml`, `.env.example`; add `GET /api/health/detailed`.

**Operator steps:**

```bash
cd /home/ansible/atems
docker compose exec atems-api flask db upgrade
# Add LITELLM_* to .env (see docs/ALFA_AI_HOW_TO_USE.md)
docker compose up -d --no-deps --force-recreate atems-api
curl -fsS http://127.0.0.1:5000/api/health
curl -fsS http://127.0.0.1:5000/api/health/detailed | python3 -m json.tool
```

**Exit criteria:** `/api/health/detailed` shows `litellm.status` and `litellm.base_url: http://192.168.0.111:8413`; migration applied; one owner on port 5000.

---

### Stage 2 — Ask AI API + PII redaction + trust tests

**Prerequisites:** Stage 1 green.

**Files:** NEW `blueprints/ai.py`, `services/ai_narrative_llm.py`, `services/atems_ask_ai_context.py`, `services/atems_pii_redaction.py`, `utils/auth_helpers.py`; EDIT `atems.py`; NEW `tests/test_ai_trust_boundary.py`, `tests/test_atems_pii_redaction.py`.

**Operator steps:**

```bash
cd /home/ansible/atems
pytest tests/test_atems_pii_redaction.py tests/test_ai_trust_boundary.py -v
# Log in via browser; copy session cookie or use test client with login
curl -fsS -X POST http://127.0.0.1:5000/api/ai/ask \
  -H "Content-Type: application/json" \
  -H "Cookie: session=<session>" \
  -d '{"page":"dashboard","question":"How many tools are overdue for calibration?","context":{}}'
```

**Exit criteria:** Unauthenticated → 401; authenticated → 200; activity log row has `metadata.trust_zone: app_authenticated`; redaction tests pass (no email/phone in captured prompt fixtures).

---

### Stage 3 — Jinja2 Ask AI dock (MVP UI)

**Prerequisites:** Stage 2 green.

**Files:** NEW `templates/partials/ai_dock.html`, `static/js/ai_dock.js`; EDIT `templates/base.html`, `dashboard.html`, `reports.html`, `settings.html`.

**Operator steps:** Sign in as `user` or `admin` → open Dashboard → submit Ask AI question about calibration counts.

**Exit criteria:** Dock visible on three pages; theme matches slate/sky; answers reference dashboard aggregates; kiosk `/checkinout` has **no** dock.

---

### Stage 4 — Admin AI Monitor + admin explain

**Prerequisites:** Stage 3 green.

**Files:** NEW `blueprints/admin_ai.py`, `templates/settings_ai_monitor.html`; EDIT `settings.html`.

**Operator steps:** Sign in as admin → Settings → AI Monitor; non-admin user gets 403 on `/api/admin/ai/monitor`.

**Exit criteria:** Admin sees last 50 LLM calls; `POST /api/admin/ai/explain` returns triage summary with `trust_zone: internal`.

---

### Stage 5 — RAG over domain docs

**Prerequisites:** Stage 4 green; `embed` alias smoke on brain.

**Files:** NEW `services/atems_rag.py`, `scripts/rag/index_atems_corpus.py`; EDIT `atems_ask_ai_context.py`.

**Operator steps:**

```bash
docker compose exec atems-api python scripts/rag/index_atems_corpus.py
pytest tests/test_atems_rag_smoke.py -v
```

**Exit criteria:** Ask AI cites `docs/AFI_21_101_COMPLIANCE.md` or tool status enum; indexer audit confirms zero `users` rows indexed.

---

### Stage 6 — Agentic orchestrator jobs

**Prerequisites:** Stage 5 green; `ALFA_AI_API_TOKEN` set.

**Files:** NEW `services/alfa_orchestrator_client.py`; admin job trigger route or script.

**Exit criteria:** Calibration digest job produces markdown artifact; no PII in orchestrator payload.

---

### Stage 7 — Dev-time (AGENTS.md, codegen, CI)

**Prerequisites:** Stage 4 minimum.

**Exit criteria:** Codegen scripts run; PR triage workflow posts on test PR.

---

### Stage 8 — Fine-tune capture (opt-in)

**Prerequisites:** Stage 4 green; operator sign-off.

**Exit criteria:** Export JSONL passes redaction scanner; default env leaves capture disabled.

---

**Estimated stages-to-MVP:** Stages **0–3** (preflight → client → ask API → Jinja dock) = **4 stages**.

---

## 5. Risks, Rollback, & Single-Owner Compliance

### Route / auth map (discovered)

| Class | Routes |
|-------|--------|
| **Public** | `/`, `/splash`, `/login`, `/logout`, `/api/health`, `/checkinout`, `/api/checkinout`, `/api/user-by-badge` |
| **Authenticated** | `/dashboard`, `/app/*`, `/selftest`, `/logs`, `/settings`, `/reports`, `/import`, most `/api/*` |
| **Admin (Flask-Admin + AI Monitor)** | Flask-Admin `admin.index` (`UserView.is_accessible`, `user.py:74-77`); AI Monitor Stage 4 (`is_admin()`) |

### PII redaction targets (mandatory)

| Data class | Rule |
|------------|------|
| User email / phone | Strip from prompts and logs; use username or user_id only |
| Badge ID | Never send to LLM; use opaque "User A" in aggregates |
| Supervisor/manager contact fields | Exclude from RAG and Ask AI context |
| `password_hash` | **Never** log or prompt |
| Import CSV rows | Do not embed raw upload in Ask AI |
| Checkout history | Aggregates OK; no full username lists in fine-tune capture |

### systemd vs Docker ownership

| Doc | Claims |
|-----|--------|
| `README.md:22-39` | Docker Compose **recommended for production** |
| `PORT_INFO.md:3` | "ATEMS runs **systemd**" — **stale** |
| `DEPLOY_NOW.md:3` | systemd via `RUN_ON_SERVER.md` |
| `docker-compose.yml:67-68` | Correct `127.0.0.1:5000:5000` |

**Production single owner on `.105`:** Docker Compose `atems-api`. `atems.service` must be **disabled/stopped** when Compose runs. `deploy_atems_postgres.sh` is the canonical bring-up script.

### Failure modes

| Failure | Behavior |
|---------|----------|
| LiteLLM down | Ask AI shows graceful message; check-in/out and reports unaffected |
| Redaction test fails | **Block deploy** |
| Brain UFW blocks `.105` | `/api/health/detailed` flags `connection_refused` |

### Backout per stage

| Stage | Backout |
|-------|---------|
| 1 | `LITELLM_ENABLED=false` |
| 2–3 | Remove AI blueprints; hide dock partial |
| 4 | Remove admin AI routes |
| 5–8 | Disable RAG/jobs/capture flags |

---

## 6. Validation & Evaluation

Map to `alfa-ai/docs/EVALUATION_FRAMEWORK.md`:

| Feature | Eval suite | atems scenario (gate) |
|---------|------------|----------------------|
| Ask AI on Dashboard | doc_maker `factual_consistency_score` | Answer matches dashboard calibration_overdue count |
| Ask AI on Reports | researcher `source_relevance_score` | Correctly explains usage vs calibration vs inventory report types |
| PII redaction | debugger `reproduction_accuracy_rate` | Fixture user row → zero email/phone in LiteLLM prompt capture |
| Admin explain | doc_maker `factual_consistency_score` | Identifies ERROR pattern in sample `atems.log` snippet |
| RAG retrieval | researcher `source_relevance_score` | Retrieved chunk from `docs/AFI_21_101_COMPLIANCE.md` |
| Codegen scripts | coder `build_pass_rate` | Generated route stub passes `py_compile` |
| Calibration digest job | doc_maker `coverage_score` | Digest includes overdue + due-30 counts; no emails |

**Redaction-leak test (mandatory — adapted from auth-service plan):**

```python
FORBIDDEN_PATTERNS = [
    r"@[\w.-]+\.\w+",                    # email
    r"\b\d{10}\b",                       # 10-digit phone (atems User.phone)
    r"password_hash|SECRET_KEY",
    r"Bearer eyJ",                       # session/JWT leakage
]
```

Record pass/fail in `docs/eval/atems_litellm_gate.json` before production alias promotion.

---

## 7. Open Questions / Resolved Decisions

### Resolved (policy picks — no Option B/C/D)

- LiteLLM-only via `http://192.168.0.111:8413` (no direct Ollama for app chat).
- No `public_web` / `public-chat` surface.
- Sync **`requests.Session`** HTTP client (not async httpx, not Flask async views).
- Jinja2 partial dock on primary pages; React dock deferred to Stage 3b.
- **`admin` role** gates AI Monitor (matches Flask-Admin gate).
- Compose port **`127.0.0.1:5000:5000`** already correct — no port fix needed.
- Archetype: **contracts-bot app-auth dock** + **PII redaction discipline**.

### Single decision questions (user must confirm before Stage 1)

1. **Production process owner:** Confirm Docker Compose `atems-api` as the sole owner of port 5000 on `.105` and disable `atems.service` when Compose is active?
2. **Ask AI page scope for MVP:** Confirm Dashboard + Reports + Settings only (exclude kiosk `/checkinout` until that route requires login)?

---
