"""
AI-powered analysis for identifying orders, stipulations, and key statements in court transcripts.
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import json
import asyncio
from datetime import datetime, timedelta

from ..shared.utils.ai_client import AIClient
from ..shared.database.models import User, Case, Document, TranscriptSegment
from ..shared.security.auth import get_current_user
from .transcript_processor import TranscriptProcessor


class StatementType(Enum):
    """Types of key statements that can be identified."""
    COURT_ORDER = "court_order"
    JUDICIAL_RULING = "judicial_ruling"
    STIPULATION = "stipulation"
    ADMISSION = "admission"
    SETTLEMENT_DISCUSSION = "settlement_discussion"
    JURY_INSTRUCTION = "jury_instruction"
    SCHEDULING_ORDER = "scheduling_order"
    DISCOVERY_ORDER = "discovery_order"
    SANCTIONS_ORDER = "sanctions_order"
    CONTEMPT_ORDER = "contempt_order"
    PROTECTIVE_ORDER = "protective_order"
    KEY_TESTIMONY = "key_testimony"
    EXPERT_OPINION = "expert_opinion"
    FACTUAL_FINDING = "factual_finding"
    LEGAL_CONCLUSION = "legal_conclusion"
    CASE_DISPOSITION = "case_disposition"


class OrderType(Enum):
    """Specific types of court orders."""
    PRELIMINARY_INJUNCTION = "preliminary_injunction"
    TEMPORARY_RESTRAINING_ORDER = "temporary_restraining_order"
    SUMMARY_JUDGMENT = "summary_judgment"
    MOTION_TO_DISMISS = "motion_to_dismiss"
    DISCOVERY_SANCTIONS = "discovery_sanctions"
    CONTEMPT_CITATION = "contempt_citation"
    SETTLEMENT_APPROVAL = "settlement_approval"
    CLASS_CERTIFICATION = "class_certification"
    VENUE_TRANSFER = "venue_transfer"
    CONSOLIDATION_ORDER = "consolidation_order"


class UrgencyLevel(Enum):
    """Urgency levels for identified statements."""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Action needed within 24 hours
    MEDIUM = "medium"  # Action needed within week
    LOW = "low"  # Informational only
    INFORMATIONAL = "informational"  # No action required


@dataclass
class IdentifiedStatement:
    """Represents an identified key statement."""
    statement_type: StatementType
    text: str
    speaker: str
    timestamp: float
    confidence: float
    urgency: UrgencyLevel
    context: str
    keywords: List[str]
    legal_implications: List[str]
    required_actions: List[str]
    deadlines: List[Dict[str, Any]]
    related_parties: List[str]
    case_impact: str
    order_type: Optional[OrderType] = None
    enforcement_mechanism: Optional[str] = None


@dataclass
class StipulationAnalysis:
    """Detailed analysis of a stipulation."""
    parties_involved: List[str]
    agreed_facts: List[str]
    disputed_issues: List[str]
    conditions: List[str]
    effective_date: Optional[datetime]
    expiration_date: Optional[datetime]
    modification_terms: List[str]
    enforceability_score: float


class StatementAnalyzer:
    """AI-powered analyzer for identifying orders, stipulations, and key statements."""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.transcript_processor = TranscriptProcessor()
        
        # Legal statement patterns
        self.order_patterns = [
            r"(?i)\b(?:the court|i|this court)\s+(?:order|orders|rule|rules|direct|directs|grant|grants|deny|denies)\b",
            r"(?i)\b(?:it is|it's)\s+(?:so\s+)?(?:ordered|ruled|decreed|adjudged)\b",
            r"(?i)\bmake\s+(?:this|the following)\s+(?:order|ruling|finding)\b",
            r"(?i)\b(?:upon|after)\s+(?:consideration|hearing|argument).*(?:ordered|ruled|decreed)\b",
            r"(?i)\b(?:preliminary|temporary|permanent)\s+(?:injunction|restraining order)\b"
        ]
        
        self.stipulation_patterns = [
            r"(?i)\b(?:we|the parties|counsel)\s+(?:stipulate|agree|acknowledge)\b",
            r"(?i)\b(?:stipulation|agreement|accord)\s+(?:that|to|between)\b",
            r"(?i)\b(?:for purposes of|without prejudice|subject to)\b.*\bstipulate\b",
            r"(?i)\b(?:jointly|mutually)\s+(?:agree|stipulate|acknowledge)\b",
            r"(?i)\b(?:it is|we are)\s+(?:agreed|stipulated|acknowledged)\b"
        ]
        
        self.key_statement_patterns = [
            r"(?i)\b(?:i|we)\s+(?:find|conclude|determine|hold)\s+(?:that|as follows)\b",
            r"(?i)\b(?:the evidence|testimony|record)\s+(?:shows|demonstrates|establishes)\b",
            r"(?i)\b(?:based on|in light of|given)\s+(?:the evidence|testimony|record)\b",
            r"(?i)\b(?:my|our|the court's)\s+(?:finding|conclusion|determination|ruling)\b",
            r"(?i)\b(?:expert|witness|testimony)\s+(?:opinion|finding|conclusion)\b"
        ]

    async def analyze_transcript_segment(
        self, 
        segment: TranscriptSegment,
        case_context: Optional[Case] = None
    ) -> List[IdentifiedStatement]:
        """Analyze a transcript segment for orders, stipulations, and key statements."""
        try:
            statements = []
            text = segment.text
            speaker = segment.speaker
            timestamp = segment.timestamp
            
            # Initial pattern-based detection
            potential_orders = self._detect_orders(text, speaker, timestamp)
            potential_stipulations = self._detect_stipulations(text, speaker, timestamp)
            potential_key_statements = self._detect_key_statements(text, speaker, timestamp)
            
            # AI-enhanced analysis
            ai_analysis = await self._ai_statement_analysis(text, speaker, case_context)
            
            # Combine and refine results
            all_candidates = potential_orders + potential_stipulations + potential_key_statements
            refined_statements = await self._refine_with_ai(all_candidates, ai_analysis, case_context)
            
            statements.extend(refined_statements)
            
            return statements
            
        except Exception as e:
            print(f"Error analyzing transcript segment: {e}")
            return []

    def _detect_orders(self, text: str, speaker: str, timestamp: float) -> List[IdentifiedStatement]:
        """Detect court orders using pattern matching."""
        orders = []
        
        for pattern in self.order_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end]
                
                order_type = self._classify_order_type(context)
                urgency = self._assess_order_urgency(context, order_type)
                
                order = IdentifiedStatement(
                    statement_type=StatementType.COURT_ORDER,
                    text=match.group(),
                    speaker=speaker,
                    timestamp=timestamp,
                    confidence=0.7,  # Will be refined by AI
                    urgency=urgency,
                    context=context,
                    keywords=self._extract_order_keywords(context),
                    legal_implications=[],  # Will be populated by AI
                    required_actions=[],  # Will be populated by AI
                    deadlines=[],  # Will be populated by AI
                    related_parties=[],  # Will be populated by AI
                    case_impact="",  # Will be populated by AI
                    order_type=order_type
                )
                orders.append(order)
        
        return orders

    def _detect_stipulations(self, text: str, speaker: str, timestamp: float) -> List[IdentifiedStatement]:
        """Detect stipulations using pattern matching."""
        stipulations = []
        
        for pattern in self.stipulation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                context_start = max(0, match.start() - 150)
                context_end = min(len(text), match.end() + 150)
                context = text[context_start:context_end]
                
                stipulation = IdentifiedStatement(
                    statement_type=StatementType.STIPULATION,
                    text=match.group(),
                    speaker=speaker,
                    timestamp=timestamp,
                    confidence=0.6,  # Will be refined by AI
                    urgency=UrgencyLevel.MEDIUM,
                    context=context,
                    keywords=self._extract_stipulation_keywords(context),
                    legal_implications=[],
                    required_actions=[],
                    deadlines=[],
                    related_parties=[],
                    case_impact=""
                )
                stipulations.append(stipulation)
        
        return stipulations

    def _detect_key_statements(self, text: str, speaker: str, timestamp: float) -> List[IdentifiedStatement]:
        """Detect key legal statements using pattern matching."""
        statements = []
        
        for pattern in self.key_statement_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                context_start = max(0, match.start() - 120)
                context_end = min(len(text), match.end() + 120)
                context = text[context_start:context_end]
                
                statement_type = self._classify_statement_type(context, speaker)
                
                statement = IdentifiedStatement(
                    statement_type=statement_type,
                    text=match.group(),
                    speaker=speaker,
                    timestamp=timestamp,
                    confidence=0.5,  # Will be refined by AI
                    urgency=UrgencyLevel.MEDIUM,
                    context=context,
                    keywords=self._extract_statement_keywords(context),
                    legal_implications=[],
                    required_actions=[],
                    deadlines=[],
                    related_parties=[],
                    case_impact=""
                )
                statements.append(statement)
        
        return statements

    async def _ai_statement_analysis(
        self, 
        text: str, 
        speaker: str, 
        case_context: Optional[Case]
    ) -> Dict[str, Any]:
        """Use AI to analyze text for orders, stipulations, and key statements."""
        try:
            context_info = ""
            if case_context:
                context_info = f"""
                Case Context:
                - Case Title: {case_context.title}
                - Case Type: {case_context.case_type}
                - Status: {case_context.status}
                - Key Issues: {', '.join(case_context.key_issues or [])}
                """
            
            prompt = f"""
            Analyze the following court transcript text for orders, stipulations, and key legal statements.
            
            Speaker: {speaker}
            Text: {text}
            {context_info}
            
            Identify and classify any:
            1. Court orders (including type and urgency)
            2. Stipulations between parties
            3. Key legal statements (findings, conclusions, admissions)
            4. Settlement discussions
            5. Jury instructions
            6. Expert opinions
            
            For each identified statement, provide:
            - Statement type and confidence (0-1)
            - Legal implications
            - Required actions
            - Deadlines mentioned
            - Parties involved
            - Case impact assessment
            - Urgency level (critical/high/medium/low/informational)
            
            Return as JSON with the following structure:
            {{
                "statements": [
                    {{
                        "type": "court_order|stipulation|key_testimony|etc",
                        "text": "exact text",
                        "confidence": 0.85,
                        "urgency": "high",
                        "legal_implications": ["implication1", "implication2"],
                        "required_actions": ["action1", "action2"],
                        "deadlines": [{{"deadline": "2024-01-15", "description": "file motion"}}],
                        "related_parties": ["plaintiff", "defendant"],
                        "case_impact": "description of impact",
                        "order_type": "summary_judgment" // if applicable
                    }}
                ]
            }}
            """
            
            response = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.1,
                max_tokens=2000
            )
            
            return json.loads(response)
            
        except Exception as e:
            print(f"Error in AI statement analysis: {e}")
            return {"statements": []}

    async def _refine_with_ai(
        self, 
        candidates: List[IdentifiedStatement], 
        ai_analysis: Dict[str, Any],
        case_context: Optional[Case]
    ) -> List[IdentifiedStatement]:
        """Refine candidate statements with AI analysis."""
        refined_statements = []
        
        # Merge pattern-based candidates with AI analysis
        ai_statements = ai_analysis.get("statements", [])
        
        for ai_stmt in ai_statements:
            try:
                statement_type = StatementType(ai_stmt.get("type", "key_testimony"))
                urgency = UrgencyLevel(ai_stmt.get("urgency", "medium"))
                order_type = None
                if ai_stmt.get("order_type"):
                    order_type = OrderType(ai_stmt["order_type"])
                
                refined_statement = IdentifiedStatement(
                    statement_type=statement_type,
                    text=ai_stmt.get("text", ""),
                    speaker=ai_stmt.get("speaker", ""),
                    timestamp=ai_stmt.get("timestamp", 0.0),
                    confidence=ai_stmt.get("confidence", 0.5),
                    urgency=urgency,
                    context=ai_stmt.get("context", ""),
                    keywords=ai_stmt.get("keywords", []),
                    legal_implications=ai_stmt.get("legal_implications", []),
                    required_actions=ai_stmt.get("required_actions", []),
                    deadlines=ai_stmt.get("deadlines", []),
                    related_parties=ai_stmt.get("related_parties", []),
                    case_impact=ai_stmt.get("case_impact", ""),
                    order_type=order_type
                )
                refined_statements.append(refined_statement)
                
            except (ValueError, KeyError) as e:
                print(f"Error processing AI statement: {e}")
                continue
        
        return refined_statements

    def _classify_order_type(self, context: str) -> Optional[OrderType]:
        """Classify the type of court order based on context."""
        context_lower = context.lower()
        
        order_keywords = {
            OrderType.PRELIMINARY_INJUNCTION: ["preliminary injunction", "prelim inj"],
            OrderType.TEMPORARY_RESTRAINING_ORDER: ["temporary restraining", "tro", "temp restraining"],
            OrderType.SUMMARY_JUDGMENT: ["summary judgment", "summary judgement"],
            OrderType.MOTION_TO_DISMISS: ["motion to dismiss", "dismiss", "12(b)(6)"],
            OrderType.DISCOVERY_SANCTIONS: ["discovery sanction", "sanction", "discovery violation"],
            OrderType.CONTEMPT_CITATION: ["contempt", "contempt of court"],
            OrderType.SETTLEMENT_APPROVAL: ["settlement approval", "approve settlement"],
            OrderType.CLASS_CERTIFICATION: ["class certification", "certify class"],
            OrderType.VENUE_TRANSFER: ["transfer venue", "venue transfer"],
            OrderType.CONSOLIDATION_ORDER: ["consolidate", "consolidation"]
        }
        
        for order_type, keywords in order_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                return order_type
        
        return None

    def _assess_order_urgency(self, context: str, order_type: Optional[OrderType]) -> UrgencyLevel:
        """Assess the urgency level of a court order."""
        context_lower = context.lower()
        
        # Critical urgency indicators
        critical_indicators = [
            "immediate", "forthwith", "emergency", "ex parte", "temporary restraining",
            "tro", "preliminary injunction", "contempt", "arrest", "seizure"
        ]
        
        if any(indicator in context_lower for indicator in critical_indicators):
            return UrgencyLevel.CRITICAL
        
        # High urgency indicators
        high_indicators = [
            "within 24 hours", "by tomorrow", "expedited", "sanctions",
            "discovery deadline", "motion practice"
        ]
        
        if any(indicator in context_lower for indicator in high_indicators):
            return UrgencyLevel.HIGH
        
        # Order type specific urgency
        if order_type in [OrderType.TEMPORARY_RESTRAINING_ORDER, OrderType.CONTEMPT_CITATION]:
            return UrgencyLevel.CRITICAL
        elif order_type in [OrderType.PRELIMINARY_INJUNCTION, OrderType.DISCOVERY_SANCTIONS]:
            return UrgencyLevel.HIGH
        
        return UrgencyLevel.MEDIUM

    def _classify_statement_type(self, context: str, speaker: str) -> StatementType:
        """Classify the type of key statement based on context and speaker."""
        context_lower = context.lower()
        speaker_lower = speaker.lower()
        
        # Judge/Court statements
        if any(judge_indicator in speaker_lower for judge_indicator in ["judge", "court", "magistrate"]):
            if any(ruling_word in context_lower for ruling_word in ["find", "conclude", "rule", "hold"]):
                return StatementType.JUDICIAL_RULING
            elif any(order_word in context_lower for order_word in ["order", "direct", "instruct"]):
                return StatementType.COURT_ORDER
            elif "jury" in context_lower and "instruct" in context_lower:
                return StatementType.JURY_INSTRUCTION
        
        # Expert testimony
        if "expert" in speaker_lower or "doctor" in speaker_lower or "professor" in speaker_lower:
            return StatementType.EXPERT_OPINION
        
        # Settlement discussions
        if any(settlement_word in context_lower for settlement_word in ["settle", "settlement", "resolve"]):
            return StatementType.SETTLEMENT_DISCUSSION
        
        # Admissions
        if any(admission_word in context_lower for admission_word in ["admit", "acknowledge", "concede"]):
            return StatementType.ADMISSION
        
        return StatementType.KEY_TESTIMONY

    def _extract_order_keywords(self, context: str) -> List[str]:
        """Extract relevant keywords from order context."""
        legal_terms = [
            "granted", "denied", "sustained", "overruled", "preliminary", "temporary",
            "permanent", "injunction", "restraining", "sanctions", "contempt", "dismiss",
            "summary", "judgment", "motion", "discovery", "deadline", "compliance"
        ]
        
        found_keywords = []
        context_lower = context.lower()
        
        for term in legal_terms:
            if term in context_lower:
                found_keywords.append(term)
        
        return found_keywords

    def _extract_stipulation_keywords(self, context: str) -> List[str]:
        """Extract relevant keywords from stipulation context."""
        stipulation_terms = [
            "stipulate", "agree", "acknowledge", "concede", "admit", "joint",
            "mutual", "parties", "counsel", "without prejudice", "subject to",
            "conditions", "terms", "effective", "binding"
        ]
        
        found_keywords = []
        context_lower = context.lower()
        
        for term in stipulation_terms:
            if term in context_lower:
                found_keywords.append(term)
        
        return found_keywords

    def _extract_statement_keywords(self, context: str) -> List[str]:
        """Extract relevant keywords from key statement context."""
        statement_terms = [
            "find", "conclude", "determine", "hold", "rule", "opinion", "testimony",
            "evidence", "witness", "expert", "fact", "law", "precedent", "standard"
        ]
        
        found_keywords = []
        context_lower = context.lower()
        
        for term in statement_terms:
            if term in context_lower:
                found_keywords.append(term)
        
        return found_keywords

    async def analyze_stipulation_details(
        self, 
        statement: IdentifiedStatement,
        case_context: Optional[Case] = None
    ) -> StipulationAnalysis:
        """Perform detailed analysis of a stipulation."""
        try:
            context_info = ""
            if case_context:
                context_info = f"Case: {case_context.title} ({case_context.case_type})"
            
            prompt = f"""
            Analyze this stipulation in detail:
            
            Text: {statement.text}
            Context: {statement.context}
            {context_info}
            
            Extract:
            1. Parties involved in the stipulation
            2. Agreed facts
            3. Remaining disputed issues
            4. Conditions or limitations
            5. Effective and expiration dates
            6. Terms for modification
            7. Enforceability assessment (0-1 score)
            
            Return as JSON:
            {{
                "parties_involved": ["party1", "party2"],
                "agreed_facts": ["fact1", "fact2"],
                "disputed_issues": ["issue1", "issue2"],
                "conditions": ["condition1", "condition2"],
                "effective_date": "2024-01-15" // or null,
                "expiration_date": "2024-06-15" // or null,
                "modification_terms": ["term1", "term2"],
                "enforceability_score": 0.85
            }}
            """
            
            response = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.1,
                max_tokens=1500
            )
            
            analysis_data = json.loads(response)
            
            # Parse dates
            effective_date = None
            if analysis_data.get("effective_date"):
                effective_date = datetime.fromisoformat(analysis_data["effective_date"])
            
            expiration_date = None
            if analysis_data.get("expiration_date"):
                expiration_date = datetime.fromisoformat(analysis_data["expiration_date"])
            
            return StipulationAnalysis(
                parties_involved=analysis_data.get("parties_involved", []),
                agreed_facts=analysis_data.get("agreed_facts", []),
                disputed_issues=analysis_data.get("disputed_issues", []),
                conditions=analysis_data.get("conditions", []),
                effective_date=effective_date,
                expiration_date=expiration_date,
                modification_terms=analysis_data.get("modification_terms", []),
                enforceability_score=analysis_data.get("enforceability_score", 0.5)
            )
            
        except Exception as e:
            print(f"Error analyzing stipulation details: {e}")
            return StipulationAnalysis(
                parties_involved=[],
                agreed_facts=[],
                disputed_issues=[],
                conditions=[],
                effective_date=None,
                expiration_date=None,
                modification_terms=[],
                enforceability_score=0.5
            )

    async def generate_action_items(
        self, 
        statements: List[IdentifiedStatement],
        case_context: Optional[Case] = None
    ) -> List[Dict[str, Any]]:
        """Generate actionable items based on identified statements."""
        try:
            action_items = []
            
            for statement in statements:
                if statement.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
                    items = await self._generate_statement_actions(statement, case_context)
                    action_items.extend(items)
            
            return action_items
            
        except Exception as e:
            print(f"Error generating action items: {e}")
            return []

    async def _generate_statement_actions(
        self, 
        statement: IdentifiedStatement,
        case_context: Optional[Case]
    ) -> List[Dict[str, Any]]:
        """Generate specific actions for a statement."""
        actions = []
        
        # Add required actions from statement
        for action in statement.required_actions:
            actions.append({
                "action": action,
                "priority": statement.urgency.value,
                "deadline": None,  # Will be extracted from deadlines
                "statement_type": statement.statement_type.value,
                "case_id": case_context.id if case_context else None
            })
        
        # Add deadline-based actions
        for deadline_info in statement.deadlines:
            actions.append({
                "action": deadline_info.get("description", "Comply with deadline"),
                "priority": "high" if statement.urgency == UrgencyLevel.CRITICAL else statement.urgency.value,
                "deadline": deadline_info.get("deadline"),
                "statement_type": statement.statement_type.value,
                "case_id": case_context.id if case_context else None
            })
        
        return actions