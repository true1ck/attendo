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
    """Import attendance swipe machine data from Excel or CSV file
    Expected columns: Employee Code, Employee Name, Attendance, WeekDay, 
    Shift Code, Login, Logout, Extra Work Hours, Total Working Hours, Department
    """
    try:
        # Read file based on extension
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        records_imported = 0
        records_skipped = 0
        errors = []
        
        # Print column names for debugging
        print(f"Excel columns found: {df.columns.tolist()}")
        
        for idx, row in df.iterrows():
            try:
                # Skip rows with no employee code
                if pd.isna(row.get('Employee Code', None)):
                    continue
                    
                # Map vendor by employee code (e.g., OT1)
                employee_code = str(row['Employee Code']).strip()
                vendor = Vendor.query.filter_by(vendor_id=employee_code).first()
                
                # If vendor doesn't exist, try to create one
                if not vendor:
                    # Check if we have employee name
                    employee_name = str(row.get('Employee Name', 'Unknown')).strip()
                    department = str(row.get('Department', 'Unknown')).strip()
                    
                    # Create user account first
                    user = User.query.filter_by(username=employee_code).first()
                    if not user:
                        user = User(
                            username=employee_code,
                            email=f"{employee_code.lower()}@vendor.com",
                            role=UserRole.VENDOR,
                            is_active=True
                        )
                        user.set_password('vendor123')  # Default password
                        models.db.session.add(user)
                        models.db.session.flush()
                    
                    # Create vendor profile
                    vendor = Vendor(
                        user_id=user.id,
                        vendor_id=employee_code,
                        full_name=employee_name,
                        department=department,
                        company='Vendor Company',  # Default company
                        band='B2',  # Default band
                        location='BL-A-5F'  # Default location
                    )
                    models.db.session.add(vendor)
                    models.db.session.flush()
                    print(f"Created new vendor: {employee_code} - {employee_name}")
                
                # Parse date from Attendance column (format: DD/MM/YYYY)
                attendance_str = str(row['Attendance'])
                # Handle both DD/MM/YYYY and MM/DD/YYYY formats
                try:
                    attendance_date = pd.to_datetime(attendance_str, format='%d/%m/%Y').date()
                except:
                    try:
                        attendance_date = pd.to_datetime(attendance_str, format='%m/%d/%Y').date()
                    except:
                        attendance_date = pd.to_datetime(attendance_str).date()
                
                # Check if record already exists
                existing_record = SwipeRecord.query.filter_by(
                    vendor_id=vendor.id,
                    attendance_date=attendance_date
                ).first()
                
                if existing_record:
                    records_skipped += 1
                    continue
                
                # Parse times (handle time format HH:MM)
                login_time = None
                logout_time = None
                total_hours = 0
                extra_hours = 0
                
                # Parse Login time
                if pd.notna(row.get('Login')) and str(row['Login']).strip() not in ['-', '']:
                    try:
                        login_str = str(row['Login']).strip()
                        # Handle time format like "10:32" or "10.32"
                        login_str = login_str.replace('.', ':')
                        if ':' in login_str:
                            login_time = pd.to_datetime(login_str, format='%H:%M').time()
                        else:
                            login_time = pd.to_datetime(login_str).time()
                    except:
                        pass
                
                # Parse Logout time
                if pd.notna(row.get('Logout')) and str(row['Logout']).strip() not in ['-', '']:
                    try:
                        logout_str = str(row['Logout']).strip()
                        # Handle time format like "17:25" or "17.25"
                        logout_str = logout_str.replace('.', ':')
                        if ':' in logout_str:
                            logout_time = pd.to_datetime(logout_str, format='%H:%M').time()
                        else:
                            logout_time = pd.to_datetime(logout_str).time()
                    except:
                        pass
                
                # Parse Total Working Hours (format: HH:MM or decimal)
                if pd.notna(row.get('Total Working Hours')) and str(row['Total Working Hours']).strip() not in ['-', '']:
                    try:
                        hours_str = str(row['Total Working Hours']).strip()
                        if ':' in hours_str:
                            # Format like "07:21"
                            time_parts = hours_str.split(':')
                            total_hours = float(time_parts[0]) + float(time_parts[1]) / 60
                        elif '.' in hours_str:
                            # Format like "7.35" (decimal hours)
                            total_hours = float(hours_str)
                        else:
                            total_hours = float(hours_str)
                    except:
                        total_hours = 0
                
                # Parse Extra Work Hours if available
                if pd.notna(row.get('Extra Work Hours')) and str(row['Extra Work Hours']).strip() not in ['-', '']:
                    try:
                        extra_str = str(row['Extra Work Hours']).strip()
                        if ':' in extra_str:
                            time_parts = extra_str.split(':')
                            extra_hours = float(time_parts[0]) + float(time_parts[1]) / 60
                        else:
                            extra_hours = float(extra_str)
                    except:
                        extra_hours = 0
                
                # Determine attendance status from Shift Code
                shift_code = str(row.get('Shift Code', 'AA')).strip().upper()
                attendance_status = 'AP' if shift_code == 'G' else 'AA'  # G = Present, else Absent
                
                # Get weekday
                weekday = str(row.get('WeekDay', '')).strip()
                
                # Create swipe record
                swipe_record = SwipeRecord(
                    vendor_id=vendor.id,
                    attendance_date=attendance_date,
                    weekday=weekday,
                    shift_code=shift_code,
                    login_time=login_time,
                    logout_time=logout_time,
                    total_hours=total_hours,
                    extra_hours=extra_hours,
                    attendance_status=attendance_status
                )
                
                models.db.session.add(swipe_record)
                records_imported += 1
                
                # Print progress every 100 records
                if records_imported % 100 == 0:
                    print(f"Imported {records_imported} records...")
                
            except Exception as e:
                error_msg = f"Error processing row {idx}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                continue
        
        models.db.session.commit()
        
        # Print summary
        print(f"\n=== Import Summary ===")
        print(f"Total records imported: {records_imported}")
        print(f"Records skipped (already exist): {records_skipped}")
        print(f"Errors encountered: {len(errors)}")
        if errors and len(errors) <= 10:
            print("\nFirst 10 errors:")
            for err in errors[:10]:
                print(f"  - {err}")
        
        return records_imported
        
    except Exception as e:
        models.db.session.rollback()
        print(f"Error importing swipe data: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

def detect_mismatches():
    """Detect mismatches between vendor entries, swipe data and leave/WFH approvals
    Enhanced version with half-day support and detailed mismatch information
    Rules:
    - InOffice (full/half): must have swipe AP on that date; missing swipe => mismatch
    - WFH (full/half): should not have swipe AP; if swipe AP exists => mismatch; if no WFHRecord covering date => mismatch
    - Leave (full/half): must have LeaveRecord covering date; if swipe AP exists => mismatch
    - Missing vendor entry when swipe AP exists => mismatch
    - Half-day combinations are analyzed per AM/PM with specific mismatch details
    Only considers last 60 days and approved statuses
    """
    try:
        vendors = Vendor.query.all()
        mismatches_found = 0
        start_date = date.today() - timedelta(days=60)
        
        for vendor in vendors:
            # Get approved statuses in the window
            statuses = DailyStatus.query.filter(
                DailyStatus.vendor_id == vendor.id,
                DailyStatus.status_date >= start_date,
                DailyStatus.approval_status == ApprovalStatus.APPROVED
            ).all()
            status_by_date = {s.status_date: s for s in statuses}
            
            # Get swipe records in window
            swipes = SwipeRecord.query.filter(
                SwipeRecord.vendor_id == vendor.id,
                SwipeRecord.attendance_date >= start_date
            ).all()
            swipe_by_date = {s.attendance_date: s for s in swipes}
            
            # Get leave and WFH records
            leave_dates = _get_leave_dates(vendor, start_date)
            wfh_dates = _get_wfh_dates(vendor, start_date)
            
            # Process all relevant dates
            all_dates = set(status_by_date.keys()) | set(swipe_by_date.keys()) | leave_dates | wfh_dates
            
            for d in all_dates:
                status = status_by_date.get(d)
                swipe = swipe_by_date.get(d)
                
                # Case: missing vendor entry but swipe AP exists
                if not status and swipe and swipe.attendance_status == 'AP':
                    if not MismatchRecord.query.filter_by(vendor_id=vendor.id, mismatch_date=d).first():
                        mismatch_details = {
                            'full_day_mismatch': {
                                'reason': 'No vendor status submitted but swipe record shows present',
                                'severity': 'high',
                                'swipe_status': 'AP',
                                'web_status': None
                            }
                        }
                        mm = MismatchRecord(
                            vendor_id=vendor.id,
                            mismatch_date=d,
                            web_status=None,
                            swipe_status='AP'
                        )
                        mm.set_mismatch_details(mismatch_details)
                        models.db.session.add(mm)
                        mismatches_found += 1
                    continue
                
                if not status:
                    continue
                
                # Analyze the status for mismatches
                mismatch_info = _analyze_status_for_mismatches(status, swipe, d, leave_dates, wfh_dates)
                
                if mismatch_info['has_mismatch']:
                    if not MismatchRecord.query.filter_by(vendor_id=vendor.id, mismatch_date=d).first():
                        mm = MismatchRecord(
                            vendor_id=vendor.id,
                            mismatch_date=d,
                            web_status=status.status,
                            swipe_status=swipe.attendance_status if swipe else 'AA'
                        )
                        mm.set_mismatch_details(mismatch_info['details'])
                        models.db.session.add(mm)
                        mismatches_found += 1
        
        models.db.session.commit()
        print(f"Detected {mismatches_found} new mismatches with detailed analysis")
        return mismatches_found
        
    except Exception as e:
        models.db.session.rollback()
        print(f"Error detecting mismatches: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

def _get_leave_dates(vendor, start_date):
    """Get set of dates covered by leave records"""
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
    return leave_dates

def _get_wfh_dates(vendor, start_date):
    """Get set of dates covered by WFH records"""
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
    return wfh_dates

def _analyze_status_for_mismatches(status, swipe, date, leave_dates, wfh_dates):
    """Analyze a daily status for mismatches with detailed half-day support"""
    web_status = status.status
    swipe_status = swipe.attendance_status if swipe else 'AA'
    swipe_in_time = swipe.login_time if swipe else None
    swipe_out_time = swipe.logout_time if swipe else None
    
    mismatch_details = {}
    has_mismatch = False
    
    # Define AM/PM time windows (configurable)
    AM_START = datetime.strptime('09:00', '%H:%M').time()
    AM_END = datetime.strptime('13:00', '%H:%M').time()
    PM_START = datetime.strptime('14:00', '%H:%M').time()
    PM_END = datetime.strptime('18:00', '%H:%M').time()
    
    # Analyze based on status type
    if status.is_half_day() and status.has_half_day_details():
        # Half-day with detailed AM/PM information
        has_mismatch, mismatch_details = _analyze_half_day_detailed(
            status, swipe_status, swipe_in_time, swipe_out_time, 
            date, leave_dates, wfh_dates, AM_START, AM_END, PM_START, PM_END
        )
    else:
        # Full day or legacy half-day analysis
        has_mismatch, mismatch_details = _analyze_full_day(
            web_status, swipe_status, swipe_in_time, swipe_out_time,
            date, leave_dates, wfh_dates
        )
    
    return {
        'has_mismatch': has_mismatch,
        'details': mismatch_details
    }

def _analyze_half_day_detailed(status, swipe_status, swipe_in_time, swipe_out_time, 
                             date, leave_dates, wfh_dates, AM_START, AM_END, PM_START, PM_END):
    """Analyze half-day status with AM/PM details"""
    has_mismatch = False
    mismatch_details = {}
    
    am_type = status.half_am_type
    pm_type = status.half_pm_type
    
    # Determine if swipe occurred in AM/PM periods
    am_swipe_present = False
    pm_swipe_present = False
    
    if swipe_in_time and swipe_out_time and swipe_status == 'AP':
        # Check if swipe covers AM period
        if swipe_in_time <= AM_END and swipe_out_time >= AM_START:
            am_swipe_present = True
        # Check if swipe covers PM period  
        if swipe_in_time <= PM_END and swipe_out_time >= PM_START:
            pm_swipe_present = True
    elif swipe_status == 'AP':
        # If we have AP but no detailed times, assume it covers both periods
        am_swipe_present = True
        pm_swipe_present = True
    
    # Analyze AM period
    am_mismatch = _analyze_half_period('AM', am_type, am_swipe_present, date, leave_dates, wfh_dates)
    if am_mismatch:
        has_mismatch = True
        mismatch_details['am_mismatch'] = am_mismatch
    
    # Analyze PM period
    pm_mismatch = _analyze_half_period('PM', pm_type, pm_swipe_present, date, leave_dates, wfh_dates)
    if pm_mismatch:
        has_mismatch = True
        mismatch_details['pm_mismatch'] = pm_mismatch
    
    return has_mismatch, mismatch_details

def _analyze_half_period(period_name, period_type, swipe_present, date, leave_dates, wfh_dates):
    """Analyze a single half-day period (AM or PM)"""
    from models import HalfDayType
    
    if period_type == HalfDayType.IN_OFFICE:
        if not swipe_present:
            return {
                'reason': f'{period_name} marked as in-office but no swipe record found for this period',
                'severity': 'high',
                'expected': 'swipe_present',
                'actual': 'no_swipe'
            }
    elif period_type == HalfDayType.WFH:
        if swipe_present:
            return {
                'reason': f'{period_name} marked as WFH but swipe record shows office presence',
                'severity': 'high',
                'expected': 'no_swipe',
                'actual': 'swipe_present'
            }
        elif date not in wfh_dates:
            return {
                'reason': f'{period_name} marked as WFH but no WFH approval found',
                'severity': 'medium',
                'expected': 'wfh_approval',
                'actual': 'no_approval'
            }
    elif period_type == HalfDayType.LEAVE:
        if swipe_present:
            return {
                'reason': f'{period_name} marked as leave but swipe record shows office presence',
                'severity': 'high',
                'expected': 'no_swipe',
                'actual': 'swipe_present'
            }
        elif date not in leave_dates:
            return {
                'reason': f'{period_name} marked as leave but no leave approval found',
                'severity': 'medium',
                'expected': 'leave_approval',
                'actual': 'no_approval'
            }
    elif period_type == HalfDayType.ABSENT:
        if swipe_present:
            return {
                'reason': f'{period_name} marked as absent but swipe record shows office presence',
                'severity': 'high',
                'expected': 'no_swipe',
                'actual': 'swipe_present'
            }
    
    return None

def _analyze_full_day(web_status, swipe_status, swipe_in_time, swipe_out_time, date, leave_dates, wfh_dates):
    """Analyze full-day or legacy half-day status"""
    has_mismatch = False
    mismatch_details = {}
    
    # In office must have swipe AP
    if web_status in [AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF]:
        if swipe_status != 'AP':
            has_mismatch = True
            mismatch_details['full_day_mismatch'] = {
                'reason': 'In-office status but no swipe present',
                'severity': 'high',
                'expected': 'swipe_AP',
                'actual': swipe_status
            }
    
    # WFH should not have swipe AP and must have WFH approval
    elif web_status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]:
        if swipe_status == 'AP':
            has_mismatch = True
            mismatch_details['full_day_mismatch'] = {
                'reason': 'WFH marked but swipe shows office presence',
                'severity': 'high',
                'expected': 'no_swipe',
                'actual': 'swipe_AP'
            }
        elif date not in wfh_dates:
            has_mismatch = True
            mismatch_details['full_day_mismatch'] = {
                'reason': 'WFH marked but no WFH approval record found',
                'severity': 'medium',
                'expected': 'wfh_approval',
                'actual': 'no_approval'
            }
    
    # Leave should have leave record and no AP swipe
    elif web_status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]:
        if date not in leave_dates:
            has_mismatch = True
            mismatch_details['full_day_mismatch'] = {
                'reason': 'Leave marked but no approved leave record found',
                'severity': 'medium',
                'expected': 'leave_approval',
                'actual': 'no_approval'
            }
        elif swipe_status == 'AP':
            has_mismatch = True
            mismatch_details['full_day_mismatch'] = {
                'reason': 'Leave marked but swipe shows office presence',
                'severity': 'high',
                'expected': 'no_swipe',
                'actual': 'swipe_AP'
            }
    
    return has_mismatch, mismatch_details

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


