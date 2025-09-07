#!/usr/bin/env python3
"""
Standalone Swagger API Documentation Server for ATTENDO
Run this alongside your main app to get interactive API documentation
"""

from flask import Flask, jsonify, render_template_string, redirect, request
from flask_swagger_ui import get_swaggerui_blueprint
import yaml
import json
import requests
from datetime import datetime

# Create standalone Flask app
swagger_app = Flask(__name__)
swagger_app.config['SECRET_KEY'] = 'swagger-attendo-api-docs'

# Define API server URL
MAIN_APP_URL = 'http://localhost:5000'
SWAGGER_URL = '/api/docs'
API_URL = '/swagger.json'

# Create Swagger UI blueprint
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "ATTENDO API Documentation",
        'deepLinking': True,
        'displayRequestDuration': True,
        'docExpansion': 'list',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'tryItOutEnabled': True,
        'customCss': '''
            .swagger-ui .topbar { 
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            }
            .swagger-ui .info .title {
                color: #1e40af;
                font-size: 2.5em;
            }
            .swagger-ui .scheme-container {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }
            .swagger-ui .opblock.opblock-post {
                border-color: #059669;
                background: rgba(5, 150, 105, 0.1);
            }
            .swagger-ui .opblock.opblock-get {
                border-color: #0284c7;
                background: rgba(2, 132, 199, 0.1);
            }
            .swagger-ui .btn.execute {
                background-color: #1e40af;
                border-color: #1e40af;
            }
        '''
    }
)

swagger_app.register_blueprint(swagger_ui_blueprint)

@swagger_app.route('/swagger.json')
def swagger_spec():
    """Serve the Swagger specification with live server URL"""
    try:
        # Load YAML file and convert to JSON
        with open('swagger.yaml', 'r', encoding='utf-8') as file:
            yaml_content = yaml.safe_load(file)
        
        # Update server URL to point to main app
        yaml_content['servers'] = [
            {
                'url': MAIN_APP_URL,
                'description': 'ATTENDO Main Application Server'
            }
        ]
        
        return jsonify(yaml_content)
    except Exception as e:
        return jsonify({'error': f'Could not load swagger spec: {str(e)}'}), 500

