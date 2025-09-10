# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**ATTENDO** is a comprehensive workforce management platform that streamlines attendance tracking, vendor management, and analytics for enterprises. Built as a Flask-based web application with role-based access control (Admin/Manager/Vendor), it features Excel-based notification systems, Power Automate integration, real-time dashboards, attendance reconciliation, and configurable automation.

Key Technologies: **Python 3.8+**, **Flask 3.0**, **SQLAlchemy 2.0**, **SQLite** (development), **Bootstrap 5**, **Chart.js**, **APScheduler**, **pandas/openpyxl**

## Common Development Commands

### Application Setup & Running
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application (development mode)
python app.py

# Access key interfaces:
# Web Interface: http://localhost:5000
# API Documentation: http://localhost:5000/api/docs
# Import Dashboard: http://localhost:5000/import/
# Holiday Calendar: http://localhost:5000/holiday-calendar

# Production deployment with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Environment Configuration
```bash
# Copy environment template and configure
cp .env.example .env

# Key environment variables to set:
# SECRET_KEY=your-secret-key-here
# DATABASE_URL=sqlite:///vendor_timesheet.db
# SMTP_SERVER=smtp.gmail.com
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
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

### Debugging & Troubleshooting
```bash
# View database contents for debugging
python scripts/view_database.py

# Check notification logs and system health
python scripts/notification_sync_monitor.py

# Manual database migration (if schema changes)
python scripts/migrate_database.py

# Check real-time sync status
python scripts/notification_database_sync.py

# Format Excel tables properly
python scripts/excel_table_formatter.py
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

### Testing & Validation
```bash
# API Testing via Swagger UI
# 1. Start app: python app.py
# 2. Navigate to: http://localhost:5000/api/docs
# 3. Use test credentials provided in the UI

# Manual testing workflow for core features:
# 1. Login as vendor1/vendor123 → Submit daily status
# 2. Login as manager1/manager123 → Review and approve
# 3. Login as admin/admin123 → Run reconciliation, view reports

# Test notification system (requires SMTP configuration)
# Set SMTP_USER and SMTP_PASSWORD in environment
# Notifications trigger automatically based on schedule

# Test Excel notification configurations
python scripts/excel_notification_manager.py
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

- **app.py**: Main application entry point containing all routes, authentication, and business logic (400+ lines)
- **models.py**: Database schema with SQLAlchemy ORM models and enum definitions (12 tables, enum-based status management)
- **utils.py**: Utility functions for data processing, reports, AI predictions (mismatch detection, Excel import/export)
- **import_routes.py**: Blueprint for data import functionality (admin-only, supports vendor/manager bulk import)
- **notification_service.py**: Modern notification service with Excel-based configurations and SMTP/SMS support
- **swagger_ui.py**: API documentation configuration with custom UI and test data endpoints

**Critical Implementation Note**: The app uses deferred imports within functions to prevent circular dependencies between `app.py`, `models.py`, and `utils.py`. This pattern is essential when modifying import statements.

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
- **SwipeRecord**: Physical attendance data from swipe machines (indexed by vendor/date)
- **MismatchRecord**: Reconciliation between web status and swipe data (auto-generated by utils.detect_mismatches)
- **LeaveRecord/WFHRecord**: Approved leave and work-from-home records expanded to date ranges
- **Holiday**: System-wide holiday configuration (unique per date)

**System Tracking:**
- **AuditLog**: Complete audit trail for all actions (auto-created in utils.create_audit_log)
- **NotificationLog**: Notification delivery tracking for in-app/Teams messages
- **EmailNotificationLog**: Email/SMS delivery tracking managed by notification_service
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

### Critical Development Patterns

**Single-File Flask Pattern**:
- All routes, authentication, and business logic are in `app.py` to avoid circular imports
- Use deferred imports within functions: `from models import User` inside route functions
- Database operations use `models.db.session` to avoid import conflicts

**Status Enum Handling**:
- All status types defined as enums in `models.py` (UserRole, AttendanceStatus, ApprovalStatus)
- Use enum values in database queries: `DailyStatus.query.filter_by(approval_status=ApprovalStatus.PENDING)`
- Convert to display strings: `status.status.value.replace('_', ' ').title()`

**Error Handling & Database Transactions**:
- Always use try/except with `models.db.session.rollback()` on errors
- Create audit logs for all significant actions via `utils.create_audit_log()`
- Flash user-friendly error messages with appropriate categories ('error', 'warning', 'success')

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

## Deployment & Performance Considerations

### Production Deployment
```bash
# Production environment setup
cp .env.example .env
# Configure production database URL, SMTP settings, secret key

# Use Gunicorn for WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 --timeout 120 app:app

# Docker deployment
docker build -t attendo-app .
docker run -p 8000:5000 -v $(pwd)/vendor_timesheet.db:/app/vendor_timesheet.db attendo-app
```

### Performance & Scalability Notes
- Database indexes on vendor_id/status_date for efficient queries
- Excel configurations cached in memory by notification services
- APScheduler handles background job scheduling (notifications, reconciliation)
- Lazy loading on relationships to prevent N+1 queries
- Date range queries optimized for monthly reports
- File upload handling with secure filename processing

### Security Considerations
- Password hashing via Werkzeug security functions
- SQL injection protection through SQLAlchemy ORM
- Session-based authentication with login_required decorators
- Role-based access control enforced at route level
- Secure file upload handling with allowed extensions
- CSRF protection via Flask-WTF (if forms extended)

### Monitoring & Health Checks
- View system health: `python scripts/view_database.py`
- Monitor notification sync: `python scripts/notification_sync_monitor.py`
- Check audit logs via admin dashboard: `/admin/audit-logs`
- API health check: `GET /api/dashboard/stats`

This workforce management system is designed for enterprise use with focus on Excel-based configuration, Power Automate integration, compliance, auditability, and ease of use across different user roles.
