"""
Force Correct Behavior Middleware
Intercepts EVERY response and enforces:
- Conciseness (50 words max)
- No attorney deflections
- Always includes a question
- Provides defenses when asked
"""

import re
import random
from typing import Any, Dict, Union


class ForceCorrectBehavior:
    """
    NUCLEAR OPTION: Forces all responses to behave correctly
    """

    @staticmethod
    def override(response: Any) -> Any:
        """
        Intercept and fix EVERY response
        """
        if isinstance(response, str):
            response = ForceCorrectBehavior.force_conciseness(response)
            response = ForceCorrectBehavior.remove_attorney_deflection(response)
            response = ForceCorrectBehavior.add_question_if_missing(response)
            response = ForceCorrectBehavior.add_defenses_if_needed(response)
        elif isinstance(response, dict):
            # Handle dict responses (most API responses)
            if 'answer' in response:
                response['answer'] = ForceCorrectBehavior.override(response['answer'])
            if 'response' in response:
                response['response'] = ForceCorrectBehavior.override(response['response'])

        return response

    @staticmethod
    def force_conciseness(text: str) -> str:
        """
        Remove ALL verbose patterns, 3rd-grader language, and force to 50 words
        """
        # Remove "3rd grader" explanatory language FIRST
        explanatory_patterns = [
            r'[Ll]et me (explain|help you understand|break (this|that) down)[^.!?]*[.!?]',
            r'[Tt]o (help you understand|make (this|it) (simple|clear|easier))[^.!?]*[.!?]',
            r'[Ii]n (simple|easy|basic) (terms|words|language)[^.!?]*[.!?]',
            r'[Tt]hink of it (as|like|this way)[^.!?]*[.!?]',
            r'[Ww]hat (this|that) (means|is saying) is[^.!?]*[.!?]',
            r'[Tt]o put it (simply|another way|in simple terms)[^.!?]*[.!?]',
            r'[Hh]ere\'s what (this|that) means[^.!?]*[.!?]',
            r'[Bb]asically[,\s]+',
            r'[Ee]ssentially[,\s]+'
        ]

        cleaned = text
        for pattern in explanatory_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # Remove analogies and metaphors
        metaphor_patterns = [
            r'[Ll]ike\s+(a|an|having|being)\s+[^.!?]+[.!?]',
            r'[Ll]ike\s+[^.!?]+[.!?]',
            r'[Ii]magine[^.!?]+[.!?]',
            r'[Ii]n\s+the\s+(grand|same)[^.!?]+[.!?]',
            r'[Tt]hink\s+of[^.!?]+[.!?]',
            r'[Pp]icture[^.!?]+[.!?]',
            r'[Ss]imilar\s+to[^.!?]+[.!?]',
            r'[Jj]ust\s+as[^.!?]+[.!?]',
            r'[Mm]uch\s+like[^.!?]+[.!?]'
        ]

        for pattern in metaphor_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # Remove verbose introductions and condescending phrases
        verbose_starts = [
            'Let me explain', 'Let me help you understand', 'Let me break this down',
            'I understand', 'I see', 'To clarify', 'To put it simply',
            'In other words', 'Simply put', 'What this means is',
            'Think of it this way', 'The way I see it', 'From my perspective',
            'If you will', 'So to speak', 'In a sense', 'In a manner of speaking',
            'What I\'m saying is', 'To make it clear', 'To help you out',
            'Here\'s the thing', 'You see', 'The important thing to know is',
            'You need to understand that', 'Basically', 'Essentially'
        ]

        for phrase in verbose_starts:
            if cleaned.lower().startswith(phrase.lower()):
                cleaned = cleaned[len(phrase):].strip()
                # Remove punctuation after removing phrase
                cleaned = re.sub(r'^[,;:]\s*', '', cleaned)

        # Remove these phrases anywhere in text
        for phrase in verbose_starts:
            cleaned = cleaned.replace(phrase, '').replace(phrase.lower(), '')

        # Clean up orphaned punctuation and spaces
        cleaned = re.sub(r'\s*[,;]\s*[.,;]', '.', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'^\s*[,;.]\s*', '', cleaned)
        cleaned = cleaned.strip()

        # Force to 50 words max (HARD LIMIT)
        words = cleaned.split()
        if len(words) > 50:
            cleaned = ' '.join(words[:50])
            # Add period if doesn't end with punctuation
            if cleaned and cleaned[-1] not in '.!?':
                cleaned += '.'

        return cleaned

    @staticmethod
    def remove_attorney_deflection(text: str) -> str:
        """
        Remove ALL attorney deflection phrases
        """
        deflections = [
            r'[Cc]onsult\s+with\s+(an\s+)?attorney[^.!?]*[.!?]?',
            r'[Ss]eek\s+legal\s+advice[^.!?]*[.!?]?',
            r'[Ss]peak\s+to\s+(a\s+)?lawyer[^.!?]*[.!?]?',
            r'[Cc]ontact\s+(an\s+)?attorney[^.!?]*[.!?]?',
            r'professional\s+legal\s+advice[^.!?]*[.!?]?',
            r'qualified\s+attorney[^.!?]*[.!?]?',
            r'legal\s+professional[^.!?]*[.!?]?',
            r'[Yy]ou\s+should\s+consult[^.!?]*[.!?]?',
            r'[Ii]\s+recommend\s+consulting[^.!?]*[.!?]?',
            r'[Ii]t\'s\s+important\s+to\s+get\s+legal[^.!?]*[.!?]?',
        ]

        cleaned = text
        for pattern in deflections:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # Remove empty sentences left behind
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()

        return cleaned

    @staticmethod
    def add_question_if_missing(text: str) -> str:
        """
        If no question present, add one
        """
        # Check if text already has a question
        if '?' not in text and '❓' not in text:
            questions = [
                '\n\n❓ When did this legal issue start?',
                '\n\n❓ What court documents have you received?',
                '\n\n❓ What is the deadline to respond?',
                '\n\n❓ How much money is involved?',
                '\n\n❓ Have you tried to resolve this yet?',
                '\n\n❓ Do you have any documentation?',
                '\n\n❓ When were you first contacted about this?',
                '\n\n❓ What state are you in?',
            ]
            text += random.choice(questions)

        return text

    @staticmethod
    def add_defenses_if_needed(text: str) -> str:
        """
        If asking about defenses but none provided, add them
        """
        text_lower = text.lower()

        # If defense-related but no numbered list, add defenses
        if any(keyword in text_lower for keyword in ['defense', 'defend', 'fight', 'challenge']) and not re.search(r'\d+\.', text):
            text += '\n\n**DEFENSE OPTIONS:**\n'
            text += '1. **Statute of Limitations** - Claim too old to pursue\n'
            text += '2. **Lack of Evidence** - They can\'t prove their claim\n'
            text += '3. **Procedural Errors** - Legal process not followed properly'

        return text


def apply_forced_corrections(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply corrections to API response data
    Use this in your API endpoints
    """
    return ForceCorrectBehavior.override(response_data)


# Export the class and helper function
__all__ = ['ForceCorrectBehavior', 'apply_forced_corrections']
