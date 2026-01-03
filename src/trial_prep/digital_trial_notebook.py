"""
Digital Trial Notebook System

Comprehensive digital trial notebook with day-by-day planning, real-time
trial management, witness coordination, exhibit tracking, and strategic
notes for complete trial execution support.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime, date, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
import logging
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)

class TrialDay(Enum):
    """Trial day types."""
    JURY_SELECTION = "jury_selection"
    OPENING_STATEMENTS = "opening_statements"
    PLAINTIFF_CASE = "plaintiff_case"
    DEFENDANT_CASE = "defendant_case"
    REBUTTAL = "rebuttal"
    CLOSING_ARGUMENTS = "closing_arguments"
    JURY_DELIBERATION = "jury_deliberation"
    VERDICT = "verdict"
    POST_TRIAL_MOTIONS = "post_trial_motions"

class SessionType(Enum):
    """Types of trial sessions."""
    MORNING_SESSION = "morning_session"
    AFTERNOON_SESSION = "afternoon_session"
    EVENING_SESSION = "evening_session"
    SIDEBAR_CONFERENCE = "sidebar_conference"
    JURY_INSTRUCTION_CONFERENCE = "jury_instruction_conference"
    MOTION_HEARING = "motion_hearing"

class WitnessStatus(Enum):
    """Status of witness for trial day."""
    SCHEDULED = "scheduled"
    ON_STANDBY = "on_standby"
    CALLED = "called"
    TESTIFYING = "testifying"
    COMPLETED = "completed"
    CONTINUED = "continued"
    EXCUSED = "excused"
    NO_SHOW = "no_show"

class ExhibitAction(Enum):
    """Actions for exhibits during trial."""
    MARKED_FOR_ID = "marked_for_identification"
    OFFERED = "offered"
    ADMITTED = "admitted"
    OBJECTED = "objected"
    WITHDRAWN = "withdrawn"
    USED_DURING_TESTIMONY = "used_during_testimony"

class TrialPhase(Enum):
    """Current phase of trial."""
    PRE_TRIAL = "pre_trial"
    JURY_SELECTION = "jury_selection"
    TRIAL_PROPER = "trial_proper"
    POST_TRIAL = "post_trial"
    COMPLETED = "completed"

@dataclass
class TimeBlock:
    """Time block for trial scheduling."""
    start_time: time
    end_time: time
    duration_minutes: int
    description: str = ""
    
    def overlaps_with(self, other: 'TimeBlock') -> bool:
        """Check if this time block overlaps with another."""
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)
    
    def contains_time(self, check_time: time) -> bool:
        """Check if a specific time falls within this block."""
        return self.start_time <= check_time <= self.end_time

@dataclass
class WitnessSchedule:
    """Witness schedule for a trial day."""
    witness_id: str
    witness_name: str
    examination_type: str  # "direct", "cross", "redirect", "recross"
    scheduled_time: Optional[time] = None
    estimated_duration_minutes: int = 60
    actual_start_time: Optional[time] = None
    actual_end_time: Optional[time] = None
    status: WitnessStatus = WitnessStatus.SCHEDULED
    
    # Preparation details
    key_topics: List[str] = field(default_factory=list)
    exhibits_to_use: List[str] = field(default_factory=list)  # Exhibit IDs
    anticipated_objections: List[str] = field(default_factory=list)
    special_instructions: str = ""
    
    # Real-time notes
    performance_notes: str = ""
    unexpected_testimony: List[str] = field(default_factory=list)
    objections_made: List[str] = field(default_factory=list)
    ruling_outcomes: List[str] = field(default_factory=list)

@dataclass
class ExhibitSchedule:
    """Exhibit schedule and tracking for trial day."""
    exhibit_id: str
    exhibit_number: str
    planned_introduction_time: Optional[time] = None
    introducing_witness: Optional[str] = None
    foundation_witness: Optional[str] = None
    
    # Trial tracking
    actions_taken: List[Tuple[datetime, ExhibitAction, str]] = field(default_factory=list)  # timestamp, action, notes
    current_status: str = "not_yet_introduced"
    court_ruling: Optional[str] = None
    
    # Strategic notes
    importance_level: int = 3  # 1-5 scale
    backup_plan: str = ""
    objection_responses_prepared: bool = False

@dataclass
class MotionTracking:
    """Tracking of motions during trial."""
    motion_id: str
    motion_type: str
    filed_by: str
    filing_time: Optional[datetime] = None
    hearing_scheduled: Optional[datetime] = None
    
    # Motion details
    brief_description: str = ""
    full_text: str = ""
    supporting_citations: List[str] = field(default_factory=list)
    
    # Opposition tracking
    opposition_filed: bool = False
    opposition_deadline: Optional[datetime] = None
    opposition_text: str = ""
    
    # Court action
    court_ruling: Optional[str] = None
    ruling_date: Optional[datetime] = None
    ruling_rationale: str = ""
    
    # Impact assessment
    strategic_impact: str = ""
    contingency_plans: List[str] = field(default_factory=list)

@dataclass
class TrialDayPlan:
    """Comprehensive plan for a single trial day."""
    day_id: str
    trial_date: date
    day_number: int
    day_type: TrialDay
    court_session_start: time = time(9, 0)
    court_session_end: time = time(17, 0)
    
    # Day structure
    morning_session: Optional[TimeBlock] = None
    afternoon_session: Optional[TimeBlock] = None
    lunch_break: Optional[TimeBlock] = None
    other_breaks: List[TimeBlock] = field(default_factory=list)
    
    # Day objectives and strategy
    primary_objectives: List[str] = field(default_factory=list)
    key_themes_to_emphasize: List[str] = field(default_factory=list)
    strategic_goals: List[str] = field(default_factory=list)
    
    # Witness scheduling
    witness_schedule: List[WitnessSchedule] = field(default_factory=list)
    backup_witnesses: List[str] = field(default_factory=list)  # Witness IDs on standby
    
    # Exhibit planning
    exhibit_schedule: List[ExhibitSchedule] = field(default_factory=list)
    exhibit_setup_requirements: List[str] = field(default_factory=list)
    technology_needs: List[str] = field(default_factory=list)
    
    # Legal motions and procedural items
    planned_motions: List[str] = field(default_factory=list)  # Motion IDs
    expected_objections: List[str] = field(default_factory=list)
    jury_instructions_to_request: List[str] = field(default_factory=list)
    
    # Logistics and preparation
    courtroom_setup_notes: str = ""
    team_assignments: Dict[str, List[str]] = field(default_factory=dict)  # Role -> responsibilities
    client_preparation_notes: str = ""
    media_considerations: str = ""
    
    # Real-time tracking during trial
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    unexpected_events: List[str] = field(default_factory=list)
    
    # Daily outcomes
    objectives_achieved: List[str] = field(default_factory=list)
    objectives_deferred: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    
    # Next day planning
    carry_over_items: List[str] = field(default_factory=list)
    next_day_adjustments: List[str] = field(default_factory=list)
    
    # Notes and observations
    judge_observations: str = ""
    jury_observations: str = ""
    opposing_counsel_observations: str = ""
    general_trial_notes: str = ""
    
    # Status tracking
    day_completed: bool = False
    day_assessment_score: Optional[float] = None  # 1-10 scale
    
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)

@dataclass
class TrialNotebook:
    """Complete digital trial notebook for case management."""
    notebook_id: str
    case_id: str
    case_name: str
    trial_start_date: Optional[date] = None
    trial_end_date: Optional[date] = None
    
    # Trial information
    court: str = ""
    judge: str = ""
    case_number: str = ""
    trial_type: str = "jury"  # jury, bench, arbitration
    estimated_trial_days: int = 0
    
    # Parties and representation
    plaintiff_counsel: List[str] = field(default_factory=list)
    defendant_counsel: List[str] = field(default_factory=list)
    trial_team_members: Dict[str, str] = field(default_factory=dict)  # Name -> Role
    
    # Day-by-day planning
    trial_days: Dict[str, TrialDayPlan] = field(default_factory=dict)  # Day ID -> Plan
    day_order: List[str] = field(default_factory=list)  # Ordered day IDs
    
    # Master schedules and tracking
    master_witness_list: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # Witness ID -> details
    master_exhibit_list: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # Exhibit ID -> details
    motion_tracker: Dict[str, MotionTracking] = field(default_factory=dict)  # Motion ID -> tracking
    
    # Overall trial strategy
    trial_theme: str = ""
    opening_statement_outline: List[str] = field(default_factory=list)
    closing_argument_outline: List[str] = field(default_factory=list)
    key_legal_arguments: List[str] = field(default_factory=list)
    
    # Jury management
    jury_selection_strategy: str = ""
    jury_profile_notes: str = ""
    jury_instruction_requests: List[str] = field(default_factory=list)
    
    # Risk management
    identified_risks: List[str] = field(default_factory=list)
    contingency_plans: Dict[str, List[str]] = field(default_factory=dict)  # Risk -> Plans
    
    # Trial phase tracking
    current_phase: TrialPhase = TrialPhase.PRE_TRIAL
    current_day: Optional[str] = None  # Current day ID
    
    # Performance tracking
    trial_metrics: Dict[str, Any] = field(default_factory=dict)
    daily_assessments: List[Dict[str, Any]] = field(default_factory=list)
    
    # Administrative
    budget_tracking: Dict[str, float] = field(default_factory=dict)
    expense_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Post-trial
    trial_outcome: Optional[str] = None
    verdict_details: Dict[str, Any] = field(default_factory=dict)
    post_trial_motions: List[str] = field(default_factory=list)
    appeal_considerations: List[str] = field(default_factory=list)
    
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)

class TrialPlanner:
    """Plans and optimizes trial day schedules."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".TrialPlanner")
    
    def generate_optimal_schedule(self, trial_day_plan: TrialDayPlan,
                                available_witnesses: List[Dict[str, Any]],
                                required_exhibits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate optimal schedule for trial day."""
        schedule = {
            'morning_schedule': [],
            'afternoon_schedule': [],
            'timing_analysis': {},
            'resource_conflicts': [],
            'recommendations': []
        }
        
        # Calculate available time
        total_minutes = self._calculate_session_minutes(trial_day_plan)
        morning_minutes = total_minutes // 2
        afternoon_minutes = total_minutes - morning_minutes
        
        # Sort witnesses by priority and estimated duration
        sorted_witnesses = sorted(available_witnesses, 
                                key=lambda w: (-w.get('importance', 3), w.get('duration', 60)))
        
        # Schedule morning session
        morning_time_used = 0
        afternoon_time_used = 0
        
        for witness in sorted_witnesses:
            duration = witness.get('duration', 60)
            
            if morning_time_used + duration <= morning_minutes:
                schedule['morning_schedule'].append({
                    'witness_id': witness.get('witness_id'),
                    'witness_name': witness.get('name'),
                    'start_time': self._calculate_start_time(trial_day_plan.morning_session.start_time, 
                                                           morning_time_used),
                    'duration': duration,
                    'examination_type': witness.get('examination_type', 'direct')
                })
                morning_time_used += duration
            elif afternoon_time_used + duration <= afternoon_minutes:
                schedule['afternoon_schedule'].append({
                    'witness_id': witness.get('witness_id'),
                    'witness_name': witness.get('name'),
                    'start_time': self._calculate_start_time(trial_day_plan.afternoon_session.start_time, 
                                                           afternoon_time_used),
                    'duration': duration,
                    'examination_type': witness.get('examination_type', 'direct')
                })
                afternoon_time_used += duration
            else:
                schedule['resource_conflicts'].append(f"Insufficient time for witness {witness.get('name')}")
        
        # Timing analysis
        schedule['timing_analysis'] = {
            'morning_utilization': (morning_time_used / morning_minutes) * 100,
            'afternoon_utilization': (afternoon_time_used / afternoon_minutes) * 100,
            'buffer_time_morning': morning_minutes - morning_time_used,
            'buffer_time_afternoon': afternoon_minutes - afternoon_time_used
        }
        
        # Generate recommendations
        recommendations = []
        if schedule['timing_analysis']['morning_utilization'] > 90:
            recommendations.append("Morning schedule very tight - consider moving witness to afternoon")
        
        if len(schedule['resource_conflicts']) > 0:
            recommendations.append("Schedule conflicts identified - review witness priorities")
        
        schedule['recommendations'] = recommendations
        
        return schedule
    
    def identify_scheduling_conflicts(self, trial_day_plan: TrialDayPlan) -> List[Dict[str, Any]]:
        """Identify potential scheduling conflicts in trial day plan."""
        conflicts = []
        
        # Check witness timing conflicts
        witness_times = []
        for witness in trial_day_plan.witness_schedule:
            if witness.scheduled_time:
                witness_times.append((witness.scheduled_time, witness.witness_name, witness.estimated_duration_minutes))
        
        # Sort by scheduled time
        witness_times.sort(key=lambda x: x[0])
        
        # Check for overlaps
        for i in range(len(witness_times) - 1):
            current_start = witness_times[i][0]
            current_end = self._add_minutes_to_time(current_start, witness_times[i][2])
            next_start = witness_times[i + 1][0]
            
            if current_end > next_start:
                conflicts.append({
                    'type': 'witness_overlap',
                    'description': f"Witness {witness_times[i][1]} scheduled until {current_end} but {witness_times[i + 1][1]} starts at {next_start}",
                    'severity': 'high',
                    'witnesses_involved': [witness_times[i][1], witness_times[i + 1][1]]
                })
        
        # Check exhibit preparation conflicts
        exhibit_times = defaultdict(list)
        for exhibit in trial_day_plan.exhibit_schedule:
            if exhibit.planned_introduction_time:
                exhibit_times[exhibit.planned_introduction_time].append(exhibit.exhibit_number)
        
        for time_slot, exhibits in exhibit_times.items():
            if len(exhibits) > 1:
                conflicts.append({
                    'type': 'exhibit_timing_conflict',
                    'description': f"Multiple exhibits ({', '.join(exhibits)}) scheduled for {time_slot}",
                    'severity': 'medium',
                    'exhibits_involved': exhibits
                })
        
        # Check technology resource conflicts
        tech_needs_by_time = defaultdict(list)
        for witness in trial_day_plan.witness_schedule:
            if witness.scheduled_time and witness.exhibits_to_use:
                tech_needs_by_time[witness.scheduled_time].extend(witness.exhibits_to_use)
        
        for time_slot, exhibit_ids in tech_needs_by_time.items():
            if len(exhibit_ids) > len(set(exhibit_ids)):  # Duplicate exhibit usage
                conflicts.append({
                    'type': 'technology_resource_conflict',
                    'description': f"Technology conflicts at {time_slot}",
                    'severity': 'medium'
                })
        
        return conflicts
    
    def suggest_schedule_optimizations(self, trial_day_plan: TrialDayPlan) -> List[str]:
        """Suggest optimizations for trial day schedule."""
        suggestions = []
        
        # Analyze witness order efficiency
        witness_schedule = trial_day_plan.witness_schedule
        if len(witness_schedule) > 1:
            # Check for logical witness order
            examination_types = [w.examination_type for w in witness_schedule]
            
            # Suggest grouping direct examinations
            direct_count = examination_types.count('direct')
            cross_count = examination_types.count('cross')
            
            if direct_count > 0 and cross_count > 0:
                # Check if they're intermixed inefficiently
                current_pattern = ''.join(['D' if ex == 'direct' else 'C' for ex in examination_types])
                if 'DC' in current_pattern and 'CD' in current_pattern:
                    suggestions.append("Consider grouping direct examinations together to maintain narrative flow")
        
        # Analyze timing efficiency
        total_scheduled_time = sum(w.estimated_duration_minutes for w in witness_schedule)
        available_time = self._calculate_session_minutes(trial_day_plan)
        
        utilization = (total_scheduled_time / available_time) * 100
        
        if utilization > 90:
            suggestions.append("Schedule is very tight - consider buffer time for unexpected delays")
        elif utilization < 60:
            suggestions.append("Significant unused time - consider adding backup witnesses or additional testimony")
        
        # Technology setup optimization
        tech_exhibits = [ex for ex in trial_day_plan.exhibit_schedule if ex.exhibit_number.startswith('V') or ex.exhibit_number.startswith('A')]
        if len(tech_exhibits) > 1:
            suggestions.append("Multiple technology exhibits - consider grouping to minimize setup time")
        
        # Break optimization
        if total_scheduled_time > 240:  # More than 4 hours
            break_count = len(trial_day_plan.other_breaks)
            if break_count < 2:
                suggestions.append("Long trial day - consider additional breaks for jury comfort")
        
        return suggestions
    
    def _calculate_session_minutes(self, trial_day_plan: TrialDayPlan) -> int:
        """Calculate total available session minutes."""
        start_time = trial_day_plan.court_session_start
        end_time = trial_day_plan.court_session_end
        
        total_minutes = (datetime.combine(date.today(), end_time) - 
                        datetime.combine(date.today(), start_time)).total_seconds() / 60
        
        # Subtract break times
        if trial_day_plan.lunch_break:
            lunch_minutes = trial_day_plan.lunch_break.duration_minutes
            total_minutes -= lunch_minutes
        
        for break_time in trial_day_plan.other_breaks:
            total_minutes -= break_time.duration_minutes
        
        return int(total_minutes)
    
    def _calculate_start_time(self, session_start: time, minutes_offset: int) -> time:
        """Calculate start time with minutes offset."""
        start_datetime = datetime.combine(date.today(), session_start)
        offset_datetime = start_datetime + timedelta(minutes=minutes_offset)
        return offset_datetime.time()
    
    def _add_minutes_to_time(self, time_obj: time, minutes: int) -> time:
        """Add minutes to a time object."""
        datetime_obj = datetime.combine(date.today(), time_obj)
        new_datetime = datetime_obj + timedelta(minutes=minutes)
        return new_datetime.time()

class TrialTracker:
    """Tracks real-time trial progress and updates."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".TrialTracker")
    
    def track_witness_testimony(self, trial_day_plan: TrialDayPlan, witness_id: str,
                               event_type: str, timestamp: datetime, notes: str = "") -> bool:
        """Track witness testimony events in real-time."""
        witness_schedule = None
        for w in trial_day_plan.witness_schedule:
            if w.witness_id == witness_id:
                witness_schedule = w
                break
        
        if not witness_schedule:
            return False
        
        # Update witness status based on event
        if event_type == "called":
            witness_schedule.status = WitnessStatus.CALLED
        elif event_type == "testimony_started":
            witness_schedule.status = WitnessStatus.TESTIFYING
            witness_schedule.actual_start_time = timestamp.time()
        elif event_type == "testimony_completed":
            witness_schedule.status = WitnessStatus.COMPLETED
            witness_schedule.actual_end_time = timestamp.time()
        elif event_type == "continued":
            witness_schedule.status = WitnessStatus.CONTINUED
        
        # Add performance notes
        if notes:
            if witness_schedule.performance_notes:
                witness_schedule.performance_notes += f"\n[{timestamp.strftime('%H:%M')}] {notes}"
            else:
                witness_schedule.performance_notes = f"[{timestamp.strftime('%H:%M')}] {notes}"
        
        self.logger.info(f"Tracked witness event: {witness_id} - {event_type}")
        return True
    
    def track_exhibit_action(self, trial_day_plan: TrialDayPlan, exhibit_id: str,
                           action: ExhibitAction, timestamp: datetime, notes: str = "") -> bool:
        """Track exhibit actions during trial."""
        exhibit_schedule = None
        for ex in trial_day_plan.exhibit_schedule:
            if ex.exhibit_id == exhibit_id:
                exhibit_schedule = ex
                break
        
        if not exhibit_schedule:
            return False
        
        # Record action
        exhibit_schedule.actions_taken.append((timestamp, action, notes))
        
        # Update status
        if action == ExhibitAction.MARKED_FOR_ID:
            exhibit_schedule.current_status = "marked_for_identification"
        elif action == ExhibitAction.ADMITTED:
            exhibit_schedule.current_status = "admitted"
            exhibit_schedule.court_ruling = "admitted"
        elif action == ExhibitAction.OBJECTED:
            exhibit_schedule.current_status = "objected"
        elif action == ExhibitAction.WITHDRAWN:
            exhibit_schedule.current_status = "withdrawn"
        
        self.logger.info(f"Tracked exhibit action: {exhibit_id} - {action.value}")
        return True
    
    def track_motion_filing(self, motion_tracking: MotionTracking, 
                          filing_timestamp: datetime, motion_text: str) -> bool:
        """Track motion filing during trial."""
        motion_tracking.filing_time = filing_timestamp
        motion_tracking.full_text = motion_text
        
        self.logger.info(f"Tracked motion filing: {motion_tracking.motion_id}")
        return True
    
    def track_court_ruling(self, motion_tracking: MotionTracking,
                         ruling: str, timestamp: datetime, rationale: str = "") -> bool:
        """Track court ruling on motion."""
        motion_tracking.court_ruling = ruling
        motion_tracking.ruling_date = timestamp
        motion_tracking.ruling_rationale = rationale
        
        self.logger.info(f"Tracked court ruling: {motion_tracking.motion_id} - {ruling}")
        return True
    
    def generate_daily_summary(self, trial_day_plan: TrialDayPlan) -> Dict[str, Any]:
        """Generate summary of trial day activities."""
        summary = {
            'day_info': {
                'date': trial_day_plan.trial_date,
                'day_number': trial_day_plan.day_number,
                'day_type': trial_day_plan.day_type.value
            },
            'witness_summary': {},
            'exhibit_summary': {},
            'timing_summary': {},
            'achievements': [],
            'challenges': [],
            'next_day_preparation': []
        }
        
        # Witness summary
        witnesses_called = [w for w in trial_day_plan.witness_schedule if w.status in [WitnessStatus.COMPLETED, WitnessStatus.TESTIFYING]]
        witnesses_completed = [w for w in trial_day_plan.witness_schedule if w.status == WitnessStatus.COMPLETED]
        
        summary['witness_summary'] = {
            'total_scheduled': len(trial_day_plan.witness_schedule),
            'witnesses_called': len(witnesses_called),
            'witnesses_completed': len(witnesses_completed),
            'witnesses_continuing': len([w for w in trial_day_plan.witness_schedule if w.status == WitnessStatus.CONTINUED])
        }
        
        # Exhibit summary
        exhibits_introduced = [ex for ex in trial_day_plan.exhibit_schedule if ex.actions_taken]
        exhibits_admitted = [ex for ex in trial_day_plan.exhibit_schedule if ex.current_status == "admitted"]
        
        summary['exhibit_summary'] = {
            'total_planned': len(trial_day_plan.exhibit_schedule),
            'exhibits_introduced': len(exhibits_introduced),
            'exhibits_admitted': len(exhibits_admitted),
            'exhibits_objected': len([ex for ex in trial_day_plan.exhibit_schedule if ex.current_status == "objected"])
        }
        
        # Timing summary
        if trial_day_plan.actual_start_time and trial_day_plan.actual_end_time:
            actual_duration = trial_day_plan.actual_end_time - trial_day_plan.actual_start_time
            summary['timing_summary'] = {
                'planned_start': trial_day_plan.court_session_start.strftime('%H:%M'),
                'actual_start': trial_day_plan.actual_start_time.strftime('%H:%M'),
                'planned_end': trial_day_plan.court_session_end.strftime('%H:%M'),
                'actual_end': trial_day_plan.actual_end_time.strftime('%H:%M'),
                'actual_duration_hours': actual_duration.total_seconds() / 3600
            }
        
        # Achievements and challenges
        summary['achievements'] = trial_day_plan.objectives_achieved
        summary['challenges'] = trial_day_plan.unexpected_events
        summary['next_day_preparation'] = trial_day_plan.carry_over_items
        
        return summary

class DigitalTrialNotebook:
    """Main digital trial notebook system."""
    
    def __init__(self):
        self.trial_notebooks: Dict[str, TrialNotebook] = {}
        self.planner = TrialPlanner()
        self.tracker = TrialTracker()
        self.logger = logging.getLogger(__name__ + ".DigitalTrialNotebook")
    
    def create_trial_notebook(self, case_id: str, case_name: str,
                            trial_start_date: date, estimated_days: int,
                            court: str, judge: str) -> str:
        """Create new digital trial notebook."""
        notebook_id = str(uuid.uuid4())
        
        notebook = TrialNotebook(
            notebook_id=notebook_id,
            case_id=case_id,
            case_name=case_name,
            trial_start_date=trial_start_date,
            estimated_trial_days=estimated_days,
            court=court,
            judge=judge
        )
        
        # Generate initial trial day structure
        self._generate_initial_trial_days(notebook, trial_start_date, estimated_days)
        
        self.trial_notebooks[notebook_id] = notebook
        self.logger.info(f"Created trial notebook: {notebook_id}")
        return notebook_id
    
    def create_trial_day_plan(self, notebook_id: str, trial_date: date,
                            day_number: int, day_type: TrialDay) -> str:
        """Create detailed plan for specific trial day."""
        if notebook_id not in self.trial_notebooks:
            raise ValueError(f"Trial notebook {notebook_id} not found")
        
        notebook = self.trial_notebooks[notebook_id]
        day_id = str(uuid.uuid4())
        
        # Create standard time blocks
        morning_session = TimeBlock(
            start_time=time(9, 0),
            end_time=time(12, 0),
            duration_minutes=180,
            description="Morning session"
        )
        
        lunch_break = TimeBlock(
            start_time=time(12, 0),
            end_time=time(13, 30),
            duration_minutes=90,
            description="Lunch break"
        )
        
        afternoon_session = TimeBlock(
            start_time=time(13, 30),
            end_time=time(17, 0),
            duration_minutes=210,
            description="Afternoon session"
        )
        
        trial_day_plan = TrialDayPlan(
            day_id=day_id,
            trial_date=trial_date,
            day_number=day_number,
            day_type=day_type,
            morning_session=morning_session,
            lunch_break=lunch_break,
            afternoon_session=afternoon_session
        )
        
        # Set day-specific objectives based on type
        trial_day_plan.primary_objectives = self._get_default_objectives(day_type)
        
        notebook.trial_days[day_id] = trial_day_plan
        if day_id not in notebook.day_order:
            notebook.day_order.append(day_id)
        
        self.logger.info(f"Created trial day plan: {day_id} for {trial_date}")
        return day_id
    
    def schedule_witness(self, notebook_id: str, day_id: str, witness_id: str,
                       witness_name: str, examination_type: str,
                       scheduled_time: time, duration_minutes: int = 60) -> bool:
        """Schedule witness for specific trial day."""
        if (notebook_id not in self.trial_notebooks or
            day_id not in self.trial_notebooks[notebook_id].trial_days):
            return False
        
        trial_day = self.trial_notebooks[notebook_id].trial_days[day_id]
        
        witness_schedule = WitnessSchedule(
            witness_id=witness_id,
            witness_name=witness_name,
            examination_type=examination_type,
            scheduled_time=scheduled_time,
            estimated_duration_minutes=duration_minutes
        )
        
        trial_day.witness_schedule.append(witness_schedule)
        
        # Add to master witness list if not exists
        notebook = self.trial_notebooks[notebook_id]
        if witness_id not in notebook.master_witness_list:
            notebook.master_witness_list[witness_id] = {
                'name': witness_name,
                'scheduled_days': [],
                'testimony_status': 'scheduled'
            }
        
        notebook.master_witness_list[witness_id]['scheduled_days'].append(day_id)
        
        self.logger.info(f"Scheduled witness {witness_name} for {trial_day.trial_date}")
        return True
    
    def schedule_exhibit(self, notebook_id: str, day_id: str, exhibit_id: str,
                       exhibit_number: str, planned_time: time,
                       introducing_witness: str) -> bool:
        """Schedule exhibit introduction for trial day."""
        if (notebook_id not in self.trial_notebooks or
            day_id not in self.trial_notebooks[notebook_id].trial_days):
            return False
        
        trial_day = self.trial_notebooks[notebook_id].trial_days[day_id]
        
        exhibit_schedule = ExhibitSchedule(
            exhibit_id=exhibit_id,
            exhibit_number=exhibit_number,
            planned_introduction_time=planned_time,
            introducing_witness=introducing_witness
        )
        
        trial_day.exhibit_schedule.append(exhibit_schedule)
        
        # Add to master exhibit list
        notebook = self.trial_notebooks[notebook_id]
        if exhibit_id not in notebook.master_exhibit_list:
            notebook.master_exhibit_list[exhibit_id] = {
                'exhibit_number': exhibit_number,
                'scheduled_day': day_id,
                'status': 'scheduled'
            }
        
        self.logger.info(f"Scheduled exhibit {exhibit_number} for {trial_day.trial_date}")
        return True
    
    def optimize_day_schedule(self, notebook_id: str, day_id: str) -> Dict[str, Any]:
        """Optimize schedule for specific trial day."""
        if (notebook_id not in self.trial_notebooks or
            day_id not in self.trial_notebooks[notebook_id].trial_days):
            return {'error': 'Trial day not found'}
        
        trial_day = self.trial_notebooks[notebook_id].trial_days[day_id]
        
        # Prepare witness data for optimization
        available_witnesses = []
        for witness in trial_day.witness_schedule:
            available_witnesses.append({
                'witness_id': witness.witness_id,
                'name': witness.witness_name,
                'duration': witness.estimated_duration_minutes,
                'examination_type': witness.examination_type,
                'importance': 3  # Default importance
            })
        
        # Prepare exhibit data
        required_exhibits = []
        for exhibit in trial_day.exhibit_schedule:
            required_exhibits.append({
                'exhibit_id': exhibit.exhibit_id,
                'exhibit_number': exhibit.exhibit_number,
                'importance': exhibit.importance_level
            })
        
        # Generate optimal schedule
        optimization = self.planner.generate_optimal_schedule(
            trial_day, available_witnesses, required_exhibits
        )
        
        # Identify conflicts
        conflicts = self.planner.identify_scheduling_conflicts(trial_day)
        optimization['conflicts'] = conflicts
        
        # Get suggestions
        suggestions = self.planner.suggest_schedule_optimizations(trial_day)
        optimization['optimization_suggestions'] = suggestions
        
        return optimization
    
    def start_trial_day(self, notebook_id: str, day_id: str) -> bool:
        """Start trial day tracking."""
        if (notebook_id not in self.trial_notebooks or
            day_id not in self.trial_notebooks[notebook_id].trial_days):
            return False
        
        trial_day = self.trial_notebooks[notebook_id].trial_days[day_id]
        trial_day.actual_start_time = datetime.now()
        
        # Update notebook current day
        notebook = self.trial_notebooks[notebook_id]
        notebook.current_day = day_id
        
        self.logger.info(f"Started trial day: {trial_day.trial_date}")
        return True
    
    def track_witness_event(self, notebook_id: str, day_id: str, witness_id: str,
                          event_type: str, notes: str = "") -> bool:
        """Track witness event during trial."""
        if (notebook_id not in self.trial_notebooks or
            day_id not in self.trial_notebooks[notebook_id].trial_days):
            return False
        
        trial_day = self.trial_notebooks[notebook_id].trial_days[day_id]
        return self.tracker.track_witness_testimony(trial_day, witness_id, event_type, 
                                                  datetime.now(), notes)
    
    def track_exhibit_event(self, notebook_id: str, day_id: str, exhibit_id: str,
                          action: ExhibitAction, notes: str = "") -> bool:
        """Track exhibit event during trial."""
        if (notebook_id not in self.trial_notebooks or
            day_id not in self.trial_notebooks[notebook_id].trial_days):
            return False
        
        trial_day = self.trial_notebooks[notebook_id].trial_days[day_id]
        return self.tracker.track_exhibit_action(trial_day, exhibit_id, action,
                                               datetime.now(), notes)
    
    def end_trial_day(self, notebook_id: str, day_id: str, assessment_score: float,
                    objectives_achieved: List[str], lessons_learned: List[str]) -> bool:
        """End trial day and record outcomes."""
        if (notebook_id not in self.trial_notebooks or
            day_id not in self.trial_notebooks[notebook_id].trial_days):
            return False
        
        trial_day = self.trial_notebooks[notebook_id].trial_days[day_id]
        trial_day.actual_end_time = datetime.now()
        trial_day.day_completed = True
        trial_day.day_assessment_score = assessment_score
        trial_day.objectives_achieved = objectives_achieved
        trial_day.lessons_learned = lessons_learned
        
        # Generate daily summary
        daily_summary = self.tracker.generate_daily_summary(trial_day)
        
        # Add to notebook daily assessments
        notebook = self.trial_notebooks[notebook_id]
        notebook.daily_assessments.append({
            'day_id': day_id,
            'date': trial_day.trial_date,
            'summary': daily_summary,
            'assessment_score': assessment_score
        })
        
        self.logger.info(f"Ended trial day: {trial_day.trial_date} with score {assessment_score}")
        return True
    
    def generate_trial_dashboard(self, notebook_id: str) -> Dict[str, Any]:
        """Generate comprehensive trial dashboard."""
        if notebook_id not in self.trial_notebooks:
            return {'error': 'Trial notebook not found'}
        
        notebook = self.trial_notebooks[notebook_id]
        
        dashboard = {
            'trial_info': {
                'case_name': notebook.case_name,
                'court': notebook.court,
                'judge': notebook.judge,
                'trial_phase': notebook.current_phase.value,
                'current_day': notebook.current_day
            },
            'progress_summary': {},
            'upcoming_schedule': {},
            'witness_status': {},
            'exhibit_status': {},
            'performance_metrics': {},
            'today_focus': {},
            'alerts_and_reminders': []
        }
        
        # Progress summary
        completed_days = len([day for day in notebook.trial_days.values() if day.day_completed])
        total_days = len(notebook.trial_days)
        
        dashboard['progress_summary'] = {
            'days_completed': completed_days,
            'total_planned_days': total_days,
            'progress_percentage': (completed_days / total_days * 100) if total_days > 0 else 0,
            'trial_start_date': notebook.trial_start_date,
            'estimated_end_date': notebook.trial_end_date
        }
        
        # Current day focus
        if notebook.current_day and notebook.current_day in notebook.trial_days:
            current_day = notebook.trial_days[notebook.current_day]
            dashboard['today_focus'] = {
                'date': current_day.trial_date,
                'day_type': current_day.day_type.value,
                'primary_objectives': current_day.primary_objectives,
                'witnesses_scheduled': len(current_day.witness_schedule),
                'exhibits_planned': len(current_day.exhibit_schedule)
            }
        
        # Performance metrics
        if notebook.daily_assessments:
            scores = [assessment['assessment_score'] for assessment in notebook.daily_assessments 
                     if assessment.get('assessment_score')]
            if scores:
                dashboard['performance_metrics'] = {
                    'average_daily_score': sum(scores) / len(scores),
                    'best_day_score': max(scores),
                    'trend': 'improving' if len(scores) > 1 and scores[-1] > scores[0] else 'stable'
                }
        
        return dashboard
    
    def search_trial_content(self, notebook_id: str, query: str) -> Dict[str, List[Any]]:
        """Search trial notebook content."""
        if notebook_id not in self.trial_notebooks:
            return {'error': 'Trial notebook not found'}
        
        notebook = self.trial_notebooks[notebook_id]
        query_lower = query.lower()
        
        results = {
            'witnesses': [],
            'exhibits': [],
            'notes': [],
            'objectives': []
        }
        
        # Search witness information
        for witness_id, witness_info in notebook.master_witness_list.items():
            if query_lower in witness_info['name'].lower():
                results['witnesses'].append({
                    'witness_id': witness_id,
                    'name': witness_info['name'],
                    'status': witness_info['testimony_status'],
                    'scheduled_days': len(witness_info['scheduled_days'])
                })
        
        # Search exhibit information
        for exhibit_id, exhibit_info in notebook.master_exhibit_list.items():
            if query_lower in exhibit_info['exhibit_number'].lower():
                results['exhibits'].append({
                    'exhibit_id': exhibit_id,
                    'exhibit_number': exhibit_info['exhibit_number'],
                    'status': exhibit_info['status']
                })
        
        # Search trial day notes
        for day_id, trial_day in notebook.trial_days.items():
            day_notes = f"{trial_day.general_trial_notes} {trial_day.judge_observations} {trial_day.jury_observations}"
            if query_lower in day_notes.lower():
                results['notes'].append({
                    'day_id': day_id,
                    'date': trial_day.trial_date,
                    'relevant_content': self._extract_relevant_content(day_notes, query_lower)
                })
        
        return results
    
    def _generate_initial_trial_days(self, notebook: TrialNotebook, 
                                   start_date: date, estimated_days: int) -> None:
        """Generate initial trial day structure."""
        current_date = start_date
        
        # Day 1: Jury Selection (if jury trial)
        if notebook.trial_type == "jury":
            day_id = self.create_trial_day_plan(notebook.notebook_id, current_date, 1, TrialDay.JURY_SELECTION)
            current_date += timedelta(days=1)
            estimated_days -= 1
        
        # Day 2: Opening Statements
        if estimated_days > 0:
            day_id = self.create_trial_day_plan(notebook.notebook_id, current_date, 2, TrialDay.OPENING_STATEMENTS)
            current_date += timedelta(days=1)
            estimated_days -= 1
        
        # Remaining days: Case presentation
        day_number = 3 if notebook.trial_type == "jury" else 2
        for i in range(estimated_days - 1):  # Reserve last day for closing
            if i < estimated_days // 2:
                day_type = TrialDay.PLAINTIFF_CASE
            else:
                day_type = TrialDay.DEFENDANT_CASE
            
            day_id = self.create_trial_day_plan(notebook.notebook_id, current_date, day_number, day_type)
            current_date += timedelta(days=1)
            day_number += 1
        
        # Final day: Closing Arguments
        if estimated_days > 0:
            day_id = self.create_trial_day_plan(notebook.notebook_id, current_date, day_number, TrialDay.CLOSING_ARGUMENTS)
    
    def _get_default_objectives(self, day_type: TrialDay) -> List[str]:
        """Get default objectives for trial day type."""
        objectives_map = {
            TrialDay.JURY_SELECTION: [
                "Select favorable jury composition",
                "Identify and challenge biased jurors",
                "Establish rapport with jury panel"
            ],
            TrialDay.OPENING_STATEMENTS: [
                "Present compelling case narrative",
                "Establish credibility with jury",
                "Preview key evidence and themes"
            ],
            TrialDay.PLAINTIFF_CASE: [
                "Present strongest evidence",
                "Establish liability elements",
                "Build damages foundation"
            ],
            TrialDay.DEFENDANT_CASE: [
                "Challenge plaintiff's evidence",
                "Present defense theory",
                "Undermine damages claims"
            ],
            TrialDay.CLOSING_ARGUMENTS: [
                "Summarize case strengths",
                "Address jury instructions",
                "Make compelling damages argument"
            ]
        }
        
        return objectives_map.get(day_type, ["Complete scheduled activities", "Advance case strategy"])
    
    def _extract_relevant_content(self, text: str, query: str) -> str:
        """Extract relevant content snippet around query match."""
        index = text.lower().find(query)
        if index == -1:
            return ""
        
        start = max(0, index - 50)
        end = min(len(text), index + len(query) + 50)
        snippet = text[start:end]
        
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet