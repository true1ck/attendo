"""
Swipe Record Model

Contains the SwipeRecord model for attendance machine data.
"""

from datetime import datetime
from . import db


class SwipeRecord(db.Model):
    """Attendance swipe machine records for reconciliation"""
    __tablename__ = 'swipe_records'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    weekday = db.Column(db.String(20))
    login_time = db.Column(db.Time)
    logout_time = db.Column(db.Time)
    total_hours = db.Column(db.Float)
    attendance_status = db.Column(db.String(10))  # AP (Present), AA (Absent)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.Index('idx_vendor_swipe_date', 'vendor_id', 'attendance_date'),)
    
    def __repr__(self):
        return f'<SwipeRecord {self.vendor.vendor_id} - {self.attendance_date}>'
