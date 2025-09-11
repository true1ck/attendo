from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import enum

from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# Initialize db
db = SQLAlchemy()

class UserRole(enum.Enum):
    VENDOR = "vendor"
    MANAGER = "manager"
    ADMIN = "admin"

class AttendanceStatus(enum.Enum):
    IN_OFFICE_FULL = "in_office_full"
    IN_OFFICE_HALF = "in_office_half"
    WFH_FULL = "wfh_full"
    WFH_HALF = "wfh_half"
    LEAVE_FULL = "leave_full"
    LEAVE_HALF = "leave_half"
    ABSENT = "absent"

class HalfDayType(enum.Enum):
    IN_OFFICE = "in_office"
    WFH = "wfh"
    LEAVE = "leave"
    ABSENT = "absent"

class ApprovalStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class User(UserMixin, db.Model):
    """User model for authentication and basic user info"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    vendor_profile = db.relationship('Vendor', backref='user_account', uselist=False)
    manager_profile = db.relationship('Manager', backref='user_account', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Vendor(db.Model):
    """Vendor profile with company and department information"""
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vendor_id = db.Column(db.String(50), unique=True, nullable=False)  # Employee ID like "Otsoxx"
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)  # MTB_WCS_MSE7_MS1
    company = db.Column(db.String(100), nullable=False)  # ABC Solutions
    band = db.Column(db.String(10), nullable=False)  # B2, B3, etc.
    location = db.Column(db.String(50), nullable=False)  # BL-A-5F
    manager_id = db.Column(db.String(50), db.ForeignKey('managers.manager_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    daily_statuses = db.relationship('DailyStatus', backref='vendor', lazy='dynamic')
    swipe_records = db.relationship('SwipeRecord', backref='vendor', lazy='dynamic')
    mismatch_records = db.relationship('MismatchRecord', backref='vendor', lazy='dynamic')
    leave_records = db.relationship('LeaveRecord', backref='vendor', lazy='dynamic')
    wfh_records = db.relationship('WFHRecord', backref='vendor', lazy='dynamic')
    
    def __repr__(self):
        return f'<Vendor {self.vendor_id} - {self.full_name}>'

class Manager(db.Model):
    """Manager profile to manage vendor teams"""
    __tablename__ = 'managers'
    
    id = db.Column(db.Integer, primary_key=True)
    manager_id = db.Column(db.String(50), unique=True, nullable=False)  # Manager ID like M001, M002
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    team_name = db.Column(db.String(100))
    email = db.Column(db.String(120))  # For notifications
    phone = db.Column(db.String(20))   # For SMS notifications
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    team_vendors = db.relationship('Vendor', backref='manager', lazy='dynamic')
    
    def __repr__(self):
        return f'<Manager {self.full_name}>'

class DailyStatus(db.Model):
    """Daily attendance status submitted by vendors"""
    __tablename__ = 'daily_statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    status_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(AttendanceStatus), nullable=False)
    location = db.Column(db.String(100))  # Office/Home/Other
    comments = db.Column(db.Text)
    
    # Time tracking fields
    in_time = db.Column(db.Time, nullable=True)  # Start time for the day
    out_time = db.Column(db.Time, nullable=True)  # End time for the day
    office_in_time = db.Column(db.Time, nullable=True)  # For half-day office timing
    office_out_time = db.Column(db.Time, nullable=True)  # For half-day office timing
    wfh_in_time = db.Column(db.Time, nullable=True)  # For half-day WFH timing
    wfh_out_time = db.Column(db.Time, nullable=True)  # For half-day WFH timing
    break_duration = db.Column(db.Integer, default=0)  # Break duration in minutes
    total_hours = db.Column(db.Float, nullable=True)  # Calculated total hours
    extra_hours = db.Column(db.Float, nullable=True)  # Extra/overtime hours
    
    # Half-day type columns (nullable for backward compatibility)
    half_am_type = db.Column(db.Enum(HalfDayType), nullable=True)  # AM half-day type
    half_pm_type = db.Column(db.Enum(HalfDayType), nullable=True)  # PM half-day type
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    approval_status = db.Column(db.Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    manager_comments = db.Column(db.Text)
    
    # Index for efficient queries
    __table_args__ = (db.Index('idx_vendor_date', 'vendor_id', 'status_date'),)
    
    def is_half_day(self):
        """Check if this is a half-day status"""
        return self.status in [AttendanceStatus.IN_OFFICE_HALF, AttendanceStatus.WFH_HALF, AttendanceStatus.LEAVE_HALF]
    
    def has_half_day_details(self):
        """Check if half-day details are provided"""
        return self.half_am_type is not None and self.half_pm_type is not None
    
    def get_half_day_description(self):
        """Get human readable half-day description"""
        if not self.has_half_day_details():
            return None
        return f"AM: {self.half_am_type.value.replace('_', ' ').title()}, PM: {self.half_pm_type.value.replace('_', ' ').title()}"
    
    def __repr__(self):
        return f'<DailyStatus {self.vendor.vendor_id} - {self.status_date} - {self.status.value}>'

class SwipeRecord(db.Model):
    """Attendance swipe machine records for reconciliation"""
    __tablename__ = 'swipe_records'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    weekday = db.Column(db.String(20))
    shift_code = db.Column(db.String(10))  # G, A, etc.
    login_time = db.Column(db.Time)
    logout_time = db.Column(db.Time)
    total_hours = db.Column(db.Float)
    extra_hours = db.Column(db.Float)  # Extra/Overtime hours
    attendance_status = db.Column(db.String(10))  # AP (Present), AA (Absent)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.Index('idx_vendor_swipe_date', 'vendor_id', 'attendance_date'),)
    
    def __repr__(self):
        return f'<SwipeRecord {self.vendor.vendor_id} - {self.attendance_date}>'

class Holiday(db.Model):
    """Holiday configuration"""
    __tablename__ = 'holidays'
    
    id = db.Column(db.Integer, primary_key=True)
    holiday_date = db.Column(db.Date, nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Holiday {self.holiday_date} - {self.name}>'

class MismatchRecord(db.Model):
    """Records for reconciliation mismatches between web status and swipe data"""
    __tablename__ = 'mismatch_records'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    mismatch_date = db.Column(db.Date, nullable=False)
    web_status = db.Column(db.Enum(AttendanceStatus))
    swipe_status = db.Column(db.String(20))
    vendor_reason = db.Column(db.Text)
    vendor_submitted_at = db.Column(db.DateTime)
    manager_approval = db.Column(db.Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    manager_comments = db.Column(db.Text)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Detailed mismatch information stored as JSON
    mismatch_details = db.Column(db.Text, nullable=True)  # JSON string with detailed mismatch info
    
    def set_mismatch_details(self, details_dict):
        """Set mismatch details from dictionary"""
        import json
        self.mismatch_details = json.dumps(details_dict) if details_dict else None
    
    def get_mismatch_details(self):
        """Get mismatch details as dictionary"""
        import json
        if self.mismatch_details:
            try:
                return json.loads(self.mismatch_details)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def get_mismatch_summary(self):
        """Get a human-readable summary of mismatches"""
        details = self.get_mismatch_details()
        if not details:
            return "No detailed mismatch information available"
        
        summary = []
        if 'am_mismatch' in details:
            summary.append(f"AM: {details['am_mismatch']['reason']}")
        if 'pm_mismatch' in details:
            summary.append(f"PM: {details['pm_mismatch']['reason']}")
        if 'full_day_mismatch' in details:
            summary.append(f"Full Day: {details['full_day_mismatch']['reason']}")
            
        return "; ".join(summary) if summary else "No specific mismatches"
    
    def __repr__(self):
        return f'<MismatchRecord {self.vendor.vendor_id} - {self.mismatch_date}>'

class NotificationLog(db.Model):
    """Log of all notifications sent"""
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # reminder, summary, mismatch
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<NotificationLog {self.recipient_id} - {self.notification_type}>'

class AuditLog(db.Model):
    """Comprehensive audit trail for all system actions"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # CREATE, UPDATE, DELETE, APPROVE, REJECT
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON string
    new_values = db.Column(db.Text)  # JSON string
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AuditLog {self.user_id} - {self.action} - {self.table_name}>'

