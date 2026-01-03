"""
PACER-standard document naming utility.

Generates standardized filenames for court documents following PACER conventions:
[Court]_[Case#]_[Doc#]_[Description]_[Date].pdf

Example: ilnb_2024-bk-12345_0001_Petition_20240315.pdf
"""

import re
from datetime import datetime
from typing import Optional


def sanitize_filename(text: str, max_length: int = 50) -> str:
    """
    Sanitize text for use in a filename.
    Removes illegal characters and normalizes spaces.

    Args:
        text: The text to sanitize
        max_length: Maximum length for the sanitized text

    Returns:
        A filesystem-safe string
    """
    if not text:
        return ""

    # Replace common problematic patterns
    text = text.strip()

    # Remove or replace illegal filename characters
    # Windows: \ / : * ? " < > |
    # Also remove other potentially problematic characters
    illegal_chars = r'[\\/:*?"<>|#%&{}$!\'\`\[\]@^+=~]'
    text = re.sub(illegal_chars, '', text)

    # Replace multiple spaces/underscores with single underscore
    text = re.sub(r'[\s_]+', '_', text)

    # Remove leading/trailing underscores and dots
    text = text.strip('_.')

    # Truncate to max length, but try to break at word boundary
    if len(text) > max_length:
        # Try to break at underscore
        truncated = text[:max_length]
        last_underscore = truncated.rfind('_')
        if last_underscore > max_length // 2:
            text = truncated[:last_underscore]
        else:
            text = truncated

    return text


def generate_pacer_filename(
    case_number: Optional[str] = None,
    document_number: Optional[int] = None,
    description: Optional[str] = None,
    filing_date: Optional[str] = None,
    court: Optional[str] = None,
    document_id: Optional[int] = None,
    extension: str = "pdf"
) -> str:
    """
    Generate a PACER-standard filename for a court document.

    Format: [Court]_[Case#]_[Doc#]_[Description]_[Date].[ext]
    Example: ilnb_2024-bk-12345_0001_Petition_20240315.pdf

    Args:
        case_number: The case number (e.g., "2024-bk-12345")
        document_number: The document entry number (e.g., 1, 23, 456)
        description: Brief description of the document
        filing_date: Date filed (various formats accepted, will be normalized)
        court: Court code (e.g., "ilnb", "cacd")
        document_id: CourtListener/RECAP document ID (fallback identifier)
        extension: File extension (default: "pdf")

    Returns:
        A standardized, filesystem-safe filename
    """
    parts = []

    # 1. Court code (if available)
    if court:
        court_clean = sanitize_filename(court.lower(), max_length=10)
        if court_clean:
            parts.append(court_clean)

    # 2. Case number (sanitized)
    if case_number:
        # Normalize case number format
        case_clean = sanitize_filename(case_number, max_length=30)
        if case_clean:
            parts.append(case_clean)

    # 3. Document number (zero-padded)
    if document_number is not None:
        doc_num = str(document_number).zfill(4)  # Zero-pad to 4 digits
        parts.append(doc_num)
    elif document_id is not None:
        # Use document_id as fallback
        parts.append(f"doc{document_id}")

    # 4. Description (sanitized and truncated)
    if description:
        desc_clean = sanitize_filename(description, max_length=40)
        if desc_clean:
            parts.append(desc_clean)

    # 5. Filing date (normalized to YYYYMMDD)
    if filing_date:
        date_str = normalize_date(filing_date)
        if date_str:
            parts.append(date_str)

    # Combine parts with underscore
    if parts:
        filename = "_".join(parts)
    else:
        # Fallback if no useful parts
        filename = f"court_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Add extension
    extension = extension.lstrip('.')
    return f"{filename}.{extension}"


