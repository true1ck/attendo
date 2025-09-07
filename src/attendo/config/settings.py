"""
ATTENDO Configuration Settings

This module provides configuration classes for different deployment environments
(development, production, testing) following enterprise best practices.
"""

import os
from pathlib import Path


class BaseConfig:
    """Base configuration with common settings"""
    
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hackathon-attendo-vendor-timesheet-2025'
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    
    # Notification settings
    NOTIFICATION_ENABLED = True
    NOTIFICATION_TIME = '09:00'  # Daily notification time
    
    # AI settings
    AI_PREDICTIONS_ENABLED = True
    AI_MODEL_REFRESH_INTERVAL = 3600  # 1 hour in seconds
    
    # Report settings
    REPORTS_ENABLED = True
    REPORTS_FOLDER = 'reports'
    
    # Logging settings
    LOG_LEVEL = 'INFO'
    LOG_FOLDER = 'logs'
    

class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///instance/vendor_timesheet_dev.db'
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    
    # Development-specific settings
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Database - use environment variable for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///instance/vendor_timesheet_prod.db'
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Performance settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 20,
        'pool_recycle': -1,
        'pool_pre_ping': True
    }


class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    
    DEBUG = True
    TESTING = True
    
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable external services during testing
    NOTIFICATION_ENABLED = False
    AI_PREDICTIONS_ENABLED = False
    
    # Speed up password hashing for tests
    WTF_CSRF_ENABLED = False
    

class DockerConfig(BaseConfig):
    """Docker deployment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Use PostgreSQL in Docker environment
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://attendo:password@db:5432/attendo_db'
    
    # Docker-specific settings
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration class based on environment name
    
    Args:
        config_name (str): Environment name (development, production, testing)
        
    Returns:
        BaseConfig: Configuration class instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default'])
