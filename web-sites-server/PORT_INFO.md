# Port Info for Cursor — ATEMS only

**No Docker for app, no Nginx.** Traefik handles routing.

## ATEMS on server (192.168.0.105)

| Port | App  | Subdomain                       | Traefik backend            |
|------|------|----------------------------------|----------------------------|
| 5000 | ATEMS | atems.alfaquantumdynamics.com   | host.docker.internal:5000  |

## Verify

- **Same-host:** `curl -s http://127.0.0.1:5000/ | head -c 100`
- **From elsewhere:** `curl -s http://192.168.0.105:5000/ | head -c 100`

See **TRAEFIK_ATEMS.md** for full setup.
