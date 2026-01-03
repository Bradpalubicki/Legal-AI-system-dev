"""
Legal Filing Summary Templates
Templates for generating formatted summaries in various formats

This module provides:
- HTML templates for web display
- Plain text templates for email/reports
- Markdown templates for documentation
- JSON schema for API responses
- PDF-ready templates
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import html
import json


# =============================================================================
# TEMPLATE FORMATS
# =============================================================================

class OutputFormat(Enum):
    """Available output formats"""
    HTML = "html"
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    JSON = "json"
    PDF_READY = "pdf_ready"


class SummaryStyle(Enum):
    """Summary styles for different audiences"""
    EXECUTIVE = "executive"      # Brief, high-level
    ATTORNEY = "attorney"        # Detailed, technical
    CLIENT = "client"            # Accessible, explanatory
    COURT = "court"              # Formal, procedural
    INTERNAL = "internal"        # Case management focused


# =============================================================================
# TEMPLATE CLASSES
# =============================================================================

@dataclass
class TemplateContext:
    """Context data for template rendering"""
    # Filing information
    filing_type: str
    filing_type_name: str
    category: str
    case_number: Optional[str]
    court: Optional[str]
    filing_date: Optional[str]

    # Parties
    parties: List[Dict[str, Any]]

    # Key content
    executive_summary: str
    key_points: List[str]
    procedural_status: str
    relief_sought: str

    # Citations
    case_citations: List[Dict[str, Any]]
    statute_citations: List[Dict[str, Any]]
    rule_citations: List[Dict[str, Any]]

    # Financial
    monetary_amounts: List[Dict[str, Any]]
    total_damages: Optional[float]

    # Deadlines
    deadlines: List[Dict[str, Any]]
    next_deadline: Optional[Dict[str, Any]]

    # Risk assessment
    urgency_level: str
    risk_factors: List[str]
    immediate_actions: List[str]
    recommendations: List[str]

    # Metadata
    analysis_id: str
    analyzed_at: str
    confidence: float

    @classmethod
    def from_analysis_result(cls, result: Any) -> 'TemplateContext':
        """Create context from FilingAnalysisResult"""
        # Extract case number
        case_number = None
        if result.extraction.case_numbers:
            case_number = result.extraction.case_numbers[0].get('full_number')

        # Get next deadline
        next_deadline = None
        if result.deadlines.deadlines:
            next_deadline = result.deadlines.deadlines[0]

        # Calculate total damages
        total_damages = None
        if result.extraction.monetary_amounts:
            total = sum(
                a.get('value', 0) for a in result.extraction.monetary_amounts
                if a.get('value')
            )
            if total > 0:
                total_damages = total

        return cls(
            filing_type=result.classification.filing_type_code,
            filing_type_name=result.classification.filing_type_name,
            category=result.classification.category_name,
            case_number=case_number,
            court=None,  # Would need to extract from document
            filing_date=result.summary.filing_date,
            parties=result.extraction.parties,
            executive_summary=result.summary.executive_summary,
            key_points=result.summary.key_points,
            procedural_status=result.summary.procedural_status,
            relief_sought=result.summary.main_relief_sought,
            case_citations=result.extraction.citations.get('case_law', []),
            statute_citations=result.extraction.citations.get('statutes', []),
            rule_citations=result.extraction.citations.get('rules', []),
            monetary_amounts=result.extraction.monetary_amounts,
            total_damages=total_damages,
            deadlines=result.deadlines.deadlines,
            next_deadline=next_deadline,
            urgency_level=result.risk.urgency_level.value,
            risk_factors=result.risk.risk_factors,
            immediate_actions=result.risk.immediate_actions,
            recommendations=result.risk.recommendations,
            analysis_id=result.analysis_id,
            analyzed_at=result.analyzed_at,
            confidence=result.classification.confidence
        )


# =============================================================================
# HTML TEMPLATES
# =============================================================================

HTML_SUMMARY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a365d 0%, #2d4a7c 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; font-size: 1.5em; }}
        .header .case-info {{ font-size: 0.9em; opacity: 0.9; margin-top: 8px; }}
        .urgency-badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 0.85em; font-weight: bold; text-transform: uppercase; }}
        .urgency-critical {{ background: #e53e3e; color: white; }}
        .urgency-high {{ background: #ed8936; color: white; }}
        .urgency-medium {{ background: #ecc94b; color: #744210; }}
        .urgency-low {{ background: #48bb78; color: white; }}
        .section {{ background: #f7fafc; border-radius: 8px; padding: 16px; margin-bottom: 16px; border-left: 4px solid #3182ce; }}
        .section h2 {{ color: #2d3748; font-size: 1.1em; margin-top: 0; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }}
        .deadline-item {{ background: white; padding: 12px; border-radius: 4px; margin: 8px 0; border: 1px solid #e2e8f0; }}
        .deadline-date {{ font-weight: bold; color: #c53030; }}
        .party-item {{ display: inline-block; background: #edf2f7; padding: 4px 8px; border-radius: 4px; margin: 2px; font-size: 0.9em; }}
        .citation-item {{ font-family: 'Georgia', serif; font-style: italic; margin: 4px 0; }}
        .key-point {{ padding: 8px 12px; background: #ebf8ff; border-radius: 4px; margin: 4px 0; }}
        .action-item {{ padding: 8px 12px; background: #fff5f5; border-left: 3px solid #c53030; margin: 4px 0; }}
        .footer {{ font-size: 0.8em; color: #718096; border-top: 1px solid #e2e8f0; padding-top: 16px; margin-top: 20px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 4px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{filing_type_name}</h1>
        <div class="case-info">
            {case_number_html}
            <span class="urgency-badge urgency-{urgency_level}">{urgency_level}</span>
        </div>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <p>{executive_summary}</p>
    </div>

    {parties_section}

    {deadlines_section}

    {key_points_section}

    {actions_section}

    {citations_section}

    {financial_section}

    <div class="footer">
        <p>Analysis ID: {analysis_id}<br>
        Generated: {analyzed_at}<br>
        Confidence: {confidence_pct}%</p>
        <p><em>DISCLAIMER: This analysis is for educational purposes only and does not constitute legal advice.</em></p>
    </div>
</body>
</html>
"""


