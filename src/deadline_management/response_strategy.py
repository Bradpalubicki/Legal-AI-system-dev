"""
Automated response strategy generator for legal deadlines.
Creates comprehensive action plans, task lists, and strategic recommendations.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
from collections import defaultdict

from .deadline_extractor import ExtractedDeadline, DeadlineType, PriorityLevel, DeadlineStatus

logger = logging.getLogger(__name__)


class ResponseType(Enum):
    """Types of legal responses."""
    MOTION_PRACTICE = "motion_practice"
    DISCOVERY_RESPONSE = "discovery_response"
    BRIEF_FILING = "brief_filing"
    COURT_APPEARANCE = "court_appearance"
    DOCUMENT_PRODUCTION = "document_production"
    SETTLEMENT_NEGOTIATION = "settlement_negotiation"
    COMPLIANCE_ACTION = "compliance_action"
    APPEAL_FILING = "appeal_filing"
    PAYMENT_PROCESSING = "payment_processing"
    ADMINISTRATIVE_FILING = "administrative_filing"


class TaskType(Enum):
    """Types of tasks in response strategy."""
    RESEARCH = "research"
    DRAFTING = "drafting"
    REVIEW = "review"
    CLIENT_COMMUNICATION = "client_communication"
    DISCOVERY = "discovery"
    NEGOTIATION = "negotiation"
    FILING = "filing"
    SERVICE = "service"
    PREPARATION = "preparation"
    COORDINATION = "coordination"


class ResourceType(Enum):
    """Types of resources needed."""
    ATTORNEY_TIME = "attorney_time"
    PARALEGAL_TIME = "paralegal_time"
    EXPERT_WITNESS = "expert_witness"
    DOCUMENT_REVIEW = "document_review"
    RESEARCH_TOOLS = "research_tools"
    COURT_COSTS = "court_costs"
    SERVICE_FEES = "service_fees"
    TRAVEL_EXPENSES = "travel_expenses"


class StrategyRisk(Enum):
    """Risk levels for response strategies."""
    VERY_HIGH = "very_high"     # High likelihood of adverse outcome
    HIGH = "high"               # Significant risk if not handled properly
    MEDIUM = "medium"           # Manageable risk with proper execution
    LOW = "low"                 # Minimal risk
    VERY_LOW = "very_low"       # No significant risk


@dataclass
class Task:
    """Individual task within a response strategy."""
    task_id: str
    
    # Task details
    title: str
    description: str
    task_type: TaskType
    priority: PriorityLevel
    
    # Timing
    due_date: datetime
    estimated_hours: float
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    
    # Assignment and responsibility
    assigned_to: Optional[str] = None
    responsible_attorney: Optional[str] = None
    supervising_attorney: Optional[str] = None
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # Other task IDs
    blocks: List[str] = field(default_factory=list)      # Tasks that depend on this
    
    # Resources needed
    required_resources: List[ResourceType] = field(default_factory=list)
    estimated_cost: float = 0.0
    
    # Status and progress
    status: str = "pending"  # pending, in_progress, completed, blocked, cancelled
    progress_percentage: int = 0
    
    # Documentation
    deliverables: List[str] = field(default_factory=list)
    quality_checkpoints: List[str] = field(default_factory=list)
    notes: str = ""
    
    # Metadata
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)


@dataclass
class ResponseStrategy:
    """Comprehensive response strategy for a legal deadline."""
    strategy_id: str
    deadline_id: str
    
    # Strategy overview
    response_type: ResponseType
    strategy_name: str
    objective: str
    approach: str
    
    # Timeline and scheduling
    deadline_date: datetime
    recommended_start_date: datetime
    buffer_days: int
    total_estimated_hours: float
    
    # Tasks and workflow
    tasks: List[Task] = field(default_factory=list)
    critical_path: List[str] = field(default_factory=list)  # Task IDs in critical path
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    
    # Risk assessment
    overall_risk: StrategyRisk
    risk_factors: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    contingency_plans: List[str] = field(default_factory=list)
    
    # Resource planning
    total_estimated_cost: float = 0.0
    resource_requirements: Dict[ResourceType, float] = field(default_factory=dict)
    key_personnel: List[str] = field(default_factory=list)
    
    # Quality and compliance
    quality_standards: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)
    review_checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    
    # Communication plan
    client_communication_plan: List[str] = field(default_factory=list)
    opposing_counsel_interactions: List[str] = field(default_factory=list)
    court_interactions: List[str] = field(default_factory=list)
    
    # Success metrics
    success_criteria: List[str] = field(default_factory=list)
    key_performance_indicators: Dict[str, str] = field(default_factory=dict)
    
    # Alternative strategies
    alternative_approaches: List[str] = field(default_factory=list)
    fallback_options: List[str] = field(default_factory=list)
    
    # Metadata
    created_by: Optional[str] = None
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def get_critical_path_tasks(self) -> List[Task]:
        """Get tasks on the critical path."""
        return [self.get_task_by_id(task_id) for task_id in self.critical_path 
                if self.get_task_by_id(task_id)]
    
    def calculate_total_duration(self) -> int:
        """Calculate total strategy duration in days."""
        if not self.tasks:
            return 0
        
        start_dates = [task.start_date or self.recommended_start_date for task in self.tasks]
        due_dates = [task.due_date for task in self.tasks]
        
        earliest_start = min(start_dates)
        latest_due = max(due_dates)
        
        return (latest_due - earliest_start).days
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get tasks filtered by status."""
        return [task for task in self.tasks if task.status == status]
    
    def get_overdue_tasks(self) -> List[Task]:
        """Get tasks that are overdue."""
        now = datetime.utcnow()
        return [task for task in self.tasks 
                if task.due_date < now and task.status not in ["completed", "cancelled"]]


