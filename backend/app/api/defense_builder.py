"""
Defense Strategy Builder API - ACTUAL DEFENSE STRATEGIES
Provides concrete defense options, not questions
Includes Adversarial Simulation for opposing counsel analysis
"""

import logging
import os
import re
import uuid as uuid_lib
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import anthropic
from ..src.shared.ai.concise_ai_wrapper import force_concise_claude, force_concise_defense_strategy
from ..src.core.database import get_db
from ..models.legal_documents import Document, DefenseSession, DefenseMessage, QASession, QAMessage
from ..models.adversarial import AdversarialSimulation, CounterArgument, TIER_ADVERSARIAL_FEATURES
from ..src.services.adversarial_simulation_service import AdversarialSimulationService
from ..core.feature_access import Feature, get_feature_config
from ..services.feature_gate_service import FeatureGateService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/defense", tags=["Defense Strategy"])

# Initialize Claude client
claude_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))


class DefenseAnalysisRequest(BaseModel):
    document_text: str
    document_analysis: Dict[str, Any]
    case_context: Dict[str, Any] = {}
    session_id: Optional[str] = None  # For persistence
    document_id: Optional[str] = None  # Link to document in database


# Adversarial Simulation Models
class AdversarialStartRequest(BaseModel):
    session_id: str  # Defense session ID
    case_type: str
    user_id: Optional[str] = None


class AdversarialUpdateRequest(BaseModel):
    new_facts: Dict[str, Any]
    question_key: str


@router.post("/analyze")
async def analyze_defenses(
    request: DefenseAnalysisRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyze and return ACTUAL defense strategies with concrete options
    """
    try:
        session_id = request.session_id or f"session_{datetime.now().timestamp()}"
        document_id = request.document_id
        doc_type = request.document_analysis.get('document_type', '').lower()

        # Identify case type from document
        case_type = _identify_case_type(doc_type, request.document_text)

        # Get defense analysis from Claude (now includes Q&A history)
        defense_data = await _analyze_for_defense(
            request.document_text,
            case_type,
            request.document_analysis,
            document_id,
            db
        )

        # REMOVE ATTORNEY DISCLAIMERS - Strip from actions
        actions = [action for action in defense_data["actions"]
                   if not any(phrase in action.lower() for phrase in ['consult attorney', 'seek legal', 'contact lawyer', 'speak to attorney'])]

        # Generate suggested follow-up questions based on defenses identified
        suggested_questions = _generate_defense_questions(
            case_type,
            defense_data["defenses"],
            defense_data["evidence"],
            request.document_analysis
        )

        response = {
            "situation": defense_data["situation"],
            "defenses": defense_data["defenses"],
            "actions": actions,  # Filtered to remove attorney referrals
            "evidence": defense_data["evidence"],
            "suggested_questions": suggested_questions,  # Persistent questions about defenses
            "case_type": case_type,
            "analysis_summary": {
                "total_defenses": len(defense_data["defenses"]),
                "document_type": request.document_analysis.get('document_type'),
                "analysis_date": datetime.now().isoformat()
            }
            # NO DISCLAIMERS - We give actual defenses
        }

        # Save to database for persistence
        if document_id:
            try:
                # Get or create DefenseSession
                defense_session = db.query(DefenseSession).filter(
                    DefenseSession.document_id == document_id,
                    DefenseSession.session_id == session_id
                ).first()

                if not defense_session:
                    # Create new defense session
                    defense_session = DefenseSession(
                        id=str(uuid_lib.uuid4()),
                        document_id=document_id,
                        session_id=session_id,
                        started_at=datetime.utcnow(),
                        phase='complete',  # Directly complete since this is analysis result
                        case_type=case_type,
                        situation_summary=defense_data["situation"],
                        defenses=defense_data["defenses"],
                        actions=actions,
                        evidence_needed=defense_data["evidence"],
                        analysis_data=response
                    )
                    db.add(defense_session)
                else:
                    # Update existing session
                    defense_session.case_type = case_type
                    defense_session.situation_summary = defense_data["situation"]
                    defense_session.defenses = defense_data["defenses"]
                    defense_session.actions = actions
                    defense_session.evidence_needed = defense_data["evidence"]
                    defense_session.analysis_data = response
                    defense_session.completed_at = datetime.utcnow()
                    defense_session.last_activity = datetime.utcnow()

                # Save summary message
                summary_message = DefenseMessage(
                    id=str(uuid_lib.uuid4()),
                    session_id=defense_session.id,
                    role='ai',
                    content=f"Defense Strategy Analysis Complete\n\n{defense_data['situation']}",
                    timestamp=datetime.utcnow()
                )
                db.add(summary_message)

                db.commit()
                logger.info(f"Saved defense analysis to database for session {session_id}")
            except Exception as db_error:
                logger.error(f"Database save error in defense builder: {str(db_error)}")
                db.rollback()
                # Continue even if DB save fails

        logger.info(f"Defense analysis completed for {case_type}")
        return response

    except Exception as e:
        logger.error(f"Error in defense analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Defense analysis error: {str(e)}"
        )


@router.get("/session/{session_id}")
async def get_defense_session(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieve defense session from database
    """
    try:
        # Get defense session for this session_id
        defense_session = db.query(DefenseSession).filter(
            DefenseSession.session_id == session_id
        ).order_by(DefenseSession.started_at.desc()).first()

        if not defense_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Defense session not found"
            )

        return {
            "session_id": session_id,
            "case_type": defense_session.case_type,
            "situation": defense_session.situation_summary,
            "defenses": defense_session.defenses,
            "actions": defense_session.actions,
            "evidence": defense_session.evidence_needed,
            "phase": defense_session.phase,
            "started_at": defense_session.started_at.isoformat() if defense_session.started_at else None,
            "completed_at": defense_session.completed_at.isoformat() if defense_session.completed_at else None,
            "analysis_data": defense_session.analysis_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving defense session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve defense session: {str(e)}"
        )


