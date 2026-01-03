"""
Robust Extraction Pipeline - Multi-level data extraction with confidence scores
Supports progressive enhancement and works with or without AI
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExtractionMethod(Enum):
    """Track which method was used for extraction"""
    AI_ANALYSIS = "ai_analysis"
    REGEX_PATTERN = "regex_pattern"
    MANUAL_ENTRY = "manual_entry"
    DEFAULT_VALUE = "default_value"
    NOT_FOUND = "not_found"


class ConfidenceLevel(Enum):
    """Confidence level for extracted data"""
    HIGH = "high"       # 80-100% - AI confirmed or exact match
    MEDIUM = "medium"   # 50-79% - Regex pattern or partial match
    LOW = "low"         # 20-49% - Inferred or guessed
    NONE = "none"       # 0-19% - Default fallback


@dataclass
class ExtractedField:
    """Represents a single extracted field with metadata"""
    value: Any
    confidence: ConfidenceLevel
    method: ExtractionMethod
    source: str  # Where it came from (AI, text line 45, user input, etc.)
    needs_verification: bool = False


@dataclass
class ExtractedDeadline:
    """Deadline with extraction metadata"""
    description: str
    date: str  # ISO format or 'TBD'
    days_from_now: Optional[int]
    priority: str
    confidence: ConfidenceLevel
    method: ExtractionMethod
    source_text: str


@dataclass
class ExtractionResult:
    """Complete extraction result with all metadata"""
    document_type: ExtractedField
    deadlines: List[ExtractedDeadline]
    key_dates: List[ExtractedDeadline]
    parties: ExtractedField
    case_number: ExtractedField
    court: ExtractedField
    amount_claimed: ExtractedField
    overall_confidence: float  # 0.0 to 1.0
    extraction_summary: Dict[str, Any]


class ExtractionPipeline:
    """Multi-level extraction pipeline with fallbacks"""

    def __init__(self):
        self.deadline_patterns = [
            (r'within (\d+) (?:calendar )?days?', 'relative_days'),
            (r'(\d+) days? (?:from|after|of) (?:service|receipt|filing)', 'relative_days'),
            (r'(?:respond|file|answer) (?:by|on|before) ([A-Z][a-z]+ \d{1,2},? \d{4})', 'absolute_date'),
            (r'(?:deadline|due date):?\s*([A-Z][a-z]+ \d{1,2},? \d{4})', 'absolute_date'),
            (r'no later than ([A-Z][a-z]+ \d{1,2},? \d{4})', 'absolute_date'),
            (r'hearing (?:on|scheduled for) ([A-Z][a-z]+ \d{1,2},? \d{4})', 'absolute_date'),
        ]

        self.doc_type_keywords = {
            'complaint': ['complaint', 'petition', 'summons'],
            'motion': ['motion to', 'notice of motion'],
            'answer': ['answer', 'response', 'reply'],
            'discovery': ['interrogator', 'request for production', 'subpoena'],
            'notice': ['notice of', 'notification'],
            'order': ['court order', 'judgment', 'decree'],
        }

    def extract(self,
                document_text: str,
                ai_analysis: Optional[Dict[str, Any]] = None) -> ExtractionResult:
        """
        Extract data using multi-level pipeline

        Priority:
        1. AI analysis (highest confidence)
        2. Regex extraction (medium confidence)
        3. Defaults (low confidence, needs verification)
        """

        # Extract document type
        doc_type = self._extract_document_type(document_text, ai_analysis)

        # Extract deadlines
        deadlines = self._extract_deadlines(document_text, ai_analysis)

        # Extract key dates (hearings, trials, etc.)
        key_dates = self._extract_key_dates(document_text, ai_analysis)

        # Extract parties
        parties = self._extract_parties(document_text, ai_analysis)

        # Extract case number
        case_number = self._extract_case_number(document_text, ai_analysis)

        # Extract court
        court = self._extract_court(document_text, ai_analysis)

        # Extract amount claimed
        amount_claimed = self._extract_amount(document_text, ai_analysis)

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence([
            doc_type, parties, case_number, court, amount_claimed
        ], deadlines + key_dates)

        # Create extraction summary
        summary = {
            'total_fields': 7,
            'high_confidence_fields': sum(1 for f in [doc_type, parties, case_number, court, amount_claimed]
                                         if f.confidence == ConfidenceLevel.HIGH),
            'needs_verification_count': sum(1 for f in [doc_type, parties, case_number, court, amount_claimed]
                                           if f.needs_verification),
            'deadlines_found': len(deadlines),
            'key_dates_found': len(key_dates),
            'extraction_methods_used': list(set(
                f.method.value for f in [doc_type, parties, case_number, court, amount_claimed]
            ))
        }

        return ExtractionResult(
            document_type=doc_type,
            deadlines=deadlines,
            key_dates=key_dates,
            parties=parties,
            case_number=case_number,
            court=court,
            amount_claimed=amount_claimed,
            overall_confidence=overall_confidence,
            extraction_summary=summary
        )

    def _extract_document_type(self, text: str, ai: Optional[Dict]) -> ExtractedField:
        """Extract document type with fallback"""

        # Level 1: AI analysis
        if ai and ai.get('document_type'):
            return ExtractedField(
                value=ai['document_type'],
                confidence=ConfidenceLevel.HIGH,
                method=ExtractionMethod.AI_ANALYSIS,
                source="AI analysis",
                needs_verification=False
            )

        # Level 2: Keyword matching
        text_lower = text.lower()
        for doc_type, keywords in self.doc_type_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return ExtractedField(
                    value=doc_type.title(),
                    confidence=ConfidenceLevel.MEDIUM,
                    method=ExtractionMethod.REGEX_PATTERN,
                    source=f"Keyword match: {doc_type}",
                    needs_verification=True
                )

        # Level 3: Default
        return ExtractedField(
            value="Legal Document",
            confidence=ConfidenceLevel.LOW,
            method=ExtractionMethod.DEFAULT_VALUE,
            source="Default fallback",
            needs_verification=True
        )

    def _extract_deadlines(self, text: str, ai: Optional[Dict]) -> List[ExtractedDeadline]:
        """Extract deadlines from all sources"""
        deadlines = []

        # Level 1: AI-extracted deadlines
        if ai and ai.get('deadlines'):
            for dl in ai['deadlines']:
                deadlines.append(ExtractedDeadline(
                    description=dl.get('description', 'Deadline'),
                    date=dl.get('date', 'TBD'),
                    days_from_now=self._calculate_days_until(dl.get('date')),
                    priority=self._determine_priority(dl.get('date')),
                    confidence=ConfidenceLevel.HIGH,
                    method=ExtractionMethod.AI_ANALYSIS,
                    source_text=dl.get('description', '')[:100]
                ))

        # Level 2: Regex extraction
        for pattern, pattern_type in self.deadline_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if pattern_type == 'relative_days':
                    days = int(match.group(1))
                    deadline_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
                    desc = f"Deadline: {days} days from service"
                elif pattern_type == 'absolute_date':
                    deadline_date = match.group(1)
                    desc = f"Deadline: {deadline_date}"

                # Avoid duplicates
                if not any(d.date == deadline_date for d in deadlines):
                    deadlines.append(ExtractedDeadline(
                        description=desc,
                        date=deadline_date,
                        days_from_now=days if pattern_type == 'relative_days' else None,
                        priority=self._determine_priority(deadline_date),
                        confidence=ConfidenceLevel.MEDIUM,
                        method=ExtractionMethod.REGEX_PATTERN,
                        source_text=match.group(0)
                    ))

        return deadlines

    def _extract_key_dates(self, text: str, ai: Optional[Dict]) -> List[ExtractedDeadline]:
        """Extract key dates (hearings, trials)"""
        key_dates = []

        # Level 1: AI extraction
        if ai and ai.get('key_dates'):
            for kd in ai['key_dates']:
                key_dates.append(ExtractedDeadline(
                    description=kd.get('description', 'Important Date'),
                    date=kd.get('date', 'TBD'),
                    days_from_now=self._calculate_days_until(kd.get('date')),
                    priority=self._determine_priority(kd.get('date')),
                    confidence=ConfidenceLevel.HIGH,
                    method=ExtractionMethod.AI_ANALYSIS,
                    source_text=kd.get('description', '')[:100]
                ))

        # Level 2: Pattern matching for hearings/trials
        hearing_pattern = r'(hearing|trial|conference).*?(?:on|scheduled for)\s*([A-Z][a-z]+ \d{1,2},? \d{4})'
        matches = re.finditer(hearing_pattern, text, re.IGNORECASE)

        for match in matches:
            event_type = match.group(1)
            date_str = match.group(2)

            if not any(d.date == date_str for d in key_dates):
                key_dates.append(ExtractedDeadline(
                    description=f"{event_type.title()} scheduled",
                    date=date_str,
                    days_from_now=None,
                    priority="HIGH",
                    confidence=ConfidenceLevel.MEDIUM,
                    method=ExtractionMethod.REGEX_PATTERN,
                    source_text=match.group(0)
                ))

        return key_dates

    def _extract_parties(self, text: str, ai: Optional[Dict]) -> ExtractedField:
        """Extract parties"""

        if ai and ai.get('parties'):
            return ExtractedField(
                value=ai['parties'],
                confidence=ConfidenceLevel.HIGH,
                method=ExtractionMethod.AI_ANALYSIS,
                source="AI analysis"
            )

        # Basic extraction: look for plaintiff/defendant
        parties = []
        party_pattern = r'(Plaintiff|Defendant|Petitioner|Respondent):\s*([A-Z][a-z]+(?: [A-Z][a-z]+)*)'
        matches = re.findall(party_pattern, text)

        if matches:
            parties = [f"{role}: {name}" for role, name in matches]
            return ExtractedField(
                value=parties,
                confidence=ConfidenceLevel.MEDIUM,
                method=ExtractionMethod.REGEX_PATTERN,
                source="Pattern matching",
                needs_verification=True
            )

        return ExtractedField(
            value=["Unknown"],
            confidence=ConfidenceLevel.NONE,
            method=ExtractionMethod.DEFAULT_VALUE,
            source="Default",
            needs_verification=True
        )

    def _extract_case_number(self, text: str, ai: Optional[Dict]) -> ExtractedField:
        """Extract case number"""

        if ai and ai.get('case_number'):
            return ExtractedField(
                value=ai['case_number'],
                confidence=ConfidenceLevel.HIGH,
                method=ExtractionMethod.AI_ANALYSIS,
                source="AI analysis"
            )

        # Pattern: Case No: 2024-CV-12345
        case_pattern = r'[Cc]ase [Nn]o\.?:?\s*(\d{4}-[A-Z]+-\d+|\d+-\d+)'
        match = re.search(case_pattern, text)

        if match:
            return ExtractedField(
                value=match.group(1),
                confidence=ConfidenceLevel.MEDIUM,
                method=ExtractionMethod.REGEX_PATTERN,
                source=f"Found: {match.group(0)}",
                needs_verification=True
            )

        return ExtractedField(
            value="TBD",
            confidence=ConfidenceLevel.NONE,
            method=ExtractionMethod.DEFAULT_VALUE,
            source="Not found",
            needs_verification=True
        )

    def _extract_court(self, text: str, ai: Optional[Dict]) -> ExtractedField:
        """Extract court name"""

        if ai and ai.get('court'):
            return ExtractedField(
                value=ai['court'],
                confidence=ConfidenceLevel.HIGH,
                method=ExtractionMethod.AI_ANALYSIS,
                source="AI analysis"
            )

        # Look for court keywords
        court_pattern = r'((?:United States |U\.S\. )?(?:District |Superior |Circuit )?Court(?: of [A-Z][a-z]+)?)'
        match = re.search(court_pattern, text, re.IGNORECASE)

        if match:
            return ExtractedField(
                value=match.group(1),
                confidence=ConfidenceLevel.MEDIUM,
                method=ExtractionMethod.REGEX_PATTERN,
                source=f"Found: {match.group(0)}"
            )

        return ExtractedField(
            value="Unknown Court",
            confidence=ConfidenceLevel.NONE,
            method=ExtractionMethod.DEFAULT_VALUE,
            source="Not found",
            needs_verification=True
        )

    def _extract_amount(self, text: str, ai: Optional[Dict]) -> ExtractedField:
        """Extract claimed amount"""

        if ai and ai.get('amount_claimed'):
            return ExtractedField(
                value=ai['amount_claimed'],
                confidence=ConfidenceLevel.HIGH,
                method=ExtractionMethod.AI_ANALYSIS,
                source="AI analysis"
            )

        # Look for dollar amounts
        amount_pattern = r'\$[\d,]+(?:\.\d{2})?'
        matches = re.findall(amount_pattern, text)

        if matches:
            # Take the largest amount found
            amounts = [float(m.replace('$', '').replace(',', '')) for m in matches]
            max_amount = max(amounts)
            return ExtractedField(
                value=f"${max_amount:,.2f}",
                confidence=ConfidenceLevel.MEDIUM,
                method=ExtractionMethod.REGEX_PATTERN,
                source=f"Found {len(matches)} amounts, selected largest",
                needs_verification=True
            )

        return ExtractedField(
            value="Not specified",
            confidence=ConfidenceLevel.NONE,
            method=ExtractionMethod.DEFAULT_VALUE,
            source="Not found",
            needs_verification=True
        )

    def _calculate_days_until(self, date_str: Optional[str]) -> Optional[int]:
        """Calculate days until a date"""
        if not date_str or date_str == 'TBD':
            return None

        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            delta = target_date - datetime.now()
            return delta.days
        except:
            return None

    def _determine_priority(self, date_str: Optional[str]) -> str:
        """Determine priority based on deadline proximity"""
        days = self._calculate_days_until(date_str)

        if days is None:
            return "MEDIUM"
        elif days < 7:
            return "URGENT"
        elif days < 30:
            return "HIGH"
        else:
            return "MEDIUM"

    def _calculate_overall_confidence(self,
                                     fields: List[ExtractedField],
                                     dates: List[ExtractedDeadline]) -> float:
        """Calculate overall confidence score 0.0-1.0"""

        confidence_values = {
            ConfidenceLevel.HIGH: 1.0,
            ConfidenceLevel.MEDIUM: 0.65,
            ConfidenceLevel.LOW: 0.35,
            ConfidenceLevel.NONE: 0.0
        }

        scores = [confidence_values[f.confidence] for f in fields]
        scores.extend([confidence_values[d.confidence] for d in dates])

        if not scores:
            return 0.0

        return sum(scores) / len(scores)


# Global instance
extraction_pipeline = ExtractionPipeline()
