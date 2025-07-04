# Configuration & Setup Guide

## Environment Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Gmail Configuration
GMAIL_IMAP_HOST=imap.gmail.com
GMAIL_USERNAME=your-property-email@gmail.com
GMAIL_PASSWORD=your-app-specific-password

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic Configuration  
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# Local AI Configuration
USE_LOCAL_MODELS=true
LOCAL_AI_BASE_URL=http://localhost:11434

# Application Configuration (Optional)
LOG_LEVEL=INFO
LOADER_VERIFICATION=config_loaded_successfully

# Database Configuration (Optional)
DATABASE_PATH=email_system.json
BACKUP_INTERVAL_HOURS=24
MAX_BACKUP_COUNT=30

# API Configuration (Optional)
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
CORS_ORIGINS=["*"]

# Notification Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=notifications@property.com
SMTP_PASSWORD=smtp-app-password
```

### 2. Configuration Classes

**Main Configuration (`config.py`)**
```python
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
import dotenv

dotenv.load_dotenv()

class Settings(BaseSettings):
    # Gmail Configuration
    gmail_imap_host: str = os.getenv("GMAIL_IMAP_HOST", "imap.gmail.com")
    gmail_username: str = os.getenv("GMAIL_USERNAME", "")
    gmail_password: str = os.getenv("GMAIL_PASSWORD", "")
    
    # AI Model Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Local AI Configuration
    use_local_models: bool = os.getenv("USE_LOCAL_MODELS", "false").lower() == "true"
    local_ai_base_url: str = os.getenv("LOCAL_AI_BASE_URL", "http://localhost:11434")
    
    # Model Preferences
    preferred_models: List[str] = ['gpt-4o', 'claude-3-sonnet', 'qwen2.5']

    class Config:
        env_file = ".env"
        case_sensitive = False

CONFIG = Settings()
```

**LLM Configuration (`llm_config.py`)**
```python
from .config import CONFIG

llm_config = {
    'openai_api_key': CONFIG.openai_api_key,
    'anthropic_api_key': CONFIG.anthropic_api_key,
    'use_local_models': CONFIG.use_local_models,
    'base_url': CONFIG.local_ai_base_url,
}
```

## Installation & Dependencies

### 1. Python Environment Setup

```bash
# Create virtual environment
python -m venv property-ai-env

# Activate environment (Linux/Mac)
source property-ai-env/bin/activate

# Activate environment (Windows)
property-ai-env\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 2. Core Dependencies

**Requirements.txt**
```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
tinydb==4.8.0

# Email Processing
imaplib2==3.6
email-validator==2.1.0

# AI/ML Libraries
langchain==0.1.0
langchain-openai==0.0.2
langchain-anthropic==0.0.1
langchain-ollama==0.0.1
langchain-community==0.0.10
openai==1.6.1
anthropic==0.8.1

# Vector Store & Embeddings
faiss-cpu==1.7.4
sentence-transformers==2.2.2

# Utilities
python-dotenv==1.0.0
python-multipart==0.0.6
schedule==1.2.0
requests==2.31.0

# Development & Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
black==23.11.0
flake8==6.1.0

# Optional Performance
psutil==5.9.6  # For system monitoring
slowapi==0.1.9  # For rate limiting
```

### 3. Installation Script

