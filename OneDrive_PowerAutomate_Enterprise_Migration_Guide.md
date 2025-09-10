# OneDrive & Power Automate Migration Guide - Enterprise Security Standard

## Overview
This guide provides detailed steps to migrate your 10 Excel notification configurations to OneDrive and Power Automate within **Enterprise Security Standard** constraints where webhooks are not allowed.

## Enterprise Security Constraints
- ❌ HTTP webhooks not allowed
- ❌ External API calls restricted
- ✅ OneDrive file monitoring allowed
- ✅ Scheduled triggers allowed
- ✅ SharePoint integration allowed
- ✅ Internal email/Teams notifications allowed

## Alternative Trigger Methods (Without Webhooks)

### Method 1: Excel File Monitoring (Primary Method)
- Monitor OneDrive Excel files for changes
- Use "When an item is created or modified" trigger
- Real-time response to data updates

### Method 2: Scheduled Polling
- Regular scheduled checks of status files
- Safe for enterprise environments
- Configurable intervals

### Method 3: SharePoint List Integration
- Use SharePoint lists instead of direct webhooks
- Your Python system writes to SharePoint
- Power Automate monitors SharePoint changes

## Phase 1: OneDrive Setup (Same as before)

### Step 1: Create OneDrive Folder Structure
```
📁 ATTENDO_Notifications/
├── 📁 Active_Configs/          (Current notification configurations)
├── 📁 Trigger_Files/           (Status files for triggering flows)
├── 📁 Processed/              (Archive processed notifications)
├── 📁 Templates/              (Template files)
├── 📁 Logs/                   (Power Automate logs)
└── 📁 Backups/               (Daily backups)
```

### Step 2: Additional Trigger Files Structure
```
📁 Trigger_Files/
├── 📁 Mismatch_Alerts/        (Files to trigger mismatch notifications)
├── 📁 Feedback_Notifications/ (Files to trigger feedback flows)
├── 📁 System_Alerts/         (Files to trigger admin alerts)
├── 📁 Status_Changes/        (Files to trigger status updates)
└── 📁 Processing_Queue/      (Files waiting to be processed)
```

## Phase 2: Enterprise-Compatible Flow Designs

### Flow 1: Daily Vendor Reminders (Scheduled - No Changes)
- **Trigger**: Recurrence (every 3 hours, 9 AM-6 PM)
- **Method**: Direct Excel table monitoring
- **Enterprise Safe**: ✅ Uses only scheduled triggers

### Flow 2: Manager Summary (Scheduled - No Changes)
- **Trigger**: Recurrence (12 PM and 2 PM daily)
- **Method**: Direct Excel table reading
- **Enterprise Safe**: ✅ Uses only scheduled triggers

### Flow 3: Manager All-Complete (Excel File Monitoring)

**Original Design** (Webhook): ❌ Not allowed
**Enterprise Design** (File Monitoring): ✅

1. **Create Flow**
   - Name: "ATTENDO - Team Complete Monitor"
   - Trigger: "When a file is created or modified"

2. **Trigger Setup**
   - **Location**: OneDrive for Business
   - **Folder**: `/ATTENDO_Notifications/Active_Configs/03_Manager_Complete/`
   - **File**: Monitor `Manager_Complete_Config.xlsx`

3. **Process Logic**
   - Read Excel table for rows with `Trigger_Condition` = "ALL_TEAM_SUBMITTED"
   - Send completion emails
   - Update status to prevent duplicate notifications

### Flow 4: Mismatch Alerts (File Drop Method)

**Original Design** (Webhook): ❌ Not allowed
**Enterprise Design** (File Monitoring): ✅

1. **Create Flow**
   - Name: "ATTENDO - Mismatch Alert Monitor"
   - Trigger: "When a file is created"

2. **Trigger Setup**
   - **Location**: OneDrive for Business
   - **Folder**: `/ATTENDO_Notifications/Trigger_Files/Mismatch_Alerts/`
   - **File Pattern**: `*.json` or `*.txt`

