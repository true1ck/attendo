# 🔗 Microsoft Power Automate Integration Guide

## Overview

All 10 Excel notification configuration files have been updated with **properly formatted tables** that are ready for Microsoft Power Automate integration. Each file contains a structured table that Power Automate can easily read, modify, and use to trigger notifications.

## 📊 Excel Tables Created

| File | Table Name | Purpose | Example Power Automate Use |
|------|------------|---------|---------------------------|
| `01_daily_status_reminders.xlsx` | `DailyStatusReminders` | Vendor reminder configurations | Trigger hourly flow to check for late submissions |
| `02_manager_summary_notifications.xlsx` | `ManagerSummaryNotifications` | Manager summary settings | Schedule 12 PM and 2 PM team status reports |
| `03_manager_all_complete_notifications.xlsx` | `AllCompleteNotifications` | All-team-complete alerts | Trigger when all team members submit status |
| `04_mismatch_notifications.xlsx` | `MismatchNotifications` | Mismatch alert configurations | Send alerts when attendance mismatches detected |
| `05_manager_feedback_notifications.xlsx` | `ManagerFeedbackNotifications` | Feedback notification settings | Notify vendors of manager approval/rejection |
| `06_monthly_report_notifications.xlsx` | `MonthlyReportNotifications` | Monthly report delivery | Auto-generate and email monthly reports |
| `07_admin_system_alerts.xlsx` | `AdminSystemAlerts` | System alert configurations | Critical system notifications to admins |
| `08_holiday_reminder_notifications.xlsx` | `HolidayReminderNotifications` | Holiday reminder settings | Notify all users of upcoming holidays |
| `09_late_submission_alerts.xlsx` | `LateSubmissionAlerts` | Late submission configurations | Alert managers about late submissions |
| `10_billing_correction_notifications.xlsx` | `BillingCorrectionNotifications` | Billing alert settings | Notify about billing adjustments |

## 🎯 Table Structure

Each Excel table follows a consistent structure with these key columns:

### **Core Identification**
- `Primary_Key` - Unique identifier for the configuration
- `Contact_Email` - Email address for notifications
- `Contact_Name` - Full name of the recipient
- `Role` - User role (VENDOR, MANAGER, ADMIN)

### **Control Fields**
- `Send_Notification` - YES/NO toggle to enable/disable
- `Active` - YES/NO to activate/deactivate configuration
- `Notification_Method` - Comma-separated methods (TEAMS,EMAIL,SMS)
- `Priority` - Notification priority (LOW, MEDIUM, HIGH, CRITICAL)

### **Timing Controls**
- `Notification_Times` - Specific times (e.g., "12:00,14:00")
- `Weekdays_Only` - YES/NO to limit to weekdays
- `Exclude_Holidays` - YES/NO to skip holidays

### **Content Options**
- `Custom_Message` - Custom message template
- `Teams_Channel` - Teams channel identifier
- `Phone_Number` - For SMS notifications
- Various `Include_*` fields for content customization

### **Audit Trail**
- `Created_Date` - When configuration was created
- `Last_Modified` - Last modification timestamp

## 🔧 Power Automate Integration Steps

### 1. **Connect to Excel Tables**

In Power Automate, use the **Excel Online (Business)** connector:

1. **Add Action** → **Excel Online (Business)** → **List rows present in a table**
2. **Location**: Choose your SharePoint/OneDrive location
3. **Document Library**: Select library containing notification config files
4. **File**: Choose the specific Excel file (e.g., `01_daily_status_reminders.xlsx`)
5. **Table**: Select the table name (e.g., `DailyStatusReminders`)

### 2. **Filter Active Notifications**

Add a **Filter Array** action to get only active configurations:
- **From**: Dynamic content from Excel rows
- **Condition**: `item()?['Send_Notification']` **is equal to** `YES`
- **And**: `item()?['Active']` **is equal to** `YES`

### 3. **Sample Power Automate Flows**

#### **Daily Status Reminder Flow**

```
Trigger: Recurrence (Every 3 hours, 9 AM to 6 PM, Weekdays)
├── Excel: List rows from DailyStatusReminders table
├── Filter: Only active notifications (Send_Notification = YES)
├── For Each: Active notification configuration
│   ├── Condition: Check current time vs Start_Time/End_Time
│   ├── HTTP: Check ATTENDO API for vendor late submissions
│   ├── Condition: If vendor needs reminder
│   └── Teams/Email: Send notification using config template
└── Log: Record notification sent
```

#### **Manager Summary Flow**

