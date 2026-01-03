"""
Legal Analysis Module Tests
Comprehensive test suite for legal filing analysis system
"""

import pytest
from datetime import date, datetime, timedelta
import json

# Import modules to test
from app.src.services.legal_analysis import (
    # Filing Types
    get_filing_type,
    get_all_filing_types,
    get_filing_types_by_category,
    classify_filing_by_patterns,
    search_filing_types,
    FILING_CATEGORIES,

    # Extraction
    extract_case_number,
    extract_all_citations,
    extract_parties,
    extract_monetary_amounts,
    extract_dates,

    # Deadlines
    DeadlineCalculator,
    JurisdictionType,
    ServiceMethod,
    FederalHolidayCalendar,
    ResponseDeadlineCalculator,
    get_all_deadline_rules,
    get_deadline_rule,

    # Analyzer
    LegalFilingAnalyzer,
    create_analyzer,
    ConfidenceLevel,
    UrgencyLevel,

    # Templates
    OutputFormat,
    SummaryRenderer,
    TemplateContext,
)


# =============================================================================
# FILING TYPES TESTS
# =============================================================================

class TestFilingTypes:
    """Tests for filing type classification"""

    def test_get_filing_type(self):
        """Test retrieving filing type by code"""
        complaint = get_filing_type("A1")
        assert complaint is not None
        assert complaint.code == "A1"
        assert "complaint" in complaint.name.lower()

    def test_get_all_filing_types(self):
        """Test getting all filing types"""
        all_types = get_all_filing_types()
        assert len(all_types) >= 60  # We have 60+ filing types
        assert "A1" in all_types
        assert "E1" in all_types  # Summary Judgment

    def test_get_filing_types_by_category(self):
        """Test filtering by category"""
        complaints = get_filing_types_by_category("A")
        assert len(complaints) > 0
        assert all(ft.category == "A" for ft in complaints)

    def test_classify_filing_patterns(self):
        """Test pattern-based classification"""
        # Test complaint classification
        matches = classify_filing_by_patterns("PLAINTIFF'S COMPLAINT FOR DAMAGES")
        assert len(matches) > 0
        assert matches[0]['code'].startswith('A')

        # Test motion to dismiss
        matches = classify_filing_by_patterns("MOTION TO DISMISS PURSUANT TO RULE 12(b)(6)")
        assert len(matches) > 0
        assert matches[0]['code'].startswith('C')

        # Test summary judgment
        matches = classify_filing_by_patterns("MOTION FOR SUMMARY JUDGMENT")
        assert len(matches) > 0
        assert matches[0]['code'].startswith('E')

    def test_search_filing_types(self):
        """Test searching filing types"""
        results = search_filing_types("summary judgment")
        assert len(results) > 0
        assert any("summary" in ft.name.lower() for ft in results)

    def test_filing_categories(self):
        """Test filing categories exist"""
        assert "A" in FILING_CATEGORIES
        assert "Complaints" in FILING_CATEGORIES["A"]
        assert "E" in FILING_CATEGORIES
        assert "Dispositive" in FILING_CATEGORIES["E"]


# =============================================================================
# EXTRACTION TESTS
# =============================================================================

