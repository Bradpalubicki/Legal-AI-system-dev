"""
Test Endpoint - Bypasses AI Completely
Verifies that the system can return correct responses without AI
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/test", tags=["Test"])


class TestMessageRequest(BaseModel):
    message: str


@router.post("/correct-behavior")
async def test_correct_behavior(request: TestMessageRequest) -> Dict[str, Any]:
    """
    HARDCODED CORRECT RESPONSES - NO AI
    Tests if the system can return proper responses without AI involvement
    """
    msg = request.message.lower()

    # HARDCODED CORRECT RESPONSES
    response = ''
    question = ''
    defenses = []

    if 'sued' in msg or 'lawsuit' in msg:
        response = 'File answer within 20-30 days. Deny false claims. Assert defenses.'
        question = 'When were you served with papers?'
        defenses = [
            'Statute of Limitations - if debt over 4 years old',
            'Lack of Standing - if no proof of ownership',
            'Wrong Amount - if balance calculation errors'
        ]
    elif 'debt' in msg:
        response = 'Request debt validation within 30 days. Check statute of limitations.'
        question = 'How old is this debt?'
        defenses = [
            'Time-barred - if no payment in 4+ years',
            'Already Paid - if you have receipts',
            'Not Your Debt - if identity theft or wrong person'
        ]
    elif 'evict' in msg:
        response = 'You have 5 days to respond to eviction. File answer immediately.'
        question = 'Are there repair issues with the property?'
        defenses = [
            'Improper Notice - if not 30 days notice given',
            'Habitability - if major repairs needed',
            'Retaliation - if after complaint to housing authority'
        ]
    else:
        response = 'Respond by the deadline. Gather your documents.'
        question = 'What type of legal issue is this?'
        defenses = [
            'Procedural Defense - challenge the legal process',
            'Substantive Defense - dispute the facts',
            'Affirmative Defense - admit but explain why'
        ]

    # Build final response
    full_response = response
    full_response += f'\n\n❓ {question}'
    full_response += '\n\nDEFENSE OPTIONS:\n'
    for i, defense in enumerate(defenses, 1):
        full_response += f'{i}. {defense}\n'

    word_count = len(response.split())

    logger.info(f"Test endpoint called with message: {request.message[:50]}")
    logger.info(f"Response word count: {word_count}")

    return {
        "answer": full_response,
        "response": full_response,  # Alias for compatibility
        "next_question": question,
        "defenses": defenses,
        "defense_options": defenses,
        "word_count": word_count,
        "processing_time": 0.001,  # Instant
        "model_used": "hardcoded_template",
        "is_question": True,
        "isQuestion": True,
        "test_mode": True,
        "source": "hardcoded_template",
        "message": "✅ This response bypassed AI completely - pure template"
    }


@router.get("/status")
async def test_status() -> Dict[str, Any]:
    """
    Check if test endpoint is working
    """
    return {
        "status": "operational",
        "endpoint": "/api/v1/test/correct-behavior",
        "purpose": "Test hardcoded responses without AI",
        "usage": "POST with {\"message\": \"your question\"}"
    }
