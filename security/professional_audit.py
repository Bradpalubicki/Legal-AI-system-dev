#!/usr/bin/env python3
"""
Professional Attorney Audit Logging System
Comprehensive audit trails for attorney accountability and professional responsibility
"""

import os
import json
import sqlite3
import logging
import logging.handlers
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
import hashlib
import secrets
from pathlib import Path

class ProfessionalAuditEventType(Enum):
    """Professional attorney audit event types for accountability"""
    
    # Client Relationship Events
    CLIENT_INTAKE = "client_intake"
    CLIENT_CONFLICT_CHECK = "client_conflict_check"
    CLIENT_RELATIONSHIP_ESTABLISHED = "client_relationship_established"
    CLIENT_RELATIONSHIP_TERMINATED = "client_relationship_terminated"
    CLIENT_CONTACT_LOGGED = "client_contact_logged"
    
    # Document Events
    PRIVILEGED_DOCUMENT_ACCESSED = "privileged_document_accessed"
    PRIVILEGED_DOCUMENT_CREATED = "privileged_document_created"
    PRIVILEGED_DOCUMENT_MODIFIED = "privileged_document_modified"
    PRIVILEGED_DOCUMENT_SHARED = "privileged_document_shared"
    DOCUMENT_RETENTION_APPLIED = "document_retention_applied"
    DOCUMENT_DESTRUCTION_SCHEDULED = "document_destruction_scheduled"
    
    # Case Management Events
    CASE_CREATED = "case_created"
    CASE_ASSIGNED = "case_assigned"
    CASE_REASSIGNED = "case_reassigned"
    CASE_STATUS_CHANGED = "case_status_changed"
    CASE_CLOSED = "case_closed"
    CASE_BILLING_REVIEW = "case_billing_review"
    
    # Legal Work Product Events
    LEGAL_RESEARCH_CONDUCTED = "legal_research_conducted"
    BRIEF_DRAFTED = "brief_drafted"
    BRIEF_REVIEWED = "brief_reviewed"
    BRIEF_FILED = "brief_filed"
    CONTRACT_REVIEWED = "contract_reviewed"
    CONTRACT_NEGOTIATED = "contract_negotiated"
    COURT_FILING_SUBMITTED = "court_filing_submitted"
    
    # Professional Responsibility Events
    ETHICAL_CONSULTATION = "ethical_consultation"
    CONFLICT_WAIVER_OBTAINED = "conflict_waiver_obtained"
    PROFESSIONAL_CONDUCT_REVIEW = "professional_conduct_review"
    CONTINUING_EDUCATION_LOGGED = "continuing_education_logged"
    BAR_REQUIREMENT_MET = "bar_requirement_met"
    
    # Billing and Financial Events
    TIME_ENTRY_CREATED = "time_entry_created"
    TIME_ENTRY_MODIFIED = "time_entry_modified"
    BILLING_STATEMENT_GENERATED = "billing_statement_generated"
    BILLING_STATEMENT_REVIEWED = "billing_statement_reviewed"
    PAYMENT_RECEIVED = "payment_received"
    TRUST_ACCOUNT_TRANSACTION = "trust_account_transaction"
    
    # Supervision and Review Events
    WORK_PRODUCT_SUPERVISED = "work_product_supervised"
    PEER_REVIEW_CONDUCTED = "peer_review_conducted"
    QUALITY_ASSURANCE_CHECK = "quality_assurance_check"
    COMPLIANCE_REVIEW = "compliance_review"
    
    # Security and Access Events
    ATTORNEY_LOGIN = "attorney_login"
    ATTORNEY_LOGOUT = "attorney_logout"
    SESSION_TIMEOUT = "session_timeout"
    PRIVILEGE_ESCALATION_ATTEMPTED = "privilege_escalation_attempted"
    UNAUTHORIZED_ACCESS_ATTEMPTED = "unauthorized_access_attempted"
    
    # System Administration Events
    USER_ROLE_CHANGED = "user_role_changed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    SYSTEM_CONFIGURATION_CHANGED = "system_configuration_changed"
    BACKUP_CREATED = "backup_created"
    DATA_EXPORT_PERFORMED = "data_export_performed"

class ProfessionalRiskLevel(Enum):
    """Professional risk assessment levels"""
    ROUTINE = "routine"
    ELEVATED = "elevated"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"
    REGULATORY = "regulatory"

