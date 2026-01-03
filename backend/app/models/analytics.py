"""
Legal AI System - Analytics Models
Business intelligence, user tracking, and performance analytics
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

from ..core.database import Base

class UserEvent(Base):
    """User events for analytics tracking"""
    __tablename__ = "user_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    session_id = Column(String(100), index=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    event_name = Column(String(100), nullable=False, index=True)
    properties = Column(JSON, default={})

    # Request context
    ip_address = Column(String(45))
    user_agent = Column(Text)
    referrer = Column(String(500))
    page_url = Column(String(500))

    # Timestamps
    timestamp = Column(DateTime, default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="events")

class BusinessMetric(Base):
    """Business metrics for KPI tracking"""
    __tablename__ = "business_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)

    # Metric values
    value = Column(Float, nullable=False)
    count = Column(Integer)
    percentage = Column(Float)

    # Dimensions
    dimension_1 = Column(String(100))  # e.g., plan_type, user_segment
    dimension_2 = Column(String(100))  # e.g., channel, region
    dimension_3 = Column(String(100))  # Additional dimension

    # Time period
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), default="day")  # hour, day, week, month

    created_at = Column(DateTime, default=func.now())

class ConversionFunnel(Base):
    """Conversion funnel tracking"""
    __tablename__ = "conversion_funnels"

    id = Column(Integer, primary_key=True, index=True)
    funnel_name = Column(String(100), nullable=False, index=True)
    step_name = Column(String(100), nullable=False)
    step_order = Column(Integer, nullable=False)

    # Metrics
    users_entered = Column(Integer, default=0)
    users_completed = Column(Integer, default=0)
    conversion_rate = Column(Float)
    drop_off_rate = Column(Float)

    # Time period
    date = Column(DateTime, nullable=False, index=True)

    created_at = Column(DateTime, default=func.now())

class FeatureUsage(Base):
    """Feature usage analytics"""
    __tablename__ = "feature_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    feature_name = Column(String(100), nullable=False, index=True)

    # Usage metrics
    usage_count = Column(Integer, default=1)
    duration_seconds = Column(Integer)
    success = Column(Boolean, default=True)

    # Context
    properties = Column(JSON, default={})

    # Timestamps
    first_used = Column(DateTime, default=func.now())
    last_used = Column(DateTime, default=func.now())
    date = Column(DateTime, nullable=False, index=True)

    # Relationships
    user = relationship("User")

class RevenueMetric(Base):
    """Revenue and financial metrics"""
    __tablename__ = "revenue_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)

    # Revenue values
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")

    # Dimensions
    customer_segment = Column(String(50))
    plan_type = Column(String(50))
    channel = Column(String(50))

    # Time period
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), default="day")

    created_at = Column(DateTime, default=func.now())

class CustomerSegment(Base):
    """Customer segmentation for analytics"""
    __tablename__ = "customer_segments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    segment_name = Column(String(100), nullable=False, index=True)

    # Segment properties
    properties = Column(JSON, default={})
    score = Column(Float)  # Segment score/probability

    # Timestamps
    assigned_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)

    # Relationships
    user = relationship("User")