3. **Process Logic**
   - Read trigger file content
   - Parse mismatch data
   - Send appropriate notifications
   - Move file to processed folder

### Flow 5: Manager Feedback (File Drop Method)

1. **Create Flow**
   - Name: "ATTENDO - Feedback Monitor"
   - Trigger: "When a file is created"

2. **Trigger Setup**
   - **Folder**: `/ATTENDO_Notifications/Trigger_Files/Feedback_Notifications/`

3. **File Format** (JSON):
   ```json
   {
     "vendor_id": "V001",
     "feedback_type": "REJECTION",
     "manager_comments": "Please correct attendance data",
     "manager_id": "M001",
     "timestamp": "2024-01-15T14:30:00Z"
   }
   ```

### Flow 6: Monthly Reports (Scheduled - No Changes)
- **Enterprise Safe**: ✅ Uses scheduled triggers

### Flow 7: Admin System Alerts (File Drop + Scheduled)

1. **File Drop Monitor**
   - Monitor `/Trigger_Files/System_Alerts/`
   - Process critical alerts immediately

2. **Scheduled Health Check**
   - Every 30 minutes
   - Check system status files
   - Generate alerts based on thresholds

### Flow 8: Holiday Reminders (Scheduled - No Changes)
- **Enterprise Safe**: ✅ Uses scheduled triggers

### Flow 9: Late Submission Alerts (Scheduled + File Monitoring)

1. **Scheduled Check**
   - Daily at 6 PM
   - Check for late submissions
   - Generate alerts

2. **Real-time Updates**
   - Monitor late submission status file
   - Update Excel when vendors submit

### Flow 10: Billing Corrections (File Drop Method)

1. **File Drop Monitor**
   - Monitor billing correction trigger files
   - Process high-priority financial notifications

## Phase 3: Python Integration (Enterprise-Safe Methods)

### Method 1: OneDrive File API Integration

