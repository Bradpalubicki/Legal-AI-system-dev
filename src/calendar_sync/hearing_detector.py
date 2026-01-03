"""
Automatic Hearing Detection System for CourtSync Calendar

Intelligently detects court hearings, depositions, and legal events
from various sources including PACER, ECF, and document analysis.
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Set
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import re
import json
import logging
from abc import ABC, abstractmethod

import spacy
from dateutil import parser
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

logger = logging.getLogger(__name__)


class HearingType(Enum):
    """Types of court hearings and events."""
    HEARING = "hearing"
    TRIAL = "trial"
    MOTION_HEARING = "motion_hearing"
    STATUS_CONFERENCE = "status_conference"
    SETTLEMENT_CONFERENCE = "settlement_conference"
    PRETRIAL_CONFERENCE = "pretrial_conference"
    ARRAIGNMENT = "arraignment"
    SENTENCING = "sentencing"
    DEPOSITION = "deposition"
    ARBITRATION = "arbitration"
    MEDIATION = "mediation"
    CASE_MANAGEMENT = "case_management"
    ORAL_ARGUMENT = "oral_argument"
    PLEA_HEARING = "plea_hearing"
    SCHEDULING_CONFERENCE = "scheduling_conference"
    DISCOVERY_CONFERENCE = "discovery_conference"


class HearingStatus(Enum):
    """Status of detected hearings."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    TENTATIVE = "tentative"


class ConfidenceLevel(Enum):
    """Confidence levels for hearing detection."""
    VERY_HIGH = "very_high"  # 95%+
    HIGH = "high"           # 80-94%
    MEDIUM = "medium"       # 60-79%
    LOW = "low"            # 40-59%
    VERY_LOW = "very_low"  # <40%


@dataclass
class Location:
    """Court location information."""
    court_name: str
    address: Optional[str] = None
    courtroom: Optional[str] = None
    building: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [self.address, self.city, self.state, self.zip_code]
        return ", ".join(filter(None, parts))


