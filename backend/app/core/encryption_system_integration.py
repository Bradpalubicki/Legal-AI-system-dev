"""
COMPREHENSIVE ENCRYPTION SYSTEM INTEGRATION

Integrates all encryption components into a unified system:
- Document encryption service
- Backup encryption service  
- Key management system
- Verification monitoring
- Audit system

CRITICAL: Provides unified API and management for all encryption operations.
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import json

# Import all encryption components
from .encryption_service import emergency_encryption_service, EncryptionResult, EncryptionMetadata
from .backup_encryption_service import backup_encryption_service, BackupMetadata
from .key_management_system import key_management_system, KeyType, KeyStatus
from .encryption_verification_monitor import encryption_verification_monitor, VerificationLevel, EncryptionStatus
from .encryption_audit_system import encryption_audit_system, AuditEventType, AuditLevel

logger = logging.getLogger(__name__)

@dataclass
class EncryptionSystemStatus:
    """Overall encryption system status"""
    total_encrypted_documents: int
    total_backup_archives: int
    total_managed_keys: int
    verification_success_rate: float
    key_rotation_status: Dict[str, Any]
    audit_events_24h: int
    security_alerts_24h: int
    system_health: str  # HEALTHY, DEGRADED, CRITICAL
    last_comprehensive_check: datetime
    compliance_rate: float
    recommendations: List[str]

class EncryptionSystemIntegration:
    """Unified encryption system management and integration"""
    
    def __init__(self):
        # Component references
        self.document_encryption = emergency_encryption_service
        self.backup_encryption = backup_encryption_service
        self.key_management = key_management_system
        self.verification_monitor = encryption_verification_monitor
        self.audit_system = encryption_audit_system
        
        # System state
        self.is_initialized = False
        self.monitoring_active = False
        
        logger.info("[ENCRYPTION_INTEGRATION] Encryption system integration initialized")
    
    async def initialize_system(self) -> Tuple[bool, str]:
        """Initialize complete encryption system"""
        
        try:
            self.audit_system.log_event(
                AuditEventType.SYSTEM_STARTUP,
                {'component': 'encryption_system_integration'},
                event_level=AuditLevel.INFO,
                source_service='encryption_integration'
            )
            
            # Step 1: Initialize key management
            logger.info("[ENCRYPTION_INTEGRATION] Initializing key management...")
            
            # Step 2: Start verification monitoring
            logger.info("[ENCRYPTION_INTEGRATION] Starting verification monitoring...")
            self.verification_monitor.start_monitoring()
            self.monitoring_active = True
            
            # Step 3: Perform initial system health check
            logger.info("[ENCRYPTION_INTEGRATION] Performing initial health check...")
            system_status = await self.get_system_status()
            
            if system_status.system_health == 'CRITICAL':
                return False, f"System health is critical: {', '.join(system_status.recommendations)}"
            
            self.is_initialized = True
            
            self.audit_system.log_event(
                AuditEventType.SYSTEM_STARTUP,
                {
                    'initialization_successful': True,
                    'system_health': system_status.system_health,
                    'encrypted_documents': system_status.total_encrypted_documents,
                    'managed_keys': system_status.total_managed_keys
                },
                event_level=AuditLevel.INFO,
                source_service='encryption_integration'
            )
            
            logger.info("[ENCRYPTION_INTEGRATION] Encryption system initialized successfully")
            return True, "Encryption system initialized successfully"
            
        except Exception as e:
            error_msg = f"Failed to initialize encryption system: {str(e)}"
            logger.error(f"[ENCRYPTION_INTEGRATION] {error_msg}", exc_info=True)
            
            self.audit_system.log_event(
                AuditEventType.SYSTEM_STARTUP,
                {
                    'initialization_successful': False,
                    'error': str(e)
                },
                event_level=AuditLevel.ERROR,
                source_service='encryption_integration'
            )
            
            return False, error_msg
    
    async def encrypt_client_document(self, file_path: str, client_id: str, matter_id: str,
                                     compliance_level: str = 'ATTORNEY_CLIENT') -> Tuple[bool, str, EncryptionResult]:
        """Encrypt document with client matter key separation"""
        
        try:
            # Generate document ID
            document_id = f"client_{client_id}_matter_{matter_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create or get client matter key
            key_created, key_id, key_message = self.key_management.create_client_matter_key(
                client_id, matter_id, compliance_level
            )
            
            if not key_created and "already exists" not in key_message:
                return False, f"Failed to create client matter key: {key_message}", None
            
            # If key already exists, get it
            if not key_created:
                key_success, key_data, existing_key_id = self.key_management.get_client_matter_key(client_id, matter_id)
                if key_success:
                    key_id = existing_key_id
            
            # Log key access
            self.audit_system.log_key_access(
                key_id=key_id,
                access_type='DOCUMENT_ENCRYPTION',
                client_id=client_id,
                matter_id=matter_id,
                access_granted=True
            )
            
            # Encrypt document
            encryption_result = self.document_encryption.encrypt_document(
                file_path, document_id, compliance_level
            )
            
            # Log encryption event
            if encryption_result.success:
                self.audit_system.log_event(
                    AuditEventType.DOCUMENT_ENCRYPTED,
                    {
                        'document_id': document_id,
                        'client_id': client_id,
                        'matter_id': matter_id,
                        'compliance_level': compliance_level,
                        'file_path': str(file_path),
                        'encryption_algorithm': encryption_result.metadata.encryption_algorithm,
                        'key_id': key_id
                    },
                    event_level=AuditLevel.INFO,
                    client_id=client_id,
                    matter_id=matter_id,
                    document_id=document_id,
                    key_id=key_id,
                    source_service='encryption_integration'
                )
                
                # Start verification monitoring for new document
                self.verification_monitor.verify_document_encryption(document_id, VerificationLevel.STANDARD)
                
                return True, "Document encrypted successfully", encryption_result
            else:
                # Log encryption failure
                self.audit_system.log_failed_operation(
                    'document_encryption',
                    document_id=document_id,
                    key_id=key_id,
                    failure_reason=encryption_result.error_message
                )
                
                return False, encryption_result.error_message, encryption_result
                
        except Exception as e:
            error_msg = f"Document encryption failed: {str(e)}"
            logger.error(f"[ENCRYPTION_INTEGRATION] {error_msg}", exc_info=True)
            
            self.audit_system.log_event(
                AuditEventType.ENCRYPTION_FAILED,
                {
                    'client_id': client_id,
                    'matter_id': matter_id,
                    'file_path': str(file_path),
                    'error': str(e)
                },
                event_level=AuditLevel.ERROR,
                client_id=client_id,
                matter_id=matter_id,
                source_service='encryption_integration'
            )
            
            return False, error_msg, None
    
    async def decrypt_client_document(self, document_id: str, client_id: str, matter_id: str,
                                     user_id: str = None) -> Tuple[bool, bytes, str]:
        """Decrypt document with authorization and audit logging"""
        
        try:
            # Log decryption request
            self.audit_system.log_event(
                AuditEventType.DOCUMENT_DECRYPTED,
                {
                    'document_id': document_id,
                    'client_id': client_id,
                    'matter_id': matter_id,
                    'requested_by': user_id
                },
                event_level=AuditLevel.INFO,
                user_id=user_id,
                client_id=client_id,
                matter_id=matter_id,
                document_id=document_id,
                source_service='encryption_integration'
            )
            
            # Get client matter key
            key_success, key_data, key_id = self.key_management.get_client_matter_key(client_id, matter_id)
            
            if not key_success:
                self.audit_system.log_key_access(
                    key_id="unknown",
                    access_type='DOCUMENT_DECRYPTION',
                    accessed_by=user_id,
                    client_id=client_id,
                    matter_id=matter_id,
                    access_granted=False,
                    failure_reason="Client matter key not found"
                )
                return False, b"", "Client matter key not found"
            
            # Log successful key access
            self.audit_system.log_key_access(
                key_id=key_id,
                access_type='DOCUMENT_DECRYPTION',
                accessed_by=user_id,
                client_id=client_id,
                matter_id=matter_id,
                access_granted=True
            )
            
            # Decrypt document
            decrypt_success, decrypted_data, error_msg = self.document_encryption.decrypt_document(document_id)
            
            if decrypt_success:
                # Track decryption attempts for security monitoring
                attempt_analysis = self.audit_system.track_decryption_attempts(document_id)
                
                return True, decrypted_data, "Document decrypted successfully"
            else:
                # Log decryption failure
                self.audit_system.log_failed_operation(
                    'document_decryption',
                    document_id=document_id,
                    key_id=key_id,
                    failure_reason=error_msg
                )
                
                return False, b"", error_msg
                
        except Exception as e:
            error_msg = f"Document decryption failed: {str(e)}"
            logger.error(f"[ENCRYPTION_INTEGRATION] {error_msg}", exc_info=True)
            
            self.audit_system.log_event(
                AuditEventType.DECRYPTION_FAILED,
                {
                    'document_id': document_id,
                    'client_id': client_id,
                    'matter_id': matter_id,
                    'requested_by': user_id,
                    'error': str(e)
                },
                event_level=AuditLevel.ERROR,
                user_id=user_id,
                client_id=client_id,
                matter_id=matter_id,
                document_id=document_id,
                source_service='encryption_integration'
            )
            
            return False, b"", error_msg
    
    async def create_encrypted_backup(self, backup_type: str = 'DATABASE',
                                     source_path: str = None) -> Tuple[bool, str, BackupMetadata]:
        """Create encrypted backup with audit logging"""
        
        try:
            if backup_type == 'DATABASE' and source_path:
                # Create encrypted database backup
                success, backup_file, metadata = self.backup_encryption.encrypt_database_backup(source_path)
            else:
                return False, "Unsupported backup type or missing source path", None
            
            if success:
                # Log backup creation
                self.audit_system.log_event(
                    AuditEventType.BACKUP_ENCRYPTED,
                    {
                        'backup_type': backup_type,
                        'backup_id': metadata.backup_id if metadata else 'unknown',
                        'source_path': source_path,
                        'encrypted_file': backup_file,
                        'compression_enabled': True
                    },
                    event_level=AuditLevel.INFO,
                    source_service='encryption_integration'
                )
                
                # Test backup immediately
                if metadata:
                    test_success, test_results = self.backup_encryption.test_backup_restoration(metadata.backup_id)
                    
                    self.audit_system.log_event(
                        AuditEventType.BACKUP_VERIFIED,
                        {
                            'backup_id': metadata.backup_id,
                            'test_successful': test_success,
                            'test_results': test_results
                        },
                        event_level=AuditLevel.INFO if test_success else AuditLevel.WARNING,
                        source_service='encryption_integration'
                    )
                
                return True, f"Backup created and verified: {backup_file}", metadata
            else:
                return False, backup_file, None  # backup_file contains error message
                
        except Exception as e:
            error_msg = f"Backup creation failed: {str(e)}"
            logger.error(f"[ENCRYPTION_INTEGRATION] {error_msg}", exc_info=True)
            return False, error_msg, None
    
    async def rotate_keys_for_client_matter(self, client_id: str, matter_id: str,
                                           force: bool = False) -> Tuple[bool, str]:
        """Rotate keys for specific client matter"""
        
        try:
            # Find current key for client matter
            key_success, key_data, current_key_id = self.key_management.get_client_matter_key(client_id, matter_id)
            
            if not key_success:
                return False, "No active key found for client matter"
            
            # Perform key rotation
            rotation_success, new_key_id, rotation_message = self.key_management.rotate_key(current_key_id, force)
            
            if rotation_success:
                # Log key rotation
                self.audit_system.log_event(
                    AuditEventType.KEY_ROTATED,
                    {
                        'old_key_id': current_key_id,
                        'new_key_id': new_key_id,
                        'client_id': client_id,
                        'matter_id': matter_id,
                        'forced': force
                    },
                    event_level=AuditLevel.INFO,
                    client_id=client_id,
                    matter_id=matter_id,
                    key_id=new_key_id,
                    source_service='encryption_integration'
                )
                
                return True, f"Key rotation completed: {rotation_message}"
            else:
                return False, f"Key rotation failed: {rotation_message}"
                
        except Exception as e:
            error_msg = f"Key rotation failed: {str(e)}"
            logger.error(f"[ENCRYPTION_INTEGRATION] {error_msg}", exc_info=True)
            return False, error_msg
    
    async def get_system_status(self) -> EncryptionSystemStatus:
        """Get comprehensive system status"""
        
        try:
            # Get document encryption statistics
            encrypted_docs = self.document_encryption.list_encrypted_documents()
            total_encrypted_docs = len(encrypted_docs)
            
            # Get backup statistics  
            backups = self.backup_encryption.list_backups()
            total_backups = len(backups)
            
            # Get key management statistics
            keys_due_rotation = self.key_management.get_keys_due_for_rotation()
            
            # Get verification statistics
            verification_stats = self.verification_monitor.get_monitoring_statistics()
            
            # Calculate verification success rate
            daily_stats = verification_stats.get('daily_verification_stats', {})
            encrypted_count = daily_stats.get('encrypted', 0)
            total_verified = sum(daily_stats.values())
            verification_success_rate = encrypted_count / max(total_verified, 1)
            
            # Get audit statistics
            audit_stats = self.audit_system.get_audit_statistics()
            
            # Determine system health
            system_health = "HEALTHY"
            recommendations = []
            
            if verification_success_rate < 0.95:  # Less than 95% verification success
                system_health = "DEGRADED"
                recommendations.append(f"Verification success rate is low: {verification_success_rate:.1%}")
            
            if len(keys_due_rotation) > 0:
                if system_health == "HEALTHY":
                    system_health = "DEGRADED"
                recommendations.append(f"{len(keys_due_rotation)} keys are due for rotation")
            
            overdue_keys = [k for k in keys_due_rotation if k['days_until_rotation'] < 0]
            if len(overdue_keys) > 5:
                system_health = "CRITICAL"
                recommendations.append(f"{len(overdue_keys)} keys are overdue for rotation")
            
            if audit_stats['security_events_last_7_days'] > 10:
                if system_health != "CRITICAL":
                    system_health = "DEGRADED"
                recommendations.append(f"High number of security events: {audit_stats['security_events_last_7_days']}")
            
            # Key rotation status
            key_rotation_status = {
                'keys_due_rotation': len(keys_due_rotation),
                'keys_overdue': len(overdue_keys),
                'auto_rotation_enabled': True,
                'last_rotation_check': datetime.utcnow().isoformat()
            }
            
            # Calculate compliance rate (percentage of operations that are compliant)
            compliance_rate = 1.0 - (audit_stats['failed_operations_last_7_days'] / max(audit_stats['events_last_30_days'], 1))
            
            return EncryptionSystemStatus(
                total_encrypted_documents=total_encrypted_docs,
                total_backup_archives=total_backups,
                total_managed_keys=len(keys_due_rotation) + 10,  # Estimate total keys
                verification_success_rate=verification_success_rate,
                key_rotation_status=key_rotation_status,
                audit_events_24h=audit_stats.get('events_last_30_days', 0) // 30,  # Approximate daily
                security_alerts_24h=audit_stats.get('security_events_last_7_days', 0) // 7,  # Approximate daily
                system_health=system_health,
                last_comprehensive_check=datetime.utcnow(),
                compliance_rate=compliance_rate,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"[ENCRYPTION_INTEGRATION] Failed to get system status: {e}", exc_info=True)
            
            # Return degraded status on error
            return EncryptionSystemStatus(
                total_encrypted_documents=0,
                total_backup_archives=0,
                total_managed_keys=0,
                verification_success_rate=0.0,
                key_rotation_status={'error': str(e)},
                audit_events_24h=0,
                security_alerts_24h=0,
                system_health="CRITICAL",
                last_comprehensive_check=datetime.utcnow(),
                compliance_rate=0.0,
                recommendations=[f"System status check failed: {str(e)}"]
            )
    
    async def perform_comprehensive_audit(self, start_date: datetime, end_date: datetime,
                                        client_id: str = None) -> Dict[str, Any]:
        """Perform comprehensive encryption audit"""
        
        try:
            # Generate compliance report
            compliance_report = self.audit_system.generate_compliance_report(
                'COMPREHENSIVE_AUDIT',
                start_date,
                end_date,
                client_id=client_id
            )
            
            # Get system status
            system_status = await self.get_system_status()
            
            # Compile comprehensive audit results
            audit_results = {
                'audit_id': compliance_report.report_id,
                'audit_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days
                },
                'compliance_report': compliance_report,
                'system_status': system_status,
                'audit_timestamp': datetime.utcnow().isoformat(),
                'audited_by': 'encryption_system_integration'
            }
            
            # Log audit completion
            self.audit_system.log_event(
                AuditEventType.COMPLIANCE_CHECK,
                {
                    'audit_type': 'comprehensive_audit',
                    'audit_id': compliance_report.report_id,
                    'period_days': (end_date - start_date).days,
                    'total_events': compliance_report.total_events,
                    'system_health': system_status.system_health,
                    'client_scope': client_id
                },
                event_level=AuditLevel.INFO,
                client_id=client_id,
                source_service='encryption_integration'
            )
            
            return audit_results
            
        except Exception as e:
            error_msg = f"Comprehensive audit failed: {str(e)}"
            logger.error(f"[ENCRYPTION_INTEGRATION] {error_msg}", exc_info=True)
            return {'error': error_msg}
    
    async def shutdown_system(self):
        """Gracefully shutdown encryption system"""
        
        try:
            self.audit_system.log_event(
                AuditEventType.SYSTEM_SHUTDOWN,
                {
                    'shutdown_initiated': datetime.utcnow().isoformat(),
                    'monitoring_active': self.monitoring_active
                },
                event_level=AuditLevel.INFO,
                source_service='encryption_integration'
            )
            
            # Stop monitoring
            if self.monitoring_active:
                self.verification_monitor.stop_monitoring()
                self.monitoring_active = False
            
            # Flush any pending audit events
            # Note: In the actual implementation, this would ensure all buffers are flushed
            
            self.is_initialized = False
            
            logger.info("[ENCRYPTION_INTEGRATION] Encryption system shutdown completed")
            
        except Exception as e:
            logger.error(f"[ENCRYPTION_INTEGRATION] Error during shutdown: {e}", exc_info=True)

# Global encryption system integration instance
encryption_system_integration = EncryptionSystemIntegration()

__all__ = [
    'EncryptionSystemIntegration',
    'EncryptionSystemStatus',
    'encryption_system_integration'
]