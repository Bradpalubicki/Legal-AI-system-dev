#!/usr/bin/env python3
"""
PRODUCTION LOGGING AND MONITORING

Comprehensive logging and monitoring system for production:
- Structured JSON logging with correlation IDs
- Performance metrics collection
- Business metrics tracking
- Log aggregation and alerting
- Compliance and audit logging
"""

import os
import time
import json
import logging
import logging.handlers
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
from contextlib import contextmanager
from functools import wraps
import asyncio
import traceback

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    service: str
    correlation_id: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None

class ProductionLogger:
    """Production-grade structured logger"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.correlation_id = None
        
        # Setup structured logging
        self._setup_logging()
        self.logger = logging.getLogger(service_name)
        
        # Thread local storage for correlation IDs
        self.local = threading.local()
    
    def _setup_logging(self) -> None:
        """Configure production logging"""
        
        # Create logs directory
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Remove default handlers
        root_logger.handlers.clear()
        
        # JSON formatter for structured logging
        class JSONFormatter(logging.Formatter):
            def __init__(self, service_name, logger_instance):
                super().__init__()
                self.service_name = service_name
                self.logger_instance = logger_instance
                
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': record.levelname,
                    'service': self.service_name,
                    'message': record.getMessage(),
                    'logger': record.name,
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno,
                }
                
                # Add correlation ID if available
                try:
                    correlation_id = getattr(self.logger_instance.local, 'correlation_id', None)
                    if correlation_id:
                        log_entry['correlation_id'] = correlation_id
                except AttributeError:
                    pass  # No correlation ID available
                
                # Add extra fields from record
                if hasattr(record, 'extra'):
                    log_entry.update(record.extra)
                
                # Add exception info
                if record.exc_info:
                    log_entry['exception'] = {
                        'type': record.exc_info[0].__name__,
                        'message': str(record.exc_info[1]),
                        'traceback': traceback.format_exception(*record.exc_info)
                    }
                
                return json.dumps(log_entry)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            f"{log_dir}/{self.service_name}.log",
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=10
        )
        file_handler.setFormatter(JSONFormatter(self.service_name, self))
        file_handler.setLevel(logging.INFO)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            f"{log_dir}/{self.service_name}_error.log",
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5
        )
        error_handler.setFormatter(JSONFormatter(self.service_name, self))
        error_handler.setLevel(logging.ERROR)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s'
        ))
        console_handler.setLevel(logging.WARNING)  # Only warnings and above to console
        
        # Add handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)
    
    @contextmanager
    def correlation_context(self, correlation_id: str = None):
        """Context manager for correlation ID"""
        if correlation_id is None:
            correlation_id = secrets.token_hex(8)
        
        old_id = getattr(self.local, 'correlation_id', None)
        self.local.correlation_id = correlation_id
        
        try:
            yield correlation_id
        finally:
            if old_id:
                self.local.correlation_id = old_id
            else:
                delattr(self.local, 'correlation_id')
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with structured data"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with structured data"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with structured data"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with structured data"""
        self.logger.critical(message, extra=kwargs)

