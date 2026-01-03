"""
Unit Tests for Core Configuration Module

Tests the configuration management system including environment variable
parsing, validation, and settings initialization.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from core.config import Settings, get_settings


class TestSettings:
    """Test suite for Settings configuration class"""

    def test_default_settings(self):
        """Test default configuration values"""
        settings = Settings()
        
        assert settings.APP_NAME == "Legal AI System"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.ENVIRONMENT == "development"
        assert settings.DEBUG is False
        assert settings.API_PORT == 8000
        assert settings.DATABASE_PORT == 5432
        assert settings.REDIS_PORT == 6379

    def test_environment_variable_override(self):
        """Test that environment variables override defaults"""
        with patch.dict(os.environ, {
            'APP_NAME': 'Test Legal AI',
            'DEBUG': 'true',
            'API_PORT': '9000'
        }):
            settings = Settings()
            assert settings.APP_NAME == 'Test Legal AI'
            assert settings.DEBUG is True
            assert settings.API_PORT == 9000

    def test_cors_origins_string_parsing(self):
        """Test parsing CORS origins from string"""
        with patch.dict(os.environ, {
            'CORS_ORIGINS': 'http://localhost:3000,https://example.com,https://app.legal.com'
        }):
            settings = Settings()
            assert settings.CORS_ORIGINS == [
                'http://localhost:3000',
                'https://example.com',
                'https://app.legal.com'
            ]

    def test_cors_origins_list_handling(self):
        """Test that CORS origins list is preserved"""
        settings = Settings(CORS_ORIGINS=['http://test.com', 'https://secure.com'])
        assert settings.CORS_ORIGINS == ['http://test.com', 'https://secure.com']

    def test_allowed_file_types_parsing(self):
        """Test parsing allowed file types from string"""
        with patch.dict(os.environ, {
            'ALLOWED_FILE_TYPES': 'pdf,docx,txt,rtf,doc'
        }):
            settings = Settings()
            assert settings.ALLOWED_FILE_TYPES == ['pdf', 'docx', 'txt', 'rtf', 'doc']

    def test_log_level_validation_valid(self):
        """Test valid log level validation"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            with patch.dict(os.environ, {'LOG_LEVEL': level}):
                settings = Settings()
                assert settings.LOG_LEVEL == level

    def test_log_level_validation_invalid(self):
        """Test invalid log level raises validation error"""
        with patch.dict(os.environ, {'LOG_LEVEL': 'INVALID'}):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "LOG_LEVEL must be one of" in str(exc_info.value)

    def test_environment_validation_valid(self):
        """Test valid environment validation"""
        valid_envs = ["development", "staging", "production", "testing"]
        for env in valid_envs:
            with patch.dict(os.environ, {'ENVIRONMENT': env}):
                settings = Settings()
                assert settings.ENVIRONMENT == env

    def test_environment_validation_invalid(self):
        """Test invalid environment raises validation error"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'invalid'}):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "ENVIRONMENT must be one of" in str(exc_info.value)

    def test_database_url_construction(self):
        """Test database URL construction with components"""
        with patch.dict(os.environ, {
            'DATABASE_HOST': 'db.example.com',
            'DATABASE_PORT': '5433',
            'DATABASE_NAME': 'test_db',
            'DATABASE_USER': 'test_user',
            'DATABASE_PASSWORD': 'test_pass'
        }):
            settings = Settings()
            assert settings.DATABASE_HOST == 'db.example.com'
            assert settings.DATABASE_PORT == 5433
            assert settings.DATABASE_NAME == 'test_db'
            assert settings.DATABASE_USER == 'test_user'
            assert settings.DATABASE_PASSWORD == 'test_pass'

    def test_redis_url_with_password(self):
        """Test Redis URL with password"""
        with patch.dict(os.environ, {
            'REDIS_PASSWORD': 'secret123'
        }):
            settings = Settings()
            assert settings.REDIS_PASSWORD == 'secret123'

    def test_ai_service_configuration(self):
        """Test AI service configuration settings"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123',
            'OPENAI_DEFAULT_MODEL': 'gpt-4',
            'ANTHROPIC_API_KEY': 'ant-test456',
            'AZURE_OPENAI_ENABLED': 'true'
        }):
            settings = Settings()
            assert settings.OPENAI_API_KEY == 'sk-test123'
            assert settings.OPENAI_DEFAULT_MODEL == 'gpt-4'
            assert settings.ANTHROPIC_API_KEY == 'ant-test456'
            assert settings.AZURE_OPENAI_ENABLED is True

    def test_security_settings(self):
        """Test security-related configuration"""
        settings = Settings()
        
        # Verify default security settings
        assert len(settings.JWT_SECRET) >= 32
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_EXPIRES_IN == "7d"
        assert len(settings.SESSION_SECRET) >= 32
        assert len(settings.ENCRYPTION_KEY) >= 32

    def test_legal_api_settings(self):
        """Test legal API configuration"""
        with patch.dict(os.environ, {
            'COURTLISTENER_API_KEY': 'cl-test123',
            'PACER_USERNAME': 'testuser',
            'PACER_PASSWORD': 'testpass',
            'WESTLAW_ENABLED': 'true',
            'LEXISNEXIS_ENABLED': 'false'
        }):
            settings = Settings()
            assert settings.COURTLISTENER_API_KEY == 'cl-test123'
            assert settings.PACER_USERNAME == 'testuser'
            assert settings.PACER_PASSWORD == 'testpass'
            assert settings.WESTLAW_ENABLED is True
            assert settings.LEXISNEXIS_ENABLED is False

    def test_monitoring_settings(self):
        """Test monitoring and observability configuration"""
        with patch.dict(os.environ, {
            'SENTRY_DSN': 'https://test@sentry.io/123',
            'SENTRY_ENABLED': 'true',
            'PROMETHEUS_ENABLED': 'true'
        }):
            settings = Settings()
            assert settings.SENTRY_DSN == 'https://test@sentry.io/123'
            assert settings.SENTRY_ENABLED is True
            assert settings.PROMETHEUS_ENABLED is True

    def test_file_storage_settings(self):
        """Test file storage configuration"""
        with patch.dict(os.environ, {
            'MAX_DOCUMENT_SIZE_MB': '200',
            'AWS_S3_ENABLED': 'true',
            'AWS_REGION': 'us-west-2',
            'AWS_S3_BUCKET': 'legal-docs-bucket'
        }):
            settings = Settings()
            assert settings.MAX_DOCUMENT_SIZE_MB == 200
            assert settings.AWS_S3_ENABLED is True
            assert settings.AWS_REGION == 'us-west-2'
            assert settings.AWS_S3_BUCKET == 'legal-docs-bucket'

    def test_celery_configuration(self):
        """Test Celery background task configuration"""
        with patch.dict(os.environ, {
            'CELERY_WORKER_CONCURRENCY': '8',
            'CELERY_BROKER_URL': 'redis://redis.example.com:6379/2'
        }):
            settings = Settings()
            assert settings.CELERY_WORKER_CONCURRENCY == 8
            assert settings.CELERY_BROKER_URL == 'redis://redis.example.com:6379/2'

    def test_email_settings(self):
        """Test email configuration"""
        with patch.dict(os.environ, {
            'SMTP_HOST': 'smtp.example.com',
            'SMTP_PORT': '587',
            'SMTP_USER': 'noreply@legal.com',
            'SMTP_PASSWORD': 'emailpass123',
            'FROM_EMAIL': 'system@legal.com'
        }):
            settings = Settings()
            assert settings.SMTP_HOST == 'smtp.example.com'
            assert settings.SMTP_PORT == 587
            assert settings.SMTP_USER == 'noreply@legal.com'
            assert settings.SMTP_PASSWORD == 'emailpass123'
            assert settings.FROM_EMAIL == 'system@legal.com'

    def test_rate_limiting_settings(self):
        """Test rate limiting configuration"""
        with patch.dict(os.environ, {
            'RATE_LIMIT_ENABLED': 'false',
            'RATE_LIMIT_REQUESTS_PER_MINUTE': '500'
        }):
            settings = Settings()
            assert settings.RATE_LIMIT_ENABLED is False
            assert settings.RATE_LIMIT_REQUESTS_PER_MINUTE == 500

    def test_boolean_parsing(self):
        """Test boolean environment variable parsing"""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('on', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('0', False),
            ('no', False),
            ('off', False)
        ]
        
        for str_val, expected in test_cases:
            with patch.dict(os.environ, {'DEBUG': str_val}):
                settings = Settings()
                assert settings.DEBUG == expected

    def test_case_sensitivity(self):
        """Test that configuration is case sensitive"""
        with patch.dict(os.environ, {
            'log_level': 'debug',  # lowercase, should not override
            'LOG_LEVEL': 'ERROR'   # uppercase, should override
        }):
            settings = Settings()
            assert settings.LOG_LEVEL == 'ERROR'

    def test_env_file_loading(self):
        """Test .env file configuration loading"""
        # This test would require creating a temporary .env file
        # For now, we'll test that the Config class is properly set
        config = Settings.Config
        assert config.env_file == ".env"
        assert config.env_file_encoding == "utf-8"
        assert config.case_sensitive is True


