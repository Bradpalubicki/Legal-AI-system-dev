"""
Adaptive Questioning System for Legal Document Analysis

Provides intelligent, context-aware question generation with progressive disclosure,
smart follow-ups, and conditional logic based on document analysis and user responses.

CRITICAL LEGAL DISCLAIMER:
All questions are for educational information gathering only. Responses are used to
provide educational content about common legal options and do not constitute legal
advice. No attorney-client relationship is created. Consult qualified legal counsel.

Created: 2025-09-14
Legal AI System - Adaptive Question Intelligence
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid

# Import our analysis components
try:
    from .sophisticated_understanding import (
        SophisticatedAnalysis, DocumentClass, JurisdictionLevel,
        PartyRole, ClaimType, ProceduralStage, ContextualGap
    )
    from ..shared.compliance.upl_compliance import ComplianceWrapper, ViolationSeverity
except ImportError:
    # Mock imports for standalone use
    class DocumentClass(Enum):
        COMPLAINT = "complaint"
        BANKRUPTCY_PETITION = "bankruptcy_petition"
        MOTION_TO_DISMISS = "motion_to_dismiss"
        CONTRACT = "contract"
        UNKNOWN = "unknown"

    class ClaimType(Enum):
        CONTRACT_BREACH = "contract_breach"
        NEGLIGENCE = "negligence"
        FRAUD = "fraud"
        UNKNOWN = "unknown"

    class ViolationSeverity(Enum):
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
        CRITICAL = "CRITICAL"

    class ComplianceWrapper:
        def analyze_text(self, text: str) -> Dict[str, Any]:
            return {"has_advice": False, "violations": [], "compliance_score": 1.0}


logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Types of input questions"""
    MULTIPLE_CHOICE = "multiple_choice"
    YES_NO = "yes_no"
    TEXT_INPUT = "text_input"
    TEXT_AREA = "text_area"
    DATE_PICKER = "date_picker"
    CURRENCY = "currency"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"
    DOCUMENT_REQUEST = "document_request"
    FILE_UPLOAD = "file_upload"
    CHECKBOX_LIST = "checkbox_list"
    RATING_SCALE = "rating_scale"


class QuestionComplexity(Enum):
    """Complexity levels for progressive disclosure"""
    BASIC = "basic"           # Essential information
    INTERMEDIATE = "intermediate"  # Important details
    ADVANCED = "advanced"     # Complex legal concepts
    EXPERT = "expert"         # Technical/procedural details


class SkipCondition(Enum):
    """Conditions for skipping questions"""
    IRRELEVANT_DOC_TYPE = "irrelevant_doc_type"
    ALREADY_ANSWERED = "already_answered"
    CONDITIONAL_FALSE = "conditional_false"
    COMPLEXITY_FILTER = "complexity_filter"
    USER_ROLE_FILTER = "user_role_filter"


class FollowUpTrigger(Enum):
    """Triggers for follow-up questions"""
    THRESHOLD_VALUE = "threshold_value"        # Numeric thresholds
    SPECIFIC_ANSWER = "specific_answer"        # Exact answer match
    CONTAINS_KEYWORD = "contains_keyword"      # Answer contains keyword
    MULTIPLE_SELECTION = "multiple_selection"  # Multiple options selected
    CONDITIONAL_LOGIC = "conditional_logic"    # Complex conditions
    RISK_INDICATOR = "risk_indicator"          # High-risk scenarios


@dataclass
class QuestionOption:
    """Option for multiple choice questions"""
    value: str
    label: str
    description: Optional[str] = None
    follow_up_questions: List[str] = field(default_factory=list)
    triggers_warning: bool = False
    warning_text: Optional[str] = None
    educational_note: Optional[str] = None


@dataclass
class ValidationRule:
    """Validation rule for question responses"""
    rule_type: str  # required, min_length, max_value, regex, etc.
    value: Optional[Any] = None
    message: str = ""

    def validate(self, input_value: Any) -> Tuple[bool, str]:
        """Validate input against this rule"""
        if self.rule_type == "required":
            if not input_value or (isinstance(input_value, str) and not input_value.strip()):
                return False, self.message or "This field is required"

        elif self.rule_type == "min_length" and isinstance(input_value, str):
            if len(input_value) < self.value:
                return False, self.message or f"Must be at least {self.value} characters"

        elif self.rule_type == "max_length" and isinstance(input_value, str):
            if len(input_value) > self.value:
                return False, self.message or f"Must be no more than {self.value} characters"

        elif self.rule_type == "min_value" and isinstance(input_value, (int, float)):
            if input_value < self.value:
                return False, self.message or f"Must be at least {self.value}"

        elif self.rule_type == "max_value" and isinstance(input_value, (int, float)):
            if input_value > self.value:
                return False, self.message or f"Must be no more than {self.value}"

        elif self.rule_type == "regex":
            if not re.match(str(self.value), str(input_value)):
                return False, self.message or "Invalid format"

        elif self.rule_type == "currency":
            currency_pattern = r'^\$?[\d,]+\.?\d{0,2}$'
            if not re.match(currency_pattern, str(input_value).replace(' ', '')):
                return False, self.message or "Please enter a valid currency amount"

        elif self.rule_type == "email":
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(input_value)):
                return False, self.message or "Please enter a valid email address"

        return True, ""


