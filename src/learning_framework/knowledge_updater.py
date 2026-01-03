"""
Knowledge Updater Module

Advanced knowledge base management system for maintaining and evolving
legal knowledge, case law, and domain expertise through continuous learning.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import logging
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
import asyncio
import json
import hashlib
import re
from textblob import TextBlob
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import networkx as nx

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    CASE_LAW = "case_law"
    STATUTE = "statute"
    REGULATION = "regulation"
    PRECEDENT = "precedent"
    LEGAL_CONCEPT = "legal_concept"
    PROCEDURE = "procedure"
    FORM_TEMPLATE = "form_template"
    BEST_PRACTICE = "best_practice"
    DOMAIN_EXPERTISE = "domain_expertise"
    FACT_PATTERN = "fact_pattern"
    LEGAL_STANDARD = "legal_standard"
    COURT_RULE = "court_rule"
    CITATION = "citation"
    DEFINITION = "definition"
    JURISDICTION_SPECIFIC = "jurisdiction_specific"

class UpdateStrategy(Enum):
    APPEND_NEW = "append_new"
    MERGE_CONTENT = "merge_content"
    REPLACE_OUTDATED = "replace_outdated"
    VERSION_CONTROL = "version_control"
    PRIORITY_UPDATE = "priority_update"
    GRADUAL_INTEGRATION = "gradual_integration"
    EXPERT_REVIEW = "expert_review"
    AUTOMATED_VALIDATION = "automated_validation"

class KnowledgeSource(Enum):
    COURT_DECISION = "court_decision"
    LEGISLATIVE_UPDATE = "legislative_update"
    CASE_OUTCOME = "case_outcome"
    EXPERT_INPUT = "expert_input"
    USER_CONTRIBUTION = "user_contribution"
    AUTOMATED_EXTRACTION = "automated_extraction"
    THIRD_PARTY_FEED = "third_party_feed"
    INTERNAL_RESEARCH = "internal_research"
    PEER_REVIEW = "peer_review"

@dataclass
class KnowledgeEntry:
    id: Optional[int] = None
    knowledge_type: KnowledgeType = KnowledgeType.LEGAL_CONCEPT
    title: str = ""
    content: str = ""
    summary: str = ""
    key_concepts: List[str] = field(default_factory=list)
    related_cases: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    jurisdiction: Optional[str] = None
    practice_area: Optional[str] = None
    confidence_score: float = 0.0
    authority_level: int = 1  # 1-5 scale (5 = Supreme Court level)
    relevance_score: float = 0.0
    accuracy_validated: bool = False
    source: KnowledgeSource = KnowledgeSource.AUTOMATED_EXTRACTION
    source_url: Optional[str] = None
    source_document: Optional[str] = None
    created_by: Optional[str] = None
    validated_by: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    parent_entry_id: Optional[int] = None
    superseded_by: Optional[int] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    access_count: int = 0

class KnowledgeUpdater:
    def __init__(self):
        self.knowledge_base: Dict[int, KnowledgeEntry] = {}
        self.knowledge_graph: nx.Graph = nx.Graph()
        self.update_queue: asyncio.Queue = asyncio.Queue()
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.knowledge_vectors: Optional[np.ndarray] = None
        self.update_history: List[Dict[str, Any]] = []
        
        # Configuration
        self.config = {
            'similarity_threshold': 0.8,  # For detecting duplicates
            'confidence_threshold': 0.7,  # Minimum confidence for auto-updates
            'authority_weight': 0.3,  # Weight for authority in ranking
            'recency_weight': 0.2,  # Weight for recency in ranking
            'max_related_entries': 10,  # Maximum related entries to maintain
            'auto_validation_enabled': True,
            'expert_review_threshold': 0.9,  # High-impact changes need expert review
            'batch_processing_size': 100
        }
        
        # Legal domain knowledge
        self.legal_stopwords = set([
            'court', 'case', 'defendant', 'plaintiff', 'judge', 'jury', 'trial',
            'law', 'legal', 'statute', 'rule', 'order', 'motion', 'brief',
            'appeal', 'judgment', 'verdict', 'evidence', 'testimony', 'witness'
        ]).union(set(stopwords.words('english')))

    async def add_knowledge(
        self,
        knowledge_type: KnowledgeType,
        title: str,
        content: str,
        source: KnowledgeSource = KnowledgeSource.AUTOMATED_EXTRACTION,
        metadata: Optional[Dict[str, Any]] = None,
        auto_process: bool = True,
        db: Optional[AsyncSession] = None
    ) -> Optional[KnowledgeEntry]:
        """Add new knowledge to the knowledge base."""
        try:
            # Create knowledge entry
            entry = KnowledgeEntry(
                id=len(self.knowledge_base) + 1,
                knowledge_type=knowledge_type,
                title=title,
                content=content,
                source=source,
                metadata=metadata or {}
            )
            
            if auto_process:
                # Process the knowledge entry
                await self._process_knowledge_entry(entry)
            
            # Check for duplicates and conflicts
            duplicate_check = await self._check_for_duplicates(entry)
            if duplicate_check['is_duplicate']:
                logger.info(f"Duplicate knowledge detected: {duplicate_check['similar_entries']}")
                return await self._handle_duplicate(entry, duplicate_check['similar_entries'])
            
            # Add to knowledge base
            self.knowledge_base[entry.id] = entry
            
            # Update knowledge graph
            await self._update_knowledge_graph(entry)
            
            # Update vectors for similarity search
            await self._update_knowledge_vectors()
            
            # Persist to database
            if db:
                await self._persist_knowledge_entry(entry, db)
            
            # Log the addition
            self.update_history.append({
                'action': 'add',
                'entry_id': entry.id,
                'timestamp': datetime.utcnow(),
                'source': source.value
            })
            
            logger.info(f"Added knowledge entry: {entry.id} - {title[:50]}...")
            return entry
            
        except Exception as e:
            logger.error(f"Error adding knowledge: {e}")
            return None

    async def update_knowledge(
        self,
        entry_id: int,
        updates: Dict[str, Any],
        strategy: UpdateStrategy = UpdateStrategy.MERGE_CONTENT,
        validate_update: bool = True,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """Update existing knowledge entry."""
        try:
            if entry_id not in self.knowledge_base:
                logger.warning(f"Knowledge entry {entry_id} not found")
                return False
            
            entry = self.knowledge_base[entry_id]
            original_entry = KnowledgeEntry(**entry.__dict__)
            
            # Apply update strategy
            if strategy == UpdateStrategy.APPEND_NEW:
                await self._append_to_entry(entry, updates)
            elif strategy == UpdateStrategy.MERGE_CONTENT:
                await self._merge_entry_content(entry, updates)
            elif strategy == UpdateStrategy.REPLACE_OUTDATED:
                await self._replace_entry_content(entry, updates)
            elif strategy == UpdateStrategy.VERSION_CONTROL:
                await self._create_entry_version(entry, updates)
            else:
                # Default update
                for key, value in updates.items():
                    if hasattr(entry, key):
                        setattr(entry, key, value)
            
            # Validate update if requested
            if validate_update:
                validation_result = await self._validate_knowledge_update(original_entry, entry)
                if not validation_result['valid']:
                    logger.warning(f"Knowledge update failed validation: {validation_result['reason']}")
                    return False
            
            # Update metadata
            entry.updated_at = datetime.utcnow()
            entry.version += 1
            
            # Reprocess if content changed significantly
            if 'content' in updates or 'title' in updates:
                await self._process_knowledge_entry(entry)
                await self._update_knowledge_graph(entry)
                await self._update_knowledge_vectors()
            
            # Persist changes
            if db:
                await self._persist_knowledge_entry(entry, db)
            
            # Log the update
            self.update_history.append({
                'action': 'update',
                'entry_id': entry_id,
                'strategy': strategy.value,
                'timestamp': datetime.utcnow(),
                'changes': list(updates.keys())
            })
            
            logger.info(f"Updated knowledge entry: {entry_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating knowledge {entry_id}: {e}")
            return False

    async def search_knowledge(
        self,
        query: str,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        jurisdiction: Optional[str] = None,
        practice_area: Optional[str] = None,
        min_confidence: float = 0.0,
        max_results: int = 10,
        similarity_threshold: float = 0.1
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """Search knowledge base using semantic similarity."""
        try:
            if not self.knowledge_base:
                return []
            
            # Filter entries by criteria
            candidate_entries = []
            for entry in self.knowledge_base.values():
                # Type filter
                if knowledge_types and entry.knowledge_type not in knowledge_types:
                    continue
                
                # Jurisdiction filter
                if jurisdiction and entry.jurisdiction and entry.jurisdiction != jurisdiction:
                    continue
                
                # Practice area filter
                if practice_area and entry.practice_area and entry.practice_area != practice_area:
                    continue
                
                # Confidence filter
                if entry.confidence_score < min_confidence:
                    continue
                
                candidate_entries.append(entry)
            
            if not candidate_entries:
                return []
            
            # Vectorize query and entries
            all_texts = [query] + [f"{entry.title} {entry.content}" for entry in candidate_entries]
            
            try:
                tfidf_matrix = self.vectorizer.fit_transform(all_texts)
                query_vector = tfidf_matrix[0]
                entry_vectors = tfidf_matrix[1:]
                
                # Calculate similarities
                similarities = cosine_similarity(query_vector, entry_vectors).flatten()
                
            except Exception as e:
                logger.warning(f"TF-IDF vectorization failed, using fallback: {e}")
                # Fallback to simple text matching
                similarities = []
                query_words = set(query.lower().split())
                for entry in candidate_entries:
                    entry_words = set(f"{entry.title} {entry.content}".lower().split())
                    similarity = len(query_words.intersection(entry_words)) / len(query_words.union(entry_words))
                    similarities.append(similarity)
                similarities = np.array(similarities)
            
            # Filter by similarity threshold
            valid_indices = np.where(similarities >= similarity_threshold)[0]
            
            if len(valid_indices) == 0:
                return []
            
            # Create results with scores
            results = []
            for idx in valid_indices:
                entry = candidate_entries[idx]
                similarity_score = similarities[idx]
                
                # Calculate composite score (similarity + authority + recency)
                authority_score = entry.authority_level / 5.0
                days_old = (datetime.utcnow() - entry.updated_at).days
                recency_score = max(0, 1 - days_old / 365.0)  # Decay over 1 year
                
                composite_score = (
                    similarity_score * 0.5 +
                    authority_score * self.config['authority_weight'] +
                    recency_score * self.config['recency_weight']
                )
                
                results.append((entry, composite_score))
                
                # Update access statistics
                entry.last_accessed = datetime.utcnow()
                entry.access_count += 1
            
            # Sort by composite score and limit results
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return []

    async def get_related_knowledge(
        self,
        entry_id: int,
        relation_types: Optional[List[str]] = None,
        max_results: int = 5
    ) -> List[Tuple[KnowledgeEntry, str, float]]:
        """Get knowledge entries related to a specific entry."""
        try:
            if entry_id not in self.knowledge_base:
                return []
            
            entry = self.knowledge_base[entry_id]
            related_entries = []
            
            # Use knowledge graph if available
            if self.knowledge_graph.has_node(entry_id):
                neighbors = list(self.knowledge_graph.neighbors(entry_id))
                for neighbor_id in neighbors:
                    if neighbor_id in self.knowledge_base:
                        neighbor_entry = self.knowledge_base[neighbor_id]
                        edge_data = self.knowledge_graph[entry_id][neighbor_id]
                        relation_type = edge_data.get('relation_type', 'related')
                        weight = edge_data.get('weight', 0.5)
                        
                        if not relation_types or relation_type in relation_types:
                            related_entries.append((neighbor_entry, relation_type, weight))
            
            # Fallback to content similarity
            if len(related_entries) < max_results:
                content_based = await self._find_similar_by_content(entry, max_results - len(related_entries))
                for similar_entry, similarity in content_based:
                    if similar_entry.id != entry_id:
                        related_entries.append((similar_entry, 'content_similar', similarity))
            
            # Sort by relevance score
            related_entries.sort(key=lambda x: x[2], reverse=True)
            return related_entries[:max_results]
            
        except Exception as e:
            logger.error(f"Error getting related knowledge: {e}")
            return []

    async def validate_knowledge_consistency(
        self,
        check_all: bool = False,
        entry_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Validate consistency across knowledge base."""
        try:
            validation_results = {
                'total_entries_checked': 0,
                'conflicts_found': [],
                'outdated_entries': [],
                'low_confidence_entries': [],
                'missing_citations': [],
                'inconsistencies': [],
                'suggestions': []
            }
            
            entries_to_check = []
            if check_all:
                entries_to_check = list(self.knowledge_base.values())
            elif entry_ids:
                entries_to_check = [self.knowledge_base[eid] for eid in entry_ids if eid in self.knowledge_base]
            
            validation_results['total_entries_checked'] = len(entries_to_check)
            
            for entry in entries_to_check:
                # Check for outdated content
                if entry.effective_date and entry.effective_date < datetime.utcnow() - timedelta(days=1095):  # 3 years
                    validation_results['outdated_entries'].append({
                        'id': entry.id,
                        'title': entry.title,
                        'age_days': (datetime.utcnow() - entry.effective_date).days
                    })
                
                # Check confidence levels
                if entry.confidence_score < self.config['confidence_threshold']:
                    validation_results['low_confidence_entries'].append({
                        'id': entry.id,
                        'title': entry.title,
                        'confidence': entry.confidence_score
                    })
                
                # Check for missing citations in legal content
                if entry.knowledge_type in [KnowledgeType.CASE_LAW, KnowledgeType.STATUTE] and not entry.citations:
                    validation_results['missing_citations'].append({
                        'id': entry.id,
                        'title': entry.title,
                        'type': entry.knowledge_type.value
                    })
                
                # Check for conflicts with other entries
                conflicts = await self._detect_conflicts(entry)
                validation_results['conflicts_found'].extend(conflicts)
            
            # Generate improvement suggestions
            validation_results['suggestions'] = await self._generate_consistency_suggestions(validation_results)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating knowledge consistency: {e}")
            return {'error': str(e)}

    async def update_from_case_outcome(
        self,
        case_id: int,
        outcome: Dict[str, Any],
        extract_knowledge: bool = True,
        db: Optional[AsyncSession] = None
    ) -> List[KnowledgeEntry]:
        """Update knowledge base based on case outcome."""
        try:
            new_entries = []
            
            if not extract_knowledge:
                return new_entries
            
            # Extract knowledge from case outcome
            extracted_knowledge = await self._extract_knowledge_from_outcome(case_id, outcome)
            
            for knowledge_data in extracted_knowledge:
                # Create knowledge entry
                entry = await self.add_knowledge(
                    knowledge_type=knowledge_data['type'],
                    title=knowledge_data['title'],
                    content=knowledge_data['content'],
                    source=KnowledgeSource.CASE_OUTCOME,
                    metadata={
                        'case_id': case_id,
                        'outcome_date': datetime.utcnow().isoformat(),
                        'extraction_method': 'automated',
                        **knowledge_data.get('metadata', {})
                    },
                    db=db
                )
                
                if entry:
                    new_entries.append(entry)
            
            logger.info(f"Updated knowledge base with {len(new_entries)} entries from case {case_id}")
            return new_entries
            
        except Exception as e:
            logger.error(f"Error updating knowledge from case outcome: {e}")
            return []

    async def get_knowledge_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the knowledge base."""
        try:
            total_entries = len(self.knowledge_base)
            
            if total_entries == 0:
                return {'message': 'Knowledge base is empty'}
            
            # Distribution by type
            type_distribution = Counter([entry.knowledge_type.value for entry in self.knowledge_base.values()])
            
            # Distribution by source
            source_distribution = Counter([entry.source.value for entry in self.knowledge_base.values()])
            
            # Authority levels
            authority_distribution = Counter([entry.authority_level for entry in self.knowledge_base.values()])
            
            # Confidence scores
            confidence_scores = [entry.confidence_score for entry in self.knowledge_base.values()]
            avg_confidence = np.mean(confidence_scores)
            
            # Age analysis
            ages_days = [(datetime.utcnow() - entry.created_at).days for entry in self.knowledge_base.values()]
            avg_age_days = np.mean(ages_days)
            
            # Access patterns
            access_counts = [entry.access_count for entry in self.knowledge_base.values()]
            total_accesses = sum(access_counts)
            
            # Content analysis
            content_lengths = [len(entry.content) for entry in self.knowledge_base.values()]
            avg_content_length = np.mean(content_lengths)
            
            # Validation status
            validated_entries = sum(1 for entry in self.knowledge_base.values() if entry.accuracy_validated)
            validation_rate = validated_entries / total_entries
            
            # Jurisdiction distribution
            jurisdictions = [entry.jurisdiction for entry in self.knowledge_base.values() if entry.jurisdiction]
            jurisdiction_distribution = Counter(jurisdictions)
            
            # Practice area distribution
            practice_areas = [entry.practice_area for entry in self.knowledge_base.values() if entry.practice_area]
            practice_area_distribution = Counter(practice_areas)
            
            statistics = {
                'overview': {
                    'total_entries': total_entries,
                    'validated_entries': validated_entries,
                    'validation_rate': validation_rate,
                    'total_accesses': total_accesses,
                    'avg_confidence_score': avg_confidence,
                    'avg_age_days': avg_age_days,
                    'avg_content_length': avg_content_length
                },
                'distributions': {
                    'by_type': dict(type_distribution),
                    'by_source': dict(source_distribution),
                    'by_authority_level': dict(authority_distribution),
                    'by_jurisdiction': dict(jurisdiction_distribution),
                    'by_practice_area': dict(practice_area_distribution)
                },
                'quality_metrics': {
                    'confidence_distribution': {
                        'mean': avg_confidence,
                        'std': np.std(confidence_scores),
                        'min': np.min(confidence_scores),
                        'max': np.max(confidence_scores),
                        'high_confidence_count': sum(1 for score in confidence_scores if score > 0.8)
                    },
                    'content_quality': {
                        'avg_length': avg_content_length,
                        'entries_with_citations': sum(1 for entry in self.knowledge_base.values() if entry.citations),
                        'entries_with_related': sum(1 for entry in self.knowledge_base.values() if entry.related_cases)
                    }
                },
                'update_activity': {
                    'recent_additions': len([h for h in self.update_history if 
                                           h['action'] == 'add' and 
                                           datetime.fromisoformat(h['timestamp'].replace('Z', '+00:00')) > datetime.utcnow() - timedelta(days=30)]),
                    'recent_updates': len([h for h in self.update_history if 
                                         h['action'] == 'update' and 
                                         datetime.fromisoformat(h['timestamp'].replace('Z', '+00:00')) > datetime.utcnow() - timedelta(days=30)]),
                    'total_updates': len(self.update_history)
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error generating knowledge statistics: {e}")
            return {'error': str(e)}

    # Private helper methods
    
    async def _process_knowledge_entry(self, entry: KnowledgeEntry) -> None:
        """Process and enhance knowledge entry."""
        try:
            # Generate summary if not provided
            if not entry.summary and entry.content:
                entry.summary = await self._generate_summary(entry.content)
            
            # Extract key concepts
            entry.key_concepts = await self._extract_key_concepts(entry.title + " " + entry.content)
            
            # Extract citations
            if entry.knowledge_type in [KnowledgeType.CASE_LAW, KnowledgeType.STATUTE]:
                entry.citations = await self._extract_citations(entry.content)
            
            # Determine jurisdiction and practice area if not set
            if not entry.jurisdiction:
                entry.jurisdiction = await self._infer_jurisdiction(entry.content)
            
            if not entry.practice_area:
                entry.practice_area = await self._infer_practice_area(entry.content)
            
            # Calculate confidence score
            entry.confidence_score = await self._calculate_confidence_score(entry)
            
            # Set authority level based on source and type
            entry.authority_level = await self._determine_authority_level(entry)
            
        except Exception as e:
            logger.error(f"Error processing knowledge entry: {e}")

    async def _check_for_duplicates(self, entry: KnowledgeEntry) -> Dict[str, Any]:
        """Check for duplicate or very similar entries."""
        try:
            if not self.knowledge_base:
                return {'is_duplicate': False, 'similar_entries': []}
            
            # Create comparison text
            entry_text = f"{entry.title} {entry.content}"
            similar_entries = []
            
            # Compare with existing entries
            for existing_entry in self.knowledge_base.values():
                existing_text = f"{existing_entry.title} {existing_entry.content}"
                
                # Simple similarity check
                similarity = await self._calculate_text_similarity(entry_text, existing_text)
                
                if similarity > self.config['similarity_threshold']:
                    similar_entries.append({
                        'entry_id': existing_entry.id,
                        'similarity': similarity,
                        'title': existing_entry.title
                    })
            
            is_duplicate = len(similar_entries) > 0
            return {'is_duplicate': is_duplicate, 'similar_entries': similar_entries}
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return {'is_duplicate': False, 'similar_entries': []}

    async def _handle_duplicate(
        self, 
        new_entry: KnowledgeEntry, 
        similar_entries: List[Dict[str, Any]]
    ) -> KnowledgeEntry:
        """Handle duplicate knowledge entries."""
        try:
            # Find the most similar existing entry
            most_similar = max(similar_entries, key=lambda x: x['similarity'])
            existing_entry = self.knowledge_base[most_similar['entry_id']]
            
            # Merge the entries
            merged_entry = await self._merge_knowledge_entries(existing_entry, new_entry)
            
            # Update the existing entry
            self.knowledge_base[existing_entry.id] = merged_entry
            
            logger.info(f"Merged duplicate entry with existing entry {existing_entry.id}")
            return merged_entry
            
        except Exception as e:
            logger.error(f"Error handling duplicate: {e}")
            return new_entry

    async def _merge_knowledge_entries(
        self, 
        existing: KnowledgeEntry, 
        new: KnowledgeEntry
    ) -> KnowledgeEntry:
        """Merge two knowledge entries."""
        try:
            merged = KnowledgeEntry(**existing.__dict__)
            
            # Merge content intelligently
            if new.content and new.content not in existing.content:
                merged.content += f"\n\n[Updated Content]\n{new.content}"
            
            # Merge citations
            merged.citations = list(set(existing.citations + new.citations))
            
            # Merge key concepts
            merged.key_concepts = list(set(existing.key_concepts + new.key_concepts))
            
            # Update confidence if new entry has higher confidence
            if new.confidence_score > existing.confidence_score:
                merged.confidence_score = new.confidence_score
            
            # Update authority if new entry has higher authority
            if new.authority_level > existing.authority_level:
                merged.authority_level = new.authority_level
            
            # Update timestamps
            merged.updated_at = datetime.utcnow()
            merged.version += 1
            
            return merged
            
        except Exception as e:
            logger.error(f"Error merging knowledge entries: {e}")
            return existing

    async def _update_knowledge_graph(self, entry: KnowledgeEntry) -> None:
        """Update the knowledge graph with relationships."""
        try:
            # Add node
            self.knowledge_graph.add_node(entry.id, title=entry.title, type=entry.knowledge_type.value)
            
            # Add edges based on related cases
            for related_case in entry.related_cases:
                # Find entries with matching cases
                for other_entry in self.knowledge_base.values():
                    if (other_entry.id != entry.id and 
                        related_case in other_entry.related_cases):
                        self.knowledge_graph.add_edge(entry.id, other_entry.id, 
                                                    relation_type='related_case', 
                                                    weight=0.8)
            
            # Add edges based on citations
            for citation in entry.citations:
                for other_entry in self.knowledge_base.values():
                    if (other_entry.id != entry.id and 
                        citation in other_entry.citations):
                        self.knowledge_graph.add_edge(entry.id, other_entry.id, 
                                                    relation_type='citation', 
                                                    weight=0.7)
            
            # Add edges based on key concepts
            common_concepts_threshold = 3
            for other_entry in self.knowledge_base.values():
                if other_entry.id != entry.id:
                    common_concepts = set(entry.key_concepts).intersection(set(other_entry.key_concepts))
                    if len(common_concepts) >= common_concepts_threshold:
                        weight = len(common_concepts) / max(len(entry.key_concepts), len(other_entry.key_concepts))
                        self.knowledge_graph.add_edge(entry.id, other_entry.id, 
                                                    relation_type='concept_overlap', 
                                                    weight=weight)
            
        except Exception as e:
            logger.error(f"Error updating knowledge graph: {e}")

    async def _update_knowledge_vectors(self) -> None:
        """Update TF-IDF vectors for similarity search."""
        try:
            if not self.knowledge_base:
                return
            
            texts = [f"{entry.title} {entry.content}" for entry in self.knowledge_base.values()]
            self.knowledge_vectors = self.vectorizer.fit_transform(texts)
            
        except Exception as e:
            logger.error(f"Error updating knowledge vectors: {e}")

    async def _generate_summary(self, content: str, max_sentences: int = 3) -> str:
        """Generate a summary of knowledge content."""
        try:
            if len(content) < 200:
                return content[:150] + "..." if len(content) > 150 else content
            
            # Simple extractive summarization
            sentences = sent_tokenize(content)
            if len(sentences) <= max_sentences:
                return content
            
            # Score sentences based on word frequency
            words = word_tokenize(content.lower())
            word_freq = Counter([word for word in words if word not in self.legal_stopwords])
            
            sentence_scores = {}
            for sentence in sentences:
                sentence_words = word_tokenize(sentence.lower())
                score = sum(word_freq[word] for word in sentence_words if word in word_freq)
                sentence_scores[sentence] = score
            
            # Get top sentences
            top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
            
            # Maintain original order
            summary_sentences = []
            for sentence in sentences:
                if any(sentence == s[0] for s in top_sentences):
                    summary_sentences.append(sentence)
                if len(summary_sentences) >= max_sentences:
                    break
            
            return " ".join(summary_sentences)
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return content[:200] + "..." if len(content) > 200 else content

    async def _extract_key_concepts(self, text: str, max_concepts: int = 10) -> List[str]:
        """Extract key concepts from text."""
        try:
            # Simple keyword extraction based on frequency
            words = word_tokenize(text.lower())
            
            # Filter meaningful words
            meaningful_words = [
                word for word in words 
                if (len(word) > 3 and 
                    word.isalpha() and 
                    word not in self.legal_stopwords)
            ]
            
            # Get most frequent words
            word_freq = Counter(meaningful_words)
            top_words = [word for word, freq in word_freq.most_common(max_concepts)]
            
            return top_words
            
        except Exception as e:
            logger.error(f"Error extracting key concepts: {e}")
            return []

    async def _extract_citations(self, content: str) -> List[str]:
        """Extract legal citations from content."""
        try:
            citations = []
            
            # Common citation patterns
            patterns = [
                r'\d+\s+[A-Z][a-z.]*\s+\d+',  # Volume Reporter Page
                r'\d+\s+U\.S\.\s+\d+',  # US Reports
                r'\d+\s+S\.Ct\.\s+\d+',  # Supreme Court Reporter
                r'\d+\s+F\.3d\s+\d+',  # Federal Reporter 3d
                r'\d+\s+F\.Supp\.\s+\d+',  # Federal Supplement
                r'\d+\s+USC\s+§\s*\d+',  # US Code
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                citations.extend(matches)
            
            return list(set(citations))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting citations: {e}")
            return []

    async def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        try:
            # Simple word overlap similarity
            words1 = set(word_tokenize(text1.lower()))
            words2 = set(word_tokenize(text2.lower()))
            
            # Remove stop words
            words1 = words1 - self.legal_stopwords
            words2 = words2 - self.legal_stopwords
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return 0.0

    # Additional helper methods would be implemented here for:
    # - _infer_jurisdiction
    # - _infer_practice_area  
    # - _calculate_confidence_score
    # - _determine_authority_level
    # - _find_similar_by_content
    # - _detect_conflicts
    # - _generate_consistency_suggestions
    # - _extract_knowledge_from_outcome
    # - _validate_knowledge_update
    # - _persist_knowledge_entry
    # - etc.

    async def _infer_jurisdiction(self, content: str) -> Optional[str]:
        """Infer jurisdiction from content."""
        try:
            # Simple keyword-based jurisdiction detection
            jurisdiction_keywords = {
                'federal': ['federal', 'supreme court', 'circuit court', 'district court', 'us code'],
                'california': ['california', 'ca supreme', 'cal.', 'california code'],
                'new_york': ['new york', 'ny supreme', 'n.y.', 'new york law'],
                'texas': ['texas', 'tx supreme', 'tex.', 'texas code']
            }
            
            content_lower = content.lower()
            for jurisdiction, keywords in jurisdiction_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    return jurisdiction
            
            return None
        except Exception as e:
            logger.error(f"Error inferring jurisdiction: {e}")
            return None

    async def _calculate_confidence_score(self, entry: KnowledgeEntry) -> float:
        """Calculate confidence score for knowledge entry."""
        try:
            score = 0.5  # Base score
            
            # Source reliability
            source_scores = {
                KnowledgeSource.COURT_DECISION: 0.9,
                KnowledgeSource.LEGISLATIVE_UPDATE: 0.9,
                KnowledgeSource.EXPERT_INPUT: 0.8,
                KnowledgeSource.CASE_OUTCOME: 0.7,
                KnowledgeSource.INTERNAL_RESEARCH: 0.6,
                KnowledgeSource.AUTOMATED_EXTRACTION: 0.4
            }
            source_score = source_scores.get(entry.source, 0.3)
            
            # Content quality indicators
            has_citations = len(entry.citations) > 0
            has_summary = bool(entry.summary)
            content_length = len(entry.content)
            
            # Calculate weighted score
            score = (
                source_score * 0.4 +
                (0.2 if has_citations else 0.0) +
                (0.1 if has_summary else 0.0) +
                min(0.3, content_length / 1000 * 0.3)  # Length bonus up to 0.3
            )
            
            return min(1.0, score)
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5