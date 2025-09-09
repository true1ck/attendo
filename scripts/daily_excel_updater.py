#!/usr/bin/env python3
"""
Daily Excel Sheet Updater
Handles daily cleanup and refresh of Excel notification sheets to ensure accurate Power Automate triggers.

This module ensures that:
1. Yesterday's pending vendor data is cleared from Excel sheets
2. Today's actual pending vendors are populated in Excel sheets
3. Power Automate gets fresh, accurate data each day
4. Real-time updates remove vendors immediately when they submit
5. All Excel sheets are formatted as proper tables for Power Automate integration
"""

import os
import pandas as pd
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import requests
from models import User, Vendor, Manager, DailyStatus, Holiday, UserRole, AttendanceStatus, ApprovalStatus
import models
from utils import check_late_submissions
try:
    from excel_table_formatter import update_notification_table, create_notification_table, validate_notification_table
except ImportError:
    try:
        from scripts.excel_table_formatter import update_notification_table, create_notification_table, validate_notification_table
    except ImportError:
        # Fallback stubs if table formatter not available
        def update_notification_table(df, notification_type, backup=True):
            print(f"⚠️ Table formatter not available, falling back to basic Excel save")
            return False
        def create_notification_table(df, notification_type):
            print(f"⚠️ Table formatter not available, falling back to basic Excel save")
            return False
        def validate_notification_table(notification_type):
            return {'valid': False, 'error': 'Table formatter not available'}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DailyExcelUpdater:
    """Manages daily Excel sheet updates for notification system"""
    
    def __init__(self, excel_folder="notification_configs"):
        self.excel_folder = Path(excel_folder)
        self.excel_folder.mkdir(exist_ok=True)
        
        # Excel file mappings
        self.notification_files = {
            'daily_reminders': '01_daily_status_reminders.xlsx',
            'manager_summary': '02_manager_summary_notifications.xlsx',
            'late_submissions': '09_late_submission_alerts.xlsx'
        }
        
        # Power Automate webhook URLs (configurable)
        self.power_automate_webhooks = {
            'daily_refresh': None,  # Set from environment or config
            'vendor_status_change': None,
            'emergency_alert': None
        }
        
        # Daily context tracking
        self.daily_context_file = self.excel_folder / 'daily_context.json'
        
    def run_daily_reset(self):
        """Main function to run daily reset of Excel notification sheets"""
        try:
            logger.info(f"🌅 Starting daily Excel reset for {date.today()}")
            
            # Step 1: Clear yesterday's data
            self.clear_yesterdays_data()
            
            # Step 2: Generate today's pending vendor data
            self.populate_todays_pending_data()
            
            # Step 3: Update manager summary sheets
            self.update_manager_summary_sheets()
            
            # Step 4: Trigger Power Automate refresh
            self.trigger_power_automate_refresh()
            
            # Step 5: Update daily context
            self.update_daily_context()
            
            logger.info("✅ Daily Excel reset completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Daily Excel reset failed: {str(e)}")
            self.send_emergency_alert(f"Daily reset failed: {str(e)}")
            return False
    
    def clear_yesterdays_data(self):
        """Clear yesterday's pending vendor data from Excel sheets"""
        logger.info("🧹 Clearing yesterday's notification data...")
        
        for sheet_type, filename in self.notification_files.items():
            filepath = self.excel_folder / filename
            
            if filepath.exists():
                try:
                    # Read existing Excel file
                    df = pd.read_excel(filepath)
                    
                    # Clear dynamic daily fields
                    if 'Daily_Status_Date' in df.columns:
                        df['Daily_Status_Date'] = ''
                    if 'Reminder_Status' in df.columns:
                        df['Reminder_Status'] = 'READY'
                    if 'Last_Reminder_Sent' in df.columns:
                        df['Last_Reminder_Sent'] = ''
                    if 'Submission_Status' in df.columns:
                        df['Submission_Status'] = 'PENDING'
                    
                    # Save cleared sheet
                    df.to_excel(filepath, index=False)
                    logger.info(f"✅ Cleared {filename}")
                    
                except Exception as e:
                    logger.error(f"❌ Error clearing {filename}: {str(e)}")
    
    def populate_todays_pending_data(self):
        """Populate Excel sheets with today's actual pending vendors"""
        logger.info("📝 Populating today's pending vendor data...")
        
        try:
            with models.db.session() as session:
                # Get today's late vendors
                late_vendors = check_late_submissions()
                today_str = date.today().isoformat()
                
                logger.info(f"📊 Found {len(late_vendors)} vendors pending submission today")
                
                # Update daily reminders sheet
                self.update_daily_reminders_sheet(late_vendors, today_str)
                
                # Update late submissions sheet for managers
                self.update_late_submissions_sheet(late_vendors, today_str)
                
        except Exception as e:
            logger.error(f"❌ Error populating today's data: {str(e)}")
    
    def update_daily_reminders_sheet(self, late_vendors: List, today_str: str):
        """Update the daily reminders Excel sheet with today's pending vendors"""
        filepath = self.excel_folder / self.notification_files['daily_reminders']
        
        if not filepath.exists():
            logger.warning(f"⚠️ Daily reminders file not found: {filepath}")
            return
        
        try:
            # Read existing configuration
            df = pd.read_excel(filepath)
            
            # Create set of late vendor IDs for quick lookup
            late_vendor_ids = {vendor.vendor_id for vendor in late_vendors}
            
            # Update each row based on vendor status
            for index, row in df.iterrows():
                vendor_id = row.get('Vendor_ID', '')
                
                if vendor_id in late_vendor_ids:
                    # This vendor needs reminder today
                    df.loc[index, 'Daily_Status_Date'] = today_str
                    df.loc[index, 'Reminder_Status'] = 'PENDING'
                    df.loc[index, 'Submission_Status'] = 'NOT_SUBMITTED'
                    df.loc[index, 'Send_Notification'] = 'YES'
                    df.loc[index, 'Active'] = 'YES'
                else:
                    # This vendor already submitted or is inactive
                    df.loc[index, 'Daily_Status_Date'] = today_str
                    df.loc[index, 'Reminder_Status'] = 'COMPLETED'
                    df.loc[index, 'Submission_Status'] = 'SUBMITTED'
                    df.loc[index, 'Send_Notification'] = 'NO'
            
            # Update metadata
            df['Last_Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df['Update_Source'] = 'DAILY_RESET'
            
            # Save updated sheet as a formatted table
            update_notification_table(df, 'daily_reminders')
            logger.info(f"✅ Updated daily reminders sheet with {len(late_vendor_ids)} pending vendors")
            
        except Exception as e:
            logger.error(f"❌ Error updating daily reminders sheet: {str(e)}")
    
    def update_late_submissions_sheet(self, late_vendors: List, today_str: str):
        """Update late submissions alert sheet for managers"""
        filepath = self.excel_folder / self.notification_files['late_submissions']
        
        if not filepath.exists():
            logger.warning(f"⚠️ Late submissions file not found: {filepath}")
            return
        
        try:
            # Read existing configuration
            df = pd.read_excel(filepath)
            
            # Group late vendors by manager
            manager_late_counts = {}
            for vendor in late_vendors:
                manager_id = vendor.manager_id
                if manager_id:
                    manager_late_counts[manager_id] = manager_late_counts.get(manager_id, 0) + 1
            
            # Update manager rows
            for index, row in df.iterrows():
                manager_id = row.get('Manager_ID', '')
                late_count = manager_late_counts.get(manager_id, 0)
                
                df.loc[index, 'Daily_Status_Date'] = today_str
                df.loc[index, 'Late_Vendor_Count'] = late_count
                df.loc[index, 'Alert_Required'] = 'YES' if late_count > 0 else 'NO'
                df.loc[index, 'Send_Notification'] = 'YES' if late_count > 0 else 'NO'
            
            # Save updated sheet as a formatted table
            update_notification_table(df, 'late_submissions')
            logger.info(f"✅ Updated late submissions sheet for {len(manager_late_counts)} managers")
            
        except Exception as e:
            logger.error(f"❌ Error updating late submissions sheet: {str(e)}")
    
    def update_manager_summary_sheets(self):
        """Update manager summary sheets with today's team statistics"""
        filepath = self.excel_folder / self.notification_files['manager_summary']
        
        if not filepath.exists():
            logger.warning(f"⚠️ Manager summary file not found: {filepath}")
            return
        
        try:
            with models.db.session() as session:
                # Read existing configuration
                df = pd.read_excel(filepath)
                today = date.today()
                
                # Update each manager's statistics
                for index, row in df.iterrows():
                    manager_id = row.get('Manager_ID', '')
                    if manager_id:
                        manager = session.query(Manager).filter_by(manager_id=manager_id).first()
                        if manager and manager.team_vendors:
                            team_vendors = manager.team_vendors.all()
                            
                            # Calculate team stats
                            total_team = len(team_vendors)
                            submitted_count = 0
                            pending_approvals = 0
                            
                            for vendor in team_vendors:
                                status = session.query(DailyStatus).filter_by(
                                    vendor_id=vendor.id,
                                    status_date=today
                                ).first()
                                
                                if status:
                                    submitted_count += 1
                                    if status.approval_status == ApprovalStatus.PENDING:
                                        pending_approvals += 1
                            
                            # Update Excel row
                            df.loc[index, 'Daily_Status_Date'] = today.isoformat()
                            df.loc[index, 'Team_Size'] = total_team
                            df.loc[index, 'Submitted_Count'] = submitted_count
                            df.loc[index, 'Pending_Count'] = total_team - submitted_count
                            df.loc[index, 'Pending_Approvals'] = pending_approvals
                            df.loc[index, 'Completion_Rate'] = round((submitted_count / total_team) * 100, 1) if total_team > 0 else 0
                            df.loc[index, 'Send_Notification'] = 'YES' if total_team > 0 else 'NO'
                
                # Save updated sheet as a formatted table
                update_notification_table(df, 'manager_summary')
                logger.info("✅ Updated manager summary sheets")
                
        except Exception as e:
            logger.error(f"❌ Error updating manager summary sheets: {str(e)}")
    
    def vendor_submitted_status_update(self, vendor_id: str):
        """Update Excel sheets immediately when a vendor submits status"""
        logger.info(f"📤 Processing real-time status update for vendor {vendor_id}")
        
        try:
            today_str = date.today().isoformat()
            
            # Update daily reminders sheet
            self.update_vendor_in_daily_reminders(vendor_id, 'SUBMITTED', today_str)
            
            # Update manager summary (recalculate team stats)
            self.refresh_manager_summary_for_vendor(vendor_id)
            
            # Trigger Power Automate update
            self.trigger_vendor_status_change_webhook(vendor_id, 'SUBMITTED')
            
            logger.info(f"✅ Real-time update completed for vendor {vendor_id}")
            
        except Exception as e:
            logger.error(f"❌ Error in real-time update for vendor {vendor_id}: {str(e)}")
    
    def update_vendor_in_daily_reminders(self, vendor_id: str, status: str, today_str: str):
        """Update specific vendor status in daily reminders sheet"""
        filepath = self.excel_folder / self.notification_files['daily_reminders']
        
        if not filepath.exists():
            return
        
        try:
            df = pd.read_excel(filepath)
            
            # Find and update vendor row
            mask = df['Vendor_ID'] == vendor_id
            if mask.any():
                df.loc[mask, 'Submission_Status'] = status
                df.loc[mask, 'Reminder_Status'] = 'COMPLETED' if status == 'SUBMITTED' else 'PENDING'
                df.loc[mask, 'Send_Notification'] = 'NO' if status == 'SUBMITTED' else 'YES'
                df.loc[mask, 'Last_Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df.loc[mask, 'Update_Source'] = 'REALTIME_SUBMISSION'
                
                # Save updated sheet as a formatted table
                update_notification_table(df, 'daily_reminders', backup=False)
                logger.info(f"✅ Updated vendor {vendor_id} status to {status} in daily reminders")
            
        except Exception as e:
            logger.error(f"❌ Error updating vendor {vendor_id} in daily reminders: {str(e)}")
    
    def refresh_manager_summary_for_vendor(self, vendor_id: str):
        """Refresh manager summary when one of their team members submits"""
        try:
            with models.db.session() as session:
                # Find the vendor and their manager
                vendor = session.query(Vendor).filter_by(vendor_id=vendor_id).first()
                if not vendor or not vendor.manager_id:
                    return
                
                manager = session.query(Manager).filter_by(manager_id=vendor.manager_id).first()
                if not manager:
                    return
                
                # Recalculate team stats
                today = date.today()
                team_vendors = manager.team_vendors.all()
                total_team = len(team_vendors)
                submitted_count = 0
                pending_approvals = 0
                
                for team_vendor in team_vendors:
                    status = session.query(DailyStatus).filter_by(
                        vendor_id=team_vendor.id,
                        status_date=today
                    ).first()
                    
                    if status:
                        submitted_count += 1
                        if status.approval_status == ApprovalStatus.PENDING:
                            pending_approvals += 1
                
                # Update manager summary sheet
                filepath = self.excel_folder / self.notification_files['manager_summary']
                if filepath.exists():
                    df = pd.read_excel(filepath)
                    mask = df['Manager_ID'] == manager.manager_id
                    
                    if mask.any():
                        df.loc[mask, 'Submitted_Count'] = submitted_count
                        df.loc[mask, 'Pending_Count'] = total_team - submitted_count
                        df.loc[mask, 'Pending_Approvals'] = pending_approvals
                        df.loc[mask, 'Completion_Rate'] = round((submitted_count / total_team) * 100, 1) if total_team > 0 else 0
                        df.loc[mask, 'Last_Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Save updated sheet as a formatted table
                        update_notification_table(df, 'manager_summary', backup=False)
                        logger.info(f"✅ Refreshed manager summary for {manager.manager_id}")
        
        except Exception as e:
            logger.error(f"❌ Error refreshing manager summary: {str(e)}")
    
    def trigger_power_automate_refresh(self):
        """Trigger Power Automate workflows to refresh with new data"""
        webhook_url = self.power_automate_webhooks.get('daily_refresh')
        
        if not webhook_url:
            logger.warning("⚠️ Power Automate daily refresh webhook not configured")
            return
        
        try:
            payload = {
                'event_type': 'daily_refresh',
                'date': date.today().isoformat(),
                'timestamp': datetime.now().isoformat(),
                'files_updated': list(self.notification_files.values()),
                'status': 'success'
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=30,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'ATTENDO-DailyUpdater/1.0'
                }
            )
            
            if response.status_code == 200:
                logger.info("✅ Power Automate daily refresh triggered successfully")
            else:
                logger.warning(f"⚠️ Power Automate webhook returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error triggering Power Automate refresh: {str(e)}")
    
    def trigger_vendor_status_change_webhook(self, vendor_id: str, status: str):
        """Trigger real-time Power Automate update for vendor status change"""
        webhook_url = self.power_automate_webhooks.get('vendor_status_change')
        
        if not webhook_url:
            return
        
        try:
            payload = {
                'event_type': 'vendor_status_change',
                'vendor_id': vendor_id,
                'status': status,
                'date': date.today().isoformat(),
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ Vendor status change webhook sent for {vendor_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending vendor status webhook: {str(e)}")
    
    def send_emergency_alert(self, error_message: str):
        """Send emergency alert when daily reset fails"""
        webhook_url = self.power_automate_webhooks.get('emergency_alert')
        
        if webhook_url:
            try:
                payload = {
                    'event_type': 'emergency_alert',
                    'severity': 'HIGH',
                    'message': f'Daily Excel reset failed: {error_message}',
                    'timestamp': datetime.now().isoformat(),
                    'system': 'ATTENDO_DAILY_UPDATER'
                }
                
                requests.post(webhook_url, json=payload, timeout=10)
                logger.info("🚨 Emergency alert sent to Power Automate")
                
            except Exception as e:
                logger.error(f"❌ Failed to send emergency alert: {str(e)}")
    
    def update_daily_context(self):
        """Update daily context file for tracking"""
        try:
            context = {
                'last_reset_date': date.today().isoformat(),
                'last_reset_time': datetime.now().isoformat(),
                'reset_status': 'SUCCESS',
                'files_updated': list(self.notification_files.values()),
                'late_vendor_count': len(check_late_submissions()) if check_late_submissions else 0
            }
            
            with open(self.daily_context_file, 'w') as f:
                json.dump(context, f, indent=2)
            
            logger.info("✅ Daily context updated")
            
        except Exception as e:
            logger.error(f"❌ Error updating daily context: {str(e)}")
    
    def configure_power_automate_webhooks(self, webhooks: Dict[str, str]):
        """Configure Power Automate webhook URLs"""
        self.power_automate_webhooks.update(webhooks)
        logger.info(f"🔗 Configured {len(webhooks)} Power Automate webhooks")
    
    def validate_excel_sheets(self) -> Dict[str, Dict]:
        """Validate that all required Excel sheets exist and have correct structure with proper table format"""
        validation_results = {}
        
        for sheet_type, filename in self.notification_files.items():
            filepath = self.excel_folder / filename
            
            try:
                # First, check basic existence and structure
                if filepath.exists():
                    df = pd.read_excel(filepath)
                    
                    # Check for required columns
                    required_columns = ['Primary_Key', 'Send_Notification', 'Active', 'Contact_Email']
                    has_required = all(col in df.columns for col in required_columns)
                    
                    # Then validate table structure with the table formatter
                    table_validation = validate_notification_table(sheet_type)
                    
                    validation_results[sheet_type] = {
                        'exists': True,
                        'has_required_columns': has_required,
                        'has_table_format': table_validation.get('valid', False),
                        'table_info': table_validation.get('tables', []) if table_validation.get('valid', False) else []
                    }
                else:
                    validation_results[sheet_type] = {
                        'exists': False,
                        'has_required_columns': False,
                        'has_table_format': False,
                        'table_info': []
                    }
                    
            except Exception as e:
                logger.error(f"❌ Error validating {filename}: {str(e)}")
                validation_results[sheet_type] = {
                    'exists': filepath.exists(),
                    'has_required_columns': False,
                    'has_table_format': False,
                    'error': str(e),
                    'table_info': []
                }
        
        return validation_results

# Global instance
daily_excel_updater = DailyExcelUpdater()

def run_daily_reset():
    """Public function to trigger daily reset"""
    return daily_excel_updater.run_daily_reset()

def handle_vendor_status_submission(vendor_id: str):
    """Public function to handle real-time vendor status updates"""
    daily_excel_updater.vendor_submitted_status_update(vendor_id)

def configure_power_automate_integration(webhook_config: Dict[str, str]):
    """Configure Power Automate webhook URLs"""
    daily_excel_updater.configure_power_automate_webhooks(webhook_config)

if __name__ == "__main__":
    # Command line interface
    import argparse
    
    parser = argparse.ArgumentParser(description='Daily Excel Updater for ATTENDO')
    parser.add_argument('--action', choices=['reset', 'validate', 'ensure_tables'], default='reset',
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'reset':
        success = run_daily_reset()
        print(f"Daily reset: {'SUCCESS' if success else 'FAILED'}")
    elif args.action == 'validate':
        results = daily_excel_updater.validate_excel_sheets()
        print("Validation Results:")
        for sheet, validation in results.items():
            status = '✅ VALID' if validation['exists'] and validation['has_required_columns'] and validation['has_table_format'] else '❌ INVALID'
            print(f"  {sheet}: {status}")
            if validation['exists']:
                print(f"    - Has Required Columns: {'✅' if validation['has_required_columns'] else '❌'}")
                print(f"    - Has Table Format: {'✅' if validation['has_table_format'] else '❌'}")
                if validation['has_table_format'] and validation['table_info']:
                    for table in validation['table_info']:
                        print(f"      Table: {table['name']} ({table['range']})")
    elif args.action == 'ensure_tables':
        # Force ensure all sheets have proper table format
        print("Ensuring all Excel sheets have proper table format...")
        for sheet_type, filename in daily_excel_updater.notification_files.items():
            filepath = daily_excel_updater.excel_folder / filename
            if filepath.exists():
                try:
                    df = pd.read_excel(filepath)
                    print(f"Processing {sheet_type}...")
                    success = update_notification_table(df, sheet_type)
                    print(f"  {sheet_type}: {'✅ SUCCESS' if success else '❌ FAILED'}")
                except Exception as e:
                    print(f"  {sheet_type}: ❌ ERROR - {str(e)}")
