#!/usr/bin/env python3
"""
Comprehensive Backup System
Legal AI System - Advanced Backup and Recovery Management

This module provides comprehensive backup and recovery capabilities
for the Legal AI system including database, file, and configuration backups.
"""

import os
import shutil
import sqlite3
import json
import logging
import hashlib
import gzip
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import threading
import schedule
import time

# Setup logging
logger = logging.getLogger('backup_system')

class BackupType(str, Enum):
    """Backup type categories"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"
    DATABASE = "database"
    FILES = "files"
    CONFIG = "config"

class BackupStatus(str, Enum):
    """Backup operation status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BackupJob:
    """Backup job configuration"""
    job_id: str
    name: str
    backup_type: BackupType
    source_paths: List[str]
    destination_path: str
    schedule_pattern: str
    retention_days: int
    compression: bool
    encryption: bool
    status: BackupStatus
    created_at: datetime
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

@dataclass
class BackupResult:
    """Backup operation result"""
    job_id: str
    backup_id: str
    start_time: datetime
    end_time: datetime
    status: BackupStatus
    files_backed_up: int
    total_size: int
    compressed_size: int
    backup_path: str
    checksum: str
    error_message: Optional[str] = None

class BackupSystem:
    """
    Comprehensive backup and recovery system
    Provides automated backups with retention policies and recovery capabilities
    """

    def __init__(self, backup_root: str = "backups"):
        self.logger = logger
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(exist_ok=True)

        self.jobs: Dict[str, BackupJob] = {}
        self.backup_history: List[BackupResult] = []
        self.running_backups: Dict[str, threading.Thread] = {}

        # Initialize backup directories
        self._initialize_backup_structure()

        # Load existing jobs
        self._load_backup_jobs()

        # Start scheduler
        self._start_scheduler()

    def _initialize_backup_structure(self):
        """Initialize backup directory structure"""
        directories = [
            "database",
            "files",
            "config",
            "full",
            "incremental",
            "logs",
            "temp"
        ]

        for directory in directories:
            (self.backup_root / directory).mkdir(exist_ok=True)

    def create_backup_job(self, name: str, backup_type: BackupType,
                         source_paths: List[str], destination_path: str = None,
                         schedule_pattern: str = "daily",
                         retention_days: int = 30,
                         compression: bool = True,
                         encryption: bool = True) -> str:
        """Create a new backup job"""
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if destination_path is None:
            destination_path = str(self.backup_root / backup_type.value)

        job = BackupJob(
            job_id=job_id,
            name=name,
            backup_type=backup_type,
            source_paths=source_paths,
            destination_path=destination_path,
            schedule_pattern=schedule_pattern,
            retention_days=retention_days,
            compression=compression,
            encryption=encryption,
            status=BackupStatus.PENDING,
            created_at=datetime.now()
        )

        self.jobs[job_id] = job
        self._save_backup_jobs()

        self.logger.info(f"Created backup job: {name} ({job_id})")
        return job_id

    def run_backup(self, job_id: str) -> BackupResult:
        """Execute a backup job"""
        if job_id not in self.jobs:
            raise ValueError(f"Backup job not found: {job_id}")

        job = self.jobs[job_id]

        if job_id in self.running_backups:
            raise RuntimeError(f"Backup job already running: {job_id}")

        # Start backup in separate thread for async operation
        def backup_thread():
            try:
                result = self._execute_backup(job)
                self.backup_history.append(result)
                job.last_run = result.end_time
                job.status = result.status
                self._save_backup_jobs()

                if job_id in self.running_backups:
                    del self.running_backups[job_id]

            except Exception as e:
                self.logger.error(f"Backup thread error: {e}")
                if job_id in self.running_backups:
                    del self.running_backups[job_id]

        thread = threading.Thread(target=backup_thread)
        self.running_backups[job_id] = thread
        thread.start()

        return self._create_pending_result(job)

    def _execute_backup(self, job: BackupJob) -> BackupResult:
        """Execute the actual backup operation"""
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()

        try:
            job.status = BackupStatus.RUNNING

            # Create backup destination
            backup_path = Path(job.destination_path) / backup_id

            if job.backup_type == BackupType.DATABASE:
                result = self._backup_database(job, backup_path, backup_id)
            elif job.backup_type == BackupType.FILES:
                result = self._backup_files(job, backup_path, backup_id)
            elif job.backup_type == BackupType.CONFIG:
                result = self._backup_config(job, backup_path, backup_id)
            elif job.backup_type == BackupType.FULL:
                result = self._backup_full_system(job, backup_path, backup_id)
            else:
                raise ValueError(f"Unsupported backup type: {job.backup_type}")

            # Apply retention policy
            self._apply_retention_policy(job)

            self.logger.info(f"Backup completed: {backup_id}")
            return result

        except Exception as e:
            end_time = datetime.now()
            error_result = BackupResult(
                job_id=job.job_id,
                backup_id=backup_id,
                start_time=start_time,
                end_time=end_time,
                status=BackupStatus.FAILED,
                files_backed_up=0,
                total_size=0,
                compressed_size=0,
                backup_path="",
                checksum="",
                error_message=str(e)
            )

            self.logger.error(f"Backup failed: {backup_id}, Error: {e}")
            return error_result

    def _backup_database(self, job: BackupJob, backup_path: Path, backup_id: str) -> BackupResult:
        """Backup database files"""
        backup_path.mkdir(parents=True, exist_ok=True)
        start_time = datetime.now()
        files_backed_up = 0
        total_size = 0

        try:
            for source_path in job.source_paths:
                source = Path(source_path)

                if source.suffix.lower() in ['.db', '.sqlite', '.sqlite3']:
                    # SQLite database backup
                    dest_file = backup_path / f"{source.name}_{backup_id}.db"

                    # Use SQLite backup API for consistency
                    self._backup_sqlite_database(str(source), str(dest_file))

                    files_backed_up += 1
                    total_size += dest_file.stat().st_size

                elif source.is_file():
                    # Regular file backup
                    dest_file = backup_path / source.name
                    shutil.copy2(source, dest_file)
                    files_backed_up += 1
                    total_size += dest_file.stat().st_size

            # Compress if requested
            compressed_size = total_size
            final_path = str(backup_path)

            if job.compression:
                compressed_path = f"{backup_path}.tar.gz"
                self._compress_directory(backup_path, compressed_path)
                shutil.rmtree(backup_path)
                final_path = compressed_path
                compressed_size = Path(compressed_path).stat().st_size

            # Calculate checksum
            checksum = self._calculate_checksum(final_path)

            return BackupResult(
                job_id=job.job_id,
                backup_id=backup_id,
                start_time=start_time,
                end_time=datetime.now(),
                status=BackupStatus.COMPLETED,
                files_backed_up=files_backed_up,
                total_size=total_size,
                compressed_size=compressed_size,
                backup_path=final_path,
                checksum=checksum
            )

        except Exception as e:
            raise RuntimeError(f"Database backup failed: {e}")

    def _backup_files(self, job: BackupJob, backup_path: Path, backup_id: str) -> BackupResult:
        """Backup file system files"""
        backup_path.mkdir(parents=True, exist_ok=True)
        start_time = datetime.now()
        files_backed_up = 0
        total_size = 0

        try:
            for source_path in job.source_paths:
                source = Path(source_path)

                if source.is_file():
                    dest_file = backup_path / source.name
                    shutil.copy2(source, dest_file)
                    files_backed_up += 1
                    total_size += dest_file.stat().st_size

                elif source.is_dir():
                    dest_dir = backup_path / source.name
                    shutil.copytree(source, dest_dir)

                    # Count files and calculate size
                    for file_path in dest_dir.rglob('*'):
                        if file_path.is_file():
                            files_backed_up += 1
                            total_size += file_path.stat().st_size

            # Compress if requested
            compressed_size = total_size
            final_path = str(backup_path)

            if job.compression:
                compressed_path = f"{backup_path}.tar.gz"
                self._compress_directory(backup_path, compressed_path)
                shutil.rmtree(backup_path)
                final_path = compressed_path
                compressed_size = Path(compressed_path).stat().st_size

            # Calculate checksum
            checksum = self._calculate_checksum(final_path)

            return BackupResult(
                job_id=job.job_id,
                backup_id=backup_id,
                start_time=start_time,
                end_time=datetime.now(),
                status=BackupStatus.COMPLETED,
                files_backed_up=files_backed_up,
                total_size=total_size,
                compressed_size=compressed_size,
                backup_path=final_path,
                checksum=checksum
            )

        except Exception as e:
            raise RuntimeError(f"File backup failed: {e}")

    def _backup_config(self, job: BackupJob, backup_path: Path, backup_id: str) -> BackupResult:
        """Backup configuration files"""
        backup_path.mkdir(parents=True, exist_ok=True)
        start_time = datetime.now()

        try:
            config_data = {
                "backup_id": backup_id,
                "timestamp": start_time.isoformat(),
                "system_info": self._get_system_info(),
                "job_configs": [asdict(j) for j in self.jobs.values()],
                "environment_vars": dict(os.environ),
                "backup_history": [asdict(h) for h in self.backup_history[-10:]]  # Last 10 backups
            }

            config_file = backup_path / f"system_config_{backup_id}.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)

            total_size = config_file.stat().st_size
            compressed_size = total_size
            final_path = str(backup_path)

            if job.compression:
                compressed_path = f"{backup_path}.tar.gz"
                self._compress_directory(backup_path, compressed_path)
                shutil.rmtree(backup_path)
                final_path = compressed_path
                compressed_size = Path(compressed_path).stat().st_size

            checksum = self._calculate_checksum(final_path)

            return BackupResult(
                job_id=job.job_id,
                backup_id=backup_id,
                start_time=start_time,
                end_time=datetime.now(),
                status=BackupStatus.COMPLETED,
                files_backed_up=1,
                total_size=total_size,
                compressed_size=compressed_size,
                backup_path=final_path,
                checksum=checksum
            )

        except Exception as e:
            raise RuntimeError(f"Config backup failed: {e}")

    def _backup_full_system(self, job: BackupJob, backup_path: Path, backup_id: str) -> BackupResult:
        """Backup full system (combination of database, files, and config)"""
        # This would combine all backup types
        # For now, implement as file backup
        return self._backup_files(job, backup_path, backup_id)

    def _backup_sqlite_database(self, source_db: str, dest_db: str):
        """Backup SQLite database using proper API"""
        try:
            source_conn = sqlite3.connect(source_db)
            dest_conn = sqlite3.connect(dest_db)
            source_conn.backup(dest_conn)
            source_conn.close()
            dest_conn.close()
        except Exception as e:
            # Fallback to file copy
            shutil.copy2(source_db, dest_db)

    def _compress_directory(self, directory: Path, output_path: str):
        """Compress directory to tar.gz"""
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(directory, arcname=directory.name)

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()

        if Path(file_path).is_file():
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def _apply_retention_policy(self, job: BackupJob):
        """Apply retention policy to remove old backups"""
        cutoff_date = datetime.now() - timedelta(days=job.retention_days)

        # Remove old backups
        backup_dir = Path(job.destination_path)
        if backup_dir.exists():
            for backup_item in backup_dir.iterdir():
                try:
                    # Check if backup is older than retention period
                    if backup_item.stat().st_mtime < cutoff_date.timestamp():
                        if backup_item.is_file():
                            backup_item.unlink()
                        elif backup_item.is_dir():
                            shutil.rmtree(backup_item)

                        self.logger.info(f"Removed old backup: {backup_item}")

                except Exception as e:
                    self.logger.error(f"Failed to remove old backup {backup_item}: {e}")

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for backup metadata"""
        import platform

        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "timestamp": datetime.now().isoformat()
        }

    def _create_pending_result(self, job: BackupJob) -> BackupResult:
        """Create a pending backup result"""
        return BackupResult(
            job_id=job.job_id,
            backup_id="pending",
            start_time=datetime.now(),
            end_time=datetime.now(),
            status=BackupStatus.PENDING,
            files_backed_up=0,
            total_size=0,
            compressed_size=0,
            backup_path="",
            checksum=""
        )

    def _load_backup_jobs(self):
        """Load backup jobs from configuration"""
        config_file = self.backup_root / "backup_jobs.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    jobs_data = json.load(f)

                for job_data in jobs_data:
                    job = BackupJob(**job_data)
                    self.jobs[job.job_id] = job

                self.logger.info(f"Loaded {len(self.jobs)} backup jobs")

            except Exception as e:
                self.logger.error(f"Failed to load backup jobs: {e}")

    def _save_backup_jobs(self):
        """Save backup jobs to configuration"""
        config_file = self.backup_root / "backup_jobs.json"
        try:
            jobs_data = [asdict(job) for job in self.jobs.values()]
            with open(config_file, 'w') as f:
                json.dump(jobs_data, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Failed to save backup jobs: {e}")

    def _start_scheduler(self):
        """Start backup scheduler"""
        def scheduler_thread():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        thread = threading.Thread(target=scheduler_thread, daemon=True)
        thread.start()

    def get_backup_status(self) -> Dict[str, Any]:
        """Get comprehensive backup system status"""
        total_backups = len(self.backup_history)
        successful_backups = len([b for b in self.backup_history if b.status == BackupStatus.COMPLETED])
        failed_backups = len([b for b in self.backup_history if b.status == BackupStatus.FAILED])

        success_rate = (successful_backups / total_backups * 100) if total_backups > 0 else 0

        return {
            "total_jobs": len(self.jobs),
            "running_backups": len(self.running_backups),
            "total_backups": total_backups,
            "successful_backups": successful_backups,
            "failed_backups": failed_backups,
            "success_rate": success_rate,
            "backup_storage_used": self._calculate_storage_usage(),
            "last_backup": self._get_last_backup_info()
        }

    def _calculate_storage_usage(self) -> int:
        """Calculate total backup storage usage"""
        total_size = 0
        for backup_dir in self.backup_root.iterdir():
            if backup_dir.is_dir():
                for item in backup_dir.rglob('*'):
                    if item.is_file():
                        total_size += item.stat().st_size
        return total_size

    def _get_last_backup_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the last backup"""
        if not self.backup_history:
            return None

        last_backup = max(self.backup_history, key=lambda b: b.end_time)
        return {
            "backup_id": last_backup.backup_id,
            "status": last_backup.status.value,
            "end_time": last_backup.end_time.isoformat(),
            "files_backed_up": last_backup.files_backed_up
        }

    def schedule_backup(self, job_id: str, schedule_expression: str) -> bool:
        """Schedule a backup job with cron-like expression"""
        try:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                job.schedule = schedule_expression
                job.enabled = True
                self._save_backup_jobs()
                self.logger.info(f"Scheduled backup job {job_id}: {schedule_expression}")
                return True
            else:
                self.logger.warning(f"Backup job not found: {job_id}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to schedule backup job {job_id}: {e}")
            return False

# Global backup system instance
backup_system = BackupSystem()

def create_database_backup() -> str:
    """Create a database backup job"""
    return backup_system.create_backup_job(
        name="Database Backup",
        backup_type=BackupType.DATABASE,
        source_paths=["*.db", "*.sqlite", "*.sqlite3"],
        schedule_pattern="daily",
        retention_days=30
    )

def create_config_backup() -> str:
    """Create a configuration backup job"""
    return backup_system.create_backup_job(
        name="Configuration Backup",
        backup_type=BackupType.CONFIG,
        source_paths=[".env", "config/", "settings/"],
        schedule_pattern="weekly",
        retention_days=90
    )

# Example usage and testing
if __name__ == "__main__":
    # Test the backup system
    print("Testing Backup System...")
    print("=" * 40)

    # Create test backup jobs
    db_job_id = create_database_backup()
    config_job_id = create_config_backup()

    print(f"Created database backup job: {db_job_id}")
    print(f"Created config backup job: {config_job_id}")

    # Get system status
    status = backup_system.get_backup_status()
    print(f"\nBackup System Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")

    print("\n✓ Backup system initialized successfully")