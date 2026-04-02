# ATEMS — Website deployment

Files for deploying ATEMS to https://atems.alfaquantumdynamics.com.

| File | Purpose |
|------|---------|
| `nginx-atems.conf` | Nginx site config (primary reverse proxy) |
| `atems.service` | systemd unit for gunicorn |
| `DEPLOY_NOW.md` | Step-by-step deploy instructions |
| `PORT_INFO.md` | Port scheme |
| Nginx | Use `nginx-atems.conf` |

See **NGINX_DEPLOYMENT.md** for the current Nginx setup on the ansible server.