class BillingCategory(Enum):
    """Attorney billing categories"""
    ADMINISTRATIVE = "administrative"
    CLIENT_DEVELOPMENT = "client_development"
    RESEARCH = "research"
    DRAFTING = "drafting"
    REVIEW = "review"
    NEGOTIATION = "negotiation"
    LITIGATION = "litigation"
    COURT_APPEARANCE = "court_appearance"
    TRAVEL = "travel"
    PRO_BONO = "pro_bono"

@dataclass
class ProfessionalAuditEvent:
    """Professional audit event with attorney accountability details"""
    event_id: str
    timestamp: datetime
    event_type: ProfessionalAuditEventType
    risk_level: ProfessionalRiskLevel
    
    # Attorney Information
    attorney_id: str
    attorney_email: str
    attorney_bar_number: Optional[str]
    attorney_role: str
    supervising_attorney: Optional[str]
    
    # Context Information
    client_id: Optional[str]
    case_id: Optional[str]
    matter_id: Optional[str]
    document_id: Optional[str]
    
    # Professional Details
    practice_area: Optional[str]
    billing_category: Optional[BillingCategory]
    time_spent_minutes: Optional[int]
    billable_hours: Optional[float]
    
    # Event Details
    description: str
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    session_id: str
    
    # Compliance Information
    requires_review: bool
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    compliance_notes: Optional[str]
    
    # Data Classification
    contains_privileged_info: bool
    retention_category: str
    destruction_date: Optional[datetime]

