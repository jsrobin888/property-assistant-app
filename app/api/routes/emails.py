"""
Email Management API - Fixed for proper ID handling
High-level email operations and management with full TinyDB compatibility
"""

from fastapi import APIRouter, HTTPException, Query as QueryParam
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Import email processing components
from ...plugin.email.process_emails import get_recent_emails, get_replies_for_email
from ...plugin.ai.ai_response import (
    get_pending_ai_responses, 
    select_ai_response,
    LangChainAIResponder
)
from ...models import (
    emails_table, replies_table, ai_responses_table,
    get_document_by_id, update_document_by_id, remove_document_by_id
)
from app.services.tinydb_wrapper_supabase import Query
from ...llm_config import llm_config

router = APIRouter()

# Pydantic models
class AIResponseSelectionRequest(BaseModel):
    option_id: str = Field(..., description="ID of the selected response option")
    rating: Optional[float] = Field(None, description="User rating (1-5)")
    modifications: Optional[str] = Field(None, description="User modifications to the response")

class EmailStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="New status for the email")
    notes: Optional[str] = Field(None, description="Optional notes")

class EmailSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    search_fields: List[str] = Field(["subject", "body", "sender"], description="Fields to search in")
    limit: int = Field(50, description="Maximum results to return")

class BulkUpdateStatusRequest(BaseModel):
    email_ids: List[str] = Field(..., description="List of email IDs to update")
    new_status: str = Field(..., description="New status to set for all emails")
    notes: Optional[str] = Field(None, description="Optional notes for the bulk update")

# Helper function to get email by ID
def get_email_by_id(email_id: str) -> Optional[Dict]:
    """Get email by ID with proper handling of both doc_id and custom id"""
    return get_document_by_id(emails_table, email_id)

