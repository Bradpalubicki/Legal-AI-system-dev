#!/usr/bin/env python3
"""
Educational Context Matching System
Legal AI System - Intelligent Content Matching

This module provides intelligent context matching to deliver relevant educational
materials based on document type, content analysis, and user educational needs.

Features:
- Document type to educational content matching
- Dynamic content relevance scoring
- Official resource linking
- Related FAQ suggestions
- Educational pathway recommendations

ALL CONTENT DELIVERY IS FOR EDUCATIONAL PURPOSES ONLY
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Import educational content components
try:
    from .content_library import (
        educational_content_library, ContentQuery, SubjectArea, ContentType,
        EducationLevel, EducationalContent
    )
except ImportError:
    # Fallback for testing
    print("Warning: Content library not available - using mock data")

    class ContentQuery:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class SubjectArea:
        BANKRUPTCY = "bankruptcy"
        CIVIL_PROCEDURE = "civil_procedure"
        GENERAL = "general"

    class ContentType:
        BANKRUPTCY_INFO = "bankruptcy_info"
        COURT_PROCEDURE = "court_procedure"
        FAQ = "faq"
        LEGAL_GLOSSARY = "legal_glossary"

    class EducationLevel:
        BASIC = "basic"
        INTERMEDIATE = "intermediate"
        ADVANCED = "advanced"

# Import document processing components
try:
    from ..document.classification_engine import DocumentTypeCategory, EducationalCategory
except ImportError:
    class DocumentTypeCategory:
        MOTION = "motion"
        PETITION = "petition"
        ORDER = "order"
        COMPLAINT = "complaint"
        UNKNOWN = "unknown"

    class EducationalCategory:
        BANKRUPTCY_PROCEDURE = "bankruptcy_procedure"
        CIVIL_PROCEDURE = "civil_procedure"
        GENERAL_LEGAL = "general_legal"

# Setup logging
logger = logging.getLogger('context_matcher')

class UserExperience(Enum):
    """User experience levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class MatchingStrategy(str, Enum):
    """Strategies for content matching"""
    DOCUMENT_TYPE_BASED = "document_type_based"
    CONTENT_ANALYSIS_BASED = "content_analysis_based"
    USER_LEVEL_BASED = "user_level_based"
    HYBRID = "hybrid"

class RelevanceLevel(str, Enum):
    """Content relevance levels"""
    HIGHLY_RELEVANT = "highly_relevant"
    RELEVANT = "relevant"
    SOMEWHAT_RELEVANT = "somewhat_relevant"
    BACKGROUND = "background"

@dataclass
class DocumentContext:
    """Context information from analyzed document"""
    document_type: str
    content_summary: str = ""
    key_terms: List[str] = None
    legal_areas: List[str] = None
    document_id: str = ""
    educational_category: str = ""
    extracted_dates: List[str] = None
    extracted_parties: List[str] = None
    complexity_indicators: List[str] = None
    confidence_score: float = 0.0

    def __post_init__(self):
        if self.key_terms is None:
            self.key_terms = []
        if self.legal_areas is None:
            self.legal_areas = []
        if self.extracted_dates is None:
            self.extracted_dates = []
        if self.extracted_parties is None:
            self.extracted_parties = []
        if self.complexity_indicators is None:
            self.complexity_indicators = []

@dataclass
class UserProfile:
    """User educational profile"""
    user_id: str
    experience_level: UserExperience
    subject_interests: List[SubjectArea] = None
    previous_topics: List[str] = None
    learning_goals: List[str] = None
    time_preferences: str = "quick_overview"  # "quick_overview", "detailed_study", "comprehensive"
    preferred_language: str = "English"

@dataclass
class MatchedContent:
    """Content matched to context with relevance scoring"""
    content: EducationalContent
    relevance_level: RelevanceLevel
    relevance_score: float
    matching_factors: List[str]

@dataclass
class ContextMatchResponse:
    """Response for context matching with educational content"""
    matched_content: List[EducationalContent]
    confidence_score: float
    educational_recommendations: List[str]
    related_resources: List[str] = None

    def __post_init__(self):
        if self.related_resources is None:
            self.related_resources = []

