from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date, time, timedelta
import atexit
from models import User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday, MismatchRecord, NotificationLog, AuditLog, SystemConfiguration, LeaveRecord, WFHRecord, UserRole, AttendanceStatus, ApprovalStatus
import models
from utils import check_late_submissions, send_notification, get_system_config

def start_notification_scheduler():
    """Start the background scheduler for notifications"""
    scheduler = BackgroundScheduler()
    
    # Schedule daily reminders every 3 hours (9 AM, 12 PM, 3 PM, 6 PM)
    scheduler.add_job(
        func=send_daily_reminders,
        trigger="cron",
        hour='9,12,15,18',
        minute=0,
        id='daily_reminders'
    )
    
    # Schedule manager notifications at 12 PM and 2 PM
    scheduler.add_job(
        func=send_manager_notifications,
        trigger="cron",
        hour='12,14',
        minute=0,
        id='manager_notifications'
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
        func=run_mismatch_detection,
        trigger="cron",
        hour=23,
        minute=0,
        id='mismatch_detection'
    )
    
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    
    print("Notification scheduler started!")
    return scheduler

def send_daily_reminders():
    """Send Teams reminders to vendors who haven't submitted status"""
    try:
        late_vendors = check_late_submissions()
        
        if not late_vendors:
            print("No late submissions to remind about")
            return
        
        reminder_interval = int(get_system_config('reminder_interval_hours', '3'))
        current_hour = datetime.now().hour
        
        for vendor in late_vendors:
            # Check if we should send reminder based on interval
            last_reminder = NotificationLog.query.filter_by(
                recipient_id=vendor.user_account.id,
                notification_type='daily_reminder'
            ).order_by(NotificationLog.sent_at.desc()).first()
            
            should_send = True
            if last_reminder:
                time_since_last = datetime.now() - last_reminder.sent_at
                if time_since_last.total_seconds() < (reminder_interval * 3600):
                    should_send = False
            
            if should_send:
                message = f"""
🚨 **Daily Status Reminder**

Hi {vendor.full_name},

You haven't submitted your attendance status for today ({date.today().strftime('%B %d, %Y')}).

Please update your status:
• In Office (Full/Half Day)
• Work From Home (Full/Half Day)  
• On Leave (Full/Half Day)

👉 [Submit Status Here](http://localhost:5000/vendor/dashboard)

This is an automated reminder from the Vendor Timesheet System.
                """.strip()
                
                send_teams_notification(vendor.user_account.email, "Daily Status Reminder", message)
                send_notification(vendor.user_account.id, 'daily_reminder', message)
                
        print(f"Sent reminders to {len(late_vendors)} vendors")
        
    except Exception as e:
        print(f"Error sending daily reminders: {str(e)}")

def send_manager_notifications():
    """Send notifications to managers about team status"""
    try:
        managers = Manager.query.all()
        current_time = datetime.now().time()
        
        for manager in managers:
            team_vendors = manager.team_vendors.all()
            
            if not team_vendors:
                continue
            
            today = date.today()
            submitted_count = 0
            pending_count = 0
            approved_count = 0
            
            team_status = []
            
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
                    
                    team_status.append(f"✅ {vendor.full_name}: {status.status.value.replace('_', ' ').title()}")
                else:
                    team_status.append(f"❌ {vendor.full_name}: Not submitted")
            
            # Send notification based on time
            if current_time.hour == 12:
                # 12 PM - Mid-day summary
                message = f"""
📊 **Mid-Day Team Status Summary**

Hi {manager.full_name},

Team attendance status as of 12:00 PM:

**Team Size:** {len(team_vendors)}
**Submitted:** {submitted_count}/{len(team_vendors)}
**Pending Approval:** {pending_count}
**Approved:** {approved_count}

**Individual Status:**
{chr(10).join(team_status)}

👉 [Review Team Status](http://localhost:5000/manager/dashboard)
                """.strip()
                
            elif current_time.hour == 14:
                # 2 PM - Follow-up reminder
                pending_vendors = len(team_vendors) - submitted_count
                
                if pending_vendors > 0:
                    message = f"""
⏰ **Follow-Up: Team Status Reminder**

Hi {manager.full_name},

{pending_vendors} team member(s) still haven't submitted their attendance status.

**Action Required:**
• Follow up with pending team members
• Review and approve submitted statuses

👉 [Manage Team](http://localhost:5000/manager/dashboard)
                    """.strip()
                else:
                    message = f"""
✅ **All Team Members Submitted!**

Hi {manager.full_name},

Great news! All your team members have submitted their attendance status for today.

**Pending Actions:**
• {pending_count} statuses awaiting your approval

👉 [Review Approvals](http://localhost:5000/manager/dashboard)
                    """.strip()
            
            send_teams_notification(manager.user_account.email, "Team Status Update", message)
            send_notification(manager.user_account.id, 'team_summary', message)
            
        print(f"Sent manager notifications to {len(managers)} managers")
        
    except Exception as e:
        print(f"Error sending manager notifications: {str(e)}")

