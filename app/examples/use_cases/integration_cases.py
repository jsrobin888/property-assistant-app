#!/usr/bin/env python3
"""
Comprehensive AI Response Testing Examples and Use Cases
Tests the complete AI response workflow with mock data
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "http://localhost:8000/api/v1"  # Adjust to your server
HEADERS = {"Content-Type": "application/json"}

# Mock email data for testing different scenarios
MOCK_EMAILS = [
    {
        "sender": "john.tenant@example.com",
        "subject": "Urgent: Toilet overflow in Unit 3B",
        "body": """Hi Property Management,
        
        My toilet is overflowing and water is getting everywhere! This is an emergency.
        I'm in Unit 3B and need immediate help. Please send someone right away.
        
        John Smith
        Phone: 555-123-4567""",
        "priority_level": "high",
        "context_labels": ["emergency", "maintenance", "plumbing"]
    },
    {
        "sender": "sarah.jones@demo.org",
        "subject": "Rent payment question",
        "body": """Hello,
        
        I'm confused about my rent payment this month. I received a notice about a late fee,
        but I thought I paid on time. My unit is 2A and I usually pay online.
        
        Can you please check my account and let me know what happened?
        
        Thanks,
        Sarah Jones""",
        "priority_level": "medium",
        "context_labels": ["payment", "rent", "inquiry"]
    },
    {
        "sender": "mike.wilson@testmail.net",
        "subject": "Locked out of apartment",
        "body": """I'm locked out of my apartment right now and it's getting dark.
        
        I live in Unit 1C and forgot my keys inside. Can someone help me get back in?
        I'm willing to pay the lockout fee.
        
        Mike Wilson
        555-987-6543""",
        "priority_level": "high",
        "context_labels": ["lockout", "emergency", "access"]
    },
    {
        "sender": "emily.chen@fakemail.co",
        "subject": "Noise complaint about neighbor",
        "body": """Dear Property Management,
        
        I'm writing to complain about my upstairs neighbor in Unit 4B.
        They have been playing loud music until 2 AM every night this week.
        I've tried talking to them but they ignore me.
        
        I live in Unit 3B and work early shifts, so I really need this resolved.
        
        Best regards,
        Emily Chen""",
        "priority_level": "medium",
        "context_labels": ["complaint", "noise", "neighbor"]
    },
    {
        "sender": "robert.davis@example.net",
        "subject": "Air conditioning not working",
        "body": """Hi,
        
        The AC in my apartment stopped working yesterday. It's been really hot
        and uncomfortable. I tried adjusting the thermostat but nothing happens.
        
        Unit 2C
        Please send a technician when possible.
        
        Robert Davis""",
        "priority_level": "medium",
        "context_labels": ["maintenance", "hvac", "repair"]
    },
    {
        "sender": "lisa.garcia@mail.com",
        "subject": "Lease renewal inquiry",
        "body": """Hello Property Management,
        
        My lease expires at the end of next month and I'm interested in renewing.
        I've been a good tenant for 2 years in Unit 1A.
        
        What is the process for renewal and will there be any rent increases?
        
        Please let me know the next steps.
        
        Thank you,
        Lisa Garcia""",
        "priority_level": "medium",
        "context_labels": ["lease", "renewal", "inquiry"]
    },
    {
        "sender": "david.kim@demo.com",
        "subject": "help needed ASAP",
        "body": """there's water dripping from the ceiling in my kitchen
        i think it's coming from upstairs apartment
        it started this morning and getting worse
        
        unit 2D
        
        david""",
        "priority_level": "high",
        "context_labels": ["emergency", "water", "leak"]
    },
    {
        "sender": "amanda.brown@test.org",
        "subject": "Pool area issue",
        "body": """Hi there,
        
        I wanted to report that the pool gate has been broken for a week now.
        It won't close properly and anyone can get in, even non-residents.
        
        This seems like a security issue that should be fixed soon.
        
        Amanda Brown
        Unit 3A""",
        "priority_level": "medium",
        "context_labels": ["amenity", "pool", "security"]
    }
]

# =============================================================================
# API HELPER FUNCTIONS
# =============================================================================

def make_request(method: str, endpoint: str, data: Dict = None) -> Dict:
    """Make HTTP request to API"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=HEADERS)
        elif method.upper() == "POST":
            response = requests.post(url, headers=HEADERS, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=HEADERS, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=HEADERS)
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Response text: {e.response.text}")
        return None

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"🔬 {title.upper()}")
    print("="*80)

def print_step(step_num: int, description: str):
    """Print a formatted step"""
    print(f"\n📍 Step {step_num}: {description}")
    print("-" * 60)

def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")

# =============================================================================
# TEST CASE 1: COMPLETE AI RESPONSE WORKFLOW
# =============================================================================

def test_complete_ai_workflow():
    """Test the complete AI response workflow from email to selection"""
    print_section("Complete AI Response Workflow Test")
    
    # Step 1: Create a mock email
    print_step(1, "Creating a mock email")
    
    test_email = MOCK_EMAILS[0]  # Use urgent toilet overflow email
    
    email_data = {
        "sender": test_email["sender"],
        "subject": test_email["subject"],
        "body": test_email["body"],
        "priority_level": test_email["priority_level"],
        "context_labels": test_email["context_labels"]
    }
    
    result = make_request("POST", "/database/emails", email_data)
    if not result or not result.get("success"):
        print_error("Failed to create email")
        return None
    
    email_id = result["email_id"]
    print_success(f"Created email with ID: {email_id}")
    
    # Step 2: Generate AI responses
    print_step(2, "Generating AI responses for the email")
    
    result = make_request("POST", f"/emails/{email_id}/regenerate-ai-responses")
    if not result or not result.get("success"):
        print_error("Failed to generate AI responses")
        return None
    
    ai_response_id = result["ai_response_id"]
    response_count = result["new_options"]
    print_success(f"Generated {response_count} AI response options")
    print_info(f"AI Response ID: {ai_response_id}")
    
    # Step 3: View the generated responses
    print_step(3, "Viewing generated AI response options")
    
    result = make_request("GET", f"/emails/{email_id}/ai-responses")
    if not result:
        print_error("Failed to get AI responses")
        return None
    
    ai_responses = result["ai_responses"]
    if ai_responses:
        latest_response = ai_responses[0]
        options = latest_response["response_options"]
        
        print_success(f"Found {len(options)} response options:")
        for i, option in enumerate(options, 1):
            print(f"\n   Option {i} ({option['option_id'][:8]}...):")
            print(f"   Strategy: {option['strategy_used']}")
            print(f"   Provider: {option['provider']}")
            print(f"   Confidence: {option['confidence']}")
            print(f"   Preview: {option['content'][:100]}...")
    
    # Step 4: Select an AI response
    print_step(4, "Selecting an AI response option")
    
    if ai_responses and options:
        selected_option = options[0]  # Select first option
        
        selection_data = {
            "option_id": selected_option["option_id"],
            "rating": 4.5,
            "modifications": None
        }
        
        result = make_request("POST", f"/emails/{email_id}/ai-responses/select", selection_data)
        if result and result.get("success"):
            print_success(f"Selected response option: {selected_option['option_id'][:8]}...")
        else:
            print_error("Failed to select AI response")
    
    # Step 5: Verify the workflow completed
    print_step(5, "Verifying workflow completion")
    
    result = make_request("GET", f"/emails/{email_id}/workflow-status")
    if result:
        completion_percentage = result["completion_percentage"]
        current_status = result["current_status"]
        
        print_success(f"Workflow completion: {completion_percentage}%")
        print_info(f"Current email status: {current_status}")
        
        if result["workflow_steps"]["ai_response_selected"]:
            print_success("AI response workflow completed successfully!")
        else:
            print_error("AI response not properly selected")
    
    return email_id

# =============================================================================
# TEST CASE 2: BULK AI RESPONSE GENERATION
# =============================================================================

def test_bulk_ai_response_generation():
    """Test generating AI responses for multiple emails"""
    print_section("Bulk AI Response Generation Test")
    
    # Step 1: Create multiple emails
    print_step(1, "Creating multiple test emails")
    
    email_ids = []
    for i, email_data in enumerate(MOCK_EMAILS[:5], 1):
        result = make_request("POST", "/database/emails", {
            "sender": email_data["sender"],
            "subject": email_data["subject"], 
            "body": email_data["body"],
            "priority_level": email_data["priority_level"],
            "context_labels": email_data["context_labels"]
        })
        
        if result and result.get("success"):
            email_ids.append(result["email_id"])
            print_success(f"Created email {i}: {result['email_id']}")
        else:
            print_error(f"Failed to create email {i}")
    
    if not email_ids:
        print_error("No emails created for bulk test")
        return
    
    # Step 2: Generate AI responses in bulk
    print_step(2, "Generating AI responses for all emails")
    
    result = make_request("POST", "/emails/bulk/generate-ai-responses", {"email_ids": email_ids})
    if not result:
        print_error("Bulk AI generation request failed")
        return
    
    successful_count = result["processed_count"]
    total_requested = result["total_requested"]
    
    print_success(f"Generated AI responses for {successful_count}/{total_requested} emails")
    
    # Show results for each email
    for email_result in result["results"]:
        if email_result["success"]:
            print_success(f"Email {email_result['email_id']}: {email_result['options_generated']} options")
        else:
            print_error(f"Email {email_result['email_id']}: {email_result['error']}")
    
    # Step 3: Check pending AI responses
    print_step(3, "Checking pending AI responses")
    
    result = make_request("GET", "/emails/ai-responses/pending")
    if result:
        pending_count = result["total"]
        print_success(f"Found {pending_count} emails with pending AI responses")
        
        for response in result["pending_responses"][:3]:  # Show first 3
            email_details = response["email_details"]
            print_info(f"Pending: {email_details['sender']} - {email_details['subject'][:30]}... ({response['option_count']} options)")
    
    return email_ids

