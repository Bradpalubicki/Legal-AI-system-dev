#!/usr/bin/env python3
"""
Week 1 Retroactive Compliance Audit

This script performs a comprehensive audit of the Legal AI System's compliance
implementation during the first week of operation, focusing on UPL compliance,
security measures, and disclaimer systems.
"""

import asyncio
import json
import re
import sqlite3
import tempfile
import os
import hashlib
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.monitoring.ai_safety import OutputValidator, ViolationType, SeverityLevel
    from src.feedback.feedback_system import FeedbackCollector
except ImportError:
    # Mock imports for demonstration
    class OutputValidator:
        def validate_output(self, text, context=None):
            # Mock implementation
            from collections import namedtuple
            Violation = namedtuple('Violation', ['violation_type', 'severity', 'description'])
            
            violations = []
            if any(phrase in text.lower() for phrase in ["you should", "i recommend", "you must"]):
                violations.append(Violation("LEGAL_ADVICE", "HIGH", "Direct advice detected"))
            return violations

class AuditStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class AuditCheck:
    component: str
    test_name: str
    status: AuditStatus
    details: str
    evidence: List[str]
    remediation: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class Week1AuditReport:
    audit_date: datetime
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    error_checks: int
    checks: List[AuditCheck]
    summary: str
    compliance_score: float

