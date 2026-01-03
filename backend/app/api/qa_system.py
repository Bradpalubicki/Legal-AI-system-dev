"""
Q&A System API for Legal AI System
Interactive document questions and answers using OpenAI
"""

import logging
import uuid as uuid_lib
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json
import os
import anthropic

from ..src.services.dual_ai_service import dual_ai_service, optimized_ai_client
from ..src.shared.ai.defense_builder import DefenseBuilder, ChatContext, process_message
from ..src.ai.prompts import AI_PROMPTS, ULTRA_CONCISE_PROMPT, get_prompt, format_prompt, get_model_config
from ..src.shared.ai.case_interviewer import case_interviewer
from ..src.shared.ai.question_flows import adaptive_questioner, QUESTION_FLOWS
from ..src.shared.ai.document_aware_interviewer import document_aware_interviewer, DocumentAwareInterviewer
from ..src.shared.ai.concise_ai_wrapper import force_concise_claude, aggressive_strip_verbosity
from ..src.middleware.force_correct_behavior import ForceCorrectBehavior, apply_forced_corrections
from ..src.core.database import get_db
from ..models.legal_documents import Document, QASession, QAMessage
from ..src.services.document_context_manager import get_context_manager
from ..api.deps.auth import get_current_user, CurrentUser
import random

logger = logging.getLogger(__name__)


def generate_follow_up_question(user_message: str, case_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generates strategic follow-up questions like an experienced attorney
    Returns question with options for quick answers
    """
    msg = user_message.lower()

    # Debt collection questions - Attorney-level inquiry
    if any(kw in msg for kw in ['debt', 'owe', 'collection', 'creditor']):
        questions = [
            {
                'text': 'Critical for statute of limitations: When did you last make a payment or acknowledge this debt in writing?',
                'options': ['Within last year', '1-3 years ago', '3-5 years ago', 'Over 5 years ago', 'Never acknowledged'],
                'purpose': 'statute_of_limitations'
            },
            {
                'text': 'Legal standing inquiry: Is the plaintiff the original creditor, or did they purchase this debt?',
                'options': ['Original creditor', 'Third-party debt buyer', 'Collection agency', 'Unknown - not disclosed'],
                'purpose': 'establish_standing'
            },
            {
                'text': 'Have they provided documentary evidence establishing the chain of title for this debt (assignment records)?',
                'options': ['Yes, complete documentation', 'Partial documents', 'No documentation provided', 'Have not reviewed yet'],
                'purpose': 'chain_of_title'
            },
            {
                'text': 'Amount verification: Does the claimed amount match your records, or are there unexplained fees/interest?',
                'options': ['Matches my records', 'Higher than expected', 'Includes improper fees', 'Cannot verify'],
                'purpose': 'verify_amount'
            }
        ]
        return random.choice(questions)

    # Lawsuit/served questions - Strategic attorney inquiry
    if any(kw in msg for kw in ['sued', 'lawsuit', 'served', 'papers', 'summons']):
        questions = [
            {
                'text': 'Procedural timeline: What date were you personally served with the summons and complaint?',
                'options': ['Within last 7 days', '8-20 days ago', '21-30 days ago', 'Over 30 days ago', 'Not yet served'],
                'purpose': 'response_deadline'
            },
            {
                'text': 'Critical deadline analysis: How many days do you have to file your Answer or responsive pleading?',
                'options': ['Under 10 days remaining', '10-20 days', '20-30 days', 'Over 30 days', 'Unclear from documents'],
                'purpose': 'urgent_timeline'
            },
            {
                'text': 'Service of process verification: Was service proper (personal delivery, substitute service, or publication)?',
                'options': ['Personal service', 'Left with household member', 'Certified mail', 'Improper/defective service', 'Unsure'],
                'purpose': 'service_validity'
            },
            {
                'text': 'Venue and jurisdiction: Was this case filed in the correct court with proper jurisdiction over you?',
                'options': ['Appears correct', 'Wrong county/venue', 'Lacks personal jurisdiction', 'Need to analyze'],
                'purpose': 'jurisdictional_defense'
            }
        ]
        return random.choice(questions)

    # Eviction questions - Attorney-level landlord/tenant inquiry
    if any(kw in msg for kw in ['evict', 'landlord', 'rent', 'tenant']):
        questions = [
            {
                'text': 'Notice requirements: Did the landlord provide legally compliant written notice (e.g., 30-day, 3-day pay-or-quit)?',
                'options': ['Yes, proper notice', 'Notice was defective', 'Insufficient time given', 'No notice received', 'Need to verify'],
                'purpose': 'proper_notice'
            },
            {
                'text': 'Habitability defense potential: Are there documented code violations or uninhabitable conditions?',
                'options': ['Yes - severe violations', 'Yes - moderate issues', 'Minor issues', 'No violations', 'Haven\'t documented yet'],
                'purpose': 'habitability_defense'
            },
            {
                'text': 'Evidence preservation: Do you have contemporaneous written documentation (photos, repair requests, inspection reports)?',
                'options': ['Yes - comprehensive evidence', 'Some documentation', 'Verbal only', 'No documentation', 'Can obtain'],
                'purpose': 'evidence_gathering'
            },
            {
                'text': 'Retaliation analysis: Did this eviction follow complaints about repairs, code enforcement calls, or tenant organizing?',
                'options': ['Yes - within 6 months', 'Possibly related', 'No connection', 'Unclear timeline'],
                'purpose': 'retaliation_defense'
            }
        ]
        return random.choice(questions)

    # Bankruptcy questions
    if any(kw in msg for kw in ['bankrupt', 'chapter 7', 'chapter 13']):
        questions = [
            {
                'text': 'Is this mainly business debt or personal debt?',
                'options': ['Business', 'Personal', 'Mix of both'],
                'purpose': 'bankruptcy_type'
            },
            {
                'text': 'What is your approximate total debt amount?',
                'options': ['Under $10k', '$10k-$50k', '$50k-$100k', 'Over $100k'],
                'purpose': 'debt_assessment'
            },
            {
                'text': 'Do you own a home or significant assets?',
                'options': ['Own home', 'Own car', 'Both', 'Neither'],
                'purpose': 'asset_protection'
            }
        ]
        return random.choice(questions)

    # Default questions if context unclear
    default_questions = [
        {
            'text': 'What type of legal issue are you facing?',
            'options': ['Debt collection', 'Eviction', 'Lawsuit', 'Bankruptcy', 'Other'],
            'purpose': 'case_classification'
        },
        {
            'text': 'When did this legal issue start?',
            'options': ['This week', 'This month', '1-6 months ago', 'Over 6 months ago'],
            'purpose': 'timeline_assessment'
        },
        {
            'text': 'Have you received any court papers or official documents?',
            'options': ['Yes', 'No', 'Not sure if official'],
            'purpose': 'case_status'
        },
        {
            'text': 'Is there a deadline you need to meet?',
            'options': ['Yes - urgent (under 10 days)', 'Yes - soon (10-30 days)', 'No deadline yet', 'Not sure'],
            'purpose': 'urgency_assessment'
        },
        {
            'text': 'What dollar amount is involved in this case?',
            'options': ['Under $1000', '$1000-$10000', '$10000-$50000', 'Over $50000'],
            'purpose': 'amount_assessment'
        }
    ]

    return random.choice(default_questions)


def get_hardcoded_concise_answer(message: str) -> str:
    """
    HARDCODED concise responses if AI isn't cooperating
    Maximum 50 words each
    """
    msg = message.lower()

    # Debt responses
    if 'debt' in msg or 'owe' in msg or 'collection' in msg:
        return "Request debt validation in writing. Check statute of limitations (4-6 years in most states). If past statute, file that defense. Demand proof they own the debt."

    # Lawsuit responses
    if 'sued' in msg or 'lawsuit' in msg:
        return "File answer within 20-30 days. Deny claims you dispute. Assert all applicable defenses. Missing deadline means automatic loss."

    # Eviction responses
    if 'evict' in msg:
        return "Respond within 5 days. Document repair issues with photos. File habitability defense if landlord failed repairs. Pay rent into court or vacate."

    # Bankruptcy responses
    if 'bankrupt' in msg:
        return "Chapter 7 erases most debt, takes 3-4 months, costs $300-400 filing. Chapter 13 repays over 3-5 years, keeps assets. Stop creditor harassment immediately upon filing."

    # Divorce responses
    if 'divorce' in msg:
        return "File petition in county court. Divide assets 50/50 or negotiate. Arrange child custody and support. Takes 3-6 months minimum with waiting period."

    # Foreclosure responses
    if 'foreclos' in msg:
        return "Apply for loan modification now. Document income and hardship. Request mediation. File answer to delay sale. Bankruptcy stops foreclosure automatically."

    # Default response
    return "Respond by deadline. Gather all documents. List your defenses. File proper forms with court. Missing deadlines means automatic loss."

router = APIRouter(prefix="/api/v1/qa", tags=["Q&A System"])

# In-memory storage for conversation history (in production, use a database)
conversation_store = {}

# Store document-aware interviewers per session
document_interviewers = {}

class QuestionRequest(BaseModel):
    document_text: Optional[str] = ""
    document_analysis: Optional[Dict[str, Any]] = None
    question: str
    session_id: Optional[str] = None
    document_id: Optional[str] = None  # For linking to Document in database

class FollowUpRequest(BaseModel):
    session_id: str
    question: str

class StrategicQuestionsRequest(BaseModel):
    document_analysis: Dict[str, Any]

class DefenseBuilderRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class DefenseBuilderChat(BaseModel):
    session_id: str
    message: str

class StreamQuestionRequest(BaseModel):
    question: str
    document_text: Optional[str] = ""
    session_id: Optional[str] = None


class LegalEducationChatRequest(BaseModel):
    """Request for general legal education chat - no documents required"""
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None


# ============================================================================
# LEGAL EDUCATION CHAT - General Purpose AI Assistant
# ============================================================================

@router.post("/chat")
async def legal_education_chat(
    request: LegalEducationChatRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    General-purpose Legal Education AI Assistant

    Provides educational information about legal topics without requiring documents.
    Can answer questions like "What are the types of bankruptcy?" or explain legal concepts.

    Features:
    - Full conversation history
    - Educational legal information
    - Comprehensive explanations
    - No document required

    Example questions:
    - "What are the different types of bankruptcy?"
    - "Explain statute of limitations"
    - "What is the difference between Chapter 7 and Chapter 13 bankruptcy?"
    - "How does small claims court work?"
    """
    try:
        session_id = request.session_id or f"legal_ed_{datetime.now().timestamp()}"
        user_id = request.user_id or "anonymous"

        # SECURITY: Get or create QA session for general legal education - filter by user_id
        qa_session = db.query(QASession).filter(
            QASession.session_id == session_id,
            QASession.user_id == current_user.user_id  # Only user's own sessions
        ).first()

        if not qa_session:
            # Create new legal education session (no document required)
            qa_session = QASession(
                id=str(uuid_lib.uuid4()),
                user_id=current_user.user_id,  # SECURITY: Associate session with user
                document_id=None,  # No document for general legal education
                session_id=session_id,
                started_at=datetime.utcnow(),
                is_active=True,
                question_count=0,
                document_text=None,
                document_analysis={"type": "legal_education", "purpose": "general_legal_questions"},
                collected_info={},
                case_type="general_legal_education",
                last_question=None,
                using_document_aware=False
            )
            db.add(qa_session)
            db.flush()

        # Load conversation history
        conversation_history = db.query(QAMessage).filter(
            QAMessage.session_id == qa_session.id
        ).order_by(QAMessage.timestamp).all()

        # Build conversation context for Claude
        conversation_context = []
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            conversation_context.append({
                "role": msg.role if msg.role in ["user", "assistant"] else ("user" if msg.role == "user" else "assistant"),
                "content": msg.content
            })

        # Add current message
        conversation_context.append({
            "role": "user",
            "content": request.message
        })

        # Create comprehensive legal education prompt
        system_prompt = """You are a knowledgeable Legal Education Assistant designed to help people learn about legal concepts and processes.

IMPORTANT GUIDELINES:
1. **Educational Purpose Only**: All information provided is for educational purposes and does not constitute legal advice
2. **Clear Explanations**: Explain legal concepts in clear, understandable language
3. **Comprehensive but Concise**: Provide thorough answers while remaining focused
4. **Examples**: Use practical examples when helpful
5. **Encourage Professional Consultation**: Remind users to consult licensed attorneys for specific legal matters
6. **Accuracy**: Provide accurate, up-to-date legal information
7. **Neutral Tone**: Maintain an educational, non-judgmental tone

RESPONSE STRUCTURE:
- Start with a direct answer to the question
- Provide clear explanations with examples
- Include relevant legal principles or concepts
- End with appropriate disclaimers

EDUCATIONAL DISCLAIMER:
Always include: "This information is for educational purposes only and does not constitute legal advice. For specific legal matters, consult a licensed attorney in your jurisdiction."

Answer the user's legal education question comprehensively but accessibly."""

        # Call Claude Sonnet for comprehensive legal education
        from anthropic import Anthropic
        import os

        api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="AI service unavailable. Please configure API keys."
            )

        client = Anthropic(api_key=api_key)

        # Use Claude Sonnet 4.5 for high-quality educational content
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",  # Latest Sonnet 4.5
            max_tokens=2500,  # Allow comprehensive educational responses
            temperature=0.3,  # Slightly higher for more natural educational tone
            system=system_prompt,
            messages=conversation_context
        )

        answer = response.content[0].text if response.content else "Unable to generate response."

        # Save user message to database
        user_message = QAMessage(
            id=str(uuid_lib.uuid4()),
            session_id=qa_session.id,
            role="user",
            content=request.message,
            timestamp=datetime.utcnow()
        )
        db.add(user_message)

        # Save AI response to database
        ai_message = QAMessage(
            id=str(uuid_lib.uuid4()),
            session_id=qa_session.id,
            role="assistant",
            content=answer,
            timestamp=datetime.utcnow()
        )
        db.add(ai_message)

        # Update session
        qa_session.question_count += 1
        qa_session.last_question = request.message
        qa_session.updated_at = datetime.utcnow()

        db.commit()

        # Generate suggested follow-up questions based on the topic
        suggested_questions = _generate_legal_education_suggestions(request.message, answer)

        return {
            "success": True,
            "answer": answer,
            "session_id": session_id,
            "message_count": qa_session.question_count,
            "suggested_questions": suggested_questions,
            "timestamp": datetime.utcnow().isoformat(),
            "educational_disclaimer": "This information is for educational purposes only and does not constitute legal advice. For specific legal matters, consult a licensed attorney in your jurisdiction."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in legal education chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Legal education chat error: {str(e)}"
        )


