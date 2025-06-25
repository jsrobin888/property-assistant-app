# Ticket Management System

## Ticket Schema & Data Structure

### Complete Ticket Schema
```python
{
    "ticket_id": "TKT-A1B2C3D4",           # Auto-generated unique ID
    "short_description": "Maintenance request: Broken toilet in Unit 3B",
    "description": "Tenant reported: Toilet is not flushing properly...",
    "category": "Maintenance",              # Primary category
    "subcategory": "Plumbing",             # Specific subcategory  
    "request_type": "Repair",              # Type of request
    "urgency": "1",                        # 1=High, 2=Medium, 3=Low
    "priority": "1",                       # Auto-calculated from urgency
    "property_id": "P3B0",                 # Auto-generated from unit
    "unit_number": "Unit 3B",              # Extracted from email
    "requested_for": "john.tenant@example.com",
    "assignment_group": "Property Maintenance",
    "assigned_to": "plumber@property.com", # Auto-assigned based on subcategory
    "status": "New",                       # Current status
    "created_at": "2025-06-17T10:30:00Z",
    "updated_at": "2025-06-17T10:30:00Z",
    "email_id": "email_123",               # Source email reference
    "metadata": {
        "email_subject": "Broken toilet in Unit 3B",
        "email_sender": "john.tenant@example.com",
        "requires_contractor": false,
        "after_hours": false,
        "estimated_cost": "low"
    }
}
```

## Category Classification System

### Primary Categories
```python
class TicketCategory(str, Enum):
    MAINTENANCE = "Maintenance"     # Repairs, fixes, general upkeep
    UTILITIES = "Utilities"         # Water, electricity, gas, internet
    LEASE = "Lease"                # Lease-related inquiries
    MOVE_IN_OUT = "Move-in/out"    # Moving logistics
    COMPLAINT = "Complaint"         # Noise, neighbor issues
    PAYMENT = "Payment"            # Rent, fees, billing
    AMENITY = "Amenity"           # Pool, gym, common areas
```

### Subcategory Mapping
```python
MAINTENANCE_SUBCATEGORIES = {
    'plumbing': ['toilet', 'sink', 'faucet', 'pipe', 'leak', 'water'],
    'electrical': ['outlet', 'switch', 'power', 'light', 'electrical'],
    'hvac': ['heating', 'cooling', 'air conditioning', 'furnace', 'hvac'],
    'appliance': ['refrigerator', 'stove', 'oven', 'dishwasher', 'washer'],
    'cleaning': ['clean', 'dirty', 'trash', 'pest', 'mold'],
    'general_repair': ['door', 'window', 'wall', 'floor', 'ceiling']
}

COMPLAINT_SUBCATEGORIES = {
    'noise_complaint': ['noise', 'loud', 'music', 'party', 'barking'],
    'neighbor_dispute': ['neighbor', 'dispute', 'conflict', 'harassment'],
    'parking': ['parking', 'car', 'vehicle', 'tow', 'spot'],
    'security': ['security', 'safety', 'break in', 'theft']
}
```

### Urgency Level Determination
```python
def determine_urgency(content: str) -> str:
    content_lower = content.lower()
    
    # High Urgency (1) - Emergency situations
    emergency_keywords = [
        'emergency', 'urgent', 'immediate', 'flooding', 'gas leak',
        'fire', 'smoke', 'water damage', 'electrical hazard',
        'no heat', 'no hot water', 'toilet overflow', 'ceiling leak',
        'locked out', 'door won\'t lock', 'broken window'
    ]
    
    # Medium Urgency (2) - Standard issues
    standard_keywords = [
        'broken', 'not working', 'repair', 'fix', 'issue', 'problem'
    ]
    
    if any(keyword in content_lower for keyword in emergency_keywords):
        return "1"  # High
    elif any(keyword in content_lower for keyword in standard_keywords):
        return "2"  # Medium  
    else:
        return "3"  # Low
```

## Automatic Assignment System

