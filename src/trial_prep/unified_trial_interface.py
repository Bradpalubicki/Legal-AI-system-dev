"""
Unified Trial Interface

Single interface layer providing unified access to all integrated trial
preparation systems with intelligent routing, consolidated reporting,
and seamless user experience across all components.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime, date, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
import logging
from pathlib import Path

from .integrated_trial_system import IntegratedTrialSystem, IntegrationEvent
from .trial_automation_workflows import TrialAutomationEngine, WorkflowType, AutomationTrigger
from .digital_trial_notebook import TrialDay, WitnessStatus, ExhibitAction

logger = logging.getLogger(__name__)

class InterfaceCommand(Enum):
    """Unified interface commands."""
    # Trial Management
    CREATE_TRIAL = "create_trial"
    GET_TRIAL_STATUS = "get_trial_status"
    START_TRIAL_DAY = "start_trial_day"
    END_TRIAL_DAY = "end_trial_day"
    
    # Witness Operations
    ADD_WITNESS = "add_witness"
    SCHEDULE_WITNESS = "schedule_witness"
    UPDATE_WITNESS_STATUS = "update_witness_status"
    GET_WITNESS_READINESS = "get_witness_readiness"
    
    # Exhibit Operations
    ADD_EXHIBIT = "add_exhibit"
    SCHEDULE_EXHIBIT = "schedule_exhibit"
    TRACK_EXHIBIT_ACTION = "track_exhibit_action"
    
    # Evidence Operations
    ADD_EVIDENCE = "add_evidence"
    LINK_EVIDENCE_EXHIBIT = "link_evidence_exhibit"
    
    # Document Operations
    GENERATE_DOCUMENT = "generate_document"
    GET_DOCUMENT_STATUS = "get_document_status"
    
    # Analysis Operations
    ANALYZE_CASE = "analyze_case"
    BUILD_TIMELINE = "build_timeline"
    ANALYZE_JURY = "analyze_jury"
    
    # Automation Operations
    CREATE_WORKFLOW = "create_workflow"
    EXECUTE_WORKFLOW = "execute_workflow"
    GET_AUTOMATION_RECOMMENDATIONS = "get_automation_recommendations"
    
    # Reporting Operations
    GENERATE_TRIAL_REPORT = "generate_trial_report"
    GET_DASHBOARD = "get_dashboard"
    SEARCH_TRIAL_DATA = "search_trial_data"

class ResponseStatus(Enum):
    """Status of interface responses."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PENDING = "pending"
    PARTIAL_SUCCESS = "partial_success"

@dataclass
class UnifiedCommand:
    """Unified command structure for all trial operations."""
    command_id: str
    command_type: InterfaceCommand
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 3  # 1-5 scale

@dataclass
class UnifiedResponse:
    """Unified response structure for all trial operations."""
    command_id: str
    status: ResponseStatus
    data: Dict[str, Any] = field(default_factory=dict)
    messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    execution_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

