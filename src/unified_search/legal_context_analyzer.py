"""
Legal Context Analysis Engine

Advanced legal context analysis system that understands legal concepts,
practice areas, procedural contexts, and semantic relationships in legal
documents and queries.
"""

import asyncio
import logging
import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any, NamedTuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum
import json

from .database_models import UnifiedDocument, UnifiedQuery, ContentType, DatabaseProvider

logger = logging.getLogger(__name__)


class LegalContextType(Enum):
    """Types of legal contexts"""
    PRACTICE_AREA = "practice_area"
    PROCEDURAL = "procedural"
    SUBSTANTIVE = "substantive"
    JURISDICTIONAL = "jurisdictional"
    TEMPORAL = "temporal"
    DOCTRINAL = "doctrinal"
    REMEDIAL = "remedial"
    CONSTITUTIONAL = "constitutional"


class LegalConcept(Enum):
    """Legal concepts and doctrines"""
    # Constitutional concepts
    DUE_PROCESS = "due_process"
    EQUAL_PROTECTION = "equal_protection"
    COMMERCE_CLAUSE = "commerce_clause"
    FIRST_AMENDMENT = "first_amendment"
    FOURTH_AMENDMENT = "fourth_amendment"
    SEPARATION_OF_POWERS = "separation_of_powers"
    FEDERALISM = "federalism"
    
    # Contract law concepts
    CONSIDERATION = "consideration"
    BREACH_OF_CONTRACT = "breach_of_contract"
    SPECIFIC_PERFORMANCE = "specific_performance"
    UNCONSCIONABILITY = "unconscionability"
    PAROL_EVIDENCE = "parol_evidence"
    STATUTE_OF_FRAUDS = "statute_of_frauds"
    
    # Tort law concepts
    NEGLIGENCE = "negligence"
    STRICT_LIABILITY = "strict_liability"
    CAUSATION = "causation"
    DAMAGES = "damages"
    DUTY_OF_CARE = "duty_of_care"
    PROXIMATE_CAUSE = "proximate_cause"
    
    # Procedural concepts
    SUMMARY_JUDGMENT = "summary_judgment"
    PERSONAL_JURISDICTION = "personal_jurisdiction"
    SUBJECT_MATTER_JURISDICTION = "subject_matter_jurisdiction"
    DISCOVERY = "discovery"
    MOTION_TO_DISMISS = "motion_to_dismiss"
    STANDING = "standing"
    
    # Corporate law concepts
    FIDUCIARY_DUTY = "fiduciary_duty"
    BUSINESS_JUDGMENT_RULE = "business_judgment_rule"
    PIERCING_CORPORATE_VEIL = "piercing_corporate_veil"
    DERIVATIVE_SUIT = "derivative_suit"
    
    # Criminal law concepts
    MENS_REA = "mens_rea"
    ACTUS_REUS = "actus_reus"
    REASONABLE_DOUBT = "reasonable_doubt"
    MIRANDA_RIGHTS = "miranda_rights"
    PROBABLE_CAUSE = "probable_cause"


@dataclass
class LegalContextScore:
    """Score for a specific legal context"""
    context_type: LegalContextType
    concept: Optional[LegalConcept]
    score: float
    confidence: float
    evidence: List[str]
    related_terms: List[str]


@dataclass
class PracticeAreaAnalysis:
    """Analysis of practice area relevance"""
    primary_area: str
    secondary_areas: List[str]
    confidence: float
    supporting_evidence: List[str]
    legal_concepts: List[LegalConcept]
    typical_document_types: List[ContentType]


@dataclass
class ProceduralContext:
    """Analysis of procedural context"""
    stage: str  # e.g., "pleading", "discovery", "trial", "appeal"
    motion_type: Optional[str]
    procedural_requirements: List[str]
    applicable_rules: List[str]
    timeline_considerations: List[str]


@dataclass
class LegalContextAnalysis:
    """Complete legal context analysis"""
    practice_area_analysis: PracticeAreaAnalysis
    procedural_context: Optional[ProceduralContext]
    legal_concepts: List[LegalContextScore]
    jurisdiction_analysis: Dict[str, float]
    temporal_analysis: Dict[str, Any]
    complexity_score: float
    legal_formality_score: float
    context_confidence: float


