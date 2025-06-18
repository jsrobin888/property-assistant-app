"""
Ticket Management Module
Clean, professional ticket management system for property management
"""

from .manager import Ticket, push_ticket
from .models import TicketStatus, TicketCategory, TicketUrgency, TicketRequestType
from .utils import cleanup_old_tickets, generate_ticket_report

# Main exports for clean integration
__all__ = [
    'Ticket',
    'push_ticket',
    'TicketStatus',
    'TicketCategory', 
    'TicketUrgency',
    'TicketRequestType',
    'cleanup_old_tickets',
    'generate_ticket_report'
]

# Version info
__version__ = "1.0.0"
__author__ = "Property Management System"
__description__ = "Professional ticket management system with email integration"