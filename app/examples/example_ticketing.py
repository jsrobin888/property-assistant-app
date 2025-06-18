# =============================================================================
# STANDALONE TICKET OPERATIONS
# =============================================================================

from ..plugin.tickets import Ticket, TicketStatus

# Get a ticket
ticket = Ticket.get_by_id("TKT-12345")
print("ticket", ticket)

# Update ticket status
success = Ticket.update_status("TKT-12345", TicketStatus.IN_PROGRESS, "Started working on this")
print("success", success)

# Assign ticket
success = Ticket.assign("TKT-12345", "john.technician@property.com", "Maintenance Team")
print("success", success)

# =============================================================================
# API USAGE EXAMPLES
# =============================================================================

# GET /api/tickets/
# Get all tickets with pagination and filtering

# GET /api/tickets/TKT-12345
# Get specific ticket

# PUT /api/tickets/TKT-12345
# Update ticket status or assignment

# GET /api/tickets/stats/summary
# Get ticket statistics

# POST /api/tickets/batch/assign
# Assign multiple tickets at once

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

from ..plugin.tickets.utils import cleanup_old_tickets, generate_ticket_report

# Clean up old tickets
cleaned_count = cleanup_old_tickets(days_old=90)

# Generate comprehensive report
report = generate_ticket_report()

# =============================================================================
# SCHEMA EXAMPLE - What your tickets look like
# =============================================================================

example_ticket = {
    "ticket_id": "TKT-A1B2C3D4",
    "short_description": "Maintenance request: Broken toilet in Unit 3B",
    "description": "Tenant reported: Toilet is not flushing properly...",
    "category": "Maintenance",
    "subcategory": "Plumbing",
    "request_type": "Repair",
    "urgency": "1",           # 1=High, 2=Medium, 3=Low
    "priority": "1",          # Auto-calculated from urgency
    "property_id": "P3B0",    # Auto-generated from unit
    "unit_number": "Unit 3B", # Extracted from email
    "requested_for": "john.tenant@example.com",
    "assignment_group": "Property Maintenance",
    "assigned_to": "plumber@property.com",  # Auto-assigned based on subcategory
    "status": "New",
    "created_at": "2025-06-17T10:30:00",
    "email_id": "email_123",
    "metadata": {
        "email_subject": "Broken toilet in Unit 3B",
        "email_sender": "john.tenant@example.com",
        "requires_contractor": False,
        "after_hours": False
    }
}

#!/usr/bin/env python3
"""
Fixed example ticketing script
This demonstrates the proper way to use the ticket system
"""

from datetime import datetime

# =============================================================================
# FIRST: CREATE A TICKET (since database is empty)
# =============================================================================

def create_sample_ticket():
    """Create a sample ticket first"""
    print("🎫 Creating a sample ticket first...")
    
    from ..plugin.tickets import Ticket, push_ticket
    
    # Sample email data (as would come from email processing)
    email_data = {
        'id': 'example_email_001',
        'sender': 'john.tenant@example.com',
        'subject': 'Broken faucet in Unit 2A',
        'body': '''Hi Property Management,
        
        The kitchen faucet in my apartment (Unit 2A) is leaking badly. 
        Water keeps dripping and I can't turn it off completely.
        Please send someone to fix it as soon as possible.
        
        Thank you,
        John Doe
        Unit 2A''',
        'date': datetime.now()
    }
    
    # Sample action item (as would be created by email processor)
    action_item = {
        'id': 'example_action_001',
        'action_data': {
            'action': 'create_maintenance_ticket',
            'category': 'maintenance',
            'details': 'Kitchen faucet leaking, cannot turn off completely',
            'priority': 'high',
            'tenant': {
                'name': 'John Doe',
                'email': 'john.tenant@example.com',
                'unit': 'Unit 2A'
            },
            'estimated_cost': 'low',
            'requires_contractor': False,
            'after_hours': False
        }
    }
    
    try:
        # Create and save ticket
        ticket = Ticket(email_data, action_item)
        ticket_id = push_ticket(ticket)
        
        if ticket_id:
            print(f"✅ Created sample ticket: {ticket_id}")
            return ticket_id
        else:
            print("❌ Failed to create sample ticket")
            return None
            
    except Exception as e:
        print(f"❌ Error creating sample ticket: {e}")
        return None

# =============================================================================
# STANDALONE TICKET OPERATIONS (UPDATED)
# =============================================================================