async def _analyze_for_defense(
    document: str,
    case_type: str,
    analysis: Dict[str, Any],
    document_id: Optional[str] = None,
    db: Session = None
) -> Dict[str, Any]:
    """
    Use AI to analyze interview responses and generate personalized defense strategy
    Includes Q&A session history for comprehensive context
    Falls back to templates only if AI fails
    """
    try:
        # Extract interview responses from document text
        interview_section = ""
        if "=== INTERVIEW RESPONSES ===" in document:
            interview_section = document.split("=== INTERVIEW RESPONSES ===")[1]

        # Query Q&A sessions to get previous conversation about this document
        qa_context = ""
        if document_id and db:
            qa_context = await _extract_qa_context(document_id, db)
            if qa_context:
                logger.info(f"Including Q&A context from {len(qa_context)} characters of conversation history")

        # Build comprehensive prompt for senior litigation attorney
        prompt = f"""You are a Senior Defense Counsel with 20+ years of complex litigation experience.

DOCUMENT ANALYSIS:
{document[:3000]}

INTERVIEW RESPONSES FROM CLIENT:
{interview_section}

PREVIOUS Q&A CONVERSATION ABOUT THIS CASE:
{qa_context}

CASE TYPE: {case_type}

Based on the document and the client's detailed interview responses, provide a comprehensive defense strategy analysis.

REQUIRED FORMAT (JSON):
{{
    "situation": "2-3 sentence case summary incorporating client's specific facts",
    "defenses": [
        {{
            "title": "Defense name",
            "description": "Detailed explanation of how this defense works legally",
            "reasoning": "WHY this defense is recommended for THIS specific case - reference client's specific facts, timeline, statements from interview/Q&A that make this defense viable",
            "strength": "Strong/Moderate/Weak"
        }}
    ],
    "actions": [
        "Specific action items based on client's situation (NO generic 'consult attorney' advice)"
    ],
    "evidence": [
        "Specific evidence client mentioned or should gather based on their responses"
    ]
}}

CRITICAL INSTRUCTIONS:
1. Use the client's SPECIFIC facts from BOTH their interview responses AND Q&A conversation
2. Tailor each defense to THEIR situation, not generic templates
3. Reference specific details they provided (dates, amounts, communications, concerns from Q&A)
4. If the Q&A conversation revealed important facts about the lawsuit, incorporate those into the analysis
5. Identify 3-5 viable defenses ranked by strength for THEIR case
6. Give concrete action items based on what they told you in BOTH sources
7. NO attorney disclaimers - provide actual strategic guidance
8. Be direct, precise, and actionable like a real litigation attorney

Provide ONLY the JSON response, no other text."""

        # Call Claude AI
        logger.info(f"Calling Claude AI for defense analysis of {case_type}")

        message = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        ai_response = message.content[0].text
        logger.info(f"Received AI response: {len(ai_response)} characters")

        # Parse JSON response
        import json

        # Extract JSON if wrapped in markdown
        if "```json" in ai_response:
            json_start = ai_response.find("```json") + 7
            json_end = ai_response.find("```", json_start)
            json_str = ai_response[json_start:json_end].strip()
        else:
            json_str = ai_response.strip()

        defense_data = json.loads(json_str)

        # Validate structure
        if "defenses" not in defense_data or "actions" not in defense_data:
            raise ValueError("AI response missing required fields")

        logger.info(f"Successfully parsed AI defense strategy with {len(defense_data.get('defenses', []))} defenses")
        return defense_data

    except Exception as e:
        logger.error(f"AI defense analysis failed: {str(e)}, falling back to templates")
        # Fall back to templates only if AI fails
        return _get_template_defenses(case_type)


