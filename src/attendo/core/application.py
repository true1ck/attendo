"""
ATTENDO Core Application Factory

This module provides the Flask application factory pattern for creating
and configuring the ATTENDO application with proper enterprise structure.
"""

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os


def create_app(config_name=None):
    """
    Application factory function that creates and configures Flask application
    
    Args:
        config_name (str): Configuration environment name (development, production, testing)
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__, 
                template_folder='../../../templates',
                static_folder='../../../static')
    
    # Load configuration
    from ..config.settings import get_config
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    from ..models import db
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'api.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from ..models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from ..api import register_blueprints
    register_blueprints(app)
    
    # Initialize services
    from ..services.notification_service import start_notification_scheduler
    if not app.config.get('TESTING', False):
        start_notification_scheduler()
    
    # Create database tables and demo data
    with app.app_context():
        create_database_tables()
        initialize_demo_data()
    
    return app


def create_database_tables():
    """Create database tables if they don't exist"""
    from ..models import db
    from ..models.user import User
    
    db.create_all()
    
    # Check if demo data already exists
    if User.query.count() == 0:
        from ..services.demo_data_service import create_demo_data
        create_demo_data()


def initialize_demo_data():
    """Initialize the database with demo data for presentation"""
    from ..models.user import User
    if User.query.count() == 0:
        from ..services.demo_data_service import create_demo_data
        create_demo_data()
