"""
Comprehensive Health Check Endpoints

Provides detailed health status for monitoring systems, load balancers,
and orchestration platforms (Docker, Kubernetes).
"""

import os
import time
from typing import Dict, Any
from fastapi import APIRouter, status, Response
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check_basic():
    """
    Basic health check - returns 200 if service is running.
    Used for simple liveness probes.
    """
    return {
        "status": "healthy",
        "service": "legal-ai-backend"
    }


@router.get("/system", status_code=status.HTTP_200_OK)
async def health_check_system(response: Response):
    """
    Comprehensive system health check.
    Tests all critical dependencies and returns detailed status.

    Used for readiness probes and detailed monitoring.
    Returns 503 if any critical service is unavailable.
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "legal-ai-backend",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "checks": {}
    }

    all_healthy = True

    # Check 1: Database connectivity
    db_healthy, db_details = await check_database()
    health_status["checks"]["database"] = db_details
    if not db_healthy:
        all_healthy = False

    # Check 2: Redis connectivity (if configured)
    redis_healthy, redis_details = await check_redis()
    health_status["checks"]["redis"] = redis_details
    if not redis_healthy:
        # Redis is not critical for basic operation
        logger.warning("Redis check failed but not marking as unhealthy")

    # Check 3: MinIO/S3 storage (if configured)
    storage_healthy, storage_details = await check_storage()
    health_status["checks"]["storage"] = storage_details
    if not storage_healthy:
        # Storage is not critical for basic operation
        logger.warning("Storage check failed but not marking as unhealthy")

    # Check 4: AI Services availability
    ai_healthy, ai_details = await check_ai_services()
    health_status["checks"]["ai_services"] = ai_details
    # AI services being down shouldn't mark the whole system as unhealthy
    # but we should log it

    # Update overall status
    if not all_healthy:
        health_status["status"] = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif not db_healthy:
        health_status["status"] = "degraded"
        response.status_code = status.HTTP_200_OK

    return health_status


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(response: Response):
    """
    Readiness probe - checks if service can accept traffic.
    Returns 200 if ready, 503 if not ready.
    """
    # Check critical services only
    db_healthy, _ = await check_database()

    if db_healthy:
        return {
            "status": "ready",
            "service": "legal-ai-backend"
        }
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "service": "legal-ai-backend",
            "reason": "Database not available"
        }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    Liveness probe - checks if service is alive.
    Should always return 200 unless the application is completely dead.
    """
    return {
        "status": "alive",
        "service": "legal-ai-backend"
    }


# =============================================================================
# Helper Functions for Service Checks
# =============================================================================

async def check_database() -> tuple[bool, Dict[str, Any]]:
    """Check database connectivity and health"""
    try:
        from app.src.core.database import engine

        # Test database connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()

        return True, {
            "status": "healthy",
            "type": "postgresql" if "postgresql" in str(engine.url) else "sqlite",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False, {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_redis() -> tuple[bool, Dict[str, Any]]:
    """Check Redis connectivity (including FakeRedis for development)"""
    try:
        # Check if we're using fakeredis
        use_fake_redis = os.getenv("USE_FAKE_REDIS", "false").lower() == "true"

        if use_fake_redis:
            # Use our redis cache service which handles fakeredis
            try:
                from app.src.core.cache.redis_cache import cache

                if cache.is_available():
                    # Test basic operations
                    test_key = "_health_check_test"
                    cache.set(test_key, "test", ttl=10)
                    result = cache.get(test_key)
                    cache.delete(test_key)

                    return True, {
                        "status": "healthy",
                        "type": "fakeredis",
                        "message": "FakeRedis (in-memory) connection successful"
                    }
                else:
                    return False, {
                        "status": "unhealthy",
                        "message": "FakeRedis not available"
                    }
            except Exception as e:
                logger.error(f"FakeRedis health check failed: {e}")
                return False, {
                    "status": "unhealthy",
                    "error": str(e)
                }

        # Standard Redis check
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return True, {
                "status": "not_configured",
                "message": "Redis not configured"
            }

        # Test Redis connection
        import redis
        r = redis.from_url(redis_url, socket_timeout=2)
        r.ping()

        return True, {
            "status": "healthy",
            "type": "redis",
            "message": "Redis connection successful"
        }
    except ImportError:
        return True, {
            "status": "not_configured",
            "message": "Redis client not installed"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False, {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_storage() -> tuple[bool, Dict[str, Any]]:
    """Check MinIO/S3 storage connectivity (including local file storage)"""
    try:
        # Check if we're using local storage
        use_local_storage = os.getenv("USE_LOCAL_STORAGE", "false").lower() == "true"

        if use_local_storage:
            # Check local storage directory
            import pathlib
            storage_path = os.getenv("LOCAL_STORAGE_PATH", "./storage")

            try:
                storage_dir = pathlib.Path(storage_path)

                # Check if directory exists and is writable
                if not storage_dir.exists():
                    storage_dir.mkdir(parents=True, exist_ok=True)

                # Test write permissions
                test_file = storage_dir / ".health_check_test"
                test_file.write_text("test")
                test_file.unlink()

                return True, {
                    "status": "healthy",
                    "type": "local_storage",
                    "path": str(storage_dir.absolute()),
                    "message": "Local file storage configured and writable"
                }
            except Exception as e:
                logger.error(f"Local storage health check failed: {e}")
                return False, {
                    "status": "unhealthy",
                    "type": "local_storage",
                    "error": str(e)
                }

        # Standard MinIO/S3 check
        minio_endpoint = os.getenv("MINIO_ENDPOINT")
        if not minio_endpoint:
            return True, {
                "status": "not_configured",
                "message": "MinIO/S3 not configured"
            }

        # Basic connectivity check could be added here
        # For now, just report as configured
        return True, {
            "status": "configured",
            "type": "minio",
            "message": "Storage configured"
        }
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return False, {
            "status": "unknown",
            "error": str(e)
        }


async def check_ai_services() -> tuple[bool, Dict[str, Any]]:
    """Check AI service API keys are configured"""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    services = {
        "openai": "configured" if openai_key else "not_configured",
        "anthropic": "configured" if anthropic_key else "not_configured"
    }

    all_configured = openai_key or anthropic_key

    return all_configured, {
        "status": "configured" if all_configured else "not_configured",
        "services": services,
        "message": "At least one AI service required"
    }

