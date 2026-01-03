"""
Legal analysis engine for court transcripts.

Analyzes transcript content for legal insights, objections, evidence,
key moments, and other legally significant events and patterns.
"""

import asyncio
import re
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum

from ..shared.utils import BaseAPIClient
from .models import (
    SpeakerType, LegalEvent, EventType, generate_event_id,
    CourtRole
)


class ObjectionType(Enum):
    """Types of legal objections."""
    HEARSAY = "hearsay"
    RELEVANCE = "relevance"
    FOUNDATION = "foundation"
    LEADING = "leading"
    COMPOUND = "compound"
    ARGUMENTATIVE = "argumentative"
    ASSUMES_FACTS = "assumes_facts"
    SPECULATION = "speculation"
    NARRATIVE = "narrative"
    NON_RESPONSIVE = "non_responsive"
    VAGUE = "vague"
    AMBIGUOUS = "ambiguous"
    CUMULATIVE = "cumulative"
    PREJUDICIAL = "prejudicial"
    OTHER = "other"


class EvidenceType(Enum):
    """Types of evidence being introduced."""
    DOCUMENT = "document"
    EXHIBIT = "exhibit"
    PHOTOGRAPH = "photograph"
    VIDEO = "video"
    AUDIO = "audio"
    PHYSICAL_EVIDENCE = "physical_evidence"
    TESTIMONY = "testimony"
    EXPERT_OPINION = "expert_opinion"
    DEMONSTRATIVE = "demonstrative"
    OTHER = "other"


@dataclass
class LegalInsight:
    """Legal insight detected from transcript."""
    insight_id: str
    insight_type: str
    description: str
    confidence: float
    
    # Context
    text_excerpt: str
    speaker_id: Optional[str] = None
    speaker_type: Optional[SpeakerType] = None
    
    # Legal analysis
    legal_significance: int = 1  # 1-10 scale
    potential_impact: str = "low"  # low, medium, high, critical
    legal_precedents: List[str] = field(default_factory=list)
    
    # Recommendations
    suggested_actions: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    
    # Metadata
    detected_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    
    def to_legal_event(self) -> LegalEvent:
        """Convert to LegalEvent for broadcasting."""
        event_type_map = {
            "objection": EventType.OBJECTION,
            "ruling": EventType.RULING,
            "evidence": EventType.EVIDENCE_INTRODUCTION,
            "key_testimony": EventType.KEY_TESTIMONY,
            "motion": EventType.MOTION,
            "sidebar": EventType.SIDEBAR,
            "recess": EventType.RECESS
        }
        
        return LegalEvent(
            event_id=self.insight_id,
            event_type=event_type_map.get(self.insight_type, EventType.KEY_TESTIMONY),
            description=self.description,
            transcript_excerpt=self.text_excerpt,
            speaker_id=self.speaker_id,
            speaker_type=self.speaker_type,
            confidence=self.confidence,
            significance=self.legal_significance,
            legal_implications=self.suggested_actions,
            tags=self.tags,
            detected_by="legal_analyzer"
        )


@dataclass
class ObjectionEvent:
    """Objection event with analysis."""
    objection_id: str
    objection_type: ObjectionType
    objecting_party: Optional[str]
    target_speaker: Optional[str]
    
    # Content
    objection_text: str
    questioned_content: str
    
    # Outcome
    ruling: Optional[str] = None  # sustained, overruled, taken_under_advisement
    judge_explanation: Optional[str] = None
    
    # Analysis
    merit_assessment: Optional[str] = None  # strong, weak, unclear
    strategic_significance: int = 1  # 1-10
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ruling_timestamp: Optional[datetime] = None
    
    # Context
    examination_phase: Optional[str] = None  # direct, cross, redirect, recross
    witness_type: Optional[str] = None