class TestExtraction:
    """Tests for data extraction patterns"""

    def test_extract_federal_case_number(self):
        """Test federal case number extraction"""
        text = "Case No. 2:23-cv-01234-ABC-XYZ"
        result = extract_case_number(text)
        assert result is not None
        assert result.full_number == "2:23-cv-01234-ABC-XYZ"
        assert result.court_type == "federal_district"
        assert result.year == 2023
        assert result.case_type == "cv"

    def test_extract_state_case_number(self):
        """Test state case number extraction"""
        text = "Case No. 23CV12345"
        result = extract_case_number(text)
        assert result is not None

    def test_extract_case_citations(self):
        """Test case law citation extraction"""
        text = """
        See Bell Atlantic Corp. v. Twombly, 550 U.S. 544 (2007);
        Ashcroft v. Iqbal, 556 U.S. 662, 678 (2009).
        """
        citations = extract_all_citations(text)
        case_citations = [c for c in citations if c.citation_type == 'case_law']
        assert len(case_citations) >= 2

    def test_extract_statute_citations(self):
        """Test statute citation extraction"""
        text = "Pursuant to 42 U.S.C. § 1983 and 28 U.S.C. § 1331"
        citations = extract_all_citations(text)
        statute_citations = [c for c in citations if c.citation_type == 'statute']
        assert len(statute_citations) >= 2

    def test_extract_parties(self):
        """Test party extraction"""
        text = """
        JOHN DOE, an individual, Plaintiff,
        v.
        ACME CORPORATION, a Delaware corporation, Defendant.
        """
        parties = extract_parties(text)
        assert len(parties) >= 2
        assert any("JOHN DOE" in p.name for p in parties)
        assert any("plaintiff" in p.role.lower() for p in parties)
        assert any("defendant" in p.role.lower() for p in parties)

    def test_extract_monetary_amounts(self):
        """Test monetary amount extraction"""
        text = """
        Plaintiff seeks compensatory damages in excess of $75,000
        and punitive damages of $1,000,000.
        """
        amounts = extract_monetary_amounts(text)
        assert len(amounts) >= 2
        assert any(a.value == 75000 for a in amounts)
        assert any(a.value == 1000000 for a in amounts)

    def test_extract_dates(self):
        """Test date extraction"""
        text = "Filed on January 15, 2024. Response due by February 5, 2024."
        dates = extract_dates(text)
        assert len(dates) >= 2


# =============================================================================
# DEADLINE CALCULATION TESTS
# =============================================================================

class TestDeadlineCalculation:
    """Tests for deadline calculation"""

    def test_federal_holiday_calendar(self):
        """Test federal holiday calculation"""
        holidays = FederalHolidayCalendar.get_federal_holidays(2024)
        assert len(holidays) >= 10  # At least 10 federal holidays

        # Check specific holidays
        holiday_names = [h.name for h in holidays]
        assert "New Year's Day" in holiday_names
        assert "Independence Day" in holiday_names
        assert "Thanksgiving Day" in holiday_names

    def test_is_business_day(self):
        """Test business day checking"""
        calc = DeadlineCalculator(JurisdictionType.FEDERAL)

        # Weekday should be business day (if not holiday)
        # Monday January 8, 2024 is not a holiday
        assert calc.is_business_day(date(2024, 1, 8)) == True

        # Saturday should not be business day
        assert calc.is_business_day(date(2024, 1, 6)) == False

        # Sunday should not be business day
        assert calc.is_business_day(date(2024, 1, 7)) == False

    def test_next_business_day(self):
        """Test next business day calculation"""
        calc = DeadlineCalculator(JurisdictionType.FEDERAL)

        # Friday should go to Monday
        friday = date(2024, 1, 5)
        next_day = calc.next_business_day(friday)
        assert next_day == date(2024, 1, 8)  # Monday

    def test_answer_deadline_federal(self):
        """Test federal answer deadline (21 days)"""
        service_date = date(2024, 1, 15)  # Monday
        deadline = ResponseDeadlineCalculator.calculate_answer_deadline(
            service_date,
            JurisdictionType.FEDERAL,
            waiver=False,
            service_method=ServiceMethod.PERSONAL
        )
        assert deadline is not None
        # 21 days from Jan 15 = Feb 5
        assert deadline.adjusted_deadline >= date(2024, 2, 4)

    def test_answer_deadline_waiver(self):
        """Test federal answer deadline with waiver (60 days)"""
        service_date = date(2024, 1, 15)
        deadline = ResponseDeadlineCalculator.calculate_answer_deadline(
            service_date,
            JurisdictionType.FEDERAL,
            waiver=True,
            service_method=ServiceMethod.MAIL
        )
        assert deadline is not None
        # 60 days should be mid-March
        assert deadline.adjusted_deadline > date(2024, 3, 1)

    def test_discovery_deadline(self):
        """Test discovery response deadline (30 days)"""
        service_date = date(2024, 1, 15)
        deadline = ResponseDeadlineCalculator.calculate_discovery_response_deadline(
            service_date,
            JurisdictionType.FEDERAL,
            ServiceMethod.ELECTRONIC
        )
        assert deadline is not None
        # 30 days should be mid-February
        assert deadline.adjusted_deadline > date(2024, 2, 10)

    def test_appeal_deadline(self):
        """Test notice of appeal deadline"""
        judgment_date = date(2024, 1, 15)
        deadline = ResponseDeadlineCalculator.calculate_appeal_deadline(
            judgment_date,
            JurisdictionType.FEDERAL,
            usa_party=False,
            criminal=False
        )
        assert deadline is not None
        # 30 days for civil appeal

    def test_get_deadline_rules(self):
        """Test getting deadline rules"""
        all_rules = get_all_deadline_rules()
        assert len(all_rules) > 20

        # Test specific rule
        answer_rule = get_deadline_rule("answer_complaint", JurisdictionType.FEDERAL)
        assert answer_rule is not None
        assert answer_rule.base_days == 21

    def test_add_business_days(self):
        """Test adding business days"""
        calc = DeadlineCalculator(JurisdictionType.FEDERAL)
        start = date(2024, 1, 8)  # Monday
        result = calc.add_business_days(start, 5)
        # 5 business days from Monday should be Monday (skipping weekend)
        assert result == date(2024, 1, 15)


