"""
API Dependencies Module
Provides reusable dependency functions for FastAPI routes
"""

from .auth import (
    CurrentUser,
    get_current_user,
    get_current_user_id,
    get_admin_user,
    get_optional_user,
    require_role,
    require_permission
)

__all__ = [
    'CurrentUser',
    'get_current_user',
    'get_current_user_id',
    'get_admin_user',
    'get_optional_user',
    'require_role',
    'require_permission'
]
