import imaplib
import email
import logging
from email.header import decode_header
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ...config import CONFIG

logger = logging.getLogger(__name__)

class GmailClient:
    def __init__(self, host: str = None, username: str = None, password: str = None):
        self.host = host or CONFIG.gmail_imap_host
        self.username = username or CONFIG.gmail_username
        self.password = password or CONFIG.gmail_password
        self.imap = None
    
    def connect(self) -> bool:
        """Connect to Gmail IMAP server"""
        try:
            self.imap = imaplib.IMAP4_SSL(self.host)
            self.imap.login(self.username, self.password)
            self.imap.select("INBOX")
            logger.info("Successfully connected to Gmail IMAP")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Gmail: {e}")
            return False
    
    def fetch_unread(self) -> List[Dict[str, Any]]:
        """Fetch unread emails"""
        if not self.imap:
            if not self.connect():
                return []
        
        try:
            # Search for unread messages
            status, messages = self.imap.search(None, 'UNSEEN')
            if status != "OK":
                return []
            
            email_ids = messages[0].split()
            new_emails = []
            
            for eid in email_ids:
                try:
                    status, msg_data = self.imap.fetch(eid, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extract email data
                    email_data = self._extract_email_data(msg)
                    new_emails.append(email_data)
                    
                    # Mark as seen
                    self.imap.store(eid, '+FLAGS', '\\Seen')
                    
                except Exception as e:
                    logger.error(f"Error processing email {eid}: {e}")
                    continue
            
            logger.info(f"Fetched {len(new_emails)} new emails")
            return new_emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def fetch_recent(self, count: Optional[int] = None, 
                    since_date: Optional[datetime] = None, 
                    days_back: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch recent emails with flexible options
        
        Args:
            count: Number of most recent emails to fetch (if specified, other params ignored)
            since_date: Fetch emails since this specific date
            days_back: Fetch emails from this many days back
            
        Returns:
            List of email dictionaries
        """
        if not self.imap:
            if not self.connect():
                return []
        
        try:
            # Option 1: Fetch specific number of recent emails
            if count is not None:
                return self._fetch_recent_by_count(count)
            
            # Option 2: Fetch emails within a time frame
            if since_date is not None:
                return self._fetch_recent_since_date(since_date)
            
            # Option 3: Fetch emails from days back
            if days_back is not None:
                cutoff_date = datetime.now() - timedelta(days=days_back)
                return self._fetch_recent_since_date(cutoff_date)
            
            # Default: fetch last 10 emails
            logger.info("No parameters specified, fetching last 10 emails")
            return self._fetch_recent_by_count(10)
            
        except Exception as e:
            logger.error(f"Error fetching recent emails: {e}")
            return []
    
    def _fetch_recent_by_count(self, count: int) -> List[Dict[str, Any]]:
        """Fetch the most recent N emails"""
        try:
            # Search for all messages
            status, messages = self.imap.search(None, 'ALL')
            if status != "OK":
                return []
            
            email_ids = messages[0].split()
            
            # Get the most recent email IDs (IMAP returns in ascending order)
            recent_ids = email_ids[-count:] if len(email_ids) >= count else email_ids
            recent_emails = []
            
            # Fetch emails in reverse order to get newest first
            for eid in reversed(recent_ids):
                try:
                    status, msg_data = self.imap.fetch(eid, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extract email data
                    email_data = self._extract_email_data(msg)
                    recent_emails.append(email_data)
                    
                except Exception as e:
                    logger.error(f"Error processing email {eid}: {e}")
                    continue
            
            logger.info(f"Fetched {len(recent_emails)} recent emails by count")
            return recent_emails
            
        except Exception as e:
            logger.error(f"Error fetching emails by count: {e}")
            return []
    
    def _fetch_recent_since_date(self, since_date: datetime) -> List[Dict[str, Any]]:
        """Fetch emails since a specific date"""
        try:
            # Format date for IMAP search (DD-MMM-YYYY format)
            search_date = since_date.strftime("%d-%b-%Y")
            
            # Search for messages since the specified date
            status, messages = self.imap.search(None, f'SINCE {search_date}')
            if status != "OK":
                return []
            
            email_ids = messages[0].split()
            recent_emails = []
            
            # Fetch emails in reverse order to get newest first
            for eid in reversed(email_ids):
                try:
                    status, msg_data = self.imap.fetch(eid, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extract email data
                    email_data = self._extract_email_data(msg)
                    recent_emails.append(email_data)
                    
                except Exception as e:
                    logger.error(f"Error processing email {eid}: {e}")
                    continue
            
            logger.info(f"Fetched {len(recent_emails)} emails since {search_date}")
            return recent_emails
            
        except Exception as e:
            logger.error(f"Error fetching emails by date: {e}")
            return []
    
    def _extract_email_data(self, msg) -> Dict[str, Any]:
        """Extract relevant data from email message"""
        # Get subject
        subject = ""
        if msg["Subject"]:
            subject_header = decode_header(msg["Subject"])[0]
            if isinstance(subject_header[0], bytes):
                subject = subject_header[0].decode(subject_header[1] or 'utf-8')
            else:
                subject = subject_header[0]
        
        # Get sender
        sender = msg.get("From", "")
        
        # Get date
        date_str = msg.get("Date", "")
        email_date = None
        if date_str:
            try:
                email_date = email.utils.parsedate_to_datetime(date_str)
            except Exception as e:
                logger.warning(f"Error parsing email date: {e}")
        
        # Get body
        body = self._extract_body(msg)
        
        return {
            "sender": sender,
            "subject": subject,
            "body": body,
            "date": email_date,
            "raw_message": msg
        }
    
    def _extract_body(self, msg) -> str:
        """Extract plain text body from email"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body_bytes = part.get_payload(decode=True)
                        if body_bytes:
                            body = body_bytes.decode(part.get_content_charset() or 'utf-8')
                            break
                    except Exception as e:
                        logger.warning(f"Error decoding email body: {e}")
        else:
            try:
                body_bytes = msg.get_payload(decode=True)
                if body_bytes:
                    body = body_bytes.decode(msg.get_content_charset() or 'utf-8')
            except Exception as e:
                logger.warning(f"Error decoding email body: {e}")
        
        return body.strip()
    
    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
                logger.info("Disconnected from Gmail IMAP")
            except Exception as e:
                logger.warning(f"Error disconnecting from Gmail: {e}")