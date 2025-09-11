#!/usr/bin/env python
"""
ATTENDO - Script 2: Load Sample Data
=================================

This script loads comprehensive sample data for a complete demo experience.
Run this AFTER running 1_initialize_database.py.

Usage:
  python 2_load_sample_data.py

What it creates:
- Sample managers and vendors with realistic profiles
- 30+ days of attendance and swipe data
- Intentional mismatches for reconciliation demo
- Leave and WFH records
- Notification and audit logs
"""

import os
import sys
import random
from pathlib import Path
from datetime import datetime, date, time, timedelta

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("🎯 ATTENDO - Sample Data Loading")
print("=" * 50)

try:
    from flask import Flask
    
    # Import app and models
    from app import app, db
    from models import (
        User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday, 
        MismatchRecord, NotificationLog, AuditLog, SystemConfiguration,
        LeaveRecord, WFHRecord, UserRole, AttendanceStatus, ApprovalStatus
    )
    # Import SystemIssue model for technical system health monitoring
    try:
        from system_issues import SystemIssue
    except ImportError:
        SystemIssue = None
    
    print("✅ Successfully imported Flask app and models")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\n🔧 Please run this first:")
    print("   python 1_initialize_database.py")
    sys.exit(1)

# Set random seed for reproducible sample data
random.seed(2025)

def check_database_initialized():
    """Check if database is properly initialized"""
    print("\n🔍 Checking database initialization...")
    
    with app.app_context():
        try:
            # Check if admin exists
            admin = User.query.filter_by(username='Admin').first()
            if not admin:
                print("❌ Admin user not found")
                return False
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['users', 'vendors', 'managers']
            missing = [t for t in required_tables if t not in tables]
            
            if missing:
                print(f"❌ Missing required tables: {missing}")
                return False
            
            print("✅ Database initialization verified")
            return True
            
        except Exception as e:
            print(f"❌ Database check failed: {e}")
            return False

