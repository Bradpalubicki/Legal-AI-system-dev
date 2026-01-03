"""
Comprehensive cost tracking system for legal operations.

Tracks all types of costs including PACER fees, research costs, court fees,
and other legal expenses with detailed categorization and reporting.
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
    CostType, AllocationMethod, BillingStatus, BillingAccount,
    generate_billing_id, get_cost_type_display_name, is_pacer_cost_type
)
from .pacer_billing import PACERBillingManager, PACERCost


@dataclass
class CostCategory:
    """Category for grouping related costs."""
    category_id: str
    name: str
    description: str
    cost_types: List[CostType] = field(default_factory=list)
    is_billable: bool = True
    markup_percentage: Decimal = Decimal('0.0')
    
    # Category configuration
    requires_approval: bool = False
    approval_threshold: Optional[Decimal] = None
    auto_allocate: bool = False
    default_allocation_method: AllocationMethod = AllocationMethod.DIRECT
    
    # Display settings
    color_code: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0


@dataclass
class CostEntry:
    """Individual cost entry in the system."""
    cost_id: str
    cost_type: CostType
    category_id: Optional[str]
    
    # Basic cost information
    amount: Decimal
    currency: str = "USD"
    description: str = ""
    
    # Associated entities
    client_id: Optional[str] = None
    matter_number: Optional[str] = None
    case_number: Optional[str] = None
    project_code: Optional[str] = None
    
    # Source information
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    reference_number: Optional[str] = None
    
    # Timing
    cost_date: date = field(default_factory=date.today)
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    
    # User and approval
    incurred_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Allocation
    allocation_method: AllocationMethod = AllocationMethod.DIRECT
    allocation_percentage: Decimal = Decimal('100.0')
    allocated_clients: Dict[str, Decimal] = field(default_factory=dict)
    
    # Status and billing
    status: BillingStatus = BillingStatus.DRAFT
    is_billable: bool = True
    markup_amount: Decimal = Decimal('0.0')
    total_amount: Decimal = field(init=False)
    
    # Audit trail
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    # Additional data
    tags: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Calculate total amount after initialization."""
        self.total_amount = self.amount + self.markup_amount
    
    @property
    def display_name(self) -> str:
        """Get display name for cost type."""
        return get_cost_type_display_name(self.cost_type)
    
    def update_total_amount(self):
        """Update total amount when base amount or markup changes."""
        self.total_amount = self.amount + self.markup_amount
        self.updated_at = datetime.utcnow()


@dataclass
class CostAllocation:
    """Cost allocation to specific client."""
    allocation_id: str
    cost_id: str
    client_id: str
    matter_number: Optional[str]
    
    # Allocation details
    allocated_amount: Decimal
    allocation_percentage: Decimal
    allocation_method: AllocationMethod
    allocation_basis: Optional[str] = None
    
    # Status
    status: BillingStatus = BillingStatus.PENDING_REVIEW
    invoice_id: Optional[str] = None
    billed_at: Optional[datetime] = None
    
    # Metadata
    allocated_at: datetime = field(default_factory=datetime.utcnow)
    allocated_by: Optional[str] = None
    notes: Optional[str] = None


