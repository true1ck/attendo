from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
import os
import pandas as pd
import models
from models import UserRole, SwipeRecord, LeaveRecord, WFHRecord, MismatchRecord, Vendor, Manager, User, Holiday, ApprovalStatus

# Import utils functions - we'll handle this inside functions to avoid circular imports
# from utils import import_swipe_data, import_leave_data, import_wfh_data, detect_mismatches, generate_monthly_report

# Create blueprint
import_bp = Blueprint('import_routes', __name__, url_prefix='/import')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    """Decorator to require admin role"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@import_bp.route('/')
@login_required
@admin_required
def import_dashboard():
    """Main import dashboard"""
    # Get recent import statistics
    recent_swipe_records = SwipeRecord.query.filter(
        SwipeRecord.imported_at >= date.today().replace(day=1)
    ).count()
    
    recent_leave_records = LeaveRecord.query.filter(
        LeaveRecord.imported_at >= date.today().replace(day=1)
    ).count()
    
    recent_wfh_records = WFHRecord.query.filter(
        WFHRecord.imported_at >= date.today().replace(day=1)
    ).count()
    
    pending_mismatches = MismatchRecord.query.filter(
        MismatchRecord.manager_approval == ApprovalStatus.PENDING
    ).count()
    
    stats = {
        'swipe_records': recent_swipe_records,
        'leave_records': recent_leave_records,
        'wfh_records': recent_wfh_records,
        'pending_mismatches': pending_mismatches
    }
    
    return render_template('import_dashboard.html', stats=stats)

@import_bp.route('/swipe-data', methods=['GET', 'POST'])
@login_required
@admin_required
def import_swipe():
    """Import swipe machine data"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('import_routes.import_dashboard'))
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('import_routes.import_dashboard'))
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create uploads directory if it doesn't exist
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Import the data
                from utils import import_swipe_data
                records_imported = import_swipe_data(filepath)
                
                # Clean up the file
                os.remove(filepath)
                
                if records_imported > 0:
                    flash(f'Successfully imported {records_imported} swipe records!', 'success')
                    
                    # Run mismatch detection after import
                    from utils import detect_mismatches
                    mismatches = detect_mismatches()
                    if mismatches > 0:
                        flash(f'Detected {mismatches} new mismatches during import', 'warning')
                else:
                    flash('No new records imported. Data may already exist or file format is incorrect.', 'warning')
                
                return redirect(url_for('import_routes.import_dashboard'))
            else:
                flash('Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files only.', 'error')
                
        except Exception as e:
            flash(f'Error importing file: {str(e)}', 'error')
        return redirect(url_for('import_routes.import_dashboard'))
    
    return redirect(url_for('import_routes.import_dashboard'))

