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
        UserRole, AttendanceStatus, ApprovalStatus
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


def upsert_daily_status(vendor_id, d, status, location=None, approved=True):
    ds = DailyStatus.query.filter_by(vendor_id=vendor_id, status_date=d).first()
    if not ds:
        ds = DailyStatus(
            vendor_id=vendor_id,
            status_date=d,
            status=status,
            location=location or ("Office" if 'IN_OFFICE' in status.value else "Home" if 'WFH' in status.value else "N/A"),
            submitted_at=datetime.combine(d, time(9, 30)),
            approval_status=ApprovalStatus.APPROVED if approved else ApprovalStatus.PENDING
        )
        db.session.add(ds)
    else:
        ds.status = status
        ds.location = location or ("Office" if 'IN_OFFICE' in status.value else "Home" if 'WFH' in status.value else "N/A")
        ds.approval_status = ApprovalStatus.APPROVED if approved else ApprovalStatus.PENDING
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
    with app.app_context():
        vendors = Vendor.query.order_by(Vendor.id).all()
        if not vendors:
            print("❌ No vendors found. Please run 2_load_sample_data.py first.")
            return 0
        days = next_business_days(6)
        v_targets = vendors[:3]  # use first 3 vendors for deterministic cases
        created = 0

        # Case 1: WFH claimed but swipe shows present (no WFH approval)
        d1 = days[0]
        v = v_targets[0]
        upsert_daily_status(v.id, d1, AttendanceStatus.WFH_FULL, location='Home', approved=True)
        upsert_swipe(v.id, d1, present=True, partial=False)
        created += 1

        # Case 2: In-office claimed but no swipe (AA)
        d2 = days[1]
        v = v_targets[0]
        upsert_daily_status(v.id, d2, AttendanceStatus.IN_OFFICE_FULL, location='Office', approved=True)
        upsert_swipe(v.id, d2, present=False)
        created += 1

        # Case 3: Leave claimed but swipe shows present
        d3 = days[2]
        v = v_targets[1]
        upsert_daily_status(v.id, d3, AttendanceStatus.LEAVE_FULL, location='N/A', approved=True)
        # Optionally also record a leave approval to cover the date
        add_leave(v.id, d3, d3, leave_type='Casual Leave')
        upsert_swipe(v.id, d3, present=True)
        created += 1

        # Case 4: Leave claimed but no Leave approval record (and no swipe)
        d4 = days[3]
        v = v_targets[1]
        upsert_daily_status(v.id, d4, AttendanceStatus.LEAVE_FULL, location='N/A', approved=True)
        upsert_swipe(v.id, d4, present=False)
        # No LeaveRecord added intentionally
        created += 1

        # Case 5: Swipe AP exists but no daily status at all
        d5 = days[4]
        v = v_targets[2]
        # Ensure no DailyStatus for d5
        ds = DailyStatus.query.filter_by(vendor_id=v.id, status_date=d5).first()
        if ds:
            db.session.delete(ds)
        upsert_swipe(v.id, d5, present=True)
        created += 1

        # Case 6: Absent claimed but partial swipe exists (login only)
        d6 = days[5]
        v = v_targets[2]
        upsert_daily_status(v.id, d6, AttendanceStatus.ABSENT, location='N/A', approved=True)
        upsert_swipe(v.id, d6, present=True, partial=True)
        created += 1

        # Case 7: Half-day WFH but swipe AP present
        d7 = days[0] - timedelta(days=7)  # a week earlier (business day assumed)
        while d7.weekday() >= 5:
            d7 -= timedelta(days=1)
        v = v_targets[0]
        upsert_daily_status(v.id, d7, AttendanceStatus.WFH_HALF, location='Home', approved=True)
        upsert_swipe(v.id, d7, present=True)
        created += 1

        # Case 8: Half-day In-Office but swipe absent
        d8 = d7 - timedelta(days=1)
        while d8.weekday() >= 5:
            d8 -= timedelta(days=1)
        v = v_targets[1]
        upsert_daily_status(v.id, d8, AttendanceStatus.IN_OFFICE_HALF, location='Office', approved=True)
        upsert_swipe(v.id, d8, present=False)
        created += 1

        # Case 9: Half-day Leave but swipe AP present and no leave approval
        d9 = d8 - timedelta(days=1)
        while d9.weekday() >= 5:
            d9 -= timedelta(days=1)
        v = v_targets[2]
        upsert_daily_status(v.id, d9, AttendanceStatus.LEAVE_HALF, location='N/A', approved=True)
        upsert_swipe(v.id, d9, present=True)
        # No LeaveRecord on purpose
        created += 1

        db.session.commit()
        print(f"✅ Injected {created} special-case day scenarios across vendors {', '.join([vt.vendor_id for vt in v_targets])}")
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
        scenarios = create_special_cases()
        if scenarios == 0:
            print("❌ No scenarios created. Ensure sample data is loaded first.")
            return
        run_detection()
        # Quick summary of mismatches
        total = MismatchRecord.query.count()
        recent = MismatchRecord.query.order_by(MismatchRecord.created_at.desc()).limit(10).all()
        print(f"\n📈 Total mismatch records in DB: {total}")
        if recent:
            print("🧾 Recent mismatches:")
            for mm in recent:
                print(f"  - {mm.mismatch_date} | VendorID={mm.vendor_id} | web={mm.web_status.value if mm.web_status else 'None'} | swipe={mm.swipe_status}")
        print("\n✨ Done. Open /admin/reconciliation to view mismatches.")


if __name__ == "__main__":
    main()

