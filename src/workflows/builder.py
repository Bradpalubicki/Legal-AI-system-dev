"""
Custom Workflow Builder System
Drag-and-drop workflow builder with conditional logic, automation, and approvals.
"""

from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator
import json
import uuid
import asyncio
from collections import defaultdict
import re


class NodeType(Enum):
    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"
    APPROVAL = "approval"
    EMAIL = "email"
    DELAY = "delay"
    CONDITION = "condition"
    WEBHOOK = "webhook"
    DOCUMENT_GENERATION = "document_generation"
    NOTIFICATION = "notification"
    DATA_TRANSFORMATION = "data_transformation"
    INTEGRATION = "integration"


class WorkflowStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_APPROVAL = "waiting_approval"


class TriggerType(Enum):
    MANUAL = "manual"
    DOCUMENT_UPLOAD = "document_upload"
    CASE_STATUS_CHANGE = "case_status_change"
    DEADLINE_APPROACHING = "deadline_approaching"
    FORM_SUBMISSION = "form_submission"
    EMAIL_RECEIVED = "email_received"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"


class ConditionOperator(Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    MATCHES_REGEX = "matches_regex"


@dataclass
class WorkflowNode:
    node_id: str
    node_type: NodeType
    name: str
    description: Optional[str] = None
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    config: Dict[str, Any] = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)  # Input connector IDs
    outputs: List[str] = field(default_factory=list)  # Output connector IDs
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowConnection:
    connection_id: str
    source_node_id: str
    target_node_id: str
    source_output: str = "default"
    target_input: str = "default"
    condition: Optional[Dict[str, Any]] = None
    label: Optional[str] = None


@dataclass
class WorkflowTrigger:
    trigger_id: str
    trigger_type: TriggerType
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    conditions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: Optional[str] = None
    firm_id: str
    created_by: str
    status: WorkflowStatus = WorkflowStatus.DRAFT
    version: int = 1
    nodes: Dict[str, WorkflowNode] = field(default_factory=dict)
    connections: Dict[str, WorkflowConnection] = field(default_factory=dict)
    triggers: Dict[str, WorkflowTrigger] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_executed: Optional[datetime] = None
    execution_count: int = 0


@dataclass
class WorkflowExecution:
    execution_id: str
    workflow_id: str
    workflow_version: int
    status: ExecutionStatus = ExecutionStatus.PENDING
    triggered_by: Optional[str] = None
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    current_node_id: Optional[str] = None
    node_executions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ApprovalRequest:
    approval_id: str
    execution_id: str
    node_id: str
    approver_id: str
    message: str
    approval_data: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, approved, rejected
    requested_at: datetime = field(default_factory=datetime.now)
    responded_at: Optional[datetime] = None
    response_message: Optional[str] = None


