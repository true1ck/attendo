"""
ATTENDO - Simple Standalone Runner
This runs the application with minimal dependencies
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta, date
import json
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hackathon-attendo-vendor-timesheet-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/vendor_timesheet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Import all models
exec(open('models.py', encoding='utf-8').read())

# Import demo data
exec(open('demo_data.py', encoding='utf-8').read())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Home page - redirect to login or dashboard"""
    if current_user.is_authenticated:
        if current_user.role == UserRole.VENDOR:
            return redirect(url_for('vendor_dashboard'))
        elif current_user.role == UserRole.MANAGER:
            return redirect(url_for('manager_dashboard'))
        elif current_user.role == UserRole.ADMIN:
            return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash(f'Welcome {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/vendor/dashboard')
@login_required
def vendor_dashboard():
    """Vendor dashboard"""
    if current_user.role != UserRole.VENDOR:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    vendor = current_user.vendor_profile
    if not vendor:
        flash('Vendor profile not found', 'error')
        return redirect(url_for('login'))
    
    return render_template('vendor_dashboard.html', vendor=vendor)

@app.route('/manager/dashboard')
@login_required
def manager_dashboard():
    """Manager dashboard"""
    if current_user.role != UserRole.MANAGER:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    manager = current_user.manager_profile
    if not manager:
        flash('Manager profile not found', 'error')
        return redirect(url_for('login'))
    
    return render_template('manager_dashboard.html', manager=manager)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    # Get statistics
    total_vendors = Vendor.query.count()
    total_managers = Manager.query.count()
    total_statuses_today = DailyStatus.query.filter_by(status_date=date.today()).count()
    
    return render_template('admin_dashboard.html',
                         total_vendors=total_vendors,
                         total_managers=total_managers,
                         total_statuses_today=total_statuses_today)

@app.route('/admin/ai-insights')
@login_required
def ai_insights():
    """AI Insights Dashboard"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    # Mock AI statistics
    ai_stats = {
        'last_trained': 'Today, 09:30 AM',
        'accuracy': '94.2%',
        'predictions_made': '1,247',
        'absence_predictions': 8,
        'wfh_predictions': 12,
        'risk_alerts': 3,
        'pattern_insights': 15
    }
    
    return render_template('ai_insights.html', ai_stats=ai_stats)

@app.route('/admin/reports-dashboard')
@login_required
def reports_dashboard():
    """Reports Dashboard"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    stats = {
        'monthly_reports': 12,
        'billing_reports': 8,
        'analytics_reports': 15,
        'scheduled_reports': 5
    }
    
    return render_template('reports_dashboard.html', stats=stats)

@app.route('/admin/import-dashboard')
@login_required
def import_dashboard():
    """Import Dashboard"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    return render_template('import_dashboard.html')

@app.route('/api/docs')
def api_docs():
    """API Documentation with Swagger UI"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ATTENDO API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css">
        <style>
            body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; padding: 20px; text-align: center; }
            h1 { margin: 0; font-size: 2.5em; }
            .subtitle { margin-top: 10px; font-size: 1.2em; opacity: 0.9; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 ATTENDO API Documentation</h1>
            <div class="subtitle">Interactive API Explorer - Try it out!</div>
        </div>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-bundle.js"></script>
        <script>
            const ui = SwaggerUIBundle({
                url: "/swagger.yaml",
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout"
            })
        </script>
    </body>
    </html>
    '''

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        
        # Check if demo data already exists
        if User.query.count() == 0:
            print("📦 Creating demo data...")
            create_demo_data()
            print("✅ Demo data created!")

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎯 ATTENDO - Enterprise Attendance Management System")
    print("="*70)
    print("⚡ Starting application...")
    
    # Create database directory if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    
    # Create tables and demo data
    with app.app_context():
        create_tables()
    
    print("="*70)
    print("🚀 ATTENDO is now running!")
    print("="*70)
    print("\n📌 Access Points:")
    print("   🌐 Web Interface:     http://localhost:5000")
    print("   📚 API Documentation: http://localhost:5000/api/docs")
    print("\n🔐 Login Credentials:")
    print("   👑 Admin:    admin / admin123")
    print("   👔 Manager:  manager1 / manager123")  
    print("   👤 Vendor:   vendor1 / vendor123")
    print("\n💡 Tips:")
    print("   • Try the AI Insights dashboard (Admin login)")
    print("   • Check out the interactive API docs")
    print("   • Submit attendance as a vendor")
    print("   • Approve requests as a manager")
    print("\n✨ Press CTRL+C to stop the server")
    print("="*70 + "\n")
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
