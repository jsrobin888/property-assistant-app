"""
Ticket schema validation and transformation
Handles ticket data validation and mapping from email content
"""

from typing import Dict, Any, Optional, Tuple
from .models import TicketCategory, TicketSubcategory, TicketUrgency, TicketRequestType
import re

class TicketSchemaValidator:
    """Validates and transforms data according to ticket schema"""
    
    REQUIRED_FIELDS = [
        'short_description', 'description', 'category', 'subcategory',
        'request_type', 'urgency', 'priority', 'property_id', 
        'unit_number', 'requested_for', 'assignment_group', 
        'assigned_to', 'status'
    ]
    
    @classmethod
    def validate_ticket_data(cls, ticket_data: Dict[str, Any]) -> Tuple[bool, list]:
        """Validate ticket data against schema requirements"""
        missing_fields = []
        
        for field in cls.REQUIRED_FIELDS:
            if field not in ticket_data or ticket_data[field] is None:
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields
    
    @classmethod
    def create_ticket_schema(cls, 
                           short_description: str,
                           description: str,
                           category: str,
                           subcategory: str,
                           request_type: str,
                           urgency: str,
                           property_id: str,
                           unit_number: str,
                           requested_for: str,
                           assignment_group: str,
                           assigned_to: str,
                           **kwargs) -> Dict[str, Any]:
        """Create a complete ticket schema dict"""
        
        ticket_schema = {
            "short_description": short_description,
            "description": description,
            "category": category,
            "subcategory": subcategory,
            "request_type": request_type,
            "urgency": urgency,
            "priority": urgency,  # Auto-calculated from urgency
            "property_id": property_id,
            "unit_number": unit_number,
            "requested_for": requested_for,
            "assignment_group": assignment_group,
            "assigned_to": assigned_to,
            "status": "New"
        }
        
        # Add optional fields
        for key, value in kwargs.items():
            if key not in cls.REQUIRED_FIELDS:
                ticket_schema[key] = value
        
        return ticket_schema

class CategoryMapper:
    """Maps email content to appropriate ticket categories"""
    
    CATEGORY_KEYWORDS = {
        'maintenance': {
            'keywords': [
                'broken', 'fix', 'repair', 'maintenance', 'not working',
                'leak', 'toilet', 'faucet', 'heater', 'air conditioning',
                'plumbing', 'electrical', 'hvac', 'appliance', 'damage'
            ],
            'category': TicketCategory.MAINTENANCE.value,
            'request_type': TicketRequestType.REPAIR.value
        },
        'lockout': {
            'keywords': [
                'locked out', 'can\'t get in', 'lost key', 'keys', 'access',
                'door', 'entrance', 'lock', 'keycard', 'entry'
            ],
            'category': TicketCategory.MAINTENANCE.value,
            'request_type': TicketRequestType.EMERGENCY.value
        },
        'complaint': {
            'keywords': [
                'noise', 'complain', 'neighbor', 'disturbance', 'problem',
                'loud', 'party', 'music', 'shouting', 'annoying'
            ],
            'category': TicketCategory.COMPLAINT.value,
            'request_type': TicketRequestType.GENERAL.value
        },
        'payment': {
            'keywords': [
                'rent', 'payment', 'late fee', 'balance', 'deposit',
                'charge', 'invoice', 'bill', 'overdue', 'money'
            ],
            'category': TicketCategory.PAYMENT.value,
            'request_type': TicketRequestType.GENERAL.value
        },
        'lease': {
            'keywords': [
                'lease', 'contract', 'renewal', 'move out', 'termination',
                'end of lease', 'moving', 'vacate', 'extend'
            ],
            'category': TicketCategory.LEASE.value,
            'request_type': TicketRequestType.GENERAL.value
        },
        'amenity': {
            'keywords': [
                'pool', 'gym', 'laundry', 'parking', 'amenity',
                'facility', 'clubhouse', 'mailroom', 'elevator'
            ],
            'category': TicketCategory.AMENITY.value,
            'request_type': TicketRequestType.REPAIR.value
        }
    }
    
    URGENCY_KEYWORDS = {
        TicketUrgency.HIGH.value: [
            'emergency', 'urgent', 'immediate', 'flooding', 'gas leak',
            'fire', 'smoke', 'water damage', 'electrical hazard', 'help',
            'no heat', 'no hot water', 'toilet overflow', 'ceiling leak'
        ],
        TicketUrgency.MEDIUM.value: [
            'broken', 'not working', 'repair', 'fix', 'issue', 'problem'
        ]
    }
    
    @classmethod
    def determine_category_from_content(cls, content: str) -> Tuple[str, str]:
        """Determine category and request type from email content"""
        content_lower = content.lower()
        
        for category_type, info in cls.CATEGORY_KEYWORDS.items():
            if any(keyword in content_lower for keyword in info['keywords']):
                return info['category'], info['request_type']
        
        # Default fallback
        return TicketCategory.MAINTENANCE.value, TicketRequestType.GENERAL.value
    
    @classmethod
    def determine_subcategory(cls, content: str, category: str) -> str:
        """Determine specific subcategory based on content and category"""
        content_lower = content.lower()
        
        if category == TicketCategory.MAINTENANCE.value:
            if any(keyword in content_lower for keyword in ['toilet', 'sink', 'faucet', 'pipe', 'leak', 'water']):
                return TicketSubcategory.PLUMBING.value
            elif any(keyword in content_lower for keyword in ['electrical', 'outlet', 'switch', 'power', 'light']):
                return TicketSubcategory.ELECTRICAL.value
            elif any(keyword in content_lower for keyword in ['hvac', 'heating', 'cooling', 'air conditioning', 'furnace']):
                return TicketSubcategory.HVAC.value
            elif any(keyword in content_lower for keyword in ['refrigerator', 'stove', 'oven', 'dishwasher', 'appliance']):
                return TicketSubcategory.APPLIANCE.value
            elif any(keyword in content_lower for keyword in ['clean', 'dirty', 'trash', 'pest']):
                return TicketSubcategory.CLEANING.value
            else:
                return TicketSubcategory.GENERAL_REPAIR.value
        
        elif category == TicketCategory.COMPLAINT.value:
            if any(keyword in content_lower for keyword in ['noise', 'loud', 'music', 'party']):
                return TicketSubcategory.NOISE_COMPLAINT.value
            elif any(keyword in content_lower for keyword in ['neighbor', 'dispute', 'conflict']):
                return TicketSubcategory.NEIGHBOR_DISPUTE.value
            else:
                return TicketSubcategory.OTHER.value
        
        elif category == TicketCategory.PAYMENT.value:
            if any(keyword in content_lower for keyword in ['late fee', 'penalty']):
                return TicketSubcategory.LATE_FEES.value
            else:
                return TicketSubcategory.RENT_PAYMENT.value
        
        elif category == TicketCategory.AMENITY.value:
            if 'pool' in content_lower:
                return TicketSubcategory.POOL.value
            elif 'gym' in content_lower:
                return TicketSubcategory.GYM.value
            elif 'parking' in content_lower:
                return TicketSubcategory.PARKING.value
            else:
                return TicketSubcategory.OTHER.value
        
        return TicketSubcategory.OTHER.value
    
    @classmethod
    def determine_urgency(cls, content: str) -> str:
        """Determine urgency level from content"""
        content_lower = content.lower()
        
        for urgency, keywords in cls.URGENCY_KEYWORDS.items():
            if any(keyword in content_lower for keyword in keywords):
                return urgency
        
        return TicketUrgency.LOW.value

class PropertyInfoExtractor:
    """Extracts property and unit information from email content"""
    
    UNIT_PATTERNS = [
        r'apt\s*(\w+)',
        r'apartment\s*(\w+)',
        r'unit\s*(\w+)',
        r'#(\w+)',
        r'room\s*(\w+)',
        r'suite\s*(\w+)'
    ]
    
    @classmethod
    def extract_unit_info(cls, content: str) -> str:
        """Extract unit information from email content"""
        for pattern in cls.UNIT_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return f"Unit {match.group(1).upper()}"
        
        return "Unit not specified"
    
    @classmethod
    def generate_property_id(cls, unit_info: str) -> str:
        """Generate property ID from unit information"""
        if 'Unit' in unit_info:
            # Extract unit number and create property ID
            unit_num = unit_info.replace('Unit ', '').strip()
            if unit_num and unit_num != 'not specified':
                # Take first 3 characters for property ID
                property_id = f"P{unit_num[:3].zfill(3)}"
                return property_id
        
        return "P000"  # Default property ID

class AssignmentMapper:
    """Maps ticket categories to appropriate assignment groups and assignees"""
    
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
        },
        TicketCategory.AMENITY.value: {
            'assignment_group': 'Property Maintenance',
            'assigned_to': 'maintenance@property.com'
        }
    }
    
    SPECIALIST_ASSIGNMENTS = {
        TicketSubcategory.PLUMBING.value: 'plumber@property.com',
        TicketSubcategory.ELECTRICAL.value: 'electrician@property.com',
        TicketSubcategory.HVAC.value: 'hvac@property.com'
    }
    
    @classmethod
    def get_assignment(cls, category: str, subcategory: str = None) -> Tuple[str, str]:
        """Get assignment group and assignee for a category/subcategory"""
        # Get base assignment
        base_assignment = cls.ASSIGNMENT_MAPPING.get(
            category, 
            {'assignment_group': 'General Support', 'assigned_to': 'support@property.com'}
        )
        
        assignment_group = base_assignment['assignment_group']
        assigned_to = base_assignment['assigned_to']
        
        # Override with specialist if available
        if subcategory and subcategory in cls.SPECIALIST_ASSIGNMENTS:
            assigned_to = cls.SPECIALIST_ASSIGNMENTS[subcategory]
        
        return assignment_group, assigned_to