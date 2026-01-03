"""
Authority Scoring Engine

Advanced authority scoring system for legal documents that evaluates
precedential value, court hierarchy, citation networks, and jurisprudential
significance.
"""

import asyncio
import logging
import re
import math
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any, NamedTuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum

from .database_models import UnifiedDocument, ContentType, DatabaseProvider

logger = logging.getLogger(__name__)


class AuthorityType(Enum):
    """Types of legal authority"""
    PRIMARY_BINDING = "primary_binding"
    PRIMARY_PERSUASIVE = "primary_persuasive"
    SECONDARY_AUTHORITATIVE = "secondary_authoritative"
    SECONDARY_PERSUASIVE = "secondary_persuasive"
    ADMINISTRATIVE = "administrative"
    HISTORICAL = "historical"


class CourtLevel(Enum):
    """Court hierarchy levels"""
    SUPREME_COURT_US = "supreme_court_us"
    CIRCUIT_COURT = "circuit_court"
    DISTRICT_COURT = "district_court"
    STATE_SUPREME = "state_supreme"
    STATE_APPELLATE = "state_appellate"
    STATE_TRIAL = "state_trial"
    SPECIALIZED_FEDERAL = "specialized_federal"
    ADMINISTRATIVE_COURT = "administrative_court"
    BANKRUPTCY_COURT = "bankruptcy_court"
    TAX_COURT = "tax_court"
    UNKNOWN = "unknown"


@dataclass
class AuthorityScore:
    """Individual authority scoring component"""
    component: str
    score: float
    weight: float
    confidence: float
    explanation: str
    details: Dict[str, Any]


@dataclass
class CitationAnalysis:
    """Citation network analysis"""
    cited_by_count: int
    citing_cases_authority: float
    citation_network_centrality: float
    self_citation_ratio: float
    forward_citations: List[str]
    backward_citations: List[str]
    citation_age_distribution: Dict[str, int]


@dataclass
class AuthorityAssessment:
    """Complete authority assessment for a document"""
    document_id: str
    overall_authority: float
    authority_type: AuthorityType
    court_level: CourtLevel
    individual_scores: List[AuthorityScore]
    citation_analysis: Optional[CitationAnalysis]
    precedential_value: float
    persuasive_value: float
    historical_significance: float
    confidence: float
    authority_explanation: List[str]


