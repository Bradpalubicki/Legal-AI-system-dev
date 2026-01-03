#!/usr/bin/env python3
"""
Document Classification Engine
Legal AI System - Educational Document Categorization

This module provides secure document classification with:
- Document type identification (motion, petition, order)
- Key metadata extraction for educational purposes
- Confidence scoring for classification accuracy
- Educational categorization only (no legal advice)
- Attorney review flagging for compliance
"""

import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Import system components
from ..core.attorney_review import AttorneyReviewSystem
from ..core.audit_logger import AuditLogger
from ..core.security import encrypt_data, decrypt_data
from .ocr_processor import ocr_processor

# Setup logging
logger = logging.getLogger('document_classifier')

class DocumentTypeCategory(str, Enum):
    """Legal document type categories - Educational Only"""
    MOTION = "motion"
    PETITION = "petition"
    ORDER = "order"
    COMPLAINT = "complaint"
    ANSWER = "answer"
    BRIEF = "brief"
    CONTRACT = "contract"
    CORRESPONDENCE = "correspondence"
    FINANCIAL = "financial"
    PROCEDURAL = "procedural"
    UNKNOWN = "unknown"

class ClassificationConfidence(str, Enum):
    """Classification confidence levels"""
    HIGH = "high"      # 90%+
    MEDIUM = "medium"  # 70-89%
    LOW = "low"        # 50-69%
    UNCERTAIN = "uncertain"  # <50%

class EducationalCategory(str, Enum):
    """Educational categorization for learning purposes"""
    BANKRUPTCY_PROCEDURE = "bankruptcy_procedure"
    CIVIL_PROCEDURE = "civil_procedure"
    CONTRACT_LAW = "contract_law"
    FAMILY_LAW = "family_law"
    CRIMINAL_LAW = "criminal_law"
    EMPLOYMENT_LAW = "employment_law"
    REAL_ESTATE = "real_estate"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    GENERAL_LEGAL = "general_legal"
    ADMINISTRATIVE = "administrative"

@dataclass
class KeyMetadata:
    """Key document metadata for educational analysis"""
    document_title: Optional[str]
    case_number: Optional[str]
    court_name: Optional[str]
    parties_involved: List[str]
    filing_date: Optional[datetime]
    document_date: Optional[datetime]
    attorney_names: List[str]
    jurisdiction: Optional[str]
    subject_matter: List[str]
    key_dates: List[Tuple[str, datetime]]  # (description, date)

@dataclass
class ClassificationResult:
    """Document classification result"""
    classification_id: str
    document_id: str
    ocr_id: Optional[str]
    document_type: DocumentTypeCategory
    educational_category: EducationalCategory
    confidence_score: float
    confidence_level: ClassificationConfidence
    key_metadata: KeyMetadata
    extracted_patterns: Dict[str, List[str]]
    educational_tags: List[str]
    compliance_flags: List[str]
    attorney_review_required: bool
    processing_time: float
    created_at: datetime
    warnings: List[str]
    disclaimer_required: bool

