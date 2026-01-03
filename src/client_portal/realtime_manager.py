"""
Real-time Updates Manager for Client Portal

Handles WebSocket connections, real-time notifications, live updates,
and synchronization of client portal data across multiple sessions.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Set, Optional, Any, List
from dataclasses import dataclass, asdict
import uuid
import weakref
from enum import Enum

import redis
from sqlalchemy.orm import Session
from fastapi import WebSocket, WebSocketDisconnect

from .models import (
    ClientNotification, NotificationType, NotificationPriority,
    ClientUser, ClientDocument, ClientMessage, ClientCase
)
from .notification_manager import NotificationManager


class ConnectionStatus(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"

class UpdateType(Enum):
    NOTIFICATION = "notification"
    DOCUMENT = "document"
    MESSAGE = "message"
    CASE_UPDATE = "case_update"
    SYSTEM_ALERT = "system_alert"
    SESSION_UPDATE = "session_update"

@dataclass
class ClientConnection:
    """Represents a client WebSocket connection."""
    connection_id: str
    client_id: int
    websocket: WebSocket
    connected_at: datetime
    last_ping: datetime
    status: ConnectionStatus
    subscriptions: Set[str]
    metadata: Dict[str, Any]

@dataclass
class RealtimeUpdate:
    """Represents a real-time update to be sent to clients."""
    update_id: str
    update_type: UpdateType
    target_client_id: Optional[int]
    target_group: Optional[str]
    data: Dict[str, Any]
    priority: NotificationPriority
    expires_at: Optional[datetime]
    created_at: datetime


class RealtimeManager:
    """Manages real-time connections and updates for client portal."""
    
    def __init__(self, db_session: Session, redis_client: redis.Redis):
        self.db = db_session
        self.redis = redis_client
        self.notification_manager = NotificationManager(db_session, redis_client)
        
        # Connection management
        self.connections: Dict[str, ClientConnection] = {}
        self.client_connections: Dict[int, Set[str]] = {}  # client_id -> connection_ids
        self.connection_groups: Dict[str, Set[str]] = {}  # group_name -> connection_ids
        
        # Update queue and processing
        self.update_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        
        # Settings
        self.ping_interval = 30  # seconds
        self.connection_timeout = 300  # seconds
        self.max_connections_per_client = 5
        
    async def start(self):
        """Start the real-time manager."""
        self.processing_task = asyncio.create_task(self._process_updates())
        await self._start_ping_task()
    
    async def stop(self):
        """Stop the real-time manager."""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
    
    async def connect_client(
        self, 
        websocket: WebSocket, 
        client_id: int, 
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Connect a new client WebSocket."""
        try:
            await websocket.accept()
            
            # Check connection limits
            existing_connections = self.client_connections.get(client_id, set())
            if len(existing_connections) >= self.max_connections_per_client:
                # Disconnect oldest connection
                oldest_conn_id = min(existing_connections, 
                                   key=lambda cid: self.connections[cid].connected_at)
                await self._disconnect_client(oldest_conn_id, "connection_limit_exceeded")
            
            # Create connection
            connection_id = str(uuid.uuid4())
            connection = ClientConnection(
                connection_id=connection_id,
                client_id=client_id,
                websocket=websocket,
                connected_at=datetime.utcnow(),
                last_ping=datetime.utcnow(),
                status=ConnectionStatus.CONNECTED,
                subscriptions=set(),
                metadata=metadata or {}
            )
            
            # Store connection
            self.connections[connection_id] = connection
            if client_id not in self.client_connections:
                self.client_connections[client_id] = set()
            self.client_connections[client_id].add(connection_id)
            
            # Subscribe to default channels
            await self._subscribe_connection(connection_id, f"client_{client_id}")
            
            # Store in Redis for multi-instance coordination
            await self._store_connection_in_redis(connection)
            
            # Send initial connection confirmation
            await self._send_to_connection(connection_id, {
                'type': 'connection_established',
                'connection_id': connection_id,
                'timestamp': datetime.utcnow().isoformat(),
                'subscriptions': list(connection.subscriptions)
            })
            
            # Send any pending notifications
            await self._send_pending_notifications(client_id, connection_id)
            
            return connection_id
            
        except Exception as e:
            print(f"Connection failed for client {client_id}: {str(e)}")
            raise
    
    async def disconnect_client(self, connection_id: str, reason: str = "client_disconnect"):
        """Disconnect a client WebSocket."""
        await self._disconnect_client(connection_id, reason)
    
    async def send_notification(
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
        try:
            # Create notification update
            update = RealtimeUpdate(
                update_id=str(uuid.uuid4()),
                update_type=UpdateType.NOTIFICATION,
                target_client_id=client_id,
                target_group=None,
                data={
                    'type': 'notification',
                    'notification_type': notification_type.value,
                    'title': title,
                    'message': message,
                    'priority': priority.value,
                    'data': data or {},
                    'action_url': action_url,
                    'timestamp': datetime.utcnow().isoformat()
                },
                priority=priority,
                expires_at=None,
                created_at=datetime.utcnow()
            )
            
            # Queue for processing
            await self.update_queue.put(update)
            
            # Also store in database via notification manager
            await self.notification_manager.create_notification(
                client_id=client_id,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                action_data=data,
                action_url=action_url,
                delivery_method=['portal']
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
            return False
    
    async def broadcast_document_update(
        self,
        client_id: int,
        document: ClientDocument,
        action: str
    ):
        """Broadcast document-related updates to client."""
        update = RealtimeUpdate(
            update_id=str(uuid.uuid4()),
            update_type=UpdateType.DOCUMENT,
            target_client_id=client_id,
            target_group=None,
            data={
                'type': 'document_update',
                'action': action,
                'document': document.to_dict(),
                'timestamp': datetime.utcnow().isoformat()
            },
            priority=NotificationPriority.MEDIUM,
            expires_at=None,
            created_at=datetime.utcnow()
        )
        
        await self.update_queue.put(update)
    
    async def broadcast_message_update(
        self,
        client_id: int,
        message: ClientMessage,
        action: str
    ):
        """Broadcast message-related updates to client."""
        update = RealtimeUpdate(
            update_id=str(uuid.uuid4()),
            update_type=UpdateType.MESSAGE,
            target_client_id=client_id,
            target_group=None,
            data={
                'type': 'message_update',
                'action': action,
                'message': {
                    'id': message.message_id,
                    'subject': message.subject,
                    'content': message.content[:200] + "..." if len(message.content) > 200 else message.content,
                    'sender_type': 'attorney' if message.sender_id != client_id else 'client',
                    'status': message.status.value,
                    'sent_at': message.sent_at.isoformat() if message.sent_at else None,
                    'thread_id': message.thread_id,
                    'case_id': message.case_id
                },
                'timestamp': datetime.utcnow().isoformat()
            },
            priority=NotificationPriority.HIGH,
            expires_at=None,
            created_at=datetime.utcnow()
        )
        
        await self.update_queue.put(update)
    
    async def broadcast_case_update(
        self,
        client_id: int,
        case: ClientCase,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Broadcast case-related updates to client."""
        update = RealtimeUpdate(
            update_id=str(uuid.uuid4()),
            update_type=UpdateType.CASE_UPDATE,
            target_client_id=client_id,
            target_group=None,
            data={
                'type': 'case_update',
                'action': action,
                'case': {
                    'id': case.case_id,
                    'case_number': case.case_number,
                    'title': case.title,
                    'status': case.status.value,
                    'progress_percentage': case.progress_percentage,
                    'assigned_attorney': case.assigned_attorney,
                    'next_hearing': case.next_hearing.isoformat() if case.next_hearing else None
                },
                'details': details or {},
                'timestamp': datetime.utcnow().isoformat()
            },
            priority=NotificationPriority.HIGH,
            expires_at=None,
            created_at=datetime.utcnow()
        )
        
        await self.update_queue.put(update)
    
    async def send_system_alert(
        self,
        target_client_id: Optional[int] = None,
        target_group: Optional[str] = None,
        title: str = "System Alert",
        message: str = "",
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None
    ):
        """Send system-wide or targeted alerts."""
        update = RealtimeUpdate(
            update_id=str(uuid.uuid4()),
            update_type=UpdateType.SYSTEM_ALERT,
            target_client_id=target_client_id,
            target_group=target_group,
            data={
                'type': 'system_alert',
                'title': title,
                'message': message,
                'priority': priority.value,
                'data': data or {},
                'timestamp': datetime.utcnow().isoformat()
            },
            priority=priority,
            expires_at=None,
            created_at=datetime.utcnow()
        )
        
        await self.update_queue.put(update)
    
    async def subscribe_to_group(self, connection_id: str, group_name: str) -> bool:
        """Subscribe connection to a group channel."""
        return await self._subscribe_connection(connection_id, group_name)
    
    async def unsubscribe_from_group(self, connection_id: str, group_name: str) -> bool:
        """Unsubscribe connection from a group channel."""
        return await self._unsubscribe_connection(connection_id, group_name)
    
    async def get_client_connections(self, client_id: int) -> List[str]:
        """Get all active connection IDs for a client."""
        return list(self.client_connections.get(client_id, set()))
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get real-time connection statistics."""
        return {
            'total_connections': len(self.connections),
            'unique_clients': len(self.client_connections),
            'connection_groups': {
                group: len(connections) 
                for group, connections in self.connection_groups.items()
            },
            'queue_size': self.update_queue.qsize()
        }
    
    async def _process_updates(self):
        """Process queued real-time updates."""
        while True:
            try:
                update = await self.update_queue.get()
                await self._handle_update(update)
                self.update_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing update: {str(e)}")
    
    async def _handle_update(self, update: RealtimeUpdate):
        """Handle individual update distribution."""
        try:
            target_connections = set()
            
            # Determine target connections
            if update.target_client_id:
                client_connections = self.client_connections.get(update.target_client_id, set())
                target_connections.update(client_connections)
            
            if update.target_group:
                group_connections = self.connection_groups.get(update.target_group, set())
                target_connections.update(group_connections)
            
            # Send to all target connections
            if target_connections:
                tasks = [
                    self._send_to_connection(conn_id, update.data)
                    for conn_id in target_connections
                    if conn_id in self.connections
                ]
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            print(f"Error handling update {update.update_id}: {str(e)}")
    
    async def _send_to_connection(self, connection_id: str, data: Dict[str, Any]) -> bool:
        """Send data to specific connection."""
        try:
            connection = self.connections.get(connection_id)
            if not connection or connection.status != ConnectionStatus.CONNECTED:
                return False
            
            await connection.websocket.send_text(json.dumps(data))
            return True
            
        except WebSocketDisconnect:
            await self._disconnect_client(connection_id, "websocket_disconnect")
            return False
        except Exception as e:
            print(f"Error sending to connection {connection_id}: {str(e)}")
            await self._disconnect_client(connection_id, "send_error")
            return False
    
    async def _disconnect_client(self, connection_id: str, reason: str):
        """Internal method to disconnect and cleanup client connection."""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return
            
            # Update status
            connection.status = ConnectionStatus.DISCONNECTED
            
            # Close WebSocket if still open
            try:
                await connection.websocket.close()
            except:
                pass
            
            # Clean up subscriptions
            for group in connection.subscriptions.copy():
                await self._unsubscribe_connection(connection_id, group)
            
            # Remove from tracking
            if connection.client_id in self.client_connections:
                self.client_connections[connection.client_id].discard(connection_id)
                if not self.client_connections[connection.client_id]:
                    del self.client_connections[connection.client_id]
            
            # Remove connection
            del self.connections[connection_id]
            
            # Remove from Redis
            await self._remove_connection_from_redis(connection_id)
            
            print(f"Client {connection.client_id} disconnected: {reason}")
            
        except Exception as e:
            print(f"Error disconnecting client {connection_id}: {str(e)}")
    
    async def _subscribe_connection(self, connection_id: str, group_name: str) -> bool:
        """Subscribe connection to group."""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return False
            
            connection.subscriptions.add(group_name)
            
            if group_name not in self.connection_groups:
                self.connection_groups[group_name] = set()
            self.connection_groups[group_name].add(connection_id)
            
            return True
            
        except Exception as e:
            print(f"Error subscribing connection {connection_id} to {group_name}: {str(e)}")
            return False
    
    async def _unsubscribe_connection(self, connection_id: str, group_name: str) -> bool:
        """Unsubscribe connection from group."""
        try:
            connection = self.connections.get(connection_id)
            if connection:
                connection.subscriptions.discard(group_name)
            
            if group_name in self.connection_groups:
                self.connection_groups[group_name].discard(connection_id)
                if not self.connection_groups[group_name]:
                    del self.connection_groups[group_name]
            
            return True
            
        except Exception as e:
            print(f"Error unsubscribing connection {connection_id} from {group_name}: {str(e)}")
            return False
    
    async def _send_pending_notifications(self, client_id: int, connection_id: str):
        """Send any pending notifications to newly connected client."""
        try:
            # Get recent undelivered notifications
            pending_notifications = await self.notification_manager.get_undelivered_notifications(
                client_id=client_id,
                limit=10
            )
            
            if pending_notifications['success'] and pending_notifications['notifications']:
                for notification in pending_notifications['notifications']:
                    await self._send_to_connection(connection_id, {
                        'type': 'pending_notification',
                        'notification': notification
                    })
                    
                    # Mark as delivered
                    await self.notification_manager.mark_as_delivered(
                        notification['notification_id']
                    )
            
        except Exception as e:
            print(f"Error sending pending notifications to client {client_id}: {str(e)}")
    
    async def _store_connection_in_redis(self, connection: ClientConnection):
        """Store connection info in Redis for multi-instance coordination."""
        try:
            connection_data = {
                'client_id': connection.client_id,
                'connected_at': connection.connected_at.isoformat(),
                'status': connection.status.value,
                'subscriptions': list(connection.subscriptions),
                'metadata': connection.metadata
            }
            
            await self.redis.hset(
                f"client_connections:{connection.connection_id}",
                mapping=connection_data
            )
            
            # Set expiration
            await self.redis.expire(
                f"client_connections:{connection.connection_id}",
                self.connection_timeout
            )
            
        except Exception as e:
            print(f"Error storing connection in Redis: {str(e)}")
    
    async def _remove_connection_from_redis(self, connection_id: str):
        """Remove connection from Redis."""
        try:
            await self.redis.delete(f"client_connections:{connection_id}")
        except Exception as e:
            print(f"Error removing connection from Redis: {str(e)}")
    
    async def _start_ping_task(self):
        """Start periodic ping task to maintain connections."""
        async def ping_connections():
            while True:
                try:
                    current_time = datetime.utcnow()
                    disconnected_connections = []
                    
                    for connection_id, connection in self.connections.items():
                        time_since_ping = (current_time - connection.last_ping).total_seconds()
                        
                        if time_since_ping > self.connection_timeout:
                            disconnected_connections.append(connection_id)
                        elif time_since_ping > self.ping_interval:
                            # Send ping
                            ping_sent = await self._send_to_connection(connection_id, {
                                'type': 'ping',
                                'timestamp': current_time.isoformat()
                            })
                            
                            if ping_sent:
                                connection.last_ping = current_time
                    
                    # Clean up disconnected connections
                    for connection_id in disconnected_connections:
                        await self._disconnect_client(connection_id, "timeout")
                    
                    await asyncio.sleep(self.ping_interval)
                    
                except Exception as e:
                    print(f"Error in ping task: {str(e)}")
                    await asyncio.sleep(self.ping_interval)
        
        asyncio.create_task(ping_connections())