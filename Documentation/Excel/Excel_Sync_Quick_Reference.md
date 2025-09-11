# 🔄 Excel Sync - Quick Reference Card

## 🚀 Quick Start (5 Minutes)

1. **Access Admin Panel**
   ```
   http://localhost:5000 → Login as Admin → Admin Dashboard → "Excel Sync Admin"
   ```

2. **Configure Network Path**
   ```
   Enter: \\server\shared\notification_configs
   Click: "💾 Save Path"
   ```

3. **Start Sync Service**
   ```
   Click: "▶️ Start Service"
   Status: Should show "🟢 Running"
   ```

4. **Verify Sync**
   ```
   Click: "🔄 Force Sync Now"
   Check: Files Synced count (should be 10-13)
   ```

## 📊 Dashboard Overview

### Status Indicators
| Icon | Status | Meaning |
|------|---------|---------|
| 🟢 | Running | Auto-syncing every 10 minutes |
| 🟡 | Paused | Service running but sync disabled |
| 🔴 | Stopped | Service not running |
| ❌ | Error | Sync failed - check errors |

### Control Buttons
| Button | Action | Use When |
|--------|--------|----------|
| ▶️ Start Service | Begin auto-sync | First setup or after stop |
| ⏹️ Stop Service | Halt all sync operations | Maintenance or troubleshooting |
| ⏸️ Pause | Temporarily disable sync | Keep service but stop copying |
| ▶️ Resume | Re-enable sync | After pause |
| 🔄 Force Sync Now | Immediate sync all files | Test or urgent update |
| 🔄 Refresh Status | Update dashboard display | Check latest status |

## 📁 Files Synced

| File | Purpose | Power Automate Use |
|------|---------|-------------------|
| `01_daily_status_reminders.xlsx` | Vendor daily reminders | 3-hour interval notifications |
| `02_manager_summary_notifications.xlsx` | Manager team summaries | 12 PM & 2 PM daily reports |
| `03_manager_all_complete_notifications.xlsx` | Team completion alerts | When all team members submit |
| `04_mismatch_notifications.xlsx` | Attendance mismatches | Swipe vs status discrepancies |
| `05_manager_feedback_notifications.xlsx` | Approval/rejection notices | Manager decision notifications |
| `06_monthly_report_notifications.xlsx` | Monthly reports | End of month summaries |
| `07_admin_system_alerts.xlsx` | System notifications | Critical system alerts |
| `08_holiday_reminder_notifications.xlsx` | Holiday announcements | Advance holiday notifications |
| `09_late_submission_alerts.xlsx` | Late submission warnings | Overdue submission alerts |
| `10_billing_correction_notifications.xlsx` | Financial corrections | Billing adjustment notices |
| `PA_backup_*.xlsx` | Power Automate backups | Redundancy files |

## 🔧 API Quick Commands

### Check Status
```bash
curl http://localhost:5000/api/excel-sync/status
```

### Start Service
```bash
curl -X POST http://localhost:5000/api/excel-sync/control/start
```

### Force Sync
```bash
curl -X POST http://localhost:5000/api/excel-sync/force
```

### Configure Path
```bash
curl -X POST http://localhost:5000/api/excel-sync/config \
  -H "Content-Type: application/json" \
  -d '{"network_folder": "\\\\server\\path\\notification_configs"}'
```

## 🛠️ Troubleshooting

### Common Issues & Quick Fixes

#### ❌ "Network folder not configured"
**Fix:** Set network path in admin interface

#### ❌ "Permission denied"
**Fix:** 
```
1. Check network path exists
2. Verify Windows authentication 
3. Test folder access manually
4. Ensure write permissions
```

#### ❌ "Files not syncing"
**Fix:**
```
1. Check network connectivity
2. Verify local files exist in notification_configs/
3. Review error log in admin interface
4. Try force sync
```

#### ❌ "Partial sync (some files missing)"
**Fix:**
```
1. Check individual file locks
2. Verify all Excel files are closed
3. Check antivirus interference
4. Restart sync service
```

### Log Monitoring
Check console output for:
```
[EXCEL SYNC 2025-09-11 02:48:26] ✅ Copied: filename.xlsx
[EXCEL SYNC 2025-09-11 02:48:26] 📊 Sync completed: X/Y files
```

## 📋 Network Path Examples

### Windows UNC Paths
```
\\server\shared\notifications
\\192.168.1.100\attendo\configs
\\domain-server\projects\MediaTek\notifications
```

### Mapped Drive Paths
```
Z:\notifications\configs
P:\shared\attendo\notifications
X:\project\notification_configs
```

### SharePoint/OneDrive Paths
```
\\company.sharepoint.com\sites\attendo\notifications
\\tenant-my.sharepoint.com\personal\user\notifications
```

## ⚙️ Configuration Settings

### Default Settings
```
Local Folder: notification_configs
Sync Interval: 10 minutes
Auto-start: Yes (if network path configured)
Include Backups: Yes
Max Retry: 3 attempts
```

### Customizable Options
- Network folder path (required)
- Sync frequency (via code modification)
- Error notification thresholds
- File inclusion patterns

## 🔍 Monitoring Checklist

### Daily Checks
- [ ] Service status is "Running"
- [ ] Files synced count matches expected (10-13)
- [ ] Error count is 0
- [ ] Last sync time is recent (<10 minutes)

### Weekly Checks
- [ ] Network path still accessible
- [ ] Disk space on network drive
- [ ] Review error logs
- [ ] Test manual sync

### Monthly Checks
- [ ] Review sync performance metrics
- [ ] Check backup file accumulation
- [ ] Validate Power Automate integration
- [ ] Update documentation if needed

## 🎯 Best Practices

### ✅ Do This
- Use UNC paths for network shares
- Test network connectivity before setup
- Monitor sync status regularly  
- Keep Excel files closed during sync
- Use descriptive network folder names

### ❌ Avoid This  
- Don't use local paths for network folder
- Don't modify files during sync
- Don't ignore error messages
- Don't disable antivirus completely
- Don't use spaces in folder names (if possible)

## 📞 Quick Help

### Getting Support
1. Check admin interface error log
2. Review console output logs
3. Test network path manually
4. Try force sync to isolate issues
5. Check Windows Event Viewer for system errors

### Emergency Recovery
```bash
# Stop and restart sync service
1. Click "⏹️ Stop Service"  
2. Wait 10 seconds
3. Click "▶️ Start Service"
4. Click "🔄 Force Sync Now"
5. Verify files synced count
```

---
**💡 Pro Tip:** Bookmark the admin interface at `http://localhost:5000/admin/excel-sync` for quick access!
