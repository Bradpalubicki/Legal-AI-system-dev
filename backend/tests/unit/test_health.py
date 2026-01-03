"""
Unit tests for health check endpoints

Tests use FastAPI's TestClient for isolated testing without requiring
a running server.
"""

import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.unit
def test_root_endpoint(test_client):
    """Test that the root endpoint returns basic info."""
    response = test_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Legal AI System API"
    assert data["status"] == "running"
    assert data["version"] == "1.0.0"


@pytest.mark.unit
def test_health_endpoint(test_client):
    """Test basic health check endpoint."""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "legal-ai-backend"


@pytest.mark.unit
def test_health_endpoint_content_type(test_client):
    """Test that health endpoint returns JSON."""
    response = test_client.get("/health")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


@pytest.mark.unit
def test_health_live_endpoint(test_client):
    """Test liveness probe endpoint."""
    response = test_client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert data["service"] == "legal-ai-backend"


@pytest.mark.unit
def test_health_ready_endpoint(test_client):
    """Test readiness probe endpoint."""
    response = test_client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["service"] == "legal-ai-backend"


@pytest.mark.unit
def test_health_system_endpoint(test_client):
    """Test comprehensive system health check."""
    response = test_client.get("/health/system")

    assert response.status_code in [200, 503]  # May be 503 if services unavailable
    data = response.json()

    # Check structure
    assert "status" in data
    assert "timestamp" in data
    assert "service" in data
    assert "environment" in data
    assert "checks" in data

    # Check that major systems are checked
    checks = data["checks"]
    assert "database" in checks
    # Redis/storage/AI may not be configured in test environment
    assert "redis" in checks
    assert "storage" in checks
    assert "ai_services" in checks


@pytest.mark.unit
def test_health_system_endpoint_structure(test_client):
    """Test system health endpoint has all required fields."""
    response = test_client.get("/health/system")

    data = response.json()
    required_fields = ["status", "timestamp", "service", "environment", "checks"]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


@pytest.mark.unit
def test_docs_endpoint_accessible(test_client):
    """Test that API docs are accessible."""
    response = test_client.get("/docs")

    assert response.status_code == 200


@pytest.mark.unit
def test_openapi_schema_accessible(test_client):
    """Test that OpenAPI schema is accessible."""
    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "Legal AI System"


@pytest.mark.unit
def test_health_endpoint_no_sensitive_data(test_client):
    """Test that health endpoints don't expose sensitive information."""
    response = test_client.get("/health/system")

    data_str = str(response.json()).lower()

    # Ensure no sensitive data is exposed
    sensitive_keywords = ["password", "secret", "api_key", "token", "credential"]

    for keyword in sensitive_keywords:
        assert keyword not in data_str, f"Health endpoint exposes sensitive data: {keyword}"
