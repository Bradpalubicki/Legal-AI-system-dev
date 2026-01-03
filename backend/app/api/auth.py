"""
Legal AI System - Authentication API
User registration, login, logout, and token management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Any
from datetime import datetime, timedelta
import re

from ..src.core.database import get_db
from ..models.user import User, UserRole
from ..utils.auth import (
    hash_password,
    verify_password,
    authenticate_user,
    create_tokens_for_user,
    refresh_access_token,
    get_current_user as get_auth_user,
    get_current_active_user
)
from ..api.deps import get_current_user, CurrentUser
from ..models.case_notification_history import CaseNotification

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    # Support both old and new format
    full_name: Optional[str] = Field(None, max_length=200)
    firstName: Optional[str] = Field(None, max_length=100)
    lastName: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = None
    termsAccepted: Optional[bool] = None
    acceptedDocuments: Optional[list] = None

    @validator('password')
    def validate_password(cls, v):
        """Validate password complexity"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict
    # New filings data for popup notification
    new_filings: Optional[dict] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_password(cls, v):
        """Validate password complexity"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserResponse(BaseModel):
    """User profile response"""
    id: str
    email: str
    username: Optional[str]
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: Optional[str]
    last_login_at: Optional[str]


class UserPreferencesResponse(BaseModel):
    """User preferences response"""
    show_new_filing_notifications: bool = True
    email_notifications: bool = True
    case_alerts: bool = True
    document_alerts: bool = True
    auto_download_enabled: bool = False
    auto_download_free_only: bool = False  # Default: download all docs within budget


class UpdatePreferencesRequest(BaseModel):
    """Update user preferences request"""
    show_new_filing_notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None
    case_alerts: Optional[bool] = None
    document_alerts: Optional[bool] = None
    auto_download_enabled: Optional[bool] = None
    auto_download_free_only: Optional[bool] = None


# Default preferences for new users
DEFAULT_PREFERENCES = {
    "show_new_filing_notifications": True,
    "email_notifications": True,
    "case_alerts": True,
    "document_alerts": True,
    "auto_download_enabled": False,
    "auto_download_free_only": False  # Default: download all docs within budget
}


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    - **email**: Valid email address (must be unique)
    - **username**: Unique username (3-50 characters, alphanumeric, -, _)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, number, special char)
    - **full_name**: Optional full name
    - **phone**: Optional phone number

    Returns JWT access and refresh tokens upon successful registration.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Handle firstName/lastName format from frontend
    if user_data.firstName and user_data.lastName:
        full_name = f"{user_data.firstName} {user_data.lastName}"
        first_name = user_data.firstName
        last_name = user_data.lastName
        # Generate username from email if not provided
        username = user_data.username or user_data.email.split('@')[0]
    else:
        full_name = user_data.full_name
        first_name = None
        last_name = None
        username = user_data.username

    # Check if username already exists
    if username:
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            # If auto-generated, append number
            if not user_data.username:
                username = f"{username}{existing_user.id if existing_user else 1}"
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )

    # Determine role
    user_role = UserRole.USER
    if user_data.role:
        role_map = {
            'ATTORNEY': UserRole.ATTORNEY,
            'CLIENT': UserRole.CLIENT,
            'ADMIN': UserRole.ADMIN,
            'USER': UserRole.USER
        }
        user_role = role_map.get(user_data.role.upper(), UserRole.USER)

    # Create new user
    new_user = User(
        email=user_data.email,
        username=username,
        hashed_password=hash_password(user_data.password),
        full_name=full_name,
        first_name=first_name,
        last_name=last_name,
        phone=user_data.phone,
        role=user_role,
        is_active=True,
        is_verified=False,  # Require email verification in production
        created_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create tokens
    tokens = create_tokens_for_user(new_user)

    return TokenResponse(**tokens)


@router.post("/login", response_model=TokenResponse)
async def login_user(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.

    - **email**: User's email address
    - **password**: User's password

    Returns access token (15 min expiry) and refresh token (7 day expiry).
    Also returns new_filings data for popup notification if user has
    new filing notifications enabled.

    Account will be locked for 30 minutes after 5 failed login attempts.
    """
    # IMPORTANT: Get user's previous_login_at BEFORE authentication updates timestamps
    # This is needed to check for new filings since last login
    pre_auth_user = db.query(User).filter(User.email == credentials.email).first()
    previous_login_at = None
    show_notifications = False

    if pre_auth_user:
        # Save the previous_login_at BEFORE authenticate_user updates it
        previous_login_at = pre_auth_user.previous_login_at or pre_auth_user.last_login_at
        # Check user preferences for notifications
        prefs = pre_auth_user.preferences or {}
        show_notifications = prefs.get('show_new_filing_notifications', True)
        print(f'[LOGIN] Pre-auth: previous_login_at={previous_login_at}, show_notifications={show_notifications}', flush=True)

    # Authenticate user (this updates timestamps)
    user = authenticate_user(db, credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )

    # Create tokens
    tokens = create_tokens_for_user(user)

    # Check for new filings if notifications are enabled
    # Always initialize with default values so it's always included in response
    new_filings_data = {
        "has_new_filings": False,
        "total_new_documents": 0,
        "cases_count": 0,
        "cases": [],
        "since": previous_login_at.isoformat() if previous_login_at else None
    }
    print(f'[LOGIN] Checking for new filings: show_notifications={show_notifications}, previous_login_at={previous_login_at}', flush=True)

    if show_notifications and previous_login_at:
        try:
            # Query notifications for this user since previous login
            notifications = db.query(CaseNotification).filter(
                CaseNotification.sent_at > previous_login_at,
                CaseNotification.notification_type == "new_documents"
            ).order_by(CaseNotification.sent_at.desc()).all()

            # Filter to only this user's notifications
            user_notifications = []
            for notification in notifications:
                extra = notification.extra_data or {}
                if str(extra.get("user_id")) == str(user.id):
                    user_notifications.append(notification)

            if user_notifications:
                # Group by case
                cases_with_new_filings = {}
                total_new_documents = 0

                for notification in user_notifications:
                    docket_id = notification.docket_id
                    if docket_id not in cases_with_new_filings:
                        cases_with_new_filings[docket_id] = {
                            "docket_id": docket_id,
                            "case_name": notification.case_name,
                            "court": notification.court,
                            "new_documents": [],
                            "document_count": 0,
                            "_seen_entries": set()  # Track seen entry numbers for deduplication
                        }
                    if notification.documents:
                        # Deduplicate documents by entry_number
                        for doc in notification.documents:
                            entry_num = doc.get('entry_number') or doc.get('entry_num')
                            if entry_num and entry_num not in cases_with_new_filings[docket_id]["_seen_entries"]:
                                cases_with_new_filings[docket_id]["_seen_entries"].add(entry_num)
                                cases_with_new_filings[docket_id]["new_documents"].append(doc)
                            elif not entry_num:
                                # No entry number, add anyway (shouldn't happen often)
                                cases_with_new_filings[docket_id]["new_documents"].append(doc)

                # Clean up internal tracking and update counts
                for case_data in cases_with_new_filings.values():
                    del case_data["_seen_entries"]
                    case_data["document_count"] = len(case_data["new_documents"])
                    total_new_documents += case_data["document_count"]

                cases_list = list(cases_with_new_filings.values())

                new_filings_data = {
                    "has_new_filings": len(cases_list) > 0,
                    "total_new_documents": total_new_documents,
                    "cases_count": len(cases_list),
                    "cases": cases_list,
                    "since": previous_login_at.isoformat() if previous_login_at else None
                }
                print(f'[LOGIN] Found {len(cases_list)} cases with {total_new_documents} new documents since {previous_login_at}', flush=True)
        except Exception as e:
            print(f'[LOGIN] Error checking new filings: {e}', flush=True)
            # Don't fail login if notification check fails
            pass

    return TokenResponse(**tokens, new_filings=new_filings_data)