**setup.py**
```python
#!/usr/bin/env python3
"""
Installation and setup script for Property Management AI Assistant
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
    ])

def setup_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "backups",
        "logs", 
        "data",
        "tests/reports",
        "config"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✓ Created {dir_path}")

def setup_environment_file():
    """Create environment file from template"""
    print("⚙️ Setting up environment configuration...")
    
    env_template = """# Gmail Configuration
GMAIL_IMAP_HOST=imap.gmail.com
GMAIL_USERNAME=your-property-email@gmail.com
GMAIL_PASSWORD=your-app-specific-password

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic Configuration  
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# Local AI Configuration
USE_LOCAL_MODELS=true
LOCAL_AI_BASE_URL=http://localhost:11434

# Application Configuration
LOG_LEVEL=INFO
LOADER_VERIFICATION=config_loaded_successfully
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_template)
        print("   ✓ Created .env file template")
        print("   ⚠️ Please edit .env with your actual API keys and credentials")
    else:
        print("   ℹ️ .env file already exists")

def setup_logging():
    """Setup logging configuration"""
    print("📝 Setting up logging...")
    
    logging_config = """
import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    \"\"\"Configure application logging\"\"\"
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # Console handler
            logging.StreamHandler(),
            
            # File handler with rotation
            logging.handlers.RotatingFileHandler(
                "logs/property_ai.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            
            # Error file handler
            logging.handlers.RotatingFileHandler(
                "logs/errors.log",
                maxBytes=5*1024*1024,   # 5MB
                backupCount=3,
                level=logging.ERROR
            )
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
"""
    
    with open("config/logging_config.py", "w") as f:
        f.write(logging_config)
    print("   ✓ Created logging configuration")

def check_system_requirements():
    """Check system requirements"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("   ❌ Python 3.8+ required")
        return False
    print(f"   ✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check available disk space
    import shutil
    free_space_gb = shutil.disk_usage('.').free / (1024**3)
    if free_space_gb < 1:
        print("   ⚠️ Low disk space (< 1GB free)")
    else:
        print(f"   ✓ Disk space: {free_space_gb:.1f}GB free")
    
    return True

def setup_ollama():
    """Setup Ollama for local models (optional)"""
    print("🤖 Setting up Ollama for local models...")
    
    try:
        # Check if Ollama is installed
        result = subprocess.run(["ollama", "version"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✓ Ollama is installed")
            
            # Pull recommended model
            print("   📥 Pulling recommended model (qwen2.5:14b)...")
            subprocess.run(["ollama", "pull", "qwen2.5:14b"])
            print("   ✓ Model pulled successfully")
            
        else:
            print("   ⚠️ Ollama not found. Install from https://ollama.ai")
            
    except FileNotFoundError:
        print("   ⚠️ Ollama not found. Install from https://ollama.ai")

def create_systemd_service():
    """Create systemd service file for production deployment"""
    print("🔧 Creating systemd service file...")
    
    service_content = f"""[Unit]
Description=Property Management AI Assistant
After=network.target

[Service]
Type=exec
User={os.getenv('USER', 'property-ai')}
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/property-ai-env/bin
ExecStart={os.getcwd()}/property-ai-env/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    
    with open("property-ai.service", "w") as f:
        f.write(service_content)
    
    print("   ✓ Created property-ai.service")
    print("   ℹ️ To install: sudo cp property-ai.service /etc/systemd/system/")
    print("   ℹ️ To enable: sudo systemctl enable property-ai")

def run_initial_tests():
    """Run basic tests to verify installation"""
    print("🧪 Running initial tests...")
    
    try:
        # Test imports
        import fastapi
        import tinydb
        import langchain
        print("   ✓ Core dependencies imported successfully")
        
        # Test database creation
        from app.services.turso_tinydb import TinyDB
        test_db = TinyDB('test_db.json')
        test_db.insert({'test': 'data'})
        test_db.close()
        os.remove('test_db.json')
        print("   ✓ Database functionality working")
        
        # Test configuration loading
        from app.config import CONFIG
        print(f"   ✓ Configuration loaded: {CONFIG.log_level}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Property Management AI Assistant Setup")
    print("=" * 50)
    
    if not check_system_requirements():
        print("❌ System requirements not met")
        sys.exit(1)
    
    setup_directories()
    install_requirements()
    setup_environment_file()
    setup_logging()
    setup_ollama()
    create_systemd_service()
    
    if run_initial_tests():
        print("\n✅ Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Edit .env file with your API keys and credentials")
        print("2. Test Gmail connection: python -m app.test_gmail")
        print("3. Start the server: uvicorn main:app --reload")
        print("4. Open http://localhost:8000/docs for API documentation")
    else:
        print("\n❌ Setup completed with errors")
        print("Please check the error messages above and resolve issues")

if __name__ == "__main__":
    main()
```

## Gmail Setup & Authentication

### 1. Gmail App Password Setup

```bash
# Steps to create Gmail App Password:
# 1. Enable 2-Factor Authentication on your Google account
# 2. Go to Google Account settings > Security > 2-Step Verification
# 3. Generate App Password for "Mail" application
# 4. Use the generated 16-character password in GMAIL_PASSWORD
```

### 2. Gmail Connection Test

