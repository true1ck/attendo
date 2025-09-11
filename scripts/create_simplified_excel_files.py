#!/usr/bin/env python3
"""
Create Simplified Excel Files for Power Automate Network Folder
Creates 5-column Excel files with only: EmployeeID, ContactEmail, Message, NotificationType, Priority
"""

import pandas as pd
import os
from pathlib import Path

def create_simplified_excel_files():
    """Create simplified 5-column Excel files for all notification types"""
    
    # Base directories
    source_dir = Path("notification_configs")
    output_dir = Path("network_folder_simplified")
    output_dir.mkdir(exist_ok=True)
    
    # File mappings and data transformations
    notification_files = {
        '01_daily_status_reminders.xlsx': {
            'EmployeeID': 'Vendor_ID',
            'ContactEmail': 'Contact_Email',
            'Message': 'Custom_Message',
            'NotificationType': lambda df: 'DAILY_REMINDER',
            'Priority': 'Priority'
        },
        '02_manager_summary_notifications.xlsx': {
            'EmployeeID': 'Manager_ID', 
            'ContactEmail': 'Contact_Email',
            'Message': 'Custom_Message',
            'NotificationType': 'Notification_Type',
            'Priority': 'Priority'
        },
        '03_manager_all_complete_notifications.xlsx': {
            'EmployeeID': 'Manager_ID',
            'ContactEmail': 'Contact_Email', 
            'Message': 'Custom_Message',
            'NotificationType': lambda df: 'ALL_COMPLETE',
            'Priority': 'Priority'
        },
        '04_mismatch_notifications.xlsx': {
            'EmployeeID': lambda df: df.get('Vendor_ID', df.get('Manager_ID', '')),
            'ContactEmail': 'Contact_Email',
            'Message': 'Custom_Message', 
            'NotificationType': lambda df: 'MISMATCH_ALERT',
            'Priority': 'Priority'
        },
        '05_manager_feedback_notifications.xlsx': {
            'EmployeeID': 'Vendor_ID',
            'ContactEmail': 'Contact_Email',
            'Message': 'Custom_Message',
            'NotificationType': lambda df: 'FEEDBACK',
            'Priority': 'Priority'
        },
        '06_monthly_report_notifications.xlsx': {
            'EmployeeID': lambda df: df.get('Manager_ID', df.get('User_ID', '')),
            'ContactEmail': 'Contact_Email',
            'Message': 'Custom_Message',
            'NotificationType': lambda df: 'MONTHLY_REPORT',
            'Priority': 'Priority'
        },
        '07_admin_system_alerts.xlsx': {
            'EmployeeID': lambda df: 'ADMIN',
            'ContactEmail': 'Contact_Email', 
            'Message': 'Custom_Message',
            'NotificationType': lambda df: 'SYSTEM_ALERT',
            'Priority': 'Priority'
        },
        '08_holiday_reminder_notifications.xlsx': {
            'EmployeeID': 'User_ID',
            'ContactEmail': 'Contact_Email',
            'Message': 'Custom_Message', 
            'NotificationType': lambda df: 'HOLIDAY_REMINDER',
            'Priority': 'Priority'
        },
        '09_late_submission_alerts.xlsx': {
            'EmployeeID': 'Manager_ID',
            'ContactEmail': 'Contact_Email',
            'Message': 'Custom_Message',
            'NotificationType': lambda df: 'LATE_SUBMISSION',
            'Priority': 'Priority'
        },
        '10_billing_correction_notifications.xlsx': {
            'EmployeeID': lambda df: df.get('Manager_ID', 'ADMIN'),
            'ContactEmail': 'Contact_Email',
            'Message': 'Custom_Message',
            'NotificationType': lambda df: 'BILLING_CORRECTION', 
            'Priority': 'Priority'
        }
    }
    
    print("🚀 Creating simplified Excel files for Power Automate network folder...")
    print(f"📁 Output directory: {output_dir.absolute()}")
    
    created_files = []
    
    for filename, column_mapping in notification_files.items():
        source_path = source_dir / filename
        
        if not source_path.exists():
            print(f"⚠️  Skipping {filename} - file not found")
            continue
            
        try:
            # Read source Excel file
            df_source = pd.read_excel(source_path)
            print(f"📖 Reading {filename} ({len(df_source)} rows, {len(df_source.columns)} columns)")
            
            # Create simplified dataframe
            df_simplified = pd.DataFrame()
            
            for target_col, source_mapping in column_mapping.items():
                if callable(source_mapping):
                    # Dynamic value (lambda function)
                    df_simplified[target_col] = source_mapping(df_source)
                elif source_mapping in df_source.columns:
                    # Direct column mapping
                    df_simplified[target_col] = df_source[source_mapping]
                else:
                    # Fallback if column doesn't exist
                    print(f"   ⚠️  Column '{source_mapping}' not found, using placeholder")
                    df_simplified[target_col] = f"DATA_FROM_{source_mapping.upper()}"
            
            # Fill any NaN values
            df_simplified = df_simplified.fillna('')
            
            # Output filename (keep original name)
            output_path = output_dir / filename
            df_simplified.to_excel(output_path, index=False)
            
            created_files.append(output_path)
            print(f"✅ Created {output_path.name} ({len(df_simplified)} rows, 5 columns)")
            
            # Show sample data
            print(f"   📊 Sample data:")
            for i, row in df_simplified.head(2).iterrows():
                print(f"      Row {i+1}: {row['EmployeeID']} | {row['ContactEmail']} | {row['NotificationType']} | {row['Priority']}")
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {str(e)}")
    
    print(f"\n🎉 Successfully created {len(created_files)} simplified Excel files!")
    print(f"📁 All files saved in: {output_dir.absolute()}")
    
    # Create summary file
    summary_data = []
    for file_path in created_files:
        try:
            df = pd.read_excel(file_path)
            summary_data.append({
                'File': file_path.name,
                'Rows': len(df),
                'Notification_Types': df['NotificationType'].nunique(),
                'Sample_EmployeeID': df['EmployeeID'].iloc[0] if len(df) > 0 else '',
                'Sample_Priority': df['Priority'].iloc[0] if len(df) > 0 else ''
            })
        except:
            pass
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_path = output_dir / "00_SUMMARY_all_notification_files.xlsx"
        summary_df.to_excel(summary_path, index=False)
        print(f"📋 Created summary file: {summary_path.name}")
    
    return created_files

if __name__ == "__main__":
    create_simplified_excel_files()
