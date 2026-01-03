"""
Advanced Relevance Ranking Engine

Sophisticated relevance ranking system for legal documents using multiple
algorithms including TF-IDF, legal term weighting, citation analysis,
and machine learning models.
"""

import asyncio
import logging
import math
import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any, NamedTuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum
import json

from .database_models import UnifiedDocument, UnifiedQuery, ContentType, DatabaseProvider

logger = logging.getLogger(__name__)


class RankingFeature(Enum):
    """Types of ranking features"""
    TEXTUAL_RELEVANCE = "textual_relevance"
    LEGAL_TERM_MATCH = "legal_term_match"
    CITATION_RELEVANCE = "citation_relevance"
    AUTHORITY_SCORE = "authority_score"
    RECENCY_SCORE = "recency_score"
    COMPLETENESS_SCORE = "completeness_score"
    JURISDICTION_MATCH = "jurisdiction_match"
    CONTENT_TYPE_MATCH = "content_type_match"
    QUERY_COVERAGE = "query_coverage"
    SEMANTIC_SIMILARITY = "semantic_similarity"


@dataclass
class RankingScore:
    """Individual ranking score component"""
    feature: RankingFeature
    score: float
    weight: float
    confidence: float
    explanation: str
    details: Dict[str, Any]


@dataclass
class DocumentRanking:
    """Complete ranking analysis for a document"""
    document_id: str
    final_score: float
    normalized_score: float
    individual_scores: List[RankingScore]
    ranking_explanation: List[str]
    confidence: float
    feature_weights: Dict[RankingFeature, float]


@dataclass
class QueryAnalysis:
    """Analysis of the search query for ranking purposes"""
    query_text: str
    normalized_query: str
    query_terms: Dict[str, float]  # term -> weight
    legal_concepts: Dict[str, float]  # concept -> relevance
    practice_areas: List[str]
    document_type_hints: List[ContentType]
    jurisdiction_hints: List[str]
    temporal_hints: Dict[str, Any]
    query_complexity: float
    semantic_vector: Optional[List[float]] = None


