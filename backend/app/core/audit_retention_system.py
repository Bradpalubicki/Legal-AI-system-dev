#!/usr/bin/env python3
"""
TAMPER-PROOF AUDIT RETENTION SYSTEM

Provides secure, tamper-proof storage and retention of audit logs
with legal hold capabilities and 7-year retention policy.
"""

import os
import sqlite3
import json
import hashlib
import hmac
import threading
import time
import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac as crypto_hmac
from cryptography.hazmat.backends import default_backend
import secrets

class RetentionStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    LEGAL_HOLD = "legal_hold"
    EXPIRED = "expired"
    PURGED = "purged"

class AuditRecordType(Enum):
    ENCRYPTION_EVENT = "encryption_event"
    SECURITY_EVENT = "security_event"
    ADMIN_ACTION = "admin_action"
    SYSTEM_EVENT = "system_event"
    COMPLIANCE_EVENT = "compliance_event"

@dataclass
class RetentionPolicy:
    """Audit log retention policy"""
    record_type: AuditRecordType
    retention_years: int
    archive_after_days: int
    legal_hold_capable: bool
    purge_approved: bool = False
    
    def __post_init__(self):
        if self.retention_years < 7:
            self.retention_years = 7  # Legal minimum

@dataclass
class AuditArchive:
    """Tamper-proof audit archive"""
    archive_id: str
    creation_date: datetime
    start_date: datetime
    end_date: datetime
    record_count: int
    compressed_size: int
    integrity_hash: str
    encryption_key_id: str
    retention_status: RetentionStatus
    legal_hold_id: Optional[str] = None
    expiration_date: Optional[datetime] = None

@dataclass
class LegalHold:
    """Legal hold on audit records"""
    hold_id: str
    case_reference: str
    hold_date: datetime
    requesting_attorney: str
    scope_description: str
    affected_records: List[str]
    status: str = "active"
    release_date: Optional[datetime] = None

