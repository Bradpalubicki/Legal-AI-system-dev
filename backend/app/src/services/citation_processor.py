"""
Citation Processing Service

Automatic extraction, validation, and enrichment of legal citations.
Uses Eyecite library for citation parsing and validation.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# CITATION TYPES & MODELS
# =============================================================================

class CitationType(str, Enum):
    """Types of legal citations"""
    CASE = "case"  # Case law citation
    STATUTE = "statute"  # Statutory citation
    REGULATION = "regulation"  # Regulatory citation
    CONSTITUTION = "constitution"  # Constitutional citation
    SECONDARY = "secondary"  # Secondary source (law review, treatise)
    UNKNOWN = "unknown"


class CitationStatus(str, Enum):
    """Citation validation status"""
    VALID = "valid"
    INVALID = "invalid"
    AMBIGUOUS = "ambiguous"
    UNVERIFIED = "unverified"


@dataclass
class ExtractedCitation:
    """Extracted citation with metadata"""
    text: str  # Full citation text
    type: CitationType
    status: CitationStatus
    span: Tuple[int, int]  # Character span in source text

    # Case citation fields
    case_name: Optional[str] = None
    reporter: Optional[str] = None
    volume: Optional[int] = None
    page: Optional[int] = None
    year: Optional[int] = None
    court: Optional[str] = None

    # Statute citation fields
    title: Optional[str] = None
    section: Optional[str] = None
    jurisdiction: Optional[str] = None

    # Validation
    confidence: float = 0.0  # 0.0 - 1.0
    normalized: Optional[str] = None  # Normalized citation format
    bluebook: Optional[str] = None  # Bluebook format

    # Enrichment
    url: Optional[str] = None
    full_case_name: Optional[str] = None
    synopsis: Optional[str] = None


# =============================================================================
# CITATION EXTRACTION
# =============================================================================

class CitationExtractor:
    """
    Extract legal citations from text.

    Uses regular expressions and the Eyecite library for robust citation detection.
    """

    # Common reporter abbreviations
    REPORTERS = [
        "U.S.", "S.Ct.", "L.Ed.", "F.", "F.2d", "F.3d", "F.Supp.", "F.Supp.2d", "F.Supp.3d",
        "Fed.Appx.", "A.", "A.2d", "A.3d", "P.", "P.2d", "P.3d", "N.E.", "N.E.2d", "N.E.3d",
        "N.W.", "N.W.2d", "S.E.", "S.E.2d", "S.W.", "S.W.2d", "S.W.3d", "So.", "So.2d", "So.3d",
        "Cal.Rptr.", "Cal.Rptr.2d", "Cal.Rptr.3d", "N.Y.S.", "N.Y.S.2d", "N.Y.S.3d"
    ]

    # Citation patterns
    CASE_PATTERN = re.compile(
        r'\b(\d+)\s+('  # Volume
        r'U\.S\.|S\.Ct\.|L\.Ed\.|'  # Supreme Court reporters
        r'F\.|F\.2d|F\.3d|F\.Supp\.|F\.Supp\.2d|F\.Supp\.3d|Fed\.Appx\.|'  # Federal reporters
        r'A\.|A\.2d|A\.3d|P\.|P\.2d|P\.3d|'  # Regional reporters
        r'N\.E\.|N\.E\.2d|N\.E\.3d|N\.W\.|N\.W\.2d|'
        r'S\.E\.|S\.E\.2d|S\.W\.|S\.W\.2d|S\.W\.3d|'
        r'So\.|So\.2d|So\.3d|'
        r'Cal\.Rptr\.|Cal\.Rptr\.2d|Cal\.Rptr\.3d|'
        r'N\.Y\.S\.|N\.Y\.S\.2d|N\.Y\.S\.3d'
        r')\s+(\d+)',  # Page
        re.IGNORECASE
    )

    STATUTE_PATTERN = re.compile(
        r'\b(\d+)\s+(U\.S\.C\.|U\.S\.C\.A\.|Stat\.)(?:\s+§?\s*(\d+(?:\([a-z0-9]+\))?(?:-\d+)?))?',
        re.IGNORECASE
    )

    USC_PATTERN = re.compile(
        r'\b(\d+)\s+U\.S\.C\.\s+§?\s*(\d+(?:\([a-z0-9]+\))?)',
        re.IGNORECASE
    )

    CFR_PATTERN = re.compile(
        r'\b(\d+)\s+C\.F\.R\.\s+§?\s*(\d+(?:\.\d+)*)',
        re.IGNORECASE
    )

    def __init__(self):
        """Initialize citation extractor"""
        # Try to import eyecite for enhanced citation parsing
        try:
            import eyecite
            self.eyecite_available = True
            logger.info("Eyecite library available for enhanced citation parsing")
        except ImportError:
            self.eyecite_available = False
            logger.warning("Eyecite library not available - using regex-based extraction")

    def extract_citations(self, text: str) -> List[ExtractedCitation]:
        """
        Extract all citations from text.

        Args:
            text: Text to extract citations from

        Returns:
            List of extracted citations
        """
        citations = []

        # Try Eyecite first if available
        if self.eyecite_available:
            try:
                citations.extend(self._extract_with_eyecite(text))
            except Exception as e:
                logger.error(f"Error using Eyecite: {e}")

        # Fall back to regex-based extraction
        if not citations:
            citations.extend(self._extract_with_regex(text))

        # Remove duplicates
        citations = self._deduplicate_citations(citations)

        return citations

    def _extract_with_eyecite(self, text: str) -> List[ExtractedCitation]:
        """
        Extract citations using Eyecite library.

        Args:
            text: Text to parse

        Returns:
            List of extracted citations
        """
        import eyecite

        citations = []

        try:
            # Parse citations with Eyecite
            found_cites = eyecite.get_citations(text)

            for cite in found_cites:
                # Determine citation type
                cite_type = CitationType.CASE
                if hasattr(cite, 'groups') and 'statute' in str(cite.groups).lower():
                    cite_type = CitationType.STATUTE

                # Extract metadata
                extracted = ExtractedCitation(
                    text=cite.matched_text() if hasattr(cite, 'matched_text') else str(cite),
                    type=cite_type,
                    status=CitationStatus.VALID,
                    span=cite.span(),
                    confidence=0.9  # High confidence for Eyecite results
                )

                # Extract case citation fields
                if cite_type == CitationType.CASE:
                    if hasattr(cite, 'groups'):
                        groups = cite.groups
                        extracted.volume = groups.get('volume')
                        extracted.reporter = groups.get('reporter')
                        extracted.page = groups.get('page')

                # Add normalized form
                if hasattr(cite, 'corrected_citation'):
                    extracted.normalized = cite.corrected_citation()

                citations.append(extracted)

        except Exception as e:
            logger.error(f"Eyecite parsing error: {e}")

        return citations

    def _extract_with_regex(self, text: str) -> List[ExtractedCitation]:
        """
        Extract citations using regular expressions.

        Args:
            text: Text to parse

        Returns:
            List of extracted citations
        """
        citations = []

        # Extract case citations
        for match in self.CASE_PATTERN.finditer(text):
            citations.append(ExtractedCitation(
                text=match.group(0),
                type=CitationType.CASE,
                status=CitationStatus.UNVERIFIED,
                span=match.span(),
                volume=int(match.group(1)),
                reporter=match.group(2),
                page=int(match.group(3)),
                confidence=0.7  # Medium confidence for regex
            ))

        # Extract USC citations
        for match in self.USC_PATTERN.finditer(text):
            citations.append(ExtractedCitation(
                text=match.group(0),
                type=CitationType.STATUTE,
                status=CitationStatus.UNVERIFIED,
                span=match.span(),
                title=match.group(1),
                section=match.group(2),
                jurisdiction="federal",
                confidence=0.8
            ))

        # Extract CFR citations (regulations)
        for match in self.CFR_PATTERN.finditer(text):
            citations.append(ExtractedCitation(
                text=match.group(0),
                type=CitationType.REGULATION,
                status=CitationStatus.UNVERIFIED,
                span=match.span(),
                title=match.group(1),
                section=match.group(2),
                jurisdiction="federal",
                confidence=0.8
            ))

        return citations

    def _deduplicate_citations(self, citations: List[ExtractedCitation]) -> List[ExtractedCitation]:
        """
        Remove duplicate citations.

        Args:
            citations: List of citations

        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []

        for cite in citations:
            # Create unique key based on citation text and span
            key = (cite.text.strip(), cite.span)
            if key not in seen:
                seen.add(key)
                unique.append(cite)

        return unique

    def extract_case_citations(self, text: str) -> List[ExtractedCitation]:
        """Extract only case law citations"""
        all_citations = self.extract_citations(text)
        return [c for c in all_citations if c.type == CitationType.CASE]

    def extract_statute_citations(self, text: str) -> List[ExtractedCitation]:
        """Extract only statutory citations"""
        all_citations = self.extract_citations(text)
        return [c for c in all_citations if c.type == CitationType.STATUTE]


