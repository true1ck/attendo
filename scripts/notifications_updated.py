from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date, time, timedelta
import atexit
from models import User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday, MismatchRecord, NotificationLog, AuditLog, SystemConfiguration, LeaveRecord, WFHRecord, UserRole, AttendanceStatus, ApprovalStatus
import models
from utils import check_late_submissions, send_notification, get_system_config

# Import the new Excel-based notification manager
from excel_notification_manager import (
    excel_notification_manager,
    send_configured_daily_reminders,
    send_configured_manager_notifications,
    send_configured_mismatch_notifications
)

# Import daily Excel updater for Power Automate accuracy
from daily_excel_updater import run_daily_reset

def start_notification_scheduler():
    """Start the background scheduler for notifications using Excel configuration"""
    scheduler = BackgroundScheduler()
    
    # 🆕 Schedule daily Excel reset at midnight (CRITICAL for Power Automate accuracy)
    scheduler.add_job(
        func=run_daily_excel_reset,
        trigger="cron",
        hour=0,  # Midnight
        minute=5,  # 5 minutes past midnight
        id='daily_excel_reset'
    )
    
    # Schedule daily reminders every hour (Excel config controls actual timing)
    scheduler.add_job(
        func=send_configured_daily_reminders,
        trigger="cron",
        hour='*',  # Run every hour, Excel config filters appropriate times
        minute=0,
        id='excel_daily_reminders'
    )
    
    # Schedule manager notifications every hour (Excel config controls timing)
    scheduler.add_job(
        func=send_configured_manager_notifications,
        trigger="cron",
        hour='*',  # Run every hour, Excel config determines 12 PM and 2 PM
        minute=0,
        id='excel_manager_notifications'
    )
    
    # Schedule end-of-day summary at 6 PM
    scheduler.add_job(
        func=send_end_of_day_summary,
        trigger="cron",
        hour=18,
        minute=0,
        id='end_of_day_summary'
    )
    
    # Schedule mismatch detection daily at 11 PM
    scheduler.add_job(
        func=run_mismatch_detection_with_notifications,
        trigger="cron",
        hour=23,
        minute=0,
        id='excel_mismatch_detection'
    )
    
    # Schedule holiday reminders
    scheduler.add_job(
        func=send_holiday_reminders,
        trigger="cron",
        hour=9,
        minute=0,
        id='holiday_reminders'
    )
    
    # Schedule monthly report notifications (1st of each month)
    scheduler.add_job(
        func=send_monthly_report_notifications,
        trigger="cron",
        day=1,
        hour=9,
        minute=0,
        id='monthly_report_notifications'
    )
    
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    
    print("✅ Excel-based notification scheduler started!")
    print("📊 Loaded notification configurations:")
    for config_type, df in excel_notification_manager.notification_configs.items():
        active_count = len(df[df['Send_Notification'] == 'YES'])
        print(f"   • {config_type}: {active_count} active recipients")
    
    return scheduler

def run_mismatch_detection_with_notifications():
    """Run mismatch detection and send notifications using Excel configuration"""
    try:
        from utils import detect_mismatches
        mismatches_found = detect_mismatches()
        
        if mismatches_found > 0:
            # Get recent mismatches to send notifications
            recent_mismatches = MismatchRecord.query.filter(
                MismatchRecord.created_at >= datetime.utcnow() - timedelta(hours=2)
            ).all()
            
            # Send notifications using Excel configuration
            send_configured_mismatch_notifications(recent_mismatches)
            
        print(f"✅ Mismatch detection completed: {mismatches_found} new issues found")
        
    except Exception as e:
        print(f"❌ Error in mismatch detection: {str(e)}")

