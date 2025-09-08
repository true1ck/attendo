import json
import pandas as pd
from datetime import datetime, date, timedelta
from flask import request
from models import User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday, MismatchRecord, NotificationLog, AuditLog, SystemConfiguration, LeaveRecord, WFHRecord, UserRole, AttendanceStatus, ApprovalStatus
import models

def create_audit_log(user_id, action, table_name, record_id=None, old_values=None, new_values=None):
    """Create an audit log entry"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=request.remote_addr if request else None,
            user_agent=request.user_agent.string if request else None
        )
        models.db.session.add(audit_log)
        models.db.session.commit()
    except Exception as e:
        models.db.session.rollback()
        print(f"Error creating audit log: {str(e)}")

def generate_monthly_report(manager_id, month_str):
    """Generate monthly attendance report for a manager's team"""
    try:
        # Parse month string (YYYY-MM format)
        year, month = map(int, month_str.split('-'))
        
        # Calculate month start and end dates
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get manager and team vendors
        if manager_id:
            manager = Manager.query.get(manager_id)
            vendors = manager.team_vendors.all()
        else:
            vendors = Vendor.query.all()
        
        report_data = []
        
        for vendor in vendors:
            # Get all statuses for the month
            statuses = DailyStatus.query.filter(
                DailyStatus.vendor_id == vendor.id,
                DailyStatus.status_date >= start_date,
                DailyStatus.status_date <= end_date
            ).all()
            
            # Calculate statistics
            total_working_days = 0
            office_days = 0
            wfh_days = 0
            leave_days = 0
            leave_dates = []
            wfh_dates = []
            
            # Count working days (excluding weekends and holidays)
            current_date = start_date
            while current_date <= end_date:
                is_weekend = current_date.weekday() >= 5
                is_holiday = Holiday.query.filter_by(holiday_date=current_date).first() is not None
                
                if not is_weekend and not is_holiday:
                    total_working_days += 1
                
                current_date += timedelta(days=1)
            
            # Analyze statuses
            for status in statuses:
                if status.status in [AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF]:
                    office_days += 1 if status.status == AttendanceStatus.IN_OFFICE_FULL else 0.5
                elif status.status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]:
                    wfh_days += 1 if status.status == AttendanceStatus.WFH_FULL else 0.5
                    wfh_dates.append(status.status_date.strftime('%Y-%m-%d'))
                elif status.status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]:
                    leave_days += 1 if status.status == AttendanceStatus.LEAVE_FULL else 0.5
                    leave_dates.append(status.status_date.strftime('%Y-%m-%d'))
            
            report_data.append({
                'Vendor Name': vendor.full_name,
                'Email ID': vendor.user_account.email,
                'Vendor ID': vendor.vendor_id,
                'Department': vendor.department,
                'Vending Company': vendor.company,
                'Band': vendor.band,
                'Total Working Days': total_working_days,
                'Total Office Days': office_days,
                'Total WFH Days': wfh_days,
                'Total Leave Days': leave_days,
                'Leave Dates': ', '.join(leave_dates),
                'WFH Dates': ', '.join(wfh_dates),
                'Comments': ''
            })
        
        return report_data
        
    except Exception as e:
        print(f"Error generating monthly report: {str(e)}")
        return []

def import_swipe_data(file_path):
    """Import attendance swipe machine data from Excel or CSV file"""
    try:
        # Read file based on extension
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        records_imported = 0
        
        for _, row in df.iterrows():
            try:
                # Map vendor by employee ID (assuming vendor_id matches Employee ID)
                vendor = Vendor.query.filter_by(vendor_id=str(row['Employee ID'])).first()
                if not vendor:
                    continue
                
                # Parse date
                attendance_date = pd.to_datetime(row['Attendance Date']).date()
                
                # Check if record already exists
                existing_record = SwipeRecord.query.filter_by(
                    vendor_id=vendor.id,
                    attendance_date=attendance_date
                ).first()
                
                if existing_record:
                    continue
                
                # Parse times
                login_time = None
                logout_time = None
                total_hours = 0
                
                if pd.notna(row['Login']) and row['Login'] != '-':
                    login_time = pd.to_datetime(row['Login']).time()
                
                if pd.notna(row['Logout']) and row['Logout'] != '-':
                    logout_time = pd.to_datetime(row['Logout']).time()
                
                if pd.notna(row['Total Working Hours']) and row['Total Working Hours'] != '-':
                    # Parse time string like "07:21" to hours
                    time_parts = str(row['Total Working Hours']).split(':')
                    if len(time_parts) == 2:
                        total_hours = float(time_parts[0]) + float(time_parts[1]) / 60
                
                # Create swipe record
                swipe_record = SwipeRecord(
                    vendor_id=vendor.id,
                    attendance_date=attendance_date,
                    weekday=row['Weekday'],
                    login_time=login_time,
                    logout_time=logout_time,
                    total_hours=total_hours,
                    attendance_status=row['Attendance Status']
                )
                
                models.db.session.add(swipe_record)
                records_imported += 1
                
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue
        
        models.db.session.commit()
        return records_imported
        
    except Exception as e:
        models.db.session.rollback()
        print(f"Error importing swipe data: {str(e)}")
        return 0

