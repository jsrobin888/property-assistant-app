import logging
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from tinydb import TinyDB, Query
from ...models import db, ai_responses_table
# Modern LangChain imports
try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_anthropic import ChatAnthropic
    from langchain_ollama import ChatOllama
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.chains import RetrievalQA
    from langchain_core.prompts import PromptTemplate
    from langchain_core.documents import Document
    from langchain_core.messages import HumanMessage
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    print(f"LangChain not available: {e}")
    print("Install with: pip install langchain-openai langchain-anthropic langchain-ollama langchain-community")

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

class LangChainRAGSystem:
    """LangChain-based RAG system with vector store"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize embeddings
        self.embeddings = self._init_embeddings()
        
        # Initialize vector store
        self.vector_store = None
        self._init_vector_store()
        
        # Text splitter for documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
    
    def _init_embeddings(self):
        """Initialize embeddings model with modern LangChain"""
        try:
            if self.config.get('openai_api_key'):
                return OpenAIEmbeddings(
                    api_key=self.config['openai_api_key'],
                    model="text-embedding-3-small"  # Latest embedding model
                )
            else:
                # Use local embeddings
                return HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
        except Exception as e:
            logger.warning(f"Could not initialize embeddings: {e}")
            return None
    
    def _init_vector_store(self):
        """Initialize vector store with property management knowledge"""
        if not self.embeddings:
            return
        
        try:
            # Property management knowledge base
            # Domestic Docu manage
            documents = [
                Document(metadata={"type": "maintenance"}, page_content="Standard maintenance requests are handled within 24-48 hours during business days (Monday-Friday, 9 AM - 6 PM)."),
                Document(metadata={"type": "emergency"}, page_content="Emergency repairs (flooding, gas leaks, electrical hazards, heating/cooling failures) are addressed immediately 24/7."),
                Document(metadata={"type": "maintenance"}, page_content="For maintenance requests, call (555) 123-4567 or submit online at portal.property.com/maintenance."),
                Document(metadata={"type": "rent"}, page_content="Rent is due on the 1st of each month. Grace period until the 5th without late fees."),
                Document(metadata={"type": "rent"}, page_content="Late fees of $50 apply after the 5th of the month. Additional $25 fee for each subsequent week."),
                Document(metadata={"type": "rent"}, page_content="Accepted payment methods: online portal, ACH transfer, certified check, money order. Cash not accepted."),
                Document(metadata={"type": "lockout"}, page_content="During business hours (9 AM - 6 PM), contact office at (555) 123-4567 for lockout assistance."),
                Document(metadata={"type": "lockout"}, page_content="After hours lockout service: call emergency line (555) 123-4567. Service fee: $75 weekdays, $100 weekends/holidays."),
                Document(metadata={"type": "emergency"}, page_content="Emergency maintenance: (555) 123-4567 (available 24/7 for true emergencies only)."),
                Document(metadata={"type": "general"}, page_content="Office hours: Monday-Friday 9 AM - 6 PM, Saturday 10 AM - 4 PM, Closed Sundays."),
                Document(metadata={"type": "general"}, page_content="Main office: (555) 123-4567, Email: info@property.com"),
            ]
            
            # Create vector store
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            logger.info("Initialized FAISS vector store with property management knowledge")
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            self.vector_store = None
    
    def retrieve_context(self, query: str, k: int = 3) -> List[str]:
        """Retrieve relevant context using vector similarity"""
        if not self.vector_store:
            return []
        
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []

class LangChainLLMManager:
    """LangChain-based LLM manager supporting multiple models"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = {}
                
        # Initialize available models
        self._init_models()
        print(self.config)
        
    def _init_models(self):
        """Initialize all available LLM models with modern LangChain"""
        
        # OpenAI models
        if self.config.get('openai_api_key'):
            try:
                self.models['openai_gpt35'] = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    api_key=self.config['openai_api_key'],
                    temperature=0.7,
                    max_completion_tokens=2000
                )
                self.models['openai_gpt4'] = ChatOpenAI(
                    model="gpt-4",
                    api_key=self.config['openai_api_key'],
                    temperature=0.7,
                    max_completion_tokens=2000
                )
                self.models['openai_gpt4o'] = ChatOpenAI(
                    model="gpt-4o",
                    api_key=self.config['openai_api_key'],
                    temperature=0.7,
                    max_completion_tokens=2000
                )
                self.models['openai_gpt4o_mini'] = ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=self.config['openai_api_key'],
                    temperature=0.7,
                    max_completion_tokens=2000
                )
                logger.info("Initialized OpenAI models (GPT-3.5, GPT-4, GPT-4o)")
            except Exception as e:
                logger.error(f"Error initializing OpenAI: {e}")
        
        # Anthropic models
        if self.config.get('anthropic_api_key'):
            try:
                self.models['anthropic_claude3_haiku'] = ChatAnthropic(
                    model="claude-3-haiku-20240307",
                    api_key=self.config['anthropic_api_key'],
                    temperature=0.7,
                    max_tokens_to_sample=2000
                    
                )
                self.models['anthropic_claude3_sonnet'] = ChatAnthropic(
                    model="claude-3-sonnet-20240229",
                    api_key=self.config['anthropic_api_key'],
                    temperature=0.7,
                    max_tokens_to_sample=2000
                )
                logger.info("Initialized Anthropic models (Claude-3 Haiku, Sonnet)")
            except Exception as e:
                logger.error(f"Error initializing Anthropic: {e}")
        
        # Local models via Ollama
        if self.config.get('use_local_models') and self.config.get("base_url"):
            try:
                # Try common local models available in Ollama
                local_models = [
                    # ('llama3.1', 'llama3.1:8b'),
                    # ('llama3', 'llama3:8b'),
                    # ('mistral', 'mistral:7b'),
                    # ('codellama', 'codellama:7b'),
                    # ('phi3', 'phi3:mini'),
                    ('qwen2.5','qwen2.5:14b')
                ]
                
                for model_key, model_name in local_models:
                    try:
                        self.models[f'local_{model_key}'] = ChatOllama(
                            model=model_name,
                            temperature=0.7,
                            base_url=self.config.get("base_url"),
                            num_ctx=2000,
                        )
                        logger.info(f"Initialized local model: {model_name}")
                        break  # Use first available local model
                    except Exception as e:
                        logger.debug(f"Could not initialize {model_name}: {e}")
                        continue
            except Exception as e:
                logger.error(f"Error initializing local models: {e}")
        else:
          logger.error("<use_local_models> is 'False' or missing base_url ")
        logger.info(f"Initialized {len(self.models)} LLM models: {list(self.models.keys())}")
    
    def get_model(self, model_name: str):
        """Get specific model instance"""
        return self.models.get(model_name)
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return list(self.models.keys())
    
    def generate_response(self, model_name: str, prompt: str) -> str:
        """Generate response using specified model with modern LangChain"""
        model = self.get_model(model_name)
        if not model:
            raise ValueError(f"Model {model_name} not available")
        
        try:
            # Modern LangChain approach
            messages = [HumanMessage(content=prompt)]
            response = model.invoke(messages)
            
            # Extract content from response
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Error generating response with {model_name}: {e}")
            raise