def send_holiday_reminders():
    """Send holiday reminders based on Excel configuration"""
    try:
        # Get upcoming holidays (within 7 days)
        upcoming_holidays = Holiday.query.filter(
            Holiday.holiday_date > date.today(),
            Holiday.holiday_date <= date.today() + timedelta(days=7)
        ).all()
        
        if not upcoming_holidays:
            return
        
        # Get holiday reminder configurations
        holiday_configs = excel_notification_manager.get_active_recipients('holiday_reminders')
        
        for holiday in upcoming_holidays:
            days_until = (holiday.holiday_date - date.today()).days
            
            for config in holiday_configs:
                advance_notice_days = config.get('Advance_Notice_Days', 7)
                
                if days_until <= advance_notice_days:
                    message = f"""
🗓️ **Holiday Reminder**

Hi {config['Contact_Name']},

**{holiday.name}** is coming up on {holiday.holiday_date.strftime('%B %d, %Y')} ({days_until} days from now).

{holiday.description or ''}

Please plan your attendance accordingly.

This is an automated reminder from the ATTENDO system.
                    """.strip()
                    
                    methods = config.get('Notification_Method', 'EMAIL').split(',')
                    
                    if 'EMAIL' in methods:
                        excel_notification_manager.send_email_notification(
                            recipient_email=config['Contact_Email'],
                            subject=f"ATTENDO: Holiday Reminder - {holiday.name}",
                            body=message.replace('\n', '<br>'),
                            is_html=True
                        )
                    
                    if 'TEAMS' in methods and config.get('Teams_Channel'):
                        teams_webhook = f"https://teams.webhook.url/{config.get('Teams_Channel')}"
                        excel_notification_manager.send_teams_notification(
                            teams_webhook, message, "Holiday Reminder"
                        )
        
        print(f"✅ Sent holiday reminders for {len(upcoming_holidays)} holidays")
        
    except Exception as e:
        print(f"❌ Error sending holiday reminders: {str(e)}")

def send_monthly_report_notifications():
    """Send monthly report notifications based on Excel configuration"""
    try:
        # Get report configurations
        report_configs = excel_notification_manager.get_active_recipients('monthly_reports')
        
        current_date = date.today()
        report_month = (current_date - timedelta(days=1)).strftime('%Y-%m')  # Previous month
        
        for config in report_configs:
            if config.get('Auto_Generate_Monthly') != 'YES':
                continue
            
            role = config.get('Role', 'UNKNOWN')
            
            # Generate report based on role
            if role == 'MANAGER':
                manager_id = config.get('Manager_ID')
                if manager_id:
                    from utils import generate_monthly_report
                    try:
                        manager_obj = Manager.query.filter_by(manager_id=manager_id).first()
                        if manager_obj:
                            report_data = generate_monthly_report(manager_obj.id, report_month)
                            
                            message = f"""
📊 **Monthly Attendance Report**

Hi {config['Contact_Name']},

Your team's attendance report for {report_month} is ready.

**Summary:**
• Total Records: {len(report_data)}
• Report Period: {report_month}
• Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

👉 [View Full Report](http://localhost:5000/monthly-report?month={report_month})

This is an automated report from the ATTENDO system.
                            """.strip()
                            
                            methods = config.get('Notification_Method', 'EMAIL').split(',')
                            
                            if 'EMAIL' in methods:
                                attachments = []
                                if config.get('Include_Excel_Attachment') == 'YES':
                                    # Generate Excel file (would be implemented)
                                    pass
                                
                                excel_notification_manager.send_email_notification(
                                    recipient_email=config['Contact_Email'],
                                    subject=f"ATTENDO: Monthly Report - {report_month}",
                                    body=message.replace('\n', '<br>'),
                                    attachments=attachments,
                                    is_html=True
                                )
                            
                    except Exception as e:
                        print(f"❌ Error generating report for manager {manager_id}: {e}")
            
            elif role == 'ADMIN':
                # Generate system-wide report
                message = f"""
📊 **System-Wide Monthly Report**

Hi {config['Contact_Name']},

The system-wide attendance report for {report_month} is ready.

**System Summary:**
• Report Period: {report_month}
• Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

👉 [View Admin Reports](http://localhost:5000/admin/reports-dashboard)

This is an automated system report from ATTENDO.
                """.strip()
                
                methods = config.get('Notification_Method', 'EMAIL').split(',')
                
                if 'EMAIL' in methods:
                    excel_notification_manager.send_email_notification(
                        recipient_email=config['Contact_Email'],
                        subject=f"ATTENDO: System Report - {report_month}",
                        body=message.replace('\n', '<br>'),
                        is_html=True
                    )
        
        print(f"✅ Sent monthly report notifications for {report_month}")
        
    except Exception as e:
        print(f"❌ Error sending monthly report notifications: {str(e)}")

