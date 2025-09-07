"""
Leave Record Model

Contains the LeaveRecord model for leave management.
"""

from datetime import datetime
from . import db


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
