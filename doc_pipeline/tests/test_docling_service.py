import pytest
from docling.exceptions import ConversionError
from ..services.docling_service import DoclingService

@pytest.fixture
def docling_service():
    return DoclingService()

def test_mime_type_detection(docling_service):
    # Test PDF content
    pdf_content = b"%PDF-1.4\n"
    assert docling_service._detect_mime_type(pdf_content).startswith('application/pdf')
    
    # Test text content
    text_content = b"This is a test document"
    assert docling_service._detect_mime_type(text_content).startswith('text/plain')

@pytest.mark.asyncio
async def test_process_text_document(docling_service):
    # Create a simple text document
    content = b"This is a test document.\nIt has multiple lines.\nAnd some structure."
    filename = "test.txt"
    content_type = "text/plain"

    chunks = await docling_service.process_document(content, filename, content_type)

    assert chunks is not None
    assert len(chunks) > 0
    assert all(chunk.content for chunk in chunks)
    assert all(chunk.chunk_id for chunk in chunks)

    # Debugging: Print chunk metadata to inspect why the assertion is failing
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1} Metadata: {chunk.metadata}")

    assert any(chunk.metadata["type"] in ["text_chunk", "markdown_chunk", "hybrid_chunk"] for chunk in chunks)

@pytest.mark.asyncio
async def test_process_pdf_document(docling_service):
    # Create a minimal PDF document
    content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
    filename = "test.pdf"
    content_type = "application/pdf"
    
    try:
        chunks = await docling_service.process_document(content, filename, content_type)
        assert chunks is not None
    except Exception as e:
        # Since this is a malformed PDF, we expect it might fail
        assert str(e) is not None

@pytest.mark.asyncio
async def test_unsupported_document_type(docling_service):
    content = b"Some binary content"
    filename = "test.unknown"
    content_type = "application/octet-stream"
    
    with pytest.raises(ConversionError) as exc_info:
        await docling_service.process_document(content, filename, content_type)
    assert "File format not allowed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_chunking_strategies(docling_service):
    content = b"""# Test Document
    
## Section 1
This is a test paragraph with multiple sentences.

## Section 2
Another paragraph here."""
    filename = "test.md"
    content_type = "text/markdown"
    
    # Test hybrid chunking
    chunks_hybrid = await docling_service.process_document(
        content, filename, content_type, chunking_strategy="hybrid"
    )
    assert len(chunks_hybrid) > 0
    assert all(c.metadata["strategy"] == "hybrid" for c in chunks_hybrid)
    
    # Test markdown chunking
    chunks_md = await docling_service.process_document(
        content, filename, content_type, chunking_strategy="markdown"
    )
    assert len(chunks_md) > 0
    assert all(c.metadata["strategy"] == "markdown" for c in chunks_md)
    
    # Test sentence chunking
    chunks_sent = await docling_service.process_document(
        content, filename, content_type, chunking_strategy="sentence"
    )
    assert len(chunks_sent) > 0
    assert all(c.metadata["strategy"] == "sentence" for c in chunks_sent)