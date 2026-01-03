"""
Unit Tests for Legal Citation Parser

Tests legal citation parsing, validation, and formatting including
case law, statutes, regulations, and international citations.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime


class TestCitationParser:
    """Test suite for legal citation parsing functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.sample_citations = {
            "case_law": [
                "Brown v. Board of Education, 347 U.S. 483 (1954)",
                "Miranda v. Arizona, 384 U.S. 436, 86 S.Ct. 1602 (1966)",
                "Roe v. Wade, 410 U.S. 113, 93 S.Ct. 705, 35 L.Ed.2d 147 (1973)",
                "Smith v. Jones, 123 F.3d 456 (9th Cir. 2023)",
                "Doe v. Corporation, 789 F.Supp.2d 123 (S.D.N.Y. 2022)"
            ],
            "statutes": [
                "42 U.S.C. § 1983",
                "15 U.S.C. §§ 78a-78qq",
                "Cal. Civ. Code § 1798.100",
                "N.Y. C.P.L.R. § 3212"
            ],
            "regulations": [
                "29 C.F.R. § 1630.2",
                "17 C.F.R. § 240.10b-5"
            ],
            "international": [
                "Treaty of Rome, Mar. 25, 1957, 298 U.N.T.S. 11",
                "Vienna Convention on the Law of Treaties, May 23, 1969, 1155 U.N.T.S. 331"
            ]
        }

    def test_case_citation_parsing_basic(self):
        """Test basic case citation parsing"""
        
        def parse_case_citation(citation: str) -> Dict[str, Any]:
            """Parse a basic case law citation"""
            # Pattern for case citations: Case Name, Volume Reporter Page (Court Year)
            pattern = r'^(.+?),\s*(\d+)\s+([A-Za-z0-9\.]+)\s+(\d+)(?:\s*,\s*.*?)?\s*\((.+?)\s+(\d{4})\)$'
            match = re.match(pattern, citation.strip())
            
            if not match:
                return {"valid": False, "error": "Invalid citation format"}
            
            case_name, volume, reporter, page, court, year = match.groups()
            
            return {
                "valid": True,
                "type": "case_law",
                "case_name": case_name.strip(),
                "volume": int(volume),
                "reporter": reporter.strip(),
                "page": int(page),
                "court": court.strip(),
                "year": int(year),
                "full_citation": citation
            }
        
        # Test valid case citation
        citation = "Brown v. Board of Education, 347 U.S. 483 (1954)"
        result = parse_case_citation(citation)
        
        assert result["valid"] is True
        assert result["case_name"] == "Brown v. Board of Education"
        assert result["volume"] == 347
        assert result["reporter"] == "U.S."
        assert result["page"] == 483
        assert result["year"] == 1954

    def test_case_citation_with_multiple_reporters(self):
        """Test parsing case citations with parallel citations"""
        
        def parse_parallel_citation(citation: str) -> Dict[str, Any]:
            """Parse citation with parallel reporters"""
            # Enhanced pattern for parallel citations
            pattern = r'^(.+?),\s*(\d+)\s+([A-Za-z0-9\.]+)\s+(\d+)(?:\s*,\s*(\d+)\s+([A-Za-z0-9\.]+)\s+(\d+))*.*?\s*\((.+?)\s+(\d{4})\)$'
            match = re.match(pattern, citation.strip())
            
            if not match:
                return {"valid": False, "error": "Invalid parallel citation format"}
            
            groups = match.groups()
            case_name = groups[0].strip()
            court_year = groups[-2:]
            
            # Extract all reporter citations
            reporters = []
            citation_parts = citation.split('(')[0].split(',')[1:]  # Everything after case name, before court
            
            for part in citation_parts:
                part = part.strip()
                reporter_match = re.match(r'(\d+)\s+([A-Za-z0-9\.]+)\s+(\d+)', part)
                if reporter_match:
                    vol, rep, page = reporter_match.groups()
                    reporters.append({
                        "volume": int(vol),
                        "reporter": rep,
                        "page": int(page)
                    })
            
            return {
                "valid": True,
                "type": "case_law_parallel",
                "case_name": case_name,
                "reporters": reporters,
                "court": court_year[0].strip(),
                "year": int(court_year[1]),
                "full_citation": citation
            }
        
        citation = "Miranda v. Arizona, 384 U.S. 436, 86 S.Ct. 1602 (1966)"
        result = parse_parallel_citation(citation)
        
        assert result["valid"] is True
        assert result["case_name"] == "Miranda v. Arizona"
        assert len(result["reporters"]) >= 2
        assert any(r["reporter"] == "U.S." for r in result["reporters"])
        assert any(r["reporter"] == "S.Ct." for r in result["reporters"])

    def test_statute_citation_parsing(self):
        """Test statutory citation parsing"""
        
        def parse_statute_citation(citation: str) -> Dict[str, Any]:
            """Parse statutory citations"""
            patterns = [
                # Federal: Title U.S.C. § Section
                r'^(\d+)\s+U\.S\.C\.\s+§\s*(\d+(?:\w+)?(?:\([^)]+\))?(?:-\d+(?:\w+)?)?(?:,\s*\d+(?:\w+)?)*?)$',
                # Federal range: Title U.S.C. §§ Section-Section  
                r'^(\d+)\s+U\.S\.C\.\s+§§\s*(\d+\w*(?:\([^)]+\))?)(?:-(\d+\w*(?:\([^)]+\))?))?$',
                # State: State Code § Section
                r'^([A-Za-z\.]+)\s+([A-Za-z\.]+)\s+Code\s+§\s*(\d+(?:\.\d+)*(?:\([^)]+\))?)$',
                # California style: Cal. Code § Section
                r'^(Cal\.)\s+([A-Za-z\.]+)\s+Code\s+§\s*(\d+(?:\.\d+)*(?:\([^)]+\))?)$'
            ]
            
            for pattern in patterns:
                match = re.match(pattern, citation.strip())
                if match:
                    groups = match.groups()
                    
                    if "U.S.C." in citation:
                        return {
                            "valid": True,
                            "type": "federal_statute",
                            "title": int(groups[0]),
                            "code": "U.S.C.",
                            "section": groups[1],
                            "jurisdiction": "federal",
                            "full_citation": citation
                        }
                    else:
                        return {
                            "valid": True,
                            "type": "state_statute",
                            "state": groups[0],
                            "code": groups[1] if len(groups) > 2 else "Code",
                            "section": groups[-1],
                            "jurisdiction": "state",
                            "full_citation": citation
                        }
            
            return {"valid": False, "error": "Invalid statute citation format"}
        
        # Test federal statute
        federal_citation = "42 U.S.C. § 1983"
        result = parse_statute_citation(federal_citation)
        
        assert result["valid"] is True
        assert result["type"] == "federal_statute"
        assert result["title"] == 42
        assert result["section"] == "1983"
        
        # Test state statute
        state_citation = "Cal. Civ. Code § 1798.100"
        result = parse_statute_citation(state_citation)
        
        assert result["valid"] is True
        assert result["type"] == "state_statute"
        assert result["state"] == "Cal."

    def test_regulation_citation_parsing(self):
        """Test regulation citation parsing"""
        
        def parse_regulation_citation(citation: str) -> Dict[str, Any]:
            """Parse regulation citations (C.F.R.)"""
            # Pattern for CFR: Title C.F.R. § Section
            pattern = r'^(\d+)\s+C\.F\.R\.\s+§\s*(\d+(?:\.\d+)*(?:\([^)]+\))?)$'
            match = re.match(pattern, citation.strip())
            
            if not match:
                return {"valid": False, "error": "Invalid regulation citation format"}
            
            title, section = match.groups()
            
            return {
                "valid": True,
                "type": "federal_regulation",
                "title": int(title),
                "code": "C.F.R.",
                "section": section,
                "jurisdiction": "federal",
                "full_citation": citation
            }
        
        citation = "29 C.F.R. § 1630.2"
        result = parse_regulation_citation(citation)
        
        assert result["valid"] is True
        assert result["type"] == "federal_regulation"
        assert result["title"] == 29
        assert result["section"] == "1630.2"

    def test_bluebook_citation_validation(self):
        """Test Bluebook citation format validation"""
        
        def validate_bluebook_format(citation: str, citation_type: str) -> Dict[str, Any]:
            """Validate citation against Bluebook format"""
            validation = {
                "valid": True,
                "format": "bluebook",
                "errors": [],
                "warnings": []
            }
            
            if citation_type == "case_law":
                # Check case name formatting
                if " v. " not in citation and " vs. " not in citation:
                    validation["errors"].append("Case name should use 'v.' not 'vs.'")
                    validation["valid"] = False
                
                # Check year format
                if not re.search(r'\(\d{4}\)$', citation):
                    validation["errors"].append("Year should be in parentheses at the end")
                    validation["valid"] = False
                
                # Check reporter abbreviation
                known_reporters = ["U.S.", "S.Ct.", "F.3d", "F.2d", "F.Supp.", "F.Supp.2d"]
                if not any(reporter in citation for reporter in known_reporters):
                    validation["warnings"].append("Unknown or non-standard reporter abbreviation")
            
            elif citation_type == "statute":
                # Check section symbol
                if "§" not in citation and "Section" not in citation:
                    validation["errors"].append("Should use § symbol or 'Section'")
                    validation["valid"] = False
            
            return validation
        
        # Test valid case citation
        valid_case = "Brown v. Board of Education, 347 U.S. 483 (1954)"
        result = validate_bluebook_format(valid_case, "case_law")
        assert result["valid"] is True
        
        # Test invalid case citation
        invalid_case = "Brown vs. Board of Education, 347 U.S. 483 1954"
        result = validate_bluebook_format(invalid_case, "case_law")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_citation_normalization(self):
        """Test citation normalization and standardization"""
        
        def normalize_citation(citation: str) -> str:
            """Normalize citation format"""
            normalized = citation
            
            # Standardize spacing
            normalized = re.sub(r'\s+', ' ', normalized.strip())
            
            # Fix common abbreviation issues
            normalized = normalized.replace(' vs. ', ' v. ')
            normalized = normalized.replace(' versus ', ' v. ')
            
            # Standardize section symbols
            normalized = normalized.replace('Section ', '§ ')
            normalized = normalized.replace('Sec. ', '§ ')
            
            # Fix reporter abbreviations
            reporter_fixes = {
                'US ': 'U.S. ',
                'SCt ': 'S.Ct. ',
                'F3d ': 'F.3d ',
                'F2d ': 'F.2d ',
                'FSupp ': 'F.Supp. ',
                'USC ': 'U.S.C. ',
                'CFR ': 'C.F.R. '
            }
            
            for incorrect, correct in reporter_fixes.items():
                normalized = normalized.replace(incorrect, correct)
            
            return normalized
        
        messy_citation = "Brown  vs.  Board of Education,  347 US 483 (1954)"
        normalized = normalize_citation(messy_citation)
        
        expected = "Brown v. Board of Education, 347 U.S. 483 (1954)"
        assert normalized == expected

    def test_citation_extraction_from_text(self):
        """Test extracting citations from legal text"""
        
        def extract_citations_from_text(text: str) -> List[Dict[str, Any]]:
            """Extract citations from a block of legal text"""
            citations = []
            
            # Pattern for case citations
            case_pattern = r'\b[A-Z][a-zA-Z\s&]+v\.\s+[A-Z][a-zA-Z\s&]+,\s+\d+\s+[A-Za-z0-9\.]+\s+\d+.*?\(\d{4}\)'
            case_matches = re.finditer(case_pattern, text)
            
            for match in case_matches:
                citations.append({
                    "type": "case_law",
                    "text": match.group().strip(),
                    "start": match.start(),
                    "end": match.end()
                })
            
            # Pattern for statute citations
            statute_pattern = r'\b\d+\s+U\.S\.C\.\s+§\s*\d+\w*(?:\([^)]+\))?'
            statute_matches = re.finditer(statute_pattern, text)
            
            for match in statute_matches:
                citations.append({
                    "type": "statute",
                    "text": match.group().strip(),
                    "start": match.start(),
                    "end": match.end()
                })
            
            return sorted(citations, key=lambda x: x["start"])
        
        legal_text = """
        In Brown v. Board of Education, 347 U.S. 483 (1954), the Court held that 
        separate educational facilities are inherently unequal. This decision was 
        based on the Equal Protection Clause found in 42 U.S.C. § 1983 and other 
        provisions. Later, in Miranda v. Arizona, 384 U.S. 436 (1966), the Court 
        established the requirement for warnings.
        """
        
        citations = extract_citations_from_text(legal_text)
        
        assert len(citations) >= 3  # At least 2 cases and 1 statute
        assert any(c["type"] == "case_law" and "Brown" in c["text"] for c in citations)
        assert any(c["type"] == "case_law" and "Miranda" in c["text"] for c in citations)
        assert any(c["type"] == "statute" and "42 U.S.C." in c["text"] for c in citations)

    def test_citation_context_analysis(self):
        """Test analysis of citation context and usage"""
        
        def analyze_citation_context(text: str, citation_start: int, citation_end: int) -> Dict[str, Any]:
            """Analyze the context around a citation"""
            context_window = 100  # Characters before and after
            
            start = max(0, citation_start - context_window)
            end = min(len(text), citation_end + context_window)
            
            before_text = text[start:citation_start].strip()
            after_text = text[citation_end:end].strip()
            
            # Analyze citation usage
            usage_indicators = {
                "holding": ["held", "holding", "ruled", "decided", "found"],
                "support": ["see", "citing", "accord", "see also"],
                "distinguish": ["distinguish", "but see", "contra", "compare"],
                "overrule": ["overruled", "overturned", "reversed"]
            }
            
            usage_type = "general"
            for usage, indicators in usage_indicators.items():
                if any(indicator in before_text.lower() for indicator in indicators):
                    usage_type = usage
                    break
            
            return {
                "before_context": before_text[-50:] if len(before_text) > 50 else before_text,
                "after_context": after_text[:50] if len(after_text) > 50 else after_text,
                "usage_type": usage_type,
                "signal_words": [word for indicators in usage_indicators.values() 
                               for word in indicators if word in before_text.lower()]
            }
        
        text_with_citation = "The Court held that separate is inherently unequal. Brown v. Board, 347 U.S. 483 (1954). This landmark decision changed education."
        citation_start = text_with_citation.find("Brown v. Board")
        citation_end = citation_start + len("Brown v. Board, 347 U.S. 483 (1954)")
        
        context = analyze_citation_context(text_with_citation, citation_start, citation_end)
        
        assert context["usage_type"] == "holding"
        assert "held" in context["signal_words"]

    def test_citation_verification(self):
        """Test citation accuracy verification"""
        
        def verify_citation_accuracy(citation: Dict[str, Any]) -> Dict[str, Any]:
            """Verify citation accuracy against known legal databases"""
            # Mock verification against legal database
            known_cases = {
                ("Brown v. Board of Education", 347, "U.S.", 483, 1954): {
                    "correct": True,
                    "full_name": "Brown v. Board of Education of Topeka",
                    "docket": "1, 2, 8, 101, 191",
                    "court": "Supreme Court of the United States"
                },
                ("Miranda v. Arizona", 384, "U.S.", 436, 1966): {
                    "correct": True,
                    "full_name": "Miranda v. Arizona",
                    "docket": "759",
                    "court": "Supreme Court of the United States"
                }
            }
            
            if citation["type"] == "case_law":
                key = (
                    citation.get("case_name"),
                    citation.get("volume"),
                    citation.get("reporter"),
                    citation.get("page"),
                    citation.get("year")
                )
                
                if key in known_cases:
                    return {
                        "verified": True,
                        "accurate": True,
                        "additional_info": known_cases[key]
                    }
                else:
                    return {
                        "verified": False,
                        "accurate": None,
                        "error": "Citation not found in database"
                    }
            
            return {"verified": False, "error": "Unsupported citation type"}
        
        # Test known citation
        citation = {
            "type": "case_law",
            "case_name": "Brown v. Board of Education",
            "volume": 347,
            "reporter": "U.S.",
            "page": 483,
            "year": 1954
        }
        
        verification = verify_citation_accuracy(citation)
        assert verification["verified"] is True
        assert verification["accurate"] is True

    def test_citation_currency_check(self):
        """Test checking citation currency and validity"""
        
        def check_citation_currency(citation: Dict[str, Any]) -> Dict[str, Any]:
            """Check if citation is still good law"""
            # Mock Shepardizing/KeyCiting functionality
            currency_data = {
                ("Brown v. Board of Education", 347, "U.S.", 483): {
                    "status": "good_law",
                    "treatment": "followed",
                    "subsequent_history": [],
                    "citing_decisions": 1247
                },
                ("Plessy v. Ferguson", 163, "U.S.", 537): {
                    "status": "overruled",
                    "treatment": "overruled by Brown v. Board",
                    "subsequent_history": ["overruled"],
                    "citing_decisions": 89
                }
            }
            
            if citation["type"] == "case_law":
                key = (
                    citation.get("case_name"),
                    citation.get("volume"),
                    citation.get("reporter"),
                    citation.get("page")
                )
                
                if key in currency_data:
                    data = currency_data[key]
                    return {
                        "current": data["status"] == "good_law",
                        "status": data["status"],
                        "treatment": data["treatment"],
                        "warning": data["status"] != "good_law",
                        "subsequent_history": data["subsequent_history"]
                    }
            
            return {
                "current": None,
                "status": "unknown",
                "warning": True,
                "error": "Cannot verify currency"
            }
        
        # Test good law
        good_citation = {
            "type": "case_law",
            "case_name": "Brown v. Board of Education",
            "volume": 347,
            "reporter": "U.S.",
            "page": 483
        }
        
        currency = check_citation_currency(good_citation)
        assert currency["current"] is True
        assert currency["status"] == "good_law"

    def test_international_citation_parsing(self):
        """Test parsing international legal citations"""
        
        def parse_international_citation(citation: str) -> Dict[str, Any]:
            """Parse international legal citations"""
            patterns = {
                "treaty": r'^(.+?),\s+([A-Za-z]+\.?\s+\d+,\s+\d{4}),\s+(\d+)\s+U\.N\.T\.S\.\s+(\d+)$',
                "icj": r'^(.+?),\s+(\d{4})\s+I\.C\.J\.\s+(\d+)(?:\s+\(([^)]+)\))?$',
                "ecthr": r'^(.+?),\s+App\.\s+No\.\s+(\d+/\d+),\s+(\d+)\s+Eur\.\s+Ct\.\s+H\.R\.\s+(\d+)$'
            }
            
            for citation_type, pattern in patterns.items():
                match = re.match(pattern, citation.strip())
                if match:
                    if citation_type == "treaty":
                        name, date, unts_vol, unts_page = match.groups()
                        return {
                            "valid": True,
                            "type": "treaty",
                            "name": name.strip(),
                            "date": date.strip(),
                            "unts_volume": int(unts_vol),
                            "unts_page": int(unts_page),
                            "full_citation": citation
                        }
                    elif citation_type == "icj":
                        name, year, page, phase = match.groups()
                        return {
                            "valid": True,
                            "type": "icj_case",
                            "case_name": name.strip(),
                            "year": int(year),
                            "page": int(page),
                            "phase": phase,
                            "full_citation": citation
                        }
            
            return {"valid": False, "error": "Unknown international citation format"}
        
        treaty_citation = "Treaty of Rome, Mar. 25, 1957, 298 U.N.T.S. 11"
        result = parse_international_citation(treaty_citation)
        
        assert result["valid"] is True
        assert result["type"] == "treaty"
        assert result["name"] == "Treaty of Rome"
        assert result["unts_volume"] == 298

    def test_citation_comparison(self):
        """Test comparison and matching of citations"""
        
        def citations_match(cite1: str, cite2: str) -> Dict[str, Any]:
            """Determine if two citations refer to the same source"""
            from difflib import SequenceMatcher
            
            # Normalize both citations
            def normalize(citation):
                return re.sub(r'\s+', ' ', citation.lower().strip())
            
            norm1 = normalize(cite1)
            norm2 = normalize(cite2)
            
            # Exact match
            if norm1 == norm2:
                return {"match": True, "confidence": 1.0, "type": "exact"}
            
            # Similar match using sequence matching
            similarity = SequenceMatcher(None, norm1, norm2).ratio()
            
            if similarity > 0.9:
                return {"match": True, "confidence": similarity, "type": "high_similarity"}
            elif similarity > 0.7:
                return {"match": True, "confidence": similarity, "type": "likely_match"}
            else:
                return {"match": False, "confidence": similarity, "type": "different"}
        
        # Test similar citations
        cite1 = "Brown v. Board of Education, 347 U.S. 483 (1954)"
        cite2 = "Brown v. Bd. of Ed., 347 U.S. 483 (1954)"
        
        result = citations_match(cite1, cite2)
        assert result["match"] is True
        assert result["confidence"] > 0.8