# Power Automate Single Flow Setup Guide

This guide shows you how to create **one single Power Automate flow** that handles all notifications by running every 10 minutes.

## Overview

The unified notification system works as follows:

```
Master Excel Rules → Python Logic → sent_noti_now.xlsx → Power Automate → Teams Notifications
     (Config)         (Every 10min)      (Network Folder)     (Single Flow)    (All Types)
```

## Files Created

1. **`master_notification_rules.xlsx`** - Master configuration with all 9 notification types
2. **`unified_notification_processor.py`** - Logic layer that processes rules and creates output
3. **`power_automate_scheduler.py`** - 10-minute scheduler for Power Automate
4. **`network_folder_simplified/sent_noti_now.xlsx`** - Output file Power Automate reads

## Power Automate Flow Setup

### Step 1: Create New Flow

1. Go to Power Automate (https://make.powerautomate.com)
2. Click **"+ Create"**
3. Choose **"Scheduled cloud flow"**
4. Name: `"Unified Notification Handler"`
5. Set to run **every 10 minutes**

### Step 2: Add Python Script Execution

Add an action to run the Python script:

```
Action: Execute a script (Power Automate for desktop)
Script: python "G:\Projects\Hackathon\MediaTek\vendor-timesheet-tool\power_automate_scheduler.py" --mode single
```

Or use **HTTP Request** to call a web endpoint (see API section below).

### Step 3: Read Excel File

Add **Excel Online** action:
```
Action: List rows present in a table
File: network_folder_simplified/sent_noti_now.xlsx
Table: NotificationsNow
```

### Step 4: Loop Through Notifications

Add **Apply to each** control:
```
Input: value (from Excel step)
```

### Step 5: Send Teams Notifications

Inside the loop, add **Teams** action:
```
Action: Post message in a chat or channel
Recipient: @{items('Apply_to_each')?['ContactEmail']}
Message: @{items('Apply_to_each')?['Message']}
Subject: @{items('Apply_to_each')?['NotificationType']} - Priority: @{items('Apply_to_each')?['Priority']}
```

### Step 6: Add Error Handling

Add **Scope** around all actions with error handling:
```
Configure run after: is successful, has failed, is skipped, has timed out
```

## Excel File Format

The `sent_noti_now.xlsx` file always has exactly these columns:

| Column | Description | Example |
|--------|-------------|---------|
| EmployeeID | Unique identifier | V001, M001, ADMIN_001 |
| ContactEmail | Email address | vendor1@company.com |
| Message | Notification text | Please submit your daily attendance status - John Doe |
| NotificationType | Type of notification | Daily Status Reminders |
| Priority | Priority level | Medium, High, Critical |

## API Endpoint (Optional)

If you prefer to use HTTP requests instead of running Python directly:

### 1. Start the API Server

```bash
python -c "from power_automate_scheduler import scheduler; print('API Ready')"
```

### 2. Power Automate HTTP Action

```
Action: HTTP
Method: POST
URL: http://localhost:5000/api/notifications/process
Headers: Content-Type: application/json
Body: {"force": false}
```

## Testing the System

### Test 1: Run Scheduler Manually

```bash
# Test single execution
python power_automate_scheduler.py --mode single --force

# Check status
python power_automate_scheduler.py --mode status

# Test continuous mode (for development)
python power_automate_scheduler.py --mode continuous --duration 30
```

### Test 2: Check Output Files

1. **Master rules**: `master_notification_rules.xlsx` should exist with 9 notification types
2. **Output file**: `network_folder_simplified/sent_noti_now.xlsx` should be created/updated
3. **Status file**: `network_folder_simplified/scheduler_status.json` tracks execution

### Test 3: Verify Excel Content

Open `sent_noti_now.xlsx` and verify:
- Headers: EmployeeID, ContactEmail, Message, NotificationType, Priority
- Data: Only notifications that are due RIGHT NOW
- Table formatting: Excel table named "NotificationsNow"

## Customization

### Modify Notification Rules

Edit `master_notification_rules.xlsx`:
1. Change `Active` to YES/NO to enable/disable notification types
2. Modify `Time_Intervals` to change when notifications are sent
3. Update `Message_Template` to customize messages
4. Change `Priority` levels as needed

### Add New Notification Types

1. Add row to `master_notification_rules.xlsx`
2. Add processing logic in `unified_notification_processor.py`
3. Restart the scheduler

### Change Timing

- **Power Automate Flow**: Change from 10 minutes to desired interval
- **Time Windows**: Modify 10-minute window in `check_time_condition()`
- **Scheduling Logic**: Update `should_run_now()` in scheduler

## Production Deployment

### Option 1: Power Automate Only

Use Power Automate's **Run a script** action to execute:
```
python power_automate_scheduler.py --mode single
```

### Option 2: Windows Task Scheduler + Power Automate

1. **Task Scheduler**: Run `power_automate_scheduler.py` every 10 minutes
2. **Power Automate**: Read `sent_noti_now.xlsx` every 10 minutes
3. **Benefit**: More reliable, separate concerns

### Option 3: Web API + Power Automate

1. **API Server**: Host the processing as a web service
2. **Power Automate**: Call HTTP endpoint every 10 minutes
3. **Benefit**: Better monitoring, logging, scalability

## Troubleshooting

### Common Issues

1. **No notifications generated**:
   - Check if vendors are actually pending in database
   - Verify time conditions in master rules
   - Check logs in `power_automate_scheduler.log`

2. **Excel file not updating**:
   - Check file permissions in network folder
   - Verify master rules file exists
   - Check database connectivity

3. **Power Automate flow failing**:
   - Verify Excel file path is accessible
   - Check table name "NotificationsNow" exists
   - Validate column names match exactly

4. **Timing issues**:
   - Verify system time is correct
   - Check time zone settings
   - Review 10-minute window logic

### Debug Commands

```bash
# Check current status
python power_automate_scheduler.py --mode status

# Force run to see output
python power_automate_scheduler.py --mode single --force

# Test notification processor directly
python unified_notification_processor.py

# Check master rules loading
python -c "from unified_notification_processor import unified_processor; print(unified_processor.load_master_rules())"
```

## Support

For issues:
1. Check `power_automate_scheduler.log`
2. Review `network_folder_simplified/notification_context.json`
3. Verify database connectivity
4. Test individual components separately

---

## Summary

This unified system provides:

✅ **Single Power Automate Flow** - No need for multiple flows  
✅ **Master Configuration** - All rules in one Excel file  
✅ **10-minute Updates** - Fresh notifications every cycle  
✅ **Standard Format** - Consistent output for Power Automate  
✅ **Error Handling** - Robust production-ready system  
✅ **Easy Customization** - Modify Excel file, no code changes

The system automatically handles all 9 notification types and only outputs notifications that are due RIGHT NOW, making Power Automate's job simple and efficient.