def _generate_legal_education_suggestions(question: str, answer: str) -> List[str]:
    """Generate relevant follow-up questions for legal education"""
    question_lower = question.lower()

    # Bankruptcy-related suggestions
    if any(kw in question_lower for kw in ['bankruptcy', 'chapter 7', 'chapter 13', 'chapter 11']):
        return [
            "What is the difference between Chapter 7 and Chapter 13 bankruptcy?",
            "What debts cannot be discharged in bankruptcy?",
            "How does bankruptcy affect my credit score?",
            "What is the means test in bankruptcy?",
            "Can I keep my house if I file for bankruptcy?"
        ]

    # Civil litigation suggestions
    if any(kw in question_lower for kw in ['lawsuit', 'sue', 'court', 'litigation', 'claim']):
        return [
            "What is the statute of limitations?",
            "What is the difference between small claims and regular court?",
            "What happens if I don't respond to a lawsuit?",
            "What is discovery in a lawsuit?",
            "How long does a typical lawsuit take?"
        ]

    # Criminal law suggestions
    if any(kw in question_lower for kw in ['criminal', 'arrest', 'charges', 'felony', 'misdemeanor']):
        return [
            "What is the difference between a felony and misdemeanor?",
            "What are my rights when arrested?",
            "What is probable cause?",
            "How does bail work?",
            "What is a plea bargain?"
        ]

    # Contracts suggestions
    if any(kw in question_lower for kw in ['contract', 'agreement', 'breach']):
        return [
            "What makes a contract legally binding?",
            "What is breach of contract?",
            "Can I get out of a contract?",
            "What damages can I recover for breach of contract?",
            "Do verbal contracts hold up in court?"
        ]

    # Family law suggestions
    if any(kw in question_lower for kw in ['divorce', 'custody', 'child support', 'alimony', 'family law']):
        return [
            "How is child custody determined?",
            "What factors affect child support calculations?",
            "What is the difference between legal and physical custody?",
            "How long does a divorce take?",
            "What is marital property?"
        ]

    # Default general legal questions
    return [
        "What is the difference between civil and criminal law?",
        "How do I find a good attorney?",
        "What should I bring to a consultation with a lawyer?",
        "How much do attorneys typically cost?",
        "What are my rights in court?"
    ]


