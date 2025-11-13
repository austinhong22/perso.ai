"""Infrastructure configuration - environment-driven settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "FastAPI Service"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API
    api_prefix: str = "/api/v1"
    
    # Security
    secret_key: Optional[str] = None
    
    # Embedding Model
    embed_model: str = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"
    
    # Hallucination Guard
    similarity_threshold: float = 0.8
    enable_source_reference: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()