@dataclass
class CompleteContextMatchResponse:
    """Complete context matching response"""
    response_id: str
    document_context: DocumentContext
    primary_matches: List[MatchedContent]
    related_matches: List[MatchedContent]
    official_resources: List[Dict[str, str]]
    suggested_faqs: List[EducationalContent]
    learning_pathway: List[str]
    next_steps: List[str]
    educational_disclaimers: List[str]
    attorney_consultation_required: bool

class EducationalContextMatcher:
    """
    Intelligent context matching system for educational content delivery
    """

    def __init__(self):
        self.logger = logger

        # Initialize content mapping strategies
        self._initialize_document_mappings()
        self._initialize_concept_mappings()
        self._initialize_pathway_mappings()

        # Educational disclaimers
        self.educational_disclaimers = [
            "All content provided is for educational purposes only and does not constitute legal advice.",
            "Educational materials are designed to increase understanding of legal concepts and procedures.",
            "Specific legal requirements vary by jurisdiction and individual circumstances.",
            "Always consult with a qualified attorney for legal advice pertaining to your situation."
        ]

    def _initialize_document_mappings(self):
        """Initialize document type to content mappings"""
        self.document_content_map = {
            # Bankruptcy Documents
            DocumentTypeCategory.PETITION: {
                SubjectArea.BANKRUPTCY: [
                    ContentType.BANKRUPTCY_INFO,
                    ContentType.FAQ,
                    ContentType.TIMELINES,
                    ContentType.COURT_PROCEDURE
                ]
            },

            # Motion Documents
            DocumentTypeCategory.MOTION: {
                SubjectArea.CIVIL_PROCEDURE: [
                    ContentType.COURT_PROCEDURE,
                    ContentType.DOCUMENT_TYPES,
                    ContentType.LEGAL_GLOSSARY
                ],
                SubjectArea.BANKRUPTCY: [
                    ContentType.BANKRUPTCY_INFO,
                    ContentType.COURT_PROCEDURE,
                    ContentType.FAQ
                ]
            },

            # Order Documents
            DocumentTypeCategory.ORDER: {
                SubjectArea.CIVIL_PROCEDURE: [
                    ContentType.COURT_PROCEDURE,
                    ContentType.LEGAL_GLOSSARY,
                    ContentType.TIMELINES
                ],
                SubjectArea.BANKRUPTCY: [
                    ContentType.BANKRUPTCY_INFO,
                    ContentType.TIMELINES
                ]
            },

            # Complaint Documents
            DocumentTypeCategory.COMPLAINT: {
                SubjectArea.CIVIL_PROCEDURE: [
                    ContentType.COURT_PROCEDURE,
                    ContentType.DOCUMENT_TYPES,
                    ContentType.TIMELINES
                ]
            }
        }

    def _initialize_concept_mappings(self):
        """Initialize concept to content mappings"""
        self.concept_content_map = {
            # Bankruptcy Concepts
            "bankruptcy": [SubjectArea.BANKRUPTCY],
            "chapter 7": [SubjectArea.BANKRUPTCY],
            "chapter 13": [SubjectArea.BANKRUPTCY],
            "discharge": [SubjectArea.BANKRUPTCY],
            "automatic stay": [SubjectArea.BANKRUPTCY],
            "trustee": [SubjectArea.BANKRUPTCY],
            "creditor": [SubjectArea.BANKRUPTCY],
            "debtor": [SubjectArea.BANKRUPTCY],

            # Civil Procedure Concepts
            "motion": [SubjectArea.CIVIL_PROCEDURE],
            "discovery": [SubjectArea.CIVIL_PROCEDURE],
            "summary judgment": [SubjectArea.CIVIL_PROCEDURE],
            "jurisdiction": [SubjectArea.CIVIL_PROCEDURE, SubjectArea.GENERAL],
            "venue": [SubjectArea.CIVIL_PROCEDURE],
            "service of process": [SubjectArea.CIVIL_PROCEDURE],

            # General Legal Concepts
            "due process": [SubjectArea.GENERAL],
            "affidavit": [SubjectArea.GENERAL],
            "appeal": [SubjectArea.GENERAL],
            "hearing": [SubjectArea.GENERAL]
        }

    def _initialize_pathway_mappings(self):
        """Initialize learning pathway mappings"""
        self.learning_pathways = {
            SubjectArea.BANKRUPTCY: {
                EducationLevel.BASIC: [
                    "Introduction to Bankruptcy Law",
                    "Types of Bankruptcy (Chapters 7, 11, 13)",
                    "Bankruptcy Process Overview",
                    "Key Terms and Concepts",
                    "When to Consider Bankruptcy"
                ],
                EducationLevel.INTERMEDIATE: [
                    "Detailed Chapter 7 Process",
                    "Chapter 13 Payment Plans",
                    "Automatic Stay Provisions",
                    "Discharge and Non-Dischargeable Debts",
                    "Trustee Roles and Responsibilities"
                ],
                EducationLevel.ADVANCED: [
                    "Complex Bankruptcy Issues",
                    "Business Bankruptcy Considerations",
                    "Appeals and Litigation in Bankruptcy",
                    "Cross-Border Insolvency",
                    "Bankruptcy Planning and Strategy"
                ]
            },

            SubjectArea.CIVIL_PROCEDURE: {
                EducationLevel.BASIC: [
                    "Court System Overview",
                    "How to Start a Lawsuit",
                    "Basic Court Procedures",
                    "Legal Documents and Filings",
                    "Timeline of Civil Cases"
                ],
                EducationLevel.INTERMEDIATE: [
                    "Discovery Process",
                    "Motion Practice",
                    "Pre-Trial Procedures",
                    "Trial Preparation",
                    "Settlement Negotiations"
                ],
                EducationLevel.ADVANCED: [
                    "Complex Motion Practice",
                    "Evidence and Expert Witnesses",
                    "Appeals Process",
                    "Alternative Dispute Resolution",
                    "Federal vs State Procedure Differences"
                ]
            }
        }

    def match_content_to_document(self, document_context: DocumentContext,
                                 user_profile: Optional[UserProfile] = None,
                                 strategy: MatchingStrategy = MatchingStrategy.HYBRID) -> ContextMatchResponse:
        """Match educational content to document context"""
        try:
            self.logger.info(f"Matching content for document: {document_context.document_id}")

            # Generate response ID
            response_id = f"match_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Determine matching strategy
            if strategy == MatchingStrategy.HYBRID:
                primary_matches = self._hybrid_matching(document_context, user_profile)
            elif strategy == MatchingStrategy.DOCUMENT_TYPE_BASED:
                primary_matches = self._document_type_matching(document_context)
            elif strategy == MatchingStrategy.CONTENT_ANALYSIS_BASED:
                primary_matches = self._content_analysis_matching(document_context)
            else:
                primary_matches = self._user_level_matching(document_context, user_profile)

            # Find related content
            related_matches = self._find_related_content(document_context, primary_matches)

            # Get official resources
            official_resources = self._get_contextual_official_resources(document_context)

            # Suggest relevant FAQs
            suggested_faqs = self._suggest_relevant_faqs(document_context)

            # Generate learning pathway
            learning_pathway = self._generate_learning_pathway(document_context, user_profile)

            # Generate next steps
            next_steps = self._generate_next_steps(document_context, user_profile)

            # Determine if attorney consultation required
            attorney_required = self._assess_attorney_consultation_need(document_context)

            response = ContextMatchResponse(
                response_id=response_id,
                document_context=document_context,
                primary_matches=primary_matches[:5],  # Top 5 matches
                related_matches=related_matches[:3],   # Top 3 related
                official_resources=official_resources,
                suggested_faqs=suggested_faqs[:3],     # Top 3 FAQs
                learning_pathway=learning_pathway,
                next_steps=next_steps,
                educational_disclaimers=self.educational_disclaimers,
                attorney_consultation_required=attorney_required
            )

            # Log matching activity
            self._log_matching_activity(document_context, response, user_profile)

            return response

        except Exception as e:
            self.logger.error(f"Content matching failed: {e}")
            return self._create_fallback_response(document_context.document_id, str(e))

    def _hybrid_matching(self, document_context: DocumentContext,
                        user_profile: Optional[UserProfile]) -> List[MatchedContent]:
        """Combine multiple matching strategies"""
        all_matches = []

        # Document type based matching (40% weight)
        doc_matches = self._document_type_matching(document_context)
        for match in doc_matches:
            match.relevance_score *= 0.4
            all_matches.append(match)

        # Content analysis based matching (35% weight)
        content_matches = self._content_analysis_matching(document_context)
        for match in content_matches:
            match.relevance_score *= 0.35
            all_matches.append(match)

        # User level based matching (25% weight)
        if user_profile:
            user_matches = self._user_level_matching(document_context, user_profile)
            for match in user_matches:
                match.relevance_score *= 0.25
                all_matches.append(match)

        # Combine and deduplicate
        combined_matches = {}
        for match in all_matches:
            content_id = match.content.content_id
            if content_id in combined_matches:
                # Combine scores and factors
                existing = combined_matches[content_id]
                existing.relevance_score += match.relevance_score
                existing.matching_factors.extend(match.matching_factors)
                existing.matching_factors = list(set(existing.matching_factors))
            else:
                combined_matches[content_id] = match

        # Sort by combined relevance score
        final_matches = list(combined_matches.values())
        final_matches.sort(key=lambda x: x.relevance_score, reverse=True)

        # Update relevance levels based on final scores
        for match in final_matches:
            if match.relevance_score >= 0.8:
                match.relevance_level = RelevanceLevel.HIGHLY_RELEVANT
            elif match.relevance_score >= 0.6:
                match.relevance_level = RelevanceLevel.RELEVANT
            elif match.relevance_score >= 0.4:
                match.relevance_level = RelevanceLevel.SOMEWHAT_RELEVANT
            else:
                match.relevance_level = RelevanceLevel.BACKGROUND

        return final_matches

    def _document_type_matching(self, document_context: DocumentContext) -> List[MatchedContent]:
        """Match content based on document type"""
        matches = []

        try:
            # Map document type to educational category
            doc_type = document_context.document_type
            edu_category = document_context.educational_category

            # Determine subject areas
            subject_areas = []
            if "bankruptcy" in edu_category.lower():
                subject_areas.append(SubjectArea.BANKRUPTCY)
            if "civil" in edu_category.lower() or "procedure" in edu_category.lower():
                subject_areas.append(SubjectArea.CIVIL_PROCEDURE)
            if not subject_areas:
                subject_areas.append(SubjectArea.GENERAL)

            # Get relevant content types
            content_types = []
            if doc_type in self.document_content_map:
                for subject in subject_areas:
                    if subject in self.document_content_map[doc_type]:
                        content_types.extend(self.document_content_map[doc_type][subject])

            if not content_types:
                content_types = [ContentType.LEGAL_GLOSSARY, ContentType.COURT_PROCEDURE]

            # Create query and search
            query = ContentQuery(
                query_id=f"doc_match_{document_context.document_id}",
                subject_areas=subject_areas,
                content_types=list(set(content_types)),
                education_level=EducationLevel.BASIC,  # Default to basic
                keywords=document_context.key_terms[:5],  # Top 5 concepts
                document_context=document_context.document_type
            )

            # Search content library
            if 'content_library' in globals():
                response = educational_content_library.search_content(query)

                for content in response.matched_content:
                    match = MatchedContent(
                        content=content,
                        relevance_level=RelevanceLevel.RELEVANT,
                        relevance_score=0.8,  # High relevance for type match
                        matching_factors=["document_type_match", "subject_area_match"],
                        educational_pathway=[]
                    )
                    matches.append(match)

        except Exception as e:
            self.logger.error(f"Document type matching failed: {e}")

        return matches

    def _content_analysis_matching(self, document_context: DocumentContext) -> List[MatchedContent]:
        """Match content based on document content analysis"""
        matches = []

        try:
            # Analyze key concepts for subject area mapping
            subject_areas = set()
            for concept in document_context.key_terms:
                concept_lower = concept.lower()
                if concept_lower in self.concept_content_map:
                    subject_areas.update(self.concept_content_map[concept_lower])

            if not subject_areas:
                subject_areas = {SubjectArea.GENERAL}

            # Create concept-based query
            query = ContentQuery(
                query_id=f"content_match_{document_context.document_id}",
                subject_areas=list(subject_areas),
                content_types=[ContentType.LEGAL_GLOSSARY, ContentType.FAQ],
                education_level=EducationLevel.BASIC,
                keywords=document_context.key_terms,
                document_context=f"concepts: {', '.join(document_context.key_terms)}"
            )

            # Search for concept-related content
            if 'content_library' in globals():
                response = educational_content_library.search_content(query)

                for content in response.matched_content:
                    # Calculate concept overlap score
                    concept_overlap = len(set(document_context.key_terms) &
                                        set(content.key_terms)) / max(1, len(content.key_terms))

                    match = MatchedContent(
                        content=content,
                        relevance_level=RelevanceLevel.RELEVANT if concept_overlap > 0.3 else RelevanceLevel.SOMEWHAT_RELEVANT,
                        relevance_score=min(0.9, 0.5 + concept_overlap),
                        matching_factors=["concept_overlap", "keyword_match"],
                        educational_pathway=[]
                    )
                    matches.append(match)

        except Exception as e:
            self.logger.error(f"Content analysis matching failed: {e}")

        return matches

    def _user_level_matching(self, document_context: DocumentContext,
                           user_profile: Optional[UserProfile]) -> List[MatchedContent]:
        """Match content based on user educational level and interests"""
        matches = []

        if not user_profile:
            return matches

        try:
            # Create user-focused query
            query = ContentQuery(
                query_id=f"user_match_{document_context.document_id}",
                subject_areas=user_profile.subject_interests,
                content_types=[ContentType.BANKRUPTCY_INFO, ContentType.COURT_PROCEDURE, ContentType.FAQ],
                education_level=user_profile.experience_level,
                keywords=user_profile.previous_topics + document_context.key_terms[:3],
                user_id=user_profile.user_id
            )

            # Search with user preferences
            if 'content_library' in globals():
                response = educational_content_library.search_content(query)

                for content in response.matched_content:
                    # Adjust score based on user preferences
                    level_match = 1.0 if content.education_level == user_profile.experience_level else 0.7
                    interest_match = 1.0 if content.subject_area in user_profile.subject_interests else 0.5

                    final_score = (level_match + interest_match) / 2

                    match = MatchedContent(
                        content=content,
                        relevance_level=RelevanceLevel.RELEVANT if final_score > 0.7 else RelevanceLevel.SOMEWHAT_RELEVANT,
                        relevance_score=final_score,
                        matching_factors=["education_level_match", "user_interest_match"],
                        educational_pathway=[]
                    )
                    matches.append(match)

        except Exception as e:
            self.logger.error(f"User level matching failed: {e}")

        return matches

    def _find_related_content(self, document_context: DocumentContext,
                            primary_matches: List[MatchedContent]) -> List[MatchedContent]:
        """Find content related to primary matches"""
        related_matches = []

        try:
            # Collect topics from primary matches
            related_topics = set()
            for match in primary_matches:
                related_topics.update(match.content.related_topics)

            # Search for content on related topics
            if related_topics:
                query = ContentQuery(
                    query_id=f"related_{document_context.document_id}",
                    subject_areas=[SubjectArea.GENERAL],
                    content_types=[ContentType.LEGAL_GLOSSARY, ContentType.FAQ],
                    education_level=EducationLevel.BASIC,
                    keywords=list(related_topics)[:5]
                )

                if 'content_library' in globals():
                    response = educational_content_library.search_content(query)

                    for content in response.matched_content:
                        # Avoid duplicates from primary matches
                        if not any(match.content.content_id == content.content_id for match in primary_matches):
                            match = MatchedContent(
                                content=content,
                                relevance_level=RelevanceLevel.BACKGROUND,
                                relevance_score=0.3,
                                matching_factors=["related_topic_match"],
                                educational_pathway=[]
                            )
                            related_matches.append(match)

        except Exception as e:
            self.logger.error(f"Related content search failed: {e}")

        return related_matches

    def _get_contextual_official_resources(self, document_context: DocumentContext) -> List[Dict[str, str]]:
        """Get official resources relevant to document context"""
        resources = []

        # Base government resources
        resources.append({
            "title": "U.S. Courts Official Website",
            "url": "https://www.uscourts.gov",
            "description": "Official federal court information and procedures",
            "relevance": "general"
        })

        # Context-specific resources
        if "bankruptcy" in document_context.educational_category.lower():
            resources.extend([
                {
                    "title": "U.S. Trustee Program",
                    "url": "https://www.justice.gov/ust",
                    "description": "Official bankruptcy administration and trustee information",
                    "relevance": "bankruptcy"
                },
                {
                    "title": "Bankruptcy Forms and Information",
                    "url": "https://www.uscourts.gov/forms/bankruptcy-forms",
                    "description": "Official bankruptcy forms and filing information",
                    "relevance": "bankruptcy"
                }
            ])

        if document_context.document_type in ["motion", "complaint", "answer"]:
            resources.append({
                "title": "Federal Rules of Civil Procedure",
                "url": "https://www.law.cornell.edu/rules/frcp",
                "description": "Official rules governing federal civil cases",
                "relevance": "civil_procedure"
            })

        return resources

    def _suggest_relevant_faqs(self, document_context: DocumentContext) -> List[EducationalContent]:
        """Suggest relevant FAQs based on document context"""
        try:
            # Create FAQ-specific query
            query = ContentQuery(
                query_id=f"faq_{document_context.document_id}",
                subject_areas=[SubjectArea.BANKRUPTCY, SubjectArea.CIVIL_PROCEDURE],
                content_types=[ContentType.FAQ],
                education_level=EducationLevel.BASIC,
                keywords=document_context.key_terms[:3]
            )

            if 'content_library' in globals():
                response = educational_content_library.search_content(query)
                return response.matched_content
            else:
                return []

        except Exception as e:
            self.logger.error(f"FAQ suggestion failed: {e}")
            return []

    def _generate_learning_pathway(self, document_context: DocumentContext,
                                 user_profile: Optional[UserProfile]) -> List[str]:
        """Generate suggested learning pathway"""
        try:
            # Determine subject area
            if "bankruptcy" in document_context.educational_category.lower():
                subject = SubjectArea.BANKRUPTCY
            elif "civil" in document_context.educational_category.lower():
                subject = SubjectArea.CIVIL_PROCEDURE
            else:
                subject = SubjectArea.GENERAL

            # Determine education level
            level = user_profile.experience_level if user_profile else EducationLevel.BASIC

            # Get pathway from mapping
            if subject in self.learning_pathways and level in self.learning_pathways[subject]:
                return self.learning_pathways[subject][level]
            else:
                return [
                    "Understanding Legal Documents",
                    "Basic Legal Procedures",
                    "Key Legal Concepts",
                    "When to Seek Legal Help",
                    "Official Resources and References"
                ]

        except Exception as e:
            self.logger.error(f"Learning pathway generation failed: {e}")
            return ["Consult educational resources and qualified legal counsel"]

    def _generate_next_steps(self, document_context: DocumentContext,
                           user_profile: Optional[UserProfile]) -> List[str]:
        """Generate suggested next steps for learning"""
        next_steps = [
            "Review the educational materials provided above",
            "Study official government resources for accurate information",
            "Consider your specific jurisdiction's requirements"
        ]

        # Context-specific suggestions
        if "bankruptcy" in document_context.educational_category.lower():
            next_steps.extend([
                "Learn about bankruptcy alternatives and consequences",
                "Understand the differences between bankruptcy chapters",
                "Review local bankruptcy court procedures"
            ])

        # Always include attorney consultation
        next_steps.append("Consult with a qualified attorney for legal advice specific to your situation")

        return next_steps

    def _assess_attorney_consultation_need(self, document_context: DocumentContext) -> bool:
        """Assess if attorney consultation is strongly recommended"""
        # High-risk indicators
        risk_indicators = [
            "bankruptcy" in document_context.educational_category.lower(),
            "motion" in document_context.document_type.lower(),
            "petition" in document_context.document_type.lower(),
            document_context.confidence_score < 0.7,  # Low confidence in analysis
            len(document_context.extracted_dates) > 0,  # Time-sensitive content
            len(document_context.complexity_indicators) > 2  # Complex document
        ]

        return sum(risk_indicators) >= 2  # 2 or more risk factors

    def _log_matching_activity(self, document_context: DocumentContext,
                             response: ContextMatchResponse,
                             user_profile: Optional[UserProfile]):
        """Log matching activity for audit and improvement"""
        try:
            # Simple logging for audit trail
            self.logger.info(f"Context matching completed: {response.response_id}")
            self.logger.info(f"Document type: {document_context.document_type}")
            self.logger.info(f"Primary matches: {len(response.primary_matches)}")
            self.logger.info(f"Attorney consultation required: {response.attorney_consultation_required}")

        except Exception as e:
            self.logger.error(f"Matching activity logging failed: {e}")

    def _create_fallback_response(self, document_id: str, error_message: str) -> ContextMatchResponse:
        """Create fallback response when matching fails"""
        return ContextMatchResponse(
            response_id=f"fallback_{document_id}",
            document_context=DocumentContext(
                document_id=document_id,
                document_type="unknown",
                educational_category="general",
                key_terms=[],
                extracted_dates=[],
                extracted_parties=[],
                complexity_indicators=[],
                confidence_score=0.0
            ),
            primary_matches=[],
            related_matches=[],
            official_resources=[
                {
                    "title": "U.S. Courts Official Website",
                    "url": "https://www.uscourts.gov",
                    "description": "Official federal court information",
                    "relevance": "general"
                }
            ],
            suggested_faqs=[],
            learning_pathway=["Consult official legal resources", "Seek qualified legal counsel"],
            next_steps=["Contact a qualified attorney for assistance"],
            educational_disclaimers=self.educational_disclaimers,
            attorney_consultation_required=True
        )