@dataclass
class StrategyRecommendation:
    """Recommendation for response strategy."""
    recommendation_id: str
    deadline_id: str
    
    # Recommendation details
    title: str
    description: str
    rationale: str
    confidence_score: float
    
    # Impact assessment
    potential_outcomes: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    
    # Implementation guidance
    implementation_steps: List[str] = field(default_factory=list)
    required_resources: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_time: float = 0.0
    
    # Priority and timing
    urgency: PriorityLevel = PriorityLevel.MEDIUM
    recommended_timing: Optional[datetime] = None
    
    # Supporting information
    legal_authority: List[str] = field(default_factory=list)
    precedent_cases: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    
    # Metadata
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)


class ResponseStrategyGenerator:
    """Generates comprehensive response strategies for legal deadlines."""
    
    def __init__(self):
        """Initialize response strategy generator."""
        
        # Strategy templates for different deadline types
        self._initialize_strategy_templates()
        
        # Task libraries
        self._initialize_task_libraries()
        
        # Resource and cost estimates
        self._initialize_cost_estimates()
        
        # Risk assessment frameworks
        self._initialize_risk_frameworks()
        
        # Best practices database
        self._initialize_best_practices()
    
    def _initialize_strategy_templates(self):
        """Initialize strategy templates for different deadline types."""
        
        self.strategy_templates = {
            DeadlineType.RESPONSE: {
                'response_type': ResponseType.MOTION_PRACTICE,
                'default_buffer_days': 7,
                'typical_hours': 20,
                'key_tasks': [
                    'analyze_claims_and_defenses',
                    'research_applicable_law',
                    'draft_response',
                    'client_review_and_approval',
                    'file_and_serve_response'
                ]
            },
            DeadlineType.MOTION: {
                'response_type': ResponseType.MOTION_PRACTICE,
                'default_buffer_days': 10,
                'typical_hours': 35,
                'key_tasks': [
                    'research_legal_standards',
                    'analyze_factual_basis',
                    'draft_motion_and_brief',
                    'prepare_supporting_documents',
                    'file_motion_and_schedule_hearing'
                ]
            },
            DeadlineType.DISCOVERY: {
                'response_type': ResponseType.DISCOVERY_RESPONSE,
                'default_buffer_days': 5,
                'typical_hours': 25,
                'key_tasks': [
                    'analyze_discovery_requests',
                    'identify_responsive_documents',
                    'prepare_responses_and_objections',
                    'coordinate_document_production',
                    'serve_discovery_responses'
                ]
            },
            DeadlineType.APPEAL: {
                'response_type': ResponseType.APPEAL_FILING,
                'default_buffer_days': 14,
                'typical_hours': 60,
                'key_tasks': [
                    'analyze_appealable_issues',
                    'prepare_record_on_appeal',
                    'research_appellate_law',
                    'draft_appellate_brief',
                    'file_notice_of_appeal'
                ]
            },
            DeadlineType.HEARING: {
                'response_type': ResponseType.COURT_APPEARANCE,
                'default_buffer_days': 7,
                'typical_hours': 15,
                'key_tasks': [
                    'prepare_hearing_materials',
                    'coordinate_witness_availability',
                    'prepare_oral_argument',
                    'file_pre_hearing_documents',
                    'appear_at_hearing'
                ]
            }
        }
    
    def _initialize_task_libraries(self):
        """Initialize libraries of common legal tasks."""
        
        self.task_library = {
            # Research tasks
            'legal_research': {
                'type': TaskType.RESEARCH,
                'typical_hours': 8,
                'description': 'Research applicable law and precedents',
                'deliverables': ['Legal research memo', 'Case law summary'],
                'resources': [ResourceType.ATTORNEY_TIME, ResourceType.RESEARCH_TOOLS]
            },
            'fact_investigation': {
                'type': TaskType.RESEARCH,
                'typical_hours': 12,
                'description': 'Investigate and analyze relevant facts',
                'deliverables': ['Fact summary', 'Evidence inventory'],
                'resources': [ResourceType.ATTORNEY_TIME, ResourceType.PARALEGAL_TIME]
            },
            
            # Drafting tasks
            'draft_motion': {
                'type': TaskType.DRAFTING,
                'typical_hours': 12,
                'description': 'Draft motion and supporting brief',
                'deliverables': ['Motion document', 'Supporting brief'],
                'resources': [ResourceType.ATTORNEY_TIME]
            },
            'draft_response': {
                'type': TaskType.DRAFTING,
                'typical_hours': 10,
                'description': 'Draft response to motion or complaint',
                'deliverables': ['Response document'],
                'resources': [ResourceType.ATTORNEY_TIME]
            },
            'draft_discovery_responses': {
                'type': TaskType.DRAFTING,
                'typical_hours': 8,
                'description': 'Prepare responses to discovery requests',
                'deliverables': ['Discovery responses', 'Document production'],
                'resources': [ResourceType.ATTORNEY_TIME, ResourceType.PARALEGAL_TIME]
            },
            
            # Review tasks
            'client_review': {
                'type': TaskType.REVIEW,
                'typical_hours': 2,
                'description': 'Client review and approval of documents',
                'deliverables': ['Client approval'],
                'resources': [ResourceType.ATTORNEY_TIME]
            },
            'document_review': {
                'type': TaskType.REVIEW,
                'typical_hours': 20,
                'description': 'Review documents for privilege and relevance',
                'deliverables': ['Privilege log', 'Document production'],
                'resources': [ResourceType.ATTORNEY_TIME, ResourceType.PARALEGAL_TIME]
            },
            
            # Filing and service tasks
            'file_documents': {
                'type': TaskType.FILING,
                'typical_hours': 1,
                'description': 'File documents with court',
                'deliverables': ['Filed documents', 'Proof of service'],
                'resources': [ResourceType.PARALEGAL_TIME, ResourceType.COURT_COSTS]
            },
            'serve_documents': {
                'type': TaskType.SERVICE,
                'typical_hours': 1,
                'description': 'Serve documents on opposing parties',
                'deliverables': ['Proof of service'],
                'resources': [ResourceType.PARALEGAL_TIME, ResourceType.SERVICE_FEES]
            }
        }
    
    def _initialize_cost_estimates(self):
        """Initialize cost estimation data."""
        
        # Hourly rates by role
        self.hourly_rates = {
            ResourceType.ATTORNEY_TIME: 400.0,
            ResourceType.PARALEGAL_TIME: 150.0,
            ResourceType.DOCUMENT_REVIEW: 75.0
        }
        
        # Fixed costs
        self.fixed_costs = {
            ResourceType.COURT_COSTS: 350.0,
            ResourceType.SERVICE_FEES: 75.0,
            ResourceType.EXPERT_WITNESS: 5000.0,
            ResourceType.RESEARCH_TOOLS: 500.0
        }
    
    def _initialize_risk_frameworks(self):
        """Initialize risk assessment frameworks."""
        
        self.risk_factors = {
            'tight_timeline': {
                'description': 'Very tight deadline with minimal buffer time',
                'impact': StrategyRisk.HIGH,
                'mitigation': ['Add additional resources', 'Work extended hours', 'Prioritize critical tasks']
            },
            'complex_legal_issues': {
                'description': 'Complex or novel legal issues requiring extensive research',
                'impact': StrategyRisk.MEDIUM,
                'mitigation': ['Engage legal experts', 'Conduct thorough research', 'Prepare alternative arguments']
            },
            'large_document_volume': {
                'description': 'Large volume of documents to review or produce',
                'impact': StrategyRisk.MEDIUM,
                'mitigation': ['Use document review technology', 'Engage additional reviewers', 'Implement systematic review process']
            },
            'uncooperative_opposing_party': {
                'description': 'Opposing party likely to be uncooperative or obstructionist',
                'impact': StrategyRisk.MEDIUM,
                'mitigation': ['Prepare for motions practice', 'Document all communications', 'Seek court intervention if necessary']
            },
            'critical_deadline': {
                'description': 'Jurisdictional or case-ending deadline',
                'impact': StrategyRisk.VERY_HIGH,
                'mitigation': ['Multiple backup plans', 'Assign senior attorneys', 'Daily progress monitoring']
            }
        }
    
    def _initialize_best_practices(self):
        """Initialize best practices database."""
        
        self.best_practices = {
            DeadlineType.MOTION: [
                'Start work immediately upon receiving deadline',
                'Research thoroughly before drafting',
                'Allow time for multiple review cycles',
                'Prepare for oral argument even if not scheduled',
                'File motion with sufficient time for response and reply'
            ],
            DeadlineType.DISCOVERY: [
                'Meet and confer before filing motions to compel',
                'Use technology for efficient document review',
                'Maintain detailed privilege logs',
                'Coordinate with client early in process',
                'Preserve electronic data immediately'
            ],
            DeadlineType.APPEAL: [
                'Analyze appealability before filing notice',
                'Perfect the record meticulously',
                'Focus on strongest appellate issues',
                'Follow appellate court rules precisely',
                'Consider settlement during appeal process'
            ]
        }
    
    def generate_strategy(self, deadline: ExtractedDeadline, 
                         context: Dict[str, Any] = None) -> ResponseStrategy:
        """Generate comprehensive response strategy for a deadline.
        
        Args:
            deadline: Extracted deadline requiring response
            context: Additional context about case, client, resources
            
        Returns:
            Complete response strategy
        """
        logger.info(f"Generating response strategy for deadline: {deadline.deadline_id}")
        
        context = context or {}
        
        # Get strategy template
        template = self.strategy_templates.get(deadline.deadline_type, {})
        
        # Create base strategy
        strategy = self._create_base_strategy(deadline, template, context)
        
        # Generate tasks
        strategy.tasks = self._generate_tasks(deadline, template, context)
        
        # Calculate critical path
        strategy.critical_path = self._calculate_critical_path(strategy.tasks)
        
        # Assess risks
        strategy.overall_risk, strategy.risk_factors = self._assess_risks(deadline, strategy, context)
        
        # Generate mitigation strategies
        strategy.mitigation_strategies = self._generate_mitigation_strategies(strategy.risk_factors)
        
        # Calculate resource requirements
        strategy.resource_requirements, strategy.total_estimated_cost = self._calculate_resources(strategy.tasks)
        
        # Create milestones
        strategy.milestones = self._create_milestones(strategy.tasks)
        
        # Generate quality and compliance requirements
        strategy.quality_standards = self._generate_quality_standards(deadline.deadline_type)
        strategy.compliance_requirements = self._generate_compliance_requirements(deadline, context)
        
        # Create communication plan
        strategy.client_communication_plan = self._create_communication_plan(deadline, context)
        
        # Define success criteria
        strategy.success_criteria = self._define_success_criteria(deadline, context)
        
        # Generate alternatives
        strategy.alternative_approaches = self._generate_alternatives(deadline, context)
        
        return strategy
    
    def _create_base_strategy(self, deadline: ExtractedDeadline, 
                             template: Dict[str, Any], 
                             context: Dict[str, Any]) -> ResponseStrategy:
        """Create base response strategy."""
        
        # Calculate timing
        buffer_days = template.get('default_buffer_days', 7)
        recommended_start = deadline.date - timedelta(days=buffer_days + 3)  # Additional safety margin
        
        # Generate strategy name and objective
        strategy_name = f"Response Strategy: {deadline.description}"
        objective = f"Successfully complete {deadline.action_required} by {deadline.date.strftime('%B %d, %Y')}"
        
        return ResponseStrategy(
            strategy_id=f"strategy_{deadline.deadline_id}_{int(datetime.utcnow().timestamp())}",
            deadline_id=deadline.deadline_id,
            response_type=template.get('response_type', ResponseType.MOTION_PRACTICE),
            strategy_name=strategy_name,
            objective=objective,
            approach=self._generate_approach(deadline, template, context),
            deadline_date=deadline.date,
            recommended_start_date=max(recommended_start, datetime.utcnow()),
            buffer_days=buffer_days,
            total_estimated_hours=template.get('typical_hours', 20),
            created_by=context.get('attorney_name', 'System')
        )
    
    def _generate_approach(self, deadline: ExtractedDeadline, 
                          template: Dict[str, Any], 
                          context: Dict[str, Any]) -> str:
        """Generate strategic approach description."""
        
        approaches = {
            DeadlineType.RESPONSE: "Analyze claims thoroughly, research applicable defenses, and prepare comprehensive response addressing all allegations while preserving client's rights.",
            DeadlineType.MOTION: "Research legal standards, analyze factual record, and prepare persuasive motion with strong supporting arguments and comprehensive brief.",
            DeadlineType.DISCOVERY: "Systematically review requests, identify responsive materials, prepare appropriate objections, and coordinate efficient document production.",
            DeadlineType.APPEAL: "Identify strongest appellate issues, perfect the record, research appellate standards, and prepare compelling brief focused on reversible error.",
            DeadlineType.HEARING: "Prepare comprehensive materials, coordinate all participants, develop strong oral presentation, and anticipate court questions."
        }
        
        base_approach = approaches.get(deadline.deadline_type, "Develop comprehensive strategy to meet deadline requirements effectively.")
        
        # Add context-specific elements
        if context.get('case_complexity') == 'high':
            base_approach += " Given case complexity, employ additional research and expert consultation."
        
        if deadline.priority == PriorityLevel.CRITICAL:
            base_approach += " Critical deadline requires expedited timeline and additional quality controls."
        
        return base_approach
    
    def _generate_tasks(self, deadline: ExtractedDeadline, 
                       template: Dict[str, Any], 
                       context: Dict[str, Any]) -> List[Task]:
        """Generate detailed task list for strategy."""
        
        tasks = []
        task_sequence = template.get('key_tasks', [])
        
        # Calculate task timing
        total_days = (deadline.date - datetime.utcnow()).days
        buffer_days = template.get('default_buffer_days', 7)
        work_days = max(1, total_days - buffer_days)
        
        # Generate tasks based on deadline type
        for i, task_key in enumerate(task_sequence):
            task_template = self.task_library.get(task_key, {})
            
            # Calculate task timing
            task_duration = task_template.get('typical_hours', 8) / 8  # Convert to days
            start_offset = (work_days * i) / len(task_sequence)
            
            task_start = datetime.utcnow() + timedelta(days=int(start_offset))
            task_due = task_start + timedelta(days=int(task_duration))
            
            # Create task
            task = Task(
                task_id=f"task_{deadline.deadline_id}_{i+1}",
                title=task_key.replace('_', ' ').title(),
                description=task_template.get('description', f'Complete {task_key}'),
                task_type=task_template.get('type', TaskType.PREPARATION),
                priority=deadline.priority,
                due_date=task_due,
                start_date=task_start,
                estimated_hours=task_template.get('typical_hours', 8),
                required_resources=task_template.get('resources', []),
                deliverables=task_template.get('deliverables', []),
                assigned_to=context.get('primary_attorney', 'TBD'),
                responsible_attorney=context.get('primary_attorney', 'TBD')
            )
            
            # Set dependencies (sequential by default)
            if i > 0:
                task.depends_on = [tasks[i-1].task_id]
                tasks[i-1].blocks = [task.task_id]
            
            # Add quality checkpoints
            if task.task_type in [TaskType.DRAFTING, TaskType.FILING]:
                task.quality_checkpoints = ['Initial draft review', 'Final quality check', 'Client approval']
            
            tasks.append(task)
        
        # Add buffer task
        if buffer_days > 0:
            buffer_task = Task(
                task_id=f"task_{deadline.deadline_id}_buffer",
                title="Final Review and Buffer",
                description="Final review period and buffer for unexpected issues",
                task_type=TaskType.REVIEW,
                priority=deadline.priority,
                due_date=deadline.date - timedelta(days=1),
                start_date=deadline.date - timedelta(days=buffer_days),
                estimated_hours=4,
                assigned_to=context.get('supervising_attorney', context.get('primary_attorney', 'TBD'))
            )
            
            if tasks:
                buffer_task.depends_on = [tasks[-1].task_id]
                tasks[-1].blocks = [buffer_task.task_id]
            
            tasks.append(buffer_task)
        
        return tasks
    
    def _calculate_critical_path(self, tasks: List[Task]) -> List[str]:
        """Calculate critical path through task network."""
        
        # Simple implementation - longest path through dependencies
        # In practice, would use more sophisticated CPM algorithm
        
        if not tasks:
            return []
        
        # Find tasks with no dependencies (starting points)
        start_tasks = [t for t in tasks if not t.depends_on]
        
        if not start_tasks:
            # If all tasks have dependencies, start with first task
            start_tasks = [tasks[0]]
        
        # Follow longest path
        critical_path = []
        current_tasks = start_tasks
        
        while current_tasks:
            # Find task with longest remaining path
            longest_task = max(current_tasks, key=lambda t: t.estimated_hours)
            critical_path.append(longest_task.task_id)
            
            # Find next tasks
            next_tasks = [t for t in tasks if longest_task.task_id in t.depends_on]
            current_tasks = next_tasks
        
        return critical_path
    
    def _assess_risks(self, deadline: ExtractedDeadline, 
                     strategy: ResponseStrategy, 
                     context: Dict[str, Any]) -> Tuple[StrategyRisk, List[str]]:
        """Assess risks for the strategy."""
        
        risk_factors = []
        risk_scores = []
        
        # Timeline risk
        days_until = (deadline.date - datetime.utcnow()).days
        if days_until < 7:
            risk_factors.append("tight_timeline")
            risk_scores.append(4)
        elif days_until < 14:
            risk_factors.append("moderate_timeline_pressure")
            risk_scores.append(3)
        
        # Complexity risk
        if context.get('case_complexity') == 'high':
            risk_factors.append("complex_legal_issues")
            risk_scores.append(3)
        
        # Resource risk
        if strategy.total_estimated_hours > 40:
            risk_factors.append("high_resource_requirements")
            risk_scores.append(2)
        
        # Priority risk
        if deadline.priority == PriorityLevel.CRITICAL:
            risk_factors.append("critical_deadline")
            risk_scores.append(4)
        
        # Stakeholder risk
        if context.get('opposing_counsel_cooperation') == 'low':
            risk_factors.append("uncooperative_opposing_party")
            risk_scores.append(3)
        
        # Calculate overall risk
        if not risk_scores:
            overall_risk = StrategyRisk.LOW
        else:
            avg_score = sum(risk_scores) / len(risk_scores)
            if avg_score >= 4:
                overall_risk = StrategyRisk.VERY_HIGH
            elif avg_score >= 3:
                overall_risk = StrategyRisk.HIGH
            elif avg_score >= 2:
                overall_risk = StrategyRisk.MEDIUM
            else:
                overall_risk = StrategyRisk.LOW
        
        return overall_risk, risk_factors
    
    def _generate_mitigation_strategies(self, risk_factors: List[str]) -> List[str]:
        """Generate risk mitigation strategies."""
        
        mitigations = []
        
        for risk_factor in risk_factors:
            if risk_factor in self.risk_factors:
                mitigations.extend(self.risk_factors[risk_factor]['mitigation'])
        
        # Add general mitigations
        mitigations.extend([
            "Maintain daily progress monitoring",
            "Prepare contingency plans for delays",
            "Establish clear communication protocols",
            "Document all decisions and rationale"
        ])
        
        return list(set(mitigations))  # Remove duplicates
    
    def _calculate_resources(self, tasks: List[Task]) -> Tuple[Dict[ResourceType, float], float]:
        """Calculate resource requirements and total cost."""
        
        resource_totals = defaultdict(float)
        total_cost = 0.0
        
        for task in tasks:
            # Add hours for different resource types
            for resource in task.required_resources:
                if resource in [ResourceType.ATTORNEY_TIME, ResourceType.PARALEGAL_TIME, 
                              ResourceType.DOCUMENT_REVIEW]:
                    resource_totals[resource] += task.estimated_hours
                else:
                    resource_totals[resource] += 1.0  # Count of fixed resources
        
        # Calculate costs
        for resource, quantity in resource_totals.items():
            if resource in self.hourly_rates:
                total_cost += quantity * self.hourly_rates[resource]
            elif resource in self.fixed_costs:
                total_cost += quantity * self.fixed_costs[resource]
        
        return dict(resource_totals), total_cost
    
    def _create_milestones(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """Create project milestones."""
        
        milestones = []
        
        # Key milestone points
        milestone_tasks = [
            TaskType.RESEARCH,
            TaskType.DRAFTING,
            TaskType.REVIEW,
            TaskType.FILING
        ]
        
        for milestone_type in milestone_tasks:
            milestone_task = next((t for t in tasks if t.task_type == milestone_type), None)
            if milestone_task:
                milestones.append({
                    'name': f"{milestone_type.value.title()} Complete",
                    'date': milestone_task.due_date.isoformat(),
                    'description': f"Completion of {milestone_type.value} phase",
                    'task_id': milestone_task.task_id,
                    'deliverables': milestone_task.deliverables
                })
        
        return milestones
    
    def _generate_quality_standards(self, deadline_type: DeadlineType) -> List[str]:
        """Generate quality standards for deadline type."""
        
        base_standards = [
            "All work product reviewed by supervising attorney",
            "Client consultation on major strategic decisions",
            "Compliance with all applicable rules and procedures",
            "Timely filing with adequate buffer for unexpected issues"
        ]
        
        type_specific = {
            DeadlineType.MOTION: [
                "Motion supported by strong legal authority",
                "Factual allegations supported by evidence",
                "Brief follows court's preferred format and length limits"
            ],
            DeadlineType.DISCOVERY: [
                "All objections properly stated and supported",
                "Privilege claims adequately documented",
                "Production organized and clearly indexed"
            ],
            DeadlineType.APPEAL: [
                "Record citations accurate and complete",
                "Appellate brief complies with all formatting rules",
                "Issues presented clearly and persuasively"
            ]
        }
        
        return base_standards + type_specific.get(deadline_type, [])
    
    def _generate_compliance_requirements(self, deadline: ExtractedDeadline, 
                                        context: Dict[str, Any]) -> List[str]:
        """Generate compliance requirements."""
        
        requirements = [
            "Meet all statutory and rule-based deadlines",
            "Comply with local court rules and procedures",
            "Maintain client confidentiality throughout process"
        ]
        
        # Add jurisdiction-specific requirements
        jurisdiction = deadline.jurisdiction or context.get('jurisdiction', 'federal')
        if jurisdiction == 'california':
            requirements.append("Comply with California Rules of Court")
        elif jurisdiction == 'new_york':
            requirements.append("Comply with CPLR requirements")
        
        # Add deadline-specific requirements
        if deadline.deadline_type == DeadlineType.DISCOVERY:
            requirements.extend([
                "Meet and confer before filing motions to compel",
                "Maintain privilege logs for all withheld documents"
            ])
        elif deadline.deadline_type == DeadlineType.APPEAL:
            requirements.extend([
                "Perfect appeal within statutory time limits",
                "Comply with appellate court formatting requirements"
            ])
        
        return requirements
    
    def _create_communication_plan(self, deadline: ExtractedDeadline, 
                                  context: Dict[str, Any]) -> List[str]:
        """Create client communication plan."""
        
        plan = [
            "Initial strategy discussion with client",
            "Regular progress updates during work",
            "Review of key documents before filing",
            "Post-deadline summary and next steps discussion"
        ]
        
        # Add priority-based communications
        if deadline.priority == PriorityLevel.CRITICAL:
            plan.insert(1, "Daily progress updates given critical nature")
        
        # Add deadline-specific communications
        if deadline.deadline_type == DeadlineType.MOTION:
            plan.append("Preparation for potential oral argument")
        elif deadline.deadline_type == DeadlineType.SETTLEMENT:
            plan.append("Strategy discussion for settlement negotiations")
        
        return plan
    
    def _define_success_criteria(self, deadline: ExtractedDeadline, 
                               context: Dict[str, Any]) -> List[str]:
        """Define success criteria for strategy."""
        
        criteria = [
            "Deadline met with all required actions completed",
            "High-quality work product delivered",
            "Client objectives advanced",
            "Budget and timeline adhered to"
        ]
        
        # Add deadline-specific criteria
        type_specific = {
            DeadlineType.MOTION: [
                "Motion granted or achieves settlement leverage",
                "Strong factual and legal arguments presented"
            ],
            DeadlineType.DISCOVERY: [
                "All responsive documents properly produced",
                "Objections sustained where appropriate"
            ],
            DeadlineType.APPEAL: [
                "Appeal perfected and briefed effectively",
                "Strong chance of reversal or favorable settlement"
            ]
        }
        
        criteria.extend(type_specific.get(deadline.deadline_type, []))
        
        return criteria
    
    def _generate_alternatives(self, deadline: ExtractedDeadline, 
                             context: Dict[str, Any]) -> List[str]:
        """Generate alternative approaches."""
        
        alternatives = []
        
        # General alternatives
        alternatives.extend([
            "Seek extension of deadline if grounds exist",
            "Negotiate with opposing counsel for modified timeline",
            "Consider settlement to avoid deadline pressure"
        ])
        
        # Deadline-specific alternatives
        if deadline.deadline_type == DeadlineType.MOTION:
            alternatives.extend([
                "File motion with limited briefing and request hearing",
                "Consider dispositive motion instead of discovery motion"
            ])
        elif deadline.deadline_type == DeadlineType.DISCOVERY:
            alternatives.extend([
                "Produce documents in phases with court approval",
                "Seek protective order for sensitive information"
            ])
        elif deadline.deadline_type == DeadlineType.APPEAL:
            alternatives.extend([
                "Consider interlocutory appeal if available",
                "Explore settlement before appeal briefing"
            ])
        
        return alternatives
    
    def generate_recommendations(self, deadline: ExtractedDeadline, 
                               strategies: List[ResponseStrategy]) -> List[StrategyRecommendation]:
        """Generate strategic recommendations."""
        
        recommendations = []
        
        # Analyze strategies and generate recommendations
        for strategy in strategies:
            # Timing recommendation
            if (strategy.deadline_date - datetime.utcnow()).days < strategy.buffer_days:
                rec = StrategyRecommendation(
                    recommendation_id=f"rec_timing_{strategy.strategy_id}",
                    deadline_id=deadline.deadline_id,
                    title="Immediate Action Required",
                    description="Deadline approaching with insufficient buffer time",
                    rationale="Current timeline leaves minimal room for unexpected delays or revisions",
                    confidence_score=0.9,
                    urgency=PriorityLevel.CRITICAL,
                    implementation_steps=[
                        "Begin work immediately",
                        "Assign additional resources if available",
                        "Prepare contingency plans",
                        "Consider seeking extension if appropriate"
                    ]
                )
                recommendations.append(rec)
            
            # Resource recommendation
            if strategy.total_estimated_cost > 10000:
                rec = StrategyRecommendation(
                    recommendation_id=f"rec_resources_{strategy.strategy_id}",
                    deadline_id=deadline.deadline_id,
                    title="Significant Resource Commitment",
                    description=f"Strategy requires substantial resources (${strategy.total_estimated_cost:,.2f})",
                    rationale="High cost may warrant discussion of alternatives or phased approach",
                    confidence_score=0.8,
                    urgency=PriorityLevel.HIGH,
                    implementation_steps=[
                        "Discuss budget with client",
                        "Consider phased approach",
                        "Explore cost-saving alternatives",
                        "Obtain client authorization for expenses"
                    ]
                )
                recommendations.append(rec)
            
            # Risk recommendation
            if strategy.overall_risk in [StrategyRisk.HIGH, StrategyRisk.VERY_HIGH]:
                rec = StrategyRecommendation(
                    recommendation_id=f"rec_risk_{strategy.strategy_id}",
                    deadline_id=deadline.deadline_id,
                    title="High Risk Strategy",
                    description="Strategy carries significant risk of adverse outcomes",
                    rationale="Multiple risk factors present require careful management and contingency planning",
                    confidence_score=0.85,
                    urgency=PriorityLevel.HIGH,
                    implementation_steps=[
                        "Implement all mitigation strategies",
                        "Develop comprehensive contingency plans",
                        "Increase supervision and quality control",
                        "Consider alternative approaches"
                    ]
                )
                recommendations.append(rec)
        
        return recommendations
    
    def update_strategy_progress(self, strategy_id: str, task_updates: Dict[str, Dict[str, Any]]) -> bool:
        """Update progress on strategy tasks."""
        
        # This would integrate with project management system
        # For now, return placeholder
        logger.info(f"Updating strategy progress: {strategy_id}")
        return True
    
    def export_strategy(self, strategy: ResponseStrategy, format: str = "json") -> str:
        """Export strategy in specified format."""
        
        if format.lower() == "json":
            # Convert to JSON-serializable format
            data = {
                "strategy_id": strategy.strategy_id,
                "deadline_id": strategy.deadline_id,
                "strategy_name": strategy.strategy_name,
                "objective": strategy.objective,
                "response_type": strategy.response_type.value,
                "deadline_date": strategy.deadline_date.isoformat(),
                "recommended_start_date": strategy.recommended_start_date.isoformat(),
                "buffer_days": strategy.buffer_days,
                "total_estimated_hours": strategy.total_estimated_hours,
                "total_estimated_cost": strategy.total_estimated_cost,
                "overall_risk": strategy.overall_risk.value,
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "title": task.title,
                        "description": task.description,
                        "task_type": task.task_type.value,
                        "priority": task.priority.value,
                        "due_date": task.due_date.isoformat(),
                        "estimated_hours": task.estimated_hours,
                        "assigned_to": task.assigned_to,
                        "status": task.status,
                        "deliverables": task.deliverables,
                        "depends_on": task.depends_on
                    }
                    for task in strategy.tasks
                ],
                "critical_path": strategy.critical_path,
                "milestones": strategy.milestones,
                "risk_factors": strategy.risk_factors,
                "mitigation_strategies": strategy.mitigation_strategies,
                "success_criteria": strategy.success_criteria,
                "creation_timestamp": strategy.creation_timestamp.isoformat()
            }
            
            return json.dumps(data, indent=2, default=str)
            
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_strategy_statistics(self) -> Dict[str, Any]:
        """Get strategy generator statistics."""
        
        return {
            "supported_deadline_types": [dt.value for dt in DeadlineType],
            "response_types": [rt.value for rt in ResponseType],
            "task_types": [tt.value for tt in TaskType],
            "resource_types": [rt.value for rt in ResourceType],
            "risk_levels": [sr.value for sr in StrategyRisk],
            "strategy_templates": len(self.strategy_templates),
            "task_library_size": len(self.task_library),
            "risk_factors": len(self.risk_factors),
            "best_practices": sum(len(practices) for practices in self.best_practices.values())
        }