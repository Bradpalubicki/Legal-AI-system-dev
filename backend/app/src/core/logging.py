"""
Logging Configuration for Legal AI System

Comprehensive logging setup with structured logging, multiple handlers,
and integration with FastAPI request/response cycle.
"""

import json
import logging
import logging.config
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import uuid

from pythonjsonlogger import jsonlogger

from .config import get_settings

settings = get_settings()


# =============================================================================
# CUSTOM LOG FORMATTERS
# =============================================================================

class CustomJSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add process and thread info
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread
        log_record['thread_name'] = record.threadName
        
        # Add application context
        log_record['application'] = 'legal-ai-system'
        log_record['environment'] = settings.ENVIRONMENT
        log_record['version'] = getattr(settings, 'APP_VERSION', '1.0.0')


class RequestFormatter(logging.Formatter):
    """Formatter for HTTP request/response logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Extract request context if available
        if hasattr(record, 'request_id'):
            record.request_id = record.request_id
        else:
            record.request_id = str(uuid.uuid4())[:8]
        
        return super().format(record)


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

def configure_logging():
    """Configure application logging"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.LOG_FILE_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Base logging configuration
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                '()': CustomJSONFormatter,
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
            },
            'request': {
                '()': RequestFormatter,
                'format': '[%(request_id)s] %(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': settings.LOG_LEVEL,
                'formatter': 'json' if settings.LOG_FORMAT == 'json' else 'standard',
                'stream': sys.stdout
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': settings.LOG_LEVEL,
                'formatter': 'json' if settings.LOG_FORMAT == 'json' else 'detailed',
                'filename': settings.LOG_FILE_PATH,
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 10,
                'encoding': 'utf8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json' if settings.LOG_FORMAT == 'json' else 'detailed',
                'filename': str(Path(settings.LOG_FILE_PATH).parent / 'error.log'),
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 5,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            '': {  # Root logger
                'level': settings.LOG_LEVEL,
                'handlers': ['console'],
                'propagate': False
            },
            'legal-ai-system': {
                'level': settings.LOG_LEVEL,
                'handlers': ['console', 'file', 'error_file'] if settings.LOG_FILE_ENABLED else ['console'],
                'propagate': False
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'fastapi': {
                'level': 'INFO',
                'handlers': ['console', 'file'] if settings.LOG_FILE_ENABLED else ['console'],
                'propagate': False
            },
            'sqlalchemy': {
                'level': 'WARNING',  # Reduce SQLAlchemy verbosity
                'handlers': ['console', 'file'] if settings.LOG_FILE_ENABLED else ['console'],
                'propagate': False
            },
            'celery': {
                'level': 'INFO',
                'handlers': ['console', 'file'] if settings.LOG_FILE_ENABLED else ['console'],
                'propagate': False
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Set up application logger
    logger = logging.getLogger('legal-ai-system')
    logger.info(f"Logging configured - Level: {settings.LOG_LEVEL}, Format: {settings.LOG_FORMAT}")
    
    return logger


# =============================================================================
# REQUEST CONTEXT LOGGER
# =============================================================================

class RequestContextLogger:
    """Logger with request context information"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.request_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.correlation_id: Optional[str] = None
    
    def set_context(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Set request context for logging"""
        self.request_id = request_id
        self.user_id = user_id
        self.session_id = session_id
        self.correlation_id = correlation_id
    
    def _add_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add context information to log record"""
        context = extra or {}
        
        if self.request_id:
            context['request_id'] = self.request_id
        if self.user_id:
            context['user_id'] = self.user_id
        if self.session_id:
            context['session_id'] = self.session_id
        if self.correlation_id:
            context['correlation_id'] = self.correlation_id
        
        return context
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.logger.debug(message, extra=self._add_context(extra))
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.logger.info(message, extra=self._add_context(extra))
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.logger.warning(message, extra=self._add_context(extra))
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        self.logger.error(message, extra=self._add_context(extra), exc_info=exc_info)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        self.logger.critical(message, extra=self._add_context(extra), exc_info=exc_info)


# =============================================================================
# SPECIALIZED LOGGERS
# =============================================================================

class AuditLogger:
    """Specialized logger for audit events"""
    
    def __init__(self):
        self.logger = logging.getLogger('legal-ai-system.audit')
        
        # Create audit log file handler if not exists
        if settings.LOG_FILE_ENABLED:
            audit_log_path = Path(settings.LOG_FILE_PATH).parent / 'audit.log'
            audit_handler = logging.handlers.RotatingFileHandler(
                audit_log_path,
                maxBytes=100 * 1024 * 1024,  # 100MB
                backupCount=20,
                encoding='utf8'
            )
            audit_handler.setFormatter(CustomJSONFormatter())
            self.logger.addHandler(audit_handler)
    
    def log_action(
        self,
        action: str,
        resource: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        """Log an audit action"""
        audit_data = {
            'audit_action': action,
            'audit_resource': resource,
            'audit_timestamp': datetime.now(timezone.utc).isoformat(),
            'audit_user_id': user_id,
            'audit_resource_id': resource_id,
            'audit_details': details or {},
            'request_id': request_id
        }
        
        self.logger.info(f"AUDIT: {action} on {resource}", extra=audit_data)


class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self):
        self.logger = logging.getLogger('legal-ai-system.security')
        
        # Create security log file handler if not exists
        if settings.LOG_FILE_ENABLED:
            security_log_path = Path(settings.LOG_FILE_PATH).parent / 'security.log'
            security_handler = logging.handlers.RotatingFileHandler(
                security_log_path,
                maxBytes=50 * 1024 * 1024,  # 50MB
                backupCount=10,
                encoding='utf8'
            )
            security_handler.setFormatter(CustomJSONFormatter())
            self.logger.addHandler(security_handler)
    
    def log_auth_attempt(
        self,
        username: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log authentication attempt"""
        security_data = {
            'security_event': 'auth_attempt',
            'username': username,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'details': details or {}
        }
        
        level = logging.INFO if success else logging.WARNING
        message = f"Authentication {'succeeded' if success else 'failed'} for user: {username}"
        self.logger.log(level, message, extra=security_data)
    
    def log_access_denied(
        self,
        user_id: str,
        resource: str,
        action: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log access denied event"""
        security_data = {
            'security_event': 'access_denied',
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'reason': reason,
            'details': details or {}
        }
        
        self.logger.warning(f"Access denied: {user_id} -> {action} on {resource}", extra=security_data)


class PerformanceLogger:
    """Specialized logger for performance metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger('legal-ai-system.performance')
    
    def log_request_metrics(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
        user_id: Optional[str] = None
    ):
        """Log request performance metrics"""
        metrics_data = {
            'performance_type': 'http_request',
            'http_method': method,
            'http_path': path,
            'http_status_code': status_code,
            'duration_ms': duration_ms,
            'request_size_bytes': request_size,
            'response_size_bytes': response_size,
            'user_id': user_id
        }
        
        # Log as warning if request is slow
        level = logging.WARNING if duration_ms > 5000 else logging.INFO
        self.logger.log(level, f"Request: {method} {path} - {duration_ms:.2f}ms", extra=metrics_data)
    
    def log_db_query_metrics(
        self,
        query_type: str,
        table: str,
        duration_ms: float,
        row_count: Optional[int] = None
    ):
        """Log database query performance metrics"""
        metrics_data = {
            'performance_type': 'db_query',
            'query_type': query_type,
            'table': table,
            'duration_ms': duration_ms,
            'row_count': row_count
        }
        
        # Log as warning if query is slow
        level = logging.WARNING if duration_ms > 1000 else logging.INFO
        self.logger.log(level, f"DB Query: {query_type} on {table} - {duration_ms:.2f}ms", extra=metrics_data)


# =============================================================================
# LOGGER FACTORY
# =============================================================================

def get_logger(name: str) -> RequestContextLogger:
    """Get a logger with request context support"""
    base_logger = logging.getLogger(f'legal-ai-system.{name}')
    return RequestContextLogger(base_logger)


# =============================================================================
# GLOBAL LOGGER INSTANCES
# =============================================================================

# Initialize logging on module import
configure_logging()

# Create global logger instances
audit_logger = AuditLogger()
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()

# Main application logger
app_logger = get_logger('app')


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'configure_logging',
    'get_logger',
    'RequestContextLogger',
    'AuditLogger',
    'SecurityLogger',
    'PerformanceLogger',
    'audit_logger',
    'security_logger',
    'performance_logger',
    'app_logger'
]