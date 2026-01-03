"""
Citation validation engine for legal documents.
Validates citation formats, checks citation accuracy, and provides citation normalization.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import json

from ..types.unified_types import UnifiedDocument, ContentType


class CitationFormat(Enum):
    """Standard legal citation formats."""
    BLUEBOOK = "bluebook"
    ALWD = "alwd"
    CHICAGO = "chicago"
    MLA = "mla"
    APA = "apa"
    UNKNOWN = "unknown"


class CitationType(Enum):
    """Types of legal citations."""
    CASE = "case"
    STATUTE = "statute"
    REGULATION = "regulation"
    CONSTITUTION = "constitution"
    LAW_REVIEW = "law_review"
    BOOK = "book"
    JOURNAL = "journal"
    NEWSPAPER = "newspaper"
    WEB = "web"
    SECONDARY = "secondary"


class ValidationSeverity(Enum):
    """Severity levels for citation validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


@dataclass
class CitationComponents:
    """Components of a parsed citation."""
    full_citation: str
    case_name: Optional[str] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page: Optional[str] = None
    year: Optional[int] = None
    court: Optional[str] = None
    jurisdiction: Optional[str] = None
    parallel_citations: List[str] = field(default_factory=list)
    pinpoint: Optional[str] = None
    
    # Statute/Code specific
    title: Optional[str] = None
    section: Optional[str] = None
    code_name: Optional[str] = None
    
    # Law review specific
    author: Optional[str] = None
    article_title: Optional[str] = None
    journal_name: Optional[str] = None
    journal_volume: Optional[str] = None
    start_page: Optional[str] = None


@dataclass
class ValidationIssue:
    """A citation validation issue."""
    severity: ValidationSeverity
    message: str
    suggestion: Optional[str] = None
    rule_violated: Optional[str] = None
    position: Optional[Tuple[int, int]] = None  # Start, end positions in text


@dataclass
class CitationValidationResult:
    """Result of citation validation."""
    citation: str
    is_valid: bool
    format_detected: CitationFormat
    citation_type: CitationType
    components: CitationComponents
    issues: List[ValidationIssue]
    normalized_citation: Optional[str] = None
    confidence: float = 0.0