# Global context matcher instance
context_matcher = EducationalContextMatcher()

def validate_context_matcher():
    """Validate educational context matcher"""
    try:
        print("Testing Educational Context Matcher...")

        # Create test document context
        test_context = DocumentContext(
            document_id="test_doc_001",
            document_type="petition",
            educational_category="bankruptcy_procedure",
            key_terms=["chapter 7", "discharge", "automatic stay", "creditors"],
            extracted_dates=["2024-01-15"],
            extracted_parties=["debtor", "trustee"],
            complexity_indicators=["legal terminology", "multiple parties"],
            confidence_score=0.85
        )

        # Create test user profile
        test_user = UserProfile(
            user_id="test_user_001",
            education_level=EducationLevel.BASIC,
            subject_interests=[SubjectArea.BANKRUPTCY],
            previous_topics=["bankruptcy basics"],
            learning_goals=["understand bankruptcy process"],
            time_preferences="detailed_study"
        )

        # Test context matching
        response = context_matcher.match_content_to_document(test_context, test_user)

        print(f"[PASS] Context matching completed: {response.response_id}")
        print(f"   Primary matches: {len(response.primary_matches)}")
        print(f"   Related matches: {len(response.related_matches)}")
        print(f"   Official resources: {len(response.official_resources)}")
        print(f"   Suggested FAQs: {len(response.suggested_faqs)}")
        print(f"   Attorney consultation required: {response.attorney_consultation_required}")

        if response.primary_matches:
            first_match = response.primary_matches[0]
            print(f"   Top match: {first_match.content.title}")
            print(f"   Relevance: {first_match.relevance_level.value}")
            print(f"   Score: {first_match.relevance_score:.2f}")

        print(f"\n[INFO] Learning Pathway:")
        for i, step in enumerate(response.learning_pathway[:3], 1):
            print(f"   {i}. {step}")

        print(f"\n[INFO] Educational Disclaimer:")
        print(f"   {response.educational_disclaimers[0]}")

        return True

    except Exception as e:
        print(f"[FAIL] Context matcher validation failed: {e}")
        return False

