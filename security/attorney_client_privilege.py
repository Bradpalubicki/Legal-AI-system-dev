#!/usr/bin/env python3
"""
Attorney-Client Privilege Protection System
Enterprise-grade protection for privileged attorney-client communications
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import hashlib
import re
from pathlib import Path
import secrets

class PrivilegeLevel(Enum):
    """Attorney-client privilege levels"""
    PUBLIC = "public"
    CONFIDENTIAL = "confidential"
    ATTORNEY_CLIENT_PRIVILEGED = "attorney_client_privileged"
    WORK_PRODUCT = "work_product"
    JOINTLY_PRIVILEGED = "jointly_privileged"
    CLASSIFIED = "classified"

class CommunicationType(Enum):
    """Types of attorney-client communications"""
    EMAIL = "email"
    DOCUMENT = "document"
    PHONE_CALL = "phone_call"
    VIDEO_CONFERENCE = "video_conference"
    IN_PERSON_MEETING = "in_person_meeting"
    INSTANT_MESSAGE = "instant_message"
    VOICEMAIL = "voicemail"
    TEXT_MESSAGE = "text_message"
    LEGAL_BRIEF = "legal_brief"
    CONTRACT = "contract"

class PrivilegeWaiverType(Enum):
    """Types of privilege waivers"""
    EXPLICIT_WAIVER = "explicit_waiver"
    INADVERTENT_DISCLOSURE = "inadvertent_disclosure"
    PARTIAL_WAIVER = "partial_waiver"
    JOINT_CLIENT_WAIVER = "joint_client_waiver"
    COURT_ORDERED = "court_ordered"
    ETHICAL_DISCLOSURE = "ethical_disclosure"

@dataclass
class PrivilegedCommunication:
    """Represents a privileged attorney-client communication"""
    communication_id: str
    client_id: str
    attorney_id: str
    case_id: Optional[str]
    communication_type: CommunicationType
    privilege_level: PrivilegeLevel
    subject: str
    participants: List[str]  # All parties involved
    attorney_participants: List[str]
    client_participants: List[str]
    third_party_participants: List[str]
    communication_date: datetime
    content_hash: str  # For integrity verification
    is_privileged: bool
    privilege_reasoning: str
    waiver_status: Optional[PrivilegeWaiverType]
    waiver_date: Optional[datetime]
    waiver_authorized_by: Optional[str]
    retention_period_years: int
    destruction_date: Optional[datetime]
    access_log: List[Dict[str, Any]]
    created_at: datetime
    created_by: str

@dataclass
class EthicalWall:
    """Represents an ethical wall/Chinese wall for conflicts"""
    wall_id: str
    client_a_id: str
    client_b_id: str
    matter_description: str
    conflicted_attorneys: List[str]
    walled_attorneys: List[str]
    exempted_attorneys: List[str]  # Managing partners, etc.
    wall_established_date: datetime
    wall_established_by: str
    wall_reason: str
    is_active: bool
    periodic_review_date: Optional[datetime]
    last_reviewed_date: Optional[datetime]
    reviewed_by: Optional[str]

class AttorneyClientPrivilegeManager:
    """Manages attorney-client privilege protection and ethical walls"""
    
    def __init__(self, db_path: str = "privilege_protection.db"):
        self.db_path = db_path
        self.logger = self._setup_logger()
        self._init_database()
        
        # Privilege indicators - words/phrases that suggest privileged communications
        self.privilege_indicators = {
            "legal_advice": [
                "legal advice", "attorney advice", "counsel recommends", "legal opinion",
                "attorney-client", "confidential", "privileged", "legal strategy",
                "litigation strategy", "settlement strategy", "legal analysis"
            ],
            "client_confidences": [
                "client told me", "client informed", "client disclosed", "client shared",
                "in confidence", "confidentially", "between us", "off the record"
            ],
            "work_product": [
                "litigation strategy", "trial preparation", "case analysis", "legal research",
                "witness preparation", "expert analysis", "settlement analysis",
                "discovery strategy", "cross-examination", "opening statement"
            ],
            "settlement_discussions": [
                "settlement", "negotiate", "offer", "demand", "compromise", "resolution",
                "mediation", "arbitration", "plea", "agreement"
            ]
        }
        
        # Third parties that may break privilege
        self.privilege_breaking_parties = {
            "opposing_counsel", "opposing_party", "court", "judge", "jury",
            "prosecutor", "government_agency", "regulatory_body", "media",
            "public", "unrelated_third_party"
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup privilege protection logger"""
        logger = logging.getLogger('privilege_protection')
        logger.setLevel(logging.INFO)
        
        Path('logs').mkdir(exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            'logs/privilege_protection.log',
            maxBytes=50*1024*1024,
            backupCount=100,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - PRIVILEGE - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize privilege protection database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Privileged communications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS privileged_communications (
                communication_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                attorney_id TEXT NOT NULL,
                case_id TEXT,
                communication_type TEXT NOT NULL,
                privilege_level TEXT NOT NULL,
                subject TEXT NOT NULL,
                participants TEXT NOT NULL,
                attorney_participants TEXT NOT NULL,
                client_participants TEXT NOT NULL,
                third_party_participants TEXT NOT NULL,
                communication_date TIMESTAMP NOT NULL,
                content_hash TEXT NOT NULL,
                is_privileged BOOLEAN NOT NULL,
                privilege_reasoning TEXT NOT NULL,
                waiver_status TEXT,
                waiver_date TIMESTAMP,
                waiver_authorized_by TEXT,
                retention_period_years INTEGER NOT NULL,
                destruction_date TIMESTAMP,
                access_log TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                created_by TEXT NOT NULL
            )
        ''')
        
        # Ethical walls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ethical_walls (
                wall_id TEXT PRIMARY KEY,
                client_a_id TEXT NOT NULL,
                client_b_id TEXT NOT NULL,
                matter_description TEXT NOT NULL,
                conflicted_attorneys TEXT NOT NULL,
                walled_attorneys TEXT NOT NULL,
                exempted_attorneys TEXT NOT NULL,
                wall_established_date TIMESTAMP NOT NULL,
                wall_established_by TEXT NOT NULL,
                wall_reason TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                periodic_review_date TIMESTAMP,
                last_reviewed_date TIMESTAMP,
                reviewed_by TEXT
            )
        ''')
        
        # Privilege waivers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS privilege_waivers (
                waiver_id TEXT PRIMARY KEY,
                communication_id TEXT NOT NULL,
                waiver_type TEXT NOT NULL,
                waiver_date TIMESTAMP NOT NULL,
                authorized_by TEXT NOT NULL,
                recipient TEXT,
                scope_of_waiver TEXT NOT NULL,
                waiver_document TEXT,
                is_revocable BOOLEAN DEFAULT TRUE,
                revocation_date TIMESTAMP,
                revoked_by TEXT,
                court_ordered BOOLEAN DEFAULT FALSE,
                court_order_reference TEXT,
                FOREIGN KEY (communication_id) REFERENCES privileged_communications (communication_id)
            )
        ''')
        
        # Access control table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS privilege_access_control (
                access_id TEXT PRIMARY KEY,
                communication_id TEXT NOT NULL,
                attorney_id TEXT NOT NULL,
                access_level TEXT NOT NULL,
                granted_by TEXT NOT NULL,
                granted_date TIMESTAMP NOT NULL,
                access_reason TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                revoked_date TIMESTAMP,
                revoked_by TEXT,
                FOREIGN KEY (communication_id) REFERENCES privileged_communications (communication_id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_privilege_client ON privileged_communications (client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_privilege_attorney ON privileged_communications (attorney_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_privilege_case ON privileged_communications (case_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_privilege_level ON privileged_communications (privilege_level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ethical_walls_active ON ethical_walls (is_active)')
        
        conn.commit()
        conn.close()
    
    def analyze_privilege(
        self,
        content: str,
        participants: List[str],
        attorney_participants: List[str],
        client_participants: List[str],
        communication_type: CommunicationType
    ) -> Tuple[bool, PrivilegeLevel, str, float]:
        """Analyze content for attorney-client privilege"""
        
        confidence_score = 0.0
        privilege_reasons = []
        
        # Check for attorney-client relationship
        has_attorney = len(attorney_participants) > 0
        has_client = len(client_participants) > 0
        
        if not (has_attorney and has_client):
            return False, PrivilegeLevel.PUBLIC, "No attorney-client relationship", 0.0
        
        # Check for third parties that break privilege
        third_parties = [p for p in participants if p not in attorney_participants + client_participants]
        privilege_breaking_parties = [p for p in third_parties if any(
            bp in p.lower() for bp in self.privilege_breaking_parties
        )]
        
        if privilege_breaking_parties:
            return False, PrivilegeLevel.CONFIDENTIAL, f"Third parties present: {privilege_breaking_parties}", 0.2
        
        # Content analysis for privilege indicators
        content_lower = content.lower()
        
        # Legal advice indicators
        legal_advice_matches = sum(1 for indicator in self.privilege_indicators["legal_advice"] 
                                 if indicator in content_lower)
        if legal_advice_matches > 0:
            confidence_score += 0.4
            privilege_reasons.append(f"Legal advice indicators: {legal_advice_matches}")
        
        # Client confidences
        confidence_matches = sum(1 for indicator in self.privilege_indicators["client_confidences"]
                               if indicator in content_lower)
        if confidence_matches > 0:
            confidence_score += 0.3
            privilege_reasons.append(f"Client confidence indicators: {confidence_matches}")
        
        # Work product indicators
        work_product_matches = sum(1 for indicator in self.privilege_indicators["work_product"]
                                 if indicator in content_lower)
        if work_product_matches > 0:
            confidence_score += 0.35
            privilege_reasons.append(f"Work product indicators: {work_product_matches}")
        
        # Settlement discussions
        settlement_matches = sum(1 for indicator in self.privilege_indicators["settlement_discussions"]
                               if indicator in content_lower)
        if settlement_matches > 0:
            confidence_score += 0.25
            privilege_reasons.append(f"Settlement discussion indicators: {settlement_matches}")
        
        # Communication type bonus
        privileged_communication_types = {
            CommunicationType.IN_PERSON_MEETING: 0.1,
            CommunicationType.VIDEO_CONFERENCE: 0.1,
            CommunicationType.PHONE_CALL: 0.1,
            CommunicationType.EMAIL: 0.05,
            CommunicationType.DOCUMENT: 0.15
        }
        
        type_bonus = privileged_communication_types.get(communication_type, 0)
        confidence_score += type_bonus
        
        # Determine privilege level
        is_privileged = confidence_score >= 0.3
        
        if confidence_score >= 0.8:
            privilege_level = PrivilegeLevel.ATTORNEY_CLIENT_PRIVILEGED
        elif confidence_score >= 0.6 and work_product_matches > 0:
            privilege_level = PrivilegeLevel.WORK_PRODUCT
        elif confidence_score >= 0.4:
            privilege_level = PrivilegeLevel.CONFIDENTIAL
        else:
            privilege_level = PrivilegeLevel.PUBLIC
        
        reasoning = "; ".join(privilege_reasons) if privilege_reasons else "No privilege indicators found"
        
        return is_privileged, privilege_level, reasoning, confidence_score
    
    def register_privileged_communication(
        self,
        client_id: str,
        attorney_id: str,
        communication_type: CommunicationType,
        subject: str,
        content: str,
        participants: List[str],
        attorney_participants: List[str],
        client_participants: List[str],
        case_id: Optional[str] = None,
        created_by: str = "system"
    ) -> str:
        """Register a potentially privileged communication"""
        
        communication_id = secrets.token_hex(16)
        
        # Analyze privilege
        is_privileged, privilege_level, reasoning, confidence = self.analyze_privilege(
            content, participants, attorney_participants, client_participants, communication_type
        )
        
        # Calculate content hash for integrity
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Third party participants
        third_party_participants = [p for p in participants 
                                   if p not in attorney_participants + client_participants]
        
        # Set retention period based on privilege level
        retention_periods = {
            PrivilegeLevel.ATTORNEY_CLIENT_PRIVILEGED: 20,
            PrivilegeLevel.WORK_PRODUCT: 10,
            PrivilegeLevel.CONFIDENTIAL: 7,
            PrivilegeLevel.PUBLIC: 3
        }
        retention_period = retention_periods[privilege_level]
        destruction_date = datetime.now() + timedelta(days=365 * retention_period)
        
        communication = PrivilegedCommunication(
            communication_id=communication_id,
            client_id=client_id,
            attorney_id=attorney_id,
            case_id=case_id,
            communication_type=communication_type,
            privilege_level=privilege_level,
            subject=subject,
            participants=participants,
            attorney_participants=attorney_participants,
            client_participants=client_participants,
            third_party_participants=third_party_participants,
            communication_date=datetime.now(),
            content_hash=content_hash,
            is_privileged=is_privileged,
            privilege_reasoning=reasoning,
            waiver_status=None,
            waiver_date=None,
            waiver_authorized_by=None,
            retention_period_years=retention_period,
            destruction_date=destruction_date,
            access_log=[],
            created_at=datetime.now(),
            created_by=created_by
        )
        
        # Store in database
        self._store_privileged_communication(communication)
        
        # Log privilege registration
        self.logger.info(
            f"Privileged communication registered: {communication_id} - "
            f"Client: {client_id} - Attorney: {attorney_id} - "
            f"Privilege: {privilege_level.value} - Confidence: {confidence:.2f}"
        )
        
        return communication_id
    
    def _store_privileged_communication(self, comm: PrivilegedCommunication):
        """Store privileged communication in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO privileged_communications (
                    communication_id, client_id, attorney_id, case_id, communication_type,
                    privilege_level, subject, participants, attorney_participants,
                    client_participants, third_party_participants, communication_date,
                    content_hash, is_privileged, privilege_reasoning, waiver_status,
                    waiver_date, waiver_authorized_by, retention_period_years,
                    destruction_date, access_log, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                comm.communication_id, comm.client_id, comm.attorney_id, comm.case_id,
                comm.communication_type.value, comm.privilege_level.value, comm.subject,
                json.dumps(comm.participants), json.dumps(comm.attorney_participants),
                json.dumps(comm.client_participants), json.dumps(comm.third_party_participants),
                comm.communication_date.isoformat(), comm.content_hash, comm.is_privileged,
                comm.privilege_reasoning, comm.waiver_status.value if comm.waiver_status else None,
                comm.waiver_date.isoformat() if comm.waiver_date else None,
                comm.waiver_authorized_by, comm.retention_period_years,
                comm.destruction_date.isoformat() if comm.destruction_date else None,
                json.dumps(comm.access_log), comm.created_at.isoformat(), comm.created_by
            ))
            
            conn.commit()
        finally:
            conn.close()
    
    def establish_ethical_wall(
        self,
        client_a_id: str,
        client_b_id: str,
        matter_description: str,
        conflicted_attorneys: List[str],
        walled_attorneys: List[str],
        established_by: str,
        wall_reason: str,
        exempted_attorneys: Optional[List[str]] = None
    ) -> str:
        """Establish an ethical wall for conflicted matters"""
        
        wall_id = secrets.token_hex(16)
        
        if exempted_attorneys is None:
            exempted_attorneys = []
        
        wall = EthicalWall(
            wall_id=wall_id,
            client_a_id=client_a_id,
            client_b_id=client_b_id,
            matter_description=matter_description,
            conflicted_attorneys=conflicted_attorneys,
            walled_attorneys=walled_attorneys,
            exempted_attorneys=exempted_attorneys,
            wall_established_date=datetime.now(),
            wall_established_by=established_by,
            wall_reason=wall_reason,
            is_active=True,
            periodic_review_date=datetime.now() + timedelta(days=90),  # Review every 90 days
            last_reviewed_date=None,
            reviewed_by=None
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO ethical_walls (
                    wall_id, client_a_id, client_b_id, matter_description,
                    conflicted_attorneys, walled_attorneys, exempted_attorneys,
                    wall_established_date, wall_established_by, wall_reason,
                    is_active, periodic_review_date, last_reviewed_date, reviewed_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                wall.wall_id, wall.client_a_id, wall.client_b_id, wall.matter_description,
                json.dumps(wall.conflicted_attorneys), json.dumps(wall.walled_attorneys),
                json.dumps(wall.exempted_attorneys), wall.wall_established_date.isoformat(),
                wall.wall_established_by, wall.wall_reason, wall.is_active,
                wall.periodic_review_date.isoformat() if wall.periodic_review_date else None,
                wall.last_reviewed_date.isoformat() if wall.last_reviewed_date else None,
                wall.reviewed_by
            ))
            
            conn.commit()
            
            self.logger.info(
                f"Ethical wall established: {wall_id} - "
                f"Clients: {client_a_id}, {client_b_id} - "
                f"Walled attorneys: {len(walled_attorneys)}"
            )
            
            return wall_id
            
        finally:
            conn.close()
    
    def check_ethical_wall_violation(
        self,
        attorney_id: str,
        client_id: str,
        case_id: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """Check if attorney access would violate an ethical wall"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for active ethical walls
        cursor.execute('''
            SELECT wall_id, client_a_id, client_b_id, walled_attorneys, exempted_attorneys
            FROM ethical_walls
            WHERE is_active = TRUE
            AND (client_a_id = ? OR client_b_id = ?)
        ''', (client_id, client_id))
        
        walls = cursor.fetchall()
        violations = []
        
        for wall_data in walls:
            wall_id, client_a_id, client_b_id, walled_attorneys_json, exempted_attorneys_json = wall_data
            
            walled_attorneys = json.loads(walled_attorneys_json)
            exempted_attorneys = json.loads(exempted_attorneys_json)
            
            # Check if attorney is exempted
            if attorney_id in exempted_attorneys:
                continue
            
            # Check if attorney is walled from this client
            if attorney_id in walled_attorneys:
                violations.append(wall_id)
        
        conn.close()
        
        return len(violations) > 0, violations
    
    def grant_privilege_access(
        self,
        communication_id: str,
        attorney_id: str,
        access_level: str,
        granted_by: str,
        access_reason: str
    ) -> bool:
        """Grant access to privileged communication"""
        
        # Check for ethical wall violations first
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT client_id FROM privileged_communications WHERE communication_id = ?',
                      (communication_id,))
        result = cursor.fetchone()
        
        if not result:
            return False
        
        client_id = result[0]
        is_violation, violated_walls = self.check_ethical_wall_violation(attorney_id, client_id)
        
        if is_violation:
            self.logger.warning(
                f"Privilege access denied due to ethical wall violation: "
                f"Attorney {attorney_id} - Client {client_id} - Walls {violated_walls}"
            )
            return False
        
        # Grant access
        access_id = secrets.token_hex(16)
        
        cursor.execute('''
            INSERT INTO privilege_access_control (
                access_id, communication_id, attorney_id, access_level,
                granted_by, granted_date, access_reason, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            access_id, communication_id, attorney_id, access_level,
            granted_by, datetime.now().isoformat(), access_reason, True
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.info(
            f"Privilege access granted: {access_id} - "
            f"Attorney: {attorney_id} - Communication: {communication_id}"
        )
        
        return True
    
    def get_privilege_summary(self, attorney_id: str, days: int = 30) -> Dict[str, Any]:
        """Get privilege protection summary for attorney"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Get privilege statistics
        cursor.execute('''
            SELECT 
                privilege_level,
                COUNT(*) as count,
                communication_type
            FROM privileged_communications
            WHERE attorney_id = ? AND created_at >= ?
            GROUP BY privilege_level, communication_type
        ''', (attorney_id, start_date.isoformat()))
        
        stats = cursor.fetchall()
        
        # Get ethical walls affecting this attorney
        cursor.execute('''
            SELECT wall_id, client_a_id, client_b_id, matter_description
            FROM ethical_walls
            WHERE is_active = TRUE
            AND (? = ANY(json_each.value) OR ? = ANY(json_each.value))
        ''', (attorney_id, attorney_id))
        
        walls = cursor.fetchall()
        
        conn.close()
        
        return {
            "attorney_id": attorney_id,
            "reporting_period_days": days,
            "privilege_statistics": [
                {
                    "privilege_level": stat[0],
                    "count": stat[1],
                    "communication_type": stat[2]
                }
                for stat in stats
            ],
            "active_ethical_walls": len(walls),
            "ethical_walls": [
                {
                    "wall_id": wall[0],
                    "client_a": wall[1],
                    "client_b": wall[2],
                    "matter": wall[3]
                }
                for wall in walls
            ],
            "total_privileged_communications": sum(stat[1] for stat in stats)
        }

# Global privilege manager instance
privilege_manager = AttorneyClientPrivilegeManager()