# ============================================================================
# EMAIL MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/")
async def list_emails(
    skip: int = QueryParam(0, ge=0),
    limit: int = QueryParam(20, ge=1, le=100),
    status: Optional[str] = QueryParam(None),
    priority: Optional[str] = QueryParam(None),
    has_tickets: Optional[bool] = QueryParam(None),
    has_replies: Optional[bool] = QueryParam(None)
):
    """
    List emails with comprehensive filtering options
    """
    try:
        all_emails = emails_table.all()
        
        # Apply filters
        filtered_emails = all_emails
        
        if status:
            filtered_emails = [e for e in filtered_emails if e.get("status") == status]
        
        if priority:
            filtered_emails = [e for e in filtered_emails if e.get("priority_level") == priority]
        
        if has_tickets is not None:
            if has_tickets:
                filtered_emails = [e for e in filtered_emails if e.get("tickets_created")]
            else:
                filtered_emails = [e for e in filtered_emails if not e.get("tickets_created")]
        
        if has_replies is not None:
            for email in filtered_emails[:]:  # Copy list to modify during iteration
                email_id = email.get("id", str(email.get("doc_id", "")))
                replies = get_replies_for_email(email_id)
                has_reply = len(replies) > 0
                
                if has_replies and not has_reply:
                    filtered_emails.remove(email)
                elif not has_replies and has_reply:
                    filtered_emails.remove(email)
        
        # Sort by received_at (most recent first)
        sorted_emails = sorted(
            filtered_emails,
            key=lambda x: x.get("received_at", ""),
            reverse=True
        )
        
        # Apply pagination
        paginated = sorted_emails[skip:skip + limit]
        
        # Enhance emails with summary data
        enhanced_emails = []
        for email in paginated:
            email_id = email.get("id", str(email.get("doc_id", "")))
            replies = get_replies_for_email(email_id)
            
            enhanced_email = {
                **email,
                "reply_count": len(replies),
                "ticket_count": len(email.get("tickets_created", [])),
                "has_pending_ai_responses": bool(email.get("ai_response_id"))
            }
            enhanced_emails.append(enhanced_email)
        
        return {
            "emails": enhanced_emails,
            "total": len(sorted_emails),
            "skip": skip,
            "limit": limit,
            "filters": {
                "status": status,
                "priority": priority,
                "has_tickets": has_tickets,
                "has_replies": has_replies
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing emails: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing emails: {str(e)}")

@router.get("/{email_id}")
async def get_email_details(email_id: str):
    """
    Get comprehensive email details including all related data
    """
    try:
        # Get email
        email = get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Get the proper email ID for related data
        custom_id = email.get("id", str(email.get("doc_id", "")))
        
        # Get related data
        replies = get_replies_for_email(custom_id)
        
        # Get action items
        from ...models import action_items_table
        ActionItem = Query()
        action_items = action_items_table.search(ActionItem.email_id == custom_id)
        
        # Get AI responses
        AIResponse = Query()
        ai_responses = ai_responses_table.search(AIResponse.email_id == custom_id)
        
        # Get tickets
        tickets_info = []
        if email.get("tickets_created"):
            from ...plugin.tickets.manager import Ticket
            for ticket_id in email["tickets_created"]:
                try:
                    ticket = Ticket.get_by_id(ticket_id)
                    if ticket:
                        tickets_info.append({
                            "ticket_id": ticket_id,
                            "status": ticket.get("status"),
                            "category": ticket.get("category"),
                            "urgency": ticket.get("urgency"),
                            "assigned_to": ticket.get("assigned_to")
                        })
                except Exception as e:
                    logger.warning(f"Error getting ticket {ticket_id}: {e}")
        
        return {
            "email": email,
            "related_data": {
                "replies": replies,
                "action_items": action_items,
                "ai_responses": ai_responses,
                "tickets": tickets_info
            },
            "summary": {
                "reply_count": len(replies),
                "action_item_count": len(action_items),
                "ticket_count": len(tickets_info),
                "ai_response_count": len(ai_responses)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email details for {email_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting email details: {str(e)}")

@router.put("/{email_id}/status")
async def update_email_status(email_id: str, request: EmailStatusUpdateRequest):
    """Update email status"""
    try:
        # Find email
        email = get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Update status
        update_data = {
            "status": request.status,
            "updated_at": datetime.now().isoformat()
        }
        
        if request.notes:
            update_data["status_notes"] = request.notes
        
        # Update in database
        success = update_document_by_id(emails_table, email_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update email status")
        
        return {
            "success": True,
            "email_id": email_id,
            "new_status": request.status,
            "message": "Email status updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email status for {email_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating email status: {str(e)}")

# ============================================================================
# AI RESPONSE MANAGEMENT
# ============================================================================

@router.get("/ai-responses/pending")
async def get_pending_ai_responses_endpoint():
    """Get all emails with pending AI response selections"""
    try:
        pending_responses = get_pending_ai_responses()
        
        # Enhance with email details
        enhanced_responses = []
        for response in pending_responses:
            email_id = response.get("email_id")
            email = get_email_by_id(email_id) if email_id else None
            
            enhanced_response = {
                **response,
                "email_details": {
                    "sender": email.get("sender") if email else "Unknown",
                    "subject": email.get("subject") if email else "Unknown",
                    "received_at": email.get("received_at") if email else None
                },
                "option_count": len(response.get("response_options", []))
            }
            enhanced_responses.append(enhanced_response)
        
        return {
            "pending_responses": enhanced_responses,
            "total": len(enhanced_responses)
        }
        
    except Exception as e:
        logger.error(f"Error getting pending AI responses: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting pending AI responses: {str(e)}")

@router.get("/{email_id}/ai-responses")
async def get_email_ai_responses(email_id: str):
    """Get AI response options for a specific email"""
    try:
        # Check if email exists
        email = get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Get the proper email ID for searching
        custom_id = email.get("id", str(email.get("doc_id", "")))
        
        # Get AI responses
        AIResponse = Query()
        ai_responses = ai_responses_table.search(AIResponse.email_id == custom_id)
        
        if not ai_responses:
            return {
                "email_id": email_id,
                "ai_responses": [],
                "message": "No AI responses found for this email"
            }
        
        return {
            "email_id": email_id,
            "ai_responses": ai_responses,
            "total": len(ai_responses)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI responses for {email_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting AI responses: {str(e)}")

@router.post("/{email_id}/ai-responses/select")
async def select_ai_response_for_email(email_id: str, request: AIResponseSelectionRequest):
    """Select an AI response option for an email"""
    try:
        # Check if email exists
        email = get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Get the proper email ID for the selection
        custom_id = email.get("id", str(email.get("doc_id", "")))
        
        # Select the AI response
        success = select_ai_response(
            email_id=custom_id,  # Use custom ID for AI response functions
            option_id=request.option_id,
            rating=request.rating,
            modifications=request.modifications
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to select AI response")
        
        return {
            "success": True,
            "email_id": email_id,
            "selected_option_id": request.option_id,
            "message": "AI response selected and saved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting AI response for {email_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error selecting AI response: {str(e)}")

@router.post("/{email_id}/regenerate-ai-responses")
async def regenerate_ai_responses(email_id: str):
    """Regenerate AI responses for an email"""
    try:
        # Check if email exists
        email = get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Initialize AI responder
        config = llm_config
        ai_responder = LangChainAIResponder(config)
        
        # Get the proper email ID
        custom_id = email.get("id", str(email.get("doc_id", "")))
        
        # Prepare email data
        email_data = {
            "sender": email.get("sender"),
            "subject": email.get("subject"),
            "body": email.get("content", "") or email.get("body", "")
        }
        
        # Generate new responses
        response_options = ai_responder.generate_reply(email_data, custom_id)
        
        # Save to waiting zone
        from ...plugin.ai.ai_response import save_ai_responses_to_waiting_zone
        ai_response_id = save_ai_responses_to_waiting_zone(custom_id, response_options)
        
        return {
            "success": True,
            "email_id": email_id,
            "ai_response_id": ai_response_id,
            "new_options": len(response_options),
            "message": "New AI responses generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating AI responses for {email_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error regenerating AI responses: {str(e)}")

# ============================================================================
# EMAIL SEARCH AND ANALYTICS
# ============================================================================

@router.post("/search")
async def search_emails(request: EmailSearchRequest):
    """Advanced email search"""
    try:
        all_emails = emails_table.all()
        matching_emails = []
        query_lower = request.query.lower()
        
        for email in all_emails:
            match_found = False
            match_details = []
            
            # Search in specified fields
            for field in request.search_fields:
                field_value = email.get(field, "")
                if isinstance(field_value, str) and query_lower in field_value.lower():
                    match_found = True
                    match_details.append(f"Found in {field}")
            
            # Also search in context labels
            if "context_labels" in request.search_fields or "all" in request.search_fields:
                context_labels = email.get("context_labels", [])
                for label in context_labels:
                    if query_lower in label.lower():
                        match_found = True
                        match_details.append(f"Found in context: {label}")
            
            if match_found:
                email_with_match = {
                    **email,
                    "match_details": match_details
                }
                matching_emails.append(email_with_match)
                
            if len(matching_emails) >= request.limit:
                break
        
        return {
            "query": request.query,
            "search_fields": request.search_fields,
            "results": matching_emails,
            "count": len(matching_emails),
            "limit": request.limit
        }
        
    except Exception as e:
        logger.error(f"Error searching emails: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching emails: {str(e)}")

@router.get("/analytics/summary")
async def get_email_analytics():
    """Get email analytics and summary statistics"""
    try:
        all_emails = emails_table.all()
        
        # Basic counts
        total_emails = len(all_emails)
        
        # Status distribution
        status_counts = {}
        for email in all_emails:
            status = email.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Priority distribution
        priority_counts = {}
        for email in all_emails:
            priority = email.get("priority_level", "unknown")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Context label distribution
        context_counts = {}
        for email in all_emails:
            for label in email.get("context_labels", []):
                context_counts[label] = context_counts.get(label, 0) + 1
        
        # Ticket creation statistics
        emails_with_tickets = [e for e in all_emails if e.get("tickets_created")]
        total_tickets_created = sum(len(e.get("tickets_created", [])) for e in all_emails)
        
        # Recent activity (last 7 days)
        from datetime import datetime, timedelta
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        recent_emails = [e for e in all_emails if e.get("received_at", "") > week_ago]
        
        return {
            "generated_at": datetime.now().isoformat(),
            "overview": {
                "total_emails": total_emails,
                "emails_with_tickets": len(emails_with_tickets),
                "total_tickets_created": total_tickets_created,
                "recent_emails_7days": len(recent_emails)
            },
            "distributions": {
                "by_status": status_counts,
                "by_priority": priority_counts,
                "by_context": context_counts
            },
            "performance_metrics": {
                "ticket_creation_rate": len(emails_with_tickets) / total_emails if total_emails > 0 else 0,
                "avg_tickets_per_email": total_tickets_created / total_emails if total_emails > 0 else 0,
                "weekly_activity": len(recent_emails)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting email analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting email analytics: {str(e)}")

# ============================================================================
# BULK EMAIL OPERATIONS
# ============================================================================

@router.post("/bulk/update-status")
async def bulk_update_email_status(request: BulkUpdateStatusRequest):
    """Update status for multiple emails"""
    try:
        updated_count = 0
        errors = []
        
        for email_id in request.email_ids:
            try:
                # Update email status
                update_data = {
                    "status": request.new_status,
                    "updated_at": datetime.now().isoformat()
                }
                
                if request.notes:
                    update_data["bulk_update_notes"] = request.notes
                
                # Update in database
                success = update_document_by_id(emails_table, email_id, update_data)
                
                if success:
                    updated_count += 1
                else:
                    errors.append(f"Failed to update email {email_id}")
                    
            except Exception as e:
                errors.append(f"Error updating email {email_id}: {str(e)}")
        
        return {
            "success": True,
            "updated_count": updated_count,
            "total_requested": len(request.email_ids),
            "new_status": request.new_status,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk status update: {e}")
        raise HTTPException(status_code=500, detail=f"Error in bulk status update: {str(e)}")

@router.post("/bulk/generate-ai-responses")
async def bulk_generate_ai_responses(email_ids: List[str]):
    """Generate AI responses for multiple emails"""
    try:
        # Initialize AI responder
        config = llm_config
        ai_responder = LangChainAIResponder(config)
        
        results = []
        successful_count = 0
        
        for email_id in email_ids:
            try:
                # Get email
                email = get_email_by_id(email_id)
                if not email:
                    results.append({
                        "email_id": email_id,
                        "success": False,
                        "error": "Email not found"
                    })
                    continue
                
                # Get proper email ID
                custom_id = email.get("id", str(email.get("doc_id", "")))
                
                # Prepare email data
                email_data = {
                    "sender": email.get("sender"),
                    "subject": email.get("subject"),
                    "body": email.get("content", "") or email.get("body", "")
                }
                
                # Generate responses
                response_options = ai_responder.generate_reply(email_data, custom_id)
                
                # Save to waiting zone
                from ...plugin.ai.ai_response import save_ai_responses_to_waiting_zone
                ai_response_id = save_ai_responses_to_waiting_zone(custom_id, response_options)
                
                results.append({
                    "email_id": email_id,
                    "success": True,
                    "ai_response_id": ai_response_id,
                    "options_generated": len(response_options)
                })
                successful_count += 1
                
            except Exception as e:
                results.append({
                    "email_id": email_id,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "processed_count": successful_count,
            "total_requested": len(email_ids),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in bulk AI response generation: {e}")
        raise HTTPException(status_code=500, detail=f"Error in bulk AI response generation: {str(e)}")

@router.get("/health")
async def route_health_status():
    """Health check endpoint"""
    return {"status": "Healthy!"}