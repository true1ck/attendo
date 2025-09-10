#!/usr/bin/env python
"""
ATTENDO - Script 4: View Database
=================================

This script provides a comprehensive view of all database tables and their data.
Perfect for exploring the sample data after running the setup scripts.

Usage:
  python 4_ViewDatabase.py                    # Interactive menu
  python 4_ViewDatabase.py --all              # Show all tables at once
  python 4_ViewDatabase.py --summary          # Quick overview
  python 4_ViewDatabase.py --users            # Show users only
  python 4_ViewDatabase.py --mismatches       # Show mismatches only
  python 4_ViewDatabase.py --attendance       # Show attendance data

Features:
- Interactive menu for easy navigation
- Formatted table output with colors
- Quick statistics and counts
- Detailed data exploration
- Export options for tables
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import json

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("📊 ATTENDO - Database Viewer")
print("=" * 50)

try:
    from app import app, db
    from models import (
        User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday,
        MismatchRecord, NotificationLog, AuditLog, SystemConfiguration,
        LeaveRecord, WFHRecord, UserRole, AttendanceStatus, ApprovalStatus
    )
    from tabulate import tabulate
    print("✅ Imported app, models, and tabulate")
except Exception as e:
    print(f"❌ Import error: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(title):
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{'='*60}")
    print(f"{Colors.YELLOW}{Colors.BOLD}{title.center(60)}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")

def print_subheader(title):
    """Print a formatted subheader"""
    print(f"\n{Colors.BLUE}{'-'*50}")
    print(f"{Colors.GREEN}{title}")
    print(f"{Colors.BLUE}{'-'*50}{Colors.END}")

def get_table_stats():
    """Get statistics for all tables"""
    with app.app_context():
        stats = []
        tables = [
            ('users', User),
            ('vendors', Vendor),
            ('managers', Manager),
            ('daily_statuses', DailyStatus),
            ('swipe_records', SwipeRecord),
            ('mismatch_records', MismatchRecord),
            ('holidays', Holiday),
            ('leave_records', LeaveRecord),
            ('wfh_records', WFHRecord),
            ('notification_logs', NotificationLog),
            ('audit_logs', AuditLog),
            ('system_configurations', SystemConfiguration)
        ]
        
        for table_name, model in tables:
            try:
                count = model.query.count()
                stats.append([table_name, count])
            except Exception as e:
                stats.append([table_name, f"Error: {str(e)[:20]}"])
        
        return stats

def view_summary():
    """Display database summary"""
    print_header("DATABASE SUMMARY")
    
    # Database file info
    db_path = ROOT / "vendor_timesheet.db"
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"{Colors.CYAN}Database Path: {Colors.END}{db_path}")
        print(f"{Colors.CYAN}Database Size: {Colors.END}{size_mb:.2f} MB")
    else:
        print(f"{Colors.RED}Database file not found!{Colors.END}")
        return
    
    # Table statistics
    stats = get_table_stats()
    print(f"\n{Colors.GREEN}Table Statistics:{Colors.END}")
    print(tabulate(stats, headers=['Table', 'Records'], tablefmt='grid'))
    
    # Total records
    total = sum([s[1] for s in stats if isinstance(s[1], int)])
    print(f"\n{Colors.BOLD}{Colors.GREEN}Total Records: {total}{Colors.END}")

def view_users():
    """Display all users"""
    print_subheader("USERS")
    
    with app.app_context():
        users = User.query.all()
        if not users:
            print(f"{Colors.YELLOW}No users found.{Colors.END}")
            return
        
        data = []
        for user in users:
            data.append([
                user.id,
                user.username,
                user.email,
                user.role.value if user.role else 'N/A',
                '✓' if user.is_active else '✗',
                user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A',
                user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
            ])
        
        print(tabulate(data, headers=[
            'ID', 'Username', 'Email', 'Role', 'Active', 'Created', 'Last Login'
        ], tablefmt='grid'))
        
        print(f"\n{Colors.BOLD}Total Users: {len(users)}{Colors.END}")

def view_vendors():
    """Display all vendors"""
    print_subheader("VENDORS")
    
    with app.app_context():
        vendors = Vendor.query.all()
        if not vendors:
            print(f"{Colors.YELLOW}No vendors found.{Colors.END}")
            return
        
        data = []
        for vendor in vendors:
            user = User.query.get(vendor.user_id)
            manager = Manager.query.filter_by(manager_id=vendor.manager_id).first() if vendor.manager_id else None
            
            data.append([
                vendor.id,
                vendor.vendor_id,
                vendor.full_name,
                user.username if user else 'N/A',
                vendor.department[:20] + '...' if len(vendor.department) > 20 else vendor.department,
                vendor.company,
                vendor.band,
                vendor.location,
                manager.full_name if manager else 'N/A'
            ])
        
        print(tabulate(data, headers=[
            'ID', 'Vendor ID', 'Full Name', 'Username', 'Department', 
            'Company', 'Band', 'Location', 'Manager'
        ], tablefmt='grid'))
        
        print(f"\n{Colors.BOLD}Total Vendors: {len(vendors)}{Colors.END}")

def view_managers():
    """Display all managers"""
    print_subheader("MANAGERS")
    
    with app.app_context():
        managers = Manager.query.all()
        if not managers:
            print(f"{Colors.YELLOW}No managers found.{Colors.END}")
            return
        
        data = []
        for manager in managers:
            user = User.query.get(manager.user_id)
            team_count = Vendor.query.filter_by(manager_id=manager.manager_id).count()
            
            data.append([
                manager.id,
                manager.manager_id,
                manager.full_name,
                user.username if user else 'N/A',
                manager.department[:20] + '...' if len(manager.department) > 20 else manager.department,
                manager.team_name or 'N/A',
                team_count,
                manager.email or 'N/A',
                manager.phone or 'N/A'
            ])
        
        print(tabulate(data, headers=[
            'ID', 'Manager ID', 'Full Name', 'Username', 'Department',
            'Team Name', 'Team Size', 'Email', 'Phone'
        ], tablefmt='grid'))
        
        print(f"\n{Colors.BOLD}Total Managers: {len(managers)}{Colors.END}")

def view_attendance(limit=20):
    """Display recent attendance records"""
    print_subheader(f"DAILY ATTENDANCE STATUS (Last {limit})")
    
    with app.app_context():
        statuses = DailyStatus.query.order_by(DailyStatus.status_date.desc()).limit(limit).all()
        if not statuses:
            print(f"{Colors.YELLOW}No attendance records found.{Colors.END}")
            return
        
        data = []
        for status in statuses:
            vendor = Vendor.query.get(status.vendor_id)
            approver = User.query.get(status.approved_by) if status.approved_by else None
            
            data.append([
                status.id,
                vendor.vendor_id if vendor else 'N/A',
                vendor.full_name if vendor else 'N/A',
                status.status_date.strftime('%Y-%m-%d'),
                status.status.value if status.status else 'N/A',
                status.location or 'N/A',
                status.approval_status.value if status.approval_status else 'N/A',
                approver.username if approver else 'N/A',
                status.submitted_at.strftime('%H:%M') if status.submitted_at else 'N/A'
            ])
        
        print(tabulate(data, headers=[
            'ID', 'Vendor ID', 'Name', 'Date', 'Status', 
            'Location', 'Approval', 'Approved By', 'Submitted'
        ], tablefmt='grid'))
        
        total_count = DailyStatus.query.count()
        print(f"\n{Colors.BOLD}Showing {len(statuses)} of {total_count} attendance records{Colors.END}")

def view_swipe_records(limit=20):
    """Display recent swipe records"""
    print_subheader(f"SWIPE RECORDS (Last {limit})")
    
    with app.app_context():
        swipes = SwipeRecord.query.order_by(SwipeRecord.attendance_date.desc()).limit(limit).all()
        if not swipes:
            print(f"{Colors.YELLOW}No swipe records found.{Colors.END}")
            return
        
        data = []
        for swipe in swipes:
            vendor = Vendor.query.get(swipe.vendor_id)
            
            data.append([
                swipe.id,
                vendor.vendor_id if vendor else 'N/A',
                swipe.attendance_date.strftime('%Y-%m-%d'),
                swipe.weekday or 'N/A',
                swipe.login_time.strftime('%H:%M') if swipe.login_time else '--',
                swipe.logout_time.strftime('%H:%M') if swipe.logout_time else '--',
                f"{swipe.total_hours:.1f}" if swipe.total_hours else '0.0',
                swipe.attendance_status or 'N/A'
            ])
        
        print(tabulate(data, headers=[
            'ID', 'Vendor ID', 'Date', 'Weekday', 'Login', 
            'Logout', 'Hours', 'Status'
        ], tablefmt='grid'))
        
        total_count = SwipeRecord.query.count()
        print(f"\n{Colors.BOLD}Showing {len(swipes)} of {total_count} swipe records{Colors.END}")

def view_mismatches():
    """Display all mismatch records"""
    print_subheader("MISMATCH RECORDS")
    
    with app.app_context():
        mismatches = MismatchRecord.query.order_by(MismatchRecord.created_at.desc()).all()
        if not mismatches:
            print(f"{Colors.YELLOW}No mismatch records found.{Colors.END}")
            return
        
        data = []
        for mismatch in mismatches:
            vendor = Vendor.query.get(mismatch.vendor_id)
            approver = User.query.get(mismatch.approved_by) if mismatch.approved_by else None
            
            data.append([
                mismatch.id,
                vendor.vendor_id if vendor else 'N/A',
                mismatch.mismatch_date.strftime('%Y-%m-%d'),
                mismatch.web_status.value if mismatch.web_status else 'None',
                mismatch.swipe_status or 'N/A',
                mismatch.manager_approval.value if mismatch.manager_approval else 'pending',
                approver.username if approver else 'N/A',
                mismatch.created_at.strftime('%m-%d %H:%M') if mismatch.created_at else 'N/A',
                '✓' if mismatch.vendor_reason else '✗'
            ])
        
        print(tabulate(data, headers=[
            'ID', 'Vendor', 'Date', 'Web Status', 'Swipe', 
            'Approval', 'Approved By', 'Created', 'Explained'
        ], tablefmt='grid'))
        
        print(f"\n{Colors.BOLD}Total Mismatches: {len(mismatches)}{Colors.END}")
        
        # Status breakdown
        pending = len([m for m in mismatches if m.manager_approval == ApprovalStatus.PENDING])
        approved = len([m for m in mismatches if m.manager_approval == ApprovalStatus.APPROVED])
        rejected = len([m for m in mismatches if m.manager_approval == ApprovalStatus.REJECTED])
        
        print(f"\n{Colors.GREEN}Status Breakdown:{Colors.END}")
        print(f"  • Pending: {pending}")
        print(f"  • Approved: {approved}")  
        print(f"  • Rejected: {rejected}")

def view_holidays():
    """Display all holidays"""
    print_subheader("HOLIDAYS")
    
    with app.app_context():
        holidays = Holiday.query.order_by(Holiday.holiday_date).all()
        if not holidays:
            print(f"{Colors.YELLOW}No holidays found.{Colors.END}")
            return
        
        data = []
        for holiday in holidays:
            creator = User.query.get(holiday.created_by)
            
            data.append([
                holiday.id,
                holiday.holiday_date.strftime('%Y-%m-%d'),
                holiday.name,
                holiday.description[:40] + '...' if holiday.description and len(holiday.description) > 40 else holiday.description or 'N/A',
                creator.username if creator else 'N/A'
            ])
        
        print(tabulate(data, headers=[
            'ID', 'Date', 'Name', 'Description', 'Created By'
        ], tablefmt='grid'))
        
        print(f"\n{Colors.BOLD}Total Holidays: {len(holidays)}{Colors.END}")

def view_notifications(limit=20):
    """Display recent notifications"""
    print_subheader(f"NOTIFICATIONS (Last {limit})")
    
    with app.app_context():
        notifications = NotificationLog.query.order_by(NotificationLog.sent_at.desc()).limit(limit).all()
        if not notifications:
            print(f"{Colors.YELLOW}No notifications found.{Colors.END}")
            return
        
        data = []
        for notif in notifications:
            recipient = User.query.get(notif.recipient_id)
            
            data.append([
                notif.id,
                recipient.username if recipient else 'N/A',
                notif.notification_type,
                notif.message[:50] + '...' if len(notif.message) > 50 else notif.message,
                notif.sent_at.strftime('%m-%d %H:%M') if notif.sent_at else 'N/A',
                '✓' if notif.is_read else '✗'
            ])
        
        print(tabulate(data, headers=[
            'ID', 'Recipient', 'Type', 'Message', 'Sent', 'Read'
        ], tablefmt='grid'))
        
        total_count = NotificationLog.query.count()
        print(f"\n{Colors.BOLD}Showing {len(notifications)} of {total_count} notifications{Colors.END}")

def view_audit_logs(limit=20):
    """Display recent audit logs"""
    print_subheader(f"AUDIT LOGS (Last {limit})")
    
    with app.app_context():
        logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        if not logs:
            print(f"{Colors.YELLOW}No audit logs found.{Colors.END}")
            return
        
        data = []
        for log in logs:
            user = User.query.get(log.user_id)
            
            data.append([
                log.id,
                user.username if user else 'N/A',
                log.action,
                log.table_name,
                log.record_id or 'N/A',
                log.ip_address or 'N/A',
                log.created_at.strftime('%m-%d %H:%M') if log.created_at else 'N/A'
            ])
        
        print(tabulate(data, headers=[
            'ID', 'User', 'Action', 'Table', 'Record ID', 'IP', 'Created'
        ], tablefmt='grid'))
        
        total_count = AuditLog.query.count()
        print(f"\n{Colors.BOLD}Showing {len(logs)} of {total_count} audit logs{Colors.END}")

def view_leave_wfh():
    """Display leave and WFH records"""
    print_subheader("LEAVE & WFH RECORDS")
    
    with app.app_context():
        leaves = LeaveRecord.query.all()
        wfh_records = WFHRecord.query.all()
        
        if leaves:
            print(f"\n{Colors.GREEN}Leave Records:{Colors.END}")
            leave_data = []
            for leave in leaves:
                vendor = Vendor.query.get(leave.vendor_id)
                leave_data.append([
                    leave.id,
                    vendor.vendor_id if vendor else 'N/A',
                    leave.start_date.strftime('%Y-%m-%d'),
                    leave.end_date.strftime('%Y-%m-%d'),
                    leave.leave_type,
                    leave.total_days
                ])
            
            print(tabulate(leave_data, headers=[
                'ID', 'Vendor', 'Start Date', 'End Date', 'Type', 'Days'
            ], tablefmt='grid'))
        else:
            print(f"{Colors.YELLOW}No leave records found.{Colors.END}")
        
        if wfh_records:
            print(f"\n{Colors.GREEN}WFH Records:{Colors.END}")
            wfh_data = []
            for wfh in wfh_records:
                vendor = Vendor.query.get(wfh.vendor_id)
                wfh_data.append([
                    wfh.id,
                    vendor.vendor_id if vendor else 'N/A',
                    wfh.start_date.strftime('%Y-%m-%d'),
                    wfh.end_date.strftime('%Y-%m-%d'),
                    wfh.duration_days
                ])
            
            print(tabulate(wfh_data, headers=[
                'ID', 'Vendor', 'Start Date', 'End Date', 'Days'
            ], tablefmt='grid'))
        else:
            print(f"{Colors.YELLOW}No WFH records found.{Colors.END}")

def view_all():
    """Display all tables"""
    print_header("COMPLETE DATABASE VIEW")
    
    view_summary()
    view_users()
    view_managers()
    view_vendors()
    view_attendance(10)
    view_swipe_records(10)
    view_mismatches()
    view_holidays()
    view_leave_wfh()
    view_notifications(10)
    view_audit_logs(10)
    
    print_header("DATABASE VIEW COMPLETE")

def interactive_menu():
    """Display interactive menu"""
    while True:
        print_header("ATTENDO DATABASE VIEWER - INTERACTIVE MENU")
        
        options = [
            "1.  Database Summary",
            "2.  Users",
            "3.  Managers", 
            "4.  Vendors",
            "5.  Daily Attendance (last 20)",
            "6.  Swipe Records (last 20)",
            "7.  Mismatch Records (all)",
            "8.  Holidays",
            "9.  Leave & WFH Records",
            "10. Notifications (last 20)",
            "11. Audit Logs (last 20)",
            "12. View All Tables",
            "0.  Exit"
        ]
        
        for option in options:
            print(f"  {Colors.CYAN}{option}{Colors.END}")
        
        try:
            choice = input(f"\n{Colors.YELLOW}Enter your choice: {Colors.END}").strip()
            
            if choice == '0':
                print(f"\n{Colors.GREEN}Thank you for using ATTENDO Database Viewer!{Colors.END}")
                break
            elif choice == '1':
                view_summary()
            elif choice == '2':
                view_users()
            elif choice == '3':
                view_managers()
            elif choice == '4':
                view_vendors()
            elif choice == '5':
                view_attendance()
            elif choice == '6':
                view_swipe_records()
            elif choice == '7':
                view_mismatches()
            elif choice == '8':
                view_holidays()
            elif choice == '9':
                view_leave_wfh()
            elif choice == '10':
                view_notifications()
            elif choice == '11':
                view_audit_logs()
            elif choice == '12':
                view_all()
            else:
                print(f"{Colors.RED}Invalid choice. Please try again.{Colors.END}")
            
            if choice != '0':
                input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Interrupted by user. Exiting...{Colors.END}")
            break
        except Exception as e:
            print(f"{Colors.RED}Error: {str(e)}{Colors.END}")
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='ATTENDO Database Viewer')
    parser.add_argument('--all', action='store_true', help='Show all tables')
    parser.add_argument('--summary', action='store_true', help='Show summary only')
    parser.add_argument('--users', action='store_true', help='Show users only')
    parser.add_argument('--vendors', action='store_true', help='Show vendors only')
    parser.add_argument('--managers', action='store_true', help='Show managers only')
    parser.add_argument('--attendance', action='store_true', help='Show attendance data')
    parser.add_argument('--swipes', action='store_true', help='Show swipe records')
    parser.add_argument('--mismatches', action='store_true', help='Show mismatch records')
    parser.add_argument('--holidays', action='store_true', help='Show holidays')
    parser.add_argument('--notifications', action='store_true', help='Show notifications')
    parser.add_argument('--audit', action='store_true', help='Show audit logs')
    
    args = parser.parse_args()
    
    # Command line options
    if args.all:
        view_all()
    elif args.summary:
        view_summary()
    elif args.users:
        view_users()
    elif args.vendors:
        view_vendors()
    elif args.managers:
        view_managers()
    elif args.attendance:
        view_attendance()
    elif args.swipes:
        view_swipe_records()
    elif args.mismatches:
        view_mismatches()
    elif args.holidays:
        view_holidays()
    elif args.notifications:
        view_notifications()
    elif args.audit:
        view_audit_logs()
    else:
        # Interactive mode
        interactive_menu()

if __name__ == '__main__':
    main()
