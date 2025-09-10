#!/usr/bin/env python
"""
ATTENDO - Script 5: Clear All Tables in Database
================================================

This script deletes all data from database tables while preserving the table structure.
Useful for resetting the database to a clean state for fresh testing or deployment.

WARNING: This script will DELETE ALL DATA from all tables!
Use with caution and ensure you have backups if needed.

Run order (if starting fresh):
  1) python 5_clear_Tables_In_DataBase.py
  2) python 1_initialize_database.py  
  3) python 2_load_sample_data.py
  4) python 3_Add_Special_Cases_SampleData.py

Features:
- Preserves table structure (schema remains intact)
- Handles foreign key constraints properly
- Provides detailed feedback on clearing process
- Creates fresh Admin user after clearing
- Resets auto-increment sequences
"""

import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("🗑️  ATTENDO - Clear All Tables in Database")
print("=" * 60)
print("⚠️  WARNING: This will DELETE ALL DATA from database tables!")
print("   Table structure will be preserved, but all records will be removed.")
print("=" * 60)

try:
    from app import app, db
    from models import (
        User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday,
        MismatchRecord, SystemConfiguration, LeaveRecord, WFHRecord,
        NotificationLog, AuditLog, EmailNotificationLog,
        UserRole, AttendanceStatus, ApprovalStatus
    )
    print("✅ Imported app, models, and database components")
except Exception as e:
    print(f"❌ Import error: {e}")
    print("Please run from the project root and ensure dependencies are installed.")
    sys.exit(1)

def get_user_confirmation():
    """Get user confirmation before proceeding with data deletion"""
    print("\n🤔 Are you sure you want to delete ALL DATA from the database?")
    print("   This action cannot be undone!")
    
    while True:
        response = input("\nType 'YES DELETE ALL' to confirm (or 'cancel' to abort): ").strip()
        
        if response == "YES DELETE ALL":
            return True
        elif response.lower() in ['cancel', 'no', 'n']:
            return False
        else:
            print("❌ Invalid response. Please type 'YES DELETE ALL' or 'cancel'")

def get_table_info():
    """Get information about all tables and their record counts"""
    with app.app_context():
        tables_info = []
        
        # List of model classes to check
        models = [
            ('Users', User),
            ('Vendors', Vendor), 
            ('Managers', Manager),
            ('Daily Statuses', DailyStatus),
            ('Swipe Records', SwipeRecord),
            ('Holidays', Holiday),
            ('Mismatch Records', MismatchRecord),
            ('System Configurations', SystemConfiguration),
            ('Leave Records', LeaveRecord),
            ('WFH Records', WFHRecord),
            ('Notification Logs', NotificationLog),
            ('Audit Logs', AuditLog),
            ('Email Notification Logs', EmailNotificationLog)
        ]
        
        total_records = 0
        for name, model in models:
            try:
                count = model.query.count()
                tables_info.append((name, model, count))
                total_records += count
            except Exception as e:
                print(f"⚠️  Warning: Could not count records in {name}: {e}")
                tables_info.append((name, model, 0))
        
        return tables_info, total_records

