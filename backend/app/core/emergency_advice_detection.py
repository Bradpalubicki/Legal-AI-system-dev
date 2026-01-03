#!/usr/bin/env python3
"""
EMERGENCY ADVICE DETECTION SYSTEM
Detects legal advice in all AI outputs and applies mandatory warnings.
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

class AdviceLevel(Enum):
    NONE = "none"
    INFORMATIONAL = "informational"
    GUIDANCE = "guidance"
    ADVICE = "advice"
    LEGAL_ADVICE = "legal_advice"

class EmergencyAdviceDetector:
    """Real-time advice detection for all AI outputs"""
    
    def __init__(self):
        # High-risk legal advice patterns
        self.legal_advice_patterns = [
            r'\\b(you should|you must|you need to|i recommend|i suggest|i advise)\\b.*\\b(file|sue|claim|contract|legal action)\\b',
            r'\\b(this means you|you have the right to|you are entitled to|you can claim)\\b',
            r'\\b(in your case|for your situation|given your circumstances)\\b.*\\b(legal|lawsuit|contract|liability)\\b',
            r'\\b(you should (not )?|you must (not )?|i recommend|my advice is)\\b.*\\b(sign|agree|proceed|file|sue)\\b',
            r'\\b(this is|this constitutes|this means)\\b.*\\b(fraud|negligence|breach|violation|illegal)\\b',
            r'\\b(you have a (strong )?case|you should win|you will likely)\\b',
            r'\\b(file a|submit a|bring a)\\b.*\\b(lawsuit|claim|motion|appeal)\\b',
            r'\\b(liable|responsible|at fault|negligent)\\b.*\\b(for|in|regarding)\\b'
        ]
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def analyze_output(self, text: str) -> Dict[str, Any]:
        """Analyze AI output for legal advice content"""
        
        if not text:
            return {
                'advice_level': AdviceLevel.NONE.value,
                'requires_disclaimer': False,
                'risk_score': 0.0,
                'detected_patterns': 0
            }
        
        text_lower = text.lower()
        
        # Check for legal advice patterns
        detected_count = 0
        for pattern in self.legal_advice_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                detected_count += 1
        
        # Determine advice level and risk score
        if detected_count >= 3:
            advice_level = AdviceLevel.LEGAL_ADVICE
            risk_score = min(0.9 + (detected_count * 0.05), 1.0)
        elif detected_count >= 1:
            advice_level = AdviceLevel.GUIDANCE
            risk_score = min(0.6 + (detected_count * 0.1), 0.8)
        else:
            advice_level = AdviceLevel.INFORMATIONAL
            risk_score = 0.3
        
        requires_disclaimer = risk_score >= 0.5
        
        result = {
            'advice_level': advice_level.value,
            'requires_disclaimer': requires_disclaimer,
            'risk_score': risk_score,
            'detected_patterns': detected_count,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
        
        # Log high-risk detections
        if risk_score >= 0.8:
            self.logger.warning(f"HIGH RISK LEGAL ADVICE DETECTED: {advice_level.value} (score: {risk_score:.2f})")
        
        return result
    
    def get_mandatory_disclaimer(self, advice_level: str) -> str:
        """Get appropriate mandatory disclaimer"""
        
        if advice_level == AdviceLevel.LEGAL_ADVICE.value:
            return """CRITICAL LEGAL DISCLAIMER

This response contains information that may constitute legal advice. 
This information is provided for general informational purposes only 
and should not be considered legal advice. Legal matters are highly 
fact-specific and laws vary by jurisdiction. You should consult with 
a qualified attorney in your jurisdiction for advice regarding your 
specific legal situation.

DO NOT RELY ON THIS INFORMATION FOR LEGAL DECISIONS WITHOUT 
CONSULTING A LICENSED ATTORNEY."""
        
        elif advice_level in [AdviceLevel.GUIDANCE.value, AdviceLevel.ADVICE.value]:
            return """LEGAL GUIDANCE DISCLAIMER

This response contains general guidance on legal matters. 
This information is provided for educational purposes only and 
should not be considered legal advice. Laws and procedures vary 
by jurisdiction and individual circumstances. Please consult with 
a qualified attorney for advice specific to your situation."""
        
        else:
            return """LEGAL INFORMATION DISCLAIMER

This response contains legal information for general educational 
purposes only. This is not legal advice and should not be relied 
upon for legal decisions. Laws vary by jurisdiction and individual 
circumstances may affect legal outcomes."""

# Global instance
emergency_advice_detector = EmergencyAdviceDetector()
