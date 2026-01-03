"""
Base models and utilities for the Legal AI System database.

Provides common base classes, mixins, and utilities used across all database models.
"""

import enum
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates
import uuid


# Create the declarative base
Base = declarative_base()


# =============================================================================
# COMMON ENUMS
# =============================================================================

class StatusEnum(enum.Enum):
    """Generic status enum for various entities"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class PriorityEnum(enum.Enum):
    """Priority levels for tasks, cases, etc."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class ConfidentialityLevel(enum.Enum):
    """Document and case confidentiality levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


# =============================================================================
# BASE MIXINS
# =============================================================================

class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models"""
    
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False,
        doc="Timestamp when the record was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), 
        nullable=False,
        doc="Timestamp when the record was last updated"
    )


class UUIDMixin:
    """Mixin to add UUID field"""
    
    uuid = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
        doc="Unique identifier for external references"
    )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality"""
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the record was soft deleted"
    )
    
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Flag indicating if record is soft deleted"
    )
    
    def soft_delete(self):
        """Mark record as soft deleted"""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self):
        """Restore soft deleted record"""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """Mixin to add audit trail fields"""
    
    created_by_id = Column(
        Integer,
        nullable=True,
        doc="ID of user who created the record"
    )
    
    updated_by_id = Column(
        Integer,
        nullable=True,
        doc="ID of user who last updated the record"
    )
    
    version = Column(
        Integer,
        default=1,
        nullable=False,
        doc="Version number for optimistic locking"
    )


class MetadataMixin:
    """Mixin to add metadata and custom fields"""

    record_metadata = Column(
        JSON,
        default=dict,
        nullable=False,
        doc="Metadata and custom fields"
    )
    
    tags = Column(
        JSON,
        default=list,
        nullable=False,
        doc="Tags for categorization and search"
    )
    
    def add_tag(self, tag: str):
        """Add a tag to the record"""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the record"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag: str) -> bool:
        """Check if record has a specific tag"""
        return self.tags and tag in self.tags


class BaseModelMixin(TimestampMixin, UUIDMixin, SoftDeleteMixin, AuditMixin, MetadataMixin):
    """Complete base mixin with all common fields"""
    
    id = Column(
        Integer, 
        primary_key=True, 
        index=True, 
        autoincrement=True,
        doc="Primary key identifier"
    )


# =============================================================================
# BASE MODEL CLASSES
# =============================================================================

class BaseModel(Base, BaseModelMixin):
    """Abstract base model with all common functionality"""
    
    __abstract__ = True
    
    def to_dict(self, exclude_private: bool = True) -> Dict[str, Any]:
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            if exclude_private and column.name.startswith('_'):
                continue
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = float(value)
            elif isinstance(value, enum.Enum):
                value = value.value
            result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude_fields: Optional[set] = None):
        """Update model from dictionary"""
        exclude_fields = exclude_fields or {'id', 'created_at', 'uuid'}
        
        for key, value in data.items():
            if key in exclude_fields:
                continue
            if hasattr(self, key):
                setattr(self, key, value)
    
    @validates('tags')
    def validate_tags(self, key, tags):
        """Validate tags format"""
        if tags is None:
            return []
        if not isinstance(tags, list):
            raise ValueError("Tags must be a list")
        return [str(tag).strip() for tag in tags if tag and str(tag).strip()]
    
    @validates('metadata')
    def validate_metadata(self, key, metadata):
        """Validate metadata format"""
        if metadata is None:
            return {}
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")
        return metadata


class NamedModel(BaseModel):
    """Base model for entities with name and description"""
    
    __abstract__ = True
    
    name = Column(
        String(200),
        nullable=False,
        index=True,
        doc="Name of the entity"
    )
    
    description = Column(
        Text,
        nullable=True,
        doc="Description of the entity"
    )
    
    @validates('name')
    def validate_name(self, key, name):
        """Validate name field"""
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        return name.strip()


class StatusModel(BaseModel):
    """Base model for entities with status"""
    
    __abstract__ = True
    
    status = Column(
        String(50),
        default="active",
        nullable=False,
        index=True,
        doc="Current status of the entity"
    )
    
    status_changed_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when status was last changed"
    )
    
    status_changed_by_id = Column(
        Integer,
        nullable=True,
        doc="ID of user who last changed the status"
    )
    
    def change_status(self, new_status: str, user_id: Optional[int] = None):
        """Change entity status"""
        if self.status != new_status:
            self.status = new_status
            self.status_changed_at = datetime.now(timezone.utc)
            self.status_changed_by_id = user_id


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_database_url(
    driver: str = "postgresql+asyncpg",
    username: str = None,
    password: str = None,
    host: str = "localhost",
    port: int = 5432,
    database: str = None
) -> str:
    """Create database URL from components"""
    if not all([username, password, database]):
        raise ValueError("Username, password, and database are required")
    
    return f"{driver}://{username}:{password}@{host}:{port}/{database}"


def generate_table_name(class_name: str) -> str:
    """Generate table name from class name using snake_case"""
    import re
    
    # Convert CamelCase to snake_case
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', class_name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    # Add plural 's' if not already plural
    if not s2.endswith('s'):
        s2 += 's'
    
    return s2


# =============================================================================
# DATABASE UTILITIES
# =============================================================================

class DatabaseUtils:
    """Utility class for database operations"""
    
    @staticmethod
    def get_enum_values(enum_class) -> list:
        """Get all values from an enum class"""
        return [item.value for item in enum_class]
    
    @staticmethod
    def create_search_vector_column(columns: list) -> str:
        """Create PostgreSQL search vector for full-text search"""
        column_parts = []
        for col in columns:
            if isinstance(col, tuple):
                column, weight = col
                column_parts.append(f"setweight(to_tsvector('english', COALESCE({column}, '')), '{weight}')")
            else:
                column_parts.append(f"to_tsvector('english', COALESCE({col}, ''))")
        
        return " || ".join(column_parts)
    
    @staticmethod
    def create_gin_index(table_name: str, column_name: str) -> str:
        """Create GIN index for JSONB or array columns"""
        index_name = f"idx_{table_name}_{column_name}_gin"
        return f"CREATE INDEX {index_name} ON {table_name} USING gin ({column_name});"
    
    @staticmethod
    def create_partial_index(table_name: str, column_name: str, condition: str) -> str:
        """Create partial index with condition"""
        index_name = f"idx_{table_name}_{column_name}_partial"
        return f"CREATE INDEX {index_name} ON {table_name} ({column_name}) WHERE {condition};"


# =============================================================================
# EXPORT ALL
# =============================================================================

__all__ = [
    'Base',
    'StatusEnum',
    'PriorityEnum', 
    'ConfidentialityLevel',
    'TimestampMixin',
    'UUIDMixin',
    'SoftDeleteMixin',
    'AuditMixin',
    'MetadataMixin',
    'BaseModelMixin',
    'BaseModel',
    'NamedModel',
    'StatusModel',
    'create_database_url',
    'generate_table_name',
    'DatabaseUtils'
]