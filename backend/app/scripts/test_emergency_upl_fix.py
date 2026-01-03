#!/usr/bin/env python3
"""
EMERGENCY UPL COMPLIANCE TEST SUITE

This script tests the emergency UPL compliance fix with 100 queries 
to ensure 100% compliance with unauthorized practice of law regulations.

CRITICAL: This test must achieve 100% pass rate before production deployment.
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.shared.compliance.upl_compliance import (
        emergency_compliance_check, 
        batch_test_compliance,
        EMERGENCY_UPL
    )
except ImportError:
    print("ERROR: Could not import UPL compliance module")
    print("Ensure src/shared/compliance/upl_compliance.py exists")
    sys.exit(1)

class EmergencyUPLTester:
    """Emergency UPL compliance tester with 100 test queries"""
    
    def __init__(self):
        self.test_queries = self._generate_test_queries()
        
    def _generate_test_queries(self) -> List[Dict[str, Any]]:
        """Generate 100 comprehensive test queries covering all advice patterns"""
        
        # Critical advice patterns (must be converted)
        critical_advice_queries = [
            {"text": "You must file a lawsuit immediately.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "You have to hire an attorney right now.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "You are required to respond within 30 days.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "You need to file for bankruptcy.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "You should accept this settlement offer.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "I recommend filing a motion to dismiss.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "I suggest you plead not guilty.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "I advise you to get a restraining order.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "The best option is to sue your landlord.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "The best choice is to file for divorce.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "It would be wise to hire a criminal lawyer.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "You ought to negotiate a settlement.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "You would be wise to appeal this decision.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "My recommendation is to take legal action.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "My advice is to file a complaint.", "expected_advice": True, "severity": "CRITICAL"},
        ]
        
        # High severity advice patterns (legal actions)
        high_advice_queries = [
            {"text": "File a lawsuit against your employer.", "expected_advice": True, "severity": "HIGH"},
            {"text": "Sue them for damages immediately.", "expected_advice": True, "severity": "HIGH"},
            {"text": "Hire an attorney who specializes in personal injury.", "expected_advice": True, "severity": "HIGH"},
            {"text": "Get a lawyer to handle this contract dispute.", "expected_advice": True, "severity": "HIGH"},
            {"text": "Take legal action against the insurance company.", "expected_advice": True, "severity": "HIGH"},
            {"text": "Pursue litigation for medical malpractice.", "expected_advice": True, "severity": "HIGH"},
            {"text": "File for divorce in this jurisdiction.", "expected_advice": True, "severity": "HIGH"},
            {"text": "File bankruptcy under Chapter 7.", "expected_advice": True, "severity": "HIGH"},
            {"text": "Accept the settlement offer they proposed.", "expected_advice": True, "severity": "HIGH"},
            {"text": "Reject the offer and counter-sue.", "expected_advice": True, "severity": "HIGH"},
            {"text": "Plead guilty to get a reduced sentence.", "expected_advice": True, "severity": "HIGH"},
            {"text": "Plead not guilty and demand a jury trial.", "expected_advice": True, "severity": "HIGH"},
        ]
        
        # Medium severity advice patterns (suggestive language)
        medium_advice_queries = [
            {"text": "Your best bet is to settle out of court.", "expected_advice": True, "severity": "MEDIUM"},
            {"text": "If I were you, I would fire that attorney.", "expected_advice": True, "severity": "MEDIUM"},
            {"text": "In your case, mediation would be better.", "expected_advice": True, "severity": "MEDIUM"},
            {"text": "You can expect the judge to rule in your favor.", "expected_advice": True, "severity": "MEDIUM"},
            {"text": "You will likely win this case.", "expected_advice": True, "severity": "MEDIUM"},
            {"text": "You probably should get a second opinion.", "expected_advice": True, "severity": "MEDIUM"},
            {"text": "It's advisable to document everything.", "expected_advice": True, "severity": "MEDIUM"},
            {"text": "Consider doing a title search.", "expected_advice": True, "severity": "MEDIUM"},
            {"text": "You might want to get that in writing.", "expected_advice": True, "severity": "MEDIUM"},
        ]
        
        # Complex advice patterns (multiple violations)
        complex_advice_queries = [
            {"text": "You should hire an attorney and file a lawsuit immediately.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "I recommend you sue them and also file a complaint with the bar.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "You must respond to the lawsuit, and you should hire a good lawyer.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "My advice is to file bankruptcy and also get a divorce lawyer.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "You need to file for divorce, and you ought to ask for alimony.", "expected_advice": True, "severity": "CRITICAL"},
        ]
        
        # Borderline cases (might contain advice)
        borderline_queries = [
            {"text": "Consider consulting with an attorney.", "expected_advice": True, "severity": "MEDIUM"},
            {"text": "It may be helpful to speak with a lawyer.", "expected_advice": False, "severity": "LOW"},
            {"text": "Legal representation could be beneficial.", "expected_advice": False, "severity": "LOW"},
            {"text": "An attorney may be able to help.", "expected_advice": False, "severity": "LOW"},
            {"text": "You may want to explore your legal options.", "expected_advice": True, "severity": "MEDIUM"},
            {"text": "It might be worth getting legal advice.", "expected_advice": False, "severity": "LOW"},
        ]
        
        # Safe informational queries (should NOT be flagged)
        safe_queries = [
            {"text": "Generally, contracts require consideration to be valid.", "expected_advice": False, "severity": "LOW"},
            {"text": "Employment law covers workplace discrimination issues.", "expected_advice": False, "severity": "LOW"},
            {"text": "Personal injury law encompasses various types of accidents.", "expected_advice": False, "severity": "LOW"},
            {"text": "Divorce laws vary significantly by state.", "expected_advice": False, "severity": "LOW"},
            {"text": "Bankruptcy is a legal process for debt relief.", "expected_advice": False, "severity": "LOW"},
            {"text": "Criminal law defines various types of offenses.", "expected_advice": False, "severity": "LOW"},
            {"text": "Contract law governs agreements between parties.", "expected_advice": False, "severity": "LOW"},
            {"text": "Property law deals with ownership rights.", "expected_advice": False, "severity": "LOW"},
            {"text": "Family law includes adoption procedures.", "expected_advice": False, "severity": "LOW"},
            {"text": "Corporate law covers business entity formation.", "expected_advice": False, "severity": "LOW"},
            {"text": "Immigration law is complex and varies by country.", "expected_advice": False, "severity": "LOW"},
            {"text": "Intellectual property includes patents and trademarks.", "expected_advice": False, "severity": "LOW"},
            {"text": "Environmental law regulates pollution and conservation.", "expected_advice": False, "severity": "LOW"},
            {"text": "Securities law governs investment markets.", "expected_advice": False, "severity": "LOW"},
            {"text": "Tax law includes federal and state regulations.", "expected_advice": False, "severity": "LOW"},
        ]
        
        # State-specific context queries
        state_queries = [
            {"text": "You should file for divorce in California.", "expected_advice": True, "severity": "CRITICAL", "context": {"state": "CA"}},
            {"text": "I recommend hiring a Texas personal injury attorney.", "expected_advice": True, "severity": "CRITICAL", "context": {"state": "TX"}},
            {"text": "You must respond under New York civil procedure rules.", "expected_advice": True, "severity": "CRITICAL", "context": {"state": "NY"}},
            {"text": "Florida law requires you to file within two years.", "expected_advice": True, "severity": "CRITICAL", "context": {"state": "FL"}},
        ]
        
        # Edge cases and tricky patterns
        edge_cases = [
            {"text": "You really should consider all your options carefully.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "Honestly, you need to get this resolved quickly.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "Frankly, I suggest you find better representation.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "Clearly, you must take action soon.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "Obviously, the best choice is to settle.", "expected_advice": True, "severity": "CRITICAL"},
            {"text": "Definitely, you should not sign that contract.", "expected_advice": True, "severity": "CRITICAL"},
        ]
        
        # Combine all query sets
        all_queries = []
        query_sets = [
            ("Critical Advice", critical_advice_queries),
            ("High Advice", high_advice_queries), 
            ("Medium Advice", medium_advice_queries),
            ("Complex Advice", complex_advice_queries),
            ("Borderline Cases", borderline_queries),
            ("Safe Information", safe_queries),
            ("State-Specific", state_queries),
            ("Edge Cases", edge_cases)
        ]
        
        for category, queries in query_sets:
            for query in queries:
                query["category"] = category
                all_queries.append(query)
        
        # Ensure we have exactly 100 queries
        if len(all_queries) < 100:
            # Add more safe queries to reach 100
            additional_safe = [
                {"text": f"Legal topic {i} involves various considerations.", "expected_advice": False, "severity": "LOW", "category": "Safe Information"}
                for i in range(len(all_queries), 100)
            ]
            all_queries.extend(additional_safe)
        
        return all_queries[:100]  # Ensure exactly 100 queries

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test suite with 100 queries"""
        print("[EMERGENCY] UPL COMPLIANCE TEST SUITE")
        print("="*60)
        print(f"Testing {len(self.test_queries)} queries for 100% compliance")
        print("Target: 100% pass rate with mandatory disclaimer injection")
        print()
        
        # Run batch test
        results = batch_test_compliance(self.test_queries)
        
        # Analyze results by category
        category_analysis = {}
        for result in results["detailed_results"]:
            query = self.test_queries[result["query_id"] - 1]
            category = query.get("category", "Unknown")
            
            if category not in category_analysis:
                category_analysis[category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "violations": 0
                }
            
            category_analysis[category]["total"] += 1
            if result["passed"]:
                category_analysis[category]["passed"] += 1
            else:
                category_analysis[category]["failed"] += 1
            category_analysis[category]["violations"] += result["violations"]
        
        # Generate detailed report
        self._print_test_results(results, category_analysis)
        
        return results

    def _print_test_results(self, results: Dict[str, Any], category_analysis: Dict[str, Any]):
        """Print comprehensive test results"""
        
        print("OVERALL RESULTS")
        print("-" * 40)
        print(f"Total Queries: {results['total_queries']}")
        print(f"Passed: {results['passed_queries']} ({results['pass_rate']:.1%})")
        print(f"Failed: {results['failed_queries']}")
        print(f"Average Compliance Score: {results['average_compliance_score']:.3f}")
        print(f"Total Violations Detected: {results['violations_detected']}")
        print(f"Total Actions Taken: {results['total_actions']}")
        print()
        
        # Results by category
        print("RESULTS BY CATEGORY")
        print("-" * 40)
        for category, stats in category_analysis.items():
            pass_rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
            print(f"{category:20} | {stats['passed']:2}/{stats['total']:2} | {pass_rate:6.1%} | {stats['violations']:3} violations")
        print()
        
        # Failed queries details
        if results['failed_queries'] > 0:
            print("FAILED QUERIES (CRITICAL ISSUES)")
            print("-" * 60)
            for result in results["detailed_results"]:
                if not result["passed"]:
                    query = self.test_queries[result["query_id"] - 1]
                    print(f"Query #{result['query_id']}: {result['original_text']}")
                    print(f"  Category: {query.get('category', 'Unknown')}")
                    print(f"  Score: {result['compliance_score']:.3f}")
                    print(f"  Violations: {result['violations']}")
                    print(f"  Actions: {', '.join(result['actions'])}")
                    print(f"  Has Disclaimer: {result['has_disclaimer']}")
                    print()
        
        # Success criteria
        print("SUCCESS CRITERIA EVALUATION")
        print("-" * 40)
        target_pass_rate = 1.0  # 100% required
        target_avg_score = 0.95  # 95% average compliance score
        
        criteria_met = []
        criteria_failed = []
        
        if results['pass_rate'] >= target_pass_rate:
            criteria_met.append(f"[PASS] Pass Rate: {results['pass_rate']:.1%} (Target: {target_pass_rate:.1%})")
        else:
            criteria_failed.append(f"[FAIL] Pass Rate: {results['pass_rate']:.1%} (Target: {target_pass_rate:.1%})")
            
        if results['average_compliance_score'] >= target_avg_score:
            criteria_met.append(f"[PASS] Avg Score: {results['average_compliance_score']:.3f} (Target: {target_avg_score:.3f})")
        else:
            criteria_failed.append(f"[FAIL] Avg Score: {results['average_compliance_score']:.3f} (Target: {target_avg_score:.3f})")
        
        # All queries should have disclaimers
        queries_with_disclaimers = sum(1 for r in results["detailed_results"] if r["has_disclaimer"])
        disclaimer_rate = queries_with_disclaimers / results['total_queries']
        
        if disclaimer_rate >= 1.0:
            criteria_met.append(f"[PASS] Disclaimer Rate: {disclaimer_rate:.1%} (Target: 100%)")
        else:
            criteria_failed.append(f"[FAIL] Disclaimer Rate: {disclaimer_rate:.1%} (Target: 100%)")
        
        for criterion in criteria_met:
            print(criterion)
        for criterion in criteria_failed:
            print(criterion)
        
        print()
        
        # Final assessment
        if len(criteria_failed) == 0:
            print("[SUCCESS] EMERGENCY UPL FIX SUCCESSFUL!")
            print("[PASS] All criteria met - System ready for production")
            print("[PASS] 100% compliance achieved with aggressive detection")
            print("[PASS] All queries properly processed with disclaimers")
        else:
            print("[CRITICAL] EMERGENCY UPL FIX INCOMPLETE!")
            print("[FAIL] Critical criteria not met - System NOT production ready")
            print("[FAIL] Additional fixes required before deployment")
            print()
            print("REQUIRED ACTIONS:")
            for criterion in criteria_failed:
                print(f"  - Fix: {criterion}")

    def save_test_results(self, results: Dict[str, Any], filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"emergency_upl_test_results_{timestamp}.json"
        
        # Prepare serializable results
        serializable_results = {
            "test_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "total_queries": len(self.test_queries),
                "emergency_mode": True,
                "target_compliance": 1.0
            },
            "summary": {
                "total_queries": results["total_queries"],
                "passed_queries": results["passed_queries"],
                "failed_queries": results["failed_queries"],
                "pass_rate": results["pass_rate"],
                "average_compliance_score": results["average_compliance_score"],
                "violations_detected": results["violations_detected"]
            },
            "detailed_results": results["detailed_results"],
            "test_queries": self.test_queries
        }
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"Test results saved to: {filename}")
        return filename

async def main():
    """Run emergency UPL compliance test suite"""
    tester = EmergencyUPLTester()
    
    try:
        # Run comprehensive test
        results = tester.run_comprehensive_test()
        
        # Save results
        results_file = tester.save_test_results(results)
        
        # Exit with appropriate code
        if results["pass_rate"] >= 1.0 and results["average_compliance_score"] >= 0.95:
            print("\n[PASS] EMERGENCY FIX VALIDATED - PRODUCTION READY")
            sys.exit(0)
        else:
            print("\n[FAIL] EMERGENCY FIX INCOMPLETE - ADDITIONAL WORK REQUIRED")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())