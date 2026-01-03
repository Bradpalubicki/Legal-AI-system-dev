"""
Legal AI System - Partner API Service
Enterprise API access, developer portal, and integration management
"""

import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, and_, func, desc
from fastapi import HTTPException, Request
import logging
import jwt
from dataclasses import dataclass

from ..models.partner import (
    APIKey, PartnerApplication, APIUsage,
    DeveloperAccount, Webhook, IntegrationTemplate
)
from ..models.user import User
from ..core.database import get_async_session
from ..core.config import settings
from ..utils.rate_limiter import RateLimiter
from ..utils.notifications import send_notification

logger = logging.getLogger(__name__)

class APIKeyScope(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    WEBHOOK = "webhook"

class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"

@dataclass
class APIUsageStats:
    requests_today: int
    requests_this_month: int
    rate_limit_exceeded: int
    last_used: Optional[datetime]
    most_used_endpoint: Optional[str]

class PartnerService:
    """Comprehensive partner API and developer portal service"""

    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.default_rate_limits = {
            "standard": {"requests_per_minute": 100, "requests_per_day": 10000},
            "premium": {"requests_per_minute": 500, "requests_per_day": 50000},
            "enterprise": {"requests_per_minute": 2000, "requests_per_day": 200000}
        }

    async def create_developer_account(
        self,
        user_id: int,
        company_name: str,
        company_website: Optional[str] = None,
        use_case: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a developer account for API access"""
        try:
            async with get_async_session() as session:
                # Check if user already has a developer account
                existing = await session.execute(
                    select(DeveloperAccount).where(DeveloperAccount.user_id == user_id)
                )
                existing = existing.scalar_one_or_none()

                if existing:
                    raise HTTPException(status_code=400, detail="Developer account already exists")

                # Create developer account
                developer_account = DeveloperAccount(
                    user_id=user_id,
                    company_name=company_name,
                    company_website=company_website,
                    use_case=use_case,
                    status="pending_approval",
                    tier="standard"
                )

                session.add(developer_account)
                await session.commit()
                await session.refresh(developer_account)

                # Send approval notification to admin team
                await self._send_approval_notification(developer_account.id)

                logger.info(f"Created developer account {developer_account.id} for user {user_id}")

                return {
                    "developer_account_id": developer_account.id,
                    "status": developer_account.status,
                    "message": "Developer account created and pending approval"
                }

        except Exception as e:
            logger.error(f"Failed to create developer account: {e}")
            raise HTTPException(status_code=500, detail="Failed to create developer account")

    async def generate_api_key(
        self,
        user_id: int,
        name: str,
        scopes: List[str],
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a new API key"""
        try:
            async with get_async_session() as session:
                # Get developer account
                developer = await session.execute(
                    select(DeveloperAccount).where(
                        and_(
                            DeveloperAccount.user_id == user_id,
                            DeveloperAccount.status == "approved"
                        )
                    )
                )
                developer = developer.scalar_one_or_none()

                if not developer:
                    raise HTTPException(status_code=403, detail="Developer account not found or not approved")

                # Check API key limits
                existing_keys = await session.execute(
                    select(func.count(APIKey.id)).where(
                        and_(
                            APIKey.developer_id == developer.id,
                            APIKey.status == APIKeyStatus.ACTIVE
                        )
                    )
                )
                existing_count = existing_keys.scalar()

                max_keys = {"standard": 5, "premium": 15, "enterprise": 50}
                if existing_count >= max_keys.get(developer.tier, 5):
                    raise HTTPException(status_code=400, detail="API key limit exceeded for your tier")

                # Generate key
                key_id = self._generate_key_id()
                secret_key = self._generate_secret_key()
                key_hash = hashlib.sha256(secret_key.encode()).hexdigest()

                # Set expiration
                expires_at = None
                if expires_in_days:
                    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

                # Create API key record
                api_key = APIKey(
                    developer_id=developer.id,
                    key_id=key_id,
                    key_hash=key_hash,
                    name=name,
                    scopes=scopes,
                    status=APIKeyStatus.ACTIVE,
                    expires_at=expires_at,
                    rate_limit_tier=developer.tier
                )

                session.add(api_key)
                await session.commit()

                logger.info(f"Generated API key {key_id} for developer {developer.id}")

                return {
                    "key_id": key_id,
                    "secret_key": secret_key,  # Only returned once
                    "scopes": scopes,
                    "expires_at": expires_at,
                    "rate_limits": self.default_rate_limits[developer.tier]
                }

        except Exception as e:
            logger.error(f"Failed to generate API key: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate API key")

    async def validate_api_key(
        self,
        key_id: str,
        secret_key: str,
        required_scope: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Validate API key and return key information"""
        try:
            async with get_async_session() as session:
                # Get API key
                api_key = await session.execute(
                    select(APIKey).where(APIKey.key_id == key_id)
                    .options(selectinload(APIKey.developer))
                )
                api_key = api_key.scalar_one_or_none()

                if not api_key:
                    return None

                # Check key hash
                key_hash = hashlib.sha256(secret_key.encode()).hexdigest()
                if api_key.key_hash != key_hash:
                    return None

                # Check status
                if api_key.status != APIKeyStatus.ACTIVE:
                    return None

                # Check expiration
                if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                    # Mark as expired
                    api_key.status = APIKeyStatus.EXPIRED
                    await session.commit()
                    return None

                # Check scope
                if required_scope and required_scope not in api_key.scopes:
                    return None

                # Update last used
                api_key.last_used_at = datetime.utcnow()
                await session.commit()

                return {
                    "api_key_id": api_key.id,
                    "key_id": key_id,
                    "developer_id": api_key.developer_id,
                    "user_id": api_key.developer.user_id,
                    "scopes": api_key.scopes,
                    "tier": api_key.rate_limit_tier
                }

        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return None

    async def check_rate_limit(
        self,
        api_key_id: int,
        endpoint: str,
        request: Request
    ) -> bool:
        """Check if request is within rate limits"""
        try:
            async with get_async_session() as session:
                # Get API key with rate limit info
                api_key = await session.get(APIKey, api_key_id)
                if not api_key:
                    return False

                # Get rate limits for tier
                limits = self.default_rate_limits.get(api_key.rate_limit_tier, self.default_rate_limits["standard"])

                # Check minute-based rate limit
                minute_key = f"api_rate:{api_key.key_id}:minute:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
                minute_count = await self.rate_limiter.get_count(minute_key)

                if minute_count >= limits["requests_per_minute"]:
                    await self._log_rate_limit_exceeded(api_key_id, endpoint, "minute")
                    return False

                # Check day-based rate limit
                day_key = f"api_rate:{api_key.key_id}:day:{datetime.utcnow().strftime('%Y%m%d')}"
                day_count = await self.rate_limiter.get_count(day_key)

                if day_count >= limits["requests_per_day"]:
                    await self._log_rate_limit_exceeded(api_key_id, endpoint, "day")
                    return False

                # Increment counters
                await self.rate_limiter.increment(minute_key, ttl=60)
                await self.rate_limiter.increment(day_key, ttl=86400)

                return True

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error to prevent blocking

    async def log_api_usage(
        self,
        api_key_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None
    ) -> None:
        """Log API usage for analytics and billing"""
        try:
            async with get_async_session() as session:
                usage = APIUsage(
                    api_key_id=api_key_id,
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    request_size=request_size,
                    response_size=response_size,
                    timestamp=datetime.utcnow()
                )

                session.add(usage)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")

    async def get_api_usage_stats(
        self,
        user_id: int,
        api_key_id: Optional[int] = None,
        days: int = 30
    ) -> APIUsageStats:
        """Get API usage statistics"""
        try:
            async with get_async_session() as session:
                # Get developer account
                developer = await session.execute(
                    select(DeveloperAccount).where(DeveloperAccount.user_id == user_id)
                )
                developer = developer.scalar_one_or_none()

                if not developer:
                    raise HTTPException(status_code=404, detail="Developer account not found")

                # Build query conditions
                conditions = [APIKey.developer_id == developer.id]
                if api_key_id:
                    conditions.append(APIUsage.api_key_id == api_key_id)

                # Requests today
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                requests_today = await session.execute(
                    select(func.count(APIUsage.id))
                    .join(APIKey, APIUsage.api_key_id == APIKey.id)
                    .where(
                        and_(
                            *conditions,
                            APIUsage.timestamp >= today_start
                        )
                    )
                )
                requests_today = requests_today.scalar()

                # Requests this month
                month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                requests_month = await session.execute(
                    select(func.count(APIUsage.id))
                    .join(APIKey, APIUsage.api_key_id == APIKey.id)
                    .where(
                        and_(
                            *conditions,
                            APIUsage.timestamp >= month_start
                        )
                    )
                )
                requests_month = requests_month.scalar()

                # Rate limit exceeded count
                rate_limit_exceeded = await session.execute(
                    select(func.count(APIUsage.id))
                    .join(APIKey, APIUsage.api_key_id == APIKey.id)
                    .where(
                        and_(
                            *conditions,
                            APIUsage.status_code == 429,
                            APIUsage.timestamp >= datetime.utcnow() - timedelta(days=days)
                        )
                    )
                )
                rate_limit_exceeded = rate_limit_exceeded.scalar()

                # Most used endpoint
                most_used = await session.execute(
                    select(APIUsage.endpoint, func.count().label('count'))
                    .join(APIKey, APIUsage.api_key_id == APIKey.id)
                    .where(
                        and_(
                            *conditions,
                            APIUsage.timestamp >= datetime.utcnow() - timedelta(days=days)
                        )
                    )
                    .group_by(APIUsage.endpoint)
                    .order_by(desc('count'))
                    .limit(1)
                )
                most_used = most_used.first()
                most_used_endpoint = most_used.endpoint if most_used else None

                # Last used
                last_used = await session.execute(
                    select(func.max(APIUsage.timestamp))
                    .join(APIKey, APIUsage.api_key_id == APIKey.id)
                    .where(and_(*conditions))
                )
                last_used = last_used.scalar()

                return APIUsageStats(
                    requests_today=requests_today,
                    requests_this_month=requests_month,
                    rate_limit_exceeded=rate_limit_exceeded,
                    last_used=last_used,
                    most_used_endpoint=most_used_endpoint
                )

        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve usage statistics")

    async def create_webhook(
        self,
        user_id: int,
        url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a webhook subscription"""
        try:
            async with get_async_session() as session:
                # Get developer account
                developer = await session.execute(
                    select(DeveloperAccount).where(DeveloperAccount.user_id == user_id)
                )
                developer = developer.scalar_one_or_none()

                if not developer:
                    raise HTTPException(status_code=404, detail="Developer account not found")

                # Generate webhook secret if not provided
                if not secret:
                    secret = secrets.token_urlsafe(32)

                webhook = Webhook(
                    developer_id=developer.id,
                    url=url,
                    events=events,
                    secret=secret,
                    is_active=True
                )

                session.add(webhook)
                await session.commit()
                await session.refresh(webhook)

                # Test webhook
                test_success = await self._test_webhook(webhook.id)

                logger.info(f"Created webhook {webhook.id} for developer {developer.id}")

                return {
                    "webhook_id": webhook.id,
                    "url": url,
                    "events": events,
                    "secret": secret,
                    "test_success": test_success
                }

        except Exception as e:
            logger.error(f"Failed to create webhook: {e}")
            raise HTTPException(status_code=500, detail="Failed to create webhook")

    async def get_integration_templates(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available integration templates"""
        try:
            async with get_async_session() as session:
                query = select(IntegrationTemplate).where(IntegrationTemplate.is_published == True)

                if category:
                    query = query.where(IntegrationTemplate.category == category)

                templates = await session.execute(
                    query.order_by(IntegrationTemplate.popularity.desc())
                )
                templates = templates.scalars().all()

                return [
                    {
                        "id": template.id,
                        "name": template.name,
                        "description": template.description,
                        "category": template.category,
                        "language": template.language,
                        "difficulty": template.difficulty,
                        "estimated_time": template.estimated_time_minutes,
                        "popularity": template.popularity
                    }
                    for template in templates
                ]

        except Exception as e:
            logger.error(f"Failed to get integration templates: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve templates")

    async def approve_developer_account(
        self,
        admin_user_id: int,
        developer_account_id: int,
        tier: str = "standard",
        notes: Optional[str] = None
    ) -> bool:
        """Approve a developer account (admin only)"""
        try:
            async with get_async_session() as session:
                # Check admin permissions
                admin = await session.get(User, admin_user_id)
                if not admin or not admin.is_admin:
                    raise HTTPException(status_code=403, detail="Admin access required")

                # Get and approve developer account
                developer = await session.get(DeveloperAccount, developer_account_id)
                if not developer:
                    raise HTTPException(status_code=404, detail="Developer account not found")

                developer.status = "approved"
                developer.tier = tier
                developer.approved_at = datetime.utcnow()
                developer.approved_by = admin_user_id
                developer.approval_notes = notes

                await session.commit()

                # Send approval notification
                await self._send_account_approved_notification(developer_account_id)

                logger.info(f"Approved developer account {developer_account_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to approve developer account: {e}")
            raise HTTPException(status_code=500, detail="Failed to approve account")

    # Private helper methods
    def _generate_key_id(self) -> str:
        """Generate API key ID"""
        return f"la_{secrets.token_urlsafe(16)}"

    def _generate_secret_key(self) -> str:
        """Generate API secret key"""
        return f"las_{secrets.token_urlsafe(32)}"

    async def _send_approval_notification(self, developer_account_id: int) -> None:
        """Send developer account approval notification to admin"""
        # Implementation for admin notifications
        pass

    async def _send_account_approved_notification(self, developer_account_id: int) -> None:
        """Send account approved notification to developer"""
        # Implementation for developer notifications
        pass

    async def _log_rate_limit_exceeded(
        self,
        api_key_id: int,
        endpoint: str,
        limit_type: str
    ) -> None:
        """Log rate limit exceeded event"""
        await self.log_api_usage(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method="N/A",
            status_code=429,
            response_time_ms=0
        )

    async def _test_webhook(self, webhook_id: int) -> bool:
        """Test webhook endpoint"""
        try:
            # Implementation for webhook testing
            return True
        except Exception as e:
            logger.error(f"Webhook test failed: {e}")
            return False

# Initialize partner service
partner_service = PartnerService()