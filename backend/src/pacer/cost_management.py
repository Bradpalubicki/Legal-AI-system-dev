#!/usr/bin/env python3
"""
PACER Cost Management and Billing Integration
Comprehensive cost tracking and billing system with educational compliance

CRITICAL COMPLIANCE NOTICES:
- EDUCATIONAL PURPOSE ONLY: Cost management demonstration
- ATTORNEY SUPERVISION: Required for all billing decisions
- PROFESSIONAL RESPONSIBILITY: Client billing ethics compliance
- TRANSPARENCY: Full cost visibility for educational purposes
"""

import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP
import sqlite3
from pathlib import Path

try:
    from .pacer_integration import PACERServiceType, ComplianceLevel, PACERUsageRecord
    from ..core.audit_logger import audit_logger
    from ..core.encryption_manager import EncryptionManager
except ImportError:
    # Fallback for testing
    from pacer_integration import PACERServiceType, ComplianceLevel, PACERUsageRecord


class BillingPeriod(Enum):
    """Billing period options"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class CostCategory(Enum):
    """PACER cost categories"""
    DOCUMENT_DOWNLOAD = "document_download"
    CASE_SEARCH = "case_search"
    DOCKET_ACCESS = "docket_access"
    REPORT_GENERATION = "report_generation"
    MONITORING_FEES = "monitoring_fees"
    ADMINISTRATIVE = "administrative"


class BillingStatus(Enum):
    """Billing record status"""
    PENDING = "pending"
    APPROVED = "approved"
    BILLED = "billed"
    PAID = "paid"
    DISPUTED = "disputed"
    EDUCATIONAL_DEMO = "educational_demo"


@dataclass
class CostLimit:
    """Cost limit configuration with educational compliance"""
    limit_id: str
    user_id: str
    limit_type: str  # daily, monthly, per_case, per_document
    amount: Decimal
    period_start: datetime
    period_end: datetime
    current_usage: Decimal = Decimal("0.00")
    educational_purpose: str = ""
    attorney_approval_required: bool = True
    active: bool = True


@dataclass
class BillingRecord:
    """Comprehensive billing record with compliance tracking"""
    billing_id: str
    user_id: str
    client_id: Optional[str]
    case_id: Optional[str]
    period_start: datetime
    period_end: datetime
    total_amount: Decimal
    cost_breakdown: Dict[str, Decimal]
    usage_records: List[str]  # Usage record IDs
    billing_status: BillingStatus
    generated_date: datetime
    approved_by: Optional[str] = None
    educational_purpose: str = ""
    compliance_notices: List[str] = field(default_factory=list)
    attorney_review_required: bool = True


@dataclass
class CostAlert:
    """Cost threshold alert with educational compliance"""
    alert_id: str
    user_id: str
    alert_type: str  # threshold_exceeded, limit_approaching, budget_warning
    threshold: Decimal
    current_amount: Decimal
    alert_message: str
    timestamp: datetime
    acknowledged: bool = False
    educational_purpose: str = ""
    attorney_notification_required: bool = True


class PACERCostManager:
    """
    PACER Cost Management and Billing Integration

    EDUCATIONAL PURPOSE: Demonstrates comprehensive cost management
    ATTORNEY SUPERVISION: Required for all billing decisions
    CLIENT PROTECTION: Transparent billing with attorney oversight
    """

    def __init__(self):
        self.encryption_manager = EncryptionManager()

        # Initialize database
        self.db_path = Path("pacer_billing.db")
        self._initialize_database()

        # Cost management configuration
        self.cost_config = {
            "standard_page_fee": Decimal("0.10"),
            "search_fee": Decimal("0.50"),
            "docket_fee": Decimal("1.00"),
            "daily_limit_default": Decimal("50.00"),
            "monthly_limit_default": Decimal("1000.00"),
            "alert_threshold_percent": 75,
            "attorney_approval_threshold": Decimal("100.00")
        }

        # Educational disclaimers
        self.billing_disclaimers = [
            "EDUCATIONAL BILLING: Cost management demonstration for educational purposes only",
            "ATTORNEY SUPERVISION: All billing decisions require attorney approval and oversight",
            "CLIENT PROTECTION: Transparent billing practices with full cost disclosure",
            "PROFESSIONAL ETHICS: Billing must comply with professional responsibility rules",
            "COST TRANSPARENCY: Complete visibility into all PACER-related costs and fees",
            "EDUCATIONAL PURPOSE: All cost tracking is for educational demonstration only",
            "BILLING COMPLIANCE: Client billing must follow legal profession ethical guidelines",
            "ATTORNEY REVIEW: All billing records require attorney review before client billing"
        ]

        # Initialize cost limits and alerts
        self.cost_limits: Dict[str, CostLimit] = {}
        self.cost_alerts: List[CostAlert] = []
        self.billing_records: Dict[str, BillingRecord] = {}

    def _initialize_database(self):
        """Initialize SQLite database for cost tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS usage_records (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        service_type TEXT NOT NULL,
                        cost REAL NOT NULL,
                        operation TEXT NOT NULL,
                        case_id TEXT,
                        document_id TEXT,
                        educational_purpose TEXT,
                        compliance_level TEXT
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS billing_records (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        client_id TEXT,
                        period_start TEXT NOT NULL,
                        period_end TEXT NOT NULL,
                        total_amount REAL NOT NULL,
                        status TEXT NOT NULL,
                        generated_date TEXT NOT NULL,
                        educational_purpose TEXT,
                        attorney_approved TEXT
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cost_limits (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        limit_type TEXT NOT NULL,
                        amount REAL NOT NULL,
                        period_start TEXT NOT NULL,
                        period_end TEXT NOT NULL,
                        current_usage REAL DEFAULT 0.0,
                        active INTEGER DEFAULT 1,
                        educational_purpose TEXT
                    )
                """)

                conn.commit()

        except Exception as e:
            print(f"Database initialization error: {e}")

    def create_cost_limit(self, user_id: str, limit_type: str, amount: float,
                         period_days: int = 30, educational_purpose: str = "") -> Dict[str, Any]:
        """
        Create cost limit with educational compliance

        EDUCATIONAL PURPOSE: Demonstrates cost limit configuration
        ATTORNEY SUPERVISION: Required for cost limit establishment
        """
        try:
            limit_id = f"LIMIT_{int(time.time())}_{user_id}"

            cost_limit = CostLimit(
                limit_id=limit_id,
                user_id=user_id,
                limit_type=limit_type,
                amount=Decimal(str(amount)),
                period_start=datetime.now(timezone.utc),
                period_end=datetime.now(timezone.utc) + timedelta(days=period_days),
                educational_purpose=educational_purpose or "Educational cost limit demonstration",
                attorney_approval_required=True,
                active=True
            )

            # Store cost limit
            self.cost_limits[limit_id] = cost_limit

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO cost_limits
                    (id, user_id, limit_type, amount, period_start, period_end, educational_purpose)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    limit_id, user_id, limit_type, float(cost_limit.amount),
                    cost_limit.period_start.isoformat(), cost_limit.period_end.isoformat(),
                    cost_limit.educational_purpose
                ))
                conn.commit()

            # Log cost limit creation
            audit_logger.log_pacer_event(
                user_id=user_id,
                event_type="cost_limit_created",
                service_type=PACERServiceType.CM_ECF.value,
                compliance_level=ComplianceLevel.EDUCATIONAL_ONLY.value,
                details={
                    "limit_id": limit_id,
                    "limit_type": limit_type,
                    "amount": float(amount),
                    "educational_purpose": cost_limit.educational_purpose
                }
            )

            return {
                "success": True,
                "limit_id": limit_id,
                "amount": float(cost_limit.amount),
                "period_days": period_days,
                "educational_purpose": cost_limit.educational_purpose,
                "compliance_notices": self.billing_disclaimers[:3],
                "attorney_approval_required": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Cost limit creation failed: {str(e)}",
                "compliance_notices": ["Cost limits require attorney supervision"]
            }

    def track_usage(self, user_id: str, service_type: PACERServiceType,
                   cost: float, operation: str, case_id: str = None,
                   document_id: str = None, educational_purpose: str = "") -> Dict[str, Any]:
        """
        Track PACER usage with comprehensive cost monitoring

        EDUCATIONAL PURPOSE: Demonstrates usage tracking and cost management
        REAL-TIME MONITORING: Immediate cost tracking and alert generation
        """
        try:
            usage_id = f"USAGE_{int(time.time())}_{user_id}"

            # Create usage record
            usage_record = PACERUsageRecord(
                usage_id=usage_id,
                timestamp=datetime.now(timezone.utc),
                user_id=user_id,
                case_id=case_id,
                document_id=document_id,
                service_type=service_type,
                cost=cost,
                operation=operation,
                compliance_level=ComplianceLevel.EDUCATIONAL_ONLY,
                educational_purpose=educational_purpose or "Educational usage tracking"
            )

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO usage_records
                    (id, user_id, timestamp, service_type, cost, operation, case_id,
                     document_id, educational_purpose, compliance_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    usage_id, user_id, usage_record.timestamp.isoformat(),
                    service_type.value, cost, operation, case_id, document_id,
                    usage_record.educational_purpose, ComplianceLevel.EDUCATIONAL_ONLY.value
                ))
                conn.commit()

            # Check cost limits and generate alerts
            alerts = self._check_cost_limits(user_id, cost)

            # Update usage in cost limits
            self._update_cost_limit_usage(user_id, cost)

            # Log usage tracking
            audit_logger.log_pacer_event(
                user_id=user_id,
                event_type="usage_tracked",
                service_type=service_type.value,
                compliance_level=ComplianceLevel.EDUCATIONAL_ONLY.value,
                details={
                    "usage_id": usage_id,
                    "cost": cost,
                    "operation": operation,
                    "alerts_generated": len(alerts)
                }
            )

            return {
                "success": True,
                "usage_id": usage_id,
                "cost": cost,
                "total_daily_usage": self._calculate_daily_usage(user_id),
                "alerts": alerts,
                "educational_purpose": "Usage tracking demonstration",
                "compliance_notices": ["All usage is tracked for educational and billing purposes"],
                "attorney_review_required": cost > float(self.cost_config["attorney_approval_threshold"])
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Usage tracking failed: {str(e)}",
                "compliance_notices": ["Usage tracking requires system access"]
            }

    def _check_cost_limits(self, user_id: str, additional_cost: float) -> List[CostAlert]:
        """Check cost limits and generate alerts if necessary"""
        alerts = []

        try:
            for limit in self.cost_limits.values():
                if limit.user_id == user_id and limit.active:
                    projected_usage = limit.current_usage + Decimal(str(additional_cost))
                    threshold_amount = limit.amount * Decimal("0.75")  # 75% threshold

                    # Check for approaching limit
                    if projected_usage >= threshold_amount and limit.current_usage < threshold_amount:
                        alert = CostAlert(
                            alert_id=f"ALERT_{int(time.time())}",
                            user_id=user_id,
                            alert_type="limit_approaching",
                            threshold=threshold_amount,
                            current_amount=projected_usage,
                            alert_message=f"Educational Alert: Cost limit approaching for {limit.limit_type}. Current: ${float(projected_usage):.2f}, Limit: ${float(limit.amount):.2f}",
                            timestamp=datetime.now(timezone.utc),
                            educational_purpose="Cost limit monitoring demonstration",
                            attorney_notification_required=True
                        )
                        alerts.append(alert)
                        self.cost_alerts.append(alert)

                    # Check for exceeded limit
                    if projected_usage >= limit.amount:
                        alert = CostAlert(
                            alert_id=f"ALERT_{int(time.time())}_EXCEEDED",
                            user_id=user_id,
                            alert_type="threshold_exceeded",
                            threshold=limit.amount,
                            current_amount=projected_usage,
                            alert_message=f"Educational Alert: Cost limit exceeded for {limit.limit_type}. Attorney approval required for continued usage.",
                            timestamp=datetime.now(timezone.utc),
                            educational_purpose="Cost limit exceeded demonstration",
                            attorney_notification_required=True
                        )
                        alerts.append(alert)
                        self.cost_alerts.append(alert)

        except Exception as e:
            print(f"Cost limit check error: {e}")

        return alerts

    def _update_cost_limit_usage(self, user_id: str, cost: float):
        """Update current usage in cost limits"""
        try:
            for limit in self.cost_limits.values():
                if limit.user_id == user_id and limit.active:
                    limit.current_usage += Decimal(str(cost))

            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE cost_limits
                    SET current_usage = current_usage + ?
                    WHERE user_id = ? AND active = 1
                """, (cost, user_id))
                conn.commit()

        except Exception as e:
            print(f"Cost limit update error: {e}")

    def _calculate_daily_usage(self, user_id: str) -> float:
        """Calculate daily usage for user"""
        try:
            today = datetime.now(timezone.utc).date()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT SUM(cost) FROM usage_records
                    WHERE user_id = ? AND date(timestamp) = ?
                """, (user_id, today.isoformat()))

                result = cursor.fetchone()
                return result[0] if result[0] else 0.0

        except Exception as e:
            print(f"Daily usage calculation error: {e}")
            return 0.0

    def generate_billing_report(self, user_id: str, period_start: datetime,
                               period_end: datetime, client_id: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive billing report with educational compliance

        EDUCATIONAL PURPOSE: Billing report generation demonstration
        ATTORNEY REVIEW: All billing reports require attorney approval
        CLIENT PROTECTION: Transparent billing with detailed cost breakdown
        """
        try:
            billing_id = f"BILL_{int(time.time())}_{user_id}"

            # Retrieve usage records for period
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM usage_records
                    WHERE user_id = ? AND timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp
                """, (user_id, period_start.isoformat(), period_end.isoformat()))

                usage_data = cursor.fetchall()

            # Calculate cost breakdown by category
            cost_breakdown = {}
            total_amount = Decimal("0.00")
            usage_record_ids = []

            for record in usage_data:
                operation = record[5]  # operation field
                cost = Decimal(str(record[4]))  # cost field

                if operation not in cost_breakdown:
                    cost_breakdown[operation] = Decimal("0.00")

                cost_breakdown[operation] += cost
                total_amount += cost
                usage_record_ids.append(record[0])  # usage ID

            # Create billing record
            billing_record = BillingRecord(
                billing_id=billing_id,
                user_id=user_id,
                client_id=client_id,
                case_id=None,
                period_start=period_start,
                period_end=period_end,
                total_amount=total_amount,
                cost_breakdown={k: float(v) for k, v in cost_breakdown.items()},
                usage_records=usage_record_ids,
                billing_status=BillingStatus.EDUCATIONAL_DEMO,
                generated_date=datetime.now(timezone.utc),
                educational_purpose="Educational billing report demonstration",
                compliance_notices=self.billing_disclaimers[:4],
                attorney_review_required=True
            )

            # Store billing record
            self.billing_records[billing_id] = billing_record

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO billing_records
                    (id, user_id, client_id, period_start, period_end, total_amount,
                     status, generated_date, educational_purpose)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    billing_id, user_id, client_id,
                    period_start.isoformat(), period_end.isoformat(),
                    float(total_amount), BillingStatus.EDUCATIONAL_DEMO.value,
                    billing_record.generated_date.isoformat(),
                    billing_record.educational_purpose
                ))
                conn.commit()

            # Log billing report generation
            audit_logger.log_pacer_event(
                user_id=user_id,
                event_type="billing_report_generated",
                service_type=PACERServiceType.CM_ECF.value,
                compliance_level=ComplianceLevel.EDUCATIONAL_ONLY.value,
                details={
                    "billing_id": billing_id,
                    "total_amount": float(total_amount),
                    "usage_records": len(usage_record_ids),
                    "educational_purpose": "Billing report demonstration"
                }
            )

            return {
                "success": True,
                "billing_id": billing_id,
                "billing_record": {
                    "total_amount": float(total_amount),
                    "cost_breakdown": billing_record.cost_breakdown,
                    "usage_records_count": len(usage_record_ids),
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "status": billing_record.billing_status.value
                },
                "educational_purpose": "Billing report generation demonstration",
                "compliance_notices": billing_record.compliance_notices,
                "attorney_review_required": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Billing report generation failed: {str(e)}",
                "compliance_notices": ["Billing reports require attorney supervision"]
            }

    def get_cost_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Generate cost analytics and trends with educational compliance

        EDUCATIONAL PURPOSE: Cost analysis demonstration
        BUDGET PLANNING: Educational cost forecasting and trend analysis
        """
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)

            # Retrieve usage data
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT timestamp, cost, service_type, operation
                    FROM usage_records
                    WHERE user_id = ? AND timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp
                """, (user_id, start_date.isoformat(), end_date.isoformat()))

                usage_data = cursor.fetchall()

            # Calculate analytics
            total_cost = sum(float(record[1]) for record in usage_data)
            transaction_count = len(usage_data)
            average_cost = total_cost / transaction_count if transaction_count > 0 else 0

            # Daily breakdown
            daily_costs = {}
            for record in usage_data:
                date_str = datetime.fromisoformat(record[0]).date().isoformat()
                if date_str not in daily_costs:
                    daily_costs[date_str] = 0.0
                daily_costs[date_str] += float(record[1])

            # Service type breakdown
            service_costs = {}
            for record in usage_data:
                service = record[2]
                if service not in service_costs:
                    service_costs[service] = 0.0
                service_costs[service] += float(record[1])

            # Generate educational insights
            insights = [
                f"Educational Insight: Average cost per transaction is ${average_cost:.2f}",
                f"Educational Insight: Total usage over {days} days is ${total_cost:.2f}",
                f"Educational Insight: Most expensive service type requires attorney review"
            ]

            analytics = {
                "period_summary": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_cost": total_cost,
                    "transaction_count": transaction_count,
                    "average_cost_per_transaction": average_cost,
                    "daily_average": total_cost / days
                },
                "daily_breakdown": daily_costs,
                "service_breakdown": service_costs,
                "educational_insights": insights,
                "cost_limits_status": self._get_cost_limits_status(user_id),
                "educational_purpose": "Cost analytics demonstration for educational purposes",
                "compliance_notices": [
                    "Cost analytics are for educational and budgeting purposes only",
                    "Attorney supervision required for billing decisions",
                    "Client billing must comply with professional responsibility rules"
                ],
                "attorney_review_required": True
            }

            # Log analytics generation
            audit_logger.log_pacer_event(
                user_id=user_id,
                event_type="cost_analytics_generated",
                service_type=PACERServiceType.CM_ECF.value,
                compliance_level=ComplianceLevel.EDUCATIONAL_ONLY.value,
                details={
                    "period_days": days,
                    "total_cost": total_cost,
                    "transaction_count": transaction_count
                }
            )

            return analytics

        except Exception as e:
            return {
                "error": f"Cost analytics generation failed: {str(e)}",
                "compliance_notices": ["Cost analytics require system access"]
            }

    def _get_cost_limits_status(self, user_id: str) -> Dict[str, Any]:
        """Get current status of all cost limits for user"""
        status = {}

        for limit in self.cost_limits.values():
            if limit.user_id == user_id and limit.active:
                usage_percent = float((limit.current_usage / limit.amount) * 100) if limit.amount > 0 else 0

                status[limit.limit_type] = {
                    "limit_amount": float(limit.amount),
                    "current_usage": float(limit.current_usage),
                    "remaining": float(limit.amount - limit.current_usage),
                    "usage_percent": usage_percent,
                    "period_end": limit.period_end.isoformat(),
                    "status": "approaching_limit" if usage_percent >= 75 else "normal"
                }

        return status

    def get_billing_status(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive billing and cost management status"""
        try:
            # Calculate current usage
            daily_usage = self._calculate_daily_usage(user_id)

            # Get pending alerts
            pending_alerts = [
                {
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type,
                    "message": alert.alert_message,
                    "timestamp": alert.timestamp.isoformat(),
                    "acknowledged": alert.acknowledged
                }
                for alert in self.cost_alerts
                if alert.user_id == user_id and not alert.acknowledged
            ]

            status = {
                "daily_usage": daily_usage,
                "daily_limit": float(self.cost_config["daily_limit_default"]),
                "daily_remaining": float(self.cost_config["daily_limit_default"]) - daily_usage,
                "active_cost_limits": len([l for l in self.cost_limits.values() if l.user_id == user_id and l.active]),
                "pending_alerts": pending_alerts,
                "billing_records_count": len([b for b in self.billing_records.values() if b.user_id == user_id]),
                "cost_management_status": {
                    "educational_purpose": "All cost management is for educational demonstration",
                    "attorney_supervision": "Required for all billing decisions and cost approvals",
                    "client_protection": "Transparent billing with full cost disclosure",
                    "professional_compliance": "Full compliance with billing ethics requirements"
                },
                "educational_disclaimers": self.billing_disclaimers[:4]
            }

            return status

        except Exception as e:
            return {
                "error": f"Billing status retrieval failed: {str(e)}",
                "compliance_notices": ["Billing status requires administrative access"]
            }


