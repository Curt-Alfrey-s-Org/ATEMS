# ATEMS behind Traefik — Setup on Ansible (Same as Rankings Bot)

**Cursor: Use this Traefik setup, not Nginx.** Mirrors the rankings-bot pattern.

Use the **existing Traefik** reverse proxy on the webserver (192.168.0.105). ATEMS runs via systemd on the same host; Traefik (in Docker) proxies to it via `host.docker.internal`.

## Architecture (from rankings-bot SERVER_SETUP_REVIEW)

```
Internet (HTTPS)
       ↓
Cloudflare (DNS + optional HTTPS)
       ↓
Webserver 192.168.0.105
       ├── Traefik (Docker) — ports 80/443
       │        ↓
       │   Host rule: atems.alfaquantumdynamics.com
       │        ↓
       │   Backend: http://host.docker.internal:5000
       │
       └── ATEMS (systemd, user ansible) — port 5000
                ├── Serves / (Flask templates)
                ├── Serves /app (React SPA from static/app/)
                └── Serves /api/* (Flask API)
```

## API & HTTP (why it works)

1. **ProxyFix** — ATEMS has `ProxyFix` in `atems.py` (enabled when `DEBUG=False` or `USE_PROXY_FIX=true`). Traefik sends `X-Forwarded-Proto`, `X-Forwarded-Host`, etc. ProxyFix makes Flask generate correct `https://` URLs and `url_for()`.
2. **Single backend** — Traefik sends all traffic for `atems.alfaquantumdynamics.com` to one backend. No separate static server.
3. **host.docker.internal** — From inside the Traefik container, the host is `host.docker.internal`. The API must listen on **0.0.0.0:5000** so it’s reachable.
4. **If 502** — Try `http://172.17.0.1:5000` in the Traefik config if `host.docker.internal` isn’t available on your Docker setup.

## Port scheme (same-host deployment)

| Service  | Host          | Port | Subdomain                        |
|----------|---------------|------|----------------------------------|
| Rankings Bot | 192.168.0.105 | 8001 | rankings-bot.alfaquantumdynamics.com |
| ATEMS    | 192.168.0.105 | 5000 | atems.alfaquantumdynamics.com    |
| Traefik  | 192.168.0.105 | 80/443 | —                              |

## Steps

### 1. Deploy ATEMS to the server

From Mint:
```bash
# Use ATEMS deploy script if available, or rsync manually
cd /home/n4s1/ATEMS
./scripts/deploy-to-server.sh   # or rsync to ansible@192.168.0.105:~/atems/
```

### 2. One-time: systemd service on server

From Mint:
```bash
scp /home/n4s1/ATEMS/web-sites-server/atems.service ansible@192.168.0.105:~/
```

On server (SSH ansible@192.168.0.105):
```bash
sudo mv ~/atems.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now atems
sudo systemctl status atems
```

ATEMS must bind **0.0.0.0:5000** (gunicorn in `atems.service` already does this).

### 3. Add Traefik dynamic config

From Mint:
```bash
scp /home/n4s1/ATEMS/web-sites-server/traefik-atems.yml ansible@192.168.0.105:~/
```

On server:
```bash
sudo cp ~/traefik-atems.yml /etc/traefik/dynamic/atems.yml
```

### 4. Restart Traefik

```bash
sudo docker restart traefik
sleep 2
```

### 5. Verify

```bash
# On server
curl -s http://127.0.0.1:5000/ | head -c 200

# From anywhere (HTTPS)
curl -k https://atems.alfaquantumdynamics.com/
```

### 6. DNS (Cloudflare)

Add **A record**: **atems.alfaquantumdynamics.com** → **192.168.0.105**

## Summary

| Item      | Value                                |
|-----------|--------------------------------------|
| Subdomain | atems.alfaquantumdynamics.com        |
| Backend   | http://host.docker.internal:5000     |
| Config    | /etc/traefik/dynamic/atems.yml       |
| Nginx     | Not used                             |
| ProxyFix  | Yes (in atems.py for correct HTTPS)  |

All apps run on the webserver (192.168.0.105). See **PORT_INFO.md** for the full port scheme.