def _identify_case_type(doc_type: str, document_text: str) -> str:
    """Identify case type from document"""
    doc_lower = doc_type.lower() + " " + document_text[:1000].lower()

    if any(kw in doc_lower for kw in ['debt', 'collection', 'creditor', 'owe', 'payment']):
        return 'debt_collection'
    elif any(kw in doc_lower for kw in ['eviction', 'evict', 'landlord', 'tenant', 'lease', 'rent']):
        return 'eviction'
    elif any(kw in doc_lower for kw in ['bankruptcy', 'chapter 7', 'chapter 13', 'discharge']):
        return 'bankruptcy'
    elif any(kw in doc_lower for kw in ['foreclosure', 'mortgage', 'default notice']):
        return 'foreclosure'
    elif any(kw in doc_lower for kw in ['criminal', 'arrest', 'charge', 'prosecution']):
        return 'criminal'
    else:
        return 'general'


def _extract_situation(text: str) -> str:
    """Extract situation summary"""
    match = re.search(r'SITUATION:\s*(.+?)(?:\n|DEFENSE)', text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return "Legal matter requiring defense analysis."


def _extract_defenses(text: str) -> List[Dict[str, Any]]:
    """Parse defense options from AI response"""
    defense_section = re.search(r'DEFENSE OPTIONS:(.*?)IMMEDIATE ACTIONS:', text, re.IGNORECASE | re.DOTALL)
    if not defense_section:
        return []

    defenses = []
    lines = defense_section.group(1).split('\n')

    for line in lines:
        line = line.strip()
        if not line or not line[0].isdigit():
            continue

        # Match pattern: "1. Defense Name: Description Requirements: Requirements"
        match = re.match(r'\d+\.\s*([^:]+):\s*(.+?)(?:Requirements?:\s*(.+))?$', line, re.IGNORECASE)
        if match:
            defenses.append({
                "name": match.group(1).strip(),
                "description": match.group(2).strip(),
                "requirements": match.group(3).strip() if match.group(3) else "Consult attorney for specific requirements",
                "strength": 0.75  # Default strength
            })

    return defenses


def _extract_actions(text: str) -> List[str]:
    """Extract immediate actions"""
    action_section = re.search(r'IMMEDIATE ACTIONS:(.*?)EVIDENCE NEEDED:', text, re.IGNORECASE | re.DOTALL)
    if not action_section:
        return ["Consult attorney immediately", "Review all deadlines", "Gather documentation"]

    actions = []
    for line in action_section.group(1).split('\n'):
        line = line.strip()
        if line and (line.startswith('-') or line.startswith('•')):
            actions.append(line[1:].strip())

    return actions[:5]  # Limit to 5


def _extract_evidence(text: str) -> List[str]:
    """Extract evidence needed"""
    evidence_section = re.search(r'EVIDENCE NEEDED:(.*?)(?:\n\n|$)', text, re.IGNORECASE | re.DOTALL)
    if not evidence_section:
        return ["All related documents", "Communication records", "Financial records"]

    evidence = []
    for line in evidence_section.group(1).split('\n'):
        line = line.strip()
        if line and (line.startswith('-') or line.startswith('•')):
            evidence.append(line[1:].strip())

    return evidence[:5]  # Limit to 5


async def _extract_qa_context(document_id: str, db: Session) -> str:
    """
    Extract relevant Q&A conversation history for the document
    Returns formatted string of Q&A exchanges that provide case context
    """
    try:
        # Query all Q&A sessions for this document
        qa_sessions = db.query(QASession).filter(
            QASession.document_id == document_id,
            QASession.is_active == True
        ).all()

        if not qa_sessions:
            return ""

        # Build conversation context from all sessions
        qa_exchanges = []

        for session in qa_sessions:
            # Get all messages for this session
            messages = db.query(QAMessage).filter(
                QAMessage.session_id == session.id
            ).order_by(QAMessage.timestamp).all()

            # Group messages into Q&A pairs
            i = 0
            while i < len(messages):
                if messages[i].role == "user" and i + 1 < len(messages) and messages[i + 1].role == "ai":
                    user_question = messages[i].content
                    ai_answer = messages[i + 1].content

                    # Only include substantive exchanges (skip very short ones)
                    if len(user_question) > 10 and len(ai_answer) > 20:
                        qa_exchanges.append(f"User: {user_question}\nAI: {ai_answer[:500]}...")  # Limit AI response length

                    i += 2
                else:
                    i += 1

        if not qa_exchanges:
            return ""

        # Format the Q&A context
        formatted_context = "\n\n".join(qa_exchanges[:10])  # Limit to 10 most relevant exchanges

        return formatted_context

    except Exception as e:
        logger.error(f"Error extracting Q&A context: {str(e)}")
        return ""


def _generate_defense_questions(
    case_type: str,
    defenses: List[Dict[str, Any]],
    evidence: List[str],
    document_analysis: Dict[str, Any]
) -> List[str]:
    """
    Generate suggested follow-up questions about the defenses identified
    """
    questions = []

    # General questions about implementing defenses
    questions.extend([
        "Which defense should I prioritize?",
        "What evidence strengthens each defense?",
        "What are the next steps to pursue these defenses?",
        "How do I document evidence for these defenses?"
    ])

    # Case-specific questions
    if case_type == 'debt_collection':
        questions.extend([
            "How do I request debt validation?",
            "What documents prove the statute of limitations?",
            "How do I challenge the plaintiff's standing?"
        ])
    elif case_type == 'eviction':
        questions.extend([
            "How do I document property conditions?",
            "What constitutes proper notice in my state?",
            "How do I prove retaliatory eviction?"
        ])
    elif case_type == 'bankruptcy':
        questions.extend([
            "What debts can be discharged?",
            "How long does the bankruptcy process take?",
            "What assets are protected?"
        ])
    elif case_type == 'foreclosure':
        questions.extend([
            "What is dual-tracking and how do I prove it?",
            "How do I apply for loan modification?",
            "What are my rights during foreclosure?"
        ])

    # Add defense-specific questions
    for defense in defenses[:2]:  # Focus on top 2 defenses
        defense_title = defense.get('title', '')
        if 'statute of limitations' in defense_title.lower():
            questions.append("How do I calculate when the statute of limitations started?")
        elif 'standing' in defense_title.lower():
            questions.append("What documents prove they don't own the debt?")
        elif 'notice' in defense_title.lower():
            questions.append("What are the exact notice requirements in my jurisdiction?")

    # Return unique questions
    seen = set()
    unique_questions = []
    for q in questions:
        if q.lower() not in seen and len(unique_questions) < 5:
            seen.add(q.lower())
            unique_questions.append(q)

    return unique_questions


def _get_template_defenses(case_type: str) -> Dict[str, Any]:
    """
    FALLBACK TEMPLATES WITH REAL DEFENSES
    """
    templates = {
        'debt_collection': {
            'situation': 'Debt collection lawsuit filed against you.',
            'defenses': [
                {
                    'title': 'Statute of Limitations',
                    'description': 'Debt may be too old to collect legally. Last payment over 4-6 years ago (varies by state). If applicable, this is a complete bar to recovery.',
                    'reasoning': 'Recommended because many debt collection lawsuits involve old debts where the statute of limitations has expired. If your last payment or written acknowledgment was over 4-6 years ago, this defense can result in complete dismissal.',
                    'strength': 'Strong'
                },
                {
                    'title': 'Lack of Standing',
                    'description': 'Plaintiff cannot prove they own the debt. Request original contract and chain of ownership documentation. Many debt buyers lack proper documentation.',
                    'reasoning': 'Recommended because debt buyers often lack proper documentation showing they legally own the debt. Forcing them to prove the chain of ownership frequently results in dismissals when they cannot produce required evidence.',
                    'strength': 'Moderate'
                },
                {
                    'title': 'Payment Already Made',
                    'description': 'Debt was already paid or settled. Gather bank statements or settlement agreements showing payment.',
                    'reasoning': 'Recommended if you have any record of payment, settlement, or discharge of this debt. Collection companies sometimes pursue debts that were already paid or included in bankruptcy discharge.',
                    'strength': 'Strong'
                }
            ],
            'actions': [
                'File answer within 20-30 days',
                'Request debt validation letter in writing',
                'Gather all payment records and bank statements',
                'Calendar all court dates immediately',
                'Request original contract and assignment documents'
            ],
            'evidence': [
                'Original signed contract',
                'Payment history',
                'Account statements',
                'Settlement letters',
                'Credit report'
            ]
        },
        'eviction': {
            'situation': 'Eviction notice received from landlord.',
            'defenses': [
                {
                    'title': 'Improper Notice',
                    'description': "Landlord didn't follow proper eviction procedures. Check notice period and format against state law. Technical defects in notice can defeat eviction.",
                    'reasoning': 'Recommended because landlords frequently make procedural errors in eviction notices. If the notice period was too short, wrong format was used, or required information is missing, the eviction can be dismissed and landlord must start over with proper notice.',
                    'strength': 'Strong'
                },
                {
                    'title': 'Warranty of Habitability',
                    'description': 'Property has serious repair issues landlord failed to address. Document with photos and repair requests. Can offset or eliminate rent liability.',
                    'reasoning': 'Recommended if you have documented any serious repair issues (heating, plumbing, mold, etc.) that the landlord failed to address. This defense can reduce or eliminate claimed rent owed and may result in you receiving damages.',
                    'strength': 'Moderate'
                },
                {
                    'title': 'Retaliatory Eviction',
                    'description': 'Eviction is revenge for exercising tenant rights (complaints, requests). Create timeline showing complaints preceded eviction notice.',
                    'reasoning': 'Recommended if you recently made repair requests, complained to housing authorities, or exercised tenant rights before receiving the eviction notice. Retaliation is illegal and can result in dismissal plus damages.',
                    'strength': 'Moderate'
                }
            ],
            'actions': [
                'File response by deadline on notice (typically 5 days)',
                'Document property conditions with dated photos',
                'Gather all rent payment receipts',
                'Review lease agreement for violations',
                'Send repair requests via certified mail'
            ],
            'evidence': [
                'Lease agreement',
                'Rent receipts',
                'Repair requests',
                'Photos of property issues',
                'Communication with landlord'
            ]
        },
        'bankruptcy': {
            'situation': 'Considering bankruptcy filing to address overwhelming debt.',
            'defenses': [
                {
                    'title': 'Chapter 7 Liquidation',
                    'description': 'Discharge most debts quickly (3-6 months). Must pass means test with income below state median. Provides fresh financial start.',
                    'reasoning': 'Recommended if your income is below state median and you have primarily unsecured debts (credit cards, medical bills, personal loans). Provides fastest relief with most debts discharged in 3-6 months.',
                    'strength': 'Strong'
                },
                {
                    'title': 'Chapter 13 Reorganization',
                    'description': 'Keep property and repay affordable portion over 3-5 years. Requires regular income to fund payment plan. Can save home from foreclosure.',
                    'reasoning': 'Recommended if you have regular income and want to keep valuable property like a home or car. Allows you to catch up on mortgage arrears while protecting assets from liquidation. Particularly useful if facing foreclosure.',
                    'strength': 'Strong'
                },
                {
                    'title': 'Subchapter V Small Business',
                    'description': 'Simplified reorganization process for small business. Requires business debts under $3,024,725. More flexible than Chapter 11.',
                    'reasoning': 'Recommended if you are a small business owner with business debts under $3 million. Provides reorganization benefits with fewer requirements and lower costs than traditional Chapter 11.',
                    'strength': 'Moderate'
                }
            ],
            'actions': [
                'Complete credit counseling course (required within 180 days)',
                'Gather 2 years tax returns and 6 months pay stubs',
                'List all debts, assets, and monthly expenses',
                'Stop making payments on dischargeable debts',
                'File petition with bankruptcy court ($338 fee)'
            ],
            'evidence': [
                'Tax returns (2 years)',
                'Pay stubs (6 months)',
                'Bank statements',
                'List of creditors with amounts',
                'Property valuations'
            ]
        },
        'foreclosure': {
            'situation': 'Foreclosure action initiated on your property.',
            'defenses': [
                {
                    'title': 'Dual-Tracking Violation',
                    'description': 'Bank violated dual-tracking rules by pursuing foreclosure while modification pending. Federal law prohibits this. Can halt foreclosure.',
                    'reasoning': 'Recommended if you applied for a loan modification and received a foreclosure notice while your application was pending. Federal law prohibits banks from pursuing foreclosure while actively reviewing loss mitigation applications.',
                    'strength': 'Strong'
                },
                {
                    'title': 'Improper Notice',
                    'description': 'Required foreclosure notices not properly given. Check state-specific notice requirements. Technical defects can defeat foreclosure action.',
                    'reasoning': 'Recommended because banks frequently fail to provide all required foreclosure notices or provide them in improper format/timing. Technical defects in notice can invalidate the entire foreclosure proceeding.',
                    'strength': 'Moderate'
                },
                {
                    'title': 'Payment Accounting Error',
                    'description': 'Dispute default calculation. Compare payment records with servicer accounting. Force reconciliation and proper crediting.',
                    'reasoning': 'Recommended if you have made payments that may not have been properly credited, or if you dispute the servicer\'s calculation of the default amount. Payment misapplication is common and can eliminate claimed defaults.',
                    'strength': 'Moderate'
                }
            ],
            'actions': [
                'Request full payment history from servicer',
                'Apply for loss mitigation within 37 days of notice',
                'File answer to foreclosure complaint by deadline',
                'Request all loan documents via qualified written request',
                'Document all income and hardship proof'
            ],
            'evidence': [
                'Mortgage documents',
                'Payment records',
                'Modification correspondence',
                'Hardship documentation',
                'Property valuation'
            ]
        },
        'criminal': {
            'situation': 'Criminal charges filed requiring immediate legal representation.',
            'defenses': [
                {
                    'title': 'Insufficient Evidence',
                    'description': 'Prosecution cannot prove case beyond reasonable doubt. Challenge credibility and sufficiency of evidence. Force prosecution to meet burden.',
                    'reasoning': 'Recommended because prosecution bears the burden of proving guilt beyond a reasonable doubt. If evidence is weak, circumstantial, or relies on unreliable witnesses, this defense challenges whether prosecution can meet their burden.',
                    'strength': 'Moderate'
                },
                {
                    'title': 'Constitutional Violations',
                    'description': 'Illegal search, seizure, or interrogation. Evidence of rights violations can result in suppression of evidence. May lead to dismissal.',
                    'reasoning': 'Recommended if police conducted searches without warrant, questioned you without Miranda warnings, or violated other constitutional protections. Suppression of illegally obtained evidence often results in case dismissal.',
                    'strength': 'Strong'
                },
                {
                    'title': 'Alibi Defense',
                    'description': 'Defendant was elsewhere when crime occurred. Gather witnesses or records proving different location (GPS, receipts, surveillance).',
                    'reasoning': 'Recommended if you have credible evidence showing you were at a different location when the crime occurred. GPS data, receipts, surveillance footage, or credible witnesses can provide strong alibi evidence.',
                    'strength': 'Strong'
                }
            ],
            'actions': [
                'Exercise right to remain silent',
                'Request attorney immediately',
                'Do not speak to police without attorney',
                'Gather alibi witnesses',
                'Preserve all evidence'
            ],
            'evidence': [
                'Witness statements',
                'Location records (GPS, receipts)',
                'Surveillance footage',
                'Communication records',
                'Character references'
            ]
        },
        'general': {
            'situation': 'Legal matter requiring comprehensive defense strategy.',
            'defenses': [
                {
                    'title': 'Statute of Limitations',
                    'description': 'Claim may be time-barred. Calculate time from when cause of action accrued. If expired, complete defense to lawsuit.',
                    'reasoning': 'Recommended to investigate the timing of when the alleged incident or breach occurred. If the applicable statute of limitations has expired, this provides a complete defense resulting in dismissal regardless of claim merits.',
                    'strength': 'Strong'
                },
                {
                    'title': 'Procedural Defects',
                    'description': 'Opposing party failed to follow proper procedures. Identify specific procedural violations (service, notice, filing). Can result in dismissal.',
                    'reasoning': 'Recommended because plaintiffs frequently make procedural errors in service of process, notice requirements, or filing deadlines. Identifying and challenging these defects can result in dismissal or delay while plaintiff corrects errors.',
                    'strength': 'Moderate'
                },
                {
                    'title': 'Insufficient Evidence',
                    'description': 'Opposing party cannot meet their burden of proof. Challenge credibility, relevance, and admissibility of evidence.',
                    'reasoning': 'Recommended as a baseline defense in any case. Force the opposing party to prove every element of their claim with admissible evidence. Many cases fail when plaintiff cannot produce sufficient evidence to meet their burden.',
                    'strength': 'Moderate'
                }
            ],
            'actions': [
                'File timely response',
                'Preserve all evidence',
                'Document everything',
                'Consult qualified attorney',
                'Review all deadlines carefully'
            ],
            'evidence': [
                'All related documents',
                'Communication records',
                'Witness contact information',
                'Financial records if relevant',
                'Timeline of events'
            ]
        }
    }

    return templates.get(case_type, templates['general'])


# =============================================================================
# ADVERSARIAL SIMULATION ENDPOINTS
# =============================================================================

@router.post("/adversarial/start")
async def start_adversarial_simulation(
    request: AdversarialStartRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Start an adversarial simulation for a defense session.
    Runs in background to generate opposing counsel arguments.

    Requires: ADVERSARIAL_SIMULATION feature access (Basic tier and above)
    """
    try:
        # Check feature access
        # For now, use tier from request or default to basic limits
        # In production, would check user's actual tier via FeatureGateService
        tier = "basic"  # Default tier for unauthenticated requests

        tier_config = TIER_ADVERSARIAL_FEATURES.get(tier, TIER_ADVERSARIAL_FEATURES["free"])

        if not tier_config.get("enabled"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Feature not available",
                    "message": "Adversarial simulation requires a Basic subscription or higher",
                    "upgrade_url": "/settings?tab=subscription"
                }
            )

        max_counter_arguments = tier_config.get("counter_arguments", 3)

        # Verify defense session exists
        defense_session = db.query(DefenseSession).filter(
            DefenseSession.id == request.session_id
        ).first()

        if not defense_session:
            # Try matching by session_id field
            defense_session = db.query(DefenseSession).filter(
                DefenseSession.session_id == request.session_id
            ).first()

        if not defense_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Defense session not found"
            )

        # Create adversarial simulation service
        service = AdversarialSimulationService(db)

        # Start simulation
        result = await service.start_simulation(
            defense_session_id=defense_session.id,
            user_id=request.user_id or defense_session.user_id or "anonymous",
            case_type=request.case_type or defense_session.case_type or "general",
            max_counter_arguments=max_counter_arguments
        )

        logger.info(f"Started adversarial simulation {result['simulation_id']} for session {request.session_id}")

        return {
            "simulation_id": result["simulation_id"],
            "status": "started",
            "max_counter_arguments": max_counter_arguments,
            "weakness_analysis": tier_config.get("weakness_analysis", False),
            "message": "Adversarial simulation started. Use /status endpoint to track progress."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting adversarial simulation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start simulation: {str(e)}"
        )


@router.get("/adversarial/{simulation_id}/status")
async def get_adversarial_status(
    simulation_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the current status and progress of an adversarial simulation.
    """
    try:
        simulation = db.query(AdversarialSimulation).filter(
            AdversarialSimulation.id == simulation_id
        ).first()

        if not simulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation not found"
            )

        # Count generated counter-arguments
        counter_count = db.query(CounterArgument).filter(
            CounterArgument.simulation_id == simulation_id
        ).count()

        # Estimate time remaining based on progress
        if simulation.status == 'completed':
            estimated_time_remaining = 0
        elif simulation.status == 'failed':
            estimated_time_remaining = None
        else:
            # Rough estimate: 30 seconds per counter-argument
            remaining_args = simulation.max_counter_arguments - counter_count
            estimated_time_remaining = remaining_args * 30

        return {
            "simulation_id": simulation_id,
            "status": simulation.status,
            "progress": simulation.progress,
            "counter_count": counter_count,
            "max_counter_arguments": simulation.max_counter_arguments,
            "estimated_time_remaining": estimated_time_remaining,
            "case_type": simulation.case_type,
            "error_message": simulation.error_message if simulation.status == 'failed' else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting simulation status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/adversarial/{simulation_id}/results")
async def get_adversarial_results(
    simulation_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the completed counter-argument matrix from an adversarial simulation.
    """
    try:
        simulation = db.query(AdversarialSimulation).filter(
            AdversarialSimulation.id == simulation_id
        ).first()

        if not simulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation not found"
            )

        if simulation.status != 'completed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Simulation not completed. Current status: {simulation.status}"
            )

        # Get all counter-arguments with rebuttals
        counter_arguments = db.query(CounterArgument).filter(
            CounterArgument.simulation_id == simulation_id
        ).order_by(CounterArgument.likelihood_score.desc()).all()

        # Format counter-arguments for response
        formatted_counters = []
        for counter in counter_arguments:
            formatted_counters.append({
                "id": counter.id,
                "argument_title": counter.argument_title,
                "argument_description": counter.argument_description,
                "legal_basis": counter.legal_basis,
                "likelihood": counter.likelihood,
                "likelihood_score": counter.likelihood_score,
                "likelihood_reasoning": counter.likelihood_reasoning,
                "category": counter.category,
                "evidence_to_support": counter.evidence_to_support,
                "rebuttals": counter.rebuttals
            })

        return {
            "simulation_id": simulation_id,
            "status": "completed",
            "case_type": simulation.case_type,
            "counter_arguments": formatted_counters,
            "weaknesses": simulation.weaknesses or [],
            "overall_strength": simulation.overall_strength,
            "recommendations": simulation.recommendations or [],
            "completed_at": simulation.completed_at.isoformat() if simulation.completed_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting simulation results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get results: {str(e)}"
        )


@router.post("/adversarial/{simulation_id}/update")
async def update_adversarial_simulation(
    simulation_id: str,
    request: AdversarialUpdateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update simulation with new facts from the interview.
    Called after each interview answer.
    """
    try:
        service = AdversarialSimulationService(db)

        result = await service.process_incremental_update(
            simulation_id=simulation_id,
            new_facts=request.new_facts,
            question_key=request.question_key
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating simulation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update simulation: {str(e)}"
        )


@router.post("/adversarial/{simulation_id}/finalize")
async def finalize_adversarial_simulation(
    simulation_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Finalize the simulation - generate all counter-arguments and complete analysis.
    """
    try:
        simulation = db.query(AdversarialSimulation).filter(
            AdversarialSimulation.id == simulation_id
        ).first()

        if not simulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation not found"
            )

        # Get tier config to determine if weakness analysis is enabled
        # For now, use basic tier - in production would check actual user tier
        tier_config = TIER_ADVERSARIAL_FEATURES.get("basic", {})
        include_weaknesses = tier_config.get("weakness_analysis", False)

        service = AdversarialSimulationService(db)

        result = await service.finalize_simulation(
            simulation_id=simulation_id,
            include_weaknesses=include_weaknesses
        )

        logger.info(f"Finalized simulation {simulation_id} with {len(result.get('counter_arguments', []))} counter-arguments")

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error finalizing simulation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalize simulation: {str(e)}"
        )
