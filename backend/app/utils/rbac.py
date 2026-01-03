"""
Legal AI System - Role-Based Access Control (RBAC)
Decorators and utilities for role-based and permission-based access control
"""

from functools import wraps
from typing import Callable
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.orm import Session

from ..models.user import User, UserRole
from ..src.core.database import get_db
from ..api.deps import get_current_user, CurrentUser


# ============================================================================
# ROLE-BASED DECORATORS
# ============================================================================

def require_role(required_role: UserRole):
    """
    Decorator factory to require a specific role or higher.

    Uses role hierarchy: GUEST (1) < USER (2) < ADMIN (3)

    Usage:
        @router.get("/admin/users")
        @require_role(UserRole.ADMIN)
        async def get_all_users(current_user: CurrentUser = Depends(get_current_user)):
            # Only admins can access
            return {"users": [...]}

    Args:
        required_role: The minimum role required (UserRole enum)

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: CurrentUser = Depends(get_current_user),
            db: Session = Depends(get_db),
            **kwargs
        ):
            # Get full user object from database
            user = db.query(User).filter(User.id == current_user.user_id).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Check role hierarchy
            if not user.has_role(required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {required_role.value} role or higher"
                )

            return await func(*args, current_user=current_user, **kwargs)

        return wrapper
    return decorator


def require_admin(func: Callable):
    """
    Decorator to require admin role.

    Shorthand for @require_role(UserRole.ADMIN)

    Usage:
        @router.post("/admin/settings")
        @require_admin
        async def update_settings(current_user: CurrentUser = Depends(get_current_user)):
            return {"message": "Settings updated"}
    """
    return require_role(UserRole.ADMIN)(func)


def require_user(func: Callable):
    """
    Decorator to require at least USER role (excludes GUEST).

    Usage:
        @router.post("/documents/upload")
        @require_user
        async def upload_document(current_user: CurrentUser = Depends(get_current_user)):
            return {"message": "Document uploaded"}
    """
    return require_role(UserRole.USER)(func)


# ============================================================================
# RESOURCE OWNERSHIP DECORATORS
# ============================================================================

def require_own_resource(resource_id_param: str = "resource_id"):
    """
    Decorator factory to require user owns the resource or is admin.

    Usage:
        @router.get("/documents/{document_id}")
        @require_own_resource(resource_id_param="document_id")
        async def get_document(
            document_id: str,
            current_user: CurrentUser = Depends(get_current_user)
        ):
            # User must own this document or be admin
            return {"document": {...}}

    Args:
        resource_id_param: Name of the parameter containing the resource owner ID

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: CurrentUser = Depends(get_current_user),
            db: Session = Depends(get_db),
            **kwargs
        ):
            # Get resource owner ID from kwargs
            resource_owner_id = kwargs.get(resource_id_param)

            if not resource_owner_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required parameter: {resource_id_param}"
                )

            # Get full user object from database
            user = db.query(User).filter(User.id == current_user.user_id).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Check ownership or admin access
            if not user.can_access_resource(resource_owner_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You don't own this resource"
                )

            return await func(*args, current_user=current_user, **kwargs)

        return wrapper
    return decorator


# ============================================================================
# PERMISSION-BASED DECORATORS
# ============================================================================

def require_permission(permission: str):
    """
    Decorator factory to require a specific permission.

    Note: Permissions must be stored in user.token_payload['permissions']

    Usage:
        @router.delete("/documents/{doc_id}")
        @require_permission("documents.delete")
        async def delete_document(
            doc_id: str,
            current_user: CurrentUser = Depends(get_current_user)
        ):
            return {"message": "Document deleted"}

    Args:
        permission: The required permission string

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: CurrentUser = Depends(get_current_user),
            **kwargs
        ):
            # Check if user has the required permission
            user_permissions = current_user.permissions

            # '*' means all permissions
            if '*' in user_permissions or permission in user_permissions:
                return await func(*args, current_user=current_user, **kwargs)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}"
            )

        return wrapper
    return decorator


def require_any_permission(*permissions: str):
    """
    Decorator factory to require ANY of the specified permissions.

    Usage:
        @router.get("/admin/reports")
        @require_any_permission("reports.view", "admin.full_access")
        async def get_reports(current_user: CurrentUser = Depends(get_current_user)):
            return {"reports": [...]}

    Args:
        *permissions: Variable number of permission strings

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: CurrentUser = Depends(get_current_user),
            **kwargs
        ):
            user_permissions = current_user.permissions

            # '*' means all permissions
            if '*' in user_permissions:
                return await func(*args, current_user=current_user, **kwargs)

            # Check if user has any of the required permissions
            if any(perm in user_permissions for perm in permissions):
                return await func(*args, current_user=current_user, **kwargs)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing one of required permissions: {', '.join(permissions)}"
            )

        return wrapper
    return decorator


def require_all_permissions(*permissions: str):
    """
    Decorator factory to require ALL of the specified permissions.

    Usage:
        @router.post("/admin/critical-action")
        @require_all_permissions("admin.write", "critical.execute")
        async def critical_action(current_user: CurrentUser = Depends(get_current_user)):
            return {"message": "Action executed"}

    Args:
        *permissions: Variable number of permission strings

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: CurrentUser = Depends(get_current_user),
            **kwargs
        ):
            user_permissions = current_user.permissions

            # '*' means all permissions
            if '*' in user_permissions:
                return await func(*args, current_user=current_user, **kwargs)

            # Check if user has all required permissions
            if all(perm in user_permissions for perm in permissions):
                return await func(*args, current_user=current_user, **kwargs)

            missing = [p for p in permissions if p not in user_permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing)}"
            )

        return wrapper
    return decorator


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_user_role(user: User, required_role: UserRole) -> bool:
    """
    Check if user has required role or higher.

    Args:
        user: User object
        required_role: Required UserRole

    Returns:
        True if user has required role or higher, False otherwise
    """
    return user.has_role(required_role)


def check_user_owns_resource(user: User, resource_owner_id: str) -> bool:
    """
    Check if user owns a resource or is admin.

    Args:
        user: User object
        resource_owner_id: ID of the resource owner

    Returns:
        True if user owns resource or is admin, False otherwise
    """
    return user.can_access_resource(resource_owner_id)


def get_user_permissions(current_user: CurrentUser) -> list:
    """
    Get list of user permissions from token payload.

    Args:
        current_user: CurrentUser object from get_current_user dependency

    Returns:
        List of permission strings
    """
    return current_user.permissions


def has_permission(current_user: CurrentUser, permission: str) -> bool:
    """
    Check if user has a specific permission.

    Args:
        current_user: CurrentUser object
        permission: Permission string to check

    Returns:
        True if user has permission, False otherwise
    """
    return '*' in current_user.permissions or permission in current_user.permissions
