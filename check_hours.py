import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app import app, db, DailyStatus, Vendor
from datetime import date

with app.app_context():
    v = Vendor.query.filter_by(vendor_id='EMP001').first()
    if v:
        s = DailyStatus.query.filter_by(vendor_id=v.id, status_date=date.today()).first()
        if s:
            print(f'Today ({date.today()}) total_hours in DB: {s.total_hours}')
            print(f'Status: {s.status.value}')
            print(f'Location: {s.location}')
        else:
            print(f'No status found for today ({date.today()})')
    else:
        print('Vendor EMP001 not found')