def render_html_summary(context: TemplateContext) -> str:
    """Render HTML summary from context"""
    # Case number
    case_number_html = f"Case: {html.escape(context.case_number)}" if context.case_number else ""

    # Parties section
    if context.parties:
        parties_html = '<div class="section"><h2>Parties</h2>'
        for party in context.parties:
            role = party.get('role', 'Party').title()
            name = html.escape(party.get('name', 'Unknown'))
            parties_html += f'<span class="party-item"><strong>{role}:</strong> {name}</span> '
        parties_html += '</div>'
    else:
        parties_html = ''

    # Deadlines section
    if context.deadlines:
        deadlines_html = '<div class="section"><h2>Deadlines</h2>'
        for deadline in context.deadlines:
            desc = html.escape(deadline.get('description', ''))
            date_str = deadline.get('date', 'TBD')
            rule = html.escape(deadline.get('rule_basis', ''))
            jurisdictional = ' <strong>(JURISDICTIONAL)</strong>' if deadline.get('is_jurisdictional') else ''
            deadlines_html += f'''
            <div class="deadline-item">
                <span class="deadline-date">{date_str}</span> - {desc}{jurisdictional}
                <br><small>Rule: {rule}</small>
            </div>
            '''
        deadlines_html += '</div>'
    else:
        deadlines_html = ''

    # Key points section
    if context.key_points:
        points_html = '<div class="section"><h2>Key Points</h2>'
        for point in context.key_points:
            points_html += f'<div class="key-point">{html.escape(point)}</div>'
        points_html += '</div>'
    else:
        points_html = ''

    # Actions section
    if context.immediate_actions or context.recommendations:
        actions_html = '<div class="section"><h2>Required Actions</h2>'
        for action in context.immediate_actions:
            actions_html += f'<div class="action-item"><strong>IMMEDIATE:</strong> {html.escape(action)}</div>'
        for rec in context.recommendations:
            actions_html += f'<div class="key-point">{html.escape(rec)}</div>'
        actions_html += '</div>'
    else:
        actions_html = ''

    # Citations section
    if context.case_citations or context.statute_citations:
        citations_html = '<div class="section"><h2>Legal Citations</h2>'
        if context.case_citations:
            citations_html += '<h3>Case Law</h3><ul>'
            for cite in context.case_citations[:10]:  # Limit to 10
                citations_html += f'<li class="citation-item">{html.escape(cite.get("citation", ""))}</li>'
            citations_html += '</ul>'
        if context.statute_citations:
            citations_html += '<h3>Statutes</h3><ul>'
            for cite in context.statute_citations[:10]:
                citations_html += f'<li class="citation-item">{html.escape(cite.get("citation", ""))}</li>'
            citations_html += '</ul>'
        citations_html += '</div>'
    else:
        citations_html = ''

    # Financial section
    if context.total_damages:
        financial_html = f'''
        <div class="section">
            <h2>Financial Information</h2>
            <p><strong>Total Damages Claimed:</strong> ${context.total_damages:,.2f}</p>
        </div>
        '''
    else:
        financial_html = ''

    return HTML_SUMMARY_TEMPLATE.format(
        filing_type_name=html.escape(context.filing_type_name),
        case_number_html=case_number_html,
        urgency_level=context.urgency_level.lower(),
        executive_summary=html.escape(context.executive_summary),
        parties_section=parties_html,
        deadlines_section=deadlines_html,
        key_points_section=points_html,
        actions_section=actions_html,
        citations_section=citations_html,
        financial_section=financial_html,
        analysis_id=context.analysis_id,
        analyzed_at=context.analyzed_at,
        confidence_pct=int(context.confidence * 100)
    )


