"""
Webhook Receiver System
Comprehensive webhook handling for PACER, court systems, payment processors, and legal service integrations.
"""

import asyncio
import json
import logging
import hashlib
import hmac
import sqlite3
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union, Callable
from pathlib import Path
import ipaddress
from cryptography.fernet import Fernet
import aioredis
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import stripe
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Webhook data models
class WebhookEventType:
    # PACER webhooks
    PACER_NEW_FILING = "pacer.new_filing"
    PACER_DOCKET_UPDATE = "pacer.docket_update"
    PACER_CALENDAR_CHANGE = "pacer.calendar_change"
    PACER_DOCUMENT_AVAILABLE = "pacer.document_available"

    # Court system webhooks
    COURT_FILING_CONFIRMATION = "court.filing_confirmation"
    COURT_HEARING_UPDATE = "court.hearing_update"
    COURT_JUDGE_ASSIGNMENT = "court.judge_assignment"
    COURT_CLOSURE_DELAY = "court.closure_delay"

    # Payment webhooks (Stripe)
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILURE = "payment.failure"
    SUBSCRIPTION_UPDATE = "subscription.update"
    REFUND_PROCESSED = "refund.processed"
    DISPUTE_CREATED = "dispute.created"

    # Legal service webhooks
    BACKGROUND_CHECK_COMPLETE = "background_check.complete"
    CREDIT_REPORT_READY = "credit_report.ready"
    STATE_BAR_UPDATE = "state_bar.update"
    LEGAL_RESEARCH_ALERT = "legal_research.alert"

@dataclass
class WebhookEvent:
    """Standard webhook event structure"""
    event_id: str
    event_type: str
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str]
    headers: Dict[str, str]
    ip_address: str
    user_agent: Optional[str]
    retries: int = 0
    processed: bool = False
    error_message: Optional[str] = None

class PacerFilingWebhook(BaseModel):
    """PACER new filing webhook payload"""
    case_number: str
    court_code: str
    filing_date: str
    document_type: str
    filing_party: str
    docket_entry_number: int
    document_url: Optional[str]
    filing_fee: Optional[float]
    sealed: bool = False

    @validator('case_number')
    def validate_case_number(cls, v):
        if not v or len(v) < 5:
            raise ValueError('Invalid case number')
        return v

class CourtHearingWebhook(BaseModel):
    """Court hearing update webhook payload"""
    case_number: str
    court_code: str
    hearing_type: str
    hearing_date: str
    hearing_time: str
    judge_name: str
    courtroom: str
    status: str  # scheduled, rescheduled, cancelled
    participants: List[str]

class StripeWebhook(BaseModel):
    """Stripe payment webhook payload"""
    id: str
    object: str
    created: int
    type: str
    data: Dict[str, Any]
    livemode: bool
    pending_webhooks: int
    request: Dict[str, Any]

