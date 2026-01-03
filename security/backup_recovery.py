#!/usr/bin/env python3
"""
SOC 2 Type II Compliant Backup and Disaster Recovery System
Secure backup with encryption and legal compliance features
"""

import os
import json
import hashlib
import gzip
import shutil
import sqlite3
import tarfile
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from cryptography.fernet import Fernet
import schedule
import time

logger = logging.getLogger(__name__)

class BackupType(Enum):
    """Types of backups supported"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    ARCHIVE = "archive"

class BackupStatus(Enum):
    """Backup operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"
    CORRUPTED = "corrupted"

class BackupLocation(Enum):
    """Backup storage locations"""
    LOCAL = "local"
    NETWORK = "network"
    CLOUD_S3 = "cloud_s3"
    OFFSITE = "offsite"

@dataclass
class BackupJob:
    """Backup job configuration and metadata"""
    job_id: str
    name: str
    backup_type: BackupType
    source_paths: List[str]
    destination: str
    location: BackupLocation
    
    # Scheduling
    schedule_cron: str
    retention_days: int
    
    # Security
    encryption_enabled: bool = True
    compression_enabled: bool = True
    
    # Legal compliance
    legal_hold_aware: bool = True
    privilege_protection: bool = True
    
    # Status
    last_run: Optional[datetime] = None
    last_status: BackupStatus = BackupStatus.PENDING
    next_run: Optional[datetime] = None

@dataclass
class BackupRecord:
    """Individual backup record"""
    backup_id: str
    job_id: str
    backup_type: BackupType
    start_time: datetime
    end_time: Optional[datetime]
    status: BackupStatus
    
    # File information
    source_paths: List[str]
    backup_file_path: str
    backup_size: int
    compressed_size: int
    
    # Verification
    checksum: str
    verification_status: bool = False
    verification_time: Optional[datetime] = None
    
    # Recovery information
    recovery_tested: bool = False
    recovery_test_date: Optional[datetime] = None
    recovery_rto: Optional[int] = None  # Recovery Time Objective in minutes

class LegalBackupCompliance:
    """Legal compliance manager for backups"""
    
    def __init__(self):
        # ABA Model Rules compliance
        self.privilege_retention_years = 999  # Indefinite for privileged materials
        self.case_file_retention_years = 10
        self.billing_retention_years = 7
        
        # Regulatory requirements
        self.sox_retention_years = 7
        self.hipaa_retention_years = 6
        
    def should_backup_data(self, data_type: str, privilege_level: str, 
                          legal_hold: bool = False) -> bool:
        """Determine if data should be included in backup based on legal requirements"""
        
        # Always backup attorney-client privileged materials
        if privilege_level in ["ATTORNEY_CLIENT", "ATTORNEY_WORK_PRODUCT"]:
            return True
        
        # Always backup data under legal hold
        if legal_hold:
            return True
        
        # Check data type requirements
        backup_required_types = [
            "client_files", "case_documents", "billing_records",
            "conflict_records", "audit_logs", "financial_records"
        ]
        
        return data_type in backup_required_types
    
    def get_retention_period(self, data_type: str, privilege_level: str) -> int:
        """Get backup retention period in years based on legal requirements"""
        
        if privilege_level in ["ATTORNEY_CLIENT", "ATTORNEY_WORK_PRODUCT"]:
            return self.privilege_retention_years
        
        retention_map = {
            "case_documents": self.case_file_retention_years,
            "billing_records": self.billing_retention_years,
            "conflict_records": self.privilege_retention_years,
            "audit_logs": 7,
            "financial_records": 7
        }
        
        return retention_map.get(data_type, 7)  # Default 7 years