@dataclass
class EvidenceEvent:
    """Evidence introduction event."""
    evidence_id: str
    evidence_type: EvidenceType
    exhibit_number: Optional[str]
    
    # Description
    description: str
    offered_by: Optional[str] = None
    
    # Status
    status: str = "offered"  # offered, admitted, rejected, pending
    objections: List[str] = field(default_factory=list)
    
    # Analysis
    relevance_assessment: Optional[str] = None
    authenticity_issues: List[str] = field(default_factory=list)
    strategic_value: int = 1  # 1-10
    
    # Timing
    offered_at: datetime = field(default_factory=datetime.utcnow)
    ruled_at: Optional[datetime] = None


class ObjectionTracker:
    """Tracks objections and rulings throughout proceedings."""
    
    def __init__(self):
        self.objections: Dict[str, ObjectionEvent] = {}
        self.objection_patterns = self._compile_objection_patterns()
        self.ruling_patterns = self._compile_ruling_patterns()
        
    def _compile_objection_patterns(self) -> Dict[ObjectionType, List[re.Pattern]]:
        """Compile patterns for objection detection."""
        return {
            ObjectionType.HEARSAY: [
                re.compile(r'\bhearsay\b', re.IGNORECASE),
                re.compile(r'\bcalls?\s+for\s+hearsay\b', re.IGNORECASE)
            ],
            ObjectionType.RELEVANCE: [
                re.compile(r'\brelevance\b', re.IGNORECASE),
                re.compile(r'\birrelevant\b', re.IGNORECASE),
                re.compile(r'\bnot\s+relevant\b', re.IGNORECASE)
            ],
            ObjectionType.FOUNDATION: [
                re.compile(r'\bfoundation\b', re.IGNORECASE),
                re.compile(r'\blacks?\s+foundation\b', re.IGNORECASE),
                re.compile(r'\bno\s+foundation\b', re.IGNORECASE)
            ],
            ObjectionType.LEADING: [
                re.compile(r'\bleading\b', re.IGNORECASE),
                re.compile(r'\bleading\s+(?:the\s+)?witness\b', re.IGNORECASE),
                re.compile(r'\bleading\s+question\b', re.IGNORECASE)
            ],
            ObjectionType.COMPOUND: [
                re.compile(r'\bcompound\b', re.IGNORECASE),
                re.compile(r'\bcompound\s+question\b', re.IGNORECASE)
            ],
            ObjectionType.ARGUMENTATIVE: [
                re.compile(r'\bargumentative\b', re.IGNORECASE),
                re.compile(r'\barguing\s+with\s+(?:the\s+)?witness\b', re.IGNORECASE)
            ],
            ObjectionType.ASSUMES_FACTS: [
                re.compile(r'\bassumes?\s+facts?\b', re.IGNORECASE),
                re.compile(r'\bassumes?\s+facts?\s+not\s+in\s+evidence\b', re.IGNORECASE)
            ],
            ObjectionType.SPECULATION: [
                re.compile(r'\bspeculat\w*\b', re.IGNORECASE),
                re.compile(r'\bcalls?\s+for\s+speculation\b', re.IGNORECASE),
                re.compile(r'\basking?\s+(?:him|her|them)\s+to\s+speculate\b', re.IGNORECASE)
            ],
            ObjectionType.NARRATIVE: [
                re.compile(r'\bnarrative\b', re.IGNORECASE),
                re.compile(r'\bcalls?\s+for\s+(?:a\s+)?narrative\b', re.IGNORECASE)
            ],
            ObjectionType.NON_RESPONSIVE: [
                re.compile(r'\bnon.?responsive\b', re.IGNORECASE),
                re.compile(r'\bnot\s+responsive\b', re.IGNORECASE),
                re.compile(r'\bmove\s+to\s+strike\s+as\s+non.?responsive\b', re.IGNORECASE)
            ],
            ObjectionType.VAGUE: [
                re.compile(r'\bvague\b', re.IGNORECASE),
                re.compile(r'\bambiguous\b', re.IGNORECASE),
                re.compile(r'\bvague\s+and\s+ambiguous\b', re.IGNORECASE)
            ]
        }
    
    def _compile_ruling_patterns(self) -> Dict[str, re.Pattern]:
        """Compile patterns for ruling detection.""" 
        return {
            "sustained": re.compile(r'\bsustained\b', re.IGNORECASE),
            "overruled": re.compile(r'\boverruled\b', re.IGNORECASE),
            "taken_under_advisement": re.compile(r'\btaken\s+under\s+advisement\b', re.IGNORECASE)
        }
    
    def detect_objection(self, text: str, speaker_id: Optional[str] = None) -> Optional[ObjectionEvent]:
        """Detect objection in text."""
        # Look for the word "objection" first
        if not re.search(r'\bobjection\b', text, re.IGNORECASE):
            return None
        
        # Determine objection type
        objection_type = ObjectionType.OTHER
        for obj_type, patterns in self.objection_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    objection_type = obj_type
                    break
            if objection_type != ObjectionType.OTHER:
                break
        
        # Create objection event
        objection = ObjectionEvent(
            objection_id=generate_event_id(),
            objection_type=objection_type,
            objecting_party=speaker_id,
            objection_text=text.strip(),
            questioned_content="",  # Would be filled from context
            strategic_significance=5  # Default medium significance
        )
        
        self.objections[objection.objection_id] = objection
        return objection
    
    def detect_ruling(self, text: str, pending_objections: List[str]) -> Optional[Tuple[str, str]]:
        """Detect ruling on pending objections."""
        for ruling_type, pattern in self.ruling_patterns.items():
            if pattern.search(text):
                # Find most recent pending objection
                if pending_objections:
                    objection_id = pending_objections[-1]
                    objection = self.objections.get(objection_id)
                    if objection:
                        objection.ruling = ruling_type
                        objection.ruling_timestamp = datetime.utcnow()
                        objection.judge_explanation = text.strip()
                    return objection_id, ruling_type
        return None