def send_end_of_day_summary():
    """Send end-of-day summary (existing function, keeping for compatibility)"""
    try:
        managers = Manager.query.all()
        today = date.today()
        
        for manager in managers:
            team_vendors = manager.team_vendors.all()
            if not team_vendors:
                continue
            
            submitted_count = 0
            pending_count = 0
            approved_count = 0
            
            for vendor in team_vendors:
                status = DailyStatus.query.filter_by(
                    vendor_id=vendor.id,
                    status_date=today
                ).first()
                
                if status:
                    submitted_count += 1
                    if status.approval_status == ApprovalStatus.APPROVED:
                        approved_count += 1
                    elif status.approval_status == ApprovalStatus.PENDING:
                        pending_count += 1
            
            # Use existing notification function for now
            message = f"""
📋 **End-of-Day Summary**

Hi {manager.full_name},

Today's team attendance summary:

**Team Size:** {len(team_vendors)}
**Submitted:** {submitted_count}/{len(team_vendors)}
**Approved:** {approved_count}
**Pending:** {pending_count}

Have a great evening!

This is an automated summary from the ATTENDO system.
            """.strip()
            
            send_notification(manager.user_id, 'end_of_day_summary', message)
        
        print(f"✅ Sent end-of-day summaries to {len(managers)} managers")
        
    except Exception as e:
        print(f"❌ Error sending end-of-day summaries: {str(e)}")

def send_late_submission_alerts():
    """Send late submission alerts based on Excel configuration"""
    try:
        # Get late submission configurations
        late_configs = excel_notification_manager.get_active_recipients('late_submissions')
        
        current_time = datetime.now()
        
        for config in late_configs:
            role = config.get('Role')
            alert_after_hours = config.get('Alert_After_Hours', 24)
            
            # Calculate cutoff time
            cutoff_time = current_time - timedelta(hours=alert_after_hours)
            cutoff_date = cutoff_time.date()
            
            if role == 'MANAGER':
                manager_id = config.get('Manager_ID')
                if manager_id:
                    try:
                        manager = Manager.query.filter_by(manager_id=manager_id).first()
                        if manager:
                            team_vendors = manager.team_vendors.all()
                            late_vendors = []
                            
                            for vendor in team_vendors:
                                # Check if vendor submitted for cutoff date
                                status = DailyStatus.query.filter_by(
                                    vendor_id=vendor.id,
                                    status_date=cutoff_date
                                ).first()
                                
                                if not status:
                                    late_vendors.append(vendor)
                            
                            if late_vendors and config.get('Send_Notification') == 'YES':
                                message = f"""
⏰ **Late Submission Alert**

Hi {config['Contact_Name']},

{len(late_vendors)} team member(s) have not submitted attendance for {cutoff_date.strftime('%B %d, %Y')}:

"""
                                
                                if config.get('Include_Individual_Details') == 'YES':
                                    for vendor in late_vendors[:10]:  # Limit to 10
                                        message += f"• {vendor.full_name} ({vendor.vendor_id})\n"
                                
                                message += f"""

Please follow up with these team members.

👉 [View Team Status](http://localhost:5000/manager/dashboard)

This is an automated alert from the ATTENDO system.
                                """.strip()
                                
                                methods = config.get('Notification_Method', 'EMAIL').split(',')
                                
                                if 'EMAIL' in methods:
                                    excel_notification_manager.send_email_notification(
                                        recipient_email=config['Contact_Email'],
                                        subject=f"ATTENDO: Late Submissions - {len(late_vendors)} Members",
                                        body=message.replace('\n', '<br>'),
                                        is_html=True
                                    )
                                
                                print(f"✅ Sent late submission alert to manager {manager.full_name}")
                    
                    except Exception as e:
                        print(f"❌ Error processing late alerts for manager {manager_id}: {e}")
        
    except Exception as e:
        print(f"❌ Error sending late submission alerts: {str(e)}")

