"""
Case Access Service
Handles case access validation and checking
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.models.user import User
from app.models.case_access import CaseAccess, CaseAccessStatus
from app.models.billing import Subscription
from shared.database.models import TrackedDocket


class CaseAccessService:
    """Service for checking and managing case access"""

    def __init__(self, db: Session):
        self.db = db

    def check_user_access(self, user: User, case_id: int) -> dict:
        """
        Check if user has access to a specific case

        Returns:
            dict with has_access, access_type, reason, etc.
        """
        # Check if user is admin (full access)
        if user.is_admin:
            return {
                "has_access": True,
                "access_type": "admin",
                "reason": "Administrator access"
            }

        # Check direct case access purchase
        case_access = self.db.query(CaseAccess).filter(
            CaseAccess.user_id == user.id,
            CaseAccess.case_id == case_id,
            CaseAccess.status == CaseAccessStatus.ACTIVE
        ).first()

        if case_access and case_access.is_active():
            return {
                "has_access": True,
                "access_type": case_access.access_type.value,
                "case_access_id": case_access.id,
                "expires_at": case_access.expires_at,
                "days_remaining": case_access.days_remaining(),
                "reason": "Direct case purchase"
            }

        # Check subscription-based access (Pro/Firm tiers)
        subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status.in_(["active", "trialing"])
        ).first()

        if subscription and subscription.plan:
            plan_name = subscription.plan.name.lower()

            # Pro and Firm tiers include unlimited case monitoring
            if any(tier in plan_name for tier in ["pro", "firm", "enterprise", "professional"]):
                return {
                    "has_access": True,
                    "access_type": "subscription",
                    "subscription_tier": plan_name,
                    "reason": f"Included in {subscription.plan.name} subscription"
                }

        # Check if case is owned by user (for case creators)
        case = self.db.query(TrackedDocket).filter(TrackedDocket.id == case_id).first()
        if case and case.assigned_attorney_id == user.id:
            return {
                "has_access": True,
                "access_type": "owner",
                "reason": "Case owner"
            }

        # No access
        return {
            "has_access": False,
            "reason": "No active access to this case",
            "purchase_options": self._get_purchase_options()
        }

    def _get_purchase_options(self) -> list:
        """Get available purchase options for case access"""
        return [
            {
                "type": "one_time",
                "price": 5.00,
                "description": "Monitor this case until it closes"
            },
            {
                "type": "monthly",
                "price": 19.00,
                "description": "Monitor unlimited cases for 30 days"
            },
            {
                "type": "subscription_pro",
                "price": 49.00,
                "description": "Pro plan with unlimited case monitoring + AI features"
            }
        ]

    def get_user_cases(self, user: User) -> list:
        """Get all cases user has access to"""
        # Get directly purchased cases
        purchased_cases = self.db.query(CaseAccess).filter(
            CaseAccess.user_id == user.id,
            CaseAccess.status == CaseAccessStatus.ACTIVE
        ).all()

        cases = []
        for access in purchased_cases:
            if access.is_active() and access.case:
                cases.append({
                    "case": access.case,
                    "access": access,
                    "access_type": access.access_type.value
                })

        # If user has Pro/Firm subscription, they can access all cases
        subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status.in_(["active", "trialing"])
        ).first()

        if subscription and subscription.plan:
            plan_name = subscription.plan.name.lower()
            if any(tier in plan_name for tier in ["pro", "firm", "enterprise"]):
                # User has unlimited access - could list all cases or user's tracked cases
                pass

        return cases

    def grant_access(
        self,
        user_id: int,
        case_id: int,
        access_type: str = "subscription",
        subscription_id: Optional[int] = None,
        duration_days: Optional[int] = None
    ) -> CaseAccess:
        """
        Grant case access to a user

        Args:
            user_id: User to grant access to
            case_id: Case to grant access to
            access_type: Type of access (subscription, one_time, monthly)
            subscription_id: Related subscription ID (if applicable)
            duration_days: How many days access lasts (None = unlimited)

        Returns:
            CaseAccess record
        """
        from app.models.case_access import CaseAccessType
        from datetime import timedelta

        # Check if access already exists
        existing = self.db.query(CaseAccess).filter(
            CaseAccess.user_id == user_id,
            CaseAccess.case_id == case_id,
            CaseAccess.status == CaseAccessStatus.ACTIVE
        ).first()

        if existing and existing.is_active():
            # Extend access if applicable
            if duration_days:
                existing.extend_access(duration_days)
                self.db.commit()
            return existing

        # Create new access
        expires_at = None
        if duration_days:
            expires_at = datetime.utcnow() + timedelta(days=duration_days)

        access = CaseAccess(
            user_id=user_id,
            case_id=case_id,
            access_type=CaseAccessType(access_type),
            status=CaseAccessStatus.ACTIVE,
            subscription_id=subscription_id,
            granted_at=datetime.utcnow(),
            expires_at=expires_at,
            notifications_enabled=True
        )

        self.db.add(access)
        self.db.commit()
        self.db.refresh(access)

        return access

    def revoke_access(self, case_access_id: int, reason: str = None):
        """Revoke case access"""
        access = self.db.query(CaseAccess).filter(CaseAccess.id == case_access_id).first()

        if access:
            access.cancel(reason)
            self.db.commit()

    def check_and_expire_access(self):
        """
        Check all case accesses and expire any that have passed their expiration date
        Should be run periodically (e.g., daily cron job)
        """
        expired_accesses = self.db.query(CaseAccess).filter(
            CaseAccess.status == CaseAccessStatus.ACTIVE,
            CaseAccess.expires_at.isnot(None),
            CaseAccess.expires_at < datetime.utcnow()
        ).all()

        for access in expired_accesses:
            access.status = CaseAccessStatus.EXPIRED
            self.db.commit()

        return len(expired_accesses)
