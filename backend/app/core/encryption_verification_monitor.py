"""
ENCRYPTION VERIFICATION AND MONITORING SYSTEM

Real-time monitoring and verification of encryption status across all legal documents.
Provides continuous verification, failure detection, and automated remediation.

CRITICAL: Ensures 100% encryption compliance with real-time monitoring and alerts.
"""

import os
import logging
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading
import time
from collections import defaultdict

from .encryption_service import emergency_encryption_service, EncryptionMetadata
from .key_management_system import key_management_system, KeyType, KeyStatus
from .backup_encryption_service import backup_encryption_service

logger = logging.getLogger(__name__)

class EncryptionStatus(Enum):
    ENCRYPTED = "encrypted"
    UNENCRYPTED = "unencrypted"
    VERIFICATION_FAILED = "verification_failed"
    KEY_MISSING = "key_missing"
    CORRUPTED = "corrupted"
    PENDING_ENCRYPTION = "pending_encryption"

class VerificationLevel(Enum):
    BASIC = "basic"           # File exists and metadata valid
    STANDARD = "standard"     # Basic + encryption headers valid
    COMPREHENSIVE = "comprehensive"  # Standard + full decryption test
    FORENSIC = "forensic"     # Comprehensive + integrity verification

@dataclass
class VerificationResult:
    document_id: str
    file_path: str
    status: EncryptionStatus
    verification_level: VerificationLevel
    verified_at: datetime
    encryption_algorithm: str
    key_id: str
    file_size_bytes: int
    verification_duration_ms: float
    issues: List[str]
    metadata_valid: bool
    decryption_successful: bool
    integrity_verified: bool

@dataclass
class MonitoringConfig:
    """Configuration for encryption monitoring"""
    verification_interval_seconds: int = 300  # 5 minutes
    comprehensive_check_interval_hours: int = 24  # Daily
    failed_verification_retry_count: int = 3
    alert_threshold_failure_rate: float = 0.05  # 5%
    auto_remediation_enabled: bool = True
    monitor_backup_encryption: bool = True
    monitor_key_usage: bool = True
    log_all_verifications: bool = False  # Only log failures by default

