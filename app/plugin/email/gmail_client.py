import imaplib
import email
import logging
from email.header import decode_header
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ...config import CONFIG

logger = logging.getLogger(__name__)

class GmailClient:
    def __init__(self):
        self.host = CONFIG.gmail_imap_host
        self.username = CONFIG.gmail_username
        self.password = CONFIG.gmail_password
        self.port = 993
        self.imap = None
        
        # Validate configuration on initialization
        self._validate_config()
    
    def update_credential(self, host: str = None, username: str = None, password: str = None, port: int = 993):
        self.host = host if host else CONFIG.gmail_imap_host
        self.username = username if username else CONFIG.gmail_username
        self.password = password if password else CONFIG.gmail_password
        self.port = port if port else 993
    
    def _validate_config(self) -> None:
        """Validate Gmail configuration and provide helpful error messages"""
        issues = []
        
        if not self.host:
            issues.append("GMAIL_IMAP_HOST is not set")
        
        if not self.username:
            issues.append("GMAIL_USERNAME is not set")
        elif not "@" in self.username:
            issues.append("GMAIL_USERNAME should be a full email address (e.g., your.email@gmail.com)")
        
        if not self.password:
            issues.append("GMAIL_PASSWORD is not set")
        elif len(self.password) < 16:
            issues.append("GMAIL_PASSWORD appears to be too short - you likely need an App Password (16 characters)")
        
        if issues:
            logger.error("Gmail configuration issues found:")
            for issue in issues:
                logger.error(f"  - {issue}")
            
            logger.error("\n" + "="*60)
            logger.error("GMAIL SETUP INSTRUCTIONS:")
            logger.error("="*60)
            logger.error("1. Enable 2-Factor Authentication on your Gmail account")
            logger.error("2. Generate an App Password:")
            logger.error("   - Go to https://myaccount.google.com/apppasswords")
            logger.error("   - Select 'Mail' and your device")
            logger.error("   - Copy the 16-character password")
            logger.error("3. Set environment variables:")
            logger.error("   GMAIL_USERNAME=your.email@gmail.com")
            logger.error("   GMAIL_PASSWORD=your-16-char-app-password")
            logger.error("   GMAIL_IMAP_HOST=imap.gmail.com")
            logger.error("4. Enable IMAP in Gmail settings:")
            logger.error("   - Go to Gmail Settings > Forwarding and POP/IMAP")
            logger.error("   - Enable IMAP access")
            logger.error("="*60)
    
    def connect(self) -> bool:
        """Connect to Gmail IMAP server with enhanced error handling"""
        # Re-validate before connecting
        if not self.username or not self.password:
            logger.error("Cannot connect: Missing username or password")
            return False
        
        try:
            logger.info(f"Attempting to connect to {self.host} as {self.username}")
            
            # Step 1: Establish SSL connection
            try:
                self.imap = imaplib.IMAP4_SSL(self.host, self.port)
                logger.info("SSL connection established")
            except Exception as e:
                logger.error(f"Failed to establish SSL connection to {self.host}: {e}")
                return False
            
            # Step 2: Authenticate
            try:
                # Debug: Show masked credentials (first 3 and last 3 characters)
                masked_password = f"{self.password[:3]}{'*' * (len(self.password) - 6)}{self.password[-3:]}" if len(self.password) > 6 else "***"
                logger.info(f"Authenticating with username: {self.username}")
                logger.info(f"Password length: {len(self.password)} characters (masked: {masked_password})")
                
                # Perform login
                result = self.imap.login(self.username, self.password)
                logger.info(f"Login result: {result}")
                
            except imaplib.IMAP4.error as e:
                self._handle_imap_error(e)
                return False
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                self._suggest_fixes_for_auth_error(str(e))
                return False
            
            # Step 3: Select INBOX
            try:
                result = self.imap.select("INBOX")
                logger.info(f"INBOX selection result: {result}")
                
                if result[0] != 'OK':
                    logger.error(f"Failed to select INBOX: {result}")
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to select INBOX: {e}")
                return False
            
            logger.info("Successfully connected to Gmail IMAP")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error during Gmail connection: {e}")
            return False
    
    def _handle_imap_error(self, error: imaplib.IMAP4.error) -> None:
        """Handle specific IMAP errors with helpful messages"""
        error_str = str(error).lower()
        
        if "not enough arguments" in error_str:
            logger.error("LOGIN ERROR: Not enough arguments provided")
            logger.error("This usually means username or password is empty")
            logger.error(f"Username provided: {'YES' if self.username else 'NO'}")
            logger.error(f"Password provided: {'YES' if self.password else 'NO'}")
            
        elif "authentication failed" in error_str or "invalid credentials" in error_str:
            logger.error("AUTHENTICATION ERROR: Invalid credentials")
            self._suggest_fixes_for_auth_error(error_str)
            
        elif "too many login attempts" in error_str:
            logger.error("RATE LIMIT ERROR: Too many login attempts")
            logger.error("Wait 15 minutes before trying again")
            
        elif "imap access is disabled" in error_str:
            logger.error("IMAP DISABLED ERROR: IMAP access is not enabled")
            logger.error("Enable IMAP in Gmail Settings > Forwarding and POP/IMAP")
            
        else:
            logger.error(f"IMAP ERROR: {error}")
    
    def _suggest_fixes_for_auth_error(self, error_str: str) -> None:
        """Suggest fixes for authentication errors"""
        logger.error("\nPOSSIBLE FIXES:")
        logger.error("1. Make sure you're using an App Password, not your regular Gmail password")
        logger.error("2. Check that 2-Factor Authentication is enabled on your account")
        logger.error("3. Verify your username is the full email address")
        logger.error("4. Try generating a new App Password")
        logger.error("5. Check if IMAP is enabled in Gmail settings")
        
        if "invalid credentials" in error_str:
            logger.error("6. Double-check that you copied the App Password correctly")
            logger.error("7. Make sure there are no extra spaces in your credentials")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection and return detailed status"""
        test_result = {
            "success": False,
            "host": self.host,
            "username": self.username,
            "password_length": len(self.password) if self.password else 0,
            "errors": [],
            "suggestions": []
        }
        
        # Test 1: Configuration validation
        if not self.username:
            test_result["errors"].append("Username not provided")
            test_result["suggestions"].append("Set GMAIL_USERNAME environment variable")
        
        if not self.password:
            test_result["errors"].append("Password not provided") 
            test_result["suggestions"].append("Set GMAIL_PASSWORD environment variable")
        elif len(self.password) < 16:
            test_result["errors"].append("Password appears to be regular password, not App Password")
            test_result["suggestions"].append("Generate and use a 16-character App Password")
        
        if not self.host:
            test_result["errors"].append("IMAP host not provided")
            test_result["suggestions"].append("Set GMAIL_IMAP_HOST=imap.gmail.com")
        
        # Test 2: Connection attempt
        if not test_result["errors"]:
            if self.connect():
                test_result["success"] = True
                test_result["message"] = "Connection successful"
                self.disconnect()
            else:
                test_result["errors"].append("Connection failed")
                test_result["suggestions"].append("Check logs above for specific error details")
        
        return test_result
    
    def fetch_unread(self) -> List[Dict[str, Any]]:
        """Fetch unread emails"""
        if not self.imap:
            if not self.connect():
                logger.error("Cannot fetch emails: Not connected to Gmail")
                return []
        
        try:
            # Search for unread messages
            status, messages = self.imap.search(None, 'UNSEEN')
            if status != "OK":
                logger.error(f"Failed to search for unread messages: {status}")
                return []
            
            email_ids = messages[0].split()
            new_emails = []
            
            logger.info(f"Found {len(email_ids)} unread emails")
            
            for eid in email_ids:
                try:
                    status, msg_data = self.imap.fetch(eid, "(RFC822)")
                    if status != "OK":
                        logger.warning(f"Failed to fetch email {eid}: {status}")
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
            
            logger.info(f"Successfully fetched {len(new_emails)} new emails")
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
                logger.error("Cannot fetch emails: Not connected to Gmail")
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
                logger.error(f"Failed to search for messages: {status}")
                return []
            
            email_ids = messages[0].split()
            
            # Get the most recent email IDs (IMAP returns in ascending order)
            recent_ids = email_ids[-count:] if len(email_ids) >= count else email_ids
            recent_emails = []
            
            logger.info(f"Fetching {len(recent_ids)} recent emails")
            
            # Fetch emails in reverse order to get newest first
            for eid in reversed(recent_ids):
                try:
                    status, msg_data = self.imap.fetch(eid, "(RFC822)")
                    if status != "OK":
                        logger.warning(f"Failed to fetch email {eid}: {status}")
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
            
            logger.info(f"Successfully fetched {len(recent_emails)} recent emails by count")
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
                logger.error(f"Failed to search for messages since {search_date}: {status}")
                return []
            
            email_ids = messages[0].split()
            recent_emails = []
            
            logger.info(f"Found {len(email_ids)} emails since {search_date}")
            
            # Fetch emails in reverse order to get newest first
            for eid in reversed(email_ids):
                try:
                    status, msg_data = self.imap.fetch(eid, "(RFC822)")
                    if status != "OK":
                        logger.warning(f"Failed to fetch email {eid}: {status}")
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
            
            logger.info(f"Successfully fetched {len(recent_emails)} emails since {search_date}")
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


# # =============================================================================
# # GMAIL SETUP TESTING UTILITY
# # =============================================================================

# def test_gmail_setup():
#     """Test Gmail setup and provide detailed feedback"""
#     print("🔍 Testing Gmail IMAP Setup...")
#     print("="*50)
    
#     client = GmailClient()
#     test_result = client.test_connection()
    
#     print(f"Host: {test_result['host']}")
#     print(f"Username: {test_result['username']}")
#     print(f"Password Length: {test_result['password_length']} characters")
#     print()
    
#     if test_result['success']:
#         print("✅ Gmail connection successful!")
#     else:
#         print("❌ Gmail connection failed!")
#         print("\nErrors found:")
#         for error in test_result['errors']:
#             print(f"  - {error}")
        
#         print("\nSuggested fixes:")
#         for suggestion in test_result['suggestions']:
#             print(f"  - {suggestion}")
    
#     return test_result['success']


# if __name__ == "__main__":
#     # Run test when script is executed directly
#     test_gmail_setup()