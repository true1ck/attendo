#!/usr/bin/env python
"""
ATTENDO - Script 3: Add Special Cases Sample Data
=================================================

This script injects explicit special-case scenarios into the database to ensure
mismatch records are visible for demos and testing. It then runs the built-in
mismatch detector to populate the mismatch_records table.

Run order (recommended):
  1) python 1_initialize_database.py
  2) python 2_load_sample_data.py
  3) python 3_Add_Special_Cases_SampleData.py

Scenarios added (for recent business days):
- WFH claimed but swipe shows present (no WFH approval record)
- Leave claimed but swipe shows present
- Leave claimed but missing Leave approval record
- In-office claimed but no swipe (or absent swipe)
- Swipe present (AP) but no daily status submitted
- Absent claimed but swipe AP exists (partial swipe variant too)
- Half-day variants for in_office_half, leave_half, wfh_half
"""
import sys
from pathlib import Path
from datetime import datetime, date, time, timedelta
import random

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("🧪 ATTENDO - Adding Special Case Sample Data")
print("=" * 60)

try:
    from app import app, db
    from models import (
        User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday,
        MismatchRecord, SystemConfiguration, LeaveRecord, WFHRecord,
        UserRole, AttendanceStatus, ApprovalStatus, HalfDayType
    )
    from utils import detect_mismatches
    print("✅ Imported app, models, and utils.detect_mismatches")
except Exception as e:
    print(f"❌ Import error: {e}")
    print("Please run from the project root and ensure dependencies are installed.")
    sys.exit(1)

random.seed(777)


def next_business_days(n=7):
    """Return a list of recent business dates (excluding weekends), yesterday backwards"""
    dates = []
    d = date.today() - timedelta(days=1)
    while len(dates) < n:
        if d.weekday() < 5:  # 0-4 Mon-Fri
            dates.append(d)
        d -= timedelta(days=1)
    return dates


def upsert_daily_status(vendor_id, d, status, location=None, approved=True, half_am_type=None, half_pm_type=None):
    ds = DailyStatus.query.filter_by(vendor_id=vendor_id, status_date=d).first()
    
    # Calculate working hours based on status
    total_work_hours = 0.0
    extra_work_hours = 0.0
    
    if status == AttendanceStatus.IN_OFFICE_FULL:
        total_work_hours = 8.5  # Slightly more than 8 for variation
        extra_work_hours = 0.5
    elif status == AttendanceStatus.IN_OFFICE_HALF:
        total_work_hours = 4.0
        extra_work_hours = 0.0
    elif status == AttendanceStatus.WFH_FULL:
        total_work_hours = 8.0
        extra_work_hours = 0.0
    elif status == AttendanceStatus.WFH_HALF:
        total_work_hours = 4.0
        extra_work_hours = 0.0
    elif status == AttendanceStatus.LEAVE_HALF:
        # Only half day working
        total_work_hours = 4.0
        extra_work_hours = 0.0
    # Leave full and absent have 0 hours
    
    if not ds:
        ds = DailyStatus(
            vendor_id=vendor_id,
            status_date=d,
            status=status,
            location=location or ("Office" if 'IN_OFFICE' in status.value else "Home" if 'WFH' in status.value else "N/A"),
            total_hours=total_work_hours,
            extra_hours=extra_work_hours,
            submitted_at=datetime.combine(d, time(9, 30)),
            approval_status=ApprovalStatus.APPROVED if approved else ApprovalStatus.PENDING,
            half_am_type=half_am_type,
            half_pm_type=half_pm_type
        )
        db.session.add(ds)
    else:
        ds.status = status
        ds.location = location or ("Office" if 'IN_OFFICE' in status.value else "Home" if 'WFH' in status.value else "N/A")
        ds.total_hours = total_work_hours
        ds.extra_hours = extra_work_hours
        ds.approval_status = ApprovalStatus.APPROVED if approved else ApprovalStatus.PENDING
        ds.half_am_type = half_am_type
        ds.half_pm_type = half_pm_type
    return ds