def clear_all_tables():
    """Clear all data from database tables in the correct order to handle foreign keys"""
    with app.app_context():
        try:
            print("\n🧹 Starting database cleanup process...")
            
            # Get initial table information
            tables_info, total_records = get_table_info()
            
            print(f"\n📊 Current database state:")
            for name, model, count in tables_info:
                if count > 0:
                    print(f"   📋 {name}: {count} records")
            print(f"   📈 Total records to delete: {total_records}")
            
            if total_records == 0:
                print("\n✅ Database is already empty!")
                return True
            
            print(f"\n🗑️  Deleting {total_records} records from {len(tables_info)} tables...")
            
            # Delete in reverse order of dependencies to avoid foreign key issues
            deletion_order = [
                ('Email Notification Logs', EmailNotificationLog),
                ('Audit Logs', AuditLog),
                ('Notification Logs', NotificationLog),
                ('Mismatch Records', MismatchRecord),
                ('WFH Records', WFHRecord),
                ('Leave Records', LeaveRecord),
                ('Swipe Records', SwipeRecord),
                ('Daily Statuses', DailyStatus),
                ('System Configurations', SystemConfiguration),
                ('Holidays', Holiday),
                ('Vendors', Vendor),
                ('Managers', Manager),
                ('Users', User)
            ]
            
            deleted_counts = {}
            
            for name, model in deletion_order:
                try:
                    count_before = model.query.count()
                    if count_before > 0:
                        # Delete all records from this table
                        model.query.delete()
                        db.session.commit()
                        
                        count_after = model.query.count()
                        deleted = count_before - count_after
                        deleted_counts[name] = deleted
                        
                        if deleted > 0:
                            print(f"   ✅ Cleared {name}: {deleted} records deleted")
                        
                except Exception as e:
                    db.session.rollback()
                    print(f"   ❌ Error clearing {name}: {e}")
                    # Continue with other tables
            
            # Reset auto-increment sequences (SQLite specific)
            try:
                from sqlalchemy import text
                db.session.execute(text("DELETE FROM sqlite_sequence"))
                db.session.commit()
                print("   ✅ Reset auto-increment sequences")
            except Exception as e:
                print(f"   ⚠️  Could not reset sequences: {e}")
            
            # Verify all tables are empty
            print("\n🔍 Verifying cleanup...")
            tables_info_after, remaining_records = get_table_info()
            
            if remaining_records == 0:
                print("✅ All tables successfully cleared!")
            else:
                print(f"⚠️  Warning: {remaining_records} records remain in database")
                for name, model, count in tables_info_after:
                    if count > 0:
                        print(f"   📋 {name}: {count} records remaining")
            
            return remaining_records == 0
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Database cleanup failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def create_fresh_admin():
    """Create a fresh admin user after clearing tables"""
    with app.app_context():
        try:
            print("\n👤 Creating fresh Admin user...")
            
            # Check if admin already exists (shouldn't after clearing)
            existing_admin = User.query.filter_by(username='Admin').first()
            if existing_admin:
                print("   ℹ️  Admin user already exists")
                return True
            
            # Create new admin user
            admin_user = User(
                username='Admin',
                email='admin@attendo.com',
                role=UserRole.ADMIN,
                is_active=True
            )
            admin_user.set_password('admin123')
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("   ✅ Admin user created successfully")
            print("      Username: Admin")
            print("      Password: admin123")
            print("      Email: admin@attendo.com")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ Failed to create Admin user: {e}")
            return False

def main():
    """Main function to orchestrate the database clearing process"""
    
    # Get user confirmation
    if not get_user_confirmation():
        print("\n❌ Operation cancelled by user.")
        print("   No data was deleted.")
        return
    
    print(f"\n⏰ Starting cleanup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with app.app_context():
        # Step 1: Clear all tables
        success = clear_all_tables()
        
        if not success:
            print("\n❌ Database cleanup failed!")
            print("   Some data may still remain in the database.")
            return
        
        # Step 2: Create fresh admin user
        admin_created = create_fresh_admin()
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎉 Database cleanup completed successfully!")
        print("=" * 60)
        print("📋 Summary:")
        print("   ✅ All table data deleted")
        print("   ✅ Table structures preserved") 
        print("   ✅ Auto-increment sequences reset")
        
        if admin_created:
            print("   ✅ Fresh Admin user created")
        else:
            print("   ⚠️  Admin user creation failed")
        
        print("\n📝 Next steps:")
        print("   1. Run: python 1_initialize_database.py")
        print("   2. Run: python 2_load_sample_data.py")
        print("   3. Run: python 3_Add_Special_Cases_SampleData.py")
        print("   4. Start app: python app.py")
        
        print(f"\n⏰ Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