# =============================================================================
# PLAIN TEXT TEMPLATES
# =============================================================================

PLAIN_TEXT_TEMPLATE = """
================================================================================
LEGAL FILING ANALYSIS
================================================================================

FILING TYPE: {filing_type_name}
CATEGORY: {category}
CASE NUMBER: {case_number}
URGENCY: {urgency_level}
CONFIDENCE: {confidence_pct}%

--------------------------------------------------------------------------------
EXECUTIVE SUMMARY
--------------------------------------------------------------------------------
{executive_summary}

{parties_section}
{deadlines_section}
{key_points_section}
{actions_section}
{citations_section}
{financial_section}
--------------------------------------------------------------------------------
ANALYSIS METADATA
--------------------------------------------------------------------------------
Analysis ID: {analysis_id}
Generated: {analyzed_at}

DISCLAIMER: This analysis is for educational purposes only and does not
constitute legal advice. Please consult a licensed attorney for legal matters.
================================================================================
"""


def render_plain_text_summary(context: TemplateContext) -> str:
    """Render plain text summary from context"""
    # Parties
    if context.parties:
        parties_lines = ["", "PARTIES", "-" * 40]
        for party in context.parties:
            role = party.get('role', 'Party').upper()
            name = party.get('name', 'Unknown')
            parties_lines.append(f"  {role}: {name}")
        parties_section = "\n".join(parties_lines) + "\n"
    else:
        parties_section = ""

    # Deadlines
    if context.deadlines:
        deadline_lines = ["", "DEADLINES", "-" * 40]
        for deadline in context.deadlines:
            desc = deadline.get('description', '')
            date_str = deadline.get('date', 'TBD')
            jurisdictional = " [JURISDICTIONAL]" if deadline.get('is_jurisdictional') else ""
            deadline_lines.append(f"  * {date_str}: {desc}{jurisdictional}")
        deadlines_section = "\n".join(deadline_lines) + "\n"
    else:
        deadlines_section = ""

    # Key points
    if context.key_points:
        points_lines = ["", "KEY POINTS", "-" * 40]
        for point in context.key_points:
            points_lines.append(f"  * {point}")
        key_points_section = "\n".join(points_lines) + "\n"
    else:
        key_points_section = ""

    # Actions
    if context.immediate_actions or context.recommendations:
        action_lines = ["", "REQUIRED ACTIONS", "-" * 40]
        for action in context.immediate_actions:
            action_lines.append(f"  [!] IMMEDIATE: {action}")
        for rec in context.recommendations:
            action_lines.append(f"  [ ] {rec}")
        actions_section = "\n".join(action_lines) + "\n"
    else:
        actions_section = ""

    # Citations
    if context.case_citations or context.statute_citations:
        citation_lines = ["", "CITATIONS", "-" * 40]
        if context.case_citations:
            citation_lines.append("  Case Law:")
            for cite in context.case_citations[:5]:
                citation_lines.append(f"    - {cite.get('citation', '')}")
        if context.statute_citations:
            citation_lines.append("  Statutes:")
            for cite in context.statute_citations[:5]:
                citation_lines.append(f"    - {cite.get('citation', '')}")
        citations_section = "\n".join(citation_lines) + "\n"
    else:
        citations_section = ""

    # Financial
    if context.total_damages:
        financial_section = f"\nFINANCIAL\n{'-' * 40}\n  Total Damages Claimed: ${context.total_damages:,.2f}\n"
    else:
        financial_section = ""

    return PLAIN_TEXT_TEMPLATE.format(
        filing_type_name=context.filing_type_name,
        category=context.category,
        case_number=context.case_number or "Not identified",
        urgency_level=context.urgency_level.upper(),
        confidence_pct=int(context.confidence * 100),
        executive_summary=context.executive_summary,
        parties_section=parties_section,
        deadlines_section=deadlines_section,
        key_points_section=key_points_section,
        actions_section=actions_section,
        citations_section=citations_section,
        financial_section=financial_section,
        analysis_id=context.analysis_id,
        analyzed_at=context.analyzed_at
    )


