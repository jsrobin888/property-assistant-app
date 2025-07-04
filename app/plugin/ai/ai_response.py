import logging
import json
import uuid
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from tinydb import TinyDB, Query
from ...models import db, ai_responses_table

# Lightweight imports - only cloud APIs
try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_anthropic import ChatAnthropic
    from langchain_core.prompts import PromptTemplate
    from langchain_core.messages import HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    print(f"LangChain not available: {e}")
    print("Install with: pip install langchain-openai langchain-anthropic langchain-core")

# Direct API imports as fallback
try:
    import openai
    OPENAI_DIRECT_AVAILABLE = True
except ImportError:
    OPENAI_DIRECT_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_DIRECT_AVAILABLE = True
except ImportError:
    ANTHROPIC_DIRECT_AVAILABLE = False

from ...models import (
    emails_table, 
    replies_table, 
    EmailMessage, 
    EmailStatus
)

import re
from email.message import EmailMessage as EmailMsgFunc
from email.utils import parseaddr

logger = logging.getLogger(__name__)

# Feature flags for conditional loading
FEATURES = {
    'use_vector_search': os.getenv('USE_VECTOR_SEARCH', 'false').lower() == 'true',
    'use_openai_embeddings': os.getenv('USE_OPENAI_EMBEDDINGS', 'false').lower() == 'true',
    'use_direct_apis': os.getenv('USE_DIRECT_APIS', 'true').lower() == 'true',
}

