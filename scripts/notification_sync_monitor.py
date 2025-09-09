"""
Notification Sync Monitoring and Validation System
Provides tools to monitor sync status, validate Excel tables against database,
detect and correct sync issues, and generate reports on notification system health.
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from flask import Flask, jsonify, render_template, Blueprint

# Import our sync utilities
from notification_database_sync import NotificationDatabaseSync
from realtime_notification_sync import RealtimeNotificationSync, SyncEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_monitoring.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class NotificationSyncMonitor:
    """
    Monitors notification sync system health and provides validation tools
    """
    
    def __init__(
        self, 
        app: Flask = None, 
        sync_manager: NotificationDatabaseSync = None,
        realtime_sync: RealtimeNotificationSync = None
    ):
        self.app = app
        self.sync_manager = sync_manager
        self.realtime_sync = realtime_sync
        
        # Monitoring configuration
        self.config = {
            'alert_thresholds': {
                'sync_failure_count': 3,
                'consecutive_failures': 2,
                'sync_duration_seconds': 300,
                'validation_failures': 1
            },
            'email_alerts': {
                'enabled': True,
                'recipients': [],
                'from_address': 'notification-sync@attendo.com',
                'smtp_server': 'localhost',
                'smtp_port': 25
            },
            'monitoring_interval_minutes': 30,
            'validation_interval_hours': 6,
            'health_check_endpoints': [],
            'report_path': 'sync_reports',
            'max_report_age_days': 14
        }
        
        # Monitoring state
        self.monitoring_state = {
            'last_check': None,
            'last_validation': None,
            'consecutive_failures': 0,
            'last_report_time': None,
            'sync_history': [],
            'validation_history': [],
            'active_alerts': []
        }
        
        # Setup blueprints
        self.setup_blueprints()
    
    def init_app(self, app: Flask, sync_manager: NotificationDatabaseSync, realtime_sync: RealtimeNotificationSync):
        """Initialize with Flask app and sync utilities"""
        self.app = app
        self.sync_manager = sync_manager
        self.realtime_sync = realtime_sync
        
        # Register blueprint
        app.register_blueprint(self.monitor_blueprint, url_prefix='/api/monitor')
        
        # Load configuration from app config
        self.load_config_from_app()
        
        # Create report directory
        if not os.path.exists(self.config['report_path']):
            os.makedirs(self.config['report_path'])
        
        logger.info("Notification sync monitoring system initialized")
    
    def load_config_from_app(self):
        """Load configuration from Flask app config"""
        if self.app:
            app_config = self.app.config
            
            # Email configuration
            smtp_server = app_config.get('SMTP_SERVER')
            if smtp_server:
                self.config['email_alerts'].update({
                    'enabled': True,
                    'smtp_server': smtp_server,
                    'smtp_port': app_config.get('SMTP_PORT', 25),
                    'from_address': app_config.get('SYNC_ALERT_FROM', 'notification-sync@attendo.com')
                })
            
            # Recipients
            admin_emails = app_config.get('ADMIN_EMAILS', [])
            if admin_emails:
                self.config['email_alerts']['recipients'] = admin_emails
            
            # Monitoring intervals
            if app_config.get('SYNC_MONITORING_INTERVAL_MINUTES'):
                self.config['monitoring_interval_minutes'] = app_config.get('SYNC_MONITORING_INTERVAL_MINUTES')
            
            if app_config.get('SYNC_VALIDATION_INTERVAL_HOURS'):
                self.config['validation_interval_hours'] = app_config.get('SYNC_VALIDATION_INTERVAL_HOURS')
    
    def setup_blueprints(self):
        """Setup Flask blueprints for monitoring endpoints"""
        self.monitor_blueprint = Blueprint('monitor', __name__)
        
        @self.monitor_blueprint.route('/status', methods=['GET'])
        def monitor_status():
            """Get monitoring system status"""
            try:
                return jsonify({
                    'status': 'active',
                    'config': self.config,
                    'state': self.monitoring_state,
                    'active_alerts': self.monitoring_state['active_alerts']
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.monitor_blueprint.route('/check', methods=['GET'])
        def run_health_check():
            """Run a health check"""
            try:
                check_result = self.perform_health_check()
                return jsonify({
                    'status': 'success',
                    'health_check': check_result
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.monitor_blueprint.route('/validate', methods=['GET'])
        def run_validation():
            """Run a validation check"""
            try:
                validation_result = self.validate_sync_accuracy()
                return jsonify({
                    'status': 'success',
                    'validation': validation_result
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.monitor_blueprint.route('/repair', methods=['GET'])
        def repair_sync_issues():
            """Attempt to repair sync issues"""
            try:
                repair_result = self.repair_sync_issues()
                return jsonify({
                    'status': 'success',
                    'repair': repair_result
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.monitor_blueprint.route('/report', methods=['GET'])
        def generate_report():
            """Generate sync report"""
            try:
                report_result = self.generate_sync_report()
                return jsonify({
                    'status': 'success',
                    'report': report_result
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.monitor_blueprint.route('/test-alert', methods=['GET'])
        def test_alert():
            """Send test alert"""
            try:
                test_alert = {
                    'type': 'test',
                    'title': 'Test Alert',
                    'message': 'This is a test alert from the notification sync monitor',
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'info'
                }
                
                alert_sent = self.send_alert(test_alert)
                
                return jsonify({
                    'status': 'success',
                    'alert_sent': alert_sent,
                    'alert': test_alert
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
    
    def perform_health_check(self) -> Dict:
        """Perform a health check on the sync system"""
        check_result = {
            'timestamp': datetime.now().isoformat(),
            'database_connection': False,
            'excel_access': False,
            'sync_manager_status': 'not_checked',
            'realtime_sync_status': 'not_checked',
            'sync_queue_size': 0,
            'last_sync_time': None,
            'failures_detected': False,
            'issues': []
        }
        
        try:
            if not self.app or not self.sync_manager or not self.realtime_sync:
                check_result['issues'].append('Components not fully initialized')
                return check_result
            
            # Check database connection
            with self.app.app_context():
                from models import User
                from app import db
                
                # Test DB connection with a simple query
                db.session.query(User).limit(1).all()
                check_result['database_connection'] = True
            
            # Check Excel files access
            excel_path = self.sync_manager.excel_folder_path
            if excel_path.exists() and excel_path.is_dir():
                # Count Excel files
                excel_files = list(excel_path.glob('*.xlsx'))
                check_result['excel_access'] = True
                check_result['excel_files_count'] = len(excel_files)
            
            # Check sync manager
            check_result['sync_manager_status'] = 'available'
            
            # Check realtime sync
            if self.realtime_sync.is_running:
                check_result['realtime_sync_status'] = 'running'
                check_result['sync_queue_size'] = self.realtime_sync.sync_queue.qsize()
                check_result['last_sync_time'] = self.realtime_sync.metrics.get('last_sync_time')
            else:
                check_result['realtime_sync_status'] = 'stopped'
                check_result['issues'].append('Realtime sync worker is not running')
            
            # Check for recent failures
            if self.realtime_sync.metrics.get('failed_syncs', 0) > 0:
                recent_failures = self.realtime_sync.metrics.get('failed_syncs', 0)
                check_result['failures_detected'] = True
                check_result['issues'].append(f'Recent sync failures detected: {recent_failures}')
            
            # Record health check
            self.monitoring_state['last_check'] = datetime.now().isoformat()
            self.monitoring_state['sync_history'].append({
                'timestamp': datetime.now().isoformat(),
                'type': 'health_check',
                'status': 'healthy' if not check_result['issues'] else 'issues_detected',
                'issues': check_result['issues']
            })
            
            # Limit history size
            if len(self.monitoring_state['sync_history']) > 100:
                self.monitoring_state['sync_history'] = self.monitoring_state['sync_history'][-100:]
                
            return check_result
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            check_result['issues'].append(f"Error during health check: {str(e)}")
            
            # Record failed health check
            self.monitoring_state['sync_history'].append({
                'timestamp': datetime.now().isoformat(),
                'type': 'health_check',
                'status': 'failed',
                'issues': [str(e)]
            })
            
            # Increment consecutive failures
            self.monitoring_state['consecutive_failures'] += 1
            
            # Send alert if threshold reached
            if self.monitoring_state['consecutive_failures'] >= self.config['alert_thresholds']['consecutive_failures']:
                self.send_alert({
                    'type': 'health_check_failure',
                    'title': 'Health Check Failures',
                    'message': f"Multiple consecutive health check failures detected. Last error: {str(e)}",
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'critical'
                })
            
            return check_result
    
    def validate_sync_accuracy(self) -> Dict:
        """Validate that Excel tables are in sync with database"""
        try:
            if not self.sync_manager or not self.app:
                return {
                    'status': 'error',
                    'message': 'Sync manager not initialized'
                }
            
            # Get validation from sync manager
            validation_results = self.sync_manager.validate_sync_accuracy()
            
            # Record validation
            self.monitoring_state['last_validation'] = datetime.now().isoformat()
            self.monitoring_state['validation_history'].append({
                'timestamp': datetime.now().isoformat(),
                'issues_count': len(validation_results['sync_issues']),
                'details': validation_results
            })
            
            # Limit history size
            if len(self.monitoring_state['validation_history']) > 20:
                self.monitoring_state['validation_history'] = self.monitoring_state['validation_history'][-20:]
            
            # Generate alert if issues found
            if validation_results['sync_issues'] and len(validation_results['sync_issues']) >= self.config['alert_thresholds']['validation_failures']:
                self.send_alert({
                    'type': 'validation_failure',
                    'title': 'Excel Sync Validation Failures',
                    'message': f"Found {len(validation_results['sync_issues'])} sync issues during validation",
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'warning',
                    'details': validation_results['sync_issues']
                })
                
                # Queue repair if validation fails
                if self.realtime_sync:
                    self.realtime_sync.queue_sync_event(SyncEvent(
                        event_type='repair_sync',
                        entity_type='all',
                        action='UPDATE',
                        metadata={'source': 'validation_monitor', 'force_sync': True}
                    ))
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            self.send_alert({
                'type': 'validation_error',
                'title': 'Excel Sync Validation Error',
                'message': f"Error during sync validation: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'severity': 'error'
            })
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def repair_sync_issues(self) -> Dict:
        """Attempt to repair sync issues"""
        try:
            if not self.sync_manager or not self.realtime_sync:
                return {
                    'status': 'error',
                    'message': 'Sync components not initialized'
                }
            
            # Get current validation state
            validation_results = self.sync_manager.validate_sync_accuracy()
            issues_before = len(validation_results['sync_issues'])
            
            if issues_before == 0:
                return {
                    'status': 'success',
                    'message': 'No sync issues to repair',
                    'issues_fixed': 0
                }
            
            # Force a full sync to repair issues
            self.sync_manager.sync_all_excel_tables()
            
            # Check validation after repair
            validation_after = self.sync_manager.validate_sync_accuracy()
            issues_after = len(validation_after['sync_issues'])
            
            repair_results = {
                'status': 'success',
                'issues_before': issues_before,
                'issues_after': issues_after,
                'issues_fixed': issues_before - issues_after,
                'remaining_issues': validation_after['sync_issues'] if issues_after > 0 else []
            }
            
            # Send alert on repair results
            if issues_after == 0:
                self.send_alert({
                    'type': 'repair_success',
                    'title': 'Sync Issues Repaired',
                    'message': f"Successfully repaired {issues_before} sync issues",
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'info'
                })
            else:
                self.send_alert({
                    'type': 'repair_partial',
                    'title': 'Partial Sync Repair',
                    'message': f"Fixed {issues_before - issues_after} issues, but {issues_after} issues remain",
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'warning',
                    'details': validation_after['sync_issues']
                })
            
            return repair_results
            
        except Exception as e:
            logger.error(f"Repair error: {str(e)}")
            self.send_alert({
                'type': 'repair_error',
                'title': 'Sync Repair Error',
                'message': f"Error during sync repair: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'severity': 'error'
            })
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def generate_sync_report(self) -> Dict:
        """Generate comprehensive sync status report"""
        try:
            if not self.app or not self.sync_manager or not self.realtime_sync:
                return {
                    'status': 'error',
                    'message': 'Components not fully initialized'
                }
            
            report_time = datetime.now()
            report_id = f"sync_report_{report_time.strftime('%Y%m%d_%H%M%S')}"
            report_file = os.path.join(self.config['report_path'], f"{report_id}.json")
            
            # Get health check
            health_check = self.perform_health_check()
            
            # Get validation
            validation = self.sync_manager.validate_sync_accuracy()
            
            # Get sync metrics
            sync_metrics = self.realtime_sync.metrics
            
            # Get detailed Excel table statistics
            excel_stats = {}
            
            with self.app.app_context():
                from models import User, Vendor, Manager, UserRole
                from app import db
                
                # Count database records by type
                total_users = db.session.query(User).count()
                active_users = db.session.query(User).filter(User.is_active == True).count()
                vendors = db.session.query(User).filter(User.role == UserRole.VENDOR).count()
                managers = db.session.query(User).filter(User.role == UserRole.MANAGER).count()
                admins = db.session.query(User).filter(User.role == UserRole.ADMIN).count()
                
                # Excel table statistics
                for filename, config in self.sync_manager.excel_configs.items():
                    file_path = self.sync_manager.excel_folder_path / filename
                    
                    if file_path.exists():
                        try:
                            df = pd.read_excel(file_path, sheet_name=config["table_name"])
                            active_records = len(df[df['Active'] == 'YES'])
                            inactive_records = len(df[df['Active'] == 'NO'])
                            
                            # Expected count based on database
                            expected_count = db.session.query(User).filter(
                                User.role.in_([UserRole(role) for role in config["roles"]]),
                                User.is_active == True
                            ).count()
                            
                            excel_stats[filename] = {
                                'total_records': len(df),
                                'active_records': active_records,
                                'inactive_records': inactive_records,
                                'expected_active_count': expected_count,
                                'is_synced': active_records == expected_count,
                                'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            }
                        except Exception as e:
                            excel_stats[filename] = {
                                'error': str(e),
                                'is_synced': False
                            }
                    else:
                        excel_stats[filename] = {
                            'error': 'File does not exist',
                            'is_synced': False
                        }
            
            # Compile the report
            report = {
                'report_id': report_id,
                'timestamp': report_time.isoformat(),
                'health_check': health_check,
                'validation': validation,
                'sync_metrics': sync_metrics,
                'database_stats': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'vendors': vendors,
                    'managers': managers,
                    'admins': admins
                },
                'excel_stats': excel_stats,
                'sync_history': self.monitoring_state['sync_history'][-10:],
                'validation_history': self.monitoring_state['validation_history'][-5:],
                'active_alerts': self.monitoring_state['active_alerts']
            }
            
            # Save report to file
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=4)
            
            # Update monitoring state
            self.monitoring_state['last_report_time'] = report_time.isoformat()
            
            # Clean up old reports
            self.clean_old_reports()
            
            return {
                'status': 'success',
                'report_id': report_id,
                'report_file': report_file,
                'timestamp': report_time.isoformat(),
                'summary': {
                    'database_records': total_users,
                    'excel_files': len(excel_stats),
                    'sync_issues': len(validation['sync_issues']),
                    'health_status': 'healthy' if not health_check['issues'] else 'issues_detected'
                }
            }
            
        except Exception as e:
            logger.error(f"Report generation error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def clean_old_reports(self):
        """Clean up old report files"""
        try:
            report_dir = Path(self.config['report_path'])
            if not report_dir.exists() or not report_dir.is_dir():
                return
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=self.config['max_report_age_days'])
            
            for report_file in report_dir.glob('sync_report_*.json'):
                try:
                    # Extract timestamp from filename
                    timestamp_str = report_file.stem.split('_', 2)[2]
                    file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    
                    # Delete if older than cutoff
                    if file_date < cutoff_date:
                        report_file.unlink()
                        logger.info(f"Deleted old report: {report_file}")
                except Exception as e:
                    logger.warning(f"Error cleaning up report file {report_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old reports: {str(e)}")
    
    def send_alert(self, alert: Dict) -> bool:
        """Send alert via configured channels"""
        try:
            # Add alert to active alerts
            alert_id = f"alert_{int(time.time())}_{hash(alert['title'])}"
            alert['id'] = alert_id
            
            # Add to active alerts
            self.monitoring_state['active_alerts'].append(alert)
            
            # Limit active alerts to most recent 20
            if len(self.monitoring_state['active_alerts']) > 20:
                self.monitoring_state['active_alerts'] = self.monitoring_state['active_alerts'][-20:]
            
            # Log the alert
            logger.warning(f"SYNC ALERT: {alert['title']} - {alert['message']}")
            
            # Send email alert if configured
            if self.config['email_alerts']['enabled'] and self.config['email_alerts']['recipients']:
                self.send_email_alert(alert)
            
            # If Power Automate webhook is available, send alert
            if self.realtime_sync and self.realtime_sync.config['enable_power_automate_webhooks']:
                webhook_urls = self.realtime_sync.config['power_automate_webhook_urls']
                if webhook_urls:
                    self.send_webhook_alert(alert, webhook_urls[0])
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")
            return False
    
    def send_email_alert(self, alert: Dict) -> bool:
        """Send email alert"""
        try:
            recipients = self.config['email_alerts']['recipients']
            from_address = self.config['email_alerts']['from_address']
            smtp_server = self.config['email_alerts']['smtp_server']
            smtp_port = self.config['email_alerts']['smtp_port']
            
            if not recipients or not smtp_server:
                logger.warning("Email alert not sent - missing configuration")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_address
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"SYNC ALERT: {alert['title']}"
            
            # Email body
            body = f"""
