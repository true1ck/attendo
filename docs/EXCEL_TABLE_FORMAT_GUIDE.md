# Excel Table Format Guide

## Overview

This guide explains how to ensure that all Excel sheet updates in the ATTENDO system are saved in proper table format for Power Automate compatibility. With the new table formatting system, every Excel file is automatically structured as a named table that Power Automate can easily reference.

## Why Table Format is Important

Power Automate works best with Excel data when it's structured as tables because:

- **Reliable References**: Tables have names that don't change when data is added or removed
- **Dynamic Ranges**: Tables automatically expand/contract as data changes
- **Better Performance**: Power Automate can process table data more efficiently
- **Consistent Structure**: Tables ensure consistent column headers and data types

## New Features

### 1. Excel Table Formatter Module (`excel_table_formatter.py`)

The core module that handles all table formatting operations:

```python
from excel_table_formatter import (
    update_notification_table,
    create_notification_table,
    save_dataframe_as_table,
    validate_notification_table
)

# Update a notification file with table format
df = pd.DataFrame(your_data)
success = update_notification_table(df, 'daily_reminders')

# Create a new notification file with table format  
success = create_notification_table(df, 'manager_summary')
```

### 2. Excel Table Utils (`excel_table_utils.py`)

Wrapper functions that can replace `pandas.DataFrame.to_excel()`:

```python
from excel_table_utils import to_excel_with_table, update_excel_table

# Instead of: df.to_excel('file.xlsx')
# Use: 
success = to_excel_with_table(df, 'file.xlsx', table_name='MyData')

# Update existing Excel file while preserving table structure
success = update_excel_table(df, 'existing_file.xlsx')
```

## Supported Notification Types

The system automatically recognizes these notification types and applies appropriate table configurations:

| Notification Type | Table Name | Sheet Name | File Pattern |
|---|---|---|---|
| `daily_reminders` | DailyStatusReminders | Daily_Reminders | `*daily_reminders*` |
| `manager_summary` | ManagerSummaryNotifications | Manager_Summary | `*manager_summary*` |
| `late_submissions` | LateSubmissionAlerts | Late_Submissions | `*late_submission*` |
| `mismatch_alerts` | MismatchNotifications | Mismatch_Alerts | `*mismatch*` |
| `manager_feedback` | ManagerFeedbackNotifications | Manager_Feedback | `*manager_feedback*` |
| `monthly_reports` | MonthlyReportNotifications | Monthly_Reports | `*monthly_report*` |
| `admin_alerts` | AdminSystemAlerts | System_Alerts | `*admin*alert*` |
| `holiday_reminders` | HolidayReminderNotifications | Holiday_Reminders | `*holiday*` |
| `billing_corrections` | BillingCorrectionNotifications | Billing_Corrections | `*billing*` |

## How to Use

### For Developers

#### 1. Updating Existing Code

**Old way:**
```python
df.to_excel('notification_configs/daily_reminders.xlsx', index=False)
```

**New way:**
```python
from excel_table_formatter import update_notification_table
update_notification_table(df, 'daily_reminders')
```

#### 2. Creating New Files

```python
from excel_table_formatter import create_notification_table

# Create notification file with proper table format
data = pd.DataFrame({
    'Primary_Key': ['VENDOR_001', 'VENDOR_002'],
    'Contact_Email': ['user1@company.com', 'user2@company.com'],
    'Send_Notification': ['YES', 'YES'],
    'Active': ['YES', 'YES'],
    # ... other columns
})

success = create_notification_table(data, 'daily_reminders')
```

#### 3. Validating Table Structure

```python
from excel_table_formatter import validate_notification_table

# Validate a specific notification type
result = validate_notification_table('daily_reminders')
print(f"Valid: {result['valid']}")
if result['valid']:
    for table in result['tables']:
        print(f"Table: {table['name']} ({table['range']})")
```

### For System Administrators

#### 1. Validate All Excel Files

Use the daily updater to check all notification files:

```bash
python daily_excel_updater.py --action validate
```

Sample output:
```
Validation Results:
  daily_reminders: ✅ VALID
    - Has Required Columns: ✅
    - Has Table Format: ✅
      Table: DailyStatusReminders (A1:V5)
  manager_summary: ✅ VALID
    - Has Required Columns: ✅
    - Has Table Format: ✅
      Table: ManagerSummaryNotifications (A1:U3)
```

#### 2. Ensure All Files Have Table Format

Convert existing Excel files to proper table format:

