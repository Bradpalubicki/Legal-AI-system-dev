"""
ADMIN ACTION AUDIT SYSTEM

Comprehensive audit system for administrative actions including:
- Configuration changes and system settings
- User account modifications and permissions
- System overrides and emergency access
- Compliance adjustments and policy changes

CRITICAL: Provides complete audit trail for all administrative activities.
"""

import os
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)

class AdminActionType(Enum):
    # User Management
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    USER_MODIFIED = "user_modified"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    USER_PASSWORD_RESET = "user_password_reset"
    USER_PASSWORD_FORCE_CHANGE = "user_password_force_change"
    
    # Role and Permission Management
    ROLE_CREATED = "role_created"
    ROLE_MODIFIED = "role_modified"
    ROLE_DELETED = "role_deleted"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    BULK_PERMISSION_CHANGE = "bulk_permission_change"
    
    # System Configuration
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    SECURITY_SETTING_CHANGED = "security_setting_changed"
    COMPLIANCE_SETTING_CHANGED = "compliance_setting_changed"
    ENCRYPTION_SETTING_CHANGED = "encryption_setting_changed"
    AUDIT_SETTING_CHANGED = "audit_setting_changed"
    BACKUP_SETTING_CHANGED = "backup_setting_changed"
    
    # Emergency and Override Actions
    EMERGENCY_ACCESS_GRANTED = "emergency_access_granted"
    SYSTEM_OVERRIDE_ACTIVATED = "system_override_activated"
    SECURITY_BYPASS_ENABLED = "security_bypass_enabled"
    MAINTENANCE_MODE_ACTIVATED = "maintenance_mode_activated"
    MAINTENANCE_MODE_DEACTIVATED = "maintenance_mode_deactivated"
    
    # Data Management
    DATA_EXPORT_AUTHORIZED = "data_export_authorized"
    DATA_PURGE_EXECUTED = "data_purge_executed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    DATABASE_MODIFIED = "database_modified"
    
    # Compliance and Legal
    LEGAL_HOLD_APPLIED = "legal_hold_applied"
    LEGAL_HOLD_REMOVED = "legal_hold_removed"
    COMPLIANCE_EXCEPTION_GRANTED = "compliance_exception_granted"
    AUDIT_LOG_ACCESSED = "audit_log_accessed"
    AUDIT_SETTING_MODIFIED = "audit_setting_modified"
    
    # Client and Matter Management
    CLIENT_CREATED = "client_created"
    CLIENT_MODIFIED = "client_modified"
    CLIENT_ARCHIVED = "client_archived"
    MATTER_CREATED = "matter_created"
    MATTER_MODIFIED = "matter_modified"
    MATTER_CLOSED = "matter_closed"
    CLIENT_MATTER_MERGED = "client_matter_merged"
    
    # System Monitoring
    ALERT_SUPPRESSED = "alert_suppressed"
    MONITORING_DISABLED = "monitoring_disabled"
    MONITORING_ENABLED = "monitoring_enabled"
    LOG_LEVEL_CHANGED = "log_level_changed"

