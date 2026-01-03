"""
Composite Ranking Engine

Advanced composite ranking system that intelligently combines multiple
scoring algorithms including deduplication, relevance, authority, and
legal context analysis to produce optimal document rankings.
"""

import asyncio
import logging
import math
from datetime import datetime, date
from typing import Dict, List, Optional, Set, Tuple, Any, NamedTuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum

from .database_models import UnifiedDocument, UnifiedQuery, UnifiedSearchResult, ContentType
from .deduplication_engine import DeduplicationEngine
from .relevance_ranking_engine import RelevanceRankingEngine, RankingFeature
from .authority_scoring_engine import AuthorityScoringEngine, AuthorityType, CourtLevel
from .legal_context_analyzer import LegalContextAnalyzer, LegalContextType

logger = logging.getLogger(__name__)


class RankingStrategy(Enum):
    """Different ranking strategies"""
    BALANCED = "balanced"
    AUTHORITY_FOCUSED = "authority_focused"
    RELEVANCE_FOCUSED = "relevance_focused"
    RECENCY_FOCUSED = "recency_focused"
    DIVERSITY_FOCUSED = "diversity_focused"
    RESEARCH_FOCUSED = "research_focused"
    PRACTICE_FOCUSED = "practice_focused"


class RankingContext(Enum):
    """Context for ranking optimization"""
    ACADEMIC_RESEARCH = "academic_research"
    LEGAL_PRACTICE = "legal_practice"
    CASE_PREPARATION = "case_preparation"
    STATUTORY_ANALYSIS = "statutory_analysis"
    HISTORICAL_RESEARCH = "historical_research"
    CURRENT_LAW = "current_law"
    COMPARATIVE_ANALYSIS = "comparative_analysis"


@dataclass
class CompositeScore:
    """Complete composite scoring result"""
    document_id: str
    final_score: float
    component_scores: Dict[str, float]
    component_weights: Dict[str, float]
    ranking_explanation: List[str]
    confidence: float
    authority_assessment: Optional[Any]  # AuthorityAssessment
    relevance_ranking: Optional[Any]     # DocumentRanking
    legal_context: Optional[Any]         # LegalContextAnalysis
    deduplication_info: Optional[Dict[str, Any]]


@dataclass
class RankingConfiguration:
    """Configuration for composite ranking"""
    strategy: RankingStrategy
    context: Optional[RankingContext]
    
    # Component weights (should sum to 1.0)
    relevance_weight: float = 0.35
    authority_weight: float = 0.30
    recency_weight: float = 0.15
    completeness_weight: float = 0.10
    diversity_weight: float = 0.05
    context_weight: float = 0.05
    
    # Quality thresholds
    min_relevance_threshold: float = 0.2
    min_authority_threshold: float = 0.1
    min_confidence_threshold: float = 0.3
    
    # Diversity parameters
    max_same_provider_ratio: float = 0.6
    max_same_court_ratio: float = 0.7
    max_same_jurisdiction_ratio: float = 0.8
    
    # Advanced options
    boost_landmark_cases: bool = True
    penalize_outdated_secondary: bool = True
    prioritize_primary_authority: bool = True
    consider_citation_networks: bool = True