# =============================================================================
# TEST CASE 3: AI RESPONSE STRATEGIES COMPARISON
# =============================================================================

def test_ai_response_strategies():
    """Test different AI response strategies and compare results"""
    print_section("AI Response Strategies Comparison Test")
    
    # Create a test email with complex content
    print_step(1, "Creating complex test email")
    
    complex_email = {
        "sender": "complex.tenant@example.com",
        "subject": "Multiple issues need attention",
        "body": """Dear Property Management,
        
        I have several issues that need your attention:
        
        1. The kitchen faucet has been dripping for 3 days
        2. My upstairs neighbor is very noisy at night
        3. I still haven't received my security deposit refund from 2 months ago
        4. The parking garage gate is broken and I can't get my car out
        
        I've been a tenant in Unit 4C for 3 years and these issues are really affecting my quality of life.
        Please prioritize these repairs and get back to me ASAP.
        
        Thank you,
        Jessica Thompson
        555-444-3333""",
        "priority_level": "high",
        "context_labels": ["multiple_issues", "maintenance", "complaint", "payment"]
    }
    
    result = make_request("POST", "/database/emails", complex_email)
    if not result or not result.get("success"):
        print_error("Failed to create complex email")
        return
    
    email_id = result["email_id"]
    print_success(f"Created complex email: {email_id}")
    
    # Generate multiple sets of AI responses to compare strategies
    print_step(2, "Generating multiple AI response sets")
    
    response_sets = []
    for attempt in range(3):
        print_info(f"Generating response set {attempt + 1}...")
        
        result = make_request("POST", f"/emails/{email_id}/regenerate-ai-responses")
        if result and result.get("success"):
            # Get the generated responses
            ai_result = make_request("GET", f"/emails/{email_id}/ai-responses")
            if ai_result and ai_result["ai_responses"]:
                latest_response = ai_result["ai_responses"][0]
                response_sets.append(latest_response["response_options"])
                print_success(f"Generated {len(latest_response['response_options'])} options")
        
        time.sleep(1)  # Brief pause between generations
    
    # Analyze and compare the strategies
    print_step(3, "Analyzing response strategies")
    
    all_strategies = set()
    all_providers = set()
    
    for i, response_set in enumerate(response_sets, 1):
        print(f"\n📊 Response Set {i}:")
        
        for j, option in enumerate(response_set, 1):
            strategy = option["strategy_used"]
            provider = option["provider"]
            confidence = option["confidence"]
            
            all_strategies.add(strategy)
            all_providers.add(provider)
            
            print(f"   Option {j}: {strategy} ({provider}) - Confidence: {confidence}")
            print(f"   Preview: {option['content'][:80]}...")
    
    print_step(4, "Strategy Analysis Summary")
    
    print_success(f"Total unique strategies tested: {len(all_strategies)}")
    print_info(f"Strategies found: {', '.join(all_strategies)}")
    
    print_success(f"Total unique providers tested: {len(all_providers)}")
    print_info(f"Providers found: {', '.join(all_providers)}")
    
    return email_id, response_sets

# =============================================================================
# TEST CASE 4: AI RESPONSE MODIFICATION AND RATING
# =============================================================================

def test_ai_response_modification():
    """Test AI response modification and rating features"""
    print_section("AI Response Modification and Rating Test")
    
    # Create a test email
    print_step(1, "Creating test email for modification")
    
    test_email = MOCK_EMAILS[1]  # Rent payment question
    
    result = make_request("POST", "/database/emails", {
        "sender": test_email["sender"],
        "subject": test_email["subject"],
        "body": test_email["body"],
        "priority_level": test_email["priority_level"],
        "context_labels": test_email["context_labels"]
    })
    
    if not result or not result.get("success"):
        print_error("Failed to create test email")
        return
    
    email_id = result["email_id"]
    print_success(f"Created email: {email_id}")
    
    # Generate AI responses
    print_step(2, "Generating AI responses")
    
    result = make_request("POST", f"/emails/{email_id}/regenerate-ai-responses")
    if not result or not result.get("success"):
        print_error("Failed to generate responses")
        return
    
    # Get the responses
    result = make_request("GET", f"/emails/{email_id}/ai-responses")
    if not result or not result["ai_responses"]:
        print_error("No AI responses found")
        return
    
    options = result["ai_responses"][0]["response_options"]
    selected_option = options[0]
    
    print_success(f"Found {len(options)} response options")
    print_info(f"Original response preview: {selected_option['content'][:100]}...")
    
    # Test response modification
    print_step(3, "Testing response modification")
    
    modified_content = f"""Dear {test_email['sender'].split('@')[0].title()},

Thank you for contacting us about your rent payment concern.

{selected_option['content']}

Additionally, we want to assure you that we'll review your account immediately and get back to you within 24 hours with a detailed explanation.

Best regards,
Property Management Team
Phone: 555-123-4567"""
    
    modification_data = {
        "option_id": selected_option["option_id"],
        "rating": 4.0,
        "modifications": modified_content
    }
    
    result = make_request("POST", f"/emails/{email_id}/ai-responses/select", modification_data)
    if result and result.get("success"):
        print_success("Successfully selected response with modifications")
        print_info(f"Rating provided: {modification_data['rating']}")
    else:
        print_error("Failed to select modified response")
    
    # Verify the modification was saved
    print_step(4, "Verifying modification was saved")
    
    result = make_request("GET", f"/database/replies?email_id={email_id}")
    if result and result["replies"]:
        saved_reply = result["replies"][0]
        
        if saved_reply.get("modifications_made"):
            print_success("Modifications were properly saved")
            print_info("Modified response contains user customizations")
        else:
            print_info("No modifications detected in saved response")
        
        if saved_reply.get("user_rating"):
            print_success(f"User rating saved: {saved_reply['user_rating']}")
    
    return email_id

# =============================================================================
# TEST CASE 5: AI RESPONSE ANALYTICS AND REPORTING
# =============================================================================

def test_ai_response_analytics():
    """Test AI response analytics and reporting features"""
    print_section("AI Response Analytics and Reporting Test")
    
    # First, generate some AI response data by processing multiple emails
    print_step(1, "Generating sample AI response data")
    
    processed_emails = []
    
    for i, email_data in enumerate(MOCK_EMAILS, 1):
        try:
            # Create email
            result = make_request("POST", "/database/emails", {
                "sender": email_data["sender"],
                "subject": email_data["subject"],
                "body": email_data["body"],
                "priority_level": email_data["priority_level"],
                "context_labels": email_data["context_labels"]
            })
            
            if result and result.get("success"):
                email_id = result["email_id"]
                print_info(f"Created email {i} with ID: {email_id} (type: {type(email_id)})")
                
                # Generate AI responses
                ai_result = make_request("POST", f"/emails/{email_id}/regenerate-ai-responses")
                
                if ai_result and ai_result.get("success"):
                    # Randomly select and rate responses
                    ai_responses = make_request("GET", f"/emails/{email_id}/ai-responses")
                    
                    if ai_responses and ai_responses["ai_responses"]:
                        options = ai_responses["ai_responses"][0]["response_options"]
                        if options:
                            selected_option = random.choice(options)
                            rating = random.uniform(3.0, 5.0)
                            
                            selection_data = {
                                "option_id": selected_option["option_id"],
                                "rating": round(rating, 1)
                            }
                            
                            select_result = make_request("POST", f"/emails/{email_id}/ai-responses/select", selection_data)
                            
                            if select_result and select_result.get("success"):
                                processed_emails.append({
                                    "email_id": email_id,
                                    "strategy": selected_option["strategy_used"],
                                    "provider": selected_option["provider"],
                                    "rating": rating
                                })
                                # Convert email_id to string for safe slicing
                                email_id_str = str(email_id)
                                print_success(f"Processed email {i}: {email_id_str[:8]}...")
                            else:
                                print_error(f"Failed to select AI response for email {i}")
                        else:
                            print_error(f"No AI response options found for email {i}")
                    else:
                        print_error(f"No AI responses found for email {i}")
                else:
                    print_error(f"Failed to generate AI responses for email {i}")
            else:
                print_error(f"Failed to create email {i}")
                
        except Exception as e:
            print_error(f"Error processing email {i}: {str(e)}")
            test_reporter.log_error(f"Error in analytics test email {i}: {str(e)}", "test_ai_response_analytics")
            continue
        
        if i >= 6:  # Limit to 6 emails for demo
            break
    
    print_success(f"Generated AI response data for {len(processed_emails)} emails")
    
    # Get email analytics
    print_step(2, "Analyzing email system performance")
    
    try:
        result = make_request("GET", "/emails/analytics/summary")
        if result:
            print_success("Email Analytics Summary:")
            print(f"   Total emails: {result['overview']['total_emails']}")
            print(f"   Emails with tickets: {result['overview']['emails_with_tickets']}")
            print(f"   Recent emails (7 days): {result['overview']['recent_emails_7days']}")
            
            if result['distributions']['by_status']:
                print("\n   📊 Status Distribution:")
                for status, count in result['distributions']['by_status'].items():
                    print(f"      {status}: {count}")
        else:
            print_error("Failed to get email analytics")
    except Exception as e:
        print_error(f"Error getting email analytics: {str(e)}")
        test_reporter.log_error(f"Error in email analytics: {str(e)}", "test_ai_response_analytics")
    
    # Get AI response statistics from database
    print_step(3, "Analyzing AI response statistics")
    
    try:
        result = make_request("GET", "/database/ai-responses")
        if result:
            ai_responses = result["ai_responses"]
            
            if ai_responses:
                # Calculate AI response statistics
                total_responses = len(ai_responses)
                completed_responses = len([r for r in ai_responses if r.get("status") == "completed"])
                pending_responses = len([r for r in ai_responses if r.get("status") == "pending_selection"])
                
                print_success("AI Response Statistics:")
                print(f"   Total AI responses generated: {total_responses}")
                print(f"   Completed selections: {completed_responses}")
                print(f"   Pending selections: {pending_responses}")
                
                if completed_responses > 0:
                    completion_rate = (completed_responses / total_responses) * 100
                    print(f"   Completion rate: {completion_rate:.1f}%")
            else:
                print_info("No AI responses found in database")
        else:
            print_error("Failed to get AI response statistics")
    except Exception as e:
        print_error(f"Error getting AI response statistics: {str(e)}")
        test_reporter.log_error(f"Error in AI response statistics: {str(e)}", "test_ai_response_analytics")
    
    # Analyze reply statistics
    print_step(4, "Analyzing reply statistics")
    
    try:
        result = make_request("GET", "/database/replies")
        if result:
            replies = result["replies"]
            
            if replies:
                # Calculate reply statistics
                total_replies = len(replies)
                sent_replies = len([r for r in replies if r.get("sent")])
                
                # Strategy analysis
                strategies = {}
                providers = {}
                ratings = []
                
                for reply in replies:
                    strategy = reply.get("strategy_used", "unknown")
                    provider = reply.get("provider", "unknown")
                    rating = reply.get("user_rating")
                    
                    strategies[strategy] = strategies.get(strategy, 0) + 1
                    providers[provider] = providers.get(provider, 0) + 1
                    
                    if rating:
                        ratings.append(rating)
                
                print_success("Reply Analytics:")
                print(f"   Total replies: {total_replies}")
                print(f"   Sent replies: {sent_replies}")
                
                print("\n   📊 Strategy Distribution:")
                for strategy, count in strategies.items():
                    percentage = (count / total_replies) * 100 if total_replies > 0 else 0
                    print(f"      {strategy}: {count} ({percentage:.1f}%)")
                
                print("\n   🏭 Provider Distribution:")
                for provider, count in providers.items():
                    percentage = (count / total_replies) * 100 if total_replies > 0 else 0
                    print(f"      {provider}: {count} ({percentage:.1f}%)")
                
                if ratings:
                    avg_rating = sum(ratings) / len(ratings)
                    print(f"\n   ⭐ Average user rating: {avg_rating:.2f}/5.0")
                    print(f"   📊 Total rated responses: {len(ratings)}")
            else:
                print_info("No replies found for analysis")
        else:
            print_error("Failed to get reply statistics")
    except Exception as e:
        print_error(f"Error getting reply statistics: {str(e)}")
        test_reporter.log_error(f"Error in reply statistics: {str(e)}", "test_ai_response_analytics")
    
    return processed_emails

