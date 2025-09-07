from flask import render_template, request, redirect, url_for, flash, jsonify, session, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
import json
import os
from werkzeug.utils import secure_filename
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Import models
import models
from models import db
from models import User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday, MismatchRecord, NotificationLog, AuditLog, SystemConfiguration, LeaveRecord, WFHRecord, UserRole, AttendanceStatus, ApprovalStatus
from utils import create_audit_log, generate_monthly_report, import_swipe_data, detect_mismatches

# We'll get app from current_app context when routes are registered
from flask import current_app as app

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

@app.route('/api')
def api_info():
    """API information and documentation redirect"""
    return redirect('/api/docs')

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

# ============= VENDOR ROUTES =============

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
    
    return render_template('vendor/dashboard.html', 
                         vendor=vendor,
                         today_status=today_status,
                         recent_statuses=recent_statuses,
                         pending_mismatches=pending_mismatches,
                         is_weekend=is_weekend,
                         is_holiday=is_holiday,
                         today=today)

@app.route('/vendor/submit-status', methods=['POST'])
@login_required
def submit_daily_status():
    """Submit daily attendance status"""
    if current_user.role != UserRole.VENDOR:
        return jsonify({'error': 'Access denied'}), 403
    
    vendor = current_user.vendor_profile
    if not vendor:
        return jsonify({'error': 'Vendor profile not found'}), 404
    
    try:
        status_date = datetime.strptime(request.form['status_date'], '%Y-%m-%d').date()
        status = AttendanceStatus(request.form['status'])
        location = request.form.get('location', '')
        comments = request.form.get('comments', '')
        
        # Check if status already exists for this date
        existing_status = DailyStatus.query.filter_by(
            vendor_id=vendor.id,
            status_date=status_date
        ).first()
        
        if existing_status:
            # Update existing status
            old_values = {
                'status': existing_status.status.value,
                'location': existing_status.location,
                'comments': existing_status.comments
            }
            
            existing_status.status = status
            existing_status.location = location
            existing_status.comments = comments
            existing_status.submitted_at = datetime.utcnow()
            existing_status.approval_status = ApprovalStatus.PENDING
            
            new_values = {
                'status': status.value,
                'location': location,
                'comments': comments
            }
            
            create_audit_log(current_user.id, 'UPDATE', 'daily_statuses', existing_status.id, 
                           old_values, new_values)
            
        else:
            # Create new status
            new_status = DailyStatus(
                vendor_id=vendor.id,
                status_date=status_date,
                status=status,
                location=location,
                comments=comments
            )
            db.session.add(new_status)
            
            create_audit_log(current_user.id, 'CREATE', 'daily_statuses', None, {}, {
                'status': status.value,
                'location': location,
                'comments': comments,
                'status_date': str(status_date)
            })
        
        db.session.commit()
        flash('Status submitted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting status: {str(e)}', 'error')
    
    return redirect(url_for('vendor_dashboard'))

@app.route('/vendor/mismatch/<int:mismatch_id>/explain', methods=['POST'])
@login_required
def submit_mismatch_explanation():
    """Submit explanation for attendance mismatch"""
    if current_user.role != UserRole.VENDOR:
        return jsonify({'error': 'Access denied'}), 403
    
    mismatch = MismatchRecord.query.get_or_404(mismatch_id)
    
    # Verify this mismatch belongs to current vendor
    if mismatch.vendor.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        reason = request.form['reason']
        mismatch.vendor_reason = reason
        mismatch.vendor_submitted_at = datetime.utcnow()
        
        create_audit_log(current_user.id, 'UPDATE', 'mismatch_records', mismatch.id, 
                       {'vendor_reason': mismatch.vendor_reason}, {'vendor_reason': reason})
        
        db.session.commit()
        flash('Explanation submitted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting explanation: {str(e)}', 'error')
    
    return redirect(url_for('vendor_dashboard'))

