# Power Automate Integration Guide

## Overview

This guide explains how to integrate ATTENDO with Microsoft Power Automate for accurate daily attendance notifications. The system ensures Power Automate always has fresh, correct data by implementing **Daily Excel Sheet Updates**.

## 🚨 Problem Solved

**Before**: Excel sheets contained stale vendor data from previous days, causing incorrect notifications.

**After**: Daily midnight refresh ensures Excel sheets only contain TODAY'S pending vendors, guaranteeing Power Automate accuracy.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ATTENDO       │    │  Excel Sheets    │    │ Power Automate  │
│   Database      │◄──►│  (Daily Reset)   │◄──►│  Workflows      │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
    Real-time              Daily Cleanup            Accurate
    Updates               + Fresh Data            Notifications
```

## 📅 Daily Process Flow

### Midnight (00:05 AM)
1. **Daily Excel Reset** automatically runs
2. Clears yesterday's notification data from Excel sheets
3. Queries database for TODAY'S pending vendors
4. Updates Excel sheets with fresh, accurate data
5. Triggers Power Automate refresh webhook

### Throughout the Day
1. **Real-time Updates**: When vendors submit attendance
   - Excel sheets updated immediately  
   - Vendor removed from reminder lists
   - Power Automate notified of change

### Result: Power Automate Always Has Current Data

## 🔧 API Endpoints

### Base URL: `http://localhost:5000/api/power-automate`

### 1. Daily Reset Trigger
```http
POST /daily-reset
Content-Type: application/json

{
    "force": false
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Daily reset completed",
    "timestamp": "2025-01-09T00:05:23",
    "date": "2025-01-09"
}
```

### 2. Get Pending Vendors
```http
GET /pending-vendors
```

**Response:**
```json
{
    "status": "success",
    "date": "2025-01-09",
    "pending_count": 3,
    "vendors": [
        {
            "vendor_id": "V001",
            "full_name": "John Doe",
            "email": "john@company.com",
            "department": "Engineering",
            "manager_id": "M001",
            "status": "PENDING_SUBMISSION"
        }
    ]
}
```

### 3. Manager Summary
```http
GET /manager-summary?manager_id=M001
```

**Response:**
```json
{
    "status": "success",
    "date": "2025-01-09",
    "summaries": [
        {
            "manager_id": "M001",
            "manager_name": "Jane Smith",
            "team_size": 5,
            "submitted_count": 2,
            "pending_submissions": 3,
            "completion_rate": 40.0,
            "alert_level": "HIGH"
        }
    ]
}
```

### 4. Excel Status Check
```http
GET /excel-status
```

**Response:**
```json
{
    "status": "success",
    "files": {
        "daily_reminders": {
            "filename": "01_daily_status_reminders.xlsx",
            "exists": true,
            "last_modified": "2025-01-09T00:05:30",
            "readable": true,
            "writable": true
        }
    },
    "daily_context": {
        "last_reset_date": "2025-01-09",
        "reset_status": "SUCCESS"
    }
}
```

### 5. Health Check
```http
GET /health-check
```

**Response:**
```json
{
    "status": "healthy",
    "database": "ok",
    "excel_files": "ok",
    "daily_reset": "current",
    "date": "2025-01-09"
}
```

## 🔗 Power Automate Setup

### Step 1: Configure Webhook URLs

```http
POST /webhook/configure
Content-Type: application/json

{
    "daily_refresh": "https://prod-123.westus.logic.azure.com:443/workflows/abc123/triggers/manual/paths/invoke",
    "vendor_status_change": "https://prod-456.westus.logic.azure.com:443/workflows/def456/triggers/manual/paths/invoke",
    "emergency_alert": "https://prod-789.westus.logic.azure.com:443/workflows/ghi789/triggers/manual/paths/invoke"
}
```

### Step 2: Create Power Automate Flows

#### A. Daily Reminder Flow
**Trigger:** HTTP Request (scheduled daily at various hours)
**Actions:**
1. Call `GET /pending-vendors`
2. For each pending vendor:
   - Send Teams notification
   - Send email reminder
   - Log notification sent