# =============================================================================
# CITATION VALIDATION
# =============================================================================

class CitationValidator:
    """
    Validate and verify legal citations.
    """

    def __init__(self, research_service=None):
        """
        Initialize citation validator.

        Args:
            research_service: LegalResearchService for citation verification
        """
        self.research_service = research_service

    async def validate_citation(self, citation: ExtractedCitation) -> ExtractedCitation:
        """
        Validate a single citation.

        Args:
            citation: Citation to validate

        Returns:
            Citation with updated validation status
        """
        # Basic format validation
        if not self._is_valid_format(citation):
            citation.status = CitationStatus.INVALID
            citation.confidence = 0.1
            return citation

        # Verify against legal database if available
        if self.research_service and citation.type == CitationType.CASE:
            is_valid = await self._verify_case_citation(citation)
            citation.status = CitationStatus.VALID if is_valid else CitationStatus.INVALID
            citation.confidence = 0.95 if is_valid else 0.3
        else:
            # Mark as unverified if we can't check database
            citation.status = CitationStatus.UNVERIFIED

        return citation

    def _is_valid_format(self, citation: ExtractedCitation) -> bool:
        """Check if citation has valid format"""
        if citation.type == CitationType.CASE:
            return (
                citation.volume is not None and
                citation.reporter is not None and
                citation.page is not None
            )
        elif citation.type == CitationType.STATUTE:
            return (
                citation.title is not None and
                citation.section is not None
            )
        return True

    async def _verify_case_citation(self, citation: ExtractedCitation) -> bool:
        """
        Verify case citation against legal database.

        Args:
            citation: Case citation to verify

        Returns:
            True if citation is valid
        """
        if not self.research_service:
            return False

        try:
            # Search for case by citation
            from .legal_research import ResearchQuery

            query = ResearchQuery(
                query=citation.text,
                citation=citation.text,
                limit=1
            )

            results = await self.research_service.search_cases(query)

            # Citation is valid if we found matching cases
            if results:
                # Enrich citation with additional data
                result = results[0]
                citation.full_case_name = result.case_name
                citation.court = result.court
                citation.url = result.url
                return True

            return False

        except Exception as e:
            logger.error(f"Error verifying citation: {e}")
            return False

    async def validate_all(self, citations: List[ExtractedCitation]) -> List[ExtractedCitation]:
        """
        Validate multiple citations.

        Args:
            citations: List of citations to validate

        Returns:
            List of validated citations
        """
        validated = []
        for citation in citations:
            validated_cite = await self.validate_citation(citation)
            validated.append(validated_cite)

        return validated


