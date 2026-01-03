"""
Notification Integration Module

Integrates the intelligent notification system with the existing client portal
backend, providing seamless integration with real-time updates and enhanced
client communication capabilities.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from sqlalchemy.orm import Session
from dataclasses import asdict
import asyncio
import json

from .intelligent_notification_system import (
    IntelligentNotificationSystem, ComplexityLevel, TranslationContext
)
from .notification_enhancement import (
    NotificationEnhancementEngine, SentimentType, ClientPersonality
)
from .notification_manager import NotificationManager
from .realtime_manager import RealtimeManager
from .models import (
    ClientUser, ClientDocument, ClientMessage, ClientCase, ClientAppointment,
    ClientInvoice, NotificationType, NotificationPriority, DocumentType,
    MessageStatus, CaseStatus, AppointmentStatus, InvoiceStatus
)


class SmartNotificationDispatcher:
    """Central dispatcher for intelligent notifications across the client portal."""
    
    def __init__(
        self,
        db_session: Session,
        notification_manager: NotificationManager,
        realtime_manager: RealtimeManager,
        redis_client = None
    ):
        self.db = db_session
        self.notification_manager = notification_manager
        self.realtime_manager = realtime_manager
        self.redis_client = redis_client
        
        # Initialize intelligent systems
        self.intelligent_system = IntelligentNotificationSystem(db_session, notification_manager)
        self.enhancement_engine = NotificationEnhancementEngine(
            db_session, self.intelligent_system, notification_manager
        )
        
        # Event handlers for different portal events
        self.event_handlers = {
            'document_uploaded': self._handle_document_event,
            'document_shared': self._handle_document_event,
            'message_sent': self._handle_message_event,
            'case_status_changed': self._handle_case_status_event,
            'appointment_scheduled': self._handle_appointment_event,
            'appointment_confirmed': self._handle_appointment_event,
            'invoice_generated': self._handle_invoice_event,
            'payment_received': self._handle_payment_event,
            'payment_overdue': self._handle_payment_event,
            'deadline_approaching': self._handle_deadline_event,
            'settlement_offer': self._handle_settlement_event,
            'court_filing': self._handle_court_filing_event
        }
        
    async def dispatch_notification(
        self,
        event_type: str,
        client_id: int,
        event_data: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        send_immediately: bool = False
    ) -> Dict[str, Any]:
        """Dispatch an intelligent notification for a portal event."""
        
        try:
            # Get event handler
            handler = self.event_handlers.get(event_type)
            if not handler:
                return await self._handle_generic_event(event_type, client_id, event_data, priority)
            
            # Process the specific event
            result = await handler(client_id, event_data, priority)
            
            # Send immediately if requested or urgent
            if send_immediately or priority == NotificationPriority.URGENT:
                await self._send_immediate_notification(result)
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': f'Notification dispatch failed: {str(e)}'}
    
    async def _handle_document_event(
        self,
        client_id: int,
        event_data: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Handle document-related events."""
        
        document_title = event_data.get('document_title', 'Untitled Document')
        document_type = event_data.get('document_type', 'document')
        action = event_data.get('action', 'shared')
        case_context = event_data.get('case_context', {})
        
        return await self.intelligent_system.translate_legal_document_event(
            client_id=client_id,
            document_title=document_title,
            document_type=document_type,
            action=action,
            case_context=case_context
        )
    
    async def _handle_message_event(
        self,
        client_id: int,
        event_data: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Handle message-related events."""
        
        sender_type = event_data.get('sender_type', 'attorney')
        subject = event_data.get('subject', 'New Message')
        message_preview = event_data.get('message_preview', '')
        case_title = event_data.get('case_title')
        
        # Determine context and create appropriate notification
        if sender_type == 'attorney':
            title = "New Message from Your Legal Team"
            if case_title:
                message = f"You have a new message about your case '{case_title}': {subject}"
            else:
                message = f"You have a new message: {subject}"
            
            if message_preview:
                message += f"\n\nPreview: {message_preview[:100]}..."
            
            message += "\n\nYou can read and reply to this message through your client portal."
        
        return await self.enhancement_engine.create_enhanced_notification(
            client_id=client_id,
            event_type='message_received',
            original_data={
                'sender_type': sender_type,
                'subject': subject,
                'message_preview': message_preview,
                'case_title': case_title
            },
            context=TranslationContext.CASE_UPDATE,
            priority=priority
        )
    
    async def _handle_case_status_event(
        self,
        client_id: int,
        event_data: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Handle case status change events."""
        
        case_title = event_data.get('case_title', 'Your Case')
        old_status = event_data.get('old_status', 'unknown')
        new_status = event_data.get('new_status', 'updated')
        details = event_data.get('details', {})
        
        return await self.intelligent_system.translate_case_status_change(
            client_id=client_id,
            case_title=case_title,
            old_status=old_status,
            new_status=new_status,
            details=details
        )
    
    async def _handle_appointment_event(
        self,
        client_id: int,
        event_data: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Handle appointment-related events."""
        
        appointment_title = event_data.get('appointment_title', 'Legal Appointment')
        appointment_date = event_data.get('appointment_date')
        appointment_type = event_data.get('appointment_type', 'consultation')
        action = event_data.get('action', 'scheduled')
        location_info = event_data.get('location_info', {})
        
        # Parse appointment date
        if isinstance(appointment_date, str):
            try:
                appointment_date = datetime.fromisoformat(appointment_date.replace('Z', '+00:00'))
            except ValueError:
                appointment_date = None
        
        # Create user-friendly notification
        if action == 'scheduled':
            title = f"Appointment Scheduled: {appointment_title}"
            if appointment_date:
                date_str = appointment_date.strftime('%B %d, %Y at %I:%M %p')
                message = f"Your {appointment_type} has been scheduled for {date_str}."
            else:
                message = f"Your {appointment_type} has been scheduled."
            
            if location_info.get('location_type') == 'video':
                message += " This will be a video conference - we'll send you the meeting link."
            elif location_info.get('address'):
                message += f" Location: {location_info['address']}"
            else:
                message += " We'll confirm the location details with you soon."
            
            message += " We'll send you a reminder as the date approaches."
            
        elif action == 'confirmed':
            title = "Appointment Confirmed"
            message = f"Thank you for confirming your {appointment_type} appointment"
            if appointment_date:
                message += f" on {appointment_date.strftime('%B %d, %Y')}."
            else:
                message += "."
            message += " We look forward to meeting with you."
        
        else:
            title = f"Appointment {action.title()}"
            message = f"Your appointment has been {action}."
        
        return await self.enhancement_engine.create_enhanced_notification(
            client_id=client_id,
            event_type=f'appointment_{action}',
            original_data=event_data,
            context=TranslationContext.APPOINTMENT_SCHEDULING,
            priority=priority
        )
    
    async def _handle_invoice_event(
        self,
        client_id: int,
        event_data: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Handle billing and invoice events."""
        
        amount = event_data.get('amount', 0.0)
        description = event_data.get('description', '')
        event_type = event_data.get('event_type', 'invoice_generated')
        due_date = event_data.get('due_date')
        
        return await self.intelligent_system.translate_billing_event(
            client_id=client_id,
            event_type=event_type,
            amount=amount,
            description=description,
            invoice_data=event_data
        )
    
    async def _handle_payment_event(
        self,
        client_id: int,
        event_data: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Handle payment-related events."""
        
        return await self._handle_invoice_event(client_id, event_data, priority)
    
    async def _handle_deadline_event(
        self,
        client_id: int,
        event_data: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Handle deadline and court date reminders."""
        
        deadline_type = event_data.get('deadline_type', 'deadline')
        deadline_date = event_data.get('deadline_date')
        case_title = event_data.get('case_title', 'Your Case')
        requirements = event_data.get('requirements', [])
        
        # Parse deadline date
        if isinstance(deadline_date, str):
            try:
                deadline_date = datetime.fromisoformat(deadline_date.replace('Z', '+00:00'))
            except ValueError:
                deadline_date = datetime.utcnow() + timedelta(days=7)
        
        return await self.intelligent_system.translate_court_deadline(
            client_id=client_id,
            deadline_type=deadline_type,
            deadline_date=deadline_date,
            case_title=case_title,
            requirements=requirements
        )
    
    async def _handle_settlement_event(
        self,
        client_id: int,
        event_data: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Handle settlement offer events."""
        
        offer_amount = event_data.get('offer_amount', 0.0)
        deadline = event_data.get('deadline')
        case_title = event_data.get('case_title', 'Your Case')
        our_recommendation = event_data.get('recommendation', 'under_review')
        
        # Parse deadline
        if isinstance(deadline, str):
            try:
                deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            except ValueError:
                deadline = datetime.utcnow() + timedelta(days=14)
        
        return await self.intelligent_system.translate_settlement_offer(
            client_id=client_id,
            offer_amount=offer_amount,
            deadline=deadline,
            case_title=case_title,
            our_recommendation=our_recommendation
        )
    
    async def _handle_court_filing_event(
        self,
        client_id: int,
        event_data: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Handle court filing events."""
        
        filing_type = event_data.get('filing_type', 'court_document')
        document_title = event_data.get('document_title', 'Court Filing')
        case_title = event_data.get('case_title', 'Your Case')
        filing_purpose = event_data.get('purpose', '')
        
        # Translate court filing into plain English
        title = "New Court Filing in Your Case"
        
        filing_translations = {
            'motion': 'formal request to the judge',
            'brief': 'legal argument document',
            'pleading': 'court document',
            'response': 'response to the other side',
            'reply': 'follow-up response',
            'discovery': 'information request'
        }
        
        filing_plain = filing_translations.get(filing_type.lower(), filing_type.replace('_', ' '))
        
        message = f"We've filed a {filing_plain} with the court for your case '{case_title}'."
        
        if filing_purpose:
            message += f" This {filing_plain} {filing_purpose}."
        
        message += " This is part of the normal legal process, and we'll keep you updated on any response from the court or the other side."
        
        return await self.enhancement_engine.create_enhanced_notification(
            client_id=client_id,
            event_type='court_filing',
            original_data=event_data,
            context=TranslationContext.COURT_FILING,
            priority=priority
        )
    
    async def _handle_generic_event(
        self,
        event_type: str,
        client_id: int,
        event_data: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Handle generic events that don't have specific handlers."""
        
        title = event_data.get('title', f'{event_type.replace("_", " ").title()} Update')
        message = event_data.get('message', 'There has been an update to your case.')
        
        return await self.enhancement_engine.create_enhanced_notification(
            client_id=client_id,
            event_type=event_type,
            original_data=event_data,
            context=TranslationContext.CASE_UPDATE,
            priority=priority
        )
    
    async def _send_immediate_notification(self, notification_result: Dict[str, Any]):
        """Send notification immediately through all appropriate channels."""
        
        if not notification_result.get('success'):
            return
        
        enhanced = notification_result.get('enhanced_notification')
        delivery_plan = notification_result.get('delivery_plan', {})
        channel_content = notification_result.get('channel_content', {})
        
        if not enhanced:
            return
        
        # Send through real-time manager
        if self.realtime_manager:
            await self.realtime_manager.send_notification(
                client_id=enhanced.base_notification.get('client_id'),
                notification_type=NotificationType.SYSTEM_ALERT,  # Will be mapped appropriately
                title=enhanced.personalized_content.get('portal', {}).get('title', ''),
                message=enhanced.personalized_content.get('portal', {}).get('message', ''),
                priority=NotificationPriority.HIGH,
                data=enhanced.base_notification
            )
    
    # Integration methods for portal events
    
    async def on_document_upload(
        self,
        client_id: int,
        document: ClientDocument,
        uploaded_by: str
    ):
        """Handle document upload event."""
        
        await self.dispatch_notification(
            event_type='document_uploaded',
            client_id=client_id,
            event_data={
                'document_title': document.original_filename,
                'document_type': document.document_type.value if document.document_type else 'document',
                'action': 'uploaded',
                'uploaded_by': uploaded_by,
                'case_context': {'case_id': document.case_id} if document.case_id else None
            },
            priority=NotificationPriority.MEDIUM
        )
    
    async def on_message_received(
        self,
        client_id: int,
        message: ClientMessage,
        sender_type: str = 'attorney'
    ):
        """Handle new message received event."""
        
        await self.dispatch_notification(
            event_type='message_sent',
            client_id=client_id,
            event_data={
                'sender_type': sender_type,
                'subject': message.subject,
                'message_preview': message.content[:100] if message.content else '',
                'case_title': message.case.title if message.case else None
            },
            priority=NotificationPriority.HIGH,
            send_immediately=True
        )
    
    async def on_case_status_change(
        self,
        client_id: int,
        case: ClientCase,
        old_status: str,
        new_status: str
    ):
        """Handle case status change event."""
        
        await self.dispatch_notification(
            event_type='case_status_changed',
            client_id=client_id,
            event_data={
                'case_title': case.title,
                'old_status': old_status,
                'new_status': new_status,
                'case_type': case.case_type,
                'progress_percentage': case.progress_percentage
            },
            priority=NotificationPriority.HIGH
        )
    
    async def on_appointment_scheduled(
        self,
        client_id: int,
        appointment: ClientAppointment
    ):
        """Handle appointment scheduled event."""
        
        await self.dispatch_notification(
            event_type='appointment_scheduled',
            client_id=client_id,
            event_data={
                'appointment_title': appointment.title,
                'appointment_date': appointment.scheduled_start.isoformat() if appointment.scheduled_start else None,
                'appointment_type': appointment.appointment_type,
                'action': 'scheduled',
                'location_info': {
                    'location_type': appointment.location_type,
                    'address': appointment.location_address,
                    'meeting_url': appointment.meeting_url
                }
            },
            priority=NotificationPriority.MEDIUM
        )
    
    async def on_invoice_generated(
        self,
        client_id: int,
        invoice: ClientInvoice
    ):
        """Handle invoice generated event."""
        
        await self.dispatch_notification(
            event_type='invoice_generated',
            client_id=client_id,
            event_data={
                'event_type': 'invoice_generated',
                'amount': float(invoice.total_amount) if invoice.total_amount else 0.0,
                'description': invoice.description or f'Invoice {invoice.invoice_number}',
                'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                'invoice_number': invoice.invoice_number
            },
            priority=NotificationPriority.MEDIUM
        )
    
    async def on_payment_overdue(
        self,
        client_id: int,
        invoice: ClientInvoice,
        days_overdue: int
    ):
        """Handle payment overdue event."""
        
        priority = NotificationPriority.HIGH if days_overdue > 30 else NotificationPriority.MEDIUM
        
        await self.dispatch_notification(
            event_type='payment_overdue',
            client_id=client_id,
            event_data={
                'event_type': 'payment_overdue',
                'amount': float(invoice.total_amount) if invoice.total_amount else 0.0,
                'description': f'Payment overdue by {days_overdue} days',
                'invoice_number': invoice.invoice_number,
                'days_overdue': days_overdue
            },
            priority=priority
        )
    
    async def on_settlement_offer_received(
        self,
        client_id: int,
        case: ClientCase,
        offer_amount: float,
        deadline: datetime,
        recommendation: str = 'under_review'
    ):
        """Handle settlement offer received event."""
        
        await self.dispatch_notification(
            event_type='settlement_offer',
            client_id=client_id,
            event_data={
                'offer_amount': offer_amount,
                'deadline': deadline.isoformat(),
                'case_title': case.title,
                'recommendation': recommendation
            },
            priority=NotificationPriority.URGENT,
            send_immediately=True
        )
    
    async def schedule_deadline_reminders(
        self,
        client_id: int,
        deadline_type: str,
        deadline_date: datetime,
        case_title: str,
        requirements: List[str] = None
    ):
        """Schedule deadline reminder notifications."""
        
        # Calculate reminder times (7 days, 3 days, 1 day before)
        reminder_intervals = [7, 3, 1]
        
        for days_before in reminder_intervals:
            reminder_time = deadline_date - timedelta(days=days_before)
            
            if reminder_time > datetime.utcnow():
                # In a production system, you'd schedule this with a task queue
                await self.dispatch_notification(
                    event_type='deadline_approaching',
                    client_id=client_id,
                    event_data={
                        'deadline_type': deadline_type,
                        'deadline_date': deadline_date.isoformat(),
                        'case_title': case_title,
                        'requirements': requirements or [],
                        'days_until': days_before
                    },
                    priority=NotificationPriority.HIGH if days_before <= 1 else NotificationPriority.MEDIUM
                )


class NotificationIntegrationManager:
    """Manages integration between intelligent notifications and portal events."""
    
    def __init__(
        self,
        db_session: Session,
        notification_manager: NotificationManager,
        realtime_manager: RealtimeManager,
        redis_client = None
    ):
        self.dispatcher = SmartNotificationDispatcher(
            db_session, notification_manager, realtime_manager, redis_client
        )
        
        # Auto-register for portal events
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Set up automatic event listeners for portal events."""
        
        # This would integrate with your existing portal event system
        # For example, using SQLAlchemy events or a message queue
        
        pass
    
    async def handle_bulk_notifications(
        self,
        notifications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle multiple notifications efficiently."""
        
        results = []
        
        for notification in notifications:
            result = await self.dispatcher.dispatch_notification(
                event_type=notification['event_type'],
                client_id=notification['client_id'],
                event_data=notification['event_data'],
                priority=notification.get('priority', NotificationPriority.MEDIUM),
                send_immediately=notification.get('send_immediately', False)
            )
            results.append(result)
        
        return {
            'success': True,
            'processed': len(results),
            'results': results
        }
    
    async def get_notification_analytics(
        self,
        client_id: Optional[int] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get analytics on notification effectiveness."""
        
        # This would analyze notification delivery rates, read rates, etc.
        # Placeholder for comprehensive analytics
        
        return {
            'success': True,
            'analytics': {
                'total_sent': 0,
                'delivery_rate': 0.0,
                'read_rate': 0.0,
                'action_rate': 0.0,
                'sentiment_breakdown': {},
                'channel_effectiveness': {},
                'optimal_timing': {}
            }
        }
    
    def get_dispatcher(self) -> SmartNotificationDispatcher:
        """Get the notification dispatcher for direct use."""
        return self.dispatcher