class TrialDashboard:
    """Consolidated trial dashboard with real-time status."""
    
    def __init__(self, integrated_system: IntegratedTrialSystem):
        self.integrated_system = integrated_system
        self.logger = logging.getLogger(__name__ + ".TrialDashboard")
    
    def generate_comprehensive_dashboard(self, trial_context_id: str) -> Dict[str, Any]:
        """Generate comprehensive trial dashboard."""
        dashboard = {
            'trial_overview': {},
            'current_status': {},
            'today_schedule': {},
            'witness_status': {},
            'exhibit_status': {},
            'document_status': {},
            'automation_status': {},
            'performance_metrics': {},
            'alerts_notifications': [],
            'quick_actions': [],
            'recent_activity': []
        }
        
        try:
            # Get trial context
            if trial_context_id not in self.integrated_system.data_integrator.trial_contexts:
                return {'error': 'Trial context not found'}
            
            context = self.integrated_system.data_integrator.trial_contexts[trial_context_id]
            
            # Trial overview
            if context.trial_notebook_id in self.integrated_system.digital_trial_notebook.trial_notebooks:
                notebook = self.integrated_system.digital_trial_notebook.trial_notebooks[context.trial_notebook_id]
                
                dashboard['trial_overview'] = {
                    'case_name': notebook.case_name,
                    'court': notebook.court,
                    'judge': notebook.judge,
                    'trial_start_date': notebook.trial_start_date,
                    'estimated_end_date': notebook.trial_end_date,
                    'total_trial_days': len(notebook.trial_days),
                    'completed_days': len([d for d in notebook.trial_days.values() if d.day_completed]),
                    'current_phase': context.trial_phase
                }
                
                # Current status
                current_day_plan = None
                if context.current_trial_day and context.current_trial_day in notebook.trial_days:
                    current_day_plan = notebook.trial_days[context.current_trial_day]
                
                dashboard['current_status'] = {
                    'current_trial_day': context.current_trial_day,
                    'day_type': current_day_plan.day_type.value if current_day_plan else None,
                    'day_objectives': current_day_plan.primary_objectives if current_day_plan else [],
                    'active_session': self._determine_current_session(current_day_plan) if current_day_plan else None
                }
                
                # Today's schedule
                if current_day_plan:
                    dashboard['today_schedule'] = self._generate_daily_schedule_summary(current_day_plan)
            
            # Witness status summary
            dashboard['witness_status'] = self._generate_witness_status_summary(context)
            
            # Exhibit status summary  
            dashboard['exhibit_status'] = self._generate_exhibit_status_summary(context)
            
            # Document status summary
            dashboard['document_status'] = self._generate_document_status_summary(context)
            
            # Performance metrics
            dashboard['performance_metrics'] = self._calculate_performance_metrics(context)
            
            # Alerts and notifications
            dashboard['alerts_notifications'] = self._generate_alerts_and_notifications(context)
            
            # Quick actions
            dashboard['quick_actions'] = self._generate_quick_actions(context)
            
            # Recent activity
            dashboard['recent_activity'] = self._generate_recent_activity(context)
            
        except Exception as e:
            dashboard['error'] = str(e)
            self.logger.error(f"Dashboard generation failed: {e}")
        
        return dashboard
    
    def _determine_current_session(self, trial_day_plan) -> Optional[str]:
        """Determine current session based on time."""
        current_time = datetime.now().time()
        
        if trial_day_plan.morning_session and trial_day_plan.morning_session.contains_time(current_time):
            return "morning_session"
        elif trial_day_plan.afternoon_session and trial_day_plan.afternoon_session.contains_time(current_time):
            return "afternoon_session"
        elif trial_day_plan.lunch_break and trial_day_plan.lunch_break.contains_time(current_time):
            return "lunch_break"
        
        return None
    
    def _generate_daily_schedule_summary(self, trial_day_plan) -> Dict[str, Any]:
        """Generate summary of daily schedule."""
        return {
            'witnesses_scheduled': len(trial_day_plan.witness_schedule),
            'exhibits_planned': len(trial_day_plan.exhibit_schedule),
            'next_witness': self._get_next_witness(trial_day_plan),
            'session_progress': self._calculate_session_progress(trial_day_plan),
            'estimated_completion': self._estimate_day_completion(trial_day_plan)
        }
    
    def _generate_witness_status_summary(self, context) -> Dict[str, Any]:
        """Generate witness status summary."""
        witnesses = self.integrated_system.witness_manager.witnesses
        
        status_counts = {}
        for witness in witnesses.values():
            status = witness.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_witnesses': len(witnesses),
            'status_breakdown': status_counts,
            'preparation_complete': len([w for w in witnesses.values() 
                                       if w.preparation_status.value == 'trial_ready']),
            'witnesses_today': len(context.active_witnesses)
        }
    
    def _generate_exhibit_status_summary(self, context) -> Dict[str, Any]:
        """Generate exhibit status summary."""
        exhibits = self.integrated_system.exhibit_manager.exhibits
        
        status_counts = {}
        for exhibit in exhibits.values():
            status = exhibit.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_exhibits': len(exhibits),
            'status_breakdown': status_counts,
            'authenticated': len([e for e in exhibits.values() 
                                if e.authentication and e.authentication.foundation_complete]),
            'exhibits_today': len(context.active_exhibits)
        }
    
    def _generate_document_status_summary(self, context) -> Dict[str, Any]:
        """Generate document status summary."""
        documents = self.integrated_system.document_generator.documents
        case_docs = [d for d in documents.values() if d.case_id == context.case_id]
        
        status_counts = {}
        for doc in case_docs:
            status = doc.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_documents': len(case_docs),
            'status_breakdown': status_counts,
            'pending_generation': len(self.integrated_system.document_generator.generation_requests),
            'ready_for_trial': len([d for d in case_docs if d.status.value == 'approved'])
        }
    
    def _calculate_performance_metrics(self, context) -> Dict[str, Any]:
        """Calculate trial performance metrics."""
        notebook = self.integrated_system.digital_trial_notebook.trial_notebooks.get(context.trial_notebook_id)
        
        metrics = {
            'trial_progress_percentage': 0.0,
            'average_daily_score': 0.0,
            'objective_completion_rate': 0.0,
            'efficiency_rating': 'N/A'
        }
        
        if notebook:
            # Trial progress
            completed_days = len([d for d in notebook.trial_days.values() if d.day_completed])
            total_days = len(notebook.trial_days)
            metrics['trial_progress_percentage'] = (completed_days / total_days * 100) if total_days > 0 else 0
            
            # Daily assessments
            if notebook.daily_assessments:
                scores = [a.get('assessment_score', 0) for a in notebook.daily_assessments if a.get('assessment_score')]
                if scores:
                    metrics['average_daily_score'] = sum(scores) / len(scores)
            
            # Objective completion
            total_objectives = 0
            completed_objectives = 0
            for day_plan in notebook.trial_days.values():
                total_objectives += len(day_plan.primary_objectives)
                completed_objectives += len(day_plan.objectives_achieved)
            
            if total_objectives > 0:
                metrics['objective_completion_rate'] = (completed_objectives / total_objectives * 100)
        
        return metrics
    
    def _generate_alerts_and_notifications(self, context) -> List[Dict[str, Any]]:
        """Generate alerts and notifications."""
        alerts = []
        
        # Check for critical deadlines
        # Check for unprepared witnesses
        # Check for missing documents
        # Check for technology requirements
        
        # Example alerts
        alerts.extend([
            {
                'type': 'deadline',
                'priority': 'high',
                'message': 'Jury instruction conference scheduled for tomorrow',
                'action_required': 'Review proposed instructions'
            },
            {
                'type': 'preparation',
                'priority': 'medium', 
                'message': '2 witnesses need final preparation review',
                'action_required': 'Schedule preparation sessions'
            }
        ])
        
        return alerts
    
    def _generate_quick_actions(self, context) -> List[Dict[str, Any]]:
        """Generate quick action items."""
        actions = []
        
        # Common quick actions based on current state
        if context.trial_phase == 'preparation':
            actions.extend([
                {'action': 'sync_all_systems', 'label': 'Sync All Systems', 'icon': 'sync'},
                {'action': 'check_witness_readiness', 'label': 'Check Witness Readiness', 'icon': 'users'},
                {'action': 'prepare_exhibits', 'label': 'Prepare Exhibits', 'icon': 'folder'},
                {'action': 'generate_daily_summary', 'label': 'Generate Daily Summary', 'icon': 'file-text'}
            ])
        elif context.trial_phase == 'active_trial':
            actions.extend([
                {'action': 'start_trial_day', 'label': 'Start Trial Day', 'icon': 'play'},
                {'action': 'track_witness', 'label': 'Track Witness', 'icon': 'user-check'},
                {'action': 'mark_exhibit', 'label': 'Mark Exhibit', 'icon': 'tag'},
                {'action': 'add_trial_note', 'label': 'Add Trial Note', 'icon': 'edit'}
            ])
        
        return actions
    
    def _generate_recent_activity(self, context) -> List[Dict[str, Any]]:
        """Generate recent activity log."""
        # Would pull from actual system logs
        activities = [
            {
                'timestamp': datetime.now() - timedelta(hours=1),
                'type': 'witness_update',
                'description': 'Updated witness John Smith preparation status to ready',
                'user': 'Attorney A'
            },
            {
                'timestamp': datetime.now() - timedelta(hours=2),
                'type': 'exhibit_prepared',
                'description': 'Exhibit P-15 authenticated and prepared for trial',
                'user': 'Paralegal B'
            },
            {
                'timestamp': datetime.now() - timedelta(hours=3),
                'type': 'document_generated',
                'description': 'Generated daily trial summary for Day 3',
                'user': 'System'
            }
        ]
        
        return activities
    
    def _get_next_witness(self, trial_day_plan) -> Optional[Dict[str, Any]]:
        """Get next scheduled witness."""
        current_time = datetime.now().time()
        
        for witness in trial_day_plan.witness_schedule:
            if witness.scheduled_time and witness.scheduled_time > current_time:
                return {
                    'witness_id': witness.witness_id,
                    'name': witness.witness_name,
                    'scheduled_time': witness.scheduled_time,
                    'examination_type': witness.examination_type,
                    'status': witness.status.value
                }
        
        return None
    
    def _calculate_session_progress(self, trial_day_plan) -> Dict[str, Any]:
        """Calculate session progress."""
        # Simplified calculation based on witness completion
        total_witnesses = len(trial_day_plan.witness_schedule)
        completed_witnesses = len([w for w in trial_day_plan.witness_schedule 
                                 if w.status == WitnessStatus.COMPLETED])
        
        progress_percentage = (completed_witnesses / total_witnesses * 100) if total_witnesses > 0 else 0
        
        return {
            'progress_percentage': progress_percentage,
            'completed_witnesses': completed_witnesses,
            'total_witnesses': total_witnesses
        }
    
    def _estimate_day_completion(self, trial_day_plan) -> Optional[time]:
        """Estimate trial day completion time."""
        remaining_witnesses = [w for w in trial_day_plan.witness_schedule 
                             if w.status not in [WitnessStatus.COMPLETED, WitnessStatus.EXCUSED]]
        
        if not remaining_witnesses:
            return datetime.now().time()
        
        remaining_minutes = sum(w.estimated_duration_minutes for w in remaining_witnesses)
        estimated_completion = datetime.now() + timedelta(minutes=remaining_minutes)
        
        return estimated_completion.time()

