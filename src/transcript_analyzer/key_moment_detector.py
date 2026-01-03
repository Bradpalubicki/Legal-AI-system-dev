"""
AI-powered detection of key moments, breakthrough statements, and significant developments in court proceedings.
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import json
import asyncio
from datetime import datetime

from ..shared.utils.ai_client import AIClient
from ..shared.database.models import Case, TranscriptSegment
from .statement_analyzer import IdentifiedStatement, StatementType


class MomentType(Enum):
    """Types of key moments that can be detected."""
    BREAKTHROUGH_ADMISSION = "breakthrough_admission"
    SMOKING_GUN_EVIDENCE = "smoking_gun_evidence"
    WITNESS_BREAKDOWN = "witness_breakdown"
    EXPERT_CONTRADICTION = "expert_contradiction"
    SURPRISE_REVELATION = "surprise_revelation"
    DRAMATIC_OBJECTION = "dramatic_objection"
    SETTLEMENT_INDICATION = "settlement_indication"
    CASE_TURNING_POINT = "case_turning_point"
    CREDIBILITY_ATTACK = "credibility_attack"
    IMPEACHMENT_SUCCESS = "impeachment_success"
    HOSTILE_WITNESS = "hostile_witness"
    EMOTIONAL_TESTIMONY = "emotional_testimony"
    TECHNICAL_KNOCKOUT = "technical_knockout"
    PROCEDURAL_ERROR = "procedural_error"
    JUDICIAL_INTERVENTION = "judicial_intervention"
    ATTORNEY_MISCONDUCT = "attorney_misconduct"
    PERJURY_INDICATION = "perjury_indication"
    PRIVILEGE_ASSERTION = "privilege_assertion"
    CONSTITUTIONAL_ISSUE = "constitutional_issue"
    PRECEDENT_CHALLENGE = "precedent_challenge"


class ImpactLevel(Enum):
    """Impact level of the key moment on the case."""
    CASE_CHANGING = "case_changing"      # Likely to determine case outcome
    HIGHLY_SIGNIFICANT = "highly_significant"  # Major impact on strategy
    SIGNIFICANT = "significant"          # Important for case development
    MODERATE = "moderate"               # Notable but not decisive
    MINOR = "minor"                     # Interesting but minimal impact


class EmotionalTone(Enum):
    """Emotional tone of the moment."""
    DRAMATIC = "dramatic"
    TENSE = "tense"
    HEATED = "heated"
    EMOTIONAL = "emotional"
    SHOCKING = "shocking"
    CONFRONTATIONAL = "confrontational"
    TRIUMPHANT = "triumphant"
    DEFLATING = "deflating"
    NEUTRAL = "neutral"
    HUMOROUS = "humorous"


@dataclass
class KeyMoment:
    """Represents a key moment detected in the transcript."""
    moment_id: str
    moment_type: MomentType
    title: str
    description: str
    transcript_text: str
    speaker: str
    timestamp: float
    duration: float  # Length of the moment in seconds
    impact_level: ImpactLevel
    emotional_tone: EmotionalTone
    confidence: float
    context_before: str
    context_after: str
    participants: List[str]
    legal_significance: str
    strategic_implications: List[str]
    evidence_implications: List[str]
    credibility_impact: Dict[str, float]  # Impact on witness/party credibility
    case_theory_impact: List[str]
    follow_up_questions: List[str]
    related_moments: List[str]  # IDs of related moments
    tags: List[str]
    quotable_excerpts: List[str]
    media_worthy: bool = False
    requires_immediate_action: bool = False


@dataclass
class MomentCluster:
    """Group of related key moments forming a narrative."""
    cluster_id: str
    title: str
    description: str
    moments: List[KeyMoment]
    narrative_arc: str
    overall_impact: ImpactLevel
    time_span: Tuple[float, float]  # Start and end timestamps
    key_participants: List[str]
    legal_theme: str
    strategic_value: str


class KeyMomentDetector:
    """AI-powered detector for identifying key moments in court proceedings."""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.detected_moments: List[KeyMoment] = []
        self.moment_clusters: List[MomentCluster] = []
        
        # Patterns for different types of moments
        self.breakthrough_patterns = [
            r"(?i)\b(?:admit|acknowledge|yes|that's correct|that is true)\b.*\b(?:did|was|were|have)\b",
            r"(?i)\b(?:you're right|that's accurate|i can't deny|i have to admit)\b",
            r"(?i)\b(?:i lied|i was wrong|i made a mistake|i didn't tell the truth)\b"
        ]
        
        self.dramatic_patterns = [
            r"(?i)\b(?:objection|sustained|overruled)\b.*\b(?:your honor|the court)\b",
            r"(?i)\b(?:that's outrageous|this is ridiculous|i can't believe)\b",
            r"(?i)\b(?:you can't be serious|are you kidding me|that's impossible)\b"
        ]
        
        self.credibility_patterns = [
            r"(?i)\b(?:contradicts|inconsistent with|different from what you said)\b",
            r"(?i)\b(?:didn't you say|but you testified|you stated earlier)\b",
            r"(?i)\b(?:impeach|impeachment|prior statement|previous testimony)\b"
        ]

    async def analyze_segment_for_moments(
        self, 
        segment: TranscriptSegment,
        case_context: Optional[Case] = None,
        surrounding_context: Optional[List[TranscriptSegment]] = None
    ) -> List[KeyMoment]:
        """Analyze a transcript segment for key moments."""
        try:
            moments = []
            
            # Get surrounding context for better analysis
            context_before = ""
            context_after = ""
            
            if surrounding_context:
                # Get context from surrounding segments
                current_index = next((i for i, s in enumerate(surrounding_context) 
                                    if s.id == segment.id), -1)
                
                if current_index > 0:
                    context_before = " ".join([s.text for s in surrounding_context[max(0, current_index-3):current_index]])
                
                if current_index < len(surrounding_context) - 1:
                    context_after = " ".join([s.text for s in surrounding_context[current_index+1:current_index+4]])
            
            # Pattern-based initial detection
            potential_moments = self._detect_moment_patterns(segment, context_before, context_after)
            
            # AI-enhanced analysis
            if potential_moments or self._has_moment_indicators(segment.text):
                ai_moments = await self._ai_moment_analysis(
                    segment, context_before, context_after, case_context
                )
                moments.extend(ai_moments)
            
            # Refine and score moments
            refined_moments = await self._refine_moments(moments, case_context)
            
            # Add to detected moments
            self.detected_moments.extend(refined_moments)
            
            return refined_moments
            
        except Exception as e:
            print(f"Error analyzing segment for moments: {e}")
            return []

    def _detect_moment_patterns(
        self, 
        segment: TranscriptSegment,
        context_before: str,
        context_after: str
    ) -> List[KeyMoment]:
        """Use pattern matching to detect potential key moments."""
        potential_moments = []
        text = segment.text
        
        # Check breakthrough admission patterns
        for pattern in self.breakthrough_patterns:
            if re.search(pattern, text):
                moment = KeyMoment(
                    moment_id=f"moment_{segment.id}_{len(potential_moments)}",
                    moment_type=MomentType.BREAKTHROUGH_ADMISSION,
                    title="Potential Breakthrough Admission",
                    description="Pattern detected suggesting admission or acknowledgment",
                    transcript_text=text,
                    speaker=segment.speaker,
                    timestamp=segment.timestamp,
                    duration=segment.duration,
                    impact_level=ImpactLevel.SIGNIFICANT,
                    emotional_tone=EmotionalTone.DRAMATIC,
                    confidence=0.6,  # Will be refined by AI
                    context_before=context_before,
                    context_after=context_after,
                    participants=[segment.speaker],
                    legal_significance="",
                    strategic_implications=[],
                    evidence_implications=[],
                    credibility_impact={},
                    case_theory_impact=[],
                    follow_up_questions=[],
                    related_moments=[],
                    tags=["admission", "breakthrough"],
                    quotable_excerpts=[]
                )
                potential_moments.append(moment)
                break
        
        # Check dramatic moment patterns
        for pattern in self.dramatic_patterns:
            if re.search(pattern, text):
                moment = KeyMoment(
                    moment_id=f"moment_{segment.id}_{len(potential_moments)}",
                    moment_type=MomentType.DRAMATIC_OBJECTION,
                    title="Dramatic Courtroom Exchange",
                    description="Pattern detected suggesting dramatic exchange",
                    transcript_text=text,
                    speaker=segment.speaker,
                    timestamp=segment.timestamp,
                    duration=segment.duration,
                    impact_level=ImpactLevel.MODERATE,
                    emotional_tone=EmotionalTone.DRAMATIC,
                    confidence=0.5,
                    context_before=context_before,
                    context_after=context_after,
                    participants=[segment.speaker],
                    legal_significance="",
                    strategic_implications=[],
                    evidence_implications=[],
                    credibility_impact={},
                    case_theory_impact=[],
                    follow_up_questions=[],
                    related_moments=[],
                    tags=["dramatic", "objection"],
                    quotable_excerpts=[]
                )
                potential_moments.append(moment)
                break
        
        # Check credibility attack patterns
        for pattern in self.credibility_patterns:
            if re.search(pattern, text):
                moment = KeyMoment(
                    moment_id=f"moment_{segment.id}_{len(potential_moments)}",
                    moment_type=MomentType.CREDIBILITY_ATTACK,
                    title="Credibility Challenge",
                    description="Pattern detected suggesting credibility attack",
                    transcript_text=text,
                    speaker=segment.speaker,
                    timestamp=segment.timestamp,
                    duration=segment.duration,
                    impact_level=ImpactLevel.SIGNIFICANT,
                    emotional_tone=EmotionalTone.CONFRONTATIONAL,
                    confidence=0.7,
                    context_before=context_before,
                    context_after=context_after,
                    participants=[segment.speaker],
                    legal_significance="",
                    strategic_implications=[],
                    evidence_implications=[],
                    credibility_impact={},
                    case_theory_impact=[],
                    follow_up_questions=[],
                    related_moments=[],
                    tags=["credibility", "impeachment"],
                    quotable_excerpts=[]
                )
                potential_moments.append(moment)
                break
        
        return potential_moments

    def _has_moment_indicators(self, text: str) -> bool:
        """Check if text has indicators suggesting a key moment."""
        text_lower = text.lower()
        
        moment_indicators = [
            "objection", "sustained", "overruled", "sidebar", "approach",
            "smoking gun", "gotcha", "contradiction", "inconsistent",
            "perjury", "lie", "truth", "admit", "deny", "confess",
            "revelation", "surprise", "shocking", "dramatic", "explosive",
            "breakthrough", "game changer", "turning point", "crucial",
            "settlement", "plea", "deal", "negotiate", "dismiss"
        ]
        
        return any(indicator in text_lower for indicator in moment_indicators)

    async def _ai_moment_analysis(
        self,
        segment: TranscriptSegment,
        context_before: str,
        context_after: str,
        case_context: Optional[Case]
    ) -> List[KeyMoment]:
        """Use AI to analyze the segment for key moments."""
        try:
            context_info = ""
            if case_context:
                context_info = f"""
                Case Context:
                - Title: {case_context.title}
                - Type: {case_context.case_type}
                - Status: {case_context.status}
                - Key Issues: {', '.join(case_context.key_issues or [])}
                """
            
            prompt = f"""
            Analyze this court transcript segment for key moments, breakthrough statements, and significant developments.
            
            Speaker: {segment.speaker}
            Text: {segment.text}
            Context Before: {context_before}
            Context After: {context_after}
            {context_info}
            
            Identify any key moments such as:
            1. Breakthrough admissions or revelations
            2. Smoking gun evidence introduction
            3. Witness credibility attacks or breakdowns
            4. Expert contradictions or technical knockouts
            5. Dramatic objections or confrontations
            6. Settlement indications or case turning points
            7. Surprise developments or shocking revelations
            8. Emotional or highly significant testimony
            9. Judicial interventions or rulings
            10. Procedural errors or attorney misconduct
            
            For each key moment found, analyze:
            - Type and significance level
            - Impact on case outcome (case-changing to minor)
            - Emotional tone and drama level
            - Legal and strategic implications
            - Effect on witness/party credibility
            - Quotable excerpts for media or briefs
            - Follow-up questions or actions needed
            - Connection to case theories
            
            Return as JSON:
            {{
                "moments": [
                    {{
                        "type": "breakthrough_admission|smoking_gun_evidence|witness_breakdown|etc",
                        "title": "Brief descriptive title",
                        "description": "Detailed description of what happened",
                        "impact_level": "case_changing|highly_significant|significant|moderate|minor",
                        "emotional_tone": "dramatic|tense|shocking|confrontational|etc",
                        "confidence": 0.85,
                        "participants": ["speaker1", "speaker2"],
                        "legal_significance": "Analysis of legal importance",
                        "strategic_implications": ["implication1", "implication2"],
                        "evidence_implications": ["evidence impact1", "evidence impact2"],
                        "credibility_impact": {{"witness_name": 0.7, "party_name": -0.3}},
                        "case_theory_impact": ["impact on theory1", "impact on theory2"],
                        "follow_up_questions": ["question1", "question2"],
                        "tags": ["tag1", "tag2", "tag3"],
                        "quotable_excerpts": ["quote1", "quote2"],
                        "media_worthy": true,
                        "requires_immediate_action": false
                    }}
                ]
            }}
            """
            
            response = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.2,
                max_tokens=2500
            )
            
            ai_data = json.loads(response)
            moments = []
            
            for i, moment_data in enumerate(ai_data.get("moments", [])):
                try:
                    moment_type = MomentType(moment_data.get("type", "key_testimony"))
                    impact_level = ImpactLevel(moment_data.get("impact_level", "moderate"))
                    emotional_tone = EmotionalTone(moment_data.get("emotional_tone", "neutral"))
                    
                    moment = KeyMoment(
                        moment_id=f"ai_moment_{segment.id}_{i}",
                        moment_type=moment_type,
                        title=moment_data.get("title", "Key Moment"),
                        description=moment_data.get("description", ""),
                        transcript_text=segment.text,
                        speaker=segment.speaker,
                        timestamp=segment.timestamp,
                        duration=segment.duration,
                        impact_level=impact_level,
                        emotional_tone=emotional_tone,
                        confidence=moment_data.get("confidence", 0.5),
                        context_before=context_before,
                        context_after=context_after,
                        participants=moment_data.get("participants", [segment.speaker]),
                        legal_significance=moment_data.get("legal_significance", ""),
                        strategic_implications=moment_data.get("strategic_implications", []),
                        evidence_implications=moment_data.get("evidence_implications", []),
                        credibility_impact=moment_data.get("credibility_impact", {}),
                        case_theory_impact=moment_data.get("case_theory_impact", []),
                        follow_up_questions=moment_data.get("follow_up_questions", []),
                        related_moments=[],
                        tags=moment_data.get("tags", []),
                        quotable_excerpts=moment_data.get("quotable_excerpts", []),
                        media_worthy=moment_data.get("media_worthy", False),
                        requires_immediate_action=moment_data.get("requires_immediate_action", False)
                    )
                    
                    moments.append(moment)
                    
                except (ValueError, KeyError) as e:
                    print(f"Error processing AI moment data: {e}")
                    continue
            
            return moments
            
        except Exception as e:
            print(f"Error in AI moment analysis: {e}")
            return []

    async def _refine_moments(
        self, 
        moments: List[KeyMoment],
        case_context: Optional[Case]
    ) -> List[KeyMoment]:
        """Refine and validate detected moments."""
        refined_moments = []
        
        for moment in moments:
            # Filter low-confidence moments
            if moment.confidence < 0.4:
                continue
            
            # Enhance moment with additional analysis
            enhanced_moment = await self._enhance_moment(moment, case_context)
            refined_moments.append(enhanced_moment)
        
        return refined_moments

    async def _enhance_moment(
        self, 
        moment: KeyMoment,
        case_context: Optional[Case]
    ) -> KeyMoment:
        """Enhance a moment with additional context and analysis."""
        try:
            # Generate quotable excerpts if not present
            if not moment.quotable_excerpts:
                moment.quotable_excerpts = self._extract_quotable_excerpts(moment.transcript_text)
            
            # Determine media worthiness
            if not moment.media_worthy:
                moment.media_worthy = self._assess_media_worthiness(moment)
            
            # Check for immediate action requirements
            moment.requires_immediate_action = self._requires_immediate_action(moment)
            
            return moment
            
        except Exception as e:
            print(f"Error enhancing moment: {e}")
            return moment

    def _extract_quotable_excerpts(self, text: str) -> List[str]:
        """Extract quotable excerpts from transcript text."""
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        quotable = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Too short
                continue
            if len(sentence) > 200:  # Too long
                continue
            
            # Look for dramatic or significant statements
            if any(word in sentence.lower() for word in [
                "admit", "acknowledge", "deny", "lie", "truth", "never", "always",
                "shocking", "unbelievable", "impossible", "absolutely", "completely"
            ]):
                quotable.append(sentence)
        
        return quotable[:3]  # Return top 3

    def _assess_media_worthiness(self, moment: KeyMoment) -> bool:
        """Assess if a moment is worthy of media attention."""
        media_indicators = [
            moment.impact_level in [ImpactLevel.CASE_CHANGING, ImpactLevel.HIGHLY_SIGNIFICANT],
            moment.emotional_tone in [EmotionalTone.DRAMATIC, EmotionalTone.SHOCKING],
            moment.moment_type in [
                MomentType.BREAKTHROUGH_ADMISSION, MomentType.SMOKING_GUN_EVIDENCE,
                MomentType.WITNESS_BREAKDOWN, MomentType.SURPRISE_REVELATION
            ],
            len(moment.quotable_excerpts) > 0,
            moment.confidence > 0.8
        ]
        
        return sum(media_indicators) >= 2

    def _requires_immediate_action(self, moment: KeyMoment) -> bool:
        """Determine if the moment requires immediate legal action."""
        immediate_action_indicators = [
            moment.moment_type in [
                MomentType.PERJURY_INDICATION, MomentType.ATTORNEY_MISCONDUCT,
                MomentType.PROCEDURAL_ERROR, MomentType.CONSTITUTIONAL_ISSUE
            ],
            moment.impact_level == ImpactLevel.CASE_CHANGING,
            "sanction" in moment.legal_significance.lower(),
            "contempt" in moment.legal_significance.lower(),
            "mistrial" in moment.legal_significance.lower()
        ]
        
        return any(immediate_action_indicators)

    async def create_moment_clusters(
        self, 
        moments: List[KeyMoment],
        time_window: float = 300.0  # 5 minutes
    ) -> List[MomentCluster]:
        """Group related moments into narrative clusters."""
        try:
            clusters = []
            processed_moments = set()
            
            for moment in moments:
                if moment.moment_id in processed_moments:
                    continue
                
                # Find related moments within time window
                related_moments = [moment]
                processed_moments.add(moment.moment_id)
                
                for other_moment in moments:
                    if (other_moment.moment_id not in processed_moments and
                        abs(other_moment.timestamp - moment.timestamp) <= time_window):
                        
                        # Check for thematic relationship
                        if self._are_moments_related(moment, other_moment):
                            related_moments.append(other_moment)
                            processed_moments.add(other_moment.moment_id)
                
                # Create cluster if multiple related moments
                if len(related_moments) > 1:
                    cluster = await self._create_cluster(related_moments)
                    clusters.append(cluster)
            
            self.moment_clusters.extend(clusters)
            return clusters
            
        except Exception as e:
            print(f"Error creating moment clusters: {e}")
            return []

    def _are_moments_related(self, moment1: KeyMoment, moment2: KeyMoment) -> bool:
        """Check if two moments are thematically related."""
        # Check for common participants
        common_participants = set(moment1.participants) & set(moment2.participants)
        if common_participants:
            return True
        
        # Check for common tags
        common_tags = set(moment1.tags) & set(moment2.tags)
        if len(common_tags) >= 2:
            return True
        
        # Check for related moment types
        related_types = [
            [MomentType.CREDIBILITY_ATTACK, MomentType.IMPEACHMENT_SUCCESS],
            [MomentType.EXPERT_CONTRADICTION, MomentType.TECHNICAL_KNOCKOUT],
            [MomentType.BREAKTHROUGH_ADMISSION, MomentType.SMOKING_GUN_EVIDENCE],
            [MomentType.SETTLEMENT_INDICATION, MomentType.CASE_TURNING_POINT]
        ]
        
        for type_group in related_types:
            if moment1.moment_type in type_group and moment2.moment_type in type_group:
                return True
        
        return False

    async def _create_cluster(self, moments: List[KeyMoment]) -> MomentCluster:
        """Create a moment cluster from related moments."""
        timestamps = [m.timestamp for m in moments]
        time_span = (min(timestamps), max(timestamps))
        
        # Determine overall impact
        impact_levels = [m.impact_level for m in moments]
        overall_impact = max(impact_levels, key=lambda x: [
            ImpactLevel.CASE_CHANGING, ImpactLevel.HIGHLY_SIGNIFICANT,
            ImpactLevel.SIGNIFICANT, ImpactLevel.MODERATE, ImpactLevel.MINOR
        ].index(x))
        
        # Get key participants
        all_participants = set()
        for moment in moments:
            all_participants.update(moment.participants)
        
        # Generate narrative description
        narrative_arc = await self._generate_narrative_arc(moments)
        
        cluster_id = f"cluster_{int(datetime.now().timestamp())}_{len(self.moment_clusters)}"
        
        return MomentCluster(
            cluster_id=cluster_id,
            title=f"Key Development: {moments[0].title}",
            description=f"Series of {len(moments)} related moments",
            moments=moments,
            narrative_arc=narrative_arc,
            overall_impact=overall_impact,
            time_span=time_span,
            key_participants=list(all_participants),
            legal_theme=self._identify_legal_theme(moments),
            strategic_value=self._assess_strategic_value(moments)
        )

    async def _generate_narrative_arc(self, moments: List[KeyMoment]) -> str:
        """Generate a narrative description of the moment sequence."""
        try:
            moment_summaries = []
            for moment in sorted(moments, key=lambda x: x.timestamp):
                summary = f"{moment.speaker}: {moment.title} - {moment.description}"
                moment_summaries.append(summary)
            
            prompt = f"""
            Create a compelling narrative arc describing this sequence of key courtroom moments:
            
            {chr(10).join(moment_summaries)}
            
            Write a 2-3 sentence narrative that captures the drama and legal significance
            of this sequence. Focus on the story arc and its implications for the case.
            """
            
            response = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.3,
                max_tokens=200
            )
            
            return response.strip()
            
        except Exception as e:
            print(f"Error generating narrative arc: {e}")
            return f"Sequence of {len(moments)} related courtroom moments"

    def _identify_legal_theme(self, moments: List[KeyMoment]) -> str:
        """Identify the overarching legal theme of the moment cluster."""
        all_tags = []
        for moment in moments:
            all_tags.extend(moment.tags)
        
        # Count tag frequency
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Get most common tags
        common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        if common_tags:
            return ", ".join([tag for tag, count in common_tags])
        
        return "General Legal Development"

    def _assess_strategic_value(self, moments: List[KeyMoment]) -> str:
        """Assess the strategic value of the moment cluster."""
        high_impact_count = sum(1 for m in moments if m.impact_level in [
            ImpactLevel.CASE_CHANGING, ImpactLevel.HIGHLY_SIGNIFICANT
        ])
        
        if high_impact_count >= 2:
            return "Potentially case-defining sequence with multiple high-impact moments"
        elif high_impact_count == 1:
            return "Significant development with important strategic implications"
        else:
            return "Notable sequence that may influence case strategy"

    def get_moments_summary(
        self, 
        case_id: Optional[str] = None,
        time_range: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """Get a summary of detected key moments."""
        filtered_moments = self.detected_moments
        
        if case_id:
            # Filter would require case_id to be stored in moments
            pass
        
        if time_range:
            start_time, end_time = time_range
            filtered_moments = [
                m for m in filtered_moments
                if start_time <= m.timestamp <= end_time
            ]
        
        # Categorize moments
        moment_counts = {}
        for moment_type in MomentType:
            moment_counts[moment_type.value] = sum(
                1 for m in filtered_moments if m.moment_type == moment_type
            )
        
        # Impact distribution
        impact_counts = {}
        for impact_level in ImpactLevel:
            impact_counts[impact_level.value] = sum(
                1 for m in filtered_moments if m.impact_level == impact_level
            )
        
        # Top moments by impact
        top_moments = sorted(
            filtered_moments,
            key=lambda x: ([ImpactLevel.CASE_CHANGING, ImpactLevel.HIGHLY_SIGNIFICANT,
                           ImpactLevel.SIGNIFICANT, ImpactLevel.MODERATE, ImpactLevel.MINOR]
                          .index(x.impact_level), -x.confidence)
        )[:10]
        
        return {
            "total_moments": len(filtered_moments),
            "moment_type_counts": moment_counts,
            "impact_level_counts": impact_counts,
            "total_clusters": len(self.moment_clusters),
            "media_worthy_moments": sum(1 for m in filtered_moments if m.media_worthy),
            "immediate_action_moments": sum(1 for m in filtered_moments if m.requires_immediate_action),
            "top_moments": [
                {
                    "moment_id": m.moment_id,
                    "title": m.title,
                    "type": m.moment_type.value,
                    "impact_level": m.impact_level.value,
                    "timestamp": m.timestamp,
                    "confidence": m.confidence
                }
                for m in top_moments
            ]
        }