def upsert_swipe(vendor_id, d, present=True, partial=False):
    sr = SwipeRecord.query.filter_by(vendor_id=vendor_id, attendance_date=d).first()
    if present:
        # Present swipe (AP)
        if partial:
            login_h = random.randint(8, 10)
            login_m = random.randint(0, 59)
            values = dict(
                weekday=d.strftime('%A'),
                shift_code='G',
                login_time=time(login_h, login_m),
                logout_time=None,
                total_hours=0.0,
                extra_hours=0.0,
                attendance_status='AP'
            )
        else:
            login_h = random.randint(8, 10)
            login_m = random.randint(0, 59)
            logout_h = random.randint(17, 19)
            logout_m = random.randint(0, 59)
            total_mins = (logout_h * 60 + logout_m) - (login_h * 60 + login_m)
            values = dict(
                weekday=d.strftime('%A'),
                shift_code='G',
                login_time=time(login_h, login_m),
                logout_time=time(logout_h, logout_m),
                total_hours=round(total_mins / 60.0, 2),
                extra_hours=max(0.0, round((total_mins - 480) / 60.0, 2)),
                attendance_status='AP'
            )
    else:
        # Absent swipe (AA)
        values = dict(
            weekday=d.strftime('%A'),
            shift_code='A',
            login_time=None,
            logout_time=None,
            total_hours=0.0,
            extra_hours=0.0,
            attendance_status='AA'
        )
    if not sr:
        sr = SwipeRecord(vendor_id=vendor_id, attendance_date=d, **values)
        db.session.add(sr)
    else:
        for k, v in values.items():
            setattr(sr, k, v)
    return sr


def add_leave(vendor_id, start_d, end_d, leave_type='Earned Leave'):
    lr = LeaveRecord.query.filter_by(vendor_id=vendor_id, start_date=start_d, end_date=end_d, leave_type=leave_type).first()
    if not lr:
        lr = LeaveRecord(
            vendor_id=vendor_id,
            start_date=start_d,
            end_date=end_d,
            leave_type=leave_type,
            total_days=(end_d - start_d).days + 1
        )
        db.session.add(lr)
    return lr


def add_wfh(vendor_id, start_d, end_d):
    wr = WFHRecord.query.filter_by(vendor_id=vendor_id, start_date=start_d, end_date=end_d).first()
    if not wr:
        wr = WFHRecord(
            vendor_id=vendor_id,
            start_date=start_d,
            end_date=end_d,
            duration_days=(end_d - start_d).days + 1
        )
        db.session.add(wr)
    return wr


