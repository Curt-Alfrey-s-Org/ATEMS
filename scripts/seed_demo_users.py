#!/usr/bin/env python3
"""
Seed demo users for https://atems.alfaquantumdynamics.com
Creates admin, user, and guest accounts with appropriate permissions.
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
        'password': 'admin123',
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
        'password': 'user123',
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
    {
        'username': 'guest',
        'password': 'guest123',
        'first_name': 'Guest',
        'last_name': 'Demo',
        'email': 'guest@alfaquantumdynamics.com',
        'badge_id': 'GUEST001',
        'phone': '5550003000',
        'department': 'ATEMS',
        'role': 'guest',
        'supervisor_username': 'admin',
        'supervisor_email': 'admin@alfaquantumdynamics.com',
        'supervisor_phone': '5550001000',
    },
]


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        
        created = 0
        for user_data in DEMO_USERS:
            username = user_data['username']
            if User.query.filter_by(username=username).first():
                print(f"User '{username}' already exists, skipping.")
                continue
            
            password = user_data.pop('password')
            u = User(**user_data)
            u.set_password(password)
            db.session.add(u)
            created += 1
            print(f"Created {user_data['role']} user: {username} / {password}")
        
        if created > 0:
            db.session.commit()
            print(f"\n✓ Created {created} demo users")
        else:
            print("\n✓ All demo users already exist")


if __name__ == "__main__":
    main()
