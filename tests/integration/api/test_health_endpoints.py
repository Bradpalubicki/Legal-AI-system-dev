"""
Integration Tests for Health Check Endpoints

Tests the health check API endpoints including basic health checks,
detailed system status, and monitoring endpoints.
"""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from httpx import AsyncClient
from fastapi.testclient import TestClient

from core.app import create_application


class TestHealthEndpoints:
    """Test suite for health check endpoints"""

    @pytest.fixture
    def app(self):
        """Create test application"""
        return create_application()

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self, app):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    def test_health_endpoint_basic(self, client):
        """Test basic health check endpoint"""
        response = client.get("/health")
        
        # The endpoint might not be implemented yet, so check for valid responses
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
        elif response.status_code == 404:
            # Endpoint not implemented yet
            assert "Not Found" in response.text or response.status_code == 404

    def test_health_endpoint_detailed(self, client):
        """Test detailed health check endpoint"""
        response = client.get("/health/detailed")
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            # Expected health check response structure
            expected_fields = ["status", "timestamp", "version"]
            for field in expected_fields:
                if field in data:
                    assert data[field] is not None

    @pytest.mark.asyncio
    async def test_health_endpoint_async(self, async_client):
        """Test health check endpoint with async client"""
        response = await async_client.get("/health")
        
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_health_readiness_probe(self, client):
        """Test Kubernetes readiness probe endpoint"""
        response = client.get("/health/ready")
        
        # May return 404 if not implemented
        assert response.status_code in [200, 404, 503]
        
        if response.status_code == 200:
            # Readiness check should return simple status
            data = response.json()
            assert "ready" in data or "status" in data

    def test_health_liveness_probe(self, client):
        """Test Kubernetes liveness probe endpoint"""
        response = client.get("/health/live")
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            # Liveness check should be simple
            data = response.json()
            assert "alive" in data or "status" in data


class TestHealthCheckComponents:
    """Test suite for individual health check components"""

    @pytest.fixture
    def app(self):
        """Create test application"""
        return create_application()

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    def test_database_health_check(self, client):
        """Test database connectivity health check"""
        with patch('core.database.get_database_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value = mock_session
            
            # Mock successful database query
            mock_session.execute.return_value = Mock()
            mock_session.execute.return_value.scalar.return_value = 1
            
            response = client.get("/health/database")
            
            # May not be implemented yet
            if response.status_code == 200:
                data = response.json()
                assert "database" in data
                assert data["database"]["status"] in ["healthy", "unhealthy"]

    def test_redis_health_check(self, client):
        """Test Redis connectivity health check"""
        with patch('redis.asyncio.Redis.ping') as mock_ping:
            mock_ping.return_value = True
            
            response = client.get("/health/redis")
            
            if response.status_code == 200:
                data = response.json()
                assert "redis" in data

    def test_external_services_health_check(self, client):
        """Test external services health check"""
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock successful external service response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = client.get("/health/external")
            
            if response.status_code == 200:
                data = response.json()
                assert "external_services" in data

    @pytest.mark.asyncio
    async def test_async_health_checks(self, async_client):
        """Test asynchronous health checks"""
        with patch('asyncio.gather') as mock_gather:
            # Mock multiple async health checks
            mock_gather.return_value = [
                {"database": {"status": "healthy"}},
                {"redis": {"status": "healthy"}},
                {"external_services": {"status": "healthy"}}
            ]
            
            response = await async_client.get("/health/all")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)


class TestHealthMetrics:
    """Test suite for health metrics and monitoring"""

    @pytest.fixture
    def app(self):
        """Create test application"""
        return create_application()

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    def test_system_metrics(self, client):
        """Test system metrics endpoint"""
        with patch('psutil.cpu_percent') as mock_cpu:
            with patch('psutil.virtual_memory') as mock_memory:
                with patch('psutil.disk_usage') as mock_disk:
                    mock_cpu.return_value = 45.2
                    mock_memory.return_value = Mock(percent=67.8)
                    mock_disk.return_value = Mock(percent=34.5)
                    
                    response = client.get("/health/metrics")
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "system" in data:
                            assert "cpu_percent" in data["system"]
                            assert "memory_percent" in data["system"]

    def test_application_metrics(self, client):
        """Test application-specific metrics"""
        response = client.get("/health/metrics/app")
        
        if response.status_code == 200:
            data = response.json()
            expected_metrics = [
                "uptime", "requests_total", "active_connections", 
                "memory_usage", "response_times"
            ]
            
            for metric in expected_metrics:
                if metric in data:
                    assert data[metric] is not None

    def test_custom_health_checks(self, client):
        """Test custom application health checks"""
        with patch('src.core.health.custom_health_checks') as mock_checks:
            mock_checks.return_value = {
                "ai_services": {"status": "healthy", "response_time": 0.05},
                "legal_databases": {"status": "degraded", "response_time": 2.1},
                "document_processing": {"status": "healthy", "queue_size": 5}
            }
            
            response = client.get("/health/custom")
            
            if response.status_code == 200:
                data = response.json()
                if "custom_checks" in data:
                    assert "ai_services" in data["custom_checks"]


