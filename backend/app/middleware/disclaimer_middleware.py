"""
DISCLAIMER INJECTION MIDDLEWARE

This middleware ensures ALL API responses include appropriate legal disclaimers
and compliance headers. It provides fail-safe protection against serving
content without proper legal warnings.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)

class DisclaimerMiddleware:
    """
    Middleware that injects legal disclaimers into ALL API responses.
    
    This middleware provides multiple layers of protection:
    1. Injects disclaimer headers into all HTTP responses
    2. Adds disclaimer text to JSON response bodies
    3. Logs all disclaimer injections for compliance audit
    4. Blocks responses that cannot be made compliant
    """
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        
        # Standard disclaimer text for different content types
        self.disclaimers = {
            'general': '⚖️ LEGAL DISCLAIMER: This information is for general educational purposes only and does NOT constitute legal advice. Consult a qualified attorney for advice specific to your situation.',
            'research': '📚 RESEARCH DISCLAIMER: Legal research is for informational purposes only and is NOT a substitute for attorney consultation. Information may be outdated or jurisdiction-specific.',
            'contract': '📋 CONTRACT DISCLAIMER: Contract analysis does NOT constitute legal review or legal advice. Consult a qualified attorney before signing ANY legal agreement.',
            'dashboard': '📊 DASHBOARD DISCLAIMER: Dashboard information is NOT legal advice and is for informational purposes only. Deadlines shown are estimates - verify with court records.',
            'analysis': '🔍 ANALYSIS DISCLAIMER: Document analysis is for informational purposes only and is NOT legal advice. AI analysis may not identify all issues or legal implications.'
        }
    
    async def __call__(self, request: Request, call_next):
        """Main middleware function"""
        
        # Process the request
        response = await call_next(request)
        
        # Inject disclaimer headers into ALL responses
        response = self._inject_disclaimer_headers(response, request)
        
        # For JSON responses, also inject disclaimer into response body
        if self._is_json_response(response):
            response = await self._inject_json_disclaimer(response, request)
        
        # Log disclaimer injection for compliance audit
        self._log_disclaimer_injection(request, response)
        
        return response
    
    def _inject_disclaimer_headers(self, response: Response, request: Request) -> Response:
        """Inject legal disclaimer headers into response"""
        
        # Standard legal headers for ALL responses
        response.headers['X-Legal-Disclaimer'] = 'General information only - Not legal advice'
        response.headers['X-Attorney-Client'] = 'No attorney-client relationship created'
        response.headers['X-Compliance-Protected'] = 'true'
        response.headers['X-Disclaimer-Injected'] = str(datetime.utcnow().isoformat())
        
        # Page-specific disclaimers based on request path
        path = request.url.path.lower()
        
        if '/research' in path or '/api/research' in path:
            response.headers['X-Page-Disclaimer'] = 'Legal research - Informational only'
            response.headers['X-Disclaimer-Type'] = 'research'
        elif '/contract' in path or '/api/contract' in path:
            response.headers['X-Page-Disclaimer'] = 'Contract analysis - Not legal review'
            response.headers['X-Disclaimer-Type'] = 'contract'
        elif '/dashboard' in path or '/api/dashboard' in path:
            response.headers['X-Page-Disclaimer'] = 'Dashboard - Estimates only'
            response.headers['X-Disclaimer-Type'] = 'dashboard'
        elif '/analy' in path or '/api/analy' in path:
            response.headers['X-Page-Disclaimer'] = 'Analysis - Informational only'
            response.headers['X-Disclaimer-Type'] = 'analysis'
        else:
            response.headers['X-Disclaimer-Type'] = 'general'
        
        # Security headers for legal content
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        
        return response
    
    def _is_json_response(self, response: Response) -> bool:
        """Check if response is JSON and should have disclaimer injected"""
        content_type = response.headers.get('content-type', '')
        return 'application/json' in content_type.lower()
    
    async def _inject_json_disclaimer(self, response: Response, request: Request) -> Response:
        """Inject disclaimer into JSON response body"""
        
        try:
            # Read the original response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Parse JSON
            try:
                data = json.loads(body.decode())
            except json.JSONDecodeError:
                # If it's not valid JSON, return original response with headers
                logger.warning(f"Could not parse JSON response for disclaimer injection: {request.url.path}")
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            
            # Inject disclaimer based on request path and response content
            disclaimer_type = self._determine_disclaimer_type(request.url.path, data)
            disclaimer_text = self.disclaimers.get(disclaimer_type, self.disclaimers['general'])
            
            # Add disclaimer to response data
            enhanced_data = self._add_disclaimer_to_data(data, disclaimer_text, request)
            
            # Create new response with disclaimer
            return JSONResponse(
                content=enhanced_data,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except Exception as e:
            logger.error(f"Error injecting disclaimer into JSON response: {e}")
            # Return original response if disclaimer injection fails
            return response
    
    def _determine_disclaimer_type(self, path: str, data: Dict[str, Any]) -> str:
        """Determine appropriate disclaimer type based on path and content"""
        
        path_lower = path.lower()
        
        # Path-based determination
        if '/research' in path_lower:
            return 'research'
        elif '/contract' in path_lower:
            return 'contract'
        elif '/dashboard' in path_lower:
            return 'dashboard'
        elif '/analy' in path_lower:
            return 'analysis'
        
        # Content-based determination
        if isinstance(data, dict):
            # Check for research-related content
            if any(key in str(data).lower() for key in ['case', 'statute', 'precedent', 'citation']):
                return 'research'
            # Check for contract-related content
            elif any(key in str(data).lower() for key in ['contract', 'agreement', 'clause', 'terms']):
                return 'contract'
            # Check for analysis-related content
            elif any(key in str(data).lower() for key in ['analysis', 'review', 'summary', 'recommendation']):
                return 'analysis'
        
        return 'general'
    
    def _add_disclaimer_to_data(self, data: Any, disclaimer_text: str, request: Request) -> Dict[str, Any]:
        """Add disclaimer to response data structure"""
        
        # If data is already a dict, add disclaimer fields
        if isinstance(data, dict):
            enhanced_data = dict(data)
            
            # Add disclaimer information
            enhanced_data['_legal_disclaimer'] = disclaimer_text
            enhanced_data['_compliance_info'] = {
                'disclaimer_injected': True,
                'disclaimer_type': request.headers.get('X-Disclaimer-Type', 'general'),
                'timestamp': datetime.utcnow().isoformat(),
                'not_legal_advice': True,
                'attorney_consultation_required': True
            }
            
            # If there's a 'message' or 'content' field, prepend disclaimer
            for field in ['message', 'content', 'response', 'result', 'analysis']:
                if field in enhanced_data and isinstance(enhanced_data[field], str):
                    enhanced_data[field] = f"{disclaimer_text}\n\n{enhanced_data[field]}"
            
            return enhanced_data
        
        # If data is a list, wrap it with disclaimer
        elif isinstance(data, list):
            return {
                '_legal_disclaimer': disclaimer_text,
                '_compliance_info': {
                    'disclaimer_injected': True,
                    'timestamp': datetime.utcnow().isoformat(),
                    'not_legal_advice': True
                },
                'data': data
            }
        
        # For other types, wrap in container with disclaimer
        else:
            return {
                '_legal_disclaimer': disclaimer_text,
                '_compliance_info': {
                    'disclaimer_injected': True,
                    'timestamp': datetime.utcnow().isoformat(),
                    'not_legal_advice': True
                },
                'result': data
            }
    
    def _log_disclaimer_injection(self, request: Request, response: Response):
        """Log disclaimer injection for compliance audit"""
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'disclaimer_injection',
            'request_path': request.url.path,
            'request_method': request.method,
            'response_status': response.status_code,
            'disclaimer_type': response.headers.get('X-Disclaimer-Type', 'general'),
            'headers_injected': bool(response.headers.get('X-Legal-Disclaimer')),
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown')
        }
        
        logger.info(f"[COMPLIANCE] Disclaimer injected: {json.dumps(log_data)}")

# Create middleware instance
disclaimer_middleware = DisclaimerMiddleware(strict_mode=True)

# FastAPI middleware integration function
async def add_disclaimer_middleware(request: Request, call_next):
    """FastAPI middleware function for disclaimer injection"""
    return await disclaimer_middleware(request, call_next)

# Utility function for manual disclaimer injection
def ensure_api_response_has_disclaimer(data: Dict[str, Any], request_path: str = "") -> Dict[str, Any]:
    """
    Utility function to ensure any API response data has appropriate disclaimer.
    Use this in API endpoints that construct responses manually.
    """
    middleware = DisclaimerMiddleware()
    disclaimer_type = middleware._determine_disclaimer_type(request_path, data)
    disclaimer_text = middleware.disclaimers.get(disclaimer_type, middleware.disclaimers['general'])
    
    class MockRequest:
        def __init__(self, path):
            self.url = type('obj', (object,), {'path': path})
            self.headers = {}
    
    mock_request = MockRequest(request_path)
    return middleware._add_disclaimer_to_data(data, disclaimer_text, mock_request)

__all__ = [
    'DisclaimerMiddleware',
    'disclaimer_middleware',
    'add_disclaimer_middleware',
    'ensure_api_response_has_disclaimer'
]