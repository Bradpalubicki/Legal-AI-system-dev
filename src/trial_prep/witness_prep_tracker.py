"""
Witness Preparation Tracker

Advanced witness preparation tracking system including preparation sessions,
progress monitoring, readiness assessment, and performance analytics for
optimal witness preparation and trial readiness.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
import logging
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)

class PrepSessionType(Enum):
    """Types of witness preparation sessions."""
    INITIAL_INTERVIEW = "initial_interview"
    DOCUMENT_REVIEW = "document_review"
    DIRECT_EXAMINATION = "direct_examination"
    CROSS_EXAMINATION = "cross_examination"
    MOCK_TRIAL = "mock_trial"
    FINAL_PREPARATION = "final_preparation"
    EXPERT_OPINION_DEVELOPMENT = "expert_opinion_development"
    DEMONSTRATIVE_PRACTICE = "demonstrative_practice"
    HOSTILE_WITNESS_PREP = "hostile_witness_prep"
    REHABILITATION_PRACTICE = "rehabilitation_practice"
    COURTROOM_LOGISTICS = "courtroom_logistics"
    CONFIDENCE_BUILDING = "confidence_building"

class PrepSkillArea(Enum):
    """Skill areas for witness preparation."""
    CONTENT_MASTERY = "content_mastery"
    COMMUNICATION_CLARITY = "communication_clarity"
    CONFIDENCE_LEVEL = "confidence_level"
    QUESTION_LISTENING = "question_listening"
    ANSWER_PRECISION = "answer_precision"
    BODY_LANGUAGE = "body_language"
    VOICE_PROJECTION = "voice_projection"
    HANDLING_OBJECTIONS = "handling_objections"
    CROSS_EXAM_RESILIENCE = "cross_exam_resilience"
    DOCUMENT_FAMILIARITY = "document_familiarity"
    TIMELINE_KNOWLEDGE = "timeline_knowledge"
    TECHNICAL_EXPLANATION = "technical_explanation"

class ReadinessLevel(Enum):
    """Levels of witness trial readiness."""
    NOT_READY = 1
    BASIC_READY = 2
    MODERATELY_READY = 3
    WELL_PREPARED = 4
    TRIAL_READY = 5

class SessionOutcome(Enum):
    """Outcomes of preparation sessions."""
    EXCELLENT_PROGRESS = "excellent_progress"
    GOOD_PROGRESS = "good_progress"
    ADEQUATE_PROGRESS = "adequate_progress"
    LIMITED_PROGRESS = "limited_progress"
    NO_PROGRESS = "no_progress"
    REGRESSION = "regression"

class IssueCategory(Enum):
    """Categories of preparation issues."""
    CONTENT_KNOWLEDGE = "content_knowledge"
    COMMUNICATION_SKILLS = "communication_skills"
    ANXIETY_NERVOUSNESS = "anxiety_nervousness"
    CREDIBILITY_CONCERNS = "credibility_concerns"
    MEMORY_ISSUES = "memory_issues"
    HOSTILITY_DEFENSIVENESS = "hostility_defensiveness"
    TECHNICAL_COMPLEXITY = "technical_complexity"
    LANGUAGE_BARRIERS = "language_barriers"
    SCHEDULING_CONFLICTS = "scheduling_conflicts"
    COOPERATION_ISSUES = "cooperation_issues"

@dataclass
class PrepExercise:
    """Individual preparation exercise or drill."""
    exercise_id: str
    exercise_name: str
    skill_areas: List[PrepSkillArea]
    description: str
    duration_minutes: int = 0
    
    # Exercise parameters
    difficulty_level: int = 3  # 1-5 scale
    repetitions_recommended: int = 1
    success_criteria: List[str] = field(default_factory=list)
    
    # Performance tracking
    attempts: int = 0
    successful_completions: int = 0
    last_attempt_date: Optional[datetime] = None
    best_performance_score: float = 0.0
    average_score: float = 0.0
    
    # Notes and feedback
    exercise_notes: str = ""
    improvement_suggestions: List[str] = field(default_factory=list)

@dataclass
class SkillAssessment:
    """Assessment of specific skill area."""
    skill_area: PrepSkillArea
    current_score: float = 0.0  # 0-10 scale
    target_score: float = 8.0
    baseline_score: float = 0.0
    
    # Progress tracking
    score_history: List[Tuple[datetime, float]] = field(default_factory=list)
    improvement_rate: float = 0.0
    sessions_focused: int = 0
    
    # Detailed assessment
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    specific_feedback: str = ""
    
    # Improvement planning
    improvement_strategy: str = ""
    recommended_exercises: List[str] = field(default_factory=list)  # Exercise IDs
    estimated_sessions_to_target: int = 0

@dataclass
class PrepIssue:
    """Issue identified during preparation."""
    issue_id: str
    category: IssueCategory
    severity: int = 3  # 1-5 scale
    title: str = ""
    description: str = ""
    
    # Issue tracking
    identified_date: datetime = field(default_factory=datetime.now)
    identified_by: str = ""
    sessions_affected: List[str] = field(default_factory=list)
    
    # Resolution tracking
    resolved: bool = False
    resolution_date: Optional[datetime] = None
    resolution_strategy: str = ""
    resolution_notes: str = ""
    
    # Impact assessment
    impact_on_readiness: float = 0.0  # -1 to 1 scale
    requires_specialist: bool = False
    specialist_type: str = ""  # e.g., "speech coach", "anxiety counselor"

@dataclass
class MockExamination:
    """Mock examination session details."""
    mock_exam_id: str
    exam_type: str  # "direct", "cross", "redirect"
    duration_minutes: int = 0
    examiner: str = ""
    
    # Examination structure
    questions_prepared: int = 0
    questions_asked: int = 0
    questions_answered_well: int = 0
    questions_with_issues: int = 0
    
    # Performance metrics
    overall_performance_score: float = 0.0  # 0-10 scale
    confidence_level: float = 0.0  # 0-10 scale
    clarity_score: float = 0.0  # 0-10 scale
    responsiveness_score: float = 0.0  # 0-10 scale
    
    # Detailed feedback
    strong_areas: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    specific_question_feedback: Dict[str, str] = field(default_factory=dict)
    
    # Follow-up requirements
    follow_up_needed: List[str] = field(default_factory=list)
    additional_practice_areas: List[str] = field(default_factory=list)
    
    # Recording and review
    recorded: bool = False
    recording_reviewed: bool = False
    transcript_available: bool = False
    
    created_date: datetime = field(default_factory=datetime.now)

@dataclass
class PrepSession:
    """Detailed witness preparation session."""
    session_id: str
    witness_id: str
    session_type: PrepSessionType
    session_date: datetime
    duration_minutes: int = 0
    
    # Session participants
    lead_attorney: str = ""
    supporting_attorneys: List[str] = field(default_factory=list)
    paralegal: Optional[str] = None
    other_participants: List[str] = field(default_factory=list)
    
    # Session structure
    agenda_items: List[str] = field(default_factory=list)
    materials_used: List[str] = field(default_factory=list)
    exercises_completed: List[str] = field(default_factory=list)  # Exercise IDs
    
    # Session outcomes
    session_outcome: SessionOutcome = SessionOutcome.ADEQUATE_PROGRESS
    objectives_met: List[str] = field(default_factory=list)
    objectives_missed: List[str] = field(default_factory=list)
    
    # Performance assessment
    skill_assessments: Dict[str, float] = field(default_factory=dict)  # Skill -> Score
    overall_session_score: float = 0.0  # 0-10 scale
    witness_engagement_level: float = 0.0  # 0-10 scale
    
    # Issues and challenges
    issues_identified: List[str] = field(default_factory=list)  # Issue IDs
    challenges_encountered: List[str] = field(default_factory=list)
    breakthrough_moments: List[str] = field(default_factory=list)
    
    # Mock examinations
    mock_exams_conducted: List[str] = field(default_factory=list)  # Mock exam IDs
    
    # Session notes and feedback
    attorney_notes: str = ""
    witness_feedback: str = ""
    observer_notes: str = ""
    
    # Follow-up planning
    homework_assigned: List[str] = field(default_factory=list)
    next_session_focus: List[str] = field(default_factory=list)
    recommended_follow_up_date: Optional[datetime] = None
    
    # Progress indicators
    readiness_level_before: ReadinessLevel = ReadinessLevel.NOT_READY
    readiness_level_after: ReadinessLevel = ReadinessLevel.NOT_READY
    confidence_improvement: float = 0.0  # -5 to 5 scale
    
    # Administrative
    session_cost: Optional[float] = None
    billing_notes: str = ""
    created_by: str = ""

@dataclass
class WitnessReadinessReport:
    """Comprehensive witness readiness assessment."""
    report_id: str
    witness_id: str
    assessment_date: datetime
    assessor: str = ""
    
    # Overall readiness
    overall_readiness_level: ReadinessLevel = ReadinessLevel.NOT_READY
    overall_readiness_score: float = 0.0  # 0-100 scale
    trial_ready: bool = False
    
    # Skill area breakdown
    skill_scores: Dict[PrepSkillArea, float] = field(default_factory=dict)
    skill_readiness: Dict[PrepSkillArea, ReadinessLevel] = field(default_factory=dict)
    
    # Preparation statistics
    total_prep_hours: float = 0.0
    sessions_completed: int = 0
    exercises_completed: int = 0
    mock_exams_completed: int = 0
    
    # Progress analysis
    improvement_trajectory: str = ""  # "improving", "plateaued", "declining"
    weeks_in_preparation: int = 0
    sessions_remaining_recommended: int = 0
    estimated_hours_remaining: float = 0.0
    
    # Issue summary
    critical_issues: List[str] = field(default_factory=list)
    moderate_issues: List[str] = field(default_factory=list)
    resolved_issues: List[str] = field(default_factory=list)
    
    # Strengths and concerns
    key_strengths: List[str] = field(default_factory=list)
    major_concerns: List[str] = field(default_factory=list)
    
    # Recommendations
    immediate_actions: List[str] = field(default_factory=list)
    continued_focus_areas: List[str] = field(default_factory=list)
    specialist_referrals: List[str] = field(default_factory=list)
    
    # Trial day readiness
    direct_exam_ready: bool = False
    cross_exam_ready: bool = False
    redirect_ready: bool = False
    courtroom_procedure_ready: bool = False
    
    # Confidence and psychological readiness
    confidence_level: float = 0.0  # 0-10 scale
    anxiety_level: float = 0.0  # 0-10 scale (lower is better)
    stress_management_ready: bool = False
    
    # Final recommendations
    trial_participation_recommendation: str = ""
    backup_witness_recommended: bool = False
    additional_preparation_critical: bool = False
    
    # Report metadata
    report_version: int = 1
    previous_report_id: Optional[str] = None
    next_assessment_recommended: Optional[datetime] = None

class PrepAnalyzer:
    """Analyzes witness preparation progress and effectiveness."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".PrepAnalyzer")
    
    def analyze_preparation_effectiveness(self, sessions: List[PrepSession],
                                        skill_assessments: Dict[str, SkillAssessment]) -> Dict[str, Any]:
        """Analyze overall effectiveness of preparation program."""
        analysis = {
            'effectiveness_score': 0.0,
            'progress_metrics': {},
            'session_analysis': {},
            'skill_development': {},
            'time_efficiency': {},
            'recommendations': []
        }
        
        if not sessions:
            return analysis
        
        # Calculate progress metrics
        total_hours = sum(s.duration_minutes for s in sessions) / 60.0
        session_scores = [s.overall_session_score for s in sessions if s.overall_session_score > 0]
        
        if session_scores:
            avg_session_score = statistics.mean(session_scores)
            score_trend = self._calculate_trend(session_scores)
        else:
            avg_session_score = 0.0
            score_trend = 0.0
        
        analysis['progress_metrics'] = {
            'total_preparation_hours': total_hours,
            'total_sessions': len(sessions),
            'average_session_score': avg_session_score,
            'score_improvement_trend': score_trend,
            'sessions_per_week': self._calculate_session_frequency(sessions)
        }
        
        # Session type analysis
        session_types = defaultdict(list)
        for session in sessions:
            session_types[session.session_type].append(session.overall_session_score)
        
        session_effectiveness = {}
        for session_type, scores in session_types.items():
            if scores:
                session_effectiveness[session_type.value] = {
                    'count': len(scores),
                    'average_score': statistics.mean(scores),
                    'effectiveness': statistics.mean(scores) / 10.0  # Convert to 0-1 scale
                }
        
        analysis['session_analysis'] = session_effectiveness
        
        # Skill development analysis
        skill_development = {}
        for skill_area, assessment in skill_assessments.items():
            if assessment.score_history:
                initial_score = assessment.score_history[0][1]
                current_score = assessment.current_score
                improvement = current_score - initial_score
                
                skill_development[skill_area.value] = {
                    'initial_score': initial_score,
                    'current_score': current_score,
                    'improvement': improvement,
                    'improvement_rate': assessment.improvement_rate,
                    'target_progress': (current_score / assessment.target_score) * 100
                }
        
        analysis['skill_development'] = skill_development
        
        # Time efficiency analysis
        hours_per_skill_point = {}
        if total_hours > 0:
            for skill_area, development in skill_development.items():
                if development['improvement'] > 0:
                    hours_per_skill_point[skill_area] = total_hours / development['improvement']
        
        analysis['time_efficiency'] = {
            'hours_per_session': total_hours / len(sessions) if sessions else 0,
            'hours_per_skill_point_improvement': hours_per_skill_point,
            'efficiency_score': self._calculate_efficiency_score(total_hours, skill_development)
        }
        
        # Calculate overall effectiveness
        factors = []
        if avg_session_score > 0:
            factors.append(avg_session_score / 10.0)  # Normalize to 0-1
        if score_trend > 0:
            factors.append(min(score_trend, 1.0))  # Cap at 1.0
        
        skill_improvements = [dev['improvement'] for dev in skill_development.values() if dev['improvement'] > 0]
        if skill_improvements:
            avg_skill_improvement = statistics.mean(skill_improvements)
            factors.append(min(avg_skill_improvement / 5.0, 1.0))  # Normalize assuming max 5-point improvement
        
        if factors:
            analysis['effectiveness_score'] = statistics.mean(factors)
        
        # Generate recommendations
        recommendations = []
        
        if analysis['effectiveness_score'] < 0.6:
            recommendations.append("Consider revising preparation approach - effectiveness below 60%")
        
        if score_trend < 0:
            recommendations.append("Address declining session performance")
        
        inefficient_skills = [skill for skill, hours in hours_per_skill_point.items() if hours > 10]
        if inefficient_skills:
            recommendations.append(f"Focus on more efficient methods for: {', '.join(inefficient_skills)}")
        
        analysis['recommendations'] = recommendations
        
        return analysis
    
    def assess_witness_readiness(self, witness_id: str, sessions: List[PrepSession],
                               skill_assessments: Dict[PrepSkillArea, SkillAssessment],
                               issues: List[PrepIssue]) -> WitnessReadinessReport:
        """Generate comprehensive readiness assessment."""
        report = WitnessReadinessReport(
            report_id=str(uuid.uuid4()),
            witness_id=witness_id,
            assessment_date=datetime.now()
        )
        
        # Calculate preparation statistics
        report.total_prep_hours = sum(s.duration_minutes for s in sessions) / 60.0
        report.sessions_completed = len(sessions)
        report.exercises_completed = sum(len(s.exercises_completed) for s in sessions)
        report.mock_exams_completed = sum(len(s.mock_exams_conducted) for s in sessions)
        
        if sessions:
            first_session = min(sessions, key=lambda s: s.session_date)
            weeks_prep = (datetime.now() - first_session.session_date).days / 7
            report.weeks_in_preparation = max(1, int(weeks_prep))
        
        # Assess skill readiness
        skill_scores = {}
        skill_readiness_levels = {}
        
        for skill_area, assessment in skill_assessments.items():
            skill_scores[skill_area] = assessment.current_score
            
            # Determine readiness level based on score
            score = assessment.current_score
            if score >= 9.0:
                readiness = ReadinessLevel.TRIAL_READY
            elif score >= 7.0:
                readiness = ReadinessLevel.WELL_PREPARED
            elif score >= 5.0:
                readiness = ReadinessLevel.MODERATELY_READY
            elif score >= 3.0:
                readiness = ReadinessLevel.BASIC_READY
            else:
                readiness = ReadinessLevel.NOT_READY
            
            skill_readiness_levels[skill_area] = readiness
        
        report.skill_scores = skill_scores
        report.skill_readiness = skill_readiness_levels
        
        # Calculate overall readiness
        if skill_scores:
            avg_skill_score = statistics.mean(skill_scores.values())
            report.overall_readiness_score = (avg_skill_score / 10.0) * 100
            
            # Determine overall readiness level
            if avg_skill_score >= 8.5:
                report.overall_readiness_level = ReadinessLevel.TRIAL_READY
            elif avg_skill_score >= 7.0:
                report.overall_readiness_level = ReadinessLevel.WELL_PREPARED
            elif avg_skill_score >= 5.5:
                report.overall_readiness_level = ReadinessLevel.MODERATELY_READY
            elif avg_skill_score >= 3.5:
                report.overall_readiness_level = ReadinessLevel.BASIC_READY
            else:
                report.overall_readiness_level = ReadinessLevel.NOT_READY
        
        # Analyze issues
        critical_issues = [i for i in issues if not i.resolved and i.severity >= 4]
        moderate_issues = [i for i in issues if not i.resolved and 2 <= i.severity < 4]
        resolved_issues = [i for i in issues if i.resolved]
        
        report.critical_issues = [i.title for i in critical_issues]
        report.moderate_issues = [i.title for i in moderate_issues]
        report.resolved_issues = [i.title for i in resolved_issues]
        
        # Determine trial readiness
        report.trial_ready = (
            report.overall_readiness_level.value >= 4 and
            len(critical_issues) == 0 and
            report.total_prep_hours >= 10  # Minimum preparation threshold
        )
        
        # Specific examination readiness
        content_mastery = skill_scores.get(PrepSkillArea.CONTENT_MASTERY, 0)
        communication_clarity = skill_scores.get(PrepSkillArea.COMMUNICATION_CLARITY, 0)
        cross_exam_resilience = skill_scores.get(PrepSkillArea.CROSS_EXAM_RESILIENCE, 0)
        
        report.direct_exam_ready = content_mastery >= 7.0 and communication_clarity >= 7.0
        report.cross_exam_ready = cross_exam_resilience >= 6.0 and communication_clarity >= 6.0
        report.redirect_ready = content_mastery >= 6.0
        report.courtroom_procedure_ready = True  # Would check specific logistics skills
        
        # Confidence and psychological assessment
        confidence_scores = [s.witness_engagement_level for s in sessions if s.witness_engagement_level > 0]
        if confidence_scores:
            report.confidence_level = statistics.mean(confidence_scores)
        
        # Estimate remaining preparation needs
        if not report.trial_ready:
            target_score = 8.0
            current_avg = statistics.mean(skill_scores.values()) if skill_scores else 0
            score_gap = target_score - current_avg
            
            if score_gap > 0 and report.weeks_in_preparation > 0:
                improvement_rate = current_avg / report.weeks_in_preparation
                if improvement_rate > 0:
                    weeks_needed = score_gap / improvement_rate
                    report.sessions_remaining_recommended = max(1, int(weeks_needed * 1.5))  # 1.5 sessions/week
                    report.estimated_hours_remaining = report.sessions_remaining_recommended * 2.0  # 2 hours/session
        
        # Generate recommendations
        self._generate_readiness_recommendations(report, critical_issues, moderate_issues, skill_scores)
        
        return report
    
    def identify_preparation_gaps(self, sessions: List[PrepSession],
                                target_skills: List[PrepSkillArea]) -> Dict[str, Any]:
        """Identify gaps in preparation coverage."""
        gaps_analysis = {
            'skill_coverage_gaps': [],
            'session_type_gaps': [],
            'frequency_issues': [],
            'depth_concerns': [],
            'recommendations': []
        }
        
        # Analyze skill coverage
        covered_skills = set()
        for session in sessions:
            for skill_area in session.skill_assessments.keys():
                covered_skills.add(skill_area)
        
        target_skills_set = set(target_skills)
        uncovered_skills = target_skills_set - covered_skills
        gaps_analysis['skill_coverage_gaps'] = [skill.value for skill in uncovered_skills]
        
        # Analyze session type coverage
        session_types_used = set(s.session_type for s in sessions)
        recommended_types = {
            PrepSessionType.DIRECT_EXAMINATION,
            PrepSessionType.CROSS_EXAMINATION,
            PrepSessionType.MOCK_TRIAL,
            PrepSessionType.FINAL_PREPARATION
        }
        missing_types = recommended_types - session_types_used
        gaps_analysis['session_type_gaps'] = [st.value for st in missing_types]
        
        # Analyze preparation frequency
        if sessions:
            sessions_by_week = defaultdict(int)
            for session in sessions:
                week_key = session.session_date.strftime("%Y-%W")
                sessions_by_week[week_key] += 1
            
            weeks_with_no_sessions = []
            avg_sessions_per_week = statistics.mean(sessions_by_week.values())
            
            if avg_sessions_per_week < 1:
                gaps_analysis['frequency_issues'].append("Insufficient session frequency")
        
        # Generate recommendations
        recommendations = []
        if gaps_analysis['skill_coverage_gaps']:
            recommendations.append(f"Address uncovered skills: {', '.join(gaps_analysis['skill_coverage_gaps'])}")
        
        if gaps_analysis['session_type_gaps']:
            recommendations.append(f"Add missing session types: {', '.join(gaps_analysis['session_type_gaps'])}")
        
        gaps_analysis['recommendations'] = recommendations
        
        return gaps_analysis
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend in values (positive = improving, negative = declining)."""
        if len(values) < 2:
            return 0.0
        
        # Simple linear regression slope
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x_squared_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x_squared_sum - x_sum * x_sum)
        return slope
    
    def _calculate_session_frequency(self, sessions: List[PrepSession]) -> float:
        """Calculate average sessions per week."""
        if len(sessions) < 2:
            return 0.0
        
        sessions_by_date = sorted(sessions, key=lambda s: s.session_date)
        first_date = sessions_by_date[0].session_date
        last_date = sessions_by_date[-1].session_date
        
        weeks = max(1, (last_date - first_date).days / 7)
        return len(sessions) / weeks
    
    def _calculate_efficiency_score(self, total_hours: float,
                                  skill_development: Dict[str, Dict[str, float]]) -> float:
        """Calculate preparation efficiency score."""
        if total_hours <= 0:
            return 0.0
        
        total_improvement = sum(dev['improvement'] for dev in skill_development.values()
                               if dev['improvement'] > 0)
        
        if total_improvement <= 0:
            return 0.0
        
        # Score based on improvement per hour
        improvement_per_hour = total_improvement / total_hours
        
        # Normalize to 0-1 scale (assuming 0.5 improvement points per hour is excellent)
        return min(1.0, improvement_per_hour / 0.5)
    
    def _generate_readiness_recommendations(self, report: WitnessReadinessReport,
                                         critical_issues: List[PrepIssue],
                                         moderate_issues: List[PrepIssue],
                                         skill_scores: Dict[PrepSkillArea, float]) -> None:
        """Generate specific readiness recommendations."""
        
        # Critical immediate actions
        if critical_issues:
            report.immediate_actions.append(f"Address {len(critical_issues)} critical preparation issues")
        
        if report.overall_readiness_score < 60:
            report.immediate_actions.append("Intensive preparation required - readiness below 60%")
        
        low_skill_areas = [skill.value for skill, score in skill_scores.items() if score < 5.0]
        if low_skill_areas:
            report.immediate_actions.append(f"Focus on low-scoring areas: {', '.join(low_skill_areas)}")
        
        # Continued focus areas
        moderate_skill_areas = [skill.value for skill, score in skill_scores.items() 
                               if 5.0 <= score < 7.0]
        if moderate_skill_areas:
            report.continued_focus_areas.extend(moderate_skill_areas)
        
        # Specialist referrals
        if any(issue.category == IssueCategory.ANXIETY_NERVOUSNESS for issue in critical_issues):
            report.specialist_referrals.append("Anxiety/performance coaching")
        
        if any(issue.category == IssueCategory.COMMUNICATION_SKILLS for issue in critical_issues):
            report.specialist_referrals.append("Communication skills training")
        
        # Trial participation recommendation
        if report.trial_ready:
            report.trial_participation_recommendation = "Witness is prepared for trial testimony"
        elif report.overall_readiness_level.value >= 3:
            report.trial_participation_recommendation = "Additional preparation recommended but witness can testify"
        else:
            report.trial_participation_recommendation = "Significant additional preparation required"
            report.backup_witness_recommended = True
        
        # Additional preparation critical assessment
        report.additional_preparation_critical = (
            len(critical_issues) > 0 or
            report.overall_readiness_score < 50 or
            not report.direct_exam_ready
        )

class WitnessPrepTracker:
    """Main witness preparation tracking system."""
    
    def __init__(self):
        self.prep_sessions: Dict[str, PrepSession] = {}
        self.skill_assessments: Dict[str, Dict[PrepSkillArea, SkillAssessment]] = {}  # witness_id -> skills
        self.prep_exercises: Dict[str, PrepExercise] = {}
        self.prep_issues: Dict[str, PrepIssue] = {}
        self.mock_examinations: Dict[str, MockExamination] = {}
        self.readiness_reports: Dict[str, WitnessReadinessReport] = {}
        self.analyzer = PrepAnalyzer()
        self.logger = logging.getLogger(__name__ + ".WitnessPrepTracker")
    
    def create_preparation_session(self, witness_id: str, session_type: PrepSessionType,
                                 lead_attorney: str, duration_minutes: int = 120) -> str:
        """Create new preparation session."""
        session_id = str(uuid.uuid4())
        
        session = PrepSession(
            session_id=session_id,
            witness_id=witness_id,
            session_type=session_type,
            session_date=datetime.now(),
            duration_minutes=duration_minutes,
            lead_attorney=lead_attorney,
            created_by=lead_attorney
        )
        
        self.prep_sessions[session_id] = session
        self.logger.info(f"Created preparation session: {session_id}")
        return session_id
    
    def initialize_skill_assessments(self, witness_id: str, 
                                   target_skills: List[PrepSkillArea]) -> None:
        """Initialize skill assessments for witness."""
        if witness_id not in self.skill_assessments:
            self.skill_assessments[witness_id] = {}
        
        for skill_area in target_skills:
            if skill_area not in self.skill_assessments[witness_id]:
                assessment = SkillAssessment(
                    skill_area=skill_area,
                    baseline_score=3.0,  # Default baseline
                    current_score=3.0,
                    target_score=8.0
                )
                self.skill_assessments[witness_id][skill_area] = assessment
        
        self.logger.info(f"Initialized {len(target_skills)} skill assessments for witness {witness_id}")
    
    def record_session_completion(self, session_id: str, session_outcome: SessionOutcome,
                                overall_score: float, skill_scores: Dict[PrepSkillArea, float],
                                attorney_notes: str = "", witness_feedback: str = "") -> bool:
        """Record completion of preparation session."""
        if session_id not in self.prep_sessions:
            return False
        
        session = self.prep_sessions[session_id]
        witness_id = session.witness_id
        
        # Update session details
        session.session_outcome = session_outcome
        session.overall_session_score = overall_score
        session.attorney_notes = attorney_notes
        session.witness_feedback = witness_feedback
        
        # Update skill assessments
        if witness_id in self.skill_assessments:
            for skill_area, score in skill_scores.items():
                if skill_area in self.skill_assessments[witness_id]:
                    assessment = self.skill_assessments[witness_id][skill_area]
                    assessment.current_score = score
                    assessment.score_history.append((datetime.now(), score))
                    assessment.sessions_focused += 1
                    
                    # Calculate improvement rate
                    if len(assessment.score_history) > 1:
                        first_score = assessment.score_history[0][1]
                        sessions_completed = len(assessment.score_history)
                        assessment.improvement_rate = (score - first_score) / sessions_completed
                
                session.skill_assessments[skill_area.value] = score
        
        # Determine readiness level change
        avg_score = statistics.mean(skill_scores.values()) if skill_scores else 0
        session.readiness_level_after = self._score_to_readiness_level(avg_score)
        
        self.logger.info(f"Recorded session completion: {session_id}")
        return True
    
    def create_mock_examination(self, session_id: str, exam_type: str,
                              examiner: str, duration_minutes: int) -> str:
        """Create mock examination record."""
        mock_exam_id = str(uuid.uuid4())
        
        mock_exam = MockExamination(
            mock_exam_id=mock_exam_id,
            exam_type=exam_type,
            duration_minutes=duration_minutes,
            examiner=examiner
        )
        
        self.mock_examinations[mock_exam_id] = mock_exam
        
        # Add to session if specified
        if session_id in self.prep_sessions:
            self.prep_sessions[session_id].mock_exams_conducted.append(mock_exam_id)
        
        self.logger.info(f"Created mock examination: {mock_exam_id}")
        return mock_exam_id
    
    def record_mock_exam_results(self, mock_exam_id: str, performance_scores: Dict[str, float],
                               questions_asked: int, questions_answered_well: int,
                               feedback: Dict[str, List[str]]) -> bool:
        """Record mock examination results."""
        if mock_exam_id not in self.mock_examinations:
            return False
        
        mock_exam = self.mock_examinations[mock_exam_id]
        
        # Update performance metrics
        mock_exam.questions_asked = questions_asked
        mock_exam.questions_answered_well = questions_answered_well
        mock_exam.questions_with_issues = questions_asked - questions_answered_well
        
        # Update performance scores
        mock_exam.overall_performance_score = performance_scores.get('overall', 0.0)
        mock_exam.confidence_level = performance_scores.get('confidence', 0.0)
        mock_exam.clarity_score = performance_scores.get('clarity', 0.0)
        mock_exam.responsiveness_score = performance_scores.get('responsiveness', 0.0)
        
        # Record feedback
        mock_exam.strong_areas = feedback.get('strengths', [])
        mock_exam.improvement_areas = feedback.get('improvements', [])
        mock_exam.follow_up_needed = feedback.get('follow_up', [])
        
        self.logger.info(f"Recorded mock exam results: {mock_exam_id}")
        return True
    
    def identify_preparation_issue(self, witness_id: str, category: IssueCategory,
                                 severity: int, title: str, description: str,
                                 identified_by: str) -> str:
        """Identify and record preparation issue."""
        issue_id = str(uuid.uuid4())
        
        issue = PrepIssue(
            issue_id=issue_id,
            category=category,
            severity=severity,
            title=title,
            description=description,
            identified_by=identified_by
        )
        
        self.prep_issues[issue_id] = issue
        self.logger.info(f"Identified preparation issue: {issue_id} - {title}")
        return issue_id
    
    def resolve_preparation_issue(self, issue_id: str, resolution_strategy: str,
                                resolution_notes: str = "") -> bool:
        """Mark preparation issue as resolved."""
        if issue_id not in self.prep_issues:
            return False
        
        issue = self.prep_issues[issue_id]
        issue.resolved = True
        issue.resolution_date = datetime.now()
        issue.resolution_strategy = resolution_strategy
        issue.resolution_notes = resolution_notes
        
        self.logger.info(f"Resolved preparation issue: {issue_id}")
        return True
    
    def generate_readiness_assessment(self, witness_id: str, assessor: str = "") -> str:
        """Generate comprehensive readiness assessment."""
        report_id = str(uuid.uuid4())
        
        # Get relevant data for witness
        witness_sessions = [s for s in self.prep_sessions.values() if s.witness_id == witness_id]
        witness_skills = self.skill_assessments.get(witness_id, {})
        witness_issues = [i for i in self.prep_issues.values() 
                         if witness_id in [s.witness_id for s in self.prep_sessions.values() 
                                         if i.issue_id in s.issues_identified]]
        
        # Generate assessment using analyzer
        report = self.analyzer.assess_witness_readiness(witness_id, witness_sessions, 
                                                       witness_skills, witness_issues)
        report.report_id = report_id
        report.assessor = assessor
        
        self.readiness_reports[report_id] = report
        self.logger.info(f"Generated readiness assessment: {report_id} for witness {witness_id}")
        return report_id
    
    def get_preparation_dashboard(self, witness_id: str) -> Dict[str, Any]:
        """Generate comprehensive preparation dashboard for witness."""
        witness_sessions = [s for s in self.prep_sessions.values() if s.witness_id == witness_id]
        witness_skills = self.skill_assessments.get(witness_id, {})
        witness_issues = [i for i in self.prep_issues.values() if not i.resolved]
        
        dashboard = {
            'witness_id': witness_id,
            'preparation_summary': {},
            'skill_progress': {},
            'recent_sessions': [],
            'current_issues': [],
            'readiness_indicators': {},
            'upcoming_tasks': [],
            'recommendations': []
        }
        
        # Preparation summary
        total_hours = sum(s.duration_minutes for s in witness_sessions) / 60.0
        recent_sessions = sorted(witness_sessions, key=lambda s: s.session_date, reverse=True)[:5]
        
        dashboard['preparation_summary'] = {
            'total_sessions': len(witness_sessions),
            'total_hours': total_hours,
            'sessions_this_week': len([s for s in witness_sessions 
                                     if (datetime.now() - s.session_date).days <= 7]),
            'last_session_date': recent_sessions[0].session_date if recent_sessions else None,
            'average_session_score': statistics.mean([s.overall_session_score for s in witness_sessions 
                                                    if s.overall_session_score > 0]) if witness_sessions else 0
        }
        
        # Skill progress
        skill_progress = {}
        for skill_area, assessment in witness_skills.items():
            skill_progress[skill_area.value] = {
                'current_score': assessment.current_score,
                'target_score': assessment.target_score,
                'progress_percentage': (assessment.current_score / assessment.target_score) * 100,
                'improvement_rate': assessment.improvement_rate,
                'sessions_focused': assessment.sessions_focused
            }
        
        dashboard['skill_progress'] = skill_progress
        
        # Recent sessions
        dashboard['recent_sessions'] = [
            {
                'session_id': s.session_id,
                'date': s.session_date,
                'type': s.session_type.value,
                'score': s.overall_session_score,
                'outcome': s.session_outcome.value
            }
            for s in recent_sessions
        ]
        
        # Current issues
        dashboard['current_issues'] = [
            {
                'issue_id': i.issue_id,
                'category': i.category.value,
                'severity': i.severity,
                'title': i.title,
                'days_open': (datetime.now() - i.identified_date).days
            }
            for i in witness_issues
        ]
        
        # Readiness indicators
        if witness_skills:
            avg_skill_score = statistics.mean(a.current_score for a in witness_skills.values())
            readiness_level = self._score_to_readiness_level(avg_skill_score)
            
            dashboard['readiness_indicators'] = {
                'overall_readiness_level': readiness_level.value,
                'trial_ready': readiness_level.value >= 4,
                'critical_issues_count': len([i for i in witness_issues if i.severity >= 4]),
                'skills_at_target': len([a for a in witness_skills.values() 
                                       if a.current_score >= a.target_score])
            }
        
        return dashboard
    
    def track_preparation_progress(self, witness_id: str) -> Dict[str, Any]:
        """Track detailed preparation progress over time."""
        witness_sessions = sorted([s for s in self.prep_sessions.values() if s.witness_id == witness_id],
                                key=lambda s: s.session_date)
        witness_skills = self.skill_assessments.get(witness_id, {})
        
        progress_tracking = {
            'session_timeline': [],
            'skill_progression': {},
            'preparation_milestones': [],
            'effectiveness_analysis': {},
            'trend_analysis': {}
        }
        
        # Session timeline
        for session in witness_sessions:
            progress_tracking['session_timeline'].append({
                'date': session.session_date,
                'session_type': session.session_type.value,
                'duration_hours': session.duration_minutes / 60.0,
                'score': session.overall_session_score,
                'outcome': session.session_outcome.value,
                'readiness_after': session.readiness_level_after.value
            })
        
        # Skill progression over time
        for skill_area, assessment in witness_skills.items():
            progression = []
            for timestamp, score in assessment.score_history:
                progression.append({
                    'date': timestamp,
                    'score': score
                })
            
            progress_tracking['skill_progression'][skill_area.value] = {
                'baseline_score': assessment.baseline_score,
                'current_score': assessment.current_score,
                'target_score': assessment.target_score,
                'score_history': progression,
                'improvement_rate': assessment.improvement_rate
            }
        
        # Analyze preparation effectiveness
        if witness_sessions:
            effectiveness_analysis = self.analyzer.analyze_preparation_effectiveness(
                witness_sessions, witness_skills
            )
            progress_tracking['effectiveness_analysis'] = effectiveness_analysis
        
        return progress_tracking
    
    def search_preparation_history(self, witness_id: str, query: str) -> Dict[str, List[Any]]:
        """Search preparation history for specific content."""
        results = {
            'sessions': [],
            'issues': [],
            'mock_exams': [],
            'assessments': []
        }
        
        query_lower = query.lower()
        
        # Search sessions
        witness_sessions = [s for s in self.prep_sessions.values() if s.witness_id == witness_id]
        for session in witness_sessions:
            searchable_text = (
                f"{session.attorney_notes} {session.witness_feedback} " +
                f"{' '.join(session.objectives_met)} {' '.join(session.challenges_encountered)}"
            ).lower()
            
            if query_lower in searchable_text:
                results['sessions'].append({
                    'session_id': session.session_id,
                    'date': session.session_date,
                    'type': session.session_type.value,
                    'score': session.overall_session_score,
                    'relevant_content': self._extract_relevant_content(searchable_text, query_lower)
                })
        
        # Search issues
        for issue in self.prep_issues.values():
            searchable_text = f"{issue.title} {issue.description} {issue.resolution_notes}".lower()
            if query_lower in searchable_text:
                results['issues'].append({
                    'issue_id': issue.issue_id,
                    'title': issue.title,
                    'category': issue.category.value,
                    'severity': issue.severity,
                    'resolved': issue.resolved
                })
        
        return results
    
    def _score_to_readiness_level(self, score: float) -> ReadinessLevel:
        """Convert numeric score to readiness level."""
        if score >= 8.5:
            return ReadinessLevel.TRIAL_READY
        elif score >= 7.0:
            return ReadinessLevel.WELL_PREPARED
        elif score >= 5.5:
            return ReadinessLevel.MODERATELY_READY
        elif score >= 3.5:
            return ReadinessLevel.BASIC_READY
        else:
            return ReadinessLevel.NOT_READY
    
    def _extract_relevant_content(self, text: str, query: str) -> str:
        """Extract relevant content snippet around query match."""
        index = text.find(query)
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