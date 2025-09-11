#!/usr/bin/env python3
"""
Power Automate Compatible Excel Refresh
Updates Excel notification sheets with proper Power Automate table structure
"""

import sqlite3
import pandas as pd
from datetime import datetime, date
import os
from pathlib import Path
import shutil

# Import from same scripts directory
try:
    from excel_table_formatter import update_notification_table, save_dataframe_as_table, excel_table_formatter
except ImportError:
    try:
        from scripts.excel_table_formatter import update_notification_table, save_dataframe_as_table, excel_table_formatter
    except ImportError:
        # If not available, provide stubs
        excel_table_formatter = None
        def update_notification_table(*args, **kwargs):
            return False
        def save_dataframe_as_table(df, file_path, table_name='Table1', sheet_name='Sheet1'):
            df.to_excel(file_path, sheet_name=sheet_name, index=False)
            return True

def power_automate_excel_refresh():
    """Refresh Excel files with Power Automate compatible format"""
    
    db_path = 'vendor_timesheet.db'
    excel_folder = Path('notification_configs')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    print("=" * 100)
    print("🔄 POWER AUTOMATE COMPATIBLE EXCEL REFRESH")
    print("=" * 100)
    print(f"📅 Date: {date.today()}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    conn = sqlite3.connect(db_path)
    
    try:
        today = date.today().isoformat()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Step 1: Get pending vendors from database
        print("📊 Step 1: Querying database for pending vendors...")
        
        vendor_query = """
        SELECT 
            v.vendor_id,
            v.full_name,
            u.email,
            v.department,
            v.company,
            v.manager_id,
            m.full_name as manager_name,
            m.email as manager_email,
            CASE 
                WHEN ds.id IS NULL THEN 'PENDING_SUBMISSION'
                WHEN ds.approval_status = 'REJECTED' THEN 'REJECTED'
                ELSE 'COMPLETED'
            END as notification_status
        FROM vendors v
        JOIN users u ON v.user_id = u.id
        LEFT JOIN managers m ON v.manager_id = m.manager_id
        LEFT JOIN daily_statuses ds ON v.id = ds.vendor_id AND ds.status_date = ?
        WHERE u.is_active = 1
        ORDER BY v.vendor_id
        """
        
        vendors_df = pd.read_sql_query(vendor_query, conn, params=[today])
        pending_vendors = vendors_df[vendors_df['notification_status'].isin(['PENDING_SUBMISSION', 'REJECTED'])].copy()
        
        print(f"✅ Found {len(vendors_df)} total active vendors")
        print(f"⚠️  Found {len(pending_vendors)} vendors needing notifications")
        
        # Step 2: Update Daily Status Reminders with Power Automate format
        print(f"\n📋 Step 2: Creating Power Automate compatible daily reminders...")
        
        daily_reminders_file = excel_folder / '01_daily_status_reminders.xlsx'
        
        if len(pending_vendors) > 0:
            # Create Power Automate compatible structure based on your image
            daily_data = []
            for i, (_, vendor) in enumerate(pending_vendors.iterrows(), 1):
                daily_data.append({
                    'Primary_Key': f"VENDOR_{vendor['vendor_id']}_{today.replace('-', '')}",
                    'Contact_Email': vendor['email'],
                    'Vendor_Name': vendor['full_name'], 
                    'Vendor_ID': vendor['vendor_id'],
                    'Department': vendor['department'] if pd.notna(vendor['department']) else "",
                    'Company': vendor['company'] if pd.notna(vendor['company']) else "",
                    'Manager_ID': vendor['manager_id'] if pd.notna(vendor['manager_id']) else "",
                    'Notification_Interval_Hours': 3,
                    'Start_Time': '09:00',
                    'End_Time': '18:00',
                    'Reminders_Sent_Today': 0,
                    'Weekdays_Only': 'YES',
                    'Include_Holidays': 'NO',
                    'Notification_Message': f"Please submit your daily attendance status - {vendor['full_name']}",
                    'Teams_Channel': f"vendor_{vendor['vendor_id'].lower()}",
                    'Phone_Number': None,
                    'Notification_Method': 'EMAIL,TEAMS',
                    'Priority': 'MEDIUM',
                    'Active': 'YES',
                    'Created_Date': today,
                    'Last_Updated': current_time
                })
            
            df_daily = pd.DataFrame(daily_data)
        else:
            # Empty structure for no pending vendors
            df_daily = pd.DataFrame(columns=[
                'Primary_Key', 'Contact_Email', 'Vendor_Name', 'Vendor_ID', 'Department', 
                'Company', 'Manager_ID', 'Notification_Interval_Hours', 'Start_Time', 
                'End_Time', 'Reminders_Sent_Today', 'Weekdays_Only', 'Include_Holidays', 
                'Notification_Message', 'Teams_Channel', 'Phone_Number', 'Notification_Method',
                'Priority', 'Active', 'Created_Date', 'Last_Updated'
            ])
        
        # Write daily reminders file with proper table formatting
        try:
            
            # Save as Excel table for Power Automate compatibility
            if excel_table_formatter:
                success = excel_table_formatter.create_excel_table_from_dataframe(
                    df_daily, str(daily_reminders_file), 'daily_reminders'
                )
                if success:
                    print(f"✅ Updated {daily_reminders_file} with {len(df_daily)} vendors (Power Automate table format)")
                else:
                    print(f"❌ Failed to update {daily_reminders_file} with table format")
            else:
                save_dataframe_as_table(df_daily, str(daily_reminders_file), 
                                      table_name='DailyStatusReminders', 
                                      sheet_name='Daily_Reminders')
                print(f"✅ Updated {daily_reminders_file} with {len(df_daily)} vendors (basic format)")
            
        except Exception as e:
            print(f"❌ Error updating daily reminders: {str(e)}")
            return False
        
        # Step 3: Update Manager Summary with Power Automate format
        print(f"\n👔 Step 3: Creating Power Automate compatible manager summary...")
        
        manager_summary_file = excel_folder / '02_manager_summary_notifications.xlsx'
        
        if len(pending_vendors) > 0:
            # Group by manager
            manager_groups = pending_vendors.groupby(['manager_id', 'manager_name', 'manager_email']).agg({
                'vendor_id': 'count'
            }).rename(columns={'vendor_id': 'pending_count'}).reset_index()
            
            # Create manager data with Power Automate format
            manager_data = []
            for _, manager in manager_groups.iterrows():
                if pd.isna(manager['manager_id']) or not manager['manager_id']:
                    continue
                    
                manager_data.append({
                    'Primary_Key': f"MGR_SUMMARY_{manager['manager_id']}_{today.replace('-', '')}",
                    'Contact_Email': manager['manager_email'],
                    'Contact_Name': manager['manager_name'],
                    'Manager_ID': manager['manager_id'],
                    'Department': 'Various',  # Could be enhanced to get actual dept
                    'Team_Name': f"Team {manager['manager_id']}",
                    'Pending_Submissions': int(manager['pending_count']),
                    'Send_Notification': 'YES',
                    'Notification_Type': 'TEAM_SUMMARY',
                    'Notification_Time': '12:00,14:00',
                    'Include_Vendor_List': 'YES',
                    'Escalation_Required': 'YES' if manager['pending_count'] >= 5 else 'NO',
                    'Custom_Message': f"Team Update: {int(manager['pending_count'])} team members need to submit their daily status",
                    'Teams_Channel': f"team_{manager['manager_id'].lower()}",
                    'Phone_Number': None,
                    'Notification_Method': 'EMAIL,TEAMS',
                    'Priority': 'HIGH' if manager['pending_count'] >= 5 else 'MEDIUM',
                    'Active': 'YES',
                    'Created_Date': today,
                    'Last_Modified': current_time
                })
            
            df_managers = pd.DataFrame(manager_data)
        else:
            # Empty manager summary
            df_managers = pd.DataFrame(columns=[
                'Primary_Key', 'Contact_Email', 'Contact_Name', 'Manager_ID', 'Department',
                'Team_Name', 'Pending_Submissions', 'Send_Notification', 'Notification_Type',
                'Notification_Time', 'Include_Vendor_List', 'Escalation_Required', 'Custom_Message',
                'Teams_Channel', 'Phone_Number', 'Notification_Method', 'Priority', 'Active',
                'Created_Date', 'Last_Modified'
            ])
        
        # Write manager summary file with proper table formatting
        try:
            
            # Save as Excel table for Power Automate compatibility
            if excel_table_formatter:
                success = excel_table_formatter.create_excel_table_from_dataframe(
                    df_managers, str(manager_summary_file), 'manager_summary'
                )
                if success:
                    print(f"✅ Updated {manager_summary_file} with {len(df_managers)} managers (Power Automate table format)")
                else:
                    print(f"❌ Failed to update {manager_summary_file} with table format")
            else:
                save_dataframe_as_table(df_managers, str(manager_summary_file),
                                      table_name='ManagerSummaryNotifications',
                                      sheet_name='Manager_Summary')
                print(f"✅ Updated {manager_summary_file} with {len(df_managers)} managers (basic format)")
            
        except Exception as e:
            print(f"❌ Error updating manager summary: {str(e)}")
        
        # Step 4: Update Late Submissions with Power Automate format
        print(f"\n⚠️  Step 4: Creating Power Automate compatible late submissions...")
        
        late_submissions_file = excel_folder / '09_late_submission_alerts.xlsx'
        late_vendors = pending_vendors[pending_vendors['notification_status'] == 'PENDING_SUBMISSION']
        
        if len(late_vendors) > 0:
            # Create late submission alerts
            late_data = []
            for _, vendor in late_vendors.iterrows():
                late_data.append({
                    'Primary_Key': f"LATE_{vendor['vendor_id']}_{today.replace('-', '')}",
                    'Contact_Email': vendor['email'],
                    'Vendor_Name': vendor['full_name'],
                    'Vendor_ID': vendor['vendor_id'],
                    'Manager_ID': vendor['manager_id'] if pd.notna(vendor['manager_id']) else "",
                    'Manager_Name': vendor['manager_name'] if pd.notna(vendor['manager_name']) else "",
                    'Manager_Email': vendor['manager_email'] if pd.notna(vendor['manager_email']) else "",
                    'Alert_Type': 'LATE_SUBMISSION',
                    'Send_Alert': 'YES',
                    'Hours_Since_Deadline': 24,
                    'Escalation_Level': 'HIGH',
                    'Include_Manager_CC': 'YES',
                    'Urgent_Flag': 'YES',
                    'Message': f"🚨 URGENT: Daily attendance submission missing - {vendor['full_name']}",
                    'Teams_Channel': f"alerts_{vendor['manager_id'].lower()}" if pd.notna(vendor['manager_id']) else "general_alerts",
                    'Phone_Number': None,
                    'Notification_Method': 'EMAIL,TEAMS,SMS',
                    'Priority': 'CRITICAL',
                    'Active': 'YES',
                    'Date': today,
                    'Time_Generated': datetime.now().strftime('%H:%M:%S'),
                    'Status': 'ACTIVE',
                    'Last_Updated': current_time
                })
            
            df_late = pd.DataFrame(late_data)
        else:
            # Empty late submissions
            df_late = pd.DataFrame(columns=[
                'Primary_Key', 'Contact_Email', 'Vendor_Name', 'Vendor_ID', 'Manager_ID',
                'Manager_Name', 'Manager_Email', 'Alert_Type', 'Send_Alert', 'Hours_Since_Deadline',
                'Escalation_Level', 'Include_Manager_CC', 'Urgent_Flag', 'Message', 'Teams_Channel',
                'Phone_Number', 'Notification_Method', 'Priority', 'Active', 'Date', 
                'Time_Generated', 'Status', 'Last_Updated'
            ])
        
        # Write late submissions file with proper table formatting
        try:
            
            # Save as Excel table for Power Automate compatibility
            if excel_table_formatter:
                success = excel_table_formatter.create_excel_table_from_dataframe(
                    df_late, str(late_submissions_file), 'late_submissions'
                )
                if success:
                    print(f"✅ Updated {late_submissions_file} with {len(df_late)} late submissions (Power Automate table format)")
                else:
                    print(f"❌ Failed to update {late_submissions_file} with table format")
            else:
                save_dataframe_as_table(df_late, str(late_submissions_file),
                                      table_name='LateSubmissionAlerts',
                                      sheet_name='Late_Submissions')
                print(f"✅ Updated {late_submissions_file} with {len(df_late)} late submissions (basic format)")
            
        except Exception as e:
            print(f"❌ Error updating late submissions: {str(e)}")
        
        # Step 5: Summary Report
        print(f"\n📊 POWER AUTOMATE REFRESH SUMMARY")
        print("=" * 70)
        print(f"📅 Date: {today}")
        print(f"🕐 Completed at: {datetime.now().strftime('%H:%M:%S')}")
        print(f"👥 Total Active Vendors: {len(vendors_df)}")
        print(f"⚠️  Vendors Needing Notifications: {len(pending_vendors)}")
        print(f"👔 Managers Receiving Alerts: {len(df_managers)}")
        print(f"🚨 Late Submission Alerts: {len(df_late)}")
        
        if len(pending_vendors) > 0:
            print(f"\n📋 Power Automate will process these vendors:")
            for _, vendor in pending_vendors.head(10).iterrows():
                status_icon = "⏳" if vendor['notification_status'] == 'PENDING_SUBMISSION' else "❌"
                print(f"   {status_icon} {vendor['vendor_id']}: {vendor['full_name']} ({vendor['email']})")
            if len(pending_vendors) > 10:
                print(f"   ... and {len(pending_vendors) - 10} more vendors")
        
        print(f"\n✅ Excel files are now Power Automate compatible!")
        print(f"🔗 Power Automate can use these files for accurate notifications")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during refresh: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()
    
    print("=" * 100)

if __name__ == "__main__":
    power_automate_excel_refresh()
