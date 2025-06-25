# Corrected API Endpoints Reference

Based on the current FastAPI implementation, the following are the available API endpoints. For a complete list, visit the interactive API documentation at http://0.0.0.0:8000/docs [http://127.0.0.1:8000/docs, http://localhost:8000/docs, http://MyDomainAddress/docs], powered by FastAPI's integrated OpenAPI interface.

## Base API Structure

All endpoints are prefixed with `/api/v1` based on the main routes configuration.

---

## Workflow Control API (`/api/v1/workflows`)

### Core Workflow Operations

#### `POST /api/v1/workflows/process-emails`
Trigger the complete email processing workflow.

**Request Body:**
```json
{
  "auto_replay_strategy": null,
  "auto_create_tickets": true,
  "mark_as_read": true
}
```

**Response:**
```json
{
  "workflow_id": "wf_20250617_143022_a1b2c3d4",
  "status": "started",
  "started_at": "2025-06-17T14:30:22",
  "completed_at": null,
  "results": {},
  "errors": []
}
```

#### `GET /api/v1/workflows/status/{workflow_id}`
Get the status of a running workflow.

#### `GET /api/v1/workflows/status`
Get status of all workflows.

#### `POST /api/v1/workflows/fetch-gmail`
Fetch emails from Gmail without processing.

**Request Body:**
```json
{
  "fetch_type": "unread",
  "count": 10,
  "days_back": 7,
  "mark_as_read": false
}
```

#### `POST /api/v1/workflows/process-single-email/{email_id}`
Process a single email by ID.

#### `POST /api/v1/workflows/generate-ai-responses/{email_id}`
Generate AI responses for a specific email.

#### `POST /api/v1/workflows/create-tickets-from-email`
Create tickets from email action items.

**Request Body:**
```json
{
  "email_id": "email_123",
  "force_create": false
}
```

#### `POST /api/v1/workflows/cleanup-old-records`
Clean up old records.

**Query Parameters:**
- `days_old`: Days old for cleanup (default: 30)

#### `GET /api/v1/workflows/health-check`
Check health of all workflow components.

#### `GET /api/v1/workflows/health`
Simple health status endpoint.

---

## Email Management API (`/api/v1/emails`)

### Email Operations

#### `GET /api/v1/emails/`
List emails with comprehensive filtering.

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Number of results (default: 20, max: 100)
- `status`: Filter by email status
- `priority`: Filter by priority level
- `has_tickets`: Filter emails with/without tickets (boolean)
- `has_replies`: Filter emails with/without replies (boolean)

**Response:**
```json
{
  "emails": [
    {
      "id": "email_123",
      "sender": "john.tenant@example.com",
      "subject": "Broken toilet in Unit 3B",
      "status": "processed",
      "priority_level": "high",
      "reply_count": 1,
      "ticket_count": 1,
      "has_pending_ai_responses": false,
      "received_at": "2025-06-17T14:30:22Z"
    }
  ],
  "total": 145,
  "skip": 0,
  "limit": 20,
  "filters": {
    "status": null,
    "priority": null,
    "has_tickets": null,
    "has_replies": null
  }
}
```

#### `GET /api/v1/emails/{email_id}`
Get comprehensive email details.

#### `PUT /api/v1/emails/{email_id}/status`
Update email status.

**Request Body:**
```json
{
  "status": "processed",
  "notes": "Maintenance ticket created"
}
```

### AI Response Management

#### `GET /api/v1/emails/ai-responses/pending`
Get all emails with pending AI response selections.

#### `GET /api/v1/emails/{email_id}/ai-responses`
Get AI response options for a specific email.

#### `POST /api/v1/emails/{email_id}/ai-responses/select`
Select an AI response option.

**Request Body:**
```json
{
  "option_id": "opt_789",
  "rating": 4.5,
  "modifications": "Added emergency contact number"
}
```

#### `POST /api/v1/emails/{email_id}/regenerate-ai-responses`
Generate new AI responses for an email.

### Email Search and Analytics

#### `POST /api/v1/emails/search`
Advanced email search.

**Request Body:**
```json
{
  "query": "toilet broken",
  "search_fields": ["subject", "body", "sender"],
  "limit": 50
}
```

#### `GET /api/v1/emails/analytics/summary`
Get email analytics and summary statistics.

