from elasticsearch import AsyncElasticsearch
from typing import List, Dict, Optional
from ..models.document import DocumentEmbedding
from ..config.settings import settings

class VectorStorage:
    def __init__(self):
        self.es = AsyncElasticsearch(
            hosts=[f"{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
            basic_auth=(
                settings.ELASTICSEARCH_USERNAME,
                settings.ELASTICSEARCH_PASSWORD
            ) if settings.ELASTICSEARCH_USERNAME else None
        )
        self.index_name = "document_embeddings"
    
    async def initialize(self):
        if not await self.es.indices.exists(index=self.index_name):
            await self.create_index()
    
    async def create_index(self):
        settings = {
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "embedding_provider": {"type": "keyword"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 768,  # Adjust based on embedding dimension
                        "index": True,
                        "similarity": "cosine"
                    },
                    "metadata": {"type": "object"},
                    "created_at": {"type": "date"}
                }
            }
        }
        await self.es.indices.create(index=self.index_name, body=settings)
    
    async def store_embedding(self, embedding: DocumentEmbedding):
        doc = embedding.dict()
        await self.es.index(
            index=self.index_name,
            id=f"{embedding.chunk_id}_{embedding.embedding_provider}",
            body=doc
        )
    
    async def search_similar(
        self,
        query_embedding: List[float],
        provider: str,
        k: int = 10
    ) -> List[Dict]:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "embedding_provider": provider
                            }
                        },
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                    "params": {"query_vector": query_embedding}
                                }
                            }
                        }
                    ]
                }
            },
            "size": k
        }
        
        response = await self.es.search(index=self.index_name, body=query)
        return [hit["_source"] for hit in response["hits"]["hits"]]
    
    async def close(self):
        await self.es.close()