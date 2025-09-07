from datetime import datetime, date, timedelta
import random
from werkzeug.security import generate_password_hash
from models import User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday, MismatchRecord, NotificationLog, AuditLog, SystemConfiguration, LeaveRecord, WFHRecord, UserRole, AttendanceStatus, ApprovalStatus
import models

def create_demo_data():
    """Create comprehensive demo data for hackathon presentation"""
    
    print("Creating demo data...")
    
    # Create Admin User
    admin_user = User(
        username='admin',
        email='admin@attendo.com',
        role=UserRole.ADMIN,
        is_active=True
    )
    admin_user.set_password('admin123')
    models.db.session.add(admin_user)
    models.db.session.commit()
    
    # Create Manager Users
    managers_data = [
        {'name': 'Sarah Johnson', 'email': 'sarah.johnson@attendo.com', 'dept': 'ATD_WCS_MSE7_MS1', 'team': 'Team Alpha'},
        {'name': 'Michael Chen', 'email': 'michael.chen@attendo.com', 'dept': 'ATD_WCS_MSE7_MS2', 'team': 'Team Beta'},
        {'name': 'Emily Davis', 'email': 'emily.davis@attendo.com', 'dept': 'ATD_WCS_MSE7_MS3', 'team': 'Team Gamma'}
    ]
    
    managers = []
    for i, mgr_data in enumerate(managers_data):
        # Create User
        user = User(
            username=f'manager{i+1}',
            email=mgr_data['email'],
            role=UserRole.MANAGER,
            is_active=True,
            last_login=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )
        user.set_password('manager123')
        models.db.session.add(user)
        models.db.session.commit()
        
        # Create Manager Profile
        manager = Manager(
            user_id=user.id,
            full_name=mgr_data['name'],
            department=mgr_data['dept'],
            team_name=mgr_data['team']
        )
        models.db.session.add(manager)
        managers.append(manager)
    
    models.db.session.commit()
    
    # Create Vendor Users
    vendors_data = [
        {'name': 'John Doe', 'email': 'john.doe@vendor1.com', 'vendor_id': 'VND001', 'company': 'ABC Solutions', 'band': 'B2', 'dept': 'MTB_WCS_MSE7_MS1'},
        {'name': 'Jane Smith', 'email': 'jane.smith@vendor1.com', 'vendor_id': 'VND002', 'company': 'ABC Solutions', 'band': 'B3', 'dept': 'MTB_WCS_MSE7_MS1'},
        {'name': 'Robert Wilson', 'email': 'robert.wilson@vendor2.com', 'vendor_id': 'VND003', 'company': 'XYZ Technologies', 'band': 'B2', 'dept': 'MTB_WCS_MSE7_MS1'},
        {'name': 'Lisa Brown', 'email': 'lisa.brown@vendor2.com', 'vendor_id': 'VND004', 'company': 'XYZ Technologies', 'band': 'B3', 'dept': 'MTB_WCS_MSE7_MS2'},
        {'name': 'David Lee', 'email': 'david.lee@vendor3.com', 'vendor_id': 'VND005', 'company': 'Tech Partners', 'band': 'B2', 'dept': 'MTB_WCS_MSE7_MS2'},
        {'name': 'Maria Garcia', 'email': 'maria.garcia@vendor3.com', 'vendor_id': 'VND006', 'company': 'Tech Partners', 'band': 'B1', 'dept': 'MTB_WCS_MSE7_MS2'},
        {'name': 'James Miller', 'email': 'james.miller@vendor4.com', 'vendor_id': 'VND007', 'company': 'Digital Innovations', 'band': 'B2', 'dept': 'MTB_WCS_MSE7_MS3'},
        {'name': 'Anna Taylor', 'email': 'anna.taylor@vendor4.com', 'vendor_id': 'VND008', 'company': 'Digital Innovations', 'band': 'B3', 'dept': 'MTB_WCS_MSE7_MS3'},
        {'name': 'Chris Anderson', 'email': 'chris.anderson@vendor5.com', 'vendor_id': 'VND009', 'company': 'Smart Systems', 'band': 'B2', 'dept': 'MTB_WCS_MSE7_MS3'},
        {'name': 'Sophie Martin', 'email': 'sophie.martin@vendor5.com', 'vendor_id': 'VND010', 'company': 'Smart Systems', 'band': 'B1', 'dept': 'MTB_WCS_MSE7_MS1'}
    ]
    
    vendors = []
    for i, vendor_data in enumerate(vendors_data):
        # Create User
        user = User(
            username=f'vendor{i+1}',
            email=vendor_data['email'],
            role=UserRole.VENDOR,
            is_active=True,
            last_login=datetime.utcnow() - timedelta(hours=random.randint(1, 24))
        )
        user.set_password('vendor123')
        models.db.session.add(user)
        models.db.session.commit()
        
        # Assign to manager based on department
        manager = None
        if 'MS1' in vendor_data['dept']:
            manager = managers[0]
        elif 'MS2' in vendor_data['dept']:
            manager = managers[1]
        elif 'MS3' in vendor_data['dept']:
            manager = managers[2]
        
        # Create Vendor Profile
        vendor = Vendor(
            user_id=user.id,
            vendor_id=vendor_data['vendor_id'],
            full_name=vendor_data['name'],
            department=vendor_data['dept'],
            company=vendor_data['company'],
            band=vendor_data['band'],
            location='BL-A-5F',
            manager_id=manager.id if manager else None
        )
        models.db.session.add(vendor)
        vendors.append(vendor)
    
    models.db.session.commit()
    
    # Create Holidays
    holidays_data = [
        (date(2025, 1, 1), 'New Year\'s Day'),
        (date(2025, 1, 26), 'Republic Day'),
        (date(2025, 3, 14), 'Holi'),
        (date(2025, 8, 15), 'Independence Day'),
        (date(2025, 10, 2), 'Gandhi Jayanti'),
        (date(2025, 11, 1), 'Diwali'),
        (date(2025, 12, 25), 'Christmas Day')
    ]
    
    for holiday_date, holiday_name in holidays_data:
        holiday = Holiday(
            holiday_date=holiday_date,
            name=holiday_name,
            description=f'National holiday - {holiday_name}',
            created_by=admin_user.id
        )
        models.db.session.add(holiday)
    
    models.db.session.commit()
    
    # Create Daily Status Records (Last 30 days)
    status_options = [
        AttendanceStatus.IN_OFFICE_FULL,
        AttendanceStatus.IN_OFFICE_HALF,
        AttendanceStatus.WFH_FULL,
        AttendanceStatus.WFH_HALF,
        AttendanceStatus.LEAVE_FULL,
        AttendanceStatus.LEAVE_HALF
    ]
    
    locations = ['BL-A-5F', 'Home', 'BL-B-3F', 'Client Site']
    
    start_date = date.today() - timedelta(days=30)
    end_date = date.today()
    
    current_date = start_date
    while current_date <= end_date:
        # Skip weekends and holidays
        if current_date.weekday() >= 5:  # Weekend
            current_date += timedelta(days=1)
            continue
        
        is_holiday = any(h.holiday_date == current_date for h in models.db.session.query(Holiday).all())
        if is_holiday:
            current_date += timedelta(days=1)
            continue
        
        for vendor in vendors:
            # 85% chance of submitting status
            if random.random() < 0.85:
                status = random.choice(status_options)
                
                # Adjust probabilities for more realistic data
                if random.random() < 0.7:  # 70% chance in office
                    status = random.choice([AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF])
                elif random.random() < 0.2:  # 20% chance WFH
                    status = random.choice([AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF])
                else:  # 10% chance leave
                    status = random.choice([AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF])
                
                location = random.choice(locations)
                if status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]:
                    location = 'Home'
                elif status in [AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF]:
                    location = 'BL-A-5F'
                
                # Create status with some submitted in the past
                submitted_time = datetime.combine(current_date, datetime.min.time()) + timedelta(
                    hours=random.randint(8, 11),
                    minutes=random.randint(0, 59)
                )
                
                daily_status = DailyStatus(
                    vendor_id=vendor.id,
                    status_date=current_date,
                    status=status,
                    location=location,
                    comments=random.choice(['', 'Working on project X', 'Client meeting', 'Training session', '']),
                    submitted_at=submitted_time,
                    approval_status=random.choice([ApprovalStatus.APPROVED, ApprovalStatus.PENDING, ApprovalStatus.APPROVED, ApprovalStatus.APPROVED])  # Mostly approved
                )
                
                # If approved, set approval details
                if daily_status.approval_status == ApprovalStatus.APPROVED:
                    daily_status.approved_by = vendor.manager.user_id if vendor.manager else admin_user.id
                    daily_status.approved_at = submitted_time + timedelta(hours=random.randint(1, 6))
                
                models.db.session.add(daily_status)
        
        current_date += timedelta(days=1)
    
    models.db.session.commit()
    
    # Create some Swipe Records for reconciliation demo
    swipe_statuses = ['AP', 'AA']  # Present, Absent
    
    for vendor in vendors[:5]:  # Only for first 5 vendors
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() >= 5 or any(h.holiday_date == current_date for h in models.db.session.query(Holiday).all()):
                current_date += timedelta(days=1)
                continue
            
            # 90% chance of swipe record
            if random.random() < 0.9:
                swipe_status = random.choice(swipe_statuses)
                
                login_time = None
                logout_time = None
                total_hours = 0
                
                if swipe_status == 'AP':  # Present
                    login_hour = random.randint(8, 10)
                    login_minute = random.randint(0, 59)
                    login_time = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=login_hour, minutes=login_minute)
                    
                    logout_hour = random.randint(17, 19)
                    logout_minute = random.randint(0, 59)
                    logout_time = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=logout_hour, minutes=logout_minute)
                    
                    total_hours = (logout_time - login_time).total_seconds() / 3600
                
                swipe_record = SwipeRecord(
                    vendor_id=vendor.id,
                    attendance_date=current_date,
                    weekday=current_date.strftime('%A'),
                    login_time=login_time.time() if login_time else None,
                    logout_time=logout_time.time() if logout_time else None,
                    total_hours=total_hours,
                    attendance_status=swipe_status
                )
                models.db.session.add(swipe_record)
            
            current_date += timedelta(days=1)
    
    models.db.session.commit()
    
    # Create some Mismatch Records
    mismatches_created = 0
    for vendor in vendors[:3]:  # Create mismatches for first 3 vendors
        # Find dates where there might be mismatches
        recent_statuses = DailyStatus.query.filter(
            DailyStatus.vendor_id == vendor.id,
            DailyStatus.status_date >= date.today() - timedelta(days=15)
        ).all()
        
        for status in recent_statuses[:2]:  # Only 2 mismatches per vendor
            swipe = SwipeRecord.query.filter_by(
                vendor_id=vendor.id,
                attendance_date=status.status_date
            ).first()
            
            if swipe:
                # Create intentional mismatch
                if status.status == AttendanceStatus.IN_OFFICE_FULL and swipe.attendance_status == 'AP':
                    # Change swipe to absent to create mismatch
                    swipe.attendance_status = 'AA'
                    swipe.login_time = None
                    swipe.logout_time = None
                    swipe.total_hours = 0
                    
                    mismatch = MismatchRecord(
                        vendor_id=vendor.id,
                        mismatch_date=status.status_date,
                        web_status=status.status,
                        swipe_status='AA'
                    )
                    
                    # Some mismatches have vendor explanations
                    if random.random() < 0.6:
                        explanations = [
                            'Forgot to swipe due to urgent meeting',
                            'Card reader was not working',
                            'Emergency call from client, left without swiping',
                            'System maintenance on that day'
                        ]
                        mismatch.vendor_reason = random.choice(explanations)
                        mismatch.vendor_submitted_at = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
                    
                    models.db.session.add(mismatch)
                    mismatches_created += 1
    
    models.db.session.commit()
    
    # Create Notification Logs
    notification_types = ['daily_reminder', 'team_summary', 'mismatch_alert', 'daily_summary']
    
    for user in User.query.all():
        # Create some recent notifications
        for _ in range(random.randint(1, 5)):
            notification = NotificationLog(
                recipient_id=user.id,
                notification_type=random.choice(notification_types),
                message=f'Sample notification message for {user.username}',
                sent_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
                is_read=random.random() < 0.7  # 70% chance of being read
            )
            models.db.session.add(notification)
    
    models.db.session.commit()
    
    # Create System Configurations
    configs = [
        ('reminder_interval_hours', '3', 'Hours between reminder notifications'),
        ('manager_notification_times', '12,14', 'Hours when manager notifications are sent'),
        ('working_hours_start', '09:00', 'Standard working hours start time'),
        ('working_hours_end', '18:00', 'Standard working hours end time'),
        ('auto_approve_days', '7', 'Days after which pending statuses are auto-approved'),
        ('mismatch_detection_enabled', 'true', 'Enable automatic mismatch detection')
    ]
    
    for key, value, description in configs:
        config = SystemConfiguration(
            key=key,
            value=value,
            description=description,
            updated_by=admin_user.id
        )
        models.db.session.add(config)
    
    models.db.session.commit()
    
    # Create some Leave Records
    leave_types = ['Earned Leave(EL)', 'Casual leave(CL)', 'Sick leave(SL)', 'Personal Leave']
    
    for vendor in vendors[:6]:  # Create leave records for first 6 vendors
        for _ in range(random.randint(1, 3)):
            start_date_leave = date.today() - timedelta(days=random.randint(5, 60))
            duration = random.randint(1, 5)
            end_date_leave = start_date_leave + timedelta(days=duration-1)
            
            leave_record = LeaveRecord(
                vendor_id=vendor.id,
                start_date=start_date_leave,
                end_date=end_date_leave,
                leave_type=random.choice(leave_types),
                total_days=duration
            )
            models.db.session.add(leave_record)
    
    models.db.session.commit()
    
    # Create some WFH Records
    for vendor in vendors[:8]:  # Create WFH records for first 8 vendors
        for _ in range(random.randint(1, 4)):
            start_date_wfh = date.today() - timedelta(days=random.randint(1, 30))
            duration = random.randint(1, 3)
            end_date_wfh = start_date_wfh + timedelta(days=duration-1)
            
            wfh_record = WFHRecord(
                vendor_id=vendor.id,
                start_date=start_date_wfh,
                end_date=end_date_wfh,
                duration_days=duration
            )
            models.db.session.add(wfh_record)
    
    models.db.session.commit()
    
    # Create Audit Logs
    actions = ['LOGIN', 'CREATE', 'UPDATE', 'APPROVE', 'REJECT']
    tables = ['daily_statuses', 'users', 'vendors', 'mismatch_records']
    
    for _ in range(50):  # Create 50 audit log entries
        audit_log = AuditLog(
            user_id=random.choice([u.id for u in User.query.all()]),
            action=random.choice(actions),
            table_name=random.choice(tables),
            record_id=random.randint(1, 100),
            old_values='{}',
            new_values='{}',
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 168))  # Last week
        )
        models.db.session.add(audit_log)
    
    models.db.session.commit()
    
    print(f"Demo data created successfully!")
    print(f"Created:")
    print(f"  - 1 Admin user (admin/admin123)")
    print(f"  - {len(managers)} Manager users (manager1-3/manager123)")
    print(f"  - {len(vendors)} Vendor users (vendor1-10/vendor123)")
    print(f"  - {len(holidays_data)} Holidays")
    print(f"  - Daily status records for last 30 days")
    print(f"  - Swipe records for reconciliation")
    print(f"  - {mismatches_created} Mismatch records")
    print(f"  - Notification logs")
    print(f"  - System configurations")
    print(f"  - Leave and WFH records")
    print(f"  - Audit trail logs")
    print(f"")
    print(f"🎉 Ready for hackathon demo!")
    print(f"📝 Login credentials:")
    print(f"   Admin: admin/admin123")
    print(f"   Managers: manager1-3/manager123")
    print(f"   Vendors: vendor1-10/vendor123")

if __name__ == '__main__':
    create_demo_data()
