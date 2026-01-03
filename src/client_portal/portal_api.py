"""
Client Portal FastAPI Application

Main API endpoints for client portal functionality including authentication,
document management, messaging, notifications, and real-time features.
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import redis
import json
from pathlib import Path
import io

from ..core.config import get_database_session, get_redis_client
from .auth_manager import ClientAuthManager
from .document_manager import ClientDocumentManager
from .communication_manager import CommunicationManager
from .notification_manager import NotificationManager
from .realtime_manager import RealtimeManager
from .case_manager import ClientCaseManager
from .billing_manager import ClientBillingManager
from .appointment_manager import ClientAppointmentManager
from .audit_manager import ClientAuditManager
from .websocket_handler import ClientWebSocketHandler
from .models import (
    DocumentType, NotificationType, NotificationPriority,
    MessageStatus, CaseStatus, InvoiceStatus, AppointmentStatus
)

# Pydantic models for request/response
from pydantic import BaseModel, EmailStr
from enum import Enum


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    company_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    two_factor_code: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str

class DocumentUploadMetadata(BaseModel):
    document_type: DocumentType
    title: Optional[str] = None
    description: Optional[str] = None
    case_id: Optional[int] = None
    tags: Optional[List[str]] = []
    is_confidential: bool = False

class MessageRequest(BaseModel):
    recipient_type: str
    subject: str
    content: str
    case_id: Optional[int] = None
    thread_id: Optional[str] = None
    parent_message_id: Optional[int] = None

class NotificationPreferences(BaseModel):
    email_notifications: bool = True
    sms_notifications: bool = False
    push_notifications: bool = True
    case_updates: bool = True
    document_notifications: bool = True
    message_notifications: bool = True
    appointment_reminders: bool = True


class ClientPortalAPI:
    """Main FastAPI application for client portal."""
    
    def __init__(self, jwt_secret: str, storage_path: str, email_config: Dict = None):
        self.app = FastAPI(
            title="Legal AI Client Portal",
            description="Secure client portal for legal document sharing and communication",
            version="1.0.0"
        )
        
        self.jwt_secret = jwt_secret
        self.storage_path = storage_path
        self.email_config = email_config or {}
        
        # Security
        self.security = HTTPBearer()
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize managers (will be done per request)
        self.realtime_manager = None
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all API routes."""
        
        # Authentication routes
        @self.app.post("/auth/register", tags=["Authentication"])
        async def register(
            request: RegisterRequest,
            db: Session = Depends(get_database_session)
        ):
            auth_manager = ClientAuthManager(db, self.jwt_secret)
            
            result = auth_manager.register_client(
                email=request.email,
                password=request.password,
                first_name=request.first_name,
                last_name=request.last_name,
                phone_number=request.phone_number,
                company_name=request.company_name
            )
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            return {
                "success": True,
                "message": "Registration successful. Please check your email for verification.",
                "user_id": result['user_id']
            }
        
        @self.app.post("/auth/verify-email", tags=["Authentication"])
        async def verify_email(
            verification_token: str,
            db: Session = Depends(get_database_session)
        ):
            auth_manager = ClientAuthManager(db, self.jwt_secret)
            result = auth_manager.verify_email(verification_token)
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            return result
        
        @self.app.post("/auth/login", tags=["Authentication"])
        async def login(
            request: LoginRequest,
            user_ip: str = "0.0.0.0",  # Get from request headers in production
            user_agent: str = "Unknown",
            db: Session = Depends(get_database_session)
        ):
            auth_manager = ClientAuthManager(db, self.jwt_secret)
            
            result = auth_manager.authenticate_client(
                email=request.email,
                password=request.password,
                ip_address=user_ip,
                user_agent=user_agent,
                two_factor_code=request.two_factor_code
            )
            
            if not result['success']:
                if result.get('requires_2fa'):
                    raise HTTPException(status_code=202, detail=result)
                raise HTTPException(status_code=401, detail=result['error'])
            
            return {
                "success": True,
                "user": result['user'],
                "access_token": result['access_token'],
                "refresh_token": result['refresh_token'],
                "session_id": result['session_id']
            }
        
        @self.app.post("/auth/logout", tags=["Authentication"])
        async def logout(
            session_id: str,
            user_ip: str = "0.0.0.0",
            db: Session = Depends(get_database_session),
            current_user: dict = Depends(self._get_current_user)
        ):
            auth_manager = ClientAuthManager(db, self.jwt_secret)
            result = auth_manager.logout_client(session_id, user_ip)
            
            return result
        
        @self.app.post("/auth/change-password", tags=["Authentication"])
        async def change_password(
            request: ChangePasswordRequest,
            db: Session = Depends(get_database_session),
            current_user: dict = Depends(self._get_current_user)
        ):
            auth_manager = ClientAuthManager(db, self.jwt_secret)
            result = auth_manager.change_password(
                user_id=current_user['user_id'],
                current_password=request.current_password,
                new_password=request.new_password
            )
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            return result
        
        # Document routes
        @self.app.post("/documents/upload", tags=["Documents"])
        async def upload_document(
            file: UploadFile = File(...),
            metadata: str = None,  # JSON string
            user_ip: str = "0.0.0.0",
            db: Session = Depends(get_database_session),
            current_user: dict = Depends(self._get_current_user)
        ):
            doc_manager = ClientDocumentManager(db, self.storage_path)
            
            # Parse metadata
            if metadata:
                try:
                    metadata_dict = json.loads(metadata)
                    doc_metadata = DocumentUploadMetadata(**metadata_dict)
                except:
                    raise HTTPException(status_code=400, detail="Invalid metadata format")
            else:
                doc_metadata = DocumentUploadMetadata(document_type=DocumentType.OTHER)
            
            result = doc_manager.upload_document(
                client_id=current_user['user_id'],
                file_data=file.file,
                original_filename=file.filename,
                document_type=doc_metadata.document_type,
                title=doc_metadata.title,
                description=doc_metadata.description,
                case_id=doc_metadata.case_id,
                tags=doc_metadata.tags,
                is_confidential=doc_metadata.is_confidential,
                uploaded_by=f"client_{current_user['user_id']}",
                ip_address=user_ip
            )
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            return result
        
        @self.app.get("/documents", tags=["Documents"])
        async def get_documents(
            document_type: Optional[DocumentType] = None,
            case_id: Optional[int] = None,
            search: Optional[str] = None,
            page: int = 1,
            limit: int = 20,
            db: Session = Depends(get_database_session),
            current_user: dict = Depends(self._get_current_user)
        ):
            doc_manager = ClientDocumentManager(db, self.storage_path)
            
            result = doc_manager.get_client_documents(
                client_id=current_user['user_id'],
                document_type=document_type,
                case_id=case_id,
                search_query=search,
                page=page,
                limit=limit
            )
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            return result
        
        @self.app.get("/documents/{document_id}", tags=["Documents"])
        async def get_document(
            document_id: str,
            user_ip: str = "0.0.0.0",
            db: Session = Depends(get_database_session),
            current_user: dict = Depends(self._get_current_user)
        ):
            doc_manager = ClientDocumentManager(db, self.storage_path)
            
            result = doc_manager.get_document(
                document_id=document_id,
                client_id=current_user['user_id'],
                ip_address=user_ip
            )
            
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            
            return result
        
        @self.app.get("/documents/{document_id}/download", tags=["Documents"])
        async def download_document(
            document_id: str,
            user_ip: str = "0.0.0.0",
            db: Session = Depends(get_database_session),
            current_user: dict = Depends(self._get_current_user)
        ):
            doc_manager = ClientDocumentManager(db, self.storage_path)
            
            result = doc_manager.download_document(
                document_id=document_id,
                client_id=current_user['user_id'],
                ip_address=user_ip
            )
            
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            
            file_path = Path(result['file_path'])
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            return FileResponse(
                path=str(file_path),
                filename=result['filename'],
                media_type=result['mime_type']
            )
        
        # Messaging routes
        @self.app.post("/messages", tags=["Messages"])
        async def send_message(
            request: MessageRequest,
            db: Session = Depends(get_database_session),
            current_user: dict = Depends(self._get_current_user)
        ):
            comm_manager = CommunicationManager(db)
            
            result = await comm_manager.send_message(
                sender_id=current_user['user_id'],
                recipient_type=request.recipient_type,
                subject=request.subject,
                content=request.content,
                case_id=request.case_id,
                thread_id=request.thread_id,
                parent_message_id=request.parent_message_id
            )
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            return result
        
        @self.app.get("/messages", tags=["Messages"])
        async def get_messages(
            thread_id: Optional[str] = None,
            case_id: Optional[int] = None,
            status: Optional[MessageStatus] = None,
            page: int = 1,
            limit: int = 20,
            db: Session = Depends(get_database_session),
            current_user: dict = Depends(self._get_current_user)
        ):
            comm_manager = CommunicationManager(db)
            
            result = await comm_manager.get_client_messages(
                client_id=current_user['user_id'],
                thread_id=thread_id,
                case_id=case_id,
                status=status,
                page=page,
                limit=limit
            )
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            return result
        
        # Notification routes
        @self.app.get("/notifications", tags=["Notifications"])
        async def get_notifications(
            notification_type: Optional[NotificationType] = None,
            is_read: Optional[bool] = None,
            priority: Optional[NotificationPriority] = None,
            page: int = 1,
            limit: int = 20,
            db: Session = Depends(get_database_session),
            redis_client: redis.Redis = Depends(get_redis_client),
            current_user: dict = Depends(self._get_current_user)
        ):
            notification_manager = NotificationManager(db, redis_client, self.email_config)
            
            result = await notification_manager.get_client_notifications(
                client_id=current_user['user_id'],
                notification_type=notification_type,
                is_read=is_read,
                priority=priority,
                page=page,
                limit=limit
            )
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            return result
        
        @self.app.post("/notifications/{notification_id}/mark-read", tags=["Notifications"])
        async def mark_notification_read(
            notification_id: str,
            db: Session = Depends(get_database_session),
            redis_client: redis.Redis = Depends(get_redis_client),
            current_user: dict = Depends(self._get_current_user)
        ):
            notification_manager = NotificationManager(db, redis_client, self.email_config)
            
            result = await notification_manager.mark_as_read(
                notification_id=notification_id,
                client_id=current_user['user_id']
            )
            
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            
            return result
        
        # Case routes
        @self.app.get("/cases", tags=["Cases"])
        async def get_cases(
            status: Optional[CaseStatus] = None,
            page: int = 1,
            limit: int = 20,
            db: Session = Depends(get_database_session),
            current_user: dict = Depends(self._get_current_user)
        ):
            case_manager = ClientCaseManager(db)
            
            result = await case_manager.get_client_cases(
                client_id=current_user['user_id'],
                status=status,
                page=page,
                limit=limit
            )
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            return result
        
        @self.app.get("/cases/{case_id}", tags=["Cases"])
        async def get_case(
            case_id: str,
            db: Session = Depends(get_database_session),
            current_user: dict = Depends(self._get_current_user)
        ):
            case_manager = ClientCaseManager(db)
            
            result = await case_manager.get_case_details(
                case_id=case_id,
                client_id=current_user['user_id']
            )
            
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            
            return result
        
        # Dashboard route
        @self.app.get("/dashboard", tags=["Dashboard"])
        async def get_dashboard(
            db: Session = Depends(get_database_session),
            redis_client: redis.Redis = Depends(get_redis_client),
            current_user: dict = Depends(self._get_current_user)
        ):
            # Gather dashboard data from various managers
            doc_manager = ClientDocumentManager(db, self.storage_path)
            notification_manager = NotificationManager(db, redis_client, self.email_config)
            case_manager = ClientCaseManager(db)
            
            # Get statistics
            doc_stats = doc_manager.get_document_statistics(current_user['user_id'])
            notification_stats = await notification_manager.get_notification_statistics(current_user['user_id'])
            case_stats = await case_manager.get_case_statistics(current_user['user_id'])
            
            return {
                'success': True,
                'dashboard': {
                    'documents': doc_stats.get('statistics', {}) if doc_stats['success'] else {},
                    'notifications': notification_stats.get('statistics', {}) if notification_stats['success'] else {},
                    'cases': case_stats.get('statistics', {}) if case_stats['success'] else {},
                    'last_updated': datetime.utcnow().isoformat()
                }
            }
        
        # WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(
            websocket: WebSocket,
            token: str,
            db: Session = Depends(get_database_session),
            redis_client: redis.Redis = Depends(get_redis_client)
        ):
            # Validate token and get user
            try:
                auth_manager = ClientAuthManager(db, self.jwt_secret)
                # Implement token validation here
                user_data = self._decode_token(token)  # You'll need to implement this
                
                if not self.realtime_manager:
                    self.realtime_manager = RealtimeManager(db, redis_client)
                    await self.realtime_manager.start()
                
                # Connect client
                connection_id = await self.realtime_manager.connect_client(
                    websocket=websocket,
                    client_id=user_data['user_id'],
                    session_id=user_data.get('session_id', ''),
                    metadata={'ip_address': '0.0.0.0'}  # Get from request
                )
                
                try:
                    while True:
                        # Handle incoming messages
                        data = await websocket.receive_text()
                        message = json.loads(data)
                        
                        # Process different message types
                        if message.get('type') == 'ping':
                            await websocket.send_text(json.dumps({
                                'type': 'pong',
                                'timestamp': datetime.utcnow().isoformat()
                            }))
                        
                except WebSocketDisconnect:
                    pass
                finally:
                    await self.realtime_manager.disconnect_client(
                        connection_id, "websocket_closed"
                    )
                    
            except Exception as e:
                await websocket.close(code=1008, reason=f"Authentication failed: {str(e)}")
    
    async def _get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        db: Session = Depends(get_database_session)
    ) -> dict:
        """Extract current user from JWT token."""
        try:
            auth_manager = ClientAuthManager(db, self.jwt_secret)
            # Implement JWT validation here
            token_data = self._decode_token(credentials.credentials)
            return token_data
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    def _decode_token(self, token: str) -> dict:
        """Decode and validate JWT token."""
        # Implement JWT decoding using your JWT manager
        # This is a placeholder - implement actual JWT validation
        return {
            'user_id': 1,
            'client_id': 'client_123',
            'email': 'test@example.com',
            'session_id': 'session_123'
        }


def create_client_portal_app(
    jwt_secret: str,
    storage_path: str,
    email_config: Dict = None
) -> FastAPI:
    """Factory function to create client portal FastAPI app."""
    portal_api = ClientPortalAPI(jwt_secret, storage_path, email_config)
    return portal_api.app