# ATTENDO Database Scripts Guide

This guide explains all the database setup and management scripts available for the ATTENDO Vendor Timesheet Tool.

## 📋 Scripts Overview

| Script | Purpose | Safety Level | When to Use |
|--------|---------|--------------|-------------|
| `1_initialize_database.py` | Create tables and basic setup | ✅ Safe | First setup, after clearing |
| `2_load_sample_data.py` | Load comprehensive sample data | ✅ Safe | Development, testing |
| `3_Add_Special_Cases_SampleData.py` | Add mismatch scenarios | ✅ Safe | Testing, demos |
| `4_add_halfday_columns_migration.py` | Add half-day support columns | ⚠️ Migration | One-time upgrade |
| `5_clear_Tables_In_DataBase.py` | Clear all data | ⚠️ Destructive | Fresh start, testing |

## 🚀 Quick Start Sequence

For a **fresh installation** or **complete reset**:

```bash
# 1. Clear existing data (optional, if database exists)
python 5_clear_Tables_In_DataBase.py

# 2. Initialize database structure and admin user
python 1_initialize_database.py

# 3. Load comprehensive sample data
python 2_load_sample_data.py

# 4. Add complex mismatch scenarios for testing
python 3_Add_Special_Cases_SampleData.py

# 5. Start the application
python app.py
```

## 📖 Detailed Script Documentation

### 1. `1_initialize_database.py` - Database Initialization
**Purpose**: Creates database tables, system configurations, basic holidays, and admin user.

**Features**:
- ✅ Creates all database tables with proper schema
- ✅ Sets up default admin user (Admin/admin123)
- ✅ Adds basic holidays and system configurations
- ✅ Initializes notification settings
- ✅ Safe to run multiple times (idempotent)

**Output**:
- Admin user created
- 4 holidays added
- System configurations initialized
- Database schema ready

---

### 2. `2_load_sample_data.py` - Sample Data Loading
**Purpose**: Loads comprehensive realistic sample data for development and testing.

**Features**:
- ✅ Creates 3 managers and 5 vendors
- ✅ Generates 45 days of attendance data
- ✅ Creates realistic swipe records
- ✅ Adds leave and WFH approvals
- ✅ Includes notification logs and audit trails

**Data Created**:
- 8 users (3 managers + 5 vendors)
- 225 daily status records
- 225 swipe records
- Various leave/WFH approvals
- Notification and audit logs

---

### 3. `3_Add_Special_Cases_SampleData.py` - Mismatch Scenarios
**Purpose**: Creates specific mismatch scenarios for testing and demonstration.

**Features**:
- ✅ 9 basic mismatch scenarios
- ✅ 8 enhanced half-day mismatch scenarios
- ✅ Realistic edge cases and conflicts
- ✅ Tests enhanced mismatch detection algorithm
- ✅ Generates detailed half-day analysis

**Scenarios Created**:
- WFH claimed but swipe shows office presence
- Leave claimed but no approval record
- Half-day combinations with timing conflicts
- Complex AM/PM period mismatches

---

### 4. `4_add_halfday_columns_migration.py` - Half-Day Migration
**Purpose**: One-time migration to add enhanced half-day support columns.

**Features**:
- ✅ Adds `half_am_type` and `half_pm_type` columns to daily_statuses
- ✅ Adds `mismatch_details` JSON column to mismatch_records
- ✅ Maintains backward compatibility
- ✅ Verifies migration success

**Migration Details**:
- Adds nullable enum columns for half-day types
- Adds JSON text column for detailed mismatch storage
- Preserves existing data
- Only needs to be run once

---

### 5. `5_clear_Tables_In_DataBase.py` - Database Reset
**Purpose**: Completely clears all data while preserving table structure.

**⚠️ WARNING**: This script **DELETES ALL DATA** from the database!

**Features**:
- ⚠️ Requires explicit confirmation ("YES DELETE ALL")
- ✅ Preserves table schema and structure
- ✅ Handles foreign key constraints properly
- ✅ Resets auto-increment sequences
- ✅ Creates fresh admin user after cleanup
- ✅ Provides detailed progress feedback

**Safety Features**:
- Shows current record counts before deletion
- Requires exact confirmation phrase
- Handles errors gracefully
- Verifies complete cleanup
- Provides next steps after completion

## 🎯 Use Case Examples

### Development Setup
```bash
# Start with fresh database
python 1_initialize_database.py
python 2_load_sample_data.py
python app.py
```

### Testing Complex Scenarios
```bash
python 3_Add_Special_Cases_SampleData.py
# Then test mismatch detection and resolution
```

### Production Migration
```bash
# Backup database first!
python 4_add_halfday_columns_migration.py
# Test application functionality
```

### Fresh Reset for Demo
```bash
python 5_clear_Tables_In_DataBase.py
python 1_initialize_database.py
python 2_load_sample_data.py
python 3_Add_Special_Cases_SampleData.py
```

## 🔍 Script Outputs and Verification

### Expected Results After Full Setup:
- **Users**: 9 total (1 admin + 3 managers + 5 vendors)
- **Daily Statuses**: ~400+ records (base + enhanced scenarios)
- **Swipe Records**: ~400+ records
- **Mismatch Records**: 60+ mismatches with detailed analysis
- **Other Records**: Holidays, notifications, audit logs, approvals

### Login Credentials Created:
- **Admin**: Admin / admin123
- **Managers**: M001-M003 / password123
- **Vendors**: EMP001-EMP005 / password123

## ⚡ Performance and Safety

### Database Size After Full Setup:
- Approximately 1,000+ total records
- SQLite file size: ~500KB - 1MB
- Fast execution on modern systems

### Safety Considerations:
- Scripts include error handling and rollback
- Confirmation required for destructive operations
- Detailed logging and progress reporting
- Idempotent operations where possible

## 🔧 Troubleshooting

### Common Issues:

1. **Import Errors**:
   ```
   Solution: Run from project root directory
   cd /path/to/vendor-timesheet-tool
   python script_name.py
   ```

2. **Database Locked**:
   ```
   Solution: Close any running instances of the app
   pkill -f "python app.py"
   ```

3. **Migration Already Applied**:
   ```
   Info: Migration scripts detect if already run
   Safe to re-execute
   ```

4. **Permission Issues**:
   ```
   Solution: Check file permissions on database file
   chmod 664 vendor_timesheet.db
   ```

## 📊 Monitoring Script Success

### Check Database After Setup:
```bash
# Quick verification
sqlite3 vendor_timesheet.db ".tables"
sqlite3 vendor_timesheet.db "SELECT COUNT(*) FROM users;"
sqlite3 vendor_timesheet.db "SELECT COUNT(*) FROM daily_statuses;"
sqlite3 vendor_timesheet.db "SELECT COUNT(*) FROM mismatch_records;"
```

### Application Health Check:
```bash
python app.py
# Visit http://localhost:5000
# Login with Admin/admin123
# Check vendor dashboard for sample data
```

---

## 🎉 Ready to Use!

After running the appropriate scripts, your ATTENDO system will be ready with:
- ✅ Complete database schema with half-day support
- ✅ Realistic sample data for development
- ✅ Complex mismatch scenarios for testing
- ✅ Enhanced detection algorithms
- ✅ Detailed reconciliation capabilities

Choose the scripts that match your use case and follow the recommended sequence for the best results!
