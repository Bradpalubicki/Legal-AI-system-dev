#!/usr/bin/env python3
"""
Legal Advice vs Legal Information Detector
Critical compliance tool to distinguish between impermissible legal advice and permissible legal information
"""

import re
import logging
import logging.handlers
import sqlite3
from typing import Dict, List, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

class ContentClassification(Enum):
    """Classification of legal content"""
    LEGAL_INFORMATION = "legal_information"      # Permissible - general legal information
    LEGAL_ADVICE = "legal_advice"               # Impermissible - specific advice to client
    BORDERLINE = "borderline"                   # Requires attorney review
    PROCEDURAL_GUIDANCE = "procedural_guidance"  # Permissible - process information
    EDUCATIONAL_CONTENT = "educational_content"  # Permissible - educational material

class AdviceRiskLevel(Enum):
    """Risk level for potential legal advice"""
    LOW = "low"           # Clearly informational
    MEDIUM = "medium"     # Some advice indicators
    HIGH = "high"         # Clear advice language
    CRITICAL = "critical" # Direct client advice

@dataclass
class AdviceAnalysis:
    """Analysis results for legal advice detection"""
    classification: ContentClassification
    risk_level: AdviceRiskLevel
    confidence_score: float
    advice_indicators: List[str]
    information_indicators: List[str]
    problematic_phrases: List[str]
    suggested_corrections: List[Dict[str, str]]
    requires_attorney_review: bool
    explanation: str

