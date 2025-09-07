from datetime import datetime, date, timedelta
import random
import json
from werkzeug.security import generate_password_hash
from models import (User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday, 
                   MismatchRecord, NotificationLog, AuditLog, SystemConfiguration, 
                   LeaveRecord, WFHRecord, UserRole, AttendanceStatus, ApprovalStatus)
import models

def create_enhanced_demo_data():
    """Create comprehensive demo data for hackathon demonstration"""
    from app import app
    
    print("Creating enhanced demo data for hackathon...")
    
    with app.app_context():
        try:
            # Clear existing data
            models.db.drop_all()
            models.db.create_all()
            
            models.db.session.query(NotificationLog).delete()
            models.db.session.query(MismatchRecord).delete()
            models.db.session.query(SwipeRecord).delete()
            models.db.session.query(DailyStatus).delete()
            models.db.session.query(WFHRecord).delete()
            models.db.session.query(LeaveRecord).delete()
            models.db.session.query(SystemConfiguration).delete()
            models.db.session.query(Holiday).delete()
            models.db.session.query(Vendor).delete()
            models.db.session.query(Manager).delete()
            models.db.session.query(User).delete()
            models.db.session.commit()
            
            # Create Admin User
            admin_user = User(
            username='admin',
            email='admin@attendo.com',
            role=UserRole.ADMIN,
            is_active=True,
            last_login=datetime.utcnow() - timedelta(minutes=15)
        )
        admin_user.set_password('admin123')
        models.db.session.add(admin_user)
        models.db.session.commit()
        
        # Create 8 Manager Users (as per demo script requirement)
        managers_data = [
            {'name': 'Sarah Johnson', 'email': 'sarah.johnson@attendo.com', 'dept': 'ATD_WCS_MSE7_MS1', 'team': 'Team Alpha', 'username': 'manager1'},
            {'name': 'Michael Chen', 'email': 'michael.chen@attendo.com', 'dept': 'ATD_WCS_MSE7_MS2', 'team': 'Team Beta', 'username': 'manager2'},
            {'name': 'Emily Davis', 'email': 'emily.davis@attendo.com', 'dept': 'ATD_WCS_MSE7_MS3', 'team': 'Team Gamma', 'username': 'manager3'},
            {'name': 'Robert Wilson', 'email': 'robert.wilson@attendo.com', 'dept': 'ATD_WCS_MSE7_MS4', 'team': 'Team Delta', 'username': 'manager4'},
            {'name': 'Lisa Anderson', 'email': 'lisa.anderson@attendo.com', 'dept': 'ATD_WCS_MSE7_MS5', 'team': 'Team Echo', 'username': 'manager5'},
            {'name': 'David Martinez', 'email': 'david.martinez@attendo.com', 'dept': 'ATD_WCS_MSE7_MS6', 'team': 'Team Foxtrot', 'username': 'manager6'},
            {'name': 'Jennifer Taylor', 'email': 'jennifer.taylor@attendo.com', 'dept': 'ATD_WCS_MSE7_MS7', 'team': 'Team Golf', 'username': 'manager7'},
            {'name': 'Christopher Lee', 'email': 'christopher.lee@attendo.com', 'dept': 'ATD_WCS_MSE7_MS8', 'team': 'Team Hotel', 'username': 'manager8'}
        ]
        
        managers = []
        for i, mgr_data in enumerate(managers_data):
            # Create User
            user = User(
                username=mgr_data['username'],
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
        
        # Create 45 Vendor Users (as per demo script requirement)
        vendor_companies = [
            'TechFlow Solutions', 'DataBridge Innovations', 'CloudSync Systems', 
            'DevOps Partners', 'AgileCore Technologies', 'NextGen Solutions',
            'SmartFlow Dynamics', 'CodeCraft Solutions', 'InnovateTech Hub',
            'DigitalEdge Partners', 'TechVantage Solutions', 'FlexiCode Systems'
        ]
        
        vendor_departments = [
            'ATD_WCS_MSE7_MS1', 'ATD_WCS_MSE7_MS2', 'ATD_WCS_MSE7_MS3', 'ATD_WCS_MSE7_MS4',
            'ATD_WCS_MSE7_MS5', 'ATD_WCS_MSE7_MS6', 'ATD_WCS_MSE7_MS7', 'ATD_WCS_MSE7_MS8'
        ]
        
        vendors = []
        for i in range(45):
            # Create User
            username = f'vendor{i+1}'
            company = random.choice(vendor_companies)
            department = vendor_departments[i % 8]  # Distribute across 8 departments
            
            user = User(
                username=username,
                email=f'{username}@{company.lower().replace(" ", "")}.com',
                role=UserRole.VENDOR,
                is_active=True,
                last_login=datetime.utcnow() - timedelta(hours=random.randint(1, 72))
            )
            user.set_password('vendor123')
            models.db.session.add(user)
            models.db.session.commit()
            
            # Create Vendor Profile
            vendor = Vendor(
                user_id=user.id,
                vendor_id=f'VND{str(i+1).zfill(3)}',
                full_name=f'Vendor {i+1} Name',
                department=department,
                company=company,
                band=random.choice(['B1', 'B2', 'B3']),
                location='BL-A-5F',
                manager_id=managers[i % 8].id  # Distribute across 8 managers
            )
            models.db.session.add(vendor)
            vendors.append(vendor)
        
        models.db.session.commit()
        
        # Create 2025 Holidays
        holidays_data = [
            (date(2025, 1, 1), 'New Year Day'),
            (date(2025, 1, 26), 'Republic Day'),
            (date(2025, 3, 14), 'Holi'),
            (date(2025, 4, 18), 'Good Friday'),
            (date(2025, 5, 1), 'Labor Day'),
            (date(2025, 8, 15), 'Independence Day'),
            (date(2025, 10, 2), 'Gandhi Jayanti'),
            (date(2025, 10, 20), 'Dussehra'),
            (date(2025, 11, 8), 'Diwali'),
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
        
        # Create Daily Status Records (Last 60 days for better AI predictions)
        status_options = [
            AttendanceStatus.IN_OFFICE_FULL,
            AttendanceStatus.IN_OFFICE_HALF,
            AttendanceStatus.WFH_FULL,
            AttendanceStatus.WFH_HALF,
            AttendanceStatus.LEAVE_FULL,
            AttendanceStatus.LEAVE_HALF
        ]
        
        locations = ['BL-A-5F', 'Home', 'BL-B-3F', 'Client Site', 'Remote']
        comments_pool = [
            'Project milestone work', 'Client deliverable', 'Team collaboration',
            'Technical documentation', 'Code review session', 'Sprint planning',
            'System maintenance', 'Training session', 'Meeting with stakeholders',
            'Working on critical bug fix', ''
        ]
        
        start_date = date.today() - timedelta(days=60)
        end_date = date.today()
        
        current_date = start_date
        while current_date <= end_date:
            # Skip weekends and holidays
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            is_holiday = any(h.holiday_date == current_date for h in models.db.session.query(Holiday).all())
            if is_holiday:
                current_date += timedelta(days=1)
                continue
            
            for vendor in vendors:
                # Create patterns for specific vendors for AI demo
                if vendor.vendor_id == 'VND001':  # vendor1 - high Monday absence risk
                    if current_date.weekday() == 0 and random.random() < 0.4:  # 40% Monday absence
                        # Skip Monday submissions for pattern
                        current_date += timedelta(days=1)
                        continue
                elif vendor.vendor_id == 'VND002':  # vendor2 - high WFH pattern
                    wfh_probability = 0.6  # 60% WFH
                else:
                    wfh_probability = 0.2  # Normal 20% WFH
                
                # 90% chance of submitting status (higher for demo)
                if random.random() < 0.90:
                    # Determine status based on patterns
                    if random.random() < 0.65:  # 65% in office
                        status = random.choice([AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF])
                        location = random.choice(['BL-A-5F', 'BL-B-3F', 'Client Site'])
                    elif random.random() < wfh_probability:  # Variable WFH chance
                        status = random.choice([AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF])
                        location = 'Home'
                    else:  # Leave
                        status = random.choice([AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF])
                        location = ''
                    
                    # Create status with realistic submission times
                    submitted_time = datetime.combine(current_date, datetime.min.time()) + timedelta(
                        hours=random.randint(8, 11),
                        minutes=random.randint(0, 59)
                    )
                    
                    daily_status = DailyStatus(
                        vendor_id=vendor.id,
                        status_date=current_date,
                        status=status,
                        location=location,
                        comments=random.choice(comments_pool),
                        submitted_at=submitted_time,
                        approval_status=random.choice([
                            ApprovalStatus.APPROVED, ApprovalStatus.APPROVED, 
                            ApprovalStatus.APPROVED, ApprovalStatus.PENDING
                        ])  # 75% approved, 25% pending
                    )
                    
                    # If approved, set approval details
                    if daily_status.approval_status == ApprovalStatus.APPROVED:
                        daily_status.approved_by = vendor.manager.user_id
                        daily_status.approved_at = submitted_time + timedelta(hours=random.randint(1, 8))
                    
                    models.db.session.add(daily_status)
            
            current_date += timedelta(days=1)
        
        models.db.session.commit()
        
        # Create Swipe Records for reconciliation (last 30 days)
        swipe_start = date.today() - timedelta(days=30)
        
        for vendor in vendors[:25]:  # Create swipe records for 25 vendors
            current_date = swipe_start
            while current_date <= date.today():
                if current_date.weekday() >= 5 or any(h.holiday_date == current_date for h in models.db.session.query(Holiday).all()):
                    current_date += timedelta(days=1)
                    continue
                
                # 85% chance of swipe record
                if random.random() < 0.85:
                    swipe_status = random.choice(['AP', 'AA'])  # Present/Absent
                    
                    login_time = None
                    logout_time = None
                    total_hours = 0
                    
                    if swipe_status == 'AP':  # Present
                        login_hour = random.randint(8, 10)
                        login_minute = random.randint(0, 59)
                        login_time = datetime.combine(current_date, datetime.min.time()) + timedelta(
                            hours=login_hour, minutes=login_minute
                        )
                        
                        logout_hour = random.randint(17, 19)
                        logout_minute = random.randint(0, 59)
                        logout_time = datetime.combine(current_date, datetime.min.time()) + timedelta(
                            hours=logout_hour, minutes=logout_minute
                        )
                        
                        total_hours = (logout_time - login_time).total_seconds() / 3600
                    
                    swipe_record = SwipeRecord(
                        vendor_id=vendor.id,
                        attendance_date=current_date,
                        weekday=current_date.strftime('%A'),
                        login_time=login_time.time() if login_time else None,
                        logout_time=logout_time.time() if logout_time else None,
                        total_hours=round(total_hours, 2),
                        attendance_status=swipe_status
                    )
                    models.db.session.add(swipe_record)
                
                current_date += timedelta(days=1)
        
        models.db.session.commit()
        
        # Create Mismatch Records for demo (targeting specific scenarios)
        mismatches_created = 0
        for vendor in vendors[:10]:  # Create mismatches for first 10 vendors
            recent_statuses = DailyStatus.query.filter(
                DailyStatus.vendor_id == vendor.id,
                DailyStatus.status_date >= date.today() - timedelta(days=15)
            ).limit(3).all()
            
            for status in recent_statuses[:2]:  # Max 2 mismatches per vendor
                swipe = SwipeRecord.query.filter_by(
                    vendor_id=vendor.id,
                    attendance_date=status.status_date
                ).first()
                
                if swipe:
                    # Create strategic mismatches
                    create_mismatch = False
                    
                    if status.status == AttendanceStatus.IN_OFFICE_FULL and swipe.attendance_status == 'AP':
                        # Change swipe to absent to create mismatch
                        swipe.attendance_status = 'AA'
                        swipe.login_time = None
                        swipe.logout_time = None
                        swipe.total_hours = 0
                        create_mismatch = True
                    elif status.status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF] and swipe.attendance_status == 'AP':
                        # Leave vs Present mismatch
                        create_mismatch = True
                    
                    if create_mismatch:
                        mismatch = MismatchRecord(
                            vendor_id=vendor.id,
                            mismatch_date=status.status_date,
                            web_status=status.status,
                            swipe_status=swipe.attendance_status
                        )
                        
                        # 70% have vendor explanations
                        if random.random() < 0.7:
                            explanations = [
                                'Forgot to swipe due to urgent client call - was in office all day',
                                'Card reader malfunction in the morning, IT ticket #INC-2024-5847',
                                'Emergency meeting in different building, unable to swipe at usual location',
                                'System maintenance window affected swipe machine functionality',
                                'Attended off-site client meeting, have email confirmation as proof',
                                'Family emergency required early departure, informed manager via Teams'
                            ]
                            mismatch.vendor_reason = random.choice(explanations)
                            mismatch.vendor_submitted_at = datetime.utcnow() - timedelta(
                                hours=random.randint(2, 48)
                            )
                        
                        models.db.session.add(mismatch)
                        mismatches_created += 1
        
        models.db.session.commit()
        
        # Create Leave Records for realistic data
        leave_types = ['Earned Leave (EL)', 'Casual Leave (CL)', 'Sick Leave (SL)', 
                      'Maternity Leave', 'Personal Leave', 'Comp Off']
        
        for vendor in vendors[:30]:  # Create leave records for 30 vendors
            for _ in range(random.randint(2, 5)):
                start_date_leave = date.today() - timedelta(days=random.randint(10, 90))
                duration = random.randint(1, 7)
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
        
        # Create WFH Records
        for vendor in vendors[:35]:  # Create WFH records for 35 vendors
            for _ in range(random.randint(3, 8)):
                start_date_wfh = date.today() - timedelta(days=random.randint(5, 60))
                duration = random.randint(1, 5)
                end_date_wfh = start_date_wfh + timedelta(days=duration-1)
                
                wfh_record = WFHRecord(
                    vendor_id=vendor.id,
                    start_date=start_date_wfh,
                    end_date=end_date_wfh,
                    duration_days=duration
                )
                models.db.session.add(wfh_record)
        
        models.db.session.commit()
        
        # Create Rich Notification Logs
        notification_types = [
            'daily_reminder', 'team_summary', 'mismatch_alert', 'daily_summary',
            'absence_prediction', 'approval_pending', 'system_update', 'report_ready'
        ]
        
        notification_messages = {
            'daily_reminder': 'Reminder: Please submit your daily attendance status',
            'team_summary': 'Team attendance summary for today',
            'mismatch_alert': 'New attendance mismatch detected requiring review',
            'daily_summary': 'End-of-day team summary report',
            'absence_prediction': 'AI prediction: High absence risk detected for tomorrow',
            'approval_pending': 'Pending attendance status approvals require your attention',
            'system_update': 'System maintenance completed successfully',
            'report_ready': 'Monthly attendance report generated and ready for download'
        }
        
        for user in User.query.all():
            for _ in range(random.randint(5, 15)):
                notif_type = random.choice(notification_types)
                notification = NotificationLog(
                    recipient_id=user.id,
                    notification_type=notif_type,
                    message=notification_messages.get(notif_type, 'System notification'),
                    sent_at=datetime.utcnow() - timedelta(hours=random.randint(1, 168)),
                    is_read=random.random() < 0.65  # 65% read rate
                )
                models.db.session.add(notification)
        
        models.db.session.commit()
        
        # Create System Configurations
        configs = [
            ('reminder_interval_hours', '3', 'Hours between reminder notifications'),
            ('manager_notification_times', '12,14,18', 'Hours when manager notifications are sent'),
            ('working_hours_start', '09:00', 'Standard working hours start time'),
            ('working_hours_end', '18:00', 'Standard working hours end time'),
            ('auto_approve_days', '7', 'Days after which pending statuses are auto-approved'),
            ('mismatch_detection_enabled', 'true', 'Enable automatic mismatch detection'),
            ('ai_prediction_enabled', 'true', 'Enable AI absence predictions'),
            ('ai_model_accuracy', '94.2', 'Current AI model accuracy percentage'),
            ('notification_teams_webhook', 'https://outlook.office.com/webhook/demo', 'Teams webhook URL'),
            ('export_formats_enabled', 'excel,pdf,csv,json', 'Enabled export formats'),
            ('max_file_upload_size', '10', 'Maximum file upload size in MB'),
            ('session_timeout_hours', '8', 'User session timeout in hours')
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
        
        # Create Comprehensive Audit Logs
        actions = ['LOGIN', 'CREATE', 'UPDATE', 'APPROVE', 'REJECT', 'IMPORT', 'EXPORT', 'DELETE']
        tables = ['daily_statuses', 'users', 'vendors', 'mismatch_records', 'swipe_records', 
                 'leave_records', 'wfh_records', 'system_configurations']
        
        for _ in range(200):  # Create 200 audit log entries
            action = random.choice(actions)
            table = random.choice(tables)
            user_id = random.choice([u.id for u in User.query.all()])
            
            # Create realistic audit data
            old_values = {}
            new_values = {}
            
            if action == 'UPDATE' and table == 'daily_statuses':
                old_values = {'status': 'in_office_full', 'approval_status': 'pending'}
                new_values = {'status': 'wfh_full', 'approval_status': 'approved'}
            elif action == 'APPROVE':
                old_values = {'approval_status': 'pending'}
                new_values = {'approval_status': 'approved', 'approved_by': user_id}
            elif action == 'IMPORT':
                new_values = {'records_imported': random.randint(50, 200), 'file_name': f'swipe_data_{random.randint(1000, 9999)}.xlsx'}
            
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                table_name=table,
                record_id=random.randint(1, 1000),
                old_values=json.dumps(old_values),
                new_values=json.dumps(new_values),
                ip_address=f'192.168.{random.randint(0, 255)}.{random.randint(1, 255)}',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 336))  # Last 2 weeks
            )
            models.db.session.add(audit_log)
        
        models.db.session.commit()
        
        print(f"✅ Enhanced demo data created successfully!")
        print(f"📊 Summary:")
        print(f"  - 1 Admin user (admin/admin123)")
        print(f"  - 8 Manager users (manager1-8/manager123)")
        print(f"  - 45 Vendor users (vendor1-45/vendor123)")
        print(f"  - 10 Holidays for 2025")
        print(f"  - 60 days of attendance data with patterns")
        print(f"  - 25 vendors with swipe records")
        print(f"  - {mismatches_created} strategic mismatch records")
        print(f"  - Leave and WFH records for realistic scenarios")
        print(f"  - Rich notification logs")
        print(f"  - 12 system configurations")
        print(f"  - 200 comprehensive audit trail entries")
        print(f"")
        print(f"🎯 Demo-Ready Features:")
        print(f"  ✅ AI predictions with 94.2% accuracy simulation")
        print(f"  ✅ Specific vendor patterns (vendor1 = Monday absence risk)")
        print(f"  ✅ Realistic mismatch scenarios with explanations")
        print(f"  ✅ Complete workflow data for all user roles")
        print(f"  ✅ Rich audit trail for compliance demo")
        print(f"  ✅ Notification system with realistic messages")
        print(f"")
        print(f"🎬 Hackathon Demo Credentials:")
        print(f"   👨‍💻 Admin: admin/admin123")
        print(f"   👨‍💼 Manager: manager1-8/manager123")
        print(f"   👤 Vendor: vendor1-45/vendor123")
        print(f"")
        print(f"🚀 System is now ready for hackathon presentation!")
        
            return True
            
        except Exception as e:
            models.db.session.rollback()
            print(f"❌ Error creating demo data: {str(e)}")
            return False

if __name__ == '__main__':
    create_enhanced_demo_data()
