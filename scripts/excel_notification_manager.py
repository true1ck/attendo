#!/usr/bin/env python3
"""
Excel-based Notification Management System
Replaces the current hard-coded notification logic with configurable Excel sheets with table formatting.
Based on requirements from requirement_doc.html
"""

import pandas as pd
import os
import smtplib
from datetime import datetime, date, time, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests
import json
from typing import List, Dict, Optional, Any
from models import User, Vendor, Manager, DailyStatus, Holiday, UserRole, AttendanceStatus, ApprovalStatus
import models
from excel_table_formatter import update_notification_table, validate_notification_table

class ExcelNotificationManager:
    """Manages all notifications based on Excel configuration files"""
    
    def __init__(self, config_dir="notification_configs"):
        self.config_dir = config_dir
        self.notification_configs = {}
        self.load_all_configs()
    
    def load_all_configs(self):
        """Load all notification configurations from Excel files"""
        config_files = {
            'daily_reminders': '01_daily_status_reminders.xlsx',
            'manager_summary': '02_manager_summary_notifications.xlsx',
            'manager_complete': '03_manager_all_complete_notifications.xlsx',
            'mismatch_alerts': '04_mismatch_notifications.xlsx',
            'manager_feedback': '05_manager_feedback_notifications.xlsx',
            'monthly_reports': '06_monthly_report_notifications.xlsx',
            'admin_alerts': '07_admin_system_alerts.xlsx',
            'holiday_reminders': '08_holiday_reminder_notifications.xlsx',
            'late_submissions': '09_late_submission_alerts.xlsx',
            'billing_corrections': '10_billing_correction_notifications.xlsx'
        }
        
        for config_type, filename in config_files.items():
            filepath = os.path.join(self.config_dir, filename)
            if os.path.exists(filepath):
                try:
                    df = pd.read_excel(filepath)
                    self.notification_configs[config_type] = df
                    print(f"✅ Loaded {config_type} config: {len(df)} entries")
                except Exception as e:
                    print(f"❌ Error loading {config_type}: {e}")
            else:
                print(f"⚠️ Config file not found: {filepath}")
    
    def get_active_recipients(self, config_type: str, filters: Dict[str, Any] = None) -> List[Dict]:
        """Get active recipients for a notification type with optional filters"""
        if config_type not in self.notification_configs:
            print(f"❌ Configuration not found for: {config_type}")
            return []
        
        df = self.notification_configs[config_type]
        
        # Filter for active notifications only
        active_df = df[df['Send_Notification'] == 'YES']
        active_df = active_df[active_df['Active'] == 'YES']
        
        # Apply additional filters if provided
        if filters:
            for key, value in filters.items():
                if key in active_df.columns:
                    if isinstance(value, list):
                        active_df = active_df[active_df[key].isin(value)]
                    else:
                        active_df = active_df[active_df[key] == value]
        
        # Convert to list of dictionaries
        return active_df.to_dict('records')
    
    def send_teams_notification(self, webhook_url: str, message: str, title: str = "ATTENDO Notification"):
        """Send notification to Microsoft Teams"""
        try:
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": title,
                "themeColor": "0078D4",
                "title": title,
                "text": message,
                "potentialAction": [
                    {
                        "@type": "OpenUri",
                        "name": "Open ATTENDO",
                        "targets": [
                            {
                                "os": "default",
                                "uri": "http://localhost:5000"
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(webhook_url, data=json.dumps(payload), headers={
                'Content-Type': 'application/json'
            })
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Teams notification failed: {e}")
            return False
    
    def send_email_notification(self, recipient_email: str, subject: str, body: str, 
                              attachments: List[str] = None, is_html: bool = True):
        """Send email notification"""
        try:
            from flask import current_app
            
            smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = current_app.config.get('SMTP_PORT', 587)
            smtp_user = current_app.config.get('SMTP_USER')
            smtp_password = current_app.config.get('SMTP_PASSWORD')
            
            if not smtp_user or not smtp_password:
                print("⚠️ SMTP credentials not configured")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_user, recipient_email, text)
            server.quit()
            return True
            
        except Exception as e:
            print(f"❌ Email notification failed: {e}")
            return False
    
    def send_daily_status_reminders(self):
        """Send daily status reminders to vendors based on Excel configuration"""
        from utils import check_late_submissions
        
        # Get vendors who haven't submitted status
        late_vendors = check_late_submissions()
        
        if not late_vendors:
            print("✅ No late submissions to remind about")
            return
        
        # Get reminder configurations
        reminder_configs = self.get_active_recipients('daily_reminders')
        
        current_time = datetime.now()
        current_hour = current_time.hour
        
        for vendor in late_vendors:
            # Find config for this vendor
            vendor_config = None
            for config in reminder_configs:
                if config.get('Vendor_ID') == vendor.vendor_id:
                    vendor_config = config
                    break
            
            if not vendor_config:
                continue  # No config found for this vendor
            
            # Check timing constraints
            start_time = datetime.strptime(vendor_config.get('Start_Time', '09:00'), '%H:%M').time()
            end_time = datetime.strptime(vendor_config.get('End_Time', '18:00'), '%H:%M').time()
            current_time_only = current_time.time()
            
            if not (start_time <= current_time_only <= end_time):
                continue  # Outside notification hours
            
            # Check if weekdays only
            if vendor_config.get('Weekdays_Only') == 'YES' and current_time.weekday() >= 5:
                continue  # Weekend skip
            
            # Check holidays
            if vendor_config.get('Exclude_Holidays') == 'YES':
                if Holiday.query.filter_by(holiday_date=current_time.date()).first():
                    continue  # Holiday skip
            
            # Check reminder interval
            interval_hours = vendor_config.get('Reminder_Interval_Hours', 3)
            # Here you would check last reminder time from database
            
            # Prepare message
            custom_message = vendor_config.get('Custom_Message', '')
            if not custom_message:
                custom_message = f"Hi {vendor.full_name}, please submit your daily attendance status for {date.today().strftime('%B %d, %Y')}."
            
            message = f"""
🚨 **Daily Status Reminder**

{custom_message}

Please update your status:
• In Office (Full/Half Day)
• Work From Home (Full/Half Day)
• On Leave (Full/Half Day)

👉 [Submit Status Here](http://localhost:5000/vendor/dashboard)

This is an automated reminder from the ATTENDO system.
            """.strip()
            
            # Send notifications based on configured methods
            methods = vendor_config.get('Notification_Method', 'EMAIL').split(',')
            
            if 'EMAIL' in methods:
                self.send_email_notification(
                    recipient_email=vendor_config['Contact_Email'],
                    subject="ATTENDO: Daily Status Reminder",
                    body=message.replace('\n', '<br>'),
                    is_html=True
                )
            
            if 'TEAMS' in methods and vendor_config.get('Teams_Channel'):
                # In production, you would use the actual Teams webhook URL
                teams_webhook = f"https://teams.webhook.url/{vendor_config.get('Teams_Channel')}"
                self.send_teams_notification(teams_webhook, message, "Daily Status Reminder")
            
            print(f"✅ Sent reminder to {vendor.full_name}")
    
    def send_manager_summary_notifications(self):
        """Send manager summary notifications based on Excel configuration"""
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # Get manager summary configurations
        summary_configs = self.get_active_recipients('manager_summary')
        
        for config in summary_configs:
            # Check if current time matches notification times
            notification_times = config.get('Notification_Times', '12:00,14:00').split(',')
            current_time_str = f"{current_hour:02d}:00"
            
            if current_time_str not in [t.strip() for t in notification_times]:
                continue  # Not the right time
            
            # Check weekdays only
            if config.get('Weekdays_Only') == 'YES' and current_time.weekday() >= 5:
                continue
            
            # Check holidays
            if config.get('Exclude_Holidays') == 'YES':
                if Holiday.query.filter_by(holiday_date=current_time.date()).first():
                    continue
            
            # Get manager data
            manager_id = config.get('Manager_ID')
            if not manager_id:
                continue
            
            try:
                with models.db.session() as session:
                    manager = session.query(Manager).filter_by(manager_id=manager_id).first()
                    if not manager:
                        continue
                    
                    team_vendors = manager.team_vendors.all()
                    
                    # Calculate team statistics
                    today = date.today()
                    submitted_count = 0
                    pending_count = 0
                    approved_count = 0
                    team_status = []
                    
                    for vendor in team_vendors:
                        status = session.query(DailyStatus).filter_by(
                            vendor_id=vendor.id,
                            status_date=today
                        ).first()
                        
                        if status:
                            submitted_count += 1
                            if status.approval_status == ApprovalStatus.APPROVED:
                                approved_count += 1
                            elif status.approval_status == ApprovalStatus.PENDING:
                                pending_count += 1
                            
                            team_status.append(f"✅ {vendor.full_name}: {status.status.value.replace('_', ' ').title()}")
                        else:
                            team_status.append(f"❌ {vendor.full_name}: Not submitted")
                    
                    # Prepare message based on configuration options
                    message_parts = [f"📊 **Team Status Summary - {current_time_str}**", "", f"Hi {config['Contact_Name']},", ""]
                    
                    if config.get('Include_Team_Stats') == 'YES':
                        message_parts.extend([
                            f"**Team Size:** {len(team_vendors)}",
                            f"**Submitted:** {submitted_count}/{len(team_vendors)}",
                            f"**Approved:** {approved_count}",
                            ""
                        ])
                    
                    if config.get('Include_Pending_Count') == 'YES':
                        message_parts.append(f"**Pending Approval:** {pending_count}")
                        message_parts.append("")
                    
                    if config.get('Include_Individual_Status') == 'YES':
                        message_parts.extend(["**Individual Status:**"] + team_status + [""])
                    
                    message_parts.extend([
                        "👉 [Review Team Status](http://localhost:5000/manager/dashboard)",
                        "",
                        "This is an automated summary from the ATTENDO system."
                    ])
                    
                    custom_message = config.get('Custom_Message', '')
                    if custom_message:
                        message_parts.insert(4, custom_message)
                        message_parts.insert(5, "")
                    
                    message = "\n".join(message_parts)
                    
                    # Send notifications
                    methods = config.get('Notification_Method', 'EMAIL').split(',')
                    
                    if 'EMAIL' in methods:
                        self.send_email_notification(
                            recipient_email=config['Contact_Email'],
                            subject=f"ATTENDO: Team Status Summary - {current_time_str}",
                            body=message.replace('\n', '<br>'),
                            is_html=True
                        )
                    
                    if 'TEAMS' in methods and config.get('Teams_Channel'):
                        teams_webhook = f"https://teams.webhook.url/{config.get('Teams_Channel')}"
                        self.send_teams_notification(teams_webhook, message, "Team Status Summary")
                    
                    print(f"✅ Sent summary to manager {manager.full_name}")
                    
            except Exception as e:
                print(f"❌ Error processing manager {manager_id}: {e}")
    
    def send_mismatch_notifications(self, mismatches: List[Any]):
        """Send mismatch notifications based on Excel configuration"""
        if not mismatches:
            return
        
        # Get mismatch configurations
        mismatch_configs = self.get_active_recipients('mismatch_alerts')
        
        # Group mismatches by manager and vendor
        manager_mismatches = {}
        vendor_mismatches = {}
        
        for mismatch in mismatches:
            vendor = mismatch.vendor
            manager_id = vendor.manager_id
            
            if manager_id:
                if manager_id not in manager_mismatches:
                    manager_mismatches[manager_id] = []
                manager_mismatches[manager_id].append(mismatch)
            
            vendor_id = vendor.vendor_id
            if vendor_id not in vendor_mismatches:
                vendor_mismatches[vendor_id] = []
            vendor_mismatches[vendor_id].append(mismatch)
        
        # Send notifications to managers
        for manager_id, mgr_mismatches in manager_mismatches.items():
            for config in mismatch_configs:
                if config.get('Role') == 'MANAGER' and config.get('Manager_ID') == manager_id:
                    self._send_mismatch_notification_to_manager(config, mgr_mismatches)
                    break
        
        # Send notifications to vendors
        for vendor_id, vnd_mismatches in vendor_mismatches.items():
            for config in mismatch_configs:
                if config.get('Role') == 'VENDOR' and config.get('Vendor_ID') == vendor_id:
                    self._send_mismatch_notification_to_vendor(config, vnd_mismatches)
                    break
    
    def _send_mismatch_notification_to_manager(self, config: Dict, mismatches: List[Any]):
        """Send mismatch notification to a manager"""
        message_parts = [
            "🔍 **Attendance Mismatch Alert**",
            "",
            f"Hi {config['Contact_Name']},",
            "",
            f"New attendance mismatches detected for your team ({len(mismatches)} issues):",
            ""
        ]
        
        if config.get('Include_Vendor_Details') == 'YES':
            for mismatch in mismatches[:10]:  # Limit to 10 for readability
                vendor_name = mismatch.vendor.full_name
                mismatch_date = mismatch.mismatch_date.strftime('%Y-%m-%d')
                web_status = mismatch.web_status.value if mismatch.web_status else 'Not submitted'
                swipe_status = mismatch.swipe_status or 'No swipe'
                
                message_parts.append(f"• **{vendor_name}** ({mismatch_date}): Web={web_status}, Swipe={swipe_status}")
        
        if config.get('Include_Explanation_Required') == 'YES':
            message_parts.extend([
                "",
                "**Action Required:**",
                "• Review each mismatch with team members",
                "• Approve or reject vendor explanations",
                "• Update attendance records as needed"
            ])
        
        message_parts.extend([
            "",
            "👉 [Review Mismatches](http://localhost:5000/manager/mismatches)",
            "",
            custom_msg if (custom_msg := config.get('Custom_Message')) else "",
            "",
            "This is an automated alert from the ATTENDO system."
        ])
        
        message = "\n".join(filter(None, message_parts))
        
        # Send notification
        methods = config.get('Notification_Method', 'EMAIL').split(',')
        
        if 'EMAIL' in methods:
            self.send_email_notification(
                recipient_email=config['Contact_Email'],
                subject=f"ATTENDO: Attendance Mismatches - {len(mismatches)} Issues",
                body=message.replace('\n', '<br>'),
                is_html=True
            )
        
        if 'TEAMS' in methods and config.get('Teams_Channel'):
            teams_webhook = f"https://teams.webhook.url/{config.get('Teams_Channel')}"
            self.send_teams_notification(teams_webhook, message, "Attendance Mismatch Alert")
        
        print(f"✅ Sent mismatch alert to manager {config['Contact_Name']}")
    
    def _send_mismatch_notification_to_vendor(self, config: Dict, mismatches: List[Any]):
        """Send mismatch notification to a vendor"""
        message_parts = [
            "⚠️ **Attendance Mismatch - Action Required**",
            "",
            f"Hi {config['Contact_Name']},",
            "",
            "We found discrepancies in your attendance records that need your explanation:",
            ""
        ]
        
        for mismatch in mismatches:
            mismatch_date = mismatch.mismatch_date.strftime('%B %d, %Y')
            web_status = mismatch.web_status.value if mismatch.web_status else 'Not submitted'
            swipe_status = mismatch.swipe_status or 'No swipe record'
            
            message_parts.extend([
                f"**Date:** {mismatch_date}",
                f"**Your Submitted Status:** {web_status}",
                f"**Swipe Record:** {swipe_status}",
                ""
            ])
        
        message_parts.extend([
            "**Please provide an explanation for the discrepancy.**",
            "",
            "👉 [Explain Mismatch](http://localhost:5000/vendor/dashboard)",
            "",
            custom_msg if (custom_msg := config.get('Custom_Message')) else "",
            "",
            "This notification is from the ATTENDO system."
        ])
        
        message = "\n".join(filter(None, message_parts))
        
        # Send notification
        methods = config.get('Notification_Method', 'EMAIL').split(',')
        
        if 'EMAIL' in methods:
            self.send_email_notification(
                recipient_email=config['Contact_Email'],
                subject="ATTENDO: Attendance Mismatch - Explanation Required",
                body=message.replace('\n', '<br>'),
                is_html=True
            )
        
        print(f"✅ Sent mismatch notification to vendor {config['Contact_Name']}")
    
    def update_notification_config(self, config_type: str, primary_key: str, updates: Dict[str, Any]):
        """Update a specific notification configuration with proper table formatting"""
        if config_type not in self.notification_configs:
            return False
        
        df = self.notification_configs[config_type]
        mask = df['Primary_Key'] == primary_key
        
        if not mask.any():
            return False
        
        # Update the dataframe
        for key, value in updates.items():
            if key in df.columns:
                df.loc[mask, key] = value
        
        df.loc[mask, 'Last_Modified'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update the in-memory config
        self.notification_configs[config_type] = df
        
        # Save back to Excel with proper table formatting
        try:
            update_notification_table(df, config_type, backup=True)
            print(f"✅ Updated {config_type} config for {primary_key} with table format")
            return True
        except Exception as e:
            print(f"❌ Error updating {config_type} config: {str(e)}")
            return False
    
    def _get_config_filename(self, config_type: str) -> str:
        """Get filename for config type"""
        config_files = {
            'daily_reminders': '01_daily_status_reminders.xlsx',
            'manager_summary': '02_manager_summary_notifications.xlsx',
            'manager_complete': '03_manager_all_complete_notifications.xlsx',
            'mismatch_alerts': '04_mismatch_notifications.xlsx',
            'manager_feedback': '05_manager_feedback_notifications.xlsx',
            'monthly_reports': '06_monthly_report_notifications.xlsx',
            'admin_alerts': '07_admin_system_alerts.xlsx',
            'holiday_reminders': '08_holiday_reminder_notifications.xlsx',
            'late_submissions': '09_late_submission_alerts.xlsx',
            'billing_corrections': '10_billing_correction_notifications.xlsx'
        }
        return config_files.get(config_type, 'unknown.xlsx')

# Global instance
excel_notification_manager = ExcelNotificationManager()

def send_configured_daily_reminders():
    """Replacement for current daily reminder function"""
    excel_notification_manager.send_daily_status_reminders()

def send_configured_manager_notifications():
    """Replacement for current manager notification function"""
    excel_notification_manager.send_manager_summary_notifications()

def send_configured_mismatch_notifications(mismatches):
    """Replacement for current mismatch notification function"""
    excel_notification_manager.send_mismatch_notifications(mismatches)
