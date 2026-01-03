"""
Legal AI System - User Models
User management, authentication, and profile models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
import enum

from ..src.core.database import Base

# Import for type hinting and relationship resolution
if TYPE_CHECKING:
    from .case_access import CaseAccess


class UserRole(enum.Enum):
    """User role enumeration for role-based access control"""
    GUEST = "guest"          # Limited read-only access
    USER = "user"            # Standard authenticated user
    ATTORNEY = "attorney"    # Licensed attorney with full legal access
    CLIENT = "client"        # Client with limited access to own cases
    ADMIN = "admin"          # Full administrative access

class User(Base):
    """User accounts and profiles"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, index=True)

    # Personal information
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(200))
    phone = Column(String(50))

    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime)

    # Roles and permissions (RBAC)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False, index=True)
    is_admin = Column(Boolean, default=False)
    is_support_agent = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)

    # Security tracking
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime)
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime)

    # Profile
    avatar_url = Column(String(500))
    bio = Column(Text)
    website = Column(String(500))
    company = Column(String(200))
    job_title = Column(String(100))

    # Preferences
    preferences = Column(JSON, default={})
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")

    # Billing integration
    stripe_customer_id = Column(String(100), unique=True, index=True)

    # OAuth
    oauth_provider = Column(String(50))
    oauth_id = Column(String(100))

    # Activity tracking
    last_login_at = Column(DateTime)
    previous_login_at = Column(DateTime)  # Track previous login for new-filings-since-login feature
    last_active_at = Column(DateTime)
    login_count = Column(Integer, default=0)

    # Account status
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)

    # Billing relationships
    subscriptions = relationship("Subscription", back_populates="user")
    invoices = relationship("Invoice", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    usage_records = relationship("Usage", back_populates="user")
    payment_methods = relationship("PaymentMethod", back_populates="user")

    # Case access relationships (pay-per-case feature)
    case_accesses = relationship("CaseAccess", back_populates="user")

    # support_tickets = relationship("SupportTicket", back_populates="user")
    # ticket_comments = relationship("TicketComment", back_populates="user")
    # chat_sessions = relationship("ChatSession", back_populates="user")

    # events = relationship("UserEvent", back_populates="user")

    # Developer account relationship
    # developer_account = relationship("DeveloperAccount", back_populates="user", uselist=False)

    # Agent profile relationship
    # agent_profile = relationship("SupportAgent", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def display_name(self) -> str:
        """Get display name for user"""
        if self.full_name:
            return self.full_name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.email

    @property
    def is_developer(self) -> bool:
        """Check if user has a developer account"""
        return self.developer_account is not None

    @property
    def is_support_staff(self) -> bool:
        """Check if user is support staff"""
        return self.is_admin or self.is_support_agent

    def has_role(self, required_role: UserRole) -> bool:
        """Check if user has required role or higher (role hierarchy)"""
        role_hierarchy = {
            UserRole.GUEST: 1,
            UserRole.USER: 2,
            UserRole.ADMIN: 3,
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)

    def can_access_resource(self, resource_owner_id: str) -> bool:
        """Check if user can access a resource (admins can access all, users their own)"""
        if self.role == UserRole.ADMIN or self.is_admin:
            return True
        return str(self.id) == str(resource_owner_id)

    def is_account_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.account_locked_until:
            return False
        return datetime.utcnow() < self.account_locked_until

    def to_dict(self, include_sensitive=False) -> Dict[str, Any]:
        """Convert user to dictionary (excluding sensitive data by default)"""
        user_dict = {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "role": self.role.value if self.role else "user",
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_admin": self.is_admin,
            "full_name": self.full_name or self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }

        if include_sensitive:
            user_dict.update({
                "phone": self.phone,
                "company": self.company,
                "job_title": self.job_title,
                "is_premium": self.is_premium,
                "failed_login_attempts": self.failed_login_attempts,
            })

        return user_dict