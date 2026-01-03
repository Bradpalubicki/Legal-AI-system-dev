#!/usr/bin/env python3
"""
DOCUMENT INTELLIGENCE CORE - INTELLIGENT INTAKE SYSTEM

Advanced document analysis system for legal AI document processing.
Identifies document types, extracts key information, and identifies gaps
for bankruptcy, litigation, and contract documents.

COMPLIANCE: Operates under strict UPL compliance with educational-only outputs.
All analysis results are for informational purposes only.
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib

# Import compliance wrapper
try:
    from ..shared.compliance.upl_compliance import ComplianceWrapper, ViolationSeverity, ComplianceAction
except ImportError:
    # Mock compliance wrapper for standalone use
    class ViolationSeverity(Enum):
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
        CRITICAL = "CRITICAL"

    class ComplianceAction(Enum):
        BLOCK = "BLOCK"
        CONVERT = "CONVERT"
        WARN = "WARN"
        LOG = "LOG"

    class ComplianceWrapper:
        def analyze_text(self, text: str) -> Dict[str, Any]:
            return {"has_advice": False, "violations": [], "compliance_score": 1.0}

# Import document models
try:
    from ..document_processor.models import DocumentCategory
except ImportError:
    # Define local document categories
    class DocumentCategory(Enum):
        # Bankruptcy Documents
        BANKRUPTCY_PETITION = "bankruptcy_petition"
        BANKRUPTCY_SCHEDULE = "bankruptcy_schedule"
        STATEMENT_OF_AFFAIRS = "statement_of_affairs"
        PROOF_OF_CLAIM = "proof_of_claim"

        # Litigation Documents
        COMPLAINT = "complaint"
        ANSWER = "answer"
        MOTION = "motion"
        BRIEF = "brief"
        DISCOVERY = "discovery"
        SUBPOENA = "subpoena"

        # Contract Documents
        CONTRACT = "contract"
        AGREEMENT = "agreement"
        AMENDMENT = "amendment"
        TERMINATION = "termination"

        # General
        UNKNOWN = "unknown"
        OTHER = "other"

logger = logging.getLogger(__name__)


@dataclass
class DocumentType:
    """Represents an identified document type with confidence scoring"""
    category: DocumentCategory
    subcategory: Optional[str] = None
    confidence_score: float = 0.0
    identifying_features: List[str] = field(default_factory=list)
    form_number: Optional[str] = None
    jurisdiction: Optional[str] = None


@dataclass
class ExtractedEntity:
    """Represents an extracted piece of information from a document"""
    entity_type: str
    value: str
    confidence: float
    location: str
    validation_status: str = "unvalidated"
    source_text: Optional[str] = None


@dataclass
class InformationGap:
    """Represents missing critical information in a document"""
    gap_type: str
    description: str
    severity: ViolationSeverity
    required_for: List[str]
    suggestions: List[str] = field(default_factory=list)


@dataclass
class DocumentAnalysisResult:
    """Complete analysis result for a document"""
    document_id: str
    document_type: DocumentType
    extracted_entities: List[ExtractedEntity]
    information_gaps: List[InformationGap]
    analysis_metadata: Dict[str, Any]
    compliance_status: Dict[str, Any]
    processing_timestamp: datetime = field(default_factory=datetime.now)


class DocumentIntakeAnalyzer:
    """
    Advanced document intelligence system for legal document analysis.

    This class provides sophisticated document type identification,
    key information extraction, and gap analysis capabilities.

    DISCLAIMER: This system provides educational analysis only and does not
    constitute legal advice. All outputs require attorney review.
    """

    def __init__(self):
        """Initialize the document analyzer with pattern libraries"""
        self.compliance_wrapper = ComplianceWrapper()
        self._initialize_pattern_libraries()
        self.logger = logging.getLogger(__name__)

    def _initialize_pattern_libraries(self):
        """Initialize document identification and extraction patterns"""

        # Document identification patterns
        self.document_patterns = {
            DocumentCategory.BANKRUPTCY_PETITION: {
                "form_indicators": [
                    r"voluntary petition for.*bankruptcy",
                    r"chapter\s+(7|11|13).*petition",
                    r"form\s+b\s*101",
                    r"bankruptcy petition.*voluntary",
                    r"united states bankruptcy court"
                ],
                "content_patterns": [
                    r"debtor.*full name",
                    r"social security.*last four digits",
                    r"filing fee.*paid.*waiver",
                    r"bankruptcy code.*title 11",
                    r"schedules.*statement of affairs"
                ],
                "required_sections": [
                    "debtor information",
                    "filing fee status",
                    "attorney information",
                    "bankruptcy chapter"
                ]
            },

            DocumentCategory.BANKRUPTCY_SCHEDULE: {
                "form_indicators": [
                    r"schedule\s+[a-k]\s*[\-\:]\s*",
                    r"form\s+b\s*10[6-8]",
                    r"schedule.*assets",
                    r"schedule.*liabilities",
                    r"schedule.*income.*expenses"
                ],
                "content_patterns": [
                    r"creditor.*name.*address",
                    r"amount.*claim.*contingent",
                    r"current market value",
                    r"monthly income.*expenses",
                    r"property.*owned.*leased"
                ],
                "required_sections": [
                    "creditor information",
                    "debt amounts",
                    "asset valuations"
                ]
            },

            DocumentCategory.COMPLAINT: {
                "form_indicators": [
                    r"complaint.*damages",
                    r"civil.*action.*complaint",
                    r"plaintiff.*defendant",
                    r"jurisdiction.*venue",
                    r"prayer.*relief"
                ],
                "content_patterns": [
                    r"parties.*this action",
                    r"cause.*action.*arises",
                    r"wherefore.*plaintiff.*prays",
                    r"jury.*trial.*demanded",
                    r"venue.*proper.*district"
                ],
                "required_sections": [
                    "parties identification",
                    "factual allegations",
                    "causes of action",
                    "prayer for relief"
                ]
            },

            DocumentCategory.CONTRACT: {
                "form_indicators": [
                    r"agreement.*entered.*between",
                    r"contract.*parties.*agreement",
                    r"terms.*conditions.*agreement",
                    r"whereas.*now therefore",
                    r"effective date.*agreement"
                ],
                "content_patterns": [
                    r"party.*agrees.*perform",
                    r"consideration.*payment.*sum",
                    r"term.*agreement.*expires",
                    r"breach.*default.*remedy",
                    r"governing law.*jurisdiction"
                ],
                "required_sections": [
                    "party identification",
                    "consideration terms",
                    "performance obligations",
                    "termination provisions"
                ]
            }
        }

        # Entity extraction patterns
        self.extraction_patterns = {
            "party_names": [
                r"(?:plaintiff|defendant|debtor|creditor).*?([A-Z][A-Za-z\s\.,]+?)(?:\n|,|\s{2})",
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*(?:an?|the)?\s*(?:individual|corporation|LLC|partnership)",
                r"between\s+([A-Z][A-Za-z\s&,\.]+?)\s+and\s+([A-Z][A-Za-z\s&,\.]+)"
            ],

            "case_numbers": [
                r"case\s*(?:no\.?|number)\s*:?\s*([0-9\-A-Z:]+)",
                r"civil\s*(?:action\s*)?(?:no\.?|number)\s*:?\s*([0-9\-A-Z:]+)",
                r"bankruptcy\s*(?:case\s*)?(?:no\.?|number)\s*:?\s*([0-9\-A-Z:]+)"
            ],

            "dates": [
                r"(?:dated?|filed?|effective)\s*(?:on\s*)?:?\s*([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
                r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
                r"([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})"
            ],

            "monetary_amounts": [
                r"\$\s*([0-9,]+\.?[0-9]*)",
                r"(?:sum|amount|debt|claim).*?\$\s*([0-9,]+\.?[0-9]*)",
                r"([0-9,]+\.?[0-9]*)\s*dollars?"
            ],

            "addresses": [
                r"(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Court|Ct|Place|Pl).*?(?:\n|[A-Z]{2}\s+\d{5}))",
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\s+\d{5}(?:\-\d{4})?)"
            ],

            "ssn_partial": [
                r"(?:social security|SSN).*?(?:last four|ending in).*?(\d{4})",
                r"XXX\-XX\-(\d{4})"
            ],

            "court_names": [
                r"(?:united states|state)\s+(?:bankruptcy\s+)?court.*?(?:for\s+the\s+)?([A-Za-z\s]+(?:district|county))",
                r"in\s+the\s+([A-Z][A-Za-z\s]+(?:court|tribunal))"
            ]
        }

        # Information gap detection rules
        self.gap_detection_rules = {
            DocumentCategory.BANKRUPTCY_PETITION: {
                "critical_fields": [
                    "debtor_name", "debtor_address", "chapter_type",
                    "attorney_name", "filing_fee_status", "case_number"
                ],
                "validation_rules": {
                    "debtor_name": r"[A-Z][a-z]+\s+[A-Z][a-z]+",
                    "case_number": r"\d{2}\-\d{5}",
                    "chapter_type": r"chapter\s+(7|11|13)"
                }
            },

            DocumentCategory.COMPLAINT: {
                "critical_fields": [
                    "plaintiff_name", "defendant_name", "case_number",
                    "court_jurisdiction", "cause_of_action", "damages_sought"
                ],
                "validation_rules": {
                    "damages_sought": r"\$[0-9,]+",
                    "case_number": r"\d+:\d+\-cv\-\d+"
                }
            },

            DocumentCategory.CONTRACT: {
                "critical_fields": [
                    "party_1", "party_2", "effective_date",
                    "consideration", "termination_date", "governing_law"
                ],
                "validation_rules": {
                    "effective_date": r"[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}",
                    "consideration": r"\$[0-9,]+"
                }
            }
        }

    def identify_document_type(self, document_text: str, filename: Optional[str] = None) -> DocumentType:
        """
        Identify the type of document using advanced pattern analysis.

        This method analyzes document content, structure, and formatting
        to determine the most likely document category.

        DISCLAIMER: Document type identification is for informational purposes
        only and does not constitute legal analysis or advice.

        Args:
            document_text (str): Full text content of the document
            filename (Optional[str]): Original filename for additional context

        Returns:
            DocumentType: Identified document type with confidence score
        """

        # Normalize text for analysis
        normalized_text = self._normalize_text(document_text)

        # Score each document type
        type_scores = {}

        for doc_category, patterns in self.document_patterns.items():
            score = self._calculate_document_score(normalized_text, patterns, filename)
            type_scores[doc_category] = score

            self.logger.debug(f"Document type {doc_category.value} scored: {score['total_score']:.3f}")

        # Find best match
        best_match = max(type_scores.items(), key=lambda x: x[1]['total_score'])
        doc_type, score_data = best_match

        # Extract additional metadata
        form_number = self._extract_form_number(normalized_text)
        jurisdiction = self._extract_jurisdiction(normalized_text)

        return DocumentType(
            category=doc_type,
            confidence_score=score_data['total_score'],
            identifying_features=score_data['matched_features'],
            form_number=form_number,
            jurisdiction=jurisdiction
        )

    def extract_key_information(self, document_text: str, document_type: DocumentType) -> List[ExtractedEntity]:
        """
        Extract key information entities from the document based on its type.

        This method performs intelligent extraction of critical data points
        including parties, dates, amounts, case numbers, and other relevant information.

        DISCLAIMER: Information extraction is for educational analysis only.
        All extracted data requires verification and attorney review.

        Args:
            document_text (str): Full text content of the document
            document_type (DocumentType): Previously identified document type

        Returns:
            List[ExtractedEntity]: List of extracted information entities
        """

        normalized_text = self._normalize_text(document_text)
        extracted_entities = []

        # Extract common entities for all document types
        common_entities = self._extract_common_entities(normalized_text)
        extracted_entities.extend(common_entities)

        # Extract document-type-specific entities
        if document_type.category == DocumentCategory.BANKRUPTCY_PETITION:
            bankruptcy_entities = self._extract_bankruptcy_entities(normalized_text)
            extracted_entities.extend(bankruptcy_entities)

        elif document_type.category == DocumentCategory.COMPLAINT:
            litigation_entities = self._extract_litigation_entities(normalized_text)
            extracted_entities.extend(litigation_entities)

        elif document_type.category == DocumentCategory.CONTRACT:
            contract_entities = self._extract_contract_entities(normalized_text)
            extracted_entities.extend(contract_entities)

        # Validate and score extracted entities
        validated_entities = []
        for entity in extracted_entities:
            validated_entity = self._validate_entity(entity, normalized_text)
            if validated_entity.confidence > 0.3:  # Minimum confidence threshold
                validated_entities.append(validated_entity)

        # Remove duplicates and sort by confidence
        unique_entities = self._deduplicate_entities(validated_entities)
        unique_entities.sort(key=lambda x: x.confidence, reverse=True)

        return unique_entities

    def identify_information_gaps(self,
                                document_text: str,
                                document_type: DocumentType,
                                extracted_entities: List[ExtractedEntity]) -> List[InformationGap]:
        """
        Identify missing critical information in the document.

        This method analyzes the document against expected requirements
        for its type and identifies gaps that may need to be addressed.

        DISCLAIMER: Gap analysis is for educational purposes only and does not
        constitute legal advice about document completeness or requirements.

        Args:
            document_text (str): Full text content of the document
            document_type (DocumentType): Previously identified document type
            extracted_entities (List[ExtractedEntity]): Previously extracted entities

        Returns:
            List[InformationGap]: List of identified information gaps
        """

        gaps = []

        # Get gap detection rules for document type
        if document_type.category not in self.gap_detection_rules:
            return gaps  # No rules defined for this document type

        rules = self.gap_detection_rules[document_type.category]
        critical_fields = rules.get("critical_fields", [])
        validation_rules = rules.get("validation_rules", {})

        # Check for missing critical fields
        extracted_types = {entity.entity_type for entity in extracted_entities}

        for field in critical_fields:
            if field not in extracted_types:
                gap = self._create_information_gap(field, document_type.category, "missing")
                gaps.append(gap)
            else:
                # Check if extracted field meets validation rules
                if field in validation_rules:
                    field_entities = [e for e in extracted_entities if e.entity_type == field]
                    for entity in field_entities:
                        if not re.search(validation_rules[field], entity.value, re.IGNORECASE):
                            gap = self._create_information_gap(field, document_type.category, "invalid_format")
                            gaps.append(gap)

        # Document-specific gap analysis
        if document_type.category == DocumentCategory.BANKRUPTCY_PETITION:
            bankruptcy_gaps = self._analyze_bankruptcy_gaps(document_text, extracted_entities)
            gaps.extend(bankruptcy_gaps)

        elif document_type.category == DocumentCategory.COMPLAINT:
            litigation_gaps = self._analyze_litigation_gaps(document_text, extracted_entities)
            gaps.extend(litigation_gaps)

        elif document_type.category == DocumentCategory.CONTRACT:
            contract_gaps = self._analyze_contract_gaps(document_text, extracted_entities)
            gaps.extend(contract_gaps)

        # Sort gaps by severity
        gaps.sort(key=lambda x: self._gap_severity_score(x.severity), reverse=True)

        return gaps

    def analyze_document(self, document_text: str, filename: Optional[str] = None) -> DocumentAnalysisResult:
        """
        Perform complete document analysis including type identification,
        information extraction, and gap analysis.

        DISCLAIMER: This analysis is for educational purposes only and does not
        constitute legal advice. All results require attorney review and verification.

        Args:
            document_text (str): Full text content of the document
            filename (Optional[str]): Original filename for context

        Returns:
            DocumentAnalysisResult: Complete analysis results
        """

        # Generate document ID
        doc_id = hashlib.md5(document_text.encode()).hexdigest()[:12]

        # Compliance check
        compliance_result = self.compliance_wrapper.analyze_text(document_text)

        try:
            # Step 1: Identify document type
            doc_type = self.identify_document_type(document_text, filename)

            # Step 2: Extract key information
            extracted_entities = self.extract_key_information(document_text, doc_type)

            # Step 3: Identify information gaps
            information_gaps = self.identify_information_gaps(document_text, doc_type, extracted_entities)

            # Analysis metadata
            metadata = {
                "document_length": len(document_text),
                "word_count": len(document_text.split()),
                "filename": filename,
                "analysis_version": "1.0.0",
                "processing_time": datetime.now().isoformat(),
                "confidence_threshold": 0.3,
                "total_entities_found": len(extracted_entities),
                "total_gaps_identified": len(information_gaps)
            }

            return DocumentAnalysisResult(
                document_id=doc_id,
                document_type=doc_type,
                extracted_entities=extracted_entities,
                information_gaps=information_gaps,
                analysis_metadata=metadata,
                compliance_status=compliance_result
            )

        except Exception as e:
            self.logger.error(f"Document analysis failed: {str(e)}")

            # Return minimal result with error information
            return DocumentAnalysisResult(
                document_id=doc_id,
                document_type=DocumentType(
                    category=DocumentCategory.UNKNOWN,
                    confidence_score=0.0,
                    identifying_features=["analysis_error"]
                ),
                extracted_entities=[],
                information_gaps=[],
                analysis_metadata={"error": str(e), "filename": filename},
                compliance_status=compliance_result
            )

    def analyze(self, document: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        STANDARDIZED INTERFACE: Analyze document and return consistent format

        Args:
            document (str): Document text to analyze
            filename (Optional[str]): Original filename

        Returns:
            Dict with keys: 'document_type', 'gaps', 'extracted_data'
        """
        analysis_result = self.analyze_document(document, filename)

        # Convert to standardized format
        return {
            'document_type': analysis_result.document_type.category.value,
            'gaps': [gap.gap_type for gap in analysis_result.information_gaps],
            'extracted_data': {
                'document_id': analysis_result.document_id,
                'confidence': analysis_result.document_type.confidence_score,
                'entities': [
                    {
                        'type': entity.entity_type,
                        'value': entity.value,
                        'confidence': entity.confidence
                    }
                    for entity in analysis_result.extracted_entities
                ],
                'metadata': analysis_result.analysis_metadata
            }
        }

    # Helper methods

    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent analysis"""
        # Remove extra whitespace and standardize line breaks
        normalized = re.sub(r'\s+', ' ', text.strip())
        # Convert to lowercase for pattern matching
        return normalized.lower()

    def _calculate_document_score(self, text: str, patterns: Dict[str, List[str]], filename: Optional[str]) -> Dict[str, Any]:
        """Calculate confidence score for document type"""
        score_data = {
            "form_score": 0.0,
            "content_score": 0.0,
            "filename_score": 0.0,
            "total_score": 0.0,
            "matched_features": []
        }

        # Score form indicators
        form_matches = 0
        for pattern in patterns.get("form_indicators", []):
            if re.search(pattern, text):
                form_matches += 1
                score_data["matched_features"].append(f"form_pattern: {pattern[:30]}...")

        score_data["form_score"] = min(form_matches / max(len(patterns.get("form_indicators", [1])), 1), 1.0)

        # Score content patterns
        content_matches = 0
        for pattern in patterns.get("content_patterns", []):
            if re.search(pattern, text):
                content_matches += 1
                score_data["matched_features"].append(f"content_pattern: {pattern[:30]}...")

        score_data["content_score"] = min(content_matches / max(len(patterns.get("content_patterns", [1])), 1), 1.0)

        # Score filename if available
        if filename:
            filename_lower = filename.lower()
            for indicator in patterns.get("form_indicators", []):
                if any(keyword in filename_lower for keyword in indicator.split() if len(keyword) > 3):
                    score_data["filename_score"] = 0.2
                    score_data["matched_features"].append(f"filename_match: {filename}")
                    break

        # Calculate total weighted score
        score_data["total_score"] = (
            score_data["form_score"] * 0.5 +
            score_data["content_score"] * 0.4 +
            score_data["filename_score"] * 0.1
        )

        return score_data

    def _extract_form_number(self, text: str) -> Optional[str]:
        """Extract form number if present"""
        form_patterns = [
            r"form\s+([a-z]*\d+[a-z]*)",
            r"form\s+([b\-]?\s*\d+[a-z]*)",
            r"official\s+form\s+(\d+)"
        ]

        for pattern in form_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return None

    def _extract_jurisdiction(self, text: str) -> Optional[str]:
        """Extract jurisdiction information"""
        jurisdiction_patterns = [
            r"(?:united states|u\.s\.)\s+(?:bankruptcy\s+)?court.*?for\s+the\s+([a-z\s]+district)",
            r"(?:state\s+of\s+|commonwealth\s+of\s+)([a-z]+)",
            r"in\s+the\s+([a-z\s]+(?:court|tribunal))"
        ]

        for pattern in jurisdiction_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip().title()

        return None

    def _extract_common_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract entities common to all document types"""
        entities = []

        # Extract party names
        for pattern in self.extraction_patterns["party_names"]:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                for i, group in enumerate(match.groups(), 1):
                    if group:
                        entities.append(ExtractedEntity(
                            entity_type="party_name",
                            value=group.strip(),
                            confidence=0.7,
                            location=f"position_{match.start()}",
                            source_text=match.group(0)
                        ))

        # Extract case numbers
        for pattern in self.extraction_patterns["case_numbers"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(ExtractedEntity(
                    entity_type="case_number",
                    value=match.group(1).strip(),
                    confidence=0.8,
                    location=f"position_{match.start()}",
                    source_text=match.group(0)
                ))

        # Extract dates
        for pattern in self.extraction_patterns["dates"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(ExtractedEntity(
                    entity_type="date",
                    value=match.group(1).strip(),
                    confidence=0.6,
                    location=f"position_{match.start()}",
                    source_text=match.group(0)
                ))

        # Extract monetary amounts
        for pattern in self.extraction_patterns["monetary_amounts"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(ExtractedEntity(
                    entity_type="monetary_amount",
                    value=f"${match.group(1).strip()}",
                    confidence=0.8,
                    location=f"position_{match.start()}",
                    source_text=match.group(0)
                ))

        return entities

    def _extract_bankruptcy_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract bankruptcy-specific entities"""
        entities = []

        # Chapter type
        chapter_pattern = r"chapter\s+(7|11|13)"
        matches = re.finditer(chapter_pattern, text, re.IGNORECASE)
        for match in matches:
            entities.append(ExtractedEntity(
                entity_type="bankruptcy_chapter",
                value=f"Chapter {match.group(1)}",
                confidence=0.9,
                location=f"position_{match.start()}",
                source_text=match.group(0)
            ))

        # Debtor name
        debtor_patterns = [
            r"debtor.*?([A-Z][a-z]+\s+[A-Z][a-z]+)",
            r"in\s+re:?\s*([A-Z][a-zA-Z\s]+?)(?:\n|,|$)"
        ]

        for pattern in debtor_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                entities.append(ExtractedEntity(
                    entity_type="debtor_name",
                    value=match.group(1).strip(),
                    confidence=0.8,
                    location=f"position_{match.start()}",
                    source_text=match.group(0)
                ))

        return entities

    def _extract_litigation_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract litigation-specific entities"""
        entities = []

        # Plaintiff/Defendant
        party_patterns = [
            r"plaintiff:?\s*([A-Z][a-zA-Z\s&,\.]+?)(?:\n|,|vs?\.)",
            r"defendant:?\s*([A-Z][a-zA-Z\s&,\.]+?)(?:\n|,|$)"
        ]

        for pattern in party_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                party_type = "plaintiff" if "plaintiff" in pattern else "defendant"
                entities.append(ExtractedEntity(
                    entity_type=f"{party_type}_name",
                    value=match.group(1).strip(),
                    confidence=0.8,
                    location=f"position_{match.start()}",
                    source_text=match.group(0)
                ))

        return entities

    def _extract_contract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract contract-specific entities"""
        entities = []

        # Effective date
        effective_patterns = [
            r"effective(?:\s+date)?:?\s*([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
            r"dated(?:\s+as\s+of)?:?\s*([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})"
        ]

        for pattern in effective_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(ExtractedEntity(
                    entity_type="effective_date",
                    value=match.group(1).strip(),
                    confidence=0.8,
                    location=f"position_{match.start()}",
                    source_text=match.group(0)
                ))

        return entities

    def _validate_entity(self, entity: ExtractedEntity, full_text: str) -> ExtractedEntity:
        """Validate and adjust entity confidence based on context"""
        # Basic validation rules
        if entity.entity_type == "monetary_amount":
            # Check if amount format is valid
            if re.match(r"\$[\d,]+\.?\d*", entity.value):
                entity.confidence *= 1.1  # Boost confidence for well-formatted amounts
            else:
                entity.confidence *= 0.8

        elif entity.entity_type == "date":
            # Check if date format is reasonable
            if re.match(r"[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}", entity.value):
                entity.confidence *= 1.1

        elif entity.entity_type in ["party_name", "debtor_name", "plaintiff_name", "defendant_name"]:
            # Check if name looks reasonable
            if len(entity.value.split()) >= 2 and entity.value.istitle():
                entity.confidence *= 1.1
            else:
                entity.confidence *= 0.9

        # Cap confidence at 1.0
        entity.confidence = min(entity.confidence, 1.0)

        # Set validation status
        entity.validation_status = "validated" if entity.confidence > 0.7 else "needs_review"

        return entity

    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove duplicate entities, keeping the highest confidence ones"""
        seen_entities = {}

        for entity in entities:
            key = (entity.entity_type, entity.value.lower().strip())
            if key not in seen_entities or entity.confidence > seen_entities[key].confidence:
                seen_entities[key] = entity

        return list(seen_entities.values())

    def _create_information_gap(self, field: str, doc_category: DocumentCategory, gap_type: str) -> InformationGap:
        """Create an information gap object"""
        gap_descriptions = {
            "debtor_name": "Debtor's full legal name is required for bankruptcy petition",
            "case_number": "Court case number must be present and properly formatted",
            "plaintiff_name": "Plaintiff identification is required for legal proceedings",
            "defendant_name": "Defendant identification is required for legal proceedings",
            "effective_date": "Contract effective date must be clearly specified",
            "consideration": "Contract consideration (payment/value) must be defined"
        }

        severity_map = {
            "missing": ViolationSeverity.CRITICAL,
            "invalid_format": ViolationSeverity.HIGH,
            "incomplete": ViolationSeverity.MEDIUM
        }

        return InformationGap(
            gap_type=field,
            description=gap_descriptions.get(field, f"Missing critical field: {field}"),
            severity=severity_map.get(gap_type, ViolationSeverity.MEDIUM),
            required_for=[doc_category.value],
            suggestions=[f"Please provide or verify {field.replace('_', ' ')}"]
        )

    def _analyze_bankruptcy_gaps(self, text: str, entities: List[ExtractedEntity]) -> List[InformationGap]:
        """Analyze bankruptcy-specific information gaps"""
        gaps = []

        # Check for required schedules mention
        if not re.search(r"schedule.*[a-k]", text, re.IGNORECASE):
            gaps.append(InformationGap(
                gap_type="missing_schedules",
                description="Bankruptcy schedules (A-K) should be referenced or attached",
                severity=ViolationSeverity.HIGH,
                required_for=["bankruptcy_petition"],
                suggestions=["Verify all required schedules are included", "Check schedule completion status"]
            ))

        # Check for meeting of creditors notice
        if not re.search(r"meeting.*creditors|341.*meeting", text, re.IGNORECASE):
            gaps.append(InformationGap(
                gap_type="creditors_meeting",
                description="Section 341 meeting of creditors information may be missing",
                severity=ViolationSeverity.MEDIUM,
                required_for=["bankruptcy_petition"],
                suggestions=["Include meeting of creditors scheduling information"]
            ))

        return gaps

    def _analyze_litigation_gaps(self, text: str, entities: List[ExtractedEntity]) -> List[InformationGap]:
        """Analyze litigation-specific information gaps"""
        gaps = []

        # Check for jurisdiction statement
        if not re.search(r"jurisdiction.*proper|venue.*appropriate", text, re.IGNORECASE):
            gaps.append(InformationGap(
                gap_type="jurisdiction_statement",
                description="Jurisdiction and venue statement may be incomplete",
                severity=ViolationSeverity.HIGH,
                required_for=["complaint"],
                suggestions=["Include clear jurisdiction and venue statements"]
            ))

        # Check for service requirements
        if not re.search(r"service.*process|served.*upon", text, re.IGNORECASE):
            gaps.append(InformationGap(
                gap_type="service_requirements",
                description="Service of process requirements not addressed",
                severity=ViolationSeverity.MEDIUM,
                required_for=["complaint"],
                suggestions=["Include service of process information"]
            ))

        return gaps

    def _analyze_contract_gaps(self, text: str, entities: List[ExtractedEntity]) -> List[InformationGap]:
        """Analyze contract-specific information gaps"""
        gaps = []

        # Check for termination clause
        if not re.search(r"terminat|expir|end.*agreement", text, re.IGNORECASE):
            gaps.append(InformationGap(
                gap_type="termination_clause",
                description="Contract termination provisions should be specified",
                severity=ViolationSeverity.HIGH,
                required_for=["contract"],
                suggestions=["Include clear termination conditions and procedures"]
            ))

        # Check for governing law
        if not re.search(r"governing.*law|jurisdiction.*agreement", text, re.IGNORECASE):
            gaps.append(InformationGap(
                gap_type="governing_law",
                description="Governing law and jurisdiction clause recommended",
                severity=ViolationSeverity.MEDIUM,
                required_for=["contract"],
                suggestions=["Specify which state/country law governs the agreement"]
            ))

        return gaps

    def _gap_severity_score(self, severity: ViolationSeverity) -> int:
        """Convert severity to numeric score for sorting"""
        severity_scores = {
            ViolationSeverity.CRITICAL: 4,
            ViolationSeverity.HIGH: 3,
            ViolationSeverity.MEDIUM: 2,
            ViolationSeverity.LOW: 1
        }
        return severity_scores.get(severity, 0)


def test_with_sample_bankruptcy_petition():
    """
    Test the DocumentIntakeAnalyzer with a sample bankruptcy petition.

    DISCLAIMER: This is a test function for educational purposes only.
    Sample data does not represent actual legal documents.
    """

    sample_bankruptcy_text = """
    UNITED STATES BANKRUPTCY COURT
    FOR THE EASTERN DISTRICT OF VIRGINIA

    VOLUNTARY PETITION FOR INDIVIDUALS FILING FOR BANKRUPTCY

    In re: John Doe Smith                           Case No. 23-12345
           Debtor                                   Chapter 7

    DEBTOR INFORMATION:
    Name: John Doe Smith
    Address: 123 Main Street, Richmond, VA 23219
    Social Security No.: XXX-XX-1234

    I, John Doe Smith, request relief in accordance with the chapter of
    title 11, United States Code, specified in this petition.

    FILING FEE: $338 (paid)

    ATTORNEY INFORMATION:
    Jane Attorney, Esq.
    Virginia State Bar No. 12345
    Law Firm Name
    456 Legal Avenue, Richmond, VA 23220

    The debtor requests that the filing fee be paid in installments and
    has filed the number of installments requested and the proposed amount
    of each installment.

    I declare under penalty of perjury that the information provided in
    this petition is true and correct, and that I have been authorized
    to file this petition on behalf of the debtor.

    Schedules A through K and Statement of Financial Affairs for
    Individuals Filing for Bankruptcy (Official Form B7) are attached
    and made a part of this petition.

    Date: March 15, 2023

    /s/ John Doe Smith
    John Doe Smith, Debtor
    """

    # Initialize analyzer
    analyzer = DocumentIntakeAnalyzer()

    print("Testing Document Intelligence Core with Sample Bankruptcy Petition")
    print("=" * 70)

    try:
        # Perform complete analysis
        result = analyzer.analyze_document(sample_bankruptcy_text, "sample_petition.pdf")

        print(f"Document ID: {result.document_id}")
        print(f"Document Type: {result.document_type.category.value}")
        print(f"Confidence Score: {result.document_type.confidence_score:.3f}")
        print(f"Form Number: {result.document_type.form_number or 'Not detected'}")
        print(f"Jurisdiction: {result.document_type.jurisdiction or 'Not detected'}")
        print()

        print("IDENTIFYING FEATURES:")
        for feature in result.document_type.identifying_features[:3]:
            print(f"  • {feature}")
        print()

        print("EXTRACTED ENTITIES:")
        for entity in result.extracted_entities[:10]:  # Show top 10
            print(f"  • {entity.entity_type}: {entity.value} (confidence: {entity.confidence:.2f})")
        print()

        print("INFORMATION GAPS:")
        for gap in result.information_gaps:
            print(f"  • {gap.gap_type.upper()}: {gap.description}")
            print(f"    Severity: {gap.severity.value}")
            for suggestion in gap.suggestions[:2]:
                print(f"    → {suggestion}")
        print()

        print("ANALYSIS METADATA:")
        metadata = result.analysis_metadata
        print(f"  • Document Length: {metadata.get('document_length', 0)} characters")
        print(f"  • Word Count: {metadata.get('word_count', 0)} words")
        print(f"  • Entities Found: {metadata.get('total_entities_found', 0)}")
        print(f"  • Gaps Identified: {metadata.get('total_gaps_identified', 0)}")

        print("\n" + "=" * 70)
        print("DISCLAIMER: This analysis is for educational purposes only.")
        print("All results require attorney review and verification.")
        print("This does not constitute legal advice.")

        return result

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        return None


if __name__ == "__main__":
    # Run test when module is executed directly
    test_with_sample_bankruptcy_petition()