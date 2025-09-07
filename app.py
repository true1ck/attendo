"""
ATTENDO Application - Simple Working Version
This combines everything in one file to avoid circular imports
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import os
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import pytz

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hackathon-attendo-vendor-timesheet-2025'
# Use absolute path for SQLite database to ensure it's created in the correct location
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath("vendor_timesheet.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Notification Configuration
app.config['BASE_URL'] = os.getenv('BASE_URL', 'http://localhost:5000')
app.config['SMTP_SERVER'] = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
app.config['SMTP_PORT'] = int(os.getenv('SMTP_PORT', 587))
app.config['SMTP_USER'] = os.getenv('SMTP_USER')  # Set this in environment
app.config['SMTP_PASSWORD'] = os.getenv('SMTP_PASSWORD')  # Set this in environment
app.config['SMS_API_URL'] = os.getenv('SMS_API_URL')  # Optional SMS API endpoint
app.config['SMS_API_KEY'] = os.getenv('SMS_API_KEY')  # Optional SMS API key

# Initialize models first
import models

# Initialize extensions
db = models.db
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Import other modules
from import_routes import import_bp
from notifications import start_notification_scheduler
from swagger_ui import register_swagger_ui
from notification_service import notification_service, setup_notification_scheduler

# Register blueprints
app.register_blueprint(import_bp)

# Register Swagger UI
register_swagger_ui(app)

# Initialize notification service
notification_service.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

def create_tables():
    """Create database tables and initialize demo data"""
    with app.app_context():
        from models import User
        db.create_all()
        
        # Check if demo data already exists
        if User.query.count() == 0:
            initialize_demo_data()
        
        # Setup notification scheduler after tables are created
        setup_notification_scheduler(app, notification_service)

def initialize_demo_data():
    """Initialize the database with demo data for hackathon presentation"""
    from demo_data import create_demo_data
    create_demo_data()

# Import all the route functions directly here
from models import User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday, MismatchRecord, NotificationLog, AuditLog, SystemConfiguration, LeaveRecord, WFHRecord, UserRole, AttendanceStatus, ApprovalStatus
from utils import create_audit_log, generate_monthly_report, import_swipe_data, detect_mismatches

@app.route('/')
def index():
    """Home page - redirect to appropriate dashboard based on user role"""
    if current_user.is_authenticated:
        if current_user.role == UserRole.VENDOR:
            return redirect(url_for('vendor_dashboard'))
        elif current_user.role == UserRole.MANAGER:
            return redirect(url_for('manager_dashboard'))
        elif current_user.role == UserRole.ADMIN:
            return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            create_audit_log(user.id, 'LOGIN', 'users', user.id, {}, {'last_login': str(datetime.utcnow())})
            
            flash(f'Welcome {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    create_audit_log(current_user.id, 'LOGOUT', 'users', current_user.id, {}, {})
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/vendor/dashboard')
@login_required
def vendor_dashboard():
    """Vendor dashboard showing status submission and history"""
    if current_user.role != UserRole.VENDOR:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    vendor = current_user.vendor_profile
    if not vendor:
        flash('Vendor profile not found', 'error')
        return redirect(url_for('login'))
    
    # Get manager information
    manager = None
    if vendor.manager_id:
        manager = Manager.query.filter_by(manager_id=vendor.manager_id).first()
    
    # Get today's status
    today = date.today()
    today_status = DailyStatus.query.filter_by(
        vendor_id=vendor.id, 
        status_date=today
    ).first()
    
    # Get recent status history
    recent_statuses = DailyStatus.query.filter_by(
        vendor_id=vendor.id
    ).order_by(DailyStatus.status_date.desc()).limit(10).all()
    
    # Get pending mismatches
    pending_mismatches = MismatchRecord.query.filter_by(
        vendor_id=vendor.id,
        manager_approval=ApprovalStatus.PENDING
    ).all()
    
    # Check if today is weekend or holiday
    is_weekend = today.weekday() >= 5  # Saturday=5, Sunday=6
    is_holiday = Holiday.query.filter_by(holiday_date=today).first() is not None
    
    return render_template('vendor_dashboard.html', 
                         vendor=vendor,
                         manager=manager,
                         today_status=today_status,
                         recent_statuses=recent_statuses,
                         pending_mismatches=pending_mismatches,
                         is_weekend=is_weekend,
                         is_holiday=is_holiday,
                         today=today)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    # Get statistics
    total_vendors = Vendor.query.count()
    total_managers = Manager.query.count()
    total_statuses_today = DailyStatus.query.filter_by(status_date=date.today()).count()
    
    # Create system stats object for template
    system_stats = {
        'total_vendors': total_vendors,
        'total_managers': total_managers,
        'todays_submissions': total_statuses_today,
        'system_issues': 0  # placeholder
    }
    
    return render_template('admin_dashboard.html',
                         system_stats=system_stats,
                         total_vendors=total_vendors,
                         total_managers=total_managers,
                         total_statuses_today=total_statuses_today)

@app.route('/manager/dashboard')
@login_required
def manager_dashboard():
    """Manager dashboard with real team data"""
    if current_user.role != UserRole.MANAGER:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    manager = current_user.manager_profile
    if not manager:
        flash('Manager profile not found', 'error')
        return redirect(url_for('login'))
    
    # Get team statistics
    today = date.today()
    team_vendors = manager.team_vendors.all() if manager.team_vendors else []
    vendor_ids = [v.id for v in team_vendors]
    
    # Get today's statuses for team
    today_statuses = []
    present_count = 0
    pending_approvals = 0
    mismatches_count = 0
    
    for vendor in team_vendors:
        # Get today's status
        today_status = DailyStatus.query.filter_by(
            vendor_id=vendor.id, 
            status_date=today
        ).first()
        
        if today_status:
            if today_status.status in [AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF, 
                                     AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]:
                present_count += 1
            if today_status.approval_status == ApprovalStatus.PENDING:
                pending_approvals += 1
                
        # Get pending mismatches for this vendor
        vendor_mismatches = MismatchRecord.query.filter_by(
            vendor_id=vendor.id,
            manager_approval=ApprovalStatus.PENDING
        ).count()
        mismatches_count += vendor_mismatches
        
        # Add to today's status list
        today_statuses.append({
            'vendor': vendor,
            'status': today_status,
            'has_mismatch': vendor_mismatches > 0
        })
    
    # Pending approvals for the team (recent)
    pending_statuses = []
    if vendor_ids:
        pending_statuses = DailyStatus.query.filter(
            DailyStatus.vendor_id.in_(vendor_ids),
            DailyStatus.approval_status == ApprovalStatus.PENDING
        ).order_by(DailyStatus.status_date.desc(), DailyStatus.submitted_at.desc()).limit(50).all()
    
    team_stats = {
        'total_members': len(team_vendors),
        'present_today': present_count,
        'pending_approvals': pending_approvals,
        'mismatches': mismatches_count
    }
    
    return render_template('manager_dashboard.html', 
                         manager=manager,
                         team_stats=team_stats,
                         today_statuses=today_statuses,
                         pending_statuses=pending_statuses,
                         today_date=today.strftime('%B %d, %Y'))

# ============= API ROUTES FOR SWAGGER =============

@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """Get dashboard statistics based on user role"""
    if current_user.role == UserRole.ADMIN:
        stats = {
            'total_users': User.query.count(),
            'total_vendors': Vendor.query.count(),
            'total_managers': Manager.query.count(),
            'active_today': DailyStatus.query.filter_by(status_date=date.today()).count(),
            'system_health': 'Excellent',
            'notifications': 5
        }
    elif current_user.role == UserRole.MANAGER:
        manager = current_user.manager_profile
        team_vendors = manager.team_vendors.all() if manager and manager.team_vendors else []
        stats = {
            'team_size': len(team_vendors),
            'pending_approvals': DailyStatus.query.filter(
                DailyStatus.vendor_id.in_([v.id for v in team_vendors]),
                DailyStatus.approval_status == ApprovalStatus.PENDING
            ).count() if team_vendors else 0,
            'approved_today': DailyStatus.query.filter(
                DailyStatus.vendor_id.in_([v.id for v in team_vendors]),
                DailyStatus.status_date == date.today(),
                DailyStatus.approval_status == ApprovalStatus.APPROVED
            ).count() if team_vendors else 0
        }
    else:  # Vendor
        vendor = current_user.vendor_profile
        stats = {
            'total_statuses': DailyStatus.query.filter_by(vendor_id=vendor.id).count() if vendor else 0,
            'pending_mismatches': MismatchRecord.query.filter_by(
                vendor_id=vendor.id, 
                manager_approval=ApprovalStatus.PENDING
            ).count() if vendor else 0,
            'attendance_rate': 95.5,
            'current_month_days': DailyStatus.query.filter(
                DailyStatus.vendor_id == vendor.id,
                DailyStatus.status_date >= date.today().replace(day=1)
            ).count() if vendor else 0
        }
    
    return jsonify(stats)

@app.route('/api/charts/attendance-trends')
@login_required
def api_attendance_trends():
    """Get attendance trend data for charts"""
    # Mock data for demo - replace with actual database queries
    data = {
        'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        'office_attendance': [85, 78, 92, 88],
        'wfh_attendance': [12, 18, 5, 8],
        'leave_requests': [3, 4, 3, 4]
    }
    return jsonify(data)

@app.route('/api/notifications')
@login_required
def api_notifications():
    """Get user notifications"""
    notifications = [
        {
            'id': 1,
            'title': 'Status Approval Required',
            'message': '3 vendor statuses pending your approval',
            'type': 'warning',
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 2,
            'title': 'Monthly Report Ready',
            'message': 'January 2025 attendance report is ready for download',
            'type': 'info',
            'timestamp': datetime.now().isoformat()
        }
    ]
    return jsonify(notifications)

@app.route('/api/test/notification/<notification_type>')
@login_required
def test_notification(notification_type):
    """Test notification sending (for managers only)"""
    if current_user.role != UserRole.MANAGER:
        return jsonify({'error': 'Access denied - managers only'}), 403
    
    try:
        if notification_type == 'summary':
            notification_service.send_daily_summary_notifications('manual')
            message = 'Daily summary notifications sent successfully'
        elif notification_type == 'urgent':
            notification_service.send_urgent_reminder_notifications()
            message = 'Urgent reminder notifications sent successfully'
        else:
            return jsonify({'error': 'Invalid notification type. Use "summary" or "urgent"'}), 400
        
        return jsonify({
            'status': 'success',
            'message': message,
            'notification_type': notification_type
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to send notifications: {str(e)}'
        }), 500

@app.route('/api/export/monthly-report')
@login_required
def api_export_monthly_report():
    """Export monthly attendance report"""
    month = request.args.get('month', date.today().strftime('%Y-%m'))
    format_type = request.args.get('format', 'excel')
    
    try:
        if current_user.role == UserRole.VENDOR:
            # For vendors, generate personal report
            vendor = current_user.vendor_profile
            if not vendor:
                return jsonify({'error': 'Vendor profile not found'}), 404
            
            # Parse month string
            year, month_num = map(int, month.split('-'))
            start_date = date(year, month_num, 1)
            if month_num == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month_num + 1, 1) - timedelta(days=1)
            
            # Get vendor's statuses for the month
            statuses = DailyStatus.query.filter(
                DailyStatus.vendor_id == vendor.id,
                DailyStatus.status_date >= start_date,
                DailyStatus.status_date <= end_date
            ).order_by(DailyStatus.status_date.asc()).all()
            
            # Create report data
            report_data = []
            for status in statuses:
                report_data.append({
                    'Date': status.status_date.strftime('%Y-%m-%d'),
                    'Weekday': status.status_date.strftime('%A'),
                    'Status': status.status.value.replace('_', ' ').title(),
                    'Location': status.location or '-',
                    'Comments': status.comments or '-',
                    'Approval Status': status.approval_status.value.title(),
                    'Submitted At': status.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if status.submitted_at else '-'
                })
            
            if format_type == 'excel' and report_data:
                import pandas as pd
                from io import BytesIO
                from flask import send_file
                
                # Create Excel file in memory
                df = pd.DataFrame(report_data)
                excel_buffer = BytesIO()
                
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=f'{vendor.full_name} - {month}', index=False)
                    
                    # Get workbook and worksheet for formatting
                    workbook = writer.book
                    worksheet = writer.sheets[f'{vendor.full_name} - {month}']
                    
                    # Auto-adjust column widths
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                excel_buffer.seek(0)
                
                filename = f'{vendor.full_name}_{month}_attendance_report.xlsx'
                return send_file(
                    excel_buffer,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            
            elif not report_data:
                return jsonify({
                    'status': 'error',
                    'message': f'No attendance data found for {month}'
                }), 404
            
            else:
                # Return JSON format
                return jsonify({
                    'status': 'success',
                    'data': report_data,
                    'vendor_name': vendor.full_name,
                    'month': month,
                    'total_records': len(report_data)
                })
        
        elif current_user.role == UserRole.MANAGER:
            # For managers, use existing team report logic
            manager = current_user.manager_profile
            if not manager:
                return jsonify({'error': 'Manager profile not found'}), 404
            
            report_data = generate_monthly_report(manager.id, month)
            
            if format_type == 'excel' and report_data:
                import pandas as pd
                from io import BytesIO
                from flask import send_file
                
                df = pd.DataFrame(report_data)
                excel_buffer = BytesIO()
                
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=f'Team Report - {month}', index=False)
                
                excel_buffer.seek(0)
                filename = f'team_report_{month}.xlsx'
                return send_file(
                    excel_buffer,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            
            return jsonify({
                'status': 'success',
                'data': report_data,
                'month': month
            })
        
        else:  # Admin
            report_data = generate_monthly_report(None, month)  # All vendors
            return jsonify({
                'status': 'success',
                'data': report_data,
                'month': month
            })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error generating report: {str(e)}'
        }), 500

@app.route('/monthly-report')
@login_required
def monthly_report_view():
    """Display monthly report with charts and graphs"""
    month = request.args.get('month', date.today().strftime('%Y-%m'))
    
    if current_user.role == UserRole.VENDOR:
        vendor = current_user.vendor_profile
        if not vendor:
            flash('Vendor profile not found', 'error')
            return redirect(url_for('index'))
        
        return render_template('monthly_report.html', 
                             user_type='vendor',
                             profile=vendor,
                             selected_month=month)
    
    elif current_user.role == UserRole.MANAGER:
        manager = current_user.manager_profile
        if not manager:
            flash('Manager profile not found', 'error')
            return redirect(url_for('index'))
        
        return render_template('monthly_report.html',
                             user_type='manager', 
                             profile=manager,
                             selected_month=month)
    
    else:  # Admin
        return render_template('monthly_report.html',
                             user_type='admin',
                             profile=current_user,
                             selected_month=month)

@app.route('/api/monthly-report-data')
@login_required
def api_monthly_report_data():
    """API endpoint for monthly report data (for charts)"""
    month = request.args.get('month', date.today().strftime('%Y-%m'))
    
    try:
        if current_user.role == UserRole.VENDOR:
            vendor = current_user.vendor_profile
            if not vendor:
                return jsonify({'error': 'Vendor profile not found'}), 404
            
            # Parse month string
            year, month_num = map(int, month.split('-'))
            start_date = date(year, month_num, 1)
            if month_num == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month_num + 1, 1) - timedelta(days=1)
            
            # Get vendor's statuses for the month
            statuses = DailyStatus.query.filter(
                DailyStatus.vendor_id == vendor.id,
                DailyStatus.status_date >= start_date,
                DailyStatus.status_date <= end_date
            ).order_by(DailyStatus.status_date.asc()).all()
            
            # Process data for charts
            status_counts = {}
            daily_data = []
            approval_counts = {'pending': 0, 'approved': 0, 'rejected': 0}
            
            for status in statuses:
                # Count status types
                status_type = status.status.value
                status_counts[status_type] = status_counts.get(status_type, 0) + 1
                
                # Count approval status
                approval_status = status.approval_status.value
                approval_counts[approval_status] += 1
                
                # Daily data for timeline
                daily_data.append({
                    'date': status.status_date.strftime('%Y-%m-%d'),
                    'status': status_type,
                    'location': status.location or 'Not specified'
                })
            
            # Calculate working days in month
            total_working_days = 0
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    is_holiday = Holiday.query.filter_by(holiday_date=current_date).first()
                    if not is_holiday:
                        total_working_days += 1
                current_date += timedelta(days=1)
            
            # Calculate attendance rate
            submitted_days = len(statuses)
            attendance_rate = (submitted_days / total_working_days * 100) if total_working_days > 0 else 0
            
            return jsonify({
                'success': True,
                'vendor_name': vendor.full_name,
                'vendor_id': vendor.vendor_id,
                'month': month,
                'status_breakdown': status_counts,
                'approval_breakdown': approval_counts,
                'daily_data': daily_data,
                'summary': {
                    'total_working_days': total_working_days,
                    'submitted_days': submitted_days,
                    'attendance_rate': round(attendance_rate, 1),
                    'pending_approvals': approval_counts['pending']
                }
            })
        
        else:
            # For managers and admins - return team/all data
            return jsonify({'error': 'Manager/Admin reports not implemented yet'}), 501
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/manager/mismatches')
@login_required
def manager_mismatches():
    """Review attendance mismatches between swipe records and submitted status"""
    if current_user.role != UserRole.MANAGER:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    manager = current_user.manager_profile
    if not manager:
        flash('Manager profile not found', 'error')
        return redirect(url_for('login'))
    
    # Get filters
    status_filter = request.args.get('status', 'pending')
    vendor_filter = request.args.get('vendor', 'all')
    
    # Get team vendors
    team_vendors = manager.team_vendors.all()
    vendor_ids = [v.id for v in team_vendors]
    
    # Build query for mismatches
    mismatch_query = MismatchRecord.query.filter(
        MismatchRecord.vendor_id.in_(vendor_ids)
    )
    
    if status_filter != 'all':
        if status_filter == 'pending':
            mismatch_query = mismatch_query.filter(
                MismatchRecord.manager_approval == ApprovalStatus.PENDING
            )
        elif status_filter == 'approved':
            mismatch_query = mismatch_query.filter(
                MismatchRecord.manager_approval == ApprovalStatus.APPROVED
            )
        elif status_filter == 'rejected':
            mismatch_query = mismatch_query.filter(
                MismatchRecord.manager_approval == ApprovalStatus.REJECTED
            )
    
    if vendor_filter != 'all':
        vendor = next((v for v in team_vendors if v.vendor_id == vendor_filter), None)
        if vendor:
            mismatch_query = mismatch_query.filter(MismatchRecord.vendor_id == vendor.id)
    
    # Get mismatches with vendor details
    mismatches = mismatch_query.order_by(MismatchRecord.mismatch_date.desc()).all()
    
    # Group mismatches by vendor
    vendor_mismatches = {}
    for mismatch in mismatches:
        vendor_id = mismatch.vendor.vendor_id
        if vendor_id not in vendor_mismatches:
            vendor_mismatches[vendor_id] = {
                'vendor': mismatch.vendor,
                'mismatches': [],
                'pending_count': 0,
                'total_count': 0
            }
        
        vendor_mismatches[vendor_id]['mismatches'].append(mismatch)
        vendor_mismatches[vendor_id]['total_count'] += 1
        if mismatch.manager_approval == ApprovalStatus.PENDING:
            vendor_mismatches[vendor_id]['pending_count'] += 1
    
    # Calculate summary stats
    total_mismatches = len(mismatches)
    pending_mismatches = len([m for m in mismatches if m.manager_approval == ApprovalStatus.PENDING])
    vendors_with_mismatches = len(vendor_mismatches)
    
    summary_stats = {
        'total_mismatches': total_mismatches,
        'pending_mismatches': pending_mismatches,
        'vendors_affected': vendors_with_mismatches,
        'resolution_rate': round((total_mismatches - pending_mismatches) / total_mismatches * 100, 1) if total_mismatches > 0 else 100
    }
    
    return render_template('manager_mismatches.html',
                         manager=manager,
                         vendor_mismatches=vendor_mismatches,
                         summary_stats=summary_stats,
                         status_filter=status_filter,
                         vendor_filter=vendor_filter,
                         team_vendors=team_vendors,
                         approval_statuses=ApprovalStatus)

@app.route('/manager/mismatch/<int:mismatch_id>/approve', methods=['POST'])
@login_required
def approve_mismatch_explanation(mismatch_id):
    """Approve vendor's mismatch explanation"""
    if current_user.role != UserRole.MANAGER:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        mismatch = MismatchRecord.query.get_or_404(mismatch_id)
        manager = current_user.manager_profile
        