def demonstrate_ticket_operations():
    """Demonstrate ticket operations with proper setup"""
    
    from ..plugin.tickets import Ticket, TicketStatus
    
    print("\n" + "="*60)
    print("🔧 STANDALONE TICKET OPERATIONS")
    print("="*60)
    
    # First, create a ticket to work with
    ticket_id = create_sample_ticket()
    
    if not ticket_id:
        print("❌ Cannot demonstrate operations without a ticket")
        return
    
    print(f"\nNow demonstrating operations on ticket: {ticket_id}")
    
    # Get a ticket
    print("\n1️⃣ Getting ticket...")
    ticket = Ticket.get_by_id(ticket_id)
    print("ticket:", ticket['ticket_id'] if ticket else None)
    
    if ticket:
        print(f"   ✅ Found ticket: {ticket['ticket_id']}")
        print(f"   Description: {ticket['short_description']}")
        print(f"   Status: {ticket['status']}")
        print(f"   Category: {ticket['category']}")
        print(f"   Urgency: {ticket['urgency']}")
    else:
        print("   ❌ Ticket not found")
        return
    
    # Update ticket status
    print("\n2️⃣ Updating ticket status...")
    success = Ticket.update_status(ticket_id, TicketStatus.IN_PROGRESS, "Started working on this")
    print("success:", success)
    
    if success:
        print("   ✅ Status updated successfully")
        # Verify the update
        updated_ticket = Ticket.get_by_id(ticket_id)
        print(f"   New status: {updated_ticket['status']}")
    else:
        print("   ❌ Failed to update status")
    
    # Assign ticket
    print("\n3️⃣ Assigning ticket...")
    success = Ticket.assign(ticket_id, "john.technician@property.com", "Maintenance Team")
    print("success:", success)
    
    if success:
        print("   ✅ Ticket assigned successfully")
        # Verify the assignment
        assigned_ticket = Ticket.get_by_id(ticket_id)
        print(f"   Assigned to: {assigned_ticket['assigned_to']}")
        print(f"   Assignment group: {assigned_ticket['assignment_group']}")
    else:
        print("   ❌ Failed to assign ticket")

def show_all_tickets():
    """Show all tickets in the system"""
    print("\n" + "="*60)
    print("📋 ALL TICKETS IN SYSTEM")
    print("="*60)
    
    try:
        from ..plugin.tickets.models import TicketData
        
        all_tickets = TicketData.get_all()
        
        if not all_tickets:
            print("No tickets found in system")
            return
        
        print(f"Found {len(all_tickets)} tickets:")
        
        for i, ticket in enumerate(all_tickets, 1):
            print(f"\n{i}. Ticket ID: {ticket['ticket_id']}")
            print(f"   Description: {ticket['short_description']}")
            print(f"   Status: {ticket['status']}")
            print(f"   Category: {ticket['category']}")
            print(f"   Created: {ticket['created_at']}")
            print(f"   Assigned to: {ticket['assigned_to']}")
            
    except Exception as e:
        print(f"❌ Error retrieving tickets: {e}")

def show_statistics():
    """Show ticket statistics"""
    print("\n" + "="*60)
    print("📊 TICKET STATISTICS")
    print("="*60)
    
    try:
        from ..plugin.tickets.manager import get_ticket_statistics
        
        stats = get_ticket_statistics()
        
        print(f"Total tickets: {stats['total_tickets']}")
        print(f"Open tickets: {stats['open_tickets']}")
        print(f"Closed tickets: {stats['closed_tickets']}")
        
        if stats['by_status']:
            print("\nBy Status:")
            for status, count in stats['by_status'].items():
                print(f"  {status}: {count}")
        
        if stats['by_category']:
            print("\nBy Category:")
            for category, count in stats['by_category'].items():
                print(f"  {category}: {count}")
        
        if stats['by_urgency']:
            print("\nBy Urgency:")
            urgency_labels = {'1': 'High', '2': 'Medium', '3': 'Low'}
            for urgency, count in stats['by_urgency'].items():
                label = urgency_labels.get(urgency, urgency)
                print(f"  {label} ({urgency}): {count}")
                
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main function to run all demonstrations"""
    print("🚀 TICKET MANAGEMENT SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    try:
        # Test imports first
        from ..plugin.tickets import Ticket, TicketStatus, push_ticket
        print("✅ Successfully imported ticket modules")
        
        # Demonstrate ticket operations
        demonstrate_ticket_operations()
        
        # Show all tickets
        show_all_tickets()
        
        # Show statistics
        show_statistics()
        
        print("\n" + "="*60)
        print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure the ticket modules are properly installed")
        print("Run: python setup_and_test.py first")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()