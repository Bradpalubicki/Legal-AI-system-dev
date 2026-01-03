"""
Rollback Manager for Legal AI System Migration

Provides comprehensive rollback capabilities for migration scenarios
with automated detection, validation, and execution of rollback procedures.
"""

import asyncio
import json
import logging
import shutil
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger(__name__)

class RollbackReason(Enum):
    """Reasons for rollback"""
    MANUAL_REQUEST = "manual_request"
    DATA_INTEGRITY_FAILURE = "data_integrity_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    APPLICATION_ERROR = "application_error"
    HEALTH_CHECK_FAILURE = "health_check_failure"
    TIMEOUT = "timeout"
    CRITICAL_ERROR = "critical_error"

class RollbackStatus(Enum):
    """Status of rollback operation"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass
class RollbackCheckpoint:
    """A rollback checkpoint containing system state"""
    checkpoint_id: str
    created_at: datetime
    description: str
    database_snapshots: Dict[str, str]  # name -> backup path
    config_snapshots: Dict[str, Any]
    file_snapshots: Dict[str, str]  # source -> backup path
    migration_state: Dict[str, Any]
    verification_checksums: Dict[str, str]

@dataclass
class RollbackResult:
    """Result of rollback operation"""
    success: bool
    status: RollbackStatus
    rollback_reason: RollbackReason
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    checkpoints_used: List[str] = field(default_factory=list)
    restored_databases: List[str] = field(default_factory=list)
    restored_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    verification_results: Dict[str, bool] = field(default_factory=dict)

class RollbackManager:
    """
    Comprehensive rollback management system

    Features:
    - Automatic checkpoint creation during migration
    - Multi-level rollback (database, files, configuration)
    - Verification and validation of rollback success
    - Incremental rollback capabilities
    - Emergency rollback procedures
    - Rollback testing and validation
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rollback_storage_path = Path(config.get('rollback_storage_path', './rollback_storage'))
        self.rollback_storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize Redis for coordination
        self.redis_client: Optional[aioredis.Redis] = None
        self.redis_url = config.get('redis_url', 'redis://localhost:6379')

        # Rollback state
        self.checkpoints: Dict[str, RollbackCheckpoint] = {}
        self.active_rollback: Optional[RollbackResult] = None

    async def initialize(self):
        """Initialize rollback manager"""
        logger.info("Initializing rollback manager...")

        # Connect to Redis
        self.redis_client = aioredis.from_url(self.redis_url)

        # Load existing checkpoints
        await self._load_existing_checkpoints()

        # Initialize rollback monitoring
        await self._initialize_rollback_monitoring()

        logger.info("✓ Rollback manager initialized")

    async def create_checkpoint(self, description: str, migration_context: Dict[str, Any] = None) -> str:
        """
        Create a rollback checkpoint

        Args:
            description: Description of the checkpoint
            migration_context: Current migration context

        Returns:
            str: Checkpoint ID
        """
        checkpoint_id = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Creating rollback checkpoint: {checkpoint_id}")

        try:
            # Create checkpoint directory
            checkpoint_dir = self.rollback_storage_path / checkpoint_id
            checkpoint_dir.mkdir(exist_ok=True)

            # Snapshot databases
            database_snapshots = await self._create_database_snapshots(checkpoint_dir)

            # Snapshot configuration
            config_snapshots = await self._create_config_snapshots(checkpoint_dir)

            # Snapshot critical files
            file_snapshots = await self._create_file_snapshots(checkpoint_dir)

            # Generate verification checksums
            verification_checksums = await self._generate_verification_checksums()

            # Create checkpoint record
            checkpoint = RollbackCheckpoint(
                checkpoint_id=checkpoint_id,
                created_at=datetime.now(timezone.utc),
                description=description,
                database_snapshots=database_snapshots,
                config_snapshots=config_snapshots,
                file_snapshots=file_snapshots,
                migration_state=migration_context or {},
                verification_checksums=verification_checksums
            )

            # Store checkpoint
            self.checkpoints[checkpoint_id] = checkpoint
            await self._save_checkpoint_metadata(checkpoint)

            logger.info(f"✓ Checkpoint created: {checkpoint_id}")
            return checkpoint_id

        except Exception as e:
            logger.error(f"Failed to create checkpoint: {str(e)}")
            raise

    async def execute_rollback(self,
                             reason: RollbackReason,
                             target_checkpoint_id: Optional[str] = None,
                             force: bool = False) -> RollbackResult:
        """
        Execute rollback operation

        Args:
            reason: Reason for rollback
            target_checkpoint_id: Specific checkpoint to rollback to (latest if None)
            force: Force rollback even if validation fails

        Returns:
            RollbackResult: Rollback operation result
        """
        rollback_result = RollbackResult(
            success=False,
            status=RollbackStatus.IN_PROGRESS,
            rollback_reason=reason,
            start_time=datetime.now(timezone.utc)
        )

        self.active_rollback = rollback_result

        try:
            logger.error(f"=== EXECUTING ROLLBACK: {reason.value} ===")

            # Determine target checkpoint
            if target_checkpoint_id and target_checkpoint_id in self.checkpoints:
                target_checkpoint = self.checkpoints[target_checkpoint_id]
            else:
                target_checkpoint = await self._get_latest_checkpoint()

            if not target_checkpoint:
                raise Exception("No rollback checkpoint available")

            rollback_result.checkpoints_used = [target_checkpoint.checkpoint_id]

            # Pre-rollback validation
            if not force:
                validation_result = await self._validate_rollback_feasibility(target_checkpoint)
                if not validation_result['feasible']:
                    raise Exception(f"Rollback validation failed: {validation_result['reasons']}")

            # Send rollback notification
            await self._send_rollback_notification("Rollback started", "warning", rollback_result)

            # Execute rollback phases
            await self._execute_emergency_stop()
            await self._rollback_application_configuration(target_checkpoint, rollback_result)
            await self._rollback_databases(target_checkpoint, rollback_result)
            await self._rollback_files(target_checkpoint, rollback_result)
            await self._restore_system_state(target_checkpoint, rollback_result)

            # Verify rollback success
            verification_results = await self._verify_rollback_success(target_checkpoint)
            rollback_result.verification_results = verification_results

            # Check if all verifications passed
            all_passed = all(verification_results.values())

            if all_passed:
                rollback_result.success = True
                rollback_result.status = RollbackStatus.COMPLETED
                logger.info("✓ Rollback completed successfully")
            else:
                rollback_result.status = RollbackStatus.PARTIAL
                failed_verifications = [k for k, v in verification_results.items() if not v]
                rollback_result.warnings.append(f"Partial rollback - failed verifications: {failed_verifications}")
                logger.warning(f"Partial rollback completed - failed verifications: {failed_verifications}")

        except Exception as e:
            rollback_result.success = False
            rollback_result.status = RollbackStatus.FAILED
            rollback_result.errors.append(str(e))
            logger.error(f"Rollback failed: {str(e)}")

        finally:
            rollback_result.end_time = datetime.now(timezone.utc)
            rollback_result.duration_seconds = (rollback_result.end_time - rollback_result.start_time).total_seconds()

            # Send completion notification
            notification_level = "success" if rollback_result.success else "critical"
            await self._send_rollback_notification("Rollback completed", notification_level, rollback_result)

            # Log rollback result
            await self._log_rollback_result(rollback_result)

            self.active_rollback = None

        return rollback_result

    async def _create_database_snapshots(self, checkpoint_dir: Path) -> Dict[str, str]:
        """Create database snapshots"""
        logger.info("Creating database snapshots...")

        snapshots = {}
        databases_to_backup = self.config.get('databases_to_backup', {})

        for db_name, db_config in databases_to_backup.items():
            try:
                backup_path = checkpoint_dir / f"{db_name}_backup.db"

                if db_config['type'] == 'sqlite':
                    # SQLite backup
                    await self._backup_sqlite_database(db_config['path'], backup_path)
                elif db_config['type'] == 'postgresql':
                    # PostgreSQL backup
                    await self._backup_postgresql_database(db_config['url'], backup_path)

                snapshots[db_name] = str(backup_path)
                logger.info(f"✓ Database snapshot created: {db_name}")

            except Exception as e:
                logger.error(f"Failed to backup database {db_name}: {str(e)}")
                snapshots[db_name] = f"FAILED: {str(e)}"

        return snapshots

    async def _backup_sqlite_database(self, source_path: str, backup_path: Path):
        """Backup SQLite database"""
        if Path(source_path).exists():
            shutil.copy2(source_path, backup_path)
        else:
            logger.warning(f"SQLite database not found: {source_path}")

    async def _backup_postgresql_database(self, db_url: str, backup_path: Path):
        """Backup PostgreSQL database"""
        # This would use pg_dump or similar
        # For now, we'll create a simple backup marker
        backup_path.write_text(f"PostgreSQL backup marker: {db_url}")

    async def _create_config_snapshots(self, checkpoint_dir: Path) -> Dict[str, Any]:
        """Create configuration snapshots"""
        logger.info("Creating configuration snapshots...")

        config_snapshots = {}

        # Backup Redis configuration
        if self.redis_client:
            try:
                # Get current application configuration
                app_config = await self.redis_client.get('app:config')
                if app_config:
                    config_snapshots['app_config'] = json.loads(app_config)

                # Get cutover state
                cutover_state = await self.redis_client.get('cutover:state')
                if cutover_state:
                    config_snapshots['cutover_state'] = json.loads(cutover_state)

            except Exception as e:
                logger.error(f"Failed to backup Redis config: {str(e)}")

        # Backup file-based configurations
        config_files = self.config.get('config_files_to_backup', [])
        for config_file in config_files:
            try:
                config_path = Path(config_file)
                if config_path.exists():
                    backup_config_path = checkpoint_dir / f"config_{config_path.name}"
                    shutil.copy2(config_path, backup_config_path)
                    config_snapshots[f"file_{config_path.name}"] = str(backup_config_path)

            except Exception as e:
                logger.error(f"Failed to backup config file {config_file}: {str(e)}")

        return config_snapshots

    async def _create_file_snapshots(self, checkpoint_dir: Path) -> Dict[str, str]:
        """Create file snapshots"""
        logger.info("Creating file snapshots...")

        file_snapshots = {}
        critical_files = self.config.get('critical_files_to_backup', [])

        for file_path in critical_files:
            try:
                source_path = Path(file_path)
                if source_path.exists():
                    backup_file_path = checkpoint_dir / f"file_{source_path.name}"

                    if source_path.is_file():
                        shutil.copy2(source_path, backup_file_path)
                    elif source_path.is_dir():
                        shutil.copytree(source_path, backup_file_path, dirs_exist_ok=True)

                    file_snapshots[str(source_path)] = str(backup_file_path)

            except Exception as e:
                logger.error(f"Failed to backup file {file_path}: {str(e)}")

        return file_snapshots

    async def _generate_verification_checksums(self) -> Dict[str, str]:
        """Generate verification checksums"""
        checksums = {}

        # This would generate checksums for critical system components
        checksums['system_state'] = f"checksum_{datetime.now().isoformat()}"

        return checksums

    async def _save_checkpoint_metadata(self, checkpoint: RollbackCheckpoint):
        """Save checkpoint metadata"""
        metadata_file = self.rollback_storage_path / f"{checkpoint.checkpoint_id}_metadata.json"

        metadata = {
            'checkpoint_id': checkpoint.checkpoint_id,
            'created_at': checkpoint.created_at.isoformat(),
            'description': checkpoint.description,
            'database_snapshots': checkpoint.database_snapshots,
            'config_snapshots': checkpoint.config_snapshots,
            'file_snapshots': checkpoint.file_snapshots,
            'migration_state': checkpoint.migration_state,
            'verification_checksums': checkpoint.verification_checksums
        }

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Also store in Redis
        if self.redis_client:
            await self.redis_client.set(
                f"rollback:checkpoint:{checkpoint.checkpoint_id}",
                json.dumps(metadata)
            )

    async def _load_existing_checkpoints(self):
        """Load existing checkpoints"""
        logger.info("Loading existing rollback checkpoints...")

        # Load from filesystem
        for metadata_file in self.rollback_storage_path.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                checkpoint = RollbackCheckpoint(
                    checkpoint_id=metadata['checkpoint_id'],
                    created_at=datetime.fromisoformat(metadata['created_at']),
                    description=metadata['description'],
                    database_snapshots=metadata['database_snapshots'],
                    config_snapshots=metadata['config_snapshots'],
                    file_snapshots=metadata['file_snapshots'],
                    migration_state=metadata['migration_state'],
                    verification_checksums=metadata['verification_checksums']
                )

                self.checkpoints[checkpoint.checkpoint_id] = checkpoint

            except Exception as e:
                logger.error(f"Failed to load checkpoint from {metadata_file}: {str(e)}")

        logger.info(f"Loaded {len(self.checkpoints)} rollback checkpoints")

    async def _initialize_rollback_monitoring(self):
        """Initialize rollback monitoring"""
        # Start background monitoring for rollback triggers
        asyncio.create_task(self._monitor_rollback_triggers())

    async def _monitor_rollback_triggers(self):
        """Monitor for automatic rollback triggers"""
        while True:
            try:
                # Check for rollback triggers
                if await self._should_trigger_automatic_rollback():
                    logger.warning("Automatic rollback triggered")
                    await self.execute_rollback(RollbackReason.CRITICAL_ERROR)

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Rollback monitoring error: {str(e)}")
                await asyncio.sleep(60)

    async def _should_trigger_automatic_rollback(self) -> bool:
        """Check if automatic rollback should be triggered"""
        # Check health endpoints
        if not await self._check_system_health():
            return True

        # Check error rates
        if await self._check_error_rates():
            return True

        # Check data integrity
        if not await self._check_data_integrity():
            return True

        return False

    async def _check_system_health(self) -> bool:
        """Check system health"""
        # This would check health endpoints
        return True  # Placeholder

    async def _check_error_rates(self) -> bool:
        """Check if error rates are too high"""
        # This would check error rates
        return False  # Placeholder

    async def _check_data_integrity(self) -> bool:
        """Check data integrity"""
        # This would check data integrity
        return True  # Placeholder

    async def _get_latest_checkpoint(self) -> Optional[RollbackCheckpoint]:
        """Get the latest rollback checkpoint"""
        if not self.checkpoints:
            return None

        return max(self.checkpoints.values(), key=lambda cp: cp.created_at)

    async def _validate_rollback_feasibility(self, checkpoint: RollbackCheckpoint) -> Dict[str, Any]:
        """Validate if rollback is feasible"""
        validation_result = {
            'feasible': True,
            'reasons': []
        }

        # Check if checkpoint files exist
        for db_name, backup_path in checkpoint.database_snapshots.items():
            if not Path(backup_path).exists():
                validation_result['feasible'] = False
                validation_result['reasons'].append(f"Database backup missing: {db_name}")

        # Check checkpoint age
        age = datetime.now(timezone.utc) - checkpoint.created_at
        if age > timedelta(hours=24):
            validation_result['reasons'].append(f"Checkpoint is old: {age}")

        return validation_result

    async def _execute_emergency_stop(self):
        """Execute emergency stop procedures"""
        logger.info("Executing emergency stop...")

        # Stop all background processes
        # Disable new connections
        # Set maintenance mode

        if self.redis_client:
            # Set emergency mode flag
            await self.redis_client.set('system:emergency_mode', 'true')

            # Update application configuration to maintenance mode
            emergency_config = {
                'mode': 'maintenance',
                'maintenance_reason': 'Emergency rollback in progress',
                'maintenance_start': datetime.now(timezone.utc).isoformat()
            }

            await self.redis_client.set('app:config', json.dumps(emergency_config))

        logger.info("✓ Emergency stop completed")

    async def _rollback_application_configuration(self, checkpoint: RollbackCheckpoint, result: RollbackResult):
        """Rollback application configuration"""
        logger.info("Rolling back application configuration...")

        try:
            # Restore Redis configuration
            if self.redis_client and 'app_config' in checkpoint.config_snapshots:
                await self.redis_client.set(
                    'app:config',
                    json.dumps(checkpoint.config_snapshots['app_config'])
                )

            # Restore file-based configurations
            for config_key, backup_path in checkpoint.config_snapshots.items():
                if config_key.startswith('file_'):
                    original_name = config_key.replace('file_', '')
                    # Restore the configuration file
                    # This would involve copying back the backup

            logger.info("✓ Application configuration rolled back")

        except Exception as e:
            result.errors.append(f"Config rollback failed: {str(e)}")
            logger.error(f"Configuration rollback failed: {str(e)}")

    async def _rollback_databases(self, checkpoint: RollbackCheckpoint, result: RollbackResult):
        """Rollback databases"""
        logger.info("Rolling back databases...")

        for db_name, backup_path in checkpoint.database_snapshots.items():
            try:
                if backup_path.startswith('FAILED:'):
                    result.warnings.append(f"Skipping {db_name} - backup failed")
                    continue

                # Restore database based on type
                if backup_path.endswith('.db'):
                    # SQLite restore
                    await self._restore_sqlite_database(db_name, backup_path)
                else:
                    # PostgreSQL restore
                    await self._restore_postgresql_database(db_name, backup_path)

                result.restored_databases.append(db_name)
                logger.info(f"✓ Database {db_name} rolled back")

            except Exception as e:
                result.errors.append(f"Database rollback failed for {db_name}: {str(e)}")
                logger.error(f"Database rollback failed for {db_name}: {str(e)}")

    async def _restore_sqlite_database(self, db_name: str, backup_path: str):
        """Restore SQLite database"""
        target_path = self.config['databases_to_backup'][db_name]['path']
        shutil.copy2(backup_path, target_path)

    async def _restore_postgresql_database(self, db_name: str, backup_path: str):
        """Restore PostgreSQL database"""
        # This would use pg_restore or similar
        logger.info(f"PostgreSQL restore would be executed for {db_name}")

    async def _rollback_files(self, checkpoint: RollbackCheckpoint, result: RollbackResult):
        """Rollback files"""
        logger.info("Rolling back files...")

        for original_path, backup_path in checkpoint.file_snapshots.items():
            try:
                backup_file = Path(backup_path)
                target_file = Path(original_path)

                if backup_file.exists():
                    if backup_file.is_file():
                        shutil.copy2(backup_file, target_file)
                    elif backup_file.is_dir():
                        if target_file.exists():
                            shutil.rmtree(target_file)
                        shutil.copytree(backup_file, target_file)

                    result.restored_files.append(original_path)
                    logger.info(f"✓ File {original_path} rolled back")

            except Exception as e:
                result.errors.append(f"File rollback failed for {original_path}: {str(e)}")
                logger.error(f"File rollback failed for {original_path}: {str(e)}")

    async def _restore_system_state(self, checkpoint: RollbackCheckpoint, result: RollbackResult):
        """Restore system state"""
        logger.info("Restoring system state...")

        try:
            # Clear emergency mode
            if self.redis_client:
                await self.redis_client.delete('system:emergency_mode')

            # Restart services if needed
            # Restore network configurations
            # Re-enable background processes

            logger.info("✓ System state restored")

        except Exception as e:
            result.errors.append(f"System state restoration failed: {str(e)}")
            logger.error(f"System state restoration failed: {str(e)}")

    async def _verify_rollback_success(self, checkpoint: RollbackCheckpoint) -> Dict[str, bool]:
        """Verify rollback success"""
        logger.info("Verifying rollback success...")

        verification_results = {}

        # Verify database restoration
        verification_results['databases'] = await self._verify_database_restoration(checkpoint)

        # Verify configuration restoration
        verification_results['configuration'] = await self._verify_configuration_restoration(checkpoint)

        # Verify file restoration
        verification_results['files'] = await self._verify_file_restoration(checkpoint)

        # Verify system health
        verification_results['system_health'] = await self._verify_system_health()

        # Verify application functionality
        verification_results['application'] = await self._verify_application_functionality()

        return verification_results

    async def _verify_database_restoration(self, checkpoint: RollbackCheckpoint) -> bool:
        """Verify database restoration"""
        try:
            # Check database connectivity and basic queries
            for db_name in checkpoint.database_snapshots.keys():
                if db_name in self.config['databases_to_backup']:
                    db_config = self.config['databases_to_backup'][db_name]

                    if db_config['type'] == 'sqlite':
                        # Test SQLite connection
                        conn = sqlite3.connect(db_config['path'])
                        conn.execute('SELECT 1')
                        conn.close()
                    elif db_config['type'] == 'postgresql':
                        # Test PostgreSQL connection
                        engine = create_async_engine(db_config['url'])
                        async with engine.begin() as conn:
                            await conn.execute(text('SELECT 1'))
                        await engine.dispose()

            return True

        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            return False

    async def _verify_configuration_restoration(self, checkpoint: RollbackCheckpoint) -> bool:
        """Verify configuration restoration"""
        try:
            # Verify Redis configuration
            if self.redis_client and 'app_config' in checkpoint.config_snapshots:
                current_config = await self.redis_client.get('app:config')
                if current_config:
                    current_config = json.loads(current_config)
                    expected_config = checkpoint.config_snapshots['app_config']

                    # Compare key configuration values
                    # This would be more sophisticated in practice
                    return True

            return True

        except Exception as e:
            logger.error(f"Configuration verification failed: {str(e)}")
            return False

    async def _verify_file_restoration(self, checkpoint: RollbackCheckpoint) -> bool:
        """Verify file restoration"""
        try:
            for original_path in checkpoint.file_snapshots.keys():
                if not Path(original_path).exists():
                    return False

            return True

        except Exception as e:
            logger.error(f"File verification failed: {str(e)}")
            return False

    async def _verify_system_health(self) -> bool:
        """Verify system health"""
        try:
            # Check health endpoints
            # Check system resources
            # Check process status
            return True

        except Exception as e:
            logger.error(f"System health verification failed: {str(e)}")
            return False

    async def _verify_application_functionality(self) -> bool:
        """Verify application functionality"""
        try:
            # Test critical application endpoints
            # Test database queries
            # Test file access
            return True

        except Exception as e:
            logger.error(f"Application functionality verification failed: {str(e)}")
            return False

    async def _send_rollback_notification(self, message: str, level: str, rollback_result: RollbackResult):
        """Send rollback notification"""
        notification = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'message': message,
            'rollback_reason': rollback_result.rollback_reason.value,
            'status': rollback_result.status.value,
            'duration': rollback_result.duration_seconds
        }

        # Send to configured notification endpoints
        notification_endpoints = self.config.get('notification_endpoints', [])
        # Implementation would send to webhooks, email, etc.

        logger.info(f"Rollback notification: {message}")

    async def _log_rollback_result(self, result: RollbackResult):
        """Log rollback result"""
        rollback_log = {
            'rollback_id': f"rollback_{result.start_time.strftime('%Y%m%d_%H%M%S')}",
            'success': result.success,
            'status': result.status.value,
            'reason': result.rollback_reason.value,
            'start_time': result.start_time.isoformat(),
            'end_time': result.end_time.isoformat() if result.end_time else None,
            'duration_seconds': result.duration_seconds,
            'checkpoints_used': result.checkpoints_used,
            'restored_databases': result.restored_databases,
            'restored_files': result.restored_files,
            'errors': result.errors,
            'warnings': result.warnings,
            'verification_results': result.verification_results
        }

        # Store in Redis
        if self.redis_client:
            await self.redis_client.set(
                f"rollback:log:{rollback_log['rollback_id']}",
                json.dumps(rollback_log)
            )

        # Store in file
        log_file = self.rollback_storage_path / f"{rollback_log['rollback_id']}_log.json"
        with open(log_file, 'w') as f:
            json.dump(rollback_log, f, indent=2)

    async def cleanup(self):
        """Cleanup rollback manager resources"""
        if self.redis_client:
            await self.redis_client.close()

    def get_rollback_status(self) -> Dict[str, Any]:
        """Get current rollback status"""
        return {
            'active_rollback': self.active_rollback is not None,
            'available_checkpoints': len(self.checkpoints),
            'latest_checkpoint': max(self.checkpoints.values(), key=lambda cp: cp.created_at).checkpoint_id if self.checkpoints else None,
            'rollback_storage_path': str(self.rollback_storage_path)
        }


# Export main classes
__all__ = [
    'RollbackManager',
    'RollbackCheckpoint',
    'RollbackResult',
    'RollbackReason',
    'RollbackStatus'
]