```python
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

class EnterpriseNotificationTrigger:
    """Enterprise-safe notification triggering using OneDrive file drops"""
    
    def __init__(self, onedrive_sync_path):
        # Path to local OneDrive sync folder
        self.onedrive_path = Path(onedrive_sync_path)
        self.trigger_path = self.onedrive_path / "ATTENDO_Notifications" / "Trigger_Files"
        
        # Ensure trigger directories exist
        self.mismatch_path = self.trigger_path / "Mismatch_Alerts"
        self.feedback_path = self.trigger_path / "Feedback_Notifications"
        self.system_alerts_path = self.trigger_path / "System_Alerts"
        self.status_changes_path = self.trigger_path / "Status_Changes"
        
        # Create directories if they don't exist
        for path in [self.mismatch_path, self.feedback_path, 
                     self.system_alerts_path, self.status_changes_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def trigger_mismatch_alert(self, vendor_id, manager_id, mismatch_details):
        """Trigger mismatch alert by creating a file"""
        trigger_data = {
            'trigger_type': 'mismatch_alert',
            'vendor_id': vendor_id,
            'manager_id': manager_id,
            'mismatch_type': mismatch_details.get('type'),
            'details': mismatch_details,
            'timestamp': datetime.now().isoformat(),
            'urgency': 'HIGH' if mismatch_details.get('critical') else 'MEDIUM'
        }
        
        # Create unique filename to prevent conflicts
        filename = f"mismatch_{vendor_id}_{uuid.uuid4().hex[:8]}.json"
        filepath = self.mismatch_path / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(trigger_data, f, indent=2)
            print(f"✅ Mismatch alert triggered: {filename}")
            return True
        except Exception as e:
            print(f"❌ Error triggering mismatch alert: {e}")
            return False
    
    def trigger_feedback_notification(self, vendor_id, feedback_type, manager_comments, manager_id):
        """Trigger feedback notification by creating a file"""
        trigger_data = {
            'trigger_type': 'feedback_notification',
            'vendor_id': vendor_id,
            'feedback_type': feedback_type,
            'manager_comments': manager_comments,
            'manager_id': manager_id,
            'timestamp': datetime.now().isoformat(),
            'priority': 'HIGH' if feedback_type == 'REJECTION' else 'MEDIUM'
        }
        
        filename = f"feedback_{vendor_id}_{uuid.uuid4().hex[:8]}.json"
        filepath = self.feedback_path / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(trigger_data, f, indent=2)
            print(f"✅ Feedback notification triggered: {filename}")
            return True
        except Exception as e:
            print(f"❌ Error triggering feedback notification: {e}")
            return False
    
    def trigger_system_alert(self, alert_type, message, severity="MEDIUM"):
        """Trigger system alert by creating a file"""
        trigger_data = {
            'trigger_type': 'system_alert',
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'source': 'ATTENDO_SYSTEM'
        }
        
        filename = f"alert_{alert_type}_{uuid.uuid4().hex[:8]}.json"
        filepath = self.system_alerts_path / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(trigger_data, f, indent=2)
            print(f"✅ System alert triggered: {filename}")
            return True
        except Exception as e:
            print(f"❌ Error triggering system alert: {e}")
            return False
    
    def update_excel_for_team_complete(self, manager_id):
        """Update Excel file to trigger team complete notification"""
        try:
            # Path to manager complete config
            config_path = (self.onedrive_path / "ATTENDO_Notifications" / 
                          "Active_Configs" / "03_Manager_Complete" / 
                          "Manager_Complete_Config.xlsx")
            
            if config_path.exists():
                # Read, update, and save Excel file
                import pandas as pd
                df = pd.read_excel(config_path)
                
                # Find manager row and update trigger condition
                mask = df['Manager_ID'] == manager_id
                if mask.any():
                    df.loc[mask, 'Trigger_Condition'] = 'ALL_TEAM_SUBMITTED'
                    df.loc[mask, 'Last_Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    df.loc[mask, 'Send_Notification'] = 'YES'
                    
                    # Save back to Excel
                    df.to_excel(config_path, index=False)
                    print(f"✅ Team complete trigger updated for manager {manager_id}")
                    return True
            return False
        except Exception as e:
            print(f"❌ Error updating team complete trigger: {e}")
            return False

# Integration in your existing code
enterprise_notifier = EnterpriseNotificationTrigger(
    onedrive_sync_path="C:/Users/YourUser/OneDrive - Company"  # Adjust path
)

# Update your existing methods
def send_mismatch_alert(self, vendor_id, manager_id, mismatch_data):
    """Updated method for enterprise environment"""
    enterprise_notifier.trigger_mismatch_alert(vendor_id, manager_id, mismatch_data)

def send_feedback_notification(self, vendor_id, feedback_type, comments, manager_id):
    """Updated method for enterprise environment"""
    enterprise_notifier.trigger_feedback_notification(vendor_id, feedback_type, comments, manager_id)

def handle_team_complete(self, manager_id):
    """Updated method for enterprise environment"""
    enterprise_notifier.update_excel_for_team_complete(manager_id)

def send_system_alert(self, alert_type, message, severity="MEDIUM"):
    """Updated method for enterprise environment"""
    enterprise_notifier.trigger_system_alert(alert_type, message, severity)
```

### Method 2: Direct Excel File Updates

```python
import pandas as pd
from datetime import datetime
import shutil

class ExcelBasedTrigger:
    """Direct Excel file manipulation for triggering flows"""
    
    def __init__(self, excel_configs_path):
        self.configs_path = Path(excel_configs_path)
    
    def update_vendor_reminder_status(self, vendor_id, status):
        """Update vendor reminder status directly in Excel"""
        excel_path = self.configs_path / "01_Daily_Reminders" / "Daily_Vendor_Reminders_Config.xlsx"
        
        try:
            # Create backup
            backup_path = excel_path.with_suffix('.backup.xlsx')
            shutil.copy2(excel_path, backup_path)
            
            # Read and update
            df = pd.read_excel(excel_path)
            mask = df['Vendor_ID'] == vendor_id
            
            if mask.any():
                df.loc[mask, 'Submission_Status'] = status
                df.loc[mask, 'Reminder_Status'] = 'COMPLETED' if status == 'SUBMITTED' else 'PENDING'
                df.loc[mask, 'Last_Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Save back
                df.to_excel(excel_path, index=False)
                print(f"✅ Updated vendor {vendor_id} status to {status}")
                return True
            
        except Exception as e:
            print(f"❌ Error updating vendor status: {e}")
            # Restore backup on error
            if backup_path.exists():
                shutil.copy2(backup_path, excel_path)
        
        return False
```

