# ATEMS — Website deployment

Files for deploying ATEMS to https://atems.alfaquantumdynamics.com (same pattern as rankings-bot).

| File | Purpose |
|------|---------|
| `nginx-atems.conf` | Nginx server block (proxy to gunicorn on port 5000) |
| `atems.service` | systemd unit for gunicorn |
| `DEPLOY_NOW.md` | Step-by-step deploy instructions |

See **DEPLOY_NOW.md** for full steps.
