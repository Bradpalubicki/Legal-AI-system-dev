#!/usr/bin/env python3
"""
Input Validation Module
Legal AI System - Comprehensive Input Sanitization and Validation

This module provides security-focused input validation to prevent:
- SQL injection attacks
- XSS (Cross-Site Scripting) attacks
- Command injection
- Path traversal attacks
- Invalid data types and formats
"""

import re
import html
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import pydantic
from pydantic import BaseModel, Field, validator

# Setup logging
logger = logging.getLogger('input_validation')

class ValidationResult(str, Enum):
    """Validation result status"""
    VALID = "valid"
    INVALID = "invalid"
    SANITIZED = "sanitized"
    BLOCKED = "blocked"

@dataclass
class ValidationReport:
    """Validation result report"""
    status: ValidationResult
    original_value: Any
    sanitized_value: Any
    issues: List[str]
    risk_level: str  # low, medium, high, critical

class InputValidator:
    """
    Comprehensive input validation and sanitization system
    Provides protection against common security vulnerabilities
    """

    def __init__(self):
        self.logger = logger

        # SQL injection patterns
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(--|#|/\*|\*/)",
            r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT)\b)",
            r"('|\"|;|\\)"
        ]

        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>"
        ]

        # Command injection patterns
        self.command_injection_patterns = [
            r"[;&|`$]",
            r"\b(rm|del|format|fdisk|dd)\b",
            r"\.\./",
            r"~/"
        ]

        # Path traversal patterns
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"/etc/",
            r"\\windows\\",
            r"/proc/",
            r"/sys/"
        ]

    def validate_string(self, value: str, max_length: int = 1000,
                       allow_html: bool = False) -> ValidationReport:
        """Validate and sanitize string input"""
        issues = []
        risk_level = "low"
        original_value = value
        sanitized_value = value

        try:
            # Check for SQL injection
            if self._contains_sql_injection(value):
                issues.append("Potential SQL injection detected")
                risk_level = "critical"
                sanitized_value = self._sanitize_sql(value)

            # Check for XSS
            if self._contains_xss(value):
                issues.append("Potential XSS detected")
                if risk_level != "critical":
                    risk_level = "high"
                sanitized_value = self._sanitize_xss(sanitized_value)

            # Check for command injection
            if self._contains_command_injection(value):
                issues.append("Potential command injection detected")
                risk_level = "critical"
                sanitized_value = self._sanitize_commands(sanitized_value)

            # Check length
            if len(value) > max_length:
                issues.append(f"Input exceeds maximum length ({max_length})")
                sanitized_value = sanitized_value[:max_length]
                if risk_level == "low":
                    risk_level = "medium"

            # HTML sanitization
            if not allow_html:
                sanitized_value = html.escape(sanitized_value)

            # Determine status
            if issues and risk_level in ["critical", "high"]:
                status = ValidationResult.BLOCKED
            elif sanitized_value != original_value:
                status = ValidationResult.SANITIZED
            elif issues:
                status = ValidationResult.INVALID
            else:
                status = ValidationResult.VALID

            return ValidationReport(
                status=status,
                original_value=original_value,
                sanitized_value=sanitized_value,
                issues=issues,
                risk_level=risk_level
            )

        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return ValidationReport(
                status=ValidationResult.BLOCKED,
                original_value=original_value,
                sanitized_value="",
                issues=[f"Validation error: {e}"],
                risk_level="critical"
            )

    def validate_email(self, email: str) -> ValidationReport:
        """Validate email address format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if re.match(email_pattern, email):
            return ValidationReport(
                status=ValidationResult.VALID,
                original_value=email,
                sanitized_value=email.lower().strip(),
                issues=[],
                risk_level="low"
            )
        else:
            return ValidationReport(
                status=ValidationResult.INVALID,
                original_value=email,
                sanitized_value="",
                issues=["Invalid email format"],
                risk_level="medium"
            )

    def validate_file_path(self, path: str) -> ValidationReport:
        """Validate file path for security"""
        issues = []
        risk_level = "low"
        sanitized_path = path

        # Check for path traversal
        if self._contains_path_traversal(path):
            issues.append("Path traversal detected")
            risk_level = "critical"

        # Check for suspicious file extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js']
        if any(path.lower().endswith(ext) for ext in dangerous_extensions):
            issues.append("Dangerous file extension detected")
            risk_level = "high"

        # Normalize path
        sanitized_path = re.sub(r'[<>:"|?*]', '', path)
        sanitized_path = sanitized_path.replace('..', '')

        status = ValidationResult.BLOCKED if risk_level == "critical" else ValidationResult.VALID
        if sanitized_path != path:
            status = ValidationResult.SANITIZED

        return ValidationReport(
            status=status,
            original_value=path,
            sanitized_value=sanitized_path,
            issues=issues,
            risk_level=risk_level
        )

    def validate_integer(self, value: Any, min_val: int = None, max_val: int = None) -> ValidationReport:
        """Validate integer input"""
        try:
            int_value = int(value)
            issues = []
            risk_level = "low"

            if min_val is not None and int_value < min_val:
                issues.append(f"Value below minimum ({min_val})")
                risk_level = "medium"

            if max_val is not None and int_value > max_val:
                issues.append(f"Value above maximum ({max_val})")
                risk_level = "medium"

            status = ValidationResult.INVALID if issues else ValidationResult.VALID

            return ValidationReport(
                status=status,
                original_value=value,
                sanitized_value=int_value,
                issues=issues,
                risk_level=risk_level
            )

        except (ValueError, TypeError):
            return ValidationReport(
                status=ValidationResult.INVALID,
                original_value=value,
                sanitized_value=0,
                issues=["Invalid integer format"],
                risk_level="medium"
            )

    def _contains_sql_injection(self, value: str) -> bool:
        """Check for SQL injection patterns"""
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    def _contains_xss(self, value: str) -> bool:
        """Check for XSS patterns"""
        for pattern in self.xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    def _contains_command_injection(self, value: str) -> bool:
        """Check for command injection patterns"""
        for pattern in self.command_injection_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    def _contains_path_traversal(self, value: str) -> bool:
        """Check for path traversal patterns"""
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    def _sanitize_sql(self, value: str) -> str:
        """Sanitize SQL injection attempts"""
        # Remove SQL keywords and dangerous characters
        sanitized = re.sub(r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b', '', value, flags=re.IGNORECASE)
        sanitized = re.sub(r"[';\"\\]", '', sanitized)
        sanitized = re.sub(r"(--|#|/\*|\*/)", '', sanitized)
        return sanitized.strip()

    def _sanitize_xss(self, value: str) -> str:
        """Sanitize XSS attempts"""
        # Remove script tags and dangerous attributes
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
        return sanitized

    def _sanitize_commands(self, value: str) -> str:
        """Sanitize command injection attempts"""
        # Remove command injection characters
        sanitized = re.sub(r'[;&|`$]', '', value)
        sanitized = re.sub(r'\b(rm|del|format|fdisk|dd)\b', '', sanitized, flags=re.IGNORECASE)
        return sanitized

# Pydantic models for additional validation
class UserInputModel(BaseModel):
    """Pydantic model for user input validation"""
    username: str = Field(..., min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_-]+$')
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v and '-' not in v:
            raise ValueError('Username must be alphanumeric with optional underscores or hyphens')
        return v

class DocumentInputModel(BaseModel):
    """Pydantic model for document input validation"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., max_length=50000)
    file_type: str = Field(..., regex=r'^(pdf|docx?|txt|rtf)$')

    @validator('content')
    def validate_content(cls, v):
        validator = InputValidator()
        result = validator.validate_string(v, max_length=50000)
        if result.status == ValidationResult.BLOCKED:
            raise ValueError(f'Content validation failed: {", ".join(result.issues)}')
        return result.sanitized_value