def create_special_cases():
    """Create comprehensive mismatch scenarios covering all major categories
    Categories covered:
    1. Status vs Swipe Mismatches
    2. Approval Record Mismatches 
    3. Time Validation Mismatches
    4. Missing Submission Mismatches
    5. Overtime Mismatches
    6. Weekend/Holiday Mismatches
    7. Half-day Specific Mismatches
    
    Limited to 1-2 cases per category for realistic testing
    """
    with app.app_context():
        vendors = Vendor.query.order_by(Vendor.id).all()
        if not vendors:
            print("❌ No vendors found. Please run 2_load_sample_data.py first.")
            return 0
        
        days = next_business_days(10)  # Need more days for varied scenarios
        v_targets = vendors[:5] if len(vendors) >= 5 else vendors  # Use up to 5 vendors
        created = 0

        print("\n🎯 Creating Enhanced Comprehensive Mismatch Scenarios...")
        
        # Category 1: Status vs Swipe Mismatches (2 cases)
        print("\n📝 Category 1: Status vs Swipe Mismatches")
        
        # Case 1a: WFH claimed but swipe shows present
        d1 = days[0]
        v = v_targets[0]
        upsert_daily_status(v.id, d1, AttendanceStatus.WFH_FULL, location='Home', approved=True)
        upsert_swipe(v.id, d1, present=True, partial=False)  # Full day swipe conflicts with WFH
        print(f"  ✓ Case 1a: WFH status but office swipe present on {d1} (Vendor: {v.vendor_id})")
        created += 1

        # Case 1b: In-office claimed but no swipe
        d2 = days[1]
        v = v_targets[1]
        upsert_daily_status(v.id, d2, AttendanceStatus.IN_OFFICE_FULL, location='BL-A-5F', approved=True)
        upsert_swipe(v.id, d2, present=False)  # No swipe conflicts with office claim
        print(f"  ✓ Case 1b: Office status but no swipe record on {d2} (Vendor: {v.vendor_id})")
        created += 1

        # Category 2: Approval Record Mismatches (2 cases)
        print("\n📋 Category 2: Approval Record Mismatches")
        
        # Case 2a: Leave claimed but no Leave approval record
        d3 = days[2]
        v = v_targets[2]
        upsert_daily_status(v.id, d3, AttendanceStatus.LEAVE_FULL, location='N/A', approved=True)
        upsert_swipe(v.id, d3, present=False)
        # Intentionally no LeaveRecord to create approval mismatch
        print(f"  ✓ Case 2a: Leave status but no approval record on {d3} (Vendor: {v.vendor_id})")
        created += 1

        # Case 2b: WFH claimed but no WFH approval record
        d4 = days[3]
        v = v_targets[3]
        upsert_daily_status(v.id, d4, AttendanceStatus.WFH_FULL, location='Home', approved=True)
        upsert_swipe(v.id, d4, present=False)  # No swipe is correct for WFH
        # Intentionally no WFHRecord to create approval mismatch
        print(f"  ✓ Case 2b: WFH status but no approval record on {d4} (Vendor: {v.vendor_id})")
        created += 1

        # Category 3: Missing Submission Mismatches (1 case)
        print("\n❓ Category 3: Missing Submission Mismatches")
        
        # Case 3: Swipe present but no daily status submitted
        d5 = days[4]
        v = v_targets[0]  # Reuse vendor
        # Ensure no DailyStatus exists
        existing_ds = DailyStatus.query.filter_by(vendor_id=v.id, status_date=d5).first()
        if existing_ds:
            db.session.delete(existing_ds)
        upsert_swipe(v.id, d5, present=True, partial=False)  # Swipe shows present
        print(f"  ✓ Case 3: Swipe record exists but no status submitted on {d5} (Vendor: {v.vendor_id})")
        created += 1

        # Category 4: Time Validation Mismatches (2 cases)
        print("\n⏰ Category 4: Time Validation Mismatches")
        
        # Case 4a: Early departure scenario
        d6 = days[5]
        v = v_targets[1]  # Reuse vendor
        upsert_daily_status(v.id, d6, AttendanceStatus.IN_OFFICE_FULL, location='BL-A-5F', approved=True)
        # Create swipe with early departure (logout before 3 PM)
        sr = SwipeRecord.query.filter_by(vendor_id=v.id, attendance_date=d6).first()
        if not sr:
            sr = SwipeRecord(
                vendor_id=v.id,
                attendance_date=d6,
                weekday=d6.strftime('%A'),
                shift_code='G',
                login_time=time(9, 15),
                logout_time=time(14, 30),  # Early departure at 2:30 PM
                total_hours=5.25,
                extra_hours=0.0,
                attendance_status='AP'
            )
            db.session.add(sr)
        print(f"  ✓ Case 4a: Early departure at 14:30 on {d6} (Vendor: {v.vendor_id})")
        created += 1
        
        # Case 4b: Late arrival scenario
        d7 = days[6]
        v = v_targets[2]  # Reuse vendor
        upsert_daily_status(v.id, d7, AttendanceStatus.IN_OFFICE_FULL, location='BL-A-5F', approved=True)
        # Create swipe with late arrival (login after 11 AM)
        sr = SwipeRecord.query.filter_by(vendor_id=v.id, attendance_date=d7).first()
        if not sr:
            sr = SwipeRecord(
                vendor_id=v.id,
                attendance_date=d7,
                weekday=d7.strftime('%A'),
                shift_code='G',
                login_time=time(11, 45),  # Late arrival at 11:45 AM
                logout_time=time(18, 0),
                total_hours=6.25,
                extra_hours=0.0,
                attendance_status='AP'
            )
            db.session.add(sr)
        print(f"  ✓ Case 4b: Late arrival at 11:45 on {d7} (Vendor: {v.vendor_id})")
        created += 1

        # Category 5: Overtime Mismatches (1 case)
        print("\n💼 Category 5: Overtime Mismatches")
        
        # Case 5: Overtime hours mismatch between swipe and status
        d8 = days[7]
        v = v_targets[3]  # Reuse vendor
        # Create status with total hours different from swipe extra hours
        upsert_daily_status(v.id, d8, AttendanceStatus.IN_OFFICE_FULL, location='BL-A-5F', approved=True)
        ds = DailyStatus.query.filter_by(vendor_id=v.id, status_date=d8).first()
        if ds:
            ds.total_hours = 10.0  # Claiming 10 total hours (2 hours overtime)
        
        # Create swipe showing different extra hours
        sr = SwipeRecord.query.filter_by(vendor_id=v.id, attendance_date=d8).first()
        if not sr:
            sr = SwipeRecord(
                vendor_id=v.id,
                attendance_date=d8,
                weekday=d8.strftime('%A'),
                shift_code='G',
                login_time=time(9, 0),
                logout_time=time(18, 30),
                total_hours=9.5,
                extra_hours=1.5,  # Swipe shows 1.5h extra vs status claiming 2h
                attendance_status='AP'
            )
            db.session.add(sr)
        print(f"  ✓ Case 5: Overtime mismatch - Status: 2h extra, Swipe: 1.5h extra on {d8} (Vendor: {v.vendor_id})")
        created += 1

        # Category 6: Weekend/Holiday Mismatches (1 case)
        print("\n📅 Category 6: Weekend/Holiday Mismatches")
        
        # Case 6: Status submitted on weekend
        # Find next Saturday
        weekend_date = date.today()
        while weekend_date.weekday() != 5:  # Find Saturday
            weekend_date += timedelta(days=1)
        # Make sure it's within reasonable range
        if (weekend_date - date.today()).days > 7:
            weekend_date = weekend_date - timedelta(days=7)
            
        v = v_targets[4 % len(v_targets)]  # Use available vendor
        upsert_daily_status(v.id, weekend_date, AttendanceStatus.IN_OFFICE_FULL, location='BL-A-5F', approved=True)
        upsert_swipe(v.id, weekend_date, present=True, partial=False)
        print(f"  ✓ Case 6: Weekend work status on {weekend_date.strftime('%A, %Y-%m-%d')} (Vendor: {v.vendor_id})")
        created += 1

        # Category 7: Half-day Specific Mismatches (kept from enhanced scenarios)
        # Note: These will be covered by the existing create_enhanced_half_day_scenarios() function
        # which provides more detailed AM/PM half-day conflict scenarios
        
        db.session.commit()
        
        print(f"\n✅ Enhanced Comprehensive Mismatch Scenarios Complete!")
        print(f"Total scenarios created: {created}")
        print(f"\nCategories covered:")
        print(f"  • Status vs Swipe Mismatches: 2 cases")
        print(f"  • Approval Record Mismatches: 2 cases")
        print(f"  • Missing Submission Mismatches: 1 case")
        print(f"  • Time Validation Mismatches: 2 cases")
        print(f"  • Overtime Mismatches: 1 case")
        print(f"  • Weekend/Holiday Mismatches: 1 case")
        print(f"\nVendors used: {', '.join([vt.vendor_id for vt in v_targets])}")
        print(f"\n📈 These scenarios will generate realistic mismatches for testing and demo purposes.")
        
        return created

