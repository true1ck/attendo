# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**ATTENDO** is a comprehensive workforce management platform that streamlines attendance tracking, vendor management, and analytics for enterprises. Built as a Flask-based web application with role-based access control (Admin/Manager/Vendor), it features Excel-based notification systems, Power Automate integration, real-time dashboards, attendance reconciliation, and configurable automation.

## Common Development Commands

### Application Setup & Running
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application (development)
python app.py

# Access the application
# Web Interface: http://localhost:5000
# API Documentation: http://localhost:5000/api/docs
# Import Dashboard: http://localhost:5000/import/
```

### Development Utilities
```bash
# View database contents for debugging
python scripts/view_database.py

# Create Excel notification configurations
python scripts/create_notification_configs.py

# Migrate database schema
python scripts/migrate_database.py

# Create Power Automate tables
python scripts/create_power_automate_tables.py

# Set up real-time notification sync system
python scripts/setup_realtime_notification_sync.py

# Generate sample Excel attendance data
python scripts/create_sample_attendance_excel.py
```

### Data Import & Testing
```bash
# Test with pre-built Test_DATA folder (recommended workflow)
# 1) Start the app: python app.py
# 2) Open Import Dashboard: http://localhost:5000/import/
# 3) Import files from Test_DATA/ folder:
#    - Import Swipe Data → Test_DATA/swipe_data.csv
#    - Import Leave Data → Test_DATA/leave_data.csv
#    - Import WFH Data → Test_DATA/wfh_data.csv
# 4) Validate: Click "Validate Imported Data"
# 5) Reconcile: Go to /admin/reconciliation and click "Run Reconciliation"

# Import attendance data programmatically
python scripts/import_attendance_excel.py

# Create test status submissions
python create_test_status.py
```

### Database Operations
```bash
# The application automatically creates and initializes the database on first run
# Database file: vendor_timesheet.db (SQLite)
# Demo data is loaded automatically for testing

# Run database migrations if schema changes
python scripts/migrate_database.py
```

### Test Credentials
- **Admin**: `admin` / `admin123`
- **Manager**: `manager1` / `manager123`  
- **Vendor**: `vendor1` / `vendor123`

## Architecture Overview

### Core Application Structure
The application follows a single-file Flask architecture with key components:

- **app.py**: Main application entry point containing all routes, authentication, and business logic
- **models.py**: Database schema with SQLAlchemy ORM models and enum definitions
- **utils.py**: Utility functions for data processing, reports, and AI predictions
- **import_routes.py**: Blueprint for data import functionality (admin-only)
- **notification_service.py**: Modern notification service with Excel-based configurations
- **swagger_ui.py**: API documentation configuration

### Excel-Based Notification System
The platform features a comprehensive Excel-based notification system that replaces hard-coded logic:

**Configuration Files** (in `notification_configs/`):
- `01_daily_status_reminders.xlsx` - Vendor reminder configurations
- `02_manager_summary_notifications.xlsx` - Manager summary notifications
- `03_manager_all_complete_notifications.xlsx` - Team completion alerts
- `04_mismatch_notifications.xlsx` - Data reconciliation alerts
- `05_manager_feedback_notifications.xlsx` - Approval/rejection feedback
- `06_monthly_report_notifications.xlsx` - Report delivery settings
- `07_admin_system_alerts.xlsx` - System health alerts
- `08_holiday_reminder_notifications.xlsx` - Holiday notifications
- `09_late_submission_alerts.xlsx` - Late submission tracking
- `10_billing_correction_notifications.xlsx` - Billing adjustment alerts

**Key Components**:
- **ExcelNotificationManager** (`scripts/excel_notification_manager.py`): Core engine for Excel-based notifications
- **Power Automate API** (`scripts/power_automate_api.py`): REST API for Microsoft Power Automate integration
- **Real-time Sync System** (`scripts/setup_realtime_notification_sync.py`): Automated synchronization with external systems

### Database Architecture
The system uses SQLAlchemy with enum-based status management:

**Core Entities:**
- **User**: Authentication and role management (Admin/Manager/Vendor)
- **Vendor**: Employee profiles with department/company information
- **Manager**: Team management with vendor assignments
- **DailyStatus**: Daily attendance submissions with approval workflow

**Operational Data:**
- **SwipeRecord**: Physical attendance data from swipe machines
- **MismatchRecord**: Reconciliation between web status and swipe data
- **LeaveRecord/WFHRecord**: Approved leave and work-from-home records
- **Holiday**: System-wide holiday configuration

**System Tracking:**
- **AuditLog**: Complete audit trail for all actions
- **NotificationLog**: Notification delivery tracking
- **SystemConfiguration**: Configurable system settings

### Key Design Patterns

**Role-Based Access Control:**
- Three distinct user roles with separate dashboards and permissions
- Decorators for route-level access control
- Manager-vendor assignment for approval workflows

**Status Workflow:**
1. Vendor submits daily status (pending)
2. Manager reviews and approves/rejects
3. System reconciles with swipe data
4. Mismatches flagged for resolution

**Import & Reconciliation:**
- Excel/CSV import for swipe data, leave records, WFH approvals
- Automatic mismatch detection between web submissions and physical data
- Admin-controlled reconciliation process

### Power Automate Integration Architecture

**API Endpoints** (available at `/api/power-automate/`):
- `POST /daily-reset` - Trigger daily Excel refresh for Power Automate flows
- `POST /vendor-status-update` - Handle real-time vendor status updates
- `GET /pending-vendors` - Get list of vendors pending submission
- `GET /manager-summary` - Get manager team summary data

**Excel Workflow Integration:**
1. **Daily Reset Flow**: Power Automate triggers daily Excel table updates
2. **Real-time Updates**: Vendor status changes immediately update Excel sheets
3. **Manager Notifications**: Teams/Email notifications based on Excel configurations
4. **Sync Monitoring**: Automated monitoring and alerting for sync failures

**Configuration Management:**
- Business users modify notification settings directly in Excel files
- No code deployment required for notification rule changes
- Granular control over timing, recipients, and message templates
- Multi-channel support (Email, Teams, SMS)

## Development Guidelines

### Excel Configuration System
The platform uses Excel files for business-user configurable notifications and workflows:

**Excel Table Structure** (consistent across all notification config files):
- **Primary_Key**: Unique identifier for each configuration
- **Contact_Email/Contact_Name**: Notification recipients
- **Send_Notification**: YES/NO toggle for enabling notifications
- **Active**: YES/NO status control
- **Notification_Method**: TEAMS,EMAIL,SMS (comma-separated)
- **Priority**: LOW/MEDIUM/HIGH/CRITICAL
- **Custom_Message**: Template for notification content
- **Timing Controls**: Start_Time, End_Time, Weekdays, Holiday_Handling
- **Audit Fields**: Created_Date, Modified_Date, Last_Triggered

**Working with Excel Configurations**:
```python
# Load Excel configurations
from scripts.excel_notification_manager import ExcelNotificationManager
notification_manager = ExcelNotificationManager()

