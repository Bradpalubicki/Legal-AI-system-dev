"""
Referral API Router for Legal AI System

Provides endpoints for attorney referrals, legal aid connections, and 
pro bono program matching while maintaining proper disclaimers.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid

# Import referral modules
from app.src.referrals import (
    AttorneyDirectory,
    ReferralEngine,
    LegalAidConnector,
    AttorneyProfile,
    ReferralRequest,
    ReferralMatch,
    Location,
    BarAssociation,
    PracticeArea,
    CaseType,
    FeeStructure,
    BarMembershipStatus
)

# Import authentication dependencies
from app.api.deps.auth import get_current_user, get_current_user_id, get_optional_user, CurrentUser

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize referral services
attorney_directory = AttorneyDirectory()
referral_engine = ReferralEngine(attorney_directory)
legal_aid_connector = LegalAidConnector()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class LocationModel(BaseModel):
    address: str
    city: str
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str
    county: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @validator('state')
    def validate_state(cls, v):
        return v.upper()


class AttorneySearchRequest(BaseModel):
    practice_areas: List[PracticeArea] = []
    location: LocationModel
    radius_miles: float = Field(default=50, ge=1, le=500)
    fee_structures: List[FeeStructure] = []
    languages: List[str] = []
    accepting_new_clients: bool = True
    min_experience: int = Field(default=0, ge=0)
    max_hourly_rate: Optional[float] = Field(None, ge=0)
    free_consultation_only: bool = False
    max_results: int = Field(default=20, ge=1, le=100)


class ReferralRequestModel(BaseModel):
    case_type: CaseType
    practice_areas: List[PracticeArea]
    description: str = Field(..., min_length=10, max_length=2000)
    location: LocationModel
    urgency: str = Field(..., pattern="^(low|medium|high|emergency)$")
    budget_range: Optional[Tuple[float, float]] = None
    preferred_fee_structure: List[FeeStructure] = []
    preferred_languages: List[str] = []
    special_requirements: List[str] = []

    # Client information
    client_name: str = Field(..., min_length=2, max_length=100)
    client_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    client_phone: str = Field(..., min_length=10, max_length=20)

    @validator('description')
    def validate_description(cls, v):
        # Remove potentially sensitive information patterns
        import re
        # Remove SSN patterns
        v = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED]', v)
        # Remove credit card patterns
        v = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[REDACTED]', v)
        return v


class LegalAidSearchRequest(BaseModel):
    location: LocationModel
    case_type: CaseType
    household_income: float = Field(..., ge=0)
    family_size: int = Field(..., ge=1, le=20)
    preferred_language: str = "English"
    practice_areas: List[PracticeArea] = []


class ContactRequestModel(BaseModel):
    attorney_bar_number: str
    referral_request_id: str
    message: str = Field(..., min_length=10, max_length=1000)
    preferred_contact_method: str = Field(..., pattern="^(phone|email|both)$")
    preferred_contact_time: Optional[str] = None


# Response Models
class AttorneyResponseModel(BaseModel):
    bar_number: str
    first_name: str
    last_name: str
    firm_name: Optional[str]
    email: str
    phone: str
    location: LocationModel
    practice_areas: List[PracticeArea]
    years_experience: int
    bar_memberships: Dict[str, str]
    fee_structures: List[FeeStructure]
    languages: List[str]
    website: Optional[str]
    bio: Optional[str]
    hourly_rate_min: Optional[float]
    hourly_rate_max: Optional[float]
    consultation_fee: Optional[float]
    free_consultation: bool
    accepting_new_clients: bool
    profile_completeness: float
    distance_miles: Optional[float] = None


class ReferralMatchResponseModel(BaseModel):
    attorney: AttorneyResponseModel
    match_score: float
    match_reasons: List[str]
    distance_miles: Optional[float]
    estimated_cost_range: Optional[Tuple[float, float]]
    referral_source: str


class BarAssociationResponseModel(BaseModel):
    name: str
    state: str
    website: str
    referral_phone: str
    referral_website: Optional[str]
    fee_for_referral: Optional[float]
    referral_requirements: List[str]
    languages_available: List[str]


class LegalAidResponseModel(BaseModel):
    id: str
    name: str
    state: str
    counties_served: List[str]
    phone: str
    website: str
    email: Optional[str]
    services: List[str]
    languages: List[str]
    income_guidelines: Dict[str, float]
    emergency_services: bool
    location: Optional[Dict[str, str]]
    match_reason: str


class IncomeEligibilityResponseModel(BaseModel):
    poverty_line: float
    household_income: float
    family_size: int
    legal_aid_eligible: bool
    legal_aid_limit: float
    pro_bono_eligible: bool
    pro_bono_limit: float
    reduced_fee_eligible: bool
    reduced_fee_limit: float


# =============================================================================
# ATTORNEY DIRECTORY ENDPOINTS
# =============================================================================

@router.post(
    "/attorneys/search",
    response_model=List[AttorneyResponseModel],
    summary="Search Attorney Directory",
    description="Search for attorneys based on practice areas, location, and other criteria"
)
async def search_attorneys(
    search_request: AttorneySearchRequest,
    current_user: Optional[CurrentUser] = Depends(get_optional_user)  # Optional auth for search
):
    """Search attorneys in the directory with filtering options"""
    try:
        # Convert Pydantic models to internal models
        location = Location(
            address=search_request.location.address,
            city=search_request.location.city,
            state=search_request.location.state,
            zip_code=search_request.location.zip_code,
            county=search_request.location.county,
            latitude=search_request.location.latitude,
            longitude=search_request.location.longitude
        )
        
        # Search attorneys
        attorneys = attorney_directory.search_attorneys(
            practice_areas=search_request.practice_areas,
            location=location,
            radius_miles=search_request.radius_miles,
            fee_structures=search_request.fee_structures,
            languages=search_request.languages,
            accepting_new_clients=search_request.accepting_new_clients,
            min_experience=search_request.min_experience,
            max_hourly_rate=search_request.max_hourly_rate,
            free_consultation_only=search_request.free_consultation_only
        )
        
        # Limit results
        attorneys = attorneys[:search_request.max_results]
        
        # Convert to response format
        response_attorneys = []
        for attorney in attorneys:
            # Calculate distance if possible
            distance = attorney_directory._calculate_distance(attorney.location, location)
            
            response_attorney = AttorneyResponseModel(
                bar_number=attorney.bar_number,
                first_name=attorney.first_name,
                last_name=attorney.last_name,
                firm_name=attorney.firm_name,
                email=attorney.email,
                phone=attorney.phone,
                location=LocationModel(
                    address=attorney.location.address,
                    city=attorney.location.city,
                    state=attorney.location.state,
                    zip_code=attorney.location.zip_code,
                    county=attorney.location.county,
                    latitude=attorney.location.latitude,
                    longitude=attorney.location.longitude
                ),
                practice_areas=attorney.practice_areas,
                years_experience=attorney.years_experience,
                bar_memberships={k: v.value for k, v in attorney.bar_memberships.items()},
                fee_structures=attorney.fee_structures,
                languages=attorney.languages,
                website=attorney.website,
                bio=attorney.bio,
                hourly_rate_min=attorney.hourly_rate_min,
                hourly_rate_max=attorney.hourly_rate_max,
                consultation_fee=attorney.consultation_fee,
                free_consultation=attorney.free_consultation,
                accepting_new_clients=attorney.accepting_new_clients,
                profile_completeness=attorney.profile_completeness,
                distance_miles=distance if distance != float('inf') else None
            )
            
            response_attorneys.append(response_attorney)
        
        logger.info(f"Found {len(response_attorneys)} attorneys matching search criteria")
        return response_attorneys
        
    except Exception as e:
        logger.error(f"Error searching attorneys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching attorney directory"
        )


@router.get(
    "/attorneys/{bar_number}",
    response_model=AttorneyResponseModel,
    summary="Get Attorney Profile",
    description="Retrieve detailed information about a specific attorney"
)
async def get_attorney_profile(
    bar_number: str = Path(..., description="Attorney's bar number"),
    current_user: Optional[CurrentUser] = Depends(get_optional_user)  # Optional auth for viewing
):
    """Get detailed attorney profile by bar number"""
    try:
        attorney = attorney_directory._attorneys.get(bar_number)
        
        if not attorney:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attorney with bar number '{bar_number}' not found"
            )
        
        response_attorney = AttorneyResponseModel(
            bar_number=attorney.bar_number,
            first_name=attorney.first_name,
            last_name=attorney.last_name,
            firm_name=attorney.firm_name,
            email=attorney.email,
            phone=attorney.phone,
            location=LocationModel(
                address=attorney.location.address,
                city=attorney.location.city,
                state=attorney.location.state,
                zip_code=attorney.location.zip_code,
                county=attorney.location.county,
                latitude=attorney.location.latitude,
                longitude=attorney.location.longitude
            ),
            practice_areas=attorney.practice_areas,
            years_experience=attorney.years_experience,
            bar_memberships={k: v.value for k, v in attorney.bar_memberships.items()},
            fee_structures=attorney.fee_structures,
            languages=attorney.languages,
            website=attorney.website,
            bio=attorney.bio,
            hourly_rate_min=attorney.hourly_rate_min,
            hourly_rate_max=attorney.hourly_rate_max,
            consultation_fee=attorney.consultation_fee,
            free_consultation=attorney.free_consultation,
            accepting_new_clients=attorney.accepting_new_clients,
            profile_completeness=attorney.profile_completeness
        )
        
        logger.info(f"Retrieved attorney profile for bar number: {bar_number}")
        return response_attorney
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving attorney profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving attorney profile"
        )


@router.get(
    "/attorneys/{bar_number}/verify",
    summary="Verify Attorney Bar Status",
    description="Verify an attorney's bar membership status"
)
async def verify_attorney_status(
    bar_number: str = Path(..., description="Attorney's bar number"),
    state: str = Query(..., description="State bar to verify against", min_length=2, max_length=2)
):
    """Verify attorney's bar membership status"""
    try:
        verification_result = attorney_directory.verify_attorney_bar_status(
            bar_number, 
            state.upper()
        )
        
        logger.info(f"Verified bar status for {bar_number} in {state}")
        return verification_result
        
    except Exception as e:
        logger.error(f"Error verifying attorney bar status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying attorney bar status"
        )


