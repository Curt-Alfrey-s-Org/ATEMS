# Port Info — ATEMS on Server (192.168.0.105)

**ATEMS runs systemd, Nginx handles HTTP/HTTPS routing.**

## ATEMS Architecture

| Port | Service | Purpose | Notes |
|------|---------|---------|-------|
| 5000 | ATEMS (gunicorn) | Flask app + API | Listens on 127.0.0.1:5000 (localhost only) |
| 80 | Nginx | HTTP reverse proxy | Public-facing, proxies to :5000 |
| 443 | Nginx | HTTPS reverse proxy | Public-facing (via Let's Encrypt), proxies to :5000 |

## Verify

**Local verification** (on server):
```bash
curl -s http://127.0.0.1:5000/ | head -c 100
```

**Public verification** (from anywhere):
```bash
curl -s https://atems.alfaquantumdynamics.com/ | head -c 100
```

See **NGINX_DEPLOYMENT.md** for full setup.
