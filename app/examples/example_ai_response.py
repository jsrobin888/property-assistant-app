from ..plugin.ai.ai_response import *
import random
from ..llm_config import llm_config

# Test the LangChain system
_test_email_1 = {
    'sender': 'john.doe@email.com',
    'subject': 'Toilet is broken in apt 3B',
    'body': 'Hi, my toilet stopped working this morning. Water is not filling up. Please help!'
}

_test_email_2 = {
    'sender': 'alice.go@email.com',
    'subject': 'Door is fall down apt 4B building 3',
    'body': 'Hi, the front door fall down last night, no sign of broke in, please help fix it!'
}

_test_email_01 = {
    "sender": "jordan.smith@example.com",
    "subject": "help!",
    "body": "Greenwich ave,i locked myself out and I need access to my apartment"
}

_test_email_02 = {
    "sender": "emily.tan@demo.org",
    "subject": "rent",
    "body": "Good night, im Wilkin Dan the tennant of 2000 Holland Av Apt 1F Im writing because I received a massage from you, i need to tell you, i have the money order for the payment, but im not going to send you, until fix the toilat, the aparment is in so bad condition"
}

_test_email_03 = {
    "sender": "rajiv.kumar@testmail.net",
    "subject": "Lease terms",
    "body": "Hello, I'm writing in behalf of my sister Miki at 100 Holland Av Apt 2D. Can you let me know what is our monthly rent?"
}


_test_email_04 = {
    "sender": "lisa.chen@fakemail.co",
    "subject": "call me back please",
    "body": "I'm available tomorrow 4pm."
}
    
test_emails = [_test_email_1, _test_email_2, _test_email_01, _test_email_02, _test_email_03, _test_email_04]

# Initialize system with multiple model support
config = llm_config

try:
    ai_responder = LangChainAIResponder(config)
    
    print(f"Available models: {ai_responder.llm_manager.get_available_models()}")
    
    for test_email in test_emails:
        test_email_id = f"{test_email['sender']}_{str(uuid.uuid4())[:4]}"
        # Generate responses
        response_options = ai_responder.generate_reply(test_email, test_email_id)
        
        print("\nGenerated LangChain Response Options:")
        for i, option in enumerate(response_options, 1):
            print(f"\n--- Option {i} ---")
            print(f"Strategy: {option['strategy_used']}")
            print(f"Provider: {option['provider']}")
            print(f"Confidence: {option['confidence']}")
            print(f"Content: {option['content'][:100]}...")
        
        # Save to waiting zone
        ai_response_id = save_ai_responses_to_waiting_zone(test_email_id, response_options)
        print(f"\nSaved to waiting zone: {ai_response_id}")
        
        # Simulate user selection
        if response_options:
            selected_option = response_options[random.choice([n for n in range(len(response_options))])]
            success = select_ai_response(
                test_email_id, 
                selected_option['option_id'], 
                rating=4.5
            )
            print(f"Selection result: {'Success' if success else 'Failed'}")
        
except ImportError as e:
    print(f"LangChain not available: {e}")
    print("Install with: pip install langchain langchain-openai langchain-anthropic")
    print("For local models, also install: pip install langchain-community")