# =============================================================================
# REFERRAL ENGINE ENDPOINTS
# =============================================================================

@router.post(
    "/referrals/match",
    response_model=List[ReferralMatchResponseModel],
    summary="Find Attorney Matches",
    description="Find attorney matches for a specific referral request using intelligent matching"
)
async def find_attorney_matches(
    referral_request: ReferralRequestModel,
    max_results: int = Query(default=10, ge=1, le=25, description="Maximum number of matches to return"),
    require_conflict_check: bool = Query(default=True, description="Whether to perform conflict checking")
):
    """Find attorney matches for a referral request"""
    try:
        # Convert to internal models
        location = Location(
            address=referral_request.location.address,
            city=referral_request.location.city,
            state=referral_request.location.state,
            zip_code=referral_request.location.zip_code,
            county=referral_request.location.county,
            latitude=referral_request.location.latitude,
            longitude=referral_request.location.longitude
        )
        
        request_obj = ReferralRequest(
            id=str(uuid.uuid4()),
            case_type=referral_request.case_type,
            practice_areas=referral_request.practice_areas,
            description=referral_request.description,
            location=location,
            urgency=referral_request.urgency,
            budget_range=referral_request.budget_range,
            preferred_fee_structure=referral_request.preferred_fee_structure,
            preferred_languages=referral_request.preferred_languages,
            special_requirements=referral_request.special_requirements,
            client_name=referral_request.client_name,
            client_email=referral_request.client_email,
            client_phone=referral_request.client_phone
        )
        
        # Find matches
        matches = referral_engine.find_matches(
            request_obj,
            max_results=max_results,
            require_conflict_check=require_conflict_check
        )
        
        # Convert to response format
        response_matches = []
        for match in matches:
            attorney_response = AttorneyResponseModel(
                bar_number=match.attorney.bar_number,
                first_name=match.attorney.first_name,
                last_name=match.attorney.last_name,
                firm_name=match.attorney.firm_name,
                email=match.attorney.email,
                phone=match.attorney.phone,
                location=LocationModel(
                    address=match.attorney.location.address,
                    city=match.attorney.location.city,
                    state=match.attorney.location.state,
                    zip_code=match.attorney.location.zip_code,
                    county=match.attorney.location.county,
                    latitude=match.attorney.location.latitude,
                    longitude=match.attorney.location.longitude
                ),
                practice_areas=match.attorney.practice_areas,
                years_experience=match.attorney.years_experience,
                bar_memberships={k: v.value for k, v in match.attorney.bar_memberships.items()},
                fee_structures=match.attorney.fee_structures,
                languages=match.attorney.languages,
                website=match.attorney.website,
                bio=match.attorney.bio,
                hourly_rate_min=match.attorney.hourly_rate_min,
                hourly_rate_max=match.attorney.hourly_rate_max,
                consultation_fee=match.attorney.consultation_fee,
                free_consultation=match.attorney.free_consultation,
                accepting_new_clients=match.attorney.accepting_new_clients,
                profile_completeness=match.attorney.profile_completeness,
                distance_miles=match.distance_miles
            )
            
            match_response = ReferralMatchResponseModel(
                attorney=attorney_response,
                match_score=match.match_score,
                match_reasons=match.match_reasons,
                distance_miles=match.distance_miles,
                estimated_cost_range=match.estimated_cost_range,
                referral_source=match.referral_source
            )
            
            response_matches.append(match_response)
        
        logger.info(f"Found {len(response_matches)} attorney matches for referral request")
        return response_matches
        
    except Exception as e:
        logger.error(f"Error finding attorney matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error finding attorney matches"
        )


