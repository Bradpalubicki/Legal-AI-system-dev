"""
Witness Management System

Comprehensive witness management system for trial preparation including
witness profiling, preparation sessions, testimony analysis, and 
coordination with evidence and case strategy.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class WitnessType(Enum):
    """Types of witnesses in legal proceedings."""
    FACT_WITNESS = "fact_witness"
    EXPERT_WITNESS = "expert_witness"
    CHARACTER_WITNESS = "character_witness"
    EYEWITNESS = "eyewitness"
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    POLICE_OFFICER = "police_officer"
    MEDICAL_PROFESSIONAL = "medical_professional"
    TECHNICAL_EXPERT = "technical_expert"
    INVESTIGATOR = "investigator"
    CORPORATE_REPRESENTATIVE = "corporate_representative"
    GOVERNMENT_OFFICIAL = "government_official"

class WitnessStatus(Enum):
    """Current status of witness in case preparation."""
    IDENTIFIED = "identified"
    CONTACTED = "contacted"
    COOPERATIVE = "cooperative"
    HOSTILE = "hostile"
    SUBPOENAED = "subpoenaed"
    PREPARED = "prepared"
    DEPOSED = "deposed"
    UNAVAILABLE = "unavailable"
    WITHDRAWN = "withdrawn"

class TestimonyType(Enum):
    """Type of testimony expected from witness."""
    DIRECT_EXAMINATION = "direct_examination"
    CROSS_EXAMINATION = "cross_examination"
    REDIRECT = "redirect"
    RECROSS = "recross"
    DEPOSITION = "deposition"
    AFFIDAVIT = "affidavit"

class PreparationStatus(Enum):
    """Status of witness preparation sessions."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BASIC_COMPLETE = "basic_complete"
    ADVANCED_COMPLETE = "advanced_complete"
    TRIAL_READY = "trial_ready"
    NEEDS_REFRESH = "needs_refresh"

class CredibilityLevel(Enum):
    """Assessment of witness credibility."""
    EXCELLENT = 5
    GOOD = 4
    AVERAGE = 3
    QUESTIONABLE = 2
    POOR = 1

@dataclass
class PreparationSession:
    """Individual witness preparation session."""
    session_id: str
    date: datetime
    duration_minutes: int
    session_type: str
    topics_covered: List[str]
    strengths_identified: List[str]
    weaknesses_identified: List[str]
    areas_for_improvement: List[str]
    follow_up_needed: List[str]
    attorney_notes: str
    witness_feedback: Optional[str] = None
    materials_reviewed: List[str] = field(default_factory=list)
    mock_questions_answered: int = 0
    confidence_level: int = 3  # 1-5 scale
    preparation_score: float = 0.0

@dataclass
class TestimonyOutline:
    """Structured outline of expected witness testimony."""
    outline_id: str
    testimony_type: TestimonyType
    key_points: List[str]
    chronological_order: List[str]
    supporting_evidence: List[str]
    potential_objections: List[str]
    responses_to_objections: List[str]
    cross_exam_vulnerabilities: List[str]
    rehabilitation_strategies: List[str]
    time_estimate_minutes: int
    created_by: str
    last_updated: datetime

@dataclass
class WitnessProfile:
    """Comprehensive witness profile with all relevant information."""
    witness_id: str
    name: str
    witness_type: WitnessType
    status: WitnessStatus
    
    # Contact Information
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    preferred_contact_method: str = "phone"
    
    # Professional Information
    occupation: Optional[str] = None
    employer: Optional[str] = None
    credentials: List[str] = field(default_factory=list)
    relevant_experience: str = ""
    
    # Case Relationship
    relationship_to_case: str = ""
    knowledge_of_facts: str = ""
    expected_testimony_summary: str = ""
    favorable_points: List[str] = field(default_factory=list)
    damaging_points: List[str] = field(default_factory=list)
    
    # Assessment
    credibility_level: CredibilityLevel = CredibilityLevel.AVERAGE
    communication_skills: int = 3  # 1-5 scale
    appearance_presentation: int = 3  # 1-5 scale
    potential_bias: str = ""
    prior_testimony_experience: bool = False
    
    # Background Information
    criminal_history: Optional[str] = None
    civil_litigation_history: List[str] = field(default_factory=list)
    media_exposure: List[str] = field(default_factory=list)
    social_media_concerns: List[str] = field(default_factory=list)
    
    # Availability and Logistics
    availability_constraints: List[str] = field(default_factory=list)
    travel_required: bool = False
    special_accommodations: List[str] = field(default_factory=list)
    interpreter_needed: bool = False
    language: str = "English"
    
    # Preparation Tracking
    preparation_status: PreparationStatus = PreparationStatus.NOT_STARTED
    preparation_sessions: List[str] = field(default_factory=list)  # Session IDs
    last_contact_date: Optional[datetime] = None
    next_contact_scheduled: Optional[datetime] = None
    
    # Documentation
    documents_provided: List[str] = field(default_factory=list)
    documents_requested: List[str] = field(default_factory=list)
    related_evidence: List[str] = field(default_factory=list)
    
    # Strategic Notes
    strategic_value: int = 3  # 1-5 scale
    risks: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    backup_witnesses: List[str] = field(default_factory=list)
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    last_modified: datetime = field(default_factory=datetime.now)
    notes: List[str] = field(default_factory=list)