## Phase 4: Power Automate Flow Updates for File Monitoring

### Updated Flow 4: Mismatch Alerts (File Monitoring)

1. **Create Flow**
   - Name: "ATTENDO - Mismatch File Monitor"
   - Trigger: "When a file is created"

2. **Trigger Configuration**
   - **Site Address**: OneDrive for Business
   - **Folder ID**: `/ATTENDO_Notifications/Trigger_Files/Mismatch_Alerts/`

3. **Flow Steps**:
   ```
   1. When a file is created (Trigger)
   2. Get file content
   3. Parse JSON content
   4. Condition: Check urgency level
   5a. If HIGH urgency:
       - Send immediate Teams message
       - Send priority email
   5b. If MEDIUM urgency:
       - Send standard email
   6. Move file to processed folder
   7. Update tracking log
   ```

4. **Parse JSON Action**
   - **Action**: "Parse JSON"
   - **Content**: File content from step 2
   - **Schema**:
   ```json
   {
     "type": "object",
     "properties": {
       "trigger_type": {"type": "string"},
       "vendor_id": {"type": "string"},
       "manager_id": {"type": "string"},
       "mismatch_type": {"type": "string"},
       "details": {"type": "object"},
       "urgency": {"type": "string"}
     }
   }
   ```

### Updated Flow 5: Feedback Monitor

Similar structure but monitors `/Trigger_Files/Feedback_Notifications/`

## Phase 5: Testing Strategy for Enterprise Environment

### Test 1: File Drop Mechanism
```python
# Test script to verify file drop triggers
def test_enterprise_triggers():
    notifier = EnterpriseNotificationTrigger("C:/Users/YourUser/OneDrive - Company")
    
    # Test mismatch alert
    test_mismatch = {
        'type': 'SWIPE_WEB_MISMATCH',
        'description': 'Test mismatch for validation',
        'critical': True
    }
    
    success = notifier.trigger_mismatch_alert("TEST001", "MGR001", test_mismatch)
    print(f"Mismatch alert test: {'✅ PASS' if success else '❌ FAIL'}")
    
    # Test feedback notification
    success = notifier.trigger_feedback_notification(
        "TEST001", "REJECTION", "Test feedback", "MGR001"
    )
    print(f"Feedback notification test: {'✅ PASS' if success else '❌ FAIL'}")

if __name__ == "__main__":
    test_enterprise_triggers()
```

## Phase 6: Monitoring and Maintenance

### File-based Monitoring
- Monitor OneDrive sync status
- Check for failed file operations
- Regular cleanup of processed files

### Flow Health Monitoring
- Daily flow run reports
- Error notification setup
- Performance metrics tracking

## Security Benefits of This Approach

✅ **No external webhooks** - All triggers are internal
✅ **File-based audit trail** - Every trigger creates a traceable file
✅ **OneDrive security** - Inherits enterprise OneDrive security
✅ **No open ports** - No network endpoints exposed
✅ **Gradual processing** - Files are processed in order
✅ **Backup friendly** - All trigger data is backed up with OneDrive

## Migration Timeline

**Week 1**: Setup OneDrive structure and scheduled flows (1, 2, 6, 8)
**Week 2**: Implement file monitoring flows (3, 4, 5, 7, 9, 10)
**Week 3**: Update Python integration code
**Week 4**: Testing and validation
**Week 5**: Production deployment and monitoring setup

This enterprise-safe approach provides the same functionality as webhooks while staying within your security constraints!
