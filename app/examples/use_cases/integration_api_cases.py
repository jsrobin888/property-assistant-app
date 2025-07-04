#!/usr/bin/env python3
"""
Comprehensive API Examples for Property Management System
Focus: AI Response System & Workflow Management
Base URL: CONFIG.base_url_interactive_cli or http://localhost:8000 or http://127.0.0.1:8000

Priority Areas:
1. AI Response Generation & Selection (HIGH PRIORITY)
2. Workflow Control & Processing (HIGH PRIORITY) 
3. Email Management with AI Integration
4. Ticket Management & Creation
5. Database Operations & Analytics
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from ...config import CONFIG
# =============================================================================
# CONFIGURATION & UTILITIES
# =============================================================================

BASE_URL = f"{CONFIG.base_url_interactive_cli}/api/v1"
# Alternative: BASE_URL = "http://localhost:8000/api/v1"
# Alternative: BASE_URL = "http://127.0.0.1:8000/api/v1"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def make_api_call(method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
    """Make API call with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=HEADERS, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, headers=HEADERS, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=HEADERS, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=HEADERS)
        
        response.raise_for_status()
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json(),
            "url": url
        }
        
    except requests.exceptions.RequestException as e:
        error_detail = None
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
        
        return {
            "success": False,
            "error": str(e),
            "error_detail": error_detail,
            "url": url
        }

def print_api_result(title: str, result: Dict):
    """Pretty print API result"""
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")
    print(f"URL: {result['url']}")
    
    if result['success']:
        print(f"✅ Status: {result['status_code']}")
        if 'data' in result:
            print("📋 Response:")
            print(json.dumps(result['data'], indent=2, default=str))
    else:
        print(f"❌ Error: {result['error']}")
        if result.get('error_detail'):
            print(f"📋 Details: {result['error_detail']}")

# =============================================================================
# HIGH PRIORITY: AI RESPONSE SYSTEM EXAMPLES
# =============================================================================

