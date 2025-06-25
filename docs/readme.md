# Property Management AI Assistant - Comprehensive Documentation

## Table of Contents

- [Property Management AI Assistant - Comprehensive Documentation](#property-management-ai-assistant---comprehensive-documentation)
  - [Table of Contents](#table-of-contents)
  - [System Overview](#system-overview)
    - [Key Features](#key-features)
    - [Technology Stack](#technology-stack)
  - [Architecture](#architecture)
    - [Core Components](#core-components)
  - [AI Response System](#ai-response-system)
    - [Strategy Overview](#strategy-overview)
    - [1. Template-Based Strategy](#1-template-based-strategy)
    - [2. RAG-Enhanced Strategy](#2-rag-enhanced-strategy)
    - [3. LLM-Powered Strategy](#3-llm-powered-strategy)
    - [Multi-Model Strategy Implementation](#multi-model-strategy-implementation)
    - [Response Selection and Learning](#response-selection-and-learning)
  - [API Documentation](#api-documentation)
    - [Base URL](#base-url)
    - [Authentication](#authentication)
  - [Email Processing Workflow](#email-processing-workflow)
  - [Ticket Management System](#ticket-management-system)
  - [Database Schema](#database-schema)
  - [Configuration \& Setup](#configuration--setup)
  - [Test Framework](#test-framework)
  - [V2 Roadmap - Advanced AI Features](#v2-roadmap---advanced-ai-features)
  - [10. V2 Roadmap – Advanced AI Features](#10-v2-roadmap--advanced-ai-features)
    - [Key Enhancements in V2](#key-enhancements-in-v2)
      - [🔄 1. Dynamic Prompting Engine](#-1-dynamic-prompting-engine)
      - [🧠 2. Cached Learning \& Behavioral Memory](#-2-cached-learning--behavioral-memory)
      - [♻️ 3. Reinforcement Learning from Feedback](#️-3-reinforcement-learning-from-feedback)
      - [📊 4. Periodic Behavioral Analysis](#-4-periodic-behavioral-analysis)
      - [🧪 5. A/B Strategy Testing Framework](#-5-ab-strategy-testing-framework)
    - [V2 Proof-of-Concept (PoC) Overview](#v2-proof-of-concept-poc-overview)

```
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [AI Response System](#ai-response-system)
4. [API Documentation](#api-documentation)
5. [Email Processing Workflow](#email-processing-workflow)
6. [Ticket Management System](#ticket-management-system)
7. [Database Schema](#database-schema)
8. [Configuration & Setup](#configuration--setup)
9. [Testing Framework](#testing-framework)
10. [V2 Roadmap - Advanced AI Features](#v2-roadmap---advanced-ai-features)
```
---

## System Overview

The Property Management AI Assistant is a comprehensive email processing and ticket management system designed to automate tenant communication and maintenance request handling. The system uses multiple AI strategies to generate appropriate responses to tenant emails and automatically creates tickets for actionable requests.

### Key Features

- **Multi-Strategy AI Response Generation**: Template-based, RAG-enhanced, and LLM-powered responses
- **Automated Email Processing**: Extract action items and create tickets automatically
- **Intelligent Categorization**: Automatic classification of maintenance, complaints, payment inquiries
- **Comprehensive API**: RESTful endpoints for all system operations
- **Real-time Monitoring**: System health checks and performance analytics
- **Flexible Configuration**: Support for multiple LLM providers and local models

### Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: TinyDB (JSON-based, lightweight)
- **AI/ML**: LangChain, OpenAI GPT models, Anthropic Claude, Local LLMs via Ollama
- **Email**: IMAP integration with Gmail
- **Testing**: Comprehensive test suite with performance benchmarking

---

## Architecture

[system-architecture](system-architecture.md)

### Core Components

1. **Email Processing Pipeline**: Ingests emails, extracts metadata, and classifies content
2. **AI Response Engine**: Generates multiple response options using different strategies
3. **Ticket Management System**: Automatically creates and manages maintenance tickets
4. **API Layer**: Provides RESTful interfaces for all system operations
5. **Database Layer**: Stores emails, responses, tickets, and system data

---

## AI Response System

The AI Response System is the core innovation of this platform, providing three distinct strategies for generating tenant responses, each optimized for different scenarios and use cases.

### Strategy Overview
[strategy overview](strategy-overview.md)

### 1. Template-Based Strategy

**Philosophy**: Fast, consistent, and reliable responses using predefined templates.

**How it Works**:
```python
def _generate_template_response(self, email_data: Dict[str, Any], tenant_name: str) -> str:
    issue_type = self._detect_issue_type(email_data)
    specific_issue = email_data.get('subject', 'your inquiry')
    
    templates = {
        'maintenance': f"""Dear {tenant_name},
        
        Thank you for reporting the maintenance issue: {specific_issue}.
        
        We have received your request and our maintenance team will address this 
        within 24-48 hours during business days. If this is an emergency, 
        please call (555) 123-4567 immediately.
        
        Best regards,
        Property Management Team""",
        # ... more templates
    }
    
    return templates.get(issue_type, templates['general'])
```

**Advantages**:
- **Lightning Fast**: Sub-second response times
- **Zero Cost**: No API calls or token usage
- **100% Reliable**: Never fails or produces inappropriate content
- **Brand Consistent**: Maintains uniform tone and messaging
- **Offline Capable**: Works without internet connectivity

**Limitations**:
- **Limited Personalization**: Cannot adapt to specific tenant situations
- **Rigid Structure**: May sound robotic for complex issues
- **No Learning**: Cannot improve based on feedback

**Use Cases**:
- Standard acknowledgments ("We received your maintenance request")
- Emergency contact information
- Office hours and basic policy information
- Fallback when other strategies fail

### 2. RAG-Enhanced Strategy

**Philosophy**: Combine retrieval of relevant property knowledge with AI generation for accurate, contextual responses.

**How it Works**:
```python
def _generate_rag_response(self, query: str, tenant_name: str) -> str:
    # 1. Retrieve relevant context from knowledge base
    context_docs = self.rag_system.retrieve_context(query, k=3)
    context = "\n".join(context_docs)
    
    # 2. Use LLM with retrieved context
    prompt = self.templates['rag'].format(
        context=context,
        question=query,
        tenant_name=tenant_name
    )
    
    return self.llm_manager.generate_response(model_name, prompt)
```

**Knowledge Base Content**:
- Property-specific maintenance procedures
- Local regulations and policies  
- Historical resolution patterns
- Vendor contact information
- Emergency protocols

**Advantages**:
- **High Accuracy**: Responses grounded in factual property information
- **Contextually Relevant**: Uses specific property knowledge
- **Cost Efficient**: Lower token usage than pure LLM
- **Consistent Quality**: Maintains accuracy across similar queries
- **Auditable**: Can trace response sources

**Limitations**:
- **Knowledge Base Dependency**: Quality depends on curated content
- **Setup Complexity**: Requires initial knowledge base creation
- **Update Overhead**: Knowledge base needs maintenance

**Use Cases**:
- Property amenity questions ("What are the pool hours?")
- Maintenance procedures ("How do I reset the garbage disposal?")
- Policy clarifications ("What's the guest parking policy?")
- Vendor information ("Who should I call for appliance repair?")

### 3. LLM-Powered Strategy

**Philosophy**: Leverage large language models for maximum flexibility and human-like responses.

**How it Works**:
```python
def _generate_llm_response(self, model_name: str, email_content: str, tenant_name: str) -> str:
    prompt = self.templates['direct'].format(
        email_content=email_content,
        tenant_name=tenant_name
    )
    
    return self.llm_manager.generate_response(model_name, prompt)
```

**Supported Models**:
- **OpenAI**: GPT-4, GPT-4o, GPT-3.5-turbo
- **Anthropic**: Claude-3 Haiku, Claude-3 Sonnet
- **Local Models**: Llama, Mistral, Qwen via Ollama

**Advantages**:
- **Maximum Flexibility**: Can handle any type of inquiry
- **Natural Language**: Human-like, empathetic responses
- **Context Understanding**: Grasps nuanced situations
- **Creative Solutions**: Can suggest novel approaches
- **Continuous Improvement**: Models improve over time

**Limitations**:
- **Variable Quality**: Output consistency depends on prompt and model
- **Higher Cost**: API usage fees accumulate
- **Potential Hallucination**: May generate incorrect information
- **Rate Limits**: API constraints can slow processing

**Use Cases**:
- Complex tenant complaints requiring empathy
- Unusual maintenance situations
- Negotiation scenarios (lease modifications)
- Sensitive situations (noise complaints between neighbors)

### Multi-Model Strategy Implementation

The system intelligently uses multiple models to provide response diversity:

```python
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
```

### Response Selection and Learning

The system generates multiple responses and allows users to select the best option:

1. **Multiple Options**: Each strategy generates a response option
2. **User Selection**: Property managers choose the most appropriate response
3. **Rating System**: Users can rate responses (1-5 stars)
4. **Modification Support**: Selected responses can be edited before sending
5. **Feedback Loop**: Ratings inform future strategy selection

```python
def select_ai_response(email_id: str, option_id: str, rating: float = None, 
                      modifications: str = None) -> bool:
    # Apply modifications if provided
    final_content = modifications if modifications else selected_option['content']
    
    # Save to replies table with feedback
    reply_data = {
        'email_id': email_id,
        'content': final_content,
        'strategy_used': selected_option['strategy_used'],
        'user_rating': rating,
        'modifications_made': modifications is not None,
        'original_content': selected_option['content'] if modifications else None
    }
```

---

## API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
Currently uses basic configuration-based authentication. See Configuration section for setup.

[API Endpoints Reference](endpoints-reference.md)

## Email Processing Workflow

The email processing workflow is the core automation pipeline that transforms incoming tenant emails into actionable tickets and AI-generated responses.

[Email Processing Workflow](email-processing-workflow.md)

## Ticket Management System

The ticket management system automatically converts email-derived action items into structured maintenance and service tickets with proper categorization, assignment, and tracking.

[Ticket Management](ticket-management.md)

## Database Schema

The system uses TinyDB, a lightweight JSON-based database, providing flexibility and simplicity for development while maintaining structured data relationships.---

[Database Schema Nosql](database-schema.md)

## Configuration & Setup
See README.md from root level

## Test Framework
Checkout use cases and integrations in `app.examples`

## V2 Roadmap - Advanced AI Features
Thank you — based on your documents and the request to **continue the readme with part 10**, here's a **V2 Roadmap** section draft to complete the documentation and include your expectations for dynamic prompting, cached learning, and reinforcement learning based on prior behavior:

---

## 10. V2 Roadmap – Advanced AI Features

The next generation of the Property Management AI Assistant (V2) will introduce adaptive intelligence capabilities that learn and personalize over time. This version will move beyond static prompting and manual selection toward autonomous adaptation.

### Key Enhancements in V2

#### 🔄 1. Dynamic Prompting Engine

* **Objective**: Generate personalized prompts in real time based on tenant profile, context, and past correspondence.
* **Features**:

  * Time-sensitive prompt adjustments (e.g., holidays, business hours)
  * Subject-adaptive phrasing (e.g., urgency or tone based on detected sentiment)
  * Tenant-specific tone (e.g., formal vs. casual based on past interactions)

#### 🧠 2. Cached Learning & Behavioral Memory

* **Objective**: Cache and recall past selections, email types, tenant patterns, and preferred resolutions.
* **Memory Modules**:

  * **Per-Tenant History Cache**: Tracks tenant preferences, typical issues, and prior replies
  * **Template Usage Feedback**: Boosts or suppresses templates based on selection frequency
  * **Category Reinforcement**: Learns mappings between keywords and subcategories from labeled tickets

#### ♻️ 3. Reinforcement Learning from Feedback

* **Objective**: Continuously improve strategy selection and response quality using real-world feedback.
* **Mechanisms**:

  * **User Selection Signals**: Response options chosen by users are positively reinforced
  * **Rating-Driven Rewarding**: Highly rated replies boost the strategy or model's future weight
  * **Edit Feedback Loop**: Modified replies are tracked to guide future phrasing and tone

#### 📊 4. Periodic Behavioral Analysis

* **Objective**: Capture trends and periodic behaviors to guide response prioritization.
* **Examples**:

  * Monthly maintenance surges → proactive prep messaging
  * Seasonal amenity use → preemptive reminders (e.g., pool rules in summer)
  * Rent reminders adapted to prior late-payment history

#### 🧪 5. A/B Strategy Testing Framework

* **Purpose**: Continuously test different strategies for similar inputs to optimize performance
* **Implementation**:

  * Randomized response generation using RAG vs. LLM vs. hybrid
  * Tracking downstream metrics (reply time, ticket creation rate, satisfaction rating)

---

### V2 Proof-of-Concept (PoC) Overview

**Architecture Extension**:

```mermaid
graph TD
    A[Incoming Email] --> B[Email Processor]
    B --> C[Context + History Cache]
    C --> D[Dynamic Prompting Engine]
    D --> E[Multi-Strategy Generator (Template/RAG/LLM)]
    E --> F[AI Responses]
    F --> G[User Interface]

    G --> H[Selection & Feedback]
    H --> I[Learning Reinforcement Module]
    I --> C

    subgraph "Behavioral Memory"
        C1[Per-Tenant Cache]
        C2[Contextual Features]
        C3[Frequency Patterns]
        C --> C1
        C --> C2
        C --> C3
    end
```

**Sample Workflow**:

1. New email arrives.
2. System queries cache: prior issues, preferred response types, rating history.
3. Prompt generator adjusts context (e.g., “again”, “as discussed last month”, etc.).
4. Response candidates are ranked by learned preferences.
5. User selection further informs model via feedback loop.