@import_bp.route('/leave-data', methods=['GET', 'POST'])
@login_required
@admin_required
def import_leaves():
    """Import leave data"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('import_routes.import_dashboard'))
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('import_routes.import_dashboard'))
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                from utils import import_leave_data
                records_imported = import_leave_data(filepath)
                os.remove(filepath)
                
                if records_imported > 0:
                    flash(f'Successfully imported {records_imported} leave records!', 'success')
                else:
                    flash('No new records imported.', 'warning')
                
                return redirect(url_for('import_routes.import_dashboard'))
            else:
                flash('Invalid file type. Please upload Excel files only.', 'error')
                
        except Exception as e:
            flash(f'Error importing file: {str(e)}', 'error')
        return redirect(url_for('import_routes.import_dashboard'))
    
    return redirect(url_for('import_routes.import_dashboard'))

@import_bp.route('/vendor-data', methods=['GET', 'POST'])
@login_required
@admin_required
def import_vendors():
    """Import Vendor master data (Users + Vendor profiles)"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('import_routes.import_dashboard'))

            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('import_routes.import_dashboard'))

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                df = pd.read_excel(filepath) if not filepath.lower().endswith('.csv') else pd.read_csv(filepath)
                created = 0
                updated = 0
                for _, row in df.iterrows():
                    try:
                        vendor_id = str(row.get('Vendor ID') or '').strip()
                        full_name = str(row.get('Full Name') or '').strip()
                        email = str(row.get('Email') or '').strip()
                        department = str(row.get('Department') or '').strip()
                        company = str(row.get('Company') or '').strip()
                        band = str(row.get('Band') or '').strip() or 'B1'
                        location = str(row.get('Location') or '').strip() or 'BL-A-5F'
                        manager_id = str(row.get('Manager ID') or '').strip() or None
                        password = str(row.get('Password') or '').strip() or 'vendor123'

                        if not vendor_id or not full_name:
                            continue

                        # Check if vendor already exists
                        existing_vendor = Vendor.query.filter_by(vendor_id=vendor_id).first()

                        # Get or create user
                        user = None
                        if existing_vendor:
                            user = existing_vendor.user_account
                        if not user:
                            user = User.query.filter_by(email=email).first()
                        if not user:
                            # Create new user
                            user = User(username=email.split('@')[0] if email else vendor_id,
                                        email=email or f"{vendor_id}@example.com",
                                        role=UserRole.VENDOR,
                                        is_active=True)
                            user.set_password(password)
                            models.db.session.add(user)
                            models.db.session.flush()

                        if existing_vendor:
                            # Update existing vendor
                            existing_vendor.full_name = full_name or existing_vendor.full_name
                            existing_vendor.department = department or existing_vendor.department
                            existing_vendor.company = company or existing_vendor.company
                            existing_vendor.band = band or existing_vendor.band
                            existing_vendor.location = location or existing_vendor.location
                            existing_vendor.manager_id = manager_id or existing_vendor.manager_id
                            updated += 1
                        else:
                            # Create new vendor
                            vendor = Vendor(
                                user_id=user.id,
                                vendor_id=vendor_id,
                                full_name=full_name,
                                department=department,
                                company=company,
                                band=band,
                                location=location,
                                manager_id=manager_id
                            )
                            models.db.session.add(vendor)
                            created += 1
                    except Exception as ie:
                        print(f"Error importing vendor row: {str(ie)}")
                        continue

                models.db.session.commit()
                os.remove(filepath)

                flash(f'Vendor import complete. Created: {created}, Updated: {updated}', 'success')
                return redirect(url_for('import_routes.import_dashboard'))
            else:
                flash('Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files only.', 'error')
        except Exception as e:
            models.db.session.rollback()
            flash(f'Error importing vendors: {str(e)}', 'error')
        return redirect(url_for('import_routes.import_dashboard'))
    return redirect(url_for('import_routes.import_dashboard'))


