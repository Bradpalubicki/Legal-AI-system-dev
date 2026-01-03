#!/usr/bin/env python3
"""
Attorney-Client Privilege Protection System
SOC 2 compliant privilege screening and protection with ethical walls
"""

import os
import json
import hashlib
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PrivilegeLevel(Enum):
    """Privilege levels based on legal protection"""
    PUBLIC = "public"
    CONFIDENTIAL = "confidential"
    ATTORNEY_CLIENT = "attorney_client"
    ATTORNEY_WORK_PRODUCT = "attorney_work_product"
    JOINT_CLIENT = "joint_client"
    COMMON_INTEREST = "common_interest"

class ConflictType(Enum):
    """Types of conflicts of interest"""
    DIRECT_ADVERSE = "direct_adverse"
    POSITIONAL_CONFLICT = "positional_conflict"
    FORMER_CLIENT = "former_client"
    IMPUTED_CONFLICT = "imputed_conflict"
    PERSONAL_INTEREST = "personal_interest"
    THIRD_PARTY_INTEREST = "third_party_interest"

class EthicalWallStatus(Enum):
    """Status of ethical walls"""
    ACTIVE = "active"
    PENDING = "pending"
    BREACHED = "breached"
    EXPIRED = "expired"
    WAIVED = "waived"

@dataclass
class ClientRelationship:
    """Client relationship record"""
    relationship_id: str
    client_id: str
    client_name: str
    attorney_id: str
    attorney_bar_number: str
    
    # Relationship details
    start_date: datetime
    end_date: Optional[datetime]
    relationship_type: str  # "current", "former", "prospective"
    matter_description: str
    
    # Privilege information
    privilege_level: PrivilegeLevel
    joint_clients: List[str] = None
    common_interest_parties: List[str] = None
    
    # Conflict screening
    conflicts_cleared: bool = False
    clearance_date: Optional[datetime] = None
    cleared_by: Optional[str] = None
    
    def __post_init__(self):
        if self.joint_clients is None:
            self.joint_clients = []
        if self.common_interest_parties is None:
            self.common_interest_parties = []

@dataclass
class ConflictRecord:
    """Conflict of interest record"""
    conflict_id: str
    client_a: str
    client_b: str
    attorney_id: str
    conflict_type: ConflictType
    
    # Conflict details
    matter_description: str
    identified_date: datetime
    severity: str  # "low", "medium", "high", "disqualifying"
    
    # Resolution
    status: str  # "identified", "waived", "resolved", "disqualifying"
    resolution_notes: Optional[str] = None
    waiver_obtained: bool = False
    
    # Ethical wall
    ethical_wall_required: bool = False
    ethical_wall_id: Optional[str] = None

@dataclass
class EthicalWall:
    """Ethical wall (Chinese Wall) implementation"""
    wall_id: str
    matter_name: str
    client_id: str
    
    # Wall configuration
    screened_attorneys: List[str]
    permitted_attorneys: List[str]
    sensitive_documents: List[str]
    
    # Dates
    effective_date: datetime
    expiration_date: Optional[datetime]
    status: EthicalWallStatus
    
    # Monitoring
    breach_attempts: List[Dict[str, Any]] = None
    last_reviewed: Optional[datetime] = None
    
    def __post_init__(self):
        if self.breach_attempts is None:
            self.breach_attempts = []

