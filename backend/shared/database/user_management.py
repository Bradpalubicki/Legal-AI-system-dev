"""
User Management Models for Legal AI System

Models for authentication, authorization, user profiles, and role-based access control.
Includes support for law firms, clients, and different user types.
"""

import enum
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint,
    CheckConstraint, Table
)
from sqlalchemy.orm import relationship, validates

from passlib.context import CryptContext

from .base import BaseModel, NamedModel, StatusModel, StatusEnum, ConfidentialityLevel


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# ENUMS
# =============================================================================

class UserType(enum.Enum):
    """Types of users in the system"""
    ADMIN = "admin"
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal" 
    SECRETARY = "secretary"
    CLIENT = "client"
    EXPERT = "expert"
    VENDOR = "vendor"
    GUEST = "guest"


class UserStatus(enum.Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    EXPIRED = "expired"


class PermissionType(enum.Enum):
    """Types of permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"


class AuthenticationMethod(enum.Enum):
    """Authentication methods"""
    PASSWORD = "password"
    OAUTH2 = "oauth2"
    SAML = "saml"
    LDAP = "ldap"
    MFA = "mfa"
    API_KEY = "api_key"


class FirmSize(enum.Enum):
    """Law firm size categories"""
    SOLO = "solo"
    SMALL = "small"          # 2-10 attorneys
    MEDIUM = "medium"        # 11-50 attorneys
    LARGE = "large"          # 51-200 attorneys
    BIG_LAW = "big_law"      # 200+ attorneys


class PracticeArea(enum.Enum):
    """Legal practice areas"""
    CORPORATE = "corporate"
    LITIGATION = "litigation"
    REAL_ESTATE = "real_estate"
    FAMILY = "family"
    CRIMINAL = "criminal"
    IMMIGRATION = "immigration"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    LABOR_EMPLOYMENT = "labor_employment"
    TAX = "tax"
    BANKRUPTCY = "bankruptcy"
    PERSONAL_INJURY = "personal_injury"
    ESTATE_PLANNING = "estate_planning"
    ENVIRONMENTAL = "environmental"
    HEALTHCARE = "healthcare"
    SECURITIES = "securities"
    OTHER = "other"


# =============================================================================
# ASSOCIATION TABLES
# =============================================================================

# Many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    BaseModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    Column('assigned_by_id', Integer, ForeignKey('users.id')),
    Index('ix_user_roles_user_id', 'user_id'),
    Index('ix_user_roles_role_id', 'role_id')
)

# Many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    BaseModel.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    Column('granted_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    Column('granted_by_id', Integer, ForeignKey('users.id')),
    Index('ix_role_permissions_role_id', 'role_id'),
    Index('ix_role_permissions_permission_id', 'permission_id')
)

# Many-to-many relationship between users and firms (for external users)
user_firms = Table(
    'user_firms',
    BaseModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('firm_id', Integer, ForeignKey('law_firms.id', ondelete='CASCADE'), primary_key=True),
    Column('relationship', String(50), default='client'),  # client, opposing_counsel, expert, etc.
    Column('started_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    Column('ended_at', DateTime(timezone=True)),
    Index('ix_user_firms_user_id', 'user_id'),
    Index('ix_user_firms_firm_id', 'firm_id')
)


# =============================================================================
# CORE USER MODELS
# =============================================================================

class User(BaseModel):
    """Core user model with authentication and profile information"""
    
    __tablename__ = 'users'
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    title = Column(String(100))  # Mr., Ms., Dr., Esq., etc.
    professional_suffix = Column(String(50))  # Jr., Sr., III, etc.
    
    # Contact Information
    phone = Column(String(20))
    mobile_phone = Column(String(20))
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(100), default='United States')
    
    # Professional Information
    user_type = Column(SQLEnum(UserType), nullable=False, default=UserType.CLIENT)
    bar_number = Column(String(50))  # Attorney bar admission number
    bar_state = Column(String(50))   # State of bar admission
    license_number = Column(String(50))  # Professional license number
    firm_id = Column(Integer, ForeignKey('law_firms.id'), nullable=True)
    department = Column(String(100))
    job_title = Column(String(100))
    
    # Account Status and Security
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Authentication Settings
    auth_method = Column(SQLEnum(AuthenticationMethod), default=AuthenticationMethod.PASSWORD)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(32))  # TOTP secret
    
    # Session Management
    last_login = Column(DateTime(timezone=True))
    last_activity = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    password_expires_at = Column(DateTime(timezone=True))
    
    # Preferences and Settings
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    notification_preferences = Column(JSON, default=dict)
    ui_preferences = Column(JSON, default=dict)
    
    # API Access
    api_key = Column(String(255), unique=True, nullable=True, index=True)
    api_key_created_at = Column(DateTime(timezone=True))
    api_key_last_used = Column(DateTime(timezone=True))
    api_rate_limit = Column(Integer, default=1000)  # Requests per hour
    
    # Compliance and Legal
    confidentiality_level = Column(SQLEnum(ConfidentialityLevel), default=ConfidentialityLevel.INTERNAL)
    data_retention_date = Column(DateTime(timezone=True))
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime(timezone=True))
    privacy_policy_accepted = Column(Boolean, default=False)
    terms_accepted = Column(Boolean, default=False)
    
    # Profile and Bio
    bio = Column(Text)
    profile_image_url = Column(String(500))
    linkedin_profile = Column(String(200))
    website = Column(String(200))
    
    # Relationships
    firm = relationship("LawFirm", back_populates="members")
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    created_cases = relationship("Case", foreign_keys="Case.created_by_id")
    assigned_cases = relationship("Case", foreign_keys="Case.assigned_attorney_id")
    audit_logs = relationship("AuditLog", foreign_keys="AuditLog.user_id")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_users_name', 'first_name', 'last_name'),
        Index('ix_users_status_type', 'status', 'user_type'),
        Index('ix_users_firm_type', 'firm_id', 'user_type'),
        Index('ix_users_last_activity', 'last_activity'),
        CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'", name='ck_valid_email'),
        UniqueConstraint('bar_number', 'bar_state', name='uq_bar_admission'),
    )
    
    @property
    def full_name(self) -> str:
        """Get full name with title and suffix"""
        parts = []
        if self.title:
            parts.append(self.title)
        parts.append(self.first_name)
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        if self.professional_suffix:
            parts.append(self.professional_suffix)
        return ' '.join(parts)
    
    @property
    def display_name(self) -> str:
        """Get display name (first + last)"""
        return f"{self.first_name} {self.last_name}"
    
    def set_password(self, password: str):
        """Set password hash"""
        self.password_hash = pwd_context.hash(password)
        self.password_changed_at = datetime.now(timezone.utc)
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        if not self.password_hash:
            return False
        return pwd_context.verify(password, self.password_hash)
    
    def generate_api_key(self) -> str:
        """Generate new API key"""
        import secrets
        self.api_key = secrets.token_urlsafe(32)
        self.api_key_created_at = datetime.now(timezone.utc)
        return self.api_key
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has specific permission"""
        for role in self.roles:
            if role.has_permission(permission_name):
                return True
        return False
    
    def is_attorney(self) -> bool:
        """Check if user is an attorney"""
        return self.user_type == UserType.ATTORNEY and bool(self.bar_number)
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format"""
        import re
        if not email or not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
            raise ValueError("Invalid email format")
        return email.lower().strip()
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.display_name}')>"


class LawFirm(NamedModel):
    """Law firm or legal organization"""
    
    __tablename__ = 'law_firms'
    
    # Basic Information
    short_name = Column(String(100))  # Abbreviated name
    legal_name = Column(String(300))  # Full legal name
    firm_type = Column(String(50), default='law_firm')  # law_firm, corporate_legal, government
    
    # Contact Information
    website = Column(String(200))
    email = Column(String(255))
    phone = Column(String(20))
    fax = Column(String(20))
    
    # Address
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(100), default='United States')
    
    # Firm Details
    size = Column(SQLEnum(FirmSize), default=FirmSize.SMALL)
    attorney_count = Column(Integer, default=0)
    founded_year = Column(Integer)
    
    # Practice Areas
    primary_practice_areas = Column(JSON, default=list)  # List of PracticeArea values
    secondary_practice_areas = Column(JSON, default=list)
    
    # Business Information
    tax_id = Column(String(20))  # EIN or similar
    state_bar_id = Column(String(50))
    
    # Billing and Accounting
    billing_address_same = Column(Boolean, default=True)
    billing_address_line1 = Column(String(200))
    billing_address_line2 = Column(String(200))
    billing_city = Column(String(100))
    billing_state = Column(String(50))
    billing_postal_code = Column(String(20))
    billing_country = Column(String(100))
    
    # Settings
    default_hourly_rate = Column(Integer)  # In cents
    default_currency = Column(String(3), default='USD')
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(50), default='active')
    
    # Relationships
    members = relationship("User", back_populates="firm")
    clients = relationship("Client", back_populates="firm")
    cases = relationship("Case", back_populates="firm")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_law_firms_size_status', 'size', 'status'),
        Index('ix_law_firms_location', 'city', 'state'),
        UniqueConstraint('legal_name', 'state', name='uq_firm_legal_name_state'),
    )
    
    @property
    def primary_practice_area_names(self) -> List[str]:
        """Get primary practice area names"""
        if not self.primary_practice_areas:
            return []
        return [area for area in self.primary_practice_areas if area in [e.value for e in PracticeArea]]
    
    def add_practice_area(self, area: PracticeArea, is_primary: bool = True):
        """Add practice area to firm"""
        area_value = area.value if isinstance(area, PracticeArea) else area
        
        if is_primary:
            if not self.primary_practice_areas:
                self.primary_practice_areas = []
            if area_value not in self.primary_practice_areas:
                self.primary_practice_areas.append(area_value)
        else:
            if not self.secondary_practice_areas:
                self.secondary_practice_areas = []
            if area_value not in self.secondary_practice_areas:
                self.secondary_practice_areas.append(area_value)
    
    def __repr__(self):
        return f"<LawFirm(id={self.id}, name='{self.name}', size='{self.size.value if self.size else None}')>"


class Client(BaseModel):
    """Client of the law firm"""
    
    __tablename__ = 'clients'
    
    # Client Type
    is_individual = Column(Boolean, default=True, nullable=False)
    
    # Individual Client Information
    first_name = Column(String(100))
    last_name = Column(String(100))
    middle_name = Column(String(100))
    title = Column(String(50))
    date_of_birth = Column(DateTime(timezone=True))
    ssn_last_four = Column(String(4))  # Last 4 digits only for privacy
    
    # Corporate Client Information
    company_name = Column(String(300))
    legal_entity_type = Column(String(50))  # LLC, Corp, Partnership, etc.
    tax_id = Column(String(20))
    industry = Column(String(100))
    annual_revenue = Column(Integer)  # In cents
    employee_count = Column(Integer)
    
    # Contact Information
    email = Column(String(255), index=True)
    phone = Column(String(20))
    mobile_phone = Column(String(20))
    preferred_contact_method = Column(String(20), default='email')
    
    # Address
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(100), default='United States')
    
    # Professional Information
    occupation = Column(String(100))
    employer = Column(String(200))
    referral_source = Column(String(200))
    
    # Relationship with Firm
    firm_id = Column(Integer, ForeignKey('law_firms.id'), nullable=False)
    client_number = Column(String(50), unique=True, index=True)
    relationship_manager_id = Column(Integer, ForeignKey('users.id'))
    client_since = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Status and Classification
    status = Column(String(50), default='active')
    client_type = Column(String(50))  # corporate, individual, nonprofit, government
    risk_level = Column(String(20), default='low')  # low, medium, high
    confidentiality_level = Column(SQLEnum(ConfidentialityLevel), default=ConfidentialityLevel.CONFIDENTIAL)
    
    # Billing Information
    hourly_rate = Column(Integer)  # In cents, override firm default
    billing_address_same = Column(Boolean, default=True)
    billing_contact_name = Column(String(200))
    billing_email = Column(String(255))
    billing_phone = Column(String(20))
    payment_terms = Column(String(50), default='net_30')
    credit_limit = Column(Integer)  # In cents
    
    # Legal Hold and Compliance
    legal_hold_active = Column(Boolean, default=False)
    conflicts_checked = Column(Boolean, default=False)
    conflicts_cleared = Column(Boolean, default=False)
    kyc_completed = Column(Boolean, default=False)  # Know Your Customer
    kyc_date = Column(DateTime(timezone=True))
    
    # Notes and Communication
    notes = Column(Text)
    communication_preferences = Column(JSON, default=dict)
    special_instructions = Column(Text)
    
    # Relationships
    firm = relationship("LawFirm", back_populates="clients")
    relationship_manager = relationship("User", foreign_keys=[relationship_manager_id])
    cases = relationship("Case", back_populates="client")
    user_account = relationship("User", secondary=user_firms, viewonly=True)
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_clients_firm_status', 'firm_id', 'status'),
        Index('ix_clients_name', 'first_name', 'last_name', 'company_name'),
        Index('ix_clients_contact', 'email', 'phone'),
        CheckConstraint("(is_individual = true AND first_name IS NOT NULL AND last_name IS NOT NULL) OR (is_individual = false AND company_name IS NOT NULL)", name='ck_client_name_required'),
        UniqueConstraint('firm_id', 'client_number', name='uq_client_number_per_firm'),
    )
    
    @property
    def display_name(self) -> str:
        """Get display name based on client type"""
        if self.is_individual:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.company_name or "Unknown Client"
    
    @property
    def full_name(self) -> str:
        """Get full name with title"""
        if self.is_individual:
            parts = []
            if self.title:
                parts.append(self.title)
            parts.append(self.first_name)
            if self.middle_name:
                parts.append(self.middle_name)
            parts.append(self.last_name)
            return ' '.join(parts)
        else:
            return self.company_name or "Unknown Client"
    
    def generate_client_number(self) -> str:
        """Generate unique client number"""
        import random
        import string
        
        if self.firm_id:
            # Generate format: FIRM_ID-YYYY-NNNNN
            year = datetime.now().year
            random_suffix = ''.join(random.choices(string.digits, k=5))
            self.client_number = f"{self.firm_id:04d}-{year}-{random_suffix}"
        
        return self.client_number
    
    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.display_name}', firm_id={self.firm_id})>"


# =============================================================================
# ROLE-BASED ACCESS CONTROL
# =============================================================================

class Role(NamedModel):
    """Role for role-based access control"""
    
    __tablename__ = 'roles'
    
    # Role Properties
    is_system_role = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    level = Column(Integer, default=0)  # Role hierarchy level
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if role has specific permission"""
        return any(perm.name == permission_name for perm in self.permissions)
    
    def add_permission(self, permission: "Permission"):
        """Add permission to role"""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: "Permission"):
        """Remove permission from role"""
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', level={self.level})>"


class Permission(NamedModel):
    """Permission for access control"""
    
    __tablename__ = 'permissions'
    
    # Permission Properties
    resource = Column(String(100), nullable=False, index=True)  # What resource
    action = Column(SQLEnum(PermissionType), nullable=False)    # What action
    scope = Column(String(100))  # Optional scope limitation
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint('resource', 'action', 'scope', name='uq_permission'),
        Index('ix_permissions_resource_action', 'resource', 'action'),
    )
    
    @property
    def full_name(self) -> str:
        """Get full permission name"""
        if self.scope:
            return f"{self.resource}:{self.action.value}:{self.scope}"
        return f"{self.resource}:{self.action.value}"
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.full_name}')>"


# =============================================================================
# EXPORT ALL MODELS
# =============================================================================

__all__ = [
    'User',
    'LawFirm', 
    'Client',
    'Role',
    'Permission',
    'UserType',
    'UserStatus',
    'PermissionType',
    'AuthenticationMethod',
    'FirmSize',
    'PracticeArea',
    'user_roles',
    'role_permissions',
    'user_firms'
]