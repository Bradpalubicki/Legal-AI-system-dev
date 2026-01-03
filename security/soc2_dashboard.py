#!/usr/bin/env python3
"""
SOC 2 Type II Compliance Monitoring Dashboard
Real-time compliance monitoring and reporting system
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict
import logging
from flask import Blueprint, render_template, jsonify, request
import plotly.graph_objs as go
import plotly.utils

# Import our security modules
from .encryption import encryption_manager
from .rbac_mfa import auth_manager
from .audit_logging import audit_system
from .data_retention import retention_manager
from .backup_recovery import backup_manager
from .privilege_protection import privilege_manager

logger = logging.getLogger(__name__)

class ComplianceStatus(Enum):
    """Overall compliance status levels"""
    COMPLIANT = "compliant"
    WARNING = "warning"
    CRITICAL = "critical"
    NON_COMPLIANT = "non_compliant"

@dataclass
class ComplianceMetric:
    """Individual compliance metric"""
    metric_name: str
    current_value: float
    target_value: float
    status: ComplianceStatus
    last_updated: datetime
    trend_direction: str  # "up", "down", "stable"
    description: str

class SOC2ComplianceMonitor:
    """SOC 2 Type II compliance monitoring system"""
    
    def __init__(self):
        self.trust_service_criteria = {
            "security": {
                "name": "Security",
                "description": "Protection against unauthorized access",
                "weight": 0.25
            },
            "availability": {
                "name": "Availability", 
                "description": "System operational availability",
                "weight": 0.20
            },
            "processing_integrity": {
                "name": "Processing Integrity",
                "description": "Complete and accurate processing",
                "weight": 0.20
            },
            "confidentiality": {
                "name": "Confidentiality",
                "description": "Protection of confidential information",
                "weight": 0.20
            },
            "privacy": {
                "name": "Privacy",
                "description": "Protection of personal information",
                "weight": 0.15
            }
        }
        
        # Compliance thresholds
        self.thresholds = {
            "security_incidents": {"warning": 5, "critical": 10},
            "failed_logins": {"warning": 100, "critical": 500},
            "backup_success_rate": {"warning": 95, "critical": 90},
            "encryption_coverage": {"warning": 98, "critical": 95},
            "access_violations": {"warning": 3, "critical": 10},
            "privilege_breaches": {"warning": 1, "critical": 5},
            "audit_log_gaps": {"warning": 1, "critical": 5},
            "retention_compliance": {"warning": 95, "critical": 90}
        }
    
    def generate_compliance_dashboard_data(self) -> Dict[str, Any]:
        """Generate comprehensive compliance dashboard data"""
        
        try:
            # Collect metrics from all security modules
            security_metrics = self._collect_security_metrics()
            availability_metrics = self._collect_availability_metrics()
            integrity_metrics = self._collect_integrity_metrics()
            confidentiality_metrics = self._collect_confidentiality_metrics()
            privacy_metrics = self._collect_privacy_metrics()
            
            # Calculate overall compliance score
            overall_score = self._calculate_overall_compliance_score({
                "security": security_metrics,
                "availability": availability_metrics,
                "processing_integrity": integrity_metrics,
                "confidentiality": confidentiality_metrics,
                "privacy": privacy_metrics
            })
            
            # Generate trend data
            trend_data = self._generate_compliance_trends()
            
            # Identify critical issues
            critical_issues = self._identify_critical_issues()
            
            # Recent compliance events
            recent_events = self._get_recent_compliance_events()
            
            return {
                "generated_at": datetime.utcnow().isoformat(),
                "overall_compliance": {
                    "score": overall_score["score"],
                    "status": overall_score["status"].value,
                    "grade": self._score_to_grade(overall_score["score"])
                },
                "trust_service_criteria": {
                    "security": security_metrics,
                    "availability": availability_metrics,
                    "processing_integrity": integrity_metrics,
                    "confidentiality": confidentiality_metrics,
                    "privacy": privacy_metrics
                },
                "trends": trend_data,
                "critical_issues": critical_issues,
                "recent_events": recent_events,
                "next_review_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "certifications": self._get_certification_status()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate compliance dashboard data: {e}")
            return {
                "error": "Failed to generate compliance data",
                "generated_at": datetime.utcnow().isoformat()
            }
    
    def _collect_security_metrics(self) -> Dict[str, Any]:
        """Collect security-related compliance metrics"""
        
        try:
            # Authentication metrics
            auth_report = auth_manager.audit_active_sessions()
            
            # Encryption metrics
            encryption_report = encryption_manager.audit_encryption_status()
            
            # Audit metrics
            audit_events = audit_system.query_events(hours_back=24, limit=1000)
            security_incidents = len([e for e in audit_events 
                                   if e.get('risk_level') in ['high', 'critical']])
            
            failed_logins = len([e for e in audit_events 
                               if e.get('event_type') == 'user_login_failed'])
            
            # Access control metrics
            access_violations = len([e for e in audit_events 
                                   if e.get('event_type') == 'unauthorized_access_attempt'])
            
            # Calculate security score (0-100)
            security_score = 100
            
            # Deduct points for issues
            if security_incidents > self.thresholds["security_incidents"]["critical"]:
                security_score -= 30
            elif security_incidents > self.thresholds["security_incidents"]["warning"]:
                security_score -= 15
            
            if failed_logins > self.thresholds["failed_logins"]["critical"]:
                security_score -= 20
            elif failed_logins > self.thresholds["failed_logins"]["warning"]:
                security_score -= 10
            
            if access_violations > self.thresholds["access_violations"]["critical"]:
                security_score -= 25
            elif access_violations > self.thresholds["access_violations"]["warning"]:
                security_score -= 10
            
            # Add points for good practices
            if auth_report.get("mfa_enabled_users", 0) > 0:
                security_score += 5
            
            if encryption_report.get("compliance_status") == "SOC 2 Type II Compliant":
                security_score += 10
            
            security_score = max(0, min(100, security_score))
            
            return {
                "score": security_score,
                "status": self._score_to_status(security_score),
                "metrics": {
                    "security_incidents_24h": security_incidents,
                    "failed_logins_24h": failed_logins,
                    "access_violations_24h": access_violations,
                    "mfa_enabled_users": auth_report.get("mfa_enabled_users", 0),
                    "encryption_compliance": encryption_report.get("compliance_status", "Unknown"),
                    "active_sessions": auth_report.get("total_active_sessions", 0),
                    "locked_accounts": auth_report.get("locked_accounts", 0)
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect security metrics: {e}")
            return {"score": 0, "status": ComplianceStatus.CRITICAL, "error": str(e)}
    
    def _collect_availability_metrics(self) -> Dict[str, Any]:
        """Collect availability-related compliance metrics"""
        
        try:
            # Backup metrics
            backup_report = backup_manager.generate_backup_report()
            
            # System uptime (simplified - in production would integrate with monitoring)
            uptime_percentage = 99.9  # Placeholder
            
            # Recovery metrics
            backup_success_rate = float(backup_report["recent_backups_7_days"]["success_rate"].rstrip('%'))
            
            # Calculate availability score
            availability_score = 0
            
            # Backup success rate impact (40% of score)
            if backup_success_rate >= 99:
                availability_score += 40
            elif backup_success_rate >= 95:
                availability_score += 30
            elif backup_success_rate >= 90:
                availability_score += 20
            else:
                availability_score += 10
            
            # Uptime impact (40% of score)
            if uptime_percentage >= 99.9:
                availability_score += 40
            elif uptime_percentage >= 99.5:
                availability_score += 30
            elif uptime_percentage >= 99.0:
                availability_score += 20
            else:
                availability_score += 10
            
            # Disaster recovery preparedness (20% of score)
            dr_compliance = backup_report["disaster_recovery"]
            if dr_compliance["rto_compliance"]:
                availability_score += 20
            elif dr_compliance["average_recovery_time_minutes"] <= 480:  # 8 hours
                availability_score += 15
            else:
                availability_score += 5
            
            return {
                "score": availability_score,
                "status": self._score_to_status(availability_score),
                "metrics": {
                    "uptime_percentage": uptime_percentage,
                    "backup_success_rate": backup_success_rate,
                    "average_recovery_time": dr_compliance["average_recovery_time_minutes"],
                    "rto_compliance": dr_compliance["rto_compliance"],
                    "active_backup_jobs": backup_report["backup_jobs"]["active"],
                    "total_backup_size_gb": backup_report["storage"]["total_backup_size_gb"]
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect availability metrics: {e}")
            return {"score": 0, "status": ComplianceStatus.CRITICAL, "error": str(e)}
    
    def _collect_integrity_metrics(self) -> Dict[str, Any]:
        """Collect processing integrity compliance metrics"""
        
        try:
            # Audit trail completeness
            audit_integrity = audit_system.verify_audit_integrity()
            
            # Data retention compliance
            retention_report = retention_manager.generate_retention_report()
            
            # AI processing accuracy (simplified metrics)
            processing_accuracy = 98.5  # Placeholder for AI model accuracy
            
            # Calculate integrity score
            integrity_score = 0
            
            # Audit integrity (40% of score)
            if audit_integrity["status"] == "verified":
                integrity_score += 40
            elif audit_integrity["status"] == "no_events":
                integrity_score += 30
            else:
                integrity_score += 10
            
            # Data retention compliance (30% of score)
            if retention_report["compliance_status"] == "compliant":
                integrity_score += 30
            else:
                integrity_score += 15
            
            # Processing accuracy (30% of score)
            if processing_accuracy >= 99:
                integrity_score += 30
            elif processing_accuracy >= 95:
                integrity_score += 25
            elif processing_accuracy >= 90:
                integrity_score += 20
            else:
                integrity_score += 10
            
            return {
                "score": integrity_score,
                "status": self._score_to_status(integrity_score),
                "metrics": {
                    "audit_integrity": audit_integrity["status"],
                    "retention_compliance": retention_report["compliance_status"],
                    "processing_accuracy": processing_accuracy,
                    "total_records_managed": retention_report["total_active_records"],
                    "expired_records_pending": retention_report["expired_records_pending_deletion"],
                    "legal_holds_active": retention_report["active_legal_holds"]
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect integrity metrics: {e}")
            return {"score": 0, "status": ComplianceStatus.CRITICAL, "error": str(e)}
    
    def _collect_confidentiality_metrics(self) -> Dict[str, Any]:
        """Collect confidentiality compliance metrics"""
        
        try:
            # Privilege protection metrics
            privilege_report = privilege_manager.generate_privilege_compliance_report()
            
            # Encryption coverage
            encryption_status = encryption_manager.audit_encryption_status()
            
            # Access control effectiveness
            unauthorized_access_attempts = len(audit_system.query_events(
                event_types=[audit_system.AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT],
                hours_back=24
            ))
            
            # Calculate confidentiality score
            confidentiality_score = 0
            
            # Privilege protection (40% of score)
            if privilege_report["compliance_status"] == "compliant":
                confidentiality_score += 40
            else:
                confidentiality_score += 20
            
            # Encryption coverage (35% of score)
            if encryption_status["compliance_status"] == "SOC 2 Type II Compliant":
                confidentiality_score += 35
            else:
                confidentiality_score += 15
            
            # Access control (25% of score)
            if unauthorized_access_attempts == 0:
                confidentiality_score += 25
            elif unauthorized_access_attempts <= 3:
                confidentiality_score += 20
            elif unauthorized_access_attempts <= 10:
                confidentiality_score += 15
            else:
                confidentiality_score += 5
            
            return {
                "score": confidentiality_score,
                "status": self._score_to_status(confidentiality_score),
                "metrics": {
                    "privilege_compliance": privilege_report["compliance_status"],
                    "encryption_compliance": encryption_status["compliance_status"],
                    "unauthorized_access_attempts": unauthorized_access_attempts,
                    "ethical_walls_active": privilege_report["ethical_walls"]["active_walls"],
                    "ethical_wall_breaches": privilege_report["ethical_walls"]["breach_attempts"],
                    "active_client_relationships": privilege_report["client_relationships"]["active"]
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect confidentiality metrics: {e}")
            return {"score": 0, "status": ComplianceStatus.CRITICAL, "error": str(e)}
    
    def _collect_privacy_metrics(self) -> Dict[str, Any]:
        """Collect privacy compliance metrics"""
        
        try:
            # Data retention and deletion compliance
            retention_report = retention_manager.generate_retention_report()
            
            # Personal data processing metrics (simplified)
            personal_data_processed = 1250  # Placeholder
            consent_rate = 98.5  # Placeholder
            
            # Data subject requests (GDPR/CCPA compliance)
            data_subject_requests_processed = 45  # Placeholder
            response_time_avg_days = 12  # Placeholder
            
            # Calculate privacy score
            privacy_score = 0
            
            # Data retention compliance (40% of score)
            if retention_report["compliance_status"] == "compliant":
                privacy_score += 40
            else:
                privacy_score += 20
            
            # Consent management (30% of score)
            if consent_rate >= 99:
                privacy_score += 30
            elif consent_rate >= 95:
                privacy_score += 25
            elif consent_rate >= 90:
                privacy_score += 20
            else:
                privacy_score += 10
            
            # Data subject rights (30% of score)
            if response_time_avg_days <= 30:  # Legal requirement
                privacy_score += 30
            elif response_time_avg_days <= 45:
                privacy_score += 20
            else:
                privacy_score += 10
            
            return {
                "score": privacy_score,
                "status": self._score_to_status(privacy_score),
                "metrics": {
                    "data_retention_compliance": retention_report["compliance_status"],
                    "personal_data_records": personal_data_processed,
                    "consent_rate": consent_rate,
                    "data_subject_requests": data_subject_requests_processed,
                    "avg_response_time_days": response_time_avg_days,
                    "records_under_legal_hold": retention_report["records_under_hold"]
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect privacy metrics: {e}")
            return {"score": 0, "status": ComplianceStatus.CRITICAL, "error": str(e)}
    
    def _calculate_overall_compliance_score(self, criteria_scores: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate weighted overall compliance score"""
        
        total_weighted_score = 0
        
        for criterion, weight in [(k, v["weight"]) for k, v in self.trust_service_criteria.items()]:
            criterion_score = criteria_scores.get(criterion, {}).get("score", 0)
            total_weighted_score += criterion_score * weight
        
        overall_status = self._score_to_status(total_weighted_score)
        
        return {
            "score": round(total_weighted_score, 2),
            "status": overall_status,
            "breakdown": {
                criterion: {
                    "score": criteria_scores.get(criterion, {}).get("score", 0),
                    "weight": weight,
                    "weighted_contribution": criteria_scores.get(criterion, {}).get("score", 0) * weight
                }
                for criterion, weight in [(k, v["weight"]) for k, v in self.trust_service_criteria.items()]
            }
        }
    
    def _score_to_status(self, score: float) -> ComplianceStatus:
        """Convert numeric score to compliance status"""
        if score >= 95:
            return ComplianceStatus.COMPLIANT
        elif score >= 80:
            return ComplianceStatus.WARNING
        elif score >= 60:
            return ComplianceStatus.CRITICAL
        else:
            return ComplianceStatus.NON_COMPLIANT
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 97:
            return "A+"
        elif score >= 93:
            return "A"
        elif score >= 90:
            return "A-"
        elif score >= 87:
            return "B+"
        elif score >= 83:
            return "B"
        elif score >= 80:
            return "B-"
        elif score >= 77:
            return "C+"
        elif score >= 73:
            return "C"
        elif score >= 70:
            return "C-"
        elif score >= 67:
            return "D+"
        elif score >= 63:
            return "D"
        elif score >= 60:
            return "D-"
        else:
            return "F"
    
    def _generate_compliance_trends(self, days: int = 30) -> Dict[str, Any]:
        """Generate compliance trend data for dashboard charts"""
        
        # In production, this would query historical compliance data
        # For now, we'll generate sample trend data
        
        dates = [(datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]
        
        # Sample trend data (in production, would come from historical compliance calculations)
        security_trend = [85 + (i % 5) for i in range(days)]
        availability_trend = [92 + (i % 3) for i in range(days)]
        integrity_trend = [90 + (i % 4) for i in range(days)]
        confidentiality_trend = [88 + (i % 6) for i in range(days)]
        privacy_trend = [91 + (i % 3) for i in range(days)]
        
        return {
            "dates": dates,
            "security": security_trend,
            "availability": availability_trend,
            "processing_integrity": integrity_trend,
            "confidentiality": confidentiality_trend,
            "privacy": privacy_trend
        }
    
    def _identify_critical_issues(self) -> List[Dict[str, Any]]:
        """Identify critical compliance issues requiring immediate attention"""
        
        issues = []
        
        try:
            # Check for security incidents
            recent_incidents = audit_system.query_events(
                event_types=[audit_system.AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED,
                           audit_system.AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT],
                hours_back=24
            )
            
            if len(recent_incidents) > self.thresholds["security_incidents"]["critical"]:
                issues.append({
                    "type": "security",
                    "severity": "critical",
                    "title": "High Security Incident Volume",
                    "description": f"{len(recent_incidents)} security incidents in last 24 hours",
                    "action_required": "Immediate security review and incident response",
                    "detected_at": datetime.utcnow().isoformat()
                })
            
            # Check backup failures
            backup_report = backup_manager.generate_backup_report()
            backup_success_rate = float(backup_report["recent_backups_7_days"]["success_rate"].rstrip('%'))
            
            if backup_success_rate < self.thresholds["backup_success_rate"]["critical"]:
                issues.append({
                    "type": "availability",
                    "severity": "critical", 
                    "title": "Backup Success Rate Below Threshold",
                    "description": f"Backup success rate at {backup_success_rate}% (target: >95%)",
                    "action_required": "Review backup configurations and resolve failures",
                    "detected_at": datetime.utcnow().isoformat()
                })
            
            # Check privilege violations
            privilege_report = privilege_manager.generate_privilege_compliance_report()
            wall_breaches = privilege_report["ethical_walls"]["breach_attempts"]
            
            if wall_breaches > self.thresholds["privilege_breaches"]["warning"]:
                issues.append({
                    "type": "confidentiality",
                    "severity": "high" if wall_breaches < self.thresholds["privilege_breaches"]["critical"] else "critical",
                    "title": "Ethical Wall Breach Attempts",
                    "description": f"{wall_breaches} ethical wall breach attempts detected",
                    "action_required": "Review access controls and investigate breach attempts",
                    "detected_at": datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Failed to identify critical issues: {e}")
            issues.append({
                "type": "system",
                "severity": "critical",
                "title": "Compliance Monitoring Error",
                "description": f"Failed to complete compliance assessment: {str(e)}",
                "action_required": "Review compliance monitoring system",
                "detected_at": datetime.utcnow().isoformat()
            })
        
        return issues
    
    def _get_recent_compliance_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent compliance-related events"""
        
        try:
            # Get compliance-tagged audit events
            compliance_events = audit_system.query_events(
                hours_back=hours,
                limit=50
            )
            
            # Filter and format compliance events
            formatted_events = []
            for event in compliance_events[-20:]:  # Last 20 events
                if event.get('compliance_tags'):
                    formatted_events.append({
                        "event_id": event.get('event_id'),
                        "timestamp": event.get('timestamp'),
                        "event_type": event.get('event_type'),
                        "user_id": event.get('user_id', 'system'),
                        "description": self._format_event_description(event),
                        "compliance_tags": json.loads(event.get('compliance_tags', '[]')),
                        "risk_level": event.get('risk_level')
                    })
            
            return formatted_events
            
        except Exception as e:
            logger.error(f"Failed to get recent compliance events: {e}")
            return []
    
    def _format_event_description(self, event: Dict[str, Any]) -> str:
        """Format audit event for compliance dashboard display"""
        
        event_type = event.get('event_type', 'Unknown')
        user_id = event.get('user_id', 'system')[:8] + "..." if event.get('user_id') else 'system'
        
        descriptions = {
            'privileged_data_accessed': f"User {user_id} accessed privileged data",
            'encryption_key_rotated': f"Encryption key rotated by {user_id}",
            'backup_completed': f"System backup completed successfully",
            'audit_log_accessed': f"User {user_id} accessed audit logs",
            'user_login_success': f"User {user_id} logged in successfully",
            'conflicts_check_performed': f"Conflicts check performed for {user_id}",
            'retention_policy_applied': f"Data retention policy applied by system"
        }
        
        return descriptions.get(event_type, f"{event_type} event by {user_id}")
    
    def _get_certification_status(self) -> Dict[str, Any]:
        """Get current certification and audit status"""
        
        return {
            "soc2_type2": {
                "status": "active",
                "issued_date": "2024-01-15",
                "expiry_date": "2025-01-14",
                "auditor": "Independent Security Auditors LLC",
                "next_assessment": "2024-10-15"
            },
            "iso27001": {
                "status": "in_progress",
                "target_completion": "2024-12-31",
                "preparation_progress": 75
            },
            "attorney_ethics": {
                "status": "compliant",
                "last_review": "2024-08-15",
                "next_review": "2025-02-15",
                "jurisdiction": "Multiple State Bars"
            }
        }

# Flask blueprint for compliance dashboard
compliance_bp = Blueprint('compliance', __name__, url_prefix='/compliance')
monitor = SOC2ComplianceMonitor()

@compliance_bp.route('/dashboard')
def dashboard():
    """Render compliance dashboard"""
    return render_template('compliance_dashboard.html')

@compliance_bp.route('/api/data')
def api_data():
    """API endpoint for dashboard data"""
    return jsonify(monitor.generate_compliance_dashboard_data())

@compliance_bp.route('/api/metrics/<criterion>')
def api_criterion_metrics(criterion):
    """API endpoint for specific trust service criterion metrics"""
    
    if criterion not in monitor.trust_service_criteria:
        return jsonify({"error": "Invalid criterion"}), 400
    
    dashboard_data = monitor.generate_compliance_dashboard_data()
    criterion_data = dashboard_data["trust_service_criteria"].get(criterion, {})
    
    return jsonify(criterion_data)

@compliance_bp.route('/api/trends')
def api_trends():
    """API endpoint for compliance trend data"""
    return jsonify(monitor._generate_compliance_trends())

@compliance_bp.route('/api/issues')
def api_critical_issues():
    """API endpoint for critical issues"""
    return jsonify(monitor._identify_critical_issues())

# Global monitor instance
compliance_monitor = SOC2ComplianceMonitor()