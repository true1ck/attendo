"""
Vendor Model

Contains the Vendor model for vendor profile management.
"""

from datetime import datetime
from . import db


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
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    daily_statuses = db.relationship('DailyStatus', backref='vendor', lazy='dynamic')
    swipe_records = db.relationship('SwipeRecord', backref='vendor', lazy='dynamic')
    
    def __repr__(self):
        return f'<Vendor {self.vendor_id} - {self.full_name}>'