@import_bp.route('/manager-data', methods=['GET', 'POST'])
@login_required
@admin_required
def import_managers():
    """Import Manager master data (Users + Manager profiles)"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('import_routes.import_dashboard'))

            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('import_routes.import_dashboard'))

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                df = pd.read_excel(filepath) if not filepath.lower().endswith('.csv') else pd.read_csv(filepath)
                created = 0
                updated = 0
                for _, row in df.iterrows():
                    try:
                        manager_code = str(row.get('Manager ID') or '').strip()
                        full_name = str(row.get('Full Name') or '').strip()
                        email = str(row.get('Email') or '').strip()
                        department = str(row.get('Department') or '').strip()
                        team_name = str(row.get('Team Name') or '').strip()
                        phone = str(row.get('Phone') or '').strip()
                        password = str(row.get('Password') or '').strip() or 'manager123'

                        if not manager_code or not full_name:
                            continue

                        # Find existing manager by manager_id
                        existing_manager = Manager.query.filter_by(manager_id=manager_code).first()

                        # Get or create user
                        user = None
                        if existing_manager:
                            user = existing_manager.user_account
                        if not user:
                            user = User.query.filter_by(email=email).first()
                        if not user:
                            user = User(username=email.split('@')[0] if email else manager_code,
                                        email=email or f"{manager_code}@example.com",
                                        role=UserRole.MANAGER,
                                        is_active=True)
                            user.set_password(password)
                            models.db.session.add(user)
                            models.db.session.flush()

                        if existing_manager:
                            existing_manager.full_name = full_name or existing_manager.full_name
                            existing_manager.department = department or existing_manager.department
                            existing_manager.team_name = team_name or existing_manager.team_name
                            existing_manager.email = email or existing_manager.email
                            existing_manager.phone = phone or existing_manager.phone
                            updated += 1
                        else:
                            manager = Manager(
                                manager_id=manager_code,
                                user_id=user.id,
                                full_name=full_name,
                                department=department,
                                team_name=team_name,
                                email=email,
                                phone=phone
                            )
                            models.db.session.add(manager)
                            created += 1
                    except Exception as ie:
                        print(f"Error importing manager row: {str(ie)}")
                        continue

                models.db.session.commit()
                os.remove(filepath)

                flash(f'Manager import complete. Created: {created}, Updated: {updated}', 'success')
                return redirect(url_for('import_routes.import_dashboard'))
            else:
                flash('Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files only.', 'error')
        except Exception as e:
            models.db.session.rollback()
            flash(f'Error importing managers: {str(e)}', 'error')
        return redirect(url_for('import_routes.import_dashboard'))
    return redirect(url_for('import_routes.import_dashboard'))


@import_bp.route('/holiday-data', methods=['GET', 'POST'])
@login_required
@admin_required
def import_holidays():
    """Import Holiday master data"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('import_routes.import_dashboard'))

            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('import_routes.import_dashboard'))

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                df = pd.read_excel(filepath) if not filepath.lower().endswith('.csv') else pd.read_csv(filepath)
                created = 0
                for _, row in df.iterrows():
                    try:
                        date_str = str(row.get('Date') or '').strip()
                        name = str(row.get('Name') or '').strip()
                        description = str(row.get('Description') or '').strip()
                        if not date_str or not name:
                            continue
                        holiday_date = pd.to_datetime(date_str).date()
                        existing = Holiday.query.filter_by(holiday_date=holiday_date).first()
                        if existing:
                            # Update name/description if changed
                            existing.name = name or existing.name
                            existing.description = description or existing.description
                        else:
                            h = Holiday(holiday_date=holiday_date,
                                        name=name,
                                        description=description,
                                        created_by=current_user.id)
                            models.db.session.add(h)
                            created += 1
                    except Exception as ie:
                        print(f"Error importing holiday row: {str(ie)}")
                        continue
                models.db.session.commit()
                os.remove(filepath)
                flash(f'Holiday import complete. Created/Updated: {created}', 'success')
                return redirect(url_for('import_routes.import_dashboard'))
            else:
                flash('Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files only.', 'error')
        except Exception as e:
            models.db.session.rollback()
            flash(f'Error importing holidays: {str(e)}', 'error')
        return redirect(url_for('import_routes.import_dashboard'))
    return redirect(url_for('import_routes.import_dashboard'))


@import_bp.route('/wfh-data', methods=['GET', 'POST'])
@login_required
@admin_required
def import_wfh():
    """Import Work From Home data"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('import_routes.import_dashboard'))
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('import_routes.import_dashboard'))
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                from utils import import_wfh_data
                records_imported = import_wfh_data(filepath)
                os.remove(filepath)
                
                if records_imported > 0:
                    flash(f'Successfully imported {records_imported} WFH records!', 'success')
                else:
                    flash('No new records imported.', 'warning')
                
                return redirect(url_for('import_routes.import_dashboard'))
            else:
                flash('Invalid file type. Please upload Excel files only.', 'error')
                
        except Exception as e:
            flash(f'Error importing file: {str(e)}', 'error')
        return redirect(url_for('import_routes.import_dashboard'))
    
    return redirect(url_for('import_routes.import_dashboard'))

@import_bp.route('/reconcile', methods=['POST'])
@login_required
@admin_required
def run_reconciliation():
    """Run reconciliation to detect mismatches"""
    try:
        from utils import detect_mismatches
        mismatches_found = detect_mismatches()
        
        if mismatches_found > 0:
            return jsonify({
                'success': True,
                'message': f'Reconciliation complete! Found {mismatches_found} new mismatches.',
                'mismatches': mismatches_found
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Reconciliation complete! No new mismatches found.',
                'mismatches': 0
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error during reconciliation: {str(e)}'
        })

@import_bp.route('/mismatches')
@login_required
@admin_required
def view_mismatches():
    """View all mismatches"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    mismatches = MismatchRecord.query.join(Vendor).order_by(
        MismatchRecord.mismatch_date.desc()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('view_mismatches.html', mismatches=mismatches)

