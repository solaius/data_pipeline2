from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DocumentChunk(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    chunk_id: str
    content: str
    page_number: Optional[int] = None
    position: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Document(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    doc_id: str
    filename: str
    content_type: str
    status: DocumentStatus
    chunks: List[DocumentChunk] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None

class DocumentEmbedding(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    chunk_id: str
    embedding_provider: str
    embedding: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
