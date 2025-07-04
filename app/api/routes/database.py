"""
Database CRUD API - Direct database operations for all tables
"""

from fastapi import APIRouter, HTTPException, Query as QueryParam
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.services.tinydb_wrapper_supabase import Query

# Import database tables and models
from ...models import (
    emails_table, replies_table, action_items_table, tenants_table,
    response_feedback_table, context_patterns_table, ai_responses_table,
    EmailMessage, Reply, ActionItem, Tenant, ResponseFeedback, ContextPattern,
    get_database_stats
)

router = APIRouter()

# Pydantic models for API requests
class EmailCreateRequest(BaseModel):
    sender: str
    subject: str
    body: str
    status: Optional[str] = "unprocessed"
    priority_level: Optional[str] = "medium"
    context_labels: Optional[List[str]] = []

class TenantCreateRequest(BaseModel):
    name: str
    email: str
    unit: Optional[str] = None
    phone: Optional[str] = None
    rent_amount: Optional[float] = None

class ActionItemCreateRequest(BaseModel):
    email_id: str
    action_data: Dict[str, Any]
    status: Optional[str] = "open"

class ReplyCreateRequest(BaseModel):
    email_id: str
    content: str
    strategy_used: str
    sent: Optional[bool] = False

# ============================================================================
# DATABASE STATISTICS AND OVERVIEW
# ============================================================================

@router.get("/stats")
async def get_database_statistics():
    """Get comprehensive database statistics"""
    try:
        stats = get_database_stats()
        
        # Add more detailed stats
        recent_emails = emails_table.all()[-10:] if emails_table.all() else []
        
        detailed_stats = {
            **stats,
            "last_updated": datetime.now().isoformat(),
            "recent_activity": {
                "recent_emails": [
                    {
                        "id": email.get("id"),
                        "sender": email.get("sender"),
                        "subject": email.get("subject"),
                        "received_at": email.get("received_at")
                    }
                    for email in recent_emails
                ]
            }
        }
        
        return detailed_stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database stats: {str(e)}")

@router.get("/tables")
async def list_database_tables():
    """List all available database tables and their info"""
    return {
        "tables": {
            "emails": {
                "description": "Email messages and processing data",
                "count": len(emails_table.all()),
                "fields": ["id", "sender", "subject", "body", "received_at", "status", "priority_level"]
            },
            "replies": {
                "description": "AI-generated replies to emails", 
                "count": len(replies_table.all()),
                "fields": ["id", "email_id", "content", "strategy_used", "sent", "created_date"]
            },
            "action_items": {
                "description": "Action items extracted from emails",
                "count": len(action_items_table.all()),
                "fields": ["id", "email_id", "action_data", "status", "created_date"]
            },
            "tenants": {
                "description": "Tenant information and contacts",
                "count": len(tenants_table.all()),
                "fields": ["id", "name", "email", "unit", "phone", "rent_amount"]
            },
            "ai_responses": {
                "description": "AI response options in waiting zone",
                "count": len(ai_responses_table.all()),
                "fields": ["id", "email_id", "response_options", "status", "created_at"]
            }
        }
    }

# ============================================================================
# EMAILS TABLE CRUD
# ============================================================================

