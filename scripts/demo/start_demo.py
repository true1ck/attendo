#!/usr/bin/env python3
"""
ATTENDO Hackathon Demo Launcher
Starts both the main application and Swagger documentation server
"""

import subprocess
import threading
import time
import webbrowser
import sys
import os

def start_main_app():
    """Start the main ATTENDO application"""
    print("🚀 Starting ATTENDO Main Application...")
    
    # Simple version without blueprint conflicts
    main_app_code = '''
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import os

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

# Import routes after model initialization
from routes import *

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
'''
    
    # Write simplified app
    with open('main_app_simple.py', 'w') as f:
        f.write(main_app_code)
    
    # Start the app
    subprocess.run([sys.executable, 'main_app_simple.py'])

def start_swagger_app():
    """Start the Swagger documentation server"""
    print("📖 Starting Swagger Documentation Server...")
    subprocess.run([sys.executable, 'swagger_app.py'])

def main():
    """Main demo launcher"""
    print("=" * 60)
    print("🎯 ATTENDO HACKATHON DEMO LAUNCHER")
    print("=" * 60)
    print("🚀 AI-Powered Workforce Management Platform")
    print("📊 Complete API Documentation & Testing Suite")
    print("=" * 60)
    
    # Check if files exist
    required_files = ['models.py', 'routes.py', 'swagger.yaml', 'swagger_app.py']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return
    
    print("✅ All required files found")
    print("")
    print("Starting applications...")
    print("")
    
    try:
        # Start both apps in separate threads
        main_thread = threading.Thread(target=start_main_app, daemon=True)
        swagger_thread = threading.Thread(target=start_swagger_app, daemon=True)
        
        main_thread.start()
        time.sleep(3)  # Give main app time to start
        
        swagger_thread.start()
        time.sleep(2)  # Give swagger app time to start
        
        print("=" * 60)
        print("🎉 ATTENDO DEMO IS READY!")
        print("=" * 60)
        print("🏠 Main Application: http://localhost:5000")
        print("📖 API Documentation: http://localhost:5001/api/docs")
        print("📋 Test Data: http://localhost:5001/test-data")
        print("⚡ System Status: http://localhost:5001/status")
        print("=" * 60)
        print("🔐 Demo Credentials:")
        print("   👨‍💻 Admin:   admin / admin123")
        print("   👨‍💼 Manager: manager1 / manager123")
        print("   👤 Vendor:  vendor1 / vendor123")
        print("=" * 60)
        print("🎯 Features to Demo:")
        print("   • Role-based Authentication")
        print("   • AI-Powered Absence Predictions")
        print("   • Real-time Dashboard Analytics")
        print("   • Data Import & Reconciliation")
        print("   • Interactive API Documentation")
        print("   • Comprehensive Audit Trail")
        print("=" * 60)
        print("🏆 Ready for Hackathon Victory!")
        print("=" * 60)
        
        # Open browser windows
        print("🌐 Opening browser windows...")
        time.sleep(2)
        webbrowser.open('http://localhost:5000')
        time.sleep(1)
        webbrowser.open('http://localhost:5001/api/docs')
        
        # Keep running
        print("📱 Applications running... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\\n🛑 Shutting down applications...")
        print("✅ Demo completed successfully!")

if __name__ == '__main__':
    main()
