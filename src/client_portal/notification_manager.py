"""
Client Portal Notification Manager

Handles notification creation, delivery, persistence, and management
for various client portal events and updates.
"""

import json
import smtplib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import redis
import uuid

from .models import (
    ClientNotification, ClientUser, NotificationType, 
    NotificationPriority, ClientAuditLog, AuditAction
)


class NotificationManager:
    """Manages client portal notifications and delivery."""
    
    def __init__(self, db_session: Session, redis_client: redis.Redis, email_config: Optional[Dict] = None):
        self.db = db_session
        self.redis = redis_client
        self.email_config = email_config or {}
        
        # Default settings
        self.batch_size = 100
        self.retry_attempts = 3
        self.retry_delay = timedelta(minutes=5)
        
        # Email templates
        self.email_templates = {
            NotificationType.CASE_UPDATE: {
                'subject': 'Case Update - {case_title}',
                'template': 'case_update_email.html'
            },
            NotificationType.DOCUMENT_SHARED: {
                'subject': 'New Document Available - {document_title}',
                'template': 'document_shared_email.html'
            },
            NotificationType.MESSAGE_RECEIVED: {
                'subject': 'New Message from Your Legal Team',
                'template': 'message_received_email.html'
            },
            NotificationType.APPOINTMENT_SCHEDULED: {
                'subject': 'Appointment Scheduled - {appointment_title}',
                'template': 'appointment_scheduled_email.html'
            },
            NotificationType.INVOICE_GENERATED: {
                'subject': 'New Invoice Available',
                'template': 'invoice_generated_email.html'
            },
            NotificationType.DEADLINE_REMINDER: {
                'subject': 'Important Deadline Reminder',
                'template': 'deadline_reminder_email.html'
            },
            NotificationType.SYSTEM_ALERT: {
                'subject': 'System Alert',
                'template': 'system_alert_email.html'
            }
        }
    
    async def create_notification(
        self,
        client_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None,
        action_url: Optional[str] = None,
        action_data: Optional[Dict[str, Any]] = None,
        delivery_method: Optional[List[str]] = None,
        scheduled_for: Optional[datetime] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a new notification for a client."""
        try:
            # Validate client exists
            client = self.db.query(ClientUser).filter(ClientUser.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            # Create notification
            notification = ClientNotification(
                client_id=client_id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                action_url=action_url,
                action_data=action_data or {},
                delivery_method=delivery_method or ['portal'],
                scheduled_for=scheduled_for,
                expires_at=expires_at
            )
            
            self.db.add(notification)
            self.db.commit()
            
            # Queue for immediate delivery if not scheduled
            if not scheduled_for or scheduled_for <= datetime.utcnow():
                await self._queue_notification_delivery(notification)
            
            return {
                'success': True,
                'notification_id': notification.notification_id,
                'message': 'Notification created successfully'
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Failed to create notification: {str(e)}'}
    
    async def get_client_notifications(
        self,
        client_id: int,
        notification_type: Optional[NotificationType] = None,
        is_read: Optional[bool] = None,
        priority: Optional[NotificationPriority] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get notifications for a client."""
        try:
            # Build query
            query = self.db.query(ClientNotification).filter(
                ClientNotification.client_id == client_id
            )
            
            # Apply filters
            if notification_type:
                query = query.filter(ClientNotification.notification_type == notification_type)
            
            if is_read is not None:
                query = query.filter(ClientNotification.is_read == is_read)
            
            if priority:
                query = query.filter(ClientNotification.priority == priority)
            
            # Filter out expired notifications
            query = query.filter(
                or_(
                    ClientNotification.expires_at.is_(None),
                    ClientNotification.expires_at > datetime.utcnow()
                )
            )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            notifications = query.order_by(
                desc(ClientNotification.priority),
                desc(ClientNotification.created_at)
            ).offset((page - 1) * limit).limit(limit).all()
            
            return {
                'success': True,
                'notifications': [self._notification_to_dict(n) for n in notifications],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit
                },
                'unread_count': query.filter(ClientNotification.is_read == False).count()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to get notifications: {str(e)}'}
    
    async def mark_as_read(self, notification_id: str, client_id: int) -> Dict[str, Any]:
        """Mark notification as read."""
        try:
            notification = self.db.query(ClientNotification).filter(
                and_(
                    ClientNotification.notification_id == notification_id,
                    ClientNotification.client_id == client_id
                )
            ).first()
            
            if not notification:
                return {'success': False, 'error': 'Notification not found'}
            
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                self.db.commit()
            
            return {'success': True, 'message': 'Notification marked as read'}
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Failed to mark as read: {str(e)}'}
    
    async def mark_as_delivered(self, notification_id: str) -> Dict[str, Any]:
        """Mark notification as delivered."""
        try:
            notification = self.db.query(ClientNotification).filter(
                ClientNotification.notification_id == notification_id
            ).first()
            
            if not notification:
                return {'success': False, 'error': 'Notification not found'}
            
            if not notification.is_delivered:
                notification.is_delivered = True
                notification.delivered_at = datetime.utcnow()
                self.db.commit()
            
            return {'success': True, 'message': 'Notification marked as delivered'}
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Failed to mark as delivered: {str(e)}'}
    
    async def mark_all_as_read(self, client_id: int) -> Dict[str, Any]:
        """Mark all notifications as read for a client."""
        try:
            updated = self.db.query(ClientNotification).filter(
                and_(
                    ClientNotification.client_id == client_id,
                    ClientNotification.is_read == False
                )
            ).update({
                'is_read': True,
                'read_at': datetime.utcnow()
            })
            
            self.db.commit()
            
            return {
                'success': True,
                'message': f'Marked {updated} notifications as read'
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Failed to mark all as read: {str(e)}'}
    
    async def delete_notification(self, notification_id: str, client_id: int) -> Dict[str, Any]:
        """Delete a notification."""
        try:
            notification = self.db.query(ClientNotification).filter(
                and_(
                    ClientNotification.notification_id == notification_id,
                    ClientNotification.client_id == client_id
                )
            ).first()
            
            if not notification:
                return {'success': False, 'error': 'Notification not found'}
            
            self.db.delete(notification)
            self.db.commit()
            
            return {'success': True, 'message': 'Notification deleted successfully'}
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Failed to delete notification: {str(e)}'}
    
    async def get_undelivered_notifications(
        self,
        client_id: Optional[int] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get undelivered notifications for processing."""
        try:
            query = self.db.query(ClientNotification).filter(
                and_(
                    ClientNotification.is_delivered == False,
                    or_(
                        ClientNotification.scheduled_for.is_(None),
                        ClientNotification.scheduled_for <= datetime.utcnow()
                    ),
                    or_(
                        ClientNotification.expires_at.is_(None),
                        ClientNotification.expires_at > datetime.utcnow()
                    )
                )
            )
            
            if client_id:
                query = query.filter(ClientNotification.client_id == client_id)
            
            notifications = query.order_by(
                desc(ClientNotification.priority),
                ClientNotification.created_at
            ).limit(limit).all()
            
            return {
                'success': True,
                'notifications': [self._notification_to_dict(n) for n in notifications]
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to get undelivered notifications: {str(e)}'}
    
    async def update_notification_preferences(
        self,
        client_id: int,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update client notification preferences."""
        try:
            client = self.db.query(ClientUser).filter(ClientUser.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            # Update preferences
            client.notification_preferences = {
                **(client.notification_preferences or {}),
                **preferences
            }
            
            self.db.commit()
            
            return {
                'success': True,
                'preferences': client.notification_preferences,
                'message': 'Notification preferences updated'
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Failed to update preferences: {str(e)}'}
    
    async def get_notification_statistics(self, client_id: int) -> Dict[str, Any]:
        """Get notification statistics for client."""
        try:
            # Count by type
            type_counts = {}
            for notification_type in NotificationType:
                count = self.db.query(ClientNotification).filter(
                    and_(
                        ClientNotification.client_id == client_id,
                        ClientNotification.notification_type == notification_type
                    )
                ).count()
                type_counts[notification_type.value] = count
            
            # Count by priority
            priority_counts = {}
            for priority in NotificationPriority:
                count = self.db.query(ClientNotification).filter(
                    and_(
                        ClientNotification.client_id == client_id,
                        ClientNotification.priority == priority
                    )
                ).count()
                priority_counts[priority.value] = count
            
            # Overall stats
            total_notifications = sum(type_counts.values())
            unread_count = self.db.query(ClientNotification).filter(
                and_(
                    ClientNotification.client_id == client_id,
                    ClientNotification.is_read == False
                )
            ).count()
            
            # Recent activity (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_count = self.db.query(ClientNotification).filter(
                and_(
                    ClientNotification.client_id == client_id,
                    ClientNotification.created_at >= week_ago
                )
            ).count()
            
            return {
                'success': True,
                'statistics': {
                    'total_notifications': total_notifications,
                    'unread_count': unread_count,
                    'recent_count': recent_count,
                    'by_type': type_counts,
                    'by_priority': priority_counts
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to get statistics: {str(e)}'}
    
    async def send_email_notification(
        self,
        notification: ClientNotification,
        client: ClientUser
    ) -> bool:
        """Send email notification to client."""
        try:
            if not self.email_config or not client.email:
                return False
            
            # Check if client wants email notifications
            prefs = client.notification_preferences or {}
            if not prefs.get('email_notifications', True):
                return False
            
            # Check notification type preferences
            type_key = f"email_{notification.notification_type.value}"
            if not prefs.get(type_key, True):
                return False
            
            # Get email template
            template_config = self.email_templates.get(notification.notification_type)
            if not template_config:
                return False
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.email_config.get('smtp_from')
            msg['To'] = client.email
            msg['Subject'] = template_config['subject'].format(
                client_name=f"{client.first_name} {client.last_name}",
                **notification.action_data
            )
            
            # Email body
            body = self._generate_email_body(notification, client, template_config['template'])
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(
                self.email_config.get('smtp_host'),
                self.email_config.get('smtp_port', 587)
            ) as server:
                server.starttls()
                server.login(
                    self.email_config.get('smtp_user'),
                    self.email_config.get('smtp_password')
                )
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Failed to send email notification: {str(e)}")
            return False
    
    async def cleanup_expired_notifications(self) -> Dict[str, Any]:
        """Clean up expired notifications."""
        try:
            expired_count = self.db.query(ClientNotification).filter(
                and_(
                    ClientNotification.expires_at.isnot(None),
                    ClientNotification.expires_at <= datetime.utcnow()
                )
            ).count()
            
            # Delete expired notifications
            self.db.query(ClientNotification).filter(
                and_(
                    ClientNotification.expires_at.isnot(None),
                    ClientNotification.expires_at <= datetime.utcnow()
                )
            ).delete()
            
            self.db.commit()
            
            return {
                'success': True,
                'expired_count': expired_count,
                'message': f'Cleaned up {expired_count} expired notifications'
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Cleanup failed: {str(e)}'}
    
    async def _queue_notification_delivery(self, notification: ClientNotification):
        """Queue notification for delivery processing."""
        try:
            delivery_data = {
                'notification_id': notification.notification_id,
                'client_id': notification.client_id,
                'delivery_method': notification.delivery_method,
                'created_at': notification.created_at.isoformat(),
                'priority': notification.priority.value
            }
            
            # Add to Redis queue for processing
            await self.redis.lpush('notification_delivery_queue', json.dumps(delivery_data))
            
        except Exception as e:
            print(f"Failed to queue notification delivery: {str(e)}")
    
    def _notification_to_dict(self, notification: ClientNotification) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            'notification_id': notification.notification_id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type.value,
            'priority': notification.priority.value,
            'is_read': notification.is_read,
            'is_delivered': notification.is_delivered,
            'related_entity_type': notification.related_entity_type,
            'related_entity_id': notification.related_entity_id,
            'action_url': notification.action_url,
            'action_data': notification.action_data,
            'created_at': notification.created_at.isoformat() if notification.created_at else None,
            'delivered_at': notification.delivered_at.isoformat() if notification.delivered_at else None,
            'read_at': notification.read_at.isoformat() if notification.read_at else None,
            'expires_at': notification.expires_at.isoformat() if notification.expires_at else None
        }
    
    def _generate_email_body(
        self,
        notification: ClientNotification,
        client: ClientUser,
        template_name: str
    ) -> str:
        """Generate email body from template."""
        # Simple template for now - in production, use a proper template engine
        return f"""
        <html>
        <body>
        <h2>{notification.title}</h2>
        <p>Dear {client.first_name} {client.last_name},</p>
        <p>{notification.message}</p>
        
        {f'<p><a href="{notification.action_url}">Click here to view details</a></p>' if notification.action_url else ''}
        
        <p>Best regards,<br>Your Legal Team</p>
        
        <hr>
        <p><small>This is an automated message from your legal portal. 
        Please do not reply directly to this email.</small></p>
        </body>
        </html>
        """