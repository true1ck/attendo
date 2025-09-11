# Unified Power Automate Notification System

## 🎯 Overview

This system implements your exact requirements: **One single Power Automate flow** that runs every 10 minutes and handles **all notifications** from an Excel-based schedule.

## 📁 Files Created

| File | Purpose |
|------|---------|
| `master_notification_rules.xlsx` | Master Excel with all 9 notification rules |
| `unified_notification_processor.py` | Logic layer that processes rules and generates output |
| `power_automate_scheduler.py` | 10-minute scheduler for Power Automate |
| `standardize_excel_format.py` | Ensures all Excel files have consistent format |
| `network_folder_simplified/sent_noti_now.xlsx` | **Output file Power Automate reads** |
| `POWER_AUTOMATE_FLOW_GUIDE.md` | Step-by-step Power Automate setup guide |

## 🔄 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    UNIFIED NOTIFICATION SYSTEM              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐                                    │
│  │ master_notification │  ─────┐                             │
│  │     _rules.xlsx     │       │                             │
│  │                     │       │                             │
│  │ • Daily Status      │       │                             │
│  │ • Manager Summary   │       ▼                             │
│  │ • All-Complete      │  ┌─────────────────┐                │
│  │ • Mismatch Alerts   │  │ Python Logic    │                │
│  │ • Manager Feedback  │  │ Layer           │                │
│  │ • Monthly Reports   │  │ (Every 10 min)  │                │
│  │ • System Alerts     │  │                 │                │
│  │ • Holiday Reminders │  │ • Read rules    │                │
│  │ • Late Submission   │  │ • Apply time    │                │
│  └─────────────────────┘  │ • Check DB      │                │
│                           │ • Generate      │                │
│                           └─────────────────┘                │
│                                     │                        │
│                                     ▼                        │
│                      ┌─────────────────────────┐             │
│                      │  sent_noti_now.xlsx    │             │
│                      │  (Network Folder)      │             │
│                      │                        │             │
│                      │ EmployeeID            │              │
│                      │ ContactEmail          │              │
│                      │ Message               │              │
│                      │ NotificationType      │              │
│                      │ Priority              │              │
│                      └─────────────────────────┘             │
│                                     │                        │
│                                     ▼                        │
│                      ┌─────────────────────────┐             │
│                      │   POWER AUTOMATE       │             │
│                      │   (Single Flow)        │             │
│                      │                        │             │
│                      │ • Runs every 10 min    │             │
│                      │ • Reads Excel file     │             │
│                      │ • Sends Teams messages │             │
│                      │ • Handles ALL types    │             │
│                      └─────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Setup Files (Already Done!)

All files are created and ready to use:

```bash
# Check master rules file exists
dir master_notification_rules.xlsx

# Test the logic layer
python unified_notification_processor.py

# Test the scheduler
python power_automate_scheduler.py --mode single --force
```

### 2. Power Automate Flow Setup

1. **Create new Scheduled Flow** in Power Automate
2. **Set to run every 10 minutes**
3. **Add action**: Run script or HTTP request
4. **Read Excel**: `network_folder_simplified/sent_noti_now.xlsx`
5. **Loop through rows**: Send Teams notifications

See `POWER_AUTOMATE_FLOW_GUIDE.md` for detailed steps.

### 3. Start the System

```bash
# Option 1: Manual testing
python power_automate_scheduler.py --mode single --force

# Option 2: Continuous testing (30 minutes)
python power_automate_scheduler.py --mode continuous --duration 30

# Option 3: Check status
python power_automate_scheduler.py --mode status
```

## 📊 Master Notification Rules

The `master_notification_rules.xlsx` contains all 9 notification types from your specification:

| # | Notification Type | Frequency | Primary Trigger Time | Recipients | Priority |
|---|-------------------|-----------|---------------------|------------|----------|
| 1 | Daily Status Reminders | Every 3 hours | 9 AM – 6 PM | Vendors | Medium |
| 2 | Manager Summary | 2x daily | 12 PM, 2 PM | Managers | Medium |
| 3 | All-Complete | Event-driven | When team complete | Managers | Low |
| 4 | Mismatch Alerts | Daily + Escalation | 6 PM daily | Vendors, Managers | High |
| 5 | Manager Feedback | Event-driven | Within 1 hour | Vendors | Medium |
| 6 | Monthly Reports | Monthly | 1st at 9 AM | Managers, Admins | Medium |
| 7 | System Alerts | Event-driven | Immediate | Admins | Critical |
| 8 | Holiday Reminders | Before holidays | 3 days, 1 day before | All Users | Low |
| 9 | Late Submission | After deadlines | 24h, 48h after | Managers, Admins | High |

## 📝 Standard Excel Format

**ALL** Excel files now have the same data format as requested:

