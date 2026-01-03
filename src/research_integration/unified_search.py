"""
Unified Search Engine

Comprehensive search orchestration system that combines Westlaw and LexisNexis
APIs to provide unified legal research with result deduplication, ranking, and
intelligent query optimization.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set, Any
from uuid import UUID, uuid4

from .westlaw_client import WestlawClient, WestlawCredentials
from .lexisnexis_client import LexisNexisClient, LexisNexisCredentials
from .models import (
    ResearchQuery, SearchResult, LegalDocument, Citation,
    DocumentType, ResearchProvider, SearchType
)

logger = logging.getLogger(__name__)


class SearchStrategy:
    """Search strategy configuration"""
    def __init__(
        self,
        providers: List[ResearchProvider],
        parallel_execution: bool = True,
        result_fusion_method: str = "round_robin",  # round_robin, interleave, score_based
        deduplication_threshold: float = 0.85,
        max_total_results: int = 100,
        provider_weight: Dict[ResearchProvider, float] = None
    ):
        self.providers = providers
        self.parallel_execution = parallel_execution
        self.result_fusion_method = result_fusion_method
        self.deduplication_threshold = deduplication_threshold
        self.max_total_results = max_total_results
        self.provider_weight = provider_weight or {
            ResearchProvider.WESTLAW: 0.5,
            ResearchProvider.LEXISNEXIS: 0.5
        }


class QueryOptimizer:
    """Intelligent query optimization for different providers"""
    
    @staticmethod
    def optimize_for_westlaw(query: ResearchQuery) -> ResearchQuery:
        """Optimize query for Westlaw-specific features"""
        optimized = query.copy(deep=True)
        
        # Use Key Number search if available
        if "key(" in query.query_text.lower():
            optimized.search_type = SearchType.HEADNOTE
        
        # Optimize boolean queries for Westlaw syntax
        if query.terms_and_connectors:
            optimized.query_text = QueryOptimizer._convert_to_westlaw_boolean(query.query_text)
        
        # Adjust result limits for Westlaw
        optimized.max_results = min(query.max_results, 200)
        
        return optimized
    
    @staticmethod
    def optimize_for_lexisnexis(query: ResearchQuery) -> ResearchQuery:
        """Optimize query for LexisNexis-specific features"""
        optimized = query.copy(deep=True)
        
        # Use topic search if available
        if "topic(" in query.query_text.lower():
            optimized.search_type = SearchType.BOOLEAN
            optimized.terms_and_connectors = True
        
        # Optimize boolean queries for LexisNexis syntax
        if query.terms_and_connectors:
            optimized.query_text = QueryOptimizer._convert_to_lexis_boolean(query.query_text)
        
        # Adjust result limits for LexisNexis
        optimized.max_results = min(query.max_results, 100)
        
        return optimized
    
    @staticmethod
    def _convert_to_westlaw_boolean(query_text: str) -> str:
        """Convert boolean query to Westlaw syntax"""
        # Basic conversions - in production would be more sophisticated
        converted = query_text
        converted = converted.replace(" AND ", " & ")
        converted = converted.replace(" OR ", " | ")
        converted = converted.replace(" NOT ", " % ")
        return converted
    
    @staticmethod
    def _convert_to_lexis_boolean(query_text: str) -> str:
        """Convert boolean query to LexisNexis syntax"""
        # Basic conversions - in production would be more sophisticated
        converted = query_text
        converted = converted.replace(" & ", " AND ")
        converted = converted.replace(" | ", " OR ")
        converted = converted.replace(" % ", " AND NOT ")
        return converted


class ResultFusion:
    """Result fusion and deduplication engine"""
    
    @staticmethod
    def merge_results(
        results: List[SearchResult],
        strategy: SearchStrategy,
        original_query: ResearchQuery
    ) -> SearchResult:
        """Merge search results from multiple providers"""
        
        if not results:
            return SearchResult(query=original_query)
        
        # Collect all documents
        all_documents = []
        for result in results:
            all_documents.extend(result.documents)
        
        # Deduplicate documents
        unique_documents = ResultFusion._deduplicate_documents(
            all_documents, strategy.deduplication_threshold
        )
        
        # Apply result fusion strategy
        if strategy.result_fusion_method == "round_robin":
            merged_documents = ResultFusion._round_robin_merge(results)
        elif strategy.result_fusion_method == "interleave":
            merged_documents = ResultFusion._interleave_merge(results)
        elif strategy.result_fusion_method == "score_based":
            merged_documents = ResultFusion._score_based_merge(unique_documents, strategy)
        else:
            merged_documents = unique_documents
        
        # Limit results
        if len(merged_documents) > strategy.max_total_results:
            merged_documents = merged_documents[:strategy.max_total_results]
        
        # Calculate combined metrics
        total_results = sum(result.total_results for result in results)
        westlaw_results = sum(result.westlaw_results for result in results)
        lexisnexis_results = sum(result.lexisnexis_results for result in results)
        search_time_ms = max(result.search_time_ms for result in results)
        
        # Merge facets
        merged_facets = ResultFusion._merge_facets(results)
        
        return SearchResult(
            query=original_query,
            documents=merged_documents,
            total_results=total_results,
            results_returned=len(merged_documents),
            westlaw_results=westlaw_results,
            lexisnexis_results=lexisnexis_results,
            search_time_ms=search_time_ms,
            providers_searched=[ResearchProvider.BOTH],
            search_strategy="unified_search",
            jurisdiction_facets=merged_facets.get("jurisdiction", {}),
            court_facets=merged_facets.get("court", {}),
            date_facets=merged_facets.get("date", {}),
            document_type_facets=merged_facets.get("document_type", {}),
            has_more_results=any(result.has_more_results for result in results)
        )
    
    @staticmethod
    def _deduplicate_documents(
        documents: List[LegalDocument], 
        threshold: float
    ) -> List[LegalDocument]:
        """Remove duplicate documents based on similarity threshold"""
        unique_documents = []
        processed_citations = set()
        
        for doc in documents:
            # Check for exact citation matches first
            citation_key = doc.citation.normalized_citation.strip().lower()
            if citation_key in processed_citations:
                continue
            
            # Check for similarity with existing documents
            is_duplicate = False
            for existing_doc in unique_documents:
                similarity = ResultFusion._calculate_document_similarity(doc, existing_doc)
                if similarity >= threshold:
                    # Keep the document with higher relevance score
                    if doc.relevance_score and existing_doc.relevance_score:
                        if doc.relevance_score > existing_doc.relevance_score:
                            # Replace existing document
                            idx = unique_documents.index(existing_doc)
                            unique_documents[idx] = doc
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_documents.append(doc)
                processed_citations.add(citation_key)
        
        return unique_documents
    
    @staticmethod
    def _calculate_document_similarity(doc1: LegalDocument, doc2: LegalDocument) -> float:
        """Calculate similarity score between two documents"""
        # Simple similarity calculation - in production would use more sophisticated methods
        
        # Citation similarity (highest weight)
        citation_sim = 0.0
        if doc1.citation.normalized_citation and doc2.citation.normalized_citation:
            if doc1.citation.normalized_citation.lower() == doc2.citation.normalized_citation.lower():
                citation_sim = 1.0
            elif doc1.citation.case_name and doc2.citation.case_name:
                # Compare case names
                if doc1.citation.case_name.lower() == doc2.citation.case_name.lower():
                    citation_sim = 0.9
        
        # Title similarity
        title_sim = 0.0
        if doc1.title and doc2.title:
            if doc1.title.lower() == doc2.title.lower():
                title_sim = 1.0
            else:
                # Simple word overlap
                words1 = set(doc1.title.lower().split())
                words2 = set(doc2.title.lower().split())
                if words1 and words2:
                    title_sim = len(words1.intersection(words2)) / len(words1.union(words2))
        
        # Court and date similarity
        court_sim = 1.0 if doc1.court == doc2.court else 0.0
        date_sim = 1.0 if doc1.decision_date == doc2.decision_date else 0.0
        
        # Weighted average
        weights = {"citation": 0.5, "title": 0.3, "court": 0.1, "date": 0.1}
        similarity = (
            citation_sim * weights["citation"] +
            title_sim * weights["title"] +
            court_sim * weights["court"] +
            date_sim * weights["date"]
        )
        
        return similarity
    
    @staticmethod
    def _round_robin_merge(results: List[SearchResult]) -> List[LegalDocument]:
        """Merge results using round-robin approach"""
        merged = []
        max_length = max(len(result.documents) for result in results) if results else 0
        
        for i in range(max_length):
            for result in results:
                if i < len(result.documents):
                    merged.append(result.documents[i])
        
        return merged
    
    @staticmethod
    def _interleave_merge(results: List[SearchResult]) -> List[LegalDocument]:
        """Merge results by interleaving based on provider weights"""
        if len(results) != 2:
            return ResultFusion._round_robin_merge(results)
        
        westlaw_docs = []
        lexis_docs = []
        
        for result in results:
            if result.westlaw_results > 0:
                westlaw_docs = result.documents
            elif result.lexisnexis_results > 0:
                lexis_docs = result.documents
        
        # Interleave with 1:1 ratio by default
        merged = []
        westlaw_idx = lexis_idx = 0
        
        while westlaw_idx < len(westlaw_docs) or lexis_idx < len(lexis_docs):
            if westlaw_idx < len(westlaw_docs):
                merged.append(westlaw_docs[westlaw_idx])
                westlaw_idx += 1
            
            if lexis_idx < len(lexis_docs):
                merged.append(lexis_docs[lexis_idx])
                lexis_idx += 1
        
        return merged
    
    @staticmethod
    def _score_based_merge(
        documents: List[LegalDocument], 
        strategy: SearchStrategy
    ) -> List[LegalDocument]:
        """Merge results based on relevance scores and provider weights"""
        
        # Adjust scores based on provider weights
        for doc in documents:
            if doc.provider == ResearchProvider.WESTLAW:
                weight = strategy.provider_weight.get(ResearchProvider.WESTLAW, 0.5)
            elif doc.provider == ResearchProvider.LEXISNEXIS:
                weight = strategy.provider_weight.get(ResearchProvider.LEXISNEXIS, 0.5)
            else:
                weight = 1.0
            
            if doc.relevance_score:
                doc.relevance_score *= weight
        
        # Sort by adjusted relevance score
        return sorted(
            documents,
            key=lambda d: d.relevance_score or 0.0,
            reverse=True
        )
    
    @staticmethod
    def _merge_facets(results: List[SearchResult]) -> Dict[str, Dict[str, int]]:
        """Merge facet counts from multiple results"""
        merged_facets = {
            "jurisdiction": {},
            "court": {},
            "date": {},
            "document_type": {}
        }
        
        for result in results:
            # Merge jurisdiction facets
            for key, count in result.jurisdiction_facets.items():
                merged_facets["jurisdiction"][key] = merged_facets["jurisdiction"].get(key, 0) + count
            
            # Merge court facets
            for key, count in result.court_facets.items():
                merged_facets["court"][key] = merged_facets["court"].get(key, 0) + count
            
            # Merge date facets
            for key, count in result.date_facets.items():
                merged_facets["date"][key] = merged_facets["date"].get(key, 0) + count
            
            # Merge document type facets
            for key, count in result.document_type_facets.items():
                merged_facets["document_type"][key] = merged_facets["document_type"].get(key, 0) + count
        
        return merged_facets


class UnifiedSearchEngine:
    """
    Comprehensive unified search engine that orchestrates searches across
    multiple legal research providers with intelligent result fusion.
    """
    
    def __init__(
        self,
        westlaw_credentials: Optional[WestlawCredentials] = None,
        lexisnexis_credentials: Optional[LexisNexisCredentials] = None,
        default_strategy: Optional[SearchStrategy] = None
    ):
        self.westlaw_client = WestlawClient(westlaw_credentials) if westlaw_credentials else None
        self.lexisnexis_client = LexisNexisClient(lexisnexis_credentials) if lexisnexis_credentials else None
        
        self.default_strategy = default_strategy or SearchStrategy(
            providers=[ResearchProvider.BOTH] if (westlaw_credentials and lexisnexis_credentials) else 
                     [ResearchProvider.WESTLAW] if westlaw_credentials else 
                     [ResearchProvider.LEXISNEXIS] if lexisnexis_credentials else [],
            parallel_execution=True,
            result_fusion_method="interleave",
            deduplication_threshold=0.85,
            max_total_results=100
        )
        
        logger.info("Unified Search Engine initialized")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def initialize(self):
        """Initialize all clients"""
        init_tasks = []
        
        if self.westlaw_client:
            init_tasks.append(self.westlaw_client.initialize())
        
        if self.lexisnexis_client:
            init_tasks.append(self.lexisnexis_client.initialize())
        
        if init_tasks:
            await asyncio.gather(*init_tasks, return_exceptions=True)
    
    async def close(self):
        """Close all clients"""
        close_tasks = []
        
        if self.westlaw_client:
            close_tasks.append(self.westlaw_client.close())
        
        if self.lexisnexis_client:
            close_tasks.append(self.lexisnexis_client.close())
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
    
    async def search(
        self,
        query: ResearchQuery,
        strategy: Optional[SearchStrategy] = None
    ) -> SearchResult:
        """Perform unified search across multiple providers"""
        try:
            strategy = strategy or self.default_strategy
            logger.info(f"Starting unified search: {query.query_text[:100]}...")
            
            # Determine which providers to use
            providers_to_search = self._determine_providers(query, strategy)
            
            if not providers_to_search:
                raise Exception("No available research providers")
            
            # Execute searches
            search_results = []
            
            if strategy.parallel_execution:
                # Parallel execution
                search_tasks = []
                
                for provider in providers_to_search:
                    if provider == ResearchProvider.WESTLAW and self.westlaw_client:
                        optimized_query = QueryOptimizer.optimize_for_westlaw(query)
                        search_tasks.append(self._search_westlaw(optimized_query))
                    elif provider == ResearchProvider.LEXISNEXIS and self.lexisnexis_client:
                        optimized_query = QueryOptimizer.optimize_for_lexisnexis(query)
                        search_tasks.append(self._search_lexisnexis(optimized_query))
                
                results = await asyncio.gather(*search_tasks, return_exceptions=True)
                
                # Filter out exceptions
                for result in results:
                    if isinstance(result, SearchResult):
                        search_results.append(result)
                    else:
                        logger.error(f"Search error: {result}")
            
            else:
                # Sequential execution
                for provider in providers_to_search:
                    try:
                        if provider == ResearchProvider.WESTLAW and self.westlaw_client:
                            optimized_query = QueryOptimizer.optimize_for_westlaw(query)
                            result = await self._search_westlaw(optimized_query)
                            search_results.append(result)
                        elif provider == ResearchProvider.LEXISNEXIS and self.lexisnexis_client:
                            optimized_query = QueryOptimizer.optimize_for_lexisnexis(query)
                            result = await self._search_lexisnexis(optimized_query)
                            search_results.append(result)
                    except Exception as e:
                        logger.error(f"Search error for {provider}: {str(e)}")
                        continue
            
            if not search_results:
                raise Exception("All searches failed")
            
            # Merge results
            unified_result = ResultFusion.merge_results(search_results, strategy, query)
            
            logger.info(f"Unified search completed: {unified_result.results_returned} total results")
            return unified_result
            
        except Exception as e:
            logger.error(f"Unified search failed: {str(e)}")
            raise
    
    async def search_cases(
        self,
        query_text: str,
        jurisdiction: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        max_results: int = 50
    ) -> SearchResult:
        """Specialized case law search"""
        query = ResearchQuery(
            query_text=query_text,
            document_types=[DocumentType.CASE],
            jurisdictions=[jurisdiction] if jurisdiction else [],
            max_results=max_results
        )
        
        if date_from:
            query.date_from = datetime.fromisoformat(date_from).date()
        if date_to:
            query.date_to = datetime.fromisoformat(date_to).date()
        
        return await self.search(query)
    
    async def search_statutes(
        self,
        query_text: str,
        jurisdiction: Optional[str] = None,
        max_results: int = 50
    ) -> SearchResult:
        """Specialized statute search"""
        query = ResearchQuery(
            query_text=query_text,
            document_types=[DocumentType.STATUTE],
            jurisdictions=[jurisdiction] if jurisdiction else [],
            max_results=max_results
        )
        
        return await self.search(query)
    
    async def search_secondary_sources(
        self,
        query_text: str,
        practice_area: Optional[str] = None,
        max_results: int = 50
    ) -> SearchResult:
        """Specialized secondary sources search"""
        query = ResearchQuery(
            query_text=query_text,
            document_types=[DocumentType.SECONDARY, DocumentType.TREATISE, DocumentType.JOURNAL],
            practice_area=practice_area,
            max_results=max_results
        )
        
        return await self.search(query)
    
    async def comprehensive_search(
        self,
        query_text: str,
        jurisdiction: Optional[str] = None,
        practice_area: Optional[str] = None
    ) -> Dict[str, SearchResult]:
        """Perform comprehensive search across all document types"""
        try:
            # Create separate queries for different document types
            queries = {
                "cases": ResearchQuery(
                    query_text=query_text,
                    document_types=[DocumentType.CASE],
                    jurisdictions=[jurisdiction] if jurisdiction else [],
                    practice_area=practice_area,
                    max_results=25
                ),
                "statutes": ResearchQuery(
                    query_text=query_text,
                    document_types=[DocumentType.STATUTE],
                    jurisdictions=[jurisdiction] if jurisdiction else [],
                    max_results=25
                ),
                "secondary": ResearchQuery(
                    query_text=query_text,
                    document_types=[DocumentType.SECONDARY, DocumentType.TREATISE, DocumentType.JOURNAL],
                    practice_area=practice_area,
                    max_results=25
                )
            }
            
            # Execute searches in parallel
            search_tasks = [
                self.search(query) for query in queries.values()
            ]
            
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Build results dictionary
            comprehensive_results = {}
            for i, (doc_type, result) in enumerate(zip(queries.keys(), results)):
                if isinstance(result, SearchResult):
                    comprehensive_results[doc_type] = result
                else:
                    logger.error(f"Comprehensive search error for {doc_type}: {result}")
                    comprehensive_results[doc_type] = SearchResult(query=queries[doc_type])
            
            return comprehensive_results
            
        except Exception as e:
            logger.error(f"Comprehensive search failed: {str(e)}")
            raise
    
    async def validate_citation(self, citation: str) -> Dict[ResearchProvider, Any]:
        """Validate citation across all available providers"""
        validation_results = {}
        
        validation_tasks = []
        
        if self.westlaw_client:
            validation_tasks.append(
                self._validate_citation_westlaw(citation)
            )
        
        if self.lexisnexis_client:
            validation_tasks.append(
                self._validate_citation_lexisnexis(citation)
            )
        
        if validation_tasks:
            results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            if self.westlaw_client and len(results) >= 1:
                if isinstance(results[0], Exception):
                    logger.error(f"Westlaw validation error: {results[0]}")
                else:
                    validation_results[ResearchProvider.WESTLAW] = results[0]
            
            lexis_idx = 1 if self.westlaw_client else 0
            if self.lexisnexis_client and len(results) > lexis_idx:
                if isinstance(results[lexis_idx], Exception):
                    logger.error(f"LexisNexis validation error: {results[lexis_idx]}")
                else:
                    validation_results[ResearchProvider.LEXISNEXIS] = results[lexis_idx]
        
        return validation_results
    
    def _determine_providers(
        self,
        query: ResearchQuery,
        strategy: SearchStrategy
    ) -> List[ResearchProvider]:
        """Determine which providers to use for the search"""
        available_providers = []
        
        if self.westlaw_client:
            available_providers.append(ResearchProvider.WESTLAW)
        
        if self.lexisnexis_client:
            available_providers.append(ResearchProvider.LEXISNEXIS)
        
        # Filter based on query preferences
        if query.providers:
            query_providers = []
            for provider in query.providers:
                if provider == ResearchProvider.BOTH:
                    query_providers.extend(available_providers)
                elif provider in available_providers:
                    query_providers.append(provider)
            available_providers = list(set(query_providers))
        
        # Filter based on strategy
        if strategy.providers:
            strategy_providers = []
            for provider in strategy.providers:
                if provider == ResearchProvider.BOTH:
                    strategy_providers.extend(available_providers)
                elif provider in available_providers:
                    strategy_providers.append(provider)
            available_providers = list(set(strategy_providers))
        
        return available_providers
    
    async def _search_westlaw(self, query: ResearchQuery) -> SearchResult:
        """Execute Westlaw search"""
        if not self.westlaw_client:
            raise Exception("Westlaw client not available")
        
        return await self.westlaw_client.search(query)
    
    async def _search_lexisnexis(self, query: ResearchQuery) -> SearchResult:
        """Execute LexisNexis search"""
        if not self.lexisnexis_client:
            raise Exception("LexisNexis client not available")
        
        return await self.lexisnexis_client.search(query)
    
    async def _validate_citation_westlaw(self, citation: str):
        """Validate citation using Westlaw"""
        if not self.westlaw_client:
            raise Exception("Westlaw client not available")
        
        return await self.westlaw_client.validate_citation(citation)
    
    async def _validate_citation_lexisnexis(self, citation: str):
        """Validate citation using LexisNexis"""
        if not self.lexisnexis_client:
            raise Exception("LexisNexis client not available")
        
        return await self.lexisnexis_client.validate_citation(citation)
    
    def get_usage_metrics(self) -> Dict[str, Any]:
        """Get usage metrics from all clients"""
        metrics = {}
        
        if self.westlaw_client:
            metrics["westlaw"] = self.westlaw_client.usage_metrics
        
        if self.lexisnexis_client:
            metrics["lexisnexis"] = self.lexisnexis_client.usage_metrics
        
        return metrics
    
    def get_available_providers(self) -> List[ResearchProvider]:
        """Get list of available providers"""
        providers = []
        
        if self.westlaw_client:
            providers.append(ResearchProvider.WESTLAW)
        
        if self.lexisnexis_client:
            providers.append(ResearchProvider.LEXISNEXIS)
        
        return providers