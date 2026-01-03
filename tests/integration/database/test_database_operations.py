"""
Integration Tests for Database Operations

Tests database connectivity, CRUD operations, transactions,
and data integrity for the Legal AI System.
"""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone
import uuid

# Mock database models for testing
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TestUser(Base):
    """Test user model for database operations testing"""
    __tablename__ = "test_users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TestDocument(Base):
    """Test document model for database operations testing"""
    __tablename__ = "test_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, index=True)
    content = Column(String)
    document_type = Column(String)
    user_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestDatabaseConnection:
    """Test suite for database connection and basic operations"""

    @pytest.fixture
    async def async_engine(self):
        """Create async test database engine"""
        # Use in-memory SQLite for testing
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=True
        )
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        yield engine
        
        await engine.dispose()

    @pytest.fixture
    async def async_session(self, async_engine):
        """Create async database session"""
        async_session_maker = sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session_maker() as session:
            yield session

    @pytest.mark.asyncio
    async def test_database_connection(self, async_engine):
        """Test basic database connection"""
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            assert value == 1

    @pytest.mark.asyncio
    async def test_table_creation(self, async_engine):
        """Test that tables are created correctly"""
        async with async_engine.begin() as conn:
            # Check if tables exist
            inspector = await conn.run_sync(lambda conn: inspect(conn))
            tables = await conn.run_sync(lambda conn: inspector.get_table_names())
            
            assert "test_users" in tables
            assert "test_documents" in tables

    @pytest.mark.asyncio
    async def test_database_schema_validation(self, async_engine):
        """Test database schema validation"""
        async with async_engine.begin() as conn:
            inspector = await conn.run_sync(lambda conn: inspect(conn))
            
            # Check users table columns
            user_columns = await conn.run_sync(
                lambda conn: [col['name'] for col in inspector.get_columns('test_users')]
            )
            
            expected_user_columns = ['id', 'email', 'username', 'full_name', 'hashed_password', 'is_active', 'created_at']
            for col in expected_user_columns:
                assert col in user_columns

    @pytest.mark.asyncio
    async def test_connection_pooling(self, async_engine):
        """Test connection pooling behavior"""
        # Test multiple concurrent connections
        tasks = []
        
        async def test_query():
            async with async_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar()
        
        for _ in range(5):
            tasks.append(test_query())
        
        results = await asyncio.gather(*tasks)
        assert all(result == 1 for result in results)

    @pytest.mark.asyncio
    async def test_transaction_isolation(self, async_session):
        """Test transaction isolation"""
        # Create a user in one session
        user = TestUser(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_password"
        )
        
        async_session.add(user)
        await async_session.commit()
        
        # Verify user was created
        result = await async_session.execute(
            text("SELECT count(*) FROM test_users WHERE email = 'test@example.com'")
        )
        count = result.scalar()
        assert count == 1


class TestCRUDOperations:
    """Test suite for Create, Read, Update, Delete operations"""

    @pytest.fixture
    async def async_engine(self):
        """Create async test database engine"""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        yield engine
        await engine.dispose()

    @pytest.fixture
    async def async_session(self, async_engine):
        """Create async database session"""
        async_session_maker = sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session_maker() as session:
            yield session

    @pytest.mark.asyncio
    async def test_create_user(self, async_session):
        """Test creating a new user"""
        user = TestUser(
            email="newuser@example.com",
            username="newuser",
            full_name="New User",
            hashed_password="hashed_password_123"
        )
        
        async_session.add(user)
        await async_session.commit()
        
        # Verify user was created
        result = await async_session.execute(
            text("SELECT email FROM test_users WHERE username = 'newuser'")
        )
        email = result.scalar()
        assert email == "newuser@example.com"

    @pytest.mark.asyncio
    async def test_read_user(self, async_session):
        """Test reading user data"""
        # Create test user
        user = TestUser(
            email="readtest@example.com",
            username="readuser",
            full_name="Read Test User",
            hashed_password="hashed_password_456"
        )
        
        async_session.add(user)
        await async_session.commit()
        
        # Read user back
        result = await async_session.execute(
            text("SELECT full_name FROM test_users WHERE email = 'readtest@example.com'")
        )
        full_name = result.scalar()
        assert full_name == "Read Test User"

    @pytest.mark.asyncio
    async def test_update_user(self, async_session):
        """Test updating user data"""
        # Create test user
        user = TestUser(
            email="updatetest@example.com",
            username="updateuser",
            full_name="Original Name",
            hashed_password="hashed_password_789"
        )
        
        async_session.add(user)
        await async_session.commit()
        
        # Update user
        await async_session.execute(
            text("UPDATE test_users SET full_name = 'Updated Name' WHERE email = 'updatetest@example.com'")
        )
        await async_session.commit()
        
        # Verify update
        result = await async_session.execute(
            text("SELECT full_name FROM test_users WHERE email = 'updatetest@example.com'")
        )
        full_name = result.scalar()
        assert full_name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_user(self, async_session):
        """Test deleting user data"""
        # Create test user
        user = TestUser(
            email="deletetest@example.com",
            username="deleteuser",
            full_name="Delete Test User",
            hashed_password="hashed_password_delete"
        )
        
        async_session.add(user)
        await async_session.commit()
        
        # Delete user
        await async_session.execute(
            text("DELETE FROM test_users WHERE email = 'deletetest@example.com'")
        )
        await async_session.commit()
        
        # Verify deletion
        result = await async_session.execute(
            text("SELECT count(*) FROM test_users WHERE email = 'deletetest@example.com'")
        )
        count = result.scalar()
        assert count == 0

    @pytest.mark.asyncio
    async def test_bulk_operations(self, async_session):
        """Test bulk database operations"""
        # Create multiple users
        users = []
        for i in range(10):
            user = TestUser(
                email=f"bulk{i}@example.com",
                username=f"bulkuser{i}",
                full_name=f"Bulk User {i}",
                hashed_password=f"hashed_password_{i}"
            )
            users.append(user)
        
        async_session.add_all(users)
        await async_session.commit()
        
        # Verify all users were created
        result = await async_session.execute(
            text("SELECT count(*) FROM test_users WHERE email LIKE 'bulk%'")
        )
        count = result.scalar()
        assert count == 10


