"""
WebSocket server for real-time transcript streaming.

High-performance WebSocket server with authentication, session management,
and real-time message broadcasting for court transcript streaming.
"""

import asyncio
import json
import logging
import ssl
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException

from .models import (
    TranscriptMessage, MessageType, ConnectionInfo, StreamStatus,
    generate_connection_id, create_heartbeat_message, create_error_message,
    create_status_message, MessageValidator, get_message_priority
)
from .auth_middleware import WebSocketAuthMiddleware
from .session_manager import SessionManager


@dataclass
class WebSocketConfig:
    """Configuration for WebSocket server."""
    host: str = "0.0.0.0"
    port: int = 8765
    
    # SSL configuration
    use_ssl: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    
    # Connection limits
    max_connections: int = 1000
    max_connections_per_ip: int = 10
    connection_timeout: int = 300  # seconds
    
    # Message handling
    max_message_size: int = 1024 * 1024  # 1MB
    message_queue_size: int = 100
    heartbeat_interval: int = 30  # seconds
    
    # Authentication
    require_auth: bool = True
    auth_timeout: int = 30  # seconds
    
    # Logging
    log_level: str = "INFO"
    log_messages: bool = False
    
    # Performance
    compression: bool = True
    ping_interval: int = 20
    ping_timeout: int = 20
    
    # CORS settings
    allowed_origins: Optional[List[str]] = None


