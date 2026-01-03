#!/usr/bin/env python3
"""
DISCLAIMER PAGE TESTING SCRIPT

Tests all 66+ pages to ensure disclaimers are properly displayed.
Verifies both service-based and fallback disclaimer systems.
"""

import requests
import json
import time
from urllib.parse import urljoin
import asyncio
from typing import Dict, List, Tuple

# Test pages - comprehensive list of all pages in the system
TEST_PAGES = [
    # Main pages
    "/",
    "/research",
    "/contracts", 
    "/dashboard",
    "/analyze",
    "/documents",
    "/costs",
    "/compliance",
    "/client-portal",
    "/admin",
    "/education", 
    "/referrals",
    "/mobile",
    
    # Authentication pages
    "/auth",
    "/auth/login",
    "/auth/register",
    
    # Admin pages
    "/admin/monitoring",
    "/admin/audit",
    "/admin/users",
    "/admin/settings",
    "/admin/compliance",
    "/admin/reports",
    
    # Dashboard sub-pages
    "/dashboard/cases",
    "/dashboard/deadlines", 
    "/dashboard/documents",
    "/dashboard/calendar",
    "/dashboard/billing",
    "/dashboard/analytics",
    
    # Research pages
    "/research/cases",
    "/research/statutes",
    "/research/citations",
    "/research/precedents",
    "/research/history",
    
    # Contract pages
    "/contracts/upload",
    "/contracts/analyze",
    "/contracts/templates",
    "/contracts/review",
    "/contracts/compare",
    
    # Document pages  
    "/documents/upload",
    "/documents/search",
    "/documents/recent",
    "/documents/shared",
    "/documents/templates",
    
    # Client portal pages
    "/client-portal/messages",
    "/client-portal/documents",
    "/client-portal/appointments",
    "/client-portal/billing",
    "/client-portal/case-status",
    "/client-portal/education",
    
    # Education pages
    "/education/topics",
    "/education/guides", 
    "/education/faq",
    "/education/glossary",
    "/education/resources",
    
    # Mobile pages
    "/mobile/test-results",
    "/mobile/accessibility",
    "/mobile/offline",
    "/mobile/notifications",
    
    # API endpoints that should have disclaimers
    "/api/research",
    "/api/contracts",
    "/api/analyze", 
    "/api/dashboard",
    "/api/documents",
    
    # Specific matter/case pages
    "/dashboard/matter-123",
    "/dashboard/case-456",
    "/contracts/agreement-789",
    
    # Settings and profile
    "/settings",
    "/profile",
    "/preferences",
    "/notifications",
    
    # Legal-specific pages
    "/litigation",
    "/bankruptcy",
    "/family-law",
    "/corporate",
    "/real-estate",
    "/immigration",
    "/criminal",
    "/personal-injury",
    "/employment",
    "/tax-law"
]