@router.get("/emails")
async def get_all_emails(
    skip: int = QueryParam(0, ge=0),
    limit: int = QueryParam(100, ge=1, le=1000),
    status: Optional[str] = QueryParam(None),
    sender: Optional[str] = QueryParam(None)
):
    """Get all emails with filtering and pagination"""
    try:
        all_emails = emails_table.all()
        
        # Apply filters
        if status:
            all_emails = [e for e in all_emails if e.get("status") == status]
        if sender:
            all_emails = [e for e in all_emails if sender.lower() in e.get("sender", "").lower()]
        
        # Sort by received_at (most recent first)
        sorted_emails = sorted(
            all_emails, 
            key=lambda x: x.get("received_at", ""), 
            reverse=True
        )
        
        # Apply pagination
        paginated = sorted_emails[skip:skip + limit]
        
        return {
            "emails": paginated,
            "total": len(sorted_emails),
            "skip": skip,
            "limit": limit,
            "filters_applied": {"status": status, "sender": sender}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {str(e)}")

@router.get("/emails/{email_id}")
async def get_email_by_id(email_id: str):
    """Get specific email by ID"""
    try:
        # Try both doc_id and custom id field
        email = emails_table.get(doc_id=int(email_id)) if email_id.isdigit() else None
        
        if not email:
            # Try by custom id field
            Email = Query()
            email = emails_table.get(Email.id == email_id)
        
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Get related data
        Email = Query()
        replies = replies_table.search(Email.email_id == email_id)
        action_items = action_items_table.search(Email.email_id == email_id)
        
        return {
            "email": email,
            "replies": replies,
            "action_items": action_items,
            "related_data_count": {
                "replies": len(replies),
                "action_items": len(action_items)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching email: {str(e)}")

@router.post("/emails")
async def create_email(request: EmailCreateRequest):
    """Create a new email record"""
    try:
        email_id = EmailMessage.create(
            sender=request.sender,
            subject=request.subject,
            body=request.body,
            status=request.status,
            priority_level=request.priority_level,
            context_labels=request.context_labels
        )
        
        return {
            "success": True,
            "email_id": email_id,
            "message": "Email created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating email: {str(e)}")

@router.put("/emails/{email_id}")
async def update_email(email_id: str, update_data: Dict[str, Any]):
    """Update an email record"""
    try:
        # Find email first
        email = emails_table.get(doc_id=int(email_id)) if email_id.isdigit() else None
        if not email:
            Email = Query()
            email = emails_table.get(Email.id == email_id)
        
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Update with timestamp
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Update in database
        if email_id.isdigit():
            emails_table.update(update_data, doc_ids=[int(email_id)])
        else:
            Email = Query()
            emails_table.update(update_data, Email.id == email_id)
        
        return {
            "success": True,
            "email_id": email_id,
            "message": "Email updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating email: {str(e)}")

@router.delete("/emails/{email_id}")
async def delete_email(email_id: str):
    """Delete an email and all related data"""
    try:
        # Find and delete email
        email = emails_table.get(doc_id=int(email_id)) if email_id.isdigit() else None
        if not email:
            Email = Query()
            email = emails_table.get(Email.id == email_id)
            
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Delete related data
        Email = Query()
        replies_deleted = len(replies_table.remove(Email.email_id == email_id))
        action_items_deleted = len(action_items_table.remove(Email.email_id == email_id))
        ai_responses_deleted = len(ai_responses_table.remove(Email.email_id == email_id))
        
        # Delete email
        if email_id.isdigit():
            emails_table.remove(doc_ids=[int(email_id)])
        else:
            emails_table.remove(Email.id == email_id)
        
        return {
            "success": True,
            "email_id": email_id,
            "deleted_related_data": {
                "replies": replies_deleted,
                "action_items": action_items_deleted,
                "ai_responses": ai_responses_deleted
            },
            "message": "Email and related data deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting email: {str(e)}")

# ============================================================================
# TENANTS TABLE CRUD
# ============================================================================

@router.get("/tenants")
async def get_all_tenants():
    """Get all tenants"""
    try:
        tenants = tenants_table.all()
        return {
            "tenants": tenants,
            "total": len(tenants)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tenants: {str(e)}")

@router.get("/tenants/{tenant_id}")
async def get_tenant_by_id(tenant_id: str):
    """Get specific tenant by ID"""
    try:
        # Try by doc_id first
        tenant = tenants_table.get(doc_id=int(tenant_id)) if tenant_id.isdigit() else None
        
        if not tenant:
            # Try by custom id field
            Tenant = Query()
            tenant = tenants_table.get(Tenant.id == tenant_id)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Get tenant's emails
        Email = Query()
        tenant_emails = emails_table.search(Email.sender == tenant.get("email", ""))
        
        return {
            "tenant": tenant,
            "emails": tenant_emails,
            "email_count": len(tenant_emails)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tenant: {str(e)}")

@router.post("/tenants")
async def create_tenant(request: TenantCreateRequest):
    """Create a new tenant"""
    try:
        # Check if tenant already exists
        existing = Tenant.get_by_email(request.email)
        if existing:
            raise HTTPException(status_code=400, detail="Tenant with this email already exists")
        
        tenant_id = Tenant.create(
            name=request.name,
            email=request.email,
            unit=request.unit,
            phone=request.phone,
            rent_amount=request.rent_amount
        )
        
        return {
            "success": True,
            "tenant_id": tenant_id,
            "message": "Tenant created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating tenant: {str(e)}")

@router.get("/tenants/by-email/{email}")
async def get_tenant_by_email(email: str):
    """Get tenant by email address"""
    try:
        tenant = Tenant.get_by_email(email)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Get tenant's emails and tickets
        Email = Query()
        tenant_emails = emails_table.search(Email.sender == email)
        
        # Get tickets created from tenant's emails
        tickets_created = []
        for email_record in tenant_emails:
            if email_record.get("tickets_created"):
                tickets_created.extend(email_record["tickets_created"])
        
        return {
            "tenant": tenant,
            "emails": tenant_emails,
            "tickets_created": tickets_created,
            "summary": {
                "email_count": len(tenant_emails),
                "ticket_count": len(tickets_created)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tenant: {str(e)}")

# ============================================================================
# ACTION ITEMS TABLE CRUD
# ============================================================================

@router.get("/action-items")
async def get_all_action_items(
    status: Optional[str] = QueryParam(None),
    email_id: Optional[str] = QueryParam(None)
):
    """Get all action items with filtering"""
    try:
        all_items = action_items_table.all()
        
        # Apply filters
        if status:
            all_items = [item for item in all_items if item.get("status") == status]
        if email_id:
            all_items = [item for item in all_items if item.get("email_id") == email_id]
        
        # Sort by created_date (most recent first)
        sorted_items = sorted(
            all_items,
            key=lambda x: x.get("created_date", ""),
            reverse=True
        )
        
        return {
            "action_items": sorted_items,
            "total": len(sorted_items),
            "filters_applied": {"status": status, "email_id": email_id}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching action items: {str(e)}")

@router.get("/action-items/{item_id}")
async def get_action_item_by_id(item_id: str):
    """Get specific action item by ID"""
    try:
        # Try by doc_id first
        item = action_items_table.get(doc_id=int(item_id)) if item_id.isdigit() else None
        
        if not item:
            # Try by custom id field
            ActionItem = Query()
            item = action_items_table.get(ActionItem.id == item_id)
        
        if not item:
            raise HTTPException(status_code=404, detail="Action item not found")
        
        # Get related email
        email = None
        if item.get("email_id"):
            email = get_email_by_id(item["email_id"])
        
        return {
            "action_item": item,
            "related_email": email,
            "ticket_id": item.get("ticket_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching action item: {str(e)}")

@router.post("/action-items")
async def create_action_item(request: ActionItemCreateRequest):
    """Create a new action item"""
    try:
        item_id = ActionItem.create(
            email_id=request.email_id,
            action_data=request.action_data,
            status=request.status
        )
        
        return {
            "success": True,
            "action_item_id": item_id,
            "message": "Action item created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating action item: {str(e)}")

# ============================================================================
# REPLIES TABLE CRUD
# ============================================================================

@router.get("/replies")
async def get_all_replies(email_id: Optional[str] = QueryParam(None)):
    """Get all replies, optionally filtered by email_id"""
    try:
        if email_id:
            replies = Reply.get_by_email_id(email_id)
        else:
            replies = replies_table.all()
        
        # Sort by created_date (most recent first)
        sorted_replies = sorted(
            replies,
            key=lambda x: x.get("created_date", ""),
            reverse=True
        )
        
        return {
            "replies": sorted_replies,
            "total": len(sorted_replies),
            "email_id_filter": email_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching replies: {str(e)}")

@router.get("/replies/{reply_id}")
async def get_reply_by_id(reply_id: str):
    """Get specific reply by ID"""
    try:
        # Try by doc_id first
        reply = replies_table.get(doc_id=int(reply_id)) if reply_id.isdigit() else None
        
        if not reply:
            # Try by custom id field
            Reply = Query()
            reply = replies_table.get(Reply.id == reply_id)
        
        if not reply:
            raise HTTPException(status_code=404, detail="Reply not found")
        
        return {"reply": reply}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching reply: {str(e)}")

@router.post("/replies")
async def create_reply(request: ReplyCreateRequest):
    """Create a new reply"""
    try:
        reply_id = Reply.create(
            email_id=request.email_id,
            content=request.content,
            strategy_used=request.strategy_used,
            sent=request.sent
        )
        
        return {
            "success": True,
            "reply_id": reply_id,
            "message": "Reply created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating reply: {str(e)}")

# ============================================================================
# AI RESPONSES TABLE CRUD
# ============================================================================

@router.get("/ai-responses")
async def get_all_ai_responses(
    status: Optional[str] = QueryParam(None),
    email_id: Optional[str] = QueryParam(None)
):
    """Get all AI responses with filtering"""
    try:
        all_responses = ai_responses_table.all()
        
        # Apply filters
        if status:
            all_responses = [r for r in all_responses if r.get("status") == status]
        if email_id:
            all_responses = [r for r in all_responses if r.get("email_id") == email_id]
        
        # Sort by created_at (most recent first)
        sorted_responses = sorted(
            all_responses,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        return {
            "ai_responses": sorted_responses,
            "total": len(sorted_responses),
            "filters_applied": {"status": status, "email_id": email_id}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching AI responses: {str(e)}")

@router.get("/ai-responses/{response_id}")
async def get_ai_response_by_id(response_id: str):
    """Get specific AI response by ID"""
    try:
        # Try by doc_id first
        response = ai_responses_table.get(doc_id=int(response_id)) if response_id.isdigit() else None
        
        if not response:
            # Try by custom id field
            AIResponse = Query()
            response = ai_responses_table.get(AIResponse.id == response_id)
        
        if not response:
            raise HTTPException(status_code=404, detail="AI response not found")
        
        return {"ai_response": response}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching AI response: {str(e)}")

# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/bulk/delete-emails")
async def bulk_delete_emails(email_ids: List[str]):
    """Delete multiple emails and their related data"""
    try:
        deleted_count = 0
        errors = []
        
        for email_id in email_ids:
            try:
                # Delete email and related data (reuse single delete logic)
                await delete_email(email_id)
                deleted_count += 1
            except Exception as e:
                errors.append(f"Error deleting email {email_id}: {str(e)}")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "total_requested": len(email_ids),
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in bulk delete: {str(e)}")

@router.post("/bulk/update-action-items-status")
async def bulk_update_action_items_status(item_ids: List[str], new_status: str):
    """Update status for multiple action items"""
    try:
        updated_count = 0
        errors = []
        
        for item_id in item_ids:
            try:
                # Update action item status
                ActionItemQuery = Query()
                result = action_items_table.update(
                    {
                        "status": new_status,
                        "updated_date": datetime.now().isoformat()
                    },
                    ActionItemQuery.id == item_id
                )
                if result:
                    updated_count += 1
            except Exception as e:
                errors.append(f"Error updating item {item_id}: {str(e)}")
        
        return {
            "success": True,
            "updated_count": updated_count,
            "total_requested": len(item_ids),
            "new_status": new_status,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in bulk update: {str(e)}")

# ============================================================================
# SEARCH AND QUERY OPERATIONS
# ============================================================================

@router.get("/search/emails")
async def search_emails(
    query: str,
    search_in: Optional[str] = QueryParam("all", description="Fields to search: 'subject', 'body', 'sender', 'all'"),
    limit: int = QueryParam(50, ge=1, le=200)
):
    """Search emails by content"""
    try:
        all_emails = emails_table.all()
        matching_emails = []
        query_lower = query.lower()
        
        for email in all_emails:
            match_found = False
            
            if search_in in ["all", "subject"] and query_lower in email.get("subject", "").lower():
                match_found = True
            elif search_in in ["all", "body"] and query_lower in email.get("body", "").lower():
                match_found = True
            elif search_in in ["all", "sender"] and query_lower in email.get("sender", "").lower():
                match_found = True
            
            if match_found:
                matching_emails.append(email)
                
            if len(matching_emails) >= limit:
                break
        
        return {
            "query": query,
            "search_in": search_in,
            "results": matching_emails,
            "count": len(matching_emails),
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching emails: {str(e)}")

@router.get("/reports/daily-summary")
async def get_daily_summary(date: Optional[str] = QueryParam(None, description="Date in YYYY-MM-DD format")):
    """Get daily summary report"""
    try:
        target_date = date or datetime.now().strftime("%Y-%m-%d")
        
        # Get emails for the day
        daily_emails = [
            email for email in emails_table.all()
            if email.get("received_at", "").startswith(target_date)
        ]
        
        # Get action items for the day
        daily_action_items = [
            item for item in action_items_table.all()
            if item.get("created_date", "").startswith(target_date)
        ]
        
        # Get replies for the day
        daily_replies = [
            reply for reply in replies_table.all()
            if reply.get("created_date", "").startswith(target_date)
        ]
        
        # Calculate statistics
        status_counts = {}
        for email in daily_emails:
            status = email.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        category_counts = {}
        for item in daily_action_items:
            category = item.get("action_data", {}).get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "date": target_date,
            "summary": {
                "emails_received": len(daily_emails),
                "action_items_created": len(daily_action_items),
                "replies_generated": len(daily_replies),
                "emails_by_status": status_counts,
                "action_items_by_category": category_counts
            },
            "details": {
                "emails": daily_emails,
                "action_items": daily_action_items,
                "replies": daily_replies
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating daily summary: {str(e)}")

def get_email_by_id_internal(email_id: str):
    """Internal helper function to get email by ID"""
    # Try both doc_id and custom id field
    email = emails_table.get(doc_id=int(email_id)) if email_id.isdigit() else None
    
    if not email:
        Email = Query()
        email = emails_table.get(Email.id == email_id)
    
    return email

@router.get("/health")
async def route_health_status():
  return {"status": "Healthy!"}