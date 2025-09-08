Test data for ATTENDO imports and reconciliation.

Files:
- swipe_data.csv
  Columns: Employee ID, Attendance Date (YYYY-MM-DD), Weekday, Login, Logout, Total Working Hours, Attendance Status (AP/AA)
  Sample includes:
    - EMP001 present on 2025-09-01 (AP)
    - EMP001 absent on 2025-09-02 (AA)
    - EMP002 present on 2025-09-01 (AP)

- leave_data.csv
  Columns: OT ID, Start Date, End Date, Attendance or Absence Type, Day
  Sample includes: EMP001 leave on 2025-09-02 (1 day)

- wfh_data.csv
  Columns: RD Name, Start Date, End Date, Duration
  Sample includes: John Vendor WFH on 2025-09-04 (1 day)

NOTE:
- Make sure the Employee IDs (EMP001, EMP002) and names (John Vendor, Jane Vendor) match vendors in your database
  (Vendor.vendor_id and Vendor.full_name). If not, edit the CSV to use your existing IDs/names.

How to test:
1) Import swipe_data.csv via Import Dashboard → Import Swipe Data
2) Import leave_data.csv via Import Leave Data
3) Import wfh_data.csv via Import WFH Data
4) Go to Reconciliation page: /admin/reconciliation and click "Run Reconciliation"
5) Review mismatches and summary.

