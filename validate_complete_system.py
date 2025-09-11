#!/usr/bin/env python3
"""
Complete System Validation Script
Validates that the unified notification system is working correctly
"""

import os
from pathlib import Path
import pandas as pd
import json
from datetime import datetime
import sys

def check_file_exists(filepath, description):
    """Check if a file exists and report status"""
    path = Path(filepath)
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    
    status = "✅ EXISTS" if exists else "❌ MISSING"
    size_str = f"({size} bytes)" if exists else ""
    
    print(f"   {status:<12} {filepath} {size_str}")
    if exists and description:
        print(f"                 └─ {description}")
    
    return exists

def validate_excel_format(filepath):
    """Validate Excel file has correct format"""
    try:
        df = pd.read_excel(filepath)
        expected_columns = ['EmployeeID', 'ContactEmail', 'Message', 'NotificationType', 'Priority']
        
        has_correct_columns = all(col in df.columns for col in expected_columns)
        
        if has_correct_columns:
            print(f"       ✅ Correct format: {list(df.columns)}")
            print(f"       📊 Rows: {len(df)}")
            return True
        else:
            print(f"       ❌ Wrong format: {list(df.columns)}")
            print(f"       Expected: {expected_columns}")
            return False
    except Exception as e:
        print(f"       ❌ Error reading: {str(e)}")
        return False

