#!/usr/bin/env python
"""
Generate realistic sample mismatches for demonstration purposes.

This script creates intentional mismatches between daily status submissions
and swipe records to demonstrate the mismatch detection and resolution features.

Usage:
  python scripts/generate_sample_mismatches.py
"""
import random
from datetime import datetime, date, timedelta, time

import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app, db
from models import User, Vendor, DailyStatus, SwipeRecord, MismatchRecord, AttendanceStatus, ApprovalStatus
from utils import detect_mismatches

random.seed(123)  # For reproducible results

def create_intentional_mismatches():
    """Create intentional mismatches between daily status and swipe data"""
    
    print("🔄 Generating realistic sample mismatches...")
    
    # Get all vendors
    vendors = Vendor.query.all()
    if not vendors:
        print("❌ No vendors found. Please run setup_database_with_samples.py first.")
        return
    
    # Generate mismatches for the last 10 days
    end_date = date.today() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=10)   # 10 days ago
    
    mismatch_scenarios = [
        {
            'name': 'WFH claimed but showed up in office',
            'web_status': AttendanceStatus.WFH_FULL,
            'swipe_present': True,
            'probability': 0.15
        },
        {
            'name': 'Office claimed but no swipe record',
            'web_status': AttendanceStatus.IN_OFFICE_FULL,
            'swipe_present': False,
            'probability': 0.10
        },
        {
            'name': 'Leave claimed but swiped in',
            'web_status': AttendanceStatus.LEAVE_FULL,
            'swipe_present': True,
            'probability': 0.05
        },
        {
            'name': 'Absent status but partial swipe',
            'web_status': AttendanceStatus.ABSENT,
            'swipe_present': 'partial',  # Login but no logout
            'probability': 0.08
        }
    ]
    
    created_mismatches = 0
    current_date = start_date
    
    while current_date <= end_date:
        # Skip weekends for most scenarios
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
            
        for vendor in vendors:
            # Randomly decide if this vendor should have a mismatch today
            if random.random() < 0.20:  # 20% chance of mismatch per vendor per day
                scenario = random.choices(
                    mismatch_scenarios, 
                    weights=[s['probability'] for s in mismatch_scenarios]
                )[0]
                
                # Create or update daily status
                daily_status = DailyStatus.query.filter_by(
                    vendor_id=vendor.id,
                    status_date=current_date
                ).first()
                
                if not daily_status:
                    daily_status = DailyStatus(
                        vendor_id=vendor.id,
                        status_date=current_date,
                        status=scenario['web_status'],
                        location='Home' if 'WFH' in scenario['web_status'].value else 'Office',
                        submitted_at=datetime.combine(current_date, time(9, 30)) + timedelta(minutes=random.randint(-30, 60))
                    )
                    db.session.add(daily_status)
                else:
                    daily_status.status = scenario['web_status']
                    daily_status.location = 'Home' if 'WFH' in scenario['web_status'].value else 'Office'
                
                # Create or update swipe record based on scenario
                swipe_record = SwipeRecord.query.filter_by(
                    vendor_id=vendor.id,
                    attendance_date=current_date
                ).first()
                
                if scenario['swipe_present'] is True:
                    # Create normal office swipe
                    login_h = random.randint(8, 10)
                    login_m = random.randint(0, 59)
                    logout_h = random.randint(17, 19)
                    logout_m = random.randint(0, 59)
                    total_hours = (logout_h * 60 + logout_m) - (login_h * 60 + login_m)
                    
                    if not swipe_record:
                        swipe_record = SwipeRecord(
                            vendor_id=vendor.id,
                            attendance_date=current_date,
                            weekday=current_date.strftime('%A'),
                            shift_code='G',
                            login_time=time(login_h, login_m),
                            logout_time=time(logout_h, logout_m),
                            total_hours=round(total_hours / 60.0, 2),
                            extra_hours=max(0.0, round((total_hours - 480) / 60.0, 2)),
                            attendance_status='AP'
                        )
                        db.session.add(swipe_record)
                    else:
                        swipe_record.login_time = time(login_h, login_m)
                        swipe_record.logout_time = time(logout_h, logout_m)
                        swipe_record.total_hours = round(total_hours / 60.0, 2)
                        swipe_record.attendance_status = 'AP'
                
                elif scenario['swipe_present'] == 'partial':
                    # Only login, no logout (system issue or emergency)
                    login_h = random.randint(8, 10)
                    login_m = random.randint(0, 59)
                    
                    if not swipe_record:
                        swipe_record = SwipeRecord(
                            vendor_id=vendor.id,
                            attendance_date=current_date,
                            weekday=current_date.strftime('%A'),
                            shift_code='G',
                            login_time=time(login_h, login_m),
                            logout_time=None,
                            total_hours=0.0,
                            extra_hours=0.0,
                            attendance_status='AP'  # Present but incomplete
                        )
                        db.session.add(swipe_record)
                    else:
                        swipe_record.login_time = time(login_h, login_m)
                        swipe_record.logout_time = None
                        swipe_record.total_hours = 0.0
                        swipe_record.attendance_status = 'AP'
                
                elif scenario['swipe_present'] is False:
                    # No swipe record or absent swipe
                    if not swipe_record:
                        swipe_record = SwipeRecord(
                            vendor_id=vendor.id,
                            attendance_date=current_date,
                            weekday=current_date.strftime('%A'),
                            shift_code='A',
                            login_time=None,
                            logout_time=None,
                            total_hours=0.0,
                            extra_hours=0.0,
                            attendance_status='AA'  # Absent
                        )
                        db.session.add(swipe_record)
                    else:
                        swipe_record.attendance_status = 'AA'
                        swipe_record.login_time = None
                        swipe_record.logout_time = None
                        swipe_record.total_hours = 0.0
                
                created_mismatches += 1
                print(f"   Created mismatch for {vendor.vendor_id} on {current_date}: {scenario['name']}")
        
        current_date += timedelta(days=1)
    
    db.session.commit()
    print(f"✅ Generated {created_mismatches} intentional mismatches")
    return created_mismatches

