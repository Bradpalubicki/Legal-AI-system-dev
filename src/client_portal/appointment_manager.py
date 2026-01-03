"""
Client Portal Appointment Manager

Handles appointment scheduling, management, and client access to
appointment information with calendar integration capabilities.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import uuid
from icalendar import Calendar, Event
import pytz

from .models import (
    ClientAppointment, ClientUser, ClientCase, AppointmentStatus,
    ClientAuditLog, AuditAction
)
from .audit_manager import ClientAuditManager
from .notification_manager import NotificationManager
from .models import NotificationType, NotificationPriority


class ClientAppointmentManager:
    """Manages client appointment scheduling and access."""
    
    def __init__(self, db_session: Session, notification_manager: Optional[NotificationManager] = None):
        self.db = db_session
        self.audit_manager = ClientAuditManager(db_session)
        self.notification_manager = notification_manager
        
        # Default settings
        self.default_appointment_duration = timedelta(hours=1)
        self.reminder_intervals = [
            timedelta(days=7),   # 1 week before
            timedelta(days=1),   # 1 day before
            timedelta(hours=2)   # 2 hours before
        ]
    
    async def get_client_appointments(
        self,
        client_id: int,
        status: Optional[AppointmentStatus] = None,
        case_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get appointments for a client with filtering options."""
        try:
            # Validate client exists
            client = self.db.query(ClientUser).filter(ClientUser.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            # Build query
            query = self.db.query(ClientAppointment).filter(
                ClientAppointment.client_id == client_id
            )
            
            # Apply filters
            if status:
                query = query.filter(ClientAppointment.status == status)
            
            if case_id:
                query = query.filter(ClientAppointment.case_id == case_id)
            
            if date_from:
                query = query.filter(ClientAppointment.scheduled_start >= date_from)
            
            if date_to:
                query = query.filter(ClientAppointment.scheduled_end <= date_to)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            appointments = query.order_by(desc(ClientAppointment.scheduled_start)).offset(
                (page - 1) * limit
            ).limit(limit).all()
            
            # Enhance appointments with additional info
            appointment_dicts = []
            for appointment in appointments:
                apt_dict = self._appointment_to_dict(appointment)
                
                # Add case information if available
                if appointment.case_id:
                    case = self.db.query(ClientCase).filter(ClientCase.id == appointment.case_id).first()
                    if case:
                        apt_dict['case'] = {
                            'case_id': case.case_id,
                            'case_number': case.case_number,
                            'title': case.title
                        }
                
                # Add time until appointment
                if appointment.scheduled_start:
                    time_until = appointment.scheduled_start - datetime.utcnow()
                    apt_dict['time_until_hours'] = time_until.total_seconds() / 3600
                    apt_dict['is_upcoming'] = time_until.total_seconds() > 0
                
                appointment_dicts.append(apt_dict)
            
            return {
                'success': True,
                'appointments': appointment_dicts,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve appointments: {str(e)}'}
    
    async def get_appointment_details(
        self,
        appointment_id: str,
        client_id: int,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed information for a specific appointment."""
        try:
            # Get appointment with access validation
            appointment = self.db.query(ClientAppointment).filter(
                and_(
                    ClientAppointment.appointment_id == appointment_id,
                    ClientAppointment.client_id == client_id
                )
            ).first()
            
            if not appointment:
                return {'success': False, 'error': 'Appointment not found or access denied'}
            
            # Log access
            self.audit_manager.log_event(
                user_id=client_id,
                action=AuditAction.APPOINTMENT_SCHEDULED,
                resource_type='appointment',
                resource_id=appointment_id,
                ip_address=ip_address,
                action_details={
                    'appointment_title': appointment.title,
                    'scheduled_start': appointment.scheduled_start.isoformat() if appointment.scheduled_start else None
                }
            )
            
            appointment_dict = self._appointment_to_dict(appointment, include_details=True)
            
            # Add case information if available
            if appointment.case_id:
                case = self.db.query(ClientCase).filter(ClientCase.id == appointment.case_id).first()
                if case:
                    appointment_dict['case'] = {
                        'case_id': case.case_id,
                        'case_number': case.case_number,
                        'title': case.title,
                        'status': case.status.value if case.status else None
                    }
            
            # Add preparation information
            if appointment.scheduled_start:
                time_until = appointment.scheduled_start - datetime.utcnow()
                appointment_dict['preparation'] = {
                    'time_until_hours': time_until.total_seconds() / 3600,
                    'is_upcoming': time_until.total_seconds() > 0,
                    'reminder_sent': appointment.reminder_sent,
                    'requires_confirmation': appointment.confirmation_required and not appointment.confirmed_at
                }
            
            return {
                'success': True,
                'appointment': appointment_dict
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve appointment details: {str(e)}'}
    
    async def confirm_appointment(
        self,
        appointment_id: str,
        client_id: int,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Confirm an appointment."""
        try:
            # Get appointment with access validation
            appointment = self.db.query(ClientAppointment).filter(
                and_(
                    ClientAppointment.appointment_id == appointment_id,
                    ClientAppointment.client_id == client_id,
                    ClientAppointment.confirmation_required == True,
                    ClientAppointment.confirmed_at.is_(None)
                )
            ).first()
            
            if not appointment:
                return {'success': False, 'error': 'Appointment not found, already confirmed, or confirmation not required'}
            
            # Update confirmation
            appointment.confirmed_at = datetime.utcnow()
            appointment.status = AppointmentStatus.CONFIRMED
            
            # Log confirmation
            self.audit_manager.log_event(
                user_id=client_id,
                action=AuditAction.APPOINTMENT_SCHEDULED,
                resource_type='appointment',
                resource_id=appointment_id,
                ip_address=ip_address,
                action_details={
                    'action': 'confirmed',
                    'appointment_title': appointment.title
                }
            )
            
            self.db.commit()
            
            # Send confirmation notification to legal team
            if self.notification_manager:
                await self.notification_manager.create_notification(
                    client_id=client_id,
                    notification_type=NotificationType.APPOINTMENT_SCHEDULED,
                    title="Appointment Confirmed",
                    message=f"Appointment '{appointment.title}' has been confirmed for {appointment.scheduled_start.strftime('%Y-%m-%d %H:%M')}",
                    priority=NotificationPriority.MEDIUM,
                    related_entity_type='appointment',
                    related_entity_id=appointment_id
                )
            
            return {
                'success': True,
                'message': 'Appointment confirmed successfully',
                'appointment': self._appointment_to_dict(appointment)
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Failed to confirm appointment: {str(e)}'}
    
    async def request_reschedule(
        self,
        appointment_id: str,
        client_id: int,
        preferred_times: List[Dict[str, str]],
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Request to reschedule an appointment."""
        try:
            # Get appointment with access validation
            appointment = self.db.query(ClientAppointment).filter(
                and_(
                    ClientAppointment.appointment_id == appointment_id,
                    ClientAppointment.client_id == client_id,
                    ClientAppointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
                )
            ).first()
            
            if not appointment:
                return {'success': False, 'error': 'Appointment not found or cannot be rescheduled'}
            
            # Store reschedule request information
            reschedule_data = {
                'requested_at': datetime.utcnow().isoformat(),
                'preferred_times': preferred_times,
                'reason': reason,
                'original_time': appointment.scheduled_start.isoformat() if appointment.scheduled_start else None
            }
            
            # Update appointment notes with reschedule request
            current_notes = appointment.notes or ""
            appointment.notes = f"{current_notes}\n\nReschedule requested: {reschedule_data}"
            
            # Log reschedule request
            self.audit_manager.log_event(
                user_id=client_id,
                action=AuditAction.APPOINTMENT_SCHEDULED,
                resource_type='appointment',
                resource_id=appointment_id,
                ip_address=ip_address,
                action_details={
                    'action': 'reschedule_requested',
                    'appointment_title': appointment.title,
                    'preferred_times': preferred_times,
                    'reason': reason
                }
            )
            
            self.db.commit()
            
            # Notify legal team about reschedule request
            if self.notification_manager:
                await self.notification_manager.create_notification(
                    client_id=client_id,
                    notification_type=NotificationType.APPOINTMENT_SCHEDULED,
                    title="Appointment Reschedule Requested",
                    message=f"Client has requested to reschedule '{appointment.title}'",
                    priority=NotificationPriority.HIGH,
                    related_entity_type='appointment',
                    related_entity_id=appointment_id,
                    action_data={'reschedule_data': reschedule_data}
                )
            
            return {
                'success': True,
                'message': 'Reschedule request submitted successfully. You will be contacted to confirm new timing.',
                'appointment': self._appointment_to_dict(appointment)
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Failed to request reschedule: {str(e)}'}
    
    async def cancel_appointment(
        self,
        appointment_id: str,
        client_id: int,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel an appointment."""
        try:
            # Get appointment with access validation
            appointment = self.db.query(ClientAppointment).filter(
                and_(
                    ClientAppointment.appointment_id == appointment_id,
                    ClientAppointment.client_id == client_id,
                    ClientAppointment.status.in_([
                        AppointmentStatus.SCHEDULED, 
                        AppointmentStatus.CONFIRMED
                    ])
                )
            ).first()
            
            if not appointment:
                return {'success': False, 'error': 'Appointment not found or cannot be cancelled'}
            
            # Check cancellation policy (e.g., minimum notice required)
            if appointment.scheduled_start:
                time_until = appointment.scheduled_start - datetime.utcnow()
                if time_until.total_seconds() < 24 * 3600:  # Less than 24 hours notice
                    # Still allow cancellation but note the short notice
                    reason = f"Short notice cancellation. {reason or ''}"
            
            # Update appointment status
            appointment.status = AppointmentStatus.CANCELLED
            if reason:
                current_notes = appointment.notes or ""
                appointment.notes = f"{current_notes}\n\nCancelled: {reason} (at {datetime.utcnow().isoformat()})"
            
            # Log cancellation
            self.audit_manager.log_event(
                user_id=client_id,
                action=AuditAction.APPOINTMENT_SCHEDULED,
                resource_type='appointment',
                resource_id=appointment_id,
                ip_address=ip_address,
                action_details={
                    'action': 'cancelled',
                    'appointment_title': appointment.title,
                    'reason': reason
                }
            )
            
            self.db.commit()
            
            # Notify legal team about cancellation
            if self.notification_manager:
                await self.notification_manager.create_notification(
                    client_id=client_id,
                    notification_type=NotificationType.APPOINTMENT_SCHEDULED,
                    title="Appointment Cancelled",
                    message=f"Appointment '{appointment.title}' has been cancelled",
                    priority=NotificationPriority.HIGH,
                    related_entity_type='appointment',
                    related_entity_id=appointment_id,
                    action_data={'reason': reason}
                )
            
            return {
                'success': True,
                'message': 'Appointment cancelled successfully',
                'appointment': self._appointment_to_dict(appointment)
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Failed to cancel appointment: {str(e)}'}
    
    async def get_upcoming_appointments(
        self,
        client_id: int,
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """Get upcoming appointments for client."""
        try:
            # Calculate date range
            now = datetime.utcnow()
            end_date = now + timedelta(days=days_ahead)
            
            # Get upcoming appointments
            appointments = self.db.query(ClientAppointment).filter(
                and_(
                    ClientAppointment.client_id == client_id,
                    ClientAppointment.scheduled_start >= now,
                    ClientAppointment.scheduled_start <= end_date,
                    ClientAppointment.status.in_([
                        AppointmentStatus.SCHEDULED,
                        AppointmentStatus.CONFIRMED
                    ])
                )
            ).order_by(ClientAppointment.scheduled_start).all()
            
            # Group by day
            appointments_by_day = {}
            for appointment in appointments:
                if appointment.scheduled_start:
                    day_key = appointment.scheduled_start.date().isoformat()
                    if day_key not in appointments_by_day:
                        appointments_by_day[day_key] = []
                    
                    apt_dict = self._appointment_to_dict(appointment)
                    
                    # Add case info if available
                    if appointment.case_id:
                        case = self.db.query(ClientCase).filter(ClientCase.id == appointment.case_id).first()
                        if case:
                            apt_dict['case'] = {
                                'case_id': case.case_id,
                                'title': case.title
                            }
                    
                    appointments_by_day[day_key].append(apt_dict)
            
            return {
                'success': True,
                'upcoming_appointments': appointments_by_day,
                'total_count': len(appointments),
                'date_range': {
                    'from': now.isoformat(),
                    'to': end_date.isoformat()
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve upcoming appointments: {str(e)}'}
    
    async def get_appointment_statistics(self, client_id: int) -> Dict[str, Any]:
        """Get appointment statistics for client."""
        try:
            # Count by status
            status_counts = {}
            for status in AppointmentStatus:
                count = self.db.query(ClientAppointment).filter(
                    and_(
                        ClientAppointment.client_id == client_id,
                        ClientAppointment.status == status
                    )
                ).count()
                status_counts[status.value] = count
            
            # Count by appointment type
            type_counts = self.db.query(
                ClientAppointment.appointment_type,
                func.count(ClientAppointment.id)
            ).filter(
                ClientAppointment.client_id == client_id
            ).group_by(ClientAppointment.appointment_type).all()
            
            appointment_types = {
                apt_type: count for apt_type, count in type_counts if apt_type
            }
            
            # Recent appointments
            recent_appointments = self.db.query(ClientAppointment).filter(
                ClientAppointment.client_id == client_id
            ).order_by(desc(ClientAppointment.created_at)).limit(5).all()
            
            # Next appointment
            next_appointment = self.db.query(ClientAppointment).filter(
                and_(
                    ClientAppointment.client_id == client_id,
                    ClientAppointment.scheduled_start >= datetime.utcnow(),
                    ClientAppointment.status.in_([
                        AppointmentStatus.SCHEDULED,
                        AppointmentStatus.CONFIRMED
                    ])
                )
            ).order_by(ClientAppointment.scheduled_start).first()
            
            next_apt_info = None
            if next_appointment:
                next_apt_info = {
                    'appointment_id': next_appointment.appointment_id,
                    'title': next_appointment.title,
                    'scheduled_start': next_appointment.scheduled_start.isoformat() if next_appointment.scheduled_start else None,
                    'appointment_type': next_appointment.appointment_type,
                    'time_until_hours': (next_appointment.scheduled_start - datetime.utcnow()).total_seconds() / 3600 if next_appointment.scheduled_start else None
                }
            
            return {
                'success': True,
                'statistics': {
                    'total_appointments': sum(status_counts.values()),
                    'by_status': status_counts,
                    'by_type': appointment_types,
                    'next_appointment': next_apt_info,
                    'recent_appointments': [
                        {
                            'appointment_id': apt.appointment_id,
                            'title': apt.title,
                            'scheduled_start': apt.scheduled_start.isoformat() if apt.scheduled_start else None,
                            'status': apt.status.value if apt.status else None
                        } for apt in recent_appointments
                    ]
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Statistics failed: {str(e)}'}
    
    async def generate_calendar_file(
        self,
        client_id: int,
        appointment_id: Optional[str] = None,
        date_range_days: int = 90
    ) -> Dict[str, Any]:
        """Generate iCalendar file for appointments."""
        try:
            # Get appointments
            query = self.db.query(ClientAppointment).filter(
                ClientAppointment.client_id == client_id
            )
            
            if appointment_id:
                query = query.filter(ClientAppointment.appointment_id == appointment_id)
            else:
                # Get appointments in date range
                start_date = datetime.utcnow()
                end_date = start_date + timedelta(days=date_range_days)
                query = query.filter(
                    and_(
                        ClientAppointment.scheduled_start >= start_date,
                        ClientAppointment.scheduled_end <= end_date,
                        ClientAppointment.status.in_([
                            AppointmentStatus.SCHEDULED,
                            AppointmentStatus.CONFIRMED
                        ])
                    )
                )
            
            appointments = query.all()
            
            # Create calendar
            cal = Calendar()
            cal.add('prodid', '-//Legal AI Portal//Client Portal//EN')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'PUBLISH')
            
            # Add appointments as events
            for appointment in appointments:
                event = Event()
                event.add('uid', f"{appointment.appointment_id}@legalai-portal.com")
                event.add('dtstart', appointment.scheduled_start)
                event.add('dtend', appointment.scheduled_end)
                event.add('dtstamp', datetime.utcnow())
                event.add('summary', appointment.title)
                
                if appointment.description:
                    event.add('description', appointment.description)
                
                if appointment.location_address:
                    event.add('location', appointment.location_address)
                elif appointment.meeting_url:
                    event.add('location', f"Video Conference: {appointment.meeting_url}")
                
                # Add attorney information
                if appointment.attorney_name:
                    event.add('organizer', f"mailto:appointments@legalai-portal.com")
                    event.add('attendee', f"cn={appointment.attorney_name}")
                
                # Add reminders
                if appointment.status == AppointmentStatus.CONFIRMED:
                    event.add('status', 'CONFIRMED')
                else:
                    event.add('status', 'TENTATIVE')
                
                cal.add_component(event)
            
            # Generate calendar content
            calendar_content = cal.to_ical().decode('utf-8')
            
            return {
                'success': True,
                'calendar_content': calendar_content,
                'appointment_count': len(appointments),
                'filename': f"appointments_client_{client_id}_{datetime.now().strftime('%Y%m%d')}.ics"
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to generate calendar file: {str(e)}'}
    
    def _appointment_to_dict(self, appointment: ClientAppointment, include_details: bool = False) -> Dict[str, Any]:
        """Convert appointment to dictionary representation."""
        base_dict = {
            'appointment_id': appointment.appointment_id,
            'title': appointment.title,
            'description': appointment.description,
            'appointment_type': appointment.appointment_type,
            'scheduled_start': appointment.scheduled_start.isoformat() if appointment.scheduled_start else None,
            'scheduled_end': appointment.scheduled_end.isoformat() if appointment.scheduled_end else None,
            'timezone': appointment.timezone,
            'status': appointment.status.value if appointment.status else None,
            'location_type': appointment.location_type,
            'attorney_name': appointment.attorney_name,
            'confirmation_required': appointment.confirmation_required,
            'confirmed_at': appointment.confirmed_at.isoformat() if appointment.confirmed_at else None,
            'created_at': appointment.created_at.isoformat() if appointment.created_at else None
        }
        
        if include_details:
            base_dict.update({
                'location_address': appointment.location_address,
                'meeting_url': appointment.meeting_url,
                'meeting_credentials': appointment.meeting_credentials,
                'participants': appointment.participants,
                'reminder_sent': appointment.reminder_sent,
                'notes': appointment.notes,
                'created_by': appointment.created_by,
                'updated_at': appointment.updated_at.isoformat() if appointment.updated_at else None
            })
        
        return base_dict