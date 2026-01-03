#!/usr/bin/env python3
"""
Enterprise Attorney Role-Based Access Control System
Professional-grade security with attorney-specific roles and permissions
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, asdict
import secrets
import sqlite3
from cryptography.fernet import Fernet
import pyotp
import qrcode
import io
import base64

# Configure logger
logger = logging.getLogger('attorney_security')

class AttorneyRole(Enum):
    """Attorney-specific role hierarchy with practice area considerations"""
    # Support Staff
    RECEPTIONIST = "receptionist"
    LEGAL_ASSISTANT = "legal_assistant"
    PARALEGAL = "paralegal"
    
    # Attorney Levels
    CONTRACT_ATTORNEY = "contract_attorney"
    ASSOCIATE = "associate"
    SENIOR_ASSOCIATE = "senior_associate"
    JUNIOR_PARTNER = "junior_partner"
    PARTNER = "partner"
    SENIOR_PARTNER = "senior_partner"
    MANAGING_PARTNER = "managing_partner"
    
    # Administrative
    FIRM_ADMINISTRATOR = "firm_administrator"
    IT_ADMINISTRATOR = "it_administrator"
    COMPLIANCE_OFFICER = "compliance_officer"

class PracticeArea(Enum):
    """Legal practice area specializations"""
    GENERAL_PRACTICE = "general_practice"
    CORPORATE = "corporate"
    LITIGATION = "litigation"
    CRIMINAL = "criminal"
    FAMILY = "family"
    ESTATE_PLANNING = "estate_planning"
    REAL_ESTATE = "real_estate"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    EMPLOYMENT = "employment"
    BANKRUPTCY = "bankruptcy"
    IMMIGRATION = "immigration"
    PERSONAL_INJURY = "personal_injury"

class PermissionLevel(Enum):
    """Permission levels for attorney operations"""
    NONE = 0
    VIEW_ONLY = 1
    EDIT = 2
    SUPERVISE = 3
    ADMIN = 4

@dataclass
class AttorneyPermissions:
    """Attorney-specific permissions with practice area considerations"""
    # Client Management
    view_clients: PermissionLevel
    create_clients: PermissionLevel
    edit_clients: PermissionLevel
    delete_clients: PermissionLevel
    
    # Document Management
    view_documents: PermissionLevel
    create_documents: PermissionLevel
    edit_documents: PermissionLevel
    delete_documents: PermissionLevel
    privileged_documents: PermissionLevel
    
    # Case Management
    view_cases: PermissionLevel
    create_cases: PermissionLevel
    edit_cases: PermissionLevel
    assign_cases: PermissionLevel
    close_cases: PermissionLevel
    
    # Financial
    view_billing: PermissionLevel
    create_billing: PermissionLevel
    approve_billing: PermissionLevel
    view_financials: PermissionLevel
    
    # Administrative
    user_management: PermissionLevel
    system_config: PermissionLevel
    audit_access: PermissionLevel
    compliance_access: PermissionLevel
    
    # Attorney Work Product
    legal_research: PermissionLevel
    brief_writing: PermissionLevel
    contract_review: PermissionLevel
    court_filings: PermissionLevel
    
    # Cross-practice restrictions
    practice_areas: Set[PracticeArea]
    ethical_wall_exemption: bool

@dataclass
class AttorneyUser:
    """Attorney user with professional credentials"""
    user_id: str
    email: str
    bar_number: Optional[str]
    bar_state: Optional[str]
    role: AttorneyRole
    practice_areas: List[PracticeArea]
    permissions: AttorneyPermissions
    is_licensed: bool
    license_status: str
    firm_id: str
    department: Optional[str]
    supervisor_id: Optional[str]
    ethical_walls: List[str]  # Case IDs with conflicts
    created_at: datetime
    last_login: Optional[datetime]
    session_timeout_minutes: int
    mfa_enabled: bool
    mfa_secret: Optional[str]
    backup_codes: List[str]
    password_hash: str
    failed_login_attempts: int
    locked_until: Optional[datetime]

class AttorneySecurityManager:
    """Enterprise attorney security management system"""
    
    def __init__(self, db_path: str = "attorney_security.db"):
        self.db_path = db_path
        self.encryption_key = self._load_or_create_key()
        self.cipher = Fernet(self.encryption_key)
        self._init_database()
        
        # Role-based permission templates
        self.role_permissions = {
            AttorneyRole.RECEPTIONIST: AttorneyPermissions(
                view_clients=PermissionLevel.VIEW_ONLY,
                create_clients=PermissionLevel.EDIT,
                edit_clients=PermissionLevel.VIEW_ONLY,
                delete_clients=PermissionLevel.NONE,
                view_documents=PermissionLevel.NONE,
                create_documents=PermissionLevel.NONE,
                edit_documents=PermissionLevel.NONE,
                delete_documents=PermissionLevel.NONE,
                privileged_documents=PermissionLevel.NONE,
                view_cases=PermissionLevel.VIEW_ONLY,
                create_cases=PermissionLevel.NONE,
                edit_cases=PermissionLevel.NONE,
                assign_cases=PermissionLevel.NONE,
                close_cases=PermissionLevel.NONE,
                view_billing=PermissionLevel.NONE,
                create_billing=PermissionLevel.NONE,
                approve_billing=PermissionLevel.NONE,
                view_financials=PermissionLevel.NONE,
                user_management=PermissionLevel.NONE,
                system_config=PermissionLevel.NONE,
                audit_access=PermissionLevel.NONE,
                compliance_access=PermissionLevel.NONE,
                legal_research=PermissionLevel.NONE,
                brief_writing=PermissionLevel.NONE,
                contract_review=PermissionLevel.NONE,
                court_filings=PermissionLevel.NONE,
                practice_areas={PracticeArea.GENERAL_PRACTICE},
                ethical_wall_exemption=False
            ),
            
            AttorneyRole.PARALEGAL: AttorneyPermissions(
                view_clients=PermissionLevel.VIEW_ONLY,
                create_clients=PermissionLevel.EDIT,
                edit_clients=PermissionLevel.EDIT,
                delete_clients=PermissionLevel.NONE,
                view_documents=PermissionLevel.VIEW_ONLY,
                create_documents=PermissionLevel.EDIT,
                edit_documents=PermissionLevel.EDIT,
                delete_documents=PermissionLevel.VIEW_ONLY,
                privileged_documents=PermissionLevel.VIEW_ONLY,
                view_cases=PermissionLevel.VIEW_ONLY,
                create_cases=PermissionLevel.EDIT,
                edit_cases=PermissionLevel.EDIT,
                assign_cases=PermissionLevel.NONE,
                close_cases=PermissionLevel.NONE,
                view_billing=PermissionLevel.VIEW_ONLY,
                create_billing=PermissionLevel.EDIT,
                approve_billing=PermissionLevel.NONE,
                view_financials=PermissionLevel.NONE,
                user_management=PermissionLevel.NONE,
                system_config=PermissionLevel.NONE,
                audit_access=PermissionLevel.NONE,
                compliance_access=PermissionLevel.NONE,
                legal_research=PermissionLevel.EDIT,
                brief_writing=PermissionLevel.EDIT,
                contract_review=PermissionLevel.VIEW_ONLY,
                court_filings=PermissionLevel.EDIT,
                practice_areas={PracticeArea.GENERAL_PRACTICE},
                ethical_wall_exemption=False
            ),
            
            AttorneyRole.ASSOCIATE: AttorneyPermissions(
                view_clients=PermissionLevel.EDIT,
                create_clients=PermissionLevel.EDIT,
                edit_clients=PermissionLevel.EDIT,
                delete_clients=PermissionLevel.VIEW_ONLY,
                view_documents=PermissionLevel.EDIT,
                create_documents=PermissionLevel.EDIT,
                edit_documents=PermissionLevel.EDIT,
                delete_documents=PermissionLevel.EDIT,
                privileged_documents=PermissionLevel.EDIT,
                view_cases=PermissionLevel.EDIT,
                create_cases=PermissionLevel.EDIT,
                edit_cases=PermissionLevel.EDIT,
                assign_cases=PermissionLevel.VIEW_ONLY,
                close_cases=PermissionLevel.EDIT,
                view_billing=PermissionLevel.EDIT,
                create_billing=PermissionLevel.EDIT,
                approve_billing=PermissionLevel.VIEW_ONLY,
                view_financials=PermissionLevel.NONE,
                user_management=PermissionLevel.NONE,
                system_config=PermissionLevel.NONE,
                audit_access=PermissionLevel.NONE,
                compliance_access=PermissionLevel.VIEW_ONLY,
                legal_research=PermissionLevel.EDIT,
                brief_writing=PermissionLevel.EDIT,
                contract_review=PermissionLevel.EDIT,
                court_filings=PermissionLevel.EDIT,
                practice_areas={PracticeArea.GENERAL_PRACTICE},
                ethical_wall_exemption=False
            ),
            
            AttorneyRole.PARTNER: AttorneyPermissions(
                view_clients=PermissionLevel.ADMIN,
                create_clients=PermissionLevel.ADMIN,
                edit_clients=PermissionLevel.ADMIN,
                delete_clients=PermissionLevel.ADMIN,
                view_documents=PermissionLevel.ADMIN,
                create_documents=PermissionLevel.ADMIN,
                edit_documents=PermissionLevel.ADMIN,
                delete_documents=PermissionLevel.ADMIN,
                privileged_documents=PermissionLevel.ADMIN,
                view_cases=PermissionLevel.ADMIN,
                create_cases=PermissionLevel.ADMIN,
                edit_cases=PermissionLevel.ADMIN,
                assign_cases=PermissionLevel.ADMIN,
                close_cases=PermissionLevel.ADMIN,
                view_billing=PermissionLevel.ADMIN,
                create_billing=PermissionLevel.ADMIN,
                approve_billing=PermissionLevel.ADMIN,
                view_financials=PermissionLevel.SUPERVISE,
                user_management=PermissionLevel.SUPERVISE,
                system_config=PermissionLevel.VIEW_ONLY,
                audit_access=PermissionLevel.SUPERVISE,
                compliance_access=PermissionLevel.ADMIN,
                legal_research=PermissionLevel.ADMIN,
                brief_writing=PermissionLevel.ADMIN,
                contract_review=PermissionLevel.ADMIN,
                court_filings=PermissionLevel.ADMIN,
                practice_areas=set(PracticeArea),
                ethical_wall_exemption=True
            ),
            
            AttorneyRole.MANAGING_PARTNER: AttorneyPermissions(
                view_clients=PermissionLevel.ADMIN,
                create_clients=PermissionLevel.ADMIN,
                edit_clients=PermissionLevel.ADMIN,
                delete_clients=PermissionLevel.ADMIN,
                view_documents=PermissionLevel.ADMIN,
                create_documents=PermissionLevel.ADMIN,
                edit_documents=PermissionLevel.ADMIN,
                delete_documents=PermissionLevel.ADMIN,
                privileged_documents=PermissionLevel.ADMIN,
                view_cases=PermissionLevel.ADMIN,
                create_cases=PermissionLevel.ADMIN,
                edit_cases=PermissionLevel.ADMIN,
                assign_cases=PermissionLevel.ADMIN,
                close_cases=PermissionLevel.ADMIN,
                view_billing=PermissionLevel.ADMIN,
                create_billing=PermissionLevel.ADMIN,
                approve_billing=PermissionLevel.ADMIN,
                view_financials=PermissionLevel.ADMIN,
                user_management=PermissionLevel.ADMIN,
                system_config=PermissionLevel.ADMIN,
                audit_access=PermissionLevel.ADMIN,
                compliance_access=PermissionLevel.ADMIN,
                legal_research=PermissionLevel.ADMIN,
                brief_writing=PermissionLevel.ADMIN,
                contract_review=PermissionLevel.ADMIN,
                court_filings=PermissionLevel.ADMIN,
                practice_areas=set(PracticeArea),
                ethical_wall_exemption=True
            )
        }
    
    def _load_or_create_key(self) -> bytes:
        """Load existing encryption key or create new one"""
        key_file = "attorney_security_key.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            return key
    
    def _init_database(self):
        """Initialize attorney security database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Attorney users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attorney_users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                bar_number TEXT,
                bar_state TEXT,
                role TEXT NOT NULL,
                practice_areas TEXT NOT NULL,
                permissions TEXT NOT NULL,
                is_licensed BOOLEAN NOT NULL,
                license_status TEXT NOT NULL,
                firm_id TEXT NOT NULL,
                department TEXT,
                supervisor_id TEXT,
                ethical_walls TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                last_login TIMESTAMP,
                session_timeout_minutes INTEGER NOT NULL,
                mfa_enabled BOOLEAN NOT NULL,
                mfa_secret TEXT,
                backup_codes TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                FOREIGN KEY (supervisor_id) REFERENCES attorney_users (user_id)
            )
        ''')
        
        # Attorney sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attorney_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                last_activity TIMESTAMP NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES attorney_users (user_id)
            )
        ''')
        
        # Ethical walls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ethical_walls (
                wall_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                conflicted_attorneys TEXT NOT NULL,
                exempted_attorneys TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                created_by TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_attorney_user(
        self,
        email: str,
        password: str,
        role: AttorneyRole,
        bar_number: Optional[str] = None,
        bar_state: Optional[str] = None,
        practice_areas: Optional[List[PracticeArea]] = None,
        firm_id: str = "default",
        supervisor_id: Optional[str] = None
    ) -> AttorneyUser:
        """Create new attorney user with professional credentials"""
        
        user_id = hashlib.sha256(f"{email}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Generate MFA secret and backup codes
        mfa_secret = pyotp.random_base32()
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        # Set default practice areas
        if practice_areas is None:
            practice_areas = [PracticeArea.GENERAL_PRACTICE]
        
        # Get role-based permissions
        permissions = self.role_permissions.get(role, self.role_permissions[AttorneyRole.ASSOCIATE])
        
        # Determine if this is a licensed attorney role
        is_licensed = role in [
            AttorneyRole.CONTRACT_ATTORNEY,
            AttorneyRole.ASSOCIATE,
            AttorneyRole.SENIOR_ASSOCIATE,
            AttorneyRole.JUNIOR_PARTNER,
            AttorneyRole.PARTNER,
            AttorneyRole.SENIOR_PARTNER,
            AttorneyRole.MANAGING_PARTNER
        ]
        
        # Set session timeout based on role
        timeout_map = {
            AttorneyRole.RECEPTIONIST: 240,  # 4 hours
            AttorneyRole.LEGAL_ASSISTANT: 480,  # 8 hours
            AttorneyRole.PARALEGAL: 480,  # 8 hours
            AttorneyRole.ASSOCIATE: 720,  # 12 hours
            AttorneyRole.PARTNER: 720,  # 12 hours
            AttorneyRole.MANAGING_PARTNER: 480  # 8 hours (security)
        }
        session_timeout = timeout_map.get(role, 480)
        
        attorney_user = AttorneyUser(
            user_id=user_id,
            email=email,
            bar_number=bar_number,
            bar_state=bar_state,
            role=role,
            practice_areas=practice_areas,
            permissions=permissions,
            is_licensed=is_licensed,
            license_status="active" if is_licensed else "not_applicable",
            firm_id=firm_id,
            department=None,
            supervisor_id=supervisor_id,
            ethical_walls=[],
            created_at=datetime.now(),
            last_login=None,
            session_timeout_minutes=session_timeout,
            mfa_enabled=True,
            mfa_secret=mfa_secret,
            backup_codes=backup_codes,
            password_hash=password_hash,
            failed_login_attempts=0,
            locked_until=None
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO attorney_users (
                    user_id, email, bar_number, bar_state, role, practice_areas,
                    permissions, is_licensed, license_status, firm_id, department,
                    supervisor_id, ethical_walls, created_at, last_login,
                    session_timeout_minutes, mfa_enabled, mfa_secret, backup_codes,
                    password_hash, failed_login_attempts, locked_until
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                attorney_user.user_id,
                attorney_user.email,
                attorney_user.bar_number,
                attorney_user.bar_state,
                attorney_user.role.value,
                json.dumps([pa.value for pa in attorney_user.practice_areas]),
                json.dumps(asdict(attorney_user.permissions), default=str),
                attorney_user.is_licensed,
                attorney_user.license_status,
                attorney_user.firm_id,
                attorney_user.department,
                attorney_user.supervisor_id,
                json.dumps(attorney_user.ethical_walls),
                attorney_user.created_at.isoformat(),
                attorney_user.last_login.isoformat() if attorney_user.last_login else None,
                attorney_user.session_timeout_minutes,
                attorney_user.mfa_enabled,
                self.cipher.encrypt(attorney_user.mfa_secret.encode()).decode(),
                json.dumps(attorney_user.backup_codes),
                attorney_user.password_hash,
                attorney_user.failed_login_attempts,
                attorney_user.locked_until.isoformat() if attorney_user.locked_until else None
            ))
            
            conn.commit()
            logger.info(f"Created attorney user {user_id} with role {role.value}")
            return attorney_user
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to create attorney user: {e}")
            raise ValueError("Email already exists")
        finally:
            conn.close()
    
    def authenticate_attorney(
        self, 
        email: str, 
        password: str, 
        mfa_token: Optional[str] = None
    ) -> Optional[AttorneyUser]:
        """Authenticate attorney with professional verification"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM attorney_users WHERE email = ?', (email,))
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"Attorney authentication failed: user not found - {email}")
                return None
            
            # Parse user data
            columns = [desc[0] for desc in cursor.description]
            user_data = dict(zip(columns, row))
            
            # Check if account is locked
            if user_data['locked_until']:
                locked_until = datetime.fromisoformat(user_data['locked_until'])
                if datetime.now() < locked_until:
                    logger.warning(f"Attorney account locked until {locked_until}: {email}")
                    return None
            
            # Verify password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if user_data['password_hash'] != password_hash:
                # Increment failed attempts
                failed_attempts = user_data['failed_login_attempts'] + 1
                lock_time = None
                
                if failed_attempts >= 5:
                    lock_time = datetime.now() + timedelta(hours=1)
                    logger.warning(f"Attorney account locked due to failed attempts: {email}")
                
                cursor.execute('''
                    UPDATE attorney_users 
                    SET failed_login_attempts = ?, locked_until = ?
                    WHERE email = ?
                ''', (failed_attempts, lock_time.isoformat() if lock_time else None, email))
                conn.commit()
                
                return None
            
            # Verify MFA if enabled
            if user_data['mfa_enabled']:
                if not mfa_token:
                    logger.warning(f"MFA token required for attorney: {email}")
                    return None
                
                # Decrypt MFA secret
                encrypted_secret = user_data['mfa_secret']
                mfa_secret = self.cipher.decrypt(encrypted_secret.encode()).decode()
                
                # Verify TOTP or backup code
                totp = pyotp.TOTP(mfa_secret)
                backup_codes = json.loads(user_data['backup_codes'])
                
                if not (totp.verify(mfa_token) or mfa_token.upper() in backup_codes):
                    logger.warning(f"MFA verification failed for attorney: {email}")
                    return None
                
                # Remove used backup code
                if mfa_token.upper() in backup_codes:
                    backup_codes.remove(mfa_token.upper())
                    cursor.execute('''
                        UPDATE attorney_users SET backup_codes = ? WHERE email = ?
                    ''', (json.dumps(backup_codes), email))
            
            # Reset failed attempts on successful login
            cursor.execute('''
                UPDATE attorney_users 
                SET failed_login_attempts = 0, locked_until = NULL, last_login = ?
                WHERE email = ?
            ''', (datetime.now().isoformat(), email))
            conn.commit()
            
            # Build AttorneyUser object
            attorney_user = AttorneyUser(
                user_id=user_data['user_id'],
                email=user_data['email'],
                bar_number=user_data['bar_number'],
                bar_state=user_data['bar_state'],
                role=AttorneyRole(user_data['role']),
                practice_areas=[PracticeArea(pa) for pa in json.loads(user_data['practice_areas'])],
                permissions=AttorneyPermissions(**json.loads(user_data['permissions'])),
                is_licensed=user_data['is_licensed'],
                license_status=user_data['license_status'],
                firm_id=user_data['firm_id'],
                department=user_data['department'],
                supervisor_id=user_data['supervisor_id'],
                ethical_walls=json.loads(user_data['ethical_walls']),
                created_at=datetime.fromisoformat(user_data['created_at']),
                last_login=datetime.fromisoformat(user_data['last_login']) if user_data['last_login'] else None,
                session_timeout_minutes=user_data['session_timeout_minutes'],
                mfa_enabled=user_data['mfa_enabled'],
                mfa_secret=mfa_secret if user_data['mfa_enabled'] else None,
                backup_codes=backup_codes,
                password_hash=user_data['password_hash'],
                failed_login_attempts=0,
                locked_until=None
            )
            
            logger.info(f"Attorney authenticated successfully: {email} (Role: {attorney_user.role.value})")
            return attorney_user
            
        finally:
            conn.close()
    
    def has_permission(
        self, 
        user: AttorneyUser, 
        permission: str, 
        required_level: PermissionLevel,
        case_id: Optional[str] = None
    ) -> bool:
        """Check if attorney has required permission level"""
        
        # Check ethical wall restrictions
        if case_id and case_id in user.ethical_walls and not user.permissions.ethical_wall_exemption:
            logger.warning(f"Ethical wall blocks access for {user.email} to case {case_id}")
            return False
        
        # Get permission level
        user_level = getattr(user.permissions, permission, PermissionLevel.NONE)
        
        if isinstance(user_level, set):  # Handle practice_areas
            return bool(user_level)
        
        return user_level.value >= required_level.value
    
    def create_session(
        self, 
        user: AttorneyUser, 
        ip_address: str, 
        user_agent: str
    ) -> str:
        """Create secure attorney session"""
        
        session_id = secrets.token_urlsafe(32)
        created_at = datetime.now()
        expires_at = created_at + timedelta(minutes=user.session_timeout_minutes)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO attorney_sessions (
                session_id, user_id, created_at, expires_at, last_activity,
                ip_address, user_agent, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            user.user_id,
            created_at.isoformat(),
            expires_at.isoformat(),
            created_at.isoformat(),
            ip_address,
            user_agent,
            True
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created session for attorney {user.email}: {session_id[:8]}...")
        return session_id
    
    def generate_mfa_qr_code(self, user: AttorneyUser, firm_name: str = "Law Firm") -> str:
        """Generate MFA QR code for attorney setup"""
        
        if not user.mfa_secret:
            raise ValueError("MFA not enabled for user")
        
        totp_uri = pyotp.totp.TOTP(user.mfa_secret).provisioning_uri(
            name=user.email,
            issuer_name=f"{firm_name} - Attorney Portal"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return base64.b64encode(img_buffer.getvalue()).decode()

# Global attorney security manager instance
attorney_security = AttorneySecurityManager()