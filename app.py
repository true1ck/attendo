"""
ATTENDO Application Entry Point

This is the main entry point for the ATTENDO application using enterprise
application factory pattern for better organization and scalability.
"""

import os
import sys

# Add the src directory to Python path for proper imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from attendo import create_app
from attendo.services.notification_service import start_notification_scheduler

# Create application using factory pattern
app = create_app()

if __name__ == '__main__':
    # Start notification scheduler for development
    start_notification_scheduler()
    
    # Run the Flask app
    app.run(
        debug=app.config.get('DEBUG', False),
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000)
    )
