#!/usr/bin/env python3
"""
Add demo data including vendors to the database
"""

from flask import Flask
import os
from datetime import datetime, date, timedelta

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo-key'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath("vendor_timesheet.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import models
import models
models.db.init_app(app)

with app.app_context():
    from models import User, Vendor, Manager, UserRole, AttendanceStatus, DailyStatus, Holiday
    
    print("🎯 ADDING DEMO DATA TO ATTENDO DATABASE")
    print("="*50)
    
    # Check existing users
    existing_users = User.query.count()
    print(f"👥 Existing users: {existing_users}")
    
    # Add demo users if they don't exist
    demo_users = [
        {
            'username': 'vendor1',
            'email': 'vendor1@company.com',
            'password': 'vendor123',
            'role': UserRole.VENDOR
        },
        {
            'username': 'vendor2', 
            'email': 'vendor2@company.com',
            'password': 'vendor123',
            'role': UserRole.VENDOR
        },
        {
            'username': 'manager1',
            'email': 'manager1@company.com', 
            'password': 'manager123',
            'role': UserRole.MANAGER
        }
    ]
    
    created_users = []
    
    for user_data in demo_users:
        existing_user = User.query.filter_by(username=user_data['username']).first()
        if not existing_user:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role']
            )
            user.set_password(user_data['password'])
            models.db.session.add(user)
            created_users.append(user)
            print(f"✅ Created user: {user_data['username']} ({user_data['role'].value})")
        else:
            created_users.append(existing_user)
            print(f"⚠️  User already exists: {user_data['username']}")
    
    models.db.session.commit()
    
    # Create manager profile
    manager_user = next((u for u in created_users if u.username == 'manager1'), None)
    if manager_user and not manager_user.manager_profile:
        manager = Manager(
            user_id=manager_user.id,
            full_name="John Manager",
            department="Engineering",
            team_name="Development Team A"
        )
        models.db.session.add(manager)
        print("✅ Created manager profile: John Manager")
    
    models.db.session.commit()
    manager_profile = Manager.query.filter_by(user_id=manager_user.id).first()
    
    # Create vendor profiles
    vendor_profiles = [
        {
            'user_id': next((u.id for u in created_users if u.username == 'vendor1'), None),
            'vendor_id': 'V001',
            'full_name': 'Alice Vendor',
            'department': 'MTK_WCS_MSE7_MS1',
            'company': 'ABC Solutions', 
            'band': 'B2',
            'location': 'BL-A-5F',
            'manager_id': manager_profile.id if manager_profile else None
        },
        {
            'user_id': next((u.id for u in created_users if u.username == 'vendor2'), None),
            'vendor_id': 'V002', 
            'full_name': 'Bob Developer',
            'department': 'MTK_WCS_MSE7_MS2',
            'company': 'XYZ Technologies',
            'band': 'B3',
            'location': 'BL-B-3F',
            'manager_id': manager_profile.id if manager_profile else None
        }
    ]
    
    for vendor_data in vendor_profiles:
        if vendor_data['user_id']:
            existing_vendor = Vendor.query.filter_by(user_id=vendor_data['user_id']).first()
            if not existing_vendor:
                vendor = Vendor(**vendor_data)
                models.db.session.add(vendor)
                print(f"✅ Created vendor profile: {vendor_data['full_name']} ({vendor_data['vendor_id']})")
            else:
                print(f"⚠️  Vendor profile already exists: {vendor_data['full_name']}")
    
    models.db.session.commit()
    
    # Add some sample daily status submissions
    vendors = Vendor.query.all()
    today = date.today()
    
    for vendor in vendors:
        # Add today's status
        existing_status = DailyStatus.query.filter_by(
            vendor_id=vendor.id,
            status_date=today
        ).first()
        
        if not existing_status:
            status = DailyStatus(
                vendor_id=vendor.id,
                status_date=today,
                status=AttendanceStatus.IN_OFFICE_FULL,
                location="Office",
                comments="Working on project tasks"
            )
            models.db.session.add(status)
            print(f"✅ Added today's status for {vendor.full_name}")
        
        # Add yesterday's status
        yesterday = today - timedelta(days=1)
        existing_yesterday = DailyStatus.query.filter_by(
            vendor_id=vendor.id,
            status_date=yesterday
        ).first()
        
        if not existing_yesterday:
            status = DailyStatus(
                vendor_id=vendor.id,
                status_date=yesterday,
                status=AttendanceStatus.WFH_FULL,
                location="Home",
                comments="Work from home day"
            )
            models.db.session.add(status)
            print(f"✅ Added yesterday's status for {vendor.full_name}")
    
    # Add some holidays
    holidays_data = [
        {
            'holiday_date': date(2025, 12, 25),
            'name': 'Christmas Day',
            'description': 'Christmas holiday'
        },
        {
            'holiday_date': date(2025, 1, 1),
            'name': 'New Year Day',
            'description': 'New Year celebration'
        }
    ]
    
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        for holiday_data in holidays_data:
            existing_holiday = Holiday.query.filter_by(holiday_date=holiday_data['holiday_date']).first()
            if not existing_holiday:
                holiday = Holiday(
                    holiday_date=holiday_data['holiday_date'],
                    name=holiday_data['name'],
                    description=holiday_data['description'],
                    created_by=admin_user.id
                )
                models.db.session.add(holiday)
                print(f"✅ Added holiday: {holiday_data['name']}")
    
    models.db.session.commit()
    
    print("\n" + "="*50)
    print("🎉 DEMO DATA CREATION COMPLETED!")
    print("="*50)
    
    # Show final statistics
    print(f"👥 Total Users: {User.query.count()}")
    print(f"🏢 Total Vendors: {Vendor.query.count()}")
    print(f"👔 Total Managers: {Manager.query.count()}")
    print(f"📅 Total Daily Statuses: {DailyStatus.query.count()}")
    print(f"🎄 Total Holidays: {Holiday.query.count()}")
    
    print("\n🔐 LOGIN CREDENTIALS:")
    print("   Admin:    admin / admin123")
    print("   Manager:  manager1 / manager123") 
    print("   Vendor 1: vendor1 / vendor123")
    print("   Vendor 2: vendor2 / vendor123")
    
    print(f"\n🚀 You can now login to the vendor application!")
    print("   Start the app with: python app.py")
    print("   Then visit: http://localhost:5000")
