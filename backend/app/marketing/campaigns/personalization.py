"""
AI Email Personalization

Uses the shared AI layer (Claude/GPT) to personalize email content
based on contact information and case context.
"""

import os
import logging
from typing import Optional, Dict, Any

from app.marketing.campaigns.models import EmailSend
from app.marketing.contacts.models import Contact, ContactCase

logger = logging.getLogger(__name__)


class EmailPersonalizer:
    """
    AI-powered email personalization.

    Uses the existing dual AI service to personalize
    email content based on contact and case context.
    """

    def __init__(self):
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')

    async def personalize_email(
        self,
        email_send: EmailSend,
        contact: Contact,
        custom_prompt: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Personalize email content using AI.

        Args:
            email_send: EmailSend with template content
            contact: Recipient contact with profile info
            custom_prompt: Optional custom personalization prompt

        Returns:
            Dict with personalized 'subject' and 'body_html', or None if failed
        """
        if not self.anthropic_key and not self.openai_key:
            logger.warning("No AI API key configured for personalization")
            return None

        try:
            # Build context from contact and case info
            context = self._build_context(email_send, contact)

            # Build personalization prompt
            prompt = self._build_prompt(
                email_send.subject_line,
                email_send.body_html,
                context,
                custom_prompt
            )

            # Call AI service
            result = await self._call_ai(prompt)

            if result:
                return {
                    "subject": result.get("subject", email_send.subject_line),
                    "body_html": result.get("body_html", email_send.body_html)
                }

        except Exception as e:
            logger.error(f"Error personalizing email: {e}", exc_info=True)

        return None

    def _build_context(
        self,
        email_send: EmailSend,
        contact: Contact
    ) -> Dict[str, Any]:
        """Build context dictionary for personalization."""
        context = {
            "contact": {
                "first_name": contact.first_name or "",
                "last_name": contact.last_name or "",
                "full_name": contact.full_name or contact.display_name,
                "firm_name": contact.firm_name or "",
                "title": contact.title or "",
                "city": contact.city or "",
                "state": contact.state or "",
                "contact_type": contact.contact_type.value if contact.contact_type else "unknown"
            }
        }

        # Add case context from personalization_data
        if email_send.personalization_data:
            context["case"] = {
                "case_name": email_send.personalization_data.get("case_name", ""),
                "case_number": email_send.personalization_data.get("case_number", ""),
                "court": email_send.personalization_data.get("court", ""),
                "nature_of_suit": email_send.personalization_data.get("nature_of_suit", "")
            }

        return context

    def _build_prompt(
        self,
        subject: str,
        body_html: str,
        context: Dict[str, Any],
        custom_prompt: Optional[str] = None
    ) -> str:
        """Build the AI personalization prompt."""
        base_prompt = f"""You are an email personalization assistant for a legal technology company.
Your task is to personalize the following marketing email while maintaining professionalism
and CAN-SPAM compliance.

RECIPIENT CONTEXT:
- Name: {context['contact']['full_name']}
- Firm/Company: {context['contact']['firm_name']}
- Title: {context['contact']['title']}
- Location: {context['contact']['city']}, {context['contact']['state']}
- Contact Type: {context['contact']['contact_type']}

"""

        if context.get('case'):
            base_prompt += f"""CASE CONTEXT:
- Case Name: {context['case']['case_name']}
- Case Number: {context['case']['case_number']}
- Court: {context['case']['court']}

"""

        if custom_prompt:
            base_prompt += f"""CUSTOM INSTRUCTIONS:
{custom_prompt}

"""

        base_prompt += f"""ORIGINAL EMAIL:
Subject: {subject}

Body:
{body_html}

INSTRUCTIONS:
1. Personalize the email to be more relevant to this specific recipient
2. Keep the core message and call-to-action intact
3. Maintain a professional tone appropriate for legal professionals
4. Do NOT add false claims or promises
5. Do NOT remove the unsubscribe link or physical address
6. Do NOT make up case details that weren't provided

Return ONLY a JSON object with two keys:
- "subject": the personalized subject line
- "body_html": the personalized HTML body

Return valid JSON only, no other text."""

        return base_prompt

    async def _call_ai(self, prompt: str) -> Optional[Dict[str, str]]:
        """Call AI service for personalization."""
        import json

        # Try Anthropic first
        if self.anthropic_key:
            try:
                import anthropic

                client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)

                response = await client.messages.create(
                    model="claude-3-5-haiku-20241022",  # Use faster model for personalization
                    max_tokens=2000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                content = response.content[0].text
                return json.loads(content)

            except Exception as e:
                logger.warning(f"Anthropic personalization failed: {e}")

        # Fallback to OpenAI
        if self.openai_key:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=self.openai_key)

                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )

                content = response.choices[0].message.content
                return json.loads(content)

            except Exception as e:
                logger.warning(f"OpenAI personalization failed: {e}")

        return None

    async def generate_case_summary(
        self,
        case: ContactCase
    ) -> Optional[str]:
        """
        Generate an AI summary of a case for email personalization.

        Args:
            case: ContactCase record

        Returns:
            AI-generated case summary or None
        """
        if not self.anthropic_key and not self.openai_key:
            return None

        prompt = f"""Summarize this court case in 2-3 sentences for a marketing email context.
Keep it factual and professional.

Case: {case.case_name or 'Unknown'}
Case Number: {case.case_number or 'Unknown'}
Court: {case.court or 'Unknown'}
Nature of Suit: {case.nature_of_suit or 'Unknown'}
Date Filed: {case.date_filed.strftime('%Y-%m-%d') if case.date_filed else 'Unknown'}
Role: {case.role or 'Unknown'}

Return ONLY the summary text, no other formatting."""

        try:
            if self.anthropic_key:
                import anthropic

                client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)
                response = await client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()

            elif self.openai_key:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=self.openai_key)
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200
                )
                return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating case summary: {e}")

        return None

    async def score_lead(
        self,
        contact: Contact,
        cases: list[ContactCase]
    ) -> Dict[str, Any]:
        """
        Use AI to score a lead based on profile and cases.

        Args:
            contact: Contact record
            cases: List of associated cases

        Returns:
            Dict with score and reasoning
        """
        if not self.anthropic_key and not self.openai_key:
            return {"score": 50, "reasoning": "No AI available for scoring"}

        # Build context
        case_info = "\n".join([
            f"- {c.case_name} ({c.nature_of_suit}) - {c.role}"
            for c in cases[:5]  # Limit to 5 cases
        ]) or "No cases"

        prompt = f"""Score this lead for a legal technology SaaS product (0-100).
Consider their potential value as a customer based on their profile and cases.

Contact Type: {contact.contact_type.value if contact.contact_type else 'unknown'}
Firm: {contact.firm_name or 'Unknown'}
Location: {contact.city}, {contact.state}
Cases:
{case_info}

Return a JSON object with:
- "score": integer 0-100
- "tier": "hot", "warm", or "cold"
- "reasoning": brief explanation

Return valid JSON only."""

        try:
            import json

            if self.anthropic_key:
                import anthropic

                client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)
                response = await client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )
                return json.loads(response.content[0].text)

            elif self.openai_key:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=self.openai_key)
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Error scoring lead: {e}")

        return {"score": 50, "tier": "warm", "reasoning": "Default score"}
