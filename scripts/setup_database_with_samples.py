#!/usr/bin/env python
"""
Setup the SQLite database with comprehensive sample data
- Creates tables (via SQLAlchemy models)
- Ensures default admin
- Adds sample managers and vendors
- Generates daily statuses and swipe records for a recent month
- Inserts holidays and introduces some mismatches intentionally

Usage:
  python scripts/setup_database_with_samples.py

You can safely re-run this script; it will upsert by unique keys.
"""
import os
from datetime import datetime, timedelta, date, time
import random

from flask import Flask
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Reuse the app config (database path)
from app import app, db
from models import (
    User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday,
    MismatchRecord, NotificationLog, AuditLog, UserRole, AttendanceStatus, ApprovalStatus
)

random.seed(42)

def ensure_admin():
    from sqlalchemy import or_
    admin = User.query.filter(or_(User.username=='Admin', User.email=='admin@attendo.com')).first()
    if not admin:
        admin = User(username='Admin', email='admin@attendo.com', role=UserRole.ADMIN, is_active=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
    else:
        admin.username = 'Admin'
        admin.email = 'admin@attendo.com'
        admin.role = UserRole.ADMIN
        admin.is_active = True
        admin.set_password('admin123')
        db.session.commit()
    return admin


def upsert_user(username, email, role, password, active=True):
    u = User.query.filter_by(username=username).first()
    if not u:
        u = User(username=username, email=email, role=role, is_active=active)
        u.set_password(password)
        db.session.add(u)
    else:
        u.email = email
        u.role = role
        u.is_active = active
        u.set_password(password)
    db.session.commit()
    return u


def upsert_manager(manager_id, user, full_name, department, email=None, phone=None):
    m = Manager.query.filter_by(manager_id=manager_id).first()
    if not m:
        m = Manager(manager_id=manager_id, user_id=user.id, full_name=full_name, department=department, email=email, phone=phone)
        db.session.add(m)
    else:
        m.user_id = user.id
        m.full_name = full_name
        m.department = department
        m.email = email
        m.phone = phone
    db.session.commit()
    return m


def upsert_vendor(vendor_id, user, full_name, department, company, band, location, manager: Manager=None):
    v = Vendor.query.filter_by(vendor_id=vendor_id).first()
    manager_db_id = manager.manager_id if manager else None
    if not v:
        v = Vendor(user_id=user.id, vendor_id=vendor_id, full_name=full_name, department=department, company=company, band=band, location=location, manager_id=manager_db_id)
        db.session.add(v)
    else:
        v.user_id = user.id
        v.full_name = full_name
        v.department = department
        v.company = company
        v.band = band
        v.location = location
        v.manager_id = manager_db_id
    db.session.commit()
    return v


def seed_reference_data(admin: User):
    # Holidays
    holidays = [
        (date(datetime.utcnow().year, 1, 1), 'New Year'),
        (date(datetime.utcnow().year, 8, 15), 'Independence Day'),
        (date(datetime.utcnow().year, 12, 25), 'Christmas Day'),
    ]
    for d, name in holidays:
        h = Holiday.query.filter_by(holiday_date=d).first()
        if not h:
            h = Holiday(holiday_date=d, name=name, description=f'{name} Holiday', created_by=admin.id)
            db.session.add(h)
    db.session.commit()


def generate_month_data(vendors, start_date: date, end_date: date):
    # For each vendor, generate weekday statuses and swipe data
    cur = start_date
    while cur <= end_date:
        weekday = cur.weekday()  # 0=Mon, 6=Sun
        is_weekend = weekday >= 5
        for v in vendors:
            # Skip most weekends
            if is_weekend:
                if random.random() < 0.85:
                    continue
            # Decide status
            if random.random() < 0.1:
                status = AttendanceStatus.ABSENT
            elif random.random() < 0.2:
                status = AttendanceStatus.WFH_FULL
            else:
                status = AttendanceStatus.IN_OFFICE_FULL
            
            # Insert DailyStatus
            ds = DailyStatus.query.filter_by(vendor_id=v.id, status_date=cur).first()
            if not ds:
                ds = DailyStatus(vendor_id=v.id, status_date=cur, status=status, location='Office' if 'IN_OFFICE' in status.value else 'Home')
                db.session.add(ds)
            else:
                ds.status = status
                ds.location = 'Office' if 'IN_OFFICE' in status.value else 'Home'

            # Swipe data: present for in-office, absent otherwise, with some noise
            sr = SwipeRecord.query.filter_by(vendor_id=v.id, attendance_date=cur).first()
            if status == AttendanceStatus.IN_OFFICE_FULL and random.random() > 0.05:
                login_h = random.randint(9, 10)
                login_m = random.randint(0, 59)
                logout_h = random.randint(17, 19)
                logout_m = random.randint(0, 59)
                total_hours = (logout_h*60 + logout_m) - (login_h*60 + login_m)
                sr_values = dict(
                    weekday=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][weekday],
                    shift_code='G',
                    login_time=time(login_h, login_m),
                    logout_time=time(logout_h, logout_m),
                    total_hours=round(total_hours/60.0, 2),
                    extra_hours=max(0.0, round((total_hours-480)/60.0, 2)),
                    attendance_status='AP',
                )
            else:
                sr_values = dict(
                    weekday=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][weekday],
                    shift_code='A',
                    login_time=None,
                    logout_time=None,
                    total_hours=0.0,
                    extra_hours=0.0,
                    attendance_status='AA',
                )
            if not sr:
                sr = SwipeRecord(vendor_id=v.id, attendance_date=cur, **sr_values)
                db.session.add(sr)
            else:
                for k, val in sr_values.items():
                    setattr(sr, k, val)
        cur += timedelta(days=1)
    db.session.commit()


