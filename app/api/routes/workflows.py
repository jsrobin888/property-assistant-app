"""
Workflow Control API - Triggers email processing and workflow components
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging

# Import your email processing functions
from ...plugin.email.process_emails import (
    process_new_emails, 
    get_email_by_id, 
    get_recent_emails,
    cleanup_old_records
)
from ...plugin.email.gmail_client import GmailClient
from ...plugin.email.email_processor import EmailProcessor
from ...plugin.ai.ai_response import LangChainAIResponder, save_ai_responses_to_waiting_zone
from ...plugin.tickets.manager import Ticket, push_ticket
from ...llm_config import llm_config

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models for API requests
class EmailProcessingRequest(BaseModel):
    auto_replay_strategy: Optional[str] = Field(None, description="Auto-reply strategy: 'strategy_used' or None")
    auto_create_tickets: bool = Field(True, description="Whether to automatically create tickets")
    mark_as_read: bool = Field(True, description="Whether to mark emails as read after processing")

class GmailFetchRequest(BaseModel):
    fetch_type: str = Field("unread", description="Type of fetch: 'unread', 'recent', 'count', 'since_date'")
    count: Optional[int] = Field(None, description="Number of emails to fetch (for count type)")
    days_back: Optional[int] = Field(None, description="Days back to fetch (for recent type)")
    mark_as_read: bool = Field(False, description="Whether to mark fetched emails as read")

class TicketCreationRequest(BaseModel):
    email_id: str = Field(..., description="Email ID to create tickets from")
    force_create: bool = Field(False, description="Force create even if tickets already exist")

class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    results: Dict[str, Any]
    errors: List[str] = []

# Workflow status tracking (in-memory for simplicity)
workflow_status = {}

def generate_workflow_id() -> str:
    """Generate unique workflow ID"""
    import uuid
    return f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

# ============================================================================
# MAIN EMAIL PROCESSING WORKFLOW
# ============================================================================

@router.post("/process-emails", response_model=WorkflowStatusResponse)
async def trigger_email_processing(
    request: EmailProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger the complete email processing workflow
    This is the main API endpoint that triggers process_new_emails()
    """
    workflow_id = generate_workflow_id()
    
    # Initialize workflow status
    workflow_status[workflow_id] = {
        "workflow_id": workflow_id,
        "status": "started",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "results": {},
        "errors": []
    }
    
    # Run email processing in background
    background_tasks.add_task(
        run_email_processing_workflow,
        workflow_id,
        request.auto_replay_strategy,
        request.auto_create_tickets
    )
    
    return WorkflowStatusResponse(**workflow_status[workflow_id])

async def run_email_processing_workflow(
    workflow_id: str, 
    auto_replay_strategy: Optional[str], 
    auto_create_tickets: bool
):
    """Run the complete email processing workflow"""
    try:
        logger.info(f"Starting email processing workflow {workflow_id}")
        
        # Update status
        workflow_status[workflow_id]["status"] = "processing"
        
        # Run the main email processing function
        process_new_emails(
            auto_replay_strategy=auto_replay_strategy,
            auto_create_tickets=auto_create_tickets
        )
        
        # Get results
        recent_emails = get_recent_emails(5)
        
        # Update status with results
        workflow_status[workflow_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "results": {
                "emails_processed": len(recent_emails),
                "recent_emails": [
                    {
                        "id": email.get("id", "unknown"),
                        "sender": email.get("sender"),
                        "subject": email.get("subject"),
                        "tickets_created": email.get("tickets_created", [])
                    }
                    for email in recent_emails
                ]
            }
        })
        
        logger.info(f"Completed email processing workflow {workflow_id}")
        
    except Exception as e:
        logger.error(f"Error in email processing workflow {workflow_id}: {e}")
        workflow_status[workflow_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "errors": [str(e)]
        })

@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """Get the status of a workflow"""
    if workflow_id not in workflow_status:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return WorkflowStatusResponse(**workflow_status[workflow_id])

@router.get("/status", response_model=List[WorkflowStatusResponse])
async def get_all_workflow_status():
    """Get status of all workflows"""
    return [WorkflowStatusResponse(**status) for status in workflow_status.values()]

# ============================================================================
# INDIVIDUAL WORKFLOW COMPONENTS
# ============================================================================

