from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from prometheus_client import make_asgi_app
from .routes import documents
from ..config.settings import settings
from ..utils.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handlers."""
    logger.info("Starting application")
    yield
    logger.info("Shutting down application")

app = FastAPI(
    title="Document Processing Pipeline",
    description="A Kubeflow-based document processing pipeline with embedding generation and vector search capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(
    documents.router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["documents"]
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

def start_server():
    """Start the FastAPI server."""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "50007"))
    
    print(f"Starting server on {host}:{port}")
    uvicorn.run(
        "doc_pipeline.api.main:app",
        host=host,
        port=port,
        reload=True,
        access_log=True,
        log_level="debug"
    )

if __name__ == "__main__":
    start_server()
