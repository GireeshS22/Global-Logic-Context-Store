"""
API Tests - Test Suite for GLCS REST API.

Tests all API endpoints for correctness, error handling, and edge cases.

Author: GLCS PhD Research Team
Version: 2.1.0 (Stage 2.1)
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from glcs.api.app import app

# Create test client
client = TestClient(app)


# ============================================================================
# Root & Health Tests
# ============================================================================

def test_root_endpoint():
    """Test root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "GLCS REST API"
    assert data["version"] == "2.1.0"
    assert "docs" in data
    assert "endpoints" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "components" in data
    assert data["version"] == "2.1.0"


# ============================================================================
# Parse Endpoint Tests
# ============================================================================

def test_parse_simple_statement():
    """Test parsing a simple statement."""
    response = client.post("/api/v1/parse", json={
        "text": "John is a manager",
        "context_id": "test-ctx-1"
    })
    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "id" in data
    assert "source_text" in data
    assert data["source_text"] == "John is a manager"
    assert "logical_type" in data
    assert "subject" in data
    assert "predicate" in data
    assert "confidence_score" in data

    # Check subject
    assert data["subject"]["name"] == "john"

    # Check predicate
    assert data["predicate"]["verb"] == "is"


def test_parse_with_cache():
    """Test parsing with caching enabled."""
    request_data = {
        "text": "Alice is an engineer",
        "context_id": "test-ctx-2",
        "use_cache": True
    }

    # First request
    response1 = client.post("/api/v1/parse", json=request_data)
    assert response1.status_code == 200

    # Second request (should use cache)
    response2 = client.post("/api/v1/parse", json=request_data)
    assert response2.status_code == 200

    # Results should be identical
    assert response1.json()["source_text"] == response2.json()["source_text"]


def test_parse_missing_text():
    """Test parsing with missing text field."""
    response = client.post("/api/v1/parse", json={
        "context_id": "test-ctx-3"
    })
    assert response.status_code == 422  # Validation error


def test_parse_empty_text():
    """Test parsing with empty text."""
    response = client.post("/api/v1/parse", json={
        "text": "",
        "context_id": "test-ctx-4"
    })
    assert response.status_code == 422  # Validation error


def test_parse_missing_context():
    """Test parsing with missing context_id."""
    response = client.post("/api/v1/parse", json={
        "text": "Bob is a developer"
    })
    assert response.status_code == 422  # Validation error


# ============================================================================
# Batch Parse Tests
# ============================================================================

def test_batch_parse():
    """Test batch parsing multiple statements."""
    response = client.post("/api/v1/parse/batch", json={
        "texts": [
            "Charlie is a designer",
            "Diana is a manager",
            "Eve is an engineer"
        ],
        "context_id": "test-ctx-batch-1"
    })
    assert response.status_code == 200
    data = response.json()

    # Should return list of parsed forms
    assert isinstance(data, list)
    assert len(data) == 3

    # Check first result
    assert data[0]["source_text"] == "Charlie is a designer"
    assert "subject" in data[0]
    assert "predicate" in data[0]


def test_batch_parse_empty_list():
    """Test batch parsing with empty list."""
    response = client.post("/api/v1/parse/batch", json={
        "texts": [],
        "context_id": "test-ctx-batch-2"
    })
    assert response.status_code == 422  # Validation error


# ============================================================================
# Consistency Check Tests
# ============================================================================

def test_check_consistency_simple():
    """Test consistency checking."""
    # First, add a statement
    client.post("/api/v1/parse", json={
        "text": "Frank is a developer",
        "context_id": "test-ctx-check-1"
    })

    # Check a new statement
    response = client.post("/api/v1/check", json={
        "text": "Frank is an engineer",
        "context_id": "test-ctx-check-1"
    })
    assert response.status_code == 200
    data = response.json()

    assert "is_consistent" in data
    assert "violations" in data
    assert isinstance(data["violations"], list)


def test_check_missing_text():
    """Test consistency check with missing text."""
    response = client.post("/api/v1/check", json={
        "context_id": "test-ctx-check-2"
    })
    assert response.status_code == 422


# ============================================================================
# Search Tests
# ============================================================================

def test_search_knowledge():
    """Test semantic search."""
    # First, add some statements
    client.post("/api/v1/parse", json={
        "text": "Grace is a manager",
        "context_id": "test-ctx-search-1"
    })
    client.post("/api/v1/parse", json={
        "text": "Heidi is a developer",
        "context_id": "test-ctx-search-1"
    })

    # Search
    response = client.get("/api/v1/search", params={
        "query": "manager",
        "context_id": "test-ctx-search-1"
    })
    assert response.status_code == 200
    data = response.json()

    assert "query" in data
    assert data["query"] == "manager"
    assert "results" in data
    assert isinstance(data["results"], list)
    assert "total_count" in data


