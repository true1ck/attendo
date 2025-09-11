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
            
            # Analyze statuses and calculate working hours
            total_work_hours = 0.0
            total_extra_hours = 0.0
            
            for status in statuses:
                if status.status in [AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF]:
                    office_days += 1 if status.status == AttendanceStatus.IN_OFFICE_FULL else 0.5
                elif status.status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]:
                    wfh_days += 1 if status.status == AttendanceStatus.WFH_FULL else 0.5
                    wfh_dates.append(status.status_date.strftime('%Y-%m-%d'))
                elif status.status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]:
                    leave_days += 1 if status.status == AttendanceStatus.LEAVE_FULL else 0.5
                    leave_dates.append(status.status_date.strftime('%Y-%m-%d'))
                
                # Add working hours if available
                if status.total_hours:
                    total_work_hours += status.total_hours
                if status.extra_hours:
                    total_extra_hours += status.extra_hours
            
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
                'Total Working Hours': round(total_work_hours, 2),
                'Total Extra Hours': round(total_extra_hours, 2),
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
    Expected columns based on requirements document:
    S.No, Employee Name, Employee ID, Attendance Date, Weekday, Shift Code, Login, Logout, 
    Extra Work Hours, Total Working Hours, Attendance Status, Floor Unit, Business Unit, Department, Sub-Department
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
                # Skip rows with no employee ID (updated column name)
                employee_id = row.get('Employee ID') or row.get('Employee Code')
                if pd.isna(employee_id):
                    continue
                    
                # Map vendor by employee ID
                employee_id = str(employee_id).strip()
                vendor = Vendor.query.filter_by(vendor_id=employee_id).first()
                
                # If vendor doesn't exist, try to create one
                if not vendor:
                    # Check if we have employee name
                    employee_name = str(row.get('Employee Name', 'Unknown')).strip()
                    # Try different department column names from requirements format
                    department = str(row.get('Department', row.get('Sub-Department', 'Unknown'))).strip()
                    business_unit = str(row.get('Business Unit', 'Unknown')).strip()
                    floor_unit = str(row.get('Floor Unit', 'BL-A-5F')).strip()
                    
                    # Create user account first
                    user = User.query.filter_by(username=employee_id).first()
                    if not user:
                        user = User(
                            username=employee_id,
                            email=f"{employee_id.lower()}@vendor.com",
                            role=UserRole.VENDOR,
                            is_active=True
                        )
                        user.set_password('vendor123')  # Default password
                        models.db.session.add(user)
                        models.db.session.flush()
                    
                    # Create vendor profile
                    vendor = Vendor(
                        user_id=user.id,
                        vendor_id=employee_id,
                        full_name=employee_name,
                        department=f"{business_unit}/{department}" if business_unit != 'Unknown' else department,
                        company='Vendor Company',  # Default company
                        band='B2',  # Default band
                        location=floor_unit  # Use Floor Unit from data
                    )
                    models.db.session.add(vendor)
                    models.db.session.flush()
                    print(f"Created new vendor: {employee_id} - {employee_name}")
                
                # Parse date from Attendance Date column (format: DD/MM/YYYY or YYYY-MM-DD)
                # Try different column names for date
                date_value = row.get('Attendance Date') or row.get('Attendance') or row.get('Date')
                attendance_str = str(date_value)
                
                # Handle multiple date formats
                try:
                    # Try YYYY-MM-DD format first
                    attendance_date = pd.to_datetime(attendance_str, format='%Y-%m-%d').date()
                except:
                    try:
                        # Try DD/MM/YYYY format
                        attendance_date = pd.to_datetime(attendance_str, format='%d/%m/%Y').date()
                    except:
                        try:
                            # Try MM/DD/YYYY format
                            attendance_date = pd.to_datetime(attendance_str, format='%m/%d/%Y').date()
                        except:
                            # Let pandas handle it automatically
                            attendance_date = pd.to_datetime(attendance_str).date()
                
                # Check if record already exists
                existing_record = SwipeRecord.query.filter_by(
                    vendor_id=vendor.id,
                    attendance_date=attendance_date
                ).first()
                
                if existing_record:
                    records_skipped += 1
                    continue
                
                # Parse times and additional fields from requirements format
                login_time = None
                logout_time = None
                total_hours = 0
                extra_hours = 0
                shift_code = str(row.get('Shift Code', 'G')).strip()
                attendance_status = str(row.get('Attendance Status', 'AA')).strip()
                weekday = str(row.get('Weekday', '')).strip()
                
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
                
                # Parse Total Working Hours from requirements format (HH:MM format)
                total_working_hours = row.get('Total Working Hours')
                if pd.notna(total_working_hours) and str(total_working_hours).strip() not in ['-', '']:
                    try:
                        hours_str = str(total_working_hours).strip()
                        if ':' in hours_str:
                            # Format like "06:53" or "07:17"
                            hours, minutes = map(int, hours_str.split(':'))
                            total_hours = hours + (minutes / 60.0)
                        else:
                            total_hours = float(hours_str)
                    except:
                        total_hours = 0
                
                # Parse Extra Work Hours from requirements format
                extra_work_hours = row.get('Extra Work Hours')
                if pd.notna(extra_work_hours) and str(extra_work_hours).strip() not in ['-', '']:
                    try:
                        extra_str = str(extra_work_hours).strip()
                        if ':' in extra_str:
                            # Format like "00:25" or "00:48"
                            hours, minutes = map(int, extra_str.split(':'))
                            extra_hours = hours + (minutes / 60.0)
                        else:
                            extra_hours = float(extra_str)
                    except:
                        extra_hours = 0
                
                # Calculate total hours if login/logout times are available (fallback)
                if total_hours == 0 and login_time and logout_time:
                    # Calculate total hours from login/logout times
                    login_minutes = login_time.hour * 60 + login_time.minute
                    logout_minutes = logout_time.hour * 60 + logout_time.minute
                    total_minutes = logout_minutes - login_minutes
                    if total_minutes < 0:  # Handle overnight shifts
                        total_minutes += 24 * 60
                    total_hours = round(total_minutes / 60.0, 2)
                    
                    # Calculate extra hours based on 8-hour standard day
                    standard_work_hours = 8.0
                    extra_hours = max(0.0, round(total_hours - standard_work_hours, 2))
                else:
                    # Parse Total Working Hours from spreadsheet if no times
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
                    
                    # Parse Extra Work Hours from spreadsheet if available
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
                    else:
                        # Calculate extra hours based on 8-hour standard if not provided
                        standard_work_hours = 8.0
                        extra_hours = max(0.0, round(total_hours - standard_work_hours, 2))
                
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
    """Enhanced mismatch detection with comprehensive scenarios
    
    Detects the following types of mismatches:
    1. Status vs Swipe Mismatches: Office claimed but no swipe, WFH claimed but swipe present
    2. Approval Record Mismatches: Leave/WFH claimed but no approval records
    3. Time Validation Mismatches: Early departure, late arrival inconsistencies
    4. Half-day Specific Mismatches: AM/PM period conflicts between status and swipe
    5. Missing Submission Mismatches: Swipe present but no status submitted
    6. Overtime Mismatches: Extra hours claimed but not reflected in swipe data
    7. Weekend/Holiday Mismatches: Status submitted on non-working days
    
    Only processes last 60 days and approved statuses to focus on relevant data.
    Limited to 1-2 mismatches per category to avoid overwhelming the system.
    """
    try:
        vendors = Vendor.query.all()
        mismatches_found = 0
        start_date = date.today() - timedelta(days=60)
        
        # Counters for each mismatch category to limit to 1-2 per type
        category_counts = {
            'missing_submission': 0,
            'status_swipe_mismatch': 0, 
            'approval_missing': 0,
            'time_validation': 0,
            'half_day_conflict': 0,
            'overtime_mismatch': 0,
            'weekend_holiday': 0
        }
        max_per_category = 2  # Limit to 2 mismatches per category
        
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
            
            # Get holidays for weekend/holiday validation
            holidays = Holiday.query.filter(
                Holiday.holiday_date >= start_date,
                Holiday.holiday_date <= date.today()
            ).all()
            holiday_dates = {h.holiday_date for h in holidays}
            
            # Process all relevant dates
            all_dates = set(status_by_date.keys()) | set(swipe_by_date.keys()) | leave_dates | wfh_dates
            
            for d in all_dates:
                status = status_by_date.get(d)
                swipe = swipe_by_date.get(d)
                
                # Skip if we've reached max mismatches for all categories
                if all(count >= max_per_category for count in category_counts.values()):
                    break
                
                # Skip if this date already has a mismatch record
                if MismatchRecord.query.filter_by(vendor_id=vendor.id, mismatch_date=d).first():
                    continue
                
                # Category 1: Missing submission mismatches
                if (not status and swipe and swipe.attendance_status == 'AP' and 
                    category_counts['missing_submission'] < max_per_category):
                    mismatch_details = {
                        'category': 'missing_submission',
                        'full_day_mismatch': {
                            'reason': 'No vendor status submitted but swipe record shows present',
                            'severity': 'high',
                            'swipe_status': 'AP',
                            'web_status': None,
                            'recommendation': 'Submit daily status for this date'
                        }
                    }
                    _create_mismatch_record(vendor.id, d, None, 'AP', mismatch_details)
                    category_counts['missing_submission'] += 1
                    mismatches_found += 1
                    continue
                
                if not status:
                    continue
                
                # Category 2: Weekend/Holiday mismatches
                if (d.weekday() >= 5 or d in holiday_dates) and category_counts['weekend_holiday'] < max_per_category:
                    if status.status not in [AttendanceStatus.ABSENT, AttendanceStatus.LEAVE_FULL]:
                        mismatch_details = {
                            'category': 'weekend_holiday',
                            'full_day_mismatch': {
                                'reason': f'Status submitted on {"weekend" if d.weekday() >= 5 else "holiday"} - {d.strftime("%A")}',
                                'severity': 'medium',
                                'web_status': status.status.value,
                                'swipe_status': swipe.attendance_status if swipe else 'N/A',
                                'recommendation': 'Review if work was actually performed on non-working day'
                            }
                        }
                        _create_mismatch_record(vendor.id, d, status.status, swipe.attendance_status if swipe else 'AA', mismatch_details)
                        category_counts['weekend_holiday'] += 1
                        mismatches_found += 1
                        continue
                
                # Category 3: Overtime mismatches
                if (swipe and swipe.extra_hours > 0 and status.total_hours and 
                    abs(swipe.extra_hours - (status.total_hours - 8)) > 0.5 and
                    category_counts['overtime_mismatch'] < max_per_category):
                    mismatch_details = {
                        'category': 'overtime_mismatch',
                        'full_day_mismatch': {
                            'reason': f'Overtime hours mismatch: Swipe shows {swipe.extra_hours:.2f}h extra, Status implies {max(0, status.total_hours - 8):.2f}h',
                            'severity': 'medium',
                            'web_hours': status.total_hours,
                            'swipe_extra': swipe.extra_hours,
                            'recommendation': 'Verify actual overtime hours worked'
                        }
                    }
                    _create_mismatch_record(vendor.id, d, status.status, swipe.attendance_status, mismatch_details)
                    category_counts['overtime_mismatch'] += 1
                    mismatches_found += 1
                    continue
                
                # Category 4: Time validation mismatches
                if (swipe and swipe.attendance_status == 'AP' and swipe.login_time and swipe.logout_time and
                    category_counts['time_validation'] < max_per_category):
                    # Check for very early departure (before 3 PM)
                    if swipe.logout_time < datetime.strptime('15:00', '%H:%M').time():
                        mismatch_details = {
                            'category': 'time_validation',
                            'full_day_mismatch': {
                                'reason': f'Early departure: Logout at {swipe.logout_time.strftime("%H:%M")} (before 3 PM)',
                                'severity': 'medium',
                                'login_time': swipe.login_time.strftime('%H:%M'),
                                'logout_time': swipe.logout_time.strftime('%H:%M'),
                                'total_hours': swipe.total_hours,
                                'recommendation': 'Verify if this was planned early departure or half-day'
                            }
                        }
                        _create_mismatch_record(vendor.id, d, status.status, swipe.attendance_status, mismatch_details)
                        category_counts['time_validation'] += 1
                        mismatches_found += 1
                        continue
                    
                    # Check for very late arrival (after 11 AM)
                    elif swipe.login_time > datetime.strptime('11:00', '%H:%M').time():
                        mismatch_details = {
                            'category': 'time_validation',
                            'full_day_mismatch': {
                                'reason': f'Late arrival: Login at {swipe.login_time.strftime("%H:%M")} (after 11 AM)',
                                'severity': 'low',
                                'login_time': swipe.login_time.strftime('%H:%M'),
                                'logout_time': swipe.logout_time.strftime('%H:%M') if swipe.logout_time else 'N/A',
                                'total_hours': swipe.total_hours,
                                'recommendation': 'Verify if late arrival was approved'
                            }
                        }
                        _create_mismatch_record(vendor.id, d, status.status, swipe.attendance_status, mismatch_details)
                        category_counts['time_validation'] += 1
                        mismatches_found += 1
                        continue
                
                # Analyze the status for traditional mismatches
                mismatch_info = _analyze_status_for_mismatches(status, swipe, d, leave_dates, wfh_dates, category_counts, max_per_category)
                
                if mismatch_info['has_mismatch']:
                    mm = MismatchRecord(
                        vendor_id=vendor.id,
                        mismatch_date=d,
                        web_status=status.status,
                        swipe_status=swipe.attendance_status if swipe else 'AA'
                    )
                    mm.set_mismatch_details(mismatch_info['details'])
                    models.db.session.add(mm)
                    
                    # Update category counts
                    category = mismatch_info['details'].get('category', 'status_swipe_mismatch')
                    if category in category_counts:
                        category_counts[category] += 1
                    mismatches_found += 1
        
        models.db.session.commit()
        
        # Print summary by category
        print(f"\n=== Enhanced Mismatch Detection Results ===")
        print(f"Total mismatches detected: {mismatches_found}")
        print("\nBy category:")
        for category, count in category_counts.items():
            if count > 0:
                print(f"  {category.replace('_', ' ').title()}: {count}")
        
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

