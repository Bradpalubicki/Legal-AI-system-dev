"""
EMERGENCY UPL COMPLIANCE MODULE

This module provides ZERO-TOLERANCE advice language detection and mandatory
disclaimer injection to prevent any unauthorized practice of law violations.

CRITICAL: This module must achieve 100% compliance rate for all outputs.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class ComplianceResult:
    is_compliant: bool
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    violations: List[str]
    original_text: str
    sanitized_text: str
    disclaimer_added: bool
    emergency_override: bool
    timestamp: datetime

class EmergencyUPLCompliance:
    """Emergency UPL compliance system with zero-tolerance advice detection"""
    
    def __init__(self):
        # ULTRA-AGGRESSIVE advice detection patterns - zero tolerance
        self.CRITICAL_ADVICE_PATTERNS = [
            # Direct instruction patterns (more comprehensive)
            r'\byou\s+must\b',
            r'\byou\s+have\s+to\b', 
            r'\byou\s+are\s+required\s+to\b',
            r'\byou\s+need\s+to\b',
            r'\byou\s+should\b',
            r'\byou\s+shall\b',
            r'\byou\s+ought\s+to\b',
            r'\byou\s+can\s+(?:sue|file|claim|argue|assert|negotiate|demand)\b',
            r'\byou\s+would\s+be\s+wise\s+to\b',
            r'\byou\s+better\b',
            r'\byou\s+have\s+no\s+choice\s+but\s+to\b',
            
            # Recommendation patterns (enhanced)
            r'\bi\s+recommend\s+(that\s+)?you\b',
            r'\bi\s+suggest\s+(that\s+)?you\b',
            r'\bi\s+advise\s+(that\s+)?you\b',
            r'\bmy\s+recommendation\s+(is\s+)?(?:that\s+)?you\b',
            r'\bmy\s+advice\s+(is\s+)?(?:that\s+)?you\b',
            r'\bin\s+my\s+opinion,?\s+you\s+should\b',
            r'\bit\s+would\s+be\s+wise\s+(for\s+you\s+)?to\b',
            r'\byou\s+would\s+be\s+(well-)?advised\s+to\b',
            
            # Strategy and recommendation patterns (ultra-comprehensive)
            r'\bthe\s+best\s+(option|choice|approach|strategy|course\s+of\s+action|thing\s+to\s+do)\s+(is|would\s+be)\s+(?:for\s+you\s+)?to\b',
            r'\bi\s+recommend\b',
            r'\bi\s+suggest\b',
            r'\bi\s+would\s+recommend\b',
            r'\bi\s+would\s+suggest\b',
            r'\bi\s+(strongly|highly)\s+(recommend|suggest|advise)\b',
            r'\byou\s+would\s+be\s+best\s+served\s+by\b',
            r'\bthe\s+(smart|right|wise)\s+(move|thing\s+to\s+do|choice)\s+(is|would\s+be)\b',
            r'\bthe\s+only\s+(option|choice)\s+is\s+to\b',
            r'\byou\s+have\s+no\s+(other\s+)?choice\s+but\s+to\b',
            r'\bif\s+i\s+were\s+you\b',
            r'\bin\s+your\s+(shoes|position|situation)\b',
            r'\byou\s+(really|definitely|absolutely|certainly)\s+(should|must|need\s+to)\b',
            r'\byou\'d\s+be\s+(wise|smart|foolish\s+not)\s+to\b',
            r'\bthere\'s\s+no\s+(doubt|question)\s+(that\s+)?you\s+should\b',
            r'\byou\s+(simply|just)\s+(cannot|must|should)\b',
            
            # Legal action advice
            r'\byou\s+(can|should|must)\s+sue\b',
            r'\byou\s+(can|should|must)\s+file\s+(a\s+)?(lawsuit|claim|suit)\b',
            r'\byou\s+have\s+(grounds|a\s+case)\s+(for|to)\b',
            r'\byou\s+should\s+contact\s+(a\s+)?lawyer\b',
            r'\byou\s+need\s+(legal\s+)?representation\b',
            r'\byou\s+should\s+hire\s+(an?\s+)?attorney\b',
            
            # Contract/document advice
            r'\byou\s+(should|must)\s+(not\s+)?sign\b',
            r'\bdon\'t\s+sign\s+(this|that|anything)\b',
            r'\byou\s+should\s+negotiate\b',
            r'\byou\s+should\s+include\s+a\s+clause\b',
            r'\byou\s+should\s+add\s+language\b',
            
            # Compliance/regulatory advice
            r'\byou\s+(must|need\s+to|should)\s+comply\s+with\b',
            r'\byou\s+are\s+(required|obligated)\s+to\b',
            r'\byou\s+have\s+an?\s+obligation\s+to\b',
            r'\byou\s+(must|should)\s+disclose\b',
            r'\byou\s+(must|should)\s+report\b',
            
            # Strategy advice
            r'\byour\s+(best\s+)?(strategy|approach)\s+(is|would\s+be)\b',
            r'\bi\s+would\s+(do|try|approach)\b',
            r'\bif\s+i\s+were\s+you\b',
            r'\bin\s+your\s+(situation|case|position)\b',
            
            # Outcome predictions
            r'\byou\s+will\s+(win|lose|succeed|fail)\b',
            r'\byour\s+chances\s+(are|look)\b',
            r'\byou\s+have\s+a\s+(strong|weak|good|poor)\s+case\b',
            r'\byou\s+(definitely|certainly|probably)\s+(will|can|should)\b',
        ]
        
        # Professional service language that creates attorney-client expectations
        self.PROFESSIONAL_SERVICE_PATTERNS = [
            r'\bas\s+your\s+(attorney|lawyer|counsel)\b',
            r'\bi\s+am\s+representing\s+you\b',
            r'\bin\s+my\s+professional\s+(opinion|judgment)\b',
            r'\bas\s+legal\s+counsel\b',
            r'\bunder\s+attorney[-\s]client\s+privilege\b',
            r'\bthis\s+is\s+confidential\b(?=.*legal)',
            r'\bi\s+am\s+providing\s+legal\s+(advice|services)\b',
            r'\bour\s+attorney[-\s]client\s+relationship\b',
        ]
        
        # Legal conclusion language
        self.LEGAL_CONCLUSION_PATTERNS = [
            r'\bthis\s+(violates|breaches|constitutes)\b',
            r'\bthis\s+is\s+(legal|illegal|unlawful|actionable)\b',
            r'\byou\s+have\s+been\s+(discriminated|harassed|wronged)\b',
            r'\bthis\s+is\s+(malpractice|negligence|fraud)\b',
            r'\byou\s+have\s+a\s+(claim|case|right)\s+(against|to)\b',
            r'\bthe\s+law\s+(requires|prohibits|mandates)\b',
            r'\baccording\s+to\s+(the\s+)?law\b',
        ]
        
        # Emergency disclaimer templates
        self.EMERGENCY_DISCLAIMERS = {
            'CRITICAL': """
