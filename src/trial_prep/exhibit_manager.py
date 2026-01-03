"""
Exhibit Management System

Comprehensive exhibit management system for trial preparation including
exhibit numbering, organization, authentication tracking, courtroom logistics,
technology integration, and real-time exhibit status during trial.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
import logging
from pathlib import Path
import hashlib
from collections import defaultdict

logger = logging.getLogger(__name__)

class ExhibitType(Enum):
    """Types of trial exhibits."""
    DOCUMENT = "document"
    PHOTOGRAPH = "photograph"
    VIDEO = "video"
    AUDIO = "audio"
    DEMONSTRATIVE = "demonstrative"
    CHART_GRAPH = "chart_graph"
    MAP_DIAGRAM = "map_diagram"
    PHYSICAL_OBJECT = "physical_object"
    DIGITAL_EVIDENCE = "digital_evidence"
    ANIMATION = "animation"
    PRESENTATION = "presentation"
    MODEL = "model"
    X_RAY = "x_ray"
    MEDICAL_IMAGE = "medical_image"
    TIMELINE = "timeline"

class ExhibitStatus(Enum):
    """Status of exhibit in trial process."""
    IDENTIFIED = "identified"
    PREPARED = "prepared"
    PRE_MARKED = "pre_marked"
    AUTHENTICATED = "authenticated"
    ADMITTED = "admitted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    STIPULATED = "stipulated"
    RESERVED = "reserved"
    OBJECTED = "objected"

class ExhibitParty(Enum):
    """Which party is offering the exhibit."""
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    COURT = "court"
    JOINT = "joint"

class TechnologyRequirement(Enum):
    """Technology needed for exhibit presentation."""
    NONE = "none"
    PROJECTOR = "projector"
    AUDIO_SYSTEM = "audio_system"
    VIDEO_PLAYER = "video_player"
    COMPUTER = "computer"
    DOCUMENT_CAMERA = "document_camera"
    ELMO = "elmo"
    SMART_BOARD = "smart_board"
    EVIDENCE_CAM = "evidence_cam"
    WIRELESS_DISPLAY = "wireless_display"

class ObjectionType(Enum):
    """Types of objections to exhibits."""
    RELEVANCE = "relevance"
    AUTHENTICATION = "authentication"
    HEARSAY = "hearsay"
    BEST_EVIDENCE = "best_evidence"
    PREJUDICIAL = "prejudicial"
    FOUNDATION = "foundation"
    PRIVILEGE = "privilege"
    CUMULATIVE = "cumulative"
    MISLEADING = "misleading"
    SPECULATION = "speculation"

@dataclass
class ExhibitAuthentication:
    """Authentication requirements and status for exhibit."""
    authentication_id: str
    required_witness: Optional[str] = None
    authenticating_witness: Optional[str] = None
    authentication_method: str = ""
    foundation_elements: List[str] = field(default_factory=list)
    foundation_complete: bool = False
    authentication_script: str = ""
    potential_challenges: List[str] = field(default_factory=list)
    backup_authentication: List[str] = field(default_factory=list)
    
    # Chain of custody for physical evidence
    custody_verified: bool = False
    custody_gaps: List[str] = field(default_factory=list)
    
    # Technical authentication for digital evidence
    hash_verified: bool = False
    metadata_preserved: bool = False
    original_available: bool = True
    
    created_date: datetime = field(default_factory=datetime.now)

@dataclass
class ExhibitObjection:
    """Objection to exhibit admission."""
    objection_id: str
    objection_type: ObjectionType
    objecting_party: str
    objection_details: str
    anticipated: bool = False
    
    # Response preparation
    response_strategy: str = ""
    supporting_authority: List[str] = field(default_factory=list)
    alternative_approach: str = ""
    
    # Status tracking
    ruled_on: bool = False
    court_ruling: Optional[str] = None
    ruling_reason: str = ""
    
    created_date: datetime = field(default_factory=datetime.now)

@dataclass
class ExhibitPresentation:
    """Presentation details and logistics for exhibit."""
    presentation_id: str
    technology_needed: List[TechnologyRequirement] = field(default_factory=list)
    setup_time_minutes: int = 0
    presentation_duration_minutes: int = 0
    
    # File and format information
    file_formats: List[str] = field(default_factory=list)
    backup_formats: List[str] = field(default_factory=list)
    file_sizes: Dict[str, int] = field(default_factory=dict)
    resolution_requirements: Dict[str, str] = field(default_factory=dict)
    
    # Courtroom logistics
    positioning_notes: str = ""
    lighting_requirements: str = ""
    audio_requirements: str = ""
    jury_visibility_confirmed: bool = False
    
    # Practice and testing
    tested_in_courtroom: bool = False
    test_date: Optional[datetime] = None
    technical_issues_identified: List[str] = field(default_factory=list)
    backup_plan: str = ""
    
    # Presentation flow
    introduction_script: str = ""
    key_highlighting_points: List[str] = field(default_factory=list)
    conclusion_script: str = ""

@dataclass
class Exhibit:
    """Comprehensive exhibit with all management details."""
    exhibit_id: str
    exhibit_number: str
    party: ExhibitParty
    exhibit_type: ExhibitType
    title: str
    description: str
    
    # Source information
    source_evidence_id: Optional[str] = None
    source_document_path: Optional[str] = None
    original_filename: Optional[str] = None
    
    # Physical properties
    physical_dimensions: Optional[str] = None
    weight: Optional[str] = None
    storage_location: str = ""
    storage_requirements: List[str] = field(default_factory=list)
    
    # Trial logistics
    status: ExhibitStatus = ExhibitStatus.IDENTIFIED
    order_of_presentation: Optional[int] = None
    witness_presenting: Optional[str] = None
    trial_day_planned: Optional[int] = None
    
    # Authentication and foundation
    authentication: Optional[ExhibitAuthentication] = None
    foundation_witness: Optional[str] = None
    foundation_questions: List[str] = field(default_factory=list)
    
    # Legal challenges
    objections: List[str] = field(default_factory=list)  # ObjectionIDs
    anticipated_objections: List[str] = field(default_factory=list)
    response_prepared: bool = False
    
    # Presentation details
    presentation: Optional[ExhibitPresentation] = None
    demonstrative_aids: List[str] = field(default_factory=list)
    
    # Relationships
    related_exhibits: List[str] = field(default_factory=list)  # Exhibit IDs
    supporting_exhibits: List[str] = field(default_factory=list)
    contradicted_by: List[str] = field(default_factory=list)
    
    # Quality and preparation
    copies_made: int = 0
    copies_locations: List[str] = field(default_factory=list)
    blown_up_versions: List[str] = field(default_factory=list)
    highlighting_applied: bool = False
    
    # Trial tracking
    marked_for_identification: bool = False
    identification_date: Optional[datetime] = None
    admission_attempted: bool = False
    admission_date: Optional[datetime] = None
    court_reporter_notation: str = ""
    
    # Strategic importance
    importance_level: int = 3  # 1-5 scale
    strategic_notes: str = ""
    impact_assessment: str = ""
    jury_appeal_factor: int = 3  # 1-5 scale
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    last_modified: datetime = field(default_factory=datetime.now)
    modification_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Notes and comments
    attorney_notes: str = ""
    paralegal_notes: str = ""
    trial_notes: str = ""
    post_trial_notes: str = ""

@dataclass
class ExhibitList:
    """Complete exhibit list for trial."""
    list_id: str
    case_id: str
    party: ExhibitParty
    trial_date: Optional[date] = None
    
    # Exhibit organization
    exhibits: List[str] = field(default_factory=list)  # Exhibit IDs
    exhibit_categories: Dict[str, List[str]] = field(default_factory=dict)
    presentation_order: List[str] = field(default_factory=list)
    
    # List metadata
    total_exhibits: int = 0
    exhibits_by_type: Dict[str, int] = field(default_factory=dict)
    exhibits_by_status: Dict[str, int] = field(default_factory=dict)
    
    # Preparation status
    list_complete: bool = False
    list_filed: bool = False
    filing_date: Optional[datetime] = None
    filed_with_court: str = ""
    
    # Logistics summary
    total_setup_time: int = 0  # minutes
    technology_requirements: Set[TechnologyRequirement] = field(default_factory=set)
    storage_requirements: Dict[str, List[str]] = field(default_factory=dict)
    
    # Quality control
    reviewed_by: List[str] = field(default_factory=list)
    review_complete: bool = False
    issues_identified: List[str] = field(default_factory=list)
    
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

class ExhibitAnalyzer:
    """Analyzes exhibits for strategic value and presentation optimization."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".ExhibitAnalyzer")
    
    def analyze_exhibit_strategic_value(self, exhibit: Exhibit,
                                      case_theme: str = "") -> Dict[str, Any]:
        """Analyze strategic value and presentation impact of exhibit."""
        analysis = {
            'strategic_score': 0.0,
            'impact_factors': {},
            'presentation_recommendations': [],
            'risk_assessment': {},
            'optimization_suggestions': []
        }
        
        # Calculate strategic score
        score_factors = []
        
        # Importance level impact
        score_factors.append(exhibit.importance_level * 0.3)
        
        # Jury appeal factor
        score_factors.append(exhibit.jury_appeal_factor * 0.2)
        
        # Exhibit type effectiveness
        type_effectiveness = {
            ExhibitType.PHOTOGRAPH: 0.8,
            ExhibitType.VIDEO: 0.9,
            ExhibitType.DEMONSTRATIVE: 0.85,
            ExhibitType.CHART_GRAPH: 0.7,
            ExhibitType.DOCUMENT: 0.6,
            ExhibitType.AUDIO: 0.75,
            ExhibitType.ANIMATION: 0.9,
            ExhibitType.TIMELINE: 0.8
        }
        effectiveness = type_effectiveness.get(exhibit.exhibit_type, 0.5)
        score_factors.append(effectiveness * 0.3)
        
        # Authentication strength
        if exhibit.authentication and exhibit.authentication.foundation_complete:
            score_factors.append(0.2)
        elif exhibit.authentication:
            score_factors.append(0.1)
        
        analysis['strategic_score'] = min(1.0, sum(score_factors) / 5.0)
        
        # Impact factors
        analysis['impact_factors'] = {
            'visual_impact': self._assess_visual_impact(exhibit),
            'emotional_impact': self._assess_emotional_impact(exhibit),
            'credibility_impact': self._assess_credibility_impact(exhibit),
            'complexity_factor': self._assess_complexity(exhibit),
            'memorability_factor': self._assess_memorability(exhibit)
        }
        
        # Presentation recommendations
        recommendations = []
        
        if exhibit.exhibit_type in [ExhibitType.PHOTOGRAPH, ExhibitType.CHART_GRAPH]:
            recommendations.append("Consider blown-up version for jury visibility")
        
        if exhibit.exhibit_type in [ExhibitType.VIDEO, ExhibitType.AUDIO]:
            recommendations.append("Test all audio/video equipment before trial")
            recommendations.append("Prepare transcript for jury reference")
        
        if exhibit.jury_appeal_factor >= 4:
            recommendations.append("Use early in case to set strong foundation")
        
        if exhibit.importance_level >= 4 and not exhibit.demonstrative_aids:
            recommendations.append("Consider adding demonstrative aids to enhance impact")
        
        analysis['presentation_recommendations'] = recommendations
        
        # Risk assessment
        risk_factors = []
        risk_score = 0.0
        
        if exhibit.objections:
            risk_factors.append("Active objections pending")
            risk_score += 0.3
        
        if exhibit.anticipated_objections and not exhibit.response_prepared:
            risk_factors.append("Anticipated objections without prepared responses")
            risk_score += 0.2
        
        if exhibit.authentication and not exhibit.authentication.foundation_complete:
            risk_factors.append("Authentication foundation incomplete")
            risk_score += 0.25
        
        if exhibit.presentation and exhibit.presentation.technology_needed and not exhibit.presentation.tested_in_courtroom:
            risk_factors.append("Technology requirements not tested in courtroom")
            risk_score += 0.15
        
        analysis['risk_assessment'] = {
            'risk_score': min(1.0, risk_score),
            'risk_factors': risk_factors,
            'mitigation_needed': risk_score > 0.3
        }
        
        # Optimization suggestions
        suggestions = []
        
        if analysis['strategic_score'] < 0.6:
            suggestions.append("Consider strengthening exhibit or removing from list")
        
        if exhibit.exhibit_type == ExhibitType.DOCUMENT and exhibit.jury_appeal_factor < 3:
            suggestions.append("Consider creating demonstrative version to increase impact")
        
        if not exhibit.strategic_notes:
            suggestions.append("Add strategic notes explaining exhibit's role in case theory")
        
        analysis['optimization_suggestions'] = suggestions
        
        return analysis
    
    def optimize_exhibit_order(self, exhibits: List[Exhibit],
                             case_strategy: str = "") -> List[str]:
        """Optimize order of exhibit presentation."""
        # Sort exhibits by strategic factors
        def sort_key(exhibit):
            # Primary factors: importance and strategic impact
            primary_score = (exhibit.importance_level + exhibit.jury_appeal_factor) / 2
            
            # Secondary factors: authentication readiness and presentation ease
            secondary_score = 0
            if exhibit.authentication and exhibit.authentication.foundation_complete:
                secondary_score += 2
            if not exhibit.presentation or not exhibit.presentation.technology_needed:
                secondary_score += 1  # Easier to present
            
            return (primary_score, secondary_score)
        
        sorted_exhibits = sorted(exhibits, key=sort_key, reverse=True)
        return [exhibit.exhibit_id for exhibit in sorted_exhibits]
    
    def identify_exhibit_themes(self, exhibits: List[Exhibit]) -> Dict[str, List[str]]:
        """Identify thematic groupings of exhibits."""
        themes = defaultdict(list)
        
        for exhibit in exhibits:
            # Group by exhibit type
            type_theme = f"{exhibit.exhibit_type.value.replace('_', ' ').title()} Evidence"
            themes[type_theme].append(exhibit.exhibit_id)
            
            # Group by strategic notes keywords
            if exhibit.strategic_notes:
                # Simple keyword extraction
                keywords = exhibit.strategic_notes.lower().split()
                for keyword in ['damages', 'liability', 'causation', 'negligence', 'contract']:
                    if keyword in keywords:
                        theme_name = f"{keyword.title()} Evidence"
                        themes[theme_name].append(exhibit.exhibit_id)
            
            # Group by witness
            if exhibit.witness_presenting:
                theme_name = f"Witness: {exhibit.witness_presenting}"
                themes[theme_name].append(exhibit.exhibit_id)
        
        return dict(themes)
    
    def _assess_visual_impact(self, exhibit: Exhibit) -> float:
        """Assess visual impact of exhibit on jury."""
        visual_scores = {
            ExhibitType.PHOTOGRAPH: 0.9,
            ExhibitType.VIDEO: 0.95,
            ExhibitType.DEMONSTRATIVE: 0.85,
            ExhibitType.CHART_GRAPH: 0.8,
            ExhibitType.MAP_DIAGRAM: 0.75,
            ExhibitType.ANIMATION: 0.9,
            ExhibitType.TIMELINE: 0.7,
            ExhibitType.DOCUMENT: 0.3,
            ExhibitType.AUDIO: 0.1
        }
        
        base_score = visual_scores.get(exhibit.exhibit_type, 0.5)
        
        # Adjust for highlighting and blown-up versions
        if exhibit.highlighting_applied:
            base_score += 0.1
        if exhibit.blown_up_versions:
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def _assess_emotional_impact(self, exhibit: Exhibit) -> float:
        """Assess emotional impact on jury."""
        # This would be more sophisticated in real implementation
        emotional_keywords = ['injury', 'accident', 'pain', 'suffering', 'loss', 'damage']
        
        base_score = 0.3
        description_lower = exhibit.description.lower()
        
        for keyword in emotional_keywords:
            if keyword in description_lower:
                base_score += 0.15
        
        # Visual exhibits generally have higher emotional impact
        if exhibit.exhibit_type in [ExhibitType.PHOTOGRAPH, ExhibitType.VIDEO]:
            base_score += 0.2
        
        return min(1.0, base_score)
    
    def _assess_credibility_impact(self, exhibit: Exhibit) -> float:
        """Assess credibility enhancement potential."""
        base_score = 0.5
        
        # Strong authentication increases credibility
        if exhibit.authentication and exhibit.authentication.foundation_complete:
            base_score += 0.3
        
        # Official sources increase credibility
        if exhibit.source_document_path and 'official' in exhibit.source_document_path.lower():
            base_score += 0.2
        
        # Certain exhibit types have inherent credibility
        credible_types = [ExhibitType.X_RAY, ExhibitType.MEDICAL_IMAGE, ExhibitType.DOCUMENT]
        if exhibit.exhibit_type in credible_types:
            base_score += 0.2
        
        return min(1.0, base_score)
    
    def _assess_complexity(self, exhibit: Exhibit) -> float:
        """Assess complexity of exhibit presentation."""
        complexity_score = 0.2  # Base low complexity
        
        # Technology requirements add complexity
        if exhibit.presentation:
            tech_count = len(exhibit.presentation.technology_needed)
            complexity_score += tech_count * 0.15
        
        # Authentication requirements add complexity
        if exhibit.authentication and not exhibit.authentication.foundation_complete:
            complexity_score += 0.3
        
        # Objections add complexity
        if exhibit.objections or exhibit.anticipated_objections:
            complexity_score += 0.2
        
        return min(1.0, complexity_score)
    
    def _assess_memorability(self, exhibit: Exhibit) -> float:
        """Assess how memorable exhibit will be for jury."""
        memorable_types = [
            ExhibitType.VIDEO, ExhibitType.ANIMATION, ExhibitType.PHOTOGRAPH,
            ExhibitType.DEMONSTRATIVE, ExhibitType.MODEL
        ]
        
        base_score = 0.8 if exhibit.exhibit_type in memorable_types else 0.4
        
        # High jury appeal factor increases memorability
        base_score += (exhibit.jury_appeal_factor - 3) * 0.1
        
        # Unique or unusual exhibits are more memorable
        if exhibit.exhibit_type in [ExhibitType.ANIMATION, ExhibitType.MODEL]:
            base_score += 0.2
        
        return min(1.0, max(0.1, base_score))