class UnifiedTrialInterface:
    """Unified interface for all trial preparation and management operations."""
    
    def __init__(self):
        # Initialize integrated systems
        self.integrated_system = IntegratedTrialSystem()
        self.automation_engine = TrialAutomationEngine(self.integrated_system)
        self.dashboard = TrialDashboard(self.integrated_system)
        
        # Command processing
        self.command_history: List[UnifiedCommand] = []
        self.active_contexts: Dict[str, str] = {}  # user_id -> trial_context_id
        
        self.logger = logging.getLogger(__name__ + ".UnifiedTrialInterface")
    
    def execute_command(self, command: UnifiedCommand) -> UnifiedResponse:
        """Execute unified command and return response."""
        start_time = datetime.now()
        
        response = UnifiedResponse(
            command_id=command.command_id,
            status=ResponseStatus.SUCCESS
        )
        
        try:
            # Route command to appropriate handler
            if command.command_type == InterfaceCommand.CREATE_TRIAL:
                response = self._handle_create_trial(command)
            elif command.command_type == InterfaceCommand.GET_TRIAL_STATUS:
                response = self._handle_get_trial_status(command)
            elif command.command_type == InterfaceCommand.START_TRIAL_DAY:
                response = self._handle_start_trial_day(command)
            elif command.command_type == InterfaceCommand.ADD_WITNESS:
                response = self._handle_add_witness(command)
            elif command.command_type == InterfaceCommand.SCHEDULE_WITNESS:
                response = self._handle_schedule_witness(command)
            elif command.command_type == InterfaceCommand.ADD_EXHIBIT:
                response = self._handle_add_exhibit(command)
            elif command.command_type == InterfaceCommand.GENERATE_DOCUMENT:
                response = self._handle_generate_document(command)
            elif command.command_type == InterfaceCommand.GET_DASHBOARD:
                response = self._handle_get_dashboard(command)
            elif command.command_type == InterfaceCommand.CREATE_WORKFLOW:
                response = self._handle_create_workflow(command)
            elif command.command_type == InterfaceCommand.GET_AUTOMATION_RECOMMENDATIONS:
                response = self._handle_get_automation_recommendations(command)
            else:
                response.status = ResponseStatus.ERROR
                response.errors.append(f"Unknown command type: {command.command_type}")
        
        except Exception as e:
            response.status = ResponseStatus.ERROR
            response.errors.append(str(e))
            self.logger.error(f"Command execution failed: {e}")
        
        # Calculate execution time
        execution_time = datetime.now() - start_time
        response.execution_time_ms = int(execution_time.total_seconds() * 1000)
        
        # Store command in history
        self.command_history.append(command)
        
        return response
    
    def quick_execute(self, command_type: str, parameters: Dict[str, Any], 
                     user_id: str = "") -> UnifiedResponse:
        """Quick command execution with simplified parameters."""
        command = UnifiedCommand(
            command_id=str(uuid.uuid4()),
            command_type=InterfaceCommand(command_type),
            parameters=parameters,
            user_id=user_id
        )
        
        return self.execute_command(command)
    
    def set_active_trial_context(self, user_id: str, trial_context_id: str) -> bool:
        """Set active trial context for user."""
        if trial_context_id in self.integrated_system.data_integrator.trial_contexts:
            self.active_contexts[user_id] = trial_context_id
            return True
        return False
    
    def get_user_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get dashboard for user's active trial context."""
        if user_id in self.active_contexts:
            trial_context_id = self.active_contexts[user_id]
            return self.dashboard.generate_comprehensive_dashboard(trial_context_id)
        
        return {'error': 'No active trial context for user'}
    
    def batch_execute(self, commands: List[UnifiedCommand]) -> List[UnifiedResponse]:
        """Execute multiple commands in batch."""
        responses = []
        
        for command in commands:
            response = self.execute_command(command)
            responses.append(response)
            
            # Stop batch execution if critical error occurs
            if response.status == ResponseStatus.ERROR and command.priority >= 4:
                remaining_responses = [UnifiedResponse(
                    command_id=cmd.command_id,
                    status=ResponseStatus.PENDING,
                    messages=["Batch execution stopped due to critical error"]
                ) for cmd in commands[len(responses):]]
                responses.extend(remaining_responses)
                break
        
        return responses
    
    def _handle_create_trial(self, command: UnifiedCommand) -> UnifiedResponse:
        """Handle create trial command."""
        response = UnifiedResponse(command_id=command.command_id, status=ResponseStatus.SUCCESS)
        
        try:
            case_id = command.parameters['case_id']
            case_name = command.parameters['case_name']
            trial_start_date = datetime.strptime(command.parameters['trial_start_date'], '%Y-%m-%d').date()
            estimated_days = command.parameters.get('estimated_days', 5)
            court = command.parameters.get('court', '')
            judge = command.parameters.get('judge', '')
            
            # Create integrated trial
            integration_ids = self.integrated_system.create_integrated_trial(
                case_id, case_name, trial_start_date, estimated_days, court, judge
            )
            
            # Set as active context for user
            trial_context_id = integration_ids['trial_context_id']
            if command.user_id:
                self.set_active_trial_context(command.user_id, trial_context_id)
            
            response.data = integration_ids
            response.messages.append(f"Successfully created integrated trial for {case_name}")
            
        except Exception as e:
            response.status = ResponseStatus.ERROR
            response.errors.append(str(e))
        
        return response
    
    def _handle_get_trial_status(self, command: UnifiedCommand) -> UnifiedResponse:
        """Handle get trial status command."""
        response = UnifiedResponse(command_id=command.command_id, status=ResponseStatus.SUCCESS)
        
        try:
            trial_context_id = command.parameters.get('trial_context_id') or self.active_contexts.get(command.user_id)
            
            if not trial_context_id:
                response.status = ResponseStatus.ERROR
                response.errors.append("No trial context specified")
                return response
            
            trial_status = self.integrated_system.get_integrated_trial_status(trial_context_id)
            response.data = trial_status
            
        except Exception as e:
            response.status = ResponseStatus.ERROR
            response.errors.append(str(e))
        
        return response
    
    def _handle_start_trial_day(self, command: UnifiedCommand) -> UnifiedResponse:
        """Handle start trial day command."""
        response = UnifiedResponse(command_id=command.command_id, status=ResponseStatus.SUCCESS)
        
        try:
            trial_context_id = command.parameters.get('trial_context_id') or self.active_contexts.get(command.user_id)
            day_id = command.parameters['day_id']
            
            if not trial_context_id:
                response.status = ResponseStatus.ERROR
                response.errors.append("No trial context specified")
                return response
            
            context = self.integrated_system.data_integrator.trial_contexts[trial_context_id]
            notebook_id = context.trial_notebook_id
            
            # Start trial day
            success = self.integrated_system.digital_trial_notebook.start_trial_day(notebook_id, day_id)
            
            if success:
                # Trigger automation workflows
                workflow_id = self.automation_engine.create_automation_workflow(
                    WorkflowType.DAILY_PREPARATION,
                    AutomationTrigger.TRIAL_DAY_START,
                    trial_context_id
                )
                
                # Execute daily preparation workflow
                workflow_result = self.automation_engine.execute_workflow(workflow_id)
                
                response.data = {
                    'trial_day_started': True,
                    'day_id': day_id,
                    'automation_workflow_id': workflow_id,
                    'automation_result': workflow_result
                }
                response.messages.append("Trial day started successfully with automated preparation")
            else:
                response.status = ResponseStatus.ERROR
                response.errors.append("Failed to start trial day")
                
        except Exception as e:
            response.status = ResponseStatus.ERROR
            response.errors.append(str(e))
        
        return response
    
    def _handle_add_witness(self, command: UnifiedCommand) -> UnifiedResponse:
        """Handle add witness command."""
        response = UnifiedResponse(command_id=command.command_id, status=ResponseStatus.SUCCESS)
        
        try:
            from .witness_manager import WitnessProfile, WitnessType
            
            # Create witness profile from parameters
            witness_profile = WitnessProfile(
                witness_id=str(uuid.uuid4()),
                name=command.parameters['name'],
                witness_type=WitnessType(command.parameters.get('witness_type', 'fact_witness')),
                occupation=command.parameters.get('occupation'),
                phone=command.parameters.get('phone'),
                email=command.parameters.get('email')
            )
            
            # Add to witness manager
            witness_id = self.integrated_system.witness_manager.add_witness(witness_profile)
            
            response.data = {'witness_id': witness_id}
            response.messages.append(f"Added witness: {witness_profile.name}")
            
        except Exception as e:
            response.status = ResponseStatus.ERROR
            response.errors.append(str(e))
        
        return response
    
    def _handle_schedule_witness(self, command: UnifiedCommand) -> UnifiedResponse:
        """Handle schedule witness command."""
        response = UnifiedResponse(command_id=command.command_id, status=ResponseStatus.SUCCESS)
        
        try:
            trial_context_id = command.parameters.get('trial_context_id') or self.active_contexts.get(command.user_id)
            
            if not trial_context_id:
                response.status = ResponseStatus.ERROR
                response.errors.append("No trial context specified")
                return response
            
            context = self.integrated_system.data_integrator.trial_contexts[trial_context_id]
            notebook_id = context.trial_notebook_id
            
            # Schedule witness
            success = self.integrated_system.digital_trial_notebook.schedule_witness(
                notebook_id,
                command.parameters['day_id'],
                command.parameters['witness_id'],
                command.parameters['witness_name'],
                command.parameters['examination_type'],
                datetime.strptime(command.parameters['scheduled_time'], '%H:%M').time(),
                command.parameters.get('duration_minutes', 60)
            )
            
            if success:
                response.data = {'witness_scheduled': True}
                response.messages.append("Witness scheduled successfully")
            else:
                response.status = ResponseStatus.ERROR
                response.errors.append("Failed to schedule witness")
                
        except Exception as e:
            response.status = ResponseStatus.ERROR
            response.errors.append(str(e))
        
        return response
    
    def _handle_add_exhibit(self, command: UnifiedCommand) -> UnifiedResponse:
        """Handle add exhibit command."""
        response = UnifiedResponse(command_id=command.command_id, status=ResponseStatus.SUCCESS)
        
        try:
            from .exhibit_manager import Exhibit, ExhibitType, ExhibitParty
            
            # Create exhibit from parameters
            exhibit = Exhibit(
                exhibit_id=str(uuid.uuid4()),
                exhibit_number=command.parameters.get('exhibit_number', ''),
                party=ExhibitParty(command.parameters.get('party', 'plaintiff')),
                exhibit_type=ExhibitType(command.parameters.get('exhibit_type', 'document')),
                title=command.parameters['title'],
                description=command.parameters.get('description', '')
            )
            
            # Add to exhibit manager
            exhibit_id = self.integrated_system.exhibit_manager.add_exhibit(exhibit)
            
            response.data = {'exhibit_id': exhibit_id}
            response.messages.append(f"Added exhibit: {exhibit.title}")
            
        except Exception as e:
            response.status = ResponseStatus.ERROR
            response.errors.append(str(e))
        
        return response
    
    def _handle_generate_document(self, command: UnifiedCommand) -> UnifiedResponse:
        """Handle generate document command."""
        response = UnifiedResponse(command_id=command.command_id, status=ResponseStatus.SUCCESS)
        
        try:
            from .document_generator import GenerationRequest, DocumentType, DocumentPriority
            
            # Create document generation request
            request = GenerationRequest(
                request_id=str(uuid.uuid4()),
                document_type=DocumentType(command.parameters['document_type']),
                template_id=command.parameters.get('template_id', ''),
                case_id=command.parameters['case_id'],
                data_sources=command.parameters.get('data_sources', {}),
                priority=DocumentPriority(command.parameters.get('priority', 'medium')),
                requested_by=command.user_id
            )
            
            # Submit request
            request_id = self.integrated_system.document_generator.request_document_generation(request)
            
            # Generate document
            document_id = self.integrated_system.document_generator.generate_document(request_id)
            
            response.data = {
                'document_id': document_id,
                'request_id': request_id
            }
            response.messages.append("Document generated successfully")
            
        except Exception as e:
            response.status = ResponseStatus.ERROR
            response.errors.append(str(e))
        
        return response
    
    def _handle_get_dashboard(self, command: UnifiedCommand) -> UnifiedResponse:
        """Handle get dashboard command."""
        response = UnifiedResponse(command_id=command.command_id, status=ResponseStatus.SUCCESS)
        
        try:
            trial_context_id = command.parameters.get('trial_context_id') or self.active_contexts.get(command.user_id)
            
            if not trial_context_id:
                response.status = ResponseStatus.ERROR
                response.errors.append("No trial context specified")
                return response
            
            dashboard_data = self.dashboard.generate_comprehensive_dashboard(trial_context_id)
            response.data = dashboard_data
            
        except Exception as e:
            response.status = ResponseStatus.ERROR
            response.errors.append(str(e))
        
        return response
    
    def _handle_create_workflow(self, command: UnifiedCommand) -> UnifiedResponse:
        """Handle create workflow command."""
        response = UnifiedResponse(command_id=command.command_id, status=ResponseStatus.SUCCESS)
        
        try:
            trial_context_id = command.parameters.get('trial_context_id') or self.active_contexts.get(command.user_id)
            
            if not trial_context_id:
                response.status = ResponseStatus.ERROR
                response.errors.append("No trial context specified")
                return response
            
            workflow_id = self.automation_engine.create_automation_workflow(
                WorkflowType(command.parameters['workflow_type']),
                AutomationTrigger(command.parameters['trigger_condition']),
                trial_context_id,
                command.parameters.get('custom_parameters')
            )
            
            response.data = {'workflow_id': workflow_id}
            response.messages.append("Workflow created successfully")
            
        except Exception as e:
            response.status = ResponseStatus.ERROR
            response.errors.append(str(e))
        
        return response
    
    def _handle_get_automation_recommendations(self, command: UnifiedCommand) -> UnifiedResponse:
        """Handle get automation recommendations command."""
        response = UnifiedResponse(command_id=command.command_id, status=ResponseStatus.SUCCESS)
        
        try:
            trial_context_id = command.parameters.get('trial_context_id') or self.active_contexts.get(command.user_id)
            
            if not trial_context_id:
                response.status = ResponseStatus.ERROR
                response.errors.append("No trial context specified")
                return response
            
            recommendations = self.automation_engine.get_automation_recommendations(trial_context_id)
            response.data = {'recommendations': recommendations}
            
        except Exception as e:
            response.status = ResponseStatus.ERROR
            response.errors.append(str(e))
        
        return response