class WebhookSecurity:
    """Webhook security validation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.allowed_ips = self._parse_allowed_ips(config.get('allowed_ips', []))
        self.secrets = config.get('webhook_secrets', {})

    def _parse_allowed_ips(self, ip_list: List[str]) -> List[ipaddress.IPv4Network]:
        """Parse allowed IP addresses and networks"""
        networks = []
        for ip_str in ip_list:
            try:
                if '/' in ip_str:
                    networks.append(ipaddress.IPv4Network(ip_str))
                else:
                    networks.append(ipaddress.IPv4Network(f"{ip_str}/32"))
            except ValueError as e:
                logger.warning(f"Invalid IP address format: {ip_str}: {e}")
        return networks

    def verify_ip_address(self, ip_address: str) -> bool:
        """Verify if IP address is allowed"""
        if not self.allowed_ips:
            return True  # No restrictions

        try:
            client_ip = ipaddress.IPv4Address(ip_address)
            return any(client_ip in network for network in self.allowed_ips)
        except ValueError:
            logger.warning(f"Invalid IP address: {ip_address}")
            return False

    def verify_signature(self, payload: bytes, signature: str, source: str) -> bool:
        """Verify webhook signature"""
        secret = self.secrets.get(source)
        if not secret:
            logger.warning(f"No secret configured for source: {source}")
            return False

        if source == 'stripe':
            return self._verify_stripe_signature(payload, signature, secret)
        elif source in ['pacer', 'court']:
            return self._verify_hmac_signature(payload, signature, secret)
        else:
            return self._verify_custom_signature(payload, signature, secret, source)

    def _verify_stripe_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            stripe.Webhook.construct_event(payload, signature, secret)
            return True
        except (stripe.error.SignatureVerificationError, ValueError) as e:
            logger.warning(f"Stripe signature verification failed: {e}")
            return False

    def _verify_hmac_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify HMAC SHA256 signature"""
        try:
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()

            # Remove prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]

            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.warning(f"HMAC signature verification failed: {e}")
            return False

    def _verify_custom_signature(self, payload: bytes, signature: str, secret: str, source: str) -> bool:
        """Verify custom signature format"""
        # Implementation would depend on specific source requirements
        logger.info(f"Custom signature verification for {source} not implemented")
        return True

