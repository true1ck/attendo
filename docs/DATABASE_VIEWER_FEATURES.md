# 🎯 ATTENDO Database Viewer - Comprehensive Features

## Overview
The `view_database.py` script now provides complete access to all 13 tables in your ATTENDO Workforce Management System database with enhanced analytics and reporting capabilities.

## 📊 Database Tables Supported

### Core User Management Tables
1. **users** - Main user authentication table
2. **vendors** - Vendor profile information 
3. **managers** - Manager profile information

### Core Functionality Tables  
4. **daily_statuses** - Main attendance status records
5. **swipe_records** - Physical swipe card data

### System Configuration Tables
6. **holidays** - Holiday calendar
7. **system_configurations** - System settings

### Data Import Tables
8. **leave_records** - External leave data
9. **wfh_records** - External WFH data

### Reconciliation & Audit Tables
10. **mismatch_records** - Attendance discrepancies
11. **audit_logs** - Complete system audit trail

### Notification Tables
12. **notification_logs** - General notifications
13. **email_notification_logs** - Email/SMS notifications

## 🎯 Menu Categories

### 📊 BASIC VIEWS (1-5)
- Show all tables
- View users
- View vendors  
- View managers
- View daily status submissions

### 📈 ATTENDANCE DATA (6-9)
- View swipe records
- View mismatch records
- View leave records
- View WFH records

### 🔔 SYSTEM DATA (10-14)
- View holidays
- View system configurations
- View notifications
- View email notifications
- View audit logs

### 📊 ANALYTICS & REPORTS (15-21)
- **Database statistics** - Complete count of all records
- **Attendance summary** - Status distribution and approval rates
- **Vendor summary** - Statistics by company and band
- **Pending approvals** - Items requiring manager action
- **Team status overview** - Manager team statistics
- **Attendance trends** - Historical attendance patterns
- **Recent activity** - Last 24 hours of system activity

### 🔧 UTILITIES (22-24)
- Search data across tables
- View specific table with custom limits
- Refresh database connection

## 🚀 Key Features

### Enhanced Data Views
- All table views include proper joins to show meaningful data
- Vendor and manager names displayed instead of just IDs
- Timestamps formatted for readability
- Configurable record limits for large tables

### Comprehensive Statistics
- Real-time counts for all 13 tables
- Attendance status distribution with percentages  
- Approval status breakdowns
- Company and band distribution analysis

### Advanced Analytics
- **Pending Approvals**: Combines daily status and mismatch approval queues
- **Team Status**: Shows manager workload and pending items
- **Attendance Trends**: Historical patterns over customizable periods
- **Recent Activity**: Cross-table activity monitoring

### Smart Search
- Multi-table search across users and vendors
- Pattern matching on names, IDs, companies, and departments

### Error Handling
- Graceful error handling for missing tables
- Connection retry capabilities
- Clear error messages with debugging info

## 💡 Usage Examples

### Quick Database Overview
```bash
python view_database.py
# Choose option 15 for complete statistics
```

### Check Pending Work
```bash
python view_database.py
# Choose option 18 to see all items awaiting approval
```

### Analyze Team Performance
```bash
python view_database.py
# Choose option 19 for team status overview
# Choose option 20 for attendance trends
```

### Search for Specific Data
```bash
python view_database.py
# Choose option 22 and search for vendor names, IDs, or companies
```

## 🔍 Data Relationships Visualized

The viewer intelligently joins related tables to provide meaningful insights:
- **Vendors** ↔ **Users** ↔ **Managers** (User management chain)
- **Daily Statuses** ↔ **Vendors** (Attendance submissions)
- **Swipe Records** ↔ **Vendors** (Physical attendance)
- **Mismatch Records** ↔ **Vendors** (Reconciliation issues)
- **Audit Logs** ↔ **Users** (System activity tracking)
- **Notifications** ↔ **Users/Managers** (Communication logs)

## 📈 Business Intelligence Features

1. **Manager Dashboard View**: Team size, pending approvals, submission rates
2. **Attendance Analytics**: Office vs WFH trends, leave patterns
3. **System Health**: Audit trail, notification delivery, error tracking
4. **Operational Efficiency**: Approval turnaround times, data quality metrics

This comprehensive database viewer transforms your raw database into an accessible, business-friendly interface for monitoring and managing your workforce attendance system.