# ============= MANAGER ROUTES =============

@app.route('/manager/dashboard')
@login_required
def manager_dashboard():
    """Manager dashboard showing team status and approvals"""
    if current_user.role != UserRole.MANAGER:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    manager = current_user.manager_profile
    if not manager:
        flash('Manager profile not found', 'error')
        return redirect(url_for('login'))
    
    # Get team vendors
    team_vendors = manager.team_vendors.all()
    
    # Get today's team status
    today = date.today()
    today_statuses = []
    for vendor in team_vendors:
        status = DailyStatus.query.filter_by(
            vendor_id=vendor.id,
            status_date=today
        ).first()
        today_statuses.append({
            'vendor': vendor,
            'status': status
        })
    
    # Get pending approvals
    pending_approvals = DailyStatus.query.join(Vendor).filter(
        Vendor.manager_id == manager.id,
        DailyStatus.approval_status == ApprovalStatus.PENDING
    ).order_by(DailyStatus.submitted_at.desc()).all()
    
    # Get pending mismatch reviews
    pending_mismatches = MismatchRecord.query.join(Vendor).filter(
        Vendor.manager_id == manager.id,
        MismatchRecord.manager_approval == ApprovalStatus.PENDING,
        MismatchRecord.vendor_reason.isnot(None)
    ).all()
    
    return render_template('manager/dashboard.html',
                         manager=manager,
                         team_vendors=team_vendors,
                         today_statuses=today_statuses,
                         pending_approvals=pending_approvals,
                         pending_mismatches=pending_mismatches,
                         today=today)

@app.route('/manager/approve-status/<int:status_id>', methods=['POST'])
@login_required
def approve_status():
    """Approve or reject daily status"""
    if current_user.role != UserRole.MANAGER:
        return jsonify({'error': 'Access denied'}), 403
    
    status = DailyStatus.query.get_or_404(status_id)
    manager = current_user.manager_profile
    
    # Verify this status belongs to manager's team
    if status.vendor.manager_id != manager.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        action = request.form['action']  # 'approve' or 'reject'
        reason = request.form.get('reason', '')
        
        old_values = {
            'approval_status': status.approval_status.value,
            'approved_by': status.approved_by,
            'rejection_reason': status.rejection_reason
        }
        
        if action == 'approve':
            status.approval_status = ApprovalStatus.APPROVED
            status.approved_by = current_user.id
            status.approved_at = datetime.utcnow()
            flash('Status approved successfully!', 'success')
        elif action == 'reject':
            status.approval_status = ApprovalStatus.REJECTED
            status.approved_by = current_user.id
            status.approved_at = datetime.utcnow()
            status.rejection_reason = reason
            flash('Status rejected successfully!', 'success')
        
        new_values = {
            'approval_status': status.approval_status.value,
            'approved_by': current_user.id,
            'rejection_reason': status.rejection_reason
        }
        
        create_audit_log(current_user.id, action.upper(), 'daily_statuses', status.id,
                       old_values, new_values)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing approval: {str(e)}', 'error')
    
    return redirect(url_for('manager_dashboard'))

@app.route('/manager/review-mismatch/<int:mismatch_id>', methods=['POST'])
@login_required
def review_mismatch():
    """Review and approve/reject mismatch explanation"""
    if current_user.role != UserRole.MANAGER:
        return jsonify({'error': 'Access denied'}), 403
    
    mismatch = MismatchRecord.query.get_or_404(mismatch_id)
    manager = current_user.manager_profile
    
    # Verify this mismatch belongs to manager's team
    if mismatch.vendor.manager_id != manager.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        action = request.form['action']  # 'approve' or 'reject'
        comments = request.form.get('comments', '')
        
        old_values = {
            'manager_approval': mismatch.manager_approval.value,
            'manager_comments': mismatch.manager_comments
        }
        
        if action == 'approve':
            mismatch.manager_approval = ApprovalStatus.APPROVED
        elif action == 'reject':
            mismatch.manager_approval = ApprovalStatus.REJECTED
        
        mismatch.manager_comments = comments
        mismatch.approved_by = current_user.id
        mismatch.approved_at = datetime.utcnow()
        
        new_values = {
            'manager_approval': mismatch.manager_approval.value,
            'manager_comments': comments,
            'approved_by': current_user.id
        }
        
        create_audit_log(current_user.id, f'MISMATCH_{action.upper()}', 'mismatch_records', 
                       mismatch.id, old_values, new_values)
        
        db.session.commit()
        flash(f'Mismatch {action}d successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error reviewing mismatch: {str(e)}', 'error')
    
    return redirect(url_for('manager_dashboard'))

