"""
Case Analysis and Strategy Module

AI-powered case analysis, legal strategy generation, and strategic insights
for comprehensive trial preparation.
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
import json
import re
from abc import ABC, abstractmethod

import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from textblob import TextBlob
import networkx as nx

logger = logging.getLogger(__name__)


class CaseType(Enum):
    """Types of legal cases."""
    CIVIL_LITIGATION = "civil_litigation"
    CRIMINAL_DEFENSE = "criminal_defense"
    CRIMINAL_PROSECUTION = "criminal_prosecution"
    PERSONAL_INJURY = "personal_injury"
    CONTRACT_DISPUTE = "contract_dispute"
    EMPLOYMENT_LAW = "employment_law"
    FAMILY_LAW = "family_law"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    REAL_ESTATE = "real_estate"
    CORPORATE_LAW = "corporate_law"
    BANKRUPTCY = "bankruptcy"
    TAX_LAW = "tax_law"
    IMMIGRATION = "immigration"
    ADMINISTRATIVE_LAW = "administrative_law"


class CaseStrength(Enum):
    """Assessment of case strength."""
    VERY_STRONG = "very_strong"      # 80-100%
    STRONG = "strong"                # 60-80%
    MODERATE = "moderate"            # 40-60%
    WEAK = "weak"                   # 20-40%
    VERY_WEAK = "very_weak"         # 0-20%


class StrategyType(Enum):
    """Types of legal strategies."""
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"
    SETTLEMENT_FOCUSED = "settlement_focused"
    DISCOVERY_INTENSIVE = "discovery_intensive"
    MOTION_BASED = "motion_based"
    COLLABORATIVE = "collaborative"
    PRECEDENT_BASED = "precedent_based"


class RiskLevel(Enum):
    """Risk assessment levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class LegalIssue:
    """Represents a legal issue in the case."""
    issue_id: str
    title: str
    description: str
    legal_basis: List[str]  # Statutes, regulations, case law
    elements_required: List[str]
    evidence_needed: List[str]
    precedents: List[str] = field(default_factory=list)
    strength_assessment: CaseStrength = CaseStrength.MODERATE
    complexity_score: float = 0.5  # 0-1 scale
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'issue_id': self.issue_id,
            'title': self.title,
            'description': self.description,
            'legal_basis': self.legal_basis,
            'elements_required': self.elements_required,
            'evidence_needed': self.evidence_needed,
            'precedents': self.precedents,
            'strength_assessment': self.strength_assessment.value,
            'complexity_score': self.complexity_score
        }


@dataclass
class StrategicInsight:
    """Strategic insight or recommendation."""
    insight_id: str
    category: str  # "strength", "weakness", "opportunity", "threat", "recommendation"
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    confidence: float  # 0-1 scale
    impact_assessment: str
    recommended_actions: List[str] = field(default_factory=list)
    supporting_analysis: Optional[str] = None
    deadline: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'insight_id': self.insight_id,
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'confidence': self.confidence,
            'impact_assessment': self.impact_assessment,
            'recommended_actions': self.recommended_actions,
            'supporting_analysis': self.supporting_analysis,
            'deadline': self.deadline.isoformat() if self.deadline else None
        }


@dataclass
class CaseAnalysis:
    """Comprehensive case analysis results."""
    analysis_id: str
    case_id: str
    case_type: CaseType
    overall_strength: CaseStrength
    confidence_score: float  # Overall confidence in assessment
    
    # Core analysis components
    legal_issues: List[LegalIssue]
    strategic_insights: List[StrategicInsight]
    
    # SWOT Analysis
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    
    # Recommendations
    recommended_strategy: StrategyType
    key_actions: List[str]
    timeline_recommendations: List[str]
    resource_requirements: List[str]
    
    # Risk assessment
    overall_risk_level: RiskLevel
    risk_factors: List[Dict[str, Any]]
    mitigation_strategies: List[str]
    
    # Metadata
    analyzed_at: datetime = field(default_factory=datetime.now)
    analysis_method: str = "comprehensive_ai"
    documents_analyzed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'analysis_id': self.analysis_id,
            'case_id': self.case_id,
            'case_type': self.case_type.value,
            'overall_strength': self.overall_strength.value,
            'confidence_score': self.confidence_score,
            'legal_issues': [issue.to_dict() for issue in self.legal_issues],
            'strategic_insights': [insight.to_dict() for insight in self.strategic_insights],
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'opportunities': self.opportunities,
            'threats': self.threats,
            'recommended_strategy': self.recommended_strategy.value,
            'key_actions': self.key_actions,
            'timeline_recommendations': self.timeline_recommendations,
            'resource_requirements': self.resource_requirements,
            'overall_risk_level': self.overall_risk_level.value,
            'risk_factors': self.risk_factors,
            'mitigation_strategies': self.mitigation_strategies,
            'analyzed_at': self.analyzed_at.isoformat(),
            'analysis_method': self.analysis_method,
            'documents_analyzed': self.documents_analyzed
        }


