#!/usr/bin/env python3
"""
Legal AI System Local Testing Script

This script tests all available endpoints of the Legal AI System running on port 8003.
It provides detailed test results, response times, and system status summary.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

class LegalAITester:
    def __init__(self, base_url: str = "http://127.0.0.1:8003"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Legal-AI-Tester/1.0'
        })
        
        # Test results tracking
        self.results: List[Dict[str, Any]] = []
        self.start_time = time.time()
        
        # Define all test endpoints
        self.endpoints = [
            {
                'name': 'System Health Check',
                'method': 'GET',
                'path': '/health',
                'expected_status': 200,
                'critical': True
            },
            {
                'name': 'Root Endpoint',
                'method': 'GET', 
                'path': '/',
                'expected_status': 200,
                'critical': True
            },
            {
                'name': 'PACER Gateway Status',
                'method': 'GET',
                'path': '/api/pacer/status',
                'expected_status': 200,
                'critical': True
            },
            {
                'name': 'PACER Health Check',
                'method': 'GET',
                'path': '/api/pacer/health',
                'expected_status': 200,
                'critical': True
            },
            {
                'name': 'Available Courts List',
                'method': 'GET',
                'path': '/api/pacer/courts',
                'expected_status': 200,
                'critical': True
            },
            {
                'name': 'PACER Statistics',
                'method': 'GET',
                'path': '/api/pacer/stats',
                'expected_status': 200,
                'critical': True
            },
            {
                'name': 'Track Docket',
                'method': 'POST',
                'path': '/api/pacer/track-docket',
                'expected_status': 200,
                'critical': True,
                'data': {
                    'court_id': 'cand',
                    'case_number': '5:20-cv-00001'
                }
            }
        ]

    def print_header(self):
        """Print formatted test header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}  Legal AI System - Local Testing Suite{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.CYAN}Target Server: {Colors.WHITE}{self.base_url}{Colors.RESET}")
        print(f"{Colors.CYAN}Test Started:  {Colors.WHITE}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.CYAN}Total Tests:   {Colors.WHITE}{len(self.endpoints)}{Colors.RESET}")
        print(f"{Colors.BLUE}{'-'*70}{Colors.RESET}\n")

    def test_endpoint(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single endpoint and return results"""
        
        print(f"{Colors.YELLOW}Testing: {Colors.WHITE}{endpoint['name']}{Colors.RESET}")
        print(f"  {Colors.CYAN}{endpoint['method']} {self.base_url}{endpoint['path']}{Colors.RESET}")
        
        # Prepare request
        url = self.base_url + endpoint['path']
        method = endpoint['method'].lower()
        
        # Start timing
        start_time = time.time()
        
        try:
            # Make request
            if method == 'get':
                response = self.session.get(url, timeout=10)
            elif method == 'post':
                data = endpoint.get('data', {})
                response = self.session.post(url, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text
            
            # Determine test result
            success = response.status_code == endpoint['expected_status']
            
            result = {
                'name': endpoint['name'],
                'method': endpoint['method'],
                'path': endpoint['path'],
                'success': success,
                'status_code': response.status_code,
                'expected_status': endpoint['expected_status'],
                'response_time': response_time,
                'response_data': response_data,
                'critical': endpoint.get('critical', False),
                'error': None
            }
            
            # Print result
            status_color = Colors.GREEN if success else Colors.RED
            status_text = "PASS" if success else "FAIL"
            
            print(f"  {status_color}[{status_text}]{Colors.RESET} "
                  f"Status: {response.status_code} | "
                  f"Time: {response_time:.0f}ms")
            
            # Show response preview
            if isinstance(response_data, dict):
                preview = json.dumps(response_data, indent=2)[:200]
                if len(preview) >= 200:
                    preview += "..."
            else:
                preview = str(response_data)[:200]
                if len(preview) >= 200:
                    preview += "..."
            
            print(f"  {Colors.MAGENTA}Response Preview:{Colors.RESET}")
            for line in preview.split('\n')[:3]:  # Show first 3 lines
                print(f"    {Colors.WHITE}{line}{Colors.RESET}")
            
            if not success:
                print(f"  {Colors.RED}Expected status {endpoint['expected_status']}, got {response.status_code}{Colors.RESET}")
            
        except requests.exceptions.RequestException as e:
            response_time = (time.time() - start_time) * 1000
            
            result = {
                'name': endpoint['name'],
                'method': endpoint['method'],
                'path': endpoint['path'],
                'success': False,
                'status_code': 0,
                'expected_status': endpoint['expected_status'],
                'response_time': response_time,
                'response_data': None,
                'critical': endpoint.get('critical', False),
                'error': str(e)
            }
            
            print(f"  {Colors.RED}[FAIL]{Colors.RESET} "
                  f"Connection Error | Time: {response_time:.0f}ms")
            print(f"  {Colors.RED}Error: {str(e)}{Colors.RESET}")
        
        print()  # Empty line for spacing
        return result

    def run_all_tests(self) -> None:
        """Run all endpoint tests"""
        self.print_header()
        
        for endpoint in self.endpoints:
            result = self.test_endpoint(endpoint)
            self.results.append(result)
            time.sleep(0.1)  # Small delay between tests

    def print_summary(self) -> None:
        """Print test summary and statistics"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        critical_failures = sum(1 for r in self.results if not r['success'] and r['critical'])
        
        # Calculate average response time (only for successful requests)
        successful_times = [r['response_time'] for r in self.results if r['success']]
        avg_response_time = sum(successful_times) / len(successful_times) if successful_times else 0
        
        # Determine overall system status
        if critical_failures > 0:
            system_status = "CRITICAL"
            status_color = Colors.RED
        elif failed_tests > 0:
            system_status = "DEGRADED"
            status_color = Colors.YELLOW
        else:
            system_status = "OPERATIONAL"
            status_color = Colors.GREEN
        
        total_time = time.time() - self.start_time
        
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}  Test Summary{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        
        print(f"{Colors.CYAN}Total Tests Run:     {Colors.WHITE}{total_tests}{Colors.RESET}")
        print(f"{Colors.GREEN}Tests Passed:        {Colors.WHITE}{passed_tests}{Colors.RESET}")
        print(f"{Colors.RED}Tests Failed:        {Colors.WHITE}{failed_tests}{Colors.RESET}")
        print(f"{Colors.YELLOW}Critical Failures:   {Colors.WHITE}{critical_failures}{Colors.RESET}")
        print(f"{Colors.MAGENTA}Avg Response Time:   {Colors.WHITE}{avg_response_time:.0f}ms{Colors.RESET}")
        print(f"{Colors.CYAN}Total Test Time:     {Colors.WHITE}{total_time:.1f}s{Colors.RESET}")
        print(f"{Colors.BOLD}System Status:       {status_color}{system_status}{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}{'-'*70}{Colors.RESET}")
        
        # Show failed tests details
        if failed_tests > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}Failed Tests:{Colors.RESET}")
            for result in self.results:
                if not result['success']:
                    error_detail = result['error'] if result['error'] else f"Status {result['status_code']}"
                    print(f"  {Colors.RED}✗{Colors.RESET} {result['name']}: {error_detail}")
        
        # Show performance details
        print(f"\n{Colors.CYAN}{Colors.BOLD}Performance Details:{Colors.RESET}")
        for result in self.results:
            if result['success']:
                time_color = Colors.GREEN if result['response_time'] < 1000 else Colors.YELLOW
                print(f"  {Colors.GREEN}✓{Colors.RESET} {result['name']}: {time_color}{result['response_time']:.0f}ms{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")

    def save_results(self, filename: str = "test_results.json") -> None:
        """Save test results to JSON file"""
        output = {
            'test_run': {
                'timestamp': datetime.now().isoformat(),
                'base_url': self.base_url,
                'total_tests': len(self.results),
                'passed': sum(1 for r in self.results if r['success']),
                'failed': sum(1 for r in self.results if not r['success']),
                'duration_seconds': time.time() - self.start_time
            },
            'results': self.results
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(output, f, indent=2)
            print(f"\n{Colors.GREEN}Results saved to {filename}{Colors.RESET}")
        except Exception as e:
            print(f"\n{Colors.RED}Failed to save results: {e}{Colors.RESET}")

def main():
    """Main function to run the test suite"""
    print(f"{Colors.BOLD}Legal AI System - Local Test Runner{Colors.RESET}")
    
    # Initialize tester
    tester = LegalAITester()
    
    try:
        # Run all tests
        tester.run_all_tests()
        
        # Print summary
        tester.print_summary()
        
        # Save results
        tester.save_results()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.RESET}")

if __name__ == "__main__":
    main()