@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.

    - **refresh_token**: Valid refresh token from login/register

    Returns new access token (refresh token remains valid).
    """
    try:
        new_tokens = refresh_access_token(request.refresh_token, db)
        return new_tokens
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout_user(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Logout current user.

    Note: In a stateless JWT system, actual logout happens client-side by
    removing tokens. Server-side logout would require token blacklisting.

    For now, this endpoint simply confirms logout and instructs client to
    clear tokens.
    """
    return {
        "message": "Successfully logged out",
        "user_id": current_user.user_id,
        "note": "Please remove tokens from client storage"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's profile.

    Returns full user profile information for the authenticated user.
    """
    # Get full user object from database
    user = db.query(User).filter(User.id == current_user.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role.value if user.role else "user",
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    full_name: Optional[str] = None,
    phone: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information.

    - **full_name**: Optional updated full name
    - **phone**: Optional updated phone number
    """
    # Get user from database
    user = db.query(User).filter(User.id == current_user.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields if provided
    if full_name is not None:
        user.full_name = full_name
    if phone is not None:
        user.phone = phone

    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role.value if user.role else "user",
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None
    )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.

    - **current_password**: User's current password
    - **new_password**: New password (must meet complexity requirements)

    Requires authentication. User must provide current password.
    """
    # Get user from database
    user = db.query(User).filter(User.id == current_user.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Check if new password is same as current
    if verify_password(password_data.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Update password
    user.hashed_password = hash_password(password_data.new_password)
    user.updated_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Password changed successfully",
        "note": "Please login again with your new password"
    }


@router.get("/verify-token")
async def verify_current_token(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Verify that the current token is valid.

    Useful for checking authentication status from frontend.
    """
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "roles": current_user.roles,
        "authenticated_at": current_user.authenticated_at.isoformat()
    }


