"""
Database Test Fixtures

Provides database setup, teardown, and data fixtures for testing
the Legal AI System database operations.
"""

import asyncio
import pytest
from typing import AsyncGenerator, Generator, Dict, Any, List, Optional
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, timezone

from .sample_data import (
    SampleData, UserFactory, ClientFactory, DocumentFactory, 
    CaseFactory, AnnotationFactory, BulkDataGenerator
)


class DatabaseFixtures:
    """Container for database-related test fixtures"""
    
    def __init__(self):
        self.test_db_url = "sqlite+aiosqlite:///:memory:"
        self.sync_test_db_url = "sqlite:///test_legal_ai.db"
        self._async_engine = None
        self._sync_engine = None
        self._session_maker = None
        self._async_session_maker = None
    
    @property
    def async_engine(self):
        """Get async database engine"""
        if not self._async_engine:
            self._async_engine = create_async_engine(
                self.test_db_url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=False  # Set to True for SQL debugging
            )
        return self._async_engine
    
    @property
    def sync_engine(self):
        """Get sync database engine"""
        if not self._sync_engine:
            self._sync_engine = create_engine(
                self.sync_test_db_url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=False
            )
        return self._sync_engine
    
    @property
    def async_session_maker(self):
        """Get async session maker"""
        if not self._async_session_maker:
            self._async_session_maker = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._async_session_maker
    
    @property
    def session_maker(self):
        """Get sync session maker"""
        if not self._session_maker:
            self._session_maker = sessionmaker(
                bind=self.sync_engine,
                expire_on_commit=False
            )
        return self._session_maker
    
    async def create_tables(self):
        """Create all database tables"""
        # This would create tables from actual models
        # For testing, we'll create simple tables
        async with self.async_engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR PRIMARY KEY,
                    email VARCHAR UNIQUE NOT NULL,
                    username VARCHAR UNIQUE NOT NULL,
                    full_name VARCHAR,
                    hashed_password VARCHAR NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    role VARCHAR DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    profile JSON
                )
            """))
            
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS clients (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    email VARCHAR,
                    phone VARCHAR,
                    contact_person VARCHAR,
                    industry VARCHAR,
                    user_id VARCHAR,
                    status VARCHAR DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    address JSON,
                    metadata JSON,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS documents (
                    id VARCHAR PRIMARY KEY,
                    title VARCHAR NOT NULL,
                    filename VARCHAR NOT NULL,
                    content TEXT,
                    document_type VARCHAR,
                    mime_type VARCHAR,
                    file_size INTEGER,
                    client_id VARCHAR,
                    uploaded_by VARCHAR,
                    status VARCHAR DEFAULT 'uploaded',
                    language VARCHAR DEFAULT 'en',
                    page_count INTEGER,
                    word_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    metadata JSON,
                    ai_analysis JSON,
                    FOREIGN KEY (client_id) REFERENCES clients (id),
                    FOREIGN KEY (uploaded_by) REFERENCES users (id)
                )
            """))
            
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cases (
                    id VARCHAR PRIMARY KEY,
                    case_number VARCHAR UNIQUE NOT NULL,
                    title VARCHAR NOT NULL,
                    description TEXT,
                    case_type VARCHAR,
                    status VARCHAR DEFAULT 'active',
                    priority VARCHAR DEFAULT 'medium',
                    client_id VARCHAR,
                    assigned_lawyer VARCHAR,
                    court VARCHAR,
                    jurisdiction VARCHAR,
                    practice_area VARCHAR,
                    date_opened TIMESTAMP,
                    date_closed TIMESTAMP,
                    statute_of_limitations TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    parties JSON,
                    financial JSON,
                    timeline JSON,
                    FOREIGN KEY (client_id) REFERENCES clients (id),
                    FOREIGN KEY (assigned_lawyer) REFERENCES users (id)
                )
            """))
            
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS annotations (
                    id VARCHAR PRIMARY KEY,
                    document_id VARCHAR NOT NULL,
                    user_id VARCHAR NOT NULL,
                    type VARCHAR NOT NULL,
                    content TEXT,
                    page_number INTEGER,
                    position JSON,
                    color VARCHAR,
                    category VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSON,
                    FOREIGN KEY (document_id) REFERENCES documents (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS citations (
                    id VARCHAR PRIMARY KEY,
                    citation_text VARCHAR NOT NULL,
                    case_name VARCHAR,
                    court VARCHAR,
                    year INTEGER,
                    volume INTEGER,
                    reporter VARCHAR,
                    page INTEGER,
                    jurisdiction VARCHAR,
                    citation_type VARCHAR,
                    status VARCHAR DEFAULT 'valid',
                    precedential_value VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSON
                )
            """))
    
    async def drop_tables(self):
        """Drop all database tables"""
        async with self.async_engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS annotations"))
            await conn.execute(text("DROP TABLE IF EXISTS citations"))
            await conn.execute(text("DROP TABLE IF EXISTS cases"))
            await conn.execute(text("DROP TABLE IF EXISTS documents"))
            await conn.execute(text("DROP TABLE IF EXISTS clients"))
            await conn.execute(text("DROP TABLE IF EXISTS users"))
    
    async def cleanup(self):
        """Clean up database resources"""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._sync_engine:
            self._sync_engine.dispose()


