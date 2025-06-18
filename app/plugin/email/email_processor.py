import json
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from ...models import EmailMessage, ActionItem, Tenant, EmailStatus, PriorityLevel, ActionStatus

logger = logging.getLogger(__name__)

class EmailProcessor:
    def __init__(self):
        self.action_keywords = {
            'maintenance': [
                'broken', 'fix', 'repair', 'maintenance', 'not working',
                'leak', 'toilet', 'faucet', 'heater', 'air conditioning',
                'plumbing', 'electrical', 'hvac', 'appliance', 'damage'
            ],
            'lockout': [
                'locked out', 'can\'t get in', 'lost key', 'keys', 'access',
                'door', 'entrance', 'lock', 'keycard', 'entry'
            ],
            'complaint': [
                'noise', 'complain', 'neighbor', 'disturbance', 'problem',
                'loud', 'party', 'music', 'shouting', 'annoying'
            ],
            'payment': [
                'rent', 'payment', 'late fee', 'balance', 'deposit',
                'charge', 'invoice', 'bill', 'overdue', 'money'
            ],
            'lease': [
                'lease', 'contract', 'renewal', 'move out', 'termination',
                'end of lease', 'moving', 'vacate', 'extend'
            ],
            'amenity': [
                'pool', 'gym', 'laundry', 'parking', 'amenity',
                'facility', 'clubhouse', 'mailroom', 'elevator'
            ]
        }
        
        self.urgent_keywords = [
            'emergency', 'urgent', 'immediate', 'flooding', 'gas leak',
            'fire', 'smoke', 'water damage', 'electrical hazard', 'help'
        ]
        
        self.high_priority_keywords = [
            'no heat', 'no hot water', 'toilet overflow', 'ceiling leak',
            'broken window', 'door won\'t lock', 'refrigerator broken'
        ]
    
    def process_email(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming email and extract action items"""
        try:
            # Determine priority and status
            priority_level = self._determine_priority_level(email_data)
            context_labels = self._extract_context_labels(email_data)
            
            # Create email record
            email_id = EmailMessage.create(
                sender=email_data['sender'],
                subject=email_data.get('subject', ''),
                body=email_data.get('body', ''),
                status=EmailStatus.PROCESSING,
                priority_level=priority_level,
                context_labels=context_labels,
                processed_date=datetime.now().isoformat()
            )
            
            # Get the created email record
            created_email = EmailMessage.get_by_id(email_id)
            if not created_email:
                logger.error(f"Failed to retrieve created email with ID: {email_id}")
                return None
            
            # Extract and save action items
            action_items = self._extract_action_items(email_data, created_email['id'])
            
            # Save action items to database
            for action_data in action_items:
                ActionItem.create(
                    email_id=created_email['id'],
                    action_data=action_data,
                    status=ActionStatus.OPEN
                )
            
            # Update email status to processed
            EmailMessage.update_status(created_email['id'], EmailStatus.PROCESSED)
            
            logger.info(f"Processed email from {email_data['sender']} with {len(action_items)} action items")
            
            return {
                'email_id': created_email['id'],
                'action_items_count': len(action_items),
                'priority_level': priority_level.value,
                'context_labels': context_labels,
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return None
    
    def _extract_action_items(self, email_data: Dict[str, Any], email_id: str) -> List[Dict[str, Any]]:
        """Extract action items from email content"""
        action_items = []
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        content = f"{subject} {body}"
        sender = email_data.get('sender', '')
        
        # Get tenant info
        tenant_info = self._get_or_create_tenant_info(sender)
        unit_info = self._extract_unit_info(content)
        priority = self._determine_priority(content)
        
        # Check for maintenance requests
        if self._contains_keywords(content, self.action_keywords['maintenance']):
            action_items.append({
                "action": "create_maintenance_ticket",
                "category": "maintenance",
                "details": self._extract_maintenance_details(email_data),
                "priority": priority,
                "tenant": tenant_info,
                "unit": unit_info,
                "keywords_found": self._get_matching_keywords(content, self.action_keywords['maintenance']),
                "estimated_cost": self._estimate_maintenance_cost(content),
                "requires_contractor": self._requires_contractor(content)
            })
        
        # Check for lockout situations
        if self._contains_keywords(content, self.action_keywords['lockout']):
            action_items.append({
                "action": "emergency_lockout_assistance",
                "category": "lockout",
                "details": "Tenant locked out of apartment, needs immediate assistance",
                "priority": "urgent",
                "tenant": tenant_info,
                "unit": unit_info,
                "response_time_required": "immediate",
                "after_hours": self._is_after_hours()
            })
        
        # Check for complaints
        if self._contains_keywords(content, self.action_keywords['complaint']):
            action_items.append({
                "action": "investigate_complaint",
                "category": "complaint",
                "details": self._extract_complaint_details(email_data),
                "priority": self._determine_complaint_priority(content),
                "tenant": tenant_info,
                "unit": unit_info,
                "complaint_type": self._classify_complaint(content),
                "requires_mediation": self._requires_mediation(content)
            })
        
        # Check for payment inquiries
        if self._contains_keywords(content, self.action_keywords['payment']):
            action_items.append({
                "action": "review_tenant_account",
                "category": "payment",
                "details": "Tenant inquiry about payment/rent/account balance",
                "priority": "medium",
                "tenant": tenant_info,
                "unit": unit_info,
                "payment_type": self._identify_payment_type(content),
                "amount_mentioned": self._extract_amount(content)
            })
        
        # Check for lease inquiries
        if self._contains_keywords(content, self.action_keywords['lease']):
            action_items.append({
                "action": "lease_inquiry",
                "category": "lease",
                "details": self._extract_lease_details(email_data),
                "priority": "medium",
                "tenant": tenant_info,
                "unit": unit_info,
                "lease_action": self._identify_lease_action(content)
            })
        
        # Check for amenity issues
        if self._contains_keywords(content, self.action_keywords['amenity']):
            action_items.append({
                "action": "amenity_issue",
                "category": "amenity",
                "details": self._extract_amenity_details(email_data),
                "priority": "low",
                "tenant": tenant_info,
                "unit": unit_info,
                "amenity_type": self._identify_amenity(content)
            })
        
        return action_items
    
    def _determine_priority_level(self, email_data: Dict[str, Any]) -> PriorityLevel:
        """Determine priority level for the email"""
        content = f"{email_data.get('subject', '')} {email_data.get('body', '')}".lower()
        
        if any(keyword in content for keyword in self.urgent_keywords):
            return PriorityLevel.URGENT
        elif any(keyword in content for keyword in self.high_priority_keywords):
            return PriorityLevel.HIGH
        elif self._contains_keywords(content, self.action_keywords['lockout']):
            return PriorityLevel.URGENT
        elif self._contains_keywords(content, self.action_keywords['maintenance']):
            return PriorityLevel.HIGH
        else:
            return PriorityLevel.MEDIUM
    
    def _extract_context_labels(self, email_data: Dict[str, Any]) -> List[str]:
        """Extract context labels from email"""
        labels = []
        content = f"{email_data.get('subject', '')} {email_data.get('body', '')}".lower()
        
        for category, keywords in self.action_keywords.items():
            if self._contains_keywords(content, keywords):
                labels.append(category)
        
        return labels
    
    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords"""
        return any(keyword in text for keyword in keywords)
    
    def _get_matching_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Get list of matching keywords"""
        return [keyword for keyword in keywords if keyword in text]
    
    def _determine_priority(self, content: str) -> str:
        """Determine priority based on content"""
        if any(keyword in content for keyword in self.urgent_keywords):
            return "urgent"
        elif any(keyword in content for keyword in self.high_priority_keywords):
            return "high"
        return "medium"
    
    def _get_or_create_tenant_info(self, sender: str) -> Dict[str, Any]:
        """Get tenant info from database or create basic info"""
        # Try to find existing tenant
        tenant = Tenant.get_by_email(sender)
        
        if tenant:
            return {
                'id': tenant['id'],
                'name': tenant['name'],
                'email': tenant['email'],
                'unit': tenant.get('unit', 'Unknown'),
                'phone': tenant.get('phone', 'Not provided')
            }
        else:
            # Create basic tenant info
            tenant_name = self._extract_tenant_name(sender)
            return {
                'id': None,
                'name': tenant_name,
                'email': sender,
                'unit': 'Unknown',
                'phone': 'Not provided',
                'new_tenant': True
            }
    
    def _extract_tenant_name(self, sender: str) -> str:
        """Extract tenant name from sender email"""
        if '<' in sender:
            name_part = sender.split('<')[0].strip()
            return name_part if name_part else sender
        return sender.split('@')[0].replace('.', ' ').title()
    
    def _extract_unit_info(self, content: str) -> str:
        """Extract unit information from email content"""
        patterns = [
            r'apt\s*(\w+)',
            r'apartment\s*(\w+)',
            r'unit\s*(\w+)',
            r'#(\w+)',
            r'room\s*(\w+)',
            r'suite\s*(\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return f"Unit {match.group(1).upper()}"
        
        return "Unit not specified"
    
    def _extract_maintenance_details(self, email_data: Dict[str, Any]) -> str:
        """Extract specific maintenance details"""
        body = email_data.get('body', '')
        subject = email_data.get('subject', '')
        
        if body:
            sentences = body.split('.')
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in self.action_keywords['maintenance']):
                    return sentence.strip()
        
        return f"Maintenance request: {subject}"
    
    def _extract_complaint_details(self, email_data: Dict[str, Any]) -> str:
        """Extract complaint details"""
        body = email_data.get('body', '')
        subject = email_data.get('subject', '')
        
        if body and len(body) > 50:
            return body[:200] + "..." if len(body) > 200 else body
        
        return f"Tenant complaint: {subject}"
    
    def _extract_lease_details(self, email_data: Dict[str, Any]) -> str:
        """Extract lease-related details"""
        body = email_data.get('body', '')
        subject = email_data.get('subject', '')
        
        if body and len(body) > 30:
            return body[:150] + "..." if len(body) > 150 else body
        
        return f"Lease inquiry: {subject}"
    
    def _extract_amenity_details(self, email_data: Dict[str, Any]) -> str:
        """Extract amenity-related details"""
        body = email_data.get('body', '')
        subject = email_data.get('subject', '')
        
        return f"Amenity issue: {subject} - {body[:100]}..." if len(body) > 100 else f"Amenity issue: {subject} - {body}"
    
    def _estimate_maintenance_cost(self, content: str) -> str:
        """Estimate maintenance cost category"""
        high_cost_keywords = ['replace', 'new', 'install', 'major repair']
        if any(keyword in content for keyword in high_cost_keywords):
            return "high"
        return "low"
    
    def _requires_contractor(self, content: str) -> bool:
        """Check if maintenance requires external contractor"""
        contractor_keywords = ['electrical', 'plumbing', 'hvac', 'appliance', 'major']
        return any(keyword in content for keyword in contractor_keywords)
    
    def _is_after_hours(self) -> bool:
        """Check if current time is after business hours"""
        current_hour = datetime.now().hour
        return current_hour < 8 or current_hour > 18
    
    def _determine_complaint_priority(self, content: str) -> str:
        """Determine complaint priority"""
        high_priority_complaints = ['noise', 'harassment', 'safety', 'health']
        if any(keyword in content for keyword in high_priority_complaints):
            return "high"
        return "medium"
    
    def _classify_complaint(self, content: str) -> str:
        """Classify type of complaint"""
        if 'noise' in content:
            return "noise"
        elif 'neighbor' in content:
            return "neighbor_dispute"
        elif 'parking' in content:
            return "parking"
        else:
            return "general"
    
    def _requires_mediation(self, content: str) -> bool:
        """Check if complaint requires mediation"""
        mediation_keywords = ['neighbor', 'dispute', 'harassment', 'conflict']
        return any(keyword in content for keyword in mediation_keywords)
    
    def _identify_payment_type(self, content: str) -> str:
        """Identify type of payment inquiry"""
        if 'late fee' in content:
            return "late_fee"
        elif 'deposit' in content:
            return "security_deposit"
        elif 'rent' in content:
            return "rent"
        else:
            return "general_payment"
    
    def _extract_amount(self, content: str) -> Optional[str]:
        """Extract monetary amount from content"""
        import re
        amount_pattern = r'\$[\d,]+\.?\d*'
        match = re.search(amount_pattern, content)
        return match.group() if match else None
    
    def _identify_lease_action(self, content: str) -> str:
        """Identify what lease action is being requested"""
        if 'renewal' in content or 'renew' in content:
            return "renewal"
        elif 'move out' in content or 'termination' in content:
            return "termination"
        elif 'extend' in content:
            return "extension"
        else:
            return "inquiry"
    
    def _identify_amenity(self, content: str) -> str:
        """Identify which amenity is being referenced"""
        amenities = ['pool', 'gym', 'laundry', 'parking', 'elevator', 'mailroom']
        for amenity in amenities:
            if amenity in content:
                return amenity
        return "general"