### Assignment Rules Engine
```python
class AssignmentMapper:
    ASSIGNMENT_MAPPING = {
        TicketCategory.MAINTENANCE.value: {
            'assignment_group': 'Property Maintenance',
            'assigned_to': 'maintenance@property.com'
        },
        TicketCategory.COMPLAINT.value: {
            'assignment_group': 'Property Management',
            'assigned_to': 'manager@property.com'
        },
        TicketCategory.PAYMENT.value: {
            'assignment_group': 'Accounting',
            'assigned_to': 'accounting@property.com'
        },
        TicketCategory.LEASE.value: {
            'assignment_group': 'Leasing Office', 
            'assigned_to': 'leasing@property.com'
        }
    }
    
    # Specialist assignments override general assignments
    SPECIALIST_ASSIGNMENTS = {
        TicketSubcategory.PLUMBING.value: 'plumber@property.com',
        TicketSubcategory.ELECTRICAL.value: 'electrician@property.com',
        TicketSubcategory.HVAC.value: 'hvac@property.com',
        TicketSubcategory.APPLIANCE.value: 'appliance@property.com'
    }
    
    @classmethod
    def get_assignment(cls, category: str, subcategory: str = None) -> Tuple[str, str]:
        # Get base assignment
        base = cls.ASSIGNMENT_MAPPING.get(category, {
            'assignment_group': 'General Support',
            'assigned_to': 'support@property.com'
        })
        
        assignment_group = base['assignment_group']
        assigned_to = base['assigned_to']
        
        # Override with specialist if available
        if subcategory in cls.SPECIALIST_ASSIGNMENTS:
            assigned_to = cls.SPECIALIST_ASSIGNMENTS[subcategory]
        
        return assignment_group, assigned_to
```

### Assignment Escalation Rules
```python
def check_escalation_rules(ticket: Dict[str, Any]) -> Optional[str]:
    """Check if ticket needs escalation based on business rules"""
    
    # High urgency tickets unassigned for > 30 minutes
    if ticket['urgency'] == '1' and ticket['status'] == 'New':
        created_time = datetime.fromisoformat(ticket['created_at'])
        if (datetime.now() - created_time).total_seconds() > 1800:  # 30 minutes
            return 'supervisor@property.com'
    
    # Tickets requiring contractors
    if ticket.get('metadata', {}).get('requires_contractor'):
        return 'contractor_coordinator@property.com'
    
    # After-hours emergencies
    if ticket.get('metadata', {}).get('after_hours') and ticket['urgency'] == '1':
        return 'emergency_coordinator@property.com'
    
    return None
```

## Ticket Lifecycle Management

### Status Progression
```python
class TicketStatus(str, Enum):
    NEW = "New"                    # Just created
    IN_PROGRESS = "In Progress"    # Work started
    PENDING = "Pending"            # Waiting for parts/approval
    RESOLVED = "Resolved"          # Work completed
    CLOSED = "Closed"              # Tenant confirmed resolution

# Valid status transitions
STATUS_TRANSITIONS = {
    TicketStatus.NEW: [TicketStatus.IN_PROGRESS, TicketStatus.CLOSED],
    TicketStatus.IN_PROGRESS: [TicketStatus.PENDING, TicketStatus.RESOLVED, TicketStatus.CLOSED],
    TicketStatus.PENDING: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED],
    TicketStatus.RESOLVED: [TicketStatus.CLOSED, TicketStatus.IN_PROGRESS],  # Reopening
    TicketStatus.CLOSED: []  # Terminal state
}
```

### Automatic Status Updates
```python
def update_ticket_status(ticket_id: str, new_status: TicketStatus, notes: str = None):
    """Update ticket status with automatic timestamp management"""
    
    update_data = {
        'status': new_status.value,
        'updated_at': datetime.now().isoformat()
    }
    
    # Add status-specific timestamps
    if new_status == TicketStatus.IN_PROGRESS:
        update_data['started_at'] = datetime.now().isoformat()
    elif new_status == TicketStatus.RESOLVED:
        update_data['resolved_at'] = datetime.now().isoformat()
    elif new_status == TicketStatus.CLOSED:
        update_data['closed_at'] = datetime.now().isoformat()
    
    # Add notes if provided
    if notes:
        update_data['status_notes'] = notes
    
    return TicketData.update(ticket_id, update_data)
```

