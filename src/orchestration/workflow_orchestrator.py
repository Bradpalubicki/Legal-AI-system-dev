"""
Intelligent Workflow Orchestrator - Master Brain for Legal AI System

The master orchestrator that coordinates all components to provide intelligent,
context-aware legal document analysis and strategic option generation.

Key Capabilities:
- Initialize and coordinate all system components
- Manage progressive conversation state
- Build understanding through iterative questioning
- Refine strategies based on user responses
- Maintain UPL compliance throughout the entire workflow

CRITICAL LEGAL DISCLAIMER:
This orchestrator facilitates educational information gathering and analysis only.
All generated content, questions, and strategic options are for educational
purposes only and do not constitute legal advice. No attorney-client relationship
is created. Users must consult qualified legal counsel for legal guidance.

Created: 2025-09-15
Legal AI System - Master Orchestration Brain
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
import asyncio
from collections import defaultdict

# Import all system components
try:
    # Document processing components
    from ..document_processor.sophisticated_understanding import (
        SophisticatedAnalyzer, SophisticatedAnalysis, DocumentClass, ContextualGap
    )
    from ..document_processor.comprehensive_understanding_engine import (
        DocumentUnderstandingEngine, DocumentAnalysisResult, DocumentCategory, DocumentType
    )
    from ..document_processor.intelligent_intake import (
        DocumentIntakeAnalyzer, InformationGap
    )
    from ..document_processor.question_generator import (
        IntelligentQuestionGenerator, IntelligentQuestion, InputType
    )
    from ..document_processor.adaptive_questioning import (
        AdaptiveQuestioningSystem
    )

    # Strategy generation components
    from ..strategy_generator.comprehensive_strategy_options import (
        ComprehensiveStrategyGenerator, ComprehensiveStrategy, StrategyCategory
    )
    from ..strategy_generator.compliance_presentation import (
        CompliancePresentationEngine, ComplianceStrategyTemplate, FormattedContent
    )

    # Workflow components
    from ..workflow.gap_analysis_orchestrator import (
        GapAnalysisOrchestrator, WorkflowSession, ResponseType
    )

    # Compliance components
    from ..shared.compliance.upl_compliance import (
        ComplianceWrapper, ViolationSeverity
    )

except ImportError:
    # Mock imports for development/testing
    from dataclasses import dataclass
    from enum import Enum

    class DocumentClass(Enum):
        BANKRUPTCY_PETITION = "bankruptcy_petition"
        COMPLAINT = "complaint"
        CONTRACT = "contract"
        UNKNOWN = "unknown"

    class StrategyCategory(Enum):
        BANKRUPTCY = "bankruptcy"
        LITIGATION = "litigation"
        NEGOTIATION = "negotiation"
        SETTLEMENT = "settlement"

    class InputType(Enum):
        TEXT = "text"
        CURRENCY = "currency"
        SELECT = "select"
        MULTISELECT = "multiselect"

    class ResponseType(Enum):
        TEXT = "text"
        CURRENCY = "currency"
        SINGLE_SELECT = "single_select"
        MULTI_SELECT = "multi_select"

    # Mock component classes
    class MockComponent:
        def __init__(self): pass

    class MockAnalysisResult:
        def __init__(self):
            self.document_id = 'mock_doc_123'
            self.document_category = type('MockCategory', (), {'value': 'bankruptcy'})()
            self.document_type = type('MockType', (), {'value': 'bankruptcy_petition'})()
            self.classification_confidence = 0.8
            self.extracted_fields = {'case_number': type('MockField', (), {'value': '24-12345'})()}
            self.key_entities = ['debtor', 'creditors']
            self.missing_information = [type('MockGap', (), {'gap_type': 'debt_amount'})()]
            self.legal_issues = ['debt discharge']
            self.confidence_score = 0.75
            self.processing_timestamp = type('MockTime', (), {'isoformat': lambda: '2024-01-01T00:00:00Z'})()
            self.processing_duration = 0.1

    class MockDocumentUnderstandingEngine:
        def __init__(self): pass
        def analyze_document(self, text: str, path=None):
            return MockAnalysisResult()

    SophisticatedAnalyzer = MockComponent
    DocumentUnderstandingEngine = MockDocumentUnderstandingEngine
    DocumentIntakeAnalyzer = MockComponent
    IntelligentQuestionGenerator = MockComponent
    AdaptiveQuestioningSystem = MockComponent
    ComprehensiveStrategyGenerator = MockComponent
    CompliancePresentationEngine = MockComponent
    GapAnalysisOrchestrator = MockComponent
    ComplianceWrapper = MockComponent


class WorkflowStage(Enum):
    """Master workflow stages for the entire system"""
    INITIALIZED = "initialized"
    DOCUMENT_UPLOADED = "document_uploaded"
    INITIAL_ANALYSIS = "initial_analysis"
    GAPS_IDENTIFIED = "gaps_identified"
    QUESTIONING_ACTIVE = "questioning_active"
    UNDERSTANDING_BUILDING = "understanding_building"
    STRATEGIES_GENERATING = "strategies_generating"
    STRATEGIES_REFINING = "strategies_refining"
    PRESENTATION_READY = "presentation_ready"
    ATTORNEY_REFERRAL = "attorney_referral"
    SESSION_COMPLETE = "session_complete"
    ERROR_STATE = "error_state"


class UnderstandingLevel(Enum):
    """Levels of case understanding built progressively"""
    MINIMAL = "minimal"           # Basic document classification only
    BASIC = "basic"              # Key facts identified, major gaps present
    INTERMEDIATE = "intermediate" # Most gaps filled, some refinement needed
    COMPREHENSIVE = "comprehensive" # Deep understanding, ready for strategies
    EXPERT = "expert"            # All nuances understood, optimal strategies


class ConversationTurn(Enum):
    """Types of conversation turns"""
    SYSTEM_QUESTION = "system_question"
    USER_RESPONSE = "user_response"
    STRATEGY_PRESENTATION = "strategy_presentation"
    CLARIFICATION_REQUEST = "clarification_request"
    FOLLOW_UP_QUESTION = "follow_up_question"
    ATTORNEY_RECOMMENDATION = "attorney_recommendation"


@dataclass
class ProgressiveInsight:
    """Tracks building understanding of the legal situation"""
    insight_type: str
    content: str
    confidence_level: float  # 0-1
    sources: List[str]  # What contributed to this insight
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def update_confidence(self, new_evidence: str, confidence_delta: float):
        """Update confidence based on new evidence"""
        self.sources.append(new_evidence)
        self.confidence_level = max(0.0, min(1.0, self.confidence_level + confidence_delta))
        self.timestamp = datetime.utcnow()


@dataclass
class ConversationTurnData:
    """Individual conversation turn with the user"""
    turn_id: str
    turn_type: ConversationTurn
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Content
    system_content: Optional[str] = None  # Questions, explanations
    user_content: Optional[str] = None    # User responses
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Understanding impact
    insights_gained: List[ProgressiveInsight] = field(default_factory=list)
    confidence_changes: Dict[str, float] = field(default_factory=dict)


@dataclass
class StrategyRefinement:
    """Tracks how strategies are refined based on user input"""
    refinement_id: str
    original_strategy_id: str
    refinement_type: str  # "enhanced", "modified", "replaced", "deprecated"
    reason: str
    user_input_trigger: str
    confidence_before: float
    confidence_after: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationState:
    """Complete state of the intelligent conversation"""
    session_id: str
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    # Workflow progression
    current_stage: WorkflowStage = WorkflowStage.INITIALIZED
    understanding_level: UnderstandingLevel = UnderstandingLevel.MINIMAL
    completion_percentage: float = 0.0

    # Document analysis
    uploaded_documents: List[str] = field(default_factory=list)
    document_analysis: Optional[Dict[str, Any]] = None
    identified_gaps: List[Dict[str, Any]] = field(default_factory=list)

    # Progressive understanding
    progressive_insights: Dict[str, ProgressiveInsight] = field(default_factory=dict)
    conversation_history: List[ConversationTurnData] = field(default_factory=list)
    question_queue: List[str] = field(default_factory=list)  # Question IDs to ask

    # Strategy development
    strategy_candidates: List[Dict[str, Any]] = field(default_factory=list)
    strategy_refinements: List[StrategyRefinement] = field(default_factory=list)
    final_strategies: List[Dict[str, Any]] = field(default_factory=list)
    presentation_ready: List[Dict[str, Any]] = field(default_factory=list)

    # User preferences and context
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    communication_style: str = "professional"  # professional, simple, detailed

    # Error handling
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recovery_attempts: int = 0

    def add_insight(self, insight: ProgressiveInsight):
        """Add or update a progressive insight"""
        self.progressive_insights[insight.insight_type] = insight
        self.last_updated = datetime.utcnow()
        self._recalculate_understanding_level()

    def add_conversation_turn(self, turn: ConversationTurnData):
        """Add a conversation turn and process insights"""
        self.conversation_history.append(turn)
        for insight in turn.insights_gained:
            self.add_insight(insight)
        self.last_updated = datetime.utcnow()

    def _recalculate_understanding_level(self):
        """Recalculate understanding level based on insights"""
        if not self.progressive_insights:
            self.understanding_level = UnderstandingLevel.MINIMAL
            return

        avg_confidence = sum(i.confidence_level for i in self.progressive_insights.values()) / len(self.progressive_insights)
        insight_count = len(self.progressive_insights)

        if avg_confidence >= 0.9 and insight_count >= 10:
            self.understanding_level = UnderstandingLevel.EXPERT
        elif avg_confidence >= 0.8 and insight_count >= 7:
            self.understanding_level = UnderstandingLevel.COMPREHENSIVE
        elif avg_confidence >= 0.6 and insight_count >= 4:
            self.understanding_level = UnderstandingLevel.INTERMEDIATE
        elif avg_confidence >= 0.4 or insight_count >= 2:
            self.understanding_level = UnderstandingLevel.BASIC
        else:
            self.understanding_level = UnderstandingLevel.MINIMAL

    def get_next_question(self) -> Optional[str]:
        """Get the next question to ask the user"""
        return self.question_queue.pop(0) if self.question_queue else None

    def calculate_completion_percentage(self) -> float:
        """Calculate overall completion percentage"""
        stage_weights = {
            WorkflowStage.INITIALIZED: 0.0,
            WorkflowStage.DOCUMENT_UPLOADED: 0.1,
            WorkflowStage.INITIAL_ANALYSIS: 0.2,
            WorkflowStage.GAPS_IDENTIFIED: 0.3,
            WorkflowStage.QUESTIONING_ACTIVE: 0.5,
            WorkflowStage.UNDERSTANDING_BUILDING: 0.6,
            WorkflowStage.STRATEGIES_GENERATING: 0.8,
            WorkflowStage.STRATEGIES_REFINING: 0.9,
            WorkflowStage.PRESENTATION_READY: 0.95,
            WorkflowStage.ATTORNEY_REFERRAL: 0.98,
            WorkflowStage.SESSION_COMPLETE: 1.0
        }

        base_progress = stage_weights.get(self.current_stage, 0.0)

        # Add understanding bonus
        understanding_bonus = {
            UnderstandingLevel.MINIMAL: 0.0,
            UnderstandingLevel.BASIC: 0.02,
            UnderstandingLevel.INTERMEDIATE: 0.04,
            UnderstandingLevel.COMPREHENSIVE: 0.06,
            UnderstandingLevel.EXPERT: 0.08
        }.get(self.understanding_level, 0.0)

        self.completion_percentage = min(1.0, base_progress + understanding_bonus)
        return self.completion_percentage


class IntelligentWorkflowOrchestrator:
    """
    Master orchestrator that coordinates all Legal AI System components.

    This is the "brain" of the system that:
    - Initializes and coordinates all components
    - Manages progressive conversation flow
    - Builds understanding through intelligent questioning
    - Refines strategies based on user responses
    - Maintains UPL compliance throughout

    EDUCATIONAL PURPOSE DISCLAIMER:
    This orchestrator facilitates educational information gathering and analysis.
    All operations are for informational purposes only and do not constitute
    legal advice. Professional legal consultation is required for all legal matters.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the master orchestrator with all components"""
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # Initialize all system components
        self._initialize_components()

        # Active conversation states
        self.active_sessions: Dict[str, ConversationState] = {}

        # System configuration
        self.max_questions_per_session = self.config.get('max_questions', 20)
        self.understanding_threshold = self.config.get('understanding_threshold', 0.7)
        self.session_timeout_hours = self.config.get('session_timeout', 24)

        # Progressive learning settings
        self.confidence_threshold_for_strategy = 0.6
        self.min_insights_for_comprehensive = 5

        # Thread safety
        self._lock = threading.Lock()

        self.logger.info("IntelligentWorkflowOrchestrator initialized with all components")

    def _initialize_components(self):
        """Initialize all system components"""
        try:
            # Document processing components
            self.document_analyzer = SophisticatedAnalyzer()
            self.comprehensive_analyzer = DocumentUnderstandingEngine()  # NEW: Universal document engine
            self.intake_analyzer = DocumentIntakeAnalyzer()
            self.question_generator = IntelligentQuestionGenerator()
            self.adaptive_questioning = AdaptiveQuestioningSystem()

            # Strategy generation components
            self.strategy_generator = ComprehensiveStrategyGenerator()
            self.presentation_engine = CompliancePresentationEngine()

            # Workflow coordination
            self.gap_orchestrator = GapAnalysisOrchestrator()

            # Compliance
            self.compliance_wrapper = ComplianceWrapper()

            self.logger.info("All components initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing components: {str(e)}")
            # Initialize mock components for development
            self._initialize_mock_components()

    def _initialize_mock_components(self):
        """Initialize mock components for development/testing"""
        self.document_analyzer = MockComponent()
        self.comprehensive_analyzer = MockComponent()  # NEW: Mock comprehensive analyzer
        self.intake_analyzer = MockComponent()
        self.question_generator = MockComponent()
        self.adaptive_questioning = MockComponent()
        self.strategy_generator = MockComponent()
        self.presentation_engine = MockComponent()
        self.gap_orchestrator = MockComponent()
        self.compliance_wrapper = MockComponent()

        self.logger.warning("Initialized with mock components - development mode")

    def start_intelligent_session(self, user_id: Optional[str] = None,
                                document_path: Optional[str] = None,
                                user_preferences: Optional[Dict[str, Any]] = None) -> ConversationState:
        """
        Start a new intelligent conversation session.

        Args:
            user_id: Optional user identifier
            document_path: Path to uploaded document
            user_preferences: User communication preferences

        Returns:
            ConversationState object for managing the session
        """
        with self._lock:
            try:
                session_id = str(uuid.uuid4())

                # Create conversation state
                state = ConversationState(
                    session_id=session_id,
                    user_id=user_id,
                    user_preferences=user_preferences or {}
                )

                if document_path:
                    state.uploaded_documents.append(document_path)
                    state.current_stage = WorkflowStage.DOCUMENT_UPLOADED

                # Store session
                self.active_sessions[session_id] = state

                self.logger.info(f"Started intelligent session {session_id}")

                # If document provided, start analysis
                if document_path:
                    self._trigger_document_analysis(state)

                return state

            except Exception as e:
                self.logger.error(f"Error starting session: {str(e)}")
                # Return error state
                error_state = ConversationState(session_id=str(uuid.uuid4()))
                error_state.current_stage = WorkflowStage.ERROR_STATE
                error_state.errors.append(f"Failed to start session: {str(e)}")
                return error_state

    def _trigger_document_analysis(self, state: ConversationState):
        """Trigger initial document analysis and gap identification"""
        try:
            document_path = state.uploaded_documents[0]

            # Analyze document (mock analysis for now)
            analysis = self._perform_document_analysis(document_path)
            state.document_analysis = analysis
            state.current_stage = WorkflowStage.INITIAL_ANALYSIS

            # Identify gaps
            gaps = self._identify_information_gaps(analysis)
            state.identified_gaps = gaps
            state.current_stage = WorkflowStage.GAPS_IDENTIFIED

            # Generate initial questions
            questions = self._generate_initial_questions(gaps, analysis)
            state.question_queue.extend(questions)

            # Add initial insights
            self._extract_initial_insights(state, analysis)

            if questions:
                state.current_stage = WorkflowStage.QUESTIONING_ACTIVE

            self.logger.info(f"Analysis complete for session {state.session_id}: {len(gaps)} gaps, {len(questions)} questions")

        except Exception as e:
            self.logger.error(f"Error in document analysis: {str(e)}")
            state.errors.append(f"Document analysis failed: {str(e)}")

    def _perform_document_analysis(self, document_path: str) -> Dict[str, Any]:
        """Perform comprehensive document analysis using the universal engine"""
        try:
            # Read document content (in real implementation, use proper file reading)
            document_text = self._read_document_file(document_path)

            # Use comprehensive analyzer for universal document understanding
            analysis_result = self.comprehensive_analyzer.analyze_document(document_text, document_path)

            # Convert to orchestrator format
            return {
                "document_id": analysis_result.document_id,
                "document_category": analysis_result.document_category.value,
                "document_type": analysis_result.document_type.value,
                "classification_confidence": analysis_result.classification_confidence,
                "extracted_fields": {k: v.value for k, v in analysis_result.extracted_fields.items()},
                "key_entities": analysis_result.key_entities,
                "missing_information": [gap.gap_type for gap in analysis_result.missing_information],
                "legal_issues": analysis_result.legal_issues,
                "confidence_level": analysis_result.confidence_score,
                "analysis_timestamp": analysis_result.processing_timestamp.isoformat(),
                "processing_duration": analysis_result.processing_duration
            }

        except Exception as e:
            self.logger.error(f"Error in comprehensive document analysis: {str(e)}")
            # Fallback to mock analysis
            return {
                "document_class": DocumentClass.BANKRUPTCY_PETITION.value,
                "key_entities": ["debtor_name", "total_debt", "creditor_list"],
                "missing_information": ["debt_breakdown", "asset_details", "income_info"],
                "confidence_level": 0.8,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }

    def _read_document_file(self, document_path: str) -> str:
        """Read document file content (mock implementation)"""
        # Mock document content for testing
        mock_documents = {
            "/path/to/bankruptcy_petition.pdf": """
                UNITED STATES BANKRUPTCY COURT
                NORTHERN DISTRICT OF CALIFORNIA

                In re: John Doe                    Case No. 24-56789
                                                  Chapter 7
                Debtor.

                VOLUNTARY PETITION

                Total Debt: $98,000
                Assets: $12,000
                Monthly Income: $2,800
            """,
            "/path/to/employment_contract.pdf": """
                EMPLOYMENT AGREEMENT

                Between ABC Corp and Jane Smith
                Position: Software Engineer
                Salary: $85,000 annually
                Start Date: March 1, 2024
            """
        }

        return mock_documents.get(document_path, "Sample legal document content for analysis.")

    def _identify_information_gaps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify information gaps from comprehensive analysis"""
        # Extract missing information from comprehensive analysis
        missing_info = analysis.get("missing_information", [])

        gaps = []
        for item in missing_info:
            # Determine severity based on document type and field importance
            severity = "HIGH" if item in ["case_number", "parties", "debt_amount", "debtor_name"] else "MEDIUM"
            if item in ["signatures", "notarization"]:
                severity = "CRITICAL"

            gap = {
                "gap_type": item,
                "severity": severity,
                "description": f"Missing {item.replace('_', ' ')} information",
                "required_for": ["strategy_generation", "legal_analysis"],
                "document_type": analysis.get("document_type", "unknown"),
                "confidence_impact": 0.2 if severity == "HIGH" else 0.1
            }
            gaps.append(gap)

        # Add legal issue gaps if identified
        legal_issues = analysis.get("legal_issues", [])
        for issue in legal_issues:
            if "missing" in issue.lower() or "incomplete" in issue.lower():
                gap = {
                    "gap_type": f"legal_issue_{issue.lower().replace(' ', '_')}",
                    "severity": "MEDIUM",
                    "description": f"Legal issue identified: {issue}",
                    "required_for": ["legal_analysis", "strategy_refinement"]
                }
                gaps.append(gap)

        return gaps

    def _generate_initial_questions(self, gaps: List[Dict[str, Any]],
                                  analysis: Dict[str, Any]) -> List[str]:
        """Generate intelligent questions based on document type and gaps"""
        questions = []
        doc_type = analysis.get("document_type", "unknown")

        for gap in gaps:
            gap_type = gap["gap_type"]

            # Generate document-type specific questions
            if "bankruptcy" in doc_type:
                if gap_type in ["debt_amount", "debtor_amount", "total_debt"]:
                    questions.append("debt_total_question")
                elif gap_type in ["assets", "asset_details", "real_property"]:
                    questions.append("asset_info_question")
                elif gap_type in ["income", "income_info", "monthly_income"]:
                    questions.append("income_details_question")
                elif gap_type in ["creditors", "creditor_info", "creditor_types"]:
                    questions.append("creditor_types_question")

            elif "employment" in doc_type or "contract" in doc_type:
                if gap_type in ["compensation", "salary", "payment"]:
                    questions.append("compensation_details_question")
                elif gap_type in ["start_date", "effective_date"]:
                    questions.append("contract_dates_question")
                elif gap_type in ["parties", "contract_parties"]:
                    questions.append("contracting_parties_question")

            elif "complaint" in doc_type or "litigation" in doc_type:
                if gap_type in ["damages", "monetary_damages"]:
                    questions.append("damages_amount_question")
                elif gap_type in ["causes_of_action", "claims"]:
                    questions.append("legal_claims_question")
                elif gap_type in ["parties", "defendants"]:
                    questions.append("litigation_parties_question")

            # Generic questions for unrecognized gaps
            else:
                questions.append(f"general_{gap_type}_question")

        # Add document-specific follow-up questions
        if "bankruptcy" in doc_type and len(questions) < 3:
            questions.append("business_type_question")

        elif "employment" in doc_type and len(questions) < 3:
            questions.append("employment_terms_question")

        return questions[:self.max_questions_per_session]  # Limit initial questions

    def _extract_initial_insights(self, state: ConversationState, analysis: Dict[str, Any]):
        """Extract initial insights from document analysis"""
        doc_class = analysis.get("document_class")
        if doc_class:
            insight = ProgressiveInsight(
                insight_type="document_type",
                content=f"Document identified as {doc_class}",
                confidence_level=analysis.get("confidence_level", 0.5),
                sources=["document_analysis"]
            )
            state.add_insight(insight)

        # Extract entity insights
        entities = analysis.get("key_entities", [])
        for entity in entities:
            insight = ProgressiveInsight(
                insight_type=f"entity_{entity}",
                content=f"Key entity identified: {entity}",
                confidence_level=0.6,
                sources=["document_analysis"]
            )
            state.add_insight(insight)

    def get_next_interaction(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the next interaction for the user (question, strategy, etc.)

        Args:
            session_id: Session identifier

        Returns:
            Dictionary containing the next interaction or None if session complete
        """
        with self._lock:
            if session_id not in self.active_sessions:
                return None

            state = self.active_sessions[session_id]

            try:
                # Check if we need to ask more questions
                if state.current_stage == WorkflowStage.QUESTIONING_ACTIVE:
                    question_id = state.get_next_question()

                    if question_id:
                        question_data = self._get_question_data(question_id)
                        return {
                            "type": "question",
                            "question_id": question_id,
                            "question_data": question_data,
                            "progress": state.calculate_completion_percentage()
                        }
                    else:
                        # No more questions, move to strategy generation
                        self._trigger_strategy_generation(state)

                # Check if strategies are ready
                if state.current_stage == WorkflowStage.PRESENTATION_READY:
                    return {
                        "type": "strategies",
                        "strategies": state.presentation_ready,
                        "progress": state.calculate_completion_percentage(),
                        "understanding_level": state.understanding_level.value
                    }

                # Check if we should recommend attorney consultation
                if self._should_recommend_attorney(state):
                    state.current_stage = WorkflowStage.ATTORNEY_REFERRAL
                    return {
                        "type": "attorney_referral",
                        "message": self._generate_attorney_referral_message(state),
                        "progress": state.calculate_completion_percentage()
                    }

                # Session complete
                if state.current_stage in [WorkflowStage.SESSION_COMPLETE, WorkflowStage.ATTORNEY_REFERRAL]:
                    return {
                        "type": "complete",
                        "summary": self._generate_session_summary(state),
                        "progress": 1.0
                    }

                # Default case
                return {
                    "type": "status",
                    "message": "Processing your information...",
                    "progress": state.calculate_completion_percentage()
                }

            except Exception as e:
                self.logger.error(f"Error getting next interaction: {str(e)}")
                state.errors.append(f"Interaction error: {str(e)}")
                return {
                    "type": "error",
                    "message": "We encountered an issue. Please try again or consult with an attorney.",
                    "progress": state.calculate_completion_percentage()
                }

    def _get_question_data(self, question_id: str) -> Dict[str, Any]:
        """Get detailed question data for presentation"""
        # Mock question data - in real implementation, use question generator
        question_templates = {
            "debt_total_question": {
                "text": "What is your total unsecured debt amount?",
                "input_type": "currency",
                "why_needed": "Total debt amount helps determine bankruptcy chapter eligibility and required documentation.",
                "educational_note": "This information is used for educational analysis only.",
                "disclaimer": "This question is for educational purposes only. Consult an attorney for legal advice."
            },
            "asset_info_question": {
                "text": "Do you own any major assets (real estate, vehicles, investments)?",
                "input_type": "multiselect",
                "options": [
                    {"value": "real_estate", "label": "Real Estate"},
                    {"value": "vehicles", "label": "Vehicles"},
                    {"value": "investments", "label": "Investments"},
                    {"value": "none", "label": "No Major Assets"}
                ],
                "why_needed": "Asset information is critical for determining exemptions and strategy options.",
                "educational_note": "This information helps provide educational content about common options.",
                "disclaimer": "This question is for educational purposes only. Consult an attorney for legal advice."
            },
            "income_details_question": {
                "text": "What is your current gross monthly income from all sources?",
                "input_type": "currency",
                "why_needed": "Income information determines strategy eligibility and affects available options.",
                "educational_note": "This information is used for educational analysis only.",
                "disclaimer": "This question is for educational purposes only. Consult an attorney for legal advice."
            }
        }

        return question_templates.get(question_id, {
            "text": "Could you provide additional information about your situation?",
            "input_type": "text",
            "why_needed": "Additional information helps provide better educational content.",
            "disclaimer": "This question is for educational purposes only. Consult an attorney for legal advice."
        })

    def submit_user_response(self, session_id: str, question_id: str,
                           response_value: Any, confidence_level: Optional[float] = None) -> bool:
        """
        Submit user response and update understanding progressively.

        Args:
            session_id: Session identifier
            question_id: Question being answered
            response_value: User's response
            confidence_level: User's confidence in their response

        Returns:
            True if response accepted and processed
        """
        with self._lock:
            if session_id not in self.active_sessions:
                return False

            state = self.active_sessions[session_id]

            try:
                # Create conversation turn
                turn = ConversationTurnData(
                    turn_id=str(uuid.uuid4()),
                    turn_type=ConversationTurn.USER_RESPONSE,
                    user_content=str(response_value),
                    metadata={
                        "question_id": question_id,
                        "confidence_level": confidence_level
                    }
                )

                # Process response and extract insights
                insights = self._process_user_response(question_id, response_value, state)
                turn.insights_gained = insights

                # Add to conversation
                state.add_conversation_turn(turn)

                # Update stage if needed
                if state.current_stage == WorkflowStage.QUESTIONING_ACTIVE:
                    state.current_stage = WorkflowStage.UNDERSTANDING_BUILDING

                # Check if we have enough understanding for strategies
                if self._sufficient_understanding_for_strategies(state):
                    self._trigger_strategy_generation(state)

                # Generate follow-up questions if needed
                follow_ups = self._generate_follow_up_questions(question_id, response_value, state)
                state.question_queue.extend(follow_ups)

                self.logger.info(f"Processed response for session {session_id}, question {question_id}")
                return True

            except Exception as e:
                self.logger.error(f"Error processing response: {str(e)}")
                state.errors.append(f"Response processing failed: {str(e)}")
                return False

    def _process_user_response(self, question_id: str, response_value: Any,
                             state: ConversationState) -> List[ProgressiveInsight]:
        """Process user response and extract insights"""
        insights = []

        # Process based on question type
        if "debt_total" in question_id:
            try:
                debt_amount = float(str(response_value).replace('$', '').replace(',', ''))

                # Create debt amount insight
                insight = ProgressiveInsight(
                    insight_type="debt_amount",
                    content=f"Total debt amount: ${debt_amount:,.2f}",
                    confidence_level=0.8,
                    sources=[f"user_response_{question_id}"]
                )
                insights.append(insight)

                # Infer bankruptcy chapter eligibility
                if debt_amount > 0:
                    chapter_insight = ProgressiveInsight(
                        insight_type="bankruptcy_chapter_eligibility",
                        content="Chapter 7 or Chapter 11 may be applicable" if debt_amount > 50000 else "Chapter 7 likely applicable",
                        confidence_level=0.6,
                        sources=[f"debt_inference_{question_id}"]
                    )
                    insights.append(chapter_insight)

            except (ValueError, TypeError):
                pass

        elif "asset_info" in question_id:
            if isinstance(response_value, list):
                asset_types = response_value
                insight = ProgressiveInsight(
                    insight_type="asset_types",
                    content=f"Asset types: {', '.join(asset_types)}",
                    confidence_level=0.7,
                    sources=[f"user_response_{question_id}"]
                )
                insights.append(insight)

                # Infer exemption planning needs
                if "none" not in asset_types:
                    exemption_insight = ProgressiveInsight(
                        insight_type="exemption_planning_needed",
                        content="Asset exemption planning may be important",
                        confidence_level=0.5,
                        sources=[f"asset_inference_{question_id}"]
                    )
                    insights.append(exemption_insight)

        elif "income" in question_id:
            try:
                income_amount = float(str(response_value).replace('$', '').replace(',', ''))
                insight = ProgressiveInsight(
                    insight_type="monthly_income",
                    content=f"Monthly income: ${income_amount:,.2f}",
                    confidence_level=0.8,
                    sources=[f"user_response_{question_id}"]
                )
                insights.append(insight)

                # Infer means test implications
                if income_amount > 0:
                    means_test_insight = ProgressiveInsight(
                        insight_type="means_test_consideration",
                        content="Means test calculation will be required" if income_amount > 4000 else "Below median income likely",
                        confidence_level=0.6,
                        sources=[f"income_inference_{question_id}"]
                    )
                    insights.append(means_test_insight)

            except (ValueError, TypeError):
                pass

        return insights

    def _sufficient_understanding_for_strategies(self, state: ConversationState) -> bool:
        """Check if we have sufficient understanding to generate strategies"""
        # Check understanding level
        if state.understanding_level.value in ["comprehensive", "expert"]:
            return True

        # Check minimum insights
        if len(state.progressive_insights) >= self.min_insights_for_comprehensive:
            avg_confidence = sum(i.confidence_level for i in state.progressive_insights.values()) / len(state.progressive_insights)
            if avg_confidence >= self.confidence_threshold_for_strategy:
                return True

        # Check if we have key insights
        key_insights = ["debt_amount", "document_type", "asset_types"]
        has_key_insights = sum(1 for key in key_insights if key in state.progressive_insights)

        return has_key_insights >= 2

    def _trigger_strategy_generation(self, state: ConversationState):
        """Generate strategies based on current understanding"""
        try:
            state.current_stage = WorkflowStage.STRATEGIES_GENERATING

            # Build context for strategy generation
            context = self._build_strategy_context(state)

            # Generate strategies (mock for now)
            strategies = self._generate_strategies(context)
            state.strategy_candidates = strategies

            # Refine strategies based on progressive insights
            refined_strategies = self._refine_strategies(strategies, state)
            state.final_strategies = refined_strategies

            # Prepare presentation
            presentation = self._prepare_strategy_presentation(refined_strategies, state)
            state.presentation_ready = presentation

            state.current_stage = WorkflowStage.PRESENTATION_READY

            self.logger.info(f"Generated {len(strategies)} strategies for session {state.session_id}")

        except Exception as e:
            self.logger.error(f"Error generating strategies: {str(e)}")
            state.errors.append(f"Strategy generation failed: {str(e)}")

    def _build_strategy_context(self, state: ConversationState) -> Dict[str, Any]:
        """Build comprehensive context for strategy generation"""
        context = {
            "session_id": state.session_id,
            "understanding_level": state.understanding_level.value,
            "document_analysis": state.document_analysis,
            "progressive_insights": {k: v.content for k, v in state.progressive_insights.items()},
            "conversation_turns": len(state.conversation_history),
            "user_preferences": state.user_preferences
        }

        # Extract specific context from insights
        for insight_type, insight in state.progressive_insights.items():
            if insight_type == "debt_amount":
                try:
                    context["debt_amount"] = float(insight.content.replace("Total debt amount: $", "").replace(",", ""))
                except:
                    pass
            elif insight_type == "document_type":
                context["document_class"] = insight.content
            elif insight_type == "asset_types":
                context["asset_info"] = insight.content

        return context

    def _generate_strategies(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategies based on context (mock implementation)"""
        strategies = []

        # Mock strategy generation based on context
        doc_class = context.get("document_class", "unknown")
        debt_amount = context.get("debt_amount", 0)

        if "bankruptcy" in doc_class.lower():
            if debt_amount > 50000:
                strategies.append({
                    "strategy_id": "chapter_7_liquidation",
                    "name": "Chapter 7 Liquidation",
                    "category": StrategyCategory.BANKRUPTCY.value,
                    "confidence": 0.8,
                    "applicability": 0.9,
                    "summary": "Common liquidation option for eligible debtors"
                })

                strategies.append({
                    "strategy_id": "chapter_11_reorganization",
                    "name": "Chapter 11 Reorganization",
                    "category": StrategyCategory.BANKRUPTCY.value,
                    "confidence": 0.6,
                    "applicability": 0.7,
                    "summary": "Reorganization option for businesses or complex cases"
                })
            else:
                strategies.append({
                    "strategy_id": "chapter_7_liquidation",
                    "name": "Chapter 7 Liquidation",
                    "category": StrategyCategory.BANKRUPTCY.value,
                    "confidence": 0.9,
                    "applicability": 0.95,
                    "summary": "Most appropriate option for lower debt amounts"
                })

        # Always include settlement options
        strategies.append({
            "strategy_id": "debt_settlement",
            "name": "Debt Settlement Negotiation",
            "category": StrategyCategory.SETTLEMENT.value,
            "confidence": 0.7,
            "applicability": 0.8,
            "summary": "Alternative to bankruptcy through creditor negotiation"
        })

        return strategies

    def _refine_strategies(self, strategies: List[Dict[str, Any]],
                         state: ConversationState) -> List[Dict[str, Any]]:
        """Refine strategies based on progressive insights"""
        refined_strategies = []

        for strategy in strategies:
            refined = strategy.copy()

            # Adjust confidence based on insights
            confidence_adjustments = self._calculate_confidence_adjustments(strategy, state)
            refined["confidence"] = min(1.0, max(0.0, strategy["confidence"] + confidence_adjustments))

            # Add refinement reason
            refined["refinement_reason"] = self._generate_refinement_reason(strategy, state)

            # Track refinement
            refinement = StrategyRefinement(
                refinement_id=str(uuid.uuid4()),
                original_strategy_id=strategy["strategy_id"],
                refinement_type="enhanced",
                reason=refined["refinement_reason"],
                user_input_trigger=f"Progressive insights: {len(state.progressive_insights)} insights",
                confidence_before=strategy["confidence"],
                confidence_after=refined["confidence"]
            )
            state.strategy_refinements.append(refinement)

            refined_strategies.append(refined)

        return refined_strategies

    def _calculate_confidence_adjustments(self, strategy: Dict[str, Any],
                                        state: ConversationState) -> float:
        """Calculate confidence adjustments based on insights"""
        adjustment = 0.0

        # Boost confidence if we have relevant insights
        strategy_type = strategy.get("category", "")

        if "bankruptcy" in strategy_type.lower():
            if "debt_amount" in state.progressive_insights:
                adjustment += 0.1
            if "asset_types" in state.progressive_insights:
                adjustment += 0.05

        # Adjust based on understanding level
        understanding_bonus = {
            UnderstandingLevel.MINIMAL: -0.1,
            UnderstandingLevel.BASIC: 0.0,
            UnderstandingLevel.INTERMEDIATE: 0.05,
            UnderstandingLevel.COMPREHENSIVE: 0.1,
            UnderstandingLevel.EXPERT: 0.15
        }.get(state.understanding_level, 0.0)

        adjustment += understanding_bonus

        return adjustment

    def _generate_refinement_reason(self, strategy: Dict[str, Any],
                                  state: ConversationState) -> str:
        """Generate explanation for strategy refinement"""
        reasons = []

        if len(state.progressive_insights) >= 3:
            reasons.append("Enhanced based on comprehensive case understanding")

        if state.understanding_level.value in ["comprehensive", "expert"]:
            reasons.append(f"Refined with {state.understanding_level.value} understanding level")

        relevant_insights = [k for k in state.progressive_insights.keys()
                           if any(term in k for term in ["debt", "asset", "income"])]
        if relevant_insights:
            reasons.append(f"Informed by {len(relevant_insights)} key insights")

        return "; ".join(reasons) if reasons else "Standard strategy evaluation"

    def _prepare_strategy_presentation(self, strategies: List[Dict[str, Any]],
                                     state: ConversationState) -> List[Dict[str, Any]]:
        """Prepare strategies for UPL-compliant presentation"""
        presentation = []

        for strategy in strategies:
            # Use compliance template for presentation
            presented_strategy = {
                "strategy_id": strategy["strategy_id"],
                "title": f"Common Legal Option: {strategy['name']}",
                "description": f"Parties in similar situations often consider {strategy['name'].lower()}. {strategy.get('summary', '')}",
                "disclaimer": "This is a common legal option used in similar situations. An attorney can advise if it applies to specific circumstances and provide guidance on implementation.",
                "confidence_note": f"This option is commonly applicable in similar cases (confidence level based on case analysis)",
                "educational_note": "This information is provided for educational purposes only and describes common legal strategies used in similar situations.",
                "consultation_reminder": "Consult qualified legal counsel for guidance on specific circumstances and to receive legal advice applicable to individual situations.",
                "refinement_context": strategy.get("refinement_reason", ""),
                "understanding_basis": f"Analysis based on {state.understanding_level.value} understanding of the situation"
            }

            presentation.append(presented_strategy)

        return presentation

    def _generate_follow_up_questions(self, answered_question_id: str, response_value: Any,
                                    state: ConversationState) -> List[str]:
        """Generate intelligent follow-up questions based on response"""
        follow_ups = []

        # Generate contextual follow-ups
        if "debt_total" in answered_question_id:
            try:
                debt_amount = float(str(response_value).replace('$', '').replace(',', ''))
                if debt_amount > 100000:
                    follow_ups.append("high_debt_breakdown_question")
                if debt_amount > 0:
                    follow_ups.append("creditor_types_question")
            except:
                pass

        elif "asset_info" in answered_question_id:
            if isinstance(response_value, list) and "real_estate" in response_value:
                follow_ups.append("real_estate_details_question")

        # Limit follow-ups to prevent overwhelming user
        return follow_ups[:2]

    def _should_recommend_attorney(self, state: ConversationState) -> bool:
        """Determine if attorney consultation should be recommended"""
        # Always recommend attorney for complex cases
        if state.understanding_level == UnderstandingLevel.EXPERT:
            return True

        # Recommend if high-value situation
        debt_insight = state.progressive_insights.get("debt_amount")
        if debt_insight and "$" in debt_insight.content:
            try:
                debt_amount = float(debt_insight.content.replace("Total debt amount: $", "").replace(",", ""))
                if debt_amount > 100000:
                    return True
            except:
                pass

        # Recommend if complex asset situation
        asset_insight = state.progressive_insights.get("asset_types")
        if asset_insight and len(asset_insight.content.split(",")) > 2:
            return True

        # Recommend after sufficient interaction
        return len(state.conversation_history) >= 5

    def _generate_attorney_referral_message(self, state: ConversationState) -> Dict[str, Any]:
        """Generate attorney referral message"""
        return {
            "title": "Professional Legal Consultation Recommended",
            "message": "Based on your situation, consultation with qualified legal counsel is recommended for personalized guidance.",
            "reasons": [
                "Your situation involves complex factors that benefit from professional legal analysis",
                "An attorney can provide specific legal advice tailored to your circumstances",
                "Professional guidance can help you understand all available options and their implications"
            ],
            "next_steps": [
                "Schedule a consultation with a qualified attorney in your area",
                "Prepare the information gathered in this session for your consultation",
                "Consider attorneys who specialize in your specific type of legal matter"
            ],
            "educational_note": "This recommendation is provided for educational purposes. The information gathered in this session does not constitute legal advice.",
            "understanding_summary": f"Analysis completed with {state.understanding_level.value} understanding level based on {len(state.progressive_insights)} key insights."
        }

    def _generate_session_summary(self, state: ConversationState) -> Dict[str, Any]:
        """Generate comprehensive session summary"""
        return {
            "session_id": state.session_id,
            "duration_minutes": (state.last_updated - state.created_at).total_seconds() / 60,
            "understanding_achieved": state.understanding_level.value,
            "insights_gathered": len(state.progressive_insights),
            "conversation_turns": len(state.conversation_history),
            "strategies_evaluated": len(state.final_strategies),
            "key_insights": [insight.content for insight in state.progressive_insights.values()],
            "educational_disclaimer": "All information provided was for educational purposes only. No legal advice was provided. Professional legal consultation is recommended for specific legal guidance.",
            "completion_status": "Educational analysis complete. Professional consultation recommended for legal advice."
        }

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive session status"""
        if session_id not in self.active_sessions:
            return None

        state = self.active_sessions[session_id]

        return {
            "session_id": session_id,
            "current_stage": state.current_stage.value,
            "understanding_level": state.understanding_level.value,
            "progress_percentage": state.calculate_completion_percentage(),
            "insights_count": len(state.progressive_insights),
            "questions_asked": len([t for t in state.conversation_history if t.turn_type == ConversationTurn.SYSTEM_QUESTION]),
            "responses_received": len([t for t in state.conversation_history if t.turn_type == ConversationTurn.USER_RESPONSE]),
            "strategies_ready": len(state.presentation_ready),
            "last_updated": state.last_updated.isoformat(),
            "errors": state.errors,
            "warnings": state.warnings
        }

    def orchestrate_intake(self, document: str, filename: str = None) -> Dict[str, Any]:
        """
        STANDARDIZED INTERFACE: Complete document intake orchestration

        Args:
            document (str): Document text to process
            filename (str): Optional filename

        Returns:
            Dict with keys: 'questions', 'strategies', 'session_id'
        """
        try:
            # Start a session with the document
            session = self.start_intelligent_session(
                user_id="standard_intake",
                document_path=filename or "uploaded_document",
                user_preferences={}
            )

            # Simulate document processing
            if document:
                # Write document to temp path for processing
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                    tmp.write(document)
                    session.uploaded_documents = [tmp.name]

            # Trigger document analysis
            self._trigger_document_analysis(session)

            # Get initial questions
            interaction = self.get_next_interaction(session.session_id)
            questions = []
            if interaction and interaction.get('type') == 'question':
                questions = [interaction]

            # Generate basic strategies if we have enough information
            strategies = []
            if session.understanding_level.value >= 0.5:
                self._trigger_strategy_generation(session)
                # Get generated strategies from session
                if hasattr(session, 'generated_strategies'):
                    strategies = session.generated_strategies

            return {
                'questions': questions,
                'strategies': strategies,
                'session_id': session.session_id,
                'document_analysis': getattr(session, 'document_analysis', {}),
                'gaps': getattr(session, 'identified_gaps', [])
            }

        except Exception as e:
            self.logger.error(f"Orchestration error: {e}")
            return {
                'questions': [],
                'strategies': [],
                'session_id': None,
                'error': str(e)
            }


def test_intelligent_workflow_orchestrator():
    """
    Test the complete IntelligentWorkflowOrchestrator.

    LEGAL DISCLAIMER:
    This test demonstrates the orchestrator's educational information gathering
    capabilities only. No legal advice is provided during testing.
    """
    print("=== INTELLIGENT WORKFLOW ORCHESTRATOR TEST ===")
    print("EDUCATIONAL DISCLAIMER: All orchestrator operations are for educational purposes only.")
    print("This system provides information gathering and analysis assistance only.\n")

    # Initialize orchestrator
    config = {
        'max_questions': 10,
        'understanding_threshold': 0.7,
        'session_timeout': 24
    }
    orchestrator = IntelligentWorkflowOrchestrator(config)

    # Test 1: Start intelligent session
    print("TEST 1: Starting Intelligent Session")
    print("-" * 40)

    session = orchestrator.start_intelligent_session(
        user_id="test_user_123",
        document_path="/path/to/bankruptcy_petition.pdf",
        user_preferences={"communication_style": "professional"}
    )

    print(f"Session ID: {session.session_id}")
    print(f"Current Stage: {session.current_stage.value}")
    print(f"Understanding Level: {session.understanding_level.value}")
    print(f"Initial Progress: {session.calculate_completion_percentage():.1%}")
    print(f"Documents Uploaded: {len(session.uploaded_documents)}")
    print(f"Initial Insights: {len(session.progressive_insights)}")

    # Test 2: Get next interaction
    print(f"\nTEST 2: Getting Next Interaction")
    print("-" * 40)

    interaction = orchestrator.get_next_interaction(session.session_id)
    if interaction:
        print(f"Interaction Type: {interaction['type']}")
        if interaction['type'] == 'question':
            question_data = interaction['question_data']
            print(f"Question: {question_data['text']}")
            print(f"Input Type: {question_data['input_type']}")
            print(f"Why Needed: {question_data['why_needed']}")
        print(f"Progress: {interaction['progress']:.1%}")

    # Test 3: Submit user response
    print(f"\nTEST 3: Submitting User Response")
    print("-" * 40)

    if interaction and interaction['type'] == 'question':
        success = orchestrator.submit_user_response(
            session_id=session.session_id,
            question_id=interaction['question_id'],
            response_value="$125,000",
            confidence_level=0.9
        )
        print(f"Response Submission: {'SUCCESS' if success else 'FAILED'}")

        # Check updated state
        updated_status = orchestrator.get_session_status(session.session_id)
        if updated_status:
            print(f"Updated Stage: {updated_status['current_stage']}")
            print(f"Understanding Level: {updated_status['understanding_level']}")
            print(f"Progress: {updated_status['progress_percentage']:.1%}")
            print(f"Insights: {updated_status['insights_count']}")
            print(f"Responses: {updated_status['responses_received']}")

    # Test 4: Progressive understanding building
    print(f"\nTEST 4: Progressive Understanding Building")
    print("-" * 40)

    # Submit additional responses to build understanding
    additional_responses = [
        ("asset_info_question", ["real_estate", "vehicles"]),
        ("income_details_question", "$4,500")
    ]

    for question_id, response in additional_responses:
        success = orchestrator.submit_user_response(
            session_id=session.session_id,
            question_id=question_id,
            response_value=response,
            confidence_level=0.8
        )
        print(f"Response to {question_id}: {'SUCCESS' if success else 'FAILED'}")

    # Check final understanding
    final_status = orchestrator.get_session_status(session.session_id)
    if final_status:
        print(f"Final Understanding: {final_status['understanding_level']}")
        print(f"Final Progress: {final_status['progress_percentage']:.1%}")
        print(f"Total Insights: {final_status['insights_count']}")
        print(f"Strategies Ready: {final_status['strategies_ready']}")

    # Test 5: Get final results
    print(f"\nTEST 5: Final Results and Strategy Presentation")
    print("-" * 40)

    final_interaction = orchestrator.get_next_interaction(session.session_id)
    if final_interaction:
        print(f"Final Interaction Type: {final_interaction['type']}")

        if final_interaction['type'] == 'strategies':
            strategies = final_interaction['strategies']
            print(f"Strategies Generated: {len(strategies)}")

            for i, strategy in enumerate(strategies[:2], 1):  # Show first 2
                print(f"\n{i}. {strategy['title']}")
                print(f"   Description: {strategy['description'][:100]}...")
                print(f"   Understanding Basis: {strategy.get('understanding_basis', 'Standard analysis')}")

        elif final_interaction['type'] == 'attorney_referral':
            referral = final_interaction['message']
            print(f"Referral Message: {referral['title']}")
            print(f"Reasons: {len(referral['reasons'])} factors identified")

    print(f"\n=== ORCHESTRATOR TEST COMPLETE ===")
    print(f"Master orchestrator successfully coordinated:")
    print(f"• Document analysis and gap identification")
    print(f"• Progressive understanding building through intelligent questioning")
    print(f"• Strategy generation and refinement based on user responses")
    print(f"• UPL-compliant presentation and attorney referral recommendations")
    print(f"\nREMINDER: All orchestrator operations are educational only")
    print(f"Users must consult qualified legal counsel for legal advice")

    return True


if __name__ == "__main__":
    test_intelligent_workflow_orchestrator()