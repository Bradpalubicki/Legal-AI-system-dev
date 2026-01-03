"""
Legal Analysis Module
Comprehensive AI-powered legal document analysis system

This module provides:
- Document classification (60+ filing types)
- Data extraction (case numbers, citations, parties, etc.)
- Deadline calculation (federal and state rules)
- AI-powered analysis and summarization
- Multiple output formats (HTML, Markdown, JSON, PDF)

Usage:
    from app.src.services.legal_analysis import (
        LegalFilingAnalyzer,
        create_analyzer,
        DeadlineCalculator,
        JurisdictionType
    )

    # Create analyzer
    analyzer = create_analyzer(jurisdiction='federal')

    # Analyze a filing
    result = await analyzer.analyze(document_text)

    # Get formatted output
    from app.src.services.legal_analysis import SummaryRenderer, OutputFormat
    html_output = SummaryRenderer.render(result, OutputFormat.HTML)
"""

# Filing Types
from .filing_types import (
    FilingType,
    FilingCategory,
    FILING_CATEGORIES,
    get_filing_type,
    get_all_filing_types,
    get_filing_types_by_category,
    classify_filing_by_patterns,
    search_filing_types,
)

# Extraction Patterns
from .extraction_patterns import (
    CourtType,
    CaseNumberPattern,
    PartyExtractionResult,
    CitationResult,
    extract_case_number,
    extract_all_citations,
    extract_monetary_amounts,
    extract_parties_from_caption,
    determine_entity_type,
)

# Aliases for backward compatibility
CaseNumber = CaseNumberPattern
LegalCitation = CitationResult
Party = PartyExtractionResult
extract_parties = extract_parties_from_caption

# Deadline Rules
from .deadline_rules import (
    JurisdictionType,
    DeadlineType,
    ServiceMethod,
    Holiday,
    DeadlineRule,
    CalculatedDeadline,
    FederalHolidayCalendar,
    StateHolidayCalendar,
    DeadlineCalculator,
    ResponseDeadlineCalculator,
    AppealBriefCalculator,
    FEDERAL_DEADLINE_RULES,
    get_all_deadline_rules,
    get_deadline_rule,
    get_deadline_rules_by_type,
    format_deadline_info,
)

# Legal Prompts
from .legal_prompts import (
    PromptCategory,
    PromptConfig,
    LegalPromptBuilder,
    LEGAL_EXPERT_SYSTEM_PROMPT,
    CLASSIFICATION_SYSTEM_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    SUMMARIZATION_SYSTEM_PROMPT,
    COMPREHENSIVE_ANALYSIS_PROMPT,
    OUTPUT_SCHEMA_INSTRUCTIONS,
    get_prompt_template,
)

# Core Analyzer
from .legal_filing_analyzer import (
    LegalFilingAnalyzer,
    FilingAnalysisResult,
    ClassificationResult,
    ExtractionResult,
    DeadlineResult,
    RiskAssessment,
    AnalysisSummary,
    ConfidenceLevel,
    UrgencyLevel,
    create_analyzer,
)

# Summary Templates
from .summary_templates import (
    OutputFormat,
    SummaryStyle,
    TemplateContext,
    SummaryRenderer,
    render_html_summary,
    render_plain_text_summary,
    render_markdown_summary,
    render_json_summary,
    render_pdf_ready_summary,
    render_email_summary,
)

# Integration
from .integration import (
    LegalAnalysisIntegration,
    AIServiceAdapter,
    quick_analyze,
    get_filing_deadlines,
    create_integrated_analyzer,
)


__all__ = [
    # Filing Types
    "FilingType",
    "FilingCategory",
    "FILING_CATEGORIES",
    "get_filing_type",
    "get_all_filing_types",
    "get_filing_types_by_category",
    "classify_filing_by_patterns",
    "search_filing_types",

    # Extraction
    "CourtType",
    "CaseNumberPattern",
    "PartyExtractionResult",
    "CitationResult",
    "CaseNumber",  # Alias
    "LegalCitation",  # Alias
    "Party",  # Alias
    "extract_case_number",
    "extract_all_citations",
    "extract_parties",
    "extract_parties_from_caption",
    "extract_monetary_amounts",
    "determine_entity_type",

    # Deadlines
    "JurisdictionType",
    "DeadlineType",
    "ServiceMethod",
    "Holiday",
    "DeadlineRule",
    "CalculatedDeadline",
    "FederalHolidayCalendar",
    "StateHolidayCalendar",
    "DeadlineCalculator",
    "ResponseDeadlineCalculator",
    "AppealBriefCalculator",
    "FEDERAL_DEADLINE_RULES",
    "get_all_deadline_rules",
    "get_deadline_rule",
    "get_deadline_rules_by_type",
    "format_deadline_info",

    # Prompts
    "PromptCategory",
    "PromptConfig",
    "LegalPromptBuilder",
    "LEGAL_EXPERT_SYSTEM_PROMPT",
    "CLASSIFICATION_SYSTEM_PROMPT",
    "EXTRACTION_SYSTEM_PROMPT",
    "SUMMARIZATION_SYSTEM_PROMPT",
    "COMPREHENSIVE_ANALYSIS_PROMPT",
    "OUTPUT_SCHEMA_INSTRUCTIONS",
    "get_prompt_template",

    # Analyzer
    "LegalFilingAnalyzer",
    "FilingAnalysisResult",
    "ClassificationResult",
    "ExtractionResult",
    "DeadlineResult",
    "RiskAssessment",
    "AnalysisSummary",
    "ConfidenceLevel",
    "UrgencyLevel",
    "create_analyzer",

    # Templates
    "OutputFormat",
    "SummaryStyle",
    "TemplateContext",
    "SummaryRenderer",
    "render_html_summary",
    "render_plain_text_summary",
    "render_markdown_summary",
    "render_json_summary",
    "render_pdf_ready_summary",
    "render_email_summary",

    # Integration
    "LegalAnalysisIntegration",
    "AIServiceAdapter",
    "quick_analyze",
    "get_filing_deadlines",
    "create_integrated_analyzer",
]

__version__ = "1.0.0"
