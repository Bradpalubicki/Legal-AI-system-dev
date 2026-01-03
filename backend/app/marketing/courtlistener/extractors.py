"""
Contact Extractors

Extract structured contact information from CourtListener API responses.
Handles parsing of raw attorney contact strings and party information.
"""

import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from app.marketing.contacts.models import ContactType

logger = logging.getLogger(__name__)


@dataclass
class ExtractedContact:
    """Structured contact extracted from CourtListener data"""
    email: Optional[str]
    full_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    firm_name: Optional[str]
    phone: Optional[str]
    fax: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    contact_type: ContactType
    role: str
    raw_data: Dict[str, Any]
    courtlistener_attorney_id: Optional[int] = None
    courtlistener_party_id: Optional[int] = None


class ContactExtractor:
    """
    Extract structured contact information from CourtListener API responses.

    CourtListener returns attorney contact as a raw string like:
    "Federal Defenders of New York\nOne Pierrepont Plaza\n16th Floor\n
     Brooklyn, NY 11201\n718-330-1257\nFax: 718-855-0760\nEmail: attorney@fd.org"
    """

    # Regex patterns for parsing contact strings
    EMAIL_PATTERN = re.compile(r'[Ee]mail:\s*([^\s\n]+@[^\s\n]+)')
    EMAIL_BARE_PATTERN = re.compile(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b')
    PHONE_PATTERN = re.compile(r'(?:Tel(?:ephone)?:?\s*)?(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})')
    FAX_PATTERN = re.compile(r'[Ff]ax:?\s*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})')
    ZIP_PATTERN = re.compile(r'\b(\d{5}(?:-\d{4})?)\b')
    STATE_PATTERN = re.compile(r',?\s*([A-Z]{2})\s+\d{5}')

    # US States for validation
    US_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
    }

    # Business name indicators
    BUSINESS_INDICATORS = [
        'inc', 'llc', 'corp', 'ltd', 'company', 'co.', 'associates',
        'group', 'partners', 'bank', 'insurance', 'holdings', 'industries',
        'services', 'solutions', 'enterprises', 'international', 'foundation',
        'association', 'corporation', 'limited', 'l.l.c.', 'p.c.', 'p.a.',
        'llp', 'l.l.p.', 'pllc', 'p.l.l.c.'
    ]

    def extract_from_attorney(
        self,
        attorney_data: Dict[str, Any],
        docket_data: Optional[Dict[str, Any]] = None
    ) -> Optional[ExtractedContact]:
        """
        Extract contact from CourtListener attorney object.

        attorney_data format:
        {
            "id": 12345,
            "name": "John Smith",
            "contact_raw_text": "Smith & Associates\n123 Main St\nNew York, NY 10001\n212-555-1234\nEmail: jsmith@firm.com",
            "roles": ["Lead Attorney", "Attorney to be Noticed"],
            "organizations": [{"name": "Smith & Associates", ...}]
        }

        Args:
            attorney_data: Attorney record from CourtListener API
            docket_data: Optional docket context

        Returns:
            ExtractedContact or None if invalid
        """
        if not attorney_data:
            return None

        # Try different field names for contact info
        contact_string = (
            attorney_data.get("contact_raw_text") or
            attorney_data.get("contact") or
            ""
        )
        name = attorney_data.get("name", "")

        if not name:
            return None

        # Parse the raw contact string
        parsed = self._parse_contact_string(contact_string)

        # Extract name parts
        first_name, last_name = self._split_name(name)

        # Get firm name from organizations if available
        firm_name = parsed.get("firm_name")
        orgs = attorney_data.get("organizations") or []
        if not firm_name and orgs:
            firm_name = orgs[0].get("name") if isinstance(orgs[0], dict) else str(orgs[0])

        # Build role string from roles list
        roles = attorney_data.get("roles", [])
        if isinstance(roles, list):
            role = ", ".join(str(r) for r in roles) if roles else "Attorney"
        else:
            role = str(roles) if roles else "Attorney"

        return ExtractedContact(
            email=parsed.get("email"),
            full_name=name,
            first_name=first_name,
            last_name=last_name,
            firm_name=firm_name,
            phone=parsed.get("phone"),
            fax=parsed.get("fax"),
            address_line1=parsed.get("address_line1"),
            address_line2=parsed.get("address_line2"),
            city=parsed.get("city"),
            state=parsed.get("state"),
            zip_code=parsed.get("zip_code"),
            contact_type=ContactType.ATTORNEY,
            role=role,
            raw_data=attorney_data,
            courtlistener_attorney_id=attorney_data.get("id")
        )

    def extract_from_party(
        self,
        party_data: Dict[str, Any],
        docket_data: Optional[Dict[str, Any]] = None
    ) -> Optional[ExtractedContact]:
        """
        Extract contact from CourtListener party object.

        Parties may be individuals or businesses. Usually don't have
        email in CourtListener, but useful for tracking and potential
        enrichment.

        Args:
            party_data: Party record from CourtListener API
            docket_data: Optional docket context

        Returns:
            ExtractedContact or None if invalid
        """
        if not party_data:
            return None

        name = party_data.get("name", "")
        extra_info = party_data.get("extra_info", "")

        if not name:
            return None

        # Determine if business or individual
        is_business = self._is_business_name(name)
        contact_type = ContactType.PARTY_BUSINESS if is_business else ContactType.PARTY_INDIVIDUAL

        # Get party type (plaintiff, defendant, etc.)
        party_types = party_data.get("party_types", [])
        if party_types and isinstance(party_types, list):
            if isinstance(party_types[0], dict):
                role = party_types[0].get("name", "Party")
            else:
                role = str(party_types[0])
        else:
            role = "Party"

        first_name = None
        last_name = None
        if not is_business:
            first_name, last_name = self._split_name(name)

        return ExtractedContact(
            email=None,  # Parties typically don't have email in CourtListener
            full_name=name,
            first_name=first_name,
            last_name=last_name,
            firm_name=name if is_business else None,
            phone=None,
            fax=None,
            address_line1=None,
            address_line2=None,
            city=None,
            state=None,
            zip_code=None,
            contact_type=contact_type,
            role=role,
            raw_data=party_data,
            courtlistener_party_id=party_data.get("id")
        )

    def extract_all_from_docket(
        self,
        docket_data: Dict[str, Any],
        attorneys: List[Dict[str, Any]],
        parties: Optional[List[Dict[str, Any]]] = None
    ) -> List[ExtractedContact]:
        """
        Extract all contacts from a docket and its related data.

        Args:
            docket_data: Docket record from CourtListener
            attorneys: List of attorney records
            parties: Optional list of party records

        Returns:
            List of extracted contacts
        """
        contacts = []

        # Extract from attorneys
        for attorney in attorneys:
            contact = self.extract_from_attorney(attorney, docket_data)
            if contact:
                contacts.append(contact)

        # Extract from parties
        if parties:
            for party in parties:
                contact = self.extract_from_party(party, docket_data)
                if contact:
                    contacts.append(contact)

        return contacts

    def _parse_contact_string(self, contact_str: str) -> Dict[str, Optional[str]]:
        """
        Parse raw contact string into structured fields.

        Args:
            contact_str: Raw contact string from CourtListener

        Returns:
            Dictionary of parsed contact fields
        """
        result = {
            "email": None,
            "phone": None,
            "fax": None,
            "firm_name": None,
            "address_line1": None,
            "address_line2": None,
            "city": None,
            "state": None,
            "zip_code": None
        }

        if not contact_str:
            return result

        # Split into lines
        lines = [l.strip() for l in contact_str.split('\n') if l.strip()]

        # Extract email (try labeled first, then bare)
        email_match = self.EMAIL_PATTERN.search(contact_str)
        if email_match:
            result["email"] = email_match.group(1).lower().strip()
        else:
            bare_match = self.EMAIL_BARE_PATTERN.search(contact_str)
            if bare_match:
                result["email"] = bare_match.group(1).lower().strip()

        # Validate email format
        if result["email"] and not self._is_valid_email(result["email"]):
            result["email"] = None

        # Extract fax (before phone to avoid confusion)
        fax_match = self.FAX_PATTERN.search(contact_str)
        if fax_match:
            result["fax"] = self._normalize_phone(fax_match.group(1))

        # Extract phone (excluding fax number)
        contact_without_fax = self.FAX_PATTERN.sub('', contact_str)
        phone_match = self.PHONE_PATTERN.search(contact_without_fax)
        if phone_match:
            result["phone"] = self._normalize_phone(phone_match.group(1))

        # Extract zip and state
        zip_match = self.ZIP_PATTERN.search(contact_str)
        if zip_match:
            result["zip_code"] = zip_match.group(1)

        state_match = self.STATE_PATTERN.search(contact_str)
        if state_match and state_match.group(1) in self.US_STATES:
            result["state"] = state_match.group(1)

        # Parse address lines (heuristic approach)
        self._parse_address_lines(lines, result)

        return result

    def _parse_address_lines(
        self,
        lines: List[str],
        result: Dict[str, Optional[str]]
    ) -> None:
        """
        Parse address lines from contact string.

        Modifies result dict in place.
        """
        address_lines = []

        for line in lines:
            # Skip lines that are clearly not address
            if any(x in line.lower() for x in ['email:', 'fax:', '@', 'telephone:', 'tel:']):
                continue
            if self.PHONE_PATTERN.match(line):
                continue
            address_lines.append(line)

        if address_lines:
            # First line is usually firm name
            result["firm_name"] = address_lines[0]

            if len(address_lines) > 1:
                # Look for city, state zip line
                for i, line in enumerate(address_lines[1:], 1):
                    if result["zip_code"] and result["zip_code"] in line:
                        # This is the city/state/zip line
                        city_match = re.match(r'^([^,]+),?\s*[A-Z]{2}\s*\d{5}', line)
                        if city_match:
                            result["city"] = city_match.group(1).strip().rstrip(',')

                        # Previous lines are address
                        if i > 1:
                            result["address_line1"] = address_lines[1]
                        if i > 2:
                            result["address_line2"] = address_lines[2]
                        break
                else:
                    # No city/state/zip line found, treat as address
                    if len(address_lines) > 1:
                        result["address_line1"] = address_lines[1]
                    if len(address_lines) > 2:
                        result["address_line2"] = address_lines[2]

    def _split_name(self, full_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Split full name into first and last name.

        Args:
            full_name: Full name string

        Returns:
            Tuple of (first_name, last_name)
        """
        if not full_name:
            return None, None

        # Remove common suffixes
        clean_name = re.sub(r',?\s*(Jr\.?|Sr\.?|II|III|IV|Esq\.?)$', '', full_name.strip())

        parts = clean_name.split()
        if len(parts) >= 2:
            return parts[0], " ".join(parts[1:])
        elif len(parts) == 1:
            return parts[0], None
        return None, None

    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to consistent format.

        Args:
            phone: Raw phone number string

        Returns:
            Formatted phone number
        """
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        return phone

    def _is_business_name(self, name: str) -> bool:
        """
        Determine if name is a business entity.

        Args:
            name: Name to check

        Returns:
            True if appears to be a business name
        """
        name_lower = name.lower()
        return any(ind in name_lower for ind in self.BUSINESS_INDICATORS)

    def _is_valid_email(self, email: str) -> bool:
        """
        Basic email validation.

        Args:
            email: Email address to validate

        Returns:
            True if email format is valid
        """
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