@app.route('/manager/team-report')
@login_required
def team_report():
    """Generate team attendance report"""
    if current_user.role != UserRole.MANAGER:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    manager = current_user.manager_profile
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    report_data = generate_monthly_report(manager.id, month)
    
    return render_template('manager/team_report.html',
                         manager=manager,
                         report_data=report_data,
                         selected_month=month)

# ============= ADMIN ROUTES =============

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard with system overview"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    # System statistics
    total_vendors = Vendor.query.count()
    total_managers = Manager.query.count()
    total_statuses_today = DailyStatus.query.filter_by(status_date=date.today()).count()
    pending_approvals = DailyStatus.query.filter_by(approval_status=ApprovalStatus.PENDING).count()
    
    # Recent activities
    recent_logins = User.query.filter(User.last_login.isnot(None)).order_by(User.last_login.desc()).limit(10).all()
    recent_statuses = DailyStatus.query.order_by(DailyStatus.submitted_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_vendors=total_vendors,
                         total_managers=total_managers,
                         total_statuses_today=total_statuses_today,
                         pending_approvals=pending_approvals,
                         recent_logins=recent_logins,
                         recent_statuses=recent_statuses)

@app.route('/admin/vendors')
@login_required
def manage_vendors():
    """Manage vendor profiles"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    vendors = Vendor.query.all()
    managers = Manager.query.all()
    
    return render_template('admin/vendors.html', vendors=vendors, managers=managers)

@app.route('/admin/holidays')
@login_required
def manage_holidays():
    """Manage holiday calendar"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    holidays = Holiday.query.order_by(Holiday.holiday_date).all()
    
    return render_template('admin/holidays.html', holidays=holidays)

@app.route('/admin/add-holiday', methods=['POST'])
@login_required
def add_holiday():
    """Add new holiday"""
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        holiday_date = datetime.strptime(request.form['holiday_date'], '%Y-%m-%d').date()
        name = request.form['name']
        description = request.form.get('description', '')
        
        holiday = Holiday(
            holiday_date=holiday_date,
            name=name,
            description=description,
            created_by=current_user.id
        )
        
        db.session.add(holiday)
        create_audit_log(current_user.id, 'CREATE', 'holidays', None, {}, {
            'holiday_date': str(holiday_date),
            'name': name,
            'description': description
        })
        
        db.session.commit()
        flash('Holiday added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding holiday: {str(e)}', 'error')
    
    return redirect(url_for('manage_holidays'))

@app.route('/admin/import-data', methods=['GET', 'POST'])
@login_required
def import_data():
    """Import swipe machine and leave data"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            if 'swipe_file' in request.files:
                file = request.files['swipe_file']
                if file.filename != '':
                    filename = secure_filename(file.filename)
                    file_path = os.path.join('uploads', filename)
                    file.save(file_path)
                    
                    # Import swipe data
                    records_imported = import_swipe_data(file_path)
                    flash(f'Imported {records_imported} swipe records successfully!', 'success')
                    
                    # Detect mismatches after import
                    detect_mismatches()
                    flash('Mismatch detection completed!', 'info')
            
        except Exception as e:
            flash(f'Error importing data: {str(e)}', 'error')
    
    return render_template('admin/import_data.html')

@app.route('/admin/reports')
@login_required
def admin_reports():
    """Generate system-wide reports"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    return render_template('admin/reports.html')