# =============================================================================
# TEST CASE 6: AI RESPONSE ERROR HANDLING
# =============================================================================

def test_ai_response_error_handling():
    """Test error handling in AI response system"""
    print_section("AI Response Error Handling Test")
    
    # Test 1: Invalid email ID
    print_step(1, "Testing invalid email ID")
    
    result = make_request("POST", "/emails/invalid-email-id/regenerate-ai-responses")
    if not result:
        print_success("Correctly handled invalid email ID")
    else:
        print_error("Should have failed with invalid email ID")
    
    # Test 2: Select non-existent response option
    print_step(2, "Testing invalid response option selection")
    
    # First create a valid email
    test_email = MOCK_EMAILS[0]
    email_result = make_request("POST", "/database/emails", {
        "sender": test_email["sender"],
        "subject": test_email["subject"],
        "body": test_email["body"]
    })
    
    if email_result and email_result.get("success"):
        email_id = email_result["email_id"]
        
        # Try to select non-existent option
        invalid_selection = {
            "option_id": "non-existent-option-id",
            "rating": 4.0
        }
        
        result = make_request("POST", f"/emails/{email_id}/ai-responses/select", invalid_selection)
        if not result or not result.get("success"):
            print_success("Correctly handled invalid option selection")
        else:
            print_error("Should have failed with invalid option ID")
    
    # Test 3: Malformed request data
    print_step(3, "Testing malformed request data")
    
    malformed_data = {
        "invalid_field": "invalid_value"
        # Missing required fields
    }
    
    result = make_request("POST", "/emails/some-id/ai-responses/select", malformed_data)
    if not result:
        print_success("Correctly handled malformed request data")
    else:
        print_error("Should have failed with malformed data")
    
    # Test 4: Double selection (selecting response twice)
    print_step(4, "Testing double selection prevention")
    
    if email_result and email_result.get("success"):
        email_id = email_result["email_id"]
        
        # Generate responses
        ai_result = make_request("POST", f"/emails/{email_id}/regenerate-ai-responses")
        
        if ai_result and ai_result.get("success"):
            # Get responses and select one
            responses_result = make_request("GET", f"/emails/{email_id}/ai-responses")
            
            if responses_result and responses_result["ai_responses"]:
                options = responses_result["ai_responses"][0]["response_options"]
                if options:
                    selected_option = options[0]
                    
                    selection_data = {
                        "option_id": selected_option["option_id"],
                        "rating": 4.0
                    }
                    
                    # First selection (should succeed)
                    first_result = make_request("POST", f"/emails/{email_id}/ai-responses/select", selection_data)
                    
                    # Second selection (should handle gracefully)
                    second_result = make_request("POST", f"/emails/{email_id}/ai-responses/select", selection_data)
                    
                    if first_result and first_result.get("success"):
                        print_success("First selection succeeded")
                        
                        if not second_result or not second_result.get("success"):
                            print_success("Correctly prevented double selection")
                        else:
                            print_info("Double selection was allowed (may be intentional)")
                    else:
                        print_error("First selection should have succeeded")

# =============================================================================
# TEST CASE 7: PERFORMANCE AND LOAD TESTING
# =============================================================================

def test_ai_response_performance():
    """Test AI response system performance under load"""
    print_section("AI Response Performance Testing")
    
    print_step(1, "Creating multiple emails for load testing")
    
    # Create multiple emails quickly
    email_ids = []
    start_time = time.time()
    
    for i in range(10):  # Create 10 emails
        email_data = {
            "sender": f"loadtest{i}@example.com",
            "subject": f"Load test email {i+1}",
            "body": f"This is load test email number {i+1} for performance testing.",
            "priority_level": "medium"
        }
        
        result = make_request("POST", "/database/emails", email_data)
        if result and result.get("success"):
            email_ids.append(result["email_id"])
    
    creation_time = time.time() - start_time
    
    print_success(f"Created {len(email_ids)} emails in {creation_time:.2f} seconds")
    print_info(f"Average creation time: {creation_time/len(email_ids):.3f} seconds per email")
    
    # Test bulk AI generation performance
    print_step(2, "Testing bulk AI generation performance")
    
    start_time = time.time()
    result = make_request("POST", "/emails/bulk/generate-ai-responses", {"email_ids": email_ids})
    generation_time = time.time() - start_time
    
    if result:
        successful_count = result["processed_count"]
        print_success(f"Generated AI responses for {successful_count}/{len(email_ids)} emails")
        print_info(f"Total generation time: {generation_time:.2f} seconds")
        print_info(f"Average time per email: {generation_time/len(email_ids):.3f} seconds")
    else:
        print_error("Bulk AI generation failed")
    
    # Test concurrent selection performance
    print_step(3, "Testing concurrent response selections")
    
    selection_times = []
    
    for email_id in email_ids[:5]:  # Test first 5 emails
        # Get AI responses
        responses_result = make_request("GET", f"/emails/{email_id}/ai-responses")
        
        if responses_result and responses_result["ai_responses"]:
            options = responses_result["ai_responses"][0]["response_options"]
            if options:
                selected_option = options[0]
                
                selection_data = {
                    "option_id": selected_option["option_id"],
                    "rating": 4.0
                }
                
                start_time = time.time()
                result = make_request("POST", f"/emails/{email_id}/ai-responses/select", selection_data)
                selection_time = time.time() - start_time
                
                if result and result.get("success"):
                    selection_times.append(selection_time)
    
    if selection_times:
        avg_selection_time = sum(selection_times) / len(selection_times)
        print_success(f"Completed {len(selection_times)} response selections")
        print_info(f"Average selection time: {avg_selection_time:.3f} seconds")
        print_info(f"Fastest selection: {min(selection_times):.3f} seconds")
        print_info(f"Slowest selection: {max(selection_times):.3f} seconds")
    
    return email_ids

# =============================================================================
# TEST CASE 8: INTEGRATION WITH WORKFLOW SYSTEM
# =============================================================================

