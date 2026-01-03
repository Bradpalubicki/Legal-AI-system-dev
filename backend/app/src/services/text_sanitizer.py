"""
Text sanitization utilities for AI API calls.
Removes control characters that break JSON parsing.
"""

import re


def sanitize_text_for_ai(text: str) -> str:
    """
    Sanitize document text before sending to AI APIs.
    Removes control characters that break JSON parsing.

    Args:
        text: Raw document text that may contain control characters

    Returns:
        Cleaned text safe for JSON encoding and AI API calls
    """
    if not text:
        return text

    # Remove null bytes
    text = text.replace('\x00', '')

    # Normalize line endings (CRLF -> LF)
    text = text.replace('\r\n', '\n')
    text = text.replace('\r', '\n')

    # Convert tabs to spaces
    text = text.replace('\t', '    ')

    # Remove other control characters (except newline 0x0A)
    # Control chars are 0x00-0x1F and 0x7F-0x9F
    text = re.sub(r'[\x00-\x09\x0b-\x1f\x7f-\x9f]', '', text)

    # Remove any remaining problematic unicode characters
    text = text.encode('utf-8', errors='ignore').decode('utf-8')

    return text
