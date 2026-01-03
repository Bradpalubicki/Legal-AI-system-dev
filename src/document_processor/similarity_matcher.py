"""
Advanced document similarity matching system.
Provides semantic search, content-based recommendations, and related document discovery.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
import numpy as np
from datetime import datetime
import json
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
import faiss

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of document matches."""
    SEMANTIC = "semantic"          # Similar meaning/content
    TOPICAL = "topical"           # Similar topics/themes
    STRUCTURAL = "structural"      # Similar document structure
    LEGAL_CONCEPT = "legal_concept"  # Similar legal concepts
    CITATION = "citation"          # Shared legal citations
    ENTITY = "entity"              # Shared entities (parties, courts)
    TEMPORAL = "temporal"          # Similar time periods
    PROCEDURAL = "procedural"      # Similar procedural context


class SearchMode(Enum):
    """Document search modes."""
    EXACT = "exact"                # Exact phrase matching
    FUZZY = "fuzzy"               # Fuzzy text matching
    SEMANTIC = "semantic"          # Semantic similarity search
    HYBRID = "hybrid"             # Combined approach
    CONCEPTUAL = "conceptual"     # Legal concept matching


@dataclass
class SimilarityMatch:
    """Represents a document similarity match."""
    source_document_id: str
    matched_document_id: str
    match_type: MatchType
    similarity_score: float
    confidence: float
    matched_features: List[str]
    explanation: str
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class SearchResult:
    """Search result with relevance scoring."""
    document_id: str
    relevance_score: float
    match_highlights: List[str]
    match_type: MatchType
    snippet: str
    metadata: Dict[str, Any]


@dataclass
class DocumentIndex:
    """Document index for efficient similarity search."""
    document_id: str
    content_vector: np.ndarray
    topic_distribution: np.ndarray
    legal_concepts: Set[str]
    entities: Set[str]
    citations: Set[str]
    structural_features: Dict[str, Any]
    creation_time: datetime
    last_updated: datetime


