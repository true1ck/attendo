"""
ATTENDO Models Package

This package contains all database models for the ATTENDO application.
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Import all models for easy access
from .user import User, UserRole
from .vendor import Vendor
from .manager import Manager
from .attendance import DailyStatus, AttendanceStatus, ApprovalStatus
from .swipe_record import SwipeRecord
from .holiday import Holiday
from .mismatch_record import MismatchRecord
from .notification import NotificationLog
from .audit import AuditLog
from .system_config import SystemConfiguration
from .leave_record import LeaveRecord
from .wfh_record import WFHRecord

__all__ = [
    'db',
    'User', 'UserRole',
    'Vendor',
    'Manager', 
    'DailyStatus', 'AttendanceStatus', 'ApprovalStatus',
    'SwipeRecord',
    'Holiday',
    'MismatchRecord',
    'NotificationLog',
    'AuditLog',
    'SystemConfiguration',
    'LeaveRecord',
    'WFHRecord'
]