| Column | Description | Example |
|--------|-------------|---------|
| **EmployeeID** | Unique identifier | V001, M001, ADMIN_001 |
| **ContactEmail** | Email address | vendor1@company.com |
| **Message** | Notification text | Please submit your daily attendance status - John Doe |
| **NotificationType** | Type of notification | Daily Status Reminders |
| **Priority** | Priority level | Medium, High, Critical |

## 🔧 Customization

### Modify Notification Rules

Edit `master_notification_rules.xlsx`:
- **Active**: YES/NO to enable/disable
- **Time_Intervals**: Change timing (09:00,12:00,15:00)
- **Message_Template**: Customize messages
- **Priority**: Low/Medium/High/Critical

### Change Timing

- **Power Automate**: Change flow from 10 minutes to desired interval
- **Script**: Modify time window in `check_time_condition()`

### Add New Notification Types

1. Add row to `master_notification_rules.xlsx`
2. Add processing logic in `unified_notification_processor.py`

## 🧪 Testing Commands

```bash
# 1. Test master rules loading
python -c "from unified_notification_processor import unified_processor; print(unified_processor.load_master_rules())"

# 2. Test notification processing
python unified_notification_processor.py

# 3. Test scheduler (force run)
python power_automate_scheduler.py --mode single --force

# 4. Check scheduler status
python power_automate_scheduler.py --mode status

# 5. Standardize Excel format
python standardize_excel_format.py --action sample

# 6. Continuous testing mode
python power_automate_scheduler.py --mode continuous --duration 30
```

## 📂 File Structure

```
vendor-timesheet-tool/
├── master_notification_rules.xlsx          # Master configuration
├── unified_notification_processor.py       # Logic layer
├── power_automate_scheduler.py             # 10-minute scheduler
├── standardize_excel_format.py            # Format standardizer
├── POWER_AUTOMATE_FLOW_GUIDE.md           # Setup guide
└── network_folder_simplified/
    ├── sent_noti_now.xlsx                 # ⭐ Power Automate reads this
    ├── notification_context.json          # Processing context
    ├── scheduler_status.json              # Scheduler status
    └── sample_standard_format.xlsx        # Sample format
```

## ⚡ Power Automate Integration Options

### Option 1: Direct Script Execution
```
Action: Run script
Script: python "G:\...\power_automate_scheduler.py" --mode single
```

### Option 2: HTTP Request (Recommended)
```
Method: POST
URL: http://localhost:5000/api/notifications
Body: {"force": false}
```

### Option 3: File Monitoring
```
Trigger: When file is modified
File: network_folder_simplified/sent_noti_now.xlsx
```

## 🚨 Error Handling

### Logs and Monitoring
- **Processing logs**: `power_automate_scheduler.log`
- **Status tracking**: `network_folder_simplified/scheduler_status.json`
- **Context data**: `network_folder_simplified/notification_context.json`

### Common Issues

1. **No notifications generated**:
   - Check database has pending vendors
   - Verify time conditions in master rules
   - Check current time matches intervals

2. **Excel file not updating**:
   - Check file permissions
   - Verify master rules file exists
   - Check database connectivity

3. **Power Automate flow failing**:
   - Verify Excel file path accessible
   - Check table name "NotificationsNow"
   - Validate column names exact match

## 🎯 Key Features

✅ **Single Power Automate Flow** - No need for multiple flows  
✅ **Master Excel Configuration** - All rules in one file  
✅ **10-minute Updates** - Fresh notifications every cycle  
✅ **Standard Format** - Consistent EmployeeID, ContactEmail, Message, NotificationType, Priority  
✅ **Time Condition Logic** - Only notifications due RIGHT NOW  
✅ **Error Handling** - Robust production-ready system  
✅ **Easy Customization** - Modify Excel, no code changes  
✅ **File Locking** - Prevents conflicts  
✅ **Comprehensive Logging** - Full audit trail  

## 🔄 Production Deployment

### Recommended Setup

1. **Windows Task Scheduler**: Run `power_automate_scheduler.py --mode single` every 10 minutes
2. **Power Automate Flow**: Read `sent_noti_now.xlsx` every 10 minutes and send Teams notifications
3. **Monitoring**: Check logs and status files regularly

### Alternative Setup

1. **Power Automate Only**: Use "Run script" action to execute Python directly
2. **Web API**: Host as web service with HTTP endpoints
3. **Azure Functions**: Deploy as serverless functions

## 📞 Support

For issues:
1. Check `power_automate_scheduler.log`
2. Review status files in `network_folder_simplified/`
3. Test components individually
4. Verify database connectivity and permissions

---

## 🎉 Summary

This unified system provides exactly what you requested:

🎯 **One Master Excel File** with all notification rules  
🎯 **Logic Layer** that processes rules every 10 minutes  
🎯 **Single Excel Output** (`sent_noti_now.xlsx`) with standard format  
🎯 **Single Power Automate Flow** that reads the output and sends notifications  

**The system is complete and ready to use!** 🚀
