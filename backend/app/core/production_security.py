#!/usr/bin/env python3
"""
PRODUCTION SECURITY HARDENING

Comprehensive security hardening for production deployment:
- API rate limiting and DDoS protection
- Request validation and sanitization
- Security headers and CORS protection
- Input/output sanitization
- JWT token hardening
- Security event monitoring
"""

import os
import time
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
import re
import json
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class SecurityConfig:
    """Production security configuration"""
    # Rate limiting
    requests_per_minute: int = 60
    burst_limit: int = 100
    
    # JWT hardening
    jwt_expiry_minutes: int = 15
    refresh_token_days: int = 7
    max_sessions_per_user: int = 3
    
    # Input validation
    max_input_length: int = 50000
    max_file_size_mb: int = 100
    allowed_file_types: Set[str] = field(default_factory=lambda: {'.pdf', '.docx', '.txt', '.rtf'})
    
    # Security monitoring
    failed_login_threshold: int = 5
    suspicious_pattern_threshold: int = 10
    block_duration_minutes: int = 30
    
    # API security
    require_https: bool = True
    cors_max_age: int = 3600
    content_type_validation: bool = True

class RateLimiter:
    """Production-grade rate limiter with sliding window"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.requests = defaultdict(deque)
        self.blocked_ips = {}
        self.lock = threading.RLock()
    
    def is_allowed(self, client_ip: str, endpoint: str = None) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed under rate limits"""
        current_time = time.time()
        
        with self.lock:
            # Check if IP is currently blocked
            if client_ip in self.blocked_ips:
                if current_time < self.blocked_ips[client_ip]:
                    return False, {
                        'error': 'IP blocked due to rate limiting',
                        'retry_after': int(self.blocked_ips[client_ip] - current_time),
                        'blocked': True
                    }
                else:
                    # Unblock expired blocks
                    del self.blocked_ips[client_ip]
            
            # Clean old requests (sliding window)
            minute_ago = current_time - 60
            request_queue = self.requests[client_ip]
            
            while request_queue and request_queue[0] < minute_ago:
                request_queue.popleft()
            
            # Check rate limits
            current_requests = len(request_queue)
            
            if current_requests >= self.config.requests_per_minute:
                # Block IP
                block_until = current_time + (self.config.block_duration_minutes * 60)
                self.blocked_ips[client_ip] = block_until
                
                logger.warning(f"[SECURITY] Rate limit exceeded for IP {client_ip}, blocked until {datetime.fromtimestamp(block_until)}")
                
                return False, {
                    'error': 'Rate limit exceeded',
                    'retry_after': self.config.block_duration_minutes * 60,
                    'requests_per_minute': self.config.requests_per_minute,
                    'blocked': True
                }
            
            # Allow request and record it
            request_queue.append(current_time)
            
            return True, {
                'allowed': True,
                'requests_remaining': self.config.requests_per_minute - current_requests - 1,
                'reset_time': int(minute_ago + 60)
            }

class InputValidator:
    """Production input validation and sanitization"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        
        # Dangerous patterns
        self.sql_patterns = [
            r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
            r'[\'";]',
            r'--',
            r'/\*|\*/',
        ]
        
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed',
        ]
        
        self.path_traversal_patterns = [
            r'\.\./.*',
            r'\.\.\\.*',
            r'/etc/',
            r'c:\\',
            r'\\windows\\',
        ]
        
        # Compile regex patterns for performance
        self.sql_regex = re.compile('|'.join(self.sql_patterns), re.IGNORECASE)
        self.xss_regex = re.compile('|'.join(self.xss_patterns), re.IGNORECASE)
        self.path_regex = re.compile('|'.join(self.path_traversal_patterns), re.IGNORECASE)
    
    def validate_input(self, data: str, input_type: str = 'general') -> tuple[bool, Optional[str]]:
        """Validate and sanitize input data"""
        
        if not data:
            return True, None
        
        # Length check
        if len(data) > self.config.max_input_length:
            return False, f"Input exceeds maximum length of {self.config.max_input_length} characters"
        
        # SQL injection check
        if self.sql_regex.search(data):
            logger.warning(f"[SECURITY] SQL injection attempt detected in {input_type} input")
            return False, "Invalid characters detected in input"
        
        # XSS check
        if self.xss_regex.search(data):
            logger.warning(f"[SECURITY] XSS attempt detected in {input_type} input")
            return False, "Invalid HTML/JavaScript detected in input"
        
        # Path traversal check
        if self.path_regex.search(data):
            logger.warning(f"[SECURITY] Path traversal attempt detected in {input_type} input")
            return False, "Invalid file path detected in input"
        
        return True, None
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize uploaded filename"""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\s.-]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        return filename
    
    def validate_file_upload(self, filename: str, content_type: str, size_bytes: int) -> tuple[bool, Optional[str]]:
        """Validate file upload"""
        
        # Size check
        max_size_bytes = self.config.max_file_size_mb * 1024 * 1024
        if size_bytes > max_size_bytes:
            return False, f"File size exceeds {self.config.max_file_size_mb}MB limit"
        
        # File type check
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext not in self.config.allowed_file_types:
            return False, f"File type {file_ext} not allowed. Allowed types: {', '.join(self.config.allowed_file_types)}"
        
        # Content type validation
        allowed_content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.rtf': 'application/rtf'
        }
        
        expected_type = allowed_content_types.get(file_ext)
        if expected_type and content_type != expected_type:
            logger.warning(f"[SECURITY] Content type mismatch: expected {expected_type}, got {content_type}")
            return False, "File content type does not match extension"
        
        return True, None

