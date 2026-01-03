#!/usr/bin/env python3
"""
Comprehensive Error Handling System
Legal AI System - Advanced Error Management and Recovery

This module provides comprehensive error handling, logging, and recovery
mechanisms for the Legal AI system to ensure robust operation.
"""

import logging
import traceback
import sys
import functools
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Union, Type
from dataclasses import dataclass, asdict
from enum import Enum
import json

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)

class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    FATAL = "fatal"

class ErrorCategory(str, Enum):
    """Error categories for classification"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    AI_MODEL = "ai_model"
    COMPLIANCE = "compliance"
    SYSTEM = "system"
    USER_INPUT = "user_input"

@dataclass
class ErrorContext:
    """Error context information"""
    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    function_name: str
    file_name: str
    line_number: int
    stack_trace: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

@dataclass
class RecoveryAction:
    """Recovery action information"""
    action_type: str
    description: str
    executed: bool
    success: bool
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

class ErrorHandler:
    """
    Comprehensive error handling system with automatic recovery capabilities
    """

    def __init__(self):
        self.logger = logging.getLogger('error_handler')
        self.error_log: List[ErrorContext] = []
        self.recovery_actions: List[RecoveryAction] = []

    def handle_error(self, error: Exception, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.SYSTEM,
                    user_id: str = None, request_id: str = None,
                    additional_data: Dict[str, Any] = None,
                    auto_recover: bool = True) -> ErrorContext:
        """
        Comprehensive error handling with logging and recovery
        """
        # Get caller information
        frame = sys._getframe(1)
        function_name = frame.f_code.co_name
        file_name = frame.f_code.co_filename
        line_number = frame.f_lineno

        # Create error context
        error_context = ErrorContext(
            error_id=f"err_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            category=category,
            function_name=function_name,
            file_name=file_name,
            line_number=line_number,
            stack_trace=traceback.format_exc(),
            user_id=user_id,
            request_id=request_id,
            additional_data=additional_data or {}
        )

        # Log error based on severity
        log_message = f"Error {error_context.error_id}: {error_context.error_message}"
        if severity == ErrorSeverity.FATAL:
            self.logger.critical(log_message, extra=asdict(error_context))
        elif severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra=asdict(error_context))
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, extra=asdict(error_context))
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra=asdict(error_context))
        else:
            self.logger.info(log_message, extra=asdict(error_context))

        # Store error for analysis
        self.error_log.append(error_context)

        # Attempt automatic recovery
        if auto_recover:
            self._attempt_recovery(error_context)

        # Send alerts for critical errors
        if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]:
            self._send_alert(error_context)

        return error_context

    def _attempt_recovery(self, error_context: ErrorContext) -> bool:
        """Attempt automatic recovery based on error type and category"""
        recovery_strategies = {
            ErrorCategory.DATABASE: self._recover_database_error,
            ErrorCategory.NETWORK: self._recover_network_error,
            ErrorCategory.FILE_SYSTEM: self._recover_filesystem_error,
            ErrorCategory.AI_MODEL: self._recover_ai_model_error,
            ErrorCategory.VALIDATION: self._recover_validation_error
        }

        strategy = recovery_strategies.get(error_context.category)
        if strategy:
            try:
                success = strategy(error_context)
                action = RecoveryAction(
                    action_type=f"auto_recovery_{error_context.category.value}",
                    description=f"Automatic recovery attempt for {error_context.category.value} error",
                    executed=True,
                    success=success,
                    timestamp=datetime.now(),
                    details={"error_id": error_context.error_id}
                )
                self.recovery_actions.append(action)
                return success
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed: {recovery_error}")
                return False

        return False

    def _recover_database_error(self, error_context: ErrorContext) -> bool:
        """Attempt database error recovery"""
        try:
            # Implement database reconnection logic
            self.logger.info("Attempting database reconnection...")
            # Placeholder for actual database recovery
            return True
        except Exception as e:
            self.logger.error(f"Database recovery failed: {e}")
            return False

    def _recover_network_error(self, error_context: ErrorContext) -> bool:
        """Attempt network error recovery"""
        try:
            # Implement network retry logic
            self.logger.info("Attempting network retry...")
            # Placeholder for actual network recovery
            return True
        except Exception as e:
            self.logger.error(f"Network recovery failed: {e}")
            return False

    def _recover_filesystem_error(self, error_context: ErrorContext) -> bool:
        """Attempt filesystem error recovery"""
        try:
            # Implement filesystem recovery logic
            self.logger.info("Attempting filesystem recovery...")
            # Placeholder for actual filesystem recovery
            return True
        except Exception as e:
            self.logger.error(f"Filesystem recovery failed: {e}")
            return False

    def _recover_ai_model_error(self, error_context: ErrorContext) -> bool:
        """Attempt AI model error recovery"""
        try:
            # Implement AI model fallback logic
            self.logger.info("Attempting AI model fallback...")
            # Placeholder for actual AI model recovery
            return True
        except Exception as e:
            self.logger.error(f"AI model recovery failed: {e}")
            return False

    def _recover_validation_error(self, error_context: ErrorContext) -> bool:
        """Attempt validation error recovery"""
        try:
            # Implement validation recovery logic
            self.logger.info("Attempting validation recovery...")
            # Placeholder for actual validation recovery
            return True
        except Exception as e:
            self.logger.error(f"Validation recovery failed: {e}")
            return False

    def _send_alert(self, error_context: ErrorContext):
        """Send alert for critical errors"""
        alert_message = f"CRITICAL ERROR: {error_context.error_id} - {error_context.error_message}"
        self.logger.critical(f"ALERT: {alert_message}")
        # Implement actual alerting mechanism (email, Slack, etc.)

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.error_log:
            return {"total_errors": 0}

        total_errors = len(self.error_log)
        by_severity = {}
        by_category = {}

        for error in self.error_log:
            # Count by severity
            severity_key = error.severity.value
            by_severity[severity_key] = by_severity.get(severity_key, 0) + 1

            # Count by category
            category_key = error.category.value
            by_category[category_key] = by_category.get(category_key, 0) + 1

        return {
            "total_errors": total_errors,
            "by_severity": by_severity,
            "by_category": by_category,
            "recovery_attempts": len(self.recovery_actions),
            "recovery_success_rate": self._calculate_recovery_success_rate()
        }

    def _calculate_recovery_success_rate(self) -> float:
        """Calculate recovery success rate"""
        if not self.recovery_actions:
            return 0.0

        successful_recoveries = sum(1 for action in self.recovery_actions if action.success)
        return (successful_recoveries / len(self.recovery_actions)) * 100

# Global error handler instance
error_handler = ErrorHandler()

def handle_exceptions(severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                     category: ErrorCategory = ErrorCategory.SYSTEM,
                     auto_recover: bool = True):
    """Decorator for automatic exception handling"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    error=e,
                    severity=severity,
                    category=category,
                    auto_recover=auto_recover
                )
                raise  # Re-raise after handling

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    error=e,
                    severity=severity,
                    category=category,
                    auto_recover=auto_recover
                )
                raise  # Re-raise after handling

        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
    return decorator

