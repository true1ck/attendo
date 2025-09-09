"""
Complete Real-Time Notification Sync System Setup
This script integrates all components to create a fully functional real-time
notification system that keeps Excel tables synchronized with database changes.
"""

import os
import sys
from pathlib import Path
from flask import Flask

# Import our sync components
from notification_database_sync import setup_notification_database_sync
from realtime_notification_sync import setup_realtime_sync, register_database_change_hooks
from notification_sync_monitor import setup_notification_sync_monitor

def setup_complete_notification_sync_system(app: Flask):
    """
    Complete setup function to initialize all components of the real-time notification sync system
    
    Args:
        app (Flask): The Flask application instance
        
    Returns:
        dict: Dictionary containing all initialized components
    """
    
    print("🚀 Setting up Complete Real-Time Notification Sync System...")
    
    # Step 1: Initialize the database sync manager
    print("📊 Step 1: Initializing Database Sync Manager...")
    sync_manager = setup_notification_database_sync(app)
    print("✅ Database sync manager initialized")
    
    # Step 2: Initialize the real-time sync system
    print("⚡ Step 2: Initializing Real-Time Sync System...")
    realtime_sync = setup_realtime_sync(app, sync_manager)
    print("✅ Real-time sync system initialized")
    
    # Step 3: Register database change hooks
    print("🔗 Step 3: Registering Database Change Hooks...")
    register_database_change_hooks(app, realtime_sync)
    print("✅ Database change hooks registered")
    
    # Step 4: Initialize the monitoring system
    print("🔍 Step 4: Initializing Monitoring System...")
    monitor = setup_notification_sync_monitor(app, sync_manager, realtime_sync)
    print("✅ Monitoring system initialized")
    
    # Step 5: Perform initial sync
    print("🔄 Step 5: Performing Initial Sync...")
    try:
        sync_manager.sync_all_excel_tables()
        print("✅ Initial sync completed successfully")
    except Exception as e:
        print(f"⚠️ Initial sync encountered an issue: {str(e)}")
        print("   This is normal if no users exist yet")
    
    # Step 6: Validate system health
    print("🏥 Step 6: Validating System Health...")
    health_check = monitor.perform_health_check()
    if health_check['issues']:
        print(f"⚠️ System health issues detected: {health_check['issues']}")
    else:
        print("✅ System health check passed")
    
    print("\n🎉 Real-Time Notification Sync System Setup Complete!")
    print("=" * 60)
    print("📋 System Summary:")
    print(f"   📁 Excel Files Location: {sync_manager.excel_folder_path}")
    print(f"   📊 Excel Configurations: {len(sync_manager.excel_configs)} files")
    print(f"   🔄 Real-time Sync: {'Running' if realtime_sync.is_running else 'Stopped'}")
    print(f"   📡 Webhook Endpoints: {len(realtime_sync.config['power_automate_webhook_urls'])} configured")
    print(f"   🔍 Monitoring: Active with {monitor.config['monitoring_interval_minutes']}min intervals")
    print("=" * 60)
    print("\n🌐 Available Endpoints:")
    print("   📤 Manual Sync Trigger: POST /api/sync/trigger")
    print("   📊 Sync Status: GET /api/sync/status")
    print("   📡 Power Automate Webhook: POST /api/sync/webhook/power-automate")
    print("   🔍 Health Check: GET /api/monitor/check")
    print("   ✅ Validate Sync: GET /api/monitor/validate")
    print("   🔧 Auto Repair: GET /api/monitor/repair")
    print("   📈 Generate Report: GET /api/monitor/report")
    print("=" * 60)
    
    # Return all components for further use
    return {
        'sync_manager': sync_manager,
        'realtime_sync': realtime_sync,
        'monitor': monitor,
        'health_status': health_check
    }

def add_configuration_recommendations(app: Flask):
    """
    Add recommended configuration settings to Flask app
    """
    print("\n⚙️ Configuration Recommendations:")
    print("Add these settings to your Flask app configuration:")
    print()
    print("```python")
    print("# Real-time sync settings")
    print("SYNC_INTERVAL_MINUTES = 5")
    print("WEBHOOK_TIMEOUT_SECONDS = 30")
    print("ENABLE_POWER_AUTOMATE_WEBHOOKS = True")
    print()
    print("# Power Automate webhook URLs (add your actual URLs)")
    print("POWER_AUTOMATE_WEBHOOK_URLS = [")
    print("    'https://prod-xx.westus.logic.azure.com/workflows/...',")
    print("    'https://prod-yy.westus.logic.azure.com/workflows/...'")
    print("]")
    print()
    print("# Monitoring settings")
    print("SYNC_MONITORING_INTERVAL_MINUTES = 30")
    print("SYNC_VALIDATION_INTERVAL_HOURS = 6")
    print("ADMIN_EMAILS = ['admin@yourcompany.com']")
    print()
    print("# Email alerts")
    print("SYNC_ALERT_FROM = 'attendo-sync@yourcompany.com'")
    print("SMTP_SERVER = 'smtp.yourcompany.com'")
    print("SMTP_PORT = 587")
    print("```")
    print()

