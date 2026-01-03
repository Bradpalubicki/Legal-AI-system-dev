"""
Jury Selection Analytics System

Comprehensive jury selection analysis system including juror profiling,
bias detection, demographic analysis, challenge recommendations, and
jury composition optimization for trial strategy.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime, date
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
import logging
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)

class JurorBias(Enum):
    """Types of potential juror bias."""
    PRO_PLAINTIFF = "pro_plaintiff"
    PRO_DEFENDANT = "pro_defendant"
    ANTI_CORPORATE = "anti_corporate"
    PRO_CORPORATE = "pro_corporate"
    ANTI_GOVERNMENT = "anti_government"
    PRO_GOVERNMENT = "pro_government"
    ANTI_LITIGATION = "anti_litigation"
    PRO_LITIGATION = "pro_litigation"
    CONSERVATIVE = "conservative"
    LIBERAL = "liberal"
    AUTHORITARIAN = "authoritarian"
    LIBERTARIAN = "libertarian"
    NONE_DETECTED = "none_detected"

class ChallengeType(Enum):
    """Types of jury challenges."""
    CAUSE = "cause"
    PEREMPTORY = "peremptory"
    NONE = "none"

class JurorStatus(Enum):
    """Status of juror in selection process."""
    QUALIFIED = "qualified"
    CHALLENGED_FOR_CAUSE = "challenged_for_cause"
    PEREMPTORY_CHALLENGE = "peremptory_challenge"
    SELECTED = "selected"
    ALTERNATE = "alternate"
    DISMISSED = "dismissed"

class DemographicCategory(Enum):
    """Demographic categories for analysis."""
    AGE = "age"
    GENDER = "gender"
    RACE_ETHNICITY = "race_ethnicity"
    EDUCATION = "education"
    OCCUPATION = "occupation"
    INCOME = "income"
    MARITAL_STATUS = "marital_status"
    CHILDREN = "children"
    POLITICAL_AFFILIATION = "political_affiliation"
    RELIGION = "religion"

@dataclass
class JurorProfile:
    """Comprehensive profile of potential juror."""
    juror_id: str
    juror_number: int
    
    # Basic Demographics
    age: Optional[int] = None
    age_range: Optional[str] = None  # "25-35", "35-45", etc.
    gender: Optional[str] = None
    race_ethnicity: Optional[str] = None
    
    # Socioeconomic
    education_level: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    income_range: Optional[str] = None
    
    # Personal Information
    marital_status: Optional[str] = None
    children_count: Optional[int] = None
    children_ages: List[int] = field(default_factory=list)
    
    # Background
    prior_jury_service: bool = False
    litigation_experience: Optional[str] = None
    criminal_history: Optional[str] = None
    military_service: Optional[str] = None
    
    # Attitudes and Beliefs
    political_affiliation: Optional[str] = None
    religious_affiliation: Optional[str] = None
    media_consumption: List[str] = field(default_factory=list)
    social_media_activity: Dict[str, str] = field(default_factory=dict)
    
    # Case-Specific Information
    case_knowledge: str = ""
    personal_connections: List[str] = field(default_factory=list)
    relevant_experiences: List[str] = field(default_factory=list)
    expressed_opinions: List[str] = field(default_factory=list)
    
    # Voir Dire Responses
    questionnaire_responses: Dict[str, str] = field(default_factory=dict)
    voir_dire_answers: Dict[str, str] = field(default_factory=dict)
    body_language_notes: List[str] = field(default_factory=list)
    verbal_cues: List[str] = field(default_factory=list)
    
    # Analysis Results
    bias_assessment: JurorBias = JurorBias.NONE_DETECTED
    bias_strength: float = 0.0  # 0-1 scale
    favorability_score: float = 0.5  # 0-1 scale (0=very unfavorable, 1=very favorable)
    reliability_score: float = 0.5  # 0-1 scale
    influence_potential: float = 0.5  # Potential to influence other jurors
    
    # Challenge Assessment
    challenge_recommendation: ChallengeType = ChallengeType.NONE
    challenge_priority: int = 0  # 1-10 scale
    challenge_reasons: List[str] = field(default_factory=list)
    
    # Status Tracking
    status: JurorStatus = JurorStatus.QUALIFIED
    notes: List[str] = field(default_factory=list)
    analyst_comments: str = ""
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class JuryComposition:
    """Analysis of overall jury composition."""
    composition_id: str
    selected_jurors: List[str] = field(default_factory=list)  # Juror IDs
    alternate_jurors: List[str] = field(default_factory=list)  # Juror IDs
    
    # Demographic Composition
    age_distribution: Dict[str, int] = field(default_factory=dict)
    gender_distribution: Dict[str, int] = field(default_factory=dict)
    education_distribution: Dict[str, int] = field(default_factory=dict)
    occupation_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Bias Analysis
    overall_bias_lean: JurorBias = JurorBias.NONE_DETECTED
    bias_strength: float = 0.0
    favorability_average: float = 0.5
    
    # Composition Quality
    diversity_score: float = 0.0  # 0-1 scale
    balance_score: float = 0.0  # 0-1 scale
    predictability_score: float = 0.0  # 0-1 scale
    
    # Strategic Assessment
    plaintiff_advantage: float = 0.0  # -1 to 1 scale
    defendant_advantage: float = 0.0  # -1 to 1 scale
    key_swing_jurors: List[str] = field(default_factory=list)  # Juror IDs
    
    # Recommendations
    strengths: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    strategic_recommendations: List[str] = field(default_factory=list)

@dataclass
class JurySelection:
    """Complete jury selection process and results."""
    selection_id: str
    case_id: str
    venue: str
    judge: str
    
    # Selection Process
    jury_pool_size: int
    voir_dire_date: Optional[date] = None
    selection_completed: bool = False
    
    # Participants
    plaintiff_attorneys: List[str] = field(default_factory=list)
    defendant_attorneys: List[str] = field(default_factory=list)
    
    # Challenge Usage
    peremptory_challenges_used: Dict[str, int] = field(default_factory=dict)  # party -> count
    peremptory_challenges_available: Dict[str, int] = field(default_factory=dict)
    cause_challenges: List[str] = field(default_factory=list)  # Juror IDs
    
    # Results
    final_composition: Optional[str] = None  # JuryComposition ID
    selection_summary: Dict[str, Any] = field(default_factory=dict)
    
    # Analysis
    selection_strategy_effectiveness: float = 0.0  # 0-1 scale
    missed_opportunities: List[str] = field(default_factory=list)
    successful_challenges: List[str] = field(default_factory=list)
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    completed_date: Optional[datetime] = None

class BiasDetector:
    """Detects potential juror bias based on various factors."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".BiasDetector")
        # Pre-defined bias indicators (would be more sophisticated in real implementation)
        self.bias_indicators = {
            JurorBias.ANTI_CORPORATE: {
                'occupations': ['union_member', 'activist', 'social_worker'],
                'keywords': ['corporate greed', 'big business', 'exploitation'],
                'experiences': ['layoff', 'workplace_injury', 'pension_loss']
            },
            JurorBias.PRO_CORPORATE: {
                'occupations': ['executive', 'manager', 'business_owner'],
                'keywords': ['free enterprise', 'job creation', 'economic growth'],
                'experiences': ['business_success', 'entrepreneurship']
            },
            JurorBias.ANTI_LITIGATION: {
                'keywords': ['lawsuit abuse', 'frivolous lawsuits', 'personal responsibility'],
                'experiences': ['sued_previously', 'insurance_fraud_victim']
            },
            JurorBias.PRO_LITIGATION: {
                'occupations': ['attorney', 'paralegal', 'legal_aid'],
                'experiences': ['successful_lawsuit', 'injury_claim']
            }
        }
    
    def detect_bias(self, juror: JurorProfile) -> Tuple[JurorBias, float, List[str]]:
        """Detect potential bias in juror profile."""
        bias_scores = defaultdict(float)
        reasons = []
        
        # Analyze occupation-based bias
        if juror.occupation:
            for bias_type, indicators in self.bias_indicators.items():
                if juror.occupation.lower() in indicators.get('occupations', []):
                    bias_scores[bias_type] += 0.3
                    reasons.append(f"Occupation ({juror.occupation}) suggests {bias_type.value}")
        
        # Analyze questionnaire responses
        for question, response in juror.questionnaire_responses.items():
            response_lower = response.lower()
            for bias_type, indicators in self.bias_indicators.items():
                for keyword in indicators.get('keywords', []):
                    if keyword.lower() in response_lower:
                        bias_scores[bias_type] += 0.2
                        reasons.append(f"Response contains bias indicator: {keyword}")
        
        # Analyze relevant experiences
        for experience in juror.relevant_experiences:
            experience_lower = experience.lower()
            for bias_type, indicators in self.bias_indicators.items():
                for exp_indicator in indicators.get('experiences', []):
                    if exp_indicator.lower() in experience_lower:
                        bias_scores[bias_type] += 0.25
                        reasons.append(f"Experience suggests bias: {experience}")
        
        # Analyze expressed opinions
        for opinion in juror.expressed_opinions:
            opinion_lower = opinion.lower()
            # Simple keyword matching for demonstration
            if any(word in opinion_lower for word in ['corporations are evil', 'big business']):
                bias_scores[JurorBias.ANTI_CORPORATE] += 0.4
                reasons.append(f"Expressed anti-corporate opinion: {opinion}")
            elif any(word in opinion_lower for word in ['lawsuits are frivolous', 'sue happy']):
                bias_scores[JurorBias.ANTI_LITIGATION] += 0.4
                reasons.append(f"Expressed anti-litigation opinion: {opinion}")
        
        # Determine strongest bias
        if not bias_scores:
            return JurorBias.NONE_DETECTED, 0.0, []
        
        strongest_bias = max(bias_scores.items(), key=lambda x: x[1])
        return strongest_bias[0], min(strongest_bias[1], 1.0), reasons
    
    def calculate_favorability_score(self, juror: JurorProfile, case_type: str,
                                   client_position: str) -> float:
        """Calculate how favorable juror is likely to be."""
        base_score = 0.5  # Neutral starting point
        
        # Adjust based on detected bias
        bias_adjustment = 0.0
        if client_position == "plaintiff":
            if juror.bias_assessment in [JurorBias.PRO_PLAINTIFF, JurorBias.PRO_LITIGATION]:
                bias_adjustment = juror.bias_strength * 0.3
            elif juror.bias_assessment in [JurorBias.PRO_DEFENDANT, JurorBias.ANTI_LITIGATION]:
                bias_adjustment = -juror.bias_strength * 0.3
        else:  # defendant
            if juror.bias_assessment in [JurorBias.PRO_DEFENDANT, JurorBias.ANTI_LITIGATION]:
                bias_adjustment = juror.bias_strength * 0.3
            elif juror.bias_assessment in [JurorBias.PRO_PLAINTIFF, JurorBias.PRO_LITIGATION]:
                bias_adjustment = -juror.bias_strength * 0.3
        
        # Case-specific adjustments
        case_adjustment = 0.0
        if case_type == "personal_injury" and client_position == "plaintiff":
            # Factors that might favor plaintiff in PI cases
            if juror.children_count and juror.children_count > 0:
                case_adjustment += 0.1  # Parents may be more sympathetic
            if juror.occupation and "healthcare" in juror.occupation.lower():
                case_adjustment += 0.15  # Healthcare workers understand injuries
        elif case_type == "corporate" and client_position == "defendant":
            # Factors that might favor corporate defendants
            if juror.occupation and any(term in juror.occupation.lower() 
                                     for term in ['business', 'manager', 'executive']):
                case_adjustment += 0.2
        
        # Demographic adjustments (simplified)
        demographic_adjustment = 0.0
        if juror.education_level:
            if "graduate" in juror.education_level.lower():
                demographic_adjustment += 0.05  # Higher education = more analytical
        
        final_score = base_score + bias_adjustment + case_adjustment + demographic_adjustment
        return max(0.0, min(1.0, final_score))