class AdminActionSeverity(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AdminAction:
    """Individual admin action record"""
    action_id: str
    action_type: AdminActionType
    severity: AdminActionSeverity
    timestamp: datetime
    admin_user_id: str
    admin_session_id: Optional[str]
    target_object_type: str  # user, system, client, matter, etc.
    target_object_id: Optional[str]
    action_details: Dict[str, Any]
    before_state: Optional[Dict[str, Any]]
    after_state: Optional[Dict[str, Any]]
    justification: Optional[str]
    approval_required: bool
    approved_by: Optional[str]
    approval_timestamp: Optional[datetime]
    ip_address: Optional[str]
    user_agent: Optional[str]
    requires_notification: bool = False
    legal_hold: bool = False

class AdminActionAuditSystem:
    """Comprehensive admin action audit system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        
        # Initialize admin audit database
        self.db_path = Path(self.config['admin_audit_db_path'])
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_admin_audit_database()
        
        # Action buffer for performance
        self._action_buffer = []
        self._buffer_lock = threading.RLock()
        
        # Statistics tracking
        self.action_stats = defaultdict(int)
        
        # Critical action tracking
        self.critical_actions = []
        
        # Start background processing
        self._start_background_processors()
        
        logger.info("[ADMIN_AUDIT] Admin action audit system initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for admin audit"""
        return {
            'admin_audit_db_path': 'audit/admin_actions.db',
            'buffer_flush_interval_seconds': 30,
            'critical_action_notification': True,
            'approval_required_actions': [
                'USER_DELETED', 'DATA_PURGE_EXECUTED', 'EMERGENCY_ACCESS_GRANTED',
                'SYSTEM_OVERRIDE_ACTIVATED', 'LEGAL_HOLD_REMOVED'
            ],
            'auto_approve_low_risk': True,
            'retention_years': 10
        }
    
    def _init_admin_audit_database(self):
        """Initialize admin audit database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS admin_actions (
                    action_id TEXT PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    admin_user_id TEXT NOT NULL,
                    admin_session_id TEXT,
                    target_object_type TEXT NOT NULL,
                    target_object_id TEXT,
                    action_details TEXT NOT NULL,
                    before_state TEXT,
                    after_state TEXT,
                    justification TEXT,
                    approval_required BOOLEAN,
                    approved_by TEXT,
                    approval_timestamp TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    requires_notification BOOLEAN DEFAULT FALSE,
                    legal_hold BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS admin_approvals (
                    approval_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    requested_at TEXT NOT NULL,
                    approver_id TEXT,
                    approved_at TEXT,
                    approval_status TEXT DEFAULT 'PENDING',
                    approval_notes TEXT,
                    FOREIGN KEY (action_id) REFERENCES admin_actions (action_id)
                );
                
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    session_id TEXT PRIMARY KEY,
                    admin_user_id TEXT NOT NULL,
                    session_start TEXT NOT NULL,
                    session_end TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    elevated_privileges BOOLEAN DEFAULT FALSE,
                    actions_performed INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE
                );
                
                CREATE TABLE IF NOT EXISTS configuration_changes (
                    change_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    config_section TEXT NOT NULL,
                    config_key TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    change_reason TEXT,
                    rollback_available BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (action_id) REFERENCES admin_actions (action_id)
                );
                
                CREATE TABLE IF NOT EXISTS emergency_access_log (
                    access_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    emergency_type TEXT NOT NULL,
                    granted_by TEXT NOT NULL,
                    granted_to TEXT NOT NULL,
                    granted_at TEXT NOT NULL,
                    expires_at TEXT,
                    access_reason TEXT NOT NULL,
                    supervisor_notification_sent BOOLEAN DEFAULT FALSE,
                    revoked_at TEXT,
                    revoked_by TEXT,
                    FOREIGN KEY (action_id) REFERENCES admin_actions (action_id)
                );
                
                -- Indexes for performance
                CREATE INDEX IF NOT EXISTS idx_admin_actions_timestamp ON admin_actions(timestamp);
                CREATE INDEX IF NOT EXISTS idx_admin_actions_type ON admin_actions(action_type);
                CREATE INDEX IF NOT EXISTS idx_admin_actions_admin ON admin_actions(admin_user_id);
                CREATE INDEX IF NOT EXISTS idx_admin_actions_target ON admin_actions(target_object_type, target_object_id);
                CREATE INDEX IF NOT EXISTS idx_admin_actions_severity ON admin_actions(severity);
                CREATE INDEX IF NOT EXISTS idx_admin_approvals_status ON admin_approvals(approval_status);
                CREATE INDEX IF NOT EXISTS idx_config_changes_section ON configuration_changes(config_section);
            """)
            conn.commit()
    
    def log_admin_action(self, action_type: AdminActionType, admin_user_id: str,
                        target_object_type: str, target_object_id: str = None,
                        action_details: Dict[str, Any] = None,
                        before_state: Dict[str, Any] = None,
                        after_state: Dict[str, Any] = None,
                        justification: str = None,
                        session_id: str = None, ip_address: str = None,
                        user_agent: str = None) -> str:
        """Log administrative action with full audit trail"""
        
        # Generate action ID
        action_id = f"admin_{action_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Determine severity
        severity = self._determine_action_severity(action_type, action_details)
        
        # Check if approval is required
        approval_required = self._requires_approval(action_type, severity, action_details)
        
        # Check if this requires legal hold
        legal_hold = self._requires_legal_hold(action_type, target_object_type)
        
        # Check if notification is required
        requires_notification = self._requires_notification(action_type, severity)
        
        # Create admin action record
        admin_action = AdminAction(
            action_id=action_id,
            action_type=action_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            admin_user_id=admin_user_id,
            admin_session_id=session_id,
            target_object_type=target_object_type,
            target_object_id=target_object_id,
            action_details=action_details or {},
            before_state=before_state,
            after_state=after_state,
            justification=justification,
            approval_required=approval_required,
            approved_by=None,
            approval_timestamp=None,
            ip_address=ip_address,
            user_agent=user_agent,
            requires_notification=requires_notification,
            legal_hold=legal_hold
        )
        
        # Store action
        self._store_admin_action(admin_action)
        
        # Handle special action types
        if action_type in [AdminActionType.SYSTEM_CONFIG_CHANGED, AdminActionType.SECURITY_SETTING_CHANGED]:
            self._log_configuration_change(admin_action, action_details)
        elif action_type == AdminActionType.EMERGENCY_ACCESS_GRANTED:
            self._log_emergency_access(admin_action, action_details)
        
        # Handle approval workflow
        if approval_required and not self._is_auto_approved(action_type, admin_user_id):
            self._create_approval_request(action_id, admin_user_id)
        
        # Send notifications if required
        if requires_notification:
            self._send_action_notification(admin_action)
        
        # Update statistics
        self.action_stats[action_type.value] += 1
        self.action_stats[f"severity_{severity.value}"] += 1
        
        if severity == AdminActionSeverity.CRITICAL:
            self.critical_actions.append(admin_action)
        
        logger.info(f"[ADMIN_AUDIT] Admin action logged: {action_type.value} by {admin_user_id}")
        
        return action_id
    
    def log_user_management_action(self, action_type: AdminActionType, admin_user_id: str,
                                  target_user_id: str, changes: Dict[str, Any] = None,
                                  justification: str = None, **context) -> str:
        """Log user management actions"""
        
        # Get current user state for before/after comparison
        before_state = self._get_user_state(target_user_id)
        
        action_details = {
            'target_user_id': target_user_id,
            'changes': changes or {},
            'action_context': context
        }
        
        return self.log_admin_action(
            action_type=action_type,
            admin_user_id=admin_user_id,
            target_object_type='user',
            target_object_id=target_user_id,
            action_details=action_details,
            before_state=before_state,
            after_state=None,  # Will be updated after action is completed
            justification=justification,
            session_id=context.get('session_id'),
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
    
    def log_system_configuration_change(self, admin_user_id: str, config_section: str,
                                      config_key: str, old_value: Any, new_value: Any,
                                      change_reason: str = None, **context) -> str:
        """Log system configuration changes"""
        
        action_details = {
            'config_section': config_section,
            'config_key': config_key,
            'old_value': str(old_value),
            'new_value': str(new_value),
            'change_reason': change_reason
        }
        
        before_state = {config_key: old_value}
        after_state = {config_key: new_value}
        
        # Determine specific action type based on config section
        if config_section.lower() == 'security':
            action_type = AdminActionType.SECURITY_SETTING_CHANGED
        elif config_section.lower() == 'compliance':
            action_type = AdminActionType.COMPLIANCE_SETTING_CHANGED
        elif config_section.lower() == 'encryption':
            action_type = AdminActionType.ENCRYPTION_SETTING_CHANGED
        elif config_section.lower() == 'audit':
            action_type = AdminActionType.AUDIT_SETTING_CHANGED
        else:
            action_type = AdminActionType.SYSTEM_CONFIG_CHANGED
        
        return self.log_admin_action(
            action_type=action_type,
            admin_user_id=admin_user_id,
            target_object_type='system_config',
            target_object_id=f"{config_section}.{config_key}",
            action_details=action_details,
            before_state=before_state,
            after_state=after_state,
            justification=change_reason,
            session_id=context.get('session_id'),
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
    
    def log_emergency_access(self, admin_user_id: str, emergency_type: str,
                           granted_to: str, access_reason: str,
                           expires_at: datetime = None, **context) -> str:
        """Log emergency access grants"""
        
        action_details = {
            'emergency_type': emergency_type,
            'granted_to': granted_to,
            'access_reason': access_reason,
            'expires_at': expires_at.isoformat() if expires_at else None,
            'supervisor_notified': True  # Always notify for emergency access
        }
        
        return self.log_admin_action(
            action_type=AdminActionType.EMERGENCY_ACCESS_GRANTED,
            admin_user_id=admin_user_id,
            target_object_type='emergency_access',
            target_object_id=granted_to,
            action_details=action_details,
            justification=access_reason,
            session_id=context.get('session_id'),
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
    
    def log_data_action(self, action_type: AdminActionType, admin_user_id: str,
                       data_type: str, data_identifier: str,
                       action_details: Dict[str, Any] = None,
                       justification: str = None, **context) -> str:
        """Log data-related administrative actions"""
        
        details = {
            'data_type': data_type,
            'data_identifier': data_identifier,
            'record_count': action_details.get('record_count') if action_details else None,
            'data_size': action_details.get('data_size') if action_details else None
        }
        
        if action_details:
            details.update(action_details)
        
        return self.log_admin_action(
            action_type=action_type,
            admin_user_id=admin_user_id,
            target_object_type='data',
            target_object_id=data_identifier,
            action_details=details,
            justification=justification,
            session_id=context.get('session_id'),
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
    
    def approve_action(self, action_id: str, approver_id: str,
                      approval_notes: str = None) -> bool:
        """Approve a pending admin action"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Update approval status
            conn.execute(
                """UPDATE admin_approvals 
                   SET approver_id = ?, approved_at = ?, approval_status = 'APPROVED', 
                       approval_notes = ?
                   WHERE action_id = ? AND approval_status = 'PENDING'""",
                (approver_id, datetime.utcnow().isoformat(), approval_notes, action_id)
            )
            
            # Update the admin action
            conn.execute(
                """UPDATE admin_actions 
                   SET approved_by = ?, approval_timestamp = ?
                   WHERE action_id = ?""",
                (approver_id, datetime.utcnow().isoformat(), action_id)
            )
            
            conn.commit()
            rows_affected = conn.total_changes
        
        if rows_affected > 0:
            logger.info(f"[ADMIN_AUDIT] Action approved: {action_id} by {approver_id}")
            
            # Log the approval as an admin action
            self.log_admin_action(
                action_type=AdminActionType.SYSTEM_OVERRIDE_ACTIVATED,
                admin_user_id=approver_id,
                target_object_type='approval',
                target_object_id=action_id,
                action_details={
                    'approved_action_id': action_id,
                    'approval_notes': approval_notes
                },
                justification=f"Approved action {action_id}"
            )
            
            return True
        
        return False
    
    def get_pending_approvals(self, approver_id: str = None) -> List[Dict[str, Any]]:
        """Get pending approval requests"""
        
        with sqlite3.connect(self.db_path) as conn:
            if approver_id:
                # In a real system, this would check if the approver has permission
                query = """
                    SELECT aa.action_id, aa.action_type, aa.severity, aa.admin_user_id,
                           aa.target_object_type, aa.target_object_id, aa.justification,
                           ap.requested_at, ap.approval_status
                    FROM admin_actions aa
                    JOIN admin_approvals ap ON aa.action_id = ap.action_id
                    WHERE ap.approval_status = 'PENDING'
                    ORDER BY ap.requested_at ASC
                """
                cursor = conn.execute(query)
            else:
                query = """
                    SELECT aa.action_id, aa.action_type, aa.severity, aa.admin_user_id,
                           aa.target_object_type, aa.target_object_id, aa.justification,
                           ap.requested_at, ap.approval_status
                    FROM admin_actions aa
                    JOIN admin_approvals ap ON aa.action_id = ap.action_id
                    WHERE ap.approval_status = 'PENDING'
                    ORDER BY ap.requested_at ASC
                """
                cursor = conn.execute(query)
            
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
        
        return results
    
    def get_admin_action_history(self, admin_user_id: str = None, 
                               start_date: datetime = None, 
                               end_date: datetime = None,
                               action_types: List[AdminActionType] = None,
                               limit: int = 1000) -> List[Dict[str, Any]]:
        """Get admin action history with filtering"""
        
        conditions = []
        params = []
        
        if admin_user_id:
            conditions.append("admin_user_id = ?")
            params.append(admin_user_id)
        
        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date.isoformat())
        
        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date.isoformat())
        
        if action_types:
            type_conditions = []
            for action_type in action_types:
                type_conditions.append("action_type = ?")
                params.append(action_type.value)
            conditions.append(f"({' OR '.join(type_conditions)})")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT action_id, action_type, severity, timestamp, admin_user_id,
                   target_object_type, target_object_id, action_details, justification,
                   approval_required, approved_by, ip_address
            FROM admin_actions
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params + [limit])
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                action_dict = dict(zip(columns, row))
                # Parse JSON fields
                if action_dict['action_details']:
                    action_dict['action_details'] = json.loads(action_dict['action_details'])
                results.append(action_dict)
        
        return results
    
    def _store_admin_action(self, action: AdminAction):
        """Store admin action in buffer"""
        with self._buffer_lock:
            self._action_buffer.append(action)
            
            # Flush buffer if getting full
            if len(self._action_buffer) >= 50:
                self._flush_action_buffer()
    
    def _flush_action_buffer(self):
        """Flush action buffer to database"""
        if not self._action_buffer:
            return
        
        actions_to_flush = self._action_buffer.copy()
        self._action_buffer.clear()
        
        with sqlite3.connect(self.db_path) as conn:
            for action in actions_to_flush:
                conn.execute(
                    """INSERT INTO admin_actions 
                       (action_id, action_type, severity, timestamp, admin_user_id,
                        admin_session_id, target_object_type, target_object_id,
                        action_details, before_state, after_state, justification,
                        approval_required, approved_by, approval_timestamp,
                        ip_address, user_agent, requires_notification, legal_hold)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        action.action_id, action.action_type.value, action.severity.value,
                        action.timestamp.isoformat(), action.admin_user_id,
                        action.admin_session_id, action.target_object_type, action.target_object_id,
                        json.dumps(action.action_details),
                        json.dumps(action.before_state) if action.before_state else None,
                        json.dumps(action.after_state) if action.after_state else None,
                        action.justification, action.approval_required,
                        action.approved_by,
                        action.approval_timestamp.isoformat() if action.approval_timestamp else None,
                        action.ip_address, action.user_agent,
                        action.requires_notification, action.legal_hold
                    )
                )
            conn.commit()
    
    def _determine_action_severity(self, action_type: AdminActionType, action_details: Dict[str, Any]) -> AdminActionSeverity:
        """Determine severity of admin action"""
        
        # Critical actions
        if action_type in [
            AdminActionType.USER_DELETED,
            AdminActionType.DATA_PURGE_EXECUTED,
            AdminActionType.EMERGENCY_ACCESS_GRANTED,
            AdminActionType.SYSTEM_OVERRIDE_ACTIVATED,
            AdminActionType.LEGAL_HOLD_REMOVED
        ]:
            return AdminActionSeverity.CRITICAL
        
        # High severity actions
        elif action_type in [
            AdminActionType.SECURITY_SETTING_CHANGED,
            AdminActionType.ENCRYPTION_SETTING_CHANGED,
            AdminActionType.BULK_PERMISSION_CHANGE,
            AdminActionType.DATABASE_MODIFIED,
            AdminActionType.AUDIT_SETTING_MODIFIED
        ]:
            return AdminActionSeverity.HIGH
        
        # Medium severity actions
        elif action_type in [
            AdminActionType.USER_MODIFIED,
            AdminActionType.ROLE_MODIFIED,
            AdminActionType.SYSTEM_CONFIG_CHANGED,
            AdminActionType.COMPLIANCE_SETTING_CHANGED
        ]:
            return AdminActionSeverity.MEDIUM
        
        # Low severity actions
        elif action_type in [
            AdminActionType.USER_CREATED,
            AdminActionType.ROLE_CREATED,
            AdminActionType.CLIENT_CREATED,
            AdminActionType.MATTER_CREATED
        ]:
            return AdminActionSeverity.LOW
        
        # Default to medium
        else:
            return AdminActionSeverity.MEDIUM
    
    def _requires_approval(self, action_type: AdminActionType, severity: AdminActionSeverity, action_details: Dict[str, Any]) -> bool:
        """Check if action requires approval"""
        
        # Critical actions always require approval
        if severity == AdminActionSeverity.CRITICAL:
            return True
        
        # Specific actions that require approval
        if action_type.value.upper() in self.config['approval_required_actions']:
            return True
        
        # Bulk operations require approval
        if 'bulk' in action_type.value.lower():
            return True
        
        return False
    
    def _requires_legal_hold(self, action_type: AdminActionType, target_object_type: str) -> bool:
        """Check if action requires legal hold"""
        
        legal_hold_actions = [
            AdminActionType.DATA_PURGE_EXECUTED,
            AdminActionType.LEGAL_HOLD_REMOVED,
            AdminActionType.DATA_EXPORT_AUTHORIZED
        ]
        
        return action_type in legal_hold_actions or target_object_type in ['legal_document', 'client_data']
    
    def _requires_notification(self, action_type: AdminActionType, severity: AdminActionSeverity) -> bool:
        """Check if action requires notification"""
        
        return severity in [AdminActionSeverity.CRITICAL, AdminActionSeverity.HIGH]
    
    def _is_auto_approved(self, action_type: AdminActionType, admin_user_id: str) -> bool:
        """Check if action can be auto-approved"""
        
        # Super admins can auto-approve low-risk actions
        if self.config['auto_approve_low_risk'] and self._is_super_admin(admin_user_id):
            low_risk_actions = [
                AdminActionType.USER_CREATED,
                AdminActionType.ROLE_CREATED,
                AdminActionType.CLIENT_CREATED
            ]
            return action_type in low_risk_actions
        
        return False
    
    def _create_approval_request(self, action_id: str, requested_by: str):
        """Create approval request"""
        
        approval_id = f"approval_{action_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO admin_approvals 
                   (approval_id, action_id, requested_by, requested_at)
                   VALUES (?, ?, ?, ?)""",
                (approval_id, action_id, requested_by, datetime.utcnow().isoformat())
            )
            conn.commit()
    
    def _log_configuration_change(self, action: AdminAction, action_details: Dict[str, Any]):
        """Log configuration change details"""
        
        change_id = f"config_{action.action_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO configuration_changes 
                   (change_id, action_id, config_section, config_key, old_value, new_value, change_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (change_id, action.action_id,
                 action_details.get('config_section', 'unknown'),
                 action_details.get('config_key', 'unknown'),
                 action_details.get('old_value'),
                 action_details.get('new_value'),
                 action_details.get('change_reason'))
            )
            conn.commit()
    
    def _log_emergency_access(self, action: AdminAction, action_details: Dict[str, Any]):
        """Log emergency access details"""
        
        access_id = f"emergency_{action.action_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO emergency_access_log 
                   (access_id, action_id, emergency_type, granted_by, granted_to, 
                    granted_at, expires_at, access_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (access_id, action.action_id,
                 action_details.get('emergency_type', 'unknown'),
                 action.admin_user_id,
                 action_details.get('granted_to'),
                 action.timestamp.isoformat(),
                 action_details.get('expires_at'),
                 action_details.get('access_reason'))
            )
            conn.commit()
    
    def _send_action_notification(self, action: AdminAction):
        """Send notification for critical admin action"""
        # Placeholder for notification system
        logger.warning(f"[ADMIN_AUDIT] CRITICAL ACTION: {action.action_type.value} by {action.admin_user_id}")
    
    def _get_user_state(self, user_id: str) -> Dict[str, Any]:
        """Get current user state for audit trail"""
        # Placeholder - would fetch from user management system
        return {'user_id': user_id, 'status': 'active'}
    
    def _is_super_admin(self, admin_user_id: str) -> bool:
        """Check if user is super admin"""
        # Placeholder - would check user roles
        return admin_user_id.startswith('admin_')
    
    def _start_background_processors(self):
        """Start background processing threads"""
        
        def flush_periodically():
            import time
            while True:
                try:
                    time.sleep(self.config['buffer_flush_interval_seconds'])
                    with self._buffer_lock:
                        if self._action_buffer:
                            self._flush_action_buffer()
                except Exception as e:
                    logger.error(f"[ADMIN_AUDIT] Error flushing buffer: {e}")
        
        # Start background thread
        flush_thread = threading.Thread(target=flush_periodically, name="AdminAuditFlush", daemon=True)
        flush_thread.start()
    
    def get_admin_statistics(self) -> Dict[str, Any]:
        """Get comprehensive admin action statistics"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Total actions
            cursor = conn.execute("SELECT COUNT(*) FROM admin_actions")
            total_actions = cursor.fetchone()[0]
            
            # Actions by severity (last 24 hours)
            yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
            cursor = conn.execute(
                """SELECT severity, COUNT(*) FROM admin_actions 
                   WHERE timestamp > ? GROUP BY severity""",
                (yesterday,)
            )
            severity_stats = dict(cursor.fetchall())
            
            # Pending approvals
            cursor = conn.execute("SELECT COUNT(*) FROM admin_approvals WHERE approval_status = 'PENDING'")
            pending_approvals = cursor.fetchone()[0]
            
            # Emergency access grants (last 7 days)
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            cursor = conn.execute(
                "SELECT COUNT(*) FROM emergency_access_log WHERE granted_at > ?",
                (week_ago,)
            )
            emergency_access_7d = cursor.fetchone()[0]
        
        return {
            'total_admin_actions': total_actions,
            'total_actions': total_actions,  # Alias for compatibility
            'actions_last_24h': sum(severity_stats.values()),
            'severity_distribution': severity_stats,
            'pending_approvals': pending_approvals,
            'emergency_access_last_7d': emergency_access_7d,
            'buffer_size': len(self._action_buffer),
            'action_type_stats': dict(self.action_stats),
            'system_health': 'healthy'
        }
    
    def get_admin_audit_statistics(self) -> Dict[str, Any]:
        """Alias for get_admin_statistics for compatibility"""
        return self.get_admin_statistics()

# Global admin action audit system
admin_action_audit = AdminActionAuditSystem()

__all__ = [
    'AdminActionAuditSystem',
    'AdminAction',
    'AdminActionType',
    'AdminActionSeverity',
    'admin_action_audit'
]