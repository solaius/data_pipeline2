from typing import Dict, Any
import time
from prometheus_client import Counter, Histogram, Gauge
from functools import wraps
import logging

# Metrics
CHUNK_COUNTER = Counter(
    'document_chunks_total',
    'Total number of chunks created',
    ['strategy', 'status']
)

CHUNK_SIZE_HISTOGRAM = Histogram(
    'chunk_size_bytes',
    'Distribution of chunk sizes in bytes',
    ['strategy']
)

PROCESSING_TIME_HISTOGRAM = Histogram(
    'document_processing_seconds',
    'Time spent processing documents',
    ['operation']
)

ACTIVE_DOCUMENTS_GAUGE = Gauge(
    'active_documents',
    'Number of documents currently being processed'
)

def log_chunking_metrics(strategy: str, chunks: list, processing_time: float):
    """Log metrics about chunking operation."""
    CHUNK_COUNTER.labels(strategy=strategy, status='success').inc(len(chunks))
    
    for chunk in chunks:
        CHUNK_SIZE_HISTOGRAM.labels(strategy=strategy).observe(len(chunk.content))
    
    PROCESSING_TIME_HISTOGRAM.labels(operation='chunking').observe(processing_time)

def track_processing_time(func):
    """Decorator to track processing time of functions."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        ACTIVE_DOCUMENTS_GAUGE.inc()
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            processing_time = time.time() - start_time
            
            # Log metrics if result contains chunks
            if hasattr(result, '__iter__'):
                strategy = kwargs.get('chunking_strategy', 'hybrid')
                log_chunking_metrics(strategy, result, processing_time)
            
            return result
        except Exception as e:
            CHUNK_COUNTER.labels(
                strategy=kwargs.get('chunking_strategy', 'hybrid'),
                status='error'
            ).inc()
            raise
        finally:
            ACTIVE_DOCUMENTS_GAUGE.dec()
    
    return wrapper