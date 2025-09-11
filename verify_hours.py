from app import app, db, DailyStatus, Vendor
from datetime import datetime, date

with app.app_context():
    # Get the vendor
    vendor = Vendor.query.filter_by(vendor_id='EMP001').first()
    
    if vendor:
        # Get recent status submissions
        recent_statuses = DailyStatus.query.filter_by(vendor_id=vendor.id).order_by(DailyStatus.status_date.desc()).limit(5).all()
        
        print("📊 Recent Status Submissions for EMP001:")
        print("=" * 80)
        
        for status in recent_statuses:
            print(f"\n📅 Date: {status.status_date}")
            print(f"   Status: {status.status.value}")
            print(f"   Location: {status.location}")
            print(f"   Total Hours: {status.total_hours if status.total_hours else 'Not recorded'}")
            
            if status.in_time and status.out_time:
                print(f"   In Time: {status.in_time}")
                print(f"   Out Time: {status.out_time}")
            
            if status.half_am_type and status.half_pm_type:
                print(f"   Half Day - AM: {status.half_am_type.value}, PM: {status.half_pm_type.value}")
                
                if status.office_in_time or status.wfh_in_time:
                    print(f"   Office In: {status.office_in_time}, Office Out: {status.office_out_time}")
                    print(f"   WFH In: {status.wfh_in_time}, WFH Out: {status.wfh_out_time}")
            
            print(f"   Break Duration: {status.break_duration} minutes")
            print(f"   Approval Status: {status.approval_status.value}")
    else:
        print("Vendor EMP001 not found")
