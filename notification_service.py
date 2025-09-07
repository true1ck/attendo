from datetime import datetime, timedelta, time
import schedule
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import requests
from models import db, Manager, Vendor, DailyStatus, EmailNotificationLog
import threading
import time as time_module

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling automated notifications to managers"""
    
    def __init__(self, app=None):
        self.app = app
        self.smtp_server = None
        self.smtp_port = 587
        self.smtp_user = None
        self.smtp_password = None
        self.sms_api_url = None
        self.sms_api_key = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the notification service with Flask app config"""
        self.app = app
        self.smtp_server = app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = app.config.get('SMTP_PORT', 587)
        self.smtp_user = app.config.get('SMTP_USER')
        self.smtp_password = app.config.get('SMTP_PASSWORD')
        self.sms_api_url = app.config.get('SMS_API_URL')
        self.sms_api_key = app.config.get('SMS_API_KEY')
        
        logger.info(f"NotificationService initialized with SMTP: {self.smtp_server}:{self.smtp_port}")
    
    def get_pending_submissions_summary(self, today=None):
        """Get summary of pending submissions for today by manager"""
        if today is None:
            today = datetime.now().date()
        
        # Get all managers and their vendors
        managers = Manager.query.all()
        summary = {}
        
        for manager in managers:
            # Get all vendors under this manager
            vendors = Vendor.query.filter_by(manager_id=manager.manager_id).all()
            
            if not vendors:
                continue
            
            vendor_ids = [v.vendor_id for v in vendors]
            
            # Count submitted and pending for today
            submitted_count = DailyStatus.query.filter(
                DailyStatus.vendor_id.in_(vendor_ids),
                DailyStatus.status_date == today
            ).count()
            
            total_vendors = len(vendors)
            pending_count = total_vendors - submitted_count
            
            # Get list of pending vendors
            submitted_vendor_ids = db.session.query(DailyStatus.vendor_id).filter(
                DailyStatus.vendor_id.in_(vendor_ids),
                DailyStatus.status_date == today
            ).all()
            submitted_vendor_ids = [vid[0] for vid in submitted_vendor_ids]
            
            pending_vendors = [v for v in vendors if v.vendor_id not in submitted_vendor_ids]
            
            summary[manager.manager_id] = {
                'manager': manager,
                'total_vendors': total_vendors,
                'submitted_count': submitted_count,
                'pending_count': pending_count,
                'pending_vendors': pending_vendors,
                'completion_rate': round((submitted_count / total_vendors) * 100, 1) if total_vendors > 0 else 0
            }
        
        return summary
    
    def send_email_notification(self, to_email, subject, body, is_html=True):
        """Send email notification"""
        try:
            if not self.smtp_user or not self.smtp_password:
                logger.warning("SMTP credentials not configured. Skipping email.")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect and send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.smtp_user, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_sms_notification(self, phone_number, message):
        """Send SMS notification using external API"""
        try:
            if not self.sms_api_url or not self.sms_api_key:
                logger.warning("SMS API not configured. Skipping SMS.")
                return False
            
            payload = {
                'apikey': self.sms_api_key,
                'numbers': phone_number,
                'message': message,
                'sender': 'VendorTrack'
            }
            
            response = requests.post(self.sms_api_url, data=payload)
            
            if response.status_code == 200:
                logger.info(f"SMS sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"SMS API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            return False
    
    def log_notification(self, manager_id, notification_type, message, status, recipient=None):
        """Log notification attempt to database"""
        try:
            log_entry = EmailNotificationLog(
                manager_id=manager_id,
                notification_type=notification_type,
                recipient=recipient,
                message=message[:500],  # Truncate if too long
                status=status,
                sent_at=datetime.utcnow()
            )
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")
    
    def generate_summary_email_body(self, manager_name, team_name, summary_data):
        """Generate HTML email body for daily summary"""
        completion_rate = summary_data['completion_rate']
        submitted_count = summary_data['submitted_count']
        pending_count = summary_data['pending_count']
        total_vendors = summary_data['total_vendors']
        pending_vendors = summary_data['pending_vendors']
        
        # Determine status color
        if completion_rate >= 100:
            status_color = "#28a745"  # Green
            status_text = "All Complete!"
        elif completion_rate >= 80:
            status_color = "#ffc107"  # Yellow
            status_text = "Nearly Complete"
        else:
            status_color = "#dc3545"  # Red
            status_text = "Action Required"
        
        # Build pending vendors list
        pending_list = ""
        if pending_vendors:
            for vendor in pending_vendors[:10]:  # Limit to 10 for email readability
                pending_list += f"""
                    <li style="margin-bottom: 8px;">
                        <strong>{vendor.full_name}</strong> ({vendor.vendor_id})
                        <br><small style="color: #6c757d;">{vendor.department} - {vendor.company}</small>
                    </li>
                """
            if len(pending_vendors) > 10:
                pending_list += f"<li><em>... and {len(pending_vendors) - 10} more</em></li>"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Daily Attendance Summary</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #4e73df 0%, #224abe 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                    <h1 style="margin: 0; font-size: 24px;">Daily Attendance Summary</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">{team_name} Team</p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.8;">{datetime.now().strftime('%A, %B %d, %Y')}</p>
                </div>
                
                <div style="background: white; border: 1px solid #dee2e6; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                    <h2 style="color: #4e73df; margin-top: 0;">Hello {manager_name},</h2>
                    <p>Here's your team's attendance submission status for today:</p>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <div style="width: 60px; height: 60px; border-radius: 50%; background: {status_color}; color: white; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; margin-right: 20px;">
                                {completion_rate}%
                            </div>
                            <div>
                                <h3 style="margin: 0; color: {status_color};">{status_text}</h3>
                                <p style="margin: 5px 0 0 0; color: #6c757d;">
                                    {submitted_count} of {total_vendors} submissions received
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin: 20px 0;">
                        <div style="text-align: center; padding: 15px; background: #e8f5e8; border-radius: 8px;">
                            <div style="font-size: 24px; font-weight: bold; color: #28a745;">{submitted_count}</div>
                            <div style="font-size: 12px; color: #6c757d;">SUBMITTED</div>
                        </div>
                        <div style="text-align: center; padding: 15px; background: #fff3cd; border-radius: 8px;">
                            <div style="font-size: 24px; font-weight: bold; color: #ffc107;">{pending_count}</div>
                            <div style="font-size: 12px; color: #6c757d;">PENDING</div>
                        </div>
                        <div style="text-align: center; padding: 15px; background: #e2e6ea; border-radius: 8px;">
                            <div style="font-size: 24px; font-weight: bold; color: #6c757d;">{total_vendors}</div>
                            <div style="font-size: 12px; color: #6c757d;">TOTAL TEAM</div>
                        </div>
                    </div>
        """
        
        if pending_vendors:
            html_body += f"""
                    <div style="margin: 20px 0;">
                        <h3 style="color: #dc3545; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">
                            <i style="margin-right: 5px;">⚠️</i> Pending Submissions
                        </h3>
                        <ul style="list-style: none; padding: 0;">
                            {pending_list}
                        </ul>
                    </div>
            """
        
        html_body += f"""
                    <div style="margin: 30px 0; text-align: center;">
                        <a href="{self.app.config.get('BASE_URL', '')}/manager/dashboard" 
                           style="background: #4e73df; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; display: inline-block; font-weight: bold;">
                            View Manager Dashboard
                        </a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                    <p style="font-size: 12px; color: #6c757d; text-align: center;">
                        This is an automated notification from the Vendor Timesheet Management System.<br>
                        Time sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def send_daily_summary_notifications(self, notification_time="12:00"):
        """Send daily summary notifications to all managers"""
        logger.info(f"Starting daily summary notifications at {notification_time}")
        
        try:
            with self.app.app_context():
                summary_data = self.get_pending_submissions_summary()
                
                for manager_id, data in summary_data.items():
                    manager = data['manager']
                    
                    # Skip if no email configured
                    if not manager.email:
                        logger.warning(f"No email configured for manager {manager.full_name}")
                        continue
                    
                    # Determine notification type based on completion
                    if data['completion_rate'] >= 100:
                        subject = f"✅ All Team Submissions Complete - {data['manager'].team_name}"
                        notification_type = "COMPLETE_SUMMARY"
                    else:
                        subject = f"⚠️ Daily Attendance Summary - {data['pending_count']} Pending - {data['manager'].team_name}"
                        notification_type = "PENDING_SUMMARY"
                    
                    # Generate email body
                    email_body = self.generate_summary_email_body(
                        manager.full_name,
                        manager.team_name,
                        data
                    )
                    
                    # Send email
                    success = self.send_email_notification(
                        manager.email,
                        subject,
                        email_body,
                        is_html=True
                    )
                    
                    # Log notification
                    status = "SENT" if success else "FAILED"
                    self.log_notification(
                        manager_id,
                        notification_type,
                        subject,
                        status,
                        manager.email
                    )
                    
                    # Send SMS if configured and pending count > 0
                    if manager.phone and data['pending_count'] > 0:
                        sms_message = f"VendorTrack Alert: {data['pending_count']} attendance submissions pending for {manager.team_name} team. Check dashboard for details."
                        sms_success = self.send_sms_notification(manager.phone, sms_message)
                        
                        # Log SMS
                        self.log_notification(
                            manager_id,
                            "SMS_ALERT",
                            sms_message,
                            "SENT" if sms_success else "FAILED",
                            manager.phone
                        )
                
                logger.info("Daily summary notifications completed")
                
        except Exception as e:
            logger.error(f"Error in send_daily_summary_notifications: {str(e)}")
    
    def send_urgent_reminder_notifications(self):
        """Send urgent reminder notifications (2 PM)"""
        logger.info("Starting urgent reminder notifications at 2:00 PM")
        
        try:
            with self.app.app_context():
                summary_data = self.get_pending_submissions_summary()
                
                for manager_id, data in summary_data.items():
                    manager = data['manager']
                    
                    # Only send urgent reminders if there are pending submissions
                    if data['pending_count'] == 0:
                        continue
                    
                    if not manager.email:
                        continue
                    
                    subject = f"🚨 URGENT: {data['pending_count']} Attendance Submissions Still Pending - {manager.team_name}"
                    
                    # Generate urgent email body
                    email_body = self.generate_urgent_email_body(
                        manager.full_name,
                        manager.team_name,
                        data
                    )
                    
                    # Send email
                    success = self.send_email_notification(
                        manager.email,
                        subject,
                        email_body,
                        is_html=True
                    )
                    
                    # Log notification
                    status = "SENT" if success else "FAILED"
                    self.log_notification(
                        manager_id,
                        "URGENT_REMINDER",
                        subject,
                        status,
                        manager.email
                    )
                    
                    # Always send SMS for urgent reminders if phone available
                    if manager.phone:
                        sms_message = f"URGENT: {data['pending_count']} attendance submissions still pending for {manager.team_name}. Please follow up immediately."
                        sms_success = self.send_sms_notification(manager.phone, sms_message)
                        
                        self.log_notification(
                            manager_id,
                            "URGENT_SMS",
                            sms_message,
                            "SENT" if sms_success else "FAILED",
                            manager.phone
                        )
                
                logger.info("Urgent reminder notifications completed")
                
        except Exception as e:
            logger.error(f"Error in send_urgent_reminder_notifications: {str(e)}")
    
    def generate_urgent_email_body(self, manager_name, team_name, summary_data):
        """Generate HTML email body for urgent reminders"""
        pending_count = summary_data['pending_count']
        pending_vendors = summary_data['pending_vendors']
        
        pending_list = ""
        for vendor in pending_vendors:
            pending_list += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #dee2e6;">{vendor.full_name}</td>
                    <td style="padding: 8px; border: 1px solid #dee2e6;">{vendor.vendor_id}</td>
                    <td style="padding: 8px; border: 1px solid #dee2e6;">{vendor.department}</td>
                    <td style="padding: 8px; border: 1px solid #dee2e6;">{vendor.company}</td>
                </tr>
            """
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Urgent Attendance Reminder</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #dc3545 0%, #bd2130 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                    <h1 style="margin: 0; font-size: 24px;">🚨 URGENT REMINDER</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Attendance Submissions Pending</p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">{datetime.now().strftime('%A, %B %d, %Y - %H:%M')}</p>
                </div>
                
                <div style="background: white; border: 2px solid #dc3545; border-radius: 10px; padding: 20px;">
                    <h2 style="color: #dc3545; margin-top: 0;">Dear {manager_name},</h2>
                    <p style="font-size: 16px; color: #dc3545; font-weight: bold;">
                        ⚠️ You have {pending_count} team members who have not submitted their attendance for today.
                    </p>
                    <p>As we approach the end of the business day, please follow up with the following team members immediately:</p>
                    
                    <div style="margin: 20px 0;">
                        <h3 style="color: #dc3545;">Pending Submissions:</h3>
                        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                            <thead>
                                <tr style="background: #f8f9fa;">
                                    <th style="padding: 10px; border: 1px solid #dee2e6; text-align: left;">Name</th>
                                    <th style="padding: 10px; border: 1px solid #dee2e6; text-align: left;">Vendor ID</th>
                                    <th style="padding: 10px; border: 1px solid #dee2e6; text-align: left;">Department</th>
                                    <th style="padding: 10px; border: 1px solid #dee2e6; text-align: left;">Company</th>
                                </tr>
                            </thead>
                            <tbody>
                                {pending_list}
                            </tbody>
                        </table>
                    </div>
                    
                    <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 15px; margin: 20px 0;">
                        <strong style="color: #856404;">Action Required:</strong>
                        <ul style="margin: 10px 0; color: #856404;">
                            <li>Contact the above team members immediately</li>
                            <li>Remind them to submit their daily attendance status</li>
                            <li>Check for any technical issues preventing submission</li>
                            <li>Ensure 100% compliance by end of day</li>
                        </ul>
                    </div>
                    
                    <div style="margin: 30px 0; text-align: center;">
                        <a href="{self.app.config.get('BASE_URL', '')}/manager/dashboard" 
                           style="background: #dc3545; color: white; text-decoration: none; padding: 15px 40px; border-radius: 5px; display: inline-block; font-weight: bold; font-size: 16px;">
                            Take Action Now
                        </a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_body


# Scheduler setup
def setup_notification_scheduler(app, notification_service):
    """Setup scheduled tasks for notifications"""
    
    def run_12pm_notifications():
        notification_service.send_daily_summary_notifications("12:00")
    
    def run_2pm_notifications():
        notification_service.send_urgent_reminder_notifications()
    
    # Schedule notifications
    schedule.every().day.at("12:00").do(run_12pm_notifications)
    schedule.every().day.at("14:00").do(run_2pm_notifications)
    
    def run_scheduler():
        """Run scheduled tasks in a separate thread"""
        while True:
            schedule.run_pending()
            time_module.sleep(60)  # Check every minute
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Notification scheduler setup completed - notifications at 12:00 PM and 2:00 PM")


# Create notification service instance
notification_service = NotificationService()