@router.post("/ask")
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    DOCUMENT-AWARE Q&A: Analyzes document first, then asks targeted questions

    Uses document context and analysis to provide informed answers
    Maintains conversation history for follow-up questions
    SECURITY: Only accesses user's own documents and sessions.
    """
    try:
        logger.info(f"====== Q&A REQUEST ====== Question: {request.question}")
        session_id = request.session_id or f"session_{datetime.now().timestamp()}"
        document_id = request.document_id

        # TEMPORARILY DISABLED: Document-aware interviewer has dependency issues
        # Check if we need to do document analysis first
        # if session_id not in document_interviewers and request.document_text:
        #     ... (code disabled)

        # SECURITY: Get or create QA session from database - filter by user_id
        qa_session = None
        if document_id:
            qa_session = db.query(QASession).filter(
                QASession.document_id == document_id,
                QASession.session_id == session_id,
                QASession.user_id == current_user.user_id  # Only user's own sessions
            ).first()

            if not qa_session:
                # Create new QA session in database with user ownership
                qa_session = QASession(
                    id=str(uuid_lib.uuid4()),
                    user_id=current_user.user_id,  # SECURITY: Associate session with user
                    document_id=document_id,
                    session_id=session_id,
                    started_at=datetime.utcnow(),
                    is_active=True,
                    question_count=0,
                    document_text=request.document_text[:8000],
                    document_analysis=request.document_analysis,
                    collected_info={},
                    case_type=None,
                    last_question=None,
                    using_document_aware=False
                )
                db.add(qa_session)
                db.flush()  # Get the qa_session.id

        # Build session context from database or create fallback
        if qa_session:
            # Load conversation from database messages
            messages = db.query(QAMessage).filter(
                QAMessage.session_id == qa_session.id
            ).order_by(QAMessage.timestamp).all()

            conversation = []
            i = 0
            while i < len(messages):
                if messages[i].role == "user" and i + 1 < len(messages) and messages[i + 1].role == "ai":
                    conversation.append({
                        "question": messages[i].content,
                        "answer": messages[i + 1].content,
                        "timestamp": messages[i].timestamp.isoformat(),
                        "confidence": messages[i + 1].confidence.get("score", 0.8) if messages[i + 1].confidence else 0.8,
                        "follow_up": messages[i + 1].follow_up_question
                    })
                    i += 2
                else:
                    i += 1

            session_context = {
                "document_analysis": qa_session.document_analysis or request.document_analysis or {},
                "document_text": qa_session.document_text or (request.document_text or "")[:8000],
                "conversation": conversation,
                "created_at": qa_session.started_at.isoformat(),
                "case_type": qa_session.case_type,
                "collected_info": qa_session.collected_info or {},
                "question_count": qa_session.question_count,
                "last_question": qa_session.last_question,
                "using_document_aware": qa_session.using_document_aware or False
            }
        else:
            # Fallback for sessions without document_id (backward compatibility)
            if session_id not in conversation_store:
                conversation_store[session_id] = {
                    "document_analysis": request.document_analysis or {},
                    "document_text": (request.document_text or "")[:8000],
                    "conversation": [],
                    "created_at": datetime.now().isoformat(),
                    "case_type": None,
                    "collected_info": {},
                    "question_count": 0,
                    "last_question": None,
                    "using_document_aware": False
                }
            session_context = conversation_store[session_id]
            conversation = session_context["conversation"]

        # Check if using document-aware interviewer
        if session_context.get("using_document_aware") and session_id in document_interviewers:
            interviewer = document_interviewers[session_id]
            last_question = session_context.get("last_question")

            if last_question:
                # Process answer in document context
                result = await interviewer.process_answer_and_generate_next(
                    last_question,
                    request.question
                )

                # Build response based on result type
                if result['type'] == 'defense_found':
                    response_text = f"{result['message']}\n\nRecommended action: {result.get('action', 'Consult attorney immediately')}"

                    return {
                        "session_id": session_id,
                        "answer": response_text,
                        "defense_status": result.get('defense'),
                        "confidence": 0.95,
                        "sources": [],
                        "follow_up_questions": [],
                        "suggested_questions": [],
                        "conversation_length": len(conversation),
                        "timestamp": datetime.now().isoformat(),
                        "response_type": "defense_found"
                    }

                # Answer question with comprehensive paralegal-level analysis
                ai_response = await _call_claude_paralegal_comprehensive(f"Answer this question: {request.question}")
                # Don't strip verbosity from comprehensive responses - users need complete answers

                # Add next document-aware question if available
                next_q = result.get('next_question')
                if next_q:
                    ai_response += f"\n\n**Based on your document, I need to know:** {next_q.get('text', next_q)}"
                    session_context["last_question"] = next_q.get('text', next_q) if isinstance(next_q, dict) else next_q
                    # Persist to database if qa_session exists
                    if qa_session:
                        qa_session.last_question = session_context["last_question"]

                # Add to conversation
                conversation.append({
                    "question": request.question,
                    "answer": ai_response,
                    "timestamp": datetime.now().isoformat()
                })

                completion = interviewer.get_completion_status()

                return {
                    "session_id": session_id,
                    "answer": ai_response,
                    "confidence": 0.9,
                    "sources": [],
                    "follow_up_questions": result.get('options', []),
                    "suggested_questions": [],
                    "conversation_length": len(conversation),
                    "timestamp": datetime.now().isoformat(),
                    "progress": f"{completion['questions_answered']} of {completion['total_questions']} answered",
                    "response_type": "document_aware_followup"
                }

        # Detect case type from first message
        if not session_context.get("case_type"):
            session_context["case_type"] = case_interviewer.detect_case_type(request.question)
            # Persist to database if qa_session exists
            if qa_session:
                qa_session.case_type = session_context["case_type"]

        # Check if this is an answer to our previous question
        last_question = session_context.get("last_question")
        if last_question:
            # Store the answer
            session_context["collected_info"][last_question] = request.question
            session_context["question_count"] = session_context.get("question_count", 0) + 1

            # Persist to database if qa_session exists
            if qa_session:
                qa_session.collected_info = session_context["collected_info"]
                qa_session.question_count = session_context["question_count"]

            # Check for smart follow-up based on specific answer
            smart_followup = case_interviewer.generate_smart_followup(last_question, request.question)
            if smart_followup and session_context["question_count"] < 5:
                # Return the smart follow-up immediately
                session_context["last_question"] = smart_followup
                # Persist to database if qa_session exists
                if qa_session:
                    qa_session.last_question = smart_followup
                    db.commit()
                return {
                    "session_id": session_id,
                    "answer": smart_followup,
                    "confidence": 0.9,
                    "sources": [],
                    "follow_up_questions": [],
                    "defense_options": [],
                    "quick_actions": [],
                    "suggested_questions": [],
                    "conversation_length": len(conversation),
                    "timestamp": datetime.now().isoformat(),
                    "is_question": True,
                    "progress": f"Question {session_context['question_count']} of 5-7",
                    "response_type": "interviewer_followup"
                }

        # Build context-aware prompt with collected information AND document text
        context_info = "\n".join([f"{q}: {a}" for q, a in session_context.get("collected_info", {}).items()])

        # Include document text in the prompt - THIS IS CRITICAL
        has_document = request.document_text and len(request.document_text.strip()) > 10

        # ============================================================================
        # DOCUMENT CONTEXT MANAGER - Prevents AI amnesia and hallucinations
        # ============================================================================
        # Use smart context building instead of blind truncation
        # OLD: document_text = request.document_text[:3000]  # Lost 99% of long docs
        # NEW: Uses 100K char context with semantic chunking

        if has_document and document_id:
            # Get context manager for database operations
            context_manager = get_context_manager(db)

            try:
                # Build smart context (100K chars vs old 3K limit!)
                # This extracts relevant sections instead of blind truncation
                document_context = context_manager.build_smart_context(
                    primary_document_id=document_id,
                    question=request.question,
                    max_chars=100000  # 33x more than before!
                )

                enhanced_prompt = f"""You are Sarah Chen, a senior litigation paralegal with 20+ years of experience. You're warm, approachable, and excellent at explaining complex legal issues in plain English while maintaining professional expertise.

YOUR CONVERSATIONAL STYLE:
- Speak naturally using "I" and "you" - this is a conversation, not a memo
- Start by acknowledging their concern/situation with empathy
- Use conversational transitions like "Here's what I see...", "Let me explain...", "I notice that..."
- Ask clarifying questions when something's unclear
- Show genuine interest in understanding their full situation
- Remember and reference details from earlier in our conversation

YOUR DEEP LEGAL EXPERTISE:
**BANKRUPTCY:** Chapter 7/11/13, automatic stay (11 USC § 362), discharge exceptions (11 USC § 523), exemptions
**DEBT COLLECTION:** FDCPA (15 USC § 1692), FCRA, TCPA, statute of limitations, validation rights
**CIVIL PROCEDURE:** FRCP, service of process, jurisdiction, answer deadlines, affirmative defenses
**EVIDENCE:** Business records (FRE 803(6)), authentication, burden of proof, chain of custody

{document_context}

CASE INFORMATION FROM OUR CONVERSATION:
{context_info if context_info else 'This is the start of our conversation'}

THEIR QUESTION:
{request.question}

YOUR RESPONSE APPROACH:

1. **START WITH EMPATHY** - Acknowledge what they're going through
   - "I can see this situation is stressful..." or "I understand your concern about..."

2. **ANALYZE WHAT YOU SEE** - Review their document and situation conversationally
   - "Looking at your document, I notice..."
   - Reference specific details: parties, amounts, dates, deadlines
   - Flag critical issues immediately: "This is time-sensitive because..."

3. **EXPLAIN THE LAW CLEARLY** - Apply legal expertise in plain English
   - Use statutes/rules but explain what they mean
   - "Under the FDCPA (15 USC § 1692g), you have certain rights. Here's what that means for you..."
   - Connect legal concepts to their specific situation

4. **GIVE STRATEGIC ADVICE** - Be direct about options and next steps
   - Discuss defenses, strengths, weaknesses
   - Suggest specific actions with timelines
   - Identify what evidence they need

5. **ASK CLARIFYING QUESTIONS** - Be curious and proactive
   - If information is missing: "To give you better guidance, I'd like to know..."
   - If something seems unclear: "Can you tell me more about..."

6. **END CONVERSATIONALLY** - Keep the dialogue flowing
   - "What other questions do you have about this?"
   - "Would you like me to explain any part of this in more detail?"

Write in natural paragraphs (4-6), not bullet points. Be warm but professional. Use legal precision but conversational tone.

YOUR RESPONSE:"""

                logger.info(f"Using DocumentContextManager for document_id={document_id} (smart context with semantic chunking)")

            except Exception as ctx_error:
                logger.warning(f"DocumentContextManager failed, falling back to truncation: {ctx_error}")
                # Fallback to larger truncation (still better than 3K)
                document_text = request.document_text[:50000]  # At least use 50K instead of 3K
                enhanced_prompt = f"""You are Sarah Chen, a senior litigation paralegal with 20+ years of experience. You're warm, approachable, and excellent at explaining complex legal issues in plain English while maintaining professional expertise.

YOUR CONVERSATIONAL STYLE:
- Speak naturally using "I" and "you" - this is a conversation, not a memo
- Start by acknowledging their concern/situation with empathy
- Use conversational transitions like "Here's what I see...", "Let me explain...", "I notice that..."
- Ask clarifying questions when something's unclear
- Show genuine interest in understanding their full situation
- Remember and reference details from earlier in our conversation

YOUR DEEP LEGAL EXPERTISE:

**BANKRUPTCY LAW:**
- Chapter 7 (liquidation): means test, exemptions, discharge timing
- Chapter 11 (reorganization): plan confirmation, cramdown, absolute priority rule
- Chapter 13 (wage earner): payment plans, confirmation requirements, discharge
- Automatic stay (11 USC § 362): violations, relief from stay, exceptions
- Discharge exceptions (11 USC § 523): fraud, willful injury, student loans, taxes
- Fraudulent transfers (11 USC § 548): actual and constructive fraud
- Preference actions (11 USC § 547): 90-day and insider preference periods
- Exemptions: federal exemptions (11 USC § 522(d)) vs state exemptions, wildcard exemption

**DEBT COLLECTION LAW:**
- Fair Debt Collection Practices Act (FDCPA, 15 USC § 1692): prohibited practices, validation rights, cease communication, damages ($1,000 statutory + actual damages)
- Fair Credit Reporting Act (FCRA, 15 USC § 1681): dispute rights, credit reporting violations, 7-year reporting period
- Telephone Consumer Protection Act (TCPA): robocalls, consent requirements, $500-$1,500 per violation
- State debt collection statutes and licensing requirements
- Statute of limitations by state (typically 3-6 years for written contracts)
- Time-barred debt collection restrictions

**CIVIL PROCEDURE:**
- Federal Rules of Civil Procedure (FRCP): pleading standards, discovery, motions
- State civil procedure rules and local court rules
- Service of process requirements and defects
- Personal jurisdiction and venue requirements
- Default judgment procedures and setting aside defaults
- Answer deadlines (typically 21 days after service)
- Affirmative defenses (FRCP 8(c)): statute of limitations, payment, waiver, estoppel, failure of consideration
- Summary judgment standards (FRCP 56): genuine dispute of material fact