# =============================================================================
# MARKDOWN TEMPLATES
# =============================================================================

def render_markdown_summary(context: TemplateContext) -> str:
    """Render Markdown summary from context"""
    lines = [
        f"# Legal Filing Analysis: {context.filing_type_name}",
        "",
        f"**Category:** {context.category}  ",
        f"**Case Number:** {context.case_number or 'Not identified'}  ",
        f"**Urgency:** `{context.urgency_level.upper()}`  ",
        f"**Confidence:** {int(context.confidence * 100)}%",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        context.executive_summary,
        ""
    ]

    # Parties
    if context.parties:
        lines.extend(["## Parties", ""])
        for party in context.parties:
            role = party.get('role', 'Party').title()
            name = party.get('name', 'Unknown')
            entity = party.get('entity_type', '')
            lines.append(f"- **{role}:** {name}" + (f" ({entity})" if entity else ""))
        lines.append("")

    # Deadlines
    if context.deadlines:
        lines.extend(["## Deadlines", "", "| Date | Description | Rule | Jurisdictional |", "|------|-------------|------|----------------|"])
        for deadline in context.deadlines:
            desc = deadline.get('description', '')
            date_str = deadline.get('date', 'TBD')
            rule = deadline.get('rule_basis', '')
            jurisdictional = "Yes" if deadline.get('is_jurisdictional') else "No"
            lines.append(f"| {date_str} | {desc} | {rule} | {jurisdictional} |")
        lines.append("")

    # Key Points
    if context.key_points:
        lines.extend(["## Key Points", ""])
        for point in context.key_points:
            lines.append(f"- {point}")
        lines.append("")

    # Actions
    if context.immediate_actions or context.recommendations:
        lines.extend(["## Required Actions", ""])
        if context.immediate_actions:
            lines.append("### Immediate")
            for action in context.immediate_actions:
                lines.append(f"- [ ] **{action}**")
            lines.append("")
        if context.recommendations:
            lines.append("### Recommendations")
            for rec in context.recommendations:
                lines.append(f"- [ ] {rec}")
            lines.append("")

    # Risk Factors
    if context.risk_factors:
        lines.extend(["## Risk Factors", ""])
        for factor in context.risk_factors:
            lines.append(f"- {factor}")
        lines.append("")

    # Citations
    if context.case_citations or context.statute_citations:
        lines.extend(["## Legal Citations", ""])
        if context.case_citations:
            lines.append("### Case Law")
            for cite in context.case_citations[:10]:
                lines.append(f"- *{cite.get('citation', '')}*")
            lines.append("")
        if context.statute_citations:
            lines.append("### Statutes")
            for cite in context.statute_citations[:10]:
                lines.append(f"- {cite.get('citation', '')}")
            lines.append("")

    # Financial
    if context.total_damages:
        lines.extend([
            "## Financial Information",
            "",
            f"**Total Damages Claimed:** ${context.total_damages:,.2f}",
            ""
        ])

    # Footer
    lines.extend([
        "---",
        "",
        f"*Analysis ID: {context.analysis_id}*  ",
        f"*Generated: {context.analyzed_at}*",
        "",
        "> **Disclaimer:** This analysis is for educational purposes only and does not constitute legal advice.",
        ""
    ])

    return "\n".join(lines)