class EducationalContextMatcher:
    """Simple context matcher for educational content"""

    def match_content_to_document(self, document_context: DocumentContext,
                                 user_profile: Optional[UserProfile] = None) -> ContextMatchResponse:
        """Match educational content to document context"""
        try:
            # Simple matching using content library
            from .content_library import educational_content_library

            # Create search query based on document context
            query_terms = document_context.content_summary
            if document_context.key_terms:
                query_terms += " " + " ".join(document_context.key_terms[:3])

            # Search for matching content
            search_results = educational_content_library.search_content(
                query=query_terms,
                subject_area="bankruptcy" if "bankruptcy" in query_terms.lower() else "general",
                education_level="beginner"
            )

            # Create response
            matched_content = search_results.matched_content[:5] if hasattr(search_results, 'matched_content') else []

            educational_recommendations = [
                "Review basic legal concepts before proceeding",
                "Consult with qualified attorney for your specific situation",
                "Understand jurisdictional requirements in your area"
            ]

            return ContextMatchResponse(
                matched_content=matched_content,
                confidence_score=0.8,
                educational_recommendations=educational_recommendations,
                related_resources=["State Bar Association", "Legal Aid Organizations"]
            )

        except Exception as e:
            # Return minimal response on error
            return ContextMatchResponse(
                matched_content=[],
                confidence_score=0.0,
                educational_recommendations=["Consult qualified attorney"],
                related_resources=["Local Bar Association"]
            )

# Global context matcher instance
context_matcher = EducationalContextMatcher()

if __name__ == "__main__":
    print("Testing Educational Context Matcher...")
    print("=" * 50)

    if validate_context_matcher():
        print("\nEducational Context Matcher is operational")
    else:
        print("Context matcher validation failed")