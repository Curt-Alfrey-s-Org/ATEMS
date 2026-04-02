# Port Info for Cursor — ATEMS only

**ATEMS runs in Docker. Nginx + Cloudflare tunnel (cf-alfa) handle routing.**

## ATEMS on server (192.168.0.105)

| Port | App  | Subdomain                     | Backend |
|------|------|--------------------------------|---------|
| 5000 | ATEMS | atems.alfaquantumdynamics.com | 127.0.0.1:5000 |

## Verify

- **Same-host:** `curl -s http://127.0.0.1:5000/ | head -c 100`
- **Public URL:** `curl -s https://atems.alfaquantumdynamics.com/ | head -c 100`

See **RUN_ON_SERVER.md** and **.github/PORT_ASSIGNMENTS.md** for details.
