"""
GLCS REST API Application.

This module creates and configures the FastAPI application for the
Global Logical Context Store system.

Usage:
    # Development server with auto-reload
    uvicorn glcs.api.app:app --reload --host 0.0.0.0 --port 8000

    # Production server
    uvicorn glcs.api.app:app --host 0.0.0.0 --port 8000 --workers 4

Author: GLCS PhD Research Team
Version: 2.1.0 (Stage 2.1)
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from glcs.api.routes import router, initialize_glcs
from glcs.api.models import ErrorResponse
from glcs.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Lifespan Events
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    This initializes the GLCS system on startup and cleans up on shutdown.
    """
    # Startup
    logger.info("Starting GLCS API server...")

    # Get configuration from environment or use defaults
    parser_provider = os.getenv('GLCS_PARSER_PROVIDER', 'ollama')
    parser_model = os.getenv('GLCS_PARSER_MODEL', 'qwen2.5:0.5b')
    encoder_model = os.getenv('GLCS_ENCODER_MODEL', 'all-mpnet-base-v2')
    in_memory = os.getenv('GLCS_IN_MEMORY', 'true').lower() == 'true'

    logger.info(f"Configuration:")
    logger.info(f"  Parser Provider: {parser_provider}")
    logger.info(f"  Parser Model: {parser_model}")
    logger.info(f"  Encoder Model: {encoder_model}")
    logger.info(f"  In-Memory Mode: {in_memory}")

    try:
        # Initialize GLCS
        initialize_glcs(
            parser_provider=parser_provider,
            parser_model=parser_model,
            encoder_model=encoder_model,
            in_memory=in_memory
        )
        logger.info(" GLCS system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize GLCS: {e}")
        logger.warning("API will start but GLCS functionality will be unavailable")

    yield

    # Shutdown
    logger.info("Shutting down GLCS API server...")
    logger.info(" Shutdown complete")


# ============================================================================
# Create FastAPI Application
# ============================================================================

app = FastAPI(
    title="GLCS REST API",
    description="""
    **Global Logical Context Store (GLCS) REST API**

    A neuro-symbolic middleware for LLM consistency checking and knowledge management.

    ## Features

    * **Parse** - Convert natural language to structured logical forms
    * **Check** - Verify consistency with existing knowledge
    * **Search** - Semantic search across stored knowledge
    * **Contexts** - Manage multiple knowledge contexts

    ## Quick Start

    ```python
    import requests

    # Parse a statement
    response = requests.post('http://localhost:8000/parse', json={
        'text': 'John is a manager',
        'context_id': 'team-db'
    })
    print(response.json())
    ```

    ## Architecture

    GLCS uses a multi-stage pipeline:
    1. **LLM Parser** - Extracts logical structure from text
    2. **Semantic Encoder** - Generates 768-dim embeddings
    3. **Memory Manager** - Stores in vector database (ChromaDB)
    4. **Consistency Checker** - Detects contradictions

    ## Configuration

    Set via environment variables:
    * `GLCS_PARSER_PROVIDER` - LLM provider (default: ollama)
    * `GLCS_PARSER_MODEL` - Model name (default: qwen2.5:0.5b)
    * `GLCS_ENCODER_MODEL` - Encoder model (default: all-mpnet-base-v2)
    * `GLCS_IN_MEMORY` - Use in-memory storage (default: true)

    ## Links

    * [GitHub Repository](https://github.com/GireeshS22/Global-Logic-Context-Store)
    * [Documentation](https://github.com/GireeshS22/Global-Logic-Context-Store/blob/develop/docs/)
    * [LLM Parser Guide](https://github.com/GireeshS22/Global-Logic-Context-Store/blob/develop/docs/LLM_PARSER_GUIDE.md)
    """,
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================================================
# Middleware
# ============================================================================

# CORS middleware
# allow_origins=["*"] is incompatible with allow_credentials=True per the CORS spec.
# Credentials (cookies, Authorization headers) require explicit origin allowlisting.
_cors_origins = os.getenv("GLCS_CORS_ORIGINS", "").split(",")
_allow_origins = [o.strip() for o in _cors_origins if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=_allow_origins != ["*"],  # only True when origins are explicit
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = datetime.now(timezone.utc)

    # Log request
    logger.info(f"{request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Log response
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")

    return response


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_response = ErrorResponse(
        error="InternalServerError",
        message="An unexpected error occurred",
        details={"error_type": type(exc).__name__},
        timestamp=datetime.now(timezone.utc)
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json")  # (#16: mode=json converts datetime to ISO string)
    )


# ============================================================================
# Include Routers
# ============================================================================

app.include_router(router, prefix="/api/v1")


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["Root"])
def root():
    """
    API root endpoint.

    Returns basic API information and links to documentation.
    """
    return {
        "name": "GLCS REST API",
        "version": "2.1.0",
        "description": "Global Logical Context Store - Neuro-symbolic middleware for LLM consistency checking",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/api/v1/health",
        "endpoints": {
            "parse": "POST /api/v1/parse",
            "check": "POST /api/v1/check",
            "search": "GET /api/v1/search",
            "contexts": "GET /api/v1/contexts"
        },
        "github": "https://github.com/GireeshS22/Global-Logic-Context-Store"
    }


# ============================================================================
# Entry Point (for direct execution)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Run development server
    uvicorn.run(
        "glcs.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
