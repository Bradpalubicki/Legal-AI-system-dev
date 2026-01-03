"""
External API Access System
RESTful API, GraphQL endpoint, webhooks, rate limiting, and API key management.
"""

from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from fastapi import APIRouter, HTTPException, Depends, Request, Header, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import json
import uuid
import hmac
import hashlib
import time
from collections import defaultdict, deque
import asyncio
import httpx
from urllib.parse import urljoin
import graphql
from graphql import build_schema, execute


class APIKeyStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"


class WebhookStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    SUSPENDED = "suspended"


class RateLimitType(Enum):
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"
    DATA_TRANSFER_MB = "data_transfer_mb"


class WebhookEvent(Enum):
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_ANALYZED = "document.analyzed"
    CASE_CREATED = "case.created"
    CASE_UPDATED = "case.updated"
    USER_CREATED = "user.created"
    WORKFLOW_COMPLETED = "workflow.completed"
    BILLING_UPDATED = "billing.updated"
    SECURITY_ALERT = "security.alert"


@dataclass
class APIKey:
    key_id: str
    key_secret: str
    firm_id: str
    name: str
    description: Optional[str] = None
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    permissions: List[str] = field(default_factory=list)
    rate_limits: Dict[RateLimitType, int] = field(default_factory=dict)
    allowed_ips: List[str] = field(default_factory=list)
    referrer_restrictions: List[str] = field(default_factory=list)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_stats: Dict[str, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class WebhookEndpoint:
    webhook_id: str
    firm_id: str
    name: str
    url: str
    events: List[WebhookEvent]
    status: WebhookStatus = WebhookStatus.ACTIVE
    secret: str = field(default_factory=lambda: str(uuid.uuid4()))
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30  # seconds
    max_retries: int = 3
    retry_backoff: int = 60  # seconds
    failed_attempts: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WebhookDelivery:
    delivery_id: str
    webhook_id: str
    event_type: WebhookEvent
    payload: Dict[str, Any]
    status: str = "pending"  # pending, delivered, failed
    attempts: int = 0
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RateLimitBucket:
    firm_id: str
    api_key_id: str
    limit_type: RateLimitType
    limit: int
    current_count: int = 0
    reset_time: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=1))
    blocked_until: Optional[datetime] = None