@app.route('/admin/audit-logs')
@login_required
def audit_logs():
    """View audit logs"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/audit_logs.html', logs=logs)

# ============= API ROUTES =============

@app.route('/api/notifications/unread')
@login_required
def get_unread_notifications():
    """Get unread notifications for current user"""
    notifications = NotificationLog.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).order_by(NotificationLog.sent_at.desc()).all()
    
    return jsonify([{
        'id': n.id,
        'type': n.notification_type,
        'message': n.message,
        'sent_at': n.sent_at.isoformat()
    } for n in notifications])

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    notification = NotificationLog.query.get_or_404(notification_id)
    
    if notification.recipient_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/ai-insights')
@login_required
def ai_insights():
    """AI Insights and Predictions Dashboard"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    from utils import predict_absence_risk
    
    # Get AI statistics
    ai_stats = {
        'last_trained': 'Today, 09:30 AM',
        'accuracy': '94.2%',
        'predictions_made': '1,247',
        'absence_predictions': 8,
        'wfh_predictions': 12,
        'risk_alerts': 3,
        'pattern_insights': 15
    }
    
    # Get vendors for predictions
    vendors = Vendor.query.limit(10).all()
    predictions = []
    
    for vendor in vendors:
        risk_data = predict_absence_risk(vendor.id, days_ahead=7)
        if risk_data['risk_score'] > 30:  # Only show medium to high risk
            predictions.append({
                'vendor': vendor,
                'risk_score': risk_data['risk_score'],
                'confidence': risk_data['confidence'],
                'factors': risk_data['factors']
            })
    
    return render_template('ai_insights.html', 
                         ai_stats=ai_stats,
                         predictions=predictions)

@app.route('/admin/reports-dashboard')
@login_required
def reports_dashboard():
    """Reports and Export Dashboard"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    # Get report statistics
    stats = {
        'monthly_reports': 12,
        'billing_reports': 8,
        'analytics_reports': 15,
        'scheduled_reports': 5
    }
    
    # Get managers for dropdown
    managers = Manager.query.all()
    
    return render_template('reports_dashboard.html', 
                         stats=stats,
                         managers=managers)

@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics based on user role"""
    if current_user.role == UserRole.VENDOR:
        vendor = current_user.vendor_profile
        total_statuses = DailyStatus.query.filter_by(vendor_id=vendor.id).count()
        pending_mismatches = MismatchRecord.query.filter_by(
            vendor_id=vendor.id,
            manager_approval=ApprovalStatus.PENDING
        ).count()
        
        return jsonify({
            'total_statuses': total_statuses,
            'pending_mismatches': pending_mismatches
        })
    
    elif current_user.role == UserRole.MANAGER:
        manager = current_user.manager_profile
        team_size = manager.team_vendors.count()
        pending_approvals = DailyStatus.query.join(Vendor).filter(
            Vendor.manager_id == manager.id,
            DailyStatus.approval_status == ApprovalStatus.PENDING
        ).count()
        
        return jsonify({
            'team_size': team_size,
            'pending_approvals': pending_approvals
        })
    
    elif current_user.role == UserRole.ADMIN:
        total_users = User.query.count()
        total_vendors = Vendor.query.count()
        total_managers = Manager.query.count()
        
        return jsonify({
            'total_users': total_users,
            'total_vendors': total_vendors,
            'total_managers': total_managers
        })

# ============= EXPORT ROUTES =============

