#!/usr/bin/env python3
"""
Attorney Referral System
Educational system for providing attorney referral information with proper disclaimers
"""

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import json


class PracticeArea(Enum):
    """Legal practice areas for attorney specialization"""
    BANKRUPTCY = "bankruptcy"
    PERSONAL_INJURY = "personal_injury"
    FAMILY_LAW = "family_law"
    CRIMINAL_DEFENSE = "criminal_defense"
    CIVIL_LITIGATION = "civil_litigation"
    CORPORATE_LAW = "corporate_law"
    REAL_ESTATE = "real_estate"
    IMMIGRATION = "immigration"
    EMPLOYMENT = "employment"
    ESTATE_PLANNING = "estate_planning"
    TAX_LAW = "tax_law"
    INTELLECTUAL_PROPERTY = "intellectual_property"


class AttorneyStatus(Enum):
    """Attorney licensing and status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    RETIRED = "retired"
    UNKNOWN = "unknown"


@dataclass
class GeographicLocation:
    """Geographic information for attorney location"""
    state: str
    city: str
    county: Optional[str] = None
    zip_code: Optional[str] = None
    bar_jurisdiction: str = ""


@dataclass
class AttorneyProfile:
    """Attorney profile information"""
    attorney_id: str
    full_name: str
    bar_number: str
    license_state: str
    status: AttorneyStatus
    practice_areas: List[PracticeArea]
    location: GeographicLocation
    years_practicing: Optional[int] = None
    law_school: Optional[str] = None
    bar_admissions: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    accepts_pro_bono: bool = False
    contact_method: str = "bar_association"  # Never direct contact
    created_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ReferralRequest:
    """Request for attorney referral"""
    request_id: str
    practice_area: PracticeArea
    location: GeographicLocation
    language_preference: Optional[str] = None
    pro_bono_needed: bool = False
    case_description: Optional[str] = None  # Educational context only
    urgency_level: str = "standard"
    user_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ReferralResponse:
    """Response containing attorney referrals with disclaimers"""
    request_id: str
    matching_attorneys: List[AttorneyProfile]
    referral_disclaimers: List[str]
    bar_association_contacts: List[Dict[str, str]]
    next_steps: List[str]
    educational_resources: List[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AttorneyReferralSystem:
    """Educational attorney referral system with comprehensive disclaimers"""

    def __init__(self):
        self.sample_attorneys = self._initialize_sample_attorneys()
        self.referral_disclaimers = self._initialize_disclaimers()
        self.bar_associations = self._initialize_bar_associations()

    def _initialize_sample_attorneys(self) -> List[AttorneyProfile]:
        """Initialize sample attorney database for educational purposes"""
        return [
            AttorneyProfile(
                attorney_id="EDU-001",
                full_name="Sample Attorney - Educational Use Only",
                bar_number="EDU123456",
                license_state="Virginia",
                status=AttorneyStatus.ACTIVE,
                practice_areas=[PracticeArea.BANKRUPTCY, PracticeArea.CIVIL_LITIGATION],
                location=GeographicLocation(
                    state="Virginia",
                    city="Richmond",
                    county="Henrico",
                    zip_code="23219",
                    bar_jurisdiction="Virginia State Bar"
                ),
                years_practicing=15,
                law_school="Sample Law School",
                bar_admissions=["Virginia", "Federal District Court"],
                languages=["English"],
                accepts_pro_bono=True
            ),
            AttorneyProfile(
                attorney_id="EDU-002",
                full_name="Educational Example Attorney",
                bar_number="EDU789012",
                license_state="Virginia",
                status=AttorneyStatus.ACTIVE,
                practice_areas=[PracticeArea.FAMILY_LAW, PracticeArea.ESTATE_PLANNING],
                location=GeographicLocation(
                    state="Virginia",
                    city="Norfolk",
                    county="Norfolk City",
                    zip_code="23510",
                    bar_jurisdiction="Virginia State Bar"
                ),
                years_practicing=8,
                law_school="Educational Law Institute",
                bar_admissions=["Virginia"],
                languages=["English", "Spanish"],
                accepts_pro_bono=False
            ),
            AttorneyProfile(
                attorney_id="EDU-003",
                full_name="Demo Legal Professional",
                bar_number="EDU345678",
                license_state="Virginia",
                status=AttorneyStatus.ACTIVE,
                practice_areas=[PracticeArea.CRIMINAL_DEFENSE, PracticeArea.CIVIL_LITIGATION],
                location=GeographicLocation(
                    state="Virginia",
                    city="Virginia Beach",
                    county="Virginia Beach City",
                    zip_code="23451",
                    bar_jurisdiction="Virginia State Bar"
                ),
                years_practicing=22,
                law_school="Sample University Law School",
                bar_admissions=["Virginia", "North Carolina"],
                languages=["English"],
                accepts_pro_bono=True
            )
        ]

    def _initialize_disclaimers(self) -> List[str]:
        """Initialize comprehensive referral disclaimers"""
        return [
            "EDUCATIONAL REFERRAL DISCLAIMER: This attorney referral information is provided for EDUCATIONAL PURPOSES ONLY and does not constitute a recommendation or endorsement of any specific attorney.",

            "NO ATTORNEY-CLIENT RELATIONSHIP: Receiving referral information does not create an attorney-client relationship. You must independently contact and retain an attorney.",

            "VERIFICATION REQUIRED: You must independently verify all attorney credentials, licensing status, and qualifications before engaging their services.",

            "BAR ASSOCIATION CONTACT: For official attorney referrals, contact your local or state bar association directly. This system provides educational information only.",

            "NO LEGAL ADVICE: This referral system does not provide legal advice. Only a licensed attorney can provide legal advice specific to your situation.",

            "INDEPENDENT CONSULTATION: You must independently consult with attorneys to determine their suitability for your specific legal needs.",

            "LIABILITY DISCLAIMER: This system assumes no responsibility for attorney performance, outcomes, or professional conduct.",

            "JURISDICTIONAL NOTICE: Attorney licensing and practice rules vary by jurisdiction. Verify attorneys are licensed in your jurisdiction.",

            "FEES AND COSTS: Attorney fees and costs are matters between you and the attorney. This system provides no fee information or guarantees.",

            "PROFESSIONAL RESPONSIBILITY: Attorneys must comply with professional responsibility rules. Report any concerns to the appropriate bar association."
        ]

    def _initialize_bar_associations(self) -> Dict[str, Dict[str, str]]:
        """Initialize bar association contact information"""
        return {
            "Virginia": {
                "name": "Virginia State Bar",
                "phone": "(804) 775-0500",
                "website": "https://www.vsb.org",
                "referral_service": "https://www.vsb.org/site/public/lawyer-referral-service",
                "address": "1111 East Main Street, Suite 700, Richmond, VA 23219"
            },
            "Federal": {
                "name": "American Bar Association",
                "phone": "(312) 988-5000",
                "website": "https://www.americanbar.org",
                "referral_service": "https://www.americanbar.org/groups/legal_services/flh-home/",
                "address": "321 N Clark St, Chicago, IL 60654"
            }
        }

    def find_attorneys(self, referral_request: ReferralRequest) -> ReferralResponse:
        """Find attorneys matching referral criteria with educational disclaimers"""
        try:
            # Filter attorneys by practice area and location
            matching_attorneys = []

            for attorney in self.sample_attorneys:
                # Check practice area match
                if referral_request.practice_area in attorney.practice_areas:
                    # Check location match (state level for educational demo)
                    if attorney.location.state.lower() == referral_request.location.state.lower():
                        # Check pro bono requirement if needed
                        if not referral_request.pro_bono_needed or attorney.accepts_pro_bono:
                            # Check language preference if specified
                            if (not referral_request.language_preference or
                                referral_request.language_preference in attorney.languages):
                                matching_attorneys.append(attorney)

            # Get relevant bar association contacts
            bar_contacts = []
            state_key = referral_request.location.state
            if state_key in self.bar_associations:
                bar_contacts.append(self.bar_associations[state_key])

            # Always include general ABA contact
            bar_contacts.append(self.bar_associations["Federal"])

            # Educational next steps
            next_steps = [
                "1. Contact your state bar association for official attorney referrals",
                "2. Verify attorney credentials through state bar website",
                "3. Schedule initial consultations with multiple attorneys",
                "4. Ask about fees, experience, and case approach during consultation",
                "5. Ensure attorney is licensed in your jurisdiction",
                "6. Review attorney disciplinary records before hiring",
                "7. Obtain written fee agreement before proceeding"
            ]

            # Educational resources
            educational_resources = [
                "State Bar Association Lawyer Referral Services",
                "Legal Aid Organizations for Low-Income Assistance",
                "Pro Bono Programs for Qualifying Cases",
                "Attorney Disciplinary Database for Background Checks",
                "Legal Ethics Rules and Professional Standards",
                "Client Rights and Responsibilities Information",
                "Fee Dispute Resolution Programs"
            ]

            return ReferralResponse(
                request_id=referral_request.request_id,
                matching_attorneys=matching_attorneys,
                referral_disclaimers=self.referral_disclaimers,
                bar_association_contacts=bar_contacts,
                next_steps=next_steps,
                educational_resources=educational_resources
            )

        except Exception as e:
            # Return educational error response
            return ReferralResponse(
                request_id=referral_request.request_id,
                matching_attorneys=[],
                referral_disclaimers=self.referral_disclaimers + [
                    f"SYSTEM ERROR: Unable to process referral request. Please contact your local bar association directly. Error: Educational system only."
                ],
                bar_association_contacts=[self.bar_associations["Federal"]],
                next_steps=["Contact your local bar association for attorney referral assistance"],
                educational_resources=["State Bar Association Directory"]
            )

    def get_bar_association_info(self, state: str) -> Dict[str, str]:
        """Get bar association contact information for educational purposes"""
        state_key = state.strip().title()

        if state_key in self.bar_associations:
            return self.bar_associations[state_key]
        else:
            # Return general ABA information for unknown states
            return self.bar_associations["Federal"]

    def create_referral_request(self, practice_area: str, state: str, city: str,
                               pro_bono_needed: bool = False,
                               language_preference: Optional[str] = None,
                               user_id: str = "educational_user") -> ReferralRequest:
        """Create a new attorney referral request for educational purposes"""

        # Convert practice area string to enum
        try:
            practice_area_enum = PracticeArea(practice_area.lower())
        except ValueError:
            practice_area_enum = PracticeArea.CIVIL_LITIGATION  # Default fallback

        return ReferralRequest(
            request_id=f"REF-{uuid.uuid4().hex[:8].upper()}",
            practice_area=practice_area_enum,
            location=GeographicLocation(
                state=state.strip().title(),
                city=city.strip().title()
            ),
            language_preference=language_preference,
            pro_bono_needed=pro_bono_needed,
            user_id=user_id
        )

    def generate_referral_summary(self, response: ReferralResponse) -> str:
        """Generate educational summary of referral response"""
        summary_lines = [
            "ATTORNEY REFERRAL EDUCATIONAL SUMMARY",
            "=" * 50,
            "",
            f"Request ID: {response.request_id}",
            f"Generated: {response.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            f"Educational Matches Found: {len(response.matching_attorneys)}",
            ""
        ]

        if response.matching_attorneys:
            summary_lines.append("SAMPLE ATTORNEY INFORMATION (Educational Only):")
            summary_lines.append("-" * 45)

            for i, attorney in enumerate(response.matching_attorneys, 1):
                summary_lines.extend([
                    f"{i}. {attorney.full_name}",
                    f"   Practice Areas: {', '.join([area.value.replace('_', ' ').title() for area in attorney.practice_areas])}",
                    f"   Location: {attorney.location.city}, {attorney.location.state}",
                    f"   Experience: {attorney.years_practicing or 'Not specified'} years",
                    f"   Pro Bono: {'Yes' if attorney.accepts_pro_bono else 'No'}",
                    f"   Languages: {', '.join(attorney.languages)}",
                    ""
                ])

        summary_lines.extend([
            "BAR ASSOCIATION CONTACTS:",
            "-" * 30
        ])

        for contact in response.bar_association_contacts:
            summary_lines.extend([
                f"Organization: {contact['name']}",
                f"Phone: {contact['phone']}",
                f"Website: {contact['website']}",
                f"Referral Service: {contact['referral_service']}",
                ""
            ])

        summary_lines.extend([
            "IMPORTANT DISCLAIMERS:",
            "-" * 25
        ])

        for disclaimer in response.referral_disclaimers[:5]:  # Show first 5 disclaimers
            summary_lines.append(f"• {disclaimer}")

        summary_lines.extend([
            "",
            "NEXT STEPS (Educational Guidance):",
            "-" * 35
        ])

        for step in response.next_steps:
            summary_lines.append(f"  {step}")

        return "\n".join(summary_lines)


# Global attorney referral system instance
attorney_referral_system = AttorneyReferralSystem()


def main():
    """Test the attorney referral system with educational examples"""
    print("ATTORNEY REFERRAL SYSTEM - EDUCATIONAL TEST")
    print("=" * 50)

    # Test bankruptcy attorney referral
    print("\nTesting Bankruptcy Attorney Referral...")
    bankruptcy_request = attorney_referral_system.create_referral_request(
        practice_area="bankruptcy",
        state="Virginia",
        city="Richmond",
        pro_bono_needed=True,
        user_id="test_user"
    )

    bankruptcy_response = attorney_referral_system.find_attorneys(bankruptcy_request)

    print(f"Found {len(bankruptcy_response.matching_attorneys)} matching attorneys")
    print(f"Bar associations provided: {len(bankruptcy_response.bar_association_contacts)}")
    print(f"Disclaimers included: {len(bankruptcy_response.referral_disclaimers)}")

    # Generate and display summary
    summary = attorney_referral_system.generate_referral_summary(bankruptcy_response)
    print("\n" + summary)


if __name__ == "__main__":
    main()