@dataclass
class HearingEvent:
    """Detected hearing event."""
    hearing_id: str
    case_number: str
    case_title: str
    hearing_type: HearingType
    date_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[Location] = None
    judge: Optional[str] = None
    status: HearingStatus = HearingStatus.SCHEDULED
    confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    
    # Source information
    source: str = "unknown"
    source_document_id: Optional[str] = None
    raw_text: Optional[str] = None
    
    # Additional details
    parties: List[str] = field(default_factory=list)
    attorneys: List[str] = field(default_factory=list)
    description: Optional[str] = None
    notes: Optional[str] = None
    requirements: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    detected_by: str = "hearing_detector"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        data = {
            'hearing_id': self.hearing_id,
            'case_number': self.case_number,
            'case_title': self.case_title,
            'hearing_type': self.hearing_type.value,
            'date_time': self.date_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'location': self.location.__dict__ if self.location else None,
            'judge': self.judge,
            'status': self.status.value,
            'confidence': self.confidence,
            'confidence_level': self.confidence_level.value,
            'source': self.source,
            'source_document_id': self.source_document_id,
            'raw_text': self.raw_text,
            'parties': self.parties,
            'attorneys': self.attorneys,
            'description': self.description,
            'notes': self.notes,
            'requirements': self.requirements,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'detected_by': self.detected_by
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HearingEvent':
        """Create from dictionary format."""
        # Convert datetime strings back to datetime objects
        data['date_time'] = datetime.fromisoformat(data['date_time'])
        if data.get('end_time'):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # Convert enums
        data['hearing_type'] = HearingType(data['hearing_type'])
        data['status'] = HearingStatus(data['status'])
        data['confidence_level'] = ConfidenceLevel(data['confidence_level'])
        
        # Convert location
        if data.get('location'):
            data['location'] = Location(**data['location'])
        
        return cls(**data)


class HearingDetectionRule:
    """Rule-based hearing detection pattern."""
    
    def __init__(self, name: str, pattern: str, hearing_type: HearingType, 
                 confidence: float = 0.8, requires_date: bool = True):
        self.name = name
        self.pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        self.hearing_type = hearing_type
        self.confidence = confidence
        self.requires_date = requires_date
    
    def matches(self, text: str) -> List[re.Match]:
        """Check if rule matches the text."""
        return list(self.pattern.finditer(text))


class DateTimeExtractor:
    """Extracts and parses dates and times from text."""
    
    def __init__(self):
        # Common date/time patterns in legal documents
        self.patterns = [
            # Full datetime patterns
            r'(?:on\s+)?(\w+day,?\s+\w+\s+\d{1,2},?\s+\d{4})\s+at\s+(\d{1,2}:\d{2}(?:\s*[aApP][mM])?)',
            r'(\d{1,2}/\d{1,2}/\d{2,4})\s+at\s+(\d{1,2}:\d{2}(?:\s*[aApP][mM])?)',
            r'(\d{1,2}-\d{1,2}-\d{2,4})\s+at\s+(\d{1,2}:\d{2}(?:\s*[aApP][mM])?)',
            
            # Date only patterns (will assume 9:00 AM default)
            r'(?:on\s+)?(\w+day,?\s+\w+\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{2,4})',
            r'(\d{1,2}-\d{1,2}-\d{2,4})',
            
            # Relative date patterns
            r'(tomorrow)\s+at\s+(\d{1,2}:\d{2}(?:\s*[aApP][mM])?)',
            r'(next\s+\w+day)\s+at\s+(\d{1,2}:\d{2}(?:\s*[aApP][mM])?)',
        ]
        
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]
    
    def extract_datetime(self, text: str, reference_date: Optional[datetime] = None) -> List[datetime]:
        """Extract all potential dates and times from text."""
        if reference_date is None:
            reference_date = datetime.now()
        
        found_datetimes = []
        
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                try:
                    groups = match.groups()
                    if len(groups) >= 2:  # Date and time
                        date_str, time_str = groups[0], groups[1]
                        dt_str = f"{date_str} {time_str}"
                    else:  # Date only
                        date_str = groups[0]
                        dt_str = f"{date_str} 9:00 AM"  # Default time
                    
                    # Parse the datetime
                    parsed_dt = parser.parse(dt_str, default=reference_date)
                    found_datetimes.append(parsed_dt)
                    
                except (ValueError, parser.ParserError) as e:
                    logger.warning(f"Failed to parse datetime '{match.group()}': {str(e)}")
                    continue
        
        # Remove duplicates and sort
        unique_datetimes = list(set(found_datetimes))
        unique_datetimes.sort()
        
        return unique_datetimes


class LocationExtractor:
    """Extracts court location information from text."""
    
    def __init__(self):
        # Load spaCy model for entity recognition
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Location extraction will be limited.")
            self.nlp = None
        
        # Court name patterns
        self.court_patterns = [
            r'(?:in the )?(.+?\s+(?:court|courthouse))(?:\s+of\s+(.+?))?',
            r'(?:at the )?(.+?\s+(?:district|circuit|superior|municipal|county)\s+court)',
            r'courthouse\s+(?:located\s+)?(?:at\s+)?(.+?)(?:\s+in\s+(.+?))?',
        ]
        
        # Address patterns
        self.address_patterns = [
            r'(\d+\s+[^,]+),\s*([^,]+),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)',
            r'located at\s+(.+?)(?:\s+in\s+(.+?))?',
        ]
    
    def extract_location(self, text: str) -> Optional[Location]:
        """Extract location information from text."""
        location_info = {}
        
        # Extract court name
        for pattern in self.court_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location_info['court_name'] = match.group(1).strip()
                if len(match.groups()) > 1 and match.group(2):
                    location_info['city'] = match.group(2).strip()
                break
        
        # Use spaCy for additional entity extraction if available
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == "GPE":  # Geopolitical entity
                    if 'city' not in location_info:
                        location_info['city'] = ent.text
                elif ent.label_ == "FAC":  # Facility
                    if 'court_name' not in location_info and 'court' in ent.text.lower():
                        location_info['court_name'] = ent.text
        
        # Extract courtroom information
        courtroom_match = re.search(r'(?:courtroom|room)\s+([a-z0-9]+)', text, re.IGNORECASE)
        if courtroom_match:
            location_info['courtroom'] = courtroom_match.group(1)
        
        if location_info:
            return Location(**location_info)
        return None