## Property Information Extraction

### Unit Identification System
```python
class PropertyInfoExtractor:
    UNIT_PATTERNS = [
        r'apt\s*(\w+)',           # "apt 3B"
        r'apartment\s*(\w+)',     # "apartment 3B"
        r'unit\s*(\w+)',          # "unit 3B"  
        r'#(\w+)',                # "#3B"
        r'room\s*(\w+)',          # "room 3B"
        r'suite\s*(\w+)',         # "suite 3B"
        r'(\d+[A-Z])',            # "3B" 
        r'(\d+\w+)',              # "3B1"
    ]
    
    @classmethod
    def extract_unit_info(cls, content: str) -> str:
        for pattern in cls.UNIT_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                unit = match.group(1).upper()
                return f"Unit {unit}"
        
        return "Unit not specified"
    
    @classmethod  
    def generate_property_id(cls, unit_info: str) -> str:
        """Generate property ID from unit information"""
        if 'Unit' in unit_info:
            unit_num = unit_info.replace('Unit ', '').strip()
            if unit_num and unit_num != 'not specified':
                # Create property ID: P + first 3 characters
                property_id = f"P{unit_num[:3].zfill(3)}"
                return property_id
        
        return "P000"  # Default property ID
```

### Address & Location Parsing
```python
def extract_location_details(email_content: str) -> Dict[str, str]:
    """Extract additional location information from email"""
    
    location_info = {
        'building': None,
        'floor': None,
        'section': None
    }
    
    # Building patterns
    building_patterns = [
        r'building\s*(\w+)',
        r'bldg\s*(\w+)',
        r'(\w+)\s*building'
    ]
    
    # Floor patterns
    floor_patterns = [
        r'(\d+)(?:st|nd|rd|th)\s*floor',
        r'floor\s*(\d+)',
        r'level\s*(\d+)'
    ]
    
    content_lower = email_content.lower()
    
    for pattern in building_patterns:
        match = re.search(pattern, content_lower)
        if match:
            location_info['building'] = match.group(1).upper()
            break
    
    for pattern in floor_patterns:
        match = re.search(pattern, content_lower)
        if match:
            location_info['floor'] = match.group(1)
            break
    
    return location_info
```

## Ticket Analytics & Reporting

### Performance Metrics
```python
def get_ticket_analytics() -> Dict[str, Any]:
    """Generate comprehensive ticket analytics"""
    
    all_tickets = TicketData.get_all(limit=10000)
    
    analytics = {
        'summary': {
            'total_tickets': len(all_tickets),
            'open_tickets': 0,
            'closed_tickets': 0,
            'avg_resolution_time': 0
        },
        'by_category': {},
        'by_urgency': {},
        'by_assignee': {},
        'trends': {
            'daily_creation': {},
            'resolution_rates': {}
        },
        'performance': {
            'sla_compliance': 0,
            'escalation_rate': 0,
            'tenant_satisfaction': 0
        }
    }
    
    resolution_times = []
    
    for ticket in all_tickets:
        # Count by status
        status = ticket.get('status', 'Unknown')
        if status in ['New', 'In Progress', 'Pending']:
            analytics['summary']['open_tickets'] += 1
        else:
            analytics['summary']['closed_tickets'] += 1
        
        # Count by category
        category = ticket.get('category', 'Unknown')
        analytics['by_category'][category] = analytics['by_category'].get(category, 0) + 1
        
        # Count by urgency
        urgency = ticket.get('urgency', '3')
        analytics['by_urgency'][urgency] = analytics['by_urgency'].get(urgency, 0) + 1
        
        # Count by assignee
        assignee = ticket.get('assigned_to', 'Unassigned')
        analytics['by_assignee'][assignee] = analytics['by_assignee'].get(assignee, 0) + 1
        
        # Calculate resolution time
        if ticket.get('resolved_at') and ticket.get('created_at'):
            try:
                created = datetime.fromisoformat(ticket['created_at'])
                resolved = datetime.fromisoformat(ticket['resolved_at'])
                resolution_time = (resolved - created).total_seconds() / 3600  # hours
                resolution_times.append(resolution_time)
            except:
                pass
    
    # Calculate average resolution time
    if resolution_times:
        analytics['summary']['avg_resolution_time'] = sum(resolution_times) / len(resolution_times)
    
    return analytics
```