<html>
<body>
<h2>Notification Sync Alert</h2>
<p><strong>Type:</strong> {alert['type']}</p>
<p><strong>Severity:</strong> {alert['severity']}</p>
<p><strong>Time:</strong> {alert['timestamp']}</p>
<p><strong>Message:</strong> {alert['message']}</p>
"""
            
            # Add details if available
            if 'details' in alert and alert['details']:
                body += "<h3>Details:</h3><pre>" + json.dumps(alert['details'], indent=2) + "</pre>"
            
            body += """
<p>This is an automated message from the notification sync monitoring system.</p>
</body>
</html>
"""
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.send_message(msg)
                
            logger.info(f"Email alert sent to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}")
            return False
    
    def send_webhook_alert(self, alert: Dict, webhook_url: str) -> bool:
        """Send alert via webhook"""
        try:
            import requests
            
            payload = {
                'alert_type': 'sync_monitor_alert',
                'alert': alert
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=30,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'ATTENDO-SyncMonitor/1.0'
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook alert sent successfully to {webhook_url}")
                return True
            else:
                logger.warning(f"Webhook alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending webhook alert: {str(e)}")
            return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        try:
            # Find and remove the alert
            self.monitoring_state['active_alerts'] = [
                a for a in self.monitoring_state['active_alerts'] if a.get('id') != alert_id
            ]
            logger.info(f"Alert {alert_id} resolved")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {str(e)}")
            return False
    
    def schedule_monitoring_tasks(self):
        """Schedule monitoring tasks to run in the background"""
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        
        scheduler = BackgroundScheduler()
        
        # Schedule health check
        scheduler.add_job(
            self.perform_health_check,
            IntervalTrigger(minutes=self.config['monitoring_interval_minutes']),
            id='health_check'
        )
        
        # Schedule validation
        scheduler.add_job(
            self.validate_sync_accuracy,
            IntervalTrigger(hours=self.config['validation_interval_hours']),
            id='validation'
        )
        
        # Schedule daily report
        scheduler.add_job(
            self.generate_sync_report,
            IntervalTrigger(hours=24),
            id='daily_report'
        )
        
        # Start the scheduler
        scheduler.start()
        logger.info("Monitoring tasks scheduled")

def setup_notification_sync_monitor(app: Flask, sync_manager: NotificationDatabaseSync, realtime_sync: RealtimeNotificationSync) -> NotificationSyncMonitor:
    """Setup function to initialize sync monitoring with Flask app"""
    monitor = NotificationSyncMonitor()
    monitor.init_app(app, sync_manager, realtime_sync)
    
    # Schedule monitoring tasks
    monitor.schedule_monitoring_tasks()
    
    logger.info("Notification sync monitoring system initialized")
    return monitor

if __name__ == "__main__":
    # Example usage
    print("Notification Sync Monitoring System")
    print("This module should be imported and initialized with your Flask app")
    print("Example:")
    print("  from notification_sync_monitor import setup_notification_sync_monitor")
    print("  monitor = setup_notification_sync_monitor(app, sync_manager, realtime_sync)")
