# Unified Notification System Guide

## Overview
The unified notification system reads from 9 Excel files in the network drive, creates a queue of notifications to be sent, and manages them through Power Automate integration.

## System Architecture

```
[9 Excel Files in Network Drive (G:\Test)]
                ↓
[unified_notification_processor.py]
                ↓
[sent_noti_now.xlsx - Notification Queue]
                ↓
[Power Automate reads & sends notifications]
                ↓
[Marks NTStatusSent = True]
                ↓
[Processor removes sent notifications]
```

## Key Components

### 1. Input Files (Network Drive)
- `01_daily_status_reminders.xlsx`
- `02_manager_summary_notifications.xlsx`
- `03_manager_all_complete_notifications.xlsx`
- `04_mismatch_notifications.xlsx`
- `05_manager_feedback_notifications.xlsx`
- `06_monthly_report_notifications.xlsx`
- `07_admin_system_alerts.xlsx`
- `08_holiday_reminder_notifications.xlsx`
- `09_late_submission_alerts.xlsx`

Each file contains:
- `EmployeeID`: Vendor identifier (e.g., EMP001)
- `ContactEmail`: Email address for notifications
- `Message`: Notification content
- `NotificationType`: Type of notification
- `Priority`: High/Medium/Low

### 2. Output Queue File
**Location**: `network_folder_simplified/sent_noti_now.xlsx`

**Columns**:
- `EmployeeID`: Employee/Vendor ID
- `ContactEmail`: Recipient email
- `Message`: Notification message
- `NotificationType`: Type of notification
- `Priority`: Urgency level
- `NTStatusSent`: Boolean flag (False initially, Power Automate sets to True when sent)

### 3. Notification Timing Rules

| Notification Type | Interval | Max Daily | Description |
|------------------|----------|-----------|-------------|
| Daily Reminder | 3 hours | 3 | Sent maximum 3 times per day |
| Manager Summary | 24 hours | 1 | Once per day |
| Mismatch Alert | 1 hour | 6 | Urgent alerts |
| Late Submission | 2 hours | 4 | Escalating reminders |
| Holiday Reminder | 48 hours | 1 | Advance notice |
| System Alert | 30 minutes | 10 | Critical system notifications |

## Scripts

### unified_notification_processor.py
Main processor that:
- Reads all 9 Excel files from network drive
- Applies timing rules (e.g., daily reminders every 3 hours, max 3 per day)
- Creates notification queue in `sent_noti_now.xlsx`
- Tracks notification history in `notification_tracking.json`
- Removes sent notifications (where `NTStatusSent = True`)

### power_automate_scheduler.py
Scheduler that:
- Runs notification processing every 10 minutes
- Cleans up sent notifications every 5 minutes
- Provides status reports every 30 minutes
- Logs all activities to `scheduler.log`

## Usage

### Run Once (Testing)
```bash
python power_automate_scheduler.py --once
```

### Start Continuous Scheduler
```bash
python power_automate_scheduler.py
```

### Custom Paths
```bash
python power_automate_scheduler.py --network-folder "G:/Test" --output-folder "network_folder_simplified"
```

## Power Automate Integration

### Flow Configuration
1. **Trigger**: Recurrence - Every 10 minutes
2. **Action 1**: List rows present in table
   - File: `network_folder_simplified/sent_noti_now.xlsx`
   - Table: `NotificationQueue`
   - Filter: `NTStatusSent eq false`

3. **Action 2**: For each row
   - Send Teams notification or Email
   - To: `@{items('Apply_to_each')?['ContactEmail']}`
   - Message: `@{items('Apply_to_each')?['Message']}`
   - Priority: `@{items('Apply_to_each')?['Priority']}`

4. **Action 3**: Update row
   - Set `NTStatusSent` = `true`

### Power Automate Example
```json
{
  "trigger": {
    "type": "Recurrence",
    "interval": 10,
    "frequency": "minute"
  },
  "actions": [
    {
      "type": "Excel.ListRows",
      "inputs": {
        "file": "network_folder_simplified/sent_noti_now.xlsx",
        "table": "NotificationQueue",
        "filter": "NTStatusSent eq false"
      }
    },
    {
      "type": "Apply_to_each",
      "foreach": "@body('List_rows')?['value']",
      "actions": [
        {
          "type": "Teams.PostMessage",
          "inputs": {
            "recipient": "@items('Apply_to_each')?['ContactEmail']",
            "message": "@items('Apply_to_each')?['Message']",
            "importance": "@items('Apply_to_each')?['Priority']"
          }
        },
        {
          "type": "Excel.UpdateRow",
          "inputs": {
            "row": "@items('Apply_to_each')",
            "NTStatusSent": true
          }
        }
      ]
    }
  ]
}
```

## Queue Management

### How the Queue Works
1. **Creation**: Processor reads all 9 files and creates notifications based on timing rules
2. **Queue File**: Notifications are added to `sent_noti_now.xlsx` with `NTStatusSent = False`
3. **Power Automate**: Reads unsent notifications, sends them, marks `NTStatusSent = True`
4. **Cleanup**: Processor removes sent notifications from queue on next run

### Tracking System
- **File**: `notification_tracking.json`
- **Purpose**: Tracks when each notification was last sent
- **Prevents**: Duplicate notifications within time intervals
- **Ensures**: Daily limits are respected

## Monitoring

### Log Files
- **Scheduler Log**: `network_folder_simplified/scheduler.log`
- **Tracking Data**: `network_folder_simplified/notification_tracking.json`

### Status Check
```python
# Check queue status
import pandas as pd
df = pd.read_excel('network_folder_simplified/sent_noti_now.xlsx')
print(f"Total in queue: {len(df)}")
print(f"Unsent: {len(df[df['NTStatusSent'] == False])}")
print(f"Sent: {len(df[df['NTStatusSent'] == True])}")
```

## Troubleshooting

### No Notifications in Queue
1. Check if Excel files exist in network drive
2. Verify files have correct column structure
3. Check `notification_tracking.json` for timing restrictions

### Notifications Not Being Sent
1. Verify Power Automate flow is running
2. Check `NTStatusSent` column is being updated
3. Review Power Automate run history for errors

### Duplicate Notifications
1. Check tracking file is being updated
2. Verify cleanup process is running
3. Ensure Power Automate is marking notifications as sent

### Queue Not Clearing
1. Verify `NTStatusSent` is being set to `True`
2. Check cleanup job is running (every 5 minutes)
3. Review scheduler log for errors

## Best Practices

1. **Regular Monitoring**: Check queue size regularly
2. **Log Review**: Review scheduler.log daily
3. **Backup**: Keep backups of tracking file
4. **Testing**: Test with `--once` flag before running continuous
5. **Power Automate**: Ensure flow handles errors gracefully

## System Requirements

- Python 3.7+
- Required packages: pandas, openpyxl, schedule
- Network access to Excel files
- Write permissions for output folder
- Power Automate with Excel Online connector

## Configuration

### Timing Customization
Edit `unified_notification_processor.py`:
```python
self.notification_intervals = {
    'Daily Reminder': 3,  # Hours between notifications
    'Manager Summary': 24,
    # ... adjust as needed
}

self.max_daily_notifications = {
    'Daily Reminder': 3,  # Max per day
    'Manager Summary': 1,
    # ... adjust as needed
}
```

### Scheduler Interval
Edit `power_automate_scheduler.py`:
```python
schedule.every(10).minutes.do(self.process_notifications_job)  # Main process
schedule.every(5).minutes.do(self.cleanup_sent_notifications)  # Cleanup
```

This unified system ensures all notifications are properly queued, tracked, sent, and cleaned up automatically!
