from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from contextlib import asynccontextmanager
from ...models.document import Document, DocumentStatus
from ...models.job import Job, JobStatus
from ...services.document_processor import DocumentProcessor
from ...services.embedding_service import EmbeddingService
from ...services.vector_storage import VectorStorage
from ...utils.logging import logger

@asynccontextmanager
async def lifespan(app):
    await document_processor.start()
    await vector_storage.initialize()
    logger.info("API routes initialized")
    yield
    await document_processor.stop()
    await vector_storage.close()
    logger.info("API routes shutdown")

router = APIRouter(lifespan=lifespan)
document_processor = DocumentProcessor()
embedding_service = EmbeddingService()
vector_storage = VectorStorage()

@router.post("/documents/", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload a document for processing."""
    try:
        content = await file.read()
        document = await document_processor.submit_document(
            content=content,
            filename=file.filename,
            content_type=file.content_type
        )
        logger.info(f"Document uploaded: {document.doc_id}")
        return document
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{doc_id}", response_model=Document)
async def get_document(doc_id: str):
    """Retrieve a document by its ID."""
    try:
        document = await document_processor.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document {doc_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{doc_id}/status", response_model=DocumentStatus)
async def get_document_status(doc_id: str):
    """Get the current status of a document."""
    try:
        status = await document_processor.get_document_status(doc_id)
        if not status:
            raise HTTPException(status_code=404, detail="Document not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving status for document {doc_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/{doc_id}/process")
async def process_document(doc_id: str):
    """Manually trigger document processing."""
    try:
        document = await document_processor.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.status == DocumentStatus.PROCESSING:
            raise HTTPException(status_code=400, detail="Document is already being processed")
        
        # Reset status and resubmit for processing
        document.status = DocumentStatus.PENDING
        await document_processor.submit_document(
            content=b"",  # Content will be loaded from storage
            filename=document.filename,
            content_type=document.content_type
        )
        return {"status": "processing", "doc_id": doc_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/{doc_id}/generate-embeddings")
async def generate_embeddings(doc_id: str, provider: str = "nomic"):
    """Generate embeddings for a document using the specified provider."""
    try:
        document = await document_processor.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.status != DocumentStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Document must be in COMPLETED state to generate embeddings"
            )
        
        # TODO: Implement actual embedding generation
        raise HTTPException(status_code=501, detail="Embedding generation not implemented yet")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating embeddings for document {doc_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/search")
async def search_documents(query: str, provider: str = "nomic", k: int = 10):
    """Search for similar documents using semantic search."""
    try:
        # TODO: Implement actual semantic search
        raise HTTPException(status_code=501, detail="Semantic search not implemented yet")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing semantic search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
