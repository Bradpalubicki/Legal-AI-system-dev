#!/usr/bin/env python3
"""
Attorney API Security Framework
Enterprise-grade API security for legal professional applications
"""

import os
import json
import sqlite3
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from functools import wraps
import ipaddress
import re
from pathlib import Path
import hmac
import base64
import time

class APISecurityLevel(Enum):
    """API endpoint security levels"""
    PUBLIC = "public"              # No authentication required
    AUTHENTICATED = "authenticated" # Basic authentication required
    ATTORNEY_ONLY = "attorney_only" # Licensed attorney access only
    PRIVILEGED = "privileged"       # Access to privileged information
    ADMINISTRATIVE = "administrative" # Admin/partner access only
    CRITICAL = "critical"           # Highest security for sensitive operations

class RateLimitTier(Enum):
    """Rate limiting tiers based on attorney role"""
    BASIC = "basic"              # 100 requests/hour
    PROFESSIONAL = "professional" # 500 requests/hour
    PREMIUM = "premium"          # 1000 requests/hour
    ENTERPRISE = "enterprise"    # 5000 requests/hour
    UNLIMITED = "unlimited"      # No limits (for system accounts)

class APIEventType(Enum):
    """API security event types"""
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILURE = "auth_failure"
    AUTHORIZATION_DENIED = "authorization_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    API_KEY_COMPROMISED = "api_key_compromised"
    PRIVILEGED_ACCESS = "privileged_access"
    DATA_EXPORT = "data_export"
    BULK_OPERATION = "bulk_operation"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"

@dataclass
class APIKey:
    """Attorney API key with comprehensive tracking"""
    key_id: str
    api_key_hash: str  # Hashed version of the actual key
    attorney_id: str
    attorney_email: str
    attorney_role: str
    key_name: str
    description: str
    
    # Permissions
    security_level: APISecurityLevel
    allowed_endpoints: List[str]
    denied_endpoints: List[str]
    allowed_ip_ranges: List[str]
    
    # Rate limiting
    rate_limit_tier: RateLimitTier
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int
    
    # Lifecycle
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    is_active: bool
    
    # Usage tracking
    total_requests: int
    successful_requests: int
    failed_requests: int
    privileged_requests: int
    
    # Security
    requires_ip_whitelist: bool
    requires_signature: bool
    signature_secret: Optional[str]
    
    # Compliance
    purpose: str  # Business purpose for the key
    data_retention_days: int
    compliance_notes: List[str]

@dataclass
class APISecurityEvent:
    """API security event for monitoring and compliance"""
    event_id: str
    timestamp: datetime
    event_type: APIEventType
    severity: str
    
    # Request details
    api_key_id: Optional[str]
    attorney_id: Optional[str]
    endpoint: str
    http_method: str
    ip_address: str
    user_agent: str
    
    # Security details
    security_level: APISecurityLevel
    authentication_result: bool
    authorization_result: bool
    rate_limit_status: Dict[str, Any]
    
    # Event details
    description: str
    details: Dict[str, Any]
    response_code: int
    response_time_ms: float
    
    # Risk assessment
    risk_score: float
    requires_review: bool
    
    # Compliance
    contains_privileged_data: bool
    client_data_accessed: List[str]

