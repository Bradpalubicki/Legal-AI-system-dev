"""
State Court Information API Endpoints

Provides information about state court coverage and limitations.
"""

from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel

from app.services.state_court_info_service import state_court_service

router = APIRouter(prefix="/state-courts", tags=["State Court Information"])


class StateInfoResponse(BaseModel):
    """Response model for state court information."""
    state: str
    trial_court_available: bool
    appellate_opinions_available: bool
    official_portal: Optional[str]
    portal_name: Optional[str]
    api_available: bool
    free_search: Optional[bool]
    notes: Optional[str]
    subscription_cost: Optional[str]


class LimitationExplanationResponse(BaseModel):
    """Response model for limitation explanations."""
    state: str
    explanation: str
    portal_url: Optional[str]


class SearchGuidanceResponse(BaseModel):
    """Response model for search guidance."""
    has_guidance: bool
    message: Optional[str]


class CourtTypeExplanationResponse(BaseModel):
    """Response model for court type explanation."""
    explanation: str


@router.get("/info/{state}")
async def get_state_info(state: str) -> dict:
    """
    Get court coverage information for a specific state.

    Args:
        state: State name or abbreviation (e.g., "Wisconsin", "WI")

    Returns:
        State court information including portal URLs and availability
    """
    info = state_court_service.get_state_info(state)
    if info:
        return {
            "found": True,
            "state": state,
            "data": info
        }
    return {
        "found": False,
        "state": state,
        "message": f"No specific information available for {state}. State trial courts are generally not available through our system."
    }


@router.get("/explanation/{state}")
async def get_limitation_explanation(state: str) -> LimitationExplanationResponse:
    """
    Get a user-friendly explanation of why state court cases aren't available.

    Args:
        state: State name or abbreviation

    Returns:
        Explanation with portal URL
    """
    explanation = state_court_service.get_limitation_explanation(state)
    portal_url = state_court_service.get_portal_url(state)

    return LimitationExplanationResponse(
        state=state,
        explanation=explanation,
        portal_url=portal_url
    )


@router.get("/portal/{state}")
async def get_portal_url(state: str) -> dict:
    """
    Get the official court portal URL for a state.

    Args:
        state: State name or abbreviation

    Returns:
        Portal URL and name
    """
    info = state_court_service.get_state_info(state)
    if info:
        return {
            "found": True,
            "state": state,
            "portal_url": info.get("official_portal"),
            "portal_name": info.get("portal_name"),
            "free_search": info.get("free_search", False)
        }
    return {
        "found": False,
        "state": state,
        "message": "Portal information not available. Please search for your state's official court website."
    }


@router.get("/search-guidance")
async def get_search_guidance(
    query: str = Query(..., description="The search query used"),
    results_count: int = Query(0, description="Number of results returned"),
    court_type: Optional[str] = Query(None, description="Court type filter used")
) -> SearchGuidanceResponse:
    """
    Get guidance when search returns no/few results.

    Helps users understand if they might be looking for state court cases.
    """
    guidance = state_court_service.search_guidance(query, results_count, court_type)

    return SearchGuidanceResponse(
        has_guidance=guidance is not None,
        message=guidance
    )


@router.get("/court-types")
async def get_court_type_explanation() -> CourtTypeExplanationResponse:
    """
    Get explanation of the difference between federal and state courts.
    """
    return CourtTypeExplanationResponse(
        explanation=state_court_service.get_court_type_explanation()
    )


@router.get("/free-search-states")
async def get_free_search_states() -> dict:
    """
    Get list of states that offer free online case search.

    Returns:
        List of states with free search and their portal URLs
    """
    states = state_court_service.get_states_with_free_search()
    return {
        "count": len(states),
        "states": states,
        "note": "These states offer free online case search, but still require manual web searches. No API access."
    }


@router.get("/api-available-states")
async def get_api_available_states() -> dict:
    """
    Get list of states that offer API access (even if paid).

    Returns:
        List of states with API availability and costs
    """
    states = state_court_service.get_states_with_api()
    return {
        "count": len(states),
        "states": states,
        "note": "Very few states offer programmatic API access. Most require expensive subscriptions."
    }


@router.get("/summary")
async def get_coverage_summary() -> dict:
    """
    Get a summary of our court coverage capabilities.
    """
    return {
        "federal_courts": {
            "available": True,
            "source": "CourtListener/RECAP",
            "cost": "Free",
            "includes": [
                "All U.S. District Courts",
                "All U.S. Bankruptcy Courts",
                "All U.S. Circuit Courts of Appeals",
                "U.S. Supreme Court"
            ]
        },
        "state_courts": {
            "trial_courts_available": False,
            "appellate_opinions_available": True,
            "reason": "State trial courts do not provide public APIs. Most prohibit automated access or require expensive subscriptions ($2,250-$12,500+/year).",
            "user_action": "Users must search their state's official court website directly."
        },
        "common_misconceptions": [
            {
                "misconception": "All court records are searchable through PACER",
                "reality": "PACER only covers federal courts. State courts have separate systems."
            },
            {
                "misconception": "Foreclosures are in bankruptcy court",
                "reality": "Most foreclosures are in state court (usually Circuit or Superior Court). Only bankruptcies with foreclosure proceedings are in federal bankruptcy court."
            },
            {
                "misconception": "CourtListener has all court records",
                "reality": "CourtListener has federal courts and state appellate opinions. State trial court dockets are not available."
            }
        ]
    }
