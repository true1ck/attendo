"""
WFH Record Model

Contains the WFHRecord model for work from home tracking.
"""

from datetime import datetime
from . import db


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
