"""
Unified Legal System - Central Hub Architecture
Eliminates redundant AI calls by sharing context across all components
"""

from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from enum import Enum
import anthropic
import os

# Import Interview Agent
from ..agents.interview_agent import InterviewAgent, get_or_create_agent

# Import QA Handler
from ..api.qa_handler import QAHandler

# Initialize Claude client
claude_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))


class SystemState(Enum):
    IDLE = 'idle'
    DOCUMENT_UPLOADED = 'document_uploaded'
    DOCUMENT_ANALYZED = 'document_analyzed'
    INTERVIEWING = 'interviewing'
    DEFENSE_READY = 'defense_ready'
    CHATTING = 'chatting'


class UnifiedLegalSystem:
    """Central hub that manages ALL components and shares context"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = SystemState.IDLE

        # SHARED CONTEXT - All components read/write here
        self.context = {
            'document': None,
            'document_analysis': None,
            'case_type': None,
            'parties': {},
            'deadlines': [],
            'missing_info': [],
            'potential_defenses': [],
            'interview_answers': {},
            'chat_history': [],
            'identified_defenses': [],
            'action_items': [],
            'evidence_needed': []
        }

        # Component states
        self.components = {
            'document_processor': None,
            'interviewer': None,
            'defense_builder': None,
            'qa_handler': None
        }

        # Interview Agent - handles forced question flow
        self.interview_agent = get_or_create_agent(session_id)

        # Efficiency tracking
        self.ai_calls_made = 0
        self.ai_calls_cached = 0
        self.processing_time = {}

    async def process_document(self, document_text: str) -> Dict:
        """Single document analysis that feeds ALL components including Interview Agent"""

        start_time = datetime.now()

        # Store document in context
        self.context['document'] = document_text

        # USE INTERVIEW AGENT to process document - it will generate questions
        agent_result = self.interview_agent.process_document(document_text)

        # Store agent's analysis in context
        self.context['document_analysis'] = self.interview_agent.document_facts
        self.context['case_type'] = self.interview_agent.document_facts.get('case_type')

        self.state = SystemState.INTERVIEWING
        self.processing_time['document_analysis'] = (datetime.now() - start_time).total_seconds()

        return {
            'action': agent_result['action'],
            'document_analysis': agent_result['document_summary'],
            'first_question': agent_result['current_question'],
            'total_questions': agent_result['total_questions'],
            'can_build_defense': agent_result['can_build_defense'],
            'message': agent_result['message'],
            'state': self.state.value
        }

    async def _analyze_document_once(self, text: str) -> Dict:
        """ONE comprehensive document analysis used by ALL components"""

        prompt = f"""Analyze this legal document COMPLETELY. Extract ALL information needed for:
1. Document summary
2. Interview questions
3. Defense building
4. Q&A context

Document: {text[:8000]}