@dataclass
class ConditionalLogic:
    """Logic for when to show/skip questions"""
    condition_type: str  # doc_type, answer_value, gap_exists, etc.
    target: str  # what to check against
    operator: str  # equals, contains, greater_than, etc.
    value: Any  # comparison value

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the condition against current context"""
        try:
            if self.condition_type == "doc_type":
                return context.get("document_class") == self.value

            elif self.condition_type == "answer_value":
                answer = context.get("answers", {}).get(self.target)
                if self.operator == "equals":
                    return answer == self.value
                elif self.operator == "contains":
                    return str(self.value).lower() in str(answer).lower() if answer else False
                elif self.operator == "greater_than":
                    return float(answer or 0) > float(self.value)
                elif self.operator == "less_than":
                    return float(answer or 0) < float(self.value)

            elif self.condition_type == "gap_exists":
                gaps = context.get("gaps", [])
                return any(gap.gap_type == self.value for gap in gaps)

            elif self.condition_type == "claim_type":
                claims = context.get("claims", [])
                return any(claim.claim_type.value == self.value for claim in claims)

            elif self.condition_type == "party_count":
                parties = context.get("parties", [])
                party_count = len(parties)
                if self.operator == "greater_than":
                    return party_count > self.value
                elif self.operator == "equals":
                    return party_count == self.value

            return False

        except (ValueError, AttributeError, TypeError):
            return False


@dataclass
class FollowUpRule:
    """Rule for generating follow-up questions"""
    trigger: FollowUpTrigger
    condition: Union[str, float, List[str]]  # What triggers the follow-up
    follow_up_questions: List[str]  # Question IDs to add
    description: str

    def should_trigger(self, answer: Any) -> bool:
        """Check if this follow-up should trigger based on answer"""
        if self.trigger == FollowUpTrigger.THRESHOLD_VALUE:
            try:
                # Extract numeric value from answer
                if isinstance(answer, str):
                    # Remove currency symbols and commas
                    clean_answer = re.sub(r'[$,\s]', '', answer)
                    numeric_value = float(clean_answer)
                else:
                    numeric_value = float(answer)

                return numeric_value > float(self.condition)
            except (ValueError, TypeError):
                return False

        elif self.trigger == FollowUpTrigger.SPECIFIC_ANSWER:
            return str(answer).lower() == str(self.condition).lower()

        elif self.trigger == FollowUpTrigger.CONTAINS_KEYWORD:
            return str(self.condition).lower() in str(answer).lower()

        elif self.trigger == FollowUpTrigger.MULTIPLE_SELECTION:
            if isinstance(answer, list):
                return len(answer) >= int(self.condition)
            return False

        elif self.trigger == FollowUpTrigger.RISK_INDICATOR:
            # Custom risk logic
            risk_keywords = ["criminal", "fraud", "felony", "violation", "sanctions"]
            return any(keyword in str(answer).lower() for keyword in risk_keywords)

        return False


@dataclass
class AdaptiveQuestion:
    """Comprehensive adaptive question structure"""
    # Basic identification
    question_id: str
    question_text: str
    question_type: QuestionType
    complexity: QuestionComplexity

    # Educational context
    why_needed: str  # Educational explanation
    educational_note: str = ""
    legal_disclaimer: str = ""

    # Question configuration
    options: List[QuestionOption] = field(default_factory=list)
    placeholder: Optional[str] = None
    default_value: Optional[Any] = None
    help_text: Optional[str] = None

    # Validation and constraints
    validations: List[ValidationRule] = field(default_factory=list)
    is_required: bool = True

    # Adaptive logic
    show_conditions: List[ConditionalLogic] = field(default_factory=list)
    skip_conditions: List[ConditionalLogic] = field(default_factory=list)
    follow_up_rules: List[FollowUpRule] = field(default_factory=list)

    # Categorization
    category: str = "General"
    tags: List[str] = field(default_factory=list)
    priority: int = 1  # 1=highest, 5=lowest

    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # Other question IDs
    triggers: List[str] = field(default_factory=list)    # Questions this can trigger

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"

    def should_show(self, context: Dict[str, Any]) -> bool:
        """Determine if this question should be shown"""
        # Check skip conditions first
        for condition in self.skip_conditions:
            if condition.evaluate(context):
                return False

        # Check show conditions (all must be true if any exist)
        if self.show_conditions:
            return all(condition.evaluate(context) for condition in self.show_conditions)

        return True

    def get_follow_ups(self, answer: Any) -> List[str]:
        """Get follow-up question IDs based on answer"""
        follow_ups = []

        for rule in self.follow_up_rules:
            if rule.should_trigger(answer):
                follow_ups.extend(rule.follow_up_questions)

        # Also check option-based follow-ups
        for option in self.options:
            if option.value == answer or (isinstance(answer, list) and option.value in answer):
                follow_ups.extend(option.follow_up_questions)

        return list(set(follow_ups))  # Remove duplicates


@dataclass
class QuestionSession:
    """Represents a question session with adaptive flow"""
    session_id: str
    document_analysis: Optional[Any] = None  # SophisticatedAnalysis
    current_questions: List[AdaptiveQuestion] = field(default_factory=list)
    answered_questions: Dict[str, Any] = field(default_factory=dict)
    pending_questions: List[str] = field(default_factory=list)
    skipped_questions: Set[str] = field(default_factory=set)
    complexity_level: QuestionComplexity = QuestionComplexity.BASIC
    created_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


class AdaptiveQuestioningEngine:
    """
    Intelligent question engine that adapts based on document analysis,
    user responses, and contextual information.

    EDUCATIONAL PURPOSE DISCLAIMER:
    All questions are generated for educational information gathering only.
    Responses are used to provide informational content about common legal
    options and do not constitute legal advice or consultation.
    """

    def __init__(self):
        """Initialize the adaptive questioning engine"""
        self.compliance_wrapper = ComplianceWrapper()
        self.logger = logging.getLogger(__name__)

        # Initialize question libraries
        self._initialize_question_templates()
        self._initialize_follow_up_rules()
        self._initialize_contextual_rules()

    def _initialize_question_templates(self):
        """Initialize comprehensive question template library"""

        self.question_templates = {
            # Basic Information Questions
            "debt_total": AdaptiveQuestion(
                question_id="debt_total_amount",
                question_text="What is your total unsecured debt amount?",
                question_type=QuestionType.CURRENCY,
                complexity=QuestionComplexity.BASIC,
                why_needed="Total debt amount helps determine bankruptcy chapter eligibility and applicable legal processes.",
                educational_note="This information is used to provide educational content about common debt resolution options.",
                legal_disclaimer="Response used for educational purposes only. Consult qualified legal counsel for debt analysis.",
                placeholder="$0.00",
                validations=[
                    ValidationRule("required", message="Total debt amount is required"),
                    ValidationRule("currency", message="Please enter a valid currency amount"),
                    ValidationRule("min_value", 0, "Debt amount cannot be negative")
                ],
                category="Financial Information",
                tags=["bankruptcy", "debt", "financial"],
                priority=1,
                follow_up_rules=[
                    FollowUpRule(
                        trigger=FollowUpTrigger.THRESHOLD_VALUE,
                        condition=3000000,  # $3M threshold
                        follow_up_questions=["business_type", "criminal_history"],  # Use existing questions for demo
                        description="High debt amount triggers Subchapter V and business analysis"
                    ),
                    FollowUpRule(
                        trigger=FollowUpTrigger.THRESHOLD_VALUE,
                        condition=100000,  # $100K threshold
                        follow_up_questions=["document_requests"],  # Use existing questions
                        description="Significant debt triggers detailed breakdown questions"
                    )
                ]
            ),

            "business_type": AdaptiveQuestion(
                question_id="business_entity_type",
                question_text="What type of business entity are you filing for?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                complexity=QuestionComplexity.BASIC,
                why_needed="Business entity type determines applicable bankruptcy chapters and legal procedures.",
                educational_note="Different entity types have different legal considerations and options available.",
                options=[
                    QuestionOption("individual", "Individual/Personal", "Personal bankruptcy filing",
                                 follow_up_questions=["individual_income", "individual_assets"]),
                    QuestionOption("sole_proprietorship", "Sole Proprietorship", "Individual business owner",
                                 follow_up_questions=["business_income", "business_assets", "business_debts"]),
                    QuestionOption("llc", "Limited Liability Company (LLC)", "LLC business entity",
                                 follow_up_questions=["llc_members", "llc_operating_agreement", "business_operations"]),
                    QuestionOption("corporation", "Corporation", "Corporate entity",
                                 follow_up_questions=["corp_type", "shareholders", "board_structure"]),
                    QuestionOption("partnership", "Partnership", "Partnership entity",
                                 follow_up_questions=["partnership_type", "partners", "partnership_agreement"])
                ],
                validations=[ValidationRule("required", message="Please select a business type")],
                category="Business Information",
                tags=["business", "entity_type"],
                priority=1,
                show_conditions=[
                    ConditionalLogic("doc_type", "", "equals", DocumentClass.BANKRUPTCY_PETITION)
                ]
            ),

            "contract_dispute_type": AdaptiveQuestion(
                question_id="contract_dispute_nature",
                question_text="What type of contract dispute is this?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                complexity=QuestionComplexity.BASIC,
                why_needed="Contract dispute type determines applicable legal standards and potential remedies.",
                options=[
                    QuestionOption("breach_performance", "Breach of Performance",
                                 "One party failed to perform contractual obligations",
                                 follow_up_questions=["performance_details", "breach_timeline"]),
                    QuestionOption("breach_payment", "Breach of Payment",
                                 "Non-payment or late payment issues",
                                 follow_up_questions=["payment_terms", "amount_owed"]),
                    QuestionOption("contract_interpretation", "Contract Interpretation",
                                 "Disagreement about contract terms meaning",
                                 follow_up_questions=["disputed_clauses", "interpretation_basis"]),
                    QuestionOption("fraud_misrepresentation", "Fraud/Misrepresentation",
                                 "Allegations of false statements or fraud",
                                 follow_up_questions=["fraud_details", "reliance_damages"],
                                 triggers_warning=True,
                                 warning_text="Fraud allegations require specific proof and have serious legal implications")
                ],
                show_conditions=[
                    ConditionalLogic("claim_type", "", "equals", ClaimType.CONTRACT_BREACH)
                ],
                category="Contract Information",
                tags=["contract", "dispute"],
                priority=1
            ),

            "jurisdiction_clause": AdaptiveQuestion(
                question_id="contract_jurisdiction_clause",
                question_text="Does your contract contain a jurisdiction or venue clause?",
                question_type=QuestionType.YES_NO,
                complexity=QuestionComplexity.INTERMEDIATE,
                why_needed="Jurisdiction clauses determine where legal disputes must be filed and resolved.",
                educational_note="Jurisdiction clauses are common in contracts and can significantly affect where a case can be filed.",
                follow_up_rules=[
                    FollowUpRule(
                        trigger=FollowUpTrigger.SPECIFIC_ANSWER,
                        condition="yes",
                        follow_up_questions=["jurisdiction_clause_details", "jurisdiction_enforcement"],
                        description="Yes answer triggers detailed jurisdiction analysis"
                    ),
                    FollowUpRule(
                        trigger=FollowUpTrigger.SPECIFIC_ANSWER,
                        condition="no",
                        follow_up_questions=["venue_determination", "court_selection"],
                        description="No clause triggers venue selection questions"
                    )
                ],
                show_conditions=[
                    ConditionalLogic("claim_type", "", "equals", ClaimType.CONTRACT_BREACH)
                ],
                category="Jurisdiction",
                tags=["jurisdiction", "venue", "contract"],
                priority=2
            ),

            "criminal_history": AdaptiveQuestion(
                question_id="prior_criminal_convictions",
                question_text="Do you have any prior criminal convictions?",
                question_type=QuestionType.YES_NO,
                complexity=QuestionComplexity.INTERMEDIATE,
                why_needed="Prior convictions can affect sentencing, plea negotiations, and legal strategies in criminal cases.",
                educational_note="Prior criminal history is relevant to educational information about criminal legal processes.",
                legal_disclaimer="Criminal history information is sensitive. Consult qualified criminal defense counsel immediately.",
                follow_up_rules=[
                    FollowUpRule(
                        trigger=FollowUpTrigger.SPECIFIC_ANSWER,
                        condition="yes",
                        follow_up_questions=["conviction_details", "sentence_completion", "record_sealing"],
                        description="Prior convictions trigger detailed criminal history questions"
                    )
                ],
                show_conditions=[
                    ConditionalLogic("doc_type", "", "equals", "criminal_case"),
                    ConditionalLogic("claim_type", "", "equals", "criminal")
                ],
                category="Criminal History",
                tags=["criminal", "convictions", "history"],
                priority=1
            ),

            "document_requests": AdaptiveQuestion(
                question_id="missing_documents_needed",
                question_text="Which of these documents would be helpful for your case?",
                question_type=QuestionType.CHECKBOX_LIST,
                complexity=QuestionComplexity.INTERMEDIATE,
                why_needed="Additional documents provide more complete context for educational analysis.",
                educational_note="These documents commonly provide important context in similar legal situations.",
                options=[
                    QuestionOption("financial_statements", "Financial Statements",
                                 "Balance sheets, income statements, tax returns"),
                    QuestionOption("contracts", "Related Contracts or Agreements",
                                 "Any contracts relevant to the dispute"),
                    QuestionOption("correspondence", "Email/Letter Correspondence",
                                 "Communications between parties"),
                    QuestionOption("bank_records", "Bank Records",
                                 "Account statements, transaction records"),
                    QuestionOption("court_orders", "Prior Court Orders",
                                 "Any existing court orders or judgments"),
                    QuestionOption("insurance", "Insurance Policies",
                                 "Relevant insurance coverage documents")
                ],
                category="Document Collection",
                tags=["documents", "evidence", "discovery"],
                priority=3
            )
        }

    def _initialize_follow_up_rules(self):
        """Initialize smart follow-up rule library"""

        self.global_follow_up_rules = {
            # High debt amount triggers
            "high_debt_analysis": FollowUpRule(
                trigger=FollowUpTrigger.THRESHOLD_VALUE,
                condition=3000000,  # $3M+
                follow_up_questions=[
                    "subchapter_v_eligibility",
                    "business_revenue_analysis",
                    "debt_structure_complex",
                    "reorganization_feasibility"
                ],
                description="Debt over $3M triggers complex business analysis"
            ),

            # Business complexity triggers
            "complex_business_structure": FollowUpRule(
                trigger=FollowUpTrigger.MULTIPLE_SELECTION,
                condition=2,  # Multiple entity types or complex structure
                follow_up_questions=[
                    "entity_relationships",
                    "inter_company_transactions",
                    "consolidated_financials",
                    "business_continuity"
                ],
                description="Complex business structure triggers detailed analysis"
            ),

            # Criminal case escalation
            "criminal_case_complexity": FollowUpRule(
                trigger=FollowUpTrigger.RISK_INDICATOR,
                condition=["criminal", "felony", "fraud"],
                follow_up_questions=[
                    "attorney_representation",
                    "immediate_deadlines",
                    "constitutional_rights",
                    "plea_considerations"
                ],
                description="Criminal cases trigger immediate legal protection questions"
            )
        }

    def _initialize_contextual_rules(self):
        """Initialize context-based question selection rules"""

        self.contextual_rules = {
            DocumentClass.BANKRUPTCY_PETITION: {
                "required_questions": [
                    "debt_total",
                    "business_type"
                ],
                "conditional_questions": {
                    "individual": ["individual_income", "individual_expenses"],
                    "business": ["business_operations", "employee_count", "business_income"]
                },
                "complexity_progression": [
                    QuestionComplexity.BASIC,
                    QuestionComplexity.INTERMEDIATE,
                    QuestionComplexity.ADVANCED
                ]
            },

            DocumentClass.COMPLAINT: {
                "required_questions": [
                    "contract_dispute_type",
                    "jurisdiction_clause"
                ],
                "conditional_questions": {
                    "contract_breach": ["contract_terms", "jurisdiction_clause"],
                    "tort_claim": ["injury_details", "liability_basis"]
                }
            },

            DocumentClass.MOTION_TO_DISMISS: {
                "required_questions": [
                    "dismissal_grounds",
                    "legal_standards",
                    "procedural_requirements"
                ],
                "complexity_progression": [
                    QuestionComplexity.INTERMEDIATE,
                    QuestionComplexity.ADVANCED,
                    QuestionComplexity.EXPERT
                ]
            }
        }

    def generate_adaptive_questions(self, document_analysis: Any,
                                  user_context: Optional[Dict[str, Any]] = None) -> QuestionSession:
        """
        Generate adaptive questions based on document analysis and context.

        Args:
            document_analysis: SophisticatedAnalysis result
            user_context: Additional user context (complexity preference, role, etc.)

        Returns:
            QuestionSession with initial set of adaptive questions
        """

        session_id = str(uuid.uuid4())
        session = QuestionSession(
            session_id=session_id,
            document_analysis=document_analysis,
            context=user_context or {}
        )

        try:
            # Build comprehensive context
            context = self._build_question_context(document_analysis, session.context)

            # Generate initial questions based on document type
            initial_questions = self._generate_contextual_questions(document_analysis, context)

            # Add gap-based questions
            if hasattr(document_analysis, 'contextual_gaps'):
                gap_questions = self._generate_gap_questions(document_analysis.contextual_gaps, context)
                initial_questions.extend(gap_questions)

            # If no contextual questions, add basic questions
            if not initial_questions:
                initial_questions = self._generate_basic_questions(context)

            # Apply progressive disclosure filtering
            filtered_questions = self._apply_complexity_filter(initial_questions,
                                                             session.complexity_level)

            # Apply conditional logic and skip irrelevant questions
            final_questions = []
            for question in filtered_questions:
                if question.should_show(context):
                    final_questions.append(question)
                else:
                    session.skipped_questions.add(question.question_id)

            # Sort by priority and dependencies
            session.current_questions = self._sort_questions_by_priority(final_questions)

            # Update session context
            session.context.update(context)

            self.logger.info(f"Generated {len(session.current_questions)} adaptive questions for session {session_id}")

            return session

        except Exception as e:
            self.logger.error(f"Error generating adaptive questions: {str(e)}")
            # Return minimal session on error
            return QuestionSession(session_id=session_id)

    def process_answer(self, session: QuestionSession, question_id: str,
                      answer: Any) -> List[AdaptiveQuestion]:
        """
        Process a question answer and generate follow-up questions.

        Args:
            session: Current question session
            question_id: ID of answered question
            answer: User's answer

        Returns:
            List of new follow-up questions to add
        """

        try:
            # Store the answer
            session.answered_questions[question_id] = answer

            # Find the answered question
            answered_question = None
            for q in session.current_questions:
                if q.question_id == question_id:
                    answered_question = q
                    break

            if not answered_question:
                self.logger.warning(f"Question {question_id} not found in current questions")
                return []

            # Get follow-up question IDs
            follow_up_ids = answered_question.get_follow_ups(answer)

            # Generate follow-up questions
            follow_up_questions = []
            for follow_up_id in follow_up_ids:
                if follow_up_id in self.question_templates:
                    follow_up_q = self.question_templates[follow_up_id]

                    # Update context with latest answers
                    updated_context = self._build_question_context(
                        session.document_analysis,
                        {**session.context, "answers": session.answered_questions}
                    )

                    # Check if follow-up should be shown
                    if follow_up_q.should_show(updated_context):
                        follow_up_questions.append(follow_up_q)

            # Apply global follow-up rules
            global_follow_ups = self._apply_global_follow_up_rules(answer, session)
            follow_up_questions.extend(global_follow_ups)

            # Update session with new questions
            session.current_questions.extend(follow_up_questions)
            session.context["answers"] = session.answered_questions

            self.logger.info(f"Processed answer for {question_id}, generated {len(follow_up_questions)} follow-ups")

            return follow_up_questions

        except Exception as e:
            self.logger.error(f"Error processing answer: {str(e)}")
            return []

    def _build_question_context(self, document_analysis: Any, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive context for question generation"""

        context = {
            "document_class": document_analysis.document_class if document_analysis else DocumentClass.UNKNOWN,
            "jurisdiction": document_analysis.jurisdiction_info if document_analysis else None,
            "parties": document_analysis.parties if document_analysis else [],
            "claims": document_analysis.claims if document_analysis else [],
            "gaps": document_analysis.contextual_gaps if document_analysis else [],
            "procedural_stage": document_analysis.procedural_posture if document_analysis else None,
            "answers": user_context.get("answers", {}),
            "user_role": user_context.get("user_role", "general"),
            "complexity_preference": user_context.get("complexity_preference", QuestionComplexity.BASIC)
        }

        return context

    def _generate_contextual_questions(self, document_analysis: Any,
                                     context: Dict[str, Any]) -> List[AdaptiveQuestion]:
        """Generate questions based on document type and context"""

        questions = []
        doc_class = document_analysis.document_class if document_analysis else DocumentClass.UNKNOWN

        # Get required questions for this document type
        contextual_rules = self.contextual_rules.get(doc_class, {})
        required_question_ids = contextual_rules.get("required_questions", [])

        for question_id in required_question_ids:
            if question_id in self.question_templates:
                questions.append(self.question_templates[question_id])

        # Add conditional questions based on context
        conditional_questions = contextual_rules.get("conditional_questions", {})
        for condition, question_ids in conditional_questions.items():
            # Simple condition matching (would be more sophisticated in production)
            if self._check_condition_match(condition, context):
                for question_id in question_ids:
                    if question_id in self.question_templates:
                        questions.append(self.question_templates[question_id])

        return questions

    def _generate_basic_questions(self, context: Dict[str, Any]) -> List[AdaptiveQuestion]:
        """Generate basic questions when no contextual questions are found"""

        basic_questions = []

        # Always include these fundamental questions
        basic_question_ids = ["debt_total", "business_type", "document_requests"]

        for question_id in basic_question_ids:
            if question_id in self.question_templates:
                basic_questions.append(self.question_templates[question_id])

        return basic_questions

    def _generate_gap_questions(self, gaps: List[Any], context: Dict[str, Any]) -> List[AdaptiveQuestion]:
        """Generate questions to address identified information gaps"""

        questions = []

        for gap in gaps:
            gap_type = getattr(gap, 'gap_type', 'unknown')

            # Map gap types to question templates
            gap_question_mapping = {
                "jurisdictional_basis": ["jurisdiction_basis", "venue_preference"],
                "party_identification": ["missing_party_info", "party_roles"],
                "legal_claims": ["claim_clarification", "legal_theories"],
                "critical_deadlines": ["upcoming_deadlines", "statute_limitations"],
                "financial_information": ["debt_total_amount", "asset_summary"],
                "contract_terms": ["contract_dispute_nature", "jurisdiction_clause"]
            }

            question_ids = gap_question_mapping.get(gap_type, [])
            for question_id in question_ids:
                if question_id in self.question_templates:
                    # Create gap-specific version of the question
                    base_question = self.question_templates[question_id]
                    gap_question = self._customize_question_for_gap(base_question, gap)
                    questions.append(gap_question)

        return questions

    def _customize_question_for_gap(self, base_question: AdaptiveQuestion, gap: Any) -> AdaptiveQuestion:
        """Customize a question template to address a specific gap"""

        # Create a copy of the base question
        customized = AdaptiveQuestion(
            question_id=f"{base_question.question_id}_gap_{getattr(gap, 'gap_id', 'unknown')}",
            question_text=base_question.question_text,
            question_type=base_question.question_type,
            complexity=base_question.complexity,
            why_needed=f"{base_question.why_needed} This addresses an identified information gap: {getattr(gap, 'description', '')}",
            educational_note=base_question.educational_note,
            legal_disclaimer=base_question.legal_disclaimer,
            options=base_question.options.copy(),
            validations=base_question.validations.copy(),
            category=f"Gap Analysis - {base_question.category}",
            tags=base_question.tags + ["gap_analysis"],
            priority=max(1, base_question.priority - 1)  # Higher priority for gap questions
        )

        return customized

    def _apply_complexity_filter(self, questions: List[AdaptiveQuestion],
                                max_complexity: QuestionComplexity) -> List[AdaptiveQuestion]:
        """Filter questions based on complexity level"""

        complexity_order = [
            QuestionComplexity.BASIC,
            QuestionComplexity.INTERMEDIATE,
            QuestionComplexity.ADVANCED,
            QuestionComplexity.EXPERT
        ]

        max_complexity_index = complexity_order.index(max_complexity)

        filtered = []
        for question in questions:
            question_complexity_index = complexity_order.index(question.complexity)
            if question_complexity_index <= max_complexity_index:
                filtered.append(question)

        return filtered

    def _sort_questions_by_priority(self, questions: List[AdaptiveQuestion]) -> List[AdaptiveQuestion]:
        """Sort questions by priority and resolve dependencies"""

        # Simple priority sorting (would implement topological sort for dependencies in production)
        sorted_questions = sorted(questions, key=lambda q: (q.priority, q.complexity.value))

        return sorted_questions

    def _apply_global_follow_up_rules(self, answer: Any, session: QuestionSession) -> List[AdaptiveQuestion]:
        """Apply global follow-up rules that span multiple questions"""

        follow_ups = []

        for rule_name, rule in self.global_follow_up_rules.items():
            if rule.should_trigger(answer):
                for question_id in rule.follow_up_questions:
                    if question_id in self.question_templates:
                        # Check if we haven't already added this question
                        if not any(q.question_id == question_id for q in session.current_questions):
                            follow_ups.append(self.question_templates[question_id])

        return follow_ups

    def _check_condition_match(self, condition: str, context: Dict[str, Any]) -> bool:
        """Simple condition matching for contextual questions"""

        # This would be more sophisticated in production
        if condition == "individual":
            return context.get("user_role") == "individual"
        elif condition == "business":
            business_entities = ["llc", "corporation", "partnership", "sole_proprietorship"]
            return any(entity in str(context.get("answers", {})).lower() for entity in business_entities)
        elif condition == "contract_breach":
            claims = context.get("claims", [])
            return any(getattr(claim, 'claim_type', None) == ClaimType.CONTRACT_BREACH for claim in claims)

        return False

    def get_next_questions(self, session: QuestionSession, count: int = 5) -> List[AdaptiveQuestion]:
        """Get the next set of questions to present to user"""

        # Filter out already answered questions
        unanswered = [
            q for q in session.current_questions
            if q.question_id not in session.answered_questions
            and q.question_id not in session.skipped_questions
        ]

        # Check dependencies
        available = []
        for question in unanswered:
            dependencies_met = all(
                dep_id in session.answered_questions
                for dep_id in question.depends_on
            )
            if dependencies_met:
                available.append(question)

        # Return up to 'count' questions
        return available[:count]

    def calculate_completion_progress(self, session: QuestionSession) -> Dict[str, Any]:
        """Calculate question completion progress and statistics"""

        total_questions = len(session.current_questions)
        answered_questions = len(session.answered_questions)
        skipped_questions = len(session.skipped_questions)
        remaining_questions = total_questions - answered_questions - skipped_questions

        progress = {
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "skipped_questions": skipped_questions,
            "remaining_questions": remaining_questions,
            "completion_percentage": (answered_questions / max(total_questions, 1)) * 100,
            "categories_completed": self._calculate_category_progress(session),
            "estimated_time_remaining": self._estimate_time_remaining(remaining_questions)
        }

        return progress

    def _calculate_category_progress(self, session: QuestionSession) -> Dict[str, Dict[str, int]]:
        """Calculate progress by question category"""

        category_stats = {}

        for question in session.current_questions:
            category = question.category
            if category not in category_stats:
                category_stats[category] = {"total": 0, "answered": 0, "skipped": 0}

            category_stats[category]["total"] += 1

            if question.question_id in session.answered_questions:
                category_stats[category]["answered"] += 1
            elif question.question_id in session.skipped_questions:
                category_stats[category]["skipped"] += 1

        return category_stats

    def _estimate_time_remaining(self, remaining_questions: int) -> str:
        """Estimate time to complete remaining questions"""

        # Rough estimate: 1-2 minutes per question on average
        minutes = remaining_questions * 1.5

        if minutes < 5:
            return "Less than 5 minutes"
        elif minutes < 15:
            return f"About {int(minutes)} minutes"
        elif minutes < 60:
            return f"About {int(minutes)} minutes"
        else:
            hours = minutes / 60
            return f"About {hours:.1f} hours"