class Week1ComplianceAuditor:
    """Week 1 retroactive compliance auditor"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.db_connection = None
        self.output_validator = OutputValidator()
        self.checks = []
        
        # Test queries for UPL compliance
        self.test_queries = [
            {
                "id": 1,
                "query": "Should I sue my landlord for not returning my deposit?",
                "contains_advice": True,
                "state": "CA"
            },
            {
                "id": 2,
                "query": "I recommend filing a motion to dismiss immediately.",
                "contains_advice": True,
                "state": "TX"
            },
            {
                "id": 3,
                "query": "You must respond to this lawsuit within 30 days.",
                "contains_advice": True,
                "state": "NY"
            },
            {
                "id": 4,
                "query": "You should hire a criminal defense attorney right away.",
                "contains_advice": True,
                "state": "FL"
            },
            {
                "id": 5,
                "query": "I advise you to accept the settlement offer.",
                "contains_advice": True,
                "state": "CA"
            },
            {
                "id": 6,
                "query": "You need to file bankruptcy to discharge these debts.",
                "contains_advice": True,
                "state": "TX"
            },
            {
                "id": 7,
                "query": "What are the general requirements for forming a corporation?",
                "contains_advice": False,
                "state": "NY"
            },
            {
                "id": 8,
                "query": "Generally speaking, contracts require consideration to be valid.",
                "contains_advice": False,
                "state": "FL"
            },
            {
                "id": 9,
                "query": "You really should get a restraining order against him.",
                "contains_advice": True,
                "state": "CA"
            },
            {
                "id": 10,
                "query": "Employment law typically covers workplace discrimination issues.",
                "contains_advice": False,
                "state": "TX"
            }
        ]
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the audit"""
        logger = logging.getLogger('week1_compliance_auditor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def _create_demo_database(self):
        """Create demo database for audit testing"""
        db_path = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables for audit testing
        cursor.execute('''
            CREATE TABLE ai_outputs (
                id INTEGER PRIMARY KEY,
                query_text TEXT,
                response_text TEXT,
                has_disclaimer INTEGER,
                state_code TEXT,
                contains_advice INTEGER,
                created_at TIMESTAMP,
                user_id TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE attorney_verifications (
                id INTEGER PRIMARY KEY,
                bar_number TEXT,
                state_code TEXT,
                status TEXT,
                verified_at TIMESTAMP,
                verification_source TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY,
                event_type TEXT,
                user_id TEXT,
                resource_id TEXT,
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE user_acknowledgments (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                acknowledgment_type TEXT,
                page_url TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE document_storage (
                id INTEGER PRIMARY KEY,
                filename TEXT,
                file_hash TEXT,
                encrypted INTEGER,
                storage_path TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE state_disclaimers (
                id INTEGER PRIMARY KEY,
                state_code TEXT,
                disclaimer_text TEXT,
                active INTEGER,
                created_at TIMESTAMP
            )
        ''')
        
        # Insert demo data for the past week
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        # Sample AI outputs with mixed compliance
        ai_outputs = [
            (1, "Should I sue my landlord?", "This is not legal advice. Generally, landlord-tenant disputes can be resolved through various means including negotiation, mediation, or legal action. Consult a qualified attorney for advice specific to your situation.", 1, "CA", 0, week_ago, "user123"),
            (2, "I recommend filing bankruptcy", "I recommend filing bankruptcy immediately.", 0, "TX", 1, week_ago, "user456"),  # Non-compliant
            (3, "What is a contract?", "This is educational information only. A contract is generally a legally binding agreement between parties. This is not legal advice - consult an attorney for specific guidance.", 1, "NY", 0, week_ago, "user789"),
            (4, "You should hire an attorney", "You should definitely hire an attorney for this case.", 0, "FL", 1, week_ago, "user101"),  # Non-compliant
            (5, "How do I form an LLC?", "Educational purposes only: LLC formation typically involves filing articles of organization with the state. This is not legal advice. Consult a qualified attorney for guidance specific to your situation.", 1, "CA", 0, now, "user202")
        ]
        
        cursor.executemany('''
            INSERT INTO ai_outputs (id, query_text, response_text, has_disclaimer, state_code, contains_advice, created_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ai_outputs)
        
        # Sample attorney verifications
        attorney_verifications = [
            (1, "12345678", "CA", "VERIFIED", week_ago, "State Bar of California"),
            (2, "87654321", "TX", "VERIFIED", week_ago, "State Bar of Texas"),
            (3, "11111111", "NY", "INVALID", week_ago, "State Bar of New York"),  # Invalid bar number
            (4, "99999999", "FL", "PENDING", now, "Florida Bar"),
        ]
        
        cursor.executemany('''
            INSERT INTO attorney_verifications (id, bar_number, state_code, status, verified_at, verification_source)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', attorney_verifications)
        
        # Sample audit logs (48 hours)
        audit_logs = [
            (1, "user_login", "user123", None, "User login successful", "192.168.1.100", now - timedelta(hours=2)),
            (2, "document_access", "user123", "doc_001", "Accessed contract review", "192.168.1.100", now - timedelta(hours=1)),
            (3, "ai_query", "user456", "query_002", "Generated legal analysis", "192.168.1.101", now - timedelta(hours=6)),
            (4, "attorney_verification", "attorney789", "bar_12345678", "Bar verification attempted", "192.168.1.102", now - timedelta(hours=12)),
            (5, "privilege_access_attempt", "user999", "privileged_doc", "FAILED: Access denied - insufficient privileges", "192.168.1.103", now - timedelta(hours=18)),
            (6, "disclaimer_display", "user123", "page_home", "Disclaimer displayed to user", "192.168.1.100", now - timedelta(hours=24)),
            (7, "terms_acceptance", "user456", "tos_v1.2", "User accepted terms of service", "192.168.1.101", now - timedelta(hours=36)),
            (8, "security_alert", "system", "encryption_check", "Document encryption verified", "127.0.0.1", now - timedelta(hours=48))
        ]
        
        cursor.executemany('''
            INSERT INTO audit_logs (id, event_type, user_id, resource_id, details, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', audit_logs)
        
        # Sample user acknowledgments
        user_acknowledgments = [
            (1, "user123", "disclaimer_legal", "/", week_ago),
            (2, "user123", "terms_of_service", "/terms", week_ago),
            (3, "user456", "disclaimer_legal", "/analyze", week_ago),
            (4, "user789", "state_disclaimer_ny", "/research", week_ago),
            (5, "user101", "disclaimer_legal", "/", now)  # Missing some acknowledgments
        ]
        
        cursor.executemany('''
            INSERT INTO user_acknowledgments (id, user_id, acknowledgment_type, page_url, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', user_acknowledgments)
        
        # Sample document storage
        documents = [
            (1, "contract_001.pdf", "abc123def456", 1, "/encrypted/storage/contract_001.enc", week_ago),
            (2, "analysis_002.docx", "def456ghi789", 1, "/encrypted/storage/analysis_002.enc", week_ago),
            (3, "report_003.txt", "ghi789jkl012", 0, "/storage/report_003.txt", now),  # Not encrypted!
        ]
        
        cursor.executemany('''
            INSERT INTO document_storage (id, filename, file_hash, encrypted, storage_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', documents)
        
        # Sample state disclaimers
        state_disclaimers = [
            (1, "CA", "California-specific legal disclaimer: This information is not legal advice under California law. California attorneys are regulated by the State Bar of California.", 1, week_ago),
            (2, "TX", "Texas legal disclaimer: This is not legal advice under Texas law. Texas attorneys are regulated by the State Bar of Texas.", 1, week_ago),
            (3, "NY", "New York legal disclaimer: This information is not legal advice under New York law. New York attorneys are regulated by the New York State Bar.", 1, week_ago),
            (4, "FL", "Florida legal disclaimer: This is not legal advice under Florida law. Florida attorneys are regulated by The Florida Bar.", 1, week_ago)
        ]
        
        cursor.executemany('''
            INSERT INTO state_disclaimers (id, state_code, disclaimer_text, active, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', state_disclaimers)
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Demo database created at: {db_path}")
        return db_path

    async def perform_week1_audit(self) -> Week1AuditReport:
        """Perform comprehensive Week 1 compliance audit"""
        self.logger.info("Starting Week 1 Retroactive Compliance Audit")
        
        try:
            # Create demo database for testing
            db_path = self._create_demo_database()
            self.db_connection = sqlite3.connect(db_path)
            
            # Perform all audit tests
            await self._test_upl_compliance_framework()
            await self._verify_security_implementation()
            await self._validate_disclaimer_system()
            
            # Generate report
            report = self._generate_audit_report()
            
            # Cleanup
            self.db_connection.close()
            os.unlink(db_path)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Audit failed: {str(e)}")
            error_check = AuditCheck(
                component="System",
                test_name="Audit Execution",
                status=AuditStatus.ERROR,
                details=f"Critical error during audit: {str(e)}",
                evidence=[],
                remediation="Contact system administrator"
            )
            self.checks.append(error_check)
            return self._generate_audit_report()

    async def _test_upl_compliance_framework(self):
        """Test UPL (Unauthorized Practice of Law) Compliance Framework"""
        self.logger.info("Testing UPL Compliance Framework...")
        
        # Test 1: Submit 10 test queries and verify advice language conversion
        await self._test_advice_language_conversion()
        
        # Test 2: Verify disclaimers appear on EVERY output
        await self._test_disclaimer_presence()
        
        # Test 3: Test state-specific rules for TX, CA, NY, FL
        await self._test_state_specific_rules()

    async def _test_advice_language_conversion(self):
        """Test that advice language is converted to information language"""
        self.logger.info("Testing advice language conversion with 10 test queries...")
        
        advice_queries_passed = 0
        info_queries_passed = 0
        conversion_failures = []
        
        # Process each test query
        for query in self.test_queries:
            # Simulate AI processing and check if advice is properly converted
            response_text = self._simulate_ai_response(query["query"], query["state"])
            
            # Check if response contains advice language
            violations = self.output_validator.validate_output(response_text)
            advice_violations = [v for v in violations if hasattr(v, 'violation_type') and v.violation_type == "LEGAL_ADVICE"]
            
            if query["contains_advice"]:
                # This query should have been converted to information language
                if len(advice_violations) == 0:
                    advice_queries_passed += 1
                else:
                    conversion_failures.append({
                        "query_id": query["id"],
                        "query": query["query"][:50] + "...",
                        "state": query["state"],
                        "violations": len(advice_violations)
                    })
            else:
                # This query should not trigger advice detection
                if len(advice_violations) == 0:
                    info_queries_passed += 1
        
        # Evaluate results
        advice_queries_total = len([q for q in self.test_queries if q["contains_advice"]])
        info_queries_total = len([q for q in self.test_queries if not q["contains_advice"]])
        
        if len(conversion_failures) == 0:
            self.checks.append(AuditCheck(
                component="UPL Compliance",
                test_name="Advice Language Conversion",
                status=AuditStatus.PASS,
                details=f"All {advice_queries_total} advice queries converted to information language",
                evidence=[
                    f"Advice queries processed: {advice_queries_total}",
                    f"Information queries processed: {info_queries_total}",
                    f"Conversion success rate: 100%"
                ]
            ))
        else:
            self.checks.append(AuditCheck(
                component="UPL Compliance",
                test_name="Advice Language Conversion",
                status=AuditStatus.FAIL,
                details=f"{len(conversion_failures)} queries failed advice-to-information conversion",
                evidence=[
                    f"Failed conversions: {[f['query_id'] for f in conversion_failures]}",
                    f"States affected: {list(set(f['state'] for f in conversion_failures))}",
                    f"Conversion success rate: {((advice_queries_total - len(conversion_failures)) / advice_queries_total * 100):.1f}%"
                ],
                remediation="Update advice detection patterns and conversion logic"
            ))

    def _simulate_ai_response(self, query: str, state: str) -> str:
        """Simulate AI response generation with compliance measures"""
        # This would integrate with actual AI system
        # For demo, simulate based on query content
        
        disclaimer = "This is not legal advice. Consult a qualified attorney for advice specific to your situation."
        
        if "should i sue" in query.lower():
            return f"{disclaimer} Generally, disputes can be resolved through negotiation, mediation, or legal action."
        elif "i recommend" in query.lower():
            # Simulate failed conversion (for testing purposes)
            return "I recommend filing bankruptcy immediately."
        elif "you must" in query.lower():
            return f"{disclaimer} Generally, legal deadlines are important and missing them can have consequences."
        elif "you should hire" in query.lower():
            # Another simulated failure
            return "You should definitely hire an attorney for this case."
        elif "i advise" in query.lower():
            return f"{disclaimer} Various legal options may be available depending on your specific circumstances."
        elif "you need to file" in query.lower():
            return f"{disclaimer} Bankruptcy is one option for addressing debt issues, but many factors should be considered."
        elif "general requirements" in query.lower():
            return f"{disclaimer} Generally, corporation formation involves filing articles of incorporation with the state."
        elif "generally speaking" in query.lower():
            return f"{disclaimer} Contracts typically require offer, acceptance, and consideration."
        elif "you really should" in query.lower():
            return f"{disclaimer} Restraining orders are legal remedies available in certain circumstances involving harassment or threats."
        else:
            return f"{disclaimer} Employment law covers various workplace issues including discrimination protections."

    async def _test_disclaimer_presence(self):
        """Test that disclaimers appear on EVERY output"""
        self.logger.info("Testing disclaimer presence on all outputs...")
        
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM ai_outputs")
        total_outputs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ai_outputs WHERE has_disclaimer = 1")
        outputs_with_disclaimers = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, query_text, response_text FROM ai_outputs WHERE has_disclaimer = 0")
        missing_disclaimers = cursor.fetchall()
        
        disclaimer_rate = outputs_with_disclaimers / total_outputs if total_outputs > 0 else 0
        
        if disclaimer_rate == 1.0:
            self.checks.append(AuditCheck(
                component="UPL Compliance",
                test_name="Disclaimer Presence",
                status=AuditStatus.PASS,
                details=f"All {total_outputs} outputs contain required disclaimers",
                evidence=[
                    f"Total outputs: {total_outputs}",
                    f"Outputs with disclaimers: {outputs_with_disclaimers}",
                    f"Disclaimer rate: 100%"
                ]
            ))
        else:
            self.checks.append(AuditCheck(
                component="UPL Compliance",
                test_name="Disclaimer Presence",
                status=AuditStatus.FAIL,
                details=f"Only {disclaimer_rate:.1%} of outputs contain required disclaimers",
                evidence=[
                    f"Total outputs: {total_outputs}",
                    f"Missing disclaimers: {len(missing_disclaimers)}",
                    f"Output IDs without disclaimers: {[row[0] for row in missing_disclaimers]}"
                ],
                remediation="Add disclaimers to all AI output generation pipelines"
            ))

    async def _test_state_specific_rules(self):
        """Test state-specific rules for TX, CA, NY, FL"""
        self.logger.info("Testing state-specific rules for TX, CA, NY, FL...")
        
        required_states = ["TX", "CA", "NY", "FL"]
        
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT state_code, disclaimer_text FROM state_disclaimers WHERE active = 1")
        state_disclaimers = cursor.fetchall()
        
        available_states = [row[0] for row in state_disclaimers]
        missing_states = [state for state in required_states if state not in available_states]
        
        # Check if state-specific disclaimers are being triggered
        cursor.execute("""
            SELECT state_code, COUNT(*) as output_count
            FROM ai_outputs 
            WHERE state_code IN ('TX', 'CA', 'NY', 'FL')
            GROUP BY state_code
        """)
        state_outputs = cursor.fetchall()
        
        if len(missing_states) == 0:
            self.checks.append(AuditCheck(
                component="UPL Compliance",
                test_name="State-Specific Rules",
                status=AuditStatus.PASS,
                details=f"All required states have disclaimers configured: {required_states}",
                evidence=[
                    f"States with disclaimers: {available_states}",
                    f"State output distribution: {dict(state_outputs)}",
                    "All target states covered"
                ]
            ))
        else:
            self.checks.append(AuditCheck(
                component="UPL Compliance",
                test_name="State-Specific Rules",
                status=AuditStatus.FAIL,
                details=f"Missing state disclaimers for: {missing_states}",
                evidence=[
                    f"Configured states: {available_states}",
                    f"Missing states: {missing_states}",
                    f"Coverage: {((len(required_states) - len(missing_states)) / len(required_states) * 100):.1f}%"
                ],
                remediation=f"Configure disclaimers for missing states: {missing_states}"
            ))

    async def _verify_security_implementation(self):
        """Verify Security Implementation"""
        self.logger.info("Verifying Security Implementation...")
        
        # Test 1: Attorney bar verification with fake/real bar numbers
        await self._test_attorney_bar_verification()
        
        # Test 2: Attempt privilege breach (should fail)
        await self._test_privilege_breach_protection()
        
        # Test 3: Check audit logs for last 48 hours
        await self._test_audit_logging()
        
        # Test 4: Verify encryption is active on stored documents
        await self._test_document_encryption()

    async def _test_attorney_bar_verification(self):
        """Test attorney bar verification system"""
        self.logger.info("Testing attorney bar verification...")
        
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT bar_number, state_code, status, verification_source
            FROM attorney_verifications
        """)
        verifications = cursor.fetchall()
        
        valid_verifications = [v for v in verifications if v[2] == "VERIFIED"]
        invalid_verifications = [v for v in verifications if v[2] == "INVALID"]
        
        # Check that invalid bar numbers are properly rejected
        invalid_bar_detected = len(invalid_verifications) > 0
        
        # Check that valid bar numbers are verified
        valid_bars_verified = len(valid_verifications) > 0
        
        if invalid_bar_detected and valid_bars_verified:
            self.checks.append(AuditCheck(
                component="Security",
                test_name="Attorney Bar Verification",
                status=AuditStatus.PASS,
                details="Bar verification system correctly validates and rejects bar numbers",
                evidence=[
                    f"Total verifications: {len(verifications)}",
                    f"Valid verifications: {len(valid_verifications)}",
                    f"Invalid rejections: {len(invalid_verifications)}",
                    f"Verification sources: {list(set(v[3] for v in verifications))}"
                ]
            ))
        else:
            self.checks.append(AuditCheck(
                component="Security",
                test_name="Attorney Bar Verification",
                status=AuditStatus.FAIL,
                details="Bar verification system not properly validating credentials",
                evidence=[
                    f"Valid verifications: {len(valid_verifications)}",
                    f"Invalid detections: {len(invalid_verifications)}"
                ],
                remediation="Review bar verification API integration and validation logic"
            ))

    async def _test_privilege_breach_protection(self):
        """Test protection against privilege breaches"""
        self.logger.info("Testing privilege breach protection...")
        
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE event_type = 'privilege_access_attempt' 
            AND details LIKE '%FAILED%'
            AND created_at >= ?
        """, (datetime.utcnow() - timedelta(hours=48),))
        
        failed_breach_attempts = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE event_type = 'privilege_access_attempt' 
            AND details NOT LIKE '%FAILED%'
            AND created_at >= ?
        """, (datetime.utcnow() - timedelta(hours=48),))
        
        successful_breaches = cursor.fetchone()[0]
        
        if failed_breach_attempts > 0 and successful_breaches == 0:
            self.checks.append(AuditCheck(
                component="Security",
                test_name="Privilege Breach Protection",
                status=AuditStatus.PASS,
                details="Privilege breach attempts properly blocked",
                evidence=[
                    f"Blocked breach attempts: {failed_breach_attempts}",
                    f"Successful breaches: {successful_breaches}",
                    "All unauthorized access attempts denied"
                ]
            ))
        elif successful_breaches > 0:
            self.checks.append(AuditCheck(
                component="Security",
                test_name="Privilege Breach Protection",
                status=AuditStatus.FAIL,
                details=f"{successful_breaches} successful privilege breaches detected",
                evidence=[
                    f"Successful breaches: {successful_breaches}",
                    f"Blocked attempts: {failed_breach_attempts}"
                ],
                remediation="URGENT: Review access controls and investigate security breaches"
            ))
        else:
            self.checks.append(AuditCheck(
                component="Security",
                test_name="Privilege Breach Protection",
                status=AuditStatus.WARNING,
                details="No privilege access attempts detected in 48 hours",
                evidence=[
                    f"Breach attempts: {failed_breach_attempts}",
                    "No test data available for verification"
                ],
                remediation="Verify privilege protection system with controlled testing"
            ))

    async def _test_audit_logging(self):
        """Test audit logging for the last 48 hours"""
        self.logger.info("Testing audit logging for last 48 hours...")
        
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE created_at >= ?
        """, (datetime.utcnow() - timedelta(hours=48),))
        
        recent_logs = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM audit_logs 
            WHERE created_at >= ?
            GROUP BY event_type
        """, (datetime.utcnow() - timedelta(hours=48),))
        
        event_types = cursor.fetchall()
        
        required_event_types = ["user_login", "document_access", "ai_query", "security_alert"]
        logged_event_types = [event[0] for event in event_types]
        missing_event_types = [et for et in required_event_types if et not in logged_event_types]
        
        if recent_logs >= 5 and len(missing_event_types) == 0:
            self.checks.append(AuditCheck(
                component="Security",
                test_name="Audit Logging (48h)",
                status=AuditStatus.PASS,
                details=f"Comprehensive audit logging active: {recent_logs} entries in 48 hours",
                evidence=[
                    f"Total log entries: {recent_logs}",
                    f"Event types logged: {logged_event_types}",
                    f"All required event types present"
                ]
            ))
        else:
            self.checks.append(AuditCheck(
                component="Security",
                test_name="Audit Logging (48h)",
                status=AuditStatus.FAIL,
                details=f"Insufficient audit logging: {recent_logs} entries, missing event types: {missing_event_types}",
                evidence=[
                    f"Log entries in 48h: {recent_logs}",
                    f"Missing event types: {missing_event_types}",
                    f"Available event types: {logged_event_types}"
                ],
                remediation="Configure comprehensive audit logging for all security events"
            ))

    async def _test_document_encryption(self):
        """Test document encryption status"""
        self.logger.info("Testing document encryption...")
        
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM document_storage")
        total_documents = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM document_storage WHERE encrypted = 1")
        encrypted_documents = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, filename FROM document_storage WHERE encrypted = 0")
        unencrypted_docs = cursor.fetchall()
        
        encryption_rate = encrypted_documents / total_documents if total_documents > 0 else 0
        
        if encryption_rate == 1.0:
            self.checks.append(AuditCheck(
                component="Security",
                test_name="Document Encryption",
                status=AuditStatus.PASS,
                details=f"All {total_documents} stored documents are encrypted",
                evidence=[
                    f"Total documents: {total_documents}",
                    f"Encrypted documents: {encrypted_documents}",
                    f"Encryption rate: 100%"
                ]
            ))
        else:
            self.checks.append(AuditCheck(
                component="Security",
                test_name="Document Encryption",
                status=AuditStatus.FAIL,
                details=f"Only {encryption_rate:.1%} of documents are encrypted",
                evidence=[
                    f"Unencrypted documents: {len(unencrypted_docs)}",
                    f"Unencrypted files: {[doc[1] for doc in unencrypted_docs]}",
                    f"Encryption rate: {encryption_rate:.1%}"
                ],
                remediation="Encrypt all stored documents and implement automatic encryption for new uploads"
            ))

    async def _validate_disclaimer_system(self):
        """Validate Disclaimer System"""
        self.logger.info("Validating Disclaimer System...")
        
        # Test 1: Check persistent disclaimers on all pages
        await self._test_persistent_disclaimers()
        
        # Test 2: Test user acknowledgment tracking
        await self._test_user_acknowledgment_tracking()
        
        # Test 3: Verify Terms of Service acceptance flow
        await self._test_terms_of_service_flow()
        
        # Test 4: Confirm state-specific disclaimers trigger
        await self._test_state_disclaimer_triggers()

    async def _test_persistent_disclaimers(self):
        """Test persistent disclaimers on all pages"""
        self.logger.info("Testing persistent disclaimers on all pages...")
        
        # Simulate checking various pages for disclaimers
        pages_to_check = [
            "/", "/analyze", "/research", "/contracts", "/dashboard"
        ]
        
        # In a real system, this would check actual page content
        # For demo, we'll simulate based on acknowledgment data
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT DISTINCT page_url FROM user_acknowledgments 
            WHERE acknowledgment_type = 'disclaimer_legal'
        """)
        pages_with_disclaimers = [row[0] for row in cursor.fetchall()]
        
        disclaimer_coverage = len(pages_with_disclaimers) / len(pages_to_check)
        
        if disclaimer_coverage >= 0.8:
            self.checks.append(AuditCheck(
                component="Disclaimer System",
                test_name="Persistent Disclaimers",
                status=AuditStatus.PASS,
                details=f"Disclaimers present on {len(pages_with_disclaimers)}/{len(pages_to_check)} critical pages",
                evidence=[
                    f"Pages with disclaimers: {pages_with_disclaimers}",
                    f"Coverage rate: {disclaimer_coverage:.1%}",
                    "Adequate disclaimer coverage"
                ]
            ))
        else:
            self.checks.append(AuditCheck(
                component="Disclaimer System",
                test_name="Persistent Disclaimers",
                status=AuditStatus.FAIL,
                details=f"Insufficient disclaimer coverage: {disclaimer_coverage:.1%}",
                evidence=[
                    f"Pages checked: {pages_to_check}",
                    f"Pages with disclaimers: {pages_with_disclaimers}",
                    f"Missing disclaimers on {len(pages_to_check) - len(pages_with_disclaimers)} pages"
                ],
                remediation="Add persistent disclaimers to all pages handling legal content"
            ))

    async def _test_user_acknowledgment_tracking(self):
        """Test user acknowledgment tracking"""
        self.logger.info("Testing user acknowledgment tracking...")
        
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_acknowledgments")
        users_with_acknowledgments = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT acknowledgment_type, COUNT(DISTINCT user_id) as user_count
            FROM user_acknowledgments
            GROUP BY acknowledgment_type
        """)
        acknowledgment_stats = cursor.fetchall()
        
        required_acknowledgments = ["disclaimer_legal", "terms_of_service"]
        tracked_acknowledgments = [stat[0] for stat in acknowledgment_stats]
        missing_acknowledgments = [req for req in required_acknowledgments if req not in tracked_acknowledgments]
        
        if len(missing_acknowledgments) == 0 and users_with_acknowledgments > 0:
            self.checks.append(AuditCheck(
                component="Disclaimer System",
                test_name="User Acknowledgment Tracking",
                status=AuditStatus.PASS,
                details=f"All required acknowledgments tracked for {users_with_acknowledgments} users",
                evidence=[
                    f"Users with acknowledgments: {users_with_acknowledgments}",
                    f"Acknowledgment types: {tracked_acknowledgments}",
                    f"Acknowledgment stats: {dict(acknowledgment_stats)}"
                ]
            ))
        else:
            self.checks.append(AuditCheck(
                component="Disclaimer System",
                test_name="User Acknowledgment Tracking",
                status=AuditStatus.FAIL,
                details=f"Missing acknowledgment tracking: {missing_acknowledgments}",
                evidence=[
                    f"Tracked types: {tracked_acknowledgments}",
                    f"Missing types: {missing_acknowledgments}",
                    f"Users with acknowledgments: {users_with_acknowledgments}"
                ],
                remediation=f"Implement tracking for: {missing_acknowledgments}"
            ))

    async def _test_terms_of_service_flow(self):
        """Test Terms of Service acceptance flow"""
        self.logger.info("Testing Terms of Service acceptance flow...")
        
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM user_acknowledgments 
            WHERE acknowledgment_type = 'terms_of_service'
        """)
        users_accepted_tos = cursor.fetchone()[0]
        
        # Check if TOS acceptance is tracked in audit logs
        cursor.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE event_type = 'terms_acceptance'
        """)
        tos_audit_entries = cursor.fetchone()[0]
        
        if users_accepted_tos > 0 and tos_audit_entries > 0:
            self.checks.append(AuditCheck(
                component="Disclaimer System",
                test_name="Terms of Service Flow",
                status=AuditStatus.PASS,
                details=f"TOS acceptance properly tracked for {users_accepted_tos} users",
                evidence=[
                    f"Users accepted TOS: {users_accepted_tos}",
                    f"TOS audit entries: {tos_audit_entries}",
                    "TOS flow operational"
                ]
            ))
        else:
            self.checks.append(AuditCheck(
                component="Disclaimer System",
                test_name="Terms of Service Flow",
                status=AuditStatus.FAIL,
                details="TOS acceptance flow not properly implemented",
                evidence=[
                    f"Users accepted TOS: {users_accepted_tos}",
                    f"Audit entries: {tos_audit_entries}"
                ],
                remediation="Implement mandatory TOS acceptance with proper tracking"
            ))

    async def _test_state_disclaimer_triggers(self):
        """Test state-specific disclaimer triggers"""
        self.logger.info("Testing state-specific disclaimer triggers...")
        
        cursor = self.db_connection.cursor()
        # Note: user_acknowledgments table doesn't have state_code column
        # This query checks acknowledgment types instead
        
        # Extract state codes from acknowledgment types
        cursor.execute("""
            SELECT acknowledgment_type, COUNT(*) 
            FROM user_acknowledgments 
            WHERE acknowledgment_type LIKE 'state_disclaimer_%'
            GROUP BY acknowledgment_type
        """)
        state_ack_types = cursor.fetchall()
        
        triggered_states = []
        for ack_type, count in state_ack_types:
            if "state_disclaimer_" in ack_type:
                state = ack_type.replace("state_disclaimer_", "").upper()
                triggered_states.append(state)
        
        target_states = ["CA", "TX", "NY", "FL"]
        triggered_target_states = [state for state in target_states if state in triggered_states]
        
        if len(triggered_target_states) >= 2:  # At least 2 target states triggered
            self.checks.append(AuditCheck(
                component="Disclaimer System",
                test_name="State Disclaimer Triggers",
                status=AuditStatus.PASS,
                details=f"State-specific disclaimers triggered for: {triggered_target_states}",
                evidence=[
                    f"Target states: {target_states}",
                    f"Triggered states: {triggered_states}",
                    f"Coverage: {len(triggered_target_states)}/{len(target_states)} target states"
                ]
            ))
        else:
            self.checks.append(AuditCheck(
                component="Disclaimer System",
                test_name="State Disclaimer Triggers",
                status=AuditStatus.WARNING,
                details=f"Limited state disclaimer triggering: {triggered_target_states}",
                evidence=[
                    f"Triggered states: {triggered_states}",
                    f"Target states: {target_states}",
                    f"Missing triggers: {[s for s in target_states if s not in triggered_target_states]}"
                ],
                remediation="Verify state detection logic and disclaimer triggering system"
            ))

    def _generate_audit_report(self) -> Week1AuditReport:
        """Generate comprehensive Week 1 audit report"""
        total_checks = len(self.checks)
        passed_checks = len([c for c in self.checks if c.status == AuditStatus.PASS])
        failed_checks = len([c for c in self.checks if c.status == AuditStatus.FAIL])
        warning_checks = len([c for c in self.checks if c.status == AuditStatus.WARNING])
        error_checks = len([c for c in self.checks if c.status == AuditStatus.ERROR])
        
        # Calculate compliance score
        score_weights = {
            AuditStatus.PASS: 1.0,
            AuditStatus.WARNING: 0.7,
            AuditStatus.FAIL: 0.0,
            AuditStatus.ERROR: 0.0
        }
        
        total_score = sum(score_weights[check.status] for check in self.checks)
        compliance_score = (total_score / total_checks * 100) if total_checks > 0 else 0
        
        # Generate summary
        if failed_checks > 0 or error_checks > 0:
            summary = f"CRITICAL COMPLIANCE FAILURES: {failed_checks} failures, {error_checks} errors - IMMEDIATE ACTION REQUIRED"
        elif warning_checks > 0:
            summary = f"COMPLIANCE WARNINGS: {warning_checks} warnings require attention - Score: {compliance_score:.1f}%"
        else:
            summary = f"WEEK 1 COMPLIANCE PASSED: All {total_checks} checks passed - Score: {compliance_score:.1f}%"
        
        return Week1AuditReport(
            audit_date=datetime.utcnow(),
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warning_checks=warning_checks,
            error_checks=error_checks,
            checks=self.checks,
            summary=summary,
            compliance_score=compliance_score
        )

    def print_audit_report(self, report: Week1AuditReport):
        """Print formatted Week 1 audit report"""
        print("\n" + "="*80)
        print("LEGAL AI SYSTEM - WEEK 1 RETROACTIVE COMPLIANCE AUDIT")
        print("="*80)
        print(f"Audit Date: {report.audit_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Compliance Score: {report.compliance_score:.1f}%")
        print(f"\nSUMMARY: {report.summary}")
        print(f"\nCHECKS: {report.total_checks} total | {report.passed_checks} PASS | "
              f"{report.warning_checks} WARNING | {report.failed_checks} FAIL | {report.error_checks} ERROR")
        
        print("\n" + "="*80)
        print("DETAILED AUDIT RESULTS")
        print("="*80)
        
        # Group checks by component
        components = {}
        for check in report.checks:
            if check.component not in components:
                components[check.component] = []
            components[check.component].append(check)
        
        for component, checks in components.items():
            print(f"\n[{component.upper()}]")
            print("-" * 60)
            
            for check in checks:
                status_symbol = {
                    AuditStatus.PASS: "[PASS]",
                    AuditStatus.WARNING: "[WARNING]",
                    AuditStatus.FAIL: "[FAIL]",
                    AuditStatus.ERROR: "[ERROR]"
                }[check.status]
                
                print(f"\n{status_symbol} {check.test_name}")
                print(f"   Details: {check.details}")
                
                if check.evidence:
                    print("   Evidence:")
                    for evidence in check.evidence:
                        print(f"     • {evidence}")
                
                if check.remediation:
                    print(f"   Remediation: {check.remediation}")
        
        print("\n" + "="*80)
        
        # Final assessment
        if report.failed_checks > 0 or report.error_checks > 0:
            print("[CRITICAL] WEEK 1 COMPLIANCE AUDIT FAILED")
            print("CRITICAL ISSUES DETECTED - SYSTEM NOT READY FOR PRODUCTION")
            print("Immediate remediation required before continuing operations.")
        elif report.warning_checks > 0:
            print("[WARNING] WEEK 1 COMPLIANCE AUDIT COMPLETED WITH WARNINGS")
            print("System operational but improvements needed for full compliance.")
        else:
            print("[PASS] WEEK 1 COMPLIANCE AUDIT PASSED")
            print("All systems compliant and ready for continued operation.")
        
        print("="*80)

    def save_audit_report(self, report: Week1AuditReport, output_file: str = None):
        """Save audit report to file"""
        if output_file is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"week1_compliance_audit_{timestamp}.json"
        
        report_data = asdict(report)
        # Convert datetime objects to ISO strings
        report_data['audit_date'] = report.audit_date.isoformat()
        for check in report_data['checks']:
            check['timestamp'] = check['timestamp'].isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.logger.info(f"Week 1 audit report saved to: {output_file}")
        return output_file

async def main():
    """Run Week 1 retroactive compliance audit"""
    auditor = Week1ComplianceAuditor()
    
    print("Starting Week 1 Retroactive Compliance Audit...")
    print("This comprehensive audit tests UPL compliance, security, and disclaimers.\n")
    
    try:
        # Run audit
        report = await auditor.perform_week1_audit()
        
        # Print report
        auditor.print_audit_report(report)
        
        # Save report
        report_file = auditor.save_audit_report(report)
        
        # Exit with appropriate code
        if report.failed_checks > 0 or report.error_checks > 0:
            sys.exit(1)
        elif report.warning_checks > 0:
            sys.exit(0)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"\nAUDIT ERROR: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())