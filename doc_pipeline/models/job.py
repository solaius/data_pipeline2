from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(str, Enum):
    DOCUMENT_PROCESSING = "document_processing"
    EMBEDDING_GENERATION = "embedding_generation"
    INDEX_UPDATE = "index_update"
    BATCH_PROCESSING = "batch_processing"

class Job(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)  # Allow arbitrary types
    
    job_id: str
    job_type: JobType
    status: JobStatus
    priority: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Fixed 'any' -> 'Any'
    progress: float = 0.0
    total_items: int = 0
    processed_items: int = 0

class JobResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    job_id: str
    status: JobStatus
    result: Optional[Dict[str, Any]] = None  # Fixed 'any' -> 'Any'
    error_message: Optional[str] = None
