"""
Interview AI Agent
FORCES users to answer questions before defense building
Ensures we have complete information for best defense strategy
NOW POWERED BY REAL AI - Uses SmartClaudeClient for intelligent question generation
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import json
import re
import asyncio
import logging

# Import AI client for real AI-powered interviews
try:
    from ..shared.ai.claude_client import smart_claude_client
    AI_ENABLED = True
except ImportError:
    AI_ENABLED = False
    logging.warning("SmartClaudeClient not available - using fallback questions")

logger = logging.getLogger(__name__)


class AgentState(Enum):
    WAITING_FOR_DOCUMENT = 'waiting_for_document'
    ASKING_QUESTIONS = 'asking_questions'
    READY_FOR_DEFENSE = 'ready_for_defense'
    BUILDING_DEFENSE = 'building_defense'
    COMPLETE = 'complete'


class InterviewAgent:
    """AI Agent that MUST ask questions before building defense"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = AgentState.WAITING_FOR_DOCUMENT
        self.current_question_index = 0
        self.max_questions = 5

        # Document context
        self.document_text = None
        self.document_type = None
        self.document_facts = {}

        # Question management
        self.questions_queue = []
        self.answers_collected = {}

        # Defense building blocked until questions answered
        self.can_build_defense = False

    def process_document(self, document_text: str) -> Dict:
        """Process document and START interview immediately - NOW WITH AI!"""

        self.document_text = document_text
        self.state = AgentState.ASKING_QUESTIONS

        # Try AI-powered analysis first
        if AI_ENABLED:
            try:
                logger.info("🤖 Using Claude AI for document analysis...")
                analysis_result = asyncio.run(self._ai_analyze_document(document_text))
                self.document_facts = analysis_result.get('facts', {})
                self.questions_queue = analysis_result.get('questions', [])

                logger.info(f"✅ AI generated {len(self.questions_queue)} strategic questions")
            except Exception as e:
                logger.error(f"AI analysis failed, using fallback: {e}")
                # Fallback to rule-based approach
                self.document_facts = self._extract_document_facts(document_text)
                self.questions_queue = self._generate_smart_questions()
        else:
            # Fallback to rule-based approach
            self.document_facts = self._extract_document_facts(document_text)
            self.questions_queue = self._generate_smart_questions()

        # FORCE first question
        first_question = self.questions_queue[0] if self.questions_queue else None
        self.current_question_index = 0

        return {
            'action': 'START_INTERVIEW',
            'document_summary': self._summarize_document(),
            'current_question': first_question,
            'question_number': 1,
            'total_questions': len(self.questions_queue),
            'can_build_defense': False,  # BLOCKED
            'message': 'I need to ask you some questions before building your defense.'
        }

    async def _ai_analyze_document(self, document_text: str) -> Dict:
        """Use Claude AI to analyze document and generate intelligent questions"""
        try:
            # Use Claude to analyze the document
            analysis_response = await smart_claude_client.analyze_document(
                document=document_text,
                task_type='legal_interview',
                min_confidence=0.7
            )

            # Extract analysis
            analysis_text = analysis_response.get('analysis', '')

            # Generate AI-powered questions
            question_prompt = f"""Based on this legal document, generate 5 strategic interview questions to gather information for building a defense.

Document Analysis: {analysis_text[:1000]}

Generate questions in this exact JSON format:
[
  {{
    "id": "question_id",
    "text": "The question to ask",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "critical": true,
    "priority": 1
  }}
]

Focus on:
1. Statute of limitations (last payment/contact dates)
2. Standing (who owns the debt/claim)
3. Amount accuracy
4. Available defenses
5. Evidence defendant has

Return ONLY the JSON array, no other text."""

            question_response = await smart_claude_client.analyze_document(
                document=question_prompt,
                task_type='question_generation',
                min_confidence=0.7
            )

            # Parse questions from AI response
            questions_text = question_response.get('analysis', '[]')

            # Extract JSON from response
            try:
                # Look for JSON array in the response
                if '[' in questions_text:
                    json_start = questions_text.find('[')
                    json_end = questions_text.rfind(']') + 1
                    questions_json = questions_text[json_start:json_end]
                    questions = json.loads(questions_json)
                else:
                    logger.warning("No JSON array found in AI response, using fallback")
                    questions = []
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI questions: {questions_text}")
                questions = []

            # Extract facts from analysis
            facts = {
                'case_type': self._detect_case_type(document_text),
                'ai_analysis': analysis_text[:500],
                'confidence': analysis_response.get('confidence', 0.7)
            }

            return {
                'facts': facts,
                'questions': questions if questions else self._generate_smart_questions()
            }

        except Exception as e:
            logger.error(f"AI document analysis error: {e}")
            raise

    def _detect_case_type(self, text: str) -> str:
        """Detect case type from document text"""
        text_lower = text.lower()
        if 'debt' in text_lower or 'collection' in text_lower:
            return 'debt_collection'
        elif 'evict' in text_lower:
            return 'eviction'
        elif 'foreclosure' in text_lower:
            return 'foreclosure'
        else:
            return 'general'

    def _extract_document_facts(self, text: str) -> Dict:
        """Extract facts we know from document"""

        facts = {}
        text_lower = text.lower()

        # Detect case type
        if 'debt' in text_lower or 'owe' in text_lower or 'collection' in text_lower:
            facts['case_type'] = 'debt_collection'
        elif 'evict' in text_lower or 'landlord' in text_lower or 'tenant' in text_lower:
            facts['case_type'] = 'eviction'
        elif 'bankruptcy' in text_lower or 'chapter' in text_lower:
            facts['case_type'] = 'bankruptcy'
        elif 'foreclosure' in text_lower or 'mortgage' in text_lower:
            facts['case_type'] = 'foreclosure'
        else:
            facts['case_type'] = 'general'

        # Extract amounts (simple regex)
        amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', text)
        if amounts:
            facts['amount'] = amounts[0]

        # Extract dates
        dates = re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}', text)
        if dates:
            facts['dates'] = dates

        # Check what's missing
        facts['missing'] = []
        if 'contract' not in text_lower and 'agreement' not in text_lower:
            facts['missing'].append('original_contract')
        if 'last payment' not in text_lower:
            facts['missing'].append('last_payment_date')
        if 'assignment' not in text_lower and facts['case_type'] == 'debt_collection':
            facts['missing'].append('proof_of_ownership')

        return facts

    def _generate_smart_questions(self) -> List[Dict]:
        """Generate questions based on case type and missing info"""

        questions = []
        case_type = self.document_facts.get('case_type', 'general')

        if case_type == 'debt_collection':
            # CRITICAL questions for debt cases
            questions = [
                {
                    'id': 'last_payment',
                    'text': 'When did you make your LAST payment on this debt?',
                    'options': ['Within 1 year', '1-3 years ago', '3-5 years ago', 'Over 5 years ago', 'Never'],
                    'critical': True,
                    'priority': 1
                },
                {
                    'id': 'original_creditor',
                    'text': 'Is the company suing you the original creditor or did they buy the debt?',
                    'options': ['Original creditor', 'Debt buyer', 'Not sure'],
                    'critical': True,
                    'priority': 1
                },
                {
                    'id': 'amount_correct',
                    'text': f'They claim {self.document_facts.get("amount", "an amount")}. Is this correct?',
                    'options': ['Yes', 'Too high', 'Already paid', "Don't recognize"],
                    'critical': False,
                    'priority': 2
                },
                {
                    'id': 'attempted_payment',
                    'text': 'Have you tried to pay or settle this debt?',
                    'options': ['Yes', 'No', 'They refused payment'],
                    'critical': False,
                    'priority': 3
                },
                {
                    'id': 'have_records',
                    'text': 'Do you have payment records or the original agreement?',
                    'options': ['Yes', 'Some records', 'No records'],
                    'critical': False,
                    'priority': 3
                }
            ]

        elif case_type == 'eviction':
            questions = [
                {
                    'id': 'rent_current',
                    'text': 'Are you current on rent?',
                    'options': ['Yes', 'No', 'Partial payments', 'Landlord refused'],
                    'critical': True,
                    'priority': 1
                },
                {
                    'id': 'repair_issues',
                    'text': 'Are there serious repair issues with the property?',
                    'options': ['Yes - major', 'Yes - minor', 'No'],
                    'critical': True,
                    'priority': 1
                },
                {
                    'id': 'proper_notice',
                    'text': 'Did you receive proper 30-day notice?',
                    'options': ['Yes', 'No', 'Less than 30 days', 'No notice'],
                    'critical': True,
                    'priority': 1
                },
                {
                    'id': 'repair_requests',
                    'text': 'Did you request repairs in writing?',
                    'options': ['Yes - have proof', 'Yes - no proof', 'No'],
                    'critical': False,
                    'priority': 2
                }
            ]

        elif case_type == 'foreclosure':
            questions = [
                {
                    'id': 'loan_modification',
                    'text': 'Did you apply for loan modification?',
                    'options': ['Yes - approved', 'Yes - denied', 'Yes - pending', 'No'],
                    'critical': True,
                    'priority': 1
                },
                {
                    'id': 'last_mortgage_payment',
                    'text': 'When was your last mortgage payment?',
                    'options': ['This month', '1-3 months ago', '3-6 months ago', 'Over 6 months'],
                    'critical': True,
                    'priority': 1
                }
            ]

        else:
            # Generic questions
            questions = [
                {
                    'id': 'when_started',
                    'text': 'When did this legal issue start?',
                    'options': ['This month', '1-6 months ago', '6-12 months ago', 'Over 1 year ago'],
                    'critical': True,
                    'priority': 1
                },
                {
                    'id': 'attempted_resolution',
                    'text': 'Have you tried to resolve this issue?',
                    'options': ['Yes', 'No', 'Other party refused'],
                    'critical': False,
                    'priority': 2
                },
                {
                    'id': 'have_documentation',
                    'text': 'Do you have documentation of this matter?',
                    'options': ['Yes', 'Some', 'No'],
                    'critical': False,
                    'priority': 3
                }
            ]

        return questions[:self.max_questions]  # Limit to max questions

    def answer_question(self, answer: str) -> Dict:
        """Process answer and move to next question or defense"""

        if self.state != AgentState.ASKING_QUESTIONS:
            return {
                'error': 'Not in questioning state',
                'current_state': self.state.value
            }

        # Store answer
        current_q = self.questions_queue[self.current_question_index]
        self.answers_collected[current_q['id']] = answer

        # Check if this answer triggers immediate defense
        defense_trigger = self._check_defense_trigger(current_q['id'], answer)

        # Move to next question
        self.current_question_index += 1

        if self.current_question_index < len(self.questions_queue):
            # More questions to ask
            next_question = self.questions_queue[self.current_question_index]

            response = {
                'action': 'NEXT_QUESTION',
                'current_question': next_question,
                'question_number': self.current_question_index + 1,
                'total_questions': len(self.questions_queue),
                'can_build_defense': False,  # Still blocked
                'answers_so_far': len(self.answers_collected),
                'progress': (self.current_question_index / len(self.questions_queue)) * 100
            }

            if defense_trigger:
                response['defense_found'] = defense_trigger
                response['message'] = f'Good news! You have a {defense_trigger} defense.'

            return response
        else:
            # All questions answered - UNLOCK defense building
            self.state = AgentState.READY_FOR_DEFENSE
            self.can_build_defense = True

            return {
                'action': 'INTERVIEW_COMPLETE',
                'can_build_defense': True,  # NOW UNLOCKED
                'message': 'Interview complete. Now I can build your defense strategy.',
                'answers_collected': len(self.answers_collected),
                'ready_to_build': True
            }

    def _check_defense_trigger(self, question_id: str, answer: str) -> Optional[str]:
        """Check if answer reveals strong defense"""

        triggers = {
            'last_payment': {
                'Over 5 years ago': 'Statute of Limitations',
                '3-5 years ago': 'Possible Statute of Limitations'
            },
            'original_creditor': {
                'Debt buyer': 'Lack of Standing',
                'Not sure': 'Possible Lack of Standing'
            },
            'amount_correct': {
                'Too high': 'Incorrect Amount',
                'Already paid': 'Payment Defense',
                "Don't recognize": 'Identity/Fraud Defense'
            },
            'repair_issues': {
                'Yes - major': 'Habitability Defense'
            },
            'proper_notice': {
                'No': 'Improper Notice',
                'Less than 30 days': 'Improper Notice',
                'No notice': 'Improper Notice'
            },
            'loan_modification': {
                'Yes - pending': 'Dual Tracking Violation'
            }
        }

        if question_id in triggers and answer in triggers[question_id]:
            return triggers[question_id][answer]

        return None

    def build_defense(self) -> Dict:
        """Build defense ONLY after questions answered - NOW WITH AI!"""

        if not self.can_build_defense:
            return {
                'error': 'Cannot build defense yet',
                'message': 'Please answer all interview questions first',
                'questions_remaining': len(self.questions_queue) - self.current_question_index,
                'current_question': self.questions_queue[self.current_question_index] if self.current_question_index < len(self.questions_queue) else None
            }

        self.state = AgentState.BUILDING_DEFENSE

        # Try AI-powered defense building
        if AI_ENABLED:
            try:
                logger.info("🤖 Using Claude AI to build defense strategy...")
                defense_result = asyncio.run(self._ai_build_defense())
                defenses = defense_result.get('defenses', [])
                logger.info(f"✅ AI generated {len(defenses)} defense strategies")
            except Exception as e:
                logger.error(f"AI defense building failed, using fallback: {e}")
                defenses = self._generate_defenses()
        else:
            # Fallback to rule-based defenses
            defenses = self._generate_defenses()

        self.state = AgentState.COMPLETE

        return {
            'action': 'DEFENSE_READY',
            'defenses': defenses,
            'immediate_actions': self._get_immediate_actions(),
            'evidence_needed': self._get_evidence_needed(),
            'based_on': {
                'document_facts': len(self.document_facts),
                'interview_answers': len(self.answers_collected)
            }
        }

    async def _ai_build_defense(self) -> Dict:
        """Use Claude AI to build comprehensive defense strategy with DETAILED reasoning"""
        try:
            # Prepare context for AI
            context = f"""
LEGAL DOCUMENT:
{self.document_text[:2000]}...

CASE TYPE: {self.document_facts.get('case_type', 'general')}

INTERVIEW ANSWERS:
{json.dumps(self.answers_collected, indent=2)}

Based on this information, generate a comprehensive defense strategy with HIGHLY DETAILED, specific, actionable defenses.

Return in this EXACT JSON format with ALL fields filled:
[
  {{
    "name": "Defense Name",
    "description": "One sentence description",
    "strength": 85,
    "strength_level": "STRONG",
    "why_recommended": "DETAILED explanation (3-5 sentences) citing specific facts from the document, missing documents, and interview answers that justify this defense. MUST reference actual document content and interview responses.",
    "document_evidence": {{
      "plaintiff_claims": "What the plaintiff specifically claimed in the document",
      "missing_from_complaint": ["List of items missing from the complaint that weaken their case"],
      "defendant_answers_support": "How the defendant's interview answers support this defense",
      "specific_facts": ["Specific dates, amounts, or facts from document/interview"]
    }},
    "detailed_explanation": "Comprehensive legal explanation with reasoning (2-3 sentences)",
    "how_to_assert": "Exact steps to assert this defense in your Answer:\\n1. Step one\\n2. Step two\\n3. Step three",
    "winning_scenarios": ["Scenario 1 where this defense wins", "Scenario 2"],
    "risks_to_avoid": ["Risk 1 to watch out for", "Risk 2"],
    "evidence_needed": ["Evidence item 1", "Evidence item 2"]
  }}
]

CRITICAL REQUIREMENTS:
1. Generate 3-5 defenses total
2. Each defense MUST have a detailed "why_recommended" section citing specific facts
3. Each defense MUST have complete "document_evidence" with all 4 sub-fields
4. Strength should be 65-95 (number, not string)
5. strength_level should be "STRONG", "MODERATE", or "WEAK"
6. Focus on: Statute of limitations, Standing/ownership, Amount disputes, Procedural defenses, Evidence gaps

EXAMPLE why_recommended:
"This defense is recommended because the complaint states the debt is from 2017, but the defendant's interview revealed the last payment was over 5 years ago, which exceeds most states' statute of limitations for debt collection (typically 3-6 years). Additionally, the complaint is missing proof of when the cause of action accrued, and lacks documentation of the original account agreement showing when payments were due."

Return ONLY the JSON array, no other text."""

            # Use Claude for defense strategy
            response = await smart_claude_client.analyze_document(
                document=context,
                task_type='defense_strategy',
                min_confidence=0.8
            )

            defenses_text = response.get('analysis', '[]')

            # Parse defense strategies
            try:
                if '[' in defenses_text:
                    json_start = defenses_text.find('[')
                    json_end = defenses_text.rfind(']') + 1
                    defenses_json = defenses_text[json_start:json_end]
                    defenses = json.loads(defenses_json)

                    # Validate defenses have required detail
                    for defense in defenses:
                        if not defense.get('why_recommended') or len(defense.get('why_recommended', '')) < 100:
                            logger.warning(f"Defense '{defense.get('name')}' has insufficient detail, using fallback")
                            return {'defenses': self._generate_detailed_defenses()}
                else:
                    logger.warning("No JSON array found in AI defense response")
                    defenses = []
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI defenses: {defenses_text}")
                defenses = []

            return {
                'defenses': defenses if defenses else self._generate_detailed_defenses()
            }

        except Exception as e:
            logger.error(f"AI defense building error: {e}")
            raise

    def _generate_detailed_defenses(self) -> List[Dict]:
        """Generate DETAILED defenses with comprehensive reasoning - ENHANCED version"""

        defenses = []
        case_type = self.document_facts.get('case_type', 'general')

        # Check for statute of limitations
        last_payment = self.answers_collected.get('last_payment', '')
        if 'Over 5 years ago' in last_payment or '3-5 years ago' in last_payment:
            is_strong = 'Over 5 years' in last_payment
            defenses.append({
                'name': 'Statute of Limitations Defense',
                'description': 'The debt is beyond the legal time limit for collection',
                'strength': 90 if is_strong else 75,
                'strength_level': 'STRONG' if is_strong else 'MODERATE',
                'why_recommended': f"This defense is recommended because you indicated your last payment was {last_payment}. Most states have a statute of limitations of 3-6 years for debt collection. The complaint does not specify when the cause of action accrued, and based on your interview response, this debt appears to be time-barred. Courts must dismiss claims filed after the statute of limitations has expired.",
                'document_evidence': {
                    'plaintiff_claims': self.document_facts.get('amount', 'debt owed'),
                    'missing_from_complaint': ['Date when cause of action accrued', 'Proof of tolling or revival of statute', 'Account statement showing last activity'],
                    'defendant_answers_support': f"Defendant stated last payment was {last_payment}, which likely exceeds the applicable statute of limitations",
                    'specific_facts': [f'Last payment: {last_payment}', f'Case type: {case_type}', 'No tolling agreements mentioned']
                },
                'detailed_explanation': 'The statute of limitations is an affirmative defense that bars claims filed after a specific time period. For debt collection, this is typically 3-6 years depending on the state and type of debt. Once expired, the creditor loses the legal right to sue for the debt.',
                'how_to_assert': 'In your Answer to the Complaint:\n1. Include as an affirmative defense: "The claim is barred by the applicable statute of limitations"\n2. State the date of last payment or account activity\n3. Request dismissal with prejudice\n4. Attach any evidence of the last payment date if available',
                'winning_scenarios': [
                    'If you can prove last payment was beyond the statute period, case dismissed',
                    'If plaintiff cannot prove the debt is within the limitation period',
                    'If court finds no tolling or revival of the statute occurred'
                ],
                'risks_to_avoid': [
                    'Do NOT make any new payment - this could restart the statute of limitations',
                    'Do NOT acknowledge the debt in writing',
                    'Assert this defense immediately in your Answer - it can be waived if not timely raised'
                ],
                'evidence_needed': ['Bank statements showing last payment date', 'Account records or correspondence showing account activity dates']
            })

        # Check for standing issues
        if self.answers_collected.get('original_creditor') in ['Debt buyer', 'Not sure']:
            defenses.append({
                'name': 'Lack of Standing',
                'description': 'Plaintiff may not have legal right to sue for this debt',
                'strength': 85,
                'strength_level': 'STRONG',
                'why_recommended': f"You indicated the company suing is {self.answers_collected.get('original_creditor', 'possibly a debt buyer')}. Debt buyers must prove they have standing to sue by showing complete chain of ownership. The complaint is missing proof of assignment, which is required to establish the plaintiff's legal right to collect. Without proper documentation of ownership transfer, the plaintiff lacks standing to pursue this claim.",
                'document_evidence': {
                    'plaintiff_claims': 'Claims to be owner/assignee of the debt',
                    'missing_from_complaint': ['Assignment agreement', 'Bill of sale transferring the debt', 'Proof of consideration paid', 'Complete chain of title if multiple transfers'],
                    'defendant_answers_support': f"Defendant indicated plaintiff is {self.answers_collected.get('original_creditor')}, raising questions about ownership",
                    'specific_facts': ['No assignment documentation attached', 'Plaintiff identity differs from original creditor', 'No proof of valid assignment']
                },
                'detailed_explanation': 'Standing requires the plaintiff to prove they are the real party in interest with the legal right to enforce the claim. Debt buyers must provide evidence of valid assignment, including the assignment agreement and proof that consideration was paid. Missing or defective assignment documentation defeats standing.',
                'how_to_assert': 'In your Answer:\n1. Deny that plaintiff has standing to sue\n2. Deny that plaintiff owns the debt\n3. Demand plaintiff prove valid assignment\n4. Request discovery: demand production of assignment agreements and chain of title\n5. File Motion to Dismiss for Lack of Standing if proof not provided',
                'winning_scenarios': [
                    'Plaintiff cannot produce valid assignment documentation',
                    'Assignment agreement is defective (no consideration, improper execution)',
                    'Chain of title is broken with missing assignments',
                    'Plaintiff fails to respond to discovery requests for assignment proof'
                ],
                'risks_to_avoid': [
                    'Do not admit plaintiff owns the debt',
                    'Challenge standing early - file Motion to Dismiss if no proof provided with complaint',
                    'Demand all ownership documents in discovery immediately'
                ],
                'evidence_needed': ['Any correspondence from original creditor', 'Account statements showing original creditor name', 'Credit report showing account ownership history']
            })

        # Amount dispute defense
        if self.answers_collected.get('amount_correct') in ['Too high', 'Already paid', "Don't recognize"]:
            defenses.append({
                'name': 'Incorrect Amount / Account Stated',
                'description': 'The amount claimed is disputed and not proven',
                'strength': 70,
                'strength_level': 'MODERATE',
                'why_recommended': f"You indicated the amount is {self.answers_collected.get('amount_correct')}. The plaintiff has the burden of proving the amount owed with documentary evidence. The complaint lacks an itemized accounting showing how the amount was calculated, what charges were added, and proof that you agreed to these charges. Without detailed documentation, the plaintiff cannot meet their burden of proof.",
                'document_evidence': {
                    'plaintiff_claims': f"Claims amount of {self.document_facts.get('amount', 'unspecified')}",
                    'missing_from_complaint': ['Itemized account statement', 'Original contract showing interest rate and fees', 'Accounting of payments received', 'Proof of valid charges'],
                    'defendant_answers_support': f"Defendant disputes the amount as {self.answers_collected.get('amount_correct')}",
                    'specific_facts': [f'Claimed amount: {self.document_facts.get("amount", "not specified")}', 'No itemized statement provided', 'No payment history shown']
                },
                'detailed_explanation': 'Plaintiff must prove the amount owed through documentary evidence including the original agreement, account statements, and itemized charges. Burden of proof requires showing principal, interest calculation, fees charged, and credits for payments made.',
                'how_to_assert': 'In your Answer:\n1. Deny the amount alleged\n2. Demand strict proof of the amount claimed\n3. Request itemized accounting in discovery\n4. Challenge any interest or fees not authorized by original agreement',
                'winning_scenarios': [
                    'Plaintiff cannot provide itemized statement',
                    'Interest or fees exceed what was authorized',
                    'Payments were not properly credited',
                    'Original agreement shows different terms'
                ],
                'risks_to_avoid': [
                    'Do not make partial payment without written settlement agreement',
                    'Demand complete accounting before considering any settlement'
                ],
                'evidence_needed': ['Your payment records', 'Original contract/agreement', 'Account statements you received', 'Correspondence about the account']
            })

        # Always add procedural defenses
        if len(defenses) < 3:
            defenses.append({
                'name': 'Failure to State a Claim',
                'description': 'Complaint may be deficient in required elements',
                'strength': 65,
                'strength_level': 'MODERATE',
                'why_recommended': 'The complaint fails to provide sufficient detail to establish a valid claim. It lacks essential elements such as when the cause of action accrued, the terms of the original agreement, and proof of breach. Federal and state rules require complaints to contain sufficient facts to state a plausible claim for relief.',
                'document_evidence': {
                    'plaintiff_claims': 'General allegations of debt owed',
                    'missing_from_complaint': ['Contract terms', 'Breach specifics', 'Date of breach', 'Damages calculation'],
                    'defendant_answers_support': 'Lack of detail prevents proper defense',
                    'specific_facts': ['No contract attached', 'No specific breach alleged', 'Vague allegations']
                },
                'detailed_explanation': 'Under notice pleading standards, complaints must provide fair notice of the claim and sufficient facts for the defendant to prepare a defense. A complaint that fails to specify essential elements or contains only conclusory allegations may be dismissed.',
                'how_to_assert': 'File Motion to Dismiss under Rule 12(b)(6) or state equivalent:\n1. Identify specific deficiencies in the complaint\n2. Argue plaintiff has not stated a claim upon which relief can be granted\n3. Request dismissal or order requiring more definite statement',
                'winning_scenarios': [
                    'Court finds complaint too vague or conclusory',
                    'Essential elements of claim are not alleged',
                    'Plaintiff fails to cure deficiencies after motion granted'
                ],
                'risks_to_avoid': [
                    'File motion early - before answering if possible',
                    'Be specific about what is deficient'
                ],
                'evidence_needed': ['Copy of the complaint to analyze for deficiencies']
            })

        return defenses[:5]  # Return top 5 detailed defenses

    def _generate_defenses(self) -> List[Dict]:
        """Basic defenses - fallback to detailed version"""
        return self._generate_detailed_defenses()

    def _summarize_document(self) -> str:
        """Brief document summary"""
        case_type = self.document_facts.get('case_type', 'legal')
        amount = self.document_facts.get('amount', 'unspecified amount')
        return f'{case_type.replace("_", " ").title()} case for {amount}.'

    def _get_immediate_actions(self) -> List[str]:
        """Get immediate action items"""
        actions = [
            'File your answer within deadline (typically 20-30 days)',
            'Request all documents from plaintiff via discovery',
            'Gather your payment records and documentation',
            'Do NOT ignore this lawsuit - respond by the deadline'
        ]

        # Add case-specific actions
        if self.document_facts.get('case_type') == 'debt_collection':
            actions.append('Send debt validation letter within 30 days if recent')

        if self.document_facts.get('case_type') == 'eviction':
            actions.append('Document all property conditions with photos')

        return actions

    def _get_evidence_needed(self) -> List[str]:
        """Get evidence needed"""
        evidence = [
            'Original contract or agreement',
            'Payment history and receipts',
            'All correspondence with other party',
            'Bank statements showing payments'
        ]

        # Add case-specific evidence
        if self.answers_collected.get('repair_issues') in ['Yes - major', 'Yes - minor']:
            evidence.append('Photos of repair issues')
            evidence.append('Written repair requests')

        if self.answers_collected.get('have_records') == 'Yes':
            evidence.append('Organize all records chronologically')

        return evidence

    def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            'state': self.state.value,
            'questions_asked': self.current_question_index,
            'total_questions': len(self.questions_queue),
            'answers_collected': len(self.answers_collected),
            'can_build_defense': self.can_build_defense,
            'document_loaded': self.document_text is not None,
            'case_type': self.document_facts.get('case_type'),
            'progress_percentage': (self.current_question_index / max(len(self.questions_queue), 1)) * 100
        }


# Global agent manager
interview_agents: Dict[str, InterviewAgent] = {}


def get_or_create_agent(session_id: str) -> InterviewAgent:
    """Get existing agent or create new one"""
    if session_id not in interview_agents:
        interview_agents[session_id] = InterviewAgent(session_id)
    return interview_agents[session_id]