def detect_mismatches():
    """Detect mismatches between vendor entries, swipe data and leave/WFH approvals
    Rules:
    - InOffice (full/half): must have swipe AP on that date; missing swipe => mismatch
    - WFH (full/half): should not have swipe AP; if swipe AP exists => mismatch; if no WFHRecord covering date => mismatch
    - Leave (full/half): must have LeaveRecord covering date; if swipe AP exists => mismatch
    - Missing vendor entry when swipe AP exists => mismatch
    Only considers last 60 days and approved statuses
    """
    try:
        vendors = Vendor.query.all()
        mismatches_found = 0
        start_date = date.today() - timedelta(days=60)
        for vendor in vendors:
            # Approved statuses window
            statuses = DailyStatus.query.filter(
                DailyStatus.vendor_id == vendor.id,
                DailyStatus.status_date >= start_date,
                DailyStatus.approval_status == ApprovalStatus.APPROVED
            ).all()
            # Build quick date map
            status_by_date = {s.status_date: s for s in statuses}
            # Get swipe records in window
            swipes = SwipeRecord.query.filter(
                SwipeRecord.vendor_id == vendor.id,
                SwipeRecord.attendance_date >= start_date
            ).all()
            swipe_by_date = {s.attendance_date: s for s in swipes}
            # Leave records -> expand to date set
            leave_recs = LeaveRecord.query.filter(
                LeaveRecord.vendor_id == vendor.id,
                LeaveRecord.start_date >= start_date
            ).all()
            leave_dates = set()
            for lr in leave_recs:
                d = lr.start_date
                while d <= lr.end_date:
                    leave_dates.add(d)
                    d += timedelta(days=1)
            # WFH records -> expand to date set
            wfh_recs = WFHRecord.query.filter(
                WFHRecord.vendor_id == vendor.id,
                WFHRecord.start_date >= start_date
            ).all()
            wfh_dates = set()
            for wr in wfh_recs:
                d = wr.start_date
                while d <= wr.end_date:
                    wfh_dates.add(d)
                    d += timedelta(days=1)
            # Union of relevant dates
            all_dates = set(status_by_date.keys()) | set(swipe_by_date.keys()) | leave_dates | wfh_dates
            for d in all_dates:
                s = status_by_date.get(d)
                swipe = swipe_by_date.get(d)
                # Case: missing vendor entry but swipe AP exists
                if not s and swipe and swipe.attendance_status == 'AP':
                    if not MismatchRecord.query.filter_by(vendor_id=vendor.id, mismatch_date=d).first():
                        mm = MismatchRecord(vendor_id=vendor.id, mismatch_date=d, web_status=None, swipe_status='AP')
                        models.db.session.add(mm)
                        mismatches_found += 1
                    continue
                if not s:
                    continue
                web_status = s.status
                swipe_status = swipe.attendance_status if swipe else 'AA'
                detail = None
                detected = False
                # In office must have swipe AP
                if web_status in [AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF]:
                    if swipe_status != 'AP':
                        detected = True
                        detail = 'In-Office status but no swipe present'
                # WFH should not have swipe AP and must have WFH approval
                elif web_status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]:
                    if swipe_status == 'AP':
                        detected = True
                        detail = 'WFH marked but swipe shows present'
                    elif d not in wfh_dates:
                        detected = True
                        detail = 'WFH marked but no WFH approval record'
                # Leave should have leave record and no AP swipe
                elif web_status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]:
                    if d not in leave_dates:
                        detected = True
                        detail = 'Leave marked but no approved Leave record'
                    elif swipe_status == 'AP':
                        detected = True
                        detail = 'Leave marked but swipe shows present'
                if detected:
                    if not MismatchRecord.query.filter_by(vendor_id=vendor.id, mismatch_date=d).first():
                        mm = MismatchRecord(vendor_id=vendor.id, mismatch_date=d, web_status=web_status, swipe_status=swipe_status, manager_comments=detail)
                        models.db.session.add(mm)
                        mismatches_found += 1
        models.db.session.commit()
        print(f"Detected {mismatches_found} new mismatches")
        return mismatches_found
    except Exception as e:
        models.db.session.rollback()
        print(f"Error detecting mismatches: {str(e)}")
        return 0

