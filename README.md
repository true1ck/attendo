# 🎯 ATTENDO - Workforce Management Platform

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)](https://www.sqlalchemy.org)

A comprehensive workforce management platform that streamlines attendance tracking, vendor management, and analytics for modern enterprises.

## 🚀 Features

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

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd vendor-timesheet-tool
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

4. **Access the application**
- Web Interface: http://localhost:5000
- API Documentation: http://localhost:5000/api/docs

### Test Credentials
- **Admin:** `admin` / `admin123`
- **Manager:** `manager1` / `manager123`
- **Vendor:** `vendor1` / `vendor123`

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

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

---

**A professional workforce management solution for modern enterprises**
