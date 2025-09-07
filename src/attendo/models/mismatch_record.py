"""
Mismatch Record Model

Contains the MismatchRecord model for attendance reconciliation.
"""

from datetime import datetime
from . import db
from .attendance import AttendanceStatus, ApprovalStatus


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

    # Relationship
    vendor = db.relationship('Vendor', backref='mismatch_records')
    
    def __repr__(self):
        return f'<MismatchRecord {self.vendor.vendor_id} - {self.mismatch_date}>'
