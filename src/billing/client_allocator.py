"""
Client cost allocation system for legal billing.

Handles allocation of costs to clients based on configurable rules,
time tracking, case associations, and custom allocation methods.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
from collections import defaultdict

from ..shared.utils import BaseAPIClient
from .models import (
    CostType, AllocationMethod, BillingAccount, BillingStatus,
    generate_billing_id, get_default_allocation_method
)


@dataclass
class AllocationRule:
    """Rule for allocating costs to clients."""
    rule_id: str
    name: str
    description: str
    priority: int  # Higher number = higher priority
    
    # Rule conditions
    cost_types: List[CostType] = field(default_factory=list)
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    case_numbers: List[str] = field(default_factory=list)
    matter_codes: List[str] = field(default_factory=list)
    users: List[str] = field(default_factory=list)
    departments: List[str] = field(default_factory=list)
    
    # Allocation configuration
    allocation_method: AllocationMethod = AllocationMethod.DIRECT
    default_client: Optional[str] = None
    client_percentages: Dict[str, Decimal] = field(default_factory=dict)
    
    # Time-based allocation settings
    time_period_days: int = 30
    billable_only: bool = True
    
    # Rule metadata
    effective_from: date = field(default_factory=date.today)
    effective_to: Optional[date] = None
    is_active: bool = True
    created_by: Optional[str] = None
    
    def matches_cost(self, cost_entry: Dict[str, Any]) -> bool:
        """Check if this rule applies to the cost entry."""
        # Check cost type
        if self.cost_types and cost_entry.get("cost_type") not in self.cost_types:
            return False
        
        # Check amount range
        amount = Decimal(str(cost_entry.get("amount", 0)))
        if self.amount_min and amount < self.amount_min:
            return False
        if self.amount_max and amount > self.amount_max:
            return False
        
        # Check case numbers
        if self.case_numbers and cost_entry.get("case_number") not in self.case_numbers:
            return False
        
        # Check matter codes
        if self.matter_codes and cost_entry.get("matter_code") not in self.matter_codes:
            return False
        
        # Check users
        if self.users and cost_entry.get("user") not in self.users:
            return False
        
        # Check departments
        if self.departments and cost_entry.get("department") not in self.departments:
            return False
        
        return True


@dataclass
class AllocationResult:
    """Result of cost allocation to clients."""
    allocation_id: str
    original_cost_id: str
    total_amount: Decimal
    
    # Client allocations
    client_allocations: Dict[str, Decimal] = field(default_factory=dict)
    allocation_percentages: Dict[str, Decimal] = field(default_factory=dict)
    
    # Allocation details
    method_used: AllocationMethod = AllocationMethod.DIRECT
    rules_applied: List[str] = field(default_factory=list)
    allocation_basis: Optional[str] = None  # time, value, equal, custom
    
    # Metadata
    allocated_at: datetime = field(default_factory=datetime.utcnow)
    allocated_by: Optional[str] = None
    notes: Optional[str] = None
    
    # Validation
    is_fully_allocated: bool = False
    allocation_warnings: List[str] = field(default_factory=list)
    
    @property
    def allocated_amount(self) -> Decimal:
        """Total amount that has been allocated."""
        return sum(self.client_allocations.values())
    
    @property
    def unallocated_amount(self) -> Decimal:
        """Amount that remains unallocated."""
        return self.total_amount - self.allocated_amount
    
    @property
    def total_percentage(self) -> Decimal:
        """Total allocation percentage."""
        return sum(self.allocation_percentages.values())


@dataclass
class TimeAllocationData:
    """Time-based allocation data for a client."""
    client_id: str
    matter_number: Optional[str]
    total_hours: Decimal
    billable_hours: Decimal
    hourly_rate: Optional[Decimal] = None
    total_value: Optional[Decimal] = None


class ClientAllocator:
    """Advanced client cost allocation system."""
    
    def __init__(self, api_client: Optional[BaseAPIClient] = None):
        self.api_client = api_client
        self.allocation_rules: List[AllocationRule] = []
        self.client_accounts: Dict[str, BillingAccount] = {}
        self.allocation_cache: Dict[str, AllocationResult] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default allocation rules."""
        # Direct PACER cost allocation
        self.allocation_rules.append(AllocationRule(
            rule_id="pacer_direct",
            name="Direct PACER Cost Allocation",
            description="Allocate PACER costs directly to specified client",
            priority=100,
            cost_types=[CostType.PACER_SEARCH, CostType.PACER_DOCUMENT, CostType.PACER_DOCKET],
            allocation_method=AllocationMethod.DIRECT
        ))
        
        # Court filing fees - direct allocation
        self.allocation_rules.append(AllocationRule(
            rule_id="court_fees_direct",
            name="Direct Court Fee Allocation", 
            description="Allocate court filing fees directly to case client",
            priority=90,
            cost_types=[CostType.COURT_FILING_FEE],
            allocation_method=AllocationMethod.DIRECT
        ))
        
        # Research costs - time-based allocation
        self.allocation_rules.append(AllocationRule(
            rule_id="research_time_based",
            name="Time-Based Research Allocation",
            description="Allocate research costs based on attorney time",
            priority=70,
            cost_types=[CostType.WESTLAW_SEARCH, CostType.WESTLAW_DOCUMENT, 
                       CostType.LEXIS_SEARCH, CostType.LEXIS_DOCUMENT],
            allocation_method=AllocationMethod.TIME_BASED,
            time_period_days=30,
            billable_only=True
        ))
        
        # Travel expenses - proportional allocation
        self.allocation_rules.append(AllocationRule(
            rule_id="travel_proportional", 
            name="Proportional Travel Allocation",
            description="Allocate travel costs proportionally by case value",
            priority=60,
            cost_types=[CostType.TRAVEL_EXPENSE],
            allocation_method=AllocationMethod.PROPORTIONAL
        ))
        
        # Office expenses - overhead (not billable)
        self.allocation_rules.append(AllocationRule(
            rule_id="office_overhead",
            name="Office Overhead",
            description="Office expenses are firm overhead",
            priority=50,
            cost_types=[CostType.PRINTING_COPYING, CostType.POSTAGE_DELIVERY],
            allocation_method=AllocationMethod.OVERHEAD
        ))
    
    async def allocate_cost(self, 
                          cost_entry: Dict[str, Any],
                          force_method: Optional[AllocationMethod] = None,
                          custom_allocations: Optional[Dict[str, Decimal]] = None) -> AllocationResult:
        """
        Allocate a cost entry to clients based on rules.
        
        Args:
            cost_entry: Cost information to allocate
            force_method: Force specific allocation method
            custom_allocations: Custom client allocations
            
        Returns:
            AllocationResult with client allocations
        """
        cost_id = cost_entry.get("cost_id", generate_billing_id())
        amount = Decimal(str(cost_entry.get("amount", 0)))
        
        # Initialize result
        result = AllocationResult(
            allocation_id=generate_billing_id(),
            original_cost_id=cost_id,
            total_amount=amount
        )
        
        try:
            # Use custom allocations if provided
            if custom_allocations:
                result.client_allocations = custom_allocations.copy()
                result.method_used = AllocationMethod.CUSTOM
                result.allocation_basis = "custom"
                
                # Calculate percentages
                for client_id, allocation_amount in custom_allocations.items():
                    percentage = (allocation_amount / amount) * Decimal('100')
                    result.allocation_percentages[client_id] = percentage
                
                result.is_fully_allocated = abs(result.unallocated_amount) < Decimal('0.01')
                return result
            
            # Find applicable rules
            applicable_rules = self._find_applicable_rules(cost_entry)
            
            if not applicable_rules:
                # No rules found, try default allocation
                await self._apply_default_allocation(cost_entry, result)
            else:
                # Apply the highest priority rule
                best_rule = max(applicable_rules, key=lambda r: r.priority)
                await self._apply_allocation_rule(cost_entry, best_rule, result)
                result.rules_applied.append(best_rule.rule_id)
            
            # Override with forced method if specified
            if force_method:
                await self._apply_forced_allocation(cost_entry, force_method, result)
            
            # Validate allocation
            self._validate_allocation(result)
            
            # Cache result
            self.allocation_cache[result.allocation_id] = result
            
            self.logger.info(
                f"Allocated cost {cost_id}: ${amount} -> "
                f"{len(result.client_allocations)} clients using {result.method_used.value}"
            )
            
        except Exception as e:
            self.logger.error(f"Cost allocation failed for {cost_id}: {e}")
            result.allocation_warnings.append(f"Allocation failed: {str(e)}")
        
        return result
    
    async def allocate_batch(self,
                           cost_entries: List[Dict[str, Any]],
                           progress_callback: Optional[callable] = None) -> List[AllocationResult]:
        """
        Allocate multiple cost entries in batch.
        
        Args:
            cost_entries: List of cost entries to allocate
            progress_callback: Optional progress callback
            
        Returns:
            List of allocation results
        """
        self.logger.info(f"Starting batch allocation of {len(cost_entries)} cost entries")
        
        results = []
        for i, cost_entry in enumerate(cost_entries):
            try:
                result = await self.allocate_cost(cost_entry)
                results.append(result)
                
                if progress_callback:
                    await progress_callback(
                        cost_entry.get("cost_id", f"cost_{i}"),
                        "allocated",
                        {"clients": len(result.client_allocations)}
                    )
                    
            except Exception as e:
                self.logger.error(f"Failed to allocate cost entry {i}: {e}")
                # Create failed result
                failed_result = AllocationResult(
                    allocation_id=generate_billing_id(),
                    original_cost_id=cost_entry.get("cost_id", f"cost_{i}"),
                    total_amount=Decimal(str(cost_entry.get("amount", 0)))
                )
                failed_result.allocation_warnings.append(f"Allocation failed: {str(e)}")
                results.append(failed_result)
        
        successful = sum(1 for r in results if r.is_fully_allocated)
        self.logger.info(f"Batch allocation completed: {successful}/{len(cost_entries)} successful")
        
        return results
    
    def _find_applicable_rules(self, cost_entry: Dict[str, Any]) -> List[AllocationRule]:
        """Find allocation rules that apply to the cost entry."""
        applicable_rules = []
        
        for rule in self.allocation_rules:
            if not rule.is_active:
                continue
            
            # Check effective date
            cost_date = cost_entry.get("cost_date")
            if cost_date:
                if isinstance(cost_date, str):
                    cost_date = datetime.fromisoformat(cost_date).date()
                
                if cost_date < rule.effective_from:
                    continue
                
                if rule.effective_to and cost_date > rule.effective_to:
                    continue
            
            # Check if rule matches cost
            if rule.matches_cost(cost_entry):
                applicable_rules.append(rule)
        
        return applicable_rules
    
    async def _apply_allocation_rule(self,
                                   cost_entry: Dict[str, Any],
                                   rule: AllocationRule,
                                   result: AllocationResult):
        """Apply specific allocation rule to cost entry."""
        result.method_used = rule.allocation_method
        
        if rule.allocation_method == AllocationMethod.DIRECT:
            await self._apply_direct_allocation(cost_entry, rule, result)
        elif rule.allocation_method == AllocationMethod.PROPORTIONAL:
            await self._apply_proportional_allocation(cost_entry, rule, result)
        elif rule.allocation_method == AllocationMethod.EQUAL_SPLIT:
            await self._apply_equal_split_allocation(cost_entry, rule, result)
        elif rule.allocation_method == AllocationMethod.TIME_BASED:
            await self._apply_time_based_allocation(cost_entry, rule, result)
        elif rule.allocation_method == AllocationMethod.OVERHEAD:
            await self._apply_overhead_allocation(cost_entry, rule, result)
        else:
            await self._apply_custom_allocation(cost_entry, rule, result)
    
    async def _apply_direct_allocation(self,
                                     cost_entry: Dict[str, Any],
                                     rule: AllocationRule,
                                     result: AllocationResult):
        """Apply direct allocation to specified client."""
        client_id = cost_entry.get("client_id") or rule.default_client
        
        if client_id:
            result.client_allocations[client_id] = result.total_amount
            result.allocation_percentages[client_id] = Decimal('100.0')
            result.allocation_basis = "direct"
            result.is_fully_allocated = True
        else:
            result.allocation_warnings.append("No client specified for direct allocation")
    
    async def _apply_proportional_allocation(self,
                                           cost_entry: Dict[str, Any],
                                           rule: AllocationRule,
                                           result: AllocationResult):
        """Apply proportional allocation based on case values or other metrics."""
        # Get client case values for proportional allocation
        case_values = await self._get_client_case_values(cost_entry)
        
        if case_values:
            total_value = sum(case_values.values())
            
            for client_id, case_value in case_values.items():
                percentage = (case_value / total_value) * Decimal('100')
                allocation_amount = (result.total_amount * percentage) / Decimal('100')
                
                result.client_allocations[client_id] = allocation_amount
                result.allocation_percentages[client_id] = percentage
            
            result.allocation_basis = "case_value"
            result.is_fully_allocated = True
        else:
            result.allocation_warnings.append("No case values available for proportional allocation")
    
    async def _apply_equal_split_allocation(self,
                                          cost_entry: Dict[str, Any],
                                          rule: AllocationRule,
                                          result: AllocationResult):
        """Apply equal split allocation among relevant clients."""
        clients = await self._get_relevant_clients(cost_entry)
        
        if clients:
            equal_percentage = Decimal('100.0') / Decimal(str(len(clients)))
            equal_amount = result.total_amount / Decimal(str(len(clients)))
            
            for client_id in clients:
                result.client_allocations[client_id] = equal_amount
                result.allocation_percentages[client_id] = equal_percentage
            
            result.allocation_basis = "equal_split"
            result.is_fully_allocated = True
        else:
            result.allocation_warnings.append("No clients found for equal split allocation")
    
    async def _apply_time_based_allocation(self,
                                         cost_entry: Dict[str, Any],
                                         rule: AllocationRule,
                                         result: AllocationResult):
        """Apply time-based allocation using attorney time tracking."""
        time_data = await self._get_time_allocation_data(cost_entry, rule)
        
        if time_data:
            total_hours = sum(data.billable_hours if rule.billable_only else data.total_hours
                            for data in time_data)
            
            if total_hours > 0:
                for data in time_data:
                    hours = data.billable_hours if rule.billable_only else data.total_hours
                    percentage = (hours / total_hours) * Decimal('100')
                    allocation_amount = (result.total_amount * percentage) / Decimal('100')
                    
                    result.client_allocations[data.client_id] = allocation_amount
                    result.allocation_percentages[data.client_id] = percentage
                
                result.allocation_basis = "billable_time" if rule.billable_only else "total_time"
                result.is_fully_allocated = True
            else:
                result.allocation_warnings.append("No time entries found for time-based allocation")
        else:
            result.allocation_warnings.append("No time data available for time-based allocation")
    
    async def _apply_overhead_allocation(self,
                                       cost_entry: Dict[str, Any],
                                       rule: AllocationRule,
                                       result: AllocationResult):
        """Mark cost as overhead (not billable to clients)."""
        result.allocation_basis = "overhead"
        result.is_fully_allocated = True
        result.notes = "Cost treated as firm overhead, not allocated to clients"
    
    async def _apply_custom_allocation(self,
                                     cost_entry: Dict[str, Any],
                                     rule: AllocationRule,
                                     result: AllocationResult):
        """Apply custom allocation based on rule configuration."""
        if rule.client_percentages:
            for client_id, percentage in rule.client_percentages.items():
                allocation_amount = (result.total_amount * percentage) / Decimal('100')
                result.client_allocations[client_id] = allocation_amount
                result.allocation_percentages[client_id] = percentage
            
            result.allocation_basis = "custom_percentages"
            result.is_fully_allocated = abs(result.total_percentage - Decimal('100.0')) < Decimal('0.01')
        else:
            result.allocation_warnings.append("No custom allocation percentages configured")
    
    async def _apply_default_allocation(self,
                                      cost_entry: Dict[str, Any],
                                      result: AllocationResult):
        """Apply default allocation when no rules match."""
        cost_type = cost_entry.get("cost_type")
        default_method = get_default_allocation_method(CostType(cost_type)) if cost_type else AllocationMethod.DIRECT
        
        # Create temporary rule with default method
        default_rule = AllocationRule(
            rule_id="default",
            name="Default Allocation",
            description="Default allocation method",
            priority=0,
            allocation_method=default_method
        )
        
        await self._apply_allocation_rule(cost_entry, default_rule, result)
    
    async def _apply_forced_allocation(self,
                                     cost_entry: Dict[str, Any],
                                     method: AllocationMethod,
                                     result: AllocationResult):
        """Apply forced allocation method, overriding rule-based allocation."""
        # Clear existing allocations
        result.client_allocations.clear()
        result.allocation_percentages.clear()
        
        # Create temporary rule with forced method
        forced_rule = AllocationRule(
            rule_id="forced",
            name="Forced Allocation",
            description="Manually forced allocation method",
            priority=1000,
            allocation_method=method
        )
        
        await self._apply_allocation_rule(cost_entry, forced_rule, result)
        result.notes = f"Allocation method forced to {method.value}"
    
    async def _get_client_case_values(self, cost_entry: Dict[str, Any]) -> Dict[str, Decimal]:
        """Get case values for proportional allocation."""
        try:
            if self.api_client:
                response = await self.api_client.get(
                    "/billing/case-values",
                    params={"related_to": cost_entry.get("case_number")}
                )
                
                case_values = {}
                for case_data in response.get("cases", []):
                    client_id = case_data.get("client_id")
                    case_value = Decimal(str(case_data.get("case_value", 0)))
                    if client_id and case_value > 0:
                        case_values[client_id] = case_value
                
                return case_values
            else:
                # Return mock data for testing
                return {
                    "client_1": Decimal('100000'),
                    "client_2": Decimal('50000')
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get case values: {e}")
            return {}
    
    async def _get_relevant_clients(self, cost_entry: Dict[str, Any]) -> List[str]:
        """Get list of clients relevant to the cost entry."""
        try:
            if self.api_client:
                response = await self.api_client.get(
                    "/billing/relevant-clients",
                    params={
                        "case_number": cost_entry.get("case_number"),
                        "matter_code": cost_entry.get("matter_code"),
                        "user": cost_entry.get("user")
                    }
                )
                
                return response.get("clients", [])
            else:
                # Return mock data for testing
                return ["client_1", "client_2", "client_3"]
                
        except Exception as e:
            self.logger.error(f"Failed to get relevant clients: {e}")
            return []
    
    async def _get_time_allocation_data(self,
                                      cost_entry: Dict[str, Any],
                                      rule: AllocationRule) -> List[TimeAllocationData]:
        """Get time allocation data for time-based allocation."""
        try:
            if self.api_client:
                end_date = cost_entry.get("cost_date", datetime.utcnow().date())
                start_date = end_date - timedelta(days=rule.time_period_days)
                
                response = await self.api_client.get(
                    "/billing/time-allocations",
                    params={
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "user": cost_entry.get("user"),
                        "case_number": cost_entry.get("case_number")
                    }
                )
                
                time_data = []
                for entry in response.get("time_entries", []):
                    time_data.append(TimeAllocationData(
                        client_id=entry["client_id"],
                        matter_number=entry.get("matter_number"),
                        total_hours=Decimal(str(entry["total_hours"])),
                        billable_hours=Decimal(str(entry["billable_hours"])),
                        hourly_rate=Decimal(str(entry["hourly_rate"])) if entry.get("hourly_rate") else None
                    ))
                
                return time_data
            else:
                # Return mock data for testing
                return [
                    TimeAllocationData(
                        client_id="client_1",
                        total_hours=Decimal('10.5'),
                        billable_hours=Decimal('8.0')
                    ),
                    TimeAllocationData(
                        client_id="client_2", 
                        total_hours=Decimal('5.0'),
                        billable_hours=Decimal('4.5')
                    )
                ]
                
        except Exception as e:
            self.logger.error(f"Failed to get time allocation data: {e}")
            return []
    
    def _validate_allocation(self, result: AllocationResult):
        """Validate allocation result and add warnings if needed."""
        # Check if fully allocated
        if abs(result.unallocated_amount) > Decimal('0.01'):
            result.allocation_warnings.append(
                f"Allocation incomplete: ${result.unallocated_amount} unallocated"
            )
            result.is_fully_allocated = False
        
        # Check percentage total
        if abs(result.total_percentage - Decimal('100.0')) > Decimal('0.01') and result.client_allocations:
            result.allocation_warnings.append(
                f"Percentage total: {result.total_percentage}% (should be 100%)"
            )
        
        # Check for negative allocations
        for client_id, amount in result.client_allocations.items():
            if amount < 0:
                result.allocation_warnings.append(
                    f"Negative allocation for {client_id}: ${amount}"
                )
        
        # Validate client exists
        for client_id in result.client_allocations.keys():
            if client_id not in self.client_accounts:
                result.allocation_warnings.append(
                    f"Unknown client ID: {client_id}"
                )