def create_sample_users_and_profiles():
    """Create sample managers and vendors with their user accounts"""
    print("\n👥 Creating sample users and profiles...")
    
    with app.app_context():
        try:
            created_users = 0
            
            # Sample managers data
            managers_data = [
                {
                    'username': 'manager1', 'email': 'alice.manager@attendo.com',
                    'manager_id': 'M001', 'full_name': 'Alice Johnson',
                    'department': 'Engineering', 'team_name': 'Backend Team',
                    'phone': '+1-555-0101'
                },
                {
                    'username': 'manager2', 'email': 'bob.manager@attendo.com',
                    'manager_id': 'M002', 'full_name': 'Bob Chen',
                    'department': 'Operations', 'team_name': 'Infrastructure Team',
                    'phone': '+1-555-0102'
                },
                {
                    'username': 'manager3', 'email': 'carol.manager@attendo.com',
                    'manager_id': 'M003', 'full_name': 'Carol Davis',
                    'department': 'Quality Assurance', 'team_name': 'QA Team',
                    'phone': '+1-555-0103'
                }
            ]
            
            # Create manager users and profiles
            for mgr_data in managers_data:
                # Check if user exists
                user = User.query.filter_by(username=mgr_data['username']).first()
                if not user:
                    user = User(
                        username=mgr_data['username'],
                        email=mgr_data['email'],
                        role=UserRole.MANAGER,
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                    user.set_password('manager123')
                    db.session.add(user)
                    db.session.flush()  # Get user ID
                    created_users += 1
                
                # Check if manager profile exists
                manager = Manager.query.filter_by(manager_id=mgr_data['manager_id']).first()
                if not manager:
                    manager = Manager(
                        manager_id=mgr_data['manager_id'],
                        user_id=user.id,
                        full_name=mgr_data['full_name'],
                        department=mgr_data['department'],
                        team_name=mgr_data['team_name'],
                        email=mgr_data['email'],
                        phone=mgr_data.get('phone'),
                        created_at=datetime.utcnow()
                    )
                    db.session.add(manager)
            
            # Sample vendors data - username matches vendor_id for consistent login
            vendors_data = [
                {
                    'username': 'EMP001', 'email': 'john.vendor@company.com',
                    'vendor_id': 'EMP001', 'full_name': 'John Smith',
                    'department': 'Engineering', 'company': 'TechCorp Solutions',
                    'band': 'B2', 'location': 'BL-A-5F', 'manager_id': 'M001'
                },
                {
                    'username': 'EMP002', 'email': 'jane.vendor@company.com',
                    'vendor_id': 'EMP002', 'full_name': 'Jane Wilson',
                    'department': 'Engineering', 'company': 'TechCorp Solutions',
                    'band': 'B2', 'location': 'BL-A-5F', 'manager_id': 'M001'
                },
                {
                    'username': 'EMP003', 'email': 'mike.vendor@company.com',
                    'vendor_id': 'EMP003', 'full_name': 'Mike Rodriguez',
                    'department': 'Operations', 'company': 'InfraCorp Ltd',
                    'band': 'B3', 'location': 'BL-B-3F', 'manager_id': 'M002'
                },
                {
                    'username': 'EMP004', 'email': 'sarah.vendor@company.com',
                    'vendor_id': 'EMP004', 'full_name': 'Sarah Parker',
                    'department': 'Quality Assurance', 'company': 'QualityCorp Inc',
                    'band': 'B2', 'location': 'BL-C-4F', 'manager_id': 'M003'
                },
                {
                    'username': 'EMP005', 'email': 'david.vendor@company.com',
                    'vendor_id': 'EMP005', 'full_name': 'David Kim',
                    'department': 'Engineering', 'company': 'TechCorp Solutions',
                    'band': 'B3', 'location': 'BL-A-6F', 'manager_id': 'M001'
                }
            ]
            
            # Create vendor users and profiles
            for vnd_data in vendors_data:
                # Check if user exists
                user = User.query.filter_by(username=vnd_data['username']).first()
                if not user:
                    user = User(
                        username=vnd_data['username'],
                        email=vnd_data['email'],
                        role=UserRole.VENDOR,
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                    user.set_password('vendor123')
                    db.session.add(user)
                    db.session.flush()  # Get user ID
                    created_users += 1
                
                # Check if vendor profile exists
                vendor = Vendor.query.filter_by(vendor_id=vnd_data['vendor_id']).first()
                if not vendor:
                    vendor = Vendor(
                        user_id=user.id,
                        vendor_id=vnd_data['vendor_id'],
                        full_name=vnd_data['full_name'],
                        department=vnd_data['department'],
                        company=vnd_data['company'],
                        band=vnd_data['band'],
                        location=vnd_data['location'],
                        manager_id=vnd_data['manager_id'],
                        created_at=datetime.utcnow()
                    )
                    db.session.add(vendor)
            
            db.session.commit()
            print(f"   ✅ Created {created_users} new user accounts")
            print(f"   ✅ Created {len(managers_data)} manager profiles")
            print(f"   ✅ Created {len(vendors_data)} vendor profiles")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating users and profiles: {e}")
            return False

def generate_attendance_data():
    """Generate realistic attendance data for the past month"""
    print("\n📅 Generating attendance data...")
    
    with app.app_context():
        try:
            # Get all vendors
            vendors = Vendor.query.all()
            if not vendors:
                print("❌ No vendors found")
                return False
            
            # Generate data for the past 45 days
            end_date = date.today() - timedelta(days=1)  # Yesterday
            start_date = end_date - timedelta(days=45)   # 45 days ago
            
            attendance_created = 0
            swipe_created = 0
            
            current_date = start_date
            while current_date <= end_date:
                weekday = current_date.weekday()  # 0=Monday, 6=Sunday
                is_weekend = weekday >= 5
                
                for vendor in vendors:
                    # Skip most weekends (85% chance)
                    if is_weekend and random.random() < 0.85:
                        continue
                    
                    # Determine attendance status based on realistic patterns
                    if is_weekend:
                        # Weekend work is rare
                        status = AttendanceStatus.IN_OFFICE_FULL if random.random() < 0.1 else AttendanceStatus.ABSENT
                    else:
                        # Weekday patterns
                        rand = random.random()
                        if rand < 0.75:  # 75% in office
                            status = AttendanceStatus.IN_OFFICE_FULL
                        elif rand < 0.90:  # 15% WFH
                            status = AttendanceStatus.WFH_FULL
                        elif rand < 0.95:  # 5% leave
                            status = AttendanceStatus.LEAVE_FULL
                        else:  # 5% absent
                            status = AttendanceStatus.ABSENT
                    
                    # Create daily status
                    existing_status = DailyStatus.query.filter_by(
                        vendor_id=vendor.id, status_date=current_date
                    ).first()
                    
                    if not existing_status:
                        # Calculate total and extra hours for the status
                        total_work_hours = 0.0
                        extra_work_hours = 0.0
                        
                        if status == AttendanceStatus.IN_OFFICE_FULL:
                            # Full day office work: 8 hours standard + random overtime
                            base_hours = 8.0
                            overtime = random.choice([0, 0.5, 1.0, 1.5, 2.0]) if random.random() < 0.3 else 0
                            total_work_hours = base_hours + overtime
                            extra_work_hours = overtime
                        elif status == AttendanceStatus.IN_OFFICE_HALF:
                            # Half day office work: 4 hours
                            total_work_hours = 4.0
                            extra_work_hours = 0.0
                        elif status == AttendanceStatus.WFH_FULL:
                            # Full day WFH: similar to office
                            base_hours = 8.0
                            overtime = random.choice([0, 0.5, 1.0]) if random.random() < 0.2 else 0
                            total_work_hours = base_hours + overtime
                            extra_work_hours = overtime
                        elif status == AttendanceStatus.WFH_HALF:
                            # Half day WFH: 4 hours
                            total_work_hours = 4.0
                            extra_work_hours = 0.0
                        # Leave and absent don't have working hours
                        
                        daily_status = DailyStatus(
                            vendor_id=vendor.id,
                            status_date=current_date,
                            status=status,
                            location='Office' if 'IN_OFFICE' in status.value else ('Home' if 'WFH' in status.value else 'N/A'),
                            total_hours=total_work_hours,
                            extra_hours=extra_work_hours,
                            submitted_at=datetime.combine(
                                current_date, 
                                time(random.randint(8, 10), random.randint(0, 59))
                            ),
                            approval_status=ApprovalStatus.APPROVED if random.random() < 0.9 else ApprovalStatus.PENDING
                        )
                        db.session.add(daily_status)
                        attendance_created += 1
                    
                    # Create corresponding swipe record
                    existing_swipe = SwipeRecord.query.filter_by(
                        vendor_id=vendor.id, attendance_date=current_date
                    ).first()
                    
                    if not existing_swipe:
                        if status == AttendanceStatus.IN_OFFICE_FULL and not is_weekend:
                            # Present in office - generate realistic swipe times
                            login_hour = random.randint(8, 10)
                            login_minute = random.randint(0, 59)
                            logout_hour = random.randint(17, 19)
                            logout_minute = random.randint(0, 59)
                            
                            total_minutes = (logout_hour * 60 + logout_minute) - (login_hour * 60 + login_minute)
                            total_hours = round(total_minutes / 60.0, 2)
                            extra_hours = max(0.0, round((total_minutes - 480) / 60.0, 2))  # Over 8 hours
                            
                            swipe_record = SwipeRecord(
                                vendor_id=vendor.id,
                                attendance_date=current_date,
                                weekday=current_date.strftime('%A'),
                                shift_code='G',
                                login_time=time(login_hour, login_minute),
                                logout_time=time(logout_hour, logout_minute),
                                total_hours=total_hours,
                                extra_hours=extra_hours,
                                attendance_status='AP'  # Present
                            )
                        else:
                            # Absent, WFH, or Leave - no swipe or absent swipe
                            swipe_record = SwipeRecord(
                                vendor_id=vendor.id,
                                attendance_date=current_date,
                                weekday=current_date.strftime('%A'),
                                shift_code='A',
                                login_time=None,
                                logout_time=None,
                                total_hours=0.0,
                                extra_hours=0.0,
                                attendance_status='AA'  # Absent
                            )
                        
                        db.session.add(swipe_record)
                        swipe_created += 1
                
                current_date += timedelta(days=1)
            
            db.session.commit()
            print(f"   ✅ Created {attendance_created} daily status records")
            print(f"   ✅ Created {swipe_created} swipe records")
            print(f"   📊 Date range: {start_date} to {end_date}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error generating attendance data: {e}")
            return False

def create_sample_mismatches():
    """Create intentional mismatches for demo purposes"""
    print("\n🔍 Creating sample mismatches...")
    
    with app.app_context():
        try:
            # Import detect_mismatches function
            try:
                from utils import detect_mismatches
            except ImportError:
                print("   ⚠️ Could not import detect_mismatches, skipping mismatch creation")
                return True
            
            vendors = Vendor.query.all()
            if not vendors:
                return True
            
            # Create a few intentional mismatches in recent days
            mismatches_created = 0
            recent_days = 7
            
            for i in range(recent_days):
                mismatch_date = date.today() - timedelta(days=i+1)
                
                # Skip weekends
                if mismatch_date.weekday() >= 5:
                    continue
                
                # Create 1-2 mismatches per day
                for _ in range(random.randint(1, 2)):
                    vendor = random.choice(vendors)
                    
                    # Scenario 1: WFH claimed but showed up in office
                    if random.random() < 0.5:
                        # Update daily status to WFH
                        daily_status = DailyStatus.query.filter_by(
                            vendor_id=vendor.id, status_date=mismatch_date
                        ).first()
                        
                        if daily_status:
                            daily_status.status = AttendanceStatus.WFH_FULL
                            daily_status.location = 'Home'
                        
                        # Update swipe record to show office presence
                        swipe_record = SwipeRecord.query.filter_by(
                            vendor_id=vendor.id, attendance_date=mismatch_date
                        ).first()
                        
                        if swipe_record:
                            swipe_record.login_time = time(9, 30)
                            swipe_record.logout_time = time(18, 0)
                            swipe_record.total_hours = 8.5
                            swipe_record.attendance_status = 'AP'
                        
                        mismatches_created += 1
            
            db.session.commit()
            
            # Run mismatch detection
            try:
                end_date = date.today() - timedelta(days=1)
                start_date = end_date - timedelta(days=recent_days)
                detected_mismatches = detect_mismatches(start_date, end_date)
                
                print(f"   ✅ Created {mismatches_created} intentional mismatches")
                print(f"   🔍 Detected {len(detected_mismatches)} total mismatches")
            except Exception as e:
                print(f"   ⚠️ Mismatch detection failed: {e}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating mismatches: {e}")
            return False

def create_sample_notifications():
    """Create sample notification logs"""
    print("\n📬 Creating sample notifications...")
    
    with app.app_context():
        try:
            # Get managers and vendors
            managers = User.query.filter_by(role=UserRole.MANAGER).all()
            vendors = User.query.filter_by(role=UserRole.VENDOR).all()
            
            notifications_created = 0
            
            # Create various types of notifications
            notification_types = [
                ('daily_reminder', 'Daily attendance submission reminder'),
                ('approval_request', 'New attendance status pending approval'),
                ('mismatch_alert', 'Attendance mismatch detected'),
                ('weekly_summary', 'Weekly attendance summary'),
                ('holiday_reminder', 'Upcoming holiday notification')
            ]
            
            # Create notifications for the past 7 days
            for days_back in range(7):
                notification_date = datetime.utcnow() - timedelta(days=days_back)
                
                # Create 2-5 notifications per day
                for _ in range(random.randint(2, 5)):
                    notification_type, base_message = random.choice(notification_types)
                    recipient = random.choice(managers + vendors)
                    
                    notification = NotificationLog(
                        recipient_id=recipient.id,
                        notification_type=notification_type,
                        message=f"{base_message} - {notification_date.strftime('%Y-%m-%d')}",
                        sent_at=notification_date,
                        is_read=random.random() < 0.7  # 70% read
                    )
                    
                    db.session.add(notification)
                    notifications_created += 1
            
            db.session.commit()
            print(f"   ✅ Created {notifications_created} notification logs")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating notifications: {e}")
            return False

def create_audit_trail():
    """Create sample audit trail"""
    print("\n📝 Creating audit trail...")
    
    with app.app_context():
        try:
            users = User.query.all()
            if not users:
                return True
            
            audit_created = 0
            
            # Create various audit log entries
            actions = [
                ('LOGIN', 'users'),
                ('CREATE', 'daily_statuses'),
                ('UPDATE', 'daily_statuses'),
                ('APPROVE', 'daily_statuses'),
                ('CREATE', 'vendors'),
                ('UPDATE', 'system_configurations')
            ]
            
            # Create audit logs for past 14 days
            for days_back in range(14):
                audit_date = datetime.utcnow() - timedelta(days=days_back)
                
                # Create 5-10 audit entries per day
                for _ in range(random.randint(5, 10)):
                    action, table_name = random.choice(actions)
                    user = random.choice(users)
                    
                    audit_log = AuditLog(
                        user_id=user.id,
                        action=action,
                        table_name=table_name,
                        record_id=random.randint(1, 100),
                        old_values='{}',
                        new_values='{"updated": true}',
                        ip_address=f"192.168.1.{random.randint(100, 200)}",
                        user_agent='Mozilla/5.0 (Sample User Agent)',
                        created_at=audit_date
                    )
                    
                    db.session.add(audit_log)
                    audit_created += 1
            
            db.session.commit()
            print(f"   ✅ Created {audit_created} audit log entries")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating audit trail: {e}")
            return False

def verify_sample_data():
    """Verify all sample data was created correctly"""
    print("\n🔍 Verifying sample data...")
    
    with app.app_context():
        try:
            # Count records in each table
            counts = {
                'Users': User.query.count(),
                'Vendors': Vendor.query.count(),
                'Managers': Manager.query.count(),
                'Daily Statuses': DailyStatus.query.count(),
                'Swipe Records': SwipeRecord.query.count(),
                'Holidays': Holiday.query.count(),
                'Mismatch Records': MismatchRecord.query.count(),
                'Notifications': NotificationLog.query.count(),
                'Audit Logs': AuditLog.query.count()
            }
            
            print("   📊 Record counts:")
            for table, count in counts.items():
                print(f"      {table}: {count}")
            
            # Verify minimum expected counts
            if counts['Users'] < 6:  # Admin + 3 managers + 5 vendors
                print("   ⚠️ Warning: Expected more users")
            
            if counts['Daily Statuses'] < 100:
                print("   ⚠️ Warning: Expected more attendance data")
            
            print("   ✅ Sample data verification complete")
            return True
            
        except Exception as e:
            print(f"❌ Error verifying sample data: {e}")
            return False

def main():
    """Main sample data loading function"""
    print(f"📁 Working directory: {ROOT}")
    print(f"📊 Database file: {ROOT}/vendor_timesheet.db")
    
    # Step 0: Check database initialization
    if not check_database_initialized():
        print("\n❌ Database not properly initialized")
        print("🔧 Please run this first: python 1_initialize_database.py")
        sys.exit(1)
    
    # Step 1: Create sample users and profiles
    if not create_sample_users_and_profiles():
        print("\n❌ Failed to create sample users and profiles")
        sys.exit(1)
    
    # Step 2: Generate attendance data
    if not generate_attendance_data():
        print("\n❌ Failed to generate attendance data")
        sys.exit(1)
    
    # Step 3: Create sample mismatches
    if not create_sample_mismatches():
        print("\n⚠️ Warning: Failed to create mismatches (non-critical)")
    
    # Step 4: Create sample notifications
    if not create_sample_notifications():
        print("\n⚠️ Warning: Failed to create notifications (non-critical)")
    
    # Step 5: Create audit trail
    if not create_audit_trail():
        print("\n⚠️ Warning: Failed to create audit trail (non-critical)")
    
    # Step 6: Verify sample data
    if not verify_sample_data():
        print("\n❌ Sample data verification failed")
        sys.exit(1)
    
    # Success
    print("\n" + "=" * 50)
    print("🎉 SAMPLE DATA LOADING COMPLETE!")
    print("=" * 50)
    print("\n✅ What was created:")
    print("   👥 9 user accounts (1 Admin, 3 Managers, 5 Vendors)")
    print("   📅 45 days of realistic attendance data")
    print("   🏢 Swipe records with realistic office hours")
    print("   🔍 Intentional mismatches for reconciliation demo")
    print("   📬 Sample notifications and audit trail")
    print("   🎉 Holiday calendar and system configuration")
    
    print("\n🔑 Login Credentials:")
    print("   👑 Admin:    Admin / admin123")
    print("   👔 Manager:  manager1 / manager123 (also manager2, manager3)")
    print("   👤 Vendor:   EMP001 / vendor123 (also EMP002-EMP005)")
    print("   📝 Note:     Vendor usernames match their Employee IDs for consistency")
    
    print("\n🚀 Ready to run:")
    print("   1. Start app: python app.py")
    print("   2. Visit: http://localhost:5000")
    print("   3. Explore dashboards with different user roles")
    print("   4. Check reconciliation: /admin/reconciliation")
    print("   5. View sample data: python scripts/view_database.py")

if __name__ == '__main__':
    main()
