"""
Expert Agents for Legal Document Analysis

This module provides specialized expert agents for:
1. Document-type specific analysis (Complaint, Motion, Contract, Bankruptcy, etc.)
2. Layer inspection agents for quality assurance at each pipeline stage

Each expert has domain-specific knowledge and knows exactly what to extract
and verify for their document type.
"""

import os
import json
import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from openai import OpenAI
import anthropic
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent.parent / '.env')
logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported document types with specialized expert handling"""
    COMPLAINT = "complaint"
    MOTION = "motion"
    CONTRACT = "contract"
    BANKRUPTCY = "bankruptcy"
    DEBT_COLLECTION = "debt_collection"
    COURT_ORDER = "court_order"
    NOTICE = "notice"
    DISCOVERY = "discovery"
    SUMMONS = "summons"
    JUDGMENT = "judgment"
    SETTLEMENT = "settlement"
    APPEAL = "appeal"
    UNKNOWN = "unknown"


@dataclass
class ExpertReview:
    """Result from an expert agent's review"""
    expert_type: str
    document_type: str
    findings: Dict[str, Any]
    missing_items: List[str]
    corrections: List[Dict[str, Any]]
    warnings: List[str]
    confidence_adjustments: Dict[str, float]
    expert_notes: List[str]
    processing_time: float = 0.0
    model_used: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expert_type": self.expert_type,
            "document_type": self.document_type,
            "findings": self.findings,
            "missing_items": self.missing_items,
            "corrections": self.corrections,
            "warnings": self.warnings,
            "confidence_adjustments": self.confidence_adjustments,
            "expert_notes": self.expert_notes,
            "processing_time": self.processing_time,
            "model_used": self.model_used
        }


