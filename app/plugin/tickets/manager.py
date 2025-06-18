"""
Core ticket management functionality
Provides Ticket class and push_ticket function for email integration
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .models import TicketData, TicketStatus, AssignmentData
from .schema import (
    TicketSchemaValidator, 
    CategoryMapper, 
    PropertyInfoExtractor, 
    AssignmentMapper
)

logger = logging.getLogger(__name__)

class Ticket:
    """Main Ticket class for creating and managing tickets"""
    
    def __init__(self, email_data: Dict[str, Any], action_item: Dict[str, Any]):
        """
        Initialize ticket from email data and action item
        
        Args:
            email_data: Email information (sender, subject, body, etc.)
            action_item: Action item extracted from email processing
        """
        self.email_data = email_data
        self.action_item = action_item
        self.ticket_data = self._build_ticket_data()
    
    def _build_ticket_data(self) -> Dict[str, Any]:
        """Build complete ticket data following the schema"""
        try:
            # Extract content for analysis
            subject = self.email_data.get('subject', '')
            body = self.email_data.get('body', '')
            content = f"{subject} {body}"
            
            # Get action item details
            action_data = self.action_item.get('action_data', {})
            category_hint = action_data.get('category', 'maintenance')
            
            # Determine ticket categorization
            category, request_type = CategoryMapper.determine_category_from_content(content)
            subcategory = CategoryMapper.determine_subcategory(content, category)
            urgency = CategoryMapper.determine_urgency(content)
            
            # Extract property/unit information
            unit_info = PropertyInfoExtractor.extract_unit_info(content)
            property_id = PropertyInfoExtractor.generate_property_id(unit_info)
            
            # Get assignment information
            assignment_group, assigned_to = AssignmentMapper.get_assignment(category, subcategory)
            
            # Generate descriptions
            short_description = self._generate_short_description(subject, category)
            description = self._generate_full_description(content, action_data)
            
            # Build complete ticket schema
            ticket_data = TicketSchemaValidator.create_ticket_schema(
                short_description=short_description,
                description=description,
                category=category,
                subcategory=subcategory,
                request_type=request_type,
                urgency=urgency,
                property_id=property_id,
                unit_number=unit_info,
                requested_for=self.email_data.get('sender', ''),
                assignment_group=assignment_group,
                assigned_to=assigned_to,
                # Additional metadata
                email_id=self.email_data.get('id', ''),
                action_item_id=self.action_item.get('id', ''),
                metadata={
                    'email_subject': subject,
                    'email_sender': self.email_data.get('sender', ''),
                    'action_type': action_data.get('action', ''),
                    'estimated_cost': action_data.get('estimated_cost', 'unknown'),
                    'requires_contractor': action_data.get('requires_contractor', False),
                    'after_hours': action_data.get('after_hours', False)
                }
            )
            
            return ticket_data
            
        except Exception as e:
            logger.error(f"Error building ticket data: {e}")
            raise
    
    def _generate_short_description(self, subject: str, category: str) -> str:
        """Generate concise short description"""
        if category == "Maintenance":
            return f"Maintenance request: {subject}"
        elif category == "Complaint":
            return f"Tenant complaint: {subject}"
        elif category == "Payment":
            return f"Payment inquiry: {subject}"
        elif category == "Lease":
            return f"Lease inquiry: {subject}"
        else:
            return f"Tenant request: {subject}"
    
    def _generate_full_description(self, content: str, action_data: Dict[str, Any]) -> str:
        """Generate detailed description"""
        description = f"Tenant reported: {action_data.get('details', content[:200])}\n\n"
        description += f"Email content: {content[:300]}..."
        
        # Add additional context
        if action_data.get('requires_contractor'):
            description += "\n\nNote: May require external contractor."
        
        if action_data.get('after_hours'):
            description += "\n\nNote: Request received after business hours."
        
        return description
    
    def validate(self) -> bool:
        """Validate ticket data against schema"""
        is_valid, missing_fields = TicketSchemaValidator.validate_ticket_data(self.ticket_data)
        
        if not is_valid:
            logger.warning(f"Ticket validation failed. Missing fields: {missing_fields}")
        
        return is_valid
    
    def save(self) -> Optional[str]:
        """Save ticket to database"""
        try:
            if not self.validate():
                logger.error("Cannot save invalid ticket")
                return None
            
            ticket_id = TicketData.create(self.ticket_data)
            
            # Create assignment record
            AssignmentData.create({
                'ticket_id': ticket_id,
                'assigned_to': self.ticket_data['assigned_to'],
                'assignment_group': self.ticket_data['assignment_group']
            })
            
            logger.info(f"Created ticket {ticket_id} from email {self.email_data.get('id', 'unknown')}")
            return ticket_id
            
        except Exception as e:
            logger.error(f"Error saving ticket: {e}")
            return None
    
    @classmethod
    def get_by_id(cls, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID"""
        return TicketData.get_by_id(ticket_id)
    
    @classmethod
    def update_status(cls, ticket_id: str, status: TicketStatus, notes: str = None) -> bool:
        """Update ticket status"""
        try:
            update_data = {'status': status.value}
            
            if notes:
                update_data['status_notes'] = notes
            
            if status == TicketStatus.RESOLVED:
                update_data['resolved_at'] = datetime.now().isoformat()
            elif status == TicketStatus.CLOSED:
                update_data['closed_at'] = datetime.now().isoformat()
            
            return TicketData.update(ticket_id, update_data)
            
        except Exception as e:
            logger.error(f"Error updating ticket status: {e}")
            return False
    
    @classmethod
    def assign(cls, ticket_id: str, assigned_to: str, assignment_group: str = None) -> bool:
        """Assign ticket to a person/group"""
        try:
            update_data = {'assigned_to': assigned_to}
            
            if assignment_group:
                update_data['assignment_group'] = assignment_group
            
            success = TicketData.update(ticket_id, update_data)
            
            # Create new assignment record
            if success:
                AssignmentData.create({
                    'ticket_id': ticket_id,
                    'assigned_to': assigned_to,
                    'assignment_group': assignment_group or 'General Support'
                })
            
            return success
            
        except Exception as e:
            logger.error(f"Error assigning ticket: {e}")
            return False

