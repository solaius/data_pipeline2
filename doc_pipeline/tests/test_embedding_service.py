import pytest
import aiohttp
import json
from typing import List, Dict, Optional, Union
from unittest.mock import AsyncMock, patch, MagicMock
from tenacity import retry, stop_after_attempt, wait_exponential
from ..services.embedding_service import (
    EmbeddingService,
    BaseEmbeddingProvider,
    NomicEmbeddingProvider,
    GraniteEmbeddingProvider,
    EmbeddingError
)
from ..models.document import DocumentChunk
from ..config.settings import settings

@pytest.fixture
def mock_redis():
    with patch('redis.Redis') as mock:
        # Configure Redis mock to return None by default (cache miss)
        mock.return_value.get.return_value = None
        yield mock

@pytest.fixture
def embedding_service(mock_redis):
    return EmbeddingService()

@pytest.fixture
def sample_chunks():
    return [
        DocumentChunk(
            chunk_id=f"test_chunk_{i}",
            content=f"Test content {i}",
            metadata={"source": "test"}
        )
        for i in range(3)
    ]

@pytest.mark.asyncio
async def test_generate_single_embedding_success(embedding_service, sample_chunks):
    # Mock the API response
    mock_embedding = [0.1, 0.2, 0.3]
    
    with patch.object(
        BaseEmbeddingProvider,
        'generate_embedding',
        new_callable=AsyncMock,
        return_value=mock_embedding
    ):
        result, was_cached = await embedding_service._generate_single_embedding(
            sample_chunks[0],
            "nomic",
            embedding_service.providers["nomic"]
        )
        
        assert result.chunk_id == sample_chunks[0].chunk_id
        assert result.embedding == mock_embedding
        assert result.embedding_provider == "nomic"
        assert not was_cached

@pytest.mark.asyncio
async def test_generate_single_embedding_cached(embedding_service, sample_chunks):
    # Mock cache hit
    mock_embedding = [0.1, 0.2, 0.3]
    mock_cache_data = {
        "chunk_id": "test_chunk_0",
        "embedding_provider": "nomic",
        "embedding": mock_embedding,
        "metadata": {}
    }
    
    # Configure Redis mock to return cached data
    embedding_service.cache.redis_client.get.return_value = json.dumps(mock_cache_data)
    
    result, was_cached = await embedding_service._generate_single_embedding(
        sample_chunks[0],
        "nomic",
        embedding_service.providers["nomic"]
    )
    
    assert result.chunk_id == sample_chunks[0].chunk_id
    assert result.embedding == mock_embedding
    assert result.embedding_provider == "nomic"
    assert was_cached

@pytest.mark.asyncio
async def test_generate_embeddings_batch(embedding_service, sample_chunks):
    mock_embedding = [0.1, 0.2, 0.3]
    
    with patch.object(
        BaseEmbeddingProvider,
        'generate_embedding',
        new_callable=AsyncMock,
        return_value=mock_embedding
    ):
        results = await embedding_service.generate_embeddings(
            sample_chunks,
            provider_name="nomic",
            batch_size=2
        )
        
        assert len(results) == len(sample_chunks)
        for result, chunk in zip(results, sample_chunks):
            assert result.chunk_id == chunk.chunk_id
            assert result.embedding == mock_embedding
            assert result.embedding_provider == "nomic"

@pytest.mark.asyncio
async def test_generate_embeddings_error_handling(embedding_service, sample_chunks):
    with patch.object(
        BaseEmbeddingProvider,
        'generate_embedding',
        new_callable=AsyncMock,
        side_effect=EmbeddingError("API Error", "nomic", 500)
    ):
        results = await embedding_service.generate_embeddings(
            sample_chunks,
            provider_name="nomic",
            batch_size=2
        )
        
        # Should return empty list since all requests failed
        assert len(results) == 0

@pytest.mark.asyncio
async def test_invalid_provider(embedding_service, sample_chunks):
    with pytest.raises(ValueError, match="Unknown embedding provider: invalid"):
        await embedding_service.generate_embeddings(
            sample_chunks,
            provider_name="invalid"
        )

@pytest.mark.asyncio
async def test_retry_on_failure(embedding_service, sample_chunks):
    mock_embedding = [0.1, 0.2, 0.3]
    call_count = 0
    
    # Create a mock provider
    provider = NomicEmbeddingProvider(
        settings.NOMIC_API_URL,
        settings.NOMIC_API_KEY,
        settings.NOMIC_MODEL_NAME
    )
    
    # Create a mock session with retry behavior
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"embeddings": [mock_embedding]})
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()
    
    # First call raises error, second call succeeds
    mock_session.post = AsyncMock(side_effect=[
        aiohttp.ClientError(),  # First attempt fails
        mock_response  # Second attempt succeeds
    ])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock()
    
    # Mock the session creation
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result, was_cached = await embedding_service._generate_single_embedding(
            sample_chunks[0],
            "nomic",
            provider
        )
        
        assert result.embedding == mock_embedding
        assert mock_session.post.call_count == 2  # Verify retry happened

@pytest.mark.asyncio
async def test_nomic_provider_format(embedding_service):
    provider = embedding_service.providers["nomic"]
    text = "test text"
    
    # Test payload format
    payload = provider._get_payload(text)
    assert isinstance(payload["texts"], list)
    assert payload["texts"][0] == text
    assert payload["task_type"] == "search"
    
    # Test response parsing
    mock_response = {"embeddings": [[0.1, 0.2, 0.3]]}
    result = provider._parse_response(mock_response)
    assert result == [0.1, 0.2, 0.3]

@pytest.mark.asyncio
async def test_granite_provider_format(embedding_service):
    provider = embedding_service.providers["granite"]
    text = "test text"
    
    # Test headers format
    headers = provider._get_headers()
    assert "X-API-Key" in headers
    assert headers["X-API-Key"] == provider.api_key
    
    # Test payload format
    payload = provider._get_payload(text)
    assert payload["input"] == text
    assert payload["encoding_format"] == "float"
    
    # Test response parsing
    mock_response = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
    result = provider._parse_response(mock_response)
    assert result == [0.1, 0.2, 0.3]