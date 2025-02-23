from typing import List, Optional, Dict
import asyncio
from datetime import datetime, timezone
import uuid
import tempfile
import os

from ..models.document import Document, DocumentChunk, DocumentStatus
from ..models.job import Job, JobStatus, JobType
from ..config.settings import settings
from ..utils.logging import logger
from .document_storage import DocumentStorage
from .docling_service import DoclingService

class DocumentProcessor:
    def __init__(self):
        self.processing_queue = asyncio.Queue()
        self._is_running = False
        self.storage = DocumentStorage()
        self.docling = DoclingService()
    
    async def start(self):
        if self._is_running:
            return
        
        await self.storage.initialize()
        self._is_running = True
        asyncio.create_task(self._process_queue())
        logger.info("Document processor started")
    
    async def stop(self):
        self._is_running = False
        await self.storage.close()
        logger.info("Document processor stopped")
        
    async def submit_document(self, content: bytes, filename: str, content_type: str) -> Document:
        doc_id = str(uuid.uuid4())
        document = Document(
            doc_id=doc_id,
            filename=filename,
            content_type=content_type,
            status=DocumentStatus.PENDING
        )
        
        # Save the document content to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        job = Job(
            job_id=str(uuid.uuid4()),
            job_type=JobType.DOCUMENT_PROCESSING,
            status=JobStatus.PENDING,
            metadata={
                "doc_id": doc_id,
                "temp_file": temp_path
            }
        )
        
        # Store the document metadata
        await self.storage.store_document(document)
        await self.processing_queue.put((document, job))
        logger.info(f"Document submitted for processing: {doc_id}")
        return document
    
    async def _process_queue(self):
        while self._is_running:
            try:
                document, job = await self.processing_queue.get()
                await self._process_document(document, job)
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}", exc_info=True)
                # Update document status to failed
                await self.storage.update_document_status(
                    document.doc_id,
                    DocumentStatus.FAILED,
                    str(e)
                )
            finally:
                self.processing_queue.task_done()
                # Clean up temporary file
                if job.metadata.get("temp_file"):
                    try:
                        os.unlink(job.metadata["temp_file"])
                    except Exception as e:
                        logger.warning(f"Failed to clean up temporary file: {str(e)}")
    
    async def _process_document(self, document: Document, job: Job):
        try:
            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            await self.storage.update_document_status(document.doc_id, DocumentStatus.PROCESSING)
            
            # Process document using Docling
            temp_file = job.metadata.get("temp_file")
            if not temp_file:
                raise ValueError("No temporary file found in job metadata")
            
            with open(temp_file, 'rb') as f:
                content = f.read()
            
            # Process with Docling
            chunks = await self.docling.process_document(
                content=content,
                filename=document.filename,
                content_type=document.content_type
            )
            
            document.chunks = chunks
            document.status = DocumentStatus.COMPLETED
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            
            # Update document in storage
            await self.storage.store_document(document)
            logger.info(f"Document processed successfully: {document.doc_id}")
            
        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(datetime.timezone.utc)
            logger.error(f"Failed to process document {document.doc_id}: {str(e)}", exc_info=True)
            raise
    
    async def reprocess_document(self, doc_id: str) -> Document:
        """Reprocess an existing document."""
        document = await self.storage.get_document(doc_id)
        if not document:
            raise ValueError(f"Document not found: {doc_id}")
        
        if document.status == DocumentStatus.PROCESSING:
            raise ValueError("Document is already being processed")
        
        # Reset status and create new job
        document.status = DocumentStatus.PENDING
        document.chunks = []
        document.error_message = None
        
        job = Job(
            job_id=str(uuid.uuid4()),
            job_type=JobType.DOCUMENT_PROCESSING,
            status=JobStatus.PENDING,
            metadata={"doc_id": doc_id}
        )
        
        # Store updated document and submit for processing
        await self.storage.store_document(document)
        await self.processing_queue.put((document, job))
        
        return document
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """Retrieve a document by its ID."""
        return await self.storage.get_document(doc_id)
    
    async def get_document_status(self, doc_id: str) -> Optional[DocumentStatus]:
        """Get the current status of a document."""
        doc = await self.storage.get_document(doc_id)
        return doc.status if doc else None