class LegalContextAnalyzer:
    """
    Advanced legal context analyzer that understands legal concepts,
    practice areas, and procedural contexts.
    """
    
    def __init__(self):
        # Comprehensive legal terminology database
        self.practice_areas = {
            'constitutional_law': {
                'primary_terms': {
                    'constitutional', 'amendment', 'bill of rights', 'due process',
                    'equal protection', 'commerce clause', 'supremacy clause',
                    'establishment clause', 'free exercise', 'cruel and unusual',
                    'search and seizure', 'double jeopardy', 'self incrimination'
                },
                'secondary_terms': {
                    'fundamental right', 'compelling interest', 'strict scrutiny',
                    'rational basis', 'intermediate scrutiny', 'judicial review',
                    'incorporation doctrine', 'dormant commerce clause'
                },
                'typical_documents': [ContentType.CASES, ContentType.CONSTITUTIONS],
                'related_concepts': [
                    LegalConcept.DUE_PROCESS, LegalConcept.EQUAL_PROTECTION,
                    LegalConcept.COMMERCE_CLAUSE, LegalConcept.FIRST_AMENDMENT,
                    LegalConcept.FOURTH_AMENDMENT, LegalConcept.SEPARATION_OF_POWERS
                ]
            },
            'contract_law': {
                'primary_terms': {
                    'contract', 'agreement', 'offer', 'acceptance', 'consideration',
                    'breach', 'damages', 'specific performance', 'rescission',
                    'reformation', 'restitution', 'mutual assent'
                },
                'secondary_terms': {
                    'promissory estoppel', 'quasi contract', 'unjust enrichment',
                    'impossibility', 'frustration of purpose', 'impracticability',
                    'condition precedent', 'condition subsequent'
                },
                'typical_documents': [ContentType.CASES, ContentType.STATUTES],
                'related_concepts': [
                    LegalConcept.CONSIDERATION, LegalConcept.BREACH_OF_CONTRACT,
                    LegalConcept.SPECIFIC_PERFORMANCE, LegalConcept.UNCONSCIONABILITY
                ]
            },
            'tort_law': {
                'primary_terms': {
                    'tort', 'negligence', 'liability', 'duty of care', 'breach of duty',
                    'causation', 'damages', 'proximate cause', 'but for test',
                    'foreseeability', 'reasonable person', 'standard of care'
                },
                'secondary_terms': {
                    'contributory negligence', 'comparative negligence', 'assumption of risk',
                    'res ipsa loquitur', 'negligence per se', 'strict liability',
                    'intentional tort', 'defamation', 'privacy', 'battery', 'assault'
                },
                'typical_documents': [ContentType.CASES, ContentType.STATUTES],
                'related_concepts': [
                    LegalConcept.NEGLIGENCE, LegalConcept.STRICT_LIABILITY,
                    LegalConcept.CAUSATION, LegalConcept.DAMAGES, LegalConcept.DUTY_OF_CARE
                ]
            },
            'criminal_law': {
                'primary_terms': {
                    'criminal', 'crime', 'felony', 'misdemeanor', 'mens rea',
                    'actus reus', 'intent', 'conspiracy', 'attempt', 'solicitation',
                    'accomplice', 'accessory', 'self defense', 'insanity'
                },
                'secondary_terms': {
                    'beyond reasonable doubt', 'miranda warning', 'probable cause',
                    'reasonable suspicion', 'exclusionary rule', 'fruit of poisonous tree',
                    'double jeopardy', 'ex post facto', 'corpus delicti'
                },
                'typical_documents': [ContentType.CASES, ContentType.STATUTES],
                'related_concepts': [
                    LegalConcept.MENS_REA, LegalConcept.ACTUS_REUS,
                    LegalConcept.REASONABLE_DOUBT, LegalConcept.MIRANDA_RIGHTS
                ]
            },
            'corporate_law': {
                'primary_terms': {
                    'corporation', 'corporate', 'fiduciary duty', 'business judgment',
                    'shareholder', 'director', 'officer', 'merger', 'acquisition',
                    'securities', 'disclosure', 'proxy', 'derivative suit'
                },
                'secondary_terms': {
                    'piercing corporate veil', 'ultra vires', 'insider trading',
                    'tender offer', 'leveraged buyout', 'going private',
                    'poison pill', 'white knight', 'golden parachute'
                },
                'typical_documents': [ContentType.CASES, ContentType.STATUTES, ContentType.REGULATIONS],
                'related_concepts': [
                    LegalConcept.FIDUCIARY_DUTY, LegalConcept.BUSINESS_JUDGMENT_RULE,
                    LegalConcept.PIERCING_CORPORATE_VEIL, LegalConcept.DERIVATIVE_SUIT
                ]
            },
            'employment_law': {
                'primary_terms': {
                    'employment', 'employee', 'employer', 'discrimination',
                    'harassment', 'wrongful termination', 'at will employment',
                    'collective bargaining', 'union', 'wage and hour'
                },
                'secondary_terms': {
                    'title vii', 'ada', 'adea', 'fmla', 'flsa', 'nlra',
                    'hostile work environment', 'disparate treatment', 'disparate impact',
                    'bona fide occupational qualification', 'reasonable accommodation'
                },
                'typical_documents': [ContentType.CASES, ContentType.STATUTES, ContentType.REGULATIONS],
                'related_concepts': []
            },
            'intellectual_property': {
                'primary_terms': {
                    'patent', 'trademark', 'copyright', 'trade secret',
                    'infringement', 'fair use', 'novelty', 'non obviousness',
                    'prior art', 'licensing', 'royalty'
                },
                'secondary_terms': {
                    'prosecution history estoppel', 'doctrine of equivalents',
                    'all elements rule', 'genericness', 'functionality',
                    'secondary meaning', 'likelihood of confusion'
                },
                'typical_documents': [ContentType.CASES, ContentType.STATUTES, ContentType.REGULATIONS],
                'related_concepts': []
            },
            'tax_law': {
                'primary_terms': {
                    'tax', 'taxation', 'deduction', 'exemption', 'credit',
                    'income', 'gross income', 'adjusted gross income', 'basis',
                    'depreciation', 'amortization', 'capital gain', 'ordinary income'
                },
                'secondary_terms': {
                    'like kind exchange', 'installment sale', 'passive activity',
                    'alternative minimum tax', 'earned income credit',
                    'kiddie tax', 'wash sale', 'constructive receipt'
                },
                'typical_documents': [ContentType.STATUTES, ContentType.REGULATIONS, ContentType.CASES],
                'related_concepts': []
            }
        }
        
        # Procedural contexts and stages
        self.procedural_stages = {
            'pleading': {
                'terms': {'complaint', 'answer', 'reply', 'counterclaim', 'cross claim', 'third party complaint'},
                'motions': {'motion to dismiss', 'motion for more definite statement', 'motion to strike'},
                'rules': ['Fed. R. Civ. P. 8', 'Fed. R. Civ. P. 9', 'Fed. R. Civ. P. 12']
            },
            'discovery': {
                'terms': {'discovery', 'deposition', 'interrogatory', 'request for production', 'request for admission'},
                'motions': {'motion to compel', 'motion for protective order', 'motion for sanctions'},
                'rules': ['Fed. R. Civ. P. 26', 'Fed. R. Civ. P. 30', 'Fed. R. Civ. P. 33']
            },
            'pretrial': {
                'terms': {'pretrial conference', 'case management', 'scheduling order', 'pretrial order'},
                'motions': {'motion for summary judgment', 'motion in limine', 'motion to exclude'},
                'rules': ['Fed. R. Civ. P. 16', 'Fed. R. Civ. P. 56', 'Fed. R. Evid. 401']
            },
            'trial': {
                'terms': {'trial', 'jury selection', 'opening statement', 'closing argument', 'verdict'},
                'motions': {'motion for directed verdict', 'motion for judgment as matter of law', 'motion for new trial'},
                'rules': ['Fed. R. Civ. P. 50', 'Fed. R. Civ. P. 59', 'Fed. R. Evid. 101']
            },
            'appeal': {
                'terms': {'appeal', 'appellate', 'notice of appeal', 'brief', 'oral argument'},
                'motions': {'motion for stay', 'motion to expedite', 'motion for leave to file'},
                'rules': ['Fed. R. App. P. 3', 'Fed. R. App. P. 28', 'Fed. R. App. P. 34']
            }
        }
        
        # Legal concept patterns
        self.concept_patterns = {
            LegalConcept.DUE_PROCESS: {
                'patterns': [
                    r'\bdue process\b',
                    r'\bprocedural due process\b',
                    r'\bsubstantive due process\b',
                    r'\bfundamental fairness\b'
                ],
                'context_terms': {'fairness', 'notice', 'hearing', 'opportunity', 'fundamental'}
            },
            LegalConcept.EQUAL_PROTECTION: {
                'patterns': [
                    r'\bequal protection\b',
                    r'\bsimilarly situated\b',
                    r'\bstrict scrutiny\b',
                    r'\brational basis\b'
                ],
                'context_terms': {'discrimination', 'classification', 'scrutiny', 'compelling interest'}
            },
            LegalConcept.NEGLIGENCE: {
                'patterns': [
                    r'\bnegligence\b',
                    r'\bduty of care\b',
                    r'\bbreach of duty\b',
                    r'\breasonable person\b'
                ],
                'context_terms': {'duty', 'breach', 'causation', 'damages', 'reasonable', 'standard of care'}
            },
            LegalConcept.CONSIDERATION: {
                'patterns': [
                    r'\bconsideration\b',
                    r'\bbargained.for exchange\b',
                    r'\bdetriment\b',
                    r'\bbenefit\b'
                ],
                'context_terms': {'promise', 'exchange', 'value', 'bargain', 'detriment', 'benefit'}
            }
        }
        
        # Citation patterns for different types of legal authority
        self.authority_patterns = {
            'supreme_court': re.compile(r'\b\d+\s+U\.S\.\s+\d+\b'),
            'circuit_court': re.compile(r'\b\d+\s+F\.\d*d?\s+\d+\b'),
            'district_court': re.compile(r'\b\d+\s+F\.\s*Supp\.?\s*\d*\s+\d+\b'),
            'state_court': re.compile(r'\b\d+\s+\w{2,8}\s+\d+\b'),
            'statute': re.compile(r'\b\d+\s+U\.S\.C\.?\s+§?\s*\d+\b'),
            'regulation': re.compile(r'\b\d+\s+C\.F\.R\.?\s+§?\s*\d+\b'),
            'constitution': re.compile(r'\bU\.S\.\s*Const\.\s*art\.\s*\w+|\bamend\.\s*\w+\b', re.IGNORECASE)
        }
        
        logger.info("Legal context analyzer initialized")
    
    async def analyze_legal_context(
        self,
        text: str,
        document_type: Optional[ContentType] = None,
        query_context: Optional[UnifiedQuery] = None
    ) -> LegalContextAnalysis:
        """
        Perform comprehensive legal context analysis on text
        """
        try:
            logger.info(f"Analyzing legal context for text: '{text[:100]}...'")
            
            # Normalize text for analysis
            normalized_text = self._normalize_legal_text(text)
            
            # Practice area analysis
            practice_area_analysis = await self._analyze_practice_areas(
                normalized_text, document_type
            )
            
            # Procedural context analysis
            procedural_context = await self._analyze_procedural_context(normalized_text)
            
            # Legal concept identification
            legal_concepts = await self._identify_legal_concepts(normalized_text)
            
            # Jurisdiction analysis
            jurisdiction_analysis = await self._analyze_jurisdictions(
                normalized_text, query_context
            )
            
            # Temporal analysis
            temporal_analysis = await self._analyze_temporal_context(
                normalized_text, query_context
            )
            
            # Calculate complexity and formality scores
            complexity_score = self._calculate_legal_complexity(normalized_text)
            formality_score = self._calculate_legal_formality(normalized_text)
            
            # Overall confidence
            context_confidence = self._calculate_context_confidence(
                practice_area_analysis, procedural_context, legal_concepts
            )
            
            return LegalContextAnalysis(
                practice_area_analysis=practice_area_analysis,
                procedural_context=procedural_context,
                legal_concepts=legal_concepts,
                jurisdiction_analysis=jurisdiction_analysis,
                temporal_analysis=temporal_analysis,
                complexity_score=complexity_score,
                legal_formality_score=formality_score,
                context_confidence=context_confidence
            )
            
        except Exception as e:
            logger.error(f"Legal context analysis failed: {str(e)}")
            return LegalContextAnalysis(
                practice_area_analysis=PracticeAreaAnalysis(
                    primary_area="unknown",
                    secondary_areas=[],
                    confidence=0.0,
                    supporting_evidence=[],
                    legal_concepts=[],
                    typical_document_types=[]
                ),
                procedural_context=None,
                legal_concepts=[],
                jurisdiction_analysis={},
                temporal_analysis={},
                complexity_score=0.0,
                legal_formality_score=0.0,
                context_confidence=0.0
            )
    
    async def _analyze_practice_areas(
        self,
        text: str,
        document_type: Optional[ContentType]
    ) -> PracticeAreaAnalysis:
        """Analyze and identify relevant practice areas"""
        try:
            text_lower = text.lower()
            area_scores = {}
            evidence_by_area = defaultdict(list)
            
            # Score each practice area
            for area, area_data in self.practice_areas.items():
                score = 0.0
                
                # Primary terms (higher weight)
                primary_matches = 0
                for term in area_data['primary_terms']:
                    if term in text_lower:
                        primary_matches += 1
                        score += 2.0
                        evidence_by_area[area].append(f"Primary term: {term}")
                
                # Secondary terms (lower weight)
                secondary_matches = 0
                for term in area_data['secondary_terms']:
                    if term in text_lower:
                        secondary_matches += 1
                        score += 1.0
                        evidence_by_area[area].append(f"Secondary term: {term}")
                
                # Document type bonus
                if document_type and document_type in area_data['typical_documents']:
                    score += 1.5
                    evidence_by_area[area].append(f"Typical document type: {document_type.value}")
                
                # Normalize score by number of terms
                total_terms = len(area_data['primary_terms']) + len(area_data['secondary_terms'])
                if total_terms > 0:
                    area_scores[area] = score / total_terms
                else:
                    area_scores[area] = 0.0
            
            # Identify primary and secondary areas
            sorted_areas = sorted(area_scores.items(), key=lambda x: x[1], reverse=True)
            
            if not sorted_areas or sorted_areas[0][1] == 0:
                return PracticeAreaAnalysis(
                    primary_area="general",
                    secondary_areas=[],
                    confidence=0.0,
                    supporting_evidence=["No clear practice area indicators"],
                    legal_concepts=[],
                    typical_document_types=[]
                )
            
            primary_area = sorted_areas[0][0]
            primary_score = sorted_areas[0][1]
            
            # Secondary areas (score > 0.3 and within 50% of primary score)
            secondary_areas = []
            for area, score in sorted_areas[1:]:
                if score > 0.3 and score >= primary_score * 0.5:
                    secondary_areas.append(area)
                    if len(secondary_areas) >= 3:  # Limit to top 3 secondary areas
                        break
            
            # Calculate confidence
            confidence = min(primary_score / 2.0, 1.0)
            
            # Get related legal concepts
            related_concepts = self.practice_areas[primary_area].get('related_concepts', [])
            
            # Get typical document types
            typical_docs = self.practice_areas[primary_area].get('typical_documents', [])
            
            return PracticeAreaAnalysis(
                primary_area=primary_area,
                secondary_areas=secondary_areas,
                confidence=confidence,
                supporting_evidence=evidence_by_area[primary_area],
                legal_concepts=related_concepts,
                typical_document_types=typical_docs
            )
            
        except Exception as e:
            logger.error(f"Practice area analysis failed: {str(e)}")
            return PracticeAreaAnalysis(
                primary_area="general",
                secondary_areas=[],
                confidence=0.0,
                supporting_evidence=[],
                legal_concepts=[],
                typical_document_types=[]
            )
    
    async def _analyze_procedural_context(self, text: str) -> Optional[ProceduralContext]:
        """Analyze procedural context and stage"""
        try:
            text_lower = text.lower()
            stage_scores = {}
            
            # Score each procedural stage
            for stage, stage_data in self.procedural_stages.items():
                score = 0.0
                
                # Check for stage-specific terms
                for term in stage_data['terms']:
                    if term in text_lower:
                        score += 1.0
                
                # Check for stage-specific motions
                for motion in stage_data['motions']:
                    if motion in text_lower:
                        score += 1.5  # Motions are strong indicators
                
                # Check for relevant rules
                for rule in stage_data['rules']:
                    if rule.lower() in text_lower:
                        score += 0.5
                
                stage_scores[stage] = score
            
            # Find the most likely stage
            best_stage = max(stage_scores.items(), key=lambda x: x[1])
            
            if best_stage[1] < 0.5:  # Too low to be confident
                return None
            
            stage_name = best_stage[0]
            stage_data = self.procedural_stages[stage_name]
            
            # Identify specific motion type
            motion_type = None
            for motion in stage_data['motions']:
                if motion in text_lower:
                    motion_type = motion
                    break
            
            # Extract procedural requirements and rules
            applicable_rules = []
            for rule in stage_data['rules']:
                if rule.lower() in text_lower:
                    applicable_rules.append(rule)
            
            return ProceduralContext(
                stage=stage_name,
                motion_type=motion_type,
                procedural_requirements=list(stage_data['terms']),
                applicable_rules=applicable_rules,
                timeline_considerations=self._extract_timeline_requirements(text_lower, stage_name)
            )
            
        except Exception as e:
            logger.error(f"Procedural context analysis failed: {str(e)}")
            return None
    
    async def _identify_legal_concepts(self, text: str) -> List[LegalContextScore]:
        """Identify and score legal concepts in text"""
        try:
            text_lower = text.lower()
            concept_scores = []
            
            for concept, concept_data in self.concept_patterns.items():
                score = 0.0
                evidence = []
                related_terms = []
                
                # Check for direct pattern matches
                for pattern in concept_data['patterns']:
                    matches = re.findall(pattern, text_lower)
                    if matches:
                        score += len(matches) * 2.0
                        evidence.append(f"Direct match: {pattern}")
                
                # Check for context terms
                context_matches = 0
                for term in concept_data['context_terms']:
                    if term in text_lower:
                        context_matches += 1
                        related_terms.append(term)
                
                if context_matches > 0:
                    score += context_matches * 0.5
                    evidence.append(f"Context terms: {context_matches}/{len(concept_data['context_terms'])}")
                
                # Normalize score
                max_possible_score = len(concept_data['patterns']) * 2.0 + len(concept_data['context_terms']) * 0.5
                normalized_score = min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
                
                if normalized_score > 0.1:  # Only include concepts with meaningful scores
                    confidence = min(score / 3.0, 1.0)  # Confidence based on absolute score
                    
                    concept_scores.append(LegalContextScore(
                        context_type=LegalContextType.DOCTRINAL,
                        concept=concept,
                        score=normalized_score,
                        confidence=confidence,
                        evidence=evidence,
                        related_terms=related_terms
                    ))
            
            # Sort by score
            concept_scores.sort(key=lambda x: x.score, reverse=True)
            
            return concept_scores
            
        except Exception as e:
            logger.error(f"Legal concept identification failed: {str(e)}")
            return []
    
    async def _analyze_jurisdictions(
        self,
        text: str,
        query_context: Optional[UnifiedQuery]
    ) -> Dict[str, float]:
        """Analyze jurisdictional context"""
        try:
            jurisdiction_scores = {}
            text_lower = text.lower()
            
            # Federal jurisdiction indicators
            federal_indicators = [
                'federal', 'united states', 'supreme court', 'circuit', 'district court',
                'federal register', 'cfr', 'usc', 'congress', 'constitutional'
            ]
            
            federal_score = sum(1 for indicator in federal_indicators if indicator in text_lower)
            if federal_score > 0:
                jurisdiction_scores['federal'] = min(federal_score / len(federal_indicators), 1.0)
            
            # State jurisdiction indicators
            state_names = [
                'california', 'new york', 'texas', 'florida', 'illinois', 'pennsylvania',
                'ohio', 'georgia', 'north carolina', 'michigan', 'new jersey',
                'virginia', 'washington', 'arizona', 'massachusetts', 'tennessee'
            ]
            
            for state in state_names:
                if state in text_lower:
                    jurisdiction_scores[state] = 0.8
            
            # Check for specific court references
            if re.search(r'\bsupreme court\b', text_lower):
                if 'united states' in text_lower or 'u.s.' in text_lower:
                    jurisdiction_scores['federal'] = jurisdiction_scores.get('federal', 0) + 0.5
                else:
                    # Could be state supreme court
                    for state in state_names:
                        if state in text_lower:
                            jurisdiction_scores[state] = jurisdiction_scores.get(state, 0) + 0.3
            
            # Circuit court references
            circuit_pattern = re.compile(r'\b(\w+)\s+circuit\b')
            circuit_matches = circuit_pattern.findall(text_lower)
            for match in circuit_matches:
                jurisdiction_scores['federal'] = jurisdiction_scores.get('federal', 0) + 0.4
            
            # Query context boost
            if query_context and query_context.jurisdictions:
                for query_jurisdiction in query_context.jurisdictions:
                    query_juris_lower = query_jurisdiction.lower()
                    if query_juris_lower in jurisdiction_scores:
                        jurisdiction_scores[query_juris_lower] *= 1.2
            
            # Normalize scores
            if jurisdiction_scores:
                max_score = max(jurisdiction_scores.values())
                if max_score > 1.0:
                    for jurisdiction in jurisdiction_scores:
                        jurisdiction_scores[jurisdiction] /= max_score
            
            return jurisdiction_scores
            
        except Exception as e:
            logger.error(f"Jurisdiction analysis failed: {str(e)}")
            return {}
    
    async def _analyze_temporal_context(
        self,
        text: str,
        query_context: Optional[UnifiedQuery]
    ) -> Dict[str, Any]:
        """Analyze temporal context and requirements"""
        try:
            temporal_analysis = {}
            text_lower = text.lower()
            
            # Time-sensitive legal concepts
            urgency_indicators = [
                'emergency', 'urgent', 'immediate', 'ex parte', 'temporary restraining order',
                'preliminary injunction', 'stay', 'expedite', 'rush'
            ]
            
            urgency_score = sum(1 for indicator in urgency_indicators if indicator in text_lower)
            if urgency_score > 0:
                temporal_analysis['urgency'] = min(urgency_score / len(urgency_indicators), 1.0)
            
            # Historical vs. contemporary focus
            historical_indicators = ['historical', 'precedent', 'landmark', 'seminal', 'foundational']
            contemporary_indicators = ['recent', 'current', 'modern', 'contemporary', 'latest']
            
            historical_score = sum(1 for indicator in historical_indicators if indicator in text_lower)
            contemporary_score = sum(1 for indicator in contemporary_indicators if indicator in text_lower)
            
            if historical_score > 0:
                temporal_analysis['historical_focus'] = min(historical_score / len(historical_indicators), 1.0)
            if contemporary_score > 0:
                temporal_analysis['contemporary_focus'] = min(contemporary_score / len(contemporary_indicators), 1.0)
            
            # Extract specific years
            year_pattern = re.compile(r'\b(19|20)\d{2}\b')
            years = [int(match) for match in year_pattern.findall(text)]
            if years:
                temporal_analysis['mentioned_years'] = sorted(set(years))
                current_year = datetime.now().year
                avg_year = sum(years) / len(years)
                temporal_analysis['temporal_center'] = avg_year
                temporal_analysis['recency_bias'] = (avg_year - 1950) / (current_year - 1950)
            
            # Query temporal context
            if query_context:
                if query_context.date_from or query_context.date_to:
                    temporal_analysis['query_date_range'] = {
                        'from': query_context.date_from.isoformat() if query_context.date_from else None,
                        'to': query_context.date_to.isoformat() if query_context.date_to else None
                    }
            
            # Statute of limitations indicators
            limitation_indicators = ['statute of limitations', 'time limit', 'deadline', 'expires', 'barred by time']
            limitation_score = sum(1 for indicator in limitation_indicators if indicator in text_lower)
            if limitation_score > 0:
                temporal_analysis['limitation_relevance'] = min(limitation_score / len(limitation_indicators), 1.0)
            
            return temporal_analysis
            
        except Exception as e:
            logger.error(f"Temporal analysis failed: {str(e)}")
            return {}
    
    def _calculate_legal_complexity(self, text: str) -> float:
        """Calculate legal complexity score"""
        try:
            complexity_factors = []
            text_lower = text.lower()
            
            # Length and structure complexity
            word_count = len(text.split())
            sentence_count = len([s for s in re.split(r'[.!?]', text) if s.strip()])
            avg_sentence_length = word_count / max(sentence_count, 1)
            
            length_complexity = min(word_count / 1000, 1.0)  # Normalize to 1000 words
            structure_complexity = min(avg_sentence_length / 20, 1.0)  # Normalize to 20 words/sentence
            
            complexity_factors.append(('length', length_complexity, 0.2))
            complexity_factors.append(('structure', structure_complexity, 0.2))
            
            # Legal terminology density
            legal_terms = 0
            total_legal_terms = 0
            
            for area_data in self.practice_areas.values():
                for term in area_data['primary_terms'] | area_data['secondary_terms']:
                    total_legal_terms += 1
                    if term in text_lower:
                        legal_terms += 1
            
            if total_legal_terms > 0:
                terminology_density = legal_terms / min(word_count / 100, total_legal_terms / 10)
                complexity_factors.append(('terminology', min(terminology_density, 1.0), 0.3))
            
            # Citation density
            citation_count = 0
            for pattern in self.authority_patterns.values():
                citation_count += len(pattern.findall(text))
            
            citation_density = min(citation_count / max(word_count / 200, 1), 1.0)
            complexity_factors.append(('citations', citation_density, 0.15))
            
            # Procedural complexity
            procedural_terms = 0
            for stage_data in self.procedural_stages.values():
                for term in stage_data['terms'] | set(stage_data['motions']):
                    if term in text_lower:
                        procedural_terms += 1
            
            procedural_complexity = min(procedural_terms / 10, 1.0)
            complexity_factors.append(('procedural', procedural_complexity, 0.15))
            
            # Calculate weighted average
            total_weight = sum(weight for _, _, weight in complexity_factors)
            weighted_sum = sum(score * weight for _, score, weight in complexity_factors)
            
            return weighted_sum / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Legal complexity calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_legal_formality(self, text: str) -> float:
        """Calculate legal formality score"""
        try:
            formality_indicators = {
                'high_formality': [
                    'whereas', 'wherefore', 'heretofore', 'hereinafter', 'thereof',
                    'pursuant to', 'in accordance with', 'notwithstanding',
                    'provided that', 'subject to', 'inter alia', 'prima facie'
                ],
                'moderate_formality': [
                    'therefore', 'furthermore', 'moreover', 'nevertheless',
                    'accordingly', 'consequently', 'subsequently', 'however'
                ],
                'legal_phrases': [
                    'it is hereby', 'be it resolved', 'comes now', 'respectfully submitted',
                    'prayer for relief', 'cause of action', 'burden of proof'
                ]
            }
            
            text_lower = text.lower()
            formality_score = 0.0
            
            # High formality terms
            high_count = sum(1 for term in formality_indicators['high_formality'] if term in text_lower)
            formality_score += high_count * 0.3
            
            # Moderate formality terms
            moderate_count = sum(1 for term in formality_indicators['moderate_formality'] if term in text_lower)
            formality_score += moderate_count * 0.2
            
            # Legal phrases
            phrase_count = sum(1 for phrase in formality_indicators['legal_phrases'] if phrase in text_lower)
            formality_score += phrase_count * 0.4
            
            # Citation style formality
            formal_citations = len(re.findall(r'\b(?:see|citing|cited in|accord)\b.*?\d+.*?\d+', text_lower))
            formality_score += formal_citations * 0.1
            
            # Normalize to 0-1 scale
            word_count = len(text.split())
            normalized_score = min(formality_score / max(word_count / 100, 1), 1.0)
            
            return normalized_score
            
        except Exception as e:
            logger.error(f"Legal formality calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_context_confidence(
        self,
        practice_area_analysis: PracticeAreaAnalysis,
        procedural_context: Optional[ProceduralContext],
        legal_concepts: List[LegalContextScore]
    ) -> float:
        """Calculate overall confidence in context analysis"""
        try:
            confidence_factors = []
            
            # Practice area confidence
            confidence_factors.append(('practice_area', practice_area_analysis.confidence, 0.4))
            
            # Procedural context confidence
            if procedural_context:
                # Higher confidence if we found procedural context
                confidence_factors.append(('procedural', 0.8, 0.2))
            else:
                confidence_factors.append(('procedural', 0.3, 0.2))
            
            # Legal concepts confidence
            if legal_concepts:
                avg_concept_confidence = sum(concept.confidence for concept in legal_concepts) / len(legal_concepts)
                confidence_factors.append(('concepts', avg_concept_confidence, 0.4))
            else:
                confidence_factors.append(('concepts', 0.2, 0.4))
            
            # Calculate weighted average
            total_weight = sum(weight for _, _, weight in confidence_factors)
            weighted_sum = sum(confidence * weight for _, confidence, weight in confidence_factors)
            
            return weighted_sum / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Context confidence calculation failed: {str(e)}")
            return 0.0
    
    def _extract_timeline_requirements(self, text: str, stage: str) -> List[str]:
        """Extract timeline and deadline requirements"""
        timeline_requirements = []
        
        # Common deadline patterns
        deadline_patterns = [
            r'\b(\d+)\s+days?\b',
            r'\b(\d+)\s+months?\b',
            r'\bwithin\s+(\d+\s+\w+)\b',
            r'\bno\s+later\s+than\s+(\d+\s+\w+)\b'
        ]
        
        for pattern in deadline_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                timeline_requirements.append(f"Deadline: {match}")
        
        # Stage-specific requirements
        stage_deadlines = {
            'pleading': ['20 days to answer', '21 days for reply'],
            'discovery': ['30 days for responses', '7 days notice for depositions'],
            'pretrial': ['14 days for summary judgment responses', '7 days for motions in limine'],
            'trial': ['30 days notice for trial', '10 days for jury instructions'],
            'appeal': ['30 days for notice of appeal', '40 days for appellant brief']
        }
        
        if stage in stage_deadlines:
            timeline_requirements.extend(stage_deadlines[stage])
        
        return timeline_requirements
    
    def _normalize_legal_text(self, text: str) -> str:
        """Normalize legal text for analysis"""
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Normalize common legal abbreviations
        abbreviation_map = {
            r'\bu\.s\.c\.\b': 'usc',
            r'\bc\.f\.r\.\b': 'cfr',
            r'\bf\.\s*supp\.': 'f.supp.',
            r'\bf\.\d*d\b': 'f.2d',
            r'\bs\.\s*ct\.\b': 's.ct.',
            r'\bu\.s\.\b': 'us'
        }
        
        for pattern, replacement in abbreviation_map.items():
            normalized = re.sub(pattern, replacement, normalized)
        
        # Remove excessive whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    # Public utility methods
    
    def get_practice_areas(self) -> List[str]:
        """Get list of supported practice areas"""
        return list(self.practice_areas.keys())
    
    def get_legal_concepts(self) -> List[LegalConcept]:
        """Get list of supported legal concepts"""
        return list(LegalConcept)
    
    def get_procedural_stages(self) -> List[str]:
        """Get list of procedural stages"""
        return list(self.procedural_stages.keys())
    
    async def suggest_related_terms(self, query_text: str) -> List[str]:
        """Suggest related legal terms based on query"""
        try:
            # Analyze the query
            context_analysis = await self.analyze_legal_context(query_text)
            
            suggestions = set()
            
            # Add terms from primary practice area
            primary_area = context_analysis.practice_area_analysis.primary_area
            if primary_area != "unknown" and primary_area in self.practice_areas:
                area_data = self.practice_areas[primary_area]
                suggestions.update(list(area_data['primary_terms'])[:5])
                suggestions.update(list(area_data['secondary_terms'])[:3])
            
            # Add terms from identified legal concepts
            for concept_score in context_analysis.legal_concepts[:3]:
                if concept_score.concept and concept_score.concept in self.concept_patterns:
                    concept_data = self.concept_patterns[concept_score.concept]
                    suggestions.update(concept_data['context_terms'])
            
            # Add procedural terms if relevant
            if context_analysis.procedural_context:
                stage = context_analysis.procedural_context.stage
                if stage in self.procedural_stages:
                    stage_data = self.procedural_stages[stage]
                    suggestions.update(list(stage_data['terms'])[:3])
            
            return list(suggestions)[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"Term suggestion failed: {str(e)}")
            return []