# =============================================================================
# CITATION FORMATTER
# =============================================================================

class CitationFormatter:
    """
    Format citations in various styles (Bluebook, etc.)
    """

    @staticmethod
    def to_bluebook(citation: ExtractedCitation) -> str:
        """
        Format citation in Bluebook style.

        Args:
            citation: Citation to format

        Returns:
            Bluebook-formatted citation
        """
        if citation.type == CitationType.CASE:
            parts = []

            if citation.case_name:
                parts.append(citation.case_name)

            # Volume Reporter Page
            if citation.volume and citation.reporter and citation.page:
                parts.append(f"{citation.volume} {citation.reporter} {citation.page}")

            # Court and Year
            court_year = []
            if citation.court:
                court_year.append(citation.court)
            if citation.year:
                court_year.append(str(citation.year))

            if court_year:
                parts.append(f"({', '.join(court_year)})")

            return ", ".join(parts)

        elif citation.type == CitationType.STATUTE:
            if citation.title and citation.section:
                return f"{citation.title} U.S.C. § {citation.section}"

        return citation.text

    @staticmethod
    def to_short_form(citation: ExtractedCitation, case_name_short: Optional[str] = None) -> str:
        """
        Create short form citation for subsequent references.

        Args:
            citation: Full citation
            case_name_short: Short case name (optional)

        Returns:
            Short form citation
        """
        if citation.type == CitationType.CASE:
            if case_name_short:
                return f"{case_name_short}, {citation.volume} {citation.reporter} at {citation.page}"
            elif citation.case_name:
                # Use first party name
                first_party = citation.case_name.split(' v. ')[0] if ' v. ' in citation.case_name else citation.case_name
                return f"{first_party}, {citation.volume} {citation.reporter} at {citation.page}"

        return citation.text


# =============================================================================
# UNIFIED CITATION PROCESSOR
# =============================================================================

class CitationProcessor:
    """
    Unified citation processing service.

    Combines extraction, validation, and formatting.
    """

    def __init__(self, research_service=None):
        """
        Initialize citation processor.

        Args:
            research_service: LegalResearchService for validation
        """
        self.extractor = CitationExtractor()
        self.validator = CitationValidator(research_service)
        self.formatter = CitationFormatter()

    async def process_document(self, text: str, validate: bool = True) -> List[ExtractedCitation]:
        """
        Process document to extract and validate citations.

        Args:
            text: Document text
            validate: Whether to validate citations

        Returns:
            List of processed citations
        """
        # Extract citations
        citations = self.extractor.extract_citations(text)

        # Validate if requested
        if validate:
            citations = await self.validator.validate_all(citations)

        # Format citations
        for citation in citations:
            citation.bluebook = self.formatter.to_bluebook(citation)

        return citations

    def get_citation_summary(self, citations: List[ExtractedCitation]) -> Dict[str, Any]:
        """
        Get summary statistics for citations.

        Args:
            citations: List of citations

        Returns:
            Citation statistics
        """
        total = len(citations)
        by_type = {}
        by_status = {}

        for cite in citations:
            # Count by type
            cite_type = cite.type.value
            by_type[cite_type] = by_type.get(cite_type, 0) + 1

            # Count by status
            cite_status = cite.status.value
            by_status[cite_status] = by_status.get(cite_status, 0) + 1

        return {
            "total_citations": total,
            "by_type": by_type,
            "by_status": by_status,
            "validation_rate": by_status.get("valid", 0) / total if total > 0 else 0
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    'CitationType',
    'CitationStatus',

    # Models
    'ExtractedCitation',

    # Services
    'CitationExtractor',
    'CitationValidator',
    'CitationFormatter',
    'CitationProcessor',
]