def send_billing_correction_notifications(correction_data):
    """Send billing correction notifications based on Excel configuration"""
    try:
        # Get billing correction configurations
        billing_configs = excel_notification_manager.get_active_recipients('billing_corrections')
        
        for config in billing_configs:
            role = config.get('Role')
            
            # Prepare message based on role and correction data
            message_parts = [
                "💰 **Billing Correction Notification**",
                "",
                f"Hi {config['Contact_Name']},",
                "",
                "A billing correction has been processed:"
            ]
            
            if config.get('Include_Financial_Details') == 'YES':
                message_parts.extend([
                    f"• **Vendor:** {correction_data.get('vendor_name', 'N/A')}",
                    f"• **Date:** {correction_data.get('date', 'N/A')}",
                    f"• **Correction Type:** {correction_data.get('correction_type', 'N/A')}",
                    f"• **Amount:** {correction_data.get('amount', 'N/A')}",
                    ""
                ])
            
            if config.get('Include_Justification') == 'YES' and correction_data.get('reason'):
                message_parts.extend([
                    f"**Justification:** {correction_data.get('reason')}",
                    ""
                ])
            
            message_parts.extend([
                "👉 [View Billing Reports](http://localhost:5000/admin/billing-corrections)",
                "",
                "This is an automated notification from the ATTENDO system."
            ])
            
            message = "\n".join(message_parts)
            
            methods = config.get('Notification_Method', 'EMAIL').split(',')
            
            if 'EMAIL' in methods:
                excel_notification_manager.send_email_notification(
                    recipient_email=config['Contact_Email'],
                    subject="ATTENDO: Billing Correction Processed",
                    body=message.replace('\n', '<br>'),
                    is_html=True
                )
            
            print(f"✅ Sent billing correction notification to {config['Contact_Name']}")
    
    except Exception as e:
        print(f"❌ Error sending billing correction notifications: {str(e)}")

def send_admin_system_alerts(alert_data):
    """Send admin system alerts based on Excel configuration"""
    try:
        # Get admin alert configurations
        admin_configs = excel_notification_manager.get_active_recipients('admin_alerts')
        
        alert_type = alert_data.get('type', 'SYSTEM_ERROR')
        severity = alert_data.get('severity', 'HIGH')
        
        for config in admin_configs:
            # Check if this alert type and severity should be sent
            alert_types = config.get('Alert_Types', '').split(',')
            severity_levels = config.get('Severity_Levels', '').split(',')
            
            if alert_type not in alert_types or severity not in severity_levels:
                continue
            
            message_parts = [
                f"🚨 **System Alert - {severity}**",
                "",
                f"Hi {config['Contact_Name']},",
                "",
                f"**Alert Type:** {alert_type}",
                f"**Severity:** {severity}",
                f"**Time:** {alert_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}",
                "",
                f"**Details:** {alert_data.get('message', 'No additional details')}",
                ""
            ]
            
            if config.get('Include_System_Stats') == 'YES':
                message_parts.extend([
                    "**System Status:**",
                    f"• Database: {alert_data.get('db_status', 'Unknown')}",
                    f"• Active Users: {alert_data.get('active_users', 'Unknown')}",
                    f"• System Load: {alert_data.get('system_load', 'Unknown')}",
                    ""
                ])
            
            if config.get('Include_Recommended_Actions') == 'YES':
                message_parts.extend([
                    "**Recommended Actions:**",
                    "• Review system logs",
                    "• Check database connectivity",
                    "• Verify service status",
                    ""
                ])
            
            message_parts.extend([
                "👉 [Admin Dashboard](http://localhost:5000/admin/dashboard)",
                "",
                "This is an automated alert from the ATTENDO system."
            ])
            
            message = "\n".join(message_parts)
            
            methods = config.get('Notification_Method', 'EMAIL').split(',')
            
            if 'EMAIL' in methods:
                excel_notification_manager.send_email_notification(
                    recipient_email=config['Contact_Email'],
                    subject=f"ATTENDO: {severity} System Alert - {alert_type}",
                    body=message.replace('\n', '<br>'),
                    is_html=True
                )
            
            if 'TEAMS' in methods and config.get('Teams_Channel'):
                teams_webhook = f"https://teams.webhook.url/{config.get('Teams_Channel')}"
                excel_notification_manager.send_teams_notification(
                    teams_webhook, message, f"System Alert - {severity}"
                )
            
            print(f"✅ Sent system alert to admin {config['Contact_Name']}")
    
    except Exception as e:
        print(f"❌ Error sending admin system alerts: {str(e)}")

