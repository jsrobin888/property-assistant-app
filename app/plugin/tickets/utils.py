"""
Utility functions for ticket operations
Helper functions and cleanup utilities
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from .models import TicketData, tickets_table, ticket_assignments_table, TicketStatus
from tinydb import Query

logger = logging.getLogger(__name__)

def cleanup_old_tickets(days_old: int = 90) -> int:
    """
    Clean up old closed tickets
    
    Args:
        days_old: Remove tickets closed more than this many days ago
        
    Returns:
        Number of tickets cleaned up
    """
    try:
        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
        
        Ticket = Query()
        old_tickets = tickets_table.search(
            (Ticket.status == TicketStatus.CLOSED.value) & 
            (Ticket.closed_at < cutoff_date)
        )
        
        old_ticket_ids = [ticket['ticket_id'] for ticket in old_tickets]
        
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

def validate_email_data(email_data: Dict[str, Any]) -> bool:
    """
    Validate that email data has required fields for ticket creation
    
    Args:
        email_data: Email data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['sender', 'subject']
    
    for field in required_fields:
        if field not in email_data or not email_data[field]:
            logger.warning(f"Email data missing required field: {field}")
            return False
    
    return True

def validate_action_item(action_item: Dict[str, Any]) -> bool:
    """
    Validate that action item has required fields for ticket creation
    
    Args:
        action_item: Action item dictionary
        
    Returns:
        True if valid, False otherwise
    """
    if 'action_data' not in action_item:
        logger.warning("Action item missing action_data")
        return False
    
    action_data = action_item['action_data']
    
    if 'category' not in action_data:
        logger.warning("Action item missing category")
        return False
    
    return True

def extract_tenant_name(sender_email: str) -> str:
    """
    Extract tenant name from sender email
    
    Args:
        sender_email: Email address
        
    Returns:
        Formatted tenant name
    """
    try:
        # Handle emails with names: "John Doe <john@example.com>"
        if '<' in sender_email:
            name_part = sender_email.split('<')[0].strip()
            if name_part:
                return name_part
        
        # Extract from email address: "john.doe@example.com" -> "John Doe"
        local_part = sender_email.split('@')[0]
        name = local_part.replace('.', ' ').replace('_', ' ').title()
        return name
        
    except Exception:
        return "Tenant"

def format_ticket_summary(ticket: Dict[str, Any]) -> str:
    """
    Format a ticket summary for logging or display
    
    Args:
        ticket: Ticket data dictionary
        
    Returns:
        Formatted summary string
    """
    try:
        summary = f"Ticket {ticket.get('ticket_id', 'Unknown')}: "
        summary += f"{ticket.get('short_description', 'No description')[:50]}... "
        summary += f"[{ticket.get('category', 'Unknown')}/{ticket.get('urgency', 'Unknown')}] "
        summary += f"Status: {ticket.get('status', 'Unknown')} "
        summary += f"Assigned: {ticket.get('assigned_to', 'Unassigned')}"
        
        return summary
        
    except Exception:
        return f"Ticket {ticket.get('ticket_id', 'Unknown')}: [Error formatting summary]"

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

def generate_ticket_report() -> Dict[str, Any]:
    """
    Generate a comprehensive ticket report
    
    Returns:
        Dictionary with ticket statistics and summaries
    """
    try:
        from .models import get_ticket_statistics
        
        stats = get_ticket_statistics()
        attention_tickets = get_tickets_requiring_attention()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': stats,
            'tickets_requiring_attention': len(attention_tickets),
            'attention_ticket_details': [
                {
                    'ticket_id': ticket['ticket_id'],
                    'short_description': ticket['short_description'],
                    'urgency': ticket['urgency'],
                    'status': ticket['status'],
                    'created_at': ticket['created_at']
                }
                for ticket in attention_tickets[:10]  # Top 10
            ],
            'recommendations': []
        }
        
        # Add recommendations based on stats
        if stats['open_tickets'] > stats['closed_tickets']:
            report['recommendations'].append("High number of open tickets - consider increasing staff")
        
        if stats['by_urgency'].get('1', 0) > 5:
            report['recommendations'].append("Multiple high urgency tickets - review emergency procedures")
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating ticket report: {e}")
        return {'error': str(e)}

def search_tickets(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search tickets by content
    
    Args:
        query: Search query string
        limit: Maximum number of results
        
    Returns:
        List of matching tickets
    """
    try:
        query_lower = query.lower()
        all_tickets = TicketData.get_all(limit=1000)  # Get more for searching
        
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
            """.lower()
            
            if query_lower in searchable_text:
                matching_tickets.append(ticket)
                
                if len(matching_tickets) >= limit:
                    break
        
        return matching_tickets
        
    except Exception as e:
        logger.error(f"Error searching tickets: {e}")
        return []

def export_tickets_to_csv(tickets: List[Dict[str, Any]]) -> str:
    """
    Export tickets to CSV format
    
    Args:
        tickets: List of ticket dictionaries
        
    Returns:
        CSV content as string
    """
    try:
        import csv
        import io
        
        output = io.StringIO()
        
        if not tickets:
            return ""
        
        # Define CSV headers
        headers = [
            'ticket_id', 'short_description', 'category', 'subcategory',
            'urgency', 'status', 'property_id', 'unit_number',
            'requested_for', 'assigned_to', 'created_at'
        ]
        
        writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        
        for ticket in tickets:
            writer.writerow(ticket)
        
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error exporting tickets to CSV: {e}")
        return ""