"""
Advanced deadline extraction engine for legal documents.
Identifies, categorizes, and validates legal deadlines with high precision.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta, date
import json
import re
from collections import defaultdict

import spacy
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import pandas as pd
from transformers import pipeline

logger = logging.getLogger(__name__)


class DeadlineType(Enum):
    """Types of legal deadlines."""
    FILING = "filing"                    # Document filing deadlines
    RESPONSE = "response"                # Response/answer deadlines
    MOTION = "motion"                    # Motion practice deadlines
    DISCOVERY = "discovery"              # Discovery-related deadlines
    HEARING = "hearing"                  # Hearing appearances
    TRIAL = "trial"                      # Trial dates and prep deadlines
    APPEAL = "appeal"                    # Appeal deadlines
    PAYMENT = "payment"                  # Payment due dates
    COMPLIANCE = "compliance"            # Regulatory compliance deadlines
    STATUTE_OF_LIMITATIONS = "statute_of_limitations"  # SOL deadlines
    CONTRACT = "contract"                # Contractual deadlines
    ADMINISTRATIVE = "administrative"    # Administrative deadlines
    COURT_ORDER = "court_order"         # Court-ordered deadlines
    SETTLEMENT = "settlement"            # Settlement negotiation deadlines
    UNKNOWN = "unknown"                  # Unclassified deadlines


class PriorityLevel(Enum):
    """Priority levels for deadlines."""
    CRITICAL = "critical"        # Jurisdictional/case-ending deadlines
    HIGH = "high"               # Important substantive deadlines
    MEDIUM = "medium"           # Standard procedural deadlines
    LOW = "low"                 # Administrative or informational
    INFORMATIONAL = "informational"  # For tracking only


class DeadlineStatus(Enum):
    """Status of extracted deadlines."""
    PENDING = "pending"          # Future deadline
    APPROACHING = "approaching"  # Within warning period
    OVERDUE = "overdue"         # Past deadline
    COMPLETED = "completed"      # Action taken
    EXTENDED = "extended"        # Deadline extended
    CANCELLED = "cancelled"      # No longer applicable


class ConfidenceLevel(Enum):
    """Confidence levels for deadline extraction."""
    VERY_HIGH = "very_high"     # 90-100% confidence
    HIGH = "high"               # 80-89% confidence
    MEDIUM = "medium"           # 60-79% confidence
    LOW = "low"                 # 40-59% confidence
    VERY_LOW = "very_low"       # Below 40% confidence


@dataclass
class ExtractedDeadline:
    """Represents an extracted legal deadline."""
    deadline_id: str
    
    # Core deadline information
    date: datetime
    deadline_type: DeadlineType
    priority: PriorityLevel
    status: DeadlineStatus
    confidence: ConfidenceLevel
    
    # Descriptive information
    description: str
    context: str
    action_required: str
    
    # Source information
    source_document: str
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    extracted_text: str = ""
    
    # Legal context
    jurisdiction: Optional[str] = None
    court: Optional[str] = None
    case_number: Optional[str] = None
    rule_or_statute: Optional[str] = None
    
    # Parties and responsibility
    responsible_party: Optional[str] = None
    opposing_party: Optional[str] = None
    attorney_responsible: Optional[str] = None
    
    # Timing and extensions
    original_date: Optional[datetime] = None
    extension_count: int = 0
    can_be_extended: bool = True
    extension_conditions: List[str] = field(default_factory=list)
    
    # Dependencies and relationships
    depends_on: List[str] = field(default_factory=list)  # Other deadline IDs
    triggers: List[str] = field(default_factory=list)    # Triggered deadline IDs
    related_deadlines: List[str] = field(default_factory=list)
    
    # Response requirements
    response_time_days: Optional[int] = None
    response_format: Optional[str] = None
    service_requirements: List[str] = field(default_factory=list)
    
    # Alert settings
    alert_days_before: List[int] = field(default_factory=lambda: [30, 14, 7, 3, 1])
    custom_alerts: List[datetime] = field(default_factory=list)
    
    # Metadata
    extraction_method: str = ""
    validation_notes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    extraction_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.deadline_id:
            self.deadline_id = f"deadline_{hash(self.description + str(self.date))}"


@dataclass
class DeadlineAnalysis:
    """Analysis results for extracted deadlines."""
    analysis_id: str
    document_id: str
    
    # Extracted deadlines
    deadlines: List[ExtractedDeadline] = field(default_factory=list)
    
    # Analysis metrics
    total_deadlines: int = 0
    critical_deadlines: int = 0
    approaching_deadlines: int = 0
    overdue_deadlines: int = 0
    
    # Type distribution
    deadline_type_counts: Dict[DeadlineType, int] = field(default_factory=dict)
    
    # Time analysis
    earliest_deadline: Optional[datetime] = None
    latest_deadline: Optional[datetime] = None
    deadline_density: float = 0.0  # Deadlines per month
    
    # Quality metrics
    high_confidence_count: int = 0
    requires_validation_count: int = 0
    
    # Recommendations
    priority_actions: List[str] = field(default_factory=list)
    calendar_entries: List[Dict[str, Any]] = field(default_factory=list)
    
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)


class DeadlineExtractor:
    """Advanced deadline extraction engine for legal documents."""
    
    def __init__(self, nlp_model: str = "en_core_web_sm"):
        """Initialize deadline extractor.
        
        Args:
            nlp_model: spaCy model for NLP processing
        """
        self.nlp_model = nlp_model
        self.nlp = None
        
        # Initialize extraction patterns
        self._initialize_patterns()
        
        # Initialize models
        self._initialize_models()
        
        # Legal rules and statutes database
        self._initialize_legal_rules()
        
        # Deadline cache
        self.deadline_cache: Dict[str, DeadlineAnalysis] = {}
    
    def _initialize_patterns(self):
        """Initialize regex patterns for deadline extraction."""
        
        # Date patterns with various formats
        self.date_patterns = [
            # Standard date formats
            r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b',
            r'\b(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b',
            
            # Written dates
            r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
            r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b',
            
            # Relative dates
            r'\b(within\s+\d+\s+(?:days?|weeks?|months?))\b',
            r'\b(\d+\s+(?:days?|weeks?|months?)\s+(?:from|after|before))\b',
            r'\b(no\s+later\s+than\s+[^.!?]+)\b',
            r'\b(by\s+[^.!?]+)\b',
            
            # Court date formats
            r'\b((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b'
        ]
        
        # Deadline trigger phrases
        self.deadline_triggers = {
            DeadlineType.FILING: [
                r'\bmust\s+(?:be\s+)?fil[ed]',
                r'\bshall\s+(?:be\s+)?fil[ed]',
                r'\bfiling\s+deadline',
                r'\bdue\s+(?:date|by)',
                r'\bsubmit(?:ted)?\s+(?:by|before|no\s+later\s+than)',
                r'\blodg[ed]\s+(?:by|before)'
            ],
            DeadlineType.RESPONSE: [
                r'\brespons[e]\s+(?:is\s+)?due',
                r'\bansw[er]\s+(?:is\s+)?due',
                r'\brepl[y]\s+(?:is\s+)?due',
                r'\bwithin\s+\d+\s+days?\s+(?:of|after)',
                r'\btime\s+(?:limit|period)\s+(?:for|to)\s+respond'
            ],
            DeadlineType.MOTION: [
                r'\bmotion\s+(?:must|shall)\s+be\s+filed',
                r'\bmotion\s+deadline',
                r'\bmotions?\s+due',
                r'\bpretrial\s+motions?'
            ],
            DeadlineType.DISCOVERY: [
                r'\bdiscovery\s+(?:deadline|cutoff)',
                r'\bdiscovery\s+(?:must|shall)\s+be\s+complet[ed]',
                r'\binterrogatories?\s+due',
                r'\bdeposition\s+deadline',
                r'\bdocument\s+production\s+due'
            ],
            DeadlineType.HEARING: [
                r'\bhearing\s+(?:date|scheduled)',
                r'\bappearance\s+required',
                r'\boral\s+argument',
                r'\bstatus\s+conference',
                r'\bpretrial\s+conference'
            ],
            DeadlineType.TRIAL: [
                r'\btrial\s+(?:date|scheduled)',
                r'\bjury\s+trial',
                r'\bbench\s+trial',
                r'\btrial\s+preparation\s+deadline'
            ],
            DeadlineType.APPEAL: [
                r'\bappeal\s+(?:deadline|period)',
                r'\bnotice\s+of\s+appeal',
                r'\bappellate\s+brief',
                r'\bwithin\s+30\s+days?\s+of.*judgment'
            ],
            DeadlineType.PAYMENT: [
                r'\bpayment\s+due',
                r'\bamount\s+due\s+(?:by|before)',
                r'\binstallment\s+due',
                r'\bfees?\s+(?:must|shall)\s+be\s+paid'
            ],
            DeadlineType.COMPLIANCE: [
                r'\bcompl[yi]\s+(?:by|before|within)',
                r'\brequir[ed]\s+(?:by|before)',
                r'\bdeadline\s+(?:for|to)\s+compl[yi]',
                r'\bmust\s+be\s+complet[ed]'
            ],
            DeadlineType.STATUTE_OF_LIMITATIONS: [
                r'\bstatute\s+of\s+limitations',
                r'\blimitations?\s+period',
                r'\bclaim\s+(?:must|shall)\s+be\s+brought\s+within',
                r'\baction\s+(?:must|shall)\s+be\s+commenc[ed]'
            ]
        }
        
        # Priority indicators
        self.priority_indicators = {
            PriorityLevel.CRITICAL: [
                r'\bjurisdictional',
                r'\bmandatory',
                r'\bstatute\s+of\s+limitations',
                r'\bnotice\s+of\s+appeal',
                r'\bcannot\s+be\s+extended',
                r'\bfinal\s+deadline'
            ],
            PriorityLevel.HIGH: [
                r'\bmotion\s+(?:for\s+)?summary\s+judgment',
                r'\bdispos[ai]tive\s+motion',
                r'\btrial\s+date',
                r'\bconfirmation\s+hearing',
                r'\bimportant',
                r'\bcritical'
            ],
            PriorityLevel.MEDIUM: [
                r'\bdiscovery',
                r'\bpretrial',
                r'\bstatus\s+(?:report|conference)',
                r'\bscheduling'
            ],
            PriorityLevel.LOW: [
                r'\badministrative',
                r'\broutine',
                r'\binformational',
                r'\bnotification'
            ]
        }
        
        # Time-based warning periods
        self.warning_periods = {
            PriorityLevel.CRITICAL: [60, 30, 14, 7, 3, 1],
            PriorityLevel.HIGH: [30, 14, 7, 3, 1],
            PriorityLevel.MEDIUM: [14, 7, 3, 1],
            PriorityLevel.LOW: [7, 3, 1]
        }
    
    def _initialize_models(self):
        """Initialize NLP models and classifiers."""
        try:
            # Load spaCy model
            self.nlp = spacy.load(self.nlp_model)
            logger.info(f"Loaded spaCy model: {self.nlp_model}")
            
            # Initialize date extraction pipeline
            try:
                self.date_classifier = pipeline(
                    "token-classification",
                    model="dbmdz/bert-large-cased-finetuned-conll03-english",
                    device=-1  # Use CPU
                )
                logger.info("Loaded date classification model")
            except Exception as e:
                logger.warning(f"Could not load date classifier: {e}")
                self.date_classifier = None
                
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            self.nlp = None
    
    def _initialize_legal_rules(self):
        """Initialize database of legal rules and standard deadlines."""
        
        # Federal Rules of Civil Procedure deadlines
        self.frcp_deadlines = {
            'answer': {'days': 21, 'description': 'Answer to complaint', 'rule': 'FRCP 12(a)(1)(A)'},
            'motion_to_dismiss': {'days': 21, 'description': 'Motion to dismiss', 'rule': 'FRCP 12(b)'},
            'discovery_plan': {'days': 99, 'description': 'Meet and confer on discovery plan', 'rule': 'FRCP 26(f)'},
            'initial_disclosures': {'days': 14, 'description': 'Initial disclosures after Rule 26(f) conference', 'rule': 'FRCP 26(a)(1)'},
            'summary_judgment': {'days': 56, 'description': 'Summary judgment motion (before trial)', 'rule': 'FRCP 56(b)'},
            'jury_demand': {'days': 14, 'description': 'Jury trial demand', 'rule': 'FRCP 38(b)'}
        }
        
        # Federal Rules of Bankruptcy Procedure deadlines
        self.frbp_deadlines = {
            'proof_of_claim': {'days': 90, 'description': 'File proof of claim (non-government)', 'rule': 'FRBP 3002(c)'},
            'objection_to_claim': {'days': 30, 'description': 'Object to proof of claim', 'rule': 'FRBP 3007'},
            'reaffirmation_agreement': {'days': 60, 'description': 'File reaffirmation agreement', 'rule': 'FRBP 4008'},
            'plan_confirmation_hearing': {'days': 45, 'description': 'Confirmation hearing notice', 'rule': 'FRBP 2002(b)'},
            'adversary_complaint': {'days': 30, 'description': 'Answer to adversary complaint', 'rule': 'FRBP 7012'}
        }
        
        # Appeal deadlines
        self.appeal_deadlines = {
            'civil_appeal': {'days': 30, 'description': 'Notice of appeal (civil case)', 'rule': '28 U.S.C. § 2107'},
            'criminal_appeal': {'days': 14, 'description': 'Notice of appeal (criminal case)', 'rule': 'Fed. R. App. P. 4(b)'},
            'appellate_brief': {'days': 40, 'description': 'Appellant brief', 'rule': 'Fed. R. App. P. 31(a)'},
            'response_brief': {'days': 30, 'description': 'Response brief', 'rule': 'Fed. R. App. P. 31(a)'}
        }
        
        # State-specific variations (simplified)
        self.state_variations = {
            'california': {
                'answer_complaint': {'days': 30, 'rule': 'CCP § 412.20'},
                'summary_judgment': {'days': 75, 'rule': 'CCP § 437c'}
            },
            'new_york': {
                'answer_complaint': {'days': 20, 'rule': 'CPLR § 320'},
                'bill_of_particulars': {'days': 20, 'rule': 'CPLR § 3041'}
            },
            'texas': {
                'answer_complaint': {'days': 21, 'rule': 'TRCP 99(b)'},
                'special_exceptions': {'days': 30, 'rule': 'TRCP 90'}
            }
        }
    
    def extract_deadlines(self, content: str, document_id: str = "", 
                         context: Dict[str, Any] = None) -> DeadlineAnalysis:
        """Extract deadlines from legal document content.
        
        Args:
            content: Document text content
            document_id: Optional document identifier
            context: Additional context (jurisdiction, case type, etc.)
            
        Returns:
            Complete deadline analysis
        """
        logger.info(f"Extracting deadlines from document: {document_id}")
        
        context = context or {}
        
        # Extract all potential deadlines
        raw_deadlines = self._extract_raw_deadlines(content)
        
        # Process and classify deadlines
        processed_deadlines = self._process_deadlines(raw_deadlines, content, context)
        
        # Validate and enrich deadlines
        validated_deadlines = self._validate_deadlines(processed_deadlines, context)
        
        # Create deadline relationships
        self._create_deadline_relationships(validated_deadlines)
        
        # Generate analysis
        analysis = self._generate_analysis(validated_deadlines, document_id)
        
        return analysis
    
    def _extract_raw_deadlines(self, content: str) -> List[Dict[str, Any]]:
        """Extract raw deadline candidates from text."""
        
        raw_deadlines = []
        
        # Extract using pattern matching
        raw_deadlines.extend(self._extract_with_patterns(content))
        
        # Extract using NLP
        if self.nlp:
            raw_deadlines.extend(self._extract_with_nlp(content))
        
        # Extract using ML model
        if self.date_classifier:
            raw_deadlines.extend(self._extract_with_ml(content))
        
        return raw_deadlines
    
    def _extract_with_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract deadlines using regex patterns."""
        
        candidates = []
        
        # Find all date mentions
        for pattern in self.date_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                date_text = match.group(1)
                start_pos = match.start()
                end_pos = match.end()
                
                # Get surrounding context
                context_start = max(0, start_pos - 200)
                context_end = min(len(content), end_pos + 200)
                context = content[context_start:context_end]
                
                # Check for deadline triggers in context
                deadline_type = self._identify_deadline_type(context)
                priority = self._assess_priority(context)
                
                if deadline_type != DeadlineType.UNKNOWN:
                    candidates.append({
                        'date_text': date_text,
                        'context': context,
                        'start_pos': start_pos,
                        'end_pos': end_pos,
                        'deadline_type': deadline_type,
                        'priority': priority,
                        'extraction_method': 'pattern_matching',
                        'confidence': self._calculate_pattern_confidence(context, deadline_type)
                    })
        
        return candidates
    
    def _extract_with_nlp(self, content: str) -> List[Dict[str, Any]]:
        """Extract deadlines using spaCy NLP."""
        
        candidates = []
        
        try:
            # Process document with spaCy
            doc = self.nlp(content[:1000000])  # Limit for performance
            
            # Look for date entities
            for ent in doc.ents:
                if ent.label_ in ["DATE", "TIME"]:
                    # Get sentence context
                    sentence = ent.sent.text
                    
                    # Check for legal deadline indicators
                    deadline_type = self._identify_deadline_type(sentence)
                    
                    if deadline_type != DeadlineType.UNKNOWN:
                        priority = self._assess_priority(sentence)
                        
                        candidates.append({
                            'date_text': ent.text,
                            'context': sentence,
                            'start_pos': ent.start_char,
                            'end_pos': ent.end_char,
                            'deadline_type': deadline_type,
                            'priority': priority,
                            'extraction_method': 'nlp_entity',
                            'confidence': self._calculate_nlp_confidence(sentence, deadline_type)
                        })
                        
        except Exception as e:
            logger.warning(f"NLP deadline extraction failed: {e}")
        
        return candidates
    
    def _extract_with_ml(self, content: str) -> List[Dict[str, Any]]:
        """Extract deadlines using ML models."""
        
        candidates = []
        
        # This would be implemented with a trained model specifically
        # for legal deadline extraction. For now, return empty list.
        
        return candidates
    
    def _identify_deadline_type(self, context: str) -> DeadlineType:
        """Identify the type of deadline from context."""
        
        context_lower = context.lower()
        
        # Check each deadline type's trigger patterns
        for deadline_type, patterns in self.deadline_triggers.items():
            for pattern in patterns:
                if re.search(pattern, context_lower):
                    return deadline_type
        
        # Check for specific legal terms
        if 'statute of limitations' in context_lower:
            return DeadlineType.STATUTE_OF_LIMITATIONS
        elif 'appeal' in context_lower and 'notice' in context_lower:
            return DeadlineType.APPEAL
        elif 'hearing' in context_lower or 'conference' in context_lower:
            return DeadlineType.HEARING
        elif 'trial' in context_lower:
            return DeadlineType.TRIAL
        elif 'payment' in context_lower or 'fee' in context_lower:
            return DeadlineType.PAYMENT
        
        return DeadlineType.UNKNOWN
    
    def _assess_priority(self, context: str) -> PriorityLevel:
        """Assess the priority level of a deadline from context."""
        
        context_lower = context.lower()
        
        # Check priority indicators
        for priority, indicators in self.priority_indicators.items():
            for indicator in indicators:
                if re.search(indicator, context_lower):
                    return priority
        
        # Default based on deadline type implications
        if any(term in context_lower for term in ['jurisdictional', 'mandatory', 'appeal', 'statute']):
            return PriorityLevel.CRITICAL
        elif any(term in context_lower for term in ['motion', 'response', 'trial']):
            return PriorityLevel.HIGH
        elif any(term in context_lower for term in ['discovery', 'disclosure']):
            return PriorityLevel.MEDIUM
        else:
            return PriorityLevel.LOW
    
    def _calculate_pattern_confidence(self, context: str, deadline_type: DeadlineType) -> ConfidenceLevel:
        """Calculate confidence level for pattern-based extraction."""
        
        confidence_score = 0.5  # Base score
        
        # Boost for strong deadline indicators
        if deadline_type != DeadlineType.UNKNOWN:
            confidence_score += 0.2
        
        # Boost for specific legal terms
        legal_terms = ['must', 'shall', 'required', 'deadline', 'due', 'file', 'serve']
        term_count = sum(1 for term in legal_terms if term in context.lower())
        confidence_score += min(0.3, term_count * 0.05)
        
        # Boost for date format clarity
        if re.search(r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}', context):
            confidence_score += 0.1
        
        # Convert to confidence level
        if confidence_score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _calculate_nlp_confidence(self, context: str, deadline_type: DeadlineType) -> ConfidenceLevel:
        """Calculate confidence level for NLP-based extraction."""
        
        # NLP extractions generally have good precision
        base_confidence = 0.7
        
        if deadline_type != DeadlineType.UNKNOWN:
            base_confidence += 0.2
        
        # Convert to confidence level
        if base_confidence >= 0.85:
            return ConfidenceLevel.VERY_HIGH
        elif base_confidence >= 0.75:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.MEDIUM
    
    def _process_deadlines(self, raw_deadlines: List[Dict[str, Any]], 
                          content: str, context: Dict[str, Any]) -> List[ExtractedDeadline]:
        """Process raw deadlines into structured ExtractedDeadline objects."""
        
        processed = []
        
        for raw in raw_deadlines:
            try:
                # Parse the date
                parsed_date = self._parse_date(raw['date_text'], context)
                if not parsed_date:
                    continue
                
                # Determine status
                status = self._determine_status(parsed_date)
                
                # Extract additional details
                details = self._extract_deadline_details(raw['context'], context)
                
                # Create ExtractedDeadline object
                deadline = ExtractedDeadline(
                    deadline_id="",  # Will be generated in __post_init__
                    date=parsed_date,
                    deadline_type=raw['deadline_type'],
                    priority=raw['priority'],
                    status=status,
                    confidence=raw['confidence'],
                    description=self._generate_description(raw['context'], raw['deadline_type']),
                    context=raw['context'],
                    action_required=self._extract_action_required(raw['context']),
                    source_document=context.get('document_id', 'Unknown'),
                    extracted_text=raw['date_text'],
                    extraction_method=raw['extraction_method'],
                    **details  # Additional extracted details
                )
                
                # Set alert schedule based on priority
                deadline.alert_days_before = self.warning_periods.get(
                    deadline.priority, [7, 3, 1]
                )
                
                processed.append(deadline)
                
            except Exception as e:
                logger.warning(f"Error processing deadline: {e}")
                continue
        
        return processed
    
    def _parse_date(self, date_text: str, context: Dict[str, Any]) -> Optional[datetime]:
        """Parse date text into datetime object."""
        
        try:
            # Handle relative dates
            if 'within' in date_text.lower() or 'after' in date_text.lower():
                return self._parse_relative_date(date_text, context)
            
            # Try standard date parsing
            parsed = date_parser.parse(date_text, fuzzy=True)
            
            # If year is missing or seems wrong, adjust
            if parsed.year < 2000:
                parsed = parsed.replace(year=datetime.now().year)
            
            return parsed
            
        except Exception as e:
            logger.debug(f"Could not parse date '{date_text}': {e}")
            return None
    
    def _parse_relative_date(self, date_text: str, context: Dict[str, Any]) -> Optional[datetime]:
        """Parse relative date expressions."""
        
        reference_date = context.get('reference_date', datetime.now())
        
        # Extract number and time unit
        match = re.search(r'(\d+)\s+(day|week|month|year)s?', date_text.lower())
        if not match:
            return None
        
        number = int(match.group(1))
        unit = match.group(2)
        
        # Calculate target date
        if unit == 'day':
            return reference_date + timedelta(days=number)
        elif unit == 'week':
            return reference_date + timedelta(weeks=number)
        elif unit == 'month':
            return reference_date + relativedelta(months=number)
        elif unit == 'year':
            return reference_date + relativedelta(years=number)
        
        return None
    
    def _determine_status(self, deadline_date: datetime) -> DeadlineStatus:
        """Determine the status of a deadline."""
        
        now = datetime.now()
        days_until = (deadline_date - now).days
        
        if days_until < 0:
            return DeadlineStatus.OVERDUE
        elif days_until <= 7:
            return DeadlineStatus.APPROACHING
        else:
            return DeadlineStatus.PENDING
    
    def _extract_deadline_details(self, context: str, doc_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract additional deadline details from context."""
        
        details = {}
        
        # Extract jurisdiction
        jurisdiction_match = re.search(r'\b(federal|state|california|new york|texas)\b', context.lower())
        if jurisdiction_match:
            details['jurisdiction'] = jurisdiction_match.group(1)
        
        # Extract court information
        court_match = re.search(r'\b([^.]*court[^.]*)\b', context, re.IGNORECASE)
        if court_match:
            details['court'] = court_match.group(1).strip()
        
        # Extract case number
        case_match = re.search(r'\b(?:case|civil|criminal)\s*(?:no\.?|number)\s*[:\-]?\s*([A-Z0-9\-:]+)\b', context, re.IGNORECASE)
        if case_match:
            details['case_number'] = case_match.group(1)
        
        # Extract rule or statute reference
        rule_patterns = [
            r'\b(FRCP\s+\d+[a-z]*(?:\([^)]+\))?)\b',
            r'\b(Fed\.?\s*R\.?\s*(?:Civ|Crim|App|Bankr)\.?\s*P\.?\s*\d+[a-z]*)\b',
            r'\b(\d+\s+U\.S\.C\.?\s*§?\s*\d+[a-z]*)\b'
        ]
        
        for pattern in rule_patterns:
            rule_match = re.search(pattern, context, re.IGNORECASE)
            if rule_match:
                details['rule_or_statute'] = rule_match.group(1)
                break
        
        # Extract responsible party
        party_patterns = [
            r'\b(plaintiff|defendant|appellant|appellee|petitioner|respondent)\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+(?:must|shall|is\s+required))\b'
        ]
        
        for pattern in party_patterns:
            party_match = re.search(pattern, context, re.IGNORECASE)
            if party_match:
                details['responsible_party'] = party_match.group(1)
                break
        
        # Extract response time
        response_match = re.search(r'\bwithin\s+(\d+)\s+days?\b', context.lower())
        if response_match:
            details['response_time_days'] = int(response_match.group(1))
        
        return details
    
    def _generate_description(self, context: str, deadline_type: DeadlineType) -> str:
        """Generate a concise description of the deadline."""
        
        # Extract key action words
        action_words = []
        
        action_patterns = [
            r'\b(file|serve|submit|lodge|respond|answer|reply|appear|pay)\b',
            r'\b(motion|brief|complaint|answer|discovery|response)\b'
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, context.lower())
            action_words.extend(matches)
        
        if action_words:
            unique_words = list(set(action_words))
            description = f"{deadline_type.value.title()}: {' '.join(unique_words[:3])}"
        else:
            description = f"{deadline_type.value.title()} deadline"
        
        return description[:100]  # Limit length
    
    def _extract_action_required(self, context: str) -> str:
        """Extract the specific action required for the deadline."""
        
        # Look for imperative verbs and requirements
        action_patterns = [
            r'(?:must|shall|required to|need to)\s+([^.!?]+[.!?])',
            r'(?:file|serve|submit|lodge)\s+([^.!?]+[.!?])'
        ]
        
        for pattern in action_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "See document for specific requirements"
    
    def _validate_deadlines(self, deadlines: List[ExtractedDeadline], 
                           context: Dict[str, Any]) -> List[ExtractedDeadline]:
        """Validate and enrich extracted deadlines."""
        
        validated = []
        
        for deadline in deadlines:
            # Validate date reasonableness
            if self._is_reasonable_date(deadline.date):
                # Enrich with rule-based knowledge
                self._enrich_with_rules(deadline, context)
                
                # Add validation notes
                deadline.validation_notes = self._generate_validation_notes(deadline)
                
                validated.append(deadline)
            else:
                logger.debug(f"Rejected unreasonable date: {deadline.date}")
        
        return validated
    
    def _is_reasonable_date(self, date: datetime) -> bool:
        """Check if a date is reasonable for a legal deadline."""
        
        now = datetime.now()
        
        # Must be within reasonable range (not too far past or future)
        min_date = now - timedelta(days=365)  # Up to 1 year in past
        max_date = now + timedelta(days=365 * 5)  # Up to 5 years in future
        
        return min_date <= date <= max_date
    
    def _enrich_with_rules(self, deadline: ExtractedDeadline, context: Dict[str, Any]):
        """Enrich deadline with rule-based knowledge."""
        
        # Check against known rule deadlines
        deadline_rules = {
            **self.frcp_deadlines,
            **self.frbp_deadlines,
            **self.appeal_deadlines
        }
        
        # Try to match deadline type to known rules
        deadline_key = deadline.deadline_type.value.lower()
        
        for rule_key, rule_info in deadline_rules.items():
            if deadline_key in rule_key or rule_key in deadline_key:
                if not deadline.rule_or_statute:
                    deadline.rule_or_statute = rule_info.get('rule', '')
                
                if not deadline.response_time_days:
                    deadline.response_time_days = rule_info.get('days')
                
                # Update description if generic
                if len(deadline.description) < 20:
                    deadline.description = rule_info.get('description', deadline.description)
                
                break
    
    def _generate_validation_notes(self, deadline: ExtractedDeadline) -> List[str]:
        """Generate validation notes for a deadline."""
        
        notes = []
        
        # Confidence-based notes
        if deadline.confidence in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]:
            notes.append("Low confidence extraction - manual review recommended")
        
        # Date-based notes
        days_until = (deadline.date - datetime.now()).days
        if days_until < 0:
            notes.append("Deadline appears to be in the past")
        elif days_until < 3:
            notes.append("Urgent deadline - immediate attention required")
        
        # Priority-based notes
        if deadline.priority == PriorityLevel.CRITICAL:
            notes.append("Critical deadline - jurisdictional or case-ending")
        
        # Rule-based notes
        if not deadline.rule_or_statute:
            notes.append("No specific rule or statute identified")
        
        return notes
    
    def _create_deadline_relationships(self, deadlines: List[ExtractedDeadline]):
        """Create relationships between related deadlines."""
        
        # Group deadlines by type and date proximity
        deadline_groups = defaultdict(list)
        
        for deadline in deadlines:
            key = (deadline.deadline_type, deadline.date.month)
            deadline_groups[key].append(deadline)
        
        # Identify dependencies and triggers
        for group in deadline_groups.values():
            if len(group) > 1:
                # Sort by date
                group.sort(key=lambda x: x.date)
                
                # Create sequential relationships
                for i in range(len(group) - 1):
                    current = group[i]
                    next_deadline = group[i + 1]
                    
                    # Check if one triggers the other
                    if (next_deadline.date - current.date).days <= 30:
                        current.triggers.append(next_deadline.deadline_id)
                        next_deadline.depends_on.append(current.deadline_id)
                        next_deadline.related_deadlines.append(current.deadline_id)
                        current.related_deadlines.append(next_deadline.deadline_id)
    
    def _generate_analysis(self, deadlines: List[ExtractedDeadline], 
                          document_id: str) -> DeadlineAnalysis:
        """Generate comprehensive deadline analysis."""
        
        analysis = DeadlineAnalysis(
            analysis_id=f"analysis_{document_id}_{int(datetime.utcnow().timestamp())}",
            document_id=document_id,
            deadlines=deadlines
        )
        
        # Calculate metrics
        analysis.total_deadlines = len(deadlines)
        analysis.critical_deadlines = sum(1 for d in deadlines if d.priority == PriorityLevel.CRITICAL)
        analysis.approaching_deadlines = sum(1 for d in deadlines if d.status == DeadlineStatus.APPROACHING)
        analysis.overdue_deadlines = sum(1 for d in deadlines if d.status == DeadlineStatus.OVERDUE)
        
        # Type distribution
        analysis.deadline_type_counts = {}
        for deadline in deadlines:
            dt = deadline.deadline_type
            analysis.deadline_type_counts[dt] = analysis.deadline_type_counts.get(dt, 0) + 1
        
        # Time analysis
        if deadlines:
            dates = [d.date for d in deadlines]
            analysis.earliest_deadline = min(dates)
            analysis.latest_deadline = max(dates)
            
            # Calculate deadline density (deadlines per month)
            if analysis.latest_deadline and analysis.earliest_deadline:
                time_span_months = (analysis.latest_deadline - analysis.earliest_deadline).days / 30.0
                analysis.deadline_density = len(deadlines) / max(time_span_months, 1.0)
        
        # Quality metrics
        analysis.high_confidence_count = sum(
            1 for d in deadlines 
            if d.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]
        )
        analysis.requires_validation_count = sum(
            1 for d in deadlines 
            if d.confidence in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]
        )
        
        # Generate recommendations
        analysis.priority_actions = self._generate_priority_actions(deadlines)
        analysis.calendar_entries = self._generate_calendar_entries(deadlines)
        
        return analysis
    
    def _generate_priority_actions(self, deadlines: List[ExtractedDeadline]) -> List[str]:
        """Generate priority actions based on deadlines."""
        
        actions = []
        
        # Critical and overdue deadlines
        critical_overdue = [d for d in deadlines 
                           if d.status == DeadlineStatus.OVERDUE and d.priority == PriorityLevel.CRITICAL]
        
        if critical_overdue:
            actions.append(f"URGENT: {len(critical_overdue)} critical deadline(s) are overdue - immediate action required")
        
        # Approaching critical deadlines
        critical_approaching = [d for d in deadlines 
                              if d.status == DeadlineStatus.APPROACHING and d.priority == PriorityLevel.CRITICAL]
        
        if critical_approaching:
            actions.append(f"CRITICAL: {len(critical_approaching)} critical deadline(s) approaching within 7 days")
        
        # High volume of deadlines in next 30 days
        upcoming = [d for d in deadlines 
                   if d.status in [DeadlineStatus.PENDING, DeadlineStatus.APPROACHING] 
                   and (d.date - datetime.now()).days <= 30]
        
        if len(upcoming) > 5:
            actions.append(f"High deadline volume: {len(upcoming)} deadlines in next 30 days - prioritization needed")
        
        # Low confidence extractions
        low_confidence = [d for d in deadlines 
                         if d.confidence in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]]
        
        if len(low_confidence) > 2:
            actions.append(f"Manual review needed: {len(low_confidence)} deadline(s) with low extraction confidence")
        
        return actions
    
    def _generate_calendar_entries(self, deadlines: List[ExtractedDeadline]) -> List[Dict[str, Any]]:
        """Generate calendar entries for deadlines."""
        
        entries = []
        
        for deadline in deadlines:
            # Main deadline entry
            entries.append({
                'title': deadline.description,
                'date': deadline.date.isoformat(),
                'type': 'deadline',
                'priority': deadline.priority.value,
                'description': deadline.action_required,
                'alert_type': 'deadline_due',
                'metadata': {
                    'deadline_id': deadline.deadline_id,
                    'deadline_type': deadline.deadline_type.value,
                    'confidence': deadline.confidence.value
                }
            })
            
            # Alert entries
            for days_before in deadline.alert_days_before:
                alert_date = deadline.date - timedelta(days=days_before)
                if alert_date > datetime.now():
                    entries.append({
                        'title': f"ALERT: {deadline.description} due in {days_before} day(s)",
                        'date': alert_date.isoformat(),
                        'type': 'alert',
                        'priority': deadline.priority.value,
                        'description': f"Reminder: {deadline.action_required}",
                        'alert_type': f'deadline_alert_{days_before}d',
                        'metadata': {
                            'deadline_id': deadline.deadline_id,
                            'days_until_deadline': days_before
                        }
                    })
        
        return sorted(entries, key=lambda x: x['date'])
    
    def update_deadline_status(self, deadline_id: str, new_status: DeadlineStatus, 
                              notes: str = "") -> bool:
        """Update the status of a deadline."""
        
        # Find deadline in cache
        for analysis in self.deadline_cache.values():
            for deadline in analysis.deadlines:
                if deadline.deadline_id == deadline_id:
                    deadline.status = new_status
                    if notes:
                        deadline.validation_notes.append(f"Status update: {notes}")
                    return True
        
        return False
    
    def extend_deadline(self, deadline_id: str, new_date: datetime, 
                       reason: str = "") -> bool:
        """Extend a deadline to a new date."""
        
        # Find deadline in cache
        for analysis in self.deadline_cache.values():
            for deadline in analysis.deadlines:
                if deadline.deadline_id == deadline_id:
                    if deadline.can_be_extended:
                        if not deadline.original_date:
                            deadline.original_date = deadline.date
                        
                        deadline.date = new_date
                        deadline.extension_count += 1
                        deadline.status = self._determine_status(new_date)
                        
                        if reason:
                            deadline.validation_notes.append(f"Extended: {reason}")
                        
                        return True
        
        return False
    
    def export_deadlines(self, analysis: DeadlineAnalysis, format: str = "json") -> str:
        """Export deadline analysis in specified format."""
        
        if format.lower() == "json":
            # Convert to JSON-serializable format
            data = {
                "analysis_id": analysis.analysis_id,
                "document_id": analysis.document_id,
                "analysis_timestamp": analysis.analysis_timestamp.isoformat(),
                "summary": {
                    "total_deadlines": analysis.total_deadlines,
                    "critical_deadlines": analysis.critical_deadlines,
                    "approaching_deadlines": analysis.approaching_deadlines,
                    "overdue_deadlines": analysis.overdue_deadlines,
                    "earliest_deadline": analysis.earliest_deadline.isoformat() if analysis.earliest_deadline else None,
                    "latest_deadline": analysis.latest_deadline.isoformat() if analysis.latest_deadline else None
                },
                "deadlines": [
                    {
                        "deadline_id": d.deadline_id,
                        "date": d.date.isoformat(),
                        "deadline_type": d.deadline_type.value,
                        "priority": d.priority.value,
                        "status": d.status.value,
                        "confidence": d.confidence.value,
                        "description": d.description,
                        "action_required": d.action_required,
                        "rule_or_statute": d.rule_or_statute,
                        "responsible_party": d.responsible_party,
                        "alert_days_before": d.alert_days_before,
                        "validation_notes": d.validation_notes,
                        "metadata": d.metadata
                    }
                    for d in analysis.deadlines
                ],
                "priority_actions": analysis.priority_actions,
                "calendar_entries": analysis.calendar_entries
            }
            
            return json.dumps(data, indent=2, default=str)
            
        elif format.lower() == "csv":
            # Convert to CSV format
            rows = []
            for deadline in analysis.deadlines:
                rows.append({
                    "Deadline ID": deadline.deadline_id,
                    "Date": deadline.date.strftime("%Y-%m-%d"),
                    "Type": deadline.deadline_type.value,
                    "Priority": deadline.priority.value,
                    "Status": deadline.status.value,
                    "Confidence": deadline.confidence.value,
                    "Description": deadline.description,
                    "Action Required": deadline.action_required,
                    "Rule/Statute": deadline.rule_or_statute or "",
                    "Responsible Party": deadline.responsible_party or "",
                    "Days Until": (deadline.date - datetime.now()).days
                })
            
            df = pd.DataFrame(rows)
            return df.to_csv(index=False)
            
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_extraction_statistics(self) -> Dict[str, Any]:
        """Get deadline extraction statistics."""
        
        return {
            "supported_deadline_types": [dt.value for dt in DeadlineType],
            "priority_levels": [pl.value for pl in PriorityLevel],
            "confidence_levels": [cl.value for cl in ConfidenceLevel],
            "status_types": [ds.value for ds in DeadlineStatus],
            "extraction_methods": ["pattern_matching", "nlp_entity", "ml_model"],
            "rule_databases": {
                "frcp_rules": len(self.frcp_deadlines),
                "frbp_rules": len(self.frbp_deadlines),
                "appeal_rules": len(self.appeal_deadlines),
                "state_variations": len(self.state_variations)
            },
            "date_patterns": len(self.date_patterns),
            "trigger_patterns": sum(len(patterns) for patterns in self.deadline_triggers.values()),
            "nlp_model": self.nlp_model,
            "cache_size": len(self.deadline_cache)
        }