class WebhookRateLimiter:
    """Rate limiting for webhook endpoints"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis = None

    async def init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis = await aioredis.from_url(self.redis_url)
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None

    async def is_rate_limited(self, ip_address: str, endpoint: str, limit: int = 100, window: int = 3600) -> bool:
        """Check if request is rate limited"""
        if not self.redis:
            return False

        key = f"webhook_rate_limit:{ip_address}:{endpoint}"

        try:
            current = await self.redis.get(key)
            if current is None:
                await self.redis.setex(key, window, 1)
                return False
            elif int(current) >= limit:
                return True
            else:
                await self.redis.incr(key)
                return False
        except Exception as e:
            logger.error(f"Rate limiting check failed: {e}")
            return False

class WebhookDeadLetterQueue:
    """Dead letter queue for failed webhooks"""

    def __init__(self, db_path: str = "webhooks.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize dead letter queue database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dead_letter_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    next_retry_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            """)

    async def add_failed_webhook(self, event: WebhookEvent, error: str, max_retries: int = 3):
        """Add failed webhook to dead letter queue"""
        next_retry = datetime.now() + timedelta(minutes=5 * (event.retries + 1))

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO dead_letter_queue
                (event_id, event_type, source, payload, error_message, retry_count, max_retries, next_retry_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id, event.event_type, event.source,
                json.dumps(asdict(event)), error, event.retries, max_retries,
                next_retry.isoformat()
            ))

    async def get_pending_retries(self) -> List[WebhookEvent]:
        """Get webhooks ready for retry"""
        events = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM dead_letter_queue
                WHERE retry_count < max_retries
                AND next_retry_at <= ?
                AND resolved_at IS NULL
                ORDER BY next_retry_at
            """, (datetime.now().isoformat(),))

            for row in cursor.fetchall():
                try:
                    event_data = json.loads(row['payload'])
                    event = WebhookEvent(**event_data)
                    event.retries = row['retry_count']
                    events.append(event)
                except Exception as e:
                    logger.error(f"Failed to deserialize webhook event: {e}")

        return events

class WebhookProcessor:
    """Process different types of webhooks"""

    def __init__(self):
        self.handlers: Dict[str, Callable] = {
            WebhookEventType.PACER_NEW_FILING: self._handle_pacer_filing,
            WebhookEventType.PACER_DOCKET_UPDATE: self._handle_pacer_docket_update,
            WebhookEventType.PACER_CALENDAR_CHANGE: self._handle_pacer_calendar_change,
            WebhookEventType.PACER_DOCUMENT_AVAILABLE: self._handle_pacer_document,
            WebhookEventType.COURT_FILING_CONFIRMATION: self._handle_court_filing,
            WebhookEventType.COURT_HEARING_UPDATE: self._handle_court_hearing,
            WebhookEventType.COURT_JUDGE_ASSIGNMENT: self._handle_judge_assignment,
            WebhookEventType.COURT_CLOSURE_DELAY: self._handle_court_closure,
            WebhookEventType.PAYMENT_SUCCESS: self._handle_payment_success,
            WebhookEventType.PAYMENT_FAILURE: self._handle_payment_failure,
            WebhookEventType.SUBSCRIPTION_UPDATE: self._handle_subscription_update,
            WebhookEventType.REFUND_PROCESSED: self._handle_refund,
            WebhookEventType.DISPUTE_CREATED: self._handle_dispute,
            WebhookEventType.BACKGROUND_CHECK_COMPLETE: self._handle_background_check,
            WebhookEventType.CREDIT_REPORT_READY: self._handle_credit_report,
            WebhookEventType.STATE_BAR_UPDATE: self._handle_state_bar_update,
            WebhookEventType.LEGAL_RESEARCH_ALERT: self._handle_legal_research_alert
        }

    async def process_webhook(self, event: WebhookEvent) -> bool:
        """Process a webhook event"""
        handler = self.handlers.get(event.event_type)
        if not handler:
            logger.warning(f"No handler for event type: {event.event_type}")
            return False

        try:
            await handler(event)
            return True
        except Exception as e:
            logger.error(f"Failed to process webhook {event.event_id}: {e}")
            event.error_message = str(e)
            return False

    async def _handle_pacer_filing(self, event: WebhookEvent):
        """Handle PACER new filing webhook"""
        logger.info(f"Processing PACER filing: {event.event_id}")

        # Extract filing data
        filing_data = event.data
        case_number = filing_data.get('case_number')
        court_code = filing_data.get('court_code')
        document_type = filing_data.get('document_type')

        # Store in database
        await self._store_court_filing({
            'case_number': case_number,
            'court_code': court_code,
            'document_type': document_type,
            'filing_date': filing_data.get('filing_date'),
            'filing_party': filing_data.get('filing_party'),
            'docket_entry_number': filing_data.get('docket_entry_number'),
            'document_url': filing_data.get('document_url'),
            'sealed': filing_data.get('sealed', False),
            'source': 'pacer',
            'webhook_event_id': event.event_id
        })

        # Trigger notifications for relevant cases
        await self._notify_case_updates(case_number, 'new_filing', filing_data)

        # Auto-download unsealed documents if configured
        if not filing_data.get('sealed') and filing_data.get('document_url'):
            await self._schedule_document_download(filing_data.get('document_url'), case_number)

    async def _handle_pacer_docket_update(self, event: WebhookEvent):
        """Handle PACER docket update webhook"""
        logger.info(f"Processing PACER docket update: {event.event_id}")

        docket_data = event.data
        case_number = docket_data.get('case_number')

        # Update case docket in database
        await self._update_case_docket(case_number, docket_data)

        # Check for deadline changes
        if 'deadlines' in docket_data:
            await self._update_case_deadlines(case_number, docket_data['deadlines'])

        # Notify relevant users
        await self._notify_case_updates(case_number, 'docket_update', docket_data)

    async def _handle_pacer_calendar_change(self, event: WebhookEvent):
        """Handle PACER calendar change webhook"""
        logger.info(f"Processing PACER calendar change: {event.event_id}")

        calendar_data = event.data
        case_number = calendar_data.get('case_number')

        # Update hearing schedule
        await self._update_hearing_schedule(case_number, calendar_data)

        # Send urgent notifications for hearing changes
        await self._notify_urgent_calendar_change(case_number, calendar_data)

    async def _handle_pacer_document(self, event: WebhookEvent):
        """Handle PACER document available webhook"""
        logger.info(f"Processing PACER document: {event.event_id}")

        doc_data = event.data

        # Schedule document download
        await self._schedule_document_download(
            doc_data.get('document_url'),
            doc_data.get('case_number'),
            doc_data.get('document_id')
        )

    async def _handle_court_filing(self, event: WebhookEvent):
        """Handle court filing confirmation webhook"""
        logger.info(f"Processing court filing confirmation: {event.event_id}")

        filing_data = event.data

        # Update filing status
        await self._update_filing_status(
            filing_data.get('filing_id'),
            'confirmed',
            filing_data
        )

        # Generate confirmation receipt
        await self._generate_filing_receipt(filing_data)

    async def _handle_court_hearing(self, event: WebhookEvent):
        """Handle court hearing update webhook"""
        logger.info(f"Processing court hearing update: {event.event_id}")

        hearing_data = event.data
        case_number = hearing_data.get('case_number')

        # Update hearing in calendar
        await self._update_hearing_schedule(case_number, hearing_data)

        # Send calendar invites if needed
        if hearing_data.get('status') == 'scheduled':
            await self._send_calendar_invites(case_number, hearing_data)

    async def _handle_judge_assignment(self, event: WebhookEvent):
        """Handle judge assignment change webhook"""
        logger.info(f"Processing judge assignment: {event.event_id}")

        assignment_data = event.data
        case_number = assignment_data.get('case_number')

        # Update case judge
        await self._update_case_judge(case_number, assignment_data)

        # Notify case team
        await self._notify_judge_assignment(case_number, assignment_data)

    async def _handle_court_closure(self, event: WebhookEvent):
        """Handle court closure/delay webhook"""
        logger.info(f"Processing court closure: {event.event_id}")

        closure_data = event.data

        # Update court status
        await self._update_court_status(
            closure_data.get('court_code'),
            closure_data.get('status'),
            closure_data
        )

        # Reschedule affected hearings
        await self._reschedule_affected_hearings(closure_data)

    async def _handle_payment_success(self, event: WebhookEvent):
        """Handle successful payment webhook"""
        logger.info(f"Processing payment success: {event.event_id}")

        payment_data = event.data

        # Update payment status
        await self._update_payment_status(
            payment_data.get('payment_intent_id'),
            'succeeded',
            payment_data
        )

        # Activate services
        await self._activate_paid_services(payment_data)

        # Send receipt
        await self._send_payment_receipt(payment_data)

    async def _handle_payment_failure(self, event: WebhookEvent):
        """Handle failed payment webhook"""
        logger.info(f"Processing payment failure: {event.event_id}")

        payment_data = event.data

        # Update payment status
        await self._update_payment_status(
            payment_data.get('payment_intent_id'),
            'failed',
            payment_data
        )

        # Send failure notification
        await self._send_payment_failure_notification(payment_data)

        # Suspend services if needed
        await self._handle_payment_failure_consequences(payment_data)

    async def _handle_subscription_update(self, event: WebhookEvent):
        """Handle subscription update webhook"""
        logger.info(f"Processing subscription update: {event.event_id}")

        subscription_data = event.data

        # Update subscription in database
        await self._update_subscription(subscription_data)

        # Update user access levels
        await self._update_user_access_levels(subscription_data)

    async def _handle_refund(self, event: WebhookEvent):
        """Handle refund processed webhook"""
        logger.info(f"Processing refund: {event.event_id}")

        refund_data = event.data

        # Update refund status
        await self._update_refund_status(refund_data)

        # Send refund confirmation
        await self._send_refund_confirmation(refund_data)

    async def _handle_dispute(self, event: WebhookEvent):
        """Handle dispute created webhook"""
        logger.info(f"Processing dispute: {event.event_id}")

        dispute_data = event.data

        # Create dispute record
        await self._create_dispute_record(dispute_data)

        # Alert legal team
        await self._alert_dispute_team(dispute_data)

    async def _handle_background_check(self, event: WebhookEvent):
        """Handle background check completion webhook"""
        logger.info(f"Processing background check: {event.event_id}")

        check_data = event.data

        # Store background check results
        await self._store_background_check_results(check_data)

        # Update client verification status
        await self._update_client_verification(check_data)

    async def _handle_credit_report(self, event: WebhookEvent):
        """Handle credit report ready webhook"""
        logger.info(f"Processing credit report: {event.event_id}")

        report_data = event.data

        # Store credit report
        await self._store_credit_report(report_data)

        # Notify bankruptcy attorney
        await self._notify_bankruptcy_attorney(report_data)

    async def _handle_state_bar_update(self, event: WebhookEvent):
        """Handle state bar update webhook"""
        logger.info(f"Processing state bar update: {event.event_id}")

        bar_data = event.data

        # Update attorney status
        await self._update_attorney_status(bar_data)

        # Check for disciplinary actions
        if bar_data.get('disciplinary_action'):
            await self._handle_disciplinary_action(bar_data)

    async def _handle_legal_research_alert(self, event: WebhookEvent):
        """Handle legal research alert webhook"""
        logger.info(f"Processing legal research alert: {event.event_id}")

        alert_data = event.data

        # Store research alert
        await self._store_research_alert(alert_data)

        # Notify relevant attorneys
        await self._notify_research_alert(alert_data)

    # Helper methods for database operations
    async def _store_court_filing(self, filing_data: Dict[str, Any]):
        """Store court filing in database"""
        # Implementation would store in legal_cases.db or appropriate database
        logger.info(f"Storing court filing: {filing_data.get('case_number')}")

    async def _update_case_docket(self, case_number: str, docket_data: Dict[str, Any]):
        """Update case docket information"""
        logger.info(f"Updating docket for case: {case_number}")

    async def _update_hearing_schedule(self, case_number: str, hearing_data: Dict[str, Any]):
        """Update hearing schedule"""
        logger.info(f"Updating hearing schedule for case: {case_number}")

    async def _notify_case_updates(self, case_number: str, update_type: str, data: Dict[str, Any]):
        """Send notifications for case updates"""
        logger.info(f"Notifying case updates for {case_number}: {update_type}")

    async def _schedule_document_download(self, url: str, case_number: str, document_id: str = None):
        """Schedule document download"""
        logger.info(f"Scheduling document download for case: {case_number}")

    async def _update_payment_status(self, payment_id: str, status: str, data: Dict[str, Any]):
        """Update payment status"""
        logger.info(f"Updating payment {payment_id} status to: {status}")

    async def _activate_paid_services(self, payment_data: Dict[str, Any]):
        """Activate services after successful payment"""
        logger.info(f"Activating services for payment: {payment_data.get('id')}")

    async def _update_subscription(self, subscription_data: Dict[str, Any]):
        """Update subscription information"""
        logger.info(f"Updating subscription: {subscription_data.get('id')}")

class WebhookReceiver:
    """Main webhook receiver system"""

    def __init__(self, config_path: str = "webhook_config.json"):
        self.config = self._load_config(config_path)
        self.security = WebhookSecurity(self.config.get('security', {}))
        self.rate_limiter = WebhookRateLimiter(self.config.get('redis_url', 'redis://localhost:6379'))
        self.dead_letter_queue = WebhookDeadLetterQueue(self.config.get('db_path', 'webhooks.db'))
        self.processor = WebhookProcessor()

        self.app = FastAPI(title="Legal AI Webhook Receiver")
        self._setup_routes()

        # Initialize monitoring
        self.webhook_stats = {
            'total_received': 0,
            'total_processed': 0,
            'total_failed': 0,
            'by_source': {},
            'by_type': {}
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load webhook configuration"""
        default_config = {
            'security': {
                'allowed_ips': [],
                'webhook_secrets': {},
                'verify_signatures': True
            },
            'rate_limiting': {
                'enabled': True,
                'default_limit': 1000,
                'default_window': 3600
            },
            'retry_policy': {
                'max_retries': 3,
                'initial_delay': 300,
                'backoff_multiplier': 2
            },
            'monitoring': {
                'enabled': True,
                'metrics_retention_days': 30
            }
        }

        try:
            if Path(config_path).exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            logger.warning(f"Could not load webhook config: {e}, using defaults")

        return default_config

    def _setup_routes(self):
        """Setup FastAPI routes for webhooks"""

        @self.app.post("/webhooks/pacer/filing")
        async def handle_pacer_filing(request: Request, background_tasks: BackgroundTasks):
            return await self._handle_webhook(request, background_tasks, 'pacer', WebhookEventType.PACER_NEW_FILING)

        @self.app.post("/webhooks/pacer/docket")
        async def handle_pacer_docket(request: Request, background_tasks: BackgroundTasks):
            return await self._handle_webhook(request, background_tasks, 'pacer', WebhookEventType.PACER_DOCKET_UPDATE)

        @self.app.post("/webhooks/pacer/calendar")
        async def handle_pacer_calendar(request: Request, background_tasks: BackgroundTasks):
            return await self._handle_webhook(request, background_tasks, 'pacer', WebhookEventType.PACER_CALENDAR_CHANGE)

        @self.app.post("/webhooks/pacer/document")
        async def handle_pacer_document(request: Request, background_tasks: BackgroundTasks):
            return await self._handle_webhook(request, background_tasks, 'pacer', WebhookEventType.PACER_DOCUMENT_AVAILABLE)

        @self.app.post("/webhooks/court/filing")
        async def handle_court_filing(request: Request, background_tasks: BackgroundTasks):
            return await self._handle_webhook(request, background_tasks, 'court', WebhookEventType.COURT_FILING_CONFIRMATION)

        @self.app.post("/webhooks/court/hearing")
        async def handle_court_hearing(request: Request, background_tasks: BackgroundTasks):
            return await self._handle_webhook(request, background_tasks, 'court', WebhookEventType.COURT_HEARING_UPDATE)

        @self.app.post("/webhooks/court/judge")
        async def handle_court_judge(request: Request, background_tasks: BackgroundTasks):
            return await self._handle_webhook(request, background_tasks, 'court', WebhookEventType.COURT_JUDGE_ASSIGNMENT)

        @self.app.post("/webhooks/court/closure")
        async def handle_court_closure(request: Request, background_tasks: BackgroundTasks):
            return await self._handle_webhook(request, background_tasks, 'court', WebhookEventType.COURT_CLOSURE_DELAY)

        @self.app.post("/webhooks/stripe")
        async def handle_stripe_webhook(request: Request, background_tasks: BackgroundTasks):
            return await self._handle_stripe_webhook(request, background_tasks)

        @self.app.post("/webhooks/background-check")
        async def handle_background_check(request: Request, background_tasks: BackgroundTasks):
            return await self._handle_webhook(request, background_tasks, 'background_check', WebhookEventType.BACKGROUND_CHECK_COMPLETE)

        @self.app.post("/webhooks/credit-report")
        async def handle_credit_report(request: Request, background_tasks: BackgroundTasks):
            return await self._handle_webhook(request, background_tasks, 'credit_report', WebhookEventType.CREDIT_REPORT_READY)

        @self.app.post("/webhooks/state-bar/{state}")
        async def handle_state_bar(state: str, request: Request, background_tasks: BackgroundTasks):
            return await self._handle_webhook(request, background_tasks, f'state_bar_{state}', WebhookEventType.STATE_BAR_UPDATE)

        @self.app.post("/webhooks/legal-research")
        async def handle_legal_research(request: Request, background_tasks: BackgroundTasks):
            return await self._handle_webhook(request, background_tasks, 'legal_research', WebhookEventType.LEGAL_RESEARCH_ALERT)

        @self.app.get("/webhooks/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        @self.app.get("/webhooks/stats")
        async def webhook_stats():
            return self.webhook_stats

    async def _handle_webhook(self, request: Request, background_tasks: BackgroundTasks,
                            source: str, event_type: str) -> Dict[str, Any]:
        """Generic webhook handler"""

        # Get client IP
        client_ip = request.client.host
        if 'x-forwarded-for' in request.headers:
            client_ip = request.headers['x-forwarded-for'].split(',')[0].strip()

        # Rate limiting
        if self.config.get('rate_limiting', {}).get('enabled', True):
            if await self.rate_limiter.is_rate_limited(client_ip, source):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # IP allowlisting
        if not self.security.verify_ip_address(client_ip):
            logger.warning(f"Webhook from unauthorized IP: {client_ip}")
            raise HTTPException(status_code=403, detail="Unauthorized IP address")

        # Get payload and headers
        payload = await request.body()
        headers = dict(request.headers)

        # Signature verification
        signature = headers.get('x-signature') or headers.get('stripe-signature')
        if self.config.get('security', {}).get('verify_signatures', True) and signature:
            if not self.security.verify_signature(payload, signature, source):
                logger.warning(f"Invalid signature for webhook from {source}")
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse payload
        try:
            if headers.get('content-type', '').startswith('application/json'):
                data = json.loads(payload.decode('utf-8'))
            elif headers.get('content-type', '').startswith('application/xml'):
                data = self._parse_xml_payload(payload)
            else:
                data = {'raw_payload': payload.decode('utf-8')}
        except Exception as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload format")

        # Create webhook event
        event = WebhookEvent(
            event_id=f"{source}_{int(time.time())}_{hash(payload) % 10000}",
            event_type=event_type,
            source=source,
            timestamp=datetime.now(),
            data=data,
            signature=signature,
            headers=headers,
            ip_address=client_ip,
            user_agent=headers.get('user-agent')
        )

        # Update statistics
        self._update_stats(source, event_type)

        # Process webhook in background
        background_tasks.add_task(self._process_webhook_async, event)

        return {"status": "received", "event_id": event.event_id}

    async def _handle_stripe_webhook(self, request: Request, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        """Handle Stripe-specific webhooks"""
        payload = await request.body()
        signature = request.headers.get('stripe-signature')

        if not signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")

        try:
            stripe_event = stripe.Webhook.construct_event(
                payload, signature, self.security.secrets.get('stripe', '')
            )
        except (stripe.error.SignatureVerificationError, ValueError) as e:
            logger.warning(f"Stripe webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Map Stripe event types to our event types
        event_type_mapping = {
            'payment_intent.succeeded': WebhookEventType.PAYMENT_SUCCESS,
            'payment_intent.payment_failed': WebhookEventType.PAYMENT_FAILURE,
            'customer.subscription.updated': WebhookEventType.SUBSCRIPTION_UPDATE,
            'charge.dispute.created': WebhookEventType.DISPUTE_CREATED,
            'refund.created': WebhookEventType.REFUND_PROCESSED
        }

        our_event_type = event_type_mapping.get(stripe_event['type'], 'stripe.unknown')

        # Create our webhook event
        event = WebhookEvent(
            event_id=stripe_event['id'],
            event_type=our_event_type,
            source='stripe',
            timestamp=datetime.fromtimestamp(stripe_event['created']),
            data=stripe_event,
            signature=signature,
            headers=dict(request.headers),
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent')
        )

        # Update statistics
        self._update_stats('stripe', our_event_type)

        # Process webhook in background
        background_tasks.add_task(self._process_webhook_async, event)

        return {"status": "received", "event_id": event.event_id}

    def _parse_xml_payload(self, payload: bytes) -> Dict[str, Any]:
        """Parse XML payload"""
        try:
            root = ET.fromstring(payload.decode('utf-8'))
            return self._xml_to_dict(root)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML payload: {e}")
            return {'raw_xml': payload.decode('utf-8')}

    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}

        # Add attributes
        if element.attrib:
            result.update(element.attrib)

        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['text'] = element.text.strip()

        # Add children
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data

        return result

    async def _process_webhook_async(self, event: WebhookEvent):
        """Process webhook asynchronously"""
        try:
            success = await self.processor.process_webhook(event)

            if success:
                event.processed = True
                self.webhook_stats['total_processed'] += 1
                logger.info(f"Successfully processed webhook: {event.event_id}")
            else:
                await self._handle_webhook_failure(event)

        except Exception as e:
            logger.error(f"Unexpected error processing webhook {event.event_id}: {e}")
            event.error_message = str(e)
            await self._handle_webhook_failure(event)

    async def _handle_webhook_failure(self, event: WebhookEvent):
        """Handle failed webhook processing"""
        self.webhook_stats['total_failed'] += 1

        max_retries = self.config.get('retry_policy', {}).get('max_retries', 3)

        if event.retries < max_retries:
            # Add to dead letter queue for retry
            await self.dead_letter_queue.add_failed_webhook(
                event,
                event.error_message or "Processing failed",
                max_retries
            )
            logger.info(f"Added webhook {event.event_id} to dead letter queue for retry")
        else:
            logger.error(f"Webhook {event.event_id} failed permanently after {event.retries} retries")

    def _update_stats(self, source: str, event_type: str):
        """Update webhook statistics"""
        self.webhook_stats['total_received'] += 1

        if source not in self.webhook_stats['by_source']:
            self.webhook_stats['by_source'][source] = 0
        self.webhook_stats['by_source'][source] += 1

        if event_type not in self.webhook_stats['by_type']:
            self.webhook_stats['by_type'][event_type] = 0
        self.webhook_stats['by_type'][event_type] += 1

    async def start_retry_processor(self):
        """Start background task to process webhook retries"""
        while True:
            try:
                pending_events = await self.dead_letter_queue.get_pending_retries()

                for event in pending_events:
                    logger.info(f"Retrying webhook: {event.event_id} (attempt {event.retries + 1})")
                    event.retries += 1
                    await self._process_webhook_async(event)

                # Wait before checking again
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in retry processor: {e}")
                await asyncio.sleep(60)

    async def get_webhook_metrics(self) -> Dict[str, Any]:
        """Get comprehensive webhook metrics"""
        return {
            'statistics': self.webhook_stats,
            'configuration': {
                'rate_limiting_enabled': self.config.get('rate_limiting', {}).get('enabled'),
                'signature_verification': self.config.get('security', {}).get('verify_signatures'),
                'max_retries': self.config.get('retry_policy', {}).get('max_retries')
            },
            'health': {
                'redis_connected': self.rate_limiter.redis is not None,
                'dead_letter_queue_size': await self._get_dlq_size()
            }
        }

    async def _get_dlq_size(self) -> int:
        """Get dead letter queue size"""
        try:
            with sqlite3.connect(self.dead_letter_queue.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM dead_letter_queue
                    WHERE resolved_at IS NULL AND retry_count < max_retries
                """)
                return cursor.fetchone()[0]
        except Exception:
            return 0

# Example usage and testing
async def main():
    """Example usage of the webhook receiver"""
    receiver = WebhookReceiver()

    # Initialize components
    await receiver.rate_limiter.init_redis()

    # Start retry processor
    retry_task = asyncio.create_task(receiver.start_retry_processor())

    # Get metrics
    metrics = await receiver.get_webhook_metrics()
    print(f"Webhook metrics: {json.dumps(metrics, indent=2)}")

    # The FastAPI app can be run with: uvicorn receiver:receiver.app --host 0.0.0.0 --port 8006

if __name__ == "__main__":
    asyncio.run(main())