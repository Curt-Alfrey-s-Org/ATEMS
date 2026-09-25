#!/usr/bin/env python3
"""
Seed demo users for https://atems.alfaquantumdynamics.com
Creates admin and user accounts with appropriate permissions.

Passwords come from the environment (no built-in defaults):
    ADMIN_PASSWORD  - password for the 'admin' demo account (required)
    USER_PASSWORD   - password for the 'user' demo account (required)
Known default passwords are refused (see utils/auth_security.py).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atems import create_app
from extensions import db
from models.user import User

DEMO_USERS = [
    {
        'username': 'admin',
        'password_env': 'ADMIN_PASSWORD',
        'first_name': 'System',
        'last_name': 'Administrator',
        'email': 'admin@alfaquantumdynamics.com',
        'badge_id': 'ADMIN001',
        'phone': '5550001000',
        'department': 'ATEMS',
        'role': 'admin',
        'supervisor_username': 'admin',
        'supervisor_email': 'admin@alfaquantumdynamics.com',
        'supervisor_phone': '5550001000',
    },
    {
        'username': 'user',
        'password_env': 'USER_PASSWORD',
        'first_name': 'Demo',
        'last_name': 'User',
        'email': 'user@alfaquantumdynamics.com',
        'badge_id': 'USER001',
        'phone': '5550002000',
        'department': 'Engineering',
        'role': 'user',
        'supervisor_username': 'admin',
        'supervisor_email': 'admin@alfaquantumdynamics.com',
        'supervisor_phone': '5550001000',
    },
]

def _password_from_env(var):
    from utils.auth_security import is_known_default_password
    value = (os.getenv(var) or "").strip()
    if not value or is_known_default_password(value):
        sys.exit(f"{var} must be set to a strong, non-default password.")
    return value


def main():
    passwords = {u['password_env']: _password_from_env(u['password_env']) for u in DEMO_USERS}
    app = create_app()
    with app.app_context():
        db.create_all()
        
        created = 0
        for user_data in DEMO_USERS:
            username = user_data['username']
            if User.query.filter_by(username=username).first():
                print(f"User '{username}' already exists, skipping.")
                continue
            
            fields = {k: v for k, v in user_data.items() if k != 'password_env'}
            u = User(**fields)
            u.set_password(passwords[user_data['password_env']])
            db.session.add(u)
            created += 1
            print(f"Created {user_data['role']} user: {username} (password from {user_data['password_env']})")
        
        if created > 0:
            db.session.commit()
            print(f"\n✓ Created {created} demo users")
        else:
            print("\n✓ All demo users already exist")

if __name__ == "__main__":
    main()