class SystemConfiguration(db.Model):
    """System configuration settings"""
    __tablename__ = 'system_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemConfiguration {self.key}: {self.value}>'

class LeaveRecord(db.Model):
    """Leave records imported from external systems"""
    __tablename__ = 'leave_records'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # Earned Leave, Sick Leave, etc.
    total_days = db.Column(db.Float, nullable=False)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LeaveRecord {self.vendor.vendor_id} - {self.start_date} to {self.end_date}>'

class WFHRecord(db.Model):
    """Work From Home records imported from external systems"""
    __tablename__ = 'wfh_records'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WFHRecord {self.vendor.vendor_id} - {self.start_date} to {self.end_date}>'

class EmailNotificationLog(db.Model):
    """Log of email notifications sent to managers"""
    __tablename__ = 'email_notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    manager_id = db.Column(db.String(50), db.ForeignKey('managers.manager_id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # PENDING_SUMMARY, COMPLETE_SUMMARY, URGENT_REMINDER, SMS_ALERT, etc.
    recipient = db.Column(db.String(120), nullable=False)  # Email or phone number
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # SENT, FAILED
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailNotificationLog {self.manager_id} - {self.notification_type} - {self.status}>'

# Import SystemIssue model from system_issues.py
try:
    from system_issues import SystemIssue, SystemIssueManager, IssueType, IssueSeverity
    from system_issues import report_api_failure, report_database_error, report_excel_sync_error, report_service_down
except ImportError:
    pass  # SystemIssue will be defined elsewhere or not available