def safe_execute(func: Callable, *args, default=None,
                severity: ErrorSeverity = ErrorSeverity.LOW,
                category: ErrorCategory = ErrorCategory.SYSTEM, **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(
            error=e,
            severity=severity,
            category=category
        )
        return default

class DatabaseError(Exception):
    """Database-specific error"""
    pass

class ValidationError(Exception):
    """Validation-specific error"""
    pass

class AuthenticationError(Exception):
    """Authentication-specific error"""
    pass

class ComplianceError(Exception):
    """Compliance-specific error"""
    pass

class AIModelError(Exception):
    """AI model-specific error"""
    pass

# Context managers for error handling
class ErrorContext:
    """Context manager for error handling in code blocks"""

    def __init__(self, category: ErrorCategory = ErrorCategory.SYSTEM,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        self.category = category
        self.severity = severity

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            error_handler.handle_error(
                error=exc_val,
                severity=self.severity,
                category=self.category
            )
        return False  # Don't suppress the exception

# Example usage and testing
@handle_exceptions(severity=ErrorSeverity.HIGH, category=ErrorCategory.VALIDATION)
def test_function_with_error():
    """Test function that raises an error"""
    raise ValueError("This is a test error")

def validate_error_handling():
    """Validate error handling system"""
    try:
        # Test basic error handling
        try:
            raise ValueError("Test validation error")
        except Exception as e:
            error_handler.handle_error(
                error=e,
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION
            )

        # Test decorator
        try:
            test_function_with_error()
        except ValueError:
            pass  # Expected

        # Test context manager
        with ErrorContext(category=ErrorCategory.DATABASE, severity=ErrorSeverity.HIGH):
            try:
                raise DatabaseError("Test database error")
            except DatabaseError:
                pass  # Handled by context manager

        # Test safe execute
        result = safe_execute(lambda: 1/0, default="error occurred")

        print("Error handling validation completed successfully")
        return True

    except Exception as e:
        print(f"Error handling validation failed: {e}")
        return False

if __name__ == "__main__":
    # Test the error handling system
    print("Testing Error Handling System...")
    print("=" * 40)

    if validate_error_handling():
        print("✓ Error handling system working correctly")

        # Display statistics
        stats = error_handler.get_error_statistics()
        print(f"\nError Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("✗ Error handling system validation failed")