def run_mismatch_detection():
    """Run the mismatch detection to populate mismatch_records table"""
    print("🔍 Running mismatch detection...")
    
    # Get date range for detection
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=15)
    
    try:
        mismatches_found = detect_mismatches(start_date, end_date)
        print(f"✅ Mismatch detection complete. Found {len(mismatches_found)} mismatches.")
        return mismatches_found
    except Exception as e:
        print(f"❌ Error running mismatch detection: {e}")
        return []

def add_vendor_explanations():
    """Add some sample vendor explanations for mismatches"""
    print("📝 Adding sample vendor explanations...")
    
    explanations = [
        "Had to come to office for urgent client meeting despite WFH plan",
        "Forgot to swipe out due to emergency call",
        "System maintenance required physical presence",
        "Swipe card was not working properly",
        "Had to leave early for medical appointment",
        "Power outage at home, had to work from office",
        "Team meeting required physical presence",
        "Laptop issues, needed to use office desktop"
    ]
    
    # Get some recent mismatches
    mismatches = MismatchRecord.query.filter(
        MismatchRecord.vendor_reason.is_(None)
    ).limit(10).all()
    
    explained_count = 0
    for mismatch in mismatches:
        if random.random() < 0.7:  # 70% chance to add explanation
            mismatch.vendor_reason = random.choice(explanations)
            mismatch.vendor_submitted_at = datetime.utcnow() - timedelta(
                hours=random.randint(1, 48)
            )
            explained_count += 1
    
    db.session.commit()
    print(f"✅ Added explanations to {explained_count} mismatches")

def main():
    """Main function to generate comprehensive sample mismatches"""
    with app.app_context():
        print("🚀 Generating Comprehensive Sample Mismatches")
        print("=" * 60)
        
        # Step 1: Create intentional mismatches in daily status and swipe data
        mismatches_created = create_intentional_mismatches()
        
        if mismatches_created > 0:
            # Step 2: Run mismatch detection to populate mismatch_records table
            detected_mismatches = run_mismatch_detection()
            
            # Step 3: Add some vendor explanations
            add_vendor_explanations()
            
            print("\n" + "=" * 60)
            print("✅ Sample mismatch generation complete!")
            print(f"   Intentional mismatches created: {mismatches_created}")
            print(f"   Mismatches detected and recorded: {len(detected_mismatches)}")
            print("\n💡 You can now test the mismatch detection and resolution features!")
            print("   - Login as manager to review and approve/reject explanations")
            print("   - Go to /admin/reconciliation to see the mismatch summary")
            print("   - View detailed mismatch reports in the manager dashboard")
        else:
            print("❌ No mismatches created. Please check if vendors and date ranges are correct.")

if __name__ == '__main__':
    main()