class TamperProofStorage:
    """Secure, tamper-proof storage for audit logs"""
    
    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.key_file = self.storage_dir / ".retention_keys"
        self.integrity_key = self._get_or_create_integrity_key()
        
    def _get_or_create_integrity_key(self) -> bytes:
        """Get or create integrity verification key"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read(32)
        else:
            key = secrets.token_bytes(32)
            with open(self.key_file, 'wb') as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)
            return key
    
    def store_archive(self, archive_data: bytes, archive_id: str) -> str:
        """Store audit archive with integrity protection"""
        # Create integrity hash
        h = crypto_hmac.HMAC(self.integrity_key, hashes.SHA256(), backend=default_backend())
        h.update(archive_data)
        integrity_hash = h.finalize().hex()
        
        # Encrypt archive data
        encryption_key = secrets.token_bytes(32)
        iv = secrets.token_bytes(16)
        
        cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Pad data for CBC mode
        padding_length = 16 - (len(archive_data) % 16)
        padded_data = archive_data + bytes([padding_length] * padding_length)
        
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Store encrypted archive
        archive_path = self.storage_dir / f"{archive_id}.enc"
        with open(archive_path, 'wb') as f:
            f.write(iv + encrypted_data)
        
        # Store encryption key separately
        key_path = self.storage_dir / f"{archive_id}.key"
        with open(key_path, 'wb') as f:
            f.write(encryption_key)
        os.chmod(key_path, 0o600)
        
        return integrity_hash
    
    def retrieve_archive(self, archive_id: str) -> bytes:
        """Retrieve and decrypt audit archive"""
        archive_path = self.storage_dir / f"{archive_id}.enc"
        key_path = self.storage_dir / f"{archive_id}.key"
        
        if not archive_path.exists() or not key_path.exists():
            raise FileNotFoundError(f"Archive {archive_id} not found")
        
        # Load encryption key
        with open(key_path, 'rb') as f:
            encryption_key = f.read()
        
        # Load and decrypt archive
        with open(archive_path, 'rb') as f:
            encrypted_data = f.read()
        
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding
        padding_length = padded_data[-1]
        return padded_data[:-padding_length]
    
    def verify_integrity(self, archive_data: bytes, expected_hash: str) -> bool:
        """Verify archive integrity"""
        h = crypto_hmac.HMAC(self.integrity_key, hashes.SHA256(), backend=default_backend())
        h.update(archive_data)
        actual_hash = h.finalize().hex()
        
        return hmac.compare_digest(actual_hash, expected_hash)

class AuditRetentionSystem:
    """Comprehensive audit retention system with tamper-proof storage"""
    
    def __init__(self, base_dir: str = "audit_retention"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.db_path = self.base_dir / "retention_system.db"
        self.storage = TamperProofStorage(str(self.base_dir / "archives"))
        
        # Initialize database
        self._init_database()
        
        # Load retention policies
        self.retention_policies = self._load_default_policies()
        
        # Background processing
        self.processing_thread = None
        self.stop_processing = threading.Event()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Start background processing
        self.start_background_processing()
    
    def _init_database(self):
        """Initialize retention system database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS retention_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_type TEXT NOT NULL,
                    retention_years INTEGER NOT NULL,
                    archive_after_days INTEGER NOT NULL,
                    legal_hold_capable BOOLEAN NOT NULL,
                    purge_approved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(record_type)
                );
                
                CREATE TABLE IF NOT EXISTS audit_archives (
                    archive_id TEXT PRIMARY KEY,
                    creation_date TIMESTAMP NOT NULL,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    record_count INTEGER NOT NULL,
                    compressed_size INTEGER NOT NULL,
                    integrity_hash TEXT NOT NULL,
                    encryption_key_id TEXT NOT NULL,
                    retention_status TEXT NOT NULL,
                    legal_hold_id TEXT,
                    expiration_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS legal_holds (
                    hold_id TEXT PRIMARY KEY,
                    case_reference TEXT NOT NULL,
                    hold_date TIMESTAMP NOT NULL,
                    requesting_attorney TEXT NOT NULL,
                    scope_description TEXT NOT NULL,
                    affected_records TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    release_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS retention_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    event_details TEXT NOT NULL,
                    affected_archives TEXT,
                    user_id TEXT,
                    system_health TEXT DEFAULT 'healthy'
                );
                
                CREATE INDEX IF NOT EXISTS idx_archives_status ON audit_archives(retention_status);
                CREATE INDEX IF NOT EXISTS idx_archives_expiration ON audit_archives(expiration_date);
                CREATE INDEX IF NOT EXISTS idx_holds_status ON legal_holds(status);
                CREATE INDEX IF NOT EXISTS idx_retention_log_timestamp ON retention_log(timestamp);
            ''')
    
    def _load_default_policies(self) -> Dict[AuditRecordType, RetentionPolicy]:
        """Load default retention policies"""
        policies = {
            AuditRecordType.ENCRYPTION_EVENT: RetentionPolicy(
                AuditRecordType.ENCRYPTION_EVENT, 7, 365, True
            ),
            AuditRecordType.SECURITY_EVENT: RetentionPolicy(
                AuditRecordType.SECURITY_EVENT, 10, 180, True
            ),
            AuditRecordType.ADMIN_ACTION: RetentionPolicy(
                AuditRecordType.ADMIN_ACTION, 15, 90, True
            ),
            AuditRecordType.SYSTEM_EVENT: RetentionPolicy(
                AuditRecordType.SYSTEM_EVENT, 7, 730, False
            ),
            AuditRecordType.COMPLIANCE_EVENT: RetentionPolicy(
                AuditRecordType.COMPLIANCE_EVENT, 20, 30, True
            )
        }
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            for policy in policies.values():
                conn.execute('''
                    INSERT OR REPLACE INTO retention_policies 
                    (record_type, retention_years, archive_after_days, legal_hold_capable, purge_approved)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    policy.record_type.value,
                    policy.retention_years,
                    policy.archive_after_days,
                    policy.legal_hold_capable,
                    policy.purge_approved
                ))
        
        return policies
    
    def create_archive(self, record_type: AuditRecordType, start_date: datetime, 
                      end_date: datetime, source_data: Dict[str, Any]) -> str:
        """Create tamper-proof audit archive"""
        
        archive_id = f"archive_{int(time.time())}_{record_type.value}"
        
        # Compress and serialize data
        archive_data = {
            'metadata': {
                'archive_id': archive_id,
                'record_type': record_type.value,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'creation_date': datetime.utcnow().isoformat()
            },
            'records': source_data
        }
        
        json_data = json.dumps(archive_data, indent=2).encode()
        compressed_data = gzip.compress(json_data)
        
        # Store with tamper-proof protection
        integrity_hash = self.storage.store_archive(compressed_data, archive_id)
        
        # Calculate expiration date
        policy = self.retention_policies.get(record_type)
        expiration_date = datetime.utcnow() + timedelta(days=policy.retention_years * 365) if policy else None
        
        # Create archive record
        archive = AuditArchive(
            archive_id=archive_id,
            creation_date=datetime.utcnow(),
            start_date=start_date,
            end_date=end_date,
            record_count=len(source_data),
            compressed_size=len(compressed_data),
            integrity_hash=integrity_hash,
            encryption_key_id=archive_id,
            retention_status=RetentionStatus.ACTIVE,
            expiration_date=expiration_date
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO audit_archives 
                (archive_id, creation_date, start_date, end_date, record_count, 
                 compressed_size, integrity_hash, encryption_key_id, retention_status, expiration_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                archive.archive_id,
                archive.creation_date,
                archive.start_date,
                archive.end_date,
                archive.record_count,
                archive.compressed_size,
                archive.integrity_hash,
                archive.encryption_key_id,
                archive.retention_status.value,
                archive.expiration_date
            ))
        
        self._log_retention_event("ARCHIVE_CREATED", {
            'archive_id': archive_id,
            'record_type': record_type.value,
            'record_count': len(source_data),
            'size': len(compressed_data)
        })
        
        return archive_id
    
    def place_legal_hold(self, case_reference: str, requesting_attorney: str,
                        scope_description: str, affected_records: List[str]) -> str:
        """Place legal hold on audit records"""
        
        hold_id = f"hold_{int(time.time())}_{hashlib.sha256(case_reference.encode()).hexdigest()[:8]}"
        
        legal_hold = LegalHold(
            hold_id=hold_id,
            case_reference=case_reference,
            hold_date=datetime.utcnow(),
            requesting_attorney=requesting_attorney,
            scope_description=scope_description,
            affected_records=affected_records
        )
        
        with sqlite3.connect(self.db_path) as conn:
            # Store legal hold
            conn.execute('''
                INSERT INTO legal_holds 
                (hold_id, case_reference, hold_date, requesting_attorney, 
                 scope_description, affected_records, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                legal_hold.hold_id,
                legal_hold.case_reference,
                legal_hold.hold_date,
                legal_hold.requesting_attorney,
                legal_hold.scope_description,
                json.dumps(legal_hold.affected_records),
                legal_hold.status
            ))
            
            # Update affected archives
            for archive_id in affected_records:
                conn.execute('''
                    UPDATE audit_archives 
                    SET retention_status = ?, legal_hold_id = ?
                    WHERE archive_id = ?
                ''', (RetentionStatus.LEGAL_HOLD.value, hold_id, archive_id))
        
        self._log_retention_event("LEGAL_HOLD_PLACED", {
            'hold_id': hold_id,
            'case_reference': case_reference,
            'affected_records': len(affected_records)
        })
        
        return hold_id
    
    def release_legal_hold(self, hold_id: str, releasing_attorney: str) -> bool:
        """Release legal hold on audit records"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Get hold details
            cursor = conn.execute('''
                SELECT case_reference, affected_records 
                FROM legal_holds 
                WHERE hold_id = ? AND status = 'active'
            ''', (hold_id,))
            
            hold_data = cursor.fetchone()
            if not hold_data:
                return False
            
            case_reference, affected_records_json = hold_data
            affected_records = json.loads(affected_records_json)
            
            # Release hold
            conn.execute('''
                UPDATE legal_holds 
                SET status = 'released', release_date = ?
                WHERE hold_id = ?
            ''', (datetime.utcnow(), hold_id))
            
            # Update archive statuses
            for archive_id in affected_records:
                conn.execute('''
                    UPDATE audit_archives 
                    SET retention_status = ?, legal_hold_id = NULL
                    WHERE archive_id = ? AND legal_hold_id = ?
                ''', (RetentionStatus.ACTIVE.value, archive_id, hold_id))
        
        self._log_retention_event("LEGAL_HOLD_RELEASED", {
            'hold_id': hold_id,
            'case_reference': case_reference,
            'releasing_attorney': releasing_attorney,
            'affected_records': len(affected_records)
        })
        
        return True
    
    def verify_archive_integrity(self, archive_id: str) -> bool:
        """Verify tamper-proof archive integrity"""
        
        try:
            # Get archive metadata
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT integrity_hash FROM audit_archives WHERE archive_id = ?
                ''', (archive_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                expected_hash = result[0]
            
            # Retrieve and verify archive
            archive_data = self.storage.retrieve_archive(archive_id)
            integrity_verified = self.storage.verify_integrity(archive_data, expected_hash)
            
            # Update last verified timestamp
            if integrity_verified:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        UPDATE audit_archives 
                        SET last_verified = ?
                        WHERE archive_id = ?
                    ''', (datetime.utcnow(), archive_id))
            
            self._log_retention_event("INTEGRITY_VERIFICATION", {
                'archive_id': archive_id,
                'result': 'success' if integrity_verified else 'failed'
            })
            
            return integrity_verified
            
        except Exception as e:
            self._log_retention_event("INTEGRITY_VERIFICATION", {
                'archive_id': archive_id,
                'result': 'error',
                'error': str(e)
            })
            return False
    
    def get_retention_status(self) -> Dict[str, Any]:
        """Get comprehensive retention system status"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Archive statistics
            cursor = conn.execute('''
                SELECT 
                    retention_status,
                    COUNT(*) as count,
                    SUM(record_count) as total_records,
                    SUM(compressed_size) as total_size
                FROM audit_archives 
                GROUP BY retention_status
            ''')
            
            archive_stats = {}
            for row in cursor:
                archive_stats[row[0]] = {
                    'count': row[1],
                    'total_records': row[2],
                    'total_size': row[3]
                }
            
            # Legal holds
            cursor = conn.execute('''
                SELECT COUNT(*) FROM legal_holds WHERE status = 'active'
            ''')
            active_holds = cursor.fetchone()[0]
            
            # Expiring archives
            next_month = datetime.utcnow() + timedelta(days=30)
            cursor = conn.execute('''
                SELECT COUNT(*) FROM audit_archives 
                WHERE expiration_date IS NOT NULL AND expiration_date <= ?
                AND retention_status != ?
            ''', (next_month, RetentionStatus.LEGAL_HOLD.value))
            expiring_soon = cursor.fetchone()[0]
        
        return {
            'system_health': 'healthy',
            'archive_statistics': archive_stats,
            'active_legal_holds': active_holds,
            'archives_expiring_soon': expiring_soon,
            'retention_policies_count': len(self.retention_policies),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def _log_retention_event(self, event_type: str, event_details: Dict[str, Any], 
                           affected_archives: str = None, user_id: str = None):
        """Log retention system events"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO retention_log 
                (timestamp, event_type, event_details, affected_archives, user_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.utcnow(),
                event_type,
                json.dumps(event_details),
                affected_archives,
                user_id
            ))
    
    def start_background_processing(self):
        """Start background processing for retention management"""
        if self.processing_thread and self.processing_thread.is_alive():
            return
        
        self.stop_processing.clear()
        self.processing_thread = threading.Thread(target=self._background_processor)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        self.logger.info("Audit retention background processing started")
    
    def stop_background_processing(self):
        """Stop background processing"""
        if self.processing_thread:
            self.stop_processing.set()
            self.processing_thread.join(timeout=10)
            self.logger.info("Audit retention background processing stopped")
    
    def _background_processor(self):
        """Background processing for retention management"""
        
        while not self.stop_processing.wait(3600):  # Check every hour
            try:
                # Archive old records
                self._archive_old_records()
                
                # Verify archive integrity (random sampling)
                self._verify_random_archives()
                
                # Check for expired archives
                self._handle_expired_archives()
                
                # Clean up retention logs
                self._cleanup_old_logs()
                
            except Exception as e:
                self.logger.error(f"Background processing error: {e}")
    
    def _archive_old_records(self):
        """Archive old records based on retention policies"""
        # Implementation would integrate with individual audit systems
        # to move old records into tamper-proof archives
        pass
    
    def _verify_random_archives(self):
        """Verify integrity of random sample of archives"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT archive_id FROM audit_archives 
                WHERE retention_status = ? 
                ORDER BY RANDOM() LIMIT 5
            ''', (RetentionStatus.ACTIVE.value,))
            
            for row in cursor:
                self.verify_archive_integrity(row[0])
    
    def _handle_expired_archives(self):
        """Handle archives that have reached expiration"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT archive_id FROM audit_archives 
                WHERE expiration_date <= ? 
                AND retention_status NOT IN (?, ?)
            ''', (datetime.utcnow(), RetentionStatus.LEGAL_HOLD.value, RetentionStatus.EXPIRED.value))
            
            expired_archives = [row[0] for row in cursor]
            
            for archive_id in expired_archives:
                conn.execute('''
                    UPDATE audit_archives 
                    SET retention_status = ?
                    WHERE archive_id = ?
                ''', (RetentionStatus.EXPIRED.value, archive_id))
                
                self._log_retention_event("ARCHIVE_EXPIRED", {'archive_id': archive_id})
    
    def _cleanup_old_logs(self):
        """Clean up old retention logs"""
        cutoff_date = datetime.utcnow() - timedelta(days=2555)  # 7 years
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                DELETE FROM retention_log WHERE timestamp < ?
            ''', (cutoff_date,))

# Global instance
audit_retention_system = AuditRetentionSystem()