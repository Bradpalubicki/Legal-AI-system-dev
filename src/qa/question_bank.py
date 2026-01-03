"""
Question Banking System
Manages pre-approved questions with state-specific and judge-specific variations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from datetime import datetime
from decimal import Decimal
import uuid


class QuestionCategory(Enum):
    PROCEDURAL = "procedural"
    EVIDENCE = "evidence"
    CONTRACT = "contract"
    TORT = "tort"
    CRIMINAL = "criminal"
    CONSTITUTIONAL = "constitutional"
    FAMILY = "family"
    BANKRUPTCY = "bankruptcy"
    IMMIGRATION = "immigration"
    EMPLOYMENT = "employment"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    TAX = "tax"


class QuestionType(Enum):
    FACTUAL = "factual"
    LEGAL_STANDARD = "legal_standard"
    PROCEDURAL_STEP = "procedural_step"
    STRATEGIC = "strategic"
    OUTCOME_PREDICTION = "outcome_prediction"
    CASE_ANALYSIS = "case_analysis"
    PRECEDENT = "precedent"
    JURISDICTION_SPECIFIC = "jurisdiction_specific"


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    EXPERT_REVIEW = "expert_review"


class Jurisdiction(Enum):
    FEDERAL = "federal"
    STATE = "state"
    LOCAL = "local"
    TRIBAL = "tribal"


@dataclass
class QuestionVariation:
    variation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    base_question_id: str = ""
    variation_text: str = ""
    state_code: Optional[str] = None  # e.g., "CA", "NY", "TX"
    jurisdiction: Jurisdiction = Jurisdiction.STATE
    judge_id: Optional[str] = None
    court_id: Optional[str] = None
    context_variables: Dict[str, str] = field(default_factory=dict)
    applicability_conditions: List[str] = field(default_factory=list)
    usage_frequency: int = 0
    success_rate: Decimal = field(default=Decimal("0.0"))


@dataclass
class PreApprovedQuestion:
    question_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question_text: str = ""
    category: QuestionCategory = QuestionCategory.PROCEDURAL
    question_type: QuestionType = QuestionType.FACTUAL
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    variations: List[QuestionVariation] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    keywords: List[str] = field(default_factory=list)
    complexity_level: int = 1  # 1-10 scale
    estimated_response_time: int = 300  # seconds
    required_expertise: List[str] = field(default_factory=list)
    context_requirements: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.utcnow)
    approved_by: str = ""
    approval_date: Optional[datetime] = None
    usage_count: int = 0
    effectiveness_score: Decimal = field(default=Decimal("0.0"))


@dataclass
class QuestionTemplate:
    template_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    template_name: str = ""
    template_pattern: str = ""  # e.g., "What is the statute of limitations for {claim_type} in {state}?"
    required_variables: List[str] = field(default_factory=list)
    optional_variables: List[str] = field(default_factory=list)
    applicable_categories: List[QuestionCategory] = field(default_factory=list)
    usage_examples: List[str] = field(default_factory=list)
    generated_questions: List[str] = field(default_factory=list)


@dataclass
class JudgeProfile:
    judge_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    judge_name: str = ""
    court_name: str = ""
    jurisdiction: Jurisdiction = Jurisdiction.STATE
    state_code: Optional[str] = None
    preferred_question_types: List[QuestionType] = field(default_factory=list)
    common_rulings: Dict[str, str] = field(default_factory=dict)
    procedural_preferences: List[str] = field(default_factory=list)
    case_specialties: List[QuestionCategory] = field(default_factory=list)
    temperament_notes: str = ""
    historical_outcomes: Dict[str, Decimal] = field(default_factory=dict)


@dataclass
class OutcomeBasedQuestion:
    outcome_question_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    base_question_id: str = ""
    desired_outcome: str = ""
    outcome_probability: Decimal = field(default=Decimal("0.0"))
    strategic_context: str = ""
    risk_factors: List[str] = field(default_factory=list)
    success_indicators: List[str] = field(default_factory=list)
    alternative_approaches: List[str] = field(default_factory=list)
    precedent_strength: Decimal = field(default=Decimal("0.0"))


@dataclass
class CustomQuestion:
    custom_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question_text: str = ""
    created_by: str = ""
    case_id: str = ""
    client_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    approval_requested: bool = False
    reviewed_by: str = ""
    approved_for_bank: bool = False
    creation_date: datetime = field(default_factory=datetime.utcnow)
    usage_restricted: bool = True  # Restricted to creator by default


class QuestionBank:
    def __init__(self):
        self.questions = {}
        self.templates = {}
        self.judge_profiles = {}
        self.custom_questions = {}
        self.question_index = {}  # For fast searching
        self.state_variations = {}
        self.approval_queue = []

    async def initialize_default_questions(self):
        """Initialize the question bank with default pre-approved questions"""
        default_questions = [
            {
                "text": "What is the statute of limitations for this type of claim in this jurisdiction?",
                "category": QuestionCategory.PROCEDURAL,
                "type": QuestionType.LEGAL_STANDARD,
                "tags": {"statute_of_limitations", "procedural", "timing"},
                "complexity": 3
            },
            {
                "text": "What are the elements required to prove negligence in this case?",
                "category": QuestionCategory.TORT,
                "type": QuestionType.LEGAL_STANDARD,
                "tags": {"negligence", "elements", "proof"},
                "complexity": 4
            },
            {
                "text": "What discovery methods are most appropriate for gathering evidence?",
                "category": QuestionCategory.PROCEDURAL,
                "type": QuestionType.STRATEGIC,
                "tags": {"discovery", "evidence", "strategy"},
                "complexity": 5
            },
            {
                "text": "What are the potential damages available in this type of case?",
                "category": QuestionCategory.PROCEDURAL,
                "type": QuestionType.OUTCOME_PREDICTION,
                "tags": {"damages", "remedies", "compensation"},
                "complexity": 4
            },
            {
                "text": "What procedural requirements must be met for filing this motion?",
                "category": QuestionCategory.PROCEDURAL,
                "type": QuestionType.PROCEDURAL_STEP,
                "tags": {"motion", "procedure", "filing"},
                "complexity": 3
            },
            {
                "text": "What is the likelihood of success on the merits for this claim?",
                "category": QuestionCategory.PROCEDURAL,
                "type": QuestionType.OUTCOME_PREDICTION,
                "tags": {"success", "probability", "merits"},
                "complexity": 6
            },
            {
                "text": "What constitutional issues might arise in this case?",
                "category": QuestionCategory.CONSTITUTIONAL,
                "type": QuestionType.CASE_ANALYSIS,
                "tags": {"constitutional", "rights", "analysis"},
                "complexity": 7
            },
            {
                "text": "What are the relevant precedents that support our position?",
                "category": QuestionCategory.PROCEDURAL,
                "type": QuestionType.PRECEDENT,
                "tags": {"precedent", "case_law", "support"},
                "complexity": 5
            },
            {
                "text": "What alternative dispute resolution options are available?",
                "category": QuestionCategory.PROCEDURAL,
                "type": QuestionType.STRATEGIC,
                "tags": {"ADR", "mediation", "arbitration"},
                "complexity": 4
            },
            {
                "text": "What are the cost-benefit considerations for pursuing this claim?",
                "category": QuestionCategory.PROCEDURAL,
                "type": QuestionType.STRATEGIC,
                "tags": {"cost", "benefit", "economics"},
                "complexity": 5
            }
        ]

        for question_data in default_questions:
            question = PreApprovedQuestion(
                question_text=question_data["text"],
                category=question_data["category"],
                question_type=question_data["type"],
                approval_status=ApprovalStatus.APPROVED,
                tags=question_data["tags"],
                complexity_level=question_data["complexity"],
                approved_by="system",
                approval_date=datetime.utcnow()
            )

            # Create state variations for jurisdiction-specific questions
            if "jurisdiction" in question_data["tags"]:
                await self._create_state_variations(question)

            self.questions[question.question_id] = question
            await self._index_question(question)

    async def _create_state_variations(self, base_question: PreApprovedQuestion):
        """Create state-specific variations of a question"""
        common_states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]

        for state_code in common_states:
            variation = QuestionVariation(
                base_question_id=base_question.question_id,
                variation_text=base_question.question_text.replace(
                    "this jurisdiction", f"{state_code}"
                ).replace(
                    "jurisdiction", f"{state_code} state law"
                ),
                state_code=state_code,
                jurisdiction=Jurisdiction.STATE
            )
            base_question.variations.append(variation)

    async def _index_question(self, question: PreApprovedQuestion):
        """Index question for fast searching"""
        # Index by category
        if question.category not in self.question_index:
            self.question_index[question.category] = []
        self.question_index[question.category].append(question.question_id)

        # Index by keywords
        for keyword in question.keywords:
            key = f"keyword_{keyword}"
            if key not in self.question_index:
                self.question_index[key] = []
            self.question_index[key].append(question.question_id)

        # Index by tags
        for tag in question.tags:
            key = f"tag_{tag}"
            if key not in self.question_index:
                self.question_index[key] = []
            self.question_index[key].append(question.question_id)

    async def search_questions(self, query: str, category: Optional[QuestionCategory] = None,
                             state: Optional[str] = None, judge_id: Optional[str] = None) -> List[PreApprovedQuestion]:
        """Search for questions matching criteria"""
        matching_questions = []

        # Start with category filter if specified
        candidate_ids = []
        if category:
            candidate_ids = self.question_index.get(category, [])
        else:
            candidate_ids = list(self.questions.keys())

        # Search through candidates
        query_lower = query.lower()
        for question_id in candidate_ids:
            question = self.questions.get(question_id)
            if not question:
                continue

            # Text matching
            if query_lower in question.question_text.lower():
                matching_questions.append(question)
                continue

            # Tag matching
            if any(query_lower in tag.lower() for tag in question.tags):
                matching_questions.append(question)
                continue

            # Keyword matching
            if any(query_lower in keyword.lower() for keyword in question.keywords):
                matching_questions.append(question)
                continue

        # Filter by state/jurisdiction if specified
        if state:
            state_filtered = []
            for question in matching_questions:
                # Check if question has state-specific variations
                state_variations = [v for v in question.variations if v.state_code == state]
                if state_variations or not question.variations:  # Include general questions too
                    state_filtered.append(question)
            matching_questions = state_filtered

        # Filter by judge preferences if specified
        if judge_id:
            judge_profile = self.judge_profiles.get(judge_id)
            if judge_profile:
                judge_filtered = []
                for question in matching_questions:
                    if (question.question_type in judge_profile.preferred_question_types or
                        question.category in judge_profile.case_specialties):
                        judge_filtered.append(question)
                matching_questions = judge_filtered

        return matching_questions

    async def get_question_variations(self, question_id: str, state: Optional[str] = None,
                                    judge_id: Optional[str] = None) -> List[QuestionVariation]:
        """Get appropriate variations of a question"""
        question = self.questions.get(question_id)
        if not question:
            return []

        variations = []

        # Filter by state if specified
        if state:
            state_variations = [v for v in question.variations if v.state_code == state]
            variations.extend(state_variations)

        # Filter by judge preferences if specified
        if judge_id:
            judge_variations = [v for v in question.variations if v.judge_id == judge_id]
            variations.extend(judge_variations)

        # If no specific variations found, return general variations
        if not variations:
            variations = [v for v in question.variations if not v.state_code and not v.judge_id]

        return variations

    async def create_custom_question(self, question_text: str, created_by: str,
                                   case_id: str, context: Dict[str, Any]) -> CustomQuestion:
        """Create a custom question for specific case"""
        custom_question = CustomQuestion(
            question_text=question_text,
            created_by=created_by,
            case_id=case_id,
            context=context
        )

        self.custom_questions[custom_question.custom_id] = custom_question
        return custom_question

    async def suggest_follow_up_questions(self, base_question_id: str,
                                        answer_content: str) -> List[PreApprovedQuestion]:
        """Suggest relevant follow-up questions based on the answer"""
        base_question = self.questions.get(base_question_id)
        if not base_question:
            return []

        suggestions = []

        # Use predefined follow-up questions
        for follow_up_id in base_question.follow_up_questions:
            follow_up_question = self.questions.get(follow_up_id)
            if follow_up_question:
                suggestions.append(follow_up_question)

        # Find related questions by category and tags
        category_questions = await self.search_questions(
            query="",
            category=base_question.category
        )

        for question in category_questions:
            if (question.question_id != base_question_id and
                len(question.tags.intersection(base_question.tags)) > 0):
                suggestions.append(question)

        # Limit suggestions and sort by relevance
        suggestions = suggestions[:5]
        return suggestions

    async def create_outcome_based_questions(self, desired_outcome: str,
                                           case_context: Dict[str, Any]) -> List[OutcomeBasedQuestion]:
        """Generate questions focused on achieving specific outcomes"""
        outcome_questions = []

        # Search for relevant base questions
        outcome_keywords = desired_outcome.lower().split()
        relevant_questions = []

        for keyword in outcome_keywords:
            matching = await self.search_questions(keyword)
            relevant_questions.extend(matching)

        # Remove duplicates
        unique_questions = {q.question_id: q for q in relevant_questions}.values()

        # Create outcome-focused variations
        for base_question in unique_questions:
            outcome_question = OutcomeBasedQuestion(
                base_question_id=base_question.question_id,
                desired_outcome=desired_outcome,
                strategic_context=f"Focused on achieving: {desired_outcome}",
                outcome_probability=await self._estimate_outcome_probability(
                    base_question, desired_outcome, case_context
                )
            )
            outcome_questions.append(outcome_question)

        return outcome_questions

    async def _estimate_outcome_probability(self, question: PreApprovedQuestion,
                                          outcome: str, context: Dict[str, Any]) -> Decimal:
        """Estimate probability of achieving desired outcome"""
        # Mock implementation - would use ML/historical data
        base_probability = Decimal("0.5")

        # Adjust based on question complexity
        complexity_factor = Decimal("1.0") - (Decimal(str(question.complexity_level)) / Decimal("20.0"))
        base_probability += complexity_factor * Decimal("0.1")

        # Adjust based on question effectiveness score
        if question.effectiveness_score > Decimal("0.0"):
            base_probability += question.effectiveness_score * Decimal("0.2")

        return min(Decimal("1.0"), max(Decimal("0.0"), base_probability))

    async def submit_for_approval(self, custom_question_id: str) -> bool:
        """Submit custom question for approval to be added to bank"""
        custom_question = self.custom_questions.get(custom_question_id)
        if not custom_question:
            return False

        custom_question.approval_requested = True
        self.approval_queue.append(custom_question_id)
        return True

    async def get_approval_queue(self) -> List[CustomQuestion]:
        """Get questions pending approval"""
        return [self.custom_questions[qid] for qid in self.approval_queue
                if qid in self.custom_questions]

    async def approve_custom_question(self, custom_question_id: str, approved_by: str) -> PreApprovedQuestion:
        """Approve custom question and add to main bank"""
        custom_question = self.custom_questions.get(custom_question_id)
        if not custom_question:
            raise ValueError("Custom question not found")

        # Create approved question from custom question
        approved_question = PreApprovedQuestion(
            question_text=custom_question.question_text,
            approval_status=ApprovalStatus.APPROVED,
            approved_by=approved_by,
            approval_date=datetime.utcnow()
        )

        self.questions[approved_question.question_id] = approved_question
        await self._index_question(approved_question)

        # Mark custom question as approved
        custom_question.approved_for_bank = True
        custom_question.usage_restricted = False

        # Remove from approval queue
        if custom_question_id in self.approval_queue:
            self.approval_queue.remove(custom_question_id)

        return approved_question

    async def get_questions_by_type(self, question_type: QuestionType) -> List[PreApprovedQuestion]:
        """Get all questions of a specific type"""
        return [q for q in self.questions.values() if q.question_type == question_type]

    async def get_questions_by_category(self, category: QuestionCategory) -> List[PreApprovedQuestion]:
        """Get all questions in a category"""
        return [q for q in self.questions.values() if q.category == category]

    async def update_usage_statistics(self, question_id: str, was_effective: bool):
        """Update usage statistics for a question"""
        question = self.questions.get(question_id)
        if not question:
            return

        question.usage_count += 1

        # Update effectiveness score using weighted average
        if was_effective:
            new_score = Decimal("1.0")
        else:
            new_score = Decimal("0.0")

        # Weighted average with previous scores
        weight = Decimal("0.1")  # New score weight
        question.effectiveness_score = (
            (Decimal("1.0") - weight) * question.effectiveness_score +
            weight * new_score
        )

    async def get_question_analytics(self) -> Dict[str, Any]:
        """Get analytics about question bank usage"""
        total_questions = len(self.questions)
        approved_questions = len([q for q in self.questions.values()
                                if q.approval_status == ApprovalStatus.APPROVED])

        usage_stats = {
            "total_usage": sum(q.usage_count for q in self.questions.values()),
            "avg_effectiveness": sum(q.effectiveness_score for q in self.questions.values()) / len(self.questions) if self.questions else Decimal("0.0"),
            "most_used": max(self.questions.values(), key=lambda q: q.usage_count, default=None)
        }

        category_breakdown = {}
        for category in QuestionCategory:
            category_questions = [q for q in self.questions.values() if q.category == category]
            category_breakdown[category.value] = {
                "count": len(category_questions),
                "usage": sum(q.usage_count for q in category_questions),
                "avg_effectiveness": sum(q.effectiveness_score for q in category_questions) / len(category_questions) if category_questions else Decimal("0.0")
            }

        return {
            "total_questions": total_questions,
            "approved_questions": approved_questions,
            "pending_approval": len(self.approval_queue),
            "usage_statistics": usage_stats,
            "category_breakdown": category_breakdown,
            "custom_questions": len(self.custom_questions)
        }


# Global question bank instance
question_bank = QuestionBank()


async def get_question_bank_endpoints() -> List[Dict[str, str]]:
    """Get all question bank endpoints"""
    return [
        {"method": "GET", "path": "/qa/questions"},
        {"method": "GET", "path": "/qa/questions/search"},
        {"method": "POST", "path": "/qa/questions/custom"},
        {"method": "GET", "path": "/qa/questions/{question_id}/variations"},
        {"method": "GET", "path": "/qa/questions/{question_id}/follow-ups"},
        {"method": "POST", "path": "/qa/questions/outcome-based"},
        {"method": "GET", "path": "/qa/questions/approval-queue"},
        {"method": "PUT", "path": "/qa/questions/{question_id}/approve"},
        {"method": "POST", "path": "/qa/questions/{question_id}/usage"},
        {"method": "GET", "path": "/qa/questions/analytics"},
        {"method": "GET", "path": "/qa/questions/by-type/{question_type}"},
        {"method": "GET", "path": "/qa/questions/by-category/{category}"},
    ]


async def initialize_question_bank() -> bool:
    """Initialize the question bank system"""
    try:
        await question_bank.initialize_default_questions()
        print("Question Bank System initialized successfully")
        print("Available endpoints: 12")
        print(f"Pre-approved questions loaded: {len(question_bank.questions)}")
        return True
    except Exception as e:
        print(f"Error initializing question bank: {e}")
        return False