"""
Client Portal Backend System

A comprehensive client portal backend providing secure access to case information,
document sharing, real-time updates, and communication features for legal clients.

Main Components:
- Authentication & Authorization
- Document Management & Sharing  
- Real-time Updates & Notifications
- Secure Communication System
- Case Status & Progress Tracking
- Billing & Invoice Access
- Appointment Scheduling
- Audit Logging & Compliance
"""

from .models import (
    ClientUser,
    ClientSession, 
    ClientDocument,
    ClientMessage,
    ClientNotification,
    ClientCase,
    ClientInvoice,
    ClientAppointment,
    ClientAuditLog
)

from .auth_manager import ClientAuthManager
from .document_manager import ClientDocumentManager
from .communication_manager import CommunicationManager
from .notification_manager import NotificationManager
from .realtime_manager import RealtimeManager
from .case_manager import ClientCaseManager
from .billing_manager import ClientBillingManager
from .appointment_manager import ClientAppointmentManager
from .audit_manager import ClientAuditManager
from .portal_api import ClientPortalAPI
from .websocket_handler import ClientWebSocketHandler

__all__ = [
    # Models
    'ClientUser',
    'ClientSession',
    'ClientDocument', 
    'ClientMessage',
    'ClientNotification',
    'ClientCase',
    'ClientInvoice',
    'ClientAppointment',
    'ClientAuditLog',
    
    # Managers
    'ClientAuthManager',
    'ClientDocumentManager',
    'CommunicationManager', 
    'NotificationManager',
    'RealtimeManager',
    'ClientCaseManager',
    'ClientBillingManager',
    'ClientAppointmentManager',
    'ClientAuditManager',
    
    # API & WebSocket
    'ClientPortalAPI',
    'ClientWebSocketHandler'
]