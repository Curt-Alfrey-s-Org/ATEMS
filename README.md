# ATEMS — Automated Tool & Equipment Management System

Inventory control software for tool rooms, warehouses, and supply chain operations.

**Login:** Root `/` shows a splash screen with login. Credentials: guest/guest123 · user/user123 · admin/admin123. Run `python scripts/seed_demo_users.py` to create demo users.

---

## Deployment

Files for deploying ATEMS to https://alfaquantumdynamics.com/app/atems (same pattern as rankings-bot).

| File | Purpose |
|------|---------|
| `RUN_ON_SERVER.md` | **Primary** — run ATEMS fully on server 105 |
| `traefik-atems.yml` | Traefik dynamic config (no Nginx) |
| `atems.service` | systemd unit for gunicorn |
| `TRAEFIK_ATEMS.md` | API/HTTP/Traefik setup (mirrors rankings-bot) |
| `DEPLOY_NOW.md` | Step-by-step deploy instructions |
| `PORT_INFO.md` | Port scheme (same-host vs bot-host) |

See **RUN_ON_SERVER.md** for the full setup. **docs/ATEMS_TEST_REPORT.md** for test and splash login details.
