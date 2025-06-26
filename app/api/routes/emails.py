"""
Email Management API - High-level email operations and management
"""

from fastapi import APIRouter, HTTPException, Query as QueryParam
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import email processing components
from ...plugin.email.process_emails import get_email_by_id, get_recent_emails, get_replies_for_email
from ...plugin.ai.ai_response import (
    get_pending_ai_responses, 
    select_ai_response,
    LangChainAIResponder
)
from ...models import emails_table, replies_table, ai_responses_table
from tinydb import Query

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
                email_id = email.get("id", str(email.doc_id))
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
            email_id = email.get("id", str(email.doc_id))
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
        
        # Get related data
        replies = get_replies_for_email(email_id)
        
        # Get action items
        from ...models import action_items_table
        ActionItem = Query()
        action_items = action_items_table.search(ActionItem.email_id == email_id)
        
        # Get AI responses
        AIResponse = Query()
        ai_responses = ai_responses_table.search(AIResponse.email_id == email_id)
        
        # Get tickets
        tickets_info = []
        if email.get("tickets_created"):
            from ...plugin.tickets.manager import Ticket
            for ticket_id in email["tickets_created"]:
                ticket = Ticket.get_by_id(ticket_id)
                if ticket:
                    tickets_info.append({
                        "ticket_id": ticket_id,
                        "status": ticket.get("status"),
                        "category": ticket.get("category"),
                        "urgency": ticket.get("urgency"),
                        "assigned_to": ticket.get("assigned_to")
                    })
        
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
        if email_id.isdigit():
            emails_table.update(update_data, doc_ids=[int(email_id)])
        else:
            Email = Query()
            emails_table.update(update_data, Email.id == email_id)
        
        return {
            "success": True,
            "email_id": email_id,
            "new_status": request.status,
            "message": "Email status updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
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
        raise HTTPException(status_code=500, detail=f"Error getting pending AI responses: {str(e)}")

@router.get("/{email_id}/ai-responses")
async def get_email_ai_responses(email_id: str):
    """Get AI response options for a specific email"""
    try:
        # Check if email exists
        email = get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Get AI responses
        AIResponse = Query()
        ai_responses = ai_responses_table.search(AIResponse.email_id == email_id)
        
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
        raise HTTPException(status_code=500, detail=f"Error getting AI responses: {str(e)}")

@router.post("/{email_id}/ai-responses/select")
async def select_ai_response_for_email(email_id: str, request: AIResponseSelectionRequest):
    """Select an AI response option for an email"""
    try:
        # Check if email exists
        email = get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Select the AI response
        success = select_ai_response(
            email_id=email_id,
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
        
        # Prepare email data
        email_data = {
            "sender": email.get("sender"),
            "subject": email.get("subject"),
            "body": email.get("content", "")
        }
        
        # Generate new responses
        response_options = ai_responder.generate_reply(email_data, email_id)
        
        # Save to waiting zone
        from ...plugin.ai.ai_response import save_ai_responses_to_waiting_zone
        ai_response_id = save_ai_responses_to_waiting_zone(email_id, response_options)
        
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
        raise HTTPException(status_code=500, detail=f"Error getting email analytics: {str(e)}")

@router.get("/analytics/trends")
async def get_email_trends(days: int = QueryParam(30, ge=1, le=365)):
    """Get email trends over time"""
    try:
        all_emails = emails_table.all()
        
        # Group emails by date
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        daily_counts = defaultdict(lambda: {
            "received": 0,
            "processed": 0,
            "tickets_created": 0
        })
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        for email in all_emails:
            email_date_str = email.get("received_at", "")
            if email_date_str:
                try:
                    email_date = datetime.fromisoformat(email_date_str.replace('Z', '+00:00'))
                    if start_date <= email_date <= end_date:
                        date_key = email_date.strftime("%Y-%m-%d")
                        daily_counts[date_key]["received"] += 1
                        
                        if email.get("status") in ["processed", "responded"]:
                            daily_counts[date_key]["processed"] += 1
                        
                        daily_counts[date_key]["tickets_created"] += len(email.get("tickets_created", []))
                except:
                    continue
        
        # Convert to list format for easier consumption
        trend_data = []
        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.strftime("%Y-%m-%d")
            trend_data.append({
                "date": date_key,
                "emails_received": daily_counts[date_key]["received"],
                "emails_processed": daily_counts[date_key]["processed"],
                "tickets_created": daily_counts[date_key]["tickets_created"]
            })
            current_date += timedelta(days=1)
        
        return {
            "period_days": days,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "trend_data": trend_data,
            "summary": {
                "total_received": sum(d["emails_received"] for d in trend_data),
                "total_processed": sum(d["emails_processed"] for d in trend_data),
                "total_tickets": sum(d["tickets_created"] for d in trend_data),
                "avg_daily_received": sum(d["emails_received"] for d in trend_data) / len(trend_data),
                "avg_daily_processed": sum(d["emails_processed"] for d in trend_data) / len(trend_data)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting email trends: {str(e)}")

# ============================================================================
# EMAIL WORKFLOW OPERATIONS
# ============================================================================

@router.post("/{email_id}/reprocess")
async def reprocess_email(email_id: str):
    """Reprocess an email through the complete workflow"""
    try:
        # Get email
        email = get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Trigger reprocessing
        from ...plugin.email.process_emails import EmailProcessor
        email_processor = EmailProcessor()
        
        email_data = {
            "sender": email.get("sender"),
            "subject": email.get("subject"),
            "body": email.get("content", "")
        }
        
        # Process email
        result = email_processor.process_email(email_data)
        
        # Update email record
        update_data = {
            "reprocessed_at": datetime.now().isoformat(),
            "reprocessing_result": result
        }
        
        if email_id.isdigit():
            emails_table.update(update_data, doc_ids=[int(email_id)])
        else:
            Email = Query()
            emails_table.update(update_data, Email.id == email_id)
        
        return {
            "success": True,
            "email_id": email_id,
            "reprocessing_result": result,
            "message": "Email reprocessed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reprocessing email: {str(e)}")

@router.get("/{email_id}/workflow-status")
async def get_email_workflow_status(email_id: str):
    """Get comprehensive workflow status for an email"""
    try:
        # Get email
        email = get_email_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Get all related data
        replies = get_replies_for_email(email_id)
        
        # Get action items
        from ...models import action_items_table
        ActionItem = Query()
        action_items = action_items_table.search(ActionItem.email_id == email_id)
        
        # Get AI responses
        AIResponse = Query()
        ai_responses = ai_responses_table.search(AIResponse.email_id == email_id)
        
        # Get tickets
        tickets = []
        if email.get("tickets_created"):
            from ...plugin.tickets.manager import Ticket
            for ticket_id in email["tickets_created"]:
                ticket = Ticket.get_by_id(ticket_id)
                if ticket:
                    tickets.append(ticket)
        
        # Determine workflow completion status
        workflow_steps = {
            "email_received": bool(email),
            "email_processed": email.get("status") in ["processed", "responded"],
            "action_items_extracted": len(action_items) > 0,
            "ai_responses_generated": len(ai_responses) > 0,
            "ai_response_selected": any(r.get("sent", False) for r in replies),
            "tickets_created": len(tickets) > 0,
            "tickets_resolved": all(t.get("status") in ["Resolved", "Closed"] for t in tickets) if tickets else None
        }
        
        # Calculate completion percentage
        completed_steps = sum(1 for step, completed in workflow_steps.items() if completed and completed is not None)
        total_steps = sum(1 for step, completed in workflow_steps.items() if completed is not None)
        completion_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        return {
            "email_id": email_id,
            "workflow_steps": workflow_steps,
            "completion_percentage": completion_percentage,
            "current_status": email.get("status"),
            "summary": {
                "action_items": len(action_items),
                "ai_responses": len(ai_responses),
                "replies": len(replies),
                "tickets": len(tickets)
            },
            "next_actions": _determine_next_actions(workflow_steps, email, ai_responses, tickets)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow status: {str(e)}")

def _determine_next_actions(workflow_steps: Dict[str, bool], email: Dict, ai_responses: List, tickets: List) -> List[str]:
    """Determine what actions can be taken next in the workflow"""
    next_actions = []
    
    if not workflow_steps.get("email_processed"):
        next_actions.append("Process email to extract action items")
    
    if workflow_steps.get("email_processed") and not workflow_steps.get("ai_responses_generated"):
        next_actions.append("Generate AI responses")
    
    if workflow_steps.get("ai_responses_generated") and not workflow_steps.get("ai_response_selected"):
        next_actions.append("Select and send AI response")
    
    if workflow_steps.get("action_items_extracted") and not workflow_steps.get("tickets_created"):
        next_actions.append("Create tickets from action items")
    
    if workflow_steps.get("tickets_created") and workflow_steps.get("tickets_resolved") is False:
        next_actions.append("Work on resolving open tickets")
    
    if not next_actions:
        next_actions.append("Workflow complete - no further actions needed")
    
    return next_actions

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
                if email_id.isdigit():
                    result = emails_table.update(update_data, doc_ids=[int(email_id)])
                else:
                    Email = Query()
                    result = emails_table.update(update_data, Email.id == email_id)
                
                if result:
                    updated_count += 1
                    
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
                
                # Prepare email data
                email_data = {
                    "sender": email.get("sender"),
                    "subject": email.get("subject"),
                    "body": email.get("content", "")
                }
                
                # Generate responses
                response_options = ai_responder.generate_reply(email_data, email_id)
                
                # Save to waiting zone
                from ...plugin.ai.ai_response import save_ai_responses_to_waiting_zone
                ai_response_id = save_ai_responses_to_waiting_zone(email_id, response_options)
                
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
        raise HTTPException(status_code=500, detail=f"Error in bulk AI response generation: {str(e)}")

@router.get("/health")
async def route_health_status():
  return {"status": "Healthy!"}