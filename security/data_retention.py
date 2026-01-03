#!/usr/bin/env python3
"""
SOC 2 Type II Compliant Data Retention System
Legal ethics compliant data retention with attorney-client privilege protection
"""

import os
import json
import hashlib
import sqlite3
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class RetentionCategory(Enum):
    """Legal data retention categories based on ABA Model Rules"""
    
    # Attorney-Client Privileged Material (permanent retention recommended)
    ATTORNEY_CLIENT_PRIVILEGED = "attorney_client_privileged"
    ATTORNEY_WORK_PRODUCT = "attorney_work_product"
    
    # Case Files and Client Records
    ACTIVE_CASE_FILES = "active_case_files"
    CLOSED_CASE_FILES = "closed_case_files"
    CLIENT_COMMUNICATIONS = "client_communications"
    CLIENT_FINANCIAL_RECORDS = "client_financial_records"
    
    # Administrative Records
    BILLING_RECORDS = "billing_records"
    TIME_RECORDS = "time_records"
    CONFLICT_CHECK_RECORDS = "conflict_check_records"
    
    # System and Audit Records
    AUDIT_LOGS = "audit_logs"
    SYSTEM_LOGS = "system_logs"
    BACKUP_RECORDS = "backup_records"
    
    # Temporary Data
    TEMPORARY_WORK_PRODUCT = "temporary_work_product"
    SESSION_DATA = "session_data"
    CACHE_DATA = "cache_data"

class LegalHoldStatus(Enum):
    """Legal hold status for litigation preservation"""
    ACTIVE = "active"
    PENDING = "pending"
    RELEASED = "released"
    EXPIRED = "expired"

@dataclass
class RetentionPolicy:
    """Data retention policy definition"""
    category: RetentionCategory
    retention_years: int
    description: str
    legal_basis: str
    auto_delete: bool = False
    requires_approval: bool = False
    
    # Legal hold considerations
    hold_indefinitely: bool = False
    ethical_rules: List[str] = None
    
    def __post_init__(self):
        if self.ethical_rules is None:
            self.ethical_rules = []

@dataclass 
class DataRecord:
    """Individual data record with retention metadata"""
    record_id: str
    category: RetentionCategory
    client_id: str
    created_date: datetime
    last_accessed: datetime
    retention_date: datetime
    
    # Legal metadata
    attorney_id: str
    privilege_level: str
    case_number: Optional[str] = None
    legal_hold_id: Optional[str] = None
    
    # Technical metadata
    file_path: Optional[str] = None
    data_size: int = 0
    encryption_status: bool = True
    integrity_hash: Optional[str] = None
    
    # Status
    is_deleted: bool = False
    deletion_date: Optional[datetime] = None
    deletion_method: str = "secure_wipe"

@dataclass
class LegalHold:
    """Legal hold for litigation preservation"""
    hold_id: str
    case_name: str
    client_id: str
    issuing_attorney: str
    start_date: datetime
    end_date: Optional[datetime]
    status: LegalHoldStatus
    
    # Hold scope
    description: str
    categories_covered: List[RetentionCategory]
    keywords: List[str]
    
    # Compliance
    court_order: bool = False
    regulatory_requirement: bool = False
    notification_sent: bool = False

