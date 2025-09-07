#!/usr/bin/env python3

from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def test():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Simple Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
    <div class="container d-flex align-items-center justify-content-center" style="min-height: 100vh;">
        <div class="card shadow-lg">
            <div class="card-header text-center bg-primary text-white">
                <h3>🎉 Hackathon Login Test</h3>
            </div>
            <div class="card-body p-5">
                <form>
                    <div class="mb-3">
                        <label class="form-label">Username:</label>
                        <input type="text" class="form-control" placeholder="admin">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password:</label>
                        <input type="password" class="form-control" placeholder="admin123">
                    </div>
                    <button type="button" class="btn btn-primary w-100">Login</button>
                </form>
                <hr>
                <h5 class="text-center">Demo Credentials:</h5>
                <div class="text-center">
                    <p><strong>Admin:</strong> admin/admin123</p>
                    <p><strong>Manager:</strong> manager1/manager123</p>
                    <p><strong>Vendor:</strong> vendor1/vendor123</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    print("🧪 Simple HTML Test - Visit: http://localhost:5001")
    app.run(debug=True, port=5001)
