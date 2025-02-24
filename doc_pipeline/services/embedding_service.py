from typing import List, Dict, Optional, Tuple
import aiohttp
import asyncio
from datetime import datetime, UTC
import logging
from prometheus_client import Counter, Histogram
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.document import DocumentChunk, DocumentEmbedding
from ..config.settings import settings
from .embedding_cache import EmbeddingCache

# Prometheus metrics
EMBEDDING_REQUESTS = Counter(
    'embedding_requests_total',
    'Total number of embedding requests',
    ['provider', 'status']
)
EMBEDDING_LATENCY = Histogram(
    'embedding_latency_seconds',
    'Time spent generating embeddings',
    ['provider']
)

logger = logging.getLogger(__name__)

class EmbeddingError(Exception):
    def __init__(self, message: str, provider: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code

class BaseEmbeddingProvider:
    def __init__(self, api_url: str, api_key: str, model_name: str):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=(aiohttp.ClientError, EmbeddingError),
        retry_error_callback=lambda retry_state: None  # Return None on final attempt
    )
    async def _make_request(self, text: str) -> Dict:
        session = await self._get_session()
        headers = self._get_headers()
        payload = self._get_payload(text)
        
        try:
            async with session.post(self.api_url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise EmbeddingError(
                        f"Failed to generate embedding: {error_text}",
                        self.model_name,
                        response.status
                    )
                return await response.json()
        except aiohttp.ClientError as e:
            raise EmbeddingError(
                f"Network error while generating embedding: {str(e)}",
                self.model_name
            )
    
    async def generate_embedding(self, text: str) -> List[float]:
        result = await self._make_request(text)
        return self._parse_response(result)
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _get_payload(self, text: str) -> Dict:
        return {
            "text": text,
            "model": self.model_name
        }
    
    def _parse_response(self, response: Dict) -> List[float]:
        return response["embedding"]
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

class NomicEmbeddingProvider(BaseEmbeddingProvider):
    def _get_payload(self, text: str) -> Dict:
        return {
            "texts": [text],  # Nomic expects a list of texts
            "model": self.model_name,
            "task_type": "search"  # Optimize for search
        }
    
    def _parse_response(self, response: Dict) -> List[float]:
        # Nomic returns a list of embeddings, we take the first one
        return response["embeddings"][0]

class GraniteEmbeddingProvider(BaseEmbeddingProvider):
    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,  # Granite uses a different header
            "Content-Type": "application/json"
        }
    
    def _get_payload(self, text: str) -> Dict:
        return {
            "input": text,
            "model": self.model_name,
            "encoding_format": "float"  # Ensure we get float values
        }
    
    def _parse_response(self, response: Dict) -> List[float]:
        return response["data"][0]["embedding"]  # Granite has a different response structure

class EmbeddingService:
    def __init__(self):
        self.providers = {
            "nomic": NomicEmbeddingProvider(
                settings.NOMIC_API_URL,
                settings.NOMIC_API_KEY,
                settings.NOMIC_MODEL_NAME
            ),
            "granite": GraniteEmbeddingProvider(
                settings.GRANITE_API_URL,
                settings.GRANITE_API_KEY,
                settings.GRANITE_MODEL_NAME
            )
        }
        self.cache = EmbeddingCache()
        self.cache.cache_ttl = settings.EMBEDDING_CACHE_TTL
        
    async def _generate_single_embedding(
        self,
        chunk: DocumentChunk,
        provider_name: str,
        provider: BaseEmbeddingProvider
    ) -> Tuple[DocumentEmbedding, bool]:
        # Check cache first
        cached_embedding = await self.cache.get_embedding(chunk.chunk_id, provider_name)
        if cached_embedding:
            EMBEDDING_REQUESTS.labels(provider=provider_name, status="cache_hit").inc()
            return cached_embedding, True
            
        # Generate new embedding
        start_time = datetime.now(UTC)
        try:
            embedding = await provider.generate_embedding(chunk.content)
            EMBEDDING_REQUESTS.labels(provider=provider_name, status="success").inc()
            
            doc_embedding = DocumentEmbedding(
                chunk_id=chunk.chunk_id,
                embedding_provider=provider_name,
                embedding=embedding,
                metadata={
                    "model": provider.model_name,
                    **chunk.metadata
                }
            )
            
            # Cache the result
            await self.cache.store_embedding(doc_embedding)
            
            # Record latency
            latency = (datetime.now(UTC) - start_time).total_seconds()
            EMBEDDING_LATENCY.labels(provider=provider_name).observe(latency)
            
            return doc_embedding, False
            
        except Exception as e:
            EMBEDDING_REQUESTS.labels(provider=provider_name, status="error").inc()
            logger.error(f"Error generating embedding for chunk {chunk.chunk_id}: {str(e)}")
            raise
    
    async def generate_embeddings(
        self,
        chunks: List[DocumentChunk],
        provider_name: str = "nomic",
        batch_size: Optional[int] = None
    ) -> List[DocumentEmbedding]:
        batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        if provider_name not in self.providers:
            raise ValueError(f"Unknown embedding provider: {provider_name}")
        
        provider = self.providers[provider_name]
        results = []
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            tasks = [
                self._generate_single_embedding(chunk, provider_name, provider)
                for chunk in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for chunk, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to generate embedding for chunk {chunk.chunk_id}: {str(result)}")
                    continue
                    
                embedding, was_cached = result
                results.append(embedding)
        
        return results
    
    async def close(self):
        await asyncio.gather(*[
            provider.close() for provider in self.providers.values()
        ])