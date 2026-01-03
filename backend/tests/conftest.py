"""
Pytest configuration and fixtures for backend tests

This module sets up the test environment, including:
- Path configuration for imports
- Environment variable mocking
- Shared fixtures
- Test database setup
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add backend root to Python path - use absolute path
backend_root = Path(__file__).parent.parent.resolve()
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

# Change working directory to backend root for consistent imports
os.chdir(backend_root)

# Mock environment variables for testing
TEST_ENV = {
    'ENVIRONMENT': 'development',
    'DEBUG': 'True',
    'LOG_LEVEL': 'INFO',
    'SECRET_KEY': 'test-secret-key-for-testing-only',
    'JWT_SECRET_KEY': 'test-jwt-secret-for-testing-only',
    'OPENAI_API_KEY': 'test-openai-key',
    'ANTHROPIC_API_KEY': 'test-anthropic-key',
    'DATABASE_URL': 'sqlite:///:memory:',  # In-memory database for tests
    'CORS_ORIGINS': 'http://localhost:3000',
}


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    with patch.dict(os.environ, TEST_ENV, clear=False):
        yield


@pytest.fixture(scope="module")
def test_app():
    """
    Create a test FastAPI application instance.
    This fixture creates a minimal app for testing without full initialization.
    """
    # Import FastAPI here to avoid main.py's complex initialization
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import importlib.util
    import sys

    # Create minimal test app
    app = FastAPI(
        title="Legal AI System",
        description="AI-Powered Legal Document Analysis System",
        version="1.0.0",
    )

    # Add CORS for testing
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Load health.py directly without triggering app package imports
    health_py_path = backend_root / "app" / "api" / "health.py"
    spec = importlib.util.spec_from_file_location("health_module", health_py_path)
    health_module = importlib.util.module_from_spec(spec)
    sys.modules["health_module"] = health_module
    spec.loader.exec_module(health_module)

    # Get the router from the health module
    health_router = health_module.router
    app.include_router(health_router)

    # Add root endpoint
    @app.get("/")
    async def root():
        return {"message": "Legal AI System API", "status": "running", "version": "1.0.0"}

    return app


@pytest.fixture(scope="module")
def test_client(test_app):
    """
    Create a TestClient for the FastAPI application.
    """
    from fastapi.testclient import TestClient

    # Mock the health check functions that try to import from app package
    async def mock_check_database():
        return True, {"status": "healthy", "type": "sqlite", "message": "Mock database"}

    async def mock_check_redis():
        return True, {"status": "not_configured", "message": "Mock Redis"}

    async def mock_check_storage():
        return True, {"status": "not_configured", "message": "Mock storage"}

    async def mock_check_ai_services():
        return True, {"status": "configured", "services": {"openai": "configured", "anthropic": "configured"}, "message": "Mock AI services"}

    # Patch the health check functions
    with patch('health_module.check_database', mock_check_database), \
         patch('health_module.check_redis', mock_check_redis), \
         patch('health_module.check_storage', mock_check_storage), \
         patch('health_module.check_ai_services', mock_check_ai_services):

        yield TestClient(test_app)


@pytest.fixture(scope="function")
def clean_database():
    """
    Provide a clean database for each test.
    Uses SQLite in-memory database.
    """
    from app.src.core.database import Base, engine

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)


# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (may require external services)"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests (fast, isolated)"
    )
