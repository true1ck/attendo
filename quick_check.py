from flask import Flask
import os
import models

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath("vendor_timesheet.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
models.db.init_app(app)

with app.app_context():
    from models import User, Vendor, DailyStatus
    print('👥 Users:', User.query.count())
    print('🏢 Vendors:', Vendor.query.count()) 
    print('📅 Daily Statuses:', DailyStatus.query.count())
    
    if User.query.count() > 0:
        users = User.query.all()
        for user in users:
            print(f'   - {user.username} ({user.role.value}) - Last login: {user.last_login}')
    else:
        print('   No users found!')
