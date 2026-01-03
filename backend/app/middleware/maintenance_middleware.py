"""
EMERGENCY MAINTENANCE MODE MIDDLEWARE

This middleware blocks ALL API access during critical legal compliance maintenance.
It overrides all other middleware and ensures no API responses are served until
maintenance is complete.
"""

import os
import json
import logging
from datetime import datetime
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class MaintenanceModeMiddleware:
    """Middleware that blocks all API access during maintenance"""
    
    def __init__(self):
        self.maintenance_active = os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true'
        self.maintenance_reason = os.getenv('MAINTENANCE_REASON', 'Critical legal compliance updates')
        self.maintenance_started = datetime.utcnow().isoformat()
        
        # Endpoints that remain accessible during maintenance
        self.allowed_endpoints = [
            '/health',
            '/admin/maintenance',
            '/docs',
            '/openapi.json'
        ]
    
    async def __call__(self, request: Request, call_next):
        """Main middleware function"""
        
        if not self.maintenance_active:
            return await call_next(request)
        
        # Check if this endpoint is allowed during maintenance
        path = request.url.path
        is_allowed = any(path.startswith(allowed) for allowed in self.allowed_endpoints)
        
        if is_allowed:
            return await call_next(request)
        
        # Log blocked access attempt
        self._log_blocked_access(request)
        
        # Return maintenance response
        return self._create_maintenance_response()
    
    def _log_blocked_access(self, request: Request):
        """Log blocked access attempt for compliance audit"""
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'maintenance_access_blocked',
            'request_path': request.url.path,
            'request_method': request.method,
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'maintenance_reason': self.maintenance_reason
        }
        
        logger.warning(f"[MAINTENANCE] API access blocked during maintenance: {json.dumps(log_data)}")
    
    def _create_maintenance_response(self) -> JSONResponse:
        """Create standardized maintenance response"""
        
        return JSONResponse(
            status_code=503,
            content={
                'error': 'Service Unavailable',
                'message': 'System under maintenance - all API access suspended',
                'maintenance': {
                    'active': True,
                    'reason': self.maintenance_reason,
                    'started': self.maintenance_started,
                    'estimated_duration': '2-4 hours',
                    'status': 'Critical legal compliance updates in progress'
                },
                'contact': {
                    'email': 'admin@legalai.com',
                    'emergency': 'For urgent matters only'
                },
                'legal_notice': 'This maintenance is required to ensure full legal compliance. System will not be available until all compliance requirements are verified.',
                'retry_after': 7200,  # 2 hours in seconds
                '_compliance_info': {
                    'maintenance_mode': True,
                    'user_access_suspended': True,
                    'data_integrity_protected': True,
                    'compliance_maintenance': True
                }
            },
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Maintenance-Mode': 'active',
                'X-Maintenance-Reason': self.maintenance_reason,
                'X-Maintenance-Started': self.maintenance_started,
                'Retry-After': '7200'
            }
        )

# Create middleware instance
maintenance_middleware = MaintenanceModeMiddleware()

# FastAPI middleware integration function
async def add_maintenance_middleware(request: Request, call_next):
    """FastAPI middleware function for maintenance mode"""
    return await maintenance_middleware(request, call_next)

__all__ = [
    'MaintenanceModeMiddleware',
    'maintenance_middleware', 
    'add_maintenance_middleware'
]