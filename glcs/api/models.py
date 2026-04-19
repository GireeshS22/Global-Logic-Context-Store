"""
API Models - Request/Response Schemas for GLCS REST API.

This module defines Pydantic models for all API endpoints,
ensuring type safety and automatic validation.

Author: GLCS PhD Research Team
Version: 2.1.0 (Stage 2.1)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Request Models
# ============================================================================

class ParseRequest(BaseModel):
    """Request model for POST /parse endpoint."""
    text: str = Field(..., description="Natural language text to parse", min_length=1)
    context_id: str = Field(..., description="Context identifier for the statement", min_length=1)
    use_cache: bool = Field(True, description="Whether to use cached results if available")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "text": "John is a manager",
                "context_id": "team-db",
                "use_cache": True
            }
        }
    )


class CheckRequest(BaseModel):
    """Request model for POST /check endpoint."""
    text: str = Field(..., description="Natural language text to check", min_length=1)
    context_id: str = Field(..., description="Context identifier to check against", min_length=1)

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "text": "Bob is a designer",
                "context_id": "team-db"
            }
        }
    )


class BatchParseRequest(BaseModel):
    """Request model for POST /parse/batch endpoint."""
    texts: List[str] = Field(..., description="List of texts to parse", min_length=1)
    context_id: str = Field(..., description="Context identifier for all statements", min_length=1)
    use_cache: bool = Field(True, description="Whether to use cached results")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "texts": ["John is a manager", "Alice is an engineer"],
                "context_id": "team-db",
                "use_cache": True
            }
        }
    )


# ============================================================================
# Response Models
# ============================================================================

class EntityResponse(BaseModel):
    """Entity in a logical form."""
    name: str = Field(..., description="Entity name")
    entity_type: Optional[str] = Field(None, description="Entity type (if known)")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "name": "john",
                "entity_type": "person"
            }
        }
    )


class RelationResponse(BaseModel):
    """Relation/predicate in a logical form."""
    verb: str = Field(..., description="Verb or action")
    relation_type: Optional[str] = Field(None, description="Relation type (if known)")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "verb": "is",
                "relation_type": "property"
            }
        }
    )


class LogicalFormResponse(BaseModel):
    """Complete logical form representation."""
    id: str = Field(..., description="Unique form identifier")
    context_id: str = Field(..., description="Context identifier")
    source_text: str = Field(..., description="Original natural language text")
    logical_type: str = Field(..., description="Type of logical statement")
    subject: EntityResponse = Field(..., description="Subject entity")
    predicate: RelationResponse = Field(..., description="Predicate relation")
    object: Optional[EntityResponse] = Field(None, description="Object entity (if present)")
    polarity: str = Field(..., description="Positive or negative")
    confidence_score: float = Field(..., description="Confidence in parsing", ge=0.0, le=1.0)
    timestamp: datetime = Field(..., description="When this form was created")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "abc123",
                "context_id": "team-db",
                "source_text": "John is a manager",
                "logical_type": "ground_fact",
                "subject": {"name": "john", "entity_type": "person"},
                "predicate": {"verb": "is", "relation_type": "property"},
                "object": {"name": "manager", "entity_type": "role"},
                "polarity": "positive",
                "confidence_score": 0.95,
                "timestamp": "2025-11-18T12:00:00Z"
            }
        }
    )


class ViolationResponse(BaseModel):
    """Consistency violation."""
    violation_type: str = Field(..., description="Type of violation")
    explanation: str = Field(..., description="Human-readable explanation")
    conflicting_form_ids: List[str] = Field(..., description="IDs of conflicting forms")
    severity: str = Field(..., description="Severity level")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "violation_type": "direct_contradiction",
                "explanation": "Bob cannot be both a developer and a designer",
                "conflicting_form_ids": ["form1", "form2"],
                "severity": "high"
            }
        }
    )


class ConsistencyReportResponse(BaseModel):
    """Consistency check report."""
    is_consistent: bool = Field(..., description="Whether the statement is consistent")
    violations: List[ViolationResponse] = Field(..., description="List of violations found")
    form: Optional[LogicalFormResponse] = Field(None, description="Parsed logical form")
    checked_at: datetime = Field(..., description="When the check was performed")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "is_consistent": False,
                "violations": [{
                    "violation_type": "direct_contradiction",
                    "explanation": "Contradicts existing fact",
                    "conflicting_form_ids": ["form1"],
                    "severity": "high"
                }],
                "form": None,
                "checked_at": "2025-11-18T12:00:00Z"
            }
        }
    )


class SearchResult(BaseModel):
    """Single search result."""
    form: LogicalFormResponse = Field(..., description="The logical form")
    similarity_score: float = Field(..., description="Similarity to query", ge=0.0, le=1.0)

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "form": {
                    "id": "abc123",
                    "context_id": "team-db",
                    "source_text": "John is a manager",
                    "logical_type": "ground_fact",
                    "subject": {"name": "john", "entity_type": "person"},
                    "predicate": {"verb": "is", "relation_type": "property"},
                    "object": {"name": "manager", "entity_type": "role"},
                    "polarity": "positive",
                    "confidence_score": 0.95,
                    "timestamp": "2025-11-18T12:00:00Z"
                },
                "similarity_score": 0.92
            }
        }
    )


class SearchResponse(BaseModel):
    """Search results."""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="List of results")
    total_count: int = Field(..., description="Total number of results")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "query": "managers",
                "results": [],
                "total_count": 5
            }
        }
    )


class ContextInfo(BaseModel):
    """Information about a context."""
    context_id: str = Field(..., description="Context identifier")
    total_forms: int = Field(..., description="Number of forms in context")
    sample_statements: List[str] = Field(..., description="Sample statements from context")
    created_at: Optional[datetime] = Field(None, description="When context was created")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "context_id": "team-db",
                "total_forms": 25,
                "sample_statements": ["John is a manager", "Alice is an engineer"],
                "created_at": "2025-11-18T10:00:00Z"
            }
        }
    )


class ContextsResponse(BaseModel):
    """List of contexts."""
    contexts: List[ContextInfo] = Field(..., description="List of available contexts")
    total_count: int = Field(..., description="Total number of contexts")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "contexts": [],
                "total_count": 3
            }
        }
    )


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current server time")
    components: Dict[str, str] = Field(..., description="Status of system components")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "2.1.0",
                "timestamp": "2025-11-18T12:00:00Z",
                "components": {
                    "parser": "ready",
                    "memory": "ready",
                    "checker": "ready"
                }
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="When the error occurred")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Text field is required",
                "details": {"field": "text"},
                "timestamp": "2025-11-18T12:00:00Z"
            }
        }
    )
