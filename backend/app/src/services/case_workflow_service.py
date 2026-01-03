"""
Case Workflow Service
Handles timeline workflow engine, critical path tracking, and business logic
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ============================================================================
# TIMELINE & WORKFLOW ENGINE
# ============================================================================

class TimelineWorkflowEngine:
    """
    Manages case timelines, dependencies, and critical path
    """

    @staticmethod
    def calculate_critical_path(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate the critical path through timeline events
        Returns events on the critical path with slack time
        """
        if not events:
            return []

        # Build dependency graph
        event_map = {e['id']: e for e in events}

        # Calculate earliest start times (forward pass)
        earliest_start = {}
        for event in events:
            event_id = event['id']
            blocked_by = event.get('blocked_by_event_ids', [])

            if not blocked_by:
                earliest_start[event_id] = event['event_date']
            else:
                # Start after all blocking events complete
                max_predecessor_end = max(
                    [event_map[dep]['event_date'] for dep in blocked_by if dep in event_map],
                    default=event['event_date']
                )
                earliest_start[event_id] = max(event['event_date'], max_predecessor_end)

        # Calculate latest start times (backward pass)
        latest_start = {}
        sorted_events = sorted(events, key=lambda e: e['event_date'], reverse=True)

        for event in sorted_events:
            event_id = event['id']
            blocks = event.get('blocks_event_ids', [])

            if not blocks:
                latest_start[event_id] = earliest_start[event_id]
            else:
                # Must complete before earliest successor starts
                min_successor_start = min(
                    [latest_start.get(dep, earliest_start[dep]) for dep in blocks if dep in event_map],
                    default=earliest_start[event_id]
                )
                latest_start[event_id] = min_successor_start

        # Identify critical path (events with zero slack)
        critical_path_events = []
        for event in events:
            event_id = event['id']
            slack = (latest_start[event_id] - earliest_start[event_id]).days if isinstance(earliest_start[event_id], datetime) else 0

            event_analysis = {
                **event,
                'earliest_start': earliest_start[event_id],
                'latest_start': latest_start[event_id],
                'slack_days': slack,
                'is_critical': slack == 0
            }

            if slack == 0:
                critical_path_events.append(event_analysis)

        return sorted(critical_path_events, key=lambda e: e['event_date'])

    @staticmethod
    def identify_deadline_cascades(event: Dict[str, Any], all_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify which events will be affected if this event's deadline changes
        """
        event_id = event['id']
        affected_events = []

        # Build dependency chain
        def find_dependent_events(current_id: str, chain: List[str] = []):
            for evt in all_events:
                blocked_by = evt.get('blocked_by_event_ids', [])
                if current_id in blocked_by and evt['id'] not in chain:
                    new_chain = chain + [evt['id']]
                    affected_events.append({
                        'event': evt,
                        'dependency_chain': new_chain,
                        'cascade_level': len(new_chain)
                    })
                    # Recursively find dependencies
                    find_dependent_events(evt['id'], new_chain)

        find_dependent_events(event_id)

        return sorted(affected_events, key=lambda e: e['cascade_level'])

    @staticmethod
    def suggest_buffer_time(event_type: str, complexity: str = "medium") -> int:
        """
        Suggest buffer time in days based on event type and complexity
        """
        base_buffers = {
            'filing': 3,
            'hearing': 7,
            'deadline': 5,
            'meeting': 2,
            'motion': 7,
            'objection': 5,
            'auction': 14,
            'confirmation': 10,
            'discharge': 14,
            'other': 3
        }

        complexity_multipliers = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.5,
            'very_high': 2.0
        }

        base = base_buffers.get(event_type.lower(), 3)
        multiplier = complexity_multipliers.get(complexity.lower(), 1.0)

        return int(base * multiplier)

    @staticmethod
    def check_parallel_opportunities(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify events that can be executed in parallel
        """
        parallel_groups = []

        # Find events without dependencies that overlap in time
        independent_events = [e for e in events if not e.get('blocked_by_event_ids')]

        # Group by time proximity (within 7 days)
        for event in independent_events:
            event_date = event['event_date']

            # Find other events within 7 days
            nearby_events = [
                e for e in independent_events
                if e['id'] != event['id'] and
                abs((e['event_date'] - event_date).days) <= 7
            ]

            if nearby_events:
                parallel_groups.append({
                    'anchor_event': event,
                    'parallel_events': nearby_events,
                    'potential_time_savings': len(nearby_events) * 2  # days saved
                })

        return parallel_groups


# ============================================================================
# DEADLINE MANAGER
# ============================================================================

class DeadlineManager:
    """
    Manages deadlines, notifications, and compliance tracking
    """

    @staticmethod
    def calculate_t_minus_alerts(deadline: datetime, current_date: datetime = None) -> Dict[str, Any]:
        """
        Calculate T-minus countdown and generate alerts
        """
        if current_date is None:
            current_date = datetime.utcnow()

        days_until = (deadline - current_date).days
        hours_until = (deadline - current_date).total_seconds() / 3600

        # Determine alert level
        if days_until < 0:
            alert_level = "OVERDUE"
            urgency = "CRITICAL"
        elif days_until == 0:
            alert_level = "TODAY"
            urgency = "CRITICAL"
        elif days_until <= 1:
            alert_level = "24_HOURS"
            urgency = "URGENT"
        elif days_until <= 3:
            alert_level = "72_HOURS"
            urgency = "HIGH"
        elif days_until <= 7:
            alert_level = "ONE_WEEK"
            urgency = "MEDIUM"
        elif days_until <= 14:
            alert_level = "TWO_WEEKS"
            urgency = "LOW"
        else:
            alert_level = "FUTURE"
            urgency = "INFO"

        return {
            "deadline": deadline,
            "days_until": days_until,
            "hours_until": int(hours_until),
            "alert_level": alert_level,
            "urgency": urgency,
            "is_overdue": days_until < 0,
            "countdown_text": f"T-{days_until} days" if days_until >= 0 else f"T+{abs(days_until)} days (OVERDUE)"
        }

    @staticmethod
    def check_court_holidays(deadline: datetime, jurisdiction: str = "federal") -> Dict[str, Any]:
        """
        Check if deadline falls on court holiday and suggest adjustment
        Note: This is a simplified version. In production, use actual court calendars
        """
        # Federal holidays (simplified)
        federal_holidays = [
            datetime(2025, 1, 1),   # New Year's Day
            datetime(2025, 1, 20),  # MLK Day
            datetime(2025, 2, 17),  # Presidents Day
            datetime(2025, 5, 26),  # Memorial Day
            datetime(2025, 7, 4),   # Independence Day
            datetime(2025, 9, 1),   # Labor Day
            datetime(2025, 10, 13), # Columbus Day
            datetime(2025, 11, 11), # Veterans Day
            datetime(2025, 11, 27), # Thanksgiving
            datetime(2025, 12, 25), # Christmas
        ]

        # Check if weekend
        is_weekend = deadline.weekday() >= 5

        # Check if holiday
        is_holiday = any(
            deadline.date() == holiday.date()
            for holiday in federal_holidays
        )

        if is_weekend or is_holiday:
            # Find next business day
            next_business_day = deadline
            while next_business_day.weekday() >= 5 or any(
                next_business_day.date() == h.date() for h in federal_holidays
            ):
                next_business_day += timedelta(days=1)

            return {
                "is_court_day": False,
                "is_weekend": is_weekend,
                "is_holiday": is_holiday,
                "original_deadline": deadline,
                "suggested_deadline": next_business_day,
                "adjustment_days": (next_business_day - deadline).days
            }

        return {
            "is_court_day": True,
            "is_weekend": False,
            "is_holiday": False,
            "original_deadline": deadline,
            "suggested_deadline": deadline,
            "adjustment_days": 0
        }

    @staticmethod
    def apply_grace_periods(deadline: datetime, document_type: str) -> datetime:
        """
        Apply grace periods based on document type and rules
        """
        grace_periods = {
            'electronic_filing': timedelta(hours=23, minutes=59),  # End of day
            'mail_service': timedelta(days=3),  # Mail rule
            'notice_objection': timedelta(days=1),  # Day after service
            'response_pleading': timedelta(days=0),  # No grace period
        }

        grace = grace_periods.get(document_type, timedelta(days=0))
        return deadline + grace


# ============================================================================
# BUSINESS LOGIC & CALCULATIONS
# ============================================================================

class BusinessLogicCalculator:
    """
    Handles automated calculations for bids, distributions, fees, etc.
    """

    @staticmethod
    def calculate_bid_increment(current_bid: Decimal, asset_value: Decimal = None) -> Decimal:
        """
        Calculate minimum bid increment based on current bid amount
        """
        current = float(current_bid)

        if current < 1000:
            return Decimal("50")
        elif current < 5000:
            return Decimal("100")
        elif current < 10000:
            return Decimal("250")
        elif current < 50000:
            return Decimal("500")
        elif current < 100000:
            return Decimal("1000")
        elif current < 500000:
            return Decimal("2500")
        elif current < 1000000:
            return Decimal("5000")
        else:
            return Decimal("10000")

    @staticmethod
    def calculate_deposit_requirement(bid_amount: Decimal, deposit_percentage: Decimal = None) -> Decimal:
        """
        Calculate required deposit amount
        """
        if deposit_percentage:
            return bid_amount * (deposit_percentage / 100)

        # Default deposit percentage based on bid amount
        bid_float = float(bid_amount)
        if bid_float < 10000:
            percentage = Decimal("10")  # 10%
        elif bid_float < 100000:
            percentage = Decimal("10")  # 10%
        elif bid_float < 500000:
            percentage = Decimal("5")   # 5%
        else:
            percentage = Decimal("3")   # 3%

        return bid_amount * (percentage / 100)

    @staticmethod
    def calculate_credit_bid_conversion(
        claim_amount: Decimal,
        secured_amount: Decimal,
        asset_value: Decimal
    ) -> Dict[str, Decimal]:
        """
        Calculate credit bid conversion for secured creditors
        """
        # Credit bid limited to lesser of claim amount or asset value
        max_credit_bid = min(secured_amount, asset_value)

        # Calculate deficiency if claim exceeds asset value
        deficiency = max(Decimal("0"), claim_amount - asset_value)

        return {
            "max_credit_bid": max_credit_bid,
            "secured_claim": secured_amount,
            "total_claim": claim_amount,
            "asset_value": asset_value,
            "deficiency_claim": deficiency,
            "cash_required": Decimal("0")  # Credit bid requires no cash
        }

    @staticmethod
    def calculate_distribution_priorities(
        total_amount: Decimal,
        claims: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate distribution amounts based on priority levels
        Follows bankruptcy priority waterfall
        """
        # Sort claims by priority (1 = highest)
        sorted_claims = sorted(claims, key=lambda c: c.get('priority_level', 999))

        remaining = total_amount
        distributions = []

        for claim in sorted_claims:
            claim_amount = Decimal(str(claim['amount']))

            if remaining <= 0:
                distribution_amount = Decimal("0")
                percentage_paid = Decimal("0")
            elif remaining >= claim_amount:
                distribution_amount = claim_amount
                percentage_paid = Decimal("100")
                remaining -= claim_amount
            else:
                distribution_amount = remaining
                percentage_paid = (distribution_amount / claim_amount) * 100
                remaining = Decimal("0")

            distributions.append({
                **claim,
                "distribution_amount": distribution_amount,
                "percentage_paid": percentage_paid,
                "shortfall": claim_amount - distribution_amount
            })

        return distributions

    @staticmethod
    def calculate_professional_fee_caps(
        case_type: str,
        estate_value: Decimal
    ) -> Dict[str, Decimal]:
        """
        Calculate professional fee caps based on case type and estate value
        """
        # Simplified fee structure (actual varies by jurisdiction)
        if case_type == "bankruptcy_ch7":
            # Chapter 7 percentage caps
            if estate_value <= 50000:
                cap_percentage = Decimal("10")
            elif estate_value <= 250000:
                cap_percentage = Decimal("7.5")
            else:
                cap_percentage = Decimal("5")

        elif case_type == "bankruptcy_ch11":
            # Chapter 11 caps (more complex)
            cap_percentage = Decimal("3")  # Simplified

        else:
            cap_percentage = Decimal("15")  # General litigation

        cap_amount = estate_value * (cap_percentage / 100)

        return {
            "estate_value": estate_value,
            "cap_percentage": cap_percentage,
            "cap_amount": cap_amount,
            "case_type": case_type
        }


# ============================================================================
# VALIDATION RULES
# ============================================================================

class ValidationEngine:
    """
    Validates case data and operations
    """

    @staticmethod
    def validate_qualified_bidder(
        bidder_data: Dict[str, Any],
        criteria: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate if bidder meets qualification criteria
        """
        errors = []

        # Check deposit paid
        if criteria.get('requires_deposit') and not bidder_data.get('deposit_paid'):
            errors.append("Required deposit not paid")

        # Check financial capacity
        min_net_worth = criteria.get('minimum_net_worth')
        if min_net_worth and bidder_data.get('net_worth', 0) < min_net_worth:
            errors.append(f"Net worth below minimum requirement of ${min_net_worth:,.2f}")

        # Check prior approval
        if criteria.get('requires_court_approval') and not bidder_data.get('court_approved'):
            errors.append("Court approval required but not obtained")

        # Check conflicts of interest
        if bidder_data.get('has_conflicts'):
            errors.append("Disclosed conflicts of interest must be resolved")

        return (len(errors) == 0, errors)

    @staticmethod
    def validate_notice_period_compliance(
        filing_date: datetime,
        event_date: datetime,
        required_notice_days: int
    ) -> Tuple[bool, str]:
        """
        Validate that required notice period has been met
        """
        actual_days = (event_date - filing_date).days

        if actual_days < required_notice_days:
            return (
                False,
                f"Insufficient notice: {actual_days} days provided, {required_notice_days} required"
            )

        return (True, f"Notice period satisfied: {actual_days} days")

    @staticmethod
    def validate_document_completeness(
        document_data: Dict[str, Any],
        required_fields: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that document contains all required fields
        """
        missing_fields = [
            field for field in required_fields
            if field not in document_data or not document_data[field]
        ]

        if missing_fields:
            return (False, missing_fields)

        return (True, [])


# ============================================================================
# EXPORT INSTANCES
# ============================================================================

timeline_workflow_engine = TimelineWorkflowEngine()
deadline_manager = DeadlineManager()
business_logic_calculator = BusinessLogicCalculator()
validation_engine = ValidationEngine()
