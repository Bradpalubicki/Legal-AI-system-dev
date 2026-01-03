# Simplified exceptions module

class LegalAIException(Exception):
    """Base exception for Legal AI System"""
    pass

class ValidationException(LegalAIException):
    """Validation error"""
    pass

class BusinessLogicException(LegalAIException):
    """Business logic error"""
    pass

class AuthenticationException(LegalAIException):
    """Authentication error"""
    pass

class AuthorizationException(LegalAIException):
    """Authorization error"""
    pass

class ResourceNotFoundException(LegalAIException):
    """Resource not found"""
    pass

class DuplicateResourceException(LegalAIException):
    """Duplicate resource"""
    pass

class DatabaseException(LegalAIException):
    """Database error"""
    pass

class ExternalServiceException(LegalAIException):
    """External service error"""
    pass

class PacerException(ExternalServiceException):
    """PACER service error"""
    pass

class AIServiceException(ExternalServiceException):
    """AI service error"""
    pass

class RateLimitException(LegalAIException):
    """Rate limit exceeded"""
    pass

class ConfigurationException(LegalAIException):
    """Configuration error"""
    pass

# Exception handlers for FastAPI
EXCEPTION_HANDLERS = {}

__all__ = [
    'LegalAIException',
    'ValidationException',
    'BusinessLogicException',
    'AuthenticationException',
    'AuthorizationException',
    'ResourceNotFoundException',
    'DuplicateResourceException',
    'DatabaseException',
    'ExternalServiceException',
    'PacerException',
    'AIServiceException',
    'RateLimitException',
    'ConfigurationException',
    'EXCEPTION_HANDLERS'
]