"""
Model imports - order matters for SQLAlchemy relationship resolution
Import order: learning (AIFeedback) BEFORE legal_documents (Document)
Billing and case_access models must be imported for User relationship resolution
"""

# Only import the models we need, in the correct order
# AIFeedback MUST be imported before Document due to relationship dependency
from .learning import AIFeedback, DocumentKnowledge
from .legal_documents import Document, QASession, QAMessage, DefenseSession
from .case_notification_history import CaseNotification

# Billing models must be imported for User relationships
from .billing import (
    Subscription, 
    BillingPlan, 
    Invoice, 
    Payment, 
    Usage, 
    PaymentMethod,
    RefundRequest,
    BillingEvent,
    PromoCode,
    TaxRate
)

# Case access models for User relationship
from .case_access import CaseAccess, CaseAccessPurchase

__all__ = [
    # Learning system (must be first due to relationships)
    'AIFeedback',
    'DocumentKnowledge',
    # Legal documents
    'Document',
    'QASession',
    'QAMessage',
    'DefenseSession',
    # Notifications
    'CaseNotification',
    # Billing
    'Subscription',
    'BillingPlan',
    'Invoice',
    'Payment',
    'Usage',
    'PaymentMethod',
    'RefundRequest',
    'BillingEvent',
    'PromoCode',
    'TaxRate',
    # Case access
    'CaseAccess',
    'CaseAccessPurchase',
]
