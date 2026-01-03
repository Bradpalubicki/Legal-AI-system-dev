"""
Unit tests for workflow engine system.

Tests workflow execution, step management, conditional logic,
parallel processing, error handling, and workflow state management.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any, Optional
import uuid
import asyncio

from src.workflow.workflow_engine import WorkflowEngine
from src.workflow.models import Workflow, WorkflowStep, WorkflowExecution, StepExecution
from src.workflow.enums import WorkflowStatus, StepStatus, StepType, ExecutionMode
from src.workflow.exceptions import WorkflowError, StepExecutionError, WorkflowValidationError
from src.workflow.step_handlers import (
    DocumentProcessingStepHandler,
    AIAnalysisStepHandler,
    NotificationStepHandler,
    ConditionalStepHandler
)


class TestWorkflowEngine:
    """Test suite for WorkflowEngine class."""

    @pytest.fixture
    def workflow_engine(self, mock_db_session):
        """Create WorkflowEngine instance with mocked database."""
        return WorkflowEngine(db_session=mock_db_session)

    @pytest.fixture
    def sample_workflow_data(self):
        """Sample workflow data for testing."""
        return {
            "name": "Document Analysis Workflow",
            "description": "Automated document processing and analysis",
            "version": "1.0",
            "is_active": True,
            "steps": [
                {
                    "name": "Upload Document",
                    "step_type": StepType.DOCUMENT_PROCESSING,
                    "order": 1,
                    "is_required": True,
                    "config": {"allowed_formats": ["pdf", "docx"]},
                    "timeout_seconds": 300
                },
                {
                    "name": "AI Analysis",
                    "step_type": StepType.AI_ANALYSIS,
                    "order": 2,
                    "is_required": True,
                    "config": {"analysis_type": "contract_review"},
                    "timeout_seconds": 600
                },
                {
                    "name": "Send Notification",
                    "step_type": StepType.NOTIFICATION,
                    "order": 3,
                    "is_required": False,
                    "config": {"recipients": ["admin@example.com"]},
                    "timeout_seconds": 60
                }
            ]
        }

    @pytest.fixture
    def mock_workflow(self, sample_workflow_data):
        """Mock Workflow object."""
        workflow = Mock(spec=Workflow)
        workflow.id = str(uuid.uuid4())
        workflow.name = sample_workflow_data["name"]
        workflow.description = sample_workflow_data["description"]
        workflow.version = sample_workflow_data["version"]
        workflow.status = WorkflowStatus.ACTIVE
        workflow.created_at = datetime.now()
        workflow.steps = []
        return workflow

    @pytest.fixture
    def mock_workflow_execution(self, mock_workflow):
        """Mock WorkflowExecution object."""
        execution = Mock(spec=WorkflowExecution)
        execution.id = str(uuid.uuid4())
        execution.workflow_id = mock_workflow.id
        execution.status = WorkflowStatus.RUNNING
        execution.started_at = datetime.now()
        execution.context = {"document_id": str(uuid.uuid4())}
        execution.step_executions = []
        return execution

    @pytest.fixture
    def mock_step_handlers(self):
        """Mock step handlers for different step types."""
        handlers = {
            StepType.DOCUMENT_PROCESSING: Mock(spec=DocumentProcessingStepHandler),
            StepType.AI_ANALYSIS: Mock(spec=AIAnalysisStepHandler),
            StepType.NOTIFICATION: Mock(spec=NotificationStepHandler),
            StepType.CONDITIONAL: Mock(spec=ConditionalStepHandler)
        }
        
        for handler in handlers.values():
            handler.execute = AsyncMock()
            handler.validate_config = Mock(return_value=True)
            
        return handlers

    @pytest.mark.asyncio
    async def test_create_workflow_success(self, workflow_engine, sample_workflow_data, mock_db_session):
        """Test successful workflow creation."""
        # Arrange
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        with patch('src.workflow.models.Workflow') as MockWorkflow:
            mock_workflow_instance = Mock()
            mock_workflow_instance.id = str(uuid.uuid4())
            MockWorkflow.return_value = mock_workflow_instance
            
            with patch.object(workflow_engine, '_validate_workflow') as mock_validate:
                mock_validate.return_value = True
                
                # Act
                result = await workflow_engine.create_workflow(sample_workflow_data)
                
                # Assert
                assert result is not None
                MockWorkflow.assert_called_once()
                mock_db_session.add.assert_called_once()
                mock_db_session.commit.assert_called_once()
                mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_workflow_validation_error(self, workflow_engine, sample_workflow_data):
        """Test workflow creation with validation error."""
        # Arrange
        invalid_workflow_data = sample_workflow_data.copy()
        invalid_workflow_data["steps"] = []  # Empty steps should fail validation
        
        with patch.object(workflow_engine, '_validate_workflow') as mock_validate:
            mock_validate.side_effect = WorkflowValidationError("Workflow must have at least one step")
            
            # Act & Assert
            with pytest.raises(WorkflowValidationError):
                await workflow_engine.create_workflow(invalid_workflow_data)

    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, workflow_engine, mock_workflow, mock_step_handlers, mock_db_session):
        """Test successful workflow execution."""
        # Arrange
        workflow_engine.step_handlers = mock_step_handlers
        execution_context = {"document_id": str(uuid.uuid4()), "user_id": str(uuid.uuid4())}
        
        # Mock workflow steps
        mock_steps = [
            Mock(step_type=StepType.DOCUMENT_PROCESSING, order=1, is_required=True),
            Mock(step_type=StepType.AI_ANALYSIS, order=2, is_required=True),
            Mock(step_type=StepType.NOTIFICATION, order=3, is_required=False)
        ]
        mock_workflow.steps = mock_steps
        
        mock_db_session.get = AsyncMock(return_value=mock_workflow)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        
        # Configure step handler responses
        for handler in mock_step_handlers.values():
            handler.execute.return_value = {"status": "success", "output": {"result": "completed"}}
        
        with patch('src.workflow.models.WorkflowExecution') as MockExecution:
            mock_execution_instance = Mock()
            mock_execution_instance.id = str(uuid.uuid4())
            MockExecution.return_value = mock_execution_instance
            
            # Act
            result = await workflow_engine.execute_workflow(mock_workflow.id, execution_context)
            
            # Assert
            assert result is not None
            assert len(mock_step_handlers) >= 3  # At least 3 step types were involved
            mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_execute_workflow_step_failure(self, workflow_engine, mock_workflow, mock_step_handlers, mock_db_session):
        """Test workflow execution with step failure."""
        # Arrange
        workflow_engine.step_handlers = mock_step_handlers
        execution_context = {"document_id": str(uuid.uuid4())}
        
        # Mock workflow with one failing step
        mock_step = Mock(step_type=StepType.DOCUMENT_PROCESSING, order=1, is_required=True)
        mock_workflow.steps = [mock_step]
        
        mock_db_session.get = AsyncMock(return_value=mock_workflow)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        
        # Configure step handler to fail
        mock_step_handlers[StepType.DOCUMENT_PROCESSING].execute.side_effect = StepExecutionError("Processing failed")
        
        with patch('src.workflow.models.WorkflowExecution') as MockExecution:
            mock_execution_instance = Mock()
            mock_execution_instance.id = str(uuid.uuid4())
            MockExecution.return_value = mock_execution_instance
            
            # Act & Assert
            with pytest.raises(StepExecutionError):
                await workflow_engine.execute_workflow(mock_workflow.id, execution_context)

    @pytest.mark.asyncio
    async def test_execute_step_success(self, workflow_engine, mock_step_handlers):
        """Test successful individual step execution."""
        # Arrange
        workflow_engine.step_handlers = mock_step_handlers
        step = Mock()
        step.step_type = StepType.AI_ANALYSIS
        step.config = {"analysis_type": "contract_review"}
        step.timeout_seconds = 300
        
        execution_context = {"document_id": str(uuid.uuid4())}
        expected_result = {"status": "success", "analysis": "Contract terms analyzed"}
        
        mock_step_handlers[StepType.AI_ANALYSIS].execute.return_value = expected_result
        
        # Act
        result = await workflow_engine._execute_step(step, execution_context)
        
        # Assert
        assert result == expected_result
        mock_step_handlers[StepType.AI_ANALYSIS].execute.assert_called_once_with(
            step.config, execution_context
        )

    @pytest.mark.asyncio
    async def test_execute_step_timeout(self, workflow_engine, mock_step_handlers):
        """Test step execution timeout handling."""
        # Arrange
        workflow_engine.step_handlers = mock_step_handlers
        step = Mock()
        step.step_type = StepType.AI_ANALYSIS
        step.config = {"analysis_type": "contract_review"}
        step.timeout_seconds = 1  # Short timeout
        
        execution_context = {"document_id": str(uuid.uuid4())}
        
        # Configure handler to take longer than timeout
        async def slow_execution(*args, **kwargs):
            await asyncio.sleep(2)
            return {"status": "success"}
        
        mock_step_handlers[StepType.AI_ANALYSIS].execute = slow_execution
        
        # Act & Assert
        with pytest.raises(StepExecutionError, match="timeout"):
            await workflow_engine._execute_step(step, execution_context)

    @pytest.mark.asyncio
    async def test_execute_parallel_steps(self, workflow_engine, mock_step_handlers, mock_db_session):
        """Test parallel step execution."""
        # Arrange
        workflow_engine.step_handlers = mock_step_handlers
        execution_id = str(uuid.uuid4())
        
        # Create steps with same order (parallel execution)
        parallel_steps = [
            Mock(step_type=StepType.AI_ANALYSIS, order=2, is_required=True, id="step1"),
            Mock(step_type=StepType.NOTIFICATION, order=2, is_required=False, id="step2")
        ]
        
        execution_context = {"document_id": str(uuid.uuid4())}
        
        # Configure step handlers
        mock_step_handlers[StepType.AI_ANALYSIS].execute.return_value = {"status": "success", "result": "analysis_done"}
        mock_step_handlers[StepType.NOTIFICATION].execute.return_value = {"status": "success", "result": "notification_sent"}
        
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        
        # Act
        results = await workflow_engine._execute_parallel_steps(parallel_steps, execution_context, execution_id)
        
        # Assert
        assert len(results) == 2
        assert all(result["status"] == "success" for result in results)
        
        # Verify both handlers were called
        mock_step_handlers[StepType.AI_ANALYSIS].execute.assert_called_once()
        mock_step_handlers[StepType.NOTIFICATION].execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_conditional_step_execution(self, workflow_engine, mock_step_handlers):
        """Test conditional step execution."""
        # Arrange
        workflow_engine.step_handlers = mock_step_handlers
        step = Mock()
        step.step_type = StepType.CONDITIONAL
        step.config = {
            "condition": "context.document_type == 'contract'",
            "true_action": {"type": "ai_analysis", "config": {}},
            "false_action": {"type": "notification", "config": {}}
        }
        
        execution_context = {"document_type": "contract"}
        
        # Configure conditional handler
        mock_step_handlers[StepType.CONDITIONAL].execute.return_value = {
            "status": "success",
            "condition_result": True,
            "executed_action": "true_action"
        }
        
        # Act
        result = await workflow_engine._execute_step(step, execution_context)
        
        # Assert
        assert result["condition_result"] is True
        assert result["executed_action"] == "true_action"
        mock_step_handlers[StepType.CONDITIONAL].execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause_workflow_execution(self, workflow_engine, mock_workflow_execution, mock_db_session):
        """Test workflow execution pausing."""
        # Arrange
        execution_id = mock_workflow_execution.id
        mock_workflow_execution.status = WorkflowStatus.RUNNING
        
        mock_db_session.get = AsyncMock(return_value=mock_workflow_execution)
        mock_db_session.commit = AsyncMock()
        
        # Act
        result = await workflow_engine.pause_workflow_execution(execution_id)
        
        # Assert
        assert result.status == WorkflowStatus.PAUSED
        assert mock_workflow_execution.status == WorkflowStatus.PAUSED
        assert mock_workflow_execution.paused_at is not None
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_workflow_execution(self, workflow_engine, mock_workflow_execution, mock_db_session):
        """Test workflow execution resuming."""
        # Arrange
        execution_id = mock_workflow_execution.id
        mock_workflow_execution.status = WorkflowStatus.PAUSED
        
        mock_db_session.get = AsyncMock(return_value=mock_workflow_execution)
        mock_db_session.commit = AsyncMock()
        
        with patch.object(workflow_engine, '_continue_execution') as mock_continue:
            mock_continue.return_value = AsyncMock()
            
            # Act
            result = await workflow_engine.resume_workflow_execution(execution_id)
            
            # Assert
            assert result.status == WorkflowStatus.RUNNING
            assert mock_workflow_execution.resumed_at is not None
            mock_db_session.commit.assert_called_once()
            mock_continue.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_workflow_execution(self, workflow_engine, mock_workflow_execution, mock_db_session):
        """Test workflow execution cancellation."""
        # Arrange
        execution_id = mock_workflow_execution.id
        mock_workflow_execution.status = WorkflowStatus.RUNNING
        
        mock_db_session.get = AsyncMock(return_value=mock_workflow_execution)
        mock_db_session.commit = AsyncMock()
        
        # Act
        result = await workflow_engine.cancel_workflow_execution(execution_id, "User requested cancellation")
        
        # Assert
        assert result.status == WorkflowStatus.CANCELLED
        assert mock_workflow_execution.status == WorkflowStatus.CANCELLED
        assert mock_workflow_execution.cancelled_at is not None
        assert mock_workflow_execution.cancellation_reason == "User requested cancellation"
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_workflow_execution_status(self, workflow_engine, mock_workflow_execution, mock_db_session):
        """Test workflow execution status retrieval."""
        # Arrange
        execution_id = mock_workflow_execution.id
        mock_db_session.get = AsyncMock(return_value=mock_workflow_execution)
        
        # Mock step executions
        mock_step_executions = [
            Mock(status=StepStatus.COMPLETED, step_name="Step 1"),
            Mock(status=StepStatus.RUNNING, step_name="Step 2"),
            Mock(status=StepStatus.PENDING, step_name="Step 3")
        ]
        mock_workflow_execution.step_executions = mock_step_executions
        
        # Act
        status = await workflow_engine.get_execution_status(execution_id)
        
        # Assert
        assert status["execution_id"] == execution_id
        assert status["workflow_status"] == WorkflowStatus.RUNNING
        assert len(status["step_statuses"]) == 3
        assert status["progress_percentage"] > 0

    @pytest.mark.asyncio
    async def test_retry_failed_step(self, workflow_engine, mock_db_session, mock_step_handlers):
        """Test retrying a failed step execution."""
        # Arrange
        workflow_engine.step_handlers = mock_step_handlers
        step_execution_id = str(uuid.uuid4())
        
        mock_step_execution = Mock(spec=StepExecution)
        mock_step_execution.id = step_execution_id
        mock_step_execution.status = StepStatus.FAILED
        mock_step_execution.retry_count = 1
        mock_step_execution.step = Mock(step_type=StepType.AI_ANALYSIS, config={})
        
        mock_db_session.get = AsyncMock(return_value=mock_step_execution)
        mock_db_session.commit = AsyncMock()
        
        # Configure successful retry
        mock_step_handlers[StepType.AI_ANALYSIS].execute.return_value = {"status": "success"}
        
        # Act
        result = await workflow_engine.retry_step_execution(step_execution_id)
        
        # Assert
        assert result.status == StepStatus.COMPLETED
        assert mock_step_execution.retry_count == 2
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_execution_history(self, workflow_engine, mock_db_session):
        """Test workflow execution history retrieval."""
        # Arrange
        workflow_id = str(uuid.uuid4())
        mock_executions = [Mock(spec=WorkflowExecution) for _ in range(5)]
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_executions
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        history = await workflow_engine.get_execution_history(workflow_id, limit=10)
        
        # Assert
        assert len(history) == 5
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_workflow_configuration(self, workflow_engine, sample_workflow_data):
        """Test workflow configuration validation."""
        # Arrange
        valid_config = sample_workflow_data
        
        # Act
        result = workflow_engine._validate_workflow(valid_config)
        
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_workflow_invalid_configuration(self, workflow_engine):
        """Test workflow validation with invalid configuration."""
        # Arrange
        invalid_config = {
            "name": "",  # Empty name should fail
            "steps": []  # Empty steps should fail
        }
        
        # Act & Assert
        with pytest.raises(WorkflowValidationError):
            workflow_engine._validate_workflow(invalid_config)

    @pytest.mark.asyncio
    async def test_workflow_execution_metrics(self, workflow_engine, mock_db_session):
        """Test workflow execution metrics calculation."""
        # Arrange
        workflow_id = str(uuid.uuid4())
        
        # Mock metrics data
        mock_metrics_result = Mock()
        mock_metrics_result.fetchone.return_value = (
            10,  # total_executions
            8,   # successful_executions
            1,   # failed_executions
            1,   # cancelled_executions
            300.5  # avg_execution_time
        )
        mock_db_session.execute = AsyncMock(return_value=mock_metrics_result)
        
        # Act
        metrics = await workflow_engine.get_workflow_metrics(workflow_id)
        
        # Assert
        assert metrics["total_executions"] == 10
        assert metrics["success_rate"] == 0.8  # 8/10
        assert metrics["failure_rate"] == 0.1  # 1/10
        assert metrics["average_execution_time"] == 300.5

    @pytest.mark.asyncio
    async def test_schedule_workflow_execution(self, workflow_engine, mock_db_session):
        """Test scheduling workflow execution."""
        # Arrange
        workflow_id = str(uuid.uuid4())
        schedule_data = {
            "cron_expression": "0 9 * * 1-5",  # Weekdays at 9 AM
            "timezone": "UTC",
            "max_executions": 100,
            "context": {"automated": True}
        }
        
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        
        with patch('src.workflow.models.WorkflowSchedule') as MockSchedule:
            mock_schedule_instance = Mock()
            mock_schedule_instance.id = str(uuid.uuid4())
            MockSchedule.return_value = mock_schedule_instance
            
            # Act
            result = await workflow_engine.schedule_workflow(workflow_id, schedule_data)
            
            # Assert
            assert result is not None
            MockSchedule.assert_called_once()
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @pytest.mark.parametrize("step_type,handler_class", [
        (StepType.DOCUMENT_PROCESSING, DocumentProcessingStepHandler),
        (StepType.AI_ANALYSIS, AIAnalysisStepHandler),
        (StepType.NOTIFICATION, NotificationStepHandler),
        (StepType.CONDITIONAL, ConditionalStepHandler)
    ])
    def test_get_step_handler(self, workflow_engine, step_type, handler_class):
        """Test step handler retrieval by type."""
        # Arrange
        mock_handler = Mock(spec=handler_class)
        workflow_engine.step_handlers = {step_type: mock_handler}
        
        # Act
        handler = workflow_engine._get_step_handler(step_type)
        
        # Assert
        assert handler == mock_handler

    @pytest.mark.asyncio
    async def test_workflow_template_creation(self, workflow_engine, sample_workflow_data, mock_db_session):
        """Test workflow template creation."""
        # Arrange
        template_data = sample_workflow_data.copy()
        template_data["is_template"] = True
        template_data["category"] = "document_processing"
        
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        
        with patch('src.workflow.models.WorkflowTemplate') as MockTemplate:
            mock_template_instance = Mock()
            mock_template_instance.id = str(uuid.uuid4())
            MockTemplate.return_value = mock_template_instance
            
            # Act
            result = await workflow_engine.create_workflow_template(template_data)
            
            # Assert
            assert result is not None
            MockTemplate.assert_called_once()
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_version_management(self, workflow_engine, mock_workflow, mock_db_session):
        """Test workflow version management."""
        # Arrange
        workflow_id = mock_workflow.id
        mock_workflow.version = "1.0"
        
        updated_data = {"description": "Updated workflow", "version": "1.1"}
        
        mock_db_session.get = AsyncMock(return_value=mock_workflow)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        
        # Act
        result = await workflow_engine.create_workflow_version(workflow_id, updated_data)
        
        # Assert
        assert result is not None
        assert mock_workflow.version == "1.1"
        mock_db_session.commit.assert_called_once()