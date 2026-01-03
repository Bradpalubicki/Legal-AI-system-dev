#!/usr/bin/env python3
"""
Database Migration Script for Attorney-Client Privilege Protection System
Creates all necessary database tables and indexes for privilege protection,
document encryption, access control, and data retention.
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
import argparse
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrivilegeProtectionMigration:
    """Database migration manager for privilege protection system"""

    def __init__(self, database_path: str = "legal_ai_system.db"):
        self.database_path = database_path
        self.migration_log: List[Dict] = []

    def run_migration(self, force_recreate: bool = False) -> bool:
        """Run complete privilege protection database migration"""
        try:
            logger.info("Starting privilege protection database migration...")
            
            # Check if database exists and tables exist
            if os.path.exists(self.database_path) and not force_recreate:
                if self._check_existing_tables():
                    logger.info("Privilege protection tables already exist. Use --force to recreate.")
                    return True
            
            # Backup existing database if it exists
            if os.path.exists(self.database_path):
                self._backup_database()
            
            # Create all privilege protection tables
            self._create_privilege_tables()
            self._create_encryption_tables()
            self._create_access_control_tables()
            self._create_retention_tables()
            
            # Create indexes for performance
            self._create_indexes()
            
            # Insert default policies and configurations
            self._insert_default_data()
            
            # Log migration completion
            self._log_migration_complete()
            
            logger.info("Privilege protection database migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self._rollback_migration()
            return False

    def _check_existing_tables(self) -> bool:
        """Check if privilege protection tables already exist"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            required_tables = [
                'privilege_assertions', 'privilege_access_log', 'privilege_waivers',
                'encryption_keys', 'key_rotation_log',
                'matter_access', 'conflict_checks', 'access_grants', 'access_audit_log',
                'retention_policies', 'document_retention', 'legal_holds', 'destruction_log'
            ]
            
            for table in required_tables:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
                if not cursor.fetchone():
                    conn.close()
                    return False
            
            conn.close()
            return True
            
        except Exception as e:
            logger.warning(f"Error checking existing tables: {e}")
            return False

    def _backup_database(self):
        """Create backup of existing database"""
        try:
            backup_path = f"{self.database_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Simple file copy for SQLite
            import shutil
            shutil.copy2(self.database_path, backup_path)
            
            logger.info(f"Database backed up to: {backup_path}")
            self.migration_log.append({
                "action": "backup_created",
                "path": backup_path,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            raise

    def _create_privilege_tables(self):
        """Create privilege management tables"""
        logger.info("Creating privilege management tables...")
        
        conn = sqlite3.connect(self.database_path)
        conn.executescript('''
            -- Privileged documents registry
            CREATE TABLE IF NOT EXISTS privilege_assertions (
                document_id TEXT PRIMARY KEY,
                privilege_type TEXT NOT NULL CHECK (privilege_type IN (
                    'attorney_client', 'work_product', 'joint_defense', 
                    'common_interest', 'settlement', 'mediation', 'consultant'
                )),
                client_id TEXT NOT NULL,
                matter_id TEXT NOT NULL,
                attorney_id TEXT NOT NULL,
                assertion_date TEXT NOT NULL,
                asserted_by TEXT NOT NULL,
                privilege_log_entry TEXT NOT NULL,
                waived INTEGER DEFAULT 0 CHECK (waived IN (0, 1)),
                waived_date TEXT,
                waived_by TEXT,
                disclosure_recipients TEXT, -- JSON array
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                -- Foreign key constraints would be added based on main schema
                CONSTRAINT fk_privilege_client FOREIGN KEY (client_id) REFERENCES clients (id),
                CONSTRAINT fk_privilege_matter FOREIGN KEY (matter_id) REFERENCES matters (id),
                CONSTRAINT fk_privilege_attorney FOREIGN KEY (attorney_id) REFERENCES users (id)
            );

            -- Privilege access audit log
            CREATE TABLE IF NOT EXISTS privilege_access_log (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                document_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                access_type TEXT NOT NULL CHECK (access_type IN (
                    'PRIVILEGE_ASSERTED', 'ACCESS_DENIED', 'PRIVILEGE_WAIVED', 
                    'ACCESS_GRANTED', 'DOCUMENT_VIEWED', 'DOCUMENT_DOWNLOADED'
                )),
                access_date TEXT NOT NULL DEFAULT (datetime('now')),
                ip_address TEXT,
                user_agent TEXT,
                justification TEXT,
                approved_by TEXT,
                session_id TEXT,
                CONSTRAINT fk_access_log_document FOREIGN KEY (document_id) REFERENCES privilege_assertions (document_id),
                CONSTRAINT fk_access_log_user FOREIGN KEY (user_id) REFERENCES users (id)
            );

            -- Privilege waiver log with detailed tracking
            CREATE TABLE IF NOT EXISTS privilege_waivers (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                document_id TEXT NOT NULL,
                waived_by TEXT NOT NULL,
                waiver_date TEXT NOT NULL DEFAULT (datetime('now')),
                waiver_reason TEXT NOT NULL,
                scope_of_waiver TEXT NOT NULL,
                recipients TEXT, -- JSON array
                client_consent TEXT NOT NULL, -- Details of client consent
                attorney_approval TEXT NOT NULL,
                partial_waiver INTEGER DEFAULT 0 CHECK (partial_waiver IN (0, 1)),
                waiver_conditions TEXT, -- Any conditions on the waiver
                effective_date TEXT,
                expiration_date TEXT,
                CONSTRAINT fk_waiver_document FOREIGN KEY (document_id) REFERENCES privilege_assertions (document_id),
                CONSTRAINT fk_waiver_attorney FOREIGN KEY (waived_by) REFERENCES users (id)
            );

            -- Privilege protection settings per client/matter
            CREATE TABLE IF NOT EXISTS privilege_settings (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                client_id TEXT NOT NULL,
                matter_id TEXT,
                auto_privilege_detection INTEGER DEFAULT 1 CHECK (auto_privilege_detection IN (0, 1)),
                require_explicit_assertion INTEGER DEFAULT 0 CHECK (require_explicit_assertion IN (0, 1)),
                allow_privilege_waiver INTEGER DEFAULT 1 CHECK (allow_privilege_waiver IN (0, 1)),
                waiver_approval_required INTEGER DEFAULT 1 CHECK (waiver_approval_required IN (0, 1)),
                privilege_log_required INTEGER DEFAULT 1 CHECK (privilege_log_required IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(client_id, matter_id)
            );
        ''')
        
        conn.commit()
        conn.close()
        
        self.migration_log.append({
            "action": "privilege_tables_created",
            "timestamp": datetime.now().isoformat()
        })

    def _create_encryption_tables(self):
        """Create document encryption tables"""
        logger.info("Creating document encryption tables...")
        
        conn = sqlite3.connect(self.database_path)
        conn.executescript('''
            -- Encryption key registry
            CREATE TABLE IF NOT EXISTS encryption_keys (
                key_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                matter_id TEXT,
                key_hash TEXT NOT NULL, -- SHA-256 hash of the key for verification
                algorithm TEXT NOT NULL DEFAULT 'AES-256-CBC',
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                last_rotation TEXT NOT NULL DEFAULT (datetime('now')),
                rotation_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'revoked')),
                expiry_date TEXT, -- Optional key expiration
                created_by TEXT,
                notes TEXT,
                UNIQUE(client_id, matter_id),
                CONSTRAINT fk_encryption_client FOREIGN KEY (client_id) REFERENCES clients (id),
                CONSTRAINT fk_encryption_matter FOREIGN KEY (matter_id) REFERENCES matters (id)
            );

            -- Key rotation audit log
            CREATE TABLE IF NOT EXISTS key_rotation_log (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                key_id TEXT NOT NULL,
                old_key_hash TEXT NOT NULL,
                new_key_hash TEXT NOT NULL,
                rotation_date TEXT NOT NULL DEFAULT (datetime('now')),
                rotated_by TEXT NOT NULL,
                rotation_reason TEXT,
                rotation_method TEXT DEFAULT 'scheduled' CHECK (rotation_method IN (
                    'scheduled', 'manual', 'security_incident', 'compliance'
                )),
                verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN (
                    'pending', 'verified', 'failed'
                )),
                CONSTRAINT fk_rotation_key FOREIGN KEY (key_id) REFERENCES encryption_keys (key_id),
                CONSTRAINT fk_rotation_user FOREIGN KEY (rotated_by) REFERENCES users (id)
            );

            -- Document encryption registry
            CREATE TABLE IF NOT EXISTS document_encryption (
                document_id TEXT PRIMARY KEY,
                key_id TEXT NOT NULL,
                encryption_date TEXT NOT NULL DEFAULT (datetime('now')),
                encryption_algorithm TEXT NOT NULL DEFAULT 'AES-256-CBC',
                iv_hash TEXT, -- Hash of initialization vector for verification
                file_hash_original TEXT, -- Hash of original file
                file_hash_encrypted TEXT, -- Hash of encrypted file
                encryption_status TEXT DEFAULT 'encrypted' CHECK (encryption_status IN (
                    'encrypted', 'decrypted', 'corrupted', 'key_lost'
                )),
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0,
                CONSTRAINT fk_doc_encryption_key FOREIGN KEY (key_id) REFERENCES encryption_keys (key_id)
            );

            -- Encryption audit log
            CREATE TABLE IF NOT EXISTS encryption_audit_log (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                document_id TEXT NOT NULL,
                action TEXT NOT NULL CHECK (action IN (
                    'ENCRYPTED', 'DECRYPTED', 'KEY_ROTATED', 'ACCESS_GRANTED', 
                    'ACCESS_DENIED', 'CORRUPTION_DETECTED'
                )),
                user_id TEXT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                ip_address TEXT,
                success INTEGER NOT NULL CHECK (success IN (0, 1)),
                error_message TEXT,
                additional_data TEXT, -- JSON for extra context
                CONSTRAINT fk_enc_audit_doc FOREIGN KEY (document_id) REFERENCES document_encryption (document_id)
            );
        ''')
        
        conn.commit()
        conn.close()
        
        self.migration_log.append({
            "action": "encryption_tables_created",
            "timestamp": datetime.now().isoformat()
        })

    def _create_access_control_tables(self):
        """Create access control and Chinese wall tables"""
        logger.info("Creating access control tables...")
        
        conn = sqlite3.connect(self.database_path)
        conn.executescript('''
            -- Matter access permissions with role-based controls
            CREATE TABLE IF NOT EXISTS matter_access (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id TEXT NOT NULL,
                client_id TEXT NOT NULL,
                matter_id TEXT NOT NULL,
                access_level INTEGER NOT NULL CHECK (access_level BETWEEN 0 AND 5),
                -- 0=NONE, 1=READ_ONLY, 2=COMMENT, 3=EDIT, 4=FULL_CONTROL, 5=ADMINISTRATIVE
                granted_by TEXT NOT NULL,
                granted_date TEXT NOT NULL DEFAULT (datetime('now')),
                expiration_date TEXT,
                active INTEGER DEFAULT 1 CHECK (active IN (0, 1)),
                conditions TEXT, -- JSON for access conditions
                delegation_allowed INTEGER DEFAULT 0 CHECK (delegation_allowed IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, matter_id),
                CONSTRAINT fk_matter_access_user FOREIGN KEY (user_id) REFERENCES users (id),
                CONSTRAINT fk_matter_access_client FOREIGN KEY (client_id) REFERENCES clients (id),
                CONSTRAINT fk_matter_access_matter FOREIGN KEY (matter_id) REFERENCES matters (id),
                CONSTRAINT fk_matter_access_grantor FOREIGN KEY (granted_by) REFERENCES users (id)
            );

            -- Conflict checks and Chinese wall implementation
            CREATE TABLE IF NOT EXISTS conflict_checks (
                check_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id TEXT NOT NULL,
                client_id TEXT NOT NULL,
                matter_id TEXT NOT NULL,
                opposing_parties TEXT NOT NULL, -- JSON array of opposing party IDs
                status TEXT NOT NULL CHECK (status IN (
                    'clear', 'potential', 'actual', 'waived', 'blocked'
                )),
                checked_date TEXT NOT NULL DEFAULT (datetime('now')),
                checked_by TEXT NOT NULL,
                resolution_notes TEXT,
                waiver_signed INTEGER DEFAULT 0 CHECK (waiver_signed IN (0, 1)),
                waiver_date TEXT,
                waiver_document_id TEXT,
                ethical_screen_applied INTEGER DEFAULT 0 CHECK (ethical_screen_applied IN (0, 1)),
                screen_description TEXT,
                periodic_review_required INTEGER DEFAULT 0 CHECK (periodic_review_required IN (0, 1)),
                next_review_date TEXT,
                CONSTRAINT fk_conflict_user FOREIGN KEY (user_id) REFERENCES users (id),
                CONSTRAINT fk_conflict_client FOREIGN KEY (client_id) REFERENCES clients (id),
                CONSTRAINT fk_conflict_checker FOREIGN KEY (checked_by) REFERENCES users (id)
            );

            -- Temporary access grants with detailed tracking
            CREATE TABLE IF NOT EXISTS access_grants (
                grant_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id TEXT NOT NULL,
                resource_type TEXT NOT NULL CHECK (resource_type IN ('DOCUMENT', 'MATTER', 'CLIENT')),
                resource_id TEXT NOT NULL,
                access_level INTEGER NOT NULL CHECK (access_level BETWEEN 0 AND 5),
                granted_by TEXT NOT NULL,
                granted_date TEXT NOT NULL DEFAULT (datetime('now')),
                expiration_date TEXT NOT NULL,
                reason TEXT NOT NULL,
                conditions TEXT, -- JSON for specific conditions
                revoked INTEGER DEFAULT 0 CHECK (revoked IN (0, 1)),
                revoked_date TEXT,
                revoked_by TEXT,
                revocation_reason TEXT,
                usage_count INTEGER DEFAULT 0,
                last_used TEXT,
                CONSTRAINT fk_grant_user FOREIGN KEY (user_id) REFERENCES users (id),
                CONSTRAINT fk_grant_grantor FOREIGN KEY (granted_by) REFERENCES users (id),
                CONSTRAINT fk_grant_revoker FOREIGN KEY (revoked_by) REFERENCES users (id)
            );

            -- Comprehensive access audit log
            CREATE TABLE IF NOT EXISTS access_audit_log (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                action TEXT NOT NULL CHECK (action IN (
                    'ACCESS_GRANTED', 'ACCESS_DENIED', 'ACCESS_REVOKED', 'TEMP_ACCESS_GRANTED',
                    'TEMP_ACCESS_EXPIRED', 'CONFLICT_DETECTED', 'ETHICAL_SCREEN_APPLIED',
                    'DELEGATION_ATTEMPTED', 'PRIVILEGE_OVERRIDE'
                )),
                access_level TEXT NOT NULL,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                ip_address TEXT,
                user_agent TEXT,
                session_id TEXT,
                result TEXT NOT NULL CHECK (result IN ('SUCCESS', 'DENIED', 'ERROR')),
                reason TEXT,
                risk_score INTEGER DEFAULT 0 CHECK (risk_score BETWEEN 0 AND 100),
                additional_context TEXT, -- JSON for extra information
                CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users (id)
            );

            -- Chinese wall configuration
            CREATE TABLE IF NOT EXISTS chinese_wall_rules (
                rule_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                rule_name TEXT NOT NULL,
                client_group_a TEXT NOT NULL, -- JSON array of client IDs
                client_group_b TEXT NOT NULL, -- JSON array of client IDs
                restriction_type TEXT NOT NULL CHECK (restriction_type IN (
                    'complete_block', 'ethical_screen', 'senior_approval_required'
                )),
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                created_by TEXT NOT NULL,
                active INTEGER DEFAULT 1 CHECK (active IN (0, 1)),
                exceptions TEXT, -- JSON array of exceptions
                review_date TEXT,
                notes TEXT,
                CONSTRAINT fk_wall_creator FOREIGN KEY (created_by) REFERENCES users (id)
            );
        ''')
        
        conn.commit()
        conn.close()
        
        self.migration_log.append({
            "action": "access_control_tables_created",
            "timestamp": datetime.now().isoformat()
        })

    def _create_retention_tables(self):
        """Create data retention and legal hold tables"""
        logger.info("Creating data retention tables...")
        
        conn = sqlite3.connect(self.database_path)
        conn.executescript('''
            -- Retention policies with compliance tracking
            CREATE TABLE IF NOT EXISTS retention_policies (
                policy_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                policy_name TEXT NOT NULL,
                document_type TEXT NOT NULL,
                client_type TEXT NOT NULL,
                matter_type TEXT NOT NULL,
                retention_years INTEGER NOT NULL,
                legal_hold_capable INTEGER NOT NULL DEFAULT 1 CHECK (legal_hold_capable IN (0, 1)),
                auto_destroy INTEGER NOT NULL DEFAULT 0 CHECK (auto_destroy IN (0, 1)),
                notification_days TEXT NOT NULL, -- JSON array of notification days
                review_required INTEGER NOT NULL DEFAULT 1 CHECK (review_required IN (0, 1)),
                compliance_notes TEXT,
                regulatory_basis TEXT, -- Legal/regulatory basis for retention
                exceptions TEXT, -- JSON array of exceptions
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                created_by TEXT NOT NULL,
                last_reviewed TEXT,
                active INTEGER DEFAULT 1 CHECK (active IN (0, 1)),
                version INTEGER DEFAULT 1,
                CONSTRAINT fk_policy_creator FOREIGN KEY (created_by) REFERENCES users (id)
            );

            -- Document retention tracking
            CREATE TABLE IF NOT EXISTS document_retention (
                document_id TEXT PRIMARY KEY,
                policy_id TEXT NOT NULL,
                client_id TEXT NOT NULL,
                matter_id TEXT,
                creation_date TEXT NOT NULL,
                retention_date TEXT NOT NULL, -- Date when document can be destroyed
                destruction_date TEXT,
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN (
                    'active', 'archived', 'legal_hold', 'pending_destruction', 'destroyed'
                )),
                legal_hold INTEGER DEFAULT 0 CHECK (legal_hold IN (0, 1)),
                legal_hold_reason TEXT,
                legal_hold_date TEXT,
                legal_hold_id TEXT,
                last_review_date TEXT,
                next_review_date TEXT,
                review_notes TEXT,
                notification_sent TEXT, -- JSON array of notifications sent
                destruction_authorized_by TEXT,
                destruction_witness TEXT,
                CONSTRAINT fk_retention_policy FOREIGN KEY (policy_id) REFERENCES retention_policies (policy_id),
                CONSTRAINT fk_retention_client FOREIGN KEY (client_id) REFERENCES clients (id),
                CONSTRAINT fk_retention_matter FOREIGN KEY (matter_id) REFERENCES matters (id),
                CONSTRAINT fk_retention_hold FOREIGN KEY (legal_hold_id) REFERENCES legal_holds (hold_id)
            );

            -- Legal holds with detailed scope management
            CREATE TABLE IF NOT EXISTS legal_holds (
                hold_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                hold_name TEXT NOT NULL,
                matter_id TEXT NOT NULL,
                client_id TEXT NOT NULL,
                hold_reason TEXT NOT NULL,
                hold_date TEXT NOT NULL DEFAULT (datetime('now')),
                requested_by TEXT NOT NULL,
                approved_by TEXT NOT NULL,
                approval_date TEXT,
                scope_description TEXT NOT NULL,
                document_criteria TEXT, -- JSON object with search criteria
                custodian_list TEXT, -- JSON array of custodians
                active INTEGER DEFAULT 1 CHECK (active IN (0, 1)),
                release_date TEXT,
                release_reason TEXT,
                released_by TEXT,
                release_approval TEXT,
                periodic_review_required INTEGER DEFAULT 1 CHECK (periodic_review_required IN (0, 1)),
                next_review_date TEXT,
                compliance_monitoring INTEGER DEFAULT 1 CHECK (compliance_monitoring IN (0, 1)),
                CONSTRAINT fk_hold_matter FOREIGN KEY (matter_id) REFERENCES matters (id),
                CONSTRAINT fk_hold_client FOREIGN KEY (client_id) REFERENCES clients (id),
                CONSTRAINT fk_hold_requester FOREIGN KEY (requested_by) REFERENCES users (id),
                CONSTRAINT fk_hold_approver FOREIGN KEY (approved_by) REFERENCES users (id)
            );

            -- Destruction log with certification
            CREATE TABLE IF NOT EXISTS destruction_log (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                document_id TEXT NOT NULL,
                document_name TEXT,
                document_type TEXT,
                client_id TEXT NOT NULL,
                matter_id TEXT,
                original_creation_date TEXT,
                retention_expiry_date TEXT,
                destruction_date TEXT NOT NULL DEFAULT (datetime('now')),
                destroyed_by TEXT NOT NULL,
                destruction_method TEXT NOT NULL CHECK (destruction_method IN (
                    'secure_delete', 'physical_shredding', 'degaussing', 
                    'incineration', 'data_wiping', 'crypto_shredding'
                )),
                witness TEXT,
                certification TEXT, -- Destruction certificate details
                reason TEXT NOT NULL,
                legal_review_completed INTEGER DEFAULT 0 CHECK (legal_review_completed IN (0, 1)),
                compliance_verified INTEGER DEFAULT 0 CHECK (compliance_verified IN (0, 1)),
                audit_trail_preserved INTEGER DEFAULT 1 CHECK (audit_trail_preserved IN (0, 1)),
                destruction_cost DECIMAL(10,2),
                vendor_used TEXT,
                CONSTRAINT fk_destruction_client FOREIGN KEY (client_id) REFERENCES clients (id),
                CONSTRAINT fk_destruction_destroyer FOREIGN KEY (destroyed_by) REFERENCES users (id)
            );

            -- Retention notifications and reminders
            CREATE TABLE IF NOT EXISTS retention_notifications (
                notification_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                document_id TEXT NOT NULL,
                notification_type TEXT NOT NULL CHECK (notification_type IN (
                    'retention_warning', 'review_required', 'destruction_pending',
                    'legal_hold_applied', 'legal_hold_released'
                )),
                recipient_id TEXT NOT NULL,
                sent_date TEXT NOT NULL DEFAULT (datetime('now')),
                scheduled_date TEXT,
                message TEXT NOT NULL,
                acknowledged INTEGER DEFAULT 0 CHECK (acknowledged IN (0, 1)),
                acknowledged_date TEXT,
                action_required TEXT,
                action_taken TEXT,
                CONSTRAINT fk_notification_doc FOREIGN KEY (document_id) REFERENCES document_retention (document_id),
                CONSTRAINT fk_notification_recipient FOREIGN KEY (recipient_id) REFERENCES users (id)
            );
        ''')
        
        conn.commit()
        conn.close()
        
        self.migration_log.append({
            "action": "retention_tables_created",
            "timestamp": datetime.now().isoformat()
        })

    def _create_indexes(self):
        """Create database indexes for optimal performance"""
        logger.info("Creating database indexes...")
        
        conn = sqlite3.connect(self.database_path)
        conn.executescript('''
            -- Privilege table indexes
            CREATE INDEX IF NOT EXISTS idx_privilege_client ON privilege_assertions (client_id);
            CREATE INDEX IF NOT EXISTS idx_privilege_matter ON privilege_assertions (matter_id);
            CREATE INDEX IF NOT EXISTS idx_privilege_type ON privilege_assertions (privilege_type);
            CREATE INDEX IF NOT EXISTS idx_privilege_attorney ON privilege_assertions (attorney_id);
            CREATE INDEX IF NOT EXISTS idx_privilege_waived ON privilege_assertions (waived);
            CREATE INDEX IF NOT EXISTS idx_privilege_created ON privilege_assertions (created_at);
            
            CREATE INDEX IF NOT EXISTS idx_access_log_date ON privilege_access_log (access_date);
            CREATE INDEX IF NOT EXISTS idx_access_log_user ON privilege_access_log (user_id);
            CREATE INDEX IF NOT EXISTS idx_access_log_document ON privilege_access_log (document_id);
            CREATE INDEX IF NOT EXISTS idx_access_log_type ON privilege_access_log (access_type);
            
            -- Encryption table indexes
            CREATE INDEX IF NOT EXISTS idx_encryption_client ON encryption_keys (client_id);
            CREATE INDEX IF NOT EXISTS idx_encryption_matter ON encryption_keys (client_id, matter_id);
            CREATE INDEX IF NOT EXISTS idx_encryption_status ON encryption_keys (status);
            CREATE INDEX IF NOT EXISTS idx_encryption_rotation ON encryption_keys (last_rotation);
            
            CREATE INDEX IF NOT EXISTS idx_doc_encryption_key ON document_encryption (key_id);
            CREATE INDEX IF NOT EXISTS idx_doc_encryption_status ON document_encryption (encryption_status);
            CREATE INDEX IF NOT EXISTS idx_doc_encryption_date ON document_encryption (encryption_date);
            
            -- Access control table indexes
            CREATE INDEX IF NOT EXISTS idx_matter_access_user ON matter_access (user_id);
            CREATE INDEX IF NOT EXISTS idx_matter_access_matter ON matter_access (matter_id);
            CREATE INDEX IF NOT EXISTS idx_matter_access_client ON matter_access (client_id);
            CREATE INDEX IF NOT EXISTS idx_matter_access_active ON matter_access (active);
            CREATE INDEX IF NOT EXISTS idx_matter_access_expiry ON matter_access (expiration_date);
            
            CREATE INDEX IF NOT EXISTS idx_conflict_checks_user ON conflict_checks (user_id);
            CREATE INDEX IF NOT EXISTS idx_conflict_checks_client ON conflict_checks (client_id);
            CREATE INDEX IF NOT EXISTS idx_conflict_checks_status ON conflict_checks (status);
            CREATE INDEX IF NOT EXISTS idx_conflict_checks_date ON conflict_checks (checked_date);
            
            CREATE INDEX IF NOT EXISTS idx_access_grants_user ON access_grants (user_id);
            CREATE INDEX IF NOT EXISTS idx_access_grants_resource ON access_grants (resource_type, resource_id);
            CREATE INDEX IF NOT EXISTS idx_access_grants_expiry ON access_grants (expiration_date);
            CREATE INDEX IF NOT EXISTS idx_access_grants_active ON access_grants (revoked);
            
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON access_audit_log (timestamp);
            CREATE INDEX IF NOT EXISTS idx_audit_user ON access_audit_log (user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_resource ON access_audit_log (resource_type, resource_id);
            CREATE INDEX IF NOT EXISTS idx_audit_action ON access_audit_log (action);
            CREATE INDEX IF NOT EXISTS idx_audit_result ON access_audit_log (result);
            
            -- Retention table indexes
            CREATE INDEX IF NOT EXISTS idx_retention_policy_type ON retention_policies (document_type, client_type, matter_type);
            CREATE INDEX IF NOT EXISTS idx_retention_policy_active ON retention_policies (active);
            
            CREATE INDEX IF NOT EXISTS idx_retention_date ON document_retention (retention_date);
            CREATE INDEX IF NOT EXISTS idx_retention_status ON document_retention (status);
            CREATE INDEX IF NOT EXISTS idx_retention_client ON document_retention (client_id);
            CREATE INDEX IF NOT EXISTS idx_retention_matter ON document_retention (matter_id);
            CREATE INDEX IF NOT EXISTS idx_retention_hold ON document_retention (legal_hold);
            CREATE INDEX IF NOT EXISTS idx_retention_review ON document_retention (next_review_date);
            
            CREATE INDEX IF NOT EXISTS idx_legal_holds_matter ON legal_holds (matter_id);
            CREATE INDEX IF NOT EXISTS idx_legal_holds_client ON legal_holds (client_id);
            CREATE INDEX IF NOT EXISTS idx_legal_holds_active ON legal_holds (active);
            CREATE INDEX IF NOT EXISTS idx_legal_holds_date ON legal_holds (hold_date);
            
            CREATE INDEX IF NOT EXISTS idx_destruction_log_date ON destruction_log (destruction_date);
            CREATE INDEX IF NOT EXISTS idx_destruction_log_client ON destruction_log (client_id);
            CREATE INDEX IF NOT EXISTS idx_destruction_log_matter ON destruction_log (matter_id);
            CREATE INDEX IF NOT EXISTS idx_destruction_log_method ON destruction_log (destruction_method);
            
            CREATE INDEX IF NOT EXISTS idx_notifications_document ON retention_notifications (document_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON retention_notifications (recipient_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_type ON retention_notifications (notification_type);
            CREATE INDEX IF NOT EXISTS idx_notifications_date ON retention_notifications (sent_date);
        ''')
        
        conn.commit()
        conn.close()
        
        self.migration_log.append({
            "action": "indexes_created",
            "timestamp": datetime.now().isoformat()
        })

    def _insert_default_data(self):
        """Insert default retention policies and configurations"""
        logger.info("Inserting default data...")
        
        conn = sqlite3.connect(self.database_path)
        
        # Default retention policies based on common legal requirements
        default_policies = [
            {
                "policy_name": "Standard Contract Documents",
                "document_type": "contract",
                "client_type": "corporate",
                "matter_type": "general",
                "retention_years": 7,
                "notification_days": [90, 30, 7],
                "compliance_notes": "Standard 7-year retention for contract documents per legal requirements",
                "regulatory_basis": "SOX, State Contract Law"
            },
            {
                "policy_name": "Litigation Documents",
                "document_type": "litigation",
                "client_type": "all",
                "matter_type": "litigation",
                "retention_years": 10,
                "notification_days": [180, 90, 30, 7],
                "compliance_notes": "Extended retention for litigation materials",
                "regulatory_basis": "FRCP, State Rules of Civil Procedure"
            },
            {
                "policy_name": "Tax Documents",
                "document_type": "tax",
                "client_type": "all",
                "matter_type": "tax",
                "retention_years": 7,
                "notification_days": [365, 90, 30],
                "compliance_notes": "IRS recommended retention period",
                "regulatory_basis": "IRC Section 6501"
            },
            {
                "policy_name": "Employment Law Documents",
                "document_type": "employment",
                "client_type": "corporate",
                "matter_type": "employment",
                "retention_years": 6,
                "notification_days": [90, 30, 7],
                "compliance_notes": "EEOC and labor law compliance retention",
                "regulatory_basis": "Title VII, ADA, FLSA"
            },
            {
                "policy_name": "Confidential Communications",
                "document_type": "communication",
                "client_type": "all",
                "matter_type": "all",
                "retention_years": 10,
                "notification_days": [180, 90, 30, 7],
                "compliance_notes": "Extended retention for attorney-client privileged communications",
                "regulatory_basis": "Attorney-Client Privilege, Work Product Doctrine"
            }
        ]
        
        for policy in default_policies:
            conn.execute('''
                INSERT OR IGNORE INTO retention_policies
                (policy_name, document_type, client_type, matter_type,
                 retention_years, legal_hold_capable, auto_destroy,
                 notification_days, review_required, compliance_notes,
                 regulatory_basis, created_by)
                VALUES (?, ?, ?, ?, ?, 1, 0, ?, 1, ?, ?, 'system')
            ''', (
                policy["policy_name"],
                policy["document_type"],
                policy["client_type"],
                policy["matter_type"],
                policy["retention_years"],
                json.dumps(policy["notification_days"]),
                policy["compliance_notes"],
                policy["regulatory_basis"]
            ))
        
        # Default Chinese Wall rules for common conflict scenarios
        default_wall_rules = [
            {
                "rule_name": "Competitor Separation",
                "restriction_type": "complete_block",
                "notes": "Prevent access between directly competing clients"
            },
            {
                "rule_name": "M&A Ethical Screen",
                "restriction_type": "ethical_screen", 
                "notes": "Ethical screen for M&A transactions involving potential conflicts"
            }
        ]
        
        for rule in default_wall_rules:
            conn.execute('''
                INSERT OR IGNORE INTO chinese_wall_rules
                (rule_name, client_group_a, client_group_b, restriction_type,
                 created_by, exceptions, notes)
                VALUES (?, '[]', '[]', ?, 'system', '[]', ?)
            ''', (
                rule["rule_name"],
                rule["restriction_type"],
                rule["notes"]
            ))
        
        conn.commit()
        conn.close()
        
        self.migration_log.append({
            "action": "default_data_inserted",
            "timestamp": datetime.now().isoformat()
        })

    def _log_migration_complete(self):
        """Log migration completion and generate migration report"""
        try:
            migration_report = {
                "migration_id": f"privilege_protection_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "start_time": self.migration_log[0]["timestamp"] if self.migration_log else datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "database_path": self.database_path,
                "actions_performed": self.migration_log,
                "tables_created": [
                    "privilege_assertions", "privilege_access_log", "privilege_waivers", "privilege_settings",
                    "encryption_keys", "key_rotation_log", "document_encryption", "encryption_audit_log",
                    "matter_access", "conflict_checks", "access_grants", "access_audit_log", "chinese_wall_rules",
                    "retention_policies", "document_retention", "legal_holds", "destruction_log", "retention_notifications"
                ],
                "indexes_created": 50,  # Approximate count
                "default_policies_created": 5,
                "status": "completed"
            }
            
            # Save migration report
            report_path = f"migration_report_{migration_report['migration_id']}.json"
            with open(report_path, 'w') as f:
                json.dump(migration_report, f, indent=2)
            
            logger.info(f"Migration report saved to: {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to create migration report: {e}")

    def _rollback_migration(self):
        """Rollback migration on failure"""
        try:
            logger.warning("Attempting to rollback migration...")
            
            # Find the most recent backup
            backup_files = [f for f in os.listdir('.') if f.startswith(f"{self.database_path}.backup_")]
            if backup_files:
                latest_backup = sorted(backup_files)[-1]
                
                # Restore from backup
                import shutil
                shutil.copy2(latest_backup, self.database_path)
                logger.info(f"Database restored from backup: {latest_backup}")
            else:
                logger.warning("No backup found - manual intervention may be required")
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")

    def verify_migration(self) -> Dict:
        """Verify migration was successful"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            verification_results = {
                "tables_exist": True,
                "indexes_exist": True,
                "default_data_exists": True,
                "foreign_keys_enabled": False,
                "errors": []
            }
            
            # Check tables exist
            expected_tables = [
                'privilege_assertions', 'privilege_access_log', 'privilege_waivers', 'privilege_settings',
                'encryption_keys', 'key_rotation_log', 'document_encryption', 'encryption_audit_log',
                'matter_access', 'conflict_checks', 'access_grants', 'access_audit_log', 'chinese_wall_rules',
                'retention_policies', 'document_retention', 'legal_holds', 'destruction_log', 'retention_notifications'
            ]
            
            for table in expected_tables:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
                if not cursor.fetchone():
                    verification_results["tables_exist"] = False
                    verification_results["errors"].append(f"Table missing: {table}")
            
            # Check some indexes exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
            indexes = cursor.fetchall()
            if len(indexes) < 10:  # Should have many indexes
                verification_results["indexes_exist"] = False
                verification_results["errors"].append("Insufficient indexes created")
            
            # Check default data
            cursor.execute("SELECT COUNT(*) FROM retention_policies")
            policy_count = cursor.fetchone()[0]
            if policy_count < 3:
                verification_results["default_data_exists"] = False
                verification_results["errors"].append("Default retention policies not created")
            
            # Check foreign key support
            cursor.execute("PRAGMA foreign_keys")
            fk_enabled = cursor.fetchone()[0]
            verification_results["foreign_keys_enabled"] = bool(fk_enabled)
            
            conn.close()
            
            return verification_results
            
        except Exception as e:
            return {
                "tables_exist": False,
                "indexes_exist": False,
                "default_data_exists": False,
                "foreign_keys_enabled": False,
                "errors": [str(e)]
            }


def main():
    """Main migration script entry point"""
    parser = argparse.ArgumentParser(description="Privilege Protection Database Migration")
    parser.add_argument("--database", default="legal_ai_system.db",
                       help="Database path (default: legal_ai_system.db)")
    parser.add_argument("--force", action="store_true",
                       help="Force recreation of existing tables")
    parser.add_argument("--verify-only", action="store_true",
                       help="Only verify existing migration")
    
    args = parser.parse_args()
    
    migration = PrivilegeProtectionMigration(database_path=args.database)
    
    if args.verify_only:
        logger.info("Verifying existing migration...")
        results = migration.verify_migration()
        
        if all([results["tables_exist"], results["indexes_exist"], results["default_data_exists"]]):
            logger.info("✅ Migration verification successful!")
            return 0
        else:
            logger.error("❌ Migration verification failed!")
            for error in results["errors"]:
                logger.error(f"  - {error}")
            return 1
    
    logger.info(f"Starting migration for database: {args.database}")
    
    success = migration.run_migration(force_recreate=args.force)
    
    if success:
        logger.info("🎉 Migration completed successfully!")
        
        # Run verification
        results = migration.verify_migration()
        if results["errors"]:
            logger.warning("⚠️  Migration completed but verification found issues:")
            for error in results["errors"]:
                logger.warning(f"  - {error}")
        
        return 0
    else:
        logger.error("💥 Migration failed!")
        return 1


if __name__ == "__main__":
    exit(main())