"""
PACER Cost Tracker

Tracks and manages PACER costs with real-time monitoring,
budgeting, billing records, and cost optimization features.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from ..shared.utils.cache_manager import cache_manager
from .models import (
    BillingRecord, CostAlert, UsageStatistics, PacerAccount,
    PACER_PRICING, calculate_document_cost
)


# Configure logging
logger = logging.getLogger(__name__)


class BillingPeriod(Enum):
    """Billing period types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class CostCategory(Enum):
    """Cost categories for classification"""
    DOCUMENT_ACCESS = "document_access"
    SEARCH_FEES = "search_fees"
    DOCKET_REPORTS = "docket_reports"
    BULK_DOWNLOADS = "bulk_downloads"
    OTHER = "other"


@dataclass
class CostLimit:
    """Cost limit configuration"""
    limit_id: str
    account_id: Optional[str] = None  # None = global limit
    user_id: Optional[int] = None
    court_id: Optional[str] = None
    period: BillingPeriod = BillingPeriod.MONTHLY
    limit_cents: int = 0
    current_usage_cents: int = 0
    is_active: bool = True
    auto_suspend: bool = False
    notification_thresholds: List[int] = field(default_factory=lambda: [80, 95])  # Percentages
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def limit_dollars(self) -> float:
        """Get limit in dollars"""
        return self.limit_cents / 100.0
    
    @property
    def current_usage_dollars(self) -> float:
        """Get current usage in dollars"""
        return self.current_usage_cents / 100.0
    
    @property
    def remaining_cents(self) -> int:
        """Get remaining budget in cents"""
        return max(0, self.limit_cents - self.current_usage_cents)
    
    @property
    def remaining_dollars(self) -> float:
        """Get remaining budget in dollars"""
        return self.remaining_cents / 100.0
    
    @property
    def usage_percentage(self) -> float:
        """Get usage percentage"""
        if self.limit_cents == 0:
            return 0.0
        return (self.current_usage_cents / self.limit_cents) * 100.0
    
    def is_exceeded(self) -> bool:
        """Check if limit is exceeded"""
        return self.current_usage_cents >= self.limit_cents
    
    def should_notify(self, threshold_percentage: int) -> bool:
        """Check if notification threshold is reached"""
        return self.usage_percentage >= threshold_percentage


@dataclass
class CostAnalysis:
    """Cost analysis result"""
    period_start: datetime
    period_end: datetime
    total_cost_cents: int = 0
    total_requests: int = 0
    total_pages: int = 0
    total_documents: int = 0
    cost_by_category: Dict[CostCategory, int] = field(default_factory=dict)
    cost_by_court: Dict[str, int] = field(default_factory=dict)
    cost_by_account: Dict[str, int] = field(default_factory=dict)
    average_cost_per_request_cents: float = 0.0
    average_cost_per_page_cents: float = 0.0
    peak_cost_day: Optional[datetime] = None
    peak_cost_amount_cents: int = 0
    
    @property
    def total_cost_dollars(self) -> float:
        """Get total cost in dollars"""
        return self.total_cost_cents / 100.0
    
    def __post_init__(self):
        # Calculate averages
        if self.total_requests > 0:
            self.average_cost_per_request_cents = self.total_cost_cents / self.total_requests
        
        if self.total_pages > 0:
            self.average_cost_per_page_cents = self.total_cost_cents / self.total_pages


