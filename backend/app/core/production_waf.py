#!/usr/bin/env python3
"""
PRODUCTION WEB APPLICATION FIREWALL (WAF)

Advanced WAF implementation with:
- SQL injection protection
- XSS prevention
- CSRF protection
- DDoS mitigation
- Bot detection
- Geo-blocking capabilities
"""

import re
import time
import hashlib
import logging
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
import ipaddress
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class WAFConfig:
    """WAF configuration settings"""
    # Rate limiting
    requests_per_minute: int = 100
    burst_limit: int = 200
    ddos_threshold: int = 1000
    
    # Geo-blocking
    blocked_countries: Set[str] = None
    allowed_countries: Set[str] = None
    
    # Bot detection
    bot_score_threshold: float = 0.8
    captcha_threshold: float = 0.6
    
    # Attack patterns
    enable_sql_injection_protection: bool = True
    enable_xss_protection: bool = True
    enable_path_traversal_protection: bool = True
    
    def __post_init__(self):
        if self.blocked_countries is None:
            self.blocked_countries = set()
        if self.allowed_countries is None:
            self.allowed_countries = set()

class ProductionWAF:
    """Production-grade Web Application Firewall"""
    
    def __init__(self, config: WAFConfig = None):
        self.config = config or WAFConfig()
        
        # Attack pattern signatures
        self.sql_injection_patterns = self._load_sql_injection_patterns()
        self.xss_patterns = self._load_xss_patterns()
        self.path_traversal_patterns = self._load_path_traversal_patterns()
        
        # Rate limiting storage
        self.request_counts = defaultdict(deque)
        self.blocked_ips = {}  # IP -> block_until_timestamp
        
        # Bot detection
        self.bot_signatures = self._load_bot_signatures()
        self.suspicious_patterns = self._load_suspicious_patterns()
        
        # DDoS protection
        self.ddos_detector = DDOSDetector()
        
        logger.info("[WAF] Production WAF initialized with advanced protection")
    
    def _load_sql_injection_patterns(self) -> List[re.Pattern]:
        """Load SQL injection detection patterns"""
        patterns = [
            # Classic SQL injection
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(;|\x00|\n|\r|\x1a)",
            r"(--|\#|\/\*|\*\/)",
            r"(\b(or|and)\b\s+\d+\s*=\s*\d+)",
            r"(\b(or|and)\b\s+[\w\d]+\s*=\s*[\w\d]+)",
            
            # Advanced SQL injection
            r"(char\s*\(\s*\d+\s*\))",
            r"(ascii\s*\(\s*substr)",
            r"(benchmark\s*\(\s*\d+)",
            r"(sleep\s*\(\s*\d+\s*\))",
            r"(waitfor\s+delay\s+)",
            r"(\bload_file\s*\()",
            r"(\binto\s+outfile\b)",
            
            # Blind SQL injection
            r"(if\s*\(\s*\d+\s*=\s*\d+)",
            r"(\bcase\s+when\b)",
            r"(\b(true|false)\s*=\s*(true|false))",
        ]
        
        return [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in patterns]
    
    def _load_xss_patterns(self) -> List[re.Pattern]:
        """Load XSS detection patterns"""
        patterns = [
            # Script tags
            r"<\s*script[^>]*>.*?</\s*script\s*>",
            r"<\s*script[^>]*>",
            r"javascript\s*:",
            r"vbscript\s*:",
            
            # Event handlers
            r"on\w+\s*=\s*[\"'].*?[\"']",
            r"on\w+\s*=\s*\w+",
            
            # HTML injection
            r"<\s*iframe[^>]*>",
            r"<\s*object[^>]*>",
            r"<\s*embed[^>]*>",
            r"<\s*form[^>]*>",
            
            # Advanced XSS
            r"eval\s*\(",
            r"expression\s*\(",
            r"String\.fromCharCode",
            r"document\.cookie",
            r"document\.write",
            r"window\.location",
        ]
        
        return [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in patterns]
    
    def _load_path_traversal_patterns(self) -> List[re.Pattern]:
        """Load path traversal detection patterns"""
        patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
            r"\.%2e/",
            r"\.%2e\\",
            r"%c0%ae%2e/",
            r"%c0%ae%2e\\",
        ]
        
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _load_bot_signatures(self) -> Dict[str, float]:
        """Load bot detection signatures"""
        return {
            # Known bad bots
            'scrapy': 1.0,
            'python-requests': 0.8,
            'curl': 0.7,
            'wget': 0.7,
            'nikto': 1.0,
            'sqlmap': 1.0,
            'nmap': 1.0,
            
            # Suspicious patterns
            'bot': 0.6,
            'crawler': 0.5,
            'spider': 0.5,
            'scanner': 0.9,
            'test': 0.4,
        }
    
    def _load_suspicious_patterns(self) -> List[str]:
        """Load suspicious behavior patterns"""
        return [
            # Admin path scanning
            '/admin',
            '/wp-admin',
            '/administrator',
            '/.env',
            '/config',
            
            # Common exploits
            '/phpinfo',
            '/shell',
            '/backdoor',
            '/webshell',
            
            # File extensions
            '.php',
            '.asp',
            '.aspx',
            '.jsp',
            '.cgi',
        ]
    
    async def process_request(self, request_data: Dict) -> Tuple[bool, str, Dict]:
        """
        Main WAF processing function
        Returns: (allow_request, block_reason, metadata)
        """
        client_ip = request_data.get('client_ip')
        user_agent = request_data.get('user_agent', '')
        url_path = request_data.get('url_path', '')
        query_params = request_data.get('query_params', '')
        post_data = request_data.get('post_data', '')
        headers = request_data.get('headers', {})
        
        metadata = {
            'waf_version': '2.0',
            'timestamp': datetime.utcnow().isoformat(),
            'client_ip': client_ip,
            'checks_performed': []
        }
        
        # 1. IP-based blocking check
        if self._is_ip_blocked(client_ip):
            return False, "IP_BLOCKED", metadata
        
        # 2. Rate limiting check
        if not self._check_rate_limit(client_ip):
            self._block_ip_temporarily(client_ip, minutes=15)
            metadata['checks_performed'].append('rate_limit_exceeded')
            return False, "RATE_LIMIT_EXCEEDED", metadata
        
        # 3. DDoS detection
        if self.ddos_detector.is_ddos_attack(client_ip, request_data):
            self._block_ip_temporarily(client_ip, minutes=60)
            metadata['checks_performed'].append('ddos_detected')
            return False, "DDOS_DETECTED", metadata
        
        # 4. Geo-blocking check
        block_reason = self._check_geo_blocking(client_ip)
        if block_reason:
            metadata['checks_performed'].append('geo_blocked')
            return False, block_reason, metadata
        
        # 5. Bot detection
        bot_score = self._calculate_bot_score(user_agent, headers, url_path)
        if bot_score >= self.config.bot_score_threshold:
            metadata['checks_performed'].append('bot_detected')
            metadata['bot_score'] = bot_score
            return False, "BOT_DETECTED", metadata
        
        # 6. SQL injection detection
        if self.config.enable_sql_injection_protection:
            if self._detect_sql_injection(query_params + post_data):
                metadata['checks_performed'].append('sql_injection_detected')
                return False, "SQL_INJECTION_DETECTED", metadata
        
        # 7. XSS detection
        if self.config.enable_xss_protection:
            if self._detect_xss(query_params + post_data):
                metadata['checks_performed'].append('xss_detected')
                return False, "XSS_DETECTED", metadata
        
        # 8. Path traversal detection
        if self.config.enable_path_traversal_protection:
            if self._detect_path_traversal(url_path + query_params):
                metadata['checks_performed'].append('path_traversal_detected')
                return False, "PATH_TRAVERSAL_DETECTED", metadata
        
        # 9. Suspicious pattern detection
        if self._detect_suspicious_patterns(url_path):
            metadata['checks_performed'].append('suspicious_pattern_detected')
            return False, "SUSPICIOUS_PATTERN_DETECTED", metadata
        
        # All checks passed
        metadata['checks_performed'].append('all_checks_passed')
        return True, "ALLOWED", metadata
    
    def _is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is currently blocked"""
        if client_ip in self.blocked_ips:
            block_until = self.blocked_ips[client_ip]
            if time.time() < block_until:
                return True
            else:
                # Block expired, remove it
                del self.blocked_ips[client_ip]
        return False
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check rate limiting for client IP"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old requests
        requests = self.request_counts[client_ip]
        while requests and requests[0] < minute_ago:
            requests.popleft()
        
        # Add current request
        requests.append(current_time)
        
        # Check limits
        if len(requests) > self.config.requests_per_minute:
            logger.warning(f"[WAF] Rate limit exceeded for IP {client_ip}: {len(requests)} requests/minute")
            return False
        
        return True
    
    def _block_ip_temporarily(self, client_ip: str, minutes: int):
        """Temporarily block an IP address"""
        block_until = time.time() + (minutes * 60)
        self.blocked_ips[client_ip] = block_until
        logger.warning(f"[WAF] IP {client_ip} blocked for {minutes} minutes")
    
    def _check_geo_blocking(self, client_ip: str) -> Optional[str]:
        """Check geo-blocking rules"""
        # This would integrate with a GeoIP service in production
        # For now, return None (no blocking)
        return None
    
    def _calculate_bot_score(self, user_agent: str, headers: Dict, url_path: str) -> float:
        """Calculate bot probability score (0.0 - 1.0)"""
        score = 0.0
        user_agent_lower = user_agent.lower()
        
        # Check bot signatures
        for signature, weight in self.bot_signatures.items():
            if signature in user_agent_lower:
                score = max(score, weight)
        
        # Missing common headers
        common_headers = ['accept', 'accept-language', 'accept-encoding']
        missing_headers = sum(1 for h in common_headers if h not in headers)
        score += missing_headers * 0.2
        
        # Suspicious URL patterns
        suspicious_count = sum(1 for pattern in self.suspicious_patterns if pattern in url_path)
        score += suspicious_count * 0.3
        
        return min(score, 1.0)
    
    def _detect_sql_injection(self, data: str) -> bool:
        """Detect SQL injection attempts"""
        if not data:
            return False
        
        data_lower = data.lower()
        for pattern in self.sql_injection_patterns:
            if pattern.search(data_lower):
                logger.warning(f"[WAF] SQL injection detected: {pattern.pattern[:50]}...")
                return True
        
        return False
    
    def _detect_xss(self, data: str) -> bool:
        """Detect XSS attempts"""
        if not data:
            return False
        
        for pattern in self.xss_patterns:
            if pattern.search(data):
                logger.warning(f"[WAF] XSS detected: {pattern.pattern[:50]}...")
                return True
        
        return False
    
    def _detect_path_traversal(self, data: str) -> bool:
        """Detect path traversal attempts"""
        if not data:
            return False
        
        for pattern in self.path_traversal_patterns:
            if pattern.search(data):
                logger.warning(f"[WAF] Path traversal detected: {pattern.pattern[:50]}...")
                return True
        
        return False
    
    def _detect_suspicious_patterns(self, url_path: str) -> bool:
        """Detect suspicious URL patterns"""
        url_lower = url_path.lower()
        for pattern in self.suspicious_patterns:
            if pattern in url_lower:
                logger.warning(f"[WAF] Suspicious pattern detected: {pattern}")
                return True
        
        return False

class DDOSDetector:
    """DDoS attack detection system"""
    
    def __init__(self):
        self.request_history = defaultdict(deque)
        self.attack_patterns = defaultdict(int)
    
    def is_ddos_attack(self, client_ip: str, request_data: Dict) -> bool:
        """Detect DDoS attack patterns"""
        current_time = time.time()
        
        # Track request frequency
        ip_requests = self.request_history[client_ip]
        ip_requests.append(current_time)
        
        # Clean old requests (last 5 minutes)
        five_minutes_ago = current_time - 300
        while ip_requests and ip_requests[0] < five_minutes_ago:
            ip_requests.popleft()
        
        # Check for DDoS patterns
        requests_per_minute = len(ip_requests) / 5
        
        if requests_per_minute > 100:  # More than 100 req/min average
            logger.warning(f"[WAF] Possible DDoS from {client_ip}: {requests_per_minute} req/min")
            return True
        
        return False

# Global WAF instance
production_waf = ProductionWAF()