class ProfessionalAuditSystem:
    """Professional attorney audit system with accountability features"""
    
    def __init__(self, audit_db_path: str = "professional_audit.db"):
        self.audit_db_path = audit_db_path
        self.logger = self._setup_logger()
        self._init_database()
        
        # Risk assessment rules
        self.risk_rules = {
            # High-risk events
            ProfessionalAuditEventType.PRIVILEGED_DOCUMENT_SHARED: ProfessionalRiskLevel.HIGH_RISK,
            ProfessionalAuditEventType.CLIENT_RELATIONSHIP_TERMINATED: ProfessionalRiskLevel.HIGH_RISK,
            ProfessionalAuditEventType.CONFLICT_WAIVER_OBTAINED: ProfessionalRiskLevel.HIGH_RISK,
            ProfessionalAuditEventType.TRUST_ACCOUNT_TRANSACTION: ProfessionalRiskLevel.CRITICAL,
            
            # Regulatory events
            ProfessionalAuditEventType.COURT_FILING_SUBMITTED: ProfessionalRiskLevel.REGULATORY,
            ProfessionalAuditEventType.PROFESSIONAL_CONDUCT_REVIEW: ProfessionalRiskLevel.REGULATORY,
            ProfessionalAuditEventType.BAR_REQUIREMENT_MET: ProfessionalRiskLevel.REGULATORY,
            
            # Elevated risk events
            ProfessionalAuditEventType.PRIVILEGE_ESCALATION_ATTEMPTED: ProfessionalRiskLevel.ELEVATED,
            ProfessionalAuditEventType.TIME_ENTRY_MODIFIED: ProfessionalRiskLevel.ELEVATED,
            ProfessionalAuditEventType.USER_ROLE_CHANGED: ProfessionalRiskLevel.ELEVATED,
        }
        
        # Events requiring mandatory review
        self.mandatory_review_events = {
            ProfessionalAuditEventType.PRIVILEGED_DOCUMENT_SHARED,
            ProfessionalAuditEventType.CONFLICT_WAIVER_OBTAINED,
            ProfessionalAuditEventType.TRUST_ACCOUNT_TRANSACTION,
            ProfessionalAuditEventType.COURT_FILING_SUBMITTED,
            ProfessionalAuditEventType.CLIENT_RELATIONSHIP_TERMINATED,
            ProfessionalAuditEventType.PROFESSIONAL_CONDUCT_REVIEW
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup professional audit logger with compliance formatting"""
        logger = logging.getLogger('professional_audit')
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        Path('logs').mkdir(exist_ok=True)
        
        # Professional audit file handler
        handler = logging.handlers.RotatingFileHandler(
            'logs/professional_audit.log',
            maxBytes=100*1024*1024,  # 100MB
            backupCount=200,  # Keep 200 backup files (20GB total)
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - PROFESSIONAL_AUDIT - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize professional audit database"""
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        # Professional audit events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS professional_audit_events (
                event_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                event_type TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                attorney_id TEXT NOT NULL,
                attorney_email TEXT NOT NULL,
                attorney_bar_number TEXT,
                attorney_role TEXT NOT NULL,
                supervising_attorney TEXT,
                client_id TEXT,
                case_id TEXT,
                matter_id TEXT,
                document_id TEXT,
                practice_area TEXT,
                billing_category TEXT,
                time_spent_minutes INTEGER,
                billable_hours REAL,
                description TEXT NOT NULL,
                details TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                session_id TEXT NOT NULL,
                requires_review BOOLEAN NOT NULL,
                reviewed_by TEXT,
                reviewed_at TIMESTAMP,
                compliance_notes TEXT,
                contains_privileged_info BOOLEAN NOT NULL,
                retention_category TEXT NOT NULL,
                destruction_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Professional reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS professional_reviews (
                review_id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                reviewer_role TEXT NOT NULL,
                review_date TIMESTAMP NOT NULL,
                review_status TEXT NOT NULL,
                findings TEXT,
                recommendations TEXT,
                follow_up_required BOOLEAN DEFAULT FALSE,
                follow_up_date TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES professional_audit_events (event_id)
            )
        ''')
        
        # Attorney metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attorney_metrics (
                attorney_id TEXT NOT NULL,
                metric_date DATE NOT NULL,
                total_events INTEGER DEFAULT 0,
                high_risk_events INTEGER DEFAULT 0,
                regulatory_events INTEGER DEFAULT 0,
                billable_hours REAL DEFAULT 0.0,
                pro_bono_hours REAL DEFAULT 0.0,
                client_interactions INTEGER DEFAULT 0,
                document_reviews INTEGER DEFAULT 0,
                compliance_score REAL DEFAULT 100.0,
                PRIMARY KEY (attorney_id, metric_date)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_attorney_date ON professional_audit_events (attorney_id, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_event_type ON professional_audit_events (event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_risk_level ON professional_audit_events (risk_level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_client ON professional_audit_events (client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_case ON professional_audit_events (case_id)')
        
        conn.commit()
        conn.close()
    
    def log_professional_event(
        self,
        event_type: ProfessionalAuditEventType,
        attorney_id: str,
        attorney_email: str,
        description: str,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        session_id: str = "unknown",
        attorney_bar_number: Optional[str] = None,
        attorney_role: str = "attorney",
        supervising_attorney: Optional[str] = None,
        client_id: Optional[str] = None,
        case_id: Optional[str] = None,
        matter_id: Optional[str] = None,
        document_id: Optional[str] = None,
        practice_area: Optional[str] = None,
        billing_category: Optional[BillingCategory] = None,
        time_spent_minutes: Optional[int] = None,
        billable_hours: Optional[float] = None,
        contains_privileged_info: bool = False,
        retention_category: str = "business_records",
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log professional attorney event with accountability details"""
        
        event_id = secrets.token_hex(16)
        timestamp = datetime.now()
        
        # Determine risk level
        risk_level = self.risk_rules.get(event_type, ProfessionalRiskLevel.ROUTINE)
        
        # Determine if review is required
        requires_review = event_type in self.mandatory_review_events or risk_level in [
            ProfessionalRiskLevel.HIGH_RISK, 
            ProfessionalRiskLevel.CRITICAL, 
            ProfessionalRiskLevel.REGULATORY
        ]
        
        # Calculate destruction date based on retention category
        destruction_date = self._calculate_destruction_date(retention_category, timestamp)
        
        if details is None:
            details = {}
        
        event = ProfessionalAuditEvent(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            risk_level=risk_level,
            attorney_id=attorney_id,
            attorney_email=attorney_email,
            attorney_bar_number=attorney_bar_number,
            attorney_role=attorney_role,
            supervising_attorney=supervising_attorney,
            client_id=client_id,
            case_id=case_id,
            matter_id=matter_id,
            document_id=document_id,
            practice_area=practice_area,
            billing_category=billing_category,
            time_spent_minutes=time_spent_minutes,
            billable_hours=billable_hours,
            description=description,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            requires_review=requires_review,
            reviewed_by=None,
            reviewed_at=None,
            compliance_notes=None,
            contains_privileged_info=contains_privileged_info,
            retention_category=retention_category,
            destruction_date=destruction_date
        )
        
        # Store in database
        self._store_event(event)
        
        # Log to file
        self._log_to_file(event)
        
        # Update attorney metrics
        self._update_attorney_metrics(event)
        
        # Alert on high-risk events
        if risk_level in [ProfessionalRiskLevel.HIGH_RISK, ProfessionalRiskLevel.CRITICAL]:
            self._send_risk_alert(event)
        
        return event_id
    
    def _calculate_destruction_date(self, retention_category: str, created_at: datetime) -> Optional[datetime]:
        """Calculate document destruction date based on legal requirements"""
        retention_periods = {
            "client_files": timedelta(days=7*365),  # 7 years
            "financial_records": timedelta(days=7*365),  # 7 years
            "court_documents": timedelta(days=10*365),  # 10 years
            "privileged_communications": timedelta(days=20*365),  # 20 years
            "trust_account_records": timedelta(days=10*365),  # 10 years
            "business_records": timedelta(days=3*365),  # 3 years
            "temporary_work_product": timedelta(days=1*365),  # 1 year
            "permanent_records": None,  # Never destroy
        }
        
        period = retention_periods.get(retention_category, timedelta(days=7*365))
        return (created_at + period) if period else None
    
    def _store_event(self, event: ProfessionalAuditEvent):
        """Store professional audit event in database"""
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO professional_audit_events (
                    event_id, timestamp, event_type, risk_level, attorney_id,
                    attorney_email, attorney_bar_number, attorney_role, supervising_attorney,
                    client_id, case_id, matter_id, document_id, practice_area,
                    billing_category, time_spent_minutes, billable_hours, description,
                    details, ip_address, user_agent, session_id, requires_review,
                    reviewed_by, reviewed_at, compliance_notes, contains_privileged_info,
                    retention_category, destruction_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.timestamp.isoformat(),
                event.event_type.value,
                event.risk_level.value,
                event.attorney_id,
                event.attorney_email,
                event.attorney_bar_number,
                event.attorney_role,
                event.supervising_attorney,
                event.client_id,
                event.case_id,
                event.matter_id,
                event.document_id,
                event.practice_area,
                event.billing_category.value if event.billing_category else None,
                event.time_spent_minutes,
                event.billable_hours,
                event.description,
                json.dumps(event.details),
                event.ip_address,
                event.user_agent,
                event.session_id,
                event.requires_review,
                event.reviewed_by,
                event.reviewed_at.isoformat() if event.reviewed_at else None,
                event.compliance_notes,
                event.contains_privileged_info,
                event.retention_category,
                event.destruction_date.isoformat() if event.destruction_date else None
            ))
            
            conn.commit()
        finally:
            conn.close()
    
    def _log_to_file(self, event: ProfessionalAuditEvent):
        """Log professional event to audit file"""
        log_entry = (
            f"EventID={event.event_id} "
            f"Timestamp={event.timestamp.isoformat()} "
            f"EventType={event.event_type.value} "
            f"RiskLevel={event.risk_level.value} "
            f"Attorney={event.attorney_email} "
            f"BarNumber={event.attorney_bar_number or 'N/A'} "
            f"Role={event.attorney_role} "
            f"ClientID={event.client_id or 'N/A'} "
            f"CaseID={event.case_id or 'N/A'} "
            f"PracticeArea={event.practice_area or 'N/A'} "
            f"BillableHours={event.billable_hours or 0.0} "
            f"RequiresReview={event.requires_review} "
            f"PrivilegedInfo={event.contains_privileged_info} "
            f"Description={event.description}"
        )
        
        self.logger.info(log_entry)
    
    def _update_attorney_metrics(self, event: ProfessionalAuditEvent):
        """Update daily attorney metrics"""
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        metric_date = event.timestamp.date()
        
        try:
            # Insert or update metrics
            cursor.execute('''
                INSERT OR IGNORE INTO attorney_metrics (attorney_id, metric_date)
                VALUES (?, ?)
            ''', (event.attorney_id, metric_date.isoformat()))
            
            # Update counters
            updates = ["total_events = total_events + 1"]
            
            if event.risk_level in [ProfessionalRiskLevel.HIGH_RISK, ProfessionalRiskLevel.CRITICAL]:
                updates.append("high_risk_events = high_risk_events + 1")
            
            if event.risk_level == ProfessionalRiskLevel.REGULATORY:
                updates.append("regulatory_events = regulatory_events + 1")
            
            if event.billable_hours:
                if event.billing_category == BillingCategory.PRO_BONO:
                    updates.append(f"pro_bono_hours = pro_bono_hours + {event.billable_hours}")
                else:
                    updates.append(f"billable_hours = billable_hours + {event.billable_hours}")
            
            if event.client_id:
                updates.append("client_interactions = client_interactions + 1")
            
            if event.document_id:
                updates.append("document_reviews = document_reviews + 1")
            
            cursor.execute(f'''
                UPDATE attorney_metrics 
                SET {', '.join(updates)}
                WHERE attorney_id = ? AND metric_date = ?
            ''', (event.attorney_id, metric_date.isoformat()))
            
            conn.commit()
        finally:
            conn.close()
    
    def _send_risk_alert(self, event: ProfessionalAuditEvent):
        """Send alert for high-risk professional events"""
        alert_message = (
            f"HIGH RISK PROFESSIONAL EVENT DETECTED\n"
            f"Event Type: {event.event_type.value}\n"
            f"Risk Level: {event.risk_level.value}\n"
            f"Attorney: {event.attorney_email} (Bar: {event.attorney_bar_number})\n"
            f"Time: {event.timestamp}\n"
            f"Description: {event.description}\n"
            f"Requires Review: {event.requires_review}"
        )
        
        # Log critical alert
        self.logger.critical(f"PROFESSIONAL_RISK_ALERT - {alert_message}")
        
        # In production, this would send notifications to compliance officers
        print(f"[PROFESSIONAL RISK ALERT] {alert_message}")
    
    def get_attorney_compliance_report(
        self, 
        attorney_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate comprehensive attorney compliance report"""
        
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        # Get all events for attorney in date range
        cursor.execute('''
            SELECT * FROM professional_audit_events
            WHERE attorney_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        ''', (attorney_id, start_date.isoformat(), end_date.isoformat()))
        
        events = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        # Get attorney metrics summary
        cursor.execute('''
            SELECT 
                SUM(total_events) as total_events,
                SUM(high_risk_events) as high_risk_events,
                SUM(regulatory_events) as regulatory_events,
                SUM(billable_hours) as total_billable_hours,
                SUM(pro_bono_hours) as total_pro_bono_hours,
                SUM(client_interactions) as total_client_interactions,
                AVG(compliance_score) as avg_compliance_score
            FROM attorney_metrics
            WHERE attorney_id = ? AND metric_date BETWEEN ? AND ?
        ''', (attorney_id, start_date.date().isoformat(), end_date.date().isoformat()))
        
        metrics = cursor.fetchone()
        
        conn.close()
        
        # Process events by type
        event_summary = {}
        risk_summary = {}
        practice_area_summary = {}
        
        for event_data in events:
            event_dict = dict(zip(columns, event_data))
            event_type = event_dict['event_type']
            risk_level = event_dict['risk_level']
            practice_area = event_dict['practice_area'] or 'general'
            
            event_summary[event_type] = event_summary.get(event_type, 0) + 1
            risk_summary[risk_level] = risk_summary.get(risk_level, 0) + 1
            practice_area_summary[practice_area] = practice_area_summary.get(practice_area, 0) + 1
        
        return {
            "attorney_id": attorney_id,
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics_summary": {
                "total_events": metrics[0] or 0,
                "high_risk_events": metrics[1] or 0,
                "regulatory_events": metrics[2] or 0,
                "total_billable_hours": metrics[3] or 0.0,
                "total_pro_bono_hours": metrics[4] or 0.0,
                "total_client_interactions": metrics[5] or 0,
                "average_compliance_score": metrics[6] or 100.0
            },
            "event_type_summary": event_summary,
            "risk_level_summary": risk_summary,
            "practice_area_summary": practice_area_summary,
            "events_requiring_review": len([e for e in events if dict(zip(columns, e))['requires_review']]),
            "events_with_privileged_info": len([e for e in events if dict(zip(columns, e))['contains_privileged_info']]),
            "total_events_in_period": len(events)
        }

# Global professional audit system instance
professional_audit = ProfessionalAuditSystem()