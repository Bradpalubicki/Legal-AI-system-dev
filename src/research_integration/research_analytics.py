"""
Research Analytics

Comprehensive analytics system for legal research tracking usage patterns,
performance metrics, cost analysis, and research effectiveness insights.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
import numpy as np

from .models import (
    ResearchQuery, SearchResult, LegalDocument, Citation,
    ResearchProvider, DocumentType, ResearchSession, APIUsageMetrics
)

logger = logging.getLogger(__name__)


class QueryAnalytics(BaseModel):
    """Analytics for individual query performance"""
    query_id: UUID
    query_text: str
    search_type: str
    execution_count: int = 1
    
    # Performance metrics
    average_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    
    # Result metrics
    total_results_found: int = 0
    average_results_returned: float = 0.0
    relevance_scores: List[float] = []
    
    # User interaction
    documents_viewed: int = 0
    documents_saved: int = 0
    successful_research: bool = False
    
    # Provider performance
    provider_performance: Dict[str, Dict[str, float]] = {}
    
    # Temporal data
    first_executed: datetime = Field(default_factory=datetime.utcnow)
    last_executed: datetime = Field(default_factory=datetime.utcnow)
    peak_usage_hours: List[int] = []


class UserResearchProfile(BaseModel):
    """Research profile and behavior analysis for a user"""
    user_id: UUID
    
    # Research patterns
    total_queries: int = 0
    total_sessions: int = 0
    average_session_duration_minutes: float = 0.0
    
    # Query patterns
    common_query_types: Dict[str, int] = {}
    preferred_document_types: Dict[str, int] = {}
    jurisdiction_focus: Dict[str, int] = {}
    practice_area_focus: Dict[str, int] = {}
    
    # Provider preferences
    provider_usage: Dict[str, float] = {}
    provider_satisfaction: Dict[str, float] = {}
    
    # Research effectiveness
    research_success_rate: float = 0.0
    average_documents_per_query: float = 0.0
    citation_discovery_rate: float = 0.0
    
    # Cost analysis
    total_research_cost: float = 0.0
    cost_per_successful_research: float = 0.0
    cost_efficiency_score: float = 0.0
    
    # Temporal patterns
    active_hours: Dict[int, int] = {}  # hour -> count
    active_days: Dict[str, int] = {}  # day_name -> count
    research_velocity_trend: List[float] = []
    
    # Generated insights
    research_insights: List[str] = []
    recommendations: List[str] = []
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class SystemPerformanceMetrics(BaseModel):
    """System-wide performance metrics"""
    metric_period_start: datetime
    metric_period_end: datetime
    
    # Query metrics
    total_queries_executed: int = 0
    unique_queries: int = 0
    query_success_rate: float = 0.0
    
    # Response time metrics
    average_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    
    # Provider metrics
    provider_availability: Dict[str, float] = {}
    provider_performance: Dict[str, Dict[str, float]] = {}
    provider_error_rates: Dict[str, float] = {}
    
    # Cache metrics
    cache_hit_ratio: float = 0.0
    cache_performance_impact: float = 0.0
    
    # Cost metrics
    total_api_costs: float = 0.0
    cost_per_query: float = 0.0
    cost_breakdown_by_provider: Dict[str, float] = {}
    
    # Resource utilization
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    network_utilization: float = 0.0
    
    # Error metrics
    error_rate: float = 0.0
    error_types: Dict[str, int] = {}
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ResearchTrend(BaseModel):
    """Research trend analysis"""
    trend_id: UUID = Field(default_factory=uuid4)
    trend_type: str  # query_popularity, jurisdiction_focus, document_type_usage
    time_period: str  # daily, weekly, monthly
    
    # Trend data points
    data_points: List[Dict[str, Any]] = []  # timestamp, value, metadata
    
    # Trend analysis
    trend_direction: str = "stable"  # increasing, decreasing, stable, volatile
    trend_strength: float = 0.0  # 0.0 to 1.0
    statistical_significance: float = 0.0
    
    # Insights
    key_insights: List[str] = []
    predictions: List[str] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CostAnalysis(BaseModel):
    """Comprehensive cost analysis"""
    analysis_period_start: datetime
    analysis_period_end: datetime
    
    # Total costs
    total_cost: float = 0.0
    westlaw_cost: float = 0.0
    lexisnexis_cost: float = 0.0
    
    # Cost efficiency metrics
    cost_per_query: float = 0.0
    cost_per_document: float = 0.0
    cost_per_successful_research: float = 0.0
    
    # User cost breakdown
    cost_by_user: Dict[str, float] = {}
    high_cost_users: List[str] = []
    
    # Practice area costs
    cost_by_practice_area: Dict[str, float] = {}
    
    # Cost optimization opportunities
    potential_savings: float = 0.0
    optimization_recommendations: List[str] = []
    
    # Budget tracking
    monthly_budget: Optional[float] = None
    budget_utilization: Optional[float] = None
    projected_monthly_cost: Optional[float] = None


class ResearchAnalytics:
    """
    Comprehensive research analytics system providing insights into
    research patterns, performance, costs, and optimization opportunities.
    """
    
    def __init__(self):
        # Data storage
        self.query_analytics: Dict[str, QueryAnalytics] = {}
        self.user_profiles: Dict[UUID, UserResearchProfile] = {}
        self.sessions: List[ResearchSession] = []
        
        # Performance tracking
        self.response_times: List[float] = []
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.provider_metrics: Dict[ResearchProvider, APIUsageMetrics] = {}
        
        # Trend tracking
        self.research_trends: List[ResearchTrend] = []
        
        logger.info("Research Analytics initialized")
    
    async def record_query_execution(
        self,
        query: ResearchQuery,
        result: SearchResult,
        response_time_ms: float,
        user_id: Optional[UUID] = None
    ):
        """Record query execution for analytics"""
        try:
            query_key = self._generate_query_key(query)
            
            # Update or create query analytics
            if query_key in self.query_analytics:
                analytics = self.query_analytics[query_key]
                analytics.execution_count += 1
                
                # Update response time metrics
                total_time = (analytics.average_response_time_ms * (analytics.execution_count - 1) + response_time_ms)
                analytics.average_response_time_ms = total_time / analytics.execution_count
                analytics.min_response_time_ms = min(analytics.min_response_time_ms, response_time_ms)
                analytics.max_response_time_ms = max(analytics.max_response_time_ms, response_time_ms)
                
                analytics.last_executed = datetime.utcnow()
            else:
                analytics = QueryAnalytics(
                    query_id=query.query_id,
                    query_text=query.query_text,
                    search_type=query.search_type.value,
                    average_response_time_ms=response_time_ms,
                    min_response_time_ms=response_time_ms,
                    max_response_time_ms=response_time_ms
                )
                self.query_analytics[query_key] = analytics
            
            # Update result metrics
            analytics.total_results_found += result.total_results
            analytics.average_results_returned = (
                (analytics.average_results_returned * (analytics.execution_count - 1) + result.results_returned) /
                analytics.execution_count
            )
            
            # Update relevance scores
            for document in result.documents:
                if document.relevance_score:
                    analytics.relevance_scores.append(document.relevance_score)
            
            # Update provider performance
            for provider in result.providers_searched:
                if provider.value not in analytics.provider_performance:
                    analytics.provider_performance[provider.value] = {}
                
                provider_metrics = analytics.provider_performance[provider.value]
                provider_metrics['response_time_ms'] = response_time_ms
                provider_metrics['results_returned'] = result.results_returned
                provider_metrics['total_results'] = result.total_results
            
            # Update user profile
            if user_id:
                await self._update_user_profile(user_id, query, result)
            
            # Track response times
            self.response_times.append(response_time_ms)
            
            # Update peak usage hours
            current_hour = datetime.utcnow().hour
            if current_hour not in analytics.peak_usage_hours:
                analytics.peak_usage_hours.append(current_hour)
            
            logger.debug(f"Recorded query execution: {query_key}")
            
        except Exception as e:
            logger.error(f"Failed to record query execution: {str(e)}")
    
    async def record_user_interaction(
        self,
        user_id: UUID,
        query_id: UUID,
        interaction_type: str,  # document_viewed, document_saved, research_completed
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record user interaction for behavior analysis"""
        try:
            # Find query analytics
            query_key = None
            for key, analytics in self.query_analytics.items():
                if analytics.query_id == query_id:
                    query_key = key
                    break
            
            if query_key:
                analytics = self.query_analytics[query_key]
                
                if interaction_type == "document_viewed":
                    analytics.documents_viewed += 1
                elif interaction_type == "document_saved":
                    analytics.documents_saved += 1
                elif interaction_type == "research_completed":
                    analytics.successful_research = True
            
            # Update user profile
            await self._record_user_interaction_in_profile(user_id, interaction_type, metadata)
            
        except Exception as e:
            logger.error(f"Failed to record user interaction: {str(e)}")
    
    async def record_session(self, session: ResearchSession):
        """Record research session"""
        try:
            self.sessions.append(session)
            
            # Update user profile with session data
            if session.user_id not in self.user_profiles:
                self.user_profiles[session.user_id] = UserResearchProfile(user_id=session.user_id)
            
            profile = self.user_profiles[session.user_id]
            profile.total_sessions += 1
            
            # Update session duration
            if session.session_end:
                session_duration = (session.session_end - session.session_start).total_seconds() / 60
                total_duration = profile.average_session_duration_minutes * (profile.total_sessions - 1) + session_duration
                profile.average_session_duration_minutes = total_duration / profile.total_sessions
            
            # Update temporal patterns
            start_hour = session.session_start.hour
            profile.active_hours[start_hour] = profile.active_hours.get(start_hour, 0) + 1
            
            start_day = session.session_start.strftime("%A")
            profile.active_days[start_day] = profile.active_days.get(start_day, 0) + 1
            
            profile.last_updated = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to record session: {str(e)}")
    
    async def get_user_profile(self, user_id: UUID) -> Optional[UserResearchProfile]:
        """Get user research profile"""
        profile = self.user_profiles.get(user_id)
        
        if profile:
            # Generate insights and recommendations
            await self._generate_user_insights(profile)
        
        return profile
    
    async def get_query_analytics(self, query_text: Optional[str] = None) -> List[QueryAnalytics]:
        """Get query analytics, optionally filtered by query text"""
        if query_text:
            return [
                analytics for analytics in self.query_analytics.values()
                if query_text.lower() in analytics.query_text.lower()
            ]
        
        return list(self.query_analytics.values())
    
    async def get_system_performance_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> SystemPerformanceMetrics:
        """Get system-wide performance metrics for time period"""
        try:
            metrics = SystemPerformanceMetrics(
                metric_period_start=start_date,
                metric_period_end=end_date
            )
            
            # Query metrics
            relevant_queries = [
                analytics for analytics in self.query_analytics.values()
                if start_date <= analytics.last_executed <= end_date
            ]
            
            metrics.total_queries_executed = sum(q.execution_count for q in relevant_queries)
            metrics.unique_queries = len(relevant_queries)
            
            if relevant_queries:
                # Success rate calculation
                successful_queries = sum(1 for q in relevant_queries if q.successful_research)
                metrics.query_success_rate = successful_queries / len(relevant_queries)
                
                # Response time metrics
                all_response_times = []
                for analytics in relevant_queries:
                    all_response_times.extend([analytics.average_response_time_ms] * analytics.execution_count)
                
                if all_response_times:
                    metrics.average_response_time_ms = np.mean(all_response_times)
                    metrics.p95_response_time_ms = np.percentile(all_response_times, 95)
                    metrics.p99_response_time_ms = np.percentile(all_response_times, 99)
            
            # Provider metrics
            for provider, api_metrics in self.provider_metrics.items():
                metrics.provider_performance[provider.value] = {
                    'average_response_time': api_metrics.average_response_time,
                    'error_rate': api_metrics.error_rate,
                    'total_calls': api_metrics.api_calls
                }
                metrics.provider_error_rates[provider.value] = api_metrics.error_rate
            
            # Cache metrics (would be populated from cache system)
            metrics.cache_hit_ratio = 0.0  # Would get from cache system
            
            # Cost metrics
            metrics.total_api_costs = sum(m.total_cost for m in self.provider_metrics.values())
            if metrics.total_queries_executed > 0:
                metrics.cost_per_query = metrics.total_api_costs / metrics.total_queries_executed
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to generate system performance metrics: {str(e)}")
            return SystemPerformanceMetrics(
                metric_period_start=start_date,
                metric_period_end=end_date
            )
    
    async def analyze_research_trends(
        self,
        trend_type: str,
        time_period: str = "weekly",
        lookback_days: int = 30
    ) -> ResearchTrend:
        """Analyze research trends over time"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=lookback_days)
            
            trend = ResearchTrend(
                trend_type=trend_type,
                time_period=time_period
            )
            
            if trend_type == "query_popularity":
                await self._analyze_query_popularity_trend(trend, start_date, end_date)
            elif trend_type == "jurisdiction_focus":
                await self._analyze_jurisdiction_trend(trend, start_date, end_date)
            elif trend_type == "document_type_usage":
                await self._analyze_document_type_trend(trend, start_date, end_date)
            
            # Calculate trend direction and strength
            if len(trend.data_points) >= 2:
                values = [point['value'] for point in trend.data_points]
                trend.trend_direction, trend.trend_strength = self._calculate_trend_metrics(values)
            
            return trend
            
        except Exception as e:
            logger.error(f"Failed to analyze research trends: {str(e)}")
            return ResearchTrend(trend_type=trend_type, time_period=time_period)
    
    async def generate_cost_analysis(
        self,
        start_date: datetime,
        end_date: datetime,
        monthly_budget: Optional[float] = None
    ) -> CostAnalysis:
        """Generate comprehensive cost analysis"""
        try:
            analysis = CostAnalysis(
                analysis_period_start=start_date,
                analysis_period_end=end_date,
                monthly_budget=monthly_budget
            )
            
            # Calculate total costs from provider metrics
            for provider, metrics in self.provider_metrics.items():
                if provider == ResearchProvider.WESTLAW:
                    analysis.westlaw_cost = metrics.total_cost
                elif provider == ResearchProvider.LEXISNEXIS:
                    analysis.lexisnexis_cost = metrics.total_cost
            
            analysis.total_cost = analysis.westlaw_cost + analysis.lexisnexis_cost
            
            # Calculate efficiency metrics
            relevant_queries = [
                analytics for analytics in self.query_analytics.values()
                if start_date <= analytics.last_executed <= end_date
            ]
            
            total_queries = sum(q.execution_count for q in relevant_queries)
            successful_queries = sum(1 for q in relevant_queries if q.successful_research)
            
            if total_queries > 0:
                analysis.cost_per_query = analysis.total_cost / total_queries
            
            if successful_queries > 0:
                analysis.cost_per_successful_research = analysis.total_cost / successful_queries
            
            # User cost breakdown
            for user_id, profile in self.user_profiles.items():
                user_cost = profile.total_research_cost
                if user_cost > 0:
                    analysis.cost_by_user[str(user_id)] = user_cost
            
            # Identify high-cost users (top 20%)
            if analysis.cost_by_user:
                sorted_users = sorted(analysis.cost_by_user.items(), key=lambda x: x[1], reverse=True)
                top_20_percent = max(1, len(sorted_users) // 5)
                analysis.high_cost_users = [user_id for user_id, cost in sorted_users[:top_20_percent]]
            
            # Budget tracking
            if monthly_budget:
                analysis.budget_utilization = min(analysis.total_cost / monthly_budget, 1.0)
                
                # Project monthly cost based on usage pattern
                days_in_period = (end_date - start_date).days
                daily_cost = analysis.total_cost / days_in_period if days_in_period > 0 else 0
                analysis.projected_monthly_cost = daily_cost * 30
            
            # Generate optimization recommendations
            analysis.optimization_recommendations = await self._generate_cost_optimization_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to generate cost analysis: {str(e)}")
            return CostAnalysis(
                analysis_period_start=start_date,
                analysis_period_end=end_date
            )
    
    async def get_popular_queries(self, limit: int = 10) -> List[QueryAnalytics]:
        """Get most popular queries by execution count"""
        return sorted(
            self.query_analytics.values(),
            key=lambda q: q.execution_count,
            reverse=True
        )[:limit]
    
    async def get_research_effectiveness_metrics(self) -> Dict[str, float]:
        """Get overall research effectiveness metrics"""
        try:
            if not self.query_analytics:
                return {}
            
            total_queries = len(self.query_analytics)
            successful_queries = sum(1 for q in self.query_analytics.values() if q.successful_research)
            
            total_documents_viewed = sum(q.documents_viewed for q in self.query_analytics.values())
            total_documents_saved = sum(q.documents_saved for q in self.query_analytics.values())
            
            metrics = {
                "research_success_rate": successful_queries / total_queries if total_queries > 0 else 0.0,
                "average_documents_per_query": total_documents_viewed / total_queries if total_queries > 0 else 0.0,
                "document_save_rate": total_documents_saved / total_documents_viewed if total_documents_viewed > 0 else 0.0,
                "query_refinement_rate": 0.0,  # Would calculate based on similar queries
                "citation_discovery_efficiency": 0.0  # Would calculate based on citation extraction
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate research effectiveness metrics: {str(e)}")
            return {}
    
    def _generate_query_key(self, query: ResearchQuery) -> str:
        """Generate unique key for query"""
        # Normalize query for consistent keying
        normalized_text = query.query_text.strip().lower()
        doc_types = sorted([dt.value for dt in query.document_types])
        jurisdictions = sorted(query.jurisdictions)
        
        key_components = [
            normalized_text,
            query.search_type.value,
            "|".join(doc_types),
            "|".join(jurisdictions)
        ]
        
        return ":".join(key_components)
    
    async def _update_user_profile(
        self,
        user_id: UUID,
        query: ResearchQuery,
        result: SearchResult
    ):
        """Update user research profile with query data"""
        try:
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = UserResearchProfile(user_id=user_id)
            
            profile = self.user_profiles[user_id]
            profile.total_queries += 1
            
            # Update query patterns
            search_type = query.search_type.value
            profile.common_query_types[search_type] = profile.common_query_types.get(search_type, 0) + 1
            
            # Update document type preferences
            for doc_type in query.document_types:
                profile.preferred_document_types[doc_type.value] = (
                    profile.preferred_document_types.get(doc_type.value, 0) + 1
                )
            
            # Update jurisdiction focus
            for jurisdiction in query.jurisdictions:
                profile.jurisdiction_focus[jurisdiction] = (
                    profile.jurisdiction_focus.get(jurisdiction, 0) + 1
                )
            
            # Update practice area focus
            if query.practice_area:
                profile.practice_area_focus[query.practice_area] = (
                    profile.practice_area_focus.get(query.practice_area, 0) + 1
                )
            
            # Update provider usage
            for provider in result.providers_searched:
                provider_key = provider.value
                profile.provider_usage[provider_key] = (
                    profile.provider_usage.get(provider_key, 0) + 1
                )
            
            # Update research effectiveness
            profile.average_documents_per_query = (
                (profile.average_documents_per_query * (profile.total_queries - 1) + result.results_returned) /
                profile.total_queries
            )
            
            profile.last_updated = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to update user profile: {str(e)}")
    
    async def _record_user_interaction_in_profile(
        self,
        user_id: UUID,
        interaction_type: str,
        metadata: Optional[Dict[str, Any]]
    ):
        """Record user interaction in profile"""
        try:
            if user_id not in self.user_profiles:
                return
            
            profile = self.user_profiles[user_id]
            
            # Update based on interaction type
            if interaction_type == "research_completed":
                # Update success rate
                successful_research = profile.research_success_rate * profile.total_queries + 1
                profile.research_success_rate = successful_research / (profile.total_queries + 1)
            
            profile.last_updated = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to record interaction in profile: {str(e)}")
    
    async def _generate_user_insights(self, profile: UserResearchProfile):
        """Generate insights and recommendations for user"""
        try:
            insights = []
            recommendations = []
            
            # Query pattern insights
            if profile.common_query_types:
                most_common_type = max(profile.common_query_types, key=profile.common_query_types.get)
                insights.append(f"Most common search type: {most_common_type}")
            
            # Jurisdiction focus insights
            if profile.jurisdiction_focus:
                top_jurisdiction = max(profile.jurisdiction_focus, key=profile.jurisdiction_focus.get)
                insights.append(f"Primary jurisdiction focus: {top_jurisdiction}")
            
            # Provider usage insights
            if profile.provider_usage:
                preferred_provider = max(profile.provider_usage, key=profile.provider_usage.get)
                insights.append(f"Preferred research provider: {preferred_provider}")
            
            # Effectiveness insights
            if profile.research_success_rate < 0.5:
                recommendations.append("Consider refining search strategies to improve research success")
            
            if profile.average_session_duration_minutes > 120:
                recommendations.append("Sessions are quite long - consider breaking research into smaller focused queries")
            
            # Cost efficiency recommendations
            if profile.cost_per_successful_research > 50:  # Arbitrary threshold
                recommendations.append("Research costs are high - consider using more targeted queries")
            
            profile.research_insights = insights
            profile.recommendations = recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate user insights: {str(e)}")
    
    async def _analyze_query_popularity_trend(
        self,
        trend: ResearchTrend,
        start_date: datetime,
        end_date: datetime
    ):
        """Analyze query popularity trends"""
        try:
            # Group queries by time period
            period_counts = defaultdict(int)
            
            for analytics in self.query_analytics.values():
                if start_date <= analytics.last_executed <= end_date:
                    period_key = self._get_period_key(analytics.last_executed, trend.time_period)
                    period_counts[period_key] += analytics.execution_count
            
            # Convert to data points
            for period, count in sorted(period_counts.items()):
                trend.data_points.append({
                    'timestamp': period,
                    'value': count,
                    'metadata': {'query_count': count}
                })
            
        except Exception as e:
            logger.error(f"Failed to analyze query popularity trend: {str(e)}")
    
    async def _analyze_jurisdiction_trend(
        self,
        trend: ResearchTrend,
        start_date: datetime,
        end_date: datetime
    ):
        """Analyze jurisdiction focus trends"""
        # Implementation would analyze jurisdiction usage over time
        pass
    
    async def _analyze_document_type_trend(
        self,
        trend: ResearchTrend,
        start_date: datetime,
        end_date: datetime
    ):
        """Analyze document type usage trends"""
        # Implementation would analyze document type preferences over time
        pass
    
    def _get_period_key(self, timestamp: datetime, period_type: str) -> str:
        """Generate period key for trend analysis"""
        if period_type == "daily":
            return timestamp.strftime("%Y-%m-%d")
        elif period_type == "weekly":
            # Get week start (Monday)
            week_start = timestamp - timedelta(days=timestamp.weekday())
            return week_start.strftime("%Y-W%U")
        elif period_type == "monthly":
            return timestamp.strftime("%Y-%m")
        else:
            return timestamp.strftime("%Y-%m-%d")
    
    def _calculate_trend_metrics(self, values: List[float]) -> Tuple[str, float]:
        """Calculate trend direction and strength"""
        try:
            if len(values) < 2:
                return "stable", 0.0
            
            # Simple linear regression to determine trend
            x = np.arange(len(values))
            coefficients = np.polyfit(x, values, 1)
            slope = coefficients[0]
            
            # Determine direction
            if slope > 0.1:
                direction = "increasing"
            elif slope < -0.1:
                direction = "decreasing"
            else:
                direction = "stable"
            
            # Calculate strength (normalized slope)
            strength = min(abs(slope) / (max(values) - min(values) + 1), 1.0)
            
            return direction, strength
            
        except Exception as e:
            logger.error(f"Failed to calculate trend metrics: {str(e)}")
            return "stable", 0.0
    
    async def _generate_cost_optimization_recommendations(
        self,
        analysis: CostAnalysis
    ) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        try:
            # High-level cost recommendations
            if analysis.cost_per_query > 5.0:  # Arbitrary threshold
                recommendations.append("Consider implementing more aggressive caching to reduce API calls")
            
            if analysis.westlaw_cost > analysis.lexisnexis_cost * 1.5:
                recommendations.append("Evaluate shifting some queries to LexisNexis to balance costs")
            elif analysis.lexisnexis_cost > analysis.westlaw_cost * 1.5:
                recommendations.append("Consider shifting some queries to Westlaw to optimize costs")
            
            # User-based recommendations
            if len(analysis.high_cost_users) > 0:
                recommendations.append("Provide additional training to high-cost users on efficient search strategies")
            
            # Budget recommendations
            if analysis.budget_utilization and analysis.budget_utilization > 0.8:
                recommendations.append("Consider implementing query quotas or approval workflows for expensive searches")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate cost optimization recommendations: {str(e)}")
            return []