#### B. Manager Summary Flow  
**Trigger:** HTTP Request (scheduled at 12 PM, 2 PM)
**Actions:**
1. Call `GET /manager-summary`
2. For each manager with pending submissions:
   - Send Teams message to manager
   - Include team completion statistics

#### C. Daily Reset Flow
**Trigger:** Recurrence (daily at 12:05 AM)
**Actions:**
1. Call `POST /daily-reset`
2. If successful: Log completion
3. If failed: Send emergency alert

### Step 3: Excel File Access

Power Automate needs access to these Excel files:
- `notification_configs/01_daily_status_reminders.xlsx`
- `notification_configs/02_manager_summary_notifications.xlsx`
- `notification_configs/09_late_submission_alerts.xlsx`

**Storage Options:**
- SharePoint Online (recommended)
- OneDrive for Business
- Local file share (if accessible)

## 📊 Excel Sheet Structure

### Daily Reminders Sheet
| Column | Purpose |
|--------|---------|
| `Vendor_ID` | Unique vendor identifier |
| `Daily_Status_Date` | Today's date (updated daily) |
| `Reminder_Status` | PENDING/COMPLETED |
| `Submission_Status` | NOT_SUBMITTED/SUBMITTED |
| `Send_Notification` | YES/NO (controls Power Automate) |
| `Contact_Email` | Vendor email address |
| `Last_Updated` | Timestamp of last update |

### Key Columns for Power Automate:
- Filter by: `Send_Notification = "YES"`
- Check: `Daily_Status_Date = TODAY()`
- Use: `Reminder_Status = "PENDING"`

## ⚡ Real-Time Updates

When a vendor submits attendance:
1. Database updated immediately
2. Excel sheet updated in real-time
3. Vendor's `Send_Notification` set to `"NO"`
4. Power Automate webhook triggered (optional)

## 🔍 Monitoring & Troubleshooting

### Health Check Endpoint
Use `/health-check` to monitor system status:
- Database connectivity
- Excel file accessibility  
- Daily reset currency

### Log Files
- `daily_excel_updater.log` - Daily reset operations
- `realtime_sync.log` - Real-time updates
- `sync_monitoring.log` - System health

### Common Issues

**Issue**: Power Automate sending duplicate notifications
**Solution**: Check `Daily_Status_Date` column matches today's date

**Issue**: Vendors not removed after submission
**Solution**: Verify real-time update integration in `/vendor/submit-status`

**Issue**: Daily reset not running
**Solution**: Check scheduler logs and `/health-check` endpoint

## 🚀 Testing

### Manual Test Daily Reset
```bash
curl -X POST http://localhost:5000/api/power-automate/daily-reset \
  -H "Content-Type: application/json" \
  -d '{"force": true}'
```

### Test Vendor Status Update
```bash
curl -X POST http://localhost:5000/api/power-automate/vendor-status-update \
  -H "Content-Type: application/json" \
  -d '{"vendor_id": "V001", "status": "SUBMITTED"}'
```

### Test Notifications
```bash
curl -X POST http://localhost:5000/api/power-automate/test-notification \
  -H "Content-Type: application/json" \
  -d '{"type": "daily_reset"}'
```

## 📅 Implementation Schedule

### Phase 1: Core System (Day 1)
- [x] Daily Excel updater module
- [x] Midnight reset scheduler
- [x] Real-time vendor updates
- [x] API endpoints

### Phase 2: Power Automate Integration (Day 2-3)
- [ ] Configure webhook URLs
- [ ] Create Power Automate flows
- [ ] Test end-to-end integration
- [ ] Set up monitoring

### Phase 3: Production Deployment (Day 4-5)
- [ ] Deploy to production environment
- [ ] Configure production webhooks
- [ ] Set up monitoring alerts
- [ ] Train admin users

## 🎯 Key Benefits

✅ **Accuracy**: Power Automate always has current day's data
✅ **Real-time**: Immediate updates when vendors submit
✅ **Reliability**: Automatic daily refresh prevents stale data
✅ **Monitoring**: Health checks and error alerts
✅ **Scalability**: API-based integration supports future expansion

## 📞 Support

For technical issues:
1. Check `/health-check` endpoint
2. Review log files in application directory
3. Validate Excel file permissions
4. Test API endpoints manually

---

**This integration ensures Power Automate notifications are always accurate and timely! 🎉**
