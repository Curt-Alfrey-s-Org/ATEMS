# Port Info — All on Server (192.168.0.105)

**No Docker for apps, no Nginx.** Traefik handles routing.

## Server-only (ATEMS & rankings-bot on 192.168.0.105)

| Port | App | Subdomain | Traefik backend |
|------|-----|-----------|-----------------|
| 8001 | Rankings Bot | rankings-bot.alfaquantumdynamics.com | host.docker.internal:8001 |
| 5000 | ATEMS | atems.alfaquantumdynamics.com | 192.168.0.105:5000 |

## ATEMS verify

`curl -s http://127.0.0.1:5000/ | head -c 100`

See **TRAEFIK_ATEMS.md** for full setup.
