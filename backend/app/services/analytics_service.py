"""
Legal AI System - Comprehensive Analytics Service
Business intelligence, user tracking, and performance analytics
"""

import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_, desc, asc, text
from fastapi import HTTPException
import logging
import json
from dataclasses import dataclass
from enum import Enum

from ..models.analytics import (
    UserEvent, BusinessMetric, ConversionFunnel,
    FeatureUsage, RevenueMetric, CustomerSegment
)
from ..models.user import User
from ..models.billing import Subscription, Invoice, Payment, BillingPlan
from ..models.support import SupportTicket
from ..core.database import get_async_session
from ..core.config import settings

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    PAGE_VIEW = "page_view"
    BUTTON_CLICK = "button_click"
    FEATURE_USE = "feature_use"
    SIGNUP = "signup"
    SUBSCRIPTION = "subscription"
    CONVERSION = "conversion"
    CHURN = "churn"

class MetricType(str, Enum):
    REVENUE = "revenue"
    USERS = "users"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    RETENTION = "retention"
    SUPPORT = "support"

@dataclass
class AnalyticsQuery:
    metric_type: str
    date_range: Tuple[date, date]
    filters: Dict[str, Any] = None
    group_by: str = None
    granularity: str = "day"  # hour, day, week, month

class AnalyticsService:
    """Comprehensive analytics and business intelligence service"""

    def __init__(self):
        self.session_timeout = 30  # minutes

    async def track_event(
        self,
        user_id: Optional[int],
        event_type: str,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Track user events for analytics"""
        try:
            async with get_async_session() as session:
                event = UserEvent(
                    user_id=user_id,
                    event_type=event_type,
                    event_name=event_name,
                    properties=properties or {},
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    timestamp=datetime.utcnow()
                )

                session.add(event)
                await session.commit()

                # Update real-time metrics if needed
                await self._update_realtime_metrics(event_type, event_name, properties)

                logger.debug(f"Tracked event: {event_name} for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to track event: {e}")
            return False

    async def get_dashboard_metrics(
        self,
        user_id: int,
        date_range: Optional[Tuple[date, date]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics"""
        try:
            if not date_range:
                end_date = date.today()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)

            async with get_async_session() as session:
                # Check if user is admin
                user = await session.get(User, user_id)
                if not user or not user.is_admin:
                    raise HTTPException(status_code=403, detail="Admin access required")

                metrics = {}

                # Revenue metrics
                metrics["revenue"] = await self._get_revenue_metrics(session, date_range)

                # User metrics
                metrics["users"] = await self._get_user_metrics(session, date_range)

                # Conversion metrics
                metrics["conversion"] = await self._get_conversion_metrics(session, date_range)

                # Support metrics
                metrics["support"] = await self._get_support_metrics(session, date_range)

                # Feature usage
                metrics["features"] = await self._get_feature_usage(session, date_range)

                # Growth trends
                metrics["trends"] = await self._get_growth_trends(session, date_range)

                return metrics

        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

    async def get_user_analytics(
        self,
        user_id: int,
        target_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get analytics for a specific user"""
        try:
            async with get_async_session() as session:
                # Use target_user_id if provided (admin feature), otherwise user's own analytics
                analytics_user_id = target_user_id or user_id

                # Check permissions
                if target_user_id and target_user_id != user_id:
                    user = await session.get(User, user_id)
                    if not user or not user.is_admin:
                        raise HTTPException(status_code=403, detail="Admin access required")

                end_date = date.today()
                start_date = end_date - timedelta(days=30)

                # User activity
                activity = await session.execute(
                    select(UserEvent)
                    .where(
                        and_(
                            UserEvent.user_id == analytics_user_id,
                            UserEvent.timestamp >= start_date,
                            UserEvent.timestamp <= end_date
                        )
                    )
                    .order_by(desc(UserEvent.timestamp))
                    .limit(100)
                )
                activity = activity.scalars().all()

                # Feature usage breakdown
                feature_usage = await session.execute(
                    select(
                        UserEvent.event_name,
                        func.count().label('usage_count'),
                        func.max(UserEvent.timestamp).label('last_used')
                    )
                    .where(
                        and_(
                            UserEvent.user_id == analytics_user_id,
                            UserEvent.event_type == EventType.FEATURE_USE,
                            UserEvent.timestamp >= start_date
                        )
                    )
                    .group_by(UserEvent.event_name)
                    .order_by(desc('usage_count'))
                )
                feature_usage = feature_usage.all()

                # Session analytics
                sessions = await self._get_user_sessions(session, analytics_user_id, start_date, end_date)

                return {
                    "user_id": analytics_user_id,
                    "date_range": {"start": start_date, "end": end_date},
                    "activity": [
                        {
                            "event_type": event.event_type,
                            "event_name": event.event_name,
                            "timestamp": event.timestamp,
                            "properties": event.properties
                        }
                        for event in activity
                    ],
                    "feature_usage": [
                        {
                            "feature": usage.event_name,
                            "count": usage.usage_count,
                            "last_used": usage.last_used
                        }
                        for usage in feature_usage
                    ],
                    "sessions": sessions
                }

        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

    async def get_conversion_funnel(
        self,
        funnel_name: str,
        date_range: Optional[Tuple[date, date]] = None
    ) -> Dict[str, Any]:
        """Analyze conversion funnel performance"""
        try:
            if not date_range:
                end_date = date.today()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)

            async with get_async_session() as session:
                # Define funnel steps
                funnel_steps = self._get_funnel_definition(funnel_name)

                funnel_data = []
                total_users = 0

                for i, step in enumerate(funnel_steps):
                    if i == 0:
                        # First step - count all users who performed this action
                        count_query = select(func.count(func.distinct(UserEvent.user_id))).where(
                            and_(
                                UserEvent.event_name == step["event"],
                                UserEvent.timestamp >= date_range[0],
                                UserEvent.timestamp <= date_range[1]
                            )
                        )
                        result = await session.execute(count_query)
                        count = result.scalar()
                        total_users = count
                    else:
                        # Subsequent steps - count users who completed previous step AND this step
                        # This is a simplified funnel calculation
                        count_query = select(func.count(func.distinct(UserEvent.user_id))).where(
                            and_(
                                UserEvent.event_name == step["event"],
                                UserEvent.timestamp >= date_range[0],
                                UserEvent.timestamp <= date_range[1]
                            )
                        )
                        result = await session.execute(count_query)
                        count = result.scalar()

                    conversion_rate = (count / total_users * 100) if total_users > 0 else 0
                    drop_off = total_users - count if i > 0 else 0

                    funnel_data.append({
                        "step": step["name"],
                        "event": step["event"],
                        "users": count,
                        "conversion_rate": round(conversion_rate, 2),
                        "drop_off": drop_off
                    })

                return {
                    "funnel_name": funnel_name,
                    "date_range": {"start": date_range[0], "end": date_range[1]},
                    "steps": funnel_data,
                    "total_users": total_users
                }

        except Exception as e:
            logger.error(f"Failed to get conversion funnel: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve funnel data")

    async def get_cohort_analysis(
        self,
        metric: str = "retention",
        period: str = "month"
    ) -> Dict[str, Any]:
        """Generate cohort analysis for user retention/revenue"""
        try:
            async with get_async_session() as session:
                # This is a simplified cohort analysis
                # In production, you'd want more sophisticated cohort calculations

                cohorts = {}
                end_date = date.today()

                # Get cohorts for the last 12 periods
                for i in range(12):
                    if period == "month":
                        cohort_date = end_date - timedelta(days=30 * i)
                        cohort_key = cohort_date.strftime("%Y-%m")
                    else:  # week
                        cohort_date = end_date - timedelta(days=7 * i)
                        cohort_key = cohort_date.strftime("%Y-W%U")

                    # Get users who signed up in this cohort
                    signup_query = select(func.count(User.id)).where(
                        func.date_trunc(period, User.created_at) == cohort_date
                    )
                    result = await session.execute(signup_query)
                    cohort_size = result.scalar() or 0

                    cohorts[cohort_key] = {
                        "size": cohort_size,
                        "periods": {}
                    }

                return {
                    "metric": metric,
                    "period": period,
                    "cohorts": cohorts
                }

        except Exception as e:
            logger.error(f"Failed to generate cohort analysis: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate cohort analysis")

    async def get_ab_test_results(
        self,
        test_name: str,
        date_range: Optional[Tuple[date, date]] = None
    ) -> Dict[str, Any]:
        """Get A/B test results and statistical significance"""
        try:
            if not date_range:
                end_date = date.today()
                start_date = end_date - timedelta(days=7)
                date_range = (start_date, end_date)

            async with get_async_session() as session:
                # Get events for this A/B test
                events = await session.execute(
                    select(UserEvent).where(
                        and_(
                            UserEvent.properties.contains({"ab_test": test_name}),
                            UserEvent.timestamp >= date_range[0],
                            UserEvent.timestamp <= date_range[1]
                        )
                    )
                )
                events = events.scalars().all()

                # Analyze variants
                variants = {}
                for event in events:
                    variant = event.properties.get("variant", "control")
                    if variant not in variants:
                        variants[variant] = {"impressions": 0, "conversions": 0}

                    variants[variant]["impressions"] += 1
                    if event.event_type == EventType.CONVERSION:
                        variants[variant]["conversions"] += 1

                # Calculate conversion rates
                for variant_data in variants.values():
                    if variant_data["impressions"] > 0:
                        variant_data["conversion_rate"] = (
                            variant_data["conversions"] / variant_data["impressions"] * 100
                        )
                    else:
                        variant_data["conversion_rate"] = 0

                return {
                    "test_name": test_name,
                    "date_range": {"start": date_range[0], "end": date_range[1]},
                    "variants": variants
                }

        except Exception as e:
            logger.error(f"Failed to get A/B test results: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve test results")

    # Private helper methods
    async def _get_revenue_metrics(
        self,
        session: AsyncSession,
        date_range: Tuple[date, date]
    ) -> Dict[str, Any]:
        """Calculate revenue metrics"""
        # Monthly Recurring Revenue
        active_subscriptions = await session.execute(
            select(func.sum(BillingPlan.price_monthly))
            .join(Subscription, BillingPlan.id == Subscription.plan_id)
            .where(Subscription.status == "active")
        )
        mrr = active_subscriptions.scalar() or Decimal(0)

        # Total revenue in period
        revenue_query = await session.execute(
            select(func.sum(Payment.amount)).where(
                and_(
                    Payment.status == "succeeded",
                    func.date(Payment.created_at) >= date_range[0],
                    func.date(Payment.created_at) <= date_range[1]
                )
            )
        )
        total_revenue = revenue_query.scalar() or Decimal(0)

        # Revenue growth
        prev_period_start = date_range[0] - timedelta(days=(date_range[1] - date_range[0]).days)
        prev_revenue_query = await session.execute(
            select(func.sum(Payment.amount)).where(
                and_(
                    Payment.status == "succeeded",
                    func.date(Payment.created_at) >= prev_period_start,
                    func.date(Payment.created_at) < date_range[0]
                )
            )
        )
        prev_revenue = prev_revenue_query.scalar() or Decimal(0)

        growth_rate = 0
        if prev_revenue > 0:
            growth_rate = float((total_revenue - prev_revenue) / prev_revenue * 100)

        return {
            "mrr": float(mrr),
            "total_revenue": float(total_revenue),
            "revenue_growth": round(growth_rate, 2),
            "average_revenue_per_user": 0  # Calculate ARPU
        }

    async def _get_user_metrics(
        self,
        session: AsyncSession,
        date_range: Tuple[date, date]
    ) -> Dict[str, Any]:
        """Calculate user metrics"""
        # Total active users
        total_users = await session.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        total_users = total_users.scalar()

        # New users in period
        new_users = await session.execute(
            select(func.count(User.id)).where(
                and_(
                    func.date(User.created_at) >= date_range[0],
                    func.date(User.created_at) <= date_range[1]
                )
            )
        )
        new_users = new_users.scalar()

        # Daily/Monthly Active Users
        dau = await session.execute(
            select(func.count(func.distinct(UserEvent.user_id))).where(
                func.date(UserEvent.timestamp) == date.today()
            )
        )
        dau = dau.scalar()

        return {
            "total_users": total_users,
            "new_users": new_users,
            "daily_active_users": dau,
            "monthly_active_users": 0  # Calculate MAU
        }

    async def _get_conversion_metrics(
        self,
        session: AsyncSession,
        date_range: Tuple[date, date]
    ) -> Dict[str, Any]:
        """Calculate conversion metrics"""
        # Signup to subscription conversion
        signups = await session.execute(
            select(func.count(User.id)).where(
                and_(
                    func.date(User.created_at) >= date_range[0],
                    func.date(User.created_at) <= date_range[1]
                )
            )
        )
        signups = signups.scalar()

        subscriptions = await session.execute(
            select(func.count(Subscription.id)).where(
                and_(
                    func.date(Subscription.created_at) >= date_range[0],
                    func.date(Subscription.created_at) <= date_range[1]
                )
            )
        )
        subscriptions = subscriptions.scalar()

        conversion_rate = (subscriptions / signups * 100) if signups > 0 else 0

        return {
            "signup_to_subscription": round(conversion_rate, 2),
            "trial_to_paid": 0,  # Calculate trial conversion
            "total_conversions": subscriptions
        }

    async def _get_support_metrics(
        self,
        session: AsyncSession,
        date_range: Tuple[date, date]
    ) -> Dict[str, Any]:
        """Calculate support metrics"""
        # Total tickets
        total_tickets = await session.execute(
            select(func.count(SupportTicket.id)).where(
                and_(
                    func.date(SupportTicket.created_at) >= date_range[0],
                    func.date(SupportTicket.created_at) <= date_range[1]
                )
            )
        )
        total_tickets = total_tickets.scalar()

        # Average resolution time
        avg_resolution = await session.execute(
            select(func.avg(SupportTicket.resolution_time)).where(
                and_(
                    SupportTicket.resolved_at.isnot(None),
                    func.date(SupportTicket.created_at) >= date_range[0],
                    func.date(SupportTicket.created_at) <= date_range[1]
                )
            )
        )
        avg_resolution = avg_resolution.scalar() or 0

        return {
            "total_tickets": total_tickets,
            "avg_resolution_hours": round(avg_resolution / 3600, 2),  # Convert seconds to hours
            "satisfaction_score": 4.2  # Calculate from satisfaction ratings
        }

    async def _get_feature_usage(
        self,
        session: AsyncSession,
        date_range: Tuple[date, date]
    ) -> Dict[str, Any]:
        """Get feature usage statistics"""
        usage = await session.execute(
            select(
                UserEvent.event_name,
                func.count().label('usage_count'),
                func.count(func.distinct(UserEvent.user_id)).label('unique_users')
            ).where(
                and_(
                    UserEvent.event_type == EventType.FEATURE_USE,
                    func.date(UserEvent.timestamp) >= date_range[0],
                    func.date(UserEvent.timestamp) <= date_range[1]
                )
            ).group_by(UserEvent.event_name)
            .order_by(desc('usage_count'))
        )
        usage = usage.all()

        return [
            {
                "feature": row.event_name,
                "usage_count": row.usage_count,
                "unique_users": row.unique_users
            }
            for row in usage
        ]

    async def _get_growth_trends(
        self,
        session: AsyncSession,
        date_range: Tuple[date, date]
    ) -> Dict[str, Any]:
        """Calculate growth trends over time"""
        # Daily signups
        daily_signups = await session.execute(
            select(
                func.date(User.created_at).label('date'),
                func.count().label('signups')
            ).where(
                and_(
                    func.date(User.created_at) >= date_range[0],
                    func.date(User.created_at) <= date_range[1]
                )
            ).group_by(func.date(User.created_at))
            .order_by('date')
        )
        daily_signups = daily_signups.all()

        return {
            "daily_signups": [
                {"date": row.date, "value": row.signups}
                for row in daily_signups
            ]
        }

    async def _get_user_sessions(
        self,
        session: AsyncSession,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Get user session analytics"""
        # Simplified session calculation
        # In production, you'd have more sophisticated session tracking
        return {
            "total_sessions": 0,
            "average_duration": 0,
            "pages_per_session": 0
        }

    def _get_funnel_definition(self, funnel_name: str) -> List[Dict[str, str]]:
        """Get predefined funnel steps"""
        funnels = {
            "signup": [
                {"name": "Landing Page View", "event": "page_view_landing"},
                {"name": "Signup Page View", "event": "page_view_signup"},
                {"name": "Signup Complete", "event": "signup_complete"}
            ],
            "subscription": [
                {"name": "Signup Complete", "event": "signup_complete"},
                {"name": "Trial Start", "event": "trial_start"},
                {"name": "Subscription Created", "event": "subscription_created"}
            ]
        }
        return funnels.get(funnel_name, [])

    async def _update_realtime_metrics(
        self,
        event_type: str,
        event_name: str,
        properties: Dict[str, Any]
    ) -> None:
        """Update real-time metrics cache"""
        # Implementation for real-time metrics updates
        # Would use Redis or similar for real-time dashboards
        pass

# Initialize analytics service
analytics_service = AnalyticsService()