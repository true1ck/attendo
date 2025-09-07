"""
Notification Model

Contains the NotificationLog model for notification tracking.
"""

from datetime import datetime
from . import db


class NotificationLog(db.Model):
    """Log of all notifications sent"""
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<NotificationLog {self.recipient_id} - {self.notification_type}>'
