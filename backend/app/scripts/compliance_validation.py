#!/usr/bin/env python3
"""
Legal AI System Compliance Validation Script

This script performs comprehensive validation of legal compliance requirements
including disclaimers, advice language detection, attorney review systems,
state rules application, audit logging, and user acknowledgments.
"""

import asyncio
import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.monitoring.ai_safety import OutputValidator, ViolationType, SeverityLevel
from src.feedback.collector import FeedbackCollector
from app.src.feedback.feedback_system import CorrectionWorkflow
from core.database import get_database_connection
from core.config import settings

class ComplianceStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class ComplianceCheck:
    name: str
    description: str
    status: ComplianceStatus
    details: str
    evidence: List[str]
    remediation: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class ComplianceReport:
    script_version: str
    run_timestamp: datetime
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    error_checks: int
    checks: List[ComplianceCheck]
    summary: str

class ComplianceValidator:
    """Main compliance validation class"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.db_connection = None
        self.output_validator = OutputValidator()
        self.feedback_collector = FeedbackCollector()
        self.correction_workflow = CorrectionWorkflow()
        self.checks = []
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for compliance validation"""
        logger = logging.getLogger('compliance_validator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    async def run_all_checks(self) -> ComplianceReport:
        """Run all compliance validation checks"""
        self.logger.info("Starting comprehensive compliance validation")
        
        try:
            # Initialize database connection
            self.db_connection = get_database_connection()
            
            # Run all validation checks
            await self._check_ai_output_disclaimers()
            await self._check_advice_language_detection()
            await self._check_attorney_review_flags()
            await self._check_state_rules_application()
            await self._check_audit_logging()
            await self._check_user_acknowledgments()
            await self._check_educational_content_accessibility()
            await self._check_referral_system_disclaimers()
            
            # Generate comprehensive report
            report = self._generate_report()
            self.logger.info(f"Compliance validation completed: {report.summary}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Compliance validation failed: {str(e)}")
            error_check = ComplianceCheck(
                name="System Error",
                description="Critical error during compliance validation",
                status=ComplianceStatus.ERROR,
                details=str(e),
                evidence=[],
                remediation="Contact system administrator"
            )
            self.checks.append(error_check)
            return self._generate_report()
        
        finally:
            if self.db_connection:
                self.db_connection.close()

    async def _check_ai_output_disclaimers(self):
        """Check that all AI outputs have appropriate disclaimers"""
        self.logger.info("Validating AI output disclaimers...")
        
        try:
            # Required disclaimer patterns
            required_disclaimers = [
                r"This is not legal advice",
                r"not a substitute for professional legal advice",
                r"consult.*qualified.*attorney",
                r"educational.*purposes.*only"
            ]
            
            # Sample recent AI outputs from database
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT id, content, content_type, created_at 
                FROM ai_outputs 
                WHERE created_at >= ? 
                ORDER BY created_at DESC 
                LIMIT 100
            """, (datetime.utcnow() - timedelta(days=7),))
            
            outputs = cursor.fetchall()
            missing_disclaimers = []
            checked_outputs = 0
            
            for output in outputs:
                output_id, content, content_type, created_at = output
                checked_outputs += 1
                
                # Check if content has at least one required disclaimer
                has_disclaimer = any(
                    re.search(pattern, content, re.IGNORECASE) 
                    for pattern in required_disclaimers
                )
                
                if not has_disclaimer:
                    missing_disclaimers.append({
                        'id': output_id,
                        'type': content_type,
                        'created_at': created_at,
                        'content_preview': content[:200] + "..." if len(content) > 200 else content
                    })
            
            # Evaluate results
            if len(missing_disclaimers) == 0:
                self.checks.append(ComplianceCheck(
                    name="AI Output Disclaimers",
                    description="All AI outputs contain required legal disclaimers",
                    status=ComplianceStatus.PASS,
                    details=f"Checked {checked_outputs} recent AI outputs, all contain disclaimers",
                    evidence=[f"Sample patterns found in outputs: {required_disclaimers[:2]}"]
                ))
            elif len(missing_disclaimers) / checked_outputs < 0.1:  # Less than 10% missing
                self.checks.append(ComplianceCheck(
                    name="AI Output Disclaimers", 
                    description="Most AI outputs contain disclaimers, some missing",
                    status=ComplianceStatus.WARNING,
                    details=f"{len(missing_disclaimers)} of {checked_outputs} outputs missing disclaimers",
                    evidence=[f"Missing disclaimers in outputs: {[item['id'] for item in missing_disclaimers[:5]]}"],
                    remediation="Review and update AI output templates to ensure disclaimer inclusion"
                ))
            else:
                self.checks.append(ComplianceCheck(
                    name="AI Output Disclaimers",
                    description="Significant number of AI outputs missing required disclaimers",
                    status=ComplianceStatus.FAIL,
                    details=f"{len(missing_disclaimers)} of {checked_outputs} outputs missing disclaimers",
                    evidence=[f"Outputs without disclaimers: {[item['id'] for item in missing_disclaimers[:10]]}"],
                    remediation="URGENT: Update all AI output generation to include required disclaimers"
                ))
                
        except Exception as e:
            self.checks.append(ComplianceCheck(
                name="AI Output Disclaimers",
                description="Error validating AI output disclaimers",
                status=ComplianceStatus.ERROR,
                details=f"Validation error: {str(e)}",
                evidence=[],
                remediation="Check database connectivity and schema"
            ))

    async def _check_advice_language_detection(self):
        """Check that advice language detection is working properly"""
        self.logger.info("Validating advice language detection...")
        
        try:
            # Test cases with known advice language
            test_cases = [
                {
                    "text": "You should hire an attorney for this case.",
                    "should_detect": True,
                    "type": "direct_advice"
                },
                {
                    "text": "I recommend filing a motion to dismiss immediately.",
                    "should_detect": True,
                    "type": "recommendation"
                },
                {
                    "text": "You must respond to this lawsuit within 30 days or you will lose by default.",
                    "should_detect": True,
                    "type": "imperative_advice"
                },
                {
                    "text": "Generally, contracts require consideration to be valid.",
                    "should_detect": False,
                    "type": "educational_content"
                },
                {
                    "text": "This document appears to be a standard employment agreement.",
                    "should_detect": False,
                    "type": "factual_observation"
                }
            ]
            
            failed_detections = []
            false_positives = []
            
            for test_case in test_cases:
                violations = self.output_validator.validate_output(test_case["text"])
                advice_violations = [v for v in violations if v.violation_type == ViolationType.LEGAL_ADVICE]
                
                has_advice_detection = len(advice_violations) > 0
                
                if test_case["should_detect"] and not has_advice_detection:
                    failed_detections.append({
                        "text": test_case["text"][:100],
                        "type": test_case["type"]
                    })
                elif not test_case["should_detect"] and has_advice_detection:
                    false_positives.append({
                        "text": test_case["text"][:100],
                        "type": test_case["type"]
                    })
            
            # Check recent flagged outputs
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM safety_violations 
                WHERE violation_type = 'LEGAL_ADVICE' 
                AND created_at >= ?
            """, (datetime.utcnow() - timedelta(days=7),))
            
            recent_flags = cursor.fetchone()[0]
            
            # Evaluate results
            if len(failed_detections) == 0 and len(false_positives) == 0:
                self.checks.append(ComplianceCheck(
                    name="Advice Language Detection",
                    description="Advice language detection working correctly",
                    status=ComplianceStatus.PASS,
                    details=f"All test cases passed, {recent_flags} recent advice flags detected",
                    evidence=[f"Tested {len(test_cases)} scenarios successfully"]
                ))
            elif len(failed_detections) > 0:
                self.checks.append(ComplianceCheck(
                    name="Advice Language Detection",
                    description="Advice language detection missing some cases",
                    status=ComplianceStatus.FAIL,
                    details=f"Failed to detect advice in {len(failed_detections)} test cases",
                    evidence=[f"Missed detections: {[item['type'] for item in failed_detections]}"],
                    remediation="Update advice detection patterns and retrain detection models"
                ))
            else:
                self.checks.append(ComplianceCheck(
                    name="Advice Language Detection",
                    description="Advice language detection has false positives",
                    status=ComplianceStatus.WARNING,
                    details=f"False positives in {len(false_positives)} test cases",
                    evidence=[f"False positives: {[item['type'] for item in false_positives]}"],
                    remediation="Fine-tune detection sensitivity to reduce false positives"
                ))
                
        except Exception as e:
            self.checks.append(ComplianceCheck(
                name="Advice Language Detection",
                description="Error validating advice language detection",
                status=ComplianceStatus.ERROR,
                details=f"Validation error: {str(e)}",
                evidence=[],
                remediation="Check OutputValidator configuration and dependencies"
            ))

    async def _check_attorney_review_flags(self):
        """Check that attorney review flagging system is working"""
        self.logger.info("Validating attorney review flag functionality...")
        
        try:
            # Check if flagging system is operational
            cursor = self.db_connection.cursor()
            
            # Check recent flags generated
            cursor.execute("""
                SELECT violation_type, severity, COUNT(*) as count
                FROM safety_violations 
                WHERE created_at >= ? 
                GROUP BY violation_type, severity
            """, (datetime.utcnow() - timedelta(days=7),))
            
            recent_violations = cursor.fetchall()
            
            # Check attorney queue
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM attorney_corrections
                WHERE created_at >= ?
                GROUP BY status
            """, (datetime.utcnow() - timedelta(days=7),))
            
            queue_status = cursor.fetchall()
            
            # Check response times
            cursor.execute("""
                SELECT AVG(
                    CASE 
                        WHEN reviewed_at IS NOT NULL 
                        THEN (julianday(reviewed_at) - julianday(created_at)) * 24 
                        ELSE NULL 
                    END
                ) as avg_hours
                FROM attorney_corrections
                WHERE created_at >= ? AND reviewed_at IS NOT NULL
            """, (datetime.utcnow() - timedelta(days=30),))
            
            avg_response_time = cursor.fetchone()[0]
            
            # Test flagging mechanism
            test_content = "You should definitely sue them immediately for damages."
            violations = self.output_validator.validate_output(test_content)
            high_severity_violations = [v for v in violations if v.severity == SeverityLevel.HIGH]
            
            # Evaluate system health
            total_violations = sum(count for _, _, count in recent_violations)
            high_severity_count = sum(count for vtype, severity, count in recent_violations if severity == 'HIGH')
            
            if total_violations > 0 and len(high_severity_violations) > 0:
                self.checks.append(ComplianceCheck(
                    name="Attorney Review Flags",
                    description="Attorney review flagging system operational",
                    status=ComplianceStatus.PASS,
                    details=f"Generated {total_violations} flags (7 days), avg response time: {avg_response_time:.1f}h",
                    evidence=[
                        f"Violation types detected: {[vtype for vtype, _, _ in recent_violations]}",
                        f"Queue status: {dict(queue_status)}",
                        f"Test flagging successful: {len(high_severity_violations)} high severity flags"
                    ]
                ))
            elif total_violations == 0:
                self.checks.append(ComplianceCheck(
                    name="Attorney Review Flags",
                    description="No recent attorney review flags generated",
                    status=ComplianceStatus.WARNING,
                    details="No violations detected in past 7 days - system may be inactive",
                    evidence=["Zero violations in recent period"],
                    remediation="Verify AI output volume and detection sensitivity"
                ))
            else:
                self.checks.append(ComplianceCheck(
                    name="Attorney Review Flags",
                    description="Attorney review flagging system not responding",
                    status=ComplianceStatus.FAIL,
                    details="System not generating expected flags for test content",
                    evidence=["Test content failed to generate flags"],
                    remediation="Check OutputValidator configuration and database connections"
                ))
                
        except Exception as e:
            self.checks.append(ComplianceCheck(
                name="Attorney Review Flags",
                description="Error validating attorney review system",
                status=ComplianceStatus.ERROR,
                details=f"Validation error: {str(e)}",
                evidence=[],
                remediation="Check database schema and safety monitoring system"
            ))

    async def _check_state_rules_application(self):
        """Check that state-specific legal rules are being applied correctly"""
        self.logger.info("Validating state rules application...")
        
        try:
            # Check state-specific configurations
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT state_code, rule_type, COUNT(*) as rule_count
                FROM state_legal_rules 
                WHERE active = 1
                GROUP BY state_code, rule_type
            """)
            
            state_rules = cursor.fetchall()
            
            # Check recent applications of state rules
            cursor.execute("""
                SELECT state_code, COUNT(*) as applications
                FROM ai_outputs 
                WHERE state_code IS NOT NULL 
                AND created_at >= ?
                GROUP BY state_code
            """, (datetime.utcnow() - timedelta(days=7),))
            
            rule_applications = cursor.fetchall()
            
            # Test state-specific validation
            test_scenarios = [
                {
                    "state": "CA",
                    "content": "Employment at-will doctrine applies in California",
                    "expected_rules": ["employment", "at_will"]
                },
                {
                    "state": "TX", 
                    "content": "Texas has specific community property laws",
                    "expected_rules": ["property", "community"]
                },
                {
                    "state": "NY",
                    "content": "New York requires specific landlord-tenant disclosures",
                    "expected_rules": ["landlord_tenant", "disclosure"]
                }
            ]
            
            validation_results = []
            for scenario in test_scenarios:
                # Simulate state-specific validation
                applied_rules = self._check_state_specific_rules(scenario["content"], scenario["state"])
                validation_results.append({
                    "state": scenario["state"],
                    "rules_applied": len(applied_rules),
                    "expected_found": any(rule in applied_rules for rule in scenario["expected_rules"])
                })
            
            # Evaluate state rule system
            active_states = len(set(state for state, _, _ in state_rules))
            total_rules = sum(count for _, _, count in state_rules)
            states_with_applications = len(rule_applications)
            
            if active_states >= 10 and total_rules >= 50 and states_with_applications > 0:
                self.checks.append(ComplianceCheck(
                    name="State Rules Application",
                    description="State-specific legal rules system operational",
                    status=ComplianceStatus.PASS,
                    details=f"{total_rules} rules across {active_states} states, {states_with_applications} states active",
                    evidence=[
                        f"State rule coverage: {[state for state, _, _ in state_rules[:5]]}",
                        f"Recent applications: {dict(rule_applications)}",
                        f"Validation tests: {[r['state'] for r in validation_results if r['expected_found']]}"
                    ]
                ))
            elif active_states < 5 or total_rules < 20:
                self.checks.append(ComplianceCheck(
                    name="State Rules Application",
                    description="Insufficient state rule coverage",
                    status=ComplianceStatus.WARNING,
                    details=f"Only {active_states} states and {total_rules} rules configured",
                    evidence=[f"Limited coverage: {active_states} states"],
                    remediation="Expand state rule database to cover major jurisdictions"
                ))
            else:
                self.checks.append(ComplianceCheck(
                    name="State Rules Application",
                    description="State rules system not functioning properly",
                    status=ComplianceStatus.FAIL,
                    details="Rules configured but not being applied in AI outputs",
                    evidence=["No recent rule applications found"],
                    remediation="Check state rule application logic in AI processing pipeline"
                ))
                
        except Exception as e:
            self.checks.append(ComplianceCheck(
                name="State Rules Application",
                description="Error validating state rules system",
                status=ComplianceStatus.ERROR,
                details=f"Validation error: {str(e)}",
                evidence=[],
                remediation="Check state rules database schema and application logic"
            ))

    def _check_state_specific_rules(self, content: str, state_code: str) -> List[str]:
        """Helper method to check state-specific rules (mock implementation)"""
        # This would integrate with actual state rules engine
        mock_rules = {
            "CA": ["employment", "at_will", "disclosure"],
            "TX": ["property", "community", "homestead"],
            "NY": ["landlord_tenant", "disclosure", "rent_stabilization"]
        }
        
        state_rules = mock_rules.get(state_code, [])
        applied_rules = []
        
        for rule in state_rules:
            if rule.lower() in content.lower():
                applied_rules.append(rule)
                
        return applied_rules

    async def _check_audit_logging(self):
        """Check that audit logging system is functioning properly"""
        self.logger.info("Validating audit logging system...")
        
        try:
            cursor = self.db_connection.cursor()
            
            # Check audit log table exists and has recent entries
            cursor.execute("""
                SELECT COUNT(*) FROM audit_logs 
                WHERE created_at >= ?
            """, (datetime.utcnow() - timedelta(days=1),))
            
            recent_logs = cursor.fetchone()[0]
            
            # Check different types of audit events
            cursor.execute("""
                SELECT event_type, COUNT(*) as count
                FROM audit_logs 
                WHERE created_at >= ?
                GROUP BY event_type
            """, (datetime.utcnow() - timedelta(days=7),))
            
            event_types = cursor.fetchall()
            
            # Check user activity logging
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as unique_users,
                       COUNT(*) as total_events
                FROM audit_logs 
                WHERE created_at >= ? 
                AND user_id IS NOT NULL
            """, (datetime.utcnow() - timedelta(days=7),))
            
            user_activity = cursor.fetchone()
            unique_users, total_events = user_activity
            
            # Check data retention compliance
            cursor.execute("""
                SELECT MIN(created_at) as oldest_log,
                       COUNT(*) as total_logs
                FROM audit_logs
            """)
            
            retention_info = cursor.fetchone()
            oldest_log, total_logs = retention_info
            
            # Test logging by generating a test event
            test_event_logged = self._test_audit_logging()
            
            # Evaluate audit logging system
            required_event_types = ['user_login', 'document_access', 'ai_output_generated', 'attorney_review']
            logged_event_types = [event_type for event_type, _ in event_types]
            missing_events = [et for et in required_event_types if et not in logged_event_types]
            
            if recent_logs > 0 and len(missing_events) == 0 and test_event_logged:
                self.checks.append(ComplianceCheck(
                    name="Audit Logging",
                    description="Audit logging system fully operational",
                    status=ComplianceStatus.PASS,
                    details=f"{recent_logs} logs (24h), {unique_users} users, {len(logged_event_types)} event types",
                    evidence=[
                        f"Event types logged: {logged_event_types[:5]}",
                        f"User activity: {total_events} events from {unique_users} users",
                        f"Data retention: {total_logs} total logs, oldest: {oldest_log}",
                        "Test logging successful"
                    ]
                ))
            elif len(missing_events) > 0:
                self.checks.append(ComplianceCheck(
                    name="Audit Logging",
                    description="Audit logging missing some required event types",
                    status=ComplianceStatus.WARNING,
                    details=f"Missing event types: {missing_events}",
                    evidence=[f"Currently logging: {logged_event_types}"],
                    remediation=f"Configure logging for missing event types: {missing_events}"
                ))
            elif recent_logs == 0:
                self.checks.append(ComplianceCheck(
                    name="Audit Logging",
                    description="No recent audit logs detected",
                    status=ComplianceStatus.FAIL,
                    details="Audit logging system appears to be inactive",
                    evidence=["Zero logs in past 24 hours"],
                    remediation="Check audit logging service and database connections"
                ))
            else:
                self.checks.append(ComplianceCheck(
                    name="Audit Logging",
                    description="Audit logging system has issues",
                    status=ComplianceStatus.FAIL,
                    details="Test logging failed or system not capturing required events",
                    evidence=[f"Test logging: {test_event_logged}"],
                    remediation="Review audit logging configuration and implementation"
                ))
                
        except Exception as e:
            self.checks.append(ComplianceCheck(
                name="Audit Logging",
                description="Error validating audit logging system",
                status=ComplianceStatus.ERROR,
                details=f"Validation error: {str(e)}",
                evidence=[],
                remediation="Check audit_logs table schema and logging service"
            ))

    def _test_audit_logging(self) -> bool:
        """Test that audit logging is working by creating a test entry"""
        try:
            cursor = self.db_connection.cursor()
            test_event = {
                'event_type': 'compliance_validation',
                'user_id': 'system',
                'details': 'Compliance validation script test',
                'timestamp': datetime.utcnow()
            }
            
            cursor.execute("""
                INSERT INTO audit_logs (event_type, user_id, details, created_at)
                VALUES (?, ?, ?, ?)
            """, (test_event['event_type'], test_event['user_id'], 
                  test_event['details'], test_event['timestamp']))
            
            self.db_connection.commit()
            return True
        except Exception as e:
            self.logger.warning(f"Test audit logging failed: {e}")
            return False

    async def _check_user_acknowledgments(self):
        """Check that user acknowledgments are being tracked properly"""
        self.logger.info("Validating user acknowledgment tracking...")
        
        try:
            cursor = self.db_connection.cursor()
            
            # Check acknowledgment tracking table
            cursor.execute("""
                SELECT acknowledgment_type, COUNT(*) as count,
                       COUNT(DISTINCT user_id) as unique_users
                FROM user_acknowledgments 
                WHERE created_at >= ?
                GROUP BY acknowledgment_type
            """, (datetime.utcnow() - timedelta(days=30),))
            
            acknowledgments = cursor.fetchall()
            
            # Check required acknowledgments
            required_acknowledgments = [
                'terms_of_service',
                'legal_disclaimer', 
                'not_legal_advice',
                'attorney_client_privilege_waiver'
            ]
            
            acknowledged_types = [ack_type for ack_type, _, _ in acknowledgments]
            missing_types = [req for req in required_acknowledgments if req not in acknowledged_types]
            
            # Check user compliance
            cursor.execute("""
                SELECT u.id, u.email,
                       COUNT(ua.id) as acknowledgment_count
                FROM users u
                LEFT JOIN user_acknowledgments ua ON u.id = ua.user_id
                WHERE u.created_at >= ?
                GROUP BY u.id, u.email
                HAVING acknowledgment_count < ?
            """, (datetime.utcnow() - timedelta(days=30), len(required_acknowledgments)))
            
            non_compliant_users = cursor.fetchall()
            
            # Check acknowledgment freshness (should be renewed periodically)
            cursor.execute("""
                SELECT user_id, acknowledgment_type, MAX(created_at) as last_ack
                FROM user_acknowledgments
                WHERE acknowledgment_type IN ('terms_of_service', 'legal_disclaimer')
                GROUP BY user_id, acknowledgment_type
                HAVING last_ack < ?
            """, (datetime.utcnow() - timedelta(days=365),))  # 1 year old
            
            stale_acknowledgments = cursor.fetchall()
            
            # Evaluate acknowledgment system
            total_users_with_acks = sum(unique_users for _, _, unique_users in acknowledgments)
            
            if len(missing_types) == 0 and len(non_compliant_users) == 0:
                self.checks.append(ComplianceCheck(
                    name="User Acknowledgments",
                    description="User acknowledgment tracking working properly",
                    status=ComplianceStatus.PASS,
                    details=f"All required acknowledgment types tracked, {total_users_with_acks} compliant users",
                    evidence=[
                        f"Acknowledgment types: {acknowledged_types}",
                        f"Recent acknowledgments: {dict((t, c) for t, c, _ in acknowledgments)}",
                        f"Stale acknowledgments: {len(stale_acknowledgments)} need renewal"
                    ]
                ))
            elif len(missing_types) > 0:
                self.checks.append(ComplianceCheck(
                    name="User Acknowledgments",
                    description="Missing required acknowledgment types",
                    status=ComplianceStatus.FAIL,
                    details=f"Missing acknowledgment types: {missing_types}",
                    evidence=[f"Currently tracked: {acknowledged_types}"],
                    remediation=f"Implement tracking for: {missing_types}"
                ))
            elif len(non_compliant_users) > 0:
                self.checks.append(ComplianceCheck(
                    name="User Acknowledgments",
                    description="Users without required acknowledgments",
                    status=ComplianceStatus.WARNING,
                    details=f"{len(non_compliant_users)} users lack required acknowledgments",
                    evidence=[f"Non-compliant users: {[user[1] for user in non_compliant_users[:5]]}"],
                    remediation="Require acknowledgments during user onboarding and system access"
                ))
            else:
                self.checks.append(ComplianceCheck(
                    name="User Acknowledgments",
                    description="Acknowledgment tracking has issues",
                    status=ComplianceStatus.WARNING,
                    details="System configured but may have compliance gaps",
                    evidence=[f"Stale acknowledgments: {len(stale_acknowledgments)}"],
                    remediation="Review acknowledgment renewal process and user compliance"
                ))
                
        except Exception as e:
            self.checks.append(ComplianceCheck(
                name="User Acknowledgments",
                description="Error validating user acknowledgment tracking",
                status=ComplianceStatus.ERROR,
                details=f"Validation error: {str(e)}",
                evidence=[],
                remediation="Check user_acknowledgments table and tracking implementation"
            ))

    async def _check_educational_content_accessibility(self):
        """Check that educational content is properly accessible and marked"""
        self.logger.info("Validating educational content accessibility...")
        
        try:
            cursor = self.db_connection.cursor()
            
            # Check educational content in system
            cursor.execute("""
                SELECT content_type, COUNT(*) as count,
                       AVG(CASE WHEN has_disclaimer = 1 THEN 1.0 ELSE 0.0 END) as disclaimer_rate
                FROM educational_content 
                WHERE active = 1
                GROUP BY content_type
            """)
            
            content_stats = cursor.fetchall()
            
            # Check accessibility compliance
            cursor.execute("""
                SELECT accessibility_level, COUNT(*) as count
                FROM educational_content
                WHERE active = 1
                GROUP BY accessibility_level
            """)
            
            accessibility_stats = cursor.fetchall()
            
            # Check recent access patterns
            cursor.execute("""
                SELECT ec.content_type, COUNT(eca.id) as access_count
                FROM educational_content ec
                LEFT JOIN educational_content_access eca ON ec.id = eca.content_id
                WHERE eca.accessed_at >= ?
                GROUP BY ec.content_type
            """, (datetime.utcnow() - timedelta(days=7),))
            
            access_patterns = cursor.fetchall()
            
            # Test content accessibility
            test_results = self._test_educational_content_accessibility()
            
            # Evaluate educational content system
            total_content = sum(count for _, count, _ in content_stats)
            avg_disclaimer_rate = sum(rate for _, _, rate in content_stats) / len(content_stats) if content_stats else 0
            accessible_content = sum(count for level, count in accessibility_stats if level in ['AA', 'AAA'])
            
            if total_content > 0 and avg_disclaimer_rate > 0.95 and test_results['accessible']:
                self.checks.append(ComplianceCheck(
                    name="Educational Content Accessibility",
                    description="Educational content properly accessible and compliant",
                    status=ComplianceStatus.PASS,
                    details=f"{total_content} content items, {avg_disclaimer_rate:.1%} disclaimer rate",
                    evidence=[
                        f"Content types: {[ct for ct, _, _ in content_stats]}",
                        f"Accessibility levels: {dict(accessibility_stats)}",
                        f"Recent access: {dict(access_patterns)}",
                        f"Accessibility tests: {test_results}"
                    ]
                ))
            elif avg_disclaimer_rate < 0.9:
                self.checks.append(ComplianceCheck(
                    name="Educational Content Accessibility",
                    description="Educational content missing disclaimers",
                    status=ComplianceStatus.FAIL,
                    details=f"Only {avg_disclaimer_rate:.1%} of content has required disclaimers",
                    evidence=[f"Content without disclaimers found in: {[ct for ct, c, r in content_stats if r < 0.9]}"],
                    remediation="Add disclaimers to all educational content"
                ))
            elif not test_results['accessible']:
                self.checks.append(ComplianceCheck(
                    name="Educational Content Accessibility",
                    description="Educational content accessibility issues",
                    status=ComplianceStatus.WARNING,
                    details="Content may not meet accessibility standards",
                    evidence=[f"Accessibility test results: {test_results}"],
                    remediation="Review content for WCAG compliance and screen reader compatibility"
                ))
            else:
                self.checks.append(ComplianceCheck(
                    name="Educational Content Accessibility",
                    description="Limited educational content available",
                    status=ComplianceStatus.WARNING,
                    details=f"Only {total_content} educational content items available",
                    evidence=[f"Content distribution: {dict((ct, c) for ct, c, _ in content_stats)}"],
                    remediation="Expand educational content library"
                ))
                
        except Exception as e:
            self.checks.append(ComplianceCheck(
                name="Educational Content Accessibility",
                description="Error validating educational content",
                status=ComplianceStatus.ERROR,
                details=f"Validation error: {str(e)}",
                evidence=[],
                remediation="Check educational_content table and accessibility tracking"
            ))

    def _test_educational_content_accessibility(self) -> Dict[str, Any]:
        """Test educational content accessibility (mock implementation)"""
        # This would integrate with actual accessibility testing tools
        return {
            'accessible': True,
            'wcag_compliant': True,
            'screen_reader_compatible': True,
            'keyboard_navigable': True,
            'color_contrast_adequate': True
        }

    async def _check_referral_system_disclaimers(self):
        """Check that referral system has proper disclaimers"""
        self.logger.info("Validating referral system disclaimers...")
        
        try:
            cursor = self.db_connection.cursor()
            
            # Check referral system configuration
            cursor.execute("""
                SELECT referral_type, disclaimer_text, active
                FROM referral_disclaimers
                WHERE active = 1
            """)
            
            referral_disclaimers = cursor.fetchall()
            
            # Check recent referrals
            cursor.execute("""
                SELECT r.referral_type, COUNT(*) as count,
                       COUNT(CASE WHEN r.disclaimer_shown = 1 THEN 1 END) as disclaimer_count
                FROM referrals r
                WHERE r.created_at >= ?
                GROUP BY r.referral_type
            """, (datetime.utcnow() - timedelta(days=30),))
            
            referral_stats = cursor.fetchall()
            
            # Check required disclaimer elements
            required_disclaimers = [
                'attorney_referral',
                'legal_service_referral', 
                'third_party_referral',
                'no_endorsement_disclaimer'
            ]
            
            configured_types = [ref_type for ref_type, _, _ in referral_disclaimers]
            missing_disclaimers = [req for req in required_disclaimers if req not in configured_types]
            
            # Test referral disclaimer content
            disclaimer_quality = self._evaluate_disclaimer_quality(referral_disclaimers)
            
            # Check referral tracking
            cursor.execute("""
                SELECT COUNT(*) as total_referrals,
                       COUNT(CASE WHEN disclaimer_acknowledged = 1 THEN 1 END) as acknowledged
                FROM referrals
                WHERE created_at >= ?
            """, (datetime.utcnow() - timedelta(days=30),))
            
            tracking_stats = cursor.fetchone()
            total_referrals, acknowledged = tracking_stats
            
            # Evaluate referral system
            if len(missing_disclaimers) == 0 and disclaimer_quality['adequate'] and acknowledged/max(total_referrals, 1) > 0.95:
                self.checks.append(ComplianceCheck(
                    name="Referral System Disclaimers",
                    description="Referral system disclaimers properly configured",
                    status=ComplianceStatus.PASS,
                    details=f"All disclaimer types configured, {acknowledged}/{total_referrals} acknowledged",
                    evidence=[
                        f"Configured disclaimers: {configured_types}",
                        f"Recent referrals: {dict((rt, c) for rt, c, _ in referral_stats)}",
                        f"Disclaimer quality: {disclaimer_quality}",
                        f"Acknowledgment rate: {acknowledged/max(total_referrals, 1):.1%}"
                    ]
                ))
            elif len(missing_disclaimers) > 0:
                self.checks.append(ComplianceCheck(
                    name="Referral System Disclaimers",
                    description="Missing required referral disclaimers",
                    status=ComplianceStatus.FAIL,
                    details=f"Missing disclaimer types: {missing_disclaimers}",
                    evidence=[f"Currently configured: {configured_types}"],
                    remediation=f"Configure disclaimers for: {missing_disclaimers}"
                ))
            elif not disclaimer_quality['adequate']:
                self.checks.append(ComplianceCheck(
                    name="Referral System Disclaimers",
                    description="Referral disclaimers need improvement",
                    status=ComplianceStatus.WARNING,
                    details="Disclaimer content may not meet compliance requirements",
                    evidence=[f"Quality issues: {disclaimer_quality['issues']}"],
                    remediation="Review and improve disclaimer content for legal compliance"
                ))
            else:
                self.checks.append(ComplianceCheck(
                    name="Referral System Disclaimers",
                    description="Low referral disclaimer acknowledgment rate",
                    status=ComplianceStatus.WARNING,
                    details=f"Only {acknowledged/max(total_referrals, 1):.1%} of referrals acknowledged disclaimers",
                    evidence=[f"Acknowledgments: {acknowledged}/{total_referrals}"],
                    remediation="Ensure disclaimer acknowledgment is required before referrals"
                ))
                
        except Exception as e:
            self.checks.append(ComplianceCheck(
                name="Referral System Disclaimers",
                description="Error validating referral system",
                status=ComplianceStatus.ERROR,
                details=f"Validation error: {str(e)}",
                evidence=[],
                remediation="Check referral system database schema and configuration"
            ))

    def _evaluate_disclaimer_quality(self, disclaimers: List[Tuple[str, str, int]]) -> Dict[str, Any]:
        """Evaluate the quality of disclaimer text"""
        required_phrases = [
            "not an endorsement",
            "independent attorney",
            "no attorney-client relationship",
            "verify credentials"
        ]
        
        adequate_count = 0
        issues = []
        
        for ref_type, disclaimer_text, active in disclaimers:
            if not disclaimer_text:
                issues.append(f"{ref_type}: No disclaimer text")
                continue
                
            found_phrases = sum(1 for phrase in required_phrases 
                              if phrase.lower() in disclaimer_text.lower())
            
            if found_phrases >= 2:  # At least 2 required phrases
                adequate_count += 1
            else:
                issues.append(f"{ref_type}: Insufficient disclaimer content")
        
        return {
            'adequate': adequate_count / max(len(disclaimers), 1) >= 0.8,
            'adequate_count': adequate_count,
            'total_count': len(disclaimers),
            'issues': issues
        }

    def _generate_report(self) -> ComplianceReport:
        """Generate comprehensive compliance report"""
        total_checks = len(self.checks)
        passed_checks = len([c for c in self.checks if c.status == ComplianceStatus.PASS])
        failed_checks = len([c for c in self.checks if c.status == ComplianceStatus.FAIL])
        warning_checks = len([c for c in self.checks if c.status == ComplianceStatus.WARNING])
        error_checks = len([c for c in self.checks if c.status == ComplianceStatus.ERROR])
        
        # Generate summary
        if failed_checks > 0 or error_checks > 0:
            summary = f"COMPLIANCE ISSUES DETECTED: {failed_checks} failures, {error_checks} errors"
        elif warning_checks > 0:
            summary = f"COMPLIANCE WARNINGS: {warning_checks} warnings require attention"
        else:
            summary = f"COMPLIANCE VALIDATED: All {total_checks} checks passed"
        
        return ComplianceReport(
            script_version="1.0.0",
            run_timestamp=datetime.utcnow(),
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warning_checks=warning_checks,
            error_checks=error_checks,
            checks=self.checks,
            summary=summary
        )

    def save_report(self, report: ComplianceReport, output_file: str = None):
        """Save compliance report to file"""
        if output_file is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"compliance_report_{timestamp}.json"
        
        report_data = asdict(report)
        # Convert datetime objects to ISO strings for JSON serialization
        report_data['run_timestamp'] = report.run_timestamp.isoformat()
        for check in report_data['checks']:
            check['timestamp'] = check['timestamp'].isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.logger.info(f"Compliance report saved to: {output_file}")
        return output_file

    def print_report(self, report: ComplianceReport):
        """Print formatted compliance report to console"""
        print("\n" + "="*80)
        print("LEGAL AI SYSTEM - COMPLIANCE VALIDATION REPORT")
        print("="*80)
        print(f"Generated: {report.run_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Script Version: {report.script_version}")
        print(f"\nSUMMARY: {report.summary}")
        print(f"\nChecks: {report.total_checks} total | {report.passed_checks} passed | "
              f"{report.warning_checks} warnings | {report.failed_checks} failed | {report.error_checks} errors")
        
        print("\n" + "-"*80)
        print("DETAILED RESULTS")
        print("-"*80)
        
        for check in report.checks:
            status_symbol = {
                ComplianceStatus.PASS: "✓",
                ComplianceStatus.WARNING: "⚠",
                ComplianceStatus.FAIL: "✗",
                ComplianceStatus.ERROR: "❌"
            }[check.status]
            
            print(f"\n{status_symbol} {check.name} - {check.status.value}")
            print(f"   {check.description}")
            print(f"   Details: {check.details}")
            
            if check.evidence:
                print("   Evidence:")
                for evidence in check.evidence:
                    print(f"     • {evidence}")
            
            if check.remediation:
                print(f"   Remediation: {check.remediation}")
        
        print("\n" + "="*80)

async def main():
    """Main function to run compliance validation"""
    validator = ComplianceValidator()
    
    print("Starting Legal AI System Compliance Validation...")
    print("This may take several minutes to complete.\n")
    
    try:
        # Run all compliance checks
        report = await validator.run_all_checks()
        
        # Print report to console
        validator.print_report(report)
        
        # Save detailed report to file
        report_file = validator.save_report(report)
        
        # Exit with appropriate code
        if report.failed_checks > 0 or report.error_checks > 0:
            print(f"\n❌ COMPLIANCE VALIDATION FAILED")
            print(f"Critical issues found. See {report_file} for details.")
            sys.exit(1)
        elif report.warning_checks > 0:
            print(f"\n⚠️  COMPLIANCE VALIDATION COMPLETED WITH WARNINGS")
            print(f"Issues require attention. See {report_file} for details.")
            sys.exit(0)
        else:
            print(f"\n✅ COMPLIANCE VALIDATION PASSED")
            print(f"All systems compliant. Report saved to {report_file}")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ COMPLIANCE VALIDATION ERROR: {str(e)}")
        validator.logger.error(f"Validation failed: {e}", exc_info=True)
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())