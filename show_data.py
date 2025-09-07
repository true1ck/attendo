from flask import Flask
import os
import models
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath("vendor_timesheet.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
models.db.init_app(app)

with app.app_context():
    from models import User, Vendor, Manager, DailyStatus
    
    print('🎯 COMPLETE DATABASE OVERVIEW')
    print('='*50)
    
    print('\n👥 USERS:')
    df = pd.read_sql_query('SELECT username, email, role FROM users ORDER BY id', models.db.engine)
    print(df.to_string(index=False))
    
    print('\n🏢 VENDORS:')
    df = pd.read_sql_query('''
        SELECT v.vendor_id, v.full_name, v.department, v.company, v.band, v.location, u.username 
        FROM vendors v 
        JOIN users u ON v.user_id = u.id 
        ORDER BY v.id
    ''', models.db.engine)
    print(df.to_string(index=False))
    
    print('\n📅 DAILY STATUS SUBMISSIONS:')
    df = pd.read_sql_query('''
        SELECT v.vendor_id, v.full_name, ds.status_date, ds.status, ds.location, ds.comments
        FROM daily_statuses ds
        JOIN vendors v ON ds.vendor_id = v.id
        ORDER BY ds.status_date DESC
    ''', models.db.engine)
    print(df.to_string(index=False))
    
    print('\n👔 MANAGERS:')
    df = pd.read_sql_query('''
        SELECT m.full_name, m.department, m.team_name, u.username
        FROM managers m
        JOIN users u ON m.user_id = u.id
    ''', models.db.engine)
    print(df.to_string(index=False))
    
    print('\n🔐 LOGIN CREDENTIALS:')
    print('   Admin:    admin / admin123')
    print('   Manager:  manager1 / manager123') 
    print('   Vendor 1: vendor1 / vendor123')
    print('   Vendor 2: vendor2 / vendor123')