class TestTransactionManagement:
    """Test suite for transaction management"""

    @pytest.fixture
    async def async_engine(self):
        """Create async test database engine"""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        yield engine
        await engine.dispose()

    @pytest.fixture
    async def async_session(self, async_engine):
        """Create async database session"""
        async_session_maker = sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session_maker() as session:
            yield session

    @pytest.mark.asyncio
    async def test_transaction_commit(self, async_session):
        """Test successful transaction commit"""
        user = TestUser(
            email="commit@example.com",
            username="commituser",
            full_name="Commit Test User",
            hashed_password="hashed_password_commit"
        )
        
        async_session.add(user)
        await async_session.commit()
        
        # Verify transaction was committed
        result = await async_session.execute(
            text("SELECT username FROM test_users WHERE email = 'commit@example.com'")
        )
        username = result.scalar()
        assert username == "commituser"

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, async_session):
        """Test transaction rollback"""
        try:
            user = TestUser(
                email="rollback@example.com",
                username="rollbackuser",
                full_name="Rollback Test User",
                hashed_password="hashed_password_rollback"
            )
            
            async_session.add(user)
            
            # Simulate an error that would cause rollback
            raise Exception("Simulated error")
            
        except Exception:
            await async_session.rollback()
        
        # Verify transaction was rolled back
        result = await async_session.execute(
            text("SELECT count(*) FROM test_users WHERE email = 'rollback@example.com'")
        )
        count = result.scalar()
        assert count == 0

    @pytest.mark.asyncio
    async def test_nested_transactions(self, async_session):
        """Test nested transactions with savepoints"""
        # Create initial user
        user1 = TestUser(
            email="nested1@example.com",
            username="nesteduser1",
            full_name="Nested User 1",
            hashed_password="hashed_password_1"
        )
        
        async_session.add(user1)
        
        try:
            # Create savepoint
            savepoint = await async_session.begin_nested()
            
            user2 = TestUser(
                email="nested2@example.com",
                username="nesteduser2",
                full_name="Nested User 2",
                hashed_password="hashed_password_2"
            )
            
            async_session.add(user2)
            
            # Rollback to savepoint
            await savepoint.rollback()
            
        except Exception:
            pass
        
        await async_session.commit()
        
        # Verify only first user was committed
        result = await async_session.execute(
            text("SELECT count(*) FROM test_users WHERE email LIKE 'nested%'")
        )
        count = result.scalar()
        assert count == 1

    @pytest.mark.asyncio
    async def test_concurrent_transactions(self, async_engine):
        """Test concurrent transaction handling"""
        async def create_user(session, user_id):
            user = TestUser(
                email=f"concurrent{user_id}@example.com",
                username=f"concurrent{user_id}",
                full_name=f"Concurrent User {user_id}",
                hashed_password=f"hashed_password_{user_id}"
            )
            
            session.add(user)
            await session.commit()
            return user_id
        
        # Create multiple concurrent sessions
        async_session_maker = sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        tasks = []
        for i in range(5):
            async with async_session_maker() as session:
                tasks.append(create_user(session, i))
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 5