@dataclass
class APIRequest:
    request_id: str
    api_key_id: str
    firm_id: str
    endpoint: str
    method: str
    ip_address: str
    user_agent: str
    request_size: int = 0
    response_size: int = 0
    response_time: float = 0.0
    status_code: int = 200
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ExternalAPIManager:
    """Comprehensive external API management system"""

    def __init__(self):
        self.api_keys: Dict[str, APIKey] = {}
        self.webhooks: Dict[str, WebhookEndpoint] = {}
        self.webhook_deliveries: Dict[str, WebhookDelivery] = {}
        self.rate_limits: Dict[str, RateLimitBucket] = {}
        self.api_requests: Dict[str, List[APIRequest]] = defaultdict(list)
        self.security = HTTPBearer()
        self.webhook_queue = asyncio.Queue()
        self.graphql_schema = self._build_graphql_schema()
        self._start_webhook_processor()

    def _build_graphql_schema(self):
        """Build GraphQL schema for API access"""
        schema_definition = """
        type Query {
            firm(id: ID!): Firm
            document(id: ID!): Document
            case(id: ID!): Case
            user(id: ID!): User
            workflows(firmId: ID!, limit: Int, offset: Int): [Workflow]
            analytics(firmId: ID!, startDate: String!, endDate: String!): Analytics
        }

        type Mutation {
            createCase(input: CaseInput!): Case
            updateCase(id: ID!, input: CaseInput!): Case
            uploadDocument(input: DocumentInput!): Document
            executeWorkflow(workflowId: ID!, input: JSON): WorkflowExecution
            createWebhook(input: WebhookInput!): Webhook
        }

        type Firm {
            id: ID!
            name: String!
            status: String!
            users: [User!]!
            cases: [Case!]!
            documents: [Document!]!
            createdAt: String!
        }

        type Document {
            id: ID!
            filename: String!
            type: String!
            size: Int!
            status: String!
            analysis: DocumentAnalysis
            uploadedAt: String!
        }

        type DocumentAnalysis {
            summary: String
            keyTerms: [String!]
            entities: [Entity!]
            riskScore: Float
            recommendations: [String!]
        }

        type Entity {
            name: String!
            type: String!
            confidence: Float!
        }

        type Case {
            id: ID!
            name: String!
            status: String!
            priority: String!
            documents: [Document!]!
            assignedTo: User
            createdAt: String!
            updatedAt: String!
        }

        type User {
            id: ID!
            email: String!
            firstName: String!
            lastName: String!
            role: String!
            status: String!
            lastLogin: String
        }

        type Workflow {
            id: ID!
            name: String!
            status: String!
            executionCount: Int!
            lastExecuted: String
        }

        type WorkflowExecution {
            id: ID!
            workflowId: ID!
            status: String!
            startedAt: String!
            completedAt: String
        }

        type Analytics {
            totalUsers: Int!
            totalDocuments: Int!
            totalCases: Int!
            averageProcessingTime: Float!
            usageByFeature: JSON!
        }

        type Webhook {
            id: ID!
            url: String!
            events: [String!]!
            status: String!
            createdAt: String!
        }

        input CaseInput {
            name: String!
            description: String
            priority: String
            assignedTo: ID
        }

        input DocumentInput {
            filename: String!
            content: String!
            type: String!
        }

        input WebhookInput {
            url: String!
            events: [String!]!
            secret: String
        }

        scalar JSON
        """

        return build_schema(schema_definition)

    def _start_webhook_processor(self):
        """Start background webhook processing"""
        asyncio.create_task(self._process_webhook_queue())

    async def create_api_key(
        self,
        firm_id: str,
        name: str,
        permissions: List[str],
        created_by: str,
        description: Optional[str] = None,
        rate_limits: Optional[Dict[RateLimitType, int]] = None,
        expires_at: Optional[datetime] = None
    ) -> APIKey:
        """Create new API key"""

        key_id = f"legalai_{firm_id}_{uuid.uuid4().hex[:16]}"
        key_secret = hashlib.sha256(f"{key_id}{time.time()}".encode()).hexdigest()

        api_key = APIKey(
            key_id=key_id,
            key_secret=key_secret,
            firm_id=firm_id,
            name=name,
            description=description,
            permissions=permissions,
            rate_limits=rate_limits or {
                RateLimitType.REQUESTS_PER_MINUTE: 60,
                RateLimitType.REQUESTS_PER_HOUR: 1000,
                RateLimitType.REQUESTS_PER_DAY: 10000
            },
            expires_at=expires_at,
            created_by=created_by
        )

        self.api_keys[key_id] = api_key
        return api_key

    async def validate_api_key(self, key_id: str, key_secret: str) -> Optional[APIKey]:
        """Validate API key credentials"""

        api_key = self.api_keys.get(key_id)
        if not api_key:
            return None

        if api_key.key_secret != key_secret:
            return None

        if api_key.status != APIKeyStatus.ACTIVE:
            return None

        if api_key.expires_at and api_key.expires_at < datetime.now():
            api_key.status = APIKeyStatus.EXPIRED
            return None

        # Update last used timestamp
        api_key.last_used = datetime.now()
        return api_key

    async def check_rate_limit(
        self,
        api_key: APIKey,
        request_size: int = 0
    ) -> Dict[str, Any]:
        """Check rate limits for API key"""

        now = datetime.now()
        blocked_reasons = []

        for limit_type, limit_value in api_key.rate_limits.items():
            bucket_key = f"{api_key.key_id}_{limit_type.value}"
            bucket = self.rate_limits.get(bucket_key)

            if not bucket:
                # Create new bucket
                reset_time = self._get_reset_time(limit_type, now)
                bucket = RateLimitBucket(
                    firm_id=api_key.firm_id,
                    api_key_id=api_key.key_id,
                    limit_type=limit_type,
                    limit=limit_value,
                    reset_time=reset_time
                )
                self.rate_limits[bucket_key] = bucket

            # Reset bucket if time has passed
            if now >= bucket.reset_time:
                bucket.current_count = 0
                bucket.reset_time = self._get_reset_time(limit_type, now)
                bucket.blocked_until = None

            # Check if currently blocked
            if bucket.blocked_until and now < bucket.blocked_until:
                blocked_reasons.append(f"Blocked until {bucket.blocked_until}")
                continue

            # Check limit
            increment = 1 if limit_type != RateLimitType.DATA_TRANSFER_MB else request_size / (1024 * 1024)

            if bucket.current_count + increment > bucket.limit:
                # Rate limit exceeded
                bucket.blocked_until = bucket.reset_time
                blocked_reasons.append(f"Rate limit exceeded for {limit_type.value}")
                continue

            # Update count
            bucket.current_count += increment

        return {
            "allowed": len(blocked_reasons) == 0,
            "blocked_reasons": blocked_reasons,
            "limits": {
                bucket_key.split("_")[-1]: {
                    "limit": bucket.limit,
                    "remaining": max(0, bucket.limit - bucket.current_count),
                    "reset_time": bucket.reset_time.isoformat()
                }
                for bucket_key, bucket in self.rate_limits.items()
                if bucket.api_key_id == api_key.key_id
            }
        }

    def _get_reset_time(self, limit_type: RateLimitType, now: datetime) -> datetime:
        """Get reset time for rate limit type"""
        if limit_type == RateLimitType.REQUESTS_PER_MINUTE:
            return now + timedelta(minutes=1)
        elif limit_type == RateLimitType.REQUESTS_PER_HOUR:
            return now + timedelta(hours=1)
        elif limit_type == RateLimitType.REQUESTS_PER_DAY:
            return now + timedelta(days=1)
        else:
            return now + timedelta(minutes=1)

    async def log_api_request(
        self,
        api_key: APIKey,
        request: Request,
        response_size: int = 0,
        response_time: float = 0.0,
        status_code: int = 200,
        error_message: Optional[str] = None
    ):
        """Log API request for analytics"""

        request_id = str(uuid.uuid4())
        api_request = APIRequest(
            request_id=request_id,
            api_key_id=api_key.key_id,
            firm_id=api_key.firm_id,
            endpoint=str(request.url.path),
            method=request.method,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            request_size=int(request.headers.get("content-length", 0)),
            response_size=response_size,
            response_time=response_time,
            status_code=status_code,
            error_message=error_message
        )

        self.api_requests[api_key.firm_id].append(api_request)

        # Update API key usage stats
        endpoint_key = f"{request.method}_{request.url.path}"
        api_key.usage_stats[endpoint_key] = api_key.usage_stats.get(endpoint_key, 0) + 1

    async def create_webhook(
        self,
        firm_id: str,
        name: str,
        url: str,
        events: List[WebhookEvent],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> WebhookEndpoint:
        """Create webhook endpoint"""

        webhook_id = str(uuid.uuid4())
        webhook = WebhookEndpoint(
            webhook_id=webhook_id,
            firm_id=firm_id,
            name=name,
            url=url,
            events=events,
            secret=secret or str(uuid.uuid4()),
            headers=headers or {}
        )

        self.webhooks[webhook_id] = webhook
        return webhook

    async def trigger_webhook(
        self,
        firm_id: str,
        event_type: WebhookEvent,
        payload: Dict[str, Any]
    ):
        """Trigger webhooks for event"""

        # Find matching webhooks
        matching_webhooks = [
            webhook for webhook in self.webhooks.values()
            if webhook.firm_id == firm_id and
               webhook.status == WebhookStatus.ACTIVE and
               event_type in webhook.events
        ]

        # Queue webhook deliveries
        for webhook in matching_webhooks:
            delivery_id = str(uuid.uuid4())
            delivery = WebhookDelivery(
                delivery_id=delivery_id,
                webhook_id=webhook.webhook_id,
                event_type=event_type,
                payload=payload
            )

            self.webhook_deliveries[delivery_id] = delivery
            await self.webhook_queue.put(delivery)

    async def _process_webhook_queue(self):
        """Process webhook delivery queue"""
        while True:
            try:
                delivery = await self.webhook_queue.get()
                await self._deliver_webhook(delivery)
            except Exception as e:
                print(f"Error processing webhook delivery: {e}")

    async def _deliver_webhook(self, delivery: WebhookDelivery):
        """Deliver webhook to endpoint"""

        webhook = self.webhooks[delivery.webhook_id]
        delivery.attempts += 1

        # Prepare payload
        webhook_payload = {
            "event": delivery.event_type.value,
            "delivery_id": delivery.delivery_id,
            "timestamp": delivery.created_at.isoformat(),
            "data": delivery.payload
        }

        # Generate signature
        signature = self._generate_webhook_signature(
            json.dumps(webhook_payload),
            webhook.secret
        )

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": delivery.event_type.value,
            "X-Webhook-Delivery": delivery.delivery_id,
            **webhook.headers
        }

        try:
            async with httpx.AsyncClient(timeout=webhook.timeout) as client:
                response = await client.post(
                    webhook.url,
                    json=webhook_payload,
                    headers=headers
                )

                delivery.response_code = response.status_code
                delivery.response_body = response.text[:1000]  # Limit response body size

                if 200 <= response.status_code < 300:
                    # Success
                    delivery.status = "delivered"
                    delivery.delivered_at = datetime.now()
                    webhook.last_success = datetime.now()
                    webhook.failed_attempts = 0
                else:
                    # HTTP error
                    raise httpx.HTTPStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response
                    )

        except Exception as e:
            delivery.status = "failed"
            webhook.last_failure = datetime.now()
            webhook.failed_attempts += 1

            # Retry logic
            if delivery.attempts < webhook.max_retries:
                retry_delay = webhook.retry_backoff * (2 ** (delivery.attempts - 1))
                await asyncio.sleep(retry_delay)
                await self.webhook_queue.put(delivery)
            else:
                # Max retries reached
                if webhook.failed_attempts >= 10:
                    webhook.status = WebhookStatus.FAILED

    def _generate_webhook_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    async def execute_graphql_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        api_key: Optional[APIKey] = None
    ) -> Dict[str, Any]:
        """Execute GraphQL query"""

        # Create execution context
        context = {
            "api_key": api_key,
            "firm_id": api_key.firm_id if api_key else None
        }

        # Define resolvers
        root_resolvers = {
            "firm": self._resolve_firm,
            "document": self._resolve_document,
            "case": self._resolve_case,
            "user": self._resolve_user,
            "workflows": self._resolve_workflows,
            "analytics": self._resolve_analytics,
            "createCase": self._resolve_create_case,
            "updateCase": self._resolve_update_case,
            "uploadDocument": self._resolve_upload_document,
            "executeWorkflow": self._resolve_execute_workflow,
            "createWebhook": self._resolve_create_webhook
        }

        try:
            result = await execute(
                self.graphql_schema,
                query,
                root_value=root_resolvers,
                context_value=context,
                variable_values=variables or {}
            )

            return {
                "data": result.data,
                "errors": [str(error) for error in result.errors] if result.errors else None
            }

        except Exception as e:
            return {
                "data": None,
                "errors": [str(e)]
            }

    # GraphQL Resolvers
    async def _resolve_firm(self, info, id: str):
        """Resolve firm data"""
        # Integration with firm system
        return {
            "id": id,
            "name": "Sample Firm",
            "status": "active",
            "users": [],
            "cases": [],
            "documents": [],
            "createdAt": datetime.now().isoformat()
        }

    async def _resolve_document(self, info, id: str):
        """Resolve document data"""
        # Integration with document system
        return {
            "id": id,
            "filename": "sample.pdf",
            "type": "contract",
            "size": 102400,
            "status": "processed",
            "uploadedAt": datetime.now().isoformat()
        }

    async def _resolve_case(self, info, id: str):
        """Resolve case data"""
        # Integration with case management
        return {
            "id": id,
            "name": "Sample Case",
            "status": "active",
            "priority": "medium",
            "documents": [],
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }

    async def _resolve_user(self, info, id: str):
        """Resolve user data"""
        # Integration with user management
        return {
            "id": id,
            "email": "user@example.com",
            "firstName": "John",
            "lastName": "Doe",
            "role": "attorney",
            "status": "active"
        }

    async def _resolve_workflows(self, info, firmId: str, limit: int = 10, offset: int = 0):
        """Resolve workflows"""
        # Integration with workflow system
        return []

    async def _resolve_analytics(self, info, firmId: str, startDate: str, endDate: str):
        """Resolve analytics data"""
        # Integration with analytics system
        return {
            "totalUsers": 10,
            "totalDocuments": 50,
            "totalCases": 25,
            "averageProcessingTime": 2.5,
            "usageByFeature": {}
        }

    async def _resolve_create_case(self, info, input: Dict[str, Any]):
        """Create case mutation"""
        # Integration with case management
        case_id = str(uuid.uuid4())
        return {
            "id": case_id,
            "name": input["name"],
            "status": "active",
            "priority": input.get("priority", "medium"),
            "documents": [],
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }

    async def _resolve_update_case(self, info, id: str, input: Dict[str, Any]):
        """Update case mutation"""
        # Integration with case management
        return await self._resolve_case(info, id)

    async def _resolve_upload_document(self, info, input: Dict[str, Any]):
        """Upload document mutation"""
        # Integration with document system
        doc_id = str(uuid.uuid4())
        return {
            "id": doc_id,
            "filename": input["filename"],
            "type": input["type"],
            "size": len(input["content"]),
            "status": "processing",
            "uploadedAt": datetime.now().isoformat()
        }

    async def _resolve_execute_workflow(self, info, workflowId: str, input: Dict[str, Any]):
        """Execute workflow mutation"""
        # Integration with workflow system
        execution_id = str(uuid.uuid4())
        return {
            "id": execution_id,
            "workflowId": workflowId,
            "status": "running",
            "startedAt": datetime.now().isoformat()
        }

    async def _resolve_create_webhook(self, info, input: Dict[str, Any]):
        """Create webhook mutation"""
        webhook_id = str(uuid.uuid4())
        return {
            "id": webhook_id,
            "url": input["url"],
            "events": input["events"],
            "status": "active",
            "createdAt": datetime.now().isoformat()
        }

    async def get_api_analytics(
        self,
        firm_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get API usage analytics"""

        firm_requests = self.api_requests.get(firm_id, [])
        date_filtered = [
            req for req in firm_requests
            if start_date <= req.timestamp <= end_date
        ]

        if not date_filtered:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "error_requests": 0,
                "average_response_time": 0.0,
                "endpoints": {},
                "methods": {},
                "status_codes": {}
            }

        # Calculate statistics
        total_requests = len(date_filtered)
        successful_requests = len([r for r in date_filtered if 200 <= r.status_code < 400])
        error_requests = total_requests - successful_requests

        avg_response_time = sum(r.response_time for r in date_filtered) / total_requests

        # Group by endpoint
        endpoints = defaultdict(int)
        methods = defaultdict(int)
        status_codes = defaultdict(int)

        for req in date_filtered:
            endpoints[req.endpoint] += 1
            methods[req.method] += 1
            status_codes[str(req.status_code)] += 1

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "error_requests": error_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "average_response_time": round(avg_response_time, 3),
            "endpoints": dict(endpoints),
            "methods": dict(methods),
            "status_codes": dict(status_codes)
        }


# Dependency for API key authentication
async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    external_api: ExternalAPIManager = Depends(lambda: external_api_manager)
) -> APIKey:
    """Validate API key from Authorization header"""

    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing API key")

    # Extract key_id and secret from credentials
    parts = credentials.credentials.split(":")
    if len(parts) != 2:
        raise HTTPException(status_code=401, detail="Invalid API key format")

    key_id, key_secret = parts

    api_key = await external_api.validate_api_key(key_id, key_secret)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key


# Pydantic models for API
class APIKeyCreateModel(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str]
    rate_limits: Optional[Dict[str, int]] = None
    expires_days: Optional[int] = None


class WebhookCreateModel(BaseModel):
    name: str
    url: str = Field(..., regex=r'^https?://.+')
    events: List[WebhookEvent]
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


class GraphQLQueryModel(BaseModel):
    query: str
    variables: Optional[Dict[str, Any]] = None


# Global instance
external_api_manager = ExternalAPIManager()


def get_external_api_endpoints() -> APIRouter:
    """Get external API endpoints"""
    router = APIRouter(prefix="/external-api", tags=["external_api"])

    @router.post("/keys/{firm_id}")
    async def create_api_key(
        firm_id: str,
        key_data: APIKeyCreateModel,
        created_by: str = "system"
    ):
        """Create new API key"""
        try:
            expires_at = None
            if key_data.expires_days:
                expires_at = datetime.now() + timedelta(days=key_data.expires_days)

            # Convert rate limits
            rate_limits = {}
            if key_data.rate_limits:
                for key, value in key_data.rate_limits.items():
                    try:
                        rate_limit_type = RateLimitType(key)
                        rate_limits[rate_limit_type] = value
                    except ValueError:
                        pass

            api_key = await external_api_manager.create_api_key(
                firm_id,
                key_data.name,
                key_data.permissions,
                created_by,
                key_data.description,
                rate_limits,
                expires_at
            )

            return {
                "key_id": api_key.key_id,
                "key_secret": api_key.key_secret,  # Only returned once
                "status": "created",
                "permissions": api_key.permissions,
                "rate_limits": {k.value: v for k, v in api_key.rate_limits.items()}
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/keys/{firm_id}")
    async def list_api_keys(firm_id: str):
        """List API keys for firm"""
        keys = [
            {
                "key_id": key.key_id,
                "name": key.name,
                "description": key.description,
                "status": key.status.value,
                "permissions": key.permissions,
                "last_used": key.last_used,
                "created_at": key.created_at,
                "expires_at": key.expires_at
            }
            for key in external_api_manager.api_keys.values()
            if key.firm_id == firm_id
        ]
        return {"keys": keys}

    @router.delete("/keys/{key_id}")
    async def revoke_api_key(key_id: str):
        """Revoke API key"""
        if key_id not in external_api_manager.api_keys:
            raise HTTPException(status_code=404, detail="API key not found")

        api_key = external_api_manager.api_keys[key_id]
        api_key.status = APIKeyStatus.REVOKED
        return {"status": "revoked"}

    @router.post("/webhooks/{firm_id}")
    async def create_webhook(firm_id: str, webhook_data: WebhookCreateModel):
        """Create webhook endpoint"""
        try:
            webhook = await external_api_manager.create_webhook(
                firm_id,
                webhook_data.name,
                webhook_data.url,
                webhook_data.events,
                webhook_data.secret,
                webhook_data.headers
            )

            return {
                "webhook_id": webhook.webhook_id,
                "url": webhook.url,
                "events": [e.value for e in webhook.events],
                "secret": webhook.secret,
                "status": "created"
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/webhooks/{firm_id}")
    async def list_webhooks(firm_id: str):
        """List webhooks for firm"""
        webhooks = [
            {
                "webhook_id": webhook.webhook_id,
                "name": webhook.name,
                "url": webhook.url,
                "events": [e.value for e in webhook.events],
                "status": webhook.status.value,
                "last_success": webhook.last_success,
                "last_failure": webhook.last_failure,
                "failed_attempts": webhook.failed_attempts,
                "created_at": webhook.created_at
            }
            for webhook in external_api_manager.webhooks.values()
            if webhook.firm_id == firm_id
        ]
        return {"webhooks": webhooks}

    @router.post("/webhooks/test")
    async def test_webhook(firm_id: str, event_type: WebhookEvent):
        """Test webhook delivery"""
        test_payload = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "firm_id": firm_id
        }

        await external_api_manager.trigger_webhook(firm_id, event_type, test_payload)
        return {"status": "test_triggered"}

    @router.post("/graphql")
    async def graphql_endpoint(
        query_data: GraphQLQueryModel,
        api_key: APIKey = Depends(get_api_key)
    ):
        """GraphQL endpoint"""
        try:
            result = await external_api_manager.execute_graphql_query(
                query_data.query,
                query_data.variables,
                api_key
            )
            return result
        except Exception as e:
            return {"data": None, "errors": [str(e)]}

    @router.get("/analytics/{firm_id}")
    async def get_api_analytics(
        firm_id: str,
        start_date: datetime = Query(...),
        end_date: datetime = Query(...),
        api_key: APIKey = Depends(get_api_key)
    ):
        """Get API usage analytics"""
        if api_key.firm_id != firm_id:
            raise HTTPException(status_code=403, detail="Access denied")

        try:
            analytics = await external_api_manager.get_api_analytics(
                firm_id, start_date, end_date
            )
            return analytics
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/rate-limits")
    async def get_rate_limits(api_key: APIKey = Depends(get_api_key)):
        """Get current rate limit status"""
        rate_check = await external_api_manager.check_rate_limit(api_key)
        return rate_check

    @router.get("/health")
    async def api_health():
        """API health check"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }

    return router


async def initialize_external_api_system():
    """Initialize the external API system"""
    print("Initializing external API access system...")

    # Create sample API key for demonstration
    sample_api_key = await external_api_manager.create_api_key(
        "demo_firm",
        "Demo API Key",
        ["documents.read", "documents.write", "cases.read", "analytics.read"],
        "system",
        "Sample API key for demonstration"
    )

    # Create sample webhook
    sample_webhook = await external_api_manager.create_webhook(
        "demo_firm",
        "Demo Webhook",
        "https://example.com/webhook",
        [WebhookEvent.DOCUMENT_ANALYZED, WebhookEvent.CASE_UPDATED]
    )

    print("✓ External API manager initialized")
    print("✓ GraphQL schema configured")
    print("✓ Rate limiting system active")
    print("✓ Webhook delivery system running")
    print(f"✓ Sample API key: {sample_api_key.key_id}")
    print(f"✓ Sample webhook: {sample_webhook.webhook_id}")
    print("🔗 External API access system ready!")