class ExhibitManager:
    """Main exhibit management system."""
    
    def __init__(self):
        self.exhibits: Dict[str, Exhibit] = {}
        self.exhibit_lists: Dict[str, ExhibitList] = {}
        self.authentications: Dict[str, ExhibitAuthentication] = {}
        self.objections: Dict[str, ExhibitObjection] = {}
        self.presentations: Dict[str, ExhibitPresentation] = {}
        self.analyzer = ExhibitAnalyzer()
        self.logger = logging.getLogger(__name__ + ".ExhibitManager")
    
    def add_exhibit(self, exhibit: Exhibit) -> str:
        """Add exhibit to management system."""
        if not exhibit.exhibit_id:
            exhibit.exhibit_id = str(uuid.uuid4())
        
        # Generate exhibit number if not provided
        if not exhibit.exhibit_number:
            exhibit.exhibit_number = self._generate_exhibit_number(exhibit.party)
        
        # Initialize authentication if needed
        if not exhibit.authentication and exhibit.exhibit_type != ExhibitType.DEMONSTRATIVE:
            auth_id = str(uuid.uuid4())
            exhibit.authentication = ExhibitAuthentication(
                authentication_id=auth_id,
                foundation_elements=self._get_default_foundation_elements(exhibit.exhibit_type)
            )
            self.authentications[auth_id] = exhibit.authentication
        
        # Initialize presentation details
        if not exhibit.presentation:
            pres_id = str(uuid.uuid4())
            exhibit.presentation = ExhibitPresentation(
                presentation_id=pres_id,
                technology_needed=self._get_default_technology_requirements(exhibit.exhibit_type)
            )
            self.presentations[pres_id] = exhibit.presentation
        
        self.exhibits[exhibit.exhibit_id] = exhibit
        self.logger.info(f"Added exhibit: {exhibit.exhibit_id} - {exhibit.exhibit_number}")
        return exhibit.exhibit_id
    
    def create_exhibit_list(self, case_id: str, party: ExhibitParty,
                          trial_date: Optional[date] = None) -> str:
        """Create new exhibit list."""
        list_id = str(uuid.uuid4())
        
        exhibit_list = ExhibitList(
            list_id=list_id,
            case_id=case_id,
            party=party,
            trial_date=trial_date
        )
        
        self.exhibit_lists[list_id] = exhibit_list
        self.logger.info(f"Created exhibit list: {list_id}")
        return list_id
    
    def add_exhibit_to_list(self, list_id: str, exhibit_id: str) -> bool:
        """Add exhibit to specific exhibit list."""
        if list_id not in self.exhibit_lists or exhibit_id not in self.exhibits:
            return False
        
        exhibit_list = self.exhibit_lists[list_id]
        exhibit = self.exhibits[exhibit_id]
        
        if exhibit_id not in exhibit_list.exhibits:
            exhibit_list.exhibits.append(exhibit_id)
            
            # Update list statistics
            exhibit_list.total_exhibits = len(exhibit_list.exhibits)
            
            # Update type counts
            exhibit_type = exhibit.exhibit_type.value
            exhibit_list.exhibits_by_type[exhibit_type] = exhibit_list.exhibits_by_type.get(exhibit_type, 0) + 1
            
            # Update status counts
            status = exhibit.status.value
            exhibit_list.exhibits_by_status[status] = exhibit_list.exhibits_by_status.get(status, 0) + 1
            
            # Update technology requirements
            if exhibit.presentation:
                exhibit_list.technology_requirements.update(exhibit.presentation.technology_needed)
                exhibit_list.total_setup_time += exhibit.presentation.setup_time_minutes
            
            exhibit_list.last_updated = datetime.now()
            
            self.logger.info(f"Added exhibit {exhibit_id} to list {list_id}")
            
        return True
    
    def authenticate_exhibit(self, exhibit_id: str, witness_id: str,
                           authentication_method: str, foundation_notes: str = "") -> bool:
        """Complete exhibit authentication."""
        if exhibit_id not in self.exhibits:
            return False
        
        exhibit = self.exhibits[exhibit_id]
        
        if exhibit.authentication:
            auth = exhibit.authentication
            auth.authenticating_witness = witness_id
            auth.authentication_method = authentication_method
            auth.foundation_complete = True
            
            if foundation_notes:
                auth.authentication_script = foundation_notes
            
            # Update exhibit status
            exhibit.status = ExhibitStatus.AUTHENTICATED
            exhibit.last_modified = datetime.now()
            
            # Log modification
            exhibit.modification_log.append({
                'timestamp': datetime.now(),
                'action': 'authenticated',
                'details': f'Authenticated by {witness_id} using {authentication_method}',
                'user': 'system'
            })
            
            self.logger.info(f"Authenticated exhibit {exhibit_id}")
            return True
        
        return False
    
    def record_objection(self, exhibit_id: str, objection_type: ObjectionType,
                        objecting_party: str, details: str) -> str:
        """Record objection to exhibit."""
        objection_id = str(uuid.uuid4())
        
        objection = ExhibitObjection(
            objection_id=objection_id,
            objection_type=objection_type,
            objecting_party=objecting_party,
            objection_details=details
        )
        
        self.objections[objection_id] = objection
        
        # Add objection to exhibit
        if exhibit_id in self.exhibits:
            exhibit = self.exhibits[exhibit_id]
            exhibit.objections.append(objection_id)
            exhibit.status = ExhibitStatus.OBJECTED
            exhibit.last_modified = datetime.now()
        
        self.logger.info(f"Recorded objection {objection_id} for exhibit {exhibit_id}")
        return objection_id
    
    def prepare_exhibit_for_trial(self, exhibit_id: str, witness_id: str,
                                trial_day: int, presentation_order: int) -> Dict[str, Any]:
        """Prepare exhibit for trial presentation."""
        if exhibit_id not in self.exhibits:
            return {'error': 'Exhibit not found'}
        
        exhibit = self.exhibits[exhibit_id]
        
        # Update trial logistics
        exhibit.witness_presenting = witness_id
        exhibit.trial_day_planned = trial_day
        exhibit.order_of_presentation = presentation_order
        exhibit.status = ExhibitStatus.PREPARED
        
        # Preparation checklist
        checklist = {
            'exhibit_id': exhibit_id,
            'preparation_complete': False,
            'checklist_items': [],
            'technology_setup': {},
            'authentication_ready': False,
            'copies_prepared': False,
            'issues_identified': []
        }
        
        # Check authentication readiness
        if exhibit.authentication and exhibit.authentication.foundation_complete:
            checklist['authentication_ready'] = True
            checklist['checklist_items'].append('✓ Authentication complete')
        else:
            checklist['checklist_items'].append('⚠ Authentication needs completion')
            checklist['issues_identified'].append('Authentication foundation incomplete')
        
        # Check copies and preparation
        if exhibit.copies_made >= 3:  # Court, opposing counsel, jury
            checklist['copies_prepared'] = True
            checklist['checklist_items'].append('✓ Sufficient copies prepared')
        else:
            checklist['checklist_items'].append('⚠ Need to prepare more copies')
            checklist['issues_identified'].append('Insufficient copies prepared')
        
        # Technology setup check
        if exhibit.presentation:
            pres = exhibit.presentation
            if pres.tested_in_courtroom:
                checklist['technology_setup']['tested'] = True
                checklist['checklist_items'].append('✓ Technology tested in courtroom')
            else:
                checklist['technology_setup']['tested'] = False
                checklist['checklist_items'].append('⚠ Technology needs courtroom testing')
                checklist['issues_identified'].append('Technology not tested in courtroom')
            
            checklist['technology_setup']['requirements'] = [tech.value for tech in pres.technology_needed]
            checklist['technology_setup']['setup_time'] = pres.setup_time_minutes
        
        # Overall preparation status
        checklist['preparation_complete'] = (
            checklist['authentication_ready'] and
            checklist['copies_prepared'] and
            len(checklist['issues_identified']) == 0
        )
        
        if checklist['preparation_complete']:
            exhibit.status = ExhibitStatus.PRE_MARKED
        
        exhibit.last_modified = datetime.now()
        
        return checklist
    
    def mark_exhibit_for_identification(self, exhibit_id: str, court_reporter_notation: str = "") -> bool:
        """Mark exhibit for identification during trial."""
        if exhibit_id not in self.exhibits:
            return False
        
        exhibit = self.exhibits[exhibit_id]
        exhibit.marked_for_identification = True
        exhibit.identification_date = datetime.now()
        exhibit.court_reporter_notation = court_reporter_notation
        exhibit.last_modified = datetime.now()
        
        # Log the marking
        exhibit.modification_log.append({
            'timestamp': datetime.now(),
            'action': 'marked_for_identification',
            'details': f'Marked for identification: {court_reporter_notation}',
            'user': 'court_reporter'
        })
        
        self.logger.info(f"Marked exhibit {exhibit_id} for identification")
        return True
    
    def admit_exhibit(self, exhibit_id: str, admission_notes: str = "") -> bool:
        """Record exhibit admission by court."""
        if exhibit_id not in self.exhibits:
            return False
        
        exhibit = self.exhibits[exhibit_id]
        exhibit.status = ExhibitStatus.ADMITTED
        exhibit.admission_attempted = True
        exhibit.admission_date = datetime.now()
        exhibit.last_modified = datetime.now()
        
        # Log admission
        exhibit.modification_log.append({
            'timestamp': datetime.now(),
            'action': 'admitted',
            'details': admission_notes,
            'user': 'court'
        })
        
        self.logger.info(f"Admitted exhibit {exhibit_id}")
        return True
    
    def optimize_exhibit_presentation_order(self, list_id: str,
                                          case_strategy: str = "") -> List[str]:
        """Optimize order of exhibit presentation."""
        if list_id not in self.exhibit_lists:
            return []
        
        exhibit_list = self.exhibit_lists[list_id]
        exhibits = [self.exhibits[eid] for eid in exhibit_list.exhibits if eid in self.exhibits]
        
        optimized_order = self.analyzer.optimize_exhibit_order(exhibits, case_strategy)
        
        # Update presentation order in exhibit list
        exhibit_list.presentation_order = optimized_order
        exhibit_list.last_updated = datetime.now()
        
        return optimized_order
    
    def generate_exhibit_summary_report(self, list_id: str) -> Dict[str, Any]:
        """Generate comprehensive exhibit summary report."""
        if list_id not in self.exhibit_lists:
            return {'error': 'Exhibit list not found'}
        
        exhibit_list = self.exhibit_lists[list_id]
        exhibits = [self.exhibits[eid] for eid in exhibit_list.exhibits if eid in self.exhibits]
        
        report = {
            'list_info': {
                'list_id': list_id,
                'case_id': exhibit_list.case_id,
                'party': exhibit_list.party.value,
                'total_exhibits': len(exhibits),
                'trial_date': exhibit_list.trial_date.isoformat() if exhibit_list.trial_date else None
            },
            'preparation_status': {},
            'technology_requirements': {},
            'strategic_analysis': {},
            'risk_assessment': {},
            'logistics_summary': {},
            'recommendations': []
        }
        
        # Preparation status analysis
        status_counts = {}
        auth_complete = 0
        copies_ready = 0
        
        for exhibit in exhibits:
            status = exhibit.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if exhibit.authentication and exhibit.authentication.foundation_complete:
                auth_complete += 1
            
            if exhibit.copies_made >= 3:
                copies_ready += 1
        
        report['preparation_status'] = {
            'by_status': status_counts,
            'authentication_complete': auth_complete,
            'copies_ready': copies_ready,
            'ready_for_trial': status_counts.get('prepared', 0) + status_counts.get('pre_marked', 0),
            'completion_percentage': ((auth_complete + copies_ready) / (len(exhibits) * 2)) * 100 if exhibits else 0
        }
        
        # Technology requirements
        all_tech_requirements = set()
        total_setup_time = 0
        tech_exhibits = 0
        
        for exhibit in exhibits:
            if exhibit.presentation and exhibit.presentation.technology_needed:
                all_tech_requirements.update(exhibit.presentation.technology_needed)
                total_setup_time += exhibit.presentation.setup_time_minutes
                tech_exhibits += 1
        
        report['technology_requirements'] = {
            'equipment_needed': [tech.value for tech in all_tech_requirements],
            'total_setup_time_minutes': total_setup_time,
            'exhibits_requiring_technology': tech_exhibits,
            'courtroom_testing_needed': len([e for e in exhibits 
                                           if e.presentation and 
                                              e.presentation.technology_needed and 
                                              not e.presentation.tested_in_courtroom])
        }
        
        # Strategic analysis
        strategic_scores = []
        high_impact_exhibits = []
        
        for exhibit in exhibits:
            analysis = self.analyzer.analyze_exhibit_strategic_value(exhibit)
            strategic_scores.append(analysis['strategic_score'])
            
            if analysis['strategic_score'] >= 0.8:
                high_impact_exhibits.append(exhibit.exhibit_number)
        
        avg_strategic_score = sum(strategic_scores) / len(strategic_scores) if strategic_scores else 0
        
        report['strategic_analysis'] = {
            'average_strategic_value': avg_strategic_score,
            'high_impact_exhibits': high_impact_exhibits,
            'exhibit_themes': self.analyzer.identify_exhibit_themes(exhibits),
            'recommended_presentation_order': self.analyzer.optimize_exhibit_order(exhibits)[:5]  # Top 5
        }
        
        # Risk assessment
        total_objections = sum(len(e.objections) + len(e.anticipated_objections) for e in exhibits)
        exhibits_with_risks = len([e for e in exhibits if e.objections or e.anticipated_objections])
        
        report['risk_assessment'] = {
            'total_objections': total_objections,
            'exhibits_with_objections': exhibits_with_risks,
            'authentication_risks': len([e for e in exhibits 
                                       if e.authentication and not e.authentication.foundation_complete]),
            'technology_risks': len([e for e in exhibits 
                                   if e.presentation and e.presentation.technology_needed and 
                                      not e.presentation.tested_in_courtroom])
        }
        
        # Generate recommendations
        recommendations = []
        
        if report['preparation_status']['completion_percentage'] < 80:
            recommendations.append("Accelerate exhibit preparation - currently below 80% ready")
        
        if report['technology_requirements']['courtroom_testing_needed'] > 0:
            recommendations.append(f"Test technology for {report['technology_requirements']['courtroom_testing_needed']} exhibits in courtroom")
        
        if report['risk_assessment']['authentication_risks'] > 0:
            recommendations.append("Complete authentication foundation for all exhibits")
        
        if avg_strategic_score < 0.6:
            recommendations.append("Review exhibit list for strategic value - consider removing weak exhibits")
        
        report['recommendations'] = recommendations
        
        return report
    
    def search_exhibits(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Exhibit]:
        """Search exhibits by various criteria."""
        results = []
        query_lower = query.lower()
        
        for exhibit in self.exhibits.values():
            # Text search in title, description, and notes
            searchable_text = (
                f"{exhibit.title} {exhibit.description} {exhibit.strategic_notes} " +
                f"{exhibit.attorney_notes} {exhibit.trial_notes}"
            ).lower()
            
            if query_lower in searchable_text:
                # Apply filters if provided
                if filters:
                    if 'exhibit_type' in filters and exhibit.exhibit_type != filters['exhibit_type']:
                        continue
                    if 'status' in filters and exhibit.status != filters['status']:
                        continue
                    if 'party' in filters and exhibit.party != filters['party']:
                        continue
                    if 'importance_min' in filters and exhibit.importance_level < filters['importance_min']:
                        continue
                
                results.append(exhibit)
        
        # Sort by importance and strategic value
        return sorted(results, key=lambda x: (x.importance_level, x.jury_appeal_factor), reverse=True)
    
    def export_exhibit_list_for_court(self, list_id: str) -> Dict[str, Any]:
        """Export exhibit list in court-ready format."""
        if list_id not in self.exhibit_lists:
            return {'error': 'Exhibit list not found'}
        
        exhibit_list = self.exhibit_lists[list_id]
        exhibits = [self.exhibits[eid] for eid in exhibit_list.exhibits if eid in self.exhibits]
        
        # Sort by exhibit number
        exhibits.sort(key=lambda x: x.exhibit_number)
        
        court_list = {
            'header': {
                'case_id': exhibit_list.case_id,
                'party': exhibit_list.party.value,
                'date_filed': datetime.now().strftime("%B %d, %Y"),
                'total_exhibits': len(exhibits)
            },
            'exhibits': []
        }
        
        for exhibit in exhibits:
            court_exhibit = {
                'exhibit_number': exhibit.exhibit_number,
                'description': exhibit.title,
                'type': exhibit.exhibit_type.value.replace('_', ' ').title(),
                'witness': exhibit.witness_presenting or "TBD",
                'authentication_method': exhibit.authentication.authentication_method if exhibit.authentication else "TBD",
                'pages_or_duration': self._get_exhibit_size_description(exhibit),
                'technology_required': ', '.join([tech.value.replace('_', ' ').title() 
                                                 for tech in exhibit.presentation.technology_needed]) 
                                      if exhibit.presentation and exhibit.presentation.technology_needed else "None"
            }
            court_list['exhibits'].append(court_exhibit)
        
        return court_list
    
    def _generate_exhibit_number(self, party: ExhibitParty) -> str:
        """Generate next exhibit number for party."""
        party_prefix = {
            ExhibitParty.PLAINTIFF: "P",
            ExhibitParty.DEFENDANT: "D", 
            ExhibitParty.COURT: "C",
            ExhibitParty.JOINT: "J"
        }
        
        prefix = party_prefix.get(party, "X")
        
        # Count existing exhibits for this party
        party_exhibits = [e for e in self.exhibits.values() if e.party == party]
        next_number = len(party_exhibits) + 1
        
        return f"{prefix}-{next_number}"
    
    def _get_default_foundation_elements(self, exhibit_type: ExhibitType) -> List[str]:
        """Get default foundation elements for exhibit type."""
        foundation_elements = {
            ExhibitType.DOCUMENT: [
                "Witness recognition of document",
                "Document accuracy verification", 
                "Document completeness confirmation"
            ],
            ExhibitType.PHOTOGRAPH: [
                "Photograph accuracy",
                "Fair representation of scene",
                "Photographer identification"
            ],
            ExhibitType.VIDEO: [
                "Recording accuracy",
                "Chain of custody",
                "Equipment operation verification"
            ],
            ExhibitType.AUDIO: [
                "Voice identification",
                "Recording accuracy",
                "Chain of custody"
            ]
        }
        
        return foundation_elements.get(exhibit_type, ["Basic foundation required"])
    
    def _get_default_technology_requirements(self, exhibit_type: ExhibitType) -> List[TechnologyRequirement]:
        """Get default technology requirements for exhibit type."""
        tech_requirements = {
            ExhibitType.VIDEO: [TechnologyRequirement.PROJECTOR, TechnologyRequirement.AUDIO_SYSTEM],
            ExhibitType.AUDIO: [TechnologyRequirement.AUDIO_SYSTEM],
            ExhibitType.DIGITAL_EVIDENCE: [TechnologyRequirement.COMPUTER, TechnologyRequirement.PROJECTOR],
            ExhibitType.ANIMATION: [TechnologyRequirement.COMPUTER, TechnologyRequirement.PROJECTOR],
            ExhibitType.PRESENTATION: [TechnologyRequirement.COMPUTER, TechnologyRequirement.PROJECTOR],
            ExhibitType.PHOTOGRAPH: [TechnologyRequirement.DOCUMENT_CAMERA],
            ExhibitType.CHART_GRAPH: [TechnologyRequirement.DOCUMENT_CAMERA]
        }
        
        return tech_requirements.get(exhibit_type, [])
    
    def _get_exhibit_size_description(self, exhibit: Exhibit) -> str:
        """Get human-readable size description for exhibit."""
        if exhibit.exhibit_type in [ExhibitType.VIDEO, ExhibitType.AUDIO]:
            if exhibit.presentation:
                duration = exhibit.presentation.presentation_duration_minutes
                if duration:
                    return f"{duration} minutes"
            return "Duration TBD"
        elif exhibit.exhibit_type == ExhibitType.DOCUMENT:
            # Would determine page count in real implementation
            return "Multiple pages"
        else:
            return "N/A"