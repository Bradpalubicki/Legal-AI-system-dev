"""
Advanced timeline extraction engine for legal documents.
Extracts chronological events, dates, and temporal relationships from legal text.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta, date
import json
from collections import defaultdict
import calendar

import spacy
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import pandas as pd

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events that can be extracted."""
    FILING = "filing"                  # Document filings
    HEARING = "hearing"                # Court hearings
    MOTION = "motion"                  # Legal motions
    ORDER = "order"                    # Court orders
    DISCOVERY = "discovery"            # Discovery events
    DEPOSITION = "deposition"          # Depositions
    SETTLEMENT = "settlement"          # Settlement events
    TRIAL = "trial"                    # Trial events
    CONTRACT = "contract"              # Contract events
    DEADLINE = "deadline"              # Important deadlines
    COMMUNICATION = "communication"    # Communications
    TRANSACTION = "transaction"        # Business transactions
    INCIDENT = "incident"              # Incidents/occurrences
    MEETING = "meeting"                # Meetings
    NOTIFICATION = "notification"      # Notices/notifications
    PAYMENT = "payment"                # Payment events
    REGULATORY = "regulatory"          # Regulatory actions
    CORPORATE = "corporate"            # Corporate actions
    EMPLOYMENT = "employment"          # Employment events
    UNKNOWN = "unknown"                # Unclassified events


class EventCertainty(Enum):
    """Certainty levels for extracted events."""
    CERTAIN = "certain"                # Definite occurrence
    PROBABLE = "probable"              # Likely occurred
    POSSIBLE = "possible"              # May have occurred
    SCHEDULED = "scheduled"            # Future planned event
    CONDITIONAL = "conditional"        # Conditional occurrence
    UNCERTAIN = "uncertain"            # Unclear if occurred


class TemporalContext(Enum):
    """Temporal context of events."""
    PAST = "past"                      # Past event
    PRESENT = "present"                # Current/ongoing
    FUTURE = "future"                  # Future event
    RECURRING = "recurring"            # Recurring event
    DURATION = "duration"              # Event with duration
    DEADLINE = "deadline"              # Deadline event


@dataclass
class TemporalExpression:
    """Represents a temporal expression found in text."""
    raw_text: str
    normalized_date: Optional[datetime]
    date_range: Optional[Tuple[datetime, datetime]]
    temporal_type: str  # absolute, relative, recurring
    confidence: float
    start_position: int
    end_position: int
    context: str
    parsing_method: str


@dataclass
class TimelineEvent:
    """Represents a chronological event extracted from text."""
    event_id: str
    event_type: EventType
    description: str
    date: Optional[datetime]
    date_range: Optional[Tuple[datetime, datetime]]
    certainty: EventCertainty
    temporal_context: TemporalContext
    confidence: float
    
    # Text location
    start_position: int
    end_position: int
    source_sentence: str
    
    # Contextual information
    participants: List[str] = field(default_factory=list)
    location: Optional[str] = None
    amount: Optional[str] = None
    reference_number: Optional[str] = None
    
    # Relationships
    caused_by: List[str] = field(default_factory=list)
    leads_to: List[str] = field(default_factory=list)
    concurrent_with: List[str] = field(default_factory=list)
    
    # Metadata
    extraction_method: str = ""
    source_document: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"event_{hash(self.description + str(self.date))}"


@dataclass
class Timeline:
    """Represents a complete timeline of events."""
    timeline_id: str
    title: str
    events: List[TimelineEvent] = field(default_factory=list)
    date_range: Optional[Tuple[datetime, datetime]] = None
    confidence_score: float = 0.0
    
    # Timeline metadata
    total_events: int = 0
    event_types: Set[EventType] = field(default_factory=set)
    participants: Set[str] = field(default_factory=set)
    source_documents: Set[str] = field(default_factory=set)
    
    # Analysis results
    key_events: List[str] = field(default_factory=list)
    event_clusters: Dict[str, List[str]] = field(default_factory=dict)
    causal_chains: List[List[str]] = field(default_factory=list)
    
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)


