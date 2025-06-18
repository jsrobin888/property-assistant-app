"""
Updated main routes file that imports the new API structure
This replaces your existing routes.py file
"""

from fastapi import APIRouter
from .routes.emails import router as emails_router
from .routes.tickets import router as tickets_router
from .routes.workflows import router as workflows_router
from .routes.database import router as database_router

# Create main router
router = APIRouter()

# Include all sub-routers with proper prefixes
router.include_router(emails_router, prefix="/emails", tags=["Email Management"])
router.include_router(tickets_router, prefix="/tickets", tags=["Ticket Management"])
router.include_router(workflows_router, prefix="/workflows", tags=["Workflow Control"])
router.include_router(database_router, prefix="/database", tags=["Database Operations"])

@router.get("/")
async def api_root():
    """API root endpoint with comprehensive route information"""
    return {
        "message": "Property Management API v1.0",
        "description": "Complete email processing and ticket management system",
        "version": "1.0.0",
        "documentation": "/docs",
        "available_endpoints": {
            "workflows": {
                "base_url": "/api/v1/workflows",
                "description": "Email processing workflow control",
                "key_endpoints": {
                    "POST /process-emails": "Trigger complete email processing workflow",
                    "POST /fetch-gmail": "Fetch emails from Gmail",
                    "GET /status/{workflow_id}": "Get workflow status",
                    "POST /create-tickets-from-email": "Create tickets from email",
                    "GET /health-check": "Check system health"
                }
            },
            "emails": {
                "base_url": "/api/v1/emails",
                "description": "Email management and operations",
                "key_endpoints": {
                    "GET /": "List emails with filtering",
                    "GET /{email_id}": "Get email details",
                    "PUT /{email_id}/status": "Update email status",
                    "GET /ai-responses/pending": "Get pending AI responses",
                    "POST /{email_id}/ai-responses/select": "Select AI response",
                    "GET /analytics/summary": "Email analytics"
                }
            },
            "tickets": {
                "base_url": "/api/v1/tickets",
                "description": "Ticket management system", 
                "key_endpoints": {
                    "GET /": "List tickets with filtering",
                    "GET /{ticket_id}": "Get ticket details",
                    "PUT /{ticket_id}": "Update ticket",
                    "GET /stats/summary": "Ticket statistics",
                    "POST /batch/assign": "Bulk assign tickets",
                    "GET /search/{query}": "Search tickets"
                }
            },
            "database": {
                "base_url": "/api/v1/database",
                "description": "Direct database CRUD operations",
                "key_endpoints": {
                    "GET /stats": "Database statistics",
                    "GET /emails": "CRUD operations on emails table",
                    "GET /tenants": "CRUD operations on tenants table",
                    "GET /action-items": "CRUD operations on action items",
                    "POST /bulk/delete-emails": "Bulk delete operations"
                }
            }
        },
        "workflow_summary": {
            "1_fetch_emails": "POST /workflows/fetch-gmail - Fetch emails from Gmail",
            "2_process_emails": "POST /workflows/process-emails - Complete email processing",
            "3_manage_responses": "GET /emails/ai-responses/pending - Review and select AI responses",
            "4_manage_tickets": "GET /tickets/ - View and manage created tickets",
            "5_analytics": "GET /emails/analytics/summary - View system analytics"
        }
    }

@router.get("/health")
async def health_check():
    """Overall API health check"""
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "services": {
            "workflows": "available",
            "emails": "available", 
            "tickets": "available",
            "database": "available"
        },
        "timestamp": "2025-06-17T10:30:00Z"
    }

# Legacy compatibility - include original mock endpoints
@router.get("/test")
async def test_endpoint():
    """Test endpoint for backward compatibility"""
    return {
        "message": "Property Management API is working!",
        "version": "1.0.0",
        "note": "This is the updated API with full workflow support",
        "new_features": [
            "Complete email processing workflow",
            "Ticket management system",
            "Database CRUD operations", 
            "AI response management",
            "Analytics and reporting"
        ]
    }