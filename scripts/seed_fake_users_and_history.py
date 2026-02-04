#!/usr/bin/env python3
"""
Seed fake users and checkout history for demo site.
Creates realistic user data and tool checkout patterns.
"""
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atems import create_app
from extensions import db
from models.user import User
from models.tools import Tools
from models.checkout_history import CheckoutHistory

# Realistic first and last names
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna",
    "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Raymond", "Christine", "Gregory", "Debra",
    "Frank", "Rachel", "Alexander", "Catherine", "Patrick", "Carolyn", "Jack", "Janet",
    "Dennis", "Ruth", "Jerry", "Maria", "Tyler", "Heather", "Aaron", "Diane",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza",
    "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers",
]

DEPARTMENTS = [
    "Manufacturing", "Engineering", "Quality", "Supply Chain", "Test", "ATEMS",
    "Maintenance", "Production", "R&D", "Assembly", "Machining", "Welding",
    "Inspection", "Tooling", "Facilities", "Safety", "Shipping", "Receiving",
]

JOB_PREFIXES = [
    "JOB", "PRJ", "WO", "MO", "SO", "PO", "BUILD", "ASSY", "TEST", "MAINT",
]

CONDITIONS = ["Good", "Fair", "Damaged", None]


def generate_user(index):
    """Generate a realistic fake user."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    username = f"{first.lower()}.{last.lower()}{index if index > 1 else ''}"
    email = f"{username}@company.com"
    badge_id = f"EMP{index:05d}"
    phone = f"555{random.randint(1000000, 9999999)}"
    dept = random.choice(DEPARTMENTS)
    
    return {
        'first_name': first,
        'last_name': last,
        'username': username,
        'email': email,
        'badge_id': badge_id,
        'phone': phone,
        'department': dept,
        'role': 'user',
        'supervisor_username': 'admin',
        'supervisor_email': 'admin@alfaquantumdynamics.com',
        'supervisor_phone': '5550001000',
    }


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # Create 200 fake users
        print("Creating fake users...")
        existing_users = User.query.count()
        target_users = 200
        
        created_users = 0
        for i in range(1, target_users + 1):
            user_data = generate_user(i)
            if User.query.filter_by(username=user_data['username']).first():
                continue
            
            u = User(**user_data)
            u.set_password('demo123')  # All demo users have same password
            db.session.add(u)
            created_users += 1
            
            if created_users % 50 == 0:
                db.session.commit()
                print(f"  Created {created_users} users...")
        
        db.session.commit()
        print(f"✓ Created {created_users} fake users (total: {User.query.count()})")
        
        # Create checkout history
        print("\nCreating checkout history...")
        existing_history = CheckoutHistory.query.count()
        if existing_history > 5000:
            print(f"✓ Already have {existing_history} history records")
            return
        
        # Get all users and tools
        users = User.query.filter(User.role == 'user').all()
        tools = Tools.query.limit(5000).all()  # Use subset for history
        
        if not users or not tools:
            print("⚠ Need users and tools first")
            return
        
        # Generate 5000 checkout/checkin events over past 90 days
        today = datetime.now()
        created_history = 0
        
        for i in range(2500):  # 2500 checkout/checkin pairs
            user = random.choice(users)
            tool = random.choice(tools)
            
            # Checkout event (random time in past 90 days)
            checkout_time = today - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
            job_id = f"{random.choice(JOB_PREFIXES)}-{random.randint(2024, 2026)}-{random.randint(1, 999):03d}"
            condition = random.choice(CONDITIONS)
            
            checkout = CheckoutHistory(
                event_time=checkout_time,
                action='checkout',
                tool_id_number=tool.tool_id_number,
                tool_name=tool.tool_name,
                username=user.username,
                job_id=job_id,
                condition=condition,
            )
            db.session.add(checkout)
            created_history += 1
            
            # 80% chance of checkin (some tools still checked out)
            if random.random() < 0.8:
                checkin_time = checkout_time + timedelta(hours=random.randint(1, 168))  # 1 hour to 1 week
                checkin = CheckoutHistory(
                    event_time=checkin_time,
                    action='checkin',
                    tool_id_number=tool.tool_id_number,
                    tool_name=tool.tool_name,
                    username=user.username,
                    job_id=job_id,
                    condition=random.choice(CONDITIONS),
                )
                db.session.add(checkin)
                created_history += 1
            
            if (i + 1) % 500 == 0:
                db.session.commit()
                print(f"  Created {created_history} history records...")
        
        db.session.commit()
        print(f"✓ Created {created_history} checkout history records (total: {CheckoutHistory.query.count()})")


if __name__ == "__main__":
    main()
