#!/usr/bin/env python3
"""
Fix Mismatch Resolution Flow

This script diagnoses and fixes issues with the mismatch resolution workflow:
1. Vendors submitting explanations
2. Managers seeing and reviewing explanations
3. Approval/rejection workflow

Usage: python fix_mismatch_flow.py
"""

from app import app, db
from models import (User, Vendor, Manager, MismatchRecord, DailyStatus, SwipeRecord, 
                   UserRole, AttendanceStatus, ApprovalStatus)
from datetime import datetime, date, timedelta
import json

def diagnose_mismatch_flow():
    """Diagnose the current state of mismatch resolution flow"""
    
    print("🔍 MISMATCH RESOLUTION FLOW DIAGNOSIS")
    print("=" * 60)
    
    # Check database state
    total_mismatches = MismatchRecord.query.count()
    pending_mismatches = MismatchRecord.query.filter_by(manager_approval=ApprovalStatus.PENDING).count()
    with_explanations = MismatchRecord.query.filter(MismatchRecord.vendor_reason.isnot(None)).count()
    
    print(f"📊 Database Statistics:")
    print(f"   Total mismatches: {total_mismatches}")
    print(f"   Pending approval: {pending_mismatches}")
    print(f"   With vendor explanations: {with_explanations}")
    print()
    
    # Check user accounts
    vendors = User.query.filter_by(role=UserRole.VENDOR).count()
    managers = User.query.filter_by(role=UserRole.MANAGER).count()
    
    print(f"👥 User Accounts:")
    print(f"   Vendors: {vendors}")
    print(f"   Managers: {managers}")
    print()
    
    # Detailed manager view
    manager_user = User.query.filter_by(role=UserRole.MANAGER).first()
    if manager_user and manager_user.manager_profile:
        manager = manager_user.manager_profile
        print(f"🎯 Manager Analysis ({manager.full_name}):")
        
        team_vendors = manager.team_vendors.all()
        print(f"   Team size: {len(team_vendors)}")
        
        vendor_ids = [v.id for v in team_vendors]
        
        # Get all mismatches for team
        team_mismatches = MismatchRecord.query.filter(
            MismatchRecord.vendor_id.in_(vendor_ids)
        ).all()
        
        # Categorize them
        pending_no_explanation = []
        pending_with_explanation = []
        approved_mismatches = []
        rejected_mismatches = []
        
        for m in team_mismatches:
            if m.manager_approval == ApprovalStatus.PENDING:
                if m.vendor_reason:
                    pending_with_explanation.append(m)
                else:
                    pending_no_explanation.append(m)
            elif m.manager_approval == ApprovalStatus.APPROVED:
                approved_mismatches.append(m)
            elif m.manager_approval == ApprovalStatus.REJECTED:
                rejected_mismatches.append(m)
        
        print(f"   Total team mismatches: {len(team_mismatches)}")
        print(f"   ⏳ Pending (no explanation): {len(pending_no_explanation)}")
        print(f"   📝 Pending (with explanation): {len(pending_with_explanation)} ← READY FOR REVIEW")
        print(f"   ✅ Approved: {len(approved_mismatches)}")
        print(f"   ❌ Rejected: {len(rejected_mismatches)}")
        print()
        
        # Show ready-for-review items
        if pending_with_explanation:
            print(f"🔍 Mismatches Ready for Manager Review:")
            for m in pending_with_explanation:
                vendor = next((v for v in team_vendors if v.id == m.vendor_id), None)
                vendor_name = vendor.full_name if vendor else f"Unknown (ID: {m.vendor_id})"
                print(f"   📋 ID: {m.id} | {vendor_name} | {m.mismatch_date}")
                print(f"      Web: {m.web_status.value if m.web_status else 'None'} | Swipe: {m.swipe_status}")
                print(f"      Explanation: {m.vendor_reason[:80]}...")
                print(f"      Submitted: {m.vendor_submitted_at}")
                print()
    
    # Check template logic
    print("🖥️  Frontend Template Analysis:")
    print("   Manager should access: /manager/mismatches")
    print("   Template file: templates/manager_mismatches.html")
    print("   Filter logic: Line 209 checks if mismatch.vendor_reason exists")
    print("   Action buttons: Lines 211-217 show Approve/Reject buttons")
    print()
    
    return {
        'total_mismatches': total_mismatches,
        'pending_with_explanations': len(pending_with_explanation) if 'pending_with_explanation' in locals() else 0,
        'ready_for_review': pending_with_explanation if 'pending_with_explanation' in locals() else []
    }