# ============================================================================
# USER PREFERENCES ENDPOINTS
# ============================================================================

@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's preferences.

    Returns user notification and auto-download preferences.
    """
    user = db.query(User).filter(User.id == current_user.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get preferences from user or use defaults
    prefs = user.preferences or {}

    return UserPreferencesResponse(
        show_new_filing_notifications=prefs.get("show_new_filing_notifications", DEFAULT_PREFERENCES["show_new_filing_notifications"]),
        email_notifications=prefs.get("email_notifications", DEFAULT_PREFERENCES["email_notifications"]),
        case_alerts=prefs.get("case_alerts", DEFAULT_PREFERENCES["case_alerts"]),
        document_alerts=prefs.get("document_alerts", DEFAULT_PREFERENCES["document_alerts"]),
        auto_download_enabled=prefs.get("auto_download_enabled", DEFAULT_PREFERENCES["auto_download_enabled"]),
        auto_download_free_only=prefs.get("auto_download_free_only", DEFAULT_PREFERENCES["auto_download_free_only"])
    )


@router.put("/me/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences: UpdatePreferencesRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's preferences.

    Only provided fields will be updated; others remain unchanged.
    """
    user = db.query(User).filter(User.id == current_user.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get existing preferences or start with defaults
    current_prefs = user.preferences or dict(DEFAULT_PREFERENCES)

    # Update only provided fields
    if preferences.show_new_filing_notifications is not None:
        current_prefs["show_new_filing_notifications"] = preferences.show_new_filing_notifications
    if preferences.email_notifications is not None:
        current_prefs["email_notifications"] = preferences.email_notifications
    if preferences.case_alerts is not None:
        current_prefs["case_alerts"] = preferences.case_alerts
    if preferences.document_alerts is not None:
        current_prefs["document_alerts"] = preferences.document_alerts
    if preferences.auto_download_enabled is not None:
        current_prefs["auto_download_enabled"] = preferences.auto_download_enabled
    if preferences.auto_download_free_only is not None:
        current_prefs["auto_download_free_only"] = preferences.auto_download_free_only

    # Save to database
    user.preferences = current_prefs
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    return UserPreferencesResponse(**current_prefs)


# ============================================================================
# ADMIN ENDPOINTS (Future Implementation)
# ============================================================================

# TODO: Implement these endpoints when needed
# - POST /auth/forgot-password - Request password reset
# - POST /auth/reset-password - Reset password with token
# - POST /auth/verify-email - Verify email address
# - POST /auth/resend-verification - Resend verification email
# - GET /auth/users - Admin: List all users
# - PUT /auth/users/{user_id}/role - Admin: Update user role
# - DELETE /auth/users/{user_id} - Admin: Delete user