#### `GET /api/v1/emails/analytics/trends`
Get email trends over time.

**Query Parameters:**
- `days`: Number of days to analyze (default: 30, max: 365)

### Email Workflow Operations

#### `POST /api/v1/emails/{email_id}/reprocess`
Reprocess an email through the complete workflow.

#### `GET /api/v1/emails/{email_id}/workflow-status`
Get comprehensive workflow status for an email.

### Bulk Email Operations

#### `POST /api/v1/emails/bulk/update-status`
Update status for multiple emails.

**Request Body:**
```json
{
  "email_ids": ["email_123", "email_124"],
  "new_status": "processed",
  "notes": "Batch processed"
}
```

#### `POST /api/v1/emails/bulk/generate-ai-responses`
Generate AI responses for multiple emails.

**Request Body:**
```json
{
  "email_ids": ["email_123", "email_124"]
}
```

#### `GET /api/v1/emails/health`
Email service health check.

---

## Ticket Management API (`/api/v1/tickets`)

**Note:** The tickets router has `prefix="/tickets"` in addition to the base `/api/v1`, so all endpoints are at `/api/v1/tickets/tickets/...`

### Ticket Operations

#### `GET /api/v1/tickets/tickets/`
Get tickets with optional filtering.

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Number of results (default: 100, max: 1000)
- `status`: Filter by ticket status
- `category`: Filter by category
- `urgency`: Filter by urgency level

#### `GET /api/v1/tickets/tickets/{ticket_id}`
Get a specific ticket by ID.

#### `PUT /api/v1/tickets/tickets/{ticket_id}`
Update a ticket.

**Request Body:**
```json
{
  "status": "In Progress",
  "assigned_to": "john.technician@property.com",
  "assignment_group": "Maintenance Team",
  "notes": "Technician dispatched"
}
```

### Ticket Statistics

#### `GET /api/v1/tickets/tickets/stats/summary`
Get ticket statistics summary.

#### `GET /api/v1/tickets/tickets/stats/report`
Get comprehensive ticket report.

### Ticket Search and Utilities

#### `GET /api/v1/tickets/tickets/search/{query}`
Search tickets by content.

**Query Parameters:**
- `limit`: Maximum results (default: 20, max: 100)

#### `GET /api/v1/tickets/tickets/open/list`
Get all open tickets.

#### `GET /api/v1/tickets/tickets/categories/available`
Get available categories, statuses, and urgency levels.

### Batch Operations

#### `POST /api/v1/tickets/tickets/batch/assign`
Assign multiple tickets.

**Request Body:**
```json
{
  "ticket_ids": ["TKT-A1B2C3D4", "TKT-B2C3D4E5"],
  "assigned_to": "john.technician@property.com",
  "assignment_group": "Maintenance Team"
}
```

#### `POST /api/v1/tickets/tickets/batch/update-status`
Update status for multiple tickets.

**Request Body:**
```json
{
  "ticket_ids": ["TKT-A1B2C3D4", "TKT-B2C3D4E5"],
  "status": "Resolved",
  "notes": "Maintenance completed"
}
```

#### `GET /api/v1/tickets/tickets/export/csv`
Export tickets to CSV format.

**Query Parameters:**
- `status`: Filter by status
- `category`: Filter by category

#### `GET /api/v1/tickets/tickets/health`
Ticket service health check.

---

## Database Operations API (`/api/v1/database`)

### Database Statistics

#### `GET /api/v1/database/stats`
Get comprehensive database statistics.

#### `GET /api/v1/database/tables`
List all database tables and their information.

### Emails Table CRUD

#### `GET /api/v1/database/emails`
Get all emails with filtering and pagination.

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Number of results (default: 100, max: 1000)
- `status`: Filter by email status
- `sender`: Filter by sender (partial match)

#### `GET /api/v1/database/emails/{email_id}`
Get specific email by ID with related data.

#### `POST /api/v1/database/emails`
Create a new email record.

**Request Body:**
```json
{
  "sender": "tenant@example.com",
  "subject": "Issue with heating",
  "body": "The heating in my unit is not working...",
  "status": "unprocessed",
  "priority_level": "medium",
  "context_labels": ["maintenance", "heating"]
}
```

