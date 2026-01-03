"""
Enhanced Document Extraction Service
Captures critical operational details from legal documents including:
- Action items with deadlines (shall/must obligations)
- Conditional obligations (if X then Y)
- Permanent restrictions and prohibitions
- Notice/contact information
- Financial implications (even when redacted)
- Legal jurisdiction details
- Critical review dates
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import anthropic
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent.parent / '.env')
logger = logging.getLogger(__name__)


class EnhancedDocumentExtractor:
    """
    Advanced extractor for operational details in legal documents
    """

    def __init__(self):
        self.claude_client = None
        if os.getenv('ANTHROPIC_API_KEY'):
            self.claude_client = anthropic.Anthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                timeout=30.0
            )

    async def extract_operational_details(
        self,
        text: str,
        filename: str = "",
        basic_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract comprehensive operational details from legal document

        Args:
            text: Document text
            filename: Original filename
            basic_analysis: Optional basic analysis to enhance

        Returns:
            Dictionary with enhanced extraction fields
        """
        if self.claude_client:
            return await self._ai_enhanced_extraction(text, filename, basic_analysis)
        else:
            return self._regex_fallback_extraction(text, filename)

    async def _ai_enhanced_extraction(
        self,
        text: str,
        filename: str,
        basic_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use Claude AI for comprehensive operational extraction
        """
        try:
            # Prepare context from basic analysis if available
            context = ""
            if basic_analysis:
                # Handle parties that may be dicts or strings
                parties = basic_analysis.get('parties', [])
                if parties and isinstance(parties[0], dict):
                    parties_str = ', '.join(p.get('name', str(p)) for p in parties)
                else:
                    parties_str = ', '.join(str(p) for p in parties)
                context = f"""
BASIC ANALYSIS CONTEXT:
- Document Type: {basic_analysis.get('document_type', 'Unknown')}
- Parties: {parties_str}
- Case Number: {basic_analysis.get('case_number', 'N/A')}
"""

            prompt = f"""You are a specialized legal document extraction expert. Analyze this document and extract ALL operational details that require action, compliance, or tracking.

{context}

DOCUMENT: {filename}
TEXT: {text[:15000]}

Extract the following information in structured JSON format:

1. ACTION ITEMS WITH DEADLINES - Find all "shall", "must", "will", "agree to" obligations:
   - Extract each mandatory action
   - Identify the responsible party
   - Extract deadline (can be absolute date or relative like "within 30 days of Effective Date")
   - Calculate urgency
   - Note consequences of non-compliance

2. CONDITIONAL OBLIGATIONS - Map dependencies and triggers:
   - Identify "if...then" clauses
   - Extract trigger conditions
   - Extract resulting obligations
   - Note who is responsible
   - Track multi-party dependencies

3. PERMANENT RESTRICTIONS - Ongoing prohibitions and requirements:
   - Non-compete clauses
   - Insurance/indemnification requirements
   - Ongoing reporting obligations
   - Confidentiality requirements
   - Non-disparagement clauses
   - Usage restrictions
   - Licensing limitations

4. NOTICE & CONTACT EXTRACTION:
   - ALL email addresses mentioned
   - ALL mailing addresses (with attention lines)
   - ALL phone/fax numbers
   - Attorney contact information
   - Notice delivery methods (email, certified mail, etc.)
   - Notice timing requirements

5. FINANCIAL IMPLICATIONS:
   - If specific amounts visible: extract with context
   - If amounts redacted: note "Financial terms present but redacted: [description]"
   - Payment schedules and timing
   - Who bears costs/fees
   - Penalty/liquidated damages provisions
   - Remedy calculations

6. LEGAL JURISDICTION:
   - Governing law (state/country)
   - Venue for disputes (specific court/county)
   - Arbitration clauses (arbitrator selection, location, rules)
   - Choice of law provisions
   - Forum selection clauses
   - Class action waivers

7. CRITICAL REVIEW DATES - When to review this agreement:
   - Renewal dates
   - Termination dates
   - Option exercise deadlines
   - Review/renegotiation triggers
   - Automatic renewal provisions

Return ONLY valid JSON in this exact format:
{{
    "action_items": [
        {{
            "obligation": "Detailed description of what must be done",
            "responsible_party": "Who must do it",
            "deadline_type": "absolute|relative|ongoing",
            "deadline_date": "YYYY-MM-DD if absolute, or null",
            "deadline_description": "within X days of Y event",
            "trigger_event": "What triggers this obligation (if any)",
            "urgency": "critical|high|medium|low",
            "consequences": "What happens if not completed",
            "source_text": "Verbatim text from document"
        }}
    ],

    "conditional_obligations": [
        {{
            "condition": "IF condition description",
            "trigger_event": "What must happen to trigger",
            "resulting_obligation": "THEN what must be done",
            "responsible_party": "Who must act",
            "deadline": "When it must be done after trigger",
            "alternative_path": "ELSE clause if any",
            "source_text": "Verbatim conditional clause"
        }}
    ],

    "permanent_restrictions": [
        {{
            "restriction_type": "non-compete|confidentiality|insurance|reporting|other",
            "description": "What is prohibited or required",
            "duration": "How long (e.g., '5 years from termination', 'perpetual')",
            "scope": "Geographic/subject matter scope",
            "exceptions": "Any exceptions to the restriction",
            "breach_consequences": "What happens if violated",
            "source_text": "Verbatim restriction clause"
        }}
    ],

    "notice_contacts": [
        {{
            "contact_type": "party|attorney|agent|other",
            "party_name": "Name of party/person",
            "email_addresses": ["all email addresses for this contact"],
            "mailing_address": "Full mailing address with attention line",
            "phone": "Phone number if provided",
            "fax": "Fax number if provided",
            "notice_methods_allowed": ["email", "certified mail", "courier", "etc"],
            "notice_timing": "Deemed received when (e.g., 'next business day if email')",
            "source_section": "Section reference where found"
        }}
    ],

    "financial_terms": [
        {{
            "term_type": "payment|penalty|fee|damages|cost_allocation|other",
            "amount": "$XX,XXX or 'REDACTED' or 'To be determined'",
            "amount_visible": true|false,
            "description": "Detailed description even if amount redacted",
            "payment_schedule": "When/how often paid",
            "responsible_party": "Who pays",
            "recipient_party": "Who receives",
            "trigger": "What triggers this payment/cost",
            "calculation_method": "How amount is calculated",
            "source_text": "Verbatim financial clause"
        }}
    ],

    "jurisdiction_details": {{
        "governing_law_state": "State whose law governs",
        "governing_law_country": "Country if specified",
        "venue_court": "Specific court if named",
        "venue_county": "County for venue",
        "venue_state": "State for venue",
        "arbitration_required": true|false,
        "arbitration_rules": "AAA, JAMS, etc.",
        "arbitration_location": "City/state for arbitration",
        "arbitrator_selection": "How arbitrator is selected",
        "class_action_waiver": true|false,
        "jury_trial_waiver": true|false,
        "fee_shifting": "Description of who pays legal fees",
        "source_text": "Verbatim jurisdiction clauses"
    }},

    "critical_review_dates": [
        {{
            "review_type": "renewal|termination|option|renegotiation",
            "date": "YYYY-MM-DD if absolute or null",
            "date_description": "X days/months before [event]",
            "action_required": "What must be done by this date",
            "automatic_renewal": true|false,
            "opt_out_deadline": "Deadline to prevent auto-renewal",
            "consequences": "What happens if deadline missed"
        }}
    ],

    "extraction_metadata": {{
        "extraction_date": "{datetime.now().isoformat()}",
        "document_analyzed": "{filename}",
        "text_length_analyzed": {len(text[:15000])},
        "confidence_score": 0.0-1.0,
        "sections_found": ["list of section types found"],
        "potential_gaps": ["areas that may need manual review"]
    }}
}}

IMPORTANT EXTRACTION RULES:
1. For "shall" and "must" - these create mandatory obligations
2. Look for "within X days of" patterns for relative deadlines
3. "Effective Date" is a common trigger - note all references
4. If you see "XXXX" or "[***]" or redaction marks, note financial term exists but is redacted
5. Extract ALL addresses completely including zip codes
6. Notice provisions often require BOTH email AND certified mail
7. Arbitration clauses may reference incorporated rules (e.g., "AAA Commercial Arbitration Rules")
8. Non-compete restrictions often have geographic and temporal scope
9. Indemnification clauses create ongoing obligations

Be thorough and extract EVERYTHING. If unsure, include it with a note."""

            response = self.claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8000,  # Large response needed
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                json_str = json_match.group(0) if json_match else response_text

            operational_data = json.loads(json_str)

            # Enhance with regex extraction for backup
            regex_data = self._regex_fallback_extraction(text, filename)

            # Merge - prefer AI but supplement with regex findings
            operational_data = self._merge_extractions(operational_data, regex_data)

            return operational_data

        except Exception as e:
            logger.error(f"AI extraction error: {str(e)}, falling back to regex")
            return self._regex_fallback_extraction(text, filename)

    def _regex_fallback_extraction(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Fallback extraction using regex patterns
        """
        logger.info("Using regex fallback for operational extraction")

        # Initialize result structure
        result = {
            "action_items": [],
            "conditional_obligations": [],
            "permanent_restrictions": [],
            "notice_contacts": [],
            "financial_terms": [],
            "jurisdiction_details": {},
            "critical_review_dates": [],
            "extraction_metadata": {
                "extraction_date": datetime.now().isoformat(),
                "document_analyzed": filename,
                "confidence_score": 0.5,
                "method": "regex_fallback",
                "sections_found": []
            }
        }

        # Extract action items (shall/must patterns)
        shall_must_pattern = r'((?:[A-Z][a-z]+(?: [A-Z][a-z]+)*)\s+(?:shall|must|will|agrees to)\s+([^.;]+(?:\.|;)))'
        matches = re.finditer(shall_must_pattern, text, re.MULTILINE)

        for match in matches:
            full_text = match.group(1)
            # Try to extract deadline from same sentence
            deadline_match = re.search(r'within\s+(\d+)\s+(days?|weeks?|months?|years?)', full_text, re.IGNORECASE)

            result["action_items"].append({
                "obligation": full_text.strip(),
                "responsible_party": "See document",
                "deadline_type": "relative" if deadline_match else "unknown",
                "deadline_date": None,
                "deadline_description": deadline_match.group(0) if deadline_match else "See document",
                "trigger_event": None,
                "urgency": "high",
                "consequences": "See document",
                "source_text": full_text.strip()
            })

        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)

        if emails:
            for email in set(emails):  # Unique emails
                result["notice_contacts"].append({
                    "contact_type": "unknown",
                    "party_name": "See document",
                    "email_addresses": [email],
                    "mailing_address": None,
                    "phone": None,
                    "fax": None,
                    "notice_methods_allowed": ["email"],
                    "notice_timing": "See document",
                    "source_section": "Extracted via pattern matching"
                })

        # Extract phone numbers
        phone_pattern = r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'
        phones = re.findall(phone_pattern, text)

        # Extract addresses (basic pattern)
        address_pattern = r'\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir)\.?[,\s]+[A-Z][a-z]+[,\s]+[A-Z]{2}\s+\d{5}(?:-\d{4})?'
        addresses = re.findall(address_pattern, text)

        # Extract financial amounts
        amount_pattern = r'\$[\d,]+(?:\.\d{2})?'
        redaction_pattern = r'\[?\*+\]?|XXXX|REDACTED'

        amounts = re.findall(amount_pattern, text)
        redactions = re.findall(redaction_pattern, text)

        for amount in set(amounts):
            # Get context
            amount_pos = text.find(amount)
            context_start = max(0, amount_pos - 100)
            context_end = min(len(text), amount_pos + 100)
            context = text[context_start:context_end]

            result["financial_terms"].append({
                "term_type": "unknown",
                "amount": amount,
                "amount_visible": True,
                "description": context.replace('\n', ' ').strip(),
                "payment_schedule": "See document",
                "responsible_party": "See document",
                "recipient_party": "See document",
                "trigger": None,
                "calculation_method": None,
                "source_text": context.replace('\n', ' ').strip()[:200]
            })

        if redactions:
            result["financial_terms"].append({
                "term_type": "redacted",
                "amount": "REDACTED",
                "amount_visible": False,
                "description": f"Financial terms present but redacted ({len(redactions)} redactions found)",
                "payment_schedule": "See document",
                "responsible_party": "See document",
                "recipient_party": "See document",
                "trigger": None,
                "calculation_method": None,
                "source_text": "Multiple redacted financial terms found in document"
            })

        # Extract governing law
        gov_law_pattern = r'governed by (?:the )?laws? of (?:the )?(?:State of )?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        gov_law_match = re.search(gov_law_pattern, text, re.IGNORECASE)

        if gov_law_match:
            result["jurisdiction_details"]["governing_law_state"] = gov_law_match.group(1)

        # Extract arbitration clause
        if re.search(r'arbitration', text, re.IGNORECASE):
            result["jurisdiction_details"]["arbitration_required"] = True

            # Try to find arbitration rules
            arb_rules_pattern = r'(AAA|JAMS|American Arbitration Association|Judicial Arbitration)'
            arb_rules_match = re.search(arb_rules_pattern, text, re.IGNORECASE)
            if arb_rules_match:
                result["jurisdiction_details"]["arbitration_rules"] = arb_rules_match.group(1)

        # Extract conditional obligations (if/then)
        conditional_pattern = r'(?:If|if)\s+([^,]+),\s+(?:then\s+)?([^.]+)\.'
        conditional_matches = re.finditer(conditional_pattern, text)

        for match in conditional_matches:
            result["conditional_obligations"].append({
                "condition": match.group(1).strip(),
                "trigger_event": match.group(1).strip(),
                "resulting_obligation": match.group(2).strip(),
                "responsible_party": "See document",
                "deadline": None,
                "alternative_path": None,
                "source_text": match.group(0)
            })

        result["extraction_metadata"]["sections_found"] = [
            "action_items" if result["action_items"] else None,
            "notice_contacts" if result["notice_contacts"] else None,
            "financial_terms" if result["financial_terms"] else None,
            "jurisdiction_details" if result["jurisdiction_details"] else None,
            "conditional_obligations" if result["conditional_obligations"] else None
        ]
        result["extraction_metadata"]["sections_found"] = [s for s in result["extraction_metadata"]["sections_found"] if s]

        return result

    def _merge_extractions(
        self,
        ai_data: Dict[str, Any],
        regex_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge AI and regex extractions, preferring AI but supplementing with regex
        """
        merged = ai_data.copy()

        # Add regex-found items that AI might have missed
        for key in ["action_items", "conditional_obligations", "permanent_restrictions",
                    "notice_contacts", "financial_terms", "critical_review_dates"]:
            if key in regex_data and regex_data[key]:
                # Add regex items not found by AI
                ai_items = merged.get(key, [])
                regex_items = regex_data[key]

                # Simple deduplication by source_text
                ai_texts = {item.get("source_text", "") for item in ai_items}

                for regex_item in regex_items:
                    if regex_item.get("source_text", "") not in ai_texts:
                        ai_items.append(regex_item)

                merged[key] = ai_items

        # Merge jurisdiction details
        if "jurisdiction_details" in regex_data:
            ai_juris = merged.get("jurisdiction_details", {})
            regex_juris = regex_data["jurisdiction_details"]

            for key, value in regex_juris.items():
                if value and not ai_juris.get(key):
                    ai_juris[key] = value

            merged["jurisdiction_details"] = ai_juris

        # Update metadata
        if "extraction_metadata" in merged:
            merged["extraction_metadata"]["enhanced_with_regex"] = True
            merged["extraction_metadata"]["regex_items_added"] = sum(
                len(regex_data.get(k, [])) for k in ["action_items", "notice_contacts", "financial_terms"]
            )

        return merged


# Global instance
enhanced_extractor = EnhancedDocumentExtractor()
