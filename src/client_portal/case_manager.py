"""
Client Portal Case Manager

Handles client access to case information, status updates, timelines,
and case-related documents with appropriate security controls.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from decimal import Decimal

from .models import (
    ClientCase, ClientUser, CaseStatus, ClientDocument, 
    ClientMessage, ClientAppointment, ClientInvoice, ClientAuditLog, AuditAction
)
from .audit_manager import ClientAuditManager


class ClientCaseManager:
    """Manages client access to case information and updates."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.audit_manager = ClientAuditManager(db_session)
    
    async def get_client_cases(
        self,
        client_id: int,
        status: Optional[CaseStatus] = None,
        practice_area: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get all cases for a client."""
        try:
            # Validate client exists
            client = self.db.query(ClientUser).filter(ClientUser.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            # Build query
            query = self.db.query(ClientCase).filter(ClientCase.client_id == client_id)
            
            # Apply filters
            if status:
                query = query.filter(ClientCase.status == status)
            
            if practice_area:
                query = query.filter(ClientCase.practice_area.ilike(f"%{practice_area}%"))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            cases = query.order_by(desc(ClientCase.created_at)).offset(
                (page - 1) * limit
            ).limit(limit).all()
            
            # Convert to dictionaries with summary information
            case_summaries = []
            for case in cases:
                case_dict = self._case_to_dict(case, include_details=False)
                
                # Add summary statistics
                case_dict['summary'] = await self._get_case_summary(case.id, client_id)
                case_summaries.append(case_dict)
            
            return {
                'success': True,
                'cases': case_summaries,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve cases: {str(e)}'}
    
    async def get_case_details(
        self,
        case_id: str,
        client_id: int,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed information for a specific case."""
        try:
            # Get case with access validation
            case = self.db.query(ClientCase).filter(
                and_(
                    ClientCase.case_id == case_id,
                    ClientCase.client_id == client_id
                )
            ).first()
            
            if not case:
                return {'success': False, 'error': 'Case not found or access denied'}
            
            # Log access
            self.audit_manager.log_event(
                user_id=client_id,
                action=AuditAction.CASE_VIEWED,
                resource_type='case',
                resource_id=case_id,
                ip_address=ip_address,
                action_details={
                    'case_number': case.case_number,
                    'case_title': case.title
                }
            )
            
            # Get detailed case information
            case_dict = self._case_to_dict(case, include_details=True)
            
            # Add related information
            case_dict['documents'] = await self._get_case_documents(case.id)
            case_dict['messages'] = await self._get_case_messages(case.id)
            case_dict['appointments'] = await self._get_case_appointments(case.id)
            case_dict['invoices'] = await self._get_case_invoices(case.id)
            case_dict['timeline'] = await self._get_case_timeline(case.id)
            
            return {
                'success': True,
                'case': case_dict
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve case details: {str(e)}'}
    
    async def get_case_status_history(
        self,
        case_id: str,
        client_id: int
    ) -> Dict[str, Any]:
        """Get status change history for a case."""
        try:
            # Validate case access
            case = self.db.query(ClientCase).filter(
                and_(
                    ClientCase.case_id == case_id,
                    ClientCase.client_id == client_id
                )
            ).first()
            
            if not case:
                return {'success': False, 'error': 'Case not found or access denied'}
            
            # Get audit logs for case status changes
            # This would typically come from a separate case_status_history table
            # For now, we'll create a placeholder history based on the current case
            
            status_history = [
                {
                    'status': 'pending',
                    'date': case.opened_date.isoformat() if case.opened_date else None,
                    'description': 'Case opened and initial review started',
                    'updated_by': 'Legal Team'
                },
                {
                    'status': case.status.value,
                    'date': case.updated_at.isoformat() if case.updated_at else None,
                    'description': f'Case status updated to {case.status.value}',
                    'updated_by': 'Legal Team'
                }
            ]
            
            # If case is closed, add closing information
            if case.status == CaseStatus.CLOSED and case.closed_date:
                status_history.append({
                    'status': 'closed',
                    'date': case.closed_date.isoformat(),
                    'description': 'Case closed',
                    'updated_by': 'Legal Team'
                })
            
            return {
                'success': True,
                'case_id': case_id,
                'status_history': status_history
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve status history: {str(e)}'}
    
    async def get_case_progress(
        self,
        case_id: str,
        client_id: int
    ) -> Dict[str, Any]:
        """Get case progress information and milestones."""
        try:
            # Validate case access
            case = self.db.query(ClientCase).filter(
                and_(
                    ClientCase.case_id == case_id,
                    ClientCase.client_id == client_id
                )
            ).first()
            
            if not case:
                return {'success': False, 'error': 'Case not found or access denied'}
            
            # Calculate progress metrics
            total_documents = self.db.query(ClientDocument).filter(
                ClientDocument.case_id == case.id
            ).count()
            
            total_messages = self.db.query(ClientMessage).filter(
                ClientMessage.case_id == case.id
            ).count()
            
            completed_appointments = self.db.query(ClientAppointment).filter(
                and_(
                    ClientAppointment.case_id == case.id,
                    ClientAppointment.status == 'completed'
                )
            ).count()
            
            # Create milestone data (this would typically come from a case management system)
            milestones = [
                {
                    'id': 1,
                    'title': 'Initial Consultation',
                    'description': 'First meeting to discuss case details',
                    'target_date': case.opened_date.isoformat() if case.opened_date else None,
                    'completed': True,
                    'completed_date': case.opened_date.isoformat() if case.opened_date else None
                },
                {
                    'id': 2,
                    'title': 'Document Collection',
                    'description': 'Gathering all relevant documents and evidence',
                    'target_date': (case.opened_date + timedelta(days=30)).isoformat() if case.opened_date else None,
                    'completed': total_documents > 0,
                    'completed_date': None
                },
                {
                    'id': 3,
                    'title': 'Case Analysis',
                    'description': 'Comprehensive analysis of case merits and strategy',
                    'target_date': (case.opened_date + timedelta(days=60)).isoformat() if case.opened_date else None,
                    'completed': case.progress_percentage >= 50,
                    'completed_date': None
                }
            ]
            
            # Add case-specific milestones based on case type
            if case.next_hearing:
                milestones.append({
                    'id': 4,
                    'title': 'Court Hearing',
                    'description': f'Scheduled hearing at {case.court_name or "court"}',
                    'target_date': case.next_hearing.isoformat(),
                    'completed': case.next_hearing < datetime.utcnow(),
                    'completed_date': None
                })
            
            return {
                'success': True,
                'case_id': case_id,
                'progress': {
                    'percentage': case.progress_percentage or 0,
                    'status': case.status.value,
                    'milestones': milestones,
                    'metrics': {
                        'documents_collected': total_documents,
                        'messages_exchanged': total_messages,
                        'appointments_completed': completed_appointments
                    }
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve case progress: {str(e)}'}
    
    async def get_case_statistics(self, client_id: int) -> Dict[str, Any]:
        """Get case statistics for client dashboard."""
        try:
            # Count by status
            status_counts = {}
            for status in CaseStatus:
                count = self.db.query(ClientCase).filter(
                    and_(
                        ClientCase.client_id == client_id,
                        ClientCase.status == status
                    )
                ).count()
                status_counts[status.value] = count
            
            # Count by practice area
            practice_area_counts = self.db.query(
                ClientCase.practice_area,
                func.count(ClientCase.id)
            ).filter(
                ClientCase.client_id == client_id
            ).group_by(ClientCase.practice_area).all()
            
            practice_areas = {
                area: count for area, count in practice_area_counts if area
            }
            
            # Recent activity
            recent_cases = self.db.query(ClientCase).filter(
                ClientCase.client_id == client_id
            ).order_by(desc(ClientCase.updated_at)).limit(3).all()
            
            # Financial summary
            total_billed = self.db.query(
                func.sum(ClientCase.total_billed)
            ).filter(ClientCase.client_id == client_id).scalar() or Decimal('0')
            
            return {
                'success': True,
                'statistics': {
                    'total_cases': sum(status_counts.values()),
                    'by_status': status_counts,
                    'by_practice_area': practice_areas,
                    'total_billed': float(total_billed),
                    'recent_cases': [
                        {
                            'case_id': case.case_id,
                            'title': case.title,
                            'status': case.status.value,
                            'updated_at': case.updated_at.isoformat() if case.updated_at else None
                        } for case in recent_cases
                    ]
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Statistics failed: {str(e)}'}
    
    async def _get_case_summary(self, case_db_id: int, client_id: int) -> Dict[str, Any]:
        """Get summary statistics for a case."""
        try:
            # Count related items
            document_count = self.db.query(ClientDocument).filter(
                ClientDocument.case_id == case_db_id
            ).count()
            
            message_count = self.db.query(ClientMessage).filter(
                ClientMessage.case_id == case_db_id
            ).count()
            
            appointment_count = self.db.query(ClientAppointment).filter(
                ClientAppointment.case_id == case_db_id
            ).count()
            
            invoice_count = self.db.query(ClientInvoice).filter(
                ClientInvoice.case_id == case_db_id
            ).count()
            
            # Get latest activity
            latest_document = self.db.query(ClientDocument).filter(
                ClientDocument.case_id == case_db_id
            ).order_by(desc(ClientDocument.created_at)).first()
            
            latest_message = self.db.query(ClientMessage).filter(
                ClientMessage.case_id == case_db_id
            ).order_by(desc(ClientMessage.sent_at)).first()
            
            last_activity = None
            if latest_document and latest_message:
                last_activity = max(latest_document.created_at, latest_message.sent_at)
            elif latest_document:
                last_activity = latest_document.created_at
            elif latest_message:
                last_activity = latest_message.sent_at
            
            return {
                'document_count': document_count,
                'message_count': message_count,
                'appointment_count': appointment_count,
                'invoice_count': invoice_count,
                'last_activity': last_activity.isoformat() if last_activity else None
            }
            
        except Exception as e:
            return {}
    
    async def _get_case_documents(self, case_db_id: int) -> List[Dict[str, Any]]:
        """Get documents associated with a case."""
        try:
            documents = self.db.query(ClientDocument).filter(
                ClientDocument.case_id == case_db_id
            ).order_by(desc(ClientDocument.created_at)).limit(10).all()
            
            return [doc.to_dict() for doc in documents]
            
        except Exception as e:
            return []
    
    async def _get_case_messages(self, case_db_id: int) -> List[Dict[str, Any]]:
        """Get messages associated with a case."""
        try:
            messages = self.db.query(ClientMessage).filter(
                ClientMessage.case_id == case_db_id
            ).order_by(desc(ClientMessage.sent_at)).limit(5).all()
            
            return [
                {
                    'message_id': msg.message_id,
                    'subject': msg.subject,
                    'sent_at': msg.sent_at.isoformat() if msg.sent_at else None,
                    'status': msg.status.value if msg.status else None,
                    'thread_id': msg.thread_id
                } for msg in messages
            ]
            
        except Exception as e:
            return []
    
    async def _get_case_appointments(self, case_db_id: int) -> List[Dict[str, Any]]:
        """Get appointments associated with a case."""
        try:
            appointments = self.db.query(ClientAppointment).filter(
                ClientAppointment.case_id == case_db_id
            ).order_by(desc(ClientAppointment.scheduled_start)).limit(5).all()
            
            return [
                {
                    'appointment_id': apt.appointment_id,
                    'title': apt.title,
                    'scheduled_start': apt.scheduled_start.isoformat() if apt.scheduled_start else None,
                    'scheduled_end': apt.scheduled_end.isoformat() if apt.scheduled_end else None,
                    'status': apt.status.value if apt.status else None,
                    'location_type': apt.location_type,
                    'appointment_type': apt.appointment_type
                } for apt in appointments
            ]
            
        except Exception as e:
            return []
    
    async def _get_case_invoices(self, case_db_id: int) -> List[Dict[str, Any]]:
        """Get invoices associated with a case."""
        try:
            invoices = self.db.query(ClientInvoice).filter(
                ClientInvoice.case_id == case_db_id
            ).order_by(desc(ClientInvoice.created_at)).limit(5).all()
            
            return [
                {
                    'invoice_id': inv.invoice_id,
                    'invoice_number': inv.invoice_number,
                    'total_amount': float(inv.total_amount) if inv.total_amount else 0,
                    'status': inv.status.value if inv.status else None,
                    'issued_date': inv.issued_date.isoformat() if inv.issued_date else None,
                    'due_date': inv.due_date.isoformat() if inv.due_date else None
                } for inv in invoices
            ]
            
        except Exception as e:
            return []
    
    async def _get_case_timeline(self, case_db_id: int) -> List[Dict[str, Any]]:
        """Get timeline of events for a case."""
        try:
            timeline_events = []
            
            # Add documents to timeline
            documents = self.db.query(ClientDocument).filter(
                ClientDocument.case_id == case_db_id
            ).order_by(ClientDocument.created_at).all()
            
            for doc in documents:
                timeline_events.append({
                    'date': doc.created_at.isoformat() if doc.created_at else None,
                    'type': 'document',
                    'title': f'Document Added: {doc.title or doc.original_filename}',
                    'description': doc.description or 'Document uploaded to case',
                    'id': doc.document_id
                })
            
            # Add messages to timeline
            messages = self.db.query(ClientMessage).filter(
                ClientMessage.case_id == case_db_id
            ).order_by(ClientMessage.sent_at).all()
            
            for msg in messages:
                timeline_events.append({
                    'date': msg.sent_at.isoformat() if msg.sent_at else None,
                    'type': 'message',
                    'title': f'Message: {msg.subject}',
                    'description': 'Client communication',
                    'id': msg.message_id
                })
            
            # Add appointments to timeline
            appointments = self.db.query(ClientAppointment).filter(
                ClientAppointment.case_id == case_db_id
            ).order_by(ClientAppointment.scheduled_start).all()
            
            for apt in appointments:
                timeline_events.append({
                    'date': apt.scheduled_start.isoformat() if apt.scheduled_start else None,
                    'type': 'appointment',
                    'title': f'Appointment: {apt.title}',
                    'description': f'{apt.appointment_type} - {apt.location_type}',
                    'id': apt.appointment_id
                })
            
            # Sort timeline by date
            timeline_events.sort(key=lambda x: x['date'] or '', reverse=True)
            
            return timeline_events[:20]  # Return last 20 events
            
        except Exception as e:
            return []
    
    def _case_to_dict(self, case: ClientCase, include_details: bool = False) -> Dict[str, Any]:
        """Convert case to dictionary representation."""
        base_dict = {
            'case_id': case.case_id,
            'case_number': case.case_number,
            'title': case.title,
            'description': case.description if include_details else (case.description[:200] + "..." if case.description and len(case.description) > 200 else case.description),
            'case_type': case.case_type,
            'practice_area': case.practice_area,
            'status': case.status.value if case.status else None,
            'priority': case.priority.value if case.priority else None,
            'progress_percentage': case.progress_percentage,
            'assigned_attorney': case.assigned_attorney,
            'opened_date': case.opened_date.isoformat() if case.opened_date else None,
            'updated_at': case.updated_at.isoformat() if case.updated_at else None
        }
        
        if include_details:
            base_dict.update({
                'assigned_paralegal': case.assigned_paralegal,
                'team_members': case.team_members,
                'closed_date': case.closed_date.isoformat() if case.closed_date else None,
                'statute_limitations': case.statute_limitations.isoformat() if case.statute_limitations else None,
                'next_hearing': case.next_hearing.isoformat() if case.next_hearing else None,
                'court_name': case.court_name,
                'judge_name': case.judge_name,
                'opposing_counsel': case.opposing_counsel,
                'billing_rate': float(case.billing_rate) if case.billing_rate else None,
                'estimated_budget': float(case.estimated_budget) if case.estimated_budget else None,
                'total_billed': float(case.total_billed) if case.total_billed else None,
                'created_at': case.created_at.isoformat() if case.created_at else None,
                'created_by': case.created_by
            })
        
        return base_dict