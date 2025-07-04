"""
Fixed Ticket data models and enums
Handles ticket-related database operations and data structures with proper PostgreSQL compatibility
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
import uuid
import logging
from datetime import datetime

# Import the fixed database wrapper
from app.services.tinydb_wrapper_supabase import TinyDB, Query

logger = logging.getLogger(__name__)

# Initialize ticket-specific database tables
try:
    from ...models import db
except ImportError:
    # Fallback for standalone usage
    db = TinyDB()

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

# Helper functions for ID handling
def get_ticket_by_id(ticket_id: Union[str, int]) -> Optional[Dict]:
    """Get ticket by either doc_id (int) or custom ticket_id (str)"""
    try:
        # Try by PostgreSQL doc_id first if it's numeric
        if isinstance(ticket_id, int) or (isinstance(ticket_id, str) and ticket_id.isdigit()):
            doc_id_int = int(ticket_id)
            ticket = tickets_table.get(doc_id=doc_id_int)
            if ticket:
                return ticket
        
        # Try by custom ticket_id field
        Ticket = Query()
        ticket = tickets_table.get(Ticket.ticket_id == str(ticket_id))
        return ticket
        
    except Exception as e:
        logger.error(f"Error getting ticket by id {ticket_id}: {e}")
        return None

def update_ticket_by_id(ticket_id: Union[str, int], update_data: Dict) -> bool:
    """Update ticket by either doc_id (int) or custom ticket_id (str)"""
    try:
        # Try by PostgreSQL doc_id first if it's numeric
        if isinstance(ticket_id, int) or (isinstance(ticket_id, str) and ticket_id.isdigit()):
            doc_id_int = int(ticket_id)
            result = tickets_table.update(update_data, doc_ids=[doc_id_int])
            if result:
                return True
        
        # Try by custom ticket_id field
        Ticket = Query()
        result = tickets_table.update(update_data, Ticket.ticket_id == str(ticket_id))
        return len(result) > 0
        
    except Exception as e:
        logger.error(f"Error updating ticket by id {ticket_id}: {e}")
        return False

def remove_ticket_by_id(ticket_id: Union[str, int]) -> bool:
    """Remove ticket by either doc_id (int) or custom ticket_id (str)"""
    try:
        # Try by PostgreSQL doc_id first if it's numeric
        if isinstance(ticket_id, int) or (isinstance(ticket_id, str) and ticket_id.isdigit()):
            doc_id_int = int(ticket_id)
            result = tickets_table.remove(doc_ids=[doc_id_int])
            if result:
                return True
        
        # Try by custom ticket_id field
        Ticket = Query()
        result = tickets_table.remove(Ticket.ticket_id == str(ticket_id))
        return len(result) > 0
        
    except Exception as e:
        logger.error(f"Error removing ticket by id {ticket_id}: {e}")
        return False

class TicketData:
    """Data access layer for tickets with proper ID handling"""
    
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
            doc_id = tickets_table.insert(ticket_data)
            
            logger.info(f"Created ticket {ticket_data['ticket_id']} with doc_id {doc_id}")
            return ticket_data['ticket_id']
            
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
            raise Exception(f"Failed to create ticket: {str(e)}")
    
    @staticmethod
    def get_by_id(ticket_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Get ticket by ID (handles both doc_id and custom ticket_id)"""
        return get_ticket_by_id(ticket_id)
    
    @staticmethod
    def update(ticket_id: Union[str, int], update_data: Dict[str, Any]) -> bool:
        """Update ticket data"""
        try:
            update_data['updated_at'] = datetime.now().isoformat()
            return update_ticket_by_id(ticket_id, update_data)
            
        except Exception as e:
            logger.error(f"Error updating ticket {ticket_id}: {e}")
            return False
    
    @staticmethod
    def get_all(limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Get all tickets with pagination"""
        try:
            all_tickets = tickets_table.all()
            # Sort by created_at (most recent first)
            sorted_tickets = sorted(
                all_tickets, 
                key=lambda x: x.get('created_at', ''), 
                reverse=True
            )
            return sorted_tickets[skip:skip + limit]
        except Exception as e:
            logger.error(f"Error getting all tickets: {e}")
            return []
    
    @staticmethod
    def get_by_status(status: TicketStatus) -> List[Dict[str, Any]]:
        """Get tickets by status"""
        try:
            Ticket = Query()
            return tickets_table.search(Ticket.status == status.value)
        except Exception as e:
            logger.error(f"Error getting tickets by status {status}: {e}")
            return []
    
    @staticmethod
    def get_by_email_id(email_id: str) -> List[Dict[str, Any]]:
        """Get tickets created from a specific email"""
        try:
            Ticket = Query()
            return tickets_table.search(Ticket.email_id == email_id)
        except Exception as e:
            logger.error(f"Error getting tickets by email_id {email_id}: {e}")
            return []
    
    @staticmethod
    def delete(ticket_id: Union[str, int]) -> bool:
        """Delete a ticket"""
        try:
            return remove_ticket_by_id(ticket_id)
        except Exception as e:
            logger.error(f"Error deleting ticket {ticket_id}: {e}")
            return False
    
    @staticmethod
    def search(query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search tickets by content"""
        try:
            query_lower = query.lower()
            all_tickets = tickets_table.all()
            
            matching_tickets = []
            
            for ticket in all_tickets:
                # Search in multiple fields
                searchable_text = f"""
                    {ticket.get('short_description', '')}
                    {ticket.get('description', '')}
                    {ticket.get('category', '')}
                    {ticket.get('subcategory', '')}
                    {ticket.get('unit_number', '')}
                    {ticket.get('requested_for', '')}
                    {ticket.get('ticket_id', '')}
                """.lower()
                
                if query_lower in searchable_text:
                    matching_tickets.append(ticket)
                    
                    if len(matching_tickets) >= limit:
                        break
            
            return matching_tickets
            
        except Exception as e:
            logger.error(f"Error searching tickets: {e}")
            return []

class AssignmentData:
    """Data access layer for ticket assignments with proper ID handling"""
    
    @staticmethod
    def create(assignment_data: Dict[str, Any]) -> str:
        """Create a new assignment"""
        try:
            assignment_data['assignment_id'] = str(uuid.uuid4())
            assignment_data['assigned_at'] = datetime.now().isoformat()
            assignment_data['status'] = 'active'
            
            doc_id = ticket_assignments_table.insert(assignment_data)
            
            logger.info(f"Created assignment {assignment_data['assignment_id']} with doc_id {doc_id}")
            return assignment_data['assignment_id']
            
        except Exception as e:
            logger.error(f"Error creating assignment: {e}")
            raise Exception(f"Failed to create assignment: {str(e)}")
    
    @staticmethod
    def get_by_ticket_id(ticket_id: str) -> List[Dict[str, Any]]:
        """Get assignments for a ticket"""
        try:
            Assignment = Query()
            return ticket_assignments_table.search(Assignment.ticket_id == ticket_id)
        except Exception as e:
            logger.error(f"Error getting assignments for ticket {ticket_id}: {e}")
            return []
    
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
        except Exception as e:
            logger.error(f"Error updating assignment {assignment_id}: {e}")
            return False

def get_ticket_statistics() -> Dict[str, Any]:
    """Get comprehensive ticket statistics"""
    try:
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
        
    except Exception as e:
        logger.error(f"Error getting ticket statistics: {e}")
        return {
            'total_tickets': 0,
            'by_status': {},
            'by_category': {},
            'by_urgency': {},
            'open_tickets': 0,
            'closed_tickets': 0,
            'error': str(e)
        }

def cleanup_old_tickets(days_old: int = 90) -> int:
    """
    Clean up old closed tickets
    
    Args:
        days_old: Remove tickets closed more than this many days ago
        
    Returns:
        Number of tickets cleaned up
    """
    try:
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
        
        Ticket = Query()
        old_tickets = tickets_table.search(
            (Ticket.status == TicketStatus.CLOSED.value) & 
            (Ticket.closed_at < cutoff_date)
        )
        
        old_ticket_ids = [ticket.get('ticket_id') for ticket in old_tickets if ticket.get('ticket_id')]
        
        # Remove associated assignment records
        Assignment = Query()
        for ticket_id in old_ticket_ids:
            ticket_assignments_table.remove(Assignment.ticket_id == ticket_id)
        
        # Remove old tickets
        tickets_table.remove(
            (Ticket.status == TicketStatus.CLOSED.value) & 
            (Ticket.closed_at < cutoff_date)
        )
        
        logger.info(f"Cleaned up {len(old_ticket_ids)} old tickets")
        return len(old_ticket_ids)
        
    except Exception as e:
        logger.error(f"Error cleaning up old tickets: {e}")
        return 0

def validate_ticket_data(ticket_data: Dict[str, Any]) -> bool:
    """
    Validate ticket data has required fields
    
    Args:
        ticket_data: Ticket data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['category', 'short_description']
    
    for field in required_fields:
        if field not in ticket_data or not ticket_data[field]:
            logger.warning(f"Ticket data missing required field: {field}")
            return False
    
    return True

def get_tickets_requiring_attention() -> List[Dict[str, Any]]:
    """
    Get tickets that require immediate attention
    
    Returns:
        List of high priority or overdue tickets
    """
    try:
        # Get all open tickets
        Ticket = Query()
        open_tickets = tickets_table.search(
            Ticket.status.one_of(['New', 'In Progress', 'Pending'])
        )
        
        attention_tickets = []
        current_time = datetime.now()
        
        for ticket in open_tickets:
            # High urgency tickets
            if ticket.get('urgency') == '1':
                attention_tickets.append(ticket)
                continue
            
            # Tickets older than 24 hours without progress
            created_at = ticket.get('created_at')
            if created_at:
                try:
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if (current_time - created_time).days > 1 and ticket.get('status') == 'New':
                        attention_tickets.append(ticket)
                except Exception:
                    continue
        
        return attention_tickets
        
    except Exception as e:
        logger.error(f"Error getting tickets requiring attention: {e}")
        return []

# Export everything needed by the ticket system
__all__ = [
    'TicketStatus', 'TicketCategory', 'TicketSubcategory', 'TicketUrgency', 'TicketRequestType',
    'TicketData', 'AssignmentData', 
    'get_ticket_by_id', 'update_ticket_by_id', 'remove_ticket_by_id',
    'get_ticket_statistics', 'cleanup_old_tickets', 'validate_ticket_data',
    'get_tickets_requiring_attention',
    'tickets_table', 'ticket_assignments_table'
]