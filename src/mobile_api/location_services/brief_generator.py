"""
Quick Brief Generation Engine

AI-powered legal brief generation optimized for mobile use with
courthouse-specific formatting and local rules integration.
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import openai
from fastapi import HTTPException

from .location_models import (
    BriefGenerationRequest,
    QuickBrief,
    CourthouseInfo,
    LocationContext
)

logger = logging.getLogger(__name__)


class QuickBriefGenerator:
    """
    AI-powered quick brief generation with courthouse-specific formatting
    and local rules integration for mobile legal professionals.
    """
    
    def __init__(self, openai_client: openai.AsyncOpenAI):
        self.openai_client = openai_client
        self.brief_templates = self._initialize_brief_templates()
        self.citation_patterns = self._initialize_citation_patterns()
        self.local_rules_cache = {}
        
    def _initialize_brief_templates(self) -> Dict[str, Dict]:
        """Initialize brief templates for different document types"""
        return {
            "motion": {
                "structure": [
                    "caption",
                    "introduction", 
                    "statement_of_facts",
                    "legal_argument",
                    "conclusion",
                    "signature_block"
                ],
                "max_pages": 10,
                "key_sections": ["legal_standard", "argument", "relief_requested"]
            },
            "response": {
                "structure": [
                    "caption",
                    "introduction",
                    "counter_statement",
                    "legal_argument", 
                    "conclusion",
                    "signature_block"
                ],
                "max_pages": 15,
                "key_sections": ["response_to_facts", "counter_argument", "opposition"]
            },
            "brief": {
                "structure": [
                    "caption",
                    "table_of_contents",
                    "table_of_authorities", 
                    "statement_of_issues",
                    "statement_of_facts",
                    "argument",
                    "conclusion",
                    "signature_block"
                ],
                "max_pages": 25,
                "key_sections": ["issues_presented", "standard_of_review", "argument"]
            },
            "memo": {
                "structure": [
                    "header",
                    "executive_summary",
                    "legal_analysis",
                    "recommendations", 
                    "conclusion"
                ],
                "max_pages": 8,
                "key_sections": ["analysis", "recommendations"]
            }
        }
    
    def _initialize_citation_patterns(self) -> Dict[str, str]:
        """Initialize citation patterns for different citation styles"""
        return {
            "bluebook": {
                "case": r"([A-Za-z\s\.\&]+)\s+v\.\s+([A-Za-z\s\.\&]+),\s+(\d+)\s+([A-Za-z\.]+)\s+(\d+)",
                "statute": r"(\d+)\s+U\.?S\.?C\.?\s+§?\s*(\d+)",
                "rule": r"Fed\.?\s+R\.?\s+Civ\.?\s+P\.?\s+(\d+)",
                "constitution": r"U\.?S\.?\s+Const\.?\s+(art|amend)\.?\s+([IVX\d]+)"
            },
            "alwd": {
                "case": r"([A-Za-z\s\.\&]+)\s+v\.\s+([A-Za-z\s\.\&]+),\s+(\d+)\s+([A-Za-z\.]+)\s+(\d+)",
                "statute": r"(\d+)\s+USC\s+§\s*(\d+)",
                "rule": r"Fed\.\s+R\.\s+Civ\.\s+P\.\s+(\d+)"
            }
        }
    
    async def generate_quick_brief(
        self,
        request: BriefGenerationRequest,
        location_context: Optional[LocationContext] = None
    ) -> QuickBrief:
        """
        Generate a quick legal brief based on the request parameters
        """
        start_time = datetime.utcnow()
        
        try:
            # Get courthouse-specific formatting requirements
            court_rules = await self._get_court_formatting_rules(request.courthouse)
            
            # Generate brief content using AI
            brief_content = await self._generate_brief_content(request, court_rules, location_context)
            
            # Format according to court requirements
            formatted_brief = await self._format_brief(brief_content, court_rules, request)
            
            # Generate citations if requested
            citations = []
            if request.include_citations:
                citations = await self._generate_citations(brief_content, request.citation_style)
            
            # Find relevant precedents
            precedents = []
            if request.include_precedents:
                precedents = await self._find_precedents(request, brief_content)
            
            # Calculate metrics
            word_count = self._count_words(formatted_brief)
            confidence_score = self._calculate_confidence_score(brief_content, request)
            
            # Estimate filing fee
            filing_fee = self._estimate_filing_fee(request, request.courthouse)
            
            # Create brief object
            brief = QuickBrief(
                title=self._generate_title(request),
                brief_type=request.brief_type,
                case_info={
                    "case_id": str(request.case_id) if request.case_id else None,
                    "case_title": request.case_title,
                    "case_type": request.case_type,
                    "hearing_date": request.hearing_date.isoformat() if request.hearing_date else None,
                    "hearing_type": request.hearing_type
                },
                courthouse_info=request.courthouse,
                caption=formatted_brief.get("caption", ""),
                introduction=formatted_brief.get("introduction", ""),
                statement_of_facts=formatted_brief.get("statement_of_facts", ""),
                legal_argument=formatted_brief.get("legal_argument", ""),
                conclusion=formatted_brief.get("conclusion", ""),
                signature_block=formatted_brief.get("signature_block", ""),
                citations=citations,
                precedents=precedents,
                local_rules_cited=court_rules.get("rules_cited", []),
                word_count=word_count,
                estimated_filing_fee=filing_fee,
                confidence_score=confidence_score,
                completeness_score=self._calculate_completeness_score(formatted_brief)
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Generated {request.brief_type} brief in {processing_time:.2f}s")
            
            return brief
            
        except Exception as e:
            logger.error(f"Brief generation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Brief generation failed: {str(e)}"
            )
    
    async def _generate_brief_content(
        self,
        request: BriefGenerationRequest,
        court_rules: Dict,
        location_context: Optional[LocationContext]
    ) -> Dict[str, str]:
        """
        Generate brief content using AI based on request parameters
        """
        # Prepare context for AI
        context_info = self._prepare_ai_context(request, court_rules, location_context)
        
        # Get brief template
        template = self.brief_templates.get(request.brief_type, self.brief_templates["motion"])
        
        # Generate each section
        brief_content = {}
        
        for section in template["structure"]:
            section_content = await self._generate_section(
                section, request, context_info, brief_content
            )
            brief_content[section] = section_content
        
        return brief_content
    
    async def _generate_section(
        self,
        section_name: str,
        request: BriefGenerationRequest,
        context_info: Dict,
        existing_content: Dict[str, str]
    ) -> str:
        """
        Generate content for a specific section of the brief
        """
        section_prompts = {
            "caption": self._get_caption_prompt(request, context_info),
            "introduction": self._get_introduction_prompt(request, context_info),
            "statement_of_facts": self._get_facts_prompt(request, context_info),
            "legal_argument": self._get_argument_prompt(request, context_info),
            "conclusion": self._get_conclusion_prompt(request, context_info),
            "signature_block": self._get_signature_prompt(request, context_info)
        }
        
        prompt = section_prompts.get(section_name, f"Generate {section_name} section")
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert legal writer specializing in court documents.
                        Write clear, professional, and legally sound content. Use proper legal citation
                        format and maintain consistency with court rules and local practices."""
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent legal writing
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up and format the content
            content = self._clean_section_content(content, section_name)
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate {section_name} section: {str(e)}")
            return f"[{section_name.replace('_', ' ').title()} section - generation failed]"
    
    def _get_caption_prompt(self, request: BriefGenerationRequest, context: Dict) -> str:
        """Generate prompt for case caption"""
        court_name = "UNITED STATES DISTRICT COURT"
        if request.courthouse:
            court_name = request.courthouse.name.upper()
        
        return f"""
        Generate a proper legal case caption for:
        - Court: {court_name}
        - Case Title: {request.case_title or "TO BE DETERMINED"}
        - Document Type: {request.brief_type.replace('_', ' ').title()}
        - Case Type: {request.case_type}
        
        Include proper formatting with case number placeholder, party names,
        and document title. Follow standard legal caption format.
        """
    
    def _get_introduction_prompt(self, request: BriefGenerationRequest, context: Dict) -> str:
        """Generate prompt for introduction section"""
        return f"""
        Write a professional introduction for a {request.brief_type} in a {request.case_type} case.
        
        Key points to address:
        - Brief overview of the matter
        - Purpose of this {request.brief_type}
        - Relief or action requested
        - Key issues: {', '.join(request.key_issues) if request.key_issues else 'TBD'}
        
        Keep it concise (2-3 paragraphs) and professional.
        """
    
    def _get_facts_prompt(self, request: BriefGenerationRequest, context: Dict) -> str:
        """Generate prompt for statement of facts"""
        facts_summary = request.facts_summary or "Facts to be provided by attorney"
        
        return f"""
        Write a statement of facts section for a legal brief based on:
        
        Facts Summary: {facts_summary}
        Case Type: {request.case_type}
        Key Issues: {', '.join(request.key_issues) if request.key_issues else 'General legal matter'}
        
        Guidelines:
        - Present facts chronologically
        - Use neutral, objective language
        - Include relevant dates and details
        - Avoid argumentative language
        - Cite to record where appropriate (use placeholder citations)
        """
    
    def _get_argument_prompt(self, request: BriefGenerationRequest, context: Dict) -> str:
        """Generate prompt for legal argument section"""
        legal_standards = ', '.join(request.legal_standards) if request.legal_standards else "applicable legal standards"
        
        return f"""
        Write a legal argument section for a {request.brief_type} addressing:
        
        Key Issues: {', '.join(request.key_issues) if request.key_issues else 'TBD'}
        Legal Standards: {legal_standards}
        Case Type: {request.case_type}
        Court Requirements: {context.get('court_specific_requirements', 'Standard federal/state requirements')}
        
        Structure the argument with:
        1. Applicable legal standard
        2. Application of law to facts
        3. Supporting authority (use placeholder citations)
        4. Addressing counterarguments
        
        Make arguments clear, logical, and well-supported.
        """
    
    def _get_conclusion_prompt(self, request: BriefGenerationRequest, context: Dict) -> str:
        """Generate prompt for conclusion section"""
        return f"""
        Write a conclusion section for a {request.brief_type} that:
        
        - Summarizes the key arguments made
        - Clearly states the relief requested
        - Is appropriately respectful to the court
        - Case type: {request.case_type}
        - Brief type: {request.brief_type}
        
        Keep it concise and professional (1-2 paragraphs).
        End with specific requested relief.
        """
    
    def _get_signature_prompt(self, request: BriefGenerationRequest, context: Dict) -> str:
        """Generate prompt for signature block"""
        return f"""
        Generate a professional signature block for a legal document including:
        
        - Attorney name placeholder
        - Bar number placeholder
        - Law firm information placeholders
        - Contact information (address, phone, email)
        - "Attorney for [Party]" designation
        - Date placeholder
        
        Follow proper legal document signature formatting.
        Court: {request.courthouse.name if request.courthouse else 'Federal Court'}
        """
    
    def _prepare_ai_context(
        self,
        request: BriefGenerationRequest,
        court_rules: Dict,
        location_context: Optional[LocationContext]
    ) -> Dict[str, Any]:
        """
        Prepare context information for AI generation
        """
        context = {
            "brief_type": request.brief_type,
            "case_type": request.case_type,
            "length_preference": request.length_preference,
            "citation_style": request.citation_style,
            "court_rules": court_rules,
            "auto_research": request.auto_research,
            "include_citations": request.include_citations
        }
        
        if request.courthouse:
            context["courthouse_name"] = request.courthouse.name
            context["court_type"] = request.courthouse.court_type.value
            context["jurisdiction"] = request.courthouse.jurisdiction
            context["local_rules"] = court_rules.get("local_rules", [])
        
        if location_context:
            context["location_based"] = True
            context["business_hours"] = location_context.is_business_hours
            context["relevant_rules"] = location_context.relevant_rules
            context["filing_requirements"] = location_context.filing_requirements
        
        return context
    
    async def _get_court_formatting_rules(self, courthouse: Optional[CourthouseInfo]) -> Dict:
        """
        Get formatting rules specific to the courthouse
        """
        if not courthouse:
            return self._get_default_formatting_rules()
        
        courthouse_id = str(courthouse.id)
        
        # Check cache first
        if courthouse_id in self.local_rules_cache:
            cache_entry = self.local_rules_cache[courthouse_id]
            if (datetime.utcnow() - cache_entry["cached_at"]).hours < 24:
                return cache_entry["rules"]
        
        # Get rules for the specific court
        rules = await self._fetch_court_rules(courthouse)
        
        # Cache the rules
        self.local_rules_cache[courthouse_id] = {
            "rules": rules,
            "cached_at": datetime.utcnow()
        }
        
        return rules
    
    async def _fetch_court_rules(self, courthouse: CourthouseInfo) -> Dict:
        """
        Fetch formatting rules for specific courthouse
        """
        # In production, this would fetch from a rules database or API
        default_rules = self._get_default_formatting_rules()
        
        # Add court-specific customizations
        court_specific_rules = {}
        
        if courthouse.court_type.value.startswith("federal"):
            court_specific_rules.update({
                "font": "Times New Roman, 12pt",
                "margins": "1 inch all sides",
                "line_spacing": "double",
                "page_limit": 25,
                "citation_style": "bluebook",
                "signature_requirements": "Electronic signature acceptable via CM/ECF"
            })
        else:
            # State court rules vary
            court_specific_rules.update({
                "font": "Times New Roman or Arial, 12pt",
                "margins": "1 inch all sides", 
                "line_spacing": "double",
                "page_limit": 20,
                "citation_style": "state_specific"
            })
        
        # Merge with defaults
        default_rules.update(court_specific_rules)
        
        # Add local rules references if available
        if courthouse.local_rules_url:
            default_rules["local_rules_url"] = courthouse.local_rules_url
        
        return default_rules
    
    def _get_default_formatting_rules(self) -> Dict:
        """Get default court formatting rules"""
        return {
            "font": "Times New Roman, 12pt",
            "margins": "1 inch all sides",
            "line_spacing": "double",
            "page_limit": 25,
            "citation_style": "bluebook",
            "header": True,
            "page_numbers": True,
            "signature_required": True,
            "certificate_of_service": True,
            "rules_cited": []
        }
    
    async def _format_brief(
        self,
        content: Dict[str, str],
        court_rules: Dict,
        request: BriefGenerationRequest
    ) -> Dict[str, str]:
        """
        Format brief content according to court rules
        """
        formatted_content = {}
        
        for section, text in content.items():
            formatted_text = self._format_section(text, section, court_rules)
            formatted_content[section] = formatted_text
        
        # Add court-specific formatting elements
        if request.include_signature_block and court_rules.get("signature_required"):
            formatted_content["signature_block"] = self._format_signature_block(
                content.get("signature_block", ""), court_rules
            )
        
        return formatted_content
    
    def _format_section(self, text: str, section_name: str, court_rules: Dict) -> str:
        """
        Format individual section according to court rules
        """
        # Apply basic formatting
        formatted_text = text.strip()
        
        # Section-specific formatting
        if section_name == "caption":
            formatted_text = self._format_caption(formatted_text, court_rules)
        elif section_name in ["legal_argument", "argument"]:
            formatted_text = self._format_argument_section(formatted_text, court_rules)
        
        # Apply citation formatting
        formatted_text = self._format_citations(formatted_text, court_rules.get("citation_style", "bluebook"))
        
        return formatted_text
    
    def _format_caption(self, caption: str, court_rules: Dict) -> str:
        """Format case caption according to court requirements"""
        # Ensure proper case caption formatting
        if not caption.strip():
            return "[CASE CAPTION TO BE COMPLETED]"
        
        # Add court-specific caption requirements
        formatted_caption = caption
        
        # Ensure proper spacing and alignment
        lines = formatted_caption.split('\n')
        centered_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Center court name and major headings
                if any(word in line.upper() for word in ["COURT", "DISTRICT", "COUNTY"]):
                    centered_lines.append(f"{line:^80}")
                else:
                    centered_lines.append(line)
        
        return '\n'.join(centered_lines)
    
    def _format_argument_section(self, argument: str, court_rules: Dict) -> str:
        """Format legal argument section"""
        # Ensure proper paragraph structure
        paragraphs = argument.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # Ensure proper indentation for legal arguments
                if not para.startswith('    '):
                    para = '    ' + para
                formatted_paragraphs.append(para)
        
        return '\n\n'.join(formatted_paragraphs)
    
    def _format_citations(self, text: str, citation_style: str) -> str:
        """Format legal citations according to specified style"""
        if citation_style == "bluebook":
            return self._format_bluebook_citations(text)
        elif citation_style == "alwd":
            return self._format_alwd_citations(text)
        else:
            return text
    
    def _format_bluebook_citations(self, text: str) -> str:
        """Format citations according to Bluebook style"""
        # This is a simplified version - full implementation would be more comprehensive
        
        # Fix common citation formatting issues
        text = re.sub(r'\bv\.([A-Za-z])', r'v. \1', text)  # Add space after "v."
        text = re.sub(r'(\d+)\s+U\.?S\.?C\.?\s*§?\s*(\d+)', r'\1 U.S.C. § \2', text)  # USC format
        text = re.sub(r'Fed\.?\s*R\.?\s*Civ\.?\s*P\.?\s*(\d+)', r'Fed. R. Civ. P. \1', text)  # Federal Rules
        
        return text
    
    def _format_alwd_citations(self, text: str) -> str:
        """Format citations according to ALWD style"""
        # Simplified ALWD formatting
        text = re.sub(r'(\d+)\s+U\.?S\.?C\.?\s*§?\s*(\d+)', r'\1 USC § \2', text)
        text = re.sub(r'Fed\.?\s*R\.?\s*Civ\.?\s*P\.?\s*(\d+)', r'Fed. R. Civ. P. \1', text)
        
        return text
    
    def _format_signature_block(self, signature_text: str, court_rules: Dict) -> str:
        """Format signature block according to court requirements"""
        if not signature_text:
            signature_text = """
Respectfully submitted,

_________________________
[Attorney Name]
[State Bar Number]
[Law Firm Name]
[Address]
[City, State ZIP]
[Phone Number]
[Email Address]

Attorney for [Party Name]
            """.strip()
        
        # Add date if not present
        if "[Date]" not in signature_text and datetime.now().strftime("%B %d, %Y") not in signature_text:
            signature_text = f"Dated: {datetime.now().strftime('%B %d, %Y')}\n\n{signature_text}"
        
        return signature_text
    
    async def _generate_citations(self, content: Dict[str, str], citation_style: str) -> List[Dict[str, str]]:
        """Generate relevant legal citations for the brief"""
        # In production, this would integrate with legal research APIs
        citations = [
            {
                "type": "case",
                "citation": "Brown v. Board of Education, 347 U.S. 483 (1954)",
                "relevance": "foundational case law",
                "section": "legal_argument"
            },
            {
                "type": "statute",
                "citation": "42 U.S.C. § 1983",
                "relevance": "civil rights statute",
                "section": "legal_argument"
            },
            {
                "type": "rule",
                "citation": "Fed. R. Civ. P. 12(b)(6)",
                "relevance": "procedural rule",
                "section": "legal_argument"
            }
        ]
        
        return citations
    
    async def _find_precedents(
        self,
        request: BriefGenerationRequest,
        content: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Find relevant legal precedents"""
        # Mock precedent data - would integrate with legal databases
        precedents = [
            {
                "case_name": "Similar Case v. Example Defendant",
                "citation": "123 F.3d 456 (9th Cir. 2020)",
                "relevance_score": 0.85,
                "key_holding": "Court held that similar facts warrant similar relief",
                "distinguishing_factors": [],
                "supporting_factors": ["Similar legal standard", "Comparable facts"]
            }
        ]
        
        return precedents
    
    def _generate_title(self, request: BriefGenerationRequest) -> str:
        """Generate appropriate title for the brief"""
        brief_type = request.brief_type.replace('_', ' ').title()
        
        if request.case_title:
            return f"{brief_type} in {request.case_title}"
        else:
            return f"{brief_type} - {request.case_type.replace('_', ' ').title()}"
    
    def _count_words(self, content: Dict[str, str]) -> int:
        """Count total words in brief content"""
        total_words = 0
        for section_content in content.values():
            if section_content:
                words = len(section_content.split())
                total_words += words
        return total_words
    
    def _calculate_confidence_score(self, content: Dict[str, str], request: BriefGenerationRequest) -> float:
        """Calculate confidence score for generated brief"""
        score = 0.8  # Base score
        
        # Adjust based on available information
        if request.facts_summary:
            score += 0.1
        if request.key_issues:
            score += 0.05
        if request.legal_standards:
            score += 0.05
        if request.courthouse:
            score += 0.05
        
        # Check content completeness
        required_sections = ["introduction", "legal_argument", "conclusion"]
        completed_sections = sum(1 for section in required_sections if content.get(section))
        completion_ratio = completed_sections / len(required_sections)
        score *= completion_ratio
        
        return min(1.0, max(0.1, score))
    
    def _calculate_completeness_score(self, content: Dict[str, str]) -> float:
        """Calculate completeness score for the brief"""
        total_sections = len(content)
        completed_sections = sum(1 for section_content in content.values() if section_content and len(section_content.strip()) > 50)
        
        if total_sections == 0:
            return 0.0
        
        return completed_sections / total_sections
    
    def _estimate_filing_fee(self, request: BriefGenerationRequest, courthouse: Optional[CourthouseInfo]) -> Optional[float]:
        """Estimate filing fee for the document"""
        # Basic fee estimation - would integrate with court fee schedules
        base_fees = {
            "motion": 50.0,
            "response": 25.0,
            "brief": 100.0,
            "memo": 0.0  # Internal document, no filing fee
        }
        
        base_fee = base_fees.get(request.brief_type, 50.0)
        
        # Adjust for court type
        if courthouse and courthouse.court_type.value.startswith("federal"):
            base_fee *= 1.5  # Federal courts typically have higher fees
        
        return base_fee
    
    def _clean_section_content(self, content: str, section_name: str) -> str:
        """Clean and standardize section content"""
        # Remove extra whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = content.strip()
        
        # Section-specific cleaning
        if section_name == "caption":
            # Ensure caption formatting
            content = content.upper() if "UNITED STATES" in content.upper() else content
        
        return content