"""
Advanced duplicate detection system for legal documents.
Provides fuzzy matching, content similarity, and intelligent deduplication.
"""

import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime
import json

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher
import jellyfish
from transformers import AutoTokenizer, AutoModel
import torch
import cv2
from PIL import Image
import imagehash

logger = logging.getLogger(__name__)


class DuplicateType(Enum):
    """Types of duplicates detected."""
    EXACT = "exact"                    # Identical content
    NEAR_EXACT = "near_exact"         # Minor formatting differences
    VERSION = "version"                # Different versions of same document
    TEMPLATE = "template"              # Same template, different content
    SIMILAR = "similar"                # Similar content/structure
    PARTIAL = "partial"                # Partial overlap
    NOT_DUPLICATE = "not_duplicate"    # No significant similarity


class SimilarityMethod(Enum):
    """Methods used for similarity detection."""
    HASH = "hash"                      # Content hashing
    FUZZY = "fuzzy"                    # Fuzzy string matching
    TFIDF = "tfidf"                    # TF-IDF cosine similarity
    SEMANTIC = "semantic"              # Semantic embeddings
    STRUCTURAL = "structural"          # Document structure
    VISUAL = "visual"                  # Visual/layout similarity
    METADATA = "metadata"              # Metadata comparison


@dataclass
class DuplicateMatch:
    """Represents a duplicate document match."""
    document_id_1: str
    document_id_2: str
    duplicate_type: DuplicateType
    similarity_score: float
    confidence: float
    method_used: SimilarityMethod
    details: Dict[str, Any]
    detection_timestamp: datetime


@dataclass
class DocumentFingerprint:
    """Document fingerprint for efficient comparison."""
    document_id: str
    content_hash: str
    fuzzy_hash: str
    metadata_hash: str
    structural_features: Dict[str, Any]
    tfidf_features: Optional[np.ndarray]
    semantic_embedding: Optional[np.ndarray]
    visual_hash: Optional[str]
    word_count: int
    char_count: int
    page_count: int
    creation_time: datetime


