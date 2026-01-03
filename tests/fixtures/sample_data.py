"""
Test Fixtures and Sample Data

Provides comprehensive test data fixtures for the Legal AI System
including users, documents, cases, and legal entities.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from factory import Factory, Faker, SubFactory, LazyAttribute, Sequence
from factory.alchemy import SQLAlchemyModelFactory
import factory.fuzzy


# =============================================================================
# BASIC DATA FIXTURES
# =============================================================================

class SampleData:
    """Container for sample test data"""
    
    @staticmethod
    def create_user_data(
        email: Optional[str] = None,
        username: Optional[str] = None,
        role: str = "user"
    ) -> Dict[str, Any]:
        """Create sample user data"""
        return {
            "id": str(uuid.uuid4()),
            "email": email or f"user{uuid.uuid4().hex[:8]}@example.com",
            "username": username or f"user_{uuid.uuid4().hex[:8]}",
            "full_name": Faker('name').generate(),
            "hashed_password": "$2b$12$example_hash",
            "is_active": True,
            "is_verified": True,
            "role": role,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc) - timedelta(hours=1),
            "profile": {
                "bio": "Test user profile",
                "organization": "Test Law Firm",
                "bar_number": "123456789",
                "practice_areas": ["Corporate Law", "Litigation"]
            }
        }
    
    @staticmethod
    def create_client_data(user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create sample client data"""
        return {
            "id": str(uuid.uuid4()),
            "name": Faker('company').generate(),
            "email": Faker('company_email').generate(),
            "phone": Faker('phone_number').generate(),
            "address": {
                "street": Faker('street_address').generate(),
                "city": Faker('city').generate(),
                "state": Faker('state').generate(),
                "zip_code": Faker('zipcode').generate()
            },
            "contact_person": Faker('name').generate(),
            "industry": Faker('bs').generate(),
            "user_id": user_id or str(uuid.uuid4()),
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "metadata": {
                "source": "manual_entry",
                "referral": "website",
                "value_tier": "standard"
            }
        }
    
    @staticmethod
    def create_document_data(
        client_id: Optional[str] = None,
        user_id: Optional[str] = None,
        document_type: str = "contract"
    ) -> Dict[str, Any]:
        """Create sample document data"""
        return {
            "id": str(uuid.uuid4()),
            "title": f"Sample {document_type.title()} Document",
            "filename": f"sample_{document_type}_{uuid.uuid4().hex[:8]}.pdf",
            "content": f"This is sample content for a {document_type} document. " * 50,
            "document_type": document_type,
            "mime_type": "application/pdf",
            "file_size": 1024 * 50,  # 50KB
            "client_id": client_id or str(uuid.uuid4()),
            "uploaded_by": user_id or str(uuid.uuid4()),
            "status": "processed",
            "language": "en",
            "page_count": 15,
            "word_count": 850,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "processed_at": datetime.now(timezone.utc),
            "metadata": {
                "source": "manual_upload",
                "confidence_score": 0.95,
                "processing_duration": 12.5,
                "extracted_entities": ["Party A", "Party B", "Effective Date"],
                "key_terms": ["liability", "indemnification", "termination"]
            },
            "ai_analysis": {
                "summary": "This document outlines the terms and conditions...",
                "key_clauses": [
                    {
                        "type": "liability",
                        "content": "Party A shall not be liable...",
                        "risk_level": "medium"
                    },
                    {
                        "type": "termination", 
                        "content": "Either party may terminate...",
                        "risk_level": "low"
                    }
                ],
                "compliance_flags": [],
                "suggestions": [
                    "Consider adding force majeure clause",
                    "Review governing law section"
                ]
            }
        }
    
    @staticmethod
    def create_case_data(
        client_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: str = "active"
    ) -> Dict[str, Any]:
        """Create sample case data"""
        case_number = f"CASE-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
        
        return {
            "id": str(uuid.uuid4()),
            "case_number": case_number,
            "title": f"Sample Legal Case - {case_number}",
            "description": "This is a sample legal case for testing purposes.",
            "case_type": "civil_litigation",
            "status": status,
            "priority": "medium",
            "client_id": client_id or str(uuid.uuid4()),
            "assigned_lawyer": user_id or str(uuid.uuid4()),
            "court": "Superior Court of California",
            "jurisdiction": "california",
            "practice_area": "Commercial Litigation",
            "date_opened": datetime.now(timezone.utc),
            "date_closed": None if status == "active" else datetime.now(timezone.utc),
            "statute_of_limitations": datetime.now(timezone.utc) + timedelta(days=365),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "parties": {
                "plaintiffs": [
                    {
                        "name": "ABC Corporation",
                        "type": "corporation",
                        "role": "plaintiff"
                    }
                ],
                "defendants": [
                    {
                        "name": "XYZ LLC",
                        "type": "llc", 
                        "role": "defendant"
                    }
                ]
            },
            "financial": {
                "damages_sought": 500000.00,
                "estimated_legal_fees": 75000.00,
                "retainer_amount": 25000.00,
                "billing_rate": 450.00
            },
            "timeline": [
                {
                    "date": datetime.now(timezone.utc) - timedelta(days=30),
                    "event": "Case opened",
                    "description": "Initial client consultation and case assessment"
                },
                {
                    "date": datetime.now(timezone.utc) - timedelta(days=20),
                    "event": "Complaint filed",
                    "description": "Filed complaint with court"
                }
            ]
        }
    
    @staticmethod
    def create_annotation_data(
        document_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create sample annotation data"""
        return {
            "id": str(uuid.uuid4()),
            "document_id": document_id,
            "user_id": user_id or str(uuid.uuid4()),
            "type": "highlight",
            "content": "Important clause requiring attention",
            "page_number": 1,
            "position": {
                "x": 150.5,
                "y": 200.75,
                "width": 300.0,
                "height": 25.0
            },
            "color": "#ffeb3b",
            "category": "key_term",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "metadata": {
                "confidence": 0.92,
                "auto_generated": False,
                "tags": ["important", "review_needed"]
            }
        }
    
    @staticmethod
    def create_citation_data() -> Dict[str, Any]:
        """Create sample legal citation data"""
        return {
            "id": str(uuid.uuid4()),
            "citation_text": "Smith v. Jones, 123 F.3d 456 (9th Cir. 2023)",
            "case_name": "Smith v. Jones",
            "court": "United States Court of Appeals for the Ninth Circuit",
            "year": 2023,
            "volume": 123,
            "reporter": "F.3d",
            "page": 456,
            "jurisdiction": "federal",
            "citation_type": "case_law",
            "status": "valid",
            "precedential_value": "binding",
            "created_at": datetime.now(timezone.utc),
            "metadata": {
                "bluebook_format": "Smith v. Jones, 123 F.3d 456 (9th Cir. 2023)",
                "topic_areas": ["Contract Law", "Commercial Disputes"],
                "key_holdings": [
                    "Parties must perform contractual obligations in good faith",
                    "Material breach excuses non-breaching party performance"
                ]
            }
        }


# =============================================================================
# FACTORY CLASSES FOR AUTOMATED DATA GENERATION
# =============================================================================

class BaseFactory(Factory):
    """Base factory with common attributes"""
    id = LazyAttribute(lambda obj: str(uuid.uuid4()))
    created_at = factory.fuzzy.FuzzyDateTime(
        datetime.now(timezone.utc) - timedelta(days=30),
        datetime.now(timezone.utc)
    )
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)


class UserFactory(BaseFactory):
    """Factory for creating test users"""
    class Meta:
        model = dict
    
    email = Faker('email')
    username = Sequence(lambda n: f"user_{n}")
    full_name = Faker('name')
    hashed_password = "$2b$12$example_hash"
    is_active = True
    is_verified = True
    role = factory.fuzzy.FuzzyChoice(['user', 'lawyer', 'admin', 'client'])
    last_login = factory.fuzzy.FuzzyDateTime(
        datetime.now(timezone.utc) - timedelta(days=7),
        datetime.now(timezone.utc)
    )
    
    @factory.lazy_attribute
    def profile(self):
        return {
            "bio": Faker('text').generate(),
            "organization": Faker('company').generate(),
            "bar_number": Faker('numerify', text='#########').generate(),
            "practice_areas": factory.fuzzy.FuzzyChoice([
                ["Corporate Law", "M&A"],
                ["Litigation", "Civil Rights"],
                ["Real Estate", "Property Law"],
                ["Family Law", "Divorce"],
                ["Criminal Defense"]
            ]).fuzz()
        }


class ClientFactory(BaseFactory):
    """Factory for creating test clients"""
    class Meta:
        model = dict
    
    name = Faker('company')
    email = Faker('company_email')
    phone = Faker('phone_number')
    contact_person = Faker('name')
    industry = Faker('bs')
    status = factory.fuzzy.FuzzyChoice(['active', 'inactive', 'prospect'])
    user_id = LazyAttribute(lambda obj: str(uuid.uuid4()))
    
    @factory.lazy_attribute
    def address(self):
        return {
            "street": Faker('street_address').generate(),
            "city": Faker('city').generate(),
            "state": Faker('state').generate(),
            "zip_code": Faker('zipcode').generate()
        }
    
    @factory.lazy_attribute
    def metadata(self):
        return {
            "source": factory.fuzzy.FuzzyChoice([
                'manual_entry', 'website', 'referral', 'marketing'
            ]).fuzz(),
            "value_tier": factory.fuzzy.FuzzyChoice([
                'standard', 'premium', 'enterprise'
            ]).fuzz()
        }


class DocumentFactory(BaseFactory):
    """Factory for creating test documents"""
    class Meta:
        model = dict
    
    title = Faker('sentence', nb_words=4)
    filename = LazyAttribute(lambda obj: f"{obj.title.lower().replace(' ', '_')}.pdf")
    content = Faker('text', max_nb_chars=2000)
    document_type = factory.fuzzy.FuzzyChoice([
        'contract', 'brief', 'memorandum', 'motion', 'pleading', 'correspondence'
    ])
    mime_type = 'application/pdf'
    file_size = factory.fuzzy.FuzzyInteger(1024, 1024*1024*5)  # 1KB to 5MB
    status = factory.fuzzy.FuzzyChoice(['uploaded', 'processing', 'processed', 'failed'])
    language = 'en'
    page_count = factory.fuzzy.FuzzyInteger(1, 50)
    word_count = factory.fuzzy.FuzzyInteger(100, 5000)
    client_id = LazyAttribute(lambda obj: str(uuid.uuid4()))
    uploaded_by = LazyAttribute(lambda obj: str(uuid.uuid4()))
    processed_at = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(minutes=5) if obj.status == 'processed' else None
    )
    
    @factory.lazy_attribute
    def metadata(self):
        return {
            "source": "manual_upload",
            "confidence_score": factory.fuzzy.FuzzyFloat(0.7, 0.99).fuzz(),
            "processing_duration": factory.fuzzy.FuzzyFloat(1.0, 30.0).fuzz(),
            "extracted_entities": Faker('words', nb=5).generate(),
            "key_terms": Faker('words', nb=8).generate()
        }
    
    @factory.lazy_attribute
    def ai_analysis(self):
        return {
            "summary": Faker('paragraph').generate(),
            "key_clauses": [
                {
                    "type": "liability",
                    "content": Faker('sentence').generate(),
                    "risk_level": factory.fuzzy.FuzzyChoice(['low', 'medium', 'high']).fuzz()
                }
            ],
            "compliance_flags": [],
            "suggestions": [
                Faker('sentence').generate(),
                Faker('sentence').generate()
            ]
        }


class CaseFactory(BaseFactory):
    """Factory for creating test cases"""
    class Meta:
        model = dict
    
    case_number = Sequence(lambda n: f"CASE-{datetime.now().year}-{n:06d}")
    title = Faker('sentence', nb_words=6)
    description = Faker('paragraph')
    case_type = factory.fuzzy.FuzzyChoice([
        'civil_litigation', 'criminal_defense', 'family_law', 
        'corporate', 'real_estate', 'employment'
    ])
    status = factory.fuzzy.FuzzyChoice(['active', 'closed', 'on_hold', 'archived'])
    priority = factory.fuzzy.FuzzyChoice(['low', 'medium', 'high', 'urgent'])
    court = Faker('city')
    jurisdiction = factory.fuzzy.FuzzyChoice([
        'federal', 'state', 'local', 'international'
    ])
    practice_area = factory.fuzzy.FuzzyChoice([
        'Commercial Litigation', 'Corporate Law', 'Family Law',
        'Criminal Defense', 'Real Estate', 'Employment Law'
    ])
    date_opened = factory.fuzzy.FuzzyDateTime(
        datetime.now(timezone.utc) - timedelta(days=365),
        datetime.now(timezone.utc)
    )
    client_id = LazyAttribute(lambda obj: str(uuid.uuid4()))
    assigned_lawyer = LazyAttribute(lambda obj: str(uuid.uuid4()))
    
    @factory.lazy_attribute
    def date_closed(self):
        return (
            factory.fuzzy.FuzzyDateTime(
                self.date_opened,
                datetime.now(timezone.utc)
            ).fuzz() if self.status == 'closed' else None
        )
    
    @factory.lazy_attribute
    def statute_of_limitations(self):
        return self.date_opened + timedelta(days=factory.fuzzy.FuzzyInteger(365, 1095).fuzz())
    
    @factory.lazy_attribute
    def parties(self):
        return {
            "plaintiffs": [
                {
                    "name": Faker('company').generate(),
                    "type": "corporation",
                    "role": "plaintiff"
                }
            ],
            "defendants": [
                {
                    "name": Faker('company').generate(),
                    "type": "corporation",
                    "role": "defendant"
                }
            ]
        }
    
    @factory.lazy_attribute
    def financial(self):
        return {
            "damages_sought": factory.fuzzy.FuzzyFloat(10000, 1000000).fuzz(),
            "estimated_legal_fees": factory.fuzzy.FuzzyFloat(5000, 100000).fuzz(),
            "retainer_amount": factory.fuzzy.FuzzyFloat(2500, 50000).fuzz(),
            "billing_rate": factory.fuzzy.FuzzyFloat(200, 800).fuzz()
        }


class AnnotationFactory(BaseFactory):
    """Factory for creating test annotations"""
    class Meta:
        model = dict
    
    document_id = LazyAttribute(lambda obj: str(uuid.uuid4()))
    user_id = LazyAttribute(lambda obj: str(uuid.uuid4()))
    type = factory.fuzzy.FuzzyChoice(['highlight', 'note', 'bookmark', 'redaction'])
    content = Faker('sentence')
    page_number = factory.fuzzy.FuzzyInteger(1, 20)
    color = factory.fuzzy.FuzzyChoice(['#ffeb3b', '#4caf50', '#f44336', '#2196f3'])
    category = factory.fuzzy.FuzzyChoice([
        'key_term', 'important', 'review_needed', 'action_item', 'question'
    ])
    
    @factory.lazy_attribute
    def position(self):
        return {
            "x": factory.fuzzy.FuzzyFloat(0, 500).fuzz(),
            "y": factory.fuzzy.FuzzyFloat(0, 700).fuzz(),
            "width": factory.fuzzy.FuzzyFloat(100, 400).fuzz(),
            "height": factory.fuzzy.FuzzyFloat(20, 100).fuzz()
        }
    
    @factory.lazy_attribute
    def metadata(self):
        return {
            "confidence": factory.fuzzy.FuzzyFloat(0.7, 1.0).fuzz(),
            "auto_generated": factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
            "tags": Faker('words', nb=3).generate()
        }


class CitationFactory(BaseFactory):
    """Factory for creating test legal citations"""
    class Meta:
        model = dict
    
    case_name = LazyAttribute(lambda obj: f"{Faker('last_name').generate()} v. {Faker('last_name').generate()}")
    court = factory.fuzzy.FuzzyChoice([
        "Supreme Court of the United States",
        "United States Court of Appeals for the Ninth Circuit",
        "United States District Court",
        "Superior Court of California"
    ])
    year = factory.fuzzy.FuzzyInteger(1990, 2023)
    volume = factory.fuzzy.FuzzyInteger(1, 999)
    reporter = factory.fuzzy.FuzzyChoice(['F.3d', 'F.2d', 'U.S.', 'Cal.App.4th'])
    page = factory.fuzzy.FuzzyInteger(1, 9999)
    jurisdiction = factory.fuzzy.FuzzyChoice(['federal', 'state', 'local'])
    citation_type = factory.fuzzy.FuzzyChoice(['case_law', 'statute', 'regulation'])
    status = factory.fuzzy.FuzzyChoice(['valid', 'superseded', 'overturned'])
    precedential_value = factory.fuzzy.FuzzyChoice(['binding', 'persuasive', 'informational'])
    
    @factory.lazy_attribute
    def citation_text(self):
        return f"{self.case_name}, {self.volume} {self.reporter} {self.page} ({self.court.split()[-1]} {self.year})"
    
    @factory.lazy_attribute
    def metadata(self):
        return {
            "bluebook_format": self.citation_text,
            "topic_areas": Faker('words', nb=2).generate(),
            "key_holdings": [
                Faker('sentence').generate(),
                Faker('sentence').generate()
            ]
        }


# =============================================================================
# BULK DATA GENERATORS
# =============================================================================

class BulkDataGenerator:
    """Utility class for generating bulk test data"""
    
    @staticmethod
    def create_users(count: int = 10) -> List[Dict[str, Any]]:
        """Generate multiple users"""
        return [UserFactory() for _ in range(count)]
    
    @staticmethod
    def create_clients(count: int = 5, user_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Generate multiple clients"""
        clients = []
        for i in range(count):
            user_id = user_ids[i % len(user_ids)] if user_ids else str(uuid.uuid4())
            clients.append(ClientFactory(user_id=user_id))
        return clients
    
    @staticmethod
    def create_documents(
        count: int = 20,
        client_ids: Optional[List[str]] = None,
        user_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generate multiple documents"""
        documents = []
        for i in range(count):
            client_id = client_ids[i % len(client_ids)] if client_ids else str(uuid.uuid4())
            user_id = user_ids[i % len(user_ids)] if user_ids else str(uuid.uuid4())
            documents.append(DocumentFactory(client_id=client_id, uploaded_by=user_id))
        return documents
    
    @staticmethod
    def create_cases(
        count: int = 8,
        client_ids: Optional[List[str]] = None,
        user_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generate multiple cases"""
        cases = []
        for i in range(count):
            client_id = client_ids[i % len(client_ids)] if client_ids else str(uuid.uuid4())
            user_id = user_ids[i % len(user_ids)] if user_ids else str(uuid.uuid4())
            cases.append(CaseFactory(client_id=client_id, assigned_lawyer=user_id))
        return cases
    
    @staticmethod
    def create_complete_dataset() -> Dict[str, List[Dict[str, Any]]]:
        """Generate a complete dataset with relationships"""
        # Generate users first
        users = BulkDataGenerator.create_users(10)
        user_ids = [user['id'] for user in users]
        
        # Generate clients
        clients = BulkDataGenerator.create_clients(5, user_ids)
        client_ids = [client['id'] for client in clients]
        
        # Generate documents
        documents = BulkDataGenerator.create_documents(20, client_ids, user_ids)
        document_ids = [doc['id'] for doc in documents]
        
        # Generate cases
        cases = BulkDataGenerator.create_cases(8, client_ids, user_ids)
        
        # Generate annotations
        annotations = []
        for doc_id in document_ids[:10]:  # Annotate half the documents
            for _ in range(factory.fuzzy.FuzzyInteger(1, 5).fuzz()):
                annotations.append(AnnotationFactory(
                    document_id=doc_id,
                    user_id=factory.fuzzy.FuzzyChoice(user_ids).fuzz()
                ))
        
        # Generate citations
        citations = [CitationFactory() for _ in range(15)]
        
        return {
            "users": users,
            "clients": clients,
            "documents": documents,
            "cases": cases,
            "annotations": annotations,
            "citations": citations
        }


# =============================================================================
# SPECIALIZED TEST DATA
# =============================================================================

class LegalTestData:
    """Specialized test data for legal-specific scenarios"""
    
    @staticmethod
    def contract_documents() -> List[Dict[str, Any]]:
        """Generate contract-specific documents"""
        contract_types = [
            'employment_agreement', 'nda', 'service_agreement',
            'lease_agreement', 'merger_agreement', 'licensing_agreement'
        ]
        
        contracts = []
        for contract_type in contract_types:
            doc = DocumentFactory(
                document_type='contract',
                title=f"Sample {contract_type.replace('_', ' ').title()}",
                metadata={
                    "contract_type": contract_type,
                    "parties_count": factory.fuzzy.FuzzyInteger(2, 5).fuzz(),
                    "jurisdiction": factory.fuzzy.FuzzyChoice([
                        'california', 'new_york', 'delaware', 'texas'
                    ]).fuzz(),
                    "governing_law": factory.fuzzy.FuzzyChoice([
                        'California', 'New York', 'Delaware', 'Texas'
                    ]).fuzz()
                }
            )
            contracts.append(doc)
        
        return contracts
    
    @staticmethod
    def litigation_documents() -> List[Dict[str, Any]]:
        """Generate litigation-specific documents"""
        litigation_types = [
            'complaint', 'answer', 'motion_to_dismiss', 'discovery_request',
            'deposition', 'expert_report', 'brief', 'judgment'
        ]
        
        litigation_docs = []
        for lit_type in litigation_types:
            doc = DocumentFactory(
                document_type=lit_type,
                title=f"Sample {lit_type.replace('_', ' ').title()}",
                metadata={
                    "litigation_stage": factory.fuzzy.FuzzyChoice([
                        'pleading', 'discovery', 'pre_trial', 'trial', 'post_trial'
                    ]).fuzz(),
                    "court_level": factory.fuzzy.FuzzyChoice([
                        'district', 'appellate', 'supreme'
                    ]).fuzz(),
                    "filing_deadline": (
                        datetime.now(timezone.utc) + timedelta(days=30)
                    ).isoformat()
                }
            )
            litigation_docs.append(doc)
        
        return litigation_docs
    
    @staticmethod
    def complex_case_with_timeline() -> Dict[str, Any]:
        """Generate a complex case with detailed timeline"""
        case = CaseFactory(
            case_type='civil_litigation',
            status='active',
            priority='high'
        )
        
        # Add detailed timeline
        case['timeline'] = [
            {
                "date": (datetime.now(timezone.utc) - timedelta(days=180)).isoformat(),
                "event": "Initial client consultation",
                "description": "Met with client to discuss potential litigation",
                "type": "consultation"
            },
            {
                "date": (datetime.now(timezone.utc) - timedelta(days=150)).isoformat(),
                "event": "Complaint filed",
                "description": "Filed complaint with court and served defendant",
                "type": "filing"
            },
            {
                "date": (datetime.now(timezone.utc) - timedelta(days=120)).isoformat(),
                "event": "Answer received",
                "description": "Defendant filed answer and counterclaims",
                "type": "filing"
            },
            {
                "date": (datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),
                "event": "Discovery commenced",
                "description": "Began discovery process with document requests",
                "type": "discovery"
            },
            {
                "date": (datetime.now(timezone.utc) - timedelta(days=60)).isoformat(),
                "event": "Depositions scheduled",
                "description": "Scheduled key witness depositions",
                "type": "discovery"
            },
            {
                "date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "event": "Mediation scheduled",
                "description": "Court-ordered mediation session",
                "type": "mediation"
            },
            {
                "date": (datetime.now(timezone.utc) + timedelta(days=120)).isoformat(),
                "event": "Trial date",
                "description": "Jury trial scheduled to begin",
                "type": "trial"
            }
        ]
        
        return case


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def get_sample_user() -> Dict[str, Any]:
    """Get a single sample user"""
    return SampleData.create_user_data()


def get_sample_document() -> Dict[str, Any]:
    """Get a single sample document"""
    return SampleData.create_document_data()


def get_sample_case() -> Dict[str, Any]:
    """Get a single sample case"""
    return SampleData.create_case_data()


def get_complete_test_dataset() -> Dict[str, List[Dict[str, Any]]]:
    """Get complete test dataset with all entity types"""
    return BulkDataGenerator.create_complete_dataset()


def get_legal_test_scenarios() -> Dict[str, List[Dict[str, Any]]]:
    """Get specialized legal test scenarios"""
    return {
        "contracts": LegalTestData.contract_documents(),
        "litigation": LegalTestData.litigation_documents(),
        "complex_case": [LegalTestData.complex_case_with_timeline()]
    }