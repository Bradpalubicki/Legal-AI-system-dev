"""
Court order tracking and compliance monitoring system.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.orm import Session

from ..shared.database.models import Case, Document, User, TranscriptSegment
from ..shared.database.connection import get_db
from .statement_analyzer import IdentifiedStatement, StatementType, OrderType, UrgencyLevel


class ComplianceStatus(Enum):
    """Status of compliance with a court order."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    PARTIALLY_COMPLIED = "partially_complied"
    NON_COMPLIANT = "non_compliant"
    DISPUTED = "disputed"
    MODIFIED = "modified"
    VACATED = "vacated"


class OrderCategory(Enum):
    """Categories of court orders for organization."""
    DISCOVERY = "discovery"
    MOTION_PRACTICE = "motion_practice"
    SCHEDULING = "scheduling"
    INJUNCTIVE_RELIEF = "injunctive_relief"
    SANCTIONS = "sanctions"
    EVIDENCE = "evidence"
    SETTLEMENT = "settlement"
    PROCEDURAL = "procedural"
    SUBSTANTIVE = "substantive"


@dataclass
class ComplianceRequirement:
    """Individual requirement within a court order."""
    requirement_id: str
    description: str
    responsible_party: str
    deadline: Optional[datetime]
    status: ComplianceStatus
    evidence_required: List[str]
    completion_criteria: List[str]
    notes: List[str] = field(default_factory=list)
    completed_date: Optional[datetime] = None
    completion_evidence: List[str] = field(default_factory=list)


@dataclass
class TrackedOrder:
    """Represents a court order being tracked for compliance."""
    order_id: str
    case_id: str
    order_type: OrderType
    category: OrderCategory
    title: str
    full_text: str
    issued_date: datetime
    effective_date: Optional[datetime]
    compliance_deadline: Optional[datetime]
    issuing_judge: str
    overall_status: ComplianceStatus
    requirements: List[ComplianceRequirement]
    related_parties: List[str]
    enforcement_mechanism: Optional[str]
    modification_history: List[Dict[str, Any]] = field(default_factory=list)
    compliance_notes: List[str] = field(default_factory=list)
    urgency_level: UrgencyLevel = UrgencyLevel.MEDIUM
    auto_reminders: bool = True
    next_review_date: Optional[datetime] = None


