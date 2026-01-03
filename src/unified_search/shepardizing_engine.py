"""
Shepardizing engine for legal citation analysis and case treatment tracking.
Provides comprehensive citator services including case history, treatment analysis, and citation validation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

from ..types.unified_types import UnifiedDocument, ContentType
from .citation_validator import CitationValidator, CitationComponents


class TreatmentSignal(Enum):
    """Shepard's treatment signals for cases."""
    OVERRULED = "overruled"           # Red stop sign - no longer good law
    REVERSED = "reversed"             # Red stop sign - reversed on appeal
    SUPERSEDED = "superseded"         # Red stop sign - superseded by statute
    VACATED = "vacated"               # Red stop sign - vacated by court
    
    QUESTIONED = "questioned"         # Orange Q - validity questioned
    CRITICIZED = "criticized"         # Orange triangle - criticized by other courts
    LIMITED = "limited"               # Orange triangle - limited by other courts
    DISTINGUISHED = "distinguished"   # Orange triangle - distinguished by other courts
    
    FOLLOWED = "followed"             # Green plus - followed by other courts
    AFFIRMED = "affirmed"             # Green A - affirmed on appeal
    CITED = "cited"                   # Blue circle - cited positively
    EXPLAINED = "explained"           # Blue circle - explained by other courts
    
    NEUTRAL = "neutral"               # Yellow triangle - neutral treatment
    MENTIONED = "mentioned"           # Gray - mentioned without analysis


class CaseStatus(Enum):
    """Current status of a case."""
    GOOD_LAW = "good_law"
    QUESTIONABLE = "questionable"
    BAD_LAW = "bad_law"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"


class CitationContext(Enum):
    """Context in which a case is cited."""
    HOLDING = "holding"               # Cited for its holding
    DICTUM = "dictum"                # Cited for dicta
    DISSENT = "dissent"               # Cited from dissenting opinion
    BACKGROUND = "background"         # Cited for background/context
    PROCEDURAL = "procedural"         # Cited for procedural issue
    FACTUAL = "factual"               # Cited for similar facts
    DISTINGUISHING = "distinguishing" # Cited to distinguish facts/law


@dataclass
class CitingCase:
    """Information about a case that cites another case."""
    case_id: str
    case_name: str
    citation: str
    court: str
    jurisdiction: str
    decision_date: datetime
    treatment_signal: TreatmentSignal
    citation_context: CitationContext
    page_reference: Optional[str] = None
    headnote_number: Optional[int] = None
    relevant_text: Optional[str] = None
    confidence_score: float = 1.0


@dataclass
class CaseHistory:
    """Complete procedural history of a case."""
    case_id: str
    case_name: str
    citation: str
    
    # Procedural history (same case through different courts)
    prior_history: List['CaseHistoryEntry'] = field(default_factory=list)
    subsequent_history: List['CaseHistoryEntry'] = field(default_factory=list)
    
    # Related proceedings
    related_cases: List['RelatedCase'] = field(default_factory=list)
    
    # Final disposition
    final_disposition: Optional[str] = None
    current_status: CaseStatus = CaseStatus.UNKNOWN


@dataclass
class CaseHistoryEntry:
    """Single entry in case procedural history."""
    court: str
    jurisdiction: str
    citation: str
    decision_date: datetime
    disposition: str
    judges: List[str] = field(default_factory=list)


@dataclass
class RelatedCase:
    """Case related to the main case (e.g., companion case, consolidated case)."""
    case_id: str
    case_name: str
    citation: str
    relationship_type: str  # "companion", "consolidated", "remand", etc.
    description: Optional[str] = None


@dataclass
class HeadnoteAnalysis:
    """Analysis of specific headnotes and their treatment."""
    headnote_number: int
    headnote_text: str
    legal_principle: str
    citing_cases: List[CitingCase]
    treatment_summary: Dict[TreatmentSignal, int]
    reliability_score: float


@dataclass
class ShepardAnalysis:
    """Comprehensive Shepard's analysis for a case."""
    case_id: str
    case_name: str
    citation: str
    analysis_date: datetime
    
    # Overall status
    overall_status: CaseStatus
    status_confidence: float
    
    # Citation analysis
    citing_cases: List[CitingCase]
    total_citations: int
    positive_treatment_count: int
    negative_treatment_count: int
    neutral_treatment_count: int
    
    # Treatment breakdown
    treatment_summary: Dict[TreatmentSignal, int]
    
    # Case history
    case_history: CaseHistory
    
    # Headnote analysis
    headnote_analyses: List[HeadnoteAnalysis] = field(default_factory=list)
    
    # Alerts and warnings
    alerts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Authority assessment
    precedential_value: float = 0.0
    reliability_score: float = 0.0


