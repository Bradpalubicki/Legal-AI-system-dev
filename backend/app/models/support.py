"""
Legal AI System - Support Models
Comprehensive support system: tickets, knowledge base, chat, agents
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..core.database import Base

class SupportCategory(Base):
    """Support ticket categories"""
    __tablename__ = "support_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("support_categories.id"))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # SLA settings
    sla_response_hours = Column(Integer, default=24)  # Expected first response time
    sla_resolution_hours = Column(Integer, default=72)  # Expected resolution time

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    # parent = relationship("SupportCategory", remote_side=[id])  # Temporarily disabled - id reference issue
    # children = relationship("SupportCategory")  # Temporarily disabled - depends on parent relationship
    tickets = relationship("SupportTicket", back_populates="category")
    articles = relationship("KnowledgeBaseArticle", back_populates="category")

class SupportAgent(Base):
    """Support team agents"""
    __tablename__ = "support_agents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    agent_number = Column(String(20), unique=True, index=True)

    # Agent details
    specialties = Column(JSON, default=[])  # ["billing", "technical", "legal"]
    languages = Column(JSON, default=["en"])
    timezone = Column(String(50), default="UTC")

    # Status and availability
    status = Column(String(20), default="offline")  # online, busy, away, offline
    is_active = Column(Boolean, default=True)
    max_concurrent_chats = Column(Integer, default=3)
    max_concurrent_tickets = Column(Integer, default=10)

    # Performance metrics
    average_response_time = Column(Float)  # in minutes
    average_resolution_time = Column(Float)  # in hours
    satisfaction_rating = Column(Float)  # 1-5 scale
    total_tickets_resolved = Column(Integer, default=0)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="agent_profile")
    assigned_tickets = relationship("SupportTicket", back_populates="agent")
    chat_sessions = relationship("ChatSession", back_populates="agent")

class SupportTicket(Base):
    """Customer support tickets"""
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, nullable=False, index=True)

    # Basic info
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("support_categories.id"))
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Status and assignment
    status = Column(String(20), nullable=False, index=True)
    # open, in_progress, waiting_for_customer, resolved, closed
    priority = Column(String(10), nullable=False, index=True)  # low, medium, high, urgent
    assigned_to = Column(Integer, ForeignKey("support_agents.id"), index=True)

    # Tracking
    source = Column(String(20), default="web")  # web, email, chat, phone
    tags = Column(JSON, default=[])
    attachments = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    first_response_at = Column(DateTime)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)

    # SLA tracking
    sla_due_at = Column(DateTime)
    first_response_time = Column(Float)  # Minutes to first response
    resolution_time = Column(Float)  # Seconds to resolution
    sla_breached = Column(Boolean, default=False)

    # Customer satisfaction
    satisfaction_rating = Column(Integer)  # 1-5 scale
    satisfaction_comment = Column(Text)

    # Relationships
    user = relationship("User", back_populates="support_tickets")
    category = relationship("SupportCategory", back_populates="tickets")
    agent = relationship("SupportAgent", back_populates="assigned_tickets")
    comments = relationship("TicketComment", back_populates="ticket", order_by="TicketComment.created_at")

class TicketComment(Base):
    """Ticket comments and updates"""
    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal notes vs customer-visible
    comment_type = Column(String(20), default="comment")  # comment, status_change, note

    # Attachments and formatting
    attachments = Column(JSON, default=[])
    is_html = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    edited_at = Column(DateTime)

    # Relationships
    ticket = relationship("SupportTicket", back_populates="comments")
    user = relationship("User", back_populates="ticket_comments")

class KnowledgeBaseArticle(Base):
    """Knowledge base articles"""
    __tablename__ = "knowledge_base_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    slug = Column(String(250), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(String(500))

    # Organization
    category_id = Column(Integer, ForeignKey("support_categories.id"))
    tags = Column(JSON, default=[])
    sort_order = Column(Integer, default=0)

    # Publishing
    is_published = Column(Boolean, default=False, index=True)
    is_featured = Column(Boolean, default=False)
    published_at = Column(DateTime)

    # Authors and editors
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_edited_by = Column(Integer, ForeignKey("users.id"))

    # SEO
    meta_title = Column(String(200))
    meta_description = Column(String(500))
    keywords = Column(JSON, default=[])

    # Analytics
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    search_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("SupportCategory", back_populates="articles")
    author = relationship("User", foreign_keys=[author_id])
    editor = relationship("User", foreign_keys=[last_edited_by])

class FAQ(Base):
    """Frequently Asked Questions"""
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)

    # Organization
    category_id = Column(Integer, ForeignKey("support_categories.id"))
    sort_order = Column(Integer, default=0)
    tags = Column(JSON, default=[])

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False)

    # Analytics
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)

    # Author
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("SupportCategory")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

class ChatSession(Base):
    """Live chat sessions"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)

    # Participants
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("support_agents.id"), index=True)

    # Session details
    status = Column(String(20), nullable=False, index=True)
    # active, waiting, assigned, ended, abandoned
    initial_message = Column(Text)
    channel = Column(String(20), default="web")  # web, mobile, api

    # Timestamps
    started_at = Column(DateTime, default=func.now())
    assigned_at = Column(DateTime)
    ended_at = Column(DateTime)
    last_activity = Column(DateTime, default=func.now())

    # Metrics
    wait_time = Column(Float)  # Minutes waiting for agent
    duration = Column(Float)  # Total session duration in minutes
    message_count = Column(Integer, default=0)

    # Satisfaction
    rating = Column(Integer)  # 1-5 scale
    feedback = Column(Text)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    agent = relationship("SupportAgent", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")

class ChatMessage(Base):
    """Individual chat messages"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text, file, system, typing

    # Attachments and formatting
    attachments = Column(JSON, default=[])
    is_system_message = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    read_at = Column(DateTime)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    sender = relationship("User")

class SupportMetrics(Base):
    """Support performance metrics"""
    __tablename__ = "support_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)

    # Agent-specific metrics
    agent_id = Column(Integer, ForeignKey("support_agents.id"), index=True)

    # Metric values
    value = Column(Float, nullable=False)
    count = Column(Integer)
    percentage = Column(Float)

    # Context
    category_id = Column(Integer, ForeignKey("support_categories.id"))
    metric_metadata = Column(JSON, default={})

    created_at = Column(DateTime, default=func.now())

    # Relationships
    agent = relationship("SupportAgent")
    category = relationship("SupportCategory")

class EscalationRule(Base):
    """Automatic escalation rules"""
    __tablename__ = "escalation_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Conditions
    conditions = Column(JSON, nullable=False)  # Complex JSON conditions
    priority = Column(String(10))  # Apply to specific priority
    category_id = Column(Integer, ForeignKey("support_categories.id"))

    # Actions
    escalate_to_priority = Column(String(10))
    assign_to_agent = Column(Integer, ForeignKey("support_agents.id"))
    send_notification = Column(Boolean, default=True)
    notification_recipients = Column(JSON, default=[])

    # Timing
    trigger_after_minutes = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("SupportCategory")
    agent = relationship("SupportAgent")

class SupportSLA(Base):
    """Service Level Agreement tracking"""
    __tablename__ = "support_slas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    # SLA targets
    first_response_target = Column(Integer, nullable=False)  # Minutes
    resolution_target = Column(Integer, nullable=False)  # Hours

    # Applicability
    priority = Column(String(10))
    category_id = Column(Integer, ForeignKey("support_categories.id"))
    customer_tier = Column(String(20))  # premium, standard, basic

    # Business hours
    business_hours_only = Column(Boolean, default=True)
    timezone = Column(String(50), default="UTC")

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("SupportCategory")