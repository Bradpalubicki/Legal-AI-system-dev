#!/usr/bin/env python3
"""
AI SAFETY MONITORING SYSTEM

Comprehensive AI safety monitoring for legal AI systems:
- Model output safety validation
- Bias detection and mitigation
- Hallucination detection
- Content safety filtering
- Ethical compliance monitoring
- Real-time safety alerts
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
import threading
from collections import defaultdict, deque
import asyncio

logger = logging.getLogger(__name__)

class SafetyLevel(Enum):
    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"

class SafetyCategory(Enum):
    CONTENT_SAFETY = "content_safety"
    BIAS_DETECTION = "bias_detection"
    HALLUCINATION = "hallucination"
    ETHICAL_COMPLIANCE = "ethical_compliance"
    OUTPUT_QUALITY = "output_quality"
    LEGAL_ACCURACY = "legal_accuracy"

@dataclass
class SafetyAlert:
    """AI safety alert data structure"""
    id: str
    timestamp: datetime
    category: SafetyCategory
    level: SafetyLevel
    message: str
    model_output: str
    confidence: float
    metadata: Dict[str, Any]
    resolved: bool = False

@dataclass
class SafetyMetrics:
    """AI safety metrics"""
    total_outputs_analyzed: int
    safe_outputs: int
    warning_outputs: int
    danger_outputs: int
    critical_outputs: int
    bias_detected: int
    hallucinations_detected: int
    ethical_violations: int
    safety_score: float
    last_updated: datetime

class AISafetyMonitor:
    """Comprehensive AI safety monitoring system"""
    
    def __init__(self):
        self.safety_alerts = deque(maxlen=10000)
        self.metrics = SafetyMetrics(
            total_outputs_analyzed=0,
            safe_outputs=0,
            warning_outputs=0,
            danger_outputs=0,
            critical_outputs=0,
            bias_detected=0,
            hallucinations_detected=0,
            ethical_violations=0,
            safety_score=100.0,
            last_updated=datetime.utcnow()
        )
        
        # Initialize safety detection patterns
        self.bias_patterns = self._load_bias_patterns()
        self.hallucination_patterns = self._load_hallucination_patterns()
        self.ethical_violation_patterns = self._load_ethical_patterns()
        self.content_safety_patterns = self._load_content_safety_patterns()
        
        # Real-time monitoring
        self.monitoring_enabled = True
        self.alert_thresholds = self._load_alert_thresholds()
        
        logger.info("[AI_SAFETY] AI safety monitoring system initialized")
    
    def _load_bias_patterns(self) -> List[Dict[str, Any]]:
        """Load bias detection patterns"""
        return [
            # Gender bias
            {
                'pattern': r'\b(men|women|male|female)\s+(are|tend to be|usually|typically)\s+(better|worse|more|less)\s+(at|suited for)',
                'category': 'gender_bias',
                'severity': 'high',
                'description': 'Gender-based capability assumptions'
            },
            
            # Racial/ethnic bias
            {
                'pattern': r'\b(people of|individuals from|those from)\s+\w+\s+(background|descent|ethnicity)\s+(are|tend to|usually)',
                'category': 'racial_bias',
                'severity': 'critical',
                'description': 'Racial or ethnic stereotyping'
            },
            
            # Age bias
            {
                'pattern': r'\b(older|younger|elderly|young)\s+(people|individuals|workers|employees)\s+(cannot|are unable to|struggle with)',
                'category': 'age_bias',
                'severity': 'medium',
                'description': 'Age-based capability assumptions'
            },
            
            # Socioeconomic bias
            {
                'pattern': r'\b(low-income|poor|wealthy|rich)\s+(people|families|individuals)\s+(are|tend to be|usually)',
                'category': 'socioeconomic_bias',
                'severity': 'high',
                'description': 'Socioeconomic stereotyping'
            },
            
            # Legal bias
            {
                'pattern': r'\b(defendants|criminals|inmates)\s+(are|tend to be)\s+(typically|usually|often)\s+\w+',
                'category': 'legal_bias',
                'severity': 'critical',
                'description': 'Criminal justice bias'
            }
        ]
    
    def _load_hallucination_patterns(self) -> List[Dict[str, Any]]:
        """Load hallucination detection patterns"""
        return [
            # Fabricated legal citations
            {
                'pattern': r'\b\d+\s+[A-Z][a-z]+\.?\s+\d+,?\s+\d+\s+\(\d{4}\)',
                'category': 'fake_citation',
                'severity': 'critical',
                'description': 'Potentially fabricated legal citation'
            },
            
            # Fabricated case names
            {
                'pattern': r'\b[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+(?:\s+\w+)?,\s+Case No\.\s+\d+-\w+-\d+',
                'category': 'fake_case',
                'severity': 'critical',
                'description': 'Potentially fabricated case reference'
            },
            
            # New York specific citation patterns (for NY UPL compliance)
            {
                'pattern': r'\b\d+\s+N\.Y\.\s?\d+\s+\(\d{4}\)',
                'category': 'ny_citation_check',
                'severity': 'high',
                'description': 'NY citation requiring verification (NYC Bar Opinion 2024-5 compliance)'
            },
            {
                'pattern': r'\b\d+\s+A\.D\.\s?\d+\s+\(\d+\w+\s+Dept\.\s+\d{4}\)',
                'category': 'ny_appellate_citation',
                'severity': 'high',
                'description': 'NY Appellate Division citation requiring verification'
            },
            
            # Suspicious specificity
            {
                'pattern': r'\b(exactly|precisely)\s+\d+(\.\d+)?%\s+of\s+(cases|clients|situations)',
                'category': 'suspicious_statistic',
                'severity': 'medium',
                'description': 'Suspiciously specific statistics'
            },
            
            # Fabricated procedure details
            {
                'pattern': r'\baccording to\s+(Section|Rule|Code)\s+\d+\.\d+\.\d+\s+of\s+the\s+\w+\s+(Code|Act|Statute)',
                'category': 'fake_regulation',
                'severity': 'high',
                'description': 'Potentially fabricated legal reference'
            }
        ]
    
    def _load_ethical_patterns(self) -> List[Dict[str, Any]]:
        """Load ethical violation patterns"""
        return [
            # Encouraging illegal activity
            {
                'pattern': r'\b(you should|i recommend|consider)\s+.*(hiding|concealing|destroying)\s+(evidence|documents|records)',
                'category': 'illegal_advice',
                'severity': 'critical',
                'description': 'Encouraging evidence tampering'
            },
            
            # Discrimination encouragement
            {
                'pattern': r'\b(avoid|don\'t hire|exclude)\s+.*(because of|due to)\s+(race|gender|age|religion|disability)',
                'category': 'discrimination',
                'severity': 'critical',
                'description': 'Encouraging discrimination'
            },
            
            # Conflict of interest
            {
                'pattern': r'\b(represent both|dual representation)\s+.*(without|while hiding)',
                'category': 'conflict_of_interest',
                'severity': 'high',
                'description': 'Potential conflict of interest advice'
            },
            
            # Privacy violations
            {
                'pattern': r'\b(access|obtain|retrieve)\s+.*(private|confidential|protected)\s+(information|records|data)\s+(without|secretly)',
                'category': 'privacy_violation',
                'severity': 'high',
                'description': 'Privacy violation encouragement'
            }
        ]
    
    def _load_content_safety_patterns(self) -> List[Dict[str, Any]]:
        """Load content safety patterns"""
        return [
            # Violent content
            {
                'pattern': r'\b(violence|harm|hurt|damage)\s+(to|against)\s+(person|people|individual)',
                'category': 'violence',
                'severity': 'critical',
                'description': 'Violent content detected'
            },
            
            # Self-harm content
            {
                'pattern': r'\b(harm yourself|hurt yourself|end your life|suicide)',
                'category': 'self_harm',
                'severity': 'critical',
                'description': 'Self-harm content detected'
            },
            
            # Harassment content
            {
                'pattern': r'\b(harass|stalk|intimidate|threaten)\s+.*(person|individual|client)',
                'category': 'harassment',
                'severity': 'high',
                'description': 'Harassment content detected'
            }
        ]
    
    def _load_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Load safety alert thresholds"""
        return {
            'bias_detection': {
                'warning_threshold': 0.1,    # 10% of outputs
                'danger_threshold': 0.2,     # 20% of outputs
                'critical_threshold': 0.3    # 30% of outputs
            },
            'hallucination': {
                'warning_threshold': 0.05,   # 5% of outputs
                'danger_threshold': 0.1,     # 10% of outputs
                'critical_threshold': 0.15   # 15% of outputs
            },
            'ethical_violation': {
                'warning_threshold': 0.02,   # 2% of outputs
                'danger_threshold': 0.05,    # 5% of outputs
                'critical_threshold': 0.1    # 10% of outputs
            },
            'content_safety': {
                'warning_threshold': 0.01,   # 1% of outputs
                'danger_threshold': 0.02,    # 2% of outputs
                'critical_threshold': 0.05   # 5% of outputs
            }
        }
    
    def analyze_output(self, model_output: str, context: Dict[str, Any] = None) -> Tuple[SafetyLevel, List[SafetyAlert]]:
        """Analyze AI model output for safety issues"""
        
        if not self.monitoring_enabled:
            return SafetyLevel.SAFE, []
        
        context = context or {}
        alerts = []
        max_safety_level = SafetyLevel.SAFE
        
        # Update metrics
        self.metrics.total_outputs_analyzed += 1
        
        # 1. Bias detection
        bias_alerts = self._detect_bias(model_output, context)
        if bias_alerts:
            alerts.extend(bias_alerts)
            self.metrics.bias_detected += len(bias_alerts)
            max_safety_level = self._update_max_safety_level(max_safety_level, bias_alerts)
        
        # 2. Hallucination detection
        hallucination_alerts = self._detect_hallucinations(model_output, context)
        if hallucination_alerts:
            alerts.extend(hallucination_alerts)
            self.metrics.hallucinations_detected += len(hallucination_alerts)
            max_safety_level = self._update_max_safety_level(max_safety_level, hallucination_alerts)
        
        # 3. Ethical violation detection
        ethical_alerts = self._detect_ethical_violations(model_output, context)
        if ethical_alerts:
            alerts.extend(ethical_alerts)
            self.metrics.ethical_violations += len(ethical_alerts)
            max_safety_level = self._update_max_safety_level(max_safety_level, ethical_alerts)
        
        # 4. Content safety detection
        content_alerts = self._detect_content_safety_issues(model_output, context)
        if content_alerts:
            alerts.extend(content_alerts)
            max_safety_level = self._update_max_safety_level(max_safety_level, content_alerts)
        
        # Update metrics counters
        if max_safety_level == SafetyLevel.SAFE:
            self.metrics.safe_outputs += 1
        elif max_safety_level == SafetyLevel.WARNING:
            self.metrics.warning_outputs += 1
        elif max_safety_level == SafetyLevel.DANGER:
            self.metrics.danger_outputs += 1
        elif max_safety_level == SafetyLevel.CRITICAL:
            self.metrics.critical_outputs += 1
        
        # Store alerts
        for alert in alerts:
            self.safety_alerts.append(alert)
        
        # Update safety score
        self._update_safety_score()
        
        # Log high-risk issues
        if max_safety_level in [SafetyLevel.DANGER, SafetyLevel.CRITICAL]:
            logger.warning(f"[AI_SAFETY] {max_safety_level.value.upper()} safety issue detected: {len(alerts)} alerts")
        
        return max_safety_level, alerts
    
    def _detect_bias(self, text: str, context: Dict[str, Any]) -> List[SafetyAlert]:
        """Detect bias in AI output"""
        alerts = []
        text_lower = text.lower()
        
        for pattern_data in self.bias_patterns:
            pattern = pattern_data['pattern']
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            
            if matches:
                severity_map = {
                    'low': SafetyLevel.WARNING,
                    'medium': SafetyLevel.WARNING,
                    'high': SafetyLevel.DANGER,
                    'critical': SafetyLevel.CRITICAL
                }
                
                alert = SafetyAlert(
                    id=f"bias_{int(time.time())}_{len(alerts)}",
                    timestamp=datetime.utcnow(),
                    category=SafetyCategory.BIAS_DETECTION,
                    level=severity_map.get(pattern_data['severity'], SafetyLevel.WARNING),
                    message=f"Bias detected: {pattern_data['description']}",
                    model_output=text[:500],  # Truncate for storage
                    confidence=0.8,
                    metadata={
                        'bias_category': pattern_data['category'],
                        'pattern_matched': pattern,
                        'matches': matches[:5]  # Limit matches stored
                    }
                )
                alerts.append(alert)
        
        return alerts
    
    def _detect_hallucinations(self, text: str, context: Dict[str, Any]) -> List[SafetyAlert]:
        """Detect potential hallucinations in AI output"""
        alerts = []
        
        for pattern_data in self.hallucination_patterns:
            pattern = pattern_data['pattern']
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            if matches:
                severity_map = {
                    'low': SafetyLevel.WARNING,
                    'medium': SafetyLevel.WARNING,
                    'high': SafetyLevel.DANGER,
                    'critical': SafetyLevel.CRITICAL
                }
                
                alert = SafetyAlert(
                    id=f"hallucination_{int(time.time())}_{len(alerts)}",
                    timestamp=datetime.utcnow(),
                    category=SafetyCategory.HALLUCINATION,
                    level=severity_map.get(pattern_data['severity'], SafetyLevel.WARNING),
                    message=f"Potential hallucination: {pattern_data['description']}",
                    model_output=text[:500],
                    confidence=0.7,
                    metadata={
                        'hallucination_category': pattern_data['category'],
                        'pattern_matched': pattern,
                        'matches': matches[:3]
                    }
                )
                alerts.append(alert)
        
        return alerts
    
    def _detect_ethical_violations(self, text: str, context: Dict[str, Any]) -> List[SafetyAlert]:
        """Detect ethical violations in AI output"""
        alerts = []
        text_lower = text.lower()
        
        for pattern_data in self.ethical_violation_patterns:
            pattern = pattern_data['pattern']
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            
            if matches:
                severity_map = {
                    'low': SafetyLevel.WARNING,
                    'medium': SafetyLevel.WARNING,
                    'high': SafetyLevel.DANGER,
                    'critical': SafetyLevel.CRITICAL
                }
                
                alert = SafetyAlert(
                    id=f"ethical_{int(time.time())}_{len(alerts)}",
                    timestamp=datetime.utcnow(),
                    category=SafetyCategory.ETHICAL_COMPLIANCE,
                    level=severity_map.get(pattern_data['severity'], SafetyLevel.DANGER),
                    message=f"Ethical violation detected: {pattern_data['description']}",
                    model_output=text[:500],
                    confidence=0.9,
                    metadata={
                        'violation_category': pattern_data['category'],
                        'pattern_matched': pattern,
                        'matches': matches[:3]
                    }
                )
                alerts.append(alert)
        
        return alerts
    
    def _detect_content_safety_issues(self, text: str, context: Dict[str, Any]) -> List[SafetyAlert]:
        """Detect content safety issues in AI output"""
        alerts = []
        text_lower = text.lower()
        
        for pattern_data in self.content_safety_patterns:
            pattern = pattern_data['pattern']
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            
            if matches:
                alert = SafetyAlert(
                    id=f"content_{int(time.time())}_{len(alerts)}",
                    timestamp=datetime.utcnow(),
                    category=SafetyCategory.CONTENT_SAFETY,
                    level=SafetyLevel.CRITICAL,  # Content safety is always critical
                    message=f"Content safety issue: {pattern_data['description']}",
                    model_output=text[:500],
                    confidence=0.95,
                    metadata={
                        'safety_category': pattern_data['category'],
                        'pattern_matched': pattern,
                        'matches': matches[:3]
                    }
                )
                alerts.append(alert)
        
        return alerts
    
    def _update_max_safety_level(self, current_max: SafetyLevel, alerts: List[SafetyAlert]) -> SafetyLevel:
        """Update maximum safety level based on alerts"""
        level_priority = {
            SafetyLevel.SAFE: 0,
            SafetyLevel.WARNING: 1,
            SafetyLevel.DANGER: 2,
            SafetyLevel.CRITICAL: 3
        }
        
        max_alert_level = max((alert.level for alert in alerts), key=lambda x: level_priority[x], default=SafetyLevel.SAFE)
        
        return max_alert_level if level_priority[max_alert_level] > level_priority[current_max] else current_max
    
    def _update_safety_score(self):
        """Update overall safety score"""
        if self.metrics.total_outputs_analyzed == 0:
            self.metrics.safety_score = 100.0
            return
        
        # Calculate safety score based on violations
        total = self.metrics.total_outputs_analyzed
        violations = (
            self.metrics.warning_outputs * 0.1 +
            self.metrics.danger_outputs * 0.5 +
            self.metrics.critical_outputs * 1.0
        )
        
        # Safety score: 100 - (violation_rate * 100)
        violation_rate = violations / total
        self.metrics.safety_score = max(0.0, 100.0 - (violation_rate * 100))
        self.metrics.last_updated = datetime.utcnow()
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety monitoring status"""
        return {
            'monitoring_enabled': self.monitoring_enabled,
            'safety_score': round(self.metrics.safety_score, 2),
            'total_outputs_analyzed': self.metrics.total_outputs_analyzed,
            'safety_breakdown': {
                'safe_outputs': self.metrics.safe_outputs,
                'warning_outputs': self.metrics.warning_outputs,
                'danger_outputs': self.metrics.danger_outputs,
                'critical_outputs': self.metrics.critical_outputs
            },
            'issue_counts': {
                'bias_detected': self.metrics.bias_detected,
                'hallucinations_detected': self.metrics.hallucinations_detected,
                'ethical_violations': self.metrics.ethical_violations
            },
            'active_alerts': len([a for a in self.safety_alerts if not a.resolved]),
            'last_updated': self.metrics.last_updated.isoformat(),
            'system_status': 'healthy' if self.metrics.safety_score >= 95.0 else 'needs_attention'
        }
    
    def get_recent_alerts(self, hours: int = 24, category: SafetyCategory = None) -> List[Dict[str, Any]]:
        """Get recent safety alerts"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_alerts = [
            alert for alert in self.safety_alerts
            if alert.timestamp >= cutoff_time and (category is None or alert.category == category)
        ]
        
        return [asdict(alert) for alert in recent_alerts[-100:]]  # Limit to 100 most recent
    
    def resolve_alert(self, alert_id: str, resolution_note: str = "") -> bool:
        """Mark an alert as resolved"""
        for alert in self.safety_alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.metadata['resolution_note'] = resolution_note
                alert.metadata['resolved_at'] = datetime.utcnow().isoformat()
                logger.info(f"[AI_SAFETY] Alert resolved: {alert_id}")
                return True
        
        return False
    
    def enable_monitoring(self):
        """Enable AI safety monitoring"""
        self.monitoring_enabled = True
        logger.info("[AI_SAFETY] Safety monitoring enabled")
    
    def disable_monitoring(self):
        """Disable AI safety monitoring"""
        self.monitoring_enabled = False
        logger.warning("[AI_SAFETY] Safety monitoring disabled")

# Global AI safety monitor instance
ai_safety_monitor = AISafetyMonitor()