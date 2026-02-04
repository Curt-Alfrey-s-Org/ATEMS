# ATEMS — Run Fully on Server (192.168.0.105)

Everything runs on the server. Repo lives there; build and run there.

## One-time setup on the server

1. **SSH in:**
   ```bash
   ssh ansible@192.168.0.105
   ```

2. **Clone ATEMS** (if not already):
   ```bash
   cd ~
   git clone https://github.com/Curt-Alfrey-s-Org/ATEMS.git atems
   cd atems
   ```

3. **Python venv and deps:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure .env:**
   ```bash
   cp .env.example .env
   # Edit: SECRET_KEY, SQLALCHEMY_DATABASE_URI (e.g. sqlite:////home/ansible/atems/atems.db), DEBUG=False
   ```

5. **Database:**
   ```bash
   export FLASK_APP=atems:create_app
   flask db upgrade
   ```

6. **Frontend** (needs Node.js: `sudo apt install nodejs npm`):
   ```bash
   chmod +x scripts/build_on_server.sh
   ./scripts/build_on_server.sh
   ```

7. **systemd:**
   ```bash
   sudo cp web-sites-server/atems.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now atems
   ```

8. **Traefik:**
   ```bash
   sudo cp web-sites-server/traefik-atems.yml /etc/traefik/dynamic/atems.yml
   sudo docker restart traefik
   ```

9. **DNS:** Cloudflare A record `atems.alfaquantumdynamics.com` → 192.168.0.105

---

## Updating (run on the server)

```bash
cd ~/atems
git pull
source .venv/bin/activate
pip install -r requirements.txt   # if deps changed
export FLASK_APP=atems:create_app
flask db upgrade                  # if migrations added
./scripts/build_on_server.sh --restart
```

---

## Quick reference

| Item     | Value                                |
|----------|--------------------------------------|
| Path     | ~/atems                              |
| Port     | 5000                                 |
| Build    | `./scripts/build_on_server.sh --restart` |
| Restart  | `sudo systemctl restart atems`       |