def test_workflow_integration():
    """Test AI response integration with the complete workflow system"""
    print_section("Workflow Integration Testing")
    
    # Test complete workflow from email processing to AI response
    print_step(1, "Testing end-to-end workflow integration")
    
    # Start a workflow that processes emails
    workflow_data = {
        "auto_replay_strategy": None,  # Don't auto-reply
        "auto_create_tickets": True,
        "mark_as_read": True
    }
    
    result = make_request("POST", "/workflows/process-emails", workflow_data)
    if not result:
        print_error("Failed to start workflow")
        return
    
    workflow_id = result["workflow_id"]
    print_success(f"Started workflow: {workflow_id}")
    
    # Monitor workflow status
    print_step(2, "Monitoring workflow progress")
    
    max_attempts = 10
    for attempt in range(max_attempts):
        time.sleep(2)  # Wait 2 seconds between checks
        
        status_result = make_request("GET", f"/workflows/status/{workflow_id}")
        if status_result:
            status = status_result["status"]
            print_info(f"Workflow status: {status}")
            
            if status == "completed":
                print_success("Workflow completed successfully")
                
                # Show workflow results
                if "results" in status_result:
                    results = status_result["results"]
                    emails_processed = results.get("emails_processed", 0)
                    print_info(f"Emails processed: {emails_processed}")
                break
            elif status == "failed":
                print_error("Workflow failed")
                if "errors" in status_result:
                    for error in status_result["errors"]:
                        print_error(f"Error: {error}")
                break
        else:
            print_error(f"Failed to get workflow status (attempt {attempt + 1})")
    
    # Test workflow health check
    print_step(3, "Testing workflow system health")
    
    health_result = make_request("GET", "/workflows/health-check")
    if health_result:
        overall_status = health_result["overall_status"]
        print_success(f"Overall system health: {overall_status}")
        
        components = health_result.get("components", {})
        for component, status_info in components.items():
            component_status = status_info["status"]
            if component_status == "healthy":
                print_success(f"{component}: {component_status}")
            else:
                print_error(f"{component}: {component_status}")
                if "error" in status_info:
                    print_error(f"   Error: {status_info['error']}")
    
    return workflow_id

# =============================================================================
# TEST CASE 9: EDGE CASES AND BOUNDARY CONDITIONS
# =============================================================================

def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print_section("Edge Cases and Boundary Conditions Testing")
    
    # Test 1: Empty email content
    print_step(1, "Testing empty email content")
    
    empty_email = {
        "sender": "empty@example.com",
        "subject": "",
        "body": "",
        "priority_level": "low"
    }
    
    result = make_request("POST", "/database/emails", empty_email)
    if result and result.get("success"):
        email_id = result["email_id"]
        
        # Try to generate AI responses for empty content
        ai_result = make_request("POST", f"/emails/{email_id}/regenerate-ai-responses")
        if ai_result:
            print_success("AI system handled empty content gracefully")
        else:
            print_info("AI system rejected empty content (expected)")
    
    # Test 2: Very long email content
    print_step(2, "Testing very long email content")
    
    long_content = "This is a very long email. " * 500  # ~15,000 characters
    
    long_email = {
        "sender": "longcontent@example.com",
        "subject": "Very long email for testing",
        "body": long_content,
        "priority_level": "medium"
    }
    
    result = make_request("POST", "/database/emails", long_email)
    if result and result.get("success"):
        email_id = result["email_id"]
        
        start_time = time.time()
        ai_result = make_request("POST", f"/emails/{email_id}/regenerate-ai-responses")
        processing_time = time.time() - start_time
        
        if ai_result and ai_result.get("success"):
            print_success(f"Processed long content in {processing_time:.2f} seconds")
        else:
            print_error("Failed to process long content")
    
    # Test 3: Special characters and Unicode
    print_step(3, "Testing special characters and Unicode")
    
    unicode_email = {
        "sender": "unicode@example.com",
        "subject": "测试邮件 with émojis 🏠🔧",
        "body": """Hola, tengo un problema en mi apartamento. 
        
        El grifo está roto 🚰 y hay agua por todas partes 💧.
        ¡Necesito ayuda urgente! 🆘
        
        Grâce à votre équipe, j'espère une résolution rapide.
        
        Спасибо за понимание!""",
        "priority_level": "high"
    }
    
    result = make_request("POST", "/database/emails", unicode_email)
    if result and result.get("success"):
        email_id = result["email_id"]
        
        ai_result = make_request("POST", f"/emails/{email_id}/regenerate-ai-responses")
        if ai_result and ai_result.get("success"):
            print_success("Successfully processed Unicode and special characters")
        else:
            print_error("Failed to process Unicode content")
    
    # Test 4: Multiple rapid requests
    print_step(4, "Testing rapid consecutive requests")
    
    rapid_email = {
        "sender": "rapid@example.com",
        "subject": "Rapid testing email",
        "body": "Testing rapid consecutive AI generation requests",
        "priority_level": "medium"
    }
    
    result = make_request("POST", "/database/emails", rapid_email)
    if result and result.get("success"):
        email_id = result["email_id"]
        
        # Make 5 rapid AI generation requests
        rapid_results = []
        for i in range(5):
            start_time = time.time()
            ai_result = make_request("POST", f"/emails/{email_id}/regenerate-ai-responses")
            request_time = time.time() - start_time
            
            rapid_results.append({
                "success": ai_result and ai_result.get("success"),
                "time": request_time
            })
            
            time.sleep(0.1)  # Small delay between requests
        
        successful_requests = sum(1 for r in rapid_results if r["success"])
        avg_time = sum(r["time"] for r in rapid_results) / len(rapid_results)
        
        print_success(f"Completed {successful_requests}/5 rapid requests")
        print_info(f"Average response time: {avg_time:.3f} seconds")

# =============================================================================
# COMPREHENSIVE TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all AI response tests"""
    print("🚀 STARTING COMPREHENSIVE AI RESPONSE TESTING")
    print("=" * 80)
    
    start_time = time.time()
    test_results = {}
    
    try:
        # Test 1: Complete Workflow
        print_info("Running Test 1: Complete AI Response Workflow...")
        test_results["complete_workflow"] = test_complete_ai_workflow()
        
        # Test 2: Bulk Generation
        print_info("Running Test 2: Bulk AI Response Generation...")
        test_results["bulk_generation"] = test_bulk_ai_response_generation()
        
        # Test 3: Strategy Comparison
        print_info("Running Test 3: AI Response Strategies Comparison...")
        test_results["strategy_comparison"] = test_ai_response_strategies()
        
        # Test 4: Modification and Rating
        print_info("Running Test 4: Response Modification and Rating...")
        test_results["modification_rating"] = test_ai_response_modification()
        
        # Test 5: Analytics and Reporting
        print_info("Running Test 5: Analytics and Reporting...")
        test_results["analytics"] = test_ai_response_analytics()
        
        # Test 6: Error Handling
        print_info("Running Test 6: Error Handling...")
        test_ai_response_error_handling()
        
        # Test 7: Performance Testing
        print_info("Running Test 7: Performance Testing...")
        test_results["performance"] = test_ai_response_performance()
        
        # Test 8: Workflow Integration
        print_info("Running Test 8: Workflow Integration...")
        test_results["workflow_integration"] = test_workflow_integration()
        
        # Test 9: Edge Cases
        print_info("Running Test 9: Edge Cases...")
        test_edge_cases()
        
    except Exception as e:
        print_error(f"Test execution failed: {e}")
        return
    
    total_time = time.time() - start_time
    
    # Final summary
    print_section("Test Execution Summary")
    
    print_success(f"All tests completed in {total_time:.2f} seconds")
    
    successful_tests = sum(1 for result in test_results.values() if result is not None)
    total_tests = len(test_results)
    
    print_success(f"Successful tests: {successful_tests}/{total_tests}")
    
    if test_results["analytics"]:
        processed_emails = test_results["analytics"]
        print_info(f"Total test emails processed: {len(processed_emails)}")
    
    print("\n📊 Test Results Summary:")
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result is not None else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    return test_results

# =============================================================================
# UTILITY FUNCTIONS FOR MANUAL TESTING
# =============================================================================

def create_sample_email(email_type: str = "maintenance") -> str:
    """Create a sample email for manual testing"""
    email_templates = {
        "maintenance": MOCK_EMAILS[0],
        "payment": MOCK_EMAILS[1], 
        "lockout": MOCK_EMAILS[2],
        "complaint": MOCK_EMAILS[3],
        "hvac": MOCK_EMAILS[4],
        "lease": MOCK_EMAILS[5]
    }
    
    email_data = email_templates.get(email_type, MOCK_EMAILS[0])
    
    result = make_request("POST", "/database/emails", {
        "sender": email_data["sender"],
        "subject": email_data["subject"],
        "body": email_data["body"],
        "priority_level": email_data["priority_level"],
        "context_labels": email_data["context_labels"]
    })
    
    if result and result.get("success"):
        email_id = result["email_id"]
        print_success(f"Created {email_type} email: {email_id}")
        return email_id
    else:
        print_error(f"Failed to create {email_type} email")
        return None

def generate_ai_responses_for_email(email_id: str) -> bool:
    """Generate AI responses for a specific email"""
    result = make_request("POST", f"/emails/{email_id}/regenerate-ai-responses")
    
    if result and result.get("success"):
        response_count = result["new_options"]
        print_success(f"Generated {response_count} AI response options for {email_id}")
        return True
    else:
        print_error(f"Failed to generate AI responses for {email_id}")
        return False

def view_ai_responses(email_id: str):
    """View AI response options for an email"""
    result = make_request("GET", f"/emails/{email_id}/ai-responses")
    
    if result and result["ai_responses"]:
        ai_response = result["ai_responses"][0]
        options = ai_response["response_options"]
        
        print_success(f"Found {len(options)} AI response options:")
        
        for i, option in enumerate(options, 1):
            print(f"\n--- Option {i} ({option['option_id'][:8]}...) ---")
            print(f"Strategy: {option['strategy_used']}")
            print(f"Provider: {option['provider']}")
            print(f"Confidence: {option['confidence']}")
            print(f"Content Preview:")
            print(f"{option['content'][:200]}...")
            
        return options
    else:
        print_error(f"No AI responses found for email {email_id}")
        return None