def test_search_with_limit():
    """Test search with result limit."""
    response = client.get("/api/v1/search", params={
        "query": "engineer",
        "context_id": "test-ctx-search-2",
        "limit": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 5


def test_search_missing_query():
    """Test search with missing query parameter."""
    response = client.get("/api/v1/search", params={
        "context_id": "test-ctx-search-3"
    })
    assert response.status_code == 422


def test_search_missing_context():
    """Test search with missing context_id."""
    response = client.get("/api/v1/search", params={
        "query": "test"
    })
    assert response.status_code == 422


# ============================================================================
# Context Management Tests
# ============================================================================

def test_list_contexts():
    """Test listing all contexts."""
    # Add some data to create contexts
    client.post("/api/v1/parse", json={
        "text": "Ivan is a manager",
        "context_id": "test-ctx-list-1"
    })
    client.post("/api/v1/parse", json={
        "text": "Judy is a developer",
        "context_id": "test-ctx-list-2"
    })

    # List contexts
    response = client.get("/api/v1/contexts")
    assert response.status_code == 200
    data = response.json()

    assert "contexts" in data
    assert "total_count" in data
    assert isinstance(data["contexts"], list)
    assert data["total_count"] >= 2


def test_get_specific_context():
    """Test getting a specific context."""
    # Create context
    client.post("/api/v1/parse", json={
        "text": "Kevin is an engineer",
        "context_id": "test-ctx-specific-1"
    })

    # Get context
    response = client.get("/api/v1/contexts/test-ctx-specific-1")
    assert response.status_code == 200
    data = response.json()

    assert data["context_id"] == "test-ctx-specific-1"
    assert "total_forms" in data
    assert "sample_statements" in data
    assert data["total_forms"] >= 1


def test_get_nonexistent_context():
    """Test getting a non-existent context."""
    response = client.get("/api/v1/contexts/nonexistent-context-12345")
    # Should return 404 or empty context
    assert response.status_code in [404, 200]


# ============================================================================
# Edge Cases & Error Handling
# ============================================================================

def test_parse_very_long_text():
    """Test parsing very long text."""
    long_text = "This is a test statement. " * 100
    response = client.post("/api/v1/parse", json={
        "text": long_text,
        "context_id": "test-ctx-long"
    })
    # Should either succeed or return appropriate error
    assert response.status_code in [200, 400, 422]


def test_parse_special_characters():
    """Test parsing text with special characters."""
    response = client.post("/api/v1/parse", json={
        "text": "John's resume is impressive! @#$%",
        "context_id": "test-ctx-special"
    })
    # Should handle gracefully
    assert response.status_code in [200, 400, 422]


def test_invalid_endpoint():
    """Test accessing invalid endpoint."""
    response = client.get("/api/v1/invalid-endpoint-12345")
    assert response.status_code == 404


def test_wrong_http_method():
    """Test using wrong HTTP method."""
    # GET instead of POST for parse
    response = client.get("/api/v1/parse")
    assert response.status_code == 405  # Method not allowed


# ============================================================================
# Documentation Tests
# ============================================================================

def test_openapi_docs():
    """Test OpenAPI documentation is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data


def test_swagger_ui():
    """Test Swagger UI is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc():
    """Test ReDoc is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_parse_stores_in_memory():
    """Test that parsing a statement stores the form in memory."""
    with patch("glcs.api.routes.glcs.encoder.add_embedding_to_form") as mock_add_embedding, \
         patch("glcs.api.routes.glcs.memory.store_form") as mock_store:
         
        response = client.post("/api/v1/parse", json={
            "text": "Zack is a teacher",
            "context_id": "test-ctx-mem-1"
        })
        
        assert response.status_code == 200
        assert mock_add_embedding.called
        assert mock_store.called

def test_batch_parse_stores_in_memory():
    """Test that batch parsing statements stores forms in memory."""
    with patch("glcs.api.routes.glcs.encoder.add_embeddings_to_forms") as mock_add_embeddings, \
         patch("glcs.api.routes.glcs.memory.store_form") as mock_store:
         
        response = client.post("/api/v1/parse/batch", json={
            "texts": ["Yara is a student", "Xavier is a principal"],
            "context_id": "test-ctx-mem-2"
        })
        
        assert response.status_code == 200
        assert mock_add_embeddings.called
        assert mock_store.call_count == 2

def test_parse_memory_error_handled():
    """Test that a memory storage failure does not fail the parse response."""
    with patch("glcs.api.routes.glcs.memory.store_form", side_effect=Exception("Memory error")):
        response = client.post("/api/v1/parse", json={
            "text": "Zack is a teacher",
            "context_id": "test-ctx-mem-fail"
        })
        assert response.status_code == 200


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
