"""
Integrated Trial System

Comprehensive integration layer connecting the Digital Trial Notebook with all
trial preparation components for unified trial management, real-time updates,
and seamless data flow between all systems.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime, date, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
import logging
from pathlib import Path

# Import all trial preparation components
from .digital_trial_notebook import (
    DigitalTrialNotebook, TrialNotebook, TrialDayPlan, WitnessSchedule, 
    ExhibitSchedule, TrialDay, WitnessStatus, ExhibitAction
)
from .case_analyzer import CaseAnalyzer, CaseAnalysis, StrategicInsight
from .evidence_manager import EvidenceManager, EvidenceItem, EvidenceChain
from .witness_manager import WitnessManager, WitnessProfile, WitnessPreparation
from .document_generator import DocumentGenerator, TrialDocument, DocumentType
from .timeline_builder import TimelineBuilder, TimelineEvent, CaseTimeline
from .jury_analyzer import JuryAnalyzer, JurorProfile, JurySelection
from .exhibit_manager import ExhibitManager, Exhibit, ExhibitList
from .witness_prep_tracker import WitnessPrepTracker, PrepSession, WitnessReadinessReport
from .jury_instruction_assistant import JuryInstructionAssistant, JuryInstruction, InstructionSet

logger = logging.getLogger(__name__)

class SyncStatus(Enum):
    """Status of data synchronization between systems."""
    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    ERROR = "error"
    OUT_OF_SYNC = "out_of_sync"

class UpdatePriority(Enum):
    """Priority levels for system updates."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    ROUTINE = 1

class IntegrationEvent(Enum):
    """Types of integration events."""
    WITNESS_STATUS_CHANGE = "witness_status_change"
    EXHIBIT_STATUS_CHANGE = "exhibit_status_change"
    EVIDENCE_UPDATED = "evidence_updated"
    CASE_ANALYSIS_COMPLETE = "case_analysis_complete"
    WITNESS_PREP_COMPLETE = "witness_prep_complete"
    DOCUMENT_GENERATED = "document_generated"
    TIMELINE_UPDATED = "timeline_updated"
    JURY_SELECTION_COMPLETE = "jury_selection_complete"
    INSTRUCTION_APPROVED = "instruction_approved"
    TRIAL_DAY_STARTED = "trial_day_started"
    TRIAL_DAY_COMPLETED = "trial_day_completed"

@dataclass
class DataSyncRecord:
    """Record of data synchronization between systems."""
    sync_id: str
    source_system: str
    target_system: str
    data_type: str
    source_id: str
    target_id: str
    sync_status: SyncStatus = SyncStatus.PENDING
    last_sync_date: Optional[datetime] = None
    conflict_details: str = ""
    retry_count: int = 0

@dataclass
class SystemUpdate:
    """Update notification between integrated systems."""
    update_id: str
    source_system: str
    event_type: IntegrationEvent
    affected_entity_id: str
    update_data: Dict[str, Any] = field(default_factory=dict)
    priority: UpdatePriority = UpdatePriority.MEDIUM
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False
    target_systems: List[str] = field(default_factory=list)

@dataclass
class TrialContext:
    """Current trial context for all integrated systems."""
    case_id: str
    trial_notebook_id: str
    current_trial_day: Optional[str] = None
    trial_phase: str = "preparation"
    
    # Active entities
    active_witnesses: List[str] = field(default_factory=list)
    active_exhibits: List[str] = field(default_factory=list)
    active_evidence: List[str] = field(default_factory=list)
    active_instructions: List[str] = field(default_factory=list)
    
    # System states
    case_analysis_id: Optional[str] = None
    evidence_chain_ids: List[str] = field(default_factory=list)
    witness_prep_sessions: Dict[str, str] = field(default_factory=dict)  # witness_id -> session_id
    jury_selection_id: Optional[str] = None
    instruction_set_id: Optional[str] = None
    
    # Real-time status
    last_updated: datetime = field(default_factory=datetime.now)
    sync_status: Dict[str, SyncStatus] = field(default_factory=dict)