class RelevanceRankingEngine:
    """
    Advanced relevance ranking engine that uses multiple algorithms
    to score document relevance for legal search queries.
    """
    
    def __init__(self):
        # Legal term categories with weights
        self.legal_term_weights = {
            'procedural_high': {
                'summary judgment', 'motion to dismiss', 'preliminary injunction',
                'temporary restraining order', 'class action', 'collective action',
                'derivative suit', 'mandamus', 'certiorari', 'habeas corpus'
            },
            'procedural_medium': {
                'discovery', 'deposition', 'interrogatory', 'subpoena', 'motion',
                'pleading', 'complaint', 'answer', 'counterclaim', 'cross-claim'
            },
            'substantive_high': {
                'constitutional', 'due process', 'equal protection', 'commerce clause',
                'supremacy clause', 'first amendment', 'fourth amendment', 'takings clause'
            },
            'substantive_medium': {
                'contract', 'tort', 'negligence', 'breach', 'damages', 'liability',
                'fiduciary duty', 'business judgment', 'reasonable care'
            },
            'legal_standards': {
                'beyond reasonable doubt', 'preponderance of evidence', 'clear and convincing',
                'arbitrary and capricious', 'rational basis', 'strict scrutiny',
                'intermediate scrutiny', 'compelling interest'
            },
            'remedies': {
                'injunctive relief', 'monetary damages', 'specific performance',
                'rescission', 'restitution', 'declaratory judgment'
            }
        }
        
        # Practice area indicators
        self.practice_area_indicators = {
            'constitutional_law': {
                'constitutional', 'amendment', 'bill of rights', 'due process',
                'equal protection', 'commerce clause', 'supremacy clause'
            },
            'contract_law': {
                'contract', 'agreement', 'breach', 'consideration', 'offer',
                'acceptance', 'parol evidence', 'statute of frauds'
            },
            'tort_law': {
                'tort', 'negligence', 'duty of care', 'causation', 'damages',
                'strict liability', 'intentional tort', 'defamation'
            },
            'criminal_law': {
                'criminal', 'felony', 'misdemeanor', 'mens rea', 'actus reus',
                'conspiracy', 'intent', 'miranda', 'probable cause'
            },
            'corporate_law': {
                'corporate', 'corporation', 'securities', 'fiduciary',
                'business judgment', 'merger', 'acquisition', 'derivative'
            },
            'intellectual_property': {
                'patent', 'trademark', 'copyright', 'trade secret',
                'infringement', 'fair use', 'prior art'
            },
            'employment_law': {
                'employment', 'discrimination', 'harassment', 'wrongful termination',
                'wage and hour', 'fmla', 'ada', 'title vii'
            },
            'tax_law': {
                'tax', 'taxation', 'deduction', 'exemption', 'irs',
                'income tax', 'estate tax', 'gift tax'
            }
        }
        
        # Court hierarchy for authority scoring
        self.court_hierarchy = {
            'supreme_court_us': 10.0,
            'circuit_court': 8.0,
            'district_court': 6.0,
            'state_supreme': 7.0,
            'state_appellate': 5.0,
            'state_trial': 3.0,
            'administrative': 4.0,
            'bankruptcy': 4.0,
            'tax_court': 5.0
        }
        
        # Default feature weights
        self.default_feature_weights = {
            RankingFeature.TEXTUAL_RELEVANCE: 0.25,
            RankingFeature.LEGAL_TERM_MATCH: 0.20,
            RankingFeature.AUTHORITY_SCORE: 0.15,
            RankingFeature.RECENCY_SCORE: 0.10,
            RankingFeature.CITATION_RELEVANCE: 0.08,
            RankingFeature.COMPLETENESS_SCORE: 0.07,
            RankingFeature.JURISDICTION_MATCH: 0.05,
            RankingFeature.CONTENT_TYPE_MATCH: 0.05,
            RankingFeature.QUERY_COVERAGE: 0.03,
            RankingFeature.SEMANTIC_SIMILARITY: 0.02
        }
        
        # TF-IDF document frequency cache
        self.document_frequencies = defaultdict(int)
        self.total_documents = 0
        
        logger.info("Advanced relevance ranking engine initialized")
    
    async def rank_documents(
        self,
        documents: List[UnifiedDocument],
        query: UnifiedQuery,
        custom_weights: Optional[Dict[RankingFeature, float]] = None
    ) -> List[DocumentRanking]:
        """
        Rank documents based on relevance to the query using multiple algorithms
        """
        try:
            if not documents:
                return []
            
            logger.info(f"Ranking {len(documents)} documents for query: '{query.query_text[:100]}...'")
            
            # Step 1: Analyze the query
            query_analysis = await self._analyze_query(query)
            
            # Step 2: Determine feature weights based on query and user preferences
            feature_weights = self._determine_feature_weights(
                query_analysis, custom_weights
            )
            
            # Step 3: Update document frequency statistics
            await self._update_document_frequencies(documents)
            
            # Step 4: Calculate individual ranking scores for each document
            document_rankings = []
            for doc in documents:
                ranking = await self._rank_single_document(
                    doc, query, query_analysis, feature_weights
                )
                document_rankings.append(ranking)
            
            # Step 5: Normalize scores across all documents
            normalized_rankings = self._normalize_rankings(document_rankings)
            
            # Step 6: Sort by final score
            normalized_rankings.sort(key=lambda r: r.final_score, reverse=True)
            
            logger.info(f"Document ranking completed. Top score: {normalized_rankings[0].final_score:.3f}")
            return normalized_rankings
            
        except Exception as e:
            logger.error(f"Document ranking failed: {str(e)}")
            # Return basic rankings based on existing scores
            return [
                DocumentRanking(
                    document_id=doc.source_document_id or str(id(doc)),
                    final_score=doc.relevance_score,
                    normalized_score=doc.relevance_score,
                    individual_scores=[],
                    ranking_explanation=[f"Fallback to basic relevance: {doc.relevance_score:.2f}"],
                    confidence=0.5,
                    feature_weights={}
                )
                for doc in documents
            ]
    
    async def _analyze_query(self, query: UnifiedQuery) -> QueryAnalysis:
        """Analyze the search query to understand intent and context"""
        try:
            # Normalize query text
            normalized_query = self._normalize_legal_text(query.query_text)
            
            # Extract and weight query terms
            query_terms = self._extract_weighted_terms(query.query_text)
            
            # Identify legal concepts
            legal_concepts = self._identify_legal_concepts(query.query_text)
            
            # Detect practice areas
            practice_areas = self._detect_practice_areas(query.query_text)
            
            # Infer document type preferences
            doc_type_hints = self._infer_document_types(query)
            
            # Extract jurisdiction hints
            jurisdiction_hints = self._extract_jurisdiction_hints(query.query_text, query.jurisdictions)
            
            # Analyze temporal hints
            temporal_hints = self._analyze_temporal_context(query)
            
            # Calculate query complexity
            query_complexity = self._calculate_query_complexity(query.query_text)
            
            return QueryAnalysis(
                query_text=query.query_text,
                normalized_query=normalized_query,
                query_terms=query_terms,
                legal_concepts=legal_concepts,
                practice_areas=practice_areas,
                document_type_hints=doc_type_hints,
                jurisdiction_hints=jurisdiction_hints,
                temporal_hints=temporal_hints,
                query_complexity=query_complexity
            )
            
        except Exception as e:
            logger.error(f"Query analysis failed: {str(e)}")
            return QueryAnalysis(
                query_text=query.query_text,
                normalized_query=query.query_text.lower(),
                query_terms={term: 1.0 for term in query.query_text.lower().split()},
                legal_concepts={},
                practice_areas=[],
                document_type_hints=[],
                jurisdiction_hints=[],
                temporal_hints={},
                query_complexity=1.0
            )
    
    def _determine_feature_weights(
        self,
        query_analysis: QueryAnalysis,
        custom_weights: Optional[Dict[RankingFeature, float]]
    ) -> Dict[RankingFeature, float]:
        """Determine feature weights based on query characteristics"""
        try:
            # Start with default weights
            weights = self.default_feature_weights.copy()
            
            # Adjust weights based on query analysis
            if query_analysis.practice_areas:
                # Increase legal term weight for practice area queries
                weights[RankingFeature.LEGAL_TERM_MATCH] *= 1.2
                weights[RankingFeature.TEXTUAL_RELEVANCE] *= 0.9
            
            if query_analysis.document_type_hints:
                # Increase content type match weight
                weights[RankingFeature.CONTENT_TYPE_MATCH] *= 1.5
            
            if query_analysis.jurisdiction_hints:
                # Increase jurisdiction match weight
                weights[RankingFeature.JURISDICTION_MATCH] *= 1.3
            
            if query_analysis.temporal_hints:
                # Adjust recency weight based on temporal context
                if 'recent' in query_analysis.temporal_hints:
                    weights[RankingFeature.RECENCY_SCORE] *= 1.4
                elif 'historical' in query_analysis.temporal_hints:
                    weights[RankingFeature.RECENCY_SCORE] *= 0.7
                    weights[RankingFeature.AUTHORITY_SCORE] *= 1.2
            
            if query_analysis.query_complexity > 2.0:
                # Complex queries benefit from semantic similarity
                weights[RankingFeature.SEMANTIC_SIMILARITY] *= 1.5
                weights[RankingFeature.QUERY_COVERAGE] *= 1.3
            
            # Apply custom weights if provided
            if custom_weights:
                for feature, weight in custom_weights.items():
                    weights[feature] = weight
            
            # Normalize weights to sum to 1.0
            total_weight = sum(weights.values())
            for feature in weights:
                weights[feature] /= total_weight
            
            return weights
            
        except Exception as e:
            logger.error(f"Feature weight determination failed: {str(e)}")
            return self.default_feature_weights
    
    async def _rank_single_document(
        self,
        document: UnifiedDocument,
        query: UnifiedQuery,
        query_analysis: QueryAnalysis,
        feature_weights: Dict[RankingFeature, float]
    ) -> DocumentRanking:
        """Calculate comprehensive ranking for a single document"""
        try:
            doc_id = document.source_document_id or str(id(document))
            individual_scores = []
            explanations = []
            
            # Calculate individual feature scores
            
            # 1. Textual relevance (TF-IDF based)
            textual_score = await self._calculate_textual_relevance(
                document, query_analysis
            )
            individual_scores.append(textual_score)
            if textual_score.score > 0.7:
                explanations.append(f"High textual relevance ({textual_score.score:.2f})")
            
            # 2. Legal term matching
            legal_term_score = await self._calculate_legal_term_relevance(
                document, query_analysis
            )
            individual_scores.append(legal_term_score)
            if legal_term_score.score > 0.6:
                explanations.append(f"Strong legal term match ({legal_term_score.score:.2f})")
            
            # 3. Authority score
            authority_score = await self._calculate_enhanced_authority_score(document)
            individual_scores.append(authority_score)
            if authority_score.score > 0.8:
                explanations.append(f"High authority source ({authority_score.score:.2f})")
            
            # 4. Recency score
            recency_score = await self._calculate_enhanced_recency_score(
                document, query_analysis
            )
            individual_scores.append(recency_score)
            
            # 5. Citation relevance
            citation_score = await self._calculate_citation_relevance(
                document, query_analysis
            )
            individual_scores.append(citation_score)
            
            # 6. Completeness score
            completeness_score = await self._calculate_completeness_score(document)
            individual_scores.append(completeness_score)
            if completeness_score.score > 0.8:
                explanations.append("Comprehensive document content")
            
            # 7. Jurisdiction match
            jurisdiction_score = await self._calculate_jurisdiction_match(
                document, query, query_analysis
            )
            individual_scores.append(jurisdiction_score)
            if jurisdiction_score.score > 0.9:
                explanations.append("Perfect jurisdiction match")
            
            # 8. Content type match
            content_type_score = await self._calculate_content_type_match(
                document, query, query_analysis
            )
            individual_scores.append(content_type_score)
            
            # 9. Query coverage
            coverage_score = await self._calculate_query_coverage(
                document, query_analysis
            )
            individual_scores.append(coverage_score)
            
            # 10. Semantic similarity (if available)
            semantic_score = await self._calculate_semantic_similarity(
                document, query_analysis
            )
            individual_scores.append(semantic_score)
            
            # Calculate weighted final score
            final_score = sum(
                score.score * feature_weights.get(score.feature, 0.0)
                for score in individual_scores
            )
            
            # Calculate confidence based on score consistency
            confidence = self._calculate_ranking_confidence(individual_scores)
            
            # Add explanations for top factors
            top_scores = sorted(individual_scores, key=lambda s: s.score, reverse=True)[:3]
            for score in top_scores:
                if score.score > 0.6:
                    explanations.append(f"{score.explanation} ({score.score:.2f})")
            
            return DocumentRanking(
                document_id=doc_id,
                final_score=final_score,
                normalized_score=final_score,  # Will be normalized later
                individual_scores=individual_scores,
                ranking_explanation=explanations,
                confidence=confidence,
                feature_weights=feature_weights
            )
            
        except Exception as e:
            logger.error(f"Single document ranking failed: {str(e)}")
            return DocumentRanking(
                document_id=doc_id,
                final_score=0.5,
                normalized_score=0.5,
                individual_scores=[],
                ranking_explanation=[f"Ranking error: {str(e)}"],
                confidence=0.0,
                feature_weights={}
            )
    
    async def _calculate_textual_relevance(
        self,
        document: UnifiedDocument,
        query_analysis: QueryAnalysis
    ) -> RankingScore:
        """Calculate TF-IDF based textual relevance"""
        try:
            # Get document text
            doc_text = self._get_document_text(document)
            if not doc_text:
                return RankingScore(
                    feature=RankingFeature.TEXTUAL_RELEVANCE,
                    score=0.0,
                    weight=self.default_feature_weights[RankingFeature.TEXTUAL_RELEVANCE],
                    confidence=0.0,
                    explanation="No document text available",
                    details={}
                )
            
            # Normalize document text
            doc_text_norm = self._normalize_legal_text(doc_text)
            doc_terms = self._extract_terms(doc_text_norm)
            
            if not doc_terms:
                return RankingScore(
                    feature=RankingFeature.TEXTUAL_RELEVANCE,
                    score=0.0,
                    weight=self.default_feature_weights[RankingFeature.TEXTUAL_RELEVANCE],
                    confidence=0.0,
                    explanation="No meaningful terms in document",
                    details={}
                )
            
            # Calculate TF-IDF scores for query terms
            tfidf_scores = []
            term_matches = 0
            
            for query_term, query_weight in query_analysis.query_terms.items():
                if query_term in doc_terms:
                    term_matches += 1
                    
                    # Term frequency in document
                    tf = doc_terms.get(query_term, 0) / len(doc_terms)
                    
                    # Inverse document frequency
                    doc_freq = self.document_frequencies.get(query_term, 1)
                    idf = math.log(max(self.total_documents, 1) / doc_freq)
                    
                    # TF-IDF score
                    tfidf = tf * idf * query_weight
                    tfidf_scores.append(tfidf)
            
            # Overall textual relevance score
            if tfidf_scores:
                avg_tfidf = sum(tfidf_scores) / len(tfidf_scores)
                # Boost for higher term coverage
                coverage_boost = term_matches / len(query_analysis.query_terms)
                final_score = min(avg_tfidf * (1 + coverage_boost * 0.5), 1.0)
            else:
                final_score = 0.0
            
            confidence = min(term_matches / len(query_analysis.query_terms), 1.0)
            
            return RankingScore(
                feature=RankingFeature.TEXTUAL_RELEVANCE,
                score=final_score,
                weight=self.default_feature_weights[RankingFeature.TEXTUAL_RELEVANCE],
                confidence=confidence,
                explanation=f"TF-IDF relevance with {term_matches}/{len(query_analysis.query_terms)} term matches",
                details={
                    "term_matches": term_matches,
                    "total_query_terms": len(query_analysis.query_terms),
                    "avg_tfidf": avg_tfidf if tfidf_scores else 0.0,
                    "coverage_ratio": term_matches / len(query_analysis.query_terms)
                }
            )
            
        except Exception as e:
            logger.error(f"Textual relevance calculation failed: {str(e)}")
            return RankingScore(
                feature=RankingFeature.TEXTUAL_RELEVANCE,
                score=0.0,
                weight=self.default_feature_weights[RankingFeature.TEXTUAL_RELEVANCE],
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _calculate_legal_term_relevance(
        self,
        document: UnifiedDocument,
        query_analysis: QueryAnalysis
    ) -> RankingScore:
        """Calculate relevance based on legal terminology"""
        try:
            # Get document text
            doc_text = self._get_document_text(document)
            if not doc_text:
                return RankingScore(
                    feature=RankingFeature.LEGAL_TERM_MATCH,
                    score=0.0,
                    weight=self.default_feature_weights[RankingFeature.LEGAL_TERM_MATCH],
                    confidence=0.0,
                    explanation="No document text for legal term analysis",
                    details={}
                )
            
            doc_text_lower = doc_text.lower()
            
            # Calculate legal term matches
            total_weight = 0.0
            matched_weight = 0.0
            category_matches = defaultdict(int)
            
            # Check each category of legal terms
            for category, terms in self.legal_term_weights.items():
                category_weight = self._get_category_weight(category)
                
                for term in terms:
                    total_weight += category_weight
                    
                    # Check if term appears in document
                    if term.lower() in doc_text_lower:
                        matched_weight += category_weight
                        category_matches[category] += 1
            
            # Calculate legal concept matches
            concept_score = 0.0
            if query_analysis.legal_concepts:
                concept_matches = 0
                for concept, relevance in query_analysis.legal_concepts.items():
                    if concept.lower() in doc_text_lower:
                        concept_matches += 1
                        concept_score += relevance
                
                concept_score /= len(query_analysis.legal_concepts)
            
            # Combined legal term score
            if total_weight > 0:
                term_score = matched_weight / total_weight
            else:
                term_score = 0.0
            
            final_score = (term_score * 0.7) + (concept_score * 0.3)
            confidence = min(matched_weight / max(total_weight * 0.5, 1), 1.0)
            
            explanation = f"Legal terms: {sum(category_matches.values())} matches"
            if query_analysis.legal_concepts:
                explanation += f", {len([c for c in query_analysis.legal_concepts if c.lower() in doc_text_lower])} concepts"
            
            return RankingScore(
                feature=RankingFeature.LEGAL_TERM_MATCH,
                score=final_score,
                weight=self.default_feature_weights[RankingFeature.LEGAL_TERM_MATCH],
                confidence=confidence,
                explanation=explanation,
                details={
                    "category_matches": dict(category_matches),
                    "term_score": term_score,
                    "concept_score": concept_score,
                    "total_legal_terms": sum(category_matches.values())
                }
            )
            
        except Exception as e:
            logger.error(f"Legal term relevance calculation failed: {str(e)}")
            return RankingScore(
                feature=RankingFeature.LEGAL_TERM_MATCH,
                score=0.0,
                weight=self.default_feature_weights[RankingFeature.LEGAL_TERM_MATCH],
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _calculate_enhanced_authority_score(
        self,
        document: UnifiedDocument
    ) -> RankingScore:
        """Calculate enhanced authority score based on court hierarchy and other factors"""
        try:
            base_score = document.authority_score
            
            # Court hierarchy bonus
            court_bonus = 0.0
            if document.court:
                court_lower = document.court.lower()
                
                # Identify court type and assign hierarchy score
                for court_type, hierarchy_score in self.court_hierarchy.items():
                    if self._matches_court_type(court_lower, court_type):
                        court_bonus = hierarchy_score / 10.0  # Normalize to 0-1
                        break
            
            # Citation count bonus (if available)
            citation_bonus = 0.0
            if hasattr(document, 'citation_count') and document.citation_count:
                # Logarithmic scaling for citation count
                citation_bonus = min(math.log(document.citation_count + 1) / 10.0, 0.3)
            
            # Provider authority bonus
            provider_bonus = self._get_provider_authority_bonus(document.source_provider)
            
            # Combined authority score
            enhanced_score = min(
                base_score + court_bonus + citation_bonus + provider_bonus,
                1.0
            )
            
            confidence = 0.8 if document.court else 0.5
            
            explanation = f"Authority: {enhanced_score:.2f}"
            if court_bonus > 0:
                explanation += f" (court: +{court_bonus:.2f})"
            if citation_bonus > 0:
                explanation += f" (citations: +{citation_bonus:.2f})"
            
            return RankingScore(
                feature=RankingFeature.AUTHORITY_SCORE,
                score=enhanced_score,
                weight=self.default_feature_weights[RankingFeature.AUTHORITY_SCORE],
                confidence=confidence,
                explanation=explanation,
                details={
                    "base_score": base_score,
                    "court_bonus": court_bonus,
                    "citation_bonus": citation_bonus,
                    "provider_bonus": provider_bonus,
                    "court": document.court
                }
            )
            
        except Exception as e:
            logger.error(f"Enhanced authority score calculation failed: {str(e)}")
            return RankingScore(
                feature=RankingFeature.AUTHORITY_SCORE,
                score=document.authority_score,
                weight=self.default_feature_weights[RankingFeature.AUTHORITY_SCORE],
                confidence=0.5,
                explanation=f"Basic authority score: {document.authority_score:.2f}",
                details={}
            )
    
    async def _calculate_enhanced_recency_score(
        self,
        document: UnifiedDocument,
        query_analysis: QueryAnalysis
    ) -> RankingScore:
        """Calculate enhanced recency score considering legal context"""
        try:
            base_score = document.recency_score
            doc_date = document.decision_date or document.publication_date
            
            if not doc_date:
                return RankingScore(
                    feature=RankingFeature.RECENCY_SCORE,
                    score=0.5,  # Neutral score for unknown dates
                    weight=self.default_feature_weights[RankingFeature.RECENCY_SCORE],
                    confidence=0.0,
                    explanation="No date information available",
                    details={}
                )
            
            today = date.today()
            years_old = (today - doc_date).days / 365.25
            
            # Context-aware recency scoring
            enhanced_score = base_score
            
            # Adjust based on document type
            if document.document_type == ContentType.CASES:
                # Recent cases are often more relevant for precedential value
                if years_old <= 5:
                    enhanced_score *= 1.2
                elif years_old <= 15:
                    enhanced_score *= 1.0
                else:
                    # Very old cases might be landmark decisions
                    if document.authority_score > 0.8:
                        enhanced_score *= 1.1  # Landmark case bonus
            
            elif document.document_type == ContentType.STATUTES:
                # Statutes remain relevant longer but recent amendments are important
                if years_old <= 2:
                    enhanced_score *= 1.1
            
            elif document.document_type == ContentType.REGULATIONS:
                # Recent regulations are often more relevant
                if years_old <= 3:
                    enhanced_score *= 1.3
                elif years_old > 10:
                    enhanced_score *= 0.8
            
            # Query temporal context adjustment
            if query_analysis.temporal_hints:
                if 'recent' in query_analysis.temporal_hints and years_old <= 5:
                    enhanced_score *= 1.2
                elif 'historical' in query_analysis.temporal_hints and years_old > 20:
                    enhanced_score *= 1.1
            
            enhanced_score = min(enhanced_score, 1.0)
            confidence = 0.9  # High confidence when we have date information
            
            return RankingScore(
                feature=RankingFeature.RECENCY_SCORE,
                score=enhanced_score,
                weight=self.default_feature_weights[RankingFeature.RECENCY_SCORE],
                confidence=confidence,
                explanation=f"Recency: {years_old:.1f} years old",
                details={
                    "base_score": base_score,
                    "years_old": years_old,
                    "document_date": doc_date.isoformat(),
                    "document_type": document.document_type.value if document.document_type else None
                }
            )
            
        except Exception as e:
            logger.error(f"Enhanced recency score calculation failed: {str(e)}")
            return RankingScore(
                feature=RankingFeature.RECENCY_SCORE,
                score=document.recency_score,
                weight=self.default_feature_weights[RankingFeature.RECENCY_SCORE],
                confidence=0.5,
                explanation=f"Basic recency score: {document.recency_score:.2f}",
                details={}
            )
    
    async def _calculate_citation_relevance(
        self,
        document: UnifiedDocument,
        query_analysis: QueryAnalysis
    ) -> RankingScore:
        """Calculate relevance based on citations and legal references"""
        try:
            score = 0.0
            details = {}
            
            # Citation availability bonus
            if document.citation:
                score += 0.3
                details["has_citation"] = True
                
                # Citation format quality (more complete citations score higher)
                citation_components = len([
                    comp for comp in [
                        re.search(r'\d+', document.citation),  # Volume
                        re.search(r'\w+\.', document.citation),  # Reporter
                        re.search(r'\d+$', document.citation)   # Page
                    ] if comp
                ])
                score += (citation_components / 3) * 0.2
                details["citation_completeness"] = citation_components / 3
            
            # Cited cases analysis
            if document.cited_cases:
                # More cited cases suggests more comprehensive analysis
                cited_count = len(document.cited_cases)
                citation_density = min(cited_count / 10, 0.3)  # Cap at 0.3
                score += citation_density
                details["cited_cases_count"] = cited_count
                details["citation_density"] = citation_density
            
            # Citing cases analysis (authority indicator)
            if document.citing_cases:
                citing_count = len(document.citing_cases)
                authority_from_citations = min(citing_count / 20, 0.2)  # Cap at 0.2
                score += authority_from_citations
                details["citing_cases_count"] = citing_count
                details["authority_from_citations"] = authority_from_citations
            
            # Query-specific citation relevance
            query_lower = query_analysis.query_text.lower()
            if any(cite_term in query_lower for cite_term in ['cite', 'citation', 'cited', 'citing']):
                score *= 1.2  # Boost when query explicitly mentions citations
                details["citation_query_bonus"] = True
            
            final_score = min(score, 1.0)
            confidence = 0.7 if (document.citation or document.cited_cases or document.citing_cases) else 0.3
            
            explanation = f"Citation relevance: {final_score:.2f}"
            if document.citation:
                explanation += " (has citation)"
            if document.cited_cases:
                explanation += f" (cites {len(document.cited_cases)})"
            if document.citing_cases:
                explanation += f" (cited by {len(document.citing_cases)})"
            
            return RankingScore(
                feature=RankingFeature.CITATION_RELEVANCE,
                score=final_score,
                weight=self.default_feature_weights[RankingFeature.CITATION_RELEVANCE],
                confidence=confidence,
                explanation=explanation,
                details=details
            )
            
        except Exception as e:
            logger.error(f"Citation relevance calculation failed: {str(e)}")
            return RankingScore(
                feature=RankingFeature.CITATION_RELEVANCE,
                score=0.0,
                weight=self.default_feature_weights[RankingFeature.CITATION_RELEVANCE],
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _calculate_completeness_score(
        self,
        document: UnifiedDocument
    ) -> RankingScore:
        """Calculate document completeness score"""
        try:
            completeness_factors = []
            
            # Full text availability (most important)
            if document.full_text_available and document.full_text:
                text_length = len(document.full_text)
                if text_length > 5000:
                    completeness_factors.append(('full_text', 1.0, 0.4))
                elif text_length > 1000:
                    completeness_factors.append(('full_text', 0.8, 0.4))
                else:
                    completeness_factors.append(('full_text', 0.5, 0.4))
            elif document.full_text_available:
                completeness_factors.append(('full_text_available', 0.3, 0.4))
            
            # Summary availability
            if document.summary:
                summary_quality = min(len(document.summary) / 500, 1.0)
                completeness_factors.append(('summary', summary_quality, 0.2))
            
            # Metadata completeness
            metadata_score = 0.0
            metadata_count = 0
            
            for field, weight in [
                (document.citation, 0.15),
                (document.court, 0.15),
                (document.jurisdiction, 0.1),
                (document.decision_date, 0.1),
                (document.legal_topics, 0.1),
                (document.parties, 0.1),
                (document.judges, 0.05)
            ]:
                if field:
                    metadata_score += weight
                    metadata_count += 1
            
            if metadata_count > 0:
                completeness_factors.append(('metadata', metadata_score, 0.2))
            
            # Structured content (headnotes, key passages)
            structured_score = 0.0
            if document.headnotes:
                structured_score += 0.5
            if document.key_passages:
                structured_score += 0.5
            
            if structured_score > 0:
                completeness_factors.append(('structured', structured_score, 0.2))
            
            # Calculate weighted completeness score
            if completeness_factors:
                total_weight = sum(weight for _, _, weight in completeness_factors)
                weighted_sum = sum(score * weight for _, score, weight in completeness_factors)
                final_score = weighted_sum / total_weight if total_weight > 0 else 0.0
            else:
                final_score = 0.0
            
            confidence = min(metadata_count / 7, 1.0)  # Based on metadata richness
            
            explanation = f"Completeness: {final_score:.2f}"
            if document.full_text_available:
                explanation += " (full text)"
            if document.summary:
                explanation += " (summary)"
            if metadata_count > 4:
                explanation += " (rich metadata)"
            
            return RankingScore(
                feature=RankingFeature.COMPLETENESS_SCORE,
                score=final_score,
                weight=self.default_feature_weights[RankingFeature.COMPLETENESS_SCORE],
                confidence=confidence,
                explanation=explanation,
                details={
                    "completeness_factors": [(name, score) for name, score, _ in completeness_factors],
                    "metadata_count": metadata_count,
                    "has_full_text": document.full_text_available,
                    "has_summary": bool(document.summary)
                }
            )
            
        except Exception as e:
            logger.error(f"Completeness score calculation failed: {str(e)}")
            return RankingScore(
                feature=RankingFeature.COMPLETENESS_SCORE,
                score=0.5,
                weight=self.default_feature_weights[RankingFeature.COMPLETENESS_SCORE],
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _calculate_jurisdiction_match(
        self,
        document: UnifiedDocument,
        query: UnifiedQuery,
        query_analysis: QueryAnalysis
    ) -> RankingScore:
        """Calculate jurisdiction matching score"""
        try:
            if not document.jurisdiction and not query.jurisdictions and not query_analysis.jurisdiction_hints:
                # No jurisdiction information available
                return RankingScore(
                    feature=RankingFeature.JURISDICTION_MATCH,
                    score=0.5,  # Neutral score
                    weight=self.default_feature_weights[RankingFeature.JURISDICTION_MATCH],
                    confidence=0.0,
                    explanation="No jurisdiction information",
                    details={}
                )
            
            score = 0.0
            matches = []
            
            doc_jurisdiction = document.jurisdiction.lower() if document.jurisdiction else ""
            
            # Check explicit query jurisdictions
            if query.jurisdictions:
                for query_juris in query.jurisdictions:
                    if query_juris.lower() in doc_jurisdiction or doc_jurisdiction in query_juris.lower():
                        score = 1.0
                        matches.append(f"Explicit: {query_juris}")
                        break
                    # Partial match
                    elif any(word in doc_jurisdiction for word in query_juris.lower().split()):
                        score = max(score, 0.7)
                        matches.append(f"Partial: {query_juris}")
            
            # Check jurisdiction hints from query text
            if query_analysis.jurisdiction_hints and score < 1.0:
                for hint in query_analysis.jurisdiction_hints:
                    if hint.lower() in doc_jurisdiction:
                        score = max(score, 0.8)
                        matches.append(f"Hint: {hint}")
            
            # Default scoring if no explicit preferences
            if not query.jurisdictions and not query_analysis.jurisdiction_hints:
                if doc_jurisdiction:
                    # Federal documents get slight preference for general queries
                    if 'federal' in doc_jurisdiction:
                        score = 0.6
                        matches.append("Federal default")
                    else:
                        score = 0.5
                        matches.append("State/local default")
                else:
                    score = 0.4
            
            confidence = 1.0 if matches else 0.0
            explanation = f"Jurisdiction: {', '.join(matches) if matches else 'no match'}"
            
            return RankingScore(
                feature=RankingFeature.JURISDICTION_MATCH,
                score=score,
                weight=self.default_feature_weights[RankingFeature.JURISDICTION_MATCH],
                confidence=confidence,
                explanation=explanation,
                details={
                    "document_jurisdiction": document.jurisdiction,
                    "query_jurisdictions": query.jurisdictions,
                    "jurisdiction_hints": query_analysis.jurisdiction_hints,
                    "matches": matches
                }
            )
            
        except Exception as e:
            logger.error(f"Jurisdiction match calculation failed: {str(e)}")
            return RankingScore(
                feature=RankingFeature.JURISDICTION_MATCH,
                score=0.5,
                weight=self.default_feature_weights[RankingFeature.JURISDICTION_MATCH],
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _calculate_content_type_match(
        self,
        document: UnifiedDocument,
        query: UnifiedQuery,
        query_analysis: QueryAnalysis
    ) -> RankingScore:
        """Calculate content type matching score"""
        try:
            if not document.document_type and not query.content_types and not query_analysis.document_type_hints:
                return RankingScore(
                    feature=RankingFeature.CONTENT_TYPE_MATCH,
                    score=0.5,
                    weight=self.default_feature_weights[RankingFeature.CONTENT_TYPE_MATCH],
                    confidence=0.0,
                    explanation="No content type information",
                    details={}
                )
            
            score = 0.5  # Default neutral score
            explanation = "Content type: "
            
            # Check explicit content type preferences
            if query.content_types and document.document_type:
                if document.document_type in query.content_types:
                    score = 1.0
                    explanation += f"exact match ({document.document_type.value})"
                else:
                    score = 0.3
                    explanation += f"no match ({document.document_type.value} not in {[ct.value for ct in query.content_types]})"
            
            # Check document type hints from query
            elif query_analysis.document_type_hints and document.document_type:
                if document.document_type in query_analysis.document_type_hints:
                    score = 0.8
                    explanation += f"hint match ({document.document_type.value})"
                else:
                    score = 0.4
                    explanation += f"hint mismatch"
            
            # Default preferences when no explicit type specified
            elif not query.content_types and not query_analysis.document_type_hints:
                if document.document_type == ContentType.CASES:
                    score = 0.7  # Cases are often what users want
                    explanation += "default case preference"
                elif document.document_type in [ContentType.STATUTES, ContentType.REGULATIONS]:
                    score = 0.6  # Primary law is valuable
                    explanation += "primary law default"
                else:
                    score = 0.5
                    explanation += "secondary source default"
            
            confidence = 1.0 if (query.content_types or query_analysis.document_type_hints) else 0.3
            
            return RankingScore(
                feature=RankingFeature.CONTENT_TYPE_MATCH,
                score=score,
                weight=self.default_feature_weights[RankingFeature.CONTENT_TYPE_MATCH],
                confidence=confidence,
                explanation=explanation,
                details={
                    "document_type": document.document_type.value if document.document_type else None,
                    "query_content_types": [ct.value for ct in query.content_types] if query.content_types else [],
                    "type_hints": [ct.value for ct in query_analysis.document_type_hints]
                }
            )
            
        except Exception as e:
            logger.error(f"Content type match calculation failed: {str(e)}")
            return RankingScore(
                feature=RankingFeature.CONTENT_TYPE_MATCH,
                score=0.5,
                weight=self.default_feature_weights[RankingFeature.CONTENT_TYPE_MATCH],
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _calculate_query_coverage(
        self,
        document: UnifiedDocument,
        query_analysis: QueryAnalysis
    ) -> RankingScore:
        """Calculate how well the document covers the query terms"""
        try:
            doc_text = self._get_document_text(document)
            if not doc_text or not query_analysis.query_terms:
                return RankingScore(
                    feature=RankingFeature.QUERY_COVERAGE,
                    score=0.0,
                    weight=self.default_feature_weights[RankingFeature.QUERY_COVERAGE],
                    confidence=0.0,
                    explanation="No text or query terms for coverage analysis",
                    details={}
                )
            
            doc_text_lower = doc_text.lower()
            
            # Calculate coverage of query terms
            covered_terms = 0
            total_weight = 0.0
            covered_weight = 0.0
            
            for term, weight in query_analysis.query_terms.items():
                total_weight += weight
                if term.lower() in doc_text_lower:
                    covered_terms += 1
                    covered_weight += weight
            
            # Coverage metrics
            term_coverage = covered_terms / len(query_analysis.query_terms)
            weight_coverage = covered_weight / total_weight if total_weight > 0 else 0.0
            
            # Combined coverage score
            coverage_score = (term_coverage * 0.6) + (weight_coverage * 0.4)
            
            # Bonus for covering important legal concepts
            concept_coverage = 0.0
            if query_analysis.legal_concepts:
                covered_concepts = sum(
                    1 for concept in query_analysis.legal_concepts
                    if concept.lower() in doc_text_lower
                )
                concept_coverage = covered_concepts / len(query_analysis.legal_concepts)
            
            final_score = (coverage_score * 0.8) + (concept_coverage * 0.2)
            confidence = min(covered_terms / max(len(query_analysis.query_terms) * 0.5, 1), 1.0)
            
            explanation = f"Query coverage: {covered_terms}/{len(query_analysis.query_terms)} terms"
            if query_analysis.legal_concepts:
                covered_concepts_count = sum(
                    1 for concept in query_analysis.legal_concepts
                    if concept.lower() in doc_text_lower
                )
                explanation += f", {covered_concepts_count}/{len(query_analysis.legal_concepts)} concepts"
            
            return RankingScore(
                feature=RankingFeature.QUERY_COVERAGE,
                score=final_score,
                weight=self.default_feature_weights[RankingFeature.QUERY_COVERAGE],
                confidence=confidence,
                explanation=explanation,
                details={
                    "covered_terms": covered_terms,
                    "total_terms": len(query_analysis.query_terms),
                    "term_coverage": term_coverage,
                    "weight_coverage": weight_coverage,
                    "concept_coverage": concept_coverage
                }
            )
            
        except Exception as e:
            logger.error(f"Query coverage calculation failed: {str(e)}")
            return RankingScore(
                feature=RankingFeature.QUERY_COVERAGE,
                score=0.0,
                weight=self.default_feature_weights[RankingFeature.QUERY_COVERAGE],
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    async def _calculate_semantic_similarity(
        self,
        document: UnifiedDocument,
        query_analysis: QueryAnalysis
    ) -> RankingScore:
        """Calculate semantic similarity (placeholder for future ML implementation)"""
        # This is a placeholder for semantic similarity using embeddings/ML models
        # For now, return a basic score based on title and summary similarity
        
        try:
            # Simple semantic similarity based on content overlap
            doc_content = f"{document.title} {document.summary or ''}"
            if not doc_content.strip():
                return RankingScore(
                    feature=RankingFeature.SEMANTIC_SIMILARITY,
                    score=0.0,
                    weight=self.default_feature_weights[RankingFeature.SEMANTIC_SIMILARITY],
                    confidence=0.0,
                    explanation="No content for semantic analysis",
                    details={}
                )
            
            # Simple word overlap as proxy for semantic similarity
            doc_words = set(self._normalize_legal_text(doc_content).split())
            query_words = set(query_analysis.normalized_query.split())
            
            if not doc_words or not query_words:
                similarity = 0.0
            else:
                intersection = len(doc_words & query_words)
                union = len(doc_words | query_words)
                similarity = intersection / union if union > 0 else 0.0
            
            # Future: Replace with actual semantic embeddings
            # similarity = cosine_similarity(doc_embedding, query_embedding)
            
            confidence = 0.3  # Low confidence for simple word overlap
            explanation = f"Semantic similarity: {similarity:.2f} (word overlap)"
            
            return RankingScore(
                feature=RankingFeature.SEMANTIC_SIMILARITY,
                score=similarity,
                weight=self.default_feature_weights[RankingFeature.SEMANTIC_SIMILARITY],
                confidence=confidence,
                explanation=explanation,
                details={
                    "method": "word_overlap",
                    "doc_words": len(doc_words),
                    "query_words": len(query_words),
                    "intersection": len(doc_words & query_words) if doc_words and query_words else 0
                }
            )
            
        except Exception as e:
            logger.error(f"Semantic similarity calculation failed: {str(e)}")
            return RankingScore(
                feature=RankingFeature.SEMANTIC_SIMILARITY,
                score=0.0,
                weight=self.default_feature_weights[RankingFeature.SEMANTIC_SIMILARITY],
                confidence=0.0,
                explanation=f"Calculation error: {str(e)}",
                details={}
            )
    
    # Utility methods
    
    def _normalize_legal_text(self, text: str) -> str:
        """Normalize legal text for analysis"""
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove citations and case numbers
        normalized = re.sub(r'\([^)]*\)', '', normalized)
        normalized = re.sub(r'\[[^\]]*\]', '', normalized)
        normalized = re.sub(r'\bno\.\s*\d+[-–]?\d*\b', '', normalized)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _extract_weighted_terms(self, query_text: str) -> Dict[str, float]:
        """Extract and weight terms from query"""
        # Normalize and tokenize
        normalized = self._normalize_legal_text(query_text)
        terms = [term for term in normalized.split() if len(term) > 2]
        
        if not terms:
            return {}
        
        # Calculate term frequencies
        term_counts = Counter(terms)
        max_count = max(term_counts.values())
        
        # Weight terms based on frequency and legal importance
        weighted_terms = {}
        for term, count in term_counts.items():
            # Base weight from frequency
            tf_weight = count / max_count
            
            # Legal term boost
            legal_boost = 1.0
            for category, category_terms in self.legal_term_weights.items():
                if term in ' '.join(category_terms):
                    legal_boost = self._get_category_weight(category)
                    break
            
            weighted_terms[term] = tf_weight * legal_boost
        
        return weighted_terms
    
    def _extract_terms(self, text: str) -> Counter:
        """Extract meaningful terms from text"""
        # Simple tokenization and filtering
        terms = [term for term in text.split() if len(term) > 2]
        return Counter(terms)
    
    def _identify_legal_concepts(self, query_text: str) -> Dict[str, float]:
        """Identify legal concepts in query text"""
        concepts = {}
        query_lower = query_text.lower()
        
        # Check for legal concepts across all categories
        for category, terms in self.legal_term_weights.items():
            category_weight = self._get_category_weight(category)
            
            for term in terms:
                if term in query_lower:
                    concepts[term] = category_weight
        
        return concepts
    
    def _detect_practice_areas(self, query_text: str) -> List[str]:
        """Detect practice areas from query text"""
        detected_areas = []
        query_lower = query_text.lower()
        
        for area, indicators in self.practice_area_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                detected_areas.append(area)
        
        return detected_areas
    
    def _infer_document_types(self, query: UnifiedQuery) -> List[ContentType]:
        """Infer document types from query"""
        if query.content_types:
            return query.content_types
        
        query_lower = query.query_text.lower()
        inferred_types = []
        
        # Document type keywords
        type_keywords = {
            ContentType.CASES: ['case', 'opinion', 'decision', 'court', 'judge', 'ruling'],
            ContentType.STATUTES: ['statute', 'law', 'code', 'usc', 'title'],
            ContentType.REGULATIONS: ['regulation', 'rule', 'cfr', 'federal register'],
            ContentType.LAW_REVIEWS: ['article', 'review', 'journal', 'comment'],
            ContentType.BRIEFS: ['brief', 'motion', 'petition', 'pleading']
        }
        
        for doc_type, keywords in type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                inferred_types.append(doc_type)
        
        return inferred_types
    
    def _extract_jurisdiction_hints(self, query_text: str, explicit_jurisdictions: List[str]) -> List[str]:
        """Extract jurisdiction hints from query text"""
        hints = list(explicit_jurisdictions) if explicit_jurisdictions else []
        query_lower = query_text.lower()
        
        # Common jurisdiction indicators
        jurisdiction_indicators = [
            'federal', 'supreme court', 'circuit', 'district',
            'california', 'new york', 'texas', 'florida', 'illinois',
            'ninth circuit', 'second circuit', 'dc circuit'
        ]
        
        for indicator in jurisdiction_indicators:
            if indicator in query_lower and indicator not in hints:
                hints.append(indicator)
        
        return hints
    
    def _analyze_temporal_context(self, query: UnifiedQuery) -> Dict[str, Any]:
        """Analyze temporal context from query"""
        temporal_hints = {}
        query_lower = query.query_text.lower()
        
        # Temporal keywords
        if any(word in query_lower for word in ['recent', 'latest', 'current', 'new']):
            temporal_hints['recent'] = True
        
        if any(word in query_lower for word in ['historical', 'old', 'vintage', 'landmark']):
            temporal_hints['historical'] = True
        
        # Date range information
        if query.date_from or query.date_to:
            temporal_hints['date_range'] = {
                'from': query.date_from.isoformat() if query.date_from else None,
                'to': query.date_to.isoformat() if query.date_to else None
            }
        
        return temporal_hints
    
    def _calculate_query_complexity(self, query_text: str) -> float:
        """Calculate query complexity score"""
        # Basic complexity based on length and structure
        words = query_text.split()
        
        complexity = len(words) / 10.0  # Base complexity from word count
        
        # Boolean operators increase complexity
        boolean_ops = ['AND', 'OR', 'NOT', 'and', 'or', 'not']
        for op in boolean_ops:
            if op in query_text:
                complexity += 0.5
        
        # Quotation marks (phrase searching)
        if '"' in query_text:
            complexity += 0.3
        
        # Legal citations increase complexity
        if re.search(r'\d+\s+\w+\.?\s+\d+', query_text):
            complexity += 0.5
        
        return min(complexity, 5.0)  # Cap at 5.0
    
    def _get_category_weight(self, category: str) -> float:
        """Get weight for legal term category"""
        weights = {
            'procedural_high': 2.0,
            'procedural_medium': 1.5,
            'substantive_high': 2.5,
            'substantive_medium': 1.8,
            'legal_standards': 2.2,
            'remedies': 1.7
        }
        return weights.get(category, 1.0)
    
    def _matches_court_type(self, court_name: str, court_type: str) -> bool:
        """Check if court name matches court type"""
        type_indicators = {
            'supreme_court_us': ['united states supreme court', 'us supreme court', 'scotus'],
            'circuit_court': ['circuit', 'court of appeals'],
            'district_court': ['district court'],
            'state_supreme': ['supreme court'],
            'state_appellate': ['court of appeals', 'appellate'],
            'state_trial': ['superior court', 'county court', 'trial court'],
            'administrative': ['administrative', 'commission'],
            'bankruptcy': ['bankruptcy'],
            'tax_court': ['tax court']
        }
        
        indicators = type_indicators.get(court_type, [])
        return any(indicator in court_name for indicator in indicators)
    
    def _get_provider_authority_bonus(self, provider: Optional[DatabaseProvider]) -> float:
        """Get authority bonus based on provider"""
        if not provider:
            return 0.0
        
        provider_bonuses = {
            DatabaseProvider.SUPREMECOURT_GOV: 0.2,
            DatabaseProvider.GOVINFO: 0.15,
            DatabaseProvider.CONGRESS_GOV: 0.1,
            DatabaseProvider.COURTLISTENER: 0.05,
            DatabaseProvider.HEINONLINE: 0.1,
            DatabaseProvider.WESTLAW: 0.1,
            DatabaseProvider.LEXISNEXIS: 0.1
        }
        
        return provider_bonuses.get(provider, 0.0)
    
    def _get_document_text(self, document: UnifiedDocument) -> str:
        """Get searchable text from document"""
        # Combine title, summary, and full text
        text_parts = []
        
        if document.title:
            text_parts.append(document.title)
        
        if document.summary:
            text_parts.append(document.summary)
        
        if document.full_text:
            # For very long documents, truncate to avoid performance issues
            if len(document.full_text) > 20000:
                text_parts.append(document.full_text[:20000])
            else:
                text_parts.append(document.full_text)
        
        # Add legal topics and headnotes
        if document.legal_topics:
            text_parts.extend(document.legal_topics)
        
        if document.headnotes:
            text_parts.extend(document.headnotes[:5])  # Limit to first 5 headnotes
        
        return ' '.join(text_parts)
    
    def _calculate_ranking_confidence(self, individual_scores: List[RankingScore]) -> float:
        """Calculate confidence in ranking based on individual score consistency"""
        if not individual_scores:
            return 0.0
        
        # Calculate average confidence
        avg_confidence = sum(score.confidence for score in individual_scores) / len(individual_scores)
        
        # Calculate score variance (lower variance = higher confidence)
        scores = [score.score for score in individual_scores]
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        consistency = 1.0 - min(variance, 1.0)
        
        # Combined confidence
        return (avg_confidence * 0.7) + (consistency * 0.3)
    
    def _normalize_rankings(self, rankings: List[DocumentRanking]) -> List[DocumentRanking]:
        """Normalize ranking scores across all documents"""
        if not rankings:
            return rankings
        
        # Find min and max scores
        scores = [r.final_score for r in rankings]
        min_score = min(scores)
        max_score = max(scores)
        
        # Normalize scores to 0-1 range
        score_range = max_score - min_score
        if score_range > 0:
            for ranking in rankings:
                ranking.normalized_score = (ranking.final_score - min_score) / score_range
        else:
            # All scores are the same
            for ranking in rankings:
                ranking.normalized_score = 0.5
        
        return rankings
    
    async def _update_document_frequencies(self, documents: List[UnifiedDocument]):
        """Update document frequency statistics for TF-IDF calculation"""
        try:
            # This is a simplified version - in production, would use persistent storage
            self.total_documents = len(documents)
            
            # Count term frequencies across all documents
            for doc in documents:
                doc_text = self._get_document_text(doc)
                if doc_text:
                    normalized = self._normalize_legal_text(doc_text)
                    terms = set(self._extract_terms(normalized).keys())
                    
                    for term in terms:
                        self.document_frequencies[term] += 1
        
        except Exception as e:
            logger.error(f"Document frequency update failed: {str(e)}")