from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC
from enum import Enum
import base64  # Required for encoding/decoding

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
    content: str
    status: DocumentStatus
    chunks: List[DocumentChunk] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error_message: Optional[str] = None

    # 🔹 Automatically encode content to Base64 (if storing binary data)
    def encode_content(self):
        if isinstance(self.content, bytes):
            self.content = base64.b64encode(self.content).decode("utf-8")  # Store as Base64 string

    # 🔹 Decode Base64 back into bytes (when needed)
    def decode_content(self) -> bytes:
        try:
            return base64.b64decode(self.content.encode("utf-8"))
        except Exception:
            return self.content  # If already string, return as is

class DocumentEmbedding(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    chunk_id: str
    embedding_provider: str
    embedding: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