@router.post("/fetch-gmail")
async def fetch_gmail_emails(request: GmailFetchRequest):
    """
    Fetch emails from Gmail without processing them
    Allows granular control over email fetching
    """
    try:
        gmail_client = GmailClient()
        
        if request.fetch_type == "unread":
            emails = gmail_client.fetch_unread()
        elif request.fetch_type == "recent":
            emails = gmail_client.fetch_recent(days_back=request.days_back or 1)
        elif request.fetch_type == "count":
            emails = gmail_client.fetch_recent(count=request.count or 10)
        else:
            raise HTTPException(status_code=400, detail="Invalid fetch_type")
        
        return {
            "success": True,
            "fetch_type": request.fetch_type,
            "emails_fetched": len(emails),
            "emails": [
                {
                    "sender": email.get("sender"),
                    "subject": email.get("subject"),
                    "date": email.get("date").isoformat() if email.get("date") else None,
                    "preview": email.get("body", "")[:100] + "..." if email.get("body") else ""
                }
                for email in emails
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching Gmail emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")

@router.post("/process-single-email/{email_id}")
async def process_single_email(email_id: str):
    """
    Process a single email by ID
    """
    try:
        # Get email from database
        email = get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        logger.info(f"Processing email {email_id}: {email.get('subject', 'No subject')}")
        
        # FIX: Use EmailProcessor to properly process the email
        from ...plugin.email.email_processor import EmailProcessor
        email_processor = EmailProcessor()
        
        # Prepare email data for processing
        email_data = {
            "sender": email.get("sender"),
            "subject": email.get("subject"), 
            "body": email.get("content", "") or email.get("body", "")  # Try both fields
        }
        
        logger.info(f"Email data: sender={email_data['sender']}, subject={email_data['subject']}, body_length={len(email_data['body'])}")
        
        # FIX: Don't create a new email, just extract action items from existing one
        action_items = email_processor._extract_action_items(email_data, email_id)
        
        logger.info(f"Extracted {len(action_items)} action items")
        
        # Save action items to database
        from ...models import ActionItem, ActionStatus
        for action_data in action_items:
            ActionItem.create(
                email_id=email_id,
                action_data=action_data,
                status=ActionStatus.OPEN
            )
            logger.info(f"Saved action item: {action_data.get('action', 'unknown')}")
        
        # Update email status to processed
        from ...models import EmailMessage, EmailStatus
        EmailMessage.update_status(email_id, EmailStatus.PROCESSED)
        
        # Update email record with processing info
        from ...models import emails_table
        from app.services.tinydb_wrapper_supabase import Query
        Email = Query()
        
        emails_table.update({
            'action_items_count': len(action_items),
            'status': EmailStatus.PROCESSED.value,
            'processed_at': datetime.now().isoformat()
        }, Email.id == email_id)
        
        processing_result = {
            'email_id': email_id,
            'action_items_count': len(action_items),
            'status': EmailStatus.PROCESSED.value,
            'processed_at': datetime.now().isoformat()
        }
        
        logger.info(f"Successfully processed email {email_id}")
        
        return {
            "success": True,
            "email_id": email_id,
            "processing_result": processing_result
        }
        
    except Exception as e:
        logger.error(f"Error processing single email {email_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-ai-responses/{email_id}")
async def generate_ai_responses_for_email(email_id: str):
    """
    Generate AI responses for a specific email
    Separated from main workflow for granular control
    """
    try:
        # Get email from database
        email = get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Initialize AI responder
        config = llm_config
        ai_responder = LangChainAIResponder(config)
        
        # Generate responses
        email_data = {
            "sender": email.get("sender"),
            "subject": email.get("subject"),
            "body": email.get("content", "")
        }
        
        response_options = ai_responder.generate_reply(email_data, email_id)
        
        # Save to waiting zone
        ai_response_id = save_ai_responses_to_waiting_zone(email_id, response_options)
        
        return {
            "success": True,
            "email_id": email_id,
            "ai_response_id": ai_response_id,
            "response_count": len(response_options),
            "responses": [
                {
                    "option_id": resp["option_id"],
                    "strategy": resp["strategy_used"],
                    "provider": resp["provider"],
                    "confidence": resp["confidence"],
                    "preview": resp["content"][:100] + "..."
                }
                for resp in response_options
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating AI responses for email {email_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-tickets-from-email")
async def create_tickets_from_email_endpoint(request: TicketCreationRequest):
    """
    Create tickets from a specific email's action items
    """
    try:
        logger.info(f"Creating tickets for email {request.email_id}")
        
        # Get email from database
        email = get_email_by_id(request.email_id)
        if not email:
            logger.error(f"Email {request.email_id} not found")
            raise HTTPException(status_code=404, detail="Email not found")
        
        logger.info(f"Found email: {email.get('subject', 'No subject')}")
        
        # Get action items from database
        from ...models import action_items_table
        from app.services.tinydb_wrapper_supabase import Query
        
        ActionItem = Query()
        action_items = action_items_table.search(ActionItem.email_id == request.email_id)
        
        logger.info(f"Found {len(action_items)} action items for email {request.email_id}")
        
        if not action_items:
            return {
                "success": False,
                "message": f"No action items found for email {request.email_id}",
                "email_id": request.email_id,
                "tickets_created": [],
                "ticket_count": 0
            }
        
        # Check if tickets already exist
        existing_tickets = email.get("tickets_created", [])
        if existing_tickets and not request.force_create:
            return {
                "success": False,
                "message": "Tickets already exist for this email",
                "existing_tickets": existing_tickets,
                "use_force_create": True
            }
        
        # Prepare email data for ticket creation
        email_data = {
            "sender": email.get("sender"),
            "subject": email.get("subject"),
            "body": email.get("content", "") or email.get("body", ""),
            "id": request.email_id
        }
        
        logger.info(f"Email data prepared: sender={email_data['sender']}")
        
        # Create tickets from action items
        created_tickets = []
        errors = []
        
        for i, action_item in enumerate(action_items):
            try:
                logger.info(f"Creating ticket {i+1}/{len(action_items)} from action item {action_item.get('id')}")
                logger.info(f"Action item data: {action_item.get('action_data', {})}")
                
                # Import ticket classes
                from ...plugin.tickets.manager import Ticket, push_ticket
                
                # Create ticket instance
                ticket = Ticket(email_data, action_item)
                
                # Validate ticket before saving
                if not ticket.validate():
                    error_msg = f"Ticket validation failed for action item {action_item.get('id')}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
                
                # Save ticket
                ticket_id = push_ticket(ticket)
                
                if ticket_id:
                    created_tickets.append(ticket_id)
                    
                    # Update action item with ticket reference
                    action_items_table.update(
                        {
                            'ticket_id': ticket_id, 
                            'ticket_created_at': datetime.now().isoformat()
                        },
                        ActionItem.id == action_item['id']
                    )
                    
                    logger.info(f"✅ Created ticket {ticket_id} from action item {action_item.get('id')}")
                else:
                    error_msg = f"Failed to save ticket for action item {action_item.get('id')}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                
            except Exception as action_error:
                error_msg = f"Error creating ticket from action item {action_item.get('id')}: {action_error}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        # Update email record with created tickets
        if created_tickets:
            from ...models import emails_table
            Email = Query()
            emails_table.update(
                {
                    'tickets_created': created_tickets,
                    'tickets_created_at': datetime.now().isoformat()
                }, 
                Email.id == request.email_id
            )
            logger.info(f"Updated email {request.email_id} with {len(created_tickets)} tickets")
        
        # Return results
        success = len(created_tickets) > 0
        message = f"Created {len(created_tickets)} tickets from {len(action_items)} action items"
        if errors:
            message += f". {len(errors)} errors occurred."
        
        result = {
            "success": success,
            "email_id": request.email_id,
            "tickets_created": created_tickets,
            "ticket_count": len(created_tickets),
            "message": message,
            "action_items_processed": len(action_items)
        }
        
        if errors:
            result["errors"] = errors
        
        return result
        
    except Exception as e:
        logger.error(f"Error in create_tickets_from_email_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WORKFLOW MANAGEMENT
# ============================================================================

@router.post("/cleanup-old-records")
async def cleanup_old_records_endpoint(days_old: int = 30):
    """
    Clean up old email and ticket records
    """
    try:
        cleaned_count = cleanup_old_records(days_old)
        
        return {
            "success": True,
            "days_old": days_old,
            "records_cleaned": cleaned_count,
            "cleanup_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old records: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health-check")
async def workflow_health_check():
    """
    Check the health of all workflow components
    """
    health_status = {
        "overall_status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    try:
        # Test Gmail connection
        try:
            gmail_client = GmailClient()
            connected = gmail_client.connect()
            health_status["components"]["gmail"] = {
                "status": "healthy" if connected else "unhealthy",
                "connected": connected
            }
            if connected:
                gmail_client.disconnect()
        except Exception as e:
            health_status["components"]["gmail"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Test database
        try:
            from ...models import emails_table
            email_count = len(emails_table.all())
            health_status["components"]["database"] = {
                "status": "healthy",
                "email_count": email_count
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
        
        # Test AI responder
        try:
            config = llm_config
            ai_responder = LangChainAIResponder(config)
            available_models = ai_responder.llm_manager.get_available_models()
            health_status["components"]["ai_responder"] = {
                "status": "healthy" if available_models else "degraded",
                "available_models": available_models
            }
        except Exception as e:
            health_status["components"]["ai_responder"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Test ticket system
        try:
            from ...plugin.tickets.models import get_ticket_statistics
            stats = get_ticket_statistics()
            health_status["components"]["ticket_system"] = {
                "status": "healthy",
                "total_tickets": stats.get("total_tickets", 0)
            }
        except Exception as e:
            health_status["components"]["ticket_system"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Determine overall status
        component_statuses = [comp["status"] for comp in health_status["components"].values()]
        if "unhealthy" in component_statuses:
            health_status["overall_status"] = "unhealthy"
        elif "degraded" in component_statuses:
            health_status["overall_status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
@router.get("/health")
async def route_health_status():
  return {"status": "Healthy!"}