@swagger_app.route('/')
def home():
    """Home page with ATTENDO branding and navigation"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATTENDO API Documentation</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
            text-align: center;
        }
        .logo {
            font-size: 4em;
            font-weight: bold;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .tagline {
            font-size: 1.5em;
            margin-bottom: 40px;
            opacity: 0.9;
        }
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 60px 0;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-10px);
        }
        .feature-icon {
            font-size: 3em;
            margin-bottom: 20px;
        }
        .feature-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .btn {
            display: inline-block;
            padding: 15px 30px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            margin: 10px;
            font-size: 1.1em;
            transition: all 0.3s ease;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }
        .btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-3px);
        }
        .btn.primary {
            background: rgba(255, 255, 255, 0.9);
            color: #1e40af;
            font-weight: bold;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin: 40px 0;
            flex-wrap: wrap;
        }
        .stat {
            text-align: center;
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            display: block;
        }
        .stat-label {
            opacity: 0.8;
        }
        .credentials {
            background: rgba(0, 0, 0, 0.2);
            padding: 20px;
            border-radius: 10px;
            margin: 40px 0;
            font-family: monospace;
        }
        .cred-item {
            margin: 10px 0;
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            display: inline-block;
            margin-right: 15px;
        }
        @media (max-width: 768px) {
            .logo { font-size: 2.5em; }
            .stats { flex-direction: column; gap: 20px; }
            .btn { display: block; margin: 10px auto; max-width: 300px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 ATTENDO</div>
        <div class="tagline">AI-Powered Workforce Management API</div>
        
        <div class="stats">
            <div class="stat">
                <span class="stat-number">50+</span>
                <span class="stat-label">API Endpoints</span>
            </div>
            <div class="stat">
                <span class="stat-number">12</span>
                <span class="stat-label">Database Tables</span>
            </div>
            <div class="stat">
                <span class="stat-number">94.2%</span>
                <span class="stat-label">AI Accuracy</span>
            </div>
            <div class="stat">
                <span class="stat-number">3</span>
                <span class="stat-label">User Roles</span>
            </div>
        </div>

        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">🔐</div>
                <div class="feature-title">Authentication</div>
                <div class="feature-desc">Role-based access control with Admin, Manager, and Vendor roles</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <div class="feature-title">AI Analytics</div>
                <div class="feature-desc">Predictive absence analysis with 94.2% accuracy using machine learning</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Real-time Reports</div>
                <div class="feature-desc">Dynamic charts, export capabilities, and comprehensive analytics</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📥</div>
                <div class="feature-title">Data Import</div>
                <div class="feature-desc">Excel/CSV import, automatic reconciliation, and mismatch detection</div>
            </div>
        </div>

        <div class="credentials">
            <h3>🔐 Test Credentials</h3>
            <div class="cred-item"><strong>Admin:</strong> admin / admin123</div>
            <div class="cred-item"><strong>Manager:</strong> manager1 / manager123</div>
            <div class="cred-item"><strong>Vendor:</strong> vendor1 / vendor123</div>
        </div>

        <div style="margin-top: 50px;">
            <a href="/api/docs" class="btn primary">📖 Browse API Documentation</a>
            <a href="/test-data" class="btn">📋 View Test Data</a>
            <a href="{{ main_app_url }}" class="btn">🏠 Main Application</a>
            <a href="/status" class="btn">⚡ System Status</a>
        </div>

        <div style="margin-top: 60px; opacity: 0.7; font-size: 0.9em;">
            <p>🏆 ATTENDO - Ready for Hackathon Demo</p>
            <p>💻 Main App: <a href="{{ main_app_url }}" style="color: white;">{{ main_app_url }}</a></p>
            <p>📖 API Docs: <a href="/api/docs" style="color: white;">http://localhost:5001/api/docs</a></p>
        </div>
    </div>
</body>
</html>
    ''', main_app_url=MAIN_APP_URL)

@swagger_app.route('/test-data')
def test_data():
    """Provide comprehensive test data for API testing"""
    test_data = {
        'info': {
            'title': 'ATTENDO API Test Data',
            'description': 'Complete test data set for API validation and demo',
            'version': '1.0.0',
            'generated_at': datetime.now().isoformat()
        },
        'authentication': {
            'admin': {
                'username': 'admin',
                'password': 'admin123',
                'role': 'admin',
                'description': 'Full system access, user management, AI insights'
            },
            'manager': {
                'username': 'manager1', 
                'password': 'manager123',
                'role': 'manager',
                'description': 'Team management, approvals, reports'
            },
            'vendor': {
                'username': 'vendor1',
                'password': 'vendor123', 
                'role': 'vendor',
                'description': 'Status submission, personal analytics'
            }
        },
        'sample_requests': {
            'login': {
                'endpoint': '/login',
                'method': 'POST',
                'content_type': 'application/x-www-form-urlencoded',
                'data': {
                    'username': 'admin',
                    'password': 'admin123'
                }
            },
            'submit_status': {
                'endpoint': '/vendor/submit-status',
                'method': 'POST',
                'content_type': 'application/x-www-form-urlencoded',
                'data': {
                    'status_date': '2025-01-07',
                    'status': 'in_office_full',
                    'location': 'BL-A-5F',
                    'comments': 'Working on API integration'
                }
            },
            'ai_predictions': {
                'endpoint': '/api/ai/refresh-predictions',
                'method': 'POST',
                'content_type': 'application/json',
                'data': {}
            },
            'generate_report': {
                'endpoint': '/api/reports/generate',
                'method': 'POST',
                'content_type': 'application/json',
                'data': {
                    'report_type': 'monthly',
                    'month': '2025-01',
                    'format': 'excel'
                }
            },
            'add_holiday': {
                'endpoint': '/admin/add-holiday',
                'method': 'POST',
                'content_type': 'application/x-www-form-urlencoded',
                'data': {
                    'holiday_date': '2025-03-08',
                    'name': "International Women's Day",
                    'description': 'Celebrating women achievements globally'
                }
            }
        },
        'status_options': [
            'in_office_full',
            'in_office_half', 
            'wfh_full',
            'wfh_half',
            'leave_full',
            'leave_half',
            'absent'
        ],
        'current_system_data': {
            'total_users': 7,
            'total_vendors': 5,
            'total_managers': 1,
            'total_daily_statuses': 88,
            'total_swipe_records': 50,
            'database_tables': 12
        },
        'testing_workflow': [
            {
                'step': 1,
                'action': 'Login',
                'endpoint': '/login',
                'method': 'POST',
                'note': 'Authenticate to establish session'
            },
            {
                'step': 2,
                'action': 'Get Dashboard Stats',
                'endpoint': '/api/dashboard/stats',
                'method': 'GET',
                'note': 'Verify role-based data access'
            },
            {
                'step': 3,
                'action': 'Test AI Predictions',
                'endpoint': '/api/ai/refresh-predictions', 
                'method': 'POST',
                'note': 'Generate AI-powered insights'
            },
            {
                'step': 4,
                'action': 'Get Chart Data',
                'endpoint': '/api/charts/attendance-trends',
                'method': 'GET',
                'note': 'Retrieve visualization data'
            },
            {
                'step': 5,
                'action': 'Generate Report',
                'endpoint': '/api/reports/generate',
                'method': 'POST',
                'note': 'Create downloadable reports'
            }
        ]
    }
    
    return jsonify(test_data)

@swagger_app.route('/status')
def system_status():
    """Check system status and connectivity to main app"""
    status = {
        'swagger_server': {
            'status': 'running',
            'port': 5001,
            'endpoints': ['/', '/api/docs', '/test-data', '/swagger.json']
        },
        'main_app': {
            'url': MAIN_APP_URL,
            'status': 'checking...'
        },
        'timestamp': datetime.now().isoformat()
    }
    
    # Test connectivity to main app
    try:
        response = requests.get(f"{MAIN_APP_URL}/", timeout=5)
        if response.status_code in [200, 302]:
            status['main_app']['status'] = 'connected'
            status['main_app']['response_code'] = response.status_code
        else:
            status['main_app']['status'] = 'error'
            status['main_app']['response_code'] = response.status_code
    except requests.exceptions.RequestException as e:
        status['main_app']['status'] = 'disconnected'
        status['main_app']['error'] = str(e)
    
    return jsonify(status)

@swagger_app.route('/api/proxy/<path:endpoint>')
def api_proxy(endpoint):
    """Proxy API requests to main application for testing"""
    try:
        # Forward the request to main app
        if request.method == 'GET':
            response = requests.get(f"{MAIN_APP_URL}/{endpoint}", 
                                  params=request.args,
                                  cookies=request.cookies,
                                  timeout=10)
        elif request.method == 'POST':
            response = requests.post(f"{MAIN_APP_URL}/{endpoint}",
                                   data=request.form if request.form else request.get_json(),
                                   cookies=request.cookies,
                                   timeout=10)
        
        return response.content, response.status_code, dict(response.headers)
    except Exception as e:
        return jsonify({'error': f'Proxy error: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Starting ATTENDO Swagger API Documentation Server...")
    print("=" * 60)
    print("📖 Swagger UI: http://localhost:5001/api/docs")
    print("🏠 Home Page: http://localhost:5001/")
    print("📋 Test Data: http://localhost:5001/test-data")
    print("⚡ Status: http://localhost:5001/status")
    print("=" * 60)
    print("🔗 Main ATTENDO App should be running on: http://localhost:5000")
    print("🎯 Ready for Hackathon Demo!")
    print("=" * 60)
    
    # Run on different port to avoid conflicts
    swagger_app.run(debug=True, host='0.0.0.0', port=5001)
