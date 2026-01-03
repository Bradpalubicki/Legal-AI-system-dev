"""
Dual-AI Processing Pipeline for Legal Document Analysis
Uses OpenAI for initial heavy lifting, then Claude for finalization and legal enhancement
"""

import os
import json
import logging
import time
import hashlib
from typing import Dict, Any, Optional, List, AsyncGenerator
import asyncio
from openai import OpenAI
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from ..ai.prompts import AI_PROMPTS, ULTRA_CONCISE_PROMPT, DEFENSE_PROMPT, get_prompt, format_prompt, get_model_config
from ..shared.ai.concise_ai_wrapper import force_concise_claude, force_concise_document_analysis, aggressive_strip_verbosity
from .enhanced_document_extractor import enhanced_extractor
from .financial_details_extractor import financial_extractor
from .text_sanitizer import sanitize_text_for_ai

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent.parent / '.env')

logger = logging.getLogger(__name__)

# Model configuration - Define BEFORE classes that use them
# UPGRADED TO TOP-TIER MODELS FOR MAXIMUM ACCURACY
CLAUDE_OPUS_MODEL = 'claude-opus-4-20250514'  # Opus 4 - Highest quality for deep analysis
CLAUDE_MODEL = 'claude-opus-4-20250514'  # Use Opus for comprehensive analysis
CLAUDE_QA_MODEL = 'claude-opus-4-20250514'  # Use Opus for Q&A accuracy
CLAUDE_QUICK_MODEL = 'claude-sonnet-4-5-20250929'  # Sonnet for quick responses (still high quality)
CLAUDE_STANDARD_MODEL = 'claude-opus-4-20250514'  # Opus for standard analysis
CLAUDE_DEEP_MODEL = 'claude-opus-4-20250514'  # Opus for complex/deep analysis
CLAUDE_VERIFICATION_MODEL = 'claude-sonnet-4-5-20250929'  # Sonnet for verification layer (different model)

# OpenAI Models - Top tier
OPENAI_PRIMARY_MODEL = 'gpt-4o'  # Latest GPT-4o for primary analysis
OPENAI_VERIFICATION_MODEL = 'gpt-4-turbo'  # Different model for cross-verification

def optimize_prompt_for_speed(query: str) -> str:
    """Wrap all queries with ultra-concise speed optimization from centralized prompts"""
    return format_prompt("qa", query)

def select_model_by_length(document_length: int) -> str:
    """Select appropriate model based on document length for optimal quality"""
    if document_length < 1000:  # Small documents - use Haiku for speed
        return 'claude-3-5-haiku-20241022'
    elif document_length < 5000:  # Medium documents - use Sonnet 4.5 for quality
        return 'claude-sonnet-4-5-20250929'
    else:  # Large documents - use Sonnet 4.5 for comprehensive analysis
        return 'claude-sonnet-4-5-20250929'