def _create_mismatch_record(vendor_id, mismatch_date, web_status, swipe_status, mismatch_details):
    """Create a mismatch record with the provided details"""
    mm = MismatchRecord(
        vendor_id=vendor_id,
        mismatch_date=mismatch_date,
        web_status=web_status,
        swipe_status=swipe_status
    )
    mm.set_mismatch_details(mismatch_details)
    models.db.session.add(mm)

def _analyze_status_for_mismatches(status, swipe, date, leave_dates, wfh_dates, category_counts=None, max_per_category=2):
    """Analyze a daily status for mismatches with detailed half-day support and category management"""
    web_status = status.status
    swipe_status = swipe.attendance_status if swipe else 'AA'
    swipe_in_time = swipe.login_time if swipe else None
    swipe_out_time = swipe.logout_time if swipe else None
    
    mismatch_details = {}
    has_mismatch = False
    
    # Initialize category_counts if not provided
    if category_counts is None:
        category_counts = {}
    
    # Define AM/PM time windows (configurable)
    AM_START = datetime.strptime('09:00', '%H:%M').time()
    AM_END = datetime.strptime('13:00', '%H:%M').time()
    PM_START = datetime.strptime('14:00', '%H:%M').time()
    PM_END = datetime.strptime('18:00', '%H:%M').time()
    
    # Analyze based on status type
    if status.is_half_day() and status.has_half_day_details():
        # Half-day with detailed AM/PM information
        if category_counts.get('half_day_conflict', 0) < max_per_category:
            has_mismatch, mismatch_details = _analyze_half_day_detailed(
                status, swipe_status, swipe_in_time, swipe_out_time, 
                date, leave_dates, wfh_dates, AM_START, AM_END, PM_START, PM_END
            )
            if has_mismatch:
                mismatch_details['category'] = 'half_day_conflict'
    else:
        # Full day or legacy half-day analysis
        # Check which category this would fall under
        category = None
        if web_status in [AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF]:
            if swipe_status != 'AP':
                category = 'status_swipe_mismatch'
        elif web_status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]:
            if swipe_status == 'AP' or date not in wfh_dates:
                category = 'status_swipe_mismatch' if swipe_status == 'AP' else 'approval_missing'
        elif web_status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]:
            if date not in leave_dates or swipe_status == 'AP':
                category = 'approval_missing' if date not in leave_dates else 'status_swipe_mismatch'
        
        # Only analyze if we haven't reached the limit for this category
        if category and category_counts.get(category, 0) < max_per_category:
            has_mismatch, mismatch_details = _analyze_full_day(
                web_status, swipe_status, swipe_in_time, swipe_out_time,
                date, leave_dates, wfh_dates, status
            )
            if has_mismatch:
                mismatch_details['category'] = category
    
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
    am_mismatch = _analyze_half_period('AM', am_type, am_swipe_present, date, leave_dates, wfh_dates, status)
    if am_mismatch:
        has_mismatch = True
        mismatch_details['am_mismatch'] = am_mismatch
    
    # Analyze PM period
    pm_mismatch = _analyze_half_period('PM', pm_type, pm_swipe_present, date, leave_dates, wfh_dates, status)
    if pm_mismatch:
        has_mismatch = True
        mismatch_details['pm_mismatch'] = pm_mismatch
    
    return has_mismatch, mismatch_details

