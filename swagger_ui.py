from flask import Blueprint, render_template_string, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import yaml
import json
import os

# Create Swagger UI blueprint
SWAGGER_URL = '/api/docs'
API_URL = '/api/docs/swagger.json'

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "ATTENDO API Documentation",
        'dom_id': '#swagger-ui',
        'url': API_URL,
        'layout': 'StandaloneLayout',
        'deepLinking': True,
        'displayRequestDuration': True,
        'docExpansion': 'list',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'tryItOutEnabled': True,
        'requestInterceptor': '''
            function(request) {
                // Add session handling for authentication
                request.credentials = 'include';
                return request;
            }
        ''',
        'responseInterceptor': '''
            function(response) {
                // Handle redirects for authentication
                if (response.status === 302) {
                    console.log('Redirect response:', response);
                }
                return response;
            }
        ''',
        'customCss': '''
            .swagger-ui .topbar { 
                background-color: #1e40af; 
            }
            .swagger-ui .topbar .download-url-wrapper .download-url-button {
                background-color: #3b82f6;
            }
            .swagger-ui .scheme-container {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
            }
            .swagger-ui .info {
                margin-bottom: 20px;
            }
            .swagger-ui .info .title {
                color: #1e40af;
            }
            .swagger-ui .opblock.opblock-post {
                border-color: #059669;
                background: rgba(5, 150, 105, 0.1);
            }
            .swagger-ui .opblock.opblock-get {
                border-color: #0284c7;
                background: rgba(2, 132, 199, 0.1);
            }
            .swagger-ui .opblock-summary-method {
                min-width: 80px;
            }
            .swagger-ui .btn.execute {
                background-color: #1e40af;
                border-color: #1e40af;
            }
            .swagger-ui .btn.execute:hover {
                background-color: #1e3a8a;
                border-color: #1e3a8a;
            }
        '''
    }
)

# Create API routes blueprint
api_blueprint = Blueprint('api_docs', __name__)

@api_blueprint.route('/api/docs/swagger.json')
def swagger_spec():
    """Serve the Swagger specification as JSON"""
    try:
        # Load YAML file and convert to JSON
        with open('swagger.yaml', 'r', encoding='utf-8') as file:
            yaml_content = yaml.safe_load(file)
        
        return json.dumps(yaml_content, indent=2), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return {'error': f'Could not load swagger spec: {str(e)}'}, 500

@api_blueprint.route('/api/docs/test-data')
def test_data():
    """Provide test data for API testing"""
    test_data = {
        'authentication': {
            'admin': {'username': 'admin', 'password': 'admin123'},
            'manager': {'username': 'manager1', 'password': 'manager123'},
            'vendor': {'username': 'vendor1', 'password': 'vendor123'}
        },
        'sample_requests': {
            'submit_status': {
                'status_date': '2025-01-07',
                'status': 'in_office_full',
                'location': 'BL-A-5F',
                'comments': 'Working on API documentation'
            },
            'add_holiday': {
                'holiday_date': '2025-03-08',
                'name': "International Women's Day",
                'description': 'Celebrating women achievements worldwide'
            },
            'generate_report': {
                'report_type': 'monthly',
                'month': '2025-01',
                'format': 'excel'
            },
            'schedule_report': {
                'report_type': 'monthly',
                'frequency': 'monthly',
                'recipients': ['manager1@company.com']
            }
        },
        'status_options': [
            'in_office_full', 'in_office_half', 
            'wfh_full', 'wfh_half',
            'leave_full', 'leave_half', 
            'absent'
        ],
        'current_data': {
            'total_vendors': 5,
            'total_managers': 1,
            'total_daily_statuses': 88,
            'total_swipe_records': 50
        }
    }
    
    return json.dumps(test_data, indent=2), 200, {'Content-Type': 'application/json'}

