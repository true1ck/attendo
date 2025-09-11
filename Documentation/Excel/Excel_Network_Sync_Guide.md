# Excel Network Sync Guide

## Overview
The Excel sync system is designed to maintain different structures for local and network folders:
- **Local Folder** (`notification_configs`): Maintains original Excel structure for internal use
- **Network Folder** (configurable via UI): Populated with vendor data in Power Automate format

## Key Features

### 1. Separate Handling for Local vs Network
- Local files remain unchanged during sync operations
- Network files are automatically populated with vendor data from the database
- Network folder path is configurable through the admin UI

### 2. Vendor Data Population
When syncing to the network folder, Excel files are populated with:
- **EmployeeID**: Actual vendor IDs from the `vendors` table (e.g., EMP001, EMP002)
- **ContactEmail**: Vendor email addresses from the database
- **Message**: Context-appropriate notification messages
- **NotificationType**: Appropriate type for each file (Daily Reminder, Mismatch Alert, etc.)
- **Priority**: Dynamic priority based on notification type

## Network Folder Configuration

### Via Admin UI
1. Navigate to `/admin/excel-sync`
2. Click on "Configure Network Folder"
3. Enter the network path (e.g., `G:\Test` or `\\server\share\notifications`)
4. Save the configuration

### Via API
```bash
POST /api/excel-sync/config
Content-Type: application/json

{
    "network_folder": "G:\\Test"
}
```

## Sync Operations

### Automatic Sync
The system automatically syncs files every 10 minutes when the sync service is running:
1. Copies files from local folder
2. Populates them with vendor data
3. Saves to configured network folder

### Manual Sync
```bash
POST /api/excel-sync/force
```
Triggers immediate sync with vendor data population.

### Populate Vendor Data Only
```bash
POST /api/excel-sync/populate-vendor-data
Content-Type: application/json

{
    "network_folder": "G:\\Test"  # Optional, uses configured path if not specified
}
```
Populates network folder with vendor data without copying from local.

## Data Mapping

### Database to Excel Column Mapping

| Database Column | Excel Column | Description |
|----------------|--------------|-------------|
| `vendor_id` | EmployeeID | Unique vendor identifier |
| `email` (from users table) | ContactEmail | Vendor email address |
| Custom generated | Message | Context-appropriate notification message |
| Based on file type | NotificationType | Daily Reminder, Mismatch Alert, etc. |
| Dynamic | Priority | High/Medium/Low based on type |

### Notification Type Mapping

| File Name | Notification Type | Default Priority |
|-----------|------------------|------------------|
| 01_daily_status_reminders.xlsx | Daily Reminder | Medium/High |
| 02_manager_summary_notifications.xlsx | Manager Summary | Medium |
| 03_manager_all_complete_notifications.xlsx | Manager Summary | Medium |
| 04_mismatch_notifications.xlsx | Mismatch Alert | High |
| 05_manager_feedback_notifications.xlsx | Manager Summary | Medium |
| 06_monthly_report_notifications.xlsx | Manager Summary | Medium |
| 07_admin_system_alerts.xlsx | System Alert | High |
| 08_holiday_reminder_notifications.xlsx | Holiday Reminder | Medium |
| 09_late_submission_alerts.xlsx | Late Submission | High |

## Example Data Output

### Network Folder File (Power Automate Format)
```
EmployeeID | ContactEmail | Message | NotificationType | Priority
-----------|--------------|---------|------------------|----------
EMP001 | john.vendor@company.com | Please submit your daily timesheet | Daily Reminder | Medium
EMP002 | jane.vendor@company.com | Remember to log your work hours | Daily Reminder | High
EMP003 | mike.vendor@company.com | Timesheet submission deadline approaching | Daily Reminder | Medium
```

### Local Folder File (Original Format)
Can maintain any structure needed for internal processing, not modified by sync.

## Python Script Usage

### Import the Module
```python
from scripts.populate_excel_from_vendors import get_vendor_data, create_notification_excel
```

### Populate Network Folder Only
```python
from scripts.populate_excel_from_vendors import main

# Populate specific network folder
main(network_folder_path='G:/Test')
```

### Get Vendor Data
```python
vendors_data, vendor_emails = get_vendor_data()
# Returns tuples of vendor information and email mappings
```

## API Endpoints

### Sync Control
- `POST /api/excel-sync/control/start` - Start sync service
- `POST /api/excel-sync/control/stop` - Stop sync service
- `POST /api/excel-sync/control/pause` - Pause sync service
- `POST /api/excel-sync/control/resume` - Resume sync service

### Data Operations
- `POST /api/excel-sync/force` - Force immediate sync
- `POST /api/excel-sync/populate-vendor-data` - Populate with vendor data
- `GET /api/excel-sync/status` - Get sync status

### Configuration
- `POST /api/excel-sync/config` - Configure network folder path

## Troubleshooting

### No Vendor Data in Files
1. Check database connection
2. Verify vendors table has data
3. Check logs for errors during population

### Network Folder Access Issues
1. Verify network path is accessible
2. Check write permissions
3. Ensure path format is correct (use backslashes for Windows)

### Sync Not Working
1. Check if sync service is running
2. Verify network folder is configured
3. Check error logs in admin dashboard

## Best Practices

1. **Test Network Path**: Before configuring, ensure the network path is accessible
2. **Regular Monitoring**: Check sync status regularly in admin dashboard
3. **Database Maintenance**: Keep vendor data up-to-date in the database
4. **Backup Strategy**: Network files are overwritten on each sync, maintain backups if needed
5. **Access Control**: Ensure proper permissions on network folder for Power Automate access

## Power Automate Integration

Power Automate flows should:
1. Read from the network folder (not local)
2. Use the table name "NotificationTable" 
3. Reference columns exactly as: EmployeeID, ContactEmail, Message, NotificationType, Priority
4. Schedule based on your sync interval (default 10 minutes)

## System Architecture

```
[Database: vendors table]
         ↓
[populate_excel_from_vendors.py]
         ↓
[Local Folder: notification_configs] → [Unchanged, original format]
         ↓
[sync_excel_files()]
         ↓
[Network Folder: G:\Test] → [Populated with vendor data, Power Automate format]
         ↓
[Power Automate Flows] → [Send notifications]
```

This architecture ensures:
- Local files can maintain any format needed for internal processing
- Network files are always in the correct format for Power Automate
- Vendor data is automatically synced from the database
- The network folder path is configurable via UI