**test_gmail.py**
```python
#!/usr/bin/env python3
"""
Test Gmail IMAP connection and basic functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.config import CONFIG
from app.plugin.email.gmail_client import GmailClient

def test_gmail_connection():
    """Test Gmail IMAP connection"""
    print("🔗 Testing Gmail connection...")
    
    if not CONFIG.gmail_username or not CONFIG.gmail_password:
        print("❌ Gmail credentials not configured")
        print("Please set GMAIL_USERNAME and GMAIL_PASSWORD in .env file")
        return False
    
    try:
        client = GmailClient()
        
        # Test connection
        if client.connect():
            print("✅ Gmail connection successful")
            
            # Test fetch recent emails
            recent_emails = client.fetch_recent(count=5)
            print(f"✅ Fetched {len(recent_emails)} recent emails")
            
            # Show email preview
            for i, email in enumerate(recent_emails[:3], 1):
                print(f"   {i}. From: {email['sender']}")
                print(f"      Subject: {email['subject']}")
                print(f"      Date: {email.get('date', 'Unknown')}")
            
            client.disconnect()
            return True
        else:
            print("❌ Gmail connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Gmail test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gmail_connection()
    sys.exit(0 if success else 1)
```

## AI Model Configuration

### 1. Model Provider Setup

**OpenAI Setup**
```python
# Test OpenAI connection
def test_openai_connection():
    """Test OpenAI API connection"""
    
    if not CONFIG.openai_api_key:
        print("⚠️ OpenAI API key not configured")
        return False
    
    try:
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            api_key=CONFIG.openai_api_key,
            model="gpt-3.5-turbo",
            max_tokens=100
        )
        
        response = llm.invoke("Test connection")
        print("✅ OpenAI connection successful")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False
```

**Anthropic Setup**
```python
# Test Anthropic connection
def test_anthropic_connection():
    """Test Anthropic API connection"""
    
    if not CONFIG.anthropic_api_key:
        print("⚠️ Anthropic API key not configured")
        return False
    
    try:
        from langchain_anthropic import ChatAnthropic
        
        llm = ChatAnthropic(
            api_key=CONFIG.anthropic_api_key,
            model="claude-3-haiku-20240307",
            max_tokens=100
        )
        
        response = llm.invoke("Test connection")
        print("✅ Anthropic connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Anthropic connection failed: {e}")
        return False
```

**Local Models (Ollama) Setup**
```python
# Test Ollama connection
def test_ollama_connection():
    """Test Ollama local model connection"""
    
    if not CONFIG.use_local_models:
        print("ℹ️ Local models disabled")
        return True
    
    try:
        from langchain_ollama import ChatOllama
        
        llm = ChatOllama(
            model="qwen2.5:14b",
            base_url=CONFIG.local_ai_base_url,
            num_ctx=1000
        )
        
        response = llm.invoke("Test connection")
        print("✅ Ollama connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        print("Make sure Ollama is running: ollama serve")
        return False
```

### 2. Model Performance Configuration

**model_config.py**
```python
# Model-specific configurations
MODEL_CONFIGS = {
    'openai_gpt4o': {
        'max_tokens': 2000,
        'temperature': 0.7,
        'timeout': 30,
        'rate_limit': 3000,  # tokens per minute
        'cost_per_1k_tokens': 0.03
    },
    'anthropic_claude3_sonnet': {
        'max_tokens': 2000,
        'temperature': 0.7,
        'timeout': 30,
        'rate_limit': 2000,
        'cost_per_1k_tokens': 0.015
    },
    'local_qwen2.5': {
        'max_tokens': 2000,
        'temperature': 0.7,
        'timeout': 45,
        'rate_limit': None,  # No external rate limit
        'cost_per_1k_tokens': 0.0
    }
}

# Strategy selection preferences
STRATEGY_PREFERENCES = {
    'urgent_emails': {
        'primary': 'template',
        'fallback': 'llm',
        'timeout': 5
    },
    'complex_emails': {
        'primary': 'llm',
        'fallback': 'rag',
        'timeout': 30
    },
    'routine_emails': {
        'primary': 'rag',
        'fallback': 'template',
        'timeout': 15
    }
}
```

## Production Deployment

### 1. Docker Configuration

**Dockerfile**
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs backups data

# Create non-root user
RUN useradd -m -u 1001 property-ai
RUN chown -R property-ai:property-ai /app
USER property-ai

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**
```yaml
version: '3.8'

services:
  property-ai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./backups:/app/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Ollama service for local models
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama_data:
```

### 2. Production Configuration

