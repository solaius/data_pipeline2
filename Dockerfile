FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    libreoffice \
    git \
    build-essential \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY doc_pipeline/ ./doc_pipeline/

# Create directories for temporary files
RUN mkdir -p /app/temp

ENV DOCLING_TEMP_DIR=/app/temp

CMD ["uvicorn", "doc_pipeline.api.main:app", "--host", "0.0.0.0", "--port", "50007"]