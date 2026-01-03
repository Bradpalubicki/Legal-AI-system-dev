"""
Health Check Module for Legal AI System

Provides comprehensive health monitoring endpoints for system status,
version information, and service dependencies.
"""

import asyncio
import logging
import platform
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import psutil
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import redis
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_async_session
from ..core.config import get_settings

logger = logging.getLogger(__name__)

# Version information
__version__ = "1.0.0"
__build__ = "2024.01.001"

router = APIRouter(prefix="/health", tags=["health"])


from enum import Enum

class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceCheck(BaseModel):
    """Individual service health check result"""
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional service details")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class SystemInfo(BaseModel):
    """System information"""
    version: str = Field(..., description="Application version")
    build: str = Field(..., description="Build number")
    environment: str = Field(..., description="Environment (dev/staging/prod)")
    python_version: str = Field(..., description="Python version")
    platform: str = Field(..., description="Operating system platform")
    hostname: str = Field(..., description="System hostname")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")


class ResourceUsage(BaseModel):
    """System resource usage"""
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    memory_used_mb: float = Field(..., description="Used memory in MB")
    memory_available_mb: float = Field(..., description="Available memory in MB")
    disk_usage_percent: float = Field(..., description="Disk usage percentage")


class HealthCheckResponse(BaseModel):
    """Complete health check response"""
    status: str = Field(..., description="Overall system status")
    timestamp: str = Field(..., description="Health check timestamp (ISO format)")
    system_info: SystemInfo = Field(..., description="System information")
    resource_usage: ResourceUsage = Field(..., description="Resource usage metrics")
    services: List[ServiceCheck] = Field(..., description="Service health checks")
    dependencies: Dict[str, str] = Field(..., description="Dependency versions")


