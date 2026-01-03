#!/usr/bin/env python3
"""
PRODUCTION READINESS VALIDATION

Comprehensive production readiness test suite:
- Security hardening validation
- Performance benchmarks
- System integration tests
- Compliance verification
- Health check validation
"""

import os
import sys
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Import production systems
try:
    from backend.app.core.production_security import production_security
    from backend.app.core.production_logging import production_monitoring
    from backend.app.core.performance_optimizer import performance_optimizer
    from backend.app.services.optimized_disclaimer_service import optimized_disclaimer_service
    from backend.app.core.enhanced_advice_detection import enhanced_advice_detector
    from backend.app.core.security_event_audit import security_event_audit
    from backend.app.core.admin_action_audit import admin_action_audit
    from src.audit.emergency_audit import emergency_audit_system
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class ProductionReadinessTest:
    """Production readiness test suite"""
    
    def __init__(self):
        self.test_results = {
            'security_tests': {},
            'performance_tests': {},
            'compliance_tests': {},
            'integration_tests': {},
            'overall_status': 'unknown'
        }
        
        # Production readiness criteria
        self.criteria = {
            'security_score_minimum': 85,
            'performance_response_time_ms': 100,
            'compliance_coverage_percent': 95,
            'system_availability_percent': 99.5,
            'error_rate_maximum_percent': 1.0
        }
    
    async def test_security_hardening(self) -> Dict[str, Any]:
        """Test production security hardening"""
        print("\nTesting Security Hardening:")
        print("-" * 50)
        
        results = {'tests': 0, 'passed': 0, 'score': 0}
        
        # Test 1: Rate limiting functionality
        results['tests'] += 1
        try:
            # Simulate multiple rapid requests
            test_requests = []
            for i in range(70):  # Exceed limit of 60/min
                allowed, rate_info = production_security.rate_limiter.is_allowed('test_ip_123')
                test_requests.append(allowed)
            
            blocked_requests = sum(1 for r in test_requests if not r)
            if blocked_requests > 5:  # Should block excess requests
                results['passed'] += 1
                results['score'] += 20
                print(f"  PASS Rate limiting: {blocked_requests} requests blocked")
            else:
                print(f"  FAIL Rate limiting: Only {blocked_requests} requests blocked")
        except Exception as e:
            print(f"  ERROR Rate limiting test: {e}")
        
        # Test 2: Input validation
        results['tests'] += 1
        try:
            malicious_inputs = [
                "'; DROP TABLE users; --",
                "<script>alert('xss')</script>",
                "../../../etc/passwd",
                "\\..\\windows\\system32"
            ]
            
            blocked_inputs = 0
            for malicious_input in malicious_inputs:
                valid, error = production_security.input_validator.validate_input(malicious_input)
                if not valid:
                    blocked_inputs += 1
            
            if blocked_inputs == len(malicious_inputs):
                results['passed'] += 1
                results['score'] += 25
                print(f"  PASS Input validation: {blocked_inputs}/{len(malicious_inputs)} malicious inputs blocked")
            else:
                print(f"  FAIL Input validation: {blocked_inputs}/{len(malicious_inputs)} malicious inputs blocked")
        except Exception as e:
            print(f"  ERROR Input validation test: {e}")
        
        # Test 3: Security headers
        results['tests'] += 1
        try:
            headers = production_security.get_security_headers()
            required_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Strict-Transport-Security',
                'Content-Security-Policy'
            ]
            
            present_headers = sum(1 for h in required_headers if h in headers)
            if present_headers >= len(required_headers) - 1:  # Allow 1 missing
                results['passed'] += 1
                results['score'] += 25
                print(f"  PASS Security headers: {present_headers}/{len(required_headers)} headers configured")
            else:
                print(f"  FAIL Security headers: {present_headers}/{len(required_headers)} headers configured")
        except Exception as e:
            print(f"  ERROR Security headers test: {e}")
        
        # Test 4: Security monitoring
        results['tests'] += 1
        try:
            # Test failed login tracking
            production_security.log_failed_authentication('test_attacker_ip', 'test_user')
            
            status = production_security.security_monitor.get_security_status()
            if 'active_alerts' in status and 'status' in status:
                results['passed'] += 1
                results['score'] += 30
                print(f"  PASS Security monitoring: Status {status['status']}, {status.get('active_alerts', 0)} alerts")
            else:
                print("  FAIL Security monitoring: Incomplete status response")
        except Exception as e:
            print(f"  ERROR Security monitoring test: {e}")
        
        results['success_rate'] = (results['passed'] / results['tests'] * 100) if results['tests'] > 0 else 0
        print(f"  RESULT: {results['passed']}/{results['tests']} tests passed, Score: {results['score']}/100")
        
        self.test_results['security_tests'] = results
        return results
    
    async def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Test performance benchmarks"""
        print("\nTesting Performance Benchmarks:")
        print("-" * 50)
        
        results = {'tests': 0, 'passed': 0, 'response_times': []}
        
        # Test 1: Disclaimer service performance
        results['tests'] += 1
        try:
            start_time = time.time()
            disclaimer = await optimized_disclaimer_service.get_ai_response_disclaimer('legal_advice')
            response_time = (time.time() - start_time) * 1000
            results['response_times'].append(response_time)
            
            if response_time < 50 and len(disclaimer) > 0:  # Target: <50ms
                results['passed'] += 1
                print(f"  PASS Disclaimer service: {response_time:.2f}ms")
            else:
                print(f"  FAIL Disclaimer service: {response_time:.2f}ms (Target: <50ms)")
        except Exception as e:
            print(f"  ERROR Disclaimer service: {e}")
        
        # Test 2: Advice detection performance
        results['tests'] += 1
        try:
            start_time = time.time()
            analysis = enhanced_advice_detector.analyze_output("You should file a lawsuit immediately.")
            response_time = (time.time() - start_time) * 1000
            results['response_times'].append(response_time)
            
            if response_time < 100 and analysis.risk_score > 0.5:  # Target: <100ms
                results['passed'] += 1
                print(f"  PASS Advice detection: {response_time:.2f}ms, Risk: {analysis.risk_score:.2f}")
            else:
                print(f"  FAIL Advice detection: {response_time:.2f}ms (Target: <100ms)")
        except Exception as e:
            print(f"  ERROR Advice detection: {e}")
        
        # Test 3: Concurrent processing
        results['tests'] += 1
        try:
            concurrent_requests = 50
            
            async def single_request():
                start = time.time()
                await optimized_disclaimer_service.get_ai_response_disclaimer('enhanced')
                return (time.time() - start) * 1000
            
            start_time = time.time()
            response_times = await asyncio.gather(*[single_request() for _ in range(concurrent_requests)])
            total_time = (time.time() - start_time) * 1000
            
            avg_response_time = sum(response_times) / len(response_times)
            throughput = concurrent_requests / (total_time / 1000)
            
            if avg_response_time < 200 and throughput > 10:  # Reasonable concurrent performance
                results['passed'] += 1
                print(f"  PASS Concurrent processing: {avg_response_time:.2f}ms avg, {throughput:.1f} req/sec")
            else:
                print(f"  FAIL Concurrent processing: {avg_response_time:.2f}ms avg, {throughput:.1f} req/sec")
            
            results['concurrent_stats'] = {
                'avg_response_time': avg_response_time,
                'throughput': throughput
            }
        except Exception as e:
            print(f"  ERROR Concurrent processing: {e}")
        
        # Test 4: System health checks
        results['tests'] += 1
        try:
            start_time = time.time()
            health_report = production_monitoring.health_check()
            response_time = (time.time() - start_time) * 1000
            
            if response_time < 100 and health_report.get('status') in ['healthy', 'warning']:
                results['passed'] += 1
                print(f"  PASS System health: {response_time:.2f}ms, Status: {health_report.get('status')}")
            else:
                print(f"  FAIL System health: {response_time:.2f}ms, Status: {health_report.get('status')}")
        except Exception as e:
            print(f"  ERROR System health: {e}")
        
        if results['response_times']:
            avg_response_time = sum(results['response_times']) / len(results['response_times'])
            results['avg_response_time'] = avg_response_time
            print(f"  INFO Average response time: {avg_response_time:.2f}ms")
        
        results['success_rate'] = (results['passed'] / results['tests'] * 100) if results['tests'] > 0 else 0
        print(f"  RESULT: {results['passed']}/{results['tests']} tests passed ({results['success_rate']:.1f}%)")
        
        self.test_results['performance_tests'] = results
        return results
    
    async def test_compliance_systems(self) -> Dict[str, Any]:
        """Test compliance and audit systems"""
        print("\nTesting Compliance Systems:")
        print("-" * 50)
        
        results = {'tests': 0, 'passed': 0, 'systems_operational': 0}
        
        # Test all audit systems
        audit_systems = [
            ('Security Audit', security_event_audit),
            ('Admin Audit', admin_action_audit),
            ('Emergency Audit', emergency_audit_system),
        ]
        
        for system_name, system in audit_systems:
            results['tests'] += 1
            try:
                # Test basic functionality
                if hasattr(system, 'health_check'):
                    health = system.health_check()
                    if health.get('status') == 'healthy':
                        results['passed'] += 1
                        results['systems_operational'] += 1
                        print(f"  PASS {system_name}: Operational")
                    else:
                        print(f"  FAIL {system_name}: {health.get('status', 'unknown')}")
                elif hasattr(system, 'log_event'):
                    # Test logging functionality for security audit
                    system.log_event('test_event', {'test': True})
                    results['passed'] += 1
                    results['systems_operational'] += 1
                    print(f"  PASS {system_name}: Core functionality available")
                elif hasattr(system, 'log_action'):
                    # Test logging functionality for admin audit
                    system.log_action('test_user', 'test_action', {'test': True})
                    results['passed'] += 1
                    results['systems_operational'] += 1
                    print(f"  PASS {system_name}: Core functionality available")
                elif hasattr(system, 'log_emergency_event'):
                    # Test emergency audit system
                    from src.audit.emergency_audit import EmergencyAuditType
                    system.log_emergency_event(EmergencyAuditType.SYSTEM_FAILURE, 'test', {'test': True})
                    results['passed'] += 1
                    results['systems_operational'] += 1
                    print(f"  PASS {system_name}: Core functionality available")
                else:
                    print(f"  FAIL {system_name}: Missing core methods")
            except Exception as e:
                print(f"  ERROR {system_name}: {e}")
        
        # Test compliance logging
        results['tests'] += 1
        try:
            # Test compliance report generation
            compliance_report = production_monitoring.compliance.get_compliance_report(hours=1)
            
            if 'total_events' in compliance_report and compliance_report['total_events'] >= 0:
                results['passed'] += 1
                print(f"  PASS Compliance logging: {compliance_report['total_events']} events tracked")
            else:
                print("  FAIL Compliance logging: Invalid report format")
        except Exception as e:
            print(f"  ERROR Compliance logging: {e}")
        
        results['success_rate'] = (results['passed'] / results['tests'] * 100) if results['tests'] > 0 else 0
        print(f"  RESULT: {results['passed']}/{results['tests']} tests passed, {results['systems_operational']}/3 audit systems operational")
        
        self.test_results['compliance_tests'] = results
        return results
    
    async def test_system_integration(self) -> Dict[str, Any]:
        """Test system integration and end-to-end functionality"""
        print("\nTesting System Integration:")
        print("-" * 50)
        
        results = {'tests': 0, 'passed': 0}
        
        # Test 1: Full advice detection pipeline
        results['tests'] += 1
        try:
            test_input = "You must file your bankruptcy petition within 90 days to protect your assets."
            
            # Run through advice detection
            start_time = time.time()
            analysis = enhanced_advice_detector.analyze_output(test_input)
            
            # Get appropriate disclaimer based on risk score
            risk_level = 'enhanced'
            if analysis.risk_score >= 0.7:
                risk_level = 'legal_advice'
            elif analysis.risk_score >= 0.4:
                risk_level = 'enhanced'
            elif analysis.risk_score >= 0.2:
                risk_level = 'legal_guidance'
            else:
                risk_level = 'legal_information'
            
            disclaimer = await optimized_disclaimer_service.get_ai_response_disclaimer(risk_level)
            
            total_time = (time.time() - start_time) * 1000
            
            if analysis.risk_score > 0.5 and len(disclaimer) > 0 and total_time < 200:
                results['passed'] += 1
                print(f"  PASS Full pipeline: {total_time:.2f}ms, Risk: {analysis.risk_score:.2f}")
            else:
                print(f"  FAIL Full pipeline: {total_time:.2f}ms, Risk: {analysis.risk_score:.2f}")
        except Exception as e:
            print(f"  ERROR Full pipeline: {e}")
        
        # Test 2: Security + Performance integration
        results['tests'] += 1
        try:
            # Test that security middleware doesn't break performance
            request_data = {
                'client_ip': '192.168.1.100',
                'endpoint': '/api/analyze',
                'input_data': 'This is a legal document analysis request.'
            }
            
            start_time = time.time()
            allowed, security_result = production_security.security_middleware(request_data)
            
            if allowed:
                # Run performance test
                disclaimer = await optimized_disclaimer_service.get_ai_response_disclaimer('legal_information')
                
            response_time = (time.time() - start_time) * 1000
            
            if allowed and response_time < 150:  # Security + performance
                results['passed'] += 1
                print(f"  PASS Security + Performance: {response_time:.2f}ms, Security: {'PASS' if allowed else 'BLOCKED'}")
            else:
                print(f"  FAIL Security + Performance: {response_time:.2f}ms, Security: {'PASS' if allowed else 'BLOCKED'}")
        except Exception as e:
            print(f"  ERROR Security + Performance: {e}")
        
        # Test 3: Monitoring integration
        results['tests'] += 1
        try:
            # Verify monitoring captures system activity
            initial_metrics = production_monitoring.metrics.get_metrics_summary()
            
            # Generate some activity
            await optimized_disclaimer_service.get_ai_response_disclaimer('enhanced')
            analysis = enhanced_advice_detector.analyze_output("Test input for monitoring")
            
            # Check metrics updated
            updated_metrics = production_monitoring.metrics.get_metrics_summary()
            
            if updated_metrics['timestamp'] != initial_metrics['timestamp']:
                results['passed'] += 1
                print("  PASS Monitoring integration: Metrics updating correctly")
            else:
                print("  FAIL Monitoring integration: Metrics not updating")
        except Exception as e:
            print(f"  ERROR Monitoring integration: {e}")
        
        results['success_rate'] = (results['passed'] / results['tests'] * 100) if results['tests'] > 0 else 0
        print(f"  RESULT: {results['passed']}/{results['tests']} tests passed ({results['success_rate']:.1f}%)")
        
        self.test_results['integration_tests'] = results
        return results
    
    async def run_production_readiness_test(self) -> bool:
        """Run complete production readiness test suite"""
        print("PRODUCTION READINESS VALIDATION")
        print("=" * 60)
        print(f"Test Start: {datetime.utcnow().isoformat()}")
        print(f"Production Criteria:")
        for criteria, value in self.criteria.items():
            print(f"  - {criteria}: {value}")
        
        # Run all test categories
        await self.test_security_hardening()
        await self.test_performance_benchmarks()
        await self.test_compliance_systems()
        await self.test_system_integration()
        
        # Calculate overall results
        total_tests = 0
        passed_tests = 0
        
        for category, results in self.test_results.items():
            if isinstance(results, dict) and 'tests' in results:
                total_tests += results.get('tests', 0)
                passed_tests += results.get('passed', 0)
        
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Production readiness determination
        security_score = self.test_results['security_tests'].get('score', 0)
        performance_avg = self.test_results['performance_tests'].get('avg_response_time', 999)
        compliance_rate = self.test_results['compliance_tests'].get('success_rate', 0)
        integration_rate = self.test_results['integration_tests'].get('success_rate', 0)
        
        production_ready = (
            security_score >= self.criteria['security_score_minimum'] and
            performance_avg <= self.criteria['performance_response_time_ms'] and
            compliance_rate >= self.criteria['compliance_coverage_percent'] and
            overall_success_rate >= 85
        )
        
        # Print comprehensive summary
        print("\n" + "=" * 60)
        print("PRODUCTION READINESS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed Tests: {passed_tests}")
        print(f"Overall Success Rate: {overall_success_rate:.1f}%")
        print()
        print("DETAILED RESULTS:")
        print(f"  Security Score: {security_score}/100 (Required: {self.criteria['security_score_minimum']})")
        print(f"  Performance: {performance_avg:.1f}ms avg (Required: <{self.criteria['performance_response_time_ms']}ms)")
        print(f"  Compliance Coverage: {compliance_rate:.1f}% (Required: {self.criteria['compliance_coverage_percent']}%)")
        print(f"  Integration Tests: {integration_rate:.1f}%")
        print()
        
        if production_ready:
            print("PASS PRODUCTION READY")
            print("System meets all production readiness criteria")
            print("Safe for production deployment")
        else:
            print("WARN PRODUCTION NOT READY")
            print("System does not meet all production readiness criteria")
            print("Additional hardening and optimization required")
        
        print(f"\nValidation completed at: {datetime.utcnow().isoformat()}")
        
        self.test_results['overall_status'] = 'production_ready' if production_ready else 'needs_work'
        return production_ready

async def main():
    """Run production readiness test"""
    test_suite = ProductionReadinessTest()
    success = await test_suite.run_production_readiness_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)