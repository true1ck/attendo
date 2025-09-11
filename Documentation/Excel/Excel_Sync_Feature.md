# Excel Sync Feature Documentation

## Overview

The Excel Sync feature provides automated synchronization of notification configuration files from the local system to a network drive, enabling seamless integration with Microsoft Power Automate workflows. This feature ensures that Power Automate has access to up-to-date Excel files containing notification triggers and configurations.

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Setup & Configuration](#setup--configuration)
4. [Admin Interface](#admin-interface)
5. [API Endpoints](#api-endpoints)
6. [Power Automate Integration](#power-automate-integration)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
8. [Technical Details](#technical-details)

## Features

### ✅ Core Functionality
- **Automated Sync**: Syncs Excel files every 10 minutes (configurable)
- **Real-time Control**: Start, stop, pause, resume sync operations
- **Force Sync**: Manual immediate synchronization
- **File Preservation**: Maintains file timestamps and structure using `shutil.copy2()`
- **Backup Integration**: Includes Power Automate backup files in sync

### 📊 Monitoring & Management
- **Web-based Admin Interface**: Complete control panel integrated into admin dashboard
- **Real-time Status**: Live sync status, file counts, and error tracking
- **Auto-refresh**: Dashboard updates every 30 seconds
- **Error Logging**: Detailed error tracking and display
- **Configuration Persistence**: Settings saved in system database

### 🔒 Enterprise Ready
- **Network Drive Support**: Compatible with UNC paths and mapped drives
- **Path Validation**: Automatic validation of network folder accessibility
- **Service Integration**: Fully integrated into main application lifecycle
- **Thread-safe Operations**: Background sync without blocking main application

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ATTENDO Main Application                         │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │   Admin Web UI    │    │   Excel Sync    │    │   Config DB     │ │
│  │                   │◄──►│    Service      │◄──►│                 │ │
│  │  - Control Panel  │    │                 │    │ - Network Path  │ │
│  │  - Status Display │    │ - Background    │    │ - Settings      │ │
│  │  - Configuration  │    │   Thread        │    │ - Persistence   │ │
│  └───────────────────┘    │ - File Monitor  │    └─────────────────┘ │
│                           │ - Error Track   │                        │
│                           └─────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────────┐
                        │    File Synchronization │
                        └─────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────┐
│ Local Directory │    │   Network Drive     │    │ Power Automate  │
│                 │    │                     │    │                 │
│ notification_   │───►│ \\server\path\to\   │───►│ - Reads Excel   │
│ configs\        │    │ notification_configs│    │ - Triggers Flow │
│                 │    │                     │    │ - Sends Alerts  │
│ - 01_daily...   │    │ - 01_daily...       │    │                 │
│ - 02_manager... │    │ - 02_manager...     │    │                 │
│ - 03_complete...│    │ - 03_complete...    │    │                 │
│ - ... (10 files)│    │ - ... (10+ files)   │    │                 │
└─────────────────┘    └─────────────────────┘    └─────────────────┘
```

## Setup & Configuration

### Prerequisites
- ATTENDO application running
- Admin access to the system
- Network drive or UNC path accessible from the server
- Excel notification files generated in `notification_configs` folder

### Initial Setup

1. **Start ATTENDO Application**
   ```bash
   python app.py
   ```

2. **Login as Administrator**
   - Username: `Admin`
   - Password: `admin123`

3. **Navigate to Excel Sync**
   - Go to Admin Dashboard
   - Click "Excel Sync Admin" button

4. **Configure Network Path**
   ```
   Examples:
   - UNC Path: \\server\shared\notification_configs
   - Mapped Drive: Z:\path\to\notification_configs
   - Network Share: \\192.168.1.100\attendo\notifications
   ```

5. **Save and Start Service**
   - Enter your network path
   - Click "Save Path"
   - Click "Start Service"

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| Local Folder | Source folder for Excel files | `notification_configs` |
| Network Folder | Destination network path | User configured |
| Sync Interval | Minutes between automatic syncs | 10 minutes |
| Auto-start | Start sync when app launches | Yes (if configured) |
| Include Backups | Sync backup files too | Yes |

## Admin Interface

### Dashboard Layout

The Excel Sync Admin interface (`/admin/excel-sync`) provides:

#### 1. Configuration Panel
```
┌─────────────────────────────────────────────────────────────────────┐
│                        ⚙️ Sync Configuration                        │
├─────────────────────────────────────────────────────────────────────┤
│ Local Folder:    notification_configs                              │
│ Network Folder:  \\server\shared\notification_configs              │
│                                                                     │
│ Set Network Folder Path: [___________________] [💾 Save Path]      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 2. Service Status
```
┌─────────────────────────────────────────────┐
│            🚦 Service Status                │
├─────────────────────────────────────────────┤
│ ● Running                                   │
│                                             │
│ Last Sync: 2025-09-11 02:48:26            │
│ Files Synced: 13                           │
│ Errors: 0                                   │
└─────────────────────────────────────────────┘
```

#### 3. Control Panel
```
┌─────────────────────────────────────────────────────────────────────┐
│                      🎛️ Sync Controls                               │
├─────────────────────────────────────────────────────────────────────┤
│ [▶️ Start Service] [⏹️ Stop Service]                                │
│ [⏸️ Pause] [▶️ Resume]                                               │
│ [🔄 Force Sync Now] [🔄 Refresh Status]                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Status Indicators

| Indicator | Status | Description |
|-----------|--------|-------------|
| 🟢 Running | Service actively syncing every 10 minutes |
| 🟡 Paused | Service running but sync paused |
| 🔴 Stopped | Service not running |
| ❌ Error | Sync failed - check error log |

## API Endpoints

### Control Endpoints

#### Start/Stop/Pause/Resume Service
```http
POST /api/excel-sync/control/<action>
```
**Actions:** `start`, `stop`, `pause`, `resume`

**Response:**
```json
{
    "message": "Excel sync service started"
}
```

#### Force Immediate Sync
```http
POST /api/excel-sync/force
```
**Response:**
```json
{
    "message": "Force sync completed"
}
```

#### Configure Network Folder
```http
POST /api/excel-sync/config
Content-Type: application/json

{
    "network_folder": "\\\\server\\shared\\notification_configs"
}
```

**Response:**
```json
{
    "message": "Network folder configured successfully"
}
```

### Status Endpoints

#### Get Sync Status
```http
GET /api/excel-sync/status
```

**Response:**
```json
{
    "running": true,
    "paused": false,
    "status": "Running",
    "last_sync": "2025-09-11 02:48:26",
    "files_synced": 13,
    "error_count": 0,
    "errors": [],
    "network_folder": "\\\\server\\shared\\notification_configs",
    "local_folder": "notification_configs"
}
```

## Power Automate Integration

### Excel Files Synced

The sync service handles all notification configuration files:

| File | Description | Power Automate Use |
|------|-------------|-------------------|
| `01_daily_status_reminders.xlsx` | Daily vendor reminders | Trigger reminder emails every 3 hours |
| `02_manager_summary_notifications.xlsx` | Manager team summaries | Send team status at 12 PM & 2 PM |
| `03_manager_all_complete_notifications.xlsx` | Team completion alerts | Notify when all team members submit |
| `04_mismatch_notifications.xlsx` | Attendance mismatches | Alert on swipe vs. status discrepancies |
| `05_manager_feedback_notifications.xlsx` | Approval/rejection notices | Notify vendors of manager decisions |
| `06_monthly_report_notifications.xlsx` | Monthly reports | Generate monthly summaries |
| `07_admin_system_alerts.xlsx` | System notifications | Critical system alerts |
| `08_holiday_reminder_notifications.xlsx` | Holiday announcements | Advance holiday notifications |
| `09_late_submission_alerts.xlsx` | Late submission warnings | Alert managers of overdue submissions |
| `10_billing_correction_notifications.xlsx` | Financial corrections | Billing adjustment notifications |

### Power Automate Flow Setup

1. **File Location**: Configure Power Automate to monitor the network folder
2. **Table Format**: All files maintain Excel table structure for easy reading
3. **Triggers**: Use "When an item is created or modified" for real-time updates
4. **Backup Files**: Include `PA_backup_*` files for redundancy

### Example Power Automate Flow

```yaml
Trigger: When a file is modified
  - Site: OneDrive/SharePoint
  - Folder: \\server\shared\notification_configs
  - File: 01_daily_status_reminders.xlsx

Action: List rows in table
  - Table: DailyStatusReminders
  - Filter: Send_Notification = "YES" AND Active = "YES"

Action: Apply to each vendor
  - Send email notification
  - Update reminder status
```

## Monitoring & Troubleshooting

### Log Messages

Excel sync operations are logged with timestamps:

```
[EXCEL SYNC 2025-09-11 02:48:26] 🚀 Excel sync service started
[EXCEL SYNC 2025-09-11 02:48:26] ✅ Copied: 01_daily_status_reminders.xlsx
[EXCEL SYNC 2025-09-11 02:48:26] ✅ Copied: 02_manager_summary_notifications.xlsx
[EXCEL SYNC 2025-09-11 02:48:26] 📊 Sync completed: 13/13 files
```

### Common Issues & Solutions

#### 1. Service Won't Start
**Issue:** "Network folder not configured. Please set it in Admin Settings."
**Solution:** Configure network folder path in admin interface

#### 2. Permission Denied
**Issue:** Cannot access network folder
**Solution:** 
- Verify network path is correct
- Check Windows credentials for network access
- Ensure write permissions on destination folder

#### 3. Files Not Syncing
**Issue:** Sync runs but files don't appear
**Solution:**
- Check network connectivity
- Verify folder exists and is accessible
- Review error log in admin interface

#### 4. Partial File Sync
**Issue:** Only some files are copied
**Solution:**
- Check individual file permissions
- Verify local files exist in `notification_configs`
- Look for file lock conflicts

### Performance Monitoring

Monitor these metrics:
- **Sync Frequency**: Every 10 minutes (configurable)
- **File Count**: Should match local Excel files count
- **Error Rate**: Should be 0 under normal operation
- **Sync Duration**: Typically completes within seconds

## Technical Details

### Implementation Architecture

#### Core Components

1. **Sync Service** (`app.py` lines 2915-3120)
   - Background thread for periodic sync
   - Thread-safe operations
   - Global state management

2. **Admin Interface** (`templates/admin_excel_sync.html`)
   - Web-based control panel
   - Real-time status updates
   - Configuration management

3. **API Layer** (Routes in `app.py`)
   - RESTful endpoints for control
   - JSON response format
   - Admin authentication required

#### Configuration Storage

Settings are persisted in the system configuration database:
```python
set_system_config('excel_network_folder', network_folder, 
                 'Excel sync network folder path', current_user.id)
```

#### File Operations

Uses `shutil.copy2()` for file copying:
- Preserves original timestamps
- Maintains file metadata
- Handles large files efficiently

#### Thread Management

```python
excel_sync_thread = threading.Thread(target=excel_sync_loop, daemon=True)
excel_sync_thread.start()
```
- Daemon thread ensures clean shutdown
- Non-blocking operation
- Graceful stop mechanism

### Security Considerations

1. **Admin Access Only**: All sync operations require admin authentication
2. **Path Validation**: Network paths are validated before use
3. **Error Handling**: Comprehensive error catching and logging
4. **Configuration Security**: Settings stored in encrypted database

### Performance Optimization

- **Change Detection**: Only syncs when files are modified
- **Batch Operations**: Processes all files in single operation
- **Memory Efficient**: Uses file system operations, not in-memory loading
- **Background Processing**: Non-blocking main application

## Integration Examples

### 1. Automated Setup Script
```python
from app import app, set_system_config

# Configure network folder programmatically
with app.app_context():
    set_system_config('excel_network_folder', 
                     '\\\\server\\notifications',
                     'Auto-configured path', 1)
```

### 2. API Integration
```python
import requests

# Start sync service
response = requests.post('http://localhost:5000/api/excel-sync/control/start')
print(response.json())  # {"message": "Excel sync service started"}

# Check status
status = requests.get('http://localhost:5000/api/excel-sync/status')
print(f"Files synced: {status.json()['files_synced']}")
```

### 3. Monitoring Script
```python
def monitor_sync():
    status = get_sync_status()
    if status['error_count'] > 0:
        send_alert(f"Excel sync errors: {status['errors']}")
    if not status['running']:
        restart_sync_service()
```

## Best Practices

### 1. Network Configuration
- Use UNC paths for network shares: `\\server\share\path`
- Ensure consistent network connectivity
- Test path accessibility before configuration
- Use service accounts for automated access

### 2. Monitoring Setup
- Check sync status regularly
- Monitor error logs
- Set up alerts for sync failures
- Validate file counts periodically

### 3. Maintenance
- Review network folder permissions monthly
- Clean up old backup files if needed
- Monitor disk space on network drive
- Test sync recovery procedures

### 4. Power Automate Integration
- Keep Excel files in table format
- Use consistent column naming
- Test Power Automate flows after sync changes
- Monitor Power Automate execution logs

## Conclusion

The Excel Sync feature provides a robust, enterprise-ready solution for automatically synchronizing notification configuration files with network drives, enabling seamless Power Automate integration. With its comprehensive admin interface, real-time monitoring, and reliable file operations, it ensures that your notification workflows remain operational and up-to-date.

For additional support or advanced configuration options, refer to the main ATTENDO documentation or contact the system administrator.