**EVIDENCE & PROOF:**
- Business records exception to hearsay (FRE 803(6))
- Chain of custody for debt documents
- Standing requirements for debt buyers
- Authentication of account statements and contracts
- Burden of proof standards (preponderance of evidence in civil cases)

DOCUMENT TEXT:
{document_text}

CASE INFORMATION FROM OUR CONVERSATION:
{context_info if context_info else 'This is the start of our conversation'}

THEIR QUESTION:
{request.question}

YOUR RESPONSE APPROACH:

1. **START WITH EMPATHY** - Acknowledge what they're going through
   - "I can see this situation is stressful..." or "I understand your concern about..."

2. **ANALYZE WHAT YOU SEE** - Review their document and situation conversationally
   - "Looking at your document, I notice..."
   - Reference specific details: parties, amounts, dates, deadlines
   - Flag critical issues immediately: "This is time-sensitive because..."

3. **EXPLAIN THE LAW CLEARLY** - Apply legal expertise in plain English
   - Use statutes/rules but explain what they mean
   - "Under the FDCPA (15 USC § 1692g), you have certain rights. Here's what that means for you..."
   - Connect legal concepts to their specific situation

4. **GIVE STRATEGIC ADVICE** - Be direct about options and next steps
   - Discuss defenses, strengths, weaknesses
   - Suggest specific actions with timelines
   - Identify what evidence they need

5. **ASK CLARIFYING QUESTIONS** - Be curious and proactive
   - If information is missing: "To give you better guidance, I'd like to know..."
   - If something seems unclear: "Can you tell me more about..."

6. **END CONVERSATIONALLY** - Keep the dialogue flowing
   - "What other questions do you have about this?"
   - "Would you like me to explain any part of this in more detail?"

Write in natural paragraphs (4-6), not bullet points. Be warm but professional. Use legal precision but conversational tone.

YOUR RESPONSE:"""

        elif has_document:
            # No document_id - use improved truncation (50K instead of 3K)
            document_text = request.document_text[:50000]
            logger.info(f"No document_id provided, using improved truncation (50K chars)")

            enhanced_prompt = f"""You are a senior litigation paralegal with 20+ years of experience working at a major law firm. You have worked on over 500 debt collection, bankruptcy, and civil litigation cases. You have deep expertise in:

**BANKRUPTCY LAW:**
- Chapter 7 (liquidation): means test, exemptions, discharge timing
- Chapter 11 (reorganization): plan confirmation, cramdown, absolute priority rule
- Chapter 13 (wage earner): payment plans, confirmation requirements, discharge
- Automatic stay (11 USC § 362): violations, relief from stay, exceptions
- Discharge exceptions (11 USC § 523): fraud, willful injury, student loans, taxes
- Fraudulent transfers (11 USC § 548): actual and constructive fraud
- Preference actions (11 USC § 547): 90-day and insider preference periods
- Exemptions: federal exemptions (11 USC § 522(d)) vs state exemptions, wildcard exemption

**DEBT COLLECTION LAW:**
- Fair Debt Collection Practices Act (FDCPA, 15 USC § 1692): prohibited practices, validation rights, cease communication, damages ($1,000 statutory + actual damages)
- Fair Credit Reporting Act (FCRA, 15 USC § 1681): dispute rights, credit reporting violations, 7-year reporting period
- Telephone Consumer Protection Act (TCPA): robocalls, consent requirements, $500-$1,500 per violation
- State debt collection statutes and licensing requirements
- Statute of limitations by state (typically 3-6 years for written contracts)
- Time-barred debt collection restrictions

**CIVIL PROCEDURE:**
- Federal Rules of Civil Procedure (FRCP): pleading standards, discovery, motions
- State civil procedure rules and local court rules
- Service of process requirements and defects
- Personal jurisdiction and venue requirements
- Default judgment procedures and setting aside defaults
- Answer deadlines (typically 21 days after service)
- Affirmative defenses (FRCP 8(c)): statute of limitations, payment, waiver, estoppel, failure of consideration
- Summary judgment standards (FRCP 56): genuine dispute of material fact

**EVIDENCE & PROOF:**
- Business records exception to hearsay (FRE 803(6))
- Chain of custody for debt documents
- Standing requirements for debt buyers
- Authentication of account statements and contracts
- Burden of proof standards (preponderance of evidence in civil cases)

DOCUMENT TEXT:
{document_text}

CASE INFORMATION FROM OUR CONVERSATION:
{context_info if context_info else 'This is the start of our conversation'}

THEIR QUESTION:
{request.question}

YOUR RESPONSE APPROACH:

1. **START WITH EMPATHY** - Acknowledge what they're going through
   - "I can see this situation is stressful..." or "I understand your concern about..."

2. **ANALYZE WHAT YOU SEE** - Review their document and situation conversationally
   - "Looking at your document, I notice..."
   - Reference specific details: parties, amounts, dates, deadlines
   - Flag critical issues immediately: "This is time-sensitive because..."

3. **EXPLAIN THE LAW CLEARLY** - Apply legal expertise in plain English
   - Use statutes/rules but explain what they mean
   - "Under the FDCPA (15 USC § 1692g), you have certain rights. Here's what that means for you..."
   - Connect legal concepts to their specific situation

4. **GIVE STRATEGIC ADVICE** - Be direct about options and next steps
   - Discuss defenses, strengths, weaknesses
   - Suggest specific actions with timelines
   - Identify what evidence they need

5. **ASK CLARIFYING QUESTIONS** - Be curious and proactive
   - If information is missing: "To give you better guidance, I'd like to know..."
   - If something seems unclear: "Can you tell me more about..."

6. **END CONVERSATIONALLY** - Keep the dialogue flowing
   - "What other questions do you have about this?"
   - "Would you like me to explain any part of this in more detail?"

Write in natural paragraphs (4-6), not bullet points. Be warm but professional. Use legal precision but conversational tone.

YOUR RESPONSE:"""
        else:
            # No document provided - provide general legal guidance with deep expertise
            enhanced_prompt = f"""You are Sarah Chen, a senior litigation paralegal with 20+ years of experience. You're warm, approachable, and excellent at explaining complex legal issues in plain English while maintaining professional expertise.

YOUR CONVERSATIONAL STYLE:
- Speak naturally using "I" and "you" - this is a conversation, not a memo
- Start by acknowledging their concern/situation with empathy
- Use conversational transitions like "Here's what I see...", "Let me explain...", "I notice that..."
- Ask clarifying questions when something's unclear
- Show genuine interest in understanding their full situation
- Remember and reference details from earlier in our conversation

YOUR DEEP LEGAL EXPERTISE:

**BANKRUPTCY LAW:**
- Chapter 7 (liquidation): means test, exemptions, discharge timing
- Chapter 11 (reorganization): plan confirmation, cramdown, absolute priority rule
- Chapter 13 (wage earner): payment plans, confirmation requirements, discharge
- Automatic stay (11 USC § 362): violations, relief from stay, exceptions
- Discharge exceptions (11 USC § 523): fraud, willful injury, student loans, taxes
- Fraudulent transfers (11 USC § 548): actual and constructive fraud
- Preference actions (11 USC § 547): 90-day and insider preference periods
- Exemptions: federal exemptions (11 USC § 522(d)) vs state exemptions, wildcard exemption

**DEBT COLLECTION LAW:**
- Fair Debt Collection Practices Act (FDCPA, 15 USC § 1692): prohibited practices, validation rights, cease communication, damages ($1,000 statutory + actual damages)
- Fair Credit Reporting Act (FCRA, 15 USC § 1681): dispute rights, credit reporting violations, 7-year reporting period
- Telephone Consumer Protection Act (TCPA): robocalls, consent requirements, $500-$1,500 per violation
- State debt collection statutes and licensing requirements
- Statute of limitations by state (typically 3-6 years for written contracts)
- Time-barred debt collection restrictions

**CIVIL PROCEDURE:**
- Federal Rules of Civil Procedure (FRCP): pleading standards, discovery, motions
- State civil procedure rules and local court rules
- Service of process requirements and defects
- Personal jurisdiction and venue requirements
- Default judgment procedures and setting aside defaults
- Answer deadlines (typically 21 days after service)
- Affirmative defenses (FRCP 8(c)): statute of limitations, payment, waiver, estoppel, failure of consideration
- Summary judgment standards (FRCP 56): genuine dispute of material fact

**EVIDENCE & PROOF:**
- Business records exception to hearsay (FRE 803(6))
- Chain of custody for debt documents
- Standing requirements for debt buyers
- Authentication of account statements and contracts
- Burden of proof standards (preponderance of evidence in civil cases)

CASE INFORMATION FROM OUR CONVERSATION:
{context_info if context_info else 'We are just starting our conversation'}

THEIR QUESTION:
{request.question}

YOUR RESPONSE APPROACH:

**You notice they haven't uploaded any documents yet - That's okay!**

1. **START WITH EMPATHY** - Acknowledge their situation warmly
   - "I understand you're dealing with [situation]. Let me help you understand your options..."
   - Show you're genuinely interested in helping

2. **GIVE THEM SOLID GUIDANCE** - Share your expertise conversationally
   - Explain what typically happens in these situations
   - Use legal principles and statutes, but explain what they mean
   - "In cases like this, the law (cite statute) says... Here's what that means for you..."
   - Connect the law to their specific question

3. **GENTLY ASK FOR DOCUMENTS** - Explain why they'd be helpful
   - "To give you even more specific guidance, it would help if you could share..."
   - Explain how each document would let you give better advice
   - Be conversational: "If you have your summons and complaint, I can review the specific deadlines and claims against you"

4. **PROVIDE ACTIONABLE ADVICE** - Tell them what to do next
   - Give specific steps they can take right now
   - Mention typical timelines and what to watch for
   - Discuss common strategies and pitfalls

5. **ASK CLARIFYING QUESTIONS** - Show genuine curiosity
   - "To help you better, I'd like to know..."
   - "Can you tell me more about..."
   - Be specific about what information would help

