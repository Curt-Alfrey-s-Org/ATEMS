# ALFa AI — how to use (atems)

**App:** ATEMS — Tool & Equipment Management (Flask, port 5000 on `.105`)  
**Brain:** `192.168.0.111` (LiteLLM `:8413`, orchestrator `:8420`)  
**Authority:** [`.cursor/plans/ALFA_AI_INTEGRATION_PLAN.md`](../.cursor/plans/ALFA_AI_INTEGRATION_PLAN.md)  
**Host contract:** [`/home/ansible/.cursor/plans/ALFA_AI_INTEGRATION_PLAN_HOST_105.md`](/home/ansible/.cursor/plans/ALFA_AI_INTEGRATION_PLAN_HOST_105.md)

---

## Where the brain lives

| Component | Location | From atems container / `.105` shell |
|-----------|----------|-------------------------------------|
| LiteLLM proxy | `.111` | `http://192.168.0.111:8413` |
| ALFa API + operator UI | `.111` | `http://192.168.0.111:8420` |
| Operator console | `.111` | `http://192.168.0.111:8420/operator/` |
| atems API | `.105` loopback | `http://127.0.0.1:5000` |
| atems Postgres | `.105` | `127.0.0.1:5436` → container `5432` |

**Do not** set `LITELLM_BASE_URL=http://127.0.0.1:8413` on `.105` — brain ports are not published on the apps host.

---

## What you can run

| Capability | Who | Where | Model / zone |
|------------|-----|-------|--------------|
| **Ask AI dock** | Signed-in users | Dashboard, Reports, Settings → `POST /api/ai/ask` | `app-chat` / `app_authenticated` |
| **Admin log triage** | Admin | Settings → AI Monitor → `POST /api/admin/ai/explain` | `code` / `internal` |
| **AI Monitor** | Admin | Settings → AI Monitor | reads `ollama_activity_log` |
| **Agentic digests** | Admin / cron | `POST /api/runs` on brain | `agent` / `internal` |
| **Operator console** | Operator (browser) | `http://192.168.0.111:8420/operator/` | server-side LiteLLM |

There is **no** public anonymous Ask AI in atems MVP.

---

## Prerequisites

1. Brain healthy on `.111`:

```bash
curl -fsS http://192.168.0.111:8413/health/liveliness
curl -fsS http://192.168.0.111:8420/health
```

2. atems running (Docker — canonical on `.105`):

```bash
cd /home/ansible/atems
./deploy_atems_postgres.sh
# or after initial deploy:
docker compose ps atems-api atems-postgres
curl -fsS http://127.0.0.1:5000/api/health
```

3. **Single owner on port 5000** — do not run `atems.service` and Docker `atems-api` together:

```bash
sudo systemctl disable --now atems 2>/dev/null || true
sudo lsof -ti :5000   # should be Docker proxy only
```

---

## Enable LiteLLM env block

Add to `/home/ansible/atems/.env` (and ensure `docker-compose.yml` passes vars to `atems-api`):

```env
LITELLM_ENABLED=true
LITELLM_BASE_URL=http://192.168.0.111:8413
LITELLM_API_KEY=<same as LITELLM_MASTER_KEY on .111 unless using virtual key>
LITELLM_API_KEY_APP=<optional; else LITELLM_API_KEY>
LITELLM_MODEL_CHAT=app-chat
LITELLM_TIMEOUT=600

ALFA_AI_API_TOKEN=<brain operator token>
ALFA_BRAIN_URL=http://192.168.0.111:8420
```

Recreate the API container after editing (restart alone does not reload env):

```bash
cd /home/ansible/atems
docker compose up -d --no-deps --force-recreate atems-api
```

---

## Verify with curl

**Brain direct (from `.105` shell):**

