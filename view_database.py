#!/usr/bin/env python3
"""
Database Viewer Script for ATTENDO Workforce Management System
This script allows you to view and query the SQLite database data
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

class DatabaseViewer:
    def __init__(self, db_path="vendor_timesheet.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to the database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"✅ Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            return False
            
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def show_tables(self):
        """Show all tables in the database"""
        print("\n" + "="*50)
        print("📊 DATABASE TABLES")
        print("="*50)
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for i, (table_name,) in enumerate(tables, 1):
            print(f"{i:2}. {table_name}")
        
        return [table[0] for table in tables]
    
    def show_table_info(self, table_name):
        """Show table structure"""
        print(f"\n📋 TABLE STRUCTURE: {table_name}")
        print("-" * 40)
        
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"  {col[1]} ({col[2]}) {'- PRIMARY KEY' if col[5] else ''}")
    
    def view_table_data(self, table_name, limit=10):
        """View data from a specific table"""
        print(f"\n📁 DATA FROM: {table_name} (showing first {limit} records)")
        print("="*60)
        
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", self.conn)
            if df.empty:
                print("  (No data found)")
            else:
                print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error reading table {table_name}: {e}")
    
    def show_user_data(self):
        """Show all users and their roles"""
        print("\n👥 USER ACCOUNTS")
        print("="*50)
        
        try:
            df = pd.read_sql_query("""
                SELECT id, username, email, role, is_active, 
                       datetime(created_at) as created_at,
                       datetime(last_login) as last_login
                FROM users 
                ORDER BY id
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_vendor_data(self):
        """Show vendor profiles with manager information"""
        print("\n🏢 VENDOR PROFILES")
        print("="*60)
        
        try:
            df = pd.read_sql_query("""
                SELECT v.vendor_id, v.full_name, v.department, v.company, 
                       v.band, v.location, u.username,
                       COALESCE(m.manager_id, 'Not Assigned') as manager_id,
                       COALESCE(m.full_name, 'Not Assigned') as manager_name
                FROM vendors v
                JOIN users u ON v.user_id = u.id
                LEFT JOIN managers m ON v.manager_id = m.manager_id
                ORDER BY v.vendor_id
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_daily_status_data(self):
        """Show recent daily status submissions"""
        print("\n📅 DAILY STATUS SUBMISSIONS (Last 20)")
        print("="*60)
        
        try:
            df = pd.read_sql_query("""
                SELECT v.vendor_id, v.full_name, ds.status_date, ds.status,
                       ds.location, ds.approval_status, 
                       datetime(ds.submitted_at) as submitted_at
                FROM daily_statuses ds
                JOIN vendors v ON ds.vendor_id = v.id
                ORDER BY ds.status_date DESC, ds.submitted_at DESC
                LIMIT 20
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_manager_data(self):
        """Show manager profiles and their teams"""
        print("\n👔 MANAGER PROFILES")
        print("="*50)
        
        try:
            df = pd.read_sql_query("""
                SELECT m.manager_id, m.full_name, m.department, m.team_name,
                       m.email, m.phone, u.username,
                       COUNT(v.id) as team_size
                FROM managers m
                JOIN users u ON m.user_id = u.id
                LEFT JOIN vendors v ON m.manager_id = v.manager_id
                GROUP BY m.id
                ORDER BY m.manager_id
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_swipe_records_data(self):
        """Show recent swipe card records"""
        print("\n⏰ SWIPE RECORDS (Last 20)")
        print("="*60)
        
        try:
            df = pd.read_sql_query("""
                SELECT v.vendor_id, v.full_name, sr.attendance_date, sr.weekday,
                       sr.login_time, sr.logout_time, sr.total_hours, sr.attendance_status
                FROM swipe_records sr
                JOIN vendors v ON sr.vendor_id = v.id
                ORDER BY sr.attendance_date DESC, sr.login_time DESC
                LIMIT 20
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_holidays_data(self):
        """Show holiday calendar"""
        print("\n🎄 HOLIDAY CALENDAR")
        print("="*50)
        
        try:
            df = pd.read_sql_query("""
                SELECT h.holiday_date, h.name, h.description,
                       u.username as created_by,
                       datetime(h.created_at) as created_at
                FROM holidays h
                JOIN users u ON h.created_by = u.id
                ORDER BY h.holiday_date DESC
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_mismatch_records_data(self):
        """Show attendance mismatches requiring resolution"""
        print("\n⚠️ MISMATCH RECORDS (Reconciliation Issues)")
        print("="*60)
        
        try:
            df = pd.read_sql_query("""
                SELECT v.vendor_id, v.full_name, mr.mismatch_date,
                       mr.web_status, mr.swipe_status, mr.manager_approval,
                       mr.vendor_reason, datetime(mr.created_at) as created_at
                FROM mismatch_records mr
                JOIN vendors v ON mr.vendor_id = v.id
                ORDER BY mr.mismatch_date DESC
                LIMIT 20
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_audit_logs_data(self):
        """Show system audit trail"""
        print("\n📝 AUDIT LOGS (Last 20 Actions)")
        print("="*60)
        
        try:
            df = pd.read_sql_query("""
                SELECT u.username, al.action, al.table_name, al.record_id,
                       al.ip_address, datetime(al.created_at) as created_at
                FROM audit_logs al
                JOIN users u ON al.user_id = u.id
                ORDER BY al.created_at DESC
                LIMIT 20
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_system_config_data(self):
        """Show system configuration settings"""
        print("\n⚙️ SYSTEM CONFIGURATIONS")
        print("="*50)
        
        try:
            df = pd.read_sql_query("""
                SELECT sc.key, sc.value, sc.description,
                       u.username as updated_by,
                       datetime(sc.updated_at) as updated_at
                FROM system_configurations sc
                JOIN users u ON sc.updated_by = u.id
                ORDER BY sc.updated_at DESC
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_leave_records_data(self):
        """Show imported leave records"""
        print("\n🏖️ LEAVE RECORDS (Last 20)")
        print("="*50)
        
        try:
            df = pd.read_sql_query("""
                SELECT v.vendor_id, v.full_name, lr.start_date, lr.end_date,
                       lr.leave_type, lr.total_days,
                       datetime(lr.imported_at) as imported_at
                FROM leave_records lr
                JOIN vendors v ON lr.vendor_id = v.id
                ORDER BY lr.start_date DESC
                LIMIT 20
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_wfh_records_data(self):
        """Show imported Work From Home records"""
        print("\n🏠 WORK FROM HOME RECORDS (Last 20)")
        print("="*50)
        
        try:
            df = pd.read_sql_query("""
                SELECT v.vendor_id, v.full_name, wr.start_date, wr.end_date,
                       wr.duration_days, datetime(wr.imported_at) as imported_at
                FROM wfh_records wr
                JOIN vendors v ON wr.vendor_id = v.id
                ORDER BY wr.start_date DESC
                LIMIT 20
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_notifications_data(self):
        """Show notification logs"""
        print("\n🔔 NOTIFICATION LOGS (Last 20)")
        print("="*50)
        
        try:
            df = pd.read_sql_query("""
                SELECT u.username as recipient, nl.notification_type,
                       nl.message, nl.is_read,
                       datetime(nl.sent_at) as sent_at
                FROM notification_logs nl
                JOIN users u ON nl.recipient_id = u.id
                ORDER BY nl.sent_at DESC
                LIMIT 20
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_email_notifications_data(self):
        """Show email/SMS notification logs"""
        print("\n📧 EMAIL/SMS NOTIFICATION LOGS (Last 20)")
        print("="*60)
        
        try:
            df = pd.read_sql_query("""
                SELECT m.full_name as manager_name, enl.manager_id, 
                       enl.notification_type, enl.recipient, enl.status,
                       datetime(enl.sent_at) as sent_at
                FROM email_notification_logs enl
                JOIN managers m ON enl.manager_id = m.manager_id
                ORDER BY enl.sent_at DESC
                LIMIT 20
            """, self.conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_statistics(self):
        """Show comprehensive database statistics"""
        print("\n📊 COMPREHENSIVE DATABASE STATISTICS")
        print("="*50)
        
        stats = {
            "👥 Total Users": "SELECT COUNT(*) FROM users",
            "🏢 Total Vendors": "SELECT COUNT(*) FROM vendors", 
            "👔 Total Managers": "SELECT COUNT(*) FROM managers",
            "📅 Daily Status Records": "SELECT COUNT(*) FROM daily_statuses",
            "⏰ Swipe Records": "SELECT COUNT(*) FROM swipe_records",
            "🎄 Holidays": "SELECT COUNT(*) FROM holidays",
            "⚠️ Mismatch Records": "SELECT COUNT(*) FROM mismatch_records",
            "🔔 Notification Logs": "SELECT COUNT(*) FROM notification_logs",
            "📝 Audit Logs": "SELECT COUNT(*) FROM audit_logs",
            "📧 Email Notifications": "SELECT COUNT(*) FROM email_notification_logs",
            "⚙️ System Configurations": "SELECT COUNT(*) FROM system_configurations",
            "🏖️ Leave Records": "SELECT COUNT(*) FROM leave_records",
            "🏠 WFH Records": "SELECT COUNT(*) FROM wfh_records"
        }
        
        cursor = self.conn.cursor()
        for label, query in stats.items():
            try:
                cursor.execute(query)
                count = cursor.fetchone()[0]
                print(f"{label}: {count:>6}")
            except:
                print(f"{label}: Error")
                
    def show_attendance_summary(self):
        """Show attendance summary statistics"""
        print("\n📅 ATTENDANCE SUMMARY")
        print("="*50)
        
        try:
            # Status distribution
            df = pd.read_sql_query("""
                SELECT status, COUNT(*) as count,
                       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM daily_statuses), 2) as percentage
                FROM daily_statuses
                GROUP BY status
                ORDER BY count DESC
            """, self.conn)
            print("\n📊 STATUS DISTRIBUTION:")
            print(df.to_string(index=False))
            
            # Approval status distribution
            df2 = pd.read_sql_query("""
                SELECT approval_status, COUNT(*) as count
                FROM daily_statuses
                GROUP BY approval_status
                ORDER BY count DESC
            """, self.conn)
            print("\n✅ APPROVAL STATUS:")
            print(df2.to_string(index=False))
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_vendor_summary(self):
        """Show vendor statistics by department and company"""
        print("\n🏢 VENDOR SUMMARY")
        print("="*50)
        
        try:
            # By company
            df = pd.read_sql_query("""
                SELECT company, COUNT(*) as vendor_count
                FROM vendors
                GROUP BY company
                ORDER BY vendor_count DESC
            """, self.conn)
            print("\n🏢 BY COMPANY:")
            print(df.to_string(index=False))
            
            # By band
            df2 = pd.read_sql_query("""
                SELECT band, COUNT(*) as vendor_count
                FROM vendors
                GROUP BY band
                ORDER BY band
            """, self.conn)
            print("\n🎯 BY BAND:")
            print(df2.to_string(index=False))
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_recent_activity(self):
        """Show recent system activity across all tables"""
        print("\n🕰️ RECENT SYSTEM ACTIVITY (Last 24 Hours)")
        print("="*60)
        
        try:
            # Recent status submissions
            df = pd.read_sql_query("""
                SELECT 'Daily Status' as activity_type, 
                       v.vendor_id, 
                       'Submitted ' || ds.status as description,
                       datetime(ds.submitted_at) as timestamp
                FROM daily_statuses ds
                JOIN vendors v ON ds.vendor_id = v.id
                WHERE datetime(ds.submitted_at) >= datetime('now', '-1 day')
                
                UNION ALL
                
                SELECT 'Audit Log' as activity_type,
                       u.username as vendor_id,
                       al.action || ' on ' || al.table_name as description,
                       datetime(al.created_at) as timestamp
                FROM audit_logs al
                JOIN users u ON al.user_id = u.id
                WHERE datetime(al.created_at) >= datetime('now', '-1 day')
                
                ORDER BY timestamp DESC
                LIMIT 15
            """, self.conn)
            
            if df.empty:
                print("No recent activity found.")
            else:
                print(df.to_string(index=False))
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_pending_approvals(self):
        """Show all pending approval items requiring manager action"""
        print("\n⏳ PENDING APPROVALS (Manager Action Required)")
        print("="*60)
        
        try:
            # Pending daily status approvals
            df1 = pd.read_sql_query("""
                SELECT 'Daily Status' as type,
                       v.vendor_id, v.full_name, 
                       ds.status_date, ds.status,
                       m.full_name as manager_name,
                       datetime(ds.submitted_at) as submitted_at
                FROM daily_statuses ds
                JOIN vendors v ON ds.vendor_id = v.id
                JOIN managers m ON v.manager_id = m.manager_id
                WHERE ds.approval_status = 'pending'
                ORDER BY ds.submitted_at
            """, self.conn)
            
            # Pending mismatch approvals
            df2 = pd.read_sql_query("""
                SELECT 'Mismatch' as type,
                       v.vendor_id, v.full_name,
                       mr.mismatch_date as status_date,
                       mr.web_status || '/' || mr.swipe_status as status,
                       '' as manager_name,
                       datetime(mr.created_at) as submitted_at
                FROM mismatch_records mr
                JOIN vendors v ON mr.vendor_id = v.id
                WHERE mr.manager_approval = 'pending'
                ORDER BY mr.created_at
            """, self.conn)
            
            # Combine results
            if not df1.empty or not df2.empty:
                combined_df = pd.concat([df1, df2], ignore_index=True)
                combined_df = combined_df.sort_values('submitted_at')
                print(combined_df.to_string(index=False))
            else:
                print("✅ No pending approvals found!")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_team_status(self, manager_id=None):
        """Show team status for a specific manager or all teams"""
        if manager_id:
            print(f"\n👥 TEAM STATUS FOR MANAGER: {manager_id}")
        else:
            print("\n👥 ALL TEAM STATUS OVERVIEW")
        print("="*60)
        
        try:
            query = """
                SELECT m.manager_id, m.full_name as manager_name,
                       COUNT(v.id) as total_vendors,
                       COUNT(CASE WHEN ds.approval_status = 'pending' AND ds.status_date = date('now') THEN 1 END) as pending_today,
                       COUNT(CASE WHEN ds.status_date = date('now') THEN 1 END) as submitted_today
                FROM managers m
                LEFT JOIN vendors v ON m.manager_id = v.manager_id
                LEFT JOIN daily_statuses ds ON v.id = ds.vendor_id AND ds.status_date >= date('now', '-7 days')
                {}
                GROUP BY m.manager_id, m.full_name
                ORDER BY m.manager_id
            """.format("WHERE m.manager_id = '{}'".format(manager_id) if manager_id else "")
            
            df = pd.read_sql_query(query, self.conn)
            print(df.to_string(index=False))
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_attendance_trends(self, days=30):
        """Show attendance trends over specified days"""
        print(f"\n📈 ATTENDANCE TRENDS (Last {days} days)")
        print("="*60)
        
        try:
            df = pd.read_sql_query(f"""
                SELECT date(ds.status_date) as date,
                       COUNT(*) as total_submissions,
                       COUNT(CASE WHEN ds.status LIKE '%office%' THEN 1 END) as office_attendance,
                       COUNT(CASE WHEN ds.status LIKE '%wfh%' THEN 1 END) as wfh_count,
                       COUNT(CASE WHEN ds.status LIKE '%leave%' THEN 1 END) as leave_count,
                       ROUND(COUNT(CASE WHEN ds.status LIKE '%office%' THEN 1 END) * 100.0 / COUNT(*), 1) as office_percentage
                FROM daily_statuses ds
                WHERE ds.status_date >= date('now', '-{days} days')
                GROUP BY date(ds.status_date)
                ORDER BY ds.status_date DESC
                LIMIT 20
            """, self.conn)
            
            print(df.to_string(index=False))
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def search_data(self, search_term):
        """Search for data across tables"""
        print(f"\n🔍 SEARCHING FOR: '{search_term}'")
        print("="*50)
        
        # Search in users
        try:
            df = pd.read_sql_query(f"""
                SELECT 'users' as table_name, username, email, role
                FROM users 
                WHERE username LIKE '%{search_term}%' OR email LIKE '%{search_term}%'
            """, self.conn)
            if not df.empty:
                print("\n👥 Found in USERS:")
                print(df.to_string(index=False))
        except:
            pass
        
        # Search in vendors
        try:
            df = pd.read_sql_query(f"""
                SELECT 'vendors' as table_name, v.vendor_id, v.full_name, v.company, v.department,
                       COALESCE(m.full_name, 'No Manager') as manager_name
                FROM vendors v
                LEFT JOIN managers m ON v.manager_id = m.manager_id
                WHERE v.vendor_id LIKE '%{search_term}%' 
                   OR v.full_name LIKE '%{search_term}%' 
                   OR v.company LIKE '%{search_term}%'
                   OR m.full_name LIKE '%{search_term}%'
            """, self.conn)
            if not df.empty:
                print("\n🏢 Found in VENDORS:")
                print(df.to_string(index=False))
        except:
            pass

def main():
    print("🎯 ATTENDO DATABASE VIEWER")
    print("="*50)
    
    # Check if database exists
    if not os.path.exists("vendor_timesheet.db"):
        print("❌ Database file 'vendor_timesheet.db' not found!")
        print("   Run 'python app.py' first to create the database.")
        return
    
    # Initialize viewer
    viewer = DatabaseViewer()
    if not viewer.connect():
        return
    
    try:
        while True:
            print("\n" + "="*60)
            print("🎯 ATTENDO DATABASE VIEWER MENU")
            print("="*60)
            print("📊 BASIC VIEWS:")
            print(" 1. 📊 Show all tables")
            print(" 2. 👥 View users")
            print(" 3. 🏢 View vendors") 
            print(" 4. 👔 View managers")
            print(" 5. 📅 View daily status submissions")
            
            print("\n📈 ATTENDANCE DATA:")
            print(" 6. ⏰ View swipe records")
            print(" 7. ⚠️ View mismatch records")
            print(" 8. 🏖️ View leave records")
            print(" 9. 🏠 View WFH records")
            
            print("\n🔔 SYSTEM DATA:")
            print("10. 🎄 View holidays")
            print("11. ⚙️ View system configurations")
            print("12. 🔔 View notifications")
            print("13. 📧 View email notifications")
            print("14. 📝 View audit logs")
            
            print("\n📊 ANALYTICS & REPORTS:")
            print("15. 📊 Database statistics")
            print("16. 📅 Attendance summary")
            print("17. 🏢 Vendor summary")
            print("18. ⏳ Pending approvals")
            print("19. 👥 Team status overview")
            print("20. 📈 Attendance trends")
            print("21. 🕰️ Recent activity")
            
            print("\n🔧 UTILITIES:")
            print("22. 🔍 Search data")
            print("23. 📋 View specific table")
            print("24. 🔄 Refresh connection")
            print(" 0. ❌ Exit")
            
            choice = input("\n👉 Enter your choice (0-24): ").strip()
            
            # Basic Views (1-5)
            if choice == "1":
                tables = viewer.show_tables()
                
            elif choice == "2":
                viewer.show_user_data()
                
            elif choice == "3":
                viewer.show_vendor_data()
                
            elif choice == "4":
                viewer.show_manager_data()
                
            elif choice == "5":
                viewer.show_daily_status_data()
                
            # Attendance Data (6-9)
            elif choice == "6":
                viewer.show_swipe_records_data()
                
            elif choice == "7":
                viewer.show_mismatch_records_data()
                
            elif choice == "8":
                viewer.show_leave_records_data()
                
            elif choice == "9":
                viewer.show_wfh_records_data()
                
            # System Data (10-14)
            elif choice == "10":
                viewer.show_holidays_data()
                
            elif choice == "11":
                viewer.show_system_config_data()
                
            elif choice == "12":
                viewer.show_notifications_data()
                
            elif choice == "13":
                viewer.show_email_notifications_data()
                
            elif choice == "14":
                viewer.show_audit_logs_data()
                
            # Analytics & Reports (15-21)
            elif choice == "15":
                viewer.show_statistics()
                
            elif choice == "16":
                viewer.show_attendance_summary()
                
            elif choice == "17":
                viewer.show_vendor_summary()
                
            elif choice == "18":
                viewer.show_pending_approvals()
                
            elif choice == "19":
                manager_id = input("Enter Manager ID (leave empty for all teams): ").strip()
                viewer.show_team_status(manager_id if manager_id else None)
                
            elif choice == "20":
                days = input("Enter number of days (default 30): ").strip()
                days = int(days) if days.isdigit() else 30
                viewer.show_attendance_trends(days)
                
            elif choice == "21":
                viewer.show_recent_activity()
                
            # Utilities (22-24)
            elif choice == "22":
                search_term = input("Enter search term: ").strip()
                if search_term:
                    viewer.search_data(search_term)
                    
            elif choice == "23":
                tables = viewer.show_tables()
                table_choice = input(f"\nEnter table number (1-{len(tables)}): ").strip()
                try:
                    table_index = int(table_choice) - 1
                    if 0 <= table_index < len(tables):
                        table_name = tables[table_index]
                        limit = input("Enter number of records to show (default 10): ").strip()
                        limit = int(limit) if limit.isdigit() else 10
                        viewer.show_table_info(table_name)
                        viewer.view_table_data(table_name, limit)
                    else:
                        print("❌ Invalid table number")
                except ValueError:
                    print("❌ Invalid input")
                    
            elif choice == "24":
                viewer.close()
                viewer.connect()
                
            elif choice == "0":
                break
                
            else:
                print("❌ Invalid choice. Please try again.")
                
            input("\n📌 Press Enter to continue...")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        
    finally:
        viewer.close()

if __name__ == "__main__":
    main()
