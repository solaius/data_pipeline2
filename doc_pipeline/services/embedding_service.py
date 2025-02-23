from typing import List, Dict, Optional
import aiohttp
from ..models.document import DocumentChunk, DocumentEmbedding
from ..config.settings import settings

class EmbeddingProvider:
    def __init__(self, api_url: str, api_key: str, model_name: str):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        
    async def generate_embedding(self, text: str) -> List[float]:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "model": self.model_name
            }
            
            async with session.post(self.api_url, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to generate embedding: {await response.text()}")
                result = await response.json()
                return result["embedding"]

class EmbeddingService:
    def __init__(self):
        self.providers = {
            "nomic": EmbeddingProvider(
                settings.NOMIC_API_URL,
                settings.NOMIC_API_KEY,
                "nomic-embed-text-v1.5"
            ),
            "granite": EmbeddingProvider(
                settings.GRANITE_API_URL,
                settings.GRANITE_API_KEY,
                "Granite-Embedding-278m-multilingual"
            )
        }
    
    async def generate_embeddings(
        self,
        chunk: DocumentChunk,
        provider_name: str = "nomic"
    ) -> DocumentEmbedding:
        if provider_name not in self.providers:
            raise ValueError(f"Unknown embedding provider: {provider_name}")
        
        provider = self.providers[provider_name]
        embedding = await provider.generate_embedding(chunk.content)
        
        return DocumentEmbedding(
            chunk_id=chunk.chunk_id,
            embedding_provider=provider_name,
            embedding=embedding,
            metadata={
                "model": provider.model_name,
                **chunk.metadata
            }
        )