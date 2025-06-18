import logging
from datetime import datetime
from tinydb import TinyDB, Query
from .gmail_client import GmailClient
from ...models import db, emails_table,replies_table, action_items_table
from .email_processor import EmailProcessor
from ..ai.ai_response import LangChainAIResponder, save_ai_responses_to_waiting_zone
from ..tickets.manager import Ticket, push_ticket
from ...llm_config import llm_config

logger = logging.getLogger(__name__)
email_processor = EmailProcessor()
# Initialize LangChain AI responder with modern configuration
config = llm_config
ai_responder = LangChainAIResponder(config)

def process_new_emails(auto_replay_strategy=None, auto_create_tickets=True):
    """Process new emails from Gmail inbox"""
    logger.info("Starting email check...")
    gmail_client = GmailClient()

    try:
        # Fetch new emails
        new_emails = gmail_client.fetch_unread()
        
        if not new_emails:
            logger.info("No new emails found")
            return
        
        for email_data in new_emails:
            try:
                # Process email and extract action items
                email_record = email_processor.process_email(email_data)
                
                if email_record:
                    # Insert email record into TinyDB
                    email_id = emails_table.insert({
                        'sender': email_data['sender'],
                        'subject': email_data['subject'],
                        'content': email_data.get('content', ''),
                        'received_at': datetime.now().isoformat(),
                        'processed_at': datetime.now().isoformat(),
                        **email_record  # Include any additional fields from email_processor
                    })
                    
                    # Generate AI reply
                    # reply_content, strategy_used = ai_responder.generate_reply(email_data)
                    response_options = ai_responder.generate_reply(email_data)
                    
                    # Save reply to TinyDB
                    ai_response_id = save_ai_responses_to_waiting_zone(email_id, response_options)
                    reply_id = ""
                    #   reply_id = replies_table.insert(
                    #    {
                    #     'email_id': email_id,
                    #     'content': reply_content,
                    #     'strategy_used': strategy_used,
                    #     'created_at': datetime.now().isoformat(),
                    # })
                    
                    logger.info(f"Processed email from {email_data['sender']} (Email ID: {email_id}, AI Response ID: {ai_response_id}),")
                    auto_pick = auto_replay_strategy
                    if auto_pick: 
                        for res in response_options:
                            if auto_pick == "strategy_used":
                                reply_id = replies_table.insert(res)
                                logger.info(f"Processed auto reply email from {email_data['sender']} (Email ID: {email_id}, Reply ID: {reply_id}),")                                
                                break
                                
                    # CREATE TICKETS FROM ACTION ITEMS (FIXED)
                    if auto_create_tickets and email_record.get('action_items_count', 0) > 0:
                        try:
                            created_tickets = _create_tickets_from_action_items(email_data, email_id, email_record)
                            
                            if created_tickets:
                                # Update email record with ticket info
                                emails_table.update(
                                    {
                                        'tickets_created': created_tickets,
                                        'tickets_created_at': datetime.now().isoformat()
                                    }, 
                                    doc_ids=[email_id]
                                )
                                logger.info(f"Created {len(created_tickets)} tickets: {', '.join(created_tickets)}")
                            
                            # Push tickets to monitor or management workflows
                            # TODO
                            
                            
                        except Exception as ticket_error:
                            logger.error(f"Error creating tickets for email {email_id}: {ticket_error}")
                    
                    # # Send notifications 
                    # notification_subject = f"New email from {email_data['sender']}"
                    # notification_message = f"Subject: {email_data['subject']}\nReply generated using {strategy_used} strategy"
                    # notifier_manager.notify_all(notification_subject, notification_message)
                    # TODO
                    
                    
            except Exception as e:
                logger.error(f"Error processing individual email: {e}")
                # Note: TinyDB doesn't have rollback, but individual operations are atomic
        
    except Exception as e:
        logger.error(f"Error in process_new_emails: {e}")

def get_email_by_id(email_id):
    """Helper function to retrieve an email by ID"""
    return emails_table.get(doc_id=email_id)

def get_replies_for_email(email_id):
    """Helper function to get all replies for a specific email"""
    Email = Query()
    return replies_table.search(Email.email_id == email_id)

def get_recent_emails(limit=10):
    """Helper function to get recent emails"""
    all_emails = emails_table.all()
    # Sort by received_at (most recent first)
    sorted_emails = sorted(all_emails, 
                          key=lambda x: x.get('received_at', ''), 
                          reverse=True)
    return sorted_emails[:limit]

def cleanup_old_records(days_old=30):
    """Helper function to clean up old records"""
    from datetime import datetime, timedelta
    
    cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
    Email = Query()
    
    # Remove old emails and their associated replies
    old_emails = emails_table.search(Email.received_at < cutoff_date)
    old_email_ids = [email.doc_id for email in old_emails]
    
    # Remove associated replies
    for email_id in old_email_ids:
        replies_table.remove(Email.email_id == email_id)
    
    # Remove old emails
    emails_table.remove(Email.received_at < cutoff_date)
    
    logger.info(f"Cleaned up {len(old_email_ids)} old email records")
    
def _create_tickets_from_action_items(email_data, email_id, email_record):
    """
    Create tickets from action items stored in database
    This function gets the action items that were already created by email_processor
    """
    created_tickets = []
    
    try:
        # Get the actual email record from database to find the correct email ID
        inserted_email = emails_table.get(doc_id=email_id)
        actual_email_id = inserted_email.get('id', str(email_id))
        
        # Get action items from database (these were created by email_processor.process_email())
        ActionItem = Query()
        action_items = action_items_table.search(ActionItem.email_id == actual_email_id)
        
        logger.info(f"Found {len(action_items)} action items for email {actual_email_id}")
        
        # Add email ID to email_data for ticket creation
        email_data_with_id = {**email_data, 'id': actual_email_id}
        
        for action_item in action_items:
            try:
                # Create ticket using the clean interface
                ticket = Ticket(email_data_with_id, action_item)
                ticket_id = push_ticket(ticket)
                
                if ticket_id:
                    created_tickets.append(ticket_id)
                    
                    # Update action item with ticket reference
                    action_items_table.update(
                        {
                            'ticket_id': ticket_id, 
                            'ticket_created_at': datetime.now().isoformat()
                        },
                        ActionItem.id == action_item['id']
                    )
                    
                    logger.info(f"Created ticket {ticket_id} from action item {action_item.get('id')}")
                
            except Exception as action_error:
                logger.error(f"Error creating ticket from action item {action_item.get('id')}: {action_error}")
                continue
    
    except Exception as e:
        logger.error(f"Error in _create_tickets_from_action_items: {e}")
    
    return created_tickets
