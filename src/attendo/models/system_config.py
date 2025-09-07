"""
System Configuration Model

Contains the SystemConfiguration model for system settings.
"""

from datetime import datetime
from . import db


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
