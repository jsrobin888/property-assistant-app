from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
from app.services.tinydb_wrapper_supabase import TinyDB, Query
import hashlib
import uuid

# Initialize TinyDB
db = TinyDB()

# Define tables
emails_table = db.table('emails')
replies_table = db.table('replies')
action_items_table = db.table('action_items')
tenants_table = db.table('tenants')
response_feedback_table = db.table('response_feedback')
context_patterns_table = db.table('context_patterns')
ai_responses_table = db.table('ai_responses')

# Enums
class EmailStatus(str, Enum):
    UNPROCESSED = "unprocessed"
    PROCESSING = "processing"
    PROCESSED = "processed"
    RESPONDED = "responded"

class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ActionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    IN_PROGRESS = "in_progress"

# Pydantic Models for API validation
class EmailResponse(BaseModel):
    id: str
    sender: str
    subject: str
    body: str
    received_at: datetime
    status: EmailStatus = EmailStatus.UNPROCESSED
    priority_level: PriorityLevel = PriorityLevel.MEDIUM
    context_labels: List[str] = []
    sentiment_score: Optional[float] = None
    urgency_score: Optional[float] = None

class EmailListResponse(BaseModel):
    emails: List[EmailResponse]
    total: int
    skip: int
    limit: int

class GeneratedResponse(BaseModel):
    strategy: str
    provider: str
    response: str
    confidence_score: float
    generation_time_ms: int

class ResponseGenerationRequest(BaseModel):
    strategies: Optional[List[str]] = ["enterprise_llm", "rag_small_llm"]

class EmailProcessingResponse(BaseModel):
    email_id: str
    responses: Dict[str, GeneratedResponse]
    context_labels: List[str]
    priority_level: str
    metadata: Dict[str, Any]

class ResponseSelectionRequest(BaseModel):
    strategy: str = Field(..., description="Selected strategy")
    response: str = Field(..., description="Selected response content")
    modifications: Optional[str] = Field(None, description="User modifications")
    feedback: Optional[Dict[str, Any]] = Field(None, description="User feedback")

class ResponseSelectionResponse(BaseModel):
    success: bool
    message_id: str
    sent_at: str
    message: str

# TinyDB Model Classes
class EmailMessage:
    """Email message model for TinyDB operations"""
    
    @staticmethod
    def create(sender: str, subject: str, body: str, **kwargs) -> int:
        """Create a new email message"""
        email_data = {
            'id': str(uuid.uuid4()),
            'sender': sender,
            'subject': subject,
            'body': body,
            'received_date': datetime.now().isoformat(),
            'processed_date': kwargs.get('processed_date'),
            'reply_sent_date': kwargs.get('reply_sent_date'),
            'strategy_used': kwargs.get('strategy_used'),
            'status': kwargs.get('status', EmailStatus.UNPROCESSED.value),
            'priority_level': kwargs.get('priority_level', PriorityLevel.MEDIUM.value),
            'context_labels': kwargs.get('context_labels', []),
            'sentiment_score': kwargs.get('sentiment_score'),
            'urgency_score': kwargs.get('urgency_score')
        }
        return emails_table.insert(email_data)
    
    @staticmethod
    def get_by_id(email_id: str) -> Optional[Dict]:
        """Get email by ID"""
        Email = Query()
        return emails_table.get(Email.id == email_id)
    
    @staticmethod
    def get_all(limit: int = 100, skip: int = 0) -> List[Dict]:
        """Get all emails with pagination"""
        all_emails = emails_table.all()
        return all_emails[skip:skip + limit]
    
    @staticmethod
    def update_status(email_id: str, status: EmailStatus) -> bool:
        """Update email status"""
        Email = Query()
        return emails_table.update({'status': status.value}, Email.id == email_id)
    
    @staticmethod
    def get_unprocessed() -> List[Dict]:
        """Get all unprocessed emails"""
        Email = Query()
        return emails_table.search(Email.status == EmailStatus.UNPROCESSED.value)

class Reply:
    """Reply model for TinyDB operations"""
    
    @staticmethod
    def create(email_id: str, content: str, strategy_used: str, **kwargs) -> int:
        """Create a new reply"""
        reply_data = {
            'id': str(uuid.uuid4()),
            'email_id': email_id,
            'content': content,
            'created_date': datetime.now().isoformat(),
            'sent': kwargs.get('sent', False),
            'strategy_used': strategy_used
        }
        return replies_table.insert(reply_data)
    
    @staticmethod
    def get_by_email_id(email_id: str) -> List[Dict]:
        """Get all replies for an email"""
        Reply = Query()
        return replies_table.search(Reply.email_id == email_id)
    
    @staticmethod
    def mark_as_sent(reply_id: str) -> bool:
        """Mark reply as sent"""
        Reply = Query()
        return replies_table.update({'sent': True}, Reply.id == reply_id)

