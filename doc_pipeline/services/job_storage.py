from elasticsearch import AsyncElasticsearch
from typing import Optional, List, Dict
import json
from datetime import datetime, UTC
import redis

from ..models.job import Job, JobStatus
from ..config.settings import settings
from ..utils.logging import logger

class JobStorage:
    def __init__(self):
         # Ensure scheme is explicitly added
        es_host = settings.ELASTICSEARCH_HOST
        if not es_host.startswith("http://") and not es_host.startswith("https://"):
            scheme = "https" if settings.ELASTICSEARCH_USE_SSL else "http"
            es_host = f"{scheme}://{es_host}"
        
        self.es = AsyncElasticsearch(
            hosts=[f"{es_host}:{settings.ELASTICSEARCH_PORT}"],
            basic_auth=(
                settings.ELASTICSEARCH_USERNAME,
                settings.ELASTICSEARCH_PASSWORD
            ) if settings.ELASTICSEARCH_USERNAME else None
        )
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )
        self.index_name = "jobs"
    
    async def initialize(self):
        if not await self.es.indices.exists(index=self.index_name):
            await self.create_index()
    
    async def create_index(self):
        settings = {
            "mappings": {
                "properties": {
                    "job_id": {"type": "keyword"},
                    "job_type": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "metadata": {"type": "object"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "error_message": {"type": "text"}
                }
            }
        }
        await self.es.indices.create(index=self.index_name, body=settings)
        logger.info(f"Created index: {self.index_name}")
    
    async def add_job(self, job: Job) -> None:
        doc = job.model_dump()  # ✅ Use model_dump() instead of dict()
        
        # Ensure 'updated_at' exists before accessing it
        doc["created_at"] = doc["created_at"].isoformat()
        doc["updated_at"] = doc.get("updated_at", datetime.now(UTC)).isoformat()  # ✅ Prevent KeyError

        # Store in Elasticsearch
        await self.es.index(
            index=self.index_name,
            id=job.job_id,
            body=doc
        )

        # Cache in Redis with 1-hour expiry
        self.redis.setex(
            f"job:{job.job_id}",
            3600,  # 1 hour
            json.dumps(doc)
        )
        logger.info(f"Stored job: {job.job_id}")
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        # Try Redis first
        cached = self.redis.get(f"job:{job_id}")
        if cached:
            logger.info(f"Retrieved job from cache: {job_id}")
            data = json.loads(cached)
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            return Job(**data)
        
        # Fallback to Elasticsearch
        try:
            doc = await self.es.get(index=self.index_name, id=job_id)
            if doc["found"]:
                logger.info(f"Retrieved job from ES: {job_id}")
                data = doc["_source"]
                data["created_at"] = datetime.fromisoformat(data["created_at"])
                data["updated_at"] = datetime.fromisoformat(data["updated_at"])
                return Job(**data)
        except Exception as e:
            logger.error(f"Error retrieving job {job_id}: {str(e)}")
        
        return None
    
    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None
    ) -> None:
        update_body = {
            "doc": {
                "status": status,
                "updated_at": datetime.now(UTC).isoformat(),
                "error_message": error_message
            }
        }
        
        # Update Elasticsearch
        await self.es.update(
            index=self.index_name,
            id=job_id,
            body=update_body
        )
        
        # Update Redis if cached
        cached = self.redis.get(f"job:{job_id}")
        if cached:
            job_data = json.loads(cached)
            job_data.update(update_body["doc"])
            self.redis.setex(
                f"job:{job_id}",
                3600,  # 1 hour
                json.dumps(job_data)
            )
        
        logger.info(f"Updated job status: {job_id} -> {status}")
    
    async def close(self):
        await self.es.close()
        self.redis.close()