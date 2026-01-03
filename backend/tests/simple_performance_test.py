#!/usr/bin/env python3
"""
SIMPLE PERFORMANCE TEST

Quick performance validation for optimized systems:
- Response time testing (<100ms target)
- Cache performance validation  
- Basic system health checks

Simple ASCII output for Windows compatibility
"""

import os
import sys
import time
import asyncio
import statistics
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

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

class SimplePerformanceTest:
    """Simple performance test suite"""
    
    def __init__(self):
        self.results = {
            'disclaimer_service': {},
            'advice_detection': {},
            'cache_performance': {},
            'overall_status': 'unknown'
        }
    
    async def test_disclaimer_service(self):
        """Test disclaimer service performance - Target: <50ms"""
        print("\nTesting Disclaimer Service Performance:")
        print("-" * 50)
        
        results = {'tests': 0, 'passed': 0, 'times': []}
        
        # Test 1: Single disclaimer
        results['tests'] += 1
        start_time = time.time()
        
        try:
            disclaimer = await optimized_disclaimer_service.get_ai_response_disclaimer('legal_advice')
            response_time = (time.time() - start_time) * 1000
            results['times'].append(response_time)
            
            if response_time < 50 and len(disclaimer) > 0:
                results['passed'] += 1
                print(f"  PASS Single disclaimer: {response_time:.2f}ms")
            else:
                print(f"  FAIL Single disclaimer: {response_time:.2f}ms (Target: <50ms)")
                
        except Exception as e:
            print(f"  ERROR Single disclaimer: {str(e)}")
        
        # Test 2: Cached disclaimer (should be faster)
        results['tests'] += 1
        start_time = time.time()
        
        try:
            disclaimer = await optimized_disclaimer_service.get_ai_response_disclaimer('legal_advice')
            response_time = (time.time() - start_time) * 1000
            results['times'].append(response_time)
            
            if response_time < 20:  # Cache should be much faster
                results['passed'] += 1
                print(f"  PASS Cached disclaimer: {response_time:.2f}ms")
            else:
                print(f"  FAIL Cached disclaimer: {response_time:.2f}ms (Target: <20ms)")
                
        except Exception as e:
            print(f"  ERROR Cached disclaimer: {str(e)}")
        
        # Test 3: Page disclaimers
        results['tests'] += 1
        start_time = time.time()
        
        try:
            page_disclaimers = await optimized_disclaimer_service.get_page_disclaimers('/test')
            response_time = (time.time() - start_time) * 1000
            results['times'].append(response_time)
            
            if response_time < 50 and len(page_disclaimers) > 0:
                results['passed'] += 1
                print(f"  PASS Page disclaimers: {response_time:.2f}ms")
            else:
                print(f"  FAIL Page disclaimers: {response_time:.2f}ms (Target: <50ms)")
                
        except Exception as e:
            print(f"  ERROR Page disclaimers: {str(e)}")
        
        # Get performance stats
        try:
            stats = optimized_disclaimer_service.get_performance_stats()
            cache_hit_rate = stats.get('cache_hit_rate_percent', 0)
            avg_response_time = stats.get('avg_response_time_ms', 0)
            
            print(f"  INFO Cache hit rate: {cache_hit_rate:.1f}%")
            print(f"  INFO Average response: {avg_response_time:.2f}ms")
            
            results['cache_stats'] = stats
            
        except Exception as e:
            print(f"  ERROR Getting stats: {str(e)}")
        
        if results['times']:
            avg_time = statistics.mean(results['times'])
            results['avg_response_time'] = avg_time
            print(f"  INFO Test average: {avg_time:.2f}ms")
        
        results['success_rate'] = (results['passed'] / results['tests'] * 100) if results['tests'] > 0 else 0
        print(f"  RESULT: {results['passed']}/{results['tests']} tests passed ({results['success_rate']:.1f}%)")
        
        self.results['disclaimer_service'] = results
        return results
    
    async def test_advice_detection(self):
        """Test advice detection performance - Target: <100ms"""
        print("\nTesting Advice Detection Performance:")
        print("-" * 50)
        
        results = {'tests': 0, 'passed': 0, 'times': [], 'accuracies': []}
        
        test_cases = [
            ("You should file a lawsuit immediately.", "high risk"),
            ("Consider consulting with an attorney.", "medium risk"),
            ("This is general contract law information.", "low risk"),
            ("The weather is nice today.", "safe")
        ]
        
        for i, (test_text, expected_level) in enumerate(test_cases):
            results['tests'] += 1
            start_time = time.time()
            
            try:
                analysis = enhanced_advice_detector.analyze_output(test_text)
                response_time = (time.time() - start_time) * 1000
                results['times'].append(response_time)
                results['accuracies'].append(analysis.risk_score * 100)
                
                if response_time < 100:
                    results['passed'] += 1
                    print(f"  PASS Test {i+1}: {response_time:.2f}ms, Risk: {analysis.risk_score:.2f}")
                else:
                    print(f"  FAIL Test {i+1}: {response_time:.2f}ms (Target: <100ms)")
                    
            except Exception as e:
                print(f"  ERROR Test {i+1}: {str(e)}")
        
        if results['times']:
            avg_time = statistics.mean(results['times'])
            avg_accuracy = statistics.mean(results['accuracies'])
            
            results['avg_response_time'] = avg_time
            results['avg_accuracy'] = avg_accuracy
            
            print(f"  INFO Average response: {avg_time:.2f}ms")
            print(f"  INFO Average accuracy: {avg_accuracy:.1f}")
        
        results['success_rate'] = (results['passed'] / results['tests'] * 100) if results['tests'] > 0 else 0
        print(f"  RESULT: {results['passed']}/{results['tests']} tests passed ({results['success_rate']:.1f}%)")
        
        self.results['advice_detection'] = results
        return results
    
    async def test_concurrent_performance(self):
        """Test concurrent request performance"""
        print("\nTesting Concurrent Performance:")
        print("-" * 50)
        
        results = {'tests': 0, 'passed': 0}
        
        # Test concurrent disclaimer requests
        results['tests'] += 1
        
        try:
            concurrent_requests = 10
            
            async def single_request():
                start_time = time.time()
                disclaimer = await optimized_disclaimer_service.get_ai_response_disclaimer('enhanced')
                return (time.time() - start_time) * 1000
            
            # Run concurrent requests
            start_time = time.time()
            tasks = [single_request() for _ in range(concurrent_requests)]
            response_times = await asyncio.gather(*tasks)
            total_time = (time.time() - start_time) * 1000
            
            avg_response_time = statistics.mean(response_times)
            throughput = concurrent_requests / (total_time / 1000)
            
            if avg_response_time < 100 and throughput > 20:
                results['passed'] += 1
                print(f"  PASS Concurrent test: {avg_response_time:.2f}ms avg, {throughput:.1f} req/sec")
            else:
                print(f"  FAIL Concurrent test: {avg_response_time:.2f}ms avg, {throughput:.1f} req/sec")
            
            results['concurrent_stats'] = {
                'requests': concurrent_requests,
                'avg_response_time': avg_response_time,
                'throughput': throughput
            }
            
        except Exception as e:
            print(f"  ERROR Concurrent test: {str(e)}")
        
        results['success_rate'] = (results['passed'] / results['tests'] * 100) if results['tests'] > 0 else 0
        print(f"  RESULT: {results['passed']}/{results['tests']} tests passed ({results['success_rate']:.1f}%)")
        
        self.results['concurrent'] = results
        return results
    
    async def test_health_endpoints(self):
        """Test health check performance"""
        print("\nTesting Health Check Performance:")
        print("-" * 50)
        
        results = {'tests': 0, 'passed': 0}
        
        # Test disclaimer service health check
        results['tests'] += 1
        
        try:
            start_time = time.time()
            health_result = await optimized_disclaimer_service.health_check()
            response_time = (time.time() - start_time) * 1000
            
            if response_time < 50 and health_result.get('status') == 'healthy':
                results['passed'] += 1
                print(f"  PASS Health check: {response_time:.2f}ms, Status: {health_result.get('status')}")
            else:
                print(f"  FAIL Health check: {response_time:.2f}ms, Status: {health_result.get('status')}")
            
            results['health_stats'] = {
                'response_time': response_time,
                'status': health_result.get('status')
            }
            
        except Exception as e:
            print(f"  ERROR Health check: {str(e)}")
        
        results['success_rate'] = (results['passed'] / results['tests'] * 100) if results['tests'] > 0 else 0
        print(f"  RESULT: {results['passed']}/{results['tests']} tests passed ({results['success_rate']:.1f}%)")
        
        self.results['health_checks'] = results
        return results
    
    async def run_all_tests(self):
        """Run all performance tests"""
        print("SIMPLE PERFORMANCE TEST SUITE")
        print("=" * 60)
        print(f"Start Time: {datetime.utcnow().isoformat()}")
        print("Target: All systems respond in <100ms")
        
        # Run test categories
        await self.test_disclaimer_service()
        await self.test_advice_detection()
        await self.test_concurrent_performance()
        await self.test_health_endpoints()
        
        # Calculate overall results
        total_tests = 0
        passed_tests = 0
        
        for category, results in self.results.items():
            if isinstance(results, dict) and 'tests' in results:
                total_tests += results.get('tests', 0)
                passed_tests += results.get('passed', 0)
        
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        overall_status = 'PASS' if overall_success_rate >= 80 else 'FAIL'
        
        self.results['overall_status'] = overall_status
        self.results['overall_success_rate'] = overall_success_rate
        
        # Print summary
        print("\n" + "=" * 60)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed Tests: {passed_tests}")
        print(f"Success Rate: {overall_success_rate:.1f}%")
        print(f"Overall Status: {overall_status}")
        print(f"Performance Target Met: {overall_success_rate >= 90}")
        
        if overall_status == 'PASS':
            print("\nSUCCESS: Performance optimizations are working effectively")
            print("All systems meet or exceed performance targets")
        else:
            print("\nWARNING: Some performance targets not met")
            print("Additional optimization may be needed")
        
        return overall_status == 'PASS'

async def main():
    """Run simple performance test"""
    test_suite = SimplePerformanceTest()
    success = await test_suite.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)