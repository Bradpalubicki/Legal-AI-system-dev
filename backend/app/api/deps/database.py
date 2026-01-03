"""
Database Dependency for API Routes

Re-exports database utilities from core database module for consistent imports.
"""

from app.src.core.database import get_db, SessionLocal, engine

__all__ = ['get_db', 'SessionLocal', 'engine']