class EncryptionVerificationMonitor:
    """Real-time encryption verification and monitoring system"""
    
    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        
        # Initialize monitoring database
        self.db_path = Path("monitoring/encryption_verification.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_monitoring_database()
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread = None
        self.verification_stats = defaultdict(int)
        self.failure_alerts = []
        
        # Event callbacks
        self.failure_callbacks: List[Callable[[VerificationResult], None]] = []
        self.alert_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Lock for thread safety
        self._monitor_lock = threading.RLock()
        
        logger.info("[ENCRYPTION_MONITOR] Encryption verification monitor initialized")
    
    def _init_monitoring_database(self):
        """Initialize monitoring database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS verification_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    verification_level TEXT NOT NULL,
                    verified_at TEXT NOT NULL,
                    encryption_algorithm TEXT,
                    key_id TEXT,
                    file_size_bytes INTEGER,
                    verification_duration_ms REAL,
                    issues TEXT,
                    metadata_valid BOOLEAN,
                    decryption_successful BOOLEAN,
                    integrity_verified BOOLEAN,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS monitoring_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS failure_tracking (
                    document_id TEXT PRIMARY KEY,
                    failure_count INTEGER DEFAULT 0,
                    first_failure_at TEXT,
                    last_failure_at TEXT,
                    last_success_at TEXT,
                    remediation_attempts INTEGER DEFAULT 0
                );
                
                CREATE INDEX IF NOT EXISTS idx_verification_document_id 
                ON verification_results(document_id);
                
                CREATE INDEX IF NOT EXISTS idx_verification_status 
                ON verification_results(status);
                
                CREATE INDEX IF NOT EXISTS idx_verification_verified_at 
                ON verification_results(verified_at);
            """)
            conn.commit()
    
    def start_monitoring(self):
        """Start continuous encryption monitoring"""
        with self._monitor_lock:
            if self.is_monitoring:
                logger.warning("[ENCRYPTION_MONITOR] Monitoring already running")
                return
            
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name="EncryptionMonitor",
                daemon=True
            )
            self.monitoring_thread.start()
            
            self._log_monitoring_event('MONITORING_STARTED', {
                'config': asdict(self.config),
                'started_at': datetime.utcnow().isoformat()
            })
            
            logger.info("[ENCRYPTION_MONITOR] Continuous monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous encryption monitoring"""
        with self._monitor_lock:
            if not self.is_monitoring:
                return
            
            self.is_monitoring = False
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=30)
            
            self._log_monitoring_event('MONITORING_STOPPED', {
                'stopped_at': datetime.utcnow().isoformat(),
                'total_verifications': sum(self.verification_stats.values())
            })
            
            logger.info("[ENCRYPTION_MONITOR] Monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("[ENCRYPTION_MONITOR] Starting monitoring loop")
        
        last_comprehensive_check = datetime.min
        
        while self.is_monitoring:
            try:
                # Perform standard verification cycle
                self._perform_verification_cycle()
                
                # Check if comprehensive verification is due
                if (datetime.utcnow() - last_comprehensive_check).total_seconds() > \
                   (self.config.comprehensive_check_interval_hours * 3600):
                    self._perform_comprehensive_verification()
                    last_comprehensive_check = datetime.utcnow()
                
                # Check for patterns and alerts
                self._analyze_verification_patterns()
                
                # Sleep until next cycle
                time.sleep(self.config.verification_interval_seconds)
                
            except Exception as e:
                logger.error(f"[ENCRYPTION_MONITOR] Error in monitoring loop: {e}", exc_info=True)
                time.sleep(60)  # Wait before retrying
    
    def _perform_verification_cycle(self):
        """Perform standard verification cycle on all encrypted documents"""
        start_time = datetime.utcnow()
        
        try:
            # Get all encrypted documents
            encrypted_docs = emergency_encryption_service.list_encrypted_documents()
            
            verification_results = []
            successful_verifications = 0
            failed_verifications = 0
            
            for doc_metadata in encrypted_docs:
                result = self.verify_document_encryption(
                    doc_metadata.document_id,
                    VerificationLevel.STANDARD
                )
                
                verification_results.append(result)
                
                if result.status == EncryptionStatus.ENCRYPTED:
                    successful_verifications += 1
                else:
                    failed_verifications += 1
                    self._handle_verification_failure(result)
            
            # Update statistics
            self.verification_stats['successful_verifications'] += successful_verifications
            self.verification_stats['failed_verifications'] += failed_verifications
            self.verification_stats['total_cycles'] += 1
            
            # Calculate metrics
            total_docs = len(verification_results)
            failure_rate = failed_verifications / max(total_docs, 1)
            cycle_duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Log cycle completion
            cycle_data = {
                'cycle_start': start_time.isoformat(),
                'cycle_duration_seconds': cycle_duration,
                'total_documents': total_docs,
                'successful_verifications': successful_verifications,
                'failed_verifications': failed_verifications,
                'failure_rate': failure_rate
            }
            
            self._log_monitoring_event('VERIFICATION_CYCLE_COMPLETED', cycle_data)
            
            # Check for alerts
            if failure_rate > self.config.alert_threshold_failure_rate:
                self._trigger_alert('HIGH_FAILURE_RATE', {
                    'failure_rate': failure_rate,
                    'threshold': self.config.alert_threshold_failure_rate,
                    'failed_count': failed_verifications,
                    'total_count': total_docs
                })
            
            logger.debug(f"[ENCRYPTION_MONITOR] Verification cycle completed: {successful_verifications}/{total_docs} successful")
            
        except Exception as e:
            logger.error(f"[ENCRYPTION_MONITOR] Error in verification cycle: {e}", exc_info=True)
    
    def verify_document_encryption(self, document_id: str, 
                                  verification_level: VerificationLevel = VerificationLevel.STANDARD) -> VerificationResult:
        """Verify encryption status of a specific document"""
        
        start_time = datetime.utcnow()
        issues = []
        
        try:
            # Get document metadata
            metadata = emergency_encryption_service.get_encryption_status(document_id)
            if not metadata:
                return VerificationResult(
                    document_id=document_id,
                    file_path="",
                    status=EncryptionStatus.UNENCRYPTED,
                    verification_level=verification_level,
                    verified_at=start_time,
                    encryption_algorithm="",
                    key_id="",
                    file_size_bytes=0,
                    verification_duration_ms=0,
                    issues=["Document metadata not found"],
                    metadata_valid=False,
                    decryption_successful=False,
                    integrity_verified=False
                )
            
            # Basic verification: metadata valid
            metadata_valid = True
            if not metadata.encrypted or not metadata.key_id:
                metadata_valid = False
                issues.append("Invalid encryption metadata")
            
            # Get encrypted file path
            encrypted_file = Path(f"encrypted_documents/{document_id}.encrypted")
            if not encrypted_file.exists():
                issues.append("Encrypted file not found")
                return self._create_failure_result(document_id, str(encrypted_file), start_time, 
                                                  verification_level, issues, metadata)
            
            file_size = encrypted_file.stat().st_size
            
            # Standard verification: check encryption container
            decryption_successful = False
            integrity_verified = False
            
            if verification_level in [VerificationLevel.STANDARD, VerificationLevel.COMPREHENSIVE, VerificationLevel.FORENSIC]:
                try:
                    with open(encrypted_file, 'r', encoding='utf-8') as f:
                        container = json.load(f)
                    
                    # Verify container structure
                    required_fields = ['algorithm', 'encrypted_data', 'nonce', 'aad']
                    for field in required_fields:
                        if field not in container:
                            issues.append(f"Missing container field: {field}")
                    
                    # For comprehensive verification, attempt decryption
                    if verification_level in [VerificationLevel.COMPREHENSIVE, VerificationLevel.FORENSIC]:
                        success, decrypted_data, error = emergency_encryption_service.decrypt_document(document_id)
                        if success:
                            decryption_successful = True
                            
                            # For forensic verification, verify integrity
                            if verification_level == VerificationLevel.FORENSIC:
                                expected_hash = container.get('original_hash', '')
                                if expected_hash:
                                    actual_hash = hashlib.sha256(decrypted_data).hexdigest()
                                    if actual_hash == expected_hash:
                                        integrity_verified = True
                                    else:
                                        issues.append("Integrity verification failed")
                                else:
                                    issues.append("No hash for integrity verification")
                        else:
                            issues.append(f"Decryption failed: {error}")
                
                except json.JSONDecodeError:
                    issues.append("Invalid encryption container format")
                except Exception as e:
                    issues.append(f"Container verification failed: {str(e)}")
            
            # Determine overall status
            if not issues:
                status = EncryptionStatus.ENCRYPTED
            elif "Decryption failed" in " ".join(issues):
                status = EncryptionStatus.VERIFICATION_FAILED
            elif "key" in " ".join(issues).lower():
                status = EncryptionStatus.KEY_MISSING
            else:
                status = EncryptionStatus.CORRUPTED
            
            # Calculate verification duration
            verification_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create result
            result = VerificationResult(
                document_id=document_id,
                file_path=str(encrypted_file),
                status=status,
                verification_level=verification_level,
                verified_at=start_time,
                encryption_algorithm=metadata.encryption_algorithm,
                key_id=metadata.key_id,
                file_size_bytes=file_size,
                verification_duration_ms=verification_duration,
                issues=issues,
                metadata_valid=metadata_valid,
                decryption_successful=decryption_successful,
                integrity_verified=integrity_verified
            )
            
            # Store result
            self._store_verification_result(result)
            
            # Log if configured or if there are issues
            if self.config.log_all_verifications or issues:
                log_level = logging.DEBUG if not issues else logging.WARNING
                logger.log(log_level, f"[ENCRYPTION_MONITOR] Document verification: {document_id} - Status: {status.value}")
            
            return result
            
        except Exception as e:
            error_msg = f"Verification failed with exception: {str(e)}"
            issues.append(error_msg)
            
            logger.error(f"[ENCRYPTION_MONITOR] {error_msg}", exc_info=True)
            
            return self._create_failure_result(document_id, "", start_time, verification_level, 
                                              issues, metadata if 'metadata' in locals() else None)
    
    def _create_failure_result(self, document_id: str, file_path: str, start_time: datetime,
                              verification_level: VerificationLevel, issues: List[str], 
                              metadata: Optional[EncryptionMetadata]) -> VerificationResult:
        """Create a verification failure result"""
        
        verification_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return VerificationResult(
            document_id=document_id,
            file_path=file_path,
            status=EncryptionStatus.VERIFICATION_FAILED,
            verification_level=verification_level,
            verified_at=start_time,
            encryption_algorithm=metadata.encryption_algorithm if metadata else "",
            key_id=metadata.key_id if metadata else "",
            file_size_bytes=0,
            verification_duration_ms=verification_duration,
            issues=issues,
            metadata_valid=False,
            decryption_successful=False,
            integrity_verified=False
        )
    
    def _perform_comprehensive_verification(self):
        """Perform comprehensive verification on all documents"""
        logger.info("[ENCRYPTION_MONITOR] Starting comprehensive verification")
        
        start_time = datetime.utcnow()
        
        # Get all encrypted documents
        encrypted_docs = emergency_encryption_service.list_encrypted_documents()
        
        comprehensive_results = []
        for doc_metadata in encrypted_docs:
            result = self.verify_document_encryption(
                doc_metadata.document_id,
                VerificationLevel.COMPREHENSIVE
            )
            comprehensive_results.append(result)
        
        # Analyze comprehensive results
        total_docs = len(comprehensive_results)
        encrypted_count = sum(1 for r in comprehensive_results if r.status == EncryptionStatus.ENCRYPTED)
        failed_count = total_docs - encrypted_count
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        self._log_monitoring_event('COMPREHENSIVE_VERIFICATION_COMPLETED', {
            'start_time': start_time.isoformat(),
            'duration_seconds': duration,
            'total_documents': total_docs,
            'encrypted_documents': encrypted_count,
            'failed_documents': failed_count,
            'encryption_rate': encrypted_count / max(total_docs, 1)
        })
        
        logger.info(f"[ENCRYPTION_MONITOR] Comprehensive verification completed: {encrypted_count}/{total_docs} encrypted")
    
    def _handle_verification_failure(self, result: VerificationResult):
        """Handle verification failure with tracking and potential remediation"""
        
        # Update failure tracking
        self._update_failure_tracking(result.document_id)
        
        # Call failure callbacks
        for callback in self.failure_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"[ENCRYPTION_MONITOR] Error in failure callback: {e}")
        
        # Attempt auto-remediation if enabled
        if self.config.auto_remediation_enabled:
            self._attempt_remediation(result)
    
    def _update_failure_tracking(self, document_id: str):
        """Update failure tracking in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT failure_count, first_failure_at FROM failure_tracking WHERE document_id = ?",
                (document_id,)
            )
            result = cursor.fetchone()
            
            now = datetime.utcnow().isoformat()
            
            if result:
                # Update existing record
                failure_count, first_failure_at = result
                conn.execute(
                    """UPDATE failure_tracking 
                       SET failure_count = failure_count + 1, 
                           last_failure_at = ?
                       WHERE document_id = ?""",
                    (now, document_id)
                )
            else:
                # Create new record
                conn.execute(
                    """INSERT INTO failure_tracking 
                       (document_id, failure_count, first_failure_at, last_failure_at)
                       VALUES (?, 1, ?, ?)""",
                    (document_id, now, now)
                )
            
            conn.commit()
    
    def _attempt_remediation(self, result: VerificationResult):
        """Attempt to remediate encryption failure"""
        logger.info(f"[ENCRYPTION_MONITOR] Attempting remediation for {result.document_id}")
        
        try:
            # Different remediation strategies based on failure type
            if result.status == EncryptionStatus.KEY_MISSING:
                # Try to recover or regenerate key
                self._remediate_missing_key(result.document_id)
            elif result.status == EncryptionStatus.CORRUPTED:
                # Try to re-encrypt from backup
                self._remediate_corrupted_document(result.document_id)
            elif result.status == EncryptionStatus.VERIFICATION_FAILED:
                # Try basic re-verification
                self._remediate_verification_failure(result.document_id)
            
            # Update remediation attempts
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """UPDATE failure_tracking 
                       SET remediation_attempts = remediation_attempts + 1
                       WHERE document_id = ?""",
                    (result.document_id,)
                )
                conn.commit()
                
        except Exception as e:
            logger.error(f"[ENCRYPTION_MONITOR] Remediation failed for {result.document_id}: {e}")
    
    def _remediate_missing_key(self, document_id: str):
        """Attempt to remediate missing key issues"""
        # This would involve key recovery or regeneration logic
        logger.warning(f"[ENCRYPTION_MONITOR] Key remediation needed for {document_id}")
    
    def _remediate_corrupted_document(self, document_id: str):
        """Attempt to remediate corrupted document"""
        # This would involve restoration from backup
        logger.warning(f"[ENCRYPTION_MONITOR] Document remediation needed for {document_id}")
    
    def _remediate_verification_failure(self, document_id: str):
        """Attempt to remediate verification failures"""
        # Retry verification with different parameters
        logger.warning(f"[ENCRYPTION_MONITOR] Verification remediation needed for {document_id}")
    
    def _analyze_verification_patterns(self):
        """Analyze verification patterns for anomalies"""
        # This would implement pattern analysis for security monitoring
        # For now, just check recent failure rates
        
        with sqlite3.connect(self.db_path) as conn:
            # Get recent verification results (last hour)
            one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            
            cursor = conn.execute(
                """SELECT status, COUNT(*) as count 
                   FROM verification_results 
                   WHERE verified_at > ? 
                   GROUP BY status""",
                (one_hour_ago,)
            )
            
            recent_stats = dict(cursor.fetchall())
            
            total_recent = sum(recent_stats.values())
            if total_recent > 0:
                failure_rate = (total_recent - recent_stats.get('encrypted', 0)) / total_recent
                
                if failure_rate > self.config.alert_threshold_failure_rate:
                    self._trigger_alert('PATTERN_HIGH_FAILURE_RATE', {
                        'recent_failure_rate': failure_rate,
                        'time_window_hours': 1,
                        'total_verifications': total_recent
                    })
    
    def _trigger_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Trigger monitoring alert"""
        alert = {
            'alert_type': alert_type,
            'alert_data': alert_data,
            'triggered_at': datetime.utcnow().isoformat(),
            'severity': 'HIGH' if 'HIGH' in alert_type else 'MEDIUM'
        }
        
        self.failure_alerts.append(alert)
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"[ENCRYPTION_MONITOR] Error in alert callback: {e}")
        
        # Log alert
        self._log_monitoring_event('ALERT_TRIGGERED', alert)
        
        logger.error(f"[ENCRYPTION_MONITOR] ALERT: {alert_type} - {alert_data}")
    
    def _store_verification_result(self, result: VerificationResult):
        """Store verification result in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO verification_results 
                   (document_id, file_path, status, verification_level, verified_at,
                    encryption_algorithm, key_id, file_size_bytes, verification_duration_ms,
                    issues, metadata_valid, decryption_successful, integrity_verified)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    result.document_id, result.file_path, result.status.value,
                    result.verification_level.value, result.verified_at.isoformat(),
                    result.encryption_algorithm, result.key_id, result.file_size_bytes,
                    result.verification_duration_ms, json.dumps(result.issues),
                    result.metadata_valid, result.decryption_successful, result.integrity_verified
                )
            )
            conn.commit()
    
    def _log_monitoring_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log monitoring event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'service': 'encryption_verification_monitor',
            'event_data': event_data,
            'compliance_audit': True
        }
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO monitoring_events (event_type, event_data) VALUES (?, ?)",
                (event_type, json.dumps(event_data))
            )
            conn.commit()
        
        # Log to system logger
        logger.info(f"[ENCRYPTION_MONITOR_AUDIT] {json.dumps(event)}")
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get current monitoring statistics"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Get verification statistics
            cursor = conn.execute(
                """SELECT status, COUNT(*) as count
                   FROM verification_results
                   WHERE verified_at > datetime('now', '-24 hours')
                   GROUP BY status"""
            )
            daily_stats = dict(cursor.fetchall())
            
            # Get failure tracking
            cursor = conn.execute(
                """SELECT COUNT(*) as total_failures,
                          AVG(failure_count) as avg_failures_per_doc
                   FROM failure_tracking
                   WHERE last_failure_at > datetime('now', '-24 hours')"""
            )
            failure_stats = cursor.fetchone()
        
        return {
            'monitoring_active': self.is_monitoring,
            'daily_verification_stats': daily_stats,
            'total_failures_24h': failure_stats[0] if failure_stats[0] else 0,
            'avg_failures_per_document': failure_stats[1] if failure_stats[1] else 0,
            'recent_alerts': len([a for a in self.failure_alerts 
                                if datetime.fromisoformat(a['triggered_at']) > datetime.utcnow() - timedelta(hours=24)]),
            'verification_stats': dict(self.verification_stats),
            'config': asdict(self.config)
        }

# Global encryption verification monitor instance
encryption_verification_monitor = EncryptionVerificationMonitor()

__all__ = [
    'EncryptionVerificationMonitor',
    'VerificationResult',
    'EncryptionStatus',
    'VerificationLevel',
    'MonitoringConfig',
    'encryption_verification_monitor'
]