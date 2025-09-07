from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import pandas as pd
from models import UserRole, SwipeRecord, LeaveRecord, WFHRecord, MismatchRecord, Vendor
try:
    from app_old import db
except ImportError:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()
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
    
    pending_mismatches = MismatchRecord.query.filter_by(
        manager_approval='pending'
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
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
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
                
                return redirect(url_for('import.import_dashboard'))
            else:
                flash('Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files only.', 'error')
                
        except Exception as e:
            flash(f'Error importing file: {str(e)}', 'error')
    
    return render_template('import_swipe.html')

@import_bp.route('/leave-data', methods=['GET', 'POST'])
@login_required
@admin_required
def import_leaves():
    """Import leave data"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
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
                
                return redirect(url_for('import.import_dashboard'))
            else:
                flash('Invalid file type. Please upload Excel files only.', 'error')
                
        except Exception as e:
            flash(f'Error importing file: {str(e)}', 'error')
    
    return render_template('import_leaves.html')

@import_bp.route('/wfh-data', methods=['GET', 'POST'])
@login_required
@admin_required
def import_wfh():
    """Import Work From Home data"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
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
                
                return redirect(url_for('import.import_dashboard'))
            else:
                flash('Invalid file type. Please upload Excel files only.', 'error')
                
        except Exception as e:
            flash(f'Error importing file: {str(e)}', 'error')
    
    return render_template('import_wfh.html')

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
        # Create sample swipe data template
        sample_data = {
            'Employee ID': ['EMP001', 'EMP002'],
            'Attendance Date': ['2025-09-07', '2025-09-07'],
            'Weekday': ['Saturday', 'Saturday'],
            'Login': ['09:00:00', '09:15:00'],
            'Logout': ['18:00:00', '18:30:00'],
            'Total Working Hours': ['08:00', '08:15'],
            'Attendance Status': ['AP', 'AP']
        }
        filename = 'swipe_data_template.xlsx'
    
    elif template_type == 'leave':
        sample_data = {
            'OT ID': ['EMP001', 'EMP002'],
            'Start Date': ['2025-09-07', '2025-09-08'],
            'End Date': ['2025-09-07', '2025-09-09'],
            'Attendance or Absence Type': ['Earned Leave', 'Sick Leave'],
            'Day': [1.0, 2.0]
        }
        filename = 'leave_data_template.xlsx'
    
    elif template_type == 'wfh':
        sample_data = {
            'RD Name': ['John Doe', 'Jane Smith'],
            'Start Date': ['2025-09-07', '2025-09-08'],
            'End Date': ['2025-09-07', '2025-09-10'],
            'Duration': [1, 3]
        }
        filename = 'wfh_data_template.xlsx'
    
    else:
        flash('Invalid template type', 'error')
        return redirect(url_for('import.import_dashboard'))
    
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