class SimilarityMatcher:
    """Advanced document similarity matching and search system."""
    
    def __init__(self, 
                 vector_dimension: int = 384,
                 n_topics: int = 50,
                 similarity_threshold: float = 0.7):
        """Initialize similarity matcher.
        
        Args:
            vector_dimension: Dimension for document vectors
            n_topics: Number of topics for topic modeling
            similarity_threshold: Minimum similarity score for matches
        """
        self.vector_dimension = vector_dimension
        self.n_topics = n_topics
        self.similarity_threshold = similarity_threshold
        
        # Initialize vectorizers and models
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),
            stop_words='english',
            lowercase=True
        )
        
        self.lda_model = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=100
        )
        
        # FAISS index for fast similarity search
        self.faiss_index = None
        self.document_indices: Dict[str, DocumentIndex] = {}
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}
        
        # Legal concept patterns
        self.legal_concepts = {
            'contract_law': [
                'breach of contract', 'consideration', 'offer and acceptance',
                'contract formation', 'contract interpretation', 'damages'
            ],
            'tort_law': [
                'negligence', 'duty of care', 'causation', 'damages',
                'strict liability', 'intentional tort'
            ],
            'constitutional_law': [
                'due process', 'equal protection', 'first amendment',
                'fourth amendment', 'constitutional rights'
            ],
            'corporate_law': [
                'fiduciary duty', 'business judgment rule', 'shareholders',
                'board of directors', 'merger', 'acquisition'
            ],
            'litigation': [
                'summary judgment', 'discovery', 'motion to dismiss',
                'class action', 'settlement', 'trial'
            ],
            'intellectual_property': [
                'patent infringement', 'trademark', 'copyright',
                'trade secret', 'fair use'
            ]
        }
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models and indices."""
        try:
            # Initialize FAISS index for fast similarity search
            self.faiss_index = faiss.IndexFlatIP(self.vector_dimension)
            logger.info("Initialized FAISS index for similarity search")
            
            # Try to load sentence transformer model
            try:
                from sentence_transformers import SentenceTransformer
                self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence transformer model")
            except ImportError:
                logger.warning("sentence-transformers not available")
                self.sentence_transformer = None
                
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
    
    def index_document(self, document_id: str, content: str, 
                      metadata: Dict[str, Any] = None) -> DocumentIndex:
        """Index a document for similarity matching.
        
        Args:
            document_id: Unique document identifier
            content: Document text content
            metadata: Additional document metadata
            
        Returns:
            Document index object
        """
        logger.info(f"Indexing document: {document_id}")
        
        metadata = metadata or {}
        
        # Extract features
        content_vector = self._create_content_vector(content)
        topic_distribution = self._extract_topic_distribution(content)
        legal_concepts = self._extract_legal_concepts(content)
        entities = self._extract_entities(content)
        citations = self._extract_citations(content)
        structural_features = self._extract_structural_features(content)
        
        # Create document index
        doc_index = DocumentIndex(
            document_id=document_id,
            content_vector=content_vector,
            topic_distribution=topic_distribution,
            legal_concepts=legal_concepts,
            entities=entities,
            citations=citations,
            structural_features=structural_features,
            creation_time=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        # Store in indices
        self.document_indices[document_id] = doc_index
        
        # Add to FAISS index
        if self.faiss_index is not None and content_vector is not None:
            # Normalize vector for cosine similarity
            normalized_vector = content_vector / np.linalg.norm(content_vector)
            normalized_vector = normalized_vector.astype('float32').reshape(1, -1)
            
            index_position = self.faiss_index.ntotal
            self.id_to_index[document_id] = index_position
            self.index_to_id[index_position] = document_id
            
            self.faiss_index.add(normalized_vector)
        
        return doc_index
    
    def find_similar_documents(self, document_id: str, 
                              top_k: int = 10,
                              match_types: List[MatchType] = None) -> List[SimilarityMatch]:
        """Find documents similar to the given document.
        
        Args:
            document_id: Source document ID
            top_k: Number of similar documents to return
            match_types: Types of matches to consider
            
        Returns:
            List of similarity matches
        """
        if document_id not in self.document_indices:
            logger.error(f"Document not found in index: {document_id}")
            return []
        
        source_doc = self.document_indices[document_id]
        match_types = match_types or list(MatchType)
        
        all_matches = []
        
        # Semantic similarity search
        if MatchType.SEMANTIC in match_types:
            semantic_matches = self._find_semantic_matches(source_doc, top_k)
            all_matches.extend(semantic_matches)
        
        # Topical similarity
        if MatchType.TOPICAL in match_types:
            topical_matches = self._find_topical_matches(source_doc, top_k)
            all_matches.extend(topical_matches)
        
        # Legal concept similarity
        if MatchType.LEGAL_CONCEPT in match_types:
            concept_matches = self._find_concept_matches(source_doc, top_k)
            all_matches.extend(concept_matches)
        
        # Citation-based matches
        if MatchType.CITATION in match_types:
            citation_matches = self._find_citation_matches(source_doc, top_k)
            all_matches.extend(citation_matches)
        
        # Entity-based matches
        if MatchType.ENTITY in match_types:
            entity_matches = self._find_entity_matches(source_doc, top_k)
            all_matches.extend(entity_matches)
        
        # Structural similarity
        if MatchType.STRUCTURAL in match_types:
            structural_matches = self._find_structural_matches(source_doc, top_k)
            all_matches.extend(structural_matches)
        
        # Deduplicate and rank matches
        unique_matches = self._deduplicate_matches(all_matches)
        ranked_matches = sorted(unique_matches, key=lambda x: x.similarity_score, reverse=True)
        
        return ranked_matches[:top_k]
    
    def search_documents(self, query: str, 
                        top_k: int = 10,
                        search_mode: SearchMode = SearchMode.HYBRID,
                        filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Search for documents matching a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            search_mode: Search mode to use
            filters: Additional filters to apply
            
        Returns:
            List of search results
        """
        logger.info(f"Searching documents with query: {query[:100]}...")
        
        filters = filters or {}
        results = []
        
        if search_mode == SearchMode.SEMANTIC or search_mode == SearchMode.HYBRID:
            semantic_results = self._semantic_search(query, top_k)
            results.extend(semantic_results)
        
        if search_mode == SearchMode.EXACT or search_mode == SearchMode.HYBRID:
            exact_results = self._exact_search(query, top_k)
            results.extend(exact_results)
        
        if search_mode == SearchMode.FUZZY or search_mode == SearchMode.HYBRID:
            fuzzy_results = self._fuzzy_search(query, top_k)
            results.extend(fuzzy_results)
        
        if search_mode == SearchMode.CONCEPTUAL or search_mode == SearchMode.HYBRID:
            concept_results = self._conceptual_search(query, top_k)
            results.extend(concept_results)
        
        # Apply filters
        if filters:
            results = self._apply_filters(results, filters)
        
        # Deduplicate and rank
        unique_results = self._deduplicate_search_results(results)
        ranked_results = sorted(unique_results, key=lambda x: x.relevance_score, reverse=True)
        
        return ranked_results[:top_k]
    
    def get_document_clusters(self, n_clusters: int = 10) -> Dict[int, List[str]]:
        """Cluster documents by similarity.
        
        Args:
            n_clusters: Number of clusters to create
            
        Returns:
            Dictionary mapping cluster IDs to document IDs
        """
        if len(self.document_indices) < n_clusters:
            logger.warning("Not enough documents for clustering")
            return {}
        
        # Gather all content vectors
        doc_ids = []
        vectors = []
        
        for doc_id, doc_index in self.document_indices.items():
            if doc_index.content_vector is not None:
                doc_ids.append(doc_id)
                vectors.append(doc_index.content_vector)
        
        if not vectors:
            return {}
        
        # Perform K-means clustering
        vectors_array = np.vstack(vectors)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(vectors_array)
        
        # Group documents by cluster
        clusters = {}
        for doc_id, cluster_id in zip(doc_ids, cluster_labels):
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(doc_id)
        
        return clusters
    
    def _create_content_vector(self, content: str) -> Optional[np.ndarray]:
        """Create content vector using sentence transformer or TF-IDF."""
        try:
            if self.sentence_transformer:
                # Use sentence transformer for semantic vectors
                vector = self.sentence_transformer.encode([content])[0]
                return vector.astype('float32')
            else:
                # Fallback to TF-IDF
                if not hasattr(self.tfidf_vectorizer, 'vocabulary_'):
                    self.tfidf_vectorizer.fit([content])
                
                tfidf_vector = self.tfidf_vectorizer.transform([content])
                return tfidf_vector.toarray()[0].astype('float32')
        except Exception as e:
            logger.warning(f"Content vector creation failed: {e}")
            return None
    
    def _extract_topic_distribution(self, content: str) -> Optional[np.ndarray]:
        """Extract topic distribution using LDA."""
        try:
            # Fit TF-IDF vectorizer if needed
            if not hasattr(self.tfidf_vectorizer, 'vocabulary_'):
                self.tfidf_vectorizer.fit([content])
            
            tfidf_vector = self.tfidf_vectorizer.transform([content])
            
            # Fit LDA if needed
            if not hasattr(self.lda_model, 'components_'):
                self.lda_model.fit(tfidf_vector)
            
            topic_dist = self.lda_model.transform(tfidf_vector)[0]
            return topic_dist
        except Exception as e:
            logger.warning(f"Topic extraction failed: {e}")
            return None
    
    def _extract_legal_concepts(self, content: str) -> Set[str]:
        """Extract legal concepts from content."""
        content_lower = content.lower()
        concepts = set()
        
        for category, concept_list in self.legal_concepts.items():
            for concept in concept_list:
                if concept in content_lower:
                    concepts.add(concept)
        
        return concepts
    
    def _extract_entities(self, content: str) -> Set[str]:
        """Extract entities from content."""
        entities = set()
        
        # Extract party names
        party_patterns = [
            r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',  # Person names
            r'\b([A-Z][A-Za-z\s]+(?:Corp|Inc|LLC|Ltd|Co)\.?)\b'  # Company names
        ]
        
        for pattern in party_patterns:
            matches = re.findall(pattern, content)
            entities.update(matches)
        
        return entities
    
    def _extract_citations(self, content: str) -> Set[str]:
        """Extract legal citations from content."""
        citations = set()
        
        # Basic citation patterns
        citation_patterns = [
            r'\b\d+\s+[A-Z][a-z\.]+\s+\d+\b',  # Case citations
            r'\b\d+\s+U\.S\.C\.\s+§\s*\d+\b',  # USC citations
            r'\b\d+\s+F\.\d+\s+\d+\b'          # Federal reporter citations
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, content)
            citations.update(matches)
        
        return citations
    
    def _extract_structural_features(self, content: str) -> Dict[str, Any]:
        """Extract structural features from content."""
        features = {}
        
        features['word_count'] = len(content.split())
        features['sentence_count'] = len(re.split(r'[.!?]+', content))
        features['paragraph_count'] = len(re.split(r'\n\s*\n', content))
        features['has_numbered_sections'] = bool(re.search(r'^\s*\d+\.', content, re.MULTILINE))
        features['has_signature_block'] = bool(re.search(r'signature|signed', content, re.IGNORECASE))
        features['capitalized_ratio'] = len(re.findall(r'\b[A-Z]+\b', content)) / max(1, len(content.split()))
        
        return features
    
    def _find_semantic_matches(self, source_doc: DocumentIndex, top_k: int) -> List[SimilarityMatch]:
        """Find semantically similar documents."""
        matches = []
        
        if source_doc.content_vector is None or self.faiss_index is None:
            return matches
        
        # Search using FAISS index
        query_vector = source_doc.content_vector / np.linalg.norm(source_doc.content_vector)
        query_vector = query_vector.astype('float32').reshape(1, -1)
        
        scores, indices = self.faiss_index.search(query_vector, top_k + 1)  # +1 to exclude self
        
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # Invalid index
                continue
                
            matched_doc_id = self.index_to_id.get(idx)
            if not matched_doc_id or matched_doc_id == source_doc.document_id:
                continue
            
            if score >= self.similarity_threshold:
                matches.append(SimilarityMatch(
                    source_document_id=source_doc.document_id,
                    matched_document_id=matched_doc_id,
                    match_type=MatchType.SEMANTIC,
                    similarity_score=float(score),
                    confidence=0.8,
                    matched_features=['content_similarity'],
                    explanation=f"Semantic similarity score: {score:.3f}",
                    metadata={'faiss_score': float(score)},
                    timestamp=datetime.utcnow()
                ))
        
        return matches
    
    def _find_topical_matches(self, source_doc: DocumentIndex, top_k: int) -> List[SimilarityMatch]:
        """Find topically similar documents."""
        matches = []
        
        if source_doc.topic_distribution is None:
            return matches
        
        for doc_id, doc_index in self.document_indices.items():
            if doc_id == source_doc.document_id or doc_index.topic_distribution is None:
                continue
            
            # Calculate topic similarity using cosine similarity
            similarity = cosine_similarity([source_doc.topic_distribution], 
                                         [doc_index.topic_distribution])[0][0]
            
            if similarity >= self.similarity_threshold:
                matches.append(SimilarityMatch(
                    source_document_id=source_doc.document_id,
                    matched_document_id=doc_id,
                    match_type=MatchType.TOPICAL,
                    similarity_score=similarity,
                    confidence=0.7,
                    matched_features=['topic_distribution'],
                    explanation=f"Topic similarity score: {similarity:.3f}",
                    metadata={'topic_similarity': similarity},
                    timestamp=datetime.utcnow()
                ))
        
        return sorted(matches, key=lambda x: x.similarity_score, reverse=True)[:top_k]
    
    def _find_concept_matches(self, source_doc: DocumentIndex, top_k: int) -> List[SimilarityMatch]:
        """Find documents with similar legal concepts."""
        matches = []
        
        if not source_doc.legal_concepts:
            return matches
        
        for doc_id, doc_index in self.document_indices.items():
            if doc_id == source_doc.document_id or not doc_index.legal_concepts:
                continue
            
            # Calculate Jaccard similarity for concepts
            intersection = source_doc.legal_concepts & doc_index.legal_concepts
            union = source_doc.legal_concepts | doc_index.legal_concepts
            
            if union:
                similarity = len(intersection) / len(union)
                
                if similarity >= 0.3:  # Lower threshold for concept matching
                    matches.append(SimilarityMatch(
                        source_document_id=source_doc.document_id,
                        matched_document_id=doc_id,
                        match_type=MatchType.LEGAL_CONCEPT,
                        similarity_score=similarity,
                        confidence=0.9,
                        matched_features=list(intersection),
                        explanation=f"Shared legal concepts: {', '.join(list(intersection)[:3])}",
                        metadata={'shared_concepts': list(intersection)},
                        timestamp=datetime.utcnow()
                    ))
        
        return sorted(matches, key=lambda x: x.similarity_score, reverse=True)[:top_k]
    
    def _find_citation_matches(self, source_doc: DocumentIndex, top_k: int) -> List[SimilarityMatch]:
        """Find documents with shared citations."""
        matches = []
        
        if not source_doc.citations:
            return matches
        
        for doc_id, doc_index in self.document_indices.items():
            if doc_id == source_doc.document_id or not doc_index.citations:
                continue
            
            # Calculate citation overlap
            intersection = source_doc.citations & doc_index.citations
            union = source_doc.citations | doc_index.citations
            
            if intersection and union:
                similarity = len(intersection) / len(union)
                
                matches.append(SimilarityMatch(
                    source_document_id=source_doc.document_id,
                    matched_document_id=doc_id,
                    match_type=MatchType.CITATION,
                    similarity_score=similarity,
                    confidence=0.95,
                    matched_features=list(intersection),
                    explanation=f"Shared citations: {len(intersection)} common",
                    metadata={'shared_citations': list(intersection)},
                    timestamp=datetime.utcnow()
                ))
        
        return sorted(matches, key=lambda x: x.similarity_score, reverse=True)[:top_k]
    
    def _find_entity_matches(self, source_doc: DocumentIndex, top_k: int) -> List[SimilarityMatch]:
        """Find documents with shared entities."""
        matches = []
        
        if not source_doc.entities:
            return matches
        
        for doc_id, doc_index in self.document_indices.items():
            if doc_id == source_doc.document_id or not doc_index.entities:
                continue
            
            # Calculate entity overlap
            intersection = source_doc.entities & doc_index.entities
            union = source_doc.entities | doc_index.entities
            
            if intersection and union:
                similarity = len(intersection) / len(union)
                
                if similarity >= 0.2:  # Lower threshold for entity matching
                    matches.append(SimilarityMatch(
                        source_document_id=source_doc.document_id,
                        matched_document_id=doc_id,
                        match_type=MatchType.ENTITY,
                        similarity_score=similarity,
                        confidence=0.8,
                        matched_features=list(intersection),
                        explanation=f"Shared entities: {', '.join(list(intersection)[:3])}",
                        metadata={'shared_entities': list(intersection)},
                        timestamp=datetime.utcnow()
                    ))
        
        return sorted(matches, key=lambda x: x.similarity_score, reverse=True)[:top_k]
    
    def _find_structural_matches(self, source_doc: DocumentIndex, top_k: int) -> List[SimilarityMatch]:
        """Find structurally similar documents."""
        matches = []
        
        for doc_id, doc_index in self.document_indices.items():
            if doc_id == source_doc.document_id:
                continue
            
            # Compare structural features
            similarity = self._calculate_structural_similarity(
                source_doc.structural_features, doc_index.structural_features
            )
            
            if similarity >= 0.6:  # Threshold for structural similarity
                matches.append(SimilarityMatch(
                    source_document_id=source_doc.document_id,
                    matched_document_id=doc_id,
                    match_type=MatchType.STRUCTURAL,
                    similarity_score=similarity,
                    confidence=0.6,
                    matched_features=['document_structure'],
                    explanation=f"Structural similarity score: {similarity:.3f}",
                    metadata={'structural_similarity': similarity},
                    timestamp=datetime.utcnow()
                ))
        
        return sorted(matches, key=lambda x: x.similarity_score, reverse=True)[:top_k]
    
    def _calculate_structural_similarity(self, features1: Dict[str, Any], 
                                       features2: Dict[str, Any]) -> float:
        """Calculate structural similarity between two documents."""
        if not features1 or not features2:
            return 0.0
        
        total_score = 0.0
        feature_count = 0
        
        for key in set(features1.keys()) | set(features2.keys()):
            val1 = features1.get(key, 0)
            val2 = features2.get(key, 0)
            
            if isinstance(val1, bool) and isinstance(val2, bool):
                score = 1.0 if val1 == val2 else 0.0
            elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                if val1 == 0 and val2 == 0:
                    score = 1.0
                elif val1 == 0 or val2 == 0:
                    score = 0.0
                else:
                    ratio = min(val1, val2) / max(val1, val2)
                    score = ratio
            else:
                continue
            
            total_score += score
            feature_count += 1
        
        return total_score / feature_count if feature_count > 0 else 0.0
    
    def _semantic_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Perform semantic search using embeddings."""
        results = []
        
        if not self.sentence_transformer or not self.faiss_index:
            return results
        
        try:
            # Create query vector
            query_vector = self.sentence_transformer.encode([query])[0]
            query_vector = query_vector / np.linalg.norm(query_vector)
            query_vector = query_vector.astype('float32').reshape(1, -1)
            
            # Search
            scores, indices = self.faiss_index.search(query_vector, top_k)
            
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:
                    continue
                    
                doc_id = self.index_to_id.get(idx)
                if doc_id:
                    results.append(SearchResult(
                        document_id=doc_id,
                        relevance_score=float(score),
                        match_highlights=[query],
                        match_type=MatchType.SEMANTIC,
                        snippet=f"Semantic match with score: {score:.3f}",
                        metadata={'search_type': 'semantic', 'query': query}
                    ))
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")
        
        return results
    
    def _exact_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Perform exact text search."""
        # Placeholder for exact search implementation
        return []
    
    def _fuzzy_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Perform fuzzy text search."""
        # Placeholder for fuzzy search implementation
        return []
    
    def _conceptual_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Perform legal concept-based search."""
        results = []
        
        query_lower = query.lower()
        query_concepts = set()
        
        # Extract concepts from query
        for category, concept_list in self.legal_concepts.items():
            for concept in concept_list:
                if concept in query_lower:
                    query_concepts.add(concept)
        
        if not query_concepts:
            return results
        
        # Find documents with matching concepts
        for doc_id, doc_index in self.document_indices.items():
            intersection = query_concepts & doc_index.legal_concepts
            if intersection:
                relevance = len(intersection) / len(query_concepts)
                results.append(SearchResult(
                    document_id=doc_id,
                    relevance_score=relevance,
                    match_highlights=list(intersection),
                    match_type=MatchType.LEGAL_CONCEPT,
                    snippet=f"Matching concepts: {', '.join(list(intersection)[:3])}",
                    metadata={'search_type': 'conceptual', 'matched_concepts': list(intersection)}
                ))
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)[:top_k]
    
    def _apply_filters(self, results: List[SearchResult], 
                      filters: Dict[str, Any]) -> List[SearchResult]:
        """Apply filters to search results."""
        # Placeholder for filter implementation
        return results
    
    def _deduplicate_matches(self, matches: List[SimilarityMatch]) -> List[SimilarityMatch]:
        """Remove duplicate matches."""
        seen = set()
        unique_matches = []
        
        for match in matches:
            key = (match.source_document_id, match.matched_document_id, match.match_type)
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        return unique_matches
    
    def _deduplicate_search_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate search results."""
        seen = set()
        unique_results = []
        
        for result in results:
            if result.document_id not in seen:
                seen.add(result.document_id)
                unique_results.append(result)
            else:
                # Update existing result if this one has higher relevance
                for i, existing in enumerate(unique_results):
                    if (existing.document_id == result.document_id and 
                        result.relevance_score > existing.relevance_score):
                        unique_results[i] = result
                        break
        
        return unique_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get similarity matcher statistics."""
        return {
            "total_indexed_documents": len(self.document_indices),
            "faiss_index_size": self.faiss_index.ntotal if self.faiss_index else 0,
            "similarity_threshold": self.similarity_threshold,
            "vector_dimension": self.vector_dimension,
            "n_topics": self.n_topics
        }