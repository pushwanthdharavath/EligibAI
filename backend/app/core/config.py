from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "EligibAI"
    
    # Database Settings
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/eligibai"
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379"
    
    # LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    MODEL_NAME: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None
    
    # Web Search Settings
    SERPER_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None
    
    # Langfuse Settings
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()