def normalize_date(date_input: Optional[str]) -> Optional[str]:
    """
    Normalize various date formats to YYYYMMDD for filenames.

    Accepts formats like:
    - 2024-03-15
    - 03/15/2024
    - March 15, 2024
    - 2024-03-15T12:00:00Z

    Returns:
        Date string in YYYYMMDD format, or None if parsing fails
    """
    if not date_input:
        return None

    # Already in target format
    if re.match(r'^\d{8}$', date_input):
        return date_input

    # Common date patterns
    patterns = [
        # ISO format: 2024-03-15 or 2024-03-15T12:00:00
        (r'(\d{4})-(\d{2})-(\d{2})', lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}"),
        # US format: 03/15/2024 or 03-15-2024
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', lambda m: f"{m.group(3)}{m.group(1).zfill(2)}{m.group(2).zfill(2)}"),
        # Compact: 20240315
        (r'^(\d{4})(\d{2})(\d{2})$', lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}"),
    ]

    for pattern, formatter in patterns:
        match = re.search(pattern, date_input)
        if match:
            try:
                return formatter(match)
            except Exception:
                continue

    # Try parsing with datetime
    try:
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%Y%m%d"]:
            try:
                dt = datetime.strptime(date_input.strip(), fmt)
                return dt.strftime("%Y%m%d")
            except ValueError:
                continue
    except Exception:
        pass

    return None


def generate_display_name(
    case_number: Optional[str] = None,
    document_number: Optional[int] = None,
    description: Optional[str] = None,
    court: Optional[str] = None
) -> str:
    """
    Generate a human-readable display name for a document.

    Format: "[Case#] - Doc #X: Description"
    Example: "2024-bk-12345 - Doc #1: Voluntary Petition"

    Args:
        case_number: The case number
        document_number: The document entry number
        description: Brief description of the document
        court: Court name or code

    Returns:
        A formatted display name
    """
    parts = []

    if case_number:
        parts.append(case_number)

    if document_number is not None:
        parts.append(f"Doc #{document_number}")

    if description:
        desc_truncated = description[:60] + "..." if len(description) > 60 else description
        if parts:
            parts[-1] = parts[-1] + ":"
        parts.append(desc_truncated)

    if not parts:
        return "Court Document"

    # Join with " - " for first separator, then space for rest
    if len(parts) >= 2:
        result = parts[0] + " - " + " ".join(parts[1:])
    else:
        result = parts[0]

    return result


# Mapping of common document types to standardized short names
DOCUMENT_TYPE_ABBREVIATIONS = {
    "voluntary petition": "Petition",
    "involuntary petition": "InvPetition",
    "complaint": "Complaint",
    "answer": "Answer",
    "motion to dismiss": "MTD",
    "motion for summary judgment": "MSJ",
    "order": "Order",
    "judgment": "Judgment",
    "notice of appearance": "NOA",
    "proof of claim": "POC",
    "debtor's certification": "DebtorCert",
    "creditor matrix": "CreditorMatrix",
    "statement of financial affairs": "SOFA",
    "schedules": "Schedules",
    "chapter 13 plan": "Ch13Plan",
    "chapter 11 plan": "Ch11Plan",
    "disclosure statement": "DisclosureStmt",
    "adversary proceeding": "AP",
    "summons": "Summons",
    "subpoena": "Subpoena",
    "transcript": "Transcript",
    "brief": "Brief",
    "memorandum": "Memo",
    "declaration": "Declaration",
    "affidavit": "Affidavit",
    "exhibit": "Exhibit",
    "stipulation": "Stipulation",
    "settlement agreement": "Settlement",
    "minute entry": "MinuteEntry",
    "docket entry": "DocketEntry",
}


def abbreviate_document_type(description: str) -> str:
    """
    Attempt to abbreviate common document types for shorter filenames.

    Args:
        description: The document description

    Returns:
        Abbreviated version if matched, otherwise cleaned original
    """
    if not description:
        return ""

    desc_lower = description.lower().strip()

    # Check for exact or partial matches
    for full_name, abbreviation in DOCUMENT_TYPE_ABBREVIATIONS.items():
        if full_name in desc_lower:
            return abbreviation

    # Return sanitized original if no abbreviation found
    return sanitize_filename(description, max_length=30)
