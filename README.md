# ATEMS — Automated Tool & Equipment Management System

Inventory control software for tool rooms, warehouses, and supply chain operations.

**Workspace:** [All bots overview](../docs/BOTS_OVERVIEW.md) · [Quick reference](../docs/QUICK_REFERENCE.md)

## Shared dependency cache

This repo pulls pip and npm deps through the server-wide cache at **`/srv/dep-cache`** so containers and host builds don't redownload packages between rebuilds. `Dockerfile` uses BuildKit cache mounts with shared id `bots-pip`; `scripts/build_on_server.sh` points npm at `/srv/dep-cache/npm`. Manage with `/srv/dep-cache/bin/dep-cache {status,prune --older-than 30d,clear}`. Details: `/srv/dep-cache/README.md`.

## Production Ports (Server)

See `/home/ansible/.github/PORT_ASSIGNMENTS.md` for the canonical list.

- **API host binding:** `127.0.0.1:5000`
- **Database host binding:** `5436:5432`

**Login:** Root `/` shows a splash screen with login. Credentials: user/user123 · admin/admin123. Run `python scripts/seed_demo_users.py` to create demo users.

---

## Quick Start (Docker + PostgreSQL)

**Recommended for production:**

```bash
cd /home/ansible/atems

# 1. Configure environment
cp .env.example .env
nano .env  # Set POSTGRES_PASSWORD and SECRET_KEY

# 2. Deploy with script
./deploy_atems_postgres.sh

# 3. Access ATEMS
# http://localhost:5000
# Login: admin/admin123
```

**Database:** PostgreSQL 16 (port 5436) · See [POSTGRESQL_MIGRATION.md](POSTGRESQL_MIGRATION.md)

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
