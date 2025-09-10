#!/usr/bin/env python3
"""
Database Viewer Script for Vendor Timesheet Tool
This script provides comprehensive viewing of all database tables and their contents.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, MetaData, inspect, text
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate
import pandas as pd
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init(autoreset=True)

# Ensure project root (parent of scripts) is on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

# Import models
from models import (
    db, User, Vendor, Manager, DailyStatus, SwipeRecord, 
    Holiday, MismatchRecord, NotificationLog, AuditLog, 
    SystemConfiguration, LeaveRecord, WFHRecord, EmailNotificationLog,
    UserRole, AttendanceStatus, ApprovalStatus
)

# Database configuration
DATABASE_PATH = os.path.abspath("vendor_timesheet.db")
DATABASE_URI = f'sqlite:///{DATABASE_PATH}'

class DatabaseViewer:
    """Comprehensive database viewer for the vendor timesheet application"""
    
    def __init__(self):
        """Initialize database connection and session"""
        self.engine = create_engine(DATABASE_URI)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        self.inspector = inspect(self.engine)
        
    def get_table_stats(self):
        """Get statistics for all tables"""
        stats = []
        for table_name in self.inspector.get_table_names():
            try:
                count = self.session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                stats.append({
                    'Table': table_name,
                    'Records': count
                })
            except Exception as e:
                stats.append({
                    'Table': table_name,
                    'Records': f"Error: {str(e)}"
                })
        return stats
    
    def print_header(self, title):
        """Print a formatted header"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.YELLOW}{title.center(80)}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    
    def print_subheader(self, title):
        """Print a formatted subheader"""
        print(f"\n{Fore.GREEN}{'-'*60}")
        print(f"{Fore.GREEN}{title}")
        print(f"{Fore.GREEN}{'-'*60}{Style.RESET_ALL}")
    
    def view_users(self):
        """Display all users with their roles and status"""
        self.print_subheader("USERS TABLE")
        users = self.session.query(User).all()
        
        if not users:
            print(f"{Fore.YELLOW}No users found in database.{Style.RESET_ALL}")
            return
            
        data = []
        for user in users:
            data.append({
                'ID': user.id,
                'Username': user.username,
                'Email': user.email,
                'Role': user.role.value if user.role else 'N/A',
                'Active': '✓' if user.is_active else '✗',
                'Created': user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else 'N/A',
                'Last Login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        print(f"\nTotal Users: {len(users)}")
        
        # Role breakdown
        role_counts = {}
        for user in users:
            role = user.role.value if user.role else 'None'
            role_counts[role] = role_counts.get(role, 0) + 1
        
        print("\nRole Distribution:")
        for role, count in role_counts.items():
            print(f"  • {role.capitalize()}: {count}")
    
    def view_vendors(self):
        """Display all vendor profiles"""
        self.print_subheader("VENDORS TABLE")
        vendors = self.session.query(Vendor).all()
        
        if not vendors:
            print(f"{Fore.YELLOW}No vendors found in database.{Style.RESET_ALL}")
            return
            
        data = []
        for vendor in vendors:
            # Get associated user
            user = self.session.query(User).filter_by(id=vendor.user_id).first()
            
            data.append({
                'ID': vendor.id,
                'Vendor ID': vendor.vendor_id,
                'Full Name': vendor.full_name,
                'Username': user.username if user else 'N/A',
                'Department': vendor.department[:30] + '...' if len(vendor.department) > 30 else vendor.department,
                'Company': vendor.company,
                'Band': vendor.band,
                'Location': vendor.location,
                'Manager ID': vendor.manager_id or 'None'
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        print(f"\nTotal Vendors: {len(vendors)}")
        
        # Company breakdown
        company_counts = {}
        for vendor in vendors:
            company_counts[vendor.company] = company_counts.get(vendor.company, 0) + 1
        
        print("\nCompany Distribution:")
        for company, count in company_counts.items():
            print(f"  • {company}: {count}")
    
    def view_managers(self):
        """Display all manager profiles"""
        self.print_subheader("MANAGERS TABLE")
        managers = self.session.query(Manager).all()
        
        if not managers:
            print(f"{Fore.YELLOW}No managers found in database.{Style.RESET_ALL}")
            return
            
        data = []
        for manager in managers:
            # Get associated user
            user = self.session.query(User).filter_by(id=manager.user_id).first()
            # Count team members
            team_count = self.session.query(Vendor).filter_by(manager_id=manager.manager_id).count()
            
            data.append({
                'ID': manager.id,
                'Manager ID': manager.manager_id,
                'Full Name': manager.full_name,
                'Username': user.username if user else 'N/A',
                'Department': manager.department[:30] + '...' if len(manager.department) > 30 else manager.department,
                'Team Name': manager.team_name or 'N/A',
                'Email': manager.email or 'N/A',
                'Phone': manager.phone or 'N/A',
                'Team Size': team_count
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        print(f"\nTotal Managers: {len(managers)}")
    
    def view_daily_statuses(self, limit=20):
        """Display recent daily status submissions"""
        self.print_subheader(f"DAILY STATUSES (Last {limit} entries)")
        statuses = self.session.query(DailyStatus).order_by(DailyStatus.submitted_at.desc()).limit(limit).all()
        
        if not statuses:
            print(f"{Fore.YELLOW}No daily statuses found in database.{Style.RESET_ALL}")
            return
            
        data = []
        for status in statuses:
            vendor = self.session.query(Vendor).filter_by(id=status.vendor_id).first()
            
            data.append({
                'ID': status.id,
                'Vendor': vendor.vendor_id if vendor else 'N/A',
                'Date': status.status_date.strftime('%Y-%m-%d') if status.status_date else 'N/A',
                'Status': status.status.value if status.status else 'N/A',
                'Location': status.location or 'N/A',
                'Approval': status.approval_status.value if status.approval_status else 'N/A',
                'Submitted': status.submitted_at.strftime('%Y-%m-%d %H:%M') if status.submitted_at else 'N/A'
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        
        # Get total count
        total_count = self.session.query(DailyStatus).count()
        print(f"\nShowing {len(statuses)} of {total_count} total daily statuses")
        
        # Status breakdown
        status_counts = {}
        all_statuses = self.session.query(DailyStatus).all()
        for s in all_statuses:
            if s.status:
                status_val = s.status.value
                status_counts[status_val] = status_counts.get(status_val, 0) + 1
        
        print("\nStatus Distribution (All Records):")
        for status, count in sorted(status_counts.items()):
            print(f"  • {status}: {count}")
    
    def view_swipe_records(self, limit=20):
        """Display recent swipe records"""
        self.print_subheader(f"SWIPE RECORDS (Last {limit} entries)")
        records = self.session.query(SwipeRecord).order_by(SwipeRecord.attendance_date.desc()).limit(limit).all()
        
        if not records:
            print(f"{Fore.YELLOW}No swipe records found in database.{Style.RESET_ALL}")
            return
            
        data = []
        for record in records:
            vendor = self.session.query(Vendor).filter_by(id=record.vendor_id).first()
            
            data.append({
                'ID': record.id,
                'Vendor': vendor.vendor_id if vendor else 'N/A',
                'Date': record.attendance_date.strftime('%Y-%m-%d') if record.attendance_date else 'N/A',
                'Weekday': record.weekday or 'N/A',
                'Login': record.login_time.strftime('%H:%M') if record.login_time else 'N/A',
                'Logout': record.logout_time.strftime('%H:%M') if record.logout_time else 'N/A',
                'Hours': f"{record.total_hours:.2f}" if record.total_hours else 'N/A',
                'Status': record.attendance_status or 'N/A'
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        
        total_count = self.session.query(SwipeRecord).count()
        print(f"\nShowing {len(records)} of {total_count} total swipe records")
    
    def view_mismatches(self):
        """Display all mismatch records"""
        self.print_subheader("MISMATCH RECORDS")
        mismatches = self.session.query(MismatchRecord).order_by(MismatchRecord.created_at.desc()).all()
        
        if not mismatches:
            print(f"{Fore.YELLOW}No mismatch records found in database.{Style.RESET_ALL}")
            return
            
        data = []
        for mismatch in mismatches:
            vendor = self.session.query(Vendor).filter_by(id=mismatch.vendor_id).first()
            
            data.append({
                'ID': mismatch.id,
                'Vendor': vendor.vendor_id if vendor else 'N/A',
                'Date': mismatch.mismatch_date.strftime('%Y-%m-%d') if mismatch.mismatch_date else 'N/A',
                'Web Status': mismatch.web_status.value if mismatch.web_status else 'N/A',
                'Swipe Status': mismatch.swipe_status or 'N/A',
                'Approval': mismatch.manager_approval.value if mismatch.manager_approval else 'N/A',
                'Created': mismatch.created_at.strftime('%Y-%m-%d %H:%M') if mismatch.created_at else 'N/A'
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        print(f"\nTotal Mismatches: {len(mismatches)}")
        
        # Approval breakdown
        approval_counts = {'pending': 0, 'approved': 0, 'rejected': 0}
        for m in mismatches:
            if m.manager_approval:
                approval_counts[m.manager_approval.value] = approval_counts.get(m.manager_approval.value, 0) + 1
        
        print("\nApproval Status:")
        for status, count in approval_counts.items():
            print(f"  • {status.capitalize()}: {count}")
    
    def view_holidays(self):
        """Display all configured holidays"""
        self.print_subheader("HOLIDAYS")
        holidays = self.session.query(Holiday).order_by(Holiday.holiday_date).all()
        
        if not holidays:
            print(f"{Fore.YELLOW}No holidays configured in database.{Style.RESET_ALL}")
            return
            
        data = []
        for holiday in holidays:
            data.append({
                'ID': holiday.id,
                'Date': holiday.holiday_date.strftime('%Y-%m-%d') if holiday.holiday_date else 'N/A',
                'Name': holiday.name,
                'Description': holiday.description[:50] + '...' if holiday.description and len(holiday.description) > 50 else holiday.description or 'N/A'
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        print(f"\nTotal Holidays: {len(holidays)}")
    
    def view_notifications(self, limit=20):
        """Display recent notifications"""
        self.print_subheader(f"NOTIFICATION LOGS (Last {limit} entries)")
        notifications = self.session.query(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(limit).all()
        
        if not notifications:
            print(f"{Fore.YELLOW}No notifications found in database.{Style.RESET_ALL}")
            return
            
        data = []
        for notif in notifications:
            user = self.session.query(User).filter_by(id=notif.recipient_id).first()
            
            data.append({
                'ID': notif.id,
                'Recipient': user.username if user else 'N/A',
                'Type': notif.notification_type,
                'Message': notif.message[:50] + '...' if len(notif.message) > 50 else notif.message,
                'Sent': notif.sent_at.strftime('%Y-%m-%d %H:%M') if notif.sent_at else 'N/A',
                'Read': '✓' if notif.is_read else '✗'
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        
        total_count = self.session.query(NotificationLog).count()
        print(f"\nShowing {len(notifications)} of {total_count} total notifications")
    
    def view_email_notifications(self, limit=20):
        """Display recent email notifications"""
        self.print_subheader(f"EMAIL NOTIFICATION LOGS (Last {limit} entries)")
        emails = self.session.query(EmailNotificationLog).order_by(EmailNotificationLog.sent_at.desc()).limit(limit).all()
        
        if not emails:
            print(f"{Fore.YELLOW}No email notifications found in database.{Style.RESET_ALL}")
            return
            
        data = []
        for email in emails:
            data.append({
                'ID': email.id,
                'Manager ID': email.manager_id,
                'Type': email.notification_type,
                'Recipient': email.recipient,
                'Status': email.status,
                'Sent': email.sent_at.strftime('%Y-%m-%d %H:%M') if email.sent_at else 'N/A'
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        
        total_count = self.session.query(EmailNotificationLog).count()
        print(f"\nShowing {len(emails)} of {total_count} total email notifications")
    
    def view_audit_logs(self, limit=20):
        """Display recent audit logs"""
        self.print_subheader(f"AUDIT LOGS (Last {limit} entries)")
        logs = self.session.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
        
        if not logs:
            print(f"{Fore.YELLOW}No audit logs found in database.{Style.RESET_ALL}")
            return
            
        data = []
        for log in logs:
            user = self.session.query(User).filter_by(id=log.user_id).first()
            
            data.append({
                'ID': log.id,
                'User': user.username if user else 'N/A',
                'Action': log.action,
                'Table': log.table_name,
                'Record ID': log.record_id or 'N/A',
                'IP': log.ip_address or 'N/A',
                'Created': log.created_at.strftime('%Y-%m-%d %H:%M') if log.created_at else 'N/A'
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        
        total_count = self.session.query(AuditLog).count()
        print(f"\nShowing {len(logs)} of {total_count} total audit logs")
    
    def view_system_config(self):
        """Display system configuration"""
        self.print_subheader("SYSTEM CONFIGURATION")
        configs = self.session.query(SystemConfiguration).all()
        
        if not configs:
            print(f"{Fore.YELLOW}No system configurations found in database.{Style.RESET_ALL}")
            return
            
        data = []
        for config in configs:
            data.append({
                'Key': config.key,
                'Value': config.value[:50] + '...' if len(config.value) > 50 else config.value,
                'Description': config.description[:50] + '...' if config.description and len(config.description) > 50 else config.description or 'N/A',
                'Updated': config.updated_at.strftime('%Y-%m-%d %H:%M') if config.updated_at else 'N/A'
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        print(f"\nTotal Configurations: {len(configs)}")
    
    def view_leave_records(self, limit=20):
        """Display leave records"""
        self.print_subheader(f"LEAVE RECORDS (Last {limit} entries)")
        leaves = self.session.query(LeaveRecord).order_by(LeaveRecord.start_date.desc()).limit(limit).all()
        
        if not leaves:
            print(f"{Fore.YELLOW}No leave records found in database.{Style.RESET_ALL}")
            return
            
        data = []
        for leave in leaves:
            vendor = self.session.query(Vendor).filter_by(id=leave.vendor_id).first()
            
            data.append({
                'ID': leave.id,
                'Vendor': vendor.vendor_id if vendor else 'N/A',
                'Start': leave.start_date.strftime('%Y-%m-%d') if leave.start_date else 'N/A',
                'End': leave.end_date.strftime('%Y-%m-%d') if leave.end_date else 'N/A',
                'Type': leave.leave_type,
                'Days': leave.total_days
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        
        total_count = self.session.query(LeaveRecord).count()
        print(f"\nShowing {len(leaves)} of {total_count} total leave records")
    
    def view_wfh_records(self, limit=20):
        """Display WFH records"""
        self.print_subheader(f"WFH RECORDS (Last {limit} entries)")
        wfh_records = self.session.query(WFHRecord).order_by(WFHRecord.start_date.desc()).limit(limit).all()
        
        if not wfh_records:
            print(f"{Fore.YELLOW}No WFH records found in database.{Style.RESET_ALL}")
            return
            
        data = []
        for wfh in wfh_records:
            vendor = self.session.query(Vendor).filter_by(id=wfh.vendor_id).first()
            
            data.append({
                'ID': wfh.id,
                'Vendor': vendor.vendor_id if vendor else 'N/A',
                'Start': wfh.start_date.strftime('%Y-%m-%d') if wfh.start_date else 'N/A',
                'End': wfh.end_date.strftime('%Y-%m-%d') if wfh.end_date else 'N/A',
                'Days': wfh.duration_days
            })
        
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        
        total_count = self.session.query(WFHRecord).count()
        print(f"\nShowing {len(wfh_records)} of {total_count} total WFH records")
    
    def view_summary(self):
        """Display database summary"""
        self.print_header("DATABASE SUMMARY")
        
        print(f"\n{Fore.CYAN}Database Path: {Style.RESET_ALL}{DATABASE_PATH}")
        
        if not os.path.exists(DATABASE_PATH):
            print(f"{Fore.RED}Database file does not exist!{Style.RESET_ALL}")
            return
        
        # Get file size
        file_size = os.path.getsize(DATABASE_PATH)
        size_mb = file_size / (1024 * 1024)
        print(f"{Fore.CYAN}Database Size: {Style.RESET_ALL}{size_mb:.2f} MB")
        
        # Table statistics
        print(f"\n{Fore.YELLOW}Table Statistics:{Style.RESET_ALL}")
        stats = self.get_table_stats()
        df = pd.DataFrame(stats)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        
        # Calculate total records
        total_records = sum([s['Records'] for s in stats if isinstance(s['Records'], int)])
        print(f"\n{Fore.GREEN}Total Records Across All Tables: {total_records}{Style.RESET_ALL}")
    
    def run_interactive(self):
        """Run interactive database viewer"""
        while True:
            self.print_header("VENDOR TIMESHEET DATABASE VIEWER")
            
            print("\nSelect an option:")
            print("1.  View Database Summary")
            print("2.  View Users")
            print("3.  View Vendors")
            print("4.  View Managers")
            print("5.  View Daily Statuses")
            print("6.  View Swipe Records")
            print("7.  View Mismatch Records")
            print("8.  View Holidays")
            print("9.  View Notifications")
            print("10. View Email Notifications")
            print("11. View Audit Logs")
            print("12. View System Configuration")
            print("13. View Leave Records")
            print("14. View WFH Records")
            print("15. View All Tables (Complete Report)")
            print("0.  Exit")
            
            try:
                choice = input(f"\n{Fore.CYAN}Enter your choice: {Style.RESET_ALL}")
                
                if choice == '0':
                    print(f"\n{Fore.GREEN}Goodbye!{Style.RESET_ALL}")
                    break
                elif choice == '1':
                    self.view_summary()
                elif choice == '2':
                    self.view_users()
                elif choice == '3':
                    self.view_vendors()
                elif choice == '4':
                    self.view_managers()
                elif choice == '5':
                    self.view_daily_statuses()
                elif choice == '6':
                    self.view_swipe_records()
                elif choice == '7':
                    self.view_mismatches()
                elif choice == '8':
                    self.view_holidays()
                elif choice == '9':
                    self.view_notifications()
                elif choice == '10':
                    self.view_email_notifications()
                elif choice == '11':
                    self.view_audit_logs()
                elif choice == '12':
                    self.view_system_config()
                elif choice == '13':
                    self.view_leave_records()
                elif choice == '14':
                    self.view_wfh_records()
                elif choice == '15':
                    self.view_all()
                else:
                    print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
                
                if choice != '0':
                    input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Interrupted by user. Exiting...{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
    
    def view_all(self):
        """View all tables in sequence"""
        self.print_header("COMPLETE DATABASE REPORT")
        
        self.view_summary()
        self.view_users()
        self.view_vendors()
        self.view_managers()
        self.view_daily_statuses()
        self.view_swipe_records()
        self.view_mismatches()
        self.view_holidays()
        self.view_notifications()
        self.view_email_notifications()
        self.view_audit_logs()
        self.view_system_config()
        self.view_leave_records()
        self.view_wfh_records()
        
        print(f"\n{Fore.GREEN}{'='*80}")
        print(f"{Fore.GREEN}END OF REPORT")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
    
    def close(self):
        """Close database session"""
        self.session.close()


def main():
    """Main function to run the database viewer"""
    try:
        viewer = DatabaseViewer()
        
        # Check if running with command line arguments
        if len(sys.argv) > 1:
            arg = sys.argv[1].lower()
            
            if arg in ['--help', '-h']:
                print("Usage: python view_database.py [option]")
                print("\nOptions:")
                print("  --summary    View database summary only")
                print("  --all        View all tables (complete report)")
                print("  --users      View users table")
                print("  --vendors    View vendors table")
                print("  --managers   View managers table")
                print("  --status     View daily status table")
                print("  --swipe      View swipe records")
                print("  --mismatch   View mismatch records")
                print("  --help       Show this help message")
                print("\nNo arguments: Run interactive mode")
            elif arg == '--summary':
                viewer.view_summary()
            elif arg == '--all':
                viewer.view_all()
            elif arg == '--users':
                viewer.view_users()
            elif arg == '--vendors':
                viewer.view_vendors()
            elif arg == '--managers':
                viewer.view_managers()
            elif arg == '--status':
                viewer.view_daily_statuses()
            elif arg == '--swipe':
                viewer.view_swipe_records()
            elif arg == '--mismatch':
                viewer.view_mismatches()
            else:
                print(f"Unknown option: {arg}")
                print("Use --help for available options")
        else:
            # Run interactive mode
            viewer.run_interactive()
        
        viewer.close()
        
    except Exception as e:
        print(f"{Fore.RED}Fatal Error: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
