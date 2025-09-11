#!/usr/bin/env python3
"""
ATTENDO Notification System Updater - Clean Version
===================================================

Creates clean Excel files with only 5 columns:
- EmployeeID: Employee/Manager/Admin ID
- ContactEmail: Recipient email address  
- Message: Notification message content
- NotificationType: Type of notification
- Priority: Low/Medium/High/Critical

Updates all 9 essential notification files based on NOTIFICATION_SYSTEM_GUIDE.html
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path
from datetime import datetime, date, timedelta

class NotificationSystemUpdater:
    def __init__(self, db_path='vendor_timesheet.db', excel_folder='notification_configs'):
        self.db_path = db_path
        self.excel_folder = Path(excel_folder)
        self.excel_folder.mkdir(exist_ok=True)
        self.today = date.today()
        self.current_time = datetime.now()
        
    def get_db_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def create_clean_excel(self, data, file_path, notification_type):
        """Create clean Excel file with exactly 5 columns"""
        if data.empty:
            # Create empty table with standard headers
            data = pd.DataFrame(columns=['EmployeeID', 'ContactEmail', 'Message', 'NotificationType', 'Priority'])
        else:
            # Add NotificationType and ensure correct column order
            data['NotificationType'] = notification_type
            data = data[['EmployeeID', 'ContactEmail', 'Message', 'NotificationType', 'Priority']]
            
        # Save as Excel file
        data.to_excel(file_path, index=False, sheet_name='Notifications')
        print(f"✅ Updated {file_path} with {len(data)} notifications")
        
    def update_01_daily_status_reminders(self):
        """01_daily_status_reminders.xlsx - Remind vendors to submit daily status"""
        print("\n🔔 Updating Daily Status Reminders...")
        
        conn = self.get_db_connection()
        
        # Skip weekends
        if self.today.weekday() >= 5:
            print("   ⏭️ Skipping - Weekend")
            self.create_clean_excel(pd.DataFrame(), 
                                  self.excel_folder / '01_daily_status_reminders.xlsx',
                                  'DAILY_REMINDER')
            conn.close()
            return
            
        # Get vendors who haven't submitted status for today
        query = """
        SELECT 
            v.vendor_id as EmployeeID,
            u.email as ContactEmail,
            v.full_name
        FROM vendors v
        JOIN users u ON v.user_id = u.id
        LEFT JOIN daily_statuses ds ON v.id = ds.vendor_id AND ds.status_date = ?
        WHERE u.is_active = 1 AND ds.id IS NULL
        ORDER BY v.vendor_id
        """
        
        df = pd.read_sql_query(query, conn, params=[self.today.isoformat()])
        
        if not df.empty:
            df['Message'] = df.apply(lambda row: 
                f"📋 Hi {row['full_name']}, please submit your daily attendance status for {self.today.strftime('%B %d, %Y')}. "
                f"Your compliance helps ensure accurate tracking. Submit at: http://localhost:5000/vendor", 
                axis=1)
            df['Priority'] = 'Medium'
            result_df = df[['EmployeeID', 'ContactEmail', 'Message', 'Priority']]
        else:
            result_df = pd.DataFrame()
            
        self.create_clean_excel(result_df, 
                              self.excel_folder / '01_daily_status_reminders.xlsx',
                              'DAILY_REMINDER')
        conn.close()
        
    def update_02_manager_summary_notifications(self):
        """02_manager_summary_notifications.xlsx - Manager team summaries"""
        print("\n📊 Updating Manager Summary Notifications...")
        
        conn = self.get_db_connection()
        
        # Get manager summary data
        query = """
        SELECT 
            m.manager_id as EmployeeID,
            u.email as ContactEmail,
            m.full_name as manager_name,
            COUNT(v.id) as total_team,
            COUNT(ds.id) as completed_today,
            (COUNT(v.id) - COUNT(ds.id)) as pending_today
        FROM managers m
        JOIN users u ON m.user_id = u.id
        JOIN vendors v ON m.manager_id = v.manager_id
        LEFT JOIN daily_statuses ds ON v.id = ds.vendor_id AND ds.status_date = ?
        WHERE u.is_active = 1
        GROUP BY m.manager_id, m.full_name, u.email
        HAVING COUNT(v.id) > 0
        ORDER BY m.manager_id
        """
        
        df = pd.read_sql_query(query, conn, params=[self.today.isoformat()])
        
        if not df.empty:
            df['completion_rate'] = ((df['completed_today'] / df['total_team']) * 100).round(1)
            df['Message'] = df.apply(lambda row:
                f"📊 Team Summary for {row['manager_name']} - {self.today.strftime('%B %d, %Y')}: "
                f"{row['completed_today']}/{row['total_team']} members submitted status "
                f"({row['completion_rate']}% completion rate). "
                f"{'✅ All done!' if row['pending_today'] == 0 else f'⏳ {row['pending_today']} still pending.'}",
                axis=1)
            df['Priority'] = df.apply(lambda row: 'High' if row['pending_today'] > row['total_team'] * 0.5 else 'Medium', axis=1)
            result_df = df[['EmployeeID', 'ContactEmail', 'Message', 'Priority']]
        else:
            result_df = pd.DataFrame()
            
        self.create_clean_excel(result_df,
                              self.excel_folder / '02_manager_summary_notifications.xlsx', 
                              'MANAGER_SUMMARY')
        conn.close()
        
    def update_03_manager_all_complete_notifications(self):
        """03_manager_all_complete_notifications.xlsx - Celebrate team completion"""
        print("\n✅ Updating All-Complete Notifications...")
        
        conn = self.get_db_connection()
        
        # Get managers whose teams have 100% completion
        query = """
        SELECT 
            m.manager_id as EmployeeID,
            u.email as ContactEmail,
            m.full_name as manager_name,
            COUNT(v.id) as total_team,
            COUNT(ds.id) as completed_today,
            MAX(ds.submitted_at) as last_submission
        FROM managers m
        JOIN users u ON m.user_id = u.id
        JOIN vendors v ON m.manager_id = v.manager_id
        LEFT JOIN daily_statuses ds ON v.id = ds.vendor_id AND ds.status_date = ?
        WHERE u.is_active = 1
        GROUP BY m.manager_id, m.full_name, u.email
        HAVING COUNT(v.id) > 0 AND COUNT(ds.id) = COUNT(v.id)
        ORDER BY m.manager_id
        """
        
        df = pd.read_sql_query(query, conn, params=[self.today.isoformat()])
        
        if not df.empty:
            df['Message'] = df.apply(lambda row:
                f"🎉 Congratulations {row['manager_name']}! Your entire team ({row['total_team']} members) "
                f"has successfully submitted their attendance status for {self.today.strftime('%B %d, %Y')}. "
                f"Team completion achieved at {pd.to_datetime(row['last_submission']).strftime('%H:%M') if row['last_submission'] else 'today'}. "
                f"Excellent leadership! 👏",
                axis=1)
            df['Priority'] = 'Low'
            result_df = df[['EmployeeID', 'ContactEmail', 'Message', 'Priority']]
        else:
            result_df = pd.DataFrame()
            
        self.create_clean_excel(result_df,
                              self.excel_folder / '03_manager_all_complete_notifications.xlsx',
                              'ALL_COMPLETE')
        conn.close()
        
    def update_04_mismatch_notifications(self):
        """04_mismatch_notifications.xlsx - Alert about attendance mismatches"""
        print("\n⚠️ Updating Mismatch Notifications...")
        
        conn = self.get_db_connection()
        
        # Get mismatch records from today
        query = """
        SELECT 
            v.vendor_id as EmployeeID,
            u.email as ContactEmail,
            v.full_name,
            mr.web_status,
            mr.swipe_status,
            m.manager_id,
            mu.email as manager_email
        FROM mismatch_records mr
        JOIN vendors v ON mr.vendor_id = v.id
        JOIN users u ON v.user_id = u.id
        LEFT JOIN managers m ON v.manager_id = m.manager_id
        LEFT JOIN users mu ON m.user_id = mu.id
        WHERE DATE(mr.created_at) = ? AND u.is_active = 1
        ORDER BY mr.created_at DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[self.today.isoformat()])
        
        notifications = []
        
        if not df.empty:
            # Create notifications for vendors with mismatches
            for _, row in df.iterrows():
                # Notification to vendor
                vendor_msg = (f"⚠️ Attendance Mismatch Alert for {row['full_name']} - "
                             f"Your submitted status ({row['web_status']}) doesn't match "
                             f"card swipe data ({row['swipe_status']}) for {self.today.strftime('%B %d, %Y')}. "
                             f"Please review and update if needed: http://localhost:5000/vendor")
                
                notifications.append({
                    'EmployeeID': row['EmployeeID'],
                    'ContactEmail': row['ContactEmail'],
                    'Message': vendor_msg,
                    'Priority': 'High'
                })
                
                # Notification to manager if exists
                if row['manager_email']:
                    manager_msg = (f"⚠️ Team Mismatch Alert - {row['full_name']} ({row['EmployeeID']}) "
                                  f"has an attendance mismatch: Status={row['web_status']}, "
                                  f"Swipe={row['swipe_status']}. Please review and take action.")
                    
                    notifications.append({
                        'EmployeeID': row['manager_id'],
                        'ContactEmail': row['manager_email'],
                        'Message': manager_msg,
                        'Priority': 'High'
                    })
        
        result_df = pd.DataFrame(notifications) if notifications else pd.DataFrame()
        
        self.create_clean_excel(result_df,
                              self.excel_folder / '04_mismatch_notifications.xlsx',
                              'MISMATCH_ALERT')
        conn.close()
        
    def update_05_manager_feedback_notifications(self):
        """05_manager_feedback_notifications.xlsx - Manager feedback to vendors"""
        print("\n📝 Updating Manager Feedback Notifications...")
        
        conn = self.get_db_connection()
        
        # Get recent manager feedback (within last hour)
        one_hour_ago = self.current_time - timedelta(hours=1)
        
        query = """
        SELECT 
            v.vendor_id as EmployeeID,
            u.email as ContactEmail,
            v.full_name,
            ds.approval_status,
            ds.manager_comments,
            m.full_name as manager_name
        FROM daily_statuses ds
        JOIN vendors v ON ds.vendor_id = v.id
        JOIN users u ON v.user_id = u.id
        LEFT JOIN managers m ON v.manager_id = m.manager_id
        WHERE ds.approved_at >= ? 
          AND ds.approval_status IN ('APPROVED', 'REJECTED')
          AND u.is_active = 1
        ORDER BY ds.approved_at DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[one_hour_ago.isoformat()])
        
        if not df.empty:
            df['Message'] = df.apply(lambda row:
                f"📝 Status Update from {row['manager_name'] or 'Manager'} - "
                f"Your daily status for {self.today.strftime('%B %d, %Y')} has been "
                f"{'✅ APPROVED' if row['approval_status'] == 'APPROVED' else '❌ REJECTED'}. "
                f"{f'Comments: {row["manager_comments"]}' if row['manager_comments'] else ''} "
                f"{'Thank you for your compliance!' if row['approval_status'] == 'APPROVED' else 'Please review and resubmit if needed.'}",
                axis=1)
            df['Priority'] = df.apply(lambda row: 'High' if row['approval_status'] == 'REJECTED' else 'Medium', axis=1)
            result_df = df[['EmployeeID', 'ContactEmail', 'Message', 'Priority']]
        else:
            result_df = pd.DataFrame()
            
        self.create_clean_excel(result_df,
                              self.excel_folder / '05_manager_feedback_notifications.xlsx',
                              'MANAGER_FEEDBACK')
        conn.close()
        
    def update_06_monthly_report_notifications(self):
        """06_monthly_report_notifications.xlsx - Monthly report delivery"""
        print("\n📈 Updating Monthly Report Notifications...")
        
        # Only send on 1st of month
        if self.today.day != 1:
            print("   ⏭️ Skipping - Not 1st of month")
            self.create_clean_excel(pd.DataFrame(),
                                  self.excel_folder / '06_monthly_report_notifications.xlsx',
                                  'MONTHLY_REPORT')
            return
            
        conn = self.get_db_connection()
        
        # Get managers and admins for monthly reports
        query = """
        SELECT 
            COALESCE(m.manager_id, 'ADMIN') as EmployeeID,
            u.email as ContactEmail,
            COALESCE(m.full_name, u.username) as full_name,
            u.role
        FROM users u
        LEFT JOIN managers m ON u.id = m.user_id
        WHERE u.is_active = 1 AND u.role IN ('MANAGER', 'ADMIN')
        ORDER BY u.role, COALESCE(m.manager_id, u.username)
        """
        
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            last_month = (self.today.replace(day=1) - timedelta(days=1))
            df['Message'] = df.apply(lambda row:
                f"📈 Monthly Attendance Report - {last_month.strftime('%B %Y')} is now available! "
                f"Hi {row['full_name']}, your comprehensive attendance report including trends, "
                f"insights, and team analytics is ready for review. "
                f"{'As a manager, this includes your team statistics.' if row['role'] == 'MANAGER' else 'As an admin, this includes organization-wide analytics.'} "
                f"Access your report at: http://localhost:5000/{'manager' if row['role'] == 'MANAGER' else 'admin'}/reports",
                axis=1)
            df['Priority'] = 'Medium'
            result_df = df[['EmployeeID', 'ContactEmail', 'Message', 'Priority']]
        else:
            result_df = pd.DataFrame()
            
        self.create_clean_excel(result_df,
                              self.excel_folder / '06_monthly_report_notifications.xlsx',
                              'MONTHLY_REPORT')
        conn.close()
        
    def update_07_admin_system_alerts(self):
        """07_admin_system_alerts.xlsx - Critical system alerts"""
        print("\n🚨 Updating Admin System Alerts...")
        
        conn = self.get_db_connection()
        
        # Get system administrators
        admin_query = """
        SELECT 
            u.username as EmployeeID,
            u.email as ContactEmail,
            u.username as admin_name
        FROM users u
        WHERE u.role = 'ADMIN' AND u.is_active = 1
        """
        
        admins_df = pd.read_sql_query(admin_query, conn)
        alerts = []
        
        if not admins_df.empty:
            # Check mismatch rates (high if >20%)
            mismatch_query = "SELECT COUNT(*) as mismatch_count FROM mismatch_records WHERE DATE(created_at) = ?"
            total_submissions_query = "SELECT COUNT(*) as total_submissions FROM daily_statuses WHERE status_date = ?"
            
            mismatch_count = pd.read_sql_query(mismatch_query, conn, params=[self.today.isoformat()])['mismatch_count'].iloc[0]
            total_submissions = pd.read_sql_query(total_submissions_query, conn, params=[self.today.isoformat()])['total_submissions'].iloc[0]
            
            if total_submissions > 0:
                mismatch_rate = (mismatch_count / total_submissions) * 100
                if mismatch_rate > 20:
                    for _, admin in admins_df.iterrows():
                        alerts.append({
                            'EmployeeID': admin['EmployeeID'],
                            'ContactEmail': admin['ContactEmail'],
                            'Message': f"🚨 HIGH MISMATCH ALERT - {mismatch_rate:.1f}% mismatch rate detected today "
                                      f"({mismatch_count}/{total_submissions}). This exceeds the 20% threshold. "
                                      f"Please review system integrity and investigate potential issues.",
                            'Priority': 'Critical'
                        })
        
        result_df = pd.DataFrame(alerts) if alerts else pd.DataFrame()
        
        self.create_clean_excel(result_df,
                              self.excel_folder / '07_admin_system_alerts.xlsx',
                              'SYSTEM_ALERT')
        conn.close()
        
    def update_08_holiday_reminder_notifications(self):
        """08_holiday_reminder_notifications.xlsx - Holiday reminders"""
        print("\n🏖️ Updating Holiday Reminder Notifications...")
        
        conn = self.get_db_connection()
        
        # Get upcoming holidays (3 days and 1 day before)
        three_days_ahead = self.today + timedelta(days=3)
        one_day_ahead = self.today + timedelta(days=1)
        
        holiday_query = """
        SELECT name, holiday_date, description
        FROM holidays
        WHERE holiday_date IN (?, ?)
        ORDER BY holiday_date
        """
        
        holidays_df = pd.read_sql_query(holiday_query, conn, 
                                       params=[three_days_ahead.isoformat(), one_day_ahead.isoformat()])
        
        if holidays_df.empty:
            print("   ⏭️ No upcoming holidays")
            self.create_clean_excel(pd.DataFrame(),
                                  self.excel_folder / '08_holiday_reminder_notifications.xlsx',
                                  'HOLIDAY_REMINDER')
            conn.close()
            return
        
        # Get all users
        users_query = """
        SELECT 
            CASE 
                WHEN u.role = 'VENDOR' THEN v.vendor_id
                WHEN u.role = 'MANAGER' THEN m.manager_id  
                ELSE u.username
            END as EmployeeID,
            u.email as ContactEmail,
            COALESCE(v.full_name, m.full_name, u.username) as full_name
        FROM users u
        LEFT JOIN vendors v ON u.id = v.user_id
        LEFT JOIN managers m ON u.id = m.user_id
        WHERE u.is_active = 1
        ORDER BY u.role, COALESCE(v.vendor_id, m.manager_id, u.username)
        """
        
        users_df = pd.read_sql_query(users_query, conn)
        notifications = []
        
        for _, holiday in holidays_df.iterrows():
            holiday_date = pd.to_datetime(holiday['holiday_date']).date()
            days_until = (holiday_date - self.today).days
            
            for _, user in users_df.iterrows():
                message = (f"🏖️ Holiday Reminder - {holiday['name']} is {'tomorrow' if days_until == 1 else f'in {days_until} days'} "
                          f"({holiday_date.strftime('%B %d, %Y')}). "
                          f"{holiday['description'] if holiday['description'] else ''} "
                          f"Please plan your schedule accordingly and ensure all submissions are up to date. "
                          f"Have a wonderful holiday! 🎉")
                
                notifications.append({
                    'EmployeeID': user['EmployeeID'],
                    'ContactEmail': user['ContactEmail'], 
                    'Message': message,
                    'Priority': 'Low'
                })
        
        result_df = pd.DataFrame(notifications) if notifications else pd.DataFrame()
        
        self.create_clean_excel(result_df,
                              self.excel_folder / '08_holiday_reminder_notifications.xlsx',
                              'HOLIDAY_REMINDER')
        conn.close()
        
    def update_09_late_submission_alerts(self):
        """09_late_submission_alerts.xlsx - Late submission alerts"""
        print("\n⏰ Updating Late Submission Alerts...")
        
        conn = self.get_db_connection()
        
        # Get vendors with late submissions (24h and 48h after deadline)
        yesterday = self.today - timedelta(days=1)
        day_before_yesterday = self.today - timedelta(days=2)
        
        # 24-hour late submissions (alert managers)
        late_24h_query = """
        SELECT 
            v.vendor_id, v.full_name as vendor_name,
            m.manager_id as EmployeeID, u.email as ContactEmail,
            m.full_name as manager_name
        FROM vendors v
        JOIN managers m ON v.manager_id = m.manager_id
        JOIN users u ON m.user_id = u.id
        LEFT JOIN daily_statuses ds ON v.id = ds.vendor_id AND ds.status_date = ?
        WHERE ds.id IS NULL AND u.is_active = 1 AND m.manager_id IS NOT NULL
        """
        
        # 48-hour late submissions (alert admins)  
        late_48h_query = """
        SELECT v.vendor_id, v.full_name as vendor_name,
            u.username as EmployeeID, u.email as ContactEmail
        FROM vendors v, users u
        LEFT JOIN daily_statuses ds ON v.id = ds.vendor_id AND ds.status_date = ?
        WHERE ds.id IS NULL AND u.role = 'ADMIN' AND u.is_active = 1
        """
        
        notifications = []
        
        # 24-hour alerts to managers
        late_24h_df = pd.read_sql_query(late_24h_query, conn, params=[yesterday.isoformat()])
        
        for _, row in late_24h_df.iterrows():
            message = (f"⏰ Late Submission Alert - Team member {row['vendor_name']} ({row['vendor_id']}) "
                      f"has not submitted attendance status for {yesterday.strftime('%B %d, %Y')} "
                      f"(24 hours overdue). Please follow up to ensure compliance.")
            
            notifications.append({
                'EmployeeID': row['EmployeeID'],
                'ContactEmail': row['ContactEmail'],
                'Message': message,
                'Priority': 'High'
            })
        
        # 48-hour alerts to admins
        late_48h_df = pd.read_sql_query(late_48h_query, conn, params=[day_before_yesterday.isoformat()])
        
        # Group by admin to avoid duplicate notifications
        vendor_list = late_48h_df['vendor_name'].tolist()
        if vendor_list:
            admin_emails = late_48h_df['ContactEmail'].unique()
            for email in admin_emails:
                admin_row = late_48h_df[late_48h_df['ContactEmail'] == email].iloc[0]
                message = (f"🚨 Critical Late Submission Alert - {len(vendor_list)} vendor(s) have not "
                          f"submitted attendance for {day_before_yesterday.strftime('%B %d, %Y')} "
                          f"(48 hours overdue): {', '.join(vendor_list[:5])}{'...' if len(vendor_list) > 5 else ''}. "
                          f"Immediate administrative action required.")
                
                notifications.append({
                    'EmployeeID': admin_row['EmployeeID'],
                    'ContactEmail': admin_row['ContactEmail'],
                    'Message': message,
                    'Priority': 'Critical'
                })
        
        result_df = pd.DataFrame(notifications) if notifications else pd.DataFrame()
        
        self.create_clean_excel(result_df,
                              self.excel_folder / '09_late_submission_alerts.xlsx',
                              'LATE_SUBMISSION')
        conn.close()
        
    def update_all_notifications(self):
        """Update all 9 notification Excel files"""
        print("=" * 80)
        print("🚀 ATTENDO NOTIFICATION SYSTEM UPDATER - CLEAN VERSION")
        print("=" * 80)
        print(f"📅 Date: {self.today.strftime('%B %d, %Y')}")
        print(f"🕐 Time: {self.current_time.strftime('%H:%M:%S')}")
        print(f"📁 Output Folder: {self.excel_folder}")
        print("📋 Excel Format: EmployeeID | ContactEmail | Message | NotificationType | Priority")
        print("=" * 80)
        
        # Update each notification type
        self.update_01_daily_status_reminders()
        self.update_02_manager_summary_notifications() 
        self.update_03_manager_all_complete_notifications()
        self.update_04_mismatch_notifications()
        self.update_05_manager_feedback_notifications()
        self.update_06_monthly_report_notifications()
        self.update_07_admin_system_alerts()
        self.update_08_holiday_reminder_notifications()
        self.update_09_late_submission_alerts()
        
        print("\n" + "=" * 80)
        print("✅ CLEAN NOTIFICATION SYSTEM UPDATE COMPLETE!")
        print("🎯 All 9 Excel files updated with clean 5-column format")
        print("📧 Ready for Power Automate automation")
        print("=" * 80)

def main():
    """Main execution function"""
    updater = NotificationSystemUpdater()
    updater.update_all_notifications()

if __name__ == "__main__":
    main()
