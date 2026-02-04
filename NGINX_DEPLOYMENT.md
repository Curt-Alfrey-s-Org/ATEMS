# ATEMS Nginx Deployment Guide
## Ubuntu Pro Server Configuration for https://atems.alfaquantumdynamics.com

This guide covers deploying ATEMS on Ubuntu Pro with Nginx as a reverse proxy.

---

## Prerequisites

- Ubuntu Pro server (20.04 LTS or newer)
- Domain: `atems.alfaquantumdynamics.com` pointing to your server IP
- Root or sudo access
- Python 3.8+ installed

---

## 1. Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git
```

---

## 2. Set Up ATEMS Application

### Clone and Configure

```bash
# Create application directory
sudo mkdir -p /var/www/atems
sudo chown $USER:$USER /var/www/atems
cd /var/www/atems

# Clone or copy ATEMS files
# (Assuming files are already on server or use git clone)

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Configure Environment

```bash
# Create production .env file
cat > .env << 'EOF'
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
SQLALCHEMY_DATABASE_URI=sqlite:////var/www/atems/atems_production.db
FLASK_ENV=production
DEBUG=False
EOF

# Initialize database
flask db upgrade
python scripts/seed_demo_users.py
python scripts/seed_50k_tools.py
python scripts/seed_fake_users_and_history.py
```

---

## 3. Create Systemd Service

Create `/etc/systemd/system/atems.service`:

```ini
[Unit]
Description=ATEMS - Advanced Tool & Equipment Management System
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/atems
Environment="PATH=/var/www/atems/.venv/bin"
ExecStart=/var/www/atems/.venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/var/www/atems/atems.sock \
    --timeout 120 \
    --access-logfile /var/log/atems/access.log \
    --error-logfile /var/log/atems/error.log \
    "atems:create_app()"

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Install Gunicorn and Set Permissions

```bash
# Install gunicorn
source /var/www/atems/.venv/bin/activate
pip install gunicorn

# Create log directory
sudo mkdir -p /var/log/atems
sudo chown www-data:www-data /var/log/atems

# Set permissions
sudo chown -R www-data:www-data /var/www/atems
sudo chmod -R 755 /var/www/atems

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable atems
sudo systemctl start atems
sudo systemctl status atems
```

---

## 4. Configure Nginx

Create `/etc/nginx/sites-available/atems`:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=atems_limit:10m rate=10r/s;

# Upstream
upstream atems_app {
    server unix:/var/www/atems/atems.sock fail_timeout=0;
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name atems.alfaquantumdynamics.com;
    
    # Certbot challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name atems.alfaquantumdynamics.com;

    # SSL certificates (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/atems.alfaquantumdynamics.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/atems.alfaquantumdynamics.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/atems_access.log;
    error_log /var/log/nginx/atems_error.log;

    # Max upload size
    client_max_body_size 10M;

    # Static files
    location /static {
        alias /var/www/atems/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Application
    location / {
        limit_req zone=atems_limit burst=20 nodelay;
        
        proxy_pass http://atems_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

### Enable Site and Obtain SSL Certificate

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/atems /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Obtain SSL certificate
sudo certbot --nginx -d atems.alfaquantumdynamics.com --non-interactive --agree-tos -m admin@alfaquantumdynamics.com

# Reload nginx
sudo systemctl reload nginx
```

---

## 5. Firewall Configuration

```bash
# Allow HTTP, HTTPS, and SSH
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

---

## 6. Monitoring and Maintenance

### Check Service Status

```bash
# ATEMS application
sudo systemctl status atems
sudo journalctl -u atems -f

# Nginx
sudo systemctl status nginx
sudo tail -f /var/log/nginx/atems_access.log
sudo tail -f /var/log/nginx/atems_error.log
```

### Database Backup

```bash
# Create backup script
cat > /usr/local/bin/backup-atems-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/atems"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
cp /var/www/atems/atems_production.db $BACKUP_DIR/atems_db_$DATE.db
find $BACKUP_DIR -name "atems_db_*.db" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-atems-db.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-atems-db.sh") | crontab -
```

### SSL Certificate Renewal

Certbot auto-renews certificates. Test renewal:

```bash
sudo certbot renew --dry-run
```

---

## 7. Performance Tuning

### Nginx Worker Processes

Edit `/etc/nginx/nginx.conf`:

```nginx
worker_processes auto;
worker_connections 1024;
```

### Gunicorn Workers

Recommended: `(2 x CPU cores) + 1`

For 4-core server: 9 workers

Update `/etc/systemd/system/atems.service`:

```ini
ExecStart=/var/www/atems/.venv/bin/gunicorn \
    --workers 9 \
    --bind unix:/var/www/atems/atems.sock \
    ...
```

Then reload:

```bash
sudo systemctl daemon-reload
sudo systemctl restart atems
```

---

## 8. Demo Accounts

The following accounts are available for demo purposes:

| Username | Password   | Role  | Permissions                          |
|----------|------------|-------|--------------------------------------|
| admin    | admin123   | Admin | Full access including Flask-Admin    |
| user     | user123    | User  | Check in/out, view tools, reports    |
| guest    | guest123   | Guest | View-only, cannot access admin panel |

**Important:** Change these passwords in production!

```bash
source /var/www/atems/.venv/bin/activate
python -c "
from atems import create_app
from extensions import db
from models.user import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.set_password('YOUR_SECURE_PASSWORD_HERE')
    db.session.commit()
    print('Admin password updated')
"
```

---

## 9. Troubleshooting

### ATEMS won't start

```bash
# Check logs
sudo journalctl -u atems -n 50
sudo tail -f /var/log/atems/error.log

# Check permissions
sudo chown -R www-data:www-data /var/www/atems
sudo chmod -R 755 /var/www/atems

# Restart service
sudo systemctl restart atems
```

### 502 Bad Gateway

```bash
# Check if ATEMS is running
sudo systemctl status atems

# Check socket file
ls -la /var/www/atems/atems.sock

# Check nginx error log
sudo tail -f /var/log/nginx/atems_error.log
```

### Database locked errors

```bash
# Increase timeout in atems.py
# Add to config:
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
```

---

## 10. Security Checklist

- [ ] SSL certificate installed and auto-renewal configured
- [ ] Firewall enabled (ufw) with only necessary ports open
- [ ] Default passwords changed for all demo accounts
- [ ] SECRET_KEY set to strong random value
- [ ] DEBUG=False in production
- [ ] Regular database backups configured
- [ ] Log rotation configured
- [ ] Rate limiting enabled in Nginx
- [ ] Security headers configured
- [ ] Ubuntu Pro security updates enabled

---

## Support

For issues or questions:
- Email: admin@alfaquantumdynamics.com
- Documentation: https://atems.alfaquantumdynamics.com/docs

---

**ATEMS** - Advanced Tool & Equipment Management System  
© 2026 Alfa Quantum Dynamics
