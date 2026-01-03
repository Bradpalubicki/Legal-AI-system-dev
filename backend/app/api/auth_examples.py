"""
Authentication Examples API Router
Demonstrates all authentication patterns
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.api.deps import (
    get_current_user,
    get_current_user_id,
    get_admin_user,
    get_optional_user,
    require_role,
    CurrentUser
)

router = APIRouter(prefix="/api/v1/auth-examples", tags=["Auth Examples"])

# =============================================================================
# EXAMPLE 1: Public Endpoint (No Auth Required)
# =============================================================================

@router.get("/public")
async def public_endpoint():
    """
    Public endpoint - anyone can access

    No authentication required
    """
    return {
        "message": "This is a public endpoint",
        "auth_required": False,
        "accessible_by": "everyone"
    }


# =============================================================================
# EXAMPLE 2: Protected Endpoint (Auth Required)
# =============================================================================

@router.get("/protected")
async def protected_endpoint(user: CurrentUser = Depends(get_current_user)):
    """
    Protected endpoint - authentication required

    In development mode: Works with auto-generated mock user
    In production mode: Requires valid JWT token
    """
    return {
        "message": f"Hello, {user.user_id}!",
        "auth_required": True,
        "user_id": user.user_id,
        "auth_method": user.auth_method,
        "roles": user.roles,
        "permissions": user.permissions[:5] if user.permissions != ['*'] else ['all'],
        "note": "In dev mode, this is a mock user. In prod, this would be real."
    }


# =============================================================================
# EXAMPLE 3: User ID Only (Lightweight)
# =============================================================================

@router.get("/user-id-only")
async def user_id_only_endpoint(user_id: str = Depends(get_current_user_id)):
    """
    Get just the user ID (lightweight alternative to full CurrentUser)

    Use this when you only need the user ID, not roles/permissions
    """
    return {
        "message": "This endpoint only needs the user ID",
        "user_id": user_id,
        "note": "Lighter than get_current_user - use when you don't need roles/permissions"
    }


# =============================================================================
# EXAMPLE 4: Admin Only
# =============================================================================

@router.get("/admin-only")
async def admin_only_endpoint(admin: CurrentUser = Depends(get_admin_user)):
    """
    Admin-only endpoint

    Requires: Valid JWT token + admin role
    """
    return {
        "message": "Admin access granted",
        "admin_id": admin.user_id,
        "roles": admin.roles,
        "note": "Only users with 'admin' or 'administrator' role can access this"
    }


# =============================================================================
# EXAMPLE 5: Custom Role Required
# =============================================================================

@router.get("/moderator-only")
async def moderator_only_endpoint(
    user: CurrentUser = Depends(require_role("moderator"))
):
    """
    Moderator-only endpoint

    Requires: Valid JWT token + 'moderator' role
    """
    return {
        "message": "Moderator access granted",
        "moderator_id": user.user_id,
        "roles": user.roles,
        "note": "Only users with 'moderator' role can access this"
    }


# =============================================================================
# EXAMPLE 6: Optional Authentication
# =============================================================================

@router.get("/optional-auth")
async def optional_auth_endpoint(
    user: Optional[CurrentUser] = Depends(get_optional_user)
):
    """
    Endpoint that works with or without authentication

    Provides different features based on auth status
    """
    if user:
        return {
            "message": f"Welcome back, {user.user_id}!",
            "authenticated": True,
            "user_id": user.user_id,
            "premium_features": True,
            "personalized": True
        }
    else:
        return {
            "message": "Welcome, guest!",
            "authenticated": False,
            "premium_features": False,
            "personalized": False,
            "note": "Sign in for premium features"
        }


# =============================================================================
# EXAMPLE 7: Ownership Check
# =============================================================================

@router.get("/documents/{doc_id}")
async def get_document_with_ownership(
    doc_id: str,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get document with ownership verification

    Demonstrates checking if user owns the resource
    """
    # Simulate fetching a document
    mock_document = {
        "id": doc_id,
        "title": "Sample Legal Document",
        "owner_id": user.user_id,  # In real app, fetch from database
        "content": "This is a sample document..."
    }

    # Check ownership (allow admins to access any document)
    if mock_document["owner_id"] != user.user_id and 'admin' not in user.roles:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this document"
        )

    return {
        "document": mock_document,
        "accessed_by": user.user_id,
        "is_owner": mock_document["owner_id"] == user.user_id,
        "is_admin": 'admin' in user.roles
    }


# =============================================================================
# EXAMPLE 8: Get User Info
# =============================================================================

@router.get("/me")
async def get_current_user_info(user: CurrentUser = Depends(get_current_user)):
    """
    Get current authenticated user's information

    Common pattern for '/me' or '/profile' endpoints
    """
    return {
        "user_id": user.user_id,
        "auth_method": user.auth_method,
        "authenticated_at": user.authenticated_at.isoformat(),
        "roles": user.roles,
        "permissions": user.permissions if user.permissions != ['*'] else ['all'],
        "token_payload": user.token_payload
    }


# =============================================================================
# EXAMPLE 9: Multiple Auth Checks
# =============================================================================

@router.post("/sensitive-action")
async def sensitive_action(
    action: str,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Perform sensitive action with multiple checks

    Demonstrates role and permission checking in the endpoint
    """
    # Check if user has required role
    if 'admin' not in user.roles and 'moderator' not in user.roles:
        raise HTTPException(
            status_code=403,
            detail="Requires admin or moderator role"
        )

    # Check if user has specific permission
    required_permission = f"actions.{action}"
    if user.permissions != ['*'] and required_permission not in user.permissions:
        raise HTTPException(
            status_code=403,
            detail=f"Missing required permission: {required_permission}"
        )

    return {
        "message": f"Action '{action}' performed successfully",
        "performed_by": user.user_id,
        "roles": user.roles,
        "note": "This action required admin/moderator role and specific permission"
    }


# =============================================================================
# EXAMPLE 10: Health Check (Shows Auth Status)
# =============================================================================

@router.get("/auth-status")
async def auth_status(user: Optional[CurrentUser] = Depends(get_optional_user)):
    """
    Check authentication status

    Useful for debugging and understanding auth state
    """
    return {
        "authenticated": user is not None,
        "user_id": user.user_id if user else None,
        "auth_method": user.auth_method if user else None,
        "roles": user.roles if user else [],
        "development_mode": user.auth_method == "development" if user else True,
        "note": "In dev mode, all requests are auto-authenticated"
    }
