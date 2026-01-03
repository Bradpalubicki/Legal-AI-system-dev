"""
REAL-TIME COMPLIANCE MONITOR

Critical system for monitoring streaming AI responses in real-time to prevent
any legal advice language from being transmitted to users.

This is the final safeguard against UPL violations in streaming scenarios.
"""

import asyncio
import logging
import re
import json
import time
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable
from datetime import datetime, timezone
import websockets
from dataclasses import dataclass, asdict
from enum import Enum

from ..shared.compliance.advice_neutralizer import AIAdviceNeutralizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ViolationType(Enum):
    """Types of compliance violations."""
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"

@dataclass
class ComplianceAlert:
    """Real-time compliance alert."""
    alert_id: str
    timestamp: str
    violation_type: ViolationType
    pattern_matched: str
    context: str
    action_taken: str
    confidence_score: float
    request_id: Optional[str] = None

class RealTimeComplianceMonitor:
    """
    Real-time monitor for streaming AI responses to detect and prevent
    legal advice language transmission in real-time.
    """
    
    def __init__(self):
        """Initialize the real-time compliance monitor."""
        self.neutralizer = AIAdviceNeutralizer()
        self.active_streams = {}
        self.violation_alerts = []
        self.attorney_alerts = []
        
        # Real-time patterns optimized for streaming detection
        self.streaming_patterns = {
            ViolationType.CRITICAL: [
                r'\byou should file a lawsuit\b',
                r'\byou must take legal action\b',
                r'\bin your case.*you.*entitled to\b',
                r'\bI recommend suing\b',
                r'\bthis gives you grounds to sue\b',
                r'\byou have a strong case against\b',
                r'\bas your attorney.*I advise\b',
                r'\bthis creates liability for\b'
            ],
            ViolationType.SEVERE: [
                r'\byou should.*negotiate.*settlement\b',
                r'\byou must.*include.*clause\b',
                r'\bin your situation.*you should\b',
                r'\bI strongly recommend.*legal action\b',
                r'\byour rights.*violated\b',
                r'\byou need to.*attorney.*immediately\b',
                r'\bthis contract.*binding.*you\b'
            ],
            ViolationType.MODERATE: [
                r'\byou should.*consider\b',
                r'\byour best option.*would be\b',
                r'\bI would recommend\b',
                r'\bin your case.*typically\b',
                r'\byou might want to.*attorney\b',
                r'\bthis could.*affect.*your rights\b'
            ],
            ViolationType.MINOR: [
                r'\byou.*should.*review\b',
                r'\byour.*contract.*might\b',
                r'\bconsider.*consulting\b',
                r'\bthis.*could.*impact\b'
            ]
        }
        
        # Buffer settings for stream monitoring
        self.buffer_size = 1000  # Characters to keep in buffer
        self.check_interval = 0.1  # Seconds between checks
        self.alert_threshold = 0.8  # Confidence threshold for alerts
        
        logger.info("Real-time compliance monitor initialized")
    
    async def monitor_stream(self, 
                           stream_generator: AsyncGenerator[Any, None],
                           stream_id: str,
                           request_context: Dict) -> AsyncGenerator[Any, None]:
        """
        Monitor streaming AI response for compliance violations.
        
        Args:
            stream_generator: The original stream generator
            stream_id: Unique identifier for this stream
            request_context: Context information about the request
            
        Yields:
            Filtered stream chunks or compliance alerts
        """
        buffer = ""
        chunk_count = 0
        violations_detected = 0
        
        # Register active stream
        self.active_streams[stream_id] = {
            'start_time': datetime.now(timezone.utc),
            'request_context': request_context,
            'chunk_count': 0,
            'violations': 0,
            'status': 'active'
        }
        
        try:
            async for chunk in stream_generator:
                chunk_count += 1
                self.active_streams[stream_id]['chunk_count'] = chunk_count
                
                # Extract text from chunk
                chunk_text = self._extract_chunk_text(chunk)
                if not chunk_text:
                    yield chunk
                    continue
                
                # Add to buffer
                buffer += chunk_text
                
                # Trim buffer if too large
                if len(buffer) > self.buffer_size:
                    buffer = buffer[-self.buffer_size:]
                
                # Real-time compliance check
                violations = await self._check_compliance_realtime(buffer, stream_id)
                
                if violations:
                    violations_detected += len(violations)
                    self.active_streams[stream_id]['violations'] = violations_detected
                    
                    # Handle violations by severity
                    critical_violation = any(v.violation_type == ViolationType.CRITICAL for v in violations)
                    
                    if critical_violation:
                        # CRITICAL: Terminate stream immediately
                        logger.critical(f"CRITICAL violation in stream {stream_id} - terminating")
                        yield self._create_termination_chunk(violations)
                        break
                    
                    # SEVERE/MODERATE: Filter chunk
                    filtered_chunk = await self._filter_chunk_realtime(chunk, chunk_text, violations)
                    yield filtered_chunk
                    
                    # Send alerts for severe violations
                    severe_violations = [v for v in violations if v.violation_type in [ViolationType.SEVERE, ViolationType.CRITICAL]]
                    if severe_violations:
                        await self._send_attorney_alert(severe_violations, stream_id)
                else:
                    # No violations - yield original chunk
                    yield chunk
                
                # Rate limiting to prevent overwhelming
                await asyncio.sleep(0.001)  # 1ms delay
                
        except Exception as e:
            logger.error(f"Error monitoring stream {stream_id}: {str(e)}")
            yield self._create_error_chunk(str(e))
            
        finally:
            # Clean up stream tracking
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['status'] = 'completed'
                self.active_streams[stream_id]['end_time'] = datetime.now(timezone.utc)
    
    async def _check_compliance_realtime(self, 
                                       text: str, 
                                       stream_id: str) -> List[ComplianceAlert]:
        """
        Check text for compliance violations in real-time.
        
        Args:
            text: Text to check
            stream_id: Stream identifier
            
        Returns:
            List of compliance alerts
        """
        violations = []
        
        # Check patterns by severity (most severe first)
        for violation_type in [ViolationType.CRITICAL, ViolationType.SEVERE, 
                              ViolationType.MODERATE, ViolationType.MINOR]:
            patterns = self.streaming_patterns[violation_type]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Calculate confidence score
                    confidence = self._calculate_confidence(match, text, violation_type)
                    
                    if confidence >= self.alert_threshold:
                        alert = ComplianceAlert(
                            alert_id=f"{stream_id}_{int(time.time() * 1000)}",
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            violation_type=violation_type,
                            pattern_matched=pattern,
                            context=text[max(0, match.start()-50):match.end()+50],
                            action_taken=self._determine_action(violation_type),
                            confidence_score=confidence,
                            request_id=stream_id
                        )
                        violations.append(alert)
                        
                        # Log violation
                        logger.warning(f"Real-time violation detected: {violation_type.value} "
                                     f"in stream {stream_id} - pattern: {pattern}")
        
        return violations
    
    def _calculate_confidence(self, match, text: str, violation_type: ViolationType) -> float:
        """
        Calculate confidence score for a pattern match.
        
        Args:
            match: Regex match object
            text: Full text context
            violation_type: Type of violation
            
        Returns:
            Confidence score between 0 and 1
        """
        base_confidence = {
            ViolationType.CRITICAL: 0.95,
            ViolationType.SEVERE: 0.85,
            ViolationType.MODERATE: 0.75,
            ViolationType.MINOR: 0.65
        }[violation_type]
        
        # Adjust based on context
        context = text[max(0, match.start()-100):match.end()+100].lower()
        
        # Increase confidence for legal context
        legal_context_terms = ['contract', 'lawsuit', 'attorney', 'legal', 'court', 'liability']
        legal_terms_found = sum(1 for term in legal_context_terms if term in context)
        legal_boost = min(0.1, legal_terms_found * 0.02)
        
        # Decrease confidence for educational disclaimers
        educational_terms = ['general information', 'educational purposes', 'not legal advice']
        educational_penalty = sum(0.05 for term in educational_terms if term in context)
        
        final_confidence = base_confidence + legal_boost - educational_penalty
        return max(0.0, min(1.0, final_confidence))
    
    def _determine_action(self, violation_type: ViolationType) -> str:
        """Determine action to take based on violation type."""
        actions = {
            ViolationType.CRITICAL: "TERMINATE_STREAM",
            ViolationType.SEVERE: "FILTER_AND_ALERT",
            ViolationType.MODERATE: "FILTER_CONTENT",
            ViolationType.MINOR: "LOG_WARNING"
        }
        return actions[violation_type]
    
    async def _filter_chunk_realtime(self, 
                                   original_chunk: Any, 
                                   chunk_text: str,
                                   violations: List[ComplianceAlert]) -> Any:
        """
        Filter chunk content in real-time based on detected violations.
        
        Args:
            original_chunk: Original chunk data
            chunk_text: Text extracted from chunk
            violations: Detected violations
            
        Returns:
            Filtered chunk
        """
        # Apply neutralization
        neutralization_result = self.neutralizer.neutralize_output(chunk_text)
        neutralized_text = neutralization_result['neutralized_text']
        
        # For severe violations, add additional safety measures
        severe_violations = [v for v in violations if v.violation_type in [ViolationType.SEVERE, ViolationType.CRITICAL]]
        if severe_violations:
            safety_prefix = "[GENERAL INFORMATION ONLY] "
            safety_suffix = " [Consult qualified attorney for legal advice]"
            neutralized_text = safety_prefix + neutralized_text + safety_suffix
        
        # Apply neutralized text back to chunk
        if isinstance(original_chunk, dict):
            filtered_chunk = original_chunk.copy()
            if 'content' in filtered_chunk:
                filtered_chunk['content'] = neutralized_text
            elif 'text' in filtered_chunk:
                filtered_chunk['text'] = neutralized_text
            elif 'delta' in filtered_chunk and 'content' in filtered_chunk['delta']:
                filtered_chunk['delta']['content'] = neutralized_text
            return filtered_chunk
        elif isinstance(original_chunk, str):
            return neutralized_text
        
        return original_chunk
    
    def _create_termination_chunk(self, violations: List[ComplianceAlert]) -> Dict:
        """Create termination chunk for critical violations."""
        return {
            'type': 'compliance_termination',
            'error': 'Stream terminated due to critical compliance violation',
            'message': 'This response contained language that could constitute unauthorized practice of law.',
            'violation_count': len(violations),
            'recommendation': 'Please request general information instead of specific legal guidance.',
            'support': 'Contact compliance@legal-ai-system.com for assistance',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _create_error_chunk(self, error_message: str) -> Dict:
        """Create error chunk for stream processing errors."""
        return {
            'type': 'compliance_error',
            'error': 'Stream processing error',
            'message': 'Response stream could not be safely processed',
            'details': error_message,
            'recommendation': 'Please try again or contact support',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def _send_attorney_alert(self, 
                                 violations: List[ComplianceAlert], 
                                 stream_id: str):
        """
        Send real-time alert to attorney for severe violations.
        
        Args:
            violations: Severe violations detected
            stream_id: Stream identifier
        """
        alert_data = {
            'alert_type': 'REAL_TIME_UPL_VIOLATION',
            'stream_id': stream_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'violation_count': len(violations),
            'violations': [asdict(v) for v in violations],
            'severity': 'HIGH' if any(v.violation_type == ViolationType.CRITICAL for v in violations) else 'MEDIUM',
            'action_required': True
        }
        
        # Add to attorney alert queue
        self.attorney_alerts.append(alert_data)
        
        # In production, this would send via WebSocket, email, or SMS
        logger.critical(f"ATTORNEY ALERT: Real-time UPL violations detected in stream {stream_id}")
    
    def _extract_chunk_text(self, chunk: Any) -> Optional[str]:
        """Extract text content from various chunk formats."""
        if isinstance(chunk, str):
            return chunk
        elif isinstance(chunk, bytes):
            try:
                return chunk.decode('utf-8')
            except:
                return None
        elif isinstance(chunk, dict):
            # Handle common streaming formats
            if 'content' in chunk:
                return chunk['content']
            elif 'text' in chunk:
                return chunk['text']
            elif 'delta' in chunk:
                delta = chunk['delta']
                if isinstance(delta, dict) and 'content' in delta:
                    return delta['content']
            elif 'choices' in chunk and chunk['choices']:
                choice = chunk['choices'][0]
                if 'delta' in choice and 'content' in choice['delta']:
                    return choice['delta']['content']
        
        return None
    
    def get_monitoring_stats(self) -> Dict:
        """Get real-time monitoring statistics."""
        active_count = len([s for s in self.active_streams.values() if s['status'] == 'active'])
        total_violations = sum(s['violations'] for s in self.active_streams.values())
        
        return {
            'active_streams': active_count,
            'total_streams_monitored': len(self.active_streams),
            'total_violations_detected': total_violations,
            'violation_alerts': len(self.violation_alerts),
            'attorney_alerts': len(self.attorney_alerts),
            'average_chunks_per_stream': (
                sum(s['chunk_count'] for s in self.active_streams.values()) / 
                max(1, len(self.active_streams))
            )
        }
    
    async def create_compliance_websocket(self, websocket, stream_id: str):
        """
        Create WebSocket connection for real-time compliance monitoring.
        
        Args:
            websocket: WebSocket connection
            stream_id: Stream identifier
        """
        try:
            await websocket.accept()
            logger.info(f"Compliance WebSocket connected for stream {stream_id}")
            
            # Send initial status
            await websocket.send_json({
                'type': 'compliance_status',
                'stream_id': stream_id,
                'status': 'monitoring_active',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Monitor for violations in real-time
            while True:
                # Check for new violations for this stream
                stream_violations = [
                    alert for alert in self.violation_alerts
                    if alert.get('request_id') == stream_id
                ]
                
                if stream_violations:
                    await websocket.send_json({
                        'type': 'compliance_alert',
                        'stream_id': stream_id,
                        'violations': stream_violations,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
                
                await asyncio.sleep(1)  # Check every second
                
        except Exception as e:
            logger.error(f"WebSocket compliance monitoring error: {str(e)}")
        finally:
            logger.info(f"Compliance WebSocket disconnected for stream {stream_id}")


# Global monitor instance
compliance_monitor = RealTimeComplianceMonitor()

async def monitor_ai_stream(stream_generator: AsyncGenerator, 
                          stream_id: str, 
                          request_context: Dict) -> AsyncGenerator:
    """
    Convenience function to monitor AI stream for compliance.
    
    Args:
        stream_generator: Original stream generator
        stream_id: Unique stream identifier
        request_context: Request context information
        
    Yields:
        Filtered stream chunks
    """
    async for chunk in compliance_monitor.monitor_stream(
        stream_generator, stream_id, request_context
    ):
        yield chunk

# Export key components
__all__ = [
    'RealTimeComplianceMonitor',
    'ComplianceAlert',
    'ViolationType',
    'compliance_monitor',
    'monitor_ai_stream'
]