class DemographicAnalyzer:
    """Analyzes jury demographic composition and diversity."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".DemographicAnalyzer")
    
    def analyze_jury_diversity(self, jurors: List[JurorProfile]) -> Dict[str, Any]:
        """Analyze demographic diversity of jury."""
        analysis = {
            'diversity_score': 0.0,
            'demographic_breakdown': {},
            'diversity_strengths': [],
            'diversity_concerns': [],
            'representation_gaps': []
        }
        
        if not jurors:
            return analysis
        
        # Collect demographic data
        demographics = {
            'age_ranges': [],
            'genders': [],
            'education_levels': [],
            'occupations': [],
            'income_ranges': []
        }
        
        for juror in jurors:
            if juror.age_range:
                demographics['age_ranges'].append(juror.age_range)
            if juror.gender:
                demographics['genders'].append(juror.gender)
            if juror.education_level:
                demographics['education_levels'].append(juror.education_level)
            if juror.occupation:
                demographics['occupations'].append(juror.occupation)
            if juror.income_range:
                demographics['income_ranges'].append(juror.income_range)
        
        # Calculate diversity for each demographic
        diversity_scores = []
        
        for category, values in demographics.items():
            if values:
                unique_values = len(set(values))
                total_values = len(values)
                category_diversity = unique_values / total_values if total_values > 0 else 0
                diversity_scores.append(category_diversity)
                
                # Create breakdown
                value_counts = {}
                for value in values:
                    value_counts[value] = value_counts.get(value, 0) + 1
                analysis['demographic_breakdown'][category] = value_counts
        
        # Overall diversity score
        if diversity_scores:
            analysis['diversity_score'] = sum(diversity_scores) / len(diversity_scores)
        
        # Identify strengths and concerns
        if analysis['diversity_score'] >= 0.7:
            analysis['diversity_strengths'].append("High overall demographic diversity")
        elif analysis['diversity_score'] <= 0.4:
            analysis['diversity_concerns'].append("Low demographic diversity")
        
        # Check for specific representation gaps
        gender_breakdown = analysis['demographic_breakdown'].get('genders', {})
        if len(gender_breakdown) == 1:
            analysis['representation_gaps'].append("Single gender representation")
        
        age_breakdown = analysis['demographic_breakdown'].get('age_ranges', {})
        if len(age_breakdown) <= 2:
            analysis['representation_gaps'].append("Limited age range representation")
        
        return analysis
    
    def compare_to_community(self, jurors: List[JurorProfile], 
                           community_demographics: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Compare jury demographics to community demographics."""
        comparison = {
            'representativeness_score': 0.0,
            'category_comparisons': {},
            'over_represented': [],
            'under_represented': [],
            'well_represented': []
        }
        
        if not jurors or not community_demographics:
            return comparison
        
        # Analyze each demographic category
        representativeness_scores = []
        
        for category, community_dist in community_demographics.items():
            jury_dist = self._calculate_jury_distribution(jurors, category)
            
            # Calculate representativeness (1 - sum of absolute differences)
            total_diff = 0.0
            for demographic, community_pct in community_dist.items():
                jury_pct = jury_dist.get(demographic, 0.0)
                diff = abs(community_pct - jury_pct)
                total_diff += diff
                
                # Identify over/under representation (threshold: 15% difference)
                if diff > 0.15:
                    if jury_pct > community_pct:
                        comparison['over_represented'].append(f"{demographic} in {category}")
                    else:
                        comparison['under_represented'].append(f"{demographic} in {category}")
                else:
                    comparison['well_represented'].append(f"{demographic} in {category}")
            
            category_representativeness = max(0.0, 1.0 - (total_diff / 2.0))
            representativeness_scores.append(category_representativeness)
            comparison['category_comparisons'][category] = {
                'jury_distribution': jury_dist,
                'community_distribution': community_dist,
                'representativeness': category_representativeness
            }
        
        # Overall representativeness score
        if representativeness_scores:
            comparison['representativeness_score'] = statistics.mean(representativeness_scores)
        
        return comparison
    
    def _calculate_jury_distribution(self, jurors: List[JurorProfile], 
                                   category: str) -> Dict[str, float]:
        """Calculate distribution of demographic category in jury."""
        total_jurors = len(jurors)
        if total_jurors == 0:
            return {}
        
        category_values = []
        
        if category == "age_ranges":
            category_values = [j.age_range for j in jurors if j.age_range]
        elif category == "genders":
            category_values = [j.gender for j in jurors if j.gender]
        elif category == "education_levels":
            category_values = [j.education_level for j in jurors if j.education_level]
        elif category == "occupations":
            category_values = [j.occupation for j in jurors if j.occupation]
        
        # Calculate percentages
        distribution = {}
        for value in set(category_values):
            count = category_values.count(value)
            distribution[value] = count / total_jurors
        
        return distribution

