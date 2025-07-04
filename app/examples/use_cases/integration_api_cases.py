#!/usr/bin/env python3
"""
UPDATED: Comprehensive API Examples for Property Management System
Focus: AI Response System & Workflow Management with Fixed PostgreSQL TinyDB
Base URL: http://localhost:8000 or http://127.0.0.1:8000

Priority Areas:
1. AI Response Generation & Selection (HIGH PRIORITY)
2. Workflow Control & Processing (HIGH PRIORITY) 
3. Email Management with AI Integration
4. Ticket Management & Creation
5. Database Operations & Analytics

UPDATED FOR:
- Fixed PostgreSQL TinyDB wrapper compatibility
- Proper ID handling (doc_ids vs custom IDs)
- Fixed bulk operations
- Updated API endpoint compatibility
"""

import requests
import json
import time
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from ...config import CONFIG
# =============================================================================
# CONFIGURATION & UTILITIES
# =============================================================================

# Updated configuration - more flexible
BASE_URL = CONFIG.base_url_interactive_cli
# Alternative: BASE_URL = "http://127.0.0.1:8000/api/v1"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Global test state
test_state = {
    "created_emails": [],
    "created_tickets": [],
    "created_workflows": [],
    "test_session_id": str(uuid.uuid4())[:8]
}

def make_api_call(method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
    """Enhanced API call with better error handling and retries"""
    url = f"{BASE_URL}/api/v1{endpoint}"
    
    # Add retry logic for transient failures
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=HEADERS, params=params, timeout=60)
            elif method.upper() == "POST":
                response = requests.post(url, headers=HEADERS, json=data, timeout=60)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=HEADERS, json=data, timeout=60)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=HEADERS, timeout=60)
            
            response.raise_for_status()
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json(),
                "url": url,
                "attempt": attempt + 1
            }
            
        except requests.exceptions.RequestException as e:
            error_detail = None
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                except:
                    error_detail = e.response.text
            
            if attempt < max_retries - 1:
                print(f"⚠️  Attempt {attempt + 1} failed, retrying in 2 seconds...")
                time.sleep(2)
                continue
            
            return {
                "success": False,
                "error": str(e),
                "error_detail": error_detail,
                "url": url,
                "attempts": attempt + 1
            }
    
    return {
        "success": False,
        "error": "Max retries exceeded",
        "url": url,
        "attempts": max_retries
    }

def print_api_result(title: str, result: Dict, show_data: bool = True):
    """Enhanced API result printer with better formatting"""
    print(f"\n{'='*70}")
    print(f"🔧 {title}")
    print(f"{'='*70}")
    print(f"URL: {result['url']}")
    
    if result['success']:
        print(f"✅ Status: {result['status_code']}")
        if result.get('attempt', 1) > 1:
            print(f"📊 Success on attempt: {result['attempt']}")
        
        if show_data and 'data' in result:
            print("📋 Response:")
            # Truncate very long responses
            data_str = json.dumps(result['data'], indent=2, default=str)
            if len(data_str) > 2000:
                print(data_str[:2000] + "\n... (truncated)")
            else:
                print(data_str)
    else:
        print(f"❌ Error: {result['error']}")
        if result.get('attempts', 1) > 1:
            print(f"📊 Failed after {result['attempts']} attempts")
        
        if result.get('error_detail'):
            print(f"📋 Details: {result['error_detail']}")

def ensure_string_id(id_value) -> str:
    """Ensure ID is a string (handles both doc_ids and custom IDs)"""
    if id_value is None:
        return ""
    return str(id_value)

def cleanup_test_data():
    """Clean up test data created during testing"""
    print(f"\n{'🧹 CLEANING UP TEST DATA 🧹':=^70}")
    
    cleanup_count = 0
    
    # Clean up created emails
    for email_id in test_state["created_emails"]:
        try:
            result = make_api_call("DELETE", f"/database/emails/{email_id}")
            if result['success']:
                cleanup_count += 1
        except Exception as e:
            print(f"⚠️  Could not delete email {email_id}: {e}")
    
    test_state["created_emails"].clear()
    
    if cleanup_count > 0:
        print(f"✅ Cleaned up {cleanup_count} test records")
    else:
        print("ℹ️  No test data to clean up")

