# Port Info for Cursor

**No Docker for apps, no Nginx.** Traefik handles routing.

## Same-host (ATEMS & rankings-bot on webserver 192.168.0.105)

| Port | App | Subdomain | Traefik backend |
|------|-----|-----------|-----------------|
| 8001 | Rankings Bot | rankings-bot.alfaquantumdynamics.com | host.docker.internal:8001 |
| 5000 | ATEMS | atems.alfaquantumdynamics.com | host.docker.internal:5000 |

## All on server (192.168.0.105)

| Port | App | Subdomain |
|------|-----|-----------|
| 8000 | Market Pie5 Bot | market-bot.alfaquantumdynamics.com |
| 8001 | Rankings Bot | rankings-bot.alfaquantumdynamics.com |
| 5000 | ATEMS | atems.alfaquantumdynamics.com |

## ATEMS verify

- **Same-host:** `curl -s http://127.0.0.1:5000/ | head -c 100`
- **From elsewhere:** `curl -s http://192.168.0.105:5000/ | head -c 100`

See **TRAEFIK_ATEMS.md** for full setup.
