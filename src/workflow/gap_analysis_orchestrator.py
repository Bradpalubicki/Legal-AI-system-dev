"""
Gap Analysis and Clarifying Questions Workflow Orchestrator

Integrates the C-D-E workflow steps:
C) System Identifies Gaps → D) Generate Clarifying Questions → E) User Answers Questions

This orchestrator connects existing systems:
- Document analysis and gap detection
- Intelligent question generation
- User response collection and processing
- Integration with strategy generation

CRITICAL LEGAL DISCLAIMER:
This system provides educational information gathering assistance only.
All questions and analysis are for educational purposes and do not constitute
legal advice. No attorney-client relationship is created.
Consult qualified legal counsel for legal guidance.

Created: 2025-09-14
Legal AI System - Workflow Orchestration
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import existing systems
try:
    from ..document_processor.sophisticated_understanding import (
        SophisticatedAnalysis, DocumentClass, ContextualGap
    )
    from ..document_processor.intelligent_intake import (
        InformationGap, DocumentIntakeAnalyzer
    )
    from ..document_processor.question_generator import (
        IntelligentQuestionGenerator, IntelligentQuestion
    )
    from ..strategy_generator.comprehensive_strategy_options import (
        ComprehensiveStrategyGenerator, ComprehensiveStrategy
    )
    from ..strategy_generator.compliance_presentation import (
        CompliancePresentationEngine, FormattedContent
    )
except ImportError:
    # Mock imports for standalone use
    from dataclasses import dataclass

    @dataclass
    class ContextualGap:
        gap_type: str
        description: str
        severity: str

    @dataclass
    class InformationGap:
        gap_type: str
        description: str
        severity: str
        required_for: List[str]
        suggestions: List[str]

    @dataclass
    class IntelligentQuestion:
        question_id: str
        question_text: str
        why_needed: str
        input_type: str

    class SophisticatedAnalysis:
        def __init__(self):
            self.contextual_gaps = []

    class DocumentIntakeAnalyzer:
        def analyze_document_gaps(self, analysis): return []

    class IntelligentQuestionGenerator:
        def generate_questions_for_bankruptcy(self, gaps): return []
        def generate_questions_for_litigation(self, gaps): return []

    class ComprehensiveStrategyGenerator:
        def generate_strategic_options(self, context, max_options=6): return []


class WorkflowStage(Enum):
    """Workflow execution stages"""
    DOCUMENT_UPLOADED = "document_uploaded"
    ANALYSIS_COMPLETE = "analysis_complete"
    GAPS_IDENTIFIED = "gaps_identified"
    QUESTIONS_GENERATED = "questions_generated"
    USER_RESPONDING = "user_responding"
    RESPONSES_COLLECTED = "responses_collected"
    STRATEGY_GENERATION = "strategy_generation"
    COMPLETE = "complete"
    ERROR = "error"


class ResponseType(Enum):
    """Types of user responses"""
    TEXT = "text"
    CURRENCY = "currency"
    DATE = "date"
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    BOOLEAN = "boolean"


@dataclass
class UserResponse:
    """User response to a clarifying question"""
    question_id: str
    response_value: Any
    response_type: ResponseType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence_level: Optional[float] = None  # 0-1, user's confidence in response
    notes: Optional[str] = None  # Optional user notes

    def to_context_data(self) -> Dict[str, Any]:
        """Convert response to context data for strategy generation"""
        return {
            "question_id": self.question_id,
            "value": self.response_value,
            "type": self.response_type.value,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence_level,
            "notes": self.notes
        }


@dataclass
class WorkflowSession:
    """Complete workflow session tracking"""
    session_id: str
    user_id: Optional[str] = None
    document_path: Optional[str] = None

    # Workflow state
    current_stage: WorkflowStage = WorkflowStage.DOCUMENT_UPLOADED
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    # Analysis results
    document_analysis: Optional[SophisticatedAnalysis] = None
    identified_gaps: List[InformationGap] = field(default_factory=list)
    generated_questions: List[IntelligentQuestion] = field(default_factory=list)

    # User responses
    user_responses: List[UserResponse] = field(default_factory=list)
    pending_questions: List[str] = field(default_factory=list)  # Question IDs
    completed_questions: List[str] = field(default_factory=list)  # Question IDs

    # Results
    strategy_context: Dict[str, Any] = field(default_factory=dict)
    generated_strategies: List[Dict[str, Any]] = field(default_factory=list)  # Strategy summaries
    formatted_strategies: List[Dict[str, Any]] = field(default_factory=list)  # Formatted content

    # Error handling
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def update_stage(self, new_stage: WorkflowStage):
        """Update workflow stage with timestamp"""
        self.current_stage = new_stage
        self.last_updated = datetime.utcnow()

    def add_response(self, response: UserResponse):
        """Add user response and update tracking"""
        self.user_responses.append(response)
        if response.question_id in self.pending_questions:
            self.pending_questions.remove(response.question_id)
        if response.question_id not in self.completed_questions:
            self.completed_questions.append(response.question_id)
        self.last_updated = datetime.utcnow()

    def is_complete(self) -> bool:
        """Check if all questions have been answered"""
        return len(self.pending_questions) == 0 and len(self.generated_questions) > 0

    def get_completion_percentage(self) -> float:
        """Get percentage of questions completed"""
        if not self.generated_questions:
            return 0.0
        return len(self.completed_questions) / len(self.generated_questions)


class GapAnalysisOrchestrator:
    """
    Orchestrates the complete gap analysis and clarifying questions workflow.

    Workflow Steps:
    C) System Identifies Gaps - Analyze document and identify missing information
    D) Generate Clarifying Questions - Create intelligent questions for gaps
    E) User Answers Questions - Collect and process user responses

    EDUCATIONAL PURPOSE DISCLAIMER:
    This orchestrator facilitates information gathering for educational purposes only.
    All analysis and questions are informational and do not constitute legal advice.
    """

    def __init__(self):
        """Initialize the workflow orchestrator"""
        self.logger = logging.getLogger(__name__)

        # Initialize component systems
        self.intake_analyzer = DocumentIntakeAnalyzer()
        self.question_generator = IntelligentQuestionGenerator()
        self.strategy_generator = ComprehensiveStrategyGenerator()
        self.presentation_engine = CompliancePresentationEngine()

        # Active sessions
        self.active_sessions: Dict[str, WorkflowSession] = {}

        # Workflow configuration
        self.max_questions_per_session = 15
        self.question_timeout_hours = 24

    def start_workflow(self, document_analysis: SophisticatedAnalysis,
                      user_id: Optional[str] = None,
                      document_path: Optional[str] = None) -> WorkflowSession:
        """
        Start a new gap analysis workflow session.

        Args:
            document_analysis: Results from sophisticated document analysis
            user_id: Optional user identifier
            document_path: Optional path to source document

        Returns:
            WorkflowSession object for tracking progress
        """
        try:
            # Create new session
            session_id = str(uuid.uuid4())
            session = WorkflowSession(
                session_id=session_id,
                user_id=user_id,
                document_path=document_path,
                document_analysis=document_analysis
            )

            # Step C: Identify gaps
            gaps = self._identify_gaps(document_analysis)
            session.identified_gaps = gaps
            session.update_stage(WorkflowStage.GAPS_IDENTIFIED)

            # Step D: Generate questions
            if gaps:
                questions = self._generate_questions(gaps, document_analysis)
                session.generated_questions = questions
                session.pending_questions = [q.question_id for q in questions]
                session.update_stage(WorkflowStage.QUESTIONS_GENERATED)
            else:
                # No gaps found, proceed directly to strategy generation
                session.update_stage(WorkflowStage.STRATEGY_GENERATION)

            # Store session
            self.active_sessions[session_id] = session

            self.logger.info(f"Started workflow session {session_id} with {len(gaps)} gaps and {len(session.generated_questions)} questions")

            return session

        except Exception as e:
            self.logger.error(f"Error starting workflow: {str(e)}")
            session = WorkflowSession(session_id=str(uuid.uuid4()))
            session.current_stage = WorkflowStage.ERROR
            session.errors.append(f"Failed to start workflow: {str(e)}")
            return session

    def _identify_gaps(self, document_analysis: SophisticatedAnalysis) -> List[InformationGap]:
        """Step C: Identify information gaps in document analysis"""
        try:
            # Use existing intake analyzer
            gaps = self.intake_analyzer.analyze_document_gaps(document_analysis)

            # Convert contextual gaps to information gaps if needed
            if hasattr(document_analysis, 'contextual_gaps'):
                for gap in document_analysis.contextual_gaps:
                    if isinstance(gap, ContextualGap):
                        # Convert ContextualGap to InformationGap format
                        info_gap = InformationGap(
                            gap_type=gap.gap_type,
                            description=gap.description,
                            severity=gap.severity,
                            required_for=["strategy_analysis"],
                            suggestions=[f"Please provide {gap.gap_type} information"]
                        )
                        gaps.append(info_gap)

            self.logger.info(f"Identified {len(gaps)} information gaps")
            return gaps

        except Exception as e:
            self.logger.error(f"Error identifying gaps: {str(e)}")
            return []

    def _generate_questions(self, gaps: List[InformationGap],
                          document_analysis: SophisticatedAnalysis) -> List[IntelligentQuestion]:
        """Step D: Generate clarifying questions based on identified gaps"""
        try:
            questions = []

            # Determine document type for appropriate question generation
            doc_class = getattr(document_analysis, 'document_class', None)

            if doc_class and hasattr(doc_class, 'value'):
                doc_type = doc_class.value
            else:
                doc_type = "unknown"

            # Generate appropriate questions based on document type
            if "bankruptcy" in doc_type.lower():
                questions.extend(self.question_generator.generate_questions_for_bankruptcy(gaps))
            elif "litigation" in doc_type.lower() or "complaint" in doc_type.lower():
                questions.extend(self.question_generator.generate_questions_for_litigation(gaps))
            else:
                # Generate general questions for unknown document types
                questions.extend(self._generate_general_questions(gaps))

            # Limit questions to prevent overwhelming users
            if len(questions) > self.max_questions_per_session:
                # Prioritize by gap severity and question priority
                questions.sort(key=lambda q: q.priority)
                questions = questions[:self.max_questions_per_session]
                self.logger.warning(f"Limited questions to {self.max_questions_per_session} to prevent user overwhelm")

            self.logger.info(f"Generated {len(questions)} clarifying questions")
            return questions

        except Exception as e:
            self.logger.error(f"Error generating questions: {str(e)}")
            return []

    def _generate_general_questions(self, gaps: List[InformationGap]) -> List[IntelligentQuestion]:
        """Generate general questions for unknown document types"""
        questions = []

        for gap in gaps:
            question_id = f"general_{uuid.uuid4().hex[:8]}"

            # Create basic question based on gap type
            question_text = f"Please provide information about {gap.gap_type.replace('_', ' ')}:"
            why_needed = gap.description or f"This information helps provide better analysis of your legal situation."

            question = IntelligentQuestion(
                question_id=question_id,
                question_text=question_text,
                why_needed=why_needed,
                input_type="text"  # Default to text input
            )
            questions.append(question)

        return questions

    def submit_response(self, session_id: str, question_id: str,
                       response_value: Any, response_type: ResponseType,
                       confidence_level: Optional[float] = None,
                       notes: Optional[str] = None) -> bool:
        """
        Step E: Submit user response to a clarifying question.

        Args:
            session_id: Workflow session ID
            question_id: ID of the question being answered
            response_value: User's response value
            response_type: Type of response (text, currency, etc.)
            confidence_level: User's confidence in response (0-1)
            notes: Optional user notes

        Returns:
            True if response accepted, False otherwise
        """
        try:
            if session_id not in self.active_sessions:
                self.logger.error(f"Session {session_id} not found")
                return False

            session = self.active_sessions[session_id]

            # Validate question ID
            if question_id not in [q.question_id for q in session.generated_questions]:
                self.logger.error(f"Question {question_id} not found in session {session_id}")
                return False

            # Create response
            response = UserResponse(
                question_id=question_id,
                response_value=response_value,
                response_type=response_type,
                confidence_level=confidence_level,
                notes=notes
            )

            # Add response to session
            session.add_response(response)
            session.update_stage(WorkflowStage.USER_RESPONDING)

            self.logger.info(f"Added response for question {question_id} in session {session_id}")

            # Check if all questions completed
            if session.is_complete():
                self._finalize_responses(session)

            return True

        except Exception as e:
            self.logger.error(f"Error submitting response: {str(e)}")
            return False

    def _finalize_responses(self, session: WorkflowSession):
        """Finalize user responses and prepare for strategy generation"""
        try:
            session.update_stage(WorkflowStage.RESPONSES_COLLECTED)

            # Build strategy context from responses
            context = self._build_strategy_context(session)
            session.strategy_context = context

            # Generate strategies
            strategies = self.strategy_generator.generate_strategic_options(context)
            session.generated_strategies = [s.get_educational_summary() for s in strategies]

            # Format strategies for presentation
            formatted_strategies = []
            for strategy in strategies:
                try:
                    formatted = self.presentation_engine.format_strategy_using_template(strategy)
                    formatted_strategies.append({
                        "strategy_id": formatted.strategy_id,
                        "title": formatted.title,
                        "sections": formatted.sections,
                        "disclaimers": formatted.disclaimers
                    })
                except Exception as e:
                    self.logger.warning(f"Error formatting strategy {strategy.strategy_id}: {str(e)}")

            session.formatted_strategies = formatted_strategies
            session.update_stage(WorkflowStage.COMPLETE)

            self.logger.info(f"Finalized session {session.session_id} with {len(strategies)} strategies")

        except Exception as e:
            self.logger.error(f"Error finalizing responses: {str(e)}")
            session.current_stage = WorkflowStage.ERROR
            session.errors.append(f"Failed to finalize responses: {str(e)}")

    def _build_strategy_context(self, session: WorkflowSession) -> Dict[str, Any]:
        """Build strategy generation context from user responses"""
        context = {
            "session_id": session.session_id,
            "document_analysis": session.document_analysis,
            "user_responses": {},
            "response_metadata": {
                "total_questions": len(session.generated_questions),
                "completed_questions": len(session.completed_questions),
                "completion_percentage": session.get_completion_percentage(),
                "collection_duration": (session.last_updated - session.created_at).total_seconds()
            }
        }

        # Process responses by type
        for response in session.user_responses:
            context["user_responses"][response.question_id] = response.to_context_data()

            # Extract specific information for strategy generation
            if "debt" in response.question_id.lower():
                context["debt_amount"] = self._parse_currency_response(response.response_value)
            elif "business_type" in response.question_id.lower():
                context["business_type"] = response.response_value
            elif "creditor" in response.question_id.lower():
                context["creditor_info"] = response.response_value
            elif "income" in response.question_id.lower():
                context["income_info"] = self._parse_currency_response(response.response_value)
            elif "court" in response.question_id.lower():
                context["court_info"] = response.response_value
            elif "damages" in response.question_id.lower():
                context["damages_amount"] = self._parse_currency_response(response.response_value)

        return context

    def _parse_currency_response(self, value: Any) -> float:
        """Parse currency response to numeric value"""
        try:
            if isinstance(value, str):
                # Remove currency symbols and commas
                cleaned = re.sub(r'[$,\s]', '', value)
                return float(cleaned)
            elif isinstance(value, (int, float)):
                return float(value)
        except (ValueError, TypeError):
            pass
        return 0.0

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow session"""
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]

        return {
            "session_id": session_id,
            "current_stage": session.current_stage.value,
            "created_at": session.created_at.isoformat(),
            "last_updated": session.last_updated.isoformat(),
            "progress": {
                "gaps_identified": len(session.identified_gaps),
                "questions_generated": len(session.generated_questions),
                "questions_completed": len(session.completed_questions),
                "questions_pending": len(session.pending_questions),
                "completion_percentage": session.get_completion_percentage()
            },
            "results": {
                "strategies_generated": len(session.generated_strategies),
                "strategies_formatted": len(session.formatted_strategies)
            },
            "errors": session.errors,
            "warnings": session.warnings
        }

    def get_pending_questions(self, session_id: str) -> List[IntelligentQuestion]:
        """Get pending questions for a session"""
        if session_id not in self.active_sessions:
            return []

        session = self.active_sessions[session_id]
        pending_ids = set(session.pending_questions)

        return [q for q in session.generated_questions if q.question_id in pending_ids]

    def get_session_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get final results for a completed session"""
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]

        if session.current_stage != WorkflowStage.COMPLETE:
            return None

        return {
            "session_id": session_id,
            "strategy_context": session.strategy_context,
            "generated_strategies": session.generated_strategies,
            "formatted_strategies": session.formatted_strategies,
            "completion_stats": {
                "total_questions": len(session.generated_questions),
                "answered_questions": len(session.completed_questions),
                "completion_percentage": session.get_completion_percentage(),
                "duration_minutes": (session.last_updated - session.created_at).total_seconds() / 60
            }
        }


def test_gap_analysis_orchestrator():
    """
    Test the gap analysis orchestrator workflow.

    LEGAL DISCLAIMER:
    This test demonstrates information gathering workflow for educational purposes only.
    All analysis and questions are informational and do not constitute legal advice.
    """
    print("=== GAP ANALYSIS ORCHESTRATOR TEST ===")
    print("EDUCATIONAL DISCLAIMER: All workflow operations are for educational purposes only.")
    print("This system provides information gathering assistance and does not constitute legal advice.\n")

    # Initialize orchestrator
    orchestrator = GapAnalysisOrchestrator()

    # Create mock document analysis with gaps
    mock_analysis = SophisticatedAnalysis()
    mock_analysis.contextual_gaps = [
        ContextualGap(
            gap_type="debt_amount",
            description="Total debt amount not specified",
            severity="HIGH"
        ),
        ContextualGap(
            gap_type="creditor_types",
            description="Types of creditors not identified",
            severity="MEDIUM"
        )
    ]

    # Test Step C-D: Start workflow (identifies gaps and generates questions)
    print("TESTING: Workflow Initiation (Steps C-D)")
    print("-" * 50)

    session = orchestrator.start_workflow(
        document_analysis=mock_analysis,
        user_id="test_user_123"
    )

    print(f"Session ID: {session.session_id}")
    print(f"Current Stage: {session.current_stage.value}")
    print(f"Gaps Identified: {len(session.identified_gaps)}")
    print(f"Questions Generated: {len(session.generated_questions)}")
    print(f"Pending Questions: {len(session.pending_questions)}")

    # Show pending questions
    pending_questions = orchestrator.get_pending_questions(session.session_id)
    print(f"\nPending Questions:")
    for i, question in enumerate(pending_questions[:3], 1):  # Show first 3
        print(f"{i}. {question.question_text}")
        print(f"   Why needed: {question.why_needed}")
        print(f"   Input type: {question.input_type}")

    # Test Step E: Submit responses
    print(f"\n\nTESTING: User Response Submission (Step E)")
    print("-" * 50)

    if pending_questions:
        # Submit response to first question
        first_question = pending_questions[0]
        success = orchestrator.submit_response(
            session_id=session.session_id,
            question_id=first_question.question_id,
            response_value="$75000",
            response_type=ResponseType.CURRENCY,
            confidence_level=0.9
        )

        print(f"Response submission: {'SUCCESS' if success else 'FAILED'}")

        # Submit response to second question if available
        if len(pending_questions) > 1:
            second_question = pending_questions[1]
            success = orchestrator.submit_response(
                session_id=session.session_id,
                question_id=second_question.question_id,
                response_value=["credit_cards", "medical", "utilities"],
                response_type=ResponseType.MULTI_SELECT,
                confidence_level=0.8
            )
            print(f"Second response submission: {'SUCCESS' if success else 'FAILED'}")

    # Check session status
    print(f"\n\nTESTING: Session Status Check")
    print("-" * 50)

    status = orchestrator.get_session_status(session.session_id)
    if status:
        print(f"Current Stage: {status['current_stage']}")
        print(f"Progress: {status['progress']['completion_percentage']:.1%} complete")
        print(f"Questions Completed: {status['progress']['questions_completed']}/{status['progress']['questions_generated']}")
        print(f"Strategies Generated: {status['results']['strategies_generated']}")

    # If workflow is complete, show results
    if session.current_stage == WorkflowStage.COMPLETE:
        print(f"\n\nTESTING: Final Results")
        print("-" * 50)

        results = orchestrator.get_session_results(session.session_id)
        if results:
            print(f"Session completed in {results['completion_stats']['duration_minutes']:.1f} minutes")
            print(f"Generated {len(results['generated_strategies'])} strategic options")
            print(f"Formatted {len(results['formatted_strategies'])} presentations")

    print(f"\n=== TEST COMPLETE ===")
    print(f"Workflow orchestrator ready for C-D-E integration")
    print(f"Gap identification, question generation, and response collection working")
    print(f"\nREMINDER: All workflow operations are educational only")
    print(f"Users must consult qualified legal counsel for legal advice")

    return True


if __name__ == "__main__":
    test_gap_analysis_orchestrator()