def push_ticket(ticket: Ticket) -> Optional[str]:
    """
    Push ticket to the system - main integration point for email processing
    
    Args:
        ticket: Ticket instance to be saved
        
    Returns:
        ticket_id if successful, None if failed
    """
    try:
        if not isinstance(ticket, Ticket):
            logger.error("Invalid ticket object provided to push_ticket")
            return None
        
        ticket_id = ticket.save()
        
        if ticket_id:
            logger.info(f"Successfully pushed ticket {ticket_id}")
        else:
            logger.error("Failed to push ticket")
        
        return ticket_id
        
    except Exception as e:
        logger.error(f"Error in push_ticket: {e}")
        return None

# Additional utility functions for ticket management

def get_tickets_by_email(email_id: str) -> List[Dict[str, Any]]:
    """Get all tickets created from a specific email"""
    return TicketData.get_by_email_id(email_id)

def get_open_tickets() -> List[Dict[str, Any]]:
    """Get all open tickets (New, In Progress, Pending)"""
    open_statuses = [TicketStatus.NEW, TicketStatus.IN_PROGRESS, TicketStatus.PENDING]
    open_tickets = []
    
    for status in open_statuses:
        tickets = TicketData.get_by_status(status)
        open_tickets.extend(tickets)
    
    return open_tickets

def get_ticket_statistics() -> Dict[str, Any]:
    """Get ticket statistics"""
    from .models import get_ticket_statistics
    return get_ticket_statistics()

# Batch operations
def bulk_assign_tickets(ticket_ids: List[str], assigned_to: str, assignment_group: str = None) -> Dict[str, Any]:
    """Assign multiple tickets to a person/group"""
    results = []
    successful = 0
    
    for ticket_id in ticket_ids:
        success = Ticket.assign(ticket_id, assigned_to, assignment_group)
        results.append({
            'ticket_id': ticket_id,
            'success': success
        })
        if success:
            successful += 1
    
    return {
        'successful_count': successful,
        'total_count': len(ticket_ids),
        'results': results
    }

def bulk_update_status(ticket_ids: List[str], status: TicketStatus, notes: str = None) -> Dict[str, Any]:
    """Update status for multiple tickets"""
    results = []
    successful = 0
    
    for ticket_id in ticket_ids:
        success = Ticket.update_status(ticket_id, status, notes)
        results.append({
            'ticket_id': ticket_id,
            'success': success
        })
        if success:
            successful += 1
    
    return {
        'successful_count': successful,
        'total_count': len(ticket_ids),
        'results': results
    }