"""
Integrated Defense Flow API
Enforces interview MUST happen before defense building
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from ..agents.interview_agent import InterviewAgent, interview_agents
from .qa_handler import QAHandler


router = APIRouter(prefix="/api/defense-flow", tags=["Defense Flow"])


class StartFlowRequest(BaseModel):
    sessionId: str
    documentText: str


class AnswerRequest(BaseModel):
    sessionId: str
    answer: str


class BuildDefenseRequest(BaseModel):
    sessionId: str


class QAMessageRequest(BaseModel):
    message: str
    sessionId: Optional[str] = None


@router.post('/start')
async def start_defense_flow(request: StartFlowRequest) -> Dict[str, Any]:
    '''Start the defense flow with document upload - RETURNS FIRST QUESTION'''

    session_id = request.sessionId
    document_text = request.documentText

    # Create new interview agent
    agent = InterviewAgent(session_id)
    interview_agents[session_id] = agent

    # Process document and GET FIRST QUESTION
    result = agent.process_document(document_text)

    # ENSURE question is returned
    if not result.get('current_question'):
        # Force a question if none generated
        result['current_question'] = {
            'id': 'when_started',
            'text': 'When did this legal issue start?',
            'options': ['This month', '1-6 months ago', '6-12 months ago', 'Over 1 year ago'],
            'critical': True,
            'priority': 1
        }
        result['total_questions'] = 5

    return {
        'action': result['action'],
        'message': result['message'],
        'document_summary': result['document_summary'],
        'current_question': result['current_question'],
        'question_number': result.get('question_number', 1),
        'total_questions': result['total_questions'],
        'can_build_defense': result['can_build_defense'],
        'state': 'interviewing'
    }


@router.post('/answer')
async def answer_interview_question(request: AnswerRequest) -> Dict[str, Any]:
    '''Answer interview question - moves to next question or completes'''

    session_id = request.sessionId
    answer = request.answer

    agent = interview_agents.get(session_id)
    if not agent:
        raise HTTPException(status_code=400, detail='No interview in progress')

    # Process answer and get next question or complete
    result = agent.answer_question(answer)

    # Check if interview is complete
    if result.get('action') == 'INTERVIEW_COMPLETE':
        return {
            'action': 'INTERVIEW_COMPLETE',
            'complete': True,
            'can_build_defense': result['can_build_defense'],
            'ready_to_build': result['ready_to_build'],
            'message': result['message'],
            'answers_collected': result['answers_collected'],
            'state': 'ready_for_defense'
        }

    # Return next question
    return {
        'action': result['action'],
        'current_question': result['current_question'],
        'question_number': result['question_number'],
        'total_questions': result['total_questions'],
        'can_build_defense': result['can_build_defense'],
        'defense_found': result.get('defense_found'),
        'progress': result.get('progress', 0),
        'state': 'interviewing'
    }


@router.post('/build')
async def build_defense(request: BuildDefenseRequest) -> Dict[str, Any]:
    '''Build defense ONLY after interview complete - ENFORCED'''

    session_id = request.sessionId

    agent = interview_agents.get(session_id)
    if not agent:
        raise HTTPException(status_code=400, detail='No interview found')

    # Try to build defense - agent will block if questions not answered
    result = agent.build_defense()

    # If error, agent blocked defense building
    if 'error' in result:
        raise HTTPException(
            status_code=400,
            detail={
                'error': result['error'],
                'message': result['message'],
                'questions_remaining': result.get('questions_remaining'),
                'current_question': result.get('current_question')
            }
        )

    # Success - return defenses
    return {
        'action': result['action'],
        'defenses': result['defenses'],
        'immediate_actions': result['immediate_actions'],
        'evidence_needed': result['evidence_needed'],
        'based_on': result['based_on'],
        'state': 'complete'
    }


@router.post('/qa/message')
async def handle_qa_message(request: QAMessageRequest) -> Dict[str, Any]:
    '''Handle Q&A with FORCED conciseness - NO AI verbosity'''

    message = request.message
    session_id = request.sessionId or 'default_session'

    # Use QA handler for concise response
    result = await QAHandler.process_qa_message(message, session_id)

    return {
        'response': result['response'],
        'word_count': result['word_count'],
        'model': result['model'],
        'has_question': result['has_question'],
        'cached': True
    }


@router.get('/status/{session_id}')
async def get_flow_status(session_id: str) -> Dict[str, Any]:
    '''Get current flow status - shows interview progress'''

    agent = interview_agents.get(session_id)
    if not agent:
        return {
            'status': 'no_session',
            'message': 'No active session found'
        }

    status = agent.get_status()

    return {
        'session_id': session_id,
        'state': status['state'],
        'questions_asked': status['questions_asked'],
        'total_questions': status['total_questions'],
        'answers_collected': status['answers_collected'],
        'can_build_defense': status['can_build_defense'],
        'document_loaded': status['document_loaded'],
        'case_type': status['case_type'],
        'progress_percentage': status['progress_percentage']
    }


@router.delete('/session/{session_id}')
async def clear_session(session_id: str) -> Dict[str, Any]:
    '''Clear session data'''

    if session_id in interview_agents:
        del interview_agents[session_id]
        return {
            'cleared': True,
            'session_id': session_id
        }

    return {
        'cleared': False,
        'message': 'Session not found'
    }
