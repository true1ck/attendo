#!/usr/bin/env python
"""
Create a sample Excel file in the exact format required for attendance import
"""

import pandas as pd
from datetime import datetime, timedelta
import random

def create_sample_attendance_excel(output_file='sample_attendance.xlsx'):
    """Create a sample Excel file with attendance data"""
    
    # Sample data
    employees = [
        ('OT1', 'abc1', 'WCS/MSE7'),
        ('OT2', 'abc2', 'WCS/MSE7'),
        ('OT3', 'abc3', 'WCS/MSE8'),
    ]
    
    # Generate data for a month
    start_date = datetime(2025, 7, 1)
    end_date = datetime(2025, 7, 31)
    
    data = []
    current_date = start_date
    
    while current_date <= end_date:
        weekday = current_date.strftime('%A')
        
        for emp_code, emp_name, department in employees:
            # Skip weekends randomly
            if weekday in ['Saturday', 'Sunday']:
                if random.random() > 0.2:  # 80% chance to skip weekends
                    shift_code = 'G'
                    login = '-'
                    logout = '-'
                    extra_hours = '-'
                    total_hours = '-'
                else:
                    continue
            else:
                # Weekday - mostly present
                if random.random() > 0.1:  # 90% present on weekdays
                    shift_code = 'G'
                    
                    # Generate random login time between 9:00 and 10:30
                    login_hour = random.randint(9, 10)
                    login_minute = random.randint(0, 59)
                    login = f"{login_hour:02d}:{login_minute:02d}"
                    
                    # Generate logout time between 17:00 and 19:00
                    logout_hour = random.randint(17, 19)
                    logout_minute = random.randint(0, 59)
                    logout = f"{logout_hour:02d}:{logout_minute:02d}"
                    
                    # Calculate total hours
                    total_mins = (logout_hour * 60 + logout_minute) - (login_hour * 60 + login_minute)
                    total_h = total_mins // 60
                    total_m = total_mins % 60
                    total_hours = f"{total_h:02d}:{total_m:02d}"
                    
                    # Extra hours if worked more than 8 hours
                    if total_mins > 480:  # 8 hours = 480 minutes
                        extra_mins = total_mins - 480
                        extra_h = extra_mins // 60
                        extra_m = extra_mins % 60
                        extra_hours = f"{extra_h:02d}:{extra_m:02d}"
                    else:
                        extra_hours = "00:00"
                else:
                    # Absent
                    shift_code = 'A'
                    login = '-'
                    logout = '-'
                    extra_hours = '-'
                    total_hours = '-'
            
            data.append({
                'Sl.No.': len(data) + 1,
                'Employee Code': emp_code,
                'Employee Name': emp_name,
                'Attendance': current_date.strftime('%d/%m/%Y'),
                'WeekDay': weekday,
                'Shift Code': shift_code,
                'Login': login,
                'Logout': logout,
                'Extra Work Hours': extra_hours,
                'Total Working Hours': total_hours,
                'Department': department
            })
        
        current_date += timedelta(days=1)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to Excel
    df.to_excel(output_file, index=False)
    print(f"✅ Sample Excel file created: {output_file}")
    print(f"   Total rows: {len(df)}")
    print(f"   Date range: {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}")
    print(f"   Employees: {len(employees)}")
    
    # Show preview
    print("\nFirst 10 rows:")
    print(df.head(10))
    
    return output_file

if __name__ == "__main__":
    create_sample_attendance_excel()
