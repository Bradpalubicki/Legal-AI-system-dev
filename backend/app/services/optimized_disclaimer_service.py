#!/usr/bin/env python3
"""
OPTIMIZED DISCLAIMER SERVICE

High-performance disclaimer service with caching and optimization:
- In-memory disclaimer caching with TTL
- Pre-compiled disclaimer templates
- Async disclaimer generation
- Response time monitoring
- Cache warming and preloading

Target: <50ms response time for disclaimer retrieval
"""

import os
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import json
import hashlib
from functools import lru_cache
import threading

# Import performance optimizer
try:
    from backend.app.core.performance_optimizer import performance_optimizer
except ImportError:
    performance_optimizer = None

logger = logging.getLogger(__name__)

@dataclass
class DisclaimerTemplate:
    """Compiled disclaimer template"""
    template_id: str
    content: str
    variables: List[str]
    compiled_content: str
    last_updated: datetime

class OptimizedDisclaimerService:
    """High-performance disclaimer service with caching"""
    
    def __init__(self):
        # Pre-compiled disclaimer templates
        self.templates = {}
        self.template_cache = {}
        self.cache_lock = threading.RLock()
        
        # Performance metrics
        self.request_count = 0
        self.cache_hits = 0
        self.total_response_time = 0.0
        
        # Initialize service
        self._load_disclaimer_templates()
        self._warm_cache()
        
        logger.info("[OPTIMIZED_DISCLAIMER] Optimized disclaimer service initialized")
    
    def _load_disclaimer_templates(self) -> None:
        """Load and compile disclaimer templates"""
        
        # Critical legal advice disclaimer
        self.templates['legal_advice'] = DisclaimerTemplate(
            template_id='legal_advice',
            content="""CRITICAL LEGAL DISCLAIMER

This response contains information that may constitute legal advice. 
This information is provided for general informational purposes only 
and should not be considered legal advice. Legal matters are highly 
fact-specific and laws vary by jurisdiction. You should consult with 
a qualified attorney in your jurisdiction for advice regarding your 
specific legal situation.

DO NOT RELY ON THIS INFORMATION FOR LEGAL DECISIONS WITHOUT 
CONSULTING A LICENSED ATTORNEY.""",
            variables=[],
            compiled_content="",
            last_updated=datetime.utcnow()
        )
        
        # Legal guidance disclaimer
        self.templates['legal_guidance'] = DisclaimerTemplate(
            template_id='legal_guidance',
            content="""LEGAL GUIDANCE DISCLAIMER

This response contains general guidance on legal matters. 
This information is provided for educational purposes only and 
should not be considered legal advice. Laws and procedures vary 
by jurisdiction and individual circumstances. Please consult with 
a qualified attorney for advice specific to your situation.""",
            variables=[],
            compiled_content="",
            last_updated=datetime.utcnow()
        )
        
        # Standard legal information disclaimer
        self.templates['legal_information'] = DisclaimerTemplate(
            template_id='legal_information',
            content="""LEGAL INFORMATION DISCLAIMER

This response contains legal information for general educational 
purposes only. This is not legal advice and should not be relied 
upon for legal decisions. Laws vary by jurisdiction and individual 
circumstances may affect legal outcomes.""",
            variables=[],
            compiled_content="",
            last_updated=datetime.utcnow()
        )
        
        # Enhanced disclaimer with context
        self.templates['enhanced'] = DisclaimerTemplate(
            template_id='enhanced',
            content="""ENHANCED LEGAL DISCLAIMER

This response contains legal guidance that should not be relied upon without 
professional consultation. Legal matters are highly fact-specific and laws 
vary significantly by jurisdiction.

STRONGLY RECOMMENDED: Consult with a qualified attorney before making any 
legal decisions based on this information.""",
            variables=[],
            compiled_content="",
            last_updated=datetime.utcnow()
        )
        
        # New York-specific disclaimer for UPL compliance
        self.templates['ny_specific'] = DisclaimerTemplate(
            template_id='ny_specific',
            content="""NEW YORK COMPLIANCE NOTICE

This system provides information only - not legal advice. NY law requires licensed attorneys provide legal advice.

AI DISCLOSURE: Uses AI per NYC Bar Opinion 2024-5. All AI content must be attorney-reviewed before legal decisions.

VERIFY CITATIONS: All legal references need independent verification as AI may produce errors.

Consult a NY-licensed attorney for legal advice. No attorney-client relationship created.""",
            variables=[],
            compiled_content="",
            last_updated=datetime.utcnow()
        )
        
        # Page-level disclaimer
        self.templates['page_disclaimer'] = DisclaimerTemplate(
            template_id='page_disclaimer',
            content="""This legal AI system provides information for educational purposes only. 
All information should be verified with qualified legal professionals. 
No attorney-client relationship is created through use of this system.""",
            variables=[],
            compiled_content="",
            last_updated=datetime.utcnow()
        )
        
        # Pre-compile all templates
        for template in self.templates.values():
            template.compiled_content = template.content.strip()
    
    def _warm_cache(self) -> None:
        """Pre-warm disclaimer cache with common requests"""
        
        # Warm cache with all template types
        cache_keys = [
            'legal_advice',
            'legal_guidance', 
            'legal_information',
            'enhanced',
            'page_disclaimer',
            '/test',
            '/home',
            '/chat',
            '/analysis'
        ]
        
        for key in cache_keys:
            try:
                if key in self.templates:
                    self._cache_disclaimer(key, self.templates[key].compiled_content)
                else:
                    # Generate page disclaimer
                    disclaimer = self._generate_page_disclaimer(key)
                    self._cache_disclaimer(f"page_{key}", disclaimer)
            except Exception as e:
                logger.error(f"Failed to warm cache for {key}: {e}")
        
        logger.info(f"[OPTIMIZED_DISCLAIMER] Cache warmed with {len(cache_keys)} entries")
    
    def _cache_disclaimer(self, key: str, content: str, ttl_seconds: int = 300) -> None:
        """Cache disclaimer content"""
        if performance_optimizer:
            performance_optimizer.disclaimer_cache.set(key, content)
        else:
            # Fallback local cache
            with self.cache_lock:
                self.template_cache[key] = {
                    'content': content,
                    'timestamp': time.time(),
                    'ttl': ttl_seconds
                }
    
    def _get_cached_disclaimer(self, key: str) -> Optional[str]:
        """Get cached disclaimer content"""
        if performance_optimizer:
            return performance_optimizer.disclaimer_cache.get(key)
        else:
            # Fallback local cache
            with self.cache_lock:
                entry = self.template_cache.get(key)
                if entry:
                    if time.time() - entry['timestamp'] < entry['ttl']:
                        return entry['content']
                    else:
                        # Expired
                        del self.template_cache[key]
            return None
    
    async def get_ai_response_disclaimer(self, risk_level: str = 'legal_information') -> str:
        """Get AI response disclaimer with caching - Target: <50ms"""
        start_time = time.time()
        
        try:
            self.request_count += 1
            
            # Try cache first
            cached_disclaimer = self._get_cached_disclaimer(f"ai_{risk_level}")
            if cached_disclaimer:
                self.cache_hits += 1
                response_time = time.time() - start_time
                self.total_response_time += response_time
                
                # Record performance metrics
                if performance_optimizer:
                    performance_optimizer.metrics_collector.record_metric(
                        'disclaimers', response_time, throughput=1, accuracy=100
                    )
                
                return cached_disclaimer
            
            # Generate disclaimer
            if risk_level in self.templates:
                disclaimer = self.templates[risk_level].compiled_content
            else:
                # Fallback to standard disclaimer
                disclaimer = self.templates['legal_information'].compiled_content
            
            # Cache the result
            self._cache_disclaimer(f"ai_{risk_level}", disclaimer)
            
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            # Record performance metrics
            if performance_optimizer:
                performance_optimizer.metrics_collector.record_metric(
                    'disclaimers', response_time, throughput=1, accuracy=100
                )
            
            return disclaimer
            
        except Exception as e:
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            # Record error metrics
            if performance_optimizer:
                performance_optimizer.metrics_collector.record_metric(
                    'disclaimers', response_time, error_count=1
                )
            
            logger.error(f"Failed to get AI response disclaimer: {e}")
            return self.templates['legal_information'].compiled_content
    
    async def get_page_disclaimers(self, page_path: str) -> List[str]:
        """Get page-level disclaimers with caching - Target: <50ms"""
        start_time = time.time()
        
        try:
            self.request_count += 1
            
            # Try cache first
            cache_key = f"page_{page_path}"
            cached_disclaimers = self._get_cached_disclaimer(cache_key)
            
            if cached_disclaimers:
                self.cache_hits += 1
                response_time = time.time() - start_time
                self.total_response_time += response_time
                
                # Record performance metrics
                if performance_optimizer:
                    performance_optimizer.metrics_collector.record_metric(
                        'disclaimers', response_time, throughput=1, accuracy=100
                    )
                
                return [cached_disclaimers]  # Return as list for compatibility
            
            # Generate page disclaimer
            disclaimer = self._generate_page_disclaimer(page_path)
            
            # Cache the result
            self._cache_disclaimer(cache_key, disclaimer)
            
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            # Record performance metrics
            if performance_optimizer:
                performance_optimizer.metrics_collector.record_metric(
                    'disclaimers', response_time, throughput=1, accuracy=100
                )
            
            return [disclaimer]
            
        except Exception as e:
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            # Record error metrics
            if performance_optimizer:
                performance_optimizer.metrics_collector.record_metric(
                    'disclaimers', response_time, error_count=1
                )
            
            logger.error(f"Failed to get page disclaimers for {page_path}: {e}")
            return [self.templates['page_disclaimer'].compiled_content]
    
    def _generate_page_disclaimer(self, page_path: str) -> str:
        """Generate page-specific disclaimer"""
        
        # Customize based on page type
        if any(keyword in page_path.lower() for keyword in ['chat', 'ai', 'analysis']):
            base_disclaimer = self.templates['page_disclaimer'].compiled_content
            return f"""{base_disclaimer}

AI-Generated Content Warning: This page contains AI-generated content. 
All AI responses include appropriate legal disclaimers and should not 
be considered professional legal advice."""
        
        elif any(keyword in page_path.lower() for keyword in ['document', 'contract']):
            return """Document Analysis Disclaimer: Document analysis results are for 
informational purposes only. This system does not replace professional 
legal document review. Critical legal documents should always be reviewed 
by qualified attorneys."""
        
        else:
            return self.templates['page_disclaimer'].compiled_content
    
    def get_disclaimer_by_risk_tier(self, risk_tier: str) -> str:
        """Get disclaimer by risk tier with caching"""
        
        tier_mapping = {
            'high_risk': 'legal_advice',
            'medium_risk': 'enhanced', 
            'low_risk': 'legal_guidance',
            'safe': 'legal_information'
        }
        
        template_key = tier_mapping.get(risk_tier, 'legal_information')
        
        # Use async method synchronously for caching benefits
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.get_ai_response_disclaimer(template_key))
        except RuntimeError:
            # No event loop - return directly
            return self.templates[template_key].compiled_content
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get service performance statistics"""
        
        avg_response_time = (self.total_response_time / self.request_count * 1000) if self.request_count > 0 else 0
        cache_hit_rate = (self.cache_hits / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            'service_name': 'optimized_disclaimer_service',
            'total_requests': self.request_count,
            'cache_hits': self.cache_hits,
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'avg_response_time_ms': round(avg_response_time, 2),
            'templates_loaded': len(self.templates),
            'cache_size': len(self.template_cache) if not performance_optimizer else None,
            'status': 'healthy' if avg_response_time < 50 else 'degraded',
            'meets_target': avg_response_time < 50
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Fast health check - Target: <10ms"""
        start_time = time.time()
        
        try:
            # Test basic functionality
            test_disclaimer = await self.get_ai_response_disclaimer('legal_information')
            
            response_time = time.time() - start_time
            response_time_ms = response_time * 1000
            
            stats = self.get_performance_stats()
            
            return {
                'status': 'healthy' if response_time_ms < 10 and len(test_disclaimer) > 0 else 'degraded',
                'response_time_ms': round(response_time_ms, 2),
                'meets_target': response_time_ms < 10,
                'service_stats': stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'status': 'critical',
                'error': str(e),
                'response_time_ms': round(response_time * 1000, 2),
                'meets_target': False,
                'timestamp': datetime.utcnow().isoformat()
            }

# Global optimized disclaimer service
optimized_disclaimer_service = OptimizedDisclaimerService()