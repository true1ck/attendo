# ATTENDO Real-Time Sync API Reference

## Sync Endpoints

### POST /api/sync/trigger
Manually trigger a sync operation.

**Request Body:**
```json
{
  "event_type": "manual_trigger",
  "entity_type": "all|user|vendor|manager|file",
  "entity_id": "optional_entity_id",
  "force_sync": true|false,
  "metadata": {}
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Sync event queued successfully",
  "event_id": "unique_event_identifier"
}
```

### GET /api/sync/status
Get current sync system status and metrics.

**Response:**
```json
{
  "status": "running|stopped",
  "queue_size": 0,
  "metrics": {
    "total_syncs": 45,
    "successful_syncs": 44,
    "failed_syncs": 1,
    "last_sync_time": "2025-01-09T17:45:00Z",
    "average_sync_duration": 2.5
  },
  "config": {},
  "last_sync_hash": {}
}
```

### POST /api/sync/webhook/power-automate
Power Automate webhook for triggering sync operations.

**Request Body:**
```json
{
  "syncType": "full|partial",
  "targetFiles": ["01_daily_status_reminders.xlsx"],
  "forceSync": false
}
```

### POST /api/sync/webhook/database-change
Webhook for database change notifications.

**Request Body:**
```json
{
  "table_name": "users|vendors|managers",
  "operation": "INSERT|UPDATE|DELETE",
  "record_id": "123",
  "old_values": {},
  "new_values": {}
}
```

## Monitoring Endpoints

### GET /api/monitor/status
Get monitoring system status.

### GET /api/monitor/check
Perform health check on sync system.

### GET /api/monitor/validate
Validate Excel tables against database.

### GET /api/monitor/repair
Attempt to repair sync issues.

### GET /api/monitor/report
Generate comprehensive sync report.

### GET /api/monitor/test-alert
Send test alert through configured channels.