def import_leave_data(file_path):
    """Import leave data from Excel or CSV file"""
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        records_imported = 0
        
        for _, row in df.iterrows():
            try:
                # Find vendor by personnel number (OT ID)
                vendor = Vendor.query.filter_by(vendor_id=str(row['OT ID'])).first()
                if not vendor:
                    continue
                
                start_date = pd.to_datetime(row['Start Date']).date()
                end_date = pd.to_datetime(row['End Date']).date()
                leave_type = row['Attendance or Absence Type']
                total_days = float(row['Day'])
                
                # Check if record already exists
                existing_record = LeaveRecord.query.filter_by(
                    vendor_id=vendor.id,
                    start_date=start_date,
                    end_date=end_date,
                    leave_type=leave_type
                ).first()
                
                if existing_record:
                    continue
                
                leave_record = LeaveRecord(
                    vendor_id=vendor.id,
                    start_date=start_date,
                    end_date=end_date,
                    leave_type=leave_type,
                    total_days=total_days
                )
                
                models.db.session.add(leave_record)
                records_imported += 1
                
            except Exception as e:
                print(f"Error processing leave row: {str(e)}")
                continue
        
        models.db.session.commit()
        return records_imported
        
    except Exception as e:
        models.db.session.rollback()
        print(f"Error importing leave data: {str(e)}")
        return 0

def import_wfh_data(file_path):
    """Import Work From Home data from Excel or CSV file"""
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        records_imported = 0
        
        for _, row in df.iterrows():
            try:
                # Find vendor by name (this might need adjustment based on actual data)
                vendor = Vendor.query.filter_by(full_name=str(row['RD Name'])).first()
                if not vendor:
                    continue
                
                start_date = pd.to_datetime(row['Start Date']).date()
                end_date = pd.to_datetime(row['End Date']).date()
                duration = int(row['Duration'])
                
                # Check if record already exists
                existing_record = WFHRecord.query.filter_by(
                    vendor_id=vendor.id,
                    start_date=start_date,
                    end_date=end_date
                ).first()
                
                if existing_record:
                    continue
                
                wfh_record = WFHRecord(
                    vendor_id=vendor.id,
                    start_date=start_date,
                    end_date=end_date,
                    duration_days=duration
                )
                
                models.db.session.add(wfh_record)
                records_imported += 1
                
            except Exception as e:
                print(f"Error processing WFH row: {str(e)}")
                continue
        
        models.db.session.commit()
        return records_imported
        
    except Exception as e:
        models.db.session.rollback()
        print(f"Error importing WFH data: {str(e)}")
        return 0

def get_system_config(key, default_value=None):
    """Get system configuration value"""
    config = SystemConfiguration.query.filter_by(key=key).first()
    return config.value if config else default_value

def set_system_config(key, value, description, user_id):
    """Set system configuration value"""
    config = SystemConfiguration.query.filter_by(key=key).first()
    
    if config:
        old_value = config.value
        config.value = value
        config.updated_by = user_id
        config.updated_at = datetime.utcnow()
        
        create_audit_log(user_id, 'UPDATE', 'system_configurations', config.id,
                       {'value': old_value}, {'value': value})
    else:
        config = SystemConfiguration(
            key=key,
            value=value,
            description=description,
            updated_by=user_id
        )
        models.db.session.add(config)
        
        create_audit_log(user_id, 'CREATE', 'system_configurations', None, {},
                       {'key': key, 'value': value, 'description': description})
    
    models.db.session.commit()

