# Document Processing Pipeline

A Kubeflow-based document processing pipeline that leverages IBM Docling for document processing, supports multiple embedding providers, and enables semantic search capabilities through vector databases.

## Features

### Document Processing
- **Multi-format Support**: Process various document types:
  - PDF documents (text, tables, forms)
  - Word documents (.doc, .docx)
  - Excel spreadsheets (.xls, .xlsx)
  - PowerPoint presentations (.ppt, .pptx)
  - Plain text and Markdown
  - Images with OCR support
- **Intelligent Processing**:
  - Document structure preservation
  - Table detection and extraction
  - Text block identification
  - Font and styling information
  - OCR for images and scanned documents

### Embedding Generation
- **Multiple Providers**:
  - Nomic Embeddings (nomic-embed-text-v1.5)
  - Granite Embeddings (278m-multilingual)
- **Features**:
  - Configurable chunk size
  - Batch processing
  - Caching support
  - Extensible provider system

### Storage & Search
- **Vector Database**: Elasticsearch with dense vector support
- **Caching**: Redis for fast retrieval
- **Search Capabilities**:
  - Semantic similarity search
  - Configurable k-nearest neighbors
  - Metadata filtering

### API & Interface
- **RESTful API**: Comprehensive endpoints for all operations
- **CLI Tool**: Command-line interface for common tasks
- **Monitoring**: Prometheus metrics and Grafana dashboards

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- System dependencies (installed via Docker):
  - libmagic1
  - poppler-utils
  - tesseract-ocr
  - libreoffice

### Installation

1. Clone the repository and set up environment:
```bash
# Clone the repository
git clone <repository-url>
cd document-processing-pipeline

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

2. Configure environment:
```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

3. Start services:
```bash
# Start required services
docker-compose up -d

# Start the API server
python -m doc_pipeline.api.main
```

### Testing the Pipeline

1. Quick test with sample document:
```bash
# Run the test script
./test_services.sh
```

2. Manual testing:
```bash
# Upload and process a document
python test_pipeline.py test_docs/sample.txt

# Use CLI for operations
python -m doc_pipeline.cli.main upload /path/to/document.pdf
python -m doc_pipeline.cli.main status <doc_id>
python -m doc_pipeline.cli.main search "your query"
```

## API Documentation

### Core Endpoints

- **Document Operations**:
  - `POST /api/v1/documents/`: Upload a document
  - `GET /api/v1/documents/{doc_id}`: Get document details
  - `GET /api/v1/documents/{doc_id}/status`: Check processing status
  - `POST /api/v1/documents/{doc_id}/process`: Trigger processing

- **Embedding Operations**:
  - `POST /api/v1/documents/{doc_id}/generate-embeddings`: Generate embeddings
  - `GET /api/v1/documents/{doc_id}/embeddings`: Get document embeddings

- **Search Operations**:
  - `POST /api/v1/documents/search`: Semantic search
  - `GET /api/v1/documents/search/metadata`: Search by metadata

Access the interactive API documentation at `http://localhost:50007/docs`

## Configuration

### Environment Variables

Key configuration options (see `.env.example` for all options):

```env
# API Settings
PORT=50007
API_V1_STR=/api/v1
SECRET_KEY=your-secret-key-here

# Storage Settings
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
REDIS_HOST=localhost
REDIS_PORT=6379

# Embedding Settings
NOMIC_API_KEY=your-nomic-api-key
GRANITE_API_KEY=your-granite-api-key

# Processing Settings
MAX_CHUNK_SIZE=1000
BATCH_SIZE=50
```

### Docker Configuration

The system uses multiple containers:
- API Server: Document processing and API endpoints
- Elasticsearch: Vector storage and search
- Redis: Caching and job queue
- Prometheus: Metrics collection
- Grafana: Monitoring dashboards

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest doc_pipeline/tests/test_document_processor.py
pytest doc_pipeline/tests/test_docling_service.py
```

### Adding New Features

1. Document Processors:
   - Extend `DoclingService` class
   - Add new document type support
   - Implement custom chunking strategies

2. Embedding Providers:
   - Add new provider in `embedding_service.py`
   - Implement provider-specific logic
   - Update configuration

3. Search Features:
   - Extend vector search capabilities
   - Add new search strategies
   - Implement filtering and ranking

## Monitoring

### Metrics
- Document processing statistics
- API endpoint latencies
- Queue sizes and processing times
- Storage and cache performance

### Logging
- JSON-formatted logs
- Configurable log levels
- Audit logging support

Access Grafana dashboards at `http://localhost:3000`

## License

MIT