class MLHearingClassifier:
    """Machine learning classifier for hearing detection and type classification."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 3))
        self.detection_classifier = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.type_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        
        # Feature extraction patterns
        self.feature_patterns = {
            'time_indicators': [r'\b(?:at|on|scheduled|set)\s+(?:for\s+)?(?:\d{1,2}:\d{2}|[ap]\.?m\.?)', 
                               r'(?:morning|afternoon|evening)', r'(?:today|tomorrow|next week)'],
            'court_indicators': [r'\b(?:court|hearing|trial|proceeding)', r'judge|judicial|magistrate',
                               r'docket|calendar', r'clerk|bailiff'],
            'legal_terms': [r'motion|petition|brief|filing', r'plaintiff|defendant|appellant',
                           r'counsel|attorney|lawyer', r'evidence|testimony|witness'],
            'action_words': [r'scheduled|set|continued|postponed', r'appear|present|attend',
                           r'argue|present|testify', r'review|consider|rule']
        }
    
    def extract_features(self, text: str) -> Dict[str, float]:
        """Extract features for ML classification."""
        features = {}
        text_lower = text.lower()
        
        # Pattern-based features
        for category, patterns in self.feature_patterns.items():
            count = sum(len(re.findall(pattern, text_lower)) for pattern in patterns)
            features[f'{category}_count'] = count
            features[f'{category}_density'] = count / max(len(text.split()), 1)
        
        # Text statistics
        features['text_length'] = len(text)
        features['sentence_count'] = len(text.split('.'))
        features['avg_sentence_length'] = len(text.split()) / max(len(text.split('.')), 1)
        
        # Date/time presence
        datetime_extractor = DateTimeExtractor()
        dates_found = len(datetime_extractor.extract_datetime(text))
        features['datetime_count'] = dates_found
        features['has_datetime'] = 1.0 if dates_found > 0 else 0.0
        
        return features
    
    def train(self, training_data: List[Tuple[str, bool, Optional[HearingType]]]):
        """Train the ML classifier with labeled data."""
        if len(training_data) < 50:
            logger.warning("Insufficient training data. ML classifier may not be reliable.")
            return False
        
        texts, is_hearing_labels, type_labels = zip(*training_data)
        
        # Prepare feature vectors
        feature_vectors = []
        for text in texts:
            features = self.extract_features(text)
            feature_vectors.append(list(features.values()))
        
        feature_vectors = np.array(feature_vectors)
        
        # Train TF-IDF vectorizer
        tfidf_features = self.vectorizer.fit_transform(texts)
        
        # Combine TF-IDF and engineered features
        combined_features = np.hstack([tfidf_features.toarray(), feature_vectors])
        
        # Train detection classifier (is it a hearing?)
        X_train_det, X_test_det, y_train_det, y_test_det = train_test_split(
            combined_features, is_hearing_labels, test_size=0.2, random_state=42
        )
        
        self.detection_classifier.fit(X_train_det, y_train_det)
        
        # Evaluate detection classifier
        det_score = self.detection_classifier.score(X_test_det, y_test_det)
        logger.info(f"Hearing detection classifier accuracy: {det_score:.3f}")
        
        # Train type classifier (what type of hearing?)
        hearing_indices = [i for i, is_hearing in enumerate(is_hearing_labels) if is_hearing]
        if len(hearing_indices) > 20:  # Need enough positive samples
            hearing_features = combined_features[hearing_indices]
            hearing_types = [type_labels[i].value for i in hearing_indices if type_labels[i]]
            
            if len(set(hearing_types)) > 1:  # Need multiple classes
                X_train_type, X_test_type, y_train_type, y_test_type = train_test_split(
                    hearing_features, hearing_types, test_size=0.2, random_state=42
                )
                
                self.type_classifier.fit(X_train_type, y_train_type)
                type_score = self.type_classifier.score(X_test_type, y_test_type)
                logger.info(f"Hearing type classifier accuracy: {type_score:.3f}")
        
        self.is_trained = True
        return True
    
    def predict_hearing(self, text: str) -> Tuple[bool, float, Optional[HearingType]]:
        """Predict if text contains a hearing and its type."""
        if not self.is_trained:
            logger.warning("ML classifier not trained. Using default predictions.")
            return False, 0.5, None
        
        # Extract features
        features = self.extract_features(text)
        feature_vector = np.array([list(features.values())])
        
        # TF-IDF features
        tfidf_features = self.vectorizer.transform([text])
        
        # Combine features
        combined_features = np.hstack([tfidf_features.toarray(), feature_vector])
        
        # Predict if it's a hearing
        is_hearing_prob = self.detection_classifier.predict_proba(combined_features)[0][1]
        is_hearing = is_hearing_prob > 0.5
        
        # Predict hearing type if it's a hearing
        hearing_type = None
        if is_hearing:
            try:
                type_prediction = self.type_classifier.predict(combined_features)[0]
                hearing_type = HearingType(type_prediction)
            except (ValueError, AttributeError):
                hearing_type = HearingType.HEARING  # Default type
        
        return is_hearing, is_hearing_prob, hearing_type
    
    def save_model(self, filepath: str):
        """Save trained model to file."""
        model_data = {
            'vectorizer': self.vectorizer,
            'detection_classifier': self.detection_classifier,
            'type_classifier': self.type_classifier,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from file."""
        try:
            model_data = joblib.load(filepath)
            self.vectorizer = model_data['vectorizer']
            self.detection_classifier = model_data['detection_classifier']
            self.type_classifier = model_data['type_classifier']
            self.is_trained = model_data['is_trained']
            logger.info(f"Model loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False


class HearingDetector:
    """Main hearing detection engine."""
    
    def __init__(self):
        self.rules = self._create_detection_rules()
        self.datetime_extractor = DateTimeExtractor()
        self.location_extractor = LocationExtractor()
        self.ml_classifier = MLHearingClassifier()
        self.detected_hearings: Dict[str, HearingEvent] = {}
        
        # Detection confidence weights
        self.weights = {
            'rule_based': 0.4,
            'ml_based': 0.3,
            'datetime_presence': 0.2,
            'location_presence': 0.1
        }
    
    def _create_detection_rules(self) -> List[HearingDetectionRule]:
        """Create rule-based detection patterns."""
        rules = [
            # Motion hearings
            HearingDetectionRule(
                "motion_hearing",
                r'(?:hearing|argument)\s+(?:on|for|regarding)\s+(?:the\s+)?(?:motion|petition)',
                HearingType.MOTION_HEARING,
                confidence=0.85
            ),
            
            # Status conferences
            HearingDetectionRule(
                "status_conference", 
                r'status\s+(?:conference|hearing|check)',
                HearingType.STATUS_CONFERENCE,
                confidence=0.8
            ),
            
            # Settlement conferences
            HearingDetectionRule(
                "settlement_conference",
                r'settlement\s+(?:conference|discussion|meeting)',
                HearingType.SETTLEMENT_CONFERENCE,
                confidence=0.8
            ),
            
            # Pretrial conferences
            HearingDetectionRule(
                "pretrial_conference",
                r'pre-?trial\s+(?:conference|hearing|meeting)',
                HearingType.PRETRIAL_CONFERENCE,
                confidence=0.85
            ),
            
            # Case management
            HearingDetectionRule(
                "case_management",
                r'case\s+management\s+(?:conference|hearing|meeting)',
                HearingType.CASE_MANAGEMENT,
                confidence=0.8
            ),
            
            # Scheduling conferences
            HearingDetectionRule(
                "scheduling_conference",
                r'scheduling\s+(?:conference|hearing|meeting)',
                HearingType.SCHEDULING_CONFERENCE,
                confidence=0.8
            ),
            
            # Oral arguments
            HearingDetectionRule(
                "oral_argument",
                r'oral\s+argument(?:s)?',
                HearingType.ORAL_ARGUMENT,
                confidence=0.9
            ),
            
            # Trials
            HearingDetectionRule(
                "trial",
                r'trial\s+(?:date|scheduled|set|to\s+commence)',
                HearingType.TRIAL,
                confidence=0.9
            ),
            
            # Depositions
            HearingDetectionRule(
                "deposition",
                r'deposition\s+of\s+\w+',
                HearingType.DEPOSITION,
                confidence=0.85
            ),
            
            # General hearings
            HearingDetectionRule(
                "general_hearing",
                r'(?:court\s+)?hearing\s+(?:scheduled|set|on|for)',
                HearingType.HEARING,
                confidence=0.7
            ),
            
            # Arraignments
            HearingDetectionRule(
                "arraignment",
                r'arraignment\s+(?:hearing|scheduled|set)',
                HearingType.ARRAIGNMENT,
                confidence=0.9
            ),
            
            # Sentencing
            HearingDetectionRule(
                "sentencing",
                r'sentencing\s+(?:hearing|scheduled|set)',
                HearingType.SENTENCING,
                confidence=0.9
            )
        ]
        
        return rules
    
    async def detect_hearings(self, text: str, source: str = "unknown",
                            source_document_id: Optional[str] = None,
                            case_number: Optional[str] = None,
                            case_title: Optional[str] = None) -> List[HearingEvent]:
        """Detect hearings from text using multiple methods."""
        detected_hearings = []
        
        # Rule-based detection
        rule_detections = self._detect_with_rules(text)
        
        # ML-based detection
        ml_detection = None
        if self.ml_classifier.is_trained:
            is_hearing, ml_confidence, hearing_type = self.ml_classifier.predict_hearing(text)
            if is_hearing:
                ml_detection = (hearing_type, ml_confidence)
        
        # Extract datetime information
        detected_datetimes = self.datetime_extractor.extract_datetime(text)
        
        # Extract location information
        location = self.location_extractor.extract_location(text)
        
        # Combine detections
        if rule_detections or ml_detection:
            # Use the highest confidence detection
            best_detection = None
            
            if rule_detections:
                best_rule = max(rule_detections, key=lambda x: x[1])  # (hearing_type, confidence)
                best_detection = best_rule
            
            if ml_detection and (not best_detection or ml_detection[1] > best_detection[1]):
                best_detection = ml_detection
            
            if best_detection:
                hearing_type, base_confidence = best_detection
                
                # Calculate final confidence
                final_confidence = self._calculate_confidence(
                    rule_confidence=best_detection[1] if rule_detections else 0.0,
                    ml_confidence=ml_detection[1] if ml_detection else 0.0,
                    has_datetime=len(detected_datetimes) > 0,
                    has_location=location is not None
                )
                
                # Create hearing event for each detected datetime
                if detected_datetimes:
                    for dt in detected_datetimes:
                        hearing_event = self._create_hearing_event(
                            text=text,
                            hearing_type=hearing_type,
                            date_time=dt,
                            location=location,
                            confidence=final_confidence,
                            source=source,
                            source_document_id=source_document_id,
                            case_number=case_number,
                            case_title=case_title
                        )
                        detected_hearings.append(hearing_event)
                else:
                    # No specific datetime found, create with placeholder
                    hearing_event = self._create_hearing_event(
                        text=text,
                        hearing_type=hearing_type,
                        date_time=None,
                        location=location,
                        confidence=final_confidence * 0.7,  # Reduce confidence without datetime
                        source=source,
                        source_document_id=source_document_id,
                        case_number=case_number,
                        case_title=case_title
                    )
                    detected_hearings.append(hearing_event)
        
        # Store detected hearings
        for hearing in detected_hearings:
            self.detected_hearings[hearing.hearing_id] = hearing
        
        logger.info(f"Detected {len(detected_hearings)} hearings from {source}")
        return detected_hearings
    
    def _detect_with_rules(self, text: str) -> List[Tuple[HearingType, float]]:
        """Apply rule-based detection."""
        detections = []
        
        for rule in self.rules:
            matches = rule.matches(text)
            if matches:
                detections.append((rule.hearing_type, rule.confidence))
                logger.debug(f"Rule '{rule.name}' matched with confidence {rule.confidence}")
        
        return detections
    
    def _calculate_confidence(self, rule_confidence: float, ml_confidence: float,
                            has_datetime: bool, has_location: bool) -> float:
        """Calculate weighted confidence score."""
        score = (
            rule_confidence * self.weights['rule_based'] +
            ml_confidence * self.weights['ml_based'] +
            (1.0 if has_datetime else 0.0) * self.weights['datetime_presence'] +
            (1.0 if has_location else 0.0) * self.weights['location_presence']
        )
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _create_hearing_event(self, text: str, hearing_type: HearingType,
                            date_time: Optional[datetime], location: Optional[Location],
                            confidence: float, source: str, source_document_id: Optional[str],
                            case_number: Optional[str], case_title: Optional[str]) -> HearingEvent:
        """Create a hearing event from detection results."""
        hearing_id = f"hearing_{datetime.now().timestamp()}_{hash(text[:100])}"
        
        # Extract additional information
        judge = self._extract_judge(text)
        parties = self._extract_parties(text)
        description = self._extract_description(text, hearing_type)
        
        # Determine confidence level
        confidence_level = self._get_confidence_level(confidence)
        
        # Set default datetime if not found
        if date_time is None:
            date_time = datetime.now() + timedelta(days=1)  # Default to tomorrow
        
        # Estimate end time (default 1 hour duration)
        end_time = date_time + timedelta(hours=1)
        if hearing_type in [HearingType.TRIAL, HearingType.DEPOSITION]:
            end_time = date_time + timedelta(hours=4)  # Longer events
        
        return HearingEvent(
            hearing_id=hearing_id,
            case_number=case_number or "UNKNOWN",
            case_title=case_title or "Unknown Case",
            hearing_type=hearing_type,
            date_time=date_time,
            end_time=end_time,
            location=location,
            judge=judge,
            confidence=confidence,
            confidence_level=confidence_level,
            source=source,
            source_document_id=source_document_id,
            raw_text=text[:1000],  # Store first 1000 chars
            parties=parties,
            description=description
        )
    
    def _extract_judge(self, text: str) -> Optional[str]:
        """Extract judge name from text."""
        patterns = [
            r'(?:judge|hon\.?|honorable)\s+([a-z\s\.]+)',
            r'(?:before|presiding):\s*(?:judge|hon\.?|honorable)\s+([a-z\s\.]+)',
            r'([a-z\s\.]+),\s*(?:judge|j\.)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                judge_name = match.group(1).strip()
                # Clean up the name
                judge_name = re.sub(r'\s+', ' ', judge_name)
                if len(judge_name) > 3:  # Reasonable name length
                    return judge_name
        
        return None
    
    def _extract_parties(self, text: str) -> List[str]:
        """Extract party names from text."""
        parties = []
        
        # Common patterns for party names
        patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'plaintiff\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'defendant\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    parties.extend(match)
                else:
                    parties.append(match)
        
        # Clean and deduplicate
        cleaned_parties = []
        for party in parties:
            party = party.strip()
            if len(party) > 2 and party not in cleaned_parties:
                cleaned_parties.append(party)
        
        return cleaned_parties[:10]  # Limit to 10 parties
    
    def _extract_description(self, text: str, hearing_type: HearingType) -> Optional[str]:
        """Extract hearing description from text."""
        # Look for descriptions near the hearing type
        sentences = text.split('.')
        
        for sentence in sentences:
            if hearing_type.value.replace('_', ' ') in sentence.lower():
                # Clean up the sentence
                description = sentence.strip()
                if len(description) > 20:
                    return description[:200]  # Limit length
        
        return None
    
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Convert numeric confidence to confidence level."""
        if confidence >= 0.95:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.80:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.60:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.40:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def get_hearings_by_date_range(self, start_date: datetime, end_date: datetime) -> List[HearingEvent]:
        """Get hearings within a date range."""
        filtered_hearings = []
        
        for hearing in self.detected_hearings.values():
            if start_date <= hearing.date_time <= end_date:
                filtered_hearings.append(hearing)
        
        return sorted(filtered_hearings, key=lambda h: h.date_time)
    
    def get_hearings_by_case(self, case_number: str) -> List[HearingEvent]:
        """Get all hearings for a specific case."""
        case_hearings = []
        
        for hearing in self.detected_hearings.values():
            if hearing.case_number == case_number:
                case_hearings.append(hearing)
        
        return sorted(case_hearings, key=lambda h: h.date_time)
    
    def update_hearing_status(self, hearing_id: str, new_status: HearingStatus) -> bool:
        """Update the status of a detected hearing."""
        if hearing_id in self.detected_hearings:
            self.detected_hearings[hearing_id].status = new_status
            self.detected_hearings[hearing_id].updated_at = datetime.now()
            return True
        return False
    
    def train_ml_classifier(self, training_data_file: str) -> bool:
        """Train the ML classifier from a training data file."""
        try:
            # Load training data (expected format: CSV with columns: text, is_hearing, hearing_type)
            import pandas as pd
            df = pd.read_csv(training_data_file)
            
            training_data = []
            for _, row in df.iterrows():
                text = row['text']
                is_hearing = bool(row['is_hearing'])
                hearing_type = HearingType(row['hearing_type']) if row['hearing_type'] else None
                training_data.append((text, is_hearing, hearing_type))
            
            return self.ml_classifier.train(training_data)
        
        except Exception as e:
            logger.error(f"Failed to train ML classifier: {str(e)}")
            return False
    
    def save_ml_model(self, filepath: str):
        """Save the trained ML model."""
        self.ml_classifier.save_model(filepath)
    
    def load_ml_model(self, filepath: str):
        """Load a pre-trained ML model."""
        return self.ml_classifier.load_model(filepath)


# Example usage and testing
async def example_usage():
    """Example usage of the hearing detection system."""
    
    # Initialize detector
    detector = HearingDetector()
    
    # Sample legal texts
    sample_texts = [
        """
        Motion Hearing scheduled for Tuesday, January 15, 2024 at 9:30 AM
        in Courtroom 302, Superior Court of California, County of Los Angeles.
        The Honorable Judge Smith presiding. Case: Smith v. Jones (Case No. 23CV12345)
        """,
        
        """
        Status Conference set for 01/20/2024 at 2:00 PM before Judge Johnson
        in the matter of ABC Corporation v. XYZ Limited. All parties must appear.
        """,
        
        """
        Deposition of John Doe scheduled for January 25, 2024 at 10:00 AM
        at the offices of Smith & Associates, 123 Main Street, Anytown, CA.
        """,
        
        """
        Trial date set for February 1, 2024 at 9:00 AM in Department 15
        of the Los Angeles Superior Court. Case: People v. Defendant (Case No. 23CR67890)
        """,
        
        """
        Oral argument on appellant's motion for summary judgment
        scheduled for March 15, 2024 at 1:30 PM in the Court of Appeals.
        """
    ]
    
    # Detect hearings
    all_hearings = []
    for i, text in enumerate(sample_texts):
        hearings = await detector.detect_hearings(
            text=text,
            source=f"document_{i}",
            source_document_id=f"doc_{i}",
            case_number=f"CASE_{i:03d}",
            case_title=f"Sample Case {i+1}"
        )
        all_hearings.extend(hearings)
        
        print(f"\nDocument {i+1}:")
        print(f"Text: {text.strip()}")
        print(f"Detected {len(hearings)} hearing(s)")
        
        for hearing in hearings:
            print(f"  - Type: {hearing.hearing_type.value}")
            print(f"  - Date/Time: {hearing.date_time}")
            print(f"  - Location: {hearing.location.court_name if hearing.location else 'Unknown'}")
            print(f"  - Judge: {hearing.judge or 'Unknown'}")
            print(f"  - Confidence: {hearing.confidence:.2f} ({hearing.confidence_level.value})")
    
    # Demonstrate querying capabilities
    print(f"\n=== Summary ===")
    print(f"Total hearings detected: {len(all_hearings)}")
    
    # Group by hearing type
    type_counts = {}
    for hearing in all_hearings:
        hearing_type = hearing.hearing_type.value
        type_counts[hearing_type] = type_counts.get(hearing_type, 0) + 1
    
    print("\nHearing types:")
    for hearing_type, count in type_counts.items():
        print(f"  - {hearing_type}: {count}")
    
    # Show high-confidence hearings
    high_confidence_hearings = [h for h in all_hearings if h.confidence >= 0.8]
    print(f"\nHigh-confidence hearings ({len(high_confidence_hearings)}):")
    for hearing in high_confidence_hearings:
        print(f"  - {hearing.hearing_type.value} on {hearing.date_time.strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())