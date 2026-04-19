"""
API Routes - Endpoint Handlers for GLCS REST API.

This module implements all API endpoints for the GLCS system.

Author: GLCS PhD Research Team
Version: 2.1.0 (Stage 2.1)
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from glcs.api.models import (
    ParseRequest, CheckRequest, BatchParseRequest,
    LogicalFormResponse, ConsistencyReportResponse, SearchResponse,
    ContextsResponse, HealthResponse, ErrorResponse,
    EntityResponse, RelationResponse, ViolationResponse,
    SearchResult, ContextInfo
)
from glcs.advanced_wrapper import AdvancedGLCS
from glcs.core.models import LogicalForm
from glcs.utils.exceptions import ParsingError, ValidationError, ConsistencyError
from glcs.utils.logger import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter()

# Global GLCS instance (initialized on startup)
glcs: Optional[AdvancedGLCS] = None


def initialize_glcs(
    parser_provider: str = 'ollama',
    parser_model: str = 'qwen2.5:0.5b',
    encoder_model: str = 'all-mpnet-base-v2',
    in_memory: bool = False
):
    """Initialize the GLCS system."""
    global glcs
    glcs = AdvancedGLCS(
        parser_provider=parser_provider,
        parser_model=parser_model,
        encoder_model=encoder_model,
        in_memory=in_memory
    )
    logger.info("GLCS system initialized for API")


def _logical_form_to_response(form: LogicalForm) -> LogicalFormResponse:
    """Convert LogicalForm to API response model."""
    return LogicalFormResponse(
        id=str(form.form_id),
        context_id=form.context_id,
        source_text=form.source_text,
        logical_type=form.logical_type.value,
        subject=EntityResponse(
            name=form.subject.name,
            entity_type=form.subject.entity_type
        ),
        predicate=RelationResponse(
            verb=form.predicate.verb,
            relation_type=form.predicate.relation_type
        ),
        object=EntityResponse(
            name=form.object.name,
            entity_type=form.object.entity_type
        ) if form.object else None,
        polarity=form.polarity.value,
        confidence_score=form.confidence_score,
        timestamp=form.timestamp
    )


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """
    Health check endpoint.

    Returns system status and component readiness.
    """
    try:
        components = {
            "parser": "ready" if glcs and glcs.parser else "not_initialized",
            "memory": "ready" if glcs and glcs.memory else "not_initialized",
            "checker": "ready" if glcs and glcs.checker else "not_initialized"
        }

        return HealthResponse(
            status="healthy" if all(v == "ready" for v in components.values()) else "degraded",
            version="2.1.0",
            timestamp=datetime.now(timezone.utc),
            components=components
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version="2.1.0",
            timestamp=datetime.now(timezone.utc),
            components={"error": str(e)}
        )


# ============================================================================
# Parse Endpoints
# ============================================================================

@router.post("/parse", response_model=LogicalFormResponse, tags=["Parsing"])
def parse_statement(request: ParseRequest):
    """
    Parse a natural language statement into a logical form.

    - **text**: The natural language text to parse
    - **context_id**: Context identifier for this statement
    - **use_cache**: Whether to use cached results (default: true)

    Returns the parsed logical form with extracted entities, relations, and metadata.
    """
    try:
        logger.info(f"Parsing statement: '{request.text}' (context: {request.context_id})")

        if not glcs:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GLCS system not initialized"
            )

        # Parse the statement
        form = glcs.parser.parse(
            request.text,
            request.context_id,
            use_cache=request.use_cache
        )

        # Add embedding and store in memory (non-fatal — parse result is still returned on failure)
        try:
            glcs.encoder.add_embedding_to_form(form)
            glcs.memory.store_form(form)
        except Exception as e:
            logger.warning(f"Memory storage failed (non-fatal): {e}")

        # Convert to response model
        response = _logical_form_to_response(form)

        logger.info(f"Successfully parsed: {form.logical_type.value}")
        return response

    except ParsingError as e:
        logger.error(f"Parsing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse statement: {str(e)}"
        )
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred."
        )


@router.post("/parse/batch", response_model=List[LogicalFormResponse], tags=["Parsing"])
def parse_batch(request: BatchParseRequest):
    """
    Parse multiple statements in batch.

    - **texts**: List of natural language texts to parse
    - **context_id**: Context identifier for all statements
    - **use_cache**: Whether to use cached results (default: true)

    Returns a list of parsed logical forms.
    """
    try:
        logger.info(f"Batch parsing {len(request.texts)} statements")

        if not glcs:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GLCS system not initialized"
            )

        # Parse batch
        forms = glcs.parser.parse_batch(
            request.texts,
            request.context_id,
            use_cache=request.use_cache
        )

        # Add embeddings and store in memory (non-fatal — parse results are still returned on failure)
        try:
            glcs.encoder.add_embeddings_to_forms(forms)
            for form in forms:
                glcs.memory.store_form(form)
        except Exception as e:
            logger.warning(f"Memory storage failed (non-fatal): {e}")

        # Convert to response models
        responses = [_logical_form_to_response(form) for form in forms]

        logger.info(f"Successfully parsed {len(responses)}/{len(request.texts)} statements")
        return responses

    except Exception as e:
        logger.error(f"Batch parse error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch parsing failed due to an internal error."
        )


# ============================================================================
# Consistency Check Endpoints
# ============================================================================

@router.post("/check", response_model=ConsistencyReportResponse, tags=["Consistency"])
def check_consistency(request: CheckRequest):
    """
    Check if a statement is consistent with existing knowledge.

    - **text**: The natural language text to check
    - **context_id**: Context to check against

    Returns a consistency report with violations (if any).
    """
    try:
        logger.info(f"Checking consistency: '{request.text}' (context: {request.context_id})")

        if not glcs:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GLCS system not initialized"
            )

        # Process and check statement
        report = glcs.process_statement(request.text, request.context_id, auto_store=False)

        # Convert violations
        violations = [
            ViolationResponse(
                violation_type=v.violation_type,
                explanation=v.explanation,
                conflicting_form_ids=[str(f.form_id) for f in v.conflicting_forms] if v.conflicting_forms else [],
                severity=getattr(v, 'severity', 'medium')
            )
            for v in report.violations
        ]

        response = ConsistencyReportResponse(
            is_consistent=report.is_consistent,
            violations=violations,
            form=None,  # Parsed form not returned in consistency report
            checked_at=datetime.now(timezone.utc)
        )

        logger.info(f"Consistency check: {'PASS' if report.is_consistent else 'FAIL'}")
        return response

    except ConsistencyError as e:
        logger.error(f"Consistency error: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Consistency violation: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Consistency check failed due to an internal error."
        )


# ============================================================================
# Search Endpoints
# ============================================================================

@router.get("/search", response_model=SearchResponse, tags=["Search"])
def search_knowledge(
    query: str = Query(..., description="Search query"),
    context_id: str = Query(..., description="Context to search in"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results")
):
    """
    Search for relevant knowledge using semantic similarity.

    - **query**: The search query (natural language)
    - **context_id**: Context to search within
    - **limit**: Maximum number of results to return (1-100)

    Returns semantically similar statements ranked by similarity score.
    """
    try:
        logger.info(f"Searching: '{query}' in context '{context_id}'")

        if not glcs:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GLCS system not initialized"
            )

        # Perform semantic search
        results = glcs.search_similar(query, context_id, top_k=limit)

        # Convert to response
        search_results = [
            SearchResult(
                form=_logical_form_to_response(form),
                similarity_score=1.0  # search_similar returns ranked forms, no score exposed
            )
            for form in results
        ]

        response = SearchResponse(
            query=query,
            results=search_results,
            total_count=len(search_results)
        )

        logger.info(f"Found {len(search_results)} results")
        return response

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed due to an internal error."
        )


# ============================================================================
# Context Management Endpoints
# ============================================================================

@router.get("/contexts", response_model=ContextsResponse, tags=["Contexts"])
def list_contexts():
    """
    List all available contexts.

    Returns information about all contexts including statement counts
    and sample statements.
    """
    try:
        logger.info("Listing contexts")

        if not glcs:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GLCS system not initialized"
            )

        # Get all contexts
        context_ids = glcs.memory.list_contexts()

        # Get summary for each context
        contexts = []
        for context_id in context_ids:
            summary = glcs.get_context_summary(context_id)
            contexts.append(
                ContextInfo(
                    context_id=context_id,
                    total_forms=summary.get('total_forms', 0),
                    sample_statements=summary.get('sample_statements', [])[:5],
                    created_at=None  # Not tracked yet
                )
            )

        response = ContextsResponse(
            contexts=contexts,
            total_count=len(contexts)
        )

        logger.info(f"Found {len(contexts)} contexts")
        return response

    except Exception as e:
        logger.error(f"List contexts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list contexts due to an internal error."
        )


@router.get("/contexts/{context_id}", response_model=ContextInfo, tags=["Contexts"])
def get_context(context_id: str):
    """
    Get detailed information about a specific context.

    - **context_id**: The context identifier

    Returns detailed context information.
    """
    try:
        logger.info(f"Getting context: {context_id}")

        if not glcs:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GLCS system not initialized"
            )

        summary = glcs.get_context_summary(context_id)

        if summary.get('total_forms', 0) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Context '{context_id}' not found or empty"
            )

        response = ContextInfo(
            context_id=context_id,
            total_forms=summary.get('total_forms', 0),
            sample_statements=summary.get('sample_statements', []),
            created_at=None
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get context error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get context due to an internal error."
        )
