"""
Database Migration Script - Add Half-Day Support
Adds half_am_type and half_pm_type columns to DailyStatus table
and mismatch_details JSON column to MismatchRecord table
"""

import sqlite3
import json
from datetime import datetime

def migrate_database():
    """Add half-day support columns to existing database"""
    db_path = "vendor_timesheet.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migration is needed
        print("🔄 Checking existing database schema...")
        
        # Check if half-day columns exist in daily_statuses table
        cursor.execute("PRAGMA table_info(daily_statuses)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'half_am_type' not in columns:
            print("📝 Adding half_am_type column to daily_statuses...")
            cursor.execute("ALTER TABLE daily_statuses ADD COLUMN half_am_type TEXT NULL")
        
        if 'half_pm_type' not in columns:
            print("📝 Adding half_pm_type column to daily_statuses...")
            cursor.execute("ALTER TABLE daily_statuses ADD COLUMN half_pm_type TEXT NULL")
            
        # Check if mismatch_details column exists in mismatch_records table
        cursor.execute("PRAGMA table_info(mismatch_records)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'mismatch_details' not in columns:
            print("📝 Adding mismatch_details JSON column to mismatch_records...")
            cursor.execute("ALTER TABLE mismatch_records ADD COLUMN mismatch_details TEXT NULL")
            
        # Commit changes
        conn.commit()
        
        # Verify the migration
        print("✅ Verifying migration...")
        cursor.execute("PRAGMA table_info(daily_statuses)")
        daily_status_columns = [column[1] for column in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(mismatch_records)")
        mismatch_columns = [column[1] for column in cursor.fetchall()]
        
        success = True
        if 'half_am_type' not in daily_status_columns:
            print("❌ Failed to add half_am_type column")
            success = False
        if 'half_pm_type' not in daily_status_columns:
            print("❌ Failed to add half_pm_type column")
            success = False
        if 'mismatch_details' not in mismatch_columns:
            print("❌ Failed to add mismatch_details column")
            success = False
            
        if success:
            print("✅ Database migration completed successfully!")
            print("   - Added half_am_type column to daily_statuses")
            print("   - Added half_pm_type column to daily_statuses")
            print("   - Added mismatch_details column to mismatch_records")
        
        conn.close()
        return success
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def rollback_migration():
    """Rollback the migration (SQLite doesn't support DROP COLUMN easily, so recreate table)"""
    print("⚠️ Rollback not implemented for SQLite. Consider backing up database before migration.")
    return False

if __name__ == "__main__":
    print("🚀 Starting Half-Day Support Database Migration...")
    success = migrate_database()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