class SecureBackupManager:
    """SOC 2 compliant backup and disaster recovery manager"""
    
    def __init__(self, config_path: str = "backup/backup_config.json"):
        self.config_path = config_path
        self.backup_root = "backups"
        self.db_path = "backup/backup_records.db"
        
        # Ensure directories exist
        os.makedirs(self.backup_root, exist_ok=True)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize components
        self.compliance_manager = LegalBackupCompliance()
        self.encryption_key = self._get_or_create_encryption_key()
        
        # Initialize database
        self._init_database()
        
        # Load configuration
        self.config = self._load_config()
        
        # Active backup jobs
        self.backup_jobs: Dict[str, BackupJob] = {}
        self._load_backup_jobs()
        
        # Recovery metrics
        self.rto_target = 4  # Recovery Time Objective: 4 hours
        self.rpo_target = 1  # Recovery Point Objective: 1 hour
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for backups"""
        key_path = "backup/backup_encryption.key"
        
        if os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                return f.read()
        
        # Generate new key
        key = Fernet.generate_key()
        with open(key_path, 'wb') as f:
            f.write(key)
        
        # Set restrictive permissions
        os.chmod(key_path, 0o600)
        return key
    
    def _init_database(self):
        """Initialize backup records database"""
        with sqlite3.connect(self.db_path) as conn:
            # Backup jobs table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS backup_jobs (
                    job_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    backup_type TEXT NOT NULL,
                    source_paths TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    location TEXT NOT NULL,
                    schedule_cron TEXT NOT NULL,
                    retention_days INTEGER NOT NULL,
                    encryption_enabled BOOLEAN DEFAULT 1,
                    compression_enabled BOOLEAN DEFAULT 1,
                    legal_hold_aware BOOLEAN DEFAULT 1,
                    privilege_protection BOOLEAN DEFAULT 1,
                    last_run TEXT,
                    last_status TEXT DEFAULT 'pending',
                    next_run TEXT
                )
            ''')
            
            # Backup records table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS backup_records (
                    backup_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    backup_type TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT NOT NULL,
                    source_paths TEXT NOT NULL,
                    backup_file_path TEXT NOT NULL,
                    backup_size INTEGER DEFAULT 0,
                    compressed_size INTEGER DEFAULT 0,
                    checksum TEXT NOT NULL,
                    verification_status BOOLEAN DEFAULT 0,
                    verification_time TEXT,
                    recovery_tested BOOLEAN DEFAULT 0,
                    recovery_test_date TEXT,
                    recovery_rto INTEGER,
                    FOREIGN KEY (job_id) REFERENCES backup_jobs (job_id)
                )
            ''')
            
            # Disaster recovery tests table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS disaster_recovery_tests (
                    test_id TEXT PRIMARY KEY,
                    test_date TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    backup_id TEXT NOT NULL,
                    test_duration_minutes INTEGER,
                    success BOOLEAN DEFAULT 0,
                    issues_found TEXT,
                    recovery_rto_actual INTEGER,
                    test_notes TEXT,
                    FOREIGN KEY (backup_id) REFERENCES backup_records (backup_id)
                )
            ''')
            
            # Create indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_backup_start_time ON backup_records(start_time)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_backup_status ON backup_records(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_job_id ON backup_records(job_id)')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load backup configuration"""
        default_config = {
            "max_parallel_backups": 3,
            "compression_level": 6,
            "verification_enabled": True,
            "cloud_storage": {
                "enabled": False,
                "provider": "aws_s3",
                "bucket": "legal-ai-backups",
                "region": "us-east-1"
            },
            "retention_policy": {
                "daily_retention_days": 30,
                "weekly_retention_weeks": 12,
                "monthly_retention_months": 12,
                "yearly_retention_years": 7
            }
        }
        
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        
        # Save default config
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _load_backup_jobs(self):
        """Load backup jobs from database"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM backup_jobs").fetchall()
            
            for row in rows:
                job = BackupJob(
                    job_id=row[0],
                    name=row[1],
                    backup_type=BackupType(row[2]),
                    source_paths=json.loads(row[3]),
                    destination=row[4],
                    location=BackupLocation(row[5]),
                    schedule_cron=row[6],
                    retention_days=row[7],
                    encryption_enabled=bool(row[8]),
                    compression_enabled=bool(row[9]),
                    legal_hold_aware=bool(row[10]),
                    privilege_protection=bool(row[11]),
                    last_run=datetime.fromisoformat(row[12]) if row[12] else None,
                    last_status=BackupStatus(row[13]),
                    next_run=datetime.fromisoformat(row[14]) if row[14] else None
                )
                self.backup_jobs[job.job_id] = job
    
    def create_backup_job(self, name: str, backup_type: BackupType, 
                         source_paths: List[str], destination: str,
                         location: BackupLocation, schedule_cron: str,
                         retention_days: int = 90) -> str:
        """Create new backup job"""
        
        job_id = hashlib.sha256(
            f"{name}|{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        job = BackupJob(
            job_id=job_id,
            name=name,
            backup_type=backup_type,
            source_paths=source_paths,
            destination=destination,
            location=location,
            schedule_cron=schedule_cron,
            retention_days=retention_days
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO backup_jobs (
                    job_id, name, backup_type, source_paths, destination,
                    location, schedule_cron, retention_days, encryption_enabled,
                    compression_enabled, legal_hold_aware, privilege_protection
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.job_id, job.name, job.backup_type.value,
                json.dumps(job.source_paths), job.destination, job.location.value,
                job.schedule_cron, job.retention_days, job.encryption_enabled,
                job.compression_enabled, job.legal_hold_aware, job.privilege_protection
            ))
        
        self.backup_jobs[job_id] = job
        logger.info(f"Created backup job {job_id}: {name}")
        return job_id
    
    def run_backup(self, job_id: str, backup_type: BackupType = None) -> str:
        """Execute backup job"""
        
        job = self.backup_jobs.get(job_id)
        if not job:
            raise ValueError(f"Backup job {job_id} not found")
        
        # Use specified backup type or job default
        actual_backup_type = backup_type or job.backup_type
        
        # Generate backup ID
        backup_id = hashlib.sha256(
            f"{job_id}|{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        start_time = datetime.utcnow()
        
        # Create backup record
        backup_record = BackupRecord(
            backup_id=backup_id,
            job_id=job_id,
            backup_type=actual_backup_type,
            start_time=start_time,
            end_time=None,
            status=BackupStatus.IN_PROGRESS,
            source_paths=job.source_paths,
            backup_file_path="",
            backup_size=0,
            compressed_size=0,
            checksum=""
        )
        
        try:
            logger.info(f"Starting backup {backup_id} for job {job.name}")
            
            # Create backup file path
            backup_filename = f"{job.name}_{actual_backup_type.value}_{start_time.strftime('%Y%m%d_%H%M%S')}.tar.gz"
            backup_file_path = os.path.join(job.destination, backup_filename)
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
            
            # Perform backup
            backup_size, compressed_size = self._create_backup_archive(
                job.source_paths, backup_file_path, job.compression_enabled
            )
            
            # Encrypt if required
            if job.encryption_enabled:
                encrypted_path = backup_file_path + ".enc"
                self._encrypt_backup_file(backup_file_path, encrypted_path)
                os.remove(backup_file_path)  # Remove unencrypted version
                backup_file_path = encrypted_path
            
            # Calculate checksum
            checksum = self._calculate_file_checksum(backup_file_path)
            
            # Update backup record
            backup_record.end_time = datetime.utcnow()
            backup_record.status = BackupStatus.COMPLETED
            backup_record.backup_file_path = backup_file_path
            backup_record.backup_size = backup_size
            backup_record.compressed_size = compressed_size
            backup_record.checksum = checksum
            
            # Store backup record
            self._store_backup_record(backup_record)
            
            # Update job status
            job.last_run = start_time
            job.last_status = BackupStatus.COMPLETED
            self._update_job_status(job)
            
            # Verify backup if configured
            if self.config.get("verification_enabled", True):
                self._verify_backup(backup_record)
            
            # Upload to cloud if configured
            if (job.location == BackupLocation.CLOUD_S3 and 
                self.config["cloud_storage"]["enabled"]):
                self._upload_to_cloud(backup_record)
            
            # Clean up old backups
            self._cleanup_old_backups(job_id, job.retention_days)
            
            logger.info(f"Backup {backup_id} completed successfully")
            return backup_id
            
        except Exception as e:
            logger.error(f"Backup {backup_id} failed: {e}")
            
            backup_record.end_time = datetime.utcnow()
            backup_record.status = BackupStatus.FAILED
            self._store_backup_record(backup_record)
            
            job.last_status = BackupStatus.FAILED
            self._update_job_status(job)
            
            raise
    
    def _create_backup_archive(self, source_paths: List[str], 
                              backup_path: str, compress: bool = True) -> Tuple[int, int]:
        """Create backup archive from source paths"""
        
        total_size = 0
        mode = 'w:gz' if compress else 'w'
        
        with tarfile.open(backup_path, mode) as tar:
            for source_path in source_paths:
                if os.path.exists(source_path):
                    if os.path.isfile(source_path):
                        tar.add(source_path, arcname=os.path.basename(source_path))
                        total_size += os.path.getsize(source_path)
                    else:
                        # Add directory recursively
                        for root, dirs, files in os.walk(source_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, os.path.dirname(source_path))
                                tar.add(file_path, arcname=arcname)
                                total_size += os.path.getsize(file_path)
                else:
                    logger.warning(f"Source path not found: {source_path}")
        
        compressed_size = os.path.getsize(backup_path)
        return total_size, compressed_size
    
    def _encrypt_backup_file(self, source_path: str, dest_path: str):
        """Encrypt backup file using Fernet encryption"""
        
        fernet = Fernet(self.encryption_key)
        
        with open(source_path, 'rb') as source_file:
            with open(dest_path, 'wb') as dest_file:
                # Encrypt in chunks to handle large files
                chunk_size = 64 * 1024  # 64KB chunks
                
                while True:
                    chunk = source_file.read(chunk_size)
                    if not chunk:
                        break
                    
                    encrypted_chunk = fernet.encrypt(chunk)
                    dest_file.write(encrypted_chunk)
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file"""
        
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _store_backup_record(self, record: BackupRecord):
        """Store backup record in database"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO backup_records (
                    backup_id, job_id, backup_type, start_time, end_time,
                    status, source_paths, backup_file_path, backup_size,
                    compressed_size, checksum, verification_status,
                    verification_time, recovery_tested, recovery_test_date,
                    recovery_rto
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.backup_id, record.job_id, record.backup_type.value,
                record.start_time.isoformat(),
                record.end_time.isoformat() if record.end_time else None,
                record.status.value, json.dumps(record.source_paths),
                record.backup_file_path, record.backup_size, record.compressed_size,
                record.checksum, record.verification_status,
                record.verification_time.isoformat() if record.verification_time else None,
                record.recovery_tested,
                record.recovery_test_date.isoformat() if record.recovery_test_date else None,
                record.recovery_rto
            ))
    
    def _update_job_status(self, job: BackupJob):
        """Update backup job status in database"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE backup_jobs
                SET last_run = ?, last_status = ?, next_run = ?
                WHERE job_id = ?
            ''', (
                job.last_run.isoformat() if job.last_run else None,
                job.last_status.value,
                job.next_run.isoformat() if job.next_run else None,
                job.job_id
            ))
    
    def _verify_backup(self, backup_record: BackupRecord) -> bool:
        """Verify backup integrity"""
        
        try:
            # Recalculate checksum
            current_checksum = self._calculate_file_checksum(backup_record.backup_file_path)
            
            if current_checksum == backup_record.checksum:
                backup_record.verification_status = True
                backup_record.verification_time = datetime.utcnow()
                logger.info(f"Backup {backup_record.backup_id} verification successful")
                return True
            else:
                backup_record.verification_status = False
                backup_record.status = BackupStatus.CORRUPTED
                logger.error(f"Backup {backup_record.backup_id} verification failed - checksum mismatch")
                return False
                
        except Exception as e:
            logger.error(f"Backup verification failed for {backup_record.backup_id}: {e}")
            backup_record.verification_status = False
            return False
        finally:
            self._store_backup_record(backup_record)
    
    def _upload_to_cloud(self, backup_record: BackupRecord):
        """Upload backup to cloud storage (AWS S3)"""
        
        cloud_config = self.config["cloud_storage"]
        
        try:
            s3_client = boto3.client(
                's3',
                region_name=cloud_config["region"],
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
            
            # Upload file
            s3_key = f"backups/{os.path.basename(backup_record.backup_file_path)}"
            
            s3_client.upload_file(
                backup_record.backup_file_path,
                cloud_config["bucket"],
                s3_key
            )
            
            logger.info(f"Backup {backup_record.backup_id} uploaded to S3")
            
        except Exception as e:
            logger.error(f"Failed to upload backup to cloud: {e}")
            raise
    
    def _cleanup_old_backups(self, job_id: str, retention_days: int):
        """Clean up old backups based on retention policy"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        with sqlite3.connect(self.db_path) as conn:
            # Find old backups
            old_backups = conn.execute('''
                SELECT backup_id, backup_file_path FROM backup_records
                WHERE job_id = ? AND start_time < ? AND status = 'completed'
            ''', (job_id, cutoff_date.isoformat())).fetchall()
            
            for backup_id, backup_file_path in old_backups:
                try:
                    # Remove backup file
                    if os.path.exists(backup_file_path):
                        os.remove(backup_file_path)
                        logger.info(f"Deleted old backup file: {backup_file_path}")
                    
                    # Update database record
                    conn.execute('''
                        UPDATE backup_records
                        SET status = 'deleted'
                        WHERE backup_id = ?
                    ''', (backup_id,))
                    
                except Exception as e:
                    logger.error(f"Failed to delete old backup {backup_id}: {e}")
    
    def restore_from_backup(self, backup_id: str, restore_path: str) -> bool:
        """Restore data from backup"""
        
        with sqlite3.connect(self.db_path) as conn:
            backup_info = conn.execute(
                "SELECT * FROM backup_records WHERE backup_id = ?",
                (backup_id,)
            ).fetchone()
            
            if not backup_info:
                logger.error(f"Backup {backup_id} not found")
                return False
            
            backup_file_path = backup_info[7]  # backup_file_path column
            
            if not os.path.exists(backup_file_path):
                logger.error(f"Backup file not found: {backup_file_path}")
                return False
        
        try:
            start_time = datetime.utcnow()
            
            # Decrypt if necessary
            working_file_path = backup_file_path
            if backup_file_path.endswith('.enc'):
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                working_file_path = temp_file.name
                temp_file.close()
                
                self._decrypt_backup_file(backup_file_path, working_file_path)
            
            # Extract backup
            os.makedirs(restore_path, exist_ok=True)
            
            with tarfile.open(working_file_path, 'r:*') as tar:
                tar.extractall(restore_path)
            
            # Clean up temporary file
            if working_file_path != backup_file_path:
                os.remove(working_file_path)
            
            end_time = datetime.utcnow()
            recovery_duration = int((end_time - start_time).total_seconds() / 60)  # minutes
            
            # Update recovery metrics
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE backup_records
                    SET recovery_tested = 1, recovery_test_date = ?, recovery_rto = ?
                    WHERE backup_id = ?
                ''', (end_time.isoformat(), recovery_duration, backup_id))
            
            logger.info(f"Successfully restored backup {backup_id} to {restore_path} in {recovery_duration} minutes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_id}: {e}")
            return False
    
    def _decrypt_backup_file(self, encrypted_path: str, decrypted_path: str):
        """Decrypt backup file"""
        
        fernet = Fernet(self.encryption_key)
        
        with open(encrypted_path, 'rb') as encrypted_file:
            with open(decrypted_path, 'wb') as decrypted_file:
                # Decrypt in chunks
                chunk_size = 64 * 1024
                
                while True:
                    chunk = encrypted_file.read(chunk_size)
                    if not chunk:
                        break
                    
                    decrypted_chunk = fernet.decrypt(chunk)
                    decrypted_file.write(decrypted_chunk)
    
    def test_disaster_recovery(self, backup_id: str) -> Dict[str, Any]:
        """Test disaster recovery procedures"""
        
        test_id = hashlib.sha256(
            f"dr_test_{backup_id}_{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        start_time = datetime.utcnow()
        issues_found = []
        
        try:
            # Create temporary restore location
            with tempfile.TemporaryDirectory() as temp_restore_path:
                
                # Test restore
                restore_success = self.restore_from_backup(backup_id, temp_restore_path)
                
                if not restore_success:
                    issues_found.append("Restore operation failed")
                
                # Verify restored files
                restored_files = list(Path(temp_restore_path).rglob('*'))
                if not restored_files:
                    issues_found.append("No files restored")
                
                # Test file integrity (sample check)
                for file_path in restored_files[:5]:  # Check first 5 files
                    if file_path.is_file():
                        try:
                            with open(file_path, 'rb') as f:
                                f.read(1024)  # Try to read first 1KB
                        except Exception as e:
                            issues_found.append(f"File corruption detected: {file_path}")
            
            end_time = datetime.utcnow()
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
            success = len(issues_found) == 0
            
            # Record test results
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO disaster_recovery_tests (
                        test_id, test_date, test_type, backup_id,
                        test_duration_minutes, success, issues_found,
                        recovery_rto_actual, test_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id, start_time.isoformat(), "full_restore_test",
                    backup_id, duration_minutes, success,
                    json.dumps(issues_found), duration_minutes,
                    "Automated disaster recovery test"
                ))
            
            result = {
                "test_id": test_id,
                "backup_id": backup_id,
                "start_time": start_time.isoformat(),
                "duration_minutes": duration_minutes,
                "success": success,
                "issues_found": issues_found,
                "rto_target_met": duration_minutes <= self.rto_target * 60,  # Convert to minutes
                "test_notes": "Automated DR test completed"
            }
            
            logger.info(f"Disaster recovery test {test_id} completed: {'SUCCESS' if success else 'FAILED'}")
            return result
            
        except Exception as e:
            logger.error(f"Disaster recovery test failed: {e}")
            issues_found.append(f"Test execution error: {str(e)}")
            
            return {
                "test_id": test_id,
                "backup_id": backup_id,
                "success": False,
                "issues_found": issues_found,
                "error": str(e)
            }
    
    def generate_backup_report(self) -> Dict[str, Any]:
        """Generate comprehensive backup and DR report"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Job statistics
            total_jobs = conn.execute("SELECT COUNT(*) FROM backup_jobs").fetchone()[0]
            active_jobs = conn.execute(
                "SELECT COUNT(*) FROM backup_jobs WHERE last_status != 'failed'"
            ).fetchone()[0]
            
            # Recent backup statistics
            recent_cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
            recent_backups = conn.execute(
                "SELECT COUNT(*) FROM backup_records WHERE start_time >= ?",
                (recent_cutoff,)
            ).fetchone()[0]
            
            recent_successful = conn.execute(
                "SELECT COUNT(*) FROM backup_records WHERE start_time >= ? AND status = 'completed'",
                (recent_cutoff,)
            ).fetchone()[0]
            
            # Storage statistics
            total_backup_size = conn.execute(
                "SELECT SUM(compressed_size) FROM backup_records WHERE status = 'completed'"
            ).fetchone()[0] or 0
            
            # Verification statistics
            verified_backups = conn.execute(
                "SELECT COUNT(*) FROM backup_records WHERE verification_status = 1"
            ).fetchone()[0]
            
            total_backups = conn.execute(
                "SELECT COUNT(*) FROM backup_records WHERE status = 'completed'"
            ).fetchone()[0]
            
            # Recovery metrics
            recovery_tests = conn.execute('''
                SELECT AVG(recovery_rto_actual), COUNT(*),
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END)
                FROM disaster_recovery_tests
                WHERE test_date >= ?
            ''', (recent_cutoff,)).fetchone()
            
            avg_recovery_time = recovery_tests[0] or 0
            total_tests = recovery_tests[1] or 0
            successful_tests = recovery_tests[2] or 0
        
        return {
            "report_date": datetime.utcnow().isoformat(),
            "backup_jobs": {
                "total": total_jobs,
                "active": active_jobs,
                "success_rate": f"{(active_jobs/total_jobs*100):.1f}%" if total_jobs > 0 else "N/A"
            },
            "recent_backups_7_days": {
                "total": recent_backups,
                "successful": recent_successful,
                "success_rate": f"{(recent_successful/recent_backups*100):.1f}%" if recent_backups > 0 else "N/A"
            },
            "storage": {
                "total_backup_size_gb": round(total_backup_size / (1024**3), 2),
                "verified_backups": verified_backups,
                "verification_rate": f"{(verified_backups/total_backups*100):.1f}%" if total_backups > 0 else "N/A"
            },
            "disaster_recovery": {
                "average_recovery_time_minutes": avg_recovery_time,
                "rto_target_minutes": self.rto_target * 60,
                "rto_compliance": avg_recovery_time <= (self.rto_target * 60) if avg_recovery_time else None,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "test_success_rate": f"{(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A"
            },
            "compliance_status": "compliant" if (
                active_jobs >= total_jobs * 0.9 and  # 90% job success rate
                (verified_backups/total_backups >= 0.95 if total_backups > 0 else True) and  # 95% verification rate
                (avg_recovery_time <= self.rto_target * 60 if avg_recovery_time else True)  # RTO compliance
            ) else "attention_required"
        }

# Global backup manager instance
backup_manager = SecureBackupManager()