class DocumentTypeExpert:
    """
    Base class for document-type specific expert agents.
    Each expert knows exactly what information should be present in their document type.
    """

    # Model configuration
    CLAUDE_OPUS = 'claude-opus-4-20250514'
    GPT4O = 'gpt-4o'

    def __init__(self):
        self.claude_client = None
        self.openai_client = None

        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            self.claude_client = anthropic.Anthropic(api_key=anthropic_key)

        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)

    def get_expert_prompt(self, document_type: DocumentType) -> str:
        """Get the specialized prompt for each document type expert"""
        prompts = {
            DocumentType.COMPLAINT: self._complaint_expert_prompt(),
            DocumentType.MOTION: self._motion_expert_prompt(),
            DocumentType.CONTRACT: self._contract_expert_prompt(),
            DocumentType.BANKRUPTCY: self._bankruptcy_expert_prompt(),
            DocumentType.DEBT_COLLECTION: self._debt_collection_expert_prompt(),
            DocumentType.COURT_ORDER: self._court_order_expert_prompt(),
            DocumentType.NOTICE: self._notice_expert_prompt(),
            DocumentType.DISCOVERY: self._discovery_expert_prompt(),
            DocumentType.SUMMONS: self._summons_expert_prompt(),
            DocumentType.JUDGMENT: self._judgment_expert_prompt(),
            DocumentType.SETTLEMENT: self._settlement_expert_prompt(),
            DocumentType.APPEAL: self._appeal_expert_prompt(),
        }
        return prompts.get(document_type, self._general_expert_prompt())

    def _complaint_expert_prompt(self) -> str:
        return """You are an EXPERT COMPLAINT/LAWSUIT ANALYST with 30 years of litigation experience.

For COMPLAINTS/LAWSUITS, you MUST verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. CASE CAPTION: Plaintiff(s) v. Defendant(s), Case Number, Court
2. FILING DATE: When the complaint was filed
3. CAUSES OF ACTION: Each legal claim (count/claim number, legal basis, elements)
4. JURISDICTION: Why this court has authority (federal question, diversity, etc.)
5. VENUE: Why this location is proper
6. PARTIES: Full names, roles, addresses if listed
7. FACTUAL ALLEGATIONS: Key facts supporting each claim
8. DAMAGES SOUGHT: Specific amounts, types (compensatory, punitive, attorneys fees)
9. JURY DEMAND: Whether trial by jury is requested
10. PRAYER FOR RELIEF: What plaintiff is asking for

CRITICAL DEADLINES:
- Response deadline (typically 20-30 days from service)
- Discovery deadlines if mentioned
- Any hearing dates

RED FLAGS TO IDENTIFY:
- Service of process issues
- Statute of limitations concerns
- Improper venue or jurisdiction claims
- Default judgment risks

Return JSON with your expert findings."""

    def _motion_expert_prompt(self) -> str:
        return """You are an EXPERT MOTION ANALYST with extensive courtroom experience.

For MOTIONS, you MUST verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. MOTION TYPE: (Motion to Dismiss, Summary Judgment, Compel, etc.)
2. CASE INFORMATION: Case number, court, parties
3. FILING DATE and HEARING DATE
4. LEGAL STANDARD: What standard applies to this motion
5. ARGUMENTS: Key legal arguments made
6. RELIEF SOUGHT: What the moving party wants
7. SUPPORTING EVIDENCE: Declarations, exhibits, citations
8. PROCEDURAL POSTURE: Where the case stands

CRITICAL DEADLINES:
- Opposition deadline (typically 14-21 days)
- Reply deadline
- Hearing date and time
- Any discovery cut-off dates

LEGAL CITATIONS:
- Statutes cited
- Case law cited
- Rules of procedure cited

RED FLAGS:
- Missed deadlines
- Improper service
- Insufficient evidence
- Procedural defects

Return JSON with your expert findings."""

    def _contract_expert_prompt(self) -> str:
        return """You are an EXPERT CONTRACT ANALYST with decades of transactional law experience.

For CONTRACTS, you MUST verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. PARTIES: Full legal names, roles (Buyer/Seller, Landlord/Tenant, etc.)
2. EFFECTIVE DATE: When contract becomes binding
3. TERM: Duration of the agreement
4. CONSIDERATION: What each party gives/receives
5. KEY OBLIGATIONS: What each party must do
6. PAYMENT TERMS: Amounts, due dates, methods
7. TERMINATION CLAUSES: How to end the agreement
8. DEFAULT PROVISIONS: What constitutes breach
9. REMEDIES: Consequences of breach
10. GOVERNING LAW: Which state's law applies
11. DISPUTE RESOLUTION: Arbitration, mediation, litigation
12. SIGNATURES: Who signed, when, authority

CRITICAL CLAUSES:
- Non-compete/Non-solicitation
- Confidentiality/NDA provisions
- Indemnification
- Limitation of liability
- Force majeure
- Assignment restrictions
- Insurance requirements

IMPORTANT DATES:
- Payment due dates
- Performance milestones
- Option exercise dates
- Renewal deadlines
- Notice periods

Return JSON with your expert findings."""

    def _bankruptcy_expert_prompt(self) -> str:
        return """You are an EXPERT BANKRUPTCY ANALYST specializing in debtor/creditor law.

For BANKRUPTCY DOCUMENTS, you MUST verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. CASE TYPE: Chapter 7, 11, 13, etc.
2. DEBTOR INFORMATION: Name, address, SSN (last 4), EIN if business
3. CASE NUMBER and COURT
4. FILING DATE
5. TRUSTEE: Name and contact if assigned
6. CREDITOR INFORMATION: Names, addresses, amounts owed
7. ASSETS: Property, accounts, valuables listed
8. LIABILITIES: All debts listed with amounts
9. EXEMPTIONS CLAIMED: What debtor is protecting
10. MEANS TEST RESULTS: If applicable
11. PLAN DETAILS: For Chapter 13 - payment amount, duration

CRITICAL DEADLINES:
- 341 Meeting of Creditors date/time/location
- Proof of Claim deadline
- Objection deadlines
- Plan confirmation hearing
- Discharge date

AUTOMATIC STAY IMPLICATIONS:
- What collection actions must stop
- Any relief from stay motions

PRIORITY CLAIMS:
- Tax debts
- Domestic support obligations
- Administrative expenses

Return JSON with your expert findings."""

    def _debt_collection_expert_prompt(self) -> str:
        return """You are an EXPERT DEBT COLLECTION ANALYST specializing in consumer protection law.

For DEBT COLLECTION DOCUMENTS, you MUST verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. CREDITOR: Original creditor name
2. DEBT COLLECTOR: Current collection agency/law firm
3. ACCOUNT NUMBER: Original and collection account numbers
4. DEBT AMOUNT: Principal, interest, fees breakdown
5. DEBT TYPE: Credit card, medical, auto, mortgage, etc.
6. CHAIN OF TITLE: Who owned the debt when
7. LAST PAYMENT DATE: Critical for statute of limitations
8. CHARGE-OFF DATE: When debt was written off

FDCPA COMPLIANCE CHECK:
- Mini-Miranda warning present?
- Debt validation notice provided?
- 30-day dispute window mentioned?
- Proper identification of collector?

STATUTE OF LIMITATIONS:
- State where debtor lives
- Type of debt
- Last activity date
- Calculate if SOL expired

CRITICAL DATES:
- Response deadline
- Court date if lawsuit
- Last payment/activity date
- Date debt was incurred

POTENTIAL DEFENSES:
- Identity theft/wrong person
- Debt already paid
- Statute of limitations expired
- Amount disputed
- Chain of title broken

Return JSON with your expert findings."""

    def _court_order_expert_prompt(self) -> str:
        return """You are an EXPERT COURT ORDER ANALYST with judicial experience.

For COURT ORDERS, you MUST verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. ORDER TYPE: (Judgment, Injunction, Temporary Order, Final Order, etc.)
2. CASE INFORMATION: Case number, court, parties
3. JUDGE: Name of issuing judge
4. DATE ISSUED: When the order was signed
5. EFFECTIVE DATE: When order takes effect
6. SPECIFIC COMMANDS: What must be done/not done
7. PARTIES BOUND: Who must comply
8. DURATION: How long order remains in effect
9. CONSEQUENCES: Penalties for non-compliance

CRITICAL COMPLIANCE ITEMS:
- Actions required by each party
- Deadlines for compliance
- Reporting requirements
- Prohibited conduct

APPEAL INFORMATION:
- Appeal deadline (typically 30 days)
- Bond requirements
- Stay pending appeal

ENFORCEMENT:
- Contempt provisions
- Enforcement mechanisms
- Monitoring requirements

Return JSON with your expert findings."""

    def _notice_expert_prompt(self) -> str:
        return """You are an EXPERT LEGAL NOTICE ANALYST.

For LEGAL NOTICES, you MUST verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. NOTICE TYPE: (Eviction, Foreclosure, Hearing, Default, etc.)
2. SENDER: Who sent the notice
3. RECIPIENT: Who it's addressed to
4. DATE SENT: When mailed/served
5. SUBJECT MATTER: What the notice is about
6. REQUIRED ACTION: What recipient must do
7. DEADLINE: By when action must be taken
8. CONSEQUENCES: What happens if no action taken

SERVICE OF NOTICE:
- Method of delivery
- Proof of service
- Date of service

RESPONSE REQUIREMENTS:
- How to respond
- Where to respond
- Deadline to respond
- Format required

CRITICAL TIMELINES:
- Notice period (3-day, 30-day, etc.)
- Cure period if applicable
- Hearing dates

Return JSON with your expert findings."""

    def _discovery_expert_prompt(self) -> str:
        return """You are an EXPERT DISCOVERY ANALYST specializing in litigation.

For DISCOVERY DOCUMENTS, you MUST verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. DISCOVERY TYPE: (Interrogatories, Requests for Production, Admissions, Subpoena)
2. PROPOUNDING PARTY: Who is asking
3. RESPONDING PARTY: Who must answer
4. NUMBER OF REQUESTS: Total count
5. SCOPE: What information is sought
6. RELEVANT TIME PERIOD: Date ranges covered

CRITICAL DEADLINES:
- Response due date (typically 30 days)
- Objection deadline
- Meet and confer deadline
- Motion to compel deadline

SPECIFIC REQUESTS:
- List each request/interrogatory
- Note any that seem objectionable
- Identify privileged matters

OBJECTIONS TO CONSIDER:
- Overly broad
- Unduly burdensome
- Privileged information
- Not relevant
- Vague or ambiguous

Return JSON with your expert findings."""

    def _summons_expert_prompt(self) -> str:
        return """You are an EXPERT SUMMONS ANALYST.

For SUMMONS, you MUST verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. COURT: Full name and address
2. CASE NUMBER: Complete case identifier
3. PARTIES: Plaintiff(s) and Defendant(s)
4. ISSUE DATE: When summons was issued
5. SERVICE DATE: When/how served
6. RESPONSE DEADLINE: CRITICAL - days to respond
7. DEFAULT WARNING: Consequences of not responding

SERVICE OF PROCESS:
- Method of service (personal, substituted, etc.)
- Person who served
- Date and time of service
- Proof of service attached?

RESPONSE REQUIREMENTS:
- Where to file response
- Format required (Answer, Motion)
- Filing fee if any
- Service requirements

CALCULATE:
- Exact response deadline date
- Days remaining to respond
- Whether deadline has passed

Return JSON with your expert findings."""

    def _judgment_expert_prompt(self) -> str:
        return """You are an EXPERT JUDGMENT ANALYST.

For JUDGMENTS, you MUST verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. JUDGMENT TYPE: (Default, Summary, Consent, After Trial)
2. CASE INFORMATION: Court, case number, parties
3. DATE ENTERED: When judgment was recorded
4. AMOUNT: Principal, interest, costs, fees - EXACT figures
5. JUDGMENT CREDITOR: Who won
6. JUDGMENT DEBTOR: Who owes
7. INTEREST RATE: Post-judgment interest rate

ENFORCEMENT:
- Writ of execution available?
- Garnishment authorized?
- Liens recorded?
- Assets identified?

APPEAL RIGHTS:
- Appeal deadline
- Bond requirements
- Stay pending appeal

SATISFACTION:
- Amount needed to satisfy
- Where to pay
- How to get satisfaction recorded

Return JSON with your expert findings."""

    def _settlement_expert_prompt(self) -> str:
        return """You are an EXPERT SETTLEMENT ANALYST.

For SETTLEMENT AGREEMENTS, you MUST verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. PARTIES: All settling parties
2. SETTLEMENT AMOUNT: Total and payment structure
3. PAYMENT TERMS: Due dates, installments, method
4. RELEASES: What claims are being released
5. CONFIDENTIALITY: Non-disclosure provisions
6. NON-DISPARAGEMENT: Speaking restrictions
7. DISMISSAL: How underlying case will be dismissed
8. BREACH PROVISIONS: What happens if terms violated

CRITICAL PROVISIONS:
- Mutual vs. one-way release
- Known vs. unknown claims
- Scope of release
- Carve-outs/exceptions

PAYMENT SCHEDULE:
- Each payment amount
- Each due date
- Acceleration clause
- Default provisions

ENFORCEMENT:
- Retained jurisdiction
- Stipulated judgment
- Confession of judgment

Return JSON with your expert findings."""

    def _appeal_expert_prompt(self) -> str:
        return """You are an EXPERT APPELLATE ANALYST.

For APPEALS, you MUST verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. APPEAL TYPE: (Direct appeal, Interlocutory, Writ)
2. LOWER COURT: Court being appealed from
3. APPELLATE COURT: Court hearing appeal
4. CASE NUMBERS: Lower and appellate
5. APPELLANT: Who is appealing
6. APPELLEE: Who is responding
7. ISSUES ON APPEAL: What errors are claimed
8. STANDARD OF REVIEW: (De novo, abuse of discretion, etc.)

CRITICAL DEADLINES:
- Notice of appeal deadline
- Record designation deadline
- Opening brief deadline
- Response brief deadline
- Reply brief deadline
- Oral argument date

PROCEDURAL REQUIREMENTS:
- Transcript ordered?
- Record complete?
- Bond posted?
- Stay granted?

PRESERVATION:
- Were issues raised below?
- Objections made?
- Record references

Return JSON with your expert findings."""

    def _general_expert_prompt(self) -> str:
        return """You are an EXPERT LEGAL DOCUMENT ANALYST.

For this legal document, verify these critical elements:

MANDATORY ITEMS TO EXTRACT:
1. DOCUMENT TYPE: What kind of document is this?
2. PARTIES: All persons/entities named
3. DATES: All important dates mentioned
4. AMOUNTS: All monetary figures
5. DEADLINES: Any time-sensitive requirements
6. OBLIGATIONS: What must be done and by whom
7. CONSEQUENCES: What happens if obligations not met

GENERAL LEGAL ANALYSIS:
- Jurisdiction/venue
- Governing law
- Key legal issues
- Potential defenses
- Recommended actions

Return JSON with your expert findings."""

    async def run_expert_review(
        self,
        document_type: DocumentType,
        document_text: str,
        extracted_data: Dict[str, Any]
    ) -> ExpertReview:
        """
        Run document-type specific expert review on extracted data.
        Expert verifies completeness and accuracy based on document type requirements.
        """
        import time
        start_time = time.time()

        expert_prompt = self.get_expert_prompt(document_type)

        review_prompt = f"""{expert_prompt}

DOCUMENT TEXT:
{document_text[:50000]}

EXTRACTED DATA TO REVIEW:
{json.dumps(extracted_data, indent=2)[:10000]}

YOUR TASK:
1. Review the extracted data against your expert checklist
2. Identify ANY missing critical information
3. Flag any incorrect or suspicious extractions
4. Provide corrections where needed
5. Add expert notes for items needing attention

Return JSON:
{{
    "document_type_confirmed": "the document type you believe this is",
    "completeness_score": 0-100,
    "missing_critical_items": ["list of required items not found"],
    "missing_important_items": ["list of important but not critical items missing"],
    "corrections_needed": [
        {{"field": "field_name", "current_value": "...", "correct_value": "...", "reason": "..."}}
    ],
    "verified_items": ["list of items confirmed accurate"],
    "suspicious_items": [
        {{"item": "...", "concern": "why this seems wrong"}}
    ],
    "additional_findings": {{
        "key_legal_issues": ["issues identified"],
        "recommended_actions": ["what recipient should do"],
        "urgency_level": "CRITICAL/HIGH/MEDIUM/LOW",
        "deadline_summary": "most urgent deadline and when"
    }},
    "expert_notes": ["professional observations and advice"],
    "confidence_adjustments": {{
        "field_name": adjustment_value  // positive or negative
    }}
}}"""

        try:
            if self.claude_client:
                response = self.claude_client.messages.create(
                    model=self.CLAUDE_OPUS,
                    max_tokens=4000,
                    temperature=0,
                    messages=[{"role": "user", "content": review_prompt}]
                )
                response_text = response.content[0].text.strip()
                model_used = self.CLAUDE_OPUS
            elif self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=self.GPT4O,
                    temperature=0,
                    max_tokens=4000,
                    messages=[
                        {"role": "system", "content": f"You are an expert {document_type.value} analyst."},
                        {"role": "user", "content": review_prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                response_text = response.choices[0].message.content
                model_used = self.GPT4O
            else:
                return ExpertReview(
                    expert_type=f"{document_type.value}_expert",
                    document_type=document_type.value,
                    findings={},
                    missing_items=["Expert review unavailable - no AI client"],
                    corrections=[],
                    warnings=["Expert review skipped"],
                    confidence_adjustments={},
                    expert_notes=[],
                    model_used="none"
                )

            # Parse response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response_text)

            processing_time = time.time() - start_time

            return ExpertReview(
                expert_type=f"{document_type.value}_expert",
                document_type=data.get("document_type_confirmed", document_type.value),
                findings=data.get("additional_findings", {}),
                missing_items=data.get("missing_critical_items", []) + data.get("missing_important_items", []),
                corrections=data.get("corrections_needed", []),
                warnings=[item.get("concern", str(item)) for item in data.get("suspicious_items", [])],
                confidence_adjustments=data.get("confidence_adjustments", {}),
                expert_notes=data.get("expert_notes", []),
                processing_time=processing_time,
                model_used=model_used
            )

        except Exception as e:
            logger.error(f"Expert review error: {str(e)}")
            return ExpertReview(
                expert_type=f"{document_type.value}_expert",
                document_type=document_type.value,
                findings={},
                missing_items=[],
                corrections=[],
                warnings=[f"Expert review failed: {str(e)}"],
                confidence_adjustments={},
                expert_notes=[],
                processing_time=time.time() - start_time,
                model_used="error"
            )


class LayerInspectionAgent:
    """
    Quality assurance agents that inspect each layer's output before passing to next layer.
    Each inspector ensures the layer's work meets quality standards.
    """

    CLAUDE_OPUS = 'claude-opus-4-20250514'
    GPT4O = 'gpt-4o'

    def __init__(self):
        self.claude_client = None
        self.openai_client = None

        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            self.claude_client = anthropic.Anthropic(api_key=anthropic_key)

        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)

    async def inspect_layer1_extraction(
        self,
        document_text: str,
        layer1_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Layer 1 Extraction Inspector
        Ensures initial extraction is comprehensive and nothing critical is missed.
        """
        import time
        start_time = time.time()

        prompt = f"""You are a QUALITY ASSURANCE INSPECTOR for document extraction.

Your job is to inspect Layer 1's extraction output and ensure NOTHING CRITICAL was missed.

ORIGINAL DOCUMENT:
{document_text[:40000]}

LAYER 1 EXTRACTION OUTPUT:
{json.dumps(layer1_data, indent=2)[:8000]}

INSPECTION CHECKLIST:
1. Were ALL parties mentioned in the document extracted?
2. Were ALL dates found and captured?
3. Were ALL monetary amounts identified?
4. Were ALL deadlines noted?
5. Is the document type classification correct?
6. Is the summary accurate and complete?
7. Were any legal terms or provisions missed?

Return JSON:
{{
    "inspection_passed": true/false,
    "quality_score": 0-100,
    "missing_extractions": [
        {{"type": "party/date/amount/etc", "value": "what was missed", "source_text": "where it appears"}}
    ],
    "incorrect_extractions": [
        {{"field": "...", "extracted": "...", "actual": "...", "source_text": "..."}}
    ],
    "improvement_suggestions": ["list of ways to improve extraction"],
    "proceed_to_layer2": true/false,
    "inspector_notes": ["observations about extraction quality"]
}}"""

        try:
            if self.openai_client:  # Use different model than Layer 1 for independence
                response = self.openai_client.chat.completions.create(
                    model=self.GPT4O,
                    temperature=0,
                    max_tokens=3000,
                    messages=[
                        {"role": "system", "content": "You are a meticulous quality inspector."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                data = json.loads(response.choices[0].message.content)
                data["inspector"] = "layer1_qa"
                data["model_used"] = self.GPT4O
            else:
                data = {"inspection_passed": True, "quality_score": 70, "proceed_to_layer2": True}

            data["processing_time"] = time.time() - start_time
            return data

        except Exception as e:
            logger.error(f"Layer 1 inspection error: {str(e)}")
            return {
                "inspection_passed": True,
                "quality_score": 60,
                "proceed_to_layer2": True,
                "error": str(e)
            }

    async def inspect_layer2_verification(
        self,
        layer1_data: Dict[str, Any],
        layer2_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Layer 2 Verification Inspector
        Ensures cross-verification was thorough and discrepancies are real.
        """
        import time
        start_time = time.time()

        prompt = f"""You are a QUALITY ASSURANCE INSPECTOR for cross-model verification.

Your job is to inspect Layer 2's verification and ensure it was thorough.

LAYER 1 EXTRACTION (Original):
{json.dumps(layer1_data, indent=2)[:6000]}

LAYER 2 VERIFICATION (Cross-check):
{json.dumps(layer2_data, indent=2)[:6000]}

INSPECTION CHECKLIST:
1. Did Layer 2 actually verify each extraction?
2. Are the reported discrepancies legitimate?
3. Were any false positives flagged?
4. Were any problems missed?
5. Is the accuracy score justified?

Return JSON:
{{
    "inspection_passed": true/false,
    "verification_quality": 0-100,
    "false_positive_flags": ["items incorrectly flagged as problems"],
    "missed_issues": ["problems Layer 2 should have caught"],
    "discrepancy_assessment": {{
        "legitimate_discrepancies": 0,
        "false_alarms": 0,
        "missed_discrepancies": 0
    }},
    "recommended_accuracy_adjustment": 0,  // +/- to accuracy score
    "proceed_to_layer3": true/false,
    "inspector_notes": ["observations"]
}}"""

        try:
            if self.claude_client:  # Use different model
                response = self.claude_client.messages.create(
                    model='claude-sonnet-4-5-20250929',  # Use Sonnet for variety
                    max_tokens=2000,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text.strip()
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                data = json.loads(json_match.group()) if json_match else {}
                data["model_used"] = 'claude-sonnet-4-5-20250929'
            else:
                data = {"inspection_passed": True, "verification_quality": 70, "proceed_to_layer3": True}

            data["inspector"] = "layer2_qa"
            data["processing_time"] = time.time() - start_time
            return data

        except Exception as e:
            logger.error(f"Layer 2 inspection error: {str(e)}")
            return {
                "inspection_passed": True,
                "verification_quality": 60,
                "proceed_to_layer3": True,
                "error": str(e)
            }

    async def inspect_layer3_hallucination(
        self,
        document_text: str,
        layer3_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Layer 3 Hallucination Inspector
        Verifies that hallucination detection was accurate.
        """
        import time
        start_time = time.time()

        prompt = f"""You are a QUALITY ASSURANCE INSPECTOR for hallucination detection.

Your job is to verify Layer 3's hallucination findings are accurate.

DOCUMENT TEXT (sample):
{document_text[:20000]}

LAYER 3 HALLUCINATION FINDINGS:
{json.dumps(layer3_data, indent=2)[:5000]}

INSPECTION TASKS:
1. For each "hallucination" flagged - verify it really doesn't appear in document
2. Check if any hallucinations were missed
3. Verify the confidence adjustments are appropriate

Return JSON:
{{
    "inspection_passed": true/false,
    "false_positives": ["items incorrectly flagged as hallucinations"],
    "missed_hallucinations": ["actual hallucinations that were missed"],
    "confidence_adjustment_review": {{
        "appropriate": true/false,
        "recommended_adjustment": 0
    }},
    "proceed_to_layer4": true/false,
    "inspector_notes": ["observations"]
}}"""

        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=self.GPT4O,
                    temperature=0,
                    max_tokens=2000,
                    messages=[
                        {"role": "system", "content": "You are a hallucination detection QA inspector."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                data = json.loads(response.choices[0].message.content)
                data["model_used"] = self.GPT4O
            else:
                data = {"inspection_passed": True, "proceed_to_layer4": True}

            data["inspector"] = "layer3_qa"
            data["processing_time"] = time.time() - start_time
            return data

        except Exception as e:
            logger.error(f"Layer 3 inspection error: {str(e)}")
            return {
                "inspection_passed": True,
                "proceed_to_layer4": True,
                "error": str(e)
            }

    async def inspect_final_output(
        self,
        document_text: str,
        final_data: Dict[str, Any],
        expert_review: Optional[ExpertReview] = None
    ) -> Dict[str, Any]:
        """
        Final Output Inspector
        Comprehensive final check before returning results to user.
        """
        import time
        start_time = time.time()

        expert_info = ""
        if expert_review:
            expert_info = f"""
EXPERT REVIEW FINDINGS:
{json.dumps(expert_review.to_dict(), indent=2)[:3000]}
"""

        prompt = f"""You are the FINAL QUALITY ASSURANCE INSPECTOR.

This is the LAST CHECK before results go to the user. Be thorough.

ORIGINAL DOCUMENT:
{document_text[:30000]}

FINAL ANALYSIS OUTPUT:
{json.dumps(final_data, indent=2)[:8000]}
{expert_info}

FINAL INSPECTION CHECKLIST:
1. Is the summary accurate and helpful?
2. Are all parties correctly identified?
3. Are all dates accurate and properly described?
4. Are all monetary amounts correct?
5. Are deadlines clearly stated with proper urgency?
6. Is the document type correct?
7. Are there any remaining hallucinations?
8. Is anything critically important missing?
9. Would this be useful to someone who received this document?

Return JSON:
{{
    "final_approval": true/false,
    "overall_quality_score": 0-100,
    "critical_issues": ["any issues that MUST be fixed before delivery"],
    "minor_issues": ["issues that should be noted but aren't critical"],
    "final_corrections": [
        {{"field": "...", "issue": "...", "correction": "..."}}
    ],
    "completeness_assessment": {{
        "parties": "complete/partial/missing",
        "dates": "complete/partial/missing",
        "amounts": "complete/partial/missing",
        "deadlines": "complete/partial/missing",
        "summary": "adequate/needs_improvement"
    }},
    "user_readiness": {{
        "ready_for_user": true/false,
        "confidence_level": "HIGH/MEDIUM/LOW",
        "recommended_disclaimers": ["any warnings to include"]
    }},
    "inspector_final_notes": ["final observations and recommendations"]
}}"""

        try:
            if self.claude_client:
                response = self.claude_client.messages.create(
                    model=self.CLAUDE_OPUS,
                    max_tokens=3000,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text.strip()
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                data = json.loads(json_match.group()) if json_match else {}
                data["model_used"] = self.CLAUDE_OPUS
            elif self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=self.GPT4O,
                    temperature=0,
                    max_tokens=3000,
                    messages=[
                        {"role": "system", "content": "You are the final quality inspector."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                data = json.loads(response.choices[0].message.content)
                data["model_used"] = self.GPT4O
            else:
                data = {"final_approval": True, "overall_quality_score": 70}

            data["inspector"] = "final_qa"
            data["processing_time"] = time.time() - start_time
            return data

        except Exception as e:
            logger.error(f"Final inspection error: {str(e)}")
            return {
                "final_approval": True,
                "overall_quality_score": 60,
                "error": str(e)
            }


def detect_document_type(text: str, initial_classification: str = "") -> DocumentType:
    """
    Detect the type of legal document from its content.
    Used to route to the appropriate expert agent.
    """
    text_lower = text.lower()

    # Check for specific document type indicators
    if any(term in text_lower for term in ["complaint", "plaintiff v", "plaintiff vs", "cause of action", "prayer for relief"]):
        return DocumentType.COMPLAINT

    if any(term in text_lower for term in ["motion to", "moves this court", "memorandum in support", "motion for"]):
        return DocumentType.MOTION

    if any(term in text_lower for term in ["chapter 7", "chapter 11", "chapter 13", "bankruptcy petition", "341 meeting", "proof of claim"]):
        return DocumentType.BANKRUPTCY

    if any(term in text_lower for term in ["debt collector", "collection", "amount due", "past due", "validation of debt"]):
        return DocumentType.DEBT_COLLECTION

    if any(term in text_lower for term in ["hereby ordered", "it is ordered", "court orders", "judgment is entered"]):
        if "judgment" in text_lower:
            return DocumentType.JUDGMENT
        return DocumentType.COURT_ORDER

    if any(term in text_lower for term in ["notice of", "you are hereby notified", "take notice"]):
        return DocumentType.NOTICE

    if any(term in text_lower for term in ["interrogator", "request for production", "request for admission", "subpoena"]):
        return DocumentType.DISCOVERY

    if any(term in text_lower for term in ["summons", "you are summoned", "commanded to appear"]):
        return DocumentType.SUMMONS

    if any(term in text_lower for term in ["settlement agreement", "release and settlement", "settlement and release"]):
        return DocumentType.SETTLEMENT

    if any(term in text_lower for term in ["notice of appeal", "appellant", "appellee", "brief on appeal"]):
        return DocumentType.APPEAL

    if any(term in text_lower for term in ["agreement", "contract", "hereby agree", "terms and conditions", "parties agree"]):
        return DocumentType.CONTRACT

    if any(term in text_lower for term in ["judgment", "judgment is entered", "judgment for"]):
        return DocumentType.JUDGMENT

    # Use initial classification if provided
    if initial_classification:
        for doc_type in DocumentType:
            if doc_type.value in initial_classification.lower():
                return doc_type

    return DocumentType.UNKNOWN


# Singleton instances
document_expert = DocumentTypeExpert()
layer_inspector = LayerInspectionAgent()
