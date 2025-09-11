# Power Automate Excel Format Guide

## Overview
The vendor timesheet tool now includes automatic Excel formatting for Power Automate compatibility. This ensures all Excel files synced from the local `notification_configs` folder to the network folder (e.g., `G:\Test`) maintain a consistent format that Power Automate can reliably read.

## Required Column Structure
All Excel files **MUST** contain these columns in this exact order for Power Automate compatibility:

| Column Name | Description | Data Type | Example |
|------------|-------------|-----------|---------|
| **EmployeeID** | Unique identifier for the employee | String | EMP001 |
| **ContactEmail** | Email address for notifications | Email | john.doe@company.com |
| **Message** | Notification message content | String | Please submit your timesheet |
| **NotificationType** | Category of notification | String | Daily Reminder |
| **Priority** | Urgency level of notification | String | High/Medium/Low |

## Features

### 1. Automatic Formatting During Sync
When Excel files are synced from the local folder to the network folder via the `/admin/excel-sync` interface, they are automatically:
- Validated for the correct column structure
- Reformatted if necessary to match Power Automate requirements
- Saved as properly formatted Excel tables

### 2. Column Mapping
The formatter intelligently maps existing columns to the required format:
- Recognizes common variations (e.g., `employee_id`, `EmpID`, `UserID` → `EmployeeID`)
- Preserves existing data when possible
- Adds default values for missing columns

### 3. Excel Table Creation
All formatted files include:
- Named Excel tables for easy Power Automate reference
- Consistent table styling (TableStyleMedium9)
- Auto-adjusted column widths for readability

## API Endpoints

### Force Sync with Formatting
```
POST /api/excel-sync/force
```
Triggers immediate sync with automatic Power Automate formatting.

### Manual Format Network Folder
```
POST /api/excel-sync/format-power-automate
Content-Type: application/json

{
    "backup": true  // Create backup before formatting (optional, default: true)
}
```
Manually formats all Excel files in the network folder.

### Format Specific File
```
POST /api/excel-sync/format-power-automate
Content-Type: application/json

{
    "file_name": "01_daily_status_reminders.xlsx",
    "backup": true
}
```
Formats a specific Excel file in the network folder.

## Using the Python Module

### Import the Formatter
```python
from scripts.excel_power_automate_formatter import (
    validate_and_format_excel_for_power_automate,
    format_directory_for_power_automate
)
```

### Format Single File
```python
# Format a single Excel file
success = validate_and_format_excel_for_power_automate(
    'path/to/file.xlsx',
    backup=True  # Create backup before formatting
)
```

### Format Entire Directory
```python
# Format all Excel files in a directory
result = format_directory_for_power_automate(
    'path/to/directory',
    backup=True
)

print(f"Formatted {result['formatted_count']} files")
if result['errors']:
    print(f"Errors: {result['errors']}")
```

## Power Automate Integration

### Flow Configuration
When setting up Power Automate flows to read these Excel files:

1. **List Rows Present in Table**: Use this action to read data from the formatted Excel files
2. **Table Name**: Look for tables named `PowerAutomateTable_[filename]`
3. **Column References**: Use the exact column names:
   - `EmployeeID`
   - `ContactEmail`
   - `Message`
   - `NotificationType`
   - `Priority`

### Example Power Automate Flow
```yaml
trigger:
  - Recurrence (every 10 minutes)

actions:
  1. List rows present in table:
     - Location: OneDrive for Business / SharePoint
     - Document Library: Network Share
     - File: /G/Test/01_daily_status_reminders.xlsx
     - Table: PowerAutomateTable_01_daily_status_reminders
  
  2. Apply to each (row):
     - Send email:
         To: @{items('Apply_to_each')?['ContactEmail']}
         Subject: @{items('Apply_to_each')?['NotificationType']}
         Body: @{items('Apply_to_each')?['Message']}
         Priority: @{items('Apply_to_each')?['Priority']}
```

## Default Values
When data is missing or columns cannot be mapped, the following defaults are applied:

| Column | Default Value |
|--------|--------------|
| EmployeeID | N/A |
| ContactEmail | admin@company.com |
| Message | Notification from [filename] |
| NotificationType | Extracted from filename or "General Notification" |
| Priority | Medium |

## Notification Type Detection
The formatter automatically detects notification types from filenames:

| Filename Contains | Notification Type |
|------------------|-------------------|
| daily | Daily Reminder |
| manager_summary | Manager Summary |
| mismatch | Mismatch Alert |
| holiday | Holiday Reminder |
| late | Late Submission |
| monthly | Monthly Report |
| admin | Admin Alert |
| billing | Billing Correction |

## Backup Files
- Backups are created with the prefix `PA_backup_` followed by timestamp
- Example: `PA_backup_20250912_143022_original_file.xlsx`
- Backup files are automatically excluded from sync and formatting operations

## Troubleshooting

### Files Not Formatting Correctly
1. Check that the source file is a valid `.xlsx` file
2. Ensure the file is not locked or in use
3. Verify network folder permissions

### Power Automate Can't Read Table
1. Confirm the table name in Excel matches what's referenced in Power Automate
2. Check that the file has been properly formatted (first 5 columns should be the required ones)
3. Ensure the Excel file is saved and not corrupted

### Column Mapping Issues
If your data has custom column names not recognized by the formatter:
1. Manually rename columns to match expected names before sync
2. Or modify the `column_variations` dictionary in `excel_power_automate_formatter.py`

## Best Practices

1. **Always Test First**: Test formatting on a copy of your data before production use
2. **Keep Backups**: Enable backup creation when formatting (default behavior)
3. **Consistent Naming**: Use consistent column names across all Excel files
4. **Regular Validation**: Periodically check that files maintain correct format
5. **Monitor Sync Logs**: Check the Excel sync logs in the admin dashboard for any formatting errors

## Support
For issues or questions about Power Automate formatting:
1. Check the Excel sync logs in Admin Dashboard
2. Review error messages in the API responses
3. Verify file formats using the validation scripts
4. Contact system administrator if issues persist
