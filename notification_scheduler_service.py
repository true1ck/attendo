"""
Notification Scheduler Service for Flask Integration
Runs the enhanced notification scheduler as a background thread
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import pandas as pd
import shutil
from scripts.enhanced_notification_scheduler import EnhancedNotificationScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationSchedulerService:
    def __init__(self, app=None):
        self.app = app
        self.scheduler = None
        self.thread = None
        self.running = False
        self.paused = False
        self.status = {
            'running': False,
            'paused': False,
            'last_run': None,
            'next_run': None,
            'notifications_queued': 0,
            'notifications_sent': 0,
            'total_processed': 0,
            'errors': [],
            'current_queue_size': 0
        }
        self.interval_minutes = 10
        self._stop_event = threading.Event()
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
    def start(self):
        """Start the notification scheduler in background thread"""
        if self.running:
            return {'success': False, 'message': 'Scheduler already running'}
        
        try:
            # Initialize the scheduler
            self.scheduler = EnhancedNotificationScheduler()
            
            # Ensure network queue file exists
            self._ensure_network_file()
            
            # Start the background thread
            self.running = True
            self.paused = False
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            
            self.status['running'] = True
            self.status['paused'] = False
            self.status['errors'] = []
            
            logger.info("✅ Notification scheduler started successfully")
            return {'success': True, 'message': 'Notification scheduler started'}
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            self.running = False
            self.status['running'] = False
            self.status['errors'].append(str(e))
            return {'success': False, 'message': f'Failed to start: {str(e)}'}
    
    def stop(self):
        """Stop the notification scheduler"""
        if not self.running:
            return {'success': False, 'message': 'Scheduler not running'}
        
        try:
            self.running = False
            self._stop_event.set()
            
            # Wait for thread to finish (max 5 seconds)
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
            
            self.status['running'] = False
            self.status['paused'] = False
            
            logger.info("🛑 Notification scheduler stopped")
            return {'success': True, 'message': 'Notification scheduler stopped'}
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            return {'success': False, 'message': f'Error stopping: {str(e)}'}
    
    def pause(self):
        """Pause the notification scheduler"""
        if not self.running:
            return {'success': False, 'message': 'Scheduler not running'}
        
        self.paused = True
        self.status['paused'] = True
        logger.info("⏸️ Notification scheduler paused")
        return {'success': True, 'message': 'Notification scheduler paused'}
    
    def resume(self):
        """Resume the notification scheduler"""
        if not self.running:
            return {'success': False, 'message': 'Scheduler not running'}
        
        self.paused = False
        self.status['paused'] = False
        logger.info("▶️ Notification scheduler resumed")
        return {'success': True, 'message': 'Notification scheduler resumed'}
    
    def force_sync(self):
        """Force an immediate sync"""
        if not self.running:
            return {'success': False, 'message': 'Scheduler not running'}
        
        try:
            if self.scheduler:
                # Run process immediately
                self.scheduler.process_notifications()
                
                # Update status
                self._update_status()
                
                logger.info("🔄 Forced notification sync completed")
                return {'success': True, 'message': 'Notification sync completed'}
        except Exception as e:
            logger.error(f"Error during forced sync: {e}")
            self.status['errors'].append(str(e))
            return {'success': False, 'message': f'Sync error: {str(e)}'}
    
    def get_status(self):
        """Get current scheduler status"""
        # Update queue size
        self._update_queue_status()
        return self.status
    
    def _run_scheduler(self):
        """Main scheduler loop running in background thread"""
        logger.info(f"🚀 Notification scheduler thread started (interval: {self.interval_minutes} minutes)")
        
        while self.running and not self._stop_event.is_set():
            try:
                if not self.paused:
                    # Process notifications
                    self.scheduler.process_notifications()
                    
                    # Update status
                    self._update_status()
                    
                    logger.info(f"✅ Notification processing completed at {datetime.now().strftime('%H:%M:%S')}")
                else:
                    logger.debug("Scheduler paused, skipping processing")
                
                # Calculate next run time
                next_run = datetime.now() + timedelta(minutes=self.interval_minutes)
                self.status['next_run'] = next_run.isoformat()
                
                # Wait for interval or stop signal
                for _ in range(self.interval_minutes * 60):  # Check every second
                    if self._stop_event.is_set() or not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                self.status['errors'].append({
                    'time': datetime.now().isoformat(),
                    'error': str(e)
                })
                # Keep only last 10 errors
                if len(self.status['errors']) > 10:
                    self.status['errors'] = self.status['errors'][-10:]
                
                # Wait a bit before retrying
                time.sleep(60)
        
        logger.info("Notification scheduler thread stopped")
    
    def _update_status(self):
        """Update status after processing"""
        self.status['last_run'] = datetime.now().isoformat()
        self.status['total_processed'] += 1
        
        # Update queue status
        self._update_queue_status()
    
    def _update_queue_status(self):
        """Update current queue size and statistics"""
        try:
            queue_file = Path("network_folder_simplified/sent_noti_now.xlsx")
            if queue_file.exists():
                df = pd.read_excel(queue_file)
                total = len(df)
                
                if 'NTStatusSent' in df.columns:
                    unsent = len(df[df['NTStatusSent'] != True])
                    sent = total - unsent
                else:
                    unsent = total
                    sent = 0
                
                self.status['current_queue_size'] = unsent
                self.status['notifications_queued'] = unsent
                self.status['notifications_sent'] = sent
            else:
                self.status['current_queue_size'] = 0
                self.status['notifications_queued'] = 0
                
        except Exception as e:
            logger.error(f"Error updating queue status: {e}")
    
    def set_interval(self, minutes):
        """Set the scheduler interval in minutes"""
        if minutes < 1 or minutes > 1440:  # Between 1 minute and 24 hours
            return {'success': False, 'message': 'Interval must be between 1 and 1440 minutes'}
        
        self.interval_minutes = minutes
        logger.info(f"Scheduler interval set to {minutes} minutes")
        return {'success': True, 'message': f'Interval set to {minutes} minutes'}
    
    def _ensure_network_file(self):
        """Ensure the network queue file exists"""
        try:
            network_file = Path("G:/Test/sent_noti_now.xlsx")
            network_folder = Path("G:/Test")
            
            # Create network folder if it doesn't exist
            network_folder.mkdir(exist_ok=True, parents=True)
            
            # If network file doesn't exist, create it
            if not network_file.exists():
                logger.info(f"Creating network queue file at {network_file}")
                
                # Create empty DataFrame with required columns
                import pandas as pd
                from openpyxl.worksheet.table import Table, TableStyleInfo
                
                empty_df = pd.DataFrame(columns=[
                    'EmployeeID',
                    'ContactEmail', 
                    'Message',
                    'NotificationType',
                    'Priority',
                    'NTStatusSent'
                ])
                
                # Save with Excel table format
                with pd.ExcelWriter(network_file, engine='openpyxl') as writer:
                    empty_df.to_excel(writer, sheet_name='Notifications', index=False)
                    
                    workbook = writer.book
                    worksheet = writer.sheets['Notifications']
                    
                    # Create empty table structure
                    table_ref = "A1:F1"  # Just headers for empty table
                    table = Table(displayName="NotificationQueue", ref=table_ref)
                    style = TableStyleInfo(
                        name="TableStyleMedium2",
                        showFirstColumn=False,
                        showLastColumn=False,
                        showRowStripes=True,
                        showColumnStripes=False
                    )
                    table.tableStyleInfo = style
                    worksheet.add_table(table)
                
                logger.info(f"✅ Created network queue file: {network_file}")
                return True
            else:
                logger.info(f"Network queue file already exists: {network_file}")
                return True
                
        except Exception as e:
            logger.error(f"Error ensuring network file: {e}")
            return False

# Create global instance
notification_scheduler_service = NotificationSchedulerService()