def create_test_scenarios():
    """Create some test mismatches with explanations for testing"""
    
    print("🧪 CREATING TEST SCENARIOS")
    print("=" * 60)
    
    # Find vendor and create test mismatches
    vendor_user = User.query.filter_by(role=UserRole.VENDOR).first()
    if not vendor_user or not vendor_user.vendor_profile:
        print("❌ No vendor user found for testing")
        return
        
    vendor = vendor_user.vendor_profile
    print(f"Using vendor: {vendor.full_name}")
    
    # Create a few test mismatches without explanations first
    test_dates = [
        date.today() - timedelta(days=1),
        date.today() - timedelta(days=2), 
        date.today() - timedelta(days=3)
    ]
    
    created_count = 0
    
    for test_date in test_dates:
        # Check if mismatch already exists for this date
        existing = MismatchRecord.query.filter_by(
            vendor_id=vendor.id,
            mismatch_date=test_date
        ).first()
        
        if not existing:
            # Create new mismatch
            mismatch = MismatchRecord(
                vendor_id=vendor.id,
                mismatch_date=test_date,
                web_status=AttendanceStatus.WFH_FULL,
                swipe_status='AP',
                manager_approval=ApprovalStatus.PENDING,
                created_at=datetime.utcnow()
            )
            db.session.add(mismatch)
            created_count += 1
    
    if created_count > 0:
        db.session.commit()
        print(f"✅ Created {created_count} new test mismatches")
    else:
        print("ℹ️  Test mismatches already exist")
    
    # Now add explanations to some pending mismatches
    pending_mismatches = MismatchRecord.query.filter_by(
        vendor_id=vendor.id,
        manager_approval=ApprovalStatus.PENDING
    ).filter(MismatchRecord.vendor_reason.is_(None)).limit(2).all()
    
    explanations = [
        "Had to come to office for urgent client meeting despite planning WFH",
        "Internet connection failed at home, had to work from office",
        "Manager requested physical presence for team meeting"
    ]
    
    explanation_count = 0
    for i, mismatch in enumerate(pending_mismatches):
        if i < len(explanations):
            mismatch.vendor_reason = explanations[i]
            mismatch.vendor_submitted_at = datetime.utcnow() - timedelta(minutes=i*30)
            explanation_count += 1
    
    if explanation_count > 0:
        db.session.commit()
        print(f"✅ Added explanations to {explanation_count} mismatches")
    
    return created_count + explanation_count

def test_manager_view():
    """Test what the manager should see"""
    
    print("👔 TESTING MANAGER VIEW")
    print("=" * 60)
    
    manager_user = User.query.filter_by(role=UserRole.MANAGER).first()
    if not manager_user or not manager_user.manager_profile:
        print("❌ No manager user found")
        return
        
    manager = manager_user.manager_profile
    print(f"Manager: {manager.full_name} ({manager.manager_id})")
    print(f"Login: {manager_user.username} / manager123")
    print()
    
    # Simulate the manager mismatches route logic
    team_vendors = manager.team_vendors.all()
    vendor_ids = [v.id for v in team_vendors]
    
    # Apply the same filters as the template
    mismatch_query = MismatchRecord.query.filter(
        MismatchRecord.vendor_id.in_(vendor_ids)
    )
    
    # Filter for pending (default filter)
    mismatch_query = mismatch_query.filter(
        MismatchRecord.manager_approval == ApprovalStatus.PENDING
    )
    
    mismatches = mismatch_query.order_by(MismatchRecord.mismatch_date.desc()).all()
    
    print(f"🔍 Manager Dashboard Results:")
    print(f"   Team vendors: {len(team_vendors)}")
    print(f"   Total pending mismatches: {len(mismatches)}")
    
    # Group by vendor like the template does
    vendor_mismatches = {}
    for mismatch in mismatches:
        vendor = next((v for v in team_vendors if v.id == mismatch.vendor_id), None)
        if vendor:
            if vendor.vendor_id not in vendor_mismatches:
                vendor_mismatches[vendor.vendor_id] = {
                    'vendor': vendor,
                    'mismatches': [],
                    'pending_count': 0,
                    'total_count': 0
                }
            
            vendor_mismatches[vendor.vendor_id]['mismatches'].append(mismatch)
            vendor_mismatches[vendor.vendor_id]['total_count'] += 1
            
            if mismatch.manager_approval == ApprovalStatus.PENDING:
                vendor_mismatches[vendor.vendor_id]['pending_count'] += 1
    
    print()
    
    # Show what manager should see for each vendor
    for vendor_id, data in vendor_mismatches.items():
        print(f"👤 {data['vendor'].full_name} ({vendor_id}):")
        print(f"   {data['pending_count']} pending, {data['total_count']} total")
        
        for mismatch in data['mismatches']:
            status_icon = "📝" if mismatch.vendor_reason else "⏳"
            web_status = mismatch.web_status.value if mismatch.web_status else 'None'
            action_available = "🟢 READY TO REVIEW" if mismatch.vendor_reason else "🔸 Waiting for explanation"
            
            print(f"   {status_icon} {mismatch.mismatch_date} | {web_status} vs {mismatch.swipe_status} | {action_available}")
            if mismatch.vendor_reason:
                print(f"      Explanation: {mismatch.vendor_reason}")
        print()

def main():
    """Main function"""
    with app.app_context():
        print("🚀 MISMATCH RESOLUTION FLOW DIAGNOSTICS & FIX")
        print("=" * 80)
        print()
        
        # Step 1: Diagnose current state
        diagnosis = diagnose_mismatch_flow()
        
        # Step 2: Create test scenarios if needed
        if diagnosis['pending_with_explanations'] < 2:
            print("⚠️  Not enough test data. Creating test scenarios...")
            create_test_scenarios()
            print()
        
        # Step 3: Test manager view
        test_manager_view()
        
        print("=" * 80)
        print("🎯 RESOLUTION STEPS:")
        print()
        print("1. 🔑 Login as manager: username='manager1', password='manager123'")
        print("2. 🌐 Go to: http://localhost:5000/manager/mismatches")
        print("3. 🔍 Check filter is set to 'Pending Review' (default)")
        print("4. 👀 Look for mismatches with 'Vendor Explanation' section")
        print("5. ✅ Use Approve/Reject buttons for mismatches with explanations")
        print()
        print("🐛 If still not working, check:")
        print("   - Browser cache (hard refresh with Ctrl+F5)")
        print("   - JavaScript console for errors")
        print("   - Manager has correct team assignments")
        print("   - Database connection is working")
        print()
        
        # Final verification
        ready_count = diagnosis.get('pending_with_explanations', 0)
        if ready_count > 0:
            print(f"✅ SUCCESS: {ready_count} mismatches are ready for manager review!")
        else:
            print("⚠️  WARNING: No mismatches ready for review. Check vendor submissions.")

if __name__ == '__main__':
    main()
