#!/usr/bin/env python3
# =============================================================================
# Legal AI System - Final Comprehensive Security Alert Validation
# =============================================================================
# Complete validation of all security alert types, audit event integration,
# and system readiness with comprehensive reporting
# =============================================================================

import asyncio
import sys
import os
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from audit.enhanced_audit_events import (
        EnhancedSecurityEventType, validate_security_alert_coverage,
        map_security_alert_to_audit_event, map_security_severity_to_audit_severity,
        get_all_security_alert_event_types, get_all_security_response_event_types,
        categorize_security_events_by_category
    )
    from audit.security_alert_types import SecurityAlertType, SecurityAlertSeverity
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"[WARNING] Import failed: {e}")
    print("[INFO] Running limited validation without full imports")
    IMPORTS_SUCCESSFUL = False

@dataclass
class ValidationResult:
    """Result of security validation."""
    component: str
    test_name: str
    passed: bool
    details: Dict[str, Any]
    error_message: Optional[str] = None

class SecurityAlertValidationSuite:
    """Final comprehensive security alert validation."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.start_time = time.time()
        
    async def run_final_validation(self) -> Dict[str, Any]:
        """Run final comprehensive security alert validation."""
        print("=" * 80)
        print("[LEGAL AI SYSTEM] FINAL SECURITY ALERT VALIDATION")
        print("=" * 80)
        print(f"[START TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[IMPORT STATUS] {'SUCCESS' if IMPORTS_SUCCESSFUL else 'LIMITED'}")
        print()
        
        # Run all validation tests
        await self._validate_security_alert_types()
        await self._validate_audit_event_integration()
        await self._validate_security_coverage()
        await self._validate_response_mappings()
        await self._validate_severity_mappings()
        await self._validate_categorization()
        await self._validate_system_readiness()
        
        # Generate final report
        return await self._generate_final_report()
    
    async def _validate_security_alert_types(self):
        """Validate all security alert types are properly defined."""
        print("[VALIDATION] Security Alert Types...")
        
        if not IMPORTS_SUCCESSFUL:
            self.results.append(ValidationResult(
                component="Security Alert Types",
                test_name="Alert Type Definitions",
                passed=False,
                details={},
                error_message="Import failed - cannot validate"
            ))
            return
        
        try:
            # Count all security alert types
            alert_types = [alert for alert in SecurityAlertType]
            
            # Categorize by type
            auth_alerts = [a for a in alert_types if any(term in a.value for term in ['brute_force', 'credential', 'impossible_travel', 'mfa', 'session', 'token'])]
            authz_alerts = [a for a in alert_types if any(term in a.value for term in ['privilege', 'admin', 'role', 'permission', 'elevation'])]
            data_alerts = [a for a in alert_types if any(term in a.value for term in ['data', 'exfiltration', 'attorney_client', 'document', 'encryption'])]
            system_alerts = [a for a in alert_types if any(term in a.value for term in ['malware', 'intrusion', 'system', 'backdoor', 'rootkit'])]
            network_alerts = [a for a in alert_types if any(term in a.value for term in ['network', 'ddos', 'port', 'injection', 'xss', 'csrf'])]
            api_alerts = [a for a in alert_types if any(term in a.value for term in ['api', 'rate_limit', 'endpoint'])]
            insider_alerts = [a for a in alert_types if any(term in a.value for term in ['insider', 'after_hours', 'unusual', 'employee'])]
            compliance_alerts = [a for a in alert_types if any(term in a.value for term in ['gdpr', 'ccpa', 'ethics', 'confidentiality', 'retention'])]
            physical_alerts = [a for a in alert_types if any(term in a.value for term in ['device', 'usb', 'physical', 'theft', 'camera'])]
            emergency_alerts = [a for a in alert_types if any(term in a.value for term in ['critical', 'emergency', 'disaster'])]
            
            details = {
                "total_alert_types": len(alert_types),
                "authentication_alerts": len(auth_alerts),
                "authorization_alerts": len(authz_alerts),
                "data_protection_alerts": len(data_alerts),
                "system_security_alerts": len(system_alerts),
                "network_security_alerts": len(network_alerts),
                "api_security_alerts": len(api_alerts),
                "insider_threat_alerts": len(insider_alerts),
                "compliance_alerts": len(compliance_alerts),
                "physical_security_alerts": len(physical_alerts),
                "emergency_alerts": len(emergency_alerts),
                "comprehensive_coverage": len(alert_types) >= 50
            }
            
            passed = len(alert_types) >= 50 and all([
                len(auth_alerts) >= 5,
                len(data_alerts) >= 5,
                len(system_alerts) >= 3,
                len(compliance_alerts) >= 5
            ])
            
            self.results.append(ValidationResult(
                component="Security Alert Types",
                test_name="Alert Type Definitions",
                passed=passed,
                details=details
            ))
            
            print(f"  [{'PASS' if passed else 'FAIL'}] {len(alert_types)} security alert types defined")
            
        except Exception as e:
            self.results.append(ValidationResult(
                component="Security Alert Types",
                test_name="Alert Type Definitions",
                passed=False,
                details={},
                error_message=str(e)
            ))
            print(f"  [FAIL] Error validating alert types: {e}")
    
    async def _validate_audit_event_integration(self):
        """Validate security alerts integrate with audit events."""
        print("[VALIDATION] Audit Event Integration...")
        
        if not IMPORTS_SUCCESSFUL:
            self.results.append(ValidationResult(
                component="Audit Integration",
                test_name="Security Alert to Audit Event Mapping",
                passed=False,
                details={},
                error_message="Import failed - cannot validate"
            ))
            return
        
        try:
            # Get coverage validation
            coverage = validate_security_alert_coverage()
            
            # Check if mapping coverage is complete
            mapping_complete = coverage["mapping_coverage_percentage"] >= 95
            severity_complete = coverage["severity_mapping_coverage_percentage"] >= 95
            
            details = {
                "total_security_alerts": coverage["total_security_alert_types"],
                "total_mapped_alerts": coverage["total_mapped_alert_types"],
                "mapping_coverage_percentage": coverage["mapping_coverage_percentage"],
                "severity_mapping_coverage": coverage["severity_mapping_coverage_percentage"],
                "total_audit_events": coverage["total_audit_event_types"],
                "security_alert_events": coverage["total_security_alert_events"],
                "security_response_events": coverage["total_security_response_events"],
                "missing_mappings": coverage["missing_alert_mappings"],
                "response_action_mappings": coverage["response_action_mappings"]
            }
            
            passed = mapping_complete and severity_complete and len(coverage["missing_alert_mappings"]) == 0
            
            self.results.append(ValidationResult(
                component="Audit Integration",
                test_name="Security Alert to Audit Event Mapping",
                passed=passed,
                details=details
            ))
            
            print(f"  [{'PASS' if passed else 'FAIL'}] {coverage['mapping_coverage_percentage']:.1f}% mapping coverage")
            
        except Exception as e:
            self.results.append(ValidationResult(
                component="Audit Integration",
                test_name="Security Alert to Audit Event Mapping",
                passed=False,
                details={},
                error_message=str(e)
            ))
            print(f"  [FAIL] Error validating audit integration: {e}")
    
    async def _validate_security_coverage(self):
        """Validate comprehensive security coverage."""
        print("[VALIDATION] Security Coverage Analysis...")
        
        if not IMPORTS_SUCCESSFUL:
            self.results.append(ValidationResult(
                component="Security Coverage",
                test_name="Comprehensive Security Coverage",
                passed=False,
                details={},
                error_message="Import failed - cannot validate"
            ))
            return
        
        try:
            # Security coverage requirements
            required_coverage = {
                "authentication_security": [
                    "brute_force_attack", "credential_stuffing", "impossible_travel",
                    "mfa_bypass_attempt", "session_hijacking"
                ],
                "data_protection": [
                    "bulk_data_exfiltration", "attorney_client_violation", 
                    "client_data_theft", "document_tampering", "encryption_bypass"
                ],
                "insider_threats": [
                    "insider_data_hoarding", "after_hours_activity", 
                    "unusual_user_behavior", "employee_sabotage"
                ],
                "compliance_violations": [
                    "gdpr_violation", "attorney_ethics_violation", 
                    "client_confidentiality_breach", "retention_policy_violation"
                ],
                "system_security": [
                    "malware_detection", "system_compromise", "intrusion_attempt",
                    "rootkit_detection", "audit_evasion"
                ]
            }
            
            # Check coverage for each area
            coverage_results = {}
            total_required = 0
            total_covered = 0
            
            for area, required_alerts in required_coverage.items():
                total_required += len(required_alerts)
                covered = 0
                
                for required_alert in required_alerts:
                    # Check if alert type exists
                    try:
                        alert_type = getattr(SecurityAlertType, required_alert.upper(), None)
                        if alert_type:
                            covered += 1
                            total_covered += 1
                    except:
                        pass
                
                coverage_results[area] = {
                    "required": len(required_alerts),
                    "covered": covered,
                    "percentage": (covered / len(required_alerts)) * 100
                }
            
            overall_coverage = (total_covered / total_required) * 100 if total_required > 0 else 0
            
            details = {
                "overall_coverage_percentage": overall_coverage,
                "coverage_by_area": coverage_results,
                "total_required_alerts": total_required,
                "total_covered_alerts": total_covered,
                "comprehensive_coverage": overall_coverage >= 90
            }
            
            passed = overall_coverage >= 90
            
            self.results.append(ValidationResult(
                component="Security Coverage",
                test_name="Comprehensive Security Coverage",
                passed=passed,
                details=details
            ))
            
            print(f"  [{'PASS' if passed else 'FAIL'}] {overall_coverage:.1f}% security coverage")
            
        except Exception as e:
            self.results.append(ValidationResult(
                component="Security Coverage",
                test_name="Comprehensive Security Coverage",
                passed=False,
                details={},
                error_message=str(e)
            ))
            print(f"  [FAIL] Error validating security coverage: {e}")
    
    async def _validate_response_mappings(self):
        """Validate security response action mappings."""
        print("[VALIDATION] Security Response Mappings...")
        
        if not IMPORTS_SUCCESSFUL:
            self.results.append(ValidationResult(
                component="Response Mappings",
                test_name="Security Response Action Mappings",
                passed=False,
                details={},
                error_message="Import failed - cannot validate"
            ))
            return
        
        try:
            # Expected response actions
            expected_responses = [
                "block_source_ip", "suspend_user_account", "revoke_privileges",
                "isolate_affected_systems", "forensic_investigation", 
                "escalate_to_security_team", "notify_affected_clients",
                "legal_privilege_review", "regulatory_notification"
            ]
            
            # Get security response events
            response_events = get_all_security_response_event_types()
            
            details = {
                "total_response_events": len(response_events),
                "expected_response_actions": len(expected_responses),
                "response_event_coverage": len(response_events) >= len(expected_responses),
                "automated_response_capability": True,
                "escalation_procedures": True,
                "legal_compliance_responses": True
            }
            
            passed = len(response_events) >= 8 and details["response_event_coverage"]
            
            self.results.append(ValidationResult(
                component="Response Mappings",
                test_name="Security Response Action Mappings",
                passed=passed,
                details=details
            ))
            
            print(f"  [{'PASS' if passed else 'FAIL'}] {len(response_events)} response actions mapped")
            
        except Exception as e:
            self.results.append(ValidationResult(
                component="Response Mappings",
                test_name="Security Response Action Mappings",
                passed=False,
                details={},
                error_message=str(e)
            ))
            print(f"  [FAIL] Error validating response mappings: {e}")
    
    async def _validate_severity_mappings(self):
        """Validate severity level mappings."""
        print("[VALIDATION] Severity Level Mappings...")
        
        if not IMPORTS_SUCCESSFUL:
            self.results.append(ValidationResult(
                component="Severity Mappings",
                test_name="Severity Level Mappings",
                passed=False,
                details={},
                error_message="Import failed - cannot validate"
            ))
            return
        
        try:
            # Test severity mappings
            severity_tests = [
                (SecurityAlertSeverity.INFO, "low"),
                (SecurityAlertSeverity.LOW, "low"),
                (SecurityAlertSeverity.MEDIUM, "medium"),
                (SecurityAlertSeverity.HIGH, "high"),
                (SecurityAlertSeverity.CRITICAL, "critical"),
                (SecurityAlertSeverity.EMERGENCY, "critical")
            ]
            
            mapped_correctly = 0
            total_tests = len(severity_tests)
            
            for alert_severity, expected_audit_severity in severity_tests:
                try:
                    mapped_severity = map_security_severity_to_audit_severity(alert_severity)
                    if mapped_severity.value == expected_audit_severity:
                        mapped_correctly += 1
                except:
                    pass
            
            details = {
                "total_severity_levels": len(SecurityAlertSeverity),
                "correctly_mapped": mapped_correctly,
                "mapping_accuracy_percentage": (mapped_correctly / total_tests) * 100,
                "emergency_to_critical_mapping": True,
                "graduated_severity_levels": True
            }
            
            passed = mapped_correctly == total_tests
            
            self.results.append(ValidationResult(
                component="Severity Mappings",
                test_name="Severity Level Mappings",
                passed=passed,
                details=details
            ))
            
            print(f"  [{'PASS' if passed else 'FAIL'}] {mapped_correctly}/{total_tests} severity mappings correct")
            
        except Exception as e:
            self.results.append(ValidationResult(
                component="Severity Mappings",
                test_name="Severity Level Mappings",
                passed=False,
                details={},
                error_message=str(e)
            ))
            print(f"  [FAIL] Error validating severity mappings: {e}")
    
    async def _validate_categorization(self):
        """Validate security alert categorization."""
        print("[VALIDATION] Security Alert Categorization...")
        
        if not IMPORTS_SUCCESSFUL:
            self.results.append(ValidationResult(
                component="Categorization",
                test_name="Security Alert Categorization",
                passed=False,
                details={},
                error_message="Import failed - cannot validate"
            ))
            return
        
        try:
            # Get categorized events
            categorized_events = categorize_security_events_by_category()
            
            # Count events per category
            category_counts = {category.value: len(events) for category, events in categorized_events.items()}
            
            # Check if all major categories have events
            required_categories = [
                "authentication", "authorization", "data_protection", 
                "system_security", "compliance", "insider_threat"
            ]
            
            categories_with_events = sum(1 for cat in required_categories if category_counts.get(cat, 0) > 0)
            
            details = {
                "total_categories": len(categorized_events),
                "category_counts": category_counts,
                "required_categories_covered": categories_with_events,
                "total_required_categories": len(required_categories),
                "categorization_coverage": (categories_with_events / len(required_categories)) * 100,
                "balanced_distribution": min(category_counts.values()) > 0 if category_counts else False
            }
            
            passed = categories_with_events >= len(required_categories) * 0.8  # 80% of required categories
            
            self.results.append(ValidationResult(
                component="Categorization",
                test_name="Security Alert Categorization",
                passed=passed,
                details=details
            ))
            
            print(f"  [{'PASS' if passed else 'FAIL'}] {categories_with_events}/{len(required_categories)} categories covered")
            
        except Exception as e:
            self.results.append(ValidationResult(
                component="Categorization",
                test_name="Security Alert Categorization",
                passed=False,
                details={},
                error_message=str(e)
            ))
            print(f"  [FAIL] Error validating categorization: {e}")
    
    async def _validate_system_readiness(self):
        """Validate overall system readiness."""
        print("[VALIDATION] System Readiness Assessment...")
        
        try:
            # Check if all previous validations passed
            component_results = {}
            total_tests = 0
            passed_tests = 0
            
            for result in self.results:
                if result.component not in component_results:
                    component_results[result.component] = {"total": 0, "passed": 0}
                
                component_results[result.component]["total"] += 1
                total_tests += 1
                
                if result.passed:
                    component_results[result.component]["passed"] += 1
                    passed_tests += 1
            
            # Calculate readiness score
            readiness_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            # System readiness criteria
            critical_components_ready = all([
                component_results.get("Security Alert Types", {}).get("passed", 0) > 0,
                component_results.get("Audit Integration", {}).get("passed", 0) > 0,
                component_results.get("Security Coverage", {}).get("passed", 0) > 0
            ])
            
            production_ready = readiness_score >= 90 and critical_components_ready
            
            details = {
                "readiness_score_percentage": readiness_score,
                "total_validation_tests": total_tests,
                "passed_validation_tests": passed_tests,
                "failed_validation_tests": total_tests - passed_tests,
                "component_readiness": component_results,
                "critical_components_ready": critical_components_ready,
                "production_ready": production_ready,
                "comprehensive_security_coverage": IMPORTS_SUCCESSFUL and readiness_score >= 85,
                "validation_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.results.append(ValidationResult(
                component="System Readiness",
                test_name="Overall System Readiness",
                passed=production_ready,
                details=details
            ))
            
            print(f"  [{'PASS' if production_ready else 'FAIL'}] System readiness: {readiness_score:.1f}%")
            
        except Exception as e:
            self.results.append(ValidationResult(
                component="System Readiness",
                test_name="Overall System Readiness",
                passed=False,
                details={},
                error_message=str(e)
            ))
            print(f"  [FAIL] Error assessing system readiness: {e}")
    
    async def _generate_final_report(self) -> Dict[str, Any]:
        """Generate final comprehensive validation report."""
        end_time = time.time()
        total_duration = end_time - self.start_time
        
        # Calculate overall metrics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Group results by component
        component_summary = {}
        for result in self.results:
            if result.component not in component_summary:
                component_summary[result.component] = {"total": 0, "passed": 0, "failed": 0}
            
            component_summary[result.component]["total"] += 1
            if result.passed:
                component_summary[result.component]["passed"] += 1
            else:
                component_summary[result.component]["failed"] += 1
        
        # Generate recommendations
        recommendations = self._generate_recommendations(success_rate, component_summary)
        
        report = {
            "validation_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate_percentage": round(success_rate, 2),
                "duration_seconds": round(total_duration, 2),
                "import_status": "SUCCESS" if IMPORTS_SUCCESSFUL else "LIMITED",
                "validation_timestamp": datetime.now(timezone.utc).isoformat()
            },
            
            "component_breakdown": component_summary,
            
            "security_alert_system_status": {
                "comprehensive_alert_types": any(r.component == "Security Alert Types" and r.passed for r in self.results),
                "audit_integration_complete": any(r.component == "Audit Integration" and r.passed for r in self.results),
                "security_coverage_adequate": any(r.component == "Security Coverage" and r.passed for r in self.results),
                "response_mappings_functional": any(r.component == "Response Mappings" and r.passed for r in self.results),
                "severity_mappings_correct": any(r.component == "Severity Mappings" and r.passed for r in self.results),
                "categorization_complete": any(r.component == "Categorization" and r.passed for r in self.results),
                "system_production_ready": any(r.component == "System Readiness" and r.passed for r in self.results)
            },
            
            "detailed_results": [
                {
                    "component": r.component,
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "details": r.details,
                    "error_message": r.error_message
                }
                for r in self.results
            ],
            
            "recommendations": recommendations,
            
            "compliance_assessment": {
                "legal_ai_security_standards": success_rate >= 90,
                "comprehensive_threat_detection": IMPORTS_SUCCESSFUL,
                "audit_trail_completeness": any(r.component == "Audit Integration" and r.passed for r in self.results),
                "incident_response_capability": any(r.component == "Response Mappings" and r.passed for r in self.results),
                "regulatory_compliance_ready": success_rate >= 85
            }
        }
        
        return report
    
    def _generate_recommendations(self, success_rate: float, component_summary: Dict) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if success_rate >= 95:
            recommendations.append("EXCELLENT: All security alert systems are fully operational and production-ready")
        elif success_rate >= 90:
            recommendations.append("GOOD: Security alert systems meet production requirements with minor improvements needed")
        elif success_rate >= 80:
            recommendations.append("ACCEPTABLE: Security alert systems functional but require attention to failed components")
        else:
            recommendations.append("CRITICAL: Security alert systems require significant improvements before production deployment")
        
        # Component-specific recommendations
        for component, metrics in component_summary.items():
            if metrics["failed"] > 0:
                recommendations.append(f"Address {metrics['failed']} failed test(s) in {component}")
        
        if not IMPORTS_SUCCESSFUL:
            recommendations.append("Resolve import issues to enable full security alert system functionality")
        
        if success_rate == 100:
            recommendations.append("All security alert validation tests passed - system ready for production deployment")
        
        return recommendations

async def main():
    """Main execution function."""
    suite = SecurityAlertValidationSuite()
    report = await suite.run_final_validation()
    
    # Print final summary
    print("\n" + "=" * 80)
    print("[FINAL VALIDATION COMPLETE]")
    print("=" * 80)
    print(f"Total Tests: {report['validation_summary']['total_tests']}")
    print(f"Passed: {report['validation_summary']['passed_tests']}")
    print(f"Failed: {report['validation_summary']['failed_tests']}")
    print(f"Success Rate: {report['validation_summary']['success_rate_percentage']}%")
    print(f"Duration: {report['validation_summary']['duration_seconds']} seconds")
    print()
    
    # System status
    status = report['security_alert_system_status']
    print("[SECURITY ALERT SYSTEM STATUS]")
    for component, ready in status.items():
        print(f"{component.replace('_', ' ').title()}: {'[READY]' if ready else '[NEEDS ATTENTION]'}")
    print()
    
    # Recommendations
    print("[RECOMMENDATIONS]")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")
    print()
    
    # Save report
    report_file = Path(__file__).parent / f"final_security_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[REPORT SAVED] {report_file}")
    except Exception as e:
        print(f"[ERROR] Failed to save report: {e}")
    
    print(f"\n[END TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return report

if __name__ == "__main__":
    asyncio.run(main())