class ActionItem:
    """Action item model for TinyDB operations"""
    
    @staticmethod
    def create(email_id: str, action_data: Dict, **kwargs) -> int:
        """Create a new action item"""
        action_item_data = {
            'id': str(uuid.uuid4()),
            'email_id': email_id,
            'action_data': action_data,
            'status': kwargs.get('status', ActionStatus.OPEN.value),
            'created_date': datetime.now().isoformat(),
            'updated_date': datetime.now().isoformat()
        }
        return action_items_table.insert(action_item_data)
    
    @staticmethod
    def get_by_email_id(email_id: str) -> List[Dict]:
        """Get all action items for an email"""
        ActionItem = Query()
        return action_items_table.search(ActionItem.email_id == email_id)
    
    @staticmethod
    def update_status(action_id: str, status: ActionStatus) -> bool:
        """Update action item status"""
        ActionItem = Query()
        return action_items_table.update({
            'status': status.value,
            'updated_date': datetime.now().isoformat()
        }, ActionItem.id == action_id)
    
    @staticmethod
    def get_open_items() -> List[Dict]:
        """Get all open action items"""
        ActionItem = Query()
        return action_items_table.search(ActionItem.status == ActionStatus.OPEN.value)

class Tenant:
    """Tenant model for TinyDB operations"""
    
    @staticmethod
    def create(name: str, email: str, **kwargs) -> int:
        """Create a new tenant"""
        tenant_data = {
            'id': str(uuid.uuid4()),
            'name': name,
            'email': email,
            'unit': kwargs.get('unit'),
            'phone': kwargs.get('phone'),
            'lease_start': kwargs.get('lease_start').isoformat() if kwargs.get('lease_start') else None,
            'lease_end': kwargs.get('lease_end').isoformat() if kwargs.get('lease_end') else None,
            'rent_amount': kwargs.get('rent_amount'),
            'created_date': datetime.now().isoformat()
        }
        return tenants_table.insert(tenant_data)
    
    @staticmethod
    def get_by_email(email: str) -> Optional[Dict]:
        """Get tenant by email"""
        Tenant = Query()
        return tenants_table.get(Tenant.email == email)
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Get all tenants"""
        return tenants_table.all()

class ResponseFeedback:
    """Response feedback model for TinyDB operations"""
    
    @staticmethod
    def create(email_content: str, context_labels: List[str], gpt_response: str, 
               rag_response: str, selected_strategy: str, **kwargs) -> int:
        """Create new response feedback"""
        email_hash = hashlib.sha256(email_content.encode()).hexdigest()
        feedback_data = {
            'id': str(uuid.uuid4()),
            'email_hash': email_hash,
            'context_labels': context_labels,
            'gpt_response': gpt_response,
            'rag_response': rag_response,
            'selected_strategy': selected_strategy,
            'user_rating': kwargs.get('user_rating'),
            'improvement_notes': kwargs.get('improvement_notes'),
            'created_date': datetime.now().isoformat()
        }
        return response_feedback_table.insert(feedback_data)
    
    @staticmethod
    def get_by_strategy(strategy: str) -> List[Dict]:
        """Get feedback by strategy"""
        Feedback = Query()
        return response_feedback_table.search(Feedback.selected_strategy == strategy)
    
    @staticmethod
    def get_recent_feedback(limit: int = 50) -> List[Dict]:
        """Get recent feedback"""
        all_feedback = response_feedback_table.all()
        sorted_feedback = sorted(all_feedback, 
                               key=lambda x: x.get('created_date', ''), 
                               reverse=True)
        return sorted_feedback[:limit]

class ContextPattern:
    """Context pattern model for TinyDB operations"""
    
    @staticmethod
    def create(context_label: str, pattern_keywords: List[str], 
               preferred_strategy: str, **kwargs) -> int:
        """Create new context pattern"""
        pattern_data = {
            'id': str(uuid.uuid4()),
            'context_label': context_label,
            'pattern_keywords': pattern_keywords,
            'preferred_strategy': preferred_strategy,
            'success_rate': kwargs.get('success_rate', 0.0),
            'response_template': kwargs.get('response_template'),
            'last_updated': datetime.now().isoformat()
        }
        return context_patterns_table.insert(pattern_data)
    
    @staticmethod
    def get_by_context(context_label: str) -> Optional[Dict]:
        """Get pattern by context label"""
        Pattern = Query()
        return context_patterns_table.get(Pattern.context_label == context_label)
    
    @staticmethod
    def update_success_rate(context_label: str, success_rate: float) -> bool:
        """Update success rate for a context pattern"""
        Pattern = Query()
        return context_patterns_table.update({
            'success_rate': success_rate,
            'last_updated': datetime.now().isoformat()
        }, Pattern.context_label == context_label)
    
    @staticmethod
    def get_all_patterns() -> List[Dict]:
        """Get all context patterns"""
        return context_patterns_table.all()

# Utility functions
def cleanup_old_records(days_old: int = 30):
    """Clean up old records from all tables"""
    from datetime import timedelta
    
    cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
    
    # Clean up old emails and related data
    Email = Query()
    old_emails = emails_table.search(Email.received_date < cutoff_date)
    old_email_ids = [email['id'] for email in old_emails]
    
    # Remove associated replies and action items
    Reply = Query()
    ActionItem = Query()
    
    for email_id in old_email_ids:
        replies_table.remove(Reply.email_id == email_id)
        action_items_table.remove(ActionItem.email_id == email_id)
    
    # Remove old emails
    emails_table.remove(Email.received_date < cutoff_date)
    
    # Clean up old feedback
    Feedback = Query()
    response_feedback_table.remove(Feedback.created_date < cutoff_date)
    
    return len(old_email_ids)

def get_database_stats() -> Dict[str, int]:
    """Get database statistics"""
    return {
        'emails': len(emails_table),
        'replies': len(replies_table),
        'action_items': len(action_items_table),
        'tenants': len(tenants_table),
        'response_feedback': len(response_feedback_table),
        'context_patterns': len(context_patterns_table)
    }