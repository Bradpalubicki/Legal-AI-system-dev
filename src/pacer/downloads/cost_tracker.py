# -*- coding: utf-8 -*-
"""
PACER Cost Tracker

Tracks and manages PACER usage costs including:
- Real-time cost tracking
- Daily/monthly spending limits
- Cost alerts and notifications
- Detailed usage reports
- Cost estimation before operations
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class PACEROperation(Enum):
    """Types of PACER operations with associated costs"""
    CASE_SEARCH = "case_search"  # $0.00 (free)
    PARTY_SEARCH = "party_search"  # $0.00 (free)
    DOCKET_VIEW = "docket_view"  # $0.10 per page
    DOCUMENT_DOWNLOAD = "document_download"  # $0.10 per page
    CASE_SUMMARY = "case_summary"  # $0.00 (free)


@dataclass
class CostRecord:
    """Record of a PACER operation cost"""
    operation: PACEROperation
    cost: float
    timestamp: datetime
    user_id: str
    case_id: Optional[str] = None
    document_id: Optional[str] = None
    court: Optional[str] = None
    pages: int = 1
    description: str = ""


@dataclass
class CostAlert:
    """Cost threshold alert configuration"""
    threshold: float
    alert_type: str  # 'daily', 'monthly', 'total'
    enabled: bool = True
    last_triggered: Optional[datetime] = None


class CostTracker:
    """
    Tracks and manages PACER costs.

    Features:
    - Real-time cost tracking per user/organization
    - Daily and monthly spending limits
    - Cost alerts at configurable thresholds
    - Detailed usage reports
    - Cost estimation for operations
    """

    # Standard PACER pricing (as of 2024)
    COST_PER_PAGE = 0.10
    MAX_COST_PER_DOCUMENT = 3.00  # PACER caps at $3.00 per document
    FREE_PAGE_LIMIT_QUARTERLY = 30.00  # $30 free per quarter

    def __init__(
        self,
        daily_limit: float = 100.00,
        monthly_limit: float = 1000.00,
        alert_threshold: float = 0.75  # Alert at 75% of limit
    ):
        """
        Initialize cost tracker.

        Args:
            daily_limit: Maximum daily spending in dollars
            monthly_limit: Maximum monthly spending in dollars
            alert_threshold: Percentage of limit to trigger alert (0.0-1.0)
        """
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self.alert_threshold = alert_threshold

        # Cost records
        self.records: List[CostRecord] = []

        # Alerts
        self.alerts: Dict[str, CostAlert] = {
            "daily_75": CostAlert(
                threshold=daily_limit * alert_threshold,
                alert_type="daily"
            ),
            "daily_90": CostAlert(
                threshold=daily_limit * 0.90,
                alert_type="daily"
            ),
            "monthly_75": CostAlert(
                threshold=monthly_limit * alert_threshold,
                alert_type="monthly"
            )
        }

        # Statistics
        self.total_pages_accessed = 0
        self.total_documents_downloaded = 0

    def estimate_cost(
        self,
        operation: PACEROperation,
        pages: int = 1
    ) -> float:
        """
        Estimate cost for an operation.

        Args:
            operation: Type of PACER operation
            pages: Number of pages (for documents/dockets)

        Returns:
            Estimated cost in dollars
        """
        if operation in [PACEROperation.CASE_SEARCH, PACEROperation.PARTY_SEARCH,
                        PACEROperation.CASE_SUMMARY]:
            return 0.00

        # Calculate page cost
        cost = pages * self.COST_PER_PAGE

        # Apply per-document cap
        if operation == PACEROperation.DOCUMENT_DOWNLOAD:
            cost = min(cost, self.MAX_COST_PER_DOCUMENT)

        return round(cost, 2)

    async def can_afford_operation(
        self,
        operation: PACEROperation,
        pages: int = 1,
        user_id: Optional[str] = None
    ) -> tuple[bool, float, str]:
        """
        Check if operation is within budget limits.

        Args:
            operation: Type of operation
            pages: Number of pages
            user_id: User identifier

        Returns:
            Tuple of (can_afford: bool, estimated_cost: float, reason: str)
        """
        estimated_cost = self.estimate_cost(operation, pages)

        # Free operations always allowed
        if estimated_cost == 0:
            return True, 0.00, "Free operation"

        # Check daily limit
        daily_spent = self.get_daily_spending(user_id)
        if (daily_spent + estimated_cost) > self.daily_limit:
            return False, estimated_cost, f"Daily limit exceeded (${daily_spent:.2f}/${self.daily_limit:.2f})"

        # Check monthly limit
        monthly_spent = self.get_monthly_spending(user_id)
        if (monthly_spent + estimated_cost) > self.monthly_limit:
            return False, estimated_cost, f"Monthly limit exceeded (${monthly_spent:.2f}/${self.monthly_limit:.2f})"

        return True, estimated_cost, "Within budget"

    async def record_cost(
        self,
        operation: PACEROperation,
        user_id: str,
        pages: int = 1,
        case_id: Optional[str] = None,
        document_id: Optional[str] = None,
        court: Optional[str] = None,
        description: str = ""
    ) -> CostRecord:
        """
        Record a PACER operation cost.

        Args:
            operation: Type of operation
            user_id: User identifier
            pages: Number of pages accessed
            case_id: Associated case ID
            document_id: Associated document ID
            court: Court identifier
            description: Operation description

        Returns:
            CostRecord for the operation
        """
        cost = self.estimate_cost(operation, pages)

        record = CostRecord(
            operation=operation,
            cost=cost,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            case_id=case_id,
            document_id=document_id,
            court=court,
            pages=pages,
            description=description
        )

        self.records.append(record)

        # Update statistics
        self.total_pages_accessed += pages
        if operation == PACEROperation.DOCUMENT_DOWNLOAD:
            self.total_documents_downloaded += 1

        # Check alerts
        await self._check_alerts(user_id)

        logger.info(f"Recorded cost: ${cost:.2f} for {operation.value} ({pages} pages)")

        return record

    async def _check_alerts(self, user_id: Optional[str] = None):
        """Check if any cost alerts should be triggered"""
        daily_spent = self.get_daily_spending(user_id)
        monthly_spent = self.get_monthly_spending(user_id)

        for alert_name, alert in self.alerts.items():
            if not alert.enabled:
                continue

            should_trigger = False

            if alert.alert_type == "daily":
                should_trigger = daily_spent >= alert.threshold
                amount = daily_spent
                limit = self.daily_limit

            elif alert.alert_type == "monthly":
                should_trigger = monthly_spent >= alert.threshold
                amount = monthly_spent
                limit = self.monthly_limit

            if should_trigger:
                # Check if already triggered recently (within last hour)
                if alert.last_triggered:
                    time_since = datetime.utcnow() - alert.last_triggered
                    if time_since < timedelta(hours=1):
                        continue  # Don't spam alerts

                alert.last_triggered = datetime.utcnow()
                await self._trigger_alert(alert_name, amount, limit, alert.alert_type)

    async def _trigger_alert(
        self,
        alert_name: str,
        amount: float,
        limit: float,
        alert_type: str
    ):
        """Trigger a cost alert"""
        percentage = (amount / limit * 100) if limit > 0 else 0

        logger.warning(
            f"COST ALERT [{alert_name}]: {alert_type.capitalize()} spending at "
            f"${amount:.2f} ({percentage:.1f}% of ${limit:.2f} limit)"
        )

        # In production, this would send notifications
        # (email, Slack, SMS, etc.)
        print(f"⚠️  COST ALERT: {alert_type.capitalize()} PACER spending at ${amount:.2f} "
              f"({percentage:.1f}% of limit)")

    def get_daily_spending(
        self,
        user_id: Optional[str] = None,
        target_date: Optional[date] = None
    ) -> float:
        """
        Get total spending for a specific day.

        Args:
            user_id: Filter by user (None for all users)
            target_date: Date to check (None for today)

        Returns:
            Total spending in dollars
        """
        if target_date is None:
            target_date = date.today()

        total = sum(
            record.cost for record in self.records
            if record.timestamp.date() == target_date
            and (user_id is None or record.user_id == user_id)
        )

        return round(total, 2)

    def get_monthly_spending(
        self,
        user_id: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> float:
        """
        Get total spending for a specific month.

        Args:
            user_id: Filter by user (None for all users)
            year: Year (None for current year)
            month: Month (None for current month)

        Returns:
            Total spending in dollars
        """
        now = datetime.now()
        target_year = year or now.year
        target_month = month or now.month

        total = sum(
            record.cost for record in self.records
            if record.timestamp.year == target_year
            and record.timestamp.month == target_month
            and (user_id is None or record.user_id == user_id)
        )

        return round(total, 2)

    def get_usage_report(
        self,
        user_id: Optional[str] = None,
        days: int = 30
    ) -> Dict:
        """
        Generate comprehensive usage report.

        Args:
            user_id: Filter by user
            days: Number of days to include

        Returns:
            Usage report dictionary
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Filter records
        records = [
            r for r in self.records
            if r.timestamp >= cutoff_date
            and (user_id is None or r.user_id == user_id)
        ]

        # Calculate totals
        total_cost = sum(r.cost for r in records)
        total_pages = sum(r.pages for r in records)

        # Breakdown by operation
        by_operation = {}
        for op_type in PACEROperation:
            op_records = [r for r in records if r.operation == op_type]
            by_operation[op_type.value] = {
                "count": len(op_records),
                "total_cost": sum(r.cost for r in op_records),
                "total_pages": sum(r.pages for r in op_records)
            }

        # Breakdown by court
        by_court = {}
        for record in records:
            if record.court:
                if record.court not in by_court:
                    by_court[record.court] = {"count": 0, "cost": 0.0}
                by_court[record.court]["count"] += 1
                by_court[record.court]["cost"] += record.cost

        return {
            "period_days": days,
            "user_id": user_id or "all",
            "total_cost": round(total_cost, 2),
            "total_pages": total_pages,
            "total_operations": len(records),
            "average_cost_per_operation": round(total_cost / len(records), 2) if records else 0,
            "by_operation": by_operation,
            "by_court": by_court,
            "daily_spending": self.get_daily_spending(user_id),
            "monthly_spending": self.get_monthly_spending(user_id),
            "daily_limit": self.daily_limit,
            "monthly_limit": self.monthly_limit,
            "daily_remaining": round(self.daily_limit - self.get_daily_spending(user_id), 2),
            "monthly_remaining": round(self.monthly_limit - self.get_monthly_spending(user_id), 2)
        }


