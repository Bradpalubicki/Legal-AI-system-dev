"""
Conversation Memory System
Maintains conversation context, previous answers, and generates intelligent follow-ups.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import json


class ConversationState(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageType(Enum):
    QUESTION = "question"
    ANSWER = "answer"
    CLARIFICATION = "clarification"
    FOLLOW_UP = "follow_up"
    SUMMARY = "summary"
    SYSTEM = "system"


class ContextRelevance(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    IRRELEVANT = "irrelevant"


class MemoryType(Enum):
    SHORT_TERM = "short_term"    # Current conversation
    MEDIUM_TERM = "medium_term"  # Recent conversations (days)
    LONG_TERM = "long_term"      # Historical patterns (months)
    CASE_SPECIFIC = "case_specific"  # All conversations for specific case


@dataclass
class ConversationMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""
    message_type: MessageType = MessageType.QUESTION
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: str = ""
    context_tags: List[str] = field(default_factory=list)
    referenced_messages: List[str] = field(default_factory=list)
    confidence_score: Optional[Decimal] = None
    validation_status: str = ""
    follow_up_questions: List[str] = field(default_factory=list)


@dataclass
class ConversationContext:
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""
    case_id: Optional[str] = None
    client_id: Optional[str] = None
    context_summary: str = ""
    key_facts: List[str] = field(default_factory=list)
    legal_issues: List[str] = field(default_factory=list)
    ongoing_questions: List[str] = field(default_factory=list)
    resolved_questions: List[str] = field(default_factory=list)
    context_variables: Dict[str, Any] = field(default_factory=dict)
    relevance_score: Decimal = field(default=Decimal("1.0"))
    last_updated: datetime = field(default_factory=datetime.utcnow)
    expiry_date: Optional[datetime] = None


@dataclass
class ConversationSummary:
    summary_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""
    summary_text: str = ""
    key_decisions: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    unresolved_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence_metrics: Dict[str, Decimal] = field(default_factory=dict)
    generated_timestamp: datetime = field(default_factory=datetime.utcnow)
    auto_generated: bool = True


@dataclass
class FollowUpSuggestion:
    suggestion_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""
    suggested_question: str = ""
    rationale: str = ""
    priority: int = 1  # 1-10 scale
    context_relevance: ContextRelevance = ContextRelevance.MEDIUM
    estimated_value: Decimal = field(default=Decimal("0.5"))
    requires_clarification: bool = False
    related_messages: List[str] = field(default_factory=list)
    generated_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationPattern:
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_name: str = ""
    question_sequence: List[str] = field(default_factory=list)
    typical_outcomes: List[str] = field(default_factory=list)
    success_rate: Decimal = field(default=Decimal("0.0"))
    usage_frequency: int = 0
    case_types: List[str] = field(default_factory=list)
    avg_conversation_length: int = 0
    effectiveness_score: Decimal = field(default=Decimal("0.0"))


@dataclass
class PreviousAnswerReference:
    reference_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_question_id: str = ""
    previous_answer_id: str = ""
    similarity_score: Decimal = field(default=Decimal("0.0"))
    context_match: bool = False
    update_required: bool = False
    consistency_check: str = ""
    reuse_recommendation: str = ""


class ConversationMemory:
    def __init__(self):
        self.conversations = {}
        self.messages = {}
        self.contexts = {}
        self.summaries = {}
        self.patterns = {}
        self.follow_up_suggestions = {}
        self.answer_references = {}

        # Memory management
        self.short_term_limit = 50  # messages
        self.medium_term_days = 30
        self.long_term_months = 12

        # Context tracking
        self.active_contexts = {}
        self.context_decay_hours = 24

    async def start_conversation(self, user_id: str, case_id: Optional[str] = None,
                               client_id: Optional[str] = None) -> str:
        """Start a new conversation and initialize context"""
        conversation_id = str(uuid.uuid4())

        # Create initial context
        context = ConversationContext(
            conversation_id=conversation_id,
            case_id=case_id,
            client_id=client_id,
            context_summary="New conversation started"
        )

        self.conversations[conversation_id] = {
            "state": ConversationState.ACTIVE,
            "user_id": user_id,
            "case_id": case_id,
            "client_id": client_id,
            "started_at": datetime.utcnow(),
            "message_count": 0,
            "context_id": context.context_id
        }

        self.contexts[context.context_id] = context
        self.active_contexts[conversation_id] = context.context_id

        return conversation_id

    async def add_message(self, conversation_id: str, message_type: MessageType,
                         content: str, user_id: str, metadata: Dict[str, Any] = None) -> ConversationMessage:
        """Add a message to the conversation"""
        message = ConversationMessage(
            conversation_id=conversation_id,
            message_type=message_type,
            content=content,
            user_id=user_id,
            metadata=metadata or {}
        )

        # Extract context tags from content
        message.context_tags = await self._extract_context_tags(content)

        # Store message
        self.messages[message.message_id] = message

        # Update conversation
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["message_count"] += 1
            self.conversations[conversation_id]["last_activity"] = datetime.utcnow()

        # Update context
        await self._update_context(conversation_id, message)

        # Check for previous answer references
        if message_type == MessageType.QUESTION:
            await self._find_previous_answers(message)

        # Generate follow-up suggestions for answers
        if message_type == MessageType.ANSWER:
            await self._generate_follow_up_suggestions(message)

        return message

    async def _extract_context_tags(self, content: str) -> List[str]:
        """Extract context tags from message content"""
        legal_terms = [
            "contract", "liability", "negligence", "damages", "jurisdiction",
            "statute of limitations", "discovery", "motion", "appeal", "settlement",
            "plaintiff", "defendant", "evidence", "witness", "testimony",
            "precedent", "constitutional", "federal", "state", "court"
        ]

        tags = []
        content_lower = content.lower()

        for term in legal_terms:
            if term in content_lower:
                tags.append(term)

        return tags

    async def _update_context(self, conversation_id: str, message: ConversationMessage):
        """Update conversation context based on new message"""
        context_id = self.active_contexts.get(conversation_id)
        if not context_id:
            return

        context = self.contexts.get(context_id)
        if not context:
            return

        # Add new context tags to key facts
        for tag in message.context_tags:
            if tag not in context.key_facts:
                context.key_facts.append(tag)

        # Update legal issues based on content analysis
        legal_issues = await self._identify_legal_issues(message.content)
        for issue in legal_issues:
            if issue not in context.legal_issues:
                context.legal_issues.append(issue)

        # Track ongoing vs resolved questions
        if message.message_type == MessageType.QUESTION:
            context.ongoing_questions.append(message.message_id)
        elif message.message_type == MessageType.ANSWER:
            # Mark related questions as resolved
            related_questions = await self._find_related_questions(message)
            for q_id in related_questions:
                if q_id in context.ongoing_questions:
                    context.ongoing_questions.remove(q_id)
                    context.resolved_questions.append(q_id)

        # Update context summary
        context.context_summary = await self._generate_context_summary(context)
        context.last_updated = datetime.utcnow()

        # Update relevance score based on recency and activity
        await self._update_context_relevance(context)

    async def _identify_legal_issues(self, content: str) -> List[str]:
        """Identify legal issues mentioned in content"""
        legal_issue_patterns = [
            "breach of contract", "personal injury", "medical malpractice",
            "employment discrimination", "intellectual property", "family law",
            "criminal defense", "immigration", "bankruptcy", "tax law",
            "constitutional rights", "civil rights", "product liability"
        ]

        issues = []
        content_lower = content.lower()

        for pattern in legal_issue_patterns:
            if pattern in content_lower:
                issues.append(pattern)

        return issues

    async def _find_related_questions(self, answer_message: ConversationMessage) -> List[str]:
        """Find questions that this answer addresses"""
        related = []
        conversation_id = answer_message.conversation_id

        # Look for recent questions in same conversation
        recent_messages = [m for m in self.messages.values()
                          if (m.conversation_id == conversation_id and
                              m.message_type == MessageType.QUESTION and
                              m.timestamp > answer_message.timestamp - timedelta(hours=1))]

        # Find questions with similar context tags
        answer_tags = set(answer_message.context_tags)
        for question in recent_messages:
            question_tags = set(question.context_tags)
            if len(answer_tags.intersection(question_tags)) > 0:
                related.append(question.message_id)

        return related

    async def _generate_context_summary(self, context: ConversationContext) -> str:
        """Generate a summary of the current conversation context"""
        summary_parts = []

        if context.key_facts:
            summary_parts.append(f"Key topics: {', '.join(context.key_facts[:5])}")

        if context.legal_issues:
            summary_parts.append(f"Legal issues: {', '.join(context.legal_issues[:3])}")

        ongoing_count = len(context.ongoing_questions)
        resolved_count = len(context.resolved_questions)
        summary_parts.append(f"Questions: {ongoing_count} ongoing, {resolved_count} resolved")

        return "; ".join(summary_parts)

    async def _update_context_relevance(self, context: ConversationContext):
        """Update context relevance score based on recency and activity"""
        time_since_update = datetime.utcnow() - context.last_updated
        hours_elapsed = time_since_update.total_seconds() / 3600

        # Decay relevance over time
        decay_factor = max(Decimal("0.1"), Decimal("1.0") - Decimal(str(hours_elapsed)) / Decimal(str(self.context_decay_hours)))
        context.relevance_score *= decay_factor

        # Boost relevance for active conversations
        activity_boost = Decimal(str(len(context.ongoing_questions))) * Decimal("0.1")
        context.relevance_score = min(Decimal("1.0"), context.relevance_score + activity_boost)

    async def _find_previous_answers(self, question: ConversationMessage):
        """Find previous answers that might be relevant to current question"""
        question_content = question.content.lower()
        question_tags = set(question.context_tags)

        # Search through previous answers
        previous_answers = [m for m in self.messages.values()
                          if m.message_type == MessageType.ANSWER]

        relevant_answers = []
        for answer in previous_answers:
            # Calculate similarity based on content and tags
            similarity = await self._calculate_content_similarity(question_content, answer.content.lower())
            tag_overlap = len(question_tags.intersection(set(answer.context_tags))) / max(len(question_tags), 1)

            combined_score = (similarity + Decimal(str(tag_overlap))) / Decimal("2.0")

            if combined_score > Decimal("0.3"):  # Threshold for relevance
                reference = PreviousAnswerReference(
                    current_question_id=question.message_id,
                    previous_answer_id=answer.message_id,
                    similarity_score=combined_score,
                    context_match=tag_overlap > 0.5
                )

                # Check if answer needs updating
                reference.update_required = await self._check_answer_currency(answer)
                reference.consistency_check = await self._check_answer_consistency(answer)

                self.answer_references[reference.reference_id] = reference
                relevant_answers.append(reference)

    async def _calculate_content_similarity(self, text1: str, text2: str) -> Decimal:
        """Calculate similarity between two text contents"""
        # Simple word overlap similarity (would use more sophisticated NLP in production)
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return Decimal("0.0")

        overlap = len(words1.intersection(words2))
        total = len(words1.union(words2))

        return Decimal(str(overlap)) / Decimal(str(total))

    async def _check_answer_currency(self, answer: ConversationMessage) -> bool:
        """Check if answer information is still current"""
        # Check age of answer
        age_days = (datetime.utcnow() - answer.timestamp).days

        # Legal information older than 6 months might need updating
        return age_days > 180

    async def _check_answer_consistency(self, answer: ConversationMessage) -> str:
        """Check consistency of answer with recent information"""
        # Mock implementation - would cross-reference with legal databases
        return "consistent"

    async def _generate_follow_up_suggestions(self, answer: ConversationMessage):
        """Generate intelligent follow-up questions based on answer"""
        content = answer.content.lower()
        context_tags = answer.context_tags

        # Generate suggestions based on answer content
        suggestions = []

        # If answer mentions legal standards, suggest clarification
        if any(term in content for term in ["standard", "burden", "proof", "test"]):
            suggestions.append(FollowUpSuggestion(
                conversation_id=answer.conversation_id,
                suggested_question="What evidence would be needed to meet this legal standard?",
                rationale="Answer mentioned legal standards - clarification on evidence requirements",
                priority=7,
                context_relevance=ContextRelevance.HIGH
            ))

        # If answer mentions timeline, suggest next steps
        if any(term in content for term in ["deadline", "statute", "time", "days", "months"]):
            suggestions.append(FollowUpSuggestion(
                conversation_id=answer.conversation_id,
                suggested_question="What are the next steps and their deadlines?",
                rationale="Answer mentioned timelines - clarification on next steps needed",
                priority=8,
                context_relevance=ContextRelevance.HIGH
            ))

        # If answer mentions risks, suggest mitigation strategies
        if any(term in content for term in ["risk", "liability", "damages", "penalty"]):
            suggestions.append(FollowUpSuggestion(
                conversation_id=answer.conversation_id,
                suggested_question="What strategies can we use to mitigate these risks?",
                rationale="Answer mentioned risks - risk mitigation strategies needed",
                priority=6,
                context_relevance=ContextRelevance.MEDIUM
            ))

        # Store suggestions
        for suggestion in suggestions:
            self.follow_up_suggestions[suggestion.suggestion_id] = suggestion

    async def get_conversation_history(self, conversation_id: str,
                                     message_type: Optional[MessageType] = None) -> List[ConversationMessage]:
        """Get conversation history with optional filtering"""
        messages = [m for m in self.messages.values()
                   if m.conversation_id == conversation_id]

        if message_type:
            messages = [m for m in messages if m.message_type == message_type]

        return sorted(messages, key=lambda m: m.timestamp)

    async def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get current context for a conversation"""
        context_id = self.active_contexts.get(conversation_id)
        return self.contexts.get(context_id) if context_id else None

    async def get_follow_up_suggestions(self, conversation_id: str,
                                      limit: int = 5) -> List[FollowUpSuggestion]:
        """Get follow-up suggestions for a conversation"""
        suggestions = [s for s in self.follow_up_suggestions.values()
                      if s.conversation_id == conversation_id]

        # Sort by priority and relevance
        suggestions.sort(key=lambda s: (s.priority, s.estimated_value), reverse=True)

        return suggestions[:limit]

    async def get_previous_answer_references(self, question_id: str) -> List[PreviousAnswerReference]:
        """Get references to previous answers for a question"""
        return [ref for ref in self.answer_references.values()
                if ref.current_question_id == question_id]

    async def generate_conversation_summary(self, conversation_id: str) -> ConversationSummary:
        """Generate a comprehensive summary of the conversation"""
        messages = await self.get_conversation_history(conversation_id)
        context = await self.get_context(conversation_id)

        # Extract key information
        questions = [m for m in messages if m.message_type == MessageType.QUESTION]
        answers = [m for m in messages if m.message_type == MessageType.ANSWER]

        # Generate summary text
        summary_text = f"Conversation with {len(questions)} questions and {len(answers)} answers."
        if context:
            summary_text += f" Main topics: {', '.join(context.key_facts[:5])}."
            if context.legal_issues:
                summary_text += f" Legal issues: {', '.join(context.legal_issues[:3])}."

        # Identify key decisions and recommendations
        key_decisions = await self._extract_decisions(answers)
        recommendations = await self._extract_recommendations(answers)

        # Identify unresolved issues
        unresolved = []
        if context:
            for q_id in context.ongoing_questions:
                question = self.messages.get(q_id)
                if question:
                    unresolved.append(question.content[:100] + "...")

        summary = ConversationSummary(
            conversation_id=conversation_id,
            summary_text=summary_text,
            key_decisions=key_decisions,
            recommendations=recommendations,
            unresolved_issues=unresolved
        )

        self.summaries[summary.summary_id] = summary
        return summary

    async def _extract_decisions(self, answers: List[ConversationMessage]) -> List[str]:
        """Extract key decisions from answers"""
        decisions = []
        decision_indicators = ["decided", "determined", "concluded", "ruled", "resolved"]

        for answer in answers:
            content = answer.content.lower()
            if any(indicator in content for indicator in decision_indicators):
                # Extract sentence containing decision
                sentences = answer.content.split('.')
                for sentence in sentences:
                    if any(indicator in sentence.lower() for indicator in decision_indicators):
                        decisions.append(sentence.strip())
                        break

        return decisions[:5]  # Limit to top 5

    async def _extract_recommendations(self, answers: List[ConversationMessage]) -> List[str]:
        """Extract recommendations from answers"""
        recommendations = []
        rec_indicators = ["recommend", "suggest", "should", "advise", "propose"]

        for answer in answers:
            content = answer.content.lower()
            if any(indicator in content for indicator in rec_indicators):
                sentences = answer.content.split('.')
                for sentence in sentences:
                    if any(indicator in sentence.lower() for indicator in rec_indicators):
                        recommendations.append(sentence.strip())
                        break

        return recommendations[:5]  # Limit to top 5

    async def cleanup_old_conversations(self):
        """Clean up old conversations and manage memory"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.medium_term_days)

        # Archive old conversations
        for conv_id, conv_data in list(self.conversations.items()):
            last_activity = conv_data.get("last_activity", conv_data["started_at"])
            if last_activity < cutoff_date:
                conv_data["state"] = ConversationState.ARCHIVED

                # Remove from active contexts
                if conv_id in self.active_contexts:
                    del self.active_contexts[conv_id]

        # Clean up expired contexts
        for context_id, context in list(self.contexts.items()):
            if context.expiry_date and datetime.utcnow() > context.expiry_date:
                del self.contexts[context_id]

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about conversation memory usage"""
        return {
            "active_conversations": len([c for c in self.conversations.values()
                                       if c["state"] == ConversationState.ACTIVE]),
            "total_messages": len(self.messages),
            "active_contexts": len(self.active_contexts),
            "follow_up_suggestions": len(self.follow_up_suggestions),
            "answer_references": len(self.answer_references),
            "conversation_summaries": len(self.summaries),
            "memory_usage": {
                "short_term_messages": len([m for m in self.messages.values()
                                          if datetime.utcnow() - m.timestamp < timedelta(hours=24)]),
                "medium_term_messages": len([m for m in self.messages.values()
                                           if timedelta(hours=24) <= datetime.utcnow() - m.timestamp < timedelta(days=30)]),
                "long_term_messages": len([m for m in self.messages.values()
                                         if datetime.utcnow() - m.timestamp >= timedelta(days=30)])
            }
        }


# Global memory instance
conversation_memory = ConversationMemory()


async def get_memory_endpoints() -> List[Dict[str, str]]:
    """Get all conversation memory endpoints"""
    return [
        {"method": "POST", "path": "/qa/conversations"},
        {"method": "POST", "path": "/qa/conversations/{conversation_id}/messages"},
        {"method": "GET", "path": "/qa/conversations/{conversation_id}/history"},
        {"method": "GET", "path": "/qa/conversations/{conversation_id}/context"},
        {"method": "GET", "path": "/qa/conversations/{conversation_id}/follow-ups"},
        {"method": "GET", "path": "/qa/questions/{question_id}/previous-answers"},
        {"method": "POST", "path": "/qa/conversations/{conversation_id}/summary"},
        {"method": "GET", "path": "/qa/conversations/{conversation_id}/summary"},
        {"method": "POST", "path": "/qa/memory/cleanup"},
        {"method": "GET", "path": "/qa/memory/stats"},
    ]


async def initialize_conversation_memory() -> bool:
    """Initialize the conversation memory system"""
    try:
        print("Conversation Memory System initialized successfully")
        print("Available endpoints: 10")
        return True
    except Exception as e:
        print(f"Error initializing conversation memory: {e}")
        return False