# Verify vendor is in manager's team
        if mismatch.vendor.manager_id != manager.manager_id:
            return jsonify({'error': 'You can only review mismatches for your team members'}), 403
        
        action = request.form.get('action')
        manager_comments = request.form.get('comments', '')
        
        if action == 'approve':
            mismatch.manager_approval = ApprovalStatus.APPROVED
            message = 'Mismatch explanation approved'
        elif action == 'reject':
            mismatch.manager_approval = ApprovalStatus.REJECTED
            message = 'Mismatch explanation rejected'
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        mismatch.manager_comments = manager_comments
        mismatch.approved_by = current_user.id
        mismatch.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        # Create audit log
        create_audit_log(current_user.id, action.upper(), 'mismatch_records', mismatch_id,
                       {'manager_approval': 'pending'}, 
                       {'manager_approval': action, 'manager_comments': manager_comments})
        
        return jsonify({
            'status': 'success',
            'message': message,
            'action': action,
            'mismatch_id': mismatch_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/manager/reports')
@login_required
def manager_reports():
    """Team reports and audit history dashboard"""
    if current_user.role != UserRole.MANAGER:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    manager = current_user.manager_profile
    if not manager:
        flash('Manager profile not found', 'error')
        return redirect(url_for('login'))
    
    # Get date range filters
    start_date_str = request.args.get('start_date', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date_str = request.args.get('end_date', date.today().strftime('%Y-%m-%d'))
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except:
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
    
    # Get team vendors
    team_vendors = manager.team_vendors.all()
    vendor_ids = [v.id for v in team_vendors]
    
    # Generate team attendance report
    report_data = []
    for vendor in team_vendors:
        # Get attendance statistics
        statuses = DailyStatus.query.filter(
            DailyStatus.vendor_id == vendor.id,
            DailyStatus.status_date >= start_date,
            DailyStatus.status_date <= end_date
        ).all()
        
        total_days = len(statuses)
        office_days = len([s for s in statuses if s.status in [AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF]])
        wfh_days = len([s for s in statuses if s.status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]])
        leave_days = len([s for s in statuses if s.status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]])
        pending_days = len([s for s in statuses if s.approval_status == ApprovalStatus.PENDING])
        
        # Calculate working days in period
        working_days = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday to Friday
                is_holiday = Holiday.query.filter_by(holiday_date=current_date).first()
                if not is_holiday:
                    working_days += 1
            current_date += timedelta(days=1)
        
        attendance_rate = (total_days / working_days * 100) if working_days > 0 else 0
        
        report_data.append({
            'vendor': vendor,
            'total_days': total_days,
            'office_days': office_days,
            'wfh_days': wfh_days,
            'leave_days': leave_days,
            'pending_days': pending_days,
            'working_days': working_days,
            'attendance_rate': round(attendance_rate, 1)
        })
    
    # Get audit history for team
    audit_logs = AuditLog.query.filter(
        AuditLog.user_id.in_([manager.user_id] + [v.user_id for v in team_vendors]),
        AuditLog.created_at >= datetime.combine(start_date, datetime.min.time()),
        AuditLog.created_at <= datetime.combine(end_date, datetime.max.time())
    ).order_by(AuditLog.created_at.desc()).limit(50).all()
    
    # Calculate summary statistics
    total_submissions = sum([r['total_days'] for r in report_data])
    total_working_days = sum([r['working_days'] for r in report_data])
    avg_attendance_rate = sum([r['attendance_rate'] for r in report_data]) / len(report_data) if report_data else 0
    total_pending = sum([r['pending_days'] for r in report_data])
    
    summary_stats = {
        'total_submissions': total_submissions,
        'total_working_days': total_working_days,
        'avg_attendance_rate': round(avg_attendance_rate, 1),
        'total_pending': total_pending,
        'submission_rate': round(total_submissions / total_working_days * 100, 1) if total_working_days > 0 else 0
    }
    
    return render_template('manager_reports.html',
                         manager=manager,
                         report_data=report_data,
                         audit_logs=audit_logs,
                         summary_stats=summary_stats,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/vendor/edit-status/<int:status_id>', methods=['GET', 'POST'])
@login_required
def vendor_edit_status(status_id):
    """Edit existing daily attendance status"""
    if current_user.role != UserRole.VENDOR:
        return jsonify({'error': 'Access denied'}), 403
    
    vendor = current_user.vendor_profile
    if not vendor:
        return jsonify({'error': 'Vendor profile not found'}), 404
    
    # Get the status record
    status_record = DailyStatus.query.get_or_404(status_id)
    
    # Verify ownership
    if status_record.vendor_id != vendor.id:
        return jsonify({'error': 'Access denied - not your status'}), 403
    
    # Check if status can be edited (only pending or rejected)
    if status_record.approval_status not in [ApprovalStatus.PENDING, ApprovalStatus.REJECTED]:
        return jsonify({'error': 'Cannot edit approved status'}), 400
    
    if request.method == 'GET':
        # Return status data for the edit form
        return jsonify({
            'id': status_record.id,
            'status_date': status_record.status_date.strftime('%Y-%m-%d'),
            'status': status_record.status.value,
            'location': status_record.location or '',
            'comments': status_record.comments or '',
            'approval_status': status_record.approval_status.value
        })
    
    # POST - Update the status
    try:
        status_value = request.form['status']
        location = request.form.get('location', '')
        comments = request.form.get('comments', '')
        
        # Convert string to enum
        status_map = {
            'in_office_full': AttendanceStatus.IN_OFFICE_FULL,
            'in_office_half': AttendanceStatus.IN_OFFICE_HALF,
            'wfh_full': AttendanceStatus.WFH_FULL,
            'wfh_half': AttendanceStatus.WFH_HALF,
            'leave_full': AttendanceStatus.LEAVE_FULL,
            'leave_half': AttendanceStatus.LEAVE_HALF,
            'absent': AttendanceStatus.ABSENT
        }
        
        new_status = status_map.get(status_value)
        if not new_status:
            return jsonify({'error': 'Invalid status value'}), 400
        
        # Store old values for audit
        old_values = {
            'status': status_record.status.value,
            'location': status_record.location,
            'comments': status_record.comments,
            'approval_status': status_record.approval_status.value
        }
        
        # Update the status
        status_record.status = new_status
        status_record.location = location
        status_record.comments = comments
        status_record.submitted_at = datetime.utcnow()
        status_record.approval_status = ApprovalStatus.PENDING  # Reset to pending
        status_record.manager_comments = None  # Clear previous manager comments
        
        db.session.commit()
        
        # Create audit log
        new_values = {
            'status': status_value,
            'location': location,
            'comments': comments,
            'approval_status': 'pending'
        }
        create_audit_log(current_user.id, 'UPDATE', 'daily_statuses', status_id, old_values, new_values)
        
        return jsonify({
            'status': 'success',
            'message': 'Status updated successfully!',
            'data': {
                'id': status_record.id,
                'status': new_status.value,
                'location': location,
                'comments': comments,
                'approval_status': 'pending',
                'status_date': status_record.status_date.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error updating status: {str(e)}'
        }), 500

@app.route('/vendor/submit-status', methods=['POST'])
@login_required
def vendor_submit_status():
    """Submit daily attendance status"""
    if current_user.role != UserRole.VENDOR:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    vendor = current_user.vendor_profile
    if not vendor:
        flash('Vendor profile not found', 'error')
        return redirect(url_for('login'))
    
    try:
        status_date = datetime.strptime(request.form['status_date'], '%Y-%m-%d').date()
        status_value = request.form['status']
        location = request.form.get('location', '')
        comments = request.form.get('comments', '')
        
        # Convert string to enum
        status_map = {
            'in_office_full': AttendanceStatus.IN_OFFICE_FULL,
            'in_office_half': AttendanceStatus.IN_OFFICE_HALF,
            'wfh_full': AttendanceStatus.WFH_FULL,
            'wfh_half': AttendanceStatus.WFH_HALF,
            'leave_full': AttendanceStatus.LEAVE_FULL,
            'leave_half': AttendanceStatus.LEAVE_HALF,
            'absent': AttendanceStatus.ABSENT
        }
        
        status = status_map.get(status_value)
        if not status:
            flash('Invalid status value', 'error')
            return redirect(url_for('vendor_dashboard'))
        
        # Check if status already exists
        existing_status = DailyStatus.query.filter_by(
            vendor_id=vendor.id,
            status_date=status_date
        ).first()
        
        if existing_status:
            existing_status.status = status
            existing_status.location = location
            existing_status.comments = comments
            existing_status.submitted_at = datetime.utcnow()
            existing_status.approval_status = ApprovalStatus.PENDING
        else:
            new_status = DailyStatus(
                vendor_id=vendor.id,
                status_date=status_date,
                status=status,
                location=location,
                comments=comments
            )
            db.session.add(new_status)
        
        db.session.commit()
        
        create_audit_log(current_user.id, 'CREATE' if not existing_status else 'UPDATE', 
                       'daily_statuses', existing_status.id if existing_status else None, 
                       {}, {'status': status_value, 'location': location})
        
        flash('Status submitted successfully!', 'success')
        return redirect(url_for('vendor_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting status: {str(e)}', 'error')
        return redirect(url_for('vendor_dashboard'))

@app.route('/manager/approve-status/<int:status_id>', methods=['POST'])
@login_required
def api_approve_status(status_id):
    """Approve or reject vendor status"""
    try:
        # Check if user is manager
        if current_user.role != UserRole.MANAGER:
            print(f"❌ Access denied - User role: {current_user.role}")
            return jsonify({'error': 'Access denied - Manager role required'}), 403
        
        # Get manager profile
        manager = current_user.manager_profile
        if not manager:
            print(f"❌ Manager profile not found for user: {current_user.username}")
            return jsonify({'error': 'Manager profile not found'}), 404
        
        # Get status record
        daily_status = DailyStatus.query.get(status_id)
        if not daily_status:
            print(f"❌ Status record not found: {status_id}")
            return jsonify({'error': 'Status record not found'}), 404
        
        # Verify vendor is in manager's team
        vendor = daily_status.vendor
        # Compare against manager.manager_id (string FK), not manager.id
        if vendor.manager_id != manager.manager_id:
            print(f"❌ Vendor {vendor.vendor_id} not in manager's team")
            return jsonify({'error': 'You can only approve statuses for your team members'}), 403
        
        # Get action and reason
        action = request.form.get('action')
        reason = request.form.get('reason', '')
        
        print(f"📝 Processing {action} for status {status_id} by {current_user.username}")
        
        if action == 'approve':
            daily_status.approval_status = ApprovalStatus.APPROVED
            daily_status.manager_comments = reason or 'Approved'
            message = 'Status approved successfully'
            print(f"✅ Approved status {status_id}")
        elif action == 'reject':
            daily_status.approval_status = ApprovalStatus.REJECTED
            daily_status.manager_comments = reason or 'Rejected'
            message = 'Status rejected'
            print(f"❌ Rejected status {status_id} - Reason: {reason}")
        else:
            print(f"❌ Invalid action: {action}")
            return jsonify({'error': 'Invalid action - must be approve or reject'}), 400
        
        # Update approval metadata
        daily_status.approved_at = datetime.utcnow()
        daily_status.approved_by = current_user.id
        
        # Commit to database
        db.session.commit()
        print(f"✅ Database updated successfully")
        
        # Create audit log
        create_audit_log(current_user.id, action.upper(), 'daily_statuses', status_id, 
                       {'approval_status': 'pending'}, 
                       {'approval_status': action, 'manager_comments': reason})
        
        return jsonify({
            'status': 'success',
            'message': message,
            'action': action,
            'status_id': status_id,
            'approval_status': daily_status.approval_status.value,
            'manager_comments': daily_status.manager_comments
        })
        
    except Exception as e:
        print(f"❌ Error in approve/reject: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/manager/approve-status/bulk', methods=['POST'])
@login_required
def api_bulk_approve_status():
    """Bulk approve or reject vendor statuses for a manager's team"""
    try:
        if current_user.role != UserRole.MANAGER:
            return jsonify({'error': 'Access denied - Manager role required'}), 403
        
        manager = current_user.manager_profile
        if not manager:
            return jsonify({'error': 'Manager profile not found'}), 404
        
        data = request.get_json(silent=True) or {}
        action = data.get('action')
        status_ids = data.get('status_ids', [])
        reason = data.get('reason', '')
        
        if action not in ['approve', 'reject']:
            return jsonify({'error': 'Invalid action'}), 400
        if not status_ids:
            return jsonify({'error': 'No status IDs provided'}), 400
        
        # Limit to manager's team
        team_vendor_ids = [v.id for v in manager.team_vendors.all()] if manager.team_vendors else []
        if not team_vendor_ids:
            return jsonify({'error': 'No team members found'}), 400
        
        statuses = DailyStatus.query.filter(
            DailyStatus.id.in_(status_ids),
            DailyStatus.vendor_id.in_(team_vendor_ids)
        ).all()
        
        updated = 0
        for ds in statuses:
            old_status = ds.approval_status.value
            if action == 'approve':
                ds.approval_status = ApprovalStatus.APPROVED
                ds.manager_comments = reason or 'Approved'
            else:
                ds.approval_status = ApprovalStatus.REJECTED
                ds.manager_comments = reason or 'Rejected'
            ds.approved_at = datetime.utcnow()
            ds.approved_by = current_user.id
            updated += 1
            # Audit log per record
            create_audit_log(current_user.id, action.upper(), 'daily_statuses', ds.id,
                             {'approval_status': old_status},
                             {'approval_status': action, 'manager_comments': ds.manager_comments})
        
        db.session.commit()
        return jsonify({'status': 'success', 'updated': updated, 'action': action})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/add-holiday', methods=['POST'])
@login_required
def api_add_holiday():
    """Add a new holiday"""
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        holiday_date = datetime.strptime(request.form['holiday_date'], '%Y-%m-%d').date()
        name = request.form['name']
        description = request.form.get('description', '')
        
        # Check if holiday already exists
        existing_holiday = Holiday.query.filter_by(holiday_date=holiday_date).first()
        if existing_holiday:
            return jsonify({'error': 'Holiday already exists for this date'}), 400
        
        new_holiday = Holiday(
            holiday_date=holiday_date,
            name=name,
            description=description
        )
        
        db.session.add(new_holiday)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Holiday added successfully',
            'data': {
                'date': holiday_date.isoformat(),
                'name': name,
                'description': description
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/vendor/mismatch/<int:mismatch_id>/explain', methods=['POST'])
@login_required
def submit_mismatch_explanation(mismatch_id):
    """Submit explanation for attendance mismatch"""
    if current_user.role != UserRole.VENDOR:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    mismatch = MismatchRecord.query.get_or_404(mismatch_id)
    
    # Verify this mismatch belongs to current vendor
    vendor = current_user.vendor_profile
    if not vendor or mismatch.vendor_id != vendor.id:
        flash('Access denied', 'error')
        return redirect(url_for('vendor_dashboard'))
    
    try:
        reason = request.form['reason']
        mismatch.vendor_reason = reason
        mismatch.vendor_submitted_at = datetime.utcnow()
        
        db.session.commit()
        
        create_audit_log(current_user.id, 'UPDATE', 'mismatch_records', mismatch.id, 
                       {'vendor_reason': mismatch.vendor_reason}, 
                       {'vendor_reason': reason})
        
        flash('Mismatch explanation submitted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting explanation: {str(e)}', 'error')
    
    return redirect(url_for('vendor_dashboard'))

if __name__ == '__main__':
    print("\n" + "="*70)
    print("ATTENDO - Starting Application...")
    print("="*70)
    
    # Create tables and initialize demo data
    with app.app_context():
        create_tables()
        print("Database initialized with demo data!")
    
    # Start notification scheduler
    start_notification_scheduler()
    print("Notification scheduler started!")
    
    print("="*70)
    print("ATTENDO is now running!")
    print("="*70)
    print("\nAccess the application at:")
    print("   Web Interface: http://localhost:5000")
    print("   API Documentation: http://localhost:5000/api/docs")
    print("\nLogin Credentials:")
    print("   Admin:    admin / admin123")
    print("   Manager:  manager1 / manager123")
    print("   Vendor:   vendor1 / vendor123")
    print("\nPress CTRL+C to stop the server")
    print("="*70 + "\n")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
