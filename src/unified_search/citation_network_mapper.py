"""
Citation network mapping engine for legal documents.
Creates comprehensive citation networks, analyzes citation patterns, and provides network-based insights.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
import numpy as np
from collections import defaultdict, deque

from ..types.unified_types import UnifiedDocument, ContentType
from .shepardizing_engine import TreatmentSignal, CitingCase
from .citation_validator import CitationValidator


class NodeType(Enum):
    """Types of nodes in citation network."""
    CASE = "case"
    STATUTE = "statute"
    REGULATION = "regulation"
    CONSTITUTION = "constitution"
    LAW_REVIEW = "law_review"
    BOOK = "book"
    SECONDARY = "secondary"


class EdgeType(Enum):
    """Types of edges in citation network."""
    CITES = "cites"                    # Direct citation
    CITED_BY = "cited_by"              # Reverse citation
    OVERRULES = "overrules"            # One case overrules another
    FOLLOWS = "follows"                # One case follows another
    DISTINGUISHES = "distinguishes"    # One case distinguishes another
    QUESTIONS = "questions"            # One case questions another
    SUPERSEDES = "supersedes"          # Statute supersedes case/statute
    IMPLEMENTS = "implements"          # Regulation implements statute


class NetworkScope(Enum):
    """Scope of network analysis."""
    IMMEDIATE = "immediate"            # Direct citations only
    EXTENDED = "extended"              # 2-3 degrees of separation
    COMPREHENSIVE = "comprehensive"    # Full network within limits


@dataclass
class NetworkNode:
    """Node in citation network."""
    node_id: str
    node_type: NodeType
    title: str
    citation: str
    court: Optional[str] = None
    jurisdiction: Optional[str] = None
    decision_date: Optional[datetime] = None
    
    # Network metrics
    in_degree: int = 0
    out_degree: int = 0
    betweenness_centrality: float = 0.0
    closeness_centrality: float = 0.0
    pagerank: float = 0.0
    authority_score: float = 0.0
    
    # Content metadata
    practice_areas: List[str] = field(default_factory=list)
    key_legal_concepts: List[str] = field(default_factory=list)
    
    # Visual attributes
    size: float = 1.0
    color: str = "#1f77b4"
    label: str = ""


@dataclass
class NetworkEdge:
    """Edge in citation network."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    treatment_signal: Optional[TreatmentSignal] = None
    
    # Context information
    page_references: List[str] = field(default_factory=list)
    context_snippet: Optional[str] = None
    citation_strength: float = 1.0  # How prominent the citation is
    
    # Temporal information
    citation_date: Optional[datetime] = None
    
    # Visual attributes
    weight: float = 1.0
    color: str = "#999999"
    style: str = "solid"


@dataclass
class NetworkCluster:
    """Cluster of related nodes in citation network."""
    cluster_id: str
    cluster_type: str
    nodes: List[str]
    description: str
    coherence_score: float
    key_concepts: List[str] = field(default_factory=list)


@dataclass
class NetworkPath:
    """Path between nodes in citation network."""
    source_id: str
    target_id: str
    path_nodes: List[str]
    path_length: int
    path_strength: float
    path_description: str