class ShepardizingEngine:
    """
    Comprehensive Shepardizing engine for legal citation analysis.
    
    Provides citator services including:
    - Case treatment analysis
    - Citation validation and verification
    - Procedural history tracking
    - Authority assessment
    - Signal assignment
    """
    
    def __init__(self, citation_validator: Optional[CitationValidator] = None):
        self.citation_validator = citation_validator or CitationValidator()
        self.logger = logging.getLogger(__name__)
        
        # Cache for frequently accessed analyses
        self.analysis_cache: Dict[str, ShepardAnalysis] = {}
        self.cache_ttl = timedelta(hours=6)
        
        # Treatment signal weights for scoring
        self.signal_weights = {
            TreatmentSignal.OVERRULED: -1.0,
            TreatmentSignal.REVERSED: -1.0,
            TreatmentSignal.SUPERSEDED: -1.0,
            TreatmentSignal.VACATED: -1.0,
            TreatmentSignal.QUESTIONED: -0.7,
            TreatmentSignal.CRITICIZED: -0.5,
            TreatmentSignal.LIMITED: -0.3,
            TreatmentSignal.DISTINGUISHED: -0.2,
            TreatmentSignal.FOLLOWED: 0.8,
            TreatmentSignal.AFFIRMED: 1.0,
            TreatmentSignal.CITED: 0.5,
            TreatmentSignal.EXPLAINED: 0.3,
            TreatmentSignal.NEUTRAL: 0.0,
            TreatmentSignal.MENTIONED: 0.1
        }
    
    async def shepardize_case(self, 
                            case_document: UnifiedDocument,
                            include_history: bool = True,
                            include_headnotes: bool = True) -> ShepardAnalysis:
        """
        Perform comprehensive Shepardizing analysis on a case.
        
        Args:
            case_document: The case to analyze
            include_history: Whether to include procedural history
            include_headnotes: Whether to analyze individual headnotes
            
        Returns:
            ShepardAnalysis with complete citation analysis
        """
        case_id = case_document.id
        
        # Check cache first
        cache_key = self._generate_cache_key(case_id, include_history, include_headnotes)
        if cache_key in self.analysis_cache:
            cached_analysis = self.analysis_cache[cache_key]
            if datetime.now() - cached_analysis.analysis_date < self.cache_ttl:
                return cached_analysis
        
        self.logger.info(f"Starting Shepard's analysis for case: {case_document.title}")
        
        # Extract case citation
        case_citation = await self._extract_primary_citation(case_document)
        
        # Find all citing cases
        citing_cases = await self._find_citing_cases(case_document, case_citation)
        
        # Analyze treatment signals
        for citing_case in citing_cases:
            citing_case.treatment_signal = await self._analyze_treatment_signal(
                case_document, citing_case
            )
            citing_case.citation_context = await self._analyze_citation_context(
                case_document, citing_case
            )
        
        # Get case history if requested
        case_history = None
        if include_history:
            case_history = await self._analyze_case_history(case_document, case_citation)
        
        # Analyze headnotes if requested
        headnote_analyses = []
        if include_headnotes:
            headnote_analyses = await self._analyze_headnotes(case_document, citing_cases)
        
        # Calculate overall status and scores
        overall_status, status_confidence = await self._calculate_case_status(citing_cases)
        precedential_value = await self._calculate_precedential_value(case_document, citing_cases)
        reliability_score = await self._calculate_reliability_score(citing_cases)
        
        # Generate treatment summary
        treatment_summary = self._generate_treatment_summary(citing_cases)
        
        # Generate alerts and warnings
        alerts, warnings = await self._generate_alerts_and_warnings(citing_cases, overall_status)
        
        # Create analysis
        analysis = ShepardAnalysis(
            case_id=case_id,
            case_name=case_document.title or "Unknown Case",
            citation=case_citation,
            analysis_date=datetime.now(),
            overall_status=overall_status,
            status_confidence=status_confidence,
            citing_cases=citing_cases,
            total_citations=len(citing_cases),
            positive_treatment_count=len([c for c in citing_cases if self.signal_weights.get(c.treatment_signal, 0) > 0]),
            negative_treatment_count=len([c for c in citing_cases if self.signal_weights.get(c.treatment_signal, 0) < 0]),
            neutral_treatment_count=len([c for c in citing_cases if self.signal_weights.get(c.treatment_signal, 0) == 0]),
            treatment_summary=treatment_summary,
            case_history=case_history or CaseHistory(case_id=case_id, case_name=case_document.title, citation=case_citation),
            headnote_analyses=headnote_analyses,
            alerts=alerts,
            warnings=warnings,
            precedential_value=precedential_value,
            reliability_score=reliability_score
        )
        
        # Cache the analysis
        self.analysis_cache[cache_key] = analysis
        
        return analysis
    
    async def _extract_primary_citation(self, case_document: UnifiedDocument) -> str:
        """Extract the primary citation for a case."""
        # First try document metadata
        if case_document.citations:
            return case_document.citations[0]
        
        # Try to extract from content
        if case_document.content:
            citations = await self.citation_validator._extract_citations_from_text(case_document.content[:1000])
            if citations:
                # Validate and return the first valid case citation
                for citation in citations:
                    result = await self.citation_validator.validate_citation(citation)
                    if result.is_valid and result.citation_type.value == "case":
                        return citation
        
        # Fallback to document title or ID
        return case_document.title or f"Case ID: {case_document.id}"
    
    async def _find_citing_cases(self, case_document: UnifiedDocument, case_citation: str) -> List[CitingCase]:
        """Find all cases that cite the given case."""
        citing_cases = []
        
        # This would typically query a legal database
        # For demonstration, we'll simulate finding citing cases
        
        # Extract case name for searching
        case_name = case_document.title or ""
        case_name_parts = case_name.replace(" v. ", " ").replace(" vs. ", " ").split()
        
        # Simulate database search results
        # In practice, this would query Westlaw, Lexis, or other legal databases
        simulated_citing_cases = await self._simulate_citing_cases_search(
            case_document.id, case_name, case_citation
        )
        
        for citing_data in simulated_citing_cases:
            citing_case = CitingCase(
                case_id=citing_data['id'],
                case_name=citing_data['name'],
                citation=citing_data['citation'],
                court=citing_data['court'],
                jurisdiction=citing_data['jurisdiction'],
                decision_date=citing_data['date'],
                treatment_signal=TreatmentSignal.NEUTRAL,  # Will be analyzed later
                citation_context=CitationContext.HOLDING,  # Will be analyzed later
                page_reference=citing_data.get('page'),
                relevant_text=citing_data.get('text'),
                confidence_score=citing_data.get('confidence', 0.8)
            )
            citing_cases.append(citing_case)
        
        return citing_cases
    
    async def _simulate_citing_cases_search(self, case_id: str, case_name: str, citation: str) -> List[Dict[str, Any]]:
        """Simulate search for citing cases (placeholder for actual database queries)."""
        # This is a placeholder - real implementation would query legal databases
        return [
            {
                'id': f'citing_case_1_{case_id}',
                'name': f'Smith v. Jones',
                'citation': '123 F.3d 456',
                'court': '9th Cir.',
                'jurisdiction': 'Federal',
                'date': datetime(2022, 1, 15),
                'page': '460',
                'text': f'Following the holding in {case_name}, we conclude...',
                'confidence': 0.9
            },
            {
                'id': f'citing_case_2_{case_id}',
                'name': f'Brown v. Wilson',
                'citation': '456 F. Supp. 2d 789',
                'court': 'N.D. Cal.',
                'jurisdiction': 'Federal',
                'date': datetime(2021, 8, 22),
                'page': '795',
                'text': f'We question the reasoning in {case_name}...',
                'confidence': 0.85
            },
            {
                'id': f'citing_case_3_{case_id}',
                'name': f'Johnson v. Davis',
                'citation': '789 P.3d 123',
                'court': 'Cal. Sup. Ct.',
                'jurisdiction': 'California',
                'date': datetime(2023, 3, 10),
                'page': '128',
                'text': f'The court in {case_name} was overruled by...',
                'confidence': 0.75
            }
        ]
    
    async def _analyze_treatment_signal(self, original_case: UnifiedDocument, citing_case: CitingCase) -> TreatmentSignal:
        """Analyze how a citing case treats the original case."""
        if not citing_case.relevant_text:
            return TreatmentSignal.MENTIONED
        
        text_lower = citing_case.relevant_text.lower()
        
        # Negative signals
        if any(term in text_lower for term in ['overrule', 'overruled', 'overturned']):
            return TreatmentSignal.OVERRULED
        if any(term in text_lower for term in ['reverse', 'reversed', 'reversal']):
            return TreatmentSignal.REVERSED
        if any(term in text_lower for term in ['supersede', 'superseded']):
            return TreatmentSignal.SUPERSEDED
        if any(term in text_lower for term in ['vacate', 'vacated']):
            return TreatmentSignal.VACATED
        if any(term in text_lower for term in ['question', 'questionable', 'doubt']):
            return TreatmentSignal.QUESTIONED
        if any(term in text_lower for term in ['criticize', 'criticized', 'criticism']):
            return TreatmentSignal.CRITICIZED
        if any(term in text_lower for term in ['limit', 'limited', 'limiting']):
            return TreatmentSignal.LIMITED
        if any(term in text_lower for term in ['distinguish', 'distinguished', 'distinguishable']):
            return TreatmentSignal.DISTINGUISHED
        
        # Positive signals
        if any(term in text_lower for term in ['follow', 'followed', 'following']):
            return TreatmentSignal.FOLLOWED
        if any(term in text_lower for term in ['affirm', 'affirmed', 'affirmance']):
            return TreatmentSignal.AFFIRMED
        if any(term in text_lower for term in ['explain', 'explained', 'explanation']):
            return TreatmentSignal.EXPLAINED
        
        # Neutral/positive citation
        if any(term in text_lower for term in ['cite', 'citing', 'held', 'holding', 'rule', 'ruling']):
            return TreatmentSignal.CITED
        
        return TreatmentSignal.NEUTRAL
    
    async def _analyze_citation_context(self, original_case: UnifiedDocument, citing_case: CitingCase) -> CitationContext:
        """Analyze the context in which a case is cited."""
        if not citing_case.relevant_text:
            return CitationContext.BACKGROUND
        
        text_lower = citing_case.relevant_text.lower()
        
        # Analyze context keywords
        if any(term in text_lower for term in ['holding', 'held that', 'ruled that', 'decided that']):
            return CitationContext.HOLDING
        if any(term in text_lower for term in ['dictum', 'dicta', 'observation', 'comment']):
            return CitationContext.DICTUM
        if any(term in text_lower for term in ['dissent', 'dissenting', 'minority opinion']):
            return CitationContext.DISSENT
        if any(term in text_lower for term in ['procedure', 'procedural', 'motion', 'jurisdiction']):
            return CitationContext.PROCEDURAL
        if any(term in text_lower for term in ['facts', 'factual', 'circumstances', 'situation']):
            return CitationContext.FACTUAL
        if any(term in text_lower for term in ['distinguish', 'different', 'unlike', 'contrast']):
            return CitationContext.DISTINGUISHING
        
        return CitationContext.BACKGROUND
    
    async def _analyze_case_history(self, case_document: UnifiedDocument, case_citation: str) -> CaseHistory:
        """Analyze the procedural history of a case."""
        # This would typically query legal databases for the complete procedural history
        # For demonstration, we'll simulate the history
        
        case_history = CaseHistory(
            case_id=case_document.id,
            case_name=case_document.title or "Unknown Case",
            citation=case_citation
        )
        
        # Simulate finding prior and subsequent history
        # In practice, this would involve complex database queries and citation matching
        
        # Add simulated prior history (trial court, etc.)
        if 'Cir.' in case_citation or 'F.2d' in case_citation or 'F.3d' in case_citation:
            case_history.prior_history.append(
                CaseHistoryEntry(
                    court="District Court",
                    jurisdiction="Federal",
                    citation="123 F. Supp. 2d 456",
                    decision_date=datetime(2020, 6, 15),
                    disposition="Granted summary judgment for defendant"
                )
            )
        
        # Add simulated subsequent history if applicable
        if 'F. Supp.' in case_citation:
            case_history.subsequent_history.append(
                CaseHistoryEntry(
                    court="Court of Appeals",
                    jurisdiction="Federal",
                    citation="456 F.3d 789",
                    decision_date=datetime(2021, 9, 30),
                    disposition="Reversed and remanded"
                )
            )
        
        # Determine current status based on history
        if case_history.subsequent_history:
            latest_entry = max(case_history.subsequent_history, key=lambda x: x.decision_date)
            if 'reversed' in latest_entry.disposition.lower():
                case_history.current_status = CaseStatus.BAD_LAW
            elif 'affirmed' in latest_entry.disposition.lower():
                case_history.current_status = CaseStatus.GOOD_LAW
            else:
                case_history.current_status = CaseStatus.QUESTIONABLE
        else:
            case_history.current_status = CaseStatus.GOOD_LAW
        
        return case_history
    
    async def _analyze_headnotes(self, case_document: UnifiedDocument, citing_cases: List[CitingCase]) -> List[HeadnoteAnalysis]:
        """Analyze treatment of individual headnotes."""
        headnote_analyses = []
        
        # Extract headnotes from case content (simplified)
        if not case_document.content:
            return headnote_analyses
        
        # Simulate headnote extraction and analysis
        simulated_headnotes = [
            {
                'number': 1,
                'text': 'Contract law principle regarding consideration',
                'principle': 'Adequate consideration must exist for a valid contract'
            },
            {
                'number': 2,
                'text': 'Procedural requirements for summary judgment',
                'principle': 'Moving party must show no genuine issue of material fact'
            }
        ]
        
        for headnote_data in simulated_headnotes:
            # Find citing cases that reference this headnote
            relevant_citing_cases = [
                case for case in citing_cases
                if case.headnote_number == headnote_data['number']
                or (case.relevant_text and str(headnote_data['number']) in case.relevant_text)
            ]
            
            # Calculate treatment summary for this headnote
            treatment_summary = {}
            for citing_case in relevant_citing_cases:
                signal = citing_case.treatment_signal
                treatment_summary[signal] = treatment_summary.get(signal, 0) + 1
            
            # Calculate reliability score
            reliability_score = self._calculate_headnote_reliability(relevant_citing_cases)
            
            analysis = HeadnoteAnalysis(
                headnote_number=headnote_data['number'],
                headnote_text=headnote_data['text'],
                legal_principle=headnote_data['principle'],
                citing_cases=relevant_citing_cases,
                treatment_summary=treatment_summary,
                reliability_score=reliability_score
            )
            
            headnote_analyses.append(analysis)
        
        return headnote_analyses
    
    def _calculate_headnote_reliability(self, citing_cases: List[CitingCase]) -> float:
        """Calculate reliability score for a specific headnote."""
        if not citing_cases:
            return 0.0
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for citing_case in citing_cases:
            weight = citing_case.confidence_score
            signal_score = self.signal_weights.get(citing_case.treatment_signal, 0)
            
            total_weight += weight
            weighted_score += weight * signal_score
        
        return max(0.0, weighted_score / total_weight) if total_weight > 0 else 0.0
    
    async def _calculate_case_status(self, citing_cases: List[CitingCase]) -> Tuple[CaseStatus, float]:
        """Calculate overall case status and confidence."""
        if not citing_cases:
            return CaseStatus.UNKNOWN, 0.0
        
        # Count negative signals
        negative_signals = [
            TreatmentSignal.OVERRULED, TreatmentSignal.REVERSED, 
            TreatmentSignal.SUPERSEDED, TreatmentSignal.VACATED
        ]
        
        questionable_signals = [
            TreatmentSignal.QUESTIONED, TreatmentSignal.CRITICIZED,
            TreatmentSignal.LIMITED, TreatmentSignal.DISTINGUISHED
        ]
        
        # Check for definitive negative treatment
        for citing_case in citing_cases:
            if citing_case.treatment_signal in negative_signals:
                return CaseStatus.BAD_LAW, citing_case.confidence_score
        
        # Calculate weighted score
        total_weight = 0.0
        weighted_score = 0.0
        
        for citing_case in citing_cases:
            weight = citing_case.confidence_score
            signal_weight = self.signal_weights.get(citing_case.treatment_signal, 0)
            
            total_weight += weight
            weighted_score += weight * signal_weight
        
        average_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Determine status based on score
        if average_score >= 0.3:
            return CaseStatus.GOOD_LAW, min(0.9, total_weight / len(citing_cases))
        elif average_score >= -0.3:
            return CaseStatus.QUESTIONABLE, min(0.8, total_weight / len(citing_cases))
        else:
            return CaseStatus.BAD_LAW, min(0.7, total_weight / len(citing_cases))
    
    async def _calculate_precedential_value(self, case_document: UnifiedDocument, citing_cases: List[CitingCase]) -> float:
        """Calculate the precedential value of a case."""
        base_score = 0.5  # Base score
        
        # Boost based on number of citations
        citation_boost = min(0.3, len(citing_cases) * 0.01)
        
        # Boost based on positive treatment
        positive_citations = [c for c in citing_cases if self.signal_weights.get(c.treatment_signal, 0) > 0]
        positive_boost = min(0.2, len(positive_citations) * 0.02)
        
        # Reduce based on negative treatment
        negative_citations = [c for c in citing_cases if self.signal_weights.get(c.treatment_signal, 0) < 0]
        negative_penalty = min(0.4, len(negative_citations) * 0.05)
        
        # Court level boost (if available in metadata)
        court_boost = 0.0
        if hasattr(case_document, 'court_level'):
            court_level = getattr(case_document, 'court_level', '').lower()
            if 'supreme court' in court_level:
                court_boost = 0.3
            elif 'circuit' in court_level or 'appellate' in court_level:
                court_boost = 0.2
            elif 'district' in court_level:
                court_boost = 0.1
        
        final_score = base_score + citation_boost + positive_boost + court_boost - negative_penalty
        return max(0.0, min(1.0, final_score))
    
    async def _calculate_reliability_score(self, citing_cases: List[CitingCase]) -> float:
        """Calculate overall reliability score."""
        if not citing_cases:
            return 0.0
        
        # Average confidence of citing cases
        avg_confidence = sum(case.confidence_score for case in citing_cases) / len(citing_cases)
        
        # Treatment consistency (prefer clear signals over mixed)
        signal_counts = {}
        for case in citing_cases:
            signal = case.treatment_signal
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
        
        # Calculate entropy (lower is better - more consistent)
        total = len(citing_cases)
        entropy = 0.0
        for count in signal_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * (p.bit_length() - 1) if p > 0 else 0
        
        consistency_score = max(0.0, 1.0 - entropy / 3.0)  # Normalize entropy
        
        return (avg_confidence + consistency_score) / 2
    
    def _generate_treatment_summary(self, citing_cases: List[CitingCase]) -> Dict[TreatmentSignal, int]:
        """Generate summary of treatment signals."""
        summary = {}
        for case in citing_cases:
            signal = case.treatment_signal
            summary[signal] = summary.get(signal, 0) + 1
        return summary
    
    async def _generate_alerts_and_warnings(self, citing_cases: List[CitingCase], overall_status: CaseStatus) -> Tuple[List[str], List[str]]:
        """Generate alerts and warnings based on citation analysis."""
        alerts = []
        warnings = []
        
        # Critical alerts
        if overall_status == CaseStatus.BAD_LAW:
            alerts.append("⚠️  CRITICAL: This case has been overruled, reversed, or superseded")
        
        # Count negative treatments
        negative_count = len([c for c in citing_cases if self.signal_weights.get(c.treatment_signal, 0) < -0.5])
        if negative_count >= 3:
            alerts.append(f"⚠️  Multiple courts have criticized or questioned this case ({negative_count} instances)")
        
        # Warnings for questionable status
        if overall_status == CaseStatus.QUESTIONABLE:
            warnings.append("⚡ The validity of this case has been questioned by other courts")
        
        # Recent negative treatment
        recent_negative = [
            c for c in citing_cases 
            if self.signal_weights.get(c.treatment_signal, 0) < 0 
            and c.decision_date > datetime.now() - timedelta(days=365)
        ]
        if recent_negative:
            warnings.append(f"📅 Recent negative treatment within the past year ({len(recent_negative)} cases)")
        
        # Limited or distinguished frequently
        limited_count = len([c for c in citing_cases if c.treatment_signal in [TreatmentSignal.LIMITED, TreatmentSignal.DISTINGUISHED]])
        if limited_count >= 5:
            warnings.append(f"🔍 This case has been limited or distinguished frequently ({limited_count} times)")
        
        return alerts, warnings
    
    def _generate_cache_key(self, case_id: str, include_history: bool, include_headnotes: bool) -> str:
        """Generate cache key for analysis."""
        key_data = f"{case_id}_{include_history}_{include_headnotes}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_citation_network(self, case_document: UnifiedDocument, depth: int = 2) -> Dict[str, Any]:
        """Build citation network graph for a case."""
        network = {
            'nodes': [],
            'edges': [],
            'center_case': case_document.id
        }
        
        # Add center node
        network['nodes'].append({
            'id': case_document.id,
            'name': case_document.title,
            'type': 'center',
            'status': 'unknown'  # Will be determined by Shepardizing
        })
        
        if depth <= 0:
            return network
        
        # Get citing cases
        analysis = await self.shepardize_case(case_document, include_history=False, include_headnotes=False)
        
        for citing_case in analysis.citing_cases:
            # Add citing case node
            network['nodes'].append({
                'id': citing_case.case_id,
                'name': citing_case.case_name,
                'type': 'citing',
                'court': citing_case.court,
                'jurisdiction': citing_case.jurisdiction,
                'date': citing_case.decision_date.isoformat(),
                'treatment': citing_case.treatment_signal.value
            })
            
            # Add edge
            network['edges'].append({
                'source': citing_case.case_id,
                'target': case_document.id,
                'type': 'cites',
                'treatment': citing_case.treatment_signal.value,
                'context': citing_case.citation_context.value,
                'weight': citing_case.confidence_score
            })
        
        return network
    
    async def compare_case_treatments(self, case_documents: List[UnifiedDocument]) -> Dict[str, Any]:
        """Compare Shepard's treatment across multiple cases."""
        if len(case_documents) < 2:
            return {'error': 'At least two cases required for comparison'}
        
        analyses = []
        for case_doc in case_documents[:5]:  # Limit to 5 cases for performance
            analysis = await self.shepardize_case(case_doc, include_history=False, include_headnotes=False)
            analyses.append(analysis)
        
        comparison = {
            'cases': [],
            'summary': {},
            'recommendations': []
        }
        
        for analysis in analyses:
            case_summary = {
                'case_id': analysis.case_id,
                'case_name': analysis.case_name,
                'citation': analysis.citation,
                'status': analysis.overall_status.value,
                'confidence': analysis.status_confidence,
                'total_citations': analysis.total_citations,
                'positive_treatment': analysis.positive_treatment_count,
                'negative_treatment': analysis.negative_treatment_count,
                'precedential_value': analysis.precedential_value,
                'reliability_score': analysis.reliability_score,
                'has_alerts': len(analysis.alerts) > 0
            }
            comparison['cases'].append(case_summary)
        
        # Generate summary statistics
        all_statuses = [case['status'] for case in comparison['cases']]
        comparison['summary'] = {
            'good_law_count': all_statuses.count('good_law'),
            'questionable_count': all_statuses.count('questionable'),
            'bad_law_count': all_statuses.count('bad_law'),
            'average_precedential_value': sum(case['precedential_value'] for case in comparison['cases']) / len(comparison['cases']),
            'average_reliability': sum(case['reliability_score'] for case in comparison['cases']) / len(comparison['cases'])
        }
        
        # Generate recommendations
        bad_law_cases = [case for case in comparison['cases'] if case['status'] == 'bad_law']
        if bad_law_cases:
            comparison['recommendations'].append(
                f"⚠️  Avoid relying on {len(bad_law_cases)} case(s) with bad law status: "
                + ", ".join([case['case_name'] for case in bad_law_cases])
            )
        
        best_cases = sorted(comparison['cases'], key=lambda x: (x['precedential_value'], x['reliability_score']), reverse=True)[:2]
        if best_cases:
            comparison['recommendations'].append(
                f"✅ Strongest authorities: " + 
                ", ".join([case['case_name'] for case in best_cases])
            )
        
        return comparison


# Helper functions
async def shepardize_document(document: UnifiedDocument) -> ShepardAnalysis:
    """Helper function to Shepardize a single document."""
    engine = ShepardizingEngine()
    return await engine.shepardize_case(document)

async def quick_case_status_check(document: UnifiedDocument) -> CaseStatus:
    """Quick check of case status without full analysis."""
    engine = ShepardizingEngine()
    analysis = await engine.shepardize_case(document, include_history=False, include_headnotes=False)
    return analysis.overall_status