def send_manager_feedback_notification(vendor_id, feedback_type, manager_comments, action_required=True):
    """Send manager feedback notification to vendor based on Excel configuration"""
    try:
        # Get feedback configurations for this vendor
        feedback_configs = excel_notification_manager.get_active_recipients(
            'manager_feedback', 
            filters={'Vendor_ID': vendor_id}
        )
        
        if not feedback_configs:
            return
        
        config = feedback_configs[0]  # Use first matching config
        
        # Check if this feedback type should be sent
        feedback_types = config.get('Feedback_Types', '').split(',')
        if feedback_type not in feedback_types:
            return
        
        # Map feedback types to messages
        feedback_messages = {
            'REJECTION': '❌ **Status Rejected**',
            'CORRECTION_REQUEST': '✏️ **Correction Required**',
            'APPROVAL': '✅ **Status Approved**'
        }
        
        message_parts = [
            feedback_messages.get(feedback_type, '📝 **Manager Feedback**'),
            "",
            f"Hi {config['Contact_Name']},",
            ""
        ]
        
        if config.get('Include_Manager_Comments') == 'YES' and manager_comments:
            message_parts.extend([
                f"**Manager Comments:** {manager_comments}",
                ""
            ])
        
        if action_required and config.get('Include_Corrective_Actions') == 'YES':
            response_hours = config.get('Response_Required_Hours', 24)
            message_parts.extend([
                "**Action Required:**",
                "• Review the feedback above",
                "• Make necessary corrections",
                "• Resubmit your status",
                f"• Response required within {response_hours} hours",
                ""
            ])
        
        message_parts.extend([
            "👉 [Update Status](http://localhost:5000/vendor/dashboard)",
            "",
            "This is feedback from your manager via the ATTENDO system."
        ])
        
        message = "\n".join(message_parts)
        
        methods = config.get('Notification_Method', 'EMAIL').split(',')
        
        if 'EMAIL' in methods:
            excel_notification_manager.send_email_notification(
                recipient_email=config['Contact_Email'],
                subject=f"ATTENDO: Manager Feedback - {feedback_type.replace('_', ' ').title()}",
                body=message.replace('\n', '<br>'),
                is_html=True
            )
        
        if 'SMS' in methods and config.get('Phone_Number'):
            # SMS implementation would go here
            print(f"📱 SMS notification to {config.get('Phone_Number')}: {feedback_type}")
        
        print(f"✅ Sent {feedback_type} feedback to vendor {config['Contact_Name']}")
    
    except Exception as e:
        print(f"❌ Error sending manager feedback notification: {str(e)}")

def run_daily_excel_reset():
    """Run daily Excel reset for Power Automate accuracy"""
    try:
        print("🌅 Starting daily Excel reset...")
        success = run_daily_reset()
        if success:
            print("✅ Daily Excel reset completed successfully")
        else:
            print("❌ Daily Excel reset failed")
            # Could trigger emergency notifications here
        return success
    except Exception as e:
        print(f"❌ Fatal error in daily Excel reset: {str(e)}")
        return False

# Legacy function wrappers for backward compatibility
def send_daily_reminders():
    """Legacy function - now uses Excel configuration"""
    send_configured_daily_reminders()

def send_manager_notifications():
    """Legacy function - now uses Excel configuration"""  
    send_configured_manager_notifications()

def send_teams_notification(email, title, message):
    """Legacy Teams notification function"""
    # This would use the Excel config to determine the right webhook
    print(f"📢 Teams notification: {title} to {email}")
    return True