def create_example_power_automate_flow():
    """
    Create example Power Automate flow definitions
    """
    flows_dir = Path("power_automate_examples")
    flows_dir.mkdir(exist_ok=True)
    
    # Example 1: Real-time sync monitor flow
    monitor_flow = {
        "definition": {
            "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
            "actions": {
                "Check_Sync_Status": {
                    "type": "Http",
                    "inputs": {
                        "method": "GET",
                        "uri": "https://your-attendo-server.com/api/sync/status"
                    }
                },
                "Parse_Status_Response": {
                    "type": "ParseJson",
                    "inputs": {
                        "content": "@body('Check_Sync_Status')",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string"},
                                "metrics": {
                                    "type": "object",
                                    "properties": {
                                        "failed_syncs": {"type": "integer"},
                                        "total_syncs": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "runAfter": {
                        "Check_Sync_Status": ["Succeeded"]
                    }
                },
                "Check_For_Failures": {
                    "type": "If",
                    "expression": {
                        "greater": [
                            "@body('Parse_Status_Response')?['metrics']?['failed_syncs']",
                            0
                        ]
                    },
                    "actions": {
                        "Send_Alert_To_Teams": {
                            "type": "Http",
                            "inputs": {
                                "method": "POST",
                                "uri": "https://graph.microsoft.com/v1.0/teams/{team-id}/channels/{channel-id}/messages",
                                "headers": {
                                    "Authorization": "Bearer @{variables('TeamsToken')}",
                                    "Content-Type": "application/json"
                                },
                                "body": {
                                    "body": {
                                        "content": "🚨 ATTENDO Sync Alert: @{body('Parse_Status_Response')?['metrics']?['failed_syncs']} sync failures detected!"
                                    }
                                }
                            }
                        },
                        "Trigger_Force_Sync": {
                            "type": "Http",
                            "inputs": {
                                "method": "POST",
                                "uri": "https://your-attendo-server.com/api/sync/trigger",
                                "headers": {
                                    "Content-Type": "application/json"
                                },
                                "body": {
                                    "event_type": "manual_trigger",
                                    "entity_type": "all",
                                    "force_sync": True
                                }
                            },
                            "runAfter": {
                                "Send_Alert_To_Teams": ["Succeeded"]
                            }
                        }
                    },
                    "runAfter": {
                        "Parse_Status_Response": ["Succeeded"]
                    }
                }
            },
            "triggers": {
                "Recurrence": {
                    "type": "Recurrence",
                    "recurrence": {
                        "frequency": "Minute",
                        "interval": 30
                    }
                }
            }
        }
    }
    
    # Save example flow
    with open(flows_dir / "sync_monitor_flow.json", "w") as f:
        import json
        json.dump(monitor_flow, f, indent=2)
    
    print(f"\n📁 Example Power Automate flows created in: {flows_dir}")
    print("   - sync_monitor_flow.json - Monitors sync health and alerts on failures")

def create_documentation():
    """
    Create additional documentation files
    """
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Create API reference
    api_doc = """# ATTENDO Real-Time Sync API Reference

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
"""
    
    with open(docs_dir / "API_REFERENCE.md", "w") as f:
        f.write(api_doc)
    
    # Create troubleshooting guide
    troubleshooting_doc = """# ATTENDO Sync System Troubleshooting Guide

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
curl -X POST "http://localhost:5000/api/sync/trigger" \\
  -H "Content-Type: application/json" \\
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
"""
    
    with open(docs_dir / "TROUBLESHOOTING.md", "w") as f:
        f.write(troubleshooting_doc)
    
    print(f"\n📚 Documentation created in: {docs_dir}")
    print("   - API_REFERENCE.md - Complete API documentation")
    print("   - TROUBLESHOOTING.md - Common issues and solutions")

# Example usage in Flask app
def example_flask_integration():
    """
    Example of how to integrate the sync system into an existing Flask app
    """
    integration_example = '''
# Add this to your main Flask app file (e.g., app.py)

from setup_realtime_notification_sync import setup_complete_notification_sync_system

# After creating your Flask app and database models
app = Flask(__name__)
# ... your existing app setup ...

# Initialize the complete real-time notification sync system
if __name__ == "__main__":
    with app.app_context():
        # Setup the complete sync system
        sync_components = setup_complete_notification_sync_system(app)
        
        # Store components for later use
        app.sync_manager = sync_components['sync_manager']
        app.realtime_sync = sync_components['realtime_sync']
        app.monitor = sync_components['monitor']
        
        # Run the Flask app
        app.run(debug=True, host='0.0.0.0', port=5000)
'''
    
    print("\n💡 Flask Integration Example:")
    print(integration_example)

if __name__ == "__main__":
    """
    Main setup function - call this to set up the complete system
    """
    print("🔧 ATTENDO Real-Time Notification Sync System Setup")
    print("=" * 60)
    print("This script sets up a complete real-time notification sync system")
    print("that keeps Excel configuration tables synchronized with database changes.")
    print()
    print("To integrate with your Flask app, import and call:")
    print("  from setup_realtime_notification_sync import setup_complete_notification_sync_system")
    print("  sync_components = setup_complete_notification_sync_system(app)")
    print()
    
    # Create example files and documentation
    create_example_power_automate_flow()
    create_documentation()
    add_configuration_recommendations(None)
    example_flask_integration()
    
    print("\n✅ Setup resources created successfully!")
    print("📋 Next steps:")
    print("1. Add the recommended configuration to your Flask app")
    print("2. Import and call setup_complete_notification_sync_system(app)")
    print("3. Upload Excel files to SharePoint/OneDrive")
    print("4. Create Power Automate flows using the example templates")
    print("5. Configure monitoring alerts (email/Teams)")
    print("6. Test the complete system end-to-end")
    print()
    print("🚀 Your real-time notification sync system is ready to deploy!")