def main():
    print("🔍 UNIFIED NOTIFICATION SYSTEM VALIDATION")
    print("=" * 70)
    print(f"📅 Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    validation_results = {}
    
    # 1. Check core files
    print("\n📁 CORE FILES CHECK:")
    core_files = {
        "master_notification_rules.xlsx": "Master configuration with 9 notification types",
        "unified_notification_processor.py": "Logic layer that processes rules",
        "power_automate_scheduler.py": "10-minute scheduler for Power Automate", 
        "standardize_excel_format.py": "Excel format standardizer",
        "POWER_AUTOMATE_FLOW_GUIDE.md": "Power Automate setup guide",
        "UNIFIED_NOTIFICATION_SYSTEM_README.md": "Complete system documentation"
    }
    
    core_files_ok = 0
    for filepath, description in core_files.items():
        if check_file_exists(filepath, description):
            core_files_ok += 1
    
    validation_results['core_files'] = (core_files_ok, len(core_files))
    
    # 2. Check network folder files
    print("\n📂 NETWORK FOLDER CHECK:")
    network_folder = Path("network_folder_simplified")
    
    if network_folder.exists():
        print(f"   ✅ EXISTS     {network_folder}/")
        
        network_files = {
            "sent_noti_now.xlsx": "Main output file for Power Automate",
            "scheduler_status.json": "Scheduler execution status",
            "notification_context.json": "Processing context data"
        }
        
        network_files_ok = 0
        for filename, description in network_files.items():
            filepath = network_folder / filename
            if check_file_exists(str(filepath), description):
                network_files_ok += 1
        
        validation_results['network_files'] = (network_files_ok, len(network_files))
    else:
        print(f"   ❌ MISSING   {network_folder}/")
        validation_results['network_files'] = (0, 1)
    
    # 3. Validate Excel formats
    print("\n📋 EXCEL FORMAT VALIDATION:")
    
    # Check master rules Excel
    print("   Master Rules File:")
    if Path("master_notification_rules.xlsx").exists():
        try:
            df = pd.read_excel("master_notification_rules.xlsx")
            required_master_cols = ['Notification_Type', 'Frequency', 'Priority', 'Active']
            has_master_cols = all(col in df.columns for col in required_master_cols)
            
            if has_master_cols:
                print(f"       ✅ Valid master format with {len(df)} notification types")
                active_count = len(df[df['Active'] == 'YES'])
                print(f"       📊 Active notifications: {active_count}/{len(df)}")
                validation_results['master_format'] = True
            else:
                print(f"       ❌ Invalid master format")
                validation_results['master_format'] = False
        except Exception as e:
            print(f"       ❌ Error reading master file: {str(e)}")
            validation_results['master_format'] = False
    else:
        validation_results['master_format'] = False
    
    # Check output file format
    print("   Output File (sent_noti_now.xlsx):")
    output_file = network_folder / "sent_noti_now.xlsx"
    if output_file.exists():
        validation_results['output_format'] = validate_excel_format(str(output_file))
    else:
        print(f"       ❌ Output file not found")
        validation_results['output_format'] = False
    
    # 4. Test system functionality
    print("\n⚙️ SYSTEM FUNCTIONALITY TEST:")
    
    try:
        # Test imports
        print("   Testing Python imports...")
        from unified_notification_processor import unified_processor
        from power_automate_scheduler import scheduler
        print("       ✅ All imports successful")
        validation_results['imports'] = True
        
        # Test master rules loading
        print("   Testing master rules loading...")
        rules = unified_processor.load_master_rules()
        if not rules.empty:
            print(f"       ✅ Loaded {len(rules)} notification rules")
            validation_results['rules_loading'] = True
        else:
            print("       ❌ No rules loaded")
            validation_results['rules_loading'] = False
            
        # Test scheduler status
        print("   Testing scheduler functionality...")
        status = scheduler.get_status_summary()
        if status:
            print("       ✅ Scheduler status accessible")
            if status.get('output_file_exists'):
                print("       ✅ Output file exists and accessible")
            validation_results['scheduler'] = True
        else:
            print("       ❌ Scheduler status not accessible")
            validation_results['scheduler'] = False
            
    except ImportError as e:
        print(f"       ❌ Import error: {str(e)}")
        validation_results['imports'] = False
        validation_results['rules_loading'] = False
        validation_results['scheduler'] = False
    except Exception as e:
        print(f"       ❌ Functionality test error: {str(e)}")
        validation_results['imports'] = False
        validation_results['rules_loading'] = False
        validation_results['scheduler'] = False
    
    # 5. Summary and recommendations
    print("\n📊 VALIDATION SUMMARY:")
    print("=" * 50)
    
    total_checks = 0
    passed_checks = 0
    
    # Count results
    if 'core_files' in validation_results:
        passed, total = validation_results['core_files']
        print(f"   Core Files:       {passed}/{total} {'✅' if passed == total else '❌'}")
        total_checks += total
        passed_checks += passed
    
    if 'network_files' in validation_results:
        passed, total = validation_results['network_files'] 
        print(f"   Network Files:    {passed}/{total} {'✅' if passed == total else '❌'}")
        total_checks += total
        passed_checks += passed
    
    # Boolean checks
    bool_checks = ['master_format', 'output_format', 'imports', 'rules_loading', 'scheduler']
    for check in bool_checks:
        if check in validation_results:
            result = validation_results[check]
            check_name = check.replace('_', ' ').title()
            print(f"   {check_name:<15} {'✅' if result else '❌'}")
            total_checks += 1
            passed_checks += 1 if result else 0
    
    # Overall status
    success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
    
    print("=" * 50)
    print(f"   OVERALL STATUS:   {passed_checks}/{total_checks} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("   🎉 SYSTEM READY FOR PRODUCTION!")
        print("\n✅ NEXT STEPS:")
        print("   1. Setup Power Automate flow (see POWER_AUTOMATE_FLOW_GUIDE.md)")
        print("   2. Schedule power_automate_scheduler.py to run every 10 minutes")
        print("   3. Monitor logs and status files")
        
    elif success_rate >= 70:
        print("   ⚠️  SYSTEM MOSTLY READY - Minor issues to fix")
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("   1. Review failed checks above")
        print("   2. Run individual test commands")
        print("   3. Check file permissions")
        
    else:
        print("   ❌ SYSTEM NOT READY - Major issues found")
        print("\n🚨 REQUIRED ACTIONS:")
        print("   1. Review all failed checks")
        print("   2. Re-run setup scripts")
        print("   3. Check system requirements")
    
    # 6. Quick test commands
    print(f"\n🧪 QUICK TEST COMMANDS:")
    print("   python unified_notification_processor.py")
    print("   python power_automate_scheduler.py --mode single --force")
    print("   python power_automate_scheduler.py --mode status")
    print("   python standardize_excel_format.py --action sample")
    
    return success_rate >= 90

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
