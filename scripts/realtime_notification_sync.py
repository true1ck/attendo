"""
Real-time Notification Sync System
Provides multiple synchronization mechanisms for keeping Excel tables updated:
1. Webhook-based real-time sync
2. Scheduled background sync
3. Manual trigger endpoints
4. Power Automate webhook integration
"""

import os
import sys
import json
import logging
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass
from queue import Queue, Empty
import requests
import schedule
from flask import Flask, request, jsonify, Blueprint
from threading import Thread, Lock
import hashlib

# Import our sync utility
from notification_database_sync import NotificationDatabaseSync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('realtime_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SyncEvent:
    """Represents a synchronization event"""
    event_type: str  # 'user_change', 'scheduled_sync', 'manual_trigger'
    entity_type: str  # 'user', 'vendor', 'manager', 'all'
    entity_id: Optional[str] = None
    action: str = 'UPDATE'  # 'INSERT', 'UPDATE', 'DELETE'
    timestamp: datetime = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class RealtimeNotificationSync:
    """
    Real-time synchronization system for notification tables
    """
    
    def __init__(self, app: Flask = None, sync_manager: NotificationDatabaseSync = None):
        self.app = app
        self.sync_manager = sync_manager
        self.sync_queue = Queue()
        self.sync_lock = Lock()
        self.is_running = False
        self.sync_thread = None
        self.webhook_endpoints = []
        self.last_sync_hash = {}
        
        # Configuration
        self.config = {
            'sync_interval_minutes': 5,
            'batch_sync_enabled': True,
            'webhook_timeout_seconds': 30,
            'max_retry_attempts': 3,
            'enable_power_automate_webhooks': True,
            'power_automate_webhook_urls': []
        }
        
        # Performance metrics
        self.metrics = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'last_sync_time': None,
            'average_sync_duration': 0,
            'webhook_calls': 0,
            'queue_size': 0
        }
        
        self.setup_blueprints()
        self.setup_scheduled_sync()
        
    def init_app(self, app: Flask, sync_manager: NotificationDatabaseSync):
        """Initialize with Flask app and sync manager"""
        self.app = app
        self.sync_manager = sync_manager
        
        # Register blueprints
        app.register_blueprint(self.sync_blueprint, url_prefix='/api/sync')
        
        # Load configuration from app config
        self.load_config_from_app()
        
        # Start the sync worker
        self.start_sync_worker()
        
    def load_config_from_app(self):
        """Load configuration from Flask app config"""
        if self.app:
            app_config = self.app.config
            self.config.update({
                'sync_interval_minutes': app_config.get('SYNC_INTERVAL_MINUTES', 5),
                'webhook_timeout_seconds': app_config.get('WEBHOOK_TIMEOUT_SECONDS', 30),
                'enable_power_automate_webhooks': app_config.get('ENABLE_POWER_AUTOMATE_WEBHOOKS', True),
                'power_automate_webhook_urls': app_config.get('POWER_AUTOMATE_WEBHOOK_URLS', [])
            })
    
    def setup_blueprints(self):
        """Setup Flask blueprints for sync endpoints"""
        self.sync_blueprint = Blueprint('sync', __name__)
        
        @self.sync_blueprint.route('/trigger', methods=['POST'])
        def trigger_sync():
            """Manual sync trigger endpoint"""
            try:
                data = request.get_json() or {}
                event_type = data.get('event_type', 'manual_trigger')
                entity_type = data.get('entity_type', 'all')
                entity_id = data.get('entity_id')
                action = data.get('action', 'UPDATE')
                
                event = SyncEvent(
                    event_type=event_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    action=action,
                    metadata=data.get('metadata', {})
                )
                
                self.queue_sync_event(event)
                
                return jsonify({
                    'status': 'success',
                    'message': 'Sync event queued successfully',
                    'event_id': str(hash(f"{event.event_type}_{event.entity_type}_{event.timestamp}"))
                })
                
            except Exception as e:
                logger.error(f"Error triggering sync: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.sync_blueprint.route('/status', methods=['GET'])
        def sync_status():
            """Get synchronization status and metrics"""
            try:
                return jsonify({
                    'status': 'running' if self.is_running else 'stopped',
                    'queue_size': self.sync_queue.qsize(),
                    'metrics': self.metrics,
                    'config': self.config,
                    'last_sync_hash': {k: v for k, v in self.last_sync_hash.items()}
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.sync_blueprint.route('/validate', methods=['GET'])
        def validate_sync():
            """Validate current sync status"""
            try:
                if not self.sync_manager:
                    return jsonify({
                        'status': 'error',
                        'message': 'Sync manager not initialized'
                    }), 500
                
                validation_results = self.sync_manager.validate_sync_accuracy()
                return jsonify({
                    'status': 'success',
                    'validation': validation_results
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.sync_blueprint.route('/webhook/power-automate', methods=['POST'])
        def power_automate_webhook():
            """Webhook endpoint for Power Automate integration"""
            try:
                data = request.get_json() or {}
                
                # Log webhook call
                logger.info(f"Power Automate webhook called: {data}")
                self.metrics['webhook_calls'] += 1
                
                # Extract sync requirements from Power Automate data
                sync_type = data.get('syncType', 'full')
                target_files = data.get('targetFiles', [])
                force_sync = data.get('forceSync', False)
                
                if sync_type == 'full' or not target_files:
                    # Full synchronization
                    event = SyncEvent(
                        event_type='power_automate_webhook',
                        entity_type='all',
                        action='UPDATE',
                        metadata={'force_sync': force_sync, 'source': 'power_automate'}
                    )
                else:
                    # Partial synchronization
                    for file_name in target_files:
                        event = SyncEvent(
                            event_type='power_automate_webhook',
                            entity_type='file',
                            entity_id=file_name,
                            action='UPDATE',
                            metadata={'force_sync': force_sync, 'source': 'power_automate'}
                        )
                        self.queue_sync_event(event)
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Queued sync for {len(target_files)} files',
                        'files_processed': target_files
                    })
                
                self.queue_sync_event(event)
                
                return jsonify({
                    'status': 'success',
                    'message': 'Power Automate sync triggered',
                    'sync_type': sync_type
                })
                
            except Exception as e:
                logger.error(f"Power Automate webhook error: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.sync_blueprint.route('/webhook/database-change', methods=['POST'])
        def database_change_webhook():
            """Webhook endpoint for database change notifications"""
            try:
                data = request.get_json() or {}
                
                table_name = data.get('table_name')
                operation = data.get('operation', 'UPDATE')
                record_id = data.get('record_id')
                old_values = data.get('old_values', {})
                new_values = data.get('new_values', {})
                
                # Determine entity type from table name
                entity_type = 'user'
                if table_name == 'vendors':
                    entity_type = 'vendor'
                elif table_name == 'managers':
                    entity_type = 'manager'
                
                event = SyncEvent(
                    event_type='database_change',
                    entity_type=entity_type,
                    entity_id=str(record_id),
                    action=operation.upper(),
                    metadata={
                        'table_name': table_name,
                        'old_values': old_values,
                        'new_values': new_values
                    }
                )
                
                self.queue_sync_event(event)
                
                logger.info(f"Database change webhook: {table_name} {operation} {record_id}")
                
                return jsonify({
                    'status': 'success',
                    'message': 'Database change sync queued',
                    'event_type': entity_type,
                    'operation': operation
                })
                
            except Exception as e:
                logger.error(f"Database change webhook error: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
    
    def setup_scheduled_sync(self):
        """Setup scheduled synchronization using the schedule library"""
        def run_scheduled_sync():
            """Run scheduled sync in a separate thread"""
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        # Schedule regular full sync
        schedule.every(self.config['sync_interval_minutes']).minutes.do(
            lambda: self.queue_sync_event(SyncEvent(
                event_type='scheduled_sync',
                entity_type='all',
                action='UPDATE',
                metadata={'source': 'scheduled'}
            ))
        )
        
        # Schedule validation checks (every hour)
        schedule.every().hour.do(
            lambda: self.queue_sync_event(SyncEvent(
                event_type='validation_check',
                entity_type='all',
                action='VALIDATE',
                metadata={'source': 'scheduled_validation'}
            ))
        )
        
        # Start scheduler thread
        self.scheduler_thread = Thread(target=run_scheduled_sync, daemon=True)
    
    def start_sync_worker(self):
        """Start the background sync worker thread"""
        if self.is_running:
            return
            
        self.is_running = True
        self.sync_thread = Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        
        # Start scheduler
        if hasattr(self, 'scheduler_thread'):
            self.scheduler_thread.start()
        
        logger.info("Real-time sync worker started")
    
    def stop_sync_worker(self):
        """Stop the background sync worker"""
        self.is_running = False
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        logger.info("Real-time sync worker stopped")
    
    def queue_sync_event(self, event: SyncEvent):
        """Add a sync event to the processing queue"""
        self.sync_queue.put(event)
        self.metrics['queue_size'] = self.sync_queue.qsize()
        logger.info(f"Queued sync event: {event.event_type} - {event.entity_type}")
    
    def _sync_worker(self):
        """Background worker that processes sync events"""
        logger.info("Sync worker thread started")
        
        while self.is_running:
            try:
                # Get event from queue (with timeout)
                try:
                    event = self.sync_queue.get(timeout=1)
                except Empty:
                    continue
                
                # Process the sync event
                self._process_sync_event(event)
                self.sync_queue.task_done()
                self.metrics['queue_size'] = self.sync_queue.qsize()
                
            except Exception as e:
                logger.error(f"Error in sync worker: {str(e)}")
                self.metrics['failed_syncs'] += 1
    
    def _process_sync_event(self, event: SyncEvent):
        """Process a single sync event"""
        start_time = time.time()
        
        try:
            with self.sync_lock:
                logger.info(f"Processing sync event: {event.event_type} - {event.entity_type}")
                
                if event.action == 'VALIDATE':
                    # Validation check
                    self._run_validation()
                elif event.entity_type == 'all':
                    # Full synchronization
                    self._run_full_sync(event)
                elif event.entity_type == 'file':
                    # Single file sync
                    self._sync_single_file(event)
                else:
                    # Targeted entity sync
                    self._sync_targeted_entity(event)
                
                # Update metrics
                duration = time.time() - start_time
                self.metrics['total_syncs'] += 1
                self.metrics['successful_syncs'] += 1
                self.metrics['last_sync_time'] = datetime.now().isoformat()
                
                # Update average duration
                if self.metrics['average_sync_duration'] == 0:
                    self.metrics['average_sync_duration'] = duration
                else:
                    self.metrics['average_sync_duration'] = (
                        self.metrics['average_sync_duration'] + duration
                    ) / 2
                
                # Send webhooks if configured
                self._send_power_automate_webhooks(event, success=True)
                
        except Exception as e:
            logger.error(f"Error processing sync event {event.event_type}: {str(e)}")
            self.metrics['failed_syncs'] += 1
            self._send_power_automate_webhooks(event, success=False, error=str(e))
    
    def _run_full_sync(self, event: SyncEvent):
        """Run full synchronization of all tables"""
        if not self.sync_manager:
            raise Exception("Sync manager not initialized")
        
        # Check if sync is needed (using hash)
        force_sync = event.metadata.get('force_sync', False)
        if not force_sync and not self._sync_needed():
            logger.info("Skipping full sync - no changes detected")
            return
        
        # Perform full sync
        self.sync_manager.sync_all_excel_tables()
        
        # Update sync hash
        self._update_sync_hash()
        
        logger.info("Full sync completed successfully")
    
    def _sync_single_file(self, event: SyncEvent):
        """Sync a single Excel file"""
        if not self.sync_manager:
            raise Exception("Sync manager not initialized")
        
        file_name = event.entity_id
        if file_name not in self.sync_manager.excel_configs:
            raise Exception(f"Unknown file: {file_name}")
        
        config = self.sync_manager.excel_configs[file_name]
        users_data = self.sync_manager.get_database_users()
        file_path = self.sync_manager.excel_folder_path / file_name
        
        self.sync_manager.update_excel_table(file_path, config, users_data)
        
        logger.info(f"Single file sync completed: {file_name}")
    
    def _sync_targeted_entity(self, event: SyncEvent):
        """Sync based on specific entity changes"""
        if not self.sync_manager:
            raise Exception("Sync manager not initialized")
        
        # For now, do a full sync for any entity change
        # This could be optimized to only update affected files
        self.sync_manager.sync_all_excel_tables()
        
        logger.info(f"Targeted entity sync completed: {event.entity_type}")
    
    def _run_validation(self):
        """Run sync validation check"""
        if not self.sync_manager:
            raise Exception("Sync manager not initialized")
        
        validation_results = self.sync_manager.validate_sync_accuracy()
        
        if validation_results['sync_issues']:
            logger.warning(f"Sync validation found {len(validation_results['sync_issues'])} issues")
            
            # Trigger corrective sync if issues found
            self.queue_sync_event(SyncEvent(
                event_type='corrective_sync',
                entity_type='all',
                action='UPDATE',
                metadata={'source': 'validation_correction'}
            ))
        else:
            logger.info("Sync validation passed - all tables in sync")
    
    def _sync_needed(self) -> bool:
        """Check if sync is needed by comparing database hash"""
        try:
            if not self.sync_manager or not self.app:
                return True
            
            with self.app.app_context():
                from models import User, Vendor, Manager
                from app import db
                
                # Create hash of current database state
                users = db.session.query(User).all()
                vendors = db.session.query(Vendor).all()
                managers = db.session.query(Manager).all()
                
                state_string = ""
                for user in users:
                    state_string += f"{user.id}_{user.email}_{user.role.value}_{user.is_active}_"
                for vendor in vendors:
                    state_string += f"{vendor.id}_{vendor.vendor_id}_{vendor.full_name}_{vendor.manager_id}_"
                for manager in managers:
                    state_string += f"{manager.id}_{manager.manager_id}_{manager.full_name}_"
                
                current_hash = hashlib.md5(state_string.encode()).hexdigest()
                last_hash = self.last_sync_hash.get('database_state')
                
                return current_hash != last_hash
                
        except Exception as e:
            logger.error(f"Error checking if sync needed: {str(e)}")
            return True  # Err on the side of syncing
    
    def _update_sync_hash(self):
        """Update the sync hash after successful sync"""
        try:
            if not self.sync_manager or not self.app:
                return
            
            with self.app.app_context():
                from models import User, Vendor, Manager
                from app import db
                
                users = db.session.query(User).all()
                vendors = db.session.query(Vendor).all()
                managers = db.session.query(Manager).all()
                
                state_string = ""
                for user in users:
                    state_string += f"{user.id}_{user.email}_{user.role.value}_{user.is_active}_"
                for vendor in vendors:
                    state_string += f"{vendor.id}_{vendor.vendor_id}_{vendor.full_name}_{vendor.manager_id}_"
                for manager in managers:
                    state_string += f"{manager.id}_{manager.manager_id}_{manager.full_name}_"
                
                current_hash = hashlib.md5(state_string.encode()).hexdigest()
                self.last_sync_hash['database_state'] = current_hash
                self.last_sync_hash['last_update'] = datetime.now().isoformat()
                
        except Exception as e:
            logger.error(f"Error updating sync hash: {str(e)}")
    
    def _send_power_automate_webhooks(self, event: SyncEvent, success: bool, error: str = None):
        """Send webhook notifications to Power Automate"""
        if not self.config['enable_power_automate_webhooks']:
            return
        
        webhook_urls = self.config['power_automate_webhook_urls']
        if not webhook_urls:
            return
        
        payload = {
            'event_type': event.event_type,
            'entity_type': event.entity_type,
            'entity_id': event.entity_id,
            'action': event.action,
            'timestamp': event.timestamp.isoformat(),
            'success': success,
            'error': error,
            'metadata': event.metadata
        }
        
        for webhook_url in webhook_urls:
            try:
                response = requests.post(
                    webhook_url,
                    json=payload,
                    timeout=self.config['webhook_timeout_seconds'],
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'ATTENDO-NotificationSync/1.0'
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook sent successfully to {webhook_url}")
                else:
                    logger.warning(f"Webhook failed to {webhook_url}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error sending webhook to {webhook_url}: {str(e)}")
    
    def add_webhook_endpoint(self, url: str):
        """Add a Power Automate webhook endpoint"""
        if url not in self.config['power_automate_webhook_urls']:
            self.config['power_automate_webhook_urls'].append(url)
            logger.info(f"Added webhook endpoint: {url}")
    
    def remove_webhook_endpoint(self, url: str):
        """Remove a Power Automate webhook endpoint"""
        if url in self.config['power_automate_webhook_urls']:
            self.config['power_automate_webhook_urls'].remove(url)
            logger.info(f"Removed webhook endpoint: {url}")

def setup_realtime_sync(app: Flask, sync_manager: NotificationDatabaseSync) -> RealtimeNotificationSync:
    """Setup function to initialize real-time sync with Flask app"""
    realtime_sync = RealtimeNotificationSync()
    realtime_sync.init_app(app, sync_manager)
    
    # Load webhook URLs from environment or config
    webhook_urls = app.config.get('POWER_AUTOMATE_WEBHOOK_URLS', [])
    for url in webhook_urls:
        realtime_sync.add_webhook_endpoint(url)
    
    logger.info("Real-time notification sync system initialized")
    return realtime_sync

# Integration with the main Flask app
def register_database_change_hooks(app: Flask, realtime_sync: RealtimeNotificationSync):
    """Register Flask-SQLAlchemy event hooks for real-time sync"""
    from models import User, Vendor, Manager
    from sqlalchemy import event
    
    def trigger_sync_for_user(mapper, connection, target):
        realtime_sync.queue_sync_event(SyncEvent(
            event_type='database_change',
            entity_type='user',
            entity_id=str(target.id),
            action='UPDATE',
            metadata={'username': target.username, 'role': target.role.value}
        ))
    
    def trigger_sync_for_vendor(mapper, connection, target):
        realtime_sync.queue_sync_event(SyncEvent(
            event_type='database_change',
            entity_type='vendor',
            entity_id=str(target.id),
            action='UPDATE',
            metadata={'vendor_id': target.vendor_id, 'full_name': target.full_name}
        ))
    
    def trigger_sync_for_manager(mapper, connection, target):
        realtime_sync.queue_sync_event(SyncEvent(
            event_type='database_change',
            entity_type='manager',
            entity_id=str(target.id),
            action='UPDATE',
            metadata={'manager_id': target.manager_id, 'full_name': target.full_name}
        ))
    
    # Register event listeners
    event.listen(User, 'after_insert', trigger_sync_for_user)
    event.listen(User, 'after_update', trigger_sync_for_user)
    event.listen(User, 'after_delete', trigger_sync_for_user)
    
    event.listen(Vendor, 'after_insert', trigger_sync_for_vendor)
    event.listen(Vendor, 'after_update', trigger_sync_for_vendor)
    event.listen(Vendor, 'after_delete', trigger_sync_for_vendor)
    
    event.listen(Manager, 'after_insert', trigger_sync_for_manager)
    event.listen(Manager, 'after_update', trigger_sync_for_manager)
    event.listen(Manager, 'after_delete', trigger_sync_for_manager)
    
    logger.info("Database change hooks registered for real-time sync")

if __name__ == "__main__":
    # Example usage
    print("Real-time Notification Sync System")
    print("This module should be imported and initialized with your Flask app")
    print("Example:")
    print("  from realtime_notification_sync import setup_realtime_sync")
    print("  realtime_sync = setup_realtime_sync(app, sync_manager)")
