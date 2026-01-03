"""
Legal AI System - PACER Credentials Model
Secure storage of user PACER credentials with encryption
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from ..src.core.database import Base


class UserPACERCredentials(Base):
    """
    Stores encrypted PACER credentials for users.

    Security Notes:
    - Passwords are encrypted before storage
    - Uses Fernet encryption from cryptography library
    - Encryption key stored securely in environment/vault
    """
    __tablename__ = "user_pacer_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # PACER credentials (encrypted)
    pacer_username = Column(String(255), nullable=False)
    pacer_password_encrypted = Column(Text, nullable=False)  # Encrypted with Fernet
    pacer_client_code = Column(String(100))  # Optional client code for billing

    # Environment (production vs qa)
    environment = Column(String(20), default="production", nullable=False)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Verified by successful auth
    last_verified_at = Column(DateTime)

    # Usage tracking
    last_used_at = Column(DateTime)
    total_searches = Column(Integer, default=0)
    total_downloads = Column(Integer, default=0)

    # Cost tracking
    total_cost = Column(Float, default=0.0)
    daily_cost_limit = Column(Float, default=100.0)
    monthly_cost_limit = Column(Float, default=1000.0)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship to user
    # user = relationship("User", back_populates="pacer_credentials")

    def __repr__(self):
        return f"<UserPACERCredentials(user_id={self.user_id}, username={self.pacer_username}, env={self.environment})>"


class PACERSearchHistory(Base):
    """
    Tracks PACER search history for users.
    Useful for analytics, cost tracking, and repeating searches.
    """
    __tablename__ = "pacer_search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Search details
    search_type = Column(String(50), nullable=False)  # 'case', 'party'
    search_criteria = Column(JSON, nullable=False)  # Search parameters

    # Results
    results_count = Column(Integer, default=0)
    results_summary = Column(JSON)  # Summary of top results

    # Cost
    search_cost = Column(Float, default=0.0)

    # Metadata
    court = Column(String(10))
    timestamp = Column(DateTime, default=func.now(), index=True)

    # Relationship
    # user = relationship("User", back_populates="pacer_searches")

    def __repr__(self):
        return f"<PACERSearchHistory(user_id={self.user_id}, type={self.search_type}, court={self.court})>"


class PACERDocument(Base):
    """
    Tracks PACER documents downloaded by users.
    Links downloaded documents to cases and provides metadata.
    """
    __tablename__ = "pacer_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Document identification
    document_id = Column(String(255), nullable=False, index=True)
    case_id = Column(String(255), nullable=False, index=True)
    document_number = Column(String(50))

    # Document details
    title = Column(String(500))
    document_type = Column(String(100))  # 'complaint', 'motion', etc.
    filing_date = Column(DateTime)

    # File information
    file_path = Column(String(1000))  # Local storage path
    file_size = Column(Integer)  # Bytes
    page_count = Column(Integer)
    file_hash = Column(String(64))  # SHA-256 checksum

    # PACER information
    pacer_url = Column(String(1000))
    court = Column(String(10))
    download_cost = Column(Float, default=0.0)

    # Status
    download_status = Column(String(50), default="completed")
    is_available = Column(Boolean, default=True)

    # Metadata
    document_metadata = Column(JSON)  # Additional document metadata

    # Timestamps
    downloaded_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    # Relationship
    # user = relationship("User", back_populates="pacer_documents")

    def __repr__(self):
        return f"<PACERDocument(document_id={self.document_id}, case_id={self.case_id}, title={self.title})>"


class PACERCostTracking(Base):
    """
    Detailed PACER cost tracking per user.
    Tracks individual operations and costs for billing and reporting.
    """
    __tablename__ = "pacer_cost_tracking"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Operation details
    operation_type = Column(String(50), nullable=False)  # 'search', 'download', 'docket_view'
    operation_description = Column(String(500))

    # Cost
    cost = Column(Float, nullable=False)
    pages = Column(Integer, default=0)

    # Associated records
    case_id = Column(String(255))
    document_id = Column(String(255))
    court = Column(String(10))

    # Timestamp
    timestamp = Column(DateTime, default=func.now(), index=True)

    # Relationship
    # user = relationship("User", back_populates="pacer_costs")

    def __repr__(self):
        return f"<PACERCostTracking(user_id={self.user_id}, operation={self.operation_type}, cost=${self.cost})>"
