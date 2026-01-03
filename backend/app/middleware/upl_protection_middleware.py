"""
UPL PROTECTION MIDDLEWARE

This middleware ensures ALL responses are checked for UPL compliance
and automatically sanitizes any content that could constitute legal advice.

CRITICAL: This is the last line of defense against UPL violations.
"""

import json
import logging
from datetime import datetime
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from typing import Dict, Any

from app.core.upl_compliance import emergency_upl_compliance

logger = logging.getLogger(__name__)

class UPLProtectionMiddleware:
    """Middleware that provides fail-safe UPL compliance protection"""
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.compliance_engine = emergency_upl_compliance
        
    async def __call__(self, request: Request, call_next):
        """Main middleware function - processes all responses for UPL compliance"""
        
        # Get the response from the application
        response = await call_next(request)
        
        # Apply UPL protection to the response
        protected_response = await self._apply_upl_protection(response, request)
        
        return protected_response
    
    async def _apply_upl_protection(self, response: Response, request: Request) -> Response:
        """Apply UPL compliance protection to response"""
        
        try:
            # Check if this is a JSON response that needs content analysis
            if self._is_json_response(response):
                return await self._protect_json_response(response, request)
            
            # For HTML responses, add UPL protection headers
            elif self._is_html_response(response):
                return self._protect_html_response(response, request)
            
            # For all other responses, add basic UPL headers
            else:
                return self._add_upl_headers(response, request)
                
        except Exception as e:
            logger.error(f"[UPL_PROTECTION] Error applying UPL protection: {e}")
            
            # In strict mode, block the response if we can't ensure compliance
            if self.strict_mode:
                return self._create_emergency_compliance_response(request, str(e))
            
            # Otherwise, add basic protection and continue
            return self._add_upl_headers(response, request)
    
    def _is_json_response(self, response: Response) -> bool:
        """Check if response is JSON"""
        content_type = response.headers.get('content-type', '')
        return 'application/json' in content_type.lower()
    
    def _is_html_response(self, response: Response) -> bool:
        """Check if response is HTML"""
        content_type = response.headers.get('content-type', '')
        return 'text/html' in content_type.lower()
    
    async def _protect_json_response(self, response: Response, request: Request) -> Response:
        """Protect JSON response content from UPL violations"""
        
        try:
            # Read the response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Parse JSON
            try:
                data = json.loads(body.decode())
            except json.JSONDecodeError:
                logger.warning(f"[UPL_PROTECTION] Could not parse JSON response for {request.url.path}")
                return self._add_upl_headers(response, request)
            
            # Apply UPL compliance to the JSON data
            protected_data = self.compliance_engine.validate_api_response(data)
            
            # Check if any content was sanitized
            compliance_info = protected_data.get('_compliance_info', {})
            violations_found = any(key.endswith('_violations') for key in compliance_info.keys())
            
            if violations_found:
                logger.warning(f"[UPL_PROTECTION] UPL violations found and sanitized in {request.url.path}")
            
            # Create new response with protected data
            protected_response = JSONResponse(
                content=protected_data,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
            # Add UPL protection headers
            return self._add_upl_headers(protected_response, request, violations_found)
            
        except Exception as e:
            logger.error(f"[UPL_PROTECTION] Error protecting JSON response: {e}")
            
            if self.strict_mode:
                return self._create_emergency_compliance_response(request, str(e))
            
            return self._add_upl_headers(response, request)
    
    def _protect_html_response(self, response: Response, request: Request) -> Response:
        """Protect HTML response - mainly adds headers since content is protected by frontend"""
        
        # HTML responses are protected by the DisclaimerWrapper component
        # We just need to add the appropriate headers
        return self._add_upl_headers(response, request)
    
    def _add_upl_headers(self, response: Response, request: Request, violations_found: bool = False) -> Response:
        """Add UPL compliance headers to response"""
        
        # Standard UPL protection headers
        response.headers['X-UPL-Protected'] = 'true'
        response.headers['X-Legal-Disclaimer'] = 'General information only - not legal advice'
        response.headers['X-Attorney-Client'] = 'No attorney-client relationship created'
        response.headers['X-UPL-Compliance-Check'] = datetime.utcnow().isoformat()
        
        if violations_found:
            response.headers['X-UPL-Violations-Sanitized'] = 'true'
            response.headers['X-UPL-Content-Modified'] = 'true'
        
        # Path-specific headers
        path = request.url.path.lower()
        if '/research' in path:
            response.headers['X-UPL-Page-Type'] = 'legal-research'
            response.headers['X-UPL-Warning'] = 'Legal research information only - consult attorney'
        elif '/contract' in path:
            response.headers['X-UPL-Page-Type'] = 'contract-analysis'
            response.headers['X-UPL-Warning'] = 'Contract information only - consult attorney before signing'
        elif '/dashboard' in path:
            response.headers['X-UPL-Page-Type'] = 'case-management' 
            response.headers['X-UPL-Warning'] = 'Case information only - verify with court and attorney'
        elif '/analyze' in path:
            response.headers['X-UPL-Page-Type'] = 'document-analysis'
            response.headers['X-UPL-Warning'] = 'Document analysis only - not legal review'
        
        # Log UPL protection application
        self._log_upl_protection(request, violations_found)
        
        return response
    
    def _create_emergency_compliance_response(self, request: Request, error: str) -> JSONResponse:
        """Create emergency response when UPL compliance cannot be ensured"""
        
        logger.critical(f"[UPL_PROTECTION] EMERGENCY: Cannot ensure UPL compliance for {request.url.path}: {error}")
        
        return JSONResponse(
            status_code=503,
            content={
                'error': 'Service Temporarily Unavailable',
                'message': 'Content cannot be served due to legal compliance requirements',
                'upl_protection': {
                    'status': 'BLOCKED',
                    'reason': 'Unable to verify content compliance with UPL requirements',
                    'error': error,
                    'timestamp': datetime.utcnow().isoformat()
                },
                '_legal_disclaimer': """
🚨 CRITICAL LEGAL NOTICE 🚨
GENERAL INFORMATION ONLY - NOT LEGAL ADVICE

This system cannot serve the requested content without ensuring full compliance
with unauthorized practice of law regulations. 

⚖️ Always consult with a qualified attorney licensed in your jurisdiction.
🚫 No attorney-client relationship is created by this system.
                """,
                '_compliance_info': {
                    'upl_protection_active': True,
                    'content_blocked': True,
                    'compliance_error': True,
                    'legal_consultation_required': True
                }
            },
            headers={
                'X-UPL-Protected': 'true',
                'X-UPL-Status': 'BLOCKED',
                'X-Legal-Disclaimer': 'Content blocked for UPL compliance',
                'X-Attorney-Client': 'No attorney-client relationship created',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Retry-After': '300'  # 5 minutes
            }
        )
    
    def _log_upl_protection(self, request: Request, violations_found: bool):
        """Log UPL protection activity for compliance audit"""
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'upl_protection_applied',
            'request_path': request.url.path,
            'request_method': request.method,
            'violations_found': violations_found,
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'protection_level': 'STRICT' if self.strict_mode else 'STANDARD'
        }
        
        logger.info(f"[UPL_PROTECTION] {json.dumps(log_data)}")

# Create middleware instance with strict mode enabled
upl_protection_middleware = UPLProtectionMiddleware(strict_mode=True)

# FastAPI middleware integration function
async def add_upl_protection_middleware(request: Request, call_next):
    """FastAPI middleware function for UPL protection"""
    return await upl_protection_middleware(request, call_next)

__all__ = [
    'UPLProtectionMiddleware',
    'upl_protection_middleware',
    'add_upl_protection_middleware'
]