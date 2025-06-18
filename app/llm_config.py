from .config import CONFIG
# Initialize system with multiple model support
llm_config = {
    'openai_api_key': CONFIG.openai_api_key,
    'anthropic_api_key': CONFIG.anthropic_api_key,
    'use_local_models': CONFIG.use_local_models, # Enable local models via Ollama
    'base_url': CONFIG.local_ai_base_url,
    'preferred_models': ['gpt-4o', 'claude-3-sonnet', 'qwen2.5'],  # Model priority
}