# ATEMS Demo Site Configuration
## Professional Demo for https://atems.alfaquantumdynamics.com

This document summarizes the complete demo site setup for ATEMS.

---

## ✅ Completed Features

### 1. User Roles & Authentication
- **Admin Account**: `admin` / `admin123` - Full system access including Flask-Admin panel
- **User Account**: `user` / `user123` - Standard user with check-in/out and reporting access
- **Guest Account**: `guest` / `guest123` - View-only demo access, can explore all features but cannot access admin panel

### 2. Massive Demo Database
- **50,000 Tools** from 10 major US industries:
  - Construction (8,000 tools)
  - Manufacturing (10,000 tools)
  - Automotive (7,000 tools)
  - Oil & Gas (5,000 tools)
  - Aerospace (6,000 tools)
  - Electrical/Utilities (6,000 tools)
  - Plumbing/HVAC (5,000 tools)
  - Agriculture (4,000 tools)
  - Mining (3,000 tools)
  - Healthcare/Medical Devices (6,000 tools)

- **200+ Fake Users** with realistic names and departments
- **4,500+ Checkout History Records** spanning 90 days of activity

### 3. Professional Splash Screen
- Hero section with tool crib imagery
- Feature showcase with hover effects
- Live statistics (50K+ tools, 10 industries, 200+ users, 99.9% uptime)
- Call-to-action buttons for sign-in and demo access
- Responsive design with smooth animations
- **URL**: `/` (landing page) or `/splash`

### 4. Tool Crib Imagery
- **23 Professional Images** scraped from Unsplash
- High-quality tool crib and industrial tool room photos
- Used in splash screen and throughout UI
- Located in: `/static/images/tool_cribs/`

### 5. Comprehensive Tooltips
- **Dashboard**: Tooltips on stat cards (Total Tools, In Stock, Checked Out, Calibration Overdue) and Recent Activity table
- **Check In/Out**: Tooltips on all form fields (Username, Badge ID, Tool ID, Job/Project ID, Condition, Submit button)
- **Self-Test**: Tooltips on test controls and results
- Hover over `?` icons to see contextual help
- Implemented via `/static/js/tooltips.js`

### 6. Guest Permissions
- Guests can view all features (dashboard, tools, checkout history, reports)
- Guests **cannot** access Flask-Admin panel (`/admin`)
- Admin panel restricted to users with `role='admin'`
- Proper redirects and error messages for unauthorized access

### 7. Modern UI/UX
- Dark theme with Tailwind CSS
- Sidebar navigation with icons
- Stat cards with hover effects
- Responsive tables with mobile-friendly layouts
- Professional color scheme (slate/blue/cyan)
- Smooth transitions and animations

### 8. Deployment Documentation
- Complete Nginx configuration for Ubuntu Pro
- Systemd service setup for production
- SSL/TLS with Let's Encrypt (Certbot)
- Security headers and rate limiting
- Database backup scripts
- Performance tuning guidelines
- **File**: `NGINX_DEPLOYMENT.md`

---

## 🗂️ Database Schema

### Users Table
- `id`, `first_name`, `last_name`, `username`, `password_hash`, `email`
- `badge_id`, `phone`, `department`, `role` (admin/user/guest)
- `supervisor_username`, `supervisor_email`, `supervisor_phone`
- `manager_username`, `manager_email`, `manager_phone`

### Tools Table
- `id`, `tool_id_number`, `tool_name`, `tool_location`, `tool_status`
- `tool_calibration_due`, `tool_calibration_date`, `tool_calibration_cert`, `tool_calibration_schedule`
- `checked_out_by` (nullable, references user)

### CheckoutHistory Table
- `id`, `event_time`, `action` (checkout/checkin)
- `tool_id_number`, `tool_name`, `username`
- `job_id` (optional), `condition` (optional: Good/Fair/Damaged)

---

## 📊 Demo Statistics

| Metric | Value |
|--------|-------|
| Total Tools | 50,000 |
| Industries | 10 |
| Users | 203 (3 demo + 200 fake) |
| Checkout History Records | 4,505 |
| Tool Crib Images | 23 |
| Tooltips | 15+ |

---

## 🚀 Quick Start (Local Development)

```bash
cd /home/n4s1/rankings-bot/ATEMS

# Activate virtual environment
source .venv/bin/activate

# Run application
python run.py
# OR
flask run --host=0.0.0.0 --port=5000

# Access at: http://localhost:5000
```

---

## 🌐 Production Deployment

Follow the complete guide in `NGINX_DEPLOYMENT.md` for:
- Ubuntu Pro server setup
- Nginx reverse proxy configuration
- SSL certificate installation
- Systemd service management
- Database backups
- Security hardening

---

## 🎯 Demo Workflow for Visitors

### As Guest User:
1. Visit https://atems.alfaquantumdynamics.com
2. View professional splash screen
3. Click "Try Demo" or sign in with `guest` / `guest123`
4. Explore dashboard with 50K tools and live statistics
5. Browse tools, view checkout history, generate reports
6. Hover over `?` icons for contextual help
7. Try to access `/admin` (will be denied with friendly message)

### As Regular User:
1. Sign in with `user` / `user123`
2. Check out tools using badge ID and tool ID
3. Add job/project IDs and tool condition
4. Check in tools
5. View personal checkout history
6. Generate calibration and usage reports

### As Admin:
1. Sign in with `admin` / `admin123`
2. Access Flask-Admin panel at `/admin`
3. Manage users, tools, and checkout history
4. View system health via Self-Test page
5. Export data and generate comprehensive reports

---

## 🛠️ Maintenance Scripts

All located in `/scripts/`:

| Script | Purpose |
|--------|---------|
| `seed_demo_users.py` | Create admin/user/guest accounts |
| `seed_50k_tools.py` | Populate 50,000 tools from 10 industries |
| `seed_fake_users_and_history.py` | Generate 200 users + 4,500 history records |
| `scrape_tool_crib_images.py` | Download professional tool crib images |
| `test_all_features.py` | Comprehensive feature testing |

---

## 📝 Key Files

| File | Description |
|------|-------------|
| `templates/splash.html` | Professional landing page |
| `static/js/tooltips.js` | Tooltip system |
| `static/images/tool_cribs/` | Tool crib imagery |
| `models/user.py` | User model with roles |
| `routes.py` | All application routes |
| `NGINX_DEPLOYMENT.md` | Production deployment guide |

---

## 🔐 Security Notes

- All passwords are hashed with bcrypt
- Role-based access control enforced
- Flask-Admin restricted to admins only
- CSRF protection enabled
- SQL injection protection via SQLAlchemy ORM
- **Change default passwords in production!**

---

## 📞 Support

For questions or issues:
- Email: admin@alfaquantumdynamics.com
- Demo Site: https://atems.alfaquantumdynamics.com

---

**ATEMS** - Advanced Tool & Equipment Management System  
© 2026 Alfa Quantum Dynamics

*Built for tool crib professionals. Designed for scale.*
