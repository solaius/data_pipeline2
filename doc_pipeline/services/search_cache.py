import json
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, UTC
import redis
from ..config.settings import settings

class SearchCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        self.cache_ttl = 3600  # 1 hour by default
    
    def _get_cache_key(
        self,
        query_embedding: List[float],
        provider: str,
        filters: Optional[Dict] = None,
        k: int = 10
    ) -> str:
        # Create a deterministic cache key from the search parameters
        key_parts = [
            str(query_embedding),
            provider,
            str(filters) if filters else "",
            str(k)
        ]
        key_str = "|".join(key_parts)
        return f"search_cache:{hashlib.sha256(key_str.encode()).hexdigest()}"
    
    async def get_cached_results(
        self,
        query_embedding: List[float],
        provider: str,
        filters: Optional[Dict] = None,
        k: int = 10
    ) -> Optional[List[Dict]]:
        cache_key = self._get_cache_key(query_embedding, provider, filters, k)
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def store_results(
        self,
        query_embedding: List[float],
        provider: str,
        results: List[Dict],
        filters: Optional[Dict] = None,
        k: int = 10
    ) -> None:
        cache_key = self._get_cache_key(query_embedding, provider, filters, k)
        self.redis_client.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(results)
        )
    
    async def invalidate_cache(self, pattern: str = "search_cache:*") -> None:
        """Invalidate all search cache entries matching the pattern."""
        cursor = 0
        while True:
            cursor, keys = self.redis_client.scan(cursor, match=pattern)
            if keys:
                self.redis_client.delete(*keys)
            if cursor == 0:
                break