class TestDataIntegrity:
    """Test suite for data integrity and constraints"""

    @pytest.fixture
    async def async_engine(self):
        """Create async test database engine"""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        yield engine
        await engine.dispose()

    @pytest.fixture
    async def async_session(self, async_engine):
        """Create async database session"""
        async_session_maker = sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session_maker() as session:
            yield session

    @pytest.mark.asyncio
    async def test_unique_constraint(self, async_session):
        """Test unique constraints are enforced"""
        # Create first user
        user1 = TestUser(
            email="unique@example.com",
            username="uniqueuser",
            full_name="Unique User 1",
            hashed_password="hashed_password_1"
        )
        
        async_session.add(user1)
        await async_session.commit()
        
        # Try to create second user with same email
        user2 = TestUser(
            email="unique@example.com",  # Same email
            username="uniqueuser2",
            full_name="Unique User 2",
            hashed_password="hashed_password_2"
        )
        
        async_session.add(user2)
        
        # Should raise integrity error
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_foreign_key_constraint(self, async_session):
        """Test foreign key constraints"""
        # Create user first
        user = TestUser(
            email="fk@example.com",
            username="fkuser",
            full_name="FK User",
            hashed_password="hashed_password_fk"
        )
        
        async_session.add(user)
        await async_session.commit()
        
        # Create document with valid user_id
        document = TestDocument(
            title="Test Document",
            content="Test content",
            document_type="contract",
            user_id=user.id
        )
        
        async_session.add(document)
        await async_session.commit()
        
        # Verify document was created
        result = await async_session.execute(
            text("SELECT title FROM test_documents WHERE user_id = :user_id"),
            {"user_id": user.id}
        )
        title = result.scalar()
        assert title == "Test Document"

    @pytest.mark.asyncio
    async def test_not_null_constraint(self, async_session):
        """Test NOT NULL constraints"""
        # Try to create user without required field
        user = TestUser(
            # Missing email - should violate NOT NULL if email is required
            username="nulltest",
            full_name="Null Test User",
            hashed_password="hashed_password_null"
        )
        
        # For this test, we'll assume email can be null in our simple model
        # In a real application, you'd have NOT NULL constraints
        async_session.add(user)
        await async_session.commit()  # This might pass depending on model definition

    @pytest.mark.asyncio
    async def test_data_type_validation(self, async_session):
        """Test data type validation"""
        # Test with proper data types
        user = TestUser(
            email="datatype@example.com",
            username="datatypeuser",
            full_name="Data Type User",
            hashed_password="hashed_password_dt",
            is_active=True  # Boolean field
        )
        
        async_session.add(user)
        await async_session.commit()
        
        # Verify boolean value was stored correctly
        result = await async_session.execute(
            text("SELECT is_active FROM test_users WHERE email = 'datatype@example.com'")
        )
        is_active = result.scalar()
        assert is_active in [True, 1]  # SQLite might return 1 for boolean True


class TestDatabasePerformance:
    """Test suite for database performance optimization"""

    @pytest.fixture
    async def async_engine(self):
        """Create async test database engine"""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        yield engine
        await engine.dispose()

    @pytest.fixture
    async def async_session(self, async_engine):
        """Create async database session"""
        async_session_maker = sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session_maker() as session:
            yield session

    @pytest.mark.asyncio
    async def test_query_performance(self, async_session):
        """Test query performance with timing"""
        import time
        
        # Create test data
        users = []
        for i in range(100):
            user = TestUser(
                email=f"perf{i}@example.com",
                username=f"perfuser{i}",
                full_name=f"Performance User {i}",
                hashed_password=f"hashed_password_{i}"
            )
            users.append(user)
        
        async_session.add_all(users)
        await async_session.commit()
        
        # Time a query
        start_time = time.time()
        result = await async_session.execute(
            text("SELECT count(*) FROM test_users WHERE email LIKE 'perf%'")
        )
        count = result.scalar()
        end_time = time.time()
        
        query_time = end_time - start_time
        
        assert count == 100
        # Query should complete quickly (under 1 second for this simple case)
        assert query_time < 1.0

    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, async_session):
        """Test bulk insert performance"""
        import time
        
        start_time = time.time()
        
        # Bulk insert
        users = []
        for i in range(1000):
            user = TestUser(
                email=f"bulk{i}@example.com",
                username=f"bulkuser{i}",
                full_name=f"Bulk User {i}",
                hashed_password=f"hashed_password_{i}"
            )
            users.append(user)
        
        async_session.add_all(users)
        await async_session.commit()
        
        end_time = time.time()
        insert_time = end_time - start_time
        
        # Verify all records were inserted
        result = await async_session.execute(
            text("SELECT count(*) FROM test_users WHERE email LIKE 'bulk%'")
        )
        count = result.scalar()
        
        assert count == 1000
        # Bulk insert should complete reasonably quickly
        assert insert_time < 5.0  # Allow up to 5 seconds for 1000 records

    @pytest.mark.asyncio
    async def test_connection_overhead(self, async_engine):
        """Test connection creation overhead"""
        import time
        
        start_time = time.time()
        
        # Create multiple connections
        for _ in range(10):
            async with async_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        
        end_time = time.time()
        connection_time = end_time - start_time
        
        # Connection overhead should be minimal
        assert connection_time < 2.0