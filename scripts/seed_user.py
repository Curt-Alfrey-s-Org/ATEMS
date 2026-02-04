#!/usr/bin/env python3
"""Create a test user for development. Run from ATEMS dir with app context."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        u.set_password('admin123')
        db.session.add(u)
        db.session.commit()
        print("Created user: admin / admin123")