def send_end_of_day_summary():
    """Send end-of-day summary to all managers when all statuses are filled"""
    try:
        managers = Manager.query.all()
        
        for manager in managers:
            team_vendors = manager.team_vendors.all()
            
            if not team_vendors:
                continue
            
            today = date.today()
            total_team = len(team_vendors)
            submitted_today = 0
            approved_today = 0
            pending_approval = 0
            rejected_today = 0
            
            status_breakdown = {
                'in_office': 0,
                'wfh': 0,
                'leave': 0,
                'absent': 0
            }
            
            for vendor in team_vendors:
                status = DailyStatus.query.filter_by(
                    vendor_id=vendor.id,
                    status_date=today
                ).first()
                
                if status:
                    submitted_today += 1
                    
                    if status.approval_status == ApprovalStatus.APPROVED:
                        approved_today += 1
                    elif status.approval_status == ApprovalStatus.PENDING:
                        pending_approval += 1
                    elif status.approval_status == ApprovalStatus.REJECTED:
                        rejected_today += 1
                    
                    # Count status types
                    if status.status in [AttendanceStatus.IN_OFFICE_FULL, AttendanceStatus.IN_OFFICE_HALF]:
                        status_breakdown['in_office'] += 1
                    elif status.status in [AttendanceStatus.WFH_FULL, AttendanceStatus.WFH_HALF]:
                        status_breakdown['wfh'] += 1
                    elif status.status in [AttendanceStatus.LEAVE_FULL, AttendanceStatus.LEAVE_HALF]:
                        status_breakdown['leave'] += 1
                    elif status.status == AttendanceStatus.ABSENT:
                        status_breakdown['absent'] += 1
            
            # Check if all team members submitted
            all_submitted = (submitted_today == total_team)
            
            message = f"""
📈 **End-of-Day Team Summary**

Hi {manager.full_name},

Daily summary for {today.strftime('%B %d, %Y')}:

**Team Overview:**
• Team Size: {total_team}
• Submitted: {submitted_today}/{total_team} {'✅' if all_submitted else '⚠️'}
• Approved: {approved_today}
• Pending: {pending_approval}
• Rejected: {rejected_today}

**Status Breakdown:**
• In Office: {status_breakdown['in_office']}
• Work From Home: {status_breakdown['wfh']}
• On Leave: {status_breakdown['leave']}
• Absent: {status_breakdown['absent']}

{'🎉 **Great job! All team members submitted their status today.**' if all_submitted else '⚠️ **Action needed: Follow up with pending submissions.**'}

👉 [View Detailed Report](http://localhost:5000/manager/team-report)
            """.strip()
            
            send_teams_notification(manager.user_account.email, "End-of-Day Summary", message)
            send_notification(manager.user_account.id, 'daily_summary', message)
            
        print("Sent end-of-day summaries to all managers")
        
    except Exception as e:
        print(f"Error sending end-of-day summary: {str(e)}")

def run_mismatch_detection():
    """Run daily mismatch detection and notify relevant parties"""
    try:
        from utils import detect_mismatches
        
        new_mismatches = detect_mismatches()
        
        if new_mismatches > 0:
            # Notify admins about new mismatches
            admin_users = User.query.filter_by(role=UserRole.ADMIN).all()
            
            for admin in admin_users:
                message = f"""
🔍 **New Attendance Mismatches Detected**

Hi Admin,

The system has detected {new_mismatches} new attendance mismatches during the daily reconciliation process.

**Next Steps:**
• Vendors will be notified to provide explanations
• Managers will need to review and approve explanations
• Check the mismatch review dashboard for details

👉 [Review Mismatches](http://localhost:5000/admin/dashboard)
                """.strip()
                
                send_notification(admin.id, 'mismatch_alert', message)
            
            print(f"Detected {new_mismatches} new mismatches and notified admins")
        
    except Exception as e:
        print(f"Error in mismatch detection: {str(e)}")

