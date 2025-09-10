#!/usr/bin/env python3
"""
Migration script to add time tracking fields to the DailyStatus table
"""

import sqlite3
import os
from datetime import datetime

def add_time_tracking_fields():
    """Add time tracking fields to existing database"""
    
    db_path = 'vendor_timesheet.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Adding time tracking fields to daily_statuses table...")
        
        # List of new columns to add
        new_columns = [
            ("in_time", "TIME"),
            ("out_time", "TIME"),
            ("office_in_time", "TIME"),
            ("office_out_time", "TIME"),
            ("wfh_in_time", "TIME"),
            ("wfh_out_time", "TIME"),
            ("break_duration", "INTEGER DEFAULT 0"),
            ("total_hours", "REAL")
        ]
        
        for column_name, column_type in new_columns:
            try:
                # Check if column already exists
                cursor.execute(f"PRAGMA table_info(daily_statuses)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if column_name not in columns:
                    alter_sql = f"ALTER TABLE daily_statuses ADD COLUMN {column_name} {column_type}"
                    cursor.execute(alter_sql)
                    print(f"   ✅ Added column: {column_name}")
                else:
                    print(f"   ⚠️ Column {column_name} already exists")
                    
            except sqlite3.Error as e:
                print(f"   ❌ Error adding column {column_name}: {e}")
        
        # Commit changes
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(daily_statuses)")
        columns = cursor.fetchall()
        print(f"📋 Current daily_statuses columns ({len(columns)} total):")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Time Tracking Migration Script")
    print("=" * 50)
    
    success = add_time_tracking_fields()
    
    if success:
        print("\n🎉 Migration completed! You can now:")
        print("   - Restart the application")
        print("   - Use the enhanced status submission form")
        print("   - Track detailed time information")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
