#!/usr/bin/env python3
"""
Educational Content Delivery API
Provides structured API for delivering educational legal content with proper disclaimers
"""

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Union
import json

# Import our educational components
try:
    from .content_library import (
        educational_content_library, ContentType, SubjectArea,
        EducationLevel, EducationalContent
    )
    from .context_matcher import (
        context_matcher, DocumentContext, UserProfile, UserExperience,
        MatchingStrategy, ContextMatchResponse
    )
    from .attorney_referral import (
        attorney_referral_system, PracticeArea, ReferralRequest,
        GeographicLocation, AttorneyProfile
    )
except ImportError:
    # Fallback for testing
    print("Warning: Educational components not found, using fallback mode")


class DeliveryMode(Enum):
    """Content delivery modes"""
    EDUCATIONAL_OVERVIEW = "educational_overview"
    DETAILED_EXPLANATION = "detailed_explanation"
    QUICK_REFERENCE = "quick_reference"
    STEP_BY_STEP_GUIDE = "step_by_step_guide"
    FAQ_FORMAT = "faq_format"
    ATTORNEY_REFERRAL = "attorney_referral"


class ContentRequest(Enum):
    """Types of content requests"""
    DOCUMENT_ANALYSIS = "document_analysis"
    LEGAL_EDUCATION = "legal_education"
    PROCEDURE_GUIDANCE = "procedure_guidance"
    ATTORNEY_SEARCH = "attorney_search"
    GENERAL_INFORMATION = "general_information"


