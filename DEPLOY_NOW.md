# Deploy ATEMS — Step-by-step

**Run ATEMS fully on the server (192.168.0.105).** See **RUN_ON_SERVER.md** for the primary flow.

**Use Nginx as reverse proxy** — See **NGINX_DEPLOYMENT.md** for the full deployment flow. For legacy Traefik setup, see **TRAEFIK_ATEMS.md** (deprecated).

---

## Prerequisites

- DNS: **atems.alfaquantumdynamics.com** points to the server IP (or use IP for testing).
- SSH access to the server as **ansible** (or adjust paths in Traefik + systemd).

---

## Option A: Deploy from your Mint machine (build + sync)

1. **Build and sync** (from ATEMS repo root):
   ```bash
   cd /home/n4s1/ATEMS
   chmod +x scripts/deploy-to-server.sh
   ./scripts/deploy-to-server.sh ansible@192.168.0.105
   ```
   This builds the frontend (if present), rsyncs to `~/atems/` on the server, and prints the next steps.

2. **On the server** — SSH in and follow the one-time steps in Option B from step 3 onward.

---

## Option B: Deploy entirely on the server (clone + setup there)

1. **SSH to the server:**
   ```bash
   ssh ansible@192.168.0.105
   ```

2. **Follow RUN_ON_SERVER.md** for the full one-time setup (clone, venv, .env, db, frontend, systemd, Nginx).

---

## After first deploy — Updating

**If you use Option A (sync from Mint):**
- Run again: `./scripts/deploy-to-server.sh ansible@192.168.0.105`
- On server: `sudo systemctl restart atems`

**If you use Option B (git on server):**
```bash
ssh ansible@192.168.0.105
cd ~/atems
git pull
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=atems:create_app
flask db upgrade
./scripts/build_on_server.sh --restart
```

---

## Quick checklist (Nginx path)

| Step               | Command / action |
|--------------------|------------------|
| Sync to server     | `./scripts/deploy-to-server.sh ansible@192.168.0.105` (from ATEMS root) |
| One-time: .env     | Copy .env.example to .env, set SECRET_KEY, DB URI, DEBUG=False |
| One-time: DB       | On server: `flask db upgrade` |
| One-time: systemd  | Copy `atems.service` → /etc/systemd/system/, daemon-reload, enable, start |
| One-time: Nginx    | Copy `web-sites-server/nginx-atems.conf` → /etc/nginx/sites-available/atems, link to sites-enabled, test, reload |
| One-time: HTTPS    | Run `sudo certbot --nginx -d atems.alfaquantumdynamics.com` |
| One-time: DNS      | Cloudflare A record atems.alfaquantumdynamics.com → 192.168.0.105 |
| Update             | `sudo systemctl restart atems` |