class CostTracker:
    """PACER cost tracking and management system"""
    
    def __init__(self):
        self.billing_records: Dict[str, List[BillingRecord]] = {}  # account_id -> records
        self.cost_limits: Dict[str, CostLimit] = {}
        self.cost_alerts: Dict[str, List[CostAlert]] = {}
        
        # Cost optimization settings
        self.free_page_limit = PACER_PRICING["free_pages_per_document"]
        self.quarterly_cap_cents = PACER_PRICING["quarterly_spending_cap_cents"]
        self.auto_optimize_enabled = True
        
        logger.info("PACER Cost Tracker initialized")
    
    async def record_cost(
        self,
        account_id: str,
        court_id: str,
        description: str,
        cost_cents: int,
        case_number: str = None,
        page_count: int = 0,
        document_count: int = 0,
        category: CostCategory = CostCategory.OTHER,
        request_id: str = None
    ) -> BillingRecord:
        """Record a PACER cost transaction"""
        
        try:
            # Create billing record
            billing_record = BillingRecord(
                billing_id=f"bill_{account_id}_{int(datetime.now().timestamp())}",
                account_id=account_id,
                transaction_date=datetime.now(timezone.utc),
                court_id=court_id,
                case_number=case_number,
                description=description,
                cost_cents=cost_cents,
                page_count=page_count,
                document_count=document_count,
                request_id=request_id
            )
            
            # Calculate billable vs free pages
            if page_count > 0:
                billing_record.free_pages = min(page_count, self.free_page_limit)
                billing_record.billable_pages = max(0, page_count - self.free_page_limit)
            
            # Store billing record
            if account_id not in self.billing_records:
                self.billing_records[account_id] = []
            
            self.billing_records[account_id].append(billing_record)
            
            # Update cost limits
            await self._update_cost_limits(account_id, court_id, cost_cents)
            
            # Check alerts
            await self._check_cost_alerts(account_id, cost_cents)
            
            # Cache recent billing record
            await cache_manager.set(
                f"pacer:billing:{billing_record.billing_id}",
                billing_record.__dict__,
                ttl=86400  # 24 hours
            )
            
            logger.info(
                f"Recorded PACER cost: ${cost_cents/100:.2f} for account {account_id} "
                f"court {court_id} ({description})"
            )
            
            return billing_record
            
        except Exception as e:
            logger.error(f"Failed to record cost: {str(e)}")
            raise
    
    async def estimate_cost(
        self,
        operation_type: str,
        page_count: int = 0,
        document_count: int = 0,
        search_count: int = 0
    ) -> int:
        """Estimate cost for PACER operations in cents"""
        
        try:
            total_cost_cents = 0
            
            # Document costs
            if page_count > 0 and document_count > 0:
                avg_pages_per_doc = page_count / document_count
                
                for _ in range(document_count):
                    doc_cost = calculate_document_cost(int(avg_pages_per_doc))
                    total_cost_cents += doc_cost
            
            # Search costs
            if search_count > 0:
                search_cost_per_query = PACER_PRICING.get("search_fee_cents", 30)
                total_cost_cents += search_count * search_cost_per_query
            
            # Apply quarterly cap if enabled
            if total_cost_cents > self.quarterly_cap_cents:
                total_cost_cents = self.quarterly_cap_cents
            
            return total_cost_cents
            
        except Exception as e:
            logger.error(f"Failed to estimate cost: {str(e)}")
            return 0
    
    async def check_cost_approval(
        self,
        account_id: str,
        estimated_cost_cents: int,
        court_id: str = None,
        user_id: int = None
    ) -> Tuple[bool, str, Optional[CostLimit]]:
        """Check if cost is within limits and approved"""
        
        try:
            # Find applicable cost limits
            applicable_limits = await self._get_applicable_limits(
                account_id, court_id, user_id
            )
            
            if not applicable_limits:
                return True, "No cost limits configured", None
            
            # Check each limit
            for cost_limit in applicable_limits:
                projected_usage = cost_limit.current_usage_cents + estimated_cost_cents
                
                if projected_usage > cost_limit.limit_cents:
                    return False, (
                        f"Would exceed {cost_limit.period.value} limit: "
                        f"${projected_usage/100:.2f} > ${cost_limit.limit_dollars:.2f}"
                    ), cost_limit
            
            return True, "Cost approved", None
            
        except Exception as e:
            logger.error(f"Failed to check cost approval: {str(e)}")
            return False, f"Cost check failed: {str(e)}", None
    
    async def set_cost_limit(
        self,
        limit_id: str,
        limit_dollars: float,
        period: BillingPeriod,
        account_id: str = None,
        user_id: int = None,
        court_id: str = None,
        auto_suspend: bool = False,
        notification_thresholds: List[int] = None
    ) -> CostLimit:
        """Set or update a cost limit"""
        
        try:
            cost_limit = CostLimit(
                limit_id=limit_id,
                account_id=account_id,
                user_id=user_id,
                court_id=court_id,
                period=period,
                limit_cents=int(limit_dollars * 100),
                auto_suspend=auto_suspend,
                notification_thresholds=notification_thresholds or [80, 95]
            )
            
            # Calculate current usage for the period
            current_usage = await self._calculate_period_usage(
                period, account_id, user_id, court_id
            )
            cost_limit.current_usage_cents = current_usage
            
            self.cost_limits[limit_id] = cost_limit
            
            # Cache the limit
            await cache_manager.set(
                f"pacer:cost_limit:{limit_id}",
                cost_limit.__dict__,
                ttl=3600
            )
            
            logger.info(
                f"Set cost limit {limit_id}: ${limit_dollars:.2f} per {period.value}"
                f"{f' for account {account_id}' if account_id else ''}"
                f"{f' for user {user_id}' if user_id else ''}"
                f"{f' for court {court_id}' if court_id else ''}"
            )
            
            return cost_limit
            
        except Exception as e:
            logger.error(f"Failed to set cost limit: {str(e)}")
            raise
    
    async def get_cost_analysis(
        self,
        account_id: str = None,
        court_id: str = None,
        user_id: int = None,
        start_date: datetime = None,
        end_date: datetime = None,
        period: BillingPeriod = BillingPeriod.MONTHLY
    ) -> CostAnalysis:
        """Generate cost analysis report"""
        
        try:
            # Set default date range
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            if not start_date:
                if period == BillingPeriod.DAILY:
                    start_date = end_date - timedelta(days=1)
                elif period == BillingPeriod.WEEKLY:
                    start_date = end_date - timedelta(days=7)
                elif period == BillingPeriod.MONTHLY:
                    start_date = end_date - timedelta(days=30)
                elif period == BillingPeriod.QUARTERLY:
                    start_date = end_date - timedelta(days=90)
                else:  # YEARLY
                    start_date = end_date - timedelta(days=365)
            
            # Get billing records in range
            records = await self._get_billing_records(
                account_id, court_id, user_id, start_date, end_date
            )
            
            # Initialize analysis
            analysis = CostAnalysis(
                period_start=start_date,
                period_end=end_date
            )
            
            # Analyze records
            daily_costs: Dict[str, int] = {}
            
            for record in records:
                analysis.total_cost_cents += record.cost_cents
                analysis.total_requests += 1
                analysis.total_pages += record.page_count or 0
                analysis.total_documents += record.document_count
                
                # Cost by category (simplified categorization)
                category = self._categorize_transaction(record)
                if category not in analysis.cost_by_category:
                    analysis.cost_by_category[category] = 0
                analysis.cost_by_category[category] += record.cost_cents
                
                # Cost by court
                if record.court_id not in analysis.cost_by_court:
                    analysis.cost_by_court[record.court_id] = 0
                analysis.cost_by_court[record.court_id] += record.cost_cents
                
                # Cost by account
                if record.account_id not in analysis.cost_by_account:
                    analysis.cost_by_account[record.account_id] = 0
                analysis.cost_by_account[record.account_id] += record.cost_cents
                
                # Track daily costs for peak detection
                day_key = record.transaction_date.strftime("%Y-%m-%d")
                if day_key not in daily_costs:
                    daily_costs[day_key] = 0
                daily_costs[day_key] += record.cost_cents
            
            # Find peak cost day
            if daily_costs:
                peak_day, peak_amount = max(daily_costs.items(), key=lambda x: x[1])
                analysis.peak_cost_day = datetime.strptime(peak_day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                analysis.peak_cost_amount_cents = peak_amount
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to generate cost analysis: {str(e)}")
            raise
    
    async def optimize_cost_strategy(
        self,
        account_id: str,
        target_reduction_percentage: float = 20.0
    ) -> Dict[str, Any]:
        """Generate cost optimization recommendations"""
        
        try:
            # Analyze current usage patterns
            analysis = await self.get_cost_analysis(
                account_id=account_id,
                period=BillingPeriod.MONTHLY
            )
            
            recommendations = []
            potential_savings_cents = 0
            
            # Analyze document access patterns
            if analysis.cost_by_category.get(CostCategory.DOCUMENT_ACCESS, 0) > 0:
                doc_cost = analysis.cost_by_category[CostCategory.DOCUMENT_ACCESS]
                
                # Recommend bulk downloads for high-volume cases
                if analysis.total_documents > 100:
                    recommendations.append({
                        "type": "bulk_download",
                        "description": "Consider bulk downloads for high-volume cases",
                        "potential_savings_cents": int(doc_cost * 0.15),  # 15% savings
                        "implementation": "Use batch processing for multiple documents"
                    })
                    potential_savings_cents += int(doc_cost * 0.15)
            
            # Analyze search patterns
            if analysis.cost_by_category.get(CostCategory.SEARCH_FEES, 0) > 0:
                search_cost = analysis.cost_by_category[CostCategory.SEARCH_FEES]
                
                if analysis.total_requests > 200:
                    recommendations.append({
                        "type": "search_optimization",
                        "description": "Optimize search queries to reduce redundant searches",
                        "potential_savings_cents": int(search_cost * 0.10),  # 10% savings
                        "implementation": "Cache search results and use more specific queries"
                    })
                    potential_savings_cents += int(search_cost * 0.10)
            
            # Court-specific recommendations
            sorted_courts = sorted(
                analysis.cost_by_court.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            if len(sorted_courts) > 1:
                highest_cost_court = sorted_courts[0]
                recommendations.append({
                    "type": "court_prioritization",
                    "description": f"Focus optimization on {highest_cost_court[0]} court (highest cost)",
                    "potential_savings_cents": int(highest_cost_court[1] * 0.05),  # 5% savings
                    "implementation": "Prioritize free resources and optimize query strategies"
                })
                potential_savings_cents += int(highest_cost_court[1] * 0.05)
            
            # Time-based recommendations
            if analysis.peak_cost_day:
                recommendations.append({
                    "type": "load_balancing",
                    "description": "Distribute requests more evenly across time periods",
                    "potential_savings_cents": int(analysis.total_cost_cents * 0.03),  # 3% savings
                    "implementation": "Schedule non-urgent requests during off-peak periods"
                })
                potential_savings_cents += int(analysis.total_cost_cents * 0.03)
            
            return {
                "current_monthly_cost_dollars": analysis.total_cost_dollars,
                "target_reduction_percentage": target_reduction_percentage,
                "potential_savings_dollars": potential_savings_cents / 100.0,
                "potential_savings_percentage": (potential_savings_cents / max(1, analysis.total_cost_cents)) * 100,
                "recommendations": recommendations,
                "analysis_period": {
                    "start": analysis.period_start.isoformat(),
                    "end": analysis.period_end.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize cost strategy: {str(e)}")
            return {}
    
    async def get_billing_summary(
        self,
        account_id: str = None,
        period: BillingPeriod = BillingPeriod.MONTHLY
    ) -> Dict[str, Any]:
        """Get billing summary for an account or all accounts"""
        
        try:
            end_date = datetime.now(timezone.utc)
            
            if period == BillingPeriod.DAILY:
                start_date = end_date - timedelta(days=1)
            elif period == BillingPeriod.WEEKLY:
                start_date = end_date - timedelta(days=7)
            elif period == BillingPeriod.MONTHLY:
                start_date = end_date - timedelta(days=30)
            elif period == BillingPeriod.QUARTERLY:
                start_date = end_date - timedelta(days=90)
            else:  # YEARLY
                start_date = end_date - timedelta(days=365)
            
            records = await self._get_billing_records(
                account_id, None, None, start_date, end_date
            )
            
            # Group by account
            account_summaries = {}
            total_cost_cents = 0
            
            for record in records:
                acc_id = record.account_id
                
                if acc_id not in account_summaries:
                    account_summaries[acc_id] = {
                        "account_id": acc_id,
                        "total_cost_cents": 0,
                        "total_requests": 0,
                        "total_pages": 0,
                        "total_documents": 0,
                        "courts_used": set()
                    }
                
                summary = account_summaries[acc_id]
                summary["total_cost_cents"] += record.cost_cents
                summary["total_requests"] += 1
                summary["total_pages"] += record.page_count or 0
                summary["total_documents"] += record.document_count
                summary["courts_used"].add(record.court_id)
                
                total_cost_cents += record.cost_cents
            
            # Convert sets to lists for JSON serialization
            for summary in account_summaries.values():
                summary["courts_used"] = list(summary["courts_used"])
                summary["total_cost_dollars"] = summary["total_cost_cents"] / 100.0
                summary["average_cost_per_request_dollars"] = (
                    summary["total_cost_cents"] / max(1, summary["total_requests"]) / 100.0
                )
            
            return {
                "period": period.value,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_cost_dollars": total_cost_cents / 100.0,
                "account_count": len(account_summaries),
                "account_summaries": list(account_summaries.values())
            }
            
        except Exception as e:
            logger.error(f"Failed to get billing summary: {str(e)}")
            return {}
    
    async def _update_cost_limits(self, account_id: str, court_id: str, cost_cents: int):
        """Update current usage for applicable cost limits"""
        
        try:
            applicable_limits = await self._get_applicable_limits(account_id, court_id, None)
            
            for cost_limit in applicable_limits:
                cost_limit.current_usage_cents += cost_cents
                
                # Update cache
                await cache_manager.set(
                    f"pacer:cost_limit:{cost_limit.limit_id}",
                    cost_limit.__dict__,
                    ttl=3600
                )
            
        except Exception as e:
            logger.error(f"Failed to update cost limits: {str(e)}")
    
    async def _get_applicable_limits(
        self,
        account_id: str = None,
        court_id: str = None,
        user_id: int = None
    ) -> List[CostLimit]:
        """Get cost limits that apply to the given parameters"""
        
        applicable_limits = []
        
        for cost_limit in self.cost_limits.values():
            if not cost_limit.is_active:
                continue
            
            # Check if limit applies
            matches = True
            
            if cost_limit.account_id and cost_limit.account_id != account_id:
                matches = False
            
            if cost_limit.court_id and cost_limit.court_id != court_id:
                matches = False
            
            if cost_limit.user_id and cost_limit.user_id != user_id:
                matches = False
            
            if matches:
                applicable_limits.append(cost_limit)
        
        return applicable_limits
    
    async def _calculate_period_usage(
        self,
        period: BillingPeriod,
        account_id: str = None,
        user_id: int = None,
        court_id: str = None
    ) -> int:
        """Calculate usage for a specific period"""
        
        end_date = datetime.now(timezone.utc)
        
        if period == BillingPeriod.DAILY:
            start_date = end_date - timedelta(days=1)
        elif period == BillingPeriod.WEEKLY:
            start_date = end_date - timedelta(days=7)
        elif period == BillingPeriod.MONTHLY:
            start_date = end_date - timedelta(days=30)
        elif period == BillingPeriod.QUARTERLY:
            start_date = end_date - timedelta(days=90)
        else:  # YEARLY
            start_date = end_date - timedelta(days=365)
        
        records = await self._get_billing_records(
            account_id, court_id, user_id, start_date, end_date
        )
        
        return sum(record.cost_cents for record in records)
    
    async def _get_billing_records(
        self,
        account_id: str = None,
        court_id: str = None,
        user_id: int = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[BillingRecord]:
        """Get billing records matching criteria"""
        
        all_records = []
        
        # Collect records from all accounts or specific account
        if account_id:
            all_records.extend(self.billing_records.get(account_id, []))
        else:
            for records_list in self.billing_records.values():
                all_records.extend(records_list)
        
        # Filter records
        filtered_records = []
        
        for record in all_records:
            # Date filter
            if start_date and record.transaction_date < start_date:
                continue
            if end_date and record.transaction_date > end_date:
                continue
            
            # Court filter
            if court_id and record.court_id != court_id:
                continue
            
            # User filter (would need user_id in billing record)
            # if user_id and record.user_id != user_id:
            #     continue
            
            filtered_records.append(record)
        
        return filtered_records
    
    async def _check_cost_alerts(self, account_id: str, cost_cents: int):
        """Check and trigger cost alerts"""
        
        try:
            # Check cost limits for alert thresholds
            applicable_limits = await self._get_applicable_limits(account_id, None, None)
            
            for cost_limit in applicable_limits:
                for threshold in cost_limit.notification_thresholds:
                    if cost_limit.should_notify(threshold):
                        logger.warning(
                            f"Cost alert: Account {account_id} has reached {threshold}% "
                            f"of {cost_limit.period.value} limit "
                            f"(${cost_limit.current_usage_dollars:.2f} / ${cost_limit.limit_dollars:.2f})"
                        )
                        
                        # TODO: Implement actual alert notification
        
        except Exception as e:
            logger.error(f"Failed to check cost alerts: {str(e)}")
    
    def _categorize_transaction(self, record: BillingRecord) -> CostCategory:
        """Categorize a billing transaction"""
        
        description = record.description.lower()
        
        if "document" in description or "pdf" in description:
            return CostCategory.DOCUMENT_ACCESS
        elif "search" in description or "query" in description:
            return CostCategory.SEARCH_FEES
        elif "docket" in description:
            return CostCategory.DOCKET_REPORTS
        elif "bulk" in description or "batch" in description:
            return CostCategory.BULK_DOWNLOADS
        else:
            return CostCategory.OTHER


# Global cost tracker instance
cost_tracker = CostTracker()