class DuplicateDetector:
    """Advanced duplicate detection system for legal documents."""
    
    def __init__(self, 
                 similarity_threshold: float = 0.8,
                 semantic_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize duplicate detector.
        
        Args:
            similarity_threshold: Minimum similarity score for duplicate detection
            semantic_model: Model for semantic similarity comparison
        """
        self.similarity_threshold = similarity_threshold
        self.semantic_model = semantic_model
        
        # Initialize components
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),
            stop_words='english'
        )
        
        self.tokenizer = None
        self.model = None
        self.document_fingerprints: Dict[str, DocumentFingerprint] = {}
        self.similarity_cache: Dict[str, float] = {}
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize semantic similarity models."""
        try:
            from sentence_transformers import SentenceTransformer
            self.semantic_model_instance = SentenceTransformer(self.semantic_model)
            logger.info(f"Loaded semantic model: {self.semantic_model}")
        except ImportError:
            logger.warning("sentence-transformers not available, using basic similarity")
            self.semantic_model_instance = None
    
    def create_fingerprint(self, document_id: str, content: str, 
                          metadata: Dict[str, Any] = None,
                          image_path: str = None) -> DocumentFingerprint:
        """Create a comprehensive fingerprint for a document.
        
        Args:
            document_id: Unique document identifier
            content: Document text content
            metadata: Document metadata
            image_path: Path to document image (for visual similarity)
            
        Returns:
            Document fingerprint for comparison
        """
        logger.info(f"Creating fingerprint for document: {document_id}")
        
        metadata = metadata or {}
        
        # Content hashing
        content_hash = self._create_content_hash(content)
        fuzzy_hash = self._create_fuzzy_hash(content)
        metadata_hash = self._create_metadata_hash(metadata)
        
        # Structural features
        structural_features = self._extract_structural_features(content)
        
        # TF-IDF features
        tfidf_features = self._extract_tfidf_features(content)
        
        # Semantic embedding
        semantic_embedding = self._extract_semantic_embedding(content)
        
        # Visual hash (if image available)
        visual_hash = None
        if image_path:
            visual_hash = self._create_visual_hash(image_path)
        
        # Basic statistics
        word_count = len(content.split())
        char_count = len(content)
        page_count = max(1, word_count // 250)  # Estimate
        
        fingerprint = DocumentFingerprint(
            document_id=document_id,
            content_hash=content_hash,
            fuzzy_hash=fuzzy_hash,
            metadata_hash=metadata_hash,
            structural_features=structural_features,
            tfidf_features=tfidf_features,
            semantic_embedding=semantic_embedding,
            visual_hash=visual_hash,
            word_count=word_count,
            char_count=char_count,
            page_count=page_count,
            creation_time=datetime.utcnow()
        )
        
        # Store fingerprint
        self.document_fingerprints[document_id] = fingerprint
        
        return fingerprint
    
    def find_duplicates(self, document_id: str, 
                       target_ids: List[str] = None) -> List[DuplicateMatch]:
        """Find duplicate documents for a given document.
        
        Args:
            document_id: Source document ID
            target_ids: Optional list of target document IDs to compare against
            
        Returns:
            List of duplicate matches found
        """
        if document_id not in self.document_fingerprints:
            logger.error(f"Document fingerprint not found: {document_id}")
            return []
        
        source_fp = self.document_fingerprints[document_id]
        
        # Determine comparison targets
        if target_ids:
            targets = {tid: self.document_fingerprints[tid] 
                      for tid in target_ids if tid in self.document_fingerprints}
        else:
            targets = {tid: fp for tid, fp in self.document_fingerprints.items() 
                      if tid != document_id}
        
        duplicates = []
        
        for target_id, target_fp in targets.items():
            # Check cache first
            cache_key = f"{min(document_id, target_id)}_{max(document_id, target_id)}"
            
            if cache_key in self.similarity_cache:
                similarity = self.similarity_cache[cache_key]
                if similarity >= self.similarity_threshold:
                    duplicates.append(DuplicateMatch(
                        document_id_1=document_id,
                        document_id_2=target_id,
                        duplicate_type=DuplicateType.SIMILAR,
                        similarity_score=similarity,
                        confidence=0.8,
                        method_used=SimilarityMethod.TFIDF,
                        details={"cached": True},
                        detection_timestamp=datetime.utcnow()
                    ))
                continue
            
            # Perform comprehensive comparison
            match = self._compare_documents(source_fp, target_fp)
            
            if match and match.similarity_score >= self.similarity_threshold:
                duplicates.append(match)
                self.similarity_cache[cache_key] = match.similarity_score
        
        # Sort by similarity score (highest first)
        duplicates.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return duplicates
    
    def batch_detect_duplicates(self, document_ids: List[str] = None) -> List[DuplicateMatch]:
        """Detect duplicates across multiple documents in batch.
        
        Args:
            document_ids: Optional list of document IDs to analyze
            
        Returns:
            List of all duplicate matches found
        """
        if document_ids:
            fingerprints = {did: self.document_fingerprints[did] 
                          for did in document_ids if did in self.document_fingerprints}
        else:
            fingerprints = self.document_fingerprints
        
        all_duplicates = []
        processed_pairs = set()
        
        for doc_id_1, fp_1 in fingerprints.items():
            for doc_id_2, fp_2 in fingerprints.items():
                if doc_id_1 >= doc_id_2:  # Avoid duplicate comparisons
                    continue
                
                pair_key = f"{doc_id_1}_{doc_id_2}"
                if pair_key in processed_pairs:
                    continue
                
                processed_pairs.add(pair_key)
                
                match = self._compare_documents(fp_1, fp_2)
                if match and match.similarity_score >= self.similarity_threshold:
                    all_duplicates.append(match)
        
        return sorted(all_duplicates, key=lambda x: x.similarity_score, reverse=True)
    
    def _compare_documents(self, fp1: DocumentFingerprint, 
                          fp2: DocumentFingerprint) -> Optional[DuplicateMatch]:
        """Compare two document fingerprints comprehensively.
        
        Args:
            fp1: First document fingerprint
            fp2: Second document fingerprint
            
        Returns:
            Duplicate match if similarity found, None otherwise
        """
        # Quick hash comparison first
        if fp1.content_hash == fp2.content_hash:
            return DuplicateMatch(
                document_id_1=fp1.document_id,
                document_id_2=fp2.document_id,
                duplicate_type=DuplicateType.EXACT,
                similarity_score=1.0,
                confidence=1.0,
                method_used=SimilarityMethod.HASH,
                details={"hash_match": True},
                detection_timestamp=datetime.utcnow()
            )
        
        # Fuzzy hash comparison
        fuzzy_similarity = self._compare_fuzzy_hashes(fp1.fuzzy_hash, fp2.fuzzy_hash)
        
        # TF-IDF similarity
        tfidf_similarity = 0.0
        if fp1.tfidf_features is not None and fp2.tfidf_features is not None:
            tfidf_similarity = self._calculate_tfidf_similarity(
                fp1.tfidf_features, fp2.tfidf_features
            )
        
        # Semantic similarity
        semantic_similarity = 0.0
        if fp1.semantic_embedding is not None and fp2.semantic_embedding is not None:
            semantic_similarity = self._calculate_semantic_similarity(
                fp1.semantic_embedding, fp2.semantic_embedding
            )
        
        # Structural similarity
        structural_similarity = self._compare_structural_features(
            fp1.structural_features, fp2.structural_features
        )
        
        # Visual similarity
        visual_similarity = 0.0
        if fp1.visual_hash and fp2.visual_hash:
            visual_similarity = self._compare_visual_hashes(
                fp1.visual_hash, fp2.visual_hash
            )
        
        # Metadata similarity
        metadata_similarity = 1.0 if fp1.metadata_hash == fp2.metadata_hash else 0.0
        
        # Combine similarities with weights
        weights = {
            'fuzzy': 0.2,
            'tfidf': 0.3,
            'semantic': 0.25,
            'structural': 0.15,
            'visual': 0.05,
            'metadata': 0.05
        }
        
        combined_similarity = (
            weights['fuzzy'] * fuzzy_similarity +
            weights['tfidf'] * tfidf_similarity +
            weights['semantic'] * semantic_similarity +
            weights['structural'] * structural_similarity +
            weights['visual'] * visual_similarity +
            weights['metadata'] * metadata_similarity
        )
        
        # Determine duplicate type
        duplicate_type = self._determine_duplicate_type(
            combined_similarity, fuzzy_similarity, tfidf_similarity, 
            semantic_similarity, structural_similarity
        )
        
        # Determine primary method used
        method_scores = {
            SimilarityMethod.FUZZY: fuzzy_similarity,
            SimilarityMethod.TFIDF: tfidf_similarity,
            SimilarityMethod.SEMANTIC: semantic_similarity,
            SimilarityMethod.STRUCTURAL: structural_similarity,
        }
        primary_method = max(method_scores.items(), key=lambda x: x[1])[0]
        
        # Calculate confidence based on agreement between methods
        confidence = self._calculate_confidence(
            fuzzy_similarity, tfidf_similarity, semantic_similarity, structural_similarity
        )
        
        if combined_similarity < 0.3:  # Below minimum threshold
            return None
        
        return DuplicateMatch(
            document_id_1=fp1.document_id,
            document_id_2=fp2.document_id,
            duplicate_type=duplicate_type,
            similarity_score=combined_similarity,
            confidence=confidence,
            method_used=primary_method,
            details={
                'fuzzy_similarity': fuzzy_similarity,
                'tfidf_similarity': tfidf_similarity,
                'semantic_similarity': semantic_similarity,
                'structural_similarity': structural_similarity,
                'visual_similarity': visual_similarity,
                'metadata_similarity': metadata_similarity,
                'word_count_diff': abs(fp1.word_count - fp2.word_count),
                'page_count_diff': abs(fp1.page_count - fp2.page_count)
            },
            detection_timestamp=datetime.utcnow()
        )
    
    def _create_content_hash(self, content: str) -> str:
        """Create MD5 hash of normalized content."""
        normalized = re.sub(r'\s+', ' ', content.strip().lower())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _create_fuzzy_hash(self, content: str) -> str:
        """Create fuzzy hash for approximate matching."""
        # Simplified fuzzy hash - remove minor variations
        normalized = re.sub(r'[^\w\s]', '', content.lower())
        normalized = re.sub(r'\s+', ' ', normalized.strip())
        
        # Create hash of key content words
        words = normalized.split()
        key_words = [w for w in words if len(w) > 3]  # Keep meaningful words
        key_content = ' '.join(sorted(key_words))
        
        return hashlib.sha256(key_content.encode()).hexdigest()
    
    def _create_metadata_hash(self, metadata: Dict[str, Any]) -> str:
        """Create hash of document metadata."""
        # Sort metadata for consistent hashing
        sorted_metadata = json.dumps(metadata, sort_keys=True, default=str)
        return hashlib.md5(sorted_metadata.encode()).hexdigest()
    
    def _create_visual_hash(self, image_path: str) -> str:
        """Create perceptual hash of document image."""
        try:
            image = Image.open(image_path)
            # Create perceptual hash
            phash = imagehash.phash(image)
            return str(phash)
        except Exception as e:
            logger.warning(f"Visual hash creation failed: {e}")
            return ""
    
    def _extract_structural_features(self, content: str) -> Dict[str, Any]:
        """Extract structural features from document content."""
        features = {}
        
        # Basic structure
        features['line_count'] = len(content.split('\n'))
        features['paragraph_count'] = len(re.split(r'\n\s*\n', content))
        features['sentence_count'] = len(re.split(r'[.!?]+', content))
        
        # Legal document structure
        features['has_signature_block'] = bool(re.search(r'signature|signed|executed', content, re.IGNORECASE))
        features['has_date_line'] = bool(re.search(r'dated|date:', content, re.IGNORECASE))
        features['has_parties'] = bool(re.search(r'plaintiff|defendant|party|parties', content, re.IGNORECASE))
        features['has_whereas_clauses'] = len(re.findall(r'\bwhereas\b', content, re.IGNORECASE))
        features['has_numbered_sections'] = len(re.findall(r'^\s*\d+\.', content, re.MULTILINE))
        
        # Content patterns
        features['capitalized_words'] = len(re.findall(r'\b[A-Z]{2,}\b', content))
        features['quoted_text'] = len(re.findall(r'"[^"]*"', content))
        features['parenthetical_text'] = len(re.findall(r'\([^)]*\)', content))
        
        # Legal citations
        features['citation_count'] = len(re.findall(r'\d+\s+[A-Z][a-z\.]+\s+\d+', content))
        
        return features
    
    def _extract_tfidf_features(self, content: str) -> Optional[np.ndarray]:
        """Extract TF-IDF feature vector from content."""
        try:
            # Fit vectorizer if not already fitted
            if not hasattr(self.tfidf_vectorizer, 'vocabulary_'):
                # Use the content to fit (in practice, fit on corpus)
                self.tfidf_vectorizer.fit([content])
            
            features = self.tfidf_vectorizer.transform([content])
            return features.toarray()[0]
        except Exception as e:
            logger.warning(f"TF-IDF extraction failed: {e}")
            return None
    
    def _extract_semantic_embedding(self, content: str) -> Optional[np.ndarray]:
        """Extract semantic embedding from content."""
        if not self.semantic_model_instance:
            return None
        
        try:
            # Truncate content for model limits
            truncated_content = content[:512]
            embedding = self.semantic_model_instance.encode([truncated_content])
            return embedding[0]
        except Exception as e:
            logger.warning(f"Semantic embedding extraction failed: {e}")
            return None
    
    def _compare_fuzzy_hashes(self, hash1: str, hash2: str) -> float:
        """Compare two fuzzy hashes for similarity."""
        if not hash1 or not hash2:
            return 0.0
        
        # Calculate Hamming distance between hashes
        if len(hash1) != len(hash2):
            return 0.0
        
        differences = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        similarity = 1.0 - (differences / len(hash1))
        
        return similarity
    
    def _calculate_tfidf_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """Calculate cosine similarity between TF-IDF features."""
        try:
            similarity = cosine_similarity([features1], [features2])[0][0]
            return max(0.0, similarity)
        except Exception as e:
            logger.warning(f"TF-IDF similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_semantic_similarity(self, embed1: np.ndarray, embed2: np.ndarray) -> float:
        """Calculate cosine similarity between semantic embeddings."""
        try:
            # Normalize embeddings
            embed1_norm = embed1 / np.linalg.norm(embed1)
            embed2_norm = embed2 / np.linalg.norm(embed2)
            
            similarity = np.dot(embed1_norm, embed2_norm)
            return max(0.0, similarity)
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def _compare_structural_features(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """Compare structural features between documents."""
        if not features1 or not features2:
            return 0.0
        
        total_score = 0.0
        feature_count = 0
        
        for key in set(features1.keys()) | set(features2.keys()):
            val1 = features1.get(key, 0)
            val2 = features2.get(key, 0)
            
            if isinstance(val1, bool) and isinstance(val2, bool):
                # Boolean features
                score = 1.0 if val1 == val2 else 0.0
            elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Numeric features - calculate relative similarity
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
    
    def _compare_visual_hashes(self, hash1: str, hash2: str) -> float:
        """Compare visual hashes for similarity."""
        if not hash1 or not hash2:
            return 0.0
        
        try:
            # Convert to imagehash objects and calculate similarity
            import imagehash
            phash1 = imagehash.hex_to_hash(hash1)
            phash2 = imagehash.hex_to_hash(hash2)
            
            # Calculate Hamming distance
            distance = phash1 - phash2
            max_distance = len(hash1) * 4  # 4 bits per hex character
            
            similarity = 1.0 - (distance / max_distance)
            return max(0.0, similarity)
        except Exception as e:
            logger.warning(f"Visual hash comparison failed: {e}")
            return 0.0
    
    def _determine_duplicate_type(self, combined_similarity: float, 
                                 fuzzy_similarity: float, tfidf_similarity: float,
                                 semantic_similarity: float, structural_similarity: float) -> DuplicateType:
        """Determine the type of duplicate based on similarity scores."""
        if combined_similarity >= 0.95:
            return DuplicateType.EXACT
        elif combined_similarity >= 0.85:
            return DuplicateType.NEAR_EXACT
        elif structural_similarity >= 0.8 and tfidf_similarity >= 0.6:
            return DuplicateType.VERSION
        elif structural_similarity >= 0.9 and tfidf_similarity < 0.4:
            return DuplicateType.TEMPLATE
        elif combined_similarity >= 0.7:
            return DuplicateType.SIMILAR
        elif combined_similarity >= 0.4:
            return DuplicateType.PARTIAL
        else:
            return DuplicateType.NOT_DUPLICATE
    
    def _calculate_confidence(self, fuzzy_sim: float, tfidf_sim: float, 
                            semantic_sim: float, structural_sim: float) -> float:
        """Calculate confidence based on agreement between similarity methods."""
        similarities = [fuzzy_sim, tfidf_sim, semantic_sim, structural_sim]
        similarities = [s for s in similarities if s > 0]  # Remove zero similarities
        
        if len(similarities) < 2:
            return 0.5  # Low confidence with insufficient methods
        
        # Calculate standard deviation - lower deviation = higher confidence
        mean_sim = np.mean(similarities)
        std_sim = np.std(similarities)
        
        # Convert to confidence score (higher std = lower confidence)
        confidence = max(0.1, 1.0 - (std_sim * 2))  # Scale std to confidence
        
        # Boost confidence if mean similarity is high
        if mean_sim >= 0.8:
            confidence = min(1.0, confidence + 0.2)
        
        return confidence
    
    def get_duplicate_clusters(self, document_ids: List[str] = None) -> List[List[str]]:
        """Group documents into duplicate clusters.
        
        Args:
            document_ids: Optional list of document IDs to cluster
            
        Returns:
            List of clusters, each containing duplicate document IDs
        """
        duplicates = self.batch_detect_duplicates(document_ids)
        
        # Build graph of duplicates
        duplicate_graph = {}
        all_docs = set()
        
        for match in duplicates:
            if match.duplicate_type in [DuplicateType.EXACT, DuplicateType.NEAR_EXACT, 
                                      DuplicateType.VERSION, DuplicateType.SIMILAR]:
                doc1, doc2 = match.document_id_1, match.document_id_2
                all_docs.add(doc1)
                all_docs.add(doc2)
                
                if doc1 not in duplicate_graph:
                    duplicate_graph[doc1] = set()
                if doc2 not in duplicate_graph:
                    duplicate_graph[doc2] = set()
                
                duplicate_graph[doc1].add(doc2)
                duplicate_graph[doc2].add(doc1)
        
        # Find connected components (clusters)
        visited = set()
        clusters = []
        
        for doc_id in all_docs:
            if doc_id not in visited:
                cluster = []
                stack = [doc_id]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        cluster.append(current)
                        
                        # Add neighbors
                        neighbors = duplicate_graph.get(current, set())
                        for neighbor in neighbors:
                            if neighbor not in visited:
                                stack.append(neighbor)
                
                if len(cluster) > 1:  # Only return actual clusters
                    clusters.append(sorted(cluster))
        
        return sorted(clusters, key=len, reverse=True)
    
    def remove_duplicates(self, document_ids: List[str], 
                         keep_strategy: str = "newest") -> List[str]:
        """Remove duplicates and return list of documents to keep.
        
        Args:
            document_ids: List of document IDs to deduplicate
            keep_strategy: Strategy for choosing which duplicate to keep
                         ("newest", "oldest", "longest", "shortest")
            
        Returns:
            List of document IDs to keep after deduplication
        """
        clusters = self.get_duplicate_clusters(document_ids)
        keep_docs = set(document_ids)
        
        for cluster in clusters:
            # Determine which document to keep
            cluster_fps = [self.document_fingerprints[doc_id] for doc_id in cluster]
            
            if keep_strategy == "newest":
                keeper = max(cluster_fps, key=lambda fp: fp.creation_time)
            elif keep_strategy == "oldest":
                keeper = min(cluster_fps, key=lambda fp: fp.creation_time)
            elif keep_strategy == "longest":
                keeper = max(cluster_fps, key=lambda fp: fp.word_count)
            elif keep_strategy == "shortest":
                keeper = min(cluster_fps, key=lambda fp: fp.word_count)
            else:
                keeper = cluster_fps[0]  # Default to first
            
            # Remove all others from keep list
            for doc_id in cluster:
                if doc_id != keeper.document_id:
                    keep_docs.discard(doc_id)
        
        return sorted(list(keep_docs))
    
    def clear_cache(self):
        """Clear similarity calculation cache."""
        self.similarity_cache.clear()
        logger.info("Similarity cache cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get duplicate detection statistics."""
        total_docs = len(self.document_fingerprints)
        cache_size = len(self.similarity_cache)
        
        return {
            "total_documents": total_docs,
            "cached_comparisons": cache_size,
            "similarity_threshold": self.similarity_threshold,
            "fingerprint_creation_times": [
                fp.creation_time.isoformat() 
                for fp in self.document_fingerprints.values()
            ]
        }