#!/usr/bin/env python3
"""
PRODUCTION API MIDDLEWARE

FastAPI middleware for production deployment:
- Rate limiting integration
- Security headers
- Request/response logging
- Error handling and circuit breakers
- CORS and authentication integration
"""

import time
import logging
from typing import Callable, Dict, Any
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import asyncio
from datetime import datetime

# Import security system
try:
    from backend.app.core.production_security import production_security
    from backend.app.core.performance_optimizer import performance_optimizer
except ImportError:
    production_security = None
    performance_optimizer = None

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Production security middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Extract request information
        client_ip = request.client.host if request.client else 'unknown'
        endpoint = str(request.url.path)
        method = request.method
        
        # Get request body for validation (if applicable)
        request_data = {
            'client_ip': client_ip,
            'endpoint': endpoint,
            'method': method
        }
        
        # Read body for POST/PUT requests
        if method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body:
                    request_data['input_data'] = body.decode('utf-8')[:1000]  # First 1000 chars for validation
            except Exception as e:
                logger.error(f"Failed to read request body: {e}")
        
        # Security validation
        if production_security:
            allowed, security_result = production_security.security_middleware(request_data)
            
            if not allowed:
                logger.warning(f"[SECURITY] Request blocked from {client_ip} to {endpoint}: {security_result}")
                
                # Add security headers even to blocked requests
                response = JSONResponse(
                    status_code=429 if 'rate limit' in security_result.get('error', '').lower() else 403,
                    content=security_result
                )
                
                # Add security headers
                for header, value in production_security.get_security_headers().items():
                    response.headers[header] = value
                
                return response
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add security headers to successful responses
            if production_security:
                for header, value in production_security.get_security_headers().items():
                    response.headers[header] = value
            
            # Add rate limiting headers
            if production_security and 'rate_info' in (security_result if 'security_result' in locals() else {}):
                rate_info = security_result['rate_info']
                response.headers['X-RateLimit-Remaining'] = str(rate_info.get('requests_remaining', 0))
                response.headers['X-RateLimit-Reset'] = str(rate_info.get('reset_time', 0))
            
            # Log successful request
            response_time = (time.time() - start_time) * 1000
            logger.info(f"[API] {method} {endpoint} - {response.status_code} - {response_time:.2f}ms - {client_ip}")
            
            return response
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"[API ERROR] {method} {endpoint} - {str(e)} - {response_time:.2f}ms - {client_ip}")
            
            # Return secure error response
            return JSONResponse(
                status_code=500,
                content={'error': 'Internal server error', 'request_id': f"{int(time.time())}-{client_ip}"},
                headers=production_security.get_security_headers() if production_security else {}
            )

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Performance monitoring middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        endpoint = str(request.url.path)
        method = request.method
        
        try:
            response = await call_next(request)
            
            # Record performance metrics
            response_time = time.time() - start_time
            
            if performance_optimizer:
                performance_optimizer.metrics_collector.record_metric(
                    'api_endpoints',
                    response_time,
                    throughput=1,
                    accuracy=100 if response.status_code < 400 else 0
                )
            
            # Add performance headers
            response.headers['X-Response-Time'] = f"{response_time * 1000:.2f}ms"
            response.headers['X-Timestamp'] = datetime.utcnow().isoformat()
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            
            if performance_optimizer:
                performance_optimizer.metrics_collector.record_metric(
                    'api_endpoints',
                    response_time,
                    error_count=1
                )
            
            raise

class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Circuit breaker for external dependencies"""
    
    def __init__(self, app, failure_threshold: int = 5, recovery_timeout: int = 60):
        super().__init__(app)
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_counts = {}
        self.last_failure_times = {}
        self.circuit_states = {}  # 'closed', 'open', 'half-open'
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        endpoint = str(request.url.path)
        
        # Check circuit breaker state
        if self._is_circuit_open(endpoint):
            logger.warning(f"[CIRCUIT_BREAKER] Circuit open for {endpoint}")
            return JSONResponse(
                status_code=503,
                content={'error': 'Service temporarily unavailable', 'circuit': 'open'}
            )
        
        try:
            response = await call_next(request)
            
            # Reset failure count on success
            if response.status_code < 400:
                self.failure_counts[endpoint] = 0
                self.circuit_states[endpoint] = 'closed'
            else:
                self._record_failure(endpoint)
            
            return response
            
        except Exception as e:
            self._record_failure(endpoint)
            raise
    
    def _is_circuit_open(self, endpoint: str) -> bool:
        """Check if circuit breaker is open for endpoint"""
        current_time = time.time()
        
        # Check if circuit is open
        if self.circuit_states.get(endpoint) == 'open':
            # Check if recovery timeout has passed
            last_failure = self.last_failure_times.get(endpoint, 0)
            if current_time - last_failure > self.recovery_timeout:
                self.circuit_states[endpoint] = 'half-open'
                return False
            return True
        
        return False
    
    def _record_failure(self, endpoint: str) -> None:
        """Record failure and update circuit state"""
        self.failure_counts[endpoint] = self.failure_counts.get(endpoint, 0) + 1
        self.last_failure_times[endpoint] = time.time()
        
        if self.failure_counts[endpoint] >= self.failure_threshold:
            self.circuit_states[endpoint] = 'open'
            logger.error(f"[CIRCUIT_BREAKER] Circuit opened for {endpoint} after {self.failure_counts[endpoint]} failures")

def setup_production_middleware(app: FastAPI) -> None:
    """Setup all production middleware"""
    
    # CORS middleware (before other middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://yourdomain.com"],  # Configure for production
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        max_age=3600,
    )
    
    # Performance monitoring
    app.add_middleware(PerformanceMiddleware)
    
    # Circuit breaker
    app.add_middleware(CircuitBreakerMiddleware)
    
    # Security middleware (last to be first executed)
    app.add_middleware(SecurityMiddleware)
    
    logger.info("[PRODUCTION_MIDDLEWARE] All production middleware configured")

# Custom exception handlers for production
def setup_exception_handlers(app: FastAPI) -> None:
    """Setup production exception handlers"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={'error': exc.detail, 'status_code': exc.status_code},
            headers=production_security.get_security_headers() if production_security else {}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"[UNHANDLED_EXCEPTION] {str(exc)} - {request.url}")
        return JSONResponse(
            status_code=500,
            content={'error': 'Internal server error'},
            headers=production_security.get_security_headers() if production_security else {}
        )
    
    logger.info("[PRODUCTION_MIDDLEWARE] Exception handlers configured")