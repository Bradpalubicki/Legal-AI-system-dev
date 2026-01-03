"""
Result Fusion Engine

Advanced result fusion and ranking system that intelligently combines
search results from multiple legal databases with sophisticated scoring,
deduplication, and relevance ranking algorithms.
"""

import logging
import re
import math
from datetime import datetime, date
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict, Counter
from dataclasses import dataclass

from .database_models import (
    UnifiedDocument, UnifiedQuery, UnifiedSearchResult,
    DatabaseProvider, ContentType, SearchStrategy
)

logger = logging.getLogger(__name__)


@dataclass
class DocumentCluster:
    """Represents a cluster of similar documents"""
    representative_doc: UnifiedDocument
    similar_docs: List[UnifiedDocument]
    cluster_score: float
    diversity_score: float


@dataclass
class FusionMetrics:
    """Metrics for result fusion process"""
    total_input_documents: int
    deduplicated_documents: int
    final_ranked_documents: int
    average_relevance_score: float
    diversity_index: float
    authority_distribution: Dict[str, int]
    provider_distribution: Dict[str, int]


class ResultFusionEngine:
    """
    Advanced result fusion engine that combines search results from multiple
    legal databases using sophisticated ranking and deduplication algorithms.
    """
    
    def __init__(self):
        # Citation patterns for enhanced similarity detection
        self.citation_patterns = [
            r'\d+\s+U\.S\.\s+\d+',           # US Reports
            r'\d+\s+S\.\s?Ct\.\s+\d+',       # Supreme Court Reporter
            r'\d+\s+F\.\d*d?\s+\d+',         # Federal Reporter
            r'\d+\s+F\.\s?Supp\.\s?\d*\s+\d+', # Federal Supplement
            r'\d+\s+\w+\s+\d+',              # State reporters
            r'\d+\s+U\.S\.C\.?\s+§?\s*\d+',  # US Code
            r'\d+\s+C\.?F\.?R\.?\s+§?\s*\d+' # CFR
        ]
        
        # Legal terms for enhanced relevance scoring
        self.legal_terms = {
            'high_authority': [
                'supreme court', 'constitutional', 'precedent', 'landmark',
                'en banc', 'cert granted', 'writ of certiorari'
            ],
            'procedural': [
                'motion', 'discovery', 'summary judgment', 'plea', 'trial',
                'appeal', 'remand', 'jurisdiction'
            ],
            'substantive': [
                'contract', 'tort', 'criminal', 'constitutional', 'statutory',
                'common law', 'equity', 'remedy', 'damages'
            ]
        }
        
        logger.info("Result fusion engine initialized")
    
    async def fuse_results(
        self,
        provider_results: Dict[str, UnifiedSearchResult],
        query: UnifiedQuery,
        strategy: SearchStrategy
    ) -> UnifiedSearchResult:
        """
        Main fusion method that combines results from multiple providers
        """
        try:
            logger.info("Starting advanced result fusion")
            
            # Step 1: Collect and normalize all documents
            all_documents = self._collect_documents(provider_results)
            logger.info(f"Collected {len(all_documents)} documents from {len(provider_results)} providers")
            
            if not all_documents:
                return self._create_empty_result(query, provider_results)
            
            # Step 2: Enhanced deduplication
            deduplicated_docs = await self._advanced_deduplication(
                all_documents, strategy.deduplication_threshold
            )
            logger.info(f"After deduplication: {len(deduplicated_docs)} documents")
            
            # Step 3: Relevance enhancement
            enhanced_docs = await self._enhance_relevance_scores(
                deduplicated_docs, query
            )
            
            # Step 4: Authority scoring
            authority_scored_docs = await self._enhance_authority_scores(enhanced_docs)
            
            # Step 5: Advanced ranking
            ranked_docs = await self._advanced_ranking(
                authority_scored_docs, query, strategy
            )
            
            # Step 6: Diversity optimization
            diversified_docs = await self._optimize_diversity(
                ranked_docs, strategy
            )
            
            # Step 7: Final selection
            final_docs = diversified_docs[:strategy.max_total_results]
            
            # Step 8: Create unified result with metrics
            unified_result = await self._create_unified_result(
                final_docs, query, provider_results, strategy
            )
            
            logger.info(f"Result fusion completed: {len(final_docs)} final documents")
            return unified_result
            
        except Exception as e:
            logger.error(f"Result fusion failed: {str(e)}")
            return self._create_empty_result(query, provider_results)
    
    def _collect_documents(
        self,
        provider_results: Dict[str, UnifiedSearchResult]
    ) -> List[UnifiedDocument]:
        """Collect all documents from provider results"""
        all_documents = []
        
        for provider_key, result in provider_results.items():
            if not result.providers_failed and result.documents:
                for doc in result.documents:
                    # Add provider metadata
                    doc.provider_metadata["fusion_provider"] = provider_key
                    doc.provider_metadata["original_rank"] = len(all_documents)
                    all_documents.append(doc)
        
        return all_documents
    
    async def _advanced_deduplication(
        self,
        documents: List[UnifiedDocument],
        threshold: float
    ) -> List[UnifiedDocument]:
        """Advanced deduplication using multiple similarity metrics"""
        try:
            if len(documents) <= 1:
                return documents
            
            # Create clusters of similar documents
            clusters = await self._create_document_clusters(documents, threshold)
            
            # Select best representative from each cluster
            unique_documents = []
            for cluster in clusters:
                best_doc = self._select_cluster_representative(cluster)
                unique_documents.append(best_doc)
            
            logger.info(f"Advanced deduplication: {len(documents)} -> {len(unique_documents)} documents")
            return unique_documents
            
        except Exception as e:
            logger.error(f"Advanced deduplication failed: {str(e)}")
            return documents
    
    async def _create_document_clusters(
        self,
        documents: List[UnifiedDocument],
        threshold: float
    ) -> List[DocumentCluster]:
        """Create clusters of similar documents"""
        clusters = []
        processed_docs = set()
        
        for i, doc in enumerate(documents):
            if i in processed_docs:
                continue
            
            # Start new cluster with this document
            cluster_docs = [doc]
            processed_docs.add(i)
            
            # Find similar documents
            for j, other_doc in enumerate(documents[i+1:], i+1):
                if j in processed_docs:
                    continue
                
                similarity = await self._calculate_comprehensive_similarity(doc, other_doc)
                
                if similarity >= threshold:
                    cluster_docs.append(other_doc)
                    processed_docs.add(j)
            
            # Create cluster
            if cluster_docs:
                representative = cluster_docs[0]  # Will be refined later
                cluster = DocumentCluster(
                    representative_doc=representative,
                    similar_docs=cluster_docs,
                    cluster_score=sum(d.relevance_score for d in cluster_docs) / len(cluster_docs),
                    diversity_score=self._calculate_cluster_diversity(cluster_docs)
                )
                clusters.append(cluster)
        
        return clusters
    
    async def _calculate_comprehensive_similarity(
        self,
        doc1: UnifiedDocument,
        doc2: UnifiedDocument
    ) -> float:
        """Calculate comprehensive similarity using multiple factors"""
        try:
            similarities = []
            
            # Title similarity (high weight)
            title_sim = self._calculate_text_similarity(doc1.title, doc2.title)
            similarities.append(('title', title_sim, 0.3))
            
            # Citation similarity (very high weight if available)
            if doc1.citation and doc2.citation:
                citation_sim = self._calculate_citation_similarity(doc1.citation, doc2.citation)
                similarities.append(('citation', citation_sim, 0.4))
            
            # Court similarity
            if doc1.court and doc2.court:
                court_sim = 1.0 if doc1.court.lower() == doc2.court.lower() else 0.0
                similarities.append(('court', court_sim, 0.1))
            
            # Date similarity
            if doc1.decision_date and doc2.decision_date:
                date_sim = self._calculate_date_similarity(doc1.decision_date, doc2.decision_date)
                similarities.append(('date', date_sim, 0.1))
            
            # Summary similarity (if available)
            if doc1.summary and doc2.summary:
                summary_sim = self._calculate_text_similarity(doc1.summary, doc2.summary)
                similarities.append(('summary', summary_sim, 0.1))
            
            # Weighted average
            if similarities:
                total_weight = sum(weight for _, _, weight in similarities)
                weighted_sum = sum(sim * weight for _, sim, weight in similarities)
                return weighted_sum / total_weight
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Comprehensive similarity calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using enhanced algorithms"""
        try:
            if not text1 or not text2:
                return 0.0
            
            # Normalize texts
            norm_text1 = self._normalize_text(text1)
            norm_text2 = self._normalize_text(text2)
            
            # Exact match
            if norm_text1 == norm_text2:
                return 1.0
            
            # Word-based Jaccard similarity
            words1 = set(norm_text1.split())
            words2 = set(norm_text2.split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            jaccard = intersection / union if union > 0 else 0.0
            
            # Sequence similarity (simple)
            sequence_sim = self._calculate_sequence_similarity(norm_text1, norm_text2)
            
            # Combined similarity
            return (jaccard * 0.7) + (sequence_sim * 0.3)
            
        except Exception as e:
            logger.error(f"Text similarity calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_citation_similarity(self, citation1: str, citation2: str) -> float:
        """Calculate citation-specific similarity"""
        try:
            if not citation1 or not citation2:
                return 0.0
            
            # Exact match
            if citation1.strip() == citation2.strip():
                return 1.0
            
            # Extract and compare citation components
            components1 = self._extract_citation_components(citation1)
            components2 = self._extract_citation_components(citation2)
            
            if not components1 or not components2:
                return self._calculate_text_similarity(citation1, citation2)
            
            # Compare components
            component_matches = 0
            total_components = 0
            
            for key in ['volume', 'reporter', 'page', 'year']:
                if key in components1 or key in components2:
                    total_components += 1
                    if (key in components1 and key in components2 and 
                        components1[key] == components2[key]):
                        component_matches += 1
            
            return component_matches / total_components if total_components > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Citation similarity calculation failed: {str(e)}")
            return 0.0
    
    def _extract_citation_components(self, citation: str) -> Dict[str, str]:
        """Extract components from a legal citation"""
        try:
            components = {}
            citation = citation.strip()
            
            # Try different citation patterns
            for pattern in self.citation_patterns:
                match = re.search(pattern, citation, re.IGNORECASE)
                if match:
                    citation_text = match.group(0)
                    
                    # Extract volume, reporter, page
                    parts = citation_text.split()
                    if len(parts) >= 3:
                        components['volume'] = parts[0]
                        components['reporter'] = parts[1]
                        components['page'] = parts[2]
            
            # Extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', citation)
            if year_match:
                components['year'] = year_match.group(0)
            
            return components
            
        except Exception as e:
            logger.error(f"Citation component extraction failed: {str(e)}")
            return {}
    
    def _calculate_date_similarity(self, date1: date, date2: date) -> float:
        """Calculate similarity between two dates"""
        try:
            if date1 == date2:
                return 1.0
            
            # Calculate difference in days
            diff_days = abs((date1 - date2).days)
            
            # Similarity decreases with time difference
            if diff_days <= 1:
                return 1.0
            elif diff_days <= 7:
                return 0.9
            elif diff_days <= 30:
                return 0.7
            elif diff_days <= 365:
                return 0.5
            elif diff_days <= 1825:  # 5 years
                return 0.3
            else:
                return 0.1
                
        except:
            return 0.0
    
    def _calculate_sequence_similarity(self, text1: str, text2: str) -> float:
        """Calculate sequence-based similarity (simplified Levenshtein-like)"""
        try:
            if len(text1) == 0 or len(text2) == 0:
                return 0.0
            
            # Simplified edit distance
            max_len = max(len(text1), len(text2))
            common_chars = sum(1 for a, b in zip(text1, text2) if a == b)
            
            return common_chars / max_len
            
        except:
            return 0.0
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        try:
            # Convert to lowercase
            text = text.lower()
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            # Remove common legal formatting
            text = re.sub(r'\b(no\.|case no\.|docket no\.)\s*\d+', '', text)
            text = re.sub(r'\([^)]*\)', '', text)  # Remove parenthetical content
            
            # Remove punctuation except periods in abbreviations
            text = re.sub(r'[^\w\s\.]', ' ', text)
            
            return text.strip()
            
        except:
            return text
    
    def _calculate_cluster_diversity(self, docs: List[UnifiedDocument]) -> float:
        """Calculate diversity score for a cluster of documents"""
        try:
            if len(docs) <= 1:
                return 1.0
            
            # Provider diversity
            providers = set(doc.source_provider for doc in docs)
            provider_diversity = len(providers) / len(docs)
            
            # Jurisdiction diversity
            jurisdictions = set(doc.jurisdiction for doc in docs if doc.jurisdiction)
            jurisdiction_diversity = len(jurisdictions) / len(docs) if jurisdictions else 0.5
            
            # Date diversity
            dates = [doc.decision_date for doc in docs if doc.decision_date]
            date_diversity = 0.5
            if len(dates) > 1:
                date_range = (max(dates) - min(dates)).days
                date_diversity = min(date_range / 365.0, 1.0)  # Normalize to max 1 year
            
            # Combined diversity
            return (provider_diversity * 0.4 + 
                   jurisdiction_diversity * 0.3 + 
                   date_diversity * 0.3)
            
        except:
            return 0.5
    
    def _select_cluster_representative(self, cluster: DocumentCluster) -> UnifiedDocument:
        """Select the best representative document from a cluster"""
        try:
            if len(cluster.similar_docs) == 1:
                return cluster.similar_docs[0]
            
            best_doc = cluster.similar_docs[0]
            best_score = -1.0
            
            for doc in cluster.similar_docs:
                # Score based on multiple factors
                score = (
                    doc.relevance_score * 0.3 +
                    doc.authority_score * 0.3 +
                    doc.recency_score * 0.2 +
                    (1.0 if doc.full_text_available else 0.0) * 0.1 +
                    (1.0 if doc.citation else 0.0) * 0.1
                )
                
                if score > best_score:
                    best_score = score
                    best_doc = doc
            
            return best_doc
            
        except Exception as e:
            logger.error(f"Cluster representative selection failed: {str(e)}")
            return cluster.similar_docs[0]
    
    async def _enhance_relevance_scores(
        self,
        documents: List[UnifiedDocument],
        query: UnifiedQuery
    ) -> List[UnifiedDocument]:
        """Enhance relevance scores using advanced techniques"""
        try:
            query_terms = self._extract_query_terms(query.query_text)
            legal_context = self._analyze_legal_context(query.query_text)
            
            for doc in documents:
                enhanced_score = await self._calculate_enhanced_relevance(
                    doc, query_terms, legal_context, query
                )
                doc.relevance_score = min(enhanced_score, 1.0)
            
            logger.info("Enhanced relevance scores for all documents")
            return documents
            
        except Exception as e:
            logger.error(f"Relevance enhancement failed: {str(e)}")
            return documents
    
    def _extract_query_terms(self, query_text: str) -> Dict[str, float]:
        """Extract and weight query terms"""
        try:
            # Normalize query
            normalized_query = self._normalize_text(query_text)
            words = normalized_query.split()
            
            # Basic term frequency
            term_counts = Counter(words)
            total_words = len(words)
            
            # Calculate TF weights
            term_weights = {}
            for term, count in term_counts.items():
                tf_weight = count / total_words
                
                # Boost legal terms
                legal_boost = 1.0
                for category, terms in self.legal_terms.items():
                    if any(legal_term in term for legal_term in terms):
                        legal_boost = 1.5
                        break
                
                term_weights[term] = tf_weight * legal_boost
            
            return term_weights
            
        except Exception as e:
            logger.error(f"Query term extraction failed: {str(e)}")
            return {}
    
    def _analyze_legal_context(self, query_text: str) -> Dict[str, Any]:
        """Analyze legal context of the query"""
        context = {
            'is_case_law': False,
            'is_statutory': False,
            'is_constitutional': False,
            'practice_area': 'general',
            'jurisdiction_hints': []
        }
        
        try:
            query_lower = query_text.lower()
            
            # Detect content type
            if any(term in query_lower for term in ['case', 'opinion', 'holding', 'court']):
                context['is_case_law'] = True
            
            if any(term in query_lower for term in ['statute', 'code', 'usc', 'regulation', 'cfr']):
                context['is_statutory'] = True
            
            if any(term in query_lower for term in ['constitutional', 'amendment', 'bill of rights']):
                context['is_constitutional'] = True
            
            # Detect practice areas
            practice_areas = {
                'contract': ['contract', 'agreement', 'breach', 'consideration'],
                'tort': ['tort', 'negligence', 'liability', 'damages'],
                'criminal': ['criminal', 'felony', 'misdemeanor', 'prosecution'],
                'constitutional': ['constitutional', 'first amendment', 'due process'],
                'corporate': ['corporate', 'securities', 'merger', 'fiduciary']
            }
            
            for area, keywords in practice_areas.items():
                if any(keyword in query_lower for keyword in keywords):
                    context['practice_area'] = area
                    break
            
            # Detect jurisdiction hints
            jurisdiction_terms = [
                'federal', 'supreme court', 'circuit', 'district',
                'california', 'new york', 'texas', 'florida'
            ]
            
            for term in jurisdiction_terms:
                if term in query_lower:
                    context['jurisdiction_hints'].append(term)
            
            return context
            
        except Exception as e:
            logger.error(f"Legal context analysis failed: {str(e)}")
            return context
    
    async def _calculate_enhanced_relevance(
        self,
        doc: UnifiedDocument,
        query_terms: Dict[str, float],
        legal_context: Dict[str, Any],
        query: UnifiedQuery
    ) -> float:
        """Calculate enhanced relevance score"""
        try:
            base_score = doc.relevance_score
            
            # Term matching boost
            term_match_score = self._calculate_term_match_score(doc, query_terms)
            
            # Legal context boost
            context_boost = self._calculate_context_boost(doc, legal_context)
            
            # Query alignment boost
            alignment_boost = self._calculate_query_alignment(doc, query)
            
            # Combine scores
            enhanced_score = (
                base_score * 0.5 +
                term_match_score * 0.3 +
                context_boost * 0.1 +
                alignment_boost * 0.1
            )
            
            return min(enhanced_score, 1.0)
            
        except Exception as e:
            logger.error(f"Enhanced relevance calculation failed: {str(e)}")
            return doc.relevance_score
    
    def _calculate_term_match_score(
        self,
        doc: UnifiedDocument,
        query_terms: Dict[str, float]
    ) -> float:
        """Calculate term matching score"""
        try:
            if not query_terms:
                return 0.5
            
            # Combine document text
            doc_text = f"{doc.title} {doc.summary or ''} {' '.join(doc.legal_topics)}"
            doc_text_normalized = self._normalize_text(doc_text).lower()
            doc_words = set(doc_text_normalized.split())
            
            total_weight = 0.0
            matched_weight = 0.0
            
            for term, weight in query_terms.items():
                total_weight += weight
                
                # Exact match
                if term.lower() in doc_words:
                    matched_weight += weight
                # Partial match
                elif any(term.lower() in word for word in doc_words):
                    matched_weight += weight * 0.5
            
            return matched_weight / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Term match score calculation failed: {str(e)}")
            return 0.5
    
    def _calculate_context_boost(
        self,
        doc: UnifiedDocument,
        legal_context: Dict[str, Any]
    ) -> float:
        """Calculate legal context alignment boost"""
        try:
            boost = 0.5
            
            # Document type alignment
            if legal_context['is_case_law'] and doc.document_type == ContentType.CASES:
                boost += 0.2
            elif legal_context['is_statutory'] and doc.document_type == ContentType.STATUTES:
                boost += 0.2
            elif legal_context['is_constitutional'] and doc.document_type == ContentType.CONSTITUTIONS:
                boost += 0.2
            
            # Practice area alignment
            if legal_context['practice_area'] != 'general':
                doc_text = f"{doc.title} {doc.summary or ''}".lower()
                if legal_context['practice_area'] in doc_text:
                    boost += 0.1
            
            # Jurisdiction alignment
            if legal_context['jurisdiction_hints'] and doc.jurisdiction:
                doc_jurisdiction = doc.jurisdiction.lower()
                for hint in legal_context['jurisdiction_hints']:
                    if hint in doc_jurisdiction:
                        boost += 0.1
                        break
            
            return min(boost, 1.0)
            
        except Exception as e:
            logger.error(f"Context boost calculation failed: {str(e)}")
            return 0.5
    
    def _calculate_query_alignment(
        self,
        doc: UnifiedDocument,
        query: UnifiedQuery
    ) -> float:
        """Calculate alignment with query preferences"""
        try:
            alignment = 0.5
            
            # Content type alignment
            if query.content_types and doc.document_type in query.content_types:
                alignment += 0.2
            
            # Jurisdiction alignment
            if query.jurisdictions and doc.jurisdiction:
                if doc.jurisdiction.lower() in [j.lower() for j in query.jurisdictions]:
                    alignment += 0.2
            
            # Date range alignment
            if query.date_from or query.date_to:
                doc_date = doc.decision_date or doc.publication_date
                if doc_date:
                    in_range = True
                    if query.date_from and doc_date < query.date_from:
                        in_range = False
                    if query.date_to and doc_date > query.date_to:
                        in_range = False
                    
                    if in_range:
                        alignment += 0.1
            
            return min(alignment, 1.0)
            
        except Exception as e:
            logger.error(f"Query alignment calculation failed: {str(e)}")
            return 0.5
    
    async def _enhance_authority_scores(
        self,
        documents: List[UnifiedDocument]
    ) -> List[UnifiedDocument]:
        """Enhance authority scores using advanced metrics"""
        try:
            for doc in documents:
                enhanced_score = self._calculate_enhanced_authority(doc, documents)
                doc.authority_score = min(enhanced_score, 1.0)
            
            logger.info("Enhanced authority scores for all documents")
            return documents
            
        except Exception as e:
            logger.error(f"Authority enhancement failed: {str(e)}")
            return documents
    
    def _calculate_enhanced_authority(
        self,
        doc: UnifiedDocument,
        all_docs: List[UnifiedDocument]
    ) -> float:
        """Calculate enhanced authority score"""
        try:
            base_score = doc.authority_score
            
            # Court hierarchy boost
            court_boost = self._calculate_court_hierarchy_score(doc.court)
            
            # Citation network boost (simplified)
            citation_boost = self._calculate_citation_network_boost(doc, all_docs)
            
            # Recency vs authority balance
            recency_authority_balance = self._calculate_recency_authority_balance(doc)
            
            # Combine scores
            enhanced_score = (
                base_score * 0.6 +
                court_boost * 0.2 +
                citation_boost * 0.1 +
                recency_authority_balance * 0.1
            )
            
            return min(enhanced_score, 1.0)
            
        except Exception as e:
            logger.error(f"Enhanced authority calculation failed: {str(e)}")
            return doc.authority_score
    
    def _calculate_court_hierarchy_score(self, court: Optional[str]) -> float:
        """Calculate score based on court hierarchy"""
        if not court:
            return 0.5
        
        court_lower = court.lower()
        
        # Supreme Court
        if 'supreme court' in court_lower and 'united states' in court_lower:
            return 1.0
        elif 'supreme court' in court_lower:
            return 0.8  # State supreme court
        
        # Federal appellate
        elif any(term in court_lower for term in ['circuit', 'court of appeals']) and 'federal' in court_lower:
            return 0.9
        elif any(term in court_lower for term in ['circuit', 'court of appeals']):
            return 0.7  # State appellate
        
        # Federal district
        elif 'district' in court_lower and any(term in court_lower for term in ['us', 'united states', 'federal']):
            return 0.7
        
        # State trial courts
        elif any(term in court_lower for term in ['district', 'superior', 'county']):
            return 0.5
        
        return 0.5
    
    def _calculate_citation_network_boost(
        self,
        doc: UnifiedDocument,
        all_docs: List[UnifiedDocument]
    ) -> float:
        """Calculate boost based on citation network (simplified)"""
        try:
            if not doc.citation:
                return 0.5
            
            # Count how many other documents cite this one
            citation_count = 0
            for other_doc in all_docs:
                if other_doc != doc and other_doc.cited_cases:
                    if doc.citation in ' '.join(other_doc.cited_cases):
                        citation_count += 1
            
            # Normalize citation count
            max_citations = max(10, len(all_docs) * 0.1)  # Assume max 10% citation rate
            citation_score = min(citation_count / max_citations, 1.0)
            
            return 0.5 + (citation_score * 0.5)
            
        except Exception as e:
            logger.error(f"Citation network boost calculation failed: {str(e)}")
            return 0.5
    
    def _calculate_recency_authority_balance(self, doc: UnifiedDocument) -> float:
        """Balance recency and authority for legal documents"""
        try:
            recency = doc.recency_score
            authority = doc.authority_score
            
            # Legal documents can maintain authority over time
            if authority > 0.8:  # High authority documents
                return authority * 0.8 + recency * 0.2
            elif authority > 0.6:  # Medium authority
                return authority * 0.6 + recency * 0.4
            else:  # Lower authority documents rely more on recency
                return authority * 0.4 + recency * 0.6
            
        except:
            return 0.5
    
    async def _advanced_ranking(
        self,
        documents: List[UnifiedDocument],
        query: UnifiedQuery,
        strategy: SearchStrategy
    ) -> List[UnifiedDocument]:
        """Advanced ranking using multiple algorithms"""
        try:
            # Calculate composite scores with multiple ranking factors
            for doc in documents:
                doc.composite_score = self._calculate_composite_score(
                    doc, query, strategy
                )
            
            # Sort by composite score
            ranked_docs = sorted(
                documents,
                key=lambda d: d.composite_score,
                reverse=True
            )
            
            # Apply minimum relevance filter
            filtered_docs = [
                doc for doc in ranked_docs
                if doc.relevance_score >= strategy.min_relevance_score
            ]
            
            logger.info(f"Advanced ranking: {len(documents)} -> {len(filtered_docs)} documents")
            return filtered_docs
            
        except Exception as e:
            logger.error(f"Advanced ranking failed: {str(e)}")
            return documents
    
    def _calculate_composite_score(
        self,
        doc: UnifiedDocument,
        query: UnifiedQuery,
        strategy: SearchStrategy
    ) -> float:
        """Calculate composite score for ranking"""
        try:
            # Base scoring weights
            relevance_weight = 0.35
            authority_weight = 0.30
            recency_weight = 0.20
            completeness_weight = 0.10
            accessibility_weight = 0.05
            
            # Adjust weights based on query type
            if query.practice_area == 'research':
                # Research queries favor authority
                authority_weight = 0.40
                relevance_weight = 0.30
                recency_weight = 0.15
            elif query.case_law_only:
                # Case law queries favor authority and recency
                authority_weight = 0.35
                recency_weight = 0.25
            
            # Calculate component scores
            relevance_score = doc.relevance_score
            authority_score = doc.authority_score
            recency_score = doc.recency_score
            
            # Completeness score
            completeness_score = 0.0
            if doc.full_text_available:
                completeness_score += 0.5
            if doc.citation:
                completeness_score += 0.3
            if doc.summary:
                completeness_score += 0.2
            
            # Accessibility score
            accessibility_score = 1.0 if doc.is_free_access else 0.5
            
            # Composite score
            composite = (
                relevance_score * relevance_weight +
                authority_score * authority_weight +
                recency_score * recency_weight +
                completeness_score * completeness_weight +
                accessibility_score * accessibility_weight
            )
            
            return min(composite, 1.0)
            
        except Exception as e:
            logger.error(f"Composite score calculation failed: {str(e)}")
            return 0.5
    
    async def _optimize_diversity(
        self,
        documents: List[UnifiedDocument],
        strategy: SearchStrategy
    ) -> List[UnifiedDocument]:
        """Optimize result diversity"""
        try:
            if strategy.diversity_weight <= 0 or len(documents) <= 10:
                return documents
            
            # Use MMR (Maximal Marginal Relevance) approach
            selected_docs = []
            remaining_docs = documents[:]
            
            # Always include the top document
            if remaining_docs:
                selected_docs.append(remaining_docs.pop(0))
            
            # Select remaining documents balancing relevance and diversity
            while remaining_docs and len(selected_docs) < strategy.max_total_results:
                best_doc = None
                best_mmr_score = -1.0
                
                for doc in remaining_docs:
                    # Calculate MMR score
                    relevance_score = doc.composite_score
                    diversity_score = self._calculate_diversity_from_selected(
                        doc, selected_docs
                    )
                    
                    mmr_score = (
                        (1 - strategy.diversity_weight) * relevance_score +
                        strategy.diversity_weight * diversity_score
                    )
                    
                    if mmr_score > best_mmr_score:
                        best_mmr_score = mmr_score
                        best_doc = doc
                
                if best_doc:
                    selected_docs.append(best_doc)
                    remaining_docs.remove(best_doc)
                else:
                    break
            
            logger.info(f"Diversity optimization: selected {len(selected_docs)} diverse documents")
            return selected_docs
            
        except Exception as e:
            logger.error(f"Diversity optimization failed: {str(e)}")
            return documents
    
    def _calculate_diversity_from_selected(
        self,
        candidate_doc: UnifiedDocument,
        selected_docs: List[UnifiedDocument]
    ) -> float:
        """Calculate diversity score relative to already selected documents"""
        try:
            if not selected_docs:
                return 1.0
            
            diversity_factors = []
            
            for selected_doc in selected_docs:
                # Provider diversity
                provider_diff = 0.0 if candidate_doc.source_provider == selected_doc.source_provider else 1.0
                diversity_factors.append(('provider', provider_diff, 0.3))
                
                # Jurisdiction diversity
                jurisdiction_diff = 0.0 if candidate_doc.jurisdiction == selected_doc.jurisdiction else 1.0
                diversity_factors.append(('jurisdiction', jurisdiction_diff, 0.3))
                
                # Content type diversity
                content_diff = 0.0 if candidate_doc.document_type == selected_doc.document_type else 1.0
                diversity_factors.append(('content_type', content_diff, 0.2))
                
                # Date diversity
                date_diff = self._calculate_date_diversity(candidate_doc, selected_doc)
                diversity_factors.append(('date', date_diff, 0.2))
            
            # Calculate average diversity
            if diversity_factors:
                total_weight = sum(weight for _, _, weight in diversity_factors)
                weighted_diversity = sum(
                    diversity * weight for _, diversity, weight in diversity_factors
                )
                return weighted_diversity / total_weight
            
            return 0.5
            
        except Exception as e:
            logger.error(f"Diversity calculation failed: {str(e)}")
            return 0.5
    
    def _calculate_date_diversity(
        self,
        doc1: UnifiedDocument,
        doc2: UnifiedDocument
    ) -> float:
        """Calculate date-based diversity"""
        try:
            date1 = doc1.decision_date or doc1.publication_date
            date2 = doc2.decision_date or doc2.publication_date
            
            if not date1 or not date2:
                return 0.5
            
            # Calculate years difference
            years_diff = abs((date1 - date2).days) / 365.25
            
            # Diversity increases with time difference
            if years_diff >= 10:
                return 1.0
            elif years_diff >= 5:
                return 0.8
            elif years_diff >= 2:
                return 0.6
            elif years_diff >= 1:
                return 0.4
            else:
                return 0.2
                
        except:
            return 0.5
    
    async def _create_unified_result(
        self,
        documents: List[UnifiedDocument],
        query: UnifiedQuery,
        provider_results: Dict[str, UnifiedSearchResult],
        strategy: SearchStrategy
    ) -> UnifiedSearchResult:
        """Create the final unified search result with metrics"""
        try:
            # Calculate metrics
            total_cost = sum(result.total_cost for result in provider_results.values())
            
            provider_result_counts = {}
            provider_response_times = {}
            cost_by_provider = {}
            successful_providers = []
            failed_providers = []
            
            for provider_key, result in provider_results.items():
                provider_result_counts[provider_key] = result.total_results
                provider_response_times[provider_key] = result.search_time_ms
                cost_by_provider[provider_key] = result.total_cost
                
                if result.providers_failed:
                    failed_providers.extend(result.providers_failed)
                else:
                    # This would need proper provider mapping
                    pass  # Add successful provider logic
            
            # Calculate quality metrics
            avg_relevance = sum(doc.relevance_score for doc in documents) / max(len(documents), 1)
            
            # Create fusion metrics
            fusion_metrics = FusionMetrics(
                total_input_documents=sum(len(r.documents) for r in provider_results.values()),
                deduplicated_documents=len(documents),
                final_ranked_documents=len(documents),
                average_relevance_score=avg_relevance,
                diversity_index=self._calculate_diversity_index(documents),
                authority_distribution=self._calculate_authority_distribution(documents),
                provider_distribution=self._calculate_provider_distribution(documents)
            )
            
            # Create unified result
            unified_result = UnifiedSearchResult(
                query=query,
                total_results=len(documents),
                results_returned=len(documents),
                documents=documents,
                provider_results=provider_result_counts,
                provider_response_times=provider_response_times,
                providers_searched=successful_providers,
                providers_failed=failed_providers,
                average_relevance=avg_relevance,
                total_cost=total_cost,
                cost_by_provider=cost_by_provider
            )
            
            # Add fusion metrics to metadata
            unified_result.provider_metadata = {
                "fusion_metrics": fusion_metrics.__dict__
            }
            
            return unified_result
            
        except Exception as e:
            logger.error(f"Unified result creation failed: {str(e)}")
            return self._create_empty_result(query, provider_results)
    
    def _calculate_diversity_index(self, documents: List[UnifiedDocument]) -> float:
        """Calculate overall diversity index"""
        try:
            if len(documents) <= 1:
                return 1.0
            
            # Provider diversity
            providers = [doc.source_provider for doc in documents]
            provider_diversity = len(set(providers)) / len(providers)
            
            # Jurisdiction diversity
            jurisdictions = [doc.jurisdiction for doc in documents if doc.jurisdiction]
            jurisdiction_diversity = len(set(jurisdictions)) / max(len(jurisdictions), 1)
            
            # Content type diversity
            content_types = [doc.document_type for doc in documents]
            content_diversity = len(set(content_types)) / len(content_types)
            
            # Combined diversity
            return (provider_diversity + jurisdiction_diversity + content_diversity) / 3
            
        except:
            return 0.5
    
    def _calculate_authority_distribution(self, documents: List[UnifiedDocument]) -> Dict[str, int]:
        """Calculate distribution of authority levels"""
        distribution = {"high": 0, "medium": 0, "low": 0}
        
        for doc in documents:
            if doc.authority_score >= 0.8:
                distribution["high"] += 1
            elif doc.authority_score >= 0.5:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1
        
        return distribution
    
    def _calculate_provider_distribution(self, documents: List[UnifiedDocument]) -> Dict[str, int]:
        """Calculate distribution by provider"""
        distribution = defaultdict(int)
        
        for doc in documents:
            provider_name = doc.source_provider.value if doc.source_provider else "unknown"
            distribution[provider_name] += 1
        
        return dict(distribution)
    
    def _create_empty_result(
        self,
        query: UnifiedQuery,
        provider_results: Dict[str, UnifiedSearchResult]
    ) -> UnifiedSearchResult:
        """Create empty result when fusion fails"""
        failed_providers = []
        for result in provider_results.values():
            failed_providers.extend(result.providers_failed)
        
        return UnifiedSearchResult(
            query=query,
            providers_failed=failed_providers
        )