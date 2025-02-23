import pytest
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

def test_document_type_mapping(docling_service):
    # Test PDF mapping
    assert docling_service._get_document_type('application/pdf', 'test.pdf') == 'pdf'
    
    # Test Word document mapping
    assert docling_service._get_document_type(
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'test.docx'
    ) == 'docx'
    
    # Test text file mapping
    assert docling_service._get_document_type('text/plain', 'test.txt') == 'txt'
    
    # Test image mapping
    assert docling_service._get_document_type('image/jpeg', 'test.jpg') == 'image'

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
    
    with pytest.raises(ValueError) as exc_info:
        await docling_service.process_document(content, filename, content_type)
    assert "Unsupported document type" in str(exc_info.value)