"""
Ticket API routes - Clean separation from email processing
Provides RESTful endpoints for ticket management
"""

from fastapi import APIRouter, HTTPException, Query as QueryParam
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...plugin.tickets.manager import Ticket, get_ticket_statistics, get_open_tickets
from ...plugin.tickets.models import TicketStatus, TicketCategory, TicketUrgency
from ...plugin.tickets.utils import search_tickets, generate_ticket_report, export_tickets_to_csv

router = APIRouter(prefix="/tickets", tags=["Tickets"])

# Pydantic models for API
class TicketResponse(BaseModel):
    ticket_id: str
    short_description: str
    description: str
    category: str
    subcategory: str
    request_type: str
    urgency: str
    priority: str
    property_id: str
    unit_number: str
    requested_for: str
    assignment_group: str
    assigned_to: str
    status: str
    created_at: str
    email_id: Optional[str] = None

class TicketUpdateRequest(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    assignment_group: Optional[str] = None
    notes: Optional[str] = None

class TicketStatsResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    closed_tickets: int
    by_status: Dict[str, int]
    by_category: Dict[str, int]
    by_urgency: Dict[str, int]

@router.get("/", response_model=Dict[str, Any])
async def get_tickets(
    skip: int = QueryParam(0, ge=0),
    limit: int = QueryParam(100, ge=1, le=1000),
    status: Optional[str] = QueryParam(None),
    category: Optional[str] = QueryParam(None),
    urgency: Optional[str] = QueryParam(None)
):
    """Get tickets with optional filtering"""
    try:
        from ...plugin.tickets.models import TicketData
        
        # Get all tickets first
        all_tickets = TicketData.get_all(limit=10000)
        
        # Apply filters
        filtered_tickets = all_tickets
        
        if status:
            filtered_tickets = [t for t in filtered_tickets if t.get('status') == status]
        
        if category:
            filtered_tickets = [t for t in filtered_tickets if t.get('category') == category]
        
        if urgency:
            filtered_tickets = [t for t in filtered_tickets if t.get('urgency') == urgency]
        
        # Apply pagination
        total = len(filtered_tickets)
        paginated_tickets = filtered_tickets[skip:skip + limit]
        
        return {
            "tickets": paginated_tickets,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tickets: {str(e)}")

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):
    """Get a specific ticket by ID"""
    try:
        ticket = Ticket.get_by_id(ticket_id)
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return TicketResponse(**ticket)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ticket: {str(e)}")

@router.put("/{ticket_id}")
async def update_ticket(ticket_id: str, update_request: TicketUpdateRequest):
    """Update a ticket"""
    try:
        # Check if ticket exists
        ticket = Ticket.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        success = True
        
        # Update status if provided
        if update_request.status:
            try:
                status_enum = TicketStatus(update_request.status)
                success = Ticket.update_status(ticket_id, status_enum, update_request.notes)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status value")
        
        # Update assignment if provided
        if update_request.assigned_to or update_request.assignment_group:
            assigned_to = update_request.assigned_to or ticket.get('assigned_to')
            assignment_group = update_request.assignment_group or ticket.get('assignment_group')
            
            assignment_success = Ticket.assign(ticket_id, assigned_to, assignment_group)
            success = success and assignment_success
        
        if success:
            return {"message": "Ticket updated successfully", "ticket_id": ticket_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to update ticket")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating ticket: {str(e)}")

@router.get("/stats/summary", response_model=TicketStatsResponse)
async def get_ticket_statistics_endpoint():
    """Get ticket statistics summary"""
    try:
        stats = get_ticket_statistics()
        return TicketStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

@router.get("/stats/report")
async def get_ticket_report():
    """Get comprehensive ticket report"""
    try:
        report = generate_ticket_report()
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@router.get("/search/{query}")
async def search_tickets_endpoint(query: str, limit: int = QueryParam(20, ge=1, le=100)):
    """Search tickets by content"""
    try:
        results = search_tickets(query, limit)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching tickets: {str(e)}")

@router.get("/open/list")
async def get_open_tickets_endpoint():
    """Get all open tickets"""
    try:
        open_tickets = get_open_tickets()
        return {
            "open_tickets": open_tickets,
            "count": len(open_tickets)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching open tickets: {str(e)}")

@router.get("/categories/available")
async def get_available_categories():
    """Get available ticket categories and options"""
    try:
        return {
            "categories": [category.value for category in TicketCategory],
            "statuses": [status.value for status in TicketStatus],
            "urgency_levels": [urgency.value for urgency in TicketUrgency],
            "request_types": ["Repair", "Inspection", "Setup", "General", "Emergency"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

@router.post("/batch/assign")
async def batch_assign_tickets_endpoint(
    ticket_ids: List[str], 
    assigned_to: str, 
    assignment_group: Optional[str] = None
):
    """Assign multiple tickets to a person/group"""
    try:
        from ...plugin.tickets.manager import bulk_assign_tickets
        
        result = bulk_assign_tickets(ticket_ids, assigned_to, assignment_group)
        return {
            "message": f"Assigned {result['successful_count']}/{result['total_count']} tickets successfully",
            "results": result['results'],
            "successful_count": result['successful_count'],
            "total_count": result['total_count']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error batch assigning tickets: {str(e)}")

@router.post("/batch/update-status")
async def batch_update_ticket_status_endpoint(
    ticket_ids: List[str], 
    status: str, 
    notes: Optional[str] = None
):
    """Update status for multiple tickets"""
    try:
        from ...plugin.tickets.manager import bulk_update_status
        
        try:
            status_enum = TicketStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")
        
        result = bulk_update_status(ticket_ids, status_enum, notes)
        return {
            "message": f"Updated {result['successful_count']}/{result['total_count']} tickets successfully",
            "results": result['results'],
            "successful_count": result['successful_count'],
            "total_count": result['total_count']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error batch updating tickets: {str(e)}")

@router.get("/export/csv")
async def export_tickets_csv(
    status: Optional[str] = QueryParam(None),
    category: Optional[str] = QueryParam(None)
):
    """Export tickets to CSV format"""
    try:
        from ...plugin.tickets.models import TicketData
        
        # Get tickets with filters
        all_tickets = TicketData.get_all(limit=10000)
        
        if status:
            all_tickets = [t for t in all_tickets if t.get('status') == status]
        
        if category:
            all_tickets = [t for t in all_tickets if t.get('category') == category]
        
        csv_content = export_tickets_to_csv(all_tickets)
        
        return {
            "csv_content": csv_content,
            "ticket_count": len(all_tickets),
            "exported_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting tickets: {str(e)}")

@router.get("/health")
async def route_health_status():
  return {"status": "Healthy!"}