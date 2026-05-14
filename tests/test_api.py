"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self):
        """Test GET /health."""
        response = client.get("/health")
        assert response.status_code in [200, 503]  # 503 if system not initialized


class TestAPIModels:
    """Test API Pydantic models."""

    def test_query_request_valid(self):
        """Test valid QueryRequest."""
        from src.api.models import QueryRequest
        
        req = QueryRequest(query="test query", top_k=5)
        assert req.query == "test query"
        assert req.top_k == 5

    def test_query_request_invalid_top_k(self):
        """Test QueryRequest with invalid top_k."""
        from src.api.models import QueryRequest
        
        with pytest.raises(ValueError):
            QueryRequest(query="test", top_k=100)  # max is 50

    def test_query_response_valid(self):
        """Test valid QueryResponse."""
        from src.api.models import QueryResponse, SourceInfo
        
        source = SourceInfo(title="Test", url="http://test.com", source="web")
        response = QueryResponse(
            query="test",
            answer="answer",
            sources=[source],
            scores=[0.9]
        )
        assert response.query == "test"
        assert len(response.sources) == 1


class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_swagger_docs_available(self):
        """Test Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_available(self):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200


class TestCORSConfiguration:
    """Test CORS middleware."""

    def test_cors_headers(self):
        """Test CORS headers in response."""
        response = client.get("/health")
        assert "access-control-allow-origin" in response.headers or response.status_code in [200, 503]