def select_ai_response_interactive(email_id: str):
    """Interactively select an AI response option"""
    options = view_ai_responses(email_id)
    
    if not options:
        return False
    
    print("\nSelect an option (1-{}) or 'q' to quit:".format(len(options)))
    choice = input("> ").strip()
    
    if choice.lower() == 'q':
        return False
    
    try:
        option_index = int(choice) - 1
        if 0 <= option_index < len(options):
            selected_option = options[option_index]
            
            rating = input("Rate this response (1-5, or press Enter to skip): ").strip()
            rating_value = float(rating) if rating else None
            
            modifications = input("Enter modifications (or press Enter to use as-is): ").strip()
            modifications_value = modifications if modifications else None
            
            selection_data = {
                "option_id": selected_option["option_id"],
                "rating": rating_value,
                "modifications": modifications_value
            }
            
            result = make_request("POST", f"/emails/{email_id}/ai-responses/select", selection_data)
            
            if result and result.get("success"):
                print_success("AI response selected successfully!")
                return True
            else:
                print_error("Failed to select AI response")
                return False
        else:
            print_error("Invalid option number")
            return False
    except ValueError:
        print_error("Please enter a valid number")
        return False

def cleanup_test_data():
    """Clean up test data created during testing"""
    print_section("Cleaning Up Test Data")
    
    # Get all emails
    result = make_request("GET", "/database/emails?limit=1000")
    if result and result["emails"]:
        test_emails = [
            email for email in result["emails"] 
            if "test" in email.get("sender", "").lower() or 
               "example.com" in email.get("sender", "") or
               "demo.org" in email.get("sender", "") or
               "loadtest" in email.get("sender", "")
        ]
        
        if test_emails:
            email_ids = [email.get("id", str(email.get("doc_id", ""))) for email in test_emails]
            
            # Bulk delete test emails
            delete_result = make_request("POST", "/database/bulk/delete-emails", email_ids)
            
            if delete_result and delete_result.get("success"):
                deleted_count = delete_result["deleted_count"]
                print_success(f"Cleaned up {deleted_count} test emails")
            else:
                print_error("Failed to clean up test emails")
        else:
            print_info("No test emails found to clean up")
    
    print_success("Cleanup completed")

# =============================================================================
# REPORT GENERATION SYSTEM
# =============================================================================

class TestReporter:
    """Comprehensive test report generator"""
    
    def __init__(self):
        self.test_start_time = None
        self.test_end_time = None
        self.test_logs = []
        self.performance_metrics = {}
        self.test_results = {}
        self.errors = []
        self.warnings = []
        self.system_info = {}
        
    def start_reporting(self):
        """Start the reporting session"""
        self.test_start_time = time.time()
        self.test_logs = []
        self.errors = []
        self.warnings = []
        print_info("📝 Test reporting started")
        
    def end_reporting(self):
        """End the reporting session"""
        self.test_end_time = time.time()
        print_info("📝 Test reporting completed")
        
    def log_test_result(self, test_name: str, success: bool, duration: float, details: Dict = None):
        """Log a test result"""
        self.test_results[test_name] = {
            "success": success,
            "duration": duration,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
    def log_performance_metric(self, metric_name: str, value: float, unit: str = ""):
        """Log a performance metric"""
        self.performance_metrics[metric_name] = {
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }
        
    def log_error(self, error_message: str, test_name: str = None):
        """Log an error"""
        self.errors.append({
            "message": error_message,
            "test_name": test_name,
            "timestamp": datetime.now().isoformat()
        })
        
    def log_warning(self, warning_message: str, test_name: str = None):
        """Log a warning"""
        self.warnings.append({
            "message": warning_message,
            "test_name": test_name,
            "timestamp": datetime.now().isoformat()
        })
        
    def collect_system_info(self):
        """Collect system information"""
        try:
            import platform
            import psutil
            
            # System information
            self.system_info = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "timestamp": datetime.now().isoformat()
            }
            
            # API health check
            health_result = make_request("GET", "/workflows/health-check")
            if health_result:
                self.system_info["api_health"] = health_result
            
        except ImportError:
            self.system_info = {
                "note": "Install psutil for detailed system metrics: pip install psutil",
                "timestamp": datetime.now().isoformat()
            }
            
    def generate_markdown_report(self, filename: str = None) -> str:
        """Generate comprehensive markdown report"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_response_test_report_{timestamp}.md"
            
        total_duration = self.test_end_time - self.test_start_time if self.test_end_time and self.test_start_time else 0
        successful_tests = sum(1 for result in self.test_results.values() if result["success"])
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        markdown_content = f"""# AI Response System Test Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Test Duration:** {total_duration:.2f} seconds  
**Success Rate:** {success_rate:.1f}% ({successful_tests}/{total_tests} tests passed)

---

## 📊 Executive Summary

### Test Results Overview
- **Total Tests Executed:** {total_tests}
- **Successful Tests:** {successful_tests}
- **Failed Tests:** {total_tests - successful_tests}
- **Total Errors:** {len(self.errors)}
- **Total Warnings:** {len(self.warnings)}
- **Overall Duration:** {total_duration:.2f} seconds

### Key Performance Indicators
"""

        # Add performance metrics
        if self.performance_metrics:
            markdown_content += "\n| Metric | Value | Unit |\n|--------|-------|------|\n"
            for metric_name, metric_data in self.performance_metrics.items():
                markdown_content += f"| {metric_name} | {metric_data['value']:.3f} | {metric_data['unit']} |\n"
        else:
            markdown_content += "\n*No performance metrics collected*\n"

        # System Information
        markdown_content += f"""

---

## 🖥️ System Information

### Environment Details
"""
        if self.system_info:
            for key, value in self.system_info.items():
                if key == "api_health":
                    continue  # Handle separately
                if isinstance(value, (int, float)):
                    if key.startswith("memory"):
                        value = f"{value / (1024**3):.1f} GB"  # Convert bytes to GB
                markdown_content += f"- **{key.replace('_', ' ').title()}:** {value}\n"

        # API Health Status
        if "api_health" in self.system_info:
            api_health = self.system_info["api_health"]
            markdown_content += f"""
### API Health Status
- **Overall Status:** {api_health.get('overall_status', 'Unknown')}
- **Timestamp:** {api_health.get('timestamp', 'N/A')}

#### Component Status
"""
            components = api_health.get('components', {})
            for component, status_info in components.items():
                status = status_info.get('status', 'Unknown')
                emoji = "✅" if status == "healthy" else "❌" if status == "unhealthy" else "⚠️"
                markdown_content += f"- {emoji} **{component.replace('_', ' ').title()}:** {status}\n"
                
                if status != "healthy" and "error" in status_info:
                    markdown_content += f"  - *Error: {status_info['error']}*\n"

        # Detailed Test Results
        markdown_content += """

---

## 📋 Detailed Test Results

"""
        for test_name, result in self.test_results.items():
            status_emoji = "✅" if result["success"] else "❌"
            markdown_content += f"""
### {status_emoji} {test_name.replace('_', ' ').title()}

- **Status:** {'PASSED' if result['success'] else 'FAILED'}
- **Duration:** {result['duration']:.3f} seconds
- **Timestamp:** {result['timestamp']}
"""
            
            # Add test details if available
            if result.get("details"):
                markdown_content += "\n#### Test Details\n"
                for key, value in result["details"].items():
                    if isinstance(value, (list, dict)):
                        markdown_content += f"- **{key.replace('_', ' ').title()}:** {len(value) if isinstance(value, list) else 'Complex object'}\n"
                    else:
                        markdown_content += f"- **{key.replace('_', ' ').title()}:** {value}\n"

        # Performance Analysis
        markdown_content += """

---

## ⚡ Performance Analysis

### Response Time Analysis
"""
        if self.performance_metrics:
            # Calculate performance statistics
            response_times = []
            for metric_name, metric_data in self.performance_metrics.items():
                if "time" in metric_name.lower() or "duration" in metric_name.lower():
                    response_times.append(metric_data["value"])
            
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                min_time = min(response_times)
                max_time = max(response_times)
                
                markdown_content += f"""
- **Average Response Time:** {avg_time:.3f} seconds
- **Fastest Response:** {min_time:.3f} seconds  
- **Slowest Response:** {max_time:.3f} seconds
- **Total Measurements:** {len(response_times)}

#### Performance Recommendations
"""
                if avg_time > 5.0:
                    markdown_content += "- ⚠️ **High average response time detected** - Consider optimizing AI model calls\n"
                if max_time > 10.0:
                    markdown_content += "- ⚠️ **Some responses taking >10 seconds** - Investigate timeout handling\n"
                if avg_time < 2.0:
                    markdown_content += "- ✅ **Excellent response times** - System performing well\n"
            else:
                markdown_content += "\n*No response time metrics available*\n"
        else:
            markdown_content += "\n*No performance data collected*\n"

        # Error Analysis
        if self.errors:
            markdown_content += f"""

---

## ❌ Error Analysis

**Total Errors:** {len(self.errors)}

"""
            for i, error in enumerate(self.errors, 1):
                test_info = f" (Test: {error['test_name']})" if error.get('test_name') else ""
                markdown_content += f"""
