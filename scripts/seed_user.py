#!/usr/bin/env python3
"""Create a test user for development. Run from ATEMS dir with app context.

The password comes from ADMIN_PASSWORD (no built-in default):
    ADMIN_PASSWORD='<strong password>' python scripts/seed_user.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.auth_security import is_known_default_password

admin_password = (os.getenv("ADMIN_PASSWORD") or "").strip()
if not admin_password or is_known_default_password(admin_password):
    sys.exit("ADMIN_PASSWORD must be set to a strong, non-default password.")

from atems import create_app
from extensions import db
from models.user import User

app = create_app()
with app.app_context():
    # Create all tables if they don't exist
    db.create_all()
    
    if User.query.filter_by(username='admin').first():
        print("User 'admin' already exists.")
    else:
        u = User(
            first_name='Admin',
            last_name='User',
            username='admin',
            email='admin@example.com',
            badge_id='ADMIN001',
            phone='5550000000',
            department='ATEMS',
            supervisor_username='admin',
            supervisor_email='admin@example.com',
            supervisor_phone='5550000000',
        )
        u.set_password(admin_password)
        db.session.add(u)
        db.session.commit()
        print("Created user: admin (password from ADMIN_PASSWORD)")
