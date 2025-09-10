# 🎯 ATTENDO - Workforce Management Platform

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)](https://www.sqlalchemy.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive workforce management platform that streamlines attendance tracking, vendor management, and analytics for modern enterprises.

> **🚀 Ready to Run:** Complete with sample data, database setup scripts, and comprehensive documentation.

## 📸 Quick Demo

![ATTENDO Dashboard](docs/images/dashboard-preview.png)

*Multi-role dashboard with real-time attendance tracking, mismatch detection, and comprehensive reporting.*

## 📚 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [🎯 Features](#-features)
- [🛠️ Technology Stack](#-technology-stack)
- [📊 Database Schema](#-database-schema)
- [📖 Complete Setup Guide](#-complete-setup-guide)
- [📝 API Documentation](#-api-documentation)
- [🏢 Architecture](#-architecture)
- [🔧 Configuration](#-configuration)
- [🧪 Testing](#-testing)
- [🚀 Deployment](#-deployment)
- [🤝 Contributing](#-contributing)

## 🎯 Features

### 🔐 Authentication & Authorization
- Role-based Access Control (Admin/Manager/Vendor)
- Session Management with secure login/logout
- Multi-tenant Architecture

### 📊 Dashboard & Reporting
- Real-time Dashboards for all user roles
- Interactive Charts and visualizations
- AI Insights (heuristic absence/WFH predictions)
- Monthly Attendance Reports with Excel export
- Comprehensive audit trail
- Custom Report Scheduling

### 👥 Vendor Management
- Multi-vendor Support across departments
- Attendance Status Submission (Office/WFH/Leave)
- Manager Approval Workflows
- Mismatch Detection between web status and swipe data
- Holiday Management

### 🔔 Notifications & Integrations
- Email Alerts for pending approvals
- Background Job Scheduling
- Real-time Status Updates

### 📱 API & Documentation
- RESTful API with comprehensive endpoints
- Interactive Swagger UI for API testing
- OpenAPI 3.0 Specification

## 🛠️ Technology Stack

### Backend
- **Python 3.8+** - Core programming language
- **Flask 3.0** - Web framework
- **SQLAlchemy 2.0** - ORM and database toolkit
- **Flask-Login** - User session management
- **APScheduler** - Background job scheduling

### Frontend
- **Bootstrap 5** - Responsive UI framework
- **Chart.js** - Interactive data visualizations
- **jQuery** - DOM manipulation and AJAX

### Database
- **SQLite** - Development database (easily replaceable)
- **Support for PostgreSQL/MySQL** - Production ready

### API Documentation
- **Swagger UI** - Interactive API documentation
- **OpenAPI 3.0** - API specification standard

## 📊 Database Schema

ATTENDO uses a comprehensive database schema designed for enterprise workforce management:

### Core Tables
- **users** - Authentication and user accounts
- **vendors** - Vendor profiles and company information
- **managers** - Manager profiles and team assignments
- **daily_statuses** - Daily attendance submissions
- **swipe_records** - Physical attendance machine data
- **holidays** - Company holiday calendar

### Advanced Features
- **mismatch_records** - Attendance discrepancy tracking
- **notification_logs** - Email/SMS notification history
- **audit_logs** - Complete system activity trail
- **leave_records** - Leave management
- **wfh_records** - Work from home tracking

**View Database Schema:** Run `python scripts/view_database.py` after setup to explore all tables and relationships.

## 🚀 Quick Start

### 📍 Prerequisites
- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **pip** (comes with Python)

### ⚡ Installation Options

#### Option 1: Basic Setup (Admin Only)
```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/vendor-timesheet-tool.git
cd vendor-timesheet-tool

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database
python 1_initialize_database.py

# 4. Run the application
python app.py
```

**🌍 Access Points:**
- **Web Interface:** http://localhost:5000
- **API Documentation:** http://localhost:5000/api/docs
- **Login:** `Admin` / `admin123`

#### Option 2: Complete Setup with Sample Data (🎆 Recommended)
```bash
# 1-2. Clone and install (same as above)

# 3. Initialize database
python 1_initialize_database.py

# 4. Load comprehensive sample data
python 2_load_sample_data.py

# 5. Start the application
python app.py
```

**📋 Explore Sample Data:**
```bash
python scripts/view_database.py --summary  # Quick overview
python scripts/view_database.py           # Interactive database viewer
```

### 🔑 Test Credentials (Full Setup)

| Role | Username | Password | Access Level |
|------|----------|----------|-------------|
| **Admin** | `Admin` | `admin123` | Full system access |
| **Manager** | `manager1` | `manager123` | Team management, approvals |
| **Manager** | `manager2` | `manager123` | Team management, approvals |
| **Vendor** | `vendor1` | `vendor123` | Personal dashboard, status submission |
| **Vendor** | `vendor2` | `vendor123` | Personal dashboard, status submission |
| **Vendor** | `vendor3` | `vendor123` | Personal dashboard, status submission |

### 🚀 What You Get

✅ **Complete user accounts** (Admin, Managers, Vendors)  
✅ **Historical attendance data** (30+ days of realistic data)  
✅ **Mismatch scenarios** (WFH vs Office conflicts, missing swipes)  
✅ **Holiday calendar** (System holidays pre-configured)  
✅ **Sample reconciliation data** (CSV import ready)  
✅ **Interactive API documentation** (Swagger UI)  

## 📖 Setup Guides

### ⚡ **[QUICK_START.md](QUICK_START.md)** - 2-Minute Setup
Perfect for first-time setup with exact commands to copy/paste.

### 📚 **[SETUP.md](SETUP.md)** - Complete Guide
Detailed instructions with troubleshooting, configuration, and verification.

## 📖 API Documentation

The complete API documentation is available via Swagger UI at `/api/docs` when the application is running.

### Key Endpoints

#### Authentication
- `POST /login` - User authentication
- `GET /logout` - User logout

#### Admin APIs
- `GET /api/dashboard/stats` - System statistics
- `POST /admin/add-holiday` - Add system holidays

#### Manager APIs
- `POST /manager/approve-status/{id}` - Approve/reject vendor status
- `GET /manager/team-report` - Generate team reports

#### Vendor APIs
- `POST /vendor/submit-status` - Submit daily attendance status
- `GET /vendor/dashboard` - Personal dashboard

#### Analytics & Reports
- `GET /api/charts/attendance-trends` - Chart data
- `GET /api/export/monthly-report` - Export reports

#### AI Insights
- `GET /manager/ai-insights` - Manager AI insights page
- `GET /api/ai/report?window=7&format=excel|json` - Export AI insights
- `POST /api/ai/schedule` - Set AI analysis schedule
- `GET /api/ai/model-logs` - Recent AI-related logs
- `POST /api/ai/override` - Emergency enable/disable toggle

See docs/AI_MODEL.md for a concise overview of how AI Insights works.

## 🏗️ Architecture

### Project Structure
```
vendor-timesheet-tool/
├── app.py                 # Main application entry point
├── models.py             # Database models and schemas
├── swagger_ui.py         # Swagger UI configuration
├── demo_data.py          # Sample data initialization
├── notifications.py      # Notification system
├── utils.py              # Utility functions
├── import_routes.py      # Data import functionality
├── templates/            # HTML templates
├── static/              # Static assets (CSS, JS, images)
├── helper_scripts/      # Development and utility scripts
├── requirements.txt     # Python dependencies
├── swagger.yaml         # OpenAPI specification
└── README.md           # This file
```

### Database Schema
- **Users & Authentication** - User accounts with role-based permissions
- **Vendor Management** - Vendor profiles and company information
- **Attendance Tracking** - Daily status submissions and approvals
- **Reporting & Analytics** - Historical data and trend analysis
- **System Configuration** - Holidays, notifications, and settings

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///vendor_timesheet.db
DEBUG=True
```

### Database Setup
The application automatically creates and initializes the database with sample data on first run.

For production, update the `DATABASE_URL` in your environment variables.

## 🧪 Testing

### Quick test with Test_DATA
A ready-to-use Test_DATA folder is included for validating imports and reconciliation:

1) Start the app
```bash
pip install -r requirements.txt
python app.py
```

2) Open the Import Dashboard at http://localhost:5000/import/
- Import Swipe Data → select Test_DATA/swipe_data.csv
- Import Leave Data → select Test_DATA/leave_data.csv
- Import WFH Data → select Test_DATA/wfh_data.csv

3) Validate imports
- Click "Validate Imported Data" to see duplicate counts and overlaps

4) Run reconciliation
- Go to http://localhost:5000/admin/reconciliation and click "Run Reconciliation"
- Review the summary and open the detailed mismatch viewer

### Manual Testing
1. Start the application: `python app.py`
2. Open Swagger UI: http://localhost:5000/api/docs
3. Use the test credentials provided
4. Click "Try it out" on any endpoint

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
1. **Update configuration** for production database
2. **Set environment variables** for security
3. **Use WSGI server** like Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker Support
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🤝 Contributing

We welcome contributions to ATTENDO! Here's how you can help:

### 🐛 Bug Reports & Feature Requests
- 🔍 [Search existing issues](../../issues) first
- 📝 [Create new issue](../../issues/new) with detailed description
- 🎯 Use appropriate labels (bug, enhancement, question)

### 💻 Code Contributions

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/vendor-timesheet-tool.git
   cd vendor-timesheet-tool
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up development environment**
   ```bash
   pip install -r requirements.txt
   python scripts/setup_database_with_samples.py
   ```

4. **Make your changes**
   - Follow existing code style
   - Add tests for new features
   - Update documentation if needed

5. **Test your changes**
   ```bash
   python app.py  # Manual testing
   python scripts/view_database.py  # Verify DB changes
   ```

6. **Commit and push**
   ```bash
   git add .
   git commit -m "Add: Your descriptive commit message"
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request**
   - 📝 Provide clear description of changes
   - 🗂 Link related issues
   - ✅ Ensure all checks pass

### 📄 Documentation
- Improve setup guides, API docs, or code comments
- Add examples and use cases
- Report documentation issues

---

## 🎆 Acknowledgments

- Built with ♥️ for MediaTek Hackathon
- Powered by Flask, SQLAlchemy, and modern web technologies
- Special thanks to all contributors and testers

## 📞 Support

- 📖 **Documentation:** [SETUP.md](SETUP.md) | [API Reference](docs/API_REFERENCE.md)
- 🐛 **Issues:** [GitHub Issues](../../issues)
- 💬 **Discussions:** [GitHub Discussions](../../discussions)
- 📧 **Contact:** [Open an Issue](../../issues/new)

---

<div align="center">

**🎯 ATTENDO - Professional Workforce Management**

*Streamlining attendance tracking, vendor management, and analytics for modern enterprises*

[![⭐ Star this project](https://img.shields.io/github/stars/YOUR_USERNAME/vendor-timesheet-tool?style=social)](../../stargazers)
[![🍴 Fork this project](https://img.shields.io/github/forks/YOUR_USERNAME/vendor-timesheet-tool?style=social)](../../network/members)

Made with ♥️ by [Your Name](https://github.com/YOUR_USERNAME)

</div>