class DocumentClassificationEngine:
    """
    Educational document classification system with compliance safeguards
    """

    def __init__(self, storage_root: str = "storage/classification"):
        self.logger = logger
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # Initialize compliance components
        self.attorney_review = AttorneyReviewSystem()
        self.audit_logger = AuditLogger()

        # Load classification patterns
        self._load_classification_patterns()

        # Educational disclaimer
        self.educational_disclaimer = """
        EDUCATIONAL PURPOSES ONLY - NOT LEGAL ADVICE

        This classification is provided for educational and informational purposes only.
        It does not constitute legal advice and should not be relied upon for legal decisions.
        Always consult with a qualified attorney for legal advice specific to your situation.
        """

    def _load_classification_patterns(self):
        """Load patterns for document classification"""

        # Document type patterns - Educational identification only
        self.document_patterns = {
            DocumentTypeCategory.MOTION: [
                r"motion\s+(?:for|to)\s+(?:dismiss|summary\s+judgment|compel|strike)",
                r"notice\s+of\s+motion",
                r"plaintiff(?:'s)?\s+motion",
                r"defendant(?:'s)?\s+motion",
                r"motion\s+(?:in\s+)?limine",
                r"ex\s+parte\s+motion"
            ],
            DocumentTypeCategory.PETITION: [
                r"petition\s+(?:for|to)\s+(?:relief|bankruptcy|dissolution)",
                r"voluntary\s+petition",
                r"involuntary\s+petition",
                r"chapter\s+\d+\s+petition",
                r"petition\s+for\s+(?:writ|mandamus|certiorari)"
            ],
            DocumentTypeCategory.ORDER: [
                r"order\s+(?:granting|denying|dismissing)",
                r"preliminary\s+injunction",
                r"temporary\s+restraining\s+order",
                r"final\s+judgment",
                r"order\s+to\s+show\s+cause",
                r"consent\s+order"
            ],
            DocumentTypeCategory.COMPLAINT: [
                r"complaint\s+(?:for|and)",
                r"verified\s+complaint",
                r"first\s+amended\s+complaint",
                r"class\s+action\s+complaint",
                r"plaintiff\s+alleges"
            ],
            DocumentTypeCategory.BRIEF: [
                r"brief\s+(?:in\s+)?(?:support|opposition)",
                r"memorandum\s+(?:of\s+)?(?:law|points)",
                r"reply\s+brief",
                r"amicus\s+(?:curiae\s+)?brief"
            ]
        }

        # Educational category patterns
        self.educational_patterns = {
            EducationalCategory.BANKRUPTCY_PROCEDURE: [
                r"chapter\s+(?:7|11|13)\s+(?:bankruptcy|petition)",
                r"automatic\s+stay",
                r"discharge\s+of\s+debts?",
                r"trustee\s+appointment",
                r"creditor(?:'s)?\s+meeting",
                r"bankruptcy\s+estate",
                r"preference\s+payments?"
            ],
            EducationalCategory.CIVIL_PROCEDURE: [
                r"rule\s+\d+\s+motion",
                r"service\s+of\s+process",
                r"discovery\s+(?:request|motion)",
                r"summary\s+judgment",
                r"voir\s+dire",
                r"directed\s+verdict"
            ],
            EducationalCategory.CONTRACT_LAW: [
                r"breach\s+of\s+contract",
                r"consideration",
                r"specific\s+performance",
                r"contract\s+interpretation",
                r"mutual\s+assent",
                r"statute\s+of\s+frauds"
            ]
        }

        # Metadata extraction patterns
        self.metadata_patterns = {
            'case_number': [
                r"case\s+no\.?\s*:?\s*([a-z]?\d+[-\s]*\d+)",
                r"civil\s+action\s+no\.?\s*:?\s*([a-z]?\d+[-\s]*\d+)",
                r"bankruptcy\s+case\s+no\.?\s*:?\s*([a-z]?\d+[-\s]*\d+)"
            ],
            'court_name': [
                r"united\s+states\s+(?:district\s+)?court",
                r"(?:superior|municipal|county)\s+court",
                r"court\s+of\s+(?:appeals|common\s+pleas)",
                r"bankruptcy\s+court"
            ],
            'attorney_names': [
                r"attorney\s+for\s+(?:plaintiff|defendant)\s*:?\s*([a-z\s,\.]+)",
                r"counsel\s+for\s+(?:plaintiff|defendant)\s*:?\s*([a-z\s,\.]+)",
                r"esq\.?\s*([a-z\s,\.]+)"
            ],
            'dates': [
                r"filed\s+(?:on\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
                r"dated\s+(?:this\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
                r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"
            ]
        }

    def classify_document(self, document_id: str, user_id: str) -> ClassificationResult:
        """
        Classify document for educational purposes

        Args:
            document_id: ID of document to classify
            user_id: User requesting classification

        Returns:
            ClassificationResult with educational categorization
        """
        start_time = datetime.now()
        warnings = []

        try:
            self.logger.info(f"Starting document classification: {document_id}")

            # Generate classification ID
            classification_id = f"cls_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Get OCR results for document
            ocr_results = ocr_processor.get_document_ocr_results(document_id)
            if not ocr_results:
                warnings.append("No OCR results found - classification may be limited")
                text_content = ""
                ocr_id = None
            else:
                # Use the most recent OCR result
                latest_ocr = ocr_results[0]
                text_content = latest_ocr.extracted_text
                ocr_id = latest_ocr.ocr_id

                if latest_ocr.confidence_level.value in ['low', 'poor']:
                    warnings.append("OCR confidence is low - classification accuracy may be reduced")

            # Perform classification
            document_type, type_confidence = self._classify_document_type(text_content)
            educational_category, edu_confidence = self._classify_educational_category(text_content)

            # Calculate overall confidence
            overall_confidence = (type_confidence + edu_confidence) / 2

            # Extract metadata
            key_metadata = self._extract_key_metadata(text_content)

            # Extract patterns for educational analysis
            extracted_patterns = self._extract_educational_patterns(text_content)

            # Generate educational tags
            educational_tags = self._generate_educational_tags(document_type, educational_category, text_content)

            # Check compliance requirements
            compliance_flags = self._check_compliance_flags(text_content, document_type)
            attorney_review_required = self._check_attorney_review_requirement(text_content, document_type)

            processing_time = (datetime.now() - start_time).total_seconds()

            result = ClassificationResult(
                classification_id=classification_id,
                document_id=document_id,
                ocr_id=ocr_id,
                document_type=document_type,
                educational_category=educational_category,
                confidence_score=overall_confidence,
                confidence_level=self._determine_confidence_level(overall_confidence),
                key_metadata=key_metadata,
                extracted_patterns=extracted_patterns,
                educational_tags=educational_tags,
                compliance_flags=compliance_flags,
                attorney_review_required=attorney_review_required,
                processing_time=processing_time,
                created_at=datetime.now(),
                warnings=warnings,
                disclaimer_required=True  # Always require disclaimer
            )

            # Store classification result
            self._store_classification_result(result)

            # Log classification for audit
            self._log_classification_event(result, user_id)

            return result

        except Exception as e:
            self.logger.error(f"Document classification failed: {e}")
            return self._create_failed_classification(document_id, classification_id, str(e), start_time)

    def _classify_document_type(self, text_content: str) -> Tuple[DocumentTypeCategory, float]:
        """Classify document type with confidence score"""
        text_lower = text_content.lower()
        type_scores = {}

        for doc_type, patterns in self.document_patterns.items():
            score = 0
            matches = 0

            for pattern in patterns:
                pattern_matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                if pattern_matches > 0:
                    score += pattern_matches * 10  # Weight each match
                    matches += 1

            # Bonus for multiple pattern matches
            if matches > 1:
                score += matches * 5

            type_scores[doc_type] = score

        # Find best match
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            max_score = type_scores[best_type]

            # Convert score to confidence percentage
            confidence = min(100.0, max_score * 2)  # Scale to percentage

            if confidence >= 50:
                return best_type, confidence
            else:
                return DocumentTypeCategory.UNKNOWN, confidence
        else:
            return DocumentTypeCategory.UNKNOWN, 0.0

    def _classify_educational_category(self, text_content: str) -> Tuple[EducationalCategory, float]:
        """Classify educational category with confidence score"""
        text_lower = text_content.lower()
        category_scores = {}

        for category, patterns in self.educational_patterns.items():
            score = 0
            matches = 0

            for pattern in patterns:
                pattern_matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                if pattern_matches > 0:
                    score += pattern_matches * 15  # Higher weight for educational patterns
                    matches += 1

            # Bonus for multiple pattern matches
            if matches > 1:
                score += matches * 8

            category_scores[category] = score

        # Find best match
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            max_score = category_scores[best_category]

            # Convert score to confidence percentage
            confidence = min(100.0, max_score * 1.5)  # Scale to percentage

            if confidence >= 40:  # Lower threshold for educational categories
                return best_category, confidence
            else:
                return EducationalCategory.GENERAL_LEGAL, confidence
        else:
            return EducationalCategory.GENERAL_LEGAL, 0.0

    def _extract_key_metadata(self, text_content: str) -> KeyMetadata:
        """Extract key metadata for educational purposes"""
        try:
            # Extract case number
            case_number = self._extract_pattern_match(text_content, self.metadata_patterns['case_number'])

            # Extract court name
            court_name = self._extract_pattern_match(text_content, self.metadata_patterns['court_name'])

            # Extract attorney names
            attorney_names = self._extract_pattern_matches(text_content, self.metadata_patterns['attorney_names'])

            # Extract dates
            date_matches = self._extract_pattern_matches(text_content, self.metadata_patterns['dates'])
            key_dates = [(f"Document date {i+1}", self._parse_date(date))
                        for i, date in enumerate(date_matches) if self._parse_date(date)]

            # Extract parties (simplified pattern)
            parties = self._extract_parties(text_content)

            # Extract document title (first meaningful line)
            document_title = self._extract_document_title(text_content)

            return KeyMetadata(
                document_title=document_title,
                case_number=case_number,
                court_name=court_name,
                parties_involved=parties,
                filing_date=key_dates[0][1] if key_dates else None,
                document_date=key_dates[0][1] if key_dates else None,
                attorney_names=attorney_names,
                jurisdiction=self._extract_jurisdiction(text_content),
                subject_matter=self._extract_subject_matter(text_content),
                key_dates=key_dates
            )

        except Exception as e:
            self.logger.error(f"Metadata extraction failed: {e}")
            return KeyMetadata(
                document_title=None, case_number=None, court_name=None,
                parties_involved=[], filing_date=None, document_date=None,
                attorney_names=[], jurisdiction=None, subject_matter=[],
                key_dates=[]
            )

    def _extract_pattern_match(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract first matching pattern"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None

    def _extract_pattern_matches(self, text: str, patterns: List[str]) -> List[str]:
        """Extract all matching patterns"""
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            matches.extend(found)
        return list(set(matches))  # Remove duplicates

    def _extract_parties(self, text_content: str) -> List[str]:
        """Extract party names for educational analysis"""
        party_patterns = [
            r"plaintiff(?:s)?\s*:?\s*([a-z\s,\.]+?)(?:\s+(?:v|vs|versus))",
            r"defendant(?:s)?\s*:?\s*([a-z\s,\.]+?)(?:\s+(?:,|;|\n))",
            r"debtor(?:s)?\s*:?\s*([a-z\s,\.]+?)(?:\s+(?:,|;|\n))"
        ]

        parties = []
        for pattern in party_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            parties.extend([match.strip() for match in matches if len(match.strip()) > 2])

        return list(set(parties))[:5]  # Limit to 5 parties for privacy

    def _extract_document_title(self, text_content: str) -> Optional[str]:
        """Extract document title for educational purposes"""
        lines = text_content.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 10 and not line.isdigit():
                # Check if line looks like a title
                if any(keyword in line.lower() for keyword in ['motion', 'petition', 'order', 'brief', 'complaint']):
                    return line[:100]  # Limit length
        return None

    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        try:
            # Try common date formats
            for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            return None
        except:
            return None

    def _extract_jurisdiction(self, text_content: str) -> Optional[str]:
        """Extract jurisdiction information"""
        jurisdiction_patterns = [
            r"(?:state\s+of\s+|commonwealth\s+of\s+)([a-z\s]+)",
            r"([a-z\s]+)\s+(?:district\s+court|superior\s+court)"
        ]

        for pattern in jurisdiction_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_subject_matter(self, text_content: str) -> List[str]:
        """Extract subject matter topics for educational categorization"""
        subject_keywords = [
            'contract', 'tort', 'negligence', 'bankruptcy', 'divorce',
            'custody', 'employment', 'discrimination', 'intellectual property',
            'copyright', 'trademark', 'real estate', 'foreclosure'
        ]

        found_subjects = []
        text_lower = text_content.lower()

        for keyword in subject_keywords:
            if keyword in text_lower:
                found_subjects.append(keyword)

        return found_subjects

    def _extract_educational_patterns(self, text_content: str) -> Dict[str, List[str]]:
        """Extract patterns for educational analysis"""
        patterns = {}

        # Legal citations (educational analysis)
        citation_pattern = r'\d+\s+[A-Z][a-z]+\s+\d+'
        citations = re.findall(citation_pattern, text_content)
        patterns['citations'] = citations[:10]  # Limit for performance

        # Legal terms (educational analysis)
        legal_terms = [
            'jurisdiction', 'venue', 'standing', 'res judicata', 'collateral estoppel',
            'due process', 'equal protection', 'commerce clause', 'sovereign immunity'
        ]
        found_terms = [term for term in legal_terms if term.lower() in text_content.lower()]
        patterns['legal_terms'] = found_terms

        # Procedural terms
        procedural_terms = [
            'motion to dismiss', 'summary judgment', 'discovery', 'deposition',
            'interrogatories', 'requests for admission', 'voir dire'
        ]
        found_procedural = [term for term in procedural_terms if term.lower() in text_content.lower()]
        patterns['procedural_terms'] = found_procedural

        return patterns

    def _generate_educational_tags(self, document_type: DocumentTypeCategory,
                                 educational_category: EducationalCategory,
                                 text_content: str) -> List[str]:
        """Generate educational tags for learning purposes"""
        tags = []

        # Add type-based tags
        tags.append(f"document_type_{document_type.value}")
        tags.append(f"educational_category_{educational_category.value}")

        # Add content-based educational tags
        if 'bankruptcy' in text_content.lower():
            tags.extend(['bankruptcy_law', 'debtor_creditor_relations', 'financial_distress'])

        if any(term in text_content.lower() for term in ['motion', 'hearing', 'court']):
            tags.append('court_procedures')

        if 'contract' in text_content.lower():
            tags.extend(['contract_law', 'commercial_law'])

        # Educational complexity tags
        legal_term_count = sum(1 for term in ['whereas', 'therefore', 'heretofore', 'jurisdiction']
                              if term in text_content.lower())
        if legal_term_count > 5:
            tags.append('complex_legal_language')
        else:
            tags.append('standard_legal_language')

        return list(set(tags))  # Remove duplicates

    def _check_compliance_flags(self, text_content: str, document_type: DocumentTypeCategory) -> List[str]:
        """Check for compliance flags requiring attention"""
        flags = []

        # Flag sensitive content
        sensitive_terms = ['privileged', 'confidential', 'attorney-client', 'work product']
        if any(term in text_content.lower() for term in sensitive_terms):
            flags.append('contains_privileged_content')

        # Flag financial information
        if re.search(r'\$[\d,]+', text_content):
            flags.append('contains_financial_information')

        # Flag personal information patterns
        if re.search(r'\d{3}-\d{2}-\d{4}', text_content):  # SSN pattern
            flags.append('contains_personal_identifiers')

        # Flag court-sensitive documents
        if document_type in [DocumentTypeCategory.MOTION, DocumentTypeCategory.PETITION]:
            flags.append('active_litigation_document')

        return flags

    def _check_attorney_review_requirement(self, text_content: str,
                                         document_type: DocumentTypeCategory) -> bool:
        """Determine if attorney review is required"""
        # Use the attorney review system
        review_result = self.attorney_review.review_content(
            content=text_content[:1000],  # First 1000 chars for analysis
            content_id=f"classification_{document_type.value}"
        )

        return review_result.requires_review

    def _determine_confidence_level(self, confidence_score: float) -> ClassificationConfidence:
        """Determine confidence level from score"""
        if confidence_score >= 90:
            return ClassificationConfidence.HIGH
        elif confidence_score >= 70:
            return ClassificationConfidence.MEDIUM
        elif confidence_score >= 50:
            return ClassificationConfidence.LOW
        else:
            return ClassificationConfidence.UNCERTAIN

    def _create_failed_classification(self, document_id: str, classification_id: str,
                                    error: str, start_time: datetime) -> ClassificationResult:
        """Create failed classification result"""
        processing_time = (datetime.now() - start_time).total_seconds()

        return ClassificationResult(
            classification_id=classification_id,
            document_id=document_id,
            ocr_id=None,
            document_type=DocumentTypeCategory.UNKNOWN,
            educational_category=EducationalCategory.GENERAL_LEGAL,
            confidence_score=0.0,
            confidence_level=ClassificationConfidence.UNCERTAIN,
            key_metadata=KeyMetadata(
                document_title=None, case_number=None, court_name=None,
                parties_involved=[], filing_date=None, document_date=None,
                attorney_names=[], jurisdiction=None, subject_matter=[],
                key_dates=[]
            ),
            extracted_patterns={},
            educational_tags=['classification_failed'],
            compliance_flags=['processing_error'],
            attorney_review_required=True,
            processing_time=processing_time,
            created_at=datetime.now(),
            warnings=[f"Classification failed: {error}"],
            disclaimer_required=True
        )

    def _store_classification_result(self, result: ClassificationResult):
        """Store classification result securely"""
        try:
            storage_path = self.storage_root / f"{result.classification_id}.json"

            # Convert to dict and handle datetime serialization
            result_dict = asdict(result)

            # Encrypt and store
            result_data = json.dumps(result_dict, default=str)
            encrypted_data = encrypt_data(result_data.encode(), f"cls_{result.classification_id}")

            with open(storage_path, 'wb') as f:
                f.write(encrypted_data)

            # Set secure permissions
            import os
            os.chmod(storage_path, 0o600)

            self.logger.info(f"Classification result stored: {result.classification_id}")

        except Exception as e:
            self.logger.error(f"Failed to store classification result: {e}")
            raise

    def _log_classification_event(self, result: ClassificationResult, user_id: str):
        """Log classification event for audit"""
        self.audit_logger.log_document_event(
            event_type="document_classified",
            document_id=result.document_id,
            user_id=user_id,
            details={
                "classification_id": result.classification_id,
                "document_type": result.document_type.value,
                "educational_category": result.educational_category.value,
                "confidence_score": result.confidence_score,
                "attorney_review_required": result.attorney_review_required,
                "compliance_flags": result.compliance_flags
            }
        )

    def retrieve_classification_result(self, classification_id: str) -> Optional[ClassificationResult]:
        """Retrieve classification result by ID"""
        try:
            storage_path = self.storage_root / f"{classification_id}.json"
            if not storage_path.exists():
                return None

            # Load and decrypt
            with open(storage_path, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = decrypt_data(encrypted_data, f"cls_{classification_id}")
            result_dict = json.loads(decrypted_data.decode())

            # Convert datetime fields
            result_dict['created_at'] = datetime.fromisoformat(result_dict['created_at'])

            # Convert key_metadata dates
            metadata = result_dict['key_metadata']
            if metadata['filing_date']:
                metadata['filing_date'] = datetime.fromisoformat(metadata['filing_date'])
            if metadata['document_date']:
                metadata['document_date'] = datetime.fromisoformat(metadata['document_date'])

            # Convert key_dates
            key_dates = []
            for desc, date_str in metadata['key_dates']:
                if date_str:
                    key_dates.append((desc, datetime.fromisoformat(date_str)))
            metadata['key_dates'] = key_dates

            result_dict['key_metadata'] = KeyMetadata(**metadata)

            return ClassificationResult(**result_dict)

        except Exception as e:
            self.logger.error(f"Failed to retrieve classification result: {e}")
            return None

    def get_classification_statistics(self) -> Dict[str, Any]:
        """Get classification statistics"""
        try:
            total_classified = 0
            type_distribution = {dtype.value: 0 for dtype in DocumentTypeCategory}
            category_distribution = {cat.value: 0 for cat in EducationalCategory}
            confidence_distribution = {conf.value: 0 for conf in ClassificationConfidence}

            for cls_file in self.storage_root.glob("*.json"):
                result = self.retrieve_classification_result(cls_file.stem)
                if result:
                    total_classified += 1
                    type_distribution[result.document_type.value] += 1
                    category_distribution[result.educational_category.value] += 1
                    confidence_distribution[result.confidence_level.value] += 1

            return {
                "total_classified": total_classified,
                "document_type_distribution": type_distribution,
                "educational_category_distribution": category_distribution,
                "confidence_distribution": confidence_distribution,
                "educational_disclaimer": self.educational_disclaimer
            }

        except Exception as e:
            self.logger.error(f"Failed to get classification statistics: {e}")
            return {"error": str(e)}

# Global classification engine
classification_engine = DocumentClassificationEngine()

def validate_classification_system():
    """Validate document classification system"""
    try:
        print("✓ Document classification engine initialized")

        # Test with sample legal text
        sample_text = """
        MOTION FOR SUMMARY JUDGMENT

        Case No. 2023-CV-1234
        In the United States District Court

        Plaintiff John Doe vs. Defendant Jane Smith

        Motion for summary judgment pursuant to Rule 56.
        This bankruptcy case involves Chapter 7 proceedings.
        """

        # Create temporary document for testing
        from .upload_handler import document_uploader
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_text)
            temp_path = f.name

        try:
            # Upload test document
            with open(temp_path, 'rb') as f:
                test_data = f.read()

            upload_result = document_uploader.upload_document(test_data, "test_motion.txt", "test_user")

            if upload_result.success:
                # Process OCR
                ocr_result = ocr_processor.process_document(upload_result.document_id, "test_user")

                if ocr_result.status.value == "completed":
                    # Classify document
                    classification_result = classification_engine.classify_document(
                        upload_result.document_id, "test_user"
                    )

                    print("✓ Document classification completed")
                    print(f"  Document Type: {classification_result.document_type.value}")
                    print(f"  Educational Category: {classification_result.educational_category.value}")
                    print(f"  Confidence: {classification_result.confidence_score:.1f}%")
                    print(f"  Attorney Review Required: {classification_result.attorney_review_required}")
                    print(f"  Educational Tags: {', '.join(classification_result.educational_tags[:3])}")

                    return True
                else:
                    print("✗ OCR processing failed for classification test")
                    return False
            else:
                print("✗ Test document upload failed")
                return False

        finally:
            import os
            os.unlink(temp_path)

    except Exception as e:
        print(f"✗ Classification system validation failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Document Classification Engine...")
    print("=" * 50)

    if validate_classification_system():
        # Display statistics
        stats = classification_engine.get_classification_statistics()
        print(f"\nClassification Statistics:")
        for key, value in stats.items():
            if key != "educational_disclaimer":
                print(f"  {key}: {value}")

        print("\n" + "=" * 50)
        print("EDUCATIONAL DISCLAIMER:")
        print(stats.get("educational_disclaimer", ""))
    else:
        print("Classification system validation failed")