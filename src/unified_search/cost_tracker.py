"""
Comprehensive cost tracking system for legal research platforms.
Tracks usage, costs, and provides detailed analytics for research optimization.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import uuid

from ..types.unified_types import UnifiedDocument, ContentType


class CostCategory(Enum):
    """Categories of research costs."""
    DATABASE_ACCESS = "database_access"        # Westlaw, Lexis, Bloomberg
    API_CALLS = "api_calls"                   # Per-API call charges
    DOCUMENT_RETRIEVAL = "document_retrieval"  # Per-document fees
    SEARCH_QUERIES = "search_queries"         # Per-search charges
    CITATION_ANALYSIS = "citation_analysis"   # Shepardizing, KeyCite fees
    AI_PROCESSING = "ai_processing"           # AI analysis costs
    STORAGE = "storage"                       # Document storage costs
    BANDWIDTH = "bandwidth"                   # Data transfer costs
    SUBSCRIPTION = "subscription"             # Monthly/annual subscriptions
    THIRD_PARTY = "third_party"              # External service costs


class ResourceType(Enum):
    """Types of research resources."""
    WESTLAW = "westlaw"
    LEXIS = "lexis"
    BLOOMBERG_LAW = "bloomberg_law"
    GOOGLE_SCHOLAR = "google_scholar"
    FASTCASE = "fastcase"
    CASETEXT = "casetext"
    JUSTIA = "justia"
    INTERNAL_SYSTEM = "internal_system"
    AI_SERVICE = "ai_service"
    STORAGE_SERVICE = "storage_service"


class PricingModel(Enum):
    """Pricing models for research resources."""
    FLAT_RATE = "flat_rate"                  # Fixed monthly/annual fee
    PER_SEARCH = "per_search"                 # Cost per search query
    PER_DOCUMENT = "per_document"             # Cost per document accessed
    PER_API_CALL = "per_api_call"            # Cost per API request
    TIERED_USAGE = "tiered_usage"            # Different rates by usage volume
    TIME_BASED = "time_based"                 # Cost per minute/hour
    HYBRID = "hybrid"                         # Combination of models


@dataclass
class CostEvent:
    """Individual cost event record."""
    event_id: str
    timestamp: datetime
    user_id: str
    resource_type: ResourceType
    cost_category: CostCategory
    pricing_model: PricingModel
    
    # Cost details
    base_cost: Decimal
    additional_fees: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    total_cost: Decimal = field(init=False)
    
    # Usage details
    query_text: Optional[str] = None
    document_count: int = 0
    api_calls: int = 0
    processing_time: Optional[float] = None  # seconds
    
    # Context
    matter_id: Optional[str] = None
    client_id: Optional[str] = None
    practice_area: Optional[str] = None
    
    # Efficiency metrics
    results_found: int = 0
    relevant_results: int = 0
    success_rate: float = 0.0
    
    # Metadata
    source_ip: Optional[str] = None
    session_id: Optional[str] = None
    
    def __post_init__(self):
        self.total_cost = self.base_cost + self.additional_fees + self.tax_amount


@dataclass
class ResourcePricing:
    """Pricing configuration for a research resource."""
    resource_type: ResourceType
    pricing_model: PricingModel
    effective_date: datetime
    
    # Pricing tiers
    base_rate: Decimal = Decimal('0.00')
    per_search_rate: Decimal = Decimal('0.00')
    per_document_rate: Decimal = Decimal('0.00')
    per_api_rate: Decimal = Decimal('0.00')
    per_minute_rate: Decimal = Decimal('0.00')
    
    # Volume discounts
    tier_thresholds: List[int] = field(default_factory=list)
    tier_rates: List[Decimal] = field(default_factory=list)
    
    # Subscription details
    monthly_fee: Decimal = Decimal('0.00')
    annual_fee: Decimal = Decimal('0.00')
    included_searches: int = 0
    included_documents: int = 0
    
    # Additional fees
    setup_fee: Decimal = Decimal('0.00')
    overage_multiplier: Decimal = Decimal('1.0')
    tax_rate: Decimal = Decimal('0.00')


@dataclass
class UsageMetrics:
    """Usage metrics for cost analysis."""
    resource_type: ResourceType
    period_start: datetime
    period_end: datetime
    
    # Volume metrics
    total_searches: int = 0
    total_documents: int = 0
    total_api_calls: int = 0
    total_processing_time: float = 0.0
    
    # Cost metrics
    total_cost: Decimal = Decimal('0.00')
    average_cost_per_search: Decimal = Decimal('0.00')
    average_cost_per_document: Decimal = Decimal('0.00')
    
    # Efficiency metrics
    success_rate: float = 0.0
    average_results_per_search: float = 0.0
    cost_per_relevant_result: Decimal = Decimal('0.00')
    
    # User metrics
    unique_users: int = 0
    peak_usage_hour: Optional[int] = None
    usage_distribution: Dict[int, int] = field(default_factory=dict)  # hour -> count


@dataclass
class CostSummary:
    """Summary of costs for a period."""
    period_start: datetime
    period_end: datetime
    
    # Total costs by category
    costs_by_category: Dict[CostCategory, Decimal] = field(default_factory=dict)
    costs_by_resource: Dict[ResourceType, Decimal] = field(default_factory=dict)
    costs_by_user: Dict[str, Decimal] = field(default_factory=dict)
    costs_by_matter: Dict[str, Decimal] = field(default_factory=dict)
    
    # Usage statistics
    total_cost: Decimal = Decimal('0.00')
    total_events: int = 0
    average_cost_per_event: Decimal = Decimal('0.00')
    
    # Trends
    daily_costs: Dict[str, Decimal] = field(default_factory=dict)  # date -> cost
    cost_trend: str = "stable"  # "increasing", "decreasing", "stable", "volatile"


class CostTracker:
    """
    Comprehensive cost tracking system for legal research.
    
    Tracks all research-related costs, analyzes spending patterns,
    and provides detailed cost breakdowns for optimization.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Cost event storage
        self.cost_events: List[CostEvent] = []
        self.pricing_configs: Dict[ResourceType, ResourcePricing] = {}
        
        # Cost tracking state
        self.current_session_costs: Dict[str, List[CostEvent]] = defaultdict(list)
        self.daily_cost_cache: Dict[str, Decimal] = {}
        
        # Configuration
        self.tax_rate = Decimal('0.08')  # 8% default tax rate
        self.currency = "USD"
        self.cost_precision = 4  # Decimal places for cost calculations
        
        # Initialize default pricing
        self._initialize_default_pricing()
    
    def _initialize_default_pricing(self):
        """Initialize default pricing for common resources."""
        
        # Westlaw pricing (example rates)
        self.pricing_configs[ResourceType.WESTLAW] = ResourcePricing(
            resource_type=ResourceType.WESTLAW,
            pricing_model=PricingModel.HYBRID,
            effective_date=datetime.now(),
            monthly_fee=Decimal('500.00'),
            per_search_rate=Decimal('15.00'),
            per_document_rate=Decimal('25.00'),
            included_searches=50,
            included_documents=100,
            overage_multiplier=Decimal('1.5'),
            tax_rate=self.tax_rate
        )
        
        # Lexis pricing
        self.pricing_configs[ResourceType.LEXIS] = ResourcePricing(
            resource_type=ResourceType.LEXIS,
            pricing_model=PricingModel.HYBRID,
            effective_date=datetime.now(),
            monthly_fee=Decimal('450.00'),
            per_search_rate=Decimal('12.00'),
            per_document_rate=Decimal('20.00'),
            included_searches=60,
            included_documents=120,
            overage_multiplier=Decimal('1.4'),
            tax_rate=self.tax_rate
        )
        
        # AI Service pricing
        self.pricing_configs[ResourceType.AI_SERVICE] = ResourcePricing(
            resource_type=ResourceType.AI_SERVICE,
            pricing_model=PricingModel.PER_API_CALL,
            effective_date=datetime.now(),
            per_api_rate=Decimal('0.05'),
            tax_rate=self.tax_rate
        )
        
        # Google Scholar (free with rate limits)
        self.pricing_configs[ResourceType.GOOGLE_SCHOLAR] = ResourcePricing(
            resource_type=ResourceType.GOOGLE_SCHOLAR,
            pricing_model=PricingModel.FLAT_RATE,
            effective_date=datetime.now(),
            base_rate=Decimal('0.00')
        )
    
    async def track_search_cost(self, 
                              user_id: str,
                              resource_type: ResourceType,
                              query_text: str,
                              results_found: int,
                              relevant_results: int,
                              processing_time: float,
                              session_id: Optional[str] = None,
                              matter_id: Optional[str] = None,
                              client_id: Optional[str] = None) -> CostEvent:
        """
        Track cost of a search operation.
        
        Args:
            user_id: User performing the search
            resource_type: Research resource used
            query_text: Search query
            results_found: Total results found
            relevant_results: Number of relevant results
            processing_time: Time taken for search
            session_id: Session identifier
            matter_id: Matter/case identifier
            client_id: Client identifier
            
        Returns:
            CostEvent record
        """
        
        # Calculate cost based on pricing model
        cost_details = await self._calculate_search_cost(
            resource_type, query_text, results_found, processing_time
        )
        
        # Create cost event
        event = CostEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            user_id=user_id,
            resource_type=resource_type,
            cost_category=CostCategory.SEARCH_QUERIES,
            pricing_model=cost_details['pricing_model'],
            base_cost=cost_details['base_cost'],
            additional_fees=cost_details['additional_fees'],
            tax_amount=cost_details['tax_amount'],
            query_text=query_text,
            results_found=results_found,
            relevant_results=relevant_results,
            processing_time=processing_time,
            session_id=session_id,
            matter_id=matter_id,
            client_id=client_id,
            success_rate=relevant_results / max(1, results_found),
            api_calls=1
        )
        
        # Store event
        await self._store_cost_event(event)
        
        self.logger.info(f"Tracked search cost: {event.total_cost} for {resource_type.value}")
        
        return event
    
    async def track_document_access_cost(self,
                                       user_id: str,
                                       resource_type: ResourceType,
                                       document: UnifiedDocument,
                                       access_type: str = "view",
                                       session_id: Optional[str] = None,
                                       matter_id: Optional[str] = None,
                                       client_id: Optional[str] = None) -> CostEvent:
        """Track cost of accessing a document."""
        
        # Calculate document access cost
        cost_details = await self._calculate_document_cost(
            resource_type, document, access_type
        )
        
        # Create cost event
        event = CostEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            user_id=user_id,
            resource_type=resource_type,
            cost_category=CostCategory.DOCUMENT_RETRIEVAL,
            pricing_model=cost_details['pricing_model'],
            base_cost=cost_details['base_cost'],
            additional_fees=cost_details['additional_fees'],
            tax_amount=cost_details['tax_amount'],
            document_count=1,
            session_id=session_id,
            matter_id=matter_id,
            client_id=client_id,
            results_found=1,
            relevant_results=1,
            success_rate=1.0
        )
        
        # Store event
        await self._store_cost_event(event)
        
        self.logger.info(f"Tracked document access cost: {event.total_cost} for {resource_type.value}")
        
        return event
    
    async def track_api_cost(self,
                           user_id: str,
                           resource_type: ResourceType,
                           api_endpoint: str,
                           request_data: Dict[str, Any],
                           response_data: Dict[str, Any],
                           processing_time: float,
                           session_id: Optional[str] = None) -> CostEvent:
        """Track cost of API calls."""
        
        # Calculate API cost
        cost_details = await self._calculate_api_cost(
            resource_type, api_endpoint, request_data, response_data
        )
        
        # Create cost event
        event = CostEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            user_id=user_id,
            resource_type=resource_type,
            cost_category=CostCategory.API_CALLS,
            pricing_model=cost_details['pricing_model'],
            base_cost=cost_details['base_cost'],
            additional_fees=cost_details['additional_fees'],
            tax_amount=cost_details['tax_amount'],
            api_calls=1,
            processing_time=processing_time,
            session_id=session_id,
            query_text=api_endpoint
        )
        
        # Store event
        await self._store_cost_event(event)
        
        return event
    
    async def track_subscription_cost(self,
                                    resource_type: ResourceType,
                                    subscription_period: str,  # "monthly", "annual"
                                    billing_date: datetime,
                                    client_id: Optional[str] = None) -> CostEvent:
        """Track subscription costs."""
        
        pricing = self.pricing_configs.get(resource_type)
        if not pricing:
            raise ValueError(f"No pricing configuration for {resource_type}")
        
        # Calculate subscription cost
        if subscription_period == "monthly":
            base_cost = pricing.monthly_fee
        elif subscription_period == "annual":
            base_cost = pricing.annual_fee
        else:
            raise ValueError(f"Invalid subscription period: {subscription_period}")
        
        tax_amount = base_cost * pricing.tax_rate
        
        # Create cost event
        event = CostEvent(
            event_id=str(uuid.uuid4()),
            timestamp=billing_date,
            user_id="system",
            resource_type=resource_type,
            cost_category=CostCategory.SUBSCRIPTION,
            pricing_model=PricingModel.FLAT_RATE,
            base_cost=base_cost,
            tax_amount=tax_amount,
            client_id=client_id,
            query_text=f"{subscription_period}_subscription"
        )
        
        # Store event
        await self._store_cost_event(event)
        
        return event
    
    async def _calculate_search_cost(self, 
                                   resource_type: ResourceType,
                                   query_text: str,
                                   results_found: int,
                                   processing_time: float) -> Dict[str, Any]:
        """Calculate cost for a search operation."""
        
        pricing = self.pricing_configs.get(resource_type)
        if not pricing:
            return {
                'base_cost': Decimal('0.00'),
                'additional_fees': Decimal('0.00'),
                'tax_amount': Decimal('0.00'),
                'pricing_model': PricingModel.FLAT_RATE
            }
        
        base_cost = Decimal('0.00')
        additional_fees = Decimal('0.00')
        
        if pricing.pricing_model == PricingModel.PER_SEARCH:
            base_cost = pricing.per_search_rate
        elif pricing.pricing_model == PricingModel.TIME_BASED:
            minutes = Decimal(str(processing_time / 60))
            base_cost = pricing.per_minute_rate * minutes
        elif pricing.pricing_model == PricingModel.HYBRID:
            # Check if within included searches
            monthly_usage = await self._get_monthly_usage_count(resource_type, "searches")
            if monthly_usage > pricing.included_searches:
                overage = monthly_usage - pricing.included_searches
                base_cost = pricing.per_search_rate * pricing.overage_multiplier
        elif pricing.pricing_model == PricingModel.TIERED_USAGE:
            # Apply tiered pricing
            base_cost = await self._calculate_tiered_cost(
                resource_type, "searches", pricing.per_search_rate
            )
        
        # Calculate complexity bonus (longer queries cost more)
        if query_text and len(query_text.split()) > 10:
            additional_fees = base_cost * Decimal('0.1')  # 10% complexity bonus
        
        # Calculate tax
        tax_amount = (base_cost + additional_fees) * pricing.tax_rate
        
        return {
            'base_cost': base_cost,
            'additional_fees': additional_fees,
            'tax_amount': tax_amount,
            'pricing_model': pricing.pricing_model
        }
    
    async def _calculate_document_cost(self,
                                     resource_type: ResourceType,
                                     document: UnifiedDocument,
                                     access_type: str) -> Dict[str, Any]:
        """Calculate cost for document access."""
        
        pricing = self.pricing_configs.get(resource_type)
        if not pricing:
            return {
                'base_cost': Decimal('0.00'),
                'additional_fees': Decimal('0.00'),
                'tax_amount': Decimal('0.00'),
                'pricing_model': PricingModel.FLAT_RATE
            }
        
        base_cost = Decimal('0.00')
        additional_fees = Decimal('0.00')
        
        if pricing.pricing_model == PricingModel.PER_DOCUMENT:
            base_cost = pricing.per_document_rate
        elif pricing.pricing_model == PricingModel.HYBRID:
            # Check if within included documents
            monthly_usage = await self._get_monthly_usage_count(resource_type, "documents")
            if monthly_usage > pricing.included_documents:
                base_cost = pricing.per_document_rate * pricing.overage_multiplier
        
        # Premium content surcharge
        if self._is_premium_content(document):
            additional_fees = base_cost * Decimal('0.25')  # 25% premium surcharge
        
        # Access type modifiers
        if access_type in ["download", "export"]:
            additional_fees += base_cost * Decimal('0.15')  # 15% for downloads
        
        tax_amount = (base_cost + additional_fees) * pricing.tax_rate
        
        return {
            'base_cost': base_cost,
            'additional_fees': additional_fees,
            'tax_amount': tax_amount,
            'pricing_model': pricing.pricing_model
        }
    
    async def _calculate_api_cost(self,
                                resource_type: ResourceType,
                                api_endpoint: str,
                                request_data: Dict[str, Any],
                                response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cost for API calls."""
        
        pricing = self.pricing_configs.get(resource_type)
        if not pricing:
            return {
                'base_cost': Decimal('0.00'),
                'additional_fees': Decimal('0.00'),
                'tax_amount': Decimal('0.00'),
                'pricing_model': PricingModel.FLAT_RATE
            }
        
        base_cost = pricing.per_api_rate
        additional_fees = Decimal('0.00')
        
        # Complex API endpoints cost more
        if any(keyword in api_endpoint.lower() for keyword in ['analyze', 'process', 'ai', 'ml']):
            additional_fees = base_cost * Decimal('2.0')  # 2x for complex operations
        
        # Large request/response data
        request_size = len(str(request_data))
        response_size = len(str(response_data))
        total_size = request_size + response_size
        
        if total_size > 10000:  # Large data transfer
            size_surcharge = Decimal(str(total_size / 10000)) * base_cost * Decimal('0.1')
            additional_fees += size_surcharge
        
        tax_amount = (base_cost + additional_fees) * pricing.tax_rate
        
        return {
            'base_cost': base_cost,
            'additional_fees': additional_fees,
            'tax_amount': tax_amount,
            'pricing_model': pricing.pricing_model
        }
    
    async def _calculate_tiered_cost(self,
                                   resource_type: ResourceType,
                                   usage_type: str,
                                   base_rate: Decimal) -> Decimal:
        """Calculate cost using tiered pricing."""
        
        pricing = self.pricing_configs.get(resource_type)
        if not pricing or not pricing.tier_thresholds:
            return base_rate
        
        monthly_usage = await self._get_monthly_usage_count(resource_type, usage_type)
        
        # Find appropriate tier
        for i, threshold in enumerate(pricing.tier_thresholds):
            if monthly_usage <= threshold:
                return pricing.tier_rates[i] if i < len(pricing.tier_rates) else base_rate
        
        # Highest tier
        return pricing.tier_rates[-1] if pricing.tier_rates else base_rate
    
    async def _get_monthly_usage_count(self, resource_type: ResourceType, usage_type: str) -> int:
        """Get monthly usage count for a resource and usage type."""
        
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        
        count = 0
        for event in self.cost_events:
            if (event.timestamp >= month_start and 
                event.resource_type == resource_type):
                
                if usage_type == "searches" and event.cost_category == CostCategory.SEARCH_QUERIES:
                    count += 1
                elif usage_type == "documents" and event.cost_category == CostCategory.DOCUMENT_RETRIEVAL:
                    count += event.document_count
                elif usage_type == "api_calls" and event.cost_category == CostCategory.API_CALLS:
                    count += event.api_calls
        
        return count
    
    def _is_premium_content(self, document: UnifiedDocument) -> bool:
        """Check if document is premium content."""
        
        # Premium indicators
        premium_sources = ["westlaw", "lexis", "bloomberg"]
        premium_types = [ContentType.CASE_LAW, ContentType.STATUTE]
        
        # Check source
        if hasattr(document, 'source'):
            source = getattr(document, 'source', '').lower()
            if any(premium in source for premium in premium_sources):
                return True
        
        # Check content type
        if document.content_type in premium_types:
            return True
        
        # Check length (longer documents might be premium)
        if document.content and len(document.content) > 50000:
            return True
        
        return False
    
    async def _store_cost_event(self, event: CostEvent):
        """Store cost event."""
        
        self.cost_events.append(event)
        
        # Add to session costs if session_id provided
        if event.session_id:
            self.current_session_costs[event.session_id].append(event)
        
        # Update daily cost cache
        date_key = event.timestamp.strftime('%Y-%m-%d')
        if date_key not in self.daily_cost_cache:
            self.daily_cost_cache[date_key] = Decimal('0.00')
        self.daily_cost_cache[date_key] += event.total_cost
    
    async def get_cost_summary(self, 
                             start_date: datetime,
                             end_date: datetime,
                             group_by: Optional[str] = None) -> CostSummary:
        """
        Get cost summary for a date range.
        
        Args:
            start_date: Start of period
            end_date: End of period
            group_by: Optional grouping ("user", "matter", "resource", "category")
            
        Returns:
            CostSummary with detailed breakdown
        """
        
        # Filter events by date range
        period_events = [
            event for event in self.cost_events
            if start_date <= event.timestamp <= end_date
        ]
        
        if not period_events:
            return CostSummary(
                period_start=start_date,
                period_end=end_date,
                total_cost=Decimal('0.00'),
                total_events=0
            )
        
        # Calculate summary statistics
        summary = CostSummary(
            period_start=start_date,
            period_end=end_date,
            total_events=len(period_events)
        )
        
        # Aggregate costs by different dimensions
        for event in period_events:
            summary.total_cost += event.total_cost
            
            # By category
            category = event.cost_category
            if category not in summary.costs_by_category:
                summary.costs_by_category[category] = Decimal('0.00')
            summary.costs_by_category[category] += event.total_cost
            
            # By resource
            resource = event.resource_type
            if resource not in summary.costs_by_resource:
                summary.costs_by_resource[resource] = Decimal('0.00')
            summary.costs_by_resource[resource] += event.total_cost
            
            # By user
            if event.user_id not in summary.costs_by_user:
                summary.costs_by_user[event.user_id] = Decimal('0.00')
            summary.costs_by_user[event.user_id] += event.total_cost
            
            # By matter
            if event.matter_id:
                if event.matter_id not in summary.costs_by_matter:
                    summary.costs_by_matter[event.matter_id] = Decimal('0.00')
                summary.costs_by_matter[event.matter_id] += event.total_cost
            
            # Daily costs
            date_key = event.timestamp.strftime('%Y-%m-%d')
            if date_key not in summary.daily_costs:
                summary.daily_costs[date_key] = Decimal('0.00')
            summary.daily_costs[date_key] += event.total_cost
        
        # Calculate averages
        if summary.total_events > 0:
            summary.average_cost_per_event = summary.total_cost / Decimal(str(summary.total_events))
        
        # Determine cost trend
        summary.cost_trend = await self._analyze_cost_trend(summary.daily_costs)
        
        return summary
    
    async def _analyze_cost_trend(self, daily_costs: Dict[str, Decimal]) -> str:
        """Analyze cost trend from daily costs."""
        
        if len(daily_costs) < 3:
            return "stable"
        
        # Convert to sorted list of values
        sorted_dates = sorted(daily_costs.keys())
        costs = [float(daily_costs[date]) for date in sorted_dates]
        
        # Calculate simple linear trend
        n = len(costs)
        x_values = list(range(n))
        
        # Calculate slope using least squares
        x_mean = sum(x_values) / n
        y_mean = sum(costs) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, costs))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        # Classify trend
        if slope > y_mean * 0.1:  # More than 10% of average daily cost
            return "increasing"
        elif slope < -y_mean * 0.1:
            return "decreasing"
        else:
            # Check for volatility
            variance = sum((cost - y_mean) ** 2 for cost in costs) / n
            std_dev = variance ** 0.5
            
            if std_dev > y_mean * 0.3:  # High variance relative to mean
                return "volatile"
            else:
                return "stable"
    
    async def get_usage_metrics(self,
                              resource_type: ResourceType,
                              start_date: datetime,
                              end_date: datetime) -> UsageMetrics:
        """Get detailed usage metrics for a resource."""
        
        # Filter events
        resource_events = [
            event for event in self.cost_events
            if (event.resource_type == resource_type and 
                start_date <= event.timestamp <= end_date)
        ]
        
        if not resource_events:
            return UsageMetrics(
                resource_type=resource_type,
                period_start=start_date,
                period_end=end_date
            )
        
        # Calculate metrics
        metrics = UsageMetrics(
            resource_type=resource_type,
            period_start=start_date,
            period_end=end_date
        )
        
        # Aggregate usage data
        total_relevant_results = 0
        total_results_found = 0
        unique_users = set()
        hourly_usage = defaultdict(int)
        
        for event in resource_events:
            metrics.total_cost += event.total_cost
            
            if event.cost_category == CostCategory.SEARCH_QUERIES:
                metrics.total_searches += 1
                total_results_found += event.results_found
                total_relevant_results += event.relevant_results
            
            if event.cost_category == CostCategory.DOCUMENT_RETRIEVAL:
                metrics.total_documents += event.document_count
            
            if event.cost_category == CostCategory.API_CALLS:
                metrics.total_api_calls += event.api_calls
            
            if event.processing_time:
                metrics.total_processing_time += event.processing_time
            
            unique_users.add(event.user_id)
            
            # Track hourly usage
            hour = event.timestamp.hour
            hourly_usage[hour] += 1
        
        # Calculate derived metrics
        metrics.unique_users = len(unique_users)
        
        if metrics.total_searches > 0:
            metrics.average_cost_per_search = metrics.total_cost / Decimal(str(metrics.total_searches))
            metrics.average_results_per_search = total_results_found / metrics.total_searches
        
        if metrics.total_documents > 0:
            metrics.average_cost_per_document = metrics.total_cost / Decimal(str(metrics.total_documents))
        
        if total_results_found > 0:
            metrics.success_rate = total_relevant_results / total_results_found
        
        if total_relevant_results > 0:
            metrics.cost_per_relevant_result = metrics.total_cost / Decimal(str(total_relevant_results))
        
        # Find peak usage hour
        if hourly_usage:
            metrics.peak_usage_hour = max(hourly_usage.keys(), key=lambda k: hourly_usage[k])
            metrics.usage_distribution = dict(hourly_usage)
        
        return metrics
    
    async def get_session_cost(self, session_id: str) -> Decimal:
        """Get total cost for a session."""
        
        if session_id not in self.current_session_costs:
            return Decimal('0.00')
        
        session_events = self.current_session_costs[session_id]
        return sum(event.total_cost for event in session_events)
    
    async def get_user_costs(self, 
                           user_id: str,
                           start_date: datetime,
                           end_date: datetime) -> Dict[str, Any]:
        """Get detailed cost breakdown for a user."""
        
        user_events = [
            event for event in self.cost_events
            if (event.user_id == user_id and 
                start_date <= event.timestamp <= end_date)
        ]
        
        if not user_events:
            return {
                'user_id': user_id,
                'total_cost': Decimal('0.00'),
                'total_events': 0
            }
        
        # Aggregate user data
        total_cost = sum(event.total_cost for event in user_events)
        costs_by_category = defaultdict(Decimal)
        costs_by_resource = defaultdict(Decimal)
        costs_by_matter = defaultdict(Decimal)
        
        for event in user_events:
            costs_by_category[event.cost_category] += event.total_cost
            costs_by_resource[event.resource_type] += event.total_cost
            if event.matter_id:
                costs_by_matter[event.matter_id] += event.total_cost
        
        return {
            'user_id': user_id,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_cost': float(total_cost),
            'total_events': len(user_events),
            'average_cost_per_event': float(total_cost / len(user_events)),
            'costs_by_category': {k.value: float(v) for k, v in costs_by_category.items()},
            'costs_by_resource': {k.value: float(v) for k, v in costs_by_resource.items()},
            'costs_by_matter': {k: float(v) for k, v in costs_by_matter.items()},
            'most_expensive_resource': max(costs_by_resource.keys(), 
                                         key=lambda k: costs_by_resource[k]).value if costs_by_resource else None,
            'most_used_category': max(costs_by_category.keys(),
                                    key=lambda k: costs_by_category[k]).value if costs_by_category else None
        }
    
    async def update_pricing(self, resource_type: ResourceType, pricing_config: ResourcePricing):
        """Update pricing configuration for a resource."""
        
        self.pricing_configs[resource_type] = pricing_config
        self.logger.info(f"Updated pricing for {resource_type.value}")
    
    async def export_cost_data(self, 
                             start_date: datetime,
                             end_date: datetime,
                             format: str = "json") -> str:
        """Export cost data for external analysis."""
        
        # Filter events
        export_events = [
            event for event in self.cost_events
            if start_date <= event.timestamp <= end_date
        ]
        
        if format.lower() == "json":
            # Convert to JSON-serializable format
            export_data = []
            for event in export_events:
                export_data.append({
                    'event_id': event.event_id,
                    'timestamp': event.timestamp.isoformat(),
                    'user_id': event.user_id,
                    'resource_type': event.resource_type.value,
                    'cost_category': event.cost_category.value,
                    'total_cost': float(event.total_cost),
                    'base_cost': float(event.base_cost),
                    'additional_fees': float(event.additional_fees),
                    'tax_amount': float(event.tax_amount),
                    'query_text': event.query_text,
                    'document_count': event.document_count,
                    'api_calls': event.api_calls,
                    'processing_time': event.processing_time,
                    'matter_id': event.matter_id,
                    'client_id': event.client_id,
                    'results_found': event.results_found,
                    'relevant_results': event.relevant_results,
                    'success_rate': event.success_rate
                })
            
            return json.dumps(export_data, indent=2)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Helper functions
async def track_search_cost(user_id: str, resource_type: ResourceType, query: str, 
                          results: int, relevant: int, time: float) -> CostEvent:
    """Helper function to track search costs."""
    tracker = CostTracker()
    return await tracker.track_search_cost(user_id, resource_type, query, results, relevant, time)

async def get_daily_costs(start_date: datetime, end_date: datetime) -> CostSummary:
    """Helper function to get daily cost summary."""
    tracker = CostTracker()
    return await tracker.get_cost_summary(start_date, end_date)