# =============================================================================
# ANALYZER TESTS
# =============================================================================

class TestLegalFilingAnalyzer:
    """Tests for the main analyzer"""

    @pytest.fixture
    def sample_complaint(self):
        """Sample complaint text for testing"""
        return """
        UNITED STATES DISTRICT COURT
        SOUTHERN DISTRICT OF NEW YORK

        Case No. 1:24-cv-00123-ABC

        JOHN DOE, an individual,
            Plaintiff,
        v.

        ACME CORPORATION, a Delaware corporation,
            Defendant.

        COMPLAINT FOR DAMAGES

        Plaintiff John Doe, by and through counsel, hereby complains against
        Defendant Acme Corporation as follows:

        PARTIES

        1. Plaintiff John Doe is an individual residing in New York, New York.

        2. Defendant Acme Corporation is a Delaware corporation with its
        principal place of business in New York, New York.

        JURISDICTION AND VENUE

        3. This Court has diversity jurisdiction under 28 U.S.C. § 1332.

        FACTUAL ALLEGATIONS

        4. On or about January 1, 2024, Defendant breached its contract
        with Plaintiff.

        5. As a result, Plaintiff has suffered damages in excess of $75,000.

        CAUSES OF ACTION

        COUNT I - BREACH OF CONTRACT

        6. Defendant breached its contractual obligations to Plaintiff.

        7. As a direct result of Defendant's breach, Plaintiff suffered damages.

        PRAYER FOR RELIEF

        WHEREFORE, Plaintiff requests that this Court:

        A. Award Plaintiff compensatory damages in excess of $75,000;
        B. Award Plaintiff punitive damages of $500,000;
        C. Award Plaintiff costs and attorneys' fees; and
        D. Grant such other relief as the Court deems just and proper.

        JURY DEMAND

        Plaintiff demands a trial by jury on all issues so triable.

        Respectfully submitted,

        /s/ Jane Smith
        Jane Smith, Esq.
        Bar No. 12345
        Smith & Associates
        123 Main Street
        New York, NY 10001
        (212) 555-1234
        jsmith@smithlaw.com

        Attorney for Plaintiff
        """

    def test_create_analyzer(self):
        """Test analyzer creation"""
        analyzer = create_analyzer(jurisdiction="federal", enable_ai=False)
        assert analyzer is not None
        assert isinstance(analyzer, LegalFilingAnalyzer)

    def test_classify_only(self, sample_complaint):
        """Test classification-only mode"""
        analyzer = create_analyzer(enable_ai=False)
        result = analyzer.classify_only(sample_complaint)

        assert result is not None
        assert result.filing_type_code.startswith('A')  # Complaint category
        assert result.confidence > 0.5
        assert result.category == "A"

    def test_extract_only(self, sample_complaint):
        """Test extraction-only mode"""
        analyzer = create_analyzer(enable_ai=False)
        result = analyzer.extract_only(sample_complaint)

        assert result is not None
        assert len(result.case_numbers) > 0
        assert len(result.parties) >= 2
        assert len(result.monetary_amounts) > 0

    @pytest.mark.asyncio
    async def test_full_analysis(self, sample_complaint):
        """Test full analysis"""
        analyzer = create_analyzer(enable_ai=False)

        result = await analyzer.analyze(
            document_text=sample_complaint,
            options={'jurisdiction': 'federal'}
        )

        assert result is not None
        assert result.analysis_id is not None
        assert result.classification is not None
        assert result.extraction is not None
        assert result.deadlines is not None
        assert result.risk is not None
        assert result.summary is not None

        # Check classification
        assert result.classification.filing_type_code.startswith('A')

        # Check extraction
        assert len(result.extraction.parties) >= 2

        # Check deadlines
        assert len(result.deadlines.deadlines) > 0

        # Check summary
        assert len(result.summary.executive_summary) > 0

    @pytest.mark.asyncio
    async def test_analyze_motion_to_dismiss(self):
        """Test analyzing motion to dismiss"""
        motion_text = """
        UNITED STATES DISTRICT COURT
        Case No. 1:24-cv-00123

        DEFENDANT'S MOTION TO DISMISS
        PURSUANT TO RULE 12(b)(6)

        Defendant moves to dismiss Plaintiff's Complaint for failure
        to state a claim upon which relief can be granted.

        Under Bell Atlantic Corp. v. Twombly, 550 U.S. 544 (2007),
        a complaint must contain sufficient factual matter to state
        a claim to relief that is plausible on its face.

        Ashcroft v. Iqbal, 556 U.S. 662 (2009) further clarified
        that the court need not accept legal conclusions as true.

        For the reasons stated herein, this motion should be granted.
        """

        analyzer = create_analyzer(enable_ai=False)
        result = await analyzer.analyze(motion_text)

        # Should classify as motion to dismiss (C category)
        assert result.classification.category == "C"

        # Should extract citations
        assert len(result.extraction.citations['case_law']) >= 2