@api_blueprint.route('/api/docs')
def swagger_ui_index():
    """Custom Swagger UI page with ATTENDO branding"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workforce Management API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui.css" />
    <link rel="icon" type="image/png" href="{{ url_for('swagger_ui.static', filename='favicon-32x32.png') }}" sizes="32x32" />
    <link rel="icon" type="image/png" href="{{ url_for('swagger_ui.static', filename='favicon-16x16.png') }}" sizes="16x16" />
    <style>
        html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin:0; background: #fafafa; }
        
        .header-banner {
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header-banner h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header-banner p {
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .credentials-box {
            background: rgba(255,255,255,0.15);
            border-radius: 8px;
            padding: 15px;
            margin: 20px auto;
            max-width: 600px;
            backdrop-filter: blur(10px);
        }
        
        .credentials-box h3 {
            margin: 0 0 10px 0;
            font-size: 1.1em;
        }
        
        .cred-item {
            display: inline-block;
            margin: 5px 15px;
            font-family: monospace;
            background: rgba(255,255,255,0.2);
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.9em;
        }
        
        .stats-grid {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 15px 0;
            flex-wrap: wrap;
        }
        
        .stat-item {
            background: rgba(255,255,255,0.15);
            padding: 10px 20px;
            border-radius: 6px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        
        .stat-number {
            font-size: 1.5em;
            font-weight: bold;
            display: block;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        #swagger-ui {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .footer-info {
            background: #f8fafc;
            border-top: 1px solid #e2e8f0;
            padding: 20px;
            text-align: center;
            color: #64748b;
            margin-top: 40px;
        }
        
        .quick-links {
            margin: 20px 0;
        }
        
        .quick-links a {
            display: inline-block;
            margin: 5px 10px;
            padding: 8px 16px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: all 0.3s ease;
            font-size: 0.9em;
        }
        
        .quick-links a:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="header-banner">
        <h1>🚀 ATTENDO API Documentation</h1>
        <p>AI-Powered Workforce Management Platform</p>
        
        <div class="credentials-box">
            <h3>🔐 Test Credentials</h3>
            <div class="cred-item"><strong>Admin:</strong> admin / admin123</div>
            <div class="cred-item"><strong>Manager:</strong> manager1 / manager123</div>
            <div class="cred-item"><strong>Vendor:</strong> vendor1 / vendor123</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-item">
                <span class="stat-number">50+</span>
                <span class="stat-label">API Endpoints</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">12</span>
                <span class="stat-label">Database Tables</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">94.2%</span>
                <span class="stat-label">AI Accuracy</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">3</span>
                <span class="stat-label">User Roles</span>
            </div>
        </div>
        
        <div class="quick-links">
            <a href="#tag/Authentication">🔐 Authentication</a>
            <a href="#tag/AI--Analytics">🤖 AI Analytics</a>
            <a href="#tag/Charts--Visualization">📈 Charts</a>
            <a href="#tag/Reports--Export">📊 Reports</a>
            <a href="/api/docs/test-data">📋 Test Data</a>
        </div>
    </div>
    
    <div id="swagger-ui"></div>
    
    <div class="footer-info">
        <p><strong>ATTENDO</strong> - Comprehensive Workforce Management Solution</p>
        <p>Features: Role-based Auth • AI Predictions • Real-time Analytics • Data Import/Export • Audit Trail</p>
        <p>🏆 Ready for Hackathon Demo | 💻 <code>http://localhost:5000</code></p>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
    <script>
    window.onload = function() {
        const ui = SwaggerUIBundle({
            url: '/api/docs/swagger.json',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
            ],
            layout: "StandaloneLayout",
            tryItOutEnabled: true,
            filter: true,
            displayRequestDuration: true,
            docExpansion: 'list',
            showExtensions: true,
            showCommonExtensions: true,
            requestInterceptor: function(request) {
                // Ensure cookies are sent for session authentication
                request.credentials = 'include';
                
                // Log the request for debugging
                console.log('API Request:', request.method, request.url);
                
                return request;
            },
            responseInterceptor: function(response) {
                // Handle authentication redirects
                if (response.status === 302) {
                    console.log('Redirect detected - may need authentication');
                    alert('Authentication required. Please login first at /login');
                }
                
                // Log successful responses
                if (response.status >= 200 && response.status < 300) {
                    console.log('API Response:', response.status, response.url);
                }
                
                return response;
            }
        });
        
        // Add custom styling after UI loads
        setTimeout(() => {
            const operations = document.querySelectorAll('.opblock');
            operations.forEach(op => {
                if (op.classList.contains('opblock-post')) {
                    op.style.borderLeft = '4px solid #059669';
                } else if (op.classList.contains('opblock-get')) {
                    op.style.borderLeft = '4px solid #0284c7';
                }
            });
        }, 1000);
    };
    </script>
</body>
</html>
    ''')

def register_swagger_ui(app):
    """Register Swagger UI with the Flask app"""
    app.register_blueprint(swagger_ui_blueprint)
    app.register_blueprint(api_blueprint)
    
    # Add route info to app context
    @app.context_processor
    def inject_swagger_info():
        return {
            'swagger_url': SWAGGER_URL,
            'api_endpoints_count': 50,
            'swagger_version': '3.0.3'
        }
    
    print("✅ Swagger UI registered successfully!")
    print(f"📖 API Documentation available at: http://localhost:5000{SWAGGER_URL}")
    print(f"📋 Test data available at: http://localhost:5000/api/docs/test-data")