def calculate_working_days(start_date, end_date):
    """Calculate working days between two dates (excluding weekends and holidays)"""
    working_days = 0
    current_date = start_date
    
    # Get all holidays in the date range
    holidays = Holiday.query.filter(
        Holiday.holiday_date >= start_date,
        Holiday.holiday_date <= end_date
    ).all()
    holiday_dates = {h.holiday_date for h in holidays}
    
    while current_date <= end_date:
        # Skip weekends (Saturday=5, Sunday=6)
        if current_date.weekday() < 5 and current_date not in holiday_dates:
            working_days += 1
        current_date += timedelta(days=1)
    
    return working_days

def send_notification(recipient_id, notification_type, message):
    """Send notification to user and log it"""
    try:
        notification = NotificationLog(
            recipient_id=recipient_id,
            notification_type=notification_type,
            message=message
        )
        models.db.session.add(notification)
        models.db.session.commit()
        
        # Here you could integrate with actual Teams API
        # For demo, we'll just log it
        print(f"Notification sent to user {recipient_id}: {message}")
        
        return True
    except Exception as e:
        models.db.session.rollback()
        print(f"Error sending notification: {str(e)}")
        return False

def check_late_submissions():
    """Check for vendors who haven't submitted today's status"""
    today = date.today()
    
    # Skip weekends and holidays
    if today.weekday() >= 5:  # Weekend
        return []
    
    if Holiday.query.filter_by(holiday_date=today).first():  # Holiday
        return []
    
    # Get all active vendors
    vendors = Vendor.query.join(User).filter(User.is_active == True).all()
    late_vendors = []
    
    for vendor in vendors:
        # Check if status submitted for today
        status = DailyStatus.query.filter_by(
            vendor_id=vendor.id,
            status_date=today
        ).first()
        
        if not status:
            late_vendors.append(vendor)
    
    return late_vendors

def predict_absence_risk(vendor_id, days_ahead=7):
    """AI-based absence prediction (simplified version for demo)"""
    try:
        # Get historical data for the vendor
        end_date = date.today()
        start_date = end_date - timedelta(days=90)  # Last 3 months
        
        statuses = DailyStatus.query.filter(
            DailyStatus.vendor_id == vendor_id,
            DailyStatus.status_date >= start_date,
            DailyStatus.status_date <= end_date
        ).all()
        
        if len(statuses) < 10:  # Not enough data
            return {'risk_score': 0, 'confidence': 'low', 'factors': []}
        
        # Calculate patterns
        total_days = len(statuses)
        leave_days = len([s for s in statuses if s.status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]])
        wfh_days = len([s for s in statuses if s.status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]])
        
        # Simple risk calculation based on patterns
        leave_rate = leave_days / total_days
        wfh_rate = wfh_days / total_days
        
        # Recent trend (last 2 weeks)
        recent_date = end_date - timedelta(days=14)
        recent_statuses = [s for s in statuses if s.status_date >= recent_date]
        recent_leaves = len([s for s in recent_statuses if s.status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]])
        
        risk_score = 0
        factors = []
        
        if leave_rate > 0.1:  # More than 10% leaves
            risk_score += 30
            factors.append(f"High leave rate: {leave_rate:.1%}")
        
        if wfh_rate > 0.3:  # More than 30% WFH
            risk_score += 20
            factors.append(f"High WFH rate: {wfh_rate:.1%}")
        
        if recent_leaves >= 2:  # 2+ leaves in last 2 weeks
            risk_score += 40
            factors.append(f"Recent frequent leaves: {recent_leaves} in 2 weeks")
        
        # Day of week patterns (if it's Monday, higher risk)
        if (end_date + timedelta(days=days_ahead)).weekday() == 0:  # Monday
            risk_score += 10
            factors.append("Monday pattern risk")
        
        confidence = 'high' if len(statuses) > 50 else 'medium' if len(statuses) > 25 else 'low'
        
        return {
            'risk_score': min(risk_score, 100),
            'confidence': confidence,
            'factors': factors
        }
        
    except Exception as e:
        print(f"Error predicting absence risk: {str(e)}")
        return {'risk_score': 0, 'confidence': 'low', 'factors': []}