def create_enhanced_half_day_scenarios():
    """Create detailed half-day scenarios with AM/PM combinations that cause mismatches"""
    with app.app_context():
        vendors = Vendor.query.order_by(Vendor.id).all()
        if not vendors:
            print("❌ No vendors found for half-day scenarios.")
            return 0
        
        days = next_business_days(10)  # Get more days for varied scenarios
        v_targets = vendors[:4]  # Use first 4 vendors
        created = 0
        
        print("\n🔄 Creating Enhanced Half-Day Scenarios...")
        
        # Scenario 1: AM in-office + PM WFH, but swipe shows full day presence
        d = days[0]
        v = v_targets[0]
        upsert_daily_status(
            v.id, d, AttendanceStatus.IN_OFFICE_HALF, 
            location='BL-A-5F / Home', approved=True,
            half_am_type=HalfDayType.IN_OFFICE,
            half_pm_type=HalfDayType.WFH
        )
        # Create full day swipe (will mismatch with PM WFH)
        upsert_swipe(v.id, d, present=True, partial=False)
        # Add WFH approval for the full day to avoid that mismatch
        add_wfh(v.id, d, d)
        created += 1
        print(f"  ✓ Scenario 1: AM office + PM WFH with full-day swipe on {d}")
        
        # Scenario 2: AM WFH + PM in-office, but no swipe at all
        d = days[1]
        v = v_targets[1]
        upsert_daily_status(
            v.id, d, AttendanceStatus.IN_OFFICE_HALF,
            location='Home / BL-A-5F', approved=True,
            half_am_type=HalfDayType.WFH,
            half_pm_type=HalfDayType.IN_OFFICE
        )
        # No swipe record (will mismatch with PM in-office)
        upsert_swipe(v.id, d, present=False)
        # Add WFH approval for AM
        add_wfh(v.id, d, d)
        created += 1
        print(f"  ✓ Scenario 2: AM WFH + PM office with no swipe on {d}")
        
        # Scenario 3: AM leave + PM in-office, but swipe shows full day
        d = days[2]
        v = v_targets[2]
        upsert_daily_status(
            v.id, d, AttendanceStatus.LEAVE_HALF,
            location='N/A / BL-A-5F', approved=True,
            half_am_type=HalfDayType.LEAVE,
            half_pm_type=HalfDayType.IN_OFFICE
        )
        # Full day swipe (will mismatch with AM leave)
        upsert_swipe(v.id, d, present=True, partial=False)
        # Add leave approval for AM
        add_leave(v.id, d, d, leave_type='Sick Leave')
        created += 1
        print(f"  ✓ Scenario 3: AM leave + PM office with full-day swipe on {d}")
        
        # Scenario 4: AM in-office + PM leave, but no leave approval
        d = days[3]
        v = v_targets[3]
        upsert_daily_status(
            v.id, d, AttendanceStatus.LEAVE_HALF,
            location='BL-A-5F / N/A', approved=True,
            half_am_type=HalfDayType.IN_OFFICE,
            half_pm_type=HalfDayType.LEAVE
        )
        # Partial swipe (AM only)
        upsert_swipe(v.id, d, present=True, partial=True)
        # No leave approval (will cause mismatch)
        created += 1
        print(f"  ✓ Scenario 4: AM office + PM leave with no leave approval on {d}")
        
        # Scenario 5: AM WFH + PM absent, but swipe shows presence in PM
        d = days[4]
        v = v_targets[0]
        upsert_daily_status(
            v.id, d, AttendanceStatus.WFH_HALF,
            location='Home / N/A', approved=True,
            half_am_type=HalfDayType.WFH,
            half_pm_type=HalfDayType.ABSENT
        )
        # Late arrival swipe (PM only) - conflicts with PM absent
        sr = SwipeRecord.query.filter_by(vendor_id=v.id, attendance_date=d).first()
        if not sr:
            sr = SwipeRecord(
                vendor_id=v.id,
                attendance_date=d,
                weekday=d.strftime('%A'),
                shift_code='G',
                login_time=time(14, 30),  # PM start
                logout_time=time(18, 0),
                total_hours=3.5,
                extra_hours=0.0,
                attendance_status='AP'
            )
            db.session.add(sr)
        # Add WFH approval for AM
        add_wfh(v.id, d, d)
        created += 1
        print(f"  ✓ Scenario 5: AM WFH + PM absent with PM swipe on {d}")
        
        # Scenario 6: AM absent + PM WFH, but full day swipe
        d = days[5]
        v = v_targets[1]
        upsert_daily_status(
            v.id, d, AttendanceStatus.WFH_HALF,
            location='N/A / Home', approved=True,
            half_am_type=HalfDayType.ABSENT,
            half_pm_type=HalfDayType.WFH
        )
        # Full day swipe (conflicts with AM absent)
        upsert_swipe(v.id, d, present=True, partial=False)
        # No WFH approval (will cause additional mismatch)
        created += 1
        print(f"  ✓ Scenario 6: AM absent + PM WFH with full-day swipe and no WFH approval on {d}")
        
        # Scenario 7: Complex - AM leave + PM in-office, partial swipe + no leave approval
        d = days[6]
        v = v_targets[2]
        upsert_daily_status(
            v.id, d, AttendanceStatus.LEAVE_HALF,
            location='N/A / BL-A-5F', approved=True,
            half_am_type=HalfDayType.LEAVE,
            half_pm_type=HalfDayType.IN_OFFICE
        )
        # Partial swipe (AM only) - conflicts with both AM leave and incomplete PM office
        sr = SwipeRecord.query.filter_by(vendor_id=v.id, attendance_date=d).first()
        if not sr:
            sr = SwipeRecord(
                vendor_id=v.id,
                attendance_date=d,
                weekday=d.strftime('%A'),
                shift_code='G',
                login_time=time(9, 15),  # AM time
                logout_time=time(11, 30),  # Short AM period
                total_hours=2.25,
                extra_hours=0.0,
                attendance_status='AP'
            )
            db.session.add(sr)
        # No leave approval (will cause mismatch)
        created += 1
        print(f"  ✓ Scenario 7: AM leave + PM office with AM-only swipe and no leave approval on {d}")
        
        # Scenario 8: AM in-office + PM WFH, but no WFH approval and early departure
        d = days[7]
        v = v_targets[3]
        upsert_daily_status(
            v.id, d, AttendanceStatus.IN_OFFICE_HALF,
            location='BL-A-5F / Home', approved=True,
            half_am_type=HalfDayType.IN_OFFICE,
            half_pm_type=HalfDayType.WFH
        )
        # Partial swipe (AM only)
        sr = SwipeRecord.query.filter_by(vendor_id=v.id, attendance_date=d).first()
        if not sr:
            sr = SwipeRecord(
                vendor_id=v.id,
                attendance_date=d,
                weekday=d.strftime('%A'),
                shift_code='G',
                login_time=time(9, 0),
                logout_time=time(13, 0),  # End of AM
                total_hours=4.0,
                extra_hours=0.0,
                attendance_status='AP'
            )
            db.session.add(sr)
        # No WFH approval for PM (will cause mismatch)
        created += 1
        print(f"  ✓ Scenario 8: AM office + PM WFH with AM-only swipe and no WFH approval on {d}")
        
        db.session.commit()
        print(f"✅ Created {created} enhanced half-day scenarios with detailed AM/PM combinations")
        return created


