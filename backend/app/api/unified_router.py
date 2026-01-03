"""
Unified API Router - Single endpoint for ALL legal system operations
Routes requests through the central UnifiedLegalSystem
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from ..src.core.unified_system import session_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/unified", tags=["Unified System"])


class UnifiedRequest(BaseModel):
    """Single request model for all actions"""
    sessionId: str
    action: str
    data: Optional[Dict[str, Any]] = {}


@router.post("/process")
async def unified_process(request: UnifiedRequest) -> Dict[str, Any]:
    """
    Single endpoint that handles everything based on context

    Actions:
    - upload_document: Process legal document
    - answer_question: Answer interview question
    - build_defense: Generate defense strategy
    - chat_message: Handle Q&A chat
    - get_status: Get system status
    """

    session_id = request.sessionId
    action = request.action
    data = request.data or {}

    logger.info(f"Unified process - Session: {session_id}, Action: {action}")

    try:
        # Get or create session
        system = session_manager.get_or_create_session(session_id)

        # Route based on action
        if action == 'analyze_document' or action == 'upload_document':
            # Document upload/analysis starts everything
            document_text = data.get('documentText', '')
            if not document_text:
                raise HTTPException(status_code=400, detail="documentText required")

            result = await system.process_document(document_text)
            result['sessionId'] = session_id

        elif action == 'start_interview':
            # Start interview after document analysis
            result = await system.start_interview()
            result['sessionId'] = session_id

        elif action == 'submit_answer' or action == 'answer_question':
            # Interview answer
            answer = data.get('answer')
            if not answer:
                raise HTTPException(status_code=400, detail="answer required")

            result = await system.process_interview_answer(answer)
            result['sessionId'] = session_id

        elif action == 'build_defense':
            # Build defense using ALL context
            result = await system.build_defense_strategy()
            result['sessionId'] = session_id

        elif action == 'ask_question' or action == 'chat_message':
            # Q&A using context
            question = data.get('question') or data.get('message', '')
            if not question:
                raise HTTPException(status_code=400, detail="question or message required")

            result = await system.handle_qa_message(question)
            result['sessionId'] = session_id

        elif action == 'get_status':
            # Get current system state
            result = system.get_system_status()

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

        # Always return system efficiency metrics
        result['system_efficiency'] = {
            'session_id': session_id,
            'state': system.state.value,
            'ai_calls': system.ai_calls_made,
            'cached_responses': system.ai_calls_cached,
            'cache_rate': system.ai_calls_cached / max(system.ai_calls_made, 1) if system.ai_calls_made > 0 else 0,
            'context_size': len(str(system.context))
        }

        logger.info(f"Action {action} completed - AI calls: {system.ai_calls_made}, Cached: {system.ai_calls_cached}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified process: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"System error: {str(e)}")


@router.get("/session/{session_id}/context")
async def get_session_context(session_id: str) -> Dict[str, Any]:
    """
    Get full context for debugging
    Shows all stored context and system state
    """

    try:
        system = session_manager.get_or_create_session(session_id)

        return {
            'context': system.context,
            'state': system.state.value,
            'efficiency': system.get_system_status(),
            'components': {
                name: 'active' if component else 'inactive'
                for name, component in system.components.items()
            }
        }
    except Exception as e:
        logger.error(f"Error getting session context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def clear_session(session_id: str) -> Dict[str, Any]:
    """
    Clear session data
    Removes all stored context and frees memory
    """

    try:
        if session_id in session_manager.sessions:
            del session_manager.sessions[session_id]
            logger.info(f"Session {session_id} cleared")
            return {'cleared': True, 'session_id': session_id}
        else:
            return {'cleared': False, 'message': 'Session not found'}
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/stats")
async def get_sessions_stats() -> Dict[str, Any]:
    """
    Get statistics about all active sessions
    Useful for monitoring system load
    """

    total_sessions = len(session_manager.sessions)
    total_ai_calls = sum(s.ai_calls_made for s in session_manager.sessions.values())
    total_cached = sum(s.ai_calls_cached for s in session_manager.sessions.values())

    states = {}
    for system in session_manager.sessions.values():
        state = system.state.value
        states[state] = states.get(state, 0) + 1

    return {
        'total_sessions': total_sessions,
        'total_ai_calls': total_ai_calls,
        'total_cached_responses': total_cached,
        'overall_cache_rate': total_cached / max(total_ai_calls, 1) if total_ai_calls > 0 else 0,
        'states': states,
        'sessions': list(session_manager.sessions.keys())
    }


@router.post("/sessions/cleanup")
async def cleanup_old_sessions() -> Dict[str, Any]:
    """
    Manually trigger session cleanup
    Removes inactive sessions
    """

    before_count = len(session_manager.sessions)
    session_manager.cleanup_old_sessions()
    after_count = len(session_manager.sessions)

    return {
        'cleaned': before_count - after_count,
        'remaining': after_count
    }
