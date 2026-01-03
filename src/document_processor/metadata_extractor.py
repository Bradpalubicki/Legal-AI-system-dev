"""
Advanced metadata extraction and automated tagging system for legal documents.
Provides comprehensive document analysis, intelligent tagging, and structured metadata extraction.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json

import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd
from dateutil import parser as date_parser
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from eyecite import get_citations
from eyecite.models import FullCaseCitation, ShortformCitation, SupraCitation

logger = logging.getLogger(__name__)


class MetadataType(Enum):
    """Types of metadata that can be extracted."""
    BASIC = "basic"                    # Basic document info
    PARTIES = "parties"                # Legal parties
    DATES = "dates"                    # Important dates
    AMOUNTS = "amounts"                # Financial amounts
    CITATIONS = "citations"            # Legal citations
    CONTACTS = "contacts"              # Contact information
    LOCATIONS = "locations"            # Geographic locations
    COURT_INFO = "court_info"         # Court-specific info
    CASE_INFO = "case_info"           # Case-specific info
    LEGAL_CONCEPTS = "legal_concepts"  # Legal concepts
    PROCEDURAL = "procedural"          # Procedural information
    DOCUMENT_STRUCTURE = "structure"   # Document structure
    ENTITIES = "entities"              # Named entities
    RELATIONSHIPS = "relationships"    # Entity relationships


class TagCategory(Enum):
    """Categories for automated tags."""
    DOCUMENT_TYPE = "document_type"
    PRACTICE_AREA = "practice_area"
    URGENCY = "urgency"
    STATUS = "status"
    SUBJECT_MATTER = "subject_matter"
    LEGAL_CONCEPT = "legal_concept"
    PROCEDURAL = "procedural"
    TEMPORAL = "temporal"
    FINANCIAL = "financial"
    JURISDICTIONAL = "jurisdictional"


@dataclass
class ExtractedEntity:
    """Represents an extracted entity with metadata."""
    entity_type: str
    value: str
    confidence: float
    start_position: int
    end_position: int
    context: str
    source_method: str
    validation_status: str = "unvalidated"
    normalized_value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedMetadata:
    """Comprehensive extracted metadata for a legal document."""
    # Basic document information
    document_type: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    page_count: int = 0
    word_count: int = 0
    language: str = "en"
    
    # Party information
    plaintiffs: List[str] = field(default_factory=list)
    defendants: List[str] = field(default_factory=list)
    parties: List[str] = field(default_factory=list)
    attorneys: List[str] = field(default_factory=list)
    judges: List[str] = field(default_factory=list)
    
    # Date information
    document_date: Optional[datetime] = None
    filing_date: Optional[datetime] = None
    service_date: Optional[datetime] = None
    response_due_date: Optional[datetime] = None
    hearing_date: Optional[datetime] = None
    trial_date: Optional[datetime] = None
    deadlines: List[datetime] = field(default_factory=list)
    
    # Court and case information
    court_name: Optional[str] = None
    case_number: Optional[str] = None
    docket_number: Optional[str] = None
    jurisdiction: Optional[str] = None
    judge_name: Optional[str] = None
    
    # Financial information
    monetary_amounts: List[str] = field(default_factory=list)
    damages_claimed: List[str] = field(default_factory=list)
    settlement_amounts: List[str] = field(default_factory=list)
    costs_awarded: List[str] = field(default_factory=list)
    
    # Citations and references
    case_citations: List[str] = field(default_factory=list)
    statute_citations: List[str] = field(default_factory=list)
    regulation_citations: List[str] = field(default_factory=list)
    internal_references: List[str] = field(default_factory=list)
    
    # Contact information
    email_addresses: List[str] = field(default_factory=list)
    phone_numbers: List[str] = field(default_factory=list)
    addresses: List[str] = field(default_factory=list)
    
    # Geographic information
    locations: List[str] = field(default_factory=list)
    venues: List[str] = field(default_factory=list)
    
    # Legal concepts and subjects
    legal_concepts: List[str] = field(default_factory=list)
    subject_matter_tags: List[str] = field(default_factory=list)
    practice_areas: List[str] = field(default_factory=list)
    
    # Document structure
    has_signature_block: bool = False
    has_certificate_of_service: bool = False
    has_table_of_contents: bool = False
    has_table_of_authorities: bool = False
    section_count: int = 0
    exhibit_count: int = 0
    
    # Procedural information
    motion_type: Optional[str] = None
    relief_sought: List[str] = field(default_factory=list)
    legal_standards: List[str] = field(default_factory=list)
    procedural_posture: Optional[str] = None
    
    # Automated tags
    tags: Dict[TagCategory, List[str]] = field(default_factory=dict)
    
    # Quality metrics
    confidence_score: float = 0.0
    extraction_timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_errors: List[str] = field(default_factory=list)
    
    # Raw entities
    all_entities: List[ExtractedEntity] = field(default_factory=list)


class MetadataExtractor:
    """Advanced metadata extraction and tagging system."""
    
    def __init__(self, nlp_model: str = "en_core_web_sm"):
        """Initialize metadata extractor.
        
        Args:
            nlp_model: spaCy model name for NLP processing
        """
        self.nlp_model = nlp_model
        self.nlp = None
        
        # Initialize extraction patterns
        self._initialize_patterns()
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_patterns(self):
        """Initialize regex patterns for metadata extraction."""
        self.patterns = {
            'case_number': [
                r'\b(?:case|civil|criminal)\s*(?:no\.?|number)\s*[:\-]?\s*([A-Z0-9\-:]+)\b',
                r'\bdocket\s*(?:no\.?|number)\s*[:\-]?\s*([A-Z0-9\-:]+)\b',
                r'\b(\d{4}-\w{2,3}-\d+)\b'  # Common case number format
            ],
            'court': [
                r'\b(?:in\s+the\s+)?(.+?court.*?)(?:\n|for|$)',
                r'\b(united\s+states\s+district\s+court.*?)(?:\n|$)',
                r'\b(supreme\s+court.*?)(?:\n|$)'
            ],
            'judge': [
                r'\bhon\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'\bjudge\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'\bthe\s+honorable\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ],
            'attorney': [
                r'\besq\.?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'\battorney\s+for.*?:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*esq\.'
            ],
            'monetary_amounts': [
                r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|k|m|b))?',
                r'(?:damages|settlement|award|fine|penalty).*?\$[\d,]+(?:\.\d{2})?',
                r'(?:usd|dollars?)\s*[\d,]+(?:\.\d{2})?'
            ],
            'dates': [
                r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b',
                r'\b(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b',
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
            ],
            'phone_numbers': [
                r'\b(?:\+?1[-.\s]?)?(?:\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})\b'
            ],
            'email_addresses': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            'addresses': [
                r'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Court|Ct|Circle|Cir|Place|Pl)\b'
            ]
        }
        
        # Legal concept patterns
        self.legal_concepts = {
            'motion_types': [
                'motion to dismiss', 'motion for summary judgment', 'motion in limine',
                'motion to compel', 'motion for sanctions', 'motion to strike',
                'motion for preliminary injunction', 'motion for temporary restraining order'
            ],
            'legal_standards': [
                'preponderance of evidence', 'clear and convincing evidence',
                'beyond a reasonable doubt', 'substantial evidence', 'de novo review',
                'arbitrary and capricious', 'abuse of discretion'
            ],
            'relief_types': [
                'injunctive relief', 'monetary damages', 'punitive damages',
                'attorney fees', 'costs', 'declaratory judgment', 'mandamus'
            ],
            'contract_concepts': [
                'breach of contract', 'material breach', 'fundamental breach',
                'anticipatory breach', 'consideration', 'offer and acceptance',
                'capacity', 'duress', 'undue influence', 'unconscionability'
            ],
            'tort_concepts': [
                'negligence', 'duty of care', 'breach of duty', 'causation',
                'proximate cause', 'damages', 'strict liability', 'intentional tort',
                'defamation', 'invasion of privacy', 'emotional distress'
            ]
        }
    
    def _initialize_models(self):
        """Initialize NLP models and classifiers."""
        try:
            # Load spaCy model
            self.nlp = spacy.load(self.nlp_model)
            logger.info(f"Loaded spaCy model: {self.nlp_model}")
            
            # Initialize legal document classifier
            try:
                self.doc_classifier = pipeline(
                    "text-classification",
                    model="nlpaueb/legal-bert-base-uncased",
                    device=0 if spacy.prefer_gpu() else -1
                )
                logger.info("Loaded legal document classifier")
            except Exception as e:
                logger.warning(f"Could not load legal classifier: {e}")
                self.doc_classifier = None
                
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            self.nlp = None
    
    def extract_metadata(self, content: str, filename: str = "", 
                        extract_types: List[MetadataType] = None) -> ExtractedMetadata:
        """Extract comprehensive metadata from document content.
        
        Args:
            content: Document text content
            filename: Optional filename for additional context
            extract_types: Types of metadata to extract (all by default)
            
        Returns:
            Extracted metadata object
        """
        logger.info(f"Extracting metadata from document: {filename}")
        
        extract_types = extract_types or list(MetadataType)
        metadata = ExtractedMetadata()
        
        try:
            # Basic document information
            if MetadataType.BASIC in extract_types:
                self._extract_basic_info(content, filename, metadata)
            
            # Party information
            if MetadataType.PARTIES in extract_types:
                self._extract_parties(content, metadata)
            
            # Date information
            if MetadataType.DATES in extract_types:
                self._extract_dates(content, metadata)
            
            # Financial information
            if MetadataType.AMOUNTS in extract_types:
                self._extract_amounts(content, metadata)
            
            # Citations
            if MetadataType.CITATIONS in extract_types:
                self._extract_citations(content, metadata)
            
            # Contact information
            if MetadataType.CONTACTS in extract_types:
                self._extract_contacts(content, metadata)
            
            # Locations
            if MetadataType.LOCATIONS in extract_types:
                self._extract_locations(content, metadata)
            
            # Court information
            if MetadataType.COURT_INFO in extract_types:
                self._extract_court_info(content, metadata)
            
            # Case information
            if MetadataType.CASE_INFO in extract_types:
                self._extract_case_info(content, metadata)
            
            # Legal concepts
            if MetadataType.LEGAL_CONCEPTS in extract_types:
                self._extract_legal_concepts(content, metadata)
            
            # Procedural information
            if MetadataType.PROCEDURAL in extract_types:
                self._extract_procedural_info(content, metadata)
            
            # Document structure
            if MetadataType.DOCUMENT_STRUCTURE in extract_types:
                self._extract_document_structure(content, metadata)
            
            # Named entities
            if MetadataType.ENTITIES in extract_types:
                self._extract_named_entities(content, metadata)
            
            # Generate automated tags
            self._generate_automated_tags(metadata)
            
            # Calculate confidence score
            metadata.confidence_score = self._calculate_confidence_score(metadata)
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            metadata.processing_errors.append(str(e))
        
        return metadata
    
    def _extract_basic_info(self, content: str, filename: str, metadata: ExtractedMetadata):
        """Extract basic document information."""
        metadata.word_count = len(content.split())
        metadata.page_count = max(1, metadata.word_count // 250)  # Estimate
        
        # Extract title (first meaningful line)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if lines:
            # Look for title-like first line
            first_line = lines[0]
            if len(first_line) > 10 and not first_line.endswith('.'):
                metadata.title = first_line[:200]  # Limit length
        
        # Document type from filename
        if filename:
            filename_lower = filename.lower()
            if 'motion' in filename_lower:
                metadata.document_type = 'motion'
            elif 'brief' in filename_lower:
                metadata.document_type = 'brief'
            elif 'complaint' in filename_lower:
                metadata.document_type = 'complaint'
            elif 'contract' in filename_lower or 'agreement' in filename_lower:
                metadata.document_type = 'contract'
    
    def _extract_parties(self, content: str, metadata: ExtractedMetadata):
        """Extract party information from document."""
        content_lower = content.lower()
        
        # Extract plaintiffs
        plaintiff_patterns = [
            r'\bplaintiff[s]?[:\s]+([A-Z][A-Za-z\s,]+?)(?:\s+v\.|\s+vs\.|\n)',
            r'\bpetitioner[s]?[:\s]+([A-Z][A-Za-z\s,]+?)(?:\s+v\.|\s+vs\.|\n)'
        ]
        
        for pattern in plaintiff_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                cleaned = match.strip().rstrip(',')
                if len(cleaned) > 2:
                    metadata.plaintiffs.append(cleaned)
        
        # Extract defendants
        defendant_patterns = [
            r'\bdefendant[s]?[:\s]+([A-Z][A-Za-z\s,]+?)(?:\n|$)',
            r'\brespondent[s]?[:\s]+([A-Z][A-Za-z\s,]+?)(?:\n|$)'
        ]
        
        for pattern in defendant_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                cleaned = match.strip().rstrip(',')
                if len(cleaned) > 2:
                    metadata.defendants.append(cleaned)
        
        # Extract general parties (corporations, entities)
        party_patterns = [
            r'\b([A-Z][A-Za-z\s]+(?:Corp|Inc|LLC|Ltd|Co|LP)\.?)\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+v\.|\s+vs\.)',
            r'\b(state of [A-Z][a-z]+)\b'
        ]
        
        for pattern in party_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match not in metadata.parties and len(match) > 3:
                    metadata.parties.append(match)
        
        # Extract attorneys
        attorney_patterns = self.patterns['attorney']
        for pattern in attorney_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match not in metadata.attorneys and len(match) > 3:
                    metadata.attorneys.append(match)
    
    def _extract_dates(self, content: str, metadata: ExtractedMetadata):
        """Extract date information from document."""
        all_dates = []
        
        # Extract dates using patterns
        for pattern in self.patterns['dates']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                date_str = match.group()
                try:
                    parsed_date = date_parser.parse(date_str, fuzzy=False)
                    all_dates.append((parsed_date, match.start(), date_str))
                except (ValueError, TypeError):
                    continue
        
        # Classify dates by context
        for date_obj, position, original_str in all_dates:
            # Get context around the date
            context_start = max(0, position - 50)
            context_end = min(len(content), position + 50)
            context = content[context_start:context_end].lower()
            
            # Classify based on context
            if any(word in context for word in ['filed', 'filing', 'file']):
                if not metadata.filing_date:
                    metadata.filing_date = date_obj
            elif any(word in context for word in ['served', 'service']):
                if not metadata.service_date:
                    metadata.service_date = date_obj
            elif any(word in context for word in ['due', 'response', 'answer']):
                if not metadata.response_due_date:
                    metadata.response_due_date = date_obj
            elif any(word in context for word in ['hearing', 'oral argument']):
                if not metadata.hearing_date:
                    metadata.hearing_date = date_obj
            elif any(word in context for word in ['trial', 'jury']):
                if not metadata.trial_date:
                    metadata.trial_date = date_obj
            elif any(word in context for word in ['deadline', 'expires']):
                metadata.deadlines.append(date_obj)
            elif not metadata.document_date:
                # Default to document date if no specific context
                metadata.document_date = date_obj
        
        # Sort dates
        metadata.deadlines.sort()
    
    def _extract_amounts(self, content: str, metadata: ExtractedMetadata):
        """Extract monetary amounts from document."""
        for pattern in self.patterns['monetary_amounts']:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                cleaned_amount = re.sub(r'[^\d,.$]', '', match)
                if cleaned_amount and cleaned_amount not in metadata.monetary_amounts:
                    metadata.monetary_amounts.append(cleaned_amount)
        
        # Classify amounts by context
        content_lower = content.lower()
        for amount in metadata.monetary_amounts:
            amount_pos = content_lower.find(amount.lower())
            if amount_pos != -1:
                context_start = max(0, amount_pos - 50)
                context_end = min(len(content), amount_pos + 50)
                context = content_lower[context_start:context_end]
                
                if any(word in context for word in ['damages', 'damage', 'loss']):
                    if amount not in metadata.damages_claimed:
                        metadata.damages_claimed.append(amount)
                elif any(word in context for word in ['settlement', 'settle']):
                    if amount not in metadata.settlement_amounts:
                        metadata.settlement_amounts.append(amount)
                elif any(word in context for word in ['costs', 'fees', 'attorney']):
                    if amount not in metadata.costs_awarded:
                        metadata.costs_awarded.append(amount)
    
    def _extract_citations(self, content: str, metadata: ExtractedMetadata):
        """Extract legal citations from document."""
        try:
            # Use eyecite library for comprehensive citation extraction
            citations = get_citations(content)
            
            for citation in citations:
                citation_str = str(citation).strip()
                
                if isinstance(citation, FullCaseCitation):
                    if citation_str not in metadata.case_citations:
                        metadata.case_citations.append(citation_str)
                elif 'U.S.C.' in citation_str or 'USC' in citation_str:
                    if citation_str not in metadata.statute_citations:
                        metadata.statute_citations.append(citation_str)
                elif 'C.F.R.' in citation_str or 'CFR' in citation_str:
                    if citation_str not in metadata.regulation_citations:
                        metadata.regulation_citations.append(citation_str)
        except Exception as e:
            logger.warning(f"Citation extraction failed: {e}")
            
            # Fallback to regex patterns
            citation_patterns = [
                r'\b\d+\s+[A-Z][a-z\.]+\s+\d+\b',  # Case citations
                r'\b\d+\s+U\.S\.C\.\s+§\s*\d+\b',  # USC
                r'\b\d+\s+C\.F\.R\.\s+§\s*\d+\b'   # CFR
            ]
            
            for pattern in citation_patterns:
                matches = re.findall(pattern, content)
                metadata.case_citations.extend(matches)
    
    def _extract_contacts(self, content: str, metadata: ExtractedMetadata):
        """Extract contact information from document."""
        # Email addresses
        for pattern in self.patterns['email_addresses']:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    # Validate email
                    validated = validate_email(match)
                    if validated.email not in metadata.email_addresses:
                        metadata.email_addresses.append(validated.email)
                except EmailNotValidError:
                    continue
        
        # Phone numbers
        for pattern in self.patterns['phone_numbers']:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    # Parse and format phone number
                    parsed = phonenumbers.parse(match, "US")
                    if phonenumbers.is_valid_number(parsed):
                        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
                        if formatted not in metadata.phone_numbers:
                            metadata.phone_numbers.append(formatted)
                except Exception:
                    # Keep original if parsing fails
                    if match not in metadata.phone_numbers:
                        metadata.phone_numbers.append(match)
        
        # Addresses
        for pattern in self.patterns['addresses']:
            matches = re.findall(pattern, content)
            for match in matches:
                if match not in metadata.addresses:
                    metadata.addresses.append(match)
    
    def _extract_locations(self, content: str, metadata: ExtractedMetadata):
        """Extract location information using NLP."""
        if not self.nlp:
            return
        
        try:
            # Process with spaCy NLP
            doc = self.nlp(content[:100000])  # Limit for performance
            
            for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC"]:  # Geopolitical entities and locations
                    location = ent.text.strip()
                    if len(location) > 2 and location not in metadata.locations:
                        metadata.locations.append(location)
                        
                        # Check if it's a venue mention
                        if any(word in ent.sent.text.lower() for word in ['venue', 'jurisdiction', 'court']):
                            if location not in metadata.venues:
                                metadata.venues.append(location)
        except Exception as e:
            logger.warning(f"Location extraction failed: {e}")
    
    def _extract_court_info(self, content: str, metadata: ExtractedMetadata):
        """Extract court-specific information."""
        # Extract court name
        for pattern in self.patterns['court']:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                court_name = match.strip()
                if len(court_name) > 5 and not metadata.court_name:
                    metadata.court_name = court_name
                    break
        
        # Extract judge name
        for pattern in self.patterns['judge']:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                judge_name = match.strip()
                if len(judge_name) > 3 and judge_name not in metadata.judges:
                    metadata.judges.append(judge_name)
                    if not metadata.judge_name:
                        metadata.judge_name = judge_name
        
        # Extract jurisdiction
        jurisdiction_patterns = [
            r'\b(?:state of|commonwealth of)\s+([A-Z][a-z]+)\b',
            r'\b([A-Z][a-z]+)\s+state\s+court\b',
            r'\bunited\s+states\s+district\s+court.*?for.*?([A-Z][a-z\s]+)\b'
        ]
        
        for pattern in jurisdiction_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if not metadata.jurisdiction and len(match.strip()) > 2:
                    metadata.jurisdiction = match.strip()
                    break
    
    def _extract_case_info(self, content: str, metadata: ExtractedMetadata):
        """Extract case-specific information."""
        # Extract case number
        for pattern in self.patterns['case_number']:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                case_num = match.strip()
                if len(case_num) > 3 and not metadata.case_number:
                    metadata.case_number = case_num
                    break
        
        # Also check for docket number
        if metadata.case_number and 'docket' not in content.lower():
            metadata.docket_number = metadata.case_number
    
    def _extract_legal_concepts(self, content: str, metadata: ExtractedMetadata):
        """Extract legal concepts and practice areas."""
        content_lower = content.lower()
        
        # Extract legal concepts by category
        all_concepts = []
        for category, concepts in self.legal_concepts.items():
            for concept in concepts:
                if concept in content_lower:
                    all_concepts.append(concept)
                    
                    # Categorize by practice area
                    if category == 'contract_concepts':
                        if 'contract law' not in metadata.practice_areas:
                            metadata.practice_areas.append('contract law')
                    elif category == 'tort_concepts':
                        if 'tort law' not in metadata.practice_areas:
                            metadata.practice_areas.append('tort law')
        
        metadata.legal_concepts = list(set(all_concepts))
        
        # Additional practice area detection
        practice_area_keywords = {
            'employment law': ['employment', 'employee', 'workplace', 'discrimination', 'harassment'],
            'intellectual property': ['patent', 'trademark', 'copyright', 'trade secret'],
            'real estate': ['real estate', 'property', 'lease', 'mortgage', 'deed'],
            'family law': ['divorce', 'custody', 'marriage', 'adoption', 'support'],
            'criminal law': ['criminal', 'prosecution', 'felony', 'misdemeanor'],
            'corporate law': ['corporate', 'shareholder', 'merger', 'acquisition', 'securities'],
            'bankruptcy': ['bankruptcy', 'debtor', 'creditor', 'insolvency'],
            'immigration': ['immigration', 'visa', 'deportation', 'asylum']
        }
        
        for area, keywords in practice_area_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                if area not in metadata.practice_areas:
                    metadata.practice_areas.append(area)
    
    def _extract_procedural_info(self, content: str, metadata: ExtractedMetadata):
        """Extract procedural information."""
        content_lower = content.lower()
        
        # Extract motion type
        for motion_type in self.legal_concepts['motion_types']:
            if motion_type in content_lower:
                if not metadata.motion_type:
                    metadata.motion_type = motion_type
                break
        
        # Extract relief sought
        relief_patterns = [
            r'(?:seeks|requests|prays for|moves for)\s+([^.!?]+[.!?])',
            r'(?:wherefore|therefore).*?(?:seeks|requests|prays for)\s+([^.!?]+[.!?])'
        ]
        
        for pattern in relief_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                relief = match.strip()
                if len(relief) > 10 and relief not in metadata.relief_sought:
                    metadata.relief_sought.append(relief)
        
        # Extract legal standards
        for standard in self.legal_concepts['legal_standards']:
            if standard in content_lower:
                if standard not in metadata.legal_standards:
                    metadata.legal_standards.append(standard)
    
    def _extract_document_structure(self, content: str, metadata: ExtractedMetadata):
        """Extract document structure information."""
        content_lower = content.lower()
        
        # Check for common document elements
        metadata.has_signature_block = bool(re.search(r'signature|signed|executed', content_lower))
        metadata.has_certificate_of_service = bool(re.search(r'certificate of service', content_lower))
        metadata.has_table_of_contents = bool(re.search(r'table of contents', content_lower))
        metadata.has_table_of_authorities = bool(re.search(r'table of authorities', content_lower))
        
        # Count sections and exhibits
        metadata.section_count = len(re.findall(r'^\s*(?:section|§)\s*\d+', content, re.MULTILINE | re.IGNORECASE))
        metadata.exhibit_count = len(re.findall(r'exhibit\s+[A-Z0-9]', content, re.IGNORECASE))
    
    def _extract_named_entities(self, content: str, metadata: ExtractedMetadata):
        """Extract named entities using NLP."""
        if not self.nlp:
            return
        
        try:
            doc = self.nlp(content[:100000])  # Limit for performance
            
            for ent in doc.ents:
                entity = ExtractedEntity(
                    entity_type=ent.label_,
                    value=ent.text.strip(),
                    confidence=0.8,  # spaCy doesn't provide confidence scores
                    start_position=ent.start_char,
                    end_position=ent.end_char,
                    context=ent.sent.text[:200],
                    source_method="spacy_ner"
                )
                
                # Validate and normalize entity
                if len(entity.value) > 2:
                    entity.normalized_value = entity.value.title()
                    entity.validation_status = "valid"
                    metadata.all_entities.append(entity)
                    
        except Exception as e:
            logger.warning(f"Named entity extraction failed: {e}")
    
    def _generate_automated_tags(self, metadata: ExtractedMetadata):
        """Generate automated tags based on extracted metadata."""
        # Document type tags
        if metadata.document_type:
            metadata.tags[TagCategory.DOCUMENT_TYPE] = [metadata.document_type]
        
        # Practice area tags
        if metadata.practice_areas:
            metadata.tags[TagCategory.PRACTICE_AREA] = metadata.practice_areas
        
        # Legal concept tags
        if metadata.legal_concepts:
            metadata.tags[TagCategory.LEGAL_CONCEPT] = metadata.legal_concepts[:10]  # Limit
        
        # Urgency tags based on deadlines
        urgency_tags = []
        now = datetime.utcnow()
        for deadline in metadata.deadlines:
            days_until = (deadline - now).days
            if days_until <= 1:
                urgency_tags.append("critical")
            elif days_until <= 7:
                urgency_tags.append("high")
            elif days_until <= 30:
                urgency_tags.append("medium")
            else:
                urgency_tags.append("low")
        
        if urgency_tags:
            metadata.tags[TagCategory.URGENCY] = list(set(urgency_tags))
        
        # Financial tags
        if metadata.monetary_amounts:
            metadata.tags[TagCategory.FINANCIAL] = ["contains_financial_amounts"]
        
        # Jurisdictional tags
        if metadata.jurisdiction:
            metadata.tags[TagCategory.JURISDICTIONAL] = [metadata.jurisdiction]
        
        # Temporal tags
        temporal_tags = []
        if metadata.filing_date:
            temporal_tags.append(f"filed_{metadata.filing_date.year}")
        if metadata.hearing_date:
            temporal_tags.append("has_hearing_date")
        if metadata.trial_date:
            temporal_tags.append("has_trial_date")
        
        if temporal_tags:
            metadata.tags[TagCategory.TEMPORAL] = temporal_tags
        
        # Procedural tags
        procedural_tags = []
        if metadata.motion_type:
            procedural_tags.append(metadata.motion_type.replace(' ', '_'))
        if metadata.relief_sought:
            procedural_tags.append("seeks_relief")
        
        if procedural_tags:
            metadata.tags[TagCategory.PROCEDURAL] = procedural_tags
    
    def _calculate_confidence_score(self, metadata: ExtractedMetadata) -> float:
        """Calculate overall confidence score for extracted metadata."""
        confidence_factors = []
        
        # Basic information confidence
        if metadata.document_type:
            confidence_factors.append(0.8)
        if metadata.title:
            confidence_factors.append(0.7)
        
        # Party information confidence
        if metadata.plaintiffs or metadata.defendants:
            confidence_factors.append(0.9)
        if metadata.parties:
            confidence_factors.append(0.8)
        
        # Date information confidence
        if metadata.document_date:
            confidence_factors.append(0.8)
        if metadata.deadlines:
            confidence_factors.append(0.9)
        
        # Court information confidence
        if metadata.court_name:
            confidence_factors.append(0.9)
        if metadata.case_number:
            confidence_factors.append(0.95)
        
        # Citation confidence
        if metadata.case_citations:
            confidence_factors.append(0.9)
        
        # Error penalty
        error_penalty = len(metadata.processing_errors) * 0.1
        
        if confidence_factors:
            base_confidence = sum(confidence_factors) / len(confidence_factors)
            return max(0.0, min(1.0, base_confidence - error_penalty))
        else:
            return 0.5  # Default confidence
    
    def validate_metadata(self, metadata: ExtractedMetadata) -> Dict[str, List[str]]:
        """Validate extracted metadata and return validation results.
        
        Returns:
            Dictionary with validation errors and warnings
        """
        errors = []
        warnings = []
        
        # Validate dates
        for date_field in ['document_date', 'filing_date', 'service_date', 
                          'response_due_date', 'hearing_date', 'trial_date']:
            date_value = getattr(metadata, date_field)
            if date_value:
                # Check for future dates where inappropriate
                if date_field in ['document_date', 'filing_date'] and date_value > datetime.utcnow():
                    warnings.append(f"{date_field} is in the future")
                
                # Check for very old dates
                if date_value.year < 1900:
                    errors.append(f"{date_field} year is invalid: {date_value.year}")
        
        # Validate email addresses
        for email in metadata.email_addresses:
            try:
                validate_email(email)
            except EmailNotValidError:
                errors.append(f"Invalid email address: {email}")
        
        # Validate case numbers
        if metadata.case_number:
            if len(metadata.case_number) < 3:
                warnings.append(f"Case number seems too short: {metadata.case_number}")
        
        # Validate monetary amounts
        for amount in metadata.monetary_amounts:
            if not re.match(r'^\$?[\d,]+(?:\.\d{2})?$', amount):
                warnings.append(f"Invalid monetary amount format: {amount}")
        
        return {
            "errors": errors,
            "warnings": warnings
        }
    
    def export_metadata(self, metadata: ExtractedMetadata, format: str = "json") -> str:
        """Export metadata in specified format.
        
        Args:
            metadata: ExtractedMetadata object to export
            format: Export format ("json", "csv", "xml")
            
        Returns:
            Serialized metadata string
        """
        if format.lower() == "json":
            return json.dumps(metadata, default=str, indent=2)
        elif format.lower() == "csv":
            # Convert to pandas DataFrame for CSV export
            data = {}
            for field in metadata.__dataclass_fields__:
                value = getattr(metadata, field)
                if isinstance(value, (list, dict)):
                    data[field] = str(value)
                else:
                    data[field] = value
            
            df = pd.DataFrame([data])
            return df.to_csv(index=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_extraction_statistics(self) -> Dict[str, Any]:
        """Get metadata extraction statistics."""
        return {
            "nlp_model_loaded": self.nlp is not None,
            "classifier_loaded": hasattr(self, 'doc_classifier') and self.doc_classifier is not None,
            "supported_languages": ["en"],  # Expand as needed
            "extraction_types": [mt.value for mt in MetadataType],
            "tag_categories": [tc.value for tc in TagCategory]
        }