class LegalAnalyzer:
    """AI-powered legal document and case analyzer."""
    
    def __init__(self):
        # Load NLP model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Using fallback methods.")
            self.nlp = None
        
        # Legal concept extractors
        self.legal_concepts = self._load_legal_concepts()
        self.case_law_patterns = self._load_case_law_patterns()
        self.statute_patterns = self._load_statute_patterns()
        
        # ML models for classification
        self.case_type_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.strength_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        
        # Analysis components
        self.is_trained = False
    
    def _load_legal_concepts(self) -> Dict[str, List[str]]:
        """Load legal concepts and keywords for analysis."""
        return {
            'contract_law': [
                'breach', 'consideration', 'offer', 'acceptance', 'damages',
                'specific performance', 'liquidated damages', 'material breach',
                'substantial performance', 'frustration', 'impossibility'
            ],
            'tort_law': [
                'negligence', 'duty of care', 'breach of duty', 'causation',
                'damages', 'strict liability', 'intentional tort', 'defamation',
                'false imprisonment', 'assault', 'battery', 'trespass'
            ],
            'criminal_law': [
                'mens rea', 'actus reus', 'intent', 'malice', 'premeditation',
                'self-defense', 'duress', 'entrapment', 'miranda', 'search warrant',
                'probable cause', 'reasonable doubt', 'burden of proof'
            ],
            'constitutional_law': [
                'due process', 'equal protection', 'first amendment', 'fourth amendment',
                'commerce clause', 'supremacy clause', 'substantive due process',
                'procedural due process', 'strict scrutiny', 'intermediate scrutiny'
            ],
            'evidence_law': [
                'hearsay', 'relevance', 'prejudicial', 'authentication', 'best evidence',
                'privilege', 'attorney-client', 'work product', 'expert witness',
                'lay witness', 'impeachment', 'rehabilitation'
            ]
        }
    
    def _load_case_law_patterns(self) -> List[str]:
        """Load patterns for identifying case law citations."""
        return [
            r'\d+\s+[A-Z][a-z]+\.?\s*\d+d?\s+\d+',  # Federal reporters
            r'\d+\s+U\.S\.?\s+\d+',  # Supreme Court
            r'\d+\s+F\.?\s*\d*d?\s+\d+',  # Federal courts
            r'\d+\s+[A-Z][a-z]+\.?\s*\d*d?\s+\d+',  # State reporters
            r'[A-Z][a-zA-Z\s]+v\.?\s+[A-Z][a-zA-Z\s]+,?\s*\d+',  # Case names
        ]
    
    def _load_statute_patterns(self) -> List[str]:
        """Load patterns for identifying statutory citations."""
        return [
            r'\d+\s+U\.S\.C\.?\s+§?\s*\d+',  # USC
            r'\d+\s+C\.F\.R\.?\s+§?\s*\d+',  # CFR
            r'[A-Z][a-z]+\.?\s+Code\s+§?\s*\d+',  # State codes
            r'§\s*\d+[\.\d]*',  # Section references
        ]
    
    async def analyze_document(self, text: str, document_type: str = "pleading") -> Dict[str, Any]:
        """Analyze a single legal document."""
        analysis = {
            'document_type': document_type,
            'word_count': len(text.split()),
            'legal_concepts': {},
            'citations': {},
            'key_entities': [],
            'sentiment': {},
            'complexity_metrics': {}
        }
        
        # Extract legal concepts
        for concept_area, keywords in self.legal_concepts.items():
            concept_count = sum(1 for keyword in keywords if keyword.lower() in text.lower())
            if concept_count > 0:
                analysis['legal_concepts'][concept_area] = concept_count
        
        # Extract citations
        analysis['citations']['case_law'] = self._extract_case_citations(text)
        analysis['citations']['statutes'] = self._extract_statute_citations(text)
        
        # Named entity recognition
        if self.nlp:
            doc = self.nlp(text)
            analysis['key_entities'] = [
                {'text': ent.text, 'label': ent.label_, 'description': spacy.explain(ent.label_)}
                for ent in doc.ents
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'DATE', 'MONEY', 'LAW']
            ]
        
        # Sentiment analysis
        blob = TextBlob(text)
        analysis['sentiment'] = {
            'polarity': blob.sentiment.polarity,  # -1 to 1
            'subjectivity': blob.sentiment.subjectivity  # 0 to 1
        }
        
        # Complexity metrics
        sentences = text.split('.')
        words = text.split()
        analysis['complexity_metrics'] = {
            'sentence_count': len(sentences),
            'average_sentence_length': len(words) / max(len(sentences), 1),
            'unique_word_ratio': len(set(words)) / max(len(words), 1),
            'legal_density': sum(analysis['legal_concepts'].values()) / max(len(words), 1) * 1000
        }
        
        return analysis
    
    def _extract_case_citations(self, text: str) -> List[str]:
        """Extract case law citations from text."""
        citations = []
        for pattern in self.case_law_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations.extend(matches)
        return list(set(citations))  # Remove duplicates
    
    def _extract_statute_citations(self, text: str) -> List[str]:
        """Extract statutory citations from text."""
        citations = []
        for pattern in self.statute_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations.extend(matches)
        return list(set(citations))  # Remove duplicates
    
    async def identify_legal_issues(self, document_analyses: List[Dict[str, Any]]) -> List[LegalIssue]:
        """Identify key legal issues from document analyses."""
        issues = []
        
        # Aggregate legal concepts across all documents
        concept_aggregation = {}
        all_citations = {'case_law': [], 'statutes': []}
        
        for analysis in document_analyses:
            # Aggregate legal concepts
            for concept_area, count in analysis.get('legal_concepts', {}).items():
                concept_aggregation[concept_area] = concept_aggregation.get(concept_area, 0) + count
            
            # Aggregate citations
            citations = analysis.get('citations', {})
            all_citations['case_law'].extend(citations.get('case_law', []))
            all_citations['statutes'].extend(citations.get('statutes', []))
        
        # Create legal issues based on prominent concepts
        issue_id_counter = 1
        for concept_area, total_count in concept_aggregation.items():
            if total_count >= 3:  # Threshold for significance
                issue = LegalIssue(
                    issue_id=f"issue_{issue_id_counter:03d}",
                    title=self._generate_issue_title(concept_area),
                    description=self._generate_issue_description(concept_area, total_count),
                    legal_basis=list(set(all_citations['statutes'][:5])),  # Top 5 statutes
                    elements_required=self._get_elements_for_concept(concept_area),
                    evidence_needed=self._get_evidence_for_concept(concept_area),
                    precedents=list(set(all_citations['case_law'][:3])),  # Top 3 cases
                    strength_assessment=self._assess_issue_strength(concept_area, total_count),
                    complexity_score=min(total_count / 10.0, 1.0)  # Normalize to 0-1
                )
                issues.append(issue)
                issue_id_counter += 1
        
        return issues
    
    def _generate_issue_title(self, concept_area: str) -> str:
        """Generate a title for a legal issue."""
        title_map = {
            'contract_law': 'Breach of Contract Claims',
            'tort_law': 'Tort Liability Issues',
            'criminal_law': 'Criminal Charges and Defenses',
            'constitutional_law': 'Constitutional Violations',
            'evidence_law': 'Evidentiary Issues and Admissibility'
        }
        return title_map.get(concept_area, f"{concept_area.replace('_', ' ').title()} Issues")
    
    def _generate_issue_description(self, concept_area: str, count: int) -> str:
        """Generate a description for a legal issue."""
        return f"Analysis of case documents reveals {count} references to {concept_area.replace('_', ' ')} concepts, indicating this is a significant issue in the case."
    
    def _get_elements_for_concept(self, concept_area: str) -> List[str]:
        """Get required elements for proving a legal concept."""
        element_map = {
            'contract_law': ['Valid Contract Formation', 'Performance by Plaintiff', 'Breach by Defendant', 'Damages'],
            'tort_law': ['Duty of Care', 'Breach of Duty', 'Causation', 'Damages'],
            'criminal_law': ['Actus Reus', 'Mens Rea', 'Causation', 'Lack of Defenses'],
            'constitutional_law': ['State Action', 'Fundamental Right or Suspect Class', 'Government Interest'],
            'evidence_law': ['Relevance', 'Authentication', 'Not Hearsay or Exception Applies', 'Not Prejudicial']
        }
        return element_map.get(concept_area, ['Element 1', 'Element 2', 'Element 3'])
    
    def _get_evidence_for_concept(self, concept_area: str) -> List[str]:
        """Get types of evidence needed for a legal concept."""
        evidence_map = {
            'contract_law': ['Contract Documents', 'Communication Records', 'Performance Evidence', 'Damages Calculation'],
            'tort_law': ['Medical Records', 'Accident Reports', 'Expert Testimony', 'Witness Statements'],
            'criminal_law': ['Physical Evidence', 'Witness Testimony', 'Documentation', 'Expert Analysis'],
            'constitutional_law': ['Government Actions', 'Policy Documents', 'Statistical Evidence', 'Expert Testimony'],
            'evidence_law': ['Foundation Documents', 'Chain of Custody', 'Expert Qualifications', 'Authentication Records']
        }
        return evidence_map.get(concept_area, ['Documentary Evidence', 'Witness Testimony', 'Expert Opinion'])
    
    def _assess_issue_strength(self, concept_area: str, count: int) -> CaseStrength:
        """Assess the strength of a legal issue based on frequency and type."""
        # Simple heuristic - more sophisticated analysis would consider document types, context, etc.
        if count >= 10:
            return CaseStrength.STRONG
        elif count >= 7:
            return CaseStrength.MODERATE
        elif count >= 5:
            return CaseStrength.MODERATE
        else:
            return CaseStrength.WEAK