class TranscriptWebSocketServer:
    """WebSocket server for real-time transcript streaming."""
    
    def __init__(self, 
                 config: WebSocketConfig,
                 auth_middleware: Optional[WebSocketAuthMiddleware] = None,
                 session_manager: Optional[SessionManager] = None):
        self.config = config
        self.auth_middleware = auth_middleware
        self.session_manager = session_manager or SessionManager()
        
        # Connection management
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        self.ip_connections: Dict[str, Set[str]] = {}
        
        # Message handling
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.broadcast_subscribers: Dict[str, Set[str]] = {}  # session_id -> connection_ids
        
        # Server state
        self.is_running = False
        self.server = None
        
        # Statistics
        self.total_connections = 0
        self.total_messages = 0
        self.start_time: Optional[datetime] = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, config.log_level.upper()))
        
        # Setup message handlers
        self._setup_default_handlers()
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
    
    def _setup_default_handlers(self):
        """Setup default message handlers."""
        self.register_handler(MessageType.AUTH, self._handle_auth_message)
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        self.register_handler(MessageType.CONNECT, self._handle_connect_message)
        self.register_handler(MessageType.DISCONNECT, self._handle_disconnect_message)
    
    async def start_server(self) -> None:
        """Start the WebSocket server."""
        if self.is_running:
            self.logger.warning("Server is already running")
            return
        
        self.logger.info(f"Starting WebSocket server on {self.config.host}:{self.config.port}")
        
        # Setup SSL context if required
        ssl_context = None
        if self.config.use_ssl:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(self.config.ssl_cert_path, self.config.ssl_key_path)
        
        # Configure server options
        server_kwargs = {
            "ping_interval": self.config.ping_interval,
            "ping_timeout": self.config.ping_timeout,
            "max_size": self.config.max_message_size,
            "compression": "deflate" if self.config.compression else None
        }
        
        if self.config.allowed_origins:
            server_kwargs["origins"] = self.config.allowed_origins
        
        # Start server
        try:
            self.server = await websockets.serve(
                self._handle_connection,
                self.config.host,
                self.config.port,
                ssl=ssl_context,
                **server_kwargs
            )
            
            self.is_running = True
            self.start_time = datetime.utcnow()
            
            # Start background tasks
            self._start_background_tasks()
            
            self.logger.info("WebSocket server started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    async def stop_server(self) -> None:
        """Stop the WebSocket server."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping WebSocket server")
        
        # Stop accepting new connections
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        # Disconnect all clients
        await self._disconnect_all_clients()
        
        # Cancel background tasks
        await self._stop_background_tasks()
        
        self.is_running = False
        self.logger.info("WebSocket server stopped")
    
    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Register a message handler for a specific message type."""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        
        self.logger.debug(f"Registered handler for {message_type.value}")
    
    def unregister_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Unregister a message handler."""
        if message_type in self.message_handlers:
            if handler in self.message_handlers[message_type]:
                self.message_handlers[message_type].remove(handler)
    
    async def broadcast_message(self, 
                              message: TranscriptMessage,
                              session_id: Optional[str] = None,
                              exclude_connections: Optional[Set[str]] = None) -> int:
        """
        Broadcast message to connected clients.
        
        Args:
            message: Message to broadcast
            session_id: Optional session ID to limit broadcast
            exclude_connections: Connection IDs to exclude
            
        Returns:
            Number of connections message was sent to
        """
        if not self.is_running:
            return 0
        
        exclude_connections = exclude_connections or set()
        target_connections = set()
        
        if session_id:
            # Broadcast to session subscribers only
            target_connections = self.broadcast_subscribers.get(session_id, set())
        else:
            # Broadcast to all authenticated connections
            target_connections = {
                conn_id for conn_id, info in self.connection_info.items()
                if info.is_authenticated
            }
        
        # Remove excluded connections
        target_connections -= exclude_connections
        
        # Send message to target connections
        send_tasks = []
        for conn_id in target_connections:
            if conn_id in self.connections:
                task = asyncio.create_task(
                    self._send_message_to_connection(conn_id, message)
                )
                send_tasks.append(task)
        
        # Wait for all sends to complete
        if send_tasks:
            results = await asyncio.gather(*send_tasks, return_exceptions=True)
            success_count = sum(1 for result in results if result is True)
            
            self.logger.debug(
                f"Broadcast message {message.message_type.value} to "
                f"{success_count}/{len(send_tasks)} connections"
            )
            
            return success_count
        
        return 0
    
    async def send_message_to_connection(self, 
                                       connection_id: str, 
                                       message: TranscriptMessage) -> bool:
        """Send message to specific connection."""
        return await self._send_message_to_connection(connection_id, message)
    
    async def subscribe_to_session(self, connection_id: str, session_id: str) -> bool:
        """Subscribe connection to session broadcasts."""
        if connection_id not in self.connection_info:
            return False
        
        if session_id not in self.broadcast_subscribers:
            self.broadcast_subscribers[session_id] = set()
        
        self.broadcast_subscribers[session_id].add(connection_id)
        
        self.logger.debug(f"Connection {connection_id} subscribed to session {session_id}")
        return True
    
    async def unsubscribe_from_session(self, connection_id: str, session_id: str) -> bool:
        """Unsubscribe connection from session broadcasts."""
        if session_id in self.broadcast_subscribers:
            self.broadcast_subscribers[session_id].discard(connection_id)
            
            # Clean up empty session subscriptions
            if not self.broadcast_subscribers[session_id]:
                del self.broadcast_subscribers[session_id]
            
            self.logger.debug(f"Connection {connection_id} unsubscribed from session {session_id}")
            return True
        
        return False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get server connection statistics."""
        active_connections = len(self.connections)
        authenticated_connections = sum(
            1 for info in self.connection_info.values() 
            if info.is_authenticated
        )
        
        return {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
            "active_connections": active_connections,
            "authenticated_connections": authenticated_connections,
            "total_connections": self.total_connections,
            "total_messages": self.total_messages,
            "session_subscriptions": len(self.broadcast_subscribers),
            "ip_distribution": {ip: len(conns) for ip, conns in self.ip_connections.items()}
        }
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle new WebSocket connection."""
        connection_id = generate_connection_id()
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        
        # Check connection limits
        if len(self.connections) >= self.config.max_connections:
            await websocket.close(code=1013, reason="Server at capacity")
            return
        
        # Check per-IP limits
        ip_conn_count = len(self.ip_connections.get(client_ip, set()))
        if ip_conn_count >= self.config.max_connections_per_ip:
            await websocket.close(code=1013, reason="Too many connections from IP")
            return
        
        # Create connection info
        connection_info = ConnectionInfo(
            connection_id=connection_id,
            ip_address=client_ip,
            user_agent=websocket.request_headers.get("User-Agent")
        )
        
        # Register connection
        self.connections[connection_id] = websocket
        self.connection_info[connection_id] = connection_info
        
        if client_ip not in self.ip_connections:
            self.ip_connections[client_ip] = set()
        self.ip_connections[client_ip].add(connection_id)
        
        self.total_connections += 1
        
        self.logger.info(f"New connection {connection_id} from {client_ip}")
        
        try:
            # Send connection acknowledgment
            await self._send_message_to_connection(
                connection_id,
                create_status_message(StreamStatus.CONNECTED, {
                    "connection_id": connection_id,
                    "server_time": datetime.utcnow().isoformat()
                })
            )
            
            # Handle authentication if required
            if self.config.require_auth:
                auth_success = await self._handle_authentication(connection_id, websocket)
                if not auth_success:
                    await websocket.close(code=1008, reason="Authentication failed")
                    return
            else:
                connection_info.is_authenticated = True
            
            # Main message loop
            await self._message_loop(connection_id, websocket)
            
        except ConnectionClosed:
            self.logger.info(f"Connection {connection_id} closed")
        except WebSocketException as e:
            self.logger.warning(f"WebSocket error on connection {connection_id}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error on connection {connection_id}: {e}")
        finally:
            # Clean up connection
            await self._cleanup_connection(connection_id)
    
    async def _handle_authentication(self, 
                                   connection_id: str, 
                                   websocket: WebSocketServerProtocol) -> bool:
        """Handle connection authentication."""
        if not self.auth_middleware:
            return True  # No auth middleware, allow connection
        
        # Wait for authentication message
        try:
            auth_message = await asyncio.wait_for(
                websocket.recv(),
                timeout=self.config.auth_timeout
            )
            
            # Parse and validate auth message
            try:
                auth_data = json.loads(auth_message)
                is_valid, errors = MessageValidator.validate_auth_message(auth_data)
                
                if not is_valid:
                    await self._send_raw_message(
                        websocket,
                        create_error_message("INVALID_AUTH", "Invalid authentication message", {"errors": errors})
                    )
                    return False
                
                # Authenticate with middleware
                auth_result = await self.auth_middleware.authenticate(auth_data, connection_id)
                
                if auth_result.success:
                    # Update connection info
                    conn_info = self.connection_info[connection_id]
                    conn_info.is_authenticated = True
                    conn_info.user_id = auth_result.user_id
                    conn_info.permissions = auth_result.permissions
                    
                    # Send success message
                    await self._send_raw_message(
                        websocket,
                        create_status_message(StreamStatus.CONNECTED, {
                            "authenticated": True,
                            "user_id": auth_result.user_id,
                            "permissions": auth_result.permissions
                        })
                    )
                    
                    return True
                else:
                    # Send failure message
                    await self._send_raw_message(
                        websocket,
                        create_error_message("AUTH_FAILED", auth_result.error_message or "Authentication failed")
                    )
                    return False
                    
            except json.JSONDecodeError:
                await self._send_raw_message(
                    websocket,
                    create_error_message("INVALID_JSON", "Invalid JSON in authentication message")
                )
                return False
                
        except asyncio.TimeoutError:
            await self._send_raw_message(
                websocket,
                create_error_message("AUTH_TIMEOUT", "Authentication timeout")
            )
            return False
    
    async def _message_loop(self, connection_id: str, websocket: WebSocketServerProtocol) -> None:
        """Main message handling loop for connection."""
        connection_info = self.connection_info[connection_id]
        
        try:
            async for raw_message in websocket:
                try:
                    # Update connection statistics
                    connection_info.messages_received += 1
                    connection_info.last_heartbeat = datetime.utcnow()
                    self.total_messages += 1
                    
                    if self.config.log_messages:
                        self.logger.debug(f"Received message from {connection_id}: {raw_message[:200]}...")
                    
                    # Parse message
                    try:
                        message_data = json.loads(raw_message)
                    except json.JSONDecodeError:
                        await self._send_message_to_connection(
                            connection_id,
                            create_error_message("INVALID_JSON", "Invalid JSON message")
                        )
                        continue
                    
                    # Validate message
                    is_valid, errors = MessageValidator.validate_message(message_data)
                    if not is_valid:
                        await self._send_message_to_connection(
                            connection_id,
                            create_error_message("INVALID_MESSAGE", "Invalid message format", {"errors": errors})
                        )
                        continue
                    
                    # Convert to TranscriptMessage
                    try:
                        message = TranscriptMessage.from_dict(message_data)
                    except Exception as e:
                        await self._send_message_to_connection(
                            connection_id,
                            create_error_message("MESSAGE_PARSE_ERROR", f"Failed to parse message: {str(e)}")
                        )
                        continue
                    
                    # Handle message
                    await self._handle_message(connection_id, message)
                    
                except Exception as e:
                    self.logger.error(f"Error handling message from {connection_id}: {e}")
                    await self._send_message_to_connection(
                        connection_id,
                        create_error_message("MESSAGE_HANDLER_ERROR", "Error processing message")
                    )
                    
        except ConnectionClosed:
            pass  # Normal connection close
        except Exception as e:
            self.logger.error(f"Error in message loop for {connection_id}: {e}")
    
    async def _handle_message(self, connection_id: str, message: TranscriptMessage) -> None:
        """Handle received message."""
        # Get handlers for message type
        handlers = self.message_handlers.get(message.message_type, [])
        
        if not handlers:
            self.logger.warning(f"No handlers for message type {message.message_type.value}")
            return
        
        # Execute handlers
        for handler in handlers:
            try:
                await handler(connection_id, message)
            except Exception as e:
                self.logger.error(f"Handler error for {message.message_type.value}: {e}")
    
    async def _send_message_to_connection(self, 
                                        connection_id: str, 
                                        message: TranscriptMessage) -> bool:
        """Send message to specific connection."""
        if connection_id not in self.connections:
            return False
        
        websocket = self.connections[connection_id]
        return await self._send_raw_message(websocket, message)
    
    async def _send_raw_message(self, 
                              websocket: WebSocketServerProtocol, 
                              message: TranscriptMessage) -> bool:
        """Send raw message to websocket."""
        try:
            message_json = json.dumps(message.to_dict())
            await websocket.send(message_json)
            return True
        except ConnectionClosed:
            return False
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False
    
    async def _cleanup_connection(self, connection_id: str) -> None:
        """Clean up connection resources."""
        # Remove from connections
        if connection_id in self.connections:
            del self.connections[connection_id]
        
        # Clean up connection info
        connection_info = self.connection_info.get(connection_id)
        if connection_info:
            # Remove from IP tracking
            ip_address = connection_info.ip_address
            if ip_address in self.ip_connections:
                self.ip_connections[ip_address].discard(connection_id)
                if not self.ip_connections[ip_address]:
                    del self.ip_connections[ip_address]
            
            del self.connection_info[connection_id]
        
        # Remove from session subscriptions
        for session_id, subscribers in list(self.broadcast_subscribers.items()):
            subscribers.discard(connection_id)
            if not subscribers:
                del self.broadcast_subscribers[session_id]
        
        self.logger.debug(f"Cleaned up connection {connection_id}")
    
    async def _disconnect_all_clients(self) -> None:
        """Disconnect all clients gracefully."""
        disconnect_tasks = []
        
        for connection_id, websocket in list(self.connections.items()):
            task = asyncio.create_task(
                websocket.close(code=1001, reason="Server shutdown")
            )
            disconnect_tasks.append(task)
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        # Clear all connections
        self.connections.clear()
        self.connection_info.clear()
        self.ip_connections.clear()
        self.broadcast_subscribers.clear()
    
    def _start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        # Heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat_task())
        self.background_tasks.add(heartbeat_task)
        heartbeat_task.add_done_callback(self.background_tasks.discard)
        
        # Connection cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_task())
        self.background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self.background_tasks.discard)
    
    async def _stop_background_tasks(self) -> None:
        """Stop all background tasks."""
        for task in self.background_tasks:
            task.cancel()
        
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.background_tasks.clear()
    
    async def _heartbeat_task(self) -> None:
        """Background task for sending heartbeats."""
        while self.is_running:
            try:
                # Send heartbeat to all authenticated connections
                heartbeat_tasks = []
                for connection_id, info in list(self.connection_info.items()):
                    if info.is_authenticated:
                        heartbeat_msg = create_heartbeat_message(connection_id)
                        task = asyncio.create_task(
                            self._send_message_to_connection(connection_id, heartbeat_msg)
                        )
                        heartbeat_tasks.append(task)
                
                if heartbeat_tasks:
                    await asyncio.gather(*heartbeat_tasks, return_exceptions=True)
                
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"Error in heartbeat task: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _cleanup_task(self) -> None:
        """Background task for cleaning up stale connections."""
        while self.is_running:
            try:
                stale_connections = []
                cutoff_time = datetime.utcnow() - timedelta(seconds=self.config.connection_timeout)
                
                for connection_id, info in list(self.connection_info.items()):
                    if info.last_heartbeat < cutoff_time:
                        stale_connections.append(connection_id)
                
                # Close stale connections
                for connection_id in stale_connections:
                    if connection_id in self.connections:
                        websocket = self.connections[connection_id]
                        try:
                            await websocket.close(code=1001, reason="Connection timeout")
                        except Exception:
                            pass  # Connection might already be closed
                        
                        await self._cleanup_connection(connection_id)
                        self.logger.info(f"Cleaned up stale connection {connection_id}")
                
                await asyncio.sleep(60)  # Run cleanup every minute
                
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(10)
    
    # Default message handlers
    async def _handle_auth_message(self, connection_id: str, message: TranscriptMessage) -> None:
        """Handle authentication message (already handled in connection setup)."""
        pass
    
    async def _handle_heartbeat(self, connection_id: str, message: TranscriptMessage) -> None:
        """Handle heartbeat message."""
        if connection_id in self.connection_info:
            self.connection_info[connection_id].last_heartbeat = datetime.utcnow()
    
    async def _handle_connect_message(self, connection_id: str, message: TranscriptMessage) -> None:
        """Handle explicit connect message."""
        # Send current server status
        stats = self.get_connection_stats()
        await self._send_message_to_connection(
            connection_id,
            create_status_message(StreamStatus.CONNECTED, stats)
        )
    
    async def _handle_disconnect_message(self, connection_id: str, message: TranscriptMessage) -> None:
        """Handle disconnect message."""
        if connection_id in self.connections:
            websocket = self.connections[connection_id]
            await websocket.close(code=1000, reason="Client requested disconnect")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_server()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_server()