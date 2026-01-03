"""
Advanced usage monitoring system for legal research platforms.
Tracks user behavior, resource utilization, and identifies optimization opportunities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, deque
import statistics
import uuid

from ..types.unified_types import UnifiedDocument, ContentType
from .cost_tracker import ResourceType, CostEvent


class ActivityType(Enum):
    """Types of user activities to monitor."""
    SEARCH = "search"
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DOWNLOAD = "document_download"
    CITATION_CHECK = "citation_check"
    SHEPARDIZE = "shepardize"
    AI_ANALYSIS = "ai_analysis"
    EXPORT = "export"
    PRINT = "print"
    BOOKMARK = "bookmark"
    SHARE = "share"
    LOGIN = "login"
    LOGOUT = "logout"
    SESSION_TIMEOUT = "session_timeout"


class UsagePattern(Enum):
    """Types of usage patterns detected."""
    EFFICIENT_SEARCHER = "efficient_searcher"      # Few searches, high relevance
    EXPLORATORY_USER = "exploratory_user"          # Many searches, lower relevance
    DOCUMENT_FOCUSED = "document_focused"          # Mainly document access
    HEAVY_ANALYZER = "heavy_analyzer"              # Uses advanced analysis features
    COST_CONSCIOUS = "cost_conscious"              # Uses free/low-cost resources
    PREMIUM_USER = "premium_user"                  # Uses expensive resources frequently
    BATCH_PROCESSOR = "batch_processor"            # Processes many documents at once
    CASUAL_USER = "casual_user"                    # Infrequent, basic usage


class EfficiencyLevel(Enum):
    """User efficiency levels."""
    HIGHLY_EFFICIENT = "highly_efficient"         # >80% relevance rate
    EFFICIENT = "efficient"                       # 60-80% relevance rate
    MODERATE = "moderate"                          # 40-60% relevance rate
    INEFFICIENT = "inefficient"                   # 20-40% relevance rate
    HIGHLY_INEFFICIENT = "highly_inefficient"     # <20% relevance rate


@dataclass
class ActivityEvent:
    """Individual user activity event."""
    event_id: str
    timestamp: datetime
    user_id: str
    session_id: str
    activity_type: ActivityType
    
    # Activity details
    resource_type: Optional[ResourceType] = None
    query_text: Optional[str] = None
    document_id: Optional[str] = None
    duration: Optional[float] = None  # seconds
    
    # Results and effectiveness
    results_count: int = 0
    relevant_results: int = 0
    success: bool = True
    
    # Context
    matter_id: Optional[str] = None
    client_id: Optional[str] = None
    practice_area: Optional[str] = None
    
    # Technical details
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    page_url: Optional[str] = None
    referrer: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserSession:
    """User session information."""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Session metrics
    total_activities: int = 0
    total_searches: int = 0
    total_documents_viewed: int = 0
    total_duration: float = 0.0
    
    # Effectiveness
    successful_activities: int = 0
    relevance_score: float = 0.0
    
    # Resources used
    resources_used: Set[ResourceType] = field(default_factory=set)
    total_cost: float = 0.0
    
    # Context
    matters_accessed: Set[str] = field(default_factory=set)
    clients_accessed: Set[str] = field(default_factory=set)
    
    # Session quality indicators
    bounce_rate: float = 0.0  # Single activity sessions
    depth_score: float = 0.0  # Average activities per topic
    focus_score: float = 0.0  # Concentration on specific matters


@dataclass
class UserProfile:
    """Comprehensive user usage profile."""
    user_id: str
    profile_date: datetime
    
    # Basic metrics
    total_sessions: int = 0
    total_activities: int = 0
    average_session_duration: float = 0.0
    
    # Usage patterns
    primary_pattern: Optional[UsagePattern] = None
    secondary_patterns: List[UsagePattern] = field(default_factory=list)
    
    # Efficiency metrics
    efficiency_level: EfficiencyLevel = EfficiencyLevel.MODERATE
    overall_relevance_rate: float = 0.0
    cost_efficiency: float = 0.0  # Relevant results per dollar spent
    
    # Preferences
    preferred_resources: List[ResourceType] = field(default_factory=list)
    preferred_activities: List[ActivityType] = field(default_factory=list)
    peak_usage_hours: List[int] = field(default_factory=list)
    
    # Practice areas
    primary_practice_areas: List[str] = field(default_factory=list)
    
    # Behavioral indicators
    search_sophistication: float = 0.0  # Complexity of searches
    exploration_tendency: float = 0.0   # Tendency to explore vs. focused search
    cost_awareness: float = 0.0         # Preference for cost-effective resources
    
    # Recommendations
    efficiency_recommendations: List[str] = field(default_factory=list)
    cost_optimization_tips: List[str] = field(default_factory=list)
    training_suggestions: List[str] = field(default_factory=list)


@dataclass
class UsageAnalytics:
    """System-wide usage analytics."""
    analysis_period_start: datetime
    analysis_period_end: datetime
    
    # Overall statistics
    total_users: int = 0
    total_sessions: int = 0
    total_activities: int = 0
    total_cost: float = 0.0
    
    # Efficiency metrics
    system_efficiency: float = 0.0
    average_relevance_rate: float = 0.0
    cost_per_relevant_result: float = 0.0
    
    # Resource utilization
    resource_usage: Dict[ResourceType, int] = field(default_factory=dict)
    resource_efficiency: Dict[ResourceType, float] = field(default_factory=dict)
    resource_costs: Dict[ResourceType, float] = field(default_factory=dict)
    
    # User patterns
    pattern_distribution: Dict[UsagePattern, int] = field(default_factory=dict)
    efficiency_distribution: Dict[EfficiencyLevel, int] = field(default_factory=dict)
    
    # Time patterns
    hourly_usage: Dict[int, int] = field(default_factory=dict)
    daily_usage: Dict[str, int] = field(default_factory=dict)  # day of week
    
    # Top performers and insights
    most_efficient_users: List[str] = field(default_factory=list)
    highest_cost_users: List[str] = field(default_factory=list)
    optimization_opportunities: List[str] = field(default_factory=list)


class UsageMonitor:
    """
    Comprehensive usage monitoring system for legal research.
    
    Tracks user behavior, analyzes patterns, identifies inefficiencies,
    and provides recommendations for optimization.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Storage
        self.activity_events: List[ActivityEvent] = []
        self.user_sessions: Dict[str, UserSession] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        
        # Active sessions tracking
        self.active_sessions: Dict[str, UserSession] = {}
        self.session_activity_buffer: Dict[str, deque] = {}
        
        # Configuration
        self.session_timeout = 30 * 60  # 30 minutes
        self.profile_refresh_interval = 24 * 60 * 60  # 24 hours
        self.activity_buffer_size = 1000
        
        # Pattern recognition thresholds
        self.efficiency_thresholds = {
            EfficiencyLevel.HIGHLY_EFFICIENT: 0.8,
            EfficiencyLevel.EFFICIENT: 0.6,
            EfficiencyLevel.MODERATE: 0.4,
            EfficiencyLevel.INEFFICIENT: 0.2
        }
    
    async def track_activity(self, 
                           user_id: str,
                           session_id: str,
                           activity_type: ActivityType,
                           **kwargs) -> ActivityEvent:
        """
        Track a user activity event.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            activity_type: Type of activity
            **kwargs: Additional activity data
            
        Returns:
            ActivityEvent record
        """
        
        # Create activity event
        event = ActivityEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            activity_type=activity_type,
            resource_type=kwargs.get('resource_type'),
            query_text=kwargs.get('query_text'),
            document_id=kwargs.get('document_id'),
            duration=kwargs.get('duration'),
            results_count=kwargs.get('results_count', 0),
            relevant_results=kwargs.get('relevant_results', 0),
            success=kwargs.get('success', True),
            matter_id=kwargs.get('matter_id'),
            client_id=kwargs.get('client_id'),
            practice_area=kwargs.get('practice_area'),
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
            page_url=kwargs.get('page_url'),
            referrer=kwargs.get('referrer'),
            metadata=kwargs.get('metadata', {})
        )
        
        # Store event
        self.activity_events.append(event)
        
        # Update session tracking
        await self._update_session_tracking(event)
        
        # Buffer for real-time analysis
        if session_id not in self.session_activity_buffer:
            self.session_activity_buffer[session_id] = deque(maxlen=self.activity_buffer_size)
        self.session_activity_buffer[session_id].append(event)
        
        self.logger.debug(f"Tracked activity: {activity_type.value} for user {user_id}")
        
        return event
    
    async def _update_session_tracking(self, event: ActivityEvent):
        """Update session tracking with new activity."""
        
        session_id = event.session_id
        user_id = event.user_id
        
        # Get or create session
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = UserSession(
                session_id=session_id,
                user_id=user_id,
                start_time=event.timestamp
            )
        
        session = self.active_sessions[session_id]
        
        # Update session metrics
        session.total_activities += 1
        
        if event.activity_type == ActivityType.SEARCH:
            session.total_searches += 1
        elif event.activity_type == ActivityType.DOCUMENT_VIEW:
            session.total_documents_viewed += 1
        
        if event.duration:
            session.total_duration += event.duration
        
        if event.success:
            session.successful_activities += 1
        
        if event.resource_type:
            session.resources_used.add(event.resource_type)
        
        if event.matter_id:
            session.matters_accessed.add(event.matter_id)
        
        if event.client_id:
            session.clients_accessed.add(event.client_id)
        
        # Update relevance score
        if event.results_count > 0:
            session_relevance = event.relevant_results / event.results_count
            # Weighted average with existing relevance
            total_results = sum(e.results_count for e in self.session_activity_buffer[session_id])
            if total_results > 0:
                weight = event.results_count / total_results
                session.relevance_score = (session.relevance_score * (1 - weight)) + (session_relevance * weight)
        
        # Update session end time
        session.end_time = event.timestamp
    
    async def end_session(self, session_id: str) -> Optional[UserSession]:
        """End a user session and finalize metrics."""
        
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        # Finalize session metrics
        await self._finalize_session_metrics(session)
        
        # Move to completed sessions
        self.user_sessions[session_id] = session
        
        # Clean up active session
        del self.active_sessions[session_id]
        
        # Clean up activity buffer after a delay
        if session_id in self.session_activity_buffer:
            del self.session_activity_buffer[session_id]
        
        self.logger.info(f"Ended session {session_id} for user {session.user_id}")
        
        return session
    
    async def _finalize_session_metrics(self, session: UserSession):
        """Finalize session metrics calculations."""
        
        if session.total_activities == 0:
            return
        
        # Calculate bounce rate (sessions with only one activity)
        session.bounce_rate = 1.0 if session.total_activities == 1 else 0.0
        
        # Calculate depth score (activities per matter/topic)
        matters_count = len(session.matters_accessed) if session.matters_accessed else 1
        session.depth_score = session.total_activities / matters_count
        
        # Calculate focus score (concentration on specific matters)
        if session.matters_accessed:
            session.focus_score = len(session.matters_accessed) / session.total_activities
        else:
            session.focus_score = 1.0  # Assume focused if no matter tracking
        
        # Update total session duration
        if session.end_time and session.start_time:
            total_session_time = (session.end_time - session.start_time).total_seconds()
            session.total_duration = max(session.total_duration, total_session_time)
    
    async def check_session_timeouts(self):
        """Check for timed out sessions."""
        
        cutoff_time = datetime.now() - timedelta(seconds=self.session_timeout)
        
        timed_out_sessions = []
        for session_id, session in self.active_sessions.items():
            if session.end_time and session.end_time < cutoff_time:
                timed_out_sessions.append(session_id)
        
        # End timed out sessions
        for session_id in timed_out_sessions:
            await self.track_activity(
                user_id=self.active_sessions[session_id].user_id,
                session_id=session_id,
                activity_type=ActivityType.SESSION_TIMEOUT
            )
            await self.end_session(session_id)
    
    async def analyze_user_patterns(self, user_id: str) -> UserProfile:
        """Analyze usage patterns for a specific user."""
        
        # Get user's activities
        user_activities = [
            event for event in self.activity_events
            if event.user_id == user_id
        ]
        
        # Get user's sessions
        user_sessions = [
            session for session in self.user_sessions.values()
            if session.user_id == user_id
        ]
        
        if not user_activities:
            return UserProfile(
                user_id=user_id,
                profile_date=datetime.now()
            )
        
        # Create user profile
        profile = UserProfile(
            user_id=user_id,
            profile_date=datetime.now(),
            total_sessions=len(user_sessions),
            total_activities=len(user_activities)
        )
        
        # Calculate basic metrics
        if user_sessions:
            profile.average_session_duration = statistics.mean(
                session.total_duration for session in user_sessions
            )
        
        # Analyze usage patterns
        profile.primary_pattern = await self._identify_primary_usage_pattern(user_activities, user_sessions)
        profile.secondary_patterns = await self._identify_secondary_patterns(user_activities, user_sessions)
        
        # Calculate efficiency level
        profile.efficiency_level = await self._calculate_efficiency_level(user_activities)
        
        # Calculate overall relevance rate
        total_results = sum(event.results_count for event in user_activities)
        total_relevant = sum(event.relevant_results for event in user_activities)
        if total_results > 0:
            profile.overall_relevance_rate = total_relevant / total_results
        
        # Identify preferences
        profile.preferred_resources = await self._identify_preferred_resources(user_activities)
        profile.preferred_activities = await self._identify_preferred_activities(user_activities)
        profile.peak_usage_hours = await self._identify_peak_usage_hours(user_activities)
        profile.primary_practice_areas = await self._identify_practice_areas(user_activities)
        
        # Calculate behavioral indicators
        profile.search_sophistication = await self._calculate_search_sophistication(user_activities)
        profile.exploration_tendency = await self._calculate_exploration_tendency(user_activities)
        profile.cost_awareness = await self._calculate_cost_awareness(user_activities)
        
        # Generate recommendations
        profile.efficiency_recommendations = await self._generate_efficiency_recommendations(profile, user_activities)
        profile.cost_optimization_tips = await self._generate_cost_optimization_tips(profile, user_activities)
        profile.training_suggestions = await self._generate_training_suggestions(profile, user_activities)
        
        # Store profile
        self.user_profiles[user_id] = profile
        
        return profile
    
    async def _identify_primary_usage_pattern(self, 
                                            activities: List[ActivityEvent],
                                            sessions: List[UserSession]) -> Optional[UsagePattern]:
        """Identify the primary usage pattern for a user."""
        
        if not activities:
            return None
        
        # Calculate pattern indicators
        total_searches = len([a for a in activities if a.activity_type == ActivityType.SEARCH])
        total_documents = len([a for a in activities if a.activity_type == ActivityType.DOCUMENT_VIEW])
        total_analysis = len([a for a in activities if a.activity_type in [ActivityType.SHEPARDIZE, ActivityType.AI_ANALYSIS]])
        
        # Calculate relevance rate
        total_results = sum(a.results_count for a in activities)
        total_relevant = sum(a.relevant_results for a in activities)
        relevance_rate = total_relevant / total_results if total_results > 0 else 0
        
        # Calculate resource cost preference
        premium_usage = len([a for a in activities if a.resource_type in [ResourceType.WESTLAW, ResourceType.LEXIS]])
        free_usage = len([a for a in activities if a.resource_type == ResourceType.GOOGLE_SCHOLAR])
        
        # Pattern detection logic
        if total_searches > 0 and relevance_rate > 0.7 and total_searches / len(activities) < 0.3:
            return UsagePattern.EFFICIENT_SEARCHER
        elif total_searches > total_documents and relevance_rate < 0.5:
            return UsagePattern.EXPLORATORY_USER
        elif total_documents > total_searches * 2:
            return UsagePattern.DOCUMENT_FOCUSED
        elif total_analysis > len(activities) * 0.3:
            return UsagePattern.HEAVY_ANALYZER
        elif free_usage > premium_usage:
            return UsagePattern.COST_CONSCIOUS
        elif premium_usage > free_usage and premium_usage > len(activities) * 0.7:
            return UsagePattern.PREMIUM_USER
        elif len(sessions) > 0 and sum(s.total_documents_viewed for s in sessions) / len(sessions) > 20:
            return UsagePattern.BATCH_PROCESSOR
        else:
            return UsagePattern.CASUAL_USER
    
    async def _identify_secondary_patterns(self, 
                                         activities: List[ActivityEvent],
                                         sessions: List[UserSession]) -> List[UsagePattern]:
        """Identify secondary usage patterns."""
        
        # This is a simplified implementation
        # In practice, would use more sophisticated pattern recognition
        patterns = []
        
        total_activities = len(activities)
        if total_activities == 0:
            return patterns
        
        # Check for multiple pattern indicators
        analysis_ratio = len([a for a in activities if a.activity_type in [ActivityType.SHEPARDIZE, ActivityType.AI_ANALYSIS]]) / total_activities
        if analysis_ratio > 0.2:
            patterns.append(UsagePattern.HEAVY_ANALYZER)
        
        cost_conscious_ratio = len([a for a in activities if a.resource_type == ResourceType.GOOGLE_SCHOLAR]) / total_activities
        if cost_conscious_ratio > 0.4:
            patterns.append(UsagePattern.COST_CONSCIOUS)
        
        return patterns[:3]  # Limit to 3 secondary patterns
    
    async def _calculate_efficiency_level(self, activities: List[ActivityEvent]) -> EfficiencyLevel:
        """Calculate user efficiency level."""
        
        if not activities:
            return EfficiencyLevel.MODERATE
        
        # Calculate overall relevance rate
        total_results = sum(a.results_count for a in activities)
        total_relevant = sum(a.relevant_results for a in activities)
        
        if total_results == 0:
            return EfficiencyLevel.MODERATE
        
        relevance_rate = total_relevant / total_results
        
        # Determine efficiency level
        for level, threshold in self.efficiency_thresholds.items():
            if relevance_rate >= threshold:
                return level
        
        return EfficiencyLevel.HIGHLY_INEFFICIENT
    
    async def _identify_preferred_resources(self, activities: List[ActivityEvent]) -> List[ResourceType]:
        """Identify user's preferred resources."""
        
        resource_counts = defaultdict(int)
        for activity in activities:
            if activity.resource_type:
                resource_counts[activity.resource_type] += 1
        
        # Sort by usage count
        sorted_resources = sorted(resource_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [resource for resource, count in sorted_resources[:5]]
    
    async def _identify_preferred_activities(self, activities: List[ActivityEvent]) -> List[ActivityType]:
        """Identify user's preferred activities."""
        
        activity_counts = defaultdict(int)
        for activity in activities:
            activity_counts[activity.activity_type] += 1
        
        # Sort by usage count
        sorted_activities = sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [activity for activity, count in sorted_activities[:5]]
    
    async def _identify_peak_usage_hours(self, activities: List[ActivityEvent]) -> List[int]:
        """Identify peak usage hours for a user."""
        
        hour_counts = defaultdict(int)
        for activity in activities:
            hour_counts[activity.timestamp.hour] += 1
        
        if not hour_counts:
            return []
        
        # Find hours with above-average usage
        average_usage = sum(hour_counts.values()) / len(hour_counts)
        peak_hours = [hour for hour, count in hour_counts.items() if count > average_usage * 1.2]
        
        return sorted(peak_hours)
    
    async def _identify_practice_areas(self, activities: List[ActivityEvent]) -> List[str]:
        """Identify primary practice areas."""
        
        area_counts = defaultdict(int)
        for activity in activities:
            if activity.practice_area:
                area_counts[activity.practice_area] += 1
        
        # Sort by frequency
        sorted_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [area for area, count in sorted_areas[:3]]
    
    async def _calculate_search_sophistication(self, activities: List[ActivityEvent]) -> float:
        """Calculate search sophistication score."""
        
        search_activities = [a for a in activities if a.activity_type == ActivityType.SEARCH and a.query_text]
        
        if not search_activities:
            return 0.5
        
        # Analyze query complexity
        total_sophistication = 0.0
        for activity in search_activities:
            query = activity.query_text
            
            # Simple sophistication indicators
            sophistication = 0.0
            
            # Length bonus
            word_count = len(query.split())
            if word_count > 3:
                sophistication += 0.2
            if word_count > 6:
                sophistication += 0.2
            
            # Boolean operators
            if any(op in query.upper() for op in ['AND', 'OR', 'NOT']):
                sophistication += 0.3
            
            # Quotes (exact phrases)
            if '"' in query:
                sophistication += 0.2
            
            # Field searches (simplified detection)
            if any(field in query.lower() for field in ['title:', 'author:', 'date:', 'court:']):
                sophistication += 0.3
            
            # Parentheses (grouping)
            if '(' in query and ')' in query:
                sophistication += 0.2
            
            total_sophistication += min(1.0, sophistication)
        
        return total_sophistication / len(search_activities)
    
    async def _calculate_exploration_tendency(self, activities: List[ActivityEvent]) -> float:
        """Calculate exploration vs focused search tendency."""
        
        search_activities = [a for a in activities if a.activity_type == ActivityType.SEARCH]
        
        if len(search_activities) < 2:
            return 0.5
        
        # Calculate search diversity (different queries)
        unique_queries = set()
        for activity in search_activities:
            if activity.query_text:
                # Normalize query for comparison
                normalized = activity.query_text.lower().strip()
                unique_queries.add(normalized)
        
        # High exploration = many different queries
        exploration_score = len(unique_queries) / len(search_activities)
        
        # Also consider results browsing behavior
        view_activities = [a for a in activities if a.activity_type == ActivityType.DOCUMENT_VIEW]
        if search_activities and view_activities:
            # High exploration = viewing many results per search
            view_per_search = len(view_activities) / len(search_activities)
            if view_per_search > 5:  # Viewing many results suggests exploration
                exploration_score = min(1.0, exploration_score + 0.2)
        
        return min(1.0, exploration_score)
    
    async def _calculate_cost_awareness(self, activities: List[ActivityEvent]) -> float:
        """Calculate cost awareness score."""
        
        if not activities:
            return 0.5
        
        # Count usage of different resource types
        free_resources = [ResourceType.GOOGLE_SCHOLAR, ResourceType.JUSTIA]
        premium_resources = [ResourceType.WESTLAW, ResourceType.LEXIS, ResourceType.BLOOMBERG_LAW]
        
        free_usage = len([a for a in activities if a.resource_type in free_resources])
        premium_usage = len([a for a in activities if a.resource_type in premium_resources])
        
        total_resource_usage = free_usage + premium_usage
        
        if total_resource_usage == 0:
            return 0.5
        
        # Higher cost awareness = more use of free resources
        cost_awareness = free_usage / total_resource_usage
        
        return cost_awareness
    
    async def _generate_efficiency_recommendations(self, 
                                                 profile: UserProfile,
                                                 activities: List[ActivityEvent]) -> List[str]:
        """Generate efficiency improvement recommendations."""
        
        recommendations = []
        
        # Low relevance rate recommendations
        if profile.overall_relevance_rate < 0.5:
            recommendations.append("Improve search precision by using more specific terms and boolean operators")
            recommendations.append("Review search results more carefully before accessing documents")
        
        # Search sophistication recommendations
        if profile.search_sophistication < 0.3:
            recommendations.append("Learn advanced search techniques like field searches and boolean operators")
            recommendations.append("Use exact phrase searching with quotation marks for better precision")
        
        # Pattern-specific recommendations
        if profile.primary_pattern == UsagePattern.EXPLORATORY_USER:
            recommendations.append("Focus searches more narrowly to improve efficiency")
            recommendations.append("Use filters and advanced search options to refine results")
        elif profile.primary_pattern == UsagePattern.INEFFICIENT:
            recommendations.append("Consider training on legal research best practices")
            recommendations.append("Use research checklists to ensure thorough but efficient searches")
        
        return recommendations[:5]  # Limit to top 5
    
    async def _generate_cost_optimization_tips(self,
                                             profile: UserProfile,
                                             activities: List[ActivityEvent]) -> List[str]:
        """Generate cost optimization tips."""
        
        tips = []
        
        # Cost awareness tips
        if profile.cost_awareness < 0.3:
            tips.append("Consider using free resources like Google Scholar for initial research")
            tips.append("Use preview features before accessing full documents to avoid unnecessary costs")
        
        # Resource optimization
        if ResourceType.WESTLAW in profile.preferred_resources and ResourceType.LEXIS in profile.preferred_resources:
            tips.append("Consider standardizing on one primary premium resource to reduce subscription costs")
        
        # Usage pattern optimization
        if profile.primary_pattern == UsagePattern.PREMIUM_USER:
            tips.append("Supplement premium resources with free alternatives where appropriate")
            tips.append("Batch research tasks to maximize value from premium subscriptions")
        
        # Efficiency-based cost tips
        if profile.overall_relevance_rate < 0.4:
            tips.append("Improve search accuracy to reduce wasted premium resource usage")
        
        return tips[:5]
    
    async def _generate_training_suggestions(self,
                                           profile: UserProfile,
                                           activities: List[ActivityEvent]) -> List[str]:
        """Generate training suggestions."""
        
        suggestions = []
        
        # Efficiency-based suggestions
        if profile.efficiency_level in [EfficiencyLevel.INEFFICIENT, EfficiencyLevel.HIGHLY_INEFFICIENT]:
            suggestions.append("Basic legal research methodology training")
            suggestions.append("Boolean search techniques workshop")
        
        # Search sophistication suggestions
        if profile.search_sophistication < 0.4:
            suggestions.append("Advanced search operators and field searching")
            suggestions.append("Database-specific search training (Westlaw, Lexis)")
        
        # Pattern-specific suggestions
        if profile.primary_pattern == UsagePattern.EXPLORATORY_USER:
            suggestions.append("Focused research strategies training")
        elif profile.primary_pattern == UsagePattern.CASUAL_USER:
            suggestions.append("Legal research fundamentals course")
        
        # Cost awareness suggestions
        if profile.cost_awareness < 0.3:
            suggestions.append("Cost-effective research strategies training")
        
        return suggestions[:5]
    
    async def generate_system_analytics(self,
                                      start_date: datetime,
                                      end_date: datetime) -> UsageAnalytics:
        """Generate system-wide usage analytics."""
        
        # Filter activities by date range
        period_activities = [
            activity for activity in self.activity_events
            if start_date <= activity.timestamp <= end_date
        ]
        
        period_sessions = [
            session for session in self.user_sessions.values()
            if start_date <= session.start_time <= end_date
        ]
        
        analytics = UsageAnalytics(
            analysis_period_start=start_date,
            analysis_period_end=end_date
        )
        
        # Basic statistics
        analytics.total_users = len(set(activity.user_id for activity in period_activities))
        analytics.total_sessions = len(period_sessions)
        analytics.total_activities = len(period_activities)
        
        # Resource utilization
        for activity in period_activities:
            if activity.resource_type:
                resource = activity.resource_type
                analytics.resource_usage[resource] = analytics.resource_usage.get(resource, 0) + 1
        
        # Calculate efficiency metrics
        if period_activities:
            total_results = sum(a.results_count for a in period_activities)
            total_relevant = sum(a.relevant_results for a in period_activities)
            if total_results > 0:
                analytics.average_relevance_rate = total_relevant / total_results
        
        # Time patterns
        for activity in period_activities:
            hour = activity.timestamp.hour
            analytics.hourly_usage[hour] = analytics.hourly_usage.get(hour, 0) + 1
            
            day = activity.timestamp.strftime('%A')
            analytics.daily_usage[day] = analytics.daily_usage.get(day, 0) + 1
        
        # User pattern analysis
        for user_id in set(activity.user_id for activity in period_activities):
            profile = await self.analyze_user_patterns(user_id)
            if profile.primary_pattern:
                pattern = profile.primary_pattern
                analytics.pattern_distribution[pattern] = analytics.pattern_distribution.get(pattern, 0) + 1
            
            analytics.efficiency_distribution[profile.efficiency_level] = analytics.efficiency_distribution.get(profile.efficiency_level, 0) + 1
        
        # Identify optimization opportunities
        analytics.optimization_opportunities = await self._identify_system_optimization_opportunities(analytics, period_activities)
        
        return analytics
    
    async def _identify_system_optimization_opportunities(self,
                                                        analytics: UsageAnalytics,
                                                        activities: List[ActivityEvent]) -> List[str]:
        """Identify system-wide optimization opportunities."""
        
        opportunities = []
        
        # Low system efficiency
        if analytics.average_relevance_rate < 0.5:
            opportunities.append("System-wide search training needed to improve relevance rates")
        
        # Resource imbalance
        if analytics.resource_usage:
            total_usage = sum(analytics.resource_usage.values())
            for resource, usage in analytics.resource_usage.items():
                usage_percentage = usage / total_usage
                if resource in [ResourceType.WESTLAW, ResourceType.LEXIS] and usage_percentage > 0.8:
                    opportunities.append(f"Heavy reliance on {resource.value} - consider diversifying resources")
        
        # Pattern distribution insights
        if analytics.pattern_distribution.get(UsagePattern.INEFFICIENT, 0) > analytics.total_users * 0.3:
            opportunities.append("High percentage of inefficient users - implement training program")
        
        # Time-based optimization
        if analytics.hourly_usage:
            peak_hour = max(analytics.hourly_usage.keys(), key=lambda k: analytics.hourly_usage[k])
            peak_usage = analytics.hourly_usage[peak_hour]
            total_usage = sum(analytics.hourly_usage.values())
            if peak_usage > total_usage * 0.3:  # More than 30% usage in single hour
                opportunities.append(f"High usage concentration at {peak_hour}:00 - consider load balancing")
        
        return opportunities
    
    async def get_user_efficiency_ranking(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get ranking of most efficient users."""
        
        user_rankings = []
        
        for user_id in set(event.user_id for event in self.activity_events):
            user_activities = [e for e in self.activity_events if e.user_id == user_id]
            
            if not user_activities:
                continue
            
            # Calculate efficiency score
            total_results = sum(a.results_count for a in user_activities)
            total_relevant = sum(a.relevant_results for a in user_activities)
            
            if total_results > 0:
                efficiency = total_relevant / total_results
                user_rankings.append((user_id, efficiency))
        
        # Sort by efficiency
        user_rankings.sort(key=lambda x: x[1], reverse=True)
        
        return user_rankings[:limit]
    
    async def export_usage_data(self, 
                              start_date: datetime,
                              end_date: datetime,
                              format: str = "json") -> str:
        """Export usage data for external analysis."""
        
        # Filter data by date range
        export_activities = [
            activity for activity in self.activity_events
            if start_date <= activity.timestamp <= end_date
        ]
        
        if format.lower() == "json":
            # Convert to JSON-serializable format
            export_data = []
            for activity in export_activities:
                export_data.append({
                    'event_id': activity.event_id,
                    'timestamp': activity.timestamp.isoformat(),
                    'user_id': activity.user_id,
                    'session_id': activity.session_id,
                    'activity_type': activity.activity_type.value,
                    'resource_type': activity.resource_type.value if activity.resource_type else None,
                    'query_text': activity.query_text,
                    'document_id': activity.document_id,
                    'duration': activity.duration,
                    'results_count': activity.results_count,
                    'relevant_results': activity.relevant_results,
                    'success': activity.success,
                    'matter_id': activity.matter_id,
                    'client_id': activity.client_id,
                    'practice_area': activity.practice_area,
                    'metadata': activity.metadata
                })
            
            return json.dumps(export_data, indent=2)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Helper functions
async def track_user_search(user_id: str, session_id: str, query: str, results: int, relevant: int) -> ActivityEvent:
    """Helper function to track search activity."""
    monitor = UsageMonitor()
    return await monitor.track_activity(
        user_id=user_id,
        session_id=session_id,
        activity_type=ActivityType.SEARCH,
        query_text=query,
        results_count=results,
        relevant_results=relevant
    )

async def get_user_efficiency_profile(user_id: str) -> UserProfile:
    """Helper function to get user efficiency profile."""
    monitor = UsageMonitor()
    return await monitor.analyze_user_patterns(user_id)