class CostTracker:
    """Comprehensive cost tracking and management system."""
    
    def __init__(self, api_client: Optional[BaseAPIClient] = None):
        self.api_client = api_client
        self.pacer_billing = PACERBillingManager(api_client)
        self.cost_categories = self._initialize_cost_categories()
        self.cost_entries: Dict[str, CostEntry] = {}
        self.cost_allocations: Dict[str, List[CostAllocation]] = defaultdict(list)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_cost_categories(self) -> Dict[str, CostCategory]:
        """Initialize default cost categories."""
        categories = {}
        
        # PACER costs
        categories["pacer"] = CostCategory(
            category_id="pacer",
            name="PACER Costs",
            description="PACER court record access fees",
            cost_types=[CostType.PACER_SEARCH, CostType.PACER_DOCUMENT, 
                       CostType.PACER_DOCKET, CostType.PACER_REPORT],
            is_billable=True,
            markup_percentage=Decimal('10.0'),  # 10% markup on PACER
            requires_approval=False,
            auto_allocate=True,
            default_allocation_method=AllocationMethod.DIRECT,
            color_code="#4A90E2",
            icon="court",
            sort_order=1
        )
        
        # Legal research
        categories["research"] = CostCategory(
            category_id="research",
            name="Legal Research",
            description="Westlaw, Lexis, and other research costs",
            cost_types=[CostType.WESTLAW_SEARCH, CostType.WESTLAW_DOCUMENT,
                       CostType.LEXIS_SEARCH, CostType.LEXIS_DOCUMENT],
            is_billable=True,
            markup_percentage=Decimal('15.0'),  # 15% markup on research
            requires_approval=True,
            approval_threshold=Decimal('100.0'),
            auto_allocate=False,
            default_allocation_method=AllocationMethod.TIME_BASED,
            color_code="#7ED321",
            icon="search",
            sort_order=2
        )
        
        # Court costs
        categories["court_costs"] = CostCategory(
            category_id="court_costs",
            name="Court Costs",
            description="Filing fees and court-related expenses",
            cost_types=[CostType.COURT_FILING_FEE, CostType.SERVICE_FEE],
            is_billable=True,
            markup_percentage=Decimal('0.0'),  # No markup on court fees
            requires_approval=False,
            auto_allocate=True,
            default_allocation_method=AllocationMethod.DIRECT,
            color_code="#BD10E0",
            icon="gavel",
            sort_order=3
        )
        
        # Expert services
        categories["experts"] = CostCategory(
            category_id="experts",
            name="Expert Services",
            description="Expert witnesses and professional services",
            cost_types=[CostType.EXPERT_WITNESS, CostType.COURT_REPORTER,
                       CostType.TRANSLATION, CostType.INVESTIGATION],
            is_billable=True,
            markup_percentage=Decimal('5.0'),  # 5% markup on expert services
            requires_approval=True,
            approval_threshold=Decimal('500.0'),
            auto_allocate=False,
            default_allocation_method=AllocationMethod.DIRECT,
            color_code="#F5A623",
            icon="users",
            sort_order=4
        )
        
        # Travel and expenses
        categories["travel"] = CostCategory(
            category_id="travel",
            name="Travel & Expenses",
            description="Travel, accommodation, and related expenses",
            cost_types=[CostType.TRAVEL_EXPENSE],
            is_billable=True,
            markup_percentage=Decimal('0.0'),
            requires_approval=True,
            approval_threshold=Decimal('200.0'),
            auto_allocate=False,
            default_allocation_method=AllocationMethod.PROPORTIONAL,
            color_code="#50E3C2",
            icon="plane",
            sort_order=5
        )
        
        # Office expenses
        categories["office"] = CostCategory(
            category_id="office",
            name="Office Expenses",
            description="Printing, copying, postage, and office supplies",
            cost_types=[CostType.PRINTING_COPYING, CostType.POSTAGE_DELIVERY],
            is_billable=True,
            markup_percentage=Decimal('20.0'),  # Higher markup for office expenses
            requires_approval=False,
            approval_threshold=Decimal('50.0'),
            auto_allocate=False,
            default_allocation_method=AllocationMethod.OVERHEAD,
            color_code="#D0021B",
            icon="printer",
            sort_order=6
        )
        
        # Miscellaneous
        categories["other"] = CostCategory(
            category_id="other",
            name="Other Costs",
            description="Miscellaneous costs and expenses",
            cost_types=[CostType.PROCESS_SERVER, CostType.OTHER],
            is_billable=True,
            markup_percentage=Decimal('10.0'),
            requires_approval=True,
            approval_threshold=Decimal('100.0'),
            auto_allocate=False,
            default_allocation_method=AllocationMethod.DIRECT,
            color_code="#9013FE",
            icon="more",
            sort_order=7
        )
        
        return categories
    
    async def record_cost(self,
                         cost_type: CostType,
                         amount: Decimal,
                         description: str,
                         client_id: Optional[str] = None,
                         case_number: Optional[str] = None,
                         incurred_by: Optional[str] = None,
                         cost_date: Optional[date] = None,
                         vendor: Optional[str] = None,
                         invoice_number: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> CostEntry:
        """
        Record a new cost entry.
        
        Args:
            cost_type: Type of cost being recorded
            amount: Cost amount
            description: Description of the cost
            client_id: Client to associate with cost
            case_number: Case number if applicable
            incurred_by: User who incurred the cost
            cost_date: Date cost was incurred
            vendor: Vendor/service provider
            invoice_number: Invoice or reference number
            metadata: Additional metadata
            
        Returns:
            CostEntry object
        """
        # Determine category
        category_id = self._get_category_for_cost_type(cost_type)
        category = self.cost_categories.get(category_id)
        
        # Calculate markup if applicable
        markup_amount = Decimal('0.0')
        if category and category.markup_percentage > 0:
            markup_amount = amount * (category.markup_percentage / Decimal('100'))
        
        # Create cost entry
        cost_entry = CostEntry(
            cost_id=generate_billing_id(),
            cost_type=cost_type,
            category_id=category_id,
            amount=amount,
            description=description,
            client_id=client_id,
            case_number=case_number,
            cost_date=cost_date or date.today(),
            incurred_by=incurred_by,
            vendor=vendor,
            invoice_number=invoice_number,
            markup_amount=markup_amount,
            is_billable=category.is_billable if category else True,
            allocation_method=category.default_allocation_method if category else AllocationMethod.DIRECT,
            metadata=metadata or {}
        )
        
        # Check if approval is required
        if category and category.requires_approval:
            if not category.approval_threshold or amount >= category.approval_threshold:
                cost_entry.status = BillingStatus.PENDING_REVIEW
        
        # Store cost entry
        await self._store_cost_entry(cost_entry)
        
        # Auto-allocate if configured
        if category and category.auto_allocate and client_id:
            await self._auto_allocate_cost(cost_entry)
        
        self.logger.info(
            f"Recorded {cost_type.value} cost: ${amount} "
            f"(+${markup_amount} markup) for {client_id or 'unassigned'}"
        )
        
        return cost_entry
    
    async def record_pacer_cost(self,
                              pacer_cost: PACERCost,
                              auto_allocate: bool = True) -> CostEntry:
        """
        Record a PACER cost in the general cost tracking system.
        
        Args:
            pacer_cost: PACERCost object from PACER billing manager
            auto_allocate: Whether to auto-allocate to client
            
        Returns:
            CostEntry object
        """
        # Map PACER cost type to general cost type
        cost_type_mapping = {
            "search": CostType.PACER_SEARCH,
            "document_view": CostType.PACER_DOCUMENT,
            "docket_report": CostType.PACER_DOCKET,
            "case_summary": CostType.PACER_REPORT
        }
        
        cost_type = cost_type_mapping.get(
            pacer_cost.pacer_cost_type.value,
            CostType.PACER_SEARCH
        )
        
        # Create description
        description = f"PACER {pacer_cost.pacer_cost_type.value.replace('_', ' ').title()}"
        if pacer_cost.case_number:
            description += f" - Case {pacer_cost.case_number}"
        if pacer_cost.document_id:
            description += f" - Doc {pacer_cost.document_id}"
        
        # Record cost
        cost_entry = await self.record_cost(
            cost_type=cost_type,
            amount=pacer_cost.final_cost,
            description=description,
            client_id=pacer_cost.client_id,
            case_number=pacer_cost.case_number,
            incurred_by=pacer_cost.requested_by,
            cost_date=pacer_cost.transaction_date.date(),
            vendor="PACER",
            invoice_number=pacer_cost.transaction_id,
            metadata={
                "pacer_cost_id": pacer_cost.cost_id,
                "pacer_account_id": pacer_cost.pacer_account_id,
                "court_id": pacer_cost.court_id,
                "quantity": pacer_cost.quantity,
                "unit_cost": float(pacer_cost.unit_cost),
                "exemption_applied": float(pacer_cost.exemption_applied),
                "request_purpose": pacer_cost.request_purpose
            }
        )
        
        return cost_entry
    
    async def get_costs_by_client(self,
                                client_id: str,
                                start_date: Optional[date] = None,
                                end_date: Optional[date] = None,
                                cost_types: Optional[List[CostType]] = None,
                                include_allocated: bool = True) -> List[CostEntry]:
        """
        Get costs associated with a specific client.
        
        Args:
            client_id: Client identifier
            start_date: Start date filter
            end_date: End date filter
            cost_types: Specific cost types to include
            include_allocated: Include costs allocated from other entries
            
        Returns:
            List of cost entries for the client
        """
        try:
            if self.api_client:
                response = await self.api_client.get(
                    f"/billing/costs/client/{client_id}",
                    params={
                        "start_date": start_date.isoformat() if start_date else None,
                        "end_date": end_date.isoformat() if end_date else None,
                        "cost_types": [ct.value for ct in cost_types] if cost_types else None,
                        "include_allocated": include_allocated
                    }
                )
                
                costs = []
                for cost_data in response.get("costs", []):
                    cost = self._dict_to_cost_entry(cost_data)
                    costs.append(cost)
                
                return costs
            else:
                # Filter from cached entries
                costs = []
                for cost_entry in self.cost_entries.values():
                    if not self._cost_matches_filters(
                        cost_entry, client_id, start_date, end_date, cost_types
                    ):
                        continue
                    costs.append(cost_entry)
                
                return costs
                
        except Exception as e:
            self.logger.error(f"Failed to get costs for client {client_id}: {e}")
            return []
    
    async def get_cost_summary(self,
                             start_date: Optional[date] = None,
                             end_date: Optional[date] = None,
                             group_by: str = "category") -> Dict[str, Any]:
        """
        Get cost summary with grouping.
        
        Args:
            start_date: Start date for summary
            end_date: End date for summary
            group_by: Grouping method (category, type, client, month)
            
        Returns:
            Cost summary dictionary
        """
        try:
            if self.api_client:
                response = await self.api_client.get(
                    "/billing/costs/summary",
                    params={
                        "start_date": start_date.isoformat() if start_date else None,
                        "end_date": end_date.isoformat() if end_date else None,
                        "group_by": group_by
                    }
                )
                return response
            else:
                # Calculate summary from cached data
                return self._calculate_cost_summary(start_date, end_date, group_by)
                
        except Exception as e:
            self.logger.error(f"Failed to get cost summary: {e}")
            return {}
    
    async def approve_cost(self,
                         cost_id: str,
                         approved_by: str,
                         notes: Optional[str] = None) -> bool:
        """
        Approve a pending cost entry.
        
        Args:
            cost_id: Cost entry ID to approve
            approved_by: User approving the cost
            notes: Optional approval notes
            
        Returns:
            True if approved successfully
        """
        try:
            cost_entry = await self._get_cost_entry(cost_id)
            if not cost_entry:
                return False
            
            cost_entry.status = BillingStatus.APPROVED
            cost_entry.approved_by = approved_by
            cost_entry.approved_at = datetime.utcnow()
            if notes:
                cost_entry.notes = notes
            
            await self._update_cost_entry(cost_entry)
            
            self.logger.info(f"Approved cost {cost_id} by {approved_by}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to approve cost {cost_id}: {e}")
            return False
    
    async def allocate_cost_to_clients(self,
                                     cost_id: str,
                                     client_allocations: Dict[str, Decimal],
                                     allocated_by: Optional[str] = None) -> List[CostAllocation]:
        """
        Manually allocate cost to specific clients.
        
        Args:
            cost_id: Cost entry ID
            client_allocations: Client ID -> amount mappings
            allocated_by: User performing allocation
            
        Returns:
            List of cost allocations created
        """
        cost_entry = await self._get_cost_entry(cost_id)
        if not cost_entry:
            return []
        
        allocations = []
        total_allocated = Decimal('0.0')
        
        for client_id, amount in client_allocations.items():
            if amount <= 0:
                continue
            
            percentage = (amount / cost_entry.total_amount) * Decimal('100')
            
            allocation = CostAllocation(
                allocation_id=generate_billing_id(),
                cost_id=cost_id,
                client_id=client_id,
                matter_number=None,  # Could be enhanced to include matter
                allocated_amount=amount,
                allocation_percentage=percentage,
                allocation_method=AllocationMethod.CUSTOM,
                allocation_basis="manual",
                allocated_by=allocated_by
            )
            
            allocations.append(allocation)
            total_allocated += amount
        
        # Update cost entry with allocations
        cost_entry.allocated_clients = client_allocations.copy()
        cost_entry.allocation_method = AllocationMethod.CUSTOM
        
        if abs(total_allocated - cost_entry.total_amount) < Decimal('0.01'):
            cost_entry.status = BillingStatus.APPROVED
        
        # Store allocations
        await self._store_cost_allocations(cost_id, allocations)
        await self._update_cost_entry(cost_entry)
        
        self.logger.info(f"Allocated cost {cost_id} to {len(allocations)} clients")
        
        return allocations
    
    def _get_category_for_cost_type(self, cost_type: CostType) -> Optional[str]:
        """Get category ID for cost type."""
        for category_id, category in self.cost_categories.items():
            if cost_type in category.cost_types:
                return category_id
        return None
    
    async def _store_cost_entry(self, cost_entry: CostEntry):
        """Store cost entry in database/cache."""
        try:
            if self.api_client:
                await self.api_client.post(
                    "/billing/costs",
                    json=self._cost_entry_to_dict(cost_entry)
                )
            else:
                # Store in cache
                self.cost_entries[cost_entry.cost_id] = cost_entry
                
        except Exception as e:
            self.logger.error(f"Failed to store cost entry {cost_entry.cost_id}: {e}")
    
    async def _auto_allocate_cost(self, cost_entry: CostEntry):
        """Automatically allocate cost to client if configured."""
        if cost_entry.client_id and cost_entry.allocation_method == AllocationMethod.DIRECT:
            allocation = CostAllocation(
                allocation_id=generate_billing_id(),
                cost_id=cost_entry.cost_id,
                client_id=cost_entry.client_id,
                matter_number=cost_entry.matter_number,
                allocated_amount=cost_entry.total_amount,
                allocation_percentage=Decimal('100.0'),
                allocation_method=AllocationMethod.DIRECT,
                allocation_basis="auto"
            )
            
            await self._store_cost_allocations(cost_entry.cost_id, [allocation])
            
            # Update cost entry
            cost_entry.allocated_clients[cost_entry.client_id] = cost_entry.total_amount
    
    async def _get_cost_entry(self, cost_id: str) -> Optional[CostEntry]:
        """Get cost entry by ID."""
        if cost_id in self.cost_entries:
            return self.cost_entries[cost_id]
        
        if self.api_client:
            try:
                response = await self.api_client.get(f"/billing/costs/{cost_id}")
                if response.get("cost"):
                    return self._dict_to_cost_entry(response["cost"])
            except Exception as e:
                self.logger.error(f"Failed to get cost entry {cost_id}: {e}")
        
        return None
    
    async def _update_cost_entry(self, cost_entry: CostEntry):
        """Update cost entry in storage."""
        cost_entry.updated_at = datetime.utcnow()
        
        try:
            if self.api_client:
                await self.api_client.put(
                    f"/billing/costs/{cost_entry.cost_id}",
                    json=self._cost_entry_to_dict(cost_entry)
                )
            else:
                self.cost_entries[cost_entry.cost_id] = cost_entry
                
        except Exception as e:
            self.logger.error(f"Failed to update cost entry {cost_entry.cost_id}: {e}")
    
    async def _store_cost_allocations(self, cost_id: str, allocations: List[CostAllocation]):
        """Store cost allocations."""
        try:
            if self.api_client:
                allocation_data = [self._cost_allocation_to_dict(alloc) for alloc in allocations]
                await self.api_client.post(
                    f"/billing/costs/{cost_id}/allocations",
                    json={"allocations": allocation_data}
                )
            else:
                self.cost_allocations[cost_id] = allocations
                
        except Exception as e:
            self.logger.error(f"Failed to store cost allocations for {cost_id}: {e}")
    
    def _cost_matches_filters(self,
                            cost_entry: CostEntry,
                            client_id: Optional[str],
                            start_date: Optional[date],
                            end_date: Optional[date],
                            cost_types: Optional[List[CostType]]) -> bool:
        """Check if cost entry matches filter criteria."""
        # Client filter
        if client_id and cost_entry.client_id != client_id:
            # Check if client is in allocated clients
            if client_id not in cost_entry.allocated_clients:
                return False
        
        # Date filters
        if start_date and cost_entry.cost_date < start_date:
            return False
        if end_date and cost_entry.cost_date > end_date:
            return False
        
        # Cost type filter
        if cost_types and cost_entry.cost_type not in cost_types:
            return False
        
        return True
    
    def _calculate_cost_summary(self,
                              start_date: Optional[date],
                              end_date: Optional[date],
                              group_by: str) -> Dict[str, Any]:
        """Calculate cost summary from cached data."""
        summary = {
            "total_amount": Decimal('0.0'),
            "total_costs": 0,
            "groups": {}
        }
        
        for cost_entry in self.cost_entries.values():
            # Apply date filters
            if start_date and cost_entry.cost_date < start_date:
                continue
            if end_date and cost_entry.cost_date > end_date:
                continue
            
            # Determine group key
            if group_by == "category":
                group_key = cost_entry.category_id or "uncategorized"
            elif group_by == "type":
                group_key = cost_entry.cost_type.value
            elif group_by == "client":
                group_key = cost_entry.client_id or "unassigned"
            elif group_by == "month":
                group_key = cost_entry.cost_date.strftime("%Y-%m")
            else:
                group_key = "all"
            
            # Update summary
            if group_key not in summary["groups"]:
                summary["groups"][group_key] = {
                    "total_amount": Decimal('0.0'),
                    "count": 0
                }
            
            summary["groups"][group_key]["total_amount"] += cost_entry.total_amount
            summary["groups"][group_key]["count"] += 1
            summary["total_amount"] += cost_entry.total_amount
            summary["total_costs"] += 1
        
        return summary
    
    def _cost_entry_to_dict(self, cost_entry: CostEntry) -> Dict[str, Any]:
        """Convert CostEntry to dictionary."""
        return {
            "cost_id": cost_entry.cost_id,
            "cost_type": cost_entry.cost_type.value,
            "category_id": cost_entry.category_id,
            "amount": float(cost_entry.amount),
            "currency": cost_entry.currency,
            "description": cost_entry.description,
            "client_id": cost_entry.client_id,
            "matter_number": cost_entry.matter_number,
            "case_number": cost_entry.case_number,
            "project_code": cost_entry.project_code,
            "vendor": cost_entry.vendor,
            "invoice_number": cost_entry.invoice_number,
            "reference_number": cost_entry.reference_number,
            "cost_date": cost_entry.cost_date.isoformat(),
            "due_date": cost_entry.due_date.isoformat() if cost_entry.due_date else None,
            "paid_date": cost_entry.paid_date.isoformat() if cost_entry.paid_date else None,
            "incurred_by": cost_entry.incurred_by,
            "approved_by": cost_entry.approved_by,
            "approved_at": cost_entry.approved_at.isoformat() if cost_entry.approved_at else None,
            "allocation_method": cost_entry.allocation_method.value,
            "allocation_percentage": float(cost_entry.allocation_percentage),
            "allocated_clients": {k: float(v) for k, v in cost_entry.allocated_clients.items()},
            "status": cost_entry.status.value,
            "is_billable": cost_entry.is_billable,
            "markup_amount": float(cost_entry.markup_amount),
            "total_amount": float(cost_entry.total_amount),
            "created_at": cost_entry.created_at.isoformat(),
            "updated_at": cost_entry.updated_at.isoformat(),
            "created_by": cost_entry.created_by,
            "tags": cost_entry.tags,
            "attachments": cost_entry.attachments,
            "metadata": cost_entry.metadata,
            "notes": cost_entry.notes
        }
    
    def _cost_allocation_to_dict(self, allocation: CostAllocation) -> Dict[str, Any]:
        """Convert CostAllocation to dictionary."""
        return {
            "allocation_id": allocation.allocation_id,
            "cost_id": allocation.cost_id,
            "client_id": allocation.client_id,
            "matter_number": allocation.matter_number,
            "allocated_amount": float(allocation.allocated_amount),
            "allocation_percentage": float(allocation.allocation_percentage),
            "allocation_method": allocation.allocation_method.value,
            "allocation_basis": allocation.allocation_basis,
            "status": allocation.status.value,
            "invoice_id": allocation.invoice_id,
            "billed_at": allocation.billed_at.isoformat() if allocation.billed_at else None,
            "allocated_at": allocation.allocated_at.isoformat(),
            "allocated_by": allocation.allocated_by,
            "notes": allocation.notes
        }
    
    def _dict_to_cost_entry(self, data: Dict[str, Any]) -> CostEntry:
        """Convert dictionary to CostEntry."""
        return CostEntry(
            cost_id=data["cost_id"],
            cost_type=CostType(data["cost_type"]),
            category_id=data.get("category_id"),
            amount=Decimal(str(data["amount"])),
            currency=data.get("currency", "USD"),
            description=data.get("description", ""),
            client_id=data.get("client_id"),
            matter_number=data.get("matter_number"),
            case_number=data.get("case_number"),
            project_code=data.get("project_code"),
            vendor=data.get("vendor"),
            invoice_number=data.get("invoice_number"),
            reference_number=data.get("reference_number"),
            cost_date=date.fromisoformat(data["cost_date"]) if data.get("cost_date") else date.today(),
            incurred_by=data.get("incurred_by"),
            allocation_method=AllocationMethod(data.get("allocation_method", "direct")),
            status=BillingStatus(data.get("status", "draft")),
            is_billable=data.get("is_billable", True),
            markup_amount=Decimal(str(data.get("markup_amount", 0))),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            notes=data.get("notes")
        )