# =============================================================================
# SUMMARY TEMPLATE TESTS
# =============================================================================

class TestSummaryTemplates:
    """Tests for summary template rendering"""

    @pytest.fixture
    def sample_context(self):
        """Create sample template context"""
        return TemplateContext(
            filing_type="A1",
            filing_type_name="Original Complaint",
            category="Complaints and Initial Pleadings",
            case_number="1:24-cv-00123",
            court="U.S. District Court, S.D.N.Y.",
            filing_date="2024-01-15",
            parties=[
                {"name": "John Doe", "role": "Plaintiff", "entity_type": "Individual"},
                {"name": "Acme Corp", "role": "Defendant", "entity_type": "Corporation"}
            ],
            executive_summary="This is an original complaint for breach of contract.",
            key_points=["Breach of contract claim", "Seeks $75,000 in damages"],
            procedural_status="Case initiation - pleading stage",
            relief_sought="Compensatory and punitive damages",
            case_citations=[
                {"citation": "Twombly, 550 U.S. 544", "type": "case_law"}
            ],
            statute_citations=[
                {"citation": "28 U.S.C. § 1332", "type": "statute"}
            ],
            rule_citations=[],
            monetary_amounts=[
                {"value": 75000, "type": "compensatory"}
            ],
            total_damages=75000,
            deadlines=[
                {
                    "description": "Answer Due",
                    "date": "2024-02-05",
                    "rule_basis": "FRCP 12(a)(1)(A)",
                    "is_jurisdictional": False
                }
            ],
            next_deadline={
                "description": "Answer Due",
                "date": "2024-02-05"
            },
            urgency_level="medium",
            risk_factors=["New lawsuit filed"],
            immediate_actions=["File responsive pleading"],
            recommendations=["Consider settlement discussions"],
            analysis_id="test-123",
            analyzed_at="2024-01-15T10:00:00",
            confidence=0.85
        )

    def test_render_html(self, sample_context):
        """Test HTML rendering"""
        html = SummaryRenderer.render(sample_context, OutputFormat.HTML)
        assert "<!DOCTYPE html>" in html
        assert "Original Complaint" in html
        assert "John Doe" in html

    def test_render_markdown(self, sample_context):
        """Test Markdown rendering"""
        md = SummaryRenderer.render(sample_context, OutputFormat.MARKDOWN)
        assert "# Legal Filing Analysis" in md
        assert "**" in md  # Bold text
        assert "John Doe" in md

    def test_render_plain_text(self, sample_context):
        """Test plain text rendering"""
        text = SummaryRenderer.render(sample_context, OutputFormat.PLAIN_TEXT)
        assert "LEGAL FILING ANALYSIS" in text
        assert "John Doe" in text

    def test_render_json(self, sample_context):
        """Test JSON rendering"""
        json_str = SummaryRenderer.render(sample_context, OutputFormat.JSON)
        data = json.loads(json_str)
        assert "classification" in data
        assert "parties" in data

    def test_render_pdf_ready(self, sample_context):
        """Test PDF-ready HTML rendering"""
        pdf = SummaryRenderer.render(sample_context, OutputFormat.PDF_READY)
        assert "<style>" in pdf
        assert "@page" in pdf  # PDF-specific CSS


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the full system"""

    @pytest.mark.asyncio
    async def test_end_to_end_complaint_analysis(self):
        """Test complete workflow for complaint analysis"""
        complaint = """
        UNITED STATES DISTRICT COURT
        Case No. 2:24-cv-05678

        JANE ROE, Plaintiff, v. XYZ INC., Defendant.

        COMPLAINT

        Plaintiff sues for $100,000 in damages.

        See Smith v. Jones, 100 F.3d 200 (5th Cir. 2020).

        Filed: January 20, 2024
        """

        analyzer = create_analyzer(enable_ai=False)
        result = await analyzer.analyze(complaint)

        # Verify complete analysis
        assert result.analysis_id is not None

        # Verify classification
        assert result.classification.category == "A"

        # Verify extraction
        assert len(result.extraction.case_numbers) > 0
        assert len(result.extraction.parties) >= 2

        # Verify we can render output
        context = TemplateContext.from_analysis_result(result)
        html = SummaryRenderer.render(context, OutputFormat.HTML)
        assert len(html) > 100

    @pytest.mark.asyncio
    async def test_multiple_filing_types(self):
        """Test analyzing different filing types"""
        documents = [
            ("COMPLAINT FOR DAMAGES", "A"),
            ("ANSWER TO COMPLAINT", "B"),
            ("MOTION TO DISMISS", "C"),
            ("MOTION TO COMPEL DISCOVERY", "D"),
            ("MOTION FOR SUMMARY JUDGMENT", "E"),
            ("NOTICE OF APPEAL", "P"),
        ]

        analyzer = create_analyzer(enable_ai=False)

        for doc_title, expected_category in documents:
            result = await analyzer.analyze(doc_title)
            assert result.classification.category == expected_category, \
                f"Expected {expected_category} for '{doc_title}', got {result.classification.category}"


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance tests"""

    def test_classification_speed(self):
        """Test that classification is fast"""
        import time

        analyzer = create_analyzer(enable_ai=False)
        text = "MOTION FOR SUMMARY JUDGMENT ON ALL CLAIMS"

        start = time.time()
        for _ in range(100):
            analyzer.classify_only(text)
        elapsed = time.time() - start

        # Should complete 100 classifications in under 1 second
        assert elapsed < 1.0

    def test_extraction_speed(self):
        """Test that extraction is reasonably fast"""
        import time

        analyzer = create_analyzer(enable_ai=False)
        text = """
        Case No. 1:24-cv-00123
        JOHN DOE v. ACME CORP
        Seeks $75,000 in damages.
        See Twombly, 550 U.S. 544.
        """

        start = time.time()
        for _ in range(50):
            analyzer.extract_only(text)
        elapsed = time.time() - start

        # Should complete 50 extractions in under 2 seconds
        assert elapsed < 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
