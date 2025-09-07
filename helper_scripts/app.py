from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import os
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import pytz

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hackathon-attendo-vendor-timesheet-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vendor_timesheet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize models first
import models

# Initialize extensions
db = models.db
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Import routes and other modules after app initialization
from import_routes import import_bp
from notifications import start_notification_scheduler
from swagger_ui import register_swagger_ui

# Now import routes - must be after app is created to avoid circular import
import routes

# Register blueprints
app.register_blueprint(import_bp)

# Register Swagger UI
register_swagger_ui(app)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

def create_tables():
    """Create database tables and initialize demo data"""
    with app.app_context():
        from models import User
        db.create_all()
        
        # Check if demo data already exists
        if User.query.count() == 0:
            initialize_demo_data()

def initialize_demo_data():
    """Initialize the database with demo data for hackathon presentation"""
    from demo_data import create_demo_data
    create_demo_data()

if __name__ == '__main__':
    print("\n" + "="*70)
    print("ATTENDO - Starting Application...")
    print("="*70)
    
    # Create tables and initialize demo data
    with app.app_context():
        create_tables()
        print("Database initialized with demo data!")
    
    # Start notification scheduler
    start_notification_scheduler()
    print("Notification scheduler started!")
    
    print("="*70)
    print("ATTENDO is now running!")
    print("="*70)
    print("\nAccess the application at:")
    print("   Web Interface: http://localhost:5000")
    print("   API Documentation: http://localhost:5000/api/docs")
    print("\nLogin Credentials:")
    print("   Admin:    admin / admin123")
    print("   Manager:  manager1 / manager123")
    print("   Vendor:   vendor1 / vendor123")
    print("\nPress CTRL+C to stop the server")
    print("="*70 + "\n")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
