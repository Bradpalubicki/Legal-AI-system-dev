"""
Search Orchestrator

Comprehensive orchestration engine that coordinates searches across all
legal databases including commercial providers, free sources, and government databases.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from .database_models import (
    DatabaseProvider, UnifiedQuery, UnifiedDocument, UnifiedSearchResult,
    SearchStrategy, DatabaseConfiguration, DatabaseMetrics
)

from .providers.courtlistener_client import CourtListenerClient, CourtListenerCredentials
from .providers.google_scholar_client import GoogleScholarClient
from .providers.justia_client import JustiaClient, JustiaCredentials
from .providers.heinonline_client import HeinOnlineClient, HeinOnlineCredentials
from .providers.government_clients import (
    GovInfoClient, CongressGovClient, SupremeCourtClient, GovernmentCredentials
)

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """
    Unified search orchestrator that coordinates searches across multiple
    legal databases with intelligent provider selection, parallel execution,
    and result fusion.
    """
    
    def __init__(
        self,
        courtlistener_creds: Optional[CourtListenerCredentials] = None,
        justia_creds: Optional[JustiaCredentials] = None,
        heinonline_creds: Optional[HeinOnlineCredentials] = None,
        government_creds: Optional[GovernmentCredentials] = None
    ):
        self.credentials = {
            "courtlistener": courtlistener_creds,
            "justia": justia_creds,
            "heinonline": heinonline_creds,
            "government": government_creds
        }
        
        # Initialize client registry
        self.clients = {}
        self.client_metrics = {}
        
        # Default search strategy
        self.default_strategy = SearchStrategy(
            strategy_id="comprehensive",
            name="Comprehensive Search",
            description="Search across all available legal databases with intelligent prioritization",
            provider_priorities={
                DatabaseProvider.COURTLISTENER: 90,
                DatabaseProvider.GOOGLE_SCHOLAR: 85,
                DatabaseProvider.JUSTIA: 80,
                DatabaseProvider.GOVINFO: 85,
                DatabaseProvider.CONGRESS_GOV: 80,
                DatabaseProvider.SUPREMECOURT_GOV: 95,
                DatabaseProvider.HEINONLINE: 70  # Lower due to cost
            },
            max_providers=8,
            parallel_execution=True,
            fusion_method="weighted_score",
            deduplication_threshold=0.85,
            max_total_results=100,
            min_relevance_score=0.3,
            diversity_weight=0.15,
            prefer_free_sources=True,
            per_provider_timeout_ms=10000,
            total_timeout_ms=30000
        )
        
        logger.info("Search orchestrator initialized")
    
    async def initialize(self):
        """Initialize all database clients"""
        try:
            # Initialize free/public clients
            await self._initialize_public_clients()
            
            # Initialize premium clients if credentials provided
            await self._initialize_premium_clients()
            
            # Initialize government clients
            await self._initialize_government_clients()
            
            logger.info(f"Initialized {len(self.clients)} database clients")
            
        except Exception as e:
            logger.error(f"Error initializing clients: {str(e)}")
            raise
    
    async def close(self):
        """Close all database clients"""
        for provider, client in self.clients.items():
            try:
                await client.close()
            except Exception as e:
                logger.error(f"Error closing {provider} client: {str(e)}")
    
    async def search(
        self,
        query: UnifiedQuery,
        strategy: Optional[SearchStrategy] = None
    ) -> UnifiedSearchResult:
        """
        Execute unified search across multiple databases
        """
        try:
            start_time = datetime.utcnow()
            search_strategy = strategy or self.default_strategy
            
            logger.info(f"Starting unified search: '{query.query_text[:100]}...'")
            logger.info(f"Using strategy: {search_strategy.name}")
            
            # Select providers based on strategy and query
            selected_providers = await self._select_providers(query, search_strategy)
            logger.info(f"Selected providers: {[p.value for p in selected_providers]}")
            
            # Execute searches
            provider_results = await self._execute_searches(
                query, selected_providers, search_strategy
            )
            
            # Fuse and rank results
            unified_result = await self._fuse_results(
                query, provider_results, search_strategy, start_time
            )
            
            # Update metrics
            await self._update_metrics(provider_results, unified_result)
            
            end_time = datetime.utcnow()
            unified_result.search_time_ms = (end_time - start_time).total_seconds() * 1000
            
            logger.info(
                f"Unified search completed: {unified_result.total_results} results "
                f"in {unified_result.search_time_ms:.0f}ms"
            )
            
            return unified_result
            
        except Exception as e:
            logger.error(f"Unified search failed: {str(e)}")
            return UnifiedSearchResult(
                query=query,
                providers_failed=list(self.clients.keys())
            )
    
    async def get_document(
        self,
        provider: DatabaseProvider,
        document_id: str
    ) -> Optional[UnifiedDocument]:
        """Retrieve specific document from a provider"""
        try:
            if provider.value not in self.clients:
                logger.error(f"Provider {provider.value} not available")
                return None
            
            client = self.clients[provider.value]
            return await client.get_document(document_id)
            
        except Exception as e:
            logger.error(f"Document retrieval failed for {provider.value}: {str(e)}")
            return None
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {}
        
        for provider, client in self.clients.items():
            try:
                # Basic health check (would need provider-specific implementation)
                status[provider] = {
                    "available": True,
                    "capabilities": getattr(client, "capabilities", []),
                    "metrics": self.client_metrics.get(provider, {})
                }
            except Exception as e:
                status[provider] = {
                    "available": False,
                    "error": str(e)
                }
        
        return status
    
    async def _initialize_public_clients(self):
        """Initialize free/public database clients"""
        try:
            # CourtListener
            if self.credentials["courtlistener"]:
                courtlistener = CourtListenerClient(self.credentials["courtlistener"])
            else:
                courtlistener = CourtListenerClient()  # Free tier
            await courtlistener.initialize()
            self.clients["courtlistener"] = courtlistener
            
            # Google Scholar
            google_scholar = GoogleScholarClient()
            await google_scholar.initialize()
            self.clients["google_scholar"] = google_scholar
            
            # Justia
            if self.credentials["justia"]:
                justia = JustiaClient(self.credentials["justia"])
            else:
                justia = JustiaClient()  # Free access
            await justia.initialize()
            self.clients["justia"] = justia
            
            logger.info("Public clients initialized")
            
        except Exception as e:
            logger.error(f"Error initializing public clients: {str(e)}")
    
    async def _initialize_premium_clients(self):
        """Initialize premium database clients"""
        try:
            # HeinOnline (if credentials provided)
            if self.credentials["heinonline"]:
                heinonline = HeinOnlineClient(self.credentials["heinonline"])
                await heinonline.initialize()
                self.clients["heinonline"] = heinonline
                logger.info("HeinOnline client initialized")
            
        except Exception as e:
            logger.error(f"Error initializing premium clients: {str(e)}")
    
    async def _initialize_government_clients(self):
        """Initialize government database clients"""
        try:
            gov_creds = self.credentials["government"]
            
            # GovInfo
            govinfo = GovInfoClient(gov_creds)
            await govinfo.initialize()
            self.clients["govinfo"] = govinfo
            
            # Congress.gov
            congress = CongressGovClient(gov_creds)
            await congress.initialize()
            self.clients["congress_gov"] = congress
            
            # Supreme Court
            scotus = SupremeCourtClient()
            await scotus.initialize()
            self.clients["supremecourt_gov"] = scotus
            
            logger.info("Government clients initialized")
            
        except Exception as e:
            logger.error(f"Error initializing government clients: {str(e)}")
    
    async def _select_providers(
        self,
        query: UnifiedQuery,
        strategy: SearchStrategy
    ) -> List[DatabaseProvider]:
        """Select optimal providers based on query and strategy"""
        try:
            available_providers = []
            
            # Map client keys to DatabaseProvider enum
            provider_mapping = {
                "courtlistener": DatabaseProvider.COURTLISTENER,
                "google_scholar": DatabaseProvider.GOOGLE_SCHOLAR,
                "justia": DatabaseProvider.JUSTIA,
                "heinonline": DatabaseProvider.HEINONLINE,
                "govinfo": DatabaseProvider.GOVINFO,
                "congress_gov": DatabaseProvider.CONGRESS_GOV,
                "supremecourt_gov": DatabaseProvider.SUPREMECOURT_GOV
            }
            
            for client_key, provider in provider_mapping.items():
                if client_key in self.clients:
                    available_providers.append(provider)
            
            # Apply query preferences
            if query.preferred_providers:
                # Use preferred providers if specified
                selected = [p for p in query.preferred_providers if p in available_providers]
            else:
                # Use strategy priorities
                provider_scores = []
                for provider in available_providers:
                    if provider in query.exclude_providers:
                        continue
                    
                    base_score = strategy.provider_priorities.get(provider, 50)
                    
                    # Apply query-specific adjustments
                    adjusted_score = self._adjust_provider_score(
                        provider, query, base_score
                    )
                    
                    provider_scores.append((provider, adjusted_score))
                
                # Sort by score and take top providers
                provider_scores.sort(key=lambda x: x[1], reverse=True)
                selected = [p[0] for p in provider_scores[:strategy.max_providers]]
            
            # Filter by free sources if requested
            if query.free_sources_only:
                free_providers = [
                    DatabaseProvider.COURTLISTENER,
                    DatabaseProvider.GOOGLE_SCHOLAR,
                    DatabaseProvider.JUSTIA,
                    DatabaseProvider.GOVINFO,
                    DatabaseProvider.CONGRESS_GOV,
                    DatabaseProvider.SUPREMECOURT_GOV
                ]
                selected = [p for p in selected if p in free_providers]
            
            return selected
            
        except Exception as e:
            logger.error(f"Error selecting providers: {str(e)}")
            return list(available_providers)  # Fallback to all available
    
    def _adjust_provider_score(
        self,
        provider: DatabaseProvider,
        query: UnifiedQuery,
        base_score: int
    ) -> int:
        """Adjust provider score based on query characteristics"""
        try:
            adjusted_score = base_score
            
            # Content type preferences
            if query.content_types:
                content_bonuses = {
                    DatabaseProvider.COURTLISTENER: ["cases", "dockets"],
                    DatabaseProvider.GOOGLE_SCHOLAR: ["cases", "law_reviews"],
                    DatabaseProvider.JUSTIA: ["cases", "statutes"],
                    DatabaseProvider.HEINONLINE: ["law_reviews", "treaties"],
                    DatabaseProvider.GOVINFO: ["regulations", "congressional_materials"],
                    DatabaseProvider.CONGRESS_GOV: ["congressional_materials"],
                    DatabaseProvider.SUPREMECOURT_GOV: ["cases"]
                }
                
                provider_strengths = content_bonuses.get(provider, [])
                query_types = [ct.value for ct in query.content_types]
                
                overlap = len(set(provider_strengths) & set(query_types))
                adjusted_score += overlap * 10
            
            # Jurisdiction preferences
            if query.jurisdictions:
                if provider == DatabaseProvider.SUPREMECOURT_GOV and "federal" in [j.lower() for j in query.jurisdictions]:
                    adjusted_score += 20
                elif provider in [DatabaseProvider.GOVINFO, DatabaseProvider.CONGRESS_GOV] and "federal" in [j.lower() for j in query.jurisdictions]:
                    adjusted_score += 15
            
            # Date preferences (recent vs historical)
            if query.date_from and query.date_from.year < 2000:
                # Historical documents
                if provider == DatabaseProvider.HEINONLINE:
                    adjusted_score += 15
                elif provider == DatabaseProvider.GOOGLE_SCHOLAR:
                    adjusted_score += 10
            elif query.date_from and query.date_from.year > 2020:
                # Very recent documents
                if provider in [DatabaseProvider.COURTLISTENER, DatabaseProvider.GOVINFO]:
                    adjusted_score += 10
            
            return adjusted_score
            
        except Exception as e:
            logger.error(f"Error adjusting provider score: {str(e)}")
            return base_score
    
    async def _execute_searches(
        self,
        query: UnifiedQuery,
        providers: List[DatabaseProvider],
        strategy: SearchStrategy
    ) -> Dict[str, UnifiedSearchResult]:
        """Execute searches across selected providers"""
        provider_results = {}
        
        if strategy.parallel_execution:
            # Execute searches in parallel
            tasks = []
            for provider in providers:
                task = self._execute_single_search(query, provider, strategy)
                tasks.append((provider, task))
            
            # Wait for all searches with timeout
            timeout = strategy.total_timeout_ms / 1000.0
            
            try:
                completed_tasks = await asyncio.wait_for(
                    asyncio.gather(
                        *[task for _, task in tasks],
                        return_exceptions=True
                    ),
                    timeout=timeout
                )
                
                # Process results
                for i, result in enumerate(completed_tasks):
                    provider = providers[i]
                    if isinstance(result, UnifiedSearchResult):
                        provider_results[provider.value] = result
                    elif isinstance(result, Exception):
                        logger.error(f"Search failed for {provider.value}: {str(result)}")
                        provider_results[provider.value] = UnifiedSearchResult(
                            query=query,
                            providers_failed=[provider]
                        )
                
            except asyncio.TimeoutError:
                logger.warning(f"Search timeout after {timeout}s")
                # Create failed results for all providers
                for provider in providers:
                    if provider.value not in provider_results:
                        provider_results[provider.value] = UnifiedSearchResult(
                            query=query,
                            providers_failed=[provider]
                        )
        
        else:
            # Execute searches sequentially
            for provider in providers:
                try:
                    result = await self._execute_single_search(query, provider, strategy)
                    provider_results[provider.value] = result
                except Exception as e:
                    logger.error(f"Sequential search failed for {provider.value}: {str(e)}")
                    provider_results[provider.value] = UnifiedSearchResult(
                        query=query,
                        providers_failed=[provider]
                    )
        
        return provider_results
    
    async def _execute_single_search(
        self,
        query: UnifiedQuery,
        provider: DatabaseProvider,
        strategy: SearchStrategy
    ) -> UnifiedSearchResult:
        """Execute search for a single provider"""
        try:
            # Map provider to client
            client_mapping = {
                DatabaseProvider.COURTLISTENER: "courtlistener",
                DatabaseProvider.GOOGLE_SCHOLAR: "google_scholar",
                DatabaseProvider.JUSTIA: "justia",
                DatabaseProvider.HEINONLINE: "heinonline",
                DatabaseProvider.GOVINFO: "govinfo",
                DatabaseProvider.CONGRESS_GOV: "congress_gov",
                DatabaseProvider.SUPREMECOURT_GOV: "supremecourt_gov"
            }
            
            client_key = client_mapping.get(provider)
            if not client_key or client_key not in self.clients:
                raise Exception(f"Client not available for {provider.value}")
            
            client = self.clients[client_key]
            
            # Apply per-provider timeout
            timeout = strategy.per_provider_timeout_ms / 1000.0
            
            try:
                # Execute search with timeout
                result = await asyncio.wait_for(
                    client.search(query),
                    timeout=timeout
                )
                
                logger.info(f"{provider.value} search returned {result.total_results} results")
                return result
                
            except asyncio.TimeoutError:
                logger.warning(f"{provider.value} search timed out after {timeout}s")
                return UnifiedSearchResult(
                    query=query,
                    providers_failed=[provider]
                )
            
        except Exception as e:
            logger.error(f"Single search failed for {provider.value}: {str(e)}")
            return UnifiedSearchResult(
                query=query,
                providers_failed=[provider]
            )
    
    async def _fuse_results(
        self,
        query: UnifiedQuery,
        provider_results: Dict[str, UnifiedSearchResult],
        strategy: SearchStrategy,
        start_time: datetime
    ) -> UnifiedSearchResult:
        """Fuse results from multiple providers"""
        try:
            all_documents = []
            successful_providers = []
            failed_providers = []
            provider_result_counts = {}
            provider_response_times = {}
            total_cost = 0.0
            cost_by_provider = {}
            
            # Collect results from all providers
            for provider_key, result in provider_results.items():
                provider_result_counts[provider_key] = result.total_results
                provider_response_times[provider_key] = result.search_time_ms
                total_cost += result.total_cost
                cost_by_provider[provider_key] = result.total_cost
                
                if result.providers_failed:
                    failed_providers.extend(result.providers_failed)
                else:
                    # Map provider key back to enum
                    provider_enum_mapping = {
                        "courtlistener": DatabaseProvider.COURTLISTENER,
                        "google_scholar": DatabaseProvider.GOOGLE_SCHOLAR,
                        "justia": DatabaseProvider.JUSTIA,
                        "heinonline": DatabaseProvider.HEINONLINE,
                        "govinfo": DatabaseProvider.GOVINFO,
                        "congress_gov": DatabaseProvider.CONGRESS_GOV,
                        "supremecourt_gov": DatabaseProvider.SUPREMECOURT_GOV
                    }
                    
                    provider_enum = provider_enum_mapping.get(provider_key)
                    if provider_enum:
                        successful_providers.append(provider_enum)
                    
                    # Add documents with provider weighting
                    for doc in result.documents:
                        # Apply provider-specific weight
                        provider_weight = self._get_provider_weight(provider_key)
                        doc.relevance_score *= provider_weight
                        all_documents.append(doc)
            
            # Apply deduplication
            unique_documents = await self._deduplicate_documents(
                all_documents, strategy.deduplication_threshold
            )
            
            # Apply result fusion and ranking
            ranked_documents = await self._rank_documents(
                unique_documents, query, strategy
            )
            
            # Limit to max results
            final_documents = ranked_documents[:strategy.max_total_results]
            
            # Calculate quality metrics
            avg_relevance = sum(doc.relevance_score for doc in final_documents) / max(len(final_documents), 1)
            
            # Create unified result
            unified_result = UnifiedSearchResult(
                query=query,
                total_results=len(final_documents),
                results_returned=len(final_documents),
                documents=final_documents,
                provider_results=provider_result_counts,
                provider_response_times=provider_response_times,
                providers_searched=successful_providers,
                providers_failed=failed_providers,
                average_relevance=avg_relevance,
                total_cost=total_cost,
                cost_by_provider=cost_by_provider
            )
            
            return unified_result
            
        except Exception as e:
            logger.error(f"Result fusion failed: {str(e)}")
            return UnifiedSearchResult(
                query=query,
                providers_failed=list(provider_results.keys())
            )
    
    def _get_provider_weight(self, provider_key: str) -> float:
        """Get weight multiplier for provider"""
        weights = {
            "courtlistener": 1.0,
            "google_scholar": 0.9,
            "justia": 0.85,
            "heinonline": 1.1,
            "govinfo": 1.05,
            "congress_gov": 1.0,
            "supremecourt_gov": 1.2
        }
        
        return weights.get(provider_key, 1.0)
    
    async def _deduplicate_documents(
        self,
        documents: List[UnifiedDocument],
        threshold: float
    ) -> List[UnifiedDocument]:
        """Remove duplicate documents based on similarity"""
        try:
            if not documents:
                return documents
            
            unique_documents = []
            
            for doc in documents:
                is_duplicate = False
                
                for existing_doc in unique_documents:
                    similarity = self._calculate_similarity(doc, existing_doc)
                    
                    if similarity >= threshold:
                        # Keep the document with higher authority score
                        if doc.authority_score > existing_doc.authority_score:
                            unique_documents.remove(existing_doc)
                            unique_documents.append(doc)
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    unique_documents.append(doc)
            
            logger.info(f"Deduplication: {len(documents)} -> {len(unique_documents)} documents")
            return unique_documents
            
        except Exception as e:
            logger.error(f"Deduplication failed: {str(e)}")
            return documents
    
    def _calculate_similarity(
        self,
        doc1: UnifiedDocument,
        doc2: UnifiedDocument
    ) -> float:
        """Calculate similarity between two documents"""
        try:
            # Title similarity
            title_sim = self._text_similarity(doc1.title, doc2.title)
            
            # Citation similarity
            citation_sim = 0.0
            if doc1.citation and doc2.citation:
                citation_sim = self._text_similarity(doc1.citation, doc2.citation)
            
            # Court and date similarity
            same_court = 0.5 if doc1.court == doc2.court else 0.0
            same_date = 0.5 if doc1.decision_date == doc2.decision_date else 0.0
            
            # Weighted combination
            similarity = (
                title_sim * 0.4 +
                citation_sim * 0.3 +
                same_court * 0.15 +
                same_date * 0.15
            )
            
            return similarity
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {str(e)}")
            return 0.0
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple word overlap"""
        try:
            if not text1 or not text2:
                return 0.0
            
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            
            return intersection / union if union > 0 else 0.0
            
        except:
            return 0.0
    
    async def _rank_documents(
        self,
        documents: List[UnifiedDocument],
        query: UnifiedQuery,
        strategy: SearchStrategy
    ) -> List[UnifiedDocument]:
        """Rank documents using comprehensive scoring"""
        try:
            for doc in documents:
                # Calculate composite score
                doc.composite_score = (
                    doc.relevance_score * 0.4 +
                    doc.authority_score * 0.35 +
                    doc.recency_score * 0.15 +
                    self._calculate_diversity_bonus(doc, documents) * strategy.diversity_weight
                )
            
            # Sort by composite score
            ranked_documents = sorted(
                documents,
                key=lambda d: d.composite_score,
                reverse=True
            )
            
            # Filter by minimum relevance
            filtered_documents = [
                doc for doc in ranked_documents
                if doc.relevance_score >= strategy.min_relevance_score
            ]
            
            return filtered_documents
            
        except Exception as e:
            logger.error(f"Document ranking failed: {str(e)}")
            return documents
    
    def _calculate_diversity_bonus(
        self,
        doc: UnifiedDocument,
        all_documents: List[UnifiedDocument]
    ) -> float:
        """Calculate diversity bonus for document"""
        try:
            # Simple diversity based on provider and jurisdiction
            same_provider_count = sum(
                1 for d in all_documents
                if d.source_provider == doc.source_provider
            )
            
            same_jurisdiction_count = sum(
                1 for d in all_documents
                if d.jurisdiction == doc.jurisdiction
            )
            
            # Lower bonus for over-represented sources
            provider_penalty = min(same_provider_count / len(all_documents), 0.5)
            jurisdiction_penalty = min(same_jurisdiction_count / len(all_documents), 0.3)
            
            diversity_bonus = 1.0 - provider_penalty - jurisdiction_penalty
            return max(diversity_bonus, 0.0)
            
        except:
            return 0.5
    
    async def _update_metrics(
        self,
        provider_results: Dict[str, UnifiedSearchResult],
        unified_result: UnifiedSearchResult
    ):
        """Update performance metrics for providers"""
        try:
            for provider_key, result in provider_results.items():
                if provider_key not in self.client_metrics:
                    self.client_metrics[provider_key] = {
                        "total_searches": 0,
                        "successful_searches": 0,
                        "avg_response_time": 0.0,
                        "total_results": 0,
                        "total_cost": 0.0
                    }
                
                metrics = self.client_metrics[provider_key]
                metrics["total_searches"] += 1
                
                if not result.providers_failed:
                    metrics["successful_searches"] += 1
                    metrics["total_results"] += result.total_results
                    metrics["total_cost"] += result.total_cost
                    
                    # Update average response time
                    prev_avg = metrics["avg_response_time"]
                    new_avg = (
                        (prev_avg * (metrics["successful_searches"] - 1) + result.search_time_ms) /
                        metrics["successful_searches"]
                    )
                    metrics["avg_response_time"] = new_avg
                    
        except Exception as e:
            logger.error(f"Metrics update failed: {str(e)}")


# Add composite_score property to UnifiedDocument
setattr(UnifiedDocument, 'composite_score', 0.0)