# Global validator instance
input_validator = InputValidator()

def validate_input(value: Any, input_type: str = "string", **kwargs) -> ValidationReport:
    """Global input validation function"""
    if input_type == "string":
        return input_validator.validate_string(value, **kwargs)
    elif input_type == "email":
        return input_validator.validate_email(value)
    elif input_type == "file_path":
        return input_validator.validate_file_path(value)
    elif input_type == "integer":
        return input_validator.validate_integer(value, **kwargs)
    else:
        raise ValueError(f"Unknown input type: {input_type}")

def sanitize(value: str) -> str:
    """Quick sanitization function"""
    result = input_validator.validate_string(value)
    return result.sanitized_value

# Example usage and validation test
if __name__ == "__main__":
    # Test validation system
    validator = InputValidator()

    test_cases = [
        ("normal text", "string"),
        ("test@example.com", "email"),
        ("SELECT * FROM users", "string"),
        ("<script>alert('xss')</script>", "string"),
        ("../../../etc/passwd", "file_path"),
        ("123", "integer")
    ]

    print("Input Validation Test Results:")
    print("=" * 50)

    for test_value, test_type in test_cases:
        result = validate_input(test_value, test_type)
        print(f"Input: {test_value}")
        print(f"Type: {test_type}")
        print(f"Status: {result.status.value}")
        print(f"Risk: {result.risk_level}")
        if result.issues:
            print(f"Issues: {', '.join(result.issues)}")
        print(f"Sanitized: {result.sanitized_value}")
        print("-" * 30)