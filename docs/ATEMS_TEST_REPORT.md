# ATEMS Test Report

**Date:** 2026-02-04  
**URL:** https://alfaquantumdynamics.com/app/atems

---

## Summary

- **Service:** Running (gunicorn, port 5000)
- **Pytest:** 34/34 passed
- **Startup tests:** 6/6 passed
- **Feature test:** 17/17 passed
- **Public URLs:** Static assets and login links now work correctly
- **Splash login:** Root `/` shows login-first splash; guest/user/admin credentials required

---

## Splash Login (Feb 2026)

**Flow:** Users must sign in at the splash screen before accessing the dashboard.

- **`/`** → Splash screen with login form (when not authenticated)
- **Credentials:** guest/guest123 · user/user123 · admin/admin123
- **Template:** `templates/splash_login.html` (full-screen, tool crib background)
- **Logout** → Redirects to `/` (splash login)
- **Demo users:** Run `python scripts/seed_demo_users.py` to create guest, user, admin

---

## Fix Applied (Subpath Deployment)

**Problem:** When ATEMS is served at `/app/atems`, links and static assets used root-relative paths (`/static/...`, `/login`). Those resolved to `alfaquantumdynamics.com/static/...` (502) instead of `alfaquantumdynamics.com/app/atems/static/...`.

**Fix:** Added `APPLICATION_ROOT` support and `ScriptNameMiddleware` in `atems.py` so `url_for()` generates `/app/atems/...` paths. Configurable via env `APPLICATION_ROOT` (default `/app/atems`).

---

## Run Tests

```bash
cd /home/ansible/atems
# Use project venv or: pip install -r requirements.txt

# Seed demo users (guest, user, admin)
python scripts/seed_demo_users.py

# Full suite
pytest tests/ -v

# Startup + feature
python tests/startup_test.py
python scripts/test_all_features.py
```

---

*Last Updated: 2026-02-04*
