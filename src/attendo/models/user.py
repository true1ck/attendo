"""
User Model

Contains User model and related enumerations for authentication and user management.
"""

import enum
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db


class UserRole(enum.Enum):
    """User role enumeration"""
    VENDOR = "vendor"
    MANAGER = "manager"
    ADMIN = "admin"


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
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