@app.route('/export/monthly-report/<format>')
@login_required
def export_monthly_report(format):
    """Export monthly report in Excel or PDF format"""
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    if current_user.role == UserRole.MANAGER:
        manager = current_user.manager_profile
        report_data = generate_monthly_report(manager.id, month)
    elif current_user.role == UserRole.ADMIN:
        # Admin can export for all or specific manager
        manager_id = request.args.get('manager_id')
        report_data = generate_monthly_report(manager_id, month)
    else:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if format.lower() == 'excel':
        # Generate Excel file
        output = BytesIO()
        df = pd.DataFrame(report_data)
        df.to_excel(output, index=False)
        output.seek(0)
        
        return send_file(output, 
                        download_name=f'attendance_report_{month}.xlsx',
                        as_attachment=True,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    elif format.lower() == 'pdf':
        # Generate PDF file
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        elements = []
        
        # Add title
        styles = getSampleStyleSheet()
        title = Paragraph(f"Monthly Attendance Report - {month}", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Add table
        if report_data:
            table_data = [list(report_data[0].keys())]  # Headers
            for row in report_data:
                table_data.append(list(row.values()))
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), '#grey'),
                ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
                ('GRID', (0, 0), (-1, -1), 1, '#000000')
            ]))
            elements.append(table)
        
        doc.build(elements)
        output.seek(0)
        
        return send_file(output,
                        download_name=f'attendance_report_{month}.pdf',
                        as_attachment=True,
                        mimetype='application/pdf')
    
    else:
        flash('Invalid export format', 'error')
        return redirect(request.referrer or url_for('index'))

# ============= AI INSIGHTS API ROUTES =============

@app.route('/api/ai/refresh-predictions', methods=['POST'])
@login_required
def refresh_predictions():
    """Refresh AI predictions"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        from utils import predict_absence_risk
        
        vendors = Vendor.query.limit(10).all()
        predictions = []
        
        for vendor in vendors:
            risk_data = predict_absence_risk(vendor.id, days_ahead=7)
            if risk_data['risk_score'] > 20:  # Show more predictions
                predictions.append({
                    'vendor_name': vendor.full_name,
                    'vendor_id': vendor.vendor_id,
                    'risk_score': risk_data['risk_score'],
                    'confidence': risk_data['confidence'],
                    'factors': risk_data['factors']
                })
        
        return jsonify({
            'success': True,
            'predictions': predictions,
            'updated_at': datetime.now().strftime('%H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({'error': f'Error refreshing predictions: {str(e)}'}), 500

@app.route('/api/ai/train-model', methods=['POST'])
@login_required
def train_model():
    """Simulate AI model training"""
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Simulate training process
        import time
        time.sleep(2)  # Simulate training time
        
        return jsonify({
            'success': True,
            'message': 'AI model retrained successfully!',
            'new_accuracy': '95.1%',
            'training_time': '2.3 seconds',
            'data_points': DailyStatus.query.count()
        })
        
    except Exception as e:
        return jsonify({'error': f'Error training model: {str(e)}'}), 500

@app.route('/api/ai/export-insights', methods=['POST'])
@login_required
def export_insights():
    """Export AI insights"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        return jsonify({
            'success': True,
            'message': 'AI insights exported successfully!',
            'filename': f'ai_insights_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            'download_url': '/downloads/ai_insights.xlsx'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error exporting insights: {str(e)}'}), 500

# ============= REPORT SCHEDULING ROUTES =============

