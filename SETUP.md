# 🚀 ATTENDO - Complete Setup Guide

This guide will help you set up the ATTENDO Workforce Management Platform from scratch with sample data and database tables.

## 📋 Prerequisites

Before you start, ensure you have:

- **Python 3.8 or higher** installed
- **pip** (Python package manager)
- **Git** for cloning the repository

### Check Your Python Version
```bash
python --version
# Should show Python 3.8 or higher
```

## 🔄 Step 1: Clone and Install

### 1.1 Clone the Repository
```bash
git clone <repository-url>
cd vendor-timesheet-tool
```

### 1.2 Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 1.3 Install Dependencies
```bash
pip install -r requirements.txt
```

## 🗄️ Step 2: Database Setup with Sample Data

### 2.1 Basic Setup (Minimal Sample Data)
For a quick start with basic admin user only:

```bash
python app.py
```

This will:
- Create the database (`vendor_timesheet.db`)
- Create all necessary tables
- Add default admin user: `Admin` / `admin123`

### 2.2 Full Setup with Comprehensive Sample Data
For a complete demo experience with vendors, managers, and sample attendance data:

```bash
# Run the comprehensive setup script
python scripts/setup_database_with_samples.py
```

This will create:
- ✅ All database tables
- ✅ Admin user (`Admin` / `admin123`)
- ✅ Sample managers with accounts
- ✅ Sample vendors with accounts  
- ✅ Historical attendance records
- ✅ Sample holidays
- ✅ Realistic mismatch scenarios

## 📊 Step 3: Verify Database Setup

### 3.1 View Database Tables
```bash
python scripts/view_database.py
```

This will show you:
- All tables and their record counts
- Sample users with their roles
- Recent attendance data
- System configuration

### 3.2 View Sample Data
```bash
python scripts/view_database.py --detailed
```

## 🌐 Step 4: Start the Application

### 4.1 Run the Application
```bash
python app.py
```

### 4.2 Access the Application
Open your web browser and go to:

- **Web Interface**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/docs

## 🔐 Step 5: Test Login Credentials

### Default Accounts Created:

#### Admin Account
- **Username**: `Admin`
- **Password**: `admin123`
- **Role**: Administrator
- **Access**: Full system access

#### Sample Manager Accounts
- **Username**: `manager1`
- **Password**: `manager123`
- **Role**: Manager
- **Department**: Engineering Team

#### Sample Vendor Accounts
- **Username**: `vendor1`
- **Password**: `vendor123` 
- **Role**: Vendor
- **Employee ID**: `EMP001`

(More accounts available - see database viewer output)

## 📈 Step 6: Test with Sample Data

### 6.1 Import Test Data (Optional)
The system includes pre-made test data for import testing:

1. Login as Admin
2. Go to: http://localhost:5000/import/
3. Import the test files:
   - **Swipe Data**: `Test_DATA/swipe_data.csv`
   - **Leave Data**: `Test_DATA/leave_data.csv`  
   - **WFH Data**: `Test_DATA/wfh_data.csv`

### 6.2 Run Reconciliation
1. Go to: http://localhost:5000/admin/reconciliation
2. Click "Run Reconciliation"
3. Review the mismatch summary and detailed reports

## 🏗️ Database Structure Overview

After setup, your database will contain these main tables:

### User Management
- **users** - Authentication accounts
- **vendors** - Vendor profiles and details
- **managers** - Manager profiles and team assignments

### Attendance Tracking
- **daily_statuses** - Daily attendance submissions by vendors
- **swipe_records** - Physical swipe machine data
- **leave_records** - Leave applications and approvals
- **wfh_records** - Work from home records

### System Management
- **holidays** - System holiday calendar
- **mismatch_records** - Attendance discrepancies
- **notification_logs** - Email/SMS notification history
- **audit_logs** - Complete system activity audit trail

### Configuration
- **system_configurations** - App settings and parameters

## 🔧 Step 7: Configuration (Optional)

### 7.1 Environment Variables
Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` file for production settings:
```env
# Email Configuration (for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Database (for production)
DATABASE_URL=sqlite:///vendor_timesheet.db

# Security
SECRET_KEY=your-secure-random-key-here
```

### 7.2 Notification Setup
For email notifications to work:
1. Set up Gmail App Password (if using Gmail)
2. Update `SMTP_USER` and `SMTP_PASSWORD` in `.env`
3. Restart the application

## 🧪 Step 8: Testing the System

### 8.1 Test Different User Roles
1. **As Admin**: Manage users, view system reports, configure holidays
2. **As Manager**: Approve vendor statuses, view team reports, manage team
3. **As Vendor**: Submit daily status, view personal dashboard

### 8.2 Test Key Features
- ✅ Daily attendance submission
- ✅ Manager approval workflow
- ✅ Mismatch detection and resolution
- ✅ Report generation and export
- ✅ Holiday management
- ✅ Audit trail viewing

## 🚀 Step 9: API Testing

### 9.1 Swagger UI
Visit http://localhost:5000/api/docs for interactive API documentation

### 9.2 Postman Collection
Import `docs/project_docs/ATTENDO_Postman_Collection.json` for API testing

## 🛠️ Troubleshooting

### Common Issues:

#### Database Permission Error
```bash
# If you get permission errors, try:
chmod 755 .
python app.py
```

#### Missing Dependencies
```bash
# If imports fail, reinstall requirements:
pip install --upgrade -r requirements.txt
```

#### Port Already in Use
```bash
# If port 5000 is busy, modify app.py:
# Change: app.run(debug=True, host='0.0.0.0', port=5000)
# To: app.run(debug=True, host='0.0.0.0', port=8000)
```

#### Database Issues
```bash
# Reset database completely:
rm vendor_timesheet.db
python scripts/setup_database_with_samples.py
```

### Get Help
- Check `docs/TROUBLESHOOTING.md` for detailed solutions
- Review `docs/` folder for feature-specific documentation
- Check application logs for error messages

## ✅ Verification Checklist

After setup, verify these items work:

- [ ] Application starts without errors
- [ ] Can login with admin credentials
- [ ] Database viewer shows populated tables
- [ ] Can access all dashboards (admin/manager/vendor)
- [ ] Sample data is visible in reports
- [ ] API documentation loads properly
- [ ] Can submit and approve attendance status
- [ ] Mismatch detection works with sample data

## 🎯 Next Steps

Now that your system is set up:

1. **Explore Features**: Try all the dashboards and features
2. **Customize Data**: Modify sample data to match your needs
3. **Configure Notifications**: Set up email/SMS notifications
4. **Plan Deployment**: Review production deployment options
5. **Test Integrations**: Try the Power Automate integration features

---

**🎉 Congratulations!** Your ATTENDO system is ready for testing and development.

For production deployment, see `docs/DEPLOYMENT.md` (if available) or contact the development team.
