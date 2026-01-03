"""
Advanced case treatment analysis engine.
Provides deep analysis of how cases are treated by subsequent courts and legal authorities.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np

from ..types.unified_types import UnifiedDocument, ContentType
from .shepardizing_engine import TreatmentSignal, CaseStatus, CitingCase, CitationContext


class TreatmentDepth(Enum):
    """Depth of treatment analysis."""
    SURFACE = "surface"           # Basic mention or citation
    SUBSTANTIVE = "substantive"   # Detailed discussion
    COMPREHENSIVE = "comprehensive" # Extensive analysis


class TreatmentReliability(Enum):
    """Reliability of treatment assessment."""
    HIGH = "high"         # Clear, unambiguous treatment
    MEDIUM = "medium"     # Reasonably clear treatment
    LOW = "low"          # Ambiguous or unclear treatment
    UNCERTAIN = "uncertain" # Cannot determine treatment


@dataclass
class TreatmentContext:
    """Detailed context of how a case is treated."""
    treatment_signal: TreatmentSignal
    treatment_depth: TreatmentDepth
    reliability: TreatmentReliability
    
    # Context details
    paragraph_context: str
    surrounding_text: str
    legal_reasoning: Optional[str] = None
    
    # Citation specifics
    page_numbers: List[str] = field(default_factory=list)
    headnote_references: List[int] = field(default_factory=list)
    
    # Analysis metrics
    confidence_score: float = 0.0
    sentiment_score: float = 0.0  # -1 (very negative) to 1 (very positive)


@dataclass
class TreatmentPattern:
    """Pattern of treatment across multiple citing cases."""
    pattern_type: str
    description: str
    frequency: int
    examples: List[str]
    significance: float  # 0-1 scale


@dataclass
class JurisdictionalTreatment:
    """Treatment analysis by jurisdiction."""
    jurisdiction: str
    court_level: str
    
    total_citations: int
    positive_citations: int
    negative_citations: int
    neutral_citations: int
    
    dominant_signal: TreatmentSignal
    treatment_consistency: float  # 0-1, higher means more consistent
    authority_weight: float  # Weight of this jurisdiction's treatment


@dataclass
class TemporalTreatment:
    """Treatment analysis over time."""
    time_period: str
    start_date: datetime
    end_date: datetime
    
    citation_count: int
    treatment_trend: str  # "improving", "declining", "stable", "volatile"
    signal_distribution: Dict[TreatmentSignal, int]
    
    significant_events: List[str] = field(default_factory=list)


@dataclass
class TreatmentAnalysis:
    """Comprehensive treatment analysis for a case."""
    case_id: str
    case_name: str
    analysis_date: datetime
    
    # Overall treatment assessment
    overall_treatment: TreatmentSignal
    treatment_confidence: float
    treatment_consensus: float  # How much courts agree on treatment
    
    # Detailed treatment contexts
    treatment_contexts: List[TreatmentContext]
    
    # Pattern analysis
    treatment_patterns: List[TreatmentPattern]
    
    # Jurisdictional breakdown
    jurisdictional_analysis: List[JurisdictionalTreatment]
    
    # Temporal analysis
    temporal_analysis: List[TemporalTreatment]
    
    # Key insights
    key_insights: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class CaseTreatmentAnalyzer:
    """
    Advanced analyzer for case treatment patterns.
    
    Provides deep analysis of how cases are treated by subsequent courts,
    including sentiment analysis, pattern recognition, and trend analysis.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Treatment signal keywords and weights
        self.signal_keywords = {
            TreatmentSignal.OVERRULED: {
                'strong': ['overrule', 'overruled', 'overrules', 'overruling', 'expressly overruled'],
                'moderate': ['no longer good law', 'cannot stand', 'rejected'],
                'weak': ['contrary to', 'inconsistent with']
            },
            TreatmentSignal.QUESTIONED: {
                'strong': ['questioned', 'questionable', 'doubt', 'doubted', 'uncertain'],
                'moderate': ['problematic', 'unclear', 'ambiguous'],
                'weak': ['concern', 'issue with', 'difficulty with']
            },
            TreatmentSignal.CRITICIZED: {
                'strong': ['criticized', 'disapproved', 'condemned'],
                'moderate': ['disagreed with', 'took issue with'],
                'weak': ['noted problems', 'expressed concern']
            },
            TreatmentSignal.FOLLOWED: {
                'strong': ['followed', 'adopted', 'embraced', 'endorsed'],
                'moderate': ['applied', 'relied on', 'consistent with'],
                'weak': ['considered', 'noted', 'referenced']
            },
            TreatmentSignal.DISTINGUISHED: {
                'strong': ['distinguished', 'distinguishable', 'inapplicable'],
                'moderate': ['different facts', 'different circumstances'],
                'weak': ['factually different', 'not on point']
            }
        }
        
        # Sentiment analysis keywords
        self.positive_sentiment = {
            'strong': ['excellent', 'brilliant', 'outstanding', 'exemplary', 'seminal'],
            'moderate': ['good', 'sound', 'reasonable', 'well-reasoned', 'appropriate'],
            'weak': ['adequate', 'acceptable', 'proper']
        }
        
        self.negative_sentiment = {
            'strong': ['terrible', 'awful', 'deeply flawed', 'completely wrong'],
            'moderate': ['problematic', 'concerning', 'questionable', 'troubling'],
            'weak': ['imperfect', 'limited', 'narrow']
        }
        
        # Court hierarchy weights
        self.court_weights = {
            'Supreme Court': 1.0,
            'Circuit Court': 0.8,
            'Appellate Court': 0.8,
            'District Court': 0.6,
            'Trial Court': 0.4,
            'State Supreme Court': 0.9,
            'State Appellate Court': 0.7,
            'State Trial Court': 0.3
        }
    
    async def analyze_case_treatment(self, 
                                   case_document: UnifiedDocument,
                                   citing_cases: List[CitingCase],
                                   include_temporal: bool = True,
                                   include_jurisdictional: bool = True) -> TreatmentAnalysis:
        """
        Perform comprehensive treatment analysis.
        
        Args:
            case_document: The case being analyzed
            citing_cases: Cases that cite the target case
            include_temporal: Whether to include temporal analysis
            include_jurisdictional: Whether to include jurisdictional breakdown
            
        Returns:
            Comprehensive treatment analysis
        """
        self.logger.info(f"Analyzing treatment for case: {case_document.title}")
        
        # Analyze individual treatment contexts
        treatment_contexts = []
        for citing_case in citing_cases:
            context = await self._analyze_treatment_context(case_document, citing_case)
            treatment_contexts.append(context)
        
        # Identify treatment patterns
        treatment_patterns = await self._identify_treatment_patterns(treatment_contexts)
        
        # Jurisdictional analysis
        jurisdictional_analysis = []
        if include_jurisdictional:
            jurisdictional_analysis = await self._analyze_jurisdictional_treatment(citing_cases)
        
        # Temporal analysis
        temporal_analysis = []
        if include_temporal:
            temporal_analysis = await self._analyze_temporal_treatment(citing_cases)
        
        # Calculate overall treatment metrics
        overall_treatment, treatment_confidence = await self._calculate_overall_treatment(treatment_contexts)
        treatment_consensus = await self._calculate_treatment_consensus(treatment_contexts)
        
        # Generate insights and recommendations
        key_insights = await self._generate_key_insights(treatment_contexts, treatment_patterns)
        warnings = await self._generate_warnings(treatment_contexts, overall_treatment)
        recommendations = await self._generate_recommendations(treatment_contexts, treatment_patterns)
        
        return TreatmentAnalysis(
            case_id=case_document.id,
            case_name=case_document.title or "Unknown Case",
            analysis_date=datetime.now(),
            overall_treatment=overall_treatment,
            treatment_confidence=treatment_confidence,
            treatment_consensus=treatment_consensus,
            treatment_contexts=treatment_contexts,
            treatment_patterns=treatment_patterns,
            jurisdictional_analysis=jurisdictional_analysis,
            temporal_analysis=temporal_analysis,
            key_insights=key_insights,
            warnings=warnings,
            recommendations=recommendations
        )
    
    async def _analyze_treatment_context(self, 
                                       original_case: UnifiedDocument, 
                                       citing_case: CitingCase) -> TreatmentContext:
        """Analyze the detailed context of how a case is treated."""
        
        # Get the relevant text (would typically be extracted from full case text)
        relevant_text = citing_case.relevant_text or ""
        
        # Analyze treatment signal with confidence
        treatment_signal, signal_confidence = await self._analyze_treatment_signal_detailed(relevant_text)
        
        # Determine treatment depth
        treatment_depth = await self._assess_treatment_depth(relevant_text)
        
        # Assess reliability
        reliability = await self._assess_treatment_reliability(relevant_text, signal_confidence)
        
        # Extract legal reasoning if present
        legal_reasoning = await self._extract_legal_reasoning(relevant_text)
        
        # Calculate sentiment score
        sentiment_score = await self._calculate_sentiment_score(relevant_text)
        
        # Extract page and headnote references
        page_numbers = self._extract_page_references(relevant_text)
        headnote_references = self._extract_headnote_references(relevant_text)
        
        return TreatmentContext(
            treatment_signal=treatment_signal,
            treatment_depth=treatment_depth,
            reliability=reliability,
            paragraph_context=relevant_text[:500],  # First 500 chars
            surrounding_text=relevant_text,
            legal_reasoning=legal_reasoning,
            page_numbers=page_numbers,
            headnote_references=headnote_references,
            confidence_score=signal_confidence,
            sentiment_score=sentiment_score
        )
    
    async def _analyze_treatment_signal_detailed(self, text: str) -> Tuple[TreatmentSignal, float]:
        """Detailed analysis of treatment signal with confidence scoring."""
        if not text:
            return TreatmentSignal.NEUTRAL, 0.0
        
        text_lower = text.lower()
        
        # Score each signal type
        signal_scores = {}
        
        for signal, keyword_sets in self.signal_keywords.items():
            score = 0.0
            
            # Check for strong indicators
            for keyword in keyword_sets.get('strong', []):
                if keyword in text_lower:
                    score += 1.0
            
            # Check for moderate indicators
            for keyword in keyword_sets.get('moderate', []):
                if keyword in text_lower:
                    score += 0.6
            
            # Check for weak indicators
            for keyword in keyword_sets.get('weak', []):
                if keyword in text_lower:
                    score += 0.3
            
            if score > 0:
                signal_scores[signal] = score
        
        # If no specific signals found, check for general citation patterns
        if not signal_scores:
            if any(word in text_lower for word in ['held', 'ruled', 'decided', 'concluded']):
                signal_scores[TreatmentSignal.CITED] = 0.5
            else:
                signal_scores[TreatmentSignal.MENTIONED] = 0.3
        
        # Select highest scoring signal
        if signal_scores:
            best_signal = max(signal_scores.keys(), key=lambda x: signal_scores[x])
            confidence = min(1.0, signal_scores[best_signal] / 2.0)  # Normalize confidence
            return best_signal, confidence
        
        return TreatmentSignal.NEUTRAL, 0.2
    
    async def _assess_treatment_depth(self, text: str) -> TreatmentDepth:
        """Assess the depth of treatment based on text analysis."""
        if not text:
            return TreatmentDepth.SURFACE
        
        # Count indicators of depth
        word_count = len(text.split())
        sentence_count = len([s for s in text.split('.') if s.strip()])
        
        # Look for analysis indicators
        analysis_indicators = [
            'analysis', 'reasoning', 'rationale', 'because', 'therefore',
            'however', 'nevertheless', 'furthermore', 'moreover',
            'explained', 'discussed', 'examined', 'considered'
        ]
        
        analysis_count = sum(1 for indicator in analysis_indicators if indicator in text.lower())
        
        # Determine depth based on length and analysis indicators
        if word_count > 200 and analysis_count >= 3:
            return TreatmentDepth.COMPREHENSIVE
        elif word_count > 50 and analysis_count >= 1:
            return TreatmentDepth.SUBSTANTIVE
        else:
            return TreatmentDepth.SURFACE
    
    async def _assess_treatment_reliability(self, text: str, signal_confidence: float) -> TreatmentReliability:
        """Assess reliability of treatment assessment."""
        
        # Base reliability on signal confidence
        if signal_confidence >= 0.8:
            base_reliability = TreatmentReliability.HIGH
        elif signal_confidence >= 0.6:
            base_reliability = TreatmentReliability.MEDIUM
        elif signal_confidence >= 0.3:
            base_reliability = TreatmentReliability.LOW
        else:
            base_reliability = TreatmentReliability.UNCERTAIN
        
        # Adjust based on text characteristics
        text_lower = text.lower()
        
        # Indicators of uncertainty
        uncertainty_indicators = [
            'may', 'might', 'could', 'perhaps', 'possibly', 'arguably',
            'unclear', 'ambiguous', 'uncertain', 'questionable'
        ]
        
        uncertainty_count = sum(1 for indicator in uncertainty_indicators if indicator in text_lower)
        
        # Reduce reliability if many uncertainty indicators
        if uncertainty_count >= 3:
            if base_reliability == TreatmentReliability.HIGH:
                return TreatmentReliability.MEDIUM
            elif base_reliability == TreatmentReliability.MEDIUM:
                return TreatmentReliability.LOW
            else:
                return TreatmentReliability.UNCERTAIN
        
        return base_reliability
    
    async def _extract_legal_reasoning(self, text: str) -> Optional[str]:
        """Extract legal reasoning from treatment text."""
        if not text:
            return None
        
        # Look for reasoning indicators
        reasoning_patterns = [
            r'because\s+(.{20,200})',
            r'since\s+(.{20,200})',
            r'the\s+court\s+reasoned\s+that\s+(.{20,200})',
            r'the\s+rationale\s+(?:was|is)\s+(.{20,200})',
            r'explained\s+that\s+(.{20,200})'
        ]
        
        for pattern in reasoning_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                # Clean up the reasoning text
                reasoning = re.sub(r'\s+', ' ', reasoning)
                if len(reasoning) > 20:
                    return reasoning[:300]  # Limit length
        
        return None
    
    async def _calculate_sentiment_score(self, text: str) -> float:
        """Calculate sentiment score for treatment text."""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        positive_score = 0.0
        negative_score = 0.0
        
        # Calculate positive sentiment
        for strength, keywords in self.positive_sentiment.items():
            weight = {'strong': 1.0, 'moderate': 0.6, 'weak': 0.3}[strength]
            for keyword in keywords:
                if keyword in text_lower:
                    positive_score += weight
        
        # Calculate negative sentiment
        for strength, keywords in self.negative_sentiment.items():
            weight = {'strong': 1.0, 'moderate': 0.6, 'weak': 0.3}[strength]
            for keyword in keywords:
                if keyword in text_lower:
                    negative_score += weight
        
        # Normalize to -1 to 1 scale
        total_score = positive_score - negative_score
        return max(-1.0, min(1.0, total_score / 3.0))
    
    def _extract_page_references(self, text: str) -> List[str]:
        """Extract page number references from text."""
        page_patterns = [
            r'at\s+(\d+)',
            r'page\s+(\d+)',
            r'p\.\s*(\d+)',
            r'pp\.\s*(\d+(?:-\d+)?)'
        ]
        
        pages = []
        for pattern in page_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pages.append(match.group(1))
        
        return list(set(pages))  # Remove duplicates
    
    def _extract_headnote_references(self, text: str) -> List[int]:
        """Extract headnote number references from text."""
        headnote_patterns = [
            r'headnote\s+(\d+)',
            r'hn\s*(\d+)',
            r'\[(\d+)\]'  # Common headnote reference format
        ]
        
        headnotes = []
        for pattern in headnote_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    headnotes.append(int(match.group(1)))
                except ValueError:
                    continue
        
        return sorted(list(set(headnotes)))
    
    async def _identify_treatment_patterns(self, contexts: List[TreatmentContext]) -> List[TreatmentPattern]:
        """Identify patterns in case treatment."""
        patterns = []
        
        if not contexts:
            return patterns
        
        # Pattern 1: Consistent negative treatment
        negative_contexts = [c for c in contexts if c.sentiment_score < -0.3]
        if len(negative_contexts) >= 3:
            patterns.append(TreatmentPattern(
                pattern_type="consistent_criticism",
                description=f"Case consistently criticized across {len(negative_contexts)} courts",
                frequency=len(negative_contexts),
                examples=[c.paragraph_context[:100] for c in negative_contexts[:3]],
                significance=0.8
            ))
        
        # Pattern 2: Jurisdictional split
        signal_counts = {}
        for context in contexts:
            signal = context.treatment_signal
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
        
        if len(signal_counts) >= 3 and max(signal_counts.values()) < len(contexts) * 0.6:
            patterns.append(TreatmentPattern(
                pattern_type="jurisdictional_split",
                description="Courts are split on treatment of this case",
                frequency=len(signal_counts),
                examples=[f"{signal.value}: {count}" for signal, count in signal_counts.items()],
                significance=0.7
            ))
        
        # Pattern 3: Evolving treatment
        if len(contexts) >= 5:
            # Sort by some date criterion (would need actual dates)
            recent_contexts = contexts[-3:]  # Last 3 treatments
            older_contexts = contexts[:-3]   # Earlier treatments
            
            recent_sentiment = sum(c.sentiment_score for c in recent_contexts) / len(recent_contexts)
            older_sentiment = sum(c.sentiment_score for c in older_contexts) / len(older_contexts)
            
            if abs(recent_sentiment - older_sentiment) > 0.5:
                trend = "improving" if recent_sentiment > older_sentiment else "declining"
                patterns.append(TreatmentPattern(
                    pattern_type="evolving_treatment",
                    description=f"Treatment appears to be {trend} over time",
                    frequency=len(contexts),
                    examples=[f"Recent sentiment: {recent_sentiment:.2f}, Earlier: {older_sentiment:.2f}"],
                    significance=0.6
                ))
        
        # Pattern 4: Deep analysis pattern
        deep_contexts = [c for c in contexts if c.treatment_depth == TreatmentDepth.COMPREHENSIVE]
        if len(deep_contexts) >= 2:
            patterns.append(TreatmentPattern(
                pattern_type="thorough_analysis",
                description=f"Case receives comprehensive analysis in {len(deep_contexts)} decisions",
                frequency=len(deep_contexts),
                examples=[c.legal_reasoning[:100] if c.legal_reasoning else "Detailed discussion" for c in deep_contexts[:2]],
                significance=0.5
            ))
        
        return patterns
    
    async def _analyze_jurisdictional_treatment(self, citing_cases: List[CitingCase]) -> List[JurisdictionalTreatment]:
        """Analyze treatment by jurisdiction."""
        jurisdiction_data = {}
        
        for case in citing_cases:
            key = (case.jurisdiction, case.court)
            if key not in jurisdiction_data:
                jurisdiction_data[key] = {
                    'cases': [],
                    'signals': []
                }
            
            jurisdiction_data[key]['cases'].append(case)
            jurisdiction_data[key]['signals'].append(case.treatment_signal)
        
        jurisdictional_analyses = []
        
        for (jurisdiction, court), data in jurisdiction_data.items():
            cases = data['cases']
            signals = data['signals']
            
            # Count signal types
            signal_counts = {}
            for signal in signals:
                signal_counts[signal] = signal_counts.get(signal, 0) + 1
            
            # Categorize signals
            positive_signals = [TreatmentSignal.FOLLOWED, TreatmentSignal.AFFIRMED, TreatmentSignal.CITED]
            negative_signals = [TreatmentSignal.OVERRULED, TreatmentSignal.QUESTIONED, TreatmentSignal.CRITICIZED]
            
            positive_count = sum(signal_counts.get(s, 0) for s in positive_signals)
            negative_count = sum(signal_counts.get(s, 0) for s in negative_signals)
            neutral_count = len(signals) - positive_count - negative_count
            
            # Determine dominant signal
            dominant_signal = max(signal_counts.keys(), key=lambda x: signal_counts[x]) if signal_counts else TreatmentSignal.NEUTRAL
            
            # Calculate consistency (entropy-based)
            total = len(signals)
            consistency = 0.0
            if total > 0:
                entropy = 0.0
                for count in signal_counts.values():
                    if count > 0:
                        p = count / total
                        entropy -= p * np.log2(p) if p > 0 else 0
                consistency = max(0.0, 1.0 - entropy / 2.0)  # Normalize
            
            # Calculate authority weight based on court level
            authority_weight = self.court_weights.get(court, 0.5)
            
            analysis = JurisdictionalTreatment(
                jurisdiction=jurisdiction,
                court_level=court,
                total_citations=len(cases),
                positive_citations=positive_count,
                negative_citations=negative_count,
                neutral_citations=neutral_count,
                dominant_signal=dominant_signal,
                treatment_consistency=consistency,
                authority_weight=authority_weight
            )
            
            jurisdictional_analyses.append(analysis)
        
        # Sort by authority weight and total citations
        jurisdictional_analyses.sort(
            key=lambda x: (x.authority_weight, x.total_citations),
            reverse=True
        )
        
        return jurisdictional_analyses
    
    async def _analyze_temporal_treatment(self, citing_cases: List[CitingCase]) -> List[TemporalTreatment]:
        """Analyze treatment over time."""
        if not citing_cases:
            return []
        
        # Sort cases by date
        sorted_cases = sorted(citing_cases, key=lambda x: x.decision_date)
        
        # Define time periods (yearly buckets)
        earliest_date = sorted_cases[0].decision_date
        latest_date = sorted_cases[-1].decision_date
        
        temporal_analyses = []
        current_year = earliest_date.year
        
        while current_year <= latest_date.year:
            # Get cases for this year
            year_cases = [
                case for case in sorted_cases
                if case.decision_date.year == current_year
            ]
            
            if not year_cases:
                current_year += 1
                continue
            
            # Analyze signals for this period
            signal_distribution = {}
            for case in year_cases:
                signal = case.treatment_signal
                signal_distribution[signal] = signal_distribution.get(signal, 0) + 1
            
            # Determine trend (simplified - would be more sophisticated in practice)
            trend = "stable"  # Default
            if current_year > earliest_date.year:
                # Compare with previous period
                prev_year_cases = [
                    case for case in sorted_cases
                    if case.decision_date.year == current_year - 1
                ]
                
                if prev_year_cases:
                    # Simple sentiment comparison
                    current_sentiment = self._calculate_period_sentiment(year_cases)
                    prev_sentiment = self._calculate_period_sentiment(prev_year_cases)
                    
                    if current_sentiment > prev_sentiment + 0.2:
                        trend = "improving"
                    elif current_sentiment < prev_sentiment - 0.2:
                        trend = "declining"
            
            analysis = TemporalTreatment(
                time_period=str(current_year),
                start_date=datetime(current_year, 1, 1),
                end_date=datetime(current_year, 12, 31),
                citation_count=len(year_cases),
                treatment_trend=trend,
                signal_distribution=signal_distribution
            )
            
            temporal_analyses.append(analysis)
            current_year += 1
        
        return temporal_analyses
    
    def _calculate_period_sentiment(self, cases: List[CitingCase]) -> float:
        """Calculate average sentiment for a period."""
        if not cases:
            return 0.0
        
        # Simple sentiment based on treatment signals
        signal_weights = {
            TreatmentSignal.OVERRULED: -1.0,
            TreatmentSignal.QUESTIONED: -0.7,
            TreatmentSignal.CRITICIZED: -0.5,
            TreatmentSignal.FOLLOWED: 0.8,
            TreatmentSignal.AFFIRMED: 1.0,
            TreatmentSignal.CITED: 0.5,
            TreatmentSignal.NEUTRAL: 0.0
        }
        
        total_sentiment = sum(signal_weights.get(case.treatment_signal, 0.0) for case in cases)
        return total_sentiment / len(cases)
    
    async def _calculate_overall_treatment(self, contexts: List[TreatmentContext]) -> Tuple[TreatmentSignal, float]:
        """Calculate overall treatment signal and confidence."""
        if not contexts:
            return TreatmentSignal.NEUTRAL, 0.0
        
        # Weight signals by confidence and depth
        signal_weights = {}
        total_weight = 0.0
        
        for context in contexts:
            signal = context.treatment_signal
            
            # Base weight from confidence
            weight = context.confidence_score
            
            # Boost weight for deeper treatment
            depth_multiplier = {
                TreatmentDepth.SURFACE: 1.0,
                TreatmentDepth.SUBSTANTIVE: 1.5,
                TreatmentDepth.COMPREHENSIVE: 2.0
            }
            weight *= depth_multiplier.get(context.treatment_depth, 1.0)
            
            # Boost weight for higher reliability
            reliability_multiplier = {
                TreatmentReliability.UNCERTAIN: 0.5,
                TreatmentReliability.LOW: 0.8,
                TreatmentReliability.MEDIUM: 1.0,
                TreatmentReliability.HIGH: 1.2
            }
            weight *= reliability_multiplier.get(context.reliability, 1.0)
            
            if signal in signal_weights:
                signal_weights[signal] += weight
            else:
                signal_weights[signal] = weight
            
            total_weight += weight
        
        # Select signal with highest weighted score
        if signal_weights:
            best_signal = max(signal_weights.keys(), key=lambda x: signal_weights[x])
            confidence = min(1.0, signal_weights[best_signal] / total_weight)
            return best_signal, confidence
        
        return TreatmentSignal.NEUTRAL, 0.0
    
    async def _calculate_treatment_consensus(self, contexts: List[TreatmentContext]) -> float:
        """Calculate how much consensus exists on treatment."""
        if len(contexts) <= 1:
            return 1.0
        
        # Calculate entropy of treatment signals
        signal_counts = {}
        for context in contexts:
            signal = context.treatment_signal
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
        
        total = len(contexts)
        entropy = 0.0
        
        for count in signal_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * np.log2(p)
        
        # Normalize entropy to 0-1 scale (higher = more consensus)
        max_entropy = np.log2(len(signal_counts)) if len(signal_counts) > 1 else 1
        consensus = max(0.0, 1.0 - entropy / max_entropy)
        
        return consensus
    
    async def _generate_key_insights(self, 
                                   contexts: List[TreatmentContext], 
                                   patterns: List[TreatmentPattern]) -> List[str]:
        """Generate key insights from treatment analysis."""
        insights = []
        
        if not contexts:
            return insights
        
        # Insight about treatment volume
        if len(contexts) > 10:
            insights.append(f"📊 Frequently cited case with {len(contexts)} treatment instances")
        elif len(contexts) < 3:
            insights.append(f"📊 Limited citation history with only {len(contexts)} treatment instances")
        
        # Insight about treatment depth
        deep_treatments = [c for c in contexts if c.treatment_depth == TreatmentDepth.COMPREHENSIVE]
        if deep_treatments:
            insights.append(f"🔍 Receives comprehensive analysis in {len(deep_treatments)} cases")
        
        # Insight about reliability
        high_reliability = [c for c in contexts if c.reliability == TreatmentReliability.HIGH]
        if len(high_reliability) / len(contexts) > 0.7:
            insights.append("✅ Treatment assessments are generally reliable and clear")
        elif len(high_reliability) / len(contexts) < 0.3:
            insights.append("⚠️ Many treatment assessments are uncertain or unclear")
        
        # Insights from patterns
        for pattern in patterns:
            if pattern.significance > 0.6:
                insights.append(f"🔍 {pattern.description}")
        
        # Sentiment insights
        avg_sentiment = sum(c.sentiment_score for c in contexts) / len(contexts)
        if avg_sentiment > 0.3:
            insights.append("😊 Generally positive treatment by citing courts")
        elif avg_sentiment < -0.3:
            insights.append("😟 Generally negative treatment by citing courts")
        
        return insights
    
    async def _generate_warnings(self, 
                               contexts: List[TreatmentContext], 
                               overall_treatment: TreatmentSignal) -> List[str]:
        """Generate warnings based on treatment analysis."""
        warnings = []
        
        # Critical treatment warnings
        critical_signals = [TreatmentSignal.OVERRULED, TreatmentSignal.REVERSED, TreatmentSignal.SUPERSEDED]
        if overall_treatment in critical_signals:
            warnings.append(f"🚨 CRITICAL: Case has been {overall_treatment.value}")
        
        # Multiple negative treatments
        negative_contexts = [
            c for c in contexts 
            if c.treatment_signal in [TreatmentSignal.QUESTIONED, TreatmentSignal.CRITICIZED]
        ]
        if len(negative_contexts) >= 3:
            warnings.append(f"⚠️ Multiple courts have questioned or criticized this case ({len(negative_contexts)} instances)")
        
        # Low reliability warning
        uncertain_contexts = [c for c in contexts if c.reliability == TreatmentReliability.UNCERTAIN]
        if len(uncertain_contexts) / len(contexts) > 0.5:
            warnings.append("⚠️ Treatment analysis has high uncertainty - exercise caution")
        
        # Recent negative treatment
        # Note: Would need actual dates to implement properly
        recent_negative = [
            c for c in contexts[-3:] 
            if c.treatment_signal in [TreatmentSignal.QUESTIONED, TreatmentSignal.CRITICIZED, TreatmentSignal.OVERRULED]
        ]
        if recent_negative:
            warnings.append("📅 Recent negative treatment detected")
        
        return warnings
    
    async def _generate_recommendations(self, 
                                      contexts: List[TreatmentContext], 
                                      patterns: List[TreatmentPattern]) -> List[str]:
        """Generate recommendations based on treatment analysis."""
        recommendations = []
        
        if not contexts:
            recommendations.append("🔍 Insufficient citation data - verify case status independently")
            return recommendations
        
        # Recommendations based on overall treatment
        positive_contexts = [
            c for c in contexts 
            if c.treatment_signal in [TreatmentSignal.FOLLOWED, TreatmentSignal.AFFIRMED, TreatmentSignal.CITED]
        ]
        
        if len(positive_contexts) / len(contexts) > 0.7:
            recommendations.append("✅ Strong authority - safe to rely on this case")
        elif len(positive_contexts) / len(contexts) > 0.4:
            recommendations.append("⚖️ Generally reliable authority - consider supporting authorities")
        else:
            recommendations.append("⚠️ Use with caution - seek additional supporting authorities")
        
        # Recommendations based on patterns
        jurisdictional_split = any(p.pattern_type == "jurisdictional_split" for p in patterns)
        if jurisdictional_split:
            recommendations.append("🗺️ Jurisdictional split detected - check treatment in your jurisdiction")
        
        evolving_treatment = any(p.pattern_type == "evolving_treatment" for p in patterns)
        if evolving_treatment:
            recommendations.append("📈 Treatment is evolving - check most recent citations")
        
        # Recommendations based on treatment depth
        comprehensive_treatments = [c for c in contexts if c.treatment_depth == TreatmentDepth.COMPREHENSIVE]
        if comprehensive_treatments:
            recommendations.append(f"📚 Review comprehensive analyses in {len(comprehensive_treatments)} cases for detailed insights")
        
        return recommendations


