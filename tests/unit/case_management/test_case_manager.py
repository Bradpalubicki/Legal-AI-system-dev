"""
Unit tests for case management system.

Tests the core case management functionality including case creation,
updates, document associations, timeline tracking, and status management.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any, Optional
import uuid

from src.case_management.case_manager import CaseManager
from src.case_management.models import Case, CaseStatus, CaseType, CaseDocument, CaseEvent
from src.case_management.exceptions import CaseNotFoundError, InvalidCaseStatusError, DuplicateCaseError
from src.shared.database.session import AsyncSession
from src.shared.models.user import User


class TestCaseManager:
    """Test suite for CaseManager class."""

    @pytest.fixture
    def case_manager(self, mock_db_session):
        """Create CaseManager instance with mocked database."""
        return CaseManager(db_session=mock_db_session)

    @pytest.fixture
    def sample_case_data(self):
        """Sample case data for testing."""
        return {
            "title": "Smith v. Johnson Contract Dispute",
            "description": "Contract breach litigation case",
            "case_type": CaseType.LITIGATION,
            "status": CaseStatus.ACTIVE,
            "client_id": str(uuid.uuid4()),
            "assigned_attorney_id": str(uuid.uuid4()),
            "court_jurisdiction": "Superior Court of California",
            "case_number": "CV-2024-001234",
            "filing_date": datetime.now().date(),
            "expected_resolution_date": (datetime.now() + timedelta(days=365)).date()
        }

    @pytest.fixture
    def mock_case(self, sample_case_data):
        """Mock Case object for testing."""
        case = Mock(spec=Case)
        case.id = str(uuid.uuid4())
        case.title = sample_case_data["title"]
        case.description = sample_case_data["description"]
        case.case_type = sample_case_data["case_type"]
        case.status = sample_case_data["status"]
        case.client_id = sample_case_data["client_id"]
        case.assigned_attorney_id = sample_case_data["assigned_attorney_id"]
        case.court_jurisdiction = sample_case_data["court_jurisdiction"]
        case.case_number = sample_case_data["case_number"]
        case.filing_date = sample_case_data["filing_date"]
        case.expected_resolution_date = sample_case_data["expected_resolution_date"]
        case.created_at = datetime.now()
        case.updated_at = datetime.now()
        return case

    @pytest.mark.asyncio
    async def test_create_case_success(self, case_manager, sample_case_data, mock_db_session):
        """Test successful case creation."""
        # Arrange
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        with patch('src.case_management.models.Case') as MockCase:
            mock_case_instance = Mock()
            mock_case_instance.id = str(uuid.uuid4())
            MockCase.return_value = mock_case_instance
            
            # Act
            result = await case_manager.create_case(sample_case_data)
            
            # Assert
            assert result is not None
            assert result.id is not None
            MockCase.assert_called_once()
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_case_duplicate_case_number(self, case_manager, sample_case_data, mock_db_session):
        """Test case creation with duplicate case number."""
        # Arrange
        mock_db_session.execute = AsyncMock()
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = Mock()
        
        # Act & Assert
        with pytest.raises(DuplicateCaseError):
            await case_manager.create_case(sample_case_data)

    @pytest.mark.asyncio
    async def test_get_case_by_id_success(self, case_manager, mock_case, mock_db_session):
        """Test successful case retrieval by ID."""
        # Arrange
        case_id = mock_case.id
        mock_db_session.get = AsyncMock(return_value=mock_case)
        
        # Act
        result = await case_manager.get_case_by_id(case_id)
        
        # Assert
        assert result == mock_case
        mock_db_session.get.assert_called_once_with(Case, case_id)

    @pytest.mark.asyncio
    async def test_get_case_by_id_not_found(self, case_manager, mock_db_session):
        """Test case retrieval with invalid ID."""
        # Arrange
        case_id = str(uuid.uuid4())
        mock_db_session.get = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(CaseNotFoundError):
            await case_manager.get_case_by_id(case_id)

    @pytest.mark.asyncio
    async def test_update_case_status_success(self, case_manager, mock_case, mock_db_session):
        """Test successful case status update."""
        # Arrange
        case_id = mock_case.id
        new_status = CaseStatus.CLOSED
        mock_db_session.get = AsyncMock(return_value=mock_case)
        mock_db_session.commit = AsyncMock()
        
        with patch.object(case_manager, '_log_case_event') as mock_log_event:
            # Act
            result = await case_manager.update_case_status(case_id, new_status, "Case resolved")
            
            # Assert
            assert result.status == new_status
            assert mock_case.status == new_status
            mock_db_session.commit.assert_called_once()
            mock_log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_case_status_invalid_transition(self, case_manager, mock_case, mock_db_session):
        """Test invalid case status transition."""
        # Arrange
        case_id = mock_case.id
        mock_case.status = CaseStatus.CLOSED
        new_status = CaseStatus.ACTIVE
        mock_db_session.get = AsyncMock(return_value=mock_case)
        
        with patch.object(case_manager, '_validate_status_transition', return_value=False):
            # Act & Assert
            with pytest.raises(InvalidCaseStatusError):
                await case_manager.update_case_status(case_id, new_status)

    @pytest.mark.asyncio
    async def test_assign_attorney_success(self, case_manager, mock_case, mock_db_session):
        """Test successful attorney assignment."""
        # Arrange
        case_id = mock_case.id
        attorney_id = str(uuid.uuid4())
        mock_db_session.get = AsyncMock(return_value=mock_case)
        mock_db_session.commit = AsyncMock()
        
        with patch.object(case_manager, '_validate_attorney_assignment', return_value=True):
            with patch.object(case_manager, '_log_case_event') as mock_log_event:
                # Act
                result = await case_manager.assign_attorney(case_id, attorney_id)
                
                # Assert
                assert result.assigned_attorney_id == attorney_id
                assert mock_case.assigned_attorney_id == attorney_id
                mock_db_session.commit.assert_called_once()
                mock_log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_document_to_case_success(self, case_manager, mock_case, mock_db_session):
        """Test successful document addition to case."""
        # Arrange
        case_id = mock_case.id
        document_data = {
            "title": "Contract Agreement",
            "document_type": "contract",
            "file_path": "/storage/documents/contract.pdf",
            "uploaded_by_id": str(uuid.uuid4())
        }
        
        mock_db_session.get = AsyncMock(return_value=mock_case)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        
        with patch('src.case_management.models.CaseDocument') as MockCaseDocument:
            mock_document = Mock()
            mock_document.id = str(uuid.uuid4())
            MockCaseDocument.return_value = mock_document
            
            # Act
            result = await case_manager.add_document_to_case(case_id, document_data)
            
            # Assert
            assert result is not None
            MockCaseDocument.assert_called_once()
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_case_timeline_success(self, case_manager, mock_case, mock_db_session):
        """Test successful case timeline retrieval."""
        # Arrange
        case_id = mock_case.id
        mock_events = [
            Mock(spec=CaseEvent, event_type="case_created", timestamp=datetime.now() - timedelta(days=30)),
            Mock(spec=CaseEvent, event_type="document_added", timestamp=datetime.now() - timedelta(days=20)),
            Mock(spec=CaseEvent, event_type="status_changed", timestamp=datetime.now() - timedelta(days=10))
        ]
        
        mock_db_session.get = AsyncMock(return_value=mock_case)
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        timeline = await case_manager.get_case_timeline(case_id)
        
        # Assert
        assert len(timeline) == 3
        assert all(isinstance(event, Mock) for event in timeline)
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_cases_by_criteria(self, case_manager, mock_db_session):
        """Test case search functionality."""
        # Arrange
        search_criteria = {
            "client_id": str(uuid.uuid4()),
            "status": CaseStatus.ACTIVE,
            "case_type": CaseType.LITIGATION,
            "attorney_id": str(uuid.uuid4())
        }
        
        mock_cases = [Mock(spec=Case), Mock(spec=Case)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_cases
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        results = await case_manager.search_cases(search_criteria)
        
        # Assert
        assert len(results) == 2
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_case_statistics(self, case_manager, mock_db_session):
        """Test case statistics generation."""
        # Arrange
        mock_stats_result = Mock()
        mock_stats_result.fetchone.return_value = (10, 5, 3, 2)  # total, active, closed, pending
        mock_db_session.execute = AsyncMock(return_value=mock_stats_result)
        
        # Act
        stats = await case_manager.get_case_statistics()
        
        # Assert
        assert stats["total_cases"] == 10
        assert stats["active_cases"] == 5
        assert stats["closed_cases"] == 3
        assert stats["pending_cases"] == 2

    @pytest.mark.asyncio
    async def test_archive_case_success(self, case_manager, mock_case, mock_db_session):
        """Test successful case archiving."""
        # Arrange
        case_id = mock_case.id
        mock_case.status = CaseStatus.CLOSED
        mock_db_session.get = AsyncMock(return_value=mock_case)
        mock_db_session.commit = AsyncMock()
        
        # Act
        result = await case_manager.archive_case(case_id, "Case completed successfully")
        
        # Assert
        assert result.status == CaseStatus.ARCHIVED
        assert mock_case.archived_at is not None
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_archive_case_invalid_status(self, case_manager, mock_case, mock_db_session):
        """Test archiving case with invalid status."""
        # Arrange
        case_id = mock_case.id
        mock_case.status = CaseStatus.ACTIVE
        mock_db_session.get = AsyncMock(return_value=mock_case)
        
        # Act & Assert
        with pytest.raises(InvalidCaseStatusError):
            await case_manager.archive_case(case_id)

    def test_validate_status_transition_valid(self, case_manager):
        """Test valid status transitions."""
        # Test valid transitions
        assert case_manager._validate_status_transition(CaseStatus.PENDING, CaseStatus.ACTIVE)
        assert case_manager._validate_status_transition(CaseStatus.ACTIVE, CaseStatus.CLOSED)
        assert case_manager._validate_status_transition(CaseStatus.CLOSED, CaseStatus.ARCHIVED)

    def test_validate_status_transition_invalid(self, case_manager):
        """Test invalid status transitions."""
        # Test invalid transitions
        assert not case_manager._validate_status_transition(CaseStatus.ARCHIVED, CaseStatus.ACTIVE)
        assert not case_manager._validate_status_transition(CaseStatus.CLOSED, CaseStatus.PENDING)

    @pytest.mark.asyncio
    async def test_bulk_update_cases(self, case_manager, mock_db_session):
        """Test bulk case updates."""
        # Arrange
        case_ids = [str(uuid.uuid4()) for _ in range(3)]
        update_data = {"assigned_attorney_id": str(uuid.uuid4())}
        
        mock_db_session.execute = AsyncMock()
        mock_db_session.commit = AsyncMock()
        
        # Act
        result = await case_manager.bulk_update_cases(case_ids, update_data)
        
        # Assert
        assert result["updated_count"] == len(case_ids)
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_overdue_cases(self, case_manager, mock_db_session):
        """Test retrieval of overdue cases."""
        # Arrange
        overdue_cases = [Mock(spec=Case), Mock(spec=Case)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = overdue_cases
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        results = await case_manager.get_overdue_cases()
        
        # Assert
        assert len(results) == 2
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_case_duration(self, case_manager, mock_case):
        """Test case duration calculation."""
        # Arrange
        mock_case.created_at = datetime.now() - timedelta(days=100)
        mock_case.status = CaseStatus.ACTIVE
        
        # Act
        duration = case_manager._calculate_case_duration(mock_case)
        
        # Assert
        assert duration.days == 100

    @pytest.mark.asyncio
    async def test_generate_case_report(self, case_manager, mock_case, mock_db_session):
        """Test case report generation."""
        # Arrange
        case_id = mock_case.id
        mock_db_session.get = AsyncMock(return_value=mock_case)
        
        with patch.object(case_manager, 'get_case_timeline') as mock_timeline:
            mock_timeline.return_value = []
            
            with patch.object(case_manager, '_get_case_documents') as mock_documents:
                mock_documents.return_value = []
                
                # Act
                report = await case_manager.generate_case_report(case_id)
                
                # Assert
                assert "case_info" in report
                assert "timeline" in report
                assert "documents" in report
                assert "statistics" in report

    @pytest.mark.asyncio
    async def test_delete_case_soft_delete(self, case_manager, mock_case, mock_db_session):
        """Test soft deletion of case."""
        # Arrange
        case_id = mock_case.id
        mock_db_session.get = AsyncMock(return_value=mock_case)
        mock_db_session.commit = AsyncMock()
        
        # Act
        result = await case_manager.delete_case(case_id, soft_delete=True)
        
        # Assert
        assert result is True
        assert mock_case.deleted_at is not None
        mock_db_session.commit.assert_called_once()

    @pytest.mark.parametrize("case_type,expected_workflow", [
        (CaseType.LITIGATION, "litigation_workflow"),
        (CaseType.CONTRACT_REVIEW, "contract_workflow"),
        (CaseType.COMPLIANCE, "compliance_workflow"),
        (CaseType.CORPORATE, "corporate_workflow")
    ])
    def test_get_case_workflow_by_type(self, case_manager, case_type, expected_workflow):
        """Test workflow retrieval based on case type."""
        # Act
        workflow = case_manager._get_case_workflow(case_type)
        
        # Assert
        assert workflow == expected_workflow

    @pytest.mark.asyncio
    async def test_case_reminder_notifications(self, case_manager, mock_db_session):
        """Test case reminder notification generation."""
        # Arrange
        upcoming_cases = [Mock(spec=Case) for _ in range(3)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = upcoming_cases
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        with patch('src.notifications.service.NotificationService') as MockNotificationService:
            mock_notification_service = MockNotificationService.return_value
            mock_notification_service.send_reminder = AsyncMock()
            
            # Act
            result = await case_manager.send_case_reminders()
            
            # Assert
            assert result["reminders_sent"] == 3
            assert mock_notification_service.send_reminder.call_count == 3