### SLA Tracking
```python
SLA_TARGETS = {
    '1': {'response_time': 30, 'resolution_time': 240},    # 30 min / 4 hours
    '2': {'response_time': 120, 'resolution_time': 1440},  # 2 hours / 24 hours  
    '3': {'response_time': 480, 'resolution_time': 4320}   # 8 hours / 72 hours
}

def check_sla_compliance(ticket: Dict[str, Any]) -> Dict[str, bool]:
    """Check if ticket meets SLA requirements"""
    
    urgency = ticket.get('urgency', '3')
    targets = SLA_TARGETS.get(urgency, SLA_TARGETS['3'])
    
    compliance = {
        'response_time_met': False,
        'resolution_time_met': False
    }
    
    created_time = datetime.fromisoformat(ticket['created_at'])
    current_time = datetime.now()
    
    # Check response time (first status update)
    if ticket.get('started_at'):
        started_time = datetime.fromisoformat(ticket['started_at'])
        response_minutes = (started_time - created_time).total_seconds() / 60
        compliance['response_time_met'] = response_minutes <= targets['response_time']
    
    # Check resolution time
    if ticket.get('resolved_at'):
        resolved_time = datetime.fromisoformat(ticket['resolved_at'])
        resolution_minutes = (resolved_time - created_time).total_seconds() / 60
        compliance['resolution_time_met'] = resolution_minutes <= targets['resolution_time']
    elif ticket['status'] in ['New', 'In Progress', 'Pending']:
        # Check if still within SLA window
        elapsed_minutes = (current_time - created_time).total_seconds() / 60
        compliance['resolution_time_met'] = elapsed_minutes <= targets['resolution_time']
    
    return compliance
```

## Integration Points

### Email System Integration
```python
def create_tickets_from_email(email_data: Dict[str, Any], action_items: List[Dict[str, Any]]) -> List[str]:
    """Create tickets from email action items"""
    
    created_tickets = []
    
    for action_item in action_items:
        try:
            # Create ticket instance
            ticket = Ticket(email_data, action_item)
            
            # Validate ticket data
            if ticket.validate():
                ticket_id = ticket.save()
                if ticket_id:
                    created_tickets.append(ticket_id)
                    
                    # Link ticket to email
                    EmailMessage.add_ticket_reference(email_data['id'], ticket_id)
                    
        except Exception as e:
            logger.error(f"Failed to create ticket from action item: {e}")
    
    return created_tickets
```

### Notification System Integration
```python
def send_ticket_notifications(ticket_id: str, event_type: str):
    """Send notifications for ticket events"""
    
    ticket = TicketData.get_by_id(ticket_id)
    if not ticket:
        return
    
    notifications = []
    
    if event_type == 'created':
        # Notify assigned technician
        notifications.append({
            'recipient': ticket['assigned_to'],
            'subject': f"New Ticket Assigned: {ticket['ticket_id']}",
            'template': 'ticket_assigned'
        })
        
        # Notify tenant of ticket creation
        notifications.append({
            'recipient': ticket['requested_for'],
            'subject': f"Service Request Received: {ticket['ticket_id']}",
            'template': 'ticket_created_tenant'
        })
    
    elif event_type == 'resolved':
        # Notify tenant of resolution
        notifications.append({
            'recipient': ticket['requested_for'],
            'subject': f"Service Request Completed: {ticket['ticket_id']}",
            'template': 'ticket_resolved_tenant'
        })