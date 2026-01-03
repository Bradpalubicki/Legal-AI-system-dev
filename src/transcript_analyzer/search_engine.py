"""
Advanced search engine with legal-specific search capabilities, semantic search, and citation analysis.
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
import json
import asyncio
from collections import defaultdict, Counter
import math

from ..shared.utils.ai_client import AIClient
from .transcript_database import TranscriptDatabase, SearchQuery, SearchResults, SearchType, SearchScope


@dataclass
class LegalSearchFilter:
    """Advanced legal-specific search filters."""
    objection_types: List[str] = field(default_factory=list)
    ruling_types: List[str] = field(default_factory=list)
    evidence_types: List[str] = field(default_factory=list)
    citation_types: List[str] = field(default_factory=list)
    legal_categories: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.0
    importance_levels: List[str] = field(default_factory=list)


@dataclass
class SemanticQuery:
    """Semantic search query using AI embeddings."""
    query_text: str
    similarity_threshold: float = 0.7
    max_results: int = 50
    include_related_concepts: bool = True
    expand_legal_terms: bool = True


@dataclass
class CitationQuery:
    """Legal citation search query."""
    citation_text: str
    citation_types: List[str] = field(default_factory=list)  # case, statute, regulation, etc.
    jurisdiction: Optional[str] = None
    court_level: Optional[str] = None
    date_range: Optional[Tuple[datetime, datetime]] = None


class LegalSearchEngine:
    """Advanced search engine with legal-specific capabilities."""
    
    def __init__(self, transcript_db: TranscriptDatabase):
        self.transcript_db = transcript_db
        self.ai_client = AIClient()
        
        # Legal terminology and patterns
        self.legal_concepts = {
            'objections': {
                'hearsay': ['hearsay', 'hear say', 'out of court statement'],
                'relevance': ['relevance', 'relevant', 'irrelevant', 'not relevant'],
                'foundation': ['foundation', 'lack of foundation', 'no foundation'],
                'leading': ['leading', 'leading question', 'leading the witness'],
                'speculation': ['speculation', 'speculative', 'calls for speculation'],
                'argumentative': ['argumentative', 'arguing with witness'],
                'compound': ['compound question', 'multiple questions'],
                'assumes_facts': ['assumes facts not in evidence', 'assumes facts'],
                'best_evidence': ['best evidence', 'original document rule'],
                'privilege': ['privilege', 'privileged', 'attorney-client privilege']
            },
            'evidence': {
                'exhibit': ['exhibit', 'marked', 'identified', 'admitted'],
                'authentication': ['authentication', 'authenticate', 'foundation'],
                'chain_of_custody': ['chain of custody', 'custody', 'possession'],
                'expert_testimony': ['expert', 'opinion', 'qualified', 'expertise'],
                'character_evidence': ['character', 'reputation', 'propensity'],
                'prior_bad_acts': ['prior bad acts', '404(b)', 'other crimes']
            },
            'procedure': {
                'motion': ['motion', 'move', 'request'],
                'ruling': ['ruling', 'rule', 'order', 'direct'],
                'objection': ['objection', 'object', 'sustained', 'overruled'],
                'sidebar': ['sidebar', 'approach', 'bench conference'],
                'recess': ['recess', 'break', 'adjourn', 'suspend'],
                'jury_instruction': ['jury instruction', 'instruct the jury', 'charge']
            },
            'testimony': {
                'direct': ['direct examination', 'direct', 'questions by'],
                'cross': ['cross examination', 'cross', 'cross-examine'],
                'redirect': ['redirect', 'redirect examination'],
                'recross': ['recross', 'recross examination'],
                'impeachment': ['impeach', 'impeachment', 'prior inconsistent'],
                'rehabilitation': ['rehabilitation', 'rehabilitate', 'redirect']
            }
        }
        
        # Citation patterns
        self.citation_patterns = {
            'case_citation': [
                r'\b\d+\s+[A-Z]\w*\s+\d+\b',  # Volume Reporter Page
                r'\b\d+\s+[A-Z]\w*\s*\d*d\s+\d+\b',  # Reporter with edition
                r'\b\d+\s+U\.S\.\s+\d+\b',  # U.S. Reports
                r'\b\d+\s+S\.\s*Ct\.\s+\d+\b',  # Supreme Court Reporter
                r'\b\d+\s+F\.\s*\d*d\s+\d+\b'  # Federal Reporter
            ],
            'statute': [
                r'\b\d+\s+U\.S\.C\.\s*§?\s*\d+\b',  # United States Code
                r'\b\d+\s+C\.F\.R\.\s*§?\s*\d+\b',  # Code of Federal Regulations
                r'\bRule\s+\d+\b',  # Federal Rules
                r'\bFed\.\s*R\.\s*\w+\.\s*\d+\b'  # Federal Rules abbreviated
            ],
            'constitutional': [
                r'\bU\.S\.\s*Const\.\s*[Aa]mend\.\s*[IVXLCDM]+\b',
                r'\bU\.S\.\s*Const\.\s*[Aa]rt\.\s*[IVXLCDM]+\b',
                r'\bConstitution\b'
            ]
        }

    async def advanced_legal_search(
        self, 
        query: SearchQuery, 
        legal_filters: Optional[LegalSearchFilter] = None
    ) -> SearchResults:
        """Perform advanced legal search with specialized filters."""
        try:
            # Expand query with legal terms
            expanded_query = await self._expand_legal_query(query)
            
            # Perform base search
            results = await self.transcript_db.search_transcripts(expanded_query)
            
            # Apply legal filters
            if legal_filters:
                results = await self._apply_legal_filters(results, legal_filters)
            
            # Enhance results with legal analysis
            results = await self._enhance_with_legal_analysis(results)
            
            return results
            
        except Exception as e:
            print(f"Error in advanced legal search: {e}")
            return SearchResults(
                query=query,
                total_matches=0,
                execution_time=0.0,
                matches=[]
            )

    async def semantic_search(self, semantic_query: SemanticQuery) -> SearchResults:
        """Perform semantic search using AI embeddings."""
        try:
            # Get semantic embeddings for query
            query_embedding = await self._get_text_embedding(semantic_query.query_text)
            
            if not query_embedding:
                # Fallback to traditional search
                fallback_query = SearchQuery(
                    query_text=semantic_query.query_text,
                    search_type=SearchType.FULL_TEXT,
                    max_results=semantic_query.max_results
                )
                return await self.transcript_db.search_transcripts(fallback_query)
            
            # Get candidate segments using traditional search first
            candidate_query = SearchQuery(
                query_text=semantic_query.query_text,
                search_type=SearchType.FULL_TEXT,
                max_results=semantic_query.max_results * 3  # Get more candidates
            )
            
            candidates = await self.transcript_db.search_transcripts(candidate_query)
            
            # Score candidates using semantic similarity
            semantic_matches = []
            
            for match in candidates.matches:
                # Get embedding for segment text
                segment_embedding = await self._get_text_embedding(match.matched_text)
                
                if segment_embedding:
                    similarity = self._calculate_cosine_similarity(query_embedding, segment_embedding)
                    
                    if similarity >= semantic_query.similarity_threshold:
                        # Update relevance score with semantic similarity
                        match.relevance_score = similarity
                        semantic_matches.append(match)
            
            # Sort by semantic similarity
            semantic_matches.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Limit results
            semantic_matches = semantic_matches[:semantic_query.max_results]
            
            # Enhance with related concepts if requested
            if semantic_query.include_related_concepts:
                semantic_matches = await self._add_related_concepts(semantic_matches, semantic_query)
            
            return SearchResults(
                query=candidates.query,
                total_matches=len(semantic_matches),
                execution_time=candidates.execution_time,
                matches=semantic_matches,
                facets=candidates.facets,
                suggestions=candidates.suggestions,
                related_queries=await self._generate_semantic_related_queries(semantic_query.query_text)
            )
            
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return SearchResults(
                query=SearchQuery(query_text=semantic_query.query_text),
                total_matches=0,
                execution_time=0.0,
                matches=[]
            )

    async def citation_search(self, citation_query: CitationQuery) -> SearchResults:
        """Search for legal citations within transcripts."""
        try:
            # Extract and normalize citations
            citations = self._extract_citations(citation_query.citation_text)
            
            search_results = SearchResults(
                query=SearchQuery(query_text=citation_query.citation_text),
                total_matches=0,
                execution_time=0.0,
                matches=[]
            )
            
            if not citations:
                return search_results
            
            all_matches = []
            
            for citation in citations:
                # Search for exact citation
                exact_query = SearchQuery(
                    query_text=citation['text'],
                    search_type=SearchType.PHRASE_EXACT,
                    max_results=50
                )
                
                exact_results = await self.transcript_db.search_transcripts(exact_query)
                
                # Search for normalized citation
                if citation['normalized'] != citation['text']:
                    norm_query = SearchQuery(
                        query_text=citation['normalized'],
                        search_type=SearchType.PHRASE_EXACT,
                        max_results=50
                    )
                    
                    norm_results = await self.transcript_db.search_transcripts(norm_query)
                    exact_results.matches.extend(norm_results.matches)
                
                # Add citation metadata to matches
                for match in exact_results.matches:
                    match.annotations.append({
                        "type": "citation",
                        "citation_type": citation['type'],
                        "citation_text": citation['text'],
                        "normalized_citation": citation['normalized'],
                        "confidence": citation['confidence']
                    })
                
                all_matches.extend(exact_results.matches)
            
            # Remove duplicates and sort by relevance
            unique_matches = self._deduplicate_matches(all_matches)
            unique_matches.sort(key=lambda x: x.relevance_score, reverse=True)
            
            search_results.matches = unique_matches
            search_results.total_matches = len(unique_matches)
            
            return search_results
            
        except Exception as e:
            print(f"Error in citation search: {e}")
            return SearchResults(
                query=SearchQuery(query_text=citation_query.citation_text),
                total_matches=0,
                execution_time=0.0,
                matches=[]
            )

    async def contextual_search(
        self, 
        query_text: str, 
        context_window: int = 5,
        speaker_context: Optional[str] = None
    ) -> SearchResults:
        """Search with extended context around matches."""
        try:
            # Perform initial search
            base_query = SearchQuery(
                query_text=query_text,
                search_type=SearchType.FULL_TEXT,
                include_context=True,
                max_results=100
            )
            
            if speaker_context:
                base_query.speakers = [speaker_context]
            
            results = await self.transcript_db.search_transcripts(base_query)
            
            # Expand context for each match
            enhanced_matches = []
            
            for match in results.matches:
                enhanced_match = await self._expand_match_context(match, context_window)
                enhanced_matches.append(enhanced_match)
            
            results.matches = enhanced_matches
            return results
            
        except Exception as e:
            print(f"Error in contextual search: {e}")
            return SearchResults(
                query=SearchQuery(query_text=query_text),
                total_matches=0,
                execution_time=0.0,
                matches=[]
            )

    async def multi_term_proximity_search(
        self, 
        terms: List[str], 
        proximity_distance: int = 10,
        require_all_terms: bool = True
    ) -> SearchResults:
        """Search for multiple terms within specified proximity."""
        try:
            if len(terms) < 2:
                return SearchResults(
                    query=SearchQuery(query_text=" ".join(terms)),
                    total_matches=0,
                    execution_time=0.0,
                    matches=[]
                )
            
            # Build proximity query
            if require_all_terms:
                # All terms must be present within proximity
                query_parts = []
                for i in range(len(terms) - 1):
                    query_parts.append(f"({terms[i]} <{proximity_distance}> {terms[i+1]})")
                proximity_query = " & ".join(query_parts)
            else:
                # Any terms within proximity
                query_parts = []
                for i in range(len(terms)):
                    for j in range(i + 1, len(terms)):
                        query_parts.append(f"({terms[i]} <{proximity_distance}> {terms[j]})")
                proximity_query = " | ".join(query_parts)
            
            search_query = SearchQuery(
                query_text=proximity_query,
                search_type=SearchType.PROXIMITY,
                proximity_distance=proximity_distance,
                max_results=100
            )
            
            return await self.transcript_db.search_transcripts(search_query)
            
        except Exception as e:
            print(f"Error in proximity search: {e}")
            return SearchResults(
                query=SearchQuery(query_text=" ".join(terms)),
                total_matches=0,
                execution_time=0.0,
                matches=[]
            )

    async def temporal_search(
        self, 
        query_text: str, 
        time_range: Tuple[float, float],
        session_id: Optional[str] = None
    ) -> SearchResults:
        """Search within specific time range of a session."""
        try:
            search_query = SearchQuery(
                query_text=query_text,
                search_type=SearchType.FULL_TEXT,
                max_results=100
            )
            
            if session_id:
                search_query.session_ids = [session_id]
            
            # Get base results
            results = await self.transcript_db.search_transcripts(search_query)
            
            # Filter by time range
            start_time, end_time = time_range
            filtered_matches = [
                match for match in results.matches
                if match.timestamp is not None and start_time <= match.timestamp <= end_time
            ]
            
            results.matches = filtered_matches
            results.total_matches = len(filtered_matches)
            
            return results
            
        except Exception as e:
            print(f"Error in temporal search: {e}")
            return SearchResults(
                query=SearchQuery(query_text=query_text),
                total_matches=0,
                execution_time=0.0,
                matches=[]
            )

    async def _expand_legal_query(self, query: SearchQuery) -> SearchQuery:
        """Expand query with legal synonyms and related terms."""
        try:
            expanded_terms = []
            original_terms = query.query_text.lower().split()
            
            for term in original_terms:
                expanded_terms.append(term)
                
                # Find related legal terms
                for category, subcategories in self.legal_concepts.items():
                    for subcategory, terms_list in subcategories.items():
                        if term in terms_list:
                            # Add other terms from same subcategory
                            expanded_terms.extend([t for t in terms_list if t != term])
                            break
            
            # Remove duplicates while preserving order
            seen = set()
            unique_terms = []
            for term in expanded_terms:
                if term not in seen:
                    seen.add(term)
                    unique_terms.append(term)
            
            # Update query
            expanded_query = query
            expanded_query.query_text = " OR ".join(unique_terms[:10])  # Limit expansion
            
            return expanded_query
            
        except Exception as e:
            print(f"Error expanding legal query: {e}")
            return query

    async def _apply_legal_filters(
        self, 
        results: SearchResults, 
        filters: LegalSearchFilter
    ) -> SearchResults:
        """Apply legal-specific filters to search results."""
        try:
            filtered_matches = []
            
            for match in results.matches:
                # Check confidence threshold
                if match.relevance_score < filters.confidence_threshold:
                    continue
                
                # Check objection types
                if filters.objection_types:
                    text_lower = match.matched_text.lower()
                    if not any(obj_type.lower() in text_lower for obj_type in filters.objection_types):
                        continue
                
                # Check other filters similarly...
                filtered_matches.append(match)
            
            results.matches = filtered_matches
            results.total_matches = len(filtered_matches)
            
            return results
            
        except Exception as e:
            print(f"Error applying legal filters: {e}")
            return results

    async def _enhance_with_legal_analysis(self, results: SearchResults) -> SearchResults:
        """Enhance search results with legal analysis."""
        try:
            for match in results.matches:
                # Add legal concept detection
                legal_concepts = self._detect_legal_concepts(match.matched_text)
                if legal_concepts:
                    match.annotations.append({
                        "type": "legal_concepts",
                        "concepts": legal_concepts,
                        "confidence": 0.8
                    })
                
                # Add citation detection
                citations = self._extract_citations(match.matched_text)
                if citations:
                    match.annotations.append({
                        "type": "citations",
                        "citations": citations,
                        "confidence": 0.9
                    })
            
            return results
            
        except Exception as e:
            print(f"Error enhancing with legal analysis: {e}")
            return results

    def _detect_legal_concepts(self, text: str) -> List[Dict[str, Any]]:
        """Detect legal concepts in text."""
        concepts = []
        text_lower = text.lower()
        
        for category, subcategories in self.legal_concepts.items():
            for subcategory, terms_list in subcategories.items():
                for term in terms_list:
                    if term.lower() in text_lower:
                        concepts.append({
                            "category": category,
                            "subcategory": subcategory,
                            "term": term,
                            "confidence": 0.8
                        })
        
        return concepts

    def _extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract legal citations from text."""
        citations = []
        
        for citation_type, patterns in self.citation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    citation_text = match.group()
                    citations.append({
                        "text": citation_text,
                        "normalized": self._normalize_citation(citation_text),
                        "type": citation_type,
                        "position": match.span(),
                        "confidence": 0.9
                    })
        
        return citations

    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation format."""
        # Basic normalization - would be more sophisticated in production
        normalized = re.sub(r'\s+', ' ', citation.strip())
        normalized = re.sub(r'\.', '. ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    async def _get_text_embedding(self, text: str) -> Optional[List[float]]:
        """Get text embedding using AI service."""
        try:
            # This would integrate with an embedding service
            # For now, return None to indicate unavailable
            return None
            
        except Exception as e:
            print(f"Error getting text embedding: {e}")
            return None

    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            if len(vec1) != len(vec2):
                return 0.0
            
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(a * a for a in vec2))
            
            if magnitude1 == 0.0 or magnitude2 == 0.0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
            
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return 0.0

    async def _add_related_concepts(self, matches, semantic_query):
        """Add related legal concepts to semantic search results."""
        try:
            # This would use AI to find related concepts
            # Implementation would depend on available AI services
            return matches
            
        except Exception as e:
            print(f"Error adding related concepts: {e}")
            return matches

    async def _generate_semantic_related_queries(self, query_text: str) -> List[str]:
        """Generate semantically related query suggestions."""
        try:
            related_queries = []
            
            # Use AI to generate related queries
            prompt = f"""
            Generate 3-5 related legal search queries for: "{query_text}"
            Focus on legal concepts, synonyms, and related issues.
            Return as a simple list, one query per line.
            """
            
            response = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.3,
                max_tokens=200
            )
            
            related_queries = [
                line.strip() 
                for line in response.strip().split('\n') 
                if line.strip() and not line.startswith('-')
            ][:5]
            
            return related_queries
            
        except Exception as e:
            print(f"Error generating related queries: {e}")
            return []

    def _deduplicate_matches(self, matches):
        """Remove duplicate matches based on segment ID."""
        seen_segments = set()
        unique_matches = []
        
        for match in matches:
            if match.segment_id not in seen_segments:
                seen_segments.add(match.segment_id)
                unique_matches.append(match)
        
        return unique_matches

    async def _expand_match_context(self, match, context_window: int):
        """Expand context around a search match."""
        try:
            # This would query the database for surrounding segments
            # For now, return the match unchanged
            return match
            
        except Exception as e:
            print(f"Error expanding match context: {e}")
            return match

    async def search_across_cases(
        self, 
        query_text: str, 
        case_ids: List[str],
        compare_results: bool = True
    ) -> Dict[str, SearchResults]:
        """Search across multiple cases and optionally compare results."""
        try:
            case_results = {}
            
            for case_id in case_ids:
                case_query = SearchQuery(
                    query_text=query_text,
                    search_type=SearchType.FULL_TEXT,
                    case_ids=[case_id],
                    max_results=50
                )
                
                results = await self.transcript_db.search_transcripts(case_query)
                case_results[case_id] = results
            
            if compare_results:
                case_results['comparison'] = await self._compare_case_results(case_results, query_text)
            
            return case_results
            
        except Exception as e:
            print(f"Error in cross-case search: {e}")
            return {}

    async def _compare_case_results(
        self, 
        case_results: Dict[str, SearchResults], 
        query_text: str
    ) -> Dict[str, Any]:
        """Compare search results across cases."""
        try:
            comparison = {
                "query": query_text,
                "case_match_counts": {},
                "common_patterns": [],
                "unique_patterns": {},
                "speaker_analysis": {}
            }
            
            # Count matches per case
            for case_id, results in case_results.items():
                if case_id != 'comparison':
                    comparison["case_match_counts"][case_id] = results.total_matches
            
            # Analyze speaker patterns across cases
            all_speakers = defaultdict(list)
            for case_id, results in case_results.items():
                if case_id != 'comparison':
                    for match in results.matches:
                        all_speakers[match.speaker].append(case_id)
            
            comparison["speaker_analysis"] = {
                speaker: {
                    "cases": list(set(cases)),
                    "case_count": len(set(cases)),
                    "total_matches": len(cases)
                }
                for speaker, cases in all_speakers.items()
            }
            
            return comparison
            
        except Exception as e:
            print(f"Error comparing case results: {e}")
            return {}

    async def export_advanced_results(
        self, 
        results: SearchResults, 
        include_analysis: bool = True,
        format: str = "json"
    ) -> str:
        """Export advanced search results with legal analysis."""
        try:
            export_data = {
                "query": {
                    "text": results.query.query_text,
                    "type": results.query.search_type.value,
                    "scope": results.query.search_scope.value,
                    "filters": {
                        "case_ids": results.query.case_ids,
                        "speakers": results.query.speakers,
                        "date_range": [
                            results.query.date_range[0].isoformat(),
                            results.query.date_range[1].isoformat()
                        ] if results.query.date_range else None
                    }
                },
                "results": {
                    "total_matches": results.total_matches,
                    "execution_time": results.execution_time,
                    "matches": []
                },
                "facets": results.facets,
                "suggestions": results.suggestions
            }
            
            for match in results.matches:
                match_data = {
                    "segment_id": match.segment_id,
                    "document_id": match.document_id,
                    "relevance_score": match.relevance_score,
                    "speaker": match.speaker,
                    "timestamp": match.timestamp,
                    "text": match.matched_text,
                    "highlighted_text": match.highlighted_text,
                    "page_number": match.page_number,
                    "line_number": match.line_number
                }
                
                if include_analysis:
                    match_data["annotations"] = match.annotations
                    match_data["context"] = {
                        "before": match.context_before,
                        "after": match.context_after
                    }
                
                export_data["results"]["matches"].append(match_data)
            
            if format.lower() == "json":
                return json.dumps(export_data, indent=2, default=str)
            else:
                # Other formats could be implemented
                return json.dumps(export_data, indent=2, default=str)
                
        except Exception as e:
            print(f"Error exporting advanced results: {e}")
            return ""