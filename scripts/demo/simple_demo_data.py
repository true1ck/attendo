from app import app
from datetime import datetime, date, timedelta
import random
from models import (User, Vendor, Manager, DailyStatus, SwipeRecord, Holiday, 
                   UserRole, AttendanceStatus, ApprovalStatus, db)

def create_simple_demo_data():
    """Create basic demo data for testing"""
    
    with app.app_context():
        try:
            print("Creating demo data...")
            
            # Clear existing data
            DailyStatus.query.delete()
            SwipeRecord.query.delete()
            Vendor.query.delete()
            Manager.query.delete()
            User.query.filter(User.username != 'admin').delete()
            db.session.commit()
            
            # Create Manager
            manager_user = User(
                username='manager1',
                email='manager1@attendo.com',
                role=UserRole.MANAGER,
                is_active=True
            )
            manager_user.set_password('manager123')
            db.session.add(manager_user)
            db.session.commit()
            
            manager = Manager(
                user_id=manager_user.id,
                full_name='John Manager',
                department='ATD_WCS_MSE7_MS1',
                team_name='Team Alpha'
            )
            db.session.add(manager)
            db.session.commit()
            
            # Create 5 Vendors
            vendors = []
            for i in range(5):
                vendor_user = User(
                    username=f'vendor{i+1}',
                    email=f'vendor{i+1}@company.com',
                    role=UserRole.VENDOR,
                    is_active=True
                )
                vendor_user.set_password('vendor123')
                db.session.add(vendor_user)
                db.session.commit()
                
                vendor = Vendor(
                    user_id=vendor_user.id,
                    vendor_id=f'VND{str(i+1).zfill(3)}',
                    full_name=f'Vendor {i+1} Name',
                    department='ATD_WCS_MSE7_MS1',
                    company='TechFlow Solutions',
                    band='B2',
                    location='BL-A-5F',
                    manager_id=manager.id
                )
                db.session.add(vendor)
                vendors.append(vendor)
            
            db.session.commit()
            
            # Create some holidays
            holidays = [
                (date(2025, 1, 1), 'New Year Day'),
                (date(2025, 1, 26), 'Republic Day'),
                (date(2025, 8, 15), 'Independence Day'),
                (date(2025, 12, 25), 'Christmas Day')
            ]
            
            admin_user = User.query.filter_by(username='admin').first()
            for holiday_date, name in holidays:
                holiday = Holiday(
                    holiday_date=holiday_date,
                    name=name,
                    description=f'National holiday - {name}',
                    created_by=admin_user.id
                )
                db.session.add(holiday)
            
            db.session.commit()
            
            # Create daily status records for last 30 days
            start_date = date.today() - timedelta(days=30)
            
            for vendor in vendors:
                current_date = start_date
                while current_date <= date.today():
                    # Skip weekends
                    if current_date.weekday() >= 5:
                        current_date += timedelta(days=1)
                        continue
                    
                    # 80% chance of status submission
                    if random.random() < 0.8:
                        status = random.choice([
                            AttendanceStatus.IN_OFFICE_FULL,
                            AttendanceStatus.WFH_FULL,
                            AttendanceStatus.LEAVE_FULL
                        ])
                        
                        daily_status = DailyStatus(
                            vendor_id=vendor.id,
                            status_date=current_date,
                            status=status,
                            location='BL-A-5F' if status == AttendanceStatus.IN_OFFICE_FULL else 'Home',
                            comments='Working on project tasks',
                            submitted_at=datetime.combine(current_date, datetime.min.time()) + timedelta(hours=9),
                            approval_status=ApprovalStatus.APPROVED,
                            approved_by=manager_user.id,
                            approved_at=datetime.combine(current_date, datetime.min.time()) + timedelta(hours=12)
                        )
                        db.session.add(daily_status)
                    
                    current_date += timedelta(days=1)
            
            db.session.commit()
            
            # Create some swipe records
            for vendor in vendors[:3]:  # First 3 vendors
                current_date = start_date
                while current_date <= date.today():
                    if current_date.weekday() >= 5:
                        current_date += timedelta(days=1)
                        continue
                    
                    if random.random() < 0.9:
                        swipe_record = SwipeRecord(
                            vendor_id=vendor.id,
                            attendance_date=current_date,
                            weekday=current_date.strftime('%A'),
                            login_time=datetime.combine(current_date, datetime.min.time()).replace(hour=9, minute=0).time(),
                            logout_time=datetime.combine(current_date, datetime.min.time()).replace(hour=18, minute=0).time(),
                            total_hours=8.0,
                            attendance_status='AP'
                        )
                        db.session.add(swipe_record)
                    
                    current_date += timedelta(days=1)
            
            db.session.commit()
            
            print("✅ Demo data created successfully!")
            print("📊 Summary:")
            print("  - 1 Manager (manager1/manager123)")
            print("  - 5 Vendors (vendor1-5/vendor123)")
            print("  - 4 Holidays")
            print("  - 30 days of attendance data")
            print("  - Swipe records for 3 vendors")
            print("")
            print("🎬 Demo Credentials:")
            print("   👨‍💻 Admin: admin/admin123")
            print("   👨‍💼 Manager: manager1/manager123")
            print("   👤 Vendor: vendor1/vendor123")
            print("")
            print("🚀 Ready for testing!")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating demo data: {str(e)}")
            return False

if __name__ == '__main__':
    create_simple_demo_data()
