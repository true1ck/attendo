"""
ATTENDO API Package

This package contains all API blueprints and routes for the ATTENDO application.
"""

from flask import Blueprint


def register_blueprints(app):
    """
    Register all API blueprints with the Flask application
    
    Args:
        app: Flask application instance
    """
    from .auth import auth_bp
    from .vendor import vendor_bp
    from .manager import manager_bp
    from .admin import admin_bp
    from .reports import reports_bp
    from .charts import charts_bp
    from .swagger_ui import swagger_bp
    
    # Register all blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(vendor_bp, url_prefix='/vendor')
    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(charts_bp, url_prefix='/api/charts')
    app.register_blueprint(swagger_bp, url_prefix='/api')


__all__ = ['register_blueprints']
