import json
from typing import List, Optional
import redis
from ..config.settings import settings
from ..models.document import DocumentEmbedding

class EmbeddingCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        
    def _get_cache_key(self, chunk_id: str, provider: str) -> str:
        return f"embedding:{provider}:{chunk_id}"
    
    async def get_embedding(self, chunk_id: str, provider: str) -> Optional[DocumentEmbedding]:
        cache_key = self._get_cache_key(chunk_id, provider)
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            data = json.loads(cached_data)
            return DocumentEmbedding(**data)
        return None
    
    async def store_embedding(self, embedding: DocumentEmbedding) -> None:
        cache_key = self._get_cache_key(embedding.chunk_id, embedding.embedding_provider)
        self.redis_client.set(
            cache_key,
            embedding.model_dump_json(),
            ex=86400  # Cache for 24 hours
        )
    
    async def delete_embedding(self, chunk_id: str, provider: str) -> None:
        cache_key = self._get_cache_key(chunk_id, provider)
        self.redis_client.delete(cache_key)