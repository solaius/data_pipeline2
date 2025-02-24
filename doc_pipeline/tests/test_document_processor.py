import pytest
import asyncio
import pytest_asyncio
from ..services.document_processor import DocumentProcessor
from ..models.document import Document, DocumentStatus
from ..models.job import Job, JobStatus
import tempfile
import os

@pytest_asyncio.fixture
async def document_processor():
    processor = DocumentProcessor()
    await processor.start()
    
    try:
        yield processor  # Yield control to the tests
    finally:
        await processor.stop()
        # Ensure any background tasks are fully cancelled
        await asyncio.sleep(0.5)  # Small delay to let cleanup finish


@pytest.mark.asyncio
async def test_submit_document(document_processor):
    # Test document submission
    content = b"This is a test document"
    filename = "test.txt"
    content_type = "text/plain"
    
    document = await document_processor.submit_document(
        content=content,
        filename=filename,
        content_type=content_type
    )
    
    assert document is not None
    assert document.doc_id is not None
    assert document.filename == filename
    assert document.content_type == content_type
    assert document.status == DocumentStatus.PENDING

@pytest.mark.asyncio
async def test_document_processing(document_processor):
    # Submit a document and wait for processing
    content = b"This is a test document for processing"
    filename = "test_processing.txt"
    content_type = "text/plain"

    document = await document_processor.submit_document(
        content=content,
        filename=filename,
        content_type=content_type
    )

    # Wait for processing to complete
    max_wait = 10  # seconds
    while max_wait > 0:
        doc = await document_processor.get_document(document.doc_id)
        if doc and doc.status in [DocumentStatus.COMPLETED, DocumentStatus.FAILED]:
            break
        await asyncio.sleep(1)
        max_wait -= 1

    # Get the processed document
    processed_doc = await document_processor.get_document(document.doc_id)
    assert processed_doc is not None
    assert processed_doc.status == DocumentStatus.COMPLETED
    
    print(f"Processed document chunks: {processed_doc.chunks}")  # 🔹 Debugging output
    assert len(processed_doc.chunks) > 0

@pytest.mark.asyncio
async def test_get_document_status(document_processor):
    # Submit a document
    content = b"Test document for status check"
    filename = "test_status.txt"
    content_type = "text/plain"
    
    document = await document_processor.submit_document(
        content=content,
        filename=filename,
        content_type=content_type
    )
    
    # Check initial status
    status = await document_processor.get_document_status(document.doc_id)
    assert status == DocumentStatus.PENDING
    
    # Wait for processing and check final status
    max_wait = 10  # seconds
    while max_wait > 0:
        status = await document_processor.get_document_status(document.doc_id)
        if status in [DocumentStatus.COMPLETED, DocumentStatus.FAILED]:
            break
        await asyncio.sleep(1)
        max_wait -= 1
    
    final_status = await document_processor.get_document_status(document.doc_id)
    assert final_status == DocumentStatus.COMPLETED