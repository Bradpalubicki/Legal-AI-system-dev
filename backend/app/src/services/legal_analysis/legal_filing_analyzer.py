"""
Legal Filing Analyzer - Core Analysis Engine
Comprehensive legal document analysis using AI and rule-based extraction

This module provides:
- Document classification
- Structured data extraction
- Deadline calculation
- AI-powered analysis
- Summary generation
"""

import json
import re
import logging
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Optional, Dict, List, Any, Tuple, Union
from enum import Enum

# Local imports
from .filing_types import (
    get_filing_type,
    get_all_filing_types,
    classify_filing_by_patterns,
    FilingType,
    FILING_CATEGORIES
)
from .extraction_patterns import (
    extract_case_number,
    extract_all_citations,
    extract_monetary_amounts,
    extract_parties_from_caption,
    CaseNumberPattern as CaseNumber,
    CitationResult as LegalCitation,
    PartyExtractionResult as Party,
)

# Alias for backward compatibility
extract_parties = extract_parties_from_caption
from .deadline_rules import (
    DeadlineCalculator,
    JurisdictionType,
    ServiceMethod,
    DeadlineType,
    CalculatedDeadline,
    format_deadline_info,
    ResponseDeadlineCalculator
)
from .legal_prompts import (
    LegalPromptBuilder,
    PromptConfig,
    COMPREHENSIVE_ANALYSIS_PROMPT,
    OUTPUT_SCHEMA_INSTRUCTIONS
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES FOR ANALYSIS RESULTS
# =============================================================================

class ConfidenceLevel(Enum):
    """Confidence levels for analysis results"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class UrgencyLevel(Enum):
    """Urgency levels for filings"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ClassificationResult:
    """Result of document classification"""
    filing_type_code: str
    filing_type_name: str
    category: str
    category_name: str
    confidence: float
    confidence_level: ConfidenceLevel
    practice_areas: List[str]
    alternative_classifications: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """Result of data extraction"""
    case_numbers: List[Dict[str, Any]]
    parties: List[Dict[str, Any]]
    citations: Dict[str, List[Dict[str, Any]]]
    monetary_amounts: List[Dict[str, Any]]
    dates: List[Dict[str, Any]]
    attorneys: List[Dict[str, Any]]
    raw_text_snippets: Dict[str, str] = field(default_factory=dict)


@dataclass
class DeadlineResult:
    """Result of deadline analysis"""
    deadlines: List[Dict[str, Any]]
    jurisdiction: str
    service_method: str
    trigger_date: Optional[str]
    notes: List[str] = field(default_factory=list)


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    urgency_level: UrgencyLevel
    risk_factors: List[str]
    immediate_actions: List[str]
    recommendations: List[str]
    deadline_risks: List[str]
    financial_exposure: Optional[Dict[str, Any]]


@dataclass
class AnalysisSummary:
    """Summary of analysis"""
    executive_summary: str
    key_points: List[str]
    procedural_status: str
    main_relief_sought: str
    filing_date: Optional[str]


@dataclass
class FilingAnalysisResult:
    """Complete filing analysis result"""
    # Metadata
    analysis_id: str
    analyzed_at: str
    document_length: int
    processing_time_ms: int

    # Classification
    classification: ClassificationResult

    # Extracted data
    extraction: ExtractionResult

    # Deadlines
    deadlines: DeadlineResult

    # Risk assessment
    risk: RiskAssessment

    # Summary
    summary: AnalysisSummary

    # AI analysis (if performed)
    ai_analysis: Optional[Dict[str, Any]] = None

    # Raw AI response (for debugging)
    raw_ai_response: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert enums to values
        result['classification']['confidence_level'] = self.classification.confidence_level.value
        result['risk']['urgency_level'] = self.risk.urgency_level.value
        return result

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)


# =============================================================================
# MAIN ANALYZER CLASS
# =============================================================================