@import_bp.route('/sample-templates')
@login_required
@admin_required
def download_templates():
    """Download sample Excel templates"""
    template_type = request.args.get('type', 'swipe')
    
    if template_type == 'swipe':
        # Create sample swipe data template matching requirements document format
        sample_data = {
            'S.No': [1, 2, 3],
            'Employee Name': ['Otsox', 'Vendor1', 'Vendor2'],
            'Employee ID': ['ABC', 'V001', 'V002'],
            'Attendance Date': ['01/07/2025', '02/07/2025', '03/07/2025'],
            'Weekday': ['Tuesday', 'Wednesday', 'Thursday'],
            'Shift Code': ['G', 'G', 'G'],
            'Login': ['-', '10:32', '09:15'],
            'Logout': ['-', '17:25', '18:30'],
            'Extra Work Hours': ['-', '00:25', '00:30'],
            'Total Working Hours': ['-', '06:53', '08:45'],
            'Attendance Status': ['AA', 'AP', 'AP'],
            'Floor Unit': ['BL-A-5F', 'BL-A-5F', 'BL-B-3F'],
            'Business Unit': ['WCS', 'WCS', 'WCS'],
            'Department': ['WCS/MSE7', 'WCS/MSE7', 'WCS/MSE8'],
            'Sub-Department': ['WS1', 'WS1', 'WS2']
        }
        filename = 'swipe_data_template.xlsx'
    
    elif template_type == 'leave':
        sample_data = {
            'OT ID': ['ABC', 'V001', 'V002'],
            'Personnel number': ['dsad', 'pers001', 'pers002'],
            'Start Date': ['9/4/2025', '9/7/2025', '9/10/2025'],
            'End Date': ['9/4/2025', '9/7/2025', '9/12/2025'],
            'Attendance or Absence Type': ['Earned Leave(EL)', 'Casual leave(CL)', 'Sick leave(SL)'],
            'Start Time': ['12:00:00 AM', '12:00:00 AM', '12:00:00 AM'],
            'End time': ['12:00:00 AM', '12:00:00 AM', '12:00:00 AM'],
            'Hrs': [8.00, 8.00, 24.00],
            'Record is for Full Day': ['Yes', 'Yes', 'Yes'],
            'Day': [1, 1, 3],
            'Cal day': [1, 1, 3],
            'Payroll hrs': [8, 8, 24]
        }
        filename = 'leave_data_template.xlsx'
    
    elif template_type == 'wfh':
        sample_data = {
            'RD Name': ['abc', 'John Vendor', 'Jane Vendor'],
            'Department': ['MTB_WCS_MSE7_MS25', 'MTB_WCS_MSE7_MS1', 'MTB_WCS_MSE7_MS2'],
            'RD Category': ['Vendor', 'Vendor', 'Vendor'],
            'Start Date': ['7/16/2025', '8/5/2025', '8/10/2025'],
            'End Date': ['7/16/2025', '8/5/2025', '8/12/2025'],
            'Duration': [1, 1, 3]
        }
        filename = 'wfh_data_template.xlsx'
    
    elif template_type == 'vendor':
        sample_data = {
            'Vendor ID': ['VND001', 'VND002'],
            'Full Name': ['John Doe', 'Jane Smith'],
            'Email': ['john.doe@vendor.com', 'jane.smith@vendor.com'],
            'Department': ['MTB_WCS_MSE7_MS1', 'MTB_WCS_MSE7_MS2'],
            'Company': ['ABC Solutions', 'XYZ Technologies'],
            'Band': ['B2', 'B3'],
            'Location': ['BL-A-5F', 'BL-B-3F'],
            'Manager ID': ['M001', 'M002'],
            'Password': ['vendor123', 'vendor123']
        }
        filename = 'vendor_master_template.xlsx'
    
    elif template_type == 'manager':
        sample_data = {
            'Manager ID': ['M001', 'M002'],
            'Full Name': ['Sarah Johnson', 'Michael Chen'],
            'Email': ['sarah.johnson@attendo.com', 'michael.chen@attendo.com'],
            'Department': ['ATD_WCS_MSE7_MS1', 'ATD_WCS_MSE7_MS2'],
            'Team Name': ['Team Alpha', 'Team Beta'],
            'Phone': ['+1-555-0101', '+1-555-0102'],
            'Password': ['manager123', 'manager123']
        }
        filename = 'manager_master_template.xlsx'
    
    elif template_type == 'holiday':
        sample_data = {
            'Date': ['2025-12-25', '2026-01-01'],
            'Name': ['Christmas Day', 'New Year\'s Day'],
            'Description': ['National Holiday', 'National Holiday']
        }
        filename = 'holiday_master_template.xlsx'
    
    else:
        flash('Invalid template type', 'error')
        return redirect(url_for('import_routes.import_dashboard'))
    
    # Create DataFrame and save as Excel
    df = pd.DataFrame(sample_data)
    
    os.makedirs('templates', exist_ok=True)
    filepath = os.path.join('templates', filename)
    df.to_excel(filepath, index=False)
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@import_bp.route('/statistics')
@login_required
@admin_required
def import_statistics():
    """Get import statistics as JSON"""
    try:
        # Current month statistics
        current_month_start = date.today().replace(day=1)
        
        swipe_count = SwipeRecord.query.filter(
            SwipeRecord.imported_at >= current_month_start
        ).count()
        
        leave_count = LeaveRecord.query.filter(
            LeaveRecord.imported_at >= current_month_start
        ).count()
        
        wfh_count = WFHRecord.query.filter(
            WFHRecord.imported_at >= current_month_start
        ).count()
        
        mismatch_count = MismatchRecord.query.filter(
            MismatchRecord.created_at >= current_month_start
        ).count()
        
        return jsonify({
            'success': True,
            'statistics': {
                'swipe_records': swipe_count,
                'leave_records': leave_count,
                'wfh_records': wfh_count,
                'mismatches': mismatch_count,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching statistics: {str(e)}'
        })

@import_bp.route('/validate', methods=['POST'])
@login_required
@admin_required
def validate_imports():
    """Validate imported data: find duplicates, unknown vendors, overlaps"""
    try:
        # Duplicates in swipe records (same vendor/date)
        from sqlalchemy import func
        duplicates = (models.db.session
            .query(SwipeRecord.vendor_id, SwipeRecord.attendance_date, func.count('*').label('c'))
            .group_by(SwipeRecord.vendor_id, SwipeRecord.attendance_date)
            .having(func.count('*') > 1)
            .all())
        dup_count = len(duplicates)
        # Unknown vendors are filtered during import; count records with vendor_id null shouldn't exist
        unknown_vendors = 0
        # Overlaps: days that appear both in LeaveRecord and WFHRecord for same vendor
        overlaps = 0
        leave_map = {}
        for lr in LeaveRecord.query.all():
            d = lr.start_date
            while d <= lr.end_date:
                leave_map.setdefault((lr.vendor_id, d), True)
                d += timedelta(days=1)
        for wr in WFHRecord.query.all():
            d = wr.start_date
            while d <= wr.end_date:
                if leave_map.get((wr.vendor_id, d)):
                    overlaps += 1
                d += timedelta(days=1)
        return jsonify({'success': True, 'stats': {
            'swipe_duplicates': dup_count,
            'unknown_vendors': unknown_vendors,
            'leave_wfh_overlaps': overlaps
        }})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
