"""
Attendance Models

Contains attendance-related models and enumerations.
"""

import enum
from datetime import datetime
from . import db


class AttendanceStatus(enum.Enum):
    """Attendance status enumeration"""
    IN_OFFICE_FULL = "in_office_full"
    IN_OFFICE_HALF = "in_office_half"
    WFH_FULL = "wfh_full"
    WFH_HALF = "wfh_half"
    LEAVE_FULL = "leave_full"
    LEAVE_HALF = "leave_half"
    ABSENT = "absent"


class ApprovalStatus(enum.Enum):
    """Approval status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DailyStatus(db.Model):
    """Daily attendance status submitted by vendors"""
    __tablename__ = 'daily_statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    status_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(AttendanceStatus), nullable=False)
    location = db.Column(db.String(100))  # Office/Home/Other
    comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    approval_status = db.Column(db.Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    # Index for efficient queries
    __table_args__ = (db.Index('idx_vendor_date', 'vendor_id', 'status_date'),)
    
    def __repr__(self):
        return f'<DailyStatus {self.vendor.vendor_id} - {self.status_date} - {self.status.value}>'
