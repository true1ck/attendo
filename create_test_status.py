#!/usr/bin/env python3
"""
Create test status for approve/reject testing
"""

from flask import Flask
import os
from datetime import datetime, date

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath("vendor_timesheet.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import models
import models
models.db.init_app(app)

with app.app_context():
    from models import User, Vendor, DailyStatus, AttendanceStatus, ApprovalStatus
    
    print("🎯 CREATING TEST STATUS FOR APPROVE/REJECT")
    print("="*50)
    
    # Get vendor
    vendor_user = User.query.filter_by(username='vendor1').first()
    if not vendor_user:
        print("❌ Vendor user not found!")
        exit(1)
        
    vendor = vendor_user.vendor_profile
    if not vendor:
        print("❌ Vendor profile not found!")
        exit(1)
    
    print(f"✅ Vendor: {vendor.full_name} ({vendor.vendor_id})")
    
    # Create today's test status if it doesn't exist or reset it to pending
    today = date.today()
    existing_status = DailyStatus.query.filter_by(
        vendor_id=vendor.id,
        status_date=today
    ).first()
    
    if existing_status:
        print(f"📋 Found existing status for today: {existing_status.approval_status.value}")
        # Reset to pending
        existing_status.approval_status = ApprovalStatus.PENDING
        existing_status.manager_comments = None
        existing_status.approved_at = None
        existing_status.approved_by = None
        models.db.session.commit()
        print("✅ Reset existing status to pending")
        status_id = existing_status.id
    else:
        # Create new test status
        test_status = DailyStatus(
            vendor_id=vendor.id,
            status_date=today,
            status=AttendanceStatus.IN_OFFICE_FULL,
            location="Office - Test Location",
            comments="Test status for approve/reject functionality",
            approval_status=ApprovalStatus.PENDING
        )
        models.db.session.add(test_status)
        models.db.session.commit()
        status_id = test_status.id
        print("✅ Created new test status")
    
    print(f"📋 Status ID: {status_id}")
    print(f"📋 Status: IN_OFFICE_FULL")
    print(f"📋 Date: {today}")
    print(f"📋 Approval Status: PENDING")
    
    print("\n🚀 READY FOR TESTING!")
    print("📝 You can now test approve/reject functionality with:")
    print(f"   - Status ID: {status_id}")
    print("   - Login as manager1 / manager123")
    print("   - Go to manager dashboard or weekly report page")
    print("   - Click approve/reject on the status")
    
    print("\n🧪 Or test via API:")
    print(f"   curl -X POST http://localhost:5000/manager/approve-status/{status_id}")
    print("        -d 'action=approve'")
    print("        -H 'Content-Type: application/x-www-form-urlencoded'")
    print("        --cookie 'session=...'")
    
    print("\n🔗 Status details:")
    print(f"   http://localhost:5000/manager/reports")
