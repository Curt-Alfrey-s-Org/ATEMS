# ATEMS Migration: Traefik → Nginx-Only Architecture
**Date:** 2026-02-10  
**Status:** ✅ Complete

---

## Overview

ATEMS has been successfully migrated from a **Traefik-based reverse proxy** (Docker-based) to an **Nginx-only architecture** for HTTP/HTTPS routing. This simplifies deployment and removes Docker dependency for the reverse proxy layer.

### Before (Traefik)
```
Internet (HTTPS) → Cloudflare → Webserver 192.168.0.105
  ├─ Traefik (Docker) on ports 80/443 (via host.docker.internal)
  └─ ATEMS (systemd) on port 5000
```

### After (Nginx)
```
Internet (HTTPS) → Cloudflare → Webserver 192.168.0.105
  ├─ Nginx on ports 80/443 (native)
  └─ ATEMS (systemd) on port 5000
```

---

## Changes Made

### Files Deleted
- ✅ `/home/ansible/atems/traefik-atems.yml` — Removed root-level Traefik config
- ✅ `/home/ansible/atems/web-sites-server/traefik-atems.yml` — Removed source Traefik config

### Files Updated
1. **TRAEFIK_ATEMS.md** — Marked deprecated with migration notes
2. **DEPLOY_NOW.md** — Updated checklist: replaced Traefik with Nginx setup
3. **RUN_ON_SERVER.md** — Replaced Step 8 (Traefik) with Nginx + Let's Encrypt (Steps 8-9)
4. **PORT_INFO.md** — Updated port mapping to reflect Nginx instead of Traefik
5. **README.md** — Removed traefik-atems.yml reference, added Nginx config note
6. **gunicorn.conf.py** — Updated comment to generic "reverse proxy"
7. **.env.example** — Updated ProxyFix comment to generic "reverse proxy"

### Files Unchanged
- ✅ `NGINX_DEPLOYMENT.md` — Already ready as primary guide
- ✅ `web-sites-server/nginx-atems.conf` — Already prepared for Nginx deployment
- ✅ `web-sites-server/atems.service` — No changes (still uses same systemd unit)
- ✅ Flask code (ProxyFix middleware works with any reverse proxy)
- ✅ React frontend (no changes)

---

## Deployment Instructions (Nginx Path)

### One-Time Server Setup

1. **System packages:**
   ```bash
   sudo apt install nginx certbot python3-certbot-nginx
   ```

2. **Clone and configure ATEMS** (see RUN_ON_SERVER.md steps 1–7)

3. **Install Nginx site config:**
   ```bash
   sudo cp web-sites-server/nginx-atems.conf /etc/nginx/sites-available/atems
   sudo ln -s /etc/nginx/sites-available/atems /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```

4. **Enable HTTPS with Let's Encrypt:**
   ```bash
   sudo certbot --nginx -d atems.alfaquantumdynamics.com
   ```

5. **Verify:**
   ```bash
   curl -s https://atems.alfaquantumdynamics.com/ | head -c 100
   ```

### Updating ATEMS

```bash
cd ~/atems
git pull
source .venv/bin/activate
pip install -r requirements.txt
flask db upgrade
./scripts/build_on_server.sh --restart
sudo systemctl reload nginx  # if nginx config changes
```

---

## Benefits of Nginx

| Aspect | Traefik | Nginx |
|--------|---------|-------|
| **Setup** | Docker container + dynamic config | Native Nginx package + static config |
| **Complexity** | Higher (Docker networking) | Lower (traditional reverse proxy) |
| **Dependency** | Docker required | No Docker needed |
| **Configuration** | YAML dynamic config | Traditional nginx.conf |
| **SSL/TLS** | Manual (requires Traefik routing) | Native certbot integration |
| **Performance** | Good (Traefik overhead) | Excellent (minimal overhead) |

---

## Troubleshooting

### Issue: "Bad Gateway" from Nginx
- Verify ATEMS systemd service is running: `sudo systemctl status atems`
- Check ATEMS is listening on 127.0.0.1:5000: `curl -s http://127.0.0.1:5000/`
- Check Nginx error log: `tail -f /var/log/nginx/error.log`

### Issue: HTTPS not working
- Run certbot again: `sudo certbot --nginx -d atems.alfaquantumdynamics.com`
- Check Nginx config syntax: `sudo nginx -t`
- Reload Nginx: `sudo systemctl reload nginx`

### Issue: Database locked (SQLite)
- Set `WEB_CONCURRENCY=1` in `.env` to limit gunicorn workers to 1
- Or switch to PostgreSQL for production

---

## What's Different for Users?

**Nothing.** The public interface remains identical:
- **URL:** Still `https://atems.alfaquantumdynamics.com`
- **Features:** Unchanged
- **Login credentials:** Same
- **API endpoints:** Same

---

## References

- **Setup:** [RUN_ON_SERVER.md](RUN_ON_SERVER.md) (Steps 1–10 now Nginx-based)
- **Deployment:** [NGINX_DEPLOYMENT.md](NGINX_DEPLOYMENT.md)
- **Nginx config:** [web-sites-server/nginx-atems.conf](web-sites-server/nginx-atems.conf)
- **Deprecated (archive):** [TRAEFIK_ATEMS.md](TRAEFIK_ATEMS.md)

---

## Migration Checklist

If upgrading an existing Traefik-based deployment:

- [ ] Backup current ATEMS instance
- [ ] Ensure Nginx is installed: `sudo apt install nginx certbot python3-certbot-nginx`
- [ ] Remove Traefik config: `sudo rm /etc/traefik/dynamic/atems.yml && sudo docker restart traefik`
- [ ] Install Nginx config: `sudo cp web-sites-server/nginx-atems.conf /etc/nginx/sites-available/atems && sudo ln -s ...`
- [ ] Verify Nginx: `sudo nginx -t && sudo systemctl reload nginx`
- [ ] Enable HTTPS: `sudo certbot --nginx -d atems.alfaquantumdynamics.com`
- [ ] Test: `curl -s https://atems.alfaquantumdynamics.com/` (verify 200 OK)
- [ ] Verify systemd service: `sudo systemctl status atems`

---

**Migration completed:** 2026-02-10  
**Reviewed by:** Architecture standardization initiative  
**Status:** Ready for production use