class LangChainAIResponder:
    """Main AI responder using LangChain with multiple models"""
    
    def __init__(self, config: Dict[str, Any]):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is required. Install with: pip install langchain")
        
        self.config = config
        self.rag_system = LangChainRAGSystem(config)
        self.llm_manager = LangChainLLMManager(config)
        
        # Response templates
        self.templates = self._init_templates()

    def _init_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize LangChain prompt templates with modern syntax"""
        
        # RAG template
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
        
        # Direct LLM template
        direct_template = PromptTemplate(
            input_variables=["email_content", "tenant_name"],
            template="""You are a professional property management assistant. Write a helpful, empathetic response to this tenant email:

From: {tenant_name}
Email: {email_content}

Write a professional response addressing their concern:"""
        )
        
        # Template-based response
        template_based = PromptTemplate(
            input_variables=["issue_type", "tenant_name", "specific_issue"],
            template="""Dear {tenant_name},

Thank you for contacting us about {specific_issue}.

Based on the type of issue ({issue_type}), here is our response:

{{Generate appropriate response based on issue type}}

Best regards,
Property Management Team"""
        )
        
        return {
            'rag': rag_template,
            'direct': direct_template,
            'template': template_based
        }
    
    def generate_reply(self, email_data: Dict[str, Any], email_id: str) -> List[Dict[str, Any]]:
        """Generate multiple response options using different strategies"""
        
        responses = []
        tenant_name = self._extract_tenant_name(email_data.get('sender', ''), )
        email_content = f"Subject: {email_data.get('subject', '')}\n{email_data.get('body', '')}"
        query = email_content
        
        # 1. RAG-based response (if vector store available)
        if self.rag_system.vector_store:
            rag_response = self._generate_rag_response(query, tenant_name)
            if rag_response:
                responses.append({
                    'email_id': email_id,
                    'content': rag_response,
                    'strategy_used': 'rag',
                    'provider': 'langchain_faiss',
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
                    responses.append({
                        'email_id': email_id,
                        'content': llm_response,
                        'strategy_used': 'llm',
                        'provider': model_name,
                        'confidence': 0.8 if 'gpt4' in model_name else 0.7,
                        'created_at': datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"Error with model {model_name}: {e}")
                continue
        
        # 3. Template-based response (fallback)
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
        
        logger.info(f"Generated {len(responses)} response options using LangChain")
        return responses
    
    def _generate_rag_response(self, query: str, tenant_name: str) -> str:
        """Generate RAG-based response using vector retrieval"""
        try:
            # Retrieve relevant context
            context_docs = self.rag_system.retrieve_context(query, k=3)
            context = "\n".join(context_docs)
            
            # Use first available model for RAG
            available_models = self.llm_manager.get_available_models()
            if not available_models:
                return None
            
            model_name = available_models[0]
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
        match = re.match(r"([^@]+)@", email)
        return match.group(1).replace('.', ' ').title() if match else "Tenant"       

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
        logger.info(f"Saved {len(response_options)} LangChain response options to waiting zone")
        
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
        
        logger.info(f"Selected LangChain response {option_id} for email {email_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error selecting AI response: {e}")
        return False