class AuthorityScoringEngine:
    """
    Advanced authority scoring engine that evaluates legal documents
    based on court hierarchy, citation networks, and jurisprudential significance.
    """
    
    def __init__(self):
        # Court hierarchy definitions with authority scores
        self.court_hierarchy = {
            # Federal Courts
            CourtLevel.SUPREME_COURT_US: {
                'authority_score': 1.0,
                'precedential_weight': 1.0,
                'patterns': [
                    r'\bunited states supreme court\b',
                    r'\bsupreme court of the united states\b',
                    r'\bscotus\b',
                    r'\bus supreme court\b'
                ],
                'citation_patterns': [r'\b\d+\s+U\.S\.\s+\d+\b']
            },
            
            CourtLevel.CIRCUIT_COURT: {
                'authority_score': 0.8,
                'precedential_weight': 0.85,
                'patterns': [
                    r'\b\w+\s+circuit\s+court\s+of\s+appeals\b',
                    r'\bU\.S\.\s+Court\s+of\s+Appeals\b',
                    r'\bcourt\s+of\s+appeals\s+for\s+the\s+\w+\s+circuit\b'
                ],
                'citation_patterns': [r'\b\d+\s+F\.\d*d?\s+\d+\b']
            },
            
            CourtLevel.DISTRICT_COURT: {
                'authority_score': 0.6,
                'precedential_weight': 0.5,
                'patterns': [
                    r'\bU\.S\.\s+District\s+Court\b',
                    r'\bdistrict\s+court\s+for\s+the\b',
                    r'\bfederal\s+district\s+court\b'
                ],
                'citation_patterns': [r'\b\d+\s+F\.\s*Supp\.?\s*\d*\s+\d+\b']
            },
            
            CourtLevel.SPECIALIZED_FEDERAL: {
                'authority_score': 0.7,
                'precedential_weight': 0.75,
                'patterns': [
                    r'\bfederal\s+circuit\b',
                    r'\bcourt\s+of\s+appeals\s+for\s+the\s+federal\s+circuit\b',
                    r'\bcourt\s+of\s+international\s+trade\b'
                ],
                'citation_patterns': [r'\b\d+\s+F\.\d*d?\s+\d+\b']
            },
            
            # State Courts
            CourtLevel.STATE_SUPREME: {
                'authority_score': 0.75,
                'precedential_weight': 0.8,
                'patterns': [
                    r'\bsupreme\s+court\s+of\s+\w+\b',
                    r'\bstate\s+supreme\s+court\b',
                    r'\bhighest\s+court\s+of\s+\w+\b'
                ],
                'citation_patterns': [r'\b\d+\s+\w{2,8}\s+\d+\b']
            },
            
            CourtLevel.STATE_APPELLATE: {
                'authority_score': 0.65,
                'precedential_weight': 0.7,
                'patterns': [
                    r'\bcourt\s+of\s+appeals\s+of\s+\w+\b',
                    r'\bappellate\s+court\s+of\s+\w+\b',
                    r'\bintermediate\s+appellate\s+court\b'
                ],
                'citation_patterns': [r'\b\d+\s+\w{2,8}\s+\d+\b']
            },
            
            CourtLevel.STATE_TRIAL: {
                'authority_score': 0.4,
                'precedential_weight': 0.3,
                'patterns': [
                    r'\bsuperior\s+court\s+of\s+\w+\b',
                    r'\bcounty\s+court\s+of\s+\w+\b',
                    r'\bdistrict\s+court\s+of\s+\w+\b',
                    r'\btrial\s+court\b'
                ],
                'citation_patterns': [r'\b\d+\s+\w{2,8}\s+\d+\b']
            },
            
            # Specialized Courts
            CourtLevel.BANKRUPTCY_COURT: {
                'authority_score': 0.5,
                'precedential_weight': 0.6,
                'patterns': [
                    r'\bbankruptcy\s+court\b',
                    r'\bU\.S\.\s+Bankruptcy\s+Court\b'
                ],
                'citation_patterns': [r'\b\d+\s+B\.R\.\s+\d+\b']
            },
            
            CourtLevel.TAX_COURT: {
                'authority_score': 0.65,
                'precedential_weight': 0.7,
                'patterns': [
                    r'\btax\s+court\b',
                    r'\bU\.S\.\s+Tax\s+Court\b'
                ],
                'citation_patterns': [r'\b\d+\s+T\.C\.\s+\d+\b']
            },
            
            CourtLevel.ADMINISTRATIVE_COURT: {
                'authority_score': 0.55,
                'precedential_weight': 0.6,
                'patterns': [
                    r'\badministrative\s+court\b',
                    r'\badministrative\s+law\s+judge\b',
                    r'\bagency\s+decision\b'
                ],
                'citation_patterns': []
            }
        }
        
        # Document type authority weights
        self.document_type_weights = {
            ContentType.CASES: {
                'base_authority': 0.8,
                'precedential_value': 1.0,
                'persuasive_value': 0.9
            },
            ContentType.STATUTES: {
                'base_authority': 1.0,
                'precedential_value': 1.0,
                'persuasive_value': 1.0
            },
            ContentType.CONSTITUTIONS: {
                'base_authority': 1.0,
                'precedential_value': 1.0,
                'persuasive_value': 1.0
            },
            ContentType.REGULATIONS: {
                'base_authority': 0.9,
                'precedential_value': 0.8,
                'persuasive_value': 0.85
            },
            ContentType.LAW_REVIEWS: {
                'base_authority': 0.6,
                'precedential_value': 0.3,
                'persuasive_value': 0.8
            },
            ContentType.TREATISES: {
                'base_authority': 0.7,
                'precedential_value': 0.4,
                'persuasive_value': 0.9
            },
            ContentType.BRIEFS: {
                'base_authority': 0.3,
                'precedential_value': 0.1,
                'persuasive_value': 0.4
            },
            ContentType.DOCKETS: {
                'base_authority': 0.2,
                'precedential_value': 0.1,
                'persuasive_value': 0.2
            }
        }
        
        # Provider reliability scores
        self.provider_reliability = {
            DatabaseProvider.SUPREMECOURT_GOV: 1.0,
            DatabaseProvider.GOVINFO: 0.95,
            DatabaseProvider.CONGRESS_GOV: 0.95,
            DatabaseProvider.COURTLISTENER: 0.9,
            DatabaseProvider.WESTLAW: 0.95,
            DatabaseProvider.LEXISNEXIS: 0.95,
            DatabaseProvider.HEINONLINE: 0.9,
            DatabaseProvider.JUSTIA: 0.8,
            DatabaseProvider.GOOGLE_SCHOLAR: 0.75
        }
        
        # Authority keywords that indicate high precedential value
        self.authority_keywords = {
            'landmark': 2.0,
            'seminal': 2.0,
            'leading case': 1.8,
            'controlling': 1.8,
            'binding precedent': 1.8,
            'on point': 1.5,
            'directly on point': 1.7,
            'distinguishable': -0.3,
            'overruled': -2.0,
            'reversed': -1.5,
            'superseded': -1.8,
            'limited': -0.5,
            'criticized': -0.8,
            'questioned': -0.6,
            'followed': 1.2,
            'affirmed': 1.3,
            'adopted': 1.4,
            'relied upon': 1.3
        }
        
        logger.info("Authority scoring engine initialized")
    
    async def calculate_authority_score(
        self,
        document: UnifiedDocument,
        citation_context: Optional[Dict[str, Any]] = None
    ) -> AuthorityAssessment:
        """
        Calculate comprehensive authority score for a legal document
        """
        try:
            doc_id = document.source_document_id or str(id(document))
            logger.info(f"Calculating authority score for document: {doc_id}")
            
            individual_scores = []
            authority_explanations = []
            
            # 1. Court hierarchy score
            court_score = await self._calculate_court_authority(document)
            individual_scores.append(court_score)
            if court_score.score > 0.7:
                authority_explanations.append(f"High court authority: {court_score.explanation}")
            
            # 2. Document type authority
            doc_type_score = await self._calculate_document_type_authority(document)
            individual_scores.append(doc_type_score)
            
            # 3. Provider reliability
            provider_score = await self._calculate_provider_reliability(document)
            individual_scores.append(provider_score)
            
            # 4. Citation network analysis
            citation_analysis = await self._analyze_citation_network(document, citation_context)
            citation_score = await self._calculate_citation_authority(citation_analysis)
            individual_scores.append(citation_score)
            
            # 5. Content authority indicators
            content_score = await self._calculate_content_authority(document)
            individual_scores.append(content_score)
            if content_score.score > 0.6:
                authority_explanations.append(f"Strong content authority: {content_score.explanation}")
            
            # 6. Historical significance
            historical_score = await self._calculate_historical_significance(document)
            individual_scores.append(historical_score)
            
            # 7. Jurisdictional authority
            jurisdictional_score = await self._calculate_jurisdictional_authority(document)
            individual_scores.append(jurisdictional_score)
            
            # Calculate weighted overall authority
            overall_authority = self._calculate_weighted_authority(individual_scores)
            
            # Determine authority type and court level
            authority_type = self._determine_authority_type(document, individual_scores)
            court_level = self._identify_court_level(document)
            
            # Calculate specific authority values
            precedential_value = self._calculate_precedential_value(individual_scores, authority_type)
            persuasive_value = self._calculate_persuasive_value(individual_scores, authority_type)
            historical_significance = historical_score.score
            
            # Calculate confidence
            confidence = self._calculate_authority_confidence(individual_scores)
            
            return AuthorityAssessment(
                document_id=doc_id,
                overall_authority=overall_authority,
                authority_type=authority_type,
                court_level=court_level,
                individual_scores=individual_scores,
                citation_analysis=citation_analysis,
                precedential_value=precedential_value,
                persuasive_value=persuasive_value,
                historical_significance=historical_significance,
                confidence=confidence,
                authority_explanation=authority_explanations
            )
            
        except Exception as e:
            logger.error(f"Authority score calculation failed: {str(e)}")
            return AuthorityAssessment(
                document_id=doc_id,
                overall_authority=0.5,
                authority_type=AuthorityType.SECONDARY_PERSUASIVE,
                court_level=CourtLevel.UNKNOWN,
                individual_scores=[],
                citation_analysis=None,
                precedential_value=0.5,
                persuasive_value=0.5,
                historical_significance=0.0,
                confidence=0.0,
                authority_explanation=[f"Authority calculation error: {str(e)}"]
            )
    
    async def _calculate_court_authority(self, document: UnifiedDocument) -> AuthorityScore:
        """Calculate authority based on court hierarchy"""
        try:
            if not document.court:
                return AuthorityScore(
                    component="court_authority",
                    score=0.5,
                    weight=0.3,
                    confidence=0.0,
                    explanation="No court information",
                    details={}
                )
            
            court_text = document.court.lower()
            best_match = None
            best_score = 0.0
            
            # Find best matching court level
            for court_level, court_data in self.court_hierarchy.items():
                for pattern in court_data['patterns']:
                    if re.search(pattern, court_text):
                        score = court_data['authority_score']
                        if score > best_score:
                            best_score = score
                            best_match = court_level
                        break
            
            if best_match:
                court_data = self.court_hierarchy[best_match]
                explanation = f"{best_match.value} (score: {best_score:.2f})"
                confidence = 0.9
            else:
                # Try to infer court level from text
                if 'supreme' in court_text:
                    if 'united states' in court_text or 'us' in court_text:
                        best_score = 1.0
                        best_match = CourtLevel.SUPREME_COURT_US
                    else:
                        best_score = 0.75
                        best_match = CourtLevel.STATE_SUPREME
                elif any(term in court_text for term in ['circuit', 'appeals']):
                    best_score = 0.8
                    best_match = CourtLevel.CIRCUIT_COURT
                elif 'district' in court_text:
                    best_score = 0.6
                    best_match = CourtLevel.DISTRICT_COURT
                else:
                    best_score = 0.4
                    best_match = CourtLevel.UNKNOWN
                
                explanation = f"Inferred {best_match.value} (score: {best_score:.2f})"
                confidence = 0.6
            
            return AuthorityScore(
                component="court_authority",
                score=best_score,
                weight=0.3,
                confidence=confidence,
                explanation=explanation,
                details={
                    "court_name": document.court,
                    "identified_level": best_match.value if best_match else "unknown",
                    "authority_score": best_score
                }
            )
            
        except Exception as e:
            logger.error(f"Court authority calculation failed: {str(e)}")
            return AuthorityScore(
                component="court_authority",
                score=0.5,
                weight=0.3,
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _calculate_document_type_authority(self, document: UnifiedDocument) -> AuthorityScore:
        """Calculate authority based on document type"""
        try:
            if not document.document_type:
                return AuthorityScore(
                    component="document_type_authority",
                    score=0.5,
                    weight=0.2,
                    confidence=0.0,
                    explanation="Unknown document type",
                    details={}
                )
            
            type_weights = self.document_type_weights.get(document.document_type, {
                'base_authority': 0.5,
                'precedential_value': 0.5,
                'persuasive_value': 0.5
            })
            
            base_score = type_weights['base_authority']
            
            # Adjust for primary vs. secondary authority
            if document.document_type in [ContentType.CASES, ContentType.STATUTES, 
                                        ContentType.CONSTITUTIONS, ContentType.REGULATIONS]:
                explanation = f"Primary authority: {document.document_type.value}"
                confidence = 0.9
            else:
                explanation = f"Secondary authority: {document.document_type.value}"
                confidence = 0.8
                base_score *= 0.8  # Slight reduction for secondary authority
            
            return AuthorityScore(
                component="document_type_authority",
                score=base_score,
                weight=0.2,
                confidence=confidence,
                explanation=explanation,
                details={
                    "document_type": document.document_type.value,
                    "type_weights": type_weights,
                    "is_primary_authority": document.document_type in [
                        ContentType.CASES, ContentType.STATUTES, 
                        ContentType.CONSTITUTIONS, ContentType.REGULATIONS
                    ]
                }
            )
            
        except Exception as e:
            logger.error(f"Document type authority calculation failed: {str(e)}")
            return AuthorityScore(
                component="document_type_authority",
                score=0.5,
                weight=0.2,
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _calculate_provider_reliability(self, document: UnifiedDocument) -> AuthorityScore:
        """Calculate authority based on source provider reliability"""
        try:
            if not document.source_provider:
                return AuthorityScore(
                    component="provider_reliability",
                    score=0.7,  # Neutral score for unknown provider
                    weight=0.1,
                    confidence=0.0,
                    explanation="Unknown provider",
                    details={}
                )
            
            reliability_score = self.provider_reliability.get(document.source_provider, 0.5)
            
            # Adjust for free vs. paid sources
            if document.is_free_access:
                explanation = f"Free source: {document.source_provider.value} (reliability: {reliability_score:.2f})"
                # Slight adjustment for comprehensive free sources
                if document.source_provider in [DatabaseProvider.GOVINFO, DatabaseProvider.SUPREMECOURT_GOV]:
                    pass  # No adjustment for government sources
                else:
                    reliability_score *= 0.95
            else:
                explanation = f"Premium source: {document.source_provider.value} (reliability: {reliability_score:.2f})"
            
            confidence = 0.8
            
            return AuthorityScore(
                component="provider_reliability",
                score=reliability_score,
                weight=0.1,
                confidence=confidence,
                explanation=explanation,
                details={
                    "provider": document.source_provider.value,
                    "is_free": document.is_free_access,
                    "base_reliability": self.provider_reliability.get(document.source_provider, 0.5)
                }
            )
            
        except Exception as e:
            logger.error(f"Provider reliability calculation failed: {str(e)}")
            return AuthorityScore(
                component="provider_reliability",
                score=0.7,
                weight=0.1,
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _analyze_citation_network(
        self,
        document: UnifiedDocument,
        citation_context: Optional[Dict[str, Any]]
    ) -> Optional[CitationAnalysis]:
        """Analyze citation network for the document"""
        try:
            if not any([document.cited_cases, document.citing_cases, citation_context]):
                return None
            
            # Count citations
            cited_by_count = len(document.citing_cases) if document.citing_cases else 0
            cites_count = len(document.cited_cases) if document.cited_cases else 0
            
            # Add citation context if available
            if citation_context:
                cited_by_count += citation_context.get('citing_count', 0)
                if 'forward_citations' in citation_context:
                    forward_citations = citation_context['forward_citations']
                else:
                    forward_citations = document.citing_cases or []
            else:
                forward_citations = document.citing_cases or []
            
            backward_citations = document.cited_cases or []
            
            # Calculate citation network centrality (simplified)
            if cited_by_count > 0 and cites_count > 0:
                citation_network_centrality = math.log(cited_by_count + 1) * math.log(cites_count + 1) / 100
            else:
                citation_network_centrality = 0.0
            
            # Calculate citing cases authority (would need actual case data)
            citing_cases_authority = min(cited_by_count / 50, 1.0)  # Simplified calculation
            
            # Self-citation ratio (if analyzable)
            self_citation_ratio = 0.0  # Would require detailed analysis
            
            # Citation age distribution
            citation_age_distribution = {'recent': 0, 'medium': 0, 'old': 0}
            # Would require date analysis of citing cases
            
            return CitationAnalysis(
                cited_by_count=cited_by_count,
                citing_cases_authority=citing_cases_authority,
                citation_network_centrality=citation_network_centrality,
                self_citation_ratio=self_citation_ratio,
                forward_citations=forward_citations,
                backward_citations=backward_citations,
                citation_age_distribution=citation_age_distribution
            )
            
        except Exception as e:
            logger.error(f"Citation network analysis failed: {str(e)}")
            return None
    
    async def _calculate_citation_authority(
        self,
        citation_analysis: Optional[CitationAnalysis]
    ) -> AuthorityScore:
        """Calculate authority based on citation analysis"""
        try:
            if not citation_analysis:
                return AuthorityScore(
                    component="citation_authority",
                    score=0.5,
                    weight=0.15,
                    confidence=0.0,
                    explanation="No citation data available",
                    details={}
                )
            
            # Base score from citation count
            citation_score = 0.5
            
            # Boost from being cited by others
            if citation_analysis.cited_by_count > 0:
                # Logarithmic scaling for citation count
                citation_boost = min(math.log(citation_analysis.cited_by_count + 1) / 5, 0.4)
                citation_score += citation_boost
            
            # Network centrality boost
            citation_score += citation_analysis.citation_network_centrality * 0.1
            
            # Authority of citing cases
            citation_score += citation_analysis.citing_cases_authority * 0.1
            
            # Cap at 1.0
            citation_score = min(citation_score, 1.0)
            
            confidence = 0.7 if citation_analysis.cited_by_count > 0 else 0.3
            
            explanation = f"Citations: {citation_analysis.cited_by_count} citing"
            if citation_analysis.citation_network_centrality > 0.1:
                explanation += f", high centrality"
            
            return AuthorityScore(
                component="citation_authority",
                score=citation_score,
                weight=0.15,
                confidence=confidence,
                explanation=explanation,
                details={
                    "cited_by_count": citation_analysis.cited_by_count,
                    "network_centrality": citation_analysis.citation_network_centrality,
                    "citing_authority": citation_analysis.citing_cases_authority
                }
            )
            
        except Exception as e:
            logger.error(f"Citation authority calculation failed: {str(e)}")
            return AuthorityScore(
                component="citation_authority",
                score=0.5,
                weight=0.15,
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _calculate_content_authority(self, document: UnifiedDocument) -> AuthorityScore:
        """Calculate authority based on document content indicators"""
        try:
            content = self._get_document_content(document)
            if not content:
                return AuthorityScore(
                    component="content_authority",
                    score=0.5,
                    weight=0.1,
                    confidence=0.0,
                    explanation="No content available",
                    details={}
                )
            
            content_lower = content.lower()
            authority_score = 0.5  # Base score
            authority_indicators = []
            
            # Check for authority keywords
            keyword_boost = 0.0
            for keyword, weight in self.authority_keywords.items():
                if keyword in content_lower:
                    keyword_boost += weight * 0.1  # Scale down the weights
                    if weight > 0:
                        authority_indicators.append(f"+ {keyword}")
                    else:
                        authority_indicators.append(f"- {keyword}")
            
            # Apply keyword boost
            authority_score += min(keyword_boost, 0.3)  # Cap boost at 0.3
            
            # Content quality indicators
            quality_score = 0.0
            
            # Length and structure (longer, well-structured documents often more authoritative)
            word_count = len(content.split())
            if word_count > 5000:
                quality_score += 0.1
                authority_indicators.append("comprehensive length")
            elif word_count > 1000:
                quality_score += 0.05
            
            # Legal citation density
            citation_count = len(re.findall(r'\b\d+\s+\w+\.?\s+\d+\b', content))
            citation_density = citation_count / max(word_count / 1000, 1)  # Citations per 1000 words
            if citation_density > 5:
                quality_score += 0.1
                authority_indicators.append("high citation density")
            elif citation_density > 2:
                quality_score += 0.05
            
            # Formal legal language
            formal_indicators = [
                'whereas', 'wherefore', 'heretofore', 'pursuant to',
                'notwithstanding', 'inter alia', 'prima facie'
            ]
            formal_count = sum(1 for indicator in formal_indicators if indicator in content_lower)
            if formal_count > 3:
                quality_score += 0.05
                authority_indicators.append("formal legal language")
            
            authority_score += quality_score
            authority_score = min(authority_score, 1.0)
            
            confidence = 0.6 if authority_indicators else 0.3
            explanation = f"Content authority: {len(authority_indicators)} indicators"
            
            return AuthorityScore(
                component="content_authority",
                score=authority_score,
                weight=0.1,
                confidence=confidence,
                explanation=explanation,
                details={
                    "authority_indicators": authority_indicators,
                    "keyword_boost": keyword_boost,
                    "quality_score": quality_score,
                    "word_count": word_count,
                    "citation_density": citation_density
                }
            )
            
        except Exception as e:
            logger.error(f"Content authority calculation failed: {str(e)}")
            return AuthorityScore(
                component="content_authority",
                score=0.5,
                weight=0.1,
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _calculate_historical_significance(self, document: UnifiedDocument) -> AuthorityScore:
        """Calculate historical significance of the document"""
        try:
            doc_date = document.decision_date or document.publication_date
            if not doc_date:
                return AuthorityScore(
                    component="historical_significance",
                    score=0.3,
                    weight=0.05,
                    confidence=0.0,
                    explanation="No date information",
                    details={}
                )
            
            today = date.today()
            years_old = (today - doc_date).days / 365.25
            
            # Historical significance scoring
            historical_score = 0.0
            significance_indicators = []
            
            # Age-based significance
            if years_old > 50:
                historical_score += 0.4
                significance_indicators.append(f"historic ({years_old:.0f} years old)")
            elif years_old > 25:
                historical_score += 0.3
                significance_indicators.append(f"established ({years_old:.0f} years old)")
            elif years_old > 10:
                historical_score += 0.2
                significance_indicators.append(f"mature ({years_old:.0f} years old)")
            
            # Content-based significance indicators
            content = self._get_document_content(document)
            if content:
                content_lower = content.lower()
                
                historical_terms = [
                    'landmark', 'seminal', 'foundational', 'watershed',
                    'precedential', 'historic', 'first impression'
                ]
                
                for term in historical_terms:
                    if term in content_lower:
                        historical_score += 0.2
                        significance_indicators.append(f"significant: {term}")
                        break  # Only count once
            
            # Court level boost for historical significance
            if document.court:
                court_lower = document.court.lower()
                if 'supreme court' in court_lower:
                    historical_score += 0.3
                    significance_indicators.append("supreme court decision")
            
            historical_score = min(historical_score, 1.0)
            confidence = 0.8 if doc_date and significance_indicators else 0.4
            
            explanation = f"Historical significance: {', '.join(significance_indicators[:2])}"
            
            return AuthorityScore(
                component="historical_significance",
                score=historical_score,
                weight=0.05,
                confidence=confidence,
                explanation=explanation,
                details={
                    "years_old": years_old,
                    "significance_indicators": significance_indicators,
                    "document_date": doc_date.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Historical significance calculation failed: {str(e)}")
            return AuthorityScore(
                component="historical_significance",
                score=0.3,
                weight=0.05,
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _calculate_jurisdictional_authority(self, document: UnifiedDocument) -> AuthorityScore:
        """Calculate authority based on jurisdictional scope"""
        try:
            if not document.jurisdiction:
                return AuthorityScore(
                    component="jurisdictional_authority",
                    score=0.5,
                    weight=0.1,
                    confidence=0.0,
                    explanation="No jurisdiction information",
                    details={}
                )
            
            jurisdiction_lower = document.jurisdiction.lower()
            jurisdictional_score = 0.5
            explanation = f"Jurisdiction: {document.jurisdiction}"
            
            # Federal jurisdiction gets higher score
            if 'federal' in jurisdiction_lower or 'united states' in jurisdiction_lower:
                jurisdictional_score = 0.9
                explanation = "Federal jurisdiction (nationwide authority)"
                confidence = 0.9
            
            # Multi-state or circuit jurisdiction
            elif any(term in jurisdiction_lower for term in ['circuit', 'regional', 'multi']):
                jurisdictional_score = 0.8
                explanation = "Multi-jurisdictional authority"
                confidence = 0.8
            
            # State jurisdiction
            elif any(state in jurisdiction_lower for state in [
                'california', 'new york', 'texas', 'florida', 'illinois'
            ]):
                jurisdictional_score = 0.7
                explanation = f"State jurisdiction: {document.jurisdiction}"
                confidence = 0.7
            
            # Local jurisdiction
            elif any(term in jurisdiction_lower for term in ['county', 'city', 'local']):
                jurisdictional_score = 0.4
                explanation = f"Local jurisdiction: {document.jurisdiction}"
                confidence = 0.6
            
            else:
                # Unknown but specified jurisdiction
                jurisdictional_score = 0.6
                confidence = 0.5
            
            return AuthorityScore(
                component="jurisdictional_authority",
                score=jurisdictional_score,
                weight=0.1,
                confidence=confidence,
                explanation=explanation,
                details={
                    "jurisdiction": document.jurisdiction,
                    "is_federal": 'federal' in jurisdiction_lower
                }
            )
            
        except Exception as e:
            logger.error(f"Jurisdictional authority calculation failed: {str(e)}")
            return AuthorityScore(
                component="jurisdictional_authority",
                score=0.5,
                weight=0.1,
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    def _calculate_weighted_authority(self, individual_scores: List[AuthorityScore]) -> float:
        """Calculate weighted overall authority score"""
        try:
            if not individual_scores:
                return 0.5
            
            total_weight = sum(score.weight for score in individual_scores)
            if total_weight == 0:
                return 0.5
            
            weighted_sum = sum(score.score * score.weight for score in individual_scores)
            return weighted_sum / total_weight
            
        except Exception as e:
            logger.error(f"Weighted authority calculation failed: {str(e)}")
            return 0.5
    
    def _determine_authority_type(
        self,
        document: UnifiedDocument,
        individual_scores: List[AuthorityScore]
    ) -> AuthorityType:
        """Determine the type of legal authority"""
        try:
            # Primary vs. secondary authority
            is_primary = document.document_type in [
                ContentType.CASES, ContentType.STATUTES,
                ContentType.CONSTITUTIONS, ContentType.REGULATIONS
            ]
            
            if not is_primary:
                # Secondary authority
                if document.document_type in [ContentType.LAW_REVIEWS, ContentType.TREATISES]:
                    return AuthorityType.SECONDARY_AUTHORITATIVE
                else:
                    return AuthorityType.SECONDARY_PERSUASIVE
            
            # Primary authority - determine binding vs. persuasive
            court_score = next((s for s in individual_scores if s.component == "court_authority"), None)
            if court_score and court_score.score >= 0.8:
                # High court authority suggests binding precedent
                return AuthorityType.PRIMARY_BINDING
            elif court_score and court_score.score >= 0.6:
                # Medium court authority suggests persuasive precedent
                return AuthorityType.PRIMARY_PERSUASIVE
            else:
                return AuthorityType.PRIMARY_PERSUASIVE
                
        except Exception as e:
            logger.error(f"Authority type determination failed: {str(e)}")
            return AuthorityType.SECONDARY_PERSUASIVE
    
    def _identify_court_level(self, document: UnifiedDocument) -> CourtLevel:
        """Identify the court level of the document"""
        try:
            if not document.court:
                return CourtLevel.UNKNOWN
            
            court_text = document.court.lower()
            
            # Check each court level pattern
            for court_level, court_data in self.court_hierarchy.items():
                for pattern in court_data['patterns']:
                    if re.search(pattern, court_text):
                        return court_level
            
            # Fallback inference
            if 'supreme' in court_text:
                if 'united states' in court_text or 'us' in court_text:
                    return CourtLevel.SUPREME_COURT_US
                else:
                    return CourtLevel.STATE_SUPREME
            elif any(term in court_text for term in ['circuit', 'appeals']):
                return CourtLevel.CIRCUIT_COURT
            elif 'district' in court_text:
                return CourtLevel.DISTRICT_COURT
            else:
                return CourtLevel.UNKNOWN
                
        except Exception as e:
            logger.error(f"Court level identification failed: {str(e)}")
            return CourtLevel.UNKNOWN
    
    def _calculate_precedential_value(
        self,
        individual_scores: List[AuthorityScore],
        authority_type: AuthorityType
    ) -> float:
        """Calculate precedential value"""
        try:
            if authority_type in [AuthorityType.SECONDARY_AUTHORITATIVE, AuthorityType.SECONDARY_PERSUASIVE]:
                return 0.3  # Secondary authority has low precedential value
            
            # For primary authority, base on court authority and citations
            court_score = next((s.score for s in individual_scores if s.component == "court_authority"), 0.5)
            citation_score = next((s.score for s in individual_scores if s.component == "citation_authority"), 0.5)
            
            # Weighted combination
            precedential = (court_score * 0.7) + (citation_score * 0.3)
            
            # Boost for binding authority
            if authority_type == AuthorityType.PRIMARY_BINDING:
                precedential *= 1.2
            
            return min(precedential, 1.0)
            
        except Exception as e:
            logger.error(f"Precedential value calculation failed: {str(e)}")
            return 0.5
    
    def _calculate_persuasive_value(
        self,
        individual_scores: List[AuthorityScore],
        authority_type: AuthorityType
    ) -> float:
        """Calculate persuasive value"""
        try:
            # All authority types have some persuasive value
            base_persuasive = 0.5
            
            # Content authority affects persuasiveness
            content_score = next((s.score for s in individual_scores if s.component == "content_authority"), 0.5)
            
            # Provider reliability affects persuasiveness
            provider_score = next((s.score for s in individual_scores if s.component == "provider_reliability"), 0.7)
            
            # Historical significance adds persuasive value
            historical_score = next((s.score for s in individual_scores if s.component == "historical_significance"), 0.3)
            
            # Calculate persuasive value
            persuasive = (base_persuasive * 0.4) + (content_score * 0.3) + (provider_score * 0.2) + (historical_score * 0.1)
            
            # Adjust for authority type
            if authority_type == AuthorityType.SECONDARY_AUTHORITATIVE:
                persuasive *= 1.1  # Boost for authoritative secondary sources
            elif authority_type == AuthorityType.PRIMARY_BINDING:
                persuasive *= 1.2  # Binding authority is also highly persuasive
            
            return min(persuasive, 1.0)
            
        except Exception as e:
            logger.error(f"Persuasive value calculation failed: {str(e)}")
            return 0.5
    
    def _calculate_authority_confidence(self, individual_scores: List[AuthorityScore]) -> float:
        """Calculate confidence in authority assessment"""
        try:
            if not individual_scores:
                return 0.0
            
            # Average individual confidences
            avg_confidence = sum(score.confidence for score in individual_scores) / len(individual_scores)
            
            # Confidence boost for having multiple high-confidence scores
            high_confidence_count = sum(1 for score in individual_scores if score.confidence > 0.7)
            completeness_bonus = high_confidence_count / len(individual_scores)
            
            # Combined confidence
            overall_confidence = (avg_confidence * 0.8) + (completeness_bonus * 0.2)
            
            return min(overall_confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Authority confidence calculation failed: {str(e)}")
            return 0.0
    
    def _get_document_content(self, document: UnifiedDocument) -> str:
        """Get document content for analysis"""
        content_parts = []
        
        if document.title:
            content_parts.append(document.title)
        
        if document.summary:
            content_parts.append(document.summary)
        
        if document.full_text:
            # Limit content length for performance
            text = document.full_text[:10000] if len(document.full_text) > 10000 else document.full_text
            content_parts.append(text)
        
        if document.headnotes:
            content_parts.extend(document.headnotes[:3])  # First 3 headnotes
        
        return ' '.join(content_parts)
    
    # Public utility methods
    
    def get_court_levels(self) -> List[CourtLevel]:
        """Get list of supported court levels"""
        return list(CourtLevel)
    
    def get_authority_types(self) -> List[AuthorityType]:
        """Get list of authority types"""
        return list(AuthorityType)
    
    async def compare_authority(
        self,
        doc1: UnifiedDocument,
        doc2: UnifiedDocument
    ) -> Dict[str, Any]:
        """Compare authority between two documents"""
        try:
            assessment1 = await self.calculate_authority_score(doc1)
            assessment2 = await self.calculate_authority_score(doc2)
            
            return {
                "document1": {
                    "id": assessment1.document_id,
                    "authority": assessment1.overall_authority,
                    "type": assessment1.authority_type.value,
                    "court_level": assessment1.court_level.value
                },
                "document2": {
                    "id": assessment2.document_id,
                    "authority": assessment2.overall_authority,
                    "type": assessment2.authority_type.value,
                    "court_level": assessment2.court_level.value
                },
                "comparison": {
                    "higher_authority": assessment1.document_id if assessment1.overall_authority > assessment2.overall_authority else assessment2.document_id,
                    "authority_difference": abs(assessment1.overall_authority - assessment2.overall_authority),
                    "same_court_level": assessment1.court_level == assessment2.court_level,
                    "same_authority_type": assessment1.authority_type == assessment2.authority_type
                }
            }
            
        except Exception as e:
            logger.error(f"Authority comparison failed: {str(e)}")
            return {"error": str(e)}