def _analyze_half_period(period_name, period_type, swipe_present, date, leave_dates, wfh_dates, daily_status=None):
    """Analyze a single half-day period (AM or PM)
    
    Key Logic Fix: If manager has APPROVED the daily status, don't raise mismatch
    for missing WFH/Leave approval records.
    """
    from models import HalfDayType, ApprovalStatus
    
    # Check if the daily status was approved by manager
    is_manager_approved = daily_status and daily_status.approval_status == ApprovalStatus.APPROVED
    
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
        elif date not in wfh_dates and not is_manager_approved:
            # Only flag if BOTH no WFH approval AND manager hasn't approved
            return {
                'reason': f'{period_name} marked as WFH but no WFH approval found and manager has not approved the status',
                'severity': 'medium',
                'expected': 'wfh_approval_or_manager_approval',
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
        elif date not in leave_dates and not is_manager_approved:
            # Only flag if BOTH no leave approval AND manager hasn't approved
            return {
                'reason': f'{period_name} marked as leave but no leave approval found and manager has not approved the status',
                'severity': 'medium',
                'expected': 'leave_approval_or_manager_approval',
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

def _analyze_full_day(web_status, swipe_status, swipe_in_time, swipe_out_time, date, leave_dates, wfh_dates, daily_status=None):
    """Analyze full-day or legacy half-day status with enhanced recommendations
    
    Key Logic Fix: If manager has APPROVED a WFH/Leave status, don't raise mismatch 
    for missing approval records - manager approval of the daily status is sufficient.
    """
    has_mismatch = False
    mismatch_details = {}
    
    # Check if the daily status was approved by manager
    is_manager_approved = daily_status and daily_status.approval_status == ApprovalStatus.APPROVED
    
    # In office must have swipe AP
    if web_status in [AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF]:
        if swipe_status != 'AP':
            has_mismatch = True
            mismatch_details['full_day_mismatch'] = {
                'reason': 'In-office status submitted but no swipe record shows office presence',
                'severity': 'high',
                'expected': 'swipe_AP',
                'actual': swipe_status,
                'web_status': web_status.value,
                'swipe_status': swipe_status,
                'recommendation': 'Verify if vendor was actually in office or update status to WFH/Leave'
            }
    
    # WFH should not have swipe AP and must have WFH approval OR manager approval
    elif web_status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]:
        if swipe_status == 'AP':
            has_mismatch = True
            mismatch_details['full_day_mismatch'] = {
                'reason': 'WFH status submitted but swipe record shows office presence',
                'severity': 'high',
                'expected': 'no_swipe',
                'actual': 'swipe_AP',
                'web_status': web_status.value,
                'swipe_status': swipe_status,
                'recommendation': 'Update status to In-Office or verify if swipe was accidental'
            }
        elif date not in wfh_dates and not is_manager_approved:
            # Only flag as mismatch if BOTH conditions are true:
            # 1. No WFH approval record AND
            # 2. Manager hasn't approved the daily status
            has_mismatch = True
            mismatch_details['full_day_mismatch'] = {
                'reason': 'WFH status submitted but no WFH approval record found and manager has not approved the status',
                'severity': 'medium',
                'expected': 'wfh_approval_or_manager_approval',
                'actual': 'no_approval',
                'web_status': web_status.value,
                'swipe_status': swipe_status,
                'recommendation': 'Either submit WFH approval request or get manager approval for the daily status'
            }
    
    # Leave should have leave record and no AP swipe OR manager approval
    elif web_status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]:
        if date not in leave_dates and not is_manager_approved:
            # Only flag as mismatch if BOTH conditions are true:
            # 1. No leave approval record AND  
            # 2. Manager hasn't approved the daily status
            has_mismatch = True
            mismatch_details['full_day_mismatch'] = {
                'reason': 'Leave status submitted but no approved leave record found and manager has not approved the status',
                'severity': 'medium',
                'expected': 'leave_approval_or_manager_approval',
                'actual': 'no_approval',
                'web_status': web_status.value,
                'swipe_status': swipe_status,
                'recommendation': 'Either submit leave application or get manager approval for the daily status'
            }
        elif swipe_status == 'AP':
            has_mismatch = True
            mismatch_details['full_day_mismatch'] = {
                'reason': 'Leave status submitted but swipe record shows office presence',
                'severity': 'high',
                'expected': 'no_swipe',
                'actual': 'swipe_AP',
                'web_status': web_status.value,
                'swipe_status': swipe_status,
                'recommendation': 'Update status to In-Office or verify if leave was cancelled'
            }
    
    return has_mismatch, mismatch_details