class LegalAdviceDetector:
    """Detector to distinguish legal advice from legal information"""
    
    def __init__(self, db_path: str = "legal_advice_detection.db"):
        self.db_path = db_path
        self.logger = logging.getLogger('legal_advice_detector')
        self._init_database()
        
        # LEGAL ADVICE INDICATORS (IMPERMISSIBLE)
        self.advice_indicators = {
            # Direct recommendations
            "direct_advice": [
                r"\byou should\b",
                r"\byou must\b", 
                r"\byou need to\b",
                r"\bi recommend\b",
                r"\bi advise\b",
                r"\bi suggest\b",
                r"\byou ought to\b",
                r"\bit would be best if you\b",
                r"\byour best option is\b",
                r"\byour next step should be\b"
            ],
            
            # Imperative commands
            "imperatives": [
                r"\bfile\s+(?:an?\s+)?(?:motion|objection|petition|complaint)\b",
                r"\bdon't\s+(?:sign|agree|accept)\b",
                r"\brefuse\s+to\b",
                r"\bdemand\s+that\b",
                r"\btake\s+legal\s+action\b",
                r"\bpursue\s+(?:litigation|legal\s+action)\b"
            ],
            
            # Future predictions
            "predictions": [
                r"\byou will\s+(?:win|lose|succeed)\b",
                r"\bthe court will\s+(?:rule|find|decide)\s+in your favor\b",
                r"\byou have a\s+(?:strong|good|weak)\s+case\b",
                r"\byour chances are\b",
                r"\byou're likely to\b"
            ],
            
            # Client-specific guidance
            "client_specific": [
                r"\bin your case\b",
                r"\bbased on your situation\b",
                r"\bgiven your circumstances\b",
                r"\bfor your specific case\b",
                r"\bin your particular situation\b"
            ]
        }
        
        # LEGAL INFORMATION INDICATORS (PERMISSIBLE)
        self.information_indicators = {
            # General statements
            "general_statements": [
                r"\btypically\b",
                r"\bgenerally\b", 
                r"\busually\b",
                r"\bcommonly\b",
                r"\bin most cases\b",
                r"\bthe law provides\b",
                r"\baccording to\s+(?:statute|regulation|rule)\b",
                r"\bunder\s+(?:federal|state)\s+law\b"
            ],
            
            # Educational language
            "educational": [
                r"\bfor example\b",
                r"\bfor instance\b",
                r"\bthis means that\b",
                r"\bthe purpose of this rule is\b",
                r"\bthis statute requires\b",
                r"\bthe court held that\b"
            ],
            
            # Process descriptions
            "procedural": [
                r"\bthe process involves\b",
                r"\bsteps typically include\b",
                r"\bprocedure requires\b",
                r"\btimeline is\b",
                r"\bdeadlines are\b",
                r"\brequirements include\b"
            ],
            
            # Citation-based information
            "authority_based": [
                r"\baccording to\s+\w+\s+v\.\s+\w+\b",
                r"\bas stated in\b",
                r"\bthe statute provides\b",
                r"\bthe regulation states\b",
                r"\bper\s+(?:local\s+)?rule\b"
            ]
        }
        
        # CORRECTION TEMPLATES
        self.correction_templates = [
            {
                "problem": r"\byou should file\b",
                "correction": "parties typically file",
                "explanation": "Change from directive advice to general information"
            },
            {
                "problem": r"\bi recommend\b",
                "correction": "common approaches include",
                "explanation": "Change from personal recommendation to general options"
            },
            {
                "problem": r"\byou must\b",
                "correction": "the law requires",
                "explanation": "Change from personal directive to legal requirement statement"
            },
            {
                "problem": r"\bin your case\b",
                "correction": "in similar situations",
                "explanation": "Change from client-specific to general scenarios"
            },
            {
                "problem": r"\byou will win\b",
                "correction": "similar cases have succeeded when",
                "explanation": "Change from prediction to historical information"
            }
        ]
    
    def _init_database(self):
        """Initialize advice detection database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Advice detection results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS advice_detection_results (
                analysis_id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                analyzed_at TIMESTAMP NOT NULL,
                classification TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                advice_indicators TEXT NOT NULL,
                information_indicators TEXT NOT NULL,
                problematic_phrases TEXT NOT NULL,
                suggested_corrections TEXT NOT NULL,
                requires_review BOOLEAN NOT NULL,
                explanation TEXT NOT NULL,
                attorney_reviewed BOOLEAN DEFAULT FALSE,
                reviewer_id TEXT,
                review_date TIMESTAMP,
                review_approved BOOLEAN
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def analyze_content(self, content: str, context: Dict[str, Any] = None) -> AdviceAnalysis:
        """Analyze content to distinguish legal advice from legal information"""
        
        if context is None:
            context = {}
        
        content_lower = content.lower()
        
        # Find advice indicators
        advice_matches = []
        for category, patterns in self.advice_indicators.items():
            for pattern in patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                for match in matches:
                    advice_matches.append({
                        "category": category,
                        "pattern": pattern,
                        "match": match,
                        "severity": self._get_severity_score(category)
                    })
        
        # Find information indicators
        info_matches = []
        for category, patterns in self.information_indicators.items():
            for pattern in patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                for match in matches:
                    info_matches.append({
                        "category": category,
                        "pattern": pattern,
                        "match": match,
                        "weight": self._get_info_weight(category)
                    })
        
        # Calculate scores
        advice_score = sum(match["severity"] for match in advice_matches)
        info_score = sum(match["weight"] for match in info_matches)
        
        # Adjust for context
        if context.get("has_client_id"):
            advice_score += 2.0  # Client-specific context increases advice risk
        
        if context.get("output_type") == "legal_research":
            info_score += 1.0  # Research context favors information classification
        
        if context.get("output_type") == "client_communication":
            advice_score += 3.0  # Client communication increases advice risk
        
        # Classify content
        net_score = advice_score - info_score
        classification, risk_level = self._classify_content(net_score, advice_score, info_score)
        
        # Calculate confidence
        confidence_score = min(abs(net_score) / 5.0, 1.0)  # Normalize to 0-1
        
        # Find problematic phrases
        problematic_phrases = self._identify_problematic_phrases(content)
        
        # Generate corrections
        suggested_corrections = self._generate_corrections(content, problematic_phrases)
        
        # Determine if attorney review required
        requires_review = (
            classification == ContentClassification.LEGAL_ADVICE or
            classification == ContentClassification.BORDERLINE or
            risk_level in [AdviceRiskLevel.HIGH, AdviceRiskLevel.CRITICAL]
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            classification, advice_matches, info_matches, net_score
        )
        
        analysis = AdviceAnalysis(
            classification=classification,
            risk_level=risk_level,
            confidence_score=confidence_score,
            advice_indicators=[match["match"] for match in advice_matches],
            information_indicators=[match["match"] for match in info_matches],
            problematic_phrases=problematic_phrases,
            suggested_corrections=suggested_corrections,
            requires_attorney_review=requires_review,
            explanation=explanation
        )
        
        # Store analysis
        self._store_analysis(content, analysis)
        
        return analysis
    
    def _get_severity_score(self, category: str) -> float:
        """Get severity score for advice indicator category"""
        severity_map = {
            "direct_advice": 3.0,      # Most severe
            "imperatives": 2.5,        # Very severe
            "predictions": 2.0,        # Severe
            "client_specific": 1.5     # Moderate
        }
        return severity_map.get(category, 1.0)
    
    def _get_info_weight(self, category: str) -> float:
        """Get weight for information indicator category"""
        weight_map = {
            "authority_based": 2.0,    # Strong information indicator
            "general_statements": 1.5, # Good information indicator
            "procedural": 1.3,         # Moderate information indicator
            "educational": 1.0         # Basic information indicator
        }
        return weight_map.get(category, 1.0)
    
    def _classify_content(self, net_score: float, advice_score: float, info_score: float) -> Tuple[ContentClassification, AdviceRiskLevel]:
        """Classify content based on analysis scores"""
        
        # Critical advice (immediate attorney review required)
        if advice_score >= 5.0 or net_score >= 4.0:
            return ContentClassification.LEGAL_ADVICE, AdviceRiskLevel.CRITICAL
        
        # Clear legal advice
        if advice_score >= 3.0 or net_score >= 2.0:
            return ContentClassification.LEGAL_ADVICE, AdviceRiskLevel.HIGH
        
        # Borderline (needs review)
        if advice_score >= 1.5 or (net_score >= 0.5 and advice_score > 0):
            return ContentClassification.BORDERLINE, AdviceRiskLevel.MEDIUM
        
        # Procedural guidance (permissible if well-crafted)
        if info_score >= 2.0 and advice_score < 1.0:
            return ContentClassification.PROCEDURAL_GUIDANCE, AdviceRiskLevel.LOW
        
        # Educational content (generally permissible)
        if info_score >= 1.0 and net_score <= -1.0:
            return ContentClassification.EDUCATIONAL_CONTENT, AdviceRiskLevel.LOW
        
        # Default to legal information with low risk
        return ContentClassification.LEGAL_INFORMATION, AdviceRiskLevel.LOW
    
    def _identify_problematic_phrases(self, content: str) -> List[str]:
        """Identify specific problematic phrases in content"""
        problematic = []
        
        # Check for direct advice patterns
        direct_advice_patterns = [
            r"you should [^.]*",
            r"you must [^.]*", 
            r"i recommend [^.]*",
            r"i advise [^.]*",
            r"your best option is [^.]*",
            r"you need to [^.]*"
        ]
        
        for pattern in direct_advice_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            problematic.extend(matches)
        
        return problematic[:10]  # Limit to first 10 matches
    
    def _generate_corrections(self, content: str, problematic_phrases: List[str]) -> List[Dict[str, str]]:
        """Generate suggested corrections for problematic phrases"""
        corrections = []
        
        for template in self.correction_templates:
            if re.search(template["problem"], content, re.IGNORECASE):
                corrections.append({
                    "original": template["problem"],
                    "suggested": template["correction"],
                    "explanation": template["explanation"],
                    "example": self._generate_correction_example(content, template)
                })
        
        return corrections[:5]  # Limit to 5 suggestions
    
    def _generate_correction_example(self, content: str, template: Dict[str, str]) -> str:
        """Generate a specific correction example"""
        # Find the first sentence containing the problematic pattern
        sentences = re.split(r'[.!?]+', content)
        for sentence in sentences:
            if re.search(template["problem"], sentence, re.IGNORECASE):
                corrected = re.sub(
                    template["problem"], 
                    template["correction"], 
                    sentence, 
                    flags=re.IGNORECASE
                )
                return f"Original: '{sentence.strip()}' → Suggested: '{corrected.strip()}'"
        
        return ""
    
    def _generate_explanation(
        self, 
        classification: ContentClassification,
        advice_matches: List[Dict],
        info_matches: List[Dict],
        net_score: float
    ) -> str:
        """Generate explanation for the classification"""
        
        explanations = []
        
        if classification == ContentClassification.LEGAL_ADVICE:
            explanations.append(
                f"Content classified as LEGAL ADVICE due to {len(advice_matches)} advice indicators. "
                "This crosses the line from permissible legal information to impermissible legal advice."
            )
        elif classification == ContentClassification.BORDERLINE:
            explanations.append(
                "Content contains language that may constitute legal advice. "
                "Attorney review required to ensure compliance with ethical rules."
            )
        else:
            explanations.append(
                f"Content classified as {classification.value.replace('_', ' ').title()}. "
                "Language appears to provide general legal information rather than specific advice."
            )
        
        if advice_matches:
            advice_categories = set(match["category"] for match in advice_matches)
            explanations.append(
                f"Advice indicators found in categories: {', '.join(advice_categories)}"
            )
        
        if info_matches:
            info_categories = set(match["category"] for match in info_matches)
            explanations.append(
                f"Information indicators found in categories: {', '.join(info_categories)}"
            )
        
        explanations.append(f"Analysis score: {net_score:.1f} (positive = advice tendency)")
        
        return " ".join(explanations)
    
    def _store_analysis(self, content: str, analysis: AdviceAnalysis):
        """Store analysis results in database"""
        import hashlib
        import secrets
        import json
        
        analysis_id = secrets.token_hex(16)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO advice_detection_results (
                    analysis_id, content_hash, analyzed_at, classification,
                    risk_level, confidence_score, advice_indicators,
                    information_indicators, problematic_phrases,
                    suggested_corrections, requires_review, explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis_id, content_hash, datetime.now().isoformat(),
                analysis.classification.value, analysis.risk_level.value,
                analysis.confidence_score, json.dumps(analysis.advice_indicators),
                json.dumps(analysis.information_indicators), 
                json.dumps(analysis.problematic_phrases),
                json.dumps(analysis.suggested_corrections),
                analysis.requires_attorney_review, analysis.explanation
            ))
            
            conn.commit()
        finally:
            conn.close()
    
    def validate_content_compliance(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate content for legal advice compliance and return actionable results"""
        
        analysis = self.analyze_content(content, context)
        
        # Generate compliance report
        compliance_report = {
            "is_compliant": analysis.classification not in [
                ContentClassification.LEGAL_ADVICE
            ] and analysis.risk_level not in [
                AdviceRiskLevel.CRITICAL, AdviceRiskLevel.HIGH
            ],
            
            "classification": analysis.classification.value,
            "risk_level": analysis.risk_level.value,
            "confidence": analysis.confidence_score,
            
            "issues_found": len(analysis.advice_indicators) > 0,
            "critical_issues": analysis.risk_level in [AdviceRiskLevel.CRITICAL, AdviceRiskLevel.HIGH],
            
            "recommendations": self._generate_compliance_recommendations(analysis),
            
            "required_actions": self._generate_required_actions(analysis),
            
            "analysis_summary": analysis.explanation
        }
        
        return compliance_report
    
    def _generate_compliance_recommendations(self, analysis: AdviceAnalysis) -> List[str]:
        """Generate compliance recommendations based on analysis"""
        recommendations = []
        
        if analysis.classification == ContentClassification.LEGAL_ADVICE:
            recommendations.extend([
                "CRITICAL: Content provides legal advice and must be reviewed by supervising attorney",
                "Consider rephrasing to provide general legal information rather than specific advice",
                "Add disclaimers clarifying this is information, not advice",
                "Remove client-specific recommendations and imperatives"
            ])
        
        if analysis.risk_level == AdviceRiskLevel.HIGH:
            recommendations.extend([
                "HIGH RISK: Attorney review required before publication",
                "Revise language to be more informational and less directive"
            ])
        
        if analysis.problematic_phrases:
            recommendations.append(
                f"Address {len(analysis.problematic_phrases)} problematic phrases identified"
            )
        
        if analysis.suggested_corrections:
            recommendations.append(
                f"Apply {len(analysis.suggested_corrections)} suggested corrections"
            )
        
        return recommendations
    
    def _generate_required_actions(self, analysis: AdviceAnalysis) -> List[str]:
        """Generate required actions based on analysis"""
        actions = []
        
        if analysis.classification == ContentClassification.LEGAL_ADVICE:
            actions.extend([
                "MANDATORY: Supervising attorney review required",
                "MANDATORY: Content cannot be published without approval",
                "MANDATORY: Apply all suggested corrections"
            ])
        
        if analysis.requires_attorney_review:
            actions.append("Attorney review required before use")
        
        if analysis.risk_level in [AdviceRiskLevel.HIGH, AdviceRiskLevel.CRITICAL]:
            actions.append("Content revision required to reduce legal advice risk")
        
        return actions

# Global legal advice detector instance
legal_advice_detector = LegalAdviceDetector()