def generate_ai_insights(manager_id, prediction_window_days=7):
    """Generate AI-like insights and predictions for a manager's team using simple heuristics.
    Returns a tuple: (predictions, ai_stats, risk_distribution)
    - predictions: list of dicts for display in the table
    - ai_stats: summary KPIs used by the cards at the top
    - risk_distribution: counts for Low/Medium/High/Critical used by donut chart
    """
    try:
        from collections import defaultdict
        today = date.today()
        manager = Manager.query.get(manager_id)
        team_vendors = manager.team_vendors.all() if manager and manager.team_vendors else []

        predictions = []
        risk_counts = { 'low': 0, 'medium': 0, 'high': 0, 'critical': 0 }
        absence_pred_count = 0
        wfh_pred_count = 0
        pattern_insights_count = 0

        # Pre-fetch holidays for the prediction window (with small buffer)
        holiday_set = {
            h.holiday_date for h in Holiday.query.filter(
                Holiday.holiday_date >= today,
                Holiday.holiday_date <= today + timedelta(days=prediction_window_days + 14)
            ).all()
        }

        # Helper to get next working date matching a target weekday, within the window
        def next_working_date_for_weekday(start_date, target_weekday, window_days):
            for i in range(1, window_days + 1):
                d = start_date + timedelta(days=i)
                if d.weekday() != target_weekday:
                    continue
                # Only consider Mon-Fri and not a holiday
                if d.weekday() >= 5 or d in holiday_set:
                    continue
                return d
            return None

        for v in team_vendors:
            # Look back 120 days for patterns
            start_lookback = today - timedelta(days=120)
            statuses = DailyStatus.query.filter(
                DailyStatus.vendor_id == v.id,
                DailyStatus.status_date >= start_lookback,
                DailyStatus.status_date <= today
            ).all()

            if not statuses:
                continue

            # Day-of-week pattern tracking
            dow_total = [0] * 7
            dow_leave = [0] * 7
            dow_wfh = [0] * 7
            for s in statuses:
                dow = s.status_date.weekday()
                dow_total[dow] += 1
                if s.status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]:
                    dow_leave[dow] += 1
                elif s.status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]:
                    dow_wfh[dow] += 1

            # Determine strongest pattern (leave vs wfh) and best weekday
            best_type = None
            best_dow = None
            best_rate = 0.0
            for dwi in range(7):
                if dow_total[dwi] == 0:
                    continue
                leave_rate = dow_leave[dwi] / dow_total[dwi]
                wfh_rate = dow_wfh[dwi] / dow_total[dwi]
                if leave_rate >= wfh_rate and leave_rate > best_rate:
                    best_rate = leave_rate
                    best_type = 'leave'
                    best_dow = dwi
                if wfh_rate > leave_rate and wfh_rate > best_rate:
                    best_rate = wfh_rate
                    best_type = 'wfh'
                    best_dow = dwi

            # Base risk from existing heuristic function
            risk_info = predict_absence_risk(v.id, days_ahead=prediction_window_days)
            base_score = risk_info.get('risk_score', 0)
            reasons = list(risk_info.get('factors', []))

            # Add pattern reason if any
            if best_dow is not None and best_rate > 0:
                weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                if best_type == 'leave':
                    reasons.append(f"Historical pattern: higher leave on {weekday_names[best_dow]} ({best_rate*100:.0f}%)")
                else:
                    reasons.append(f"Historical pattern: higher WFH on {weekday_names[best_dow]} ({best_rate*100:.0f}%)")

            # Predicted date (prefer pattern weekday, next working day within window)
            predicted_date = None
            if best_dow is not None:
                predicted_date = next_working_date_for_weekday(today, best_dow, prediction_window_days)
            if not predicted_date:
                # Fallback: first working day within window
                for i in range(1, prediction_window_days + 1):
                    d = today + timedelta(days=i)
                    if d.weekday() < 5 and d not in holiday_set:
                        predicted_date = d
                        break

            # Combine base score with pattern rate to estimate likelihood
            likelihood = int(min(95, max(40, base_score * 0.6 + (best_rate * 100.0) * 0.5)))

            # Risk level
            if likelihood >= 90:
                level = 'Critical'
            elif likelihood >= 75:
                level = 'High'
            elif likelihood >= 60:
                level = 'Medium'
            else:
                level = 'Low'

            # Recommendation
            if level in ['Critical', 'High']:
                recommendation = 'Urgent Intervention' if best_type == 'leave' else 'Schedule Backup'
            elif level == 'Medium':
                recommendation = 'Proactive Check-in'
            else:
                recommendation = 'Schedule Backup'

            # Counters
            if best_type == 'leave':
                absence_pred_count += 1
            elif best_type == 'wfh':
                wfh_pred_count += 1
            risk_counts[level.lower()] += 1
            pattern_insights_count += len(reasons)

            predictions.append({
                'vendor_id': v.vendor_id,
                'vendor_name': v.full_name,
                'predicted_date': predicted_date.isoformat() if predicted_date else None,
                'predicted_date_display': predicted_date.strftime('%b %d, %Y') if predicted_date else '-',
                'likelihood': likelihood,
                'risk_level': level,
                'type': best_type or 'leave',
                'reasons': reasons,
                'recommendation': recommendation,
            })

        # Sort predictions by likelihood descending
        predictions.sort(key=lambda p: p['likelihood'], reverse=True)

        ai_stats = {
            'absence_predictions': absence_pred_count,
            'wfh_predictions': wfh_pred_count,
            'risk_alerts': risk_counts['high'] + risk_counts['critical'],
            'pattern_insights': pattern_insights_count,
            'last_trained': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'predictions_made': len(predictions),
            # Leave accuracy None to allow template fallback display, or set 'N/A'
            'accuracy': None,
        }
        risk_distribution = {
            'low': risk_counts['low'],
            'medium': risk_counts['medium'],
            'high': risk_counts['high'],
            'critical': risk_counts['critical'],
        }
        return predictions, ai_stats, risk_distribution
    except Exception as e:
        print(f"Error generating AI insights: {str(e)}")
        return [], {'absence_predictions': 0, 'wfh_predictions': 0, 'risk_alerts': 0, 'pattern_insights': 0, 'last_trained': datetime.now().strftime('%Y-%m-%d %H:%M'), 'predictions_made': 0, 'accuracy': None}, {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
