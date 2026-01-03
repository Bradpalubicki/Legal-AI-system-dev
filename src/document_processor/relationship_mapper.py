"""
Event relationship mapping system for legal timelines.
Maps complex relationships between events, entities, and temporal sequences.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
from collections import defaultdict
import networkx as nx
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .timeline_extractor import TimelineEvent, Timeline, EventType, EventCertainty
from .chronology_analyzer import ChronologyInsights

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of relationships between events."""
    CAUSAL = "causal"                  # One event causes another
    TEMPORAL = "temporal"              # Time-based relationship
    PROCEDURAL = "procedural"          # Procedural sequence
    CONCURRENT = "concurrent"          # Happening at same time
    CONDITIONAL = "conditional"        # Conditional dependency
    HIERARCHICAL = "hierarchical"      # Parent-child relationship
    CONFLICTING = "conflicting"        # Mutually exclusive
    SUPPORTIVE = "supportive"          # Mutually reinforcing
    PREREQUISITE = "prerequisite"      # Required predecessor
    OUTCOME = "outcome"                # Result of previous events


class EntityRole(Enum):
    """Roles that entities can play in events."""
    ACTOR = "actor"                    # Performs the action
    RECIPIENT = "recipient"            # Receives the action
    BENEFICIARY = "beneficiary"        # Benefits from the action
    AUTHORITY = "authority"            # Has authority over the action
    WITNESS = "witness"                # Observes the action
    FACILITATOR = "facilitator"        # Helps enable the action
    OPPONENT = "opponent"              # Opposes the action
    NEUTRAL = "neutral"                # Neutral party


class RelationshipStrength(Enum):
    """Strength levels for relationships."""
    DEFINITIVE = "definitive"          # Certain relationship
    STRONG = "strong"                  # Very likely relationship
    MODERATE = "moderate"              # Moderately confident
    WEAK = "weak"                      # Possible relationship
    SPECULATIVE = "speculative"        # Highly uncertain


@dataclass
class EventRelationship:
    """Represents a relationship between two events."""
    relationship_id: str
    source_event_id: str
    target_event_id: str
    relationship_type: RelationshipType
    strength: RelationshipStrength
    confidence: float
    
    # Relationship details
    description: str
    time_gap: Optional[timedelta] = None
    shared_entities: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    
    # Context
    context_events: List[str] = field(default_factory=list)
    legal_basis: Optional[str] = None
    procedural_context: Optional[str] = None
    
    # Metadata
    detection_method: str = ""
    validation_status: str = "unvalidated"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EntityRelationship:
    """Represents a relationship between entities across events."""
    relationship_id: str
    entity_1: str
    entity_2: str
    relationship_type: str  # adversarial, collaborative, hierarchical, etc.
    
    # Events where this relationship is observed
    supporting_events: List[str] = field(default_factory=list)
    
    # Relationship characteristics
    strength: RelationshipStrength = RelationshipStrength.WEAK
    roles: Dict[str, EntityRole] = field(default_factory=dict)  # entity -> role
    
    # Temporal aspects
    first_observed: Optional[datetime] = None
    last_observed: Optional[datetime] = None
    relationship_evolution: List[str] = field(default_factory=list)
    
    # Evidence and context
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationshipNetwork:
    """Represents the complete network of relationships."""
    network_id: str
    timeline_id: str
    
    # Relationships
    event_relationships: List[EventRelationship] = field(default_factory=list)
    entity_relationships: List[EntityRelationship] = field(default_factory=list)
    
    # Network analysis results
    central_events: List[str] = field(default_factory=list)
    central_entities: List[str] = field(default_factory=list)
    relationship_clusters: Dict[str, List[str]] = field(default_factory=dict)
    
    # Graph metrics
    network_density: float = 0.0
    average_path_length: float = 0.0
    clustering_coefficient: float = 0.0
    
    # Insights
    key_relationship_patterns: List[str] = field(default_factory=list)
    potential_missing_relationships: List[str] = field(default_factory=list)
    
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)