class EvidenceTracker:
    """Tracks evidence introduction and admission."""
    
    def __init__(self):
        self.evidence: Dict[str, EvidenceEvent] = {}
        self.exhibit_patterns = self._compile_exhibit_patterns()
        
    def _compile_exhibit_patterns(self) -> Dict[str, re.Pattern]:
        """Compile patterns for evidence detection."""
        return {
            "mark_for_identification": re.compile(
                r'\bmark(?:ed|ing)?\s+(?:this\s+)?(?:as\s+)?(?:exhibit\s+)?([a-z0-9]+)\s+for\s+identification\b',
                re.IGNORECASE
            ),
            "move_into_evidence": re.compile(
                r'\bmove\s+(?:exhibit\s+)?([a-z0-9]+)\s+into\s+evidence\b',
                re.IGNORECASE
            ),
            "offer_exhibit": re.compile(
                r'\boffer\s+(?:exhibit\s+)?([a-z0-9]+)(?:\s+into\s+evidence)?\b',
                re.IGNORECASE
            ),
            "admit_exhibit": re.compile(
                r'\b(?:exhibit\s+)?([a-z0-9]+)\s+is\s+(?:admitted|received)\b',
                re.IGNORECASE
            ),
            "exhibit_reference": re.compile(
                r'\bexhibit\s+([a-z0-9]+)\b',
                re.IGNORECASE
            )
        }
    
    def detect_evidence_event(self, text: str, speaker_id: Optional[str] = None) -> Optional[EvidenceEvent]:
        """Detect evidence-related events."""
        # Look for exhibit patterns
        for pattern_name, pattern in self.exhibit_patterns.items():
            match = pattern.search(text)
            if match:
                exhibit_number = match.group(1) if match.groups() else None
                
                # Determine evidence type and status
                if "mark" in pattern_name:
                    status = "marked"
                elif "move" in pattern_name or "offer" in pattern_name:
                    status = "offered"
                elif "admit" in pattern_name:
                    status = "admitted"
                else:
                    status = "referenced"
                
                evidence = EvidenceEvent(
                    evidence_id=generate_event_id(),
                    evidence_type=EvidenceType.EXHIBIT,
                    exhibit_number=exhibit_number,
                    description=text.strip(),
                    offered_by=speaker_id,
                    status=status,
                    strategic_value=5  # Default medium value
                )
                
                self.evidence[evidence.evidence_id] = evidence
                return evidence
        
        return None


