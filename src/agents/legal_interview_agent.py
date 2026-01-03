import json
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta

class AgentBrain:
    '''The intelligent brain of the legal agent'''

    def __init__(self):
        self.memory = {}  # Remember everything
        self.insights = []  # Track discoveries
        self.red_flags = []  # Track problems
        self.opportunities = []  # Track defenses
        self.strategy = {}  # Build strategy as we go

class LegalInterviewAgent:
    '''A TRUE AI Agent that conducts intelligent legal interviews'''

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.brain = AgentBrain()
        self.conversation_state = 'initial'
        self.question_count = 0
        self.max_questions = 10  # More thorough

        # Document understanding
        self.document_type = None
        self.plaintiff_type = None  # original_creditor, debt_buyer, landlord, etc
        self.critical_dates = {}
        self.amounts = {}
        self.claims = []
        self.missing_documents = []

        # Interview intelligence
        self.question_tree = {}
        self.asked_questions = []
        self.follow_up_needed = []
        self.defense_strength = {}

    async def analyze_document_deeply(self, document_text: str) -> Dict:
        '''DEEP analysis of document with AI intelligence'''

        # Extract EVERYTHING from document
        analysis_prompt = f'''You are a legal expert. Analyze this document THOROUGHLY.

        Extract and identify:
        1. Case type (be specific: debt_collection, eviction_nonpayment, eviction_breach, etc)
        2. Plaintiff details:
           - Name
           - Type (original_creditor, debt_buyer, collection_agency, landlord, etc)
           - Attorney representing them
        3. All dates mentioned:
           - Filing date
           - Service date
           - Response deadline
           - Date of alleged debt/incident
           - Any other dates
        4. All amounts:
           - Principal amount
           - Interest
           - Fees
           - Attorney costs
           - Total claimed
        5. Specific claims/causes of action
        6. Documents attached (list what's included)
        7. Documents NOT attached (what's missing that should be there)
        8. Legal violations visible (improper service, wrong venue, etc)
        9. Red flags that help defense
        10. Strengths of plaintiff's case

        Document: {document_text[:10000]}

        Return detailed JSON analysis.'''

        # Call AI for deep analysis
        analysis = await self.call_ai_for_analysis(analysis_prompt)

        # Store in brain
        self.brain.memory['document_analysis'] = analysis

        # Identify critical gaps
        self._identify_critical_gaps(analysis)

        # Build question strategy
        self._build_question_strategy(analysis)

        return analysis

    def _identify_critical_gaps(self, analysis: Dict):
        '''Identify what's missing that we need to know'''

        gaps = []

        # For debt collection cases
        if 'debt' in str(analysis.get('case_type', '')).lower():
            # Critical missing info
            if not analysis.get('last_payment_date'):
                gaps.append({
                    'gap': 'last_payment_date',
                    'importance': 'CRITICAL',
                    'reason': 'Determines statute of limitations defense'
                })

            if not analysis.get('original_creditor'):
                gaps.append({
                    'gap': 'original_creditor',
                    'importance': 'HIGH',
                    'reason': 'Need to verify chain of ownership'
                })

            if not analysis.get('original_contract_attached'):
                self.brain.opportunities.append('No contract attached - strong standing defense')
                gaps.append({
                    'gap': 'contract_existence',
                    'importance': 'HIGH',
                    'reason': 'They may not have proof'
                })

            if analysis.get('amount_breakdown'):
                # Check for suspicious fees
                fees = analysis['amount_breakdown'].get('fees', 0)
                principal = analysis['amount_breakdown'].get('principal', 1)
                if fees > principal * 0.5:
                    self.brain.red_flags.append('Excessive fees - possible usury or violation')

        # For eviction cases
        elif 'evict' in str(analysis.get('case_type', '')).lower():
            if not analysis.get('notice_date'):
                gaps.append({
                    'gap': 'proper_notice',
                    'importance': 'CRITICAL',
                    'reason': 'Improper notice is complete defense'
                })

            if not analysis.get('lease_attached'):
                self.brain.opportunities.append('No lease attached - may not prove terms')

        self.brain.memory['critical_gaps'] = gaps

    def _build_question_strategy(self, analysis: Dict):
        '''Build intelligent question tree based on document'''

        case_type = analysis.get('case_type', '')

        if 'debt_collection' in case_type:
            self.question_tree = self._build_debt_question_tree(analysis)
        elif 'eviction' in case_type:
            self.question_tree = self._build_eviction_question_tree(analysis)
        else:
            self.question_tree = self._build_general_question_tree(analysis)

    def _build_debt_question_tree(self, analysis: Dict) -> Dict:
        '''Sophisticated question tree for debt cases'''

        tree = {
            'tier_1_critical': [
                {
                    'id': 'last_payment',
                    'question': 'This is crucial for your defense: When did you make your LAST payment on this account?',
                    'options': [
                        'Within the last year',
                        '1-2 years ago',
                        '2-4 years ago',
                        '4-6 years ago',
                        'Over 6 years ago',
                        'Never made any payments'
                    ],
                    'follow_ups': {
                        'Over 6 years ago': 'Do you have proof of when you last paid (bank statements, cancelled checks)?',
                        '4-6 years ago': 'Did you ever acknowledge this debt in writing after that last payment?',
                        'Never made any payments': 'Did you ever agree to pay this debt or sign anything?'
                    },
                    'defense_impact': {
                        'Over 6 years ago': 'STRONG statute of limitations defense',
                        '4-6 years ago': 'Possible statute of limitations depending on state',
                        'Never made any payments': 'May dispute validity entirely'
                    }
                },
                {
                    'id': 'debt_recognition',
                    'question': f'The plaintiff {analysis.get("plaintiff_name", "company")} claims you owe ${analysis.get("amount_claimed", "this amount")}. Do you recognize this debt?',
                    'options': [
                        'Yes, I had an account with them',
                        'Yes, but not with this company',
                        'The amount is wrong',
                        'I don\'t recognize this at all',
                        'This was already paid/settled',
                        'This is identity theft/fraud'
                    ],
                    'follow_ups': {
                        'Yes, but not with this company': 'Who was the original creditor?',
                        'The amount is wrong': 'What should the correct amount be?',
                        'This was already paid/settled': 'Do you have proof of payment or settlement?',
                        'This is identity theft/fraud': 'Have you filed a police report or identity theft affidavit?'
                    }
                }
            ],
            'tier_2_important': [
                {
                    'id': 'payment_history',
                    'question': 'Do you have any records of payments you made on this account?',
                    'options': [
                        'Yes, I have bank statements',
                        'Yes, I have cancelled checks',
                        'Yes, I have receipts',
                        'Some records but not all',
                        'No records'
                    ],
                    'defense_impact': {
                        'Yes, I have bank statements': 'Can prove payments and last payment date',
                        'No records': 'Will need to request from plaintiff'
                    }
                },
                {
                    'id': 'hardship',
                    'question': 'What caused you to stop making payments?',
                    'options': [
                        'Lost job/income',
                        'Medical emergency',
                        'Divorce/separation',
                        'Disability',
                        'Dispute with creditor',
                        'Could never afford it'
                    ],
                    'follow_ups': {
                        'Medical emergency': 'Do you have medical records from that time?',
                        'Dispute with creditor': 'What was the dispute about?'
                    }
                }
            ],
            'tier_3_strategic': [
                {
                    'id': 'settlement_attempts',
                    'question': 'Have you ever tried to settle or negotiate this debt?',
                    'options': [
                        'Yes, they refused my offer',
                        'Yes, we had an agreement they broke',
                        'Yes, currently negotiating',
                        'No, never contacted them',
                        'They never contacted me'
                    ]
                },
                {
                    'id': 'other_debts',
                    'question': 'Is this the only debt you\'re being sued for?',
                    'options': [
                        'Yes, only this one',
                        'No, multiple lawsuits',
                        'Expecting more lawsuits',
                        'Considering bankruptcy'
                    ],
                    'follow_ups': {
                        'Considering bankruptcy': 'Have you consulted with a bankruptcy attorney?'
                    }
                }
            ]
        }

        return tree

    def _build_eviction_question_tree(self, analysis: Dict) -> Dict:
        '''Sophisticated question tree for eviction cases'''

        tree = {
            'tier_1_critical': [
                {
                    'id': 'notice_received',
                    'question': 'Did you receive a written notice to vacate before this lawsuit?',
                    'options': [
                        'Yes, written notice',
                        'Verbal notice only',
                        'No notice at all',
                        'Not sure/don\'t remember'
                    ],
                    'defense_impact': {
                        'Verbal notice only': 'STRONG improper notice defense',
                        'No notice at all': 'STRONG improper notice defense'
                    }
                },
                {
                    'id': 'rent_current',
                    'question': 'Are you current on your rent?',
                    'options': [
                        'Yes, fully current',
                        'Behind but catching up',
                        'Behind several months',
                        'Withholding for repairs',
                        'Disputed amount'
                    ]
                }
            ]
        }

        return tree

    def _build_general_question_tree(self, analysis: Dict) -> Dict:
        '''General question tree for other case types'''

        tree = {
            'tier_1_critical': [
                {
                    'id': 'case_understanding',
                    'question': 'Do you understand what the plaintiff is claiming?',
                    'options': [
                        'Yes, I understand the claim',
                        'Partially understand',
                        'No, very confused',
                        'The claim is false'
                    ]
                }
            ]
        }

        return tree

    def get_next_intelligent_question(self) -> Optional[Dict]:
        '''Get the next question based on document analysis and previous answers'''

        # Check for critical follow-ups first
        if self.follow_up_needed:
            follow_up = self.follow_up_needed.pop(0)
            return {
                'question': follow_up['question'],
                'type': 'follow_up',
                'options': follow_up.get('options', None),
                'importance': 'HIGH',
                'reason': follow_up.get('reason')
            }

        # Go through question tiers
        for tier in ['tier_1_critical', 'tier_2_important', 'tier_3_strategic']:
            tier_questions = self.question_tree.get(tier, [])
            for q in tier_questions:
                if q['id'] not in self.asked_questions:
                    self.asked_questions.append(q['id'])
                    self.question_count += 1
                    return {
                        'question': q['question'],
                        'options': q.get('options'),
                        'type': tier,
                        'id': q['id'],
                        'question_number': self.question_count,
                        'total_questions': min(self.max_questions, self._count_remaining_questions())
                    }

        return None  # No more questions

    def _count_remaining_questions(self) -> int:
        '''Count how many questions remain'''
        total = 0
        for tier in ['tier_1_critical', 'tier_2_important', 'tier_3_strategic']:
            tier_questions = self.question_tree.get(tier, [])
            total += len([q for q in tier_questions if q['id'] not in self.asked_questions])
        return total

    def process_answer_intelligently(self, question_id: str, answer: str) -> Dict:
        '''Process answer and adapt strategy'''

        # Store answer
        self.brain.memory[question_id] = answer

        # Check for follow-ups
        question_data = self._find_question_data(question_id)
        if question_data and 'follow_ups' in question_data:
            if answer in question_data['follow_ups']:
                follow_up = question_data['follow_ups'][answer]
                self.follow_up_needed.append({
                    'question': follow_up,
                    'reason': f'Following up on: {answer}',
                    'parent_question': question_id
                })

        # Check defense impact
        if question_data and 'defense_impact' in question_data:
            if answer in question_data['defense_impact']:
                impact = question_data['defense_impact'][answer]
                self.brain.insights.append(impact)
                self._update_defense_strength(impact)

        # Adaptive responses based on answers
        insights = self._generate_insights_from_answer(question_id, answer)

        return {
            'insights': insights,
            'defense_implications': self.brain.insights[-1] if self.brain.insights else None,
            'follow_up_needed': len(self.follow_up_needed) > 0
        }

    def _find_question_data(self, question_id: str) -> Optional[Dict]:
        '''Find question data by ID'''
        for tier in ['tier_1_critical', 'tier_2_important', 'tier_3_strategic']:
            tier_questions = self.question_tree.get(tier, [])
            for q in tier_questions:
                if q['id'] == question_id:
                    return q
        return None

    def _generate_insights_from_answer(self, question_id: str, answer: str) -> List[str]:
        '''Generate insights from answer'''
        insights = []

        if question_id == 'last_payment' and 'Over 6 years ago' in answer:
            insights.append('Strong statute of limitations defense likely available')

        if question_id == 'debt_recognition' and 'don\'t recognize' in answer:
            insights.append('Can dispute debt validity entirely')

        if question_id == 'notice_received' and 'No notice' in answer:
            insights.append('Critical procedural defense - improper notice')

        return insights

    def _update_defense_strength(self, impact: str):
        '''Update defense strength scores'''

        if 'STRONG' in impact:
            if 'statute of limitations' in impact.lower():
                self.defense_strength['statute_of_limitations'] = 90
            elif 'standing' in impact.lower():
                self.defense_strength['lack_of_standing'] = 85
            elif 'notice' in impact.lower():
                self.defense_strength['improper_notice'] = 95
        elif 'Possible' in impact:
            if 'statute of limitations' in impact.lower():
                self.defense_strength['statute_of_limitations'] = 60

    def build_comprehensive_defense_strategy(self) -> Dict:
        '''Build detailed, sophisticated defense strategy'''

        # Analyze all collected information
        defenses = []

        # 1. Statute of Limitations Analysis
        if self.brain.memory.get('last_payment'):
            sol_analysis = self._analyze_statute_of_limitations()
            if sol_analysis.get('applicable'):
                defenses.append(sol_analysis)

        # 2. Standing/Ownership Analysis
        standing_analysis = self._analyze_standing()
        if standing_analysis.get('issues_found'):
            defenses.append(standing_analysis)

        # 3. Amount Dispute Analysis
        amount_analysis = self._analyze_amount_claimed()
        if amount_analysis.get('discrepancies'):
            defenses.append(amount_analysis)

        # 4. Procedural Defenses
        procedural = self._analyze_procedural_issues()
        if procedural.get('violations'):
            defenses.append(procedural)

        # 5. Affirmative Defenses
        affirmative = self._analyze_affirmative_defenses()
        defenses.extend(affirmative)

        # Build comprehensive strategy
        strategy = {
            'primary_defenses': sorted(defenses, key=lambda x: x.get('strength', 0), reverse=True)[:3],
            'secondary_defenses': sorted(defenses, key=lambda x: x.get('strength', 0), reverse=True)[3:6],
            'immediate_actions': self._generate_action_plan(),
            'evidence_needed': self._identify_evidence_needs(),
            'negotiation_leverage': self._assess_negotiation_position(),
            'estimated_success_rate': self._calculate_overall_success_rate(),
            'detailed_explanation': self._generate_detailed_explanation()
        }

        return strategy

    def _analyze_statute_of_limitations(self) -> Dict:
        '''Detailed statute of limitations analysis'''

        last_payment = self.brain.memory.get('last_payment', '')

        # Calculate years
        years_map = {
            'Within the last year': 0.5,
            '1-2 years ago': 1.5,
            '2-4 years ago': 3,
            '4-6 years ago': 5,
            'Over 6 years ago': 7,
            'Never made any payments': None
        }

        years = years_map.get(last_payment)

        if years and years >= 4:
            return {
                'name': 'Statute of Limitations',
                'applicable': True,
                'strength': 95 if years >= 6 else 75,
                'description': f'The debt appears to be {years}+ years old, beyond the legal collection period in most states.',
                'detailed_explanation': f'''
                Based on your last payment being {last_payment}, this debt has likely exceeded the statute of limitations.
                Most states have a 3-6 year limit for debt collection lawsuits.

                Key points:
                - The plaintiff must prove the debt is within the statute
                - Your last payment date resets the clock
                - Written acknowledgment can revive expired debt
                - This is a complete defense if proven
                ''',
                'requirements': [
                    'Proof of last payment date',
                    'No written acknowledgment after last payment',
                    'Research your state\'s specific statute'
                ],
                'how_to_assert': 'Include as affirmative defense in your answer: "Plaintiff\'s claim is barred by the applicable statute of limitations"'
            }

        return {'applicable': False}

    def _analyze_standing(self) -> Dict:
        '''Detailed standing and ownership analysis'''

        issues = []
        strength = 0

        doc_analysis = self.brain.memory.get('document_analysis', {})

        # Check if debt buyer
        if 'debt_buyer' in str(doc_analysis):
            issues.append('Plaintiff appears to be a debt buyer, not original creditor')
            strength += 30

        # Check for missing documents
        if 'original_contract' not in str(doc_analysis):
            issues.append('No original contract attached to prove terms')
            strength += 25

        if 'assignment' not in str(doc_analysis):
            issues.append('No proof of assignment or chain of title')
            strength += 30

        if issues:
            return {
                'name': 'Lack of Standing',
                'issues_found': True,
                'strength': min(strength, 85),
                'description': 'Plaintiff has not proven they own this debt or have the right to collect.',
                'detailed_explanation': f'''
                The plaintiff has failed to establish proper standing to sue:

                Issues identified:
                {chr(10).join(f'- {issue}' for issue in issues)}

                Legal requirements:
                - Debt buyers must prove complete chain of ownership
                - Must show valid assignment from original creditor
                - Must prove terms of original agreement
                - Cannot rely on conclusory allegations
                ''',
                'requirements': [
                    'Demand complete chain of title',
                    'Request original signed contract',
                    'Challenge any affidavits as hearsay',
                    'Request proof of consideration for assignment'
                ],
                'how_to_assert': 'Deny plaintiff has standing and demand strict proof of ownership'
            }

        return {'issues_found': False}

    def _analyze_amount_claimed(self) -> Dict:
        '''Analyze amount claimed for discrepancies'''
        return {'discrepancies': False}

    def _analyze_procedural_issues(self) -> Dict:
        '''Analyze for procedural violations'''
        return {'violations': False}

    def _analyze_affirmative_defenses(self) -> List[Dict]:
        '''Identify available affirmative defenses'''
        return []

    def _generate_action_plan(self) -> List[Dict]:
        '''Generate detailed action plan'''

        actions = [
            {
                'action': 'File Answer',
                'deadline': self.brain.memory.get('response_deadline', '20-30 days'),
                'priority': 'CRITICAL',
                'details': 'Must file answer with court and serve on plaintiff attorney',
                'how_to': '''
                1. Use court's answer form or create your own
                2. Respond to each numbered allegation (admit/deny/lack knowledge)
                3. Include all affirmative defenses
                4. File with court clerk
                5. Mail copy to plaintiff's attorney (certified mail)
                '''
            },
            {
                'action': 'Request Discovery',
                'deadline': 'With or shortly after answer',
                'priority': 'HIGH',
                'details': 'Demand all documents supporting their claim',
                'what_to_request': [
                    'Original signed contract',
                    'Complete payment history',
                    'Chain of assignment documents',
                    'Original creditor records',
                    'Calculation of amount claimed'
                ]
            },
            {
                'action': 'Gather Your Evidence',
                'deadline': 'Immediately',
                'priority': 'HIGH',
                'details': 'Collect all documents supporting your defense',
                'what_to_gather': [
                    'Bank statements showing last payment',
                    'Any correspondence with creditor',
                    'Proof of any disputes',
                    'Settlement offers or agreements',
                    'Records of financial hardship'
                ]
            }
        ]

        return actions

    def _identify_evidence_needs(self) -> List[str]:
        '''Identify what evidence is needed'''
        return [
            'Proof of last payment date',
            'Bank statements',
            'Any written correspondence'
        ]

    def _assess_negotiation_position(self) -> Dict:
        '''Assess negotiation leverage'''
        return {
            'strength': 'Moderate',
            'leverage_points': ['Strong defenses available', 'Plaintiff may lack documentation']
        }

    def _calculate_overall_success_rate(self) -> str:
        '''Calculate overall defense success probability'''

        total_strength = sum(self.defense_strength.values())
        defense_count = len(self.defense_strength)

        if defense_count == 0:
            return 'Moderate - 40-50%'

        average_strength = total_strength / defense_count

        if average_strength >= 80:
            return 'Very Strong - 70-80% chance of success'
        elif average_strength >= 60:
            return 'Strong - 60-70% chance of success'
        elif average_strength >= 40:
            return 'Moderate - 40-60% chance of success'
        else:
            return 'Challenging - 30-40% chance of success'

    def _generate_detailed_explanation(self) -> str:
        '''Generate detailed strategy explanation'''
        return 'Based on the interview responses and document analysis, a comprehensive defense strategy has been developed.'

    async def call_ai_for_analysis(self, prompt: str) -> Dict:
        '''Call AI API for analysis (placeholder)'''
        # This would call actual AI API
        return {
            'case_type': 'debt_collection',
            'plaintiff_name': 'Unknown',
            'amount_claimed': '0'
        }

# Make it available globally
legal_agent_instances = {}
