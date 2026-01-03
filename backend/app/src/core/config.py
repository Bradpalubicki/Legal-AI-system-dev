"""
Configuration Management for Legal AI System

Centralized configuration using Pydantic settings with environment variable support.
"""

import os
from typing import Optional, List
from functools import lru_cache

from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    APP_NAME: str = Field(default="Legal AI System", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    APP_DESCRIPTION: str = Field(
        default="AI-Powered Legal Document Analysis System", 
        env="APP_DESCRIPTION"
    )
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_BASE_URL: str = Field(default="http://localhost:8000", env="API_BASE_URL")
    API_DEBUG: bool = Field(default=True, env="API_DEBUG")
    
    # =============================================================================
    # DATABASE SETTINGS
    # =============================================================================
    DATABASE_URL: str = Field(
        default="postgresql://legalai_user:secure_password@localhost:5432/legal_ai_system",
        env="DATABASE_URL"
    )
    DATABASE_HOST: str = Field(default="localhost", env="DATABASE_HOST")
    DATABASE_PORT: int = Field(default=5432, env="DATABASE_PORT")
    DATABASE_NAME: str = Field(default="legal_ai_system", env="DATABASE_NAME")
    DATABASE_USER: str = Field(default="legalai_user", env="DATABASE_USER")
    DATABASE_PASSWORD: str = Field(default="secure_password", env="DATABASE_PASSWORD")
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    
    # =============================================================================
    # REDIS SETTINGS
    # =============================================================================
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    USE_FAKE_REDIS: bool = Field(default=False, env="USE_FAKE_REDIS")
    USE_LOCAL_STORAGE: bool = Field(default=False, env="USE_LOCAL_STORAGE")

    # =============================================================================
    # AI SERVICE SETTINGS
    # =============================================================================
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_ORG_ID: Optional[str] = Field(default=None, env="OPENAI_ORG_ID")
    OPENAI_DEFAULT_MODEL: str = Field(default="gpt-4o", env="OPENAI_DEFAULT_MODEL")
    OPENAI_MAX_TOKENS: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    OPENAI_TEMPERATURE: float = Field(default=0.3, env="OPENAI_TEMPERATURE")
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    CLAUDE_API_KEY: Optional[str] = Field(default=None, env="CLAUDE_API_KEY")  # Alias for ANTHROPIC_API_KEY
    ANTHROPIC_DEFAULT_MODEL: str = Field(default="claude-sonnet-4-5-20250929", env="ANTHROPIC_DEFAULT_MODEL")
    ANTHROPIC_MAX_TOKENS: int = Field(default=4000, env="ANTHROPIC_MAX_TOKENS")
    ANTHROPIC_TEMPERATURE: float = Field(default=0.3, env="ANTHROPIC_TEMPERATURE")
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENABLED: bool = Field(default=False, env="AZURE_OPENAI_ENABLED")
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = Field(default=None, env="AZURE_OPENAI_DEPLOYMENT_NAME")
    
    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    SECRET_KEY: str = Field(
        default="your-super-secret-key-minimum-32-characters-long",
        env="SECRET_KEY"
    )

    JWT_SECRET: str = Field(
        default="your-super-secret-jwt-key-minimum-32-characters-long",
        env="JWT_SECRET"
    )
    JWT_EXPIRES_IN: str = Field(default="7d", env="JWT_EXPIRES_IN")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    SESSION_SECRET: str = Field(
        default="your-session-secret-key-minimum-32-characters",
        env="SESSION_SECRET"
    )

    ENCRYPTION_KEY: str = Field(
        default="your-32-character-encryption-key-here",
        env="ENCRYPTION_KEY"
    )
    
    # =============================================================================
    # CORS & SECURITY
    # =============================================================================
    # Store as string to avoid pydantic-settings JSON parsing issues
    # Use cors_origins_list property to get the parsed list
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://127.0.0.1:3000,http://127.0.0.1:3001",
        env="CORS_ORIGINS"
    )

    @computed_field
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into a list"""
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "":
            return ["http://localhost:3000", "http://localhost:3001"]
        # Handle both JSON array format and comma-separated format
        origins = self.CORS_ORIGINS.strip()
        if origins.startswith("["):
            import json
            try:
                return json.loads(origins)
            except json.JSONDecodeError:
                pass
        return [origin.strip() for origin in origins.split(",") if origin.strip()]
    CORS_CREDENTIALS: bool = Field(default=True, env="CORS_CREDENTIALS")
    CORS_METHODS: str = Field(default="*", env="CORS_METHODS")
    CORS_HEADERS: str = Field(default="*", env="CORS_HEADERS")

    @computed_field
    @property
    def cors_methods_list(self) -> List[str]:
        """Parse CORS_METHODS string into a list"""
        if not self.CORS_METHODS or self.CORS_METHODS.strip() == "*":
            return ["*"]
        return [m.strip() for m in self.CORS_METHODS.split(",") if m.strip()]

    @computed_field
    @property
    def cors_headers_list(self) -> List[str]:
        """Parse CORS_HEADERS string into a list"""
        if not self.CORS_HEADERS or self.CORS_HEADERS.strip() == "*":
            return ["*"]
        return [h.strip() for h in self.CORS_HEADERS.split(",") if h.strip()]
    
    # =============================================================================
    # LOGGING SETTINGS
    # =============================================================================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    LOG_FILE_ENABLED: bool = Field(default=True, env="LOG_FILE_ENABLED")
    LOG_FILE_PATH: str = Field(default="./logs/application.log", env="LOG_FILE_PATH")
    
    # =============================================================================
    # FILE STORAGE SETTINGS
    # =============================================================================
    LOCAL_STORAGE_PATH: str = Field(default="./storage", env="LOCAL_STORAGE_PATH")
    DOCUMENT_STORAGE_PATH: str = Field(default="./storage/documents", env="DOCUMENT_STORAGE_PATH")
    MAX_DOCUMENT_SIZE_MB: int = Field(default=100, env="MAX_DOCUMENT_SIZE_MB")
    # Store as string to avoid pydantic-settings JSON parsing issues
    ALLOWED_FILE_TYPES: str = Field(
        default="pdf,docx,doc,txt,rtf",
        env="ALLOWED_FILE_TYPES"
    )

    @computed_field
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Parse ALLOWED_FILE_TYPES string into a list"""
        if not self.ALLOWED_FILE_TYPES:
            return ["pdf", "docx", "doc", "txt", "rtf"]
        return [ftype.strip().lower() for ftype in self.ALLOWED_FILE_TYPES.split(",") if ftype.strip()]
    
    # AWS S3 Configuration
    AWS_S3_ENABLED: bool = Field(default=False, env="AWS_S3_ENABLED")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_S3_BUCKET: Optional[str] = Field(default=None, env="AWS_S3_BUCKET")
    
    # =============================================================================
    # LEGAL API SETTINGS
    # =============================================================================
    # CourtListener
    COURTLISTENER_API_KEY: Optional[str] = Field(default=None, env="COURTLISTENER_API_KEY")
    COURTLISTENER_ENABLED: bool = Field(default=True, env="COURTLISTENER_ENABLED")
    
    # PACER - App-level credentials (SaaS model: users don't need their own PACER account)
    PACER_USERNAME: Optional[str] = Field(default=None, env="PACER_USERNAME")
    PACER_PASSWORD: Optional[str] = Field(default=None, env="PACER_PASSWORD")
    PACER_CLIENT_CODE: Optional[str] = Field(default=None, env="PACER_CLIENT_CODE")
    PACER_ENVIRONMENT: str = Field(default="production", env="PACER_ENVIRONMENT")  # production or qa
    PACER_ENABLED: bool = Field(default=True, env="PACER_ENABLED")  # Enabled by default when credentials are set
    PACER_ENCRYPTION_KEY: Optional[str] = Field(default=None, env="PACER_ENCRYPTION_KEY")
    
    # Westlaw
    WESTLAW_API_KEY: Optional[str] = Field(default=None, env="WESTLAW_API_KEY")
    WESTLAW_ENABLED: bool = Field(default=False, env="WESTLAW_ENABLED")
    
    # LexisNexis
    LEXISNEXIS_API_KEY: Optional[str] = Field(default=None, env="LEXISNEXIS_API_KEY")
    LEXISNEXIS_ENABLED: bool = Field(default=False, env="LEXISNEXIS_ENABLED")
    
    # =============================================================================
    # MONITORING & OBSERVABILITY
    # =============================================================================
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    SENTRY_ENABLED: bool = Field(default=False, env="SENTRY_ENABLED")
    
    PROMETHEUS_ENABLED: bool = Field(default=False, env="PROMETHEUS_ENABLED")
    METRICS_ENDPOINT: str = Field(default="/metrics", env="METRICS_ENDPOINT")
    
    # =============================================================================
    # CELERY/BACKGROUND TASKS
    # =============================================================================
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")
    CELERY_WORKER_CONCURRENCY: int = Field(default=4, env="CELERY_WORKER_CONCURRENCY")
    
    # =============================================================================
    # EMAIL SETTINGS
    # =============================================================================
    SMTP_HOST: str = Field(default="localhost", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=1025, env="SMTP_PORT")  # Default to MailHog for dev
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    SMTP_USE_SSL: bool = Field(default=False, env="SMTP_USE_SSL")
    FROM_EMAIL: str = Field(default="noreply@legalai.com", env="FROM_EMAIL")
    FROM_NAME: str = Field(default="Legal AI System", env="FROM_NAME")
    EMAIL_NOTIFICATIONS_ENABLED: bool = Field(default=False, env="EMAIL_NOTIFICATIONS_ENABLED")
    NOTIFICATION_EMAIL_SUBJECT: str = Field(default="Case Update Notification", env="NOTIFICATION_EMAIL_SUBJECT")
    
    # =============================================================================
    # RATE LIMITING
    # =============================================================================
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    
    # =============================================================================
    # VALIDATORS (Pydantic v2 style)
    # =============================================================================
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        valid_envs = ["development", "staging", "production", "testing"]
        if v.lower() not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {valid_envs}")
        return v.lower()
    
    # =============================================================================
    # CONFIGURATION (Pydantic v2 style)
    # =============================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Allow extra env vars not defined in Settings
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once
    and cached for the lifetime of the application.
    """
    return Settings()


# Create settings instance for module-level access
settings = get_settings()