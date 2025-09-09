#!/usr/bin/env python
"""
Database Migration Script
Adds missing columns to existing tables
"""

import sqlite3
import sys
from datetime import datetime

def add_column_if_not_exists(conn, table, column, column_type):
    """Add a column to a table if it doesn't exist"""
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [column[1] for column in cursor.fetchall()]
    
    if column not in columns:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
            conn.commit()
            print(f"✅ Added column '{column}' to table '{table}'")
            return True
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"ℹ️ Column '{column}' already exists in table '{table}'")
            else:
                print(f"❌ Error adding column '{column}' to table '{table}': {e}")
            return False
    else:
        print(f"ℹ️ Column '{column}' already exists in table '{table}'")
        return False

def migrate_database():
    """Run database migrations"""
    db_path = 'vendor_timesheet.db'
    
    print("=" * 60)
    print("🔄 DATABASE MIGRATION")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Database: {db_path}")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Add new columns to swipe_records table
        print("\n📋 Migrating swipe_records table...")
        changes_made = False
        
        # Add shift_code column
        if add_column_if_not_exists(conn, 'swipe_records', 'shift_code', 'VARCHAR(10)'):
            changes_made = True
        
        # Add extra_hours column
        if add_column_if_not_exists(conn, 'swipe_records', 'extra_hours', 'FLOAT'):
            changes_made = True
        
        # Show current table structure
        print("\n📊 Current swipe_records table structure:")
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(swipe_records)")
        columns = cursor.fetchall()
        
        print("  Columns:")
        for col in columns:
            col_id, name, col_type, not_null, default, pk = col
            print(f"    - {name}: {col_type}")
        
        conn.close()
        
        if changes_made:
            print("\n✅ Database migration completed successfully!")
            print("   New columns have been added to support the enhanced import format.")
        else:
            print("\n✅ Database is already up to date!")
            print("   No migration needed.")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Database migration failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    if not success:
        sys.exit(1)
