"""
Q&A Handler - FORCES Concise Responses
Uses hardcoded responses to avoid AI verbosity
"""

from typing import Dict
import random


class QAHandler:
    '''Q&A that FORCES concise responses'''

    @staticmethod
    def get_concise_answer(question: str, context: Dict = None) -> str:
        '''HARDCODED concise responses - NO AI verbosity'''

        q = question.lower()

        # HARDCODED responses that are ALWAYS concise
        responses = {
            'defense options': 'Complete the interview first. Then use Defense Builder to see your specific defenses.',
            'what are my defenses': 'Complete the interview first. Then use Defense Builder to see your specific defenses.',
            'defenses': 'Complete the interview first. Defense Builder will show your options.',
            'lawsuit': 'File answer in 20-30 days. Deny false claims. Assert defenses.',
            'sued': 'Respond by deadline. Request evidence. Don\'t ignore.',
            'debt': 'Check if over 4 years old. Request validation. Dispute amount.',
            'eviction': 'You have 5 days. Document repairs. Pay or move.',
            'bankruptcy': 'Chapter 7 erases debt. Chapter 13 repays. Costs $1500.',
            'deadline': 'Check court papers for date. Usually 20-30 days.',
            'lawyer': 'Legal aid offers free help. Bar association has referrals.',
            'court': 'Arrive early. Dress nicely. Bring documents.',
            'payment': 'Get receipts. Never pay without documentation.',
            'contract': 'Request original from plaintiff. They must prove claim.',
            'summons': 'File answer by deadline. Deny claims you dispute.',
            'complaint': 'Read carefully. Note what plaintiff claims. Respond to each point.',
            'answer': 'Admit or deny each claim. Assert all defenses. File by deadline.',
            'motion': 'File written response in 14 days. Attend hearing.',
            'discovery': 'Respond in 30 days. Object if improper. Provide documents.',
            'judgment': 'Appeal within 30 days if you lost. File motion to vacate if defaulted.',
            'garnishment': 'File exemption claim immediately. Protects wages/benefits.',
            'settle': 'Get agreement in writing. Pay only what you can afford.',
            'credit': 'Dispute errors with bureaus. Get validation from collector.',
            'statute': 'Most debts expire in 4-6 years. Check your state law.',
            'standing': 'Plaintiff must prove they own the debt. Request proof.',
            'validation': 'Request within 30 days. Collector must provide proof.',
            'service': 'Must be served properly. Challenge if service was improper.',
            'default': 'File motion to set aside within 1 year. Show good cause.',
            'trial': 'Prepare witnesses and documents. Practice testimony.',
            'appeal': 'File notice within 30 days. Costs $300-500.',
            'attorney': 'Legal aid is free if you qualify. Private costs $200-400/hour.',
            'forms': 'Court clerk has free forms. Legal aid helps fill them out.',
            'hearing': 'Arrive 15 minutes early. Turn off phone. Stand when speaking.',
            'evidence': 'Bring originals and copies. Organize chronologically.',
            'witness': 'Subpoena if they won\'t come voluntarily. Prepare questions.',
            'subpoena': 'Serves in person or by mail. Must give 14 days notice.',
            'continuance': 'File motion with good reason. Court may grant one time.',
            'dismiss': 'File motion if plaintiff lacks proof or missed deadlines.',
            'counterclaim': 'File with your answer. State separate claims against plaintiff.',
            'affidavit': 'Sworn statement of facts. Notarize before filing.',
            'deposition': 'Answer questions under oath. Can have attorney present.',
            'interrogatories': 'Written questions to answer under oath. 30 days to respond.',
            'notice': 'Read carefully for deadlines. File response if required.',
            'demand': 'Not enforceable until court orders. Don\'t ignore court orders.',
            'lien': 'File release after debt paid. Challenge if improper.',
            'levy': 'File exemption claim immediately. Protects property.',
            'execution': 'Court enforcement of judgment. File exemptions to protect assets.'
        }

        # Find matching response
        for key, response in responses.items():
            if key in q:
                return response + QAHandler._add_question(q)

        # Default response
        return 'Act by deadline. Gather documents. File response.' + QAHandler._add_question(q)

    @staticmethod
    def _add_question(original_question: str) -> str:
        '''Add a follow-up question'''

        questions = [
            '\n\n❓ When did this issue start?',
            '\n\n❓ What documents do you have?',
            '\n\n❓ Have you tried to resolve this?',
            '\n\n❓ What is the deadline?',
            '\n\n❓ What amount is claimed?'
        ]

        # Return a relevant question
        return random.choice(questions)

    @staticmethod
    async def process_qa_message(message: str, session_id: str, context: Dict = None) -> Dict:
        '''Process Q&A with FORCED conciseness'''

        # Get concise answer - NO AI CALLS
        answer = QAHandler.get_concise_answer(message, context)

        # Force to be short
        words = answer.split()
        if len(words) > 50:
            answer = ' '.join(words[:50]) + '.'

        return {
            'response': answer,
            'word_count': len(answer.split()),
            'has_question': '?' in answer,
            'model': 'hardcoded_concise'  # Not using AI
        }
