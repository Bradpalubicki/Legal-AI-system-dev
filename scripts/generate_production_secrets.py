#!/usr/bin/env python3
"""
Generate Production Secrets for Legal AI System

This script generates cryptographically secure secrets for production deployment.
DO NOT commit the generated .env.production file to version control!

Usage:
    python scripts/generate_production_secrets.py

Output:
    .env.production (in root directory)
"""

import secrets
import os
from pathlib import Path
from cryptography.fernet import Fernet


def generate_jwt_secret(length: int = 64) -> str:
    """Generate a secure JWT secret"""
    return secrets.token_urlsafe(length)


def generate_session_secret(length: int = 32) -> str:
    """Generate a secure session secret"""
    return secrets.token_hex(length)


def generate_encryption_key() -> str:
    """Generate a Fernet-compatible encryption key"""
    return Fernet.generate_key().decode()


def generate_api_key(prefix: str = "legalai") -> str:
    """Generate a secure API key"""
    random_part = secrets.token_urlsafe(40)
    return f"{prefix}_{random_part}"


def main():
    print("="*70)
    print(" LEGAL AI SYSTEM - PRODUCTION SECRETS GENERATOR")
    print("="*70)
    print()
    print("⚠️  WARNING: These secrets are for PRODUCTION use only!")
    print("⚠️  DO NOT commit .env.production to version control!")
    print("⚠️  Store these secrets in a secure secrets manager!")
    print()

    # Generate all secrets
    print("Generating cryptographically secure secrets...")
    print()

    jwt_secret = generate_jwt_secret(64)
    session_secret = generate_session_secret(32)
    encryption_key = generate_encryption_key()
    api_key = generate_api_key()
    database_password = secrets.token_urlsafe(32)
    redis_password = secrets.token_urlsafe(24)

    # Create .env.production file
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env.production'

    env_content = f"""# =============================================================================
# LEGAL AI SYSTEM - PRODUCTION ENVIRONMENT SECRETS
# =============================================================================
# ⚠️  CRITICAL: DO NOT COMMIT THIS FILE TO VERSION CONTROL
# ⚠️  Generated: {os.popen('date').read().strip()}
# =============================================================================

# =============================================================================
# GENERAL APPLICATION SETTINGS
# =============================================================================
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
APP_NAME="Legal AI System"

# =============================================================================
# SECURITY SECRETS - GENERATED CRYPTOGRAPHICALLY
# =============================================================================
# JWT Secret (64 bytes, URL-safe)
JWT_SECRET={jwt_secret}

# Session Secret (32 bytes, hex-encoded)
SESSION_SECRET={session_secret}

# Encryption Key (Fernet-compatible)
ENCRYPTION_KEY={encryption_key}

# Master API Key
MASTER_API_KEY={api_key}

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
# Production database password (CHANGE THIS IN YOUR DEPLOYMENT)
DATABASE_URL=postgresql://legalai_user:{database_password}@postgres:5432/legal_ai_system
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_PASSWORD={database_password}

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================
# Production Redis password
REDIS_URL=redis://:{redis_password}@redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD={redis_password}

# =============================================================================
# CELERY BACKGROUND TASKS
# =============================================================================
CELERY_BROKER_URL=redis://:{redis_password}@redis:6379/2
CELERY_RESULT_BACKEND=redis://:{redis_password}@redis:6379/2

# =============================================================================
# FILE STORAGE (MinIO/S3)
# =============================================================================
# Production MinIO credentials (CHANGE THESE)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=prod-access-key-{secrets.token_hex(8)}
MINIO_SECRET_KEY={secrets.token_urlsafe(32)}

# =============================================================================
# AI MODEL CONFIGURATION
# =============================================================================
# ADD YOUR REAL API KEYS HERE
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================
# ADD YOUR EMAIL CREDENTIALS HERE
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-app-specific-password

# =============================================================================
# AUTHENTICATION & SECURITY
# =============================================================================
# Production CORS (restrict to your domain)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# =============================================================================
# FRONTEND CONFIGURATION
# =============================================================================
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXTAUTH_SECRET={secrets.token_urlsafe(32)}

# =============================================================================
# MONITORING & ALERTS
# =============================================================================
# ADD YOUR MONITORING SERVICE KEYS HERE
SENTRY_DSN=your-sentry-dsn-here
DATADOG_API_KEY=your-datadog-key-here
PAGERDUTY_API_KEY=your-pagerduty-key-here

# =============================================================================
# END OF PRODUCTION SECRETS
# =============================================================================
"""

    # Write to file
    with open(env_file, 'w') as f:
        f.write(env_content)

    # Set restrictive file permissions (Unix-like systems)
    try:
        os.chmod(env_file, 0o600)  # Owner read/write only
    except:
        pass  # Windows doesn't support chmod

    # Print summary
    print("✅ Production secrets generated successfully!")
    print()
    print(f"📁 File created: {env_file}")
    print()
    print("🔑 Generated Secrets:")
    print(f"   - JWT Secret: {jwt_secret[:20]}... (64 bytes)")
    print(f"   - Session Secret: {session_secret[:20]}... (32 bytes)")
    print(f"   - Encryption Key: {encryption_key[:20]}... (Fernet)")
    print(f"   - API Key: {api_key[:30]}...")
    print(f"   - Database Password: {database_password[:20]}...")
    print(f"   - Redis Password: {redis_password[:20]}...")
    print()
    print("📋 Next Steps:")
    print("   1. Review .env.production and add your API keys")
    print("   2. Update CORS_ORIGINS with your production domain")
    print("   3. Add monitoring service keys (Sentry, Datadog, etc.)")
    print("   4. Store secrets in your secrets manager (AWS Secrets Manager, etc.)")
    print("   5. DO NOT commit .env.production to version control!")
    print()
    print("🚀 To use in production:")
    print("   export $(cat .env.production | xargs)")
    print("   # or")
    print("   docker-compose --env-file .env.production up")
    print()
    print("="*70)


if __name__ == "__main__":
    main()