```bash
source /home/ansible/atems/.env
curl -fsS "${LITELLM_BASE_URL}/health/liveliness"
curl -fsS -X POST "${LITELLM_BASE_URL}/v1/chat/completions" \
  -H "Authorization: Bearer ${LITELLM_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"app-chat","messages":[{"role":"user","content":"Reply OK only."}],"max_tokens":10}'
```

**atems detailed health (after Stage 1):**

```bash
curl -fsS http://127.0.0.1:5000/api/health/detailed | python3 -m json.tool
```

Expect `litellm.base_url` = `http://192.168.0.111:8413` and `litellm.status` = `healthy` when brain is up.

**Ask AI (after Stage 2 — requires Flask-Login session cookie):**

Sign in at `http://127.0.0.1:5000/login`, then use browser devtools to copy the `session` cookie, or use the in-app dock after Stage 3.

---

## AI Monitor (admin)

After Stage 4:

1. Sign in as **admin** (role `admin` in DB or env admin user).
2. Open **Settings → AI Monitor**.
3. Verify rows show `feature`, `model`, `trust_zone`, token counts, errors.

Non-admin users receive **403** on `/api/admin/ai/monitor`.

Telemetry table: `ollama_activity_log` in atems Postgres (`atems` database).

---

## Domain-specific tips

- **Calibration questions:** Ask about overdue counts, due-in-30/60/90 buckets — the dashboard bundle supplies aggregates, not raw tool serials with custodian PII.
- **AFI 21-101 / CTK:** After Stage 5 RAG, Ask AI can cite `docs/AFI_21_101_COMPLIANCE.md` and explain MIL/inventory report usage.
- **Reports:** Ask "what report shows overdue returns?" — context comes from the Reports page registration.
- **Kiosk check-in/out:** `/checkinout` is intentionally public for scan guns; **Ask AI is not shown there** and must not receive badge lookups.
- **Import:** Do not paste CSV contents into Ask AI; use Import UI for bulk loads.

---

## When ALFa AI is down

| Surface | Without AI |
|---------|------------|
| Ask AI dock | Shows "AI temporarily unavailable"; rest of app works |
| Admin explain | Returns 503 with message; Monitor still shows historical rows |
| Check-in/out, reports, import | Unaffected |
| Agentic jobs | Skip run; log warning |

**Quick checklist:**

```bash
curl -fsS --max-time 3 http://192.168.0.111:8413/health/liveliness || echo "LiteLLM down"
curl -fsS --max-time 3 http://192.168.0.111:8420/health || echo "ALFa API down"
curl -fsS http://127.0.0.1:5000/api/health
```

Fix brain on `.111` per `alfa-ai/docs/DOCKGE_111_OPERATOR.md`. atems keeps serving inventory operations.

---

## Production hardening

Before relying on Ask AI in production:

- Strong `LITELLM_MASTER_KEY` on `.111` and matching `LITELLM_API_KEY` in atems `.env`
- Set `ALFA_AI_REQUIRE_API_AUTH=true` on brain when using orchestrator jobs
- Rotate default demo passwords (`admin/admin123`, `user/user123`) — see `README.md:18`
- Complete trust-zone checklist in `docs/ALFA_AI_TRUST_ZONES_AND_ROLLOUT.md` (after Stage 4)
- Run redaction tests: `pytest tests/test_atems_pii_redaction.py -v`

---

## Related docs

- [ALFA_AI_INTEGRATION_PLAN.md](../.cursor/plans/ALFA_AI_INTEGRATION_PLAN.md)
- [ALFA_AI_HOST_105_USAGE.md](/home/ansible/docs/ALFA_AI_HOST_105_USAGE.md)
- [USER_GUIDE.md](USER_GUIDE.md)
- [AFI_21_101_COMPLIANCE.md](AFI_21_101_COMPLIANCE.md)
- [PORT_INFO.md](../PORT_INFO.md) — note: update ownership line to Docker when Stage 0 completes
- [alfa-ai PORT_ASSIGNMENTS.md](/home/ansible/alfa-ai/docs/PORT_ASSIGNMENTS.md)

---