```
Trigger: Recurrence (Every hour)
├── Excel: List rows from ManagerSummaryNotifications table
├── Filter: Notifications for current hour (12:00 or 14:00)
├── For Each: Manager configuration
│   ├── HTTP: Get team status from ATTENDO API
│   ├── Compose: Build summary message using config options
│   └── Teams/Email: Send summary to manager
└── Update Excel: Mark last notification sent
```

#### **Mismatch Alert Flow**

```
Trigger: HTTP Request (from ATTENDO when mismatches detected)
├── Excel: List rows from MismatchNotifications table
├── Filter: Configurations matching affected users
├── For Each: Notification configuration
│   ├── Condition: Check mismatch type vs config Mismatch_Types
│   ├── Compose: Build alert message with mismatch details
│   └── Teams/Email: Send alert using configured method
└── HTTP Response: Confirm notifications sent
```

## 🎨 **Power Automate Actions Available**

### **Excel Actions**
- **List rows present in a table** - Read configuration data
- **Get a row** - Get specific configuration by Primary_Key
- **Add a row** - Add new notification configuration
- **Update a row** - Modify existing configuration
- **Delete a row** - Remove configuration

### **Teams Actions**
- **Post message in a chat or channel** - Send Teams notifications
- **Post adaptive card in a chat or channel** - Rich notifications
- **Create a meeting** - Schedule follow-up meetings

### **Outlook Actions**
- **Send an email (V2)** - Send email notifications
- **Send an email with options** - Request responses
- **Create event** - Add calendar reminders

### **SMS Actions** (via Twilio/other connectors)
- **Send Text Message (SMS)** - Send SMS notifications

## 📋 **Example Power Automate Expressions**

### **Check Time Range**
```javascript
and(
    greater(formatDateTime(utcnow(), 'HH:mm'), item()?['Start_Time']),
    less(formatDateTime(utcnow(), 'HH:mm'), item()?['End_Time'])
)
```

### **Check Weekdays Only**
```javascript
if(
    equals(item()?['Weekdays_Only'], 'YES'),
    and(
        greater(dayOfWeek(utcnow()), 1),
        less(dayOfWeek(utcnow()), 7)
    ),
    true
)
```

### **Build Dynamic Message**
```javascript
if(
    empty(item()?['Custom_Message']),
    'Default notification message',
    item()?['Custom_Message']
)
```

### **Parse Notification Methods**
```javascript
split(item()?['Notification_Method'], ',')
```

## 🔍 **Advanced Power Automate Scenarios**

### **1. Conditional Notification Logic**
Use Switch actions to handle different priority levels:
- **HIGH/CRITICAL**: Send immediately via multiple channels
- **MEDIUM**: Send via primary channel only
- **LOW**: Batch and send once daily

### **2. Escalation Workflows**
For notifications with `Auto_Escalate_Days`:
- Track notification history in SharePoint
- Auto-escalate if no response within specified days
- Send to additional recipients from escalation table

### **3. Response Tracking**
For notifications requiring acknowledgment:
- Generate unique tracking IDs
- Store response requirements in SharePoint
- Follow up with non-responders automatically

### **4. Dynamic Content Integration**
Connect to ATTENDO APIs to get real-time data:
- Vendor attendance status
- Manager team information
- System health metrics
- Mismatch detection results

## 📊 **Power Automate Dashboard Integration**

### **Create Power BI Reports**
- Connect Power BI to Excel tables
- Create notification effectiveness dashboards
- Track delivery rates and response times
- Monitor configuration changes over time

### **SharePoint Integration**
- Store Excel files in SharePoint for team access
- Use SharePoint lists for notification history
- Create approval workflows for configuration changes
- Version control for notification templates

## 🛠️ **Maintenance & Updates**

### **Configuration Management**
- **Add Recipients**: Insert new rows in Excel tables
- **Disable Notifications**: Change `Active` to `NO`
- **Update Timing**: Modify time fields directly in Excel
- **Change Messages**: Edit `Custom_Message` column

### **Monitoring Flows**
Create monitoring flows to:
- Check for failed notification deliveries
- Alert when configuration tables are modified
- Validate table structure after updates
- Generate weekly notification summary reports

## 🚀 **Best Practices**

### **Performance Optimization**
- Use **Parallel Branches** for multiple notification methods
- **Batch** similar operations where possible
- **Cache** frequently accessed data using variables
- **Limit** table queries with appropriate filters

### **Error Handling**
- Add **Try-Catch** scopes around critical actions
- **Log errors** to SharePoint or email admins
- **Retry** failed operations with exponential backoff
- **Graceful degradation** when services are unavailable

### **Security**
- Use **Service Principal** accounts for Excel access
- **Encrypt** sensitive data in custom messages
- **Audit** all notification configuration changes
- **Limit** access to configuration tables

