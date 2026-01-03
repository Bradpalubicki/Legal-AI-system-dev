"""
Comprehensive API Rate Limit and Quota Management System
Handles OpenAI, Claude, and other AI provider rate limits with intelligent fallbacks.
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from collections import defaultdict, deque
# aiofiles removed - using standard file operations
import aiohttp
from functools import wraps
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIProvider(Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"

class ModelType(Enum):
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"

class PriorityLevel(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class RequestStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    QUEUED = "queued"

@dataclass
class RateLimit:
    requests_per_minute: int
    requests_per_day: int
    tokens_per_minute: int
    tokens_per_day: int
    concurrent_requests: int

@dataclass
class Usage:
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    timestamp: datetime

@dataclass
class APIRequest:
    request_id: str
    provider: APIProvider
    model: ModelType
    priority: PriorityLevel
    prompt: str
    max_tokens: int
    temperature: float
    user_id: str
    organization_id: str
    metadata: Dict[str, Any]
    created_at: datetime
    status: RequestStatus
    estimated_tokens: int
    actual_usage: Optional[Usage] = None
    response: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    fallback_used: bool = False

@dataclass
class ProviderConfig:
    provider: APIProvider
    api_key: str
    base_url: str
    rate_limits: RateLimit
    cost_per_token: Dict[str, float]  # input/output costs
    timeout_seconds: int
    max_retries: int
    backoff_multiplier: float
    enabled: bool

class RateLimitManager:
    def __init__(self, config_path: str = "api_rate_limits_config.json"):
        self.config_path = config_path
        self.usage_db_path = "api_usage.db"
        self.cache_ttl = 3600  # 1 hour

        # Rate tracking
        self.request_counters = defaultdict(lambda: defaultdict(int))
        self.token_counters = defaultdict(lambda: defaultdict(int))
        self.last_reset = defaultdict(lambda: defaultdict(datetime))

        # Request queues by priority
        self.request_queues = defaultdict(lambda: {
            PriorityLevel.CRITICAL: deque(),
            PriorityLevel.HIGH: deque(),
            PriorityLevel.NORMAL: deque(),
            PriorityLevel.LOW: deque()
        })

        # Active requests tracking
        self.active_requests = defaultdict(int)

        # Provider configurations
        self.providers: Dict[APIProvider, ProviderConfig] = {}

        # Fallback chains
        self.fallback_chains = {
            ModelType.GPT_4: [ModelType.GPT_4_TURBO, ModelType.GPT_3_5_TURBO],
            ModelType.GPT_4_TURBO: [ModelType.GPT_3_5_TURBO],
            ModelType.CLAUDE_3_OPUS: [ModelType.CLAUDE_3_SONNET, ModelType.CLAUDE_3_HAIKU],
            ModelType.CLAUDE_3_SONNET: [ModelType.CLAUDE_3_HAIKU]
        }

        # Caching
        self.redis_client = None
        self.local_cache = {}

        # Background tasks
        self.background_tasks = []

        # Note: Call initialize_system() manually after creating instance

    async def _initialize_system(self):
        """Initialize the rate limit management system"""
        try:
            await self._setup_database()
            await self._load_configuration()
            await self._setup_redis()
            await self._start_background_tasks()
            logger.info("Rate limit manager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing rate limit manager: {str(e)}")
            raise

    async def _setup_database(self):
        """Setup SQLite database for usage tracking"""
        conn = sqlite3.connect(self.usage_db_path)
        cursor = conn.cursor()

        # API usage tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                usage_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                user_id TEXT NOT NULL,
                organization_id TEXT,
                total_tokens INTEGER NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Rate limit violations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_limit_violations (
                violation_id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                limit_type TEXT NOT NULL,
                current_usage INTEGER NOT NULL,
                limit_value INTEGER NOT NULL,
                user_id TEXT,
                organization_id TEXT,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Request queue
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_queue (
                request_id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                priority INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                organization_id TEXT,
                prompt_hash TEXT NOT NULL,
                estimated_tokens INTEGER NOT NULL,
                status TEXT NOT NULL,
                queued_at TEXT NOT NULL,
                processed_at TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Cost tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_tracking (
                cost_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                organization_id TEXT,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                total_requests INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                total_cost_usd REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON api_usage(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_user ON api_usage(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_priority ON request_queue(priority, queued_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cost_user_period ON cost_tracking(user_id, period_start, period_end)")

        conn.commit()
        conn.close()

    async def _load_configuration(self):
        """Load rate limit configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config_content = f.read()
                config = json.loads(config_content)
                await self._parse_provider_configs(config)
        except FileNotFoundError:
            # Create default configuration
            config = self._create_default_config()
            await self._save_configuration(config)
            await self._parse_provider_configs(config)

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default rate limit configuration"""
        return {
            "providers": {
                "openai": {
                    "api_key": "your-openai-api-key",
                    "base_url": "https://api.openai.com/v1",
                    "rate_limits": {
                        "requests_per_minute": 3500,
                        "requests_per_day": 200000,
                        "tokens_per_minute": 90000,
                        "tokens_per_day": 10000000,
                        "concurrent_requests": 100
                    },
                    "cost_per_token": {
                        "gpt-4": {"input": 0.00003, "output": 0.00006},
                        "gpt-4-turbo": {"input": 0.00001, "output": 0.00003},
                        "gpt-3.5-turbo": {"input": 0.0000015, "output": 0.000002}
                    },
                    "timeout_seconds": 60,
                    "max_retries": 3,
                    "backoff_multiplier": 2.0,
                    "enabled": True
                },
                "claude": {
                    "api_key": "your-claude-api-key",
                    "base_url": "https://api.anthropic.com/v1",
                    "rate_limits": {
                        "requests_per_minute": 1000,
                        "requests_per_day": 50000,
                        "tokens_per_minute": 80000,
                        "tokens_per_day": 5000000,
                        "concurrent_requests": 50
                    },
                    "cost_per_token": {
                        "claude-3-opus": {"input": 0.000015, "output": 0.000075},
                        "claude-3-sonnet": {"input": 0.000003, "output": 0.000015},
                        "claude-3-haiku": {"input": 0.00000025, "output": 0.00000125}
                    },
                    "timeout_seconds": 60,
                    "max_retries": 3,
                    "backoff_multiplier": 2.0,
                    "enabled": True
                }
            },
            "fallback_settings": {
                "enable_fallbacks": True,
                "fallback_threshold": 0.8,  # Use fallback when at 80% of rate limit
                "cost_optimization": True,
                "quality_threshold": 0.85
            },
            "caching": {
                "enabled": True,
                "ttl_seconds": 3600,
                "max_cache_size_mb": 100,
                "cache_similar_requests": True,
                "similarity_threshold": 0.9
            },
            "queue_settings": {
                "max_queue_size": 10000,
                "process_interval_seconds": 1,
                "priority_boost_after_minutes": 30,
                "auto_retry_failed": True
            }
        }

    async def _parse_provider_configs(self, config: Dict[str, Any]):
        """Parse provider configurations"""
        for provider_name, provider_config in config["providers"].items():
            provider = APIProvider(provider_name)

            rate_limits = RateLimit(
                requests_per_minute=provider_config["rate_limits"]["requests_per_minute"],
                requests_per_day=provider_config["rate_limits"]["requests_per_day"],
                tokens_per_minute=provider_config["rate_limits"]["tokens_per_minute"],
                tokens_per_day=provider_config["rate_limits"]["tokens_per_day"],
                concurrent_requests=provider_config["rate_limits"]["concurrent_requests"]
            )

            self.providers[provider] = ProviderConfig(
                provider=provider,
                api_key=provider_config["api_key"],
                base_url=provider_config["base_url"],
                rate_limits=rate_limits,
                cost_per_token=provider_config["cost_per_token"],
                timeout_seconds=provider_config["timeout_seconds"],
                max_retries=provider_config["max_retries"],
                backoff_multiplier=provider_config["backoff_multiplier"],
                enabled=provider_config["enabled"]
            )

        self.fallback_settings = config.get("fallback_settings", {})
        self.caching_settings = config.get("caching", {})
        self.queue_settings = config.get("queue_settings", {})

    async def _save_configuration(self, config: Dict[str, Any]):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            f.write(json.dumps(config, indent=2))

    async def _setup_redis(self):
        """Setup Redis for caching (simplified)"""
        try:
            # Simplified - no redis dependency
            self.redis_client = None
            logger.info("Using local cache (Redis not available)")
        except Exception as e:
            logger.warning(f"Redis not available, using local cache: {str(e)}")
            self.redis_client = None

    async def _start_background_tasks(self):
        """Start background processing tasks"""
        # Queue processor
        queue_task = asyncio.create_task(self._process_request_queue())
        self.background_tasks.append(queue_task)

        # Usage aggregator
        usage_task = asyncio.create_task(self._aggregate_usage_stats())
        self.background_tasks.append(usage_task)

        # Cache cleaner
        cache_task = asyncio.create_task(self._cleanup_cache())
        self.background_tasks.append(cache_task)

        # Rate limit reset tracker
        reset_task = asyncio.create_task(self._track_rate_limit_resets())
        self.background_tasks.append(reset_task)

    # Main API Request Handling
    async def make_request(self,
                          provider: APIProvider,
                          model: ModelType,
                          prompt: str,
                          user_id: str,
                          organization_id: str = None,
                          priority: PriorityLevel = PriorityLevel.NORMAL,
                          max_tokens: int = 1000,
                          temperature: float = 0.7,
                          use_cache: bool = True,
                          metadata: Dict[str, Any] = None) -> APIRequest:
        """Make an API request with rate limiting and fallback handling"""

        request_id = self._generate_id()
        metadata = metadata or {}

        # Estimate token usage
        estimated_tokens = self._estimate_tokens(prompt, max_tokens, model)

        # Create request object
        api_request = APIRequest(
            request_id=request_id,
            provider=provider,
            model=model,
            priority=priority,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            user_id=user_id,
            organization_id=organization_id,
            metadata=metadata,
            created_at=datetime.now(),
            status=RequestStatus.PENDING,
            estimated_tokens=estimated_tokens
        )

        try:
            # Check cache first
            if use_cache and self.caching_settings.get("enabled", True):
                cached_response = await self._check_cache(api_request)
                if cached_response:
                    api_request.response = cached_response
                    api_request.status = RequestStatus.COMPLETED
                    api_request.actual_usage = Usage(
                        total_tokens=0, prompt_tokens=0, completion_tokens=0,
                        cost_usd=0.0, timestamp=datetime.now()
                    )
                    return api_request

            # Check rate limits
            if await self._check_rate_limits(api_request):
                # Process immediately
                await self._process_request(api_request)
            else:
                # Queue for later processing
                api_request.status = RequestStatus.QUEUED
                await self._queue_request(api_request)

            return api_request

        except Exception as e:
            logger.error(f"Error processing API request {request_id}: {str(e)}")
            api_request.status = RequestStatus.FAILED
            api_request.error = str(e)
            return api_request

    async def _check_rate_limits(self, request: APIRequest) -> bool:
        """Check if request can be processed immediately"""
        provider_config = self.providers.get(request.provider)
        if not provider_config or not provider_config.enabled:
            return False

        current_time = datetime.now()
        minute_key = current_time.strftime("%Y-%m-%d-%H-%M")
        day_key = current_time.strftime("%Y-%m-%d")

        rate_limits = provider_config.rate_limits

        # Check requests per minute
        if self.request_counters[request.provider][minute_key] >= rate_limits.requests_per_minute:
            await self._log_rate_limit_violation(request, "requests_per_minute")
            return False

        # Check requests per day
        if self.request_counters[request.provider][day_key] >= rate_limits.requests_per_day:
            await self._log_rate_limit_violation(request, "requests_per_day")
            return False

        # Check tokens per minute
        if self.token_counters[request.provider][minute_key] + request.estimated_tokens > rate_limits.tokens_per_minute:
            await self._log_rate_limit_violation(request, "tokens_per_minute")
            return False

        # Check tokens per day
        if self.token_counters[request.provider][day_key] + request.estimated_tokens > rate_limits.tokens_per_day:
            await self._log_rate_limit_violation(request, "tokens_per_day")
            return False

        # Check concurrent requests
        if self.active_requests[request.provider] >= rate_limits.concurrent_requests:
            await self._log_rate_limit_violation(request, "concurrent_requests")
            return False

        return True

    async def _process_request(self, request: APIRequest):
        """Process an API request"""
        try:
            request.status = RequestStatus.PROCESSING
            self.active_requests[request.provider] += 1

            # Update counters
            await self._update_usage_counters(request)

            # Make the actual API call
            response = await self._make_api_call(request)

            if response:
                request.response = response["content"]
                request.actual_usage = Usage(
                    total_tokens=response["usage"]["total_tokens"],
                    prompt_tokens=response["usage"]["prompt_tokens"],
                    completion_tokens=response["usage"]["completion_tokens"],
                    cost_usd=self._calculate_cost(request, response["usage"]),
                    timestamp=datetime.now()
                )
                request.status = RequestStatus.COMPLETED

                # Cache the response
                if self.caching_settings.get("enabled", True):
                    await self._cache_response(request)

                # Log usage
                await self._log_usage(request)

            else:
                raise Exception("No response received from API")

        except Exception as e:
            logger.error(f"Error processing request {request.request_id}: {str(e)}")

            # Try fallback
            if not request.fallback_used and self.fallback_settings.get("enable_fallbacks", True):
                fallback_model = self._get_fallback_model(request.model)
                if fallback_model:
                    request.model = fallback_model
                    request.fallback_used = True
                    request.retry_count += 1
                    await self._process_request(request)
                    return

            request.status = RequestStatus.FAILED
            request.error = str(e)

        finally:
            self.active_requests[request.provider] -= 1

    async def _make_api_call(self, request: APIRequest) -> Optional[Dict[str, Any]]:
        """Make the actual API call to the provider"""
        provider_config = self.providers[request.provider]

        if request.provider == APIProvider.OPENAI:
            return await self._call_openai_api(request, provider_config)
        elif request.provider == APIProvider.CLAUDE:
            return await self._call_claude_api(request, provider_config)
        else:
            raise Exception(f"Unsupported provider: {request.provider}")

    async def _call_openai_api(self, request: APIRequest, config: ProviderConfig) -> Dict[str, Any]:
        """Call OpenAI API"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": request.model.value,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout_seconds)) as session:
            async with session.post(f"{config.base_url}/chat/completions",
                                   headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "content": data["choices"][0]["message"]["content"],
                        "usage": data["usage"]
                    }
                elif response.status == 429:
                    # Rate limited
                    raise Exception("Rate limit exceeded")
                else:
                    error_data = await response.json()
                    raise Exception(f"API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

    async def _call_claude_api(self, request: APIRequest, config: ProviderConfig) -> Dict[str, Any]:
        """Call Claude API"""
        headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": request.model.value,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": [{"role": "user", "content": request.prompt}]
        }

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout_seconds)) as session:
            async with session.post(f"{config.base_url}/messages",
                                   headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["content"][0]["text"] if data["content"] else ""

                    # Calculate token usage (Claude returns usage in different format)
                    usage = {
                        "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                        "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
                        "total_tokens": data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
                    }

                    return {
                        "content": content,
                        "usage": usage
                    }
                elif response.status == 429:
                    raise Exception("Rate limit exceeded")
                else:
                    error_data = await response.json()
                    raise Exception(f"API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

    # Queue Management
    async def _queue_request(self, request: APIRequest):
        """Queue a request for later processing"""
        self.request_queues[request.provider][request.priority].append(request)

        # Store in database
        await self._store_queued_request(request)

        logger.info(f"Request {request.request_id} queued with priority {request.priority.name}")

    async def _store_queued_request(self, request: APIRequest):
        """Store queued request in database"""
        conn = sqlite3.connect(self.usage_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO request_queue (
                request_id, provider, model, priority, user_id, organization_id,
                prompt_hash, estimated_tokens, status, queued_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.request_id,
            request.provider.value,
            request.model.value,
            request.priority.value,
            request.user_id,
            request.organization_id,
            hashlib.md5(request.prompt.encode()).hexdigest(),
            request.estimated_tokens,
            request.status.value,
            request.created_at.isoformat()
        ))

        conn.commit()
        conn.close()

    async def _process_request_queue(self):
        """Background task to process queued requests"""
        while True:
            try:
                for provider in APIProvider:
                    if provider not in self.providers or not self.providers[provider].enabled:
                        continue

                    # Process by priority order
                    for priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH,
                                   PriorityLevel.NORMAL, PriorityLevel.LOW]:
                        queue = self.request_queues[provider][priority]

                        while queue:
                            request = queue.popleft()

                            if await self._check_rate_limits(request):
                                await self._process_request(request)
                                break  # Process one at a time to avoid overloading
                            else:
                                # Put back at front of queue
                                queue.appendleft(request)
                                break

                await asyncio.sleep(self.queue_settings.get("process_interval_seconds", 1))

            except Exception as e:
                logger.error(f"Error in queue processing: {str(e)}")
                await asyncio.sleep(5)

    # Caching System
    async def _check_cache(self, request: APIRequest) -> Optional[str]:
        """Check if request is cached"""
        cache_key = self._generate_cache_key(request)

        try:
            if self.redis_client:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            else:
                return self.local_cache.get(cache_key)
        except Exception as e:
            logger.error(f"Error checking cache: {str(e)}")

        return None

    async def _cache_response(self, request: APIRequest):
        """Cache the API response"""
        if not request.response:
            return

        cache_key = self._generate_cache_key(request)
        ttl = self.caching_settings.get("ttl_seconds", 3600)

        try:
            if self.redis_client:
                await self.redis_client.setex(cache_key, ttl, json.dumps(request.response))
            else:
                self.local_cache[cache_key] = request.response
                # Simple TTL for local cache
                asyncio.create_task(self._expire_local_cache(cache_key, ttl))
        except Exception as e:
            logger.error(f"Error caching response: {str(e)}")

    def _generate_cache_key(self, request: APIRequest) -> str:
        """Generate cache key for request"""
        key_data = f"{request.provider.value}:{request.model.value}:{request.prompt}:{request.max_tokens}:{request.temperature}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def _expire_local_cache(self, key: str, ttl: int):
        """Expire local cache entry after TTL"""
        await asyncio.sleep(ttl)
        self.local_cache.pop(key, None)

    async def _cleanup_cache(self):
        """Background task to cleanup cache"""
        while True:
            try:
                # Clean local cache if it gets too large
                max_size = self.caching_settings.get("max_cache_size_mb", 100) * 1024 * 1024
                if len(str(self.local_cache)) > max_size:
                    # Remove oldest entries (simplified approach)
                    keys_to_remove = list(self.local_cache.keys())[:len(self.local_cache)//2]
                    for key in keys_to_remove:
                        self.local_cache.pop(key, None)

                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                logger.error(f"Error in cache cleanup: {str(e)}")
                await asyncio.sleep(3600)

    # Usage Tracking and Analytics
    async def _update_usage_counters(self, request: APIRequest):
        """Update usage counters"""
        current_time = datetime.now()
        minute_key = current_time.strftime("%Y-%m-%d-%H-%M")
        day_key = current_time.strftime("%Y-%m-%d")

        # Increment request counters
        self.request_counters[request.provider][minute_key] += 1
        self.request_counters[request.provider][day_key] += 1

        # Increment token counters
        self.token_counters[request.provider][minute_key] += request.estimated_tokens
        self.token_counters[request.provider][day_key] += request.estimated_tokens

    async def _log_usage(self, request: APIRequest):
        """Log API usage to database"""
        if not request.actual_usage:
            return

        conn = sqlite3.connect(self.usage_db_path)
        cursor = conn.cursor()

        usage_id = self._generate_id()
        cursor.execute("""
            INSERT INTO api_usage (
                usage_id, request_id, provider, model, user_id, organization_id,
                total_tokens, prompt_tokens, completion_tokens, cost_usd, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            usage_id,
            request.request_id,
            request.provider.value,
            request.model.value,
            request.user_id,
            request.organization_id,
            request.actual_usage.total_tokens,
            request.actual_usage.prompt_tokens,
            request.actual_usage.completion_tokens,
            request.actual_usage.cost_usd,
            request.actual_usage.timestamp.isoformat()
        ))

        conn.commit()
        conn.close()

    async def _log_rate_limit_violation(self, request: APIRequest, limit_type: str):
        """Log rate limit violation"""
        conn = sqlite3.connect(self.usage_db_path)
        cursor = conn.cursor()

        violation_id = self._generate_id()
        cursor.execute("""
            INSERT INTO rate_limit_violations (
                violation_id, provider, limit_type, current_usage, limit_value,
                user_id, organization_id, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            violation_id,
            request.provider.value,
            limit_type,
            0,  # Would need to calculate actual current usage
            0,  # Would need to get actual limit value
            request.user_id,
            request.organization_id,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    async def _aggregate_usage_stats(self):
        """Background task to aggregate usage statistics"""
        while True:
            try:
                # Run every hour
                await asyncio.sleep(3600)

                # Aggregate hourly statistics
                await self._create_usage_aggregations()

            except Exception as e:
                logger.error(f"Error in usage aggregation: {str(e)}")
                await asyncio.sleep(3600)

    async def _create_usage_aggregations(self):
        """Create usage aggregations for reporting"""
        conn = sqlite3.connect(self.usage_db_path)
        cursor = conn.cursor()

        # Get current hour boundaries
        current_time = datetime.now()
        hour_start = current_time.replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)

        # Aggregate by user and provider
        cursor.execute("""
            SELECT user_id, organization_id, provider, model,
                   COUNT(*) as total_requests,
                   SUM(total_tokens) as total_tokens,
                   SUM(cost_usd) as total_cost
            FROM api_usage
            WHERE timestamp >= ? AND timestamp < ?
            GROUP BY user_id, organization_id, provider, model
        """, (hour_start.isoformat(), hour_end.isoformat()))

        aggregations = cursor.fetchall()

        for agg in aggregations:
            cursor.execute("""
                INSERT OR REPLACE INTO cost_tracking (
                    cost_id, user_id, organization_id, provider, model,
                    period_start, period_end, total_requests, total_tokens, total_cost_usd
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self._generate_id(),
                agg[0], agg[1], agg[2], agg[3],
                hour_start.isoformat(), hour_end.isoformat(),
                agg[4], agg[5], agg[6]
            ))

        conn.commit()
        conn.close()

    async def _track_rate_limit_resets(self):
        """Background task to track rate limit resets"""
        while True:
            try:
                current_time = datetime.now()

                # Reset minute counters
                minute_key = (current_time - timedelta(minutes=1)).strftime("%Y-%m-%d-%H-%M")
                for provider in self.request_counters:
                    self.request_counters[provider].pop(minute_key, None)
                    self.token_counters[provider].pop(minute_key, None)

                # Reset daily counters
                if current_time.hour == 0 and current_time.minute == 0:
                    day_key = (current_time - timedelta(days=1)).strftime("%Y-%m-%d")
                    for provider in self.request_counters:
                        self.request_counters[provider].pop(day_key, None)
                        self.token_counters[provider].pop(day_key, None)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in rate limit reset tracking: {str(e)}")
                await asyncio.sleep(60)

    # Fallback and Cost Optimization
    def _get_fallback_model(self, model: ModelType) -> Optional[ModelType]:
        """Get fallback model for the given model"""
        fallback_chain = self.fallback_chains.get(model, [])
        for fallback in fallback_chain:
            if self._is_model_available(fallback):
                return fallback
        return None

    def _is_model_available(self, model: ModelType) -> bool:
        """Check if model is available and within rate limits"""
        # Determine provider for model
        provider = self._get_provider_for_model(model)
        if not provider or provider not in self.providers:
            return False

        # Check if provider is enabled
        return self.providers[provider].enabled

    def _get_provider_for_model(self, model: ModelType) -> Optional[APIProvider]:
        """Get provider for a given model"""
        if model.value.startswith("gpt"):
            return APIProvider.OPENAI
        elif model.value.startswith("claude"):
            return APIProvider.CLAUDE
        return None

    def _calculate_cost(self, request: APIRequest, usage: Dict[str, int]) -> float:
        """Calculate cost for API usage"""
        provider_config = self.providers.get(request.provider)
        if not provider_config:
            return 0.0

        model_costs = provider_config.cost_per_token.get(request.model.value, {})
        input_cost = model_costs.get("input", 0.0)
        output_cost = model_costs.get("output", 0.0)

        total_cost = (usage.get("prompt_tokens", 0) * input_cost +
                     usage.get("completion_tokens", 0) * output_cost)

        return total_cost

    def _estimate_tokens(self, prompt: str, max_tokens: int, model: ModelType) -> int:
        """Estimate token usage for a request (simplified)"""
        try:
            # Simplified estimation without tiktoken (rough approximation: 4 chars per token)
            prompt_tokens = len(prompt) // 4
            return prompt_tokens + max_tokens
        except Exception:
            # Fallback estimation
            return len(prompt) // 4 + max_tokens

    # Utility Methods
    def _generate_id(self) -> str:
        """Generate unique identifier"""
        import uuid
        return str(uuid.uuid4())

    async def get_usage_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get usage analytics for a user"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            conn = sqlite3.connect(self.usage_db_path)
            cursor = conn.cursor()

            # Total usage
            cursor.execute("""
                SELECT COUNT(*) as total_requests,
                       SUM(total_tokens) as total_tokens,
                       SUM(cost_usd) as total_cost
                FROM api_usage
                WHERE user_id = ? AND timestamp >= ?
            """, (user_id, cutoff_date.isoformat()))

            total_stats = cursor.fetchone()

            # Usage by provider
            cursor.execute("""
                SELECT provider, COUNT(*) as requests, SUM(cost_usd) as cost
                FROM api_usage
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY provider
            """, (user_id, cutoff_date.isoformat()))

            provider_stats = dict(cursor.fetchall())

            # Usage by model
            cursor.execute("""
                SELECT model, COUNT(*) as requests, SUM(cost_usd) as cost
                FROM api_usage
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY model
            """, (user_id, cutoff_date.isoformat()))

            model_stats = dict(cursor.fetchall())

            conn.close()

            return {
                "period_days": days,
                "total_requests": total_stats[0] or 0,
                "total_tokens": total_stats[1] or 0,
                "total_cost": total_stats[2] or 0.0,
                "usage_by_provider": provider_stats,
                "usage_by_model": model_stats,
                "average_cost_per_request": (total_stats[2] / total_stats[0]) if total_stats[0] else 0.0
            }

        except Exception as e:
            logger.error(f"Error getting usage analytics: {str(e)}")
            return {}

# Initialize the rate limit manager
rate_limit_manager = RateLimitManager()