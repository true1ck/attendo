#!/usr/bin/env python3
"""
Power Automate Scheduler
Runs every 10 minutes to process notification queue for Power Automate.
"""

import time
import schedule
import logging
from pathlib import Path
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scripts.unified_notification_processor import UnifiedNotificationProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PowerAutomateScheduler:
    """
    Scheduler that runs notification processing every 10 minutes.
    """
    
    def __init__(self, network_folder='G:/Test', output_folder='network_folder_simplified'):
        self.processor = UnifiedNotificationProcessor(network_folder, output_folder)
        self.run_count = 0
        self.start_time = datetime.now()
        
        # Log file for scheduler
        self.log_file = Path(output_folder) / 'scheduler.log'
        
    def process_notifications_job(self):
        """Job to process notifications."""
        self.run_count += 1
        logger.info(f"🔄 Run #{self.run_count} - Processing notifications...")
        
        try:
            # Process notifications
            count = self.processor.process_notifications()
            
            # Log success
            self.log_run(True, count)
            logger.info(f"✅ Successfully processed {count} notifications")
            
            return count
            
        except Exception as e:
            # Log error
            self.log_run(False, 0, str(e))
            logger.error(f"❌ Error processing notifications: {e}")
            return 0
    
    def log_run(self, success, count, error=None):
        """Log scheduler run to file."""
        with open(self.log_file, 'a') as f:
            timestamp = datetime.now().isoformat()
            if success:
                f.write(f"{timestamp} | Run #{self.run_count} | SUCCESS | {count} notifications\n")
            else:
                f.write(f"{timestamp} | Run #{self.run_count} | ERROR | {error}\n")
    
    def cleanup_sent_notifications(self):
        """Cleanup job to remove sent notifications."""
        logger.info("🧹 Cleaning up sent notifications...")
        try:
            removed = self.processor.remove_sent_notifications()
            logger.info(f"✅ Removed {removed} sent notifications")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    def status_report(self):
        """Print status report."""
        runtime = (datetime.now() - self.start_time).total_seconds() / 60
        logger.info(f"""
        📊 Scheduler Status Report:
        - Running for: {runtime:.1f} minutes
        - Total runs: {self.run_count}
        - Next run: In 10 minutes
        - Queue file: {self.processor.queue_file}
        """)
    
    def run_scheduler(self):
        """Main scheduler loop."""
        logger.info("🚀 Starting Power Automate Scheduler")
        logger.info(f"📁 Network folder: {self.processor.network_folder}")
        logger.info(f"📁 Output folder: {self.processor.output_folder}")
        logger.info("⏰ Schedule: Every 10 minutes")
        
        # Initial run
        self.process_notifications_job()
        
        # Schedule jobs
        schedule.every(10).minutes.do(self.process_notifications_job)
        schedule.every(5).minutes.do(self.cleanup_sent_notifications)
        schedule.every(30).minutes.do(self.status_report)
        
        # Run scheduler
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("⏹️ Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                time.sleep(60)  # Wait before retry

def run_once():
    """Run the processor once (for testing)."""
    processor = UnifiedNotificationProcessor()
    count = processor.process_notifications()
    
    print(f"\n✅ Processed {count} notifications")
    print(f"📁 Output file: {processor.queue_file}")
    
    return count


"""
Power Automate Scheduler
Helper script that runs every 10 minutes to update sent_noti_now.xlsx
Can be called directly by Power Automate flow or as a scheduled task.

This script ensures that:
1. sent_noti_now.xlsx is always current with notifications due RIGHT NOW
2. Power Automate always has fresh data to process
3. Only one instance runs at a time to avoid conflicts
4. Logging and error handling for production use
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
import filelock
from filelock import FileLock

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from unified_notification_processor import run_notification_processing, unified_processor
except ImportError:
    print("❌ Error: Could not import unified_notification_processor")
    print("   Make sure unified_notification_processor.py is in the same directory")
    sys.exit(1)

# Setup logging for production use
log_file = current_dir / "power_automate_scheduler.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PowerAutomateScheduler:
    """Handles scheduled execution for Power Automate integration"""
    
    def __init__(self):
        self.lock_file = current_dir / "scheduler.lock"
        self.status_file = current_dir / "network_folder_simplified" / "scheduler_status.json"
        self.network_folder = current_dir / "network_folder_simplified"
        self.network_folder.mkdir(exist_ok=True)
        
        # Ensure status file directory exists
        self.status_file.parent.mkdir(exist_ok=True)
    
    def save_status(self, status: str, notifications_count: int = 0, error_message: str = None):
        """Save current execution status for monitoring"""
        status_data = {
            'last_run': datetime.now().isoformat(),
            'status': status,
            'notifications_generated': notifications_count,
            'output_file': str(unified_processor.output_file),
            'next_run_expected': (datetime.now() + timedelta(minutes=10)).isoformat(),
            'error': error_message,
            'scheduler_version': '1.0'
        }
        
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save status: {str(e)}")
    
    def load_last_status(self) -> Dict[str, Any]:
        """Load last execution status"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load last status: {str(e)}")
        
        return {}
    
    def should_run_now(self) -> bool:
        """Check if we should run based on last execution time"""
        last_status = self.load_last_status()
        
        if not last_status.get('last_run'):
            return True
        
        try:
            last_run = datetime.fromisoformat(last_status['last_run'].replace('Z', '+00:00'))
            now = datetime.now()
            
            # Run if more than 8 minutes have passed (allowing for some scheduling variance)
            time_diff = (now - last_run.replace(tzinfo=None)).total_seconds() / 60
            return time_diff >= 8
            
        except Exception as e:
            logger.warning(f"Error checking last run time: {str(e)}")
            return True
    
    def run_single_execution(self) -> Dict[str, Any]:
        """Run a single execution cycle"""
        logger.info("🚀 Starting Power Automate scheduler execution")
        
        start_time = datetime.now()
        
        try:
            # Check if we should run
            if not self.should_run_now():
                logger.info("⏭️ Skipping execution - too soon since last run")
                return {
                    'status': 'skipped',
                    'reason': 'too_soon',
                    'notifications_count': 0
                }
            
            # Use file lock to prevent multiple instances
            with FileLock(self.lock_file, timeout=5):
                logger.info("🔒 Acquired lock - processing notifications...")
                
                # Run the notification processing
                notifications_count = run_notification_processing()
                
                # Save success status
                self.save_status('success', notifications_count)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"✅ Execution completed successfully")
                logger.info(f"   📊 Notifications generated: {notifications_count}")
                logger.info(f"   ⏱️ Execution time: {execution_time:.2f} seconds")
                logger.info(f"   📄 Output file: {unified_processor.output_file}")
                
                return {
                    'status': 'success',
                    'notifications_count': notifications_count,
                    'execution_time': execution_time,
                    'output_file': str(unified_processor.output_file)
                }
                
        except filelock.Timeout:
            error_msg = "Another instance is already running"
            logger.warning(f"⚠️ {error_msg}")
            self.save_status('skipped', 0, error_msg)
            return {
                'status': 'skipped',
                'reason': 'already_running',
                'notifications_count': 0
            }
            
        except Exception as e:
            error_msg = f"Execution failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.save_status('error', 0, error_msg)
            return {
                'status': 'error',
                'error': error_msg,
                'notifications_count': 0
            }
    
    def run_continuous_mode(self, duration_minutes: int = 60):
        """Run in continuous mode for testing (not for production)"""
        logger.info(f"🔄 Starting continuous mode for {duration_minutes} minutes")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        execution_count = 0
        
        while datetime.now() < end_time:
            execution_count += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 EXECUTION #{execution_count}")
            logger.info(f"{'='*60}")
            
            result = self.run_single_execution()
            
            if result['status'] == 'success':
                logger.info(f"✅ Execution #{execution_count} completed successfully")
            elif result['status'] == 'skipped':
                logger.info(f"⏭️ Execution #{execution_count} skipped: {result.get('reason', 'unknown')}")
            else:
                logger.error(f"❌ Execution #{execution_count} failed: {result.get('error', 'unknown')}")
            
            # Wait 10 minutes before next execution
            logger.info("⏰ Waiting 10 minutes until next execution...")
            time.sleep(600)  # 600 seconds = 10 minutes
        
        logger.info(f"🏁 Continuous mode completed after {execution_count} executions")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current status summary for monitoring"""
        last_status = self.load_last_status()
        
        return {
            'scheduler_running': self.lock_file.exists(),
            'last_run': last_status.get('last_run'),
            'last_status': last_status.get('status'),
            'notifications_in_last_run': last_status.get('notifications_generated', 0),
            'output_file_exists': unified_processor.output_file.exists(),
            'next_run_expected': last_status.get('next_run_expected'),
            'current_time': datetime.now().isoformat()
        }

# Global instance
scheduler = PowerAutomateScheduler()

def run_power_automate_cycle():
    """Public function for Power Automate to call"""
    return scheduler.run_single_execution()

def get_scheduler_status():
    """Public function to get scheduler status"""
    return scheduler.get_status_summary()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Power Automate Scheduler')
    parser.add_argument('--mode', choices=['single', 'continuous', 'status'], 
                       default='single', help='Execution mode')
    parser.add_argument('--duration', type=int, default=60, 
                       help='Duration for continuous mode (minutes)')
    parser.add_argument('--force', action='store_true', 
                       help='Force execution even if recently run')
    
    args = parser.parse_args()
    
    if args.mode == 'single':
        print("🚀 POWER AUTOMATE SCHEDULER - Single Execution Mode")
        print("="*60)
        
        if args.force:
            # Temporarily modify should_run_now to always return True
            original_should_run = scheduler.should_run_now
            scheduler.should_run_now = lambda: True
        
        result = scheduler.run_single_execution()
        
        if args.force:
            scheduler.should_run_now = original_should_run
        
        print("\n📊 EXECUTION SUMMARY:")
        print(f"   Status: {result['status']}")
        print(f"   Notifications: {result['notifications_count']}")
        if 'execution_time' in result:
            print(f"   Execution Time: {result['execution_time']:.2f} seconds")
        if 'output_file' in result:
            print(f"   Output File: {result['output_file']}")
        if 'error' in result:
            print(f"   Error: {result['error']}")
        
        # Exit code for automation
        sys.exit(0 if result['status'] in ['success', 'skipped'] else 1)
        
    elif args.mode == 'continuous':
        print(f"🔄 POWER AUTOMATE SCHEDULER - Continuous Mode ({args.duration} minutes)")
        print("="*60)
        print("⚠️  WARNING: This mode is for testing only!")
        print("   In production, use task scheduler or cron to call with --mode single")
        print("="*60)
        
        try:
            scheduler.run_continuous_mode(args.duration)
        except KeyboardInterrupt:
            print("\n⏹️ Continuous mode interrupted by user")
            sys.exit(0)
            
    elif args.mode == 'status':
        print("📊 POWER AUTOMATE SCHEDULER - Status Check")
        print("="*60)
        
        status = scheduler.get_status_summary()
        
        for key, value in status.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        
        sys.exit(0)

if __name__ == "__main__":
    main()
