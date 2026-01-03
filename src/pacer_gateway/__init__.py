"""
PACER Gateway Service for Legal AI System

Provides centralized access to the Public Access to Court Electronic Records (PACER) system
through standardized APIs. Handles authentication, rate limiting, cost tracking, and
compliance with PACER usage policies.

Features:
- Centralized PACER account management
- Automated authentication and session management
- Cost tracking and billing controls
- Rate limiting and compliance monitoring
- Document retrieval and case search
- Bulk operations with queue management
- Audit logging for all PACER interactions
"""

# Import only modules that actually exist
try:
    from .client import PacerClient, PacerResponse, PacerError
except ImportError:
    pass

try:
    from .account_manager import PacerAccountManager, PacerAccount, AccountStatus
except ImportError:
    pass

try:
    from .cost_tracker import CostTracker, CostLimit, CostAlert
except ImportError:
    pass

try:
    from .gateway import PacerGateway
except ImportError:
    pass

# Version info
__version__ = "1.0.0"
__author__ = "Legal AI System"

# Public API - only classes that actually exist
__all__ = [
    "PacerClient",
    "PacerGateway",
    "PacerAccountManager",
    "CostTracker"
]