class LegalAnalyzer:
    """Advanced legal analysis engine for court transcripts."""
    
    def __init__(self, api_client: Optional[BaseAPIClient] = None):
        self.api_client = api_client
        
        # Sub-analyzers
        self.objection_tracker = ObjectionTracker()
        self.evidence_tracker = EvidenceTracker()
        
        # Analysis patterns
        self.legal_patterns = self._compile_legal_patterns()
        self.procedural_patterns = self._compile_procedural_patterns()
        self.key_moment_patterns = self._compile_key_moment_patterns()
        
        # State tracking
        self.session_state: Dict[str, Dict[str, Any]] = {}
        self.pending_objections: Dict[str, List[str]] = defaultdict(list)
        
        # Legal knowledge base
        self.legal_concepts = self._load_legal_concepts()
        self.procedural_rules = self._load_procedural_rules()
        
        # Statistics
        self.total_analyzed = 0
        self.insights_generated = 0
        self.objections_detected = 0
        self.evidence_tracked = 0
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def _compile_legal_patterns(self) -> Dict[str, re.Pattern]:
        """Compile patterns for legal concept detection."""
        return {
            "motion": re.compile(
                r'\bmotion\s+(?:for|to)\s+(?:dismiss|compel|strike|summary\s+judgment|suppress|exclude|in\s+limine)\b',
                re.IGNORECASE
            ),
            "burden_of_proof": re.compile(
                r'\bburden\s+of\s+proof\b|\bpreponderance\s+of\s+(?:the\s+)?evidence\b|\bbeyond\s+(?:a\s+)?reasonable\s+doubt\b',
                re.IGNORECASE
            ),
            "constitutional_issue": re.compile(
                r'\bconstitutional\b|\bfourth\s+amendment\b|\bfifth\s+amendment\b|\bdue\s+process\b|\bequal\s+protection\b',
                re.IGNORECASE
            ),
            "privilege": re.compile(
                r'\battorney.?client\s+privilege\b|\bwork\s+product\b|\bphysician.?patient\s+privilege\b|\bspouse\s+privilege\b',
                re.IGNORECASE
            ),
            "damages": re.compile(
                r'\b(?:actual|compensatory|punitive|exemplary|liquidated)\s+damages\b|\brestitution\b|\binjunctive\s+relief\b',
                re.IGNORECASE
            ),
            "settlement": re.compile(
                r'\bsettlement\b|\bmediation\b|\barbitration\b|\bpleabargain\b|\bplea\s+agreement\b',
                re.IGNORECASE
            )
        }
    
    def _compile_procedural_patterns(self) -> Dict[str, re.Pattern]:
        """Compile patterns for procedural events."""
        return {
            "sidebar": re.compile(r'\bsidebar\b|\bapproach\s+(?:the\s+)?bench\b', re.IGNORECASE),
            "recess": re.compile(r'\brecess\b|\bbreak\b|\badjourn\b', re.IGNORECASE),
            "jury_instruction": re.compile(r'\bjury\s+instruction\b|\binstruct\s+the\s+jury\b', re.IGNORECASE),
            "voir_dire": re.compile(r'\bvoir\s+dire\b', re.IGNORECASE),
            "opening_statement": re.compile(r'\bopening\s+statement\b', re.IGNORECASE),
            "closing_argument": re.compile(r'\bclosing\s+argument\b|\bclosing\s+statement\b', re.IGNORECASE),
            "direct_examination": re.compile(r'\bdirect\s+examination\b', re.IGNORECASE),
            "cross_examination": re.compile(r'\bcross.?examination\b', re.IGNORECASE),
            "redirect": re.compile(r'\bredirect\s+examination\b', re.IGNORECASE),
            "recross": re.compile(r'\brecross.?examination\b', re.IGNORECASE)
        }
    
    def _compile_key_moment_patterns(self) -> Dict[str, re.Pattern]:
        """Compile patterns for identifying key moments."""
        return {
            "admission": re.compile(
                r'\bi\s+admit\b|\bi\s+acknowledge\b|\bthat.s\s+correct\b|\byes,?\s+i\s+did\b',
                re.IGNORECASE
            ),
            "denial": re.compile(
                r'\bi\s+deny\b|\bthat.s\s+not\s+true\b|\bi\s+did\s+not\b|\bno,?\s+i\s+didn.t\b',
                re.IGNORECASE
            ),
            "impeachment": re.compile(
                r'\bdid\s+you\s+not\s+say\b|\bisn.t\s+it\s+true\s+that\b|\byour\s+testimony\s+today\s+differs\b',
                re.IGNORECASE
            ),
            "credibility_challenge": re.compile(
                r'\bare\s+you\s+lying\b|\bisn.t\s+that\s+convenient\b|\bhow\s+convenient\b',
                re.IGNORECASE
            ),
            "expert_opinion": re.compile(
                r'\bin\s+my\s+(?:professional\s+)?opinion\b|\bbased\s+on\s+my\s+(?:training|experience)\b',
                re.IGNORECASE
            ),
            "emotional_moment": re.compile(
                r'\b(?:crying|sobbing|shouting|emotional|breakdown)\b',
                re.IGNORECASE
            )
        }
    
    def _load_legal_concepts(self) -> Dict[str, Dict[str, Any]]:
        """Load legal concepts knowledge base."""
        return {
            "hearsay": {
                "definition": "An out-of-court statement offered to prove the truth of the matter asserted",
                "exceptions": ["present sense impression", "excited utterance", "business records"],
                "significance": 8
            },
            "relevance": {
                "definition": "Evidence having tendency to make existence of fact more or less probable",
                "test": "Federal Rule of Evidence 401",
                "significance": 9
            },
            "foundation": {
                "definition": "Preliminary proof required to establish admissibility of evidence",
                "requirements": ["authenticity", "relevance", "reliability"],
                "significance": 7
            }
        }
    
    def _load_procedural_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load procedural rules knowledge base."""
        return {
            "objection_timing": {
                "rule": "Objections must be timely made",
                "consequence": "Waiver of objection if not made",
                "exceptions": ["plain error", "jurisdictional issues"]
            },
            "leading_questions": {
                "rule": "Leading questions generally not allowed on direct examination",
                "exceptions": ["hostile witness", "preliminary matters", "expert witness"],
                "significance": 6
            }
        }
    
    async def analyze_segment(self,
                            text: str,
                            context: str,
                            speaker_id: Optional[str] = None,
                            speaker_type: Optional[SpeakerType] = None,
                            session_id: Optional[str] = None) -> List[LegalInsight]:
        """
        Analyze transcript segment for legal insights.
        
        Args:
            text: Transcript segment text
            context: Context from previous segments
            speaker_id: Speaker identifier
            speaker_type: Type of speaker
            session_id: Session identifier
            
        Returns:
            List of legal insights detected
        """
        insights = []
        
        try:
            # Initialize session state if needed
            if session_id and session_id not in self.session_state:
                self.session_state[session_id] = {
                    "examination_phase": "unknown",
                    "current_witness": None,
                    "proceedings_stage": "unknown"
                }
            
            # Detect objections
            objection_insight = await self._analyze_objections(text, speaker_id, session_id)
            if objection_insight:
                insights.append(objection_insight)
            
            # Detect evidence events
            evidence_insight = await self._analyze_evidence(text, speaker_id, session_id)
            if evidence_insight:
                insights.append(evidence_insight)
            
            # Detect procedural events
            procedural_insights = await self._analyze_procedural_events(text, speaker_id, session_id)
            insights.extend(procedural_insights)
            
            # Detect key moments
            key_moment_insights = await self._analyze_key_moments(text, context, speaker_id, speaker_type)
            insights.extend(key_moment_insights)
            
            # AI-powered deep analysis
            if self.api_client and len(text.split()) > 10:  # Only for substantial content
                ai_insights = await self._perform_ai_analysis(text, context, speaker_type)
                insights.extend(ai_insights)
            
            # Update statistics
            self.total_analyzed += 1
            self.insights_generated += len(insights)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error analyzing segment: {e}")
            return []
    
    async def _analyze_objections(self,
                                text: str,
                                speaker_id: Optional[str],
                                session_id: Optional[str]) -> Optional[LegalInsight]:
        """Analyze text for objections and rulings."""
        # Detect objection
        objection = self.objection_tracker.detect_objection(text, speaker_id)
        if objection:
            self.objections_detected += 1
            
            # Add to pending objections for this session
            if session_id:
                self.pending_objections[session_id].append(objection.objection_id)
            
            # Assess objection merit
            merit = await self._assess_objection_merit(objection, text)
            objection.merit_assessment = merit
            
            return LegalInsight(
                insight_id=objection.objection_id,
                insight_type="objection",
                description=f"{objection.objection_type.value.title()} objection raised",
                confidence=0.9,
                text_excerpt=text,
                speaker_id=speaker_id,
                legal_significance=objection.strategic_significance,
                potential_impact="medium",
                suggested_actions=[
                    f"Review {objection.objection_type.value} objection merit",
                    "Prepare response or alternative approach"
                ],
                tags=["objection", objection.objection_type.value]
            )
        
        # Detect ruling
        if session_id:
            ruling_result = self.objection_tracker.detect_ruling(text, self.pending_objections[session_id])
            if ruling_result:
                objection_id, ruling_type = ruling_result
                
                # Remove from pending
                if objection_id in self.pending_objections[session_id]:
                    self.pending_objections[session_id].remove(objection_id)
                
                return LegalInsight(
                    insight_id=generate_event_id(),
                    insight_type="ruling",
                    description=f"Objection {ruling_type}",
                    confidence=0.95,
                    text_excerpt=text,
                    speaker_id=speaker_id,
                    legal_significance=7,
                    potential_impact="medium",
                    tags=["ruling", ruling_type]
                )
        
        return None
    
    async def _analyze_evidence(self,
                              text: str,
                              speaker_id: Optional[str],
                              session_id: Optional[str]) -> Optional[LegalInsight]:
        """Analyze text for evidence introduction."""
        evidence = self.evidence_tracker.detect_evidence_event(text, speaker_id)
        if evidence:
            self.evidence_tracked += 1
            
            return LegalInsight(
                insight_id=evidence.evidence_id,
                insight_type="evidence",
                description=f"Evidence {evidence.status}: {evidence.exhibit_number or 'document'}",
                confidence=0.85,
                text_excerpt=text,
                speaker_id=speaker_id,
                legal_significance=evidence.strategic_value,
                potential_impact="medium",
                suggested_actions=[
                    "Review evidence for relevance and authenticity",
                    "Prepare foundation questions if needed"
                ],
                tags=["evidence", evidence.evidence_type.value, evidence.status]
            )
        
        return None
    
    async def _analyze_procedural_events(self,
                                       text: str,
                                       speaker_id: Optional[str],
                                       session_id: Optional[str]) -> List[LegalInsight]:
        """Analyze text for procedural events."""
        insights = []
        
        for event_type, pattern in self.procedural_patterns.items():
            if pattern.search(text):
                # Update session state for examination phases
                if session_id and session_id in self.session_state:
                    if event_type in ["direct_examination", "cross_examination", "redirect", "recross"]:
                        self.session_state[session_id]["examination_phase"] = event_type
                
                insight = LegalInsight(
                    insight_id=generate_event_id(),
                    insight_type="procedural",
                    description=f"{event_type.replace('_', ' ').title()} event",
                    confidence=0.8,
                    text_excerpt=text,
                    speaker_id=speaker_id,
                    legal_significance=5,
                    potential_impact="low",
                    tags=["procedural", event_type]
                )
                insights.append(insight)
        
        return insights
    
    async def _analyze_key_moments(self,
                                 text: str,
                                 context: str,
                                 speaker_id: Optional[str],
                                 speaker_type: Optional[SpeakerType]) -> List[LegalInsight]:
        """Analyze text for key moments in testimony."""
        insights = []
        
        for moment_type, pattern in self.key_moment_patterns.items():
            matches = list(pattern.finditer(text))
            
            for match in matches:
                # Calculate significance based on speaker type and moment type
                significance = self._calculate_moment_significance(moment_type, speaker_type)
                
                insight = LegalInsight(
                    insight_id=generate_event_id(),
                    insight_type="key_testimony",
                    description=f"{moment_type.replace('_', ' ').title()} detected",
                    confidence=0.75,
                    text_excerpt=match.group(),
                    speaker_id=speaker_id,
                    speaker_type=speaker_type,
                    legal_significance=significance,
                    potential_impact=self._assess_moment_impact(moment_type, significance),
                    follow_up_questions=self._generate_follow_up_questions(moment_type, text),
                    tags=["key_moment", moment_type, speaker_type.value if speaker_type else "unknown"]
                )
                insights.append(insight)
        
        return insights
    
    async def _perform_ai_analysis(self,
                                 text: str,
                                 context: str,
                                 speaker_type: Optional[SpeakerType]) -> List[LegalInsight]:
        """Perform AI-powered deep legal analysis."""
        try:
            response = await self.api_client.post(
                "/ai/legal-analysis",
                json={
                    "text": text,
                    "context": context,
                    "speaker_type": speaker_type.value if speaker_type else None,
                    "analysis_types": [
                        "legal_issues",
                        "case_law_relevance", 
                        "strategic_implications",
                        "risk_assessment",
                        "evidence_gaps"
                    ]
                },
                timeout=15.0
            )
            
            if response.get("success"):
                ai_insights = []
                
                for analysis in response.get("analyses", []):
                    insight = LegalInsight(
                        insight_id=generate_event_id(),
                        insight_type=analysis.get("type", "ai_analysis"),
                        description=analysis.get("description", ""),
                        confidence=analysis.get("confidence", 0.7),
                        text_excerpt=text,
                        legal_significance=analysis.get("significance", 5),
                        potential_impact=analysis.get("impact", "medium"),
                        legal_precedents=analysis.get("precedents", []),
                        suggested_actions=analysis.get("actions", []),
                        tags=analysis.get("tags", ["ai_analysis"])
                    )
                    ai_insights.append(insight)
                
                return ai_insights
            
        except Exception as e:
            self.logger.warning(f"AI analysis failed: {e}")
        
        return []
    
    async def _assess_objection_merit(self, objection: ObjectionEvent, text: str) -> str:
        """Assess the merit of an objection."""
        objection_type = objection.objection_type
        
        # Rule-based merit assessment
        if objection_type == ObjectionType.HEARSAY:
            # Look for hearsay exceptions
            hearsay_exceptions = [
                r'\bpresent\s+sense\s+impression\b',
                r'\bexcited\s+utterance\b',
                r'\bbusiness\s+records?\b',
                r'\bpublic\s+records?\b'
            ]
            
            for exception in hearsay_exceptions:
                if re.search(exception, text, re.IGNORECASE):
                    return "weak"  # Exception may apply
            
            return "strong"  # No clear exception
        
        elif objection_type == ObjectionType.LEADING:
            # Check if it's actually a leading question
            if re.search(r'\bis\s+it\s+(?:not\s+)?true\s+that\b|\bdid\s+you\s+not\b', text, re.IGNORECASE):
                return "strong"
            return "unclear"
        
        elif objection_type == ObjectionType.RELEVANCE:
            # Would need more context to assess relevance
            return "unclear"
        
        return "unclear"
    
    def _calculate_moment_significance(self, moment_type: str, speaker_type: Optional[SpeakerType]) -> int:
        """Calculate significance score for key moments."""
        base_scores = {
            "admission": 9,
            "denial": 7,
            "impeachment": 8,
            "credibility_challenge": 6,
            "expert_opinion": 7,
            "emotional_moment": 5
        }
        
        base_score = base_scores.get(moment_type, 5)
        
        # Adjust based on speaker type
        if speaker_type == SpeakerType.WITNESS:
            if moment_type in ["admission", "denial"]:
                base_score += 1
        elif speaker_type == SpeakerType.EXPERT_WITNESS:
            if moment_type == "expert_opinion":
                base_score += 1
        
        return min(base_score, 10)
    
    def _assess_moment_impact(self, moment_type: str, significance: int) -> str:
        """Assess potential impact of key moments."""
        if significance >= 8:
            return "high"
        elif significance >= 6:
            return "medium"
        else:
            return "low"
    
    def _generate_follow_up_questions(self, moment_type: str, text: str) -> List[str]:
        """Generate follow-up questions for key moments."""
        questions = []
        
        if moment_type == "admission":
            questions.extend([
                "What are the implications of this admission?",
                "How does this admission affect other claims?",
                "Should this be emphasized in closing arguments?"
            ])
        elif moment_type == "denial":
            questions.extend([
                "Is there contradictory evidence to this denial?",
                "What documentation supports or refutes this denial?",
                "How credible is this denial given the context?"
            ])
        elif moment_type == "impeachment":
            questions.extend([
                "What prior statement contradicts current testimony?",
                "How significant is this inconsistency?",
                "Should additional impeachment evidence be introduced?"
            ])
        
        return questions[:3]  # Limit to top 3 questions
    
    def get_session_analysis_summary(self, session_id: str) -> Dict[str, Any]:
        """Get analysis summary for a session."""
        if session_id not in self.session_state:
            return {}
        
        # Count objections by type
        objection_counts = Counter()
        objection_outcomes = Counter()
        
        for objection in self.objection_tracker.objections.values():
            objection_counts[objection.objection_type.value] += 1
            if objection.ruling:
                objection_outcomes[objection.ruling] += 1
        
        # Count evidence by status
        evidence_counts = Counter()
        for evidence in self.evidence_tracker.evidence.values():
            evidence_counts[evidence.status] += 1
        
        return {
            "session_id": session_id,
            "session_state": self.session_state[session_id],
            "objections": {
                "total": len(self.objection_tracker.objections),
                "by_type": dict(objection_counts),
                "outcomes": dict(objection_outcomes),
                "pending": len(self.pending_objections.get(session_id, []))
            },
            "evidence": {
                "total": len(self.evidence_tracker.evidence),
                "by_status": dict(evidence_counts)
            }
        }
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get overall analysis statistics."""
        return {
            "total_segments_analyzed": self.total_analyzed,
            "insights_generated": self.insights_generated,
            "objections_detected": self.objections_detected,
            "evidence_items_tracked": self.evidence_tracked,
            "active_sessions": len(self.session_state),
            "legal_patterns_loaded": len(self.legal_patterns),
            "procedural_patterns_loaded": len(self.procedural_patterns)
        }