class ResponseCache:
    """In-memory cache for common legal queries"""

    def __init__(self):
        self.cache = {}
        self.ttl = 3600  # 1 hour cache
        self.max_size = 1000  # Maximum cache entries

    def _hash_query(self, query: str) -> str:
        """Create hash of query for cache key"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()

    def get_cached_response(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        query_hash = self._hash_query(query)
        if query_hash in self.cache:
            entry = self.cache[query_hash]
            if time.time() - entry['timestamp'] < self.ttl:
                logger.info(f"Cache HIT for query: {query[:50]}...")
                return entry['response']
            else:
                # Remove expired entry
                del self.cache[query_hash]
        return None

    def cache_response(self, query: str, response: Dict[str, Any]):
        """Cache response for future use"""
        query_hash = self._hash_query(query)

        # Clean old entries if cache is full
        if len(self.cache) >= self.max_size:
            self._cleanup_expired()
            if len(self.cache) >= self.max_size:
                # Remove oldest entry
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
                del self.cache[oldest_key]

        self.cache[query_hash] = {
            'response': response,
            'timestamp': time.time()
        }
        logger.info(f"Cached response for query: {query[:50]}...")

    def _cleanup_expired(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry['timestamp'] >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

class OptimizedAIClient:
    """Speed-optimized AI client with intelligent routing and caching"""

    def __init__(self):
        self.models = {
            'quick': CLAUDE_QUICK_MODEL,  # <1 second responses
            'standard': CLAUDE_STANDARD_MODEL,  # 2-3 second responses
            'deep': CLAUDE_DEEP_MODEL  # Only for complex analysis
        }

        self.token_limits = {
            'quick': {'input': 2000, 'output': 500},  # Forced conciseness
            'standard': {'input': 4000, 'output': 500},  # Reduced for speed
            'deep': {'input': 8000, 'output': 500}  # Even deep analysis kept concise
        }

        self.timeouts = {
            'quick': 30,  # 30 second timeout for quick queries
            'standard': 60,  # 60 second timeout for standard queries
            'deep': 120  # 120 second timeout for deep analysis
        }

        self.temperature_settings = {
            'quick': 0,  # Maximum predictability and speed
            'standard': 0,  # Zero temperature for faster responses
            'deep': 0  # All responses use 0 temperature for speed
        }

        # Only initialize Claude client if API key is available
        self.claude_available = bool(os.getenv('ANTHROPIC_API_KEY'))
        self.claude_client = None
        if self.claude_available:
            self.claude_client = anthropic.Anthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                timeout=120.0  # 2 minutes for document analysis
            )

        self.cache = ResponseCache()

        # ULTRA-CONCISE PROMPTS FROM CENTRALIZED CONFIG - ALL TIERS USE SAME ULTRA-FAST LOGIC
        qa_template = get_prompt("qa")["template"]
        self.SPEED_PROMPTS = {
            'quick': qa_template,
            'standard': qa_template,
            'deep': qa_template
        }

    def route_query(self, query: str, document_length: int = 0, query_type: str = 'general') -> str:
        """Intelligent routing optimized for maximum speed - all queries use quick tier"""
        # ALL query types now use 'quick' tier for maximum speed
        # Length-based selection happens at model level, not tier level
        return 'quick'

    async def process_query(self, query: str, query_type: str = 'qa', document_length: int = 0) -> Dict[str, Any]:
        """Process query with optimal speed and accuracy"""
        # Check cache first for Q&A queries
        if query_type in ['qa', 'chat', 'question']:
            cached = self.cache.get_cached_response(query)
            if cached:
                return cached

        # Route to appropriate model
        tier = self.route_query(query, document_length, query_type)

        # Process with selected tier and document length
        start_time = time.time()
        try:
            response = await self._process_with_tier(query, tier, query_type, document_length)

            # Cache successful Q&A responses
            if query_type in ['qa', 'chat', 'question'] and response.get('answer'):
                self.cache.cache_response(query, response)

            # Add performance metrics
            response['performance'] = {
                'tier_used': tier,
                'response_time': round(time.time() - start_time, 2),
                'cached': False
            }

            return response

        except Exception as e:
            logger.error(f"Error in optimized query processing: {str(e)}")
            return {
                'answer': f"Error processing query: {str(e)}",
                'defense_options': [],
                'follow_up_questions': [],
                'quick_actions': [],
                'performance': {
                    'tier_used': tier,
                    'response_time': round(time.time() - start_time, 2),
                    'error': str(e)
                }
            }

    async def _process_with_tier(self, query: str, tier: str, query_type: str, document_length: int = 0) -> Dict[str, Any]:
        """Process query with specified performance tier and length-based model selection"""
        # Use length-based model selection for optimal speed
        model = select_model_by_length(document_length)
        max_tokens = 500  # Fixed at 500 for all queries for speed
        temperature = 0   # Fixed at 0 for maximum speed and consistency
        timeout = 5       # Fixed 5-second timeout for all queries

        # Select appropriate prompt with speed optimization from centralized config
        if query_type in ['qa', 'chat', 'question']:
            prompt = self.SPEED_PROMPTS[tier](optimize_prompt_for_speed(query))
        else:
            prompt = optimize_prompt_for_speed(query)

        # Make API call with timeout
        response = self.claude_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            timeout=timeout
        )

        raw_response = response.content[0].text

        # Parse response based on query type
        if query_type in ['qa', 'chat', 'question']:
            return self._parse_qa_response(raw_response)
        else:
            return {'analysis': raw_response}

    def _parse_qa_response(self, raw_response: str) -> Dict[str, Any]:
        """Parse Q&A response into structured format"""
        # Simple parsing for speed
        lines = raw_response.split('\n')
        answer = ""
        defense_options = []
        follow_up_questions = []

        current_section = "answer"

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if 'defense' in line.lower() and (':' in line or 'option' in line.lower()):
                current_section = "defense"
            elif 'question' in line.lower() and (':' in line or 'for you' in line.lower()):
                current_section = "questions"
            elif line.startswith('•') or line.startswith('-'):
                if current_section == "defense":
                    defense_options.append(line[1:].strip())
            elif line.startswith(('1.', '2.', '3.')):
                if current_section == "questions":
                    follow_up_questions.append(line[2:].strip())
            elif current_section == "answer" and not answer:
                answer = line

        return {
            "answer": answer or raw_response.split('\n')[0] if raw_response else "Please provide more details.",
            "defense_options": defense_options[:3] if defense_options else [
                "Challenge the evidence",
                "Question the procedures",
                "Negotiate a settlement"
            ],
            "follow_up_questions": follow_up_questions[:2] if follow_up_questions else [
                "What specific evidence do they have?",
                "What is the deadline to respond?"
            ],
            "quick_actions": [
                "What defenses do I have?",
                "What should I do immediately?",
                "What evidence do I need?",
                "How strong is my case?",
                "What are the risks?"
            ]
        }

    async def stream_response(self, query: str, query_type: str = 'qa') -> AsyncGenerator[str, None]:
        """Stream response for better perceived speed"""
        tier = self.route_query(query, 0, query_type)
        model = self.models[tier]
        max_tokens = self.token_limits[tier]['output']
        temperature = self.temperature_settings[tier]

        prompt = self.SPEED_PROMPTS[tier](query) if query_type in ['qa', 'chat', 'question'] else query

        try:
            # Fallback to regular non-streaming for now
            response = self.claude_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Simulate streaming by yielding chunks
            full_text = response.content[0].text
            words = full_text.split()

            for i in range(0, len(words), 3):  # Yield 3 words at a time
                chunk = ' '.join(words[i:i+3]) + ' '
                yield chunk
                await asyncio.sleep(0.1)  # Small delay for streaming effect

        except Exception as e:
            yield f"Error in streaming: {str(e)}"


class ResponseFormatter:
    """Format AI responses for conciseness and practicality"""

    def __init__(self):
        self.max_response_length = 150  # words for standard responses
        self.defense_mode = True
        self.quick_actions = [
            "What defenses do I have?",
            "What should I do immediately?",
            "What evidence do I need?",
            "How strong is my case?",
            "What are the risks?"
        ]

    def format_response(self, raw_response: str) -> str:
        """Remove metaphors and flowery language, keep only essential information"""
        if not raw_response:
            return ""

        # Remove common verbose phrases
        verbose_phrases = [
            "Let me explain this in simple terms:",
            "Think of it this way:",
            "Imagine if you",
            "It's like when you",
            "Just like",
            "For example, if you",
            "To put it simply:",
            "In other words:",
            "The bottom line is:",
            "However,",
            "On the other hand,",
            "Additionally,",
            "Furthermore,",
            "Moreover,"
        ]

        cleaned = raw_response
        for phrase in verbose_phrases:
            cleaned = cleaned.replace(phrase, "")

        # Split into sentences and keep most important ones
        sentences = [s.strip() for s in cleaned.split('.') if s.strip()]
        if len(sentences) > 2:  # Even more concise - max 2 sentences
            sentences = sentences[:2]

        return '. '.join(sentences) + '.' if sentences else cleaned

    def format_defense_response(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format defense analysis for immediate actionability"""
        return {
            'current_situation': self._extract_situation(analysis),
            'defense_options': self._extract_defenses(analysis),
            'immediate_actions': self._extract_actions(analysis),
            'information_needed': self._extract_questions(analysis),
            'next_steps': self._extract_steps(analysis)
        }

    def _extract_situation(self, analysis: Dict[str, Any]) -> str:
        """Extract 1-2 sentence situation summary"""
        summary = analysis.get('summary', '')
        if len(summary) > 200:
            return summary[:200] + "..."
        return summary

    def _extract_defenses(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract top 3 defense options"""
        defenses = analysis.get('defenses', [])
        if isinstance(defenses, list):
            return [d.get('name', str(d))[:50] for d in defenses[:3]]
        return []

    def _extract_actions(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract immediate actions needed"""
        actions = analysis.get('action_items', [])
        if isinstance(actions, list):
            return [a.get('task', str(a))[:60] for a in actions[:3]]
        return []

    def _extract_questions(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract key information needed"""
        questions = analysis.get('attorney_questions', [])
        if isinstance(questions, list):
            return questions[:3]
        return []

    def _extract_steps(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract next procedural steps"""
        return [
            "Consult qualified attorney immediately",
            "Gather evidence and documentation",
            "Review all deadlines and requirements"
        ]

class DualAIProcessor:
    """
    Speed-optimized AI processing system with intelligent routing and caching
    Uses tier-based models for optimal speed vs quality balance
    """

    def __init__(self):
        # Check API keys availability first
        self.openai_available = bool(os.getenv('OPENAI_API_KEY'))
        self.claude_available = bool(os.getenv('ANTHROPIC_API_KEY'))

        # Only initialize clients if API keys are available
        self.openai_client = None
        self.claude_client = None

        if self.openai_available:
            self.openai_client = OpenAI(
                api_key=os.getenv('OPENAI_API_KEY'),
                timeout=120.0  # 2 minutes for document analysis
            )
        else:
            logger.warning("OpenAI API key not found. OpenAI features will be disabled.")

        if self.claude_available:
            self.claude_client = anthropic.Anthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                timeout=120.0  # 2 minutes for document analysis  # Add timeout for faster failure
            )
        else:
            logger.warning("Claude API key not found. Claude features will be disabled.")

        self.formatter = ResponseFormatter()

        # Initialize optimized AI client
        self.optimized_client = OptimizedAIClient()

        # ULTRA-CONCISE PROMPTS FROM CENTRALIZED CONFIG - MAXIMUM SPEED
        self.SYSTEM_PROMPT = get_prompt("qa")["system"]
        self.DEFENSE_PROMPT = get_prompt("defense_builder")["system"]

    async def analyze_document(
        self,
        text: str,
        filename: str = "",
        include_operational_details: bool = True,
        include_financial_details: bool = True
    ) -> Dict[str, Any]:
        """
        OPTIMIZED: Single-pass Claude analysis for speed (2-3s vs 10-16s)
        Now with optional enhanced operational and financial details extraction

        Args:
            text: Document text to analyze
            filename: Original filename for context
            include_operational_details: Whether to extract operational details
            include_financial_details: Whether to extract detailed financial info

        Returns:
            Fast analysis results with optional enhanced extractions
        """
        # Sanitize text to remove control characters that break JSON parsing
        text = sanitize_text_for_ai(text)
        
        analysis = None
        claude_error = None

        # Try Claude first (fast path)
        if self.claude_available:
            try:
                logger.info("Starting fast single-pass Claude analysis...")
                analysis = await self._fast_claude_analysis(text, filename)
                if analysis and analysis.get("analysis_method") != "basic_extraction":
                    logger.info("Claude analysis succeeded")
            except Exception as e:
                claude_error = str(e)
                logger.warning(f"Claude analysis failed: {claude_error}, trying OpenAI fallback...")
                analysis = None

        # Fallback to OpenAI if Claude failed or unavailable
        if analysis is None or analysis.get("analysis_method") == "basic_extraction":
            if self.openai_available:
                try:
                    logger.info("Using OpenAI as fallback for document analysis...")
                    openai_result = await self._openai_initial_analysis(text, filename)
                    if openai_result and not openai_result.get("error"):
                        # Format OpenAI result - preserve ALL fields for comprehensive analysis
                        analysis = {
                            # Document identification
                            "document_type": openai_result.get("document_type", "Legal Document"),
                            "case_caption": openai_result.get("case_caption", ""),
                            "case_number": openai_result.get("case_number"),
                            "court": openai_result.get("court"),
                            "jurisdiction": openai_result.get("jurisdiction"),
                            "filing_date": openai_result.get("filing_date"),
                            "document_number": openai_result.get("document_number"),

                            # Comprehensive summaries
                            "summary": openai_result.get("summary", ""),
                            "plain_english_summary": openai_result.get("plain_english_summary", ""),
                            "core_dispute": openai_result.get("core_dispute", ""),

                            # Parties and arguments
                            "filer": openai_result.get("filer", {}),
                            "opposing_party": openai_result.get("opposing_party", {}),
                            "all_parties": openai_result.get("all_parties", []),
                            "parties": openai_result.get("all_parties", []),  # Backwards compatibility
                            "key_arguments": openai_result.get("key_arguments", []),

                            # Dates and deadlines
                            "all_dates": openai_result.get("all_dates", []),
                            "key_dates": openai_result.get("all_dates", []),  # Backwards compatibility
                            "all_deadlines": openai_result.get("all_deadlines", []),
                            "deadlines": openai_result.get("all_deadlines", []),  # Backwards compatibility

                            # Financial information
                            "all_financial_amounts": openai_result.get("all_financial_amounts", []),
                            "financial_amounts": openai_result.get("all_financial_amounts", []),  # Backwards compatibility
                            "invoices_or_exhibits": openai_result.get("invoices_or_exhibits", []),

                            # Legal details
                            "legal_claims_and_defenses": openai_result.get("legal_claims_and_defenses", []),
                            "legal_claims": openai_result.get("legal_claims_and_defenses", []),  # Backwards compatibility
                            "cited_authority": openai_result.get("cited_authority", []),
                            "related_proceedings": openai_result.get("related_proceedings", []),
                            "evidence_referenced": openai_result.get("evidence_referenced", []),
                            "supporting_evidence": openai_result.get("evidence_referenced", []),  # Backwards compatibility

                            # Relief and next steps
                            "relief_requested": openai_result.get("relief_requested", []),
                            "hearing_info": openai_result.get("hearing_info", {}),
                            "procedural_history": openai_result.get("procedural_history", []),
                            "next_steps": openai_result.get("next_steps", []),

                            # Attorney information
                            "attorney_info": openai_result.get("attorney_info", {}),

                            # Metadata
                            "confidence": openai_result.get("confidence_score", 0.95),
                            "analysis_method": "openai_comprehensive_analysis",
                            "ai_source": "openai"
                        }
                        logger.info("OpenAI comprehensive analysis succeeded")
                except Exception as e:
                    logger.error(f"OpenAI fallback also failed: {str(e)}")

        # Final fallback to basic extraction
        if analysis is None or analysis.get("analysis_method") == "basic_extraction":
            logger.warning("Both Claude and OpenAI failed, using basic extraction")
            analysis = self._fallback_analysis(text, claude_error or "AI analysis unavailable")

        try:
            # ENHANCED: Add operational details extraction if requested
            if include_operational_details:
                logger.info("Extracting operational details...")
                operational_data = await enhanced_extractor.extract_operational_details(
                    text, filename, analysis
                )
                analysis["operational_details"] = operational_data
                logger.info("Operational details extraction completed")

            # ENHANCED: Add detailed financial extraction if requested
            if include_financial_details:
                logger.info("Extracting detailed financial information...")
                financial_data = await financial_extractor.extract_financial_details(
                    text, filename, analysis
                )
                analysis["financial_details"] = financial_data
                logger.info("Financial details extraction completed")

            logger.info(f"Analysis completed for {filename}")
            return analysis

        except Exception as e:
            logger.error(f"Error in enhanced extraction: {str(e)}")
            return analysis  # Return what we have even if enhanced extraction fails

    async def _openai_initial_analysis(self, text: str, filename: str) -> Dict[str, Any]:
        """
        OpenAI performs initial heavy lifting - data extraction and preliminary analysis
        """
        if not self.openai_available:
            return {"error": "OpenAI not available", "raw_text": text[:1000]}

        try:
            # Analyze the FULL document for complete accuracy - legal documents require 100% coverage
            # GPT-4o supports 128k context, so we can handle large documents
            text_to_analyze = text[:100000] if len(text) > 100000 else text

            prompt = f"""You are an expert legal document analyst. Your task is to create a COMPREHENSIVE and 100% ACCURATE analysis of this legal document. This analysis will be used by legal professionals who need EVERY detail captured correctly.

CRITICAL ACCURACY REQUIREMENTS:
- Extract EVERY fact, date, amount, name, and detail from the document
- Do NOT paraphrase numbers - use exact figures as written
- Do NOT summarize away important details - include everything
- If the document mentions specific invoices, list them all
- If the document references other cases or filings, include all references
- Capture ALL parties mentioned, even those referenced indirectly
- Include EVERY date mentioned with its exact context
- Quote key phrases directly when they are important

Document: {filename}
Full Text: {text_to_analyze}

Provide a COMPLETE analysis in JSON format. Be exhaustive - capture every detail:

{{
    "document_type": "exact type of document (e.g., 'Trustee's Objection to Proof of Claim')",
    "case_caption": "full case caption as it appears in the document",
    "case_number": "exact case number(s) as written",
    "court": "exact court name and division",
    "jurisdiction": "jurisdiction",
    "filing_date": "date document was filed if shown",
    "document_number": "docket/document number if shown (e.g., 'Doc 828')",

    "summary": "A COMPREHENSIVE 20-30 sentence summary that captures EVERY important aspect of this document. Include: (1) Full procedural context - what case, what stage, what prior events led to this; (2) Who filed this and their exact role; (3) What specific claim or matter is being addressed; (4) EVERY argument made - list each one with its supporting facts; (5) ALL evidence cited including specific documents, invoices, dates; (6) The opposing party's position that is being challenged; (7) EXACTLY why the filer says the opposing position is wrong - with specific facts; (8) ALL relief requested; (9) ALL procedural deadlines and next steps; (10) Any related litigation or proceedings mentioned. This must be detailed enough that someone could understand the ENTIRE document without reading it.",

    "plain_english_summary": "A 6-8 sentence explanation in simple language that captures the key dispute and why it matters. Use specific examples and numbers from the document.",

    "core_dispute": "In 3-4 sentences, explain the fundamental disagreement. What does each side claim and why do they disagree?",

    "key_arguments": [
        {{"argument": "First argument made", "supporting_facts": "specific facts/evidence cited for this argument", "legal_basis": "legal rule or principle if cited"}}
    ],

    "filer": {{"name": "exact name", "role": "exact role (e.g., Chapter 11 Trustee)", "representing": "who they represent"}},

    "opposing_party": {{"name": "exact name", "role": "their role", "their_claim": "what they are claiming/seeking"}},

    "all_parties": [
        {{"name": "exact name as written", "role": "specific role in this matter", "relationship": "relationship to the case"}}
    ],

    "all_dates": [
        {{"date": "exact date as written", "event": "what happened/happens on this date", "significance": "why this date matters"}}
    ],

    "all_deadlines": [
        {{"deadline": "exact deadline", "action_required": "what must be done", "consequence": "what happens if missed", "urgency": "high/medium/low"}}
    ],

    "all_financial_amounts": [
        {{"amount": "exact amount as written (e.g., '$920,617.94')", "description": "exactly what this amount represents", "disputed": true/false, "dispute_reason": "why disputed if applicable"}}
    ],

    "invoices_or_exhibits": [
        {{"identifier": "invoice/exhibit number or description", "amount": "amount if applicable", "date": "date if shown", "parties": "parties involved", "relevance": "why mentioned"}}
    ],

    "legal_claims_and_defenses": ["every legal claim, defense, or objection raised"],

    "cited_authority": ["any cases, statutes, rules, or legal authority cited"],

    "related_proceedings": ["any other cases, proceedings, or matters referenced"],

    "evidence_referenced": ["ALL documents, exhibits, records cited as evidence"],

    "relief_requested": ["EVERY form of relief or outcome requested"],

    "hearing_info": {{"date": "hearing date if scheduled", "time": "time if shown", "location": "courtroom/location", "purpose": "what will be decided"}},

    "procedural_history": ["key procedural events that led to this filing"],

    "next_steps": ["all actions that need to happen next"],

    "attorney_info": {{"name": "attorney name(s)", "firm": "firm name", "contact": "any contact info shown", "bar_number": "if shown"}},

    "confidence_score": 0.95
}}

ACCURACY IS PARAMOUNT: Double-check all numbers, dates, and names. If you're uncertain about any detail, note it. Do not make assumptions - only report what is explicitly stated in the document."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Use full model for maximum accuracy
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meticulous legal document analyst. Your analysis must be 100% accurate with zero errors. Extract EVERY detail from legal documents - every date, amount, name, argument, and fact. Never generalize or summarize away important details. Legal professionals depend on your accuracy. Output valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for maximum accuracy
                max_tokens=4096  # Maximum response for comprehensive output
            )

            # Parse OpenAI response
            response_text = response.choices[0].message.content

            # Extract JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            openai_data = json.loads(json_str)
            openai_data["ai_source"] = "openai"
            openai_data["raw_response"] = response_text

            return openai_data

        except Exception as e:
            logger.error(f"OpenAI analysis error: {str(e)}")
            return {"error": f"OpenAI analysis failed: {str(e)}", "ai_source": "openai"}

    async def _fast_claude_analysis(self, text: str, filename: str) -> Dict[str, Any]:
        """
        ENHANCED: Detailed Claude analysis with comprehensive summary
        Uses intelligent truncation for large documents (keeps important parts)
        Falls back to basic extraction if Claude is unavailable
        Returns structured data matching frontend component expectations
        """
        if not self.claude_available:
            logger.info("Claude not available, using fallback analysis")
            return self._extract_basic_info(text, filename)

        try:
            # SMART TRUNCATION: For very large documents, keep beginning and end
            # Most legal docs have key info at start (parties, case info) and end (relief requested)
            text_length = len(text)
            max_chars = 50000  # ~12,500 tokens - balances detail with speed

            if text_length > max_chars:
                logger.info(f"Large document ({text_length} chars) - using smart truncation to {max_chars} chars")
                # Keep first 60% and last 40% of allowed characters
                first_portion = int(max_chars * 0.6)
                last_portion = int(max_chars * 0.4)

                text_to_analyze = (
                    text[:first_portion] +
                    f"\n\n[... MIDDLE SECTION TRUNCATED - Document is {text_length} characters total ...]\n\n" +
                    text[-last_portion:]
                )
                logger.info(f"Smart truncation: keeping first {first_portion} and last {last_portion} chars")
            else:
                text_to_analyze = text
                logger.info(f"Document size ({text_length} chars) within limits - analyzing in full")

            # Select model based on document size for optimal quality
            if text_length < 10000:
                model = "claude-3-5-haiku-20241022"  # Fast model for small docs
                max_tokens = 4000
                logger.info("Using Haiku (fast) for small document")
            elif text_length < 30000:
                model = "claude-sonnet-4-5-20250929"  # Latest Sonnet 4.5 for medium docs
                max_tokens = 6000
                logger.info("Using Sonnet 4.5 (high quality) for medium document")
            else:
                model = "claude-sonnet-4-5-20250929"  # Latest Sonnet 4.5 for large docs
                max_tokens = 6000
                logger.info("Using Sonnet 4.5 (comprehensive) for large document")

            prompt = f"""You are a Harvard-trained legal document analysis expert. Analyze this legal document and provide an EXTREMELY DETAILED, COMPREHENSIVE analysis suitable for someone with no legal background.

DOCUMENT: {filename}
DOCUMENT SIZE: {text_length} characters
TEXT: {text_to_analyze}

CRITICAL: You MUST provide thorough, detailed analysis. The summary alone should be 15-25 sentences covering EVERY important aspect. Do NOT be brief - users need complete understanding.

Return ONLY valid JSON in this exact format:
{{
    "document_type": "specific type of legal document with subcategory (e.g., 'Civil Complaint - Breach of Contract', 'Motion for Summary Judgment', 'Bankruptcy Petition - Chapter 7')",

    "summary": "EXTREMELY DETAILED 15-25 sentence comprehensive summary. Start with document type and purpose. Explain the complete factual background and timeline of events. Identify ALL parties and explain their relationship to each other and to the dispute. Describe EVERY claim, allegation, or cause of action in detail with specific facts supporting each. List all legal theories and statutes being relied upon. Explain what specific relief, damages, or remedies are being sought and why. Describe the current procedural posture and what has happened in the case so far. Identify ALL critical deadlines and explain the consequences of missing them. Break down all financial amounts claimed with explanations. Discuss any settlement discussions or offers. Explain what the recipient MUST do immediately and the timeline for response. Outline potential defenses or responses available. Conclude with overall assessment of the situation's seriousness and potential outcomes.",

    "plain_english_summary": "A 3-5 sentence explanation written as if explaining to a friend with no legal knowledge. Use everyday words. Example: 'Someone is suing you because they say you didn't pay them money you owe. They're asking the court to make you pay $X plus their lawyer fees. You have 30 days to respond or they automatically win.'",

    "parties_analysis": {{
        "total_parties": 2,
        "relationship_type": "contractual/adversarial/fiduciary/etc.",
        "parties": [
            {{
                "name": "Full legal name of party",
                "role": "Plaintiff/Defendant/Petitioner/Respondent/Third-Party",
                "entity_type": "Individual/Corporation/LLC/Government Agency/etc.",
                "what_they_want": "Plain English explanation of what this party is seeking or defending against",
                "relationship_to_case": "How this party is connected to the underlying dispute"
            }}
        ]
    }},

    "timeline_analysis": {{
        "total_dates": 5,
        "critical_deadlines": [
            {{
                "date": "YYYY-MM-DD or descriptive (e.g., '30 days from service')",
                "description": "What must happen by this date",
                "consequence": "What happens if this deadline is missed",
                "urgency": "high"
            }}
        ],
        "timeline_events": [
            {{
                "date": "YYYY-MM-DD or approximate",
                "event": "What happened on this date",
                "importance": "High/Medium/Low",
                "significance": "Why this date matters to the case"
            }}
        ]
    }},

    "legal_terms": {{
        "terms_explained": {{
            "term_name": {{
                "definition": "Technical legal definition",
                "plain_english": "What this means in everyday language",
                "importance_level": "high/medium/low",
                "why_it_matters": "How this term affects the case outcome"
            }}
        }}
    }},

    "financial_analysis": {{
        "total_amount_at_stake": "$X,XXX.XX",
        "payment_amounts": ["$X for damages", "$Y for fees", "$Z for costs"],
        "payment_frequency": "one-time/monthly/annual/as-determined",
        "breakdown": [
            {{
                "category": "Compensatory Damages/Punitive Damages/Attorney Fees/Court Costs/etc.",
                "amount": "$XX,XXX.XX",
                "description": "What this amount covers and how it was calculated",
                "disputed": true
            }}
        ]
    }},

    "risk_assessment": {{
        "overall_risk_level": "High/Medium/Low",
        "risk_count": 3,
        "identified_risks": [
            {{
                "risk": "Description of the risk",
                "likelihood": "High/Medium/Low",
                "impact": "What could happen if this risk materializes",
                "mitigation": "What can be done to reduce this risk"
            }}
        ],
        "worst_case_scenario": "Plain English description of the worst possible outcome",
        "best_case_scenario": "Plain English description of the best possible outcome"
    }},

    "next_steps": [
        "First immediate action that MUST be taken with deadline",
        "Second action item with explanation of why it's important",
        "Third action item with specific instructions",
        "Fourth action - gather specific documents or evidence needed",
        "Fifth action - consider consulting with attorney about specific issues"
    ],

    "attorney_questions": [
        "Specific question to ask an attorney about this document",
        "Question about potential defenses or responses",
        "Question about likely outcomes and timeline",
        "Question about costs and alternatives"
    ],

    "key_dates": [{{"date": "YYYY-MM-DD", "description": "Detailed description of what happens"}}],
    "deadlines": [{{"date": "YYYY-MM-DD", "description": "What must be done", "urgency": "high/medium/low"}}],
    "key_terms": ["important legal terms found in document"],
    "case_number": "complete case number",
    "court": "full court name with jurisdiction",
    "amount_claimed": "total amount with breakdown",
    "financial_amounts": [{{"amount": "$XX,XXX.XX", "description": "what for", "type": "claimed/awarded/owed"}}],
    "key_figures": [{{"label": "descriptive label", "value": "$XX,XXX.XX", "context": "explanation"}}],
    "legal_claims": ["each claim with statute citations"],
    "factual_background": "detailed facts and events summary",
    "relief_requested": "all remedies being sought",
    "procedural_status": "current stage of proceedings",
    "immediate_actions": ["urgent action items"],
    "potential_risks": ["key legal risks"],
    "potential_defenses": ["possible defenses or responses available"],
    "confidence": 0.9
}}

IMPORTANT: Be THOROUGH. Users depend on this analysis to understand complex legal documents. Every field should be complete and detailed. The summary should leave no important information uncovered."""

            response = self.claude_client.messages.create(
                model=model,  # Dynamic model selection based on document size
                max_tokens=max_tokens,  # Optimized token limit
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
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                json_str = json_match.group(0) if json_match else response_text

            data = json.loads(json_str)

            # Post-process to ensure all required fields exist with proper structure
            data = self._ensure_comprehensive_fields(data, text)

            logger.info(f"Analysis complete with fields: {list(data.keys())}")
            return data

        except Exception as e:
            logger.error(f"Fast analysis error: {str(e)}, falling back to basic extraction")
            # Fallback to basic extraction instead of returning error
            return self._extract_basic_info(text, filename)

    def _ensure_comprehensive_fields(self, data: Dict[str, Any], text: str) -> Dict[str, Any]:
        """
        Ensure all required fields exist in the analysis response.
        Generates missing structured fields from available data.
        """
        # Ensure plain_english_summary exists
        if not data.get('plain_english_summary'):
            summary = data.get('summary', '')
            doc_type = data.get('document_type', 'legal document')
            # Create a simplified version
            if summary:
                # Take first 2-3 sentences and simplify
                sentences = summary.split('.')[:3]
                data['plain_english_summary'] = '. '.join(sentences) + '.'
            else:
                data['plain_english_summary'] = f"This is a {doc_type}. Please review carefully and consult an attorney."

        # Ensure parties_analysis exists with proper structure
        if not data.get('parties_analysis'):
            parties = data.get('parties', [])
            parties_list = []
            for party in parties:
                if isinstance(party, str):
                    # Parse party string like "ACME Corporation (Debtor)"
                    name = party.split('(')[0].strip() if '(' in party else party
                    role = party.split('(')[1].replace(')', '').strip() if '(' in party else "Party"
                    parties_list.append({
                        "name": name,
                        "role": role,
                        "entity_type": "Corporation" if any(c in name.upper() for c in ['LLC', 'INC', 'CORP', 'LTD', 'CORPORATION']) else "Individual",
                        "what_they_want": f"See document for {role}'s position",
                        "relationship_to_case": role
                    })
                elif isinstance(party, dict):
                    parties_list.append(party)

            data['parties_analysis'] = {
                "total_parties": len(parties_list),
                "relationship_type": "adversarial" if any(r in str(parties).lower() for r in ['plaintiff', 'defendant', 'debtor', 'creditor']) else "contractual",
                "parties": parties_list
            }

        # Ensure timeline_analysis exists
        if not data.get('timeline_analysis'):
            key_dates = data.get('key_dates', [])
            deadlines = data.get('deadlines', [])

            timeline_events = []
            for date_item in key_dates:
                if isinstance(date_item, dict):
                    timeline_events.append({
                        "date": date_item.get('date', 'Unknown'),
                        "event": date_item.get('description', 'Event'),
                        "importance": "Medium",
                        "significance": date_item.get('description', 'See document')
                    })

            critical_deadlines = []
            for deadline in deadlines:
                if isinstance(deadline, dict):
                    critical_deadlines.append({
                        "date": deadline.get('date', 'Unknown'),
                        "description": deadline.get('description', 'Deadline'),
                        "consequence": "Failure to meet this deadline may result in adverse consequences",
                        "urgency": deadline.get('urgency', 'high')
                    })

            data['timeline_analysis'] = {
                "total_dates": len(timeline_events),
                "critical_deadlines": critical_deadlines,
                "timeline_events": timeline_events
            }

        # Ensure legal_terms structure exists
        if not data.get('legal_terms') or not data.get('legal_terms', {}).get('terms_explained'):
            key_terms = data.get('key_terms', [])
            terms_explained = {}

            # Common legal term definitions
            term_definitions = {
                'motion': ('A formal request to the court', 'Asking the judge to make a decision about something'),
                'settlement': ('An agreement to resolve a dispute', 'A deal where both sides agree to end the fight'),
                'debtor': ('Person or entity that owes money', 'The person or company that owes money'),
                'creditor': ('Person or entity owed money', 'The person or company that is owed money'),
                'plaintiff': ('Party bringing a lawsuit', 'The person or company suing'),
                'defendant': ('Party being sued', 'The person or company being sued'),
                'breach': ('Violation of contract terms', 'Breaking a promise in a contract'),
                'damages': ('Money compensation for harm', 'Money to make up for harm caused'),
                'petition': ('Formal written request to court', 'A formal ask to the court'),
                'chapter 11': ('Business bankruptcy reorganization', 'A way for companies to reorganize debts while staying open'),
                'chapter 7': ('Liquidation bankruptcy', 'Selling assets to pay off debts'),
                'general unsecured claim': ('Debt without collateral', 'Money owed without property backing it up'),
                'proof of claim': ('Document proving debt owed', 'Paperwork showing how much is owed'),
                'relief': ('Remedy sought from court', 'What you are asking the court to do'),
                'jurisdiction': ('Court authority over case', 'Whether this court has the power to decide this case'),
            }

            for term in key_terms:
                term_lower = term.lower() if isinstance(term, str) else str(term).lower()
                for key, (definition, plain) in term_definitions.items():
                    if key in term_lower:
                        terms_explained[term_lower] = {
                            "definition": definition,
                            "plain_english": plain,
                            "importance_level": "high" if key in ['deadline', 'motion', 'breach', 'damages'] else "medium",
                            "why_it_matters": f"This term affects how your case will proceed"
                        }
                        break
                else:
                    # Generic entry for unknown terms
                    terms_explained[term_lower] = {
                        "definition": f"Legal term found in document",
                        "plain_english": f"A legal concept mentioned in your document",
                        "importance_level": "medium",
                        "why_it_matters": "Consult with an attorney for specific meaning in your case"
                    }

            data['legal_terms'] = {"terms_explained": terms_explained}

        # Ensure financial_analysis structure exists
        if not data.get('financial_analysis'):
            financial_amounts = data.get('financial_amounts', [])
            amount_claimed = data.get('amount_claimed', 'Unknown')

            payment_amounts = []
            breakdown = []
            for fa in financial_amounts:
                if isinstance(fa, dict):
                    payment_amounts.append(f"{fa.get('amount', 'Unknown')} - {fa.get('description', 'Amount')}")
                    breakdown.append({
                        "category": fa.get('description', 'Amount'),
                        "amount": fa.get('amount', 'Unknown'),
                        "description": fa.get('description', ''),
                        "disputed": fa.get('type', '') == 'disputed'
                    })

            data['financial_analysis'] = {
                "total_amount_at_stake": amount_claimed if amount_claimed else (financial_amounts[0].get('amount') if financial_amounts else "Unknown"),
                "payment_amounts": payment_amounts,
                "payment_frequency": "See document for payment terms",
                "breakdown": breakdown
            }

        # Ensure risk_assessment structure exists
        if not data.get('risk_assessment'):
            potential_risks = data.get('potential_risks', [])

            identified_risks = []
            for risk in potential_risks:
                if isinstance(risk, str):
                    identified_risks.append({
                        "risk": risk,
                        "likelihood": "Medium",
                        "impact": "Could affect case outcome",
                        "mitigation": "Consult with attorney for guidance"
                    })
                elif isinstance(risk, dict):
                    identified_risks.append(risk)

            # Add default risks if none identified
            if not identified_risks:
                identified_risks = [
                    {
                        "risk": "Missing response deadlines",
                        "likelihood": "High",
                        "impact": "Could result in default judgment or waived rights",
                        "mitigation": "Calendar all deadlines and respond promptly"
                    },
                    {
                        "risk": "Incomplete understanding of legal position",
                        "likelihood": "Medium",
                        "impact": "May miss important defenses or opportunities",
                        "mitigation": "Consult with qualified attorney"
                    }
                ]

            data['risk_assessment'] = {
                "overall_risk_level": "High" if any('deadline' in str(data.get('deadlines', [])).lower() or 'urgent' in str(data).lower()) else "Medium",
                "risk_count": len(identified_risks),
                "identified_risks": identified_risks,
                "worst_case_scenario": data.get('worst_case_scenario', "Failure to respond appropriately could result in adverse judgment or loss of legal rights"),
                "best_case_scenario": data.get('best_case_scenario', "With proper response and representation, matter may be resolved favorably")
            }

        # Ensure next_steps exists
        if not data.get('next_steps'):
            immediate_actions = data.get('immediate_actions', [])
            deadlines = data.get('deadlines', [])

            next_steps = []

            # Add deadline-based steps first
            for deadline in deadlines[:2]:
                if isinstance(deadline, dict):
                    next_steps.append(f"CRITICAL: {deadline.get('description', 'Meet deadline')} by {deadline.get('date', 'the specified date')}")

            # Add immediate actions
            for action in immediate_actions[:3]:
                if isinstance(action, str) and action not in next_steps:
                    next_steps.append(action)

            # Add default steps if needed
            default_steps = [
                "READ THE ENTIRE DOCUMENT CAREFULLY - Note all dates, amounts, and requirements",
                "IDENTIFY ALL DEADLINES - Missing a deadline could have serious consequences",
                "GATHER SUPPORTING DOCUMENTS - Collect all relevant records, contracts, and correspondence",
                "CONSULT AN ATTORNEY - Get professional legal advice about your options",
                "DO NOT IGNORE THIS DOCUMENT - Failing to respond could result in default judgment"
            ]

            for step in default_steps:
                if len(next_steps) < 5 and step not in next_steps:
                    next_steps.append(step)

            data['next_steps'] = next_steps[:5]

        # Ensure attorney_questions exists
        if not data.get('attorney_questions'):
            doc_type = data.get('document_type', '').lower()

            base_questions = [
                "What are my options for responding to this document?",
                "What are the strongest defenses available in my situation?",
                "What is the likely timeline and cost for resolving this matter?",
                "What are the potential outcomes if this goes to trial versus settling?"
            ]

            # Add document-type specific questions
            if 'bankruptcy' in doc_type:
                base_questions.insert(0, "How will this affect my assets and financial situation?")
            elif 'motion' in doc_type:
                base_questions.insert(0, "Should I file a response or opposition to this motion?")
            elif 'complaint' in doc_type or 'lawsuit' in doc_type:
                base_questions.insert(0, "What defenses should I raise in my answer?")
            elif 'settlement' in doc_type:
                base_questions.insert(0, "Is this settlement offer fair and should I accept it?")

            data['attorney_questions'] = base_questions[:4]

        # Ensure potential_defenses exists
        if not data.get('potential_defenses'):
            data['potential_defenses'] = [
                "Review document with attorney to identify applicable defenses",
                "Check for procedural defects or improper service",
                "Evaluate statute of limitations issues",
                "Consider any counterclaims or affirmative defenses"
            ]

        return data

    def _extract_basic_info(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Extract basic information from document without AI analysis
        Provides meaningful summary and extracted data as fallback
        Returns structured data matching frontend component expectations
        """
        import re
        from datetime import datetime

        logger.info("Performing basic text extraction (no AI)")

        lines = text.split('\n')
        text_lower = text.lower()

        # Detect document type
        doc_type = "Legal Document"
        if any(word in text_lower for word in ['complaint', 'plaintiff', 'defendant']):
            doc_type = "Legal Complaint"
        elif 'motion' in text_lower:
            doc_type = "Legal Motion"
        elif 'petition' in text_lower:
            doc_type = "Petition"
        elif 'contract' in text_lower or 'agreement' in text_lower:
            doc_type = "Contract/Agreement"
        elif 'order' in text_lower:
            doc_type = "Court Order"
        elif 'bankruptcy' in text_lower:
            doc_type = "Bankruptcy Document"
        elif 'summons' in text_lower:
            doc_type = "Summons"
        elif 'subpoena' in text_lower:
            doc_type = "Subpoena"

        # Extract parties with better structure
        parties = []
        parties_analysis = {
            "total_parties": 0,
            "relationship_type": "adversarial" if 'v.' in text or 'vs.' in text.lower() else "unknown",
            "parties": []
        }

        for i, line in enumerate(lines[:30]):  # Check first 30 lines
            line = line.strip()
            if any(word in line.lower() for word in ['plaintiff', 'petitioner', 'complainant']):
                if i > 0 and lines[i-1].strip() and len(lines[i-1].strip()) > 3:
                    party_name = lines[i-1].strip()
                    parties.append(f"{party_name} (Plaintiff)")
                    parties_analysis["parties"].append({
                        "name": party_name,
                        "role": "Plaintiff",
                        "entity_type": "Individual" if not any(corp in party_name.upper() for corp in ['LLC', 'INC', 'CORP', 'LTD']) else "Corporation",
                        "what_they_want": "Seeking damages or relief as stated in the document",
                        "relationship_to_case": "Party bringing the legal action"
                    })
            if any(word in line.lower() for word in ['defendant', 'respondent']):
                if i > 0 and lines[i-1].strip() and len(lines[i-1].strip()) > 3:
                    party_name = lines[i-1].strip()
                    parties.append(f"{party_name} (Defendant)")
                    parties_analysis["parties"].append({
                        "name": party_name,
                        "role": "Defendant",
                        "entity_type": "Individual" if not any(corp in party_name.upper() for corp in ['LLC', 'INC', 'CORP', 'LTD']) else "Corporation",
                        "what_they_want": "Defending against claims made in the document",
                        "relationship_to_case": "Party being sued or responding"
                    })

        parties_analysis["total_parties"] = len(parties_analysis["parties"])

        # Extract dates with timeline structure
        date_pattern = r'\b(?:\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b'
        dates = []
        timeline_events = []
        date_matches = list(re.finditer(date_pattern, text, re.IGNORECASE))[:5]
        for match in date_matches:
            date_str = match.group()
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].replace('\n', ' ').strip()
            dates.append({
                "date": date_str,
                "description": f"Date mentioned: {context[:60]}..."
            })
            timeline_events.append({
                "date": date_str,
                "event": context[:60] + "...",
                "importance": "Medium",
                "significance": "Date found in document - review for context"
            })

        timeline_analysis = {
            "total_dates": len(dates),
            "critical_deadlines": [],
            "timeline_events": timeline_events
        }

        # Look for deadline indicators
        deadline_patterns = [
            r'within\s+(\d+)\s+days',
            r'(\d+)\s+days\s+(?:to|from)',
            r'must\s+respond\s+by',
            r'deadline[:\s]+([^\n]+)'
        ]
        for pattern in deadline_patterns:
            match = re.search(pattern, text_lower)
            if match:
                timeline_analysis["critical_deadlines"].append({
                    "date": match.group() if match.lastindex else "See document",
                    "description": "Response or action deadline found",
                    "consequence": "Failure to meet deadline may result in default or adverse ruling",
                    "urgency": "high"
                })
                break

        # Extract dollar amounts with financial analysis structure
        amount_pattern = r'\$[\d,]+(?:\.\d{2})?'
        financial_amounts = []
        key_figures = []
        payment_amounts = []

        for match in re.finditer(amount_pattern, text):
            amount = match.group()
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].replace('\n', ' ').strip()
            context_lower = context.lower()

            description = "Unspecified amount"
            amount_type = "mentioned"

            if any(word in context_lower for word in ['damage', 'damages', 'compensation']):
                description = "Damages or compensation"
                amount_type = "claimed"
            elif any(word in context_lower for word in ['fee', 'fees', 'cost', 'costs']):
                description = "Fees or costs"
                amount_type = "claimed"
            elif any(word in context_lower for word in ['settlement', 'offer']):
                description = "Settlement offer"
                amount_type = "offered"
            elif any(word in context_lower for word in ['debt', 'owed', 'owing']):
                description = "Debt owed"
                amount_type = "owed"
            elif any(word in context_lower for word in ['contract', 'agreement', 'value']):
                description = "Contract value"
                amount_type = "contracted"

            financial_amounts.append({
                "amount": amount,
                "description": description,
                "type": amount_type
            })
            key_figures.append({
                "label": description,
                "value": amount,
                "context": context[:100]
            })
            payment_amounts.append(f"{amount} - {description}")

        # Deduplicate amounts
        seen_amounts = set()
        unique_financial_amounts = []
        unique_key_figures = []
        unique_payment_amounts = []
        for fa, kf, pa in zip(financial_amounts, key_figures, payment_amounts):
            if fa['amount'] not in seen_amounts:
                seen_amounts.add(fa['amount'])
                unique_financial_amounts.append(fa)
                unique_key_figures.append(kf)
                unique_payment_amounts.append(pa)
                if len(unique_financial_amounts) >= 5:
                    break

        financial_analysis = {
            "total_amount_at_stake": unique_financial_amounts[0]['amount'] if unique_financial_amounts else "Unknown",
            "payment_amounts": unique_payment_amounts,
            "payment_frequency": "one-time",
            "breakdown": [
                {
                    "category": fa["description"],
                    "amount": fa["amount"],
                    "description": fa["description"],
                    "disputed": True
                } for fa in unique_financial_amounts
            ]
        }

        # Extract case number
        case_pattern = r'(?:Case|Cause)\s+(?:No|Number|#)[:\s]+([A-Z0-9-]+)'
        case_match = re.search(case_pattern, text, re.IGNORECASE)
        case_number = case_match.group(1) if case_match else None

        # Extract key legal terms with explanations
        legal_terms = []
        legal_terms_explained = {}
        common_terms = {
            'breach': 'Breaking the terms of an agreement or contract',
            'contract': 'A legally binding agreement between parties',
            'damages': 'Money paid as compensation for loss or injury',
            'negligence': 'Failure to take proper care in doing something',
            'liability': 'Legal responsibility for something',
            'complaint': 'The initial document that starts a lawsuit',
            'motion': 'A formal request to the court for a ruling or order',
            'plaintiff': 'The person or entity bringing a lawsuit',
            'defendant': 'The person or entity being sued',
            'judgment': 'The final decision of a court',
            'relief': 'The remedy or outcome sought from the court',
            'summons': 'A document requiring appearance in court'
        }
        for term, definition in common_terms.items():
            if term in text_lower:
                legal_terms.append(term.title())
                legal_terms_explained[term] = {
                    "definition": definition,
                    "plain_english": definition,
                    "importance_level": "medium",
                    "why_it_matters": f"This term appears in your document and affects your legal situation"
                }

        # Generate comprehensive summary
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
        if paragraphs:
            summary = f"This is a {doc_type}. " + " ".join(paragraphs[:3])[:600] + "..."
        else:
            meaningful_lines = [l.strip() for l in lines if len(l.strip()) > 20][:7]
            summary = f"This is a {doc_type}. " + " ".join(meaningful_lines)[:600] + "..."

        # Plain English summary
        plain_english = f"You have received a {doc_type.lower()}. "
        if unique_financial_amounts:
            plain_english += f"The document involves {unique_financial_amounts[0]['amount']}. "
        plain_english += "Please review the document carefully and consider consulting with an attorney to understand your options and any required responses."

        # Risk assessment
        risk_assessment = {
            "overall_risk_level": "Medium",
            "risk_count": 2,
            "identified_risks": [
                {
                    "risk": "Missing response deadlines",
                    "likelihood": "High",
                    "impact": "Default judgment could be entered against you",
                    "mitigation": "Identify all deadlines and respond promptly"
                },
                {
                    "risk": "Incomplete understanding of claims",
                    "likelihood": "Medium",
                    "impact": "May miss important defenses or opportunities",
                    "mitigation": "Consult with a qualified attorney for complete analysis"
                }
            ],
            "worst_case_scenario": "If you don't respond appropriately, you could face a default judgment or lose important legal rights",
            "best_case_scenario": "With proper response and representation, you may be able to resolve this matter favorably"
        }

        # Next steps
        next_steps = [
            "READ THE ENTIRE DOCUMENT CAREFULLY - Note all dates, deadlines, and amounts mentioned",
            "IDENTIFY THE RESPONSE DEADLINE - Most legal documents require a response within a specific timeframe",
            "GATHER RELEVANT DOCUMENTS - Collect any contracts, correspondence, or records related to this matter",
            "CONSULT AN ATTORNEY - Consider seeking legal advice to understand your options and potential defenses",
            "DO NOT IGNORE THIS DOCUMENT - Failing to respond could result in a default judgment against you"
        ]

        return {
            "document_type": doc_type,
            "summary": summary,
            "plain_english_summary": plain_english,
            "parties": parties if parties else ["Parties not clearly identified in document"],
            "parties_analysis": parties_analysis,
            "key_dates": dates,
            "deadlines": timeline_analysis["critical_deadlines"],
            "timeline_analysis": timeline_analysis,
            "key_terms": legal_terms[:10],
            "legal_terms": {"terms_explained": legal_terms_explained},
            "case_number": case_number,
            "court": None,
            "amount_claimed": unique_financial_amounts[0]['amount'] if unique_financial_amounts else None,
            "financial_amounts": unique_financial_amounts,
            "financial_analysis": financial_analysis,
            "key_figures": unique_key_figures,
            "legal_claims": [],
            "risk_assessment": risk_assessment,
            "next_steps": next_steps,
            "attorney_questions": [
                "What are my options for responding to this document?",
                "What defenses might be available to me?",
                "What is the likely timeline and cost for resolving this matter?",
                "Are there any immediate actions I should take to protect my interests?"
            ],
            "immediate_actions": next_steps[:3],
            "potential_risks": [r["risk"] for r in risk_assessment["identified_risks"]],
            "potential_defenses": ["Review document with attorney to identify applicable defenses"],
            "confidence": 0.6,
            "analysis_method": "basic_extraction",
            "note": "This analysis was performed using basic text extraction. For detailed AI analysis, configure Claude API key."
        }

    async def _claude_finalization(self, text: str, openai_analysis: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """
        DEPRECATED: Legacy dual-AI method (kept for compatibility)
        """
        # Redirect to fast analysis
        return await self._fast_claude_analysis(text, filename)

    def _combine_analyses(self, openai_analysis: Dict[str, Any], claude_analysis: Dict[str, Any], text: str, filename: str) -> Dict[str, Any]:
        """
        Combine both AI analyses into a comprehensive final result
        """
        combined = {
            "filename": filename,
            "analysis_type": "dual_ai_enhanced",
            "processing_pipeline": ["openai_extraction", "claude_enhancement"],
            "timestamp": None,

            # Core analysis (preferring Claude's enhanced version)
            "document_type": claude_analysis.get("enhanced_analysis", {}).get("corrected_document_type") or openai_analysis.get("document_type", "Unknown"),
            "summary": claude_analysis.get("document_summary", openai_analysis.get("summary", "Document processed")),

            # OpenAI's detailed extraction
            "openai_extraction": {
                "parties": openai_analysis.get("parties", []),
                "key_dates": openai_analysis.get("key_dates", []),
                "deadlines": openai_analysis.get("deadlines", []),
                "financial_amounts": openai_analysis.get("financial_amounts", []),
                "legal_claims": openai_analysis.get("legal_claims", []),
                "case_number": openai_analysis.get("case_number"),
                "court": openai_analysis.get("court"),
                "jurisdiction": openai_analysis.get("jurisdiction"),
                "legal_issues": openai_analysis.get("legal_issues", []),
                "confidence": openai_analysis.get("confidence_score", 0.7)
            },

            # Claude's enhanced insights
            "claude_enhancement": {
                "what_this_means": claude_analysis.get("what_this_means", "Analysis completed"),
                "good_news": claude_analysis.get("good_news", "None identified"),
                "bad_news": claude_analysis.get("bad_news", "Review recommended"),
                "what_to_do_next": claude_analysis.get("what_to_do_next", ["Consult with attorney"]),
                "complexity_rating": claude_analysis.get("complexity_rating", 5),
                "urgency_rating": claude_analysis.get("urgency_rating", 5),
                "harvard_professor_notes": claude_analysis.get("harvard_professor_notes", "Professional review recommended"),
                "simple_explanation": claude_analysis.get("simple_explanation", {}),
                "confidence": claude_analysis.get("confidence_in_analysis", 0.8)
            },

            # Combined critical information
            "parties": claude_analysis.get("enhanced_analysis", {}).get("complete_parties_list") or openai_analysis.get("parties", []),
            "deadlines": self._normalize_deadlines(
                claude_analysis.get("enhanced_analysis", {}).get("critical_deadlines") or
                openai_analysis.get("deadlines", [])
            ),
            "key_dates": self._normalize_deadlines(openai_analysis.get("key_dates", [])),
            "case_number": openai_analysis.get("case_number"),
            "court": openai_analysis.get("court"),

            # Quality metrics
            "analysis_quality": {
                "openai_completeness": openai_analysis.get("extraction_completeness", "Unknown"),
                "claude_accuracy_check": claude_analysis.get("legal_accuracy_check", "Not assessed"),
                "missed_by_openai": claude_analysis.get("missed_by_openai", []),
                "overall_confidence": (openai_analysis.get("confidence_score", 0.7) + claude_analysis.get("confidence_in_analysis", 0.8)) / 2
            },

            # Fallback fields for compatibility
            "confidence": (openai_analysis.get("confidence_score", 0.7) + claude_analysis.get("confidence_in_analysis", 0.8)) / 2,
            "key_terms": self._normalize_key_terms(
                openai_analysis.get("legal_issues", []) + openai_analysis.get("legal_claims", [])
            ),
            "requesting": claude_analysis.get("what_this_means", "Dual-AI analysis completed")
        }

        # Add error information if any AI failed
        if openai_analysis.get("error"):
            combined["openai_error"] = openai_analysis["error"]
        if claude_analysis.get("error"):
            combined["claude_error"] = claude_analysis["error"]

        return combined

    def _normalize_deadlines(self, deadlines_data) -> list:
        """
        Normalize deadlines data to ensure consistent array format.

        Args:
            deadlines_data: Raw deadlines data from AI models (could be str, list, dict, None)

        Returns:
            List of deadline objects with consistent structure
        """
        if not deadlines_data:
            return []

        # If it's already a list, validate each item
        if isinstance(deadlines_data, list):
            normalized = []
            for item in deadlines_data:
                if isinstance(item, dict):
                    # Ensure required fields exist
                    normalized_item = {
                        'date': item.get('date', 'No date specified'),
                        'description': item.get('description', 'No description available')
                    }
                    # Preserve additional fields
                    for key, value in item.items():
                        if key not in ['date', 'description']:
                            normalized_item[key] = value
                    normalized.append(normalized_item)
                elif isinstance(item, str) and item.strip():
                    # Handle string entries
                    normalized.append({
                        'date': 'Unknown',
                        'description': item.strip()
                    })
            return normalized

        # If it's a string, try to parse it or return as single item
        if isinstance(deadlines_data, str) and deadlines_data.strip():
            return [{
                'date': 'Unknown',
                'description': deadlines_data.strip()
            }]

        # If it's a dict, treat as single deadline
        if isinstance(deadlines_data, dict):
            return [{
                'date': deadlines_data.get('date', 'Unknown'),
                'description': deadlines_data.get('description', 'No description available')
            }]

        # Fallback to empty array
        return []

    def _normalize_key_terms(self, key_terms_data) -> list:
        """
        Normalize key_terms data to ensure consistent string array format.

        Args:
            key_terms_data: Raw key terms data (could be str, list, None)

        Returns:
            List of strings representing key terms
        """
        if not key_terms_data:
            return []

        # If it's already a list, ensure all items are strings
        if isinstance(key_terms_data, list):
            normalized = []
            for item in key_terms_data:
                if isinstance(item, str) and item.strip():
                    normalized.append(item.strip())
                elif isinstance(item, dict) and item.get('term'):
                    # Handle objects with term field
                    normalized.append(str(item['term']).strip())
                elif item:  # Any other truthy value
                    normalized.append(str(item).strip())
            return normalized

        # If it's a string, split by common delimiters or return as single item
        if isinstance(key_terms_data, str) and key_terms_data.strip():
            # Try to split on common delimiters
            for delimiter in [',', ';', '\n', '|']:
                if delimiter in key_terms_data:
                    return [term.strip() for term in key_terms_data.split(delimiter) if term.strip()]
            # No delimiters found, return as single term
            return [key_terms_data.strip()]

        # Fallback to empty array
        return []

    async def ask_document_question(self, prompt: str) -> Dict[str, Any]:
        """
        Ultra-fast Q&A using optimized AI client with caching and intelligent routing
        Returns structured response with defense options and quick actions
        """
        try:
            if not self.openai_available and not self.claude_available:
                return {
                    "answer": "AI Q&A service is not available. Please configure API keys.",
                    "defense_options": [],
                    "follow_up_questions": [],
                    "quick_actions": self.formatter.quick_actions
                }

            # Use optimized client for maximum speed
            if self.claude_available:
                response = await self.optimized_client.process_query(
                    query=prompt,
                    query_type='qa'
                )

                # Ensure all required fields are present
                response.setdefault('answer', 'Please provide more details about your legal situation.')
                response.setdefault('defense_options', [
                    "Challenge the evidence",
                    "Question the procedures",
                    "Negotiate a settlement"
                ])
                response.setdefault('follow_up_questions', [
                    "What specific evidence do they have?",
                    "What is the deadline to respond?"
                ])
                response.setdefault('quick_actions', self.formatter.quick_actions)

                return response

            # Fallback to direct Claude call if optimized client fails
            elif self.openai_available:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": ULTRA_CONCISE_PROMPT.format(query="")
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=500  # Increased for structured response
                )
                return self._parse_structured_response(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Error in optimized Q&A: {str(e)}")
            return {
                "answer": f"Error: {str(e)}. Please try again.",
                "defense_options": [],
                "follow_up_questions": [],
                "quick_actions": self.formatter.quick_actions
            }

    async def _harvard_lawyer_qa(self, prompt: str) -> str:
        """
        Ultra-concise approach: Maximum 3 sentences, simple words only
        """
        try:
            # STEP 1: Harvard-level legal analysis with Claude
            harvard_analysis = self.claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1500,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Legal question: {prompt}

Provide brief analysis:
1. Key legal issues
2. Relevant principles
3. Main risks/opportunities
4. Next steps

Be concise and direct."""
                    }
                ]
            )

            return harvard_analysis.content[0].text

        except Exception as e:
            logger.error(f"Error in Harvard Lawyer Q&A: {str(e)}")
            # Fallback to simple Claude response
            if self.claude_available:
                response = self.claude_client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=1000,
                    messages=[{"role": "user", "content": f"Answer this legal question in simple terms: {prompt}"}]
                )
                return response.content[0].text
            return f"I encountered an error in my analysis: {str(e)}. Please try again."

    async def generate_strategic_questions(self, document_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate brilliant questions based on document gaps that could strengthen the case
        Uses SmartQuestionGenerator for specialized legal areas + Harvard-level AI analysis
        """
        try:
            # STEP 1: Get specialized questions from SmartQuestionGenerator
            smart_generator = SmartQuestionGenerator()
            doc_type = document_analysis.get('document_type', 'litigation')
            specialized_questions = smart_generator.get_questions_for_area(doc_type, document_analysis)

            if not self.claude_available:
                # Return specialized questions + basic questions if no AI available
                basic_questions = self._generate_basic_questions(document_analysis)
                return specialized_questions + basic_questions

            # STEP 1: Harvard-level analysis to identify gaps
            gap_analysis = self.claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2000,
                temperature=0.2,
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        {format_prompt("strategic", "analyze this document and identify missing information")}
                        that could be strategically important.

                        Document Analysis: {json.dumps(document_analysis, indent=2)}

                        Identify critical missing information that could:
                        1. Win the case or strengthen the position
                        2. Reveal hidden defenses or counterclaims
                        3. Show attorney malpractice or ineffective counsel
                        4. Find procedural errors or jurisdictional issues
                        5. Identify conflicts of interest
                        6. Uncover statute of limitations issues
                        7. Reveal evidence preservation problems
                        8. Show improper service or notice issues
                        9. Find discovery violations or sanctions
                        10. Identify settlement opportunities or leverage

                        For each gap, explain:
                        - What information is missing
                        - Why it's strategically important
                        - How it could change the case outcome
                        - What questions to ask to get this information

                        Provide a JSON response with strategic question categories.
                        """
                    }
                ]
            )

            # STEP 2: Convert to simple, actionable questions if we have OpenAI
            if self.openai_available:
                simple_questions = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": """
                            You are a Harvard Law expert who asks questions like you're talking to an 8-year-old.
                            Take complex legal strategy and turn it into simple questions anyone can understand.

                            Convert each strategic legal question into:
                            - Simple words (no legal jargon)
                            - Questions a regular person can ask
                            - Clear explanation of why the question matters
                            - Simple examples they can relate to

                            Example:
                            Instead of: "Was there proper service of process pursuant to Rule 4?"
                            Say: "Did they deliver the legal papers to you the right way? (This matters because if they didn't follow the rules for giving you the papers, the whole case might get thrown out - like if someone didn't follow the rules in a game.)"
                            """
                        },
                        {
                            "role": "user",
                            "content": f"""
                            Convert this Harvard-level legal analysis into simple questions:

                            {gap_analysis.content[0].text}

                            Create 8-10 strategic questions that:
                            1. Use simple words
                            2. Explain why each question matters
                            3. Give examples a regular person can understand
                            4. Are organized by importance

                            Format as JSON: {{"questions": [{{"question": "simple question", "why_important": "simple explanation", "category": "category_name"}}]}}
                            """
                        }
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )

                # Parse the response
                try:
                    response_text = simple_questions.choices[0].message.content
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        json_str = response_text[json_start:json_end].strip()
                    else:
                        json_str = response_text.strip()

                    questions_data = json.loads(json_str)
                    ai_questions = questions_data.get("questions", [])
                    # Combine specialized questions with AI-generated questions
                    return specialized_questions + ai_questions

                except json.JSONDecodeError:
                    logger.warning("Could not parse strategic questions JSON")
                    # Return specialized questions + basic questions as fallback
                    basic_questions = self._generate_basic_questions(document_analysis)
                    return specialized_questions + basic_questions

            else:
                # Just use Claude's analysis directly + specialized questions
                claude_questions = self._parse_claude_questions(gap_analysis.content[0].text)
                return specialized_questions + claude_questions

        except Exception as e:
            logger.error(f"Error generating strategic questions: {str(e)}")
            # Even on error, try to provide specialized questions + basic fallback
            try:
                smart_generator = SmartQuestionGenerator()
                doc_type = document_analysis.get('document_type', 'litigation')
                specialized_questions = smart_generator.get_questions_for_area(doc_type, document_analysis)
                basic_questions = self._generate_basic_questions(document_analysis)
                return specialized_questions + basic_questions
            except:
                return self._generate_basic_questions(document_analysis)

    def _generate_basic_questions(self, document_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate basic questions when AI is not available"""
        doc_type = document_analysis.get('document_type', '').lower()

        basic_questions = [
            {
                "question": "Who are all the people involved in this case?",
                "why_important": "We need to know everyone involved to make sure we don't miss anyone important.",
                "category": "parties"
            },
            {
                "question": "What are the important dates and deadlines?",
                "why_important": "Missing a deadline could hurt your case badly.",
                "category": "deadlines"
            },
            {
                "question": "What evidence do we have to support our side?",
                "why_important": "Evidence is like proof that shows who's right.",
                "category": "evidence"
            },
            {
                "question": "What evidence might the other side have?",
                "why_important": "We need to know what they might use against us.",
                "category": "evidence"
            },
            {
                "question": "Are there any witnesses who saw what happened?",
                "why_important": "Witnesses can tell the judge what really happened.",
                "category": "witnesses"
            }
        ]

        # Add document-specific questions
        if 'complaint' in doc_type or 'lawsuit' in doc_type:
            basic_questions.extend([
                {
                    "question": "Did this happen within the time limit for filing a lawsuit?",
                    "why_important": "There are time limits for complaining about things legally.",
                    "category": "timeliness"
                },
                {
                    "question": "Did they follow the right rules to start this lawsuit?",
                    "why_important": "If they didn't follow the rules, the case might get thrown out.",
                    "category": "procedure"
                }
            ])

        elif 'motion' in doc_type:
            basic_questions.extend([
                {
                    "question": "What exactly are they asking the judge to do?",
                    "why_important": "We need to understand what they want so we can respond properly.",
                    "category": "relief"
                },
                {
                    "question": "Do they have good reasons for what they're asking?",
                    "why_important": "The judge will only say yes if they have good legal reasons.",
                    "category": "merit"
                }
            ])

        return basic_questions[:8]  # Limit to 8 questions

    def _parse_claude_questions(self, claude_text: str) -> List[Dict[str, str]]:
        """Parse Claude's gap analysis into structured questions"""
        # This is a simplified parser - in production you'd want more sophisticated parsing
        questions = []
        lines = claude_text.split('\n')

        current_question = None
        current_importance = None

        for line in lines:
            line = line.strip()
            if line.startswith('?') or 'question:' in line.lower():
                if current_question and current_importance:
                    questions.append({
                        "question": current_question,
                        "why_important": current_importance,
                        "category": "strategic"
                    })
                current_question = line.replace('question:', '').strip('? ')
                current_importance = None
            elif 'important' in line.lower() or 'because' in line.lower():
                current_importance = line

        # Add the last question if we have one
        if current_question and current_importance:
            questions.append({
                "question": current_question,
                "why_important": current_importance,
                "category": "strategic"
            })

        return questions[:10]  # Limit to 10 questions

    def _parse_structured_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Parse structured response into components
        """
        lines = raw_response.split('\n')

        answer = ""
        defense_options = []
        follow_up_questions = []

        current_section = "answer"

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.lower().startswith('answer:'):
                answer = line.replace('Answer:', '').strip()
                current_section = "answer"
            elif 'defense option' in line.lower():
                current_section = "defense"
            elif 'question' in line.lower() and ('for you' in line.lower() or line.endswith(':')):
                current_section = "questions"
            elif line.startswith('•') or line.startswith('-'):
                if current_section == "defense":
                    defense_options.append(line[1:].strip())
            elif line.startswith(('1.', '2.', '3.')):
                if current_section == "questions":
                    follow_up_questions.append(line[2:].strip())
            elif current_section == "answer" and not answer:
                answer = line

        # Clean up answer with formatter
        answer = self.formatter.format_response(answer)

        return {
            "answer": answer or "Please provide more details about your legal situation.",
            "defense_options": defense_options[:3] if defense_options else [
                "Challenge the evidence",
                "Question the procedures",
                "Negotiate a settlement"
            ],
            "follow_up_questions": follow_up_questions[:2] if follow_up_questions else [
                "What specific evidence do they have against you?",
                "What is the deadline to respond?"
            ],
            "quick_actions": self.formatter.quick_actions
        }

    async def analyze_defenses(self, prompt: str) -> str:
        """
        Speed-optimized defense analysis using intelligent routing
        """
        try:
            if not self.claude_available and not self.openai_available:
                return "Defense analysis is not available. Please configure API keys."

            # Use optimized client for fast defense analysis
            if self.claude_available:
                response = await self.optimized_client.process_query(
                    query=prompt,
                    query_type='defense_strategy'
                )

                if response.get('analysis'):
                    return self.formatter.format_response(response['analysis'])
                elif response.get('answer'):
                    return self.formatter.format_response(response['answer'])
                else:
                    return "Defense analysis completed. Please consult with a qualified attorney."

            # Fallback to OpenAI
            elif self.openai_available:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a legal defense strategy analyst. Analyze documents and identify potential defenses clearly and accurately."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1500
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in optimized defense analysis: {str(e)}")
            return f"I encountered an error while analyzing defenses: {str(e)}. Please consult with a qualified attorney."

    async def analyze_attorney_obligations(self, prompt: str) -> str:
        """
        Enhanced attorney tracking using dual-AI
        """
        try:
            if not self.claude_available and not self.openai_available:
                return "Dual-AI attorney tracking is not available. Please configure API keys."

            # Use Claude Sonnet 4.5 for attorney analysis (better at ethical/professional analysis)
            if self.claude_available:
                response = self.claude_client.messages.create(
                    model='claude-sonnet-4-5-20250929',  # Latest Sonnet 4.5 for professional analysis
                    max_tokens=500,  # Enough for JSON
                    temperature=0,
                    messages=[
                        {
                            "role": "user",
                            "content": f"""{prompt}

Respond ONLY with valid JSON in this exact format:
{{
  "obligations": [
    {{"task": "Description", "deadline": "Date", "priority": "HIGH|MEDIUM|LOW"}}
  ]
}}"""
                        }
                    ]
                )
                return response.content[0].text

            # Fallback to OpenAI
            elif self.openai_available:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an attorney performance analyst. Focus on professional accountability while respecting legal ethics."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1200
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in dual-AI attorney analysis: {str(e)}")
            return f"I encountered an error analyzing attorney obligations: {str(e)}. Please discuss directly with your attorney."

    def _fallback_analysis(self, text: str, error_msg: str = "") -> Dict[str, Any]:
        """
        Provide basic analysis when dual-AI is not available
        """
        logger.warning(f"Using fallback analysis. Error: {error_msg}")

        # Basic text analysis
        words = text.lower().split()

        # Detect document type based on keywords
        doc_type = "Legal Document"
        if "motion" in words:
            doc_type = "Motion"
        elif "petition" in words:
            doc_type = "Petition"
        elif "order" in words:
            doc_type = "Order"
        elif "contract" in words or "agreement" in words:
            doc_type = "Contract"
        elif "brief" in words:
            doc_type = "Brief"
        elif "complaint" in words:
            doc_type = "Complaint"

        return {
            "analysis_type": "fallback_basic",
            "document_type": doc_type,
            "summary": "Document uploaded and processed. Dual-AI analysis unavailable - using basic text processing.",
            "parties": [],
            "key_dates": [],
            "deadlines": [],
            "confidence": 0.3,  # Low confidence for fallback
            "key_terms": [],
            "case_number": None,
            "court": None,
            "requesting": "Basic document processing completed",
            "claude_enhancement": {
                "what_this_means": "Document was processed with basic tools only",
                "good_news": "Document was successfully uploaded",
                "bad_news": "Advanced AI analysis was not available",
                "what_to_do_next": ["Set up OpenAI and Claude API keys for full analysis", "Consult with attorney for professional review"],
                "complexity_rating": 5,
                "urgency_rating": 5,
                "simple_explanation": {
                    "imagine_you_are": "Basic text processing only. AI analysis unavailable.",
                    "the_main_problem": "We can read the document but can't understand it deeply",
                    "what_might_happen": "You'll need professional help to understand what this document means",
                    "why_this_matters": "Legal documents are important and need expert analysis"
                }
            },
            "error_message": error_msg
        }

class SmartQuestionGenerator:
    """
    Harvard-level specialized question generator for specific legal areas
    Generates strategic questions in simple English
    """

    def generate_bankruptcy_questions(self, gaps):
        """Harvard-level bankruptcy questions in simple English"""
        return [
            {
                "question": "Did anyone tell you about the meeting where people you owe money to can ask questions? When is it?",
                "why_important": "This meeting is required by law and missing it could hurt your case.",
                "category": "procedural",
                "area": "bankruptcy"
            },
            {
                "question": "Do you have a house? Is it worth more than what you owe on it?",
                "why_important": "If your house is worth more than your loan, you might be able to keep it.",
                "category": "assets",
                "area": "bankruptcy"
            },
            {
                "question": "In the last 90 days, did you pay any friend or family member more than $600?",
                "why_important": "The court might want this money back to pay other people you owe.",
                "category": "transfers",
                "area": "bankruptcy"
            },
            {
                "question": "Do you have stuff that the law says nobody can take from you? Like your car for work?",
                "why_important": "Some things are protected and you get to keep them even in bankruptcy.",
                "category": "exemptions",
                "area": "bankruptcy"
            },
            {
                "question": "Did your lawyer explain Chapter 7 vs Chapter 13? Chapter 7 liquidates assets. Chapter 13 sets payment plan.",
                "why_important": "Choosing the wrong type could cost you money or property.",
                "category": "strategy",
                "area": "bankruptcy"
            }
        ]

    def generate_litigation_questions(self, gaps):
        """Harvard-level litigation questions in simple English"""
        return [
            {
                "question": "When did this problem first happen? The law has a timer - like milk has an expiration date.",
                "why_important": "If too much time passed, you might not be able to sue or defend yourself.",
                "category": "timeliness",
                "area": "litigation"
            },
            {
                "question": "Did you get the papers delivered to you the right way? There are rules about how legal papers must be given to you.",
                "why_important": "If they didn't follow the rules, the whole case might get thrown out.",
                "category": "service",
                "area": "litigation"
            },
            {
                "question": "Do you have witnesses who saw what happened? Can they still remember and talk about it?",
                "why_important": "Witnesses are like having other people tell the judge your side of the story.",
                "category": "evidence",
                "area": "litigation"
            },
            {
                "question": "Did you write anything down when this happened? Emails, texts, notes, pictures?",
                "why_important": "Written proof is like having a recording of what really happened.",
                "category": "documentation",
                "area": "litigation"
            },
            {
                "question": "Are you being sued in the right place? Did this happen where they filed the lawsuit?",
                "why_important": "If it's the wrong place, the case might have to start over somewhere else.",
                "category": "jurisdiction",
                "area": "litigation"
            }
        ]

    def generate_contract_questions(self, gaps):
        """Harvard-level contract questions in simple English"""
        return [
            {
                "question": "Did both people really agree to this deal? Did anyone force or trick someone?",
                "why_important": "If someone was forced or tricked, the contract might not count.",
                "category": "formation",
                "area": "contract"
            },
            {
                "question": "Was this written down properly? Did both people sign it?",
                "why_important": "Some contracts have to be written and signed or they don't count.",
                "category": "formalities",
                "area": "contract"
            },
            {
                "question": "Did someone not do what they promised? What exactly didn't they do?",
                "why_important": "You have to prove exactly what promise was broken.",
                "category": "breach",
                "area": "contract"
            },
            {
                "question": "How much money did you lose because they broke their promise?",
                "why_important": "You can only get back the money you actually lost because of their broken promise.",
                "category": "damages",
                "area": "contract"
            },
            {
                "question": "Did you do everything you were supposed to do first?",
                "why_important": "If you didn't keep your promises, you might not be able to complain about theirs.",
                "category": "performance",
                "area": "contract"
            }
        ]

    def generate_family_law_questions(self, gaps):
        """Harvard-level family law questions in simple English"""
        return [
            {
                "question": "Are the kids safe and happy where they are now?",
                "why_important": "The judge cares most about what's best for the children.",
                "category": "child_welfare",
                "area": "family"
            },
            {
                "question": "Who has been taking care of the kids day-to-day? School, doctor visits, meals?",
                "why_important": "Judges like to keep kids with the parent who has been doing the daily care.",
                "category": "custody",
                "area": "family"
            },
            {
                "question": "How much money does each parent make? Do you have pay stubs?",
                "why_important": "Child support is calculated based on how much money each parent makes.",
                "category": "support",
                "area": "family"
            },
            {
                "question": "What stuff do you own together? House, cars, bank accounts, retirement money?",
                "why_important": "Most things bought during marriage get split between both people.",
                "category": "property",
                "area": "family"
            },
            {
                "question": "Did anyone hurt anyone? Do you have pictures, police reports, or medical records?",
                "why_important": "Violence can change everything about custody and living arrangements.",
                "category": "safety",
                "area": "family"
            }
        ]

    def generate_criminal_questions(self, gaps):
        """Harvard-level criminal questions in simple English"""
        return [
            {
                "question": "Did the police tell you your rights? Like the right to stay quiet and have a lawyer?",
                "why_important": "If they didn't tell you your rights, some evidence might not be allowed in court.",
                "category": "rights",
                "area": "criminal"
            },
            {
                "question": "Did the police have permission to search you or your stuff? Did they have a warrant?",
                "why_important": "If they searched illegally, the evidence might get thrown out.",
                "category": "search",
                "area": "criminal"
            },
            {
                "question": "Do you have an alibi? Were you somewhere else when this happened? Who can prove it?",
                "why_important": "If you can prove you were somewhere else, you couldn't have done the crime.",
                "category": "alibi",
                "area": "criminal"
            },
            {
                "question": "Did the police follow all the rules when they arrested you?",
                "why_important": "If they broke the rules, some evidence might not be allowed.",
                "category": "procedure",
                "area": "criminal"
            },
            {
                "question": "Do you understand what you're being accused of? What could happen if you're found guilty?",
                "why_important": "You need to know exactly what you're facing to make good decisions.",
                "category": "charges",
                "area": "criminal"
            }
        ]

    def generate_employment_questions(self, gaps):
        """Harvard-level employment questions in simple English"""
        return [
            {
                "question": "Did you get fired for a good reason? Did your boss follow the company rules?",
                "why_important": "If they didn't follow their own rules, you might have been fired illegally.",
                "category": "termination",
                "area": "employment"
            },
            {
                "question": "Did anyone treat you badly because of your race, age, religion, or gender?",
                "why_important": "It's illegal to treat someone badly at work because of who they are.",
                "category": "discrimination",
                "area": "employment"
            },
            {
                "question": "Did you complain about something dangerous or illegal at work before you got fired?",
                "why_important": "It's illegal to fire someone for reporting dangerous or illegal things.",
                "category": "retaliation",
                "area": "employment"
            },
            {
                "question": "Did you get paid for all the hours you worked? Including overtime?",
                "why_important": "Your boss has to pay you for every hour you work, plus extra for overtime.",
                "category": "wages",
                "area": "employment"
            },
            {
                "question": "Do you have an employment contract? What does it say about getting fired?",
                "why_important": "If you have a contract, your boss might only be able to fire you for certain reasons.",
                "category": "contract",
                "area": "employment"
            }
        ]

    def get_questions_for_area(self, legal_area: str, document_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get specialized questions based on legal area"""
        area_lower = legal_area.lower()
        gaps = document_analysis  # Use document analysis as gaps indicator

        if 'bankruptcy' in area_lower:
            return self.generate_bankruptcy_questions(gaps)
        elif 'litigation' in area_lower or 'lawsuit' in area_lower or 'complaint' in area_lower:
            return self.generate_litigation_questions(gaps)
        elif 'contract' in area_lower or 'agreement' in area_lower:
            return self.generate_contract_questions(gaps)
        elif 'family' in area_lower or 'divorce' in area_lower or 'custody' in area_lower:
            return self.generate_family_law_questions(gaps)
        elif 'criminal' in area_lower or 'charge' in area_lower:
            return self.generate_criminal_questions(gaps)
        elif 'employment' in area_lower or 'workplace' in area_lower or 'fired' in area_lower:
            return self.generate_employment_questions(gaps)
        else:
            # Return general litigation questions as default
            return self.generate_litigation_questions(gaps)

# Global optimized AI service instance
dual_ai_service = DualAIProcessor()
optimized_ai_client = OptimizedAIClient()