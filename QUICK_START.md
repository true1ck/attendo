# 🚀 ATTENDO - Quick Start Guide

**Perfect sample database setup in 2 minutes!**

## 📋 Requirements
- Python 3.8+ 
- Git

## ⚡ Setup Commands

### Step 1: Clone and Install
```bash
git clone https://github.com/YOUR_USERNAME/vendor-timesheet-tool.git
cd vendor-timesheet-tool
pip install -r requirements.txt
```

### Step 2: Initialize Database (Required)
```bash
python 1_initialize_database.py
```
**Creates:** SQLite database, tables, Admin user, holidays

### Step 3: Load Sample Data (Recommended)
```bash
python 2_load_sample_data.py
```
**Creates:** 9 users, 45 days of attendance data, realistic scenarios

### Step 4: Add Special Cases & Mismatches (For Full Demo)
```bash
python 3_Add_Special_Cases_SampleData.py
```
**Creates:** 59+ mismatch scenarios, special cases, edge cases for testing

### Step 5: Start Application
```bash
python app.py
```
**Access:** http://localhost:5000

## 🔑 Login Credentials

| Role | Username | Password | Description |
|------|----------|----------|-------------|
| **Admin** | `Admin` | `admin123` | Full system access |
| **Manager** | `manager1` | `manager123` | Team management |
| **Manager** | `manager2` | `manager123` | Team management |  
| **Manager** | `manager3` | `manager123` | Team management |
| **Vendor** | `vendor1` | `vendor123` | Daily attendance |
| **Vendor** | `vendor2` | `vendor123` | Daily attendance |
| **Vendor** | `vendor3` | `vendor123` | Daily attendance |
| **Vendor** | `vendor4` | `vendor123` | Daily attendance |
| **Vendor** | `vendor5` | `vendor123` | Daily attendance |

## 📊 What You Get (After All 3 Scripts)

✅ **550+ sample records** across all tables  
✅ **175+ attendance records** (45 days of realistic data)  
✅ **175+ swipe records** with office hours and conflicts  
✅ **9 user accounts** (1 Admin + 3 Managers + 5 Vendors)  
✅ **59+ mismatch records** for reconciliation demo  
✅ **Holiday calendar** with national holidays  
✅ **Audit trail** with 100+ activity logs  
✅ **Leave & WFH records** for approval testing  
✅ **Special cases:** WFH conflicts, missing swipes, approval gaps

## 🔍 View Sample Data

### Option 1: New Comprehensive Viewer (🎆 Recommended)
```bash
python 4_ViewDatabase.py                    # Interactive menu
python 4_ViewDatabase.py --summary          # Quick overview
python 4_ViewDatabase.py --users            # View all users  
python 4_ViewDatabase.py --mismatches       # View all 59 mismatches
python 4_ViewDatabase.py --all              # Show everything
```

### Option 2: Original Viewer
```bash
python scripts/view_database.py --summary   # Quick overview
python scripts/view_database.py            # Interactive mode
```

## 🧪 Test the Features

### Admin Dashboard
- Login: `Admin` / `admin123`
- Visit: http://localhost:5000
- Features: User management, system reports, reconciliation

### Manager Dashboard  
- Login: `manager1` / `manager123`
- Features: Team oversight, attendance approvals, reports

### Vendor Dashboard
- Login: `vendor1` / `vendor123` 
- Features: Daily status submission, personal history

## 📈 Import CSV Test Data (Optional)
```bash
# Start the app, then go to http://localhost:5000/import/
# Upload these files as Admin:
# - Test_DATA/swipe_data.csv
# - Test_DATA/leave_data.csv  
# - Test_DATA/wfh_data.csv
```

## 🎯 Key URLs
- **Main App:** http://localhost:5000
- **API Docs:** http://localhost:5000/api/docs  
- **Admin Panel:** http://localhost:5000/admin/dashboard
- **Import Tools:** http://localhost:5000/import/
- **Reconciliation:** http://localhost:5000/admin/reconciliation

## 🚨 Troubleshooting

### Reset Everything
```bash
rm vendor_timesheet.db
python 1_initialize_database.py
python 2_load_sample_data.py
```

### Dependencies Issue
```bash
pip install --upgrade -r requirements.txt
```

### Port 5000 Busy
Edit `app.py`, change last line to use port 8000:
```python
app.run(debug=True, host='0.0.0.0', port=8000)
```

### Python Version Check
```bash
python --version  # Should be 3.8+
```

---

**🎉 That's it! You now have a fully functional workforce management system with realistic sample data.**

For detailed documentation, see [SETUP.md](SETUP.md)