# =============================================================================
# PYTEST FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_fixtures():
    """Session-scoped database fixtures"""
    fixtures = DatabaseFixtures()
    await fixtures.create_tables()
    yield fixtures
    await fixtures.cleanup()


@pytest.fixture
async def async_db_session(db_fixtures: DatabaseFixtures) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing"""
    async with db_fixtures.async_session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
def sync_db_session(db_fixtures: DatabaseFixtures) -> Generator:
    """Create sync database session for testing"""
    with db_fixtures.session_maker() as session:
        try:
            yield session
        finally:
            session.rollback()
            session.close()


@pytest.fixture
async def clean_database(db_fixtures: DatabaseFixtures):
    """Clean database before and after each test"""
    # Clean before test
    async with db_fixtures.async_engine.begin() as conn:
        await conn.execute(text("DELETE FROM annotations"))
        await conn.execute(text("DELETE FROM citations"))
        await conn.execute(text("DELETE FROM cases"))
        await conn.execute(text("DELETE FROM documents"))
        await conn.execute(text("DELETE FROM clients"))
        await conn.execute(text("DELETE FROM users"))
    
    yield
    
    # Clean after test
    async with db_fixtures.async_engine.begin() as conn:
        await conn.execute(text("DELETE FROM annotations"))
        await conn.execute(text("DELETE FROM citations"))
        await conn.execute(text("DELETE FROM cases"))
        await conn.execute(text("DELETE FROM documents"))
        await conn.execute(text("DELETE FROM clients"))
        await conn.execute(text("DELETE FROM users"))


# =============================================================================
# DATA POPULATION FIXTURES
# =============================================================================

class DataPopulator:
    """Utility class for populating test database with sample data"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def insert_user(self, user_data: Dict[str, Any]) -> str:
        """Insert user and return ID"""
        import json
        
        await self.session.execute(text("""
            INSERT INTO users (
                id, email, username, full_name, hashed_password, 
                is_active, is_verified, role, created_at, updated_at, 
                last_login, profile
            ) VALUES (
                :id, :email, :username, :full_name, :hashed_password,
                :is_active, :is_verified, :role, :created_at, :updated_at,
                :last_login, :profile
            )
        """), {
            **user_data,
            'profile': json.dumps(user_data.get('profile', {})),
            'created_at': user_data['created_at'].isoformat(),
            'updated_at': user_data['updated_at'].isoformat(),
            'last_login': user_data.get('last_login').isoformat() if user_data.get('last_login') else None
        })
        
        await self.session.commit()
        return user_data['id']
    
    async def insert_client(self, client_data: Dict[str, Any]) -> str:
        """Insert client and return ID"""
        import json
        
        await self.session.execute(text("""
            INSERT INTO clients (
                id, name, email, phone, contact_person, industry,
                user_id, status, created_at, updated_at, address, metadata
            ) VALUES (
                :id, :name, :email, :phone, :contact_person, :industry,
                :user_id, :status, :created_at, :updated_at, :address, :metadata
            )
        """), {
            **client_data,
            'address': json.dumps(client_data.get('address', {})),
            'metadata': json.dumps(client_data.get('metadata', {})),
            'created_at': client_data['created_at'].isoformat(),
            'updated_at': client_data['updated_at'].isoformat()
        })
        
        await self.session.commit()
        return client_data['id']
    
    async def insert_document(self, document_data: Dict[str, Any]) -> str:
        """Insert document and return ID"""
        import json
        
        await self.session.execute(text("""
            INSERT INTO documents (
                id, title, filename, content, document_type, mime_type,
                file_size, client_id, uploaded_by, status, language,
                page_count, word_count, created_at, updated_at, processed_at,
                metadata, ai_analysis
            ) VALUES (
                :id, :title, :filename, :content, :document_type, :mime_type,
                :file_size, :client_id, :uploaded_by, :status, :language,
                :page_count, :word_count, :created_at, :updated_at, :processed_at,
                :metadata, :ai_analysis
            )
        """), {
            **document_data,
            'metadata': json.dumps(document_data.get('metadata', {})),
            'ai_analysis': json.dumps(document_data.get('ai_analysis', {})),
            'created_at': document_data['created_at'].isoformat(),
            'updated_at': document_data['updated_at'].isoformat(),
            'processed_at': document_data.get('processed_at').isoformat() if document_data.get('processed_at') else None
        })
        
        await self.session.commit()
        return document_data['id']
    
    async def insert_case(self, case_data: Dict[str, Any]) -> str:
        """Insert case and return ID"""
        import json
        
        await self.session.execute(text("""
            INSERT INTO cases (
                id, case_number, title, description, case_type, status,
                priority, client_id, assigned_lawyer, court, jurisdiction,
                practice_area, date_opened, date_closed, statute_of_limitations,
                created_at, updated_at, parties, financial, timeline
            ) VALUES (
                :id, :case_number, :title, :description, :case_type, :status,
                :priority, :client_id, :assigned_lawyer, :court, :jurisdiction,
                :practice_area, :date_opened, :date_closed, :statute_of_limitations,
                :created_at, :updated_at, :parties, :financial, :timeline
            )
        """), {
            **case_data,
            'parties': json.dumps(case_data.get('parties', {})),
            'financial': json.dumps(case_data.get('financial', {})),
            'timeline': json.dumps(case_data.get('timeline', [])),
            'date_opened': case_data['date_opened'].isoformat(),
            'date_closed': case_data.get('date_closed').isoformat() if case_data.get('date_closed') else None,
            'statute_of_limitations': case_data.get('statute_of_limitations').isoformat() if case_data.get('statute_of_limitations') else None,
            'created_at': case_data['created_at'].isoformat(),
            'updated_at': case_data['updated_at'].isoformat()
        })
        
        await self.session.commit()
        return case_data['id']
    
    async def populate_complete_dataset(self) -> Dict[str, List[str]]:
        """Populate database with complete test dataset"""
        dataset = BulkDataGenerator.create_complete_dataset()
        
        # Insert users first
        user_ids = []
        for user in dataset['users']:
            user_id = await self.insert_user(user)
            user_ids.append(user_id)
        
        # Insert clients
        client_ids = []
        for i, client in enumerate(dataset['clients']):
            # Use actual user IDs
            client['user_id'] = user_ids[i % len(user_ids)]
            client_id = await self.insert_client(client)
            client_ids.append(client_id)
        
        # Insert documents
        document_ids = []
        for i, document in enumerate(dataset['documents']):
            # Use actual client and user IDs
            document['client_id'] = client_ids[i % len(client_ids)]
            document['uploaded_by'] = user_ids[i % len(user_ids)]
            document_id = await self.insert_document(document)
            document_ids.append(document_id)
        
        # Insert cases
        case_ids = []
        for i, case in enumerate(dataset['cases']):
            # Use actual client and user IDs
            case['client_id'] = client_ids[i % len(client_ids)]
            case['assigned_lawyer'] = user_ids[i % len(user_ids)]
            case_id = await self.insert_case(case)
            case_ids.append(case_id)
        
        return {
            'user_ids': user_ids,
            'client_ids': client_ids,
            'document_ids': document_ids,
            'case_ids': case_ids
        }