class StrategicAnalyzer:
    """Analyzes case strategy and provides strategic insights."""
    
    def __init__(self):
        self.strategy_rules = self._load_strategy_rules()
        self.risk_assessor = RiskAssessment()
    
    def _load_strategy_rules(self) -> Dict[str, Any]:
        """Load strategic analysis rules."""
        return {
            'settlement_indicators': [
                'high litigation costs',
                'uncertain outcome',
                'time pressure',
                'relationship preservation',
                'precedent concerns'
            ],
            'aggressive_indicators': [
                'strong evidence',
                'clear liability',
                'significant damages',
                'deterrent effect',
                'principle at stake'
            ],
            'discovery_intensive_indicators': [
                'document heavy case',
                'complex facts',
                'hidden information',
                'expert testimony needed',
                'electronic evidence'
            ]
        }
    
    async def generate_strategic_insights(self, case_analysis: Dict[str, Any], 
                                        legal_issues: List[LegalIssue]) -> List[StrategicInsight]:
        """Generate strategic insights based on case analysis."""
        insights = []
        insight_id_counter = 1
        
        # Analyze strengths
        strength_insights = await self._analyze_strengths(case_analysis, legal_issues)
        for insight in strength_insights:
            insight.insight_id = f"insight_{insight_id_counter:03d}"
            insights.append(insight)
            insight_id_counter += 1
        
        # Analyze weaknesses
        weakness_insights = await self._analyze_weaknesses(case_analysis, legal_issues)
        for insight in weakness_insights:
            insight.insight_id = f"insight_{insight_id_counter:03d}"
            insights.append(insight)
            insight_id_counter += 1
        
        # Generate strategic recommendations
        strategic_recommendations = await self._generate_recommendations(case_analysis, legal_issues)
        for insight in strategic_recommendations:
            insight.insight_id = f"insight_{insight_id_counter:03d}"
            insights.append(insight)
            insight_id_counter += 1
        
        return insights
    
    async def _analyze_strengths(self, case_analysis: Dict[str, Any], 
                               legal_issues: List[LegalIssue]) -> List[StrategicInsight]:
        """Analyze case strengths."""
        insights = []
        
        # Strong legal issues
        strong_issues = [issue for issue in legal_issues 
                        if issue.strength_assessment in [CaseStrength.STRONG, CaseStrength.VERY_STRONG]]
        
        if strong_issues:
            insight = StrategicInsight(
                insight_id="",  # Will be set by caller
                category="strength",
                title="Strong Legal Foundation",
                description=f"Case has {len(strong_issues)} strong legal issues with solid precedent and clear elements.",
                priority="high",
                confidence=0.8,
                impact_assessment="Provides strong foundation for aggressive litigation strategy or favorable settlement.",
                recommended_actions=[
                    "Prioritize discovery around strong issues",
                    "Develop motion strategy to resolve weak issues early",
                    "Use strong issues as leverage in settlement negotiations"
                ],
                supporting_analysis=f"Strong issues: {', '.join([issue.title for issue in strong_issues])}"
            )
            insights.append(insight)
        
        # Good evidence base
        total_citations = sum(len(analysis.get('citations', {}).get(cite_type, [])) 
                             for analysis in case_analysis.get('document_analyses', [])
                             for cite_type in ['case_law', 'statutes'])
        
        if total_citations > 10:
            insight = StrategicInsight(
                insight_id="",
                category="strength",
                title="Comprehensive Legal Research",
                description=f"Extensive legal citations ({total_citations}) indicate thorough legal research and support.",
                priority="medium",
                confidence=0.7,
                impact_assessment="Strong legal foundation for arguments and motions.",
                recommended_actions=[
                    "Organize citations by legal issue",
                    "Identify most persuasive precedents",
                    "Prepare comprehensive legal brief"
                ]
            )
            insights.append(insight)
        
        return insights
    
    async def _analyze_weaknesses(self, case_analysis: Dict[str, Any], 
                                legal_issues: List[LegalIssue]) -> List[StrategicInsight]:
        """Analyze case weaknesses."""
        insights = []
        
        # Weak legal issues
        weak_issues = [issue for issue in legal_issues 
                      if issue.strength_assessment in [CaseStrength.WEAK, CaseStrength.VERY_WEAK]]
        
        if weak_issues:
            insight = StrategicInsight(
                insight_id="",
                category="weakness",
                title="Vulnerable Legal Claims",
                description=f"Case has {len(weak_issues)} weak legal issues that may be difficult to prove.",
                priority="high",
                confidence=0.8,
                impact_assessment="May face dispositive motions or settlement pressure on weak claims.",
                recommended_actions=[
                    "Consider dropping weak claims",
                    "Focus discovery on strengthening weak issues",
                    "Develop alternative theories of liability",
                    "Prepare for motion to dismiss challenges"
                ],
                supporting_analysis=f"Weak issues: {', '.join([issue.title for issue in weak_issues])}"
            )
            insights.append(insight)
        
        # Evidence gaps
        missing_evidence = []
        for issue in legal_issues:
            if len(issue.evidence_needed) > 3:  # Many evidence types needed
                missing_evidence.append(issue.title)
        
        if missing_evidence:
            insight = StrategicInsight(
                insight_id="",
                category="weakness",
                title="Evidence Development Needed",
                description=f"Multiple issues require significant evidence development: {len(missing_evidence)} issues.",
                priority="medium",
                confidence=0.7,
                impact_assessment="May increase discovery costs and time to trial.",
                recommended_actions=[
                    "Prioritize evidence collection",
                    "Identify expert witnesses needed",
                    "Plan comprehensive discovery strategy",
                    "Budget for evidence development costs"
                ]
            )
            insights.append(insight)
        
        return insights
    
    async def _generate_recommendations(self, case_analysis: Dict[str, Any], 
                                      legal_issues: List[LegalIssue]) -> List[StrategicInsight]:
        """Generate strategic recommendations."""
        insights = []
        
        # Settlement analysis
        settlement_score = self._calculate_settlement_score(case_analysis, legal_issues)
        if settlement_score > 0.6:
            insight = StrategicInsight(
                insight_id="",
                category="recommendation",
                title="Consider Settlement Strategy",
                description=f"Case characteristics suggest settlement may be favorable (score: {settlement_score:.2f}).",
                priority="high",
                confidence=0.7,
                impact_assessment="Early settlement could reduce costs and risks while achieving reasonable outcome.",
                recommended_actions=[
                    "Conduct settlement value analysis",
                    "Identify settlement negotiation points",
                    "Consider mediation or direct negotiation",
                    "Evaluate timing for settlement discussions"
                ]
            )
            insights.append(insight)
        
        # Motion strategy
        if len([i for i in legal_issues if i.strength_assessment == CaseStrength.STRONG]) > 1:
            insight = StrategicInsight(
                insight_id="",
                category="recommendation",
                title="Aggressive Motion Practice",
                description="Strong legal positions support aggressive motion practice to resolve case favorably.",
                priority="medium",
                confidence=0.8,
                impact_assessment="Could achieve early resolution or significantly narrow issues for trial.",
                recommended_actions=[
                    "File motion for summary judgment",
                    "Consider dispositive motions on strong issues",
                    "Plan motion schedule strategically",
                    "Prepare for motion hearings and oral argument"
                ]
            )
            insights.append(insight)
        
        return insights
    
    def _calculate_settlement_score(self, case_analysis: Dict[str, Any], 
                                  legal_issues: List[LegalIssue]) -> float:
        """Calculate settlement favorability score."""
        score = 0.0
        factors = 0
        
        # Weak issues favor settlement
        weak_issues = sum(1 for issue in legal_issues 
                         if issue.strength_assessment in [CaseStrength.WEAK, CaseStrength.VERY_WEAK])
        if legal_issues:
            score += (weak_issues / len(legal_issues)) * 0.3
            factors += 1
        
        # High complexity favors settlement
        avg_complexity = sum(issue.complexity_score for issue in legal_issues) / max(len(legal_issues), 1)
        score += avg_complexity * 0.2
        factors += 1
        
        # Many evidence requirements favor settlement
        total_evidence_needed = sum(len(issue.evidence_needed) for issue in legal_issues)
        if legal_issues:
            evidence_complexity = min(total_evidence_needed / (len(legal_issues) * 3), 1.0)
            score += evidence_complexity * 0.3
            factors += 1
        
        # Time pressure (simplified)
        score += 0.2  # Base time pressure assumption
        factors += 1
        
        return score / max(factors, 1)


