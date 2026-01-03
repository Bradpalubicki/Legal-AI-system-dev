"""
Legal content extraction from filing documents.

Advanced content extraction system that identifies and extracts key legal
information including parties, dates, citations, claims, and structured data.
"""

import re
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal

from ..shared.utils import BaseAPIClient
from .models import ExtractedContent, LegalCitation, ActionItem


@dataclass
class ExtractionResult:
    """Complete result of content extraction from legal document."""
    extracted_content: ExtractedContent
    confidence_scores: Dict[str, float]
    extraction_method: str
    processing_time: float
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PartyInformation:
    """Information about parties involved in legal matter."""
    name: str
    role: str  # plaintiff, defendant, petitioner, etc.
    attorney: Optional[str] = None
    firm: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


@dataclass
class FinancialInformation:
    """Financial data extracted from document."""
    damages_claimed: Optional[Decimal] = None
    settlement_amount: Optional[Decimal] = None
    attorney_fees: Optional[Decimal] = None
    costs: Optional[Decimal] = None
    currency: str = "USD"


class ContentExtractor:
    """Advanced legal content extraction engine."""
    
    def __init__(self, api_client: BaseAPIClient):
        self.api_client = api_client
        self.extraction_patterns = self._initialize_patterns()
        self.citation_parser = CitationParser()
        
    def _initialize_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize regex patterns for content extraction."""
        return {
            "parties": {
                "plaintiff": r"plaintiff[s]?\s*[,:]?\s*([^,\n]+?)(?:\s*(?:v\.?|vs\.?|against)|\s*,|$)",
                "defendant": r"defendant[s]?\s*[,:]?\s*([^,\n]+?)(?:\s*,|$|\s*\n)",
                "petitioner": r"petitioner[s]?\s*[,:]?\s*([^,\n]+?)(?:\s*,|$|\s*\n)",
                "respondent": r"respondent[s]?\s*[,:]?\s*([^,\n]+?)(?:\s*,|$|\s*\n)"
            },
            "dates": {
                "filing_date": r"filed?\s*(?:on\s*)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                "hearing_date": r"hearing\s*(?:scheduled\s*)?(?:for\s*)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                "deadline": r"deadline\s*(?:is\s*)?(?:on\s*)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                "response_due": r"response\s*(?:is\s*)?due\s*(?:by\s*)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
            },
            "financial": {
                "damages": r"damages?\s*(?:in\s*the\s*amount\s*of\s*)?(?:\$|USD\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
                "settlement": r"settlement\s*(?:amount\s*)?(?:of\s*)?(?:\$|USD\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
                "attorney_fees": r"attorney\s*fees?\s*(?:in\s*the\s*amount\s*of\s*)?(?:\$|USD\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
                "costs": r"costs?\s*(?:in\s*the\s*amount\s*of\s*)?(?:\$|USD\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
            },
            "contact": {
                "phone": r"(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})",
                "email": r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                "address": r"(\d+\s+[^,\n]+,\s*[^,\n]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)"
            },
            "legal_concepts": {
                "cause_of_action": r"cause\s*of\s*action[s]?\s*(?:for\s*)?([^.\n]+)",
                "relief_sought": r"(?:seeks?|requesting?|pray(?:s|ing)?\s*for)\s*([^.\n]+)",
                "jurisdiction": r"jurisdiction\s*(?:is\s*)?(?:proper\s*)?(?:in\s*)?([^.\n]+)",
                "venue": r"venue\s*(?:is\s*)?(?:proper\s*)?(?:in\s*)?([^.\n]+)"
            }
        }
    
    async def extract_content(self, 
                            document_text: str,
                            filing_type: str,
                            metadata: Optional[Dict[str, Any]] = None) -> ExtractionResult:
        """
        Extract comprehensive content from legal document.
        
        Args:
            document_text: Full text of the legal document
            filing_type: Type of filing (motion, complaint, etc.)
            metadata: Additional document metadata
            
        Returns:
            ExtractionResult with extracted content and analysis
        """
        start_time = datetime.utcnow()
        warnings = []
        confidence_scores = {}
        
        # Extract parties information
        parties = self._extract_parties(document_text)
        confidence_scores["parties"] = self._calculate_party_confidence(parties)
        
        # Extract dates and deadlines
        dates = self._extract_dates(document_text)
        confidence_scores["dates"] = self._calculate_date_confidence(dates)
        
        # Extract financial information
        financial = self._extract_financial_info(document_text)
        confidence_scores["financial"] = self._calculate_financial_confidence(financial)
        
        # Extract legal citations
        citations = await self._extract_citations(document_text)
        confidence_scores["citations"] = self._calculate_citation_confidence(citations)
        
        # Extract key claims and arguments
        claims = await self._extract_claims(document_text, filing_type)
        confidence_scores["claims"] = 0.8  # AI-based, assume good confidence
        
        # Extract action items and deadlines
        action_items = self._extract_action_items(document_text, dates)
        
        # Extract contact information
        contact_info = self._extract_contact_info(document_text)
        
        # Build extracted content
        extracted_content = ExtractedContent(
            parties=[p.name for p in parties],
            key_dates=dates,
            claims_and_arguments=claims,
            legal_citations=citations,
            financial_info=self._format_financial_info(financial),
            jurisdiction_info=self._extract_jurisdiction_info(document_text),
            deadlines_and_actions=action_items,
            contact_information=contact_info,
            document_summary=await self._generate_summary(document_text, filing_type),
            extracted_at=datetime.utcnow()
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return ExtractionResult(
            extracted_content=extracted_content,
            confidence_scores=confidence_scores,
            extraction_method="hybrid_ai_rule_based",
            processing_time=processing_time,
            warnings=warnings,
            metadata={
                "document_length": len(document_text),
                "filing_type": filing_type,
                "extraction_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _extract_parties(self, text: str) -> List[PartyInformation]:
        """Extract party information from document text."""
        parties = []
        text_lower = text.lower()
        
        for role, pattern in self.extraction_patterns["parties"].items():
            matches = re.finditer(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                party_name = match.group(1).strip()
                if party_name and len(party_name) > 2:
                    # Try to extract attorney/firm info for this party
                    attorney_info = self._extract_attorney_info(text, party_name)
                    
                    parties.append(PartyInformation(
                        name=party_name.title(),
                        role=role,
                        attorney=attorney_info.get("attorney"),
                        firm=attorney_info.get("firm")
                    ))
        
        return parties
    
    def _extract_attorney_info(self, text: str, party_name: str) -> Dict[str, Optional[str]]:
        """Extract attorney information for a specific party."""
        attorney_patterns = [
            rf"(?:{re.escape(party_name)}[\s\S]{{0,200}}?)by\s+and\s+through\s+(?:counsel\s+)?([^,\n]+)",
            rf"attorney\s+for\s+{re.escape(party_name)}[:\s]+([^,\n]+)",
            rf"{re.escape(party_name)}[\s\S]{{0,100}}?represented\s+by\s+([^,\n]+)"
        ]
        
        for pattern in attorney_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                attorney_text = match.group(1).strip()
                
                # Try to separate attorney name from firm
                firm_match = re.search(r"(.+?)\s+(?:of\s+|,\s*)(.+?)(?:\s*,|$)", attorney_text)
                if firm_match:
                    return {
                        "attorney": firm_match.group(1).strip(),
                        "firm": firm_match.group(2).strip()
                    }
                else:
                    return {"attorney": attorney_text, "firm": None}
        
        return {"attorney": None, "firm": None}
    
    def _extract_dates(self, text: str) -> Dict[str, Any]:
        """Extract important dates from document text."""
        dates = {}
        
        for date_type, pattern in self.extraction_patterns["dates"].items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            extracted_dates = []
            for match in matches:
                date_str = match.group(1)
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    extracted_dates.append(parsed_date.isoformat())
            
            if extracted_dates:
                dates[date_type] = extracted_dates[0] if len(extracted_dates) == 1 else extracted_dates
        
        return dates
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string into date object."""
        date_formats = [
            "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y",
            "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _extract_financial_info(self, text: str) -> FinancialInformation:
        """Extract financial information from document."""
        financial = FinancialInformation()
        
        for fin_type, pattern in self.extraction_patterns["financial"].items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                amount_str = match.group(1).replace(",", "")
                try:
                    amount = Decimal(amount_str)
                    
                    if fin_type == "damages":
                        financial.damages_claimed = amount
                    elif fin_type == "settlement":
                        financial.settlement_amount = amount
                    elif fin_type == "attorney_fees":
                        financial.attorney_fees = amount
                    elif fin_type == "costs":
                        financial.costs = amount
                    
                    break  # Take first match for each type
                    
                except (ValueError, InvalidOperation):
                    continue
        
        return financial
    
    async def _extract_citations(self, text: str) -> List[LegalCitation]:
        """Extract and parse legal citations from text."""
        return await self.citation_parser.extract_citations(text)
    
    async def _extract_claims(self, text: str, filing_type: str) -> List[str]:
        """Use AI to extract key claims and arguments."""
        prompt = self._build_claims_extraction_prompt(text, filing_type)
        
        try:
            response = await self.api_client.post(
                "/ai/extract",
                json={
                    "prompt": prompt,
                    "model": "gpt-4",
                    "temperature": 0.2,
                    "max_tokens": 800
                },
                timeout=30.0
            )
            
            claims_data = response.get("claims", [])
            return [claim.get("text", "") for claim in claims_data if claim.get("text")]
            
        except Exception:
            # Fallback to rule-based extraction
            return self._extract_claims_rule_based(text)
    
    def _build_claims_extraction_prompt(self, text: str, filing_type: str) -> str:
        """Build prompt for AI-powered claims extraction."""
        return f"""
Extract the key legal claims, arguments, and contentions from this {filing_type} document.

Document text:
{text[:3000]}

Please identify and extract:
1. Primary legal claims or causes of action
2. Key factual allegations
3. Legal arguments and theories
4. Relief or remedies sought
5. Any counterclaims or defenses

Format your response as JSON:
{{
    "claims": [
        {{"type": "primary_claim", "text": "description of claim"}},
        {{"type": "factual_allegation", "text": "key facts"}},
        {{"type": "legal_argument", "text": "legal theory"}},
        {{"type": "relief_sought", "text": "remedy requested"}}
    ]
}}
"""
    
    def _extract_claims_rule_based(self, text: str) -> List[str]:
        """Fallback rule-based claims extraction."""
        claims = []
        
        # Look for numbered paragraphs (common in complaints)
        numbered_paragraphs = re.finditer(r'^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.|\Z)', 
                                         text, re.MULTILINE | re.DOTALL)
        
        for match in numbered_paragraphs:
            paragraph_text = match.group(2).strip()
            if len(paragraph_text) > 50 and any(word in paragraph_text.lower() for word in 
                                               ["alleges", "claims", "contends", "asserts"]):
                claims.append(paragraph_text[:200] + "..." if len(paragraph_text) > 200 else paragraph_text)
        
        if not claims:
            # Look for cause of action patterns
            cause_matches = re.finditer(r'cause\s*of\s*action[:\s]*([^.\n]+)', text, re.IGNORECASE)
            claims.extend([match.group(1).strip() for match in cause_matches])
        
        return claims[:10]  # Limit to top 10 claims
    
    def _extract_action_items(self, text: str, dates: Dict[str, Any]) -> List[ActionItem]:
        """Extract action items and deadlines from document."""
        action_items = []
        
        action_patterns = [
            r"(?:must|shall|should|required?\s*to)\s+([^.\n]+?)(?:by|on|before)\s+([^.\n]+)",
            r"deadline\s*(?:is\s*)?(?:for\s*)?([^.\n]+?)(?:is\s*)?(?:on\s*)?([^.\n]+)",
            r"response\s*(?:to\s*)?([^.\n]+?)\s*(?:is\s*)?due\s*(?:on\s*|by\s*)?([^.\n]+)"
        ]
        
        for pattern in action_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                description = match.group(1).strip()
                due_date_str = match.group(2).strip()
                due_date = self._parse_date(due_date_str)
                
                if description and due_date:
                    action_items.append(ActionItem(
                        description=description,
                        due_date=due_date,
                        priority="high" if any(word in description.lower() 
                                             for word in ["emergency", "immediate", "urgent"]) else "medium",
                        assigned_to=None,
                        status="pending"
                    ))
        
        return action_items
    
    def _extract_contact_info(self, text: str) -> Dict[str, List[str]]:
        """Extract contact information from document."""
        contact_info = {
            "emails": [],
            "phones": [],
            "addresses": []
        }
        
        for contact_type, pattern in self.extraction_patterns["contact"].items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                contact_value = match.group(1).strip()
                if contact_type == "phone":
                    contact_info["phones"].append(contact_value)
                elif contact_type == "email":
                    contact_info["emails"].append(contact_value)
                elif contact_type == "address":
                    contact_info["addresses"].append(contact_value)
        
        # Remove duplicates
        for key in contact_info:
            contact_info[key] = list(set(contact_info[key]))
        
        return contact_info
    
    def _extract_jurisdiction_info(self, text: str) -> Dict[str, Any]:
        """Extract jurisdiction and venue information."""
        jurisdiction_info = {}
        
        for concept, pattern in self.extraction_patterns["legal_concepts"].items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                value = match.group(1).strip()
                if value:
                    jurisdiction_info[concept] = value
                    break  # Take first match
        
        return jurisdiction_info
    
    async def _generate_summary(self, text: str, filing_type: str) -> str:
        """Generate AI-powered summary of the document."""
        prompt = f"""
Provide a concise summary of this {filing_type} document in 2-3 sentences.
Focus on the key legal issue, parties involved, and primary requests or arguments.

Document text:
{text[:2000]}

Summary:"""
        
        try:
            response = await self.api_client.post(
                "/ai/summarize",
                json={
                    "prompt": prompt,
                    "model": "gpt-4",
                    "temperature": 0.3,
                    "max_tokens": 200
                },
                timeout=20.0
            )
            
            return response.get("summary", "Summary not available")
            
        except Exception:
            return f"This {filing_type} document requires manual review for detailed summary."
    
    def _format_financial_info(self, financial: FinancialInformation) -> Dict[str, Any]:
        """Format financial information for output."""
        return {
            "damages_claimed": str(financial.damages_claimed) if financial.damages_claimed else None,
            "settlement_amount": str(financial.settlement_amount) if financial.settlement_amount else None,
            "attorney_fees": str(financial.attorney_fees) if financial.attorney_fees else None,
            "costs": str(financial.costs) if financial.costs else None,
            "currency": financial.currency
        }
    
    def _calculate_party_confidence(self, parties: List[PartyInformation]) -> float:
        """Calculate confidence score for party extraction."""
        if not parties:
            return 0.0
        
        score = min(len(parties) * 0.3, 1.0)  # More parties = higher confidence
        
        # Boost score if we have attorney info
        attorney_count = sum(1 for p in parties if p.attorney)
        score += min(attorney_count * 0.2, 0.4)
        
        return min(score, 1.0)
    
    def _calculate_date_confidence(self, dates: Dict[str, Any]) -> float:
        """Calculate confidence score for date extraction."""
        if not dates:
            return 0.0
        
        return min(len(dates) * 0.25, 1.0)
    
    def _calculate_financial_confidence(self, financial: FinancialInformation) -> float:
        """Calculate confidence score for financial extraction."""
        count = sum(1 for amount in [
            financial.damages_claimed,
            financial.settlement_amount,
            financial.attorney_fees,
            financial.costs
        ] if amount is not None)
        
        return min(count * 0.25, 1.0)
    
    def _calculate_citation_confidence(self, citations: List[LegalCitation]) -> float:
        """Calculate confidence score for citation extraction."""
        if not citations:
            return 0.0
        
        return min(len(citations) * 0.2, 1.0)


class CitationParser:
    """Specialized parser for legal citations."""
    
    def __init__(self):
        self.citation_patterns = self._initialize_citation_patterns()
    
    def _initialize_citation_patterns(self) -> List[str]:
        """Initialize regex patterns for legal citation recognition."""
        return [
            # Federal cases: Volume Reporter Page (Year)
            r'(\d+)\s+([A-Z][a-z]*\.?\s*(?:\d+d)?)\s+(\d+)(?:,\s*\d+)?\s*\(([^)]+)\)',
            
            # State cases with regional reporters
            r'(\d+)\s+(N\.?E\.?(?:\s*2d)?|S\.?E\.?(?:\s*2d)?|S\.?W\.?(?:\s*2d)?|N\.?W\.?(?:\s*2d)?|So\.?(?:\s*2d)?|A\.?(?:\s*2d)?|P\.?(?:\s*2d)?)\s+(\d+)',
            
            # U.S. Code citations
            r'(\d+)\s+U\.?S\.?C\.?\s*§\s*(\d+(?:\([a-z]\))?)',
            
            # Federal Register
            r'(\d+)\s+Fed\.?\s*Reg\.?\s*(\d+)',
            
            # Supreme Court cases
            r'(\d+)\s+U\.?S\.?\s+(\d+)',
            
            # Circuit court cases
            r'(\d+)\s+F\.?(?:\s*2d|\s*3d)?\s+(\d+)'
        ]
    
    async def extract_citations(self, text: str) -> List[LegalCitation]:
        """Extract legal citations from text."""
        citations = []
        
        for pattern in self.citation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                citation_text = match.group(0)
                citation = self._parse_citation(citation_text, match.groups())
                
                if citation:
                    citations.append(citation)
        
        # Remove duplicates based on citation text
        seen = set()
        unique_citations = []
        for citation in citations:
            if citation.citation not in seen:
                seen.add(citation.citation)
                unique_citations.append(citation)
        
        return unique_citations
    
    def _parse_citation(self, citation_text: str, groups: Tuple) -> Optional[LegalCitation]:
        """Parse citation groups into structured citation object."""
        try:
            if "U.S.C." in citation_text:
                return LegalCitation(
                    citation=citation_text,
                    case_name=None,
                    court="U.S. Code",
                    year=None,
                    citation_type="statute"
                )
            elif "Fed. Reg." in citation_text:
                return LegalCitation(
                    citation=citation_text,
                    case_name=None,
                    court="Federal Register",
                    year=None,
                    citation_type="regulation"
                )
            elif "U.S." in citation_text and len(groups) >= 2:
                return LegalCitation(
                    citation=citation_text,
                    case_name=None,
                    court="U.S. Supreme Court",
                    year=None,
                    citation_type="case"
                )
            elif len(groups) >= 3:
                year = None
                if len(groups) > 3:
                    year_match = re.search(r'\d{4}', groups[3])
                    year = int(year_match.group()) if year_match else None
                
                return LegalCitation(
                    citation=citation_text,
                    case_name=None,
                    court="Court not specified",
                    year=year,
                    citation_type="case"
                )
        except (ValueError, IndexError):
            pass
        
        return None