class WorkflowBuilder:
    """Advanced workflow builder with drag-and-drop capabilities"""

    def __init__(self):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        self.node_processors = self._initialize_node_processors()
        self.running_executions: Dict[str, asyncio.Task] = {}

    def _initialize_node_processors(self) -> Dict[NodeType, Callable]:
        """Initialize node processing functions"""
        return {
            NodeType.START: self._process_start_node,
            NodeType.END: self._process_end_node,
            NodeType.TASK: self._process_task_node,
            NodeType.DECISION: self._process_decision_node,
            NodeType.APPROVAL: self._process_approval_node,
            NodeType.EMAIL: self._process_email_node,
            NodeType.DELAY: self._process_delay_node,
            NodeType.CONDITION: self._process_condition_node,
            NodeType.WEBHOOK: self._process_webhook_node,
            NodeType.DOCUMENT_GENERATION: self._process_document_generation_node,
            NodeType.NOTIFICATION: self._process_notification_node,
            NodeType.DATA_TRANSFORMATION: self._process_data_transformation_node,
            NodeType.INTEGRATION: self._process_integration_node
        }

    async def create_workflow(
        self,
        name: str,
        firm_id: str,
        created_by: str,
        description: Optional[str] = None
    ) -> WorkflowDefinition:
        """Create a new workflow definition"""

        workflow_id = str(uuid.uuid4())

        # Create start and end nodes by default
        start_node = WorkflowNode(
            node_id=str(uuid.uuid4()),
            node_type=NodeType.START,
            name="Start",
            position={"x": 100, "y": 200},
            outputs=["output"]
        )

        end_node = WorkflowNode(
            node_id=str(uuid.uuid4()),
            node_type=NodeType.END,
            name="End",
            position={"x": 500, "y": 200},
            inputs=["input"]
        )

        workflow = WorkflowDefinition(
            workflow_id=workflow_id,
            name=name,
            description=description,
            firm_id=firm_id,
            created_by=created_by
        )

        workflow.nodes[start_node.node_id] = start_node
        workflow.nodes[end_node.node_id] = end_node

        self.workflows[workflow_id] = workflow
        return workflow

    async def add_node(
        self,
        workflow_id: str,
        node_type: NodeType,
        name: str,
        position: Dict[str, float],
        config: Dict[str, Any] = None
    ) -> WorkflowNode:
        """Add a node to the workflow"""

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        node_id = str(uuid.uuid4())
        node = WorkflowNode(
            node_id=node_id,
            node_type=node_type,
            name=name,
            position=position,
            config=config or {}
        )

        # Set default inputs/outputs based on node type
        if node_type == NodeType.START:
            node.outputs = ["output"]
        elif node_type == NodeType.END:
            node.inputs = ["input"]
        elif node_type == NodeType.DECISION:
            node.inputs = ["input"]
            node.outputs = ["yes", "no"]
        elif node_type == NodeType.CONDITION:
            node.inputs = ["input"]
            node.outputs = ["true", "false"]
        else:
            node.inputs = ["input"]
            node.outputs = ["output"]

        workflow = self.workflows[workflow_id]
        workflow.nodes[node_id] = node
        workflow.updated_at = datetime.now()

        return node

    async def connect_nodes(
        self,
        workflow_id: str,
        source_node_id: str,
        target_node_id: str,
        source_output: str = "output",
        target_input: str = "input",
        condition: Optional[Dict[str, Any]] = None
    ) -> WorkflowConnection:
        """Connect two nodes in the workflow"""

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]

        if source_node_id not in workflow.nodes:
            raise ValueError(f"Source node {source_node_id} not found")

        if target_node_id not in workflow.nodes:
            raise ValueError(f"Target node {target_node_id} not found")

        connection_id = str(uuid.uuid4())
        connection = WorkflowConnection(
            connection_id=connection_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            source_output=source_output,
            target_input=target_input,
            condition=condition
        )

        workflow.connections[connection_id] = connection
        workflow.updated_at = datetime.now()

        return connection

    async def add_trigger(
        self,
        workflow_id: str,
        trigger_type: TriggerType,
        name: str,
        config: Dict[str, Any],
        conditions: List[Dict[str, Any]] = None
    ) -> WorkflowTrigger:
        """Add a trigger to the workflow"""

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        trigger_id = str(uuid.uuid4())
        trigger = WorkflowTrigger(
            trigger_id=trigger_id,
            trigger_type=trigger_type,
            name=name,
            config=config,
            conditions=conditions or []
        )

        workflow = self.workflows[workflow_id]
        workflow.triggers[trigger_id] = trigger
        workflow.updated_at = datetime.now()

        return trigger

    async def validate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Validate workflow definition"""

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]
        errors = []
        warnings = []

        # Check for start and end nodes
        start_nodes = [n for n in workflow.nodes.values() if n.node_type == NodeType.START]
        end_nodes = [n for n in workflow.nodes.values() if n.node_type == NodeType.END]

        if not start_nodes:
            errors.append("Workflow must have at least one start node")
        elif len(start_nodes) > 1:
            warnings.append("Multiple start nodes found")

        if not end_nodes:
            errors.append("Workflow must have at least one end node")

        # Check for orphaned nodes
        connected_nodes = set()
        for conn in workflow.connections.values():
            connected_nodes.add(conn.source_node_id)
            connected_nodes.add(conn.target_node_id)

        orphaned_nodes = set(workflow.nodes.keys()) - connected_nodes
        if len(orphaned_nodes) > 2:  # Allow start and end to be orphaned initially
            warnings.append(f"Found {len(orphaned_nodes)} orphaned nodes")

        # Check for circular dependencies
        try:
            self._check_circular_dependencies(workflow)
        except ValueError as e:
            errors.append(str(e))

        # Validate node configurations
        for node in workflow.nodes.values():
            node_errors = await self._validate_node_config(node)
            errors.extend(node_errors)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _check_circular_dependencies(self, workflow: WorkflowDefinition):
        """Check for circular dependencies in workflow"""
        visited = set()
        rec_stack = set()

        def has_cycle(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)

            # Get connected nodes
            for conn in workflow.connections.values():
                if conn.source_node_id == node_id:
                    target = conn.target_node_id
                    if target not in visited:
                        if has_cycle(target):
                            return True
                    elif target in rec_stack:
                        return True

            rec_stack.remove(node_id)
            return False

        for node_id in workflow.nodes.keys():
            if node_id not in visited:
                if has_cycle(node_id):
                    raise ValueError("Circular dependency detected in workflow")

    async def _validate_node_config(self, node: WorkflowNode) -> List[str]:
        """Validate individual node configuration"""
        errors = []

        if node.node_type == NodeType.EMAIL:
            if not node.config.get("to"):
                errors.append(f"Email node '{node.name}' missing recipient")
            if not node.config.get("subject"):
                errors.append(f"Email node '{node.name}' missing subject")

        elif node.node_type == NodeType.APPROVAL:
            if not node.config.get("approvers"):
                errors.append(f"Approval node '{node.name}' missing approvers")

        elif node.node_type == NodeType.CONDITION:
            if not node.config.get("conditions"):
                errors.append(f"Condition node '{node.name}' missing conditions")

        elif node.node_type == NodeType.WEBHOOK:
            if not node.config.get("url"):
                errors.append(f"Webhook node '{node.name}' missing URL")

        elif node.node_type == NodeType.DELAY:
            if not node.config.get("duration"):
                errors.append(f"Delay node '{node.name}' missing duration")

        return errors

    async def execute_workflow(
        self,
        workflow_id: str,
        trigger_data: Dict[str, Any] = None,
        triggered_by: str = None
    ) -> WorkflowExecution:
        """Execute a workflow"""

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]

        if workflow.status != WorkflowStatus.ACTIVE:
            raise ValueError(f"Workflow {workflow_id} is not active")

        # Validate workflow before execution
        validation = await self.validate_workflow(workflow_id)
        if not validation["valid"]:
            raise ValueError(f"Workflow validation failed: {validation['errors']}")

        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version=workflow.version,
            triggered_by=triggered_by,
            trigger_data=trigger_data or {},
            context={"variables": workflow.variables.copy()}
        )

        self.executions[execution_id] = execution

        # Start execution asynchronously
        task = asyncio.create_task(self._execute_workflow_async(execution))
        self.running_executions[execution_id] = task

        # Update workflow stats
        workflow.execution_count += 1
        workflow.last_executed = datetime.now()

        return execution

    async def _execute_workflow_async(self, execution: WorkflowExecution):
        """Execute workflow asynchronously"""

        try:
            execution.status = ExecutionStatus.IN_PROGRESS
            execution.started_at = datetime.now()

            workflow = self.workflows[execution.workflow_id]

            # Find start node
            start_nodes = [n for n in workflow.nodes.values() if n.node_type == NodeType.START]
            if not start_nodes:
                raise ValueError("No start node found")

            current_node = start_nodes[0]
            execution.current_node_id = current_node.node_id

            # Execute nodes
            while current_node:
                # Process current node
                result = await self._process_node(execution, current_node)

                # Record node execution
                execution.node_executions[current_node.node_id] = {
                    "status": "completed",
                    "result": result,
                    "executed_at": datetime.now().isoformat()
                }

                # Determine next node
                next_node = await self._get_next_node(execution, current_node, result)

                if next_node:
                    execution.current_node_id = next_node.node_id
                    current_node = next_node
                else:
                    break

            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.now()

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.errors.append(str(e))
            execution.completed_at = datetime.now()

        finally:
            # Clean up running execution
            if execution.execution_id in self.running_executions:
                del self.running_executions[execution.execution_id]

    async def _process_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process individual workflow node"""

        processor = self.node_processors.get(node.node_type)
        if not processor:
            raise ValueError(f"No processor found for node type {node.node_type}")

        return await processor(execution, node)

    async def _get_next_node(
        self,
        execution: WorkflowExecution,
        current_node: WorkflowNode,
        result: Dict[str, Any]
    ) -> Optional[WorkflowNode]:
        """Determine the next node to execute"""

        workflow = self.workflows[execution.workflow_id]

        # Find connections from current node
        connections = [
            conn for conn in workflow.connections.values()
            if conn.source_node_id == current_node.node_id
        ]

        for connection in connections:
            # Check connection conditions
            if connection.condition:
                if not await self._evaluate_condition(connection.condition, execution.context, result):
                    continue

            # Check output matching
            result_output = result.get("output", "output")
            if connection.source_output != result_output:
                continue

            return workflow.nodes[connection.target_node_id]

        return None

    async def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        context: Dict[str, Any],
        result: Dict[str, Any]
    ) -> bool:
        """Evaluate a condition"""

        field = condition.get("field")
        operator = ConditionOperator(condition.get("operator"))
        value = condition.get("value")

        # Get field value from context or result
        if field.startswith("context."):
            field_value = context.get(field[8:])
        elif field.startswith("result."):
            field_value = result.get(field[7:])
        else:
            field_value = context.get(field)

        # Evaluate condition
        if operator == ConditionOperator.EQUALS:
            return field_value == value
        elif operator == ConditionOperator.NOT_EQUALS:
            return field_value != value
        elif operator == ConditionOperator.CONTAINS:
            return value in str(field_value) if field_value else False
        elif operator == ConditionOperator.NOT_CONTAINS:
            return value not in str(field_value) if field_value else True
        elif operator == ConditionOperator.GREATER_THAN:
            return float(field_value) > float(value) if field_value else False
        elif operator == ConditionOperator.LESS_THAN:
            return float(field_value) < float(value) if field_value else False
        elif operator == ConditionOperator.IS_EMPTY:
            return not field_value
        elif operator == ConditionOperator.IS_NOT_EMPTY:
            return bool(field_value)
        elif operator == ConditionOperator.MATCHES_REGEX:
            return bool(re.match(value, str(field_value))) if field_value else False

        return False

    # Node processors
    async def _process_start_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process start node"""
        return {"output": "output", "status": "started"}

    async def _process_end_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process end node"""
        return {"status": "completed"}

    async def _process_task_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process task node"""

        task_type = node.config.get("task_type", "generic")
        assignee = node.config.get("assignee")
        due_date = node.config.get("due_date")

        # Create task (integrate with task management system)
        task_id = str(uuid.uuid4())

        # For now, simulate task completion
        # In real implementation, this would create an actual task
        # and wait for completion or continue with auto-complete logic

        return {
            "output": "output",
            "task_id": task_id,
            "status": "completed",
            "task_type": task_type
        }

    async def _process_decision_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process decision node"""

        decision_logic = node.config.get("decision_logic", {})
        conditions = decision_logic.get("conditions", [])

        # Evaluate conditions
        for condition in conditions:
            if await self._evaluate_condition(condition, execution.context, {}):
                return {"output": "yes", "decision": True}

        return {"output": "no", "decision": False}

    async def _process_approval_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process approval node"""

        approvers = node.config.get("approvers", [])
        message = node.config.get("message", "Approval required")
        approval_data = node.config.get("approval_data", {})

        # Create approval request
        approval_id = str(uuid.uuid4())
        approval_request = ApprovalRequest(
            approval_id=approval_id,
            execution_id=execution.execution_id,
            node_id=node.node_id,
            approver_id=approvers[0] if approvers else "system",
            message=message,
            approval_data=approval_data
        )

        self.approval_requests[approval_id] = approval_request

        # Set execution to waiting for approval
        execution.status = ExecutionStatus.WAITING_APPROVAL

        # In real implementation, send notification to approvers
        # For now, simulate auto-approval after delay
        await asyncio.sleep(1)  # Simulate processing time

        return {
            "output": "output",
            "approval_id": approval_id,
            "status": "approved"  # Simulated
        }

    async def _process_email_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process email node"""

        to = node.config.get("to", [])
        subject = node.config.get("subject", "")
        body = node.config.get("body", "")
        template = node.config.get("template")

        # Process template variables
        context = execution.context
        processed_subject = self._process_template(subject, context)
        processed_body = self._process_template(body, context)

        # Send email (integrate with email system)
        email_id = str(uuid.uuid4())

        return {
            "output": "output",
            "email_id": email_id,
            "status": "sent",
            "recipients": to
        }

    async def _process_delay_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process delay node"""

        duration = node.config.get("duration", 0)  # seconds
        await asyncio.sleep(duration)

        return {
            "output": "output",
            "status": "completed",
            "delay_duration": duration
        }

    async def _process_condition_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process condition node"""

        conditions = node.config.get("conditions", [])

        for condition in conditions:
            if await self._evaluate_condition(condition, execution.context, {}):
                return {"output": "true", "condition_met": True}

        return {"output": "false", "condition_met": False}

    async def _process_webhook_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process webhook node"""

        url = node.config.get("url")
        method = node.config.get("method", "POST")
        headers = node.config.get("headers", {})
        payload = node.config.get("payload", {})

        # Process payload template
        processed_payload = self._process_template_dict(payload, execution.context)

        # Send webhook (implement HTTP client)
        webhook_id = str(uuid.uuid4())

        return {
            "output": "output",
            "webhook_id": webhook_id,
            "status": "sent",
            "url": url
        }

    async def _process_document_generation_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process document generation node"""

        template_id = node.config.get("template_id")
        output_format = node.config.get("output_format", "pdf")
        variables = node.config.get("variables", {})

        # Generate document
        document_id = str(uuid.uuid4())

        return {
            "output": "output",
            "document_id": document_id,
            "status": "generated",
            "format": output_format
        }

    async def _process_notification_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process notification node"""

        recipients = node.config.get("recipients", [])
        message = node.config.get("message", "")
        channels = node.config.get("channels", ["in_app"])

        # Send notifications
        notification_id = str(uuid.uuid4())

        return {
            "output": "output",
            "notification_id": notification_id,
            "status": "sent",
            "channels": channels
        }

    async def _process_data_transformation_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process data transformation node"""

        transformations = node.config.get("transformations", [])

        # Apply transformations to context
        for transform in transformations:
            transform_type = transform.get("type")
            source_field = transform.get("source_field")
            target_field = transform.get("target_field")
            operation = transform.get("operation")

            # Apply transformation logic
            if transform_type == "copy":
                execution.context[target_field] = execution.context.get(source_field)
            elif transform_type == "uppercase":
                value = execution.context.get(source_field, "")
                execution.context[target_field] = str(value).upper()
            elif transform_type == "calculate":
                # Implement calculation logic
                pass

        return {
            "output": "output",
            "status": "transformed",
            "transformations_applied": len(transformations)
        }

    async def _process_integration_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Process integration node"""

        integration_type = node.config.get("integration_type")
        operation = node.config.get("operation")
        parameters = node.config.get("parameters", {})

        # Process integration
        integration_id = str(uuid.uuid4())

        return {
            "output": "output",
            "integration_id": integration_id,
            "status": "completed",
            "integration_type": integration_type
        }

    def _process_template(self, template: str, context: Dict[str, Any]) -> str:
        """Process template with context variables"""
        if not template:
            return ""

        # Simple template processing (replace {{variable}} with values)
        processed = template
        for key, value in context.get("variables", {}).items():
            processed = processed.replace(f"{{{{{key}}}}}", str(value))

        return processed

    def _process_template_dict(self, template_dict: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process template dictionary with context variables"""
        processed = {}

        for key, value in template_dict.items():
            if isinstance(value, str):
                processed[key] = self._process_template(value, context)
            elif isinstance(value, dict):
                processed[key] = self._process_template_dict(value, context)
            else:
                processed[key] = value

        return processed

    async def approve_request(
        self,
        approval_id: str,
        approver_id: str,
        approved: bool,
        message: Optional[str] = None
    ):
        """Approve or reject an approval request"""

        if approval_id not in self.approval_requests:
            raise ValueError(f"Approval request {approval_id} not found")

        approval = self.approval_requests[approval_id]
        approval.status = "approved" if approved else "rejected"
        approval.responded_at = datetime.now()
        approval.response_message = message

        # Resume workflow execution
        execution_id = approval.execution_id
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            if execution.status == ExecutionStatus.WAITING_APPROVAL:
                # Resume execution
                task = asyncio.create_task(self._resume_workflow_execution(execution, approval))
                self.running_executions[execution_id] = task

    async def _resume_workflow_execution(
        self,
        execution: WorkflowExecution,
        approval: ApprovalRequest
    ):
        """Resume workflow execution after approval"""

        execution.status = ExecutionStatus.IN_PROGRESS

        # Update node execution result
        if approval.node_id in execution.node_executions:
            execution.node_executions[approval.node_id]["approval_result"] = {
                "approved": approval.status == "approved",
                "message": approval.response_message
            }

        # Continue execution from current node
        workflow = self.workflows[execution.workflow_id]
        current_node = workflow.nodes.get(execution.current_node_id)

        if current_node:
            # Get result from node execution
            node_result = execution.node_executions.get(current_node.node_id, {}).get("result", {})

            # Find next node
            next_node = await self._get_next_node(execution, current_node, node_result)

            # Continue execution
            while next_node:
                result = await self._process_node(execution, next_node)
                execution.node_executions[next_node.node_id] = {
                    "status": "completed",
                    "result": result,
                    "executed_at": datetime.now().isoformat()
                }

                next_node = await self._get_next_node(execution, next_node, result)

        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()

    async def get_workflow_analytics(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow analytics"""

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]

        # Get executions for this workflow
        executions = [e for e in self.executions.values() if e.workflow_id == workflow_id]

        # Calculate statistics
        total_executions = len(executions)
        completed_executions = len([e for e in executions if e.status == ExecutionStatus.COMPLETED])
        failed_executions = len([e for e in executions if e.status == ExecutionStatus.FAILED])

        success_rate = (completed_executions / total_executions * 100) if total_executions > 0 else 0

        # Calculate average execution time
        completed = [e for e in executions if e.completed_at and e.started_at]
        avg_duration = None
        if completed:
            durations = [(e.completed_at - e.started_at).total_seconds() for e in completed]
            avg_duration = sum(durations) / len(durations)

        # Node performance
        node_performance = defaultdict(lambda: {"executions": 0, "failures": 0})
        for execution in executions:
            for node_id, node_exec in execution.node_executions.items():
                node = workflow.nodes.get(node_id)
                if node:
                    node_performance[node.name]["executions"] += 1
                    if node_exec.get("status") != "completed":
                        node_performance[node.name]["failures"] += 1

        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
            "total_executions": total_executions,
            "completed_executions": completed_executions,
            "failed_executions": failed_executions,
            "success_rate": round(success_rate, 2),
            "average_duration_seconds": round(avg_duration, 2) if avg_duration else None,
            "node_performance": dict(node_performance),
            "last_executed": workflow.last_executed.isoformat() if workflow.last_executed else None
        }


# Pydantic models for API
class NodeConfigModel(BaseModel):
    node_type: NodeType
    name: str
    position: Dict[str, float]
    config: Dict[str, Any] = Field(default_factory=dict)


class ConnectionModel(BaseModel):
    source_node_id: str
    target_node_id: str
    source_output: str = "output"
    target_input: str = "input"
    condition: Optional[Dict[str, Any]] = None


class TriggerModel(BaseModel):
    trigger_type: TriggerType
    name: str
    config: Dict[str, Any]
    conditions: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowCreateModel(BaseModel):
    name: str
    description: Optional[str] = None


class WorkflowExecuteModel(BaseModel):
    trigger_data: Dict[str, Any] = Field(default_factory=dict)
    triggered_by: Optional[str] = None


class ApprovalResponseModel(BaseModel):
    approved: bool
    message: Optional[str] = None


# Global instance
workflow_builder = WorkflowBuilder()


def get_workflow_endpoints() -> APIRouter:
    """Get workflow builder FastAPI endpoints"""
    router = APIRouter(prefix="/workflows", tags=["workflows"])

    @router.post("/create/{firm_id}")
    async def create_workflow(
        firm_id: str,
        workflow_data: WorkflowCreateModel,
        created_by: str = "system"
    ):
        """Create new workflow"""
        try:
            workflow = await workflow_builder.create_workflow(
                workflow_data.name, firm_id, created_by, workflow_data.description
            )
            return {
                "workflow_id": workflow.workflow_id,
                "status": "created",
                "nodes": len(workflow.nodes)
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/{workflow_id}/nodes")
    async def add_node(workflow_id: str, node_data: NodeConfigModel):
        """Add node to workflow"""
        try:
            node = await workflow_builder.add_node(
                workflow_id,
                node_data.node_type,
                node_data.name,
                node_data.position,
                node_data.config
            )
            return {"node_id": node.node_id, "status": "added"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/{workflow_id}/connections")
    async def connect_nodes(workflow_id: str, connection_data: ConnectionModel):
        """Connect workflow nodes"""
        try:
            connection = await workflow_builder.connect_nodes(
                workflow_id,
                connection_data.source_node_id,
                connection_data.target_node_id,
                connection_data.source_output,
                connection_data.target_input,
                connection_data.condition
            )
            return {"connection_id": connection.connection_id, "status": "connected"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/{workflow_id}/triggers")
    async def add_trigger(workflow_id: str, trigger_data: TriggerModel):
        """Add trigger to workflow"""
        try:
            trigger = await workflow_builder.add_trigger(
                workflow_id,
                trigger_data.trigger_type,
                trigger_data.name,
                trigger_data.config,
                trigger_data.conditions
            )
            return {"trigger_id": trigger.trigger_id, "status": "added"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/{workflow_id}/validate")
    async def validate_workflow(workflow_id: str):
        """Validate workflow definition"""
        try:
            return await workflow_builder.validate_workflow(workflow_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/{workflow_id}/execute")
    async def execute_workflow(workflow_id: str, execution_data: WorkflowExecuteModel):
        """Execute workflow"""
        try:
            execution = await workflow_builder.execute_workflow(
                workflow_id,
                execution_data.trigger_data,
                execution_data.triggered_by
            )
            return {
                "execution_id": execution.execution_id,
                "status": execution.status.value,
                "started_at": execution.started_at
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/{workflow_id}")
    async def get_workflow(workflow_id: str):
        """Get workflow definition"""
        if workflow_id not in workflow_builder.workflows:
            raise HTTPException(status_code=404, detail="Workflow not found")

        workflow = workflow_builder.workflows[workflow_id]
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status.value,
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "node_type": node.node_type.value,
                    "name": node.name,
                    "position": node.position,
                    "config": node.config
                }
                for node_id, node in workflow.nodes.items()
            },
            "connections": {
                conn_id: {
                    "connection_id": conn.connection_id,
                    "source_node_id": conn.source_node_id,
                    "target_node_id": conn.target_node_id,
                    "source_output": conn.source_output,
                    "target_input": conn.target_input
                }
                for conn_id, conn in workflow.connections.items()
            },
            "triggers": {
                trigger_id: {
                    "trigger_id": trigger.trigger_id,
                    "trigger_type": trigger.trigger_type.value,
                    "name": trigger.name,
                    "config": trigger.config
                }
                for trigger_id, trigger in workflow.triggers.items()
            }
        }

    @router.get("/{workflow_id}/executions")
    async def get_workflow_executions(workflow_id: str):
        """Get workflow executions"""
        executions = [
            {
                "execution_id": e.execution_id,
                "status": e.status.value,
                "started_at": e.started_at,
                "completed_at": e.completed_at,
                "triggered_by": e.triggered_by
            }
            for e in workflow_builder.executions.values()
            if e.workflow_id == workflow_id
        ]

        return {"executions": executions}

    @router.get("/execution/{execution_id}")
    async def get_execution_details(execution_id: str):
        """Get detailed execution information"""
        if execution_id not in workflow_builder.executions:
            raise HTTPException(status_code=404, detail="Execution not found")

        execution = workflow_builder.executions[execution_id]
        return {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "current_node_id": execution.current_node_id,
            "node_executions": execution.node_executions,
            "errors": execution.errors
        }

    @router.post("/approval/{approval_id}")
    async def respond_to_approval(
        approval_id: str,
        response: ApprovalResponseModel,
        approver_id: str = "system"
    ):
        """Respond to approval request"""
        try:
            await workflow_builder.approve_request(
                approval_id, approver_id, response.approved, response.message
            )
            return {"status": "processed", "approved": response.approved}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/{workflow_id}/analytics")
    async def get_workflow_analytics(workflow_id: str):
        """Get workflow analytics"""
        try:
            return await workflow_builder.get_workflow_analytics(workflow_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.put("/{workflow_id}/status")
    async def update_workflow_status(workflow_id: str, status: WorkflowStatus):
        """Update workflow status"""
        if workflow_id not in workflow_builder.workflows:
            raise HTTPException(status_code=404, detail="Workflow not found")

        workflow = workflow_builder.workflows[workflow_id]
        workflow.status = status
        workflow.updated_at = datetime.now()

        return {"status": "updated", "new_status": status.value}

    return router


async def initialize_workflow_system():
    """Initialize the workflow builder system"""
    print("Initializing custom workflow builder system...")

    # Create sample workflow for demonstration
    sample_workflow = await workflow_builder.create_workflow(
        "Document Review Workflow", "demo_firm", "system",
        "Automated document review and approval process"
    )

    print("✓ Workflow builder initialized")
    print("✓ Node processors configured")
    print("✓ Execution engine ready")
    print("✓ Approval system active")
    print(f"✓ Sample workflow created: {sample_workflow.name}")
    print("🔄 Custom workflow builder system ready!")