class CitationValidator:
    """
    Comprehensive citation validation system for legal documents.
    
    Validates citation formats, checks accuracy, and provides suggestions
    for proper citation formatting according to various style guides.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.citation_patterns = self._initialize_citation_patterns()
        self.reporter_abbreviations = self._load_reporter_abbreviations()
        self.court_abbreviations = self._load_court_abbreviations()
        self.jurisdiction_codes = self._load_jurisdiction_codes()
    
    def _initialize_citation_patterns(self) -> Dict[CitationType, List[str]]:
        """Initialize regex patterns for different citation types."""
        patterns = {
            CitationType.CASE: [
                # Basic case citation: [Case Name], [Volume] [Reporter] [Page] ([Court] [Year])
                r'([A-Z][^,]+),\s*(\d+)\s+([A-Za-z\.]+)\s+(\d+)\s*\(([^)]+)\s+(\d{4})\)',
                # With pinpoint: [Case Name], [Volume] [Reporter] [Page], [Pinpoint] ([Court] [Year])
                r'([A-Z][^,]+),\s*(\d+)\s+([A-Za-z\.]+)\s+(\d+),\s*(\d+)\s*\(([^)]+)\s+(\d{4})\)',
                # Short form: [Case Name], [Volume] [Reporter] at [Page]
                r'([A-Z][^,]+),\s*(\d+)\s+([A-Za-z\.]+)\s+at\s+(\d+)',
            ],
            CitationType.STATUTE: [
                # Federal statute: [Title] U.S.C. § [Section] ([Year])
                r'(\d+)\s+U\.S\.C\.\s+§\s*([0-9a-zA-Z\-]+)\s*(?:\((\d{4})\))?',
                # State statute: [State] [Code] § [Section]
                r'([A-Z][a-z\.]+)\s+([A-Za-z\.]+)\s+§\s*([0-9a-zA-Z\-\.]+)',
                # Code of Federal Regulations: [Title] C.F.R. § [Section]
                r'(\d+)\s+C\.F\.R\.\s+§\s*([0-9a-zA-Z\-\.]+)',
            ],
            CitationType.LAW_REVIEW: [
                # Author, Title, Volume Journal Page (Year)
                r'([^,]+),\s*([^,]+),\s*(\d+)\s+([^0-9]+)\s+(\d+)\s*\((\d{4})\)',
                # Author, Title, Volume Journal Page, Pinpoint (Year)
                r'([^,]+),\s*([^,]+),\s*(\d+)\s+([^0-9]+)\s+(\d+),\s*(\d+)\s*\((\d{4})\)',
            ],
            CitationType.CONSTITUTION: [
                # U.S. Const. amend. [Amendment], § [Section]
                r'U\.S\.\s+Const\.\s+amend\.\s+([IVXLC]+),?\s*§?\s*([0-9]+)?',
                # U.S. Const. art. [Article], § [Section]
                r'U\.S\.\s+Const\.\s+art\.\s+([IVXLC]+),?\s*§?\s*([0-9]+)?',
                # State constitution: [State] Const. art. [Article], § [Section]
                r'([A-Z][a-z\.]+)\s+Const\.\s+art\.\s+([IVXLC0-9]+),?\s*§?\s*([0-9]+)?',
            ]
        }
        return patterns
    
    def _load_reporter_abbreviations(self) -> Dict[str, Dict[str, Any]]:
        """Load standard reporter abbreviations and metadata."""
        return {
            "U.S.": {"full_name": "United States Reports", "court": "Supreme Court", "jurisdiction": "Federal"},
            "S. Ct.": {"full_name": "Supreme Court Reporter", "court": "Supreme Court", "jurisdiction": "Federal"},
            "L. Ed.": {"full_name": "United States Supreme Court Reports, Lawyers' Edition", "court": "Supreme Court", "jurisdiction": "Federal"},
            "F.4th": {"full_name": "Federal Reporter, Fourth Series", "court": "Courts of Appeals", "jurisdiction": "Federal"},
            "F.3d": {"full_name": "Federal Reporter, Third Series", "court": "Courts of Appeals", "jurisdiction": "Federal"},
            "F.2d": {"full_name": "Federal Reporter, Second Series", "court": "Courts of Appeals", "jurisdiction": "Federal"},
            "F.": {"full_name": "Federal Reporter", "court": "Courts of Appeals", "jurisdiction": "Federal"},
            "F. Supp. 3d": {"full_name": "Federal Supplement, Third Series", "court": "District Courts", "jurisdiction": "Federal"},
            "F. Supp. 2d": {"full_name": "Federal Supplement, Second Series", "court": "District Courts", "jurisdiction": "Federal"},
            "F. Supp.": {"full_name": "Federal Supplement", "court": "District Courts", "jurisdiction": "Federal"},
            "P.3d": {"full_name": "Pacific Reporter, Third Series", "court": "State Courts", "jurisdiction": "State"},
            "P.2d": {"full_name": "Pacific Reporter, Second Series", "court": "State Courts", "jurisdiction": "State"},
            "P.": {"full_name": "Pacific Reporter", "court": "State Courts", "jurisdiction": "State"},
            "N.E.3d": {"full_name": "North Eastern Reporter, Third Series", "court": "State Courts", "jurisdiction": "State"},
            "N.E.2d": {"full_name": "North Eastern Reporter, Second Series", "court": "State Courts", "jurisdiction": "State"},
            "N.E.": {"full_name": "North Eastern Reporter", "court": "State Courts", "jurisdiction": "State"},
            "S.E.2d": {"full_name": "South Eastern Reporter, Second Series", "court": "State Courts", "jurisdiction": "State"},
            "S.E.": {"full_name": "South Eastern Reporter", "court": "State Courts", "jurisdiction": "State"},
            "So. 3d": {"full_name": "Southern Reporter, Third Series", "court": "State Courts", "jurisdiction": "State"},
            "So. 2d": {"full_name": "Southern Reporter, Second Series", "court": "State Courts", "jurisdiction": "State"},
            "So.": {"full_name": "Southern Reporter", "court": "State Courts", "jurisdiction": "State"},
        }
    
    def _load_court_abbreviations(self) -> Dict[str, str]:
        """Load standard court abbreviations."""
        return {
            "U.S.": "United States Supreme Court",
            "1st Cir.": "United States Court of Appeals for the First Circuit",
            "2d Cir.": "United States Court of Appeals for the Second Circuit",
            "3d Cir.": "United States Court of Appeals for the Third Circuit",
            "4th Cir.": "United States Court of Appeals for the Fourth Circuit",
            "5th Cir.": "United States Court of Appeals for the Fifth Circuit",
            "6th Cir.": "United States Court of Appeals for the Sixth Circuit",
            "7th Cir.": "United States Court of Appeals for the Seventh Circuit",
            "8th Cir.": "United States Court of Appeals for the Eighth Circuit",
            "9th Cir.": "United States Court of Appeals for the Ninth Circuit",
            "10th Cir.": "United States Court of Appeals for the Tenth Circuit",
            "11th Cir.": "United States Court of Appeals for the Eleventh Circuit",
            "D.C. Cir.": "United States Court of Appeals for the D.C. Circuit",
            "Fed. Cir.": "United States Court of Appeals for the Federal Circuit",
            "D. Del.": "United States District Court for the District of Delaware",
            "S.D.N.Y.": "United States District Court for the Southern District of New York",
            "E.D. Pa.": "United States District Court for the Eastern District of Pennsylvania",
            "N.D. Cal.": "United States District Court for the Northern District of California",
        }
    
    def _load_jurisdiction_codes(self) -> Dict[str, str]:
        """Load jurisdiction codes and full names."""
        return {
            "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
            "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
            "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
            "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
            "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
            "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
            "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
            "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
            "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
            "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
            "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
            "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
            "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia"
        }
    
    async def validate_citation(self, citation: str, format_preference: CitationFormat = CitationFormat.BLUEBOOK) -> CitationValidationResult:
        """
        Validate a single citation.
        
        Args:
            citation: The citation text to validate
            format_preference: Preferred citation format
            
        Returns:
            CitationValidationResult with validation details
        """
        citation = citation.strip()
        
        # Detect citation type and parse components
        citation_type = await self._detect_citation_type(citation)
        components = await self._parse_citation_components(citation, citation_type)
        format_detected = await self._detect_citation_format(citation, citation_type)
        
        # Validate against rules
        issues = await self._validate_citation_rules(citation, citation_type, components, format_preference)
        
        # Generate normalized citation
        normalized_citation = await self._normalize_citation(components, citation_type, format_preference)
        
        # Calculate confidence score
        confidence = await self._calculate_validation_confidence(citation, components, issues)
        
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return CitationValidationResult(
            citation=citation,
            is_valid=is_valid,
            format_detected=format_detected,
            citation_type=citation_type,
            components=components,
            issues=issues,
            normalized_citation=normalized_citation,
            confidence=confidence
        )
    
    async def validate_document_citations(self, document: UnifiedDocument) -> List[CitationValidationResult]:
        """Validate all citations in a document."""
        if not document.content:
            return []
        
        # Extract citations from document
        citations = await self._extract_citations_from_text(document.content)
        
        # Validate each citation
        results = []
        for citation in citations:
            try:
                result = await self.validate_citation(citation)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to validate citation '{citation}': {e}")
                # Add error result
                results.append(CitationValidationResult(
                    citation=citation,
                    is_valid=False,
                    format_detected=CitationFormat.UNKNOWN,
                    citation_type=CitationType.CASE,
                    components=CitationComponents(full_citation=citation),
                    issues=[ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Citation validation failed: {str(e)}"
                    )]
                ))
        
        return results
    
    async def _detect_citation_type(self, citation: str) -> CitationType:
        """Detect the type of citation."""
        citation_lower = citation.lower()
        
        # Constitutional citations
        if 'const.' in citation_lower or 'constitution' in citation_lower:
            return CitationType.CONSTITUTION
        
        # Statute citations
        if 'u.s.c.' in citation_lower or 'c.f.r.' in citation_lower or '§' in citation:
            return CitationType.STATUTE
        
        # Law review citations (look for author patterns)
        if re.search(r'^[A-Z][a-z]+(?:\s+[A-Z]\.)?\s+[A-Z][a-z]+,', citation):
            return CitationType.LAW_REVIEW
        
        # Case citations (most common fallback)
        return CitationType.CASE
    
    async def _parse_citation_components(self, citation: str, citation_type: CitationType) -> CitationComponents:
        """Parse citation into its components."""
        components = CitationComponents(full_citation=citation)
        
        patterns = self.citation_patterns.get(citation_type, [])
        
        for pattern in patterns:
            match = re.search(pattern, citation, re.IGNORECASE)
            if match:
                if citation_type == CitationType.CASE:
                    groups = match.groups()
                    if len(groups) >= 4:
                        components.case_name = groups[0].strip()
                        components.volume = groups[1]
                        components.reporter = groups[2]
                        components.page = groups[3]
                        if len(groups) >= 6:
                            components.court = groups[-2].strip()
                            components.year = int(groups[-1])
                        if len(groups) >= 7:  # Has pinpoint
                            components.pinpoint = groups[4]
                
                elif citation_type == CitationType.STATUTE:
                    groups = match.groups()
                    if 'U.S.C.' in citation:
                        components.title = groups[0]
                        components.section = groups[1]
                        if len(groups) > 2 and groups[2]:
                            components.year = int(groups[2])
                        components.code_name = "United States Code"
                    elif 'C.F.R.' in citation:
                        components.title = groups[0]
                        components.section = groups[1]
                        components.code_name = "Code of Federal Regulations"
                
                elif citation_type == CitationType.LAW_REVIEW:
                    groups = match.groups()
                    if len(groups) >= 6:
                        components.author = groups[0].strip()
                        components.article_title = groups[1].strip()
                        components.journal_volume = groups[2]
                        components.journal_name = groups[3].strip()
                        components.start_page = groups[4]
                        components.year = int(groups[5])
                        if len(groups) > 6:  # Has pinpoint
                            components.pinpoint = groups[5]
                            components.year = int(groups[6])
                
                break
        
        return components
    
    async def _detect_citation_format(self, citation: str, citation_type: CitationType) -> CitationFormat:
        """Detect the citation format used."""
        # This is a simplified detection - in practice would be more sophisticated
        
        # Look for Bluebook indicators
        if re.search(r'\b\d+\s+[A-Z][a-z\.]+\s+\d+\b', citation):  # Volume Reporter Page
            return CitationFormat.BLUEBOOK
        
        # Look for ALWD indicators (similar to Bluebook but with some differences)
        if re.search(r'\([A-Za-z\s\.]+\s+\d{4}\)', citation):  # (Court Year)
            return CitationFormat.ALWD
        
        return CitationFormat.UNKNOWN
    
    async def _validate_citation_rules(self, 
                                     citation: str, 
                                     citation_type: CitationType,
                                     components: CitationComponents,
                                     format_preference: CitationFormat) -> List[ValidationIssue]:
        """Validate citation against format rules."""
        issues = []
        
        # Basic format validation
        if citation_type == CitationType.CASE:
            issues.extend(await self._validate_case_citation(citation, components, format_preference))
        elif citation_type == CitationType.STATUTE:
            issues.extend(await self._validate_statute_citation(citation, components, format_preference))
        elif citation_type == CitationType.LAW_REVIEW:
            issues.extend(await self._validate_law_review_citation(citation, components, format_preference))
        
        # Common validation rules
        issues.extend(await self._validate_common_rules(citation))
        
        return issues
    
    async def _validate_case_citation(self, 
                                    citation: str, 
                                    components: CitationComponents,
                                    format_preference: CitationFormat) -> List[ValidationIssue]:
        """Validate case citation specific rules."""
        issues = []
        
        # Check required components
        if not components.case_name:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Missing case name",
                rule_violated="Case citations must include case name"
            ))
        
        if not components.volume or not components.reporter or not components.page:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Missing volume, reporter, or page number",
                rule_violated="Case citations must include volume, reporter, and page"
            ))
        
        # Validate reporter abbreviation
        if components.reporter and components.reporter not in self.reporter_abbreviations:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"Unknown reporter abbreviation: {components.reporter}",
                suggestion="Check reporter abbreviation against standard references"
            ))
        
        # Check case name formatting
        if components.case_name:
            if not components.case_name[0].isupper():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="Case name should start with capital letter",
                    rule_violated="Proper case formatting required"
                ))
            
            if components.case_name.endswith('.'):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="Case name should not end with period",
                    suggestion="Remove trailing period from case name"
                ))
        
        # Validate parenthetical information
        if components.court and components.year:
            if format_preference == CitationFormat.BLUEBOOK:
                if not re.search(r'\([^)]+\s+\d{4}\)', citation):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message="Court and year should be in parentheses",
                        rule_violated="Bluebook Rule 10.4"
                    ))
        
        return issues
    
    async def _validate_statute_citation(self, 
                                       citation: str, 
                                       components: CitationComponents,
                                       format_preference: CitationFormat) -> List[ValidationIssue]:
        """Validate statute citation specific rules."""
        issues = []
        
        # Check required components
        if not components.title or not components.section:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Missing title or section number",
                rule_violated="Statute citations must include title and section"
            ))
        
        # Validate section symbol
        if '§' not in citation and 'section' not in citation.lower():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Missing section symbol (§) or 'section'",
                suggestion="Use § symbol or spell out 'section'"
            ))
        
        # Check spacing around section symbol
        if '§' in citation and not re.search(r'\s§\s', citation):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Section symbol should have spaces before and after",
                rule_violated="Standard formatting convention"
            ))
        
        return issues
    
    async def _validate_law_review_citation(self, 
                                          citation: str, 
                                          components: CitationComponents,
                                          format_preference: CitationFormat) -> List[ValidationIssue]:
        """Validate law review citation specific rules."""
        issues = []
        
        # Check required components
        required_fields = ['author', 'article_title', 'journal_volume', 'journal_name', 'start_page', 'year']
        missing_fields = [field for field in required_fields if not getattr(components, field)]
        
        if missing_fields:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Missing required fields: {', '.join(missing_fields)}",
                rule_violated="Law review citations must include author, title, volume, journal, page, and year"
            ))
        
        # Check author format
        if components.author:
            if not re.search(r'^[A-Z][a-z]+', components.author):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="Author name should start with capital letter",
                    rule_violated="Proper name formatting required"
                ))
        
        # Check article title formatting
        if components.article_title:
            if format_preference == CitationFormat.BLUEBOOK:
                if not (components.article_title.startswith('"') and components.article_title.endswith('"')):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        message="Article titles should be in quotation marks",
                        rule_violated="Bluebook Rule 16.4",
                        suggestion=f'"{components.article_title}"'
                    ))
        
        return issues
    
    async def _validate_common_rules(self, citation: str) -> List[ValidationIssue]:
        """Validate common citation rules."""
        issues = []
        
        # Check for double spaces
        if '  ' in citation:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Multiple consecutive spaces found",
                suggestion="Use single spaces between elements"
            ))
        
        # Check for trailing/leading whitespace
        if citation != citation.strip():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Extra whitespace at beginning or end",
                suggestion="Remove leading and trailing spaces"
            ))
        
        # Check for missing periods in abbreviations
        abbrev_pattern = r'\b[A-Z]{2,}(?![a-z])'
        matches = re.finditer(abbrev_pattern, citation)
        for match in matches:
            abbrev = match.group()
            if not abbrev.endswith('.') and abbrev not in ['US', 'USC', 'CFR']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message=f"Abbreviation '{abbrev}' may need periods",
                    suggestion=f"Consider '{'.'.join(abbrev)}.'",
                    position=(match.start(), match.end())
                ))
        
        return issues
    
    async def _normalize_citation(self, 
                                components: CitationComponents, 
                                citation_type: CitationType,
                                target_format: CitationFormat) -> Optional[str]:
        """Generate normalized citation in target format."""
        try:
            if citation_type == CitationType.CASE and target_format == CitationFormat.BLUEBOOK:
                parts = []
                
                if components.case_name:
                    parts.append(components.case_name.rstrip(','))
                
                if components.volume and components.reporter and components.page:
                    parts.append(f"{components.volume} {components.reporter} {components.page}")
                    
                    if components.pinpoint:
                        parts[-1] += f", {components.pinpoint}"
                
                if components.court and components.year:
                    parts.append(f"({components.court} {components.year})")
                
                return ', '.join(parts) if len(parts) > 1 else parts[0] if parts else None
            
            elif citation_type == CitationType.STATUTE and target_format == CitationFormat.BLUEBOOK:
                if components.title and components.section:
                    if components.code_name == "United States Code":
                        base = f"{components.title} U.S.C. § {components.section}"
                        if components.year:
                            base += f" ({components.year})"
                        return base
                    elif components.code_name == "Code of Federal Regulations":
                        return f"{components.title} C.F.R. § {components.section}"
            
            elif citation_type == CitationType.LAW_REVIEW and target_format == CitationFormat.BLUEBOOK:
                if all([components.author, components.article_title, components.journal_volume, 
                       components.journal_name, components.start_page, components.year]):
                    
                    title = components.article_title
                    if not (title.startswith('"') and title.endswith('"')):
                        title = f'"{title}"'
                    
                    base = f"{components.author}, {title}, {components.journal_volume} {components.journal_name} {components.start_page}"
                    
                    if components.pinpoint:
                        base += f", {components.pinpoint}"
                    
                    base += f" ({components.year})"
                    return base
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to normalize citation: {e}")
            return None
    
    async def _calculate_validation_confidence(self, 
                                             citation: str, 
                                             components: CitationComponents,
                                             issues: List[ValidationIssue]) -> float:
        """Calculate confidence score for validation."""
        base_score = 1.0
        
        # Reduce confidence based on issues
        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                base_score -= 0.3
            elif issue.severity == ValidationSeverity.WARNING:
                base_score -= 0.1
            elif issue.severity == ValidationSeverity.INFO:
                base_score -= 0.05
        
        # Boost confidence if components are well-parsed
        if components.case_name and components.volume and components.reporter and components.page:
            base_score += 0.1
        
        # Boost if reporter is recognized
        if components.reporter and components.reporter in self.reporter_abbreviations:
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score))
    
    async def _extract_citations_from_text(self, text: str) -> List[str]:
        """Extract citations from document text."""
        citations = []
        
        # Combined pattern for common citation formats
        citation_patterns = [
            # Case citations: Case Name, Volume Reporter Page (Court Year)
            r'[A-Z][^,\n]{10,},\s*\d+\s+[A-Za-z\.]+\s+\d+[^(]*\([^)]+\s+\d{4}\)',
            # Statute citations: Title U.S.C. § Section
            r'\d+\s+U\.S\.C\.\s+§\s*[0-9a-zA-Z\-]+(?:\([^)]+\))?',
            # CFR citations: Title C.F.R. § Section
            r'\d+\s+C\.F\.R\.\s+§\s*[0-9a-zA-Z\-\.]+',
            # Law review citations with author
            r'[A-Z][a-z]+(?:\s+[A-Z]\.)?\s+[A-Z][a-z]+,\s*[^,]+,\s*\d+\s+[^0-9\n]+\s+\d+[^(]*\(\d{4}\)',
        ]
        
        for pattern in citation_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                citation = match.group().strip()
                if len(citation) > 10:  # Filter out very short matches
                    citations.append(citation)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_citations = []
        for citation in citations:
            if citation not in seen:
                seen.add(citation)
                unique_citations.append(citation)
        
        return unique_citations
    
    async def suggest_citation_improvements(self, citation: str) -> List[str]:
        """Suggest improvements for a citation."""
        validation_result = await self.validate_citation(citation)
        suggestions = []
        
        # Add normalized citation if different
        if validation_result.normalized_citation and validation_result.normalized_citation != citation:
            suggestions.append(f"Normalized form: {validation_result.normalized_citation}")
        
        # Add suggestions from validation issues
        for issue in validation_result.issues:
            if issue.suggestion:
                suggestions.append(issue.suggestion)
        
        return suggestions
    
    async def get_citation_completeness_score(self, citation: str) -> Tuple[float, List[str]]:
        """Calculate completeness score and identify missing elements."""
        validation_result = await self.validate_citation(citation)
        components = validation_result.components
        
        required_elements = {
            CitationType.CASE: ['case_name', 'volume', 'reporter', 'page', 'court', 'year'],
            CitationType.STATUTE: ['title', 'section', 'code_name'],
            CitationType.LAW_REVIEW: ['author', 'article_title', 'journal_volume', 'journal_name', 'start_page', 'year'],
            CitationType.CONSTITUTION: ['jurisdiction', 'section']
        }
        
        citation_type = validation_result.citation_type
        required = required_elements.get(citation_type, [])
        
        present_elements = []
        missing_elements = []
        
        for element in required:
            if hasattr(components, element) and getattr(components, element):
                present_elements.append(element)
            else:
                missing_elements.append(element)
        
        completeness_score = len(present_elements) / len(required) if required else 1.0
        
        return completeness_score, missing_elements


# Helper functions
async def validate_citations_in_document(document: UnifiedDocument) -> List[CitationValidationResult]:
    """Helper function to validate all citations in a document."""
    validator = CitationValidator()
    return await validator.validate_document_citations(document)

async def normalize_citation_to_bluebook(citation: str) -> Optional[str]:
    """Helper function to normalize a citation to Bluebook format."""
    validator = CitationValidator()
    result = await validator.validate_citation(citation, CitationFormat.BLUEBOOK)
    return result.normalized_citation