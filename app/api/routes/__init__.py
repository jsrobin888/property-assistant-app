"""
Main API router that combines all route modules
"""

from fastapi import APIRouter
from .emails import router as emails_router
from .tickets import router as tickets_router
from .workflows import router as workflows_router
from .database import router as database_router

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(emails_router, prefix="/emails", tags=["Email Management"])
router.include_router(tickets_router, prefix="/tickets", tags=["Ticket Management"]) 
router.include_router(workflows_router, prefix="/workflows", tags=["Workflow Control"])
router.include_router(database_router, prefix="/database", tags=["Database Operations"])

@router.get("/")
async def api_root():
    """API root endpoint with available routes"""
    return {
        "message": "Property Management API",
        "version": "1.0.0",
        "available_endpoints": {
            "emails": {
                "base": "/api/v1/emails",
                "description": "Email processing and management"
            },
            "tickets": {
                "base": "/api/v1/tickets", 
                "description": "Ticket management and CRUD operations"
            },
            "workflows": {
                "base": "/api/v1/workflows",
                "description": "Workflow control and email processing triggers"
            },
            "database": {
                "base": "/api/v1/database",
                "description": "Direct database CRUD operations"
            }
        }
    }