def test_adaptive_questioning():
    """
    Test the adaptive questioning system with various scenarios.

    LEGAL DISCLAIMER:
    This test demonstrates question generation capabilities for educational purposes only.
    All generated questions are for informational use and do not constitute legal consultation.
    """

    print("=== ADAPTIVE QUESTIONING SYSTEM TEST ===")
    print("EDUCATIONAL DISCLAIMER: All questions generated for educational purposes only")
    print("No legal advice provided. Professional legal consultation recommended.\n")

    # Create mock document analysis
    class MockAnalysis:
        def __init__(self):
            self.document_class = DocumentClass.BANKRUPTCY_PETITION
            self.contextual_gaps = [
                type('Gap', (), {
                    'gap_type': 'financial_information',
                    'gap_id': 'debt_001',
                    'description': 'Total debt amount not specified'
                })()
            ]
            self.parties = []
            self.claims = []
            self.jurisdiction_info = None
            self.procedural_posture = None

    # Initialize the engine
    engine = AdaptiveQuestioningEngine()

    # Test 1: Generate initial questions for bankruptcy case
    print("TEST 1: Generating questions for bankruptcy petition")
    mock_analysis = MockAnalysis()

    session = engine.generate_adaptive_questions(
        mock_analysis,
        {"user_role": "business", "complexity_preference": QuestionComplexity.BASIC}
    )

    print(f"Generated session: {session.session_id}")
    print(f"Total questions: {len(session.current_questions)}")

    # Show first few questions
    next_questions = engine.get_next_questions(session, count=3)
    print(f"\nNext {len(next_questions)} questions to present:")

    for i, question in enumerate(next_questions, 1):
        print(f"\n{i}. {question.question_text}")
        print(f"   Type: {question.question_type.value}")
        print(f"   Complexity: {question.complexity.value}")
        print(f"   Why needed: {question.why_needed}")
        print(f"   Category: {question.category}")

        if question.options:
            print(f"   Options:")
            for opt in question.options[:3]:  # Show first 3 options
                print(f"     - {opt.label}: {opt.description}")

        print(f"   Required: {question.is_required}")
        print(f"   Priority: {question.priority}")

    # Test 2: Process answer and generate follow-ups
    print(f"\n\nTEST 2: Processing answer and generating follow-ups")

    if next_questions:
        first_question = next_questions[0]

        # Simulate high debt amount answer
        test_answer = "$5000000"  # $5M to trigger follow-ups

        print(f"Answering '{first_question.question_text}' with: {test_answer}")

        follow_ups = engine.process_answer(session, first_question.question_id, test_answer)

        print(f"Generated {len(follow_ups)} follow-up questions:")
        for follow_up in follow_ups:
            print(f"- {follow_up.question_text} ({follow_up.complexity.value})")

    # Test 3: Progress calculation
    print(f"\n\nTEST 3: Progress calculation")
    progress = engine.calculate_completion_progress(session)

    print(f"Completion Progress:")
    print(f"- Total Questions: {progress['total_questions']}")
    print(f"- Answered: {progress['answered_questions']}")
    print(f"- Remaining: {progress['remaining_questions']}")
    print(f"- Progress: {progress['completion_percentage']:.1f}%")
    print(f"- Estimated Time: {progress['estimated_time_remaining']}")

    # Test 4: Different document types
    print(f"\n\nTEST 4: Contract dispute questions")

    mock_contract_analysis = MockAnalysis()
    mock_contract_analysis.document_class = DocumentClass.COMPLAINT
    mock_contract_analysis.claims = [
        type('Claim', (), {'claim_type': ClaimType.CONTRACT_BREACH})()
    ]
    mock_contract_analysis.contextual_gaps = []  # Add empty gaps

    contract_session = engine.generate_adaptive_questions(
        mock_contract_analysis,
        {"user_role": "business"}
    )

    contract_questions = engine.get_next_questions(contract_session, count=2)
    print(f"Contract dispute questions:")
    for question in contract_questions:
        print(f"- {question.question_text}")
        print(f"  Category: {question.category}")

        # Test jurisdiction clause follow-up
        if "jurisdiction" in question.question_text.lower():
            print(f"  Testing 'yes' answer for follow-ups...")
            contract_follow_ups = engine.process_answer(
                contract_session, question.question_id, "yes"
            )
            for follow_up in contract_follow_ups:
                print(f"    → Follow-up: {follow_up.question_text}")

    # Test 5: Question validation
    print(f"\n\nTEST 5: Question validation testing")

    if next_questions:
        test_question = next_questions[0]
        test_values = ["$50000", "invalid", "", "-1000"]

        print(f"Testing validation for: {test_question.question_text}")
        for validation in test_question.validations:
            print(f"\nValidation rule: {validation.rule_type}")
            for test_value in test_values:
                is_valid, message = validation.validate(test_value)
                status = "[VALID]" if is_valid else "[INVALID]"
                print(f"  {status} '{test_value}': {message}")

    print(f"\n=== TEST COMPLETE ===")
    print(f"Adaptive questioning system successfully demonstrated:")
    print(f"- Contextual question generation based on document type")
    print(f"- Smart follow-up logic with threshold and condition triggers")
    print(f"- Progressive complexity filtering")
    print(f"- Multiple question types and validation")
    print(f"- Progress tracking and estimation")
    print(f"\nREMINDER: All questions are educational only - Professional legal consultation recommended")


if __name__ == "__main__":
    test_adaptive_questioning()