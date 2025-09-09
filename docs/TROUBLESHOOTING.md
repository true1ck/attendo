# ATTENDO Sync System Troubleshooting Guide

## Common Issues

### 1. Sync Not Working
**Symptoms:** Excel tables not updating, sync status shows failures

**Solutions:**
- Check database connection: `GET /api/monitor/check`
- Validate Excel file access permissions
- Check logs in `notification_sync.log` and `realtime_sync.log`
- Force manual sync: `POST /api/sync/trigger`

### 2. Power Automate Webhooks Not Triggering
**Symptoms:** Power Automate flows not responding to sync events

**Solutions:**
- Verify webhook URLs in configuration
- Check webhook endpoint accessibility
- Test webhook manually using curl/Postman
- Verify request timeout settings

### 3. Monitoring Alerts Not Sent
**Symptoms:** No email or Teams alerts despite sync failures

**Solutions:**
- Check email configuration (SMTP settings)
- Verify admin email addresses in configuration
- Test alerts: `GET /api/monitor/test-alert`
- Check Teams webhook URLs

### 4. Excel Files Missing or Corrupted
**Symptoms:** File read errors, validation failures

**Solutions:**
- Check file permissions on notification_configs folder
- Validate Excel file format and table structure
- Regenerate Excel files: Force full sync
- Check for disk space issues

## Diagnostic Commands

```bash
# Check system health
curl -X GET "http://localhost:5000/api/monitor/check"

# Validate sync accuracy
curl -X GET "http://localhost:5000/api/monitor/validate"

# Get sync status
curl -X GET "http://localhost:5000/api/sync/status"

# Force sync
curl -X POST "http://localhost:5000/api/sync/trigger" \
  -H "Content-Type: application/json" \
  -d '{"event_type": "manual_trigger", "entity_type": "all", "force_sync": true}'

# Repair sync issues
curl -X GET "http://localhost:5000/api/monitor/repair"
```

## Log Files

- `notification_sync.log` - Database sync operations
- `realtime_sync.log` - Real-time sync events  
- `sync_monitoring.log` - Monitoring and alerts
- `sync_reports/` - Generated sync reports

## Performance Tuning

### Sync Frequency
- Default: Every 5 minutes
- High-load systems: Increase to 10-15 minutes
- Low-change environments: Decrease to 2-3 minutes

### Monitoring Intervals
- Health checks: 30 minutes (default)
- Validation: 6 hours (default)
- Adjust based on system criticality

### Webhook Timeouts
- Default: 30 seconds
- Slow networks: Increase to 60 seconds
- Fast networks: Reduce to 15 seconds
