"""
PACER-specific billing and cost tracking system.

Handles PACER fee tracking, quarterly exemption management, and detailed
cost allocation for PACER searches, document views, and docket reports.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
from collections import defaultdict

from ..shared.utils import BaseAPIClient
from .models import (
    CostType, AllocationMethod, BillingStatus, PACERRates, PACERCostType,
    BillingAccount, generate_billing_id
)


@dataclass
class PACERCost:
    """Individual PACER cost entry."""
    cost_id: str
    pacer_cost_type: PACERCostType
    case_number: Optional[str]
    document_id: Optional[str]
    court_id: str
    
    # Cost details
    quantity: int  # searches, pages, reports, etc.
    unit_cost: Decimal
    subtotal: Decimal
    exemption_applied: Decimal
    final_cost: Decimal
    
    # Client allocation
    client_id: Optional[str] = None
    matter_number: Optional[str] = None
    allocation_method: AllocationMethod = AllocationMethod.DIRECT
    allocation_percentage: Decimal = Decimal('100.0')
    
    # Transaction details
    pacer_account_id: str = ""
    transaction_id: Optional[str] = None
    transaction_date: datetime = field(default_factory=datetime.utcnow)
    
    # Request context
    requested_by: Optional[str] = None
    request_purpose: Optional[str] = None
    project_code: Optional[str] = None
    
    # Audit trail
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    
    # Billing status
    billing_status: BillingStatus = BillingStatus.DRAFT
    invoice_id: Optional[str] = None
    billed_at: Optional[datetime] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PACERTransaction:
    """PACER transaction grouping multiple costs."""
    transaction_id: str
    pacer_account_id: str
    transaction_date: datetime
    
    # Cost summary
    total_searches: int
    total_pages: int
    total_documents: int
    
    # Financial summary
    subtotal: Decimal
    exemption_applied: Decimal
    final_total: Decimal
    
    # Individual costs
    costs: List[PACERCost] = field(default_factory=list)
    
    # Client allocation
    client_allocations: Dict[str, Decimal] = field(default_factory=dict)
    
    # Transaction context
    session_id: Optional[str] = None
    batch_id: Optional[str] = None
    requested_by: Optional[str] = None
    
    # Status
    status: BillingStatus = BillingStatus.PENDING_REVIEW
    processed_at: Optional[datetime] = None
    
    @property
    def average_cost_per_page(self) -> Decimal:
        """Calculate average cost per page."""
        if self.total_pages == 0:
            return Decimal('0.0')
        return self.subtotal / Decimal(str(self.total_pages))
    
    @property
    def exemption_rate(self) -> Decimal:
        """Calculate percentage of costs covered by exemption."""
        if self.subtotal == 0:
            return Decimal('0.0')
        return (self.exemption_applied / self.subtotal) * Decimal('100')


@dataclass
class PACERQuarterlyExemption:
    """PACER quarterly exemption tracking."""
    account_id: str
    quarter: int  # 1-4
    year: int
    
    # Exemption limits
    exemption_limit: Decimal = Decimal('30.00')
    exemption_used: Decimal = Decimal('0.0')
    exemption_remaining: Decimal = Decimal('30.00')
    
    # Usage tracking
    transactions_count: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def can_apply_exemption(self, amount: Decimal) -> bool:
        """Check if exemption can be applied to amount."""
        return self.exemption_remaining > 0 and amount > 0
    
    def apply_exemption(self, amount: Decimal) -> Tuple[Decimal, Decimal]:
        """Apply exemption and return (exemption_applied, remaining_cost)."""
        if not self.can_apply_exemption(amount):
            return Decimal('0.0'), amount
        
        exemption_to_apply = min(amount, self.exemption_remaining)
        remaining_cost = amount - exemption_to_apply
        
        # Update tracking
        self.exemption_used += exemption_to_apply
        self.exemption_remaining -= exemption_to_apply
        self.last_updated = datetime.utcnow()
        
        return exemption_to_apply, remaining_cost


class PACERBillingManager:
    """Comprehensive PACER billing and cost tracking system."""
    
    def __init__(self, api_client: Optional[BaseAPIClient] = None):
        self.api_client = api_client
        self.rates = PACERRates.get_current_rates()
        self.quarterly_exemptions: Dict[str, PACERQuarterlyExemption] = {}
        self.cost_cache: Dict[str, List[PACERCost]] = defaultdict(list)
        self.logger = logging.getLogger(__name__)
        
    async def track_pacer_search(self,
                               court_id: str,
                               search_count: int = 1,
                               client_id: Optional[str] = None,
                               case_number: Optional[str] = None,
                               pacer_account_id: str = "",
                               requested_by: Optional[str] = None,
                               request_purpose: Optional[str] = None) -> PACERCost:
        """
        Track PACER search costs.
        
        Args:
            court_id: PACER court identifier
            search_count: Number of searches performed
            client_id: Client to bill for the search
            case_number: Case number if applicable
            pacer_account_id: PACER account used
            requested_by: User who made the request
            request_purpose: Purpose of the search
            
        Returns:
            PACERCost object with calculated costs
        """
        subtotal = self.rates.calculate_search_cost(search_count)
        
        # Apply quarterly exemption if available
        exemption = await self._get_quarterly_exemption(pacer_account_id)
        exemption_applied, final_cost = exemption.apply_exemption(subtotal)
        
        # Create cost entry
        cost = PACERCost(
            cost_id=generate_billing_id(),
            pacer_cost_type=PACERCostType.SEARCH,
            case_number=case_number,
            court_id=court_id,
            quantity=search_count,
            unit_cost=self.rates.search_fee,
            subtotal=subtotal,
            exemption_applied=exemption_applied,
            final_cost=final_cost,
            client_id=client_id,
            pacer_account_id=pacer_account_id,
            requested_by=requested_by,
            request_purpose=request_purpose
        )
        
        # Store cost entry
        await self._store_cost(cost)
        
        # Update quarterly exemption tracking
        await self._update_exemption_tracking(pacer_account_id, exemption)
        
        self.logger.info(f"Tracked PACER search: {search_count} searches, ${final_cost}")
        
        return cost
    
    async def track_pacer_document(self,
                                 court_id: str,
                                 document_id: str,
                                 page_count: int,
                                 client_id: Optional[str] = None,
                                 case_number: Optional[str] = None,
                                 pacer_account_id: str = "",
                                 requested_by: Optional[str] = None,
                                 request_purpose: Optional[str] = None) -> PACERCost:
        """
        Track PACER document viewing costs.
        
        Args:
            court_id: PACER court identifier
            document_id: Document identifier
            page_count: Number of pages viewed
            client_id: Client to bill for the document
            case_number: Case number
            pacer_account_id: PACER account used
            requested_by: User who requested the document
            request_purpose: Purpose of document access
            
        Returns:
            PACERCost object with calculated costs
        """
        subtotal = self.rates.calculate_document_cost(page_count)
        
        # Apply quarterly exemption if available
        exemption = await self._get_quarterly_exemption(pacer_account_id)
        exemption_applied, final_cost = exemption.apply_exemption(subtotal)
        
        # Create cost entry
        cost = PACERCost(
            cost_id=generate_billing_id(),
            pacer_cost_type=PACERCostType.DOCUMENT_VIEW,
            document_id=document_id,
            case_number=case_number,
            court_id=court_id,
            quantity=page_count,
            unit_cost=self.rates.page_fee,
            subtotal=subtotal,
            exemption_applied=exemption_applied,
            final_cost=final_cost,
            client_id=client_id,
            pacer_account_id=pacer_account_id,
            requested_by=requested_by,
            request_purpose=request_purpose
        )
        
        # Store cost entry
        await self._store_cost(cost)
        
        # Update quarterly exemption tracking
        await self._update_exemption_tracking(pacer_account_id, exemption)
        
        self.logger.info(f"Tracked PACER document: {page_count} pages, ${final_cost}")
        
        return cost
    
    async def track_pacer_docket(self,
                               court_id: str,
                               case_number: str,
                               page_count: int,
                               client_id: Optional[str] = None,
                               pacer_account_id: str = "",
                               requested_by: Optional[str] = None,
                               request_purpose: Optional[str] = None) -> PACERCost:
        """
        Track PACER docket report costs.
        
        Args:
            court_id: PACER court identifier
            case_number: Case number
            page_count: Number of pages in docket report
            client_id: Client to bill for the report
            pacer_account_id: PACER account used
            requested_by: User who requested the report
            request_purpose: Purpose of docket report
            
        Returns:
            PACERCost object with calculated costs
        """
        subtotal = self.rates.calculate_docket_cost(page_count)
        
        # Apply quarterly exemption if available
        exemption = await self._get_quarterly_exemption(pacer_account_id)
        exemption_applied, final_cost = exemption.apply_exemption(subtotal)
        
        # Create cost entry
        cost = PACERCost(
            cost_id=generate_billing_id(),
            pacer_cost_type=PACERCostType.DOCKET_REPORT,
            case_number=case_number,
            court_id=court_id,
            quantity=page_count,
            unit_cost=self.rates.page_fee,
            subtotal=subtotal,
            exemption_applied=exemption_applied,
            final_cost=final_cost,
            client_id=client_id,
            pacer_account_id=pacer_account_id,
            requested_by=requested_by,
            request_purpose=request_purpose
        )
        
        # Store cost entry
        await self._store_cost(cost)
        
        # Update quarterly exemption tracking
        await self._update_exemption_tracking(pacer_account_id, exemption)
        
        self.logger.info(f"Tracked PACER docket: {page_count} pages, ${final_cost}")
        
        return cost
    
    async def create_transaction(self,
                               costs: List[PACERCost],
                               pacer_account_id: str,
                               session_id: Optional[str] = None,
                               batch_id: Optional[str] = None,
                               requested_by: Optional[str] = None) -> PACERTransaction:
        """
        Group individual costs into a transaction.
        
        Args:
            costs: List of PACERCost objects
            pacer_account_id: PACER account ID
            session_id: Optional session identifier
            batch_id: Optional batch identifier
            requested_by: User who initiated the transaction
            
        Returns:
            PACERTransaction object
        """
        if not costs:
            raise ValueError("Cannot create transaction without costs")
        
        # Calculate totals
        total_searches = sum(1 for cost in costs if cost.pacer_cost_type == PACERCostType.SEARCH)
        total_pages = sum(
            cost.quantity for cost in costs 
            if cost.pacer_cost_type in [PACERCostType.DOCUMENT_VIEW, PACERCostType.DOCKET_REPORT]
        )
        total_documents = len(set(cost.document_id for cost in costs if cost.document_id))
        
        subtotal = sum(cost.subtotal for cost in costs)
        exemption_applied = sum(cost.exemption_applied for cost in costs)
        final_total = sum(cost.final_cost for cost in costs)
        
        # Calculate client allocations
        client_allocations = defaultdict(Decimal)
        for cost in costs:
            if cost.client_id and cost.final_cost > 0:
                allocation_amount = cost.final_cost * (cost.allocation_percentage / Decimal('100'))
                client_allocations[cost.client_id] += allocation_amount
        
        # Create transaction
        transaction = PACERTransaction(
            transaction_id=generate_billing_id(),
            pacer_account_id=pacer_account_id,
            transaction_date=datetime.utcnow(),
            total_searches=total_searches,
            total_pages=total_pages,
            total_documents=total_documents,
            subtotal=subtotal,
            exemption_applied=exemption_applied,
            final_total=final_total,
            costs=costs,
            client_allocations=dict(client_allocations),
            session_id=session_id,
            batch_id=batch_id,
            requested_by=requested_by
        )
        
        # Store transaction
        await self._store_transaction(transaction)
        
        self.logger.info(
            f"Created PACER transaction {transaction.transaction_id}: "
            f"{total_searches} searches, {total_pages} pages, ${final_total}"
        )
        
        return transaction
    
    async def get_client_costs(self,
                             client_id: str,
                             start_date: Optional[date] = None,
                             end_date: Optional[date] = None,
                             include_unbilled: bool = True) -> List[PACERCost]:
        """
        Get PACER costs for a specific client.
        
        Args:
            client_id: Client identifier
            start_date: Start date for cost query
            end_date: End date for cost query
            include_unbilled: Whether to include unbilled costs
            
        Returns:
            List of PACERCost objects for the client
        """
        try:
            if self.api_client:
                response = await self.api_client.get(
                    f"/billing/pacer-costs/client/{client_id}",
                    params={
                        "start_date": start_date.isoformat() if start_date else None,
                        "end_date": end_date.isoformat() if end_date else None,
                        "include_unbilled": include_unbilled
                    }
                )
                
                # Convert response to PACERCost objects
                costs = []
                for cost_data in response.get("costs", []):
                    cost = self._dict_to_pacer_cost(cost_data)
                    costs.append(cost)
                
                return costs
            else:
                # Return cached costs for client
                return [
                    cost for cost in self.cost_cache[client_id]
                    if self._cost_matches_date_range(cost, start_date, end_date)
                ]
                
        except Exception as e:
            self.logger.error(f"Failed to get client costs for {client_id}: {e}")
            return []
    
    async def get_quarterly_summary(self,
                                  account_id: str,
                                  quarter: int,
                                  year: int) -> Dict[str, Any]:
        """
        Get quarterly PACER cost summary.
        
        Args:
            account_id: PACER account ID
            quarter: Quarter (1-4)
            year: Year
            
        Returns:
            Dictionary with quarterly summary
        """
        quarter_start = date(year, (quarter - 1) * 3 + 1, 1)
        if quarter == 4:
            quarter_end = date(year, 12, 31)
        else:
            quarter_end = date(year, quarter * 3 + 1, 1) - timedelta(days=1)
        
        try:
            if self.api_client:
                response = await self.api_client.get(
                    f"/billing/pacer-costs/quarterly-summary",
                    params={
                        "account_id": account_id,
                        "quarter": quarter,
                        "year": year
                    }
                )
                return response
            else:
                # Calculate summary from cached data
                exemption = await self._get_quarterly_exemption(account_id, quarter, year)
                
                return {
                    "quarter": quarter,
                    "year": year,
                    "account_id": account_id,
                    "exemption_limit": float(exemption.exemption_limit),
                    "exemption_used": float(exemption.exemption_used),
                    "exemption_remaining": float(exemption.exemption_remaining),
                    "total_costs": 0.0,  # Would calculate from actual data
                    "net_costs": 0.0,
                    "transaction_count": exemption.transactions_count
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get quarterly summary: {e}")
            return {}
    
    async def allocate_costs_to_clients(self,
                                      costs: List[PACERCost],
                                      allocation_rules: Dict[str, Any]) -> Dict[str, List[PACERCost]]:
        """
        Allocate PACER costs to clients based on rules.
        
        Args:
            costs: List of costs to allocate
            allocation_rules: Rules for cost allocation
            
        Returns:
            Dictionary mapping client IDs to their allocated costs
        """
        client_costs = defaultdict(list)
        
        for cost in costs:
            if cost.client_id:
                # Direct allocation
                client_costs[cost.client_id].append(cost)
            else:
                # Apply allocation rules
                allocated_clients = self._apply_allocation_rules(cost, allocation_rules)
                
                for client_id, percentage in allocated_clients.items():
                    allocated_cost = self._create_allocated_cost(cost, client_id, percentage)
                    client_costs[client_id].append(allocated_cost)
        
        return dict(client_costs)
    
    async def get_cost_analytics(self,
                               start_date: Optional[date] = None,
                               end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get PACER cost analytics and trends.
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Dictionary with cost analytics
        """
        try:
            if self.api_client:
                response = await self.api_client.get(
                    "/billing/pacer-costs/analytics",
                    params={
                        "start_date": start_date.isoformat() if start_date else None,
                        "end_date": end_date.isoformat() if end_date else None
                    }
                )
                return response
            else:
                # Basic analytics from cached data
                return {
                    "total_costs": 0.0,
                    "total_searches": 0,
                    "total_pages": 0,
                    "average_cost_per_search": 0.0,
                    "average_cost_per_page": 0.0,
                    "top_courts": [],
                    "top_clients": [],
                    "monthly_trends": []
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get cost analytics: {e}")
            return {}
    
    async def _get_quarterly_exemption(self,
                                     account_id: str,
                                     quarter: Optional[int] = None,
                                     year: Optional[int] = None) -> PACERQuarterlyExemption:
        """Get or create quarterly exemption tracker."""
        now = datetime.utcnow()
        quarter = quarter or ((now.month - 1) // 3) + 1
        year = year or now.year
        
        exemption_key = f"{account_id}-{year}-Q{quarter}"
        
        if exemption_key not in self.quarterly_exemptions:
            self.quarterly_exemptions[exemption_key] = PACERQuarterlyExemption(
                account_id=account_id,
                quarter=quarter,
                year=year
            )
        
        return self.quarterly_exemptions[exemption_key]
    
    async def _store_cost(self, cost: PACERCost):
        """Store PACER cost entry."""
        try:
            if self.api_client:
                await self.api_client.post(
                    "/billing/pacer-costs",
                    json=self._pacer_cost_to_dict(cost)
                )
            else:
                # Store in cache
                if cost.client_id:
                    self.cost_cache[cost.client_id].append(cost)
                    
        except Exception as e:
            self.logger.error(f"Failed to store cost {cost.cost_id}: {e}")
    
    async def _store_transaction(self, transaction: PACERTransaction):
        """Store PACER transaction."""
        try:
            if self.api_client:
                await self.api_client.post(
                    "/billing/pacer-transactions",
                    json=self._pacer_transaction_to_dict(transaction)
                )
                
        except Exception as e:
            self.logger.error(f"Failed to store transaction {transaction.transaction_id}: {e}")
    
    async def _update_exemption_tracking(self, account_id: str, exemption: PACERQuarterlyExemption):
        """Update quarterly exemption tracking in storage."""
        try:
            if self.api_client:
                await self.api_client.put(
                    f"/billing/quarterly-exemptions/{account_id}",
                    json={
                        "quarter": exemption.quarter,
                        "year": exemption.year,
                        "exemption_used": float(exemption.exemption_used),
                        "exemption_remaining": float(exemption.exemption_remaining),
                        "transactions_count": exemption.transactions_count,
                        "last_updated": exemption.last_updated.isoformat()
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Failed to update exemption tracking: {e}")
    
    def _apply_allocation_rules(self, cost: PACERCost, rules: Dict[str, Any]) -> Dict[str, Decimal]:
        """Apply allocation rules to determine client allocation."""
        # Simplified allocation logic - in production this would be more complex
        default_client = rules.get("default_client")
        if default_client:
            return {default_client: Decimal('100.0')}
        
        return {}
    
    def _create_allocated_cost(self, 
                             original_cost: PACERCost, 
                             client_id: str, 
                             percentage: Decimal) -> PACERCost:
        """Create allocated cost for specific client."""
        allocated_cost = PACERCost(
            cost_id=f"{original_cost.cost_id}-{client_id}",
            pacer_cost_type=original_cost.pacer_cost_type,
            case_number=original_cost.case_number,
            document_id=original_cost.document_id,
            court_id=original_cost.court_id,
            quantity=original_cost.quantity,
            unit_cost=original_cost.unit_cost,
            subtotal=original_cost.subtotal * (percentage / Decimal('100')),
            exemption_applied=original_cost.exemption_applied * (percentage / Decimal('100')),
            final_cost=original_cost.final_cost * (percentage / Decimal('100')),
            client_id=client_id,
            allocation_percentage=percentage,
            pacer_account_id=original_cost.pacer_account_id,
            transaction_date=original_cost.transaction_date,
            requested_by=original_cost.requested_by,
            request_purpose=original_cost.request_purpose
        )
        
        return allocated_cost
    
    def _pacer_cost_to_dict(self, cost: PACERCost) -> Dict[str, Any]:
        """Convert PACERCost to dictionary."""
        return {
            "cost_id": cost.cost_id,
            "pacer_cost_type": cost.pacer_cost_type.value,
            "case_number": cost.case_number,
            "document_id": cost.document_id,
            "court_id": cost.court_id,
            "quantity": cost.quantity,
            "unit_cost": float(cost.unit_cost),
            "subtotal": float(cost.subtotal),
            "exemption_applied": float(cost.exemption_applied),
            "final_cost": float(cost.final_cost),
            "client_id": cost.client_id,
            "matter_number": cost.matter_number,
            "allocation_method": cost.allocation_method.value,
            "allocation_percentage": float(cost.allocation_percentage),
            "pacer_account_id": cost.pacer_account_id,
            "transaction_id": cost.transaction_id,
            "transaction_date": cost.transaction_date.isoformat(),
            "requested_by": cost.requested_by,
            "request_purpose": cost.request_purpose,
            "project_code": cost.project_code,
            "created_at": cost.created_at.isoformat(),
            "created_by": cost.created_by,
            "billing_status": cost.billing_status.value,
            "tags": cost.tags,
            "notes": cost.notes,
            "metadata": cost.metadata
        }
    
    def _pacer_transaction_to_dict(self, transaction: PACERTransaction) -> Dict[str, Any]:
        """Convert PACERTransaction to dictionary."""
        return {
            "transaction_id": transaction.transaction_id,
            "pacer_account_id": transaction.pacer_account_id,
            "transaction_date": transaction.transaction_date.isoformat(),
            "total_searches": transaction.total_searches,
            "total_pages": transaction.total_pages,
            "total_documents": transaction.total_documents,
            "subtotal": float(transaction.subtotal),
            "exemption_applied": float(transaction.exemption_applied),
            "final_total": float(transaction.final_total),
            "costs": [self._pacer_cost_to_dict(cost) for cost in transaction.costs],
            "client_allocations": {k: float(v) for k, v in transaction.client_allocations.items()},
            "session_id": transaction.session_id,
            "batch_id": transaction.batch_id,
            "requested_by": transaction.requested_by,
            "status": transaction.status.value,
            "processed_at": transaction.processed_at.isoformat() if transaction.processed_at else None
        }
    
    def _dict_to_pacer_cost(self, data: Dict[str, Any]) -> PACERCost:
        """Convert dictionary to PACERCost object."""
        return PACERCost(
            cost_id=data["cost_id"],
            pacer_cost_type=PACERCostType(data["pacer_cost_type"]),
            case_number=data.get("case_number"),
            document_id=data.get("document_id"),
            court_id=data["court_id"],
            quantity=data["quantity"],
            unit_cost=Decimal(str(data["unit_cost"])),
            subtotal=Decimal(str(data["subtotal"])),
            exemption_applied=Decimal(str(data["exemption_applied"])),
            final_cost=Decimal(str(data["final_cost"])),
            client_id=data.get("client_id"),
            matter_number=data.get("matter_number"),
            allocation_method=AllocationMethod(data["allocation_method"]),
            allocation_percentage=Decimal(str(data["allocation_percentage"])),
            pacer_account_id=data["pacer_account_id"],
            transaction_id=data.get("transaction_id"),
            transaction_date=datetime.fromisoformat(data["transaction_date"]),
            requested_by=data.get("requested_by"),
            request_purpose=data.get("request_purpose"),
            billing_status=BillingStatus(data["billing_status"])
        )
    
    def _cost_matches_date_range(self, 
                                cost: PACERCost, 
                                start_date: Optional[date], 
                                end_date: Optional[date]) -> bool:
        """Check if cost falls within date range."""
        cost_date = cost.transaction_date.date()
        
        if start_date and cost_date < start_date:
            return False
        
        if end_date and cost_date > end_date:
            return False
        
        return True