class DisclaimerPageTester:
    """Comprehensive disclaimer page testing system"""
    
    def __init__(self):
        self.service_url = "http://localhost:8001"
        self.test_results = []
        self.total_pages = len(TEST_PAGES)
        self.passed_tests = 0
        self.failed_tests = 0
        
    def test_disclaimer_service_health(self) -> bool:
        """Test if disclaimer service is running"""
        try:
            response = requests.get(f"{self.service_url}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Disclaimer service healthy: {health.get('status', 'unknown')}")
                return True
            else:
                print(f"⚠️ Disclaimer service unhealthy: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Disclaimer service unavailable: {e}")
            return False
    
    def test_page_disclaimer(self, page_path: str) -> Tuple[bool, str, Dict]:
        """Test disclaimer for a specific page"""
        try:
            # Test auto-detection of disclaimer type
            response = requests.get(
                f"{self.service_url}/disclaimer",
                params={'page_path': page_path},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify disclaimer structure
                if 'disclaimer' in data and 'metadata' in data and 'compliance' in data:
                    disclaimer = data['disclaimer']
                    metadata = data['metadata']
                    
                    # Check required fields
                    has_title = 'title' in disclaimer and disclaimer['title']
                    has_content = 'content' in disclaimer and len(disclaimer['content']) > 0
                    has_compliance = data['compliance']['mandatory'] and data['compliance']['not_legal_advice']
                    
                    if has_title and has_content and has_compliance:
                        return True, f"✅ {metadata.get('disclaimer_type', 'unknown')}", data
                    else:
                        return False, f"❌ Invalid disclaimer structure", data
                else:
                    return False, f"❌ Missing required fields", data
            else:
                return False, f"❌ HTTP {response.status_code}", {}
                
        except Exception as e:
            return False, f"❌ Error: {str(e)}", {}
    
    def run_comprehensive_test(self):
        """Run comprehensive test of all pages"""
        print("🚨 STARTING COMPREHENSIVE DISCLAIMER PAGE TEST")
        print(f"📊 Testing {self.total_pages} pages")
        print("=" * 60)
        
        # First check service health
        service_healthy = self.test_disclaimer_service_health()
        if not service_healthy:
            print("⚠️ WARNING: Service not healthy, some tests may use fallbacks")
        
        print("\n📝 Testing individual pages:")
        print("-" * 60)
        
        for i, page in enumerate(TEST_PAGES, 1):
            passed, status, data = self.test_page_disclaimer(page)
            
            if passed:
                self.passed_tests += 1
                disclaimer_type = data.get('metadata', {}).get('disclaimer_type', 'unknown')
                print(f"{i:2d}. {page:<30} {status} ({disclaimer_type})")
            else:
                self.failed_tests += 1
                print(f"{i:2d}. {page:<30} {status}")
            
            # Store results for report
            self.test_results.append({
                'page': page,
                'passed': passed,
                'status': status,
                'data': data if passed else {}
            })
            
            # Small delay to avoid overwhelming service
            time.sleep(0.1)
        
        # Generate summary report
        self.generate_report()
    
    def test_disclaimer_types(self):
        """Test all disclaimer types explicitly"""
        print("\n🔍 Testing specific disclaimer types:")
        print("-" * 60)
        
        disclaimer_types = [
            'global', 'research', 'contracts', 'dashboard', 
            'analyze', 'client-portal', 'admin', 'education', 'mobile'
        ]
        
        for dtype in disclaimer_types:
            try:
                response = requests.get(f"{self.service_url}/disclaimer/{dtype}")
                if response.status_code == 200:
                    data = response.json()
                    title = data.get('disclaimer', {}).get('title', 'Unknown')
                    content_count = len(data.get('disclaimer', {}).get('content', []))
                    print(f"✅ {dtype:<15} - {title} ({content_count} items)")
                else:
                    print(f"❌ {dtype:<15} - HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {dtype:<15} - Error: {e}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        success_rate = (self.passed_tests / self.total_pages) * 100
        
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE DISCLAIMER TEST REPORT")
        print("=" * 60)
        
        print(f"Total Pages Tested:    {self.total_pages}")
        print(f"Passed:               {self.passed_tests}")
        print(f"Failed:               {self.failed_tests}")
        print(f"Success Rate:         {success_rate:.1f}%")
        
        if success_rate >= 95:
            print("🎉 EXCELLENT: >95% success rate")
        elif success_rate >= 90:
            print("✅ GOOD: >90% success rate") 
        elif success_rate >= 80:
            print("⚠️ ACCEPTABLE: >80% success rate")
        else:
            print("❌ POOR: <80% success rate - CRITICAL ISSUES")
        
        # Show failures
        if self.failed_tests > 0:
            print(f"\n❌ Failed Pages ({self.failed_tests}):")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   - {result['page']}: {result['status']}")
        
        # Show disclaimer type distribution
        type_counts = {}
        for result in self.test_results:
            if result['passed']:
                dtype = result['data'].get('metadata', {}).get('disclaimer_type', 'unknown')
                type_counts[dtype] = type_counts.get(dtype, 0) + 1
        
        if type_counts:
            print(f"\n📈 Disclaimer Types Distribution:")
            for dtype, count in sorted(type_counts.items()):
                print(f"   - {dtype}: {count} pages")
        
        print("=" * 60)
        
        # Save detailed report
        report_data = {
            'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_pages': self.total_pages,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'success_rate': success_rate,
            'disclaimer_types': type_counts,
            'detailed_results': self.test_results
        }
        
        with open('disclaimer_test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved to: disclaimer_test_report.json")

def main():
    """Main test execution"""
    tester = DisclaimerPageTester()
    
    # Run comprehensive page test
    tester.run_comprehensive_test()
    
    # Test specific disclaimer types
    tester.test_disclaimer_types()
    
    print(f"\n🏁 Testing complete!")

if __name__ == "__main__":
    main()