@router.post(
    "/referrals/request-contact",
    summary="Request Attorney Contact",
    description="Request that an attorney contact a potential client"
)
async def request_attorney_contact(
    contact_request: ContactRequestModel,
    current_user: CurrentUser = Depends(get_current_user)  # Requires authentication for contact requests
):
    """Request that an attorney contact a potential client"""
    try:
        # In a real implementation, this would:
        # 1. Validate the attorney and referral request exist
        # 2. Send notification to the attorney
        # 3. Log the contact request for follow-up
        # 4. Potentially charge referral fees to attorney
        
        # For now, return a confirmation
        contact_id = str(uuid.uuid4())
        
        response = {
            "contact_request_id": contact_id,
            "attorney_bar_number": contact_request.attorney_bar_number,
            "referral_request_id": contact_request.referral_request_id,
            "status": "pending",
            "message": "Contact request submitted successfully. The attorney will be notified.",
            "expected_response_time": "24-48 hours",
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Contact request submitted: {contact_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing contact request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing contact request"
        )


# =============================================================================
# LEGAL AID ENDPOINTS
# =============================================================================

@router.post(
    "/referrals/legal-aid",
    response_model=List[LegalAidResponseModel],
    summary="Find Legal Aid Organizations",
    description="Find legal aid organizations that may assist with a case"
)
async def find_legal_aid(
    search_request: LegalAidSearchRequest
):
    """Find legal aid organizations for a client"""
    try:
        # Convert to internal models
        location = Location(
            address=search_request.location.address,
            city=search_request.location.city,
            state=search_request.location.state,
            zip_code=search_request.location.zip_code,
            county=search_request.location.county,
            latitude=search_request.location.latitude,
            longitude=search_request.location.longitude
        )
        
        # Find legal aid organizations
        legal_aid_orgs = legal_aid_connector.find_legal_aid(
            location=location,
            case_type=search_request.case_type,
            household_income=search_request.household_income,
            family_size=search_request.family_size,
            preferred_language=search_request.preferred_language
        )
        
        # Convert to response format
        response_orgs = []
        for org in legal_aid_orgs:
            response_org = LegalAidResponseModel(
                id=org["id"],
                name=org["name"],
                state=org["state"],
                counties_served=org.get("counties_served", []),
                phone=org["phone"],
                website=org["website"],
                email=org.get("email"),
                services=org["services"],
                languages=org.get("languages", ["English"]),
                income_guidelines=org.get("income_guidelines", {}),
                emergency_services=org.get("emergency_services", False),
                location=org.get("location"),
                match_reason=org.get("match_reason", "Eligible for services")
            )
            response_orgs.append(response_org)
        
        logger.info(f"Found {len(response_orgs)} legal aid organizations")
        return response_orgs
        
    except Exception as e:
        logger.error(f"Error finding legal aid organizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error finding legal aid organizations"
        )


@router.post(
    "/referrals/pro-bono",
    summary="Find Pro Bono Programs",
    description="Find pro bono legal programs that may assist with a case"
)
async def find_pro_bono_programs(
    location: LocationModel,
    case_type: CaseType,
    practice_areas: List[PracticeArea] = Body([])
):
    """Find pro bono programs for a case"""
    try:
        # Convert to internal models
        location_obj = Location(
            address=location.address,
            city=location.city,
            state=location.state,
            zip_code=location.zip_code,
            county=location.county,
            latitude=location.latitude,
            longitude=location.longitude
        )
        
        # Find pro bono programs
        programs = legal_aid_connector.find_pro_bono_programs(
            location=location_obj,
            case_type=case_type,
            practice_areas=practice_areas
        )
        
        logger.info(f"Found {len(programs)} pro bono programs")
        return programs
        
    except Exception as e:
        logger.error(f"Error finding pro bono programs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error finding pro bono programs"
        )


@router.post(
    "/referrals/law-school-clinics",
    summary="Find Law School Clinics",
    description="Find law school legal clinics that may assist with a case"
)
async def find_law_school_clinics(
    location: LocationModel,
    practice_areas: List[PracticeArea] = Body([])
):
    """Find law school clinics that might help"""
    try:
        # Convert to internal models
        location_obj = Location(
            address=location.address,
            city=location.city,
            state=location.state,
            zip_code=location.zip_code,
            county=location.county,
            latitude=location.latitude,
            longitude=location.longitude
        )
        
        # Find law school clinics
        clinics = legal_aid_connector.find_law_school_clinics(
            location=location_obj,
            practice_areas=practice_areas
        )
        
        logger.info(f"Found {len(clinics)} law school clinics")
        return clinics
        
    except Exception as e:
        logger.error(f"Error finding law school clinics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error finding law school clinics"
        )


@router.post(
    "/referrals/self-help-centers",
    summary="Find Self-Help Centers",
    description="Find court self-help centers and resources"
)
async def find_self_help_centers(
    location: LocationModel,
    case_type: CaseType
):
    """Find self-help centers in the area"""
    try:
        # Convert to internal models
        location_obj = Location(
            address=location.address,
            city=location.city,
            state=location.state,
            zip_code=location.zip_code,
            county=location.county,
            latitude=location.latitude,
            longitude=location.longitude
        )
        
        # Find self-help centers
        centers = legal_aid_connector.find_self_help_centers(
            location=location_obj,
            case_type=case_type
        )
        
        logger.info(f"Found {len(centers)} self-help centers")
        return centers
        
    except Exception as e:
        logger.error(f"Error finding self-help centers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error finding self-help centers"
        )


@router.post(
    "/referrals/income-eligibility",
    response_model=IncomeEligibilityResponseModel,
    summary="Check Income Eligibility",
    description="Check income eligibility for various legal assistance programs"
)
async def check_income_eligibility(
    household_income: float = Body(..., ge=0),
    family_size: int = Body(..., ge=1, le=20),
    program_type: str = Body(default="legal_aid")
):
    """Check if income qualifies for various programs"""
    try:
        eligibility_info = legal_aid_connector.check_income_eligibility(
            household_income=household_income,
            family_size=family_size,
            program_type=program_type
        )
        
        response = IncomeEligibilityResponseModel(**eligibility_info)
        
        logger.info(f"Checked income eligibility for family of {family_size} with income ${household_income}")
        return response
        
    except Exception as e:
        logger.error(f"Error checking income eligibility: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking income eligibility"
        )


# =============================================================================
# BAR ASSOCIATION ENDPOINTS
# =============================================================================

@router.get(
    "/referrals/bar-associations",
    response_model=List[BarAssociationResponseModel],
    summary="Get Bar Association Referral Services",
    description="Get information about state bar association referral services"
)
async def get_bar_associations(
    state: Optional[str] = Query(None, description="Filter by state (2-letter code)")
):
    """Get bar association referral information"""
    try:
        if state:
            bar_assoc = attorney_directory.get_bar_association_info(state.upper())
            if not bar_assoc:
                return []
            bar_associations = [bar_assoc]
        else:
            bar_associations = attorney_directory.get_all_bar_associations()
        
        # Convert to response format
        response_associations = []
        for bar_assoc in bar_associations:
            response_assoc = BarAssociationResponseModel(
                name=bar_assoc.name,
                state=bar_assoc.state,
                website=bar_assoc.website,
                referral_phone=bar_assoc.referral_phone,
                referral_website=bar_assoc.referral_website,
                fee_for_referral=bar_assoc.fee_for_referral,
                referral_requirements=bar_assoc.referral_requirements,
                languages_available=bar_assoc.languages_available
            )
            response_associations.append(response_assoc)
        
        logger.info(f"Retrieved {len(response_associations)} bar associations")
        return response_associations
        
    except Exception as e:
        logger.error(f"Error retrieving bar associations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving bar associations"
        )


# =============================================================================
# STATISTICS AND HEALTH ENDPOINTS
# =============================================================================

@router.get(
    "/referrals/statistics",
    summary="Get Referral System Statistics",
    description="Get statistics about the referral system"
)
async def get_referral_statistics():
    """Get referral system statistics"""
    try:
        attorney_stats = attorney_directory.get_attorney_statistics()
        referral_stats = referral_engine.get_referral_statistics()
        
        combined_stats = {
            "attorney_directory": attorney_stats,
            "referral_engine": referral_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        return combined_stats
        
    except Exception as e:
        logger.error(f"Error retrieving referral statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving referral statistics"
        )


@router.get(
    "/referrals/health",
    summary="Referral System Health Check",
    description="Check the health and availability of referral services"
)
async def referral_health_check():
    """Health check for referral services"""
    try:
        # Test each service
        attorney_count = len(attorney_directory._attorneys)
        bar_assoc_count = len(attorney_directory._bar_associations)
        legal_aid_count = len(legal_aid_connector._legal_aid_orgs)
        
        return {
            "status": "healthy",
            "services": {
                "attorney_directory": {
                    "status": "online",
                    "attorneys_available": attorney_count,
                    "bar_associations": bar_assoc_count
                },
                "referral_engine": {
                    "status": "online",
                    "matching_enabled": True
                },
                "legal_aid_connector": {
                    "status": "online",
                    "organizations_available": legal_aid_count
                }
            },
            "disclaimer": "Referrals are provided for informational purposes only and do not constitute endorsements",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Referral health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


# =============================================================================
# DISCLAIMER ENDPOINT
# =============================================================================

@router.get(
    "/referrals/disclaimer",
    summary="Get Referral Disclaimer",
    description="Get important disclaimer information about referral services"
)
async def get_referral_disclaimer():
    """Get referral service disclaimer"""
    return {
        "title": "Attorney Referral Service Disclaimer",
        "content": """
        IMPORTANT DISCLAIMER: REFERRALS ARE NOT ENDORSEMENTS
        
        The attorney referral information provided through this service is for informational 
        purposes only and does not constitute an endorsement, recommendation, or guarantee 
        of any attorney's qualifications, competence, or performance.
        
        Key Points:
        
        1. NOT AN ENDORSEMENT: The inclusion of any attorney in our referral database or 
           search results does not constitute an endorsement of that attorney's services, 
           qualifications, or competence.
        
        2. INDEPENDENT VERIFICATION: You are responsible for independently verifying any 
           attorney's credentials, bar membership status, disciplinary record, and suitability 
           for your specific legal needs.
        
        3. NO GUARANTEES: We make no warranties or guarantees regarding the quality of 
           legal services that may be provided by any referred attorney.
        
        4. YOUR RESPONSIBILITY: The decision to hire any attorney is entirely yours. You 
           should interview potential attorneys, discuss fees and representation arrangements, 
           and make your own informed decision.
        
        5. STATE BAR RESOURCES: For official attorney referral services, contact your 
           state bar association. Many state bars maintain their own referral services 
           with additional screening requirements.
        
        6. FEE ARRANGEMENTS: Discuss all fee arrangements directly with any attorney. 
           Fee estimates provided are general ranges and actual costs may vary significantly.
        
        7. CONFLICT CHECKING: While we attempt to identify potential conflicts of interest, 
           you must discuss any potential conflicts directly with prospective attorneys.
        
        8. LEGAL AID ELIGIBILITY: Income eligibility calculations for legal aid are estimates. 
           Each organization has its own specific requirements and application process.
        
        By using this referral service, you acknowledge that you understand these limitations 
        and will make your own independent evaluation of any attorney before engaging their services.
        
        For questions about this disclaimer or our referral service, please contact our 
        support team.
        """,
        "last_updated": "2024-01-08T12:00:00Z",
        "acknowledgment_required": False,
        "contact_info": {
            "support_email": "referrals@legalai.com",
            "support_phone": "1-800-LEGAL-AI"
        }
    }