6. **END WARMLY** - Invite continued conversation
   - "What else would you like to know?"
   - "Feel free to upload any documents you have - I'm here to help"

Write in natural, warm paragraphs (4-6). Be approachable but knowledgeable. Use legal precision with a human touch.

YOUR RESPONSE:"""

        # Get ultra-fast AI response
        start_time = datetime.now()

        # ALWAYS use comprehensive paralegal-level AI analysis
        if has_document:
            # We have a real document - use comprehensive paralegal analysis
            logger.info(f"Using comprehensive paralegal AI with document context (text length: {len(request.document_text)})")
            ai_response = await _call_claude_paralegal_comprehensive(enhanced_prompt)
        else:
            # No document - use comprehensive paralegal analysis for general legal guidance
            logger.info("No document provided - using comprehensive paralegal AI for general legal guidance")
            ai_response = await _call_claude_paralegal_comprehensive(enhanced_prompt)

        response_time = (datetime.now() - start_time).total_seconds()

        # DISABLED: Follow-up questions removed per user request
        follow_up_question = None
        suggested_questions = []

        # Generate additional suggested questions based on document and conversation
        suggested_questions = await _generate_contextual_suggestions(
            request.document_text or "",
            request.document_analysis or {},
            conversation,
            request.question
        )

        # ============================================================================
        # HALLUCINATION DETECTION - Validate AI response against actual documents
        # ============================================================================
        # Check if AI's response contains unverified information or cross-document confusion
        validation_warnings = []
        hallucination_risk = "low"

        if document_id and session_id:
            try:
                context_manager = get_context_manager(db)

                # Validate AI's response for hallucinations
                validation = context_manager.validate_cross_references(
                    session_id=session_id,
                    ai_response=ai_response
                )

                if not validation["is_valid"]:
                    validation_warnings = validation["warnings"]
                    hallucination_risk = validation.get("hallucination_risk", "medium")

                    logger.warning(
                        f"Hallucination detected in session {session_id}: "
                        f"{len(validation_warnings)} warnings, risk={hallucination_risk}"
                    )

            except Exception as val_error:
                logger.error(f"Validation error (non-fatal): {val_error}")
                # Continue even if validation fails

        structured_response = {
            "answer": ai_response,
            "confidence": 0.9 if hallucination_risk == "low" else (0.7 if hallucination_risk == "medium" else 0.5),
            "sources": [],
            "follow_up_question": follow_up_question,  # Intelligent follow-up
            "suggested_questions": suggested_questions,  # Persistent suggestions
            "quick_actions": [
                "What should I do next?",
                "What are my options?",
                "What evidence do I need?"
            ]
        }

        # Add hallucination warnings if detected
        if validation_warnings:
            structured_response["validation_warnings"] = validation_warnings
            structured_response["hallucination_risk"] = hallucination_risk
            structured_response["note"] = "⚠️ Some information in this response may need verification"

        # Add to conversation history
        conversation.append({
            "question": request.question,
            "answer": structured_response["answer"],
            "timestamp": datetime.now().isoformat(),
            "confidence": structured_response.get("confidence", 0.8),
            "follow_up": follow_up_question
        })

        # AGENT MODE - Conversational with intelligent follow-ups
        response = {
            "session_id": session_id,
            "answer": structured_response["answer"],
            "follow_up_question": follow_up_question,
            "suggested_questions": structured_response.get("suggested_questions", []),
            "confidence": structured_response.get("confidence", 0.8),
            "sources": structured_response.get("sources", []),
            "conversation_length": len(conversation),
            "timestamp": datetime.now().isoformat(),
            "response_type": "agent_qa",
            "performance": {
                "response_time": round(response_time, 2)
            }
        }

        # DEBUG: Log what we're about to send
        print(f"\n{'='*80}")
        print(f"[RESPONSE] About to send answer length: {len(response['answer'])} chars")
        print(f"[RESPONSE] Answer preview: {response['answer'][:200]}...")
        print(f"[RESPONSE] Answer end: ...{response['answer'][-200:]}")
        print(f"{'='*80}\n")

        logger.info(f"Q&A response generated for session {session_id}")

        # Save to database for persistence
        if document_id:
            try:
                # Get or create QASession
                qa_session = db.query(QASession).filter(
                    QASession.document_id == document_id,
                    QASession.session_id == session_id
                ).first()

                if not qa_session:
                    # Create new QA session
                    qa_session = QASession(
                        id=str(uuid_lib.uuid4()),
                        document_id=document_id,
                        session_id=session_id,
                        started_at=datetime.utcnow(),
                        is_active=True,
                        question_count=0
                    )
                    db.add(qa_session)
                    db.flush()  # Get the qa_session.id for messages

                # Save user question
                user_message = QAMessage(
                    id=str(uuid_lib.uuid4()),
                    session_id=qa_session.id,
                    role='user',
                    content=request.question,
                    timestamp=datetime.utcnow()
                )
                db.add(user_message)

                # Save AI response
                ai_message = QAMessage(
                    id=str(uuid_lib.uuid4()),
                    session_id=qa_session.id,
                    role='ai',
                    content=structured_response["answer"],
                    timestamp=datetime.utcnow(),
                    follow_up_question=follow_up_question,
                    confidence={"score": structured_response.get("confidence", 0.8)}
                )
                db.add(ai_message)

                # Update session metadata
                qa_session.question_count += 1
                qa_session.last_activity = datetime.utcnow()

                db.commit()
                logger.info(f"Saved Q&A exchange to database for session {session_id}")
            except Exception as db_error:
                logger.error(f"Database save error in Q&A: {str(db_error)}")
                db.rollback()
                # Continue even if DB save fails

        # DISABLED: Force corrections middleware was truncating responses to 50 words
        # This breaks Q&A which needs comprehensive answers
        # response = apply_forced_corrections(response)

        return response

    except Exception as e:
        logger.error(f"Error in Q&A system: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Q&A system error: {str(e)}"
        )

@router.post("/follow-up")
async def ask_follow_up(request: FollowUpRequest) -> Dict[str, Any]:
    """
    Ask a follow-up question in an existing conversation
    """
    try:
        if request.session_id not in conversation_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation session not found"
            )

        session_data = conversation_store[request.session_id]

        # Create follow-up request
        qa_request = QuestionRequest(
            document_text=session_data["document_text"],
            document_analysis=session_data["document_analysis"],
            question=request.question,
            session_id=request.session_id
        )

        return await ask_question(qa_request)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in follow-up question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Follow-up question error: {str(e)}"
        )

@router.get("/conversation/{session_id}")
async def get_conversation(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get conversation history for a session from database
    SECURITY: Only returns conversations owned by the authenticated user.
    """
    try:
        # SECURITY: Get all QA sessions for this session_id - filter by user_id
        qa_sessions = db.query(QASession).filter(
            QASession.session_id == session_id,
            QASession.user_id == current_user.user_id,  # Only user's own sessions
            QASession.is_active == True
        ).all()

        if not qa_sessions:
            # Check in-memory store for backward compatibility
            if session_id not in conversation_store:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation session not found"
                )

            session_data = conversation_store[session_id]
            return {
                "session_id": session_id,
                "conversation": session_data["conversation"],
                "document_type": session_data["document_analysis"].get("document_type"),
                "created_at": session_data["created_at"],
                "total_questions": len(session_data["conversation"])
            }

        # Build conversation from database messages
        all_messages = []
        for qa_session in qa_sessions:
            # Get all messages for this QA session
            messages = db.query(QAMessage).filter(
                QAMessage.session_id == qa_session.id
            ).order_by(QAMessage.timestamp).all()

            for msg in messages:
                all_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "follow_up_question": msg.follow_up_question,
                    "confidence": msg.confidence
                })

        # Group messages into Q&A pairs
        conversation = []
        i = 0
        while i < len(all_messages):
            if all_messages[i]["role"] == "user":
                qa_pair = {
                    "question": all_messages[i]["content"],
                    "timestamp": all_messages[i]["timestamp"]
                }

                # Look for AI response
                if i + 1 < len(all_messages) and all_messages[i + 1]["role"] == "ai":
                    qa_pair["answer"] = all_messages[i + 1]["content"]
                    qa_pair["confidence"] = all_messages[i + 1].get("confidence", {}).get("score", 0.8)
                    qa_pair["follow_up"] = all_messages[i + 1].get("follow_up_question")
                    i += 2
                else:
                    i += 1

                conversation.append(qa_pair)
            else:
                i += 1

        return {
            "session_id": session_id,
            "conversation": conversation,
            "total_questions": len(conversation),
            "created_at": qa_sessions[0].started_at.isoformat() if qa_sessions else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )

@router.delete("/conversation/{session_id}")
async def clear_conversation(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Clear conversation history for a session
    """
    if session_id in conversation_store:
        del conversation_store[session_id]

    return {
        "message": "Conversation cleared",
        "session_id": session_id
    }

@router.post("/stream")
async def stream_question(request: StreamQuestionRequest):
    """
    Stream AI response for better perceived speed
    Returns Server-Sent Events (SSE) stream
    """
    try:
        async def generate_stream():
            try:
                # Send initial response immediately
                yield f"data: {{\"type\": \"start\", \"message\": \"Processing your question...\"}}}}\n\n"

                # Use optimized client for streaming
                async for chunk in optimized_ai_client.stream_response(
                    query=request.question,
                    query_type='qa'
                ):
                    # Send each chunk as it arrives
                    chunk_data = {
                        "type": "chunk",
                        "content": chunk
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"

                # Send completion signal
                yield f"data: {{\"type\": \"complete\", \"message\": \"Response complete\"}}}}\n\n"

            except Exception as e:
                error_data = {
                    "type": "error",
                    "message": f"Streaming error: {str(e)}"
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )

    except Exception as e:
        logger.error(f"Error in streaming endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming error: {str(e)}"
        )

@router.post("/quick")
async def quick_question(request: StreamQuestionRequest) -> Dict[str, Any]:
    """
    Ultra-fast Q&A endpoint using cached responses and speed optimization
    Bypasses conversation history for maximum speed
    """
    try:
        start_time = datetime.now()

        # Use optimized client directly for maximum speed
        response = await optimized_ai_client.process_query(
            query=request.question,
            query_type='qa'
        )

        response_time = (datetime.now() - start_time).total_seconds()

        # Ensure all required fields
        response.setdefault('answer', 'Please provide more details.')
        response.setdefault('defense_options', [
            "Challenge the evidence",
            "Question the procedures",
            "Negotiate a settlement"
        ])
        response.setdefault('follow_up_questions', [
            "What specific evidence do they have?",
            "What is the deadline to respond?"
        ])
        response.setdefault('quick_actions', [
            "What defenses do I have?",
            "What should I do immediately?",
            "What evidence do I need?",
            "How strong is my case?",
            "What are the risks?"
        ])

        # Add session and timing info
        response['session_id'] = request.session_id or f"quick_{datetime.now().timestamp()}"
        response['timestamp'] = datetime.now().isoformat()
        response['response_type'] = "ultra_quick_qa"
        response['performance'] = response.get('performance', {})
        response['performance']['total_response_time'] = round(response_time, 2)

        logger.info(f"Quick Q&A response in {response_time:.2f}s")
        return response

    except Exception as e:
        logger.error(f"Error in quick Q&A: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick Q&A error: {str(e)}"
        )

def _create_qa_prompt(document_text: str, analysis: Dict[str, Any], question: str, conversation: List[Dict]) -> str:
    """Create ultra-optimized prompt for maximum speed and conciseness"""

    # Minimal conversation context for speed
    conversation_context = ""
    if conversation:
        last_qa = conversation[-1]  # Only include last Q&A for speed
        conversation_context = f"\nPrevious: Q: {last_qa['question'][:50]}... A: {last_qa['answer'][:50]}..."

    # Drastically reduced prompt for speed
    return f"""
Be concise. Answer in 2 sentences max. Use simple English.

DOCUMENT: {analysis.get('document_type', 'Legal doc')}
SUMMARY: {analysis.get('summary', 'Document review')[:100]}
TEXT: {document_text[:1500]}...{conversation_context}

QUESTION: {question}

Format:
Answer: [2 sentences max]

Defense options:
• [Defense 1]
• [Defense 2]
• [Defense 3]

Questions for you:
1. [Question 1]
2. [Question 2]
"""

def _parse_qa_response(ai_response: str, question: str) -> Dict[str, Any]:
    """Parse AI response into structured format - handles both JSON and text responses"""
    try:
        import json

        # Try to extract JSON from the response
        if "```json" in ai_response:
            json_start = ai_response.find("```json") + 7
            json_end = ai_response.find("```", json_start)
            json_str = ai_response[json_start:json_end].strip()
            parsed = json.loads(json_str)

            # Validate required fields
            if "answer" not in parsed:
                parsed["answer"] = ai_response
            return parsed
        else:
            # For non-JSON responses, return the full text as the answer
            # Don't try to parse it into sections - that breaks multi-line answers
            return {
                "answer": ai_response,  # Return full response, don't parse
                "confidence": 0.8,
                "sources": [],
                "follow_up_questions": [],
                "defense_options": [],
                "quick_actions": [
                    "What defenses do I have?",
                    "What should I do immediately?",
                    "What evidence do I need?"
                ]
            }

    except (json.JSONDecodeError, Exception):
        # Fallback to plain text response
        return {
            "answer": ai_response,
            "confidence": 0.7,
            "sources": [],
            "follow_up_questions": [],
            "defense_options": [],
            "quick_actions": [
                "What defenses do I have?",
                "What should I do immediately?",
                "What evidence do I need?"
            ]
        }

def _generate_suggested_questions(analysis: Dict[str, Any], conversation: List[Dict]) -> List[str]:
    """Generate suggested questions optimized for speed"""

    doc_type = analysis.get('document_type', '').lower()
    asked_questions = {qa['question'].lower() for qa in conversation[-3:]}  # Only check last 3 for speed

    # Reduced base questions for speed
    suggestions = [
        "What are my defense options?",
        "What should I do immediately?",
        "What are the key deadlines?",
        "What evidence do I need?",
        "How strong is my case?"
    ]

    # Document type-specific questions
    if 'motion' in doc_type:
        suggestions.extend([
            "What is being requested in this motion?",
            "What is the deadline to respond?",
            "What evidence supports this motion?",
            "What are possible defenses to this motion?"
        ])
    elif 'complaint' in doc_type or 'petition' in doc_type:
        suggestions.extend([
            "What claims are being made against me?",
            "What damages are being sought?",
            "What is the statute of limitations?",
            "What defenses might be available?"
        ])
    elif 'order' in doc_type:
        suggestions.extend([
            "What does this order require me to do?",
            "By when must I comply?",
            "What happens if I don't comply?",
            "Can this order be appealed?"
        ])
    elif 'contract' in doc_type or 'agreement' in doc_type:
        suggestions.extend([
            "What are my obligations under this agreement?",
            "What are the termination conditions?",
            "What are the penalties for breach?",
            "How can this agreement be modified?"
        ])

    # Filter out already asked questions and limit to 5
    filtered_suggestions = [
        q for q in suggestions
        if q.lower() not in asked_questions
    ][:5]

    return filtered_suggestions


async def _generate_contextual_suggestions(
    document_text: Optional[str],
    document_analysis: Optional[Dict[str, Any]],
    conversation: List[Dict],
    current_question: str
) -> List[str]:
    """
    Generate contextual suggested questions based on document and conversation history
    Uses AI to create relevant, non-redundant questions
    """
    try:
        # Get all previously asked questions for deduplication
        asked_questions = [qa['question'].lower().strip() for qa in conversation]

        # Extract key document facts
        doc_analysis = document_analysis or {}
        doc_type = doc_analysis.get('document_type', 'document')
        parties = doc_analysis.get('parties', [])
        deadlines = doc_analysis.get('deadlines', [])
        summary = doc_analysis.get('summary', '')
        doc_text_excerpt = (document_text or "")[:1000]

        # Build context for AI
        doc_context = f"""Document Type: {doc_type}
Summary: {summary[:500]}
Parties: {', '.join(parties[:3]) if parties else 'Not specified'}
Deadlines: {', '.join([str(d) for d in deadlines[:2]]) if deadlines else 'None identified'}
Document Text (excerpt): {doc_text_excerpt}

Recent Conversation:
{chr(10).join([f"Q: {qa['question']}" for qa in conversation[-3:]])}

Current Question: {current_question}"""

        prompt = f"""Based on this legal document and conversation, suggest 5 relevant follow-up questions that:
1. Are specific to THIS document's content (mention parties, dates, amounts, specific claims)
2. Have NOT been asked yet
3. Would help the user understand their situation better
4. Are actionable and practical
5. Progress the conversation forward

{doc_context}

Previously asked questions to AVOID:
{chr(10).join([f"- {q}" for q in asked_questions[-5:]])}

Return ONLY a JSON array of 5 question strings, no other text:
["Question 1", "Question 2", "Question 3", "Question 4", "Question 5"]"""

        # Call Claude for contextual questions
        response = claude_client.messages.create(
            model='claude-3-5-haiku-20241022',
            max_tokens=300,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        response_text = response.content[0].text.strip()

        # Parse JSON response
        import json
        import re

        # Extract JSON array if wrapped in markdown
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        else:
            # Try to find JSON array in response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            json_str = json_match.group(0) if json_match else response_text

        try:
            suggestions = json.loads(json_str)
        except json.JSONDecodeError as json_err:
            logger.warning(f"JSON parsing failed: {json_err}. Response was: {response_text[:200]}")
            # Try to extract questions from plain text response
            suggestions = []
            for line in response_text.split('\n'):
                line = line.strip()
                if line and line.endswith('?'):
                    # Remove bullets, numbers, etc.
                    clean_line = re.sub(r'^[\d\-\*\.\)]+\s*', '', line)
                    if clean_line:
                        suggestions.append(clean_line)

        # Ensure it's a list
        if not isinstance(suggestions, list):
            suggestions = []

        # Dedup filter: Remove any that are too similar to asked questions
        filtered_suggestions = []
        for suggestion in suggestions:
            if not isinstance(suggestion, str):
                continue
            suggestion_lower = suggestion.lower().strip()
            # Check if not already asked (fuzzy match)
            is_duplicate = any(
                _is_similar_question(suggestion_lower, asked.lower())
                for asked in asked_questions
            )
            if not is_duplicate and len(filtered_suggestions) < 5:
                filtered_suggestions.append(suggestion)

        return filtered_suggestions

    except Exception as e:
        logger.error(f"Error generating contextual suggestions: {str(e)}")
        # Fallback to static suggestions with deduplication
        return _generate_suggested_questions(document_analysis, conversation)


def _is_similar_question(q1: str, q2: str) -> bool:
    """Check if two questions are similar (for deduplication)"""
    # Remove common words and punctuation for comparison
    import re

    def normalize(q):
        q = re.sub(r'[^\w\s]', '', q.lower())
        common_words = {'what', 'when', 'where', 'who', 'how', 'why', 'is', 'are', 'the', 'a', 'an', 'my', 'your', 'do', 'does', 'can', 'should', 'would'}
        words = [w for w in q.split() if w not in common_words]
        return set(words)

    words1 = normalize(q1)
    words2 = normalize(q2)

    # If 70% of meaningful words overlap, consider it similar
    if not words1 or not words2:
        return q1 == q2

    overlap = len(words1 & words2)
    similarity = overlap / max(len(words1), len(words2))

    return similarity > 0.7

@router.post("/strategic-questions")
async def generate_strategic_questions(request: StrategicQuestionsRequest) -> Dict[str, Any]:
    """
    Generate strategic questions based on document analysis gaps

    Uses Harvard-level legal analysis to identify missing information
    that could strengthen the case or reveal defenses
    """
    try:
        # Generate strategic questions using dual-AI system
        strategic_questions = await dual_ai_service.generate_strategic_questions(
            request.document_analysis
        )

        # Organize questions by category
        categorized_questions = {}
        for question in strategic_questions:
            category = question.get('category', 'general')
            if category not in categorized_questions:
                categorized_questions[category] = []
            categorized_questions[category].append(question)

        response = {
            "strategic_questions": strategic_questions,
            "categorized_questions": categorized_questions,
            "total_questions": len(strategic_questions),
            "categories": list(categorized_questions.keys()),
            "analysis_type": "harvard_lawyer_strategic_analysis",
            "document_type": (request.document_analysis or {}).get('document_type', 'Unknown'),
            "disclaimers": [
                "These questions are generated to help identify strategic opportunities",
                "Not all questions may apply to your specific situation",
                "Consult with a qualified attorney for legal advice",
                "This analysis is for educational purposes only"
            ]
        }

        logger.info(f"Generated {len(strategic_questions)} strategic questions for {(request.document_analysis or {}).get('document_type', 'unknown')} document")
        return response

    except Exception as e:
        logger.error(f"Error generating strategic questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategic question generation failed: {str(e)}"
        )

# Defense Builder Storage
defense_sessions = {}

def _get_or_create_defense_context(session_id: str, db: Session) -> tuple[ChatContext, Any]:
    """
    Get ChatContext from memory or reconstruct from database.
    Returns (context, defense_record) tuple.
    """
    from ..models.legal_documents import DefenseSession

    # Try memory first (fast path)
    if session_id in defense_sessions:
        session_data = defense_sessions[session_id]
        defense_record = db.query(DefenseSession).filter(DefenseSession.session_id == session_id).first()
        return session_data["context"], defense_record

    # Reconstruct from database (slow path after server restart)
    defense_record = db.query(DefenseSession).filter(DefenseSession.session_id == session_id).first()
    if not defense_record:
        return None, None

    # Reconstruct ChatContext from database state
    context = ChatContext()
    context.is_new_case = (defense_record.phase == 'intro')
    context.in_interview_mode = defense_record.is_interview_active
    context.case_type = defense_record.case_type
    context.answers = defense_record.collected_answers or {}
    context.current_question_key = defense_record.current_question_key

    # Rebuild in-memory cache
    defense_sessions[session_id] = {
        "context": context,
        "created_at": defense_record.started_at.isoformat(),
        "last_activity": defense_record.last_activity.isoformat(),
        "message_count": defense_record.message_count
    }

    logger.info(f"Reconstructed ChatContext from database for session {session_id}")
    return context, defense_record

@router.post("/defense-builder/start")
async def start_defense_builder(
    request: DefenseBuilderRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Start a proactive defense building session

    This endpoint begins an interactive interview process that asks smart questions
    to identify viable defense strategies and build a customized defense plan.
    """
    try:
        session_id = request.session_id or f"defense_{datetime.now().timestamp()}"

        # Initialize defense builder context
        context = ChatContext()

        # Start the defense interview
        response = context.defense_builder.start_defense_interview(request.message)

        # Create database record for persistence
        from ..models.legal_documents import DefenseSession
        defense_record = DefenseSession(
            id=str(uuid_lib.uuid4()),
            document_id=None,  # No document required for defense builder
            session_id=session_id,
            started_at=datetime.utcnow(),
            phase='intro',
            collected_answers=context.answers,
            is_interview_active=context.in_interview_mode,
            current_question_key=context.current_question_key,
            case_type=context.case_type,
            message_count=1
        )
        db.add(defense_record)
        db.commit()
        db.refresh(defense_record)

        # Also store in memory for performance (can be rebuilt from DB if lost)
        defense_sessions[session_id] = {
            "context": context,
            "created_at": defense_record.started_at.isoformat(),
            "last_activity": defense_record.started_at.isoformat(),
            "message_count": 1
        }

        logger.info(f"Defense builder session started: {session_id} (saved to database)")

        return {
            "session_id": session_id,
            "response": response,
            "interview_active": True,
            "created_at": defense_record.started_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Error starting defense builder: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Defense builder initialization failed: {str(e)}"
        )

@router.post("/defense-builder/chat")
async def defense_builder_chat(
    request: DefenseBuilderChat,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Continue defense building conversation

    Processes user answers and either asks the next strategic question
    or generates the final defense strategy if the interview is complete.
    """
    try:
        # Get or reconstruct ChatContext from database
        context, defense_record = _get_or_create_defense_context(request.session_id, db)

        if not context or not defense_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Defense builder session not found. Please start a new session."
            )

        # Process the message using defense builder
        if context.in_interview_mode:
            # Process interview answer
            response = context.defense_builder.process_interview_answer(
                request.message,
                {
                    'case_type': context.case_type,
                    'answers': context.answers,
                    'current_question_key': context.current_question_key
                }
            )

            # Update context from response
            if 'case_type' in response:
                context.case_type = response['case_type']
            if 'current_question_key' in response:
                context.current_question_key = response['current_question_key']
            if 'answers' in response:
                context.answers = response['answers']
            if 'interview_mode' in response:
                context.in_interview_mode = response['interview_mode']

        else:
            # Regular Q&A mode after interview completion
            response = {
                'message': f"Based on our analysis of your {context.case_type or 'legal'} matter, I can answer specific questions about the defense strategies we identified.",
                'interview_mode': False
            }

        # Update session metadata in memory
        session_data = defense_sessions.get(request.session_id, {})
        session_data["last_activity"] = datetime.now().isoformat()
        session_data["message_count"] = session_data.get("message_count", 0) + 1

        # Save updated state to database
        defense_record.collected_answers = context.answers
        defense_record.is_interview_active = context.in_interview_mode
        defense_record.current_question_key = context.current_question_key
        defense_record.case_type = context.case_type
        defense_record.message_count = session_data["message_count"]
        defense_record.last_activity = datetime.utcnow()

        # Update phase based on interview state
        if not context.in_interview_mode and defense_record.phase != 'complete':
            defense_record.phase = 'analysis'

        db.commit()
        db.refresh(defense_record)

        logger.info(f"Defense builder chat processed for session {request.session_id} (saved to database)")

        return {
            "session_id": request.session_id,
            "response": response,
            "interview_active": response.get('interview_mode', False),
            "message_count": session_data["message_count"],
            "last_activity": session_data["last_activity"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in defense builder chat: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Defense builder chat error: {str(e)}"
        )

@router.get("/defense-builder/session/{session_id}")
async def get_defense_session(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get defense builder session information and progress
    """
    # Get or reconstruct ChatContext from database
    context, defense_record = _get_or_create_defense_context(session_id, db)

    if not context or not defense_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Defense builder session not found"
        )

    return {
        "session_id": session_id,
        "case_type": context.case_type,
        "interview_active": context.in_interview_mode,
        "questions_answered": len(context.answers),
        "answers_collected": context.answers,
        "created_at": defense_record.started_at.isoformat(),
        "last_activity": defense_record.last_activity.isoformat(),
        "message_count": defense_record.message_count,
        "phase": defense_record.phase
    }

@router.delete("/defense-builder/session/{session_id}")
async def clear_defense_session(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clear defense builder session
    """
    try:
        # Delete from database
        from ..models.legal_documents import DefenseSession
        defense_record = db.query(DefenseSession).filter(DefenseSession.session_id == session_id).first()

        if defense_record:
            db.delete(defense_record)
            db.commit()
            logger.info(f"Deleted defense session {session_id} from database")

        # Also delete from memory cache if present
        if session_id in defense_sessions:
            del defense_sessions[session_id]

        return {
            "message": "Defense builder session cleared",
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Error clearing defense session: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session: {str(e)}"
        )

@router.get("/defense-builder/status")
async def get_defense_builder_status() -> Dict[str, Any]:
    """
    Get defense builder system status and capabilities
    """
    return {
        "status": "operational",
        "capabilities": [
            "Proactive defense strategy building",
            "Adaptive questioning system",
            "Case type identification",
            "Evidence gap analysis",
            "Strategic planning assistance"
        ],
        "supported_case_types": [
            "bankruptcy",
            "criminal",
            "litigation",
            "employment"
        ],
        "active_sessions": len(defense_sessions),
        "features": {
            "smart_questioning": True,
            "defense_analysis": True,
            "evidence_identification": True,
            "strategic_planning": True,
            "attorney_preparation": True
        }
    }


@router.get("/interview/progress/{session_id}")
async def get_interview_progress(session_id: str) -> Dict[str, Any]:
    """
    Get case interview progress for a session
    Shows how many questions answered and what's remaining
    """
    if session_id not in conversation_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session_data = conversation_store[session_id]
    conversation = session_data["conversation"]

    # Detect case type from conversation
    all_questions = " ".join([qa['question'] for qa in conversation])
    case_type = case_interviewer.detect_case_type(all_questions)

    # Get answered questions
    answered_questions = [qa['question'] for qa in conversation]

    # Calculate progress
    completion = case_interviewer.calculate_completion(case_type, answered_questions)

    # Get all questions for this case type
    all_case_questions = case_interviewer.get_all_questions(case_type)

    # Get next question
    interview_context = {'answeredQuestions': answered_questions}
    next_question = case_interviewer.get_next_question(case_type, interview_context)

    return {
        "session_id": session_id,
        "case_type": case_type,
        "completion_percentage": round(completion, 1),
        "questions_answered": len(answered_questions),
        "total_questions": len(all_case_questions),
        "next_question": next_question,
        "remaining_questions": [q for q in all_case_questions if q not in answered_questions][:5],
        "interview_complete": next_question is None
    }


@router.get("/interview/questions/{case_type}")
async def get_case_questions(case_type: str) -> Dict[str, Any]:
    """
    Get all questions for a specific case type
    """
    valid_types = ['debt_collection', 'eviction', 'bankruptcy', 'foreclosure', 'general_lawsuit']

    if case_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid case type. Must be one of: {', '.join(valid_types)}"
        )

    questions = case_interviewer.get_all_questions(case_type)

    return {
        "case_type": case_type,
        "total_questions": len(questions),
        "questions": questions
    }


@router.get("/flows")
async def get_available_flows() -> Dict[str, Any]:
    """
    Get all available question flows
    """
    return {
        "flows": list(QUESTION_FLOWS.keys()),
        "flow_details": {
            flow_name: {
                "question_count": len(questions),
                "questions": questions
            }
            for flow_name, questions in QUESTION_FLOWS.items()
        }
    }


@router.post("/flows/start")
async def start_question_flow(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Start a predefined question flow
    """
    try:
        flow_type = request.get('flow_type')

        if not flow_type:
            # Auto-recommend flow based on description
            description = request.get('case_description', '')
            flow_type = adaptive_questioner.recommend_flow(description)

        first_question = adaptive_questioner.start_flow(flow_type)

        if not first_question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid flow type. Available: {', '.join(QUESTION_FLOWS.keys())}"
            )

        return {
            "flow_type": flow_type,
            "first_question": first_question,
            "total_questions": len(QUESTION_FLOWS[flow_type]),
            "message": f"Starting {flow_type.replace('_', ' ').title()} flow"
        }

    except Exception as e:
        logger.error(f"Error starting flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start flow: {str(e)}"
        )


@router.post("/flows/answer")
async def process_flow_answer(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process answer in current flow and get next question
    """
    try:
        question = request.get('question')
        answer = request.get('answer')

        if not question or not answer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both 'question' and 'answer' are required"
            )

        result = adaptive_questioner.process_answer(question, answer)

        return {
            "next_question": result['next_question'],
            "insights": result['insights'],
            "completion_percentage": result['completion_percentage'],
            "flow_complete": result['flow_complete'],
            "summary": adaptive_questioner.get_flow_summary() if result['flow_complete'] else None
        }

    except Exception as e:
        logger.error(f"Error processing answer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process answer: {str(e)}"
        )


@router.get("/flows/recommend")
async def recommend_flow(case_description: str) -> Dict[str, Any]:
    """
    Recommend a question flow based on case description
    """
    recommended_flow = adaptive_questioner.recommend_flow(case_description)

    return {
        "recommended_flow": recommended_flow,
        "flow_name": recommended_flow.replace('_', ' ').title(),
        "question_count": len(QUESTION_FLOWS[recommended_flow]),
        "first_question": QUESTION_FLOWS[recommended_flow][0],
        "description": f"This flow is designed for {recommended_flow.replace('_', ' ')} cases"
    }


# CLAUDE HAIKU ULTRA-FAST IMPLEMENTATION
claude_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def _strip_metaphors_and_verbosity(text: str) -> str:
    """
    AGGRESSIVE POST-PROCESSING: Remove all metaphors, verbose patterns, and condescending language
    """
    import re

    # Remove "3rd grader" explanatory language - EXPANDED
    explanatory_patterns = [
        r"[Ll]et'?s pretend[^.]*\.",
        r"borrowed a toy[^.]*\.",
        r"[Oo]kay,?\s*let'?s[^.]*\.",
        r"[Ll]et me (explain|help you understand|break (this|that) down)[^.!?]*[.!?]",
        r"[Tt]o (help you understand|make (this|it) (simple|clear|easier))[^.!?]*[.!?]",
        r"[Ii]n (simple|easy|basic) (terms|words|language)[^.!?]*[.!?]",
        r"[Tt]hink of it (as|like|this way)[^.!?]*[.!?]",
        r"[Ww]hat (this|that) (means|is saying) is[^.!?]*[.!?]",
        r"[Tt]o put it (simply|another way|in simple terms)[^.!?]*[.!?]",
        r"[Hh]ere'?s what (this|that) means[^.!?]*[.!?]",
        r"[Ss]imple [Ww]ords [Ee]xplanation:?",
        r"[Ee]veryday [Ee]xamples:?",
        r"[Bb]asically[,\s]+",
        r"[Ee]ssentially[,\s]+"
    ]

    for pattern in explanatory_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Metaphor patterns to remove - EXPANDED
    metaphor_patterns = [
        r"[Ii]magine you[^.]*\.",
        r"picture this[^.]*\.",
        r"it'?s like when[^.]*\.",
        r"think of it like[^.]*\.",
        r"[Ll]ike (a|an|having|being) [^.,!?]+[.,!?]",
        r"[Ss]imilar to [^.,!?]+[.,!?]",
        r"[Ii]magine [^.,!?]+[.,!?]",
        r"[Pp]icture [^.,!?]+[.,!?]",
        r"[Jj]ust as [^.,!?]+[.,!?]",
        r"[Mm]uch like [^.,!?]+[.,!?]",
        r"[Ii]n the (grand scheme|same way)[^.,!?]*[.,!?]"
    ]

    for pattern in metaphor_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Verbose/condescending phrases to remove
    verbose_phrases = [
        "Let me explain", "Let me help you understand", "Let me break this down",
        "I understand", "I see", "To clarify", "To put it simply",
        "In other words", "Simply put", "Think of it this way",
        "The way I see it", "From my perspective", "If you will",
        "So to speak", "In a sense", "In a manner of speaking",
        "What this means is", "What I'm saying is", "To make it clear",
        "To help you out", "Here's the thing", "You see",
        "The important thing to know is", "You need to understand that"
    ]

    for phrase in verbose_phrases:
        text = text.replace(phrase, "").replace(phrase.lower(), "")

    # Clean up extra spaces, line breaks, and orphaned punctuation
    text = re.sub(r'\s*[,;]\s*[.,;]', '.', text)  # Remove double punctuation
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^\s*[,;.]\s*', '', text)  # Remove leading punctuation

    # NOTE: Removed 50-word limit - users need complete comprehensive answers
    # Don't truncate responses from comprehensive AI calls

    return text.strip()


def _generate_document_insight(doc_analysis: Dict[str, Any]) -> str:
    """
    Generate concise document insight summary
    """
    insights = []

    # Start with what we found
    case_type = doc_analysis.get('case_type', 'document')
    insights.append(f"I've analyzed your {case_type}.")

    # Key findings
    plaintiff = doc_analysis.get('plaintiff')
    amount = doc_analysis.get('amount_claimed')
    if plaintiff:
        insights.append(f"{plaintiff} is suing for {amount if amount else 'an unspecified amount'}.")

    # Critical missing info
    missing = doc_analysis.get('missing_information', [])
    if missing and len(missing) > 0:
        first_missing = missing[0] if isinstance(missing, list) else str(missing)
        insights.append(f"Important: The document is missing {first_missing} which could help your defense.")

    # Immediate concern - deadlines
    deadlines = doc_analysis.get('deadlines', [])
    if deadlines and len(deadlines) > 0:
        urgent = deadlines[0] if isinstance(deadlines, list) else str(deadlines)
        insights.append(f"⚠️ Critical deadline: {urgent}")

    # Potential defenses spotted
    defenses = doc_analysis.get('potential_defenses', [])
    if defenses and len(defenses) > 0:
        defense_list = ', '.join(defenses[:2]) if isinstance(defenses, list) else str(defenses)
        insights.append(f"I see potential for: {defense_list}.")

    return ' '.join(insights)


async def _generate_defense_strategy(case_type: str, collected_info: Dict[str, str]) -> str:
    """
    Generate defense strategy based on collected case information - DIRECT, NO FLUFF
    """
    try:
        info_text = "\n".join([f"- {q}: {a}" for q, a in collected_info.items()])

        prompt = f"""List 3 defenses. Be direct. Max 10 words per defense.

{case_type}: {info_text}

1.
2.
3."""

        response = claude_client.messages.create(
            model='claude-3-5-haiku-20241022',  # HAIKU for speed
            max_tokens=150,  # Reduced from 400
            temperature=0,
            stop_sequences=['However,', 'Additionally,', 'Consult'],
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return aggressive_strip_verbosity(response.content[0].text.strip())

    except Exception as e:
        logger.error(f"Defense strategy generation error: {e}")
        return "1. Statute of limitations 2. Lack of evidence 3. Procedural errors"


async def _call_claude_paralegal_comprehensive(prompt: str) -> str:
    """
    Comprehensive paralegal-level analysis using OpenAI GPT-4o (switched from Claude for reliability).
    Used for detailed legal Q&A that requires deep expertise.
    """
    try:
        import openai
        import os

        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("No OpenAI API key found")
            return "AI service unavailable. Please configure API keys."

        client = openai.OpenAI(api_key=api_key)

        # Use GPT-4o for comprehensive analysis - faster and more reliable than Claude
        response = client.chat.completions.create(
            model="gpt-4o",  # GPT-4o for detailed legal analysis - fast and reliable
            max_tokens=3000,  # Allow comprehensive, detailed responses
            temperature=0.1,  # Low temperature for consistent legal analysis
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content if response.choices else ""

        # DEBUG: Log the actual response
        print(f"\n{'='*80}")
        print(f"[OPENAI] Response Length: {len(answer)} chars, {len(answer.split())} words")
        print(f"[OPENAI] Response Preview: {answer[:300]}...")
        print(f"[OPENAI] Response End: ...{answer[-200:]}")
        print(f"{'='*80}\n")
        logger.info(f"OpenAI Response Length: {len(answer)} chars, {len(answer.split())} words")

        return answer or "Unable to generate analysis. Please try again."

    except Exception as e:
        logger.error(f"OpenAI GPT-4o error in comprehensive analysis: {e}")
        # Fallback to Claude if OpenAI fails
        try:
            from anthropic import Anthropic
            api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
            if api_key:
                logger.info("Falling back to Claude Sonnet...")
                client = Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=3000,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text if response.content else ""
        except:
            pass
        return "Unable to complete legal analysis. Please try again or contact support."


async def _call_claude_haiku_direct(question: str) -> str:
    """
    LEGACY: Fast concise responses using Haiku.
    NOTE: For Q&A, use _call_claude_paralegal_comprehensive instead for detailed analysis.
    """
    try:
        # Use the forced concise wrapper with increased tokens for complete responses
        answer = force_concise_claude(
            user_query=question,
            context=None,
            max_tokens=1500,  # Increased from 100 to prevent mid-sentence cutoffs
            model='claude-3-5-haiku-20241022'
        )

        return answer or "Contact an attorney. Time limits may apply."

    except Exception as e:
        logger.error(f"Claude error: {e}")
        return "Legal options exist. Contact attorney immediately."