class OrderTracker:
    """System for tracking court orders and monitoring compliance."""
    
    def __init__(self):
        self.tracked_orders: Dict[str, TrackedOrder] = {}
        self.compliance_alerts: List[Dict[str, Any]] = []
        
    async def track_new_order(
        self, 
        statement: IdentifiedStatement, 
        case: Case,
        db: Session
    ) -> TrackedOrder:
        """Begin tracking a newly identified court order."""
        try:
            order_id = f"order_{case.id}_{int(datetime.now().timestamp())}"
            
            # Extract compliance requirements
            requirements = await self._extract_compliance_requirements(statement)
            
            # Determine category
            category = self._categorize_order(statement)
            
            # Calculate deadlines
            compliance_deadline = self._calculate_compliance_deadline(statement, requirements)
            next_review = self._calculate_next_review_date(compliance_deadline)
            
            tracked_order = TrackedOrder(
                order_id=order_id,
                case_id=case.id,
                order_type=statement.order_type or OrderType.SUMMARY_JUDGMENT,
                category=category,
                title=self._generate_order_title(statement),
                full_text=statement.text,
                issued_date=datetime.now(),
                effective_date=datetime.now(),
                compliance_deadline=compliance_deadline,
                issuing_judge=self._extract_judge_name(statement.speaker),
                overall_status=ComplianceStatus.PENDING,
                requirements=requirements,
                related_parties=statement.related_parties,
                enforcement_mechanism=statement.enforcement_mechanism,
                urgency_level=statement.urgency,
                next_review_date=next_review
            )
            
            self.tracked_orders[order_id] = tracked_order
            
            # Schedule compliance reminders
            if tracked_order.auto_reminders:
                await self._schedule_compliance_reminders(tracked_order)
            
            return tracked_order
            
        except Exception as e:
            print(f"Error tracking new order: {e}")
            raise

    async def _extract_compliance_requirements(
        self, 
        statement: IdentifiedStatement
    ) -> List[ComplianceRequirement]:
        """Extract specific compliance requirements from an order."""
        requirements = []
        
        for i, action in enumerate(statement.required_actions):
            req_id = f"req_{int(datetime.now().timestamp())}_{i}"
            
            # Find associated deadline
            deadline = None
            for deadline_info in statement.deadlines:
                if action.lower() in deadline_info.get("description", "").lower():
                    deadline = datetime.fromisoformat(deadline_info["deadline"])
                    break
            
            # Determine responsible party
            responsible_party = self._determine_responsible_party(action, statement.related_parties)
            
            requirement = ComplianceRequirement(
                requirement_id=req_id,
                description=action,
                responsible_party=responsible_party,
                deadline=deadline,
                status=ComplianceStatus.PENDING,
                evidence_required=self._determine_evidence_required(action),
                completion_criteria=self._determine_completion_criteria(action)
            )
            
            requirements.append(requirement)
        
        return requirements

    def _categorize_order(self, statement: IdentifiedStatement) -> OrderCategory:
        """Categorize the court order based on its content."""
        text_lower = statement.text.lower()
        context_lower = statement.context.lower()
        combined_text = f"{text_lower} {context_lower}"
        
        category_keywords = {
            OrderCategory.DISCOVERY: [
                "discovery", "interrogatories", "requests for production", 
                "depositions", "document production", "discovery deadline"
            ],
            OrderCategory.MOTION_PRACTICE: [
                "motion", "brief", "response", "reply", "motion to dismiss",
                "summary judgment", "motion practice"
            ],
            OrderCategory.SCHEDULING: [
                "scheduling", "trial date", "pretrial", "conference",
                "case management", "deadlines", "schedule"
            ],
            OrderCategory.INJUNCTIVE_RELIEF: [
                "injunction", "restraining order", "tro", "preliminary",
                "permanent", "enjoin", "restrain"
            ],
            OrderCategory.SANCTIONS: [
                "sanctions", "sanction", "penalty", "fine", "contempt",
                "violation", "non-compliance"
            ],
            OrderCategory.EVIDENCE: [
                "evidence", "exhibit", "demonstrative", "witness",
                "testimony", "expert", "evidentiary"
            ],
            OrderCategory.SETTLEMENT: [
                "settlement", "mediation", "arbitration", "resolve",
                "negotiate", "settlement conference"
            ]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return category
        
        # Default categorization based on order type
        if statement.order_type in [OrderType.DISCOVERY_SANCTIONS]:
            return OrderCategory.DISCOVERY
        elif statement.order_type in [OrderType.PRELIMINARY_INJUNCTION, OrderType.TEMPORARY_RESTRAINING_ORDER]:
            return OrderCategory.INJUNCTIVE_RELIEF
        
        return OrderCategory.PROCEDURAL

    def _calculate_compliance_deadline(
        self, 
        statement: IdentifiedStatement, 
        requirements: List[ComplianceRequirement]
    ) -> Optional[datetime]:
        """Calculate the overall compliance deadline for the order."""
        deadlines = []
        
        # Extract deadlines from statement
        for deadline_info in statement.deadlines:
            if deadline_info.get("deadline"):
                deadlines.append(datetime.fromisoformat(deadline_info["deadline"]))
        
        # Extract deadlines from requirements
        for req in requirements:
            if req.deadline:
                deadlines.append(req.deadline)
        
        # Return earliest deadline
        if deadlines:
            return min(deadlines)
        
        # Default deadline based on urgency
        if statement.urgency == UrgencyLevel.CRITICAL:
            return datetime.now() + timedelta(days=1)
        elif statement.urgency == UrgencyLevel.HIGH:
            return datetime.now() + timedelta(days=7)
        elif statement.urgency == UrgencyLevel.MEDIUM:
            return datetime.now() + timedelta(days=30)
        
        return None

    def _calculate_next_review_date(self, compliance_deadline: Optional[datetime]) -> Optional[datetime]:
        """Calculate when to next review compliance status."""
        if not compliance_deadline:
            return datetime.now() + timedelta(days=7)
        
        days_until_deadline = (compliance_deadline - datetime.now()).days
        
        if days_until_deadline <= 1:
            return datetime.now() + timedelta(hours=4)
        elif days_until_deadline <= 7:
            return datetime.now() + timedelta(days=1)
        elif days_until_deadline <= 30:
            return datetime.now() + timedelta(days=3)
        else:
            return datetime.now() + timedelta(weeks=1)

    def _generate_order_title(self, statement: IdentifiedStatement) -> str:
        """Generate a descriptive title for the order."""
        if statement.order_type:
            base_title = statement.order_type.value.replace("_", " ").title()
        else:
            base_title = "Court Order"
        
        # Add context if available
        context_words = statement.context.split()[:10]
        if len(context_words) > 3:
            context_snippet = " - " + " ".join(context_words[:5]) + "..."
            return base_title + context_snippet
        
        return base_title

    def _extract_judge_name(self, speaker: str) -> str:
        """Extract judge name from speaker identification."""
        # Clean up common judge identifiers
        cleaned = speaker.replace("The Court", "").replace("THE COURT", "").strip()
        if cleaned.startswith("Judge "):
            return cleaned[6:]
        elif cleaned.startswith("Magistrate "):
            return cleaned[11:]
        elif cleaned.startswith("Justice "):
            return cleaned[8:]
        
        return cleaned if cleaned else "Unknown Judge"

    def _determine_responsible_party(
        self, 
        action: str, 
        related_parties: List[str]
    ) -> str:
        """Determine which party is responsible for completing an action."""
        action_lower = action.lower()
        
        # Look for party-specific language
        if "plaintiff" in action_lower:
            return "Plaintiff"
        elif "defendant" in action_lower:
            return "Defendant"
        elif "petitioner" in action_lower:
            return "Petitioner"
        elif "respondent" in action_lower:
            return "Respondent"
        
        # Default to first related party or generic
        if related_parties:
            return related_parties[0]
        
        return "All Parties"

    def _determine_evidence_required(self, action: str) -> List[str]:
        """Determine what evidence is required to prove compliance."""
        action_lower = action.lower()
        evidence_types = []
        
        if "file" in action_lower or "filing" in action_lower:
            evidence_types.append("Court filing receipt")
            evidence_types.append("Filed document copy")
        
        if "produce" in action_lower or "provide" in action_lower:
            evidence_types.append("Production log")
            evidence_types.append("Delivered documents")
        
        if "pay" in action_lower or "payment" in action_lower:
            evidence_types.append("Payment receipt")
            evidence_types.append("Bank statement")
        
        if "appear" in action_lower or "attendance" in action_lower:
            evidence_types.append("Appearance record")
            evidence_types.append("Attendance confirmation")
        
        if not evidence_types:
            evidence_types.append("Completion documentation")
        
        return evidence_types

    def _determine_completion_criteria(self, action: str) -> List[str]:
        """Determine criteria for considering the action complete."""
        action_lower = action.lower()
        criteria = []
        
        if "file" in action_lower:
            criteria.append("Document filed with court")
            criteria.append("Proof of service completed")
        
        if "serve" in action_lower:
            criteria.append("Service completed on all parties")
            criteria.append("Proof of service filed")
        
        if "produce" in action_lower:
            criteria.append("All requested documents provided")
            criteria.append("Production complete and verified")
        
        if "comply" in action_lower:
            criteria.append("Full compliance demonstrated")
            criteria.append("No outstanding violations")
        
        if not criteria:
            criteria.append("Action completed as ordered")
        
        return criteria

    async def _schedule_compliance_reminders(self, order: TrackedOrder):
        """Schedule automatic reminders for order compliance."""
        try:
            if not order.compliance_deadline:
                return
            
            now = datetime.now()
            deadline = order.compliance_deadline
            
            # Schedule reminders at different intervals
            reminder_intervals = [
                timedelta(days=7),   # 7 days before
                timedelta(days=3),   # 3 days before  
                timedelta(days=1),   # 1 day before
                timedelta(hours=4),  # 4 hours before
                timedelta(hours=1),  # 1 hour before
            ]
            
            for interval in reminder_intervals:
                reminder_time = deadline - interval
                if reminder_time > now:
                    # Schedule reminder (in a real system, this would use a task queue)
                    print(f"Reminder scheduled for {reminder_time}: {order.title}")
                    
        except Exception as e:
            print(f"Error scheduling reminders: {e}")

    async def update_compliance_status(
        self, 
        order_id: str, 
        requirement_id: str,
        status: ComplianceStatus,
        completion_evidence: Optional[List[str]] = None,
        notes: Optional[str] = None
    ):
        """Update the compliance status of a specific requirement."""
        try:
            if order_id not in self.tracked_orders:
                raise ValueError(f"Order {order_id} not found")
            
            order = self.tracked_orders[order_id]
            
            # Find and update requirement
            for req in order.requirements:
                if req.requirement_id == requirement_id:
                    req.status = status
                    if completion_evidence:
                        req.completion_evidence = completion_evidence
                    if notes:
                        req.notes.append(f"{datetime.now().isoformat()}: {notes}")
                    if status == ComplianceStatus.COMPLETED:
                        req.completed_date = datetime.now()
                    break
            
            # Update overall order status
            await self._update_overall_status(order)
            
        except Exception as e:
            print(f"Error updating compliance status: {e}")
            raise

    async def _update_overall_status(self, order: TrackedOrder):
        """Update the overall compliance status of an order."""
        requirement_statuses = [req.status for req in order.requirements]
        
        if not requirement_statuses:
            order.overall_status = ComplianceStatus.PENDING
            return
        
        # All completed
        if all(status == ComplianceStatus.COMPLETED for status in requirement_statuses):
            order.overall_status = ComplianceStatus.COMPLETED
        
        # Any overdue
        elif any(status == ComplianceStatus.OVERDUE for status in requirement_statuses):
            order.overall_status = ComplianceStatus.OVERDUE
        
        # Any non-compliant
        elif any(status == ComplianceStatus.NON_COMPLIANT for status in requirement_statuses):
            order.overall_status = ComplianceStatus.NON_COMPLIANT
        
        # Some completed, some pending
        elif any(status == ComplianceStatus.COMPLETED for status in requirement_statuses):
            if any(status == ComplianceStatus.PENDING for status in requirement_statuses):
                order.overall_status = ComplianceStatus.PARTIALLY_COMPLIED
            else:
                order.overall_status = ComplianceStatus.IN_PROGRESS
        
        # All in progress
        elif all(status == ComplianceStatus.IN_PROGRESS for status in requirement_statuses):
            order.overall_status = ComplianceStatus.IN_PROGRESS
        
        else:
            order.overall_status = ComplianceStatus.PENDING

    async def check_compliance_deadlines(self) -> List[Dict[str, Any]]:
        """Check all tracked orders for approaching or missed deadlines."""
        alerts = []
        now = datetime.now()
        
        for order in self.tracked_orders.values():
            # Check overall order deadline
            if order.compliance_deadline:
                days_until_deadline = (order.compliance_deadline - now).days
                hours_until_deadline = (order.compliance_deadline - now).total_seconds() / 3600
                
                if order.compliance_deadline < now and order.overall_status != ComplianceStatus.COMPLETED:
                    alerts.append({
                        "type": "overdue_order",
                        "order_id": order.order_id,
                        "title": order.title,
                        "deadline": order.compliance_deadline.isoformat(),
                        "days_overdue": abs(days_until_deadline),
                        "severity": "critical"
                    })
                
                elif days_until_deadline <= 1 and order.overall_status not in [ComplianceStatus.COMPLETED, ComplianceStatus.OVERDUE]:
                    alerts.append({
                        "type": "urgent_deadline",
                        "order_id": order.order_id,
                        "title": order.title,
                        "deadline": order.compliance_deadline.isoformat(),
                        "hours_remaining": max(0, hours_until_deadline),
                        "severity": "high"
                    })
                
                elif days_until_deadline <= 7 and order.overall_status == ComplianceStatus.PENDING:
                    alerts.append({
                        "type": "upcoming_deadline",
                        "order_id": order.order_id,
                        "title": order.title,
                        "deadline": order.compliance_deadline.isoformat(),
                        "days_remaining": days_until_deadline,
                        "severity": "medium"
                    })
            
            # Check individual requirement deadlines
            for req in order.requirements:
                if req.deadline and req.status not in [ComplianceStatus.COMPLETED, ComplianceStatus.OVERDUE]:
                    req_days_until = (req.deadline - now).days
                    
                    if req.deadline < now:
                        alerts.append({
                            "type": "overdue_requirement",
                            "order_id": order.order_id,
                            "requirement_id": req.requirement_id,
                            "description": req.description,
                            "deadline": req.deadline.isoformat(),
                            "days_overdue": abs(req_days_until),
                            "severity": "high"
                        })
                    
                    elif req_days_until <= 2:
                        alerts.append({
                            "type": "urgent_requirement",
                            "order_id": order.order_id,
                            "requirement_id": req.requirement_id,
                            "description": req.description,
                            "deadline": req.deadline.isoformat(),
                            "days_remaining": req_days_until,
                            "severity": "medium"
                        })
        
        self.compliance_alerts = alerts
        return alerts

    def get_order_summary(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get a comprehensive summary of an order's status."""
        if order_id not in self.tracked_orders:
            return None
        
        order = self.tracked_orders[order_id]
        
        completed_requirements = sum(1 for req in order.requirements if req.status == ComplianceStatus.COMPLETED)
        total_requirements = len(order.requirements)
        completion_percentage = (completed_requirements / total_requirements * 100) if total_requirements > 0 else 0
        
        return {
            "order_id": order.order_id,
            "title": order.title,
            "case_id": order.case_id,
            "order_type": order.order_type.value,
            "category": order.category.value,
            "overall_status": order.overall_status.value,
            "urgency_level": order.urgency_level.value,
            "issued_date": order.issued_date.isoformat(),
            "compliance_deadline": order.compliance_deadline.isoformat() if order.compliance_deadline else None,
            "completion_percentage": completion_percentage,
            "total_requirements": total_requirements,
            "completed_requirements": completed_requirements,
            "next_review_date": order.next_review_date.isoformat() if order.next_review_date else None,
            "requirements": [
                {
                    "requirement_id": req.requirement_id,
                    "description": req.description,
                    "responsible_party": req.responsible_party,
                    "status": req.status.value,
                    "deadline": req.deadline.isoformat() if req.deadline else None,
                    "completed_date": req.completed_date.isoformat() if req.completed_date else None
                }
                for req in order.requirements
            ]
        }

    def get_case_orders_summary(self, case_id: str) -> Dict[str, Any]:
        """Get summary of all orders for a specific case."""
        case_orders = [order for order in self.tracked_orders.values() if order.case_id == case_id]
        
        total_orders = len(case_orders)
        completed_orders = sum(1 for order in case_orders if order.overall_status == ComplianceStatus.COMPLETED)
        overdue_orders = sum(1 for order in case_orders if order.overall_status == ComplianceStatus.OVERDUE)
        pending_orders = sum(1 for order in case_orders if order.overall_status == ComplianceStatus.PENDING)
        
        return {
            "case_id": case_id,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "overdue_orders": overdue_orders,
            "pending_orders": pending_orders,
            "compliance_rate": (completed_orders / total_orders * 100) if total_orders > 0 else 100,
            "orders": [
                {
                    "order_id": order.order_id,
                    "title": order.title,
                    "status": order.overall_status.value,
                    "deadline": order.compliance_deadline.isoformat() if order.compliance_deadline else None
                }
                for order in case_orders
            ]
        }