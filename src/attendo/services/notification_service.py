"""
Notification Service

Handles automated notifications and reminders for the ATTENDO system.
"""

from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
import atexit


def start_notification_scheduler():
    """Start the background notification scheduler"""
    scheduler = BackgroundScheduler()
    
    # Schedule daily reminder at 9:00 AM
    scheduler.add_job(
        func=send_daily_reminders,
        trigger="cron", 
        hour=9, 
        minute=0,
        id='daily_reminders'
    )
    
    # Schedule weekly summary on Friday at 5:00 PM
    scheduler.add_job(
        func=send_weekly_summary,
        trigger="cron",
        day_of_week=4,  # Friday
        hour=17,
        minute=0,
        id='weekly_summary'
    )
    
    scheduler.start()
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())


def send_daily_reminders():
    """Send daily attendance reminders to vendors"""
    from ..models import NotificationLog, User, Vendor
    from ..models.user import UserRole
    from datetime import date
    
    # Get all vendors who haven't submitted today's status
    today = date.today()
    vendors_without_status = []  # This would be populated from database query
    
    for vendor in vendors_without_status:
        message = f"Hi {vendor.full_name}! Don't forget to submit your attendance status for today ({today})."
        
        notification = NotificationLog(
            recipient_id=vendor.user_id,
            notification_type='reminder',
            message=message
        )
        
        # Save to database (would need db session here)
        print(f"Sending reminder to {vendor.full_name}: {message}")


def send_weekly_summary():
    """Send weekly summary to managers"""
    from ..models import NotificationLog, Manager
    
    managers = []  # This would be populated from database query
    
    for manager in managers:
        message = f"Weekly attendance summary for your team is ready. Please review pending approvals."
        
        notification = NotificationLog(
            recipient_id=manager.user_id,
            notification_type='summary',
            message=message
        )
        
        # Save to database (would need db session here)
        print(f"Sending weekly summary to {manager.full_name}: {message}")


def send_mismatch_alert(vendor_id, mismatch_date):
    """Send alert for attendance mismatch"""
    from ..models import NotificationLog, Vendor
    
    # This would get vendor from database
    message = f"Attendance mismatch detected for {mismatch_date}. Please provide explanation."
    
    notification = NotificationLog(
        recipient_id=vendor_id,
        notification_type='mismatch',
        message=message
    )
    
    # Save to database (would need db session here)
    print(f"Sending mismatch alert: {message}")
