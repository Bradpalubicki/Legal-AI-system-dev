"""
Advanced priority classification system for legal deadlines.
Uses machine learning and rule-based approaches to accurately prioritize deadlines.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import re
from collections import defaultdict

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

from .deadline_extractor import ExtractedDeadline, DeadlineType, PriorityLevel, DeadlineStatus, ConfidenceLevel

logger = logging.getLogger(__name__)


class UrgencyFactor(Enum):
    """Factors that affect deadline urgency."""
    JURISDICTIONAL = "jurisdictional"        # Cannot be waived or extended
    STATUTORY = "statutory"                  # Set by statute
    CASE_ENDING = "case_ending"             # Could end the case
    FINANCIAL_IMPACT = "financial_impact"    # High financial consequences
    CLIENT_CRITICAL = "client_critical"      # Critical to client's business
    PRECEDENTIAL = "precedential"            # Sets important precedent
    MEDIA_ATTENTION = "media_attention"      # High-profile case
    REGULATORY = "regulatory"                # Regulatory compliance
    TIME_SENSITIVE = "time_sensitive"        # Time-sensitive business matter
    DISCOVERY_DEPENDENT = "discovery_dependent"  # Blocks other discovery


class ImpactLevel(Enum):
    """Impact levels for missed deadlines."""
    CATASTROPHIC = "catastrophic"    # Case dismissal, default judgment
    SEVERE = "severe"               # Significant legal disadvantage
    MODERATE = "moderate"           # Some legal disadvantage
    MINOR = "minor"                 # Minimal impact
    NEGLIGIBLE = "negligible"       # No significant impact


class ClassificationMethod(Enum):
    """Methods used for priority classification."""
    RULE_BASED = "rule_based"
    ML_ENSEMBLE = "ml_ensemble"
    TEXT_ANALYSIS = "text_analysis"
    HYBRID = "hybrid"
    MANUAL_OVERRIDE = "manual_override"


@dataclass
class PriorityFeatures:
    """Features used for priority classification."""
    # Temporal features
    days_until_deadline: int
    business_days_until: int
    is_weekend_deadline: bool
    is_holiday_period: bool
    
    # Legal context features
    deadline_type_encoded: int
    is_jurisdictional: bool
    is_statutory: bool
    has_rule_reference: bool
    court_level: int  # 1=district, 2=appellate, 3=supreme
    
    # Document features
    text_length: int
    legal_term_count: int
    urgency_word_count: int
    modal_verb_count: int  # must, shall, etc.
    
    # Case context features
    case_value_category: int  # 1=low, 2=medium, 3=high, 4=very_high
    client_importance: int   # 1=low, 2=medium, 3=high
    opposing_counsel_reputation: int
    case_complexity: int
    
    # Historical features
    extension_history: int
    missed_deadline_history: int
    case_age_months: int
    
    # Consequence features
    potential_impact_score: float
    financial_exposure: float
    strategic_importance: float


@dataclass
class ClassificationResult:
    """Result of priority classification."""
    original_priority: PriorityLevel
    predicted_priority: PriorityLevel
    confidence_score: float
    classification_method: ClassificationMethod
    
    # Supporting analysis
    key_factors: List[str]
    urgency_factors: List[UrgencyFactor]
    impact_assessment: ImpactLevel
    risk_score: float
    
    # Feature importance
    most_important_features: List[Tuple[str, float]]
    
    # Recommendations
    priority_justification: str
    recommended_actions: List[str]
    escalation_triggers: List[str]
    
    # Metadata
    classification_timestamp: datetime = field(default_factory=datetime.utcnow)
    model_version: str = "1.0"
    
    def should_escalate(self) -> bool:
        """Determine if deadline should be escalated."""
        return (self.predicted_priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH] or
                self.impact_assessment == ImpactLevel.CATASTROPHIC or
                self.risk_score > 0.8)


@dataclass
class PriorityModel:
    """Priority classification model container."""
    model_id: str
    model_type: str
    trained_model: Any
    feature_scaler: Optional[StandardScaler]
    text_vectorizer: Optional[TfidfVectorizer]
    
    # Model metadata
    training_date: datetime
    training_samples: int
    accuracy_score: float
    feature_names: List[str]
    
    # Performance metrics
    precision_by_class: Dict[str, float] = field(default_factory=dict)
    recall_by_class: Dict[str, float] = field(default_factory=dict)
    f1_by_class: Dict[str, float] = field(default_factory=dict)


class PriorityClassifier:
    """Advanced priority classification system for legal deadlines."""
    
    def __init__(self):
        """Initialize priority classifier."""
        
        # Classification models
        self.models: Dict[str, PriorityModel] = {}
        
        # Rule-based classification rules
        self._initialize_priority_rules()
        
        # Feature extraction components
        self._initialize_feature_extractors()
        
        # Impact assessment frameworks
        self._initialize_impact_frameworks()
        
        # Training data storage
        self.training_data: List[Dict[str, Any]] = []
        
        # Classification cache
        self.classification_cache: Dict[str, ClassificationResult] = {}
    
    def _initialize_priority_rules(self):
        """Initialize rule-based priority classification rules."""
        
        # Critical priority rules (highest priority)
        self.critical_rules = [
            {
                'name': 'jurisdictional_deadline',
                'pattern': r'\b(?:jurisdictional|statute\s+of\s+limitations|notice\s+of\s+appeal)\b',
                'weight': 1.0,
                'reason': 'Jurisdictional deadlines cannot be waived or extended'
            },
            {
                'name': 'mandatory_dismissal',
                'pattern': r'\b(?:dismissal|default\s+judgment|sanctions)\b',
                'weight': 0.9,
                'reason': 'Risk of case dismissal or default judgment'
            },
            {
                'name': 'constitutional_rights',
                'pattern': r'\b(?:habeas\s+corpus|constitutional|miranda|sixth\s+amendment)\b',
                'weight': 0.95,
                'reason': 'Constitutional rights at stake'
            },
            {
                'name': 'criminal_sentencing',
                'pattern': r'\b(?:sentencing|imprisonment|custody|detention)\b',
                'weight': 0.9,
                'reason': 'Liberty interests involved'
            }
        ]
        
        # High priority rules
        self.high_rules = [
            {
                'name': 'dispositive_motion',
                'pattern': r'\b(?:summary\s+judgment|motion\s+to\s+dismiss|judgment\s+on\s+pleadings)\b',
                'weight': 0.8,
                'reason': 'Dispositive motion could end case'
            },
            {
                'name': 'preliminary_injunction',
                'pattern': r'\b(?:preliminary\s+injunction|temporary\s+restraining\s+order|emergency\s+relief)\b',
                'weight': 0.85,
                'reason': 'Emergency relief requested'
            },
            {
                'name': 'discovery_cutoff',
                'pattern': r'\b(?:discovery\s+(?:deadline|cutoff)|close\s+of\s+discovery)\b',
                'weight': 0.7,
                'reason': 'Discovery deadline blocks further fact-finding'
            },
            {
                'name': 'trial_preparation',
                'pattern': r'\b(?:trial\s+(?:date|preparation)|jury\s+selection|witness\s+list)\b',
                'weight': 0.75,
                'reason': 'Trial preparation deadline'
            }
        ]
        
        # Medium priority rules
        self.medium_rules = [
            {
                'name': 'discovery_response',
                'pattern': r'\b(?:interrogatories|document\s+production|deposition\s+notice)\b',
                'weight': 0.6,
                'reason': 'Discovery response required'
            },
            {
                'name': 'scheduling_order',
                'pattern': r'\b(?:scheduling\s+order|case\s+management|status\s+conference)\b',
                'weight': 0.5,
                'reason': 'Administrative scheduling requirement'
            },
            {
                'name': 'expert_disclosure',
                'pattern': r'\b(?:expert\s+(?:witness|disclosure|report))\b',
                'weight': 0.65,
                'reason': 'Expert witness deadline'
            }
        ]
        
        # Urgency multipliers
        self.urgency_multipliers = [
            {
                'name': 'immediate',
                'pattern': r'\b(?:immediate|urgent|emergency|asap|forthwith)\b',
                'multiplier': 1.3
            },
            {
                'name': 'extended_deadline',
                'pattern': r'\b(?:extended|continued|postponed)\b',
                'multiplier': 0.8
            },
            {
                'name': 'final_deadline',
                'pattern': r'\b(?:final|last|ultimate|absolute)\b',
                'multiplier': 1.2
            }
        ]
    
    def _initialize_feature_extractors(self):
        """Initialize feature extraction components."""
        
        # Text analysis for legal urgency
        self.urgency_keywords = {
            'critical': ['immediate', 'urgent', 'emergency', 'critical', 'asap', 'forthwith', 'expedited'],
            'high': ['important', 'significant', 'material', 'substantial', 'major'],
            'legal_imperatives': ['must', 'shall', 'required', 'mandatory', 'obligated', 'compelled'],
            'consequences': ['sanctions', 'dismissal', 'default', 'waiver', 'forfeiture', 'penalty']
        }
        
        # Court hierarchy scoring
        self.court_hierarchy = {
            'supreme_court': 5,
            'appellate_court': 4,
            'federal_district': 3,
            'state_superior': 2,
            'municipal': 1
        }
        
        # Case value categories
        self.case_value_thresholds = {
            'very_high': 10_000_000,
            'high': 1_000_000,
            'medium': 100_000,
            'low': 0
        }
    
    def _initialize_impact_frameworks(self):
        """Initialize impact assessment frameworks."""
        
        # Impact by deadline type
        self.deadline_impact_map = {
            DeadlineType.STATUTE_OF_LIMITATIONS: ImpactLevel.CATASTROPHIC,
            DeadlineType.APPEAL: ImpactLevel.CATASTROPHIC,
            DeadlineType.RESPONSE: ImpactLevel.SEVERE,
            DeadlineType.MOTION: ImpactLevel.MODERATE,
            DeadlineType.DISCOVERY: ImpactLevel.MODERATE,
            DeadlineType.HEARING: ImpactLevel.MINOR,
            DeadlineType.PAYMENT: ImpactLevel.MODERATE,
            DeadlineType.COMPLIANCE: ImpactLevel.SEVERE,
            DeadlineType.ADMINISTRATIVE: ImpactLevel.MINOR
        }
        
        # Consequence severity scoring
        self.consequence_scores = {
            'case_dismissal': 1.0,
            'default_judgment': 1.0,
            'sanctions': 0.8,
            'waiver_of_rights': 0.9,
            'loss_of_evidence': 0.7,
            'procedural_disadvantage': 0.5,
            'delay': 0.3,
            'administrative_burden': 0.1
        }
    
    def classify_priority(self, deadline: ExtractedDeadline, 
                         context: Dict[str, Any] = None) -> ClassificationResult:
        """Classify priority of a legal deadline.
        
        Args:
            deadline: Extracted deadline to classify
            context: Additional context about case, client, etc.
            
        Returns:
            Classification result with priority and analysis
        """
        logger.info(f"Classifying priority for deadline: {deadline.deadline_id}")
        
        context = context or {}
        
        # Check cache first
        cache_key = f"{deadline.deadline_id}_{hash(str(context))}"
        if cache_key in self.classification_cache:
            return self.classification_cache[cache_key]
        
        # Extract features
        features = self._extract_features(deadline, context)
        
        # Apply rule-based classification
        rule_result = self._classify_with_rules(deadline, context)
        
        # Apply ML classification if model is available
        ml_result = None
        if self.models:
            ml_result = self._classify_with_ml(features)
        
        # Combine results
        final_result = self._combine_classifications(
            deadline, rule_result, ml_result, features, context
        )
        
        # Cache result
        self.classification_cache[cache_key] = final_result
        
        return final_result
    
    def _extract_features(self, deadline: ExtractedDeadline, 
                         context: Dict[str, Any]) -> PriorityFeatures:
        """Extract features for ML classification."""
        
        # Temporal features
        now = datetime.utcnow()
        days_until = (deadline.date - now).days
        business_days = self._count_business_days(now, deadline.date)
        
        # Text analysis features
        text = f"{deadline.description} {deadline.context} {deadline.action_required}"
        text_features = self._analyze_text_features(text)
        
        # Legal context features
        legal_features = self._extract_legal_features(deadline, context)
        
        # Case context features
        case_features = self._extract_case_features(context)
        
        return PriorityFeatures(
            days_until_deadline=max(0, days_until),
            business_days_until=max(0, business_days),
            is_weekend_deadline=deadline.date.weekday() >= 5,
            is_holiday_period=self._is_holiday_period(deadline.date),
            
            deadline_type_encoded=list(DeadlineType).index(deadline.deadline_type),
            is_jurisdictional=self._is_jurisdictional(deadline),
            is_statutory=bool(deadline.rule_or_statute),
            has_rule_reference=bool(deadline.rule_or_statute),
            court_level=self._get_court_level(deadline.court),
            
            text_length=len(text),
            legal_term_count=text_features['legal_terms'],
            urgency_word_count=text_features['urgency_words'],
            modal_verb_count=text_features['modal_verbs'],
            
            case_value_category=case_features['value_category'],
            client_importance=case_features['importance'],
            opposing_counsel_reputation=case_features['opposing_reputation'],
            case_complexity=case_features['complexity'],
            
            extension_history=context.get('extension_count', 0),
            missed_deadline_history=context.get('missed_deadlines', 0),
            case_age_months=case_features['age_months'],
            
            potential_impact_score=self._calculate_impact_score(deadline, context),
            financial_exposure=case_features['financial_exposure'],
            strategic_importance=case_features['strategic_importance']
        )
    
    def _count_business_days(self, start_date: datetime, end_date: datetime) -> int:
        """Count business days between two dates."""
        days = 0
        current = start_date.date()
        end = end_date.date()
        
        while current < end:
            if current.weekday() < 5:  # Monday = 0, Friday = 4
                days += 1
            current += timedelta(days=1)
        
        return days
    
    def _is_holiday_period(self, date: datetime) -> bool:
        """Check if date falls in holiday period."""
        # Simplified holiday check
        month_day = (date.month, date.day)
        
        holidays = [
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day
            (11, 11), # Veterans Day
            (12, 25), # Christmas
        ]
        
        # Holiday periods (month ranges)
        holiday_periods = [
            ((11, 22), (11, 30)),  # Thanksgiving week
            ((12, 20), (1, 5)),    # Christmas/New Year period
        ]
        
        if month_day in holidays:
            return True
        
        for (start_month, start_day), (end_month, end_day) in holiday_periods:
            if ((date.month == start_month and date.day >= start_day) or 
                (date.month == end_month and date.day <= end_day) or
                (start_month < date.month < end_month)):
                return True
        
        return False
    
    def _is_jurisdictional(self, deadline: ExtractedDeadline) -> bool:
        """Determine if deadline is jurisdictional."""
        
        jurisdictional_types = [
            DeadlineType.STATUTE_OF_LIMITATIONS,
            DeadlineType.APPEAL
        ]
        
        if deadline.deadline_type in jurisdictional_types:
            return True
        
        # Check for jurisdictional keywords
        text = f"{deadline.description} {deadline.context}".lower()
        jurisdictional_keywords = [
            'jurisdictional', 'statute of limitations', 'notice of appeal',
            'habeas corpus', 'cannot be waived', 'cannot be extended'
        ]
        
        return any(keyword in text for keyword in jurisdictional_keywords)
    
    def _analyze_text_features(self, text: str) -> Dict[str, int]:
        """Analyze text for priority-related features."""
        
        text_lower = text.lower()
        
        # Count legal terms
        legal_terms = ['court', 'judge', 'motion', 'brief', 'hearing', 'trial', 
                      'discovery', 'deposition', 'evidence', 'witness']
        legal_count = sum(text_lower.count(term) for term in legal_terms)
        
        # Count urgency words
        urgency_count = sum(text_lower.count(word) for word in self.urgency_keywords['critical'])
        
        # Count modal verbs (indicating requirements)
        modals = ['must', 'shall', 'should', 'may', 'will', 'required', 'mandatory']
        modal_count = sum(text_lower.count(modal) for modal in modals)
        
        return {
            'legal_terms': legal_count,
            'urgency_words': urgency_count,
            'modal_verbs': modal_count
        }
    
    def _extract_legal_features(self, deadline: ExtractedDeadline, 
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract legal context features."""
        
        features = {}
        
        # Court level
        court_text = (deadline.court or '').lower()
        if 'supreme' in court_text:
            features['court_level'] = 5
        elif 'appellate' or 'appeal' in court_text:
            features['court_level'] = 4
        elif 'district' in court_text or 'federal' in court_text:
            features['court_level'] = 3
        elif 'superior' in court_text:
            features['court_level'] = 2
        else:
            features['court_level'] = 1
        
        return features
    
    def _extract_case_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract case context features."""
        
        # Case value categorization
        case_value = context.get('case_value', 0)
        if case_value >= self.case_value_thresholds['very_high']:
            value_category = 4
        elif case_value >= self.case_value_thresholds['high']:
            value_category = 3
        elif case_value >= self.case_value_thresholds['medium']:
            value_category = 2
        else:
            value_category = 1
        
        # Client importance (1-3 scale)
        client_importance = min(3, max(1, context.get('client_importance', 2)))
        
        # Case complexity (1-5 scale)
        complexity_indicators = context.get('complexity_indicators', [])
        complexity = min(5, max(1, len(complexity_indicators) + 1))
        
        # Case age
        filing_date = context.get('case_filing_date')
        if filing_date:
            if isinstance(filing_date, str):
                filing_date = datetime.fromisoformat(filing_date.replace('Z', '+00:00'))
            age_months = (datetime.utcnow() - filing_date).days // 30
        else:
            age_months = 0
        
        return {
            'value_category': value_category,
            'importance': client_importance,
            'opposing_reputation': context.get('opposing_counsel_rating', 3),
            'complexity': complexity,
            'age_months': age_months,
            'financial_exposure': float(context.get('financial_exposure', case_value)),
            'strategic_importance': context.get('strategic_importance', 0.5)
        }
    
    def _get_court_level(self, court: Optional[str]) -> int:
        """Get numeric court level."""
        if not court:
            return 1
        
        court_lower = court.lower()
        for court_type, level in self.court_hierarchy.items():
            if court_type.replace('_', ' ') in court_lower:
                return level
        
        return 1
    
    def _calculate_impact_score(self, deadline: ExtractedDeadline, 
                               context: Dict[str, Any]) -> float:
        """Calculate potential impact score for missing deadline."""
        
        base_impact = self.deadline_impact_map.get(deadline.deadline_type, ImpactLevel.MINOR)
        impact_scores = {
            ImpactLevel.CATASTROPHIC: 1.0,
            ImpactLevel.SEVERE: 0.8,
            ImpactLevel.MODERATE: 0.6,
            ImpactLevel.MINOR: 0.4,
            ImpactLevel.NEGLIGIBLE: 0.2
        }
        
        score = impact_scores[base_impact]
        
        # Adjust based on case characteristics
        case_value = context.get('case_value', 0)
        if case_value > 1_000_000:
            score *= 1.2
        elif case_value > 100_000:
            score *= 1.1
        
        # Adjust for client importance
        client_importance = context.get('client_importance', 2)
        score *= (0.8 + client_importance * 0.2)
        
        return min(1.0, score)
    
    def _classify_with_rules(self, deadline: ExtractedDeadline, 
                            context: Dict[str, Any]) -> Tuple[PriorityLevel, float, List[str]]:
        """Classify priority using rule-based approach."""
        
        text = f"{deadline.description} {deadline.context} {deadline.action_required}".lower()
        
        # Check critical rules first
        for rule in self.critical_rules:
            if re.search(rule['pattern'], text, re.IGNORECASE):
                return PriorityLevel.CRITICAL, rule['weight'], [rule['reason']]
        
        # Check high priority rules
        high_reasons = []
        high_score = 0.0
        for rule in self.high_rules:
            if re.search(rule['pattern'], text, re.IGNORECASE):
                high_score = max(high_score, rule['weight'])
                high_reasons.append(rule['reason'])
        
        if high_score > 0.7:
            return PriorityLevel.HIGH, high_score, high_reasons
        
        # Check medium priority rules
        medium_reasons = []
        medium_score = 0.0
        for rule in self.medium_rules:
            if re.search(rule['pattern'], text, re.IGNORECASE):
                medium_score = max(medium_score, rule['weight'])
                medium_reasons.append(rule['reason'])
        
        if medium_score > 0.5:
            return PriorityLevel.MEDIUM, medium_score, medium_reasons
        
        # Apply urgency multipliers
        multiplier = 1.0
        for urgency_rule in self.urgency_multipliers:
            if re.search(urgency_rule['pattern'], text, re.IGNORECASE):
                multiplier *= urgency_rule['multiplier']
        
        # Time-based priority adjustment
        days_until = (deadline.date - datetime.utcnow()).days
        if days_until <= 1:
            return PriorityLevel.CRITICAL, 0.9, ['Less than 24 hours until deadline']
        elif days_until <= 3:
            return PriorityLevel.HIGH, 0.8, ['Less than 3 days until deadline']
        elif days_until <= 7:
            return PriorityLevel.MEDIUM, 0.6, ['Less than 1 week until deadline']
        else:
            return PriorityLevel.LOW, 0.4, ['Standard timeline']
    
    def _classify_with_ml(self, features: PriorityFeatures) -> Optional[Tuple[PriorityLevel, float]]:
        """Classify priority using ML models."""
        
        if not self.models:
            return None
        
        # Use the most recent model
        model_id = max(self.models.keys())
        model = self.models[model_id]
        
        try:
            # Convert features to array
            feature_array = self._features_to_array(features)
            
            # Scale features if scaler is available
            if model.feature_scaler:
                feature_array = model.feature_scaler.transform([feature_array])
            else:
                feature_array = [feature_array]
            
            # Make prediction
            prediction = model.trained_model.predict(feature_array)[0]
            confidence = max(model.trained_model.predict_proba(feature_array)[0])
            
            # Convert prediction to PriorityLevel
            priority_levels = [PriorityLevel.LOW, PriorityLevel.MEDIUM, 
                              PriorityLevel.HIGH, PriorityLevel.CRITICAL]
            predicted_priority = priority_levels[int(prediction)]
            
            return predicted_priority, confidence
            
        except Exception as e:
            logger.warning(f"ML classification failed: {e}")
            return None
    
    def _features_to_array(self, features: PriorityFeatures) -> List[float]:
        """Convert PriorityFeatures to numeric array."""
        
        return [
            float(features.days_until_deadline),
            float(features.business_days_until),
            float(features.is_weekend_deadline),
            float(features.is_holiday_period),
            float(features.deadline_type_encoded),
            float(features.is_jurisdictional),
            float(features.is_statutory),
            float(features.has_rule_reference),
            float(features.court_level),
            float(features.text_length),
            float(features.legal_term_count),
            float(features.urgency_word_count),
            float(features.modal_verb_count),
            float(features.case_value_category),
            float(features.client_importance),
            float(features.opposing_counsel_reputation),
            float(features.case_complexity),
            float(features.extension_history),
            float(features.missed_deadline_history),
            float(features.case_age_months),
            features.potential_impact_score,
            features.financial_exposure,
            features.strategic_importance
        ]
    
    def _combine_classifications(self, deadline: ExtractedDeadline,
                                rule_result: Tuple[PriorityLevel, float, List[str]],
                                ml_result: Optional[Tuple[PriorityLevel, float]],
                                features: PriorityFeatures,
                                context: Dict[str, Any]) -> ClassificationResult:
        """Combine rule-based and ML classification results."""
        
        rule_priority, rule_confidence, rule_reasons = rule_result
        
        # If no ML result, use rule-based
        if not ml_result:
            final_priority = rule_priority
            final_confidence = rule_confidence
            method = ClassificationMethod.RULE_BASED
        else:
            ml_priority, ml_confidence = ml_result
            
            # Weight the results (rules get higher weight for critical classifications)
            if rule_priority == PriorityLevel.CRITICAL:
                final_priority = rule_priority
                final_confidence = max(rule_confidence, ml_confidence)
                method = ClassificationMethod.RULE_BASED
            elif ml_confidence > 0.8:
                final_priority = ml_priority
                final_confidence = ml_confidence
                method = ClassificationMethod.ML_ENSEMBLE
            else:
                # Average the priorities (convert to numeric, average, convert back)
                priority_values = {
                    PriorityLevel.LOW: 1,
                    PriorityLevel.MEDIUM: 2,
                    PriorityLevel.HIGH: 3,
                    PriorityLevel.CRITICAL: 4
                }
                
                rule_value = priority_values[rule_priority]
                ml_value = priority_values[ml_priority]
                avg_value = (rule_value + ml_value) / 2
                
                # Convert back to priority level
                if avg_value >= 3.5:
                    final_priority = PriorityLevel.CRITICAL
                elif avg_value >= 2.5:
                    final_priority = PriorityLevel.HIGH
                elif avg_value >= 1.5:
                    final_priority = PriorityLevel.MEDIUM
                else:
                    final_priority = PriorityLevel.LOW
                
                final_confidence = (rule_confidence + ml_confidence) / 2
                method = ClassificationMethod.HYBRID
        
        # Assess impact
        impact_assessment = self.deadline_impact_map.get(
            deadline.deadline_type, ImpactLevel.MINOR
        )
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(final_priority, features, impact_assessment)
        
        # Identify urgency factors
        urgency_factors = self._identify_urgency_factors(deadline, features, context)
        
        # Generate recommendations
        recommended_actions = self._generate_priority_recommendations(
            final_priority, urgency_factors, features
        )
        
        return ClassificationResult(
            original_priority=deadline.priority,
            predicted_priority=final_priority,
            confidence_score=final_confidence,
            classification_method=method,
            key_factors=rule_reasons,
            urgency_factors=urgency_factors,
            impact_assessment=impact_assessment,
            risk_score=risk_score,
            most_important_features=self._get_feature_importance(features),
            priority_justification=self._generate_justification(
                final_priority, rule_reasons, features
            ),
            recommended_actions=recommended_actions,
            escalation_triggers=self._generate_escalation_triggers(
                final_priority, urgency_factors
            )
        )
    
    def _calculate_risk_score(self, priority: PriorityLevel, 
                             features: PriorityFeatures,
                             impact: ImpactLevel) -> float:
        """Calculate overall risk score."""
        
        # Base risk from priority
        priority_risk = {
            PriorityLevel.CRITICAL: 0.9,
            PriorityLevel.HIGH: 0.7,
            PriorityLevel.MEDIUM: 0.5,
            PriorityLevel.LOW: 0.3
        }[priority]
        
        # Impact risk
        impact_risk = {
            ImpactLevel.CATASTROPHIC: 1.0,
            ImpactLevel.SEVERE: 0.8,
            ImpactLevel.MODERATE: 0.6,
            ImpactLevel.MINOR: 0.4,
            ImpactLevel.NEGLIGIBLE: 0.2
        }[impact]
        
        # Time pressure risk
        time_risk = max(0, (7 - features.days_until_deadline) / 7)
        
        # Combine risks
        combined_risk = (priority_risk * 0.4 + impact_risk * 0.4 + time_risk * 0.2)
        
        return min(1.0, combined_risk)
    
    def _identify_urgency_factors(self, deadline: ExtractedDeadline,
                                 features: PriorityFeatures,
                                 context: Dict[str, Any]) -> List[UrgencyFactor]:
        """Identify specific urgency factors."""
        
        factors = []
        
        if features.is_jurisdictional:
            factors.append(UrgencyFactor.JURISDICTIONAL)
        
        if features.is_statutory:
            factors.append(UrgencyFactor.STATUTORY)
        
        if deadline.deadline_type in [DeadlineType.RESPONSE, DeadlineType.MOTION]:
            factors.append(UrgencyFactor.CASE_ENDING)
        
        if features.financial_exposure > 1_000_000:
            factors.append(UrgencyFactor.FINANCIAL_IMPACT)
        
        if features.client_importance >= 3:
            factors.append(UrgencyFactor.CLIENT_CRITICAL)
        
        if context.get('regulatory_matter', False):
            factors.append(UrgencyFactor.REGULATORY)
        
        if context.get('media_attention', False):
            factors.append(UrgencyFactor.MEDIA_ATTENTION)
        
        if deadline.deadline_type == DeadlineType.DISCOVERY:
            factors.append(UrgencyFactor.DISCOVERY_DEPENDENT)
        
        return factors
    
    def _get_feature_importance(self, features: PriorityFeatures) -> List[Tuple[str, float]]:
        """Get most important features for classification."""
        
        # Simplified feature importance based on values
        feature_scores = [
            ('days_until_deadline', 1.0 / max(1, features.days_until_deadline)),
            ('is_jurisdictional', 0.9 if features.is_jurisdictional else 0),
            ('potential_impact_score', features.potential_impact_score),
            ('court_level', features.court_level / 5.0),
            ('urgency_word_count', min(1.0, features.urgency_word_count / 5.0)),
            ('financial_exposure', min(1.0, features.financial_exposure / 10_000_000)),
            ('case_value_category', features.case_value_category / 4.0)
        ]
        
        # Sort by importance score
        feature_scores.sort(key=lambda x: x[1], reverse=True)
        
        return feature_scores[:5]  # Top 5 features
    
    def _generate_justification(self, priority: PriorityLevel, 
                               reasons: List[str],
                               features: PriorityFeatures) -> str:
        """Generate justification for priority classification."""
        
        justification_parts = []
        
        # Priority level justification
        if priority == PriorityLevel.CRITICAL:
            justification_parts.append("CRITICAL priority due to potential case-ending consequences")
        elif priority == PriorityLevel.HIGH:
            justification_parts.append("HIGH priority due to significant legal implications")
        elif priority == PriorityLevel.MEDIUM:
            justification_parts.append("MEDIUM priority with standard legal requirements")
        else:
            justification_parts.append("LOW priority with minimal immediate impact")
        
        # Add specific reasons
        if reasons:
            justification_parts.append(f"Key factors: {', '.join(reasons[:3])}")
        
        # Add timing consideration
        if features.days_until_deadline <= 3:
            justification_parts.append(f"Urgent timing: {features.days_until_deadline} days remaining")
        
        # Add jurisdictional consideration
        if features.is_jurisdictional:
            justification_parts.append("Jurisdictional deadline - cannot be waived or extended")
        
        return ". ".join(justification_parts) + "."
    
    def _generate_priority_recommendations(self, priority: PriorityLevel,
                                         urgency_factors: List[UrgencyFactor],
                                         features: PriorityFeatures) -> List[str]:
        """Generate recommendations based on priority classification."""
        
        recommendations = []
        
        if priority == PriorityLevel.CRITICAL:
            recommendations.extend([
                "Assign to senior attorney immediately",
                "Clear schedule and prioritize this deadline",
                "Implement daily progress monitoring",
                "Prepare contingency plans for any delays",
                "Consider seeking extension if grounds exist"
            ])
        elif priority == PriorityLevel.HIGH:
            recommendations.extend([
                "Assign to experienced attorney",
                "Begin work within 24 hours",
                "Schedule progress check-ins",
                "Ensure adequate resources allocated"
            ])
        elif priority == PriorityLevel.MEDIUM:
            recommendations.extend([
                "Schedule work within reasonable timeframe",
                "Assign appropriate attorney based on complexity",
                "Monitor progress regularly"
            ])
        else:
            recommendations.extend([
                "Include in regular workflow",
                "Assign based on attorney availability"
            ])
        
        # Add urgency-specific recommendations
        if UrgencyFactor.JURISDICTIONAL in urgency_factors:
            recommendations.append("Verify jurisdictional requirements - no extensions possible")
        
        if UrgencyFactor.FINANCIAL_IMPACT in urgency_factors:
            recommendations.append("Consult with client on financial implications")
        
        if features.days_until_deadline <= 1:
            recommendations.append("Immediate action required - deadline within 24 hours")
        
        return recommendations
    
    def _generate_escalation_triggers(self, priority: PriorityLevel,
                                    urgency_factors: List[UrgencyFactor]) -> List[str]:
        """Generate escalation triggers."""
        
        triggers = []
        
        if priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
            triggers.extend([
                "Any delay in starting work",
                "Unexpected complications arise",
                "Additional resources needed"
            ])
        
        if UrgencyFactor.JURISDICTIONAL in urgency_factors:
            triggers.append("Any question about jurisdictional requirements")
        
        if UrgencyFactor.CLIENT_CRITICAL in urgency_factors:
            triggers.append("Client expresses concern about deadline")
        
        triggers.append("24 hours before deadline if not completed")
        
        return triggers
    
    def train_model(self, training_data: List[Dict[str, Any]]) -> PriorityModel:
        """Train ML model for priority classification."""
        
        logger.info(f"Training priority classification model with {len(training_data)} samples")
        
        # Prepare features and labels
        X = []
        y = []
        
        for sample in training_data:
            features = sample['features']
            label = sample['priority_label']
            
            X.append(self._features_to_array(features))
            
            # Convert priority to numeric
            priority_to_num = {
                PriorityLevel.LOW: 0,
                PriorityLevel.MEDIUM: 1,
                PriorityLevel.HIGH: 2,
                PriorityLevel.CRITICAL: 3
            }
            y.append(priority_to_num[label])
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train ensemble model
        model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_test_scaled)
        accuracy = (y_pred == y_test).mean()
        
        # Generate classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Create model container
        model_id = f"priority_model_{int(datetime.utcnow().timestamp())}"
        priority_model = PriorityModel(
            model_id=model_id,
            model_type="gradient_boosting",
            trained_model=model,
            feature_scaler=scaler,
            text_vectorizer=None,
            training_date=datetime.utcnow(),
            training_samples=len(training_data),
            accuracy_score=accuracy,
            feature_names=[f"feature_{i}" for i in range(len(X[0]))],
            precision_by_class={str(k): v['precision'] for k, v in report.items() if k.isdigit()},
            recall_by_class={str(k): v['recall'] for k, v in report.items() if k.isdigit()},
            f1_by_class={str(k): v['f1-score'] for k, v in report.items() if k.isdigit()}
        )
        
        # Store model
        self.models[model_id] = priority_model
        
        logger.info(f"Model trained successfully. Accuracy: {accuracy:.3f}")
        
        return priority_model
    
    def save_model(self, model_id: str, filepath: str) -> bool:
        """Save trained model to file."""
        
        if model_id not in self.models:
            return False
        
        try:
            joblib.dump(self.models[model_id], filepath)
            logger.info(f"Model {model_id} saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False
    
    def load_model(self, filepath: str) -> Optional[str]:
        """Load trained model from file."""
        
        try:
            model = joblib.load(filepath)
            model_id = model.model_id
            self.models[model_id] = model
            logger.info(f"Model {model_id} loaded from {filepath}")
            return model_id
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None
    
    def export_classification_results(self, results: List[ClassificationResult], 
                                    format: str = "json") -> str:
        """Export classification results."""
        
        if format.lower() == "json":
            data = []
            for result in results:
                data.append({
                    "original_priority": result.original_priority.value,
                    "predicted_priority": result.predicted_priority.value,
                    "confidence_score": result.confidence_score,
                    "classification_method": result.classification_method.value,
                    "key_factors": result.key_factors,
                    "urgency_factors": [uf.value for uf in result.urgency_factors],
                    "impact_assessment": result.impact_assessment.value,
                    "risk_score": result.risk_score,
                    "priority_justification": result.priority_justification,
                    "recommended_actions": result.recommended_actions,
                    "should_escalate": result.should_escalate(),
                    "classification_timestamp": result.classification_timestamp.isoformat()
                })
            
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_classification_statistics(self) -> Dict[str, Any]:
        """Get classifier statistics."""
        
        model_stats = {}
        for model_id, model in self.models.items():
            model_stats[model_id] = {
                "accuracy": model.accuracy_score,
                "training_samples": model.training_samples,
                "training_date": model.training_date.isoformat()
            }
        
        return {
            "total_models": len(self.models),
            "classification_methods": [cm.value for cm in ClassificationMethod],
            "priority_levels": [pl.value for pl in PriorityLevel],
            "urgency_factors": [uf.value for uf in UrgencyFactor],
            "impact_levels": [il.value for il in ImpactLevel],
            "rule_sets": {
                "critical_rules": len(self.critical_rules),
                "high_rules": len(self.high_rules),
                "medium_rules": len(self.medium_rules),
                "urgency_multipliers": len(self.urgency_multipliers)
            },
            "cache_size": len(self.classification_cache),
            "model_details": model_stats
        }