## 📱 **Mobile Integration**

### **Power Apps Integration**
- Create Power Apps for mobile notification management
- Allow managers to update their notification preferences
- Provide real-time notification status dashboard
- Enable quick configuration toggles

### **Teams Mobile**
- Optimize notification messages for mobile Teams app
- Use **Adaptive Cards** for rich mobile experiences
- Enable **Quick Actions** in notification messages
- Support **Push Notifications** for critical alerts

---

## 🔄 **Real-Time Database Sync Integration**

### **Automatic Excel Table Updates**

The notification system now includes **real-time database synchronization** to keep Excel tables updated automatically when users are added, removed, or modified in the ATTENDO system.

#### **🚀 Real-Time Sync Features:**

- **Database Change Detection** - Automatic sync when users/vendors/managers are modified
- **Scheduled Synchronization** - Regular updates every 5 minutes
- **Webhook Integration** - Power Automate can trigger sync operations
- **Validation & Monitoring** - Continuous health checks and sync validation
- **Error Recovery** - Automatic repair of sync issues

#### **📡 Power Automate Webhook Endpoints**

**Trigger Manual Sync:**
```
POST /api/sync/trigger
Content-Type: application/json

{
  "event_type": "manual_trigger",
  "entity_type": "all",
  "force_sync": true
}
```

**Power Automate Integration Webhook:**
```
POST /api/sync/webhook/power-automate
Content-Type: application/json

{
  "syncType": "full",
  "targetFiles": ["01_daily_status_reminders.xlsx"],
  "forceSync": false
}
```

**Get Sync Status:**
```
GET /api/sync/status

Response:
{
  "status": "running",
  "queue_size": 0,
  "metrics": {
    "total_syncs": 45,
    "successful_syncs": 44,
    "failed_syncs": 1,
    "last_sync_time": "2025-01-09T17:45:00Z"
  }
}
```

#### **🔍 Monitoring & Validation Endpoints**

**Health Check:**
```
GET /api/monitor/check

Response:
{
  "status": "success",
  "health_check": {
    "database_connection": true,
    "excel_access": true,
    "realtime_sync_status": "running",
    "failures_detected": false,
    "issues": []
  }
}
```

**Validate Sync Accuracy:**
```
GET /api/monitor/validate

Response:
{
  "status": "success",
  "validation": {
    "total_files": 10,
    "files_checked": 10,
    "sync_issues": [],
    "database_user_count": 125
  }
}
```

**Auto-Repair Sync Issues:**
```
GET /api/monitor/repair

Response:
{
  "status": "success",
  "issues_before": 3,
  "issues_after": 0,
  "issues_fixed": 3
}
```

### **🔄 Advanced Power Automate Flows**

#### **Real-Time Sync Monitor Flow**

```
Trigger: Recurrence (Every 30 minutes)
├── HTTP: GET /api/sync/status
├── Condition: Check if sync failures > 0
│   ├── Yes: Send alert to Teams channel
│   └── HTTP: POST /api/sync/trigger (force sync)
└── Log: Record monitoring result
```

#### **Database Change Response Flow**

```
Trigger: When a user is added/updated in ATTENDO
├── Delay: Wait 2 minutes (batch changes)
├── HTTP: POST /api/sync/webhook/power-automate
│   ├── Body: { "syncType": "full", "forceSync": true }
├── Condition: Check sync success
│   ├── Success: Update tracking list
│   └── Failure: Alert administrators
└── Teams: Notify relevant managers of new users
```

#### **Validation & Repair Flow**

```
Trigger: Recurrence (Every 6 hours)
├── HTTP: GET /api/monitor/validate
├── Condition: Check for sync issues
│   ├── Issues Found:
│   │   ├── HTTP: GET /api/monitor/repair
│   │   ├── Teams: Alert administrators
│   │   └── Email: Send detailed report
│   └── No Issues: Log successful validation
└── SharePoint: Update monitoring dashboard
```

### **🎛️ Configuration Management**

#### **Dynamic Webhook Registration**

Register Power Automate webhooks automatically:

```javascript
// In Power Automate HTTP action
{
  "method": "POST",
  "uri": "https://your-attendo-server.com/api/sync/webhook/register",
  "body": {
    "webhook_url": "@{triggerOutputs()['headers']['Location']}",
    "webhook_type": "power_automate",
    "description": "Main notification sync webhook"
  }
}
```

#### **Environment Configuration**

Add these to your ATTENDO app configuration:

