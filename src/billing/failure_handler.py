"""
Comprehensive Payment Failure Handling System
Manages payment failures, retry logic, alternative payment methods, and service degradation.
"""

import asyncio
import json
import logging
import sqlite3
import smtplib
import ssl
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import aiofiles
import aiohttp
import stripe
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REQUIRES_ACTION = "requires_action"
    CANCELED = "canceled"
    REFUNDED = "refunded"

class FailureReason(Enum):
    INSUFFICIENT_FUNDS = "insufficient_funds"
    CARD_DECLINED = "card_declined"
    EXPIRED_CARD = "expired_card"
    INVALID_CARD = "invalid_card"
    PROCESSING_ERROR = "processing_error"
    FRAUD_SUSPECTED = "fraud_suspected"
    NETWORK_ERROR = "network_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    LIMIT_EXCEEDED = "limit_exceeded"
    AUTHENTICATION_FAILED = "authentication_failed"

class RetryStrategy(Enum):
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    SCHEDULED = "scheduled"
    MANUAL = "manual"

class ServiceLevel(Enum):
    FULL = "full"
    LIMITED = "limited"
    BASIC = "basic"
    SUSPENDED = "suspended"

class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"

@dataclass
class PaymentAttempt:
    attempt_id: str
    payment_id: str
    user_id: str
    organization_id: Optional[str]
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    payment_method_id: str
    status: PaymentStatus
    failure_reason: Optional[FailureReason]
    failure_message: Optional[str]
    attempt_number: int
    attempted_at: datetime
    processing_time_ms: Optional[int]
    gateway_response: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]

@dataclass
class PaymentFailure:
    failure_id: str
    payment_id: str
    user_id: str
    organization_id: Optional[str]
    original_amount: Decimal
    currency: str
    failure_reason: FailureReason
    failure_message: str
    failed_at: datetime
    attempts: List[PaymentAttempt]
    retry_strategy: RetryStrategy
    next_retry_at: Optional[datetime]
    max_retries: int
    current_retry_count: int
    alternative_methods_offered: List[PaymentMethod]
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolution_method: Optional[str]

@dataclass
class ServiceRestriction:
    restriction_id: str
    user_id: str
    organization_id: Optional[str]
    service_level: ServiceLevel
    restriction_reason: str
    restricted_features: List[str]
    started_at: datetime
    expires_at: Optional[datetime]
    payment_required_amount: Optional[Decimal]
    grace_period_ends_at: Optional[datetime]
    is_active: bool

@dataclass
class AlternativePaymentOption:
    option_id: str
    payment_method: PaymentMethod
    display_name: str
    provider_name: str
    setup_fee: Decimal
    processing_fee_percentage: float
    processing_fee_fixed: Decimal
    min_amount: Decimal
    max_amount: Decimal
    supported_currencies: List[str]
    setup_time_hours: int
    is_available: bool
    priority: int