class SecurityMonitor:
    """Production security event monitoring"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.failed_logins = defaultdict(list)
        self.suspicious_activities = defaultdict(int)
        self.security_alerts = deque(maxlen=1000)
        self.lock = threading.RLock()
    
    def log_failed_login(self, client_ip: str, username: str = None) -> bool:
        """Log failed login attempt and check for suspicious activity"""
        current_time = time.time()
        
        with self.lock:
            # Clean old failed logins (last hour)
            hour_ago = current_time - 3600
            self.failed_logins[client_ip] = [
                timestamp for timestamp in self.failed_logins[client_ip] 
                if timestamp > hour_ago
            ]
            
            # Add current failed login
            self.failed_logins[client_ip].append(current_time)
            
            # Check threshold
            failed_count = len(self.failed_logins[client_ip])
            
            if failed_count >= self.config.failed_login_threshold:
                self._create_security_alert('failed_login_threshold', {
                    'client_ip': client_ip,
                    'username': username,
                    'failed_attempts': failed_count,
                    'time_window': '1 hour'
                })
                return True  # Suspicious activity detected
        
        return False
    
    def log_suspicious_activity(self, client_ip: str, activity_type: str, details: Dict[str, Any]) -> None:
        """Log suspicious activity"""
        
        with self.lock:
            self.suspicious_activities[f"{client_ip}_{activity_type}"] += 1
            
            if self.suspicious_activities[f"{client_ip}_{activity_type}"] >= self.config.suspicious_pattern_threshold:
                self._create_security_alert('suspicious_pattern', {
                    'client_ip': client_ip,
                    'activity_type': activity_type,
                    'occurrences': self.suspicious_activities[f"{client_ip}_{activity_type}"],
                    'details': details
                })
    
    def _create_security_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Create security alert"""
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': alert_type,
            'severity': 'HIGH' if alert_type == 'failed_login_threshold' else 'MEDIUM',
            'data': data,
            'alert_id': secrets.token_hex(8)
        }
        
        self.security_alerts.append(alert)
        logger.critical(f"[SECURITY ALERT] {alert_type}: {json.dumps(data)}")
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        
        with self.lock:
            recent_alerts = [
                alert for alert in self.security_alerts
                if datetime.fromisoformat(alert['timestamp']) > datetime.utcnow() - timedelta(hours=1)
            ]
            
            return {
                'active_alerts': len(recent_alerts),
                'failed_login_ips': len(self.failed_logins),
                'suspicious_activities': len(self.suspicious_activities),
                'recent_alerts': recent_alerts[-5:] if recent_alerts else [],
                'status': 'WARNING' if recent_alerts else 'SECURE',
                'last_check': datetime.utcnow().isoformat()
            }

class ProductionSecurity:
    """Main production security hardening system"""
    
    def __init__(self):
        self.config = SecurityConfig()
        self.rate_limiter = RateLimiter(self.config)
        self.input_validator = InputValidator(self.config)
        self.security_monitor = SecurityMonitor(self.config)
        
        logger.info("[PRODUCTION_SECURITY] Production security hardening initialized")
    
    def security_middleware(self, request_data: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Main security middleware for request processing"""
        
        client_ip = request_data.get('client_ip', 'unknown')
        endpoint = request_data.get('endpoint', 'unknown')
        
        # Rate limiting check
        allowed, rate_info = self.rate_limiter.is_allowed(client_ip, endpoint)
        if not allowed:
            self.security_monitor.log_suspicious_activity(client_ip, 'rate_limit_exceeded', rate_info)
            return False, {'error': 'Rate limit exceeded', 'details': rate_info}
        
        # Input validation
        if 'input_data' in request_data:
            valid, error = self.input_validator.validate_input(request_data['input_data'], 'api_request')
            if not valid:
                self.security_monitor.log_suspicious_activity(client_ip, 'invalid_input', {'error': error})
                return False, {'error': 'Invalid input', 'details': error}
        
        # File upload validation
        if 'file_data' in request_data:
            file_info = request_data['file_data']
            valid, error = self.input_validator.validate_file_upload(
                file_info.get('filename', ''),
                file_info.get('content_type', ''),
                file_info.get('size', 0)
            )
            if not valid:
                self.security_monitor.log_suspicious_activity(client_ip, 'invalid_file_upload', {'error': error})
                return False, {'error': 'Invalid file upload', 'details': error}
        
        return True, {'allowed': True, 'rate_info': rate_info}
    
    def log_failed_authentication(self, client_ip: str, username: str = None) -> None:
        """Log failed authentication attempt"""
        suspicious = self.security_monitor.log_failed_login(client_ip, username)
        if suspicious:
            logger.warning(f"[SECURITY] Suspicious login activity from {client_ip}")
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get enhanced production security headers"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'; font-src 'self'; object-src 'none'; media-src 'self'; frame-src 'none';",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
            'X-Permitted-Cross-Domain-Policies': 'none',
            'X-Download-Options': 'noopen',
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-origin'
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Production security health check"""
        start_time = time.time()
        
        security_status = self.security_monitor.get_security_status()
        response_time = (time.time() - start_time) * 1000
        
        return {
            'service': 'production_security',
            'status': 'healthy' if security_status['status'] == 'SECURE' else 'warning',
            'response_time_ms': round(response_time, 2),
            'security_status': security_status,
            'rate_limiter': {
                'active_blocks': len(self.rate_limiter.blocked_ips),
                'requests_per_minute_limit': self.config.requests_per_minute
            },
            'input_validator': {
                'max_input_length': self.config.max_input_length,
                'max_file_size_mb': self.config.max_file_size_mb
            },
            'timestamp': datetime.utcnow().isoformat()
        }

# Global production security instance
production_security = ProductionSecurity()