class TrialDataIntegrator:
    """Integrates data between all trial preparation systems."""
    
    def __init__(self):
        self.sync_records: Dict[str, DataSyncRecord] = {}
        self.trial_contexts: Dict[str, TrialContext] = {}
        self.logger = logging.getLogger(__name__ + ".TrialDataIntegrator")
    
    def sync_evidence_to_exhibits(self, evidence_manager: EvidenceManager,
                                 exhibit_manager: ExhibitManager,
                                 case_id: str) -> Dict[str, Any]:
        """Sync evidence items to exhibit management system."""
        sync_results = {
            'synced_items': [],
            'conflicts': [],
            'new_exhibits': [],
            'updated_exhibits': []
        }
        
        # Get all evidence items for the case
        evidence_items = [item for item in evidence_manager.evidence_items.values()
                         if case_id in item.tags or case_id in item.metadata.get('case_ids', [])]
        
        for evidence_item in evidence_items:
            # Check if exhibit already exists for this evidence
            existing_exhibit = None
            for exhibit in exhibit_manager.exhibits.values():
                if exhibit.source_evidence_id == evidence_item.evidence_id:
                    existing_exhibit = exhibit
                    break
            
            if existing_exhibit:
                # Update existing exhibit with evidence data
                self._update_exhibit_from_evidence(existing_exhibit, evidence_item)
                sync_results['updated_exhibits'].append(existing_exhibit.exhibit_id)
            else:
                # Create new exhibit from evidence
                new_exhibit = self._create_exhibit_from_evidence(evidence_item, case_id)
                exhibit_id = exhibit_manager.add_exhibit(new_exhibit)
                sync_results['new_exhibits'].append(exhibit_id)
            
            # Record sync
            self._record_sync('evidence_manager', 'exhibit_manager', 
                            'evidence_item', evidence_item.evidence_id,
                            existing_exhibit.exhibit_id if existing_exhibit else exhibit_id)
            
            sync_results['synced_items'].append(evidence_item.evidence_id)
        
        self.logger.info(f"Synced {len(sync_results['synced_items'])} evidence items to exhibits")
        return sync_results
    
    def sync_witnesses_to_trial_notebook(self, witness_manager: WitnessManager,
                                       trial_notebook: DigitalTrialNotebook,
                                       notebook_id: str) -> Dict[str, Any]:
        """Sync witness information to trial notebook scheduling."""
        sync_results = {
            'synced_witnesses': [],
            'scheduling_conflicts': [],
            'readiness_alerts': []
        }
        
        notebook = trial_notebook.trial_notebooks[notebook_id]
        
        # Sync witness data to master list
        for witness_id, witness in witness_manager.witnesses.items():
            notebook.master_witness_list[witness_id] = {
                'name': witness.name,
                'witness_type': witness.witness_type.value,
                'status': witness.status.value,
                'importance': witness.strategic_value,
                'preparation_status': witness.preparation_status.value,
                'scheduled_days': [],
                'testimony_status': 'scheduled',
                'contact_info': {
                    'phone': witness.phone,
                    'email': witness.email,
                    'preferred_contact': witness.preferred_contact_method
                },
                'strategic_notes': {
                    'favorable_points': witness.favorable_points,
                    'damaging_points': witness.damaging_points,
                    'risks': witness.risks,
                    'importance_level': witness.strategic_value
                }
            }
            
            sync_results['synced_witnesses'].append(witness_id)
        
        # Check witness readiness for scheduled testimony
        for day_id, trial_day in notebook.trial_days.items():
            for witness_schedule in trial_day.witness_schedule:
                witness_id = witness_schedule.witness_id
                if witness_id in witness_manager.witnesses:
                    witness = witness_manager.witnesses[witness_id]
                    
                    # Check readiness status
                    if witness.preparation_status.value in ['not_started', 'in_progress']:
                        sync_results['readiness_alerts'].append({
                            'witness_id': witness_id,
                            'witness_name': witness.name,
                            'trial_date': trial_day.trial_date,
                            'issue': 'Preparation not complete',
                            'recommendation': 'Accelerate witness preparation'
                        })
        
        return sync_results
    
    def sync_case_analysis_to_trial_strategy(self, case_analyzer: CaseAnalyzer,
                                           trial_notebook: DigitalTrialNotebook,
                                           notebook_id: str, case_analysis_id: str) -> Dict[str, Any]:
        """Sync case analysis to trial notebook strategy."""
        sync_results = {
            'strategy_updated': False,
            'themes_updated': False,
            'arguments_updated': False,
            'risks_updated': False
        }
        
        # Get case analysis
        case_analysis = case_analyzer.get_analysis(case_analysis_id)
        if not case_analysis:
            return {'error': 'Case analysis not found'}
        
        notebook = trial_notebook.trial_notebooks[notebook_id]
        
        # Update trial strategy
        notebook.trial_theme = case_analysis.primary_theory
        notebook.key_legal_arguments = case_analysis.legal_arguments[:5]  # Top 5 arguments
        
        # Update opening statement outline from strategic insights
        opening_outline = []
        for insight in case_analysis.strategic_insights[:3]:  # Top 3 insights
            opening_outline.append(insight.description)
        notebook.opening_statement_outline = opening_outline
        
        # Update risk management
        notebook.identified_risks = case_analysis.weaknesses
        
        # Generate contingency plans from strategic insights
        contingency_plans = {}
        for weakness in case_analysis.weaknesses:
            # Find strategic insights that address this weakness
            addressing_insights = [insight for insight in case_analysis.strategic_insights
                                 if weakness.lower() in insight.description.lower()]
            if addressing_insights:
                contingency_plans[weakness] = [insight.recommendation for insight in addressing_insights]
        
        notebook.contingency_plans.update(contingency_plans)
        
        # Update daily objectives based on case strategy
        for day_id, trial_day in notebook.trial_days.items():
            if trial_day.day_type in [TrialDay.PLAINTIFF_CASE, TrialDay.DEFENDANT_CASE]:
                # Add strategic themes to daily objectives
                strategic_objectives = [
                    f"Emphasize theme: {notebook.trial_theme}",
                    f"Present evidence supporting: {case_analysis.primary_theory}"
                ]
                trial_day.key_themes_to_emphasize.extend(strategic_objectives)
        
        sync_results.update({
            'strategy_updated': True,
            'themes_updated': True,
            'arguments_updated': True,
            'risks_updated': True
        })
        
        return sync_results
    
    def sync_timeline_to_trial_notebook(self, timeline_builder: TimelineBuilder,
                                      trial_notebook: DigitalTrialNotebook,
                                      notebook_id: str, timeline_id: str) -> Dict[str, Any]:
        """Sync case timeline to trial notebook for witness and exhibit coordination."""
        sync_results = {
            'events_synced': 0,
            'witness_evidence_links': [],
            'chronology_updates': []
        }
        
        if timeline_id not in timeline_builder.timelines:
            return {'error': 'Timeline not found'}
        
        timeline = timeline_builder.timelines[timeline_id]
        timeline_events = [timeline_builder.events[eid] for eid in timeline.events
                          if eid in timeline_builder.events]
        
        notebook = trial_notebook.trial_notebooks[notebook_id]
        
        # Create chronological witness examination order based on timeline
        chronological_witnesses = {}
        
        for event in sorted(timeline_events, key=lambda e: e.date):
            # Link timeline events to witnesses who observed them
            for witness_id in event.witnesses:
                if witness_id not in chronological_witnesses:
                    chronological_witnesses[witness_id] = []
                chronological_witnesses[witness_id].append({
                    'event_date': event.date,
                    'event_title': event.title,
                    'event_id': event.event_id
                })
        
        # Update trial day witness schedules with chronological context
        for day_id, trial_day in notebook.trial_days.items():
            for witness_schedule in trial_day.witness_schedule:
                witness_id = witness_schedule.witness_id
                if witness_id in chronological_witnesses:
                    # Add chronological context to witness preparation
                    witness_events = chronological_witnesses[witness_id]
                    witness_schedule.key_topics.extend([
                        f"Timeline event: {event['event_title']}" 
                        for event in witness_events[:3]  # Top 3 relevant events
                    ])
                    
                    sync_results['witness_evidence_links'].append({
                        'witness_id': witness_id,
                        'relevant_events': len(witness_events),
                        'trial_day': trial_day.trial_date
                    })
        
        # Generate chronology-based exhibit introduction order
        chronological_exhibits = []
        for event in timeline_events:
            for evidence_id in event.supporting_evidence:
                chronological_exhibits.append({
                    'event_date': event.date,
                    'evidence_id': evidence_id,
                    'event_context': event.title
                })
        
        sync_results['chronology_updates'] = chronological_exhibits
        sync_results['events_synced'] = len(timeline_events)
        
        return sync_results
    
    def sync_jury_analysis_to_trial_notebook(self, jury_analyzer: JuryAnalyzer,
                                           trial_notebook: DigitalTrialNotebook,
                                           notebook_id: str) -> Dict[str, Any]:
        """Sync jury selection and analysis to trial notebook."""
        sync_results = {
            'jury_profile_updated': False,
            'voir_dire_strategy_updated': False,
            'trial_themes_adjusted': False
        }
        
        notebook = trial_notebook.trial_notebooks[notebook_id]
        
        # Get jury composition analysis if available
        jury_compositions = list(jury_analyzer.jury_compositions.values())
        if jury_compositions:
            latest_composition = max(jury_compositions, key=lambda c: c.composition_id)
            
            # Update jury profile in trial notebook
            notebook.jury_profile_notes = f"""
            Jury Composition Analysis:
            - Overall bias lean: {latest_composition.overall_bias_lean.value}
            - Favorability average: {latest_composition.favorability_average:.2f}
            - Diversity score: {latest_composition.diversity_score:.2f}
            - Key swing jurors: {len(latest_composition.key_swing_jurors)}
            
            Strategic considerations:
            - Strengths: {', '.join(latest_composition.strengths)}
            - Concerns: {', '.join(latest_composition.concerns)}
            """
            
            sync_results['jury_profile_updated'] = True
            
            # Adjust trial themes based on jury composition
            if latest_composition.overall_bias_lean.value in ['pro_plaintiff', 'pro_litigation']:
                # Emphasize emotional and justice themes
                for day_id, trial_day in notebook.trial_days.items():
                    if trial_day.day_type == TrialDay.PLAINTIFF_CASE:
                        trial_day.key_themes_to_emphasize.extend([
                            "Justice and accountability",
                            "Impact on plaintiff's life",
                            "Corporate responsibility"
                        ])
            elif latest_composition.overall_bias_lean.value in ['pro_defendant', 'anti_litigation']:
                # Emphasize factual and economic themes
                for day_id, trial_day in notebook.trial_days.items():
                    if trial_day.day_type == TrialDay.PLAINTIFF_CASE:
                        trial_day.key_themes_to_emphasize.extend([
                            "Facts and evidence focus",
                            "Economic impact analysis",
                            "Reasonable business practices"
                        ])
            
            sync_results['trial_themes_adjusted'] = True
        
        # Generate voir dire strategy based on case themes
        if notebook.trial_theme:
            voir_dire_strategy = f"""
            Voir Dire Strategy for theme: "{notebook.trial_theme}"
            
            Key Questions to Ask:
            1. Experience with similar cases or situations
            2. Attitudes toward corporate responsibility
            3. Understanding of burden of proof
            4. Potential biases related to case theme
            
            Jurors to Challenge:
            - Strong anti-litigation bias
            - Conflicts with case theme
            - Inability to award damages
            """
            
            notebook.jury_selection_strategy = voir_dire_strategy
            sync_results['voir_dire_strategy_updated'] = True
        
        return sync_results
    
    def sync_document_generation_to_trial_notebook(self, document_generator: DocumentGenerator,
                                                 trial_notebook: DigitalTrialNotebook,
                                                 notebook_id: str) -> Dict[str, Any]:
        """Sync generated documents to trial notebook."""
        sync_results = {
            'documents_linked': [],
            'exhibits_created': [],
            'trial_materials_updated': False
        }
        
        notebook = trial_notebook.trial_notebooks[notebook_id]
        case_id = notebook.case_id
        
        # Get all documents for this case
        case_documents = [doc for doc in document_generator.documents.values()
                         if doc.case_id == case_id]
        
        # Link trial briefs to opening/closing statement outlines
        for document in case_documents:
            if document.document_type == DocumentType.OPENING_STATEMENT:
                # Extract outline from document content
                outline_points = self._extract_outline_from_content(document.content)
                notebook.opening_statement_outline = outline_points
                sync_results['documents_linked'].append(document.document_id)
                
            elif document.document_type == DocumentType.CLOSING_ARGUMENT:
                outline_points = self._extract_outline_from_content(document.content)
                notebook.closing_argument_outline = outline_points
                sync_results['documents_linked'].append(document.document_id)
                
            elif document.document_type == DocumentType.EXHIBIT_LIST:
                # Create exhibit schedules from exhibit list
                exhibit_data = self._extract_exhibits_from_list(document.content)
                for exhibit_info in exhibit_data:
                    # Find appropriate trial day for exhibit
                    target_day = self._find_optimal_trial_day(notebook, exhibit_info)
                    if target_day:
                        exhibit_schedule = ExhibitSchedule(
                            exhibit_id=exhibit_info['exhibit_id'],
                            exhibit_number=exhibit_info['exhibit_number'],
                            introducing_witness=exhibit_info.get('witness'),
                            importance_level=exhibit_info.get('importance', 3)
                        )
                        target_day.exhibit_schedule.append(exhibit_schedule)
                        sync_results['exhibits_created'].append(exhibit_info['exhibit_id'])
        
        sync_results['trial_materials_updated'] = len(sync_results['documents_linked']) > 0
        return sync_results
    
    def create_trial_context(self, case_id: str, trial_notebook_id: str) -> str:
        """Create integrated trial context for unified system management."""
        context_id = str(uuid.uuid4())
        
        trial_context = TrialContext(
            case_id=case_id,
            trial_notebook_id=trial_notebook_id
        )
        
        self.trial_contexts[context_id] = trial_context
        self.logger.info(f"Created trial context: {context_id}")
        return context_id
    
    def update_trial_context(self, context_id: str, update_data: Dict[str, Any]) -> bool:
        """Update trial context with new information from any system."""
        if context_id not in self.trial_contexts:
            return False
        
        context = self.trial_contexts[context_id]
        
        # Update context based on update data
        for key, value in update_data.items():
            if hasattr(context, key):
                setattr(context, key, value)
        
        context.last_updated = datetime.now()
        return True
    
    def _update_exhibit_from_evidence(self, exhibit: Exhibit, evidence_item: EvidenceItem) -> None:
        """Update exhibit with evidence item data."""
        exhibit.title = evidence_item.title
        exhibit.description = evidence_item.description
        exhibit.source_evidence_id = evidence_item.evidence_id
        exhibit.strategic_notes = evidence_item.case_relevance
        exhibit.importance_level = evidence_item.relevance_score.value
        
        # Update authentication from evidence
        if evidence_item.authenticity_level.name != 'UNVERIFIED':
            exhibit.authentication.foundation_complete = True
            exhibit.authentication.authentication_method = f"Evidence authentication: {evidence_item.authenticity_level.name}"
    
    def _create_exhibit_from_evidence(self, evidence_item: EvidenceItem, case_id: str) -> Exhibit:
        """Create new exhibit from evidence item."""
        from .exhibit_manager import Exhibit, ExhibitType, ExhibitParty, ExhibitStatus, ExhibitAuthentication
        
        # Map evidence type to exhibit type
        exhibit_type_mapping = {
            'document': ExhibitType.DOCUMENT,
            'photograph': ExhibitType.PHOTOGRAPH,
            'video': ExhibitType.VIDEO,
            'audio': ExhibitType.AUDIO,
            'digital': ExhibitType.DIGITAL_EVIDENCE
        }
        
        exhibit_type = exhibit_type_mapping.get(evidence_item.evidence_type.value, ExhibitType.DOCUMENT)
        
        # Create authentication from evidence
        auth = ExhibitAuthentication(
            authentication_id=str(uuid.uuid4()),
            foundation_complete=evidence_item.authenticity_level.name != 'UNVERIFIED',
            authentication_method=f"Evidence chain authentication: {evidence_item.authenticity_level.name}"
        )
        
        exhibit = Exhibit(
            exhibit_id=str(uuid.uuid4()),
            exhibit_number="TBD",  # Will be assigned by exhibit manager
            party=ExhibitParty.PLAINTIFF,  # Default, can be updated
            exhibit_type=exhibit_type,
            title=evidence_item.title,
            description=evidence_item.description,
            source_evidence_id=evidence_item.evidence_id,
            authentication=auth,
            importance_level=evidence_item.relevance_score.value,
            strategic_notes=evidence_item.case_relevance
        )
        
        return exhibit
    
    def _record_sync(self, source_system: str, target_system: str, data_type: str,
                    source_id: str, target_id: str) -> None:
        """Record synchronization between systems."""
        sync_id = str(uuid.uuid4())
        sync_record = DataSyncRecord(
            sync_id=sync_id,
            source_system=source_system,
            target_system=target_system,
            data_type=data_type,
            source_id=source_id,
            target_id=target_id,
            sync_status=SyncStatus.SYNCED,
            last_sync_date=datetime.now()
        )
        
        self.sync_records[sync_id] = sync_record
    
    def _extract_outline_from_content(self, content: str) -> List[str]:
        """Extract outline points from document content."""
        # Simple extraction - look for numbered or bulleted lists
        lines = content.split('\n')
        outline_points = []
        
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith(('1.', '2.', '3.', '4.', '5.')) or
                stripped.startswith(('•', '-', '*')) or
                stripped.startswith(('I.', 'II.', 'III.'))):
                outline_points.append(stripped)
        
        return outline_points[:10]  # Limit to 10 points
    
    def _extract_exhibits_from_list(self, content: str) -> List[Dict[str, Any]]:
        """Extract exhibit information from exhibit list content."""
        # Simplified extraction - would be more sophisticated in real implementation
        exhibits = []
        lines = content.split('\n')
        
        for line in lines:
            if 'Exhibit' in line and ('-' in line or 'P-' in line or 'D-' in line):
                parts = line.split()
                exhibit_number = next((part for part in parts if 'P-' in part or 'D-' in part), 'Unknown')
                
                exhibits.append({
                    'exhibit_id': str(uuid.uuid4()),
                    'exhibit_number': exhibit_number,
                    'description': line.strip(),
                    'importance': 3
                })
        
        return exhibits
    
    def _find_optimal_trial_day(self, notebook: TrialNotebook, exhibit_info: Dict[str, Any]) -> Optional[TrialDayPlan]:
        """Find optimal trial day for exhibit introduction."""
        # Simple heuristic - assign to plaintiff case day for P- exhibits, defendant case for D- exhibits
        exhibit_number = exhibit_info.get('exhibit_number', '')
        
        for trial_day in notebook.trial_days.values():
            if 'P-' in exhibit_number and trial_day.day_type == TrialDay.PLAINTIFF_CASE:
                return trial_day
            elif 'D-' in exhibit_number and trial_day.day_type == TrialDay.DEFENDANT_CASE:
                return trial_day
        
        # Default to first available trial day
        if notebook.trial_days:
            return list(notebook.trial_days.values())[0]
        
        return None