class AIResponseExamples:
    """High Priority: AI Response Generation and Management"""
    
    @staticmethod
    def create_sample_email_for_ai() -> str:
        """Create a sample email that will definitely be processed"""
        email_data = {
            "sender": "urgent.tenant@example.com",
            "subject": "EMERGENCY: Toilet broken and flooding bathroom!",
            "body": """Hi Property Management,
            
            This is an EMERGENCY! The toilet in my apartment Unit 2B is completely broken 
            and flooding water all over the bathroom floor. I can't turn it off and water 
            is spreading to other rooms.
            
            I need a plumber immediately! This is causing major water damage.
            Please fix this urgent maintenance issue right away.
            
            Contact me at 555-123-4567
            
            Thank you,
            John Smith
            Unit 2B""",
            "priority_level": "urgent",
            "context_labels": ["maintenance", "plumbing", "emergency", "flooding"]
        }
        
        result = make_api_call("POST", "/database/emails", email_data)
        print_api_result("Create Sample Email for AI Testing", result)
        
        if result['success']:
            email_id = result['data']['email_id']
            
            # FIX: Immediately process the email to extract action items
            print(f"\n🔧 Processing email {email_id} to extract action items...")
            process_result = make_api_call("POST", f"/workflows/process-single-email/{email_id}")
            print_api_result(f"Process Email {email_id}", process_result)
            
            return email_id
        return None
    
    @staticmethod
    def generate_ai_responses(email_id: str):
        """Generate AI responses for an email (HIGH PRIORITY)"""
        result = make_api_call("POST", f"/emails/{email_id}/regenerate-ai-responses")
        print_api_result(f"Generate AI Responses for Email {email_id}", result)
        return result
    
    @staticmethod
    def view_ai_response_options(email_id: str):
        """View AI response options for an email (HIGH PRIORITY)"""
        result = make_api_call("GET", f"/emails/{email_id}/ai-responses")
        print_api_result(f"View AI Response Options for Email {email_id}", result)
        return result
    
    @staticmethod
    def select_ai_response(email_id: str, option_id: str, rating: float = 4.5, modifications: str = None):
        """Select an AI response option (HIGH PRIORITY)"""
        selection_data = {
            "option_id": option_id,
            "rating": rating,
            "modifications": modifications
        }
        
        result = make_api_call("POST", f"/emails/{email_id}/ai-responses/select", selection_data)
        print_api_result(f"Select AI Response for Email {email_id}", result)
        return result
    
    @staticmethod
    def get_pending_ai_responses():
        """Get all emails with pending AI response selections (HIGH PRIORITY)"""
        result = make_api_call("GET", "/emails/ai-responses/pending")
        print_api_result("Get Pending AI Responses", result)
        return result
    
    @staticmethod
    def bulk_generate_ai_responses(email_ids: List[str]):
        """Generate AI responses for multiple emails"""
        try:
            # FIX: Send email_ids as the main body list
            email_ids_list = [str(email_id) for email_id in email_ids]  # Ensure strings
            
            result = make_api_call("POST", "/emails/bulk/generate-ai-responses", email_ids_list)
            print_api_result("Bulk Generate AI Responses", result)
            return result
                
        except Exception as e:
            print(f"Error in bulk AI generation: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def demo_complete_ai_workflow():
        """Demonstrate complete AI response workflow (HIGH PRIORITY)"""
        print(f"\n{'🤖 COMPLETE AI RESPONSE WORKFLOW DEMO 🤖':=^80}")
        
        # Step 1: Create email
        email_id = AIResponseExamples.create_sample_email_for_ai()
        if not email_id:
            print("❌ Failed to create sample email")
            return
        
        time.sleep(1)
        
        # Step 2: Generate AI responses
        ai_result = AIResponseExamples.generate_ai_responses(email_id)
        if not ai_result['success']:
            print("❌ Failed to generate AI responses")
            return
        
        time.sleep(1)
        
        # Step 3: View response options
        options_result = AIResponseExamples.view_ai_response_options(email_id)
        if not options_result['success']:
            print("❌ Failed to get AI response options")
            return
        
        # Step 4: Select first available option
        ai_responses = options_result['data'].get('ai_responses', [])
        if ai_responses and ai_responses[0].get('response_options'):
            first_option = ai_responses[0]['response_options'][0]
            option_id = first_option['option_id']
            
            # Add custom modifications
            modifications = f"""Dear John,

Thank you for reporting the leaking faucet issue in Unit 2B.

{first_option['content']}

We will also provide you with our 24/7 emergency contact number for future urgent maintenance issues.

Best regards,
Property Management Team"""
            
            time.sleep(1)
            
            # Step 5: Select with modifications and rating
            select_result = AIResponseExamples.select_ai_response(
                email_id, option_id, 
                rating=4.5, 
                modifications=modifications
            )
            
            if select_result['success']:
                print("\n🎉 COMPLETE AI WORKFLOW SUCCESSFUL!")
                print(f"✅ Email ID: {email_id}")
                print(f"✅ Selected Option: {option_id[:8]}...")
                print(f"✅ Rating: 4.5/5.0")
                print(f"✅ Modified: Yes")
            else:
                print("❌ Failed to select AI response")
        else:
            print("❌ No AI response options available")

# =============================================================================
# HIGH PRIORITY: WORKFLOW CONTROL EXAMPLES  
# =============================================================================

class WorkflowExamples:
    """High Priority: Workflow Control and Email Processing"""
    
    @staticmethod
    def trigger_complete_email_processing(auto_create_tickets: bool = True):
        """Trigger complete email processing workflow (HIGH PRIORITY)"""
        workflow_data = {
            "auto_replay_strategy": None,  # Don't auto-reply, let user select
            "auto_create_tickets": auto_create_tickets,
            "mark_as_read": True
        }
        
        result = make_api_call("POST", "/workflows/process-emails", workflow_data)
        print_api_result("Trigger Complete Email Processing Workflow", result)
        return result
    
    @staticmethod
    def monitor_workflow_status(workflow_id: str, max_checks: int = 10):
        """Monitor workflow status until completion (HIGH PRIORITY)"""
        print(f"\n📊 Monitoring Workflow: {workflow_id}")
        
        for check in range(max_checks):
            result = make_api_call("GET", f"/workflows/status/{workflow_id}")
            
            if result['success']:
                status = result['data']['status']
                print(f"Check {check + 1}: Status = {status}")
                
                if status == "completed":
                    print_api_result(f"Workflow {workflow_id} COMPLETED", result)
                    return result
                elif status == "failed":
                    print_api_result(f"Workflow {workflow_id} FAILED", result)
                    return result
            
            time.sleep(2)  # Wait 2 seconds between checks
        
        print(f"⚠️ Workflow monitoring timed out after {max_checks} checks")
        return None
    
    @staticmethod
    def fetch_gmail_emails(fetch_type: str = "recent", count: int = 5):
        """Fetch emails from Gmail (HIGH PRIORITY)"""
        gmail_data = {
            "fetch_type": fetch_type,
            "count": count,
            "mark_as_read": False
        }
        
        result = make_api_call("POST", "/workflows/fetch-gmail", gmail_data)
        print_api_result(f"Fetch Gmail Emails ({fetch_type})", result)
        return result
    
    @staticmethod
    def process_single_email(email_id: str):
        """Process a single email through workflow (HIGH PRIORITY)"""
        result = make_api_call("POST", f"/workflows/process-single-email/{email_id}")
        print_api_result(f"Process Single Email {email_id}", result)
        return result
    
    @staticmethod
    def create_tickets_from_email(email_id: str, force_create: bool = False):
        """Create tickets from email action items """
        # FIX: Ensure email_id is a string
        ticket_data = {
            "email_id": str(email_id),  # Convert to string
            "force_create": force_create
        }
        
        result = make_api_call("POST", "/workflows/create-tickets-from-email", ticket_data)
        print_api_result(f"Create Tickets from Email {email_id}", result)
        return result

    
    @staticmethod
    def check_system_health():
        """Check workflow system health (HIGH PRIORITY)"""
        result = make_api_call("GET", "/workflows/health-check")
        print_api_result("Workflow System Health Check", result)
        return result
    
    @staticmethod
    def demo_complete_workflow():
        """Demonstrate complete workflow processing (HIGH PRIORITY)"""
        print(f"\n{'⚙️ COMPLETE WORKFLOW PROCESSING DEMO ⚙️':=^80}")
        
        # Step 1: Check system health
        health_result = WorkflowExamples.check_system_health()
        if not health_result['success']:
            print("❌ System health check failed")
            return
        
        # Step 2: Fetch emails from Gmail
        # gmail_result = WorkflowExamples.fetch_gmail_emails("recent", 3)
        # Note: Gmail fetch may fail without proper credentials, continue anyway
        
        # Step 3: Trigger complete email processing
        workflow_result = WorkflowExamples.trigger_complete_email_processing(True)
        if not workflow_result['success']:
            print("❌ Failed to trigger workflow")
            return
        
        workflow_id = workflow_result['data']['workflow_id']
        print(f"🚀 Started Workflow: {workflow_id}")
        
        # Step 4: Monitor workflow progress
        final_result = WorkflowExamples.monitor_workflow_status(workflow_id)
        
        if final_result and final_result['success']:
            print("\n🎉 COMPLETE WORKFLOW PROCESSING SUCCESSFUL!")
        else:
            print("❌ Workflow did not complete successfully")

# =============================================================================
# EMAIL MANAGEMENT WITH AI INTEGRATION
# =============================================================================

class EmailManagementExamples:
    """Email Management with AI Integration Examples"""
    
    @staticmethod
    def create_test_emails() -> List[str]:
        """Create multiple test emails for demonstrations"""
        test_emails = [
            {
                "sender": "alice.tenant@example.com",
                "subject": "Heater not working in Unit 3A",
                "body": "The heater in my apartment stopped working yesterday. It's getting very cold. Please send someone to fix it.",
                "priority_level": "high",
                "context_labels": ["maintenance", "hvac", "urgent"]
            },
            {
                "sender": "bob.resident@demo.org", 
                "subject": "Question about rent payment",
                "body": "I received a late fee notice but I paid my rent on time. Can you please check my account?",
                "priority_level": "medium",
                "context_labels": ["payment", "inquiry"]
            },
            {
                "sender": "carol.jones@test.net",
                "subject": "Noisy neighbors complaint",
                "body": "My upstairs neighbors are very loud at night. Music and shouting until 2 AM. This has been going on for a week.",
                "priority_level": "medium", 
                "context_labels": ["complaint", "noise", "neighbor"]
            }
        ]
        
        email_ids = []
        for i, email_data in enumerate(test_emails, 1):
            result = make_api_call("POST", "/database/emails", email_data)
            print_api_result(f"Create Test Email {i}", result)
            
            if result['success']:
                email_ids.append(result['data']['email_id'])
        
        return email_ids
    
    @staticmethod
    def list_emails_with_filters():
        """List emails with various filters"""
        # Get all emails
        params = {"limit": 20, "skip": 0}
        result = make_api_call("GET", "/emails/", params=params)
        print_api_result("List All Emails (Limited)", result)
        
        # Get high priority emails
        params = {"priority": "high", "limit": 10}
        result = make_api_call("GET", "/emails/", params=params)
        print_api_result("List High Priority Emails", result)
        
        # Get emails with pending AI responses
        params = {"has_replies": False, "limit": 10}
        result = make_api_call("GET", "/emails/", params=params)
        print_api_result("List Emails Without Replies", result)
    
    @staticmethod
    def get_email_details(email_id: str):
        """Get comprehensive email details"""
        result = make_api_call("GET", f"/emails/{email_id}")
        print_api_result(f"Get Email Details for {email_id}", result)
        return result
    
    @staticmethod
    def update_email_status(email_id: str, status: str, notes: str = None):
        """Update email status"""
        update_data = {"status": status}
        if notes:
            update_data["notes"] = notes
        
        result = make_api_call("PUT", f"/emails/{email_id}/status", update_data)
        print_api_result(f"Update Email Status to {status}", result)
        return result
    
    @staticmethod
    def search_emails(query: str):
        """Search emails by content"""
        search_data = {
            "query": query,
            "search_fields": ["subject", "body", "sender"],
            "limit": 10
        }
        
        result = make_api_call("POST", "/emails/search", search_data)
        print_api_result(f"Search Emails for '{query}'", result)
        return result
    
    @staticmethod
    def get_email_analytics():
        """Get email analytics and trends"""
        result = make_api_call("GET", "/emails/analytics/summary")
        print_api_result("Email Analytics Summary", result)
        
        # Get trends
        params = {"days": 30}
        result = make_api_call("GET", "/emails/analytics/trends", params=params)
        print_api_result("Email Trends (30 days)", result)
        
        return result
    
    @staticmethod
    def demo_email_management_with_ai():
        """Demonstrate email management with AI integration"""
        print(f"\n{'📧 EMAIL MANAGEMENT WITH AI DEMO 📧':=^80}")
        
        # Step 1: Create test emails
        email_ids = EmailManagementExamples.create_test_emails()
        if not email_ids:
            print("❌ Failed to create test emails")
            return
        
        time.sleep(1)
        
        # Step 2: Generate AI responses for all emails
        AIResponseExamples.bulk_generate_ai_responses(email_ids)
        
        time.sleep(2)
        
        # Step 3: View and select responses for first email
        first_email_id = email_ids[0]
        options_result = AIResponseExamples.view_ai_response_options(first_email_id)
        
        if options_result['success']:
            ai_responses = options_result['data'].get('ai_responses', [])
            if ai_responses and ai_responses[0].get('response_options'):
                first_option = ai_responses[0]['response_options'][0]
                AIResponseExamples.select_ai_response(
                    first_email_id, 
                    first_option['option_id'], 
                    rating=4.0
                )
        
        # Step 4: Update email status
        EmailManagementExamples.update_email_status(
            first_email_id, 
            "responded", 
            "AI response selected and sent"
        )
        
        time.sleep(1)
        
        # Step 5: Search for maintenance emails
        EmailManagementExamples.search_emails("heater")
        
        # Step 6: Get analytics
        EmailManagementExamples.get_email_analytics()
        
        print("\n🎉 EMAIL MANAGEMENT WITH AI DEMO COMPLETED!")

# =============================================================================
# TICKET MANAGEMENT EXAMPLES
# =============================================================================

class TicketManagementExamples:
    """Ticket Management System Examples"""
    
    @staticmethod
    def list_tickets_with_filters():
        """List tickets with various filters"""
        # Get all tickets
        params = {"limit": 20}
        result = make_api_call("GET", "/tickets/", params=params)
        print_api_result("List All Tickets", result)
        
        # Get open tickets
        params = {"status": "New", "limit": 10}
        result = make_api_call("GET", "/tickets/", params=params)
        print_api_result("List New Tickets", result)
        
        # Get high urgency tickets
        params = {"urgency": "1", "limit": 10}
        result = make_api_call("GET", "/tickets/", params=params)
        print_api_result("List High Urgency Tickets", result)
    
    @staticmethod
    def get_ticket_details(ticket_id: str):
        """Get ticket details"""
        result = make_api_call("GET", f"/tickets/{ticket_id}")
        print_api_result(f"Get Ticket Details for {ticket_id}", result)
        return result
    
    @staticmethod
    def update_ticket_status(ticket_id: str, status: str, notes: str = None):
        """Update ticket status"""
        update_data = {"status": status}
        if notes:
            update_data["notes"] = notes
        
        result = make_api_call("PUT", f"/tickets/{ticket_id}", update_data)
        print_api_result(f"Update Ticket Status to {status}", result)
        return result
    
    @staticmethod
    def assign_ticket(ticket_id: str, assigned_to: str, assignment_group: str = None):
        """Assign ticket to person/group"""
        update_data = {"assigned_to": assigned_to}
        if assignment_group:
            update_data["assignment_group"] = assignment_group
        
        result = make_api_call("PUT", f"/tickets/{ticket_id}", update_data)
        print_api_result(f"Assign Ticket to {assigned_to}", result)
        return result
    
    @staticmethod
    def batch_assign_tickets(ticket_ids: List[str], assigned_to: str):
        """Assign multiple tickets in batch"""
        batch_data = {
            "ticket_ids": ticket_ids,
            "assigned_to": assigned_to,
            "assignment_group": "Maintenance Team"
        }
        
        result = make_api_call("POST", "/tickets/batch/assign", batch_data)
        print_api_result("Batch Assign Tickets", result)
        return result
    
    @staticmethod
    def get_ticket_statistics():
        """Get ticket statistics"""
        result = make_api_call("GET", "/tickets/stats/summary")
        print_api_result("Ticket Statistics Summary", result)
        return result
    
    @staticmethod
    def search_tickets(query: str):
        """Search tickets"""
        result = make_api_call("GET", f"/tickets/search/{query}")
        print_api_result(f"Search Tickets for '{query}'", result)
        return result
    
    @staticmethod
    def get_open_tickets():
        """Get all open tickets"""
        result = make_api_call("GET", "/tickets/open/list")
        print_api_result("Get All Open Tickets", result)
        return result

# =============================================================================
# DATABASE OPERATIONS EXAMPLES
# =============================================================================

class DatabaseExamples:
    """Database Operations and Statistics Examples"""
    
    @staticmethod
    def get_database_statistics():
        """Get comprehensive database statistics"""
        result = make_api_call("GET", "/database/stats")
        print_api_result("Database Statistics", result)
        return result
    
    @staticmethod
    def list_database_tables():
        """List all database tables and their info"""
        result = make_api_call("GET", "/database/tables")
        print_api_result("Database Tables Information", result)
        return result
    
    @staticmethod
    def get_daily_summary(date: str = None):
        """Get daily summary report"""
        params = {}
        if date:
            params["date"] = date
        
        result = make_api_call("GET", "/database/reports/daily-summary", params=params)
        print_api_result("Daily Summary Report", result)
        return result
    
    @staticmethod
    def search_database_emails(query: str):
        """Search emails in database"""
        params = {
            "query": query,
            "search_in": "all",
            "limit": 10
        }
        
        result = make_api_call("GET", "/database/search/emails", params=params)
        print_api_result(f"Database Email Search for '{query}'", result)
        return result
    
    @staticmethod
    def get_tenant_information():
        """Get tenant information"""
        result = make_api_call("GET", "/database/tenants")
        print_api_result("All Tenants Information", result)
        
        # Get tenant by email if any exist
        if result['success'] and result['data']['tenants']:
            first_tenant_email = result['data']['tenants'][0]['email']
            tenant_result = make_api_call("GET", f"/database/tenants/by-email/{first_tenant_email}")
            print_api_result(f"Tenant Details for {first_tenant_email}", tenant_result)
        
        return result

# =============================================================================
# WORKFLOW STATUS AND EMAIL PROCESSING EXAMPLES
# =============================================================================

class WorkflowStatusExamples:
    """Workflow Status and Email Processing Examples"""
    
    @staticmethod
    def get_email_workflow_status(email_id: str):
        """Get comprehensive workflow status for an email"""
        result = make_api_call("GET", f"/emails/{email_id}/workflow-status")
        print_api_result(f"Workflow Status for Email {email_id}", result)
        return result
    
    @staticmethod
    def reprocess_email(email_id: str):
        """Reprocess an email through the complete workflow"""
        result = make_api_call("POST", f"/emails/{email_id}/reprocess")
        print_api_result(f"Reprocess Email {email_id}", result)
        return result
    
    @staticmethod
    def get_all_workflow_statuses():
        """Get status of all workflows"""
        result = make_api_call("GET", "/workflows/status")
        print_api_result("All Workflow Statuses", result)
        return result
    
    @staticmethod
    def bulk_update_email_status(email_ids: List[str], new_status: str, notes: Optional[str] = None):
        """Update status for multiple emails  VERSION"""
        try:
            # Correct way: All parameters in the JSON body
            bulk_data = {
                "email_ids": [str(email_id) for email_id in email_ids],
                "new_status": new_status
            }
            if notes:
                bulk_data["notes"] = notes
            
            result = make_api_call("POST", "/emails/bulk/update-status", bulk_data)
            print_api_result("Bulk Update Email Status (FIXED)", result)
            return result
            
        except Exception as e:
            print(f"Error in bulk update: {e}")
            return {"success": False, "error": str(e)}

# ============================================================================
# MANUAL TEST FOR BULK OPERATIONS
# ============================================================================

def test_bulk_operations_manually():
    """Test bulk operations with different approaches"""
    print("🧪 TESTING BULK OPERATIONS MANUALLY")
    print("="*40)
    
    # Create some test emails first
    test_emails = []
    for i in range(3):
        email_data = {
            "sender": f"bulktest{i+1}@example.com",
            "subject": f"Bulk test email {i+1}",
            "body": f"This is bulk test email number {i+1} for testing bulk operations.",
            "priority_level": "medium"
        }
        
        result = make_api_call("POST", "/database/emails", email_data)
        if result['success']:
            test_emails.append(str(result['data']['email_id']))
            print(f"✅ Created test email {i+1}: {result['data']['email_id']}")
    
    if not test_emails:
        print("❌ No test emails created, cannot test bulk operations")
        return
    
    print(f"\n📋 Testing with email IDs: {test_emails}")
    
    # Test 1: Bulk AI generation with different approaches
    print(f"\n🤖 Test 1: Bulk AI Generation")
    print("-" * 30)
    
    # Approach 1: Direct list
    print("Approach 1: Sending email_ids as direct list...")
    try:
        response = requests.post(
            f"{BASE_URL}/emails/bulk/generate-ai-responses",
            json=test_emails,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Direct list approach works!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Approach 2: Object wrapper
    print("\nApproach 2: Sending as object with email_ids key...")
    try:
        response = requests.post(
            f"{BASE_URL}/emails/bulk/generate-ai-responses",
            json={"email_ids": test_emails},
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Object wrapper approach works!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Bulk status update with different approaches
    print(f"\n📊 Test 2: Bulk Status Update")
    print("-" * 30)
    
    # Approach 1: Query parameters
    print("Approach 1: email_ids as body, status as query param...")
    try:
        response = requests.post(
            f"{BASE_URL}/emails/bulk/update-status?new_status=processing&notes=bulk test",
            json=test_emails,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Query param approach works!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Approach 2: All in body
    print("\nApproach 2: Everything in JSON body...")
    try:
        response = requests.post(
            f"{BASE_URL}/emails/bulk/update-status",
            json={
                "email_ids": test_emails,
                "new_status": "processing", 
                "notes": "bulk test"
            },
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ JSON body approach works!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")


# =============================================================================
# COMPREHENSIVE DEMO SCENARIOS
# =============================================================================

class ComprehensiveDemos:
    """Complete demonstration scenarios combining multiple APIs"""
    
    @staticmethod
    def demo_end_to_end_email_processing():
        """Complete end-to-end email processing demo"""
        print(f"\n{'🌟 END-TO-END EMAIL PROCESSING DEMO 🌟':=^80}")
        
        # 1. Create sample email
        email_id = AIResponseExamples.create_sample_email_for_ai()
        if not email_id:
            return
        
        # 2. Process email through workflow
        WorkflowExamples.process_single_email(email_id)
        time.sleep(2)
        
        # 3. Generate AI responses
        AIResponseExamples.generate_ai_responses(email_id)
        time.sleep(2)
        
        # 4. Create tickets from email
        WorkflowExamples.create_tickets_from_email(email_id)
        time.sleep(1)
        
        # 5. View workflow status
        WorkflowStatusExamples.get_email_workflow_status(email_id)
        
        # 6. Select AI response
        options_result = AIResponseExamples.view_ai_response_options(email_id)
        if options_result['success']:
            ai_responses = options_result['data'].get('ai_responses', [])
            if ai_responses and ai_responses[0].get('response_options'):
                first_option = ai_responses[0]['response_options'][0]
                AIResponseExamples.select_ai_response(
                    email_id, 
                    first_option['option_id'], 
                    rating=5.0
                )
        
        print("\n🎉 END-TO-END PROCESSING COMPLETED!")
    
    @staticmethod
    def demo_ai_response_comparison():
        """Demo comparing different AI response strategies"""
        print(f"\n{'🤖 AI RESPONSE STRATEGY COMPARISON DEMO 🤖':=^80}")
        
        # Create multiple emails for testing different strategies
        test_scenarios = [
            {
                "sender": "urgent.tenant@example.com",
                "subject": "EMERGENCY: Water flooding my apartment",
                "body": "There's water flooding my bathroom from upstairs! Emergency help needed NOW!",
                "priority_level": "urgent",
                "context_labels": ["emergency", "water", "flooding"]
            },
            {
                "sender": "polite.tenant@example.com", 
                "subject": "Maintenance request for broken AC",
                "body": "Dear Property Management, the AC in my unit has stopped working. Would appreciate if someone could take a look when convenient. Thank you!",
                "priority_level": "medium",
                "context_labels": ["maintenance", "hvac"]
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n--- Scenario {i}: {scenario['subject']} ---")
            
            # Create email
            result = make_api_call("POST", "/database/emails", scenario)
            if result['success']:
                email_id = result['data']['email_id']
                
                # Generate multiple AI response sets
                for attempt in range(2):
                    AIResponseExamples.generate_ai_responses(email_id)
                    time.sleep(1)
                
                # View all generated options
                AIResponseExamples.view_ai_response_options(email_id)
    
    @staticmethod
    def demo_system_monitoring():
        """Demo system monitoring and health checks"""
        print(f"\n{'📊 SYSTEM MONITORING DEMO 📊':=^80}")
        
        # System health
        WorkflowExamples.check_system_health()
        
        # Database statistics
        DatabaseExamples.get_database_statistics()
        
        # Email analytics
        EmailManagementExamples.get_email_analytics()
        
        # Ticket statistics
        TicketManagementExamples.get_ticket_statistics()
        
        # Workflow statuses
        WorkflowStatusExamples.get_all_workflow_statuses()
        
        # Pending AI responses
        AIResponseExamples.get_pending_ai_responses()
        
        print("\n📈 SYSTEM MONITORING COMPLETED!")

# =============================================================================
# MAIN EXECUTION FUNCTIONS
# =============================================================================

def run_high_priority_ai_examples():
    """Run high priority AI-focused examples"""
    print(f"\n{'🚀 HIGH PRIORITY: AI RESPONSE SYSTEM EXAMPLES 🚀':=^80}")
    
    # Complete AI workflow demonstration
    AIResponseExamples.demo_complete_ai_workflow()
    
    # Pending AI responses management
    print(f"\n{'📋 PENDING AI RESPONSES MANAGEMENT':=^60}")
    AIResponseExamples.get_pending_ai_responses()
    
    # Bulk AI response generation
    print(f"\n{'⚡ BULK AI RESPONSE GENERATION':=^60}")
    email_ids = EmailManagementExamples.create_test_emails()
    if email_ids:
        AIResponseExamples.bulk_generate_ai_responses(email_ids[:2])  # Test with 2 emails

def run_high_priority_workflow_examples():
    """Run high priority workflow-focused examples"""
    print(f"\n{'⚙️ HIGH PRIORITY: WORKFLOW CONTROL EXAMPLES ⚙️':=^80}")
    
    # Complete workflow demonstration
    WorkflowExamples.demo_complete_workflow()
    
    # Individual workflow components
    print(f"\n{'🔧 INDIVIDUAL WORKFLOW COMPONENTS':=^60}")
    
    # Gmail fetch (may require credentials)
    try:
        WorkflowExamples.fetch_gmail_emails("recent", 3)
    except Exception as e:
        print(f"ℹ️ Gmail fetch skipped (credentials required): {e}")
    
    # System health monitoring
    WorkflowExamples.check_system_health()

def run_complete_integration_examples():
    """Run complete integration examples showing combined functionality"""
    print(f"\n{'🌟 COMPLETE INTEGRATION EXAMPLES 🌟':=^80}")
    
    # End-to-end processing
    ComprehensiveDemos.demo_end_to_end_email_processing()
    
    time.sleep(2)
    
    # AI strategy comparison
    ComprehensiveDemos.demo_ai_response_comparison()
    
    time.sleep(2)
    
    # System monitoring
    ComprehensiveDemos.demo_system_monitoring()

def run_crud_operation_examples():
    """Run CRUD operation examples across all entities"""
    print(f"\n{'📊 CRUD OPERATIONS EXAMPLES 📊':=^80}")
    
    # Email CRUD with AI integration
    print(f"\n{'📧 EMAIL CRUD WITH AI INTEGRATION':=^60}")
    EmailManagementExamples.demo_email_management_with_ai()
    
    # Ticket management
    print(f"\n{'🎫 TICKET MANAGEMENT CRUD':=^60}")
    TicketManagementExamples.list_tickets_with_filters()
    TicketManagementExamples.get_ticket_statistics()
    TicketManagementExamples.search_tickets("maintenance")
    
    # Database operations
    print(f"\n{'💾 DATABASE OPERATIONS':=^60}")
    DatabaseExamples.get_database_statistics()
    DatabaseExamples.list_database_tables()
    DatabaseExamples.get_daily_summary()
    DatabaseExamples.get_tenant_information()

def run_advanced_scenarios():
    """Run advanced usage scenarios """
    print(f"\n{'🎯 ADVANCED USAGE SCENARIOS 🎯':=^80}")
    
    # Scenario 1: High-volume email processing 
    print(f"\n{'📈 SCENARIO 1: HIGH-VOLUME EMAIL PROCESSING':=^60}")
    
    # Create multiple emails with proper processing
    email_ids = []
    test_emails = [
        {
            "sender": f"tenant{i+1}@example.com",
            "subject": f"Urgent maintenance request #{i+1}",
            "body": f"My toilet in Unit {i+1}A is broken and leaking water everywhere. Please send a plumber to fix this immediately. This is urgent maintenance.",
            "priority_level": "urgent",
            "context_labels": ["maintenance", "plumbing", "urgent"]
        }
        for i in range(5)
    ]
    
    # Create and process emails
    for email_data in test_emails:
        result = make_api_call("POST", "/database/emails", email_data)
        if result['success']:
            email_id = result['data']['email_id']
            email_ids.append(str(email_id))  # Ensure string
            
            # Process email to extract action items
            make_api_call("POST", f"/workflows/process-single-email/{email_id}")
    
    # FIX: Use corrected bulk operations
    if email_ids:
        #bulk AI generation
        bulk_ai_result = AIResponseExamples.bulk_generate_ai_responses(email_ids)
        time.sleep(2)
        
        #bulk status update  
        bulk_status_result = WorkflowStatusExamples.bulk_update_email_status(email_ids, "processing", "Bulk processing test")
    
    # Scenario 2: Emergency response workflow 
    print(f"\n{'🚨 SCENARIO 2: EMERGENCY RESPONSE WORKFLOW':=^60}")
    
    emergency_email = {
        "sender": "emergency.tenant@example.com",
        "subject": "URGENT: Gas leak smell in building",
        "body": "I smell gas in the hallway of my building Unit 5B. This could be dangerous and needs immediate attention. Please send someone immediately!",
        "priority_level": "urgent",
        "context_labels": ["emergency", "gas", "safety", "maintenance"]
    }
    
    result = make_api_call("POST", "/database/emails", emergency_email)
    if result['success']:
        emergency_email_id = str(result['data']['email_id'])  # Ensure string
        
        # Process the email first
        process_result = make_api_call("POST", f"/workflows/process-single-email/{emergency_email_id}")
        time.sleep(1)
        
        # Generate AI responses
        ai_result = make_api_call("POST", f"/emails/{emergency_email_id}/regenerate-ai-responses")
        time.sleep(1)
        
        # FIX: Create tickets with string email_id
        ticket_result = WorkflowExamples.create_tickets_from_email(emergency_email_id, True)
        
        # Check workflow status
        status_result = make_api_call("GET", f"/emails/{emergency_email_id}/workflow-status")
        print_api_result(f"Emergency Workflow Status", status_result)

def run_api_testing_suite():
    """Run comprehensive API testing suite"""
    print(f"\n{'🧪 COMPREHENSIVE API TESTING SUITE 🧪':=^80}")
    
    test_results = {
        "ai_response_tests": 0,
        "workflow_tests": 0,
        "email_tests": 0,
        "ticket_tests": 0,
        "database_tests": 0,
        "total_tests": 0,
        "passed_tests": 0
    }
    
    # AI Response System Tests
    print(f"\n{'🤖 AI RESPONSE SYSTEM TESTS':=^60}")
    tests = [
        ("Create Sample Email", lambda: AIResponseExamples.create_sample_email_for_ai()),
        ("Get Pending AI Responses", lambda: AIResponseExamples.get_pending_ai_responses()),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            success = result is not None if isinstance(result, str) else (result and result.get('success', False))
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name}: {status}")
            if success:
                test_results["passed_tests"] += 1
            test_results["ai_response_tests"] += 1
            test_results["total_tests"] += 1
        except Exception as e:
            print(f"{test_name}: ❌ ERROR - {e}")
            test_results["ai_response_tests"] += 1
            test_results["total_tests"] += 1
    
    # Workflow System Tests
    print(f"\n{'⚙️ WORKFLOW SYSTEM TESTS':=^60}")
    workflow_tests = [
        ("System Health Check", lambda: WorkflowExamples.check_system_health()),
        ("Get All Workflow Statuses", lambda: WorkflowStatusExamples.get_all_workflow_statuses()),
    ]
    
    for test_name, test_func in workflow_tests:
        try:
            result = test_func()
            success = result and result.get('success', False)
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name}: {status}")
            if success:
                test_results["passed_tests"] += 1
            test_results["workflow_tests"] += 1
            test_results["total_tests"] += 1
        except Exception as e:
            print(f"{test_name}: ❌ ERROR - {e}")
            test_results["workflow_tests"] += 1
            test_results["total_tests"] += 1
    
    # Email Management Tests
    print(f"\n{'📧 EMAIL MANAGEMENT TESTS':=^60}")
    email_tests = [
        ("List Emails", lambda: make_api_call("GET", "/emails/", params={"limit": 5})),
        ("Get Email Analytics", lambda: EmailManagementExamples.get_email_analytics()),
        ("Search Emails", lambda: EmailManagementExamples.search_emails("test")),
    ]
    
    for test_name, test_func in email_tests:
        try:
            result = test_func()
            success = result and result.get('success', False)
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name}: {status}")
            if success:
                test_results["passed_tests"] += 1
            test_results["email_tests"] += 1
            test_results["total_tests"] += 1
        except Exception as e:
            print(f"{test_name}: ❌ ERROR - {e}")
            test_results["email_tests"] += 1
            test_results["total_tests"] += 1
    
    # Ticket Management Tests
    print(f"\n{'🎫 TICKET MANAGEMENT TESTS':=^60}")
    ticket_tests = [
        ("List Tickets", lambda: make_api_call("GET", "/tickets/", params={"limit": 5})),
        ("Get Ticket Statistics", lambda: TicketManagementExamples.get_ticket_statistics()),
        ("Get Open Tickets", lambda: TicketManagementExamples.get_open_tickets()),
    ]
    
    for test_name, test_func in ticket_tests:
        try:
            result = test_func()
            success = result and result.get('success', False)
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name}: {status}")
            if success:
                test_results["passed_tests"] += 1
            test_results["ticket_tests"] += 1
            test_results["total_tests"] += 1
        except Exception as e:
            print(f"{test_name}: ❌ ERROR - {e}")
            test_results["ticket_tests"] += 1
            test_results["total_tests"] += 1
    
    # Database Tests
    print(f"\n{'💾 DATABASE TESTS':=^60}")
    db_tests = [
        ("Database Statistics", lambda: DatabaseExamples.get_database_statistics()),
        ("List Tables", lambda: DatabaseExamples.list_database_tables()),
        ("Daily Summary", lambda: DatabaseExamples.get_daily_summary()),
    ]
    
    for test_name, test_func in db_tests:
        try:
            result = test_func()
            success = result and result.get('success', False)
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name}: {status}")
            if success:
                test_results["passed_tests"] += 1
            test_results["database_tests"] += 1
            test_results["total_tests"] += 1
        except Exception as e:
            print(f"{test_name}: ❌ ERROR - {e}")
            test_results["database_tests"] += 1
            test_results["total_tests"] += 1
    
    # Print test summary
    print(f"\n{'📊 TEST RESULTS SUMMARY':=^60}")
    print(f"AI Response Tests: {test_results['ai_response_tests']} tests")
    print(f"Workflow Tests: {test_results['workflow_tests']} tests")
    print(f"Email Tests: {test_results['email_tests']} tests")
    print(f"Ticket Tests: {test_results['ticket_tests']} tests")
    print(f"Database Tests: {test_results['database_tests']} tests")
    print(f"")
    print(f"Total Tests: {test_results['total_tests']}")
    print(f"Passed Tests: {test_results['passed_tests']}")
    print(f"Failed Tests: {test_results['total_tests'] - test_results['passed_tests']}")
    print(f"Success Rate: {(test_results['passed_tests'] / test_results['total_tests'] * 100):.1f}%")

# ============================================================================
# ADDITIONAL DEBUG HELPER
# ============================================================================

def debug_email_processing_api():
    """Debug why emails aren't being processed properly"""
    print(f"\n{'🔍 DEBUGGING EMAIL PROCESSING':=^60}")
    
    # Create a test email
    test_email = {
        "sender": "debug.test@example.com",
        "subject": "Debug: Broken heater needs immediate repair",
        "body": "The heater in my apartment is completely broken. No heat at all. Please send maintenance to fix this urgent repair issue.",
        "priority_level": "high",
        "context_labels": ["maintenance", "hvac", "repair"]
    }
    
    # Step 1: Create email
    result = make_api_call("POST", "/database/emails", test_email)
    if not result['success']:
        print("❌ Failed to create email")
        return
    
    email_id = str(result['data']['email_id'])
    print(f"✅ Created email: {email_id}")
    
    # Step 2: Check email details before processing
    email_details = make_api_call("GET", f"/emails/{email_id}")
    print_api_result("Email Details Before Processing", email_details)
    
    # Step 3: Process email
    process_result = make_api_call("POST", f"/workflows/process-single-email/{email_id}")
    print_api_result("Email Processing Result", process_result)
    
    # Step 4: Check email details after processing
    email_details_after = make_api_call("GET", f"/emails/{email_id}")
    print_api_result("Email Details After Processing", email_details_after)
    
    # Step 5: Check workflow status
    workflow_status = make_api_call("GET", f"/emails/{email_id}/workflow-status")
    print_api_result("Workflow Status", workflow_status)
    
    # Step 6: Try creating tickets
    ticket_result = WorkflowExamples.create_tickets_from_email(email_id, True)
    
    return email_id

# =============================================================================
# QUICK START EXAMPLES
# =============================================================================

def quick_start_examples():
    """Quick start examples for immediate testing"""
    print(f"\n{'⚡ QUICK START EXAMPLES ⚡':=^80}")
    
    print("\n1️⃣ Health Check")
    result = make_api_call("GET", "/workflows/health-check")
    print_api_result("System Health Check", result)
    
    print("\n2️⃣ Create Test Email")
    email_data = {
        "sender": "quicktest@example.com",
        "subject": "Quick test email",
        "body": "This is a quick test of the email system.",
        "priority_level": "medium"
    }
    result = make_api_call("POST", "/database/emails", email_data)
    print_api_result("Create Quick Test Email", result)
    
    if result['success']:
        email_id = result['data']['email_id']
        
        print("\n3️⃣ Generate AI Response")
        ai_result = make_api_call("POST", f"/emails/{email_id}/regenerate-ai-responses")
        print_api_result("Generate AI Response", ai_result)
        
        print("\n4️⃣ View AI Options")
        options_result = make_api_call("GET", f"/emails/{email_id}/ai-responses")
        print_api_result("View AI Response Options", options_result)
        
        # Auto-select first option if available
        if options_result['success']:
            ai_responses = options_result['data'].get('ai_responses', [])
            if ai_responses and ai_responses[0].get('response_options'):
                first_option = ai_responses[0]['response_options'][0]
                
                print("\n5️⃣ Select AI Response")
                selection_data = {"option_id": first_option['option_id'], "rating": 5.0}
                select_result = make_api_call("POST", f"/emails/{email_id}/ai-responses/select", selection_data)
                print_api_result("Select AI Response", select_result)
    
    print("\n6️⃣ Database Statistics")
    stats_result = make_api_call("GET", "/database/stats")
    print_api_result("Database Statistics", stats_result)

# Usage: Add this to the interactive menu
def interactive_examples():
    """Enhanced interactive examples with debugging"""
    print(f"\n{'🎮 INTERACTIVE EXAMPLES 🎮':=^80}")
    
    while True:
        print("\nChoose an example to run:")
        print("1. Quick Start (Health + Create Email + AI Response)")
        print("2. Complete AI Workflow Demo")
        print("3. Complete Workflow Processing Demo") 
        print("4. Email Management with AI Demo")
        print("5. System Monitoring Demo")
        print("6. Run All High Priority Examples")
        print("7. Run Comprehensive Test Suite")
        print("8. Advanced Scenarios (FIXED)")
        print("9. Debug Email Processing (NEW)")  # Added debug option
        print("10. Exit")
        
        try:
            choice = input("\nEnter your choice (1-10): ").strip()
            
            if choice == "1":
                quick_start_examples()
            elif choice == "2":
                AIResponseExamples.demo_complete_ai_workflow()
            elif choice == "3":
                WorkflowExamples.demo_complete_workflow()
            elif choice == "4":
                EmailManagementExamples.demo_email_management_with_ai()
            elif choice == "5":
                ComprehensiveDemos.demo_system_monitoring()
            elif choice == "6":
                run_high_priority_ai_examples()
                run_high_priority_workflow_examples()
            elif choice == "7":
                run_api_testing_suite()
            elif choice == "8":
                run_advanced_scenarios()  #version
            elif choice == "9":
                debug_email_processing_api()  # New debug function
            elif choice == "10":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-10.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


# ============================================================================
# Workflow TESTING
# ============================================================================

def test_fixed_workflow():
    """Test the completeworkflow"""
    
    print("🔧 TESTINGWORKFLOW")
    print("="*30)
    
    # Step 1: Create email with guaranteed keywords
    test_email = {
        "sender": "test.tenant@example.com",
        "subject": "EMERGENCY: Toilet flooding and broken heater",
        "body": "My toilet is flooding the bathroom and my heater is also broken. I need urgent maintenance repair for both issues. Please send a plumber and HVAC technician immediately!",
        "priority_level": "urgent",
        "context_labels": ["maintenance", "plumbing", "hvac", "emergency"]
    }
    
    print("📧 Creating test email...")
    result = make_api_call("POST", "/database/emails", test_email)
    
    if not result['success']:
        print("❌ Failed to create email")
        return
    
    email_id = str(result['data']['email_id'])
    print(f"✅ Created email: {email_id}")
    
    # Step 2: Process email (should extract action items)
    print("⚙️ Processing email...")
    process_result = make_api_call("POST", f"/workflows/process-single-email/{email_id}")
    print_api_result("Process Email", process_result)
    
    # Step 3: Check workflow status
    print("📊 Checking workflow status...")
    status_result = make_api_call("GET", f"/emails/{email_id}/workflow-status")
    
    if status_result['success']:
        workflow_data = status_result['data']
        print(f"Action items: {workflow_data['summary']['action_items']}")
        print(f"Email processed: {workflow_data['workflow_steps']['email_processed']}")
        print(f"Action items extracted: {workflow_data['workflow_steps']['action_items_extracted']}")
    
    # Step 4: Try creating tickets
    if status_result['success'] and status_result['data']['summary']['action_items'] > 0:
        print("🎫 Creating tickets...")
        ticket_result = make_api_call("POST", "/workflows/create-tickets-from-email", {
            "email_id": email_id,
            "force_create": True
        })
        print_api_result("Create Tickets", ticket_result)
    else:
        print("❌ No action items found, cannot create tickets")
    
    return email_id

# =============================================================================
# USAGE DOCUMENTATION
# =============================================================================

def print_usage_documentation():
    """Print comprehensive usage documentation"""
    print(f"""
{'🚀 PROPERTY MANAGEMENT API EXAMPLES 🚀':=^80}

BASE URLS:
- {BASE_URL}
- http://127.0.0.1:8000/api/v1

HIGH PRIORITY ENDPOINTS (AI & WORKFLOW FOCUS):

🤖 AI RESPONSE SYSTEM:
- POST /emails/{{email_id}}/regenerate-ai-responses    # Generate AI responses
- GET  /emails/{{email_id}}/ai-responses              # View response options  
- POST /emails/{{email_id}}/ai-responses/select       # Select AI response
- GET  /emails/ai-responses/pending                   # Get pending selections
- POST /emails/bulk/generate-ai-responses             # Bulk AI generation

⚙️ WORKFLOW CONTROL:
- POST /workflows/process-emails                      # Trigger email processing
- GET  /workflows/status/{{workflow_id}}             # Monitor workflow
- POST /workflows/fetch-gmail                        # Fetch from Gmail
- POST /workflows/process-single-email/{{email_id}}  # Process single email
- GET  /workflows/health-check                       # System health

📧 EMAIL MANAGEMENT:
- GET  /emails/                                       # List emails with filters
- GET  /emails/{{email_id}}                          # Get email details
- PUT  /emails/{{email_id}}/status                   # Update email status
- POST /emails/search                                 # Search emails
- GET  /emails/analytics/summary                      # Email analytics

🎫 TICKET MANAGEMENT:
- GET  /tickets/                                      # List tickets
- GET  /tickets/{{ticket_id}}                        # Get ticket details
- PUT  /tickets/{{ticket_id}}                        # Update ticket
- GET  /tickets/stats/summary                        # Ticket statistics
- POST /tickets/batch/assign                         # Bulk assign

💾 DATABASE OPERATIONS:
- GET  /database/stats                               # Database statistics
- GET  /database/tables                              # Table information
- POST /database/emails                              # Create email
- GET  /database/search/emails                       # Search database

EXAMPLE USAGE:

1. QUICK START:
   python api_examples.py quick_start

2. AI WORKFLOW DEMO:
   python api_examples.py ai_demo

3. COMPLETE WORKFLOW:
   python api_examples.py workflow_demo

4. INTERACTIVE MODE:
   python api_examples.py interactive

5. RUN ALL TESTS:
   python api_examples.py test_suite

6. SPECIFIC EXAMPLES:
   python api_examples.py ai_priority      # AI-focused examples
   python api_examples.py workflow_priority # Workflow-focused examples
   python api_examples.py crud_examples    # CRUD operations
   python api_examples.py advanced         # Advanced scenarios

CURL EXAMPLES:

# Health Check
curl -X GET {BASE_URL}/workflows/health-check

# Create Email
curl -X POST {BASE_URL}/database/emails \\
     -H "Content-Type: application/json" \\
     -d '{{
       "sender": "test@example.com",
       "subject": "Test email",
       "body": "Test email body",
       "priority_level": "medium"
     }}'

# Generate AI Response  
curl -X POST {BASE_URL}/emails/EMAIL_ID/regenerate-ai-responses

# View AI Options
curl -X GET {BASE_URL}/emails/EMAIL_ID/ai-responses

# Select AI Response
curl -X POST {BASE_URL}/emails/EMAIL_ID/ai-responses/select \\
     -H "Content-Type: application/json" \\
     -d '{{
       "option_id": "OPTION_ID",
       "rating": 4.5
     }}'

# Get Database Stats
curl -X GET {BASE_URL}/database/stats

🎯 PRIORITY TESTING ORDER:
1. System Health Check
2. AI Response Generation & Selection
3. Workflow Processing
4. Email Management with AI
5. Ticket Creation & Management
6. Database Operations & Analytics
""")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "quick_start":
            quick_start_examples()
        elif command == "ai_demo":
            AIResponseExamples.demo_complete_ai_workflow()
        elif command == "workflow_demo":
            WorkflowExamples.demo_complete_workflow()
        elif command == "interactive":
            interactive_examples()
        elif command == "test_suite":
            run_api_testing_suite()
        elif command == "ai_priority":
            run_high_priority_ai_examples()
        elif command == "workflow_priority":
            run_high_priority_workflow_examples()
        elif command == "crud_examples":
            run_crud_operation_examples()
        elif command == "advanced":
            run_advanced_scenarios()
        elif command == "integration":
            run_complete_integration_examples()
        elif command == "help" or command == "--help":
            print_usage_documentation()
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python api_examples.py help' for usage information")
    else:
        # Default: run interactive mode
        print_usage_documentation()
        print(f"\n{'🎮 STARTING INTERACTIVE MODE 🎮':=^80}")
        interactive_examples()

if __name__ == "__main__":
    main()