# Get active recipients for a notification type
recipients = notification_manager.get_active_recipients('daily_reminders', 
    filters={'Priority': ['HIGH', 'CRITICAL']})

# Send notifications using Excel configuration
notification_manager.send_daily_status_reminders()
```

### Database Schema Considerations
- All status enums are defined in `models.py` (AttendanceStatus, ApprovalStatus, UserRole)
- Foreign key relationships use string IDs for vendor/manager mapping
- Audit logging is automatically handled via `create_audit_log()` utility

### API Design Patterns
- Session-based authentication using Flask-Login
- Form-based submissions for web interface
- JSON APIs for dashboard data and charts
- Swagger documentation available at `/api/docs`

### Background Jobs & Scheduling
- APScheduler for notification automation
- Configurable reminder intervals and notification types
- System health checks and mismatch detection

### File Upload & Processing
- Secure file handling in `import_routes.py`
- Pandas for Excel/CSV processing
- Automatic cleanup after import processing

### AI/ML Integration
The system includes a heuristic-based "AI" prediction system in `utils.py`:
- Absence risk prediction based on historical patterns
- Day-of-week pattern analysis
- Risk categorization (Low/Medium/High/Critical)
- Configurable prediction windows

### Environment Configuration
- `.env.example` provided for environment setup
- Database URL configurable via environment variables
- SMTP and notification settings externalized

## Important Implementation Details

### Circular Import Prevention
The application uses deferred imports within functions to prevent circular dependencies between `app.py`, `models.py`, and `utils.py`.

### Data Validation & Error Handling
- Comprehensive form validation with user-friendly error messages
- Database rollback on errors with proper exception handling
- Audit logging for all significant actions

### Security Considerations
- Password hashing using Werkzeug security functions
- Secure filename handling for uploads
- SQL injection protection via SQLAlchemy ORM
- Session-based authentication with login required decorators

### Testing & Demo Data
- **Test_DATA/** directory contains pre-built CSV files for import testing:
  - `swipe_data.csv` - Physical attendance machine data
  - `leave_data.csv` - Approved leave records
  - `wfh_data.csv` - Work-from-home approvals
- **Demo data** is automatically created on first app startup
- **Create test scenarios** using `create_test_status.py` for specific testing needs
- **notification_configs/** contains 10 Excel files with sample notification configurations

### Scripts Directory Architecture
The `scripts/` directory contains utility and automation scripts:

**Database & Data Management**:
- `migrate_database.py` - Handle schema migrations
- `view_database.py` - Debug database contents
- `import_attendance_excel.py` - Programmatic data import

**Excel & Notification System**:
- `excel_notification_manager.py` - Core notification engine
- `create_notification_configs.py` - Initialize Excel config files
- `excel_table_formatter.py` - Format Excel files as proper tables
- `daily_excel_updater.py` - Real-time Excel updates

**Power Automate & Integration**:
- `power_automate_api.py` - REST API for Microsoft Power Automate
- `setup_realtime_notification_sync.py` - Configure real-time synchronization
- `notification_sync_monitor.py` - Monitor sync health

### Performance Considerations
- Database indexes on frequently queried fields (vendor_id, status_date)
- Lazy loading for relationships to prevent N+1 queries
- Efficient date range queries for reports and analytics
- Excel configurations cached in memory for performance
- Background job scheduling with APScheduler for notifications

### Key File Locations
- **Main app**: `app.py` (single-file Flask application)
- **Database**: `vendor_timesheet.db` (SQLite, created automatically)
- **Excel configs**: `notification_configs/*.xlsx` (business-user editable)
- **Documentation**: `docs/` (includes API docs, guides, presentations)
- **API Documentation**: Available at `/api/docs` when app is running

This workforce management system is designed for enterprise use with focus on Excel-based configuration, Power Automate integration, compliance, auditability, and ease of use across different user roles.
