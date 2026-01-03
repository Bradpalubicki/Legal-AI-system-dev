"""
Environment Variable Validation

Validates that all required environment variables are set correctly
before the application starts. Prevents runtime failures due to
missing configuration.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EnvVar:
    """Environment variable definition"""
    name: str
    required: bool = True
    environments: Optional[List[str]] = None  # None = all environments
    description: str = ""
    validator: Optional[callable] = None


class EnvironmentValidator:
    """Validates environment configuration on startup"""

    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> bool:
        """
        Validate all required environment variables.
        Returns True if valid, False otherwise.
        """
        print("\n" + "=" * 70)
        print("ENVIRONMENT VALIDATION")
        print("=" * 70)
        print(f"Environment: {self.environment}")
        print("-" * 70)

        # Define required variables for different environments
        env_vars = self._get_env_var_definitions()

        # Validate each variable
        for env_var in env_vars:
            self._validate_env_var(env_var)

        # Print results
        self._print_results()

        # Return success status
        return len(self.errors) == 0

    def _get_env_var_definitions(self) -> List[EnvVar]:
        """Define all environment variables with their requirements"""
        return [
            # Core application settings
            EnvVar(
                name="ENVIRONMENT",
                required=False,  # Made optional - defaults to 'development'
                description="Application environment (development/staging/production)",
                validator=lambda x: x in ["development", "staging", "production"]
            ),
            EnvVar(
                name="SECRET_KEY",
                required=True,
                environments=["production", "staging"],
                description="Secret key for encryption and signing",
                validator=lambda x: len(x) >= 32
            ),
            EnvVar(
                name="JWT_SECRET",
                required=True,
                environments=["production", "staging"],
                description="Secret key for JWT token signing",
                validator=lambda x: len(x) >= 32
            ),

            # Database configuration
            EnvVar(
                name="DATABASE_URL",
                required=True,
                environments=["production", "staging"],
                description="PostgreSQL database connection URL"
            ),

            # AI Services
            EnvVar(
                name="OPENAI_API_KEY",
                required=False,
                description="OpenAI API key for GPT models"
            ),
            EnvVar(
                name="ANTHROPIC_API_KEY",
                required=False,
                description="Anthropic API key for Claude models"
            ),

            # CORS Configuration
            EnvVar(
                name="CORS_ORIGINS",
                required=True,
                environments=["production"],
                description="Comma-separated list of allowed CORS origins"
            ),

            # Redis (optional but recommended)
            EnvVar(
                name="REDIS_URL",
                required=False,
                description="Redis connection URL for caching"
            ),

            # Storage
            EnvVar(
                name="MINIO_ENDPOINT",
                required=False,
                description="MinIO/S3 endpoint for file storage"
            ),
        ]

    def _validate_env_var(self, env_var: EnvVar):
        """Validate a single environment variable"""
        # Skip if not applicable to current environment
        if env_var.environments and self.environment not in env_var.environments:
            return

        # Get value
        value = os.getenv(env_var.name)

        # Check if required
        if env_var.required and not value:
            self.errors.append(
                f"[X] {env_var.name}: MISSING (Required)"
                + (f" - {env_var.description}" if env_var.description else "")
            )
            return

        # Skip further validation if not set and not required
        if not value:
            self.warnings.append(
                f"[!] {env_var.name}: Not set (Optional)"
                + (f" - {env_var.description}" if env_var.description else "")
            )
            return

        # Run custom validator if provided
        if env_var.validator:
            try:
                if not env_var.validator(value):
                    self.errors.append(
                        f"[X] {env_var.name}: INVALID VALUE"
                        + (f" - {env_var.description}" if env_var.description else "")
                    )
                    return
            except Exception as e:
                self.errors.append(
                    f"[X] {env_var.name}: VALIDATION ERROR - {str(e)}"
                )
                return

        # Success
        print(f"[OK] {env_var.name}: Configured")

    def _print_results(self):
        """Print validation results"""
        print("-" * 70)

        # Print errors
        if self.errors:
            print("\n[ERRORS]:")
            for error in self.errors:
                print(f"  {error}")

        # Print warnings
        if self.warnings:
            print("\n[WARNINGS]:")
            for warning in self.warnings:
                print(f"  {warning}")

        # Print summary
        print("\n" + "=" * 70)
        if self.errors:
            print("[FAILED] ENVIRONMENT VALIDATION FAILED")
            print(f"   {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
        else:
            print("[PASSED] ENVIRONMENT VALIDATION PASSED")
            if self.warnings:
                print(f"   {len(self.warnings)} warning(s)")
        print("=" * 70 + "\n")

    def validate_production_requirements(self) -> bool:
        """
        Validate production-specific requirements.
        More strict validation for production deployments.
        """
        if self.environment != "production":
            return True

        print("Running production-specific validation checks...")

        # Production-specific checks
        checks = [
            self._check_strong_secrets(),
            self._check_cors_configuration(),
            self._check_database_is_postgresql(),
            self._check_ai_services(),
        ]

        return all(checks)

    def _check_strong_secrets(self) -> bool:
        """Verify secrets are strong enough for production"""
        secret_key = os.getenv("SECRET_KEY")
        jwt_secret = os.getenv("JWT_SECRET_KEY")

        weak_secrets = [
            "your-super-secret-key-change-this-in-production",
            "your-jwt-secret-key-change-this-in-production",
            "secret",
            "changeme",
            "development"
        ]

        if secret_key in weak_secrets:
            self.errors.append("SECRET_KEY is using a default/weak value")
            return False

        if jwt_secret in weak_secrets:
            self.errors.append("JWT_SECRET_KEY is using a default/weak value")
            return False

        return True

    def _check_cors_configuration(self) -> bool:
        """Verify CORS is not allowing all origins in production"""
        cors_origins = os.getenv("CORS_ORIGINS", "")

        if "*" in cors_origins:
            self.errors.append("CORS_ORIGINS contains wildcard (*) in production")
            return False

        if "localhost" in cors_origins.lower():
            self.warnings.append("CORS_ORIGINS contains localhost in production")

        return True

    def _check_database_is_postgresql(self) -> bool:
        """Verify production is using PostgreSQL"""
        db_url = os.getenv("DATABASE_URL", "")

        if "sqlite" in db_url.lower():
            self.errors.append("Production must use PostgreSQL, not SQLite")
            return False

        return True

    def _check_ai_services(self) -> bool:
        """Check that at least one AI service is configured"""
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if not openai_key and not anthropic_key:
            self.errors.append("At least one AI service (OpenAI or Anthropic) must be configured")
            return False

        return True


def validate_environment() -> bool:
    """
    Main validation function.
    Call this on application startup.
    Returns True if validation passes, False otherwise.
    """
    validator = EnvironmentValidator()

    # Run basic validation
    if not validator.validate_all():
        logger.error("Environment validation failed")
        return False

    # Run production-specific validation
    if validator.environment == "production":
        if not validator.validate_production_requirements():
            logger.error("Production validation failed")
            return False

    return True


def validate_environment_or_exit():
    """
    Validate environment and exit if validation fails.
    Use this for critical applications that should not start with invalid config.
    """
    if not validate_environment():
        print("\n[CRITICAL] Environment validation failed. Application cannot start.")
        print("   Please fix the errors above and try again.\n")
        sys.exit(1)