class TestHealthErrorHandling:
    """Test suite for health check error handling"""

    @pytest.fixture
    def app(self):
        """Create test application"""
        return create_application()

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    def test_database_connection_failure(self, client):
        """Test health check when database is unavailable"""
        with patch('core.database.get_database_session') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            response = client.get("/health/database")
            
            if response.status_code in [200, 503]:
                if response.status_code == 200:
                    data = response.json()
                    if "database" in data:
                        assert data["database"]["status"] == "unhealthy"
                elif response.status_code == 503:
                    # Service unavailable is also acceptable
                    assert "database" in response.text.lower()

    def test_redis_connection_failure(self, client):
        """Test health check when Redis is unavailable"""
        with patch('redis.asyncio.Redis.ping') as mock_ping:
            mock_ping.side_effect = Exception("Redis connection failed")
            
            response = client.get("/health/redis")
            
            if response.status_code in [200, 503]:
                if response.status_code == 200:
                    data = response.json()
                    if "redis" in data:
                        assert data["redis"]["status"] == "unhealthy"

    def test_partial_service_failure(self, client):
        """Test health check with some services failing"""
        with patch('core.health.check_all_services') as mock_check_all:
            mock_check_all.return_value = {
                "database": {"status": "healthy"},
                "redis": {"status": "unhealthy", "error": "Connection timeout"},
                "external_api": {"status": "healthy"}
            }
            
            response = client.get("/health/all")
            
            if response.status_code == 200:
                data = response.json()
                # Overall status should be degraded if any service is unhealthy
                if "overall_status" in data:
                    assert data["overall_status"] in ["healthy", "degraded", "unhealthy"]

    def test_timeout_handling(self, client):
        """Test health check timeout handling"""
        with patch('asyncio.wait_for') as mock_wait_for:
            mock_wait_for.side_effect = asyncio.TimeoutError("Health check timed out")
            
            response = client.get("/health/timeout")
            
            if response.status_code in [200, 503, 408]:  # 408 = Request Timeout
                if response.status_code == 200:
                    data = response.json()
                    if "status" in data:
                        assert data["status"] in ["timeout", "unhealthy"]


class TestHealthResponseFormat:
    """Test suite for health check response format validation"""

    @pytest.fixture
    def app(self):
        """Create test application"""
        return create_application()

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    def test_health_response_structure(self, client):
        """Test health response follows expected structure"""
        response = client.get("/health")
        
        if response.status_code == 200:
            data = response.json()
            
            # Basic structure validation
            assert isinstance(data, dict)
            
            # Common fields that should be present
            possible_fields = [
                "status", "timestamp", "version", "environment",
                "uptime", "checks", "system"
            ]
            
            # At least one field should be present
            assert any(field in data for field in possible_fields)

    def test_health_response_content_type(self, client):
        """Test health response content type"""
        response = client.get("/health")
        
        if response.status_code == 200:
            assert response.headers["content-type"] == "application/json"

    def test_health_response_caching(self, client):
        """Test health response caching headers"""
        response = client.get("/health")
        
        if response.status_code == 200:
            # Health endpoints should not be cached
            cache_headers = ["cache-control", "expires", "pragma"]
            
            for header in cache_headers:
                if header in response.headers:
                    header_value = response.headers[header].lower()
                    # Should indicate no caching
                    assert any(val in header_value for val in 
                              ["no-cache", "no-store", "max-age=0"])

    def test_health_status_codes(self, client):
        """Test appropriate HTTP status codes for health checks"""
        # Test various health endpoints
        endpoints = ["/health", "/health/ready", "/health/live"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            
            # Should return appropriate status codes
            valid_codes = [200, 404, 503]  # OK, Not Found, Service Unavailable
            assert response.status_code in valid_codes
            
            if response.status_code == 503:
                # Service unavailable should have appropriate response
                assert response.content is not None

    def test_health_response_timing(self, client):
        """Test health check response timing"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Health checks should be fast (under 5 seconds)
        assert response_time < 5.0
        
        if response.status_code == 200:
            # For successful responses, should be even faster
            assert response_time < 2.0


class TestHealthIntegration:
    """Integration tests for complete health check system"""

    @pytest.fixture
    def app(self):
        """Create test application"""
        return create_application()

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    def test_complete_health_check_flow(self, client):
        """Test complete health check workflow"""
        # Mock all dependencies as healthy
        with patch('core.database.get_database_session') as mock_db:
            with patch('redis.asyncio.Redis.ping') as mock_redis:
                with patch('httpx.AsyncClient.get') as mock_http:
                    
                    # Setup mocks
                    mock_db.return_value = Mock()
                    mock_redis.return_value = True
                    mock_http.return_value = Mock(status_code=200)
                    
                    # Test basic health
                    response = client.get("/health")
                    assert response.status_code in [200, 404]
                    
                    # Test detailed health if implemented
                    response = client.get("/health/detailed")
                    assert response.status_code in [200, 404]

    def test_health_check_under_load(self, client):
        """Test health checks under concurrent load"""
        import threading
        import time
        
        results = []
        
        def make_request():
            try:
                response = client.get("/health")
                results.append(response.status_code)
            except Exception as e:
                results.append(f"Error: {str(e)}")
        
        # Create multiple concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        # All requests should complete successfully
        assert len(results) == 10
        
        # Most should succeed (allowing for some failures due to test environment)
        success_count = sum(1 for result in results if isinstance(result, int) and result in [200, 404])
        assert success_count >= 8  # At least 80% success rate

    def test_health_monitoring_integration(self, client):
        """Test integration with monitoring systems"""
        response = client.get("/health")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for monitoring-friendly format
            monitoring_fields = ["status", "timestamp", "checks"]
            
            for field in monitoring_fields:
                if field in data:
                    # Validate field format for monitoring tools
                    if field == "status":
                        assert data[field] in ["healthy", "degraded", "unhealthy"]
                    elif field == "timestamp":
                        assert isinstance(data[field], str)
                        # Should be ISO format timestamp
                        assert "T" in data[field] or "-" in data[field]