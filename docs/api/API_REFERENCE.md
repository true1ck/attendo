# ATTENDO API Reference

## Overview

The ATTENDO API provides programmatic access to all system functionality through RESTful endpoints. The API is organized into logical blueprints with consistent response formats.

## Authentication

All API endpoints require authentication except for the login endpoint. Authentication is handled through Flask-Login sessions.

### Login
```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| POST   | `/login` | User authentication | Public |
| POST   | `/logout` | User logout | Authenticated |
| GET    | `/` | Redirect to dashboard | Authenticated |

### Vendor Endpoints

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| GET    | `/vendor/dashboard` | Vendor dashboard | Vendor |
| POST   | `/vendor/submit-status` | Submit daily attendance | Vendor |
| POST   | `/vendor/mismatch/{id}/explain` | Explain attendance mismatch | Vendor |

### Manager Endpoints

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| GET    | `/manager/dashboard` | Manager dashboard | Manager |
| POST   | `/manager/approve-status/{id}` | Approve/reject status | Manager |
| POST   | `/manager/review-mismatch/{id}` | Review mismatch explanation | Manager |
| GET    | `/manager/team-report` | Generate team report | Manager |

### Admin Endpoints

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| GET    | `/admin/dashboard` | Admin dashboard | Admin |
| GET    | `/admin/vendors` | Manage vendor profiles | Admin |
| GET    | `/admin/holidays` | Manage holidays | Admin |
| POST   | `/admin/add-holiday` | Add new holiday | Admin |
| GET    | `/admin/import-data` | Import external data | Admin |
| POST   | `/admin/import-data` | Process data import | Admin |
| GET    | `/admin/reports` | System reports | Admin |
| GET    | `/admin/audit-logs` | View audit trail | Admin |
| GET    | `/admin/ai-insights` | AI analytics dashboard | Admin |
| GET    | `/admin/reports-dashboard` | Reports dashboard | Admin |

### API Data Endpoints

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| GET    | `/api/dashboard/stats` | Dashboard statistics | Authenticated |
| GET    | `/api/notifications/unread` | Unread notifications | Authenticated |
| POST   | `/api/notifications/{id}/read` | Mark notification read | Authenticated |

### Chart Data Endpoints

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| GET    | `/api/charts/attendance-trends` | Attendance trends data | Manager/Admin |
| GET    | `/api/charts/team-performance` | Team performance metrics | Manager/Admin |
| GET    | `/api/charts/status-distribution` | Status distribution data | Manager/Admin |

### Report Endpoints

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| POST   | `/api/reports/schedule` | Schedule automatic reports | Manager/Admin |
| POST   | `/api/reports/generate` | Generate report on demand | Manager/Admin |
| GET    | `/api/reports/history` | Report generation history | Manager/Admin |

### AI Insights Endpoints

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| POST   | `/api/ai/refresh-predictions` | Refresh AI predictions | Manager/Admin |
| POST   | `/api/ai/train-model` | Retrain AI model | Admin |
| POST   | `/api/ai/export-insights` | Export AI insights | Manager/Admin |

### Export Endpoints

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| GET    | `/export/monthly-report/{format}` | Export monthly report | Manager/Admin |

## Response Formats

### Success Response
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "code": 400
}
```

### Chart Data Response
```json
{
  "labels": ["2024-01-01", "2024-01-02", ...],
  "datasets": [
    {
      "label": "In Office",
      "data": [10, 12, 8, ...],
      "backgroundColor": "#16a34a"
    }
  ]
}
```

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Standard endpoints: 100 requests per minute
- Authentication endpoints: 10 requests per minute
- Report generation: 5 requests per minute

## Interactive API Documentation

The full interactive API documentation is available at `/api/docs` when the application is running. This provides:

- Complete endpoint documentation
- Request/response examples
- Interactive testing interface
- Authentication testing with sample credentials

## SDK and Integration

The API follows REST conventions and can be integrated with any HTTP client. Sample code and SDKs are available for:

- Python (requests library)
- JavaScript (fetch API)
- cURL command examples

## Webhooks

Future versions will support webhooks for:
- Attendance submission notifications
- Approval status changes
- Mismatch detection alerts
- Report generation completion
