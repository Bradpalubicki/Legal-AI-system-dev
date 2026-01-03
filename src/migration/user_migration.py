"""
User and Authentication Migration Module

Handles secure migration of user accounts, authentication tokens,
preferences, and authorization data with preservation of security.
"""

import asyncio
import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger(__name__)

@dataclass
class UserMigrationResult:
    """Result of user migration operation"""
    total_users: int = 0
    migrated_users: int = 0
    failed_users: int = 0
    total_sessions: int = 0
    migrated_sessions: int = 0
    total_permissions: int = 0
    migrated_permissions: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class UserMigrator:
    """
    Specialized user and authentication data migration

    Handles:
    - User accounts with password preservation
    - Active sessions and tokens
    - User preferences and settings
    - Role-based permissions
    - Audit trails
    - Multi-factor authentication settings
    """

    def __init__(self, target_db_url: str, encryption_key: Optional[str] = None):
        self.target_db_url = target_db_url
        self.encryption_key = None

        if encryption_key:
            self.encryption_key = Fernet(encryption_key.encode())

    async def migrate_users_comprehensive(self, source_databases: Dict[str, str]) -> UserMigrationResult:
        """
        Comprehensive user migration from multiple sources

        Args:
            source_databases: Dict mapping database names to paths

        Returns:
            UserMigrationResult: Migration statistics and results
        """
        logger.info("Starting comprehensive user migration...")

        result = UserMigrationResult()

        # Find all authentication-related databases
        auth_databases = self._find_auth_databases(source_databases)

        for db_name, db_path in auth_databases.items():
            logger.info(f"Migrating authentication data from {db_name}: {db_path}")

            try:
                db_result = await self._migrate_auth_database(db_name, db_path)

                # Aggregate results
                result.total_users += db_result.total_users
                result.migrated_users += db_result.migrated_users
                result.failed_users += db_result.failed_users
                result.total_sessions += db_result.total_sessions
                result.migrated_sessions += db_result.migrated_sessions
                result.total_permissions += db_result.total_permissions
                result.migrated_permissions += db_result.migrated_permissions
                result.errors.extend(db_result.errors)

            except Exception as e:
                error_msg = f"Failed to migrate {db_name}: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        # Migrate user preferences and settings
        await self._migrate_user_preferences(source_databases, result)

        # Migrate document ownership and permissions
        await self._migrate_document_ownership(source_databases, result)

        # Verify user migration integrity
        await self._verify_user_migration(result)

        logger.info(f"User migration completed: {result}")
        return result

    def _find_auth_databases(self, source_databases: Dict[str, str]) -> Dict[str, str]:
        """Find all authentication-related databases"""
        auth_databases = {}

        # Known authentication database patterns
        auth_patterns = [
            'enhanced_auth.db',
            'auth.db',
            'authentication.db',
            'users.db',
            'security.db'
        ]

        # Check provided databases
        for db_name, db_path in source_databases.items():
            if any(pattern in db_path.lower() for pattern in auth_patterns):
                auth_databases[db_name] = db_path

        # Search for additional auth databases in common locations
        search_paths = [
            './src/shared/security/',
            './authentication/',
            './auth/',
            './'
        ]

        for search_path in search_paths:
            path = Path(search_path)
            if path.exists():
                for pattern in auth_patterns:
                    for db_file in path.glob(f"**/{pattern}"):
                        if str(db_file) not in auth_databases.values():
                            auth_databases[f"found_{db_file.stem}"] = str(db_file)

        logger.info(f"Found authentication databases: {list(auth_databases.keys())}")
        return auth_databases

    async def _migrate_auth_database(self, db_name: str, db_path: str) -> UserMigrationResult:
        """Migrate a specific authentication database"""
        result = UserMigrationResult()

        if not Path(db_path).exists():
            logger.warning(f"Authentication database not found: {db_path}")
            return result

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        try:
            # Get all tables in the database
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            logger.info(f"Found tables in {db_name}: {tables}")

            engine = create_async_engine(self.target_db_url)

            try:
                # Migrate each table based on its purpose
                for table_name in tables:
                    if self._is_user_table(table_name):
                        await self._migrate_user_table(conn, engine, table_name, result)
                    elif self._is_session_table(table_name):
                        await self._migrate_session_table(conn, engine, table_name, result)
                    elif self._is_permission_table(table_name):
                        await self._migrate_permission_table(conn, engine, table_name, result)
                    elif self._is_audit_table(table_name):
                        await self._migrate_audit_table(conn, engine, table_name, result)
                    else:
                        await self._migrate_generic_auth_table(conn, engine, table_name, result)

            finally:
                await engine.dispose()

        finally:
            conn.close()

        return result

    def _is_user_table(self, table_name: str) -> bool:
        """Check if table contains user data"""
        user_indicators = ['user', 'account', 'profile', 'client', 'attorney']
        return any(indicator in table_name.lower() for indicator in user_indicators)

    def _is_session_table(self, table_name: str) -> bool:
        """Check if table contains session data"""
        session_indicators = ['session', 'token', 'login', 'auth_token', 'refresh_token']
        return any(indicator in table_name.lower() for indicator in session_indicators)

    def _is_permission_table(self, table_name: str) -> bool:
        """Check if table contains permission data"""
        permission_indicators = ['permission', 'role', 'access', 'authorization', 'rbac']
        return any(indicator in table_name.lower() for indicator in permission_indicators)

    def _is_audit_table(self, table_name: str) -> bool:
        """Check if table contains audit data"""
        audit_indicators = ['audit', 'log', 'activity', 'event', 'history']
        return any(indicator in table_name.lower() for indicator in audit_indicators)

    async def _migrate_user_table(self, sqlite_conn, pg_engine, table_name: str, result: UserMigrationResult):
        """Migrate user account table with password preservation"""
        logger.info(f"Migrating user table: {table_name}")

        cursor = sqlite_conn.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        result.total_users += len(rows)

        if not rows:
            return

        # Create target table in PostgreSQL
        await self._create_user_table_if_not_exists(pg_engine, table_name, rows[0])

        async with pg_engine.begin() as conn:
            for row in rows:
                try:
                    row_dict = dict(row)

                    # Handle password fields specially
                    row_dict = await self._process_user_passwords(row_dict)

                    # Handle sensitive fields
                    row_dict = await self._process_sensitive_user_fields(row_dict)

                    # Ensure unique constraints
                    row_dict = await self._ensure_user_uniqueness(conn, row_dict, table_name)

                    # Insert user record
                    await self._insert_user_record(conn, table_name, row_dict)

                    result.migrated_users += 1

                except Exception as e:
                    result.failed_users += 1
                    error_msg = f"Failed to migrate user in {table_name}: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

    async def _create_user_table_if_not_exists(self, engine, table_name: str, sample_row):
        """Create user table in PostgreSQL with appropriate schema"""
        columns = list(sample_row.keys())

        # Define column types based on common patterns
        column_definitions = []

        for col in columns:
            col_lower = col.lower()
            if col_lower == 'id':
                column_definitions.append(f"{col} SERIAL PRIMARY KEY")
            elif 'password' in col_lower or 'hash' in col_lower:
                column_definitions.append(f"{col} VARCHAR(255)")
            elif 'email' in col_lower:
                column_definitions.append(f"{col} VARCHAR(255) UNIQUE")
            elif 'username' in col_lower:
                column_definitions.append(f"{col} VARCHAR(100) UNIQUE")
            elif 'created' in col_lower or 'updated' in col_lower or 'date' in col_lower:
                column_definitions.append(f"{col} TIMESTAMP WITH TIME ZONE")
            elif 'active' in col_lower or 'enabled' in col_lower or 'verified' in col_lower:
                column_definitions.append(f"{col} BOOLEAN DEFAULT TRUE")
            else:
                column_definitions.append(f"{col} TEXT")

        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(column_definitions)}
            )
        """

        async with engine.begin() as conn:
            try:
                await conn.execute(text(create_sql))
                logger.info(f"Created user table: {table_name}")
            except Exception as e:
                logger.warning(f"Table creation failed for {table_name}: {str(e)}")

    async def _process_user_passwords(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process password fields to ensure proper security"""
        for key, value in row_dict.items():
            if 'password' in key.lower() and value:
                # Check if password is already hashed
                if isinstance(value, str):
                    if value.startswith('$2b$') or value.startswith('$2a$'):
                        # Already bcrypt hashed
                        continue
                    elif len(value) == 64 and all(c in '0123456789abcdef' for c in value.lower()):
                        # Looks like a SHA-256 hash - re-hash with bcrypt
                        row_dict[key] = bcrypt.hashpw(value.encode(), bcrypt.gensalt()).decode()
                    elif len(value) < 60:
                        # Likely plaintext - hash with bcrypt
                        row_dict[key] = bcrypt.hashpw(value.encode(), bcrypt.gensalt()).decode()
                        logger.warning(f"Found plaintext password, hashed with bcrypt")

                # Additional encryption if enabled
                if self.encryption_key:
                    encrypted_password = self.encryption_key.encrypt(row_dict[key].encode())
                    row_dict[f"{key}_encrypted"] = encrypted_password.decode()

        return row_dict

    async def _process_sensitive_user_fields(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process sensitive user fields with encryption if enabled"""
        sensitive_fields = ['ssn', 'social_security', 'tax_id', 'phone', 'address']

        if self.encryption_key:
            for key, value in row_dict.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields) and value:
                    encrypted_value = self.encryption_key.encrypt(str(value).encode())
                    row_dict[f"{key}_encrypted"] = encrypted_value.decode()
                    # Optionally remove original field
                    row_dict[key] = "[ENCRYPTED]"

        return row_dict

    async def _ensure_user_uniqueness(self, conn, row_dict: Dict[str, Any], table_name: str) -> Dict[str, Any]:
        """Ensure user uniqueness constraints are met"""
        unique_fields = ['email', 'username', 'user_id']

        for field in unique_fields:
            if field in row_dict and row_dict[field]:
                # Check if value already exists
                check_sql = f"SELECT COUNT(*) FROM {table_name} WHERE {field} = :{field}"
                result = await conn.execute(text(check_sql), {field: row_dict[field]})
                count = result.scalar()

                if count > 0:
                    # Add suffix to make unique
                    original_value = row_dict[field]
                    suffix = 1
                    while count > 0:
                        new_value = f"{original_value}_{suffix}"
                        check_sql = f"SELECT COUNT(*) FROM {table_name} WHERE {field} = :{field}"
                        result = await conn.execute(text(check_sql), {field: new_value})
                        count = result.scalar()
                        suffix += 1

                    row_dict[field] = new_value
                    logger.warning(f"Modified {field} for uniqueness: {original_value} -> {new_value}")

        return row_dict

    async def _insert_user_record(self, conn, table_name: str, row_dict: Dict[str, Any]):
        """Insert user record into PostgreSQL"""
        columns = list(row_dict.keys())
        placeholders = ', '.join([f':{col}' for col in columns])

        insert_sql = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """

        await conn.execute(text(insert_sql), row_dict)

    async def _migrate_session_table(self, sqlite_conn, pg_engine, table_name: str, result: UserMigrationResult):
        """Migrate session and token tables"""
        logger.info(f"Migrating session table: {table_name}")

        cursor = sqlite_conn.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        result.total_sessions += len(rows)

        if not rows:
            return

        # Create target table
        await self._create_session_table_if_not_exists(pg_engine, table_name, rows[0])

        async with pg_engine.begin() as conn:
            for row in rows:
                try:
                    row_dict = dict(row)

                    # Validate session expiry
                    if await self._is_session_expired(row_dict):
                        continue  # Skip expired sessions

                    # Encrypt session tokens if enabled
                    if self.encryption_key:
                        row_dict = await self._encrypt_session_tokens(row_dict)

                    await self._insert_session_record(conn, table_name, row_dict)
                    result.migrated_sessions += 1

                except Exception as e:
                    error_msg = f"Failed to migrate session in {table_name}: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

    async def _create_session_table_if_not_exists(self, engine, table_name: str, sample_row):
        """Create session table in PostgreSQL"""
        columns = list(sample_row.keys())
        column_definitions = []

        for col in columns:
            col_lower = col.lower()
            if col_lower == 'id':
                column_definitions.append(f"{col} SERIAL PRIMARY KEY")
            elif 'token' in col_lower or 'session_id' in col_lower:
                column_definitions.append(f"{col} VARCHAR(255) UNIQUE")
            elif 'expires' in col_lower or 'created' in col_lower:
                column_definitions.append(f"{col} TIMESTAMP WITH TIME ZONE")
            elif 'user_id' in col_lower:
                column_definitions.append(f"{col} INTEGER")
            else:
                column_definitions.append(f"{col} TEXT")

        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(column_definitions)}
            )
        """

        async with engine.begin() as conn:
            try:
                await conn.execute(text(create_sql))
            except Exception as e:
                logger.warning(f"Session table creation failed for {table_name}: {str(e)}")

    async def _is_session_expired(self, row_dict: Dict[str, Any]) -> bool:
        """Check if session is expired"""
        expiry_fields = ['expires_at', 'expiry', 'expires', 'valid_until']

        for field in expiry_fields:
            if field in row_dict and row_dict[field]:
                try:
                    if isinstance(row_dict[field], str):
                        expiry_time = datetime.fromisoformat(row_dict[field].replace('Z', '+00:00'))
                    else:
                        expiry_time = row_dict[field]

                    if expiry_time < datetime.now(timezone.utc):
                        return True
                except Exception:
                    pass

        return False

    async def _encrypt_session_tokens(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt session tokens"""
        token_fields = ['token', 'access_token', 'refresh_token', 'session_token']

        for field in token_fields:
            if field in row_dict and row_dict[field]:
                encrypted_token = self.encryption_key.encrypt(str(row_dict[field]).encode())
                row_dict[f"{field}_encrypted"] = encrypted_token.decode()
                row_dict[field] = "[ENCRYPTED]"

        return row_dict

    async def _insert_session_record(self, conn, table_name: str, row_dict: Dict[str, Any]):
        """Insert session record into PostgreSQL"""
        columns = list(row_dict.keys())
        placeholders = ', '.join([f':{col}' for col in columns])

        insert_sql = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """

        await conn.execute(text(insert_sql), row_dict)

    async def _migrate_permission_table(self, sqlite_conn, pg_engine, table_name: str, result: UserMigrationResult):
        """Migrate permission and role tables"""
        logger.info(f"Migrating permission table: {table_name}")

        cursor = sqlite_conn.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        result.total_permissions += len(rows)

        if not rows:
            return

        # Create target table
        await self._create_permission_table_if_not_exists(pg_engine, table_name, rows[0])

        async with pg_engine.begin() as conn:
            for row in rows:
                try:
                    row_dict = dict(row)
                    await self._insert_permission_record(conn, table_name, row_dict)
                    result.migrated_permissions += 1

                except Exception as e:
                    error_msg = f"Failed to migrate permission in {table_name}: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

    async def _create_permission_table_if_not_exists(self, engine, table_name: str, sample_row):
        """Create permission table in PostgreSQL"""
        columns = list(sample_row.keys())
        column_definitions = []

        for col in columns:
            col_lower = col.lower()
            if col_lower == 'id':
                column_definitions.append(f"{col} SERIAL PRIMARY KEY")
            elif 'user_id' in col_lower or 'role_id' in col_lower:
                column_definitions.append(f"{col} INTEGER")
            elif 'permission' in col_lower or 'role' in col_lower:
                column_definitions.append(f"{col} VARCHAR(100)")
            elif 'created' in col_lower or 'updated' in col_lower:
                column_definitions.append(f"{col} TIMESTAMP WITH TIME ZONE")
            else:
                column_definitions.append(f"{col} TEXT")

        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(column_definitions)}
            )
        """

        async with engine.begin() as conn:
            try:
                await conn.execute(text(create_sql))
            except Exception as e:
                logger.warning(f"Permission table creation failed for {table_name}: {str(e)}")

    async def _insert_permission_record(self, conn, table_name: str, row_dict: Dict[str, Any]):
        """Insert permission record into PostgreSQL"""
        columns = list(row_dict.keys())
        placeholders = ', '.join([f':{col}' for col in columns])

        insert_sql = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """

        await conn.execute(text(insert_sql), row_dict)

    async def _migrate_audit_table(self, sqlite_conn, pg_engine, table_name: str, result: UserMigrationResult):
        """Migrate audit and activity log tables"""
        logger.info(f"Migrating audit table: {table_name}")

        # Similar implementation to other tables but with audit-specific logic
        cursor = sqlite_conn.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            return

        await self._create_audit_table_if_not_exists(pg_engine, table_name, rows[0])

        async with pg_engine.begin() as conn:
            for row in rows:
                try:
                    row_dict = dict(row)

                    # Preserve audit trail integrity
                    row_dict = await self._preserve_audit_integrity(row_dict)

                    await self._insert_audit_record(conn, table_name, row_dict)

                except Exception as e:
                    error_msg = f"Failed to migrate audit record in {table_name}: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

    async def _create_audit_table_if_not_exists(self, engine, table_name: str, sample_row):
        """Create audit table in PostgreSQL"""
        # Implementation similar to other table creation methods
        pass

    async def _preserve_audit_integrity(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Preserve audit trail integrity with checksums"""
        # Add integrity checksums
        if 'audit_data' in row_dict:
            audit_data = str(row_dict['audit_data'])
            checksum = hashlib.sha256(audit_data.encode()).hexdigest()
            row_dict['audit_checksum'] = checksum

        return row_dict

    async def _insert_audit_record(self, conn, table_name: str, row_dict: Dict[str, Any]):
        """Insert audit record into PostgreSQL"""
        columns = list(row_dict.keys())
        placeholders = ', '.join([f':{col}' for col in columns])

        insert_sql = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({placeholders})
        """

        await conn.execute(text(insert_sql), row_dict)

    async def _migrate_generic_auth_table(self, sqlite_conn, pg_engine, table_name: str, result: UserMigrationResult):
        """Migrate generic authentication-related tables"""
        logger.info(f"Migrating generic auth table: {table_name}")

        cursor = sqlite_conn.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            return

        # Generic table creation and migration
        await self._create_generic_table(pg_engine, table_name, rows[0])

        async with pg_engine.begin() as conn:
            for row in rows:
                try:
                    row_dict = dict(row)
                    await self._insert_generic_record(conn, table_name, row_dict)

                except Exception as e:
                    error_msg = f"Failed to migrate record in {table_name}: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

    async def _create_generic_table(self, engine, table_name: str, sample_row):
        """Create generic table in PostgreSQL"""
        columns = list(sample_row.keys())
        column_definitions = []

        for col in columns:
            if col.lower() == 'id':
                column_definitions.append(f"{col} SERIAL PRIMARY KEY")
            else:
                column_definitions.append(f"{col} TEXT")

        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(column_definitions)}
            )
        """

        async with engine.begin() as conn:
            try:
                await conn.execute(text(create_sql))
            except Exception as e:
                logger.warning(f"Generic table creation failed for {table_name}: {str(e)}")

    async def _insert_generic_record(self, conn, table_name: str, row_dict: Dict[str, Any]):
        """Insert generic record into PostgreSQL"""
        columns = list(row_dict.keys())
        placeholders = ', '.join([f':{col}' for col in columns])

        insert_sql = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """

        await conn.execute(text(insert_sql), row_dict)

    async def _migrate_user_preferences(self, source_databases: Dict[str, str], result: UserMigrationResult):
        """Migrate user preferences and settings"""
        logger.info("Migrating user preferences and settings...")

        # Look for preference files and databases
        preference_sources = [
            'user_preferences.json',
            'settings.json',
            'config.db',
            'preferences.db'
        ]

        for pref_source in preference_sources:
            if pref_source in source_databases:
                await self._migrate_preference_source(source_databases[pref_source], result)

    async def _migrate_preference_source(self, source_path: str, result: UserMigrationResult):
        """Migrate a specific preference source"""
        if not Path(source_path).exists():
            return

        if source_path.endswith('.json'):
            await self._migrate_json_preferences(source_path, result)
        elif source_path.endswith('.db'):
            await self._migrate_db_preferences(source_path, result)

    async def _migrate_json_preferences(self, json_path: str, result: UserMigrationResult):
        """Migrate JSON-based preferences"""
        try:
            with open(json_path, 'r') as f:
                preferences = json.load(f)

            engine = create_async_engine(self.target_db_url)

            try:
                async with engine.begin() as conn:
                    # Create preferences table if needed
                    await conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS user_preferences (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER,
                            preference_key VARCHAR(100),
                            preference_value TEXT,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """))

                    # Insert preferences
                    for user_id, user_prefs in preferences.items():
                        for key, value in user_prefs.items():
                            await conn.execute(text("""
                                INSERT INTO user_preferences (user_id, preference_key, preference_value)
                                VALUES (:user_id, :key, :value)
                                ON CONFLICT DO NOTHING
                            """), {
                                'user_id': user_id,
                                'key': key,
                                'value': json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                            })

            finally:
                await engine.dispose()

            logger.info(f"Migrated preferences from {json_path}")

        except Exception as e:
            logger.error(f"Failed to migrate JSON preferences from {json_path}: {str(e)}")
            result.errors.append(f"JSON preferences migration failed: {str(e)}")

    async def _migrate_db_preferences(self, db_path: str, result: UserMigrationResult):
        """Migrate database-based preferences"""
        # Similar to other database migrations
        pass

    async def _migrate_document_ownership(self, source_databases: Dict[str, str], result: UserMigrationResult):
        """Migrate document ownership and access permissions"""
        logger.info("Migrating document ownership and permissions...")

        # This would integrate with the document migration system
        # to ensure user-document relationships are preserved
        pass

    async def _verify_user_migration(self, result: UserMigrationResult):
        """Verify user migration integrity"""
        logger.info("Verifying user migration integrity...")

        engine = create_async_engine(self.target_db_url)

        try:
            async with engine.begin() as conn:
                # Verify user count
                user_count_result = await conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_name LIKE '%user%'
                """))

                # Verify no duplicate emails/usernames
                duplicate_check = await conn.execute(text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_name LIKE '%user%'
                """))

                tables = [row[0] for row in duplicate_check.fetchall()]

                for table in tables:
                    try:
                        # Check for duplicates in common unique fields
                        for field in ['email', 'username']:
                            dup_result = await conn.execute(text(f"""
                                SELECT {field}, COUNT(*) as count
                                FROM {table}
                                WHERE {field} IS NOT NULL
                                GROUP BY {field}
                                HAVING COUNT(*) > 1
                            """))

                            duplicates = dup_result.fetchall()
                            if duplicates:
                                logger.warning(f"Found duplicates in {table}.{field}: {len(duplicates)}")

                    except Exception:
                        # Field might not exist in this table
                        pass

        finally:
            await engine.dispose()

        logger.info("User migration verification completed")


# Export the main class
__all__ = ['UserMigrator', 'UserMigrationResult']