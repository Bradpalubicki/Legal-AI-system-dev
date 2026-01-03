"""
WebSocket Handler for Client Portal

Manages WebSocket connections, message routing, and real-time communication
between clients and the legal portal system.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Optional, Any, List, Set
from dataclasses import dataclass
from enum import Enum
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import redis

from .realtime_manager import RealtimeManager, UpdateType, NotificationPriority
from .models import ClientUser, NotificationType


class MessageType(Enum):
    # Connection management
    PING = "ping"
    PONG = "pong"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    
    # Subscriptions
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    
    # Notifications
    NOTIFICATION_ACK = "notification_ack"
    MARK_READ = "mark_read"
    
    # Real-time updates
    DOCUMENT_UPDATE = "document_update"
    MESSAGE_UPDATE = "message_update"
    CASE_UPDATE = "case_update"
    
    # Client actions
    STATUS_UPDATE = "status_update"
    TYPING_INDICATOR = "typing_indicator"
    
    # System
    ERROR = "error"
    SYSTEM_MESSAGE = "system_message"


@dataclass
class WebSocketMessage:
    """Represents a WebSocket message."""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime
    message_id: Optional[str] = None
    requires_ack: bool = False


class ClientWebSocketHandler:
    """Handles WebSocket communication for client portal."""
    
    def __init__(self, db_session: Session, redis_client: redis.Redis):
        self.db = db_session
        self.redis = redis_client
        self.realtime_manager = RealtimeManager(db_session, redis_client)
        
        # Message handlers
        self.message_handlers = {
            MessageType.PING: self._handle_ping,
            MessageType.SUBSCRIBE: self._handle_subscribe,
            MessageType.UNSUBSCRIBE: self._handle_unsubscribe,
            MessageType.NOTIFICATION_ACK: self._handle_notification_ack,
            MessageType.MARK_READ: self._handle_mark_read,
            MessageType.STATUS_UPDATE: self._handle_status_update,
            MessageType.TYPING_INDICATOR: self._handle_typing_indicator,
        }
        
        # Connection state tracking
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        
    async def start(self):
        """Start the WebSocket handler."""
        await self.realtime_manager.start()
    
    async def stop(self):
        """Stop the WebSocket handler."""
        await self.realtime_manager.stop()
    
    async def handle_client_connection(
        self,
        websocket: WebSocket,
        client_id: int,
        session_id: str,
        ip_address: str,
        user_agent: str
    ) -> Optional[str]:
        """Handle new client WebSocket connection."""
        try:
            # Validate client exists
            client = self.db.query(ClientUser).filter(ClientUser.id == client_id).first()
            if not client:
                await websocket.close(code=1008, reason="Client not found")
                return None
            
            # Connect via realtime manager
            connection_id = await self.realtime_manager.connect_client(
                websocket=websocket,
                client_id=client_id,
                session_id=session_id,
                metadata={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'connected_at': datetime.utcnow().isoformat()
                }
            )
            
            # Store connection state
            self.active_connections[connection_id] = {
                'client_id': client_id,
                'session_id': session_id,
                'websocket': websocket,
                'last_activity': datetime.utcnow(),
                'subscribed_channels': set(),
                'status': 'online'
            }
            
            # Start message processing loop
            asyncio.create_task(self._process_client_messages(connection_id, websocket))
            
            return connection_id
            
        except Exception as e:
            await websocket.close(code=1011, reason=f"Connection failed: {str(e)}")
            return None
    
    async def disconnect_client(self, connection_id: str, reason: str = "client_disconnect"):
        """Disconnect client WebSocket."""
        try:
            if connection_id in self.active_connections:
                connection_info = self.active_connections[connection_id]
                
                # Update status
                connection_info['status'] = 'offline'
                
                # Disconnect via realtime manager
                await self.realtime_manager.disconnect_client(connection_id, reason)
                
                # Clean up local state
                del self.active_connections[connection_id]
                
        except Exception as e:
            print(f"Error disconnecting client {connection_id}: {str(e)}")
    
    async def send_notification_to_client(
        self,
        client_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None
    ) -> bool:
        """Send real-time notification to client."""
        return await self.realtime_manager.send_notification(
            client_id=client_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            data=data,
            action_url=action_url
        )
    
    async def broadcast_document_update(
        self,
        client_id: int,
        document_id: str,
        action: str,
        document_data: Dict[str, Any]
    ):
        """Broadcast document update to client."""
        await self.realtime_manager.send_notification(
            client_id=client_id,
            notification_type=NotificationType.DOCUMENT_SHARED,
            title="Document Update",
            message=f"Document {action}: {document_data.get('title', 'Untitled')}",
            priority=NotificationPriority.MEDIUM,
            data={
                'document_id': document_id,
                'action': action,
                'document': document_data
            }
        )
    
    async def broadcast_message_update(
        self,
        client_id: int,
        message_id: str,
        action: str,
        message_data: Dict[str, Any]
    ):
        """Broadcast message update to client."""
        await self.realtime_manager.send_notification(
            client_id=client_id,
            notification_type=NotificationType.MESSAGE_RECEIVED,
            title="New Message",
            message=f"You have a new message: {message_data.get('subject', 'No subject')}",
            priority=NotificationPriority.HIGH,
            data={
                'message_id': message_id,
                'action': action,
                'message': message_data
            }
        )
    
    async def broadcast_case_update(
        self,
        client_id: int,
        case_id: str,
        action: str,
        case_data: Dict[str, Any],
        update_details: Optional[Dict[str, Any]] = None
    ):
        """Broadcast case update to client."""
        await self.realtime_manager.send_notification(
            client_id=client_id,
            notification_type=NotificationType.CASE_UPDATE,
            title="Case Update",
            message=f"Case update: {case_data.get('title', 'Unknown case')}",
            priority=NotificationPriority.HIGH,
            data={
                'case_id': case_id,
                'action': action,
                'case': case_data,
                'details': update_details or {}
            }
        )
    
    async def send_system_alert(
        self,
        client_id: Optional[int] = None,
        title: str = "System Alert",
        message: str = "",
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None
    ):
        """Send system alert to client(s)."""
        await self.realtime_manager.send_system_alert(
            target_client_id=client_id,
            title=title,
            message=message,
            priority=priority,
            data=data
        )
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        realtime_stats = await self.realtime_manager.get_connection_stats()
        
        # Add local stats
        local_stats = {
            'active_local_connections': len(self.active_connections),
            'connections_by_status': {},
            'connections_by_client': {}
        }
        
        # Count by status
        for conn_info in self.active_connections.values():
            status = conn_info['status']
            local_stats['connections_by_status'][status] = \
                local_stats['connections_by_status'].get(status, 0) + 1
            
            client_id = conn_info['client_id']
            local_stats['connections_by_client'][client_id] = \
                local_stats['connections_by_client'].get(client_id, 0) + 1
        
        return {
            **realtime_stats,
            **local_stats
        }
    
    async def _process_client_messages(self, connection_id: str, websocket: WebSocket):
        """Process incoming WebSocket messages from client."""
        try:
            while connection_id in self.active_connections:
                try:
                    # Wait for message
                    raw_message = await websocket.receive_text()
                    
                    # Parse message
                    try:
                        message_data = json.loads(raw_message)
                        message = self._parse_websocket_message(message_data)
                    except (json.JSONDecodeError, ValueError) as e:
                        await self._send_error(websocket, "Invalid message format", str(e))
                        continue
                    
                    # Update last activity
                    if connection_id in self.active_connections:
                        self.active_connections[connection_id]['last_activity'] = datetime.utcnow()
                    
                    # Handle message
                    await self._handle_message(connection_id, websocket, message)
                    
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    print(f"Error processing message from {connection_id}: {str(e)}")
                    await self._send_error(websocket, "Message processing error", str(e))
                    
        except Exception as e:
            print(f"Error in message processing loop for {connection_id}: {str(e)}")
        finally:
            # Clean up connection
            await self.disconnect_client(connection_id, "message_loop_ended")
    
    async def _handle_message(
        self,
        connection_id: str,
        websocket: WebSocket,
        message: WebSocketMessage
    ):
        """Handle individual WebSocket message."""
        try:
            # Get handler for message type
            handler = self.message_handlers.get(message.type)
            if handler:
                await handler(connection_id, websocket, message)
            else:
                await self._send_error(websocket, "Unknown message type", message.type.value)
                
        except Exception as e:
            print(f"Error handling message {message.type.value}: {str(e)}")
            await self._send_error(websocket, "Message handling error", str(e))
    
    async def _handle_ping(
        self,
        connection_id: str,
        websocket: WebSocket,
        message: WebSocketMessage
    ):
        """Handle ping message."""
        pong_message = {
            'type': MessageType.PONG.value,
            'data': {
                'timestamp': datetime.utcnow().isoformat(),
                'message_id': message.message_id
            }
        }
        
        await websocket.send_text(json.dumps(pong_message))
    
    async def _handle_subscribe(
        self,
        connection_id: str,
        websocket: WebSocket,
        message: WebSocketMessage
    ):
        """Handle subscription request."""
        try:
            channel = message.data.get('channel')
            if not channel:
                await self._send_error(websocket, "Missing channel in subscribe request")
                return
            
            # Subscribe to channel
            success = await self.realtime_manager.subscribe_to_group(connection_id, channel)
            
            if success:
                # Update local state
                if connection_id in self.active_connections:
                    self.active_connections[connection_id]['subscribed_channels'].add(channel)
                
                response = {
                    'type': 'subscription_confirmed',
                    'data': {
                        'channel': channel,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
            else:
                response = {
                    'type': 'subscription_failed',
                    'data': {
                        'channel': channel,
                        'error': 'Failed to subscribe'
                    }
                }
            
            await websocket.send_text(json.dumps(response))
            
        except Exception as e:
            await self._send_error(websocket, "Subscription error", str(e))
    
    async def _handle_unsubscribe(
        self,
        connection_id: str,
        websocket: WebSocket,
        message: WebSocketMessage
    ):
        """Handle unsubscription request."""
        try:
            channel = message.data.get('channel')
            if not channel:
                await self._send_error(websocket, "Missing channel in unsubscribe request")
                return
            
            # Unsubscribe from channel
            success = await self.realtime_manager.unsubscribe_from_group(connection_id, channel)
            
            if success:
                # Update local state
                if connection_id in self.active_connections:
                    self.active_connections[connection_id]['subscribed_channels'].discard(channel)
                
                response = {
                    'type': 'unsubscription_confirmed',
                    'data': {
                        'channel': channel,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
            else:
                response = {
                    'type': 'unsubscription_failed',
                    'data': {
                        'channel': channel,
                        'error': 'Failed to unsubscribe'
                    }
                }
            
            await websocket.send_text(json.dumps(response))
            
        except Exception as e:
            await self._send_error(websocket, "Unsubscription error", str(e))
    
    async def _handle_notification_ack(
        self,
        connection_id: str,
        websocket: WebSocket,
        message: WebSocketMessage
    ):
        """Handle notification acknowledgment."""
        try:
            notification_id = message.data.get('notification_id')
            if notification_id:
                # Mark notification as delivered via realtime manager
                await self.realtime_manager.notification_manager.mark_as_delivered(notification_id)
                
        except Exception as e:
            print(f"Error handling notification ack: {str(e)}")
    
    async def _handle_mark_read(
        self,
        connection_id: str,
        websocket: WebSocket,
        message: WebSocketMessage
    ):
        """Handle mark as read request."""
        try:
            notification_id = message.data.get('notification_id')
            if connection_id in self.active_connections:
                client_id = self.active_connections[connection_id]['client_id']
                
                # Mark as read via notification manager
                result = await self.realtime_manager.notification_manager.mark_as_read(
                    notification_id, client_id
                )
                
                response = {
                    'type': 'mark_read_response',
                    'data': {
                        'notification_id': notification_id,
                        'success': result['success'],
                        'message': result.get('message', result.get('error'))
                    }
                }
                
                await websocket.send_text(json.dumps(response))
                
        except Exception as e:
            await self._send_error(websocket, "Mark read error", str(e))
    
    async def _handle_status_update(
        self,
        connection_id: str,
        websocket: WebSocket,
        message: WebSocketMessage
    ):
        """Handle client status update."""
        try:
            status = message.data.get('status')
            if connection_id in self.active_connections and status:
                self.active_connections[connection_id]['status'] = status
                
                # You could broadcast status updates to other relevant connections
                # For now, just acknowledge
                response = {
                    'type': 'status_updated',
                    'data': {
                        'status': status,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
                
                await websocket.send_text(json.dumps(response))
                
        except Exception as e:
            await self._send_error(websocket, "Status update error", str(e))
    
    async def _handle_typing_indicator(
        self,
        connection_id: str,
        websocket: WebSocket,
        message: WebSocketMessage
    ):
        """Handle typing indicator."""
        try:
            # For now, just acknowledge
            # In a full implementation, you might broadcast to other relevant connections
            response = {
                'type': 'typing_acknowledged',
                'data': {
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
            await websocket.send_text(json.dumps(response))
            
        except Exception as e:
            await self._send_error(websocket, "Typing indicator error", str(e))
    
    async def _send_error(
        self,
        websocket: WebSocket,
        error_type: str,
        details: str = ""
    ):
        """Send error message to client."""
        try:
            error_message = {
                'type': MessageType.ERROR.value,
                'data': {
                    'error_type': error_type,
                    'details': details,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
            await websocket.send_text(json.dumps(error_message))
            
        except Exception as e:
            print(f"Failed to send error message: {str(e)}")
    
    def _parse_websocket_message(self, message_data: Dict[str, Any]) -> WebSocketMessage:
        """Parse raw WebSocket message data."""
        try:
            message_type = MessageType(message_data.get('type'))
            data = message_data.get('data', {})
            
            return WebSocketMessage(
                type=message_type,
                data=data,
                timestamp=datetime.utcnow(),
                message_id=message_data.get('message_id'),
                requires_ack=message_data.get('requires_ack', False)
            )
            
        except ValueError:
            raise ValueError(f"Invalid message type: {message_data.get('type')}")
        except Exception as e:
            raise ValueError(f"Invalid message format: {str(e)}")