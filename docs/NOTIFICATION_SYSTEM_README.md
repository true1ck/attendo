# Excel-Based Notification System

## Overview

This document describes the comprehensive Excel-based notification system implemented for the ATTENDO workforce management platform, based on requirements from `requirement_doc.html`.

## System Architecture

### Previous System Issues
- Hard-coded notification logic in Python files
- No easy way to modify notification settings
- Limited customization options
- Difficult to manage recipient lists

### New Excel-Based System
- **10 separate Excel configuration files** for different notification types
- **Fully configurable** notification settings, timing, and recipients
- **Dynamic recipient management** with enable/disable capabilities
- **Centralized configuration** that non-technical users can modify

## Notification Types Implemented

Based on the requirements document analysis, the following 10 notification types have been implemented:

### 1. Daily Status Reminders (`01_daily_status_reminders.xlsx`)
- **Purpose**: Remind vendors to submit daily attendance status
- **Trigger**: Every 3 hours (configurable) until status is filled
- **Recipients**: Vendors who haven't submitted status
- **Configurable Options**: Timing, intervals, weekdays only, holiday exclusions

### 2. Manager Summary Notifications (`02_manager_summary_notifications.xlsx`)
- **Purpose**: Send team status summaries to managers
- **Trigger**: 12:00 PM and 2:00 PM (configurable)
- **Recipients**: Managers
- **Configurable Options**: What information to include, timing, team statistics

### 3. Manager All-Complete Notifications (`03_manager_all_complete_notifications.xlsx`)
- **Purpose**: Notify managers when all team members have submitted status
- **Trigger**: When all team statuses are complete
- **Recipients**: Managers
- **Configurable Options**: Completion stats, next actions, auto-approval options

### 4. Mismatch Notifications (`04_mismatch_notifications.xlsx`)
- **Purpose**: Alert about attendance mismatches between web status and swipe data
- **Trigger**: After reconciliation process finds discrepancies
- **Recipients**: Managers and Vendors
- **Configurable Options**: Mismatch types, escalation timing, explanation requirements

### 5. Manager Feedback Notifications (`05_manager_feedback_notifications.xlsx`)
- **Purpose**: Send feedback from managers to vendors (approvals/rejections)
- **Trigger**: When manager approves/rejects status
- **Recipients**: Vendors
- **Configurable Options**: Feedback types, response deadlines, corrective actions

### 6. Monthly Report Notifications (`06_monthly_report_notifications.xlsx`)
- **Purpose**: Automated monthly attendance report delivery
- **Trigger**: 1st of each month
- **Recipients**: Managers and Admins
- **Configurable Options**: Report types, attachments, generation day

### 7. Admin System Alerts (`07_admin_system_alerts.xlsx`)
- **Purpose**: Critical system notifications for administrators
- **Trigger**: System errors, high mismatches, security alerts
- **Recipients**: System Administrators
- **Configurable Options**: Alert types, severity levels, escalation timing

### 8. Holiday Reminder Notifications (`08_holiday_reminder_notifications.xlsx`)
- **Purpose**: Remind all users about upcoming holidays
- **Trigger**: 7 days before holiday (configurable)
- **Recipients**: All users (Vendors, Managers, Admins)
- **Configurable Options**: Advance notice days, holiday calendar inclusion

### 9. Late Submission Alerts (`09_late_submission_alerts.xlsx`)
- **Purpose**: Alert about vendors with late attendance submissions
- **Trigger**: 24-48 hours after deadline
- **Recipients**: Managers and Admins
- **Configurable Options**: Alert timing, history inclusion, escalation

### 10. Billing Correction Notifications (`10_billing_correction_notifications.xlsx`)
- **Purpose**: Notify about billing adjustments and corrections
- **Trigger**: When billing corrections are processed
- **Recipients**: Managers and Admins
- **Configurable Options**: Financial details, justification, acknowledgment requirements

## Excel Configuration Structure

Each Excel file contains the following standard columns:

### Core Identity Fields
- `Primary_Key`: Unique identifier for each notification configuration
- `Contact_Email`: Recipient's email address
- `Contact_Name`: Recipient's full name
- `Role`: USER role (VENDOR, MANAGER, ADMIN)

### Control Fields
- `Send_Notification`: YES/NO to enable/disable notifications
- `Active`: YES/NO to activate/deactivate the configuration
- `Notification_Method`: TEAMS,EMAIL,SMS (comma-separated)
- `Priority`: LOW/MEDIUM/HIGH/CRITICAL

### Timing Controls
- `Notification_Times`: Specific times (e.g., "12:00,14:00")
- `Weekdays_Only`: YES/NO to limit to weekdays
- `Exclude_Holidays`: YES/NO to skip holiday notifications

### Content Controls
- `Custom_Message`: Custom message text
- `Include_[Various]`: YES/NO flags for content inclusion
- `Teams_Channel`: Teams channel identifier
- `Phone_Number`: For SMS notifications

### Audit Fields
- `Created_Date`: When configuration was created
- `Last_Modified`: Last modification timestamp

## File Structure

```
vendor-timesheet-tool/
├── notification_configs/
│   ├── 01_daily_status_reminders.xlsx
│   ├── 02_manager_summary_notifications.xlsx
│   ├── 03_manager_all_complete_notifications.xlsx
│   ├── 04_mismatch_notifications.xlsx
│   ├── 05_manager_feedback_notifications.xlsx
│   ├── 06_monthly_report_notifications.xlsx
│   ├── 07_admin_system_alerts.xlsx
│   ├── 08_holiday_reminder_notifications.xlsx
│   ├── 09_late_submission_alerts.xlsx
│   └── 10_billing_correction_notifications.xlsx
├── excel_notification_manager.py
├── notifications_updated.py
├── create_notification_configs.py
└── NOTIFICATION_SYSTEM_README.md
```

