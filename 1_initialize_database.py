#!/usr/bin/env python
"""
ATTENDO - Script 1: Initialize Database
====================================

This script initializes the database with proper table structure and basic admin user.
Run this FIRST when setting up ATTENDO on a new machine.

Usage:
  python 1_initialize_database.py

What it does:
- Creates SQLite database file (vendor_timesheet.db)
- Creates all required tables with proper schema
- Adds default Admin user (Admin / admin123)
- Adds basic system configuration
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("🚀 ATTENDO - Database Initialization")
print("=" * 50)

try:
    from flask import Flask
    from datetime import datetime, date
    
    # Import app and models
    from app import app, db
    from models import (
        User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday, 
        MismatchRecord, NotificationLog, AuditLog, SystemConfiguration,
        LeaveRecord, WFHRecord, UserRole, AttendanceStatus, ApprovalStatus
    )
    
    print("✅ Successfully imported Flask app and models")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\n🔧 Please install dependencies first:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

def create_database_tables():
    """Create all database tables"""
    print("\n📊 Creating database tables...")
    
    with app.app_context():
        try:
            # Drop existing tables if they exist (for clean setup)
            db.drop_all()
            print("   Cleared existing tables (if any)")
            
            # Create all tables
            db.create_all()
            print("   Created all database tables")
            
            # Get list of created tables
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"   Tables created: {', '.join(tables)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False

def create_admin_user():
    """Create default admin user"""
    print("\n👤 Creating default Admin user...")
    
    with app.app_context():
        try:
            # Check if admin already exists
            admin = User.query.filter_by(username='Admin').first()
            
            if admin:
                print("   Admin user already exists, updating...")
                admin.email = 'admin@attendo.com'
                admin.role = UserRole.ADMIN
                admin.is_active = True
                admin.set_password('admin123')
            else:
                print("   Creating new Admin user...")
                admin = User(
                    username='Admin',
                    email='admin@attendo.com',
                    role=UserRole.ADMIN,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                admin.set_password('admin123')
                db.session.add(admin)
            
            db.session.commit()
            print("   ✅ Admin user created/updated successfully")
            print("   Login: Admin / admin123")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin user: {e}")
            return False

def add_basic_holidays():
    """Add basic system holidays"""
    print("\n🎉 Adding basic holidays...")
    
    with app.app_context():
        try:
            admin = User.query.filter_by(username='Admin').first()
            if not admin:
                print("   ⚠️ Admin user not found, skipping holidays")
                return True
            
            current_year = datetime.now().year
            holidays = [
                (date(current_year, 1, 1), 'New Year\'s Day', 'National Holiday'),
                (date(current_year, 8, 15), 'Independence Day', 'National Holiday'),
                (date(current_year, 10, 2), 'Gandhi Jayanti', 'National Holiday'),
                (date(current_year, 12, 25), 'Christmas Day', 'National Holiday'),
            ]
            
            created_count = 0
            for holiday_date, name, description in holidays:
                existing = Holiday.query.filter_by(holiday_date=holiday_date).first()
                if not existing:
                    holiday = Holiday(
                        holiday_date=holiday_date,
                        name=name,
                        description=description,
                        created_by=admin.id,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(holiday)
                    created_count += 1
            
            db.session.commit()
            print(f"   ✅ Added {created_count} holidays for {current_year}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding holidays: {e}")
            return False

def add_system_configuration():
    """Add basic system configuration"""
    print("\n⚙️ Adding system configuration...")
    
    with app.app_context():
        try:
            # Get admin user for updated_by field
            admin = User.query.filter_by(username='Admin').first()
            if not admin:
                print("   ⚠️ Admin user not found, skipping system configuration")
                return True
            
            configs = [
                ('app_name', 'ATTENDO', 'Application name'),
                ('app_version', '1.0.0', 'Application version'),
                ('default_work_hours', '8', 'Default working hours per day'),
                ('notification_enabled', 'true', 'Enable email notifications'),
                ('mismatch_detection_enabled', 'true', 'Enable attendance mismatch detection'),
            ]
            
            created_count = 0
            for key, value, description in configs:
                existing = SystemConfiguration.query.filter_by(key=key).first()
                if not existing:
                    config = SystemConfiguration(
                        key=key,
                        value=value,
                        description=description,
                        updated_by=admin.id,
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(config)
                    created_count += 1
            
            db.session.commit()
            print(f"   ✅ Added {created_count} system configurations")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding system configuration: {e}")
            return False

def verify_database():
    """Verify database setup"""
    print("\n🔍 Verifying database setup...")
    
    with app.app_context():
        try:
            # Check tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = [
                'users', 'vendors', 'managers', 'daily_statuses', 
                'swipe_records', 'holidays', 'mismatch_records',
                'notification_logs', 'audit_logs', 'system_configurations'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"   ❌ Missing tables: {', '.join(missing_tables)}")
                return False
            
            # Check admin user
            admin = User.query.filter_by(username='Admin').first()
            if not admin:
                print("   ❌ Admin user not found")
                return False
            
            # Check record counts
            user_count = User.query.count()
            holiday_count = Holiday.query.count()
            config_count = SystemConfiguration.query.count()
            
            print("   ✅ Database verification successful")
            print(f"   📊 Tables: {len(tables)}")
            print(f"   👤 Users: {user_count}")
            print(f"   🎉 Holidays: {holiday_count}")
            print(f"   ⚙️ Configs: {config_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error verifying database: {e}")
            return False

def main():
    """Main initialization function"""
    print(f"📁 Working directory: {ROOT}")
    print(f"📊 Database file: {ROOT}/vendor_timesheet.db")
    
    # Step 1: Create database tables
    if not create_database_tables():
        print("\n❌ Failed to create database tables")
        sys.exit(1)
    
    # Step 2: Create admin user
    if not create_admin_user():
        print("\n❌ Failed to create admin user")
        sys.exit(1)
    
    # Step 3: Add basic holidays
    if not add_basic_holidays():
        print("\n⚠️ Warning: Failed to add holidays (non-critical)")
    
    # Step 4: Add system configuration
    if not add_system_configuration():
        print("\n⚠️ Warning: Failed to add system configuration (non-critical)")
    
    # Step 5: Verify setup
    if not verify_database():
        print("\n❌ Database verification failed")
        sys.exit(1)
    
    # Success
    print("\n" + "=" * 50)
    print("🎉 DATABASE INITIALIZATION COMPLETE!")
    print("=" * 50)
    print("\n✅ What was created:")
    print("   📊 SQLite database with all required tables")
    print("   👤 Admin user: Admin / admin123")
    print("   🎉 Basic holiday calendar")
    print("   ⚙️ System configuration")
    
    print("\n🎯 Next steps:")
    print("   1. Run: python 2_load_sample_data.py")
    print("   2. Start app: python app.py")
    print("   3. Visit: http://localhost:5000")
    print("   4. Login with: Admin / admin123")
    
    print("\n💡 For a quick test with minimal setup:")
    print("   python app.py  # Skip step 1, basic setup only")

if __name__ == '__main__':
    main()