class IntegratedTrialSystem:
    """Master integration system coordinating all trial preparation components."""
    
    def __init__(self):
        # Initialize all trial preparation components
        self.digital_trial_notebook = DigitalTrialNotebook()
        self.case_analyzer = CaseAnalyzer()
        self.evidence_manager = EvidenceManager()
        self.witness_manager = WitnessManager()
        self.document_generator = DocumentGenerator()
        self.timeline_builder = TimelineBuilder()
        self.jury_analyzer = JuryAnalyzer()
        self.exhibit_manager = ExhibitManager()
        self.witness_prep_tracker = WitnessPrepTracker()
        self.jury_instruction_assistant = JuryInstructionAssistant()
        
        # Integration layer
        self.data_integrator = TrialDataIntegrator()
        self.update_queue: List[SystemUpdate] = []
        
        self.logger = logging.getLogger(__name__ + ".IntegratedTrialSystem")
    
    def create_integrated_trial(self, case_id: str, case_name: str, trial_start_date: date,
                              estimated_days: int, court: str, judge: str) -> Dict[str, str]:
        """Create fully integrated trial with all components initialized."""
        integration_ids = {}
        
        # Create digital trial notebook
        notebook_id = self.digital_trial_notebook.create_trial_notebook(
            case_id, case_name, trial_start_date, estimated_days, court, judge
        )
        integration_ids['trial_notebook_id'] = notebook_id
        
        # Create supporting components
        timeline_id = self.timeline_builder.create_timeline(case_id, f"{case_name} Timeline")
        integration_ids['timeline_id'] = timeline_id
        
        exhibit_list_id = self.exhibit_manager.create_exhibit_list(case_id, 
                                                                  self.exhibit_manager.ExhibitParty.PLAINTIFF)
        integration_ids['exhibit_list_id'] = exhibit_list_id
        
        instruction_set_id = self.jury_instruction_assistant.create_instruction_set(case_id, "civil", court)
        integration_ids['instruction_set_id'] = instruction_set_id
        
        # Create trial context for integration
        context_id = self.data_integrator.create_trial_context(case_id, notebook_id)
        integration_ids['trial_context_id'] = context_id
        
        # Update trial context with component IDs
        self.data_integrator.update_trial_context(context_id, {
            'timeline_id': timeline_id,
            'exhibit_list_id': exhibit_list_id,
            'instruction_set_id': instruction_set_id
        })
        
        self.logger.info(f"Created integrated trial system for case {case_id}")
        return integration_ids
    
    def perform_full_system_sync(self, trial_context_id: str) -> Dict[str, Any]:
        """Perform comprehensive synchronization across all systems."""
        if trial_context_id not in self.data_integrator.trial_contexts:
            return {'error': 'Trial context not found'}
        
        context = self.data_integrator.trial_contexts[trial_context_id]
        sync_results = {
            'evidence_to_exhibits': {},
            'witnesses_to_notebook': {},
            'case_analysis_to_strategy': {},
            'timeline_to_notebook': {},
            'jury_to_notebook': {},
            'documents_to_notebook': {},
            'sync_timestamp': datetime.now(),
            'overall_success': False
        }
        
        try:
            # Sync evidence to exhibits
            sync_results['evidence_to_exhibits'] = self.data_integrator.sync_evidence_to_exhibits(
                self.evidence_manager, self.exhibit_manager, context.case_id
            )
            
            # Sync witnesses to trial notebook
            sync_results['witnesses_to_notebook'] = self.data_integrator.sync_witnesses_to_trial_notebook(
                self.witness_manager, self.digital_trial_notebook, context.trial_notebook_id
            )
            
            # Sync case analysis to trial strategy (if available)
            if context.case_analysis_id:
                sync_results['case_analysis_to_strategy'] = self.data_integrator.sync_case_analysis_to_trial_strategy(
                    self.case_analyzer, self.digital_trial_notebook, context.trial_notebook_id, context.case_analysis_id
                )
            
            # Sync timeline to trial notebook (if available)
            timeline_id = context.sync_status.get('timeline_id')
            if timeline_id:
                sync_results['timeline_to_notebook'] = self.data_integrator.sync_timeline_to_trial_notebook(
                    self.timeline_builder, self.digital_trial_notebook, context.trial_notebook_id, timeline_id
                )
            
            # Sync jury analysis to trial notebook
            sync_results['jury_to_notebook'] = self.data_integrator.sync_jury_analysis_to_trial_notebook(
                self.jury_analyzer, self.digital_trial_notebook, context.trial_notebook_id
            )
            
            # Sync document generation to trial notebook
            sync_results['documents_to_notebook'] = self.data_integrator.sync_document_generation_to_trial_notebook(
                self.document_generator, self.digital_trial_notebook, context.trial_notebook_id
            )
            
            sync_results['overall_success'] = True
            
        except Exception as e:
            sync_results['error'] = str(e)
            self.logger.error(f"Full system sync failed: {e}")
        
        return sync_results
    
    def handle_real_time_update(self, source_system: str, event_type: IntegrationEvent,
                              entity_id: str, update_data: Dict[str, Any]) -> bool:
        """Handle real-time updates between integrated systems."""
        update = SystemUpdate(
            update_id=str(uuid.uuid4()),
            source_system=source_system,
            event_type=event_type,
            affected_entity_id=entity_id,
            update_data=update_data
        )
        
        self.update_queue.append(update)
        
        # Process update immediately for critical events
        if event_type in [IntegrationEvent.TRIAL_DAY_STARTED, IntegrationEvent.WITNESS_STATUS_CHANGE]:
            return self._process_critical_update(update)
        
        return True
    
    def process_update_queue(self) -> Dict[str, Any]:
        """Process all pending updates in the queue."""
        processing_results = {
            'processed_updates': [],
            'failed_updates': [],
            'critical_issues': []
        }
        
        for update in self.update_queue.copy():
            if not update.processed:
                try:
                    success = self._process_system_update(update)
                    if success:
                        update.processed = True
                        processing_results['processed_updates'].append(update.update_id)
                    else:
                        processing_results['failed_updates'].append(update.update_id)
                except Exception as e:
                    processing_results['failed_updates'].append(update.update_id)
                    self.logger.error(f"Failed to process update {update.update_id}: {e}")
        
        # Remove processed updates
        self.update_queue = [u for u in self.update_queue if not u.processed]
        
        return processing_results
    
    def get_integrated_trial_status(self, trial_context_id: str) -> Dict[str, Any]:
        """Get comprehensive status across all integrated systems."""
        if trial_context_id not in self.data_integrator.trial_contexts:
            return {'error': 'Trial context not found'}
        
        context = self.data_integrator.trial_contexts[trial_context_id]
        
        status = {
            'trial_context': {
                'case_id': context.case_id,
                'trial_phase': context.trial_phase,
                'current_day': context.current_trial_day,
                'last_updated': context.last_updated
            },
            'system_status': {},
            'integration_health': {},
            'active_entities': {
                'witnesses': len(context.active_witnesses),
                'exhibits': len(context.active_exhibits),
                'evidence': len(context.active_evidence)
            },
            'sync_status': context.sync_status,
            'pending_updates': len([u for u in self.update_queue if not u.processed])
        }
        
        # Get status from each system
        try:
            # Trial notebook status
            if context.trial_notebook_id in self.digital_trial_notebook.trial_notebooks:
                notebook_dashboard = self.digital_trial_notebook.generate_trial_dashboard(context.trial_notebook_id)
                status['system_status']['trial_notebook'] = notebook_dashboard
            
            # Evidence manager status
            evidence_count = len(self.evidence_manager.evidence_items)
            status['system_status']['evidence'] = {
                'total_evidence_items': evidence_count,
                'evidence_chains': len(self.evidence_manager.evidence_chains)
            }
            
            # Witness manager status
            witness_count = len(self.witness_manager.witnesses)
            status['system_status']['witnesses'] = {
                'total_witnesses': witness_count,
                'preparations_active': len(self.witness_manager.preparations)
            }
            
            # Document generator status
            document_count = len(self.document_generator.documents)
            status['system_status']['documents'] = {
                'total_documents': document_count,
                'pending_generation': len(self.document_generator.generation_requests)
            }
            
        except Exception as e:
            status['system_status']['error'] = str(e)
        
        return status
    
    def _process_critical_update(self, update: SystemUpdate) -> bool:
        """Process critical updates immediately."""
        if update.event_type == IntegrationEvent.TRIAL_DAY_STARTED:
            # Update all systems with trial day start
            trial_context_id = update.update_data.get('trial_context_id')
            if trial_context_id:
                context = self.data_integrator.trial_contexts.get(trial_context_id)
                if context:
                    context.current_trial_day = update.affected_entity_id
                    context.trial_phase = 'active_trial'
                    return True
        
        elif update.event_type == IntegrationEvent.WITNESS_STATUS_CHANGE:
            # Update witness status across systems
            witness_id = update.affected_entity_id
            new_status = update.update_data.get('status')
            
            # Update witness manager
            if witness_id in self.witness_manager.witnesses:
                # Status would be updated based on the new_status value
                pass
            
            # Update trial notebook witness schedule
            # This would find the relevant trial day and update witness status
            
            return True
        
        return False
    
    def _process_system_update(self, update: SystemUpdate) -> bool:
        """Process individual system update."""
        try:
            if update.event_type == IntegrationEvent.EVIDENCE_UPDATED:
                # Re-sync evidence to exhibits
                evidence_id = update.affected_entity_id
                # Process evidence update logic
                return True
                
            elif update.event_type == IntegrationEvent.CASE_ANALYSIS_COMPLETE:
                # Sync case analysis to trial strategy
                analysis_id = update.affected_entity_id
                # Process case analysis update logic
                return True
                
            elif update.event_type == IntegrationEvent.WITNESS_PREP_COMPLETE:
                # Update witness readiness status
                witness_id = update.affected_entity_id
                # Process witness prep completion logic
                return True
                
            # Add more event type handlers as needed
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing update {update.update_id}: {e}")
            return False