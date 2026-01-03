"""
Advanced cost optimization algorithms for legal research platforms.
Provides intelligent routing, resource selection, and automated optimization strategies.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from decimal import Decimal
import random
from collections import defaultdict
import heapq

from ..types.unified_types import UnifiedDocument, ContentType, UnifiedQuery
from .cost_tracker import ResourceType, CostCategory, CostTracker
from .usage_monitor import UsageMonitor, ActivityType
from .cost_analyzer import CostAnalyzer, OptimizationRecommendation


class OptimizationStrategy(Enum):
    """Types of optimization strategies."""
    COST_MINIMIZATION = "cost_minimization"
    QUALITY_MAXIMIZATION = "quality_maximization"  
    BALANCED = "balanced"
    SPEED_OPTIMIZATION = "speed_optimization"
    RELEVANCE_OPTIMIZATION = "relevance_optimization"


class ResourceSelectionMethod(Enum):
    """Methods for resource selection."""
    CHEAPEST_FIRST = "cheapest_first"
    QUALITY_WEIGHTED = "quality_weighted"
    COST_EFFECTIVENESS = "cost_effectiveness"
    MACHINE_LEARNING = "machine_learning"
    HYBRID = "hybrid"


@dataclass
class ResourceOption:
    """Available resource option for a query."""
    resource_type: ResourceType
    estimated_cost: Decimal
    estimated_quality: float  # 0-1 scale
    estimated_relevance: float  # 0-1 scale
    estimated_time: float  # seconds
    confidence: float  # 0-1 scale
    
    # Historical performance
    historical_success_rate: float = 0.0
    average_results_count: int = 0
    user_satisfaction_score: float = 0.0
    
    # Current status
    availability: bool = True
    current_load: float = 0.0  # 0-1 scale
    rate_limit_status: str = "ok"  # "ok", "approaching", "limited"


@dataclass
class OptimizationResult:
    """Result of cost optimization."""
    selected_resource: ResourceType
    estimated_cost: Decimal
    estimated_savings: Decimal
    confidence: float
    
    # Decision rationale
    optimization_strategy: OptimizationStrategy
    selection_method: ResourceSelectionMethod
    decision_factors: Dict[str, float]
    
    # Alternative options
    alternative_resources: List[ResourceOption] = field(default_factory=list)
    
    # Execution plan
    execution_steps: List[str] = field(default_factory=list)
    fallback_options: List[ResourceType] = field(default_factory=list)


@dataclass
class BatchOptimizationRequest:
    """Request for batch optimization."""
    queries: List[UnifiedQuery]
    user_id: str
    matter_id: Optional[str] = None
    budget_limit: Optional[Decimal] = None
    quality_threshold: float = 0.7
    max_time_limit: Optional[float] = None  # seconds


@dataclass
class BatchOptimizationResult:
    """Result of batch optimization."""
    total_estimated_cost: Decimal
    total_estimated_savings: Decimal
    query_assignments: Dict[str, OptimizationResult]  # query_id -> optimization
    
    # Batch-level optimizations
    resource_consolidation_savings: Decimal = Decimal('0.00')
    bulk_discount_applied: bool = False
    load_balancing_applied: bool = False
    
    # Execution plan
    recommended_execution_order: List[str] = field(default_factory=list)  # query_ids
    estimated_total_time: float = 0.0


class CostOptimizer:
    """
    Advanced cost optimization engine for legal research.
    
    Uses machine learning, historical data, and optimization algorithms
    to select the most cost-effective research resources and strategies.
    """
    
    def __init__(self, 
                 cost_tracker: CostTracker,
                 usage_monitor: UsageMonitor,
                 cost_analyzer: CostAnalyzer):
        self.cost_tracker = cost_tracker
        self.usage_monitor = usage_monitor
        self.cost_analyzer = cost_analyzer
        self.logger = logging.getLogger(__name__)
        
        # Resource performance data
        self.resource_performance: Dict[ResourceType, Dict[str, float]] = defaultdict(dict)
        self.user_resource_preferences: Dict[str, Dict[ResourceType, float]] = defaultdict(dict)
        
        # Optimization parameters
        self.quality_weights = {
            'relevance': 0.4,
            'completeness': 0.3,
            'authority': 0.2,
            'freshness': 0.1
        }
        
        self.cost_thresholds = {
            'low': Decimal('10.00'),
            'medium': Decimal('25.00'),
            'high': Decimal('50.00')
        }
        
        # ML model parameters (simplified)
        self.model_weights = {
            'cost_factor': -0.3,
            'quality_factor': 0.4,
            'speed_factor': 0.2,
            'user_preference': 0.1
        }
        
        # Initialize resource performance baselines
        self._initialize_resource_baselines()
    
    def _initialize_resource_baselines(self):
        """Initialize baseline performance metrics for resources."""
        
        # Baseline performance data (would be learned from historical data)
        baselines = {
            ResourceType.WESTLAW: {
                'average_cost': 15.0,
                'quality_score': 0.9,
                'relevance_rate': 0.75,
                'speed_score': 0.8,
                'reliability': 0.95
            },
            ResourceType.LEXIS: {
                'average_cost': 12.0,
                'quality_score': 0.85,
                'relevance_rate': 0.72,
                'speed_score': 0.75,
                'reliability': 0.92
            },
            ResourceType.BLOOMBERG_LAW: {
                'average_cost': 18.0,
                'quality_score': 0.88,
                'relevance_rate': 0.78,
                'speed_score': 0.85,
                'reliability': 0.90
            },
            ResourceType.GOOGLE_SCHOLAR: {
                'average_cost': 0.0,
                'quality_score': 0.6,
                'relevance_rate': 0.45,
                'speed_score': 0.9,
                'reliability': 0.85
            },
            ResourceType.FASTCASE: {
                'average_cost': 5.0,
                'quality_score': 0.7,
                'relevance_rate': 0.6,
                'speed_score': 0.8,
                'reliability': 0.88
            },
            ResourceType.JUSTIA: {
                'average_cost': 0.0,
                'quality_score': 0.55,
                'relevance_rate': 0.4,
                'speed_score': 0.85,
                'reliability': 0.8
            }
        }
        
        for resource_type, metrics in baselines.items():
            self.resource_performance[resource_type] = metrics
    
    async def optimize_single_query(self, 
                                   query: UnifiedQuery,
                                   user_id: str,
                                   strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
                                   budget_limit: Optional[Decimal] = None) -> OptimizationResult:
        """
        Optimize resource selection for a single query.
        
        Args:
            query: The search query to optimize
            user_id: User making the query
            strategy: Optimization strategy to use
            budget_limit: Optional budget constraint
            
        Returns:
            OptimizationResult with recommended resource and rationale
        """
        
        self.logger.info(f"Optimizing query: {query.query_text[:50]}...")
        
        # Analyze query characteristics
        query_analysis = await self._analyze_query_requirements(query)
        
        # Get available resource options
        resource_options = await self._get_resource_options(query, user_id, query_analysis)
        
        # Apply budget constraints
        if budget_limit:
            resource_options = [opt for opt in resource_options if opt.estimated_cost <= budget_limit]
        
        if not resource_options:
            raise ValueError("No resources available within budget constraints")
        
        # Select optimal resource based on strategy
        selection_method = self._determine_selection_method(strategy, query_analysis)
        optimal_resource = await self._select_optimal_resource(
            resource_options, strategy, selection_method, query_analysis
        )
        
        # Calculate savings compared to default/most expensive option
        default_cost = max(opt.estimated_cost for opt in resource_options)
        estimated_savings = default_cost - optimal_resource.estimated_cost
        
        # Build optimization result
        result = OptimizationResult(
            selected_resource=optimal_resource.resource_type,
            estimated_cost=optimal_resource.estimated_cost,
            estimated_savings=estimated_savings,
            confidence=optimal_resource.confidence,
            optimization_strategy=strategy,
            selection_method=selection_method,
            decision_factors=await self._calculate_decision_factors(optimal_resource, resource_options),
            alternative_resources=resource_options[:3],  # Top 3 alternatives
            execution_steps=await self._generate_execution_steps(optimal_resource, query),
            fallback_options=await self._identify_fallback_options(resource_options, optimal_resource)
        )
        
        # Learn from this optimization for future improvements
        await self._record_optimization_decision(query, user_id, result)
        
        return result
    
    async def optimize_batch_queries(self, 
                                   request: BatchOptimizationRequest) -> BatchOptimizationResult:
        """
        Optimize resource selection for batch queries with cross-query optimizations.
        
        Args:
            request: Batch optimization request
            
        Returns:
            BatchOptimizationResult with optimized assignments
        """
        
        self.logger.info(f"Optimizing batch of {len(request.queries)} queries")
        
        # Individual optimizations
        individual_results = {}
        total_cost = Decimal('0.00')
        total_savings = Decimal('0.00')
        
        for query in request.queries:
            result = await self.optimize_single_query(
                query, 
                request.user_id,
                OptimizationStrategy.BALANCED,
                request.budget_limit
            )
            individual_results[query.query_id] = result
            total_cost += result.estimated_cost
            total_savings += result.estimated_savings
        
        # Apply batch-level optimizations
        batch_result = BatchOptimizationResult(
            total_estimated_cost=total_cost,
            total_estimated_savings=total_savings,
            query_assignments=individual_results
        )
        
        # Resource consolidation optimization
        consolidation_savings = await self._apply_resource_consolidation(
            batch_result, request
        )
        batch_result.resource_consolidation_savings = consolidation_savings
        batch_result.total_estimated_savings += consolidation_savings
        
        # Bulk pricing optimization
        bulk_savings = await self._apply_bulk_pricing_optimization(
            batch_result, request
        )
        if bulk_savings > 0:
            batch_result.bulk_discount_applied = True
            batch_result.total_estimated_savings += bulk_savings
        
        # Load balancing optimization
        await self._apply_load_balancing_optimization(batch_result)
        
        # Generate execution plan
        batch_result.recommended_execution_order = await self._optimize_execution_order(
            batch_result, request
        )
        batch_result.estimated_total_time = await self._estimate_total_execution_time(
            batch_result
        )
        
        return batch_result
    
    async def _analyze_query_requirements(self, query: UnifiedQuery) -> Dict[str, Any]:
        """Analyze query to determine requirements and characteristics."""
        
        analysis = {
            'complexity': 'medium',
            'urgency': 'normal',
            'quality_requirement': 0.7,
            'cost_sensitivity': 0.5,
            'content_types': [],
            'practice_areas': [],
            'jurisdictions': []
        }
        
        query_text = query.query_text.lower()
        word_count = len(query_text.split())
        
        # Analyze complexity
        if word_count > 15 or any(op in query_text for op in ['and', 'or', 'not', '"']):
            analysis['complexity'] = 'high'
        elif word_count < 5:
            analysis['complexity'] = 'low'
        
        # Detect urgency indicators
        urgent_terms = ['urgent', 'asap', 'emergency', 'immediate', 'deadline']
        if any(term in query_text for term in urgent_terms):
            analysis['urgency'] = 'high'
            analysis['cost_sensitivity'] = 0.3  # Less cost sensitive when urgent
        
        # Detect quality requirements
        quality_terms = ['comprehensive', 'thorough', 'complete', 'detailed', 'authoritative']
        if any(term in query_text for term in quality_terms):
            analysis['quality_requirement'] = 0.9
            analysis['cost_sensitivity'] = 0.3  # Less cost sensitive for quality
        
        # Detect content type preferences
        if any(term in query_text for term in ['case', 'decision', 'opinion', 'ruling']):
            analysis['content_types'].append(ContentType.CASE_LAW)
        if any(term in query_text for term in ['statute', 'code', 'law', 'regulation']):
            analysis['content_types'].append(ContentType.STATUTE)
        if any(term in query_text for term in ['article', 'law review', 'journal']):
            analysis['content_types'].append(ContentType.LAW_REVIEW)
        
        # Practice area detection (simplified)
        practice_areas_map = {
            'contract': 'Contract Law',
            'tort': 'Tort Law',
            'criminal': 'Criminal Law',
            'corporate': 'Corporate Law',
            'employment': 'Employment Law',
            'intellectual property': 'IP Law',
            'tax': 'Tax Law',
            'environmental': 'Environmental Law'
        }
        
        for keyword, area in practice_areas_map.items():
            if keyword in query_text:
                analysis['practice_areas'].append(area)
        
        # Add user context if available
        if hasattr(query, 'user_context'):
            context = getattr(query, 'user_context', {})
            analysis.update(context)
        
        return analysis
    
    async def _get_resource_options(self, 
                                  query: UnifiedQuery,
                                  user_id: str,
                                  query_analysis: Dict[str, Any]) -> List[ResourceOption]:
        """Get available resource options for a query."""
        
        options = []
        
        # Get user's historical performance with each resource
        user_profile = await self.usage_monitor.analyze_user_patterns(user_id)
        
        for resource_type in ResourceType:
            # Skip internal/AI resources for now
            if resource_type in [ResourceType.INTERNAL_SYSTEM, ResourceType.AI_SERVICE]:
                continue
            
            # Get resource performance data
            performance = self.resource_performance[resource_type]
            
            # Estimate cost based on query complexity
            base_cost = Decimal(str(performance.get('average_cost', 10.0)))
            complexity_multiplier = {
                'low': 0.8,
                'medium': 1.0,
                'high': 1.3
            }.get(query_analysis['complexity'], 1.0)
            
            estimated_cost = base_cost * Decimal(str(complexity_multiplier))
            
            # Estimate quality based on query requirements
            base_quality = performance.get('quality_score', 0.7)
            content_type_bonus = 0.0
            
            # Quality bonus for relevant content types
            if query_analysis['content_types']:
                if resource_type in [ResourceType.WESTLAW, ResourceType.LEXIS]:
                    content_type_bonus = 0.1
            
            estimated_quality = min(1.0, base_quality + content_type_bonus)
            
            # Estimate relevance
            base_relevance = performance.get('relevance_rate', 0.6)
            user_relevance_modifier = 0.0
            
            # User-specific relevance adjustment
            if resource_type in user_profile.preferred_resources:
                user_relevance_modifier = 0.1
            
            estimated_relevance = min(1.0, base_relevance + user_relevance_modifier)
            
            # Estimate time
            base_speed = performance.get('speed_score', 0.8)
            estimated_time = 30.0 / base_speed  # Base 30 seconds, adjusted by speed
            
            # Calculate confidence based on historical data availability
            historical_queries = len([
                e for e in self.cost_tracker.cost_events
                if e.user_id == user_id and e.resource_type == resource_type
            ])
            confidence = min(1.0, historical_queries / 10.0 + 0.5)  # 50% base + data bonus
            
            # Check availability and current status
            availability = True
            current_load = random.uniform(0.1, 0.7)  # Simulated load
            rate_limit_status = "ok"
            
            # Simulate rate limiting for free resources
            if resource_type in [ResourceType.GOOGLE_SCHOLAR, ResourceType.JUSTIA]:
                if current_load > 0.8:
                    rate_limit_status = "approaching"
                    estimated_time *= 2  # Slower when approaching limits
            
            option = ResourceOption(
                resource_type=resource_type,
                estimated_cost=estimated_cost,
                estimated_quality=estimated_quality,
                estimated_relevance=estimated_relevance,
                estimated_time=estimated_time,
                confidence=confidence,
                historical_success_rate=performance.get('reliability', 0.8),
                average_results_count=int(performance.get('average_results', 50)),
                user_satisfaction_score=performance.get('user_satisfaction', 0.7),
                availability=availability,
                current_load=current_load,
                rate_limit_status=rate_limit_status
            )
            
            options.append(option)
        
        return options
    
    def _determine_selection_method(self, 
                                  strategy: OptimizationStrategy,
                                  query_analysis: Dict[str, Any]) -> ResourceSelectionMethod:
        """Determine the best selection method based on strategy and query."""
        
        if strategy == OptimizationStrategy.COST_MINIMIZATION:
            return ResourceSelectionMethod.CHEAPEST_FIRST
        elif strategy == OptimizationStrategy.QUALITY_MAXIMIZATION:
            return ResourceSelectionMethod.QUALITY_WEIGHTED
        elif strategy == OptimizationStrategy.SPEED_OPTIMIZATION:
            return ResourceSelectionMethod.COST_EFFECTIVENESS  # Fast and cheap
        elif strategy == OptimizationStrategy.RELEVANCE_OPTIMIZATION:
            return ResourceSelectionMethod.MACHINE_LEARNING
        else:  # BALANCED
            if query_analysis['complexity'] == 'high':
                return ResourceSelectionMethod.MACHINE_LEARNING
            else:
                return ResourceSelectionMethod.COST_EFFECTIVENESS
    
    async def _select_optimal_resource(self, 
                                     options: List[ResourceOption],
                                     strategy: OptimizationStrategy,
                                     method: ResourceSelectionMethod,
                                     query_analysis: Dict[str, Any]) -> ResourceOption:
        """Select the optimal resource from available options."""
        
        if method == ResourceSelectionMethod.CHEAPEST_FIRST:
            return min(options, key=lambda x: x.estimated_cost)
        
        elif method == ResourceSelectionMethod.QUALITY_WEIGHTED:
            return max(options, key=lambda x: x.estimated_quality * x.confidence)
        
        elif method == ResourceSelectionMethod.COST_EFFECTIVENESS:
            # Cost-effectiveness = (Quality * Relevance) / Cost
            def cost_effectiveness(option):
                if option.estimated_cost == 0:
                    return option.estimated_quality * option.estimated_relevance * 100
                return (option.estimated_quality * option.estimated_relevance) / float(option.estimated_cost)
            
            return max(options, key=cost_effectiveness)
        
        elif method == ResourceSelectionMethod.MACHINE_LEARNING:
            return await self._ml_resource_selection(options, query_analysis)
        
        else:  # HYBRID
            # Combine multiple factors with weighted scoring
            def hybrid_score(option):
                cost_score = 1.0 - (float(option.estimated_cost) / float(max(opt.estimated_cost for opt in options)))
                quality_score = option.estimated_quality
                relevance_score = option.estimated_relevance
                speed_score = 1.0 - (option.estimated_time / max(opt.estimated_time for opt in options))
                
                # Weight based on strategy
                if strategy == OptimizationStrategy.COST_MINIMIZATION:
                    weights = {'cost': 0.6, 'quality': 0.2, 'relevance': 0.1, 'speed': 0.1}
                elif strategy == OptimizationStrategy.QUALITY_MAXIMIZATION:
                    weights = {'cost': 0.1, 'quality': 0.5, 'relevance': 0.3, 'speed': 0.1}
                elif strategy == OptimizationStrategy.SPEED_OPTIMIZATION:
                    weights = {'cost': 0.2, 'quality': 0.2, 'relevance': 0.2, 'speed': 0.4}
                else:  # BALANCED
                    weights = {'cost': 0.3, 'quality': 0.3, 'relevance': 0.25, 'speed': 0.15}
                
                return (cost_score * weights['cost'] + 
                       quality_score * weights['quality'] + 
                       relevance_score * weights['relevance'] + 
                       speed_score * weights['speed'])
            
            return max(options, key=hybrid_score)
    
    async def _ml_resource_selection(self, 
                                   options: List[ResourceOption],
                                   query_analysis: Dict[str, Any]) -> ResourceOption:
        """Use machine learning approach for resource selection."""
        
        # Simplified ML model using weighted linear combination
        def ml_score(option):
            # Feature vector
            features = {
                'cost': float(option.estimated_cost),
                'quality': option.estimated_quality,
                'relevance': option.estimated_relevance,
                'speed': 1.0 / option.estimated_time,
                'reliability': option.historical_success_rate,
                'user_satisfaction': option.user_satisfaction_score
            }
            
            # Normalize features
            normalized_features = {}
            for key, value in features.items():
                if key == 'cost':
                    # Lower cost is better
                    max_cost = max(float(opt.estimated_cost) for opt in options)
                    normalized_features[key] = 1.0 - (value / max_cost) if max_cost > 0 else 1.0
                elif key == 'speed':
                    # Higher speed (1/time) is better
                    max_speed = max(1.0 / opt.estimated_time for opt in options)
                    normalized_features[key] = value / max_speed if max_speed > 0 else 1.0
                else:
                    # Higher values are better for quality, relevance, etc.
                    normalized_features[key] = value
            
            # Apply learned weights (simplified model)
            weights = {
                'cost': 0.25,
                'quality': 0.30,
                'relevance': 0.25,
                'speed': 0.10,
                'reliability': 0.05,
                'user_satisfaction': 0.05
            }
            
            score = sum(normalized_features[key] * weights[key] for key in weights)
            
            # Apply query-specific adjustments
            if query_analysis['urgency'] == 'high':
                score += normalized_features['speed'] * 0.2  # Boost speed importance
            
            if query_analysis['quality_requirement'] > 0.8:
                score += normalized_features['quality'] * 0.2  # Boost quality importance
            
            return score * option.confidence  # Weight by confidence
        
        return max(options, key=ml_score)
    
    async def _calculate_decision_factors(self, 
                                        selected: ResourceOption,
                                        all_options: List[ResourceOption]) -> Dict[str, float]:
        """Calculate the factors that influenced the decision."""
        
        factors = {
            'cost_advantage': 0.0,
            'quality_advantage': 0.0,
            'relevance_advantage': 0.0,
            'speed_advantage': 0.0,
            'reliability_advantage': 0.0
        }
        
        if len(all_options) > 1:
            avg_cost = sum(float(opt.estimated_cost) for opt in all_options) / len(all_options)
            avg_quality = sum(opt.estimated_quality for opt in all_options) / len(all_options)
            avg_relevance = sum(opt.estimated_relevance for opt in all_options) / len(all_options)
            avg_time = sum(opt.estimated_time for opt in all_options) / len(all_options)
            avg_reliability = sum(opt.historical_success_rate for opt in all_options) / len(all_options)
            
            # Calculate advantages (positive means better than average)
            factors['cost_advantage'] = (avg_cost - float(selected.estimated_cost)) / avg_cost if avg_cost > 0 else 0
            factors['quality_advantage'] = (selected.estimated_quality - avg_quality) / avg_quality if avg_quality > 0 else 0
            factors['relevance_advantage'] = (selected.estimated_relevance - avg_relevance) / avg_relevance if avg_relevance > 0 else 0
            factors['speed_advantage'] = (avg_time - selected.estimated_time) / avg_time if avg_time > 0 else 0
            factors['reliability_advantage'] = (selected.historical_success_rate - avg_reliability) / avg_reliability if avg_reliability > 0 else 0
        
        return factors
    
    async def _generate_execution_steps(self, 
                                       selected: ResourceOption,
                                       query: UnifiedQuery) -> List[str]:
        """Generate execution steps for the optimized query."""
        
        steps = [
            f"Execute query on {selected.resource_type.value}",
            f"Monitor cost (estimated: ${selected.estimated_cost})",
            "Evaluate result quality and relevance",
        ]
        
        # Add resource-specific steps
        if selected.resource_type in [ResourceType.WESTLAW, ResourceType.LEXIS]:
            steps.extend([
                "Check subscription usage limits",
                "Apply advanced search filters if available",
                "Consider Shepardizing high-value results"
            ])
        elif selected.resource_type == ResourceType.GOOGLE_SCHOLAR:
            steps.extend([
                "Check rate limiting status",
                "Validate result authority and currency",
                "Consider supplemental premium search if results insufficient"
            ])
        
        steps.append("Record performance metrics for future optimization")
        
        return steps
    
    async def _identify_fallback_options(self, 
                                       all_options: List[ResourceOption],
                                       selected: ResourceOption) -> List[ResourceType]:
        """Identify fallback options if the primary choice fails."""
        
        # Remove the selected option and sort by quality/cost ratio
        fallback_options = [opt for opt in all_options if opt.resource_type != selected.resource_type]
        
        # Sort by combined quality and availability
        fallback_options.sort(
            key=lambda x: (x.estimated_quality * x.confidence + (1.0 if x.availability else 0.0)),
            reverse=True
        )
        
        return [opt.resource_type for opt in fallback_options[:3]]
    
    async def _record_optimization_decision(self, 
                                          query: UnifiedQuery,
                                          user_id: str,
                                          result: OptimizationResult):
        """Record optimization decision for learning and improvement."""
        
        # This would typically store the decision in a database for ML training
        # For now, we'll log it
        self.logger.info(
            f"Optimization decision recorded: "
            f"Query={query.query_text[:30]}..., "
            f"User={user_id}, "
            f"Selected={result.selected_resource.value}, "
            f"Cost=${result.estimated_cost}, "
            f"Strategy={result.optimization_strategy.value}"
        )
        
        # Update resource performance data based on decision
        # (This would be updated with actual results later)
        resource_perf = self.resource_performance[result.selected_resource]
        resource_perf['selection_count'] = resource_perf.get('selection_count', 0) + 1
    
    async def _apply_resource_consolidation(self, 
                                          batch_result: BatchOptimizationResult,
                                          request: BatchOptimizationRequest) -> Decimal:
        """Apply resource consolidation optimization to batch."""
        
        # Count resource usage
        resource_usage = defaultdict(int)
        resource_costs = defaultdict(Decimal)
        
        for query_result in batch_result.query_assignments.values():
            resource = query_result.selected_resource
            resource_usage[resource] += 1
            resource_costs[resource] += query_result.estimated_cost
        
        savings = Decimal('0.00')
        
        # Look for consolidation opportunities
        # If multiple queries use expensive resources, consider bulk discounts
        for resource, usage_count in resource_usage.items():
            if usage_count >= 5:  # 5+ queries on same resource
                # Simulate bulk discount (5% for 5+, 10% for 10+)
                discount_rate = 0.05 if usage_count < 10 else 0.10
                resource_cost = resource_costs[resource]
                discount_amount = resource_cost * Decimal(str(discount_rate))
                savings += discount_amount
                
                self.logger.info(f"Applied {discount_rate*100}% bulk discount for {resource.value}: ${discount_amount}")
        
        return savings
    
    async def _apply_bulk_pricing_optimization(self, 
                                             batch_result: BatchOptimizationResult,
                                             request: BatchOptimizationRequest) -> Decimal:
        """Apply bulk pricing optimization."""
        
        # If total cost exceeds threshold, negotiate bulk pricing
        total_cost = batch_result.total_estimated_cost
        
        if total_cost > Decimal('200.00'):  # $200 threshold
            # Simulate 8% bulk discount for large batches
            bulk_discount = total_cost * Decimal('0.08')
            self.logger.info(f"Applied bulk pricing discount: ${bulk_discount}")
            return bulk_discount
        
        return Decimal('0.00')
    
    async def _apply_load_balancing_optimization(self, batch_result: BatchOptimizationResult):
        """Apply load balancing to distribute queries across resources."""
        
        # Count resource usage
        resource_usage = defaultdict(int)
        for query_result in batch_result.query_assignments.values():
            resource_usage[query_result.selected_resource] += 1
        
        # If any resource is overloaded (>50% of queries), flag for load balancing
        total_queries = len(batch_result.query_assignments)
        for resource, usage_count in resource_usage.items():
            usage_percentage = usage_count / total_queries
            if usage_percentage > 0.5:
                batch_result.load_balancing_applied = True
                self.logger.info(f"Load balancing applied: {resource.value} usage at {usage_percentage*100:.1f}%")
                break
    
    async def _optimize_execution_order(self, 
                                      batch_result: BatchOptimizationResult,
                                      request: BatchOptimizationRequest) -> List[str]:
        """Optimize the execution order of batch queries."""
        
        # Create priority queue based on multiple factors
        query_priorities = []
        
        for query_id, optimization_result in batch_result.query_assignments.items():
            # Priority factors (lower score = higher priority)
            cost_factor = float(optimization_result.estimated_cost)
            time_factor = sum(opt.estimated_time for opt in optimization_result.alternative_resources[:1])
            
            # Queries with rate-limited resources should go first
            rate_limit_bonus = 0
            for alt in optimization_result.alternative_resources:
                if alt.rate_limit_status in ["approaching", "limited"]:
                    rate_limit_bonus = -100  # High priority
                    break
            
            priority_score = cost_factor + time_factor + rate_limit_bonus
            
            heapq.heappush(query_priorities, (priority_score, query_id))
        
        # Extract ordered query IDs
        execution_order = []
        while query_priorities:
            _, query_id = heapq.heappop(query_priorities)
            execution_order.append(query_id)
        
        return execution_order
    
    async def _estimate_total_execution_time(self, batch_result: BatchOptimizationResult) -> float:
        """Estimate total execution time for batch."""
        
        # Simple parallel execution model
        # Assume queries can run in parallel on different resources
        
        resource_times = defaultdict(list)
        for query_result in batch_result.query_assignments.values():
            resource = query_result.selected_resource
            # Use first alternative for time estimate
            if query_result.alternative_resources:
                time_estimate = query_result.alternative_resources[0].estimated_time
                resource_times[resource].append(time_estimate)
        
        # Calculate parallel execution time
        max_resource_time = 0.0
        for resource, times in resource_times.items():
            resource_total_time = sum(times)  # Sequential within resource
            max_resource_time = max(max_resource_time, resource_total_time)
        
        return max_resource_time
    
    async def learn_from_results(self, 
                               optimization_result: OptimizationResult,
                               actual_results: Dict[str, Any]):
        """Learn from actual results to improve future optimization."""
        
        selected_resource = optimization_result.selected_resource
        
        # Update resource performance based on actual results
        actual_cost = actual_results.get('actual_cost', 0.0)
        actual_relevance = actual_results.get('relevance_rate', 0.0)
        actual_quality = actual_results.get('quality_score', 0.0)
        actual_time = actual_results.get('execution_time', 0.0)
        user_satisfaction = actual_results.get('user_satisfaction', 0.0)
        
        # Update performance metrics with exponential moving average
        alpha = 0.1  # Learning rate
        perf = self.resource_performance[selected_resource]
        
        if 'average_cost' in perf:
            perf['average_cost'] = (1 - alpha) * perf['average_cost'] + alpha * actual_cost
        if 'relevance_rate' in perf:
            perf['relevance_rate'] = (1 - alpha) * perf['relevance_rate'] + alpha * actual_relevance
        if 'quality_score' in perf:
            perf['quality_score'] = (1 - alpha) * perf['quality_score'] + alpha * actual_quality
        if 'user_satisfaction' in perf:
            perf['user_satisfaction'] = (1 - alpha) * perf['user_satisfaction'] + alpha * user_satisfaction
        
        # Calculate prediction accuracy
        cost_accuracy = 1.0 - abs(float(optimization_result.estimated_cost) - actual_cost) / max(actual_cost, 1.0)
        
        self.logger.info(
            f"Learning update for {selected_resource.value}: "
            f"Cost accuracy: {cost_accuracy:.2f}, "
            f"Actual relevance: {actual_relevance:.2f}"
        )
    
    async def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get statistics about optimization performance."""
        
        stats = {
            'total_optimizations': 0,
            'average_savings_per_optimization': 0.0,
            'resource_selection_distribution': defaultdict(int),
            'strategy_effectiveness': defaultdict(list),
            'user_satisfaction_scores': defaultdict(list)
        }
        
        # This would typically query stored optimization records
        # For now, return current resource performance
        for resource_type, metrics in self.resource_performance.items():
            stats['resource_selection_distribution'][resource_type.value] = metrics.get('selection_count', 0)
        
        return dict(stats)
    
    async def recommend_strategy_for_user(self, user_id: str) -> OptimizationStrategy:
        """Recommend optimization strategy based on user profile."""
        
        user_profile = await self.usage_monitor.analyze_user_patterns(user_id)
        
        # Analyze user characteristics
        if user_profile.cost_awareness > 0.7:
            return OptimizationStrategy.COST_MINIMIZATION
        elif user_profile.efficiency_level.value in ['highly_efficient', 'efficient']:
            return OptimizationStrategy.QUALITY_MAXIMIZATION
        elif user_profile.primary_pattern and 'exploratory' in user_profile.primary_pattern.value:
            return OptimizationStrategy.SPEED_OPTIMIZATION
        else:
            return OptimizationStrategy.BALANCED
    
    async def simulate_optimization_impact(self, 
                                         queries: List[UnifiedQuery],
                                         user_id: str,
                                         strategies: List[OptimizationStrategy]) -> Dict[str, Any]:
        """Simulate the impact of different optimization strategies."""
        
        simulation_results = {}
        
        for strategy in strategies:
            total_cost = Decimal('0.00')
            total_savings = Decimal('0.00')
            quality_scores = []
            
            for query in queries:
                result = await self.optimize_single_query(query, user_id, strategy)
                total_cost += result.estimated_cost
                total_savings += result.estimated_savings
                
                # Estimate quality from selected resource
                if result.alternative_resources:
                    selected_option = next(
                        (opt for opt in result.alternative_resources if opt.resource_type == result.selected_resource),
                        result.alternative_resources[0]
                    )
                    quality_scores.append(selected_option.estimated_quality)
            
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            simulation_results[strategy.value] = {
                'total_cost': float(total_cost),
                'total_savings': float(total_savings),
                'average_quality': avg_quality,
                'cost_per_query': float(total_cost / len(queries)) if queries else 0.0
            }
        
        return simulation_results


# Helper functions
async def optimize_query_cost(query: UnifiedQuery, user_id: str) -> OptimizationResult:
    """Helper function to optimize a single query."""
    cost_tracker = CostTracker()
    usage_monitor = UsageMonitor()
    cost_analyzer = CostAnalyzer(cost_tracker, usage_monitor)
    optimizer = CostOptimizer(cost_tracker, usage_monitor, cost_analyzer)
    
    return await optimizer.optimize_single_query(query, user_id)

async def optimize_batch_cost(queries: List[UnifiedQuery], user_id: str) -> BatchOptimizationResult:
    """Helper function to optimize batch queries."""
    cost_tracker = CostTracker()
    usage_monitor = UsageMonitor()
    cost_analyzer = CostAnalyzer(cost_tracker, usage_monitor)
    optimizer = CostOptimizer(cost_tracker, usage_monitor, cost_analyzer)
    
    request = BatchOptimizationRequest(queries=queries, user_id=user_id)
    return await optimizer.optimize_batch_queries(request)