class JuryAnalyzer:
    """Main jury analysis system coordinating all components."""
    
    def __init__(self):
        self.jurors: Dict[str, JurorProfile] = {}
        self.jury_compositions: Dict[str, JuryComposition] = {}
        self.jury_selections: Dict[str, JurySelection] = {}
        self.bias_detector = BiasDetector()
        self.demographic_analyzer = DemographicAnalyzer()
        self.logger = logging.getLogger(__name__ + ".JuryAnalyzer")
    
    def add_juror(self, juror: JurorProfile) -> str:
        """Add juror profile to the system."""
        if not juror.juror_id:
            juror.juror_id = str(uuid.uuid4())
        
        # Analyze bias
        bias, strength, reasons = self.bias_detector.detect_bias(juror)
        juror.bias_assessment = bias
        juror.bias_strength = strength
        if reasons:
            juror.notes.extend(reasons)
        
        # Update timestamp
        juror.last_updated = datetime.now()
        
        self.jurors[juror.juror_id] = juror
        self.logger.info(f"Added juror: {juror.juror_id}")
        return juror.juror_id
    
    def analyze_juror_for_case(self, juror_id: str, case_type: str, 
                             client_position: str) -> Dict[str, Any]:
        """Analyze specific juror for case suitability."""
        if juror_id not in self.jurors:
            raise ValueError(f"Juror {juror_id} not found")
        
        juror = self.jurors[juror_id]
        
        analysis = {
            'juror_id': juror_id,
            'basic_info': {
                'age_range': juror.age_range,
                'gender': juror.gender,
                'occupation': juror.occupation,
                'education': juror.education_level
            },
            'bias_analysis': {
                'detected_bias': juror.bias_assessment.value,
                'bias_strength': juror.bias_strength,
                'bias_reasons': [note for note in juror.notes if 'bias' in note.lower()]
            },
            'favorability_analysis': {},
            'challenge_recommendation': {},
            'strategic_notes': []
        }
        
        # Calculate favorability
        favorability = self.bias_detector.calculate_favorability_score(
            juror, case_type, client_position
        )
        juror.favorability_score = favorability
        
        analysis['favorability_analysis'] = {
            'favorability_score': favorability,
            'interpretation': self._interpret_favorability_score(favorability),
            'key_factors': self._identify_favorability_factors(juror, case_type, client_position)
        }
        
        # Generate challenge recommendation
        challenge_rec = self._generate_challenge_recommendation(juror, case_type, client_position)
        analysis['challenge_recommendation'] = challenge_rec
        
        # Strategic notes
        strategic_notes = self._generate_strategic_notes(juror, case_type)
        analysis['strategic_notes'] = strategic_notes
        
        return analysis
    
    def optimize_jury_selection(self, available_jurors: List[str], jury_size: int,
                              case_type: str, client_position: str) -> Dict[str, Any]:
        """Optimize jury selection from available jurors."""
        juror_profiles = [self.jurors[jid] for jid in available_jurors if jid in self.jurors]
        
        if not juror_profiles:
            return {'error': 'No available jurors found'}
        
        # Calculate favorability scores for all jurors
        for juror in juror_profiles:
            juror.favorability_score = self.bias_detector.calculate_favorability_score(
                juror, case_type, client_position
            )
        
        # Generate multiple jury composition scenarios
        scenarios = self._generate_jury_scenarios(juror_profiles, jury_size, case_type)
        
        # Rank scenarios
        ranked_scenarios = sorted(scenarios, key=lambda s: s['overall_score'], reverse=True)
        
        optimization_result = {
            'recommended_composition': ranked_scenarios[0] if ranked_scenarios else None,
            'alternative_compositions': ranked_scenarios[1:3],  # Top 3 alternatives
            'juror_rankings': sorted(
                [(j.juror_id, j.favorability_score) for j in juror_profiles],
                key=lambda x: x[1], reverse=True
            ),
            'selection_strategy': self._generate_selection_strategy(juror_profiles, case_type),
            'challenge_priorities': self._prioritize_challenges(juror_profiles, client_position)
        }
        
        return optimization_result
    
    def analyze_jury_composition(self, selected_juror_ids: List[str], 
                               case_type: str, client_position: str) -> str:
        """Analyze final jury composition."""
        composition_id = str(uuid.uuid4())
        selected_jurors = [self.jurors[jid] for jid in selected_juror_ids if jid in self.jurors]
        
        if not selected_jurors:
            raise ValueError("No valid jurors provided")
        
        # Create composition analysis
        composition = JuryComposition(
            composition_id=composition_id,
            selected_jurors=selected_juror_ids
        )
        
        # Demographic analysis
        demographic_analysis = self.demographic_analyzer.analyze_jury_diversity(selected_jurors)
        composition.diversity_score = demographic_analysis['diversity_score']
        
        # Calculate bias and favorability
        bias_scores = [j.bias_strength for j in selected_jurors]
        favorability_scores = [j.favorability_score for j in selected_jurors]
        
        composition.favorability_average = statistics.mean(favorability_scores) if favorability_scores else 0.5
        composition.bias_strength = statistics.mean(bias_scores) if bias_scores else 0.0
        
        # Determine overall bias lean
        pro_client_count = len([j for j in selected_jurors if j.favorability_score > 0.6])
        anti_client_count = len([j for j in selected_jurors if j.favorability_score < 0.4])
        
        if pro_client_count > anti_client_count:
            composition.overall_bias_lean = JurorBias.PRO_PLAINTIFF if client_position == "plaintiff" else JurorBias.PRO_DEFENDANT
        elif anti_client_count > pro_client_count:
            composition.overall_bias_lean = JurorBias.PRO_DEFENDANT if client_position == "plaintiff" else JurorBias.PRO_PLAINTIFF
        else:
            composition.overall_bias_lean = JurorBias.NONE_DETECTED
        
        # Strategic assessment
        composition.plaintiff_advantage = composition.favorability_average if client_position == "plaintiff" else 1 - composition.favorability_average
        composition.defendant_advantage = 1 - composition.plaintiff_advantage
        
        # Identify swing jurors (moderate favorability scores)
        swing_jurors = [j.juror_id for j in selected_jurors if 0.4 <= j.favorability_score <= 0.6]
        composition.key_swing_jurors = swing_jurors
        
        # Generate recommendations
        composition.strengths, composition.concerns, composition.strategic_recommendations = \
            self._analyze_composition_strengths_concerns(selected_jurors, case_type, client_position)
        
        self.jury_compositions[composition_id] = composition
        return composition_id
    
    def track_jury_selection_process(self, case_id: str, venue: str, 
                                   judge: str, jury_pool_size: int) -> str:
        """Initialize jury selection process tracking."""
        selection_id = str(uuid.uuid4())
        
        selection = JurySelection(
            selection_id=selection_id,
            case_id=case_id,
            venue=venue,
            judge=judge,
            jury_pool_size=jury_pool_size
        )
        
        self.jury_selections[selection_id] = selection
        return selection_id
    
    def record_challenge_decision(self, selection_id: str, juror_id: str,
                                challenge_type: ChallengeType, challenging_party: str,
                                reason: str) -> bool:
        """Record challenge decision during jury selection."""
        if selection_id not in self.jury_selections:
            return False
        
        selection = self.jury_selections[selection_id]
        
        if challenge_type == ChallengeType.PEREMPTORY:
            current_count = selection.peremptory_challenges_used.get(challenging_party, 0)
            selection.peremptory_challenges_used[challenging_party] = current_count + 1
        elif challenge_type == ChallengeType.CAUSE:
            selection.cause_challenges.append(juror_id)
        
        # Update juror status
        if juror_id in self.jurors:
            juror = self.jurors[juror_id]
            if challenge_type == ChallengeType.PEREMPTORY:
                juror.status = JurorStatus.PEREMPTORY_CHALLENGE
            elif challenge_type == ChallengeType.CAUSE:
                juror.status = JurorStatus.CHALLENGED_FOR_CAUSE
            
            juror.challenge_reasons.append(reason)
        
        return True
    
    def generate_voir_dire_questions(self, case_type: str, key_issues: List[str]) -> List[Dict[str, str]]:
        """Generate targeted voir dire questions."""
        questions = []
        
        # Standard questions
        questions.extend([
            {
                'question': "Have you or anyone close to you ever been involved in a similar legal situation?",
                'category': 'experience',
                'purpose': 'Identify potential bias from personal experience'
            },
            {
                'question': "Do you have any strong feelings about lawsuits in general?",
                'category': 'attitude',
                'purpose': 'Detect anti-litigation bias'
            },
            {
                'question': "Have you formed any opinions about this case from media coverage?",
                'category': 'prejudgment',
                'purpose': 'Identify pre-existing opinions'
            }
        ])
        
        # Case-specific questions
        if case_type == "personal_injury":
            questions.extend([
                {
                    'question': "Do you believe people are too quick to sue when injured?",
                    'category': 'attitude',
                    'purpose': 'Detect anti-plaintiff bias in PI cases'
                },
                {
                    'question': "Have you ever been seriously injured in an accident?",
                    'category': 'experience',
                    'purpose': 'Identify potential sympathy or bias'
                }
            ])
        elif case_type == "corporate":
            questions.extend([
                {
                    'question': "What are your feelings about large corporations?",
                    'category': 'attitude',
                    'purpose': 'Detect anti-corporate bias'
                },
                {
                    'question': "Do you invest in the stock market or own business stock?",
                    'category': 'financial',
                    'purpose': 'Identify potential pro-business bias'
                }
            ])
        
        # Issue-specific questions
        for issue in key_issues:
            if "medical" in issue.lower():
                questions.append({
                    'question': f"Do you have experience with {issue}? How might that affect your judgment?",
                    'category': 'issue_specific',
                    'purpose': f'Assess bias regarding {issue}'
                })
        
        return questions
    
    def search_jurors(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[JurorProfile]:
        """Search jurors by various criteria."""
        results = []
        query_lower = query.lower()
        
        for juror in self.jurors.values():
            # Text search in occupation, education, and notes
            searchable_text = (
                f"{juror.occupation or ''} {juror.education_level or ''} " +
                f"{' '.join(juror.notes)} {juror.analyst_comments}"
            ).lower()
            
            if query_lower in searchable_text:
                # Apply filters if provided
                if filters:
                    if 'bias_assessment' in filters and juror.bias_assessment != filters['bias_assessment']:
                        continue
                    if 'favorability_min' in filters and juror.favorability_score < filters['favorability_min']:
                        continue
                    if 'age_range' in filters and juror.age_range != filters['age_range']:
                        continue
                    if 'status' in filters and juror.status != filters['status']:
                        continue
                
                results.append(juror)
        
        # Sort by favorability score (highest first)
        return sorted(results, key=lambda x: x.favorability_score, reverse=True)
    
    def _interpret_favorability_score(self, score: float) -> str:
        """Interpret favorability score into text description."""
        if score >= 0.8:
            return "Very Favorable"
        elif score >= 0.6:
            return "Favorable"
        elif score >= 0.4:
            return "Neutral"
        elif score >= 0.2:
            return "Unfavorable"
        else:
            return "Very Unfavorable"
    
    def _identify_favorability_factors(self, juror: JurorProfile, case_type: str,
                                     client_position: str) -> List[str]:
        """Identify key factors affecting favorability."""
        factors = []
        
        if juror.bias_assessment != JurorBias.NONE_DETECTED:
            factors.append(f"Detected bias: {juror.bias_assessment.value}")
        
        if juror.relevant_experiences:
            factors.append(f"Relevant experience: {juror.relevant_experiences[0]}")
        
        if juror.occupation:
            factors.append(f"Occupation: {juror.occupation}")
        
        if juror.litigation_experience:
            factors.append(f"Prior litigation: {juror.litigation_experience}")
        
        return factors[:3]  # Top 3 factors
    
    def _generate_challenge_recommendation(self, juror: JurorProfile, case_type: str,
                                         client_position: str) -> Dict[str, Any]:
        """Generate challenge recommendation for juror."""
        recommendation = {
            'challenge_type': ChallengeType.NONE,
            'priority': 0,
            'reasons': [],
            'confidence': 0.5
        }
        
        # For cause challenges
        cause_reasons = []
        if juror.case_knowledge:
            cause_reasons.append("Prior knowledge of case")
        if juror.personal_connections:
            cause_reasons.append("Personal connections to parties")
        if "bias" in juror.litigation_experience.lower() if juror.litigation_experience else False:
            cause_reasons.append("Strong bias from litigation experience")
        
        if cause_reasons:
            recommendation['challenge_type'] = ChallengeType.CAUSE
            recommendation['priority'] = 10
            recommendation['reasons'] = cause_reasons
            recommendation['confidence'] = 0.9
            return recommendation
        
        # Peremptory challenges
        if juror.favorability_score <= 0.3:
            recommendation['challenge_type'] = ChallengeType.PEREMPTORY
            recommendation['priority'] = 8
            recommendation['reasons'].append(f"Very unfavorable (score: {juror.favorability_score:.2f})")
            recommendation['confidence'] = 0.8
        elif juror.favorability_score <= 0.4 and juror.bias_strength > 0.6:
            recommendation['challenge_type'] = ChallengeType.PEREMPTORY
            recommendation['priority'] = 6
            recommendation['reasons'].append("Unfavorable with strong bias")
            recommendation['confidence'] = 0.7
        
        return recommendation
    
    def _generate_jury_scenarios(self, juror_profiles: List[JurorProfile], 
                               jury_size: int, case_type: str) -> List[Dict[str, Any]]:
        """Generate multiple jury composition scenarios."""
        scenarios = []
        
        # Sort jurors by favorability
        sorted_jurors = sorted(juror_profiles, key=lambda j: j.favorability_score, reverse=True)
        
        # Scenario 1: Most favorable jurors
        if len(sorted_jurors) >= jury_size:
            top_jurors = sorted_jurors[:jury_size]
            scenario = {
                'juror_ids': [j.juror_id for j in top_jurors],
                'avg_favorability': statistics.mean(j.favorability_score for j in top_jurors),
                'diversity_score': self.demographic_analyzer.analyze_jury_diversity(top_jurors)['diversity_score'],
                'overall_score': 0.0  # Will be calculated
            }
            scenario['overall_score'] = (scenario['avg_favorability'] * 0.7 + 
                                       scenario['diversity_score'] * 0.3)
            scenarios.append(scenario)
        
        # Scenario 2: Balanced composition (could add more sophisticated scenarios)
        
        return scenarios
    
    def _generate_selection_strategy(self, juror_profiles: List[JurorProfile],
                                   case_type: str) -> List[str]:
        """Generate strategic recommendations for jury selection."""
        strategy = []
        
        # Identify high-priority challenges
        hostile_jurors = [j for j in juror_profiles if j.favorability_score < 0.3]
        if hostile_jurors:
            strategy.append(f"Priority challenge {len(hostile_jurors)} highly unfavorable jurors")
        
        # Identify must-keep jurors
        favorable_jurors = [j for j in juror_profiles if j.favorability_score > 0.7]
        if favorable_jurors:
            strategy.append(f"Protect {len(favorable_jurors)} highly favorable jurors")
        
        # Diversity considerations
        diversity_analysis = self.demographic_analyzer.analyze_jury_diversity(juror_profiles)
        if diversity_analysis['diversity_score'] < 0.5:
            strategy.append("Consider diversity in final selection")
        
        return strategy
    
    def _prioritize_challenges(self, juror_profiles: List[JurorProfile],
                             client_position: str) -> List[Dict[str, Any]]:
        """Prioritize peremptory challenges."""
        challenges = []
        
        for juror in juror_profiles:
            if juror.favorability_score < 0.5:  # Unfavorable jurors
                priority = int((1 - juror.favorability_score) * 10)  # Convert to 1-10 scale
                challenges.append({
                    'juror_id': juror.juror_id,
                    'priority': priority,
                    'reason': f"Unfavorable score: {juror.favorability_score:.2f}",
                    'bias': juror.bias_assessment.value
                })
        
        return sorted(challenges, key=lambda c: c['priority'], reverse=True)
    
    def _analyze_composition_strengths_concerns(self, selected_jurors: List[JurorProfile],
                                              case_type: str, client_position: str) -> Tuple[List[str], List[str], List[str]]:
        """Analyze strengths and concerns of jury composition."""
        strengths = []
        concerns = []
        recommendations = []
        
        # Calculate statistics
        avg_favorability = statistics.mean(j.favorability_score for j in selected_jurors)
        favorable_count = len([j for j in selected_jurors if j.favorability_score > 0.6])
        unfavorable_count = len([j for j in selected_jurors if j.favorability_score < 0.4])
        
        # Analyze strengths
        if avg_favorability > 0.6:
            strengths.append("Overall favorable jury composition")
        if favorable_count > len(selected_jurors) // 2:
            strengths.append("Majority of jurors appear favorable")
        
        diversity_analysis = self.demographic_analyzer.analyze_jury_diversity(selected_jurors)
        if diversity_analysis['diversity_score'] > 0.7:
            strengths.append("Good demographic diversity")
        
        # Analyze concerns
        if unfavorable_count > len(selected_jurors) // 3:
            concerns.append("Significant number of unfavorable jurors")
        if avg_favorability < 0.4:
            concerns.append("Overall unfavorable jury composition")
        
        # Generate recommendations
        swing_jurors = [j for j in selected_jurors if 0.4 <= j.favorability_score <= 0.6]
        if len(swing_jurors) > 3:
            recommendations.append(f"Focus on persuading {len(swing_jurors)} swing jurors")
        
        if unfavorable_count > 0:
            recommendations.append("Prepare strategies to address unfavorable jurors")
        
        return strengths, concerns, recommendations