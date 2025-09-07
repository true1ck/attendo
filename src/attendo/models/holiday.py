"""
Holiday Model

Contains the Holiday model for holiday management.
"""

from datetime import datetime
from . import db


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