## Implementation Files

### 1. `excel_notification_manager.py`
- **Purpose**: Core notification management system
- **Features**: 
  - Loads all Excel configurations
  - Sends emails, Teams messages, SMS
  - Manages recipient filtering and timing
  - Updates configuration files

### 2. `notifications_updated.py`
- **Purpose**: Updated scheduler and notification functions
- **Features**:
  - Replaces original hard-coded notification logic
  - Uses Excel-based configurations
  - Maintains backward compatibility
  - Scheduled automation

### 3. `create_notification_configs.py`
- **Purpose**: Initial setup script to generate Excel files
- **Features**:
  - Creates all 10 Excel configuration files
  - Populates with sample data
  - Can be run to regenerate configurations

## Key Features

### 1. **Granular Control**
Each notification type can be individually configured with:
- Specific timing and frequency
- Content inclusion/exclusion options
- Recipient-specific settings
- Multiple delivery methods

### 2. **Easy Management**
- **Non-technical users** can modify Excel files
- **No code changes** required for notification adjustments
- **Immediate effect** when Excel files are saved
- **Role-based configurations** for different user types

### 3. **Comprehensive Coverage**
All notification requirements from the specification are covered:
- ✅ Teams reminders every 3 hours
- ✅ Manager notifications at 12 PM and 2 PM
- ✅ All-complete notifications
- ✅ Mismatch detection and alerts
- ✅ Monthly reconciliation notifications
- ✅ Holiday reminders
- ✅ Billing correction notifications
- ✅ Late submission tracking
- ✅ System admin alerts

### 4. **Multi-Channel Support**
- **Email**: HTML formatted emails with attachments
- **Microsoft Teams**: Webhook-based messages
- **SMS**: Phone number-based text messages
- **Mixed delivery**: Different methods for different people

### 5. **Smart Filtering**
- **Time-based**: Only send at appropriate hours
- **Day-based**: Weekdays only or include weekends
- **Holiday-aware**: Skip notifications on holidays
- **Role-based**: Different configs for different roles

## Usage Instructions

### For Administrators

1. **Modify Notification Settings**:
   - Open relevant Excel file in `notification_configs/` folder
   - Change `Send_Notification` to YES/NO to enable/disable
   - Modify timing, content, and delivery options
   - Save the Excel file (changes take effect immediately)

2. **Add New Recipients**:
   - Add new row to appropriate Excel file
   - Fill in all required fields
   - Set `Active` to YES and `Send_Notification` to YES

3. **Disable Notifications**:
   - Change `Active` to NO or `Send_Notification` to NO
   - Or delete the row entirely

### For Developers

1. **Add New Notification Types**:
   - Create new Excel file following the standard structure
   - Add corresponding functions in `excel_notification_manager.py`
   - Update the scheduler in `notifications_updated.py`

2. **Customize Message Templates**:
   - Modify the message generation logic in respective functions
   - Add new configurable fields to Excel files
   - Update the message formatting in notification functions

## Integration with Existing System

### Backward Compatibility
- Original function names maintained for compatibility
- Existing scheduler framework preserved
- Database models unchanged
- API endpoints unaffected

### Performance Considerations
- Excel files loaded once at startup
- Configurations cached in memory
- Minimal database impact
- Efficient recipient filtering

### Error Handling
- Graceful fallbacks if Excel files are missing
- Validation of required fields
- Logging of notification failures
- Continued operation if some notifications fail

## Future Enhancements

### Phase 2 Features
1. **Web-based Configuration UI**: Replace Excel editing with web interface
2. **Template Management**: Visual template editor for notification content
3. **Advanced Scheduling**: More complex timing rules and conditions
4. **Analytics Dashboard**: Track notification delivery and engagement
5. **A/B Testing**: Test different message formats and timing

### Integration Options
1. **Active Directory**: Sync recipient lists automatically
2. **LDAP Integration**: Enterprise directory services
3. **SSO Integration**: Single sign-on for notification preferences
4. **Mobile App Push**: Native mobile notifications
5. **Slack Integration**: Alternative to Teams notifications

## Compliance and Audit

### Audit Trail
- All notification configurations timestamped
- Delivery logs maintained in database
- Configuration changes tracked
- Failed delivery attempts logged

### Privacy Considerations
- Email addresses stored securely
- Phone numbers encrypted
- GDPR compliance features ready
- Opt-out mechanisms available

## Testing

### Test Commands
```bash
# Generate initial configuration files
python create_notification_configs.py

# Test notification system
python -c "from excel_notification_manager import excel_notification_manager; excel_notification_manager.send_daily_status_reminders()"

# Load and validate configurations  
python -c "from excel_notification_manager import excel_notification_manager; print('Loaded configs:', list(excel_notification_manager.notification_configs.keys()))"
```

### Sample Data
Each Excel file includes sample data for testing:
- Demo email addresses
- Example phone numbers  
- Test Teams channels
- Sample configuration options

---

## Summary

This Excel-based notification system provides a **complete replacement** for the previous hard-coded notification logic, offering:

✅ **Full Requirements Compliance**: All 10+ notification types from requirements doc  
✅ **Easy Management**: Excel files that business users can modify  
✅ **Granular Control**: Individual settings for timing, content, and delivery  
✅ **Multi-Channel Support**: Email, Teams, SMS delivery options  
✅ **Enterprise Ready**: Scalable, auditable, and maintainable  

The system is **immediately operational** and can be customized without any code changes by simply editing the Excel configuration files.