@dataclass
class WitnessPreparation:
    """Comprehensive witness preparation plan and tracking."""
    preparation_id: str
    witness_id: str
    case_id: str
    preparation_plan: List[str]
    sessions_completed: List[str]  # Session IDs
    current_phase: str
    target_completion_date: datetime
    estimated_hours_total: int
    hours_completed: int = 0
    preparation_materials: List[str] = field(default_factory=list)
    mock_examination_scripts: List[str] = field(default_factory=list)
    readiness_assessment: Dict[str, Any] = field(default_factory=dict)
    final_preparation_checklist: List[str] = field(default_factory=list)

class WitnessAnalyzer:
    """Analyzes witness profiles and testimony for strategic planning."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".WitnessAnalyzer")
    
    def analyze_witness_credibility(self, witness: WitnessProfile) -> Dict[str, Any]:
        """Comprehensive credibility analysis of witness."""
        analysis = {
            'overall_credibility_score': 0.0,
            'credibility_factors': {},
            'strengths': [],
            'weaknesses': [],
            'risk_factors': [],
            'enhancement_opportunities': [],
            'jury_perception_prediction': {}
        }
        
        # Calculate overall credibility score
        factors = []
        
        # Base credibility level
        factors.append(witness.credibility_level.value * 0.3)
        
        # Communication and presentation
        factors.append((witness.communication_skills / 5.0) * 0.2)
        factors.append((witness.appearance_presentation / 5.0) * 0.15)
        
        # Experience and credentials
        if witness.prior_testimony_experience:
            factors.append(0.1)
        if witness.credentials:
            factors.append(min(len(witness.credentials) * 0.02, 0.1))
        
        # Professional standing
        if witness.occupation:
            professional_credibility = {
                'doctor': 0.15,
                'engineer': 0.12,
                'police': 0.1,
                'teacher': 0.08,
                'lawyer': 0.12,
                'accountant': 0.1,
                'scientist': 0.15,
                'professor': 0.15
            }
            for profession, score in professional_credibility.items():
                if profession.lower() in witness.occupation.lower():
                    factors.append(score)
                    break
        
        # Negative factors
        if witness.criminal_history:
            factors.append(-0.2)
        if witness.civil_litigation_history:
            factors.append(-0.1)
        if witness.potential_bias:
            factors.append(-0.15)
        
        analysis['overall_credibility_score'] = max(0.0, min(1.0, sum(factors)))
        
        # Detailed factor analysis
        analysis['credibility_factors'] = {
            'inherent_credibility': witness.credibility_level.value,
            'communication_ability': witness.communication_skills,
            'professional_presentation': witness.appearance_presentation,
            'relevant_experience': len(witness.credentials),
            'testimony_experience': witness.prior_testimony_experience,
            'potential_bias_issues': bool(witness.potential_bias),
            'background_concerns': bool(witness.criminal_history)
        }
        
        # Identify strengths
        if witness.credibility_level.value >= 4:
            analysis['strengths'].append("High inherent credibility")
        if witness.communication_skills >= 4:
            analysis['strengths'].append("Excellent communication skills")
        if witness.appearance_presentation >= 4:
            analysis['strengths'].append("Professional presentation")
        if witness.credentials:
            analysis['strengths'].append(f"Strong credentials: {', '.join(witness.credentials[:3])}")
        if witness.prior_testimony_experience:
            analysis['strengths'].append("Experienced with testimony")
        
        # Identify weaknesses
        if witness.credibility_level.value <= 2:
            analysis['weaknesses'].append("Low inherent credibility")
        if witness.communication_skills <= 2:
            analysis['weaknesses'].append("Poor communication skills")
        if witness.potential_bias:
            analysis['weaknesses'].append(f"Potential bias: {witness.potential_bias}")
        if witness.criminal_history:
            analysis['weaknesses'].append("Criminal history may affect credibility")
        if not witness.prior_testimony_experience:
            analysis['weaknesses'].append("No prior testimony experience")
        
        # Risk factors
        if witness.social_media_concerns:
            analysis['risk_factors'].extend(witness.social_media_concerns)
        if witness.media_exposure:
            analysis['risk_factors'].append("Prior media exposure may complicate testimony")
        if witness.civil_litigation_history:
            analysis['risk_factors'].append("History of litigation involvement")
        
        # Enhancement opportunities
        if witness.communication_skills < 4:
            analysis['enhancement_opportunities'].append("Communication skills training")
        if witness.appearance_presentation < 4:
            analysis['enhancement_opportunities'].append("Presentation coaching")
        if not witness.prior_testimony_experience:
            analysis['enhancement_opportunities'].append("Mock testimony practice")
        
        # Jury perception prediction
        analysis['jury_perception_prediction'] = {
            'likely_positive_factors': analysis['strengths'][:3],
            'likely_negative_factors': analysis['weaknesses'][:3],
            'demographic_considerations': self._assess_demographic_factors(witness),
            'overall_likability_score': self._calculate_likability_score(witness)
        }
        
        return analysis
    
    def analyze_testimony_risks(self, witness: WitnessProfile, 
                              testimony_outline: TestimonyOutline) -> Dict[str, Any]:
        """Analyze potential risks in witness testimony."""
        risk_analysis = {
            'high_risk_areas': [],
            'medium_risk_areas': [],
            'low_risk_areas': [],
            'cross_examination_vulnerabilities': [],
            'mitigation_strategies': [],
            'preparation_priorities': []
        }
        
        # Analyze cross-examination vulnerabilities
        for vulnerability in testimony_outline.cross_exam_vulnerabilities:
            risk_level = self._assess_vulnerability_risk(vulnerability, witness)
            if risk_level >= 4:
                risk_analysis['high_risk_areas'].append(vulnerability)
            elif risk_level >= 2:
                risk_analysis['medium_risk_areas'].append(vulnerability)
            else:
                risk_analysis['low_risk_areas'].append(vulnerability)
        
        # Add witness-specific vulnerabilities
        if witness.potential_bias:
            risk_analysis['cross_examination_vulnerabilities'].append(
                f"Bias allegations: {witness.potential_bias}")
        
        if witness.criminal_history:
            risk_analysis['cross_examination_vulnerabilities'].append(
                f"Impeachment via criminal history: {witness.criminal_history}")
        
        if witness.civil_litigation_history:
            risk_analysis['cross_examination_vulnerabilities'].append(
                "Prior litigation involvement")
        
        # Generate mitigation strategies
        for high_risk in risk_analysis['high_risk_areas']:
            strategies = self._generate_mitigation_strategies(high_risk, witness)
            risk_analysis['mitigation_strategies'].extend(strategies)
        
        # Preparation priorities
        risk_analysis['preparation_priorities'] = [
            "Address high-risk cross-examination areas",
            "Practice responses to impeachment attempts",
            "Strengthen credibility through preparation",
            "Develop rehabilitation strategies"
        ]
        
        return risk_analysis
    
    def assess_witness_readiness(self, witness: WitnessProfile, 
                               sessions: List[PreparationSession]) -> Dict[str, Any]:
        """Assess witness readiness for testimony."""
        readiness = {
            'overall_readiness_score': 0.0,
            'preparation_completeness': 0.0,
            'confidence_level': 0.0,
            'knowledge_mastery': 0.0,
            'communication_readiness': 0.0,
            'areas_needing_work': [],
            'ready_for_trial': False,
            'recommendations': []
        }
        
        if not sessions:
            readiness['recommendations'].append("No preparation sessions completed")
            return readiness
        
        # Calculate preparation completeness
        total_prep_hours = sum(session.duration_minutes for session in sessions) / 60.0
        expected_hours = self._estimate_required_prep_hours(witness)
        readiness['preparation_completeness'] = min(1.0, total_prep_hours / expected_hours)
        
        # Average confidence level from sessions
        if sessions:
            avg_confidence = sum(session.confidence_level for session in sessions) / len(sessions)
            readiness['confidence_level'] = avg_confidence / 5.0
        
        # Knowledge mastery based on session scores
        if sessions:
            avg_score = sum(session.preparation_score for session in sessions) / len(sessions)
            readiness['knowledge_mastery'] = avg_score
        
        # Communication readiness
        readiness['communication_readiness'] = witness.communication_skills / 5.0
        
        # Overall readiness score
        readiness['overall_readiness_score'] = (
            readiness['preparation_completeness'] * 0.3 +
            readiness['confidence_level'] * 0.25 +
            readiness['knowledge_mastery'] * 0.25 +
            readiness['communication_readiness'] * 0.2
        )
        
        # Determine if ready for trial
        readiness['ready_for_trial'] = (
            readiness['overall_readiness_score'] >= 0.7 and
            readiness['confidence_level'] >= 0.6 and
            readiness['preparation_completeness'] >= 0.8
        )
        
        # Areas needing work
        if readiness['preparation_completeness'] < 0.8:
            readiness['areas_needing_work'].append("Additional preparation time needed")
        if readiness['confidence_level'] < 0.6:
            readiness['areas_needing_work'].append("Confidence building required")
        if readiness['knowledge_mastery'] < 0.7:
            readiness['areas_needing_work'].append("Better mastery of key facts needed")
        if readiness['communication_readiness'] < 0.6:
            readiness['areas_needing_work'].append("Communication skills improvement needed")
        
        # Generate recommendations
        if not readiness['ready_for_trial']:
            most_recent_session = max(sessions, key=lambda s: s.date)
            if most_recent_session.follow_up_needed:
                readiness['recommendations'].extend(most_recent_session.follow_up_needed)
        
        return readiness
    
    def _assess_demographic_factors(self, witness: WitnessProfile) -> List[str]:
        """Assess how demographic factors might affect jury perception."""
        factors = []
        
        if witness.occupation:
            if any(term in witness.occupation.lower() for term in ['doctor', 'nurse', 'teacher']):
                factors.append("Professional occupation likely viewed favorably")
            elif any(term in witness.occupation.lower() for term in ['police', 'security']):
                factors.append("Authority figure - mixed jury reactions possible")
        
        if witness.credentials:
            factors.append("Educational credentials enhance credibility")
        
        return factors
    
    def _calculate_likability_score(self, witness: WitnessProfile) -> float:
        """Calculate predicted likability score for jury."""
        score_factors = []
        
        # Communication skills impact likability
        score_factors.append(witness.communication_skills / 5.0 * 0.4)
        
        # Appearance/presentation
        score_factors.append(witness.appearance_presentation / 5.0 * 0.3)
        
        # Occupation likability
        likable_occupations = ['teacher', 'nurse', 'firefighter', 'social worker']
        if witness.occupation and any(occ in witness.occupation.lower() for occ in likable_occupations):
            score_factors.append(0.2)
        
        # Bias concerns reduce likability
        if witness.potential_bias:
            score_factors.append(-0.1)
        
        return max(0.0, min(1.0, sum(score_factors)))
    
    def _assess_vulnerability_risk(self, vulnerability: str, witness: WitnessProfile) -> int:
        """Assess risk level of cross-examination vulnerability (1-5 scale)."""
        high_risk_keywords = ['bias', 'criminal', 'inconsistent', 'financial interest']
        medium_risk_keywords = ['memory', 'prior statement', 'relationship']
        
        vulnerability_lower = vulnerability.lower()
        
        if any(keyword in vulnerability_lower for keyword in high_risk_keywords):
            return 5
        elif any(keyword in vulnerability_lower for keyword in medium_risk_keywords):
            return 3
        else:
            return 2
    
    def _generate_mitigation_strategies(self, risk_area: str, witness: WitnessProfile) -> List[str]:
        """Generate mitigation strategies for specific risk areas."""
        strategies = []
        risk_lower = risk_area.lower()
        
        if 'bias' in risk_lower:
            strategies.extend([
                "Address bias allegations directly in preparation",
                "Develop honest responses about relationships/interests",
                "Practice maintaining objectivity in testimony"
            ])
        
        if 'criminal' in risk_lower:
            strategies.extend([
                "Prepare honest, brief responses about criminal history",
                "Focus on rehabilitation and changed circumstances",
                "Practice not appearing defensive"
            ])
        
        if 'memory' in risk_lower:
            strategies.extend([
                "Review documents thoroughly before testimony",
                "Practice saying 'I don't recall' when appropriate",
                "Use contemporaneous documents to refresh memory"
            ])
        
        return strategies
    
    def _estimate_required_prep_hours(self, witness: WitnessProfile) -> float:
        """Estimate required preparation hours based on witness complexity."""
        base_hours = 2.0
        
        # Adjust based on witness type
        if witness.witness_type == WitnessType.EXPERT_WITNESS:
            base_hours += 4.0
        elif witness.witness_type == WitnessType.FACT_WITNESS:
            base_hours += 1.0
        
        # Adjust based on complexity factors
        if witness.risks:
            base_hours += len(witness.risks) * 0.5
        
        if not witness.prior_testimony_experience:
            base_hours += 2.0
        
        if witness.communication_skills <= 2:
            base_hours += 3.0
        
        return base_hours

class PreparationManager:
    """Manages witness preparation sessions and progress tracking."""
    
    def __init__(self):
        self.preparation_sessions: Dict[str, PreparationSession] = {}
        self.logger = logging.getLogger(__name__ + ".PreparationManager")
    
    def create_preparation_plan(self, witness: WitnessProfile, 
                              case_complexity: str = "medium") -> WitnessPreparation:
        """Create comprehensive preparation plan for witness."""
        preparation_id = str(uuid.uuid4())
        
        # Determine preparation phases based on witness type and complexity
        phases = self._generate_preparation_phases(witness, case_complexity)
        
        # Estimate total hours needed
        estimated_hours = self._estimate_preparation_hours(witness, case_complexity)
        
        # Set target completion date (typically 2-4 weeks before trial)
        target_date = datetime.now() + timedelta(days=21)
        
        preparation_plan = WitnessPreparation(
            preparation_id=preparation_id,
            witness_id=witness.witness_id,
            case_id="",  # Will be set by calling code
            preparation_plan=phases,
            sessions_completed=[],
            current_phase=phases[0] if phases else "initial",
            target_completion_date=target_date,
            estimated_hours_total=estimated_hours,
            preparation_materials=self._generate_material_list(witness),
            final_preparation_checklist=self._generate_final_checklist(witness)
        )
        
        return preparation_plan
    
    def conduct_preparation_session(self, witness_id: str, session_type: str,
                                  duration_minutes: int, topics: List[str],
                                  attorney_notes: str) -> str:
        """Record a preparation session."""
        session_id = str(uuid.uuid4())
        
        session = PreparationSession(
            session_id=session_id,
            date=datetime.now(),
            duration_minutes=duration_minutes,
            session_type=session_type,
            topics_covered=topics,
            strengths_identified=[],
            weaknesses_identified=[],
            areas_for_improvement=[],
            follow_up_needed=[],
            attorney_notes=attorney_notes
        )
        
        self.preparation_sessions[session_id] = session
        self.logger.info(f"Created preparation session {session_id} for witness {witness_id}")
        return session_id
    
    def update_session_assessment(self, session_id: str, 
                                strengths: List[str], weaknesses: List[str],
                                improvements: List[str], follow_ups: List[str],
                                confidence_level: int, preparation_score: float) -> bool:
        """Update session with assessment details."""
        if session_id not in self.preparation_sessions:
            return False
        
        session = self.preparation_sessions[session_id]
        session.strengths_identified = strengths
        session.weaknesses_identified = weaknesses
        session.areas_for_improvement = improvements
        session.follow_up_needed = follow_ups
        session.confidence_level = confidence_level
        session.preparation_score = preparation_score
        
        return True
    
    def generate_mock_questions(self, witness: WitnessProfile, 
                              testimony_outline: TestimonyOutline,
                              question_type: str = "direct") -> List[Dict[str, str]]:
        """Generate mock examination questions for practice."""
        questions = []
        
        if question_type == "direct":
            questions.extend(self._generate_direct_questions(witness, testimony_outline))
        elif question_type == "cross":
            questions.extend(self._generate_cross_questions(witness, testimony_outline))
        else:
            questions.extend(self._generate_direct_questions(witness, testimony_outline))
            questions.extend(self._generate_cross_questions(witness, testimony_outline))
        
        return questions
    
    def _generate_preparation_phases(self, witness: WitnessProfile, complexity: str) -> List[str]:
        """Generate preparation phases based on witness and case complexity."""
        phases = [
            "Initial Interview and Assessment",
            "Document Review and Familiarization",
            "Direct Examination Preparation"
        ]
        
        if witness.witness_type == WitnessType.EXPERT_WITNESS:
            phases.extend([
                "Expert Opinion Formulation",
                "Technical Presentation Practice",
                "Cross-Examination Preparation - Technical Challenges"
            ])
        
        phases.extend([
            "Cross-Examination Preparation",
            "Mock Trial Practice",
            "Final Review and Confidence Building"
        ])
        
        if complexity in ["high", "complex"]:
            phases.append("Advanced Cross-Examination Scenarios")
        
        return phases
    
    def _estimate_preparation_hours(self, witness: WitnessProfile, complexity: str) -> int:
        """Estimate total preparation hours needed."""
        base_hours = 4
        
        # Witness type adjustments
        type_hours = {
            WitnessType.EXPERT_WITNESS: 8,
            WitnessType.FACT_WITNESS: 3,
            WitnessType.EYEWITNESS: 4,
            WitnessType.CHARACTER_WITNESS: 2
        }
        base_hours = type_hours.get(witness.witness_type, 4)
        
        # Complexity adjustments
        if complexity == "high":
            base_hours += 6
        elif complexity == "medium":
            base_hours += 3
        
        # Experience adjustments
        if not witness.prior_testimony_experience:
            base_hours += 4
        
        # Communication skill adjustments
        if witness.communication_skills <= 2:
            base_hours += 6
        
        # Risk factor adjustments
        base_hours += len(witness.risks) * 2
        
        return max(6, base_hours)
    
    def _generate_material_list(self, witness: WitnessProfile) -> List[str]:
        """Generate list of preparation materials needed."""
        materials = [
            "Case timeline and key facts summary",
            "Relevant documents witness will testify about",
            "Witness's prior statements/depositions",
            "Mock examination questions and answers"
        ]
        
        if witness.witness_type == WitnessType.EXPERT_WITNESS:
            materials.extend([
                "Expert report and supporting data",
                "Technical references and standards",
                "Visual aids and demonstratives",
                "Curriculum vitae and qualifications"
            ])
        
        materials.extend([
            "Courtroom procedures guide",
            "Tips for effective testimony handout"
        ])
        
        return materials
    
    def _generate_final_checklist(self, witness: WitnessProfile) -> List[str]:
        """Generate final preparation checklist."""
        checklist = [
            "Review key facts one final time",
            "Practice answering core questions",
            "Confirm understanding of courtroom procedures",
            "Address any last-minute concerns",
            "Review what to wear and logistics"
        ]
        
        if witness.witness_type == WitnessType.EXPERT_WITNESS:
            checklist.extend([
                "Final review of expert opinions",
                "Check all visual aids and equipment",
                "Confirm qualifications are current"
            ])
        
        return checklist
    
    def _generate_direct_questions(self, witness: WitnessProfile,
                                 testimony_outline: TestimonyOutline) -> List[Dict[str, str]]:
        """Generate direct examination questions."""
        questions = []
        
        # Background questions
        questions.extend([
            {"question": f"Please state your full name for the record.", "type": "background"},
            {"question": f"What is your occupation?", "type": "background"},
            {"question": f"How long have you been in this field?", "type": "background"}
        ])
        
        # Qualification questions for experts
        if witness.witness_type == WitnessType.EXPERT_WITNESS:
            questions.extend([
                {"question": "Please describe your educational background.", "type": "qualification"},
                {"question": "What relevant certifications do you hold?", "type": "qualification"},
                {"question": "Have you previously testified as an expert?", "type": "qualification"}
            ])
        
        # Substantive questions based on testimony outline
        for point in testimony_outline.key_points:
            questions.append({
                "question": f"Can you tell us about {point.lower()}?",
                "type": "substantive"
            })
        
        return questions
    
    def _generate_cross_questions(self, witness: WitnessProfile,
                                testimony_outline: TestimonyOutline) -> List[Dict[str, str]]:
        """Generate cross-examination questions for practice."""
        questions = []
        
        # Challenge credibility
        if witness.potential_bias:
            questions.append({
                "question": f"Isn't it true that you have a {witness.potential_bias}?",
                "type": "credibility"
            })
        
        # Challenge memory/perception
        questions.extend([
            {"question": "How much time has passed since these events occurred?", "type": "memory"},
            {"question": "Isn't it possible your memory could be mistaken?", "type": "memory"}
        ])
        
        # Challenge qualifications (for experts)
        if witness.witness_type == WitnessType.EXPERT_WITNESS:
            questions.extend([
                {"question": "You're being paid for your testimony, correct?", "type": "bias"},
                {"question": "Have you ever had an opinion excluded by a court?", "type": "qualification"}
            ])
        
        # Challenge based on vulnerabilities
        for vulnerability in testimony_outline.cross_exam_vulnerabilities:
            questions.append({
                "question": f"Regarding {vulnerability.lower()}, isn't it true that...?",
                "type": "vulnerability"
            })
        
        return questions

class WitnessManager:
    """Main witness management system coordinating all components."""
    
    def __init__(self):
        self.witnesses: Dict[str, WitnessProfile] = {}
        self.preparations: Dict[str, WitnessPreparation] = {}
        self.testimony_outlines: Dict[str, TestimonyOutline] = {}
        self.analyzer = WitnessAnalyzer()
        self.preparation_manager = PreparationManager()
        self.logger = logging.getLogger(__name__ + ".WitnessManager")
    
    def add_witness(self, witness: WitnessProfile) -> str:
        """Add new witness to the system."""
        if not witness.witness_id:
            witness.witness_id = str(uuid.uuid4())
        
        self.witnesses[witness.witness_id] = witness
        self.logger.info(f"Added witness: {witness.witness_id} - {witness.name}")
        return witness.witness_id
    
    def create_testimony_outline(self, witness_id: str, testimony_type: TestimonyType,
                               key_points: List[str], supporting_evidence: List[str]) -> str:
        """Create testimony outline for witness."""
        if witness_id not in self.witnesses:
            raise ValueError(f"Witness {witness_id} not found")
        
        outline_id = str(uuid.uuid4())
        outline = TestimonyOutline(
            outline_id=outline_id,
            testimony_type=testimony_type,
            key_points=key_points,
            chronological_order=key_points.copy(),  # Default to input order
            supporting_evidence=supporting_evidence,
            potential_objections=[],
            responses_to_objections=[],
            cross_exam_vulnerabilities=[],
            rehabilitation_strategies=[],
            time_estimate_minutes=len(key_points) * 3,  # Rough estimate
            created_by="System",
            last_updated=datetime.now()
        )
        
        self.testimony_outlines[outline_id] = outline
        return outline_id
    
    def start_witness_preparation(self, witness_id: str, case_id: str,
                                case_complexity: str = "medium") -> str:
        """Start comprehensive witness preparation process."""
        if witness_id not in self.witnesses:
            raise ValueError(f"Witness {witness_id} not found")
        
        witness = self.witnesses[witness_id]
        preparation = self.preparation_manager.create_preparation_plan(witness, case_complexity)
        preparation.case_id = case_id
        
        self.preparations[preparation.preparation_id] = preparation
        
        # Update witness status
        witness.preparation_status = PreparationStatus.IN_PROGRESS
        witness.last_modified = datetime.now()
        
        self.logger.info(f"Started preparation for witness {witness_id}")
        return preparation.preparation_id
    
    def assess_witness_panel(self, witness_ids: List[str]) -> Dict[str, Any]:
        """Assess overall witness panel strength and strategy."""
        panel_assessment = {
            'total_witnesses': len(witness_ids),
            'witness_breakdown': {},
            'overall_strength': 0.0,
            'credibility_distribution': {},
            'risk_assessment': {},
            'strategic_recommendations': [],
            'preparation_status_summary': {}
        }
        
        witnesses = [self.witnesses[wid] for wid in witness_ids if wid in self.witnesses]
        
        if not witnesses:
            return panel_assessment
        
        # Witness type breakdown
        type_counts = {}
        credibility_scores = []
        
        for witness in witnesses:
            witness_type = witness.witness_type.value
            type_counts[witness_type] = type_counts.get(witness_type, 0) + 1
            
            # Analyze individual witness
            credibility_analysis = self.analyzer.analyze_witness_credibility(witness)
            credibility_scores.append(credibility_analysis['overall_credibility_score'])
        
        panel_assessment['witness_breakdown'] = type_counts
        panel_assessment['overall_strength'] = sum(credibility_scores) / len(credibility_scores)
        
        # Credibility distribution
        high_credibility = len([s for s in credibility_scores if s >= 0.8])
        medium_credibility = len([s for s in credibility_scores if 0.5 <= s < 0.8])
        low_credibility = len([s for s in credibility_scores if s < 0.5])
        
        panel_assessment['credibility_distribution'] = {
            'high': high_credibility,
            'medium': medium_credibility,
            'low': low_credibility
        }
        
        # Risk assessment
        high_risk_witnesses = []
        for witness in witnesses:
            if witness.risks or witness.criminal_history or witness.potential_bias:
                high_risk_witnesses.append(witness.witness_id)
        
        panel_assessment['risk_assessment'] = {
            'high_risk_count': len(high_risk_witnesses),
            'high_risk_witnesses': high_risk_witnesses,
            'risk_mitigation_needed': len(high_risk_witnesses) > 0
        }
        
        # Preparation status
        prep_status_counts = {}
        for witness in witnesses:
            status = witness.preparation_status.value
            prep_status_counts[status] = prep_status_counts.get(status, 0) + 1
        
        panel_assessment['preparation_status_summary'] = prep_status_counts
        
        # Strategic recommendations
        recommendations = []
        
        if panel_assessment['overall_strength'] < 0.6:
            recommendations.append("Consider strengthening witness panel with additional credible witnesses")
        
        if low_credibility > high_credibility:
            recommendations.append("Focus preparation efforts on improving low-credibility witnesses")
        
        if len(high_risk_witnesses) > len(witnesses) * 0.3:
            recommendations.append("Significant risk mitigation needed for witness panel")
        
        if prep_status_counts.get('not_started', 0) > 0:
            recommendations.append("Begin preparation for unprepared witnesses immediately")
        
        panel_assessment['strategic_recommendations'] = recommendations
        
        return panel_assessment
    
    def generate_witness_report(self, witness_id: str) -> Dict[str, Any]:
        """Generate comprehensive witness report."""
        if witness_id not in self.witnesses:
            raise ValueError(f"Witness {witness_id} not found")
        
        witness = self.witnesses[witness_id]
        
        report = {
            'witness_profile': witness,
            'credibility_analysis': {},
            'preparation_status': {},
            'readiness_assessment': {},
            'strategic_value': {},
            'recommendations': []
        }
        
        # Credibility analysis
        report['credibility_analysis'] = self.analyzer.analyze_witness_credibility(witness)
        
        # Preparation status
        preparation = None
        for prep in self.preparations.values():
            if prep.witness_id == witness_id:
                preparation = prep
                break
        
        if preparation:
            sessions = [self.preparation_manager.preparation_sessions[sid] 
                       for sid in preparation.sessions_completed 
                       if sid in self.preparation_manager.preparation_sessions]
            
            report['readiness_assessment'] = self.analyzer.assess_witness_readiness(witness, sessions)
            report['preparation_status'] = {
                'plan_created': True,
                'sessions_completed': len(sessions),
                'hours_completed': preparation.hours_completed,
                'estimated_hours_total': preparation.estimated_hours_total,
                'completion_percentage': (preparation.hours_completed / preparation.estimated_hours_total) * 100
            }
        else:
            report['preparation_status'] = {'plan_created': False}
            report['readiness_assessment'] = {'ready_for_trial': False}
        
        # Strategic value assessment
        report['strategic_value'] = {
            'importance_score': witness.strategic_value,
            'testimony_impact': "High" if witness.relevance_score.value >= 4 else "Medium" if witness.relevance_score.value >= 3 else "Low",
            'risk_factors': witness.risks,
            'backup_witnesses_available': len(witness.backup_witnesses) > 0
        }
        
        # Recommendations
        recommendations = []
        
        if not preparation:
            recommendations.append("Create formal preparation plan")
        elif not report['readiness_assessment'].get('ready_for_trial', False):
            recommendations.append("Additional preparation needed before trial")
        
        if witness.credibility_level.value <= 2:
            recommendations.append("Consider credibility enhancement strategies")
        
        if witness.risks:
            recommendations.append("Implement risk mitigation strategies")
        
        report['recommendations'] = recommendations
        
        return report
    
    def search_witnesses(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[WitnessProfile]:
        """Search witnesses by various criteria."""
        results = []
        query_lower = query.lower()
        
        for witness in self.witnesses.values():
            # Text search in name, occupation, and case relevance
            searchable_text = (
                f"{witness.name} {witness.occupation or ''} " +
                f"{witness.relationship_to_case} {witness.knowledge_of_facts} " +
                f"{' '.join(witness.notes)}"
            ).lower()
            
            if query_lower in searchable_text:
                # Apply filters if provided
                if filters:
                    if 'witness_type' in filters and witness.witness_type != filters['witness_type']:
                        continue
                    if 'status' in filters and witness.status != filters['status']:
                        continue
                    if 'credibility_min' in filters and witness.credibility_level.value < filters['credibility_min']:
                        continue
                    if 'preparation_status' in filters and witness.preparation_status != filters['preparation_status']:
                        continue
                
                results.append(witness)
        
        # Sort by strategic value and credibility
        return sorted(results, key=lambda x: (x.strategic_value, x.credibility_level.value), reverse=True)