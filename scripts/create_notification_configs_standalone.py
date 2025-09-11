#!/usr/bin/env python3
"""
Standalone script to create Excel configuration files for all notification types
Based on requirements from requirement_doc.html
This version works without database dependencies by using sample data
"""

import pandas as pd
import os
from datetime import datetime, time

def create_notification_excel_files():
    """Create Excel files for all notification types based on requirements"""
    
    # Ensure notification_configs directory exists
    config_dir = "notification_configs"
    os.makedirs(config_dir, exist_ok=True)
    
    # Use sample data since we're running standalone
    
    # 1. Daily Status Reminders (Every 3 hours to vendors)
    vendor_reminder_data = [
        {
            'Primary_Key': 'VENDOR_V001',
            'Contact_Email': 'vendor1@company.com',
            'Contact_Name': 'John Doe',
            'Vendor_ID': 'V001',
            'Department': 'MTB_WCS_MSE7_MS1',
            'Company': 'ABC Solutions',
            'Manager_ID': 'M001',
            'Send_Notification': 'YES',
            'Reminder_Interval_Hours': 3,
            'Start_Time': '09:00',
            'End_Time': '18:00',
            'Max_Reminders_Per_Day': 4,
            'Weekdays_Only': 'YES',
            'Exclude_Holidays': 'YES',
            'Custom_Message': 'Please submit your daily attendance status',
            'Teams_Channel': '',
            'Phone_Number': '+1234567890',
            'Notification_Method': 'TEAMS,EMAIL',
            'Priority': 'MEDIUM',
            'Active': 'YES',
            'Created_Date': datetime.now().strftime('%Y-%m-%d'),
            'Last_Modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    df_vendor_reminders = pd.DataFrame(vendor_reminder_data)
    df_vendor_reminders.to_excel(f"{config_dir}/01_daily_status_reminders.xlsx", index=False)
    
    # 2. Manager Summary Notifications (12 PM, 2 PM)
    manager_summary_data = [
        {
            'Primary_Key': 'MGR_SUMMARY_M001',
            'Contact_Email': 'manager1@company.com',
            'Contact_Name': 'Jane Smith',
            'Manager_ID': 'M001',
            'Department': 'Engineering',
            'Team_Name': 'Team Alpha',
            'Send_Notification': 'YES',
            'Notification_Times': '12:00,14:00',
            'Include_Team_Stats': 'YES',
            'Include_Individual_Status': 'YES',
            'Include_Pending_Count': 'YES',
            'Weekdays_Only': 'YES',
            'Exclude_Holidays': 'YES',
            'Custom_Message': 'Team attendance summary',
            'Teams_Channel': 'team_m001',
            'Phone_Number': '+1234567891',
            'Notification_Method': 'TEAMS,EMAIL',
            'Priority': 'HIGH',
            'Active': 'YES',
            'Created_Date': datetime.now().strftime('%Y-%m-%d'),
            'Last_Modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    df_manager_summary = pd.DataFrame(manager_summary_data)
    df_manager_summary.to_excel(f"{config_dir}/02_manager_summary_notifications.xlsx", index=False)
    
    # 3. Manager All-Complete Notifications
    manager_complete_data = [
        {
            'Primary_Key': 'MGR_COMPLETE_M001',
            'Contact_Email': 'manager1@company.com',
            'Contact_Name': 'Jane Smith',
            'Manager_ID': 'M001',
            'Department': 'Engineering',
            'Team_Name': 'Team Alpha',
            'Send_Notification': 'YES',
            'Trigger_Condition': 'ALL_TEAM_SUBMITTED',
            'Include_Completion_Stats': 'YES',
            'Include_Next_Actions': 'YES',
            'Auto_Approve_Option': 'NO',
            'Custom_Message': 'All team members have submitted their status',
            'Teams_Channel': 'team_m001',
            'Phone_Number': '+1234567891',
            'Notification_Method': 'TEAMS,EMAIL',
            'Priority': 'HIGH',
            'Active': 'YES',
            'Created_Date': datetime.now().strftime('%Y-%m-%d'),
            'Last_Modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    df_manager_complete = pd.DataFrame(manager_complete_data)
    df_manager_complete.to_excel(f"{config_dir}/03_manager_all_complete_notifications.xlsx", index=False)
    
    # 4. Mismatch Notifications
    mismatch_notification_data = [
        {
            'Primary_Key': 'MISMATCH_MGR_M001',
            'Contact_Email': 'manager1@company.com',
            'Contact_Name': 'Jane Smith',
            'Role': 'MANAGER',
            'Manager_ID': 'M001',
            'Department': 'Engineering',
            'Send_Notification': 'YES',
            'Mismatch_Types': 'SWIPE_WEB,WFH_SWIPE,LEAVE_SWIPE',
            'Include_Vendor_Details': 'YES',
            'Include_Explanation_Required': 'YES',
            'Auto_Escalate_Days': 3,
            'Custom_Message': 'New attendance mismatches found for your team',
            'Teams_Channel': 'team_m001',
            'Phone_Number': '+1234567891',
            'Notification_Method': 'TEAMS,EMAIL',
            'Priority': 'HIGH',
            'Active': 'YES',
            'Created_Date': datetime.now().strftime('%Y-%m-%d'),
            'Last_Modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    df_mismatch = pd.DataFrame(mismatch_notification_data)
    df_mismatch.to_excel(f"{config_dir}/04_mismatch_notifications.xlsx", index=False)
    
    # 5. Manager Feedback Notifications (Rejections/Corrections)
    feedback_notification_data = [
        {
            'Primary_Key': 'FEEDBACK_V001',
            'Contact_Email': 'vendor1@company.com',
            'Contact_Name': 'John Doe',
            'Vendor_ID': 'V001',
            'Department': 'MTB_WCS_MSE7_MS1',
            'Manager_ID': 'M001',
            'Send_Notification': 'YES',
            'Feedback_Types': 'REJECTION,CORRECTION_REQUEST,APPROVAL',
            'Include_Manager_Comments': 'YES',
            'Include_Corrective_Actions': 'YES',
            'Include_Deadline': 'YES',
            'Response_Required_Hours': 24,
            'Custom_Message': 'Manager feedback on your attendance submission',
            'Teams_Channel': '',
            'Phone_Number': '+1234567890',
            'Notification_Method': 'TEAMS,EMAIL,SMS',
            'Priority': 'HIGH',
            'Active': 'YES',
            'Created_Date': datetime.now().strftime('%Y-%m-%d'),
            'Last_Modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    df_feedback = pd.DataFrame(feedback_notification_data)
    df_feedback.to_excel(f"{config_dir}/05_manager_feedback_notifications.xlsx", index=False)
    
    # 6. Monthly Report Notifications
    report_notification_data = [
        {
            'Primary_Key': 'REPORT_ADMIN_1',
            'Contact_Email': 'admin@company.com',
            'Contact_Name': 'System Administrator',
            'Role': 'ADMIN',
            'Manager_ID': '',
            'Department': 'ADMINISTRATION',
            'Send_Notification': 'YES',
            'Report_Types': 'MONTHLY_ALL,SYSTEM_SUMMARY,AUDIT_REPORT,BILLING_REPORT',
            'Auto_Generate_Monthly': 'YES',
            'Generation_Day': 1,
            'Include_Excel_Attachment': 'YES',
            'Include_PDF_Summary': 'YES',
            'Include_Charts': 'YES',
            'Custom_Message': 'Monthly system-wide attendance report',
            'Teams_Channel': 'admin_channel',
            'Phone_Number': '+1234567892',
            'Notification_Method': 'TEAMS,EMAIL',
            'Priority': 'HIGH',
            'Active': 'YES',
            'Created_Date': datetime.now().strftime('%Y-%m-%d'),
            'Last_Modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    df_reports = pd.DataFrame(report_notification_data)
    df_reports.to_excel(f"{config_dir}/06_monthly_report_notifications.xlsx", index=False)
    
    # 7. Admin System Alerts
    admin_alert_data = [
        {
            'Primary_Key': 'ADMIN_ALERT_1',
            'Contact_Email': 'admin@company.com',
            'Contact_Name': 'System Administrator',
            'Role': 'ADMIN',
            'Send_Notification': 'YES',
            'Alert_Types': 'SYSTEM_ERROR,DATABASE_ISSUE,IMPORT_FAILURE,HIGH_MISMATCHES,SECURITY_ALERT',
            'Severity_Levels': 'HIGH,CRITICAL',
            'Include_System_Stats': 'YES',
            'Include_Error_Details': 'YES',
            'Include_Recommended_Actions': 'YES',
            'Auto_Escalate_Minutes': 30,
            'Custom_Message': 'System alert requiring immediate attention',
            'Teams_Channel': 'admin_alerts',
            'Phone_Number': '+1234567892',
            'Notification_Method': 'TEAMS,EMAIL,SMS',
            'Priority': 'CRITICAL',
            'Active': 'YES',
            'Created_Date': datetime.now().strftime('%Y-%m-%d'),
            'Last_Modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    df_admin_alerts = pd.DataFrame(admin_alert_data)
    df_admin_alerts.to_excel(f"{config_dir}/07_admin_system_alerts.xlsx", index=False)
    
    # 8. Holiday Reminder Notifications
    holiday_reminder_data = [
        {
            'Primary_Key': 'HOLIDAY_ALL',
            'Contact_Email': 'all@company.com',
            'Contact_Name': 'All Users',
            'Role': 'ALL',
            'User_ID': 'ALL',
            'Department': 'ALL',
            'Send_Notification': 'YES',
            'Advance_Notice_Days': 7,
            'Include_Holiday_Calendar': 'YES',
            'Include_Working_Day_Info': 'YES',
            'Notification_Times': '09:00',
            'Weekend_Notifications': 'NO',
            'Custom_Message': 'Upcoming holiday notification',
            'Teams_Channel': 'general',
            'Phone_Number': '',
            'Notification_Method': 'TEAMS,EMAIL',
            'Priority': 'LOW',
            'Active': 'YES',
            'Created_Date': datetime.now().strftime('%Y-%m-%d'),
            'Last_Modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    df_holiday_reminders = pd.DataFrame(holiday_reminder_data)
    df_holiday_reminders.to_excel(f"{config_dir}/08_holiday_reminder_notifications.xlsx", index=False)
    
    # 9. Late Submission Alert Notifications
    late_submission_data = [
        {
            'Primary_Key': 'LATE_MGR_M001',
            'Contact_Email': 'manager1@company.com',
            'Contact_Name': 'Jane Smith',
            'Role': 'MANAGER',
            'Manager_ID': 'M001',
            'Department': 'Engineering',
            'Send_Notification': 'YES',
            'Alert_After_Hours': 24,
            'Include_Late_History': 'YES',
            'Include_Team_Statistics': 'YES',
            'Include_Individual_Details': 'YES',
            'Escalate_After_Days': 3,
            'Custom_Message': 'Late submission alert for team members',
            'Teams_Channel': 'team_m001',
            'Phone_Number': '+1234567891',
            'Notification_Method': 'TEAMS,EMAIL',
            'Priority': 'MEDIUM',
            'Active': 'YES',
            'Created_Date': datetime.now().strftime('%Y-%m-%d'),
            'Last_Modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    df_late_submissions = pd.DataFrame(late_submission_data)
    df_late_submissions.to_excel(f"{config_dir}/09_late_submission_alerts.xlsx", index=False)
    
    # 10. Billing Correction Notifications
    billing_correction_data = [
        {
            'Primary_Key': 'BILLING_ADMIN_1',
            'Contact_Email': 'admin@company.com',
            'Contact_Name': 'System Administrator',
            'Role': 'ADMIN',
            'Manager_ID': '',
            'Department': 'ADMINISTRATION',
            'Send_Notification': 'YES',
            'Correction_Types': 'ALL',
            'Include_Financial_Details': 'YES',
            'Include_Justification': 'YES',
            'Include_Approval_History': 'YES',
            'Require_Acknowledgment': 'YES',
            'Custom_Message': 'System billing correction notification',
            'Teams_Channel': 'admin_billing',
            'Phone_Number': '+1234567892',
            'Notification_Method': 'TEAMS,EMAIL',
            'Priority': 'CRITICAL',
            'Active': 'YES',
            'Created_Date': datetime.now().strftime('%Y-%m-%d'),
            'Last_Modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    df_billing_corrections = pd.DataFrame(billing_correction_data)
    df_billing_corrections.to_excel(f"{config_dir}/10_billing_correction_notifications.xlsx", index=False)
    
    print("✅ Created 10 notification configuration Excel files:")
    print("1. 01_daily_status_reminders.xlsx")
    print("2. 02_manager_summary_notifications.xlsx")
    print("3. 03_manager_all_complete_notifications.xlsx")
    print("4. 04_mismatch_notifications.xlsx")
    print("5. 05_manager_feedback_notifications.xlsx")
    print("6. 06_monthly_report_notifications.xlsx")
    print("7. 07_admin_system_alerts.xlsx")
    print("8. 08_holiday_reminder_notifications.xlsx")
    print("9. 09_late_submission_alerts.xlsx")
    print("10. 10_billing_correction_notifications.xlsx")
    
    return True

if __name__ == "__main__":
    create_notification_excel_files()