**production.env**
```bash
# Production environment variables
LOG_LEVEL=WARNING
API_WORKERS=4
MAX_CONCURRENT_EMAILS=50

# Security settings
CORS_ORIGINS=["https://your-domain.com"]
API_KEY_REQUIRED=true
API_KEY_HEADER=X-API-Key

# Performance settings
DATABASE_CACHE_SIZE=1000
EMAIL_FETCH_INTERVAL=300  # 5 minutes
CLEANUP_INTERVAL=86400    # 24 hours

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=60

# Backup settings
BACKUP_TO_S3=true
S3_BUCKET=property-ai-backups
S3_REGION=us-east-1
```

### 3. Nginx Reverse Proxy

**nginx.conf**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for AI processing
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }

    # Rate limiting
    location /api/v1/workflows/ {
        limit_req zone=workflow burst=5 nodelay;
        proxy_pass http://localhost:8000/api/v1/workflows/;
    }
}

# Rate limiting configuration
http {
    limit_req_zone $binary_remote_addr zone=workflow:10m rate=10r/m;
}
```

### 4. Monitoring & Logging

**monitoring.py**
```python
import logging
import psutil
import time
from datetime import datetime
from typing import Dict, Any

class SystemMonitor:
    """Monitor system health and performance"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        
        return {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': time.time() - self.start_time,
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1)
        }
    
    def log_request(self, success: bool = True):
        """Log API request"""
        self.request_count += 1
        if not success:
            self.error_count += 1

# Prometheus metrics (optional)
try:
    from prometheus_client import Counter, Histogram, Gauge
    
    REQUEST_COUNT = Counter('api_requests_total', 'Total API requests')
    REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration')
    ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')
    
except ImportError:
    # Prometheus not available
    pass
```

## Security Configuration

### 1. API Security

**security.py**
```python
import hashlib
import secrets
from fastapi import HTTPException, Depends, Header
from typing import Optional

# API Key management
API_KEYS = {
    "admin": "admin_api_key_here",
    "readonly": "readonly_api_key_here"
}

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key"""
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    if x_api_key not in API_KEYS.values():
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return x_api_key

# Input validation
def validate_email_input(email_data: dict):
    """Validate email input for security"""
    
    # Check for potential injection attacks
    dangerous_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
    
    content = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
    
    for pattern in dangerous_patterns:
        if pattern.lower() in content.lower():
            raise HTTPException(status_code=400, detail="Invalid content detected")
    
    return email_data

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("100/minute")
async def rate_limited_endpoint():
    """Example rate-limited endpoint"""
    pass
```

### 2. Data Privacy

**privacy.py**
```python
import hashlib
from typing import Dict, Any

def anonymize_email_data(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Anonymize sensitive email data for logging/analytics"""
    
    anonymized = email_data.copy()
    
    # Hash email addresses
    if 'sender' in anonymized:
        anonymized['sender_hash'] = hashlib.sha256(
            anonymized['sender'].encode()
        ).hexdigest()[:16]
        anonymized['sender'] = f"user_{anonymized['sender_hash']}"
    
    # Truncate content for privacy
    if 'body' in anonymized:
        anonymized['body'] = anonymized['body'][:100] + "..." if len(anonymized['body']) > 100 else anonymized['body']
    
    return anonymized

def gdpr_data_export(tenant_email: str) -> Dict[str, Any]:
    """Export all data for a tenant (GDPR compliance)"""
    
    from app.models import emails_table, replies_table, tenants_table
    from app.services.turso_tinydb import Query
    
    Email = Query()
    Reply = Query()
    Tenant = Query()
    
    # Get all tenant data
    tenant_data = tenants_table.get(Tenant.email == tenant_email)
    tenant_emails = emails_table.search(Email.sender == tenant_email)
    
    email_ids = [email['id'] for email in tenant_emails]
    tenant_replies = []
    
    for email_id in email_ids:
        replies = replies_table.search(Reply.email_id == email_id)
        tenant_replies.extend(replies)
    
    return {
        'tenant_info': tenant_data,
        'emails': tenant_emails,
        'replies': tenant_replies,
        'export_date': datetime.now().isoformat()
    }

def gdpr_data_deletion(tenant_email: str) -> bool:
    """Delete all data for a tenant (GDPR right to be forgotten)"""
    
    # Implementation would delete all tenant data
    # This is a placeholder for the actual implementation
    pass
```