# =============================================================================
# HIGH PRIORITY: AI RESPONSE SYSTEM EXAMPLES (UPDATED)
# =============================================================================

class AIResponseExamples:
    """Updated AI Response Generation and Management"""
    
    @staticmethod
    def create_sample_email_for_ai() -> str:
        """Create a sample email optimized for AI processing"""
        session_id = test_state["test_session_id"]
        email_data = {
            "sender": f"urgent.tenant.{session_id}@example.com",
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
            "context_labels": ["maintenance", "plumbing", "emergency", "flooding"],
            "status": "unprocessed"
        }
        
        result = make_api_call("POST", "/database/emails", email_data)
        print_api_result("Create Sample Email for AI Testing", result)
        
        if result['success']:
            email_id = ensure_string_id(result['data']['email_id'])
            test_state["created_emails"].append(email_id)
            
            # Process the email immediately to extract action items
            print(f"\n⚙️  Processing email {email_id} to extract action items...")
            process_result = make_api_call("POST", f"/workflows/process-single-email/{email_id}")
            print_api_result(f"Process Email {email_id}", process_result, show_data=False)
            
            return email_id
        return None
    
    @staticmethod
    def generate_ai_responses(email_id: str):
        """Generate AI responses for an email (UPDATED)"""
        email_id = ensure_string_id(email_id)
        result = make_api_call("POST", f"/emails/{email_id}/regenerate-ai-responses")
        print_api_result(f"Generate AI Responses for Email {email_id}", result)
        return result
    
    @staticmethod
    def view_ai_response_options(email_id: str):
        """View AI response options for an email (UPDATED)"""
        email_id = ensure_string_id(email_id)
        result = make_api_call("GET", f"/emails/{email_id}/ai-responses")
        print_api_result(f"View AI Response Options for Email {email_id}", result)
        return result
    
    @staticmethod
    def select_ai_response(email_id: str, option_id: str, rating: float = 4.5, modifications: str = None):
        """Select an AI response option (UPDATED)"""
        email_id = ensure_string_id(email_id)
        selection_data = {
            "option_id": option_id,
            "rating": rating
        }
        if modifications:
            selection_data["modifications"] = modifications
        
        result = make_api_call("POST", f"/emails/{email_id}/ai-responses/select", selection_data)
        print_api_result(f"Select AI Response for Email {email_id}", result)
        return result
    
    @staticmethod
    def get_pending_ai_responses():
        """Get all emails with pending AI response selections (UPDATED)"""
        result = make_api_call("GET", "/emails/ai-responses/pending")
        print_api_result("Get Pending AI Responses", result)
        return result
    
    @staticmethod
    def bulk_generate_ai_responses(email_ids: List[str]):
        """FIXED: Generate AI responses for multiple emails"""
        try:
            # Ensure all IDs are strings and limit to 2 for bulk testing and recommend not exceeding 3 in single worker production
            email_ids_list = [ensure_string_id(email_id) for email_id in email_ids][:2]
            
            # FIXED: Use the correct API pattern (direct list in body)
            result = make_api_call("POST", "/emails/bulk/generate-ai-responses", email_ids_list)
            print_api_result("Bulk Generate AI Responses", result)
            return result
                
        except Exception as e:
            print(f"❌ Error in bulk AI generation: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def demo_complete_ai_workflow():
        """UPDATED: Complete AI response workflow demo"""
        print(f"\n{'🤖 COMPLETE AI RESPONSE WORKFLOW DEMO 🤖':=^80}")
        
        # Step 1: Create email
        email_id = AIResponseExamples.create_sample_email_for_ai()
        if not email_id:
            print("❌ Failed to create sample email")
            return
        
        time.sleep(2)
        
        # Step 2: Generate AI responses
        ai_result = AIResponseExamples.generate_ai_responses(email_id)
        if not ai_result['success']:
            print("❌ Failed to generate AI responses")
            return
        
        time.sleep(3)
        
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

Thank you for reporting this urgent flooding issue in Unit 2B.

{first_option['content']}

We have escalated this to our emergency maintenance team and will provide immediate 24/7 support.

Emergency Contact: 555-URGENT-1
Best regards,
Property Management Team"""
            
            time.sleep(2)
            
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
                return email_id
            else:
                print("❌ Failed to select AI response")
        else:
            print("❌ No AI response options available")
            
        return None

# =============================================================================
# HIGH PRIORITY: WORKFLOW CONTROL EXAMPLES (UPDATED)
# =============================================================================

class WorkflowExamples:
    """Updated Workflow Control and Email Processing"""
    
    @staticmethod
    def trigger_complete_email_processing(auto_create_tickets: bool = True):
        """UPDATED: Trigger complete email processing workflow"""
        workflow_data = {
            "auto_replay_strategy": None,  # Don't auto-reply, let user select
            "auto_create_tickets": auto_create_tickets,
            "mark_as_read": True
        }
        
        result = make_api_call("POST", "/workflows/process-emails", workflow_data)
        print_api_result("Trigger Complete Email Processing Workflow", result)
        
        if result['success']:
            workflow_id = result['data']['workflow_id']
            test_state["created_workflows"].append(workflow_id)
            
        return result
    
    @staticmethod
    def monitor_workflow_status(workflow_id: str, max_checks: int = 15):
        """UPDATED: Monitor workflow with better error handling"""
        workflow_id = ensure_string_id(workflow_id)
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
            else:
                print(f"⚠️  Check {check + 1}: API call failed")
            
            time.sleep(3)  # Increased wait time
        
        print(f"⚠️  Workflow monitoring timed out after {max_checks} checks")
        return None
    
    @staticmethod
    def process_single_email(email_id: str):
        """UPDATED: Process a single email with proper ID handling"""
        email_id = ensure_string_id(email_id)
        result = make_api_call("POST", f"/workflows/process-single-email/{email_id}")
        print_api_result(f"Process Single Email {email_id}", result)
        return result
    
    @staticmethod
    def create_tickets_from_email(email_id: str, force_create: bool = False):
        """UPDATED: Create tickets from email with proper ID handling"""
        email_id = ensure_string_id(email_id)
        ticket_data = {
            "email_id": email_id,
            "force_create": force_create
        }
        
        result = make_api_call("POST", "/workflows/create-tickets-from-email", ticket_data)
        print_api_result(f"Create Tickets from Email {email_id}", result)
        
        if result['success'] and result['data'].get('tickets_created'):
            test_state["created_tickets"].extend(result['data']['tickets_created'])
            
        return result
    
    @staticmethod
    def check_system_health():
        """UPDATED: Enhanced system health check"""
        result = make_api_call("GET", "/workflows/health-check")
        print_api_result("Workflow System Health Check", result)
        
        if result['success']:
            components = result['data'].get('components', {})
            overall_status = result['data'].get('overall_status', 'unknown')
            
            print(f"\n📊 System Health Summary:")
            print(f"Overall Status: {overall_status}")
            for component, status in components.items():
                component_status = status.get('status', 'unknown')
                print(f"  {component}: {component_status}")
        
        return result
    
    @staticmethod
    def demo_complete_workflow():
        """UPDATED: Complete workflow processing demo"""
        print(f"\n{'⚙️ COMPLETE WORKFLOW PROCESSING DEMO ⚙️':=^80}")
        
        # Step 1: Check system health
        health_result = WorkflowExamples.check_system_health()
        if not health_result['success']:
            print("❌ System health check failed")
            return
        
        # Step 2: Trigger complete email processing
        workflow_result = WorkflowExamples.trigger_complete_email_processing(True)
        if not workflow_result['success']:
            print("❌ Failed to trigger workflow")
            return
        
        workflow_id = workflow_result['data']['workflow_id']
        print(f"🚀 Started Workflow: {workflow_id}")
        
        # Step 3: Monitor workflow progress
        final_result = WorkflowExamples.monitor_workflow_status(workflow_id)
        
        if final_result and final_result['success']:
            print("\n🎉 COMPLETE WORKFLOW PROCESSING SUCCESSFUL!")
            return workflow_id
        else:
            print("❌ Workflow did not complete successfully")
            return None

# =============================================================================
# EMAIL MANAGEMENT WITH AI INTEGRATION (UPDATED)
# =============================================================================

class EmailManagementExamples:
    """Updated Email Management with AI Integration"""
    
    @staticmethod
    def create_test_emails() -> List[str]:
        """UPDATED: Create test emails with session tracking"""
        session_id = test_state["test_session_id"]
        test_emails = [
            {
                "sender": f"alice.tenant.{session_id}@example.com",
                "subject": "Heater not working in Unit 3A",
                "body": "The heater in my apartment stopped working yesterday. It's getting very cold. Please send someone to fix it.",
                "priority_level": "high",
                "context_labels": ["maintenance", "hvac", "urgent"]
            },
            {
                "sender": f"bob.resident.{session_id}@demo.org", 
                "subject": "Question about rent payment",
                "body": "I received a late fee notice but I paid my rent on time. Can you please check my account?",
                "priority_level": "medium",
                "context_labels": ["payment", "inquiry"]
            },
            {
                "sender": f"carol.jones.{session_id}@test.net",
                "subject": "Noisy neighbors complaint",
                "body": "My upstairs neighbors are very loud at night. Music and shouting until 2 AM. This has been going on for a week.",
                "priority_level": "medium", 
                "context_labels": ["complaint", "noise", "neighbor"]
            }
        ]
        
        email_ids = []
        for i, email_data in enumerate(test_emails, 1):
            result = make_api_call("POST", "/database/emails", email_data)
            print_api_result(f"Create Test Email {i}", result, show_data=False)
            
            if result['success']:
                email_id = ensure_string_id(result['data']['email_id'])
                email_ids.append(email_id)
                test_state["created_emails"].append(email_id)
        
        return email_ids
    
    @staticmethod
    def update_email_status(email_id: str, status: str, notes: str = None):
        """UPDATED: Update email status with proper ID handling"""
        email_id = ensure_string_id(email_id)
        update_data = {"status": status}
        if notes:
            update_data["notes"] = notes
        
        result = make_api_call("PUT", f"/emails/{email_id}/status", update_data)
        print_api_result(f"Update Email Status to {status}", result)
        return result
    
    @staticmethod
    def bulk_update_email_status(email_ids: List[str], new_status: str, notes: str = None):
        """FIXED: Bulk update email status with correct API pattern"""
        try:
            # Ensure all IDs are strings
            email_ids_list = [ensure_string_id(email_id) for email_id in email_ids]
            
            # FIXED: Use the correct API pattern (all in JSON body)
            bulk_data = {
                "email_ids": email_ids_list,
                "new_status": new_status
            }
            if notes:
                bulk_data["notes"] = notes
            
            result = make_api_call("POST", "/emails/bulk/update-status", bulk_data)
            print_api_result("Bulk Update Email Status", result)
            return result
            
        except Exception as e:
            print(f"❌ Error in bulk email update: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def demo_email_management_with_ai():
        """UPDATED: Enhanced email management with AI demo"""
        print(f"\n{'📧 EMAIL MANAGEMENT WITH AI DEMO 📧':=^80}")
        
        # Step 1: Create test emails
        email_ids = EmailManagementExamples.create_test_emails()
        if not email_ids:
            print("❌ Failed to create test emails")
            return
        
        print(f"✅ Created {len(email_ids)} test emails")
        time.sleep(2)
        
        # Step 2: Process emails to extract action items
        for email_id in email_ids:
            WorkflowExamples.process_single_email(email_id)
            time.sleep(1)
        
        # Step 3: Generate AI responses for all emails
        ai_result = AIResponseExamples.bulk_generate_ai_responses(email_ids)
        if ai_result['success']:
            print(f"✅ Generated AI responses for {len(email_ids)} emails")
        
        time.sleep(3)
        
        # Step 4: Update email statuses in bulk
        bulk_update_result = EmailManagementExamples.bulk_update_email_status(
            email_ids, 
            "processing", 
            "Processed in bulk demo"
        )
        
        if bulk_update_result['success']:
            print(f"✅ Updated {bulk_update_result['data']['updated_count']} emails")
        
        # Step 5: View and select response for first email
        if email_ids:
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
        
        print("\n🎉 EMAIL MANAGEMENT WITH AI DEMO COMPLETED!")
        return email_ids

# =============================================================================
# UPDATED TESTING FUNCTIONS
# =============================================================================

def test_fixed_bulk_operations():
    """UPDATED: Test the fixed bulk operations"""
    print(f"\n{'🧪 TESTING FIXED BULK OPERATIONS 🧪':=^70}")
    
    # Create test emails
    email_ids = EmailManagementExamples.create_test_emails()
    if not email_ids:
        print("❌ No test emails created")
        return
    
    print(f"✅ Created {len(email_ids)} test emails")
    
    # Test 1: Fixed bulk AI generation
    print(f"\n🤖 Test 1: Fixed Bulk AI Generation")
    print("-" * 40)
    
    ai_result = AIResponseExamples.bulk_generate_ai_responses(email_ids)
    if ai_result['success']:
        print("✅ Bulk AI generation works!")
        processed_count = ai_result['data'].get('processed_count', 0)
        print(f"   Processed: {processed_count}/{len(email_ids)}")
    else:
        print(f"❌ Bulk AI generation failed: {ai_result.get('error', 'Unknown error')}")
    
    # Test 2: Fixed bulk status update
    print(f"\n📊 Test 2: Fixed Bulk Status Update")
    print("-" * 40)
    
    bulk_update_result = EmailManagementExamples.bulk_update_email_status(
        email_ids, 
        "processing", 
        "Fixed bulk operation test"
    )
    
    if bulk_update_result['success']:
        print("✅ Bulk status update works!")
        updated_count = bulk_update_result['data'].get('updated_count', 0)
        errors = bulk_update_result['data'].get('errors', [])
        print(f"   Updated: {updated_count}/{len(email_ids)}")
        if errors:
            print(f"   Errors: {len(errors)}")
    else:
        print(f"❌ Bulk status update failed: {bulk_update_result.get('error', 'Unknown error')}")
    
    return email_ids

def test_complete_workflow_integration():
    """UPDATED: Test complete workflow integration"""
    print(f"\n{'🔄 COMPLETE WORKFLOW INTEGRATION TEST 🔄':=^70}")
    
    # Step 1: Create and process email
    email_id = AIResponseExamples.create_sample_email_for_ai()
    if not email_id:
        print("❌ Failed to create email")
        return
    
    # Step 2: Generate AI responses
    ai_result = AIResponseExamples.generate_ai_responses(email_id)
    if not ai_result['success']:
        print("❌ Failed to generate AI responses")
        return
    
    time.sleep(3)
    
    # Step 3: Create tickets
    ticket_result = WorkflowExamples.create_tickets_from_email(email_id, True)
    if ticket_result['success']:
        tickets_created = ticket_result['data'].get('tickets_created', [])
        print(f"✅ Created {len(tickets_created)} tickets")
    
    # Step 4: Check workflow status
    status_result = make_api_call("GET", f"/emails/{email_id}/status")
    if status_result['success']:
        workflow_data = status_result['data']
        completion_pct = workflow_data.get('completion_percentage', 0)
        print(f"✅ Workflow completion: {completion_pct}%")
    
    # Step 5: Select AI response
    options_result = AIResponseExamples.view_ai_response_options(email_id)
    if options_result['success']:
        ai_responses = options_result['data'].get('ai_responses', [])
        if ai_responses and ai_responses[0].get('response_options'):
            first_option = ai_responses[0]['response_options'][0]
            select_result = AIResponseExamples.select_ai_response(
                email_id, 
                first_option['option_id'], 
                rating=5.0
            )
            if select_result['success']:
                print("✅ AI response selected successfully")
    
    print("\n🎉 COMPLETE WORKFLOW INTEGRATION TEST PASSED!")
    return email_id

def run_comprehensive_test_suite():
    """UPDATED: Run comprehensive test suite"""
    print(f"\n{'🧪 COMPREHENSIVE TEST SUITE 🧪':=^80}")
    
    test_results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": []
    }
    
    # Test categories
    test_categories = [
        {
            "name": "System Health",
            "tests": [
                ("Health Check", lambda: WorkflowExamples.check_system_health()),
                ("Database Stats", lambda: make_api_call("GET", "/database/stats")),
            ]
        },
        {
            "name": "Email Management", 
            "tests": [
                ("Create Test Emails", lambda: EmailManagementExamples.create_test_emails()),
                ("List Emails", lambda: make_api_call("GET", "/emails/", params={"limit": 5})),
            ]
        },
        {
            "name": "AI Response System",
            "tests": [
                ("Create Sample Email", lambda: AIResponseExamples.create_sample_email_for_ai()),
                ("Get Pending AI Responses", lambda: AIResponseExamples.get_pending_ai_responses()),
            ]
        },
        {
            "name": "Workflow Control",
            "tests": [
                ("Get Workflow Statuses", lambda: make_api_call("GET", "/workflows/status")),
            ]
        },
        {
            "name": "Fixed Bulk Operations",
            "tests": [
                ("Test Fixed Bulk Operations", lambda: test_fixed_bulk_operations()),
            ]
        }
    ]
    
    for category in test_categories:
        print(f"\n{'📊 ' + category['name'].upper() + ' TESTS':=^60}")
        
        for test_name, test_func in category['tests']:
            test_results["total_tests"] += 1
            
            try:
                result = test_func()
                
                # Determine success
                if isinstance(result, dict):
                    success = result.get('success', False)
                elif isinstance(result, list):
                    success = len(result) > 0
                elif isinstance(result, str):
                    success = bool(result)
                else:
                    success = result is not None
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"{test_name}: {status}")
                
                if success:
                    test_results["passed_tests"] += 1
                else:
                    test_results["failed_tests"] += 1
                
                test_results["test_details"].append({
                    "category": category['name'],
                    "test": test_name,
                    "success": success,
                    "result": result
                })
                
            except Exception as e:
                print(f"{test_name}: ❌ ERROR - {e}")
                test_results["failed_tests"] += 1
                test_results["test_details"].append({
                    "category": category['name'],
                    "test": test_name,
                    "success": False,
                    "error": str(e)
                })
    
    # Print summary
    print(f"\n{'📊 TEST RESULTS SUMMARY':=^60}")
    print(f"Total Tests: {test_results['total_tests']}")
    print(f"Passed: {test_results['passed_tests']}")
    print(f"Failed: {test_results['failed_tests']}")
    
    if test_results['total_tests'] > 0:
        success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    return test_results

# =============================================================================
# INTERACTIVE FUNCTIONS (UPDATED)
# =============================================================================

def quick_start_demo():
    """UPDATED: Quick start demo with fixed operations"""
    print(f"\n{'⚡ QUICK START DEMO ⚡':=^70}")
    
    # 1. System health check
    print("\n1️⃣ System Health Check")
    health_result = WorkflowExamples.check_system_health()
    if not health_result['success']:
        print("❌ System health check failed - stopping demo")
        return
    
    # 2. Create and process test email
    print("\n2️⃣ Create and Process Test Email")
    email_id = AIResponseExamples.create_sample_email_for_ai()
    if not email_id:
        print("❌ Failed to create email - stopping demo")
        return
    
    # 3. Generate AI responses
    print("\n3️⃣ Generate AI Responses")
    ai_result = AIResponseExamples.generate_ai_responses(email_id)
    if not ai_result['success']:
        print("❌ Failed to generate AI responses")
        return
    
    time.sleep(3)
    
    # 4. View and select AI response
    print("\n4️⃣ View and Select AI Response")
    options_result = AIResponseExamples.view_ai_response_options(email_id)
    if options_result['success']:
        ai_responses = options_result['data'].get('ai_responses', [])
        if ai_responses and ai_responses[0].get('response_options'):
            first_option = ai_responses[0]['response_options'][0]
            select_result = AIResponseExamples.select_ai_response(
                email_id, 
                first_option['option_id'], 
                rating=5.0
            )
            if select_result['success']:
                print("✅ AI response selected successfully")
    
    # 5. Create tickets
    print("\n5️⃣ Create Tickets from Email")
    ticket_result = WorkflowExamples.create_tickets_from_email(email_id, True)
    if ticket_result['success']:
        tickets_created = ticket_result['data'].get('tickets_created', [])
        print(f"✅ Created {len(tickets_created)} tickets")
    
    # 6. Final status check
    print("\n6️⃣ Final Status Check")
    stats_result = make_api_call("GET", "/database/stats")
    if stats_result['success']:
        stats = stats_result['data']
        print(f"✅ Database contains {stats.get('emails', 0)} emails, {stats.get('ai_responses', 0)} AI responses")
    
    print("\n🎉 QUICK START DEMO COMPLETED!")
    return email_id

def interactive_menu():
    """UPDATED: Enhanced interactive menu"""
    print(f"\n{'🎮 INTERACTIVE MENU 🎮':=^70}")
    
    while True:
        print("\nChoose an option:")
        print("1. Quick Start Demo (Recommended)")
        print("2. AI Response System Demo")
        print("3. Workflow Processing Demo")
        print("4. Email Management Demo")
        print("5. Test Fixed Bulk Operations")
        print("6. Complete Workflow Integration Test")
        print("7. Run Comprehensive Test Suite")
        print("8. System Health Check")
        print("9. Database Statistics")
        print("10. Clean Up Test Data")
        print("11. Exit")
        
        try:
            choice = input("\nEnter your choice (1-11): ").strip()
            
            if choice == "1":
                quick_start_demo()
            elif choice == "2":
                AIResponseExamples.demo_complete_ai_workflow()
            elif choice == "3":
                WorkflowExamples.demo_complete_workflow()
            elif choice == "4":
                EmailManagementExamples.demo_email_management_with_ai()
            elif choice == "5":
                test_fixed_bulk_operations()
            elif choice == "6":
                test_complete_workflow_integration()
            elif choice == "7":
                run_comprehensive_test_suite()
            elif choice == "8":
                WorkflowExamples.check_system_health()
            elif choice == "9":
                make_api_call("GET", "/database/stats")
            elif choice == "10":
                cleanup_test_data()
            elif choice == "11":
                cleanup_test_data()
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-11.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            cleanup_test_data()
            break
        except Exception as e:
            print(f"❌ Error: {e}")

# =============================================================================
# MAIN EXECUTION (UPDATED)
# =============================================================================

def main():
    """UPDATED: Main execution function"""
    import sys
    
    # Set up cleanup handler
    import atexit
    atexit.register(cleanup_test_data)
    
    print(f"""
{'🚀 UPDATED PROPERTY MANAGEMENT API TEST SUITE 🚀':=^80}

Base URL: {BASE_URL}
Session ID: {test_state['test_session_id']}

Updates:
✅ Fixed PostgreSQL TinyDB compatibility
✅ Fixed bulk operations (AI generation, status updates)
✅ Improved ID handling (doc_ids vs custom IDs)
✅ Enhanced error handling and retries
✅ Automatic test data cleanup
✅ Better session management
""")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "quick":
            quick_start_demo()
        elif command == "ai":
            AIResponseExamples.demo_complete_ai_workflow()
        elif command == "workflow":
            WorkflowExamples.demo_complete_workflow()
        elif command == "email":
            EmailManagementExamples.demo_email_management_with_ai()
        elif command == "bulk":
            test_fixed_bulk_operations()
        elif command == "integration":
            test_complete_workflow_integration()
        elif command == "test":
            run_comprehensive_test_suite()
        elif command == "health":
            WorkflowExamples.check_system_health()
        elif command == "clean":
            cleanup_test_data()
        elif command == "help":
            print("""
Available commands:
  quick        - Quick start demo
  ai          - AI response system demo
  workflow    - Workflow processing demo
  email       - Email management demo
  bulk        - Test fixed bulk operations
  integration - Complete workflow integration test
  test        - Run comprehensive test suite
  health      - System health check
  clean       - Clean up test data
  help        - Show this help
""")
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python script.py help' for available commands")
    else:
        # Default: run interactive menu
        interactive_menu()

if __name__ == "__main__":
    main()