# =============================================================================
# JSON TEMPLATES
# =============================================================================

def render_json_summary(context: TemplateContext) -> str:
    """Render JSON summary from context"""
    output = {
        "analysis_metadata": {
            "analysis_id": context.analysis_id,
            "analyzed_at": context.analyzed_at,
            "confidence": context.confidence,
            "disclaimer": "This analysis is for educational purposes only and does not constitute legal advice."
        },
        "classification": {
            "filing_type_code": context.filing_type,
            "filing_type_name": context.filing_type_name,
            "category": context.category,
            "confidence": context.confidence
        },
        "case_information": {
            "case_number": context.case_number,
            "court": context.court,
            "filing_date": context.filing_date
        },
        "parties": context.parties,
        "summary": {
            "executive_summary": context.executive_summary,
            "key_points": context.key_points,
            "procedural_status": context.procedural_status,
            "relief_sought": context.relief_sought
        },
        "deadlines": context.deadlines,
        "risk_assessment": {
            "urgency_level": context.urgency_level,
            "risk_factors": context.risk_factors,
            "immediate_actions": context.immediate_actions,
            "recommendations": context.recommendations
        },
        "citations": {
            "case_law": context.case_citations,
            "statutes": context.statute_citations,
            "rules": context.rule_citations
        },
        "financial": {
            "monetary_amounts": context.monetary_amounts,
            "total_damages": context.total_damages
        }
    }

    return json.dumps(output, indent=2, default=str)


# =============================================================================
# EMAIL TEMPLATES
# =============================================================================

EMAIL_SUBJECT_TEMPLATE = "[{urgency}] Filing Analysis: {filing_type} - {case_number}"

EMAIL_HTML_TEMPLATE = """
<html>
<body style="font-family: Arial, sans-serif; color: #333; max-width: 600px;">
    <div style="background: #1a365d; color: white; padding: 15px; border-radius: 4px;">
        <h2 style="margin: 0;">{filing_type_name}</h2>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">{case_number}</p>
    </div>

    <div style="padding: 15px; background: {urgency_bg}; margin-top: 10px; border-radius: 4px;">
        <strong>Urgency Level: {urgency_level}</strong>
    </div>

    <h3>Summary</h3>
    <p>{executive_summary}</p>

    {deadline_alert}

    {action_items}

    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">

    <p style="font-size: 12px; color: #666;">
        Analysis ID: {analysis_id}<br>
        <em>This analysis is for educational purposes only and does not constitute legal advice.</em>
    </p>
</body>
</html>
"""


