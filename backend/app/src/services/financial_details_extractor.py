"""
Enhanced Financial Details Extractor
Extracts detailed financial information from legal documents including:
- Loan breakdowns (SBA, MCA, Factoring)
- Insurance policy details
- Claims breakdowns with specific amounts
- Legal precedent citations
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import anthropic
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent.parent / '.env')
logger = logging.getLogger(__name__)


class FinancialDetailsExtractor:
    """
    Advanced extractor for detailed financial information in legal documents
    """

    def __init__(self):
        self.claude_client = None
        if os.getenv('ANTHROPIC_API_KEY'):
            self.claude_client = anthropic.Anthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                timeout=30.0
            )

    async def extract_financial_details(
        self,
        text: str,
        filename: str = "",
        basic_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract comprehensive financial details from legal document

        Args:
            text: Document text
            filename: Original filename
            basic_analysis: Optional basic analysis to enhance

        Returns:
            Dictionary with detailed financial extraction
        """
        if self.claude_client:
            return await self._ai_financial_extraction(text, filename, basic_analysis)
        else:
            return self._regex_financial_extraction(text, filename)

    async def _ai_financial_extraction(
        self,
        text: str,
        filename: str,
        basic_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use Claude AI for comprehensive financial extraction with smart truncation
        """
        try:
            # SMART TRUNCATION: Financial info is usually spread throughout
            # Keep beginning (header), middle samples, and end (totals/relief)
            text_length = len(text)
            max_chars = 60000  # Slightly larger for financial extraction

            if text_length > max_chars:
                logger.info(f"Large document ({text_length} chars) - using smart truncation for financial extraction")
                # Keep first 40%, middle 20%, and last 40%
                first_chunk = int(max_chars * 0.4)
                middle_chunk = int(max_chars * 0.2)
                last_chunk = int(max_chars * 0.4)

                # Calculate middle position
                middle_start = (text_length - middle_chunk) // 2

                text_to_analyze = (
                    text[:first_chunk] +
                    f"\n\n[... SECTION TRUNCATED ...]\n\n" +
                    text[middle_start:middle_start + middle_chunk] +
                    f"\n\n[... SECTION TRUNCATED - Document is {text_length} chars total ...]\n\n" +
                    text[-last_chunk:]
                )
                logger.info(f"Smart financial truncation: first {first_chunk}, middle {middle_chunk}, last {last_chunk} chars")
            else:
                text_to_analyze = text
                logger.info(f"Financial extraction: document size ({text_length} chars) within limits")

            # Prepare context
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

            prompt = f"""You are a financial forensics expert analyzing legal documents. Extract ALL detailed financial information with precision.

CRITICAL: Use DYNAMIC EXTRACTION - find actual data in the document, do NOT use hardcoded or example values.
Extract EXACTLY what appears in the document text. If something is not present, leave it null/empty.

{context}

DOCUMENT: {filename}
DOCUMENT SIZE: {text_length} characters
TEXT: {text_to_analyze}

Extract the following in structured JSON format (REPLACE ALL EXAMPLE VALUES with actual document data):

1. FINANCIAL TRANSACTIONS & DEBT DETAILS:
   - SBA Loans (with complete breakdown of allocations)
   - MCA (Merchant Cash Advance) Agreements
   - Factoring Agreements
   - Digital Advertising Debt
   - Total claims amounts
   - Any other debt obligations

2. INSURANCE POLICY INFORMATION:
   - Policy underwriter names (e.g., Lloyd's of London, specific syndicates)
   - Policy numbers
   - Coverage limits (combined and individual)
   - Policy period dates (exact start and end dates)
   - Type of coverage
   - Named insureds
   - Additional insureds
   - Premium amounts

3. CLAIMS BREAKDOWN:
   - Proofs of Claim (POC) with:
     * Claim number
     * Claimant name
     * Claimed amount (exact figures)
     * Claim type (secured/unsecured/priority)
     * Jurisdiction
     * Filing date
   - Scheduled claims with amounts
   - Total of all claims
   - Disputed vs undisputed amounts

4. LOAN BREAKDOWNS:
   - Total loan amount
   - Specific allocations (e.g., "Operating expenses: $X", "Equipment: $Y")
   - Interest rates
   - Payment terms
   - Collateral
   - Guarantors
   - Default provisions

5. LEGAL PRECEDENTS & CITATIONS:
   - Case citations (full citation format)
   - Statute references
   - Regulatory citations
   - Court rules cited
   - Precedent application to current case

   SPECIFICALLY LOOK FOR:
   - Bartenwerfer v. Buckley (community property liability)
   - 28 U.S.C. § 157 (bankruptcy jurisdiction)
   - 28 U.S.C. § 1334 (bankruptcy jurisdiction)
   - Any community property liability cases
   - Jurisdictional basis citations

6. TRANSACTION DETAILS:
   - Payment schedules
   - Wire transfer information
   - Account numbers (partially redacted if sensitive)
   - Transaction dates
   - Payment methods

Return ONLY valid JSON in this exact format:
{{
    "financial_transactions": [
        {{
            "transaction_type": "SBA Loan|MCA|Factoring|Advertising Debt|Other",
            "creditor_name": "Name of creditor",
            "total_amount": "$X,XXX,XXX.XX",
            "amount_numeric": 0.00,
            "breakdown": [
                {{
                    "category": "Operating expenses|Equipment|Inventory|etc",
                    "amount": "$X,XXX.XX",
                    "amount_numeric": 0.00,
                    "description": "Detailed description"
                }}
            ],
            "loan_number": "Loan/Agreement number if available",
            "origination_date": "YYYY-MM-DD or description",
            "maturity_date": "YYYY-MM-DD or description",
            "interest_rate": "X.X%",
            "payment_schedule": "Monthly, quarterly, etc",
            "collateral": "Description of collateral",
            "guarantors": ["List of guarantors"],
            "current_balance": "$X,XXX.XX",
            "source_text": "Verbatim text describing this transaction"
        }}
    ],

    "total_debt_summary": {{
        "total_claims_amount": "$XXX,XXX,XXX.XX",
        "total_claims_numeric": 0.00,
        "secured_debt": "$X,XXX.XX",
        "unsecured_debt": "$X,XXX.XX",
        "priority_debt": "$X,XXX.XX",
        "number_of_creditors": 0,
        "largest_creditor": "Name and amount"
    }},

    "insurance_policies": [
        {{
            "policy_number": "Policy number from document",
            "underwriter": "Actual underwriter name from document (Lloyd's of London, etc.)",
            "syndicate_numbers": ["Extract ANY/ALL syndicate numbers found - do NOT use example values"],
            "policy_type": "D&O|E&O|General Liability|Professional Liability|etc",
            "coverage_limit": "$X,XXX,XXX.XX",
            "coverage_limit_numeric": 0.00,
            "combined_limit": true|false,
            "policy_period_start": "YYYY-MM-DD",
            "policy_period_end": "YYYY-MM-DD",
            "named_insured": ["List of named insureds"],
            "additional_insureds": ["List if any"],
            "premium_amount": "$X,XXX.XX or null",
            "deductible": "$X,XXX.XX or null",
            "coverage_details": "Description of what's covered",
            "exclusions": "Description of exclusions",
            "source_text": "Verbatim policy information"
        }}
    ],

    "claims_breakdown": [
        {{
            "claim_number": "POC #X or Claim #X",
            "claim_type": "Proof of Claim|Scheduled Claim|Administrative Claim",
            "claimant_name": "Name of claimant",
            "claim_amount": "$X,XXX.XX",
            "claim_amount_numeric": 0.00,
            "claim_classification": "Secured|Unsecured|Priority",
            "priority_level": "If priority claim, specify level",
            "jurisdiction": "Court/jurisdiction",
            "filing_date": "YYYY-MM-DD or description",
            "claim_basis": "Brief description of claim basis",
            "disputed": true|false,
            "disputed_amount": "$X,XXX.XX if any",
            "allowed_amount": "$X,XXX.XX if determined",
            "source_text": "Verbatim claim description"
        }}
    ],

    "claims_summary": {{
        "total_proofs_of_claim": 0,
        "total_poc_amount": "$X,XXX,XXX.XX",
        "total_poc_numeric": 0.00,
        "total_scheduled_claims": 0,
        "total_scheduled_amount": "$X,XXX.XX",
        "total_scheduled_numeric": 0.00,
        "grand_total_claims": "$X,XXX,XXX.XX",
        "grand_total_numeric": 0.00,
        "disputed_claims_count": 0,
        "disputed_claims_amount": "$X,XXX.XX"
    }},

    "legal_precedents": [
        {{
            "citation": "Full case citation (e.g., Case Name, 123 F.3d 456 (9th Cir. 2020))",
            "citation_type": "Case Law|Statute|Regulation|Court Rule",
            "jurisdiction": "Federal|State|Circuit",
            "relevance": "How this precedent applies to current case",
            "key_holding": "Key legal principle from this precedent",
            "quoted_text": "Any quoted passages from the precedent",
            "distinguishing_factors": "How current case differs, if applicable"
        }}
    ],

    "payment_schedules": [
        {{
            "obligation_description": "What payment is for",
            "payment_amount": "$X,XXX.XX",
            "payment_frequency": "Monthly|Quarterly|Annual|One-time",
            "first_payment_date": "YYYY-MM-DD",
            "final_payment_date": "YYYY-MM-DD",
            "number_of_payments": 0,
            "payment_method": "Wire transfer|Check|ACH|etc",
            "account_information": "Bank account (partially redacted)",
            "late_payment_penalty": "Description of penalties"
        }}
    ],

    "summary_statistics": {{
        "total_claims_for_relief": 0,
        "total_monetary_exposure": "$XXX,XXX,XXX.XX",
        "total_monetary_exposure_numeric": 0.00,
        "breakdown_by_type": {{
            "secured_claims": "$X,XXX.XX",
            "unsecured_claims": "$X,XXX.XX",
            "priority_claims": "$X,XXX.XX",
            "contingent_claims": "$X,XXX.XX",
            "unliquidated_claims": "$X,XXX.XX"
        }},
        "creditor_statistics": {{
            "total_creditors": 0,
            "secured_creditors": 0,
            "unsecured_creditors": 0,
            "largest_creditor": "Name and amount",
            "smallest_creditor": "Name and amount"
        }}
    }},

    "timeline_of_events": [
        {{
            "event_date": "YYYY-MM-DD",
            "event_description": "Description of significant event",
            "event_type": "Filing|Payment|Default|Agreement|Court Order|etc",
            "parties_involved": ["Party names"],
            "financial_impact": "$X,XXX.XX if applicable",
            "legal_significance": "Why this date matters"
        }}
    ],

    "extraction_metadata": {{
        "extraction_date": "{datetime.now().isoformat()}",
        "document_analyzed": "{filename}",
        "text_length_analyzed": {len(text)},
        "confidence_score": 0.0-1.0,
        "financial_elements_found": ["list of types found"],
        "total_financial_amounts_identified": 0,
        "currency": "USD|EUR|etc",
        "potential_discrepancies": ["Note any inconsistencies in amounts"],
        "missing_critical_information": ["List of critical fields not found"],
        "data_quality_flags": ["Issues that need manual review"],
        "validation_status": "complete|incomplete|needs_review"
    }}
}}

IMPORTANT EXTRACTION RULES:
1. Extract EXACT amounts - do not round or estimate
2. Preserve all decimal places
3. Note if amounts are "approximately", "not less than", "up to", etc.
4. Flag any mathematical inconsistencies (e.g., subtotals don't match totals)
5. For insurance policies, extract syndicate numbers if Lloyd's of London
6. For claims, distinguish between filed amount and allowed amount
7. Extract complete legal citations in proper format
8. Note if financial information is redacted but referenced
9. Capture both the dollar amount string AND numeric value
10. Include source text for verification

Be extremely thorough - financial details are critical for legal analysis."""

            response = self.claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8000,
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

            financial_data = json.loads(json_str)

            # Enhance with regex extraction
            regex_data = self._regex_financial_extraction(text, filename)
            financial_data = self._merge_financial_extractions(financial_data, regex_data)

            # Validate and flag missing critical information
            financial_data = self._validate_financial_data(financial_data, text)

            return financial_data

        except Exception as e:
            logger.error(f"AI financial extraction error: {str(e)}, falling back to regex")
            return self._regex_financial_extraction(text, filename)

    def _regex_financial_extraction(self, text: str, filename: str) -> Dict[str, Any]:
        """
        DYNAMIC extraction using regex patterns - works on ANY bankruptcy document
        Extracts data by PATTERN MATCHING, not hardcoded values
        """
        logger.info("Using DYNAMIC regex patterns for financial extraction")

        result = {
            "financial_transactions": [],
            "total_debt_summary": {},
            "insurance_policies": [],
            "claims_breakdown": [],
            "claims_summary": {},
            "legal_precedents": [],
            "payment_schedules": [],
            "docket_numbers": [],
            "extraction_metadata": {
                "extraction_date": datetime.now().isoformat(),
                "document_analyzed": filename,
                "confidence_score": 0.5,
                "method": "regex_fallback",
                "extraction_type": "DYNAMIC - pattern-based, not hardcoded"
            }
        }

        # ============================================================
        # DOLLAR AMOUNT EXTRACTION - DYNAMIC PATTERN MATCHING
        # ============================================================
        # Pattern matches ANY dollar amount: $5,000,000 or $920,617.94 or $1.23
        amount_pattern = r'\$[\d,]+(?:\.\d{1,2})?'
        amounts = list(re.finditer(amount_pattern, text))

        logger.info(f"Found {len(amounts)} dollar amounts using DYNAMIC pattern matching")

        for match in amounts:
            amount_str = match.group(0)
            amount_numeric = float(amount_str.replace('$', '').replace(',', ''))

            # Get EXTENDED context (250 chars before/after for better understanding)
            start = max(0, match.start() - 250)
            end = min(len(text), match.end() + 250)
            context = text[start:end]

            # Extract line context for parent/child relationship detection
            line_context = self._extract_line_context(text, match.start(), match.end())

            # Calculate confidence based on context clarity
            confidence = self._calculate_confidence(context, amount_str)

            # DYNAMIC categorization based on surrounding keywords
            transaction_type, category_confidence = self._categorize_transaction(context)

            # Detect if this is part of a breakdown (indented, bulleted, or sub-item)
            is_breakdown_item, parent_description = self._detect_breakdown_relationship(
                text, match.start(), line_context
            )

            # Skip insurance amounts (handled separately)
            if re.search(r'insurance|policy|premium|coverage|limit', context, re.IGNORECASE):
                # Extract policy details
                policy_data = self._extract_policy_details(context, amount_str, amount_numeric, confidence)
                if policy_data:
                    result["insurance_policies"].append(policy_data)
                continue

            # Add to financial transactions with full metadata
            transaction = {
                "transaction_type": transaction_type,
                "total_amount": amount_str,
                "amount_numeric": amount_numeric,
                "context": context.replace('\n', ' ').strip()[:300],
                "source_text": line_context,
                "confidence": confidence,
                "category_confidence": category_confidence,
                "is_breakdown_item": is_breakdown_item,
                "parent_description": parent_description if is_breakdown_item else None,
                "position_in_document": match.start()
            }

            result["financial_transactions"].append(transaction)

        # ============================================================
        # DOCKET NUMBER EXTRACTION - DYNAMIC PATTERN
        # ============================================================
        # Matches: "Docket No. 631", "[Docket. 633]", "Docket Number 634-35"
        docket_patterns = [
            r'(?:Docket|Dkt\.?)\s*(?:No\.?|Number|Num\.?|#)\s*([\d\-]+)',
            r'\[Docket[^\]]*?([\d\-]+)\]',
            r'Case\s*(?:No\.?|Number)\s*([\d\-]+)'
        ]

        for pattern in docket_patterns:
            docket_matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in docket_matches:
                docket_num = match.group(1)
                context = self._get_context(text, match.start(), match.end(), 150)

                result["docket_numbers"].append({
                    "docket_number": docket_num,
                    "full_match": match.group(0),
                    "context": context,
                    "confidence": 0.9,
                    "position_in_document": match.start()
                })

        logger.info(f"Found {len(result['docket_numbers'])} docket numbers using DYNAMIC patterns")

        # ============================================================
        # CASE CITATION EXTRACTION - DYNAMIC PATTERN
        # ============================================================
        citation_patterns = [
            # Case v. Case, 123 F.3d 456 (9th Cir. 2020)
            r'([A-Z][a-z]+(?:\s+v\.?\s+|\s+vs\.?\s+)[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*\d+\s+[A-Z]\.(?:\d+d)?\s+\d+(?:\s*\([^)]+\s+\d{4}\))?',
            # Bartenwerfer v. Buckley
            r'[A-Z][a-z]+(?:\s+v\.?\s+|\s+vs\.?\s+)[A-Z][a-z]+,?\s*\d+\s+S\.\s*Ct\.',
            # U.S.C. statute citations
            r'\d+\s+U\.S\.C\.\s*§\s*\d+(?:\([a-z0-9]+\))?',
            # Federal Rules
            r'(?:Fed\.\s*R\.\s*(?:Civ\.\s*P\.|Bankr\.\s*P\.|App\.\s*P\.|Evid\.)|F\.R\.(?:C\.P\.|B\.P\.|A\.P\.|E\.))\s*\d+(?:\([a-z0-9]+\))?'
        ]

        for pattern in citation_patterns:
            citations = re.finditer(pattern, text, re.IGNORECASE)
            for match in citations:
                citation_text = match.group(0)
                context = self._get_context(text, match.start(), match.end(), 200)

                # Determine citation type
                citation_type = "Case Law"
                if "U.S.C." in citation_text or "U.S.C.A." in citation_text:
                    citation_type = "Statute"
                elif re.search(r'Fed\.\s*R\.|F\.R\.', citation_text):
                    citation_type = "Court Rule"

                result["legal_precedents"].append({
                    "citation": citation_text,
                    "citation_type": citation_type,
                    "context": context,
                    "source_text": match.group(0),
                    "confidence": 0.85,
                    "position_in_document": match.start()
                })

        logger.info(f"Found {len(result['legal_precedents'])} legal citations using DYNAMIC patterns")

        # ============================================================
        # INSURANCE POLICY EXTRACTION - DYNAMIC PATTERN
        # ============================================================
        # Extract Lloyd's of London with ANY syndicate numbers (not hardcoded)
        lloyds_pattern = r"Lloyd'?s\s+of\s+London.*?Syndicate[s]?\s*:?\s*([\d,\s\&and]+)"
        lloyds_matches = re.finditer(lloyds_pattern, text, re.IGNORECASE | re.DOTALL)

        for match in lloyds_matches:
            # Extract ALL syndicate numbers dynamically
            syndicates = re.findall(r'\d+', match.group(1))
            context = self._get_context(text, match.start(), match.end(), 300)

            if syndicates:
                policy_data = {
                    "underwriter": "Lloyd's of London",
                    "syndicate_numbers": syndicates,  # DYNAMIC - extracts ANY numbers found
                    "source_text": match.group(0),
                    "context": context,
                    "confidence": 0.9
                }

                # Look for policy numbers near this match
                policy_num_pattern = r'(?:Policy|Pol\.?)\s*(?:No\.?|Number|#)\s*([A-Z0-9]+)'
                policy_match = re.search(policy_num_pattern, context, re.IGNORECASE)
                if policy_match:
                    policy_data["policy_number"] = policy_match.group(1)

                result["insurance_policies"].append(policy_data)

        logger.info(f"Found {len(result['insurance_policies'])} insurance policies using DYNAMIC patterns")

        # ============================================================
        # CLAIMS EXTRACTION - DYNAMIC PATTERN
        # ============================================================
        # Matches: "POC #123", "Claim No. 456", "Proof of Claim 789"
        claim_patterns = [
            r'(?:POC|Proof\s+of\s+Claim)\s*#?\s*(\d+)',
            r'Claim\s*(?:No\.?|Number|#)\s*(\d+)',
            r'(?:Filed\s+)?Claim\s+(\d+)'
        ]

        for pattern in claim_patterns:
            claims = re.finditer(pattern, text, re.IGNORECASE)

            for match in claims:
                claim_num = match.group(1)

                # Get extended context to find associated amount and claimant
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 300)
                context = text[context_start:context_end]

                # Find associated dollar amount
                amount_match = re.search(amount_pattern, context)
                claim_data = {
                    "claim_number": claim_num,
                    "claim_type": "Proof of Claim" if "POC" in match.group(0).upper() else "Claim",
                    "source_text": context.replace('\n', ' ').strip()[:250],
                    "confidence": 0.85,
                    "position_in_document": match.start()
                }

                if amount_match:
                    claim_data["claim_amount"] = amount_match.group(0)
                    claim_data["claim_amount_numeric"] = float(
                        amount_match.group(0).replace('$', '').replace(',', '')
                    )
                    claim_data["confidence"] = 0.95

                # Try to extract claimant name (word before "Claim" or after "by")
                claimant_pattern = r'(?:by|filed\s+by|claimant)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
                claimant_match = re.search(claimant_pattern, context, re.IGNORECASE)
                if claimant_match:
                    claim_data["claimant_name"] = claimant_match.group(1)

                result["claims_breakdown"].append(claim_data)

        logger.info(f"Found {len(result['claims_breakdown'])} claims using DYNAMIC patterns")

        # ============================================================
        # DATES EXTRACTION - DYNAMIC PATTERN
        # ============================================================
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*\d{4}',
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}'
        ]

        dates_found = []
        for pattern in date_patterns:
            date_matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in date_matches:
                dates_found.append({
                    "date": match.group(0),
                    "context": self._get_context(text, match.start(), match.end(), 100),
                    "position": match.start()
                })

        result["dates_extracted"] = dates_found
        logger.info(f"Found {len(dates_found)} dates using DYNAMIC patterns")

        return result

    def _get_context(self, text: str, start: int, end: int, chars: int = 200) -> str:
        """
        Extract context around a match position
        """
        context_start = max(0, start - chars)
        context_end = min(len(text), end + chars)
        return text[context_start:context_end].replace('\n', ' ').strip()

    def _extract_line_context(self, text: str, start: int, end: int) -> str:
        """
        Extract the complete line where the match occurs
        """
        # Find start of line
        line_start = text.rfind('\n', 0, start) + 1
        # Find end of line
        line_end = text.find('\n', end)
        if line_end == -1:
            line_end = len(text)

        return text[line_start:line_end].strip()

    def _calculate_confidence(self, context: str, amount_str: str) -> float:
        """
        Calculate confidence score based on context quality
        Higher confidence for amounts with clear descriptive context
        """
        confidence = 0.5  # Base confidence

        # Increase confidence for clear financial keywords
        high_confidence_keywords = [
            r'total', r'amount', r'loan', r'debt', r'payment', r'balance',
            r'claim', r'relief', r'damages', r'liability', r'obligation'
        ]

        for keyword in high_confidence_keywords:
            if re.search(keyword, context, re.IGNORECASE):
                confidence += 0.1
                if confidence >= 0.95:
                    break

        # Decrease confidence for ambiguous contexts
        ambiguous_keywords = [r'up to', r'approximately', r'about', r'around', r'estimated']
        for keyword in ambiguous_keywords:
            if re.search(keyword, context, re.IGNORECASE):
                confidence -= 0.1

        # Higher confidence if amount appears with specific descriptors
        if re.search(r'(?:in the amount of|sum of|total of)\s+\$', context, re.IGNORECASE):
            confidence += 0.15

        return max(0.3, min(0.99, confidence))

    def _categorize_transaction(self, context: str) -> tuple[str, float]:
        """
        Dynamically categorize transaction type based on context keywords
        Returns (transaction_type, confidence)
        """
        categories = {
            "SBA Loan": [r'SBA', r'Small Business Administration', r'7\(a\)\s+loan'],
            "MCA": [r'MCA', r'merchant cash advance', r'advance agreement'],
            "Factoring": [r'factor', r'factoring agreement', r'receivables'],
            "Advertising Debt": [r'advertis', r'marketing', r'digital marketing', r'ad spend'],
            "Insurance Premium": [r'premium', r'insurance payment'],
            "Legal Fees": [r'attorney.{0,20}fee', r'legal fee', r'counsel fee'],
            "Court Costs": [r'court cost', r'filing fee', r'administrative fee'],
            "Loan": [r'loan', r'borrowed', r'lending'],
            "Debt": [r'debt', r'obligation', r'owe', r'owing'],
            "Claim": [r'claim for', r'damages', r'relief'],
            "Payment": [r'payment', r'paid', r'remit'],
            "Settlement": [r'settlement', r'settle'],
            "Judgment": [r'judgment', r'awarded']
        }

        best_match = "Other"
        best_confidence = 0.4

        for category, patterns in categories.items():
            for pattern in patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    # Calculate confidence based on pattern specificity
                    confidence = 0.7 + (0.1 * len(pattern.split()))
                    if confidence > best_confidence:
                        best_match = category
                        best_confidence = min(0.95, confidence)

        return best_match, best_confidence

    def _detect_breakdown_relationship(
        self, text: str, position: int, line_context: str
    ) -> tuple[bool, Optional[str]]:
        """
        Detect if this amount is part of a breakdown (sub-item of parent category)
        Returns (is_breakdown_item, parent_description)
        """
        # Find the line
        line_start = text.rfind('\n', 0, position) + 1

        # Check for indentation (spaces or tabs at start of line)
        line_prefix = text[line_start:position]
        is_indented = bool(re.match(r'^[\s\t]+', line_prefix))

        # Check for bullet points or list markers
        has_bullet = bool(re.search(r'^[\s\t]*[-•◦○▪▫∙⋅*]\s', line_context))

        # Check for sub-item indicators
        is_sub_item = bool(re.search(r'^[\s\t]*[a-z]\)|^[\s\t]*\([a-z]\)|^[\s\t]*[ivx]+\.', line_context, re.IGNORECASE))

        is_breakdown_item = is_indented or has_bullet or is_sub_item

        parent_description = None
        if is_breakdown_item:
            # Try to find parent category by looking at previous non-indented line
            lines_before = text[:line_start].split('\n')

            # Search backwards for a non-indented line with descriptive text
            for i in range(len(lines_before) - 1, max(0, len(lines_before) - 10), -1):
                prev_line = lines_before[i].strip()

                # Skip empty lines
                if not prev_line:
                    continue

                # Check if this line is NOT indented (parent category)
                if not re.match(r'^[\s\t]+', lines_before[i]):
                    # This is likely the parent category
                    # Extract meaningful text (remove dollar amounts for cleaner description)
                    parent = re.sub(r'\$[\d,]+(?:\.\d{2})?', '', prev_line).strip()
                    if len(parent) > 5:  # Reasonable description length
                        parent_description = parent[:100]  # Limit length
                        break

        return is_breakdown_item, parent_description

    def _extract_policy_details(
        self, context: str, amount_str: str, amount_numeric: float, confidence: float
    ) -> Optional[Dict[str, Any]]:
        """
        Extract detailed insurance policy information from context
        """
        policy_data = {
            "coverage_limit": amount_str,
            "coverage_limit_numeric": amount_numeric,
            "confidence": confidence,
            "source_text": context[:300]
        }

        # Extract policy number
        policy_num_patterns = [
            r'(?:Policy|Pol\.?)\s*(?:No\.?|Number|#)\s*([A-Z0-9]+)',
            r'Policy\s+([A-Z]\d+[A-Z]?\d+)'
        ]

        for pattern in policy_num_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                policy_data["policy_number"] = match.group(1)
                break

        # Extract underwriter
        underwriter_patterns = [
            r"(Lloyd'?s\s+of\s+London)",
            r'underwritten\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
            r'underwriter:?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})'
        ]

        for pattern in underwriter_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                policy_data["underwriter"] = match.group(1)
                break

        # Extract policy type
        policy_types = {
            "D&O": r'(?:D\s*&\s*O|Directors?\s+and\s+Officers?)',
            "E&O": r'(?:E\s*&\s*O|Errors?\s+and\s+Omissions?)',
            "General Liability": r'General\s+Liability',
            "Professional Liability": r'Professional\s+Liability',
            "Commercial": r'Commercial\s+(?:General\s+)?Liability'
        }

        for policy_type, pattern in policy_types.items():
            if re.search(pattern, context, re.IGNORECASE):
                policy_data["policy_type"] = policy_type
                break

        # Extract policy dates
        date_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4})'
        dates = re.findall(date_pattern, context)
        if len(dates) >= 2:
            policy_data["policy_period_start"] = dates[0]
            policy_data["policy_period_end"] = dates[1]
        elif len(dates) == 1:
            # Try to find "to" or "through" indicating period
            if re.search(r'(?:from|effective)\s+\d{1,2}/\d{1,2}/\d{2,4}\s+(?:to|through)', context, re.IGNORECASE):
                policy_data["policy_period_start"] = dates[0]

        return policy_data if len(policy_data) > 3 else None

    def _merge_financial_extractions(
        self,
        ai_data: Dict[str, Any],
        regex_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge AI and regex financial extractions
        """
        merged = ai_data.copy()

        # Add regex-found items that AI might have missed
        for key in ["financial_transactions", "insurance_policies", "claims_breakdown", "legal_precedents"]:
            if key in regex_data and regex_data[key]:
                ai_items = merged.get(key, [])
                regex_items = regex_data[key]

                # Simple deduplication
                ai_texts = {str(item.get("source_text", "")) for item in ai_items}

                for regex_item in regex_items:
                    if str(regex_item.get("source_text", "")) not in ai_texts:
                        ai_items.append(regex_item)

                merged[key] = ai_items

        # Update metadata
        if "extraction_metadata" in merged:
            merged["extraction_metadata"]["enhanced_with_regex"] = True

        return merged

    def _validate_financial_data(
        self,
        financial_data: Dict[str, Any],
        original_text: str
    ) -> Dict[str, Any]:
        """
        Validate extracted financial data and flag missing critical information
        """
        missing = []
        quality_flags = []

        # Check for critical financial information
        if not financial_data.get("financial_transactions"):
            missing.append("No financial transactions identified")

        if not financial_data.get("total_debt_summary") or not financial_data.get("total_debt_summary", {}).get("total_claims_amount"):
            missing.append("Total debt/claims amount not found")

        if not financial_data.get("legal_precedents"):
            quality_flags.append("No legal precedents cited in document")

        # Check for specific important precedents
        precedents = financial_data.get("legal_precedents", [])
        has_bartenwerfer = any("Bartenwerfer" in str(p.get("citation", "")) for p in precedents)
        has_28_usc_157 = any("28 U.S.C." in str(p.get("citation", "")) and "157" in str(p.get("citation", "")) for p in precedents)
        has_28_usc_1334 = any("28 U.S.C." in str(p.get("citation", "")) and "1334" in str(p.get("citation", "")) for p in precedents)

        # Check original text for these citations if not found by AI
        if not has_bartenwerfer and re.search(r'Bartenwerfer.*Buckley', original_text, re.IGNORECASE):
            quality_flags.append("Bartenwerfer v. Buckley mentioned but not properly extracted")

        if not has_28_usc_157 and re.search(r'28\s+U\.S\.C\.\s*§?\s*157', original_text):
            quality_flags.append("28 U.S.C. § 157 mentioned but not properly extracted")

        if not has_28_usc_1334 and re.search(r'28\s+U\.S\.C\.\s*§?\s*1334', original_text):
            quality_flags.append("28 U.S.C. § 1334 mentioned but not properly extracted")

        # Check for timeline
        if not financial_data.get("timeline_of_events"):
            missing.append("Timeline of key events not identified")

        # Check for summary statistics
        if not financial_data.get("summary_statistics"):
            missing.append("Summary statistics not calculated")

        # Validate dollar amount formatting
        total_amounts_found = 0
        for transaction in financial_data.get("financial_transactions", []):
            if transaction.get("amount_numeric"):
                total_amounts_found += 1
                # Validate formatting
                if transaction.get("total_amount"):
                    amount_str = transaction["total_amount"]
                    # Should be in format $X,XXX.XX
                    if not re.match(r'^\$[\d,]+(?:\.\d{2})?$', amount_str):
                        quality_flags.append(f"Amount formatting inconsistent: {amount_str}")

        if total_amounts_found == 0:
            missing.append("No financial amounts with numeric values found")

        # Check for claims breakdown if this appears to be a bankruptcy/litigation doc
        is_litigation = any(word in original_text.lower() for word in ['plaintiff', 'defendant', 'claim', 'relief', 'damages'])
        if is_litigation and not financial_data.get("claims_breakdown"):
            missing.append("Claims breakdown not found in litigation document")

        # Determine validation status
        if missing:
            validation_status = "incomplete"
        elif quality_flags:
            validation_status = "needs_review"
        else:
            validation_status = "complete"

        # Update metadata
        if "extraction_metadata" not in financial_data:
            financial_data["extraction_metadata"] = {}

        financial_data["extraction_metadata"]["missing_critical_information"] = missing
        financial_data["extraction_metadata"]["data_quality_flags"] = quality_flags
        financial_data["extraction_metadata"]["validation_status"] = validation_status
        financial_data["extraction_metadata"]["total_financial_amounts_identified"] = total_amounts_found

        return financial_data

    def _format_dollar_amount(self, amount: float) -> str:
        """
        Format dollar amount consistently as $X,XXX.XX
        Ensures searchability and precision
        """
        # Format with thousands separator and exactly 2 decimal places
        return f"${amount:,.2f}"

    def _parse_dollar_amount(self, amount_str: str) -> float:
        """
        Parse dollar amount string to numeric value
        Handles various formats: $1,234.56, $1234.56, 1234.56, etc.
        """
        try:
            # Remove currency symbols and whitespace
            cleaned = amount_str.replace('$', '').replace(',', '').strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return 0.0


# Global instance
financial_extractor = FinancialDetailsExtractor()