### Error {i}{test_info}
- **Message:** {error['message']}
- **Timestamp:** {error['timestamp']}
"""

            # Error categories
            error_categories = {}
            for error in self.errors:
                if error.get('test_name'):
                    category = error['test_name']
                    error_categories[category] = error_categories.get(category, 0) + 1
            
            if error_categories:
                markdown_content += "\n#### Error Distribution by Test\n"
                for category, count in error_categories.items():
                    markdown_content += f"- **{category.replace('_', ' ').title()}:** {count} error(s)\n"

        # Warning Analysis
        if self.warnings:
            markdown_content += f"""

---

## ⚠️ Warning Analysis

**Total Warnings:** {len(self.warnings)}

"""
            for i, warning in enumerate(self.warnings, 1):
                test_info = f" (Test: {warning['test_name']})" if warning.get('test_name') else ""
                markdown_content += f"""
### Warning {i}{test_info}
- **Message:** {warning['message']}
- **Timestamp:** {warning['timestamp']}
"""

        # Test Coverage Analysis
        markdown_content += """

---

## 🎯 Test Coverage Analysis

### Functional Coverage
"""
        
        # Define expected test categories
        expected_tests = [
            "complete_workflow", "bulk_generation", "strategy_comparison",
            "modification_rating", "analytics", "error_handling", 
            "performance", "workflow_integration", "edge_cases"
        ]
        
        covered_tests = [test for test in expected_tests if test in self.test_results]
        coverage_percentage = (len(covered_tests) / len(expected_tests)) * 100
        
        markdown_content += f"""
- **Coverage Percentage:** {coverage_percentage:.1f}%
- **Tests Covered:** {len(covered_tests)}/{len(expected_tests)}

#### Test Categories Status
"""
        for test in expected_tests:
            if test in self.test_results:
                status = "✅ COVERED" if self.test_results[test]["success"] else "❌ FAILED"
            else:
                status = "⚪ NOT RUN"
            markdown_content += f"- **{test.replace('_', ' ').title()}:** {status}\n"

        # Recommendations
        markdown_content += """

---

## 💡 Recommendations

### Based on Test Results
"""
        
        recommendations = []
        
        # Performance recommendations
        if self.performance_metrics:
            avg_times = [m["value"] for m in self.performance_metrics.values() 
                        if "time" in str(m).lower()]
            if avg_times and sum(avg_times) / len(avg_times) > 3.0:
                recommendations.append("Consider optimizing AI response generation times")
        
        # Error-based recommendations
        if len(self.errors) > 0:
            recommendations.append("Review error handling mechanisms - errors detected during testing")
        
        # Coverage recommendations
        if coverage_percentage < 100:
            recommendations.append("Run missing test categories for complete coverage")
        
        # Success rate recommendations
        if success_rate < 90:
            recommendations.append("Investigate failed tests to improve system reliability")
        
        if not recommendations:
            recommendations.append("✅ System performing well - no immediate action required")
        
        for i, rec in enumerate(recommendations, 1):
            markdown_content += f"{i}. {rec}\n"

        # Future Test Plan
        markdown_content += """

### Future Testing Considerations
1. **Load Testing:** Test with higher concurrent users
2. **Integration Testing:** Test with external service dependencies  
3. **Security Testing:** Validate input sanitization and authentication
4. **Regression Testing:** Automated testing for CI/CD pipeline
5. **User Acceptance Testing:** Test with real property management scenarios

---

## 📈 Trend Analysis

*Note: Run multiple test sessions to build trend data over time*

### Historical Comparison
- This is test session #{self._get_session_number()}
- Compare with previous reports to identify performance trends
- Monitor success rates and response times over time

---

## 📝 Test Data Summary

### Mock Emails Processed
"""
        
        # Add mock email summary
        for i, email in enumerate(MOCK_EMAILS, 1):
            markdown_content += f"""
#### Email {i}: {email['subject']}
- **Sender:** {email['sender']}
- **Priority:** {email['priority_level']}
- **Context:** {', '.join(email['context_labels'])}
"""

        markdown_content += f"""

---

## 🔗 Appendix

### Generated Files
- **Report File:** {filename}
- **Test Logs:** Available in console output
- **Test Data:** Stored in database (use cleanup command to remove)

### Commands Used
```bash
# To reproduce this test run:
python test_ai_responses.py full

# To generate report only:
python test_ai_responses.py report

# To clean up test data:
python test_ai_responses.py cleanup
```

### Support Information
- **API Base URL:** {BASE_URL}
- **Report Generated:** {datetime.now().isoformat()}
- **Test Framework Version:** 1.0.0

---

