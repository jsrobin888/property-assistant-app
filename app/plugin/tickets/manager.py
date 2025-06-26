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
            
            # ADD THIS: Debug logging
            logger.info(f"Building ticket from email: {subject[:50]}...")
            logger.info(f"Email data keys: {list(self.email_data.keys())}")
            logger.info(f"Action item keys: {list(self.action_item.keys())}")
            
            # Get action item details
            action_data = self.action_item.get('action_data', {})
            category_hint = action_data.get('category', 'maintenance')
            
            # ADD THIS: More debug logging
            logger.info(f"Action data: {action_data}")
            logger.info(f"Category hint: {category_hint}")
            
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
            
            # ADD THIS: Log the key fields
            logger.info(f"Ticket fields: category={category}, urgency={urgency}, short_desc={short_description[:30]}...")
            
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
            
            # ADD THIS: Log the final ticket data
            logger.info(f"Ticket data created successfully: {ticket_data.get('ticket_id', 'No ID')}")
            return ticket_data
            
        except Exception as e:
            logger.error(f"Error building ticket data: {e}")
            # ADD THIS: Log more details about the error
            logger.error(f"Email data: {self.email_data}")
            logger.error(f"Action item: {self.action_item}")
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
        try:
            is_valid, missing_fields = TicketSchemaValidator.validate_ticket_data(self.ticket_data)
            
            if not is_valid:
                # CHANGE THIS: More detailed error logging
                logger.error(f"Ticket validation failed. Missing fields: {missing_fields}")
                logger.error(f"Ticket data fields present: {list(self.ticket_data.keys())}")
                logger.error(f"Ticket data: {self.ticket_data}")
                return False
            
            # ADD THIS: Success logging
            logger.info("Ticket validation passed successfully")
            return True
            
        except Exception as e:
            # ADD THIS: Catch validation errors
            logger.error(f"Error during ticket validation: {e}")
            return False
    
    def save(self) -> Optional[str]:
        """Save ticket to database"""
        try:
            logger.info("Starting ticket save process...")
            
            if not self.validate():
                logger.error("Cannot save invalid ticket - validation failed")
                return None
            
            logger.info("Ticket validation passed, creating in database...")
            
            # ADD THIS: More detailed database operation logging
            try:
                ticket_id = TicketData.create(self.ticket_data)
                logger.info(f"TicketData.create returned: {ticket_id}")
            except Exception as create_error:
                logger.error(f"TicketData.create failed: {create_error}")
                raise
            
            if not ticket_id:
                logger.error("TicketData.create returned None or empty ticket_id")
                return None
            
            # Create assignment record
            try:
                assignment_result = AssignmentData.create({
                    'ticket_id': ticket_id,
                    'assigned_to': self.ticket_data['assigned_to'],
                    'assignment_group': self.ticket_data['assignment_group']
                })
                logger.info(f"Assignment created: {assignment_result}")
            except Exception as assignment_error:
                # DON'T FAIL the whole ticket for assignment errors
                logger.warning(f"Assignment creation failed (non-fatal): {assignment_error}")
            
            logger.info(f"Successfully created ticket {ticket_id} from email {self.email_data.get('id', 'unknown')}")
            return ticket_id
            
        except Exception as e:
            logger.error(f"Error saving ticket: {e}")
            # ADD THIS: Don't hide the error details
            logger.error(f"Ticket data that failed to save: {self.ticket_data}")
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
        logger.info("=== STARTING PUSH_TICKET ===")
        
        if not isinstance(ticket, Ticket):
            logger.error("Invalid ticket object provided to push_ticket")
            return None
        
        logger.info("Ticket object is valid, calling save()...")
        
        ticket_id = ticket.save()
        
        if ticket_id:
            logger.info(f"✅ Successfully pushed ticket {ticket_id}")
        else:
            logger.error("❌ Failed to push ticket - save() returned None")
            # ADD THIS: Try to get more info about why it failed
            logger.error(f"Ticket object state: email_id={ticket.email_data.get('id')}")
            logger.error(f"Action item state: {ticket.action_item.get('id', 'No ID')}")
        
        return ticket_id
        
    except Exception as e:
        logger.error(f"❌ Error in push_ticket: {e}")
        # ADD THIS: More detailed error context
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")
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

def debug_ticket_creation(email_data: Dict[str, Any], action_item: Dict[str, Any]) -> bool:
    """
    Debug function to test ticket creation step by step
    ADD THIS FUNCTION to your manager.py
    """
    try:
        logger.info("=== DEBUG TICKET CREATION ===")
        logger.info(f"Email data: {email_data}")
        logger.info(f"Action item: {action_item}")
        
        # Step 1: Create ticket object
        logger.info("Step 1: Creating Ticket object...")
        ticket = Ticket(email_data, action_item)
        logger.info("✅ Ticket object created")
        
        # Step 2: Test validation
        logger.info("Step 2: Testing validation...")
        is_valid = ticket.validate()
        logger.info(f"Validation result: {is_valid}")
        
        if not is_valid:
            logger.error("❌ Validation failed, stopping debug")
            return False
        
        # Step 3: Test save
        logger.info("Step 3: Testing save...")
        ticket_id = ticket.save()
        logger.info(f"Save result: {ticket_id}")
        
        if ticket_id:
            logger.info("✅ Ticket creation successful!")
            return True
        else:
            logger.error("❌ Save failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Debug ticket creation failed: {e}")
        return False