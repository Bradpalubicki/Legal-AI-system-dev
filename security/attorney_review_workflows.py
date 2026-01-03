#!/usr/bin/env python3
"""
Attorney Review Workflow System
Enterprise-grade review workflows for legal professional accountability
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass, asdict
import secrets
from pathlib import Path
import threading

class ReviewType(Enum):
    """Types of attorney review workflows"""
    DOCUMENT_REVIEW = "document_review"
    LEGAL_OPINION_REVIEW = "legal_opinion_review"
    BRIEF_REVIEW = "brief_review"
    CONTRACT_REVIEW = "contract_review"
    COMPLIANCE_REVIEW = "compliance_review"
    PEER_REVIEW = "peer_review"
    SUPERVISORY_REVIEW = "supervisory_review"
    QUALITY_ASSURANCE = "quality_assurance"
    ETHICAL_REVIEW = "ethical_review"
    CONFLICT_REVIEW = "conflict_review"
    BILLING_REVIEW = "billing_review"
    TIME_ENTRY_REVIEW = "time_entry_review"

class ReviewStatus(Enum):
    """Review workflow status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    REQUIRES_REVISION = "requires_revision"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class ReviewPriority(Enum):
    """Review priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class ReviewAction(Enum):
    """Available review actions"""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_REVISION = "request_revision"
    ESCALATE = "escalate"
    DELEGATE = "delegate"
    DEFER = "defer"
    WITHDRAW = "withdraw"
    SUPERSEDE = "supersede"

@dataclass
class ReviewWorkflow:
    """Attorney review workflow with complete tracking"""
    workflow_id: str
    review_type: ReviewType
    title: str
    description: str
    
    # Participants
    requester_id: str
    requester_email: str
    requester_role: str
    assigned_reviewers: List[str]
    current_reviewer: Optional[str]
    
    # Content being reviewed
    content_type: str  # "document", "brief", "contract", etc.
    content_id: str
    content_summary: str
    content_location: str
    content_hash: Optional[str]
    
    # Client and case information
    client_id: Optional[str]
    case_id: Optional[str]
    matter_id: Optional[str]
    practice_area: str
    
    # Workflow configuration
    requires_parallel_review: bool
    requires_sequential_review: bool
    minimum_reviewers: int
    required_reviewer_roles: List[str]
    auto_approval_threshold: Optional[float]
    
    # Status and timing
    status: ReviewStatus
    priority: ReviewPriority
    created_at: datetime
    due_date: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    # Review history
    review_actions: List[Dict[str, Any]]
    revision_history: List[Dict[str, Any]]
    comments: List[Dict[str, Any]]
    
    # Compliance and tracking
    billable_time_minutes: Optional[int]
    compliance_category: str
    contains_privileged_info: bool
    retention_period_years: int
    
    # Metadata
    tags: List[str]
    custom_fields: Dict[str, Any]

@dataclass
class ReviewAction:
    """Individual review action within a workflow"""
    action_id: str
    workflow_id: str
    reviewer_id: str
    reviewer_email: str
    reviewer_role: str
    
    action_type: ReviewAction
    decision: str
    comments: str
    rating: Optional[int]  # 1-5 scale
    
    # Time tracking
    time_spent_minutes: Optional[int]
    action_date: datetime
    
    # Attachments and references
    attachments: List[str]
    referenced_documents: List[str]
    referenced_cases: List[str]
    
    # Follow-up requirements
    requires_follow_up: bool
    follow_up_date: Optional[datetime]
    follow_up_assignee: Optional[str]
    
    # Billing information
    is_billable: bool
    billing_code: Optional[str]
    client_communication: bool

class AttorneyReviewWorkflowManager:
    """Enterprise attorney review workflow management system"""
    
    def __init__(self, db_path: str = "attorney_review_workflows.db"):
        self.db_path = db_path
        self.logger = self._setup_logger()
        self._init_database()
        
        # Workflow configuration by review type
        self.workflow_configs = {
            ReviewType.DOCUMENT_REVIEW: {
                "default_reviewers": 1,
                "required_roles": ["associate", "senior_associate", "partner"],
                "max_review_days": 5,
                "parallel_review": False,
                "auto_approval_threshold": None
            },
            
            ReviewType.LEGAL_OPINION_REVIEW: {
                "default_reviewers": 2,
                "required_roles": ["senior_associate", "partner"],
                "max_review_days": 7,
                "parallel_review": True,
                "auto_approval_threshold": None
            },
            
            ReviewType.BRIEF_REVIEW: {
                "default_reviewers": 1,
                "required_roles": ["senior_associate", "partner"],
                "max_review_days": 3,
                "parallel_review": False,
                "auto_approval_threshold": None
            },
            
            ReviewType.CONTRACT_REVIEW: {
                "default_reviewers": 2,
                "required_roles": ["associate", "senior_associate", "partner"],
                "max_review_days": 5,
                "parallel_review": True,
                "auto_approval_threshold": None
            },
            
            ReviewType.COMPLIANCE_REVIEW: {
                "default_reviewers": 1,
                "required_roles": ["compliance_officer", "managing_partner"],
                "max_review_days": 10,
                "parallel_review": False,
                "auto_approval_threshold": None
            },
            
            ReviewType.ETHICAL_REVIEW: {
                "default_reviewers": 2,
                "required_roles": ["partner", "managing_partner", "compliance_officer"],
                "max_review_days": 7,
                "parallel_review": True,
                "auto_approval_threshold": None
            },
            
            ReviewType.BILLING_REVIEW: {
                "default_reviewers": 1,
                "required_roles": ["partner", "managing_partner"],
                "max_review_days": 3,
                "parallel_review": False,
                "auto_approval_threshold": 0.95
            }
        }
        
        # Auto-escalation rules
        self.escalation_rules = {
            "overdue_days": 2,
            "urgent_overdue_hours": 24,
            "critical_overdue_hours": 12,
            "escalation_chain": ["senior_associate", "partner", "managing_partner"]
        }
        
        # Start workflow monitoring thread
        self._start_workflow_monitor()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup review workflow logger"""
        logger = logging.getLogger('attorney_review_workflows')
        logger.setLevel(logging.INFO)
        
        Path('logs').mkdir(exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            'logs/attorney_review_workflows.log',
            maxBytes=50*1024*1024,
            backupCount=100,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - REVIEW_WORKFLOW - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize review workflow database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Review workflows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_workflows (
                workflow_id TEXT PRIMARY KEY,
                review_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                requester_id TEXT NOT NULL,
                requester_email TEXT NOT NULL,
                requester_role TEXT NOT NULL,
                assigned_reviewers TEXT NOT NULL,
                current_reviewer TEXT,
                content_type TEXT NOT NULL,
                content_id TEXT NOT NULL,
                content_summary TEXT NOT NULL,
                content_location TEXT NOT NULL,
                content_hash TEXT,
                client_id TEXT,
                case_id TEXT,
                matter_id TEXT,
                practice_area TEXT NOT NULL,
                requires_parallel_review BOOLEAN NOT NULL,
                requires_sequential_review BOOLEAN NOT NULL,
                minimum_reviewers INTEGER NOT NULL,
                required_reviewer_roles TEXT NOT NULL,
                auto_approval_threshold REAL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                due_date TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                review_actions TEXT NOT NULL,
                revision_history TEXT NOT NULL,
                comments TEXT NOT NULL,
                billable_time_minutes INTEGER,
                compliance_category TEXT NOT NULL,
                contains_privileged_info BOOLEAN NOT NULL,
                retention_period_years INTEGER NOT NULL,
                tags TEXT NOT NULL,
                custom_fields TEXT NOT NULL
            )
        ''')
        
        # Review actions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_actions (
                action_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                reviewer_email TEXT NOT NULL,
                reviewer_role TEXT NOT NULL,
                action_type TEXT NOT NULL,
                decision TEXT NOT NULL,
                comments TEXT NOT NULL,
                rating INTEGER,
                time_spent_minutes INTEGER,
                action_date TIMESTAMP NOT NULL,
                attachments TEXT NOT NULL,
                referenced_documents TEXT NOT NULL,
                referenced_cases TEXT NOT NULL,
                requires_follow_up BOOLEAN DEFAULT FALSE,
                follow_up_date TIMESTAMP,
                follow_up_assignee TEXT,
                is_billable BOOLEAN DEFAULT FALSE,
                billing_code TEXT,
                client_communication BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (workflow_id) REFERENCES review_workflows (workflow_id)
            )
        ''')
        
        # Workflow templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_templates (
                template_id TEXT PRIMARY KEY,
                template_name TEXT NOT NULL,
                review_type TEXT NOT NULL,
                description TEXT NOT NULL,
                default_reviewers INTEGER NOT NULL,
                required_roles TEXT NOT NULL,
                max_review_days INTEGER NOT NULL,
                parallel_review BOOLEAN DEFAULT FALSE,
                template_config TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Review metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_metrics (
                metric_id TEXT PRIMARY KEY,
                reviewer_id TEXT NOT NULL,
                metric_date DATE NOT NULL,
                total_reviews INTEGER DEFAULT 0,
                completed_reviews INTEGER DEFAULT 0,
                average_review_time_hours REAL DEFAULT 0.0,
                approval_rate REAL DEFAULT 0.0,
                revision_request_rate REAL DEFAULT 0.0,
                overdue_reviews INTEGER DEFAULT 0,
                quality_score REAL DEFAULT 0.0,
                billable_hours REAL DEFAULT 0.0
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_status ON review_workflows (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_requester ON review_workflows (requester_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_reviewer ON review_workflows (current_reviewer)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_due_date ON review_workflows (due_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_workflow ON review_actions (workflow_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_reviewer ON review_actions (reviewer_id)')
        
        conn.commit()
        conn.close()
    
    def create_review_workflow(
        self,
        review_type: ReviewType,
        title: str,
        description: str,
        requester_id: str,
        requester_email: str,
        requester_role: str,
        content_type: str,
        content_id: str,
        content_summary: str,
        content_location: str,
        practice_area: str,
        client_id: Optional[str] = None,
        case_id: Optional[str] = None,
        matter_id: Optional[str] = None,
        assigned_reviewers: Optional[List[str]] = None,
        priority: ReviewPriority = ReviewPriority.MEDIUM,
        due_date: Optional[datetime] = None,
        contains_privileged_info: bool = False,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create new attorney review workflow"""
        
        workflow_id = secrets.token_hex(16)
        
        # Get workflow configuration
        config = self.workflow_configs.get(review_type, self.workflow_configs[ReviewType.DOCUMENT_REVIEW])
        
        # Set due date if not specified
        if due_date is None:
            due_date = datetime.now() + timedelta(days=config["max_review_days"])
        
        # Assign reviewers if not specified
        if assigned_reviewers is None:
            assigned_reviewers = self._auto_assign_reviewers(
                review_type, 
                requester_role, 
                practice_area, 
                config["required_roles"],
                config["default_reviewers"]
            )
        
        # Determine current reviewer
        current_reviewer = assigned_reviewers[0] if assigned_reviewers else None
        
        workflow = ReviewWorkflow(
            workflow_id=workflow_id,
            review_type=review_type,
            title=title,
            description=description,
            requester_id=requester_id,
            requester_email=requester_email,
            requester_role=requester_role,
            assigned_reviewers=assigned_reviewers,
            current_reviewer=current_reviewer,
            content_type=content_type,
            content_id=content_id,
            content_summary=content_summary,
            content_location=content_location,
            content_hash=None,
            client_id=client_id,
            case_id=case_id,
            matter_id=matter_id,
            practice_area=practice_area,
            requires_parallel_review=config["parallel_review"],
            requires_sequential_review=not config["parallel_review"],
            minimum_reviewers=config["default_reviewers"],
            required_reviewer_roles=config["required_roles"],
            auto_approval_threshold=config["auto_approval_threshold"],
            status=ReviewStatus.PENDING,
            priority=priority,
            created_at=datetime.now(),
            due_date=due_date,
            started_at=None,
            completed_at=None,
            review_actions=[],
            revision_history=[],
            comments=[],
            billable_time_minutes=None,
            compliance_category=self._get_compliance_category(review_type),
            contains_privileged_info=contains_privileged_info,
            retention_period_years=7,  # Default legal retention
            tags=[],
            custom_fields=custom_fields or {}
        )
        
        # Store workflow
        self._store_workflow(workflow)
        
        # Send notifications to assigned reviewers
        self._notify_reviewers(workflow_id, "assignment")
        
        # Log workflow creation
        self.logger.info(
            f"Review workflow created: {workflow_id} - Type: {review_type.value} - "
            f"Requester: {requester_email} - Reviewers: {len(assigned_reviewers)}"
        )
        
        return workflow_id
    
    def _auto_assign_reviewers(
        self,
        review_type: ReviewType,
        requester_role: str,
        practice_area: str,
        required_roles: List[str],
        default_count: int
    ) -> List[str]:
        """Auto-assign reviewers based on workflow requirements"""
        
        # In a real implementation, this would query the attorney database
        # For now, return placeholder reviewer assignments
        
        # Ensure requester doesn't review their own work
        available_reviewers = []
        
        # Find attorneys with required roles in the same practice area
        # This would normally query the attorney database
        
        # Placeholder logic - would be replaced with actual database queries
        role_hierarchy = {
            "paralegal": ["associate", "senior_associate", "partner"],
            "associate": ["senior_associate", "partner"],
            "senior_associate": ["partner"],
            "partner": ["managing_partner"]
        }
        
        eligible_roles = role_hierarchy.get(requester_role, required_roles)
        
        # Return placeholder reviewer IDs
        # In production, this would return actual attorney IDs
        return [f"reviewer_{i}_for_{review_type.value}" for i in range(min(default_count, len(eligible_roles)))]
    
    def _get_compliance_category(self, review_type: ReviewType) -> str:
        """Get compliance category for review type"""
        category_mapping = {
            ReviewType.DOCUMENT_REVIEW: "document_management",
            ReviewType.LEGAL_OPINION_REVIEW: "legal_advice",
            ReviewType.BRIEF_REVIEW: "litigation_support",
            ReviewType.CONTRACT_REVIEW: "contract_management",
            ReviewType.COMPLIANCE_REVIEW: "regulatory_compliance",
            ReviewType.ETHICAL_REVIEW: "professional_responsibility",
            ReviewType.BILLING_REVIEW: "financial_management",
            ReviewType.TIME_ENTRY_REVIEW: "time_management"
        }
        
        return category_mapping.get(review_type, "general_review")
    
    def submit_review_action(
        self,
        workflow_id: str,
        reviewer_id: str,
        reviewer_email: str,
        reviewer_role: str,
        action_type: ReviewAction,
        decision: str,
        comments: str,
        rating: Optional[int] = None,
        time_spent_minutes: Optional[int] = None,
        attachments: Optional[List[str]] = None,
        is_billable: bool = False,
        billing_code: Optional[str] = None
    ) -> str:
        """Submit review action for workflow"""
        
        action_id = secrets.token_hex(16)
        
        # Get current workflow
        workflow = self._get_workflow_by_id(workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")
        
        # Validate reviewer is authorized
        if reviewer_id not in workflow.assigned_reviewers and reviewer_role not in workflow.required_reviewer_roles:
            raise ValueError("Reviewer not authorized for this workflow")
        
        # Create review action
        review_action = ReviewAction(
            action_id=action_id,
            workflow_id=workflow_id,
            reviewer_id=reviewer_id,
            reviewer_email=reviewer_email,
            reviewer_role=reviewer_role,
            action_type=action_type,
            decision=decision,
            comments=comments,
            rating=rating,
            time_spent_minutes=time_spent_minutes,
            action_date=datetime.now(),
            attachments=attachments or [],
            referenced_documents=[],
            referenced_cases=[],
            requires_follow_up=action_type in [ReviewAction.REQUEST_REVISION, ReviewAction.ESCALATE],
            follow_up_date=None,
            follow_up_assignee=None,
            is_billable=is_billable,
            billing_code=billing_code,
            client_communication=False
        )
        
        # Store review action
        self._store_review_action(review_action)
        
        # Update workflow status based on action
        self._update_workflow_status(workflow_id, action_type, reviewer_id)
        
        # Update reviewer metrics
        self._update_reviewer_metrics(reviewer_id, action_type, time_spent_minutes or 0)
        
        # Send notifications
        self._notify_workflow_participants(workflow_id, action_type, reviewer_email)
        
        # Log review action
        self.logger.info(
            f"Review action submitted: {action_id} - Workflow: {workflow_id} - "
            f"Action: {action_type.value} - Reviewer: {reviewer_email}"
        )
        
        return action_id
    
    def _update_workflow_status(
        self,
        workflow_id: str,
        action_type: ReviewAction,
        reviewer_id: str
    ):
        """Update workflow status based on review action"""
        
        workflow = self._get_workflow_by_id(workflow_id)
        if not workflow:
            return
        
        new_status = workflow.status
        completed_at = None
        
        if action_type == ReviewAction.APPROVE:
            # Check if all required reviews are complete
            if self._are_all_reviews_complete(workflow_id):
                new_status = ReviewStatus.APPROVED
                completed_at = datetime.now()
            else:
                new_status = ReviewStatus.UNDER_REVIEW
        
        elif action_type == ReviewAction.REJECT:
            new_status = ReviewStatus.REJECTED
            completed_at = datetime.now()
        
        elif action_type == ReviewAction.REQUEST_REVISION:
            new_status = ReviewStatus.REQUIRES_REVISION
        
        elif action_type == ReviewAction.ESCALATE:
            new_status = ReviewStatus.ESCALATED
            # Reassign to higher authority
            self._escalate_workflow(workflow_id)
        
        elif action_type in [ReviewAction.DEFER, ReviewAction.DELEGATE]:
            new_status = ReviewStatus.PENDING
        
        # Update workflow in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = ["status = ?"]
        update_values = [new_status.value]
        
        if completed_at:
            update_fields.append("completed_at = ?")
            update_values.append(completed_at.isoformat())
        
        update_values.append(workflow_id)
        
        cursor.execute(f'''
            UPDATE review_workflows
            SET {', '.join(update_fields)}
            WHERE workflow_id = ?
        ''', update_values)
        
        conn.commit()
        conn.close()
    
    def _are_all_reviews_complete(self, workflow_id: str) -> bool:
        """Check if all required reviews are complete for workflow"""
        
        workflow = self._get_workflow_by_id(workflow_id)
        if not workflow:
            return False
        
        # Get all approval actions for this workflow
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(DISTINCT reviewer_id) as approvals
            FROM review_actions
            WHERE workflow_id = ? AND action_type = 'approve'
        ''', (workflow_id,))
        
        result = cursor.fetchone()
        approval_count = result[0] if result else 0
        
        conn.close()
        
        # Check if minimum reviewers threshold is met
        return approval_count >= workflow.minimum_reviewers
    
    def get_attorney_review_dashboard(
        self,
        attorney_id: str,
        include_requested: bool = True,
        include_assigned: bool = True,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get attorney review dashboard with workflow status"""
        
        start_date = datetime.now() - timedelta(days=days_back)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        dashboard = {
            "attorney_id": attorney_id,
            "dashboard_date": datetime.now().isoformat(),
            "period_days": days_back,
            "workflows_requested": [],
            "workflows_assigned": [],
            "pending_reviews": 0,
            "completed_reviews": 0,
            "overdue_reviews": 0,
            "average_review_time_hours": 0.0,
            "approval_rate": 0.0,
            "summary_stats": {}
        }
        
        # Get workflows requested by attorney
        if include_requested:
            cursor.execute('''
                SELECT * FROM review_workflows
                WHERE requester_id = ? AND created_at >= ?
                ORDER BY created_at DESC
            ''', (attorney_id, start_date.isoformat()))
            
            requested_workflows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            for workflow_data in requested_workflows:
                workflow_dict = dict(zip(columns, workflow_data))
                dashboard["workflows_requested"].append(workflow_dict)
        
        # Get workflows assigned to attorney
        if include_assigned:
            cursor.execute('''
                SELECT * FROM review_workflows
                WHERE assigned_reviewers LIKE ? AND created_at >= ?
                ORDER BY due_date ASC
            ''', (f'%{attorney_id}%', start_date.isoformat()))
            
            assigned_workflows = cursor.fetchall()
            for workflow_data in assigned_workflows:
                workflow_dict = dict(zip(columns, workflow_data))
                dashboard["workflows_assigned"].append(workflow_dict)
                
                # Count pending/overdue
                if workflow_dict["status"] in ["pending", "in_progress"]:
                    dashboard["pending_reviews"] += 1
                    
                    due_date = datetime.fromisoformat(workflow_dict["due_date"]) if workflow_dict["due_date"] else None
                    if due_date and datetime.now() > due_date:
                        dashboard["overdue_reviews"] += 1
        
        # Get reviewer metrics
        cursor.execute('''
            SELECT 
                AVG(average_review_time_hours) as avg_time,
                AVG(approval_rate) as approval_rate,
                SUM(completed_reviews) as total_completed
            FROM review_metrics
            WHERE reviewer_id = ? AND metric_date >= ?
        ''', (attorney_id, start_date.date().isoformat()))
        
        metrics = cursor.fetchone()
        if metrics:
            dashboard["average_review_time_hours"] = metrics[0] or 0.0
            dashboard["approval_rate"] = metrics[1] or 0.0
            dashboard["completed_reviews"] = metrics[2] or 0
        
        conn.close()
        
        return dashboard
    
    def _start_workflow_monitor(self):
        """Start background workflow monitoring thread"""
        def monitor_workflows():
            while True:
                try:
                    self._check_overdue_workflows()
                    self._auto_escalate_workflows()
                    self._update_workflow_metrics()
                    time.sleep(3600)  # Check every hour
                except Exception as e:
                    self.logger.error(f"Workflow monitor error: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        monitor_thread = threading.Thread(target=monitor_workflows, daemon=True)
        monitor_thread.start()
    
    def _check_overdue_workflows(self):
        """Check for overdue workflows and send notifications"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find overdue workflows
        cursor.execute('''
            SELECT workflow_id, title, current_reviewer, due_date, priority
            FROM review_workflows
            WHERE status IN ('pending', 'in_progress') 
            AND due_date < ? 
        ''', (datetime.now().isoformat(),))
        
        overdue_workflows = cursor.fetchall()
        
        for workflow_data in overdue_workflows:
            workflow_id, title, current_reviewer, due_date, priority = workflow_data
            
            self.logger.warning(
                f"Overdue workflow detected: {workflow_id} - Title: {title} - "
                f"Due: {due_date} - Reviewer: {current_reviewer}"
            )
            
            # Send overdue notification
            self._notify_workflow_overdue(workflow_id, current_reviewer)
        
        conn.close()

# Global attorney review workflow manager instance
attorney_review_workflows = AttorneyReviewWorkflowManager()