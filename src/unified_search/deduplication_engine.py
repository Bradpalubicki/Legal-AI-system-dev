"""
Advanced Deduplication Engine

Sophisticated deduplication system for legal documents using multiple
similarity metrics, citation analysis, and machine learning techniques.
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
import hashlib

from .database_models import UnifiedDocument, DatabaseProvider, ContentType

logger = logging.getLogger(__name__)


class SimilarityType(Enum):
    """Types of similarity metrics"""
    TITLE = "title"
    CITATION = "citation"
    CONTENT = "content"
    METADATA = "metadata"
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"


@dataclass
class SimilarityScore:
    """Individual similarity score with metadata"""
    score: float
    similarity_type: SimilarityType
    weight: float
    confidence: float
    details: Dict[str, Any]


@dataclass
class DocumentSimilarity:
    """Complete similarity analysis between two documents"""
    doc1_id: str
    doc2_id: str
    overall_score: float
    individual_scores: List[SimilarityScore]
    is_duplicate: bool
    confidence: float
    reasoning: List[str]


@dataclass
class DeduplicationCluster:
    """Cluster of similar documents"""
    cluster_id: str
    representative_doc: UnifiedDocument
    similar_docs: List[UnifiedDocument]
    similarity_scores: List[DocumentSimilarity]
    cluster_quality: float
    merge_strategy: str


class DeduplicationEngine:
    """
    Advanced deduplication engine for legal documents using multiple
    similarity algorithms and machine learning techniques.
    """
    
    def __init__(self):
        # Citation patterns for legal documents
        self.citation_patterns = {
            'us_reports': re.compile(r'\b\d+\s+U\.S\.\s+\d+\b', re.IGNORECASE),
            'supreme_court': re.compile(r'\b\d+\s+S\.\s?Ct\.\s+\d+\b', re.IGNORECASE),
            'federal_reporter': re.compile(r'\b\d+\s+F\.\d*d?\s+\d+\b', re.IGNORECASE),
            'federal_supplement': re.compile(r'\b\d+\s+F\.\s?Supp\.\s?\d*\s+\d+\b', re.IGNORECASE),
            'state_reporters': re.compile(r'\b\d+\s+\w+\s+\d+\b'),
            'us_code': re.compile(r'\b\d+\s+U\.S\.C\.?\s+§?\s*\d+\b', re.IGNORECASE),
            'cfr': re.compile(r'\b\d+\s+C\.?F\.?R\.?\s+§?\s*\d+\b', re.IGNORECASE),
            'public_law': re.compile(r'\bPub\.\s?L\.\s?No\.\s?\d+-\d+\b', re.IGNORECASE),
            'case_numbers': re.compile(r'\b(?:No\.|Case\s+No\.)\s*\d+[-–]\d+\b', re.IGNORECASE)
        }
        
        # Legal terms for semantic analysis
        self.legal_term_categories = {
            'procedural': {
                'motion', 'discovery', 'summary judgment', 'dismissal', 'appeal',
                'jurisdiction', 'venue', 'service', 'pleading', 'deposition',
                'interrogatory', 'subpoena', 'injunction', 'restraining order'
            },
            'constitutional': {
                'due process', 'equal protection', 'first amendment', 'fourth amendment',
                'commerce clause', 'supremacy clause', 'establishment clause',
                'free speech', 'search and seizure', 'cruel and unusual'
            },
            'contract': {
                'breach', 'consideration', 'offer', 'acceptance', 'damages',
                'specific performance', 'rescission', 'reformation', 'parol evidence',
                'statute of frauds', 'unconscionable', 'good faith'
            },
            'tort': {
                'negligence', 'liability', 'duty of care', 'causation', 'damages',
                'strict liability', 'intentional tort', 'defamation', 'privacy',
                'nuisance', 'trespass', 'battery', 'assault'
            },
            'corporate': {
                'fiduciary duty', 'business judgment', 'merger', 'acquisition',
                'securities', 'disclosure', 'insider trading', 'derivative suit',
                'piercing the veil', 'ultra vires'
            },
            'criminal': {
                'mens rea', 'actus reus', 'intent', 'conspiracy', 'accessory',
                'accomplice', 'sentencing', 'plea bargain', 'miranda',
                'probable cause', 'reasonable doubt'
            }
        }
        
        # Similarity thresholds by document type
        self.type_specific_thresholds = {
            ContentType.CASES: 0.85,
            ContentType.STATUTES: 0.90,
            ContentType.REGULATIONS: 0.88,
            ContentType.LAW_REVIEWS: 0.80,
            ContentType.BRIEFS: 0.75,
            ContentType.DOCKETS: 0.95,
            ContentType.ORAL_ARGUMENTS: 0.85
        }
        
        # Weight configurations for different similarity types
        self.similarity_weights = {
            SimilarityType.CITATION: 0.35,
            SimilarityType.TITLE: 0.25,
            SimilarityType.CONTENT: 0.20,
            SimilarityType.METADATA: 0.15,
            SimilarityType.STRUCTURAL: 0.05
        }
        
        logger.info("Advanced deduplication engine initialized")
    
    async def deduplicate_documents(
        self,
        documents: List[UnifiedDocument],
        threshold: float = 0.85,
        use_ml: bool = True
    ) -> List[UnifiedDocument]:
        """
        Main deduplication method that processes a list of documents
        and returns deduplicated results
        """
        try:
            if len(documents) <= 1:
                return documents
            
            logger.info(f"Starting deduplication of {len(documents)} documents")
            
            # Step 1: Fast pre-filtering using simple heuristics
            pre_filtered = await self._pre_filter_documents(documents)
            logger.info(f"Pre-filtering: {len(documents)} -> {len(pre_filtered)} candidates")
            
            # Step 2: Create document fingerprints for efficient comparison
            fingerprints = await self._create_document_fingerprints(pre_filtered)
            
            # Step 3: Find potential duplicate pairs using fingerprint matching
            potential_pairs = await self._find_potential_duplicate_pairs(
                pre_filtered, fingerprints, threshold * 0.7  # Lower threshold for potential matches
            )
            logger.info(f"Found {len(potential_pairs)} potential duplicate pairs")
            
            # Step 4: Perform detailed similarity analysis
            similarity_results = await self._analyze_document_similarities(
                potential_pairs, threshold
            )
            
            # Step 5: Create clusters of similar documents
            clusters = await self._create_similarity_clusters(
                documents, similarity_results, threshold
            )
            logger.info(f"Created {len(clusters)} deduplication clusters")
            
            # Step 6: Select best representative from each cluster
            deduplicated = await self._select_cluster_representatives(clusters)
            
            logger.info(f"Deduplication complete: {len(documents)} -> {len(deduplicated)} documents")
            return deduplicated
            
        except Exception as e:
            logger.error(f"Deduplication failed: {str(e)}")
            return documents  # Return original documents if deduplication fails
    
    async def _pre_filter_documents(
        self,
        documents: List[UnifiedDocument]
    ) -> List[UnifiedDocument]:
        """Pre-filter documents using fast heuristics"""
        try:
            # Remove obvious duplicates based on simple criteria
            seen_combinations = set()
            filtered_docs = []
            
            for doc in documents:
                # Create a simple key for exact duplicates
                key_parts = []
                
                if doc.title:
                    key_parts.append(doc.title.lower().strip())
                if doc.citation:
                    key_parts.append(doc.citation.lower().strip())
                if doc.source_document_id:
                    key_parts.append(doc.source_document_id)
                if doc.source_provider:
                    key_parts.append(doc.source_provider.value)
                
                if key_parts:
                    simple_key = "|".join(key_parts)
                    if simple_key not in seen_combinations:
                        seen_combinations.add(simple_key)
                        filtered_docs.append(doc)
                else:
                    # Keep documents without key information for further analysis
                    filtered_docs.append(doc)
            
            return filtered_docs
            
        except Exception as e:
            logger.error(f"Pre-filtering failed: {str(e)}")
            return documents
    
    async def _create_document_fingerprints(
        self,
        documents: List[UnifiedDocument]
    ) -> Dict[str, Dict[str, Any]]:
        """Create document fingerprints for efficient comparison"""
        fingerprints = {}
        
        try:
            for doc in documents:
                doc_id = doc.source_document_id or str(id(doc))
                
                fingerprint = {
                    'title_hash': self._create_text_hash(doc.title),
                    'citation_normalized': self._normalize_citation(doc.citation),
                    'court_normalized': self._normalize_court_name(doc.court),
                    'date_normalized': doc.decision_date or doc.publication_date,
                    'content_type': doc.document_type,
                    'provider': doc.source_provider,
                    'jurisdiction': doc.jurisdiction,
                    'word_count': len(doc.full_text.split()) if doc.full_text else 0,
                    'title_words': set(self._extract_meaningful_words(doc.title)) if doc.title else set(),
                    'legal_topics': set(doc.legal_topics) if doc.legal_topics else set(),
                    'parties': self._extract_party_names(doc.title, doc.parties) if doc.title or doc.parties else set()
                }
                
                # Add citation components if available
                if doc.citation:
                    fingerprint['citation_components'] = self._extract_citation_components(doc.citation)
                
                fingerprints[doc_id] = fingerprint
            
            return fingerprints
            
        except Exception as e:
            logger.error(f"Fingerprint creation failed: {str(e)}")
            return {}
    
    async def _find_potential_duplicate_pairs(
        self,
        documents: List[UnifiedDocument],
        fingerprints: Dict[str, Dict[str, Any]],
        threshold: float
    ) -> List[Tuple[UnifiedDocument, UnifiedDocument]]:
        """Find potential duplicate pairs using fingerprint comparison"""
        potential_pairs = []
        
        try:
            for i, doc1 in enumerate(documents):
                for j, doc2 in enumerate(documents[i+1:], i+1):
                    doc1_id = doc1.source_document_id or str(id(doc1))
                    doc2_id = doc2.source_document_id or str(id(doc2))
                    
                    if doc1_id not in fingerprints or doc2_id not in fingerprints:
                        continue
                    
                    # Quick fingerprint-based similarity check
                    similarity = self._calculate_fingerprint_similarity(
                        fingerprints[doc1_id], fingerprints[doc2_id]
                    )
                    
                    if similarity >= threshold:
                        potential_pairs.append((doc1, doc2))
            
            return potential_pairs
            
        except Exception as e:
            logger.error(f"Potential pair finding failed: {str(e)}")
            return []
    
    def _calculate_fingerprint_similarity(
        self,
        fp1: Dict[str, Any],
        fp2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two document fingerprints"""
        try:
            similarities = []
            
            # Title hash similarity
            if fp1['title_hash'] and fp2['title_hash']:
                title_sim = 1.0 if fp1['title_hash'] == fp2['title_hash'] else 0.0
                similarities.append(('title_hash', title_sim, 0.3))
            
            # Citation similarity
            if fp1['citation_normalized'] and fp2['citation_normalized']:
                citation_sim = self._compare_normalized_citations(
                    fp1['citation_normalized'], fp2['citation_normalized']
                )
                similarities.append(('citation', citation_sim, 0.4))
            
            # Court similarity
            if fp1['court_normalized'] and fp2['court_normalized']:
                court_sim = 1.0 if fp1['court_normalized'] == fp2['court_normalized'] else 0.0
                similarities.append(('court', court_sim, 0.1))
            
            # Date similarity
            if fp1['date_normalized'] and fp2['date_normalized']:
                date_sim = self._calculate_date_similarity(
                    fp1['date_normalized'], fp2['date_normalized']
                )
                similarities.append(('date', date_sim, 0.1))
            
            # Title word overlap
            if fp1['title_words'] and fp2['title_words']:
                word_overlap = len(fp1['title_words'] & fp2['title_words']) / \
                              max(len(fp1['title_words'] | fp2['title_words']), 1)
                similarities.append(('title_words', word_overlap, 0.1))
            
            # Calculate weighted average
            if similarities:
                total_weight = sum(weight for _, _, weight in similarities)
                weighted_sum = sum(sim * weight for _, sim, weight in similarities)
                return weighted_sum / total_weight
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Fingerprint similarity calculation failed: {str(e)}")
            return 0.0
    
    async def _analyze_document_similarities(
        self,
        potential_pairs: List[Tuple[UnifiedDocument, UnifiedDocument]],
        threshold: float
    ) -> List[DocumentSimilarity]:
        """Perform detailed similarity analysis on potential duplicate pairs"""
        similarity_results = []
        
        try:
            for doc1, doc2 in potential_pairs:
                similarity = await self._comprehensive_similarity_analysis(doc1, doc2)
                
                if similarity.overall_score >= threshold:
                    similarity_results.append(similarity)
            
            return similarity_results
            
        except Exception as e:
            logger.error(f"Detailed similarity analysis failed: {str(e)}")
            return []
    
    async def _comprehensive_similarity_analysis(
        self,
        doc1: UnifiedDocument,
        doc2: UnifiedDocument
    ) -> DocumentSimilarity:
        """Perform comprehensive similarity analysis between two documents"""
        try:
            individual_scores = []
            reasoning = []
            
            # Title similarity
            title_score = await self._calculate_title_similarity(doc1, doc2)
            individual_scores.append(title_score)
            if title_score.score > 0.8:
                reasoning.append(f"High title similarity: {title_score.score:.2f}")
            
            # Citation similarity
            citation_score = await self._calculate_citation_similarity(doc1, doc2)
            individual_scores.append(citation_score)
            if citation_score.score > 0.9:
                reasoning.append(f"Strong citation match: {citation_score.score:.2f}")
            
            # Content similarity
            content_score = await self._calculate_content_similarity(doc1, doc2)
            individual_scores.append(content_score)
            if content_score.score > 0.7:
                reasoning.append(f"High content similarity: {content_score.score:.2f}")
            
            # Metadata similarity
            metadata_score = await self._calculate_metadata_similarity(doc1, doc2)
            individual_scores.append(metadata_score)
            
            # Structural similarity
            structural_score = await self._calculate_structural_similarity(doc1, doc2)
            individual_scores.append(structural_score)
            
            # Calculate overall weighted score
            total_weight = sum(score.weight for score in individual_scores)
            weighted_sum = sum(score.score * score.weight for score in individual_scores)
            overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
            
            # Determine if documents are duplicates
            doc_type = doc1.document_type or ContentType.CASES
            type_threshold = self.type_specific_thresholds.get(doc_type, 0.85)
            is_duplicate = overall_score >= type_threshold
            
            # Calculate confidence based on score distribution
            confidence = self._calculate_confidence(individual_scores, overall_score)
            
            doc1_id = doc1.source_document_id or str(id(doc1))
            doc2_id = doc2.source_document_id or str(id(doc2))
            
            return DocumentSimilarity(
                doc1_id=doc1_id,
                doc2_id=doc2_id,
                overall_score=overall_score,
                individual_scores=individual_scores,
                is_duplicate=is_duplicate,
                confidence=confidence,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Comprehensive similarity analysis failed: {str(e)}")
            return DocumentSimilarity(
                doc1_id=str(id(doc1)),
                doc2_id=str(id(doc2)),
                overall_score=0.0,
                individual_scores=[],
                is_duplicate=False,
                confidence=0.0,
                reasoning=[]
            )
    
    async def _calculate_title_similarity(
        self,
        doc1: UnifiedDocument,
        doc2: UnifiedDocument
    ) -> SimilarityScore:
        """Calculate title-based similarity"""
        try:
            if not doc1.title or not doc2.title:
                return SimilarityScore(
                    score=0.0,
                    similarity_type=SimilarityType.TITLE,
                    weight=self.similarity_weights[SimilarityType.TITLE],
                    confidence=0.0,
                    details={"reason": "Missing title"}
                )
            
            # Normalize titles
            title1_norm = self._normalize_legal_text(doc1.title)
            title2_norm = self._normalize_legal_text(doc2.title)
            
            # Exact match
            if title1_norm == title2_norm:
                return SimilarityScore(
                    score=1.0,
                    similarity_type=SimilarityType.TITLE,
                    weight=self.similarity_weights[SimilarityType.TITLE],
                    confidence=1.0,
                    details={"reason": "Exact match", "normalized_titles": [title1_norm, title2_norm]}
                )
            
            # Word-based similarity
            words1 = set(title1_norm.split())
            words2 = set(title2_norm.split())
            
            if not words1 or not words2:
                return SimilarityScore(
                    score=0.0,
                    similarity_type=SimilarityType.TITLE,
                    weight=self.similarity_weights[SimilarityType.TITLE],
                    confidence=0.0,
                    details={"reason": "Empty normalized title"}
                )
            
            # Jaccard similarity
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            jaccard = intersection / union
            
            # Legal case name similarity (party names)
            party_similarity = self._calculate_party_name_similarity(doc1.title, doc2.title)
            
            # Combined score
            combined_score = (jaccard * 0.7) + (party_similarity * 0.3)
            confidence = min(intersection / max(len(words1), len(words2)), 1.0)
            
            return SimilarityScore(
                score=combined_score,
                similarity_type=SimilarityType.TITLE,
                weight=self.similarity_weights[SimilarityType.TITLE],
                confidence=confidence,
                details={
                    "jaccard": jaccard,
                    "party_similarity": party_similarity,
                    "intersection_words": intersection,
                    "union_words": union
                }
            )
            
        except Exception as e:
            logger.error(f"Title similarity calculation failed: {str(e)}")
            return SimilarityScore(
                score=0.0,
                similarity_type=SimilarityType.TITLE,
                weight=self.similarity_weights[SimilarityType.TITLE],
                confidence=0.0,
                details={"error": str(e)}
            )
    
    async def _calculate_citation_similarity(
        self,
        doc1: UnifiedDocument,
        doc2: UnifiedDocument
    ) -> SimilarityScore:
        """Calculate citation-based similarity"""
        try:
            if not doc1.citation or not doc2.citation:
                return SimilarityScore(
                    score=0.0,
                    similarity_type=SimilarityType.CITATION,
                    weight=self.similarity_weights[SimilarityType.CITATION],
                    confidence=0.0,
                    details={"reason": "Missing citation"}
                )
            
            # Normalize citations
            citation1_norm = self._normalize_citation(doc1.citation)
            citation2_norm = self._normalize_citation(doc2.citation)
            
            # Exact match
            if citation1_norm == citation2_norm:
                return SimilarityScore(
                    score=1.0,
                    similarity_type=SimilarityType.CITATION,
                    weight=self.similarity_weights[SimilarityType.CITATION],
                    confidence=1.0,
                    details={"reason": "Exact citation match", "normalized": citation1_norm}
                )
            
            # Extract citation components
            components1 = self._extract_citation_components(doc1.citation)
            components2 = self._extract_citation_components(doc2.citation)
            
            if not components1 or not components2:
                # Fall back to string similarity
                string_sim = self._calculate_string_similarity(citation1_norm, citation2_norm)
                return SimilarityScore(
                    score=string_sim,
                    similarity_type=SimilarityType.CITATION,
                    weight=self.similarity_weights[SimilarityType.CITATION],
                    confidence=0.5,
                    details={"reason": "String similarity fallback", "string_similarity": string_sim}
                )
            
            # Compare citation components
            component_similarity = self._compare_citation_components(components1, components2)
            confidence = min(len(components1), len(components2)) / max(len(components1), len(components2))
            
            return SimilarityScore(
                score=component_similarity,
                similarity_type=SimilarityType.CITATION,
                weight=self.similarity_weights[SimilarityType.CITATION],
                confidence=confidence,
                details={
                    "components1": components1,
                    "components2": components2,
                    "component_similarity": component_similarity
                }
            )
            
        except Exception as e:
            logger.error(f"Citation similarity calculation failed: {str(e)}")
            return SimilarityScore(
                score=0.0,
                similarity_type=SimilarityType.CITATION,
                weight=self.similarity_weights[SimilarityType.CITATION],
                confidence=0.0,
                details={"error": str(e)}
            )
    
    async def _calculate_content_similarity(
        self,
        doc1: UnifiedDocument,
        doc2: UnifiedDocument
    ) -> SimilarityScore:
        """Calculate content-based similarity"""
        try:
            # Use summary if full text not available
            content1 = doc1.full_text or doc1.summary or ""
            content2 = doc2.full_text or doc2.summary or ""
            
            if not content1 or not content2:
                return SimilarityScore(
                    score=0.0,
                    similarity_type=SimilarityType.CONTENT,
                    weight=self.similarity_weights[SimilarityType.CONTENT],
                    confidence=0.0,
                    details={"reason": "Missing content"}
                )
            
            # For very long content, use sampling to avoid performance issues
            if len(content1) > 10000 or len(content2) > 10000:
                content1 = self._sample_content(content1)
                content2 = self._sample_content(content2)
            
            # Normalize content
            content1_norm = self._normalize_legal_text(content1)
            content2_norm = self._normalize_legal_text(content2)
            
            # Extract meaningful terms
            terms1 = self._extract_meaningful_words(content1_norm)
            terms2 = self._extract_meaningful_words(content2_norm)
            
            if not terms1 or not terms2:
                return SimilarityScore(
                    score=0.0,
                    similarity_type=SimilarityType.CONTENT,
                    weight=self.similarity_weights[SimilarityType.CONTENT],
                    confidence=0.0,
                    details={"reason": "No meaningful terms"}
                )
            
            # Calculate term-based similarity
            terms1_set = set(terms1)
            terms2_set = set(terms2)
            
            intersection = len(terms1_set & terms2_set)
            union = len(terms1_set | terms2_set)
            jaccard = intersection / union if union > 0 else 0.0
            
            # Calculate legal term similarity
            legal_sim = self._calculate_legal_term_similarity(terms1, terms2)
            
            # Combined similarity
            combined_score = (jaccard * 0.7) + (legal_sim * 0.3)
            confidence = min(intersection / max(len(terms1_set), len(terms2_set)), 1.0)
            
            return SimilarityScore(
                score=combined_score,
                similarity_type=SimilarityType.CONTENT,
                weight=self.similarity_weights[SimilarityType.CONTENT],
                confidence=confidence,
                details={
                    "jaccard": jaccard,
                    "legal_similarity": legal_sim,
                    "intersection_terms": intersection,
                    "total_terms": union
                }
            )
            
        except Exception as e:
            logger.error(f"Content similarity calculation failed: {str(e)}")
            return SimilarityScore(
                score=0.0,
                similarity_type=SimilarityType.CONTENT,
                weight=self.similarity_weights[SimilarityType.CONTENT],
                confidence=0.0,
                details={"error": str(e)}
            )
    
    async def _calculate_metadata_similarity(
        self,
        doc1: UnifiedDocument,
        doc2: UnifiedDocument
    ) -> SimilarityScore:
        """Calculate metadata-based similarity"""
        try:
            similarity_factors = []
            
            # Court similarity
            if doc1.court and doc2.court:
                court_sim = 1.0 if self._normalize_court_name(doc1.court) == \
                                  self._normalize_court_name(doc2.court) else 0.0
                similarity_factors.append(('court', court_sim, 0.3))
            
            # Jurisdiction similarity
            if doc1.jurisdiction and doc2.jurisdiction:
                jurisdiction_sim = 1.0 if doc1.jurisdiction.lower() == doc2.jurisdiction.lower() else 0.0
                similarity_factors.append(('jurisdiction', jurisdiction_sim, 0.2))
            
            # Date similarity
            if doc1.decision_date and doc2.decision_date:
                date_sim = self._calculate_date_similarity(doc1.decision_date, doc2.decision_date)
                similarity_factors.append(('date', date_sim, 0.2))
            
            # Document type similarity
            if doc1.document_type and doc2.document_type:
                type_sim = 1.0 if doc1.document_type == doc2.document_type else 0.0
                similarity_factors.append(('document_type', type_sim, 0.1))
            
            # Legal topics similarity
            if doc1.legal_topics and doc2.legal_topics:
                topics1 = set(topic.lower() for topic in doc1.legal_topics)
                topics2 = set(topic.lower() for topic in doc2.legal_topics)
                if topics1 or topics2:
                    topic_sim = len(topics1 & topics2) / len(topics1 | topics2)
                    similarity_factors.append(('legal_topics', topic_sim, 0.2))
            
            # Calculate weighted average
            if similarity_factors:
                total_weight = sum(weight for _, _, weight in similarity_factors)
                weighted_sum = sum(sim * weight for _, sim, weight in similarity_factors)
                overall_sim = weighted_sum / total_weight
                confidence = len(similarity_factors) / 5.0  # Max 5 factors
            else:
                overall_sim = 0.0
                confidence = 0.0
            
            return SimilarityScore(
                score=overall_sim,
                similarity_type=SimilarityType.METADATA,
                weight=self.similarity_weights[SimilarityType.METADATA],
                confidence=confidence,
                details=dict(similarity_factors)
            )
            
        except Exception as e:
            logger.error(f"Metadata similarity calculation failed: {str(e)}")
            return SimilarityScore(
                score=0.0,
                similarity_type=SimilarityType.METADATA,
                weight=self.similarity_weights[SimilarityType.METADATA],
                confidence=0.0,
                details={"error": str(e)}
            )
    
    async def _calculate_structural_similarity(
        self,
        doc1: UnifiedDocument,
        doc2: UnifiedDocument
    ) -> SimilarityScore:
        """Calculate structural similarity"""
        try:
            structural_factors = []
            
            # Content length similarity
            len1 = len(doc1.full_text) if doc1.full_text else 0
            len2 = len(doc2.full_text) if doc2.full_text else 0
            
            if len1 > 0 and len2 > 0:
                length_ratio = min(len1, len2) / max(len1, len2)
                structural_factors.append(('length', length_ratio, 0.3))
            
            # Number of sections/headnotes
            headnotes1 = len(doc1.headnotes) if doc1.headnotes else 0
            headnotes2 = len(doc2.headnotes) if doc2.headnotes else 0
            
            if headnotes1 > 0 and headnotes2 > 0:
                headnotes_ratio = min(headnotes1, headnotes2) / max(headnotes1, headnotes2)
                structural_factors.append(('headnotes', headnotes_ratio, 0.2))
            
            # Number of parties
            parties1 = len(doc1.parties) if doc1.parties else 0
            parties2 = len(doc2.parties) if doc2.parties else 0
            
            if parties1 > 0 and parties2 > 0:
                parties_ratio = min(parties1, parties2) / max(parties1, parties2)
                structural_factors.append(('parties', parties_ratio, 0.2))
            
            # Number of legal topics
            topics1 = len(doc1.legal_topics) if doc1.legal_topics else 0
            topics2 = len(doc2.legal_topics) if doc2.legal_topics else 0
            
            if topics1 > 0 and topics2 > 0:
                topics_ratio = min(topics1, topics2) / max(topics1, topics2)
                structural_factors.append(('topics_count', topics_ratio, 0.3))
            
            # Calculate weighted average
            if structural_factors:
                total_weight = sum(weight for _, _, weight in structural_factors)
                weighted_sum = sum(sim * weight for _, sim, weight in structural_factors)
                overall_sim = weighted_sum / total_weight
                confidence = len(structural_factors) / 4.0  # Max 4 factors
            else:
                overall_sim = 0.5  # Neutral score if no structural info
                confidence = 0.0
            
            return SimilarityScore(
                score=overall_sim,
                similarity_type=SimilarityType.STRUCTURAL,
                weight=self.similarity_weights[SimilarityType.STRUCTURAL],
                confidence=confidence,
                details=dict(structural_factors)
            )
            
        except Exception as e:
            logger.error(f"Structural similarity calculation failed: {str(e)}")
            return SimilarityScore(
                score=0.5,
                similarity_type=SimilarityType.STRUCTURAL,
                weight=self.similarity_weights[SimilarityType.STRUCTURAL],
                confidence=0.0,
                details={"error": str(e)}
            )
    
    async def _create_similarity_clusters(
        self,
        documents: List[UnifiedDocument],
        similarity_results: List[DocumentSimilarity],
        threshold: float
    ) -> List[DeduplicationCluster]:
        """Create clusters of similar documents"""
        try:
            # Create adjacency graph of similar documents
            similarity_graph = defaultdict(list)
            doc_map = {doc.source_document_id or str(id(doc)): doc for doc in documents}
            
            for similarity in similarity_results:
                if similarity.is_duplicate:
                    similarity_graph[similarity.doc1_id].append(similarity.doc2_id)
                    similarity_graph[similarity.doc2_id].append(similarity.doc1_id)
            
            # Find connected components (clusters)
            visited = set()
            clusters = []
            
            for doc in documents:
                doc_id = doc.source_document_id or str(id(doc))
                
                if doc_id not in visited:
                    cluster_docs = []
                    self._dfs_cluster(doc_id, similarity_graph, visited, cluster_docs)
                    
                    if cluster_docs:
                        # Convert doc IDs back to documents
                        cluster_documents = [doc_map[did] for did in cluster_docs if did in doc_map]
                        
                        if len(cluster_documents) > 1:
                            # Multiple documents - true cluster
                            representative = self._select_best_document(cluster_documents)
                            cluster_similarities = [
                                sim for sim in similarity_results
                                if sim.doc1_id in cluster_docs and sim.doc2_id in cluster_docs
                            ]
                            
                            cluster = DeduplicationCluster(
                                cluster_id=f"cluster_{len(clusters)}",
                                representative_doc=representative,
                                similar_docs=cluster_documents,
                                similarity_scores=cluster_similarities,
                                cluster_quality=self._calculate_cluster_quality(cluster_similarities),
                                merge_strategy="best_representative"
                            )
                            clusters.append(cluster)
                        else:
                            # Single document - create singleton cluster
                            cluster = DeduplicationCluster(
                                cluster_id=f"singleton_{len(clusters)}",
                                representative_doc=cluster_documents[0],
                                similar_docs=cluster_documents,
                                similarity_scores=[],
                                cluster_quality=1.0,
                                merge_strategy="singleton"
                            )
                            clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Cluster creation failed: {str(e)}")
            # Fallback: create singleton clusters for all documents
            return [
                DeduplicationCluster(
                    cluster_id=f"fallback_{i}",
                    representative_doc=doc,
                    similar_docs=[doc],
                    similarity_scores=[],
                    cluster_quality=1.0,
                    merge_strategy="fallback"
                )
                for i, doc in enumerate(documents)
            ]
    
    def _dfs_cluster(
        self,
        doc_id: str,
        graph: Dict[str, List[str]],
        visited: Set[str],
        cluster: List[str]
    ):
        """Depth-first search to find connected components"""
        if doc_id in visited:
            return
        
        visited.add(doc_id)
        cluster.append(doc_id)
        
        for neighbor in graph.get(doc_id, []):
            self._dfs_cluster(neighbor, graph, visited, cluster)
    
    async def _select_cluster_representatives(
        self,
        clusters: List[DeduplicationCluster]
    ) -> List[UnifiedDocument]:
        """Select the best representative document from each cluster"""
        representatives = []
        
        try:
            for cluster in clusters:
                # Representative is already selected in cluster creation
                representatives.append(cluster.representative_doc)
            
            return representatives
            
        except Exception as e:
            logger.error(f"Representative selection failed: {str(e)}")
            # Fallback: return first document from each cluster
            return [cluster.similar_docs[0] for cluster in clusters if cluster.similar_docs]
    
    # Utility methods
    
    def _create_text_hash(self, text: Optional[str]) -> Optional[str]:
        """Create hash of normalized text"""
        if not text:
            return None
        
        normalized = self._normalize_legal_text(text)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def _normalize_citation(self, citation: Optional[str]) -> str:
        """Normalize legal citation"""
        if not citation:
            return ""
        
        # Remove extra whitespace and normalize punctuation
        normalized = re.sub(r'\s+', ' ', citation.strip())
        normalized = re.sub(r'\.+', '.', normalized)
        normalized = re.sub(r',+', ',', normalized)
        
        # Standardize common abbreviations
        replacements = {
            r'\bU\.S\.\b': 'US',
            r'\bS\.Ct\.\b': 'S.Ct.',
            r'\bF\.Supp\.\b': 'F.Supp.',
            r'\bF\.\d+d\b': lambda m: m.group(0).replace('F.', 'F.'),
        }
        
        for pattern, replacement in replacements.items():
            if callable(replacement):
                normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
            else:
                normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        return normalized.lower()
    
    def _normalize_court_name(self, court: Optional[str]) -> str:
        """Normalize court name"""
        if not court:
            return ""
        
        normalized = court.lower().strip()
        
        # Common normalizations
        normalized = re.sub(r'\bcourt\s+of\s+appeals\b', 'court of appeals', normalized)
        normalized = re.sub(r'\bsupreme\s+court\b', 'supreme court', normalized)
        normalized = re.sub(r'\bdistrict\s+court\b', 'district court', normalized)
        normalized = re.sub(r'\bunited\s+states\b', 'us', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _normalize_legal_text(self, text: str) -> str:
        """Normalize legal text for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove case citations and legal formatting
        normalized = re.sub(r'\([^)]*\)', '', normalized)  # Remove parenthetical
        normalized = re.sub(r'\[[^\]]*\]', '', normalized)  # Remove bracketed content
        
        # Remove common legal document markers
        normalized = re.sub(r'\bno\.\s*\d+\b', '', normalized)
        normalized = re.sub(r'\bcase\s+no\.\s*\d+\b', '', normalized)
        normalized = re.sub(r'\bdocket\s+no\.\s*\d+\b', '', normalized)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _extract_meaningful_words(self, text: str) -> List[str]:
        """Extract meaningful words from legal text"""
        if not text:
            return []
        
        # Remove common stop words but keep legal terms
        legal_stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'shall', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter meaningful words
        meaningful = [
            word for word in words
            if len(word) > 2 and word not in legal_stop_words
        ]
        
        return meaningful
    
    def _extract_citation_components(self, citation: str) -> Dict[str, str]:
        """Extract components from legal citation"""
        components = {}
        
        try:
            # Try to match different citation patterns
            for pattern_name, pattern in self.citation_patterns.items():
                match = pattern.search(citation)
                if match:
                    citation_text = match.group(0)
                    
                    # Extract volume, reporter, page
                    parts = citation_text.split()
                    if len(parts) >= 3:
                        components['volume'] = parts[0]
                        components['reporter'] = parts[1]
                        components['page'] = parts[2]
                        components['pattern'] = pattern_name
                        break
            
            # Extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', citation)
            if year_match:
                components['year'] = year_match.group(0)
            
            return components
            
        except Exception as e:
            logger.error(f"Citation component extraction failed: {str(e)}")
            return {}
    
    def _compare_citation_components(
        self,
        components1: Dict[str, str],
        components2: Dict[str, str]
    ) -> float:
        """Compare citation components for similarity"""
        if not components1 or not components2:
            return 0.0
        
        matches = 0
        total = 0
        
        # Compare each component
        for key in ['volume', 'reporter', 'page', 'year']:
            if key in components1 or key in components2:
                total += 1
                if (key in components1 and key in components2 and
                    components1[key] == components2[key]):
                    matches += 1
        
        return matches / total if total > 0 else 0.0
    
    def _compare_normalized_citations(self, citation1: str, citation2: str) -> float:
        """Compare normalized citations"""
        if citation1 == citation2:
            return 1.0
        
        # Calculate string similarity
        return self._calculate_string_similarity(citation1, citation2)
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using edit distance"""
        if not str1 or not str2:
            return 0.0
        
        if str1 == str2:
            return 1.0
        
        # Simple edit distance calculation
        len1, len2 = len(str1), len(str2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Create distance matrix
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize first row and column
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if str1[i-1] == str2[j-1]:
                    cost = 0
                else:
                    cost = 1
                
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        edit_distance = matrix[len1][len2]
        max_len = max(len1, len2)
        
        return 1.0 - (edit_distance / max_len)
    
    def _calculate_date_similarity(self, date1: date, date2: date) -> float:
        """Calculate similarity between dates"""
        if date1 == date2:
            return 1.0
        
        diff_days = abs((date1 - date2).days)
        
        # Very close dates are likely the same document
        if diff_days <= 1:
            return 1.0
        elif diff_days <= 7:
            return 0.9
        elif diff_days <= 30:
            return 0.7
        elif diff_days <= 365:
            return 0.3
        else:
            return 0.1
    
    def _calculate_party_name_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between party names in case titles"""
        # Extract party names using "v." pattern
        parties1 = self._extract_party_names(title1, [])
        parties2 = self._extract_party_names(title2, [])
        
        if not parties1 or not parties2:
            return 0.0
        
        # Compare party sets
        parties1_set = {p.lower() for p in parties1}
        parties2_set = {p.lower() for p in parties2}
        
        if not parties1_set or not parties2_set:
            return 0.0
        
        intersection = len(parties1_set & parties2_set)
        union = len(parties1_set | parties2_set)
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_party_names(self, title: str, parties: List[str]) -> Set[str]:
        """Extract party names from case title"""
        party_set = set()
        
        if title and " v. " in title:
            parts = title.split(" v. ")
            if len(parts) >= 2:
                # Clean and add party names
                for part in parts[:2]:  # Usually plaintiff v. defendant
                    cleaned = re.sub(r'\([^)]*\)', '', part).strip()
                    cleaned = re.sub(r'\s+', ' ', cleaned)
                    if cleaned:
                        party_set.add(cleaned)
        
        # Add explicit parties
        if parties:
            party_set.update(parties)
        
        return party_set
    
    def _sample_content(self, content: str, max_length: int = 5000) -> str:
        """Sample content to avoid performance issues with very long texts"""
        if len(content) <= max_length:
            return content
        
        # Take beginning and end of content
        half_length = max_length // 2
        return content[:half_length] + " ... " + content[-half_length:]
    
    def _calculate_legal_term_similarity(self, terms1: List[str], terms2: List[str]) -> float:
        """Calculate similarity based on legal terminology"""
        # Count legal terms in each document
        legal_terms1 = defaultdict(int)
        legal_terms2 = defaultdict(int)
        
        for term in terms1:
            for category, legal_words in self.legal_term_categories.items():
                if term.lower() in legal_words:
                    legal_terms1[category] += 1
        
        for term in terms2:
            for category, legal_words in self.legal_term_categories.items():
                if term.lower() in legal_words:
                    legal_terms2[category] += 1
        
        if not legal_terms1 or not legal_terms2:
            return 0.0
        
        # Calculate cosine similarity of legal term vectors
        categories = set(legal_terms1.keys()) | set(legal_terms2.keys())
        
        dot_product = sum(
            legal_terms1[cat] * legal_terms2[cat]
            for cat in categories
        )
        
        norm1 = math.sqrt(sum(count ** 2 for count in legal_terms1.values()))
        norm2 = math.sqrt(sum(count ** 2 for count in legal_terms2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _select_best_document(self, documents: List[UnifiedDocument]) -> UnifiedDocument:
        """Select the best representative document from a cluster"""
        if len(documents) == 1:
            return documents[0]
        
        best_doc = documents[0]
        best_score = -1.0
        
        for doc in documents:
            # Score based on multiple factors
            score = 0.0
            
            # Authority score
            score += doc.authority_score * 0.3
            
            # Relevance score
            score += doc.relevance_score * 0.2
            
            # Completeness (full text availability)
            if doc.full_text_available:
                score += 0.2
            
            # Citation availability
            if doc.citation:
                score += 0.1
            
            # Free access preference
            if doc.is_free_access:
                score += 0.1
            
            # Content richness
            content_length = len(doc.full_text) if doc.full_text else 0
            if content_length > 1000:
                score += 0.1
            
            if score > best_score:
                best_score = score
                best_doc = doc
        
        return best_doc
    
    def _calculate_confidence(
        self,
        individual_scores: List[SimilarityScore],
        overall_score: float
    ) -> float:
        """Calculate confidence in similarity assessment"""
        if not individual_scores:
            return 0.0
        
        # Base confidence on score consistency and completeness
        score_values = [score.score for score in individual_scores]
        
        # Calculate score variance
        mean_score = sum(score_values) / len(score_values)
        variance = sum((score - mean_score) ** 2 for score in score_values) / len(score_values)
        consistency = 1.0 - min(variance, 1.0)
        
        # Factor in how many types of similarity we could assess
        completeness = len(individual_scores) / len(SimilarityType)
        
        # Factor in individual confidences
        avg_individual_confidence = sum(score.confidence for score in individual_scores) / len(individual_scores)
        
        # Combined confidence
        confidence = (consistency * 0.4 + completeness * 0.3 + avg_individual_confidence * 0.3)
        
        return min(confidence, 1.0)
    
    def _calculate_cluster_quality(self, similarities: List[DocumentSimilarity]) -> float:
        """Calculate quality of a similarity cluster"""
        if not similarities:
            return 1.0
        
        # Average similarity score in cluster
        avg_similarity = sum(sim.overall_score for sim in similarities) / len(similarities)
        
        # Average confidence
        avg_confidence = sum(sim.confidence for sim in similarities) / len(similarities)
        
        # Quality is combination of similarity and confidence
        return (avg_similarity * 0.7 + avg_confidence * 0.3)