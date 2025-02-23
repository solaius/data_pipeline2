from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Document Processing Pipeline"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Elasticsearch Settings
    ELASTICSEARCH_HOST: str = os.getenv("ELASTICSEARCH_HOST", "localhost")
    ELASTICSEARCH_PORT: int = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    ELASTICSEARCH_USERNAME: Optional[str] = os.getenv("ELASTICSEARCH_USERNAME")
    ELASTICSEARCH_PASSWORD: Optional[str] = os.getenv("ELASTICSEARCH_PASSWORD")
    
    # Redis Settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Embedding Settings
    NOMIC_API_KEY: str = os.getenv("NOMIC_API_KEY", "")
    NOMIC_API_URL: str = os.getenv("NOMIC_API_URL", "")
    GRANITE_API_KEY: str = os.getenv("GRANITE_API_KEY", "")
    GRANITE_API_URL: str = os.getenv("GRANITE_API_URL", "")
    
    # Document Processing Settings
    MAX_CHUNK_SIZE: int = 1000
    BATCH_SIZE: int = 50
    
    class Config:
        case_sensitive = True

settings = Settings()