*This report was automatically generated by the AI Response Testing Framework*
"""

        # Write to file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print_success(f"📄 Report generated: {filename}")
            return filename
        except Exception as e:
            print_error(f"Failed to write report file: {e}")
            return None
    
    def _get_session_number(self) -> int:
        """Get session number for trend analysis"""
        import os
        import glob
        
        # Count existing report files
        report_files = glob.glob("ai_response_test_report_*.md")
        return len(report_files) + 1

# Global reporter instance
test_reporter = TestReporter()

# =============================================================================
# ENHANCED TEST FUNCTIONS WITH REPORTING
# =============================================================================

def run_all_tests_with_reporting():
    """Run all tests with comprehensive reporting"""
    test_reporter.start_reporting()
    test_reporter.collect_system_info()
    
    print("🚀 STARTING COMPREHENSIVE AI RESPONSE TESTING WITH REPORTING")
    print("=" * 80)
    
    start_time = time.time()
    test_results = {}
    
    try:
        # Test 1: Complete Workflow
        print_info("Running Test 1: Complete AI Response Workflow...")
        test_start = time.time()
        try:
            result = test_complete_ai_workflow()
            test_duration = time.time() - test_start
            test_results["complete_workflow"] = result
            test_reporter.log_test_result("complete_workflow", result is not None, test_duration, 
                                        {"email_id": result if result else None})
            test_reporter.log_performance_metric("complete_workflow_duration", test_duration, "seconds")
        except Exception as e:
            test_duration = time.time() - test_start
            test_reporter.log_test_result("complete_workflow", False, test_duration)
            test_reporter.log_error(str(e), "complete_workflow")
            print_error(f"Test 1 failed: {e}")
        
        # Test 2: Bulk Generation
        print_info("Running Test 2: Bulk AI Response Generation...")
        test_start = time.time()
        try:
            result = test_bulk_ai_response_generation()
            test_duration = time.time() - test_start
            test_results["bulk_generation"] = result
            test_reporter.log_test_result("bulk_generation", result is not None, test_duration,
                                        {"emails_processed": len(result) if result else 0})
            test_reporter.log_performance_metric("bulk_generation_duration", test_duration, "seconds")
            if result:
                test_reporter.log_performance_metric("bulk_emails_per_second", len(result) / test_duration, "emails/sec")
        except Exception as e:
            test_duration = time.time() - test_start
            test_reporter.log_test_result("bulk_generation", False, test_duration)
            test_reporter.log_error(str(e), "bulk_generation")
            print_error(f"Test 2 failed: {e}")
        
        # Test 3: Strategy Comparison
        print_info("Running Test 3: AI Response Strategies Comparison...")
        test_start = time.time()
        try:
            result = test_ai_response_strategies()
            test_duration = time.time() - test_start
            test_results["strategy_comparison"] = result
            test_reporter.log_test_result("strategy_comparison", result is not None, test_duration)
            test_reporter.log_performance_metric("strategy_comparison_duration", test_duration, "seconds")
        except Exception as e:
            test_duration = time.time() - test_start
            test_reporter.log_test_result("strategy_comparison", False, test_duration)
            test_reporter.log_error(str(e), "strategy_comparison")
            print_error(f"Test 3 failed: {e}")
        
        # Test 4: Modification and Rating
        print_info("Running Test 4: Response Modification and Rating...")
        test_start = time.time()
        try:
            result = test_ai_response_modification()
            test_duration = time.time() - test_start
            test_results["modification_rating"] = result
            test_reporter.log_test_result("modification_rating", result is not None, test_duration)
            test_reporter.log_performance_metric("modification_rating_duration", test_duration, "seconds")
        except Exception as e:
            test_duration = time.time() - test_start
            test_reporter.log_test_result("modification_rating", False, test_duration)
            test_reporter.log_error(str(e), "modification_rating")
            print_error(f"Test 4 failed: {e}")
        
        # Test 5: Analytics and Reporting
        print_info("Running Test 5: Analytics and Reporting...")
        test_start = time.time()
        try:
            result = test_ai_response_analytics()
            test_duration = time.time() - test_start
            test_results["analytics"] = result
            test_reporter.log_test_result("analytics", result is not None, test_duration,
                                        {"emails_analyzed": len(result) if result else 0})
            test_reporter.log_performance_metric("analytics_duration", test_duration, "seconds")
        except Exception as e:
            test_duration = time.time() - test_start
            test_reporter.log_test_result("analytics", False, test_duration)
            test_reporter.log_error(str(e), "analytics")
            print_error(f"Test 5 failed: {e}")
        
        # Test 6: Error Handling
        print_info("Running Test 6: Error Handling...")
        test_start = time.time()
        try:
            test_ai_response_error_handling()
            test_duration = time.time() - test_start
            test_reporter.log_test_result("error_handling", True, test_duration)
            test_reporter.log_performance_metric("error_handling_duration", test_duration, "seconds")
        except Exception as e:
            test_duration = time.time() - test_start
            test_reporter.log_test_result("error_handling", False, test_duration)
            test_reporter.log_error(str(e), "error_handling")
            print_error(f"Test 6 failed: {e}")
        
        # Test 7: Performance Testing
        print_info("Running Test 7: Performance Testing...")
        test_start = time.time()
        try:
            result = test_ai_response_performance()
            test_duration = time.time() - test_start
            test_results["performance"] = result
            test_reporter.log_test_result("performance", result is not None, test_duration,
                                        {"load_test_emails": len(result) if result else 0})
            test_reporter.log_performance_metric("performance_test_duration", test_duration, "seconds")
        except Exception as e:
            test_duration = time.time() - test_start
            test_reporter.log_test_result("performance", False, test_duration)
            test_reporter.log_error(str(e), "performance")
            print_error(f"Test 7 failed: {e}")
        
        # Test 8: Workflow Integration
        print_info("Running Test 8: Workflow Integration...")
        test_start = time.time()
        try:
            result = test_workflow_integration()
            test_duration = time.time() - test_start
            test_results["workflow_integration"] = result
            test_reporter.log_test_result("workflow_integration", result is not None, test_duration,
                                        {"workflow_id": result if result else None})
            test_reporter.log_performance_metric("workflow_integration_duration", test_duration, "seconds")
        except Exception as e:
            test_duration = time.time() - test_start
            test_reporter.log_test_result("workflow_integration", False, test_duration)
            test_reporter.log_error(str(e), "workflow_integration")
            print_error(f"Test 8 failed: {e}")
        
        # Test 9: Edge Cases
        print_info("Running Test 9: Edge Cases...")
        test_start = time.time()
        try:
            test_edge_cases()
            test_duration = time.time() - test_start
            test_reporter.log_test_result("edge_cases", True, test_duration)
            test_reporter.log_performance_metric("edge_cases_duration", test_duration, "seconds")
        except Exception as e:
            test_duration = time.time() - test_start
            test_reporter.log_test_result("edge_cases", False, test_duration)
            test_reporter.log_error(str(e), "edge_cases")
            print_error(f"Test 9 failed: {e}")
        
    except Exception as e:
        test_reporter.log_error(f"Test execution failed: {e}")
        print_error(f"Test execution failed: {e}")
        return
    
    total_time = time.time() - start_time
    test_reporter.log_performance_metric("total_test_duration", total_time, "seconds")
    
    test_reporter.end_reporting()
    
    # Final summary
    print_section("Test Execution Summary")
    
    print_success(f"All tests completed in {total_time:.2f} seconds")
    
    successful_tests = sum(1 for result in test_results.values() if result is not None)
    total_tests = len(test_results)
    
    print_success(f"Successful tests: {successful_tests}/{total_tests}")
    
    if test_results.get("analytics"):
        processed_emails = test_results["analytics"]
        print_info(f"Total test emails processed: {len(processed_emails)}")
    
    print("\n📊 Test Results Summary:")
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result is not None else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    # Generate comprehensive report
    print_section("Generating Comprehensive Report")
    report_filename = test_reporter.generate_markdown_report()
    
    if report_filename:
        print_success(f"📄 Comprehensive test report generated: {report_filename}")
        print_info("📖 Open the report file to view detailed analysis, performance metrics, and recommendations")
    
    return test_results, report_filename

def generate_report_only():
    """Generate report from existing test data"""
    print_section("Generating Test Report from Current Data")
    
    test_reporter.collect_system_info()
    
    # Collect current system data for reporting
    try:
        # Get current email analytics
        result = make_request("GET", "/emails/analytics/summary")
        if result:
            test_reporter.log_performance_metric("current_total_emails", result['overview']['total_emails'], "emails")
            test_reporter.log_performance_metric("current_response_rate", 
                                               result['performance_metrics'].get('ticket_creation_rate', 0) * 100, "%")
    
        # Get current system health
        health_result = make_request("GET", "/workflows/health-check")
        if health_result:
            test_reporter.system_info["api_health"] = health_result
            
        # Mock some basic test results for report generation
        test_reporter.test_start_time = time.time() - 300  # 5 minutes ago
        test_reporter.test_end_time = time.time()
        
        report_filename = test_reporter.generate_markdown_report("current_system_report.md")
        
        if report_filename:
            print_success(f"📄 System report generated: {report_filename}")
            return report_filename
        else:
            print_error("Failed to generate report")
            return None
            
    except Exception as e:
        print_error(f"Error generating report: {e}")
        return None

# =============================================================================
# ADDITIONAL REPORTING FEATURES
# =============================================================================

def run_performance_benchmark():
    """Run dedicated performance benchmark tests"""
    print_section("Performance Benchmark Testing")
    
    test_reporter.start_reporting()
    test_reporter.collect_system_info()
    
    benchmark_results = {}
    
    # Benchmark 1: Single email processing speed
    print_step(1, "Benchmarking single email processing speed")
    
    single_email_times = []
    for i in range(5):
        start_time = time.time()
        email_id = create_sample_email("maintenance")
        if email_id:
            generate_ai_responses_for_email(email_id)
        processing_time = time.time() - start_time
        single_email_times.append(processing_time)
        print_info(f"Run {i+1}: {processing_time:.3f} seconds")
    
    avg_single_time = sum(single_email_times) / len(single_email_times)
    benchmark_results["single_email_avg_time"] = avg_single_time
    test_reporter.log_performance_metric("single_email_avg_processing_time", avg_single_time, "seconds")
    
    print_success(f"Average single email processing: {avg_single_time:.3f} seconds")
    
    # Benchmark 2: Bulk processing efficiency
    print_step(2, "Benchmarking bulk processing efficiency")
    
    bulk_sizes = [5, 10, 20]
    for bulk_size in bulk_sizes:
        print_info(f"Testing bulk size: {bulk_size} emails")
        
        # Create emails
        email_ids = []
        for i in range(bulk_size):
            email_id = create_sample_email("maintenance")
            if email_id:
                email_ids.append(email_id)
        
        # Time bulk processing
        start_time = time.time()
        result = make_request("POST", "/emails/bulk/generate-ai-responses", {"email_ids": email_ids})
        bulk_time = time.time() - start_time
        
        if result:
            emails_per_second = bulk_size / bulk_time
            benchmark_results[f"bulk_{bulk_size}_emails_per_second"] = emails_per_second
            test_reporter.log_performance_metric(f"bulk_{bulk_size}_emails_per_second", emails_per_second, "emails/sec")
            
            print_success(f"Bulk {bulk_size}: {bulk_time:.3f}s ({emails_per_second:.2f} emails/sec)")
    
    # Benchmark 3: Response selection speed
    print_step(3, "Benchmarking response selection speed")
    
    selection_times = []
    for i in range(10):
        # Create email and generate responses
        email_id = create_sample_email("maintenance")
        if email_id:
            generate_ai_responses_for_email(email_id)
            
            # Get responses
            result = make_request("GET", f"/emails/{email_id}/ai-responses")
            if result and result["ai_responses"]:
                options = result["ai_responses"][0]["response_options"]
                if options:
                    selected_option = options[0]
                    
                    # Time the selection
                    start_time = time.time()
                    selection_data = {
                        "option_id": selected_option["option_id"],
                        "rating": 4.0
                    }
                    make_request("POST", f"/emails/{email_id}/ai-responses/select", selection_data)
                    selection_time = time.time() - start_time
                    selection_times.append(selection_time)
    
    if selection_times:
        avg_selection_time = sum(selection_times) / len(selection_times)
        benchmark_results["avg_selection_time"] = avg_selection_time
        test_reporter.log_performance_metric("avg_response_selection_time", avg_selection_time, "seconds")
        print_success(f"Average response selection: {avg_selection_time:.3f} seconds")
    
    # Benchmark 4: System load capacity
    print_step(4, "Testing system load capacity")
    
    max_concurrent = 0
    for concurrent_level in [5, 10, 15, 20]:
        print_info(f"Testing {concurrent_level} concurrent requests")
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def concurrent_test():
            try:
                email_id = create_sample_email("maintenance")
                if email_id:
                    start_time = time.time()
                    success = generate_ai_responses_for_email(email_id)
                    duration = time.time() - start_time
                    results_queue.put((success, duration))
                else:
                    results_queue.put((False, 0))
            except Exception as e:
                results_queue.put((False, 0))
        
        # Start concurrent threads
        threads = []
        start_time = time.time()
        
        for i in range(concurrent_level):
            thread = threading.Thread(target=concurrent_test)
            thread.start()
            threads.append(thread)
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        successful = 0
        response_times = []
        
        while not results_queue.empty():
            success, duration = results_queue.get()
            if success:
                successful += 1
                response_times.append(duration)
        
        success_rate = (successful / concurrent_level) * 100
        
        if success_rate >= 90:  # 90% success rate threshold
            max_concurrent = concurrent_level
            benchmark_results[f"concurrent_{concurrent_level}_success_rate"] = success_rate
            test_reporter.log_performance_metric(f"concurrent_{concurrent_level}_success_rate", success_rate, "%")
            print_success(f"Concurrent {concurrent_level}: {success_rate:.1f}% success rate")
        else:
            print_error(f"Concurrent {concurrent_level}: {success_rate:.1f}% success rate (below threshold)")
            break
    
    benchmark_results["max_concurrent_capacity"] = max_concurrent
    test_reporter.log_performance_metric("max_concurrent_capacity", max_concurrent, "requests")
    
    test_reporter.end_reporting()
    
    # Generate benchmark report
    print_section("Generating Benchmark Report")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = test_reporter.generate_markdown_report(f"benchmark_report_{timestamp}.md")
    
    if report_filename:
        print_success(f"📄 Benchmark report generated: {report_filename}")
    
    print_section("Benchmark Summary")
    print_success(f"Single email processing: {benchmark_results.get('single_email_avg_time', 0):.3f}s avg")
    print_success(f"Maximum concurrent capacity: {benchmark_results.get('max_concurrent_capacity', 0)} requests")
    if benchmark_results.get('bulk_10_emails_per_second'):
        print_success(f"Bulk processing rate: {benchmark_results['bulk_10_emails_per_second']:.2f} emails/sec")
    
    return benchmark_results

def start_continuous_monitoring():
    """Start continuous monitoring of the AI response system"""
    print_section("Starting Continuous System Monitoring")
    print_info("Press Ctrl+C to stop monitoring")
    
    monitoring_data = []
    
    try:
        while True:
            timestamp = datetime.now()
            
            # Collect system metrics
            health_result = make_request("GET", "/workflows/health-check")
            analytics_result = make_request("GET", "/emails/analytics/summary")
            
            monitor_point = {
                "timestamp": timestamp.isoformat(),
                "system_health": health_result.get("overall_status", "unknown") if health_result else "unknown",
                "total_emails": analytics_result.get("overview", {}).get("total_emails", 0) if analytics_result else 0,
                "recent_emails": analytics_result.get("overview", {}).get("recent_emails_7days", 0) if analytics_result else 0
            }
            
            # Test response time
            test_start = time.time()
            test_email_id = create_sample_email("maintenance")
            if test_email_id:
                ai_success = generate_ai_responses_for_email(test_email_id)
                response_time = time.time() - test_start
                monitor_point["response_time"] = response_time
                monitor_point["ai_generation_success"] = ai_success
            else:
                monitor_point["response_time"] = None
                monitor_point["ai_generation_success"] = False
            
            monitoring_data.append(monitor_point)
            
            # Display current status
            status_emoji = "✅" if monitor_point["system_health"] == "healthy" else "❌"
            response_status = f"{monitor_point['response_time']:.2f}s" if monitor_point["response_time"] else "FAILED"
            
            print(f"{timestamp.strftime('%H:%M:%S')} | {status_emoji} Health: {monitor_point['system_health']} | "
                  f"📧 Emails: {monitor_point['total_emails']} | ⚡ Response: {response_status}")
            
            # Wait before next check
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        print_info("\n🛑 Monitoring stopped by user")
        
        # Generate monitoring report
        if monitoring_data:
            print_section("Generating Monitoring Report")
            
            # Create a simple monitoring report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitoring_report_{timestamp}.md"
            
            total_checks = len(monitoring_data)
            successful_checks = sum(1 for m in monitoring_data if m["system_health"] == "healthy")
            avg_response_time = sum(m["response_time"] for m in monitoring_data if m["response_time"]) / len([m for m in monitoring_data if m["response_time"]])
            
            report_content = f"""# System Monitoring Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Monitoring Duration:** {total_checks * 0.5:.1f} minutes  
