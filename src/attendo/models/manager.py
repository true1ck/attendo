"""
Manager Model

Contains the Manager model for team management.
"""

from datetime import datetime
from . import db


class Manager(db.Model):
    """Manager profile to manage vendor teams"""
    __tablename__ = 'managers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    team_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    team_vendors = db.relationship('Vendor', backref='manager', lazy='dynamic')
    
    def __repr__(self):
        return f'<Manager {self.full_name}>'