🚨 CRITICAL LEGAL NOTICE 🚨
GENERAL INFORMATION ONLY - NOT LEGAL ADVICE

⚖️ This information is provided for educational purposes only and does NOT constitute legal advice.
🚫 No attorney-client relationship is created by this communication.
👨‍⚖️ ALWAYS consult with a qualified attorney licensed in your jurisdiction before making any legal decisions.
📋 Laws vary significantly by state and locality and change frequently.

The information provided may not be applicable to your specific situation and should not be relied upon without professional legal consultation.
""",
            'HIGH': """
⚖️ IMPORTANT LEGAL DISCLAIMER ⚖️
GENERAL INFORMATION ONLY - NOT LEGAL ADVICE

This information is for educational purposes only and does not constitute legal advice.
No attorney-client relationship is created. Always consult a qualified attorney.
Laws vary by jurisdiction and change frequently.
""",
            'MEDIUM': """
LEGAL DISCLAIMER: This information is for educational purposes only and does not constitute legal advice.
Consult a qualified attorney for advice specific to your situation.
""",
            'LOW': """
Disclaimer: General information only - not legal advice. Consult an attorney for legal guidance.
"""
        }
        
        # Safe alternative language patterns
        self.SAFE_ALTERNATIVES = {
            r'\byou\s+must\b': 'individuals may need to',
            r'\byou\s+should\b': 'individuals typically',
            r'\bi\s+recommend\b': 'common approaches include',
            r'\bmy\s+advice\s+is\b': 'general information suggests',
            r'\byou\s+need\s+to\b': 'it may be necessary to',
            r'\byou\s+have\s+to\b': 'requirements typically include',
            r'\byou\s+can\s+sue\b': 'legal remedies may be available',
            r'\byou\s+should\s+contact\s+a\s+lawyer\b': 'legal consultation is recommended',
        }
    
    def analyze_content(self, content: str, context: Dict[str, Any] = None) -> ComplianceResult:
        """
        Analyze content for UPL compliance violations with zero tolerance.
        
        Args:
            content: Text content to analyze
            context: Additional context (user_id, session_id, etc.)
            
        Returns:
            ComplianceResult with compliance status and sanitized content
        """
        
        logger.info(f"[UPL_COMPLIANCE] Analyzing content for advice language")
        
        violations = []
        risk_level = 'LOW'
        emergency_override = False
        
        # Check for critical advice patterns
        critical_matches = []
        for pattern in self.CRITICAL_ADVICE_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                critical_matches.append({
                    'pattern': pattern,
                    'match': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })
                violations.append(f"Advice language detected: '{match.group()}'")
        
        # Check for professional service language
        professional_matches = []
        for pattern in self.PROFESSIONAL_SERVICE_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                professional_matches.append({
                    'pattern': pattern,
                    'match': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })
                violations.append(f"Professional service language: '{match.group()}'")
        
        # Check for legal conclusions
        conclusion_matches = []
        for pattern in self.LEGAL_CONCLUSION_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                conclusion_matches.append({
                    'pattern': pattern,
                    'match': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })
                violations.append(f"Legal conclusion language: '{match.group()}'")
        
        # Determine risk level
        total_violations = len(critical_matches) + len(professional_matches) + len(conclusion_matches)
        
        if len(professional_matches) > 0 or len(conclusion_matches) > 2:
            risk_level = 'CRITICAL'
            emergency_override = True
        elif len(critical_matches) > 3 or len(conclusion_matches) > 0:
            risk_level = 'HIGH'
            emergency_override = True
        elif len(critical_matches) > 1:
            risk_level = 'MEDIUM'
        elif len(critical_matches) > 0:
            risk_level = 'MEDIUM'
        
        # Apply emergency override for any violations
        if total_violations > 0:
            emergency_override = True
        
        # Sanitize content
        sanitized_content = self._sanitize_content(content, critical_matches, professional_matches, conclusion_matches)
        
        # Add disclaimer
        disclaimer_added = True
        final_content = self._add_emergency_disclaimer(sanitized_content, risk_level)
        
        # Log compliance check
        self._log_compliance_check(content, violations, risk_level, context)
        
        result = ComplianceResult(
            is_compliant=len(violations) == 0,
            risk_level=risk_level,
            violations=violations,
            original_text=content,
            sanitized_text=final_content,
            disclaimer_added=disclaimer_added,
            emergency_override=emergency_override,
            timestamp=datetime.utcnow()
        )
        
        return result
    
    def _sanitize_content(self, content: str, critical_matches: List, professional_matches: List, conclusion_matches: List) -> str:
        """Sanitize content by replacing problematic language with safe alternatives"""
        
        sanitized = content
        
        # Apply safe alternatives for common patterns
        for pattern, replacement in self.SAFE_ALTERNATIVES.items():
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        # Remove or modify highly problematic phrases
        for match_list in [critical_matches, professional_matches, conclusion_matches]:
            for match_info in match_list:
                match_text = match_info['match']
                # Replace with generic information language
                if any(word in match_text.lower() for word in ['must', 'should', 'recommend', 'advise']):
                    safe_replacement = f"[Information: General practices typically involve consideration of {match_text.lower().replace('you', 'individuals').replace('must', 'may').replace('should', 'typically')}]"
                else:
                    safe_replacement = f"[General Information: {match_text.lower()}]"
                
                sanitized = sanitized.replace(match_text, safe_replacement)
        
        return sanitized
    
    def _add_emergency_disclaimer(self, content: str, risk_level: str) -> str:
        """Add appropriate emergency disclaimer based on risk level"""
        
        disclaimer = self.EMERGENCY_DISCLAIMERS[risk_level]
        
        # Format final content with disclaimer
        final_content = f"{disclaimer}\n\n{'='*50}\nINFORMATION CONTENT:\n{'='*50}\n\n{content}\n\n{'='*50}\n{disclaimer}\n{'='*50}"
        
        return final_content
    
    def _log_compliance_check(self, content: str, violations: List[str], risk_level: str, context: Dict[str, Any] = None):
        """Log compliance check for audit trail"""
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'upl_compliance_check',
            'content_length': len(content),
            'violations_count': len(violations),
            'violations': violations,
            'risk_level': risk_level,
            'context': context or {},
            'compliance_version': '2.0_emergency'
        }
        
        logger.info(f"[UPL_COMPLIANCE] {json.dumps(log_data)}")
    
    def bulk_analyze(self, content_list: List[str]) -> List[ComplianceResult]:
        """Analyze multiple content pieces in bulk"""
        
        results = []
        
        logger.info(f"[UPL_COMPLIANCE] Bulk analyzing {len(content_list)} content pieces")
        
        for i, content in enumerate(content_list):
            context = {'bulk_analysis': True, 'item_index': i}
            result = self.analyze_content(content, context)
            results.append(result)
        
        # Log bulk analysis summary
        total_violations = sum(len(r.violations) for r in results)
        compliant_count = sum(1 for r in results if r.is_compliant)
        compliance_rate = (compliant_count / len(results)) * 100 if results else 0
        
        logger.info(f"[UPL_COMPLIANCE] Bulk analysis complete: {compliance_rate:.1f}% compliant, {total_violations} total violations")
        
        return results
    
    def validate_api_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize API response data"""
        
        if not isinstance(response_data, dict):
            return response_data
        
        # Check common fields that might contain advice language
        fields_to_check = ['message', 'content', 'response', 'result', 'analysis', 'summary', 'recommendation']
        
        violations_found = False
        
        for field in fields_to_check:
            if field in response_data and isinstance(response_data[field], str):
                result = self.analyze_content(response_data[field], {'api_response_field': field})
                
                if not result.is_compliant:
                    violations_found = True
                    response_data[field] = result.sanitized_text
                    
                    # Add compliance info to response
                    if '_compliance_info' not in response_data:
                        response_data['_compliance_info'] = {}
                    
                    response_data['_compliance_info'].update({
                        f'{field}_violations': result.violations,
                        f'{field}_risk_level': result.risk_level,
                        f'{field}_sanitized': True
                    })
        
        # Always add disclaimer to API responses
        response_data['_legal_disclaimer'] = self.EMERGENCY_DISCLAIMERS['HIGH']
        response_data['_compliance_info'] = response_data.get('_compliance_info', {})
        response_data['_compliance_info'].update({
            'disclaimer_injected': True,
            'not_legal_advice': True,
            'attorney_consultation_required': True,
            'compliance_check_timestamp': datetime.utcnow().isoformat()
        })
        
        return response_data

# Create global compliance instance
emergency_upl_compliance = EmergencyUPLCompliance()

def ensure_upl_compliance(content: str, context: Dict[str, Any] = None) -> ComplianceResult:
    """
    Convenience function to ensure UPL compliance for any content.
    
    This function should be called for ALL content that will be shown to users.
    """
    return emergency_upl_compliance.analyze_content(content, context)

def sanitize_api_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to sanitize API response data.
    
    This function should be called for ALL API responses.
    """
    return emergency_upl_compliance.validate_api_response(response_data)

__all__ = [
    'EmergencyUPLCompliance',
    'ComplianceResult',
    'emergency_upl_compliance',
    'ensure_upl_compliance',
    'sanitize_api_response'
]