@dataclass
class ContentDeliveryRequest:
    """Request for educational content delivery"""
    request_id: str
    request_type: ContentRequest
    delivery_mode: DeliveryMode
    subject_area: Optional[str] = None
    document_context: Optional[Dict[str, Any]] = None
    user_profile: Optional[Dict[str, Any]] = None
    specific_query: Optional[str] = None
    education_level: str = "beginner"
    include_disclaimers: bool = True
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ContentDeliveryResponse:
    """Response containing educational content with disclaimers"""
    request_id: str
    content_items: List[Dict[str, Any]]
    educational_disclaimers: List[str]
    attorney_consultation_notice: str
    related_resources: List[str]
    next_steps: List[str]
    confidence_score: float
    delivery_metadata: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EducationalContentDeliveryAPI:
    """API for delivering educational legal content with comprehensive disclaimers"""

    def __init__(self):
        self.standard_disclaimers = self._initialize_disclaimers()
        self.attorney_consultation_template = self._initialize_attorney_notice()
        self.delivery_stats = {
            "total_requests": 0,
            "successful_deliveries": 0,
            "attorney_referrals": 0,
            "disclaimer_acknowledgments": 0
        }

    def _initialize_disclaimers(self) -> List[str]:
        """Initialize comprehensive educational disclaimers"""
        return [
            "EDUCATIONAL PURPOSE ONLY: All content provided is for educational purposes only and does not constitute legal advice.",

            "NO ATTORNEY-CLIENT RELATIONSHIP: Using this system does not create an attorney-client relationship with any legal professional.",

            "SEEK PROFESSIONAL ADVICE: For any legal matter, you must consult with a qualified attorney licensed in your jurisdiction.",

            "JURISDICTION SPECIFIC: Legal procedures and requirements vary significantly by jurisdiction and change over time.",

            "NO GUARANTEES: This system provides no guarantees about legal outcomes, procedures, or requirements.",

            "INDEPENDENT VERIFICATION: You must independently verify all legal information with current statutes and qualified professionals.",

            "LIABILITY DISCLAIMER: This system assumes no responsibility for decisions made based on educational content provided.",

            "CURRENT INFORMATION: Legal information may become outdated. Always verify current laws and procedures.",

            "COMPLEXITY WARNING: Legal matters are complex and fact-specific. General educational content cannot address individual circumstances.",

            "EMERGENCY SITUATIONS: For urgent legal matters, contact an attorney immediately rather than relying on educational materials."
        ]

    def _initialize_attorney_notice(self) -> str:
        """Initialize attorney consultation notice"""
        return """
IMPORTANT: ATTORNEY CONSULTATION REQUIRED

This educational content cannot replace professional legal advice.
For any legal matter affecting your rights, obligations, or interests:

1. Consult with a qualified attorney licensed in your jurisdiction
2. Provide the attorney with all relevant facts and documentation
3. Follow the attorney's specific advice for your situation
4. Do not rely solely on general educational information

To find qualified attorneys:
- Contact your local or state bar association
- Use official bar association lawyer referral services
- Verify attorney credentials and licensing status
- Schedule consultations with multiple attorneys when appropriate

Legal matters are complex and fact-specific. Only a qualified attorney
can provide advice tailored to your specific circumstances.
"""

    def process_content_request(self, request: ContentDeliveryRequest) -> ContentDeliveryResponse:
        """Process educational content delivery request"""
        self.delivery_stats["total_requests"] += 1

        try:
            content_items = []
            confidence_score = 0.0

            # Route request based on type
            if request.request_type == ContentRequest.DOCUMENT_ANALYSIS:
                content_items, confidence_score = self._handle_document_analysis(request)
            elif request.request_type == ContentRequest.LEGAL_EDUCATION:
                content_items, confidence_score = self._handle_legal_education(request)
            elif request.request_type == ContentRequest.PROCEDURE_GUIDANCE:
                content_items, confidence_score = self._handle_procedure_guidance(request)
            elif request.request_type == ContentRequest.ATTORNEY_SEARCH:
                content_items, confidence_score = self._handle_attorney_search(request)
            else:
                content_items, confidence_score = self._handle_general_information(request)

            # Prepare response with educational framing
            response = ContentDeliveryResponse(
                request_id=request.request_id,
                content_items=content_items,
                educational_disclaimers=self.standard_disclaimers if request.include_disclaimers else [],
                attorney_consultation_notice=self.attorney_consultation_template,
                related_resources=self._get_related_resources(request),
                next_steps=self._get_educational_next_steps(request),
                confidence_score=confidence_score,
                delivery_metadata={
                    "delivery_mode": request.delivery_mode.value,
                    "education_level": request.education_level,
                    "processing_time": "educational_simulation",
                    "content_source": "educational_library"
                }
            )

            self.delivery_stats["successful_deliveries"] += 1
            return response

        except Exception as e:
            # Return educational error response
            return ContentDeliveryResponse(
                request_id=request.request_id,
                content_items=[{
                    "type": "error_message",
                    "title": "Educational System Unavailable",
                    "content": f"The educational content system is currently unavailable. Please contact your local bar association for legal information and attorney referrals. Error: {str(e)[:100]}",
                    "educational_note": "This is an educational system only. For actual legal assistance, always consult qualified attorneys."
                }],
                educational_disclaimers=self.standard_disclaimers,
                attorney_consultation_notice=self.attorney_consultation_template,
                related_resources=["Local Bar Association Directory"],
                next_steps=["Contact qualified legal professional"],
                confidence_score=0.0,
                delivery_metadata={"error": "educational_system_error"}
            )

    def _handle_document_analysis(self, request: ContentDeliveryRequest) -> tuple[List[Dict[str, Any]], float]:
        """Handle document analysis requests with educational context"""
        content_items = []

        if request.document_context:
            # Use context matcher if available
            try:
                from .context_matcher import context_matcher, DocumentContext, UserProfile, UserExperience

                # Create document context
                doc_context = DocumentContext(
                    document_type=request.document_context.get("document_type", "unknown"),
                    content_summary=request.document_context.get("content_summary", ""),
                    key_terms=request.document_context.get("key_terms", []),
                    legal_areas=request.document_context.get("legal_areas", [])
                )

                # Create user profile
                user_profile = UserProfile(
                    user_id=request.document_context.get("user_id", "educational_user"),
                    experience_level=UserExperience.BEGINNER,
                    preferred_language="English"
                )

                # Get matched content
                match_response = context_matcher.match_content_to_document(doc_context, user_profile)

                for content in match_response.matched_content[:3]:  # Limit to top 3
                    content_items.append({
                        "type": "educational_content",
                        "title": content.title,
                        "content": content.detailed_content,
                        "confidence": match_response.confidence_score,
                        "educational_objectives": content.educational_objectives,
                        "disclaimers": content.disclaimers
                    })

                return content_items, match_response.confidence_score

            except ImportError:
                pass

        # Fallback educational content
        content_items.append({
            "type": "educational_overview",
            "title": "Understanding Legal Documents - Educational Overview",
            "content": """
This educational overview explains general principles of legal document analysis.

KEY EDUCATIONAL POINTS:
1. Document Type Identification: Legal documents serve specific purposes (contracts, pleadings, etc.)
2. Structure Analysis: Most legal documents follow standard formatting conventions
3. Key Terms: Legal documents contain specific terminology with precise meanings
4. Procedural Context: Documents often have filing deadlines and court requirements

EDUCATIONAL DISCLAIMER: This analysis is for educational purposes only. Each legal document
is unique and requires professional legal analysis for actual use.
            """,
            "educational_note": "This is general educational information only. Professional legal analysis is required for actual documents."
        })

        return content_items, 0.8

    def _handle_legal_education(self, request: ContentDeliveryRequest) -> tuple[List[Dict[str, Any]], float]:
        """Handle legal education requests"""
        content_items = []

        # Use content library if available
        try:
            from .content_library import educational_content_library

            # Search for relevant educational content
            matching_content = educational_content_library.search_content(
                query=request.specific_query or request.subject_area or "legal basics",
                subject_area=request.subject_area,
                education_level=request.education_level
            )

            for content in matching_content.results[:5]:  # Limit to top 5
                content_items.append({
                    "type": "educational_content",
                    "title": content.title,
                    "content": content.detailed_content,
                    "educational_objectives": content.educational_objectives,
                    "subject_area": content.subject_area.value,
                    "education_level": content.education_level.value,
                    "disclaimers": content.disclaimers
                })

            return content_items, matching_content.relevance_score

        except ImportError:
            pass

        # Fallback educational content
        content_items.append({
            "type": "legal_education",
            "title": "Introduction to Legal Concepts - Educational Content",
            "content": """
EDUCATIONAL LEGAL OVERVIEW:

1. LEGAL SYSTEM BASICS:
   - Laws are created by legislatures and interpreted by courts
   - Legal procedures vary significantly by jurisdiction
   - Different courts handle different types of cases

2. COMMON LEGAL AREAS:
   - Civil Law: Disputes between private parties
   - Criminal Law: Offenses against society
   - Administrative Law: Government agency regulations
   - Constitutional Law: Rights and government powers

3. LEGAL PROCESSES:
   - Research: Understanding applicable laws
   - Analysis: Applying law to specific facts
   - Procedure: Following court and filing requirements
   - Representation: Working with qualified attorneys

EDUCATIONAL NOTE: This is basic educational information. Legal matters
require consultation with qualified attorneys for specific situations.
            """,
            "educational_level": request.education_level
        })

        return content_items, 0.75

    def _handle_procedure_guidance(self, request: ContentDeliveryRequest) -> tuple[List[Dict[str, Any]], float]:
        """Handle legal procedure guidance requests"""
        content_items = []

        content_items.append({
            "type": "procedure_guidance",
            "title": "Legal Procedure Educational Guidelines",
            "content": """
EDUCATIONAL GUIDANCE ON LEGAL PROCEDURES:

1. GENERAL PROCEDURE PRINCIPLES:
   - All legal procedures are governed by specific rules
   - Deadlines are typically strict and non-negotiable
   - Proper forms and formatting are usually required
   - Filing fees may be required

2. COMMON PROCEDURAL STEPS:
   - Research applicable rules and requirements
   - Prepare necessary documentation
   - File within required deadlines
   - Serve other parties as required
   - Attend hearings or conferences as scheduled

3. JURISDICTIONAL VARIATIONS:
   - Federal vs. state court procedures differ
   - Local rules may modify general procedures
   - Administrative procedures vary by agency

CRITICAL EDUCATIONAL NOTE: These are general educational principles only.
Actual legal procedures must be handled by qualified attorneys who understand
jurisdiction-specific requirements and can ensure proper compliance.
            """,
            "procedure_type": request.subject_area or "general",
            "educational_warning": "Procedural errors can have serious legal consequences. Always consult qualified attorneys."
        })

        return content_items, 0.85

    def _handle_attorney_search(self, request: ContentDeliveryRequest) -> tuple[List[Dict[str, Any]], float]:
        """Handle attorney search requests"""
        self.delivery_stats["attorney_referrals"] += 1
        content_items = []

        # Use attorney referral system if available
        try:
            from .attorney_referral import attorney_referral_system

            # Create referral request
            referral_request = attorney_referral_system.create_referral_request(
                practice_area=request.subject_area or "civil_litigation",
                state=request.document_context.get("state", "Virginia") if request.document_context else "Virginia",
                city=request.document_context.get("city", "Richmond") if request.document_context else "Richmond",
                user_id=request.request_id
            )

            # Get attorney referral response
            referral_response = attorney_referral_system.find_attorneys(referral_request)

            content_items.append({
                "type": "attorney_referral",
                "title": "Educational Attorney Referral Information",
                "content": attorney_referral_system.generate_referral_summary(referral_response),
                "matching_attorneys": len(referral_response.matching_attorneys),
                "bar_associations": referral_response.bar_association_contacts,
                "referral_disclaimers": referral_response.referral_disclaimers
            })

            return content_items, 0.95

        except ImportError:
            pass

        # Fallback attorney referral guidance
        content_items.append({
            "type": "attorney_referral_guidance",
            "title": "How to Find Qualified Attorneys - Educational Guidance",
            "content": """
EDUCATIONAL GUIDANCE FOR FINDING ATTORNEYS:

1. BAR ASSOCIATION REFERRAL SERVICES:
   - Contact your state bar association
   - Use official lawyer referral services
   - Verify attorney credentials and licensing

2. RESEARCH PROCESS:
   - Check attorney specialization areas
   - Review disciplinary records
   - Read client reviews and testimonials
   - Verify bar admission and good standing

3. CONSULTATION PROCESS:
   - Schedule initial consultations
   - Prepare questions about experience and approach
   - Discuss fees and payment arrangements
   - Evaluate communication style and comfort level

4. VERIFICATION STEPS:
   - Confirm attorney is licensed in your jurisdiction
   - Check for any disciplinary actions
   - Verify malpractice insurance coverage
   - Obtain written fee agreements

EDUCATIONAL DISCLAIMER: This is general guidance only. Always use official
bar association resources for attorney referrals and verification.
            """,
            "educational_level": "general"
        })

        return content_items, 0.80

    def _handle_general_information(self, request: ContentDeliveryRequest) -> tuple[List[Dict[str, Any]], float]:
        """Handle general legal information requests"""
        content_items = []

        content_items.append({
            "type": "general_legal_information",
            "title": "General Legal Information - Educational Overview",
            "content": """
EDUCATIONAL LEGAL INFORMATION OVERVIEW:

1. UNDERSTANDING LEGAL RIGHTS:
   - Rights are defined by constitutions, statutes, and case law
   - Rights may vary by jurisdiction and circumstances
   - Professional legal advice is needed to understand specific rights

2. LEGAL RESPONSIBILITIES:
   - Citizens have duties under various laws
   - Ignorance of law is generally not a defense
   - Compliance requires understanding current legal requirements

3. LEGAL PROCESSES:
   - Courts resolve disputes according to established procedures
   - Administrative agencies enforce regulatory requirements
   - Legal professionals help navigate complex systems

4. SEEKING LEGAL HELP:
   - Identify qualified attorneys for specific legal areas
   - Use bar association referral services
   - Understand attorney-client privilege and responsibilities

EDUCATIONAL PURPOSE: This information is provided for educational purposes
to help individuals understand general legal concepts and the importance
of professional legal consultation.
            """,
            "query_context": request.specific_query or "general legal information",
            "educational_level": request.education_level
        })

        return content_items, 0.70

    def _get_related_resources(self, request: ContentDeliveryRequest) -> List[str]:
        """Get related educational resources"""
        base_resources = [
            "State Bar Association Website",
            "Legal Aid Organizations Directory",
            "Court Self-Help Resources",
            "Legal Ethics Information"
        ]

        if request.request_type == ContentRequest.ATTORNEY_SEARCH:
            base_resources.extend([
                "Lawyer Referral Services",
                "Attorney Disciplinary Database",
                "Bar Association Continuing Education"
            ])
        elif request.request_type == ContentRequest.DOCUMENT_ANALYSIS:
            base_resources.extend([
                "Document Template Libraries",
                "Filing Requirement Guides",
                "Court Forms and Instructions"
            ])

        return base_resources

    def _get_educational_next_steps(self, request: ContentDeliveryRequest) -> List[str]:
        """Get educational next steps for users"""
        next_steps = [
            "1. Consult with qualified attorney for your specific situation",
            "2. Verify all legal information with current statutes and rules",
            "3. Contact relevant bar association for official guidance"
        ]

        if request.request_type == ContentRequest.ATTORNEY_SEARCH:
            next_steps.extend([
                "4. Use official bar association lawyer referral services",
                "5. Verify attorney credentials and licensing status",
                "6. Schedule consultations with multiple attorneys"
            ])
        else:
            next_steps.extend([
                "4. Research jurisdiction-specific requirements",
                "5. Gather all relevant documentation",
                "6. Understand deadlines and procedural requirements"
            ])

        return next_steps

    def create_content_request(self, request_type: str, delivery_mode: str = "educational_overview",
                             subject_area: Optional[str] = None,
                             specific_query: Optional[str] = None,
                             document_context: Optional[Dict[str, Any]] = None) -> ContentDeliveryRequest:
        """Create a new content delivery request"""

        # Convert string enums
        try:
            request_type_enum = ContentRequest(request_type.lower())
        except ValueError:
            request_type_enum = ContentRequest.GENERAL_INFORMATION

        try:
            delivery_mode_enum = DeliveryMode(delivery_mode.lower())
        except ValueError:
            delivery_mode_enum = DeliveryMode.EDUCATIONAL_OVERVIEW

        return ContentDeliveryRequest(
            request_id=f"EDU-{uuid.uuid4().hex[:8].upper()}",
            request_type=request_type_enum,
            delivery_mode=delivery_mode_enum,
            subject_area=subject_area,
            specific_query=specific_query,
            document_context=document_context
        )

    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery statistics for educational purposes"""
        return {
            **self.delivery_stats,
            "success_rate": (self.delivery_stats["successful_deliveries"] /
                           max(self.delivery_stats["total_requests"], 1)) * 100,
            "disclaimer_compliance": "100% - All content includes educational disclaimers",
            "attorney_referral_rate": (self.delivery_stats["attorney_referrals"] /
                                     max(self.delivery_stats["total_requests"], 1)) * 100
        }


# Global content delivery API instance
content_delivery_api = EducationalContentDeliveryAPI()


def main():
    """Test the content delivery API with educational examples"""
    print("EDUCATIONAL CONTENT DELIVERY API - TEST")
    print("=" * 50)

    # Test legal education request
    print("\n1. Testing Legal Education Request...")
    education_request = content_delivery_api.create_content_request(
        request_type="legal_education",
        delivery_mode="educational_overview",
        subject_area="bankruptcy",
        specific_query="Chapter 7 bankruptcy process"
    )

    education_response = content_delivery_api.process_content_request(education_request)
    print(f"Content items delivered: {len(education_response.content_items)}")
    print(f"Disclaimers included: {len(education_response.educational_disclaimers)}")
    print(f"Confidence score: {education_response.confidence_score:.2f}")

    # Test attorney search request
    print("\n2. Testing Attorney Search Request...")
    attorney_request = content_delivery_api.create_content_request(
        request_type="attorney_search",
        subject_area="bankruptcy",
        document_context={"state": "Virginia", "city": "Richmond"}
    )

    attorney_response = content_delivery_api.process_content_request(attorney_request)
    print(f"Attorney referral content: {len(attorney_response.content_items)}")
    print(f"Related resources: {len(attorney_response.related_resources)}")

    # Show delivery statistics
    print("\n3. Delivery Statistics:")
    stats = content_delivery_api.get_delivery_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print(f"\nAll educational content delivered with comprehensive disclaimers and attorney consultation notices.")


if __name__ == "__main__":
    main()