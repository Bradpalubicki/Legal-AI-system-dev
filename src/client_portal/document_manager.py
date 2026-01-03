"""
Client Portal Document Manager

Handles secure document sharing, access control, version management,
and document lifecycle for client portal users.
"""

import os
import hashlib
import magic
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, BinaryIO
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import uuid
import shutil
from pathlib import Path

from .models import (
    ClientDocument, ClientUser, ClientCase, DocumentStatus, 
    DocumentType, ClientAuditLog, AuditAction
)
from .audit_manager import ClientAuditManager


class ClientDocumentManager:
    """Manages client document operations with security and access control."""
    
    def __init__(self, db_session: Session, storage_path: str, max_file_size: int = 50 * 1024 * 1024):
        self.db = db_session
        self.storage_path = Path(storage_path)
        self.max_file_size = max_file_size
        self.audit_manager = ClientAuditManager(db_session)
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Allowed file types and their MIME types
        self.allowed_types = {
            'pdf': ['application/pdf'],
            'doc': ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'txt': ['text/plain'],
            'rtf': ['application/rtf'],
            'jpg': ['image/jpeg'],
            'png': ['image/png'],
            'gif': ['image/gif'],
            'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
            'csv': ['text/csv']
        }
    
    def upload_document(
        self,
        client_id: int,
        file_data: BinaryIO,
        original_filename: str,
        document_type: DocumentType,
        title: Optional[str] = None,
        description: Optional[str] = None,
        case_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        is_confidential: bool = False,
        uploaded_by: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a new document for client."""
        try:
            # Validate client
            client = self.db.query(ClientUser).filter(ClientUser.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            # Read and validate file
            file_content = file_data.read()
            file_size = len(file_content)
            
            if file_size > self.max_file_size:
                return {'success': False, 'error': f'File too large. Max size: {self.max_file_size // (1024*1024)}MB'}
            
            # Detect MIME type
            mime_type = magic.from_buffer(file_content, mime=True)
            
            # Validate file type
            if not self._is_allowed_file_type(mime_type, original_filename):
                return {'success': False, 'error': 'File type not allowed'}
            
            # Generate secure filename
            file_extension = Path(original_filename).suffix.lower()
            secure_filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # Create document record
            document = ClientDocument(
                client_id=client_id,
                filename=secure_filename,
                original_filename=original_filename,
                file_size=file_size,
                mime_type=mime_type,
                document_type=document_type,
                title=title or original_filename,
                description=description,
                tags=tags or [],
                case_id=case_id,
                is_confidential=is_confidential,
                status=DocumentStatus.UPLOADED,
                uploaded_by=uploaded_by
            )
            
            # Create client-specific storage directory
            client_dir = self.storage_path / f"client_{client_id}"
            client_dir.mkdir(exist_ok=True)
            
            # Store file
            file_path = client_dir / secure_filename
            document.file_path = str(file_path)
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Generate file hash for integrity
            file_hash = hashlib.sha256(file_content).hexdigest()
            document.metadata = {'file_hash': file_hash, 'upload_ip': ip_address}
            
            self.db.add(document)
            self.db.commit()
            
            # Log audit event
            self.audit_manager.log_event(
                user_id=client_id,
                action=AuditAction.DOCUMENT_VIEW,
                resource_type='document',
                resource_id=document.document_id,
                ip_address=ip_address,
                action_details={
                    'action': 'upload',
                    'filename': original_filename,
                    'file_size': file_size,
                    'document_type': document_type.value
                }
            )
            
            return {
                'success': True,
                'document': document.to_dict(),
                'message': 'Document uploaded successfully'
            }
            
        except Exception as e:
            self.db.rollback()
            # Clean up file if it was created
            try:
                if 'file_path' in locals() and file_path.exists():
                    file_path.unlink()
            except:
                pass
            return {'success': False, 'error': f'Upload failed: {str(e)}'}
    
    def get_client_documents(
        self,
        client_id: int,
        document_type: Optional[DocumentType] = None,
        case_id: Optional[int] = None,
        status: Optional[DocumentStatus] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get documents accessible to client."""
        try:
            # Build query
            query = self.db.query(ClientDocument).filter(
                ClientDocument.client_id == client_id
            )
            
            # Apply filters
            if document_type:
                query = query.filter(ClientDocument.document_type == document_type)
            
            if case_id:
                query = query.filter(ClientDocument.case_id == case_id)
            
            if status:
                query = query.filter(ClientDocument.status == status)
            else:
                # Exclude deleted documents by default
                query = query.filter(ClientDocument.status != DocumentStatus.DELETED)
            
            # Search functionality
            if search_query:
                search = f"%{search_query}%"
                query = query.filter(
                    or_(
                        ClientDocument.title.ilike(search),
                        ClientDocument.description.ilike(search),
                        ClientDocument.original_filename.ilike(search)
                    )
                )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            documents = query.order_by(desc(ClientDocument.created_at)).offset(
                (page - 1) * limit
            ).limit(limit).all()
            
            return {
                'success': True,
                'documents': [doc.to_dict() for doc in documents],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve documents: {str(e)}'}
    
    def get_document(self, document_id: str, client_id: int, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Get specific document if client has access."""
        try:
            document = self.db.query(ClientDocument).filter(
                and_(
                    ClientDocument.document_id == document_id,
                    ClientDocument.client_id == client_id,
                    ClientDocument.status != DocumentStatus.DELETED
                )
            ).first()
            
            if not document:
                return {'success': False, 'error': 'Document not found or access denied'}
            
            # Update view tracking
            document.view_count = (document.view_count or 0) + 1
            document.last_viewed = datetime.utcnow()
            
            # Log audit event
            self.audit_manager.log_event(
                user_id=client_id,
                action=AuditAction.DOCUMENT_VIEW,
                resource_type='document',
                resource_id=document_id,
                ip_address=ip_address,
                action_details={
                    'filename': document.original_filename,
                    'view_count': document.view_count
                }
            )
            
            self.db.commit()
            
            return {
                'success': True,
                'document': document.to_dict()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve document: {str(e)}'}
    
    def download_document(self, document_id: str, client_id: int, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Download document if client has access and download is allowed."""
        try:
            document = self.db.query(ClientDocument).filter(
                and_(
                    ClientDocument.document_id == document_id,
                    ClientDocument.client_id == client_id,
                    ClientDocument.status != DocumentStatus.DELETED
                )
            ).first()
            
            if not document:
                return {'success': False, 'error': 'Document not found or access denied'}
            
            if not document.download_allowed:
                return {'success': False, 'error': 'Download not permitted for this document'}
            
            # Check if file exists
            file_path = Path(document.file_path)
            if not file_path.exists():
                return {'success': False, 'error': 'Document file not found'}
            
            # Update download tracking
            document.download_count = (document.download_count or 0) + 1
            document.last_downloaded = datetime.utcnow()
            
            # Log audit event
            self.audit_manager.log_event(
                user_id=client_id,
                action=AuditAction.DOCUMENT_DOWNLOAD,
                resource_type='document',
                resource_id=document_id,
                ip_address=ip_address,
                action_details={
                    'filename': document.original_filename,
                    'download_count': document.download_count
                }
            )
            
            self.db.commit()
            
            return {
                'success': True,
                'file_path': str(file_path),
                'filename': document.original_filename,
                'mime_type': document.mime_type,
                'file_size': document.file_size
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Download failed: {str(e)}'}
    
    def update_document(
        self,
        document_id: str,
        client_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update document metadata (limited fields for clients)."""
        try:
            document = self.db.query(ClientDocument).filter(
                and_(
                    ClientDocument.document_id == document_id,
                    ClientDocument.client_id == client_id,
                    ClientDocument.status != DocumentStatus.DELETED
                )
            ).first()
            
            if not document:
                return {'success': False, 'error': 'Document not found or access denied'}
            
            # Store old values for audit
            old_values = {
                'title': document.title,
                'description': document.description,
                'tags': document.tags
            }
            
            # Update allowed fields
            if title is not None:
                document.title = title
            if description is not None:
                document.description = description
            if tags is not None:
                document.tags = tags
            
            document.updated_at = datetime.utcnow()
            
            # Log audit event
            new_values = {
                'title': document.title,
                'description': document.description,
                'tags': document.tags
            }
            
            self.audit_manager.log_event(
                user_id=client_id,
                action=AuditAction.PROFILE_UPDATED,
                resource_type='document',
                resource_id=document_id,
                ip_address=ip_address,
                action_details={'action': 'update'},
                old_values=old_values,
                new_values=new_values
            )
            
            self.db.commit()
            
            return {
                'success': True,
                'document': document.to_dict(),
                'message': 'Document updated successfully'
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Update failed: {str(e)}'}
    
    def delete_document(self, document_id: str, client_id: int, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Soft delete document (clients can only request deletion)."""
        try:
            document = self.db.query(ClientDocument).filter(
                and_(
                    ClientDocument.document_id == document_id,
                    ClientDocument.client_id == client_id,
                    ClientDocument.status != DocumentStatus.DELETED
                )
            ).first()
            
            if not document:
                return {'success': False, 'error': 'Document not found or access denied'}
            
            # For client portal, mark for deletion rather than immediate delete
            document.status = DocumentStatus.ARCHIVED
            document.updated_at = datetime.utcnow()
            
            # Log audit event
            self.audit_manager.log_event(
                user_id=client_id,
                action=AuditAction.PROFILE_UPDATED,
                resource_type='document',
                resource_id=document_id,
                ip_address=ip_address,
                action_details={
                    'action': 'delete_request',
                    'filename': document.original_filename
                }
            )
            
            self.db.commit()
            
            return {
                'success': True,
                'message': 'Document deletion requested successfully'
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Deletion failed: {str(e)}'}
    
    def search_documents(
        self,
        client_id: int,
        query: str,
        document_types: Optional[List[DocumentType]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Advanced document search for client."""
        try:
            # Build base query
            base_query = self.db.query(ClientDocument).filter(
                and_(
                    ClientDocument.client_id == client_id,
                    ClientDocument.status != DocumentStatus.DELETED
                )
            )
            
            # Text search across multiple fields
            search_terms = query.lower().split()
            for term in search_terms:
                search_pattern = f"%{term}%"
                base_query = base_query.filter(
                    or_(
                        ClientDocument.title.ilike(search_pattern),
                        ClientDocument.description.ilike(search_pattern),
                        ClientDocument.original_filename.ilike(search_pattern)
                    )
                )
            
            # Filter by document types
            if document_types:
                base_query = base_query.filter(ClientDocument.document_type.in_(document_types))
            
            # Date range filter
            if date_from:
                base_query = base_query.filter(ClientDocument.created_at >= date_from)
            if date_to:
                base_query = base_query.filter(ClientDocument.created_at <= date_to)
            
            # Get total count
            total_count = base_query.count()
            
            # Apply pagination and ordering
            documents = base_query.order_by(desc(ClientDocument.created_at)).offset(
                (page - 1) * limit
            ).limit(limit).all()
            
            return {
                'success': True,
                'documents': [doc.to_dict() for doc in documents],
                'search_query': query,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Search failed: {str(e)}'}
    
    def get_document_statistics(self, client_id: int) -> Dict[str, Any]:
        """Get document statistics for client dashboard."""
        try:
            # Basic counts
            total_docs = self.db.query(ClientDocument).filter(
                and_(
                    ClientDocument.client_id == client_id,
                    ClientDocument.status != DocumentStatus.DELETED
                )
            ).count()
            
            # Count by type
            type_counts = {}
            for doc_type in DocumentType:
                count = self.db.query(ClientDocument).filter(
                    and_(
                        ClientDocument.client_id == client_id,
                        ClientDocument.document_type == doc_type,
                        ClientDocument.status != DocumentStatus.DELETED
                    )
                ).count()
                type_counts[doc_type.value] = count
            
            # Count by status
            status_counts = {}
            for status in DocumentStatus:
                if status != DocumentStatus.DELETED:
                    count = self.db.query(ClientDocument).filter(
                        and_(
                            ClientDocument.client_id == client_id,
                            ClientDocument.status == status
                        )
                    ).count()
                    status_counts[status.value] = count
            
            # Recent documents
            recent_docs = self.db.query(ClientDocument).filter(
                and_(
                    ClientDocument.client_id == client_id,
                    ClientDocument.status != DocumentStatus.DELETED
                )
            ).order_by(desc(ClientDocument.created_at)).limit(5).all()
            
            return {
                'success': True,
                'statistics': {
                    'total_documents': total_docs,
                    'by_type': type_counts,
                    'by_status': status_counts,
                    'recent_documents': [doc.to_dict() for doc in recent_docs]
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Statistics failed: {str(e)}'}
    
    def _is_allowed_file_type(self, mime_type: str, filename: str) -> bool:
        """Check if file type is allowed."""
        # Check MIME type
        for allowed_mimes in self.allowed_types.values():
            if mime_type in allowed_mimes:
                return True
        
        # Check file extension as fallback
        file_ext = Path(filename).suffix.lower().lstrip('.')
        return file_ext in self.allowed_types
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def verify_file_integrity(self, document_id: str, client_id: int) -> Dict[str, Any]:
        """Verify file integrity using stored hash."""
        try:
            document = self.db.query(ClientDocument).filter(
                and_(
                    ClientDocument.document_id == document_id,
                    ClientDocument.client_id == client_id
                )
            ).first()
            
            if not document:
                return {'success': False, 'error': 'Document not found'}
            
            file_path = Path(document.file_path)
            if not file_path.exists():
                return {'success': False, 'error': 'Document file not found'}
            
            current_hash = self._calculate_file_hash(file_path)
            stored_hash = document.metadata.get('file_hash') if document.metadata else None
            
            if not stored_hash:
                return {'success': False, 'error': 'No stored hash for verification'}
            
            integrity_valid = current_hash == stored_hash
            
            return {
                'success': True,
                'integrity_valid': integrity_valid,
                'current_hash': current_hash,
                'stored_hash': stored_hash
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Integrity check failed: {str(e)}'}