def render_email_summary(context: TemplateContext) -> Dict[str, str]:
    """Render email summary with subject and body"""
    # Subject
    subject = EMAIL_SUBJECT_TEMPLATE.format(
        urgency=context.urgency_level.upper(),
        filing_type=context.filing_type_name,
        case_number=context.case_number or "New Filing"
    )

    # Urgency styling
    urgency_colors = {
        'critical': '#fee2e2',
        'high': '#fed7aa',
        'medium': '#fef3c7',
        'low': '#d1fae5'
    }
    urgency_bg = urgency_colors.get(context.urgency_level.lower(), '#f3f4f6')

    # Deadline alert
    if context.next_deadline:
        deadline_alert = f"""
        <div style="background: #fff5f5; border-left: 4px solid #c53030; padding: 10px; margin: 15px 0;">
            <strong>Next Deadline:</strong> {context.next_deadline.get('date', 'TBD')}<br>
            {context.next_deadline.get('description', '')}
        </div>
        """
    else:
        deadline_alert = ""

    # Action items
    if context.immediate_actions:
        action_items = "<h3>Required Actions</h3><ul>"
        for action in context.immediate_actions:
            action_items += f"<li><strong>{html.escape(action)}</strong></li>"
        action_items += "</ul>"
    else:
        action_items = ""

    body = EMAIL_HTML_TEMPLATE.format(
        filing_type_name=html.escape(context.filing_type_name),
        case_number=html.escape(context.case_number or ""),
        urgency_level=context.urgency_level.upper(),
        urgency_bg=urgency_bg,
        executive_summary=html.escape(context.executive_summary),
        deadline_alert=deadline_alert,
        action_items=action_items,
        analysis_id=context.analysis_id
    )

    return {
        "subject": subject,
        "body_html": body,
        "body_text": render_plain_text_summary(context)
    }


# =============================================================================
# PDF-READY TEMPLATES
# =============================================================================

PDF_READY_TEMPLATE = """
<style>
    @page {{ margin: 1in; }}
    body {{ font-family: 'Times New Roman', serif; font-size: 12pt; line-height: 1.5; }}
    .header {{ text-align: center; border-bottom: 2px solid black; padding-bottom: 10px; margin-bottom: 20px; }}
    .header h1 {{ font-size: 16pt; margin: 0; }}
    .section {{ margin-bottom: 20px; }}
    .section-title {{ font-size: 14pt; font-weight: bold; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-bottom: 10px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background: #f0f0f0; }}
    .footer {{ margin-top: 30px; font-size: 10pt; color: #666; }}
</style>

<div class="header">
    <h1>LEGAL FILING ANALYSIS REPORT</h1>
    <p>{filing_type_name}</p>
    <p>Case No. {case_number}</p>
</div>

<div class="section">
    <div class="section-title">Filing Information</div>
    <table>
        <tr><th>Filing Type</th><td>{filing_type_name}</td></tr>
        <tr><th>Category</th><td>{category}</td></tr>
        <tr><th>Case Number</th><td>{case_number}</td></tr>
        <tr><th>Urgency</th><td>{urgency_level}</td></tr>
        <tr><th>Analysis Confidence</th><td>{confidence_pct}%</td></tr>
    </table>
</div>

<div class="section">
    <div class="section-title">Executive Summary</div>
    <p>{executive_summary}</p>
</div>

{parties_table}

{deadlines_table}

{citations_section}

<div class="footer">
    <p>Analysis ID: {analysis_id}<br>
    Report Generated: {analyzed_at}</p>
    <p><strong>DISCLAIMER:</strong> This analysis is provided for educational purposes only and does not constitute legal advice. Please consult with a licensed attorney for legal matters.</p>
</div>
"""


