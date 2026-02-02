# Deploy ATEMS — Step-by-step

Use this to deploy to the Ubuntu server (e.g. 192.168.0.105) so the app is live at **https://atems.alfaquantumdynamics.com**.

---

## Prerequisites

- DNS: **atems.alfaquantumdynamics.com** points to the server IP (or use IP for testing).
- SSH access to the server as **ansible** (or adjust paths in nginx + systemd).

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

2. **Clone and setup** (one-time):
   ```bash
   cd ~
   git clone https://github.com/Curt-Alfrey-s-Org/ATEMS.git atems
   cd atems
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure .env** (one-time):
   ```bash
   cd ~/atems
   cp .env.example .env
   # Edit .env: set SECRET_KEY, SQLALCHEMY_DATABASE_URI (e.g. sqlite:////home/ansible/atems/atems.db), DEBUG=False
   ```

4. **Initialize database** (one-time):
   ```bash
   cd ~/atems
   source .venv/bin/activate
   flask db upgrade
   # Optional: python scripts/seed_demo_users.py && python scripts/seed_tools.py
   ```

5. **Build frontend** (one-time, optional):
   ```bash
   cd ~/atems/frontend
   npm install && npm run build
   cd ..
   ```

6. **Nginx** (one-time):
   - From Mint: `scp web-sites-server/nginx-atems.conf ansible@192.168.0.105:~/`
   - On server:
     ```bash
     sudo mv ~/nginx-atems.conf /etc/nginx/sites-available/atems
     sudo ln -sf /etc/nginx/sites-available/atems /etc/nginx/sites-enabled/
     sudo nginx -t && sudo systemctl reload nginx
     ```

7. **HTTPS** (one-time):
   ```bash
   sudo certbot --nginx -d atems.alfaquantumdynamics.com
   ```

8. **Start ATEMS** (one-time, then systemd keeps it running):
   - From Mint: `scp web-sites-server/atems.service ansible@192.168.0.105:~/`
   - On server:
     ```bash
     sudo mv ~/atems.service /etc/systemd/system/
     sudo systemctl daemon-reload
     sudo systemctl enable --now atems
     sudo systemctl status atems
     ```

9. **Open in browser:** https://atems.alfaquantumdynamics.com (or http://IP if no DNS/cert yet).

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
./scripts/deploy.sh
sudo systemctl restart atems
```

---

## Quick checklist

| Step            | Command / action |
|-----------------|------------------|
| Sync to server  | `./scripts/deploy-to-server.sh ansible@192.168.0.105` (from ATEMS root) |
| One-time: .env  | Copy .env.example to .env, set SECRET_KEY, DB URI, DEBUG=False |
| One-time: DB    | On server: `flask db upgrade` |
| One-time: Nginx | Copy `nginx-atems.conf` → sites-available, enable, reload |
| One-time: HTTPS | `sudo certbot --nginx -d atems.alfaquantumdynamics.com` |
| One-time: API   | Copy `atems.service` → systemd, enable, start |
| Update          | `sudo systemctl restart atems` |