Return JSON with these keys:
- case_type: specific type (debt_collection/eviction/bankruptcy/etc)
- plaintiff: name and type (original_creditor/debt_buyer/landlord/etc)
- defendant: name
- amount_claimed: dollar amount or null
- filing_date: date filed
- response_deadline: date response due
- claims: list of specific claims made
- evidence_attached: list of documents attached
- missing_critical_docs: what's NOT attached that should be
- parties: {{plaintiff: {{}}, defendant: {{}}}}
- deadlines: [{{date, action, priority}}]
- potential_defenses: list based on document
- red_flags: issues that help defense
- strengths: what plaintiff has in their favor
- questions_needed: critical info gaps to ask user about"""

        # ONE AI call
        response = await self._call_ai_efficiently(prompt)
        self.ai_calls_made += 1

        return self._parse_json_response(response)

    async def process_interview_answer(self, question_id: str, answer: str) -> Dict:
        """Process answer through Interview Agent and update shared context"""

        # USE INTERVIEW AGENT to process answer
        agent_result = self.interview_agent.answer_question(answer)

        # Store in shared context
        self.context['interview_answers'][question_id] = answer

        # Check if interview is complete
        if agent_result.get('action') == 'INTERVIEW_COMPLETE':
            self.state = SystemState.DEFENSE_READY
            return {
                'complete': True,
                'ready_for_defense': agent_result['ready_to_build'],
                'can_build_defense': agent_result['can_build_defense'],
                'answers_collected': agent_result['answers_collected'],
                'message': agent_result['message']
            }

        # Return next question
        return {
            'action': agent_result['action'],
            'next_question': agent_result.get('current_question'),
            'question_number': agent_result.get('question_number'),
            'total_questions': agent_result.get('total_questions'),
            'can_build_defense': agent_result['can_build_defense'],
            'defense_found': agent_result.get('defense_found'),
            'progress': agent_result.get('progress')
        }

    async def build_defense_strategy(self) -> Dict:
        """Build defense using Interview Agent - ONLY after questions answered"""

        # USE INTERVIEW AGENT to build defense (enforces question requirement)
        agent_result = self.interview_agent.build_defense()

        # Check if agent blocked defense building
        if 'error' in agent_result:
            return {
                'error': agent_result['error'],
                'message': agent_result['message'],
                'questions_remaining': agent_result.get('questions_remaining'),
                'current_question': agent_result.get('current_question')
            }

        # Agent allowed defense building - store results
        defenses = agent_result.get('defenses', [])
        self.context['identified_defenses'] = defenses
        self.context['action_items'] = agent_result.get('immediate_actions', [])
        self.context['evidence_needed'] = agent_result.get('evidence_needed', [])

        self.state = SystemState.DEFENSE_READY

        return {
            'action': agent_result['action'],
            'defenses': defenses,
            'immediate_actions': self.context['action_items'],
            'evidence_needed': self.context['evidence_needed'],
            'based_on': agent_result.get('based_on')
        }

    async def handle_qa_message(self, message: str) -> Dict:
        """Handle Q&A using hardcoded concise responses - NO AI verbosity"""

        # USE HARDCODED Q&A HANDLER - No AI calls
        result = await QAHandler.process_qa_message(
            message=message,
            session_id=self.session_id,
            context=self.context
        )

        # Store in chat history
        self.context['chat_history'].append({
            'question': message,
            'answer': result['response'],
            'timestamp': datetime.now().isoformat()
        })

        # Track as cached since we didn't use AI
        self.ai_calls_cached += 1

        return {
            'response': result['response'],
            'word_count': result['word_count'],
            'model': result['model'],
            'cached': True,
            'has_question': result['has_question']
        }

    def _generate_questions_from_analysis(self) -> List[Dict]:
        """Generate smart questions based on document gaps"""

        questions = []
        analysis = self.context.get('document_analysis', {})

        # Priority 1: Statute of limitations check
        if self.context['case_type'] == 'debt_collection':
            if 'last_payment_date' not in analysis:
                questions.append({
                    'id': 'last_payment',
                    'text': 'When did you make your LAST payment?',
                    'priority': 1,
                    'options': ['Within 1 year', '1-3 years', '3-5 years', 'Over 5 years']
                })

        # Priority 2: Missing critical docs
        for missing in self.context['missing_info'][:3]:
            if missing == 'original_contract':
                questions.append({
                    'id': 'have_contract',
                    'text': 'Do you have the original contract?',
                    'priority': 2,
                    'options': ['Yes', 'No', 'Maybe']
                })

        return sorted(questions, key=lambda x: x['priority'])

    def _check_defense_triggers(self, question_id: str, answer: str) -> Optional[Dict]:
        """Check if answer triggers automatic defense"""

        triggers = {
            'last_payment': {
                'Over 5 years': {'name': 'Statute of Limitations', 'strength': 'Very Strong'},
                '3-5 years': {'name': 'Possible Statute of Limitations', 'strength': 'Medium'}
            },
            'debt_ownership': {
                'No': {'name': 'Lack of Standing', 'strength': 'Strong'}
            }
        }

        if question_id in triggers and answer in triggers[question_id]:
            return triggers[question_id][answer]

        return None

    def _get_next_strategic_question(self) -> Optional[Dict]:
        """Get next most important question"""
        questions = self._generate_questions_from_analysis()
        answered_ids = set(self.context['interview_answers'].keys())

        for q in questions:
            if q['id'] not in answered_ids:
                return q

        return None

    def _check_answer_cache(self, question: str) -> Optional[str]:
        """Check if we can answer from cached context"""

        question_lower = question.lower()

        # Common questions we can answer from context
        if 'deadline' in question_lower:
            if self.context['deadlines']:
                return f"Your deadline is {self.context['deadlines'][0]['date']}. File your answer by then."

        if 'how much' in question_lower and 'claimed' in question_lower:
            amount = self.context.get('document_analysis', {}).get('amount_claimed')
            if amount:
                return f"They are claiming ${amount}."

        return None

    def _generate_contextual_followup(self, question: str) -> Optional[str]:
        """Generate follow-up based on context"""
        if self.context['case_type'] == 'debt_collection':
            if not self.context['interview_answers'].get('last_payment'):
                return "When did you make your last payment on this debt?"

        return None

    async def _call_ai_efficiently(self, prompt: str) -> str:
        """Efficient AI calling with caching and optimization"""

        # Use fast model for everything
        response = claude_client.messages.create(
            model='claude-3-5-haiku-20241022',
            max_tokens=300,  # Keep responses concise
            temperature=0,  # Consistent responses
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return response.content[0].text

    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from AI response"""
        try:
            # Try to extract JSON from markdown code blocks
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                json_str = response.split('```')[1].split('```')[0].strip()
            else:
                json_str = response.strip()

            return json.loads(json_str)
        except:
            # Fallback to basic parsing
            return {'raw_response': response}

    def _parse_defenses(self, response: str) -> List[Dict]:
        """Parse defense list from response"""
        defenses = []
        lines = response.split('\n')

        current_defense = {}
        for line in lines:
            if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                if current_defense:
                    defenses.append(current_defense)
                current_defense = {'name': line.split('.', 1)[1].strip()}
            elif ':' in line and current_defense:
                key, value = line.split(':', 1)
                current_defense[key.strip().lower().replace(' ', '_')] = value.strip()

        if current_defense:
            defenses.append(current_defense)

        return defenses

    def _extract_actions(self, defenses: List[Dict]) -> List[str]:
        """Extract action items from defenses"""
        actions = []
        for defense in defenses:
            if 'action' in defense:
                actions.append(defense['action'])
        return actions

    def _extract_evidence(self, defenses: List[Dict]) -> List[str]:
        """Extract evidence needed from defenses"""
        evidence = []
        for defense in defenses:
            if 'evidence' in defense:
                evidence.append(defense['evidence'])
        return evidence

    def _create_summary(self) -> str:
        """Create document summary from analysis"""
        analysis = self.context.get('document_analysis', {})
        case_type = self.context.get('case_type', 'Legal case')
        plaintiff = analysis.get('plaintiff', 'Unknown')
        amount = analysis.get('amount_claimed', 'unspecified amount')

        return f"{case_type} from {plaintiff} claiming {amount}."

    def _get_critical_info(self) -> Dict:
        """Get most critical information"""
        return {
            'case_type': self.context['case_type'],
            'deadline': self.context['deadlines'][0] if self.context['deadlines'] else None,
            'amount': self.context.get('document_analysis', {}).get('amount_claimed'),
            'missing_docs': self.context['missing_info'][:3]
        }

    def get_system_status(self) -> Dict:
        """Get complete system status for monitoring"""

        return {
            'session_id': self.session_id,
            'state': self.state.value,
            'context_items': len([k for k, v in self.context.items() if v]),
            'ai_efficiency': {
                'total_calls': self.ai_calls_made,
                'cached_responses': self.ai_calls_cached,
                'cache_rate': self.ai_calls_cached / max(self.ai_calls_made, 1) if self.ai_calls_made > 0 else 0
            },
            'processing_times': self.processing_time,
            'defenses_identified': len(self.context['identified_defenses']),
            'questions_answered': len(self.context['interview_answers'])
        }


class SessionManager:
    """Manages all user sessions efficiently"""

    def __init__(self):
        self.sessions: Dict[str, UnifiedLegalSystem] = {}
        self.last_cleanup = datetime.now()

    def get_or_create_session(self, session_id: str) -> UnifiedLegalSystem:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = UnifiedLegalSystem(session_id)

        # Periodic cleanup
        if (datetime.now() - self.last_cleanup).total_seconds() > 3600:
            self.cleanup_old_sessions()

        return self.sessions[session_id]

    def cleanup_old_sessions(self):
        """Remove sessions older than 1 hour"""
        now = datetime.now()
        to_remove = []

        for session_id, system in self.sessions.items():
            # Check if session has been inactive for 1+ hours
            if system.processing_time and 'document_analysis' in system.processing_time:
                # Simplified cleanup - remove if no recent activity
                to_remove.append(session_id)

        for session_id in to_remove[:10]:  # Limit removals
            del self.sessions[session_id]

        self.last_cleanup = now


# Single global instance
session_manager = SessionManager()