def render_pdf_ready_summary(context: TemplateContext) -> str:
    """Render PDF-ready HTML summary"""
    # Parties table
    if context.parties:
        parties_table = """
        <div class="section">
            <div class="section-title">Parties</div>
            <table>
                <tr><th>Name</th><th>Role</th><th>Entity Type</th></tr>
        """
        for party in context.parties:
            parties_table += f"""
                <tr>
                    <td>{html.escape(party.get('name', ''))}</td>
                    <td>{html.escape(party.get('role', ''))}</td>
                    <td>{html.escape(party.get('entity_type', ''))}</td>
                </tr>
            """
        parties_table += "</table></div>"
    else:
        parties_table = ""

    # Deadlines table
    if context.deadlines:
        deadlines_table = """
        <div class="section">
            <div class="section-title">Deadlines</div>
            <table>
                <tr><th>Date</th><th>Description</th><th>Rule</th><th>Jurisdictional</th></tr>
        """
        for deadline in context.deadlines:
            deadlines_table += f"""
                <tr>
                    <td>{deadline.get('date', 'TBD')}</td>
                    <td>{html.escape(deadline.get('description', ''))}</td>
                    <td>{html.escape(deadline.get('rule_basis', ''))}</td>
                    <td>{'Yes' if deadline.get('is_jurisdictional') else 'No'}</td>
                </tr>
            """
        deadlines_table += "</table></div>"
    else:
        deadlines_table = ""

    # Citations section
    if context.case_citations:
        citations_section = """
        <div class="section">
            <div class="section-title">Legal Citations</div>
            <ul>
        """
        for cite in context.case_citations[:15]:
            citations_section += f"<li><em>{html.escape(cite.get('citation', ''))}</em></li>"
        citations_section += "</ul></div>"
    else:
        citations_section = ""

    return PDF_READY_TEMPLATE.format(
        filing_type_name=html.escape(context.filing_type_name),
        category=html.escape(context.category),
        case_number=html.escape(context.case_number or "Not identified"),
        urgency_level=context.urgency_level.upper(),
        confidence_pct=int(context.confidence * 100),
        executive_summary=html.escape(context.executive_summary),
        parties_table=parties_table,
        deadlines_table=deadlines_table,
        citations_section=citations_section,
        analysis_id=context.analysis_id,
        analyzed_at=context.analyzed_at
    )


# =============================================================================
# MAIN RENDERER CLASS
# =============================================================================

class SummaryRenderer:
    """Main class for rendering summaries in various formats"""

    @staticmethod
    def render(
        context: TemplateContext,
        output_format: OutputFormat = OutputFormat.HTML,
        style: SummaryStyle = SummaryStyle.ATTORNEY
    ) -> str:
        """
        Render summary in specified format

        Args:
            context: TemplateContext with analysis data
            output_format: Desired output format
            style: Summary style for audience

        Returns:
            Formatted summary string
        """
        renderers = {
            OutputFormat.HTML: render_html_summary,
            OutputFormat.PLAIN_TEXT: render_plain_text_summary,
            OutputFormat.MARKDOWN: render_markdown_summary,
            OutputFormat.JSON: render_json_summary,
            OutputFormat.PDF_READY: render_pdf_ready_summary,
        }

        renderer = renderers.get(output_format, render_html_summary)
        return renderer(context)

    @staticmethod
    def render_email(context: TemplateContext) -> Dict[str, str]:
        """Render email-formatted summary"""
        return render_email_summary(context)

    @staticmethod
    def render_all_formats(context: TemplateContext) -> Dict[str, str]:
        """Render summary in all available formats"""
        return {
            'html': render_html_summary(context),
            'plain_text': render_plain_text_summary(context),
            'markdown': render_markdown_summary(context),
            'json': render_json_summary(context),
            'pdf_ready': render_pdf_ready_summary(context),
        }


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "OutputFormat",
    "SummaryStyle",

    # Classes
    "TemplateContext",
    "SummaryRenderer",

    # Render functions
    "render_html_summary",
    "render_plain_text_summary",
    "render_markdown_summary",
    "render_json_summary",
    "render_pdf_ready_summary",
    "render_email_summary",
]