class MetricsCollector:
    """Production metrics collection system"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'errors': 0,
            'last_hour': deque(maxlen=3600),  # Store metrics for last hour
            'daily_totals': defaultdict(int)
        })
        self.lock = threading.RLock()
        self.business_metrics = defaultdict(int)
        
        # Start cleanup task
        self._start_cleanup_task()
    
    def record_metric(self, metric_name: str, duration: float = None, 
                     count: int = 1, error: bool = False, **kwargs) -> None:
        """Record a metric with optional timing"""
        
        current_time = time.time()
        date_key = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d')
        
        with self.lock:
            metric = self.metrics[metric_name]
            
            metric['count'] += count
            metric['daily_totals'][date_key] += count
            
            if duration is not None:
                metric['total_time'] += duration
                
                # Store for percentile calculations
                metric['last_hour'].append({
                    'timestamp': current_time,
                    'duration': duration,
                    'error': error
                })
            
            if error:
                metric['errors'] += 1
                
            # Store additional data
            for key, value in kwargs.items():
                if key not in metric:
                    metric[key] = 0
                metric[key] += value if isinstance(value, (int, float)) else 1
    
    def record_business_metric(self, metric_name: str, value: Union[int, float] = 1) -> None:
        """Record business metrics (documents processed, users served, etc.)"""
        with self.lock:
            self.business_metrics[metric_name] += value
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        
        current_time = time.time()
        hour_ago = current_time - 3600
        
        with self.lock:
            summary = {
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': {},
                'business_metrics': dict(self.business_metrics),
                'system_health': 'healthy'
            }
            
            for name, metric in self.metrics.items():
                # Calculate recent metrics (last hour)
                recent_entries = [
                    entry for entry in metric['last_hour']
                    if entry['timestamp'] > hour_ago
                ]
                
                recent_durations = [e['duration'] for e in recent_entries]
                recent_errors = sum(1 for e in recent_entries if e.get('error', False))
                
                metric_summary = {
                    'total_count': metric['count'],
                    'total_errors': metric['errors'],
                    'error_rate_percent': (metric['errors'] / metric['count'] * 100) if metric['count'] > 0 else 0,
                    'recent_hour': {
                        'count': len(recent_entries),
                        'errors': recent_errors,
                        'avg_duration_ms': (sum(recent_durations) / len(recent_durations) * 1000) if recent_durations else 0,
                        'throughput_per_minute': len(recent_entries) / 60,
                    }
                }
                
                # Calculate percentiles for recent data
                if recent_durations:
                    sorted_durations = sorted(recent_durations)
                    metric_summary['recent_hour']['p50_ms'] = sorted_durations[len(sorted_durations) // 2] * 1000
                    metric_summary['recent_hour']['p95_ms'] = sorted_durations[int(len(sorted_durations) * 0.95)] * 1000
                    metric_summary['recent_hour']['p99_ms'] = sorted_durations[int(len(sorted_durations) * 0.99)] * 1000
                
                summary['metrics'][name] = metric_summary
                
                # Update system health
                if metric_summary['error_rate_percent'] > 5:
                    summary['system_health'] = 'degraded'
                elif metric_summary['error_rate_percent'] > 1:
                    summary['system_health'] = 'warning'
            
            return summary
    
    def _start_cleanup_task(self) -> None:
        """Start background task to clean old metrics"""
        def cleanup():
            while True:
                time.sleep(300)  # Clean every 5 minutes
                self._cleanup_old_metrics()
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_metrics(self) -> None:
        """Clean up old metric entries"""
        cutoff_time = time.time() - 3600  # Keep last hour
        
        with self.lock:
            for metric in self.metrics.values():
                # Clean last_hour deque (it has maxlen, but we can clean more aggressively)
                while metric['last_hour'] and metric['last_hour'][0]['timestamp'] < cutoff_time:
                    metric['last_hour'].popleft()

class ComplianceLogger:
    """Legal compliance and audit logging"""
    
    def __init__(self):
        self.logger = ProductionLogger('compliance')
        self.audit_events = deque(maxlen=10000)  # Keep recent audit events
        self.lock = threading.RLock()
    
    def log_data_access(self, user_id: str, resource_type: str, resource_id: str, 
                       action: str, success: bool = True, **kwargs) -> None:
        """Log data access for compliance"""
        
        event = {
            'event_type': 'data_access',
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action,
            'success': success,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': kwargs
        }
        
        with self.lock:
            self.audit_events.append(event)
        
        self.logger.info(f"Data access: {action} {resource_type}", extra=event)
    
    def log_document_processing(self, document_id: str, user_id: str, 
                              processing_type: str, duration_ms: float, **kwargs) -> None:
        """Log document processing events"""
        
        event = {
            'event_type': 'document_processing',
            'document_id': document_id,
            'user_id': user_id,
            'processing_type': processing_type,
            'duration_ms': duration_ms,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': kwargs
        }
        
        with self.lock:
            self.audit_events.append(event)
        
        self.logger.info(f"Document processed: {processing_type}", extra=event)
    
    def log_ai_interaction(self, user_id: str, model: str, tokens_used: int, 
                          response_time_ms: float, cost: float = None, **kwargs) -> None:
        """Log AI model interactions"""
        
        event = {
            'event_type': 'ai_interaction',
            'user_id': user_id,
            'model': model,
            'tokens_used': tokens_used,
            'response_time_ms': response_time_ms,
            'cost': cost,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': kwargs
        }
        
        with self.lock:
            self.audit_events.append(event)
        
        self.logger.info(f"AI interaction: {model}", extra=event)
    
    def get_compliance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate compliance report for specified time period"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self.lock:
            recent_events = [
                event for event in self.audit_events
                if datetime.fromisoformat(event['timestamp']) > cutoff_time
            ]
        
        # Categorize events
        by_type = defaultdict(int)
        by_user = defaultdict(int)
        failed_events = []
        
        for event in recent_events:
            by_type[event['event_type']] += 1
            if event.get('user_id'):
                by_user[event['user_id']] += 1
            if not event.get('success', True):
                failed_events.append(event)
        
        return {
            'report_period_hours': hours,
            'total_events': len(recent_events),
            'events_by_type': dict(by_type),
            'events_by_user': dict(by_user),
            'failed_events_count': len(failed_events),
            'failed_events': failed_events[-10:] if failed_events else [],
            'generated_at': datetime.utcnow().isoformat()
        }

class ProductionMonitoring:
    """Main production monitoring system"""
    
    def __init__(self):
        self.logger = ProductionLogger('production_monitoring')
        self.metrics = MetricsCollector()
        self.compliance = ComplianceLogger()
        
        # Health check metrics
        self.last_health_check = time.time()
        self.health_status = 'healthy'
        
        self.logger.info("Production monitoring system initialized")
    
    def timed_operation(self, operation_name: str):
        """Decorator for timing operations"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                error = False
                
                with self.logger.correlation_context():
                    try:
                        result = await func(*args, **kwargs)
                        self.logger.info(f"Operation completed: {operation_name}")
                        return result
                    except Exception as e:
                        error = True
                        self.logger.error(f"Operation failed: {operation_name}", exception=str(e))
                        raise
                    finally:
                        duration = time.time() - start_time
                        self.metrics.record_metric(operation_name, duration, error=error)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                error = False
                
                with self.logger.correlation_context():
                    try:
                        result = func(*args, **kwargs)
                        self.logger.info(f"Operation completed: {operation_name}")
                        return result
                    except Exception as e:
                        error = True
                        self.logger.error(f"Operation failed: {operation_name}", exception=str(e))
                        raise
                    finally:
                        duration = time.time() - start_time
                        self.metrics.record_metric(operation_name, duration, error=error)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive system health check"""
        start_time = time.time()
        
        try:
            metrics_summary = self.metrics.get_metrics_summary()
            compliance_summary = self.compliance.get_compliance_report(hours=1)
            
            # Determine overall health
            health_status = 'healthy'
            if metrics_summary['system_health'] in ['degraded', 'critical']:
                health_status = metrics_summary['system_health']
            
            response_time_ms = (time.time() - start_time) * 1000
            
            health_report = {
                'status': health_status,
                'response_time_ms': round(response_time_ms, 2),
                'timestamp': datetime.utcnow().isoformat(),
                'metrics_summary': metrics_summary,
                'compliance_summary': {
                    'events_last_hour': compliance_summary['total_events'],
                    'failed_events': compliance_summary['failed_events_count']
                },
                'system_info': {
                    'uptime_hours': round((time.time() - self.last_health_check) / 3600, 2),
                    'monitoring_active': True
                }
            }
            
            self.last_health_check = time.time()
            self.health_status = health_status
            
            return health_report
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'critical',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Global monitoring instance
production_monitoring = ProductionMonitoring()