"""
Ticket data models and enums
Handles ticket-related database operations and data structures
"""

from enum import Enum
from app.services.tinydb_wrapper_supabase import TinyDB, Query
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

# Initialize ticket-specific database tables
try:
    from ...models import db
except ImportError:
    # Fallback for standalone usage
    db = TinyDB('email_system_tickets.json')

tickets_table = db.table('tickets')
ticket_assignments_table = db.table('ticket_assignments')

class TicketStatus(str, Enum):
    """Ticket status values"""
    NEW = "New"
    IN_PROGRESS = "In Progress"
    PENDING = "Pending"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class TicketCategory(str, Enum):
    """Main ticket categories"""
    MAINTENANCE = "Maintenance"
    UTILITIES = "Utilities"
    LEASE = "Lease"
    MOVE_IN_OUT = "Move-in/out"
    COMPLAINT = "Complaint"
    PAYMENT = "Payment"
    AMENITY = "Amenity"

class TicketSubcategory(str, Enum):
    """Detailed subcategories"""
    # Maintenance
    PLUMBING = "Plumbing"
    ELECTRICAL = "Electrical"
    HVAC = "HVAC"
    CLEANING = "Cleaning"
    APPLIANCE = "Appliance"
    GENERAL_REPAIR = "General Repair"
    
    # Utilities
    WATER = "Water"
    ELECTRICITY = "Electricity"
    GAS = "Gas"
    INTERNET = "Internet"
    
    # Lease
    RENEWAL = "Renewal"
    TERMINATION = "Termination"
    VIOLATION = "Violation"
    
    # Other
    NOISE_COMPLAINT = "Noise Complaint"
    NEIGHBOR_DISPUTE = "Neighbor Dispute"
    RENT_PAYMENT = "Rent Payment"
    LATE_FEES = "Late Fees"
    POOL = "Pool"
    GYM = "Gym"
    PARKING = "Parking"
    OTHER = "Other"

class TicketUrgency(str, Enum):
    """Ticket urgency levels (1=High, 2=Medium, 3=Low)"""
    HIGH = "1"      # Emergency
    MEDIUM = "2"    # Standard
    LOW = "3"       # Non-urgent

class TicketRequestType(str, Enum):
    """Types of requests"""
    REPAIR = "Repair"
    INSPECTION = "Inspection"
    SETUP = "Setup"
    GENERAL = "General"
    EMERGENCY = "Emergency"

class TicketData:
    """Data access layer for tickets"""
    
    @staticmethod
    def create(ticket_data: Dict[str, Any]) -> str:
        """Create a new ticket in database"""
        try:
            # Generate ticket ID if not provided
            if 'ticket_id' not in ticket_data:
                ticket_data['ticket_id'] = f"TKT-{str(uuid.uuid4())[:8].upper()}"
            
            # Add timestamps
            ticket_data['created_at'] = datetime.now().isoformat()
            ticket_data['updated_at'] = datetime.now().isoformat()
            
            # Insert into database
            tickets_table.insert(ticket_data)
            
            return ticket_data['ticket_id']
            
        except Exception as e:
            raise Exception(f"Failed to create ticket: {str(e)}")
    
    @staticmethod
    def get_by_id(ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID"""
        Ticket = Query()
        return tickets_table.get(Ticket.ticket_id == ticket_id)
    
    @staticmethod
    def update(ticket_id: str, update_data: Dict[str, Any]) -> bool:
        """Update ticket data"""
        try:
            Ticket = Query()
            update_data['updated_at'] = datetime.now().isoformat()
            
            result = tickets_table.update(update_data, Ticket.ticket_id == ticket_id)
            return len(result) > 0
            
        except Exception:
            return False
    
    @staticmethod
    def get_all(limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Get all tickets with pagination"""
        all_tickets = tickets_table.all()
        # Sort by created_at (most recent first)
        sorted_tickets = sorted(
            all_tickets, 
            key=lambda x: x.get('created_at', ''), 
            reverse=True
        )
        return sorted_tickets[skip:skip + limit]
    
    @staticmethod
    def get_by_status(status: TicketStatus) -> List[Dict[str, Any]]:
        """Get tickets by status"""
        Ticket = Query()
        return tickets_table.search(Ticket.status == status.value)
    
    @staticmethod
    def get_by_email_id(email_id: str) -> List[Dict[str, Any]]:
        """Get tickets created from a specific email"""
        Ticket = Query()
        return tickets_table.search(Ticket.email_id == email_id)
    
    @staticmethod
    def delete(ticket_id: str) -> bool:
        """Delete a ticket"""
        try:
            Ticket = Query()
            result = tickets_table.remove(Ticket.ticket_id == ticket_id)
            return len(result) > 0
        except Exception:
            return False

class AssignmentData:
    """Data access layer for ticket assignments"""
    
    @staticmethod
    def create(assignment_data: Dict[str, Any]) -> str:
        """Create a new assignment"""
        assignment_data['assignment_id'] = str(uuid.uuid4())
        assignment_data['assigned_at'] = datetime.now().isoformat()
        assignment_data['status'] = 'active'
        
        ticket_assignments_table.insert(assignment_data)
        return assignment_data['assignment_id']
    
    @staticmethod
    def get_by_ticket_id(ticket_id: str) -> List[Dict[str, Any]]:
        """Get assignments for a ticket"""
        Assignment = Query()
        return ticket_assignments_table.search(Assignment.ticket_id == ticket_id)
    
    @staticmethod
    def update_status(assignment_id: str, status: str) -> bool:
        """Update assignment status"""
        try:
            Assignment = Query()
            result = ticket_assignments_table.update(
                {'status': status, 'updated_at': datetime.now().isoformat()},
                Assignment.assignment_id == assignment_id
            )
            return len(result) > 0
        except Exception:
            return False

def get_ticket_statistics() -> Dict[str, Any]:
    """Get comprehensive ticket statistics"""
    all_tickets = tickets_table.all()
    
    stats = {
        'total_tickets': len(all_tickets),
        'by_status': {},
        'by_category': {},
        'by_urgency': {},
        'open_tickets': 0,
        'closed_tickets': 0
    }
    
    for ticket in all_tickets:
        # Count by status
        status = ticket.get('status', 'Unknown')
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # Count by category
        category = ticket.get('category', 'Unknown')
        stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        # Count by urgency
        urgency = ticket.get('urgency', 'Unknown')
        stats['by_urgency'][urgency] = stats['by_urgency'].get(urgency, 0) + 1
        
        # Count open/closed
        if status in ['New', 'In Progress', 'Pending']:
            stats['open_tickets'] += 1
        else:
            stats['closed_tickets'] += 1
    
    return stats