class TestGetSettings:
    """Test suite for get_settings function"""

    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance"""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_caching(self):
        """Test that get_settings uses LRU cache"""
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should return the same instance due to caching
        assert settings1 is settings2

    @patch('core.config.Settings')
    def test_get_settings_cache_invalidation(self, mock_settings):
        """Test cache behavior with mock"""
        mock_instance = MagicMock()
        mock_settings.return_value = mock_instance
        
        # Clear any existing cache
        get_settings.cache_clear()
        
        # First call should create new instance
        result1 = get_settings()
        assert mock_settings.call_count == 1
        
        # Second call should use cached instance
        result2 = get_settings()
        assert mock_settings.call_count == 1  # Not incremented
        assert result1 is result2


class TestConfigurationIntegration:
    """Integration tests for configuration system"""

    def test_production_configuration(self):
        """Test production-specific configuration"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'SENTRY_ENABLED': 'true',
            'LOG_LEVEL': 'INFO'
        }):
            settings = Settings()
            assert settings.ENVIRONMENT == 'production'
            assert settings.DEBUG is False
            assert settings.SENTRY_ENABLED is True
            assert settings.LOG_LEVEL == 'INFO'

    def test_development_configuration(self):
        """Test development-specific configuration"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'DEBUG': 'true',
            'LOG_LEVEL': 'DEBUG'
        }):
            settings = Settings()
            assert settings.ENVIRONMENT == 'development'
            assert settings.DEBUG is True
            assert settings.LOG_LEVEL == 'DEBUG'

    def test_testing_configuration(self):
        """Test testing-specific configuration"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'testing',
            'DATABASE_URL': 'sqlite+aiosqlite:///./test.db',
            'REDIS_DB': '15'
        }):
            settings = Settings()
            assert settings.ENVIRONMENT == 'testing'
            assert 'test.db' in settings.DATABASE_URL
            assert settings.REDIS_DB == 15

    def test_minimal_configuration(self):
        """Test system works with minimal configuration"""
        # Clear environment variables that might interfere
        env_vars_to_clear = [
            'DATABASE_URL', 'REDIS_URL', 'OPENAI_API_KEY', 
            'ANTHROPIC_API_KEY', 'SENTRY_DSN'
        ]
        
        with patch.dict(os.environ, {var: '' for var in env_vars_to_clear}, clear=False):
            settings = Settings()
            
            # Should still work with defaults
            assert settings.APP_NAME == "Legal AI System"
            assert settings.ENVIRONMENT == "development"
            assert settings.API_PORT == 8000

    def test_all_required_fields_present(self):
        """Test that all required configuration fields are present"""
        settings = Settings()
        
        # Core application settings
        assert hasattr(settings, 'APP_NAME')
        assert hasattr(settings, 'APP_VERSION')
        assert hasattr(settings, 'ENVIRONMENT')
        
        # Database settings
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'DATABASE_HOST')
        
        # Security settings
        assert hasattr(settings, 'JWT_SECRET')
        assert hasattr(settings, 'ENCRYPTION_KEY')
        
        # API settings
        assert hasattr(settings, 'API_PORT')
        assert hasattr(settings, 'CORS_ORIGINS')

    def test_sensitive_data_not_logged(self):
        """Test that sensitive configuration is not accidentally logged"""
        settings = Settings()
        
        # These should not appear in string representation
        settings_str = str(settings)
        sensitive_fields = [
            'JWT_SECRET', 'DATABASE_PASSWORD', 'ENCRYPTION_KEY',
            'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'SENTRY_DSN'
        ]
        
        # Note: This is a basic check. In practice, you'd want more sophisticated
        # protection against logging sensitive data
        for field in sensitive_fields:
            # The actual values shouldn't appear in string representation
            if hasattr(settings, field):
                field_value = getattr(settings, field)
                if field_value and len(str(field_value)) > 10:
                    # For longer values that might be secrets
                    assert field_value not in settings_str or field_value == "None"