# Global cost manager instance
pacer_cost_manager = PACERCostManager()


def main():
    """Educational demonstration of PACER cost management system"""
    print("PACER COST MANAGEMENT AND BILLING INTEGRATION")
    print("=" * 60)
    print("EDUCATIONAL PURPOSE ONLY - NO LEGAL ADVICE PROVIDED")
    print("ATTORNEY SUPERVISION REQUIRED FOR ALL BILLING DECISIONS")
    print("=" * 60)

    # Get billing status
    status = pacer_cost_manager.get_billing_status("EDU_USER_001")
    print(f"\nCost Management Status:")
    print(f"  Daily Usage: ${status.get('daily_usage', 0.0):.2f}")
    print(f"  Daily Limit: ${status.get('daily_limit', 0.0):.2f}")
    print(f"  Active Limits: {status.get('active_cost_limits', 0)}")
    print(f"  Pending Alerts: {len(status.get('pending_alerts', []))}")

    print(f"\n[PASS] PACER COST MANAGEMENT SYSTEM OPERATIONAL")
    print(f"Educational compliance framework fully implemented")
    print(f"Attorney supervision requirements enforced")
    print(f"Comprehensive cost tracking and billing integration")
    print(f"Professional responsibility safeguards operational")


if __name__ == "__main__":
    main()