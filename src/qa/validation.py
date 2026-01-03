"""
Answer Validation System
Validates Q&A responses through cross-referencing, consistency checking, and expert review.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime
from decimal import Decimal
import uuid
import re
import difflib


class ValidationStatus(Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    FLAGGED = "flagged"
    EXPERT_REVIEW = "expert_review"
    REJECTED = "rejected"


class ConfidenceLevel(Enum):
    VERY_LOW = "very_low"      # 0-20%
    LOW = "low"                # 21-40%
    MODERATE = "moderate"       # 41-60%
    HIGH = "high"              # 61-80%
    VERY_HIGH = "very_high"    # 81-100%


class ValidationFlag(Enum):
    CONTRADICTION = "contradiction"
    INCONSISTENCY = "inconsistency"
    LOW_CONFIDENCE = "low_confidence"
    MISSING_CITATION = "missing_citation"
    OUTDATED_LAW = "outdated_law"
    JURISDICTION_MISMATCH = "jurisdiction_mismatch"
    EXPERT_REQUIRED = "expert_required"


@dataclass
class ValidationResult:
    validation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    answer_id: str = ""
    status: ValidationStatus = ValidationStatus.PENDING
    confidence_score: Decimal = field(default=Decimal("0.0"))
    confidence_level: ConfidenceLevel = ConfidenceLevel.VERY_LOW
    flags: List[ValidationFlag] = field(default_factory=list)
    cross_references: List[str] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    inconsistencies: List[Dict[str, Any]] = field(default_factory=list)
    expert_notes: str = ""
    validation_timestamp: datetime = field(default_factory=datetime.utcnow)
    validator_id: str = ""
    review_queue_priority: int = 0


@dataclass
class DocumentReference:
    document_id: str
    document_type: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    excerpt: str = ""
    relevance_score: Decimal = field(default=Decimal("0.0"))


@dataclass
class ConsistencyCheck:
    check_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    answer_id: str = ""
    related_answers: List[str] = field(default_factory=list)
    consistency_score: Decimal = field(default=Decimal("0.0"))
    inconsistencies: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ExpertReview:
    review_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    validation_id: str = ""
    expert_id: str = ""
    expert_type: str = ""  # "attorney", "judge", "legal_scholar"
    review_status: str = "pending"
    expert_opinion: str = ""
    corrections: List[str] = field(default_factory=list)
    approval_level: str = ""
    review_timestamp: datetime = field(default_factory=datetime.utcnow)


class AnswerValidator:
    def __init__(self):
        self.validation_results = {}
        self.document_index = {}
        self.consistency_cache = {}
        self.expert_queue = []

    async def validate_answer(self, answer: Dict[str, Any]) -> ValidationResult:
        """Validate an answer through comprehensive analysis"""
        validation = ValidationResult(
            answer_id=answer["answer_id"]
        )

        # Cross-reference with documents
        cross_refs = await self._cross_reference_documents(answer)
        validation.cross_references = cross_refs

        # Check for contradictions
        contradictions = await self._detect_contradictions(answer)
        validation.contradictions = contradictions

        # Consistency checking
        inconsistencies = await self._check_consistency(answer)
        validation.inconsistencies = inconsistencies

        # Calculate confidence score
        confidence = await self._calculate_confidence(answer, cross_refs, contradictions, inconsistencies)
        validation.confidence_score = confidence
        validation.confidence_level = self._determine_confidence_level(confidence)

        # Generate validation flags
        flags = await self._generate_flags(answer, validation)
        validation.flags = flags

        # Determine if expert review is needed
        if await self._needs_expert_review(validation):
            validation.status = ValidationStatus.EXPERT_REVIEW
            validation.review_queue_priority = await self._calculate_priority(validation)
            await self._queue_expert_review(validation)
        else:
            validation.status = ValidationStatus.VALIDATED

        self.validation_results[validation.validation_id] = validation
        return validation

    async def _cross_reference_documents(self, answer: Dict[str, Any]) -> List[str]:
        """Cross-reference answer with available documents"""
        references = []
        answer_text = answer.get("text", "").lower()

        # Extract potential legal citations
        citations = self._extract_citations(answer_text)

        for citation in citations:
            # Find matching documents
            matching_docs = await self._find_document_matches(citation)
            references.extend(matching_docs)

        # Search for topical matches
        key_terms = await self._extract_key_terms(answer_text)
        for term in key_terms:
            topical_matches = await self._find_topical_matches(term)
            references.extend(topical_matches)

        return list(set(references))  # Remove duplicates

    async def _detect_contradictions(self, answer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect contradictions between answer and known legal principles"""
        contradictions = []
        answer_text = answer.get("text", "")

        # Check against established legal principles
        principles = await self._get_legal_principles(answer.get("case_type", ""))

        for principle in principles:
            if await self._is_contradictory(answer_text, principle["text"]):
                contradiction = {
                    "type": "legal_principle",
                    "principle_id": principle["id"],
                    "principle_text": principle["text"],
                    "contradiction_reason": await self._analyze_contradiction(answer_text, principle["text"]),
                    "severity": "high"
                }
                contradictions.append(contradiction)

        # Check against previous similar answers
        similar_answers = await self._find_similar_answers(answer)
        for similar in similar_answers:
            if await self._is_contradictory(answer_text, similar["text"]):
                contradiction = {
                    "type": "previous_answer",
                    "answer_id": similar["answer_id"],
                    "similarity_score": similar["similarity_score"],
                    "contradiction_reason": await self._analyze_contradiction(answer_text, similar["text"]),
                    "severity": "medium"
                }
                contradictions.append(contradiction)

        return contradictions

    async def _check_consistency(self, answer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check consistency within the answer and with related answers"""
        inconsistencies = []
        answer_text = answer.get("text", "")

        # Internal consistency check
        internal_issues = await self._check_internal_consistency(answer_text)
        inconsistencies.extend(internal_issues)

        # Check against related Q&A pairs in same case
        case_id = answer.get("case_id")
        if case_id:
            related_qa = await self._get_case_qa_pairs(case_id)
            for qa_pair in related_qa:
                consistency_score = await self._calculate_consistency_score(answer_text, qa_pair["answer"])
                if consistency_score < Decimal("0.7"):  # Threshold for inconsistency
                    inconsistency = {
                        "type": "case_inconsistency",
                        "related_qa_id": qa_pair["id"],
                        "consistency_score": consistency_score,
                        "issue_description": await self._describe_inconsistency(answer_text, qa_pair["answer"])
                    }
                    inconsistencies.append(inconsistency)

        return inconsistencies

    async def _calculate_confidence(self, answer: Dict[str, Any], cross_refs: List[str],
                                  contradictions: List[Dict], inconsistencies: List[Dict]) -> Decimal:
        """Calculate confidence score for the answer"""
        base_score = Decimal("50.0")  # Start with neutral confidence

        # Boost for strong cross-references
        ref_boost = min(Decimal("30.0"), Decimal(str(len(cross_refs) * 5)))
        base_score += ref_boost

        # Penalty for contradictions
        contradiction_penalty = Decimal(str(len(contradictions) * 15))
        base_score -= contradiction_penalty

        # Penalty for inconsistencies
        inconsistency_penalty = Decimal(str(len(inconsistencies) * 10))
        base_score -= inconsistency_penalty

        # Factor in answer quality metrics
        quality_metrics = await self._analyze_answer_quality(answer)
        quality_adjustment = quality_metrics.get("overall_score", Decimal("0.0"))
        base_score += quality_adjustment

        # Ensure score is within bounds
        final_score = max(Decimal("0.0"), min(Decimal("100.0"), base_score))
        return final_score

    def _determine_confidence_level(self, score: Decimal) -> ConfidenceLevel:
        """Convert numeric confidence score to confidence level"""
        if score <= Decimal("20.0"):
            return ConfidenceLevel.VERY_LOW
        elif score <= Decimal("40.0"):
            return ConfidenceLevel.LOW
        elif score <= Decimal("60.0"):
            return ConfidenceLevel.MODERATE
        elif score <= Decimal("80.0"):
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH

    async def _generate_flags(self, answer: Dict[str, Any], validation: ValidationResult) -> List[ValidationFlag]:
        """Generate validation flags based on analysis"""
        flags = []

        if validation.contradictions:
            flags.append(ValidationFlag.CONTRADICTION)

        if validation.inconsistencies:
            flags.append(ValidationFlag.INCONSISTENCY)

        if validation.confidence_level in [ConfidenceLevel.VERY_LOW, ConfidenceLevel.LOW]:
            flags.append(ValidationFlag.LOW_CONFIDENCE)

        # Check for missing citations
        if not self._has_adequate_citations(answer.get("text", "")):
            flags.append(ValidationFlag.MISSING_CITATION)

        # Check for jurisdiction matching
        if not await self._matches_jurisdiction(answer):
            flags.append(ValidationFlag.JURISDICTION_MISMATCH)

        # Complex legal matters requiring expert review
        if await self._requires_expert_analysis(answer):
            flags.append(ValidationFlag.EXPERT_REQUIRED)

        return flags

    async def _needs_expert_review(self, validation: ValidationResult) -> bool:
        """Determine if answer needs expert review"""
        # High-priority flags that require expert review
        expert_flags = [
            ValidationFlag.CONTRADICTION,
            ValidationFlag.EXPERT_REQUIRED,
            ValidationFlag.JURISDICTION_MISMATCH
        ]

        if any(flag in validation.flags for flag in expert_flags):
            return True

        # Low confidence requires review
        if validation.confidence_level == ConfidenceLevel.VERY_LOW:
            return True

        # Multiple flags indicate need for review
        if len(validation.flags) >= 3:
            return True

        return False

    async def _calculate_priority(self, validation: ValidationResult) -> int:
        """Calculate priority for expert review queue (higher = more urgent)"""
        priority = 0

        # High priority flags
        if ValidationFlag.CONTRADICTION in validation.flags:
            priority += 10
        if ValidationFlag.EXPERT_REQUIRED in validation.flags:
            priority += 8
        if ValidationFlag.JURISDICTION_MISMATCH in validation.flags:
            priority += 6

        # Confidence level affects priority
        confidence_priorities = {
            ConfidenceLevel.VERY_LOW: 7,
            ConfidenceLevel.LOW: 4,
            ConfidenceLevel.MODERATE: 2,
            ConfidenceLevel.HIGH: 1,
            ConfidenceLevel.VERY_HIGH: 0
        }
        priority += confidence_priorities[validation.confidence_level]

        # Number of flags
        priority += len(validation.flags)

        return priority

    async def _queue_expert_review(self, validation: ValidationResult):
        """Add validation to expert review queue"""
        review = ExpertReview(
            validation_id=validation.validation_id,
            expert_type="attorney"  # Default, can be specialized based on case type
        )

        # Insert into queue based on priority
        inserted = False
        for i, existing_review in enumerate(self.expert_queue):
            existing_validation = self.validation_results.get(existing_review.validation_id)
            if existing_validation and validation.review_queue_priority > existing_validation.review_queue_priority:
                self.expert_queue.insert(i, review)
                inserted = True
                break

        if not inserted:
            self.expert_queue.append(review)

    # Helper methods for document analysis
    def _extract_citations(self, text: str) -> List[str]:
        """Extract legal citations from text"""
        citation_patterns = [
            r'\d+\s+[A-Z][a-z]+\.?\s+\d+',  # Standard case citation
            r'\d+\s+U\.S\.C\.?\s+§?\s*\d+',  # US Code
            r'\d+\s+F\.\d+d?\s+\d+',  # Federal Reporter
            r'\d+\s+S\.Ct\.\s+\d+',  # Supreme Court Reporter
        ]

        citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)

        return citations

    async def _find_document_matches(self, citation: str) -> List[str]:
        """Find documents matching a citation"""
        # Mock implementation - would search document database
        return [f"doc_{hash(citation) % 1000}"]

    async def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key legal terms from text"""
        # Mock implementation - would use NLP to extract legal concepts
        legal_terms = [
            "contract", "liability", "negligence", "damages", "jurisdiction",
            "statute of limitations", "due process", "constitutional", "precedent"
        ]

        found_terms = []
        text_lower = text.lower()
        for term in legal_terms:
            if term in text_lower:
                found_terms.append(term)

        return found_terms

    async def _find_topical_matches(self, term: str) -> List[str]:
        """Find documents matching a topic"""
        # Mock implementation - would search by topic
        return [f"topic_doc_{hash(term) % 1000}"]

    async def _get_legal_principles(self, case_type: str) -> List[Dict[str, Any]]:
        """Get established legal principles for case type"""
        # Mock implementation - would query legal principle database
        return [
            {
                "id": "principle_1",
                "text": "The burden of proof in civil cases is preponderance of evidence",
                "case_types": ["civil", "contract"]
            }
        ]

    async def _is_contradictory(self, text1: str, text2: str) -> bool:
        """Check if two texts are contradictory"""
        # Mock implementation - would use NLP to detect contradictions
        similarity = difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        return similarity < 0.3  # Very different texts might be contradictory

    async def _analyze_contradiction(self, answer_text: str, principle_text: str) -> str:
        """Analyze why two texts are contradictory"""
        return f"Answer contradicts established principle: {principle_text[:100]}..."

    async def _find_similar_answers(self, answer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar previous answers"""
        # Mock implementation
        return []

    async def _check_internal_consistency(self, text: str) -> List[Dict[str, Any]]:
        """Check for internal inconsistencies within answer"""
        inconsistencies = []

        # Check for contradictory statements within the same answer
        sentences = text.split('. ')
        for i, sent1 in enumerate(sentences):
            for j, sent2 in enumerate(sentences[i+1:], i+1):
                if await self._is_contradictory(sent1, sent2):
                    inconsistency = {
                        "type": "internal_contradiction",
                        "sentence1": sent1,
                        "sentence2": sent2,
                        "position1": i,
                        "position2": j
                    }
                    inconsistencies.append(inconsistency)

        return inconsistencies

    async def _get_case_qa_pairs(self, case_id: str) -> List[Dict[str, Any]]:
        """Get all Q&A pairs for a case"""
        # Mock implementation
        return []

    async def _calculate_consistency_score(self, text1: str, text2: str) -> Decimal:
        """Calculate consistency score between two texts"""
        similarity = difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        return Decimal(str(similarity))

    async def _describe_inconsistency(self, text1: str, text2: str) -> str:
        """Describe the inconsistency between two texts"""
        return "Inconsistent legal interpretation or facts"

    async def _analyze_answer_quality(self, answer: Dict[str, Any]) -> Dict[str, Decimal]:
        """Analyze overall quality metrics of answer"""
        text = answer.get("text", "")

        # Length analysis
        length_score = min(Decimal("10.0"), Decimal(str(len(text.split()) / 10)))

        # Citation density
        citations = self._extract_citations(text)
        citation_score = min(Decimal("10.0"), Decimal(str(len(citations) * 2)))

        # Legal terminology usage
        legal_terms = await self._extract_key_terms(text)
        terminology_score = min(Decimal("10.0"), Decimal(str(len(legal_terms))))

        overall_score = (length_score + citation_score + terminology_score) / Decimal("3.0")

        return {
            "length_score": length_score,
            "citation_score": citation_score,
            "terminology_score": terminology_score,
            "overall_score": overall_score
        }

    def _has_adequate_citations(self, text: str) -> bool:
        """Check if answer has adequate legal citations"""
        citations = self._extract_citations(text)
        word_count = len(text.split())

        # Rule of thumb: at least one citation per 100 words for legal answers
        required_citations = max(1, word_count // 100)
        return len(citations) >= required_citations

    async def _matches_jurisdiction(self, answer: Dict[str, Any]) -> bool:
        """Check if answer matches the required jurisdiction"""
        # Mock implementation - would check jurisdiction-specific laws and precedents
        return True

    async def _requires_expert_analysis(self, answer: Dict[str, Any]) -> bool:
        """Check if answer involves complex legal matters requiring expert review"""
        complex_terms = [
            "constitutional law", "federal jurisdiction", "appellate procedure",
            "class action", "securities fraud", "patent law", "tax law"
        ]

        text = answer.get("text", "").lower()
        return any(term in text for term in complex_terms)


# Global validator instance
answer_validator = AnswerValidator()


async def get_validation_endpoints() -> List[Dict[str, str]]:
    """Get all validation endpoints"""
    return [
        {"method": "POST", "path": "/qa/validate"},
        {"method": "GET", "path": "/qa/validations/{validation_id}"},
        {"method": "POST", "path": "/qa/expert-review"},
        {"method": "GET", "path": "/qa/expert-queue"},
        {"method": "PUT", "path": "/qa/expert-review/{review_id}"},
        {"method": "GET", "path": "/qa/validation-stats"},
        {"method": "POST", "path": "/qa/bulk-validate"},
        {"method": "GET", "path": "/qa/flagged-answers"},
    ]


async def initialize_answer_validation() -> bool:
    """Initialize the answer validation system"""
    try:
        print("Answer Validation System initialized successfully")
        print("Available endpoints: 8")
        return True
    except Exception as e:
        print(f"Error initializing validation system: {e}")
        return False