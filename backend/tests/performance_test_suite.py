#!/usr/bin/env python3
"""
PERFORMANCE TEST SUITE

Comprehensive performance testing for optimized legal AI systems:
- Response time validation (<100ms target)
- Throughput testing
- Cache performance validation
- System monitoring metrics
- Health endpoint testing

Target: All systems respond in <100ms with high accuracy
"""

import os
import sys
import time
import asyncio
import statistics
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from pathlib import Path
import json
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Import systems for testing
try:
    from backend.app.core.performance_optimizer import performance_optimizer
    from backend.app.services.optimized_disclaimer_service import optimized_disclaimer_service
    from backend.app.core.enhanced_advice_detection import enhanced_advice_detector
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceTestSuite:
    """Comprehensive performance testing suite"""
    
    def __init__(self):
        self.test_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'test_summary': {},
            'detailed_results': {},
            'performance_targets': {
                'advice_detection': 100,  # ms
                'disclaimers': 50,        # ms
                'encryption': 200,        # ms
                'audit': 100,            # ms
                'health_checks': 100     # ms
            }
        }
        
        logger.info("[PERFORMANCE_TEST] Performance test suite initialized")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive performance test suite"""
        
        print("PERFORMANCE TEST SUITE - OPTIMIZATION VALIDATION")
        print("=" * 80)
        print(f"Test Start Time: {datetime.utcnow().isoformat()}")
        print(f"Target: All systems respond in <100ms")
        print()
        
        # Test categories
        test_categories = [
            ("Disclaimer Service Performance", self.test_disclaimer_performance),
            ("Advice Detection Performance", self.test_advice_detection_performance),
            ("Cache Performance", self.test_cache_performance),
            ("Concurrent Load Testing", self.test_concurrent_load),
            ("Health Endpoint Performance", self.test_health_endpoints),
            ("System Integration Performance", self.test_system_integration)
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for category_name, test_method in test_categories:
            print(f"\n{category_name}")
            print("-" * 60)
            
            try:
                category_results = await test_method()
                
                category_passed = category_results['tests_passed']
                category_total = category_results['tests_total']
                
                total_tests += category_total
                passed_tests += category_passed
                
                self.test_results['detailed_results'][category_name] = category_results
                
                print(f"✅ Passed: {category_passed}/{category_total} tests")
                
            except Exception as e:
                print(f"❌ Category failed: {str(e)}")
                total_tests += 1
                self.test_results['detailed_results'][category_name] = {
                    'error': str(e),
                    'tests_passed': 0,
                    'tests_total': 1
                }
        
        # Generate summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.test_results['test_summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate_percent': round(success_rate, 2),
            'overall_status': 'PASS' if success_rate >= 80 else 'FAIL',
            'meets_performance_targets': success_rate >= 90
        }
        
        # Print final summary
        print("\n" + "=" * 80)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed Tests: {passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Overall Status: {self.test_results['test_summary']['overall_status']}")
        print(f"Meets Performance Targets: {self.test_results['test_summary']['meets_performance_targets']}")
        
        # Save results
        report_file = f"performance_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {report_file}")
        
        return self.test_results
    
    async def test_disclaimer_performance(self) -> Dict[str, Any]:
        """Test disclaimer service performance - Target: <50ms"""
        
        results = {
            'tests_total': 0,
            'tests_passed': 0,
            'response_times': [],
            'cache_performance': {},
            'test_details': []
        }
        
        # Test 1: Single disclaimer retrieval
        results['tests_total'] += 1
        start_time = time.time()
        
        try:
            disclaimer = await optimized_disclaimer_service.get_ai_response_disclaimer('legal_advice')
            response_time = (time.time() - start_time) * 1000  # ms
            
            success = response_time < 50 and len(disclaimer) > 0
            results['response_times'].append(response_time)
            
            if success:
                results['tests_passed'] += 1
                print(f"  PASS Single Disclaimer: {response_time:.2f}ms (Target: <50ms)")
            else:
                print(f"  FAIL Single Disclaimer: {response_time:.2f}ms (Target: <50ms)")
            
            results['test_details'].append({
                'test': 'single_disclaimer',
                'response_time_ms': response_time,
                'success': success
            })
            
        except Exception as e:
            print(f"  ❌ Single Disclaimer: Error - {str(e)}")
            results['test_details'].append({
                'test': 'single_disclaimer',
                'error': str(e),
                'success': False
            })
        
        # Test 2: Cached disclaimer retrieval
        results['tests_total'] += 1
        start_time = time.time()
        
        try:
            # Second request should hit cache
            disclaimer = await optimized_disclaimer_service.get_ai_response_disclaimer('legal_advice')
            response_time = (time.time() - start_time) * 1000  # ms
            
            success = response_time < 20  # Cache should be much faster
            results['response_times'].append(response_time)
            
            if success:
                results['tests_passed'] += 1
                print(f"  ✅ Cached Disclaimer: {response_time:.2f}ms (Target: <20ms)")
            else:
                print(f"  ❌ Cached Disclaimer: {response_time:.2f}ms (Target: <20ms)")
            
            results['test_details'].append({
                'test': 'cached_disclaimer',
                'response_time_ms': response_time,
                'success': success
            })
            
        except Exception as e:
            print(f"  ❌ Cached Disclaimer: Error - {str(e)}")
        
        # Test 3: Page disclaimers
        results['tests_total'] += 1
        start_time = time.time()
        
        try:
            page_disclaimers = await optimized_disclaimer_service.get_page_disclaimers('/test-page')
            response_time = (time.time() - start_time) * 1000  # ms
            
            success = response_time < 50 and len(page_disclaimers) > 0
            results['response_times'].append(response_time)
            
            if success:
                results['tests_passed'] += 1
                print(f"  ✅ Page Disclaimers: {response_time:.2f}ms (Target: <50ms)")
            else:
                print(f"  ❌ Page Disclaimers: {response_time:.2f}ms (Target: <50ms)")
            
        except Exception as e:
            print(f"  ❌ Page Disclaimers: Error - {str(e)}")
        
        # Test 4: Performance stats
        try:
            stats = optimized_disclaimer_service.get_performance_stats()
            results['cache_performance'] = stats
            
            cache_hit_rate = stats.get('cache_hit_rate_percent', 0)
            avg_response_time = stats.get('avg_response_time_ms', 1000)
            
            print(f"  📊 Cache Hit Rate: {cache_hit_rate:.1f}%")
            print(f"  📊 Average Response Time: {avg_response_time:.2f}ms")
            
        except Exception as e:
            print(f"  ❌ Performance Stats: Error - {str(e)}")
        
        results['average_response_time'] = statistics.mean(results['response_times']) if results['response_times'] else 0
        
        return results
    
    async def test_advice_detection_performance(self) -> Dict[str, Any]:
        """Test advice detection performance - Target: <100ms"""
        
        results = {
            'tests_total': 0,
            'tests_passed': 0,
            'response_times': [],
            'accuracy_scores': [],
            'test_details': []
        }
        
        test_cases = [
            "You should file a lawsuit immediately for this contract breach.",
            "Consider consulting with an attorney about your legal options.",
            "The best approach is to document everything before proceeding.",
            "This is general information about contract law principles.",
            "You have a strong case and should pursue legal action."
        ]
        
        for i, test_text in enumerate(test_cases):
            results['tests_total'] += 1
            start_time = time.time()
            
            try:
                analysis = enhanced_advice_detector.analyze_output(test_text)
                response_time = (time.time() - start_time) * 1000  # ms
                
                # Check if detection was accurate (non-zero risk for advice-like text)
                accuracy_score = analysis.risk_score * 100
                results['accuracy_scores'].append(accuracy_score)
                
                success = response_time < 100
                results['response_times'].append(response_time)
                
                if success:
                    results['tests_passed'] += 1
                    print(f"  ✅ Test {i+1}: {response_time:.2f}ms, Risk: {analysis.risk_score:.2f}")
                else:
                    print(f"  ❌ Test {i+1}: {response_time:.2f}ms (Target: <100ms)")
                
                results['test_details'].append({
                    'test': f'advice_detection_{i+1}',
                    'response_time_ms': response_time,
                    'risk_score': analysis.risk_score,
                    'success': success
                })
                
            except Exception as e:
                print(f"  ❌ Test {i+1}: Error - {str(e)}")
                results['test_details'].append({
                    'test': f'advice_detection_{i+1}',
                    'error': str(e),
                    'success': False
                })
        
        if results['response_times']:
            avg_response_time = statistics.mean(results['response_times'])
            avg_accuracy = statistics.mean(results['accuracy_scores']) if results['accuracy_scores'] else 0
            
            print(f"  📊 Average Response Time: {avg_response_time:.2f}ms")
            print(f"  📊 Average Accuracy Score: {avg_accuracy:.2f}")
            
            results['average_response_time'] = avg_response_time
            results['average_accuracy'] = avg_accuracy
        
        return results
    
    async def test_cache_performance(self) -> Dict[str, Any]:
        """Test cache performance and hit rates"""
        
        results = {
            'tests_total': 0,
            'tests_passed': 0,
            'cache_stats': {},
            'test_details': []
        }
        
        # Test cache warming
        results['tests_total'] += 1
        
        try:
            # Make multiple requests for same disclaimer to test caching
            test_requests = 10
            cache_times = []
            
            for i in range(test_requests):
                start_time = time.time()
                disclaimer = await optimized_disclaimer_service.get_ai_response_disclaimer('enhanced')
                response_time = (time.time() - start_time) * 1000
                cache_times.append(response_time)
            
            # Later requests should be faster due to caching
            first_request_time = cache_times[0]
            later_avg_time = statistics.mean(cache_times[1:])
            
            cache_improvement = (first_request_time - later_avg_time) / first_request_time * 100
            success = later_avg_time < first_request_time and later_avg_time < 20
            
            if success:
                results['tests_passed'] += 1
                print(f"  ✅ Cache Performance: {cache_improvement:.1f}% improvement")
                print(f"    First: {first_request_time:.2f}ms, Cached: {later_avg_time:.2f}ms")
            else:
                print(f"  ❌ Cache Performance: No significant improvement")
            
            results['test_details'].append({
                'test': 'cache_warming',
                'first_request_ms': first_request_time,
                'cached_avg_ms': later_avg_time,
                'improvement_percent': cache_improvement,
                'success': success
            })
            
        except Exception as e:
            print(f"  ❌ Cache Performance: Error - {str(e)}")
        
        # Get cache statistics
        try:
            stats = optimized_disclaimer_service.get_performance_stats()
            results['cache_stats'] = stats
            
            cache_hit_rate = stats.get('cache_hit_rate_percent', 0)
            print(f"  📊 Overall Cache Hit Rate: {cache_hit_rate:.1f}%")
            
        except Exception as e:
            print(f"  ❌ Cache Stats: Error - {str(e)}")
        
        return results
    
    async def test_concurrent_load(self) -> Dict[str, Any]:
        """Test concurrent load performance"""
        
        results = {
            'tests_total': 0,
            'tests_passed': 0,
            'concurrent_results': {},
            'test_details': []
        }
        
        # Test concurrent disclaimer requests
        results['tests_total'] += 1
        
        try:
            concurrent_requests = 20
            
            async def single_request():
                start_time = time.time()
                disclaimer = await optimized_disclaimer_service.get_ai_response_disclaimer('legal_guidance')
                return (time.time() - start_time) * 1000
            
            # Run concurrent requests
            start_time = time.time()
            tasks = [single_request() for _ in range(concurrent_requests)]
            response_times = await asyncio.gather(*tasks)
            total_time = (time.time() - start_time) * 1000
            
            avg_response_time = statistics.mean(response_times)
            throughput = concurrent_requests / (total_time / 1000)  # requests per second
            
            success = avg_response_time < 100 and throughput > 50
            
            if success:
                results['tests_passed'] += 1
                print(f"  ✅ Concurrent Load: {avg_response_time:.2f}ms avg, {throughput:.1f} req/sec")
            else:
                print(f"  ❌ Concurrent Load: {avg_response_time:.2f}ms avg, {throughput:.1f} req/sec")
            
            results['concurrent_results'] = {
                'requests': concurrent_requests,
                'avg_response_time_ms': avg_response_time,
                'throughput_req_per_sec': throughput,
                'total_time_ms': total_time
            }
            
        except Exception as e:
            print(f"  ❌ Concurrent Load: Error - {str(e)}")
        
        return results
    
    async def test_health_endpoints(self) -> Dict[str, Any]:
        """Test health endpoint performance"""
        
        results = {
            'tests_total': 0,
            'tests_passed': 0,
            'endpoint_results': {},
            'test_details': []
        }
        
        # Test optimized disclaimer service health check
        results['tests_total'] += 1
        
        try:
            start_time = time.time()
            health_result = await optimized_disclaimer_service.health_check()
            response_time = (time.time() - start_time) * 1000
            
            success = response_time < 50 and health_result.get('status') == 'healthy'
            
            if success:
                results['tests_passed'] += 1
                print(f"  ✅ Disclaimer Health: {response_time:.2f}ms")
            else:
                print(f"  ❌ Disclaimer Health: {response_time:.2f}ms or unhealthy")
            
            results['endpoint_results']['disclaimer_service'] = {
                'response_time_ms': response_time,
                'status': health_result.get('status'),
                'success': success
            }
            
        except Exception as e:
            print(f"  ❌ Disclaimer Health: Error - {str(e)}")
        
        return results
    
    async def test_system_integration(self) -> Dict[str, Any]:
        """Test integrated system performance"""
        
        results = {
            'tests_total': 0,
            'tests_passed': 0,
            'integration_results': {},
            'test_details': []
        }
        
        # Test end-to-end workflow
        results['tests_total'] += 1
        
        try:
            start_time = time.time()
            
            # 1. Detect advice
            test_text = "You should consult with an attorney about your contract."
            analysis = enhanced_advice_detector.analyze_output(test_text)
            
            # 2. Get appropriate disclaimer
            disclaimer = await optimized_disclaimer_service.get_ai_response_disclaimer(
                analysis.advice_level.value
            )
            
            total_time = (time.time() - start_time) * 1000
            
            success = total_time < 150 and len(disclaimer) > 0 and analysis.risk_score > 0
            
            if success:
                results['tests_passed'] += 1
                print(f"  ✅ End-to-End: {total_time:.2f}ms")
            else:
                print(f"  ❌ End-to-End: {total_time:.2f}ms (Target: <150ms)")
            
            results['integration_results'] = {
                'total_time_ms': total_time,
                'advice_risk_score': analysis.risk_score,
                'disclaimer_length': len(disclaimer),
                'success': success
            }
            
        except Exception as e:
            print(f"  ❌ End-to-End: Error - {str(e)}")
        
        return results

async def main():
    """Run performance test suite"""
    
    test_suite = PerformanceTestSuite()
    results = await test_suite.run_all_tests()
    
    # Return success/failure code
    return 0 if results['test_summary']['overall_status'] == 'PASS' else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)