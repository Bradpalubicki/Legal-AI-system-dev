"""
Legal AI System - Partner Models
API keys, developer accounts, and integration management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..core.database import Base

class DeveloperAccount(Base):
    """Developer accounts for API access"""
    __tablename__ = "developer_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Company information
    company_name = Column(String(200), nullable=False)
    company_website = Column(String(500))
    company_description = Column(Text)
    use_case = Column(Text)

    # Account status
    status = Column(String(20), nullable=False, index=True)  # pending_approval, approved, suspended, rejected
    tier = Column(String(20), default="standard")  # standard, premium, enterprise

    # Approval workflow
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    approval_notes = Column(Text)

    # Contact information
    contact_email = Column(String(255))
    contact_phone = Column(String(50))

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="developer_account")
    approver = relationship("User", foreign_keys=[approved_by])
    api_keys = relationship("APIKey", back_populates="developer")
    webhooks = relationship("Webhook", back_populates="developer")

class APIKey(Base):
    """API keys for authentication"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    developer_id = Column(Integer, ForeignKey("developer_accounts.id"), nullable=False, index=True)

    # Key details
    key_id = Column(String(100), nullable=False, unique=True, index=True)
    key_hash = Column(String(255), nullable=False)  # Hashed secret key
    name = Column(String(100), nullable=False)

    # Permissions and access
    scopes = Column(JSON, default=[])  # ["read", "write", "webhook"]
    status = Column(String(20), nullable=False, index=True)  # active, suspended, revoked, expired

    # Rate limiting
    rate_limit_tier = Column(String(20), default="standard")
    requests_per_minute = Column(Integer, default=100)
    requests_per_day = Column(Integer, default=10000)

    # Usage tracking
    last_used_at = Column(DateTime)
    total_requests = Column(Integer, default=0)

    # Expiration
    expires_at = Column(DateTime)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    developer = relationship("DeveloperAccount", back_populates="api_keys")
    usage_logs = relationship("APIUsage", back_populates="api_key")

class APIUsage(Base):
    """API usage logs for analytics and billing"""
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False, index=True)

    # Request details
    endpoint = Column(String(200), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False, index=True)

    # Performance metrics
    response_time_ms = Column(Integer)
    request_size = Column(Integer)  # bytes
    response_size = Column(Integer)  # bytes

    # Request context
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # Timestamps
    timestamp = Column(DateTime, default=func.now(), index=True)

    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")

class Webhook(Base):
    """Webhook subscriptions"""
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    developer_id = Column(Integer, ForeignKey("developer_accounts.id"), nullable=False, index=True)

    # Webhook configuration
    url = Column(String(500), nullable=False)
    events = Column(JSON, nullable=False)  # List of event types to subscribe to
    secret = Column(String(255), nullable=False)  # Webhook secret for verification

    # Status and configuration
    is_active = Column(Boolean, default=True, index=True)
    retry_count = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=30)

    # Statistics
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    last_delivery_at = Column(DateTime)
    last_success_at = Column(DateTime)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    developer = relationship("DeveloperAccount", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook")

class WebhookDelivery(Base):
    """Webhook delivery attempts"""
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False, index=True)

    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON, nullable=False)

    # Delivery details
    status = Column(String(20), nullable=False, index=True)  # pending, delivered, failed
    response_status_code = Column(Integer)
    response_body = Column(Text)
    error_message = Column(Text)

    # Retry information
    attempt_count = Column(Integer, default=1)
    next_retry_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    delivered_at = Column(DateTime)

    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")

class IntegrationTemplate(Base):
    """Pre-built integration templates"""
    __tablename__ = "integration_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)

    # Template details
    language = Column(String(20), nullable=False)  # python, javascript, php, etc.
    framework = Column(String(50))  # django, express, laravel, etc.
    difficulty = Column(String(20), default="beginner")  # beginner, intermediate, advanced
    estimated_time_minutes = Column(Integer)

    # Template content
    code_template = Column(Text, nullable=False)
    documentation = Column(Text)
    requirements = Column(JSON, default=[])  # List of dependencies

    # Metadata
    is_published = Column(Boolean, default=False, index=True)
    popularity = Column(Integer, default=0)
    downloads = Column(Integer, default=0)

    # Author
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    author = relationship("User")

class PartnerApplication(Base):
    """Partner program applications"""
    __tablename__ = "partner_applications"

    id = Column(Integer, primary_key=True, index=True)
    developer_id = Column(Integer, ForeignKey("developer_accounts.id"), nullable=False, index=True)

    # Application details
    partnership_type = Column(String(50), nullable=False)  # integration, reseller, technology
    business_model = Column(String(50))  # saas, consulting, agency
    expected_volume = Column(String(50))  # low, medium, high, enterprise

    # Company details
    annual_revenue = Column(String(50))
    employee_count = Column(String(50))
    target_market = Column(Text)
    existing_integrations = Column(JSON, default=[])

    # Application status
    status = Column(String(20), nullable=False, index=True)  # pending, approved, rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    developer = relationship("DeveloperAccount")
    reviewer = relationship("User")