class RiskAssessment:
    """Assesses litigation risks and provides mitigation strategies."""
    
    def __init__(self):
        self.risk_factors = self._initialize_risk_factors()
    
    def _initialize_risk_factors(self) -> Dict[str, Dict[str, Any]]:
        """Initialize risk assessment factors."""
        return {
            'legal_risk': {
                'weak_claims': {'weight': 0.3, 'description': 'Claims with weak legal foundation'},
                'adverse_precedent': {'weight': 0.25, 'description': 'Unfavorable case law'},
                'complex_legal_issues': {'weight': 0.2, 'description': 'Highly complex legal questions'},
                'statute_of_limitations': {'weight': 0.25, 'description': 'Potential SOL issues'}
            },
            'factual_risk': {
                'witness_credibility': {'weight': 0.3, 'description': 'Credibility issues with key witnesses'},
                'evidence_gaps': {'weight': 0.25, 'description': 'Missing or insufficient evidence'},
                'fact_disputes': {'weight': 0.25, 'description': 'Material fact disputes'},
                'document_issues': {'weight': 0.2, 'description': 'Document authentication or availability'}
            },
            'procedural_risk': {
                'discovery_challenges': {'weight': 0.3, 'description': 'Difficult or expensive discovery'},
                'motion_vulnerability': {'weight': 0.25, 'description': 'Vulnerability to dispositive motions'},
                'jurisdiction_issues': {'weight': 0.25, 'description': 'Venue or jurisdiction challenges'},
                'procedural_deadlines': {'weight': 0.2, 'description': 'Tight procedural deadlines'}
            },
            'financial_risk': {
                'litigation_costs': {'weight': 0.4, 'description': 'High anticipated litigation costs'},
                'damage_uncertainty': {'weight': 0.3, 'description': 'Uncertain damages calculation'},
                'collectibility': {'weight': 0.3, 'description': 'Defendant collectibility issues'}
            }
        }
    
    async def assess_case_risks(self, legal_issues: List[LegalIssue], 
                               case_context: Dict[str, Any]) -> Tuple[RiskLevel, List[Dict[str, Any]], List[str]]:
        """Assess overall case risks."""
        risk_scores = {}
        risk_details = []
        mitigation_strategies = []
        
        # Assess each risk category
        for category, factors in self.risk_factors.items():
            category_score = await self._assess_risk_category(category, factors, legal_issues, case_context)
            risk_scores[category] = category_score
            
            # Generate risk details
            risk_details.append({
                'category': category,
                'score': category_score,
                'level': self._score_to_risk_level(category_score).value,
                'description': f"{category.replace('_', ' ').title()} assessment"
            })
        
        # Calculate overall risk level
        overall_score = sum(risk_scores.values()) / len(risk_scores)
        overall_risk_level = self._score_to_risk_level(overall_score)
        
        # Generate mitigation strategies
        mitigation_strategies = await self._generate_mitigation_strategies(risk_scores, legal_issues)
        
        return overall_risk_level, risk_details, mitigation_strategies
    
    async def _assess_risk_category(self, category: str, factors: Dict[str, Dict[str, Any]], 
                                   legal_issues: List[LegalIssue], case_context: Dict[str, Any]) -> float:
        """Assess risk for a specific category."""
        if category == 'legal_risk':
            return await self._assess_legal_risk(legal_issues, case_context)
        elif category == 'factual_risk':
            return await self._assess_factual_risk(legal_issues, case_context)
        elif category == 'procedural_risk':
            return await self._assess_procedural_risk(legal_issues, case_context)
        elif category == 'financial_risk':
            return await self._assess_financial_risk(legal_issues, case_context)
        else:
            return 0.5  # Default moderate risk
    
    async def _assess_legal_risk(self, legal_issues: List[LegalIssue], case_context: Dict[str, Any]) -> float:
        """Assess legal risks."""
        if not legal_issues:
            return 0.8  # High risk if no legal issues identified
        
        # Calculate based on issue strengths
        strength_scores = []
        for issue in legal_issues:
            if issue.strength_assessment == CaseStrength.VERY_STRONG:
                strength_scores.append(0.1)
            elif issue.strength_assessment == CaseStrength.STRONG:
                strength_scores.append(0.3)
            elif issue.strength_assessment == CaseStrength.MODERATE:
                strength_scores.append(0.5)
            elif issue.strength_assessment == CaseStrength.WEAK:
                strength_scores.append(0.7)
            else:  # VERY_WEAK
                strength_scores.append(0.9)
        
        avg_risk = sum(strength_scores) / len(strength_scores)
        
        # Adjust for complexity
        avg_complexity = sum(issue.complexity_score for issue in legal_issues) / len(legal_issues)
        complexity_adjustment = avg_complexity * 0.2
        
        return min(avg_risk + complexity_adjustment, 1.0)
    
    async def _assess_factual_risk(self, legal_issues: List[LegalIssue], case_context: Dict[str, Any]) -> float:
        """Assess factual risks."""
        base_risk = 0.5  # Moderate baseline
        
        # Evidence requirements
        total_evidence_needed = sum(len(issue.evidence_needed) for issue in legal_issues)
        if legal_issues:
            evidence_risk = min(total_evidence_needed / (len(legal_issues) * 4), 1.0) * 0.4
            base_risk += evidence_risk
        
        return min(base_risk, 1.0)
    
    async def _assess_procedural_risk(self, legal_issues: List[LegalIssue], case_context: Dict[str, Any]) -> float:
        """Assess procedural risks."""
        # Simplified assessment
        return 0.4  # Moderate-low procedural risk baseline
    
    async def _assess_financial_risk(self, legal_issues: List[LegalIssue], case_context: Dict[str, Any]) -> float:
        """Assess financial risks."""
        # Simplified assessment based on case complexity
        complexity_score = sum(issue.complexity_score for issue in legal_issues) / max(len(legal_issues), 1)
        return min(complexity_score * 0.8, 1.0)
    
    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert risk score to risk level."""
        if score >= 0.8:
            return RiskLevel.CRITICAL
        elif score >= 0.6:
            return RiskLevel.HIGH
        elif score >= 0.4:
            return RiskLevel.MEDIUM
        elif score >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL
    
    async def _generate_mitigation_strategies(self, risk_scores: Dict[str, float], 
                                            legal_issues: List[LegalIssue]) -> List[str]:
        """Generate risk mitigation strategies."""
        strategies = []
        
        # Legal risk mitigation
        if risk_scores.get('legal_risk', 0) > 0.6:
            strategies.extend([
                "Conduct comprehensive legal research on weak issues",
                "Consider seeking expert legal opinions",
                "Develop alternative legal theories",
                "Plan motion strategy to test legal theories early"
            ])
        
        # Factual risk mitigation
        if risk_scores.get('factual_risk', 0) > 0.6:
            strategies.extend([
                "Prioritize evidence collection and preservation",
                "Identify and interview key witnesses early",
                "Consider hiring investigative services",
                "Develop comprehensive discovery plan"
            ])
        
        # Procedural risk mitigation
        if risk_scores.get('procedural_risk', 0) > 0.6:
            strategies.extend([
                "Create detailed procedural calendar",
                "Assign dedicated case management resources",
                "Monitor all deadlines and requirements",
                "Prepare for potential procedural challenges"
            ])
        
        # Financial risk mitigation
        if risk_scores.get('financial_risk', 0) > 0.6:
            strategies.extend([
                "Develop detailed litigation budget",
                "Consider litigation funding options",
                "Evaluate settlement opportunities early",
                "Monitor costs closely throughout case"
            ])
        
        return strategies


class CaseAnalyzer:
    """Main case analyzer that coordinates all analysis components."""
    
    def __init__(self):
        self.legal_analyzer = LegalAnalyzer()
        self.strategic_analyzer = StrategicAnalyzer()
        self.risk_assessor = RiskAssessment()
    
    async def analyze_case(self, case_id: str, documents: List[Dict[str, str]], 
                          case_type: Optional[CaseType] = None,
                          additional_context: Optional[Dict[str, Any]] = None) -> CaseAnalysis:
        """Perform comprehensive case analysis."""
        analysis_start = datetime.now()
        
        # Analyze individual documents
        document_analyses = []
        for doc in documents:
            doc_analysis = await self.legal_analyzer.analyze_document(
                doc['content'], 
                doc.get('type', 'unknown')
            )
            doc_analysis['document_id'] = doc.get('id', f"doc_{len(document_analyses)}")
            document_analyses.append(doc_analysis)
        
        # Identify legal issues
        legal_issues = await self.legal_analyzer.identify_legal_issues(document_analyses)
        
        # Determine case type if not provided
        if case_type is None:
            case_type = await self._classify_case_type(document_analyses)
        
        # Generate strategic insights
        case_analysis_context = {
            'document_analyses': document_analyses,
            'case_type': case_type,
            'additional_context': additional_context or {}
        }
        
        strategic_insights = await self.strategic_analyzer.generate_strategic_insights(
            case_analysis_context, legal_issues
        )
        
        # Assess risks
        overall_risk_level, risk_details, mitigation_strategies = await self.risk_assessor.assess_case_risks(
            legal_issues, case_analysis_context
        )
        
        # Generate SWOT analysis
        swot_analysis = await self._generate_swot_analysis(strategic_insights, legal_issues)
        
        # Determine overall case strength
        overall_strength = await self._assess_overall_strength(legal_issues, strategic_insights)
        
        # Generate recommendations
        recommendations = await self._generate_case_recommendations(
            legal_issues, strategic_insights, overall_risk_level
        )
        
        # Calculate confidence score
        confidence_score = await self._calculate_confidence_score(legal_issues, len(documents))
        
        # Create comprehensive analysis
        analysis = CaseAnalysis(
            analysis_id=f"analysis_{datetime.now().timestamp()}",
            case_id=case_id,
            case_type=case_type,
            overall_strength=overall_strength,
            confidence_score=confidence_score,
            legal_issues=legal_issues,
            strategic_insights=strategic_insights,
            strengths=swot_analysis['strengths'],
            weaknesses=swot_analysis['weaknesses'],
            opportunities=swot_analysis['opportunities'],
            threats=swot_analysis['threats'],
            recommended_strategy=recommendations['strategy'],
            key_actions=recommendations['key_actions'],
            timeline_recommendations=recommendations['timeline'],
            resource_requirements=recommendations['resources'],
            overall_risk_level=overall_risk_level,
            risk_factors=risk_details,
            mitigation_strategies=mitigation_strategies,
            documents_analyzed=len(documents),
            analyzed_at=analysis_start
        )
        
        return analysis
    
    async def _classify_case_type(self, document_analyses: List[Dict[str, Any]]) -> CaseType:
        """Classify case type based on document analysis."""
        # Aggregate legal concepts
        concept_totals = {}
        for analysis in document_analyses:
            for concept, count in analysis.get('legal_concepts', {}).items():
                concept_totals[concept] = concept_totals.get(concept, 0) + count
        
        # Determine dominant concept area
        if concept_totals:
            dominant_concept = max(concept_totals.keys(), key=lambda k: concept_totals[k])
            
            concept_to_case_type = {
                'contract_law': CaseType.CONTRACT_DISPUTE,
                'tort_law': CaseType.PERSONAL_INJURY,
                'criminal_law': CaseType.CRIMINAL_DEFENSE,
                'constitutional_law': CaseType.CIVIL_LITIGATION,
                'evidence_law': CaseType.CIVIL_LITIGATION
            }
            
            return concept_to_case_type.get(dominant_concept, CaseType.CIVIL_LITIGATION)
        
        return CaseType.CIVIL_LITIGATION  # Default
    
    async def _generate_swot_analysis(self, insights: List[StrategicInsight], 
                                    legal_issues: List[LegalIssue]) -> Dict[str, List[str]]:
        """Generate SWOT analysis from insights."""
        swot = {'strengths': [], 'weaknesses': [], 'opportunities': [], 'threats': []}
        
        # Extract from strategic insights
        for insight in insights:
            if insight.category == 'strength':
                swot['strengths'].append(insight.title)
            elif insight.category == 'weakness':
                swot['weaknesses'].append(insight.title)
            elif insight.category == 'opportunity':
                swot['opportunities'].append(insight.title)
            elif insight.category == 'threat':
                swot['threats'].append(insight.title)
        
        # Add from legal issues analysis
        strong_issues = [i for i in legal_issues if i.strength_assessment in [CaseStrength.STRONG, CaseStrength.VERY_STRONG]]
        weak_issues = [i for i in legal_issues if i.strength_assessment in [CaseStrength.WEAK, CaseStrength.VERY_WEAK]]
        
        if strong_issues:
            swot['strengths'].append(f"{len(strong_issues)} strong legal claims")
        if weak_issues:
            swot['weaknesses'].append(f"{len(weak_issues)} weak legal claims")
        
        # Default entries if none found
        if not swot['strengths']:
            swot['strengths'] = ["Case has been filed and is proceeding"]
        if not swot['opportunities']:
            swot['opportunities'] = ["Settlement negotiations", "Motion practice opportunities"]
        if not swot['threats']:
            swot['threats'] = ["Opposing counsel motions", "Discovery costs"]
        
        return swot
    
    async def _assess_overall_strength(self, legal_issues: List[LegalIssue], 
                                     insights: List[StrategicInsight]) -> CaseStrength:
        """Assess overall case strength."""
        if not legal_issues:
            return CaseStrength.WEAK
        
        # Calculate based on issue strengths
        strength_values = {
            CaseStrength.VERY_STRONG: 5,
            CaseStrength.STRONG: 4,
            CaseStrength.MODERATE: 3,
            CaseStrength.WEAK: 2,
            CaseStrength.VERY_WEAK: 1
        }
        
        avg_strength = sum(strength_values[issue.strength_assessment] for issue in legal_issues) / len(legal_issues)
        
        # Adjust based on strategic insights
        strength_insights = len([i for i in insights if i.category == 'strength'])
        weakness_insights = len([i for i in insights if i.category == 'weakness'])
        
        if strength_insights > weakness_insights:
            avg_strength += 0.5
        elif weakness_insights > strength_insights:
            avg_strength -= 0.5
        
        # Convert back to enum
        if avg_strength >= 4.5:
            return CaseStrength.VERY_STRONG
        elif avg_strength >= 3.5:
            return CaseStrength.STRONG
        elif avg_strength >= 2.5:
            return CaseStrength.MODERATE
        elif avg_strength >= 1.5:
            return CaseStrength.WEAK
        else:
            return CaseStrength.VERY_WEAK
    
    async def _generate_case_recommendations(self, legal_issues: List[LegalIssue],
                                           insights: List[StrategicInsight],
                                           risk_level: RiskLevel) -> Dict[str, Any]:
        """Generate comprehensive case recommendations."""
        # Determine strategy based on strength and risk
        strategy = StrategyType.CONSERVATIVE  # Default
        
        strong_issues = len([i for i in legal_issues if i.strength_assessment in [CaseStrength.STRONG, CaseStrength.VERY_STRONG]])
        total_issues = len(legal_issues)
        
        if strong_issues / max(total_issues, 1) > 0.7 and risk_level in [RiskLevel.LOW, RiskLevel.MINIMAL]:
            strategy = StrategyType.AGGRESSIVE
        elif risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            strategy = StrategyType.SETTLEMENT_FOCUSED
        elif total_issues > 5:
            strategy = StrategyType.DISCOVERY_INTENSIVE
        
        # Generate key actions
        key_actions = []
        for insight in insights:
            if insight.category == 'recommendation' and insight.priority == 'high':
                key_actions.extend(insight.recommended_actions[:2])  # Top 2 actions
        
        if not key_actions:
            key_actions = [
                "Complete case assessment and strategy planning",
                "Initiate discovery process",
                "Evaluate settlement opportunities"
            ]
        
        # Timeline recommendations
        timeline = [
            "Complete discovery within 6 months",
            "File dispositive motions by month 8",
            "Attend settlement conference by month 10",
            "Prepare for trial by month 12"
        ]
        
        # Resource requirements
        resources = [
            "Senior litigation attorney",
            "Paralegal for document review",
            "Expert witnesses as needed",
            "Discovery budget allocation"
        ]
        
        if any(issue.complexity_score > 0.7 for issue in legal_issues):
            resources.extend([
                "Subject matter expert consultation",
                "Additional research resources"
            ])
        
        return {
            'strategy': strategy,
            'key_actions': key_actions[:5],  # Top 5 actions
            'timeline': timeline,
            'resources': resources
        }
    
    async def _calculate_confidence_score(self, legal_issues: List[LegalIssue], 
                                        document_count: int) -> float:
        """Calculate confidence score for the analysis."""
        base_confidence = 0.6  # Base confidence
        
        # More documents increase confidence
        doc_confidence = min(document_count / 10.0, 0.3)  # Max 0.3 boost
        
        # More legal issues increase confidence
        issue_confidence = min(len(legal_issues) / 5.0, 0.2)  # Max 0.2 boost
        
        # Strong issues increase confidence
        strong_issues = len([i for i in legal_issues if i.strength_assessment in [CaseStrength.STRONG, CaseStrength.VERY_STRONG]])
        strength_confidence = min(strong_issues / max(len(legal_issues), 1), 0.2)  # Max 0.2 boost
        
        total_confidence = base_confidence + doc_confidence + issue_confidence + strength_confidence
        return min(total_confidence, 1.0)


# Example usage
async def example_case_analysis():
    """Example usage of the case analyzer."""
    
    # Initialize analyzer
    analyzer = CaseAnalyzer()
    
    # Sample case documents
    documents = [
        {
            'id': 'complaint',
            'type': 'pleading',
            'content': '''
            COMPLAINT FOR BREACH OF CONTRACT
            
            Plaintiff ABC Corporation alleges that Defendant XYZ Company breached the 
            Software Development Agreement dated January 15, 2023. The contract required
            Defendant to deliver custom software by June 15, 2023, for consideration of
            $500,000. Despite receiving full payment, Defendant failed to deliver the
            software, causing damages exceeding $1,000,000 in lost business opportunities.
            
            COUNT I: BREACH OF CONTRACT
            The parties entered into a valid contract. Plaintiff performed all obligations
            by making payment in full. Defendant materially breached by failing to deliver
            the software. As a direct result, Plaintiff suffered damages.
            
            WHEREFORE, Plaintiff demands judgment for damages, attorney fees, and costs.
            '''
        },
        {
            'id': 'answer',
            'type': 'pleading', 
            'content': '''
            ANSWER TO COMPLAINT
            
            Defendant XYZ Company admits the parties entered into a Software Development
            Agreement but denies breach. The contract contained technical specifications
            that were impossible to implement as written. Plaintiff's representatives
            repeatedly changed requirements, making performance impossible.
            
            AFFIRMATIVE DEFENSES
            1. Impossibility of performance
            2. Plaintiff's material breach
            3. Frustration of purpose
            4. Waiver and estoppel
            
            COUNTERCLAIM FOR BREACH OF CONTRACT
            Plaintiff breached by failing to provide necessary technical specifications
            and changing requirements repeatedly, causing Defendant to incur additional
            costs of $200,000.
            '''
        },
        {
            'id': 'contract',
            'type': 'contract',
            'content': '''
            SOFTWARE DEVELOPMENT AGREEMENT
            
            This Agreement is between ABC Corporation ("Client") and XYZ Company ("Developer")
            for the development of custom inventory management software.
            
            SCOPE OF WORK: Developer shall create custom software meeting specifications
            in Exhibit A, with delivery by June 15, 2023.
            
            PAYMENT: Client shall pay $500,000 in three installments: $200,000 upon signing,
            $200,000 at 50% completion, and $100,000 upon final delivery.
            
            CHANGES: Any changes to specifications must be agreed to in writing and may
            extend delivery dates and increase costs.
            
            FORCE MAJEURE: Neither party shall be liable for delays caused by circumstances
            beyond their reasonable control.
            '''
        }
    ]
    
    print("Legal Case Analysis System")
    print("=" * 50)
    
    # Perform case analysis
    print("Analyzing case documents...")
    analysis = await analyzer.analyze_case(
        case_id="CASE_ABC_v_XYZ",
        documents=documents,
        case_type=CaseType.CONTRACT_DISPUTE,
        additional_context={
            'client_type': 'corporation',
            'dispute_amount': 1000000,
            'case_age_months': 6
        }
    )
    
    print(f"\nCase Analysis Results")
    print(f"Case Type: {analysis.case_type.value}")
    print(f"Overall Strength: {analysis.overall_strength.value}")
    print(f"Risk Level: {analysis.overall_risk_level.value}")
    print(f"Confidence Score: {analysis.confidence_score:.2f}")
    print(f"Documents Analyzed: {analysis.documents_analyzed}")
    
    print(f"\nLegal Issues ({len(analysis.legal_issues)}):")
    print("-" * 30)
    for issue in analysis.legal_issues:
        print(f"• {issue.title}")
        print(f"  Strength: {issue.strength_assessment.value}")
        print(f"  Complexity: {issue.complexity_score:.2f}")
        print(f"  Elements: {len(issue.elements_required)}")
        print(f"  Evidence Needed: {len(issue.evidence_needed)}")
        print()
    
    print(f"Strategic Insights ({len(analysis.strategic_insights)}):")
    print("-" * 30)
    for insight in analysis.strategic_insights[:5]:  # Top 5
        print(f"• {insight.title} ({insight.category})")
        print(f"  Priority: {insight.priority}")
        print(f"  Confidence: {insight.confidence:.2f}")
        print(f"  Impact: {insight.impact_assessment}")
        print()
    
    print(f"SWOT Analysis:")
    print("-" * 30)
    print(f"Strengths: {', '.join(analysis.strengths[:3])}")
    print(f"Weaknesses: {', '.join(analysis.weaknesses[:3])}")
    print(f"Opportunities: {', '.join(analysis.opportunities[:3])}")
    print(f"Threats: {', '.join(analysis.threats[:3])}")
    
    print(f"\nRecommendations:")
    print(f"Strategy: {analysis.recommended_strategy.value}")
    print(f"Key Actions:")
    for action in analysis.key_actions:
        print(f"  • {action}")
    
    print(f"\nRisk Mitigation:")
    for strategy in analysis.mitigation_strategies[:5]:
        print(f"  • {strategy}")
    
    # Export analysis
    print(f"\nExporting analysis to JSON...")
    analysis_dict = analysis.to_dict()
    with open('case_analysis.json', 'w') as f:
        json.dump(analysis_dict, f, indent=2)
    
    print(f"Analysis complete and saved to case_analysis.json")


if __name__ == "__main__":
    asyncio.run(example_case_analysis())