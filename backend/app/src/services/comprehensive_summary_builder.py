"""
Comprehensive Summary Builder
Builds detailed, structured summaries from extracted legal document data
NO MORE relying on AI to follow prompt instructions - we build it ourselves
"""

from typing import Dict, Any, List


def build_comprehensive_summary(analysis_data: Dict[str, Any]) -> str:
    """
    Build a COMPREHENSIVE, STRUCTURED summary from extracted data.
    This guarantees we include ALL critical information.
    """

    sections = []

    # DOCUMENT INFO SECTION
    doc_info_parts = []
    doc_type = analysis_data.get("document_type", "Legal Document")
    doc_info_parts.append(f"This is a {doc_type}.")

    # Filer info
    filer = analysis_data.get("filer", {})
    if filer and filer.get("name"):
        doc_info_parts.append(
            f"Filed by {filer.get('name')} as {filer.get('role', 'party')} "
            f"{('representing ' + filer.get('representing')) if filer.get('representing') else ''}."
        )

    # Case info
    case_caption = analysis_data.get("case_caption", "")
    case_number = analysis_data.get("case_number", "")
    court = analysis_data.get("court", "")
    filing_date = analysis_data.get("filing_date", "")

    if case_caption or case_number:
        case_info = f"Case: {case_caption}"
        if case_number:
            case_info += f" ({case_number})"
        doc_info_parts.append(case_info + ".")

    if filing_date or court:
        filing_info = f"Filed"
        if filing_date:
            filing_info += f" on {filing_date}"
        if court:
            filing_info += f" in {court}"
        doc_info_parts.append(filing_info + ".")

    if doc_info_parts:
        sections.append("DOCUMENT INFO: " + " ".join(doc_info_parts))

    # PARTIES SECTION - Show only key parties actively involved in THIS matter
    parties = analysis_data.get("all_parties", analysis_data.get("parties", []))

    # Identify key parties (non-debtor parties with active roles)
    key_parties = []
    debtor_parties = []

    for party in parties:
        role = party.get("role", "").lower()
        name = party.get("name", "Unknown")

        # Skip if it's just a jointly administered debtor (not the main one)
        if "debtor" in role and "jointly administered" in party.get("relationship", "").lower():
            debtor_parties.append(name)
            continue

        # Include key active parties
        if any(keyword in role for keyword in ["trustee", "claimant", "plaintiff", "defendant", "petitioner", "respondent", "creditor"]):
            relationship = party.get("relationship", party.get("relationship_to_case", ""))
            party_str = f"{name} ({party.get('role', 'party')})"
            if relationship and "jointly administered" not in relationship.lower():
                party_str += f" - {relationship}"
            key_parties.append(party_str)
        elif "debtor" in role and "primary" in party.get("relationship", "").lower():
            # Include primary debtor
            key_parties.append(f"{name} ({party.get('role', 'party')})")

    if key_parties:
        party_text = "KEY PARTIES: " + "; ".join(key_parties[:5])  # Limit to 5 key parties
        if debtor_parties and len(debtor_parties) > 1:
            party_text += f" [Note: Case includes {len(debtor_parties)} jointly administered entities]"
        sections.append(party_text + ".")

    # Add opposing party details if available and not already included
    opposing = analysis_data.get("opposing_party", {})
    if opposing and opposing.get("name"):
        # Check if not already in key parties
        if not any(opposing.get("name", "") in kp for kp in key_parties):
            opp_desc = f"OPPOSING PARTY: {opposing.get('name')} ({opposing.get('role', 'party')})"
            if opposing.get("their_claim"):
                opp_desc += f" - {opposing.get('their_claim')}"
            sections.append(opp_desc + ".")

    # CORE DISPUTE
    core_dispute = analysis_data.get("core_dispute", analysis_data.get("summary", ""))
    if core_dispute and core_dispute != analysis_data.get("summary", ""):
        sections.append(f"THE DISPUTE: {core_dispute}")

    # FINANCIAL AMOUNTS - CRITICAL
    financial_amounts = analysis_data.get("all_financial_amounts", analysis_data.get("financial_amounts", []))
    if financial_amounts:
        fin_desc = []
        for amt in financial_amounts[:10]:  # First 10 amounts
            amount = amt.get("amount", "")
            description = amt.get("description", "")
            disputed = amt.get("disputed", False)
            dispute_reason = amt.get("dispute_reason", "")

            amt_str = f"{amount}"
            if description:
                amt_str += f" - {description}"
            if disputed:
                amt_str += f" [DISPUTED: {dispute_reason}]"
            fin_desc.append(amt_str)

        if fin_desc:
            sections.append("FINANCIAL AMOUNTS: " + "; ".join(fin_desc) + ".")

    # KEY ARGUMENTS
    key_arguments = analysis_data.get("key_arguments", [])
    if key_arguments:
        arg_desc = []
        for i, arg in enumerate(key_arguments[:5], 1):
            arg_text = arg.get("argument", "")
            supporting_facts = arg.get("supporting_facts", "")
            legal_basis = arg.get("legal_basis", "")

            arg_str = f"({i}) {arg_text}"
            if supporting_facts:
                arg_str += f" - {supporting_facts}"
            if legal_basis:
                arg_str += f" [Legal basis: {legal_basis}]"
            arg_desc.append(arg_str)

        if arg_desc:
            sections.append("KEY ARGUMENTS: " + " ".join(arg_desc))

    # DEADLINES - CRITICAL
    deadlines = analysis_data.get("all_deadlines", analysis_data.get("deadlines", []))
    if deadlines:
        deadline_desc = []
        for dl in deadlines[:10]:
            deadline = dl.get("deadline", "")
            action = dl.get("action_required", "")
            consequence = dl.get("consequence", dl.get("consequence_if_missed", ""))
            urgency = dl.get("urgency", "")

            dl_str = f"{deadline}"
            if action:
                dl_str += f" - {action}"
            if consequence:
                dl_str += f" (If missed: {consequence})"
            if urgency == "high":
                dl_str = f"**URGENT** {dl_str}"
            deadline_desc.append(dl_str)

        if deadline_desc:
            sections.append("DEADLINES: " + "; ".join(deadline_desc) + ".")

    # KEY DATES
    key_dates = analysis_data.get("all_dates", analysis_data.get("key_dates", []))
    if key_dates:
        date_desc = []
        for dt in key_dates[:10]:
            date = dt.get("date", "")
            event = dt.get("event", "")
            significance = dt.get("significance", "")

            dt_str = f"{date}: {event}"
            if significance:
                dt_str += f" ({significance})"
            date_desc.append(dt_str)

        if date_desc:
            sections.append("KEY DATES: " + "; ".join(date_desc) + ".")

    # PROCEDURAL HISTORY
    proc_history = analysis_data.get("procedural_history", [])
    if proc_history:
        sections.append("PROCEDURAL HISTORY: " + "; ".join(proc_history[:5]) + ".")

    # RELIEF REQUESTED - CRITICAL
    relief = analysis_data.get("relief_requested", [])
    if relief:
        sections.append("RELIEF REQUESTED: " + "; ".join(relief) + ".")

    # HEARING INFO
    hearing = analysis_data.get("hearing_info", {})
    if hearing and hearing.get("date"):
        hearing_str = f"HEARING: {hearing.get('date')}"
        if hearing.get("time"):
            hearing_str += f" at {hearing.get('time')}"
        if hearing.get("location"):
            hearing_str += f" in {hearing.get('location')}"
        if hearing.get("purpose"):
            hearing_str += f" - Purpose: {hearing.get('purpose')}"
        sections.append(hearing_str + ".")

    # LEGAL CLAIMS & CITED AUTHORITY
    legal_claims = analysis_data.get("legal_claims_and_defenses", analysis_data.get("legal_claims", []))
    if legal_claims:
        sections.append("LEGAL CLAIMS: " + "; ".join(legal_claims[:5]) + ".")

    cited_authority = analysis_data.get("cited_authority", [])
    if cited_authority:
        sections.append("CITED AUTHORITY: " + "; ".join(cited_authority[:8]) + ".")

    # PLAIN ENGLISH SUMMARY at the end for context
    plain_english = analysis_data.get("plain_english_summary", "")
    if plain_english:
        sections.append(f"IN PLAIN ENGLISH: {plain_english}")

    # Combine all sections
    comprehensive_summary = "\n\n".join(sections)

    # If we somehow have nothing, fall back to original summary
    if not comprehensive_summary.strip():
        comprehensive_summary = analysis_data.get("summary", "Document analysis completed.")

    return comprehensive_summary


def enhance_analysis_with_comprehensive_summary(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Take existing analysis data and replace the summary with a comprehensive one
    """
    comprehensive_summary = build_comprehensive_summary(analysis_data)
    analysis_data["summary"] = comprehensive_summary
    analysis_data["original_summary"] = analysis_data.get("summary", "")  # Preserve original
    return analysis_data