class CompositeRankingEngine:
    """
    Advanced composite ranking engine that intelligently combines multiple
    scoring systems to produce optimal legal document rankings.
    """
    
    def __init__(self):
        # Initialize component engines
        self.deduplication_engine = DeduplicationEngine()
        self.relevance_engine = RelevanceRankingEngine()
        self.authority_engine = AuthorityScoringEngine()
        self.context_analyzer = LegalContextAnalyzer()
        
        # Predefined ranking strategies
        self.ranking_strategies = {
            RankingStrategy.BALANCED: RankingConfiguration(
                strategy=RankingStrategy.BALANCED,
                relevance_weight=0.35,
                authority_weight=0.30,
                recency_weight=0.15,
                completeness_weight=0.10,
                diversity_weight=0.05,
                context_weight=0.05
            ),
            
            RankingStrategy.AUTHORITY_FOCUSED: RankingConfiguration(
                strategy=RankingStrategy.AUTHORITY_FOCUSED,
                relevance_weight=0.25,
                authority_weight=0.45,
                recency_weight=0.10,
                completeness_weight=0.10,
                diversity_weight=0.05,
                context_weight=0.05,
                boost_landmark_cases=True,
                prioritize_primary_authority=True
            ),
            
            RankingStrategy.RELEVANCE_FOCUSED: RankingConfiguration(
                strategy=RankingStrategy.RELEVANCE_FOCUSED,
                relevance_weight=0.50,
                authority_weight=0.20,
                recency_weight=0.10,
                completeness_weight=0.10,
                diversity_weight=0.05,
                context_weight=0.05
            ),
            
            RankingStrategy.RECENCY_FOCUSED: RankingConfiguration(
                strategy=RankingStrategy.RECENCY_FOCUSED,
                relevance_weight=0.30,
                authority_weight=0.20,
                recency_weight=0.35,
                completeness_weight=0.08,
                diversity_weight=0.04,
                context_weight=0.03,
                penalize_outdated_secondary=True
            ),
            
            RankingStrategy.DIVERSITY_FOCUSED: RankingConfiguration(
                strategy=RankingStrategy.DIVERSITY_FOCUSED,
                relevance_weight=0.30,
                authority_weight=0.25,
                recency_weight=0.15,
                completeness_weight=0.10,
                diversity_weight=0.15,
                context_weight=0.05,
                max_same_provider_ratio=0.4,
                max_same_court_ratio=0.5,
                max_same_jurisdiction_ratio=0.6
            ),
            
            RankingStrategy.RESEARCH_FOCUSED: RankingConfiguration(
                strategy=RankingStrategy.RESEARCH_FOCUSED,
                relevance_weight=0.25,
                authority_weight=0.35,
                recency_weight=0.05,
                completeness_weight=0.20,
                diversity_weight=0.10,
                context_weight=0.05,
                boost_landmark_cases=True,
                consider_citation_networks=True
            ),
            
            RankingStrategy.PRACTICE_FOCUSED: RankingConfiguration(
                strategy=RankingStrategy.PRACTICE_FOCUSED,
                relevance_weight=0.40,
                authority_weight=0.25,
                recency_weight=0.20,
                completeness_weight=0.10,
                diversity_weight=0.03,
                context_weight=0.02,
                prioritize_primary_authority=True
            )
        }
        
        logger.info("Composite ranking engine initialized")
    
    async def rank_documents(
        self,
        documents: List[UnifiedDocument],
        query: UnifiedQuery,
        strategy: RankingStrategy = RankingStrategy.BALANCED,
        custom_config: Optional[RankingConfiguration] = None,
        enable_deduplication: bool = True
    ) -> Tuple[List[CompositeScore], Dict[str, Any]]:
        """
        Perform comprehensive composite ranking of documents
        """
        try:
            if not documents:
                return [], {}
            
            logger.info(f"Starting composite ranking of {len(documents)} documents")
            logger.info(f"Strategy: {strategy.value}, Deduplication: {enable_deduplication}")
            
            # Get ranking configuration
            config = custom_config or self.ranking_strategies.get(strategy, self.ranking_strategies[RankingStrategy.BALANCED])
            
            # Step 1: Deduplication (optional)
            if enable_deduplication:
                start_time = datetime.utcnow()
                deduplicated_docs = await self.deduplication_engine.deduplicate_documents(
                    documents, threshold=0.85
                )
                dedup_time = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"Deduplication: {len(documents)} -> {len(deduplicated_docs)} documents ({dedup_time:.2f}s)")
                
                # Track which documents were removed
                dedup_info = {
                    "original_count": len(documents),
                    "deduplicated_count": len(deduplicated_docs),
                    "removed_count": len(documents) - len(deduplicated_docs),
                    "deduplication_time": dedup_time
                }
            else:
                deduplicated_docs = documents
                dedup_info = {"enabled": False}
            
            # Step 2: Analyze query context
            query_context = await self.context_analyzer.analyze_legal_context(
                query.query_text, query_context=query
            )
            
            # Step 3: Adjust configuration based on query context
            adjusted_config = self._adjust_config_for_context(config, query_context, query)
            
            # Step 4: Calculate individual component scores
            composite_scores = []
            
            for doc in deduplicated_docs:
                try:
                    composite_score = await self._calculate_composite_score(
                        doc, query, query_context, adjusted_config
                    )
                    composite_scores.append(composite_score)
                except Exception as e:
                    logger.error(f"Error calculating composite score for document {doc.source_document_id}: {str(e)}")
                    # Create fallback score
                    fallback_score = CompositeScore(
                        document_id=doc.source_document_id or str(id(doc)),
                        final_score=0.5,
                        component_scores={"error": 0.5},
                        component_weights={"error": 1.0},
                        ranking_explanation=[f"Scoring error: {str(e)}"],
                        confidence=0.0,
                        authority_assessment=None,
                        relevance_ranking=None,
                        legal_context=None,
                        deduplication_info=None
                    )
                    composite_scores.append(fallback_score)
            
            # Step 5: Apply diversity optimization
            if adjusted_config.diversity_weight > 0.01:
                composite_scores = await self._optimize_for_diversity(
                    composite_scores, deduplicated_docs, adjusted_config
                )
            
            # Step 6: Final ranking and quality filtering
            final_rankings = self._apply_final_ranking(composite_scores, adjusted_config)
            
            # Step 7: Generate ranking metadata
            ranking_metadata = {
                "strategy": strategy.value,
                "configuration": {
                    "relevance_weight": adjusted_config.relevance_weight,
                    "authority_weight": adjusted_config.authority_weight,
                    "recency_weight": adjusted_config.recency_weight,
                    "diversity_weight": adjusted_config.diversity_weight
                },
                "deduplication": dedup_info,
                "query_context": {
                    "primary_practice_area": query_context.practice_area_analysis.primary_area,
                    "legal_concepts": len(query_context.legal_concepts),
                    "complexity": query_context.complexity_score
                },
                "ranking_stats": {
                    "total_documents": len(final_rankings),
                    "avg_score": sum(score.final_score for score in final_rankings) / len(final_rankings) if final_rankings else 0,
                    "avg_confidence": sum(score.confidence for score in final_rankings) / len(final_rankings) if final_rankings else 0,
                    "high_authority_count": sum(1 for score in final_rankings if score.component_scores.get("authority", 0) > 0.8),
                    "high_relevance_count": sum(1 for score in final_rankings if score.component_scores.get("relevance", 0) > 0.8)
                }
            }
            
            logger.info(f"Composite ranking completed: {len(final_rankings)} documents ranked")
            return final_rankings, ranking_metadata
            
        except Exception as e:
            logger.error(f"Composite ranking failed: {str(e)}")
            return [], {"error": str(e)}
    
    async def _calculate_composite_score(
        self,
        document: UnifiedDocument,
        query: UnifiedQuery,
        query_context: Any,
        config: RankingConfiguration
    ) -> CompositeScore:
        """Calculate composite score for a single document"""
        try:
            doc_id = document.source_document_id or str(id(document))
            component_scores = {}
            explanations = []
            
            # 1. Relevance scoring
            relevance_rankings = await self.relevance_engine.rank_documents([document], query)
            relevance_score = relevance_rankings[0].final_score if relevance_rankings else 0.5
            component_scores["relevance"] = relevance_score
            
            if relevance_score > 0.7:
                explanations.append(f"High relevance ({relevance_score:.2f})")
            
            # 2. Authority scoring
            authority_assessment = await self.authority_engine.calculate_authority_score(document)
            authority_score = authority_assessment.overall_authority
            component_scores["authority"] = authority_score
            
            if authority_score > 0.8:
                explanations.append(f"High authority ({authority_assessment.authority_type.value})")
            
            # 3. Recency scoring
            recency_score = await self._calculate_enhanced_recency(document, query_context)
            component_scores["recency"] = recency_score
            
            # 4. Completeness scoring
            completeness_score = self._calculate_completeness_score(document)
            component_scores["completeness"] = completeness_score
            
            # 5. Context relevance scoring
            context_score = await self._calculate_context_relevance(
                document, query_context
            )
            component_scores["context"] = context_score
            
            # 6. Apply configuration-specific adjustments
            adjusted_scores = self._apply_config_adjustments(
                component_scores, document, authority_assessment, config
            )
            
            # 7. Calculate weighted final score
            final_score = self._calculate_weighted_final_score(
                adjusted_scores, config
            )
            
            # 8. Calculate confidence
            confidence = self._calculate_composite_confidence(
                adjusted_scores, authority_assessment, relevance_rankings[0] if relevance_rankings else None
            )
            
            # 9. Quality thresholds
            if (relevance_score < config.min_relevance_threshold or
                authority_score < config.min_authority_threshold or
                confidence < config.min_confidence_threshold):
                final_score *= 0.5  # Significant penalty for low-quality documents
                explanations.append("Quality threshold penalty applied")
            
            return CompositeScore(
                document_id=doc_id,
                final_score=final_score,
                component_scores=adjusted_scores,
                component_weights={
                    "relevance": config.relevance_weight,
                    "authority": config.authority_weight,
                    "recency": config.recency_weight,
                    "completeness": config.completeness_weight,
                    "context": config.context_weight
                },
                ranking_explanation=explanations,
                confidence=confidence,
                authority_assessment=authority_assessment,
                relevance_ranking=relevance_rankings[0] if relevance_rankings else None,
                legal_context=query_context,
                deduplication_info=None
            )
            
        except Exception as e:
            logger.error(f"Composite score calculation failed for document {doc_id}: {str(e)}")
            return CompositeScore(
                document_id=doc_id,
                final_score=0.3,
                component_scores={"error": 0.3},
                component_weights={"error": 1.0},
                ranking_explanation=[f"Calculation error: {str(e)}"],
                confidence=0.0,
                authority_assessment=None,
                relevance_ranking=None,
                legal_context=None,
                deduplication_info=None
            )
    
    def _adjust_config_for_context(
        self,
        base_config: RankingConfiguration,
        query_context: Any,
        query: UnifiedQuery
    ) -> RankingConfiguration:
        """Adjust ranking configuration based on query context"""
        try:
            # Create a copy of the base configuration
            adjusted_config = RankingConfiguration(
                strategy=base_config.strategy,
                context=base_config.context,
                relevance_weight=base_config.relevance_weight,
                authority_weight=base_config.authority_weight,
                recency_weight=base_config.recency_weight,
                completeness_weight=base_config.completeness_weight,
                diversity_weight=base_config.diversity_weight,
                context_weight=base_config.context_weight,
                min_relevance_threshold=base_config.min_relevance_threshold,
                min_authority_threshold=base_config.min_authority_threshold,
                min_confidence_threshold=base_config.min_confidence_threshold,
                max_same_provider_ratio=base_config.max_same_provider_ratio,
                max_same_court_ratio=base_config.max_same_court_ratio,
                max_same_jurisdiction_ratio=base_config.max_same_jurisdiction_ratio,
                boost_landmark_cases=base_config.boost_landmark_cases,
                penalize_outdated_secondary=base_config.penalize_outdated_secondary,
                prioritize_primary_authority=base_config.prioritize_primary_authority,
                consider_citation_networks=base_config.consider_citation_networks
            )
            
            # Adjust based on practice area
            primary_area = query_context.practice_area_analysis.primary_area
            
            if primary_area == "constitutional_law":
                # Constitutional law benefits from historical analysis
                adjusted_config.authority_weight *= 1.2
                adjusted_config.recency_weight *= 0.8
                adjusted_config.boost_landmark_cases = True
                
            elif primary_area == "corporate_law":
                # Corporate law needs current regulations
                adjusted_config.recency_weight *= 1.3
                adjusted_config.relevance_weight *= 1.1
                
            elif primary_area in ["criminal_law", "employment_law"]:
                # Areas with frequent changes need recent authority
                adjusted_config.recency_weight *= 1.2
                adjusted_config.authority_weight *= 1.1
                
            # Adjust for query complexity
            if query_context.complexity_score > 2.0:
                # Complex queries benefit from comprehensive analysis
                adjusted_config.completeness_weight *= 1.3
                adjusted_config.diversity_weight *= 1.2
                
            # Adjust for content type preferences
            if query.content_types:
                if ContentType.CASES in query.content_types:
                    adjusted_config.authority_weight *= 1.1
                if ContentType.STATUTES in query.content_types:
                    adjusted_config.recency_weight *= 1.2
                if ContentType.LAW_REVIEWS in query.content_types:
                    adjusted_config.completeness_weight *= 1.2
                    
            # Adjust for temporal context
            if query_context.temporal_analysis.get('recent', False):
                adjusted_config.recency_weight *= 1.4
            elif query_context.temporal_analysis.get('historical', False):
                adjusted_config.authority_weight *= 1.2
                adjusted_config.recency_weight *= 0.7
            
            # Normalize weights to sum to 1.0
            total_weight = (adjusted_config.relevance_weight + 
                           adjusted_config.authority_weight + 
                           adjusted_config.recency_weight + 
                           adjusted_config.completeness_weight + 
                           adjusted_config.diversity_weight + 
                           adjusted_config.context_weight)
            
            if total_weight > 0:
                adjusted_config.relevance_weight /= total_weight
                adjusted_config.authority_weight /= total_weight
                adjusted_config.recency_weight /= total_weight
                adjusted_config.completeness_weight /= total_weight
                adjusted_config.diversity_weight /= total_weight
                adjusted_config.context_weight /= total_weight
            
            return adjusted_config
            
        except Exception as e:
            logger.error(f"Configuration adjustment failed: {str(e)}")
            return base_config
    
    async def _calculate_enhanced_recency(
        self,
        document: UnifiedDocument,
        query_context: Any
    ) -> float:
        """Calculate enhanced recency score"""
        try:
            base_recency = document.recency_score
            
            doc_date = document.decision_date or document.publication_date
            if not doc_date:
                return base_recency
            
            today = date.today()
            years_old = (today - doc_date).days / 365.25
            
            # Context-aware recency
            enhanced_recency = base_recency
            
            # Adjust for document type
            if document.document_type == ContentType.REGULATIONS:
                # Regulations become outdated faster
                if years_old > 5:
                    enhanced_recency *= 0.8
            elif document.document_type == ContentType.CASES:
                # Cases maintain relevance longer
                if years_old < 10:
                    enhanced_recency *= 1.1
            elif document.document_type in [ContentType.LAW_REVIEWS, ContentType.TREATISES]:
                # Secondary authority ages differently
                if years_old > 15:
                    enhanced_recency *= 0.7
            
            # Practice area considerations
            primary_area = query_context.practice_area_analysis.primary_area
            if primary_area in ["tax_law", "corporate_law", "employment_law"]:
                # Fast-changing areas
                if years_old > 5:
                    enhanced_recency *= 0.8
            elif primary_area in ["constitutional_law", "contract_law"]:
                # Stable areas where older cases remain relevant
                if years_old > 20 and document.authority_score > 0.8:
                    enhanced_recency *= 1.1  # Landmark case bonus
            
            return min(enhanced_recency, 1.0)
            
        except Exception as e:
            logger.error(f"Enhanced recency calculation failed: {str(e)}")
            return document.recency_score
    
    def _calculate_completeness_score(self, document: UnifiedDocument) -> float:
        """Calculate document completeness score"""
        try:
            completeness_factors = []
            
            # Full text availability (most important)
            if document.full_text_available and document.full_text:
                text_length = len(document.full_text)
                if text_length > 10000:
                    completeness_factors.append(0.4)
                elif text_length > 2000:
                    completeness_factors.append(0.3)
                else:
                    completeness_factors.append(0.2)
            elif document.full_text_available:
                completeness_factors.append(0.1)
            
            # Metadata richness
            metadata_score = 0.0
            if document.citation:
                metadata_score += 0.15
            if document.court:
                metadata_score += 0.10
            if document.jurisdiction:
                metadata_score += 0.05
            if document.decision_date:
                metadata_score += 0.05
            if document.legal_topics:
                metadata_score += 0.10
            if document.parties:
                metadata_score += 0.05
                
            completeness_factors.append(metadata_score)
            
            # Summary and structured content
            if document.summary:
                completeness_factors.append(0.1)
            if document.headnotes:
                completeness_factors.append(0.05)
            if document.key_passages:
                completeness_factors.append(0.05)
            
            return min(sum(completeness_factors), 1.0)
            
        except Exception as e:
            logger.error(f"Completeness score calculation failed: {str(e)}")
            return 0.5
    
    async def _calculate_context_relevance(
        self,
        document: UnifiedDocument,
        query_context: Any
    ) -> float:
        """Calculate relevance to legal context"""
        try:
            # Analyze document context
            doc_text = f"{document.title or ''} {document.summary or ''}"
            if not doc_text.strip():
                return 0.5
            
            doc_context = await self.context_analyzer.analyze_legal_context(
                doc_text, document.document_type
            )
            
            context_relevance = 0.5
            
            # Practice area alignment
            if (doc_context.practice_area_analysis.primary_area == 
                query_context.practice_area_analysis.primary_area):
                context_relevance += 0.3
            elif (doc_context.practice_area_analysis.primary_area in 
                  query_context.practice_area_analysis.secondary_areas):
                context_relevance += 0.15
            
            # Legal concept overlap
            query_concepts = {concept.concept for concept in query_context.legal_concepts}
            doc_concepts = {concept.concept for concept in doc_context.legal_concepts}
            
            if query_concepts and doc_concepts:
                concept_overlap = len(query_concepts & doc_concepts) / len(query_concepts | doc_concepts)
                context_relevance += concept_overlap * 0.2
            
            # Procedural context alignment
            if (doc_context.procedural_context and query_context.procedural_context and
                doc_context.procedural_context.stage == query_context.procedural_context.stage):
                context_relevance += 0.1
            
            return min(context_relevance, 1.0)
            
        except Exception as e:
            logger.error(f"Context relevance calculation failed: {str(e)}")
            return 0.5
    
    def _apply_config_adjustments(
        self,
        component_scores: Dict[str, float],
        document: UnifiedDocument,
        authority_assessment: Any,
        config: RankingConfiguration
    ) -> Dict[str, float]:
        """Apply configuration-specific adjustments to component scores"""
        try:
            adjusted_scores = component_scores.copy()
            
            # Landmark case boost
            if (config.boost_landmark_cases and 
                authority_assessment.authority_type == AuthorityType.PRIMARY_BINDING and
                authority_assessment.court_level in [CourtLevel.SUPREME_COURT_US, CourtLevel.STATE_SUPREME]):
                adjusted_scores["authority"] *= 1.2
                
            # Primary authority prioritization
            if config.prioritize_primary_authority:
                if document.document_type in [ContentType.CASES, ContentType.STATUTES, 
                                            ContentType.CONSTITUTIONS, ContentType.REGULATIONS]:
                    adjusted_scores["authority"] *= 1.1
                else:
                    adjusted_scores["authority"] *= 0.9
            
            # Outdated secondary authority penalty
            if config.penalize_outdated_secondary:
                doc_date = document.decision_date or document.publication_date
                if (doc_date and document.document_type in [ContentType.LAW_REVIEWS, ContentType.TREATISES]):
                    years_old = (date.today() - doc_date).days / 365.25
                    if years_old > 20:
                        adjusted_scores["recency"] *= 0.7
                        adjusted_scores["authority"] *= 0.9
            
            # Citation network considerations
            if (config.consider_citation_networks and 
                authority_assessment.citation_analysis and
                authority_assessment.citation_analysis.cited_by_count > 10):
                adjusted_scores["authority"] *= 1.1
            
            # Ensure scores remain in [0, 1] range
            for key in adjusted_scores:
                adjusted_scores[key] = min(adjusted_scores[key], 1.0)
            
            return adjusted_scores
            
        except Exception as e:
            logger.error(f"Configuration adjustments failed: {str(e)}")
            return component_scores
    
    def _calculate_weighted_final_score(
        self,
        component_scores: Dict[str, float],
        config: RankingConfiguration
    ) -> float:
        """Calculate weighted final score"""
        try:
            final_score = (
                component_scores.get("relevance", 0.5) * config.relevance_weight +
                component_scores.get("authority", 0.5) * config.authority_weight +
                component_scores.get("recency", 0.5) * config.recency_weight +
                component_scores.get("completeness", 0.5) * config.completeness_weight +
                component_scores.get("context", 0.5) * config.context_weight
            )
            
            return min(final_score, 1.0)
            
        except Exception as e:
            logger.error(f"Weighted final score calculation failed: {str(e)}")
            return 0.5
    
    def _calculate_composite_confidence(
        self,
        component_scores: Dict[str, float],
        authority_assessment: Any,
        relevance_ranking: Any
    ) -> float:
        """Calculate confidence in composite ranking"""
        try:
            confidence_factors = []
            
            # Authority confidence
            if authority_assessment:
                confidence_factors.append(authority_assessment.confidence)
            
            # Relevance confidence
            if relevance_ranking:
                confidence_factors.append(relevance_ranking.confidence)
            
            # Score consistency (lower variance = higher confidence)
            if len(component_scores) > 1:
                scores = list(component_scores.values())
                mean_score = sum(scores) / len(scores)
                variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
                consistency = 1.0 - min(variance, 1.0)
                confidence_factors.append(consistency)
            
            # Data completeness
            completeness = component_scores.get("completeness", 0.5)
            confidence_factors.append(completeness)
            
            # Overall confidence
            if confidence_factors:
                return sum(confidence_factors) / len(confidence_factors)
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Composite confidence calculation failed: {str(e)}")
            return 0.5
    
    async def _optimize_for_diversity(
        self,
        composite_scores: List[CompositeScore],
        documents: List[UnifiedDocument],
        config: RankingConfiguration
    ) -> List[CompositeScore]:
        """Optimize rankings for diversity"""
        try:
            if not composite_scores or config.diversity_weight <= 0.01:
                return composite_scores
            
            # Create document lookup
            doc_lookup = {doc.source_document_id or str(id(doc)): doc for doc in documents}
            
            # Apply diversity optimization using MMR-like approach
            optimized_scores = []
            remaining_scores = composite_scores[:]
            
            # Always include the top document
            if remaining_scores:
                top_score = max(remaining_scores, key=lambda x: x.final_score)
                optimized_scores.append(top_score)
                remaining_scores.remove(top_score)
            
            # Select remaining documents balancing score and diversity
            while remaining_scores and len(optimized_scores) < len(composite_scores):
                best_score = None
                best_mmr = -1.0
                
                for score in remaining_scores:
                    # Calculate diversity from already selected documents
                    diversity = self._calculate_diversity_from_selected(
                        score, optimized_scores, doc_lookup, config
                    )
                    
                    # MMR formula: λ * relevance + (1-λ) * diversity
                    diversity_lambda = config.diversity_weight / (config.diversity_weight + 0.5)
                    mmr = (1 - diversity_lambda) * score.final_score + diversity_lambda * diversity
                    
                    if mmr > best_mmr:
                        best_mmr = mmr
                        best_score = score
                
                if best_score:
                    optimized_scores.append(best_score)
                    remaining_scores.remove(best_score)
                else:
                    break
            
            return optimized_scores
            
        except Exception as e:
            logger.error(f"Diversity optimization failed: {str(e)}")
            return composite_scores
    
    def _calculate_diversity_from_selected(
        self,
        candidate_score: CompositeScore,
        selected_scores: List[CompositeScore],
        doc_lookup: Dict[str, UnifiedDocument],
        config: RankingConfiguration
    ) -> float:
        """Calculate diversity score relative to already selected documents"""
        try:
            if not selected_scores:
                return 1.0
            
            candidate_doc = doc_lookup.get(candidate_score.document_id)
            if not candidate_doc:
                return 0.5
            
            diversity_score = 1.0
            
            # Provider diversity
            candidate_provider = candidate_doc.source_provider
            same_provider_count = sum(
                1 for score in selected_scores
                if doc_lookup.get(score.document_id) and 
                   doc_lookup[score.document_id].source_provider == candidate_provider
            )
            
            provider_ratio = same_provider_count / len(selected_scores)
            if provider_ratio > config.max_same_provider_ratio:
                diversity_score *= 0.5
            
            # Court diversity
            candidate_court = candidate_doc.court
            if candidate_court:
                same_court_count = sum(
                    1 for score in selected_scores
                    if doc_lookup.get(score.document_id) and 
                       doc_lookup[score.document_id].court == candidate_court
                )
                
                court_ratio = same_court_count / len(selected_scores)
                if court_ratio > config.max_same_court_ratio:
                    diversity_score *= 0.7
            
            # Jurisdiction diversity
            candidate_jurisdiction = candidate_doc.jurisdiction
            if candidate_jurisdiction:
                same_jurisdiction_count = sum(
                    1 for score in selected_scores
                    if doc_lookup.get(score.document_id) and 
                       doc_lookup[score.document_id].jurisdiction == candidate_jurisdiction
                )
                
                jurisdiction_ratio = same_jurisdiction_count / len(selected_scores)
                if jurisdiction_ratio > config.max_same_jurisdiction_ratio:
                    diversity_score *= 0.8
            
            # Document type diversity
            candidate_type = candidate_doc.document_type
            same_type_count = sum(
                1 for score in selected_scores
                if doc_lookup.get(score.document_id) and 
                   doc_lookup[score.document_id].document_type == candidate_type
            )
            
            type_ratio = same_type_count / len(selected_scores)
            if type_ratio > 0.7:  # Allow some concentration by type
                diversity_score *= 0.9
            
            return diversity_score
            
        except Exception as e:
            logger.error(f"Diversity calculation failed: {str(e)}")
            return 0.5
    
    def _apply_final_ranking(
        self,
        composite_scores: List[CompositeScore],
        config: RankingConfiguration
    ) -> List[CompositeScore]:
        """Apply final ranking and filtering"""
        try:
            # Sort by final score
            sorted_scores = sorted(composite_scores, key=lambda x: x.final_score, reverse=True)
            
            # Apply quality filters
            filtered_scores = []
            for score in sorted_scores:
                # Check thresholds
                relevance_ok = score.component_scores.get("relevance", 0) >= config.min_relevance_threshold
                authority_ok = score.component_scores.get("authority", 0) >= config.min_authority_threshold
                confidence_ok = score.confidence >= config.min_confidence_threshold
                
                if relevance_ok and authority_ok and confidence_ok:
                    filtered_scores.append(score)
                else:
                    # Apply penalty but don't remove entirely
                    penalized_score = CompositeScore(
                        document_id=score.document_id,
                        final_score=score.final_score * 0.3,  # Heavy penalty
                        component_scores=score.component_scores,
                        component_weights=score.component_weights,
                        ranking_explanation=score.ranking_explanation + ["Quality threshold penalty"],
                        confidence=score.confidence,
                        authority_assessment=score.authority_assessment,
                        relevance_ranking=score.relevance_ranking,
                        legal_context=score.legal_context,
                        deduplication_info=score.deduplication_info
                    )
                    filtered_scores.append(penalized_score)
            
            # Re-sort after penalties
            final_scores = sorted(filtered_scores, key=lambda x: x.final_score, reverse=True)
            
            return final_scores
            
        except Exception as e:
            logger.error(f"Final ranking application failed: {str(e)}")
            return sorted(composite_scores, key=lambda x: x.final_score, reverse=True)
    
    # Public utility methods
    
    def get_ranking_strategies(self) -> List[RankingStrategy]:
        """Get available ranking strategies"""
        return list(RankingStrategy)
    
    def get_ranking_contexts(self) -> List[RankingContext]:
        """Get available ranking contexts"""
        return list(RankingContext)
    
    def create_custom_configuration(
        self,
        strategy: RankingStrategy,
        relevance_weight: float = 0.35,
        authority_weight: float = 0.30,
        recency_weight: float = 0.15,
        completeness_weight: float = 0.10,
        diversity_weight: float = 0.05,
        context_weight: float = 0.05,
        **kwargs
    ) -> RankingConfiguration:
        """Create custom ranking configuration"""
        
        # Normalize weights
        total_weight = (relevance_weight + authority_weight + recency_weight + 
                       completeness_weight + diversity_weight + context_weight)
        
        if total_weight > 0:
            relevance_weight /= total_weight
            authority_weight /= total_weight
            recency_weight /= total_weight
            completeness_weight /= total_weight
            diversity_weight /= total_weight
            context_weight /= total_weight
        
        return RankingConfiguration(
            strategy=strategy,
            relevance_weight=relevance_weight,
            authority_weight=authority_weight,
            recency_weight=recency_weight,
            completeness_weight=completeness_weight,
            diversity_weight=diversity_weight,
            context_weight=context_weight,
            **kwargs
        )
    
    async def explain_ranking(
        self,
        composite_score: CompositeScore,
        detailed: bool = False
    ) -> Dict[str, Any]:
        """Provide detailed explanation of document ranking"""
        try:
            explanation = {
                "document_id": composite_score.document_id,
                "final_score": composite_score.final_score,
                "confidence": composite_score.confidence,
                "ranking_summary": composite_score.ranking_explanation,
                "component_breakdown": {
                    component: {
                        "score": score,
                        "weight": composite_score.component_weights.get(component, 0),
                        "contribution": score * composite_score.component_weights.get(component, 0)
                    }
                    for component, score in composite_score.component_scores.items()
                }
            }
            
            if detailed:
                explanation["detailed_analysis"] = {
                    "authority_assessment": {
                        "authority_type": composite_score.authority_assessment.authority_type.value if composite_score.authority_assessment else None,
                        "court_level": composite_score.authority_assessment.court_level.value if composite_score.authority_assessment else None,
                        "precedential_value": composite_score.authority_assessment.precedential_value if composite_score.authority_assessment else None,
                        "explanation": composite_score.authority_assessment.authority_explanation if composite_score.authority_assessment else []
                    },
                    "relevance_analysis": {
                        "explanation": composite_score.relevance_ranking.ranking_explanation if composite_score.relevance_ranking else []
                    },
                    "legal_context": {
                        "primary_practice_area": composite_score.legal_context.practice_area_analysis.primary_area if composite_score.legal_context else None,
                        "complexity": composite_score.legal_context.complexity_score if composite_score.legal_context else None
                    }
                }
            
            return explanation
            
        except Exception as e:
            logger.error(f"Ranking explanation failed: {str(e)}")
            return {"error": str(e)}