class PaymentFailureHandler:
    def __init__(self, config_path: str = "payment_failure_config.json"):
        self.config_path = config_path
        self.failures_db_path = "payment_failures.db"

        # Payment gateways
        self.stripe_client = None
        self.paypal_client = None

        # Failure tracking
        self.active_failures: Dict[str, PaymentFailure] = {}
        self.retry_queues: Dict[RetryStrategy, List[PaymentFailure]] = {
            RetryStrategy.IMMEDIATE: [],
            RetryStrategy.EXPONENTIAL_BACKOFF: [],
            RetryStrategy.SCHEDULED: []
        }

        # Service restrictions
        self.active_restrictions: Dict[str, ServiceRestriction] = {}

        # Alternative payment methods
        self.alternative_methods: List[AlternativePaymentOption] = []

        # Background tasks
        self.background_tasks = []

        # Initialize system
        asyncio.create_task(self._initialize_system())

    async def _initialize_system(self):
        """Initialize the payment failure handling system"""
        try:
            await self._setup_database()
            await self._load_configuration()
            await self._initialize_payment_gateways()
            await self._load_alternative_payment_methods()
            await self._start_background_tasks()
            logger.info("Payment failure handler initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing payment failure handler: {str(e)}")
            raise

    async def _setup_database(self):
        """Setup SQLite database for payment failure tracking"""
        conn = sqlite3.connect(self.failures_db_path)
        cursor = conn.cursor()

        # Payment failures table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_failures (
                failure_id TEXT PRIMARY KEY,
                payment_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                organization_id TEXT,
                original_amount DECIMAL NOT NULL,
                currency TEXT NOT NULL,
                failure_reason TEXT NOT NULL,
                failure_message TEXT,
                failed_at TEXT NOT NULL,
                retry_strategy TEXT NOT NULL,
                next_retry_at TEXT,
                max_retries INTEGER NOT NULL,
                current_retry_count INTEGER DEFAULT 0,
                alternative_methods_offered TEXT,
                is_resolved BOOLEAN DEFAULT FALSE,
                resolved_at TEXT,
                resolution_method TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Payment attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_attempts (
                attempt_id TEXT PRIMARY KEY,
                payment_id TEXT NOT NULL,
                failure_id TEXT,
                user_id TEXT NOT NULL,
                organization_id TEXT,
                amount DECIMAL NOT NULL,
                currency TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                payment_method_id TEXT NOT NULL,
                status TEXT NOT NULL,
                failure_reason TEXT,
                failure_message TEXT,
                attempt_number INTEGER NOT NULL,
                attempted_at TEXT NOT NULL,
                processing_time_ms INTEGER,
                gateway_response TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (failure_id) REFERENCES payment_failures (failure_id)
            )
        """)

        # Service restrictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_restrictions (
                restriction_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                organization_id TEXT,
                service_level TEXT NOT NULL,
                restriction_reason TEXT NOT NULL,
                restricted_features TEXT,
                started_at TEXT NOT NULL,
                expires_at TEXT,
                payment_required_amount DECIMAL,
                grace_period_ends_at TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Alternative payment methods table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alternative_payment_methods (
                option_id TEXT PRIMARY KEY,
                payment_method TEXT NOT NULL,
                display_name TEXT NOT NULL,
                provider_name TEXT NOT NULL,
                setup_fee DECIMAL DEFAULT 0,
                processing_fee_percentage REAL DEFAULT 0,
                processing_fee_fixed DECIMAL DEFAULT 0,
                min_amount DECIMAL DEFAULT 0,
                max_amount DECIMAL,
                supported_currencies TEXT,
                setup_time_hours INTEGER DEFAULT 0,
                is_available BOOLEAN DEFAULT TRUE,
                priority INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Payment recovery analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_recovery_analytics (
                analytics_id TEXT PRIMARY KEY,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                total_failures INTEGER NOT NULL,
                successful_recoveries INTEGER NOT NULL,
                recovery_rate REAL NOT NULL,
                total_recovered_amount DECIMAL NOT NULL,
                avg_recovery_time_hours REAL,
                most_common_failure_reason TEXT,
                most_successful_recovery_method TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_failures_user ON payment_failures(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_failures_status ON payment_failures(is_resolved)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_payment ON payment_attempts(payment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_restrictions_user ON service_restrictions(user_id, is_active)")

        conn.commit()
        conn.close()

    async def _load_configuration(self):
        """Load payment failure configuration"""
        try:
            async with aiofiles.open(self.config_path, 'r') as f:
                config_content = await f.read()
                self.config = json.loads(config_content)
        except FileNotFoundError:
            # Create default configuration
            self.config = self._create_default_config()
            await self._save_configuration()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default payment failure configuration"""
        return {
            "retry_settings": {
                "max_retries": 3,
                "initial_delay_minutes": 5,
                "exponential_backoff_multiplier": 2.0,
                "max_delay_hours": 24,
                "immediate_retry_failures": [
                    "network_error",
                    "service_unavailable",
                    "processing_error"
                ],
                "no_retry_failures": [
                    "fraud_suspected",
                    "invalid_card",
                    "authentication_failed"
                ]
            },
            "service_degradation": {
                "grace_period_hours": 72,
                "warning_periods_hours": [24, 48, 72],
                "restrictions_by_level": {
                    "limited": [
                        "premium_features",
                        "high_volume_processing",
                        "priority_support"
                    ],
                    "basic": [
                        "premium_features",
                        "high_volume_processing",
                        "priority_support",
                        "advanced_analytics",
                        "bulk_operations"
                    ],
                    "suspended": [
                        "all_features"
                    ]
                }
            },
            "notifications": {
                "enabled": True,
                "channels": ["email", "in_app", "webhook"],
                "email_templates": {
                    "payment_failed": "payment_failed_template.html",
                    "retry_scheduled": "retry_scheduled_template.html",
                    "service_restricted": "service_restricted_template.html",
                    "payment_recovered": "payment_recovered_template.html"
                }
            },
            "payment_gateways": {
                "stripe": {
                    "api_key": "your-stripe-secret-key",
                    "webhook_secret": "your-stripe-webhook-secret",
                    "enabled": True
                },
                "paypal": {
                    "client_id": "your-paypal-client-id",
                    "client_secret": "your-paypal-client-secret",
                    "sandbox": True,
                    "enabled": True
                }
            },
            "compliance": {
                "data_retention_days": 2555,  # 7 years
                "pci_compliance_enabled": True,
                "fraud_detection_enabled": True,
                "audit_logging": True
            }
        }

    async def _save_configuration(self):
        """Save configuration to file"""
        async with aiofiles.open(self.config_path, 'w') as f:
            await f.write(json.dumps(self.config, indent=2))

    async def _initialize_payment_gateways(self):
        """Initialize payment gateway clients"""
        # Initialize Stripe
        stripe_config = self.config.get("payment_gateways", {}).get("stripe", {})
        if stripe_config.get("enabled", False):
            stripe.api_key = stripe_config.get("api_key")
            self.stripe_client = stripe

        # PayPal initialization would go here
        # self.paypal_client = ...

    async def _load_alternative_payment_methods(self):
        """Load alternative payment methods from database"""
        conn = sqlite3.connect(self.failures_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM alternative_payment_methods WHERE is_available = TRUE ORDER BY priority DESC")
        rows = cursor.fetchall()

        self.alternative_methods = []
        for row in rows:
            option = AlternativePaymentOption(
                option_id=row[0],
                payment_method=PaymentMethod(row[1]),
                display_name=row[2],
                provider_name=row[3],
                setup_fee=Decimal(str(row[4])),
                processing_fee_percentage=row[5],
                processing_fee_fixed=Decimal(str(row[6])),
                min_amount=Decimal(str(row[7])),
                max_amount=Decimal(str(row[8])) if row[8] else None,
                supported_currencies=json.loads(row[9]),
                setup_time_hours=row[10],
                is_available=bool(row[11]),
                priority=row[12]
            )
            self.alternative_methods.append(option)

        conn.close()

        # Add default methods if none exist
        if not self.alternative_methods:
            await self._create_default_alternative_methods()

    async def _create_default_alternative_methods(self):
        """Create default alternative payment methods"""
        default_methods = [
            AlternativePaymentOption(
                option_id=self._generate_id(),
                payment_method=PaymentMethod.BANK_TRANSFER,
                display_name="Bank Transfer",
                provider_name="ACH",
                setup_fee=Decimal("0.00"),
                processing_fee_percentage=0.8,
                processing_fee_fixed=Decimal("0.30"),
                min_amount=Decimal("1.00"),
                max_amount=Decimal("10000.00"),
                supported_currencies=["USD", "EUR", "GBP"],
                setup_time_hours=24,
                is_available=True,
                priority=1
            ),
            AlternativePaymentOption(
                option_id=self._generate_id(),
                payment_method=PaymentMethod.PAYPAL,
                display_name="PayPal",
                provider_name="PayPal",
                setup_fee=Decimal("0.00"),
                processing_fee_percentage=2.9,
                processing_fee_fixed=Decimal("0.30"),
                min_amount=Decimal("0.01"),
                max_amount=Decimal("60000.00"),
                supported_currencies=["USD", "EUR", "GBP", "CAD", "AUD"],
                setup_time_hours=0,
                is_available=True,
                priority=2
            )
        ]

        for method in default_methods:
            await self._store_alternative_payment_method(method)
            self.alternative_methods.append(method)

    async def _store_alternative_payment_method(self, method: AlternativePaymentOption):
        """Store alternative payment method in database"""
        conn = sqlite3.connect(self.failures_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alternative_payment_methods (
                option_id, payment_method, display_name, provider_name,
                setup_fee, processing_fee_percentage, processing_fee_fixed,
                min_amount, max_amount, supported_currencies,
                setup_time_hours, is_available, priority
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            method.option_id,
            method.payment_method.value,
            method.display_name,
            method.provider_name,
            float(method.setup_fee),
            method.processing_fee_percentage,
            float(method.processing_fee_fixed),
            float(method.min_amount),
            float(method.max_amount) if method.max_amount else None,
            json.dumps(method.supported_currencies),
            method.setup_time_hours,
            method.is_available,
            method.priority
        ))

        conn.commit()
        conn.close()

    async def _start_background_tasks(self):
        """Start background processing tasks"""
        # Retry processor
        retry_task = asyncio.create_task(self._process_retry_queue())
        self.background_tasks.append(retry_task)

        # Service restriction monitor
        restriction_task = asyncio.create_task(self._monitor_service_restrictions())
        self.background_tasks.append(restriction_task)

        # Analytics aggregator
        analytics_task = asyncio.create_task(self._aggregate_recovery_analytics())
        self.background_tasks.append(analytics_task)

        # Grace period monitor
        grace_task = asyncio.create_task(self._monitor_grace_periods())
        self.background_tasks.append(grace_task)

    # Main Payment Failure Handling
    async def handle_payment_failure(self,
                                   payment_id: str,
                                   user_id: str,
                                   organization_id: Optional[str],
                                   amount: Decimal,
                                   currency: str,
                                   payment_method: PaymentMethod,
                                   payment_method_id: str,
                                   failure_reason: FailureReason,
                                   failure_message: str,
                                   gateway_response: Optional[Dict[str, Any]] = None) -> PaymentFailure:
        """Handle a payment failure with appropriate retry and notification logic"""

        failure_id = self._generate_id()
        current_time = datetime.now()

        # Create payment attempt record
        attempt = PaymentAttempt(
            attempt_id=self._generate_id(),
            payment_id=payment_id,
            user_id=user_id,
            organization_id=organization_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            payment_method_id=payment_method_id,
            status=PaymentStatus.FAILED,
            failure_reason=failure_reason,
            failure_message=failure_message,
            attempt_number=1,
            attempted_at=current_time,
            gateway_response=gateway_response,
            metadata={}
        )

        # Determine retry strategy
        retry_strategy = self._determine_retry_strategy(failure_reason)
        max_retries = self.config["retry_settings"]["max_retries"]

        # Calculate next retry time
        next_retry_at = None
        if retry_strategy != RetryStrategy.MANUAL:
            next_retry_at = self._calculate_next_retry_time(retry_strategy, 1)

        # Get alternative payment methods
        alternative_methods = self._get_applicable_alternative_methods(amount, currency)

        # Create payment failure record
        failure = PaymentFailure(
            failure_id=failure_id,
            payment_id=payment_id,
            user_id=user_id,
            organization_id=organization_id,
            original_amount=amount,
            currency=currency,
            failure_reason=failure_reason,
            failure_message=failure_message,
            failed_at=current_time,
            attempts=[attempt],
            retry_strategy=retry_strategy,
            next_retry_at=next_retry_at,
            max_retries=max_retries,
            current_retry_count=0,
            alternative_methods_offered=[method.payment_method for method in alternative_methods],
            is_resolved=False,
            resolved_at=None,
            resolution_method=None
        )

        # Store failure and attempt
        await self._store_payment_failure(failure)
        await self._store_payment_attempt(attempt, failure_id)

        # Add to active failures
        self.active_failures[failure_id] = failure

        # Queue for retry if applicable
        if retry_strategy != RetryStrategy.MANUAL:
            self.retry_queues[retry_strategy].append(failure)

        # Send notifications
        await self._send_failure_notifications(failure, alternative_methods)

        # Apply service restrictions if necessary
        await self._evaluate_service_restrictions(failure)

        logger.info(f"Payment failure {failure_id} handled for user {user_id}")
        return failure

    def _determine_retry_strategy(self, failure_reason: FailureReason) -> RetryStrategy:
        """Determine the appropriate retry strategy for a failure reason"""
        immediate_retry = self.config["retry_settings"]["immediate_retry_failures"]
        no_retry = self.config["retry_settings"]["no_retry_failures"]

        if failure_reason.value in no_retry:
            return RetryStrategy.MANUAL
        elif failure_reason.value in immediate_retry:
            return RetryStrategy.IMMEDIATE
        else:
            return RetryStrategy.EXPONENTIAL_BACKOFF

    def _calculate_next_retry_time(self, strategy: RetryStrategy, retry_count: int) -> datetime:
        """Calculate the next retry time based on strategy"""
        now = datetime.now()

        if strategy == RetryStrategy.IMMEDIATE:
            return now + timedelta(minutes=1)
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            initial_delay = self.config["retry_settings"]["initial_delay_minutes"]
            multiplier = self.config["retry_settings"]["exponential_backoff_multiplier"]
            max_delay_hours = self.config["retry_settings"]["max_delay_hours"]

            delay_minutes = min(
                initial_delay * (multiplier ** retry_count),
                max_delay_hours * 60
            )
            return now + timedelta(minutes=delay_minutes)
        elif strategy == RetryStrategy.SCHEDULED:
            # Schedule for next business day
            return now + timedelta(days=1)
        else:
            return now

    def _get_applicable_alternative_methods(self, amount: Decimal, currency: str) -> List[AlternativePaymentOption]:
        """Get alternative payment methods applicable for the amount and currency"""
        applicable_methods = []

        for method in self.alternative_methods:
            if (method.is_available and
                currency in method.supported_currencies and
                amount >= method.min_amount and
                (method.max_amount is None or amount <= method.max_amount)):
                applicable_methods.append(method)

        # Sort by priority
        applicable_methods.sort(key=lambda x: x.priority, reverse=True)
        return applicable_methods

    async def _store_payment_failure(self, failure: PaymentFailure):
        """Store payment failure in database"""
        conn = sqlite3.connect(self.failures_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO payment_failures (
                failure_id, payment_id, user_id, organization_id,
                original_amount, currency, failure_reason, failure_message,
                failed_at, retry_strategy, next_retry_at, max_retries,
                current_retry_count, alternative_methods_offered
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            failure.failure_id,
            failure.payment_id,
            failure.user_id,
            failure.organization_id,
            float(failure.original_amount),
            failure.currency,
            failure.failure_reason.value,
            failure.failure_message,
            failure.failed_at.isoformat(),
            failure.retry_strategy.value,
            failure.next_retry_at.isoformat() if failure.next_retry_at else None,
            failure.max_retries,
            failure.current_retry_count,
            json.dumps([method.value for method in failure.alternative_methods_offered])
        ))

        conn.commit()
        conn.close()

    async def _store_payment_attempt(self, attempt: PaymentAttempt, failure_id: str):
        """Store payment attempt in database"""
        conn = sqlite3.connect(self.failures_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO payment_attempts (
                attempt_id, payment_id, failure_id, user_id, organization_id,
                amount, currency, payment_method, payment_method_id,
                status, failure_reason, failure_message, attempt_number,
                attempted_at, processing_time_ms, gateway_response, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            attempt.attempt_id,
            attempt.payment_id,
            failure_id,
            attempt.user_id,
            attempt.organization_id,
            float(attempt.amount),
            attempt.currency,
            attempt.payment_method.value,
            attempt.payment_method_id,
            attempt.status.value,
            attempt.failure_reason.value if attempt.failure_reason else None,
            attempt.failure_message,
            attempt.attempt_number,
            attempt.attempted_at.isoformat(),
            attempt.processing_time_ms,
            json.dumps(attempt.gateway_response, default=str) if attempt.gateway_response else None,
            json.dumps(attempt.metadata, default=str)
        ))

        conn.commit()
        conn.close()

    # Retry Processing
    async def retry_payment(self, failure_id: str, new_payment_method: Optional[PaymentMethod] = None) -> bool:
        """Retry a failed payment"""
        if failure_id not in self.active_failures:
            logger.warning(f"Failure {failure_id} not found in active failures")
            return False

        failure = self.active_failures[failure_id]

        if failure.current_retry_count >= failure.max_retries:
            logger.warning(f"Maximum retries exceeded for failure {failure_id}")
            return False

        try:
            # Increment retry count
            failure.current_retry_count += 1
            attempt_number = len(failure.attempts) + 1

            # Use new payment method if provided
            payment_method = new_payment_method or failure.attempts[0].payment_method
            payment_method_id = failure.attempts[0].payment_method_id  # Would need to update for new method

            # Attempt payment
            success, attempt = await self._attempt_payment_retry(
                failure, payment_method, payment_method_id, attempt_number
            )

            failure.attempts.append(attempt)
            await self._store_payment_attempt(attempt, failure_id)

            if success:
                # Payment succeeded
                failure.is_resolved = True
                failure.resolved_at = datetime.now()
                failure.resolution_method = "retry_success"

                await self._update_failure_status(failure)
                await self._remove_service_restrictions(failure.user_id)
                await self._send_recovery_notification(failure)

                # Remove from active failures
                del self.active_failures[failure_id]

                logger.info(f"Payment failure {failure_id} resolved via retry")
                return True
            else:
                # Calculate next retry time
                if failure.current_retry_count < failure.max_retries:
                    failure.next_retry_at = self._calculate_next_retry_time(
                        failure.retry_strategy, failure.current_retry_count
                    )
                    await self._update_failure_status(failure)
                else:
                    # Max retries reached, apply stricter service restrictions
                    await self._apply_final_service_restrictions(failure)

                return False

        except Exception as e:
            logger.error(f"Error retrying payment {failure_id}: {str(e)}")
            return False

    async def _attempt_payment_retry(self,
                                   failure: PaymentFailure,
                                   payment_method: PaymentMethod,
                                   payment_method_id: str,
                                   attempt_number: int) -> tuple[bool, PaymentAttempt]:
        """Attempt to retry a payment"""
        start_time = datetime.now()

        attempt = PaymentAttempt(
            attempt_id=self._generate_id(),
            payment_id=failure.payment_id,
            user_id=failure.user_id,
            organization_id=failure.organization_id,
            amount=failure.original_amount,
            currency=failure.currency,
            payment_method=payment_method,
            payment_method_id=payment_method_id,
            status=PaymentStatus.PROCESSING,
            failure_reason=None,
            failure_message=None,
            attempt_number=attempt_number,
            attempted_at=start_time,
            gateway_response=None,
            metadata={"retry_attempt": True}
        )

        try:
            # Simulate payment processing (replace with actual gateway calls)
            if payment_method == PaymentMethod.STRIPE and self.stripe_client:
                result = await self._process_stripe_payment(attempt)
            elif payment_method == PaymentMethod.PAYPAL and self.paypal_client:
                result = await self._process_paypal_payment(attempt)
            else:
                # Default simulation
                result = await self._simulate_payment_processing(attempt)

            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            attempt.processing_time_ms = int(processing_time)

            if result["success"]:
                attempt.status = PaymentStatus.SUCCEEDED
                attempt.gateway_response = result.get("response", {})
                return True, attempt
            else:
                attempt.status = PaymentStatus.FAILED
                attempt.failure_reason = FailureReason(result.get("failure_reason", "processing_error"))
                attempt.failure_message = result.get("failure_message", "Payment processing failed")
                attempt.gateway_response = result.get("response", {})
                return False, attempt

        except Exception as e:
            attempt.status = PaymentStatus.FAILED
            attempt.failure_reason = FailureReason.PROCESSING_ERROR
            attempt.failure_message = str(e)
            return False, attempt

    async def _process_stripe_payment(self, attempt: PaymentAttempt) -> Dict[str, Any]:
        """Process payment via Stripe"""
        try:
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(attempt.amount * 100),  # Convert to cents
                currency=attempt.currency.lower(),
                payment_method=attempt.payment_method_id,
                confirm=True,
                return_url="https://yoursite.com/return"
            )

            if intent.status == "succeeded":
                return {
                    "success": True,
                    "response": {
                        "intent_id": intent.id,
                        "status": intent.status,
                        "charges": intent.charges.data
                    }
                }
            else:
                return {
                    "success": False,
                    "failure_reason": "card_declined",
                    "failure_message": f"Payment intent status: {intent.status}",
                    "response": {"intent_id": intent.id, "status": intent.status}
                }

        except stripe.error.CardError as e:
            return {
                "success": False,
                "failure_reason": "card_declined",
                "failure_message": str(e),
                "response": {"error": e.json_body}
            }
        except Exception as e:
            return {
                "success": False,
                "failure_reason": "processing_error",
                "failure_message": str(e),
                "response": {}
            }

    async def _process_paypal_payment(self, attempt: PaymentAttempt) -> Dict[str, Any]:
        """Process payment via PayPal"""
        # PayPal payment processing would go here
        # This is a placeholder implementation
        return await self._simulate_payment_processing(attempt)

    async def _simulate_payment_processing(self, attempt: PaymentAttempt) -> Dict[str, Any]:
        """Simulate payment processing for demo purposes"""
        import random

        # Simulate processing delay
        await asyncio.sleep(random.uniform(0.5, 2.0))

        # Simulate success/failure (70% success rate for retries)
        if random.random() < 0.7:
            return {
                "success": True,
                "response": {
                    "transaction_id": self._generate_id(),
                    "status": "completed"
                }
            }
        else:
            failure_reasons = [
                "insufficient_funds",
                "card_declined",
                "processing_error"
            ]
            reason = random.choice(failure_reasons)
            return {
                "success": False,
                "failure_reason": reason,
                "failure_message": f"Simulated failure: {reason}",
                "response": {"error_code": reason}
            }

    async def _process_retry_queue(self):
        """Background task to process retry queues"""
        while True:
            try:
                current_time = datetime.now()

                # Process each retry strategy queue
                for strategy, queue in self.retry_queues.items():
                    while queue:
                        failure = queue[0]  # Peek at first item

                        if (failure.next_retry_at and
                            current_time >= failure.next_retry_at and
                            failure.current_retry_count < failure.max_retries):

                            # Remove from queue and retry
                            queue.pop(0)
                            await self.retry_payment(failure.failure_id)
                        else:
                            # Not ready for retry yet
                            break

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in retry queue processing: {str(e)}")
                await asyncio.sleep(60)

    # Service Restrictions
    async def _evaluate_service_restrictions(self, failure: PaymentFailure):
        """Evaluate whether to apply service restrictions"""
        # Check if user already has active restrictions
        existing_restriction = self.active_restrictions.get(failure.user_id)

        if existing_restriction:
            # Escalate restriction level if payment still failing
            await self._escalate_service_restriction(existing_restriction, failure)
        else:
            # Apply initial grace period
            await self._apply_grace_period(failure)

    async def _apply_grace_period(self, failure: PaymentFailure):
        """Apply grace period before service restrictions"""
        grace_period_hours = self.config["service_degradation"]["grace_period_hours"]
        grace_period_ends = datetime.now() + timedelta(hours=grace_period_hours)

        restriction = ServiceRestriction(
            restriction_id=self._generate_id(),
            user_id=failure.user_id,
            organization_id=failure.organization_id,
            service_level=ServiceLevel.FULL,
            restriction_reason=f"Payment failure grace period - {failure.failure_reason.value}",
            restricted_features=[],
            started_at=datetime.now(),
            expires_at=None,
            payment_required_amount=failure.original_amount,
            grace_period_ends_at=grace_period_ends,
            is_active=True
        )

        await self._store_service_restriction(restriction)
        self.active_restrictions[failure.user_id] = restriction

        # Send grace period notification
        await self._send_grace_period_notification(failure, grace_period_hours)

    async def _escalate_service_restriction(self, restriction: ServiceRestriction, failure: PaymentFailure):
        """Escalate service restriction level"""
        current_level = restriction.service_level

        if current_level == ServiceLevel.FULL:
            new_level = ServiceLevel.LIMITED
        elif current_level == ServiceLevel.LIMITED:
            new_level = ServiceLevel.BASIC
        elif current_level == ServiceLevel.BASIC:
            new_level = ServiceLevel.SUSPENDED
        else:
            return  # Already at maximum restriction

        # Update restriction
        restriction.service_level = new_level
        restriction.restricted_features = self.config["service_degradation"]["restrictions_by_level"][new_level.value]
        restriction.restriction_reason = f"Escalated due to continued payment failures - {failure.failure_reason.value}"

        await self._update_service_restriction(restriction)

        # Send escalation notification
        await self._send_restriction_escalation_notification(restriction, failure)

    async def _apply_final_service_restrictions(self, failure: PaymentFailure):
        """Apply final service restrictions when all retries are exhausted"""
        restriction = self.active_restrictions.get(failure.user_id)
        if restriction:
            restriction.service_level = ServiceLevel.SUSPENDED
            restriction.restricted_features = ["all_features"]
            restriction.restriction_reason = "Maximum payment retry attempts exceeded"
            await self._update_service_restriction(restriction)

        # Send final notice
        await self._send_final_restriction_notification(failure)

    async def _remove_service_restrictions(self, user_id: str):
        """Remove service restrictions for a user"""
        if user_id in self.active_restrictions:
            restriction = self.active_restrictions[user_id]
            restriction.is_active = False
            restriction.expires_at = datetime.now()

            await self._update_service_restriction(restriction)
            del self.active_restrictions[user_id]

            logger.info(f"Service restrictions removed for user {user_id}")

    async def _store_service_restriction(self, restriction: ServiceRestriction):
        """Store service restriction in database"""
        conn = sqlite3.connect(self.failures_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO service_restrictions (
                restriction_id, user_id, organization_id, service_level,
                restriction_reason, restricted_features, started_at,
                expires_at, payment_required_amount, grace_period_ends_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            restriction.restriction_id,
            restriction.user_id,
            restriction.organization_id,
            restriction.service_level.value,
            restriction.restriction_reason,
            json.dumps(restriction.restricted_features),
            restriction.started_at.isoformat(),
            restriction.expires_at.isoformat() if restriction.expires_at else None,
            float(restriction.payment_required_amount) if restriction.payment_required_amount else None,
            restriction.grace_period_ends_at.isoformat() if restriction.grace_period_ends_at else None,
            restriction.is_active
        ))

        conn.commit()
        conn.close()

    async def _update_service_restriction(self, restriction: ServiceRestriction):
        """Update service restriction in database"""
        conn = sqlite3.connect(self.failures_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE service_restrictions
            SET service_level = ?, restriction_reason = ?, restricted_features = ?,
                expires_at = ?, is_active = ?
            WHERE restriction_id = ?
        """, (
            restriction.service_level.value,
            restriction.restriction_reason,
            json.dumps(restriction.restricted_features),
            restriction.expires_at.isoformat() if restriction.expires_at else None,
            restriction.is_active,
            restriction.restriction_id
        ))

        conn.commit()
        conn.close()

    async def _monitor_service_restrictions(self):
        """Background task to monitor service restrictions"""
        while True:
            try:
                current_time = datetime.now()

                for user_id, restriction in list(self.active_restrictions.items()):
                    # Check if grace period has ended
                    if (restriction.grace_period_ends_at and
                        current_time >= restriction.grace_period_ends_at and
                        restriction.service_level == ServiceLevel.FULL):

                        # Apply initial restrictions
                        await self._escalate_service_restriction(restriction, None)

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Error monitoring service restrictions: {str(e)}")
                await asyncio.sleep(3600)

    async def _monitor_grace_periods(self):
        """Background task to monitor grace periods and send warnings"""
        while True:
            try:
                current_time = datetime.now()
                warning_periods = self.config["service_degradation"]["warning_periods_hours"]

                for user_id, restriction in self.active_restrictions.items():
                    if restriction.grace_period_ends_at:
                        time_remaining = restriction.grace_period_ends_at - current_time
                        hours_remaining = time_remaining.total_seconds() / 3600

                        # Send warnings at specified intervals
                        for warning_hours in warning_periods:
                            if abs(hours_remaining - warning_hours) < 1:  # Within 1 hour of warning time
                                await self._send_grace_period_warning(restriction, warning_hours)

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Error monitoring grace periods: {str(e)}")
                await asyncio.sleep(3600)

    # Notification System
    async def _send_failure_notifications(self, failure: PaymentFailure, alternative_methods: List[AlternativePaymentOption]):
        """Send payment failure notifications"""
        try:
            if self.config["notifications"]["enabled"]:
                # Email notification
                if "email" in self.config["notifications"]["channels"]:
                    await self._send_failure_email(failure, alternative_methods)

                # In-app notification
                if "in_app" in self.config["notifications"]["channels"]:
                    await self._send_in_app_notification(failure)

                # Webhook notification
                if "webhook" in self.config["notifications"]["channels"]:
                    await self._send_webhook_notification(failure)

        except Exception as e:
            logger.error(f"Error sending failure notifications: {str(e)}")

    async def _send_failure_email(self, failure: PaymentFailure, alternative_methods: List[AlternativePaymentOption]):
        """Send payment failure email notification"""
        # Email implementation would use a template and SMTP
        logger.info(f"Sending payment failure email for {failure.failure_id}")

    async def _send_recovery_notification(self, failure: PaymentFailure):
        """Send payment recovery notification"""
        logger.info(f"Sending payment recovery notification for {failure.failure_id}")

    async def _send_grace_period_notification(self, failure: PaymentFailure, grace_hours: int):
        """Send grace period notification"""
        logger.info(f"Sending grace period notification for {failure.user_id} - {grace_hours} hours")

    async def _send_grace_period_warning(self, restriction: ServiceRestriction, warning_hours: int):
        """Send grace period warning"""
        logger.info(f"Sending grace period warning for {restriction.user_id} - {warning_hours} hours remaining")

    async def _send_restriction_escalation_notification(self, restriction: ServiceRestriction, failure: PaymentFailure):
        """Send service restriction escalation notification"""
        logger.info(f"Sending restriction escalation notification for {restriction.user_id}")

    async def _send_final_restriction_notification(self, failure: PaymentFailure):
        """Send final restriction notification"""
        logger.info(f"Sending final restriction notification for {failure.user_id}")

    async def _send_in_app_notification(self, failure: PaymentFailure):
        """Send in-app notification"""
        # Would integrate with your app's notification system
        pass

    async def _send_webhook_notification(self, failure: PaymentFailure):
        """Send webhook notification"""
        # Would send to configured webhook endpoints
        pass

    # Analytics and Reporting
    async def _aggregate_recovery_analytics(self):
        """Background task to aggregate payment recovery analytics"""
        while True:
            try:
                # Run daily
                await asyncio.sleep(86400)

                # Calculate analytics for the past day
                end_time = datetime.now()
                start_time = end_time - timedelta(days=1)

                analytics = await self._calculate_recovery_metrics(start_time, end_time)
                await self._store_recovery_analytics(analytics, start_time, end_time)

            except Exception as e:
                logger.error(f"Error aggregating recovery analytics: {str(e)}")
                await asyncio.sleep(86400)

    async def _calculate_recovery_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Calculate payment recovery metrics for a time period"""
        conn = sqlite3.connect(self.failures_db_path)
        cursor = conn.cursor()

        # Total failures in period
        cursor.execute("""
            SELECT COUNT(*) FROM payment_failures
            WHERE failed_at >= ? AND failed_at < ?
        """, (start_time.isoformat(), end_time.isoformat()))
        total_failures = cursor.fetchone()[0]

        # Successful recoveries
        cursor.execute("""
            SELECT COUNT(*), SUM(original_amount) FROM payment_failures
            WHERE failed_at >= ? AND failed_at < ? AND is_resolved = TRUE
        """, (start_time.isoformat(), end_time.isoformat()))
        recovery_data = cursor.fetchone()
        successful_recoveries = recovery_data[0] or 0
        total_recovered_amount = recovery_data[1] or 0

        # Recovery rate
        recovery_rate = (successful_recoveries / total_failures) if total_failures > 0 else 0

        # Average recovery time
        cursor.execute("""
            SELECT AVG(
                (julianday(resolved_at) - julianday(failed_at)) * 24
            ) FROM payment_failures
            WHERE failed_at >= ? AND failed_at < ? AND is_resolved = TRUE
        """, (start_time.isoformat(), end_time.isoformat()))
        avg_recovery_time = cursor.fetchone()[0] or 0

        # Most common failure reason
        cursor.execute("""
            SELECT failure_reason, COUNT(*) as count FROM payment_failures
            WHERE failed_at >= ? AND failed_at < ?
            GROUP BY failure_reason
            ORDER BY count DESC
            LIMIT 1
        """, (start_time.isoformat(), end_time.isoformat()))
        most_common_failure = cursor.fetchone()
        most_common_failure_reason = most_common_failure[0] if most_common_failure else "none"

        conn.close()

        return {
            "total_failures": total_failures,
            "successful_recoveries": successful_recoveries,
            "recovery_rate": recovery_rate,
            "total_recovered_amount": total_recovered_amount,
            "avg_recovery_time_hours": avg_recovery_time,
            "most_common_failure_reason": most_common_failure_reason,
            "most_successful_recovery_method": "retry_success"  # Would calculate from data
        }

    async def _store_recovery_analytics(self, analytics: Dict[str, Any], start_time: datetime, end_time: datetime):
        """Store recovery analytics in database"""
        conn = sqlite3.connect(self.failures_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO payment_recovery_analytics (
                analytics_id, period_start, period_end, total_failures,
                successful_recoveries, recovery_rate, total_recovered_amount,
                avg_recovery_time_hours, most_common_failure_reason,
                most_successful_recovery_method
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self._generate_id(),
            start_time.isoformat(),
            end_time.isoformat(),
            analytics["total_failures"],
            analytics["successful_recoveries"],
            analytics["recovery_rate"],
            analytics["total_recovered_amount"],
            analytics["avg_recovery_time_hours"],
            analytics["most_common_failure_reason"],
            analytics["most_successful_recovery_method"]
        ))

        conn.commit()
        conn.close()

    # Utility Methods
    async def _update_failure_status(self, failure: PaymentFailure):
        """Update failure status in database"""
        conn = sqlite3.connect(self.failures_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE payment_failures
            SET current_retry_count = ?, next_retry_at = ?, is_resolved = ?,
                resolved_at = ?, resolution_method = ?
            WHERE failure_id = ?
        """, (
            failure.current_retry_count,
            failure.next_retry_at.isoformat() if failure.next_retry_at else None,
            failure.is_resolved,
            failure.resolved_at.isoformat() if failure.resolved_at else None,
            failure.resolution_method,
            failure.failure_id
        ))

        conn.commit()
        conn.close()

    def _generate_id(self) -> str:
        """Generate unique identifier"""
        import uuid
        return str(uuid.uuid4())

    async def get_payment_failure_analytics(self, user_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """Get payment failure analytics"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            conn = sqlite3.connect(self.failures_db_path)
            cursor = conn.cursor()

            where_clause = "WHERE failed_at >= ?"
            params = [cutoff_date.isoformat()]

            if user_id:
                where_clause += " AND user_id = ?"
                params.append(user_id)

            # Total failures
            cursor.execute(f"SELECT COUNT(*) FROM payment_failures {where_clause}", params)
            total_failures = cursor.fetchone()[0]

            # Recovery rate
            cursor.execute(f"SELECT COUNT(*) FROM payment_failures {where_clause} AND is_resolved = TRUE", params)
            resolved_failures = cursor.fetchone()[0]

            # Failures by reason
            cursor.execute(f"""
                SELECT failure_reason, COUNT(*) FROM payment_failures
                {where_clause} GROUP BY failure_reason
            """, params)
            failures_by_reason = dict(cursor.fetchall())

            conn.close()

            recovery_rate = (resolved_failures / total_failures) if total_failures > 0 else 0

            return {
                "period_days": days,
                "total_failures": total_failures,
                "resolved_failures": resolved_failures,
                "recovery_rate": recovery_rate,
                "failures_by_reason": failures_by_reason,
                "active_failures": len([f for f in self.active_failures.values()
                                      if not user_id or f.user_id == user_id])
            }

        except Exception as e:
            logger.error(f"Error getting payment failure analytics: {str(e)}")
            return {}

# Initialize the payment failure handler
payment_failure_handler = PaymentFailureHandler()