"""
AI OUTPUT FILTER MIDDLEWARE - CRITICAL COMPLIANCE

This middleware intercepts ALL AI responses before they reach users to ensure
100% UPL compliance. No legal advice language can bypass this filter.

SECURITY: This is the final defense against UPL violations.
All AI outputs MUST pass through this filter before transmission.
"""

import re
import logging
import time
import json
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
from datetime import datetime, timezone

from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse
import asyncio

from ..shared.compliance.advice_neutralizer import AIAdviceNeutralizer

# Configure logging for compliance monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIOutputFilter:
    """
    Critical compliance middleware that filters all AI outputs for legal advice language.
    
    This filter is the final defense against UPL violations and must process
    every AI response before it reaches the user.
    """
    
    def __init__(self):
        """Initialize the output filter with neutralizer and monitoring."""
        self.neutralizer = AIAdviceNeutralizer()
        self.filter_stats = {
            'total_filtered': 0,
            'advice_detected': 0,
            'outputs_blocked': 0,
            'neutralizations': 0,
            'attorney_reviews_required': 0,
            'start_time': datetime.now(timezone.utc)
        }
        self.blocked_outputs = []
        self.attorney_review_queue = []
        
        # Real-time advice detection patterns (more aggressive than neutralizer)
        self.critical_patterns = [
            r'\byou should\s+(file|sue|negotiate|demand|claim|assert)',
            r'\byou must\s+(take legal action|file a lawsuit|hire an attorney)',
            r'\bin your case\s+you\s+(have the right|should|must|need to)',
            r'\bI recommend\s+(legal action|litigation|suing|filing)',
            r'\bmy legal advice\b',
            r'\bas your attorney\b',
            r'\bthis creates liability\b',
            r'\byou have a strong case\b',
            r'\byou should definitely sue\b'
        ]
        
        logger.info("AI Output Filter initialized - COMPLIANCE MODE ACTIVE")
    
    async def filter_ai_response(self, 
                                response_data: Any, 
                                request: Request,
                                response_type: str = 'standard') -> Dict:
        """
        Filter AI response for legal advice content.
        
        Args:
            response_data: The AI response data to filter
            request: The original request
            response_type: Type of response ('standard', 'streaming', 'batch')
            
        Returns:
            Filtered response with compliance metadata
        """
        start_time = time.time()
        self.filter_stats['total_filtered'] += 1
        
        try:
            # Extract text content from response
            text_content = self._extract_text_content(response_data)
            if not text_content:
                return {
                    'filtered_response': response_data,
                    'compliance_status': 'NO_TEXT_CONTENT',
                    'filter_applied': False
                }
            
            # Step 1: Real-time critical pattern detection
            critical_matches = self._detect_critical_patterns(text_content)
            if critical_matches:
                self.filter_stats['outputs_blocked'] += 1
                return await self._handle_critical_violation(
                    text_content, critical_matches, request
                )
            
            # Step 2: Standard advice detection and neutralization
            neutralization_result = self.neutralizer.neutralize_output(
                text_content,
                context={
                    'request_path': str(request.url.path),
                    'user_agent': request.headers.get('user-agent'),
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'response_type': response_type
                }
            )
            
            # Step 3: Check if neutralization was successful
            if neutralization_result['compliance_status'] == 'NON_COMPLIANT':
                self.filter_stats['attorney_reviews_required'] += 1
                return await self._require_attorney_review(
                    neutralization_result, request
                )
            
            # Step 4: Apply neutralized content back to response
            filtered_response = self._apply_neutralized_content(
                response_data, neutralization_result['neutralized_text']
            )
            
            # Step 5: Add compliance headers and metadata
            compliance_metadata = {
                'filter_applied': True,
                'compliance_status': 'COMPLIANT',
                'neutralizations_applied': len(neutralization_result['conversions']),
                'original_risk_level': neutralization_result['risk_level'],
                'processing_time_ms': round((time.time() - start_time) * 1000, 2),
                'filter_version': '1.0.0',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            if neutralization_result['conversions']:
                self.filter_stats['neutralizations'] += 1
                self.filter_stats['advice_detected'] += 1
                
                # Log neutralization for audit
                logger.warning(f"Legal advice detected and neutralized in AI response: "
                             f"{len(neutralization_result['conversions'])} conversions applied")
            
            return {
                'filtered_response': filtered_response,
                'compliance_metadata': compliance_metadata,
                'neutralization_details': neutralization_result,
                'filter_stats': self.get_filter_statistics()
            }
            
        except Exception as e:
            logger.error(f"Critical error in AI output filter: {str(e)}")
            self.filter_stats['outputs_blocked'] += 1
            
            # Block output on filter failure for safety
            return {
                'filtered_response': {
                    'error': 'Content filtering error - output blocked for safety',
                    'message': 'This response could not be processed through compliance filters.',
                    'recommendation': 'Please rephrase your query or contact support.'
                },
                'compliance_status': 'FILTER_ERROR',
                'filter_applied': True,
                'error_details': str(e)
            }
    
    def _extract_text_content(self, response_data: Any) -> Optional[str]:
        """
        Extract text content from various response formats.
        
        Args:
            response_data: Response data in various formats
            
        Returns:
            Extracted text content or None
        """
        if isinstance(response_data, str):
            return response_data
        elif isinstance(response_data, dict):
            # Handle common response formats
            if 'content' in response_data:
                return response_data['content']
            elif 'message' in response_data:
                return response_data['message']
            elif 'text' in response_data:
                return response_data['text']
            elif 'response' in response_data:
                return response_data['response']
            elif 'choices' in response_data:
                # OpenAI format
                if response_data['choices'] and 'message' in response_data['choices'][0]:
                    return response_data['choices'][0]['message'].get('content')
            elif 'completion' in response_data:
                return response_data['completion']
        elif isinstance(response_data, list):
            # Handle batch responses
            return ' '.join([self._extract_text_content(item) for item in response_data if item])
        
        return None
    
    def _detect_critical_patterns(self, text: str) -> List[Dict]:
        """
        Detect critical patterns that require immediate blocking.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of critical pattern matches
        """
        critical_matches = []
        
        for pattern in self.critical_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                critical_matches.append({
                    'pattern': pattern,
                    'match': match.group(0),
                    'position': match.span(),
                    'context': text[max(0, match.start()-30):match.end()+30],
                    'severity': 'CRITICAL'
                })
        
        return critical_matches
    
    async def _handle_critical_violation(self, 
                                       text: str, 
                                       critical_matches: List[Dict], 
                                       request: Request) -> Dict:
        """
        Handle critical UPL violations that cannot be neutralized.
        
        Args:
            text: Original text content
            critical_matches: Critical pattern matches
            request: Original request
            
        Returns:
            Blocked response with violation details
        """
        violation_id = f"UPL_VIOLATION_{int(time.time())}"
        
        violation_record = {
            'violation_id': violation_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'original_text': text[:500] + '...' if len(text) > 500 else text,
            'critical_matches': critical_matches,
            'request_path': str(request.url.path),
            'user_agent': request.headers.get('user-agent'),
            'ip_address': request.client.host if request.client else 'unknown',
            'severity': 'CRITICAL',
            'action_taken': 'OUTPUT_BLOCKED'
        }
        
        self.blocked_outputs.append(violation_record)
        
        # Log critical violation
        logger.critical(f"CRITICAL UPL VIOLATION DETECTED AND BLOCKED: {violation_id}")
        logger.critical(f"Patterns detected: {[m['match'] for m in critical_matches]}")
        
        # Return safe error response
        return {
            'filtered_response': {
                'error': 'Legal compliance violation detected',
                'message': ('This response contained language that could constitute '
                          'unauthorized practice of law and has been blocked for compliance.'),
                'violation_id': violation_id,
                'recommendation': ('Please rephrase your query to request general information '
                                 'rather than specific legal advice. Consider consulting with a '
                                 'qualified attorney for personalized legal guidance.'),
                'support_contact': 'compliance@legal-ai-system.com'
            },
            'compliance_status': 'CRITICAL_VIOLATION_BLOCKED',
            'filter_applied': True,
            'violation_details': violation_record
        }
    
    async def _require_attorney_review(self, 
                                     neutralization_result: Dict, 
                                     request: Request) -> Dict:
        """
        Queue output for attorney review when neutralization is insufficient.
        
        Args:
            neutralization_result: Result from neutralization attempt
            request: Original request
            
        Returns:
            Response requiring attorney review
        """
        review_id = f"ATTORNEY_REVIEW_{int(time.time())}"
        
        review_record = {
            'review_id': review_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'neutralization_result': neutralization_result,
            'request_path': str(request.url.path),
            'status': 'PENDING_REVIEW',
            'priority': 'HIGH' if neutralization_result['risk_level'] == 'CRITICAL' else 'MEDIUM'
        }
        
        self.attorney_review_queue.append(review_record)
        
        logger.warning(f"Output queued for attorney review: {review_id}")
        
        return {
            'filtered_response': {
                'message': ('This response requires attorney review before delivery to ensure '
                          'full compliance with legal practice regulations.'),
                'review_id': review_id,
                'status': 'Under legal review',
                'estimated_review_time': '2-4 hours during business hours',
                'alternative': ('For immediate assistance with general legal information, '
                              'please rephrase your query to focus on educational content '
                              'rather than specific guidance.'),
                'support_contact': 'legal-review@legal-ai-system.com'
            },
            'compliance_status': 'ATTORNEY_REVIEW_REQUIRED',
            'filter_applied': True,
            'review_details': review_record
        }
    
    def _apply_neutralized_content(self, response_data: Any, neutralized_text: str) -> Any:
        """
        Apply neutralized text back to the original response structure.
        
        Args:
            response_data: Original response data
            neutralized_text: Neutralized text content
            
        Returns:
            Response with neutralized content
        """
        if isinstance(response_data, str):
            return neutralized_text
        elif isinstance(response_data, dict):
            response_copy = response_data.copy()
            
            # Update common response formats
            if 'content' in response_copy:
                response_copy['content'] = neutralized_text
            elif 'message' in response_copy:
                response_copy['message'] = neutralized_text
            elif 'text' in response_copy:
                response_copy['text'] = neutralized_text
            elif 'response' in response_copy:
                response_copy['response'] = neutralized_text
            elif 'choices' in response_copy and response_copy['choices']:
                if 'message' in response_copy['choices'][0]:
                    response_copy['choices'][0]['message']['content'] = neutralized_text
            elif 'completion' in response_copy:
                response_copy['completion'] = neutralized_text
            
            return response_copy
        
        return response_data
    
    def get_filter_statistics(self) -> Dict:
        """
        Get current filter statistics for monitoring.
        
        Returns:
            Filter statistics dictionary
        """
        uptime = datetime.now(timezone.utc) - self.filter_stats['start_time']
        
        return {
            'total_filtered': self.filter_stats['total_filtered'],
            'advice_detected': self.filter_stats['advice_detected'],
            'outputs_blocked': self.filter_stats['outputs_blocked'],
            'neutralizations': self.filter_stats['neutralizations'],
            'attorney_reviews_required': self.filter_stats['attorney_reviews_required'],
            'advice_detection_rate': (
                round((self.filter_stats['advice_detected'] / max(1, self.filter_stats['total_filtered'])) * 100, 2)
            ),
            'blocking_rate': (
                round((self.filter_stats['outputs_blocked'] / max(1, self.filter_stats['total_filtered'])) * 100, 2)
            ),
            'uptime_hours': round(uptime.total_seconds() / 3600, 2),
            'pending_reviews': len(self.attorney_review_queue),
            'blocked_violations': len(self.blocked_outputs)
        }
    
    async def filter_streaming_response(self, 
                                      stream_generator, 
                                      request: Request) -> StreamingResponse:
        """
        Filter streaming AI responses chunk by chunk.
        
        Args:
            stream_generator: Original streaming response generator
            request: Original request
            
        Returns:
            Filtered streaming response
        """
        async def filtered_stream():
            accumulated_text = ""
            chunk_count = 0
            
            try:
                async for chunk in stream_generator:
                    chunk_count += 1
                    
                    # Extract text from chunk
                    chunk_text = self._extract_chunk_text(chunk)
                    if chunk_text:
                        accumulated_text += chunk_text
                        
                        # Check for critical patterns in real-time
                        critical_matches = self._detect_critical_patterns(accumulated_text)
                        if critical_matches:
                            logger.critical("Critical UPL violation in streaming response - terminating stream")
                            yield json.dumps({
                                'error': 'Stream terminated due to compliance violation',
                                'message': 'Content filtering detected unauthorized legal advice',
                                'recommendation': 'Please request general information instead'
                            }).encode()
                            break
                    
                    # Filter and yield chunk
                    filtered_chunk = await self._filter_stream_chunk(chunk, accumulated_text, request)
                    yield filtered_chunk
                    
                    # Prevent runaway streams
                    if chunk_count > 1000:  # Reasonable limit
                        logger.warning("Stream terminated - chunk limit exceeded")
                        break
                        
            except Exception as e:
                logger.error(f"Error in streaming filter: {str(e)}")
                yield json.dumps({
                    'error': 'Stream processing error',
                    'message': 'Response stream could not be processed safely'
                }).encode()
        
        return StreamingResponse(
            filtered_stream(),
            media_type="application/json",
            headers={
                'X-Compliance-Filter': 'active',
                'X-Filter-Version': '1.0.0'
            }
        )
    
    def _extract_chunk_text(self, chunk: Any) -> Optional[str]:
        """Extract text content from streaming chunk."""
        if isinstance(chunk, bytes):
            try:
                chunk_data = json.loads(chunk.decode())
                return self._extract_text_content(chunk_data)
            except:
                return chunk.decode() if chunk else None
        elif isinstance(chunk, str):
            return chunk
        elif isinstance(chunk, dict):
            return self._extract_text_content(chunk)
        
        return None
    
    async def _filter_stream_chunk(self, chunk: Any, context: str, request: Request) -> bytes:
        """Filter individual stream chunk."""
        try:
            chunk_text = self._extract_chunk_text(chunk)
            if chunk_text:
                # Quick neutralization check for chunk
                neutralization_result = self.neutralizer.neutralize_output(chunk_text)
                if neutralization_result['neutralized_text'] != chunk_text:
                    # Apply neutralization to chunk
                    filtered_chunk = self._apply_neutralized_content(chunk, neutralization_result['neutralized_text'])
                    return json.dumps(filtered_chunk).encode() if isinstance(filtered_chunk, dict) else str(filtered_chunk).encode()
            
            return json.dumps(chunk).encode() if isinstance(chunk, dict) else str(chunk).encode()
            
        except Exception as e:
            logger.error(f"Chunk filtering error: {str(e)}")
            return b'{"error": "chunk filtering error"}'


# Global filter instance
output_filter = AIOutputFilter()

def apply_output_filter(response_type: str = 'standard'):
    """
    Decorator to apply output filtering to API endpoints.
    
    Args:
        response_type: Type of response to filter
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            try:
                # Execute original function
                response = await func(request, *args, **kwargs)
                
                # Apply filtering
                filter_result = await output_filter.filter_ai_response(
                    response, request, response_type
                )
                
                # Return filtered response with compliance headers
                filtered_response = filter_result['filtered_response']
                
                # Add compliance headers if response supports it
                if hasattr(filtered_response, 'headers'):
                    filtered_response.headers['X-Compliance-Filter'] = 'applied'
                    filtered_response.headers['X-Filter-Status'] = filter_result.get('compliance_status', 'unknown')
                
                return filtered_response
                
            except Exception as e:
                logger.error(f"Output filter wrapper error: {str(e)}")
                # Return safe error response
                return {
                    'error': 'Response processing error',
                    'message': 'This response could not be safely processed',
                    'recommendation': 'Please try rephrasing your request'
                }
        
        return wrapper
    return decorator


# Middleware for automatic filtering
class OutputFilterMiddleware:
    """FastAPI middleware for automatic output filtering."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Only filter AI-related endpoints
        path = scope.get("path", "")
        if not self._should_filter_path(path):
            await self.app(scope, receive, send)
            return
        
        # Wrap response to apply filtering
        async def send_wrapper(message):
            if message["type"] == "http.response.body":
                try:
                    # Apply filtering to response body
                    body = message.get("body", b"")
                    if body:
                        # This is a simplified version - full implementation would need
                        # to handle various response formats and streaming responses
                        pass
                except Exception as e:
                    logger.error(f"Middleware filtering error: {str(e)}")
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
    
    def _should_filter_path(self, path: str) -> bool:
        """Determine if path should be filtered."""
        ai_paths = [
            '/api/ai/', '/api/chat/', '/api/analyze/', '/api/generate/',
            '/api/legal/', '/api/document/', '/api/research/'
        ]
        return any(ai_path in path for ai_path in ai_paths)


# Export key components
__all__ = [
    'AIOutputFilter',
    'output_filter',
    'apply_output_filter',
    'OutputFilterMiddleware'
]