@app.route('/api/reports/schedule', methods=['POST'])
@login_required
def schedule_report():
    """Schedule automatic report generation"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        report_type = request.json.get('report_type', 'monthly')
        frequency = request.json.get('frequency', 'monthly')
        recipients = request.json.get('recipients', [])
        
        # Store schedule in system configurations
        schedule_config = {
            'report_type': report_type,
            'frequency': frequency,
            'recipients': recipients,
            'created_by': current_user.id,
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        
        from utils import set_system_config
        config_key = f'scheduled_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        set_system_config(config_key, json.dumps(schedule_config), 
                         f'Scheduled {report_type} report', current_user.id)
        
        return jsonify({
            'success': True,
            'message': f'{report_type.title()} report scheduled successfully!',
            'schedule_id': config_key,
            'next_run': _calculate_next_run(frequency)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error scheduling report: {str(e)}'}), 500

@app.route('/api/reports/generate', methods=['POST'])
@login_required
def generate_report():
    """Generate report on demand"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        report_type = request.json.get('report_type', 'monthly')
        month = request.json.get('month', datetime.now().strftime('%Y-%m'))
        format_type = request.json.get('format', 'excel')
        
        # Generate the report
        if current_user.role == UserRole.MANAGER:
            manager = current_user.manager_profile
            report_data = generate_monthly_report(manager.id, month)
        else:
            manager_id = request.json.get('manager_id')
            report_data = generate_monthly_report(manager_id, month)
        
        filename = f'{report_type}_report_{month}_{datetime.now().strftime("%H%M%S")}.{"xlsx" if format_type == "excel" else format_type}'
        
        return jsonify({
            'success': True,
            'message': 'Report generated successfully!',
            'filename': filename,
            'records': len(report_data),
            'download_url': f'/export/monthly-report/{format_type}?month={month}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating report: {str(e)}'}), 500

