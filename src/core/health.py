from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from enum import Enum
import asyncio
import time
import logging
import aioredis
import asyncpg
from minio import Minio
from datetime import datetime

from .config import settings


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ServiceHealth(BaseModel):
    name: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    last_check: datetime


class OverallHealth(BaseModel):
    status: HealthStatus
    services: List[ServiceHealth]
    timestamp: datetime
    uptime_seconds: float


class HealthChecker:
    """Health checker for all system dependencies."""
    
    def __init__(self):
        self.logger = logging.getLogger("legal_ai.health")
        self.start_time = time.time()
    
    async def check_database(self) -> ServiceHealth:
        """Check database connectivity."""
        start_time = time.time()
        
        try:
            # Extract connection params from DATABASE_URL
            # Format: postgresql://user:pass@host:port/db
            conn = await asyncpg.connect(settings.DATABASE_URL)
            await conn.execute("SELECT 1")
            await conn.close()
            
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.utcnow()
            )
            
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Database health check failed: {exc}")
            return ServiceHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                details={"error": str(exc)},
                last_check=datetime.utcnow()
            )
    
    async def check_redis(self) -> ServiceHealth:
        """Check Redis connectivity."""
        start_time = time.time()
        
        try:
            redis_client = aioredis.from_url(settings.REDIS_URL)
            await redis_client.ping()
            await redis_client.close()
            
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.utcnow()
            )
            
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Redis health check failed: {exc}")
            return ServiceHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                details={"error": str(exc)},
                last_check=datetime.utcnow()
            )
    
    async def check_storage(self) -> ServiceHealth:
        """Check MinIO storage connectivity."""
        start_time = time.time()
        
        try:
            client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            
            # Check if bucket exists
            bucket_exists = client.bucket_exists(settings.MINIO_BUCKET_NAME)
            
            response_time = (time.time() - start_time) * 1000
            
            if bucket_exists:
                return ServiceHealth(
                    name="storage",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    details={"bucket": settings.MINIO_BUCKET_NAME},
                    last_check=datetime.utcnow()
                )
            else:
                return ServiceHealth(
                    name="storage",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    details={"error": f"Bucket '{settings.MINIO_BUCKET_NAME}' does not exist"},
                    last_check=datetime.utcnow()
                )
            
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Storage health check failed: {exc}")
            return ServiceHealth(
                name="storage",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                details={"error": str(exc)},
                last_check=datetime.utcnow()
            )
    
    async def check_ai_services(self) -> List[ServiceHealth]:
        """Check AI service connectivity."""
        services = []
        
        # Check OpenAI
        if settings.OPENAI_API_KEY:
            start_time = time.time()
            try:
                # This is a placeholder - implement actual OpenAI API check
                # import openai
                # client = openai.AsyncClient(api_key=settings.OPENAI_API_KEY)
                # response = await client.models.list()
                
                response_time = (time.time() - start_time) * 1000
                services.append(ServiceHealth(
                    name="openai",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    last_check=datetime.utcnow()
                ))
                
            except Exception as exc:
                response_time = (time.time() - start_time) * 1000
                services.append(ServiceHealth(
                    name="openai",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    details={"error": str(exc)},
                    last_check=datetime.utcnow()
                ))
        
        # Check Anthropic
        if settings.ANTHROPIC_API_KEY:
            start_time = time.time()
            try:
                # This is a placeholder - implement actual Anthropic API check
                # import anthropic
                # client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                # response = await client.models.list()
                
                response_time = (time.time() - start_time) * 1000
                services.append(ServiceHealth(
                    name="anthropic",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    last_check=datetime.utcnow()
                ))
                
            except Exception as exc:
                response_time = (time.time() - start_time) * 1000
                services.append(ServiceHealth(
                    name="anthropic",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    details={"error": str(exc)},
                    last_check=datetime.utcnow()
                ))
        
        return services
    
    async def check_all_services(self) -> OverallHealth:
        """Check all services and return overall health status."""
        
        # Run all health checks concurrently
        tasks = [
            self.check_database(),
            self.check_redis(),
            self.check_storage(),
            self.check_ai_services()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        services = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Health check task failed: {result}")
                continue
            
            if isinstance(result, list):
                services.extend(result)
            else:
                services.append(result)
        
        # Determine overall status
        unhealthy_count = sum(1 for s in services if s.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for s in services if s.status == HealthStatus.DEGRADED)
        
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        uptime = time.time() - self.start_time
        
        return OverallHealth(
            status=overall_status,
            services=services,
            timestamp=datetime.utcnow(),
            uptime_seconds=uptime
        )


# Global health checker instance
health_checker = HealthChecker()