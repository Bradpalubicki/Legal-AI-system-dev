"""
Legal AI System - Authentication Utilities
JWT token management, password hashing, and user authentication
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError
import bcrypt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..models.user import User

# Define JWTError for backward compatibility
JWTError = InvalidTokenError

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET", "development-jwt-secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# HTTP Bearer token scheme
security = HTTPBearer()


# ============================================================================
# PASSWORD HASHING
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt directly.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password using bcrypt directly.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiration.

    Args:
        data: Dictionary of claims to encode in the token

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token and return the payload.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary containing the token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token and return payload if valid, None otherwise.

    Args:
        token: JWT token string to verify

    Returns:
        Dictionary containing token payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check if token has expired (PyJWT handles this automatically, but double-check)
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            return None

        return payload
    except InvalidTokenError:
        return None


# ============================================================================
# USER AUTHENTICATION
# ============================================================================

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with email and password.

    Args:
        db: Database session
        email: User's email address
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        # Increment failed login attempts
        increment_failed_login(db, user)
        return None

    # Check if account is locked
    if user.is_account_locked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is locked until {user.account_locked_until}. Please try again later."
        )

    # Reset failed login attempts on successful login
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        db.commit()

    # Update login tracking - save previous login time for new-filings feature
    print(f'[AUTH DEBUG] User {user.id} login - BEFORE: last_login_at={user.last_login_at}, previous_login_at={user.previous_login_at}', flush=True)

    # Store the old last_login_at before updating
    old_last_login = user.last_login_at
    print(f'[AUTH DEBUG] Stored old_last_login: {old_last_login}', flush=True)

    # Update the user's login times
    user.previous_login_at = old_last_login
    user.last_login_at = datetime.now(timezone.utc)
    user.login_count = (user.login_count or 0) + 1

    print(f'[AUTH DEBUG] User {user.id} login - AFTER assignment: last_login_at={user.last_login_at}, previous_login_at={user.previous_login_at}', flush=True)

    # Commit the changes
    db.commit()

    # Verify the commit by re-querying
    db.refresh(user)
    print(f'[AUTH DEBUG] User {user.id} login - AFTER commit+refresh: last_login_at={user.last_login_at}, previous_login_at={user.previous_login_at}', flush=True)

    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = None
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)
        user_id: str = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user (must be active and not deleted).

    Args:
        current_user: Current authenticated user

    Returns:
        User object if active

    Raises:
        HTTPException: If user is inactive or deleted
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    if current_user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted"
        )

    if current_user.is_account_locked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is locked until {current_user.account_locked_until}"
        )

    return current_user


# ============================================================================
# ACCOUNT SECURITY
# ============================================================================

def increment_failed_login(db: Session, user: User) -> None:
    """
    Increment failed login attempts and lock account if threshold exceeded.

    Args:
        db: Database session
        user: User object
    """
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

    # Lock account after 5 failed attempts
    if user.failed_login_attempts >= 5:
        lock_account(db, user, duration_minutes=30)

    db.commit()


def lock_account(db: Session, user: User, duration_minutes: int = 30) -> None:
    """
    Lock a user account for a specified duration and send notification email.

    Args:
        db: Database session
        user: User object
        duration_minutes: Duration to lock account (default 30 minutes)
    """
    lockout_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
    user.account_locked_until = lockout_until
    db.commit()

    # Send email notification about account lockout
    try:
        from ..services.email_notification_service import email_notification_service

        email_notification_service.send_account_lockout_notification(
            to_email=user.email,
            user_name=user.display_name,
            lockout_duration_minutes=duration_minutes,
            lockout_until=lockout_until,
            failed_attempts=user.failed_login_attempts or 5
        )
    except Exception as e:
        # Don't fail the lockout if email fails - just log it
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to send lockout notification email: {e}")


def unlock_account(db: Session, user: User) -> None:
    """
    Unlock a user account and reset failed login attempts.

    Args:
        db: Database session
        user: User object
    """
    user.account_locked_until = None
    user.failed_login_attempts = 0
    db.commit()


# ============================================================================
# TOKEN UTILITIES
# ============================================================================

def create_tokens_for_user(user: User) -> Dict[str, Any]:
    """
    Create both access and refresh tokens for a user.

    Args:
        user: User object

    Returns:
        Dictionary containing access_token, refresh_token, and metadata
    """
    # Prepare token data
    token_data = {
        "user_id": user.id,  # Keep as integer for consistency with database
        "email": user.email,
        "role": user.role.value if user.role else "user",
    }

    # Create tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"user_id": user.id})  # Keep as integer

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
        "user": user.to_dict()
    }


def refresh_access_token(refresh_token: str, db: Session) -> Dict[str, Any]:
    """
    Create a new access token from a valid refresh token.

    Args:
        refresh_token: Valid refresh token
        db: Database session

    Returns:
        Dictionary with new access token

    Raises:
        HTTPException: If refresh token is invalid or user not found
    """
    payload = verify_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Create new access token
    token_data = {
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role.value if user.role else "user",
    }

    access_token = create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