class AttorneyAPISecurityManager:
    """Enterprise API security manager for attorney applications"""
    
    def __init__(self, db_path: str = "attorney_api_security.db"):
        self.db_path = db_path
        self.logger = self._setup_logger()
        self._init_database()
        
        # Rate limiting configuration
        self.rate_limits = {
            RateLimitTier.BASIC: {"hour": 100, "day": 1000, "burst": 10},
            RateLimitTier.PROFESSIONAL: {"hour": 500, "day": 5000, "burst": 25},
            RateLimitTier.PREMIUM: {"hour": 1000, "day": 10000, "burst": 50},
            RateLimitTier.ENTERPRISE: {"hour": 5000, "day": 50000, "burst": 100},
            RateLimitTier.UNLIMITED: {"hour": float('inf'), "day": float('inf'), "burst": float('inf')}
        }
        
        # Security level requirements by attorney role
        self.role_security_mapping = {
            "receptionist": [APISecurityLevel.PUBLIC, APISecurityLevel.AUTHENTICATED],
            "legal_assistant": [APISecurityLevel.PUBLIC, APISecurityLevel.AUTHENTICATED],
            "paralegal": [APISecurityLevel.PUBLIC, APISecurityLevel.AUTHENTICATED],
            "associate": [APISecurityLevel.PUBLIC, APISecurityLevel.AUTHENTICATED, APISecurityLevel.ATTORNEY_ONLY],
            "senior_associate": [APISecurityLevel.PUBLIC, APISecurityLevel.AUTHENTICATED, APISecurityLevel.ATTORNEY_ONLY, APISecurityLevel.PRIVILEGED],
            "partner": [APISecurityLevel.PUBLIC, APISecurityLevel.AUTHENTICATED, APISecurityLevel.ATTORNEY_ONLY, APISecurityLevel.PRIVILEGED, APISecurityLevel.ADMINISTRATIVE],
            "managing_partner": list(APISecurityLevel),  # Full access
            "it_administrator": list(APISecurityLevel),  # Full access
            "compliance_officer": list(APISecurityLevel)  # Full access
        }
        
        # Suspicious pattern detection
        self.suspicious_patterns = {
            "rapid_sequential_requests": {"threshold": 50, "window_seconds": 60},
            "privilege_escalation_attempts": {"threshold": 5, "window_seconds": 300},
            "unusual_endpoint_access": {"threshold": 10, "window_seconds": 3600},
            "off_hours_access": {"business_hours": (9, 18)},
            "geographic_anomaly": {"max_distance_km": 500}
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup API security logger"""
        logger = logging.getLogger('attorney_api_security')
        logger.setLevel(logging.INFO)
        
        Path('logs').mkdir(exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            'logs/attorney_api_security.log',
            maxBytes=100*1024*1024,
            backupCount=200,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - API_SECURITY - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize API security database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attorney_api_keys (
                key_id TEXT PRIMARY KEY,
                api_key_hash TEXT UNIQUE NOT NULL,
                attorney_id TEXT NOT NULL,
                attorney_email TEXT NOT NULL,
                attorney_role TEXT NOT NULL,
                key_name TEXT NOT NULL,
                description TEXT NOT NULL,
                security_level TEXT NOT NULL,
                allowed_endpoints TEXT NOT NULL,
                denied_endpoints TEXT NOT NULL,
                allowed_ip_ranges TEXT NOT NULL,
                rate_limit_tier TEXT NOT NULL,
                requests_per_hour INTEGER NOT NULL,
                requests_per_day INTEGER NOT NULL,
                burst_limit INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP,
                last_used_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                privileged_requests INTEGER DEFAULT 0,
                requires_ip_whitelist BOOLEAN DEFAULT TRUE,
                requires_signature BOOLEAN DEFAULT FALSE,
                signature_secret TEXT,
                purpose TEXT NOT NULL,
                data_retention_days INTEGER DEFAULT 2555,
                compliance_notes TEXT NOT NULL
            )
        ''')
        
        # API security events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_security_events (
                event_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                api_key_id TEXT,
                attorney_id TEXT,
                endpoint TEXT NOT NULL,
                http_method TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                security_level TEXT NOT NULL,
                authentication_result BOOLEAN NOT NULL,
                authorization_result BOOLEAN NOT NULL,
                rate_limit_status TEXT NOT NULL,
                description TEXT NOT NULL,
                details TEXT NOT NULL,
                response_code INTEGER NOT NULL,
                response_time_ms REAL NOT NULL,
                risk_score REAL DEFAULT 0.0,
                requires_review BOOLEAN DEFAULT FALSE,
                contains_privileged_data BOOLEAN DEFAULT FALSE,
                client_data_accessed TEXT NOT NULL
            )
        ''')
        
        # Rate limiting tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_rate_limits (
                limit_id TEXT PRIMARY KEY,
                api_key_id TEXT NOT NULL,
                window_start TIMESTAMP NOT NULL,
                window_type TEXT NOT NULL,
                request_count INTEGER DEFAULT 0,
                last_request TIMESTAMP NOT NULL,
                FOREIGN KEY (api_key_id) REFERENCES attorney_api_keys (key_id)
            )
        ''')
        
        # API endpoint permissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_endpoint_permissions (
                permission_id TEXT PRIMARY KEY,
                endpoint_pattern TEXT NOT NULL,
                required_security_level TEXT NOT NULL,
                allowed_roles TEXT NOT NULL,
                requires_privileged_access BOOLEAN DEFAULT FALSE,
                rate_limit_override INTEGER,
                description TEXT NOT NULL,
                compliance_category TEXT NOT NULL,
                data_sensitivity TEXT NOT NULL
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_attorney ON attorney_api_keys (attorney_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON attorney_api_keys (api_key_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON api_security_events (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_events_attorney ON api_security_events (attorney_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_events_endpoint ON api_security_events (endpoint)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rate_limits_key ON api_rate_limits (api_key_id)')
        
        conn.commit()
        conn.close()
        
        # Initialize default endpoint permissions
        self._initialize_default_endpoints()
    
    def _initialize_default_endpoints(self):
        """Initialize default API endpoint permissions"""
        default_endpoints = [
            {
                "endpoint_pattern": "/api/public/*",
                "required_security_level": APISecurityLevel.PUBLIC,
                "allowed_roles": ["all"],
                "requires_privileged_access": False,
                "description": "Public API endpoints",
                "compliance_category": "public",
                "data_sensitivity": "public"
            },
            {
                "endpoint_pattern": "/api/auth/*",
                "required_security_level": APISecurityLevel.AUTHENTICATED,
                "allowed_roles": ["all"],
                "requires_privileged_access": False,
                "description": "Authentication endpoints",
                "compliance_category": "authentication",
                "data_sensitivity": "confidential"
            },
            {
                "endpoint_pattern": "/api/clients/*",
                "required_security_level": APISecurityLevel.ATTORNEY_ONLY,
                "allowed_roles": ["associate", "senior_associate", "partner", "managing_partner"],
                "requires_privileged_access": True,
                "description": "Client management endpoints",
                "compliance_category": "client_data",
                "data_sensitivity": "privileged"
            },
            {
                "endpoint_pattern": "/api/documents/*",
                "required_security_level": APISecurityLevel.PRIVILEGED,
                "allowed_roles": ["associate", "senior_associate", "partner", "managing_partner"],
                "requires_privileged_access": True,
                "description": "Document management endpoints",
                "compliance_category": "legal_documents",
                "data_sensitivity": "privileged"
            },
            {
                "endpoint_pattern": "/api/admin/*",
                "required_security_level": APISecurityLevel.ADMINISTRATIVE,
                "allowed_roles": ["partner", "managing_partner", "it_administrator"],
                "requires_privileged_access": False,
                "description": "Administrative endpoints",
                "compliance_category": "administration",
                "data_sensitivity": "confidential"
            },
            {
                "endpoint_pattern": "/api/compliance/*",
                "required_security_level": APISecurityLevel.CRITICAL,
                "allowed_roles": ["managing_partner", "compliance_officer"],
                "requires_privileged_access": True,
                "description": "Compliance and audit endpoints",
                "compliance_category": "compliance",
                "data_sensitivity": "restricted"
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for endpoint in default_endpoints:
            permission_id = secrets.token_hex(8)
            cursor.execute('''
                INSERT OR IGNORE INTO api_endpoint_permissions (
                    permission_id, endpoint_pattern, required_security_level,
                    allowed_roles, requires_privileged_access, description,
                    compliance_category, data_sensitivity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                permission_id,
                endpoint["endpoint_pattern"],
                endpoint["required_security_level"].value,
                json.dumps(endpoint["allowed_roles"]),
                endpoint["requires_privileged_access"],
                endpoint["description"],
                endpoint["compliance_category"],
                endpoint["data_sensitivity"]
            ))
        
        conn.commit()
        conn.close()
    
    def create_api_key(
        self,
        attorney_id: str,
        attorney_email: str,
        attorney_role: str,
        key_name: str,
        description: str,
        purpose: str,
        security_level: APISecurityLevel,
        expires_days: Optional[int] = 365,
        allowed_endpoints: Optional[List[str]] = None,
        allowed_ip_ranges: Optional[List[str]] = None
    ) -> Tuple[str, str]:  # Returns (key_id, api_key)
        """Create new attorney API key with security controls"""
        
        # Validate attorney role permissions
        allowed_levels = self.role_security_mapping.get(attorney_role, [APISecurityLevel.PUBLIC])
        if security_level not in allowed_levels:
            raise ValueError(f"Attorney role {attorney_role} cannot access security level {security_level.value}")
        
        # Generate key components
        key_id = secrets.token_hex(16)
        api_key = f"atty_{secrets.token_urlsafe(32)}"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Set rate limiting based on role
        role_tier_mapping = {
            "receptionist": RateLimitTier.BASIC,
            "legal_assistant": RateLimitTier.BASIC,
            "paralegal": RateLimitTier.PROFESSIONAL,
            "associate": RateLimitTier.PROFESSIONAL,
            "senior_associate": RateLimitTier.PREMIUM,
            "partner": RateLimitTier.ENTERPRISE,
            "managing_partner": RateLimitTier.ENTERPRISE
        }
        
        rate_limit_tier = role_tier_mapping.get(attorney_role, RateLimitTier.BASIC)
        limits = self.rate_limits[rate_limit_tier]
        
        # Set expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        
        # Default IP ranges (if not specified, require IP whitelist)
        if allowed_ip_ranges is None:
            allowed_ip_ranges = []
        
        # Default endpoints (if not specified, allow based on security level)
        if allowed_endpoints is None:
            allowed_endpoints = self._get_default_endpoints_for_security_level(security_level)
        
        # Create API key object
        api_key_obj = APIKey(
            key_id=key_id,
            api_key_hash=api_key_hash,
            attorney_id=attorney_id,
            attorney_email=attorney_email,
            attorney_role=attorney_role,
            key_name=key_name,
            description=description,
            security_level=security_level,
            allowed_endpoints=allowed_endpoints,
            denied_endpoints=[],
            allowed_ip_ranges=allowed_ip_ranges,
            rate_limit_tier=rate_limit_tier,
            requests_per_hour=limits["hour"],
            requests_per_day=limits["day"],
            burst_limit=limits["burst"],
            created_at=datetime.now(),
            expires_at=expires_at,
            last_used_at=None,
            is_active=True,
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            privileged_requests=0,
            requires_ip_whitelist=len(allowed_ip_ranges) == 0,
            requires_signature=security_level in [APISecurityLevel.CRITICAL, APISecurityLevel.ADMINISTRATIVE],
            signature_secret=secrets.token_hex(32) if security_level in [APISecurityLevel.CRITICAL, APISecurityLevel.ADMINISTRATIVE] else None,
            purpose=purpose,
            data_retention_days=2555,  # 7 years default
            compliance_notes=[]
        )
        
        # Store in database
        self._store_api_key(api_key_obj)
        
        # Log API key creation
        self.logger.info(
            f"API key created: {key_id} - Attorney: {attorney_email} - "
            f"Security Level: {security_level.value} - Rate Tier: {rate_limit_tier.value}"
        )
        
        return key_id, api_key
    
    def _get_default_endpoints_for_security_level(self, security_level: APISecurityLevel) -> List[str]:
        """Get default allowed endpoints based on security level"""
        endpoint_mapping = {
            APISecurityLevel.PUBLIC: ["/api/public/*"],
            APISecurityLevel.AUTHENTICATED: ["/api/public/*", "/api/auth/*"],
            APISecurityLevel.ATTORNEY_ONLY: ["/api/public/*", "/api/auth/*", "/api/clients/*"],
            APISecurityLevel.PRIVILEGED: ["/api/public/*", "/api/auth/*", "/api/clients/*", "/api/documents/*"],
            APISecurityLevel.ADMINISTRATIVE: ["/api/public/*", "/api/auth/*", "/api/clients/*", "/api/documents/*", "/api/admin/*"],
            APISecurityLevel.CRITICAL: ["*"]  # All endpoints
        }
        
        return endpoint_mapping.get(security_level, ["/api/public/*"])
    
    def authenticate_api_request(
        self,
        api_key: str,
        endpoint: str,
        http_method: str,
        ip_address: str,
        user_agent: str,
        signature: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> Tuple[bool, Optional[APIKey], Dict[str, Any]]:
        """Authenticate and authorize API request"""
        
        # Hash the provided API key
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Look up API key
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM attorney_api_keys
            WHERE api_key_hash = ? AND is_active = TRUE
        ''', (api_key_hash,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, None, {"error": "Invalid API key"}
        
        # Parse API key data
        columns = [desc[0] for desc in cursor.description]
        key_data = dict(zip(columns, row))
        api_key_obj = self._row_to_api_key(key_data)
        
        # Check expiration
        if api_key_obj.expires_at and datetime.now() > api_key_obj.expires_at:
            conn.close()
            return False, None, {"error": "API key expired"}
        
        # Check IP whitelist
        if api_key_obj.requires_ip_whitelist and api_key_obj.allowed_ip_ranges:
            if not self._is_ip_allowed(ip_address, api_key_obj.allowed_ip_ranges):
                conn.close()
                return False, None, {"error": "IP address not allowed"}
        
        # Check endpoint permissions
        if not self._is_endpoint_allowed(endpoint, api_key_obj.allowed_endpoints):
            conn.close()
            return False, None, {"error": "Endpoint not allowed"}
        
        # Check signature if required
        if api_key_obj.requires_signature:
            if not signature or not timestamp:
                conn.close()
                return False, None, {"error": "Signature required"}
            
            if not self._verify_signature(api_key, endpoint, http_method, timestamp, signature, api_key_obj.signature_secret):
                conn.close()
                return False, None, {"error": "Invalid signature"}
        
        # Check rate limits
        rate_limit_status = self._check_rate_limits(api_key_obj.key_id, api_key_obj)
        if not rate_limit_status["allowed"]:
            conn.close()
            return False, api_key_obj, {"error": "Rate limit exceeded", "rate_limit": rate_limit_status}
        
        # Update usage statistics
        self._update_api_key_usage(api_key_obj.key_id, endpoint, True)
        
        conn.close()
        
        return True, api_key_obj, {"rate_limit": rate_limit_status}
    
    def _is_ip_allowed(self, ip_address: str, allowed_ranges: List[str]) -> bool:
        """Check if IP address is in allowed ranges"""
        try:
            client_ip = ipaddress.ip_address(ip_address)
            
            for range_str in allowed_ranges:
                if '/' in range_str:
                    # CIDR notation
                    network = ipaddress.ip_network(range_str, strict=False)
                    if client_ip in network:
                        return True
                else:
                    # Single IP
                    if client_ip == ipaddress.ip_address(range_str):
                        return True
            
            return False
        except:
            return False
    
    def _is_endpoint_allowed(self, endpoint: str, allowed_patterns: List[str]) -> bool:
        """Check if endpoint matches allowed patterns"""
        for pattern in allowed_patterns:
            if pattern == "*":
                return True
            if pattern.endswith("/*"):
                prefix = pattern[:-2]
                if endpoint.startswith(prefix):
                    return True
            elif pattern == endpoint:
                return True
        
        return False
    
    def _verify_signature(
        self,
        api_key: str,
        endpoint: str,
        http_method: str,
        timestamp: str,
        signature: str,
        secret: str
    ) -> bool:
        """Verify HMAC signature for critical endpoints"""
        try:
            # Check timestamp freshness (within 5 minutes)
            request_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if abs((datetime.now() - request_time.replace(tzinfo=None)).total_seconds()) > 300:
                return False
            
            # Create signature string
            signature_string = f"{http_method}:{endpoint}:{timestamp}:{api_key}"
            
            # Calculate expected signature
            expected_signature = hmac.new(
                secret.encode(),
                signature_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
        except:
            return False
    
    def _check_rate_limits(self, key_id: str, api_key_obj: APIKey) -> Dict[str, Any]:
        """Check rate limits for API key"""
        now = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check hourly limit
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        cursor.execute('''
            SELECT request_count FROM api_rate_limits
            WHERE api_key_id = ? AND window_type = 'hour' AND window_start = ?
        ''', (key_id, hour_start.isoformat()))
        
        hour_result = cursor.fetchone()
        hour_count = hour_result[0] if hour_result else 0
        
        # Check daily limit
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute('''
            SELECT request_count FROM api_rate_limits
            WHERE api_key_id = ? AND window_type = 'day' AND window_start = ?
        ''', (key_id, day_start.isoformat()))
        
        day_result = cursor.fetchone()
        day_count = day_result[0] if day_result else 0
        
        # Check if limits are exceeded
        hour_exceeded = hour_count >= api_key_obj.requests_per_hour
        day_exceeded = day_count >= api_key_obj.requests_per_day
        
        # Update counters if not exceeded
        if not (hour_exceeded or day_exceeded):
            # Update hourly counter
            cursor.execute('''
                INSERT OR REPLACE INTO api_rate_limits
                (limit_id, api_key_id, window_start, window_type, request_count, last_request)
                VALUES (?, ?, ?, 'hour', ?, ?)
            ''', (f"{key_id}_hour_{int(hour_start.timestamp())}", key_id, hour_start.isoformat(), hour_count + 1, now.isoformat()))
            
            # Update daily counter
            cursor.execute('''
                INSERT OR REPLACE INTO api_rate_limits
                (limit_id, api_key_id, window_start, window_type, request_count, last_request)
                VALUES (?, ?, ?, 'day', ?, ?)
            ''', (f"{key_id}_day_{int(day_start.timestamp())}", key_id, day_start.isoformat(), day_count + 1, now.isoformat()))
            
            conn.commit()
        
        conn.close()
        
        return {
            "allowed": not (hour_exceeded or day_exceeded),
            "hour_limit": api_key_obj.requests_per_hour,
            "hour_used": hour_count,
            "hour_remaining": max(0, api_key_obj.requests_per_hour - hour_count),
            "day_limit": api_key_obj.requests_per_day,
            "day_used": day_count,
            "day_remaining": max(0, api_key_obj.requests_per_day - day_count),
            "reset_hour": (hour_start + timedelta(hours=1)).isoformat(),
            "reset_day": (day_start + timedelta(days=1)).isoformat()
        }
    
    def log_api_security_event(
        self,
        event_type: APIEventType,
        severity: str,
        endpoint: str,
        http_method: str,
        ip_address: str,
        user_agent: str,
        response_code: int,
        response_time_ms: float,
        description: str,
        api_key_id: Optional[str] = None,
        attorney_id: Optional[str] = None,
        authentication_result: bool = False,
        authorization_result: bool = False,
        contains_privileged_data: bool = False,
        client_data_accessed: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log API security event for monitoring and compliance"""
        
        event_id = secrets.token_hex(16)
        
        # Calculate risk score
        risk_score = self._calculate_event_risk_score(
            event_type, severity, endpoint, response_code, contains_privileged_data
        )
        
        event = APISecurityEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            api_key_id=api_key_id,
            attorney_id=attorney_id,
            endpoint=endpoint,
            http_method=http_method,
            ip_address=ip_address,
            user_agent=user_agent,
            security_level=self._get_endpoint_security_level(endpoint),
            authentication_result=authentication_result,
            authorization_result=authorization_result,
            rate_limit_status={"status": "normal"},  # Placeholder
            description=description,
            details=details or {},
            response_code=response_code,
            response_time_ms=response_time_ms,
            risk_score=risk_score,
            requires_review=risk_score >= 7.0 or event_type in [APIEventType.API_KEY_COMPROMISED, APIEventType.PRIVILEGED_ACCESS],
            contains_privileged_data=contains_privileged_data,
            client_data_accessed=client_data_accessed or []
        )
        
        # Store event
        self._store_security_event(event)
        
        # Log event
        log_message = (
            f"API Security Event: {event_type.value} - "
            f"Endpoint: {endpoint} - IP: {ip_address} - "
            f"Risk Score: {risk_score:.1f} - "
            f"Response: {response_code}"
        )
        
        if severity == "HIGH" or severity == "CRITICAL":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        return event_id

# Global attorney API security manager instance
attorney_api_security = AttorneyAPISecurityManager()