def run_detection():
    with app.app_context():
        try:
            count = detect_mismatches()
            print(f"🔍 Mismatch detection finished. New mismatches detected: {count}")
        except TypeError:
            # In case detect_mismatches signature differs in future, call without args
            count = detect_mismatches()
            print(f"🔍 Mismatch detection finished. New mismatches detected: {count}")
        return True


def main():
    with app.app_context():
        # Create basic special cases
        scenarios = create_special_cases()
        if scenarios == 0:
            print("❌ No scenarios created. Ensure sample data is loaded first.")
            return
        
        # Create enhanced half-day scenarios
        half_day_scenarios = create_enhanced_half_day_scenarios()
        total_scenarios = scenarios + half_day_scenarios
        
        # Run mismatch detection
        run_detection()
        
        # Quick summary of mismatches
        total = MismatchRecord.query.count()
        recent = MismatchRecord.query.order_by(MismatchRecord.created_at.desc()).limit(15).all()
        print(f"\n📈 Total mismatch records in DB: {total}")
        print(f"📋 Total scenarios created: {total_scenarios} ({scenarios} basic + {half_day_scenarios} half-day)")
        
        if recent:
            print("🧾 Recent mismatches with detailed analysis:")
            for mm in recent:
                details = mm.get_mismatch_details()
                summary = mm.get_mismatch_summary() if details else "Legacy mismatch"
                print(f"  - {mm.mismatch_date} | Vendor={mm.vendor_id} | web={mm.web_status.value if mm.web_status else 'None'} | swipe={mm.swipe_status}")
                print(f"    → {summary}")
        
        print("\n✨ Done! Enhanced half-day mismatch detection is now active.")
        print("🔍 Open /admin/reconciliation to view detailed mismatch analysis.")
        print("📝 Vendors can see detailed half-day explanations in their mismatch resolution modal.")


if __name__ == "__main__":
    main()

