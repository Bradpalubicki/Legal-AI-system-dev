"""
Comprehensive analyzer that coordinates all transcript analysis components for complete court proceeding analysis.
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json
from sqlalchemy.orm import Session

from ..shared.database.models import Case, Document, User, TranscriptSegment, CourtSession
from ..shared.database.connection import get_db
from ..shared.utils.ai_client import AIClient

from .speech_analyzer import SpeechAnalyzer, SpeakerProfile
from .transcript_processor import TranscriptProcessor, ProcessedTranscript
from .legal_analyzer import LegalAnalyzer, LegalEvent, ObjectionType
from .statement_analyzer import StatementAnalyzer, IdentifiedStatement, StatementType
from .order_tracker import OrderTracker, TrackedOrder, ComplianceStatus
from .key_moment_detector import KeyMomentDetector, KeyMoment, MomentType, ImpactLevel


@dataclass
class ComprehensiveAnalysis:
    """Complete analysis results for a court proceeding."""
    session_id: str
    case_id: str
    analysis_timestamp: datetime
    duration: float
    
    # Speaker Analysis
    identified_speakers: List[SpeakerProfile]
    speaker_time_distribution: Dict[str, float]
    speaker_word_count: Dict[str, int]
    
    # Transcript Quality
    overall_quality_score: float
    audio_quality_issues: List[str]
    transcription_confidence: float
    
    # Legal Events
    total_objections: int
    objection_success_rate: float
    objection_breakdown: Dict[str, int]
    evidence_introduced: List[Dict[str, Any]]
    procedural_events: List[Dict[str, Any]]
    
    # Key Statements
    court_orders: List[IdentifiedStatement]
    stipulations: List[IdentifiedStatement]
    admissions: List[IdentifiedStatement]
    expert_opinions: List[IdentifiedStatement]
    
    # Key Moments
    breakthrough_moments: List[KeyMoment]
    dramatic_exchanges: List[KeyMoment]
    case_turning_points: List[KeyMoment]
    
    # Compliance Tracking
    new_court_orders: List[TrackedOrder]
    compliance_deadlines: List[Dict[str, Any]]
    
    # Overall Assessment
    case_momentum: str  # "favoring_plaintiff", "favoring_defendant", "neutral", "mixed"
    credibility_assessments: Dict[str, float]
    settlement_likelihood: float
    trial_outcome_prediction: Dict[str, float]
    
    # Strategic Insights
    strengths_by_party: Dict[str, List[str]]
    weaknesses_by_party: Dict[str, List[str]]
    recommended_actions: List[str]
    follow_up_questions: List[str]
    
    # Media and Communication
    quotable_moments: List[str]
    media_worthy_developments: List[Dict[str, Any]]
    public_relations_considerations: List[str]


class ComprehensiveAnalyzer:
    """Master analyzer that coordinates all transcript analysis components."""
    
    def __init__(self):
        self.speech_analyzer = SpeechAnalyzer()
        self.transcript_processor = TranscriptProcessor()
        self.legal_analyzer = LegalAnalyzer()
        self.statement_analyzer = StatementAnalyzer()
        self.order_tracker = OrderTracker()
        self.moment_detector = KeyMomentDetector()
        self.ai_client = AIClient()

    async def analyze_complete_session(
        self,
        session_id: str,
        case: Case,
        audio_segments: List[bytes],
        db: Session
    ) -> ComprehensiveAnalysis:
        """Perform comprehensive analysis of a complete court session."""
        try:
            print(f"Starting comprehensive analysis for session {session_id}")
            
            # Step 1: Speech-to-text processing and speaker identification
            print("Processing speech-to-text and identifying speakers...")
            speech_results = await self._process_speech_segments(audio_segments)
            
            # Step 2: Transcript processing and enhancement
            print("Processing and enhancing transcript...")
            processed_transcript = await self._process_transcript(speech_results)
            
            # Step 3: Parallel analysis of different aspects
            print("Performing parallel analysis...")
            analysis_tasks = [
                self._analyze_legal_events(processed_transcript, case),
                self._analyze_statements(processed_transcript, case),
                self._detect_key_moments(processed_transcript, case),
                self._assess_case_dynamics(processed_transcript, case)
            ]
            
            legal_analysis, statement_analysis, moment_analysis, dynamics_analysis = await asyncio.gather(*analysis_tasks)
            
            # Step 4: Track new court orders
            print("Tracking new court orders...")
            order_tracking = await self._track_new_orders(statement_analysis, case, db)
            
            # Step 5: Generate comprehensive insights
            print("Generating comprehensive insights...")
            comprehensive_insights = await self._generate_comprehensive_insights(
                processed_transcript, legal_analysis, statement_analysis, 
                moment_analysis, dynamics_analysis, case
            )
            
            # Step 6: Compile final analysis
            analysis = ComprehensiveAnalysis(
                session_id=session_id,
                case_id=case.id,
                analysis_timestamp=datetime.now(),
                duration=processed_transcript.total_duration,
                
                # Speaker Analysis
                identified_speakers=speech_results.get("speaker_profiles", []),
                speaker_time_distribution=speech_results.get("speaker_time", {}),
                speaker_word_count=speech_results.get("speaker_words", {}),
                
                # Transcript Quality
                overall_quality_score=processed_transcript.quality_metrics.get("overall_score", 0.0),
                audio_quality_issues=processed_transcript.quality_metrics.get("issues", []),
                transcription_confidence=processed_transcript.confidence_score,
                
                # Legal Events
                total_objections=len(legal_analysis.get("objections", [])),
                objection_success_rate=legal_analysis.get("objection_success_rate", 0.0),
                objection_breakdown=legal_analysis.get("objection_breakdown", {}),
                evidence_introduced=legal_analysis.get("evidence_events", []),
                procedural_events=legal_analysis.get("procedural_events", []),
                
                # Key Statements
                court_orders=[s for s in statement_analysis if s.statement_type == StatementType.COURT_ORDER],
                stipulations=[s for s in statement_analysis if s.statement_type == StatementType.STIPULATION],
                admissions=[s for s in statement_analysis if s.statement_type == StatementType.ADMISSION],
                expert_opinions=[s for s in statement_analysis if s.statement_type == StatementType.EXPERT_OPINION],
                
                # Key Moments
                breakthrough_moments=[m for m in moment_analysis if m.moment_type == MomentType.BREAKTHROUGH_ADMISSION],
                dramatic_exchanges=[m for m in moment_analysis if m.moment_type == MomentType.DRAMATIC_OBJECTION],
                case_turning_points=[m for m in moment_analysis if m.moment_type == MomentType.CASE_TURNING_POINT],
                
                # Compliance Tracking
                new_court_orders=order_tracking.get("new_orders", []),
                compliance_deadlines=order_tracking.get("deadlines", []),
                
                # Overall Assessment
                case_momentum=comprehensive_insights.get("case_momentum", "neutral"),
                credibility_assessments=comprehensive_insights.get("credibility_assessments", {}),
                settlement_likelihood=comprehensive_insights.get("settlement_likelihood", 0.0),
                trial_outcome_prediction=comprehensive_insights.get("outcome_prediction", {}),
                
                # Strategic Insights
                strengths_by_party=comprehensive_insights.get("strengths_by_party", {}),
                weaknesses_by_party=comprehensive_insights.get("weaknesses_by_party", {}),
                recommended_actions=comprehensive_insights.get("recommended_actions", []),
                follow_up_questions=comprehensive_insights.get("follow_up_questions", []),
                
                # Media and Communication
                quotable_moments=comprehensive_insights.get("quotable_moments", []),
                media_worthy_developments=comprehensive_insights.get("media_worthy", []),
                public_relations_considerations=comprehensive_insights.get("pr_considerations", [])
            )
            
            print(f"Comprehensive analysis completed for session {session_id}")
            return analysis
            
        except Exception as e:
            print(f"Error in comprehensive analysis: {e}")
            raise

    async def _process_speech_segments(self, audio_segments: List[bytes]) -> Dict[str, Any]:
        """Process all audio segments for speech-to-text and speaker identification."""
        try:
            all_segments = []
            speaker_profiles = []
            speaker_time = {}
            speaker_words = {}
            
            for i, audio_data in enumerate(audio_segments):
                # Process each audio segment
                result = await self.speech_analyzer.analyze_audio_segment(
                    audio_data, f"segment_{i}"
                )
                
                if result:
                    all_segments.extend(result.get("segments", []))
                    
                    # Update speaker profiles
                    for profile in result.get("speaker_profiles", []):
                        existing_profile = next((p for p in speaker_profiles if p.speaker_id == profile.speaker_id), None)
                        if existing_profile:
                            existing_profile.total_speaking_time += profile.total_speaking_time
                            existing_profile.segment_count += profile.segment_count
                        else:
                            speaker_profiles.append(profile)
            
            # Calculate speaker statistics
            for segment in all_segments:
                speaker = segment.get("speaker", "Unknown")
                duration = segment.get("duration", 0.0)
                word_count = len(segment.get("text", "").split())
                
                speaker_time[speaker] = speaker_time.get(speaker, 0.0) + duration
                speaker_words[speaker] = speaker_words.get(speaker, 0) + word_count
            
            return {
                "segments": all_segments,
                "speaker_profiles": speaker_profiles,
                "speaker_time": speaker_time,
                "speaker_words": speaker_words
            }
            
        except Exception as e:
            print(f"Error processing speech segments: {e}")
            return {"segments": [], "speaker_profiles": [], "speaker_time": {}, "speaker_words": {}}

    async def _process_transcript(self, speech_results: Dict[str, Any]) -> ProcessedTranscript:
        """Process and enhance the raw transcript."""
        try:
            segments = speech_results.get("segments", [])
            raw_text = " ".join([s.get("text", "") for s in segments])
            
            # Process with transcript processor
            processed = await self.transcript_processor.process_transcript(raw_text)
            
            # Add segment timing information
            processed.segment_count = len(segments)
            processed.total_duration = sum(s.get("duration", 0.0) for s in segments)
            
            return processed
            
        except Exception as e:
            print(f"Error processing transcript: {e}")
            # Return minimal processed transcript on error
            return ProcessedTranscript(
                original_text="",
                enhanced_text="",
                confidence_score=0.0,
                corrections_made=[],
                quality_metrics={},
                legal_terms_found=[],
                segment_count=0,
                total_duration=0.0
            )

    async def _analyze_legal_events(
        self, 
        transcript: ProcessedTranscript, 
        case: Case
    ) -> Dict[str, Any]:
        """Analyze legal events in the transcript."""
        try:
            # Create mock transcript segments for analysis
            segments = self._create_transcript_segments(transcript)
            
            all_objections = []
            all_evidence = []
            all_procedural = []
            
            for segment in segments:
                # Analyze each segment for legal events
                legal_events = await self.legal_analyzer.analyze_transcript_segment(segment, case)
                
                for event in legal_events:
                    if event.event_type.value.startswith("objection"):
                        all_objections.append(event)
                    elif "evidence" in event.event_type.value:
                        all_evidence.append(event)
                    else:
                        all_procedural.append(event)
            
            # Calculate objection success rate
            sustained_objections = sum(1 for obj in all_objections if "sustained" in obj.resolution.lower())
            total_objections = len(all_objections)
            success_rate = (sustained_objections / total_objections) if total_objections > 0 else 0.0
            
            # Objection breakdown by type
            objection_breakdown = {}
            for obj in all_objections:
                obj_type = obj.objection_type.value if obj.objection_type else "unknown"
                objection_breakdown[obj_type] = objection_breakdown.get(obj_type, 0) + 1
            
            return {
                "objections": all_objections,
                "objection_success_rate": success_rate,
                "objection_breakdown": objection_breakdown,
                "evidence_events": [self._event_to_dict(e) for e in all_evidence],
                "procedural_events": [self._event_to_dict(e) for e in all_procedural]
            }
            
        except Exception as e:
            print(f"Error analyzing legal events: {e}")
            return {
                "objections": [],
                "objection_success_rate": 0.0,
                "objection_breakdown": {},
                "evidence_events": [],
                "procedural_events": []
            }

    async def _analyze_statements(
        self, 
        transcript: ProcessedTranscript, 
        case: Case
    ) -> List[IdentifiedStatement]:
        """Analyze key statements in the transcript."""
        try:
            segments = self._create_transcript_segments(transcript)
            all_statements = []
            
            for segment in segments:
                statements = await self.statement_analyzer.analyze_transcript_segment(segment, case)
                all_statements.extend(statements)
            
            return all_statements
            
        except Exception as e:
            print(f"Error analyzing statements: {e}")
            return []

    async def _detect_key_moments(
        self, 
        transcript: ProcessedTranscript, 
        case: Case
    ) -> List[KeyMoment]:
        """Detect key moments in the transcript."""
        try:
            segments = self._create_transcript_segments(transcript)
            all_moments = []
            
            for i, segment in enumerate(segments):
                # Get surrounding context
                surrounding_context = segments[max(0, i-2):i+3]
                
                moments = await self.moment_detector.analyze_segment_for_moments(
                    segment, case, surrounding_context
                )
                all_moments.extend(moments)
            
            # Create moment clusters
            await self.moment_detector.create_moment_clusters(all_moments)
            
            return all_moments
            
        except Exception as e:
            print(f"Error detecting key moments: {e}")
            return []

    async def _assess_case_dynamics(
        self, 
        transcript: ProcessedTranscript, 
        case: Case
    ) -> Dict[str, Any]:
        """Assess overall case dynamics and momentum."""
        try:
            prompt = f"""
            Analyze this court transcript for overall case dynamics and momentum:
            
            Case: {case.title} ({case.case_type})
            Transcript: {transcript.enhanced_text[:3000]}...
            
            Assess:
            1. Case momentum (favoring which party and why)
            2. Settlement likelihood based on exchanges
            3. Credibility assessments for key participants
            4. Trial outcome predictions
            5. Strategic positioning of each party
            
            Return as JSON:
            {{
                "case_momentum": "favoring_plaintiff|favoring_defendant|neutral|mixed",
                "momentum_explanation": "Detailed explanation",
                "settlement_likelihood": 0.65,
                "settlement_indicators": ["indicator1", "indicator2"],
                "outcome_prediction": {{"plaintiff_win": 0.4, "defendant_win": 0.6}},
                "key_dynamics": ["dynamic1", "dynamic2"]
            }}
            """
            
            response = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.2,
                max_tokens=1500
            )
            
            return json.loads(response)
            
        except Exception as e:
            print(f"Error assessing case dynamics: {e}")
            return {
                "case_momentum": "neutral",
                "settlement_likelihood": 0.5,
                "outcome_prediction": {"plaintiff_win": 0.5, "defendant_win": 0.5},
                "key_dynamics": []
            }

    async def _track_new_orders(
        self, 
        statements: List[IdentifiedStatement], 
        case: Case, 
        db: Session
    ) -> Dict[str, Any]:
        """Track any new court orders identified."""
        try:
            court_orders = [s for s in statements if s.statement_type == StatementType.COURT_ORDER]
            new_tracked_orders = []
            deadlines = []
            
            for order_statement in court_orders:
                tracked_order = await self.order_tracker.track_new_order(order_statement, case, db)
                new_tracked_orders.append(tracked_order)
                
                # Extract deadlines
                if tracked_order.compliance_deadline:
                    deadlines.append({
                        "order_id": tracked_order.order_id,
                        "description": tracked_order.title,
                        "deadline": tracked_order.compliance_deadline.isoformat(),
                        "urgency": tracked_order.urgency_level.value
                    })
            
            return {
                "new_orders": new_tracked_orders,
                "deadlines": deadlines
            }
            
        except Exception as e:
            print(f"Error tracking new orders: {e}")
            return {"new_orders": [], "deadlines": []}

    async def _generate_comprehensive_insights(
        self, 
        transcript: ProcessedTranscript,
        legal_analysis: Dict[str, Any],
        statement_analysis: List[IdentifiedStatement],
        moment_analysis: List[KeyMoment],
        dynamics_analysis: Dict[str, Any],
        case: Case
    ) -> Dict[str, Any]:
        """Generate comprehensive strategic insights."""
        try:
            # Prepare summary data for AI analysis
            summary_data = {
                "transcript_quality": transcript.confidence_score,
                "total_objections": len(legal_analysis.get("objections", [])),
                "objection_success_rate": legal_analysis.get("objection_success_rate", 0.0),
                "key_statements": len(statement_analysis),
                "breakthrough_moments": len([m for m in moment_analysis if m.impact_level in [ImpactLevel.CASE_CHANGING, ImpactLevel.HIGHLY_SIGNIFICANT]]),
                "case_momentum": dynamics_analysis.get("case_momentum", "neutral")
            }
            
            prompt = f"""
            Generate comprehensive strategic insights for this court proceeding:
            
            Case: {case.title} ({case.case_type})
            Session Summary: {json.dumps(summary_data, indent=2)}
            
            Key Moments: {len(moment_analysis)} detected
            Key Statements: {len(statement_analysis)} identified
            
            Generate:
            1. Credibility assessments for key participants (0-1 scale)
            2. Strengths and weaknesses by party
            3. Recommended immediate actions
            4. Strategic follow-up questions
            5. Quotable moments for media/briefs
            6. Public relations considerations
            7. Settlement likelihood and indicators
            
            Return as JSON:
            {{
                "credibility_assessments": {{"witness_name": 0.7, "attorney_name": 0.8}},
                "strengths_by_party": {{"Plaintiff": ["strength1"], "Defendant": ["strength1"]}},
                "weaknesses_by_party": {{"Plaintiff": ["weakness1"], "Defendant": ["weakness1"]}},
                "recommended_actions": ["action1", "action2"],
                "follow_up_questions": ["question1", "question2"],
                "quotable_moments": ["quote1", "quote2"],
                "media_worthy": [{{"moment": "description", "significance": "high"}}],
                "pr_considerations": ["consideration1", "consideration2"],
                "settlement_likelihood": 0.65,
                "outcome_prediction": {{"plaintiff_win": 0.4, "defendant_win": 0.6}}
            }}
            """
            
            response = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.3,
                max_tokens=2000
            )
            
            return json.loads(response)
            
        except Exception as e:
            print(f"Error generating comprehensive insights: {e}")
            return {
                "credibility_assessments": {},
                "strengths_by_party": {},
                "weaknesses_by_party": {},
                "recommended_actions": [],
                "follow_up_questions": [],
                "quotable_moments": [],
                "media_worthy": [],
                "pr_considerations": [],
                "settlement_likelihood": 0.5,
                "outcome_prediction": {"plaintiff_win": 0.5, "defendant_win": 0.5}
            }

    def _create_transcript_segments(self, transcript: ProcessedTranscript) -> List[TranscriptSegment]:
        """Create mock transcript segments for analysis."""
        # Split transcript into sentences/segments
        sentences = transcript.enhanced_text.split('. ')
        segments = []
        
        for i, sentence in enumerate(sentences):
            if len(sentence.strip()) > 10:  # Skip very short segments
                segment = TranscriptSegment(
                    id=f"segment_{i}",
                    session_id="mock_session",
                    speaker="Unknown Speaker",  # Would need speaker diarization
                    text=sentence.strip(),
                    timestamp=float(i * 10),  # Mock timing
                    duration=10.0,  # Mock duration
                    confidence=transcript.confidence_score
                )
                segments.append(segment)
        
        return segments

    def _event_to_dict(self, event: 'LegalEvent') -> Dict[str, Any]:
        """Convert LegalEvent to dictionary for serialization."""
        return {
            "event_type": event.event_type.value,
            "timestamp": event.timestamp,
            "description": event.description,
            "participants": event.participants,
            "legal_significance": event.legal_significance,
            "objection_type": event.objection_type.value if event.objection_type else None,
            "resolution": event.resolution
        }

    def generate_session_report(self, analysis: ComprehensiveAnalysis) -> str:
        """Generate a comprehensive session report."""
        try:
            report = f"""