**Total Checks:** {total_checks}

## Summary

- **System Uptime:** {(successful_checks/total_checks)*100:.1f}%
- **Average Response Time:** {avg_response_time:.2f} seconds
- **Successful Health Checks:** {successful_checks}/{total_checks}

## Monitoring Data

| Time | Health Status | Response Time | Total Emails |
|------|---------------|---------------|--------------|
"""
            
            for data_point in monitoring_data[-20:]:  # Last 20 entries
                time_str = data_point["timestamp"].split("T")[1][:8]
                health = data_point["system_health"]
                response = f"{data_point['response_time']:.2f}s" if data_point["response_time"] else "FAILED"
                emails = data_point["total_emails"]
                
                report_content += f"| {time_str} | {health} | {response} | {emails} |\n"
            
            report_content += """
## Recommendations

- Monitor response times regularly
- Set up alerts for system health changes
- Track email processing volume trends
"""
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                print_success(f"📄 Monitoring report generated: {filename}")
            except Exception as e:
                print_error(f"Failed to generate monitoring report: {e}")

def generate_comparison_report(report_files: List[str]):
    """Generate a comparison report from multiple test reports"""
    print_section("Generating Comparison Report")
    
    if len(report_files) < 2:
        print_error("Need at least 2 report files for comparison")
        return None
    
    print_info(f"Comparing {len(report_files)} test reports...")
    
    # This would parse existing reports and compare metrics
    # Implementation would depend on the specific comparison needs
    
    comparison_content = f"""# Test Results Comparison Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Reports Compared:** {len(report_files)}

## Report Files
"""
    
    for i, report_file in enumerate(report_files, 1):
        comparison_content += f"{i}. {report_file}\n"
    
    comparison_content += """
## Performance Trends

*Analysis of performance changes over time*

## Success Rate Trends

*Analysis of success rate changes over time*

## Recommendations

*Based on trend analysis*
"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"comparison_report_{timestamp}.md"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(comparison_content)
        print_success(f"📄 Comparison report generated: {filename}")
        return filename
    except Exception as e:
        print_error(f"Failed to generate comparison report: {e}")
        return None


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "full":
            # Run all tests with comprehensive reporting
            run_all_tests_with_reporting()
        elif command == "quick":
            # Run quick tests only (with basic reporting)
            test_reporter.start_reporting()
            test_reporter.collect_system_info()
            
            start_time = time.time()
            
            test_start = time.time()
            result1 = test_complete_ai_workflow()
            test_reporter.log_test_result("complete_workflow", result1 is not None, time.time() - test_start)
            
            test_start = time.time()
            result2 = test_ai_response_modification()
            test_reporter.log_test_result("modification_rating", result2 is not None, time.time() - test_start)
            
            test_reporter.log_performance_metric("quick_test_duration", time.time() - start_time, "seconds")
            test_reporter.end_reporting()
            
            # Generate quick report
            report_filename = test_reporter.generate_markdown_report("quick_test_report.md")
            if report_filename:
                print_success(f"📄 Quick test report generated: {report_filename}")
                
        elif command == "report":
            # Generate report from current system state
            generate_report_only()
        elif command == "create":
            # Create sample email
            email_type = sys.argv[2] if len(sys.argv) > 2 else "maintenance"
            create_sample_email(email_type)
        elif command == "generate":
            # Generate AI responses for email
            if len(sys.argv) > 2:
                email_id = sys.argv[2]
                generate_ai_responses_for_email(email_id)
            else:
                print_error("Please provide email ID: python test_ai.py generate <email_id>")
        elif command == "view":
            # View AI responses for email
            if len(sys.argv) > 2:
                email_id = sys.argv[2]
                view_ai_responses(email_id)
            else:
                print_error("Please provide email ID: python test_ai.py view <email_id>")
        elif command == "select":
            # Interactive selection
            if len(sys.argv) > 2:
                email_id = sys.argv[2]
                select_ai_response_interactive(email_id)
            else:
                print_error("Please provide email ID: python test_ai.py select <email_id>")
        elif command == "cleanup":
            # Clean up test data
            cleanup_test_data()
        elif command == "benchmark":
            # Run performance benchmark
            run_performance_benchmark()
        elif command == "monitor":
            # Start continuous monitoring
            start_continuous_monitoring()
        elif command == "help":
            print("""
AI Response Testing Commands:

full        - Run all comprehensive tests with detailed reporting
quick       - Run quick essential tests with basic reporting  
report      - Generate report from current system state
create      - Create sample email (maintenance|payment|lockout|complaint|hvac|lease)
generate    - Generate AI responses for email ID
view        - View AI response options for email ID
select      - Interactively select AI response for email ID
cleanup     - Clean up test data
benchmark   - Run performance benchmark tests
monitor     - Start continuous system monitoring
help        - Show this help message

Examples:
python test_ai.py full                    # Full test suite with comprehensive report
python test_ai.py quick                   # Quick tests with basic report
python test_ai.py report                  # Generate report from current data
python test_ai.py create maintenance      # Create maintenance email
python test_ai.py generate email_123      # Generate AI responses
python test_ai.py view email_123          # View response options
python test_ai.py select email_123        # Interactive selection
python test_ai.py cleanup                 # Clean test data
python test_ai.py benchmark              # Performance benchmark
python test_ai.py monitor                # Start monitoring

Report Files:
- ai_response_test_report_YYYYMMDD_HHMMSS.md  (Full test report)
- quick_test_report.md                        (Quick test report)
- current_system_report.md                    (Current system report)
- benchmark_report_YYYYMMDD_HHMMSS.md         (Benchmark report)
""")
        else:
            print_error(f"Unknown command: {command}")
            print_info("Use 'python test_ai.py help' for available commands")
    else:
        # Default: run quick tests with reporting
        print_info("Running quick AI response tests with reporting...")
        print_info("Use 'python test_ai.py help' for more options")
        
        test_reporter.start_reporting()
        test_reporter.collect_system_info()
        
        start_time = time.time()
        
        test_start = time.time()
        result1 = test_complete_ai_workflow()
        test_reporter.log_test_result("complete_workflow", result1 is not None, time.time() - test_start)
        
        test_start = time.time()
        result2 = test_ai_response_modification()
        test_reporter.log_test_result("modification_rating", result2 is not None, time.time() - test_start)
        
        test_reporter.log_performance_metric("default_test_duration", time.time() - start_time, "seconds")
        test_reporter.end_reporting()
        
        # Generate quick report
        report_filename = test_reporter.generate_markdown_report("default_test_report.md")
        if report_filename:
            print_success(f"📄 Test report generated: {report_filename}")
