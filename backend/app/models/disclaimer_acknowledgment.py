"""
Legal AI System - Disclaimer Acknowledgment Models
Tracks when users view, acknowledge, or dismiss legal disclaimers
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any
import enum

from ..src.core.database import Base


class DisclaimerType(enum.Enum):
    """Types of disclaimers that require user acknowledgment"""
    INITIAL_WARNING = "initial_warning"
    ADVICE_LIMITATION = "advice_limitation"
    JURISDICTION_NOTICE = "jurisdiction_notice"
    CONFIDENTIALITY = "confidentiality"
    BILLING_TERMS = "billing_terms"
    EDUCATIONAL_ONLY = "educational_only"
    NO_ATTORNEY_CLIENT = "no_attorney_client"
    DATA_PRIVACY = "data_privacy"
    AI_LIMITATIONS = "ai_limitations"


class RiskLevel(enum.Enum):
    """Risk level for non-acknowledged disclaimers"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AcknowledgmentAction(enum.Enum):
    """Type of action taken by user"""
    VIEWED = "viewed"
    ACKNOWLEDGED = "acknowledged"
    DISMISSED = "dismissed"
    DISABLED = "disabled"
    RE_ENABLED = "re_enabled"


class DisclaimerAcknowledgment(Base):
    """
    Tracks user interactions with legal disclaimers and liability notices.
    Critical for legal compliance and professional responsibility.
    """
    __tablename__ = "disclaimer_acknowledgments"

    id = Column(Integer, primary_key=True, index=True)

    # User information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_type = Column(String(50))  # attorney, client, staff, guest

    # Disclaimer information
    disclaimer_type = Column(SQLEnum(DisclaimerType), nullable=False, index=True)
    disclaimer_id = Column(String(100), index=True)  # Specific disclaimer ID from frontend
    disclaimer_version = Column(String(50))  # Track version changes

    # Action tracking
    action = Column(SQLEnum(AcknowledgmentAction), nullable=False, default=AcknowledgmentAction.VIEWED)
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_at = Column(DateTime)
    dismissed_at = Column(DateTime)
    disabled_at = Column(DateTime)

    # User behavior tracking
    view_count = Column(Integer, default=1)  # How many times user saw it
    time_to_acknowledge = Column(Float)  # Seconds from first view to acknowledgment
    time_on_page = Column(Float)  # How long disclaimer was visible

    # Context information
    page_url = Column(String(500))
    page_context = Column(String(100))  # document-analysis, case-management, etc.
    jurisdiction = Column(String(50))  # State/jurisdiction if applicable

    # Session information (for audit trail)
    session_id = Column(String(255), index=True)
    ip_address = Column(String(50))  # Hashed or anonymized
    user_agent = Column(Text)

    # Risk assessment
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW, index=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_reason = Column(Text)

    # Compliance metadata
    is_mandatory = Column(Boolean, default=True)  # Must be acknowledged
    blocks_access = Column(Boolean, default=False)  # Blocks access until acknowledged
    requires_re_acknowledgment = Column(Boolean, default=False)  # Periodic re-acknowledgment
    re_acknowledgment_interval_days = Column(Integer)  # Days until re-acknowledgment required

    # Additional data (JSON for flexibility)
    extra_data = Column(Text)  # JSON string with additional context (renamed from metadata to avoid SQLAlchemy conflict)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime)  # When acknowledgment expires (if applicable)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<DisclaimerAcknowledgment {self.disclaimer_type.value} - User {self.user_id} - {self.action.value}>"

    def to_dict(self, include_pii: bool = False) -> Dict[str, Any]:
        """
        Convert acknowledgment to dictionary.
        PII is redacted by default for privacy compliance.
        """
        data = {
            "id": str(self.id),
            "user_id": f"user_***{str(self.user_id)[-4:]}" if not include_pii else str(self.user_id),
            "user_type": self.user_type,
            "disclaimer_type": self.disclaimer_type.value,
            "disclaimer_id": self.disclaimer_id,
            "action": self.action.value,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "dismissed_at": self.dismissed_at.isoformat() if self.dismissed_at else None,
            "disabled_at": self.disabled_at.isoformat() if self.disabled_at else None,
            "view_count": self.view_count,
            "time_to_acknowledge": self.time_to_acknowledge,
            "page_context": self.page_context,
            "jurisdiction": self.jurisdiction,
            "risk_level": self.risk_level.value,
            "follow_up_required": self.follow_up_required,
            "is_mandatory": self.is_mandatory,
            "blocks_access": self.blocks_access,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_pii:
            data.update({
                "session_id": self.session_id,
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
            })
        else:
            # Redact PII for privacy
            data.update({
                "session_id": f"sess_***{self.session_id[-4:]}" if self.session_id else None,
                "ip_address": "***.***.***" if self.ip_address else None,
                "user_agent": "[REDACTED]" if self.user_agent else None,
            })

        return data

    @property
    def is_expired(self) -> bool:
        """Check if acknowledgment has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def needs_re_acknowledgment(self) -> bool:
        """Check if user needs to re-acknowledge"""
        if not self.requires_re_acknowledgment or not self.acknowledged_at:
            return False
        if not self.re_acknowledgment_interval_days:
            return False

        from datetime import timedelta
        next_ack_date = self.acknowledged_at + timedelta(days=self.re_acknowledgment_interval_days)
        return datetime.utcnow() > next_ack_date


class DisclaimerTemplate(Base):
    """
    Templates for disclaimers that can be customized by jurisdiction
    """
    __tablename__ = "disclaimer_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template identification
    template_key = Column(String(100), unique=True, nullable=False, index=True)
    disclaimer_type = Column(SQLEnum(DisclaimerType), nullable=False, index=True)
    version = Column(String(50), nullable=False)

    # Template content
    title = Column(String(200), nullable=False)
    content_html = Column(Text, nullable=False)
    content_markdown = Column(Text)
    short_description = Column(Text)

    # Applicability
    jurisdiction = Column(String(50))  # null = applies to all
    user_types = Column(Text)  # JSON array of applicable user types

    # Behavior
    is_mandatory = Column(Boolean, default=True)
    blocks_access = Column(Boolean, default=False)
    requires_re_acknowledgment = Column(Boolean, default=False)
    re_acknowledgment_interval_days = Column(Integer)
    display_priority = Column(Integer, default=0)  # Higher = show first

    # Status
    is_active = Column(Boolean, default=True, index=True)
    effective_date = Column(DateTime)
    retired_date = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<DisclaimerTemplate {self.template_key} v{self.version}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            "id": str(self.id),
            "template_key": self.template_key,
            "disclaimer_type": self.disclaimer_type.value,
            "version": self.version,
            "title": self.title,
            "content_html": self.content_html,
            "content_markdown": self.content_markdown,
            "short_description": self.short_description,
            "jurisdiction": self.jurisdiction,
            "is_mandatory": self.is_mandatory,
            "blocks_access": self.blocks_access,
            "requires_re_acknowledgment": self.requires_re_acknowledgment,
            "re_acknowledgment_interval_days": self.re_acknowledgment_interval_days,
            "display_priority": self.display_priority,
            "is_active": self.is_active,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
