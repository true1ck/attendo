#!/usr/bin/env python
"""
Script to import attendance data from Excel file with the specific format:
Employee Code | Employee Name | Attendance | WeekDay | Shift Code | Login | Logout | Extra Work Hours | Total Working Hours | Department

Usage: python scripts/import_attendance_excel.py <excel_file_path>
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, Vendor, SwipeRecord, UserRole
from utils import import_swipe_data

def preview_excel_file(file_path):
    """Preview the Excel file structure before import"""
    try:
        df = pd.read_excel(file_path)
        print("\n=== Excel File Preview ===")
        print(f"Total rows: {len(df)}")
        print(f"Columns: {df.columns.tolist()}")
        print("\nFirst 5 rows:")
        print(df.head())
        print("\nData types:")
        print(df.dtypes)
        
        # Check for unique employee codes
        if 'Employee Code' in df.columns:
            unique_codes = df['Employee Code'].dropna().unique()
            print(f"\nUnique Employee Codes: {len(unique_codes)}")
            print(f"Sample codes: {list(unique_codes[:5])}")
        
        # Check date range
        if 'Attendance' in df.columns:
            df['Attendance'] = pd.to_datetime(df['Attendance'], errors='coerce')
            print(f"\nDate range: {df['Attendance'].min()} to {df['Attendance'].max()}")
        
        return True
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        return False

def import_attendance_data(file_path):
    """Import attendance data from Excel file"""
    with app.app_context():
        print(f"\nImporting data from: {file_path}")
        
        # Preview file first
        if not preview_excel_file(file_path):
            return
        
        # Confirm import
        confirm = input("\nDo you want to proceed with import? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Import cancelled.")
            return
        
        # Run import
        print("\nStarting import...")
        records_imported = import_swipe_data(file_path)
        
        if records_imported > 0:
            print(f"\n✅ Successfully imported {records_imported} records!")
            
            # Show summary of imported data
            recent_records = SwipeRecord.query.order_by(SwipeRecord.imported_at.desc()).limit(5).all()
            print("\nRecent imported records:")
            for record in recent_records:
                print(f"  - {record.vendor.vendor_id}: {record.attendance_date} - {record.attendance_status}")
        else:
            print("\n❌ No records were imported. Check the error messages above.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_attendance_excel.py <excel_file_path>")
        print("\nExample: python scripts/import_attendance_excel.py attendance_july_2025.xlsx")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found!")
        sys.exit(1)
    
    if not file_path.lower().endswith(('.xlsx', '.xls', '.csv')):
        print("Error: File must be an Excel (.xlsx, .xls) or CSV (.csv) file!")
        sys.exit(1)
    
    import_attendance_data(file_path)

if __name__ == "__main__":
    main()
