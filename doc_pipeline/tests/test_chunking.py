import pytest
from doc_pipeline.services.docling_service import DoclingService, ChunkingStrategy
from doc_pipeline.models.document import DocumentChunk
from doc_pipeline.utils.logging import logger

@pytest.fixture
def sample_text():
    return """# Test Document

## Section 1
This is a test paragraph with multiple sentences. It contains information that should be chunked. Here is another sentence.

## Section 2
Another paragraph here with different content. This should be in a separate chunk.

### Subsection 2.1
More detailed information in a subsection. This helps test the chunking strategies.

## Section 3
Final section with some concluding text. This should be handled appropriately."""

@pytest.fixture
def docling_service():
    return DoclingService(
        chunk_size=100,
        chunk_overlap=20,
        default_strategy=ChunkingStrategy.HYBRID
    )

@pytest.mark.asyncio
async def test_hybrid_chunking(docling_service, sample_text):
    chunks = await docling_service.process_document(
        content=sample_text.encode('utf-8'),
        filename="test.md",
        content_type="text/markdown",
        chunking_strategy=ChunkingStrategy.HYBRID
    )
    
    assert chunks is not None
    assert len(chunks) > 0
    assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
    assert all(chunk.content for chunk in chunks)
    assert all(chunk.metadata["strategy"] == ChunkingStrategy.HYBRID for chunk in chunks)

@pytest.mark.asyncio
async def test_markdown_chunking(docling_service, sample_text):
    chunks = await docling_service.process_document(
        content=sample_text.encode('utf-8'),
        filename="test.md",
        content_type="text/markdown",
        chunking_strategy=ChunkingStrategy.MARKDOWN
    )
    
    assert chunks is not None
    assert len(chunks) > 0
    assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
    # Check that headings are preserved
    assert any("Section" in str(chunk.metadata.get("headings", [])) for chunk in chunks)
    assert all(chunk.metadata["strategy"] == ChunkingStrategy.MARKDOWN for chunk in chunks)

@pytest.mark.asyncio
async def test_sentence_chunking(docling_service, sample_text):
    chunks = await docling_service.process_document(
        content=sample_text.encode('utf-8'),
        filename="test.md",
        content_type="text/markdown",
        chunking_strategy=ChunkingStrategy.SENTENCE
    )
    
    assert chunks is not None
    assert len(chunks) > 0
    assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
    assert all(chunk.metadata["strategy"] == ChunkingStrategy.SENTENCE for chunk in chunks)

@pytest.mark.asyncio
async def test_chunking_with_small_size(docling_service, sample_text):
    small_chunk_service = DoclingService(
        chunk_size=50,
        chunk_overlap=10,
        default_strategy=ChunkingStrategy.SENTENCE
    )
    chunks = await small_chunk_service.process_document(
        content=sample_text.encode('utf-8'),
        filename="test.md",
        chunking_strategy=ChunkingStrategy.SENTENCE
    )
    
    assert len(chunks) > 0
    
    # Print chunk details for debugging
    print("\nChunk details:")
    for i, chunk in enumerate(chunks):
        size = len(chunk.content)
        print(f"Chunk {i + 1} ({size} chars): {chunk.content[:50]}...")
        logger.debug(f"Chunk {i + 1} size: {size} characters")
        logger.debug(f"Chunk {i + 1} content: {chunk.content}")
    
    max_allowed_size = small_chunk_service.chunk_size + small_chunk_service.chunk_overlap
    oversized_chunks = []
    
    for i, chunk in enumerate(chunks, 1):
        size = len(chunk.content)
        if size > max_allowed_size:
            oversized_chunks.append((i, size, chunk.content[:50]))
    
    assert not oversized_chunks, (
        f"\nFound chunks exceeding maximum size of {max_allowed_size} characters:\n" +
        "\n".join(f"Chunk {i}: {size} chars - Content: {preview}..." 
                 for i, size, preview in oversized_chunks)
    )

@pytest.mark.asyncio
async def test_chunking_with_large_overlap(docling_service, sample_text):
    large_overlap_service = DoclingService(chunk_size=100, chunk_overlap=50)
    chunks = await large_overlap_service.process_document(
        content=sample_text.encode('utf-8'),
        filename="test.md"
    )
    
    assert len(chunks) > 0
    # Test would need content analysis to verify overlap

@pytest.mark.asyncio
async def test_fallback_strategy(docling_service):
    # Test with invalid content to trigger fallback
    invalid_content = b"Invalid content that might cause chunking to fail"
    chunks = await docling_service.process_document(
        content=invalid_content,
        filename="test.txt",
        chunking_strategy="invalid_strategy"
    )
    
    assert len(chunks) == 1
    assert chunks[0].metadata["strategy"] == ChunkingStrategy.FALLBACK
    assert chunks[0].metadata["is_fallback"] is True

@pytest.mark.asyncio
async def test_txt_to_markdown_conversion(docling_service):
    text_content = "Simple text content\nWith multiple lines\n"
    chunks = await docling_service.process_document(
        content=text_content.encode('utf-8'),
        filename="test.txt"
    )
    
    assert chunks is not None
    assert len(chunks) > 0
    assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)

@pytest.mark.asyncio
async def test_chunk_metadata(docling_service, sample_text):
    chunks = await docling_service.process_document(
        content=sample_text.encode('utf-8'),
        filename="test.md"
    )
    
    for chunk in chunks:
        assert "chunk_number" in chunk.metadata
        assert "total_chunks" in chunk.metadata
        assert "strategy" in chunk.metadata
        assert chunk.metadata["chunk_number"] <= chunk.metadata["total_chunks"]

@pytest.mark.asyncio
async def test_invalid_config():
    with pytest.raises(ValueError):
        DoclingService(chunk_size=-1)
    
    with pytest.raises(ValueError):
        DoclingService(chunk_overlap=-1)
    
    with pytest.raises(ValueError):
        DoclingService(chunk_size=100, chunk_overlap=200)