class LightweightRAGSystem:
    """Lightweight RAG system using keyword matching instead of vector embeddings"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.knowledge_base = self._init_knowledge_base()
        
        # Only use OpenAI embeddings if explicitly enabled and available
        self.embeddings = None
        if FEATURES['use_openai_embeddings'] and self.config.get('openai_api_key'):
            self.embeddings = self._init_embeddings()
    
    def _init_embeddings(self):
        """Initialize OpenAI embeddings only if enabled"""
        try:
            if LANGCHAIN_AVAILABLE:
                return OpenAIEmbeddings(
                    api_key=self.config['openai_api_key'],
                    model="text-embedding-3-small"
                )
        except Exception as e:
            logger.warning(f"Could not initialize OpenAI embeddings: {e}")
        return None
    
    def _init_knowledge_base(self) -> Dict[str, List[str]]:
        """Initialize lightweight knowledge base with keyword mapping"""
        return {
            'maintenance': [
                "Standard maintenance requests are handled within 24-48 hours during business days (Monday-Friday, 9 AM - 6 PM).",
                "For maintenance requests, call (555) 123-4567 or submit online at portal.property.com/maintenance.",
                "Emergency repairs (flooding, gas leaks, electrical hazards, heating/cooling failures) are addressed immediately 24/7."
            ],
            'rent': [
                "Rent is due on the 1st of each month. Grace period until the 5th without late fees.",
                "Late fees of $50 apply after the 5th of the month. Additional $25 fee for each subsequent week.",
                "Accepted payment methods: online portal, ACH transfer, certified check, money order. Cash not accepted."
            ],
            'lockout': [
                "During business hours (9 AM - 6 PM), contact office at (555) 123-4567 for lockout assistance.",
                "After hours lockout service: call emergency line (555) 123-4567. Service fee: $75 weekdays, $100 weekends/holidays."
            ],
            'emergency': [
                "Emergency maintenance: (555) 123-4567 (available 24/7 for true emergencies only).",
                "Emergency repairs (flooding, gas leaks, electrical hazards, heating/cooling failures) are addressed immediately 24/7."
            ],
            'general': [
                "Office hours: Monday-Friday 9 AM - 6 PM, Saturday 10 AM - 4 PM, Closed Sundays.",
                "Main office: (555) 123-4567, Email: info@property.com"
            ]
        }
    
    def retrieve_context(self, query: str, k: int = 3) -> List[str]:
        """Retrieve relevant context using keyword matching"""
        query_lower = query.lower()
        relevant_docs = []
        
        # Simple keyword matching
        for category, docs in self.knowledge_base.items():
            category_keywords = {
                'maintenance': ['broken', 'fix', 'repair', 'maintenance', 'leak', 'broken'],
                'rent': ['rent', 'payment', 'late fee', 'balance', 'due'],
                'lockout': ['locked out', 'lost key', 'keys', 'access', 'lockout'],
                'emergency': ['emergency', 'urgent', 'flooding', 'gas leak', 'electrical'],
                'general': ['office', 'hours', 'contact', 'phone', 'email']
            }
            
            if any(keyword in query_lower for keyword in category_keywords.get(category, [])):
                relevant_docs.extend(docs)
        
        # Return most relevant docs (limit to k)
        return relevant_docs[:k] if relevant_docs else self.knowledge_base['general'][:k]

# Keep original class name for compatibility
class LangChainRAGSystem(LightweightRAGSystem):
    """Alias for backward compatibility"""
    pass

class LightweightLLMManager:
    """Lightweight LLM manager using only cloud APIs"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = {}
        self._init_models()
        
    def _init_models(self):
        """Initialize only cloud-based models"""
        
        # OpenAI models via LangChain
        if LANGCHAIN_AVAILABLE and self.config.get('openai_api_key'):
            try:
                models_to_init = [
                    ('openai_gpt4o_mini', 'gpt-4o-mini'),
                    ('openai_gpt4o', 'gpt-4o'),
                    ('openai_gpt35', 'gpt-3.5-turbo'),
                ]
                
                for model_key, model_name in models_to_init:
                    try:
                        self.models[model_key] = ChatOpenAI(
                            model=model_name,
                            api_key=self.config['openai_api_key'],
                            temperature=0.7,
                            max_tokens=2000
                        )
                    except Exception as e:
                        logger.debug(f"Could not initialize {model_name}: {e}")
                        continue
                
                logger.info(f"Initialized {len([k for k in self.models.keys() if k.startswith('openai')])} OpenAI models")
            except Exception as e:
                logger.error(f"Error initializing OpenAI models: {e}")
        
        # Anthropic models via LangChain
        if LANGCHAIN_AVAILABLE and self.config.get('anthropic_api_key'):
            try:
                anthropic_models = [
                    ('anthropic_claude3_haiku', 'claude-3-haiku-20240307'),
                    ('anthropic_claude3_sonnet', 'claude-3-sonnet-20240229'),
                ]
                
                for model_key, model_name in anthropic_models:
                    try:
                        self.models[model_key] = ChatAnthropic(
                            model=model_name,
                            api_key=self.config['anthropic_api_key'],
                            temperature=0.7,
                            max_tokens=2000
                        )
                    except Exception as e:
                        logger.debug(f"Could not initialize {model_name}: {e}")
                        continue
                
                logger.info(f"Initialized {len([k for k in self.models.keys() if k.startswith('anthropic')])} Anthropic models")
            except Exception as e:
                logger.error(f"Error initializing Anthropic models: {e}")
        
        # Direct API fallbacks
        if FEATURES['use_direct_apis']:
            self._init_direct_apis()
        
        logger.info(f"Initialized {len(self.models)} total models: {list(self.models.keys())}")
    
    def _init_direct_apis(self):
        """Initialize direct API clients as fallback"""
        
        # Direct OpenAI API
        if OPENAI_DIRECT_AVAILABLE and self.config.get('openai_api_key'):
            try:
                self.openai_client = openai.OpenAI(api_key=self.config['openai_api_key'])
                if not any(k.startswith('openai') for k in self.models.keys()):
                    self.models['openai_direct'] = 'direct_openai'
                    logger.info("Initialized direct OpenAI API")
            except Exception as e:
                logger.error(f"Error initializing direct OpenAI: {e}")
        
        # Direct Anthropic API
        if ANTHROPIC_DIRECT_AVAILABLE and self.config.get('anthropic_api_key'):
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=self.config['anthropic_api_key'])
                if not any(k.startswith('anthropic') for k in self.models.keys()):
                    self.models['anthropic_direct'] = 'direct_anthropic'
                    logger.info("Initialized direct Anthropic API")
            except Exception as e:
                logger.error(f"Error initializing direct Anthropic: {e}")
    
    def get_model(self, model_name: str):
        """Get specific model instance"""
        return self.models.get(model_name)
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return list(self.models.keys())
    
    def generate_response(self, model_name: str, prompt: str) -> str:
        """Generate response using specified model"""
        model = self.get_model(model_name)
        if not model:
            raise ValueError(f"Model {model_name} not available")
        
        try:
            # LangChain models
            if hasattr(model, 'invoke'):
                messages = [HumanMessage(content=prompt)]
                response = model.invoke(messages)
                return response.content if hasattr(response, 'content') else str(response)
            
            # Direct API models
            elif model_name == 'openai_direct':
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif model_name == 'anthropic_direct':
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            else:
                raise ValueError(f"Unknown model type: {model_name}")
                
        except Exception as e:
            logger.error(f"Error generating response with {model_name}: {e}")
            raise

