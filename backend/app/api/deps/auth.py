"""
Authentication Dependencies for FastAPI Routes

Provides dependency functions to extract authenticated user information
from requests processed by SecureAuthenticationMiddleware.
"""

from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from datetime import datetime


class CurrentUser:
    """Current authenticated user information"""
    def __init__(
        self,
        user_id: str,
        auth_method: str,
        authenticated_at: datetime,
        token_payload: Optional[dict] = None
    ):
        # Always convert user_id to string for database compatibility
        self.user_id = str(user_id) if user_id is not None else None
        self.auth_method = auth_method
        self.authenticated_at = authenticated_at
        self.token_payload = token_payload or {}
        self.roles = self.token_payload.get('roles', [])
        self.permissions = self.token_payload.get('permissions', [])

        # Extract common fields from token payload for convenience
        self.email = self.token_payload.get('email')
        self.role = self.token_payload.get('role')  # Single role string
        self.username = self.token_payload.get('username')
        self.first_name = self.token_payload.get('first_name')
        self.last_name = self.token_payload.get('last_name')

    @property
    def id(self) -> str:
        """Alias for user_id for compatibility"""
        return self.user_id


async def get_current_user(request: Request) -> CurrentUser:
    """
    Get current authenticated user from request state.

    This dependency requires SecureAuthenticationMiddleware to be active.
    The middleware sets request.state.user_id after successful authentication.

    Usage:
        @router.get("/protected")
        async def protected_route(user: CurrentUser = Depends(get_current_user)):
            return {"user_id": user.user_id}

    Raises:
        HTTPException: 401 if user is not authenticated
    """
    # Check if authentication middleware set user_id
    user_id = getattr(request.state, 'user_id', None)

    print(f"[AUTH] get_current_user called for {request.url.path}")
    print(f"[AUTH] user_id from request.state: {user_id}")
    print(f"[AUTH] request.state attributes: {dir(request.state)}")

    if not user_id:
        print(f"[AUTH] No user_id found - returning 401")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract auth information from request state
    auth_method = getattr(request.state, 'auth_method', 'unknown')
    authenticated_at = getattr(request.state, 'authenticated_at', datetime.utcnow())
    token_payload = getattr(request.state, 'token_payload', {})

    return CurrentUser(
        user_id=user_id,
        auth_method=auth_method,
        authenticated_at=authenticated_at,
        token_payload=token_payload
    )


async def get_current_user_id(request: Request) -> str:
    """
    Get current user ID only (lighter version of get_current_user).

    Usage:
        @router.get("/my-data")
        async def get_my_data(user_id: str = Depends(get_current_user_id)):
            return {"user_id": user_id}
    """
    user = await get_current_user(request)
    return user.user_id


async def get_optional_user(request: Request) -> Optional[CurrentUser]:
    """
    Get current user if authenticated, None otherwise.

    Use for endpoints that work both with and without authentication.

    Usage:
        @router.get("/public-or-private")
        async def flexible_route(user: Optional[CurrentUser] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.user_id}"}
            return {"message": "Hello guest"}
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


async def get_admin_user(request: Request) -> CurrentUser:
    """
    Get current user and verify they have admin role.

    Usage:
        @router.post("/admin/settings")
        async def admin_only(user: CurrentUser = Depends(get_admin_user)):
            return {"message": "Admin access granted"}

    Raises:
        HTTPException: 403 if user doesn't have admin role
    """
    user = await get_current_user(request)

    # Check if user has admin role
    if 'admin' not in user.roles and 'administrator' not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required"
        )

    return user


def require_role(required_role: str):
    """
    Dependency factory for role-based access control.

    Usage:
        @router.get("/moderator-only")
        async def moderator_route(user: CurrentUser = Depends(require_role("moderator"))):
            return {"message": "Moderator access granted"}

    Args:
        required_role: Role name required to access the endpoint

    Returns:
        Dependency function that checks for the required role
    """
    async def role_checker(request: Request) -> CurrentUser:
        user = await get_current_user(request)

        if required_role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )

        return user

    return role_checker


def require_permission(required_permission: str):
    """
    Dependency factory for permission-based access control.

    Usage:
        @router.delete("/documents/{doc_id}")
        async def delete_doc(
            doc_id: str,
            user: CurrentUser = Depends(require_permission("documents.delete"))
        ):
            return {"message": "Document deleted"}

    Args:
        required_permission: Permission required to access the endpoint

    Returns:
        Dependency function that checks for the required permission
    """
    async def permission_checker(request: Request) -> CurrentUser:
        user = await get_current_user(request)

        if required_permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required"
            )

        return user

    return permission_checker


# Development/testing helpers
async def get_mock_user(request: Request) -> CurrentUser:
    """
    Mock user for development/testing when auth middleware is disabled.

    DO NOT USE IN PRODUCTION!
    """
    return CurrentUser(
        user_id="dev-user-123",
        auth_method="mock",
        authenticated_at=datetime.utcnow(),
        token_payload={
            'roles': ['user', 'admin'],
            'permissions': ['*']
        }
    )