class PrivilegeScreener:
    """Automated privilege and confidentiality screening"""
    
    def __init__(self):
        # Privilege indicators - terms that suggest privileged content
        self.privilege_indicators = {
            PrivilegeLevel.ATTORNEY_CLIENT: [
                "attorney-client", "legal advice", "confidential", "privileged",
                "pursuant to representation", "legal counsel", "law firm",
                "attorney consultation", "legal opinion", "counsel advised",
                "attorney reviewed", "legal analysis", "privileged and confidential"
            ],
            PrivilegeLevel.ATTORNEY_WORK_PRODUCT: [
                "work product", "litigation strategy", "case strategy", "trial preparation",
                "witness interview", "internal analysis", "attorney notes",
                "litigation plan", "discovery strategy", "settlement strategy",
                "legal research", "case assessment", "attorney memorandum"
            ],
            PrivilegeLevel.JOINT_CLIENT: [
                "joint client", "common client", "co-client", "joint representation",
                "multiple clients", "shared representation"
            ],
            PrivilegeLevel.COMMON_INTEREST: [
                "common interest", "joint defense", "shared interest",
                "common interest privilege", "allied parties"
            ]
        }
        
        # Confidentiality markers
        self.confidentiality_markers = [
            "confidential", "proprietary", "trade secret", "non-disclosure",
            "attorney eyes only", "restricted access", "privileged", "sensitive",
            "internal use only", "not for distribution"
        ]
    
    def analyze_document_privilege(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze document for privilege level and protection requirements"""
        
        content_lower = content.lower()
        detected_privileges = []
        confidence_scores = {}
        
        # Check for privilege indicators
        for privilege_level, indicators in self.privilege_indicators.items():
            matches = sum(1 for indicator in indicators if indicator in content_lower)
            if matches > 0:
                detected_privileges.append(privilege_level)
                confidence_scores[privilege_level.value] = min(matches / len(indicators), 1.0)
        
        # Check confidentiality markers
        confidentiality_score = sum(1 for marker in self.confidentiality_markers if marker in content_lower)
        confidentiality_score = min(confidentiality_score / len(self.confidentiality_markers), 1.0)
        
        # Determine final privilege level
        if PrivilegeLevel.ATTORNEY_CLIENT in detected_privileges:
            final_privilege = PrivilegeLevel.ATTORNEY_CLIENT
        elif PrivilegeLevel.ATTORNEY_WORK_PRODUCT in detected_privileges:
            final_privilege = PrivilegeLevel.ATTORNEY_WORK_PRODUCT
        elif PrivilegeLevel.JOINT_CLIENT in detected_privileges:
            final_privilege = PrivilegeLevel.JOINT_CLIENT
        elif PrivilegeLevel.COMMON_INTEREST in detected_privileges:
            final_privilege = PrivilegeLevel.COMMON_INTEREST
        elif confidentiality_score > 0.3:
            final_privilege = PrivilegeLevel.CONFIDENTIAL
        else:
            final_privilege = PrivilegeLevel.PUBLIC
        
        # Additional analysis from metadata
        author_analysis = self._analyze_author_privilege(metadata.get('author', ''))
        recipient_analysis = self._analyze_recipients_privilege(metadata.get('recipients', []))
        
        return {
            "privilege_level": final_privilege.value,
            "confidence_score": confidence_scores.get(final_privilege.value, 0.0),
            "detected_privileges": [p.value for p in detected_privileges],
            "confidentiality_score": confidentiality_score,
            "author_analysis": author_analysis,
            "recipient_analysis": recipient_analysis,
            "protection_required": final_privilege in [
                PrivilegeLevel.ATTORNEY_CLIENT, 
                PrivilegeLevel.ATTORNEY_WORK_PRODUCT
            ],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def _analyze_author_privilege(self, author: str) -> Dict[str, Any]:
        """Analyze author information for privilege implications"""
        
        author_lower = author.lower()
        attorney_indicators = ["esq", "j.d.", "attorney", "counsel", "lawyer", "bar"]
        
        is_likely_attorney = any(indicator in author_lower for indicator in attorney_indicators)
        
        return {
            "is_likely_attorney": is_likely_attorney,
            "privilege_enhanced": is_likely_attorney,
            "analysis_confidence": 0.8 if is_likely_attorney else 0.2
        }
    
    def _analyze_recipients_privilege(self, recipients: List[str]) -> Dict[str, Any]:
        """Analyze recipient list for privilege implications"""
        
        attorney_count = 0
        client_indicators = ["client", "customer"]
        
        for recipient in recipients:
            recipient_lower = recipient.lower()
            if any(indicator in recipient_lower for indicator in ["esq", "attorney", "counsel"]):
                attorney_count += 1
        
        attorney_percentage = attorney_count / len(recipients) if recipients else 0
        
        return {
            "total_recipients": len(recipients),
            "attorney_recipients": attorney_count,
            "attorney_percentage": attorney_percentage,
            "privilege_likely": attorney_percentage > 0.5,
            "broad_distribution_risk": len(recipients) > 10
        }

class AttorneyClientPrivilegeManager:
    """Comprehensive attorney-client privilege protection system"""
    
    def __init__(self, db_path: str = "privilege/privilege.db"):
        self.db_path = db_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize components
        self.privilege_screener = PrivilegeScreener()
        
        # Initialize database
        self._init_database()
        
        # Active relationships and walls
        self.client_relationships: Dict[str, ClientRelationship] = {}
        self.ethical_walls: Dict[str, EthicalWall] = {}
        self.conflict_records: Dict[str, ConflictRecord] = {}
        
        # Load existing data
        self._load_privilege_data()
    
    def _init_database(self):
        """Initialize privilege protection database"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Client relationships table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS client_relationships (
                    relationship_id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    client_name TEXT NOT NULL,
                    attorney_id TEXT NOT NULL,
                    attorney_bar_number TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    relationship_type TEXT NOT NULL,
                    matter_description TEXT NOT NULL,
                    privilege_level TEXT NOT NULL,
                    joint_clients TEXT,
                    common_interest_parties TEXT,
                    conflicts_cleared BOOLEAN DEFAULT 0,
                    clearance_date TEXT,
                    cleared_by TEXT
                )
            ''')
            
            # Conflict records table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS conflict_records (
                    conflict_id TEXT PRIMARY KEY,
                    client_a TEXT NOT NULL,
                    client_b TEXT NOT NULL,
                    attorney_id TEXT NOT NULL,
                    conflict_type TEXT NOT NULL,
                    matter_description TEXT NOT NULL,
                    identified_date TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    resolution_notes TEXT,
                    waiver_obtained BOOLEAN DEFAULT 0,
                    ethical_wall_required BOOLEAN DEFAULT 0,
                    ethical_wall_id TEXT
                )
            ''')
            
            # Ethical walls table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ethical_walls (
                    wall_id TEXT PRIMARY KEY,
                    matter_name TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    screened_attorneys TEXT NOT NULL,
                    permitted_attorneys TEXT NOT NULL,
                    sensitive_documents TEXT NOT NULL,
                    effective_date TEXT NOT NULL,
                    expiration_date TEXT,
                    status TEXT NOT NULL,
                    breach_attempts TEXT,
                    last_reviewed TEXT
                )
            ''')
            
            # Privilege screenings table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS privilege_screenings (
                    screening_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    client_id TEXT,
                    attorney_id TEXT,
                    screening_date TEXT NOT NULL,
                    privilege_level TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    detected_privileges TEXT,
                    confidentiality_score REAL NOT NULL,
                    protection_required BOOLEAN DEFAULT 0,
                    manual_override BOOLEAN DEFAULT 0,
                    override_reason TEXT,
                    screened_by TEXT
                )
            ''')
            
            # Access violations table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS access_violations (
                    violation_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    attempted_action TEXT NOT NULL,
                    violation_date TEXT NOT NULL,
                    blocked BOOLEAN DEFAULT 1,
                    severity TEXT NOT NULL,
                    investigation_status TEXT DEFAULT 'pending',
                    resolution_notes TEXT
                )
            ''')
            
            # Create indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_client_attorney ON client_relationships(client_id, attorney_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_conflict_parties ON conflict_records(client_a, client_b)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_ethical_wall_client ON ethical_walls(client_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_screening_privilege ON privilege_screenings(privilege_level)')
    
    def _load_privilege_data(self):
        """Load existing privilege data from database"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Load client relationships
            relationships = conn.execute("SELECT * FROM client_relationships").fetchall()
            for row in relationships:
                rel = ClientRelationship(
                    relationship_id=row[0],
                    client_id=row[1],
                    client_name=row[2],
                    attorney_id=row[3],
                    attorney_bar_number=row[4],
                    start_date=datetime.fromisoformat(row[5]),
                    end_date=datetime.fromisoformat(row[6]) if row[6] else None,
                    relationship_type=row[7],
                    matter_description=row[8],
                    privilege_level=PrivilegeLevel(row[9]),
                    joint_clients=json.loads(row[10]) if row[10] else [],
                    common_interest_parties=json.loads(row[11]) if row[11] else [],
                    conflicts_cleared=bool(row[12]),
                    clearance_date=datetime.fromisoformat(row[13]) if row[13] else None,
                    cleared_by=row[14]
                )
                self.client_relationships[rel.relationship_id] = rel
    
    def establish_attorney_client_relationship(self, client_id: str, client_name: str,
                                             attorney_id: str, attorney_bar_number: str,
                                             matter_description: str, 
                                             privilege_level: PrivilegeLevel = PrivilegeLevel.ATTORNEY_CLIENT) -> str:
        """Establish new attorney-client relationship with conflict checking"""
        
        # Generate relationship ID
        relationship_id = hashlib.sha256(
            f"{client_id}|{attorney_id}|{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Perform conflict check
        conflicts = self.check_conflicts_of_interest(attorney_id, client_id, matter_description)
        
        if conflicts["has_conflicts"] and conflicts["severity"] == "disqualifying":
            logger.error(f"Disqualifying conflict prevents relationship establishment: {conflicts}")
            raise ValueError(f"Disqualifying conflict prevents representation of {client_name}")
        
        # Create relationship
        relationship = ClientRelationship(
            relationship_id=relationship_id,
            client_id=client_id,
            client_name=client_name,
            attorney_id=attorney_id,
            attorney_bar_number=attorney_bar_number,
            start_date=datetime.utcnow(),
            end_date=None,
            relationship_type="current",
            matter_description=matter_description,
            privilege_level=privilege_level,
            conflicts_cleared=not conflicts["has_conflicts"]
        )
        
        # Handle conflicts if any
        if conflicts["has_conflicts"]:
            # Create ethical wall if required
            if conflicts["requires_ethical_wall"]:
                wall_id = self.create_ethical_wall(
                    matter_name=f"{client_name} - {matter_description}",
                    client_id=client_id,
                    screened_attorneys=[attorney_id],
                    sensitive_documents=[]
                )
                logger.info(f"Created ethical wall {wall_id} for relationship {relationship_id}")
        
        # Store relationship
        self._store_client_relationship(relationship)
        self.client_relationships[relationship_id] = relationship
        
        logger.info(f"Established attorney-client relationship {relationship_id} between {attorney_id} and {client_id}")
        return relationship_id
    
    def check_conflicts_of_interest(self, attorney_id: str, new_client_id: str, 
                                   matter_description: str) -> Dict[str, Any]:
        """Comprehensive conflict of interest checking"""
        
        conflicts_found = []
        max_severity = "none"
        requires_ethical_wall = False
        
        # Check against existing client relationships
        for relationship in self.client_relationships.values():
            if relationship.attorney_id == attorney_id:
                
                # Skip if same client
                if relationship.client_id == new_client_id:
                    continue
                
                # Analyze for conflicts
                conflict_analysis = self._analyze_potential_conflict(
                    relationship.matter_description, matter_description,
                    relationship.client_id, new_client_id
                )
                
                if conflict_analysis["has_conflict"]:
                    conflicts_found.append({
                        "existing_client": relationship.client_id,
                        "existing_matter": relationship.matter_description,
                        "conflict_type": conflict_analysis["conflict_type"],
                        "severity": conflict_analysis["severity"],
                        "waivable": conflict_analysis["waivable"]
                    })
                    
                    # Update max severity
                    severity_levels = {"low": 1, "medium": 2, "high": 3, "disqualifying": 4}
                    if severity_levels.get(conflict_analysis["severity"], 0) > severity_levels.get(max_severity, 0):
                        max_severity = conflict_analysis["severity"]
                    
                    # Check if ethical wall can resolve
                    if conflict_analysis["severity"] in ["medium", "high"] and conflict_analysis["waivable"]:
                        requires_ethical_wall = True
        
        # Check existing conflict records
        existing_conflicts = [
            record for record in self.conflict_records.values()
            if (record.attorney_id == attorney_id and 
                (record.client_a == new_client_id or record.client_b == new_client_id))
        ]
        
        return {
            "has_conflicts": len(conflicts_found) > 0,
            "conflict_count": len(conflicts_found),
            "conflicts": conflicts_found,
            "severity": max_severity,
            "requires_ethical_wall": requires_ethical_wall,
            "existing_conflict_records": len(existing_conflicts),
            "waiver_possible": max_severity != "disqualifying",
            "checked_date": datetime.utcnow().isoformat()
        }
    
    def _analyze_potential_conflict(self, existing_matter: str, new_matter: str,
                                  existing_client: str, new_client: str) -> Dict[str, Any]:
        """Analyze two matters for potential conflicts"""
        
        # Simple keyword-based conflict analysis
        # In production, this would use more sophisticated NLP and legal databases
        
        conflicting_keywords = [
            "v.", "vs.", "versus", "against", "dispute", "lawsuit", "litigation",
            "oppose", "adverse", "competitor", "competing"
        ]
        
        existing_lower = existing_matter.lower()
        new_lower = new_matter.lower()
        
        # Check for direct adverse indicators
        adverse_indicators = sum(1 for keyword in conflicting_keywords 
                               if keyword in existing_lower or keyword in new_lower)
        
        # Check for same industry/area conflicts
        industry_keywords = ["patent", "trademark", "merger", "acquisition", "contract", "employment"]
        shared_industries = sum(1 for keyword in industry_keywords 
                             if keyword in existing_lower and keyword in new_lower)
        
        # Determine conflict type and severity
        has_conflict = False
        conflict_type = ConflictType.POSITIONAL_CONFLICT
        severity = "low"
        waivable = True
        
        if adverse_indicators > 2:
            has_conflict = True
            conflict_type = ConflictType.DIRECT_ADVERSE
            severity = "disqualifying"
            waivable = False
        elif adverse_indicators > 0:
            has_conflict = True
            conflict_type = ConflictType.DIRECT_ADVERSE
            severity = "high"
            waivable = False
        elif shared_industries > 1:
            has_conflict = True
            conflict_type = ConflictType.POSITIONAL_CONFLICT
            severity = "medium"
            waivable = True
        
        return {
            "has_conflict": has_conflict,
            "conflict_type": conflict_type,
            "severity": severity,
            "waivable": waivable,
            "adverse_indicators": adverse_indicators,
            "shared_industries": shared_industries
        }
    
    def create_ethical_wall(self, matter_name: str, client_id: str,
                           screened_attorneys: List[str], sensitive_documents: List[str],
                           expiration_date: datetime = None) -> str:
        """Create ethical wall (Chinese Wall) for conflict resolution"""
        
        wall_id = hashlib.sha256(
            f"wall_{matter_name}_{client_id}_{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        wall = EthicalWall(
            wall_id=wall_id,
            matter_name=matter_name,
            client_id=client_id,
            screened_attorneys=screened_attorneys,
            permitted_attorneys=[],  # Will be populated as needed
            sensitive_documents=sensitive_documents,
            effective_date=datetime.utcnow(),
            expiration_date=expiration_date,
            status=EthicalWallStatus.ACTIVE
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO ethical_walls (
                    wall_id, matter_name, client_id, screened_attorneys,
                    permitted_attorneys, sensitive_documents, effective_date,
                    expiration_date, status, breach_attempts, last_reviewed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                wall.wall_id, wall.matter_name, wall.client_id,
                json.dumps(wall.screened_attorneys), json.dumps(wall.permitted_attorneys),
                json.dumps(wall.sensitive_documents), wall.effective_date.isoformat(),
                wall.expiration_date.isoformat() if wall.expiration_date else None,
                wall.status.value, json.dumps(wall.breach_attempts),
                wall.last_reviewed.isoformat() if wall.last_reviewed else None
            ))
        
        self.ethical_walls[wall_id] = wall
        logger.info(f"Created ethical wall {wall_id} for matter '{matter_name}'")
        return wall_id
    
    def check_ethical_wall_access(self, user_id: str, document_id: str, client_id: str) -> Dict[str, Any]:
        """Check if user access violates any ethical walls"""
        
        violations = []
        
        # Check all active ethical walls for this client
        for wall in self.ethical_walls.values():
            if (wall.client_id == client_id and 
                wall.status == EthicalWallStatus.ACTIVE and
                user_id in wall.screened_attorneys):
                
                # Check if document is sensitive
                if document_id in wall.sensitive_documents:
                    violation = {
                        "wall_id": wall.wall_id,
                        "matter_name": wall.matter_name,
                        "violation_type": "screened_attorney_access",
                        "severity": "high",
                        "blocked": True
                    }
                    violations.append(violation)
                    
                    # Log the violation attempt
                    self._log_access_violation(
                        user_id, document_id, client_id,
                        "ethical_wall_breach", "document_access",
                        "high", True
                    )
        
        return {
            "access_permitted": len(violations) == 0,
            "violations": violations,
            "ethical_walls_checked": len([w for w in self.ethical_walls.values() 
                                        if w.client_id == client_id]),
            "check_timestamp": datetime.utcnow().isoformat()
        }
    
    def screen_document_privilege(self, document_id: str, content: str, 
                                metadata: Dict[str, Any], client_id: str = None,
                                attorney_id: str = None) -> Dict[str, Any]:
        """Screen document for privilege level and protection requirements"""
        
        # Perform automated privilege analysis
        screening_result = self.privilege_screener.analyze_document_privilege(content, metadata)
        
        # Generate screening ID
        screening_id = hashlib.sha256(
            f"{document_id}|{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Store screening result
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO privilege_screenings (
                    screening_id, document_id, client_id, attorney_id,
                    screening_date, privilege_level, confidence_score,
                    detected_privileges, confidentiality_score, protection_required
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                screening_id, document_id, client_id, attorney_id,
                datetime.utcnow().isoformat(), screening_result["privilege_level"],
                screening_result["confidence_score"], 
                json.dumps(screening_result["detected_privileges"]),
                screening_result["confidentiality_score"],
                screening_result["protection_required"]
            ))
        
        logger.info(f"Screened document {document_id} - privilege level: {screening_result['privilege_level']}")
        return {
            "screening_id": screening_id,
            **screening_result
        }
    
    def _store_client_relationship(self, relationship: ClientRelationship):
        """Store client relationship in database"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO client_relationships (
                    relationship_id, client_id, client_name, attorney_id,
                    attorney_bar_number, start_date, end_date, relationship_type,
                    matter_description, privilege_level, joint_clients,
                    common_interest_parties, conflicts_cleared, clearance_date,
                    cleared_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                relationship.relationship_id, relationship.client_id, relationship.client_name,
                relationship.attorney_id, relationship.attorney_bar_number,
                relationship.start_date.isoformat(),
                relationship.end_date.isoformat() if relationship.end_date else None,
                relationship.relationship_type, relationship.matter_description,
                relationship.privilege_level.value, json.dumps(relationship.joint_clients),
                json.dumps(relationship.common_interest_parties),
                relationship.conflicts_cleared,
                relationship.clearance_date.isoformat() if relationship.clearance_date else None,
                relationship.cleared_by
            ))
    
    def _log_access_violation(self, user_id: str, document_id: str, client_id: str,
                            violation_type: str, attempted_action: str,
                            severity: str, blocked: bool):
        """Log access violation for investigation"""
        
        violation_id = hashlib.sha256(
            f"{user_id}|{document_id}|{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO access_violations (
                    violation_id, user_id, document_id, client_id,
                    violation_type, attempted_action, violation_date,
                    blocked, severity, investigation_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                violation_id, user_id, document_id, client_id,
                violation_type, attempted_action, datetime.utcnow().isoformat(),
                blocked, severity, "pending"
            ))
        
        logger.warning(f"Access violation logged: {violation_id} - {user_id} attempted {attempted_action} on {document_id}")
    
    def generate_privilege_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive privilege protection compliance report"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Relationship statistics
            total_relationships = conn.execute(
                "SELECT COUNT(*) FROM client_relationships"
            ).fetchone()[0]
            
            active_relationships = conn.execute(
                "SELECT COUNT(*) FROM client_relationships WHERE end_date IS NULL"
            ).fetchone()[0]
            
            # Conflict statistics
            total_conflicts = conn.execute("SELECT COUNT(*) FROM conflict_records").fetchone()[0]
            resolved_conflicts = conn.execute(
                "SELECT COUNT(*) FROM conflict_records WHERE status = 'resolved'"
            ).fetchone()[0]
            
            # Ethical wall statistics
            active_walls = conn.execute(
                "SELECT COUNT(*) FROM ethical_walls WHERE status = 'active'"
            ).fetchone()[0]
            
            wall_breaches = conn.execute(
                "SELECT COUNT(*) FROM access_violations WHERE violation_type = 'ethical_wall_breach'"
            ).fetchone()[0]
            
            # Privilege screening statistics
            recent_screenings = conn.execute('''
                SELECT privilege_level, COUNT(*) as count
                FROM privilege_screenings
                WHERE screening_date >= ?
                GROUP BY privilege_level
            ''', ((datetime.utcnow() - timedelta(days=30)).isoformat(),)).fetchall()
            
            screening_stats = {level: count for level, count in recent_screenings}
            
            # Access violations
            recent_violations = conn.execute('''
                SELECT violation_type, COUNT(*) as count
                FROM access_violations
                WHERE violation_date >= ?
                GROUP BY violation_type
            ''', ((datetime.utcnow() - timedelta(days=30)).isoformat(),)).fetchall()
            
            violation_stats = {vtype: count for vtype, count in recent_violations}
        
        return {
            "report_date": datetime.utcnow().isoformat(),
            "client_relationships": {
                "total": total_relationships,
                "active": active_relationships,
                "inactive": total_relationships - active_relationships
            },
            "conflicts_of_interest": {
                "total_identified": total_conflicts,
                "resolved": resolved_conflicts,
                "resolution_rate": f"{(resolved_conflicts/total_conflicts*100):.1f}%" if total_conflicts > 0 else "N/A"
            },
            "ethical_walls": {
                "active_walls": active_walls,
                "breach_attempts": wall_breaches,
                "effectiveness": f"{((active_walls - wall_breaches)/active_walls*100):.1f}%" if active_walls > 0 else "N/A"
            },
            "privilege_screening_30_days": screening_stats,
            "access_violations_30_days": violation_stats,
            "compliance_status": "compliant" if wall_breaches == 0 else "attention_required"
        }

# Global privilege manager instance
privilege_manager = AttorneyClientPrivilegeManager()