def import_leave_data(file_path):
    """Import leave data from Excel or CSV file
    Expected columns based on requirements document:
    OT ID, Personnel number, Start Date, End Date, Attendance or Absence Type, 
    Start Time, End time, Hrs, Record is for Full Day, Day, Cal day, Payroll hrs
    """
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        records_imported = 0
        records_skipped = 0
        
        print(f"Leave data columns found: {df.columns.tolist()}")
        
        for idx, row in df.iterrows():
            try:
                # Find vendor by OT ID (Employee ID)
                ot_id = str(row.get('OT ID', '')).strip()
                if not ot_id:
                    continue
                    
                vendor = Vendor.query.filter_by(vendor_id=ot_id).first()
                if not vendor:
                    print(f"Vendor not found for OT ID: {ot_id}")
                    continue
                
                start_date = pd.to_datetime(row['Start Date']).date()
                end_date = pd.to_datetime(row['End Date']).date()
                leave_type = str(row['Attendance or Absence Type']).strip()
                
                # Use 'Day' column for total days (this is the actual leave days)
                total_days = float(row.get('Day', 1.0))
                
                # Additional fields from requirements format
                hrs = float(row.get('Hrs', 0.0)) if pd.notna(row.get('Hrs')) else 0.0
                is_full_day = str(row.get('Record is for Full Day', 'Yes')).strip().lower() == 'yes'
                
                # Check if record already exists
                existing_record = LeaveRecord.query.filter_by(
                    vendor_id=vendor.id,
                    start_date=start_date,
                    end_date=end_date,
                    leave_type=leave_type
                ).first()
                
                if existing_record:
                    records_skipped += 1
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
                
                if records_imported % 50 == 0:
                    print(f"Imported {records_imported} leave records...")
                
            except Exception as e:
                print(f"Error processing leave row {idx}: {str(e)}")
                continue
        
        models.db.session.commit()
        
        print(f"\n=== Leave Import Summary ===")
        print(f"Records imported: {records_imported}")
        print(f"Records skipped (duplicates): {records_skipped}")
        
        return records_imported
        
    except Exception as e:
        models.db.session.rollback()
        print(f"Error importing leave data: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

def import_wfh_data(file_path):
    """Import Work From Home data from Excel or CSV file
    Expected columns based on requirements document:
    RD Name, Department, RD Category, Start Date, End Date, Duration
    """
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        records_imported = 0
        records_skipped = 0
        records_not_found = 0
        
        print(f"WFH data columns found: {df.columns.tolist()}")
        
        for idx, row in df.iterrows():
            try:
                rd_name = str(row.get('RD Name', '')).strip()
                department = str(row.get('Department', '')).strip()
                rd_category = str(row.get('RD Category', '')).strip()
                
                if not rd_name:
                    continue
                
                # Try to find vendor by RD Name (full name) first
                vendor = Vendor.query.filter_by(full_name=rd_name).first()
                
                # If not found by name, try by department match
                if not vendor and department:
                    vendor = Vendor.query.filter(
                        Vendor.department.like(f'%{department}%')
                    ).first()
                
                # If still not found, try to find by partial name match
                if not vendor:
                    vendor = Vendor.query.filter(
                        Vendor.full_name.like(f'%{rd_name}%')
                    ).first()
                
                if not vendor:
                    print(f"Vendor not found for RD Name: '{rd_name}' in Department: '{department}'")
                    records_not_found += 1
                    continue
                
                start_date = pd.to_datetime(row['Start Date']).date()
                end_date = pd.to_datetime(row['End Date']).date()
                duration = int(row.get('Duration', 1))
                
                # Check if record already exists
                existing_record = WFHRecord.query.filter_by(
                    vendor_id=vendor.id,
                    start_date=start_date,
                    end_date=end_date
                ).first()
                
                if existing_record:
                    records_skipped += 1
                    continue
                
                wfh_record = WFHRecord(
                    vendor_id=vendor.id,
                    start_date=start_date,
                    end_date=end_date,
                    duration_days=duration
                )
                
                models.db.session.add(wfh_record)
                records_imported += 1
                
                if records_imported % 50 == 0:
                    print(f"Imported {records_imported} WFH records...")
                
            except Exception as e:
                print(f"Error processing WFH row {idx}: {str(e)}")
                continue
        
        models.db.session.commit()
        
        print(f"\n=== WFH Import Summary ===")
        print(f"Records imported: {records_imported}")
        print(f"Records skipped (duplicates): {records_skipped}")
        print(f"Records not found (no matching vendor): {records_not_found}")
        
        return records_imported
        
    except Exception as e:
        models.db.session.rollback()
        print(f"Error importing WFH data: {str(e)}")
        import traceback
        traceback.print_exc()
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