#### `PUT /api/v1/database/emails/{email_id}`
Update an email record.

#### `DELETE /api/v1/database/emails/{email_id}`
Delete an email and all related data.

### Tenants Table CRUD

#### `GET /api/v1/database/tenants`
Get all tenants.

#### `GET /api/v1/database/tenants/{tenant_id}`
Get specific tenant by ID.

#### `POST /api/v1/database/tenants`
Create a new tenant.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "unit": "3B",
  "phone": "+1234567890",
  "rent_amount": 1500.00
}
```

#### `GET /api/v1/database/tenants/by-email/{email}`
Get tenant by email address.

### Action Items Table CRUD

#### `GET /api/v1/database/action-items`
Get all action items with filtering.

**Query Parameters:**
- `status`: Filter by action item status
- `email_id`: Filter by email ID

#### `GET /api/v1/database/action-items/{item_id}`
Get specific action item by ID.

#### `POST /api/v1/database/action-items`
Create a new action item.

**Request Body:**
```json
{
  "email_id": "email_123",
  "action_data": {
    "action": "create_maintenance_ticket",
    "category": "maintenance",
    "priority": "high"
  },
  "status": "open"
}
```

### Replies Table CRUD

#### `GET /api/v1/database/replies`
Get all replies.

**Query Parameters:**
- `email_id`: Filter by email ID

#### `GET /api/v1/database/replies/{reply_id}`
Get specific reply by ID.

#### `POST /api/v1/database/replies`
Create a new reply.

**Request Body:**
```json
{
  "email_id": "email_123",
  "content": "Thank you for your inquiry...",
  "strategy_used": "template",
  "sent": false
}
```

### AI Responses Table CRUD

#### `GET /api/v1/database/ai-responses`
Get all AI responses with filtering.

**Query Parameters:**
- `status`: Filter by AI response status
- `email_id`: Filter by email ID

#### `GET /api/v1/database/ai-responses/{response_id}`
Get specific AI response by ID.

### Bulk Database Operations

#### `POST /api/v1/database/bulk/delete-emails`
Delete multiple emails and their related data.

**Request Body:**
```json
{
  "email_ids": ["email_123", "email_124", "email_125"]
}
```

#### `POST /api/v1/database/bulk/update-action-items-status`
Update status for multiple action items.

**Request Body:**
```json
{
  "item_ids": ["item_123", "item_124"],
  "new_status": "closed"
}
```

### Database Search and Reports

#### `GET /api/v1/database/search/emails`
Search emails by content.

**Query Parameters:**
- `query`: Search query string
- `search_in`: Fields to search ("subject", "body", "sender", "all")
- `limit`: Maximum results (default: 50, max: 200)

#### `GET /api/v1/database/reports/daily-summary`
Get daily summary report.

**Query Parameters:**
- `date`: Date in YYYY-MM-DD format (optional, defaults to today)

#### `GET /api/v1/database/health`
Database service health check.

---

## Main API Root Endpoints

### API Information

#### `GET /api/v1/`
API root endpoint with comprehensive route information.

#### `GET /api/v1/health`
Overall API health check.

#### `GET /api/v1/test`
Test endpoint for backward compatibility.

### Application Root

#### `GET /`
Application root endpoint.

#### `GET /health`
Application health check.

---

## Key Corrections Made

1. **Ticket API Prefix Issue**: The tickets router has an additional `/tickets` prefix, making all endpoints `/api/v1/tickets/tickets/...`

2. **Missing Health Endpoints**: Added the `/health` endpoints that exist in each router.

3. **Corrected Request/Response Models**: Updated to match actual Pydantic models in the code.

4. **Query Parameters**: Corrected the actual query parameter names and types.

5. **Bulk Operations**: Updated to match actual implementation structure.

6. **Database API Structure**: Corrected the database CRUD operations to match the actual implementation.

7. **Missing Endpoints**: Added missing endpoints like `/test`, root endpoints, and various utility endpoints.

8. **Router Prefixes**: Properly documented the actual URL structure with correct prefixes.

## Common Response Patterns

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {...}
}
```

### Error Response
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### Pagination Response
```json
{
  "items": [...],
  "total": 100,
  "skip": 0,
  "limit": 20
}
```

This corrected documentation now accurately reflects the actual FastAPI implementation in your codebase.