class LegalDataRetentionManager:
    """SOC 2 compliant data retention manager for legal practices"""
    
    def __init__(self, db_path: str = "retention/retention.db"):
        self.db_path = db_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Setup default retention policies
        self.policies = self._setup_default_policies()
        
        # Active legal holds
        self.active_holds: Dict[str, LegalHold] = {}
        
        # Load existing holds
        self._load_legal_holds()
    
    def _init_database(self):
        """Initialize retention database"""
        with sqlite3.connect(self.db_path) as conn:
            # Data records table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS data_records (
                    record_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    created_date TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    retention_date TEXT NOT NULL,
                    attorney_id TEXT NOT NULL,
                    privilege_level TEXT NOT NULL,
                    case_number TEXT,
                    legal_hold_id TEXT,
                    file_path TEXT,
                    data_size INTEGER DEFAULT 0,
                    encryption_status BOOLEAN DEFAULT 1,
                    integrity_hash TEXT,
                    is_deleted BOOLEAN DEFAULT 0,
                    deletion_date TEXT,
                    deletion_method TEXT DEFAULT 'secure_wipe'
                )
            ''')
            
            # Legal holds table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS legal_holds (
                    hold_id TEXT PRIMARY KEY,
                    case_name TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    issuing_attorney TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    status TEXT NOT NULL,
                    description TEXT NOT NULL,
                    categories_covered TEXT NOT NULL,
                    keywords TEXT,
                    court_order BOOLEAN DEFAULT 0,
                    regulatory_requirement BOOLEAN DEFAULT 0,
                    notification_sent BOOLEAN DEFAULT 0
                )
            ''')
            
            # Retention policies table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS retention_policies (
                    category TEXT PRIMARY KEY,
                    retention_years INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    legal_basis TEXT NOT NULL,
                    auto_delete BOOLEAN DEFAULT 0,
                    requires_approval BOOLEAN DEFAULT 0,
                    hold_indefinitely BOOLEAN DEFAULT 0,
                    ethical_rules TEXT
                )
            ''')
            
            # Deletion audit table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deletion_audit (
                    audit_id TEXT PRIMARY KEY,
                    record_id TEXT NOT NULL,
                    deletion_date TEXT NOT NULL,
                    deletion_reason TEXT NOT NULL,
                    approved_by TEXT,
                    deletion_method TEXT NOT NULL,
                    verification_hash TEXT,
                    compliance_verification BOOLEAN DEFAULT 0
                )
            ''')
            
            # Create indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_retention_date ON data_records(retention_date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_client_id ON data_records(client_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_legal_hold ON data_records(legal_hold_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON data_records(category)')
    
    def _setup_default_policies(self) -> Dict[RetentionCategory, RetentionPolicy]:
        """Setup ABA Model Rule compliant retention policies"""
        policies = {
            # Privileged materials - permanent retention recommended
            RetentionCategory.ATTORNEY_CLIENT_PRIVILEGED: RetentionPolicy(
                category=RetentionCategory.ATTORNEY_CLIENT_PRIVILEGED,
                retention_years=999,  # Effectively permanent
                description="Attorney-client privileged communications and documents",
                legal_basis="ABA Model Rule 1.6 - Client-Lawyer Confidentiality",
                hold_indefinitely=True,
                ethical_rules=["ABA_1.6", "ABA_1.9"]
            ),
            
            RetentionCategory.ATTORNEY_WORK_PRODUCT: RetentionPolicy(
                category=RetentionCategory.ATTORNEY_WORK_PRODUCT,
                retention_years=999,  # Effectively permanent
                description="Attorney work product protected materials",
                legal_basis="Federal Rule of Civil Procedure 26(b)(3)",
                hold_indefinitely=True,
                ethical_rules=["FRCP_26"]
            ),
            
            # Case files - 7-10 years after case closure
            RetentionCategory.CLOSED_CASE_FILES: RetentionPolicy(
                category=RetentionCategory.CLOSED_CASE_FILES,
                retention_years=10,
                description="Closed case files and related materials",
                legal_basis="ABA Model Rule 1.15 - Safekeeping Property",
                requires_approval=True,
                ethical_rules=["ABA_1.15", "ABA_1.16"]
            ),
            
            RetentionCategory.CLIENT_COMMUNICATIONS: RetentionPolicy(
                category=RetentionCategory.CLIENT_COMMUNICATIONS,
                retention_years=7,
                description="Client communications and correspondence",
                legal_basis="ABA Model Rule 1.15 - Safekeeping Property",
                ethical_rules=["ABA_1.15"]
            ),
            
            # Financial records - 7 years (IRS requirement)
            RetentionCategory.CLIENT_FINANCIAL_RECORDS: RetentionPolicy(
                category=RetentionCategory.CLIENT_FINANCIAL_RECORDS,
                retention_years=7,
                description="Client financial records and trust account information",
                legal_basis="ABA Model Rule 1.15 - Safekeeping Property; IRS regulations",
                requires_approval=True,
                ethical_rules=["ABA_1.15", "IRC_6001"]
            ),
            
            RetentionCategory.BILLING_RECORDS: RetentionPolicy(
                category=RetentionCategory.BILLING_RECORDS,
                retention_years=7,
                description="Billing and fee records",
                legal_basis="ABA Model Rule 1.5 - Fees; IRS regulations",
                ethical_rules=["ABA_1.5"]
            ),
            
            # Conflict records - permanent retention
            RetentionCategory.CONFLICT_CHECK_RECORDS: RetentionPolicy(
                category=RetentionCategory.CONFLICT_CHECK_RECORDS,
                retention_years=999,
                description="Conflict of interest check records",
                legal_basis="ABA Model Rule 1.7 - Conflict of Interest",
                hold_indefinitely=True,
                ethical_rules=["ABA_1.7", "ABA_1.9", "ABA_1.10"]
            ),
            
            # Audit logs - 7 years for compliance
            RetentionCategory.AUDIT_LOGS: RetentionPolicy(
                category=RetentionCategory.AUDIT_LOGS,
                retention_years=7,
                description="System audit and security logs",
                legal_basis="SOC 2 Type II requirements",
                hold_indefinitely=False,
                ethical_rules=["SOC2", "SECURITY"]
            ),
            
            # Temporary data - short retention
            RetentionCategory.TEMPORARY_WORK_PRODUCT: RetentionPolicy(
                category=RetentionCategory.TEMPORARY_WORK_PRODUCT,
                retention_years=1,
                description="Temporary work product and draft documents",
                legal_basis="Business necessity",
                auto_delete=True
            ),
            
            RetentionCategory.SESSION_DATA: RetentionPolicy(
                category=RetentionCategory.SESSION_DATA,
                retention_years=0,  # Delete after session ends
                description="User session and temporary authentication data",
                legal_basis="Security best practices",
                auto_delete=True
            ),
            
            RetentionCategory.CACHE_DATA: RetentionPolicy(
                category=RetentionCategory.CACHE_DATA,
                retention_years=0,  # Delete after 30 days
                description="System cache and temporary processing data",
                legal_basis="Performance optimization",
                auto_delete=True
            )
        }
        
        # Store policies in database
        self._store_policies(policies)
        return policies
    
    def _store_policies(self, policies: Dict[RetentionCategory, RetentionPolicy]):
        """Store retention policies in database"""
        with sqlite3.connect(self.db_path) as conn:
            for policy in policies.values():
                conn.execute('''
                    INSERT OR REPLACE INTO retention_policies (
                        category, retention_years, description, legal_basis,
                        auto_delete, requires_approval, hold_indefinitely, ethical_rules
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    policy.category.value, policy.retention_years, policy.description,
                    policy.legal_basis, policy.auto_delete, policy.requires_approval,
                    policy.hold_indefinitely, json.dumps(policy.ethical_rules)
                ))
    
    def _load_legal_holds(self):
        """Load active legal holds from database"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM legal_holds WHERE status IN ('active', 'pending')"
            ).fetchall()
            
            for row in rows:
                hold = LegalHold(
                    hold_id=row[0],
                    case_name=row[1],
                    client_id=row[2],
                    issuing_attorney=row[3],
                    start_date=datetime.fromisoformat(row[4]),
                    end_date=datetime.fromisoformat(row[5]) if row[5] else None,
                    status=LegalHoldStatus(row[6]),
                    description=row[7],
                    categories_covered=[RetentionCategory(cat) for cat in json.loads(row[8])],
                    keywords=json.loads(row[9]) if row[9] else [],
                    court_order=bool(row[10]),
                    regulatory_requirement=bool(row[11]),
                    notification_sent=bool(row[12])
                )
                self.active_holds[hold.hold_id] = hold
    
    def register_data(self, client_id: str, attorney_id: str, category: RetentionCategory,
                     privilege_level: str, file_path: str = None, 
                     case_number: str = None, data_size: int = 0) -> str:
        """Register new data for retention management"""
        
        # Generate unique record ID
        record_id = hashlib.sha256(
            f"{client_id}|{attorney_id}|{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Calculate retention date based on policy
        policy = self.policies.get(category)
        if not policy:
            raise ValueError(f"No retention policy found for category {category.value}")
        
        if policy.hold_indefinitely:
            retention_date = datetime.utcnow() + timedelta(days=365 * 999)  # Far future
        else:
            retention_date = datetime.utcnow() + timedelta(days=365 * policy.retention_years)
        
        # Check for active legal holds
        legal_hold_id = None
        for hold in self.active_holds.values():
            if (hold.client_id == client_id and 
                category in hold.categories_covered and
                hold.status == LegalHoldStatus.ACTIVE):
                legal_hold_id = hold.hold_id
                retention_date = datetime.utcnow() + timedelta(days=365 * 999)  # Hold indefinitely
                break
        
        # Calculate integrity hash if file exists
        integrity_hash = None
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                integrity_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Create data record
        record = DataRecord(
            record_id=record_id,
            category=category,
            client_id=client_id,
            created_date=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            retention_date=retention_date,
            attorney_id=attorney_id,
            privilege_level=privilege_level,
            case_number=case_number,
            legal_hold_id=legal_hold_id,
            file_path=file_path,
            data_size=data_size,
            integrity_hash=integrity_hash
        )
        
        # Store in database
        self._store_data_record(record)
        
        logger.info(f"Registered data record {record_id} for client {client_id} with retention until {retention_date}")
        return record_id
    
    def _store_data_record(self, record: DataRecord):
        """Store data record in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO data_records (
                    record_id, category, client_id, created_date, last_accessed,
                    retention_date, attorney_id, privilege_level, case_number,
                    legal_hold_id, file_path, data_size, encryption_status,
                    integrity_hash, is_deleted, deletion_date, deletion_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.record_id, record.category.value, record.client_id,
                record.created_date.isoformat(), record.last_accessed.isoformat(),
                record.retention_date.isoformat(), record.attorney_id,
                record.privilege_level, record.case_number, record.legal_hold_id,
                record.file_path, record.data_size, record.encryption_status,
                record.integrity_hash, record.is_deleted,
                record.deletion_date.isoformat() if record.deletion_date else None,
                record.deletion_method
            ))
    
    def create_legal_hold(self, case_name: str, client_id: str, issuing_attorney: str,
                         description: str, categories: List[RetentionCategory],
                         keywords: List[str] = None, court_order: bool = False) -> str:
        """Create new legal hold for litigation preservation"""
        
        hold_id = hashlib.sha256(
            f"{case_name}|{client_id}|{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        hold = LegalHold(
            hold_id=hold_id,
            case_name=case_name,
            client_id=client_id,
            issuing_attorney=issuing_attorney,
            start_date=datetime.utcnow(),
            end_date=None,
            status=LegalHoldStatus.ACTIVE,
            description=description,
            categories_covered=categories,
            keywords=keywords or [],
            court_order=court_order
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO legal_holds (
                    hold_id, case_name, client_id, issuing_attorney, start_date,
                    end_date, status, description, categories_covered, keywords,
                    court_order, regulatory_requirement, notification_sent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hold.hold_id, hold.case_name, hold.client_id, hold.issuing_attorney,
                hold.start_date.isoformat(), None, hold.status.value,
                hold.description, json.dumps([cat.value for cat in hold.categories_covered]),
                json.dumps(hold.keywords), hold.court_order,
                hold.regulatory_requirement, hold.notification_sent
            ))
        
        # Add to active holds
        self.active_holds[hold_id] = hold
        
        # Update affected records to extend retention
        self._apply_legal_hold(hold)
        
        logger.info(f"Created legal hold {hold_id} for case {case_name}")
        return hold_id
    
    def _apply_legal_hold(self, hold: LegalHold):
        """Apply legal hold to existing records"""
        with sqlite3.connect(self.db_path) as conn:
            # Find records that match hold criteria
            for category in hold.categories_covered:
                conn.execute('''
                    UPDATE data_records
                    SET legal_hold_id = ?, retention_date = ?
                    WHERE client_id = ? AND category = ? AND is_deleted = 0
                ''', (
                    hold.hold_id,
                    (datetime.utcnow() + timedelta(days=365 * 999)).isoformat(),  # Hold indefinitely
                    hold.client_id,
                    category.value
                ))
    
    def release_legal_hold(self, hold_id: str, releasing_attorney: str) -> bool:
        """Release legal hold and restore normal retention"""
        
        hold = self.active_holds.get(hold_id)
        if not hold:
            logger.warning(f"Legal hold {hold_id} not found")
            return False
        
        # Update hold status
        hold.status = LegalHoldStatus.RELEASED
        hold.end_date = datetime.utcnow()
        
        # Update database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE legal_holds
                SET status = ?, end_date = ?
                WHERE hold_id = ?
            ''', (hold.status.value, hold.end_date.isoformat(), hold_id))
            
            # Restore normal retention for affected records
            for category in hold.categories_covered:
                policy = self.policies.get(category)
                if policy and not policy.hold_indefinitely:
                    new_retention_date = datetime.utcnow() + timedelta(days=365 * policy.retention_years)
                    
                    conn.execute('''
                        UPDATE data_records
                        SET legal_hold_id = NULL, retention_date = ?
                        WHERE legal_hold_id = ? AND category = ?
                    ''', (new_retention_date.isoformat(), hold_id, category.value))
        
        # Remove from active holds
        del self.active_holds[hold_id]
        
        logger.info(f"Released legal hold {hold_id} by attorney {releasing_attorney}")
        return True
    
    def identify_expired_records(self) -> List[Dict[str, Any]]:
        """Identify records that have passed their retention date"""
        
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute('''
                SELECT * FROM data_records
                WHERE retention_date < ? AND is_deleted = 0 AND legal_hold_id IS NULL
            ''', (datetime.utcnow().isoformat(),)).fetchall()
            
            expired_records = []
            for row in rows:
                expired_records.append({
                    "record_id": row[0],
                    "category": row[1],
                    "client_id": row[2],
                    "retention_date": row[5],
                    "attorney_id": row[6],
                    "privilege_level": row[7],
                    "file_path": row[10],
                    "data_size": row[11]
                })
            
            return expired_records
    
    def secure_delete_record(self, record_id: str, approved_by: str,
                           reason: str = "retention_policy") -> bool:
        """Securely delete record per retention policy"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Get record details
            record = conn.execute(
                "SELECT * FROM data_records WHERE record_id = ?",
                (record_id,)
            ).fetchone()
            
            if not record:
                logger.warning(f"Record {record_id} not found for deletion")
                return False
            
            # Check if record is under legal hold
            if record[9]:  # legal_hold_id column
                logger.error(f"Cannot delete record {record_id} - under legal hold {record[9]}")
                return False
            
            # Check if deletion requires approval
            category = RetentionCategory(record[1])
            policy = self.policies.get(category)
            
            if policy and policy.requires_approval and not approved_by:
                logger.error(f"Record {record_id} requires approval for deletion")
                return False
            
            # Perform secure deletion
            file_path = record[10]  # file_path column
            verification_hash = None
            
            if file_path and os.path.exists(file_path):
                # Calculate verification hash before deletion
                with open(file_path, 'rb') as f:
                    verification_hash = hashlib.sha256(f.read()).hexdigest()
                
                # Secure file deletion (overwrite multiple times)
                self._secure_file_deletion(file_path)
            
            # Mark as deleted in database
            conn.execute('''
                UPDATE data_records
                SET is_deleted = 1, deletion_date = ?, deletion_method = 'secure_wipe'
                WHERE record_id = ?
            ''', (datetime.utcnow().isoformat(), record_id))
            
            # Create deletion audit record
            audit_id = hashlib.sha256(
                f"{record_id}|{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:16]
            
            conn.execute('''
                INSERT INTO deletion_audit (
                    audit_id, record_id, deletion_date, deletion_reason,
                    approved_by, deletion_method, verification_hash,
                    compliance_verification
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                audit_id, record_id, datetime.utcnow().isoformat(),
                reason, approved_by, "secure_wipe", verification_hash, True
            ))
        
        logger.info(f"Securely deleted record {record_id} approved by {approved_by}")
        return True
    
    def _secure_file_deletion(self, file_path: str, passes: int = 3):
        """Perform secure file deletion with multiple overwrites"""
        try:
            file_size = os.path.getsize(file_path)
            
            with open(file_path, 'r+b') as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            os.remove(file_path)
            logger.info(f"Securely deleted file {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to securely delete file {file_path}: {e}")
            raise
    
    def generate_retention_report(self) -> Dict[str, Any]:
        """Generate comprehensive retention compliance report"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Total records by category
            category_counts = {}
            for category in RetentionCategory:
                count = conn.execute(
                    "SELECT COUNT(*) FROM data_records WHERE category = ? AND is_deleted = 0",
                    (category.value,)
                ).fetchone()[0]
                category_counts[category.value] = count
            
            # Records under legal hold
            hold_count = conn.execute(
                "SELECT COUNT(*) FROM data_records WHERE legal_hold_id IS NOT NULL AND is_deleted = 0"
            ).fetchone()[0]
            
            # Expired records pending deletion
            expired_count = conn.execute('''
                SELECT COUNT(*) FROM data_records
                WHERE retention_date < ? AND is_deleted = 0 AND legal_hold_id IS NULL
            ''', (datetime.utcnow().isoformat(),)).fetchone()[0]
            
            # Active legal holds
            active_holds_count = len(self.active_holds)
            
            # Deletion statistics
            deletion_stats = conn.execute('''
                SELECT COUNT(*) as total_deletions,
                       COUNT(CASE WHEN compliance_verification = 1 THEN 1 END) as compliant_deletions
                FROM deletion_audit
                WHERE deletion_date >= ?
            ''', ((datetime.utcnow() - timedelta(days=30)).isoformat(),)).fetchone()
            
            # Storage statistics
            total_size = conn.execute(
                "SELECT SUM(data_size) FROM data_records WHERE is_deleted = 0"
            ).fetchone()[0] or 0
        
        return {
            "report_date": datetime.utcnow().isoformat(),
            "total_active_records": sum(category_counts.values()),
            "records_by_category": category_counts,
            "records_under_hold": hold_count,
            "expired_records_pending_deletion": expired_count,
            "active_legal_holds": active_holds_count,
            "recent_deletions": {
                "total": deletion_stats[0],
                "compliant": deletion_stats[1]
            },
            "total_storage_bytes": total_size,
            "compliance_status": "compliant" if expired_count == 0 else "attention_required"
        }

# Global retention manager instance  
retention_manager = LegalDataRetentionManager()