class HealthChecker:
    """Health check service for monitoring system and dependencies"""
    
    def __init__(self):
        self.settings = get_settings()
        self.start_time = time.time()
        
    async def check_database(self) -> ServiceCheck:
        """Check PostgreSQL database connectivity"""
        start_time = time.time()
        
        try:
            async with get_async_session() as session:
                # Simple query to test connection
                result = await session.execute(text("SELECT 1"))
                await result.fetchone()
                
                # Get database version and stats
                version_result = await session.execute(text("SELECT version()"))
                db_version = await version_result.fetchone()
                
                response_time = (time.time() - start_time) * 1000
                
                return ServiceCheck(
                    name="postgresql",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    details={
                        "version": db_version[0] if db_version else "unknown",
                        "connection_pool": "active"
                    }
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {str(e)}")
            
            return ServiceCheck(
                name="postgresql",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def check_redis(self) -> ServiceCheck:
        """Check Redis connectivity and performance"""
        start_time = time.time()
        
        try:
            # Create Redis connection
            redis_client = redis.from_url(
                self.settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test basic operations
            await asyncio.get_event_loop().run_in_executor(
                None, redis_client.ping
            )
            
            # Get Redis info
            redis_info = await asyncio.get_event_loop().run_in_executor(
                None, redis_client.info
            )
            
            response_time = (time.time() - start_time) * 1000
            
            return ServiceCheck(
                name="redis",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={
                    "version": redis_info.get("redis_version", "unknown"),
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "used_memory_human": redis_info.get("used_memory_human", "unknown"),
                    "uptime_in_days": redis_info.get("uptime_in_days", 0)
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {str(e)}")
            
            return ServiceCheck(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def check_external_apis(self) -> List[ServiceCheck]:
        """Check external API dependencies"""
        checks = []
        
        # Check AI services (mock checks for now)
        ai_services = [
            ("openai", self.settings.OPENAI_API_KEY),
            ("anthropic", self.settings.ANTHROPIC_API_KEY)
        ]
        
        for service_name, api_key in ai_services:
            start_time = time.time()
            
            if api_key and api_key.startswith("sk-"):
                # API key is present and properly formatted
                response_time = (time.time() - start_time) * 1000
                checks.append(ServiceCheck(
                    name=service_name,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    details={"api_key_configured": True}
                ))
            else:
                response_time = (time.time() - start_time) * 1000
                checks.append(ServiceCheck(
                    name=service_name,
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    details={"api_key_configured": False},
                    error="API key not configured"
                ))
        
        return checks
    
    def get_system_info(self) -> SystemInfo:
        """Get system information"""
        return SystemInfo(
            version=__version__,
            build=__build__,
            environment=self.settings.ENVIRONMENT,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            platform=f"{platform.system()} {platform.release()}",
            hostname=platform.node(),
            uptime_seconds=time.time() - self.start_time
        )
    
    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            memory_available_mb=memory.available / 1024 / 1024,
            disk_usage_percent=disk.percent
        )
    
    def get_dependencies(self) -> Dict[str, str]:
        """Get dependency versions"""
        dependencies = {}
        
        try:
            import fastapi
            dependencies["fastapi"] = fastapi.__version__
        except ImportError:
            dependencies["fastapi"] = "unknown"
        
        try:
            import sqlalchemy
            dependencies["sqlalchemy"] = sqlalchemy.__version__
        except ImportError:
            dependencies["sqlalchemy"] = "unknown"
        
        try:
            import redis
            dependencies["redis"] = redis.__version__
        except ImportError:
            dependencies["redis"] = "unknown"
        
        try:
            import pydantic
            dependencies["pydantic"] = pydantic.__version__
        except ImportError:
            dependencies["pydantic"] = "unknown"
        
        return dependencies
    
    async def perform_health_check(self) -> HealthCheckResponse:
        """Perform comprehensive health check"""
        logger.info("Performing health check...")
        
        # Collect all service checks
        services = []
        
        # Check database
        db_check = await self.check_database()
        services.append(db_check)
        
        # Check Redis
        redis_check = await self.check_redis()
        services.append(redis_check)
        
        # Check external APIs
        api_checks = await self.check_external_apis()
        services.extend(api_checks)
        
        # Determine overall status
        unhealthy_services = [s for s in services if s.status == HealthStatus.UNHEALTHY]
        degraded_services = [s for s in services if s.status == HealthStatus.DEGRADED]
        
        if unhealthy_services:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_services:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            system_info=self.get_system_info(),
            resource_usage=self.get_resource_usage(),
            services=services,
            dependencies=self.get_dependencies()
        )


# Global health checker instance
health_checker = HealthChecker()


@router.get("/", response_model=HealthCheckResponse, summary="Comprehensive Health Check")
async def health_check():
    """
    Comprehensive health check endpoint that returns:
    - Overall system status
    - Service dependency health
    - System information and metrics
    - Resource usage statistics
    """
    try:
        health_response = await health_checker.perform_health_check()
        
        # Return appropriate HTTP status code based on health
        if health_response.status == HealthStatus.UNHEALTHY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_response.dict()
            )
        
        return health_response
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": HealthStatus.UNHEALTHY,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        )


@router.get("/ping", summary="Simple Ping Check")
async def ping():
    """
    Simple ping endpoint for basic health monitoring.
    Returns minimal response for load balancers and monitoring tools.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": __version__
    }


@router.get("/ready", summary="Readiness Check")
async def readiness_check():
    """
    Kubernetes-style readiness check.
    Returns 200 if the service is ready to accept traffic.
    """
    try:
        # Check critical dependencies only
        db_check = await health_checker.check_database()
        redis_check = await health_checker.check_redis()
        
        if db_check.status == HealthStatus.UNHEALTHY or redis_check.status == HealthStatus.UNHEALTHY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "ready": False,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "services": [db_check.dict(), redis_check.dict()]
                }
            )
        
        return {
            "ready": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": __version__
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ready": False,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        )


@router.get("/liveness", summary="Liveness Check")
async def liveness_check():
    """
    Kubernetes-style liveness check.
    Returns 200 if the service is alive (basic functionality works).
    """
    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "uptime_seconds": time.time() - health_checker.start_time
    }


@router.get("/version", summary="Version Information")
async def version_info():
    """
    Returns detailed version and build information.
    """
    return {
        "version": __version__,
        "build": __build__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system_info": health_checker.get_system_info().dict(),
        "dependencies": health_checker.get_dependencies()
    }


@router.get("/metrics", summary="System Metrics")
async def system_metrics():
    """
    Returns system resource usage metrics.
    Useful for monitoring and alerting.
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "resource_usage": health_checker.get_resource_usage().dict(),
        "uptime_seconds": time.time() - health_checker.start_time
    }