@dataclass
class NetworkAnalysis:
    """Comprehensive network analysis results."""
    network_id: str
    center_node_id: str
    analysis_date: datetime
    
    # Network structure
    total_nodes: int
    total_edges: int
    network_density: float
    average_path_length: float
    clustering_coefficient: float
    
    # Key nodes and edges
    nodes: Dict[str, NetworkNode]
    edges: List[NetworkEdge]
    
    # Network metrics
    most_cited_cases: List[Tuple[str, int]]
    most_influential_cases: List[Tuple[str, float]]
    authority_rankings: List[Tuple[str, float]]
    
    # Clusters and communities
    clusters: List[NetworkCluster]
    
    # Citation patterns
    citation_patterns: Dict[str, Any]
    
    # Paths and connections
    key_paths: List[NetworkPath]
    
    # Insights and recommendations
    insights: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class CitationNetworkMapper:
    """
    Advanced citation network mapping and analysis engine.
    
    Creates comprehensive citation networks, analyzes citation patterns,
    identifies influential authorities, and provides network-based insights
    for legal research and analysis.
    """
    
    def __init__(self, citation_validator: Optional[CitationValidator] = None):
        self.citation_validator = citation_validator or CitationValidator()
        self.logger = logging.getLogger(__name__)
        
        # Network cache
        self.network_cache: Dict[str, nx.DiGraph] = {}
        self.cache_ttl = timedelta(hours=4)
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Color schemes for different node types
        self.node_colors = {
            NodeType.CASE: "#2E86AB",
            NodeType.STATUTE: "#A23B72",
            NodeType.REGULATION: "#F18F01",
            NodeType.CONSTITUTION: "#C73E1D",
            NodeType.LAW_REVIEW: "#6A994E",
            NodeType.BOOK: "#BC4749",
            NodeType.SECONDARY: "#8E9AAF"
        }
        
        # Edge colors for different treatment signals
        self.edge_colors = {
            TreatmentSignal.FOLLOWED: "#2E8B57",
            TreatmentSignal.OVERRULED: "#DC143C",
            TreatmentSignal.QUESTIONED: "#FF8C00",
            TreatmentSignal.CITED: "#4169E1",
            TreatmentSignal.DISTINGUISHED: "#DAA520",
            None: "#808080"
        }
    
    async def build_citation_network(self, 
                                   center_document: UnifiedDocument,
                                   scope: NetworkScope = NetworkScope.EXTENDED,
                                   max_depth: int = 3,
                                   max_nodes: int = 500) -> NetworkAnalysis:
        """
        Build comprehensive citation network around a center document.
        
        Args:
            center_document: The central document to analyze
            scope: Scope of network analysis
            max_depth: Maximum degrees of separation to explore
            max_nodes: Maximum number of nodes to include
            
        Returns:
            Comprehensive network analysis
        """
        self.logger.info(f"Building citation network for: {center_document.title}")
        
        # Initialize network
        network = nx.DiGraph()
        
        # Add center node
        center_node = await self._create_network_node(center_document)
        network.add_node(center_document.id, **center_node.__dict__)
        
        # Build network based on scope
        if scope == NetworkScope.IMMEDIATE:
            max_depth = 1
        elif scope == NetworkScope.EXTENDED:
            max_depth = min(max_depth, 2)
        elif scope == NetworkScope.COMPREHENSIVE:
            max_depth = min(max_depth, 3)
        
        # Breadth-first expansion of network
        await self._expand_network_bfs(
            network, center_document.id, max_depth, max_nodes
        )
        
        # Calculate network metrics
        await self._calculate_network_metrics(network)
        
        # Identify clusters
        clusters = await self._identify_network_clusters(network)
        
        # Analyze citation patterns
        citation_patterns = await self._analyze_citation_patterns(network)
        
        # Find key paths
        key_paths = await self._find_key_citation_paths(network, center_document.id)
        
        # Generate insights
        insights, warnings = await self._generate_network_insights(network, clusters, citation_patterns)
        
        # Create analysis result
        analysis = await self._create_network_analysis(
            network, center_document.id, clusters, citation_patterns, key_paths, insights, warnings
        )
        
        return analysis
    
    async def _create_network_node(self, document: UnifiedDocument) -> NetworkNode:
        """Create a network node from a document."""
        
        # Determine node type
        node_type = self._document_type_to_node_type(document.content_type)
        
        # Extract basic information
        citation = ""
        if document.citations:
            citation = document.citations[0]
        
        # Extract practice areas and legal concepts (simplified)
        practice_areas = await self._extract_practice_areas(document)
        legal_concepts = await self._extract_legal_concepts(document)
        
        # Determine visual attributes
        color = self.node_colors.get(node_type, "#1f77b4")
        label = document.title[:50] + "..." if document.title and len(document.title) > 50 else document.title or ""
        
        return NetworkNode(
            node_id=document.id,
            node_type=node_type,
            title=document.title or "Unknown Document",
            citation=citation,
            court=getattr(document, 'court', None),
            jurisdiction=getattr(document, 'jurisdiction', None),
            decision_date=getattr(document, 'decision_date', None),
            practice_areas=practice_areas,
            key_legal_concepts=legal_concepts,
            color=color,
            label=label
        )
    
    def _document_type_to_node_type(self, content_type: ContentType) -> NodeType:
        """Convert document content type to network node type."""
        mapping = {
            ContentType.CASE_LAW: NodeType.CASE,
            ContentType.STATUTE: NodeType.STATUTE,
            ContentType.REGULATION: NodeType.REGULATION,
            ContentType.CONSTITUTIONAL: NodeType.CONSTITUTION,
            ContentType.LAW_REVIEW: NodeType.LAW_REVIEW,
            ContentType.LEGAL_BRIEF: NodeType.SECONDARY,
            ContentType.PRACTICE_GUIDE: NodeType.SECONDARY,
            ContentType.TREATISE: NodeType.BOOK
        }
        return mapping.get(content_type, NodeType.SECONDARY)
    
    async def _extract_practice_areas(self, document: UnifiedDocument) -> List[str]:
        """Extract practice areas from document (simplified implementation)."""
        if not document.content:
            return []
        
        # Common practice area keywords
        practice_area_keywords = {
            "contract": "Contract Law",
            "tort": "Tort Law",
            "constitutional": "Constitutional Law",
            "criminal": "Criminal Law",
            "employment": "Employment Law",
            "intellectual property": "Intellectual Property",
            "corporate": "Corporate Law",
            "securities": "Securities Law",
            "tax": "Tax Law",
            "environmental": "Environmental Law",
            "antitrust": "Antitrust Law",
            "bankruptcy": "Bankruptcy Law",
            "family": "Family Law",
            "immigration": "Immigration Law",
            "civil rights": "Civil Rights Law"
        }
        
        content_lower = document.content.lower()[:2000]  # First 2000 chars
        practice_areas = []
        
        for keyword, area in practice_area_keywords.items():
            if keyword in content_lower:
                practice_areas.append(area)
        
        return list(set(practice_areas))[:5]  # Limit to 5
    
    async def _extract_legal_concepts(self, document: UnifiedDocument) -> List[str]:
        """Extract key legal concepts from document (simplified implementation)."""
        if not document.content:
            return []
        
        # Common legal concepts
        legal_concepts = [
            "due process", "equal protection", "probable cause", "reasonable doubt",
            "negligence", "strict liability", "breach of contract", "consideration",
            "jurisdiction", "standing", "summary judgment", "res judicata",
            "stare decisis", "precedent", "statutory interpretation"
        ]
        
        content_lower = document.content.lower()[:2000]  # First 2000 chars
        found_concepts = []
        
        for concept in legal_concepts:
            if concept in content_lower:
                found_concepts.append(concept)
        
        return found_concepts[:10]  # Limit to 10
    
    async def _expand_network_bfs(self, 
                                network: nx.DiGraph, 
                                start_node_id: str, 
                                max_depth: int, 
                                max_nodes: int):
        """Expand network using breadth-first search."""
        
        queue = deque([(start_node_id, 0)])  # (node_id, depth)
        visited = set([start_node_id])
        
        while queue and len(network.nodes) < max_nodes:
            current_node_id, current_depth = queue.popleft()
            
            if current_depth >= max_depth:
                continue
            
            # Find documents that cite current document (citing cases)
            citing_documents = await self._find_citing_documents(current_node_id)
            
            # Find documents cited by current document (cited cases)
            cited_documents = await self._find_cited_documents(current_node_id)
            
            # Add citing documents
            for citing_doc, citing_info in citing_documents:
                if citing_doc.id not in visited and len(network.nodes) < max_nodes:
                    # Add node
                    citing_node = await self._create_network_node(citing_doc)
                    network.add_node(citing_doc.id, **citing_node.__dict__)
                    
                    # Add edge (citing -> current)
                    edge = NetworkEdge(
                        source_id=citing_doc.id,
                        target_id=current_node_id,
                        edge_type=EdgeType.CITES,
                        treatment_signal=citing_info.get('treatment_signal'),
                        context_snippet=citing_info.get('context'),
                        citation_date=citing_info.get('date'),
                        color=self.edge_colors.get(citing_info.get('treatment_signal')),
                        weight=citing_info.get('strength', 1.0)
                    )
                    
                    network.add_edge(
                        citing_doc.id, 
                        current_node_id,
                        **edge.__dict__
                    )
                    
                    queue.append((citing_doc.id, current_depth + 1))
                    visited.add(citing_doc.id)
            
            # Add cited documents
            for cited_doc, citation_info in cited_documents:
                if cited_doc.id not in visited and len(network.nodes) < max_nodes:
                    # Add node
                    cited_node = await self._create_network_node(cited_doc)
                    network.add_node(cited_doc.id, **cited_node.__dict__)
                    
                    # Add edge (current -> cited)
                    edge = NetworkEdge(
                        source_id=current_node_id,
                        target_id=cited_doc.id,
                        edge_type=EdgeType.CITES,
                        context_snippet=citation_info.get('context'),
                        citation_date=citation_info.get('date'),
                        color=self.edge_colors.get(None),
                        weight=citation_info.get('strength', 1.0)
                    )
                    
                    network.add_edge(
                        current_node_id,
                        cited_doc.id,
                        **edge.__dict__
                    )
                    
                    queue.append((cited_doc.id, current_depth + 1))
                    visited.add(cited_doc.id)
    
    async def _find_citing_documents(self, document_id: str) -> List[Tuple[UnifiedDocument, Dict[str, Any]]]:
        """Find documents that cite the given document."""
        # This would typically query a legal database
        # For demonstration, we'll simulate finding citing documents
        
        citing_documents = []
        
        # Simulate 3-5 citing documents
        for i in range(3):
            citing_doc = UnifiedDocument(
                id=f"citing_{document_id}_{i}",
                title=f"Citing Case {i+1}",
                content_type=ContentType.CASE_LAW,
                content=f"This case cites {document_id} for the principle that...",
                citations=[f"{100+i} F.3d {200+i*10}"]
            )
            
            citing_info = {
                'treatment_signal': [TreatmentSignal.FOLLOWED, TreatmentSignal.CITED, TreatmentSignal.QUESTIONED][i % 3],
                'context': f"Following the holding in the cited case, we conclude...",
                'date': datetime(2020 + i, 1, 1),
                'strength': 0.8
            }
            
            citing_documents.append((citing_doc, citing_info))
        
        return citing_documents
    
    async def _find_cited_documents(self, document_id: str) -> List[Tuple[UnifiedDocument, Dict[str, Any]]]:
        """Find documents cited by the given document."""
        # This would typically analyze the document's citations
        # For demonstration, we'll simulate finding cited documents
        
        cited_documents = []
        
        # Simulate 2-4 cited documents
        for i in range(2):
            cited_doc = UnifiedDocument(
                id=f"cited_{document_id}_{i}",
                title=f"Cited Authority {i+1}",
                content_type=ContentType.CASE_LAW if i % 2 == 0 else ContentType.STATUTE,
                content=f"This is the authority cited by {document_id}...",
                citations=[f"{50+i} U.S. {300+i*50}" if i % 2 == 0 else f"{10+i} U.S.C. § {100+i}"]
            )
            
            citation_info = {
                'context': f"As established in this precedent...",
                'date': datetime(2019 - i, 1, 1),
                'strength': 0.9
            }
            
            cited_documents.append((cited_doc, citation_info))
        
        return cited_documents
    
    async def _calculate_network_metrics(self, network: nx.DiGraph):
        """Calculate various network metrics for all nodes."""
        
        # Basic degree metrics
        in_degrees = dict(network.in_degree())
        out_degrees = dict(network.out_degree())
        
        # Centrality metrics
        try:
            betweenness = nx.betweenness_centrality(network)
            closeness = nx.closeness_centrality(network)
            pagerank = nx.pagerank(network)
        except:
            # Fallback if network is too small or disconnected
            betweenness = {node: 0.0 for node in network.nodes()}
            closeness = {node: 0.0 for node in network.nodes()}
            pagerank = {node: 1.0/len(network.nodes()) for node in network.nodes()}
        
        # Authority scores (simplified HITS algorithm)
        try:
            hits_hubs, hits_authorities = nx.hits(network)
            authority_scores = hits_authorities
        except:
            authority_scores = {node: 0.5 for node in network.nodes()}
        
        # Update node attributes
        for node_id in network.nodes():
            node_data = network.nodes[node_id]
            node_data['in_degree'] = in_degrees.get(node_id, 0)
            node_data['out_degree'] = out_degrees.get(node_id, 0)
            node_data['betweenness_centrality'] = betweenness.get(node_id, 0.0)
            node_data['closeness_centrality'] = closeness.get(node_id, 0.0)
            node_data['pagerank'] = pagerank.get(node_id, 0.0)
            node_data['authority_score'] = authority_scores.get(node_id, 0.0)
            
            # Set visual size based on importance (combination of metrics)
            importance = (
                0.3 * node_data['in_degree'] / max(1, max(in_degrees.values())) +
                0.3 * node_data['pagerank'] / max(1, max(pagerank.values())) +
                0.4 * node_data['authority_score'] / max(1, max(authority_scores.values()))
            )
            node_data['size'] = 0.5 + importance * 2.0  # Scale between 0.5 and 2.5
    
    async def _identify_network_clusters(self, network: nx.DiGraph) -> List[NetworkCluster]:
        """Identify clusters/communities in the citation network."""
        clusters = []
        
        if len(network.nodes()) < 3:
            return clusters
        
        try:
            # Convert to undirected for community detection
            undirected = network.to_undirected()
            
            # Simple clustering based on connected components
            components = list(nx.connected_components(undirected))
            
            for i, component in enumerate(components):
                if len(component) > 2:  # Only consider meaningful clusters
                    
                    # Analyze cluster characteristics
                    cluster_nodes = list(component)
                    
                    # Get common practice areas
                    all_practice_areas = []
                    for node_id in cluster_nodes:
                        node_data = network.nodes[node_id]
                        all_practice_areas.extend(node_data.get('practice_areas', []))
                    
                    # Find most common practice areas
                    area_counts = {}
                    for area in all_practice_areas:
                        area_counts[area] = area_counts.get(area, 0) + 1
                    
                    top_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                    key_concepts = [area for area, count in top_areas]
                    
                    # Determine cluster type and description
                    if key_concepts:
                        cluster_type = key_concepts[0].replace(" Law", "").lower()
                        description = f"Cluster focused on {', '.join(key_concepts[:2])}"
                    else:
                        cluster_type = "general"
                        description = f"General legal cluster with {len(cluster_nodes)} cases"
                    
                    # Calculate coherence score (simplified)
                    coherence_score = len(set(all_practice_areas)) / max(1, len(cluster_nodes))
                    coherence_score = max(0.0, min(1.0, 1.0 - coherence_score))  # Invert and normalize
                    
                    cluster = NetworkCluster(
                        cluster_id=f"cluster_{i}",
                        cluster_type=cluster_type,
                        nodes=cluster_nodes,
                        description=description,
                        coherence_score=coherence_score,
                        key_concepts=key_concepts
                    )
                    
                    clusters.append(cluster)
            
        except Exception as e:
            self.logger.warning(f"Failed to identify clusters: {e}")
        
        return clusters
    
    async def _analyze_citation_patterns(self, network: nx.DiGraph) -> Dict[str, Any]:
        """Analyze patterns in the citation network."""
        patterns = {
            "node_type_distribution": {},
            "edge_type_distribution": {},
            "treatment_signal_distribution": {},
            "temporal_patterns": {},
            "authority_patterns": {},
            "citation_depth_analysis": {}
        }
        
        # Node type distribution
        node_types = {}
        for node_id in network.nodes():
            node_type = network.nodes[node_id].get('node_type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        patterns["node_type_distribution"] = node_types
        
        # Edge type and treatment signal distribution
        edge_types = {}
        treatment_signals = {}
        
        for source, target, edge_data in network.edges(data=True):
            edge_type = edge_data.get('edge_type', 'unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
            
            treatment_signal = edge_data.get('treatment_signal')
            if treatment_signal:
                signal_str = treatment_signal.value if hasattr(treatment_signal, 'value') else str(treatment_signal)
                treatment_signals[signal_str] = treatment_signals.get(signal_str, 0) + 1
        
        patterns["edge_type_distribution"] = edge_types
        patterns["treatment_signal_distribution"] = treatment_signals
        
        # Authority patterns (most cited, most influential)
        authority_rankings = []
        for node_id in network.nodes():
            node_data = network.nodes[node_id]
            authority_rankings.append((
                node_id,
                node_data.get('in_degree', 0),
                node_data.get('authority_score', 0.0),
                node_data.get('pagerank', 0.0)
            ))
        
        authority_rankings.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
        patterns["authority_patterns"] = {
            "most_cited": authority_rankings[:5],
            "highest_authority": sorted(authority_rankings, key=lambda x: x[2], reverse=True)[:5],
            "highest_pagerank": sorted(authority_rankings, key=lambda x: x[3], reverse=True)[:5]
        }
        
        # Citation depth analysis
        try:
            # Calculate shortest paths from all nodes
            path_lengths = []
            for source in network.nodes():
                for target in network.nodes():
                    if source != target:
                        try:
                            length = nx.shortest_path_length(network, source, target)
                            path_lengths.append(length)
                        except nx.NetworkXNoPath:
                            continue
            
            if path_lengths:
                patterns["citation_depth_analysis"] = {
                    "average_path_length": np.mean(path_lengths),
                    "max_path_length": max(path_lengths),
                    "path_length_distribution": {
                        i: path_lengths.count(i) for i in range(1, max(path_lengths) + 1)
                    }
                }
        except Exception as e:
            self.logger.warning(f"Failed to analyze citation depth: {e}")
        
        return patterns
    
    async def _find_key_citation_paths(self, network: nx.DiGraph, center_node_id: str) -> List[NetworkPath]:
        """Find key citation paths in the network."""
        paths = []
        
        try:
            # Find paths from center node to high-authority nodes
            high_authority_nodes = sorted(
                network.nodes(),
                key=lambda x: network.nodes[x].get('authority_score', 0.0),
                reverse=True
            )[:5]
            
            for target_node in high_authority_nodes:
                if target_node != center_node_id:
                    try:
                        # Find shortest path
                        path_nodes = nx.shortest_path(network, center_node_id, target_node)
                        if len(path_nodes) > 1:
                            
                            # Calculate path strength (average edge weights)
                            path_strength = 1.0
                            for i in range(len(path_nodes) - 1):
                                edge_data = network.edges.get((path_nodes[i], path_nodes[i+1]), {})
                                weight = edge_data.get('weight', 1.0)
                                path_strength *= weight
                            
                            path_strength = path_strength ** (1.0 / (len(path_nodes) - 1))  # Geometric mean
                            
                            # Create path description
                            path_description = f"Path from {network.nodes[center_node_id].get('title', 'center')} to {network.nodes[target_node].get('title', 'target')}"
                            
                            path = NetworkPath(
                                source_id=center_node_id,
                                target_id=target_node,
                                path_nodes=path_nodes,
                                path_length=len(path_nodes) - 1,
                                path_strength=path_strength,
                                path_description=path_description
                            )
                            
                            paths.append(path)
                    
                    except nx.NetworkXNoPath:
                        continue
            
            # Find paths to important nodes in reverse direction
            for source_node in high_authority_nodes:
                if source_node != center_node_id:
                    try:
                        path_nodes = nx.shortest_path(network, source_node, center_node_id)
                        if len(path_nodes) > 1:
                            
                            path_strength = 1.0
                            for i in range(len(path_nodes) - 1):
                                edge_data = network.edges.get((path_nodes[i], path_nodes[i+1]), {})
                                weight = edge_data.get('weight', 1.0)
                                path_strength *= weight
                            
                            path_strength = path_strength ** (1.0 / (len(path_nodes) - 1))
                            
                            path_description = f"Authority path from {network.nodes[source_node].get('title', 'source')} to {network.nodes[center_node_id].get('title', 'center')}"
                            
                            path = NetworkPath(
                                source_id=source_node,
                                target_id=center_node_id,
                                path_nodes=path_nodes,
                                path_length=len(path_nodes) - 1,
                                path_strength=path_strength,
                                path_description=path_description
                            )
                            
                            paths.append(path)
                    
                    except nx.NetworkXNoPath:
                        continue
            
            # Sort paths by importance (shorter length, higher strength)
            paths.sort(key=lambda x: (-x.path_strength, x.path_length))
            
        except Exception as e:
            self.logger.warning(f"Failed to find key citation paths: {e}")
        
        return paths[:10]  # Return top 10 paths
    
    async def _generate_network_insights(self, 
                                       network: nx.DiGraph, 
                                       clusters: List[NetworkCluster],
                                       patterns: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Generate insights and warnings from network analysis."""
        insights = []
        warnings = []
        
        # Network size insights
        node_count = len(network.nodes())
        edge_count = len(network.edges())
        
        if node_count > 100:
            insights.append(f"📊 Extensive citation network with {node_count} authorities and {edge_count} connections")
        elif node_count > 20:
            insights.append(f"📊 Moderate citation network with {node_count} authorities and {edge_count} connections")
        else:
            insights.append(f"📊 Compact citation network with {node_count} authorities and {edge_count} connections")
        
        # Authority insights
        authority_patterns = patterns.get("authority_patterns", {})
        most_cited = authority_patterns.get("most_cited", [])
        
        if most_cited:
            top_authority = most_cited[0]
            node_title = network.nodes[top_authority[0]].get('title', 'Unknown')
            insights.append(f"⚖️ Most cited authority: {node_title} ({top_authority[1]} citations)")
        
        # Treatment signal insights
        treatment_signals = patterns.get("treatment_signal_distribution", {})
        if treatment_signals:
            dominant_signal = max(treatment_signals.items(), key=lambda x: x[1])
            total_treatments = sum(treatment_signals.values())
            percentage = (dominant_signal[1] / total_treatments) * 100
            insights.append(f"📈 Dominant treatment signal: {dominant_signal[0]} ({percentage:.1f}% of treatments)")
        
        # Cluster insights
        if clusters:
            largest_cluster = max(clusters, key=lambda x: len(x.nodes))
            insights.append(f"🎯 Largest thematic cluster: {largest_cluster.description} ({len(largest_cluster.nodes)} cases)")
            
            high_coherence_clusters = [c for c in clusters if c.coherence_score > 0.7]
            if high_coherence_clusters:
                insights.append(f"🔍 {len(high_coherence_clusters)} highly coherent cluster(s) identified")
        
        # Network structure insights
        try:
            density = nx.density(network)
            if density > 0.3:
                insights.append("🕸️ Highly interconnected citation network")
            elif density < 0.1:
                warnings.append("⚠️ Sparse citation network - may indicate isolated authorities")
        except:
            pass
        
        # Warning for negative treatment
        negative_signals = ['overruled', 'questioned', 'criticized']
        negative_count = sum(treatment_signals.get(signal, 0) for signal in negative_signals)
        total_treatments = sum(treatment_signals.values())
        
        if total_treatments > 0 and (negative_count / total_treatments) > 0.3:
            warnings.append(f"⚠️ High proportion of negative treatment signals ({negative_count}/{total_treatments})")
        
        # Warning for outdated authorities
        current_year = datetime.now().year
        old_authorities = 0
        for node_id in network.nodes():
            node_data = network.nodes[node_id]
            decision_date = node_data.get('decision_date')
            if decision_date and current_year - decision_date.year > 20:
                old_authorities += 1
        
        if old_authorities > node_count * 0.5:
            warnings.append(f"📅 Many authorities are over 20 years old ({old_authorities}/{node_count})")
        
        return insights, warnings
    
    async def _create_network_analysis(self, 
                                     network: nx.DiGraph,
                                     center_node_id: str,
                                     clusters: List[NetworkCluster],
                                     patterns: Dict[str, Any],
                                     key_paths: List[NetworkPath],
                                     insights: List[str],
                                     warnings: List[str]) -> NetworkAnalysis:
        """Create comprehensive network analysis result."""
        
        # Convert network to our data structures
        nodes = {}
        for node_id, node_data in network.nodes(data=True):
            node = NetworkNode(
                node_id=node_id,
                node_type=NodeType(node_data.get('node_type', NodeType.CASE.value)),
                title=node_data.get('title', ''),
                citation=node_data.get('citation', ''),
                court=node_data.get('court'),
                jurisdiction=node_data.get('jurisdiction'),
                decision_date=node_data.get('decision_date'),
                in_degree=node_data.get('in_degree', 0),
                out_degree=node_data.get('out_degree', 0),
                betweenness_centrality=node_data.get('betweenness_centrality', 0.0),
                closeness_centrality=node_data.get('closeness_centrality', 0.0),
                pagerank=node_data.get('pagerank', 0.0),
                authority_score=node_data.get('authority_score', 0.0),
                practice_areas=node_data.get('practice_areas', []),
                key_legal_concepts=node_data.get('key_legal_concepts', []),
                size=node_data.get('size', 1.0),
                color=node_data.get('color', '#1f77b4'),
                label=node_data.get('label', '')
            )
            nodes[node_id] = node
        
        # Convert edges
        edges = []
        for source, target, edge_data in network.edges(data=True):
            edge = NetworkEdge(
                source_id=source,
                target_id=target,
                edge_type=EdgeType(edge_data.get('edge_type', EdgeType.CITES.value)),
                treatment_signal=edge_data.get('treatment_signal'),
                page_references=edge_data.get('page_references', []),
                context_snippet=edge_data.get('context_snippet'),
                citation_strength=edge_data.get('citation_strength', 1.0),
                citation_date=edge_data.get('citation_date'),
                weight=edge_data.get('weight', 1.0),
                color=edge_data.get('color', '#999999'),
                style=edge_data.get('style', 'solid')
            )
            edges.append(edge)
        
        # Calculate network-level metrics
        try:
            density = nx.density(network)
            if nx.is_connected(network.to_undirected()):
                avg_path_length = nx.average_shortest_path_length(network.to_undirected())
                clustering_coeff = nx.average_clustering(network.to_undirected())
            else:
                avg_path_length = 0.0
                clustering_coeff = 0.0
        except:
            density = 0.0
            avg_path_length = 0.0
            clustering_coeff = 0.0
        
        # Extract rankings
        most_cited = [(node_id, nodes[node_id].in_degree) for node_id in nodes.keys()]
        most_cited.sort(key=lambda x: x[1], reverse=True)
        
        most_influential = [(node_id, nodes[node_id].pagerank) for node_id in nodes.keys()]
        most_influential.sort(key=lambda x: x[1], reverse=True)
        
        authority_rankings = [(node_id, nodes[node_id].authority_score) for node_id in nodes.keys()]
        authority_rankings.sort(key=lambda x: x[1], reverse=True)
        
        return NetworkAnalysis(
            network_id=f"network_{center_node_id}_{int(datetime.now().timestamp())}",
            center_node_id=center_node_id,
            analysis_date=datetime.now(),
            total_nodes=len(nodes),
            total_edges=len(edges),
            network_density=density,
            average_path_length=avg_path_length,
            clustering_coefficient=clustering_coeff,
            nodes=nodes,
            edges=edges,
            most_cited_cases=most_cited[:10],
            most_influential_cases=most_influential[:10],
            authority_rankings=authority_rankings[:10],
            clusters=clusters,
            citation_patterns=patterns,
            key_paths=key_paths,
            insights=insights,
            warnings=warnings
        )
    
    async def find_citation_bridges(self, 
                                  document1: UnifiedDocument, 
                                  document2: UnifiedDocument,
                                  max_depth: int = 3) -> List[NetworkPath]:
        """Find citation paths that bridge two documents."""
        
        # Build a focused network around both documents
        network = nx.DiGraph()
        
        # Add both documents as starting points
        node1 = await self._create_network_node(document1)
        node2 = await self._create_network_node(document2)
        
        network.add_node(document1.id, **node1.__dict__)
        network.add_node(document2.id, **node2.__dict__)
        
        # Expand network from both documents
        await self._expand_network_bfs(network, document1.id, max_depth, 200)
        await self._expand_network_bfs(network, document2.id, max_depth, 200)
        
        # Find all paths between the documents
        bridge_paths = []
        
        try:
            # Direct paths from doc1 to doc2
            try:
                paths = list(nx.all_shortest_paths(network, document1.id, document2.id))
                for path in paths[:5]:  # Limit to 5 paths
                    path_strength = 1.0  # Calculate based on edge weights
                    bridge_path = NetworkPath(
                        source_id=document1.id,
                        target_id=document2.id,
                        path_nodes=path,
                        path_length=len(path) - 1,
                        path_strength=path_strength,
                        path_description=f"Citation bridge from {document1.title} to {document2.title}"
                    )
                    bridge_paths.append(bridge_path)
            except nx.NetworkXNoPath:
                pass
            
            # Reverse paths from doc2 to doc1
            try:
                paths = list(nx.all_shortest_paths(network, document2.id, document1.id))
                for path in paths[:5]:  # Limit to 5 paths
                    path_strength = 1.0  # Calculate based on edge weights
                    bridge_path = NetworkPath(
                        source_id=document2.id,
                        target_id=document1.id,
                        path_nodes=path,
                        path_length=len(path) - 1,
                        path_strength=path_strength,
                        path_description=f"Citation bridge from {document2.title} to {document1.title}"
                    )
                    bridge_paths.append(bridge_path)
            except nx.NetworkXNoPath:
                pass
        
        except Exception as e:
            self.logger.error(f"Failed to find citation bridges: {e}")
        
        return bridge_paths
    
    async def analyze_citation_influence(self, document: UnifiedDocument) -> Dict[str, Any]:
        """Analyze the citation influence of a document."""
        
        # Build network around the document
        analysis = await self.build_citation_network(
            document, NetworkScope.EXTENDED, max_depth=2, max_nodes=100
        )
        
        center_node = analysis.nodes[document.id]
        
        influence_analysis = {
            "document_id": document.id,
            "document_title": document.title,
            "analysis_date": datetime.now().isoformat(),
            
            # Direct influence metrics
            "citation_count": center_node.in_degree,
            "citations_made": center_node.out_degree,
            "authority_score": center_node.authority_score,
            "pagerank_score": center_node.pagerank,
            
            # Network position
            "betweenness_centrality": center_node.betweenness_centrality,
            "closeness_centrality": center_node.closeness_centrality,
            
            # Influence classification
            "influence_category": self._classify_influence_level(center_node),
            
            # Citation quality
            "high_authority_citations": 0,  # Would calculate based on citing cases' authority
            "recent_citations": 0,          # Would calculate based on recent citations
            
            # Network effects
            "total_network_reach": analysis.total_nodes,
            "network_density": analysis.network_density,
            
            # Recommendations
            "influence_insights": self._generate_influence_insights(center_node, analysis)
        }
        
        return influence_analysis
    
    def _classify_influence_level(self, node: NetworkNode) -> str:
        """Classify the influence level of a document."""
        authority_score = node.authority_score
        citation_count = node.in_degree
        
        if authority_score > 0.8 and citation_count > 50:
            return "Highly Influential"
        elif authority_score > 0.6 and citation_count > 20:
            return "Moderately Influential" 
        elif authority_score > 0.4 and citation_count > 10:
            return "Somewhat Influential"
        elif citation_count > 5:
            return "Limited Influence"
        else:
            return "Minimal Influence"
    
    def _generate_influence_insights(self, node: NetworkNode, analysis: NetworkAnalysis) -> List[str]:
        """Generate insights about a document's influence."""
        insights = []
        
        # Citation volume insights
        if node.in_degree > 20:
            insights.append(f"Frequently cited with {node.in_degree} citations")
        elif node.in_degree < 3:
            insights.append("Limited citation history")
        
        # Authority insights
        if node.authority_score > 0.7:
            insights.append("High authority score indicates strong precedential value")
        elif node.authority_score < 0.3:
            insights.append("Low authority score suggests limited precedential impact")
        
        # Network position insights
        if node.betweenness_centrality > 0.1:
            insights.append("Central position in citation network - serves as important bridge")
        
        # Practice area insights
        if node.practice_areas:
            insights.append(f"Primary influence in: {', '.join(node.practice_areas[:3])}")
        
        return insights


# Helper functions
async def create_citation_network(document: UnifiedDocument) -> NetworkAnalysis:
    """Helper function to create citation network for a document."""
    mapper = CitationNetworkMapper()
    return await mapper.build_citation_network(document)

async def find_citation_connections(doc1: UnifiedDocument, doc2: UnifiedDocument) -> List[NetworkPath]:
    """Helper function to find citation connections between two documents."""
    mapper = CitationNetworkMapper()
    return await mapper.find_citation_bridges(doc1, doc2)