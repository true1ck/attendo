#!/usr/bin/env python3
"""
Power Automate API Integration
Provides REST API endpoints for Power Automate to interact with the daily Excel updater system.
"""

from flask import Flask, Blueprint, request, jsonify
from datetime import datetime, date
import logging
from typing import Dict, List, Any
# Import from scripts directory since we're in scripts/
try:
    from scripts.daily_excel_updater import daily_excel_updater, run_daily_reset, handle_vendor_status_submission
except ImportError:
    try:
        from daily_excel_updater import daily_excel_updater, run_daily_reset, handle_vendor_status_submission
    except ImportError:
        # If running from main app, these might not be needed
        daily_excel_updater = None
        run_daily_reset = None
        handle_vendor_status_submission = None

# Import models from parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import User, Vendor, Manager, DailyStatus, UserRole, AttendanceStatus, ApprovalStatus
import models

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for Power Automate APIs
power_automate_bp = Blueprint('power_automate', __name__, url_prefix='/api/power-automate')

@power_automate_bp.route('/daily-reset', methods=['POST'])
def trigger_daily_reset():
    """Trigger daily Excel reset manually or via Power Automate"""
    try:
        data = request.get_json() or {}
        force_reset = data.get('force', False)
        
        # Check if already reset today (unless forced)
        if not force_reset and daily_excel_updater:
            context = daily_excel_updater.daily_context_file
            if context.exists():
                import json
                with open(context) as f:
                    last_context = json.load(f)
                    last_reset_date = last_context.get('last_reset_date')
                    if last_reset_date == date.today().isoformat():
                        return jsonify({
                            'status': 'skipped',
                            'message': 'Already reset today',
                            'last_reset': last_reset_date
                        })
        
        # Run the Power Automate compatible refresh
        try:
            from scripts.power_automate_excel_refresh import power_automate_excel_refresh
            success = power_automate_excel_refresh()
        except Exception as e:
            logger.error(f"Power Automate Excel refresh failed: {str(e)}")
            # Fallback to original method
            if run_daily_reset:
                success = run_daily_reset()
            else:
                success = False
                logger.error("No refresh functions available")
        
        # Get pending count after reset
        pending_count = 0
        if success:
            try:
                # Get pending count directly from database
                import sqlite3
                from datetime import date
                
                db_conn = sqlite3.connect('vendor_timesheet.db')
                today = date.today().isoformat()
                
                cursor = db_conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM vendors v
                    JOIN users u ON v.user_id = u.id
                    LEFT JOIN daily_statuses ds ON v.id = ds.vendor_id AND ds.status_date = ?
                    WHERE u.is_active = 1 AND ds.id IS NULL
                """, [today])
                
                pending_count = cursor.fetchone()[0]
                db_conn.close()
                
            except Exception as e:
                logger.error(f"Error getting pending count: {str(e)}")
                pending_count = 0
        
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'Daily reset completed' if success else 'Daily reset failed',
            'timestamp': datetime.now().isoformat(),
            'date': date.today().isoformat(),
            'pending_count': pending_count
        })
        
    except Exception as e:
        logger.error(f"API daily reset error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@power_automate_bp.route('/vendor-status-update', methods=['POST'])
def handle_vendor_status_update():
    """Handle real-time vendor status updates for Excel sheets"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        vendor_id = data.get('vendor_id')
        status = data.get('status', 'SUBMITTED')
        
        if not vendor_id:
            return jsonify({'error': 'vendor_id is required'}), 400
        
        # Update Excel sheets
        if handle_vendor_status_submission:
            handle_vendor_status_submission(vendor_id)
        else:
            logger.warning("handle_vendor_status_submission function not available")
        
        return jsonify({
            'status': 'success',
            'message': f'Excel sheets updated for vendor {vendor_id}',
            'vendor_id': vendor_id,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Vendor status update error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@power_automate_bp.route('/pending-vendors', methods=['GET'])
def get_pending_vendors():
    """Get list of vendors pending attendance submission for Power Automate"""
    try:
        from utils import check_late_submissions
        
        late_vendors = check_late_submissions()
        today_str = date.today().isoformat()
        
        vendor_list = []
        for vendor in late_vendors:
            vendor_data = {
                'vendor_id': vendor.vendor_id,
                'full_name': vendor.full_name,
                'email': vendor.user_account.email if vendor.user_account else '',
                'department': vendor.department,
                'company': vendor.company,
                'manager_id': vendor.manager_id,
                'date': today_str,
                'status': 'PENDING_SUBMISSION'
            }
            vendor_list.append(vendor_data)
        
        return jsonify({
            'status': 'success',
            'date': today_str,
            'pending_count': len(vendor_list),
            'vendors': vendor_list,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get pending vendors error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@power_automate_bp.route('/manager-summary', methods=['GET'])
def get_manager_summary():
    """Get manager team summary data for Power Automate"""
    try:
        manager_id = request.args.get('manager_id')
        today = date.today()
        
        if manager_id:
            # Get specific manager data
            managers = [Manager.query.filter_by(manager_id=manager_id).first()]
            managers = [m for m in managers if m is not None]
        else:
            # Get all managers
            managers = Manager.query.all()
        
        manager_summaries = []
        
        for manager in managers:
            if not manager.team_vendors:
                continue
                
            team_vendors = manager.team_vendors.all()
            total_team = len(team_vendors)
            submitted_count = 0
            pending_approvals = 0
            
            # Calculate team statistics
            for vendor in team_vendors:
                status = DailyStatus.query.filter_by(
                    vendor_id=vendor.id,
                    status_date=today
                ).first()
                
                if status:
                    submitted_count += 1
                    if status.approval_status == ApprovalStatus.PENDING:
                        pending_approvals += 1
            
            pending_submissions = total_team - submitted_count
            completion_rate = round((submitted_count / total_team) * 100, 1) if total_team > 0 else 0
            
            summary = {
                'manager_id': manager.manager_id,
                'manager_name': manager.full_name,
                'department': manager.department,
                'team_name': manager.team_name,
                'email': manager.email,
                'date': today.isoformat(),
                'team_size': total_team,
                'submitted_count': submitted_count,
                'pending_submissions': pending_submissions,
                'pending_approvals': pending_approvals,
                'completion_rate': completion_rate,
                'requires_attention': pending_submissions > 0,
                'alert_level': 'HIGH' if completion_rate < 50 else 'MEDIUM' if completion_rate < 80 else 'LOW'
            }
            
            manager_summaries.append(summary)
        
        return jsonify({
            'status': 'success',
            'date': today.isoformat(),
            'manager_count': len(manager_summaries),
            'summaries': manager_summaries,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get manager summary error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@power_automate_bp.route('/excel-status', methods=['GET'])
def get_excel_status():
    """Get status of Excel files and last update times"""
    try:
        import os
        import json
        from pathlib import Path
        
        excel_folder = Path('notification_configs')
        files_status = {}
        
        # Check each notification file
        if daily_excel_updater:
            files_to_check = daily_excel_updater.notification_files.items()
        else:
            # Fallback file list if daily_excel_updater is not available
            files_to_check = {
                'daily_reminders': '01_daily_status_reminders.xlsx',
                'manager_summary': '02_manager_summary_notifications.xlsx',
                'late_submissions': '09_late_submission_alerts.xlsx'
            }.items()
            
        for file_type, filename in files_to_check:
            filepath = excel_folder / filename
            
            if filepath.exists():
                stat = filepath.stat()
                files_status[file_type] = {
                    'filename': filename,
                    'exists': True,
                    'size_bytes': stat.st_size,
                    'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'readable': os.access(filepath, os.R_OK),
                    'writable': os.access(filepath, os.W_OK)
                }
            else:
                files_status[file_type] = {
                    'filename': filename,
                    'exists': False,
                    'error': 'File not found'
                }
        
        # Get daily context if available
        context_data = {}
        if daily_excel_updater and daily_excel_updater.daily_context_file.exists():
            try:
                with open(daily_excel_updater.daily_context_file) as f:
                    context_data = json.load(f)
            except Exception as e:
                context_data = {'error': f'Could not read context: {str(e)}'}
        
        return jsonify({
            'status': 'success',
            'files': files_status,
            'daily_context': context_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get Excel status error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@power_automate_bp.route('/webhook/configure', methods=['POST'])
def configure_webhooks():
    """Configure Power Automate webhook URLs"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        webhook_config = {}
        
        # Extract webhook URLs from request
        if 'daily_refresh' in data:
            webhook_config['daily_refresh'] = data['daily_refresh']
        if 'vendor_status_change' in data:
            webhook_config['vendor_status_change'] = data['vendor_status_change']
        if 'emergency_alert' in data:
            webhook_config['emergency_alert'] = data['emergency_alert']
        
        if webhook_config:
            if daily_excel_updater:
                daily_excel_updater.configure_power_automate_webhooks(webhook_config)
            else:
                logger.warning("daily_excel_updater not available for webhook configuration")
            
            return jsonify({
                'status': 'success',
                'message': f'Configured {len(webhook_config)} webhook URLs',
                'configured': list(webhook_config.keys()),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No valid webhook URLs provided'
            }), 400
            
    except Exception as e:
        logger.error(f"Configure webhooks error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@power_automate_bp.route('/health-check', methods=['GET'])
def health_check():
    """Health check endpoint for Power Automate monitoring"""
    try:
        # Check database connectivity
        db_healthy = True
        try:
            with models.db.session() as session:
                session.execute('SELECT 1').fetchone()
        except Exception:
            db_healthy = False
        
        # Check Excel files accessibility
        excel_healthy = daily_excel_updater and len(daily_excel_updater.validate_excel_sheets()) > 0
        
        # Check if daily reset is current
        reset_current = False
        if daily_excel_updater and daily_excel_updater.daily_context_file.exists():
            try:
                import json
                with open(daily_excel_updater.daily_context_file) as f:
                    context = json.load(f)
                    last_reset = context.get('last_reset_date')
                    reset_current = last_reset == date.today().isoformat()
            except Exception:
                pass
        
        overall_healthy = db_healthy and excel_healthy
        
        return jsonify({
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'database': 'ok' if db_healthy else 'error',
            'excel_files': 'ok' if excel_healthy else 'error',
            'daily_reset': 'current' if reset_current else 'stale',
            'timestamp': datetime.now().isoformat(),
            'date': date.today().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@power_automate_bp.route('/test-notification', methods=['POST'])
def test_notification():
    """Test notification system for Power Automate validation"""
    try:
        data = request.get_json() or {}
        notification_type = data.get('type', 'test')
        
        # Simulate different notification scenarios
        if notification_type == 'daily_reset':
            # Test daily reset
            if run_daily_reset:
                success = run_daily_reset()
                return jsonify({
                    'status': 'success' if success else 'failed',
                    'message': f'Daily reset test: {"passed" if success else "failed"}',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'status': 'failed',
                    'message': 'Daily reset function not available',
                    'timestamp': datetime.now().isoformat()
                })
            
        elif notification_type == 'vendor_update':
            # Test vendor status update
            test_vendor_id = data.get('vendor_id', 'TEST001')
            if handle_vendor_status_submission:
                handle_vendor_status_submission(test_vendor_id)
                return jsonify({
                    'status': 'success',
                    'message': f'Vendor update test passed for {test_vendor_id}',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'status': 'failed',
                    'message': 'Vendor status submission function not available',
                    'timestamp': datetime.now().isoformat()
                })
            
        else:
            return jsonify({
                'status': 'success',
                'message': 'Test notification system is operational',
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Test notification error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def register_power_automate_api(app: Flask):
    """Register Power Automate API blueprint with Flask app"""
    app.register_blueprint(power_automate_bp)
    logger.info("🔗 Power Automate API endpoints registered")
    
    return power_automate_bp
