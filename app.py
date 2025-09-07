"""
ATTENDO Application - Simple Working Version
This combines everything in one file to avoid circular imports
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vendor_timesheet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

# Register blueprints
app.register_blueprint(import_bp)

# Register Swagger UI
register_swagger_ui(app)

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
    """Manager dashboard"""
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
    
    team_stats = {
        'total_members': len(team_vendors),
        'present_today': len([v for v in team_vendors if DailyStatus.query.filter_by(vendor_id=v.id, status_date=today).first()]),
        'pending_approvals': DailyStatus.query.filter(
            DailyStatus.vendor_id.in_([v.id for v in team_vendors]),
            DailyStatus.approval_status == ApprovalStatus.PENDING
        ).count() if team_vendors else 0,
        'mismatches': 0  # placeholder
    }
    
    return render_template('manager_dashboard.html', 
                         manager=manager,
                         team_stats=team_stats,
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

@app.route('/api/export/monthly-report')
@login_required
def api_export_monthly_report():
    """Export monthly attendance report"""
    month = request.args.get('month', date.today().strftime('%Y-%m'))
    format_type = request.args.get('format', 'excel')
    
    # Mock response for demo
    return jsonify({
        'status': 'success',
        'message': f'Monthly report for {month} generated successfully',
        'download_url': f'/downloads/report_{month}.xlsx',
        'format': format_type,
        'generated_at': datetime.now().isoformat()
    })

@app.route('/vendor/submit-status', methods=['POST'])
@login_required
def api_submit_vendor_status():
    """Submit daily attendance status"""
    if current_user.role != UserRole.VENDOR:
        return jsonify({'error': 'Access denied'}), 403
    
    vendor = current_user.vendor_profile
    if not vendor:
        return jsonify({'error': 'Vendor profile not found'}), 404
    
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
            return jsonify({'error': 'Invalid status value'}), 400
        
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
        
        return jsonify({
            'status': 'success',
            'message': 'Status submitted successfully',
            'data': {
                'status_date': status_date.isoformat(),
                'status': status_value,
                'location': location
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/manager/approve-status/<int:status_id>', methods=['POST'])
@login_required
def api_approve_status(status_id):
    """Approve or reject vendor status"""
    if current_user.role != UserRole.MANAGER:
        return jsonify({'error': 'Access denied'}), 403
    
    daily_status = DailyStatus.query.get_or_404(status_id)
    action = request.form.get('action')
    reason = request.form.get('reason', '')
    
    if action == 'approve':
        daily_status.approval_status = ApprovalStatus.APPROVED
        daily_status.manager_comments = reason
        message = 'Status approved successfully'
    elif action == 'reject':
        daily_status.approval_status = ApprovalStatus.REJECTED
        daily_status.manager_comments = reason
        message = 'Status rejected'
    else:
        return jsonify({'error': 'Invalid action'}), 400
    
    daily_status.approved_at = datetime.utcnow()
    daily_status.approved_by = current_user.id
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': message,
        'action': action,
        'status_id': status_id
    })

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