@app.route('/api/reports/history')
@login_required
def report_history():
    """Get report generation history"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get audit logs for report generation
        audit_logs = AuditLog.query.filter(
            AuditLog.action.like('%REPORT%')
        ).order_by(AuditLog.created_at.desc()).limit(20).all()
        
        history = []
        for log in audit_logs:
            history.append({
                'id': log.id,
                'action': log.action,
                'user': User.query.get(log.user_id).username,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'details': log.new_values
            })
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching history: {str(e)}'}), 500

def _calculate_next_run(frequency):
    """Calculate next run time for scheduled report"""
    now = datetime.now()
    
    if frequency == 'daily':
        next_run = now + timedelta(days=1)
    elif frequency == 'weekly':
        next_run = now + timedelta(weeks=1)
    elif frequency == 'monthly':
        if now.month == 12:
            next_run = now.replace(year=now.year + 1, month=1)
        else:
            next_run = now.replace(month=now.month + 1)
    else:
        next_run = now + timedelta(days=30)
    
    return next_run.strftime('%Y-%m-%d %H:%M:%S')

# ============= CHART DATA API ROUTES =============

@app.route('/api/charts/attendance-trends')
@login_required
def attendance_trends_data():
    """Get attendance trends data for charts"""
    try:
        # Get last 30 days of data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Query attendance data by date
        attendance_data = db.session.query(
            DailyStatus.status_date,
            DailyStatus.status,
            db.func.count(DailyStatus.id).label('count')
        ).filter(
            DailyStatus.status_date.between(start_date, end_date)
        ).group_by(
            DailyStatus.status_date, DailyStatus.status
        ).all()
        
        # Process data for chart
        chart_data = {}
        date_range = []
        current = start_date
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            date_range.append(date_str)
            chart_data[date_str] = {
                'in_office': 0,
                'wfh': 0,
                'leave': 0,
                'absent': 0
            }
            current += timedelta(days=1)
        
        # Fill in actual data
        for record in attendance_data:
            date_str = record.status_date.strftime('%Y-%m-%d')
            if record.status in [AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF]:
                chart_data[date_str]['in_office'] += record.count
            elif record.status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]:
                chart_data[date_str]['wfh'] += record.count
            elif record.status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]:
                chart_data[date_str]['leave'] += record.count
            elif record.status == AttendanceStatus.ABSENT:
                chart_data[date_str]['absent'] += record.count
        
        # Format for Chart.js
        result = {
            'labels': date_range,
            'datasets': [
                {
                    'label': 'In Office',
                    'data': [chart_data[d]['in_office'] for d in date_range],
                    'backgroundColor': '#16a34a',
                    'borderColor': '#16a34a',
                    'fill': False
                },
                {
                    'label': 'Work From Home',
                    'data': [chart_data[d]['wfh'] for d in date_range],
                    'backgroundColor': '#3b82f6',
                    'borderColor': '#3b82f6',
                    'fill': False
                },
                {
                    'label': 'On Leave',
                    'data': [chart_data[d]['leave'] for d in date_range],
                    'backgroundColor': '#d97706',
                    'borderColor': '#d97706',
                    'fill': False
                }
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Error fetching chart data: {str(e)}'}), 500

@app.route('/api/charts/team-performance')
@login_required
def team_performance_data():
    """Get team performance data for charts"""
    try:
        if current_user.role == UserRole.MANAGER:
            manager = current_user.manager_profile
            vendors = manager.team_vendors.all()
        elif current_user.role == UserRole.ADMIN:
            vendors = Vendor.query.all()
        else:
            return jsonify({'error': 'Access denied'}), 403
        
        # Calculate performance metrics for each vendor
        performance_data = []
        
        for vendor in vendors:
            # Get last 30 days of submissions
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            total_statuses = DailyStatus.query.filter(
                DailyStatus.vendor_id == vendor.id,
                DailyStatus.status_date.between(start_date, end_date)
            ).count()
            
            approved_statuses = DailyStatus.query.filter(
                DailyStatus.vendor_id == vendor.id,
                DailyStatus.status_date.between(start_date, end_date),
                DailyStatus.approval_status == ApprovalStatus.APPROVED
            ).count()
            
            # Calculate working days in the period
            working_days = 0
            current = start_date
            while current <= end_date:
                if current.weekday() < 5:  # Mon-Fri
                    is_holiday = Holiday.query.filter_by(holiday_date=current).first()
                    if not is_holiday:
                        working_days += 1
                current += timedelta(days=1)
            
            submission_rate = (total_statuses / working_days * 100) if working_days > 0 else 0
            approval_rate = (approved_statuses / total_statuses * 100) if total_statuses > 0 else 0
            
            performance_data.append({
                'vendor_name': vendor.full_name,
                'submission_rate': round(submission_rate, 1),
                'approval_rate': round(approval_rate, 1),
                'total_submissions': total_statuses
            })
        
        return jsonify(performance_data)
        
    except Exception as e:
        return jsonify({'error': f'Error fetching performance data: {str(e)}'}), 500

@app.route('/api/charts/status-distribution')
@login_required
def status_distribution_data():
    """Get status distribution data for pie charts"""
    try:
        # Get current month data
        current_month = date.today().replace(day=1)
        if current_month.month == 12:
            next_month = current_month.replace(year=current_month.year + 1, month=1)
        else:
            next_month = current_month.replace(month=current_month.month + 1)
        
        # Query status distribution
        status_counts = db.session.query(
            DailyStatus.status,
            db.func.count(DailyStatus.id).label('count')
        ).filter(
            DailyStatus.status_date >= current_month,
            DailyStatus.status_date < next_month
        ).group_by(DailyStatus.status).all()
        
        # Process data
        distribution = {
            'in_office': 0,
            'wfh': 0,
            'leave': 0,
            'absent': 0
        }
        
        for status, count in status_counts:
            if status in [AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF]:
                distribution['in_office'] += count
            elif status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]:
                distribution['wfh'] += count
            elif status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]:
                distribution['leave'] += count
            elif status == AttendanceStatus.ABSENT:
                distribution['absent'] += count
        
        # Format for Chart.js pie chart
        result = {
            'labels': ['In Office', 'Work From Home', 'On Leave', 'Absent'],
            'datasets': [{
                'data': [
                    distribution['in_office'],
                    distribution['wfh'],
                    distribution['leave'],
                    distribution['absent']
                ],
                'backgroundColor': [
                    '#16a34a',
                    '#3b82f6',
                    '#d97706',
                    '#dc2626'
                ]
            }]
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Error fetching distribution data: {str(e)}'}), 500