```python
# Real-time sync settings
SYNC_INTERVAL_MINUTES = 5
WEBHOOK_TIMEOUT_SECONDS = 30
ENABLE_POWER_AUTOMATE_WEBHOOKS = True

# Power Automate webhook URLs
POWER_AUTOMATE_WEBHOOK_URLS = [
    "https://prod-xx.westus.logic.azure.com/workflows/...",
    "https://prod-yy.westus.logic.azure.com/workflows/..."
]

# Monitoring settings
SYNC_MONITORING_INTERVAL_MINUTES = 30
SYNC_VALIDATION_INTERVAL_HOURS = 6
ADMIN_EMAILS = ["admin@yourcompany.com"]

# Email alerts
SYNC_ALERT_FROM = "attendo-sync@yourcompany.com"
SMTP_SERVER = "smtp.yourcompany.com"
SMTP_PORT = 587
```

### **📊 Power BI Integration**

#### **Real-Time Sync Metrics Dashboard**

Connect Power BI to sync metrics:

```
Data Source: Web
URL: https://your-attendo-server.com/api/sync/status
Refresh: Every 15 minutes

Metrics:
- Total sync operations
- Success rate
- Average sync duration
- Queue size
- Last sync time
```

#### **Sync Health Dashboard**

```
Data Source: Web
URL: https://your-attendo-server.com/api/monitor/status
Refresh: Every 30 minutes

Visualizations:
- Database connection status
- Excel file access status
- Active alerts count
- Sync validation results
```

### **🚨 Alert Configuration**

#### **Teams Channel Alerts**

```
Trigger: HTTP request from sync monitor
├── Parse JSON: Extract alert details
├── Condition: Check severity level
│   ├── Critical: @everyone mention
│   ├── Warning: @channel mention
│   └── Info: Normal message
├── Adaptive Card: Format alert message
└── Teams: Post to notification channel
```

#### **Email Alert Template**

```html
<h2>🔄 ATTENDO Sync Alert</h2>
<table>
  <tr><td><strong>Type:</strong></td><td>@{triggerBody()['alert']['type']}</td></tr>
  <tr><td><strong>Severity:</strong></td><td>@{triggerBody()['alert']['severity']}</td></tr>
  <tr><td><strong>Time:</strong></td><td>@{triggerBody()['alert']['timestamp']}</td></tr>
  <tr><td><strong>Message:</strong></td><td>@{triggerBody()['alert']['message']}</td></tr>
</table>

<h3>Quick Actions</h3>
<a href="https://your-attendo-server.com/api/monitor/repair">🔧 Auto-Repair</a>
<a href="https://your-attendo-server.com/api/sync/trigger">🔄 Force Sync</a>
```

### **🛡️ Security & Best Practices**

#### **Webhook Security**

- Use **HTTPS** for all webhook URLs
- Implement **request signing** for webhook validation
- Set **timeout limits** for webhook calls (30 seconds)
- Use **retry logic** with exponential backoff

#### **Rate Limiting**

```javascript
// In Power Automate, add delay between sync operations
{
  "delay": {
    "count": 30,
    "unit": "Second"
  }
}
```

#### **Error Handling**

```javascript
// Scope with try-catch pattern
{
  "scope": {
    "actions": {
      "Sync_Operation": {
        "type": "Http",
        "inputs": {
          "uri": "https://your-server.com/api/sync/trigger"
        }
      }
    },
    "runAfter": {},
    "type": "Scope"
  },
  "Handle_Error": {
    "runAfter": {
      "scope": ["Failed"]
    },
    "type": "Compose",
    "inputs": "Sync failed: @{outputs('scope')}"
  }
}
```

---

## 🎉 **Ready to Use!**

All Excel tables are now **properly formatted** and **Power Automate ready** with **real-time database synchronization**! Each table includes:

✅ **Structured Data** - Consistent column formats  
✅ **Sample Records** - Multiple example configurations  
✅ **Table Names** - Easy Power Automate reference  
✅ **Rich Metadata** - Complete configuration options  
✅ **Auto-formatting** - Professional Excel styling  
✅ **Real-Time Sync** - Automatic updates from database changes  
✅ **Monitoring & Alerts** - Continuous health checking  
✅ **Webhook Integration** - Power Automate triggers  
✅ **Error Recovery** - Automatic issue detection and repair  

**Start building your automated notification system today** with full real-time synchronization!

### **🚀 Implementation Steps:**
1. **Deploy** the real-time sync system to your ATTENDO server
2. **Configure** webhook URLs in Power Automate
3. **Upload** Excel files to SharePoint/OneDrive
4. **Create** Power Automate flows using the webhook endpoints
5. **Set up** monitoring dashboards in Power BI
6. **Configure** alert channels (Teams/Email)
7. **Test** the complete sync and notification pipeline
8. **Monitor** system health and optimize as needed