```bash
python daily_excel_updater.py --action ensure_tables
```

This will:
- Process all Excel files in the `notification_configs` directory
- Create backups of existing files
- Convert each file to proper table format
- Preserve all existing data

#### 3. Batch Operations

```python
from excel_table_utils import (
    ensure_all_excel_files_have_tables,
    batch_validate_excel_tables
)

# Ensure all files in a directory have table format
results = ensure_all_excel_files_have_tables('notification_configs')
for filename, success in results.items():
    print(f"{filename}: {'✅' if success else '❌'}")

# Validate all files in a directory
validations = batch_validate_excel_tables('notification_configs')
for filename, result in validations.items():
    print(f"{filename}: {'✅' if result['valid'] else '❌'}")
```

## Updated System Components

### 1. Daily Excel Updater (`daily_excel_updater.py`)

Now uses table formatting for all updates:

```python
# All these methods now save with table format:
- update_daily_reminders_sheet()
- update_late_submissions_sheet() 
- update_manager_summary_sheets()
- update_vendor_in_daily_reminders()
```

### 2. Power Automate Excel Refresh (`power_automate_excel_refresh.py`)

Creates Power Automate compatible tables:

```python
# These now create proper Excel tables:
- Daily reminders with table name 'DailyStatusReminders'
- Manager summaries with table name 'ManagerSummaryNotifications'
- Late submissions with table name 'LateSubmissionAlerts'
```

### 3. Excel Notification Manager (`excel_notification_manager.py`)

Configuration updates maintain table format:

```python
# Config updates now preserve table structure
excel_notification_manager.update_notification_config(
    'daily_reminders', 
    'VENDOR_001', 
    {'Send_Notification': 'NO'}
)
```

## Power Automate Integration

### Referencing Tables in Power Automate

With proper table formatting, you can reference Excel data in Power Automate using table names:

1. **Excel Online (Business)** connector
2. **List rows present in a table** action
3. **Table**: Select the named table (e.g., "DailyStatusReminders")

### Benefits

- **No more range references**: Instead of "A1:Z100", use table name "DailyStatusReminders"
- **Dynamic sizing**: Tables automatically adjust as data grows/shrinks
- **Consistent headers**: Table headers remain constant
- **Better error handling**: Power Automate handles table operations more reliably

## Troubleshooting

### Common Issues

1. **"No tables found in worksheet"**
   - Run: `python daily_excel_updater.py --action ensure_tables`
   - This will convert all files to table format

2. **"File does not exist"**
   - Run: `python create_power_automate_tables.py`
   - This creates all required notification config files

3. **"Invalid table range"**
   - The file may have been manually edited
   - Re-run the ensure_tables command to fix formatting

### Manual Verification

To manually check if an Excel file has proper tables:

1. Open the Excel file
2. Go to any cell with data
3. Press `Ctrl+T` or go to Insert > Table
4. If properly formatted, you should see "Your table has headers" is checked
5. The table should have a name visible in the Table Design tab

### Recovery

If files become corrupted or lose table formatting:

```bash
# Create fresh files with sample data
python create_power_automate_tables.py

# Or restore from backup (backups are created automatically)
# Look for files named "backup_YYYYMMDD_HHMMSS_filename.xlsx"
```

## Best Practices

1. **Always use the table formatter functions** instead of direct `pandas.to_excel()`
2. **Validate regularly** using the validation commands
3. **Keep backups** - the system creates automatic backups
4. **Test Power Automate flows** after any Excel file updates
5. **Monitor logs** for table formatting errors

## Migration Guide

### Existing Installations

If you have existing Excel files without table formatting:

1. **Backup your data** (system does this automatically)
2. **Run the conversion**:
   ```bash
   python daily_excel_updater.py --action ensure_tables
   ```
3. **Validate the results**:
   ```bash
   python daily_excel_updater.py --action validate
   ```
4. **Update Power Automate flows** to use table names instead of ranges

### Code Updates

Replace direct pandas calls:

```python
# Old
df.to_excel('file.xlsx', index=False)

# New  
from excel_table_formatter import update_notification_table
update_notification_table(df, 'daily_reminders')
```

## Support

If you encounter issues with table formatting:

1. Check the logs for detailed error messages
2. Use the validation tools to identify problems
3. Run the ensure_tables command to fix formatting issues
4. Verify Power Automate flows can access the tables correctly

The system is designed to be backward compatible while adding robust table formatting capabilities for better Power Automate integration.