# Example usage
async def main():
    """Test cost tracker"""
    tracker = CostTracker(daily_limit=50.00, monthly_limit=500.00)

    # Estimate costs
    print("💰 Cost Estimates:")
    print(f"   Case search: ${tracker.estimate_cost(PACEROperation.CASE_SEARCH):.2f}")
    print(f"   Document (10 pages): ${tracker.estimate_cost(PACEROperation.DOCUMENT_DOWNLOAD, 10):.2f}")
    print(f"   Document (50 pages): ${tracker.estimate_cost(PACEROperation.DOCUMENT_DOWNLOAD, 50):.2f}")

    # Check if can afford
    can_afford, cost, reason = await tracker.can_afford_operation(
        PACEROperation.DOCUMENT_DOWNLOAD,
        pages=10,
        user_id="user123"
    )
    print(f"\n✅ Can afford 10-page document? {can_afford} (${cost:.2f}) - {reason}")

    # Record some costs
    await tracker.record_cost(
        operation=PACEROperation.DOCUMENT_DOWNLOAD,
        user_id="user123",
        pages=5,
        case_id="1:24-cv-12345",
        court="nysd",
        description="Complaint document"
    )

    # Get usage report
    report = tracker.get_usage_report(user_id="user123")
    print(f"\n📊 Usage Report:")
    print(f"   Total cost: ${report['total_cost']:.2f}")
    print(f"   Total pages: {report['total_pages']}")
    print(f"   Daily spending: ${report['daily_spending']:.2f} / ${report['daily_limit']:.2f}")
    print(f"   Daily remaining: ${report['daily_remaining']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
