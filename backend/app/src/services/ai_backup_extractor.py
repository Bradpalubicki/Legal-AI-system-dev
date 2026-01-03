"""
AI Backup Extraction Service

When regex patterns fail to extract data, use AI as backup to ensure
we don't miss critical financial or legal information.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import anthropic
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class AIBackupExtractor:
    """
    AI-powered backup extraction when pattern matching fails
    """

    def __init__(self):
        self.claude_client = None
        self.openai_client = None

        # Initialize Claude if available
        if os.getenv('ANTHROPIC_API_KEY'):
            self.claude_client = anthropic.Anthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                timeout=30.0
            )

        # Initialize OpenAI if available
        if os.getenv('OPENAI_API_KEY'):
            self.openai_client = AsyncOpenAI(
                api_key=os.getenv('OPENAI_API_KEY')
            )

    async def extract_with_ai(
        self,
        text: str,
        extraction_type: str,
        current_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Backup extraction using AI when patterns fail

        Args:
            text: Document text
            extraction_type: Type of extraction (financial, ownership, legal)
            current_results: Current extraction results from pattern matching

        Returns:
            Enhanced extraction results
        """
        # Prefer Claude for legal analysis, OpenAI as fallback
        if self.claude_client:
            return await self._extract_with_claude(text, extraction_type, current_results)
        elif self.openai_client:
            return await self._extract_with_openai(text, extraction_type, current_results)
        else:
            logger.warning("No AI client available for backup extraction")
            return current_results or {}

    async def _extract_with_claude(
        self,
        text: str,
        extraction_type: str,
        current_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use Claude for backup extraction
        """
        try:
            prompt = self._build_extraction_prompt(text, extraction_type, current_results)

            response = self.claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8000,
                temperature=0,  # Deterministic extraction
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Extract JSON from response
            extracted_data = self._parse_ai_response(response_text)

            logger.info(f"Claude backup extraction completed for {extraction_type}")
            return extracted_data

        except Exception as e:
            logger.error(f"Claude backup extraction failed: {str(e)}")
            return current_results or {}

    async def _extract_with_openai(
        self,
        text: str,
        extraction_type: str,
        current_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use OpenAI for backup extraction
        """
        try:
            prompt = self._build_extraction_prompt(text, extraction_type, current_results)

            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a specialized bankruptcy document analysis expert. Extract ALL financial and legal data precisely as JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content
            extracted_data = json.loads(response_text)

            logger.info(f"OpenAI backup extraction completed for {extraction_type}")
            return extracted_data

        except Exception as e:
            logger.error(f"OpenAI backup extraction failed: {str(e)}")
            return current_results or {}

    def _build_extraction_prompt(
        self,
        text: str,
        extraction_type: str,
        current_results: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build extraction prompt based on type and current results
        """
        # Truncate text if too long
        max_text_length = 15000
        truncated_text = text[:max_text_length]
        if len(text) > max_text_length:
            truncated_text += "\n\n[... text truncated ...]"

        base_prompt = f"""You are analyzing a bankruptcy legal document. The pattern-based extraction may have missed some data.

DOCUMENT TEXT:
{truncated_text}

"""

        if extraction_type == "financial":
            base_prompt += """
TASK: Extract ALL financial data from this bankruptcy document.

You MUST find and extract:

1. MONETARY AMOUNTS - Every dollar amount with context:
   - Settlement amounts (who pays what to whom)
   - Claim amounts (secured, unsecured, priority)
   - Payment amounts
   - Debt amounts
   - Asset values

2. PERCENTAGES - Every percentage with ownership context:
   - Voting control percentages
   - Economic ownership percentages
   - Recovery rates
   - Distribution percentages

3. SHARES - Every share distribution:
   - Number of shares
   - Type (voting, non-voting, common, preferred)
   - Who receives them

4. CLAIMS - Every claim mentioned:
   - Claim amount
   - Claim type (secured, unsecured, priority)
   - Claimant if mentioned

5. SETTLEMENTS - Every settlement term:
   - Payment amount
   - Original claim/debt amount
   - Calculate premium (payment / original)

Return ONLY valid JSON in this exact format:
{
    "monetary_amounts": [
        {"amount": 5033301.46, "context": "proposes to pay creditors...", "raw": "$5,033,301.46"}
    ],
    "percentages": [
        {"value": 51.0, "type": "voting_control", "entity": "Smith", "context": "..."}
    ],
    "shares": [
        {"count": 100000, "type": "voting", "owner": "Class A creditors", "context": "..."}
    ],
    "claims": [
        {"amount": 1500000.00, "type": "secured", "context": "..."}
    ],
    "settlements": [
        {"payment_amount": 5033301.46, "original_amount": 3500000.00, "premium_multiple": 1.44, "context": "..."}
    ]
}

CRITICAL RULES:
- Amounts must be numbers (float), not strings
- Find EVERY dollar amount, even if redacted (note as "redacted": true)
- Premium = payment_amount / original_amount
- Context should be 100-200 characters around the value
- If you're unsure, include it with lower confidence
"""

        elif extraction_type == "ownership":
            base_prompt += """
TASK: Extract ALL ownership and control structure data.

You MUST find:

1. VOTING CONTROL - Who controls what percentage of voting rights
2. ECONOMIC OWNERSHIP - Who owns what percentage economically
3. CONTROL DISPARITIES - Cases where voting control != economic ownership
4. SHARE STRUCTURES - Different classes of shares and their rights

Return ONLY valid JSON:
{
    "voting_control": {"Smith": 51.0, "Jane Doe": 49.0},
    "economic_ownership": {"Smith": 15.0, "Jane Doe": 85.0},
    "control_disparities": [
        {
            "entity": "Smith",
            "voting_control": 51.0,
            "economic_ownership": 15.0,
            "disparity": 36.0,
            "controls_despite_minority": true
        }
    ]
}
"""

        elif extraction_type == "legal":
            base_prompt += """
TASK: Extract ALL legal issues, violations, and references.

You MUST find:

1. CASE CITATIONS - Every legal case referenced
   Format: "Party v. Party, Volume Reporter Page (Year)"

2. STATUTORY REFERENCES - Every U.S.C. citation

3. PRECEDENT VIOLATIONS - Cases cited as being violated

4. AUTHORITY LIMITATIONS - Statements about lack of authority/power

Return ONLY valid JSON:
{
    "case_citations": [
        {"case": "Purdue Pharma L.P. v. United States", "citation": "144 S. Ct. 2079 (2024)"}
    ],
    "statutory_references": [
        {"title": "11", "section": "363(b)", "citation": "11 U.S.C. § 363(b)"}
    ],
    "precedent_violations": [
        {
            "case": "Purdue Pharma L.P. v. United States",
            "citation": "144 S. Ct. 2079 (2024)",
            "violation_type": "non-consensual_third_party_release",
            "context": "..."
        }
    ],
    "authority_limitations": [
        {"limitation": "Trustee lacks authority", "context": "..."}
    ]
}
"""

        # Add current results if available
        if current_results:
            base_prompt += f"""

CURRENT PATTERN-BASED RESULTS (may be incomplete):
{json.dumps(current_results, indent=2)[:1000]}

Your task is to find ADDITIONAL data that the patterns missed, and correct any errors.
"""

        base_prompt += """

IMPORTANT:
- Return ONLY the JSON, no explanatory text
- All monetary amounts must be numbers (float), not strings
- Be thorough - missing data could cost millions
- If a value is redacted, include it with "amount": null and "redacted": true
"""

        return base_prompt

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse AI response and extract JSON
        """
        # Try to extract JSON from response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "{" in response_text:
            # Find the JSON object
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
        else:
            json_str = response_text

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            return {}


# Global instance
ai_backup_extractor = AIBackupExtractor()
