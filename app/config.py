import os
from typing import Optional
from pydantic_settings import BaseSettings
import dotenv

dotenv.load_dotenv()

class Settings(BaseSettings):
    # Gmail Configuration
    gmail_imap_host: str = os.getenv("GMAIL_IMAP_HOST", "") 
    gmail_username: str = os.getenv("GMAIL_USERNAME", "")
    gmail_password: str = os.getenv("GMAIL_PASSWORD", "")
    
    # OpenAI Configuration 
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Anthropic Configuration
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # General Configuration
    log_level: str = os.getenv("LOG_LEVEL")
    
    # LLM Settings
    preferred_models:list[str] = ['gpt-4o-mini', 'claude-3-sonnet', 'qwen2.5']
    use_local_models: bool = False # Local models are not supported in heroku environment due to environment constraints
    local_ai_base_url: str = os.getenv("LOCAL_AI_BASE_URL", "http://0.0.0.0:11434")
    
    
    def __str__(self):
        test_load = os.getenv("LOADER_VERIFICATION")
        msg = f"Load verification will show as: <{test_load}>"
        print(msg)
        return msg
        
CONFIG = Settings()