class RelationshipMapper:
    """Maps and analyzes relationships between events and entities in legal timelines."""
    
    def __init__(self):
        """Initialize relationship mapper."""
        
        # Relationship detection patterns
        self.causal_indicators = [
            r'\bbecause\s+of\b', r'\bas\s+a\s+result\s+of\b', r'\bdue\s+to\b',
            r'\bcaused\s+by\b', r'\brequired\s+by\b', r'\btriggered\s+by\b',
            r'\bin\s+response\s+to\b', r'\bfollowing\b', r'\bafter\b'
        ]
        
        self.temporal_indicators = [
            r'\bbefore\b', r'\bafter\b', r'\bduring\b', r'\bwhile\b',
            r'\bsimultaneously\b', r'\bconcurrently\b', r'\bthen\b'
        ]
        
        self.procedural_indicators = [
            r'\bpursuant\s+to\b', r'\bin\s+accordance\s+with\b',
            r'\bas\s+required\s+by\b', r'\bunder\s+rule\b', r'\bper\b'
        ]
        
        # Legal relationship patterns
        self.legal_relationship_patterns = {
            'adversarial': [
                r'\bplaintiff.*defendant\b', r'\bpetitioner.*respondent\b',
                r'\bversus\b', r'\bv\.\b', r'\bagainst\b'
            ],
            'representative': [
                r'\battorney\s+for\b', r'\bcounsel\s+for\b',
                r'\brepresenting\b', r'\bon\s+behalf\s+of\b'
            ],
            'authoritative': [
                r'\bcourt\s+ordered\b', r'\bjudge\s+ruled\b',
                r'\btribunal\s+decided\b', r'\bauthority\s+determined\b'
            ],
            'contractual': [
                r'\bparties\s+to\b', r'\bsignatory\b', r'\bcounterparty\b',
                r'\bcontractor\b', r'\bvendor\b', r'\bclient\b'
            ]
        }
        
        # Procedural sequences
        self.procedural_sequences = {
            'motion_practice': [
                EventType.MOTION, EventType.HEARING, EventType.ORDER
            ],
            'discovery_process': [
                EventType.DISCOVERY, EventType.DEPOSITION, EventType.MOTION, EventType.ORDER
            ],
            'settlement_negotiation': [
                EventType.COMMUNICATION, EventType.MEETING, EventType.SETTLEMENT
            ],
            'contract_execution': [
                EventType.COMMUNICATION, EventType.CONTRACT, EventType.PAYMENT
            ]
        }
        
        # Initialize TF-IDF for semantic similarity
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            stop_words='english'
        )
        
    def map_relationships(self, timeline: Timeline, 
                         insights: ChronologyInsights = None) -> RelationshipNetwork:
        """Map all relationships in the timeline.
        
        Args:
            timeline: Timeline to analyze
            insights: Optional chronology insights for additional context
            
        Returns:
            Complete relationship network
        """
        logger.info(f"Mapping relationships for timeline: {timeline.timeline_id}")
        
        network = RelationshipNetwork(
            network_id=f"network_{timeline.timeline_id}_{int(datetime.utcnow().timestamp())}",
            timeline_id=timeline.timeline_id
        )
        
        # Map event relationships
        network.event_relationships = self._map_event_relationships(timeline, insights)
        
        # Map entity relationships
        network.entity_relationships = self._map_entity_relationships(timeline)
        
        # Analyze network structure
        self._analyze_network_structure(network, timeline)
        
        # Identify patterns and insights
        self._identify_relationship_patterns(network, timeline)
        
        return network
    
    def _map_event_relationships(self, timeline: Timeline, 
                               insights: ChronologyInsights = None) -> List[EventRelationship]:
        """Map relationships between events."""
        relationships = []
        
        # Direct causal relationships from timeline
        relationships.extend(self._map_direct_causal_relationships(timeline))
        
        # Temporal relationships
        relationships.extend(self._map_temporal_relationships(timeline))
        
        # Procedural relationships
        relationships.extend(self._map_procedural_relationships(timeline))
        
        # Semantic relationships
        relationships.extend(self._map_semantic_relationships(timeline))
        
        # Entity-based relationships
        relationships.extend(self._map_entity_based_relationships(timeline))
        
        # Use insights for additional relationships
        if insights:
            relationships.extend(self._map_insight_relationships(timeline, insights))
        
        return relationships
    
    def _map_direct_causal_relationships(self, timeline: Timeline) -> List[EventRelationship]:
        """Map direct causal relationships already identified in timeline."""
        relationships = []
        
        for event in timeline.events:
            # Map causes
            for cause_id in event.caused_by:
                relationships.append(EventRelationship(
                    relationship_id=f"causal_{cause_id}_{event.event_id}",
                    source_event_id=cause_id,
                    target_event_id=event.event_id,
                    relationship_type=RelationshipType.CAUSAL,
                    strength=RelationshipStrength.STRONG,
                    confidence=0.8,
                    description=f"Direct causal relationship",
                    evidence=["Identified in timeline extraction"],
                    detection_method="timeline_analysis"
                ))
            
            # Map outcomes
            for outcome_id in event.leads_to:
                relationships.append(EventRelationship(
                    relationship_id=f"outcome_{event.event_id}_{outcome_id}",
                    source_event_id=event.event_id,
                    target_event_id=outcome_id,
                    relationship_type=RelationshipType.OUTCOME,
                    strength=RelationshipStrength.STRONG,
                    confidence=0.8,
                    description=f"Direct outcome relationship",
                    evidence=["Identified in timeline extraction"],
                    detection_method="timeline_analysis"
                ))
            
            # Map concurrent events
            for concurrent_id in event.concurrent_with:
                relationships.append(EventRelationship(
                    relationship_id=f"concurrent_{min(event.event_id, concurrent_id)}_{max(event.event_id, concurrent_id)}",
                    source_event_id=event.event_id,
                    target_event_id=concurrent_id,
                    relationship_type=RelationshipType.CONCURRENT,
                    strength=RelationshipStrength.MODERATE,
                    confidence=0.7,
                    description=f"Concurrent events",
                    evidence=["Similar timing identified"],
                    detection_method="timeline_analysis"
                ))
        
        return relationships
    
    def _map_temporal_relationships(self, timeline: Timeline) -> List[EventRelationship]:
        """Map temporal relationships between events."""
        relationships = []
        
        dated_events = [e for e in timeline.events if e.date]
        dated_events.sort(key=lambda x: x.date)
        
        # Sequential relationships
        for i in range(len(dated_events) - 1):
            current_event = dated_events[i]
            next_event = dated_events[i + 1]
            
            time_gap = next_event.date - current_event.date
            
            # Close temporal proximity suggests relationship
            if time_gap.days <= 30:  # Within 30 days
                strength = RelationshipStrength.MODERATE
                confidence = 0.6
                
                if time_gap.days <= 7:  # Within a week
                    strength = RelationshipStrength.STRONG
                    confidence = 0.7
                elif time_gap.days <= 1:  # Same day or next day
                    strength = RelationshipStrength.DEFINITIVE
                    confidence = 0.8
                
                # Check for temporal indicators in text
                evidence = []
                if self._has_temporal_indicators(current_event, next_event):
                    evidence.append("Temporal indicators found in text")
                    confidence += 0.1
                
                relationships.append(EventRelationship(
                    relationship_id=f"temporal_{current_event.event_id}_{next_event.event_id}",
                    source_event_id=current_event.event_id,
                    target_event_id=next_event.event_id,
                    relationship_type=RelationshipType.TEMPORAL,
                    strength=strength,
                    confidence=confidence,
                    description=f"Temporal sequence ({time_gap.days} days apart)",
                    time_gap=time_gap,
                    evidence=evidence,
                    detection_method="temporal_analysis"
                ))
        
        return relationships
    
    def _map_procedural_relationships(self, timeline: Timeline) -> List[EventRelationship]:
        """Map procedural relationships between events."""
        relationships = []
        
        # Map known procedural sequences
        for sequence_name, event_types in self.procedural_sequences.items():
            sequence_events = []
            
            # Find events matching each step in sequence
            for event_type in event_types:
                matching_events = [
                    e for e in timeline.events 
                    if e.event_type == event_type and e.date
                ]
                if matching_events:
                    # Take the earliest event of this type
                    matching_events.sort(key=lambda x: x.date)
                    sequence_events.append(matching_events[0])
            
            # Create relationships between sequential steps
            for i in range(len(sequence_events) - 1):
                current_event = sequence_events[i]
                next_event = sequence_events[i + 1]
                
                # Verify chronological order
                if next_event.date >= current_event.date:
                    relationships.append(EventRelationship(
                        relationship_id=f"procedural_{sequence_name}_{current_event.event_id}_{next_event.event_id}",
                        source_event_id=current_event.event_id,
                        target_event_id=next_event.event_id,
                        relationship_type=RelationshipType.PROCEDURAL,
                        strength=RelationshipStrength.STRONG,
                        confidence=0.8,
                        description=f"Procedural sequence step in {sequence_name.replace('_', ' ')}",
                        procedural_context=sequence_name,
                        evidence=[f"Part of {sequence_name} procedural sequence"],
                        detection_method="procedural_analysis"
                    ))
        
        return relationships
    
    def _map_semantic_relationships(self, timeline: Timeline) -> List[EventRelationship]:
        """Map semantic relationships based on content similarity."""
        relationships = []
        
        if len(timeline.events) < 2:
            return relationships
        
        try:
            # Extract event descriptions for similarity analysis
            descriptions = [event.description for event in timeline.events]
            
            # Create TF-IDF vectors
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(descriptions)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Find high-similarity pairs
            for i in range(len(timeline.events)):
                for j in range(i + 1, len(timeline.events)):
                    similarity = similarity_matrix[i][j]
                    
                    if similarity > 0.3:  # Threshold for semantic similarity
                        event_i = timeline.events[i]
                        event_j = timeline.events[j]
                        
                        strength = RelationshipStrength.WEAK
                        if similarity > 0.7:
                            strength = RelationshipStrength.STRONG
                        elif similarity > 0.5:
                            strength = RelationshipStrength.MODERATE
                        
                        relationships.append(EventRelationship(
                            relationship_id=f"semantic_{event_i.event_id}_{event_j.event_id}",
                            source_event_id=event_i.event_id,
                            target_event_id=event_j.event_id,
                            relationship_type=RelationshipType.SUPPORTIVE,
                            strength=strength,
                            confidence=similarity,
                            description=f"Semantic similarity (score: {similarity:.3f})",
                            evidence=[f"Content similarity score: {similarity:.3f}"],
                            detection_method="semantic_analysis",
                            metadata={"similarity_score": similarity}
                        ))
                        
        except Exception as e:
            logger.warning(f"Semantic relationship mapping failed: {e}")
        
        return relationships
    
    def _map_entity_based_relationships(self, timeline: Timeline) -> List[EventRelationship]:
        """Map relationships based on shared entities."""
        relationships = []
        
        # Group events by shared participants
        participant_events = defaultdict(list)
        for event in timeline.events:
            for participant in event.participants:
                participant_events[participant].append(event)
        
        # Create relationships between events with shared participants
        for participant, events in participant_events.items():
            if len(events) > 1:
                # Create relationships between all pairs of events with this participant
                for i in range(len(events)):
                    for j in range(i + 1, len(events)):
                        event_i = events[i]
                        event_j = events[j]
                        
                        # Determine relationship strength based on how many entities are shared
                        shared_participants = set(event_i.participants) & set(event_j.participants)
                        strength = RelationshipStrength.WEAK
                        
                        if len(shared_participants) > 2:
                            strength = RelationshipStrength.STRONG
                        elif len(shared_participants) > 1:
                            strength = RelationshipStrength.MODERATE
                        
                        relationships.append(EventRelationship(
                            relationship_id=f"entity_{event_i.event_id}_{event_j.event_id}",
                            source_event_id=event_i.event_id,
                            target_event_id=event_j.event_id,
                            relationship_type=RelationshipType.SUPPORTIVE,
                            strength=strength,
                            confidence=0.6,
                            description=f"Shared participants: {', '.join(shared_participants)}",
                            shared_entities=list(shared_participants),
                            evidence=[f"Shared participants: {len(shared_participants)}"],
                            detection_method="entity_analysis"
                        ))
        
        return relationships
    
    def _map_insight_relationships(self, timeline: Timeline, 
                                 insights: ChronologyInsights) -> List[EventRelationship]:
        """Map relationships based on chronology insights."""
        relationships = []
        
        # Use causal relationships from insights
        for causal_rel in insights.causal_relationships:
            relationships.append(EventRelationship(
                relationship_id=f"insight_causal_{causal_rel.relationship_id}",
                source_event_id=causal_rel.cause_event,
                target_event_id=causal_rel.effect_event,
                relationship_type=RelationshipType.CAUSAL,
                strength=RelationshipStrength[causal_rel.strength.upper()],
                confidence=causal_rel.confidence,
                description=f"Causal relationship identified in analysis",
                time_gap=causal_rel.time_delay,
                evidence=causal_rel.evidence,
                detection_method="chronology_analysis",
                metadata={"analysis_relationship_id": causal_rel.relationship_id}
            ))
        
        # Use event clusters for supportive relationships
        for cluster in insights.event_clusters:
            cluster_events = cluster.events
            if len(cluster_events) > 1:
                # Create supportive relationships within clusters
                for i in range(len(cluster_events)):
                    for j in range(i + 1, len(cluster_events)):
                        relationships.append(EventRelationship(
                            relationship_id=f"cluster_{cluster.cluster_id}_{cluster_events[i]}_{cluster_events[j]}",
                            source_event_id=cluster_events[i],
                            target_event_id=cluster_events[j],
                            relationship_type=RelationshipType.SUPPORTIVE,
                            strength=RelationshipStrength.MODERATE,
                            confidence=cluster.coherence_score,
                            description=f"Events in same cluster ({cluster.cluster_type})",
                            evidence=[f"Part of {cluster.cluster_type} cluster"],
                            detection_method="cluster_analysis"
                        ))
        
        return relationships
    
    def _map_entity_relationships(self, timeline: Timeline) -> List[EntityRelationship]:
        """Map relationships between entities across events."""
        relationships = []
        
        # Collect all entities and their event participation
        entity_events = defaultdict(list)
        for event in timeline.events:
            for participant in event.participants:
                entity_events[participant].append(event)
        
        entities = list(entity_events.keys())
        
        # Create relationships between entity pairs
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                entity_1 = entities[i]
                entity_2 = entities[j]
                
                # Find events where both entities appear
                shared_events = []
                entity_1_events = set(e.event_id for e in entity_events[entity_1])
                entity_2_events = set(e.event_id for e in entity_events[entity_2])
                shared_event_ids = entity_1_events & entity_2_events
                
                if shared_event_ids:
                    # Determine relationship type
                    relationship_type = self._determine_entity_relationship_type(
                        entity_1, entity_2, timeline.events
                    )
                    
                    # Calculate relationship strength
                    strength = RelationshipStrength.WEAK
                    if len(shared_event_ids) > 3:
                        strength = RelationshipStrength.STRONG
                    elif len(shared_event_ids) > 1:
                        strength = RelationshipStrength.MODERATE
                    
                    # Get temporal bounds
                    relevant_events = [
                        e for e in timeline.events 
                        if e.event_id in shared_event_ids and e.date
                    ]
                    
                    if relevant_events:
                        relevant_events.sort(key=lambda x: x.date)
                        first_observed = relevant_events[0].date
                        last_observed = relevant_events[-1].date
                    else:
                        first_observed = None
                        last_observed = None
                    
                    relationships.append(EntityRelationship(
                        relationship_id=f"entity_rel_{hash(entity_1 + entity_2)}",
                        entity_1=entity_1,
                        entity_2=entity_2,
                        relationship_type=relationship_type,
                        supporting_events=list(shared_event_ids),
                        strength=strength,
                        first_observed=first_observed,
                        last_observed=last_observed,
                        confidence=min(1.0, len(shared_event_ids) * 0.2),
                        evidence=[f"Co-appear in {len(shared_event_ids)} events"]
                    ))
        
        return relationships
    
    def _analyze_network_structure(self, network: RelationshipNetwork, timeline: Timeline):
        """Analyze the structure of the relationship network."""
        
        # Create NetworkX graph
        G = nx.DiGraph()
        
        # Add event nodes
        for event in timeline.events:
            G.add_node(event.event_id, node_type='event', event=event)
        
        # Add relationship edges
        for rel in network.event_relationships:
            G.add_edge(
                rel.source_event_id, 
                rel.target_event_id,
                relationship=rel,
                weight=rel.confidence
            )
        
        # Calculate network metrics
        if G.nodes():
            network.network_density = nx.density(G)
            
            try:
                if nx.is_strongly_connected(G):
                    network.average_path_length = nx.average_shortest_path_length(G)
                else:
                    # For disconnected graphs, calculate for largest component
                    largest_cc = max(nx.strongly_connected_components(G), key=len)
                    subgraph = G.subgraph(largest_cc)
                    if len(subgraph) > 1:
                        network.average_path_length = nx.average_shortest_path_length(subgraph)
            except:
                network.average_path_length = 0.0
            
            # Calculate clustering coefficient for undirected version
            try:
                undirected_G = G.to_undirected()
                network.clustering_coefficient = nx.average_clustering(undirected_G)
            except:
                network.clustering_coefficient = 0.0
            
            # Find central events
            try:
                centrality = nx.degree_centrality(G)
                sorted_centrality = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
                network.central_events = [event_id for event_id, _ in sorted_centrality[:5]]
            except:
                network.central_events = []
        
        # Find central entities
        entity_participation = defaultdict(int)
        for event in timeline.events:
            for participant in event.participants:
                entity_participation[participant] += 1
        
        sorted_entities = sorted(entity_participation.items(), key=lambda x: x[1], reverse=True)
        network.central_entities = [entity for entity, _ in sorted_entities[:5]]
    
    def _identify_relationship_patterns(self, network: RelationshipNetwork, timeline: Timeline):
        """Identify patterns in the relationship network."""
        
        patterns = []
        
        # Analyze relationship type distribution
        relationship_types = defaultdict(int)
        for rel in network.event_relationships:
            relationship_types[rel.relationship_type.value] += 1
        
        if relationship_types:
            most_common = max(relationship_types.items(), key=lambda x: x[1])
            patterns.append(f"Most common relationship type: {most_common[0]} ({most_common[1]} instances)")
        
        # Analyze causal chains
        causal_relationships = [
            rel for rel in network.event_relationships 
            if rel.relationship_type == RelationshipType.CAUSAL
        ]
        
        if len(causal_relationships) > 2:
            patterns.append(f"Complex causal network with {len(causal_relationships)} causal relationships")
        
        # Analyze temporal clustering
        concurrent_relationships = [
            rel for rel in network.event_relationships 
            if rel.relationship_type == RelationshipType.CONCURRENT
        ]
        
        if len(concurrent_relationships) > 3:
            patterns.append(f"High concurrent activity with {len(concurrent_relationships)} simultaneous events")
        
        # Analyze entity involvement
        entity_involvement = defaultdict(set)
        for rel in network.entity_relationships:
            for event_id in rel.supporting_events:
                entity_involvement[rel.entity_1].add(event_id)
                entity_involvement[rel.entity_2].add(event_id)
        
        if entity_involvement:
            max_involvement = max(len(events) for events in entity_involvement.values())
            if max_involvement > 5:
                patterns.append(f"High entity involvement with up to {max_involvement} events per entity")
        
        network.key_relationship_patterns = patterns
        
        # Identify potential missing relationships
        missing = []
        
        # Look for events that should be connected but aren't
        for event in timeline.events:
            event_relationships = [
                rel for rel in network.event_relationships
                if rel.source_event_id == event.event_id or rel.target_event_id == event.event_id
            ]
            
            if len(event_relationships) == 0 and event.confidence > 0.7:
                missing.append(f"High-confidence event {event.event_id} has no relationships")
        
        # Look for entity pairs that appear together but have no relationship
        entity_cooccurrence = defaultdict(set)
        for event in timeline.events:
            for i, participant_1 in enumerate(event.participants):
                for participant_2 in event.participants[i+1:]:
                    entity_cooccurrence[tuple(sorted([participant_1, participant_2]))].add(event.event_id)
        
        existing_entity_pairs = set()
        for rel in network.entity_relationships:
            existing_entity_pairs.add(tuple(sorted([rel.entity_1, rel.entity_2])))
        
        for entity_pair, events in entity_cooccurrence.items():
            if len(events) > 2 and entity_pair not in existing_entity_pairs:
                missing.append(f"Entities {entity_pair[0]} and {entity_pair[1]} co-occur in {len(events)} events but have no relationship")
        
        network.potential_missing_relationships = missing[:10]  # Limit to top 10
    
    def _has_temporal_indicators(self, event1: TimelineEvent, event2: TimelineEvent) -> bool:
        """Check if events have temporal indicators in their text."""
        combined_text = event1.source_sentence + " " + event2.source_sentence
        
        for pattern in self.temporal_indicators:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return True
        
        return False
    
    def _determine_entity_relationship_type(self, entity1: str, entity2: str, 
                                          events: List[TimelineEvent]) -> str:
        """Determine the type of relationship between two entities."""
        
        # Analyze context where entities appear together
        combined_contexts = []
        for event in events:
            if entity1 in event.participants and entity2 in event.participants:
                combined_contexts.append(event.source_sentence.lower())
        
        combined_text = " ".join(combined_contexts)
        
        # Check for relationship patterns
        for relationship_type, patterns in self.legal_relationship_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    return relationship_type
        
        # Default to collaborative if no specific pattern found
        return "collaborative"
    
    def validate_relationships(self, network: RelationshipNetwork, 
                             timeline: Timeline) -> Dict[str, Any]:
        """Validate the identified relationships."""
        
        validation_results = {
            "total_relationships": len(network.event_relationships),
            "validated_relationships": 0,
            "high_confidence_relationships": 0,
            "potential_errors": [],
            "validation_warnings": []
        }
        
        for rel in network.event_relationships:
            # Check if source and target events exist
            source_exists = any(e.event_id == rel.source_event_id for e in timeline.events)
            target_exists = any(e.event_id == rel.target_event_id for e in timeline.events)
            
            if not source_exists or not target_exists:
                validation_results["potential_errors"].append(
                    f"Relationship {rel.relationship_id} references non-existent events"
                )
                continue
            
            # Check temporal consistency for causal relationships
            if rel.relationship_type == RelationshipType.CAUSAL:
                source_event = next(e for e in timeline.events if e.event_id == rel.source_event_id)
                target_event = next(e for e in timeline.events if e.event_id == rel.target_event_id)
                
                if (source_event.date and target_event.date and 
                    source_event.date > target_event.date):
                    validation_results["potential_errors"].append(
                        f"Causal relationship {rel.relationship_id} has effect before cause"
                    )
                    continue
            
            # Count validated relationships
            validation_results["validated_relationships"] += 1
            
            if rel.confidence > 0.7:
                validation_results["high_confidence_relationships"] += 1
            elif rel.confidence < 0.3:
                validation_results["validation_warnings"].append(
                    f"Low confidence relationship: {rel.relationship_id} (confidence: {rel.confidence:.2f})"
                )
        
        return validation_results
    
    def export_network(self, network: RelationshipNetwork, format: str = "json") -> str:
        """Export relationship network in specified format."""
        
        if format.lower() == "json":
            # Convert to JSON-serializable format
            data = {
                "network_id": network.network_id,
                "timeline_id": network.timeline_id,
                "network_metrics": {
                    "density": network.network_density,
                    "average_path_length": network.average_path_length,
                    "clustering_coefficient": network.clustering_coefficient
                },
                "central_events": network.central_events,
                "central_entities": network.central_entities,
                "event_relationships": [
                    {
                        "relationship_id": rel.relationship_id,
                        "source_event_id": rel.source_event_id,
                        "target_event_id": rel.target_event_id,
                        "relationship_type": rel.relationship_type.value,
                        "strength": rel.strength.value,
                        "confidence": rel.confidence,
                        "description": rel.description,
                        "time_gap_days": rel.time_gap.days if rel.time_gap else None,
                        "shared_entities": rel.shared_entities,
                        "evidence": rel.evidence,
                        "detection_method": rel.detection_method
                    }
                    for rel in network.event_relationships
                ],
                "entity_relationships": [
                    {
                        "relationship_id": rel.relationship_id,
                        "entity_1": rel.entity_1,
                        "entity_2": rel.entity_2,
                        "relationship_type": rel.relationship_type,
                        "strength": rel.strength.value,
                        "supporting_events": rel.supporting_events,
                        "confidence": rel.confidence,
                        "first_observed": rel.first_observed.isoformat() if rel.first_observed else None,
                        "last_observed": rel.last_observed.isoformat() if rel.last_observed else None
                    }
                    for rel in network.entity_relationships
                ],
                "patterns": network.key_relationship_patterns,
                "potential_missing": network.potential_missing_relationships,
                "creation_timestamp": network.creation_timestamp.isoformat()
            }
            
            return json.dumps(data, indent=2, default=str)
            
        elif format.lower() == "graphml":
            # Export as GraphML for network analysis tools
            import networkx as nx
            
            G = nx.DiGraph()
            
            # Add nodes for events
            event_ids = set()
            for rel in network.event_relationships:
                event_ids.add(rel.source_event_id)
                event_ids.add(rel.target_event_id)
            
            for event_id in event_ids:
                G.add_node(event_id, node_type='event')
            
            # Add relationship edges
            for rel in network.event_relationships:
                G.add_edge(
                    rel.source_event_id,
                    rel.target_event_id,
                    relationship_type=rel.relationship_type.value,
                    strength=rel.strength.value,
                    confidence=rel.confidence,
                    description=rel.description
                )
            
            # Return GraphML string
            import io
            output = io.StringIO()
            nx.write_graphml(G, output)
            return output.getvalue()
            
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_relationship_statistics(self, network: RelationshipNetwork) -> Dict[str, Any]:
        """Get comprehensive relationship statistics."""
        
        event_rels = network.event_relationships
        entity_rels = network.entity_relationships
        
        # Event relationship statistics
        event_stats = {
            "total_event_relationships": len(event_rels),
            "relationship_types": {
                rt.value: len([r for r in event_rels if r.relationship_type == rt])
                for rt in RelationshipType
                if any(r.relationship_type == rt for r in event_rels)
            },
            "strength_distribution": {
                rs.value: len([r for r in event_rels if r.strength == rs])
                for rs in RelationshipStrength
                if any(r.strength == rs for r in event_rels)
            },
            "average_confidence": sum(r.confidence for r in event_rels) / len(event_rels) if event_rels else 0,
            "detection_methods": {
                method: len([r for r in event_rels if r.detection_method == method])
                for method in set(r.detection_method for r in event_rels)
            }
        }
        
        # Entity relationship statistics
        entity_stats = {
            "total_entity_relationships": len(entity_rels),
            "entity_relationship_types": {
                rt: len([r for r in entity_rels if r.relationship_type == rt])
                for rt in set(r.relationship_type for r in entity_rels)
            },
            "average_supporting_events": sum(len(r.supporting_events) for r in entity_rels) / len(entity_rels) if entity_rels else 0
        }
        
        return {
            "network_metrics": {
                "density": network.network_density,
                "average_path_length": network.average_path_length,
                "clustering_coefficient": network.clustering_coefficient
            },
            "event_relationships": event_stats,
            "entity_relationships": entity_stats,
            "central_events_count": len(network.central_events),
            "central_entities_count": len(network.central_entities),
            "identified_patterns_count": len(network.key_relationship_patterns),
            "potential_missing_count": len(network.potential_missing_relationships)
        }