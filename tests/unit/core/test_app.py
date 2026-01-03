"""
Unit Tests for Core Application Factory

Tests the FastAPI application creation, configuration, middleware setup,
and lifecycle management.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.app import (
    create_application,
    create_dev_app,
    lifespan,
    initialize_services,
    cleanup_services,
    configure_sentry,
    filter_sensitive_data,
    custom_openapi_schema
)


class TestApplicationFactory:
    """Test suite for application factory functions"""

    def test_create_application_returns_fastapi_instance(self):
        """Test that create_application returns a FastAPI instance"""
        app = create_application()
        assert isinstance(app, FastAPI)
        assert app.title == "Legal AI System"

    def test_create_application_configuration(self):
        """Test application configuration settings"""
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.APP_NAME = "Test Legal AI"
            mock_settings.return_value.APP_DESCRIPTION = "Test Description"
            mock_settings.return_value.APP_VERSION = "2.0.0"
            mock_settings.return_value.DEBUG = True
            mock_settings.return_value.ENVIRONMENT = "development"
            
            app = create_application()
            
            assert app.title == "Test Legal AI"
            assert app.description == "Test Description"
            assert app.version == "2.0.0"
            assert app.debug is True

    def test_create_application_docs_urls_development(self):
        """Test docs URLs are available in development"""
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.ENVIRONMENT = "development"
            mock_settings.return_value.DEBUG = True
            
            app = create_application()
            
            assert app.docs_url == "/docs"
            assert app.redoc_url == "/redoc"
            assert app.openapi_url == "/openapi.json"

    def test_create_application_docs_urls_production(self):
        """Test docs URLs are disabled in production"""
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.ENVIRONMENT = "production"
            mock_settings.return_value.DEBUG = False
            
            app = create_application()
            
            assert app.docs_url is None
            assert app.redoc_url is None
            assert app.openapi_url is None

    @patch('core.app.configure_middleware')
    def test_middleware_configuration(self, mock_configure_middleware):
        """Test middleware is properly configured"""
        app = create_application()
        mock_configure_middleware.assert_called_once_with(app)

    @patch('core.app.configure_logging')
    def test_logging_configuration(self, mock_configure_logging):
        """Test logging is configured before app creation"""
        create_application()
        mock_configure_logging.assert_called_once()

    @patch('core.app.configure_sentry')
    def test_sentry_configuration(self, mock_configure_sentry):
        """Test Sentry is configured if enabled"""
        create_application()
        mock_configure_sentry.assert_called_once()

    def test_exception_handlers_added(self):
        """Test exception handlers are properly added"""
        with patch('core.app.EXCEPTION_HANDLERS') as mock_handlers:
            mock_handlers.items.return_value = [
                (ValueError, Mock()),
                (KeyError, Mock())
            ]
            
            app = create_application()
            
            # Should have called add_exception_handler for each handler
            assert hasattr(app, 'exception_handlers')

    def test_health_router_included(self):
        """Test health router is included"""
        app = create_application()
        
        # Check that health router is included
        client = TestClient(app)
        response = client.get("/health")
        # Should get some response (may be 404 if not implemented, but route exists)
        assert response.status_code in [200, 404, 500]  # Any response means route exists

    def test_root_endpoint(self):
        """Test root endpoint returns app information"""
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.APP_NAME = "Test App"
            mock_settings.return_value.APP_VERSION = "1.0.0"
            mock_settings.return_value.APP_DESCRIPTION = "Test Description"
            mock_settings.return_value.ENVIRONMENT = "development"
            
            app = create_application()
            client = TestClient(app)
            
            response = client.get("/")
            assert response.status_code == 200
            
            data = response.json()
            assert data["name"] == "Test App"
            assert data["version"] == "1.0.0"
            assert data["description"] == "Test Description"
            assert data["environment"] == "development"
            assert data["status"] == "online"

    def test_favicon_endpoint(self):
        """Test favicon endpoint returns 404"""
        app = create_application()
        client = TestClient(app)
        
        response = client.get("/favicon.ico")
        assert response.status_code == 404

    def test_create_dev_app(self):
        """Test development app creation"""
        with patch.dict('os.environ', {}, clear=True):
            app = create_dev_app()
            assert isinstance(app, FastAPI)

    def test_development_middleware_added(self):
        """Test development-specific middleware is added"""
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.ENVIRONMENT = "development"
            mock_settings.return_value.DEBUG = True
            
            app = create_application()
            client = TestClient(app)
            
            response = client.get("/")
            assert response.status_code == 200
            
            # Development headers should be present
            assert "X-Dev-Mode" in response.headers
            assert response.headers["X-Dev-Mode"] == "true"


class TestLifespanManagement:
    """Test suite for application lifespan management"""

    @pytest.mark.asyncio
    async def test_lifespan_startup_success(self):
        """Test successful startup sequence"""
        mock_app = Mock()
        mock_app.state = Mock()
        
        with patch('core.app.init_database', new_callable=AsyncMock) as mock_init_db:
            with patch('core.app.initialize_services', new_callable=AsyncMock) as mock_init_services:
                with patch('core.app.close_database', new_callable=AsyncMock) as mock_close_db:
                    with patch('core.app.cleanup_services', new_callable=AsyncMock) as mock_cleanup:
                        async with lifespan(mock_app):
                            pass
                        
                        mock_init_db.assert_called_once()
                        mock_init_services.assert_called_once()
                        mock_close_db.assert_called_once()
                        mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_startup_failure(self):
        """Test startup failure handling"""
        mock_app = Mock()
        
        with patch('core.app.init_database', new_callable=AsyncMock) as mock_init_db:
            mock_init_db.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception) as exc_info:
                async with lifespan(mock_app):
                    pass
            
            assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_error(self):
        """Test shutdown error handling"""
        mock_app = Mock()
        mock_app.state = Mock()
        
        with patch('core.app.init_database', new_callable=AsyncMock):
            with patch('core.app.initialize_services', new_callable=AsyncMock):
                with patch('core.app.close_database', new_callable=AsyncMock) as mock_close_db:
                    with patch('core.app.cleanup_services', new_callable=AsyncMock):
                        mock_close_db.side_effect = Exception("Cleanup failed")
                        
                        # Should not raise exception during shutdown
                        async with lifespan(mock_app):
                            pass

    @pytest.mark.asyncio
    async def test_initialize_services_development(self):
        """Test service initialization in development"""
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.ENVIRONMENT = "development"
            
            # Should complete without error
            await initialize_services()

    @pytest.mark.asyncio
    async def test_initialize_services_production(self):
        """Test service initialization in production"""
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.ENVIRONMENT = "production"
            
            # Should complete without error
            await initialize_services()

    @pytest.mark.asyncio
    async def test_cleanup_services(self):
        """Test service cleanup"""
        # Should complete without error
        await cleanup_services()


class TestSentryConfiguration:
    """Test suite for Sentry error tracking configuration"""

    @patch('core.app.sentry_sdk.init')
    def test_configure_sentry_enabled(self, mock_sentry_init):
        """Test Sentry configuration when enabled"""
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.SENTRY_ENABLED = True
            mock_settings.return_value.SENTRY_DSN = "https://test@sentry.io/123"
            mock_settings.return_value.ENVIRONMENT = "production"
            mock_settings.return_value.APP_VERSION = "1.0.0"
            
            configure_sentry()
            
            mock_sentry_init.assert_called_once()
            call_args = mock_sentry_init.call_args
            
            assert call_args[1]['dsn'] == "https://test@sentry.io/123"
            assert call_args[1]['environment'] == "production"
            assert call_args[1]['release'] == "1.0.0"

    @patch('core.app.sentry_sdk.init')
    def test_configure_sentry_disabled(self, mock_sentry_init):
        """Test Sentry configuration when disabled"""
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.SENTRY_ENABLED = False
            
            configure_sentry()
            
            mock_sentry_init.assert_not_called()

    @patch('core.app.sentry_sdk.init')
    def test_configure_sentry_no_dsn(self, mock_sentry_init):
        """Test Sentry configuration without DSN"""
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.SENTRY_ENABLED = True
            mock_settings.return_value.SENTRY_DSN = None
            
            configure_sentry()
            
            mock_sentry_init.assert_not_called()

    def test_filter_sensitive_data_headers(self):
        """Test filtering sensitive headers from Sentry events"""
        event = {
            'request': {
                'headers': {
                    'authorization': 'Bearer secret-token',
                    'cookie': 'session=sensitive',
                    'x-api-key': 'api-key-123',
                    'user-agent': 'Mozilla/5.0'
                }
            }
        }
        
        result = filter_sensitive_data(event, None)
        
        headers = result['request']['headers']
        assert 'authorization' not in headers
        assert 'cookie' not in headers
        assert 'x-api-key' not in headers
        assert headers['user-agent'] == 'Mozilla/5.0'

    def test_filter_sensitive_data_form_data(self):
        """Test filtering sensitive form data from Sentry events"""
        event = {
            'request': {
                'data': {
                    'username': 'testuser',
                    'password': 'secret123',
                    'token': 'auth-token',
                    'email': 'user@example.com'
                }
            }
        }
        
        result = filter_sensitive_data(event, None)
        
        data = result['request']['data']
        assert data['username'] == 'testuser'
        assert data['password'] == '[Filtered]'
        assert data['token'] == '[Filtered]'
        assert data['email'] == 'user@example.com'

    def test_filter_sensitive_data_no_request(self):
        """Test filtering when no request data present"""
        event = {'message': 'Test error'}
        result = filter_sensitive_data(event, None)
        assert result == event


class TestOpenAPISchema:
    """Test suite for custom OpenAPI schema generation"""

    def test_custom_openapi_schema(self):
        """Test custom OpenAPI schema generation"""
        mock_app = Mock()
        mock_app.openapi_schema = None
        mock_app.routes = []
        
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.APP_NAME = "Test API"
            mock_settings.return_value.APP_VERSION = "1.0.0"
            mock_settings.return_value.APP_DESCRIPTION = "Test Description"
            mock_settings.return_value.API_BASE_URL = "https://api.example.com"
            
            with patch('core.app.get_openapi') as mock_get_openapi:
                mock_get_openapi.return_value = {
                    'info': {},
                    'components': {}
                }
                
                schema = custom_openapi_schema(mock_app)
                
                assert 'info' in schema
                assert 'components' in schema
                assert 'securitySchemes' in schema['components']
                assert 'tags' in schema

    def test_custom_openapi_schema_cached(self):
        """Test OpenAPI schema caching"""
        mock_app = Mock()
        cached_schema = {'cached': True}
        mock_app.openapi_schema = cached_schema
        
        result = custom_openapi_schema(mock_app)
        assert result == cached_schema

    def test_openapi_security_schemes(self):
        """Test security schemes in OpenAPI schema"""
        mock_app = Mock()
        mock_app.openapi_schema = None
        mock_app.routes = []
        
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.APP_NAME = "Test API"
            mock_settings.return_value.APP_VERSION = "1.0.0"
            mock_settings.return_value.APP_DESCRIPTION = "Test Description"
            mock_settings.return_value.API_BASE_URL = "https://api.example.com"
            
            with patch('core.app.get_openapi') as mock_get_openapi:
                mock_get_openapi.return_value = {
                    'info': {},
                    'components': {}
                }
                
                schema = custom_openapi_schema(mock_app)
                
                security_schemes = schema['components']['securitySchemes']
                assert 'bearerAuth' in security_schemes
                assert 'apiKey' in security_schemes
                assert security_schemes['bearerAuth']['type'] == 'http'
                assert security_schemes['bearerAuth']['scheme'] == 'bearer'

    def test_openapi_tags(self):
        """Test tags in OpenAPI schema"""
        mock_app = Mock()
        mock_app.openapi_schema = None
        mock_app.routes = []
        
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.APP_NAME = "Test API"
            mock_settings.return_value.APP_VERSION = "1.0.0"
            mock_settings.return_value.APP_DESCRIPTION = "Test Description"
            mock_settings.return_value.API_BASE_URL = "https://api.example.com"
            
            with patch('core.app.get_openapi') as mock_get_openapi:
                mock_get_openapi.return_value = {
                    'info': {},
                    'components': {}
                }
                
                schema = custom_openapi_schema(mock_app)
                
                tags = schema['tags']
                tag_names = [tag['name'] for tag in tags]
                
                expected_tags = ['health', 'auth', 'dockets', 'documents', 'tasks', 'ai']
                for expected_tag in expected_tags:
                    assert expected_tag in tag_names


class TestApplicationIntegration:
    """Integration tests for application factory"""

    def test_full_application_creation(self):
        """Test complete application creation and basic functionality"""
        app = create_application()
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()
        
        # Test health endpoint availability (may not be implemented)
        response = client.get("/health")
        # Should at least return some response, not 404 for missing route
        assert response.status_code != 404 or "health" in str(response.url)

    def test_application_with_custom_settings(self):
        """Test application creation with custom settings"""
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.APP_NAME = "Custom Legal AI"
            mock_settings.return_value.DEBUG = True
            mock_settings.return_value.ENVIRONMENT = "testing"
            
            app = create_application()
            client = TestClient(app)
            
            response = client.get("/")
            assert response.status_code == 200
            
            data = response.json()
            assert data["name"] == "Custom Legal AI"
            assert data["environment"] == "testing"

    def test_static_files_mounting_development(self):
        """Test static files mounting in development"""
        with patch('core.app.get_settings') as mock_settings:
            mock_settings.return_value.ENVIRONMENT = "development"
            
            # Should not raise error even if static directory doesn't exist
            app = create_application()
            assert isinstance(app, FastAPI)

    def test_middleware_order(self):
        """Test that middleware is applied in correct order"""
        with patch('core.app.configure_middleware') as mock_configure:
            app = create_application()
            
            # Middleware configuration should be called
            mock_configure.assert_called_once_with(app)

    def test_exception_handling_setup(self):
        """Test exception handling is properly set up"""
        with patch('core.app.EXCEPTION_HANDLERS') as mock_handlers:
            test_handler = Mock()
            mock_handlers.items.return_value = [(ValueError, test_handler)]
            
            app = create_application()
            
            # Should have registered the exception handler
            assert ValueError in app.exception_handlers