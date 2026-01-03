"""
Database Configuration and Session Management for Legal AI System

Provides SQLAlchemy database connectivity and session management.
Simplified for SQLite development.
"""

import os
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# =============================================================================
# DATABASE ENGINE CONFIGURATION
# =============================================================================

# Environment-aware database configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DATABASE_URL = os.getenv('DATABASE_URL')

# Railway uses postgres:// but SQLAlchemy requires postgresql://
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    logger.info("Converted postgres:// to postgresql:// for SQLAlchemy compatibility")

# If no DATABASE_URL is provided, use defaults based on environment
if not DATABASE_URL:
    if ENVIRONMENT == 'production':
        # Production should ALWAYS use PostgreSQL from environment
        logger.error("CRITICAL: DATABASE_URL not set in production environment!")
        raise ValueError("DATABASE_URL must be set in production environment")
    else:
        # Development defaults to SQLite for simplicity
        DATABASE_URL = 'sqlite:///./legal_ai.db'
        logger.info("Using SQLite for development (set DATABASE_URL for PostgreSQL)")

# Connection arguments based on database type
connect_args = {}
if 'sqlite' in DATABASE_URL:
    connect_args = {'check_same_thread': False}

# Pool settings for PostgreSQL
pool_settings = {}
if 'postgresql' in DATABASE_URL:
    pool_settings = {
        'pool_size': 20,
        'max_overflow': 40,
        'pool_pre_ping': True,  # Verify connections before using
        'pool_recycle': 3600,  # Recycle connections after 1 hour
    }

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set to True for SQL debugging
    **pool_settings
)

logger.info(f"Database engine configured: {DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else 'SQLite'}")

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# =============================================================================
# DATABASE MODELS BASE
# =============================================================================

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)

# =============================================================================
# SESSION DEPENDENCY FUNCTIONS
# =============================================================================

def get_db():
    """
    Dependency function for FastAPI to get database session.

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Compatibility aliases for existing code
get_async_session = get_db
get_db_session = get_db
async_engine = engine
sync_engine = engine
AsyncSessionLocal = SessionLocal

def get_sync_session():
    """
    Direct session for synchronous operations.

    Usage:
        with get_sync_session() as db:
            ...
    """
    return SessionLocal()

def get_async_session_context():
    """
    Context manager for database session.

    Usage:
        with get_async_session_context() as db:
            result = db.execute(select(User))
    """
    return SessionLocal()

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_database():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

def close_database():
    """Close database connections."""
    engine.dispose()