@pytest.fixture
async def sample_user(async_db_session: AsyncSession) -> Dict[str, Any]:
    """Create a sample user in the database"""
    populator = DataPopulator(async_db_session)
    user_data = SampleData.create_user_data()
    user_id = await populator.insert_user(user_data)
    user_data['id'] = user_id
    return user_data


@pytest.fixture
async def sample_client(async_db_session: AsyncSession, sample_user: Dict[str, Any]) -> Dict[str, Any]:
    """Create a sample client in the database"""
    populator = DataPopulator(async_db_session)
    client_data = SampleData.create_client_data(user_id=sample_user['id'])
    client_id = await populator.insert_client(client_data)
    client_data['id'] = client_id
    return client_data


@pytest.fixture
async def sample_document(
    async_db_session: AsyncSession,
    sample_client: Dict[str, Any],
    sample_user: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a sample document in the database"""
    populator = DataPopulator(async_db_session)
    document_data = SampleData.create_document_data(
        client_id=sample_client['id'],
        user_id=sample_user['id']
    )
    document_id = await populator.insert_document(document_data)
    document_data['id'] = document_id
    return document_data


@pytest.fixture
async def sample_case(
    async_db_session: AsyncSession,
    sample_client: Dict[str, Any],
    sample_user: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a sample case in the database"""
    populator = DataPopulator(async_db_session)
    case_data = SampleData.create_case_data(
        client_id=sample_client['id'],
        user_id=sample_user['id']
    )
    case_id = await populator.insert_case(case_data)
    case_data['id'] = case_id
    return case_data


@pytest.fixture
async def populated_database(async_db_session: AsyncSession, clean_database) -> Dict[str, List[str]]:
    """Populate database with complete test dataset"""
    populator = DataPopulator(async_db_session)
    return await populator.populate_complete_dataset()


@pytest.fixture
async def multiple_users(async_db_session: AsyncSession, clean_database) -> List[Dict[str, Any]]:
    """Create multiple users in the database"""
    populator = DataPopulator(async_db_session)
    users = BulkDataGenerator.create_users(5)
    
    user_ids = []
    for user in users:
        user_id = await populator.insert_user(user)
        user['id'] = user_id
        user_ids.append(user_id)
    
    return users


@pytest.fixture
async def multiple_documents(
    async_db_session: AsyncSession,
    sample_client: Dict[str, Any],
    sample_user: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Create multiple documents in the database"""
    populator = DataPopulator(async_db_session)
    documents = BulkDataGenerator.create_documents(
        count=10,
        client_ids=[sample_client['id']],
        user_ids=[sample_user['id']]
    )
    
    document_ids = []
    for document in documents:
        document_id = await populator.insert_document(document)
        document['id'] = document_id
        document_ids.append(document_id)
    
    return documents


# =============================================================================
# SPECIALIZED FIXTURES
# =============================================================================

@pytest.fixture
async def legal_test_scenarios(async_db_session: AsyncSession, clean_database) -> Dict[str, Any]:
    """Create specialized legal test scenarios"""
    from .sample_data import LegalTestData
    
    populator = DataPopulator(async_db_session)
    
    # Create a user and client for the scenarios
    user_data = SampleData.create_user_data(role="lawyer")
    user_id = await populator.insert_user(user_data)
    
    client_data = SampleData.create_client_data(user_id=user_id)
    client_id = await populator.insert_client(client_data)
    
    # Create contract documents
    contract_docs = LegalTestData.contract_documents()
    contract_ids = []
    for doc in contract_docs:
        doc['client_id'] = client_id
        doc['uploaded_by'] = user_id
        doc_id = await populator.insert_document(doc)
        contract_ids.append(doc_id)
    
    # Create litigation documents
    litigation_docs = LegalTestData.litigation_documents()
    litigation_ids = []
    for doc in litigation_docs:
        doc['client_id'] = client_id
        doc['uploaded_by'] = user_id
        doc_id = await populator.insert_document(doc)
        litigation_ids.append(doc_id)
    
    # Create complex case
    complex_case = LegalTestData.complex_case_with_timeline()
    complex_case['client_id'] = client_id
    complex_case['assigned_lawyer'] = user_id
    case_id = await populator.insert_case(complex_case)
    
    return {
        'user_id': user_id,
        'client_id': client_id,
        'contract_document_ids': contract_ids,
        'litigation_document_ids': litigation_ids,
        'complex_case_id': case_id
    }


@pytest.fixture
async def performance_test_data(async_db_session: AsyncSession, clean_database) -> Dict[str, Any]:
    """Create large dataset for performance testing"""
    populator = DataPopulator(async_db_session)
    
    # Create many users
    users = BulkDataGenerator.create_users(50)
    user_ids = []
    for user in users:
        user_id = await populator.insert_user(user)
        user_ids.append(user_id)
    
    # Create many clients
    clients = BulkDataGenerator.create_clients(20, user_ids)
    client_ids = []
    for client in clients:
        client_id = await populator.insert_client(client)
        client_ids.append(client_id)
    
    # Create many documents
    documents = BulkDataGenerator.create_documents(200, client_ids, user_ids)
    document_ids = []
    for document in documents:
        document_id = await populator.insert_document(document)
        document_ids.append(document_id)
    
    return {
        'user_count': len(user_ids),
        'client_count': len(client_ids),
        'document_count': len(document_ids),
        'user_ids': user_ids,
        'client_ids': client_ids,
        'document_ids': document_ids
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def verify_database_state(session: AsyncSession) -> Dict[str, int]:
    """Verify current database state by counting records"""
    counts = {}
    
    tables = ['users', 'clients', 'documents', 'cases', 'annotations', 'citations']
    
    for table in tables:
        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        counts[table] = result.scalar()
    
    return counts


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[Dict[str, Any]]:
    """Get user by email address"""
    result = await session.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": email}
    )
    row = result.fetchone()
    return dict(row._mapping) if row else None


async def get_documents_by_client(session: AsyncSession, client_id: str) -> List[Dict[str, Any]]:
    """Get all documents for a client"""
    result = await session.execute(
        text("SELECT * FROM documents WHERE client_id = :client_id ORDER BY created_at DESC"),
        {"client_id": client_id}
    )
    return [dict(row._mapping) for row in result.fetchall()]


async def get_cases_by_status(session: AsyncSession, status: str) -> List[Dict[str, Any]]:
    """Get all cases with specific status"""
    result = await session.execute(
        text("SELECT * FROM cases WHERE status = :status ORDER BY created_at DESC"),
        {"status": status}
    )
    return [dict(row._mapping) for row in result.fetchall()]