def send_teams_notification(email, subject, message):
    """
    Simulate sending Microsoft Teams notification
    In a real implementation, this would use Teams Webhook or Graph API
    """
    try:
        # For demo purposes, we'll just log the notification
        # In production, you would implement actual Teams integration here
        
        print(f"""
=== TEAMS NOTIFICATION ===
To: {email}
Subject: {subject}
Message:
{message}
=========================""")
        
        # Here's where you would implement actual Teams integration:
        # 1. Using Teams Webhook
        # webhook_url = "YOUR_TEAMS_WEBHOOK_URL"
        # payload = {
        #     "@type": "MessageCard",
        #     "themeColor": "0076D7",
        #     "summary": subject,
        #     "sections": [{
        #         "activityTitle": subject,
        #         "activityText": message.replace('\n', '<br>')
        #     }]
        # }
        # requests.post(webhook_url, json=payload)
        
        # 2. Using Microsoft Graph API
        # graph_client = GraphServiceClient(credentials, scopes)
        # chat_message = ChatMessage(
        #     body=ChatMessageBody(content=message)
        # )
        # await graph_client.teams.by_team_id(team_id).channels.by_channel_id(channel_id).messages.post(chat_message)
        
        return True
        
    except Exception as e:
        print(f"Error sending Teams notification: {str(e)}")
        return False

def notify_vendor_mismatch(vendor_id, mismatch_id):
    """Notify vendor about attendance mismatch requiring explanation"""
    try:
        vendor = Vendor.query.get(vendor_id)
        mismatch = MismatchRecord.query.get(mismatch_id)
        
        if not vendor or not mismatch:
            return False
        
        message = f"""
🔄 **Attendance Mismatch - Action Required**

Hi {vendor.full_name},

We've detected a mismatch in your attendance record:

**Date:** {mismatch.mismatch_date.strftime('%B %d, %Y')}
**Your Status:** {mismatch.web_status.value.replace('_', ' ').title()}
**Swipe Record:** {'Present' if mismatch.swipe_status == 'AP' else 'Absent'}

**Action Required:**
Please provide an explanation for this mismatch. Common reasons include:
• Forgot to swipe in/out
• System/card issues
• Emergency situations
• Meeting in different building

👉 [Provide Explanation](http://localhost:5000/vendor/dashboard)

This needs to be resolved for accurate billing and reporting.
        """.strip()
        
        send_teams_notification(vendor.user_account.email, "Attendance Mismatch - Action Required", message)
        send_notification(vendor.user_account.id, 'mismatch_vendor', message)
        
        return True
        
    except Exception as e:
        print(f"Error notifying vendor about mismatch: {str(e)}")
        return False

def notify_manager_mismatch_review(manager_id, mismatch_id):
    """Notify manager about mismatch explanation awaiting review"""
    try:
        manager = Manager.query.get(manager_id)
        mismatch = MismatchRecord.query.get(mismatch_id)
        
        if not manager or not mismatch:
            return False
        
        message = f"""
📋 **Mismatch Explanation - Review Required**

Hi {manager.full_name},

A team member has provided an explanation for an attendance mismatch:

**Vendor:** {mismatch.vendor.full_name}
**Date:** {mismatch.mismatch_date.strftime('%B %d, %Y')}
**Explanation:** {mismatch.vendor_reason}

**Action Required:**
• Review the explanation
• Approve or reject with comments
• This affects billing accuracy

👉 [Review Explanation](http://localhost:5000/manager/dashboard)
        """.strip()
        
        send_teams_notification(manager.user_account.email, "Mismatch Review Required", message)
        send_notification(manager.user_account.id, 'mismatch_manager', message)
        
        return True
        
    except Exception as e:
        print(f"Error notifying manager about mismatch review: {str(e)}")
        return False

def send_weekly_analytics():
    """Send weekly analytics to managers and admins"""
    try:
        # This could be scheduled weekly
        # Implementation would include:
        # - Weekly attendance patterns
        # - Team productivity insights
        # - Absence predictions
        # - Compliance metrics
        pass
        
    except Exception as e:
        print(f"Error sending weekly analytics: {str(e)}")

def send_custom_notification(user_id, title, message, notification_type='custom'):
    """Send custom notification to specific user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False
        
        send_teams_notification(user.email, title, message)
        send_notification(user_id, notification_type, message)
        
        return True
        
    except Exception as e:
        print(f"Error sending custom notification: {str(e)}")
        return False
