# ATEMS — Website deployment

Files for deploying ATEMS to https://atems.alfaquantumdynamics.com (same pattern as rankings-bot).

| File | Purpose |
|------|---------|
| `traefik-atems.yml` | Traefik dynamic config (primary — no Nginx) |
| `atems.service` | systemd unit for gunicorn |
| `TRAEFIK_ATEMS.md` | API/HTTP/Traefik setup (mirrors rankings-bot) |
| `DEPLOY_NOW.md` | Step-by-step deploy instructions |
| `PORT_INFO.md` | Port scheme (same-host vs bot-host) |
| Traefik | Use `traefik-atems.yml` (no Nginx) |

See **TRAEFIK_ATEMS.md** for the full setup on the ansible server.
