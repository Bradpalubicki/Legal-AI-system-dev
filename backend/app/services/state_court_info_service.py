"""
State Court Information Service

Provides information about state court record availability and limitations
to help users understand why certain cases may not appear in search results.
"""

import json
import os
from typing import Dict, Optional, List
from pathlib import Path

class StateCourtInfoService:
    """Service for providing state court coverage information."""

    def __init__(self):
        self._data = None
        self._load_data()

    def _load_data(self):
        """Load state court coverage data from JSON file."""
        data_path = Path(__file__).parent.parent / "data" / "state_court_coverage.json"
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        except FileNotFoundError:
            # Fallback to basic data if file not found
            self._data = self._get_fallback_data()

    def _get_fallback_data(self) -> Dict:
        """Fallback data if JSON file is not available."""
        return {
            "state_court_summary": {
                "general_limitation": "State trial courts are not available through our current integration. "
                                      "CourtListener only provides federal courts and state appellate opinions."
            },
            "states": {}
        }

    def get_state_info(self, state_name: str) -> Optional[Dict]:
        """
        Get court coverage information for a specific state.

        Args:
            state_name: State name (e.g., "Wisconsin", "wisconsin", "WI")

        Returns:
            Dictionary with state court information, or None if not found
        """
        # Normalize state name
        state_key = self._normalize_state_name(state_name)

        if state_key and state_key in self._data.get("states", {}):
            return self._data["states"][state_key]
        return None

    def _normalize_state_name(self, state_name: str) -> Optional[str]:
        """Convert state name to lowercase key format."""
        if not state_name:
            return None

        state_name = state_name.strip().lower()

        # Handle state abbreviations
        abbreviations = {
            "al": "alabama", "ak": "alaska", "az": "arizona", "ar": "arkansas",
            "ca": "california", "co": "colorado", "ct": "connecticut", "de": "delaware",
            "fl": "florida", "ga": "georgia", "hi": "hawaii", "id": "idaho",
            "il": "illinois", "in": "indiana", "ia": "iowa", "ks": "kansas",
            "ky": "kentucky", "la": "louisiana", "me": "maine", "md": "maryland",
            "ma": "massachusetts", "mi": "michigan", "mn": "minnesota", "ms": "mississippi",
            "mo": "missouri", "mt": "montana", "ne": "nebraska", "nv": "nevada",
            "nh": "new_hampshire", "nj": "new_jersey", "nm": "new_mexico", "ny": "new_york",
            "nc": "north_carolina", "nd": "north_dakota", "oh": "ohio", "ok": "oklahoma",
            "or": "oregon", "pa": "pennsylvania", "ri": "rhode_island", "sc": "south_carolina",
            "sd": "south_dakota", "tn": "tennessee", "tx": "texas", "ut": "utah",
            "vt": "vermont", "va": "virginia", "wa": "washington", "wv": "west_virginia",
            "wi": "wisconsin", "wy": "wyoming", "dc": "district_of_columbia"
        }

        if state_name in abbreviations:
            return abbreviations[state_name]

        # Handle full names with spaces
        state_name = state_name.replace(" ", "_")

        # Handle common variations
        variations = {
            "new hampshire": "new_hampshire",
            "new jersey": "new_jersey",
            "new mexico": "new_mexico",
            "new york": "new_york",
            "north carolina": "north_carolina",
            "north dakota": "north_dakota",
            "rhode island": "rhode_island",
            "south carolina": "south_carolina",
            "south dakota": "south_dakota",
            "west virginia": "west_virginia",
            "washington dc": "district_of_columbia",
            "washington d.c.": "district_of_columbia",
            "d.c.": "district_of_columbia",
        }

        clean_name = state_name.replace("_", " ")
        if clean_name in variations:
            return variations[clean_name]

        return state_name

    def get_portal_url(self, state_name: str) -> Optional[str]:
        """Get the official court portal URL for a state."""
        state_info = self.get_state_info(state_name)
        if state_info:
            return state_info.get("official_portal")
        return None

    def get_limitation_explanation(self, state_name: str) -> str:
        """
        Get a user-friendly explanation of why state court cases aren't available.

        Args:
            state_name: State name or abbreviation

        Returns:
            Explanation string with portal URL if available
        """
        state_info = self.get_state_info(state_name)

        if not state_info:
            return self._get_generic_explanation()

        state_key = self._normalize_state_name(state_name)
        display_name = state_key.replace("_", " ").title() if state_key else state_name

        portal_url = state_info.get("official_portal", "their state court website")
        portal_name = state_info.get("portal_name", "the state court system")
        notes = state_info.get("notes", "")

        explanation = f"""State trial court records from {display_name} are not available through our PACER/CourtListener search. Our system searches federal courts and state appellate opinions only.

**To find {display_name} state court cases:**
- Official Portal: {portal_url}
- System Name: {portal_name}

{notes}

This limitation exists because most state court systems do not provide public APIs for programmatic access."""

        return explanation

    def _get_generic_explanation(self) -> str:
        """Get generic explanation when state is not found."""
        return """State trial court records are not available through our PACER/CourtListener search. Our system searches federal courts and state appellate opinions only.

To find state court cases, please visit your state's official court website. Each state maintains its own case management system.

This limitation exists because most state court systems do not provide public APIs for programmatic access."""

    def get_recommended_response(self, response_type: str, **kwargs) -> str:
        """
        Get a pre-written response for common scenarios.

        Args:
            response_type: Type of response (e.g., "state_case_not_found", "wisconsin_specific")
            **kwargs: Variables to substitute in the response (e.g., state, portal_url)

        Returns:
            Formatted response string
        """
        responses = self._data.get("recommended_responses", {})
        response = responses.get(response_type, "")

        if response and kwargs:
            try:
                response = response.format(**kwargs)
            except KeyError:
                pass  # Return unformatted if kwargs don't match

        return response

    def get_states_with_free_search(self) -> List[Dict]:
        """Get list of states that offer free online case search."""
        free_states = []
        for state_key, state_info in self._data.get("states", {}).items():
            if state_info.get("free_search"):
                free_states.append({
                    "state": state_key.replace("_", " ").title(),
                    "portal": state_info.get("official_portal"),
                    "portal_name": state_info.get("portal_name"),
                    "free_documents": state_info.get("free_documents", False)
                })
        return free_states

    def get_states_with_api(self) -> List[Dict]:
        """Get list of states that offer API access (even if paid)."""
        api_states = []
        for state_key, state_info in self._data.get("states", {}).items():
            if state_info.get("api_available"):
                api_states.append({
                    "state": state_key.replace("_", " ").title(),
                    "api_cost": state_info.get("api_cost", "Unknown"),
                    "notes": state_info.get("notes", "")
                })
        return api_states

    def search_guidance(self, query: str, results_count: int, court_type: str = None) -> Optional[str]:
        """
        Provide guidance when search returns no/few results.

        Args:
            query: The search query used
            results_count: Number of results returned
            court_type: Type of court filter used (bankruptcy, district, circuit, or None for all)

        Returns:
            Guidance message if applicable, None otherwise
        """
        if results_count > 0:
            return None

        # Check if the query might be looking for state court cases
        state_indicators = [
            "foreclosure", "divorce", "custody", "probate", "eviction",
            "small claims", "traffic", "misdemeanor", "landlord", "tenant",
            "circuit court", "superior court", "county court", "state court"
        ]

        query_lower = query.lower()
        is_likely_state_case = any(indicator in query_lower for indicator in state_indicators)

        if is_likely_state_case:
            return """**No results found.**

This search may be looking for a **state court case**. Our PACER search only covers **federal courts** (bankruptcy, district, and circuit courts of appeals).

Common state court cases NOT in our system:
- Foreclosures (unless federal diversity jurisdiction)
- Divorces and custody cases
- Evictions and landlord-tenant disputes
- Traffic violations
- Most misdemeanors and local ordinance violations
- Probate matters
- Small claims

**To find state court records**, please search your state's official court website directly. Visit the PACER Search tab and select your state for a link to the appropriate state court portal."""

        return """**No results found.**

If you're looking for a case and it's not appearing:
1. **Federal courts**: Try different search terms or date ranges
2. **State courts**: Our system only searches federal courts. State trial court cases (foreclosures, divorces, evictions, etc.) require searching the state's official court website.

Our CourtListener integration provides free access to federal court records only."""

    def get_court_type_explanation(self) -> str:
        """Explain the difference between court types."""
        return """**Federal vs State Courts:**

**FEDERAL COURTS** (Searchable in our system):
- U.S. District Courts - Federal civil/criminal cases
- U.S. Bankruptcy Courts - All bankruptcy cases
- U.S. Circuit Courts of Appeals - Federal appeals
- U.S. Supreme Court

**STATE COURTS** (NOT in our system):
- State Supreme Courts - Only opinions available, not dockets
- State Circuit/Superior Courts - NOT available
- County Courts - NOT available
- Municipal Courts - NOT available

**Common case types by court:**
- Bankruptcies → Federal (searchable here)
- Federal crimes → Federal (searchable here)
- Patent/trademark → Federal (searchable here)
- Foreclosures → Usually State (search state website)
- Divorces → State (search state website)
- Traffic tickets → State/Municipal (search state website)
- Most civil lawsuits → State (search state website)"""


# Singleton instance for easy import
state_court_service = StateCourtInfoService()
