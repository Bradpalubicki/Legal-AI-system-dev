"""
Secure Logging Utilities
Sanitizes sensitive data from logs to prevent credential exposure
"""

import re
import logging
from typing import Any, Dict, Optional
from functools import wraps


# Patterns for sensitive data
SENSITIVE_PATTERNS = {
    'api_key': re.compile(r'(sk-[a-zA-Z0-9_-]{20,}|[a-zA-Z0-9]{32,})', re.IGNORECASE),
    'password': re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE),
    'token': re.compile(r'(Bearer\s+[a-zA-Z0-9_\-\.]+|[a-zA-Z0-9]{64,})', re.IGNORECASE),
    'jwt': re.compile(r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'),
    'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
}

# Sensitive field names to redact
SENSITIVE_FIELDS = {
    'password', 'secret', 'api_key', 'apikey', 'token', 'authorization',
    'jwt', 'bearer', 'private_key', 'client_secret', 'access_token',
    'refresh_token', 'session_id', 'ssn', 'social_security_number',
    'credit_card', 'card_number', 'cvv', 'pin'
}


def sanitize_string(value: str, mask_char: str = '*', show_last: int = 4) -> str:
    """
    Sanitize a string by masking sensitive data.

    Args:
        value: String to sanitize
        mask_char: Character to use for masking
        show_last: Number of characters to show at the end (for debugging)

    Returns:
        Sanitized string
    """
    if not value or len(value) == 0:
        return value

    # For very long strings (likely API keys/tokens), show format but mask content
    if len(value) > 20:
        if show_last > 0 and len(value) > show_last:
            return f"{mask_char * 8}...{value[-show_last:]}"
        return f"{mask_char * 12}"

    # For shorter strings, mask most of it
    if len(value) > show_last:
        return f"{mask_char * (len(value) - show_last)}{value[-show_last:]}"

    return mask_char * len(value)


def sanitize_dict(data: Dict[str, Any], mask_char: str = '*') -> Dict[str, Any]:
    """
    Recursively sanitize sensitive fields in a dictionary.

    Args:
        data: Dictionary to sanitize
        mask_char: Character to use for masking

    Returns:
        Sanitized dictionary
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        # Check if key name is sensitive
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            if isinstance(value, str) and value:
                sanitized[key] = sanitize_string(value, mask_char)
            else:
                sanitized[key] = f"<{type(value).__name__} REDACTED>"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, mask_char)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item, mask_char) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def sanitize_log_message(message: str) -> str:
    """
    Sanitize a log message by replacing sensitive patterns.

    Args:
        message: Log message to sanitize

    Returns:
        Sanitized log message
    """
    sanitized = message

    # Replace sensitive patterns
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        if pattern_name == 'email':
            # For emails, mask the local part but keep domain for debugging
            sanitized = pattern.sub(lambda m: f"***@{m.group(0).split('@')[1]}", sanitized)
        else:
            # For other sensitive data, replace with type indicator
            sanitized = pattern.sub(f"<{pattern_name.upper()}_REDACTED>", sanitized)

    return sanitized


class SecureLogger:
    """
    Secure logger wrapper that automatically sanitizes sensitive data.

    Usage:
        secure_logger = SecureLogger(__name__)
        secure_logger.info("User logged in", {"email": "user@example.com", "password": "secret"})
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _sanitize_args(self, *args, **kwargs):
        """Sanitize all arguments before logging."""
        sanitized_args = []
        for arg in args:
            if isinstance(arg, str):
                sanitized_args.append(sanitize_log_message(arg))
            elif isinstance(arg, dict):
                sanitized_args.append(sanitize_dict(arg))
            else:
                sanitized_args.append(arg)

        sanitized_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                sanitized_kwargs[key] = sanitize_log_message(value)
            elif isinstance(value, dict):
                sanitized_kwargs[key] = sanitize_dict(value)
            else:
                sanitized_kwargs[key] = value

        return sanitized_args, sanitized_kwargs

    def debug(self, *args, **kwargs):
        sanitized_args, sanitized_kwargs = self._sanitize_args(*args, **kwargs)
        self.logger.debug(*sanitized_args, **sanitized_kwargs)

    def info(self, *args, **kwargs):
        sanitized_args, sanitized_kwargs = self._sanitize_args(*args, **kwargs)
        self.logger.info(*sanitized_args, **sanitized_kwargs)

    def warning(self, *args, **kwargs):
        sanitized_args, sanitized_kwargs = self._sanitize_args(*args, **kwargs)
        self.logger.warning(*sanitized_args, **sanitized_kwargs)

    def error(self, *args, **kwargs):
        sanitized_args, sanitized_kwargs = self._sanitize_args(*args, **kwargs)
        self.logger.error(*sanitized_args, **sanitized_kwargs)

    def critical(self, *args, **kwargs):
        sanitized_args, sanitized_kwargs = self._sanitize_args(*args, **kwargs)
        self.logger.critical(*sanitized_args, **sanitized_kwargs)


def secure_log_decorator(func):
    """
    Decorator to automatically sanitize function arguments in logs.

    Usage:
        @secure_log_decorator
        def process_user(email: str, password: str):
            logger.info(f"Processing user: {email} with password {password}")
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get logger for the function's module
        logger = logging.getLogger(func.__module__)

        # Sanitize args and kwargs for logging
        sanitized_args = []
        for arg in args:
            if isinstance(arg, str):
                sanitized_args.append(sanitize_log_message(arg))
            elif isinstance(arg, dict):
                sanitized_args.append(sanitize_dict(arg))
            else:
                sanitized_args.append(arg)

        sanitized_kwargs = {
            key: sanitize_log_message(value) if isinstance(value, str)
            else sanitize_dict(value) if isinstance(value, dict)
            else value
            for key, value in kwargs.items()
        }

        logger.debug(
            f"Calling {func.__name__} with args={sanitized_args}, kwargs={sanitized_kwargs}"
        )

        return func(*args, **kwargs)

    return wrapper


# Convenience function to get a secure logger
def get_secure_logger(name: str) -> SecureLogger:
    """
    Get a secure logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        SecureLogger instance
    """
    return SecureLogger(name)


# Example usage and tests
if __name__ == "__main__":
    # Test sanitization
    test_data = {
        "email": "user@example.com",
        "password": "super_secret_password",
        "api_key": "sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyz",
        "normal_field": "this is fine",
        "nested": {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc",
            "safe_data": "also fine"
        }
    }

    print("Original:", test_data)
    print("Sanitized:", sanitize_dict(test_data))

    # Test log message sanitization
    test_message = "User sk-ant-api03-abcdef logged in with password secret123"
    print("\nOriginal message:", test_message)
    print("Sanitized message:", sanitize_log_message(test_message))