# Keep original class name for compatibility
class LangChainLLMManager(LightweightLLMManager):
    """Alias for backward compatibility"""
    pass

class LightweightAIResponder:
    """Lightweight AI responder using only cloud APIs"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rag_system = LightweightRAGSystem(config)
        self.llm_manager = LightweightLLMManager(config)
        self.templates = self._init_templates()
        
        # Fallback check
        if not self.llm_manager.get_available_models():
            logger.warning("No AI models available. Only template responses will work.")
    
    def _init_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize prompt templates"""
        
        if LANGCHAIN_AVAILABLE:
            # LangChain templates
            rag_template = PromptTemplate(
                input_variables=["context", "question", "tenant_name"],
                template="""You are a professional property management assistant.

Context:
{context}

Write a helpful, professional response to this tenant inquiry:
From: {tenant_name}
Question: {question}

Response:"""
            )
            
            direct_template = PromptTemplate(
                input_variables=["email_content", "tenant_name"],
                template="""You are a professional property management assistant. Write a helpful, empathetic response to this tenant email:

From: {tenant_name}
Email: {email_content}

Write a professional response addressing their concern:"""
            )
        else:
            # Simple string templates
            rag_template = """You are a professional property management assistant.

Context:
{context}

Write a helpful, professional response to this tenant inquiry:
From: {tenant_name}
Question: {question}

Response:"""
            
            direct_template = """You are a professional property management assistant. Write a helpful, empathetic response to this tenant email:

From: {tenant_name}
Email: {email_content}

Write a professional response addressing their concern:"""
        
        return {
            'rag': rag_template,
            'direct': direct_template
        }
    
    def generate_reply(self, email_data: Dict[str, Any], email_id: str) -> List[Dict[str, Any]]:
        """Generate multiple response options using different strategies"""
        
        responses = []
        tenant_name = self._extract_tenant_name(email_data.get('sender', ''))
        email_content = f"Subject: {email_data.get('subject', '')}\n{email_data.get('body', '')}"
        
        # 1. RAG-based response (using keyword matching)
        rag_response = self._generate_rag_response(email_content, tenant_name)
        if rag_response:
            responses.append({
                'email_id': email_id,
                'content': rag_response,
                'strategy_used': 'rag',
                'provider': 'lightweight_rag',
                'confidence': 0.85,
                'created_at': datetime.now().isoformat()
            })
        
        # 2. Direct LLM responses from available models
        available_models = self.llm_manager.get_available_models()
        
        # Use up to 2 different models for variety
        for model_name in available_models[:2]:
            try:
                llm_response = self._generate_llm_response(model_name, email_content, tenant_name)
                if llm_response:
                    confidence = 0.9 if 'gpt4' in model_name else 0.8 if 'claude' in model_name else 0.7
                    responses.append({
                        'email_id': email_id,
                        'content': llm_response,
                        'strategy_used': 'llm',
                        'provider': model_name,
                        'confidence': confidence,
                        'created_at': datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"Error with model {model_name}: {e}")
                continue
        
        # 3. Template-based response (always available fallback)
        template_response = self._generate_template_response(email_data, tenant_name)
        responses.append({
            'email_id': email_id,
            'content': template_response,
            'strategy_used': 'template',
            'provider': 'predefined_template',
            'confidence': 0.75,
            'created_at': datetime.now().isoformat()
        })
        
        # Add unique option IDs
        for i, response in enumerate(responses):
            response['option_id'] = str(uuid.uuid4())
            response['option_index'] = i
        
        logger.info(f"Generated {len(responses)} response options")
        return responses
    
    def _generate_rag_response(self, query: str, tenant_name: str) -> str:
        """Generate RAG-based response using keyword matching"""
        try:
            # Retrieve relevant context
            context_docs = self.rag_system.retrieve_context(query, k=3)
            context = "\n".join(context_docs)
            
            # Use first available model for RAG
            available_models = self.llm_manager.get_available_models()
            if not available_models:
                return None
            
            model_name = available_models[0]
            
            # Format prompt
            if LANGCHAIN_AVAILABLE and hasattr(self.templates['rag'], 'format'):
                prompt = self.templates['rag'].format(
                    context=context,
                    question=query,
                    tenant_name=tenant_name
                )
            else:
                prompt = self.templates['rag'].format(
                    context=context,
                    question=query,
                    tenant_name=tenant_name
                )
            
            return self.llm_manager.generate_response(model_name, prompt)
            
        except Exception as e:
            logger.error(f"Error in RAG response generation: {e}")
            return None
    
    def _generate_llm_response(self, model_name: str, email_content: str, tenant_name: str) -> str:
        """Generate direct LLM response"""
        try:
            # Format prompt
            if LANGCHAIN_AVAILABLE and hasattr(self.templates['direct'], 'format'):
                prompt = self.templates['direct'].format(
                    email_content=email_content,
                    tenant_name=tenant_name
                )
            else:
                prompt = self.templates['direct'].format(
                    email_content=email_content,
                    tenant_name=tenant_name
                )
            
            return self.llm_manager.generate_response(model_name, prompt)
            
        except Exception as e:
            logger.error(f"Error in LLM response generation with {model_name}: {e}")
            return None
    
    def _generate_template_response(self, email_data: Dict[str, Any], tenant_name: str) -> str:
        """Generate template-based response as fallback"""
        issue_type = self._detect_issue_type(email_data)
        specific_issue = email_data.get('subject', 'your inquiry')
        
        templates = {
            'maintenance': f"""Dear {tenant_name},

Thank you for reporting the maintenance issue: {specific_issue}.

We have received your request and our maintenance team will address this within 24-48 hours during business days. If this is an emergency, please call (555) 123-4567 immediately.

Best regards,
Property Management Team""",
            
            'rent': f"""Dear {tenant_name},

Thank you for contacting us about {specific_issue}.

Rent is due on the 1st of each month with a grace period until the 5th. For payment questions, please contact our office at (555) 123-4567.

Best regards,
Property Management Team""",
            
            'lockout': f"""Dear {tenant_name},

We understand being locked out is stressful and we're here to help immediately.

Please call our emergency line at (555) 123-4567 for lockout assistance.

Best regards,
Property Management Team""",
            
            'general': f"""Dear {tenant_name},

Thank you for contacting us about {specific_issue}.

We have received your message and will respond within 24 hours during business days.

For urgent matters, please call (555) 123-4567.

Best regards,
Property Management Team"""
        }
        
        return templates.get(issue_type, templates['general'])
    
    def _detect_issue_type(self, email_data: Dict[str, Any]) -> str:
        """Detect issue type from email content"""
        content = f"{email_data.get('subject', '')} {email_data.get('body', '')}".lower()
        
        if any(word in content for word in ['broken', 'fix', 'repair', 'maintenance', 'leak']):
            return 'maintenance'
        elif any(word in content for word in ['rent', 'payment', 'late fee', 'balance']):
            return 'rent'
        elif any(word in content for word in ['locked out', 'lost key', 'keys', 'access']):
            return 'lockout'
        else:
            return 'general'
    
    def _extract_tenant_name(self, sender: str, email_obj: EmailMsgFunc = None) -> str:
        """Extract tenant name from sender information"""
        if email_obj:
            sender_header = email_obj.get('From', '')
            name, email = parseaddr(sender_header)
            if name:
                return name.strip()
        else:
            name, email = parseaddr(sender)
            if name:
                return name.strip()
        
        # Fallback: use the local part of the email (before @) as the name
        match = re.match(r"([^@]+)@", email if email else sender)
        return match.group(1).replace('.', ' ').title() if match else "Tenant"

# Keep original class name for compatibility
class LangChainAIResponder(LightweightAIResponder):
    """Alias for backward compatibility"""
    
    def __init__(self, config: Dict[str, Any]):
        # Check if heavy dependencies are available
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not fully available. Using lightweight mode.")
        
        super().__init__(config)

# =============================================================================
# AI Response Management Functions (Waiting Zone)
# =============================================================================

def save_ai_responses_to_waiting_zone(email_id: str, response_options: List[Dict[str, Any]]) -> str:
    """Save AI response options to waiting zone"""
    try:
        ai_response_id = str(uuid.uuid4())
        
        ai_response_data = {
            'id': ai_response_id,
            'email_id': email_id,
            'response_options': response_options,
            'status': 'pending_selection',
            'created_at': datetime.now().isoformat(),
            'selected_option_id': None,
            'user_rating': None
        }
        
        ai_responses_table.insert(ai_response_data)
        logger.info(f"Saved {len(response_options)} response options to waiting zone")
        
        return ai_response_id
        
    except Exception as e:
        logger.error(f"Error saving AI responses to waiting zone: {e}")
        return None

def get_pending_ai_responses() -> List[Dict[str, Any]]:
    """Get all pending AI responses"""
    AIResponse = Query()
    return ai_responses_table.search(AIResponse.status == 'pending_selection')

def select_ai_response(email_id: str, option_id: str, rating: float = None, 
                      modifications: str = None) -> bool:
    """User selects an AI response option and saves to replies table"""
    try:
        # Find the AI response record
        AIResponse = Query()
        ai_response = ai_responses_table.get(AIResponse.email_id == email_id)
        
        if not ai_response:
            logger.error(f"No AI response found for email {email_id}")
            return False
        
        # Find the selected option
        selected_option = None
        for option in ai_response['response_options']:
            if option['option_id'] == option_id:
                selected_option = option
                break
        
        if not selected_option:
            logger.error(f"Option {option_id} not found")
            return False
        
        # Apply modifications if provided
        final_content = modifications if modifications else selected_option['content']
        
        # Save to replies table (final response)
        reply_data = {
            'email_id': email_id,
            'content': final_content,
            'strategy_used': selected_option['strategy_used'],
            'provider': selected_option['provider'],
            'confidence': selected_option['confidence'],
            'option_id': option_id,
            'user_rating': rating,
            'modifications_made': modifications is not None,
            'original_content': selected_option['content'] if modifications else None,
            'created_at': datetime.now().isoformat(),
            'sent': True
        }
        
        reply_id = replies_table.insert(reply_data)
        
        # Update AI response status
        ai_responses_table.update(
            {
                'status': 'completed',
                'selected_option_id': option_id,
                'reply_id': reply_id,
                'completed_at': datetime.now().isoformat(),
                'user_rating': rating
            },
            AIResponse.email_id == email_id
        )
        
        # Update email status
        EmailMessage.update_status(email_id, EmailStatus.RESPONDED)
        
        logger.info(f"Selected response {option_id} for email {email_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error selecting AI response: {e}")
        return False