def main():
    with app.app_context():
        # Ensure tables
        db.create_all()

        admin = ensure_admin()

        # Create users
        manager_user = upsert_user('manager1', 'manager1@example.com', UserRole.MANAGER, 'manager123')
        manager2_user = upsert_user('manager2', 'manager2@example.com', UserRole.MANAGER, 'manager123')

        vendor_user1 = upsert_user('vendor1', 'vendor1@example.com', UserRole.VENDOR, 'vendor123')
        vendor_user2 = upsert_user('vendor2', 'vendor2@example.com', UserRole.VENDOR, 'vendor123')
        vendor_user3 = upsert_user('vendor3', 'vendor3@example.com', UserRole.VENDOR, 'vendor123')

        # Create managers
        m1 = upsert_manager('M001', manager_user, 'Alice Manager', 'Engineering', email='alice.manager@example.com')
        m2 = upsert_manager('M002', manager2_user, 'Bob Manager', 'Operations', email='bob.manager@example.com')

        # Create vendors
        v1 = upsert_vendor('EMP001', vendor_user1, 'John Vendor', 'Engineering', 'ABC Solutions', 'B2', 'BL-A-5F', m1)
        v2 = upsert_vendor('EMP002', vendor_user2, 'Jane Vendor', 'Engineering', 'ABC Solutions', 'B2', 'BL-A-5F', m1)
        v3 = upsert_vendor('EMP003', vendor_user3, 'Mike Vendor', 'Operations', 'XYZ Corp', 'B3', 'BL-B-3F', m2)

        seed_reference_data(admin)

        # Generate data for last full month
        today = date.today()
        first_of_this_month = date(today.year, today.month, 1)
        end_date = first_of_this_month - timedelta(days=1)
        start_date = date(end_date.year, end_date.month, 1)

        generate_month_data([v1, v2, v3], start_date, end_date)

        print("✅ Database setup complete with comprehensive sample data!")
        print("   Admin: Admin / admin123")
        print("   Managers: manager1/manager123, manager2/manager123")
        print("   Vendors: vendor1/vendor123, vendor2/vendor123, vendor3/vendor123")
        print(f"   Sample period: {start_date} to {end_date}")

if __name__ == '__main__':
    main()

