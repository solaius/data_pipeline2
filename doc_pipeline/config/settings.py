from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
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
    ELASTICSEARCH_USE_SSL: bool = os.getenv("ELASTICSEARCH_USE_SSL", "false").lower() == "true"
    
    # Redis Settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Embedding Settings
    NOMIC_API_KEY: str = os.getenv("NOMIC_API_KEY", "")
    NOMIC_API_URL: str = os.getenv("NOMIC_API_URL", "https://api.nomic.ai/v1/embeddings")
    NOMIC_MODEL_NAME: str = os.getenv("NOMIC_MODEL_NAME", "nomic-embed-text-v1.5")
    NOMIC_EMBEDDING_DIMS: int = 768
    
    GRANITE_API_KEY: str = os.getenv("GRANITE_API_KEY", "")
    GRANITE_API_URL: str = os.getenv("GRANITE_API_URL", "https://api.granite.ai/v1/embeddings")
    GRANITE_MODEL_NAME: str = os.getenv("GRANITE_MODEL_NAME", "Granite-Embedding-278m-multilingual")
    GRANITE_EMBEDDING_DIMS: int = 768
    
    # Embedding Cache Settings
    EMBEDDING_CACHE_TTL: int = int(os.getenv("EMBEDDING_CACHE_TTL", "86400"))  # 24 hours
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    
    # Document Processing Settings
    MAX_CHUNK_SIZE: int = 1000
    BATCH_SIZE: int = 50
    CHUNK_OVERLAP: int = 50
    DEFAULT_CHUNKING_STRATEGY: str = "hybrid"
    TOKENIZER_NAME: str = "BAAI/bge-small-en-v1.5"

    # Chunking Settings
    CHUNK_MIN_SIZE: int = 100
    CHUNK_MAX_SIZE: int = 2000
    SENTENCE_OVERLAP: bool = True
    PRESERVE_MARKDOWN_STRUCTURE: bool = True
    
    model_config = ConfigDict(case_sensitive=True)

settings = Settings()