# Court Session Analysis Report

**Case:** {analysis.case_id}
**Session:** {analysis.session_id}
**Date:** {analysis.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Duration:** {analysis.duration:.1f} minutes

## Executive Summary

**Case Momentum:** {analysis.case_momentum.replace('_', ' ').title()}
**Settlement Likelihood:** {analysis.settlement_likelihood:.1%}
**Overall Quality Score:** {analysis.overall_quality_score:.2f}

## Key Statistics

- **Total Speakers:** {len(analysis.identified_speakers)}
- **Total Objections:** {analysis.total_objections}
- **Objection Success Rate:** {analysis.objection_success_rate:.1%}
- **Court Orders Issued:** {len(analysis.court_orders)}
- **Key Moments Detected:** {len(analysis.breakthrough_moments) + len(analysis.dramatic_exchanges)}

## Legal Events Breakdown

**Objections by Type:**
{self._format_objection_breakdown(analysis.objection_breakdown)}

**Evidence Introduction:** {len(analysis.evidence_introduced)} items
**Procedural Events:** {len(analysis.procedural_events)} events

## Key Statements

- **Court Orders:** {len(analysis.court_orders)}
- **Stipulations:** {len(analysis.stipulations)}
- **Admissions:** {len(analysis.admissions)}
- **Expert Opinions:** {len(analysis.expert_opinions)}

## Key Moments

**Breakthrough Moments:** {len(analysis.breakthrough_moments)}
**Dramatic Exchanges:** {len(analysis.dramatic_exchanges)}
**Case Turning Points:** {len(analysis.case_turning_points)}

## Strategic Assessment

**Recommended Actions:**
{self._format_list(analysis.recommended_actions)}

**Follow-up Questions:**
{self._format_list(analysis.follow_up_questions)}

## Compliance Tracking

**New Court Orders:** {len(analysis.new_court_orders)}
**Upcoming Deadlines:** {len(analysis.compliance_deadlines)}

## Media and Public Relations

**Quotable Moments:** {len(analysis.quotable_moments)}
**Media-Worthy Developments:** {len(analysis.media_worthy_developments)}

---
*Report generated by Legal AI System - Comprehensive Transcript Analyzer*
"""
            
            return report
            
        except Exception as e:
            print(f"Error generating session report: {e}")
            return f"Error generating report: {e}"

    def _format_objection_breakdown(self, breakdown: Dict[str, int]) -> str:
        """Format objection breakdown for report."""
        if not breakdown:
            return "None recorded"
        
        formatted = []
        for obj_type, count in breakdown.items():
            formatted.append(f"- {obj_type.replace('_', ' ').title()}: {count}")
        
        return '\n'.join(formatted)

    def _format_list(self, items: List[str]) -> str:
        """Format a list of items for report."""
        if not items:
            return "None identified"
        
        return '\n'.join([f"- {item}" for item in items])

    async def get_real_time_insights(
        self, 
        current_segment: TranscriptSegment,
        case: Case,
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get real-time insights for current segment."""
        try:
            # Quick analysis of current segment
            legal_events = await self.legal_analyzer.analyze_transcript_segment(current_segment, case)
            statements = await self.statement_analyzer.analyze_transcript_segment(current_segment, case)
            moments = await self.moment_detector.analyze_segment_for_moments(current_segment, case)
            
            # Generate real-time alerts
            alerts = []
            
            # Check for high-impact moments
            for moment in moments:
                if moment.impact_level in [ImpactLevel.CASE_CHANGING, ImpactLevel.HIGHLY_SIGNIFICANT]:
                    alerts.append({
                        "type": "key_moment",
                        "urgency": "high",
                        "message": f"Key moment detected: {moment.title}",
                        "details": moment.description
                    })
            
            # Check for court orders
            for statement in statements:
                if statement.statement_type == StatementType.COURT_ORDER:
                    alerts.append({
                        "type": "court_order",
                        "urgency": "critical",
                        "message": "Court order detected",
                        "details": statement.text
                    })
            
            # Check for objections
            for event in legal_events:
                if "objection" in event.event_type.value:
                    alerts.append({
                        "type": "objection",
                        "urgency": "medium",
                        "message": f"Objection: {event.objection_type.value if event.objection_type else 'Unknown'}",
                        "details": f"Resolution: {event.resolution}"
                    })
            
            return {
                "timestamp": current_segment.timestamp,
                "speaker": current_segment.speaker,
                "alerts": alerts,
                "legal_events_count": len(legal_events),
                "statements_count": len(statements),
                "moments_count": len(moments),
                "requires_attention": len(alerts) > 0
            }
            
        except Exception as e:
            print(f"Error getting real-time insights: {e}")
            return {
                "timestamp": current_segment.timestamp,
                "alerts": [],
                "requires_attention": False
            }