# Helper functions
async def analyze_case_treatment(case_document: UnifiedDocument, citing_cases: List[CitingCase]) -> TreatmentAnalysis:
    """Helper function to analyze case treatment."""
    analyzer = CaseTreatmentAnalyzer()
    return await analyzer.analyze_case_treatment(case_document, citing_cases)

async def quick_treatment_summary(citing_cases: List[CitingCase]) -> Dict[str, Any]:
    """Quick summary of case treatment."""
    if not citing_cases:
        return {"error": "No citing cases provided"}
    
    signal_counts = {}
    for case in citing_cases:
        signal = case.treatment_signal
        signal_counts[signal] = signal_counts.get(signal, 0) + 1
    
    total = len(citing_cases)
    positive_signals = [TreatmentSignal.FOLLOWED, TreatmentSignal.AFFIRMED, TreatmentSignal.CITED]
    negative_signals = [TreatmentSignal.OVERRULED, TreatmentSignal.QUESTIONED, TreatmentSignal.CRITICIZED]
    
    positive_count = sum(signal_counts.get(s, 0) for s in positive_signals)
    negative_count = sum(signal_counts.get(s, 0) for s in negative_signals)
    
    return {
        "total_citations": total,
        "positive_treatment": positive_count,
        "negative_treatment": negative_count,
        "neutral_treatment": total - positive_count - negative_count,
        "dominant_signal": max(signal_counts.keys(), key=lambda x: signal_counts[x]).value,
        "signal_distribution": {k.value: v for k, v in signal_counts.items()}
    }