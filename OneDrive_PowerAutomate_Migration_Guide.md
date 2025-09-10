# OneDrive & Power Automate Notification System Migration Guide

## Overview
This guide provides detailed steps to migrate your 10 Excel notification configurations from local storage to OneDrive and set up Power Automate workflows for each notification type.

## Prerequisites
- Microsoft 365 Business Account
- OneDrive for Business access
- Power Automate license (included with most M365 plans)
- Admin permissions for creating flows

## Phase 1: OneDrive Setup and File Migration

### Step 1: Create OneDrive Folder Structure

1. **Open OneDrive for Business**
   - Go to [office.com](https://office.com)
   - Sign in with your organizational account
   - Click OneDrive

2. **Create Main Folder Structure**
   ```
   📁 ATTENDO_Notifications/
   ├── 📁 Active_Configs/          (Current notification configurations)
   ├── 📁 Processed/              (Archive processed notifications)
   ├── 📁 Templates/              (Template files)
   ├── 📁 Logs/                   (Power Automate logs)
   └── 📁 Backups/               (Daily backups)
   ```

3. **Create Sub-folders in Active_Configs**
   ```
   📁 Active_Configs/
   ├── 📁 01_Daily_Reminders/
   ├── 📁 02_Manager_Summary/
   ├── 📁 03_Manager_Complete/
   ├── 📁 04_Mismatch_Alerts/
   ├── 📁 05_Manager_Feedback/
   ├── 📁 06_Monthly_Reports/
   ├── 📁 07_Admin_Alerts/
   ├── 📁 08_Holiday_Reminders/
   ├── 📁 09_Late_Submissions/
   └── 📁 10_Billing_Corrections/
   ```

### Step 2: Upload and Configure Excel Files

For each notification type, follow this process:

#### 2.1 Daily Status Reminders (01_daily_status_reminders.xlsx)

1. **Upload File**
   - Navigate to `Active_Configs/01_Daily_Reminders/`
   - Upload `01_daily_status_reminders.xlsx`
   - Rename to `Daily_Vendor_Reminders_Config.xlsx`

2. **Configure Table Format**
   - Open file in Excel Online
   - Select data range
   - Go to Home > Format as Table
   - Choose a table style
   - Name the table: `VendorReminderConfig`
   - Ensure these columns exist:
     - `Primary_Key` (unique identifier)
     - `Contact_Email` (email address)
     - `Send_Notification` (YES/NO trigger)
     - `Active` (YES/NO status)
     - `Reminder_Status` (PENDING/COMPLETED)
     - `Daily_Status_Date` (today's date)

3. **Set Sharing Permissions**
   - Click Share button
   - Add service accounts/team members
   - Set permission to "Edit"
   - Copy sharing link for Power Automate

#### 2.2 Manager Summary Notifications (02_manager_summary_notifications.xlsx)

1. **Upload Process**
   - Navigate to `Active_Configs/02_Manager_Summary/`
   - Upload `02_manager_summary_notifications.xlsx`
   - Rename to `Manager_Summary_Config.xlsx`

2. **Table Configuration**
   - Format as table named: `ManagerSummaryConfig`
   - Key columns:
     - `Manager_ID`
     - `Contact_Email`
     - `Send_Notification`
     - `Team_Size`
     - `Submitted_Count`
     - `Pending_Count`
     - `Completion_Rate`

3. **Set Permissions**
   - Share with appropriate managers
   - Enable editing for system account

#### 2.3 Manager All-Complete Notifications (03_manager_all_complete_notifications.xlsx)

1. **Upload Process**
   - Navigate to `Active_Configs/03_Manager_Complete/`
   - Upload and rename to `Manager_Complete_Config.xlsx`

2. **Table Setup**
   - Table name: `ManagerCompleteConfig`
   - Key trigger column: `Trigger_Condition` = "ALL_TEAM_SUBMITTED"

#### 2.4 Mismatch Notifications (04_mismatch_notifications.xlsx)

1. **Upload Process**
   - Navigate to `Active_Configs/04_Mismatch_Alerts/`
   - Rename to `Mismatch_Alerts_Config.xlsx`

2. **Table Setup**
   - Table name: `MismatchConfig`
   - Key columns:
     - `Role` (MANAGER/VENDOR)
     - `Mismatch_Types`
     - `Alert_Required` (YES/NO)

#### 2.5 Manager Feedback Notifications (05_manager_feedback_notifications.xlsx)

1. **Upload Process**
   - Navigate to `Active_Configs/05_Manager_Feedback/`
   - Rename to `Manager_Feedback_Config.xlsx`

2. **Table Setup**
   - Table name: `FeedbackConfig`
   - Trigger on: `Feedback_Types` and approval status changes

#### 2.6 Monthly Report Notifications (06_monthly_report_notifications.xlsx)

1. **Upload Process**
   - Navigate to `Active_Configs/06_Monthly_Reports/`
   - Rename to `Monthly_Reports_Config.xlsx`

2. **Table Setup**
   - Table name: `MonthlyReportConfig`
   - Schedule trigger: `Generation_Day` = 1

#### 2.7 Admin System Alerts (07_admin_system_alerts.xlsx)

1. **Upload Process**
   - Navigate to `Active_Configs/07_Admin_Alerts/`
   - Rename to `Admin_Alerts_Config.xlsx`

2. **Table Setup**
   - Table name: `AdminAlertConfig`
   - Priority-based triggers: `Severity_Levels`

#### 2.8 Holiday Reminder Notifications (08_holiday_reminder_notifications.xlsx)

1. **Upload Process**
   - Navigate to `Active_Configs/08_Holiday_Reminders/`
   - Rename to `Holiday_Reminders_Config.xlsx`

2. **Table Setup**
   - Table name: `HolidayConfig`
   - Date-based triggers: `Advance_Notice_Days`

#### 2.9 Late Submission Alerts (09_late_submission_alerts.xlsx)

1. **Upload Process**
   - Navigate to `Active_Configs/09_Late_Submissions/`
   - Rename to `Late_Submissions_Config.xlsx`

2. **Table Setup**
   - Table name: `LateSubmissionConfig`
   - Time-based triggers: `Alert_After_Hours`

#### 2.10 Billing Correction Notifications (10_billing_correction_notifications.xlsx)

1. **Upload Process**
   - Navigate to `Active_Configs/10_Billing_Corrections/`
   - Rename to `Billing_Corrections_Config.xlsx`

2. **Table Setup**
   - Table name: `BillingConfig`
   - Financial change triggers: `Correction_Types`

## Phase 2: Power Automate Flow Creation

### Power Automate Flow Templates

For each notification type, create a dedicated Power Automate flow:

#### Flow 1: Daily Vendor Reminders

1. **Create New Flow**
   - Go to [make.powerautomate.com](https://make.powerautomate.com)
   - Click "Create" > "Scheduled cloud flow"
   - Name: "ATTENDO - Daily Vendor Reminders"
   - Frequency: Every 3 hours (9 AM to 6 PM)

2. **Add Trigger**
   - **Trigger**: Recurrence
   - **Interval**: 3 hours
   - **Start Time**: 09:00 AM
   - **Time Zone**: Your local timezone
   - **On these days**: Monday through Friday

3. **Add OneDrive Connection**
   - **Action**: "List rows present in a table"
   - **Location**: OneDrive for Business
   - **Document Library**: OneDrive
   - **File**: `/ATTENDO_Notifications/Active_Configs/01_Daily_Reminders/Daily_Vendor_Reminders_Config.xlsx`
   - **Table**: VendorReminderConfig

4. **Add Filter Condition**
   - **Action**: "Condition"
   - **Left operand**: `Send_Notification`
   - **Operator**: is equal to
   - **Right operand**: YES
   - **AND condition**: `Active` is equal to YES
   - **AND condition**: `Reminder_Status` is equal to PENDING

5. **Add Email Action (Yes Branch)**
   - **Action**: "Send an email (V2)"
   - **To**: `Contact_Email` (dynamic content)
   - **Subject**: "Daily Status Reminder - Please Submit Today's Attendance"
   - **Body**: 
   ```html
   <html>
   <body>
   <h3>Daily Attendance Status Reminder</h3>
   <p>Hi @{items('Apply_to_each')['Contact_Name']},</p>
   <p>This is a friendly reminder to submit your daily attendance status.</p>
   <p><strong>Department:</strong> @{items('Apply_to_each')['Department']}</p>
   <p><strong>Manager:</strong> @{items('Apply_to_each')['Manager_ID']}</p>
   <p>Please log in to the ATTENDO system to submit your status.</p>
   <p>Best regards,<br>ATTENDO System</p>
   </body>
   </html>
   ```

6. **Add Teams Message (Optional)**
   - **Action**: "Post message in a chat or channel"
   - **Post as**: User
   - **Post in**: Chat with user
   - **Recipient**: `Contact_Email`
   - **Message**: "Daily status reminder: Please submit your attendance for today."

7. **Add Update Row Action**
   - **Action**: "Update a row"
   - **Location**: OneDrive for Business
   - **Document Library**: OneDrive
   - **File**: Same Excel file
   - **Table**: VendorReminderConfig
   - **Row ID**: `Primary_Key`
   - **Last_Reminder_Sent**: `utcNow()`

#### Flow 2: Manager Summary Notifications

1. **Create Flow**
   - Name: "ATTENDO - Manager Summary"
   - Trigger: Recurrence (12:00 PM and 2:00 PM daily)

2. **Trigger Setup**
   - **Frequency**: Daily
   - **At these hours**: 12, 14
   - **At these minutes**: 0

3. **Read Manager Config**
   - **Action**: "List rows present in a table"
   - **File**: `/ATTENDO_Notifications/Active_Configs/02_Manager_Summary/Manager_Summary_Config.xlsx`
   - **Table**: ManagerSummaryConfig

4. **Filter Active Managers**
   - **Condition**: `Send_Notification` equals YES AND `Active` equals YES

5. **Send Summary Email**
   - **To**: `Contact_Email`
   - **Subject**: "Team Attendance Summary - @{formatDateTime(utcNow(), 'MM/dd/yyyy')}"
   - **Body**: 
   ```html
   <h3>Daily Team Summary</h3>
   <p>Hi @{items('Apply_to_each')['Contact_Name']},</p>
   <table border="1" style="border-collapse: collapse;">
     <tr><th>Metric</th><th>Count</th></tr>
     <tr><td>Team Size</td><td>@{items('Apply_to_each')['Team_Size']}</td></tr>
     <tr><td>Submitted</td><td>@{items('Apply_to_each')['Submitted_Count']}</td></tr>
     <tr><td>Pending</td><td>@{items('Apply_to_each')['Pending_Count']}</td></tr>
     <tr><td>Completion Rate</td><td>@{items('Apply_to_each')['Completion_Rate']}%</td></tr>
   </table>
   ```

#### Flow 3: Manager All-Complete Notifications

1. **Create Flow**
   - Name: "ATTENDO - Team Complete Notifications"
   - Trigger: When an item is created or modified (Excel row)

2. **Trigger Setup**
   - **Action**: "When an item is created or modified"
   - **Site Address**: Your OneDrive URL
   - **List Name**: Manager_Complete_Config table

3. **Condition Check**
   - **Left**: `Trigger_Condition`
   - **Operator**: is equal to
   - **Right**: "ALL_TEAM_SUBMITTED"

4. **Send Completion Email**
   - Subject: "🎉 Team Complete - All Members Submitted Today"
   - Body with team statistics and next actions

#### Flow 4: Mismatch Alert Notifications

1. **Create Flow**
   - Name: "ATTENDO - Mismatch Alerts"
   - Trigger: HTTP request (webhook from your system)

2. **Trigger Setup**
   - **Trigger**: "When an HTTP request is received"
   - **Request Body JSON Schema**:
   ```json
   {
     "type": "object",
     "properties": {
       "mismatch_type": {"type": "string"},
       "vendor_id": {"type": "string"},
       "manager_id": {"type": "string"},
       "details": {"type": "object"}
     }
   }
   ```

3. **Read Mismatch Config**
   - Get recipients based on role and mismatch type

4. **Send Alert Emails**
   - Customized based on recipient role (manager vs vendor)

#### Flow 5: Manager Feedback Notifications

1. **Create Flow**
   - Name: "ATTENDO - Manager Feedback"
   - Trigger: HTTP request (when manager takes action)

2. **Process Feedback**
   - Read feedback configuration
   - Send appropriate notification to vendor
   - Update status in Excel

#### Flow 6: Monthly Report Notifications

1. **Create Flow**
   - Name: "ATTENDO - Monthly Reports"
   - Trigger: Scheduled monthly (1st day)

2. **Generate Reports**
   - Read monthly configuration
   - Compile data from system
   - Send comprehensive reports

#### Flow 7: Admin System Alerts

1. **Create Flow**
   - Name: "ATTENDO - Admin Alerts"
   - Trigger: HTTP request (system errors)

2. **Priority-Based Processing**
   - CRITICAL: Immediate Teams + Email + SMS
   - HIGH: Teams + Email
   - MEDIUM: Email only

#### Flow 8: Holiday Reminders

1. **Create Flow**
   - Name: "ATTENDO - Holiday Reminders"
   - Trigger: Daily check for upcoming holidays

2. **Holiday Logic**
   - Check upcoming holidays (advance notice days)
   - Send reminders to all users

#### Flow 9: Late Submission Alerts

1. **Create Flow**
   - Name: "ATTENDO - Late Submissions"
   - Trigger: Daily at 6 PM

2. **Check Late Submissions**
   - Identify late vendors
   - Alert managers
   - Update Excel tracking

#### Flow 10: Billing Correction Notifications

1. **Create Flow**
   - Name: "ATTENDO - Billing Corrections"
   - Trigger: HTTP request (billing changes)

2. **Financial Notifications**
   - High-priority for monetary adjustments
   - Require acknowledgment

## Phase 3: Integration with Your Python System

### Update Your Python Code

Add webhook integration to trigger Power Automate flows:

```python
import requests
import json

class PowerAutomateIntegration:
    def __init__(self):
        self.webhook_urls = {
            'mismatch_alert': 'https://prod-xx.westus.logic.azure.com:443/workflows/.../triggers/manual/paths/invoke',
            'feedback_notification': 'https://prod-xx.westus.logic.azure.com:443/workflows/.../triggers/manual/paths/invoke',
            'late_submissions': 'https://prod-xx.westus.logic.azure.com:443/workflows/.../triggers/manual/paths/invoke',
            # Add other webhook URLs
        }
    
    def trigger_mismatch_alert(self, vendor_id, manager_id, mismatch_details):
        payload = {
            'mismatch_type': mismatch_details.get('type'),
            'vendor_id': vendor_id,
            'manager_id': manager_id,
            'details': mismatch_details
        }
        
        response = requests.post(
            self.webhook_urls['mismatch_alert'],
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        return response.status_code == 200
    
    def trigger_feedback_notification(self, vendor_id, feedback_type, manager_comments):
        payload = {
            'vendor_id': vendor_id,
            'feedback_type': feedback_type,
            'manager_comments': manager_comments,
            'timestamp': datetime.now().isoformat()
        }
        
        requests.post(self.webhook_urls['feedback_notification'], json=payload)

# Integration in your existing code
pa_integration = PowerAutomateIntegration()

# In daily_excel_updater.py, modify these methods:
def trigger_power_automate_refresh(self):
    """Updated method to work with OneDrive"""
    # Update OneDrive Excel files instead of local files
    # Power Automate will automatically detect changes
    
def send_mismatch_alert(self, vendor_id, manager_id, mismatch_data):
    """New method to trigger mismatch alerts"""
    pa_integration.trigger_mismatch_alert(vendor_id, manager_id, mismatch_data)
```

## Phase 4: Testing and Validation

### Testing Each Flow

1. **Test Daily Reminders**
   - Manually run the flow
   - Verify emails are sent
   - Check Excel updates

2. **Test Manager Summaries**
   - Update Excel with test data
   - Verify summary calculations
   - Confirm email formatting

3. **Test Webhook Flows**
   - Use Postman or similar tool
   - Send test JSON payloads
   - Verify processing

### Monitoring Setup

1. **Power Automate Monitoring**
   - Enable run history
   - Set up failure notifications
   - Monitor flow performance

2. **Excel File Monitoring**
   - Set up OneDrive version history
   - Regular backup automation
   - Access log monitoring

## Phase 5: Deployment and Maintenance

### Go-Live Process

1. **Gradual Migration**
   - Start with one notification type
   - Test thoroughly
   - Migrate others incrementally

2. **User Training**
   - Update documentation
   - Train managers on new system
   - Create troubleshooting guides

3. **Monitoring**
   - Daily flow health checks
   - Weekly Excel file reviews
   - Monthly performance analysis

### Maintenance Tasks

1. **Daily**
   - Check flow run status
   - Verify critical notifications

2. **Weekly**
   - Review Excel file updates
   - Check error logs
   - Validate notification accuracy

3. **Monthly**
   - Performance optimization
   - User feedback review
   - System updates

## Troubleshooting Common Issues

### Flow Failures
- **Symptom**: Flow not triggering
- **Solution**: Check trigger conditions and Excel table format

### Email Delivery Issues
- **Symptom**: Emails not received
- **Solution**: Verify recipient email addresses and spam filters

### Excel Connection Problems
- **Symptom**: "File not found" errors
- **Solution**: Verify OneDrive permissions and file paths

### Performance Issues
- **Symptom**: Slow notification delivery
- **Solution**: Optimize conditions and reduce data processing

## Security Considerations

1. **Access Control**
   - Limit Excel file editing permissions
   - Use service accounts for automation
   - Regular permission audits

2. **Data Protection**
   - Enable OneDrive encryption
   - Audit trail for changes
   - Backup sensitive configurations

3. **Compliance**
   - GDPR considerations for email data
   - Retention policies for logs
   - Security monitoring

This migration will provide you with a robust, cloud-based notification system that's more reliable, scalable, and easier to maintain than the current local setup.