class TimelineExtractor:
    """Advanced timeline extraction engine for legal documents."""
    
    def __init__(self, nlp_model: str = "en_core_web_sm"):
        """Initialize timeline extractor.
        
        Args:
            nlp_model: spaCy model for NLP processing
        """
        self.nlp_model = nlp_model
        self.nlp = None
        
        # Initialize extraction patterns and models
        self._initialize_patterns()
        self._initialize_models()
        
        # Event extraction cache
        self.event_cache: Dict[str, List[TimelineEvent]] = {}
        
    def _initialize_patterns(self):
        """Initialize regex patterns for timeline extraction."""
        
        # Date patterns with various formats
        self.date_patterns = {
            'absolute_dates': [
                r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b',  # MM/DD/YYYY
                r'\b(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b',    # YYYY-MM-DD
                r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
                r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b',
                r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})\b'
            ],
            'relative_dates': [
                r'\b((?:on|by|before|after|within|during|until|since)\s+(?:the\s+)?(?:\d{1,2}(?:st|nd|rd|th)?\s+)?(?:day|week|month|year|business day)s?\s+(?:of|from|after|before)?\s*[^.!?]*)\b',
                r'\b((?:next|last|this|following|previous|prior)\s+(?:week|month|year|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))\b',
                r'\b((?:\d+)\s+(?:days?|weeks?|months?|years?)\s+(?:ago|later|hence|from\s+now|after|before))\b',
                r'\b((?:yesterday|today|tomorrow|the\s+day\s+(?:before|after)))\b'
            ],
            'time_ranges': [
                r'\b(from\s+[^.!?]+\s+(?:to|through|until)\s+[^.!?]+)\b',
                r'\b(between\s+[^.!?]+\s+and\s+[^.!?]+)\b',
                r'\b(during\s+the\s+period\s+[^.!?]+)\b'
            ],
            'recurring_dates': [
                r'\b((?:every|each)\s+(?:day|week|month|year|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))\b',
                r'\b((?:daily|weekly|monthly|yearly|annually|quarterly))\b',
                r'\b(on\s+the\s+\d{1,2}(?:st|nd|rd|th)\s+of\s+(?:each|every)\s+month)\b'
            ]
        }
        
        # Event trigger patterns for different event types
        self.event_patterns = {
            EventType.FILING: [
                r'\b(?:filed|filing|file|submitted|submitting|lodged)\b',
                r'\b(?:petition|complaint|answer|motion|brief|pleading)\s+(?:was|is|has been)?\s*(?:filed|submitted)\b'
            ],
            EventType.HEARING: [
                r'\b(?:hearing|oral argument|conference|appearance)\b',
                r'\b(?:scheduled|set|noticed)\s+(?:for\s+)?(?:hearing|oral argument)\b',
                r'\b(?:appear|appeared|appearing)\s+(?:before|in)\s+court\b'
            ],
            EventType.MOTION: [
                r'\b(?:moved|moves|moving|motion)\s+(?:for|to)\b',
                r'\b(?:requests?|seeking|seeks)\s+(?:that\s+)?(?:the\s+)?court\b'
            ],
            EventType.ORDER: [
                r'\b(?:ordered|orders|ordering|decreed|adjudged)\b',
                r'\b(?:court\s+)?(?:order|decree|judgment|ruling)\b',
                r'\b(?:it\s+is\s+)?(?:hereby\s+)?(?:ordered|decreed|adjudged)\b'
            ],
            EventType.DISCOVERY: [
                r'\b(?:discovery|interrogatories|deposition|document\s+production)\b',
                r'\b(?:served|serving|propounded)\s+(?:discovery|interrogatories)\b',
                r'\b(?:responses?\s+to|answered)\s+(?:discovery|interrogatories)\b'
            ],
            EventType.DEPOSITION: [
                r'\b(?:deposition|deposed|examined|testimony)\b',
                r'\b(?:noticed|scheduled)\s+(?:for\s+)?deposition\b'
            ],
            EventType.SETTLEMENT: [
                r'\b(?:settled|settlement|resolved|resolution)\b',
                r'\b(?:agreed|agreement)\s+(?:to\s+)?settle\b',
                r'\bmediatio[n]\b'
            ],
            EventType.TRIAL: [
                r'\b(?:trial|jury\s+trial|bench\s+trial)\b',
                r'\b(?:trial\s+(?:began|commenced|started|ended|concluded))\b'
            ],
            EventType.CONTRACT: [
                r'\b(?:signed|executed|entered\s+into|agreed)\s+(?:a\s+|the\s+)?(?:contract|agreement)\b',
                r'\b(?:contract|agreement)\s+(?:was|is)\s+(?:signed|executed)\b'
            ],
            EventType.DEADLINE: [
                r'\b(?:deadline|due\s+date|expires?|expiration)\b',
                r'\b(?:must|shall)\s+(?:be\s+)?(?:filed|submitted|served)\s+(?:by|before|on)\b'
            ],
            EventType.COMMUNICATION: [
                r'\b(?:called|telephoned|emailed|wrote|sent|received)\b',
                r'\b(?:letter|email|phone\s+call|communication)\b'
            ],
            EventType.PAYMENT: [
                r'\b(?:paid|payment|received|disbursed|remitted)\b',
                r'\b\$[\d,]+\.?\d*\s+(?:was|were)\s+(?:paid|received)\b'
            ],
            EventType.MEETING: [
                r'\b(?:met|meeting|conference|discussed)\b',
                r'\b(?:attended|participated\s+in)\s+(?:a\s+)?meeting\b'
            ]
        }
        
        # Temporal context indicators
        self.temporal_indicators = {
            'past': [r'\b(?:had|was|were|did|occurred|happened|took\s+place)\b'],
            'present': [r'\b(?:is|are|does|occurs?|happens?|takes?\s+place)\b'],
            'future': [r'\b(?:will|shall|going\s+to|scheduled\s+to|planned\s+to)\b'],
            'conditional': [r'\b(?:if|unless|provided\s+that|in\s+the\s+event\s+that)\b']
        }
        
        # Certainty indicators
        self.certainty_indicators = {
            EventCertainty.CERTAIN: [
                r'\b(?:did|was|were|had|occurred|happened|took\s+place)\b'
            ],
            EventCertainty.PROBABLE: [
                r'\b(?:likely|probably|appears?\s+to|seems?\s+to)\b'
            ],
            EventCertainty.POSSIBLE: [
                r'\b(?:may|might|could|possibly|perhaps)\b'
            ],
            EventCertainty.SCHEDULED: [
                r'\b(?:scheduled|planned|set\s+for|noticed\s+for)\b'
            ],
            EventCertainty.CONDITIONAL: [
                r'\b(?:if|unless|provided\s+that|in\s+the\s+event)\b'
            ]
        }
        
        # Participant extraction patterns
        self.participant_patterns = [
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+(?:filed|moved|requested|argued))\b',  # Person names
            r'\b([A-Z][A-Za-z\s]+(?:Corp|Inc|LLC|Ltd|Co)\.?)(?:\s+(?:filed|moved))\b',  # Company names
            r'\b(?:plaintiff|defendant|petitioner|respondent)\s+([A-Z][A-Za-z\s]+)\b'   # Party names
        ]
        
        # Amount extraction patterns
        self.amount_patterns = [
            r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|k|m|b))?',
            r'(?:\$\s*)?[\d,]+(?:\.\d{2})?\s+dollars?'
        ]
    
    def _initialize_models(self):
        """Initialize NLP models and processors."""
        try:
            # Load spaCy model
            self.nlp = spacy.load(self.nlp_model)
            
            # Add custom pipeline components if needed
            if "custom_temporal" not in self.nlp.pipe_names:
                # Could add custom temporal entity recognition here
                pass
                
            logger.info(f"Loaded spaCy model: {self.nlp_model}")
            
        except Exception as e:
            logger.error(f"Error initializing NLP models: {e}")
            self.nlp = None
    
    def extract_timeline(self, content: str, document_id: str = "", 
                        reference_date: datetime = None) -> Timeline:
        """Extract complete timeline from document content.
        
        Args:
            content: Document text content
            document_id: Optional document identifier
            reference_date: Reference date for relative date resolution
            
        Returns:
            Complete timeline with extracted events
        """
        logger.info(f"Extracting timeline from document: {document_id}")
        
        reference_date = reference_date or datetime.utcnow()
        
        # Extract temporal expressions first
        temporal_expressions = self._extract_temporal_expressions(content, reference_date)
        
        # Extract events with temporal information
        events = self._extract_events(content, temporal_expressions, document_id)
        
        # Resolve temporal relationships
        events = self._resolve_temporal_relationships(events)
        
        # Sort events chronologically
        sorted_events = self._sort_events_chronologically(events)
        
        # Create timeline
        timeline = Timeline(
            timeline_id=f"timeline_{document_id}_{int(datetime.utcnow().timestamp())}",
            title=f"Timeline for {document_id}" if document_id else "Document Timeline",
            events=sorted_events
        )
        
        # Analyze timeline
        self._analyze_timeline(timeline)
        
        return timeline
    
    def _extract_temporal_expressions(self, content: str, 
                                    reference_date: datetime) -> List[TemporalExpression]:
        """Extract all temporal expressions from text."""
        expressions = []
        
        # Extract absolute dates
        for pattern in self.date_patterns['absolute_dates']:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                expr = self._parse_absolute_date(
                    match.group(1), match.start(), match.end(), content
                )
                if expr:
                    expressions.append(expr)
        
        # Extract relative dates
        for pattern in self.date_patterns['relative_dates']:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                expr = self._parse_relative_date(
                    match.group(1), match.start(), match.end(), 
                    content, reference_date
                )
                if expr:
                    expressions.append(expr)
        
        # Extract time ranges
        for pattern in self.date_patterns['time_ranges']:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                expr = self._parse_time_range(
                    match.group(1), match.start(), match.end(), 
                    content, reference_date
                )
                if expr:
                    expressions.append(expr)
        
        # Extract recurring dates
        for pattern in self.date_patterns['recurring_dates']:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                expr = self._parse_recurring_date(
                    match.group(1), match.start(), match.end(), content
                )
                if expr:
                    expressions.append(expr)
        
        # Use spaCy for additional temporal entity recognition
        if self.nlp:
            expressions.extend(self._extract_temporal_with_nlp(content, reference_date))
        
        return expressions
    
    def _parse_absolute_date(self, date_str: str, start: int, end: int, 
                           content: str) -> Optional[TemporalExpression]:
        """Parse absolute date string."""
        try:
            parsed_date = date_parser.parse(date_str, fuzzy=False)
            
            # Get context around the date
            context_start = max(0, start - 50)
            context_end = min(len(content), end + 50)
            context = content[context_start:context_end]
            
            return TemporalExpression(
                raw_text=date_str,
                normalized_date=parsed_date,
                date_range=None,
                temporal_type="absolute",
                confidence=0.9,
                start_position=start,
                end_position=end,
                context=context,
                parsing_method="dateutil"
            )
        except (ValueError, TypeError) as e:
            logger.debug(f"Could not parse absolute date '{date_str}': {e}")
            return None
    
    def _parse_relative_date(self, date_str: str, start: int, end: int,
                           content: str, reference_date: datetime) -> Optional[TemporalExpression]:
        """Parse relative date string."""
        try:
            date_str_lower = date_str.lower()
            parsed_date = None
            
            # Handle common relative expressions
            if 'yesterday' in date_str_lower:
                parsed_date = reference_date - timedelta(days=1)
            elif 'today' in date_str_lower:
                parsed_date = reference_date
            elif 'tomorrow' in date_str_lower:
                parsed_date = reference_date + timedelta(days=1)
            elif 'next week' in date_str_lower:
                parsed_date = reference_date + timedelta(weeks=1)
            elif 'last week' in date_str_lower:
                parsed_date = reference_date - timedelta(weeks=1)
            elif 'next month' in date_str_lower:
                parsed_date = reference_date + relativedelta(months=1)
            elif 'last month' in date_str_lower:
                parsed_date = reference_date - relativedelta(months=1)
            elif 'next year' in date_str_lower:
                parsed_date = reference_date + relativedelta(years=1)
            elif 'last year' in date_str_lower:
                parsed_date = reference_date - relativedelta(years=1)
            else:
                # Try to parse with dateutil using reference date
                parsed_date = date_parser.parse(date_str, default=reference_date, fuzzy=True)
            
            if parsed_date:
                context_start = max(0, start - 50)
                context_end = min(len(content), end + 50)
                context = content[context_start:context_end]
                
                return TemporalExpression(
                    raw_text=date_str,
                    normalized_date=parsed_date,
                    date_range=None,
                    temporal_type="relative",
                    confidence=0.7,
                    start_position=start,
                    end_position=end,
                    context=context,
                    parsing_method="relative_parser"
                )
        except Exception as e:
            logger.debug(f"Could not parse relative date '{date_str}': {e}")
            
        return None
    
    def _parse_time_range(self, range_str: str, start: int, end: int,
                         content: str, reference_date: datetime) -> Optional[TemporalExpression]:
        """Parse time range string."""
        try:
            range_str_lower = range_str.lower()
            
            # Extract start and end dates from range
            if 'from' in range_str_lower and ('to' in range_str_lower or 'until' in range_str_lower):
                parts = re.split(r'\s+(?:to|until|through)\s+', range_str_lower, maxsplit=1)
                if len(parts) == 2:
                    start_part = parts[0].replace('from', '').strip()
                    end_part = parts[1].strip()
                    
                    start_date = date_parser.parse(start_part, default=reference_date, fuzzy=True)
                    end_date = date_parser.parse(end_part, default=reference_date, fuzzy=True)
                    
                    context_start = max(0, start - 50)
                    context_end = min(len(content), end + 50)
                    context = content[context_start:context_end]
                    
                    return TemporalExpression(
                        raw_text=range_str,
                        normalized_date=start_date,
                        date_range=(start_date, end_date),
                        temporal_type="range",
                        confidence=0.8,
                        start_position=start,
                        end_position=end,
                        context=context,
                        parsing_method="range_parser"
                    )
            elif 'between' in range_str_lower and 'and' in range_str_lower:
                parts = range_str_lower.split('and', 1)
                if len(parts) == 2:
                    start_part = parts[0].replace('between', '').strip()
                    end_part = parts[1].strip()
                    
                    start_date = date_parser.parse(start_part, default=reference_date, fuzzy=True)
                    end_date = date_parser.parse(end_part, default=reference_date, fuzzy=True)
                    
                    context_start = max(0, start - 50)
                    context_end = min(len(content), end + 50)
                    context = content[context_start:context_end]
                    
                    return TemporalExpression(
                        raw_text=range_str,
                        normalized_date=start_date,
                        date_range=(start_date, end_date),
                        temporal_type="range",
                        confidence=0.8,
                        start_position=start,
                        end_position=end,
                        context=context,
                        parsing_method="range_parser"
                    )
                    
        except Exception as e:
            logger.debug(f"Could not parse time range '{range_str}': {e}")
            
        return None
    
    def _parse_recurring_date(self, recur_str: str, start: int, end: int,
                             content: str) -> Optional[TemporalExpression]:
        """Parse recurring date string."""
        context_start = max(0, start - 50)
        context_end = min(len(content), end + 50)
        context = content[context_start:context_end]
        
        return TemporalExpression(
            raw_text=recur_str,
            normalized_date=None,  # Recurring dates don't have single dates
            date_range=None,
            temporal_type="recurring",
            confidence=0.8,
            start_position=start,
            end_position=end,
            context=context,
            parsing_method="recurring_parser"
        )
    
    def _extract_temporal_with_nlp(self, content: str, 
                                  reference_date: datetime) -> List[TemporalExpression]:
        """Extract temporal expressions using spaCy NLP."""
        expressions = []
        
        try:
            doc = self.nlp(content[:100000])  # Limit for performance
            
            for ent in doc.ents:
                if ent.label_ in ["DATE", "TIME"]:
                    try:
                        # Try to parse the entity text as a date
                        parsed_date = date_parser.parse(ent.text, default=reference_date, fuzzy=True)
                        
                        expressions.append(TemporalExpression(
                            raw_text=ent.text,
                            normalized_date=parsed_date,
                            date_range=None,
                            temporal_type="nlp_extracted",
                            confidence=0.6,  # Lower confidence for NLP extraction
                            start_position=ent.start_char,
                            end_position=ent.end_char,
                            context=ent.sent.text[:200],
                            parsing_method="spacy_ner"
                        ))
                    except (ValueError, TypeError):
                        # Keep as temporal expression even if not parseable
                        expressions.append(TemporalExpression(
                            raw_text=ent.text,
                            normalized_date=None,
                            date_range=None,
                            temporal_type="nlp_unparsed",
                            confidence=0.4,
                            start_position=ent.start_char,
                            end_position=ent.end_char,
                            context=ent.sent.text[:200],
                            parsing_method="spacy_ner"
                        ))
                        
        except Exception as e:
            logger.warning(f"NLP temporal extraction failed: {e}")
            
        return expressions
    
    def _extract_events(self, content: str, temporal_expressions: List[TemporalExpression],
                       document_id: str) -> List[TimelineEvent]:
        """Extract events from content using temporal expressions."""
        events = []
        sentences = self._split_into_sentences(content)
        
        for sentence_idx, sentence in enumerate(sentences):
            # Find temporal expressions in this sentence
            sentence_temporals = [
                te for te in temporal_expressions 
                if self._is_in_sentence(te.start_position, te.end_position, sentence, content)
            ]
            
            # Look for event triggers in the sentence
            for event_type, patterns in self.event_patterns.items():
                for pattern in patterns:
                    matches = list(re.finditer(pattern, sentence, re.IGNORECASE))
                    
                    for match in matches:
                        # Create event from pattern match
                        event = self._create_event_from_match(
                            match, sentence, sentence_temporals, event_type, 
                            document_id, sentence_idx
                        )
                        if event:
                            events.append(event)
        
        return events
    
    def _split_into_sentences(self, content: str) -> List[str]:
        """Split content into sentences."""
        if self.nlp:
            try:
                doc = self.nlp(content[:100000])  # Limit for performance
                return [sent.text for sent in doc.sents]
            except Exception:
                pass
        
        # Fallback to simple sentence splitting
        sentences = re.split(r'[.!?]+', content)
        return [s.strip() for s in sentences if s.strip()]
    
    def _is_in_sentence(self, start_pos: int, end_pos: int, sentence: str, content: str) -> bool:
        """Check if a position range is within a sentence."""
        sentence_start = content.find(sentence)
        if sentence_start == -1:
            return False
        
        sentence_end = sentence_start + len(sentence)
        return start_pos >= sentence_start and end_pos <= sentence_end
    
    def _create_event_from_match(self, match, sentence: str, 
                               temporal_expressions: List[TemporalExpression],
                               event_type: EventType, document_id: str,
                               sentence_idx: int) -> Optional[TimelineEvent]:
        """Create timeline event from pattern match."""
        
        # Get the best temporal expression for this event
        event_date = None
        date_range = None
        temporal_context = TemporalContext.PAST  # Default
        
        if temporal_expressions:
            # Use the first (closest) temporal expression
            best_temporal = temporal_expressions[0]
            event_date = best_temporal.normalized_date
            date_range = best_temporal.date_range
            
            # Determine temporal context
            if best_temporal.temporal_type == "future" or "scheduled" in best_temporal.context.lower():
                temporal_context = TemporalContext.FUTURE
            elif best_temporal.temporal_type == "recurring":
                temporal_context = TemporalContext.RECURRING
            elif date_range:
                temporal_context = TemporalContext.DURATION
        
        # Determine certainty
        certainty = self._determine_event_certainty(sentence)
        
        # Extract participants
        participants = self._extract_participants_from_sentence(sentence)
        
        # Extract amounts
        amount = self._extract_amount_from_sentence(sentence)
        
        # Extract location
        location = self._extract_location_from_sentence(sentence)
        
        # Generate event description
        description = self._generate_event_description(match.group(), sentence, event_type)
        
        # Calculate confidence
        confidence = self._calculate_event_confidence(
            match, temporal_expressions, event_type, sentence
        )
        
        event = TimelineEvent(
            event_id="",  # Will be generated in __post_init__
            event_type=event_type,
            description=description,
            date=event_date,
            date_range=date_range,
            certainty=certainty,
            temporal_context=temporal_context,
            confidence=confidence,
            start_position=match.start(),
            end_position=match.end(),
            source_sentence=sentence,
            participants=participants,
            location=location,
            amount=amount,
            extraction_method="pattern_matching",
            source_document=document_id,
            tags=[event_type.value]
        )
        
        return event
    
    def _determine_event_certainty(self, sentence: str) -> EventCertainty:
        """Determine certainty level of event from sentence."""
        sentence_lower = sentence.lower()
        
        for certainty, patterns in self.certainty_indicators.items():
            for pattern in patterns:
                if re.search(pattern, sentence_lower):
                    return certainty
        
        return EventCertainty.UNCERTAIN  # Default
    
    def _extract_participants_from_sentence(self, sentence: str) -> List[str]:
        """Extract participant names from sentence."""
        participants = []
        
        for pattern in self.participant_patterns:
            matches = re.findall(pattern, sentence)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]  # Take first group if tuple
                
                participant = match.strip()
                if len(participant) > 2 and participant not in participants:
                    participants.append(participant)
        
        return participants[:5]  # Limit to 5 participants
    
    def _extract_amount_from_sentence(self, sentence: str) -> Optional[str]:
        """Extract monetary amount from sentence."""
        for pattern in self.amount_patterns:
            match = re.search(pattern, sentence)
            if match:
                return match.group().strip()
        
        return None
    
    def _extract_location_from_sentence(self, sentence: str) -> Optional[str]:
        """Extract location from sentence using NLP."""
        if not self.nlp:
            return None
        
        try:
            doc = self.nlp(sentence)
            for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC"]:
                    return ent.text.strip()
        except Exception:
            pass
        
        return None
    
    def _generate_event_description(self, trigger_text: str, sentence: str, 
                                  event_type: EventType) -> str:
        """Generate descriptive text for the event."""
        # Clean and truncate sentence for description
        cleaned_sentence = re.sub(r'\s+', ' ', sentence).strip()
        
        if len(cleaned_sentence) > 200:
            # Find a good breaking point
            words = cleaned_sentence.split()
            truncated = ' '.join(words[:30])
            if len(truncated) < len(cleaned_sentence):
                truncated += "..."
            return truncated
        
        return cleaned_sentence
    
    def _calculate_event_confidence(self, match, temporal_expressions: List[TemporalExpression],
                                  event_type: EventType, sentence: str) -> float:
        """Calculate confidence score for event extraction."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence if we have temporal information
        if temporal_expressions:
            confidence += 0.2
            # Additional boost for high-confidence temporal expressions
            avg_temporal_confidence = sum(te.confidence for te in temporal_expressions) / len(temporal_expressions)
            confidence += avg_temporal_confidence * 0.2
        
        # Boost confidence for strong event triggers
        trigger_strength = {
            EventType.FILING: 0.3,
            EventType.ORDER: 0.3,
            EventType.HEARING: 0.2,
            EventType.SETTLEMENT: 0.3,
            EventType.CONTRACT: 0.3
        }
        confidence += trigger_strength.get(event_type, 0.1)
        
        # Boost confidence if sentence contains dates
        if re.search(r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b', sentence):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _resolve_temporal_relationships(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Resolve temporal relationships between events."""
        
        # Sort events by date for relationship analysis
        dated_events = [e for e in events if e.date]
        dated_events.sort(key=lambda e: e.date)
        
        # Identify causal relationships
        for i, event in enumerate(dated_events):
            # Look for events that might cause this event
            for j in range(max(0, i-3), i):  # Look at up to 3 preceding events
                prev_event = dated_events[j]
                if self._might_be_causal_relationship(prev_event, event):
                    event.caused_by.append(prev_event.event_id)
                    prev_event.leads_to.append(event.event_id)
            
            # Look for concurrent events (same date or very close)
            for other_event in dated_events:
                if (other_event != event and 
                    other_event.date and 
                    abs((event.date - other_event.date).days) <= 1):
                    
                    if other_event.event_id not in event.concurrent_with:
                        event.concurrent_with.append(other_event.event_id)
        
        return events
    
    def _might_be_causal_relationship(self, prev_event: TimelineEvent, 
                                    current_event: TimelineEvent) -> bool:
        """Determine if one event might cause another."""
        
        # Define causal patterns
        causal_patterns = {
            (EventType.FILING, EventType.HEARING): True,
            (EventType.MOTION, EventType.ORDER): True,
            (EventType.DISCOVERY, EventType.DEPOSITION): True,
            (EventType.HEARING, EventType.ORDER): True,
            (EventType.CONTRACT, EventType.PAYMENT): True,
            (EventType.INCIDENT, EventType.FILING): True
        }
        
        event_pair = (prev_event.event_type, current_event.event_type)
        return causal_patterns.get(event_pair, False)
    
    def _sort_events_chronologically(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Sort events in chronological order."""
        
        def sort_key(event):
            if event.date:
                return event.date
            elif event.date_range:
                return event.date_range[0]
            else:
                # Events without dates go to the end
                return datetime.max
        
        return sorted(events, key=sort_key)
    
    def _analyze_timeline(self, timeline: Timeline):
        """Perform comprehensive timeline analysis."""
        
        # Basic statistics
        timeline.total_events = len(timeline.events)
        timeline.event_types = {event.event_type for event in timeline.events}
        timeline.participants = {
            participant 
            for event in timeline.events 
            for participant in event.participants
        }
        timeline.source_documents = {
            event.source_document 
            for event in timeline.events 
            if event.source_document
        }
        
        # Calculate date range
        dated_events = [e for e in timeline.events if e.date]
        if dated_events:
            dates = [e.date for e in dated_events]
            timeline.date_range = (min(dates), max(dates))
        
        # Identify key events (high confidence or important types)
        key_event_types = {EventType.FILING, EventType.ORDER, EventType.SETTLEMENT, 
                          EventType.TRIAL, EventType.CONTRACT}
        
        timeline.key_events = [
            event.event_id for event in timeline.events
            if (event.event_type in key_event_types or 
                event.confidence > 0.8 or 
                event.certainty in [EventCertainty.CERTAIN, EventCertainty.SCHEDULED])
        ]
        
        # Create event clusters by type and time
        timeline.event_clusters = self._cluster_events(timeline.events)
        
        # Identify causal chains
        timeline.causal_chains = self._identify_causal_chains(timeline.events)
        
        # Calculate overall confidence
        if timeline.events:
            timeline.confidence_score = sum(e.confidence for e in timeline.events) / len(timeline.events)
        else:
            timeline.confidence_score = 0.0
    
    def _cluster_events(self, events: List[TimelineEvent]) -> Dict[str, List[str]]:
        """Cluster events by type and temporal proximity."""
        clusters = defaultdict(list)
        
        # Group by event type
        for event in events:
            clusters[f"type_{event.event_type.value}"].append(event.event_id)
        
        # Group by time periods (monthly clusters for dated events)
        dated_events = [e for e in events if e.date]
        monthly_groups = defaultdict(list)
        
        for event in dated_events:
            month_key = f"{event.date.year}_{event.date.month:02d}"
            monthly_groups[month_key].append(event.event_id)
        
        # Add monthly clusters
        for month, event_ids in monthly_groups.items():
            if len(event_ids) > 1:  # Only create cluster if multiple events
                clusters[f"month_{month}"] = event_ids
        
        return dict(clusters)
    
    def _identify_causal_chains(self, events: List[TimelineEvent]) -> List[List[str]]:
        """Identify chains of causally related events."""
        chains = []
        
        # Build a graph of causal relationships
        causal_graph = defaultdict(list)
        for event in events:
            for caused_by in event.caused_by:
                causal_graph[caused_by].append(event.event_id)
        
        # Find chains by following causal links
        visited = set()
        
        for event in events:
            if event.event_id not in visited and not event.caused_by:
                # This might be a chain start (no causes)
                chain = self._build_causal_chain(event.event_id, causal_graph, visited)
                if len(chain) > 2:  # Only keep chains with multiple events
                    chains.append(chain)
        
        return chains
    
    def _build_causal_chain(self, event_id: str, causal_graph: Dict[str, List[str]], 
                           visited: Set[str]) -> List[str]:
        """Build a causal chain starting from an event."""
        chain = [event_id]
        visited.add(event_id)
        
        # Follow the causal chain
        current = event_id
        while current in causal_graph:
            next_events = causal_graph[current]
            if next_events and next_events[0] not in visited:
                next_event = next_events[0]  # Take first if multiple
                chain.append(next_event)
                visited.add(next_event)
                current = next_event
            else:
                break
        
        return chain
    
    def merge_timelines(self, timelines: List[Timeline]) -> Timeline:
        """Merge multiple timelines into a single comprehensive timeline."""
        
        if not timelines:
            return Timeline(timeline_id="empty", title="Empty Timeline")
        
        if len(timelines) == 1:
            return timelines[0]
        
        # Combine all events
        all_events = []
        for timeline in timelines:
            all_events.extend(timeline.events)
        
        # Remove duplicate events (same description and date)
        unique_events = self._deduplicate_events(all_events)
        
        # Sort chronologically
        sorted_events = self._sort_events_chronologically(unique_events)
        
        # Resolve relationships across all events
        sorted_events = self._resolve_temporal_relationships(sorted_events)
        
        # Create merged timeline
        merged_timeline = Timeline(
            timeline_id=f"merged_{int(datetime.utcnow().timestamp())}",
            title=f"Merged Timeline ({len(timelines)} sources)",
            events=sorted_events
        )
        
        # Analyze merged timeline
        self._analyze_timeline(merged_timeline)
        
        return merged_timeline
    
    def _deduplicate_events(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Remove duplicate events from list."""
        seen = set()
        unique_events = []
        
        for event in events:
            # Create a key based on description, date, and type
            key = (
                event.description.lower().strip(),
                event.date.isoformat() if event.date else "no_date",
                event.event_type.value
            )
            
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        return unique_events
    
    def export_timeline(self, timeline: Timeline, format: str = "json") -> str:
        """Export timeline in specified format."""
        
        if format.lower() == "json":
            # Convert to JSON-serializable format
            data = {
                "timeline_id": timeline.timeline_id,
                "title": timeline.title,
                "date_range": [
                    timeline.date_range[0].isoformat() if timeline.date_range else None,
                    timeline.date_range[1].isoformat() if timeline.date_range else None
                ],
                "confidence_score": timeline.confidence_score,
                "total_events": timeline.total_events,
                "events": [
                    {
                        "event_id": event.event_id,
                        "event_type": event.event_type.value,
                        "description": event.description,
                        "date": event.date.isoformat() if event.date else None,
                        "date_range": [
                            event.date_range[0].isoformat() if event.date_range else None,
                            event.date_range[1].isoformat() if event.date_range else None
                        ],
                        "certainty": event.certainty.value,
                        "temporal_context": event.temporal_context.value,
                        "confidence": event.confidence,
                        "participants": event.participants,
                        "location": event.location,
                        "amount": event.amount,
                        "tags": event.tags
                    }
                    for event in timeline.events
                ]
            }
            
            return json.dumps(data, indent=2, default=str)
            
        elif format.lower() == "csv":
            # Convert to pandas DataFrame for CSV export
            rows = []
            for event in timeline.events:
                rows.append({
                    "Event ID": event.event_id,
                    "Type": event.event_type.value,
                    "Description": event.description,
                    "Date": event.date.isoformat() if event.date else "",
                    "Certainty": event.certainty.value,
                    "Confidence": event.confidence,
                    "Participants": "; ".join(event.participants),
                    "Location": event.location or "",
                    "Amount": event.amount or "",
                    "Tags": "; ".join(event.tags)
                })
            
            df = pd.DataFrame(rows)
            return df.to_csv(index=False)
            
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get timeline extraction statistics."""
        return {
            "nlp_model_loaded": self.nlp is not None,
            "supported_event_types": [et.value for et in EventType],
            "supported_certainty_levels": [ec.value for ec in EventCertainty],
            "cache_size": len(self.event_cache),
            "temporal_expression_types": list(self.date_patterns.keys())
        }