class LegalFilingAnalyzer:
    """
    Main analyzer class for legal court filings

    Provides comprehensive analysis including:
    - Document classification
    - Data extraction (case numbers, parties, citations, etc.)
    - Deadline calculation
    - Risk assessment
    - AI-powered analysis and summarization
    """

    def __init__(
        self,
        ai_service: Optional[Any] = None,
        default_jurisdiction: JurisdictionType = JurisdictionType.FEDERAL,
        enable_ai_analysis: bool = True
    ):
        """
        Initialize the analyzer

        Args:
            ai_service: AI service for enhanced analysis (Claude, OpenAI, etc.)
            default_jurisdiction: Default jurisdiction for deadline calculations
            enable_ai_analysis: Whether to perform AI-powered analysis
        """
        self.ai_service = ai_service
        self.default_jurisdiction = default_jurisdiction
        self.enable_ai_analysis = enable_ai_analysis
        self.deadline_calculator = DeadlineCalculator(default_jurisdiction)
        self.prompt_builder = LegalPromptBuilder()

    async def analyze(
        self,
        document_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> FilingAnalysisResult:
        """
        Perform comprehensive analysis of a legal filing

        Args:
            document_text: The text content of the filing
            metadata: Optional metadata (filing date, case number, etc.)
            options: Analysis options

        Returns:
            FilingAnalysisResult with complete analysis
        """
        import time
        import uuid

        start_time = time.time()
        analysis_id = str(uuid.uuid4())

        metadata = metadata or {}
        options = options or {}

        # Extract options
        jurisdiction = options.get('jurisdiction', self.default_jurisdiction)
        service_method = options.get('service_method', ServiceMethod.ELECTRONIC)
        filing_date = metadata.get('filing_date') or options.get('filing_date')
        include_ai = options.get('include_ai', self.enable_ai_analysis)

        # Ensure jurisdiction is enum type
        if isinstance(jurisdiction, str):
            jurisdiction = JurisdictionType(jurisdiction)

        # 1. Classification
        classification = self._classify_document(document_text)

        # 2. Data Extraction
        extraction = self._extract_data(document_text)

        # 3. Deadline Calculation
        deadlines = self._calculate_deadlines(
            document_text,
            classification,
            filing_date,
            jurisdiction,
            service_method
        )

        # 4. Risk Assessment
        risk = self._assess_risk(classification, extraction, deadlines)

        # 5. Generate Summary
        summary = self._generate_summary(
            document_text,
            classification,
            extraction,
            deadlines
        )

        # 6. AI Analysis (if enabled and service available)
        ai_analysis = None
        raw_ai_response = None

        if include_ai and self.ai_service:
            try:
                ai_analysis, raw_ai_response = await self._perform_ai_analysis(
                    document_text,
                    classification,
                    options
                )
            except Exception as e:
                logger.error(f"AI analysis failed: {e}")
                ai_analysis = {"error": str(e)}

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        return FilingAnalysisResult(
            analysis_id=analysis_id,
            analyzed_at=datetime.utcnow().isoformat(),
            document_length=len(document_text),
            processing_time_ms=processing_time_ms,
            classification=classification,
            extraction=extraction,
            deadlines=deadlines,
            risk=risk,
            summary=summary,
            ai_analysis=ai_analysis,
            raw_ai_response=raw_ai_response
        )

    def _classify_document(self, document_text: str) -> ClassificationResult:
        """Classify the document type using pattern matching"""
        # Get title/header from first few lines
        lines = document_text.strip().split('\n')
        title_text = '\n'.join(lines[:10])

        # Pattern-based classification
        matches = classify_filing_by_patterns(title_text)

        if matches:
            # Take best match
            best_match = matches[0]
            filing_type = get_filing_type(best_match['code'])

            if filing_type:
                confidence = best_match.get('confidence', 0.8)
                confidence_level = (
                    ConfidenceLevel.HIGH if confidence >= 0.85
                    else ConfidenceLevel.MEDIUM if confidence >= 0.6
                    else ConfidenceLevel.LOW
                )

                # Get category name
                category = filing_type.category
                category_name = FILING_CATEGORIES.get(category, "Unknown")

                return ClassificationResult(
                    filing_type_code=filing_type.code,
                    filing_type_name=filing_type.name,
                    category=category,
                    category_name=category_name,
                    confidence=confidence,
                    confidence_level=confidence_level,
                    practice_areas=list(filing_type.practice_areas),
                    alternative_classifications=[
                        {
                            'code': m['code'],
                            'name': m.get('name', ''),
                            'confidence': m.get('confidence', 0)
                        }
                        for m in matches[1:4]  # Top 3 alternatives
                    ]
                )

        # Default classification
        return ClassificationResult(
            filing_type_code="X99",
            filing_type_name="Unclassified Filing",
            category="X",
            category_name="Other/Miscellaneous",
            confidence=0.3,
            confidence_level=ConfidenceLevel.LOW,
            practice_areas=[],
            alternative_classifications=[]
        )

    def _extract_data(self, document_text: str) -> ExtractionResult:
        """Extract structured data from document"""
        # Extract case numbers
        case_numbers = []
        cn = extract_case_number(document_text)
        if cn:
            case_numbers.append({
                'full_number': cn.get('raw', ''),
                'court_type': cn.get('court_type', ''),
                'year': cn.get('year', ''),
                'case_type': cn.get('case_type', ''),
                'sequence': cn.get('sequence', ''),
                'district': cn.get('district', ''),
                'judge_initials': cn.get('judge_initials', '')
            })

        # Extract parties
        parties = []
        party_dict = extract_parties(document_text)
        # party_dict is {'plaintiffs': [...], 'defendants': [...]}
        for plaintiff in party_dict.get('plaintiffs', []):
            parties.append({
                'name': plaintiff,
                'role': 'plaintiff',
                'entity_type': '',
                'aliases': [],
                'state': ''
            })
        for defendant in party_dict.get('defendants', []):
            parties.append({
                'name': defendant,
                'role': 'defendant',
                'entity_type': '',
                'aliases': [],
                'state': ''
            })

        # Extract citations
        citations = extract_all_citations(document_text)
        citation_dict = {
            'case_law': [],
            'statutes': [],
            'rules': [],
            'regulations': []
        }

        for citation in citations:
            citation_data = {
                'citation': citation.raw_citation,
                'type': citation.citation_type,
                'short_name': '',
                'signal': '',
                'context': ''
            }

            if citation.citation_type == 'case':
                citation_data.update({
                    'volume': citation.volume,
                    'reporter': citation.reporter,
                    'page': citation.page,
                    'court': '',
                    'year': citation.year
                })
                citation_dict['case_law'].append(citation_data)
            elif citation.citation_type == 'statute':
                citation_data.update({
                    'title': citation.title,
                    'section': citation.section
                })
                citation_dict['statutes'].append(citation_data)
            elif citation.citation_type == 'rule':
                citation_dict['rules'].append(citation_data)
            else:
                citation_dict['regulations'].append(citation_data)

        # Extract monetary amounts
        amounts = []
        amount_list = extract_monetary_amounts(document_text)
        for amount in amount_list:
            amounts.append({
                'value': amount.get('amount', 0),
                'currency': amount.get('currency', 'USD'),
                'type': '',
                'qualifier': '',
                'context': amount.get('raw', '')
            })

        # Dates extraction - basic regex since extract_dates doesn't exist
        dates = []
        import re
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        for match in re.finditer(date_pattern, document_text):
            dates.append({
                'date': None,
                'original_text': match.group(0),
                'date_type': 'unknown',
                'context': ''
            })

        # Attorney extraction - basic regex since extract_attorney_info doesn't exist
        attorneys = []
        attorney_pattern = r'(?:Attorney|Counsel)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
        for match in re.finditer(attorney_pattern, document_text):
            attorneys.append({
                'name': match.group(1),
                'bar_number': '',
                'firm': '',
                'email': '',
                'phone': '',
                'address': '',
                'role': ''
            })

        return ExtractionResult(
            case_numbers=case_numbers,
            parties=parties,
            citations=citation_dict,
            monetary_amounts=amounts,
            dates=dates,
            attorneys=attorneys
        )

    def _calculate_deadlines(
        self,
        document_text: str,
        classification: ClassificationResult,
        filing_date: Optional[str],
        jurisdiction: JurisdictionType,
        service_method: ServiceMethod
    ) -> DeadlineResult:
        """Calculate relevant deadlines based on filing type"""
        deadlines = []
        notes = []

        # Parse filing date
        trigger_date = None
        if filing_date:
            try:
                if isinstance(filing_date, str):
                    trigger_date = datetime.fromisoformat(filing_date.replace('Z', '+00:00')).date()
                elif isinstance(filing_date, date):
                    trigger_date = filing_date
            except (ValueError, TypeError):
                notes.append(f"Could not parse filing date: {filing_date}")
        else:
            trigger_date = date.today()
            notes.append("Using today's date as trigger (no filing date provided)")

        # Get deadlines based on filing type
        filing_code = classification.filing_type_code

        # Map filing types to response deadline calculations
        if filing_code.startswith('A'):
            # Complaint - calculate answer deadline
            deadline = ResponseDeadlineCalculator.calculate_answer_deadline(
                trigger_date, jurisdiction, waiver=False, service_method=service_method
            )
            if deadline:
                deadlines.append({
                    'description': 'Answer/Responsive Pleading Due',
                    'date': deadline.adjusted_deadline.isoformat(),
                    'rule_basis': deadline.rule_applied,
                    'is_jurisdictional': False,
                    'calculated_from': 'Service date',
                    'notes': deadline.calculation_notes
                })

        elif filing_code.startswith('C'):
            # Motion to Dismiss - calculate opposition deadline
            calc = DeadlineCalculator(jurisdiction)
            # Opposition typically 14-21 days depending on jurisdiction
            opposition_days = 21 if jurisdiction == JurisdictionType.FEDERAL else 14
            deadline_date = calc.add_business_days(trigger_date, opposition_days)
            deadlines.append({
                'description': 'Opposition to Motion Due',
                'date': deadline_date.isoformat(),
                'rule_basis': 'Local Rule (varies by district)',
                'is_jurisdictional': False,
                'calculated_from': 'Filing date',
                'notes': ['Check local rules for exact deadline']
            })

        elif filing_code.startswith('D'):
            # Discovery motion - often has expedited timeline
            calc = DeadlineCalculator(jurisdiction)
            deadline_date = calc.add_business_days(trigger_date, 14)
            deadlines.append({
                'description': 'Response to Discovery Motion Due',
                'date': deadline_date.isoformat(),
                'rule_basis': 'Local Rule',
                'is_jurisdictional': False,
                'calculated_from': 'Filing date',
                'notes': []
            })

        elif filing_code.startswith('E'):
            # Summary Judgment - calculate opposition deadline
            calc = DeadlineCalculator(jurisdiction)
            deadline_date = calc.add_business_days(trigger_date, 21)
            deadlines.append({
                'description': 'Opposition to Summary Judgment Due',
                'date': deadline_date.isoformat(),
                'rule_basis': 'FRCP 56 / Local Rule',
                'is_jurisdictional': False,
                'calculated_from': 'Filing date',
                'notes': ['Check local rules - may require separate statement of disputed facts']
            })

        elif filing_code.startswith('L'):
            # Emergency motion - expedited response
            calc = DeadlineCalculator(jurisdiction)
            deadline_date = calc.add_business_days(trigger_date, 3)
            deadlines.append({
                'description': 'Response to Emergency Motion Due (EXPEDITED)',
                'date': deadline_date.isoformat(),
                'rule_basis': 'Local Rule / Court Order',
                'is_jurisdictional': False,
                'calculated_from': 'Filing date',
                'notes': ['Emergency timeline - check court order for specific deadline']
            })

        elif filing_code.startswith('O'):
            # Post-trial motion - strict deadlines
            calc = DeadlineCalculator(jurisdiction)
            # Most post-trial motions must be filed within 28 days
            deadline_date = calc.add_business_days(trigger_date, 14)
            deadlines.append({
                'description': 'Response to Post-Trial Motion Due',
                'date': deadline_date.isoformat(),
                'rule_basis': 'FRCP 59/60',
                'is_jurisdictional': False,
                'calculated_from': 'Filing date',
                'notes': ['Post-trial motion deadlines are strictly enforced']
            })

        elif filing_code.startswith('P'):
            # Appeal filing - JURISDICTIONAL deadlines
            if filing_code == 'P1':
                # Notice of appeal triggers response deadlines
                calc = DeadlineCalculator(jurisdiction)
                # Appellee has 14 days to cross-appeal
                deadline_date = calc.add_business_days(trigger_date, 14)
                deadlines.append({
                    'description': 'Cross-Appeal Due',
                    'date': deadline_date.isoformat(),
                    'rule_basis': 'FRAP 4(a)(3)',
                    'is_jurisdictional': True,
                    'calculated_from': 'Notice of Appeal filed',
                    'notes': ['JURISDICTIONAL - Cannot be extended']
                })

        return DeadlineResult(
            deadlines=deadlines,
            jurisdiction=jurisdiction.value,
            service_method=service_method.value,
            trigger_date=trigger_date.isoformat() if trigger_date else None,
            notes=notes
        )

    def _assess_risk(
        self,
        classification: ClassificationResult,
        extraction: ExtractionResult,
        deadlines: DeadlineResult
    ) -> RiskAssessment:
        """Assess risk level of the filing"""
        risk_factors = []
        immediate_actions = []
        recommendations = []
        deadline_risks = []

        # Assess based on filing type
        filing_code = classification.filing_type_code
        category = classification.category

        # Emergency filings are critical
        if category == 'L':
            urgency = UrgencyLevel.CRITICAL
            risk_factors.append("Emergency motion requires immediate attention")
            immediate_actions.append("Review filing immediately")
            immediate_actions.append("Prepare expedited response or contact opposing counsel")

        # Dispositive motions are high priority
        elif category == 'E':
            urgency = UrgencyLevel.HIGH
            risk_factors.append("Dispositive motion could end case")
            immediate_actions.append("Begin drafting opposition")
            recommendations.append("Consider requesting extension if needed")
            recommendations.append("Gather evidence for disputed facts")

        # Appeals are high priority with jurisdictional deadlines
        elif category == 'P':
            urgency = UrgencyLevel.HIGH
            risk_factors.append("Appeal deadline is jurisdictional")
            deadline_risks.append("Missing appeal deadline cannot be cured")
            immediate_actions.append("Verify deadline calculation")
            recommendations.append("Calendar all briefing deadlines")

        # Pre-answer motions
        elif category == 'C':
            urgency = UrgencyLevel.MEDIUM
            risk_factors.append("Motion could result in dismissal")
            recommendations.append("Evaluate whether to oppose or amend complaint")

        # New complaints
        elif category == 'A':
            urgency = UrgencyLevel.MEDIUM
            risk_factors.append("New case requires response strategy")
            immediate_actions.append("Review claims and assess defenses")
            recommendations.append("Consider waiver of service for extended response time")

        # Discovery matters
        elif category == 'D':
            urgency = UrgencyLevel.MEDIUM
            risk_factors.append("Discovery dispute could affect case timeline")
            recommendations.append("Review meet and confer requirements")

        # Default to low urgency for routine filings
        else:
            urgency = UrgencyLevel.LOW

        # Check for financial exposure
        financial_exposure = None
        if extraction.monetary_amounts:
            total = sum(
                a.get('value', 0) for a in extraction.monetary_amounts
                if a.get('value')
            )
            if total > 0:
                financial_exposure = {
                    'total_claimed': total,
                    'breakdown': extraction.monetary_amounts
                }
                if total > 1000000:
                    risk_factors.append(f"High financial exposure: ${total:,.2f}")
                    if urgency != UrgencyLevel.CRITICAL:
                        urgency = UrgencyLevel.HIGH

        # Check deadline risks
        for deadline in deadlines.deadlines:
            if deadline.get('is_jurisdictional'):
                deadline_risks.append(
                    f"JURISDICTIONAL: {deadline['description']} - {deadline['date']}"
                )

        return RiskAssessment(
            urgency_level=urgency,
            risk_factors=risk_factors,
            immediate_actions=immediate_actions,
            recommendations=recommendations,
            deadline_risks=deadline_risks,
            financial_exposure=financial_exposure
        )

    def _generate_summary(
        self,
        document_text: str,
        classification: ClassificationResult,
        extraction: ExtractionResult,
        deadlines: DeadlineResult
    ) -> AnalysisSummary:
        """Generate a summary of the filing"""
        # Build executive summary
        summary_parts = []

        # Filing type
        summary_parts.append(
            f"This is a {classification.filing_type_name} ({classification.category_name})."
        )

        # Parties
        if extraction.parties:
            plaintiffs = [p['name'] for p in extraction.parties if 'plaintiff' in p.get('role', '').lower()]
            defendants = [p['name'] for p in extraction.parties if 'defendant' in p.get('role', '').lower()]

            if plaintiffs and defendants:
                summary_parts.append(
                    f"The case involves {', '.join(plaintiffs[:2])} v. {', '.join(defendants[:2])}."
                )

        # Deadlines
        if deadlines.deadlines:
            next_deadline = deadlines.deadlines[0]
            summary_parts.append(
                f"The next deadline is {next_deadline['description']} on {next_deadline['date']}."
            )

        executive_summary = " ".join(summary_parts)

        # Key points
        key_points = []

        if classification.confidence >= 0.8:
            key_points.append(f"Filing type: {classification.filing_type_name}")

        if extraction.citations['case_law']:
            key_points.append(f"Cites {len(extraction.citations['case_law'])} cases")

        if extraction.monetary_amounts:
            key_points.append(f"Claims monetary damages")

        if deadlines.deadlines:
            key_points.append(f"Triggers {len(deadlines.deadlines)} deadline(s)")

        # Procedural status
        status_map = {
            'A': 'Case initiation - pleading stage',
            'B': 'Responsive pleading stage',
            'C': 'Pre-answer motion practice',
            'D': 'Discovery phase',
            'E': 'Dispositive motion stage',
            'F': 'Trial preparation',
            'G': 'Evidence/witness management',
            'H': 'Settlement/ADR',
            'L': 'Emergency proceedings',
            'O': 'Post-trial proceedings',
            'P': 'Appeal pending',
        }
        procedural_status = status_map.get(
            classification.category,
            'Procedural status unknown'
        )

        # Main relief sought (basic extraction from text)
        relief_patterns = [
            r'seeks?\s+([^.]+(?:damages|relief|judgment|order)[^.]*)',
            r'requests?\s+([^.]+(?:damages|relief|judgment|order)[^.]*)',
            r'prays?\s+for\s+([^.]+)',
        ]

        main_relief = "Relief sought not identified"
        for pattern in relief_patterns:
            match = re.search(pattern, document_text[:5000], re.IGNORECASE)
            if match:
                main_relief = match.group(1).strip()[:200]
                break

        # Filing date from extraction
        filing_date = None
        for d in extraction.dates:
            if d.get('date_type') == 'filing_date':
                filing_date = d.get('date')
                break

        return AnalysisSummary(
            executive_summary=executive_summary,
            key_points=key_points,
            procedural_status=procedural_status,
            main_relief_sought=main_relief,
            filing_date=filing_date
        )

    async def _perform_ai_analysis(
        self,
        document_text: str,
        classification: ClassificationResult,
        options: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str]:
        """Perform AI-powered analysis"""
        if not self.ai_service:
            return None, None

        # Build prompt based on filing type
        prompt_config = PromptConfig(
            include_system_prompt=True,
            include_few_shot=True,
            include_output_schema=True
        )

        prompts = self.prompt_builder.build_filing_specific_prompt(
            document_text[:15000],  # Limit context length
            classification.filing_type_code,
            prompt_config
        )

        try:
            # Call AI service
            response = await self.ai_service.generate(
                system_prompt=prompts['system'],
                user_prompt=prompts['user'],
                max_tokens=4000,
                temperature=0.2  # Lower temperature for more consistent output
            )

            raw_response = response.get('content', '')

            # Try to parse JSON from response
            try:
                # Find JSON in response
                json_match = re.search(r'\{[\s\S]*\}', raw_response)
                if json_match:
                    ai_analysis = json.loads(json_match.group())
                else:
                    ai_analysis = {'raw_text': raw_response}
            except json.JSONDecodeError:
                ai_analysis = {'raw_text': raw_response}

            return ai_analysis, raw_response

        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {'error': str(e)}, None

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def classify_only(self, document_text: str) -> ClassificationResult:
        """Perform classification only (no full analysis)"""
        return self._classify_document(document_text)

    def extract_only(self, document_text: str) -> ExtractionResult:
        """Perform extraction only (no full analysis)"""
        return self._extract_data(document_text)

    def calculate_deadlines_only(
        self,
        filing_type: str,
        filing_date: date,
        jurisdiction: JurisdictionType = JurisdictionType.FEDERAL,
        service_method: ServiceMethod = ServiceMethod.ELECTRONIC
    ) -> DeadlineResult:
        """Calculate deadlines for a specific filing type"""
        classification = ClassificationResult(
            filing_type_code=filing_type,
            filing_type_name="",
            category=filing_type[0] if filing_type else "X",
            category_name="",
            confidence=1.0,
            confidence_level=ConfidenceLevel.HIGH,
            practice_areas=[]
        )

        return self._calculate_deadlines(
            "",
            classification,
            filing_date.isoformat(),
            jurisdiction,
            service_method
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_analyzer(
    ai_service: Optional[Any] = None,
    jurisdiction: str = "federal",
    enable_ai: bool = True
) -> LegalFilingAnalyzer:
    """
    Factory function to create a configured analyzer

    Args:
        ai_service: Optional AI service instance
        jurisdiction: Default jurisdiction string
        enable_ai: Whether to enable AI analysis

    Returns:
        Configured LegalFilingAnalyzer instance
    """
    jurisdiction_map = {
        'federal': JurisdictionType.FEDERAL,
        'ca': JurisdictionType.STATE_CA,
        'california': JurisdictionType.STATE_CA,
        'ny': JurisdictionType.STATE_NY,
        'new_york': JurisdictionType.STATE_NY,
        'tx': JurisdictionType.STATE_TX,
        'texas': JurisdictionType.STATE_TX,
        'fl': JurisdictionType.STATE_FL,
        'florida': JurisdictionType.STATE_FL,
        'il': JurisdictionType.STATE_IL,
        'illinois': JurisdictionType.STATE_IL,
    }

    jurisdiction_type = jurisdiction_map.get(
        jurisdiction.lower(),
        JurisdictionType.FEDERAL
    )

    return LegalFilingAnalyzer(
        ai_service=ai_service,
        default_jurisdiction=jurisdiction_type,
        enable_ai_analysis=enable_ai
    )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main classes
    "LegalFilingAnalyzer",

    # Result classes
    "FilingAnalysisResult",
    "ClassificationResult",
    "ExtractionResult",
    "DeadlineResult",
    "RiskAssessment",
    "AnalysisSummary",

    # Enums
    "ConfidenceLevel",
    "UrgencyLevel",

    # Factory
    "create_analyzer",
]
