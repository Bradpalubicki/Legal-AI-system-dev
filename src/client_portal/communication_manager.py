"""
Client Portal Communication Manager

Handles secure messaging between clients and legal team including
threaded conversations, message encryption, and delivery tracking.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import uuid
import html

from .models import (
    ClientMessage, ClientUser, MessageStatus, ClientCase,
    ClientAuditLog, AuditAction
)
from .notification_manager import NotificationManager
from .audit_manager import ClientAuditManager


class CommunicationManager:
    """Manages secure client-attorney communications."""
    
    def __init__(self, db_session: Session, notification_manager: Optional[NotificationManager] = None):
        self.db = db_session
        self.notification_manager = notification_manager
        self.audit_manager = ClientAuditManager(db_session)
        
        # Message settings
        self.max_message_length = 50000
        self.message_retention_days = 365 * 7  # 7 years for legal compliance
    
    async def send_message(
        self,
        sender_id: int,
        recipient_type: str,  # 'attorney', 'paralegal', 'staff'
        subject: str,
        content: str,
        case_id: Optional[int] = None,
        thread_id: Optional[str] = None,
        parent_message_id: Optional[int] = None,
        priority: str = "medium",
        is_encrypted: bool = True,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a new message from client to legal team."""
        try:
            # Validate sender
            sender = self.db.query(ClientUser).filter(ClientUser.id == sender_id).first()
            if not sender:
                return {'success': False, 'error': 'Sender not found'}
            
            # Validate content
            if not content.strip():
                return {'success': False, 'error': 'Message content cannot be empty'}
            
            if len(content) > self.max_message_length:
                return {'success': False, 'error': f'Message too long. Maximum {self.max_message_length} characters'}
            
            # Sanitize content (basic HTML escaping)
            sanitized_content = html.escape(content)
            
            # Generate thread ID if not provided
            if not thread_id and not parent_message_id:
                thread_id = str(uuid.uuid4())
            elif parent_message_id:
                # Get parent message to inherit thread_id
                parent_message = self.db.query(ClientMessage).filter(
                    ClientMessage.id == parent_message_id
                ).first()
                if parent_message:
                    thread_id = parent_message.thread_id
                else:
                    return {'success': False, 'error': 'Parent message not found'}
            
            # Create message
            message = ClientMessage(
                sender_id=sender_id,
                recipient_type=recipient_type,
                subject=subject,
                content=sanitized_content,
                content_type='text',
                status=MessageStatus.SENT,
                is_encrypted=is_encrypted,
                thread_id=thread_id,
                parent_message_id=parent_message_id,
                case_id=case_id,
                is_privileged=True  # All client-attorney communications are privileged
            )
            
            self.db.add(message)
            self.db.commit()
            
            # Log audit event
            self.audit_manager.log_event(
                user_id=sender_id,
                action=AuditAction.MESSAGE_SENT,
                resource_type='message',
                resource_id=message.message_id,
                ip_address=ip_address,
                action_details={
                    'recipient_type': recipient_type,
                    'subject': subject[:100],  # First 100 chars for audit
                    'case_id': case_id,
                    'thread_id': thread_id
                }
            )
            
            # Send notification to legal team (if notification manager available)
            if self.notification_manager:
                await self._notify_legal_team_new_message(message, sender)
            
            return {
                'success': True,
                'message': self._message_to_dict(message),
                'message_id': message.message_id
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Failed to send message: {str(e)}'}
    
    async def get_client_messages(
        self,
        client_id: int,
        thread_id: Optional[str] = None,
        case_id: Optional[int] = None,
        status: Optional[MessageStatus] = None,
        include_replies: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get messages for a client with filtering options."""
        try:
            # Build base query for messages where client is sender or recipient
            query = self.db.query(ClientMessage).filter(
                or_(
                    ClientMessage.sender_id == client_id,
                    # For now, clients only see their own sent messages
                    # In a full system, you'd also query for messages TO the client
                )
            )
            
            # Apply filters
            if thread_id:
                query = query.filter(ClientMessage.thread_id == thread_id)
            
            if case_id:
                query = query.filter(ClientMessage.case_id == case_id)
            
            if status:
                query = query.filter(ClientMessage.status == status)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            messages = query.order_by(desc(ClientMessage.sent_at)).offset(
                (page - 1) * limit
            ).limit(limit).all()
            
            # Group messages by thread if requested
            if include_replies and messages:
                messages_dict = {}
                thread_ids = list(set(msg.thread_id for msg in messages if msg.thread_id))
                
                for thread_id in thread_ids:
                    thread_messages = self.db.query(ClientMessage).filter(
                        and_(
                            ClientMessage.thread_id == thread_id,
                            or_(
                                ClientMessage.sender_id == client_id,
                                # Include messages TO client when implemented
                            )
                        )
                    ).order_by(ClientMessage.sent_at).all()
                    
                    messages_dict[thread_id] = [
                        self._message_to_dict(msg) for msg in thread_messages
                    ]
                
                return {
                    'success': True,
                    'messages': messages_dict,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total_count,
                        'pages': (total_count + limit - 1) // limit
                    }
                }
            else:
                return {
                    'success': True,
                    'messages': [self._message_to_dict(msg) for msg in messages],
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total_count,
                        'pages': (total_count + limit - 1) // limit
                    }
                }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve messages: {str(e)}'}
    
    async def get_message_thread(
        self,
        thread_id: str,
        client_id: int,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Get all messages in a thread."""
        try:
            # Get all messages in thread that client has access to
            messages = self.db.query(ClientMessage).filter(
                and_(
                    ClientMessage.thread_id == thread_id,
                    or_(
                        ClientMessage.sender_id == client_id,
                        # Include messages TO client when recipient functionality is implemented
                    )
                )
            ).order_by(ClientMessage.sent_at).all()
            
            if not messages:
                return {'success': False, 'error': 'Thread not found or access denied'}
            
            result = {
                'success': True,
                'thread_id': thread_id,
                'messages': [self._message_to_dict(msg) for msg in messages]
            }
            
            # Add metadata if requested
            if include_metadata:
                result['metadata'] = {
                    'message_count': len(messages),
                    'participants': list(set([msg.sender_id for msg in messages])),
                    'first_message_date': messages[0].sent_at.isoformat() if messages else None,
                    'last_message_date': messages[-1].sent_at.isoformat() if messages else None,
                    'case_id': messages[0].case_id if messages and messages[0].case_id else None,
                    'subject': messages[0].subject if messages else None
                }
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve thread: {str(e)}'}
    
    async def mark_message_as_read(
        self,
        message_id: str,
        client_id: int,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark a message as read by the client."""
        try:
            message = self.db.query(ClientMessage).filter(
                and_(
                    ClientMessage.message_id == message_id,
                    ClientMessage.sender_id == client_id  # Only sender can mark their own messages
                )
            ).first()
            
            if not message:
                return {'success': False, 'error': 'Message not found or access denied'}
            
            if message.read_at:
                return {'success': True, 'message': 'Message already marked as read'}
            
            message.status = MessageStatus.READ
            message.read_at = datetime.utcnow()
            
            # Log audit event
            self.audit_manager.log_event(
                user_id=client_id,
                action=AuditAction.MESSAGE_READ,
                resource_type='message',
                resource_id=message_id,
                ip_address=ip_address,
                action_details={
                    'subject': message.subject,
                    'thread_id': message.thread_id
                }
            )
            
            self.db.commit()
            
            return {'success': True, 'message': 'Message marked as read'}
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Failed to mark as read: {str(e)}'}
    
    async def search_messages(
        self,
        client_id: int,
        search_query: str,
        case_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search messages for client."""
        try:
            # Build search query
            base_query = self.db.query(ClientMessage).filter(
                ClientMessage.sender_id == client_id  # Only search client's own messages
            )
            
            # Text search across subject and content
            search_terms = search_query.lower().split()
            for term in search_terms:
                search_pattern = f"%{term}%"
                base_query = base_query.filter(
                    or_(
                        ClientMessage.subject.ilike(search_pattern),
                        ClientMessage.content.ilike(search_pattern)
                    )
                )
            
            # Additional filters
            if case_id:
                base_query = base_query.filter(ClientMessage.case_id == case_id)
            
            if date_from:
                base_query = base_query.filter(ClientMessage.sent_at >= date_from)
            
            if date_to:
                base_query = base_query.filter(ClientMessage.sent_at <= date_to)
            
            # Get total count
            total_count = base_query.count()
            
            # Apply pagination and ordering
            messages = base_query.order_by(desc(ClientMessage.sent_at)).offset(
                (page - 1) * limit
            ).limit(limit).all()
            
            return {
                'success': True,
                'messages': [self._message_to_dict(msg) for msg in messages],
                'search_query': search_query,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Message search failed: {str(e)}'}
    
    async def get_message_statistics(self, client_id: int) -> Dict[str, Any]:
        """Get messaging statistics for client."""
        try:
            # Total messages sent
            total_sent = self.db.query(ClientMessage).filter(
                ClientMessage.sender_id == client_id
            ).count()
            
            # Messages by status
            status_counts = {}
            for status in MessageStatus:
                count = self.db.query(ClientMessage).filter(
                    and_(
                        ClientMessage.sender_id == client_id,
                        ClientMessage.status == status
                    )
                ).count()
                status_counts[status.value] = count
            
            # Messages by case
            case_counts = self.db.query(
                ClientMessage.case_id,
                ClientCase.title
            ).join(
                ClientCase, ClientMessage.case_id == ClientCase.id, isouter=True
            ).filter(
                ClientMessage.sender_id == client_id
            ).all()
            
            case_message_counts = {}
            for case_id, case_title in case_counts:
                if case_id:
                    key = f"{case_id} - {case_title}" if case_title else f"Case {case_id}"
                else:
                    key = "No Case"
                case_message_counts[key] = case_message_counts.get(key, 0) + 1
            
            # Recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_messages = self.db.query(ClientMessage).filter(
                and_(
                    ClientMessage.sender_id == client_id,
                    ClientMessage.sent_at >= thirty_days_ago
                )
            ).count()
            
            # Thread statistics
            thread_count = self.db.query(ClientMessage.thread_id).filter(
                ClientMessage.sender_id == client_id
            ).distinct().count()
            
            return {
                'success': True,
                'statistics': {
                    'total_messages_sent': total_sent,
                    'by_status': status_counts,
                    'by_case': case_message_counts,
                    'recent_messages': recent_messages,
                    'active_threads': thread_count
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Statistics failed: {str(e)}'}
    
    async def archive_old_messages(self, days_old: int = None) -> Dict[str, Any]:
        """Archive old messages based on retention policy."""
        try:
            retention_days = days_old or self.message_retention_days
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Count messages to be archived
            old_messages_count = self.db.query(ClientMessage).filter(
                and_(
                    ClientMessage.sent_at < cutoff_date,
                    ClientMessage.status != MessageStatus.ARCHIVED
                )
            ).count()
            
            # Update status to archived (don't delete for legal compliance)
            self.db.query(ClientMessage).filter(
                and_(
                    ClientMessage.sent_at < cutoff_date,
                    ClientMessage.status != MessageStatus.ARCHIVED
                )
            ).update({'status': MessageStatus.ARCHIVED})
            
            self.db.commit()
            
            return {
                'success': True,
                'archived_count': old_messages_count,
                'message': f'Archived {old_messages_count} messages older than {retention_days} days'
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Archive operation failed: {str(e)}'}
    
    async def _notify_legal_team_new_message(self, message: ClientMessage, sender: ClientUser):
        """Notify legal team of new client message (placeholder)."""
        try:
            # This would typically notify attorneys/paralegals via email or internal system
            # For now, just log that notification would be sent
            print(f"New message from {sender.first_name} {sender.last_name}: {message.subject}")
            
            # In a full implementation, you might:
            # - Send email to assigned attorney
            # - Create internal notification
            # - Update case activity log
            # - Send SMS for urgent messages
            
        except Exception as e:
            print(f"Failed to notify legal team: {str(e)}")
    
    def _message_to_dict(self, message: ClientMessage) -> Dict[str, Any]:
        """Convert message to dictionary representation."""
        return {
            'message_id': message.message_id,
            'subject': message.subject,
            'content': message.content,
            'content_type': message.content_type,
            'status': message.status.value if message.status else None,
            'is_encrypted': message.is_encrypted,
            'thread_id': message.thread_id,
            'parent_message_id': message.parent_message_id,
            'case_id': message.case_id,
            'is_privileged': message.is_privileged,
            'sent_at': message.sent_at.isoformat() if message.sent_at else None,
            'delivered_at': message.delivered_at.isoformat() if message.delivered_at else None,
            'read_at': message.read_at.isoformat() if message.read_at else None,
            'sender_id': message.sender_id,
            'recipient_type': message.recipient_type,
            'created_at': message.created_at.isoformat() if message.created_at else None
        }