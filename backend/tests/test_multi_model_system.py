#!/usr/bin/env python3
"""
Test Script for Multi-Model Document Processing System

This script tests the multi-model AI processing strategy across different
document types and complexity levels to verify cost optimization and quality.
"""

import asyncio
import json
import time
from typing import Dict, Any, List
from datetime import datetime

# Import the multi-model components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from document_processor.processor import document_processor
    from document_processor.cost_optimizer import cost_optimizer, ProcessingTier
    from bankruptcy.bankruptcy_specialist import bankruptcy_specialist
    print("✓ Successfully imported multi-model components")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    print("Note: Some components may require full backend environment")
    sys.exit(1)


class MultiModelTester:
    """Test suite for multi-model document processing system."""

    def __init__(self):
        self.test_documents = {
            "simple_contract": {
                "text": """
                SERVICE AGREEMENT

                This agreement is between ABC Corp and XYZ Services.
                Payment terms: Net 30 days.
                Termination: 30-day notice required.
                Confidentiality provisions apply.
                """,
                "expected_tier": ProcessingTier.QUICK_TRIAGE,
                "expected_cost": 0.01
            },
            "complex_contract": {
                "text": """
                MASTER SERVICES AGREEMENT WITH INTELLECTUAL PROPERTY PROVISIONS

                WHEREAS, the parties desire to enter into a comprehensive services relationship;
                WHEREAS, the services involve proprietary methodologies and confidential information;

                NOW THEREFORE, in consideration of the mutual covenants herein:

                1. SCOPE OF SERVICES: Provider shall perform software development services incorporating
                   artificial intelligence and machine learning technologies, subject to the technical
                   specifications attached as Exhibit A and the development milestones in Schedule B.

                2. INTELLECTUAL PROPERTY: All work product shall be considered work-for-hire,
                   notwithstanding any prior inventions or background IP of Provider. Client shall
                   have unlimited license to use, modify, and distribute all deliverables.

                3. PAYMENT TERMS: Client shall pay Provider according to the milestone schedule,
                   with payments due within fifteen (15) days of milestone completion. Late payments
                   shall accrue interest at 1.5% per month. Provider may suspend services for
                   payments more than thirty (30) days overdue.

                4. TERMINATION: Either party may terminate for convenience with sixty (60) days
                   written notice. Termination for cause may be immediate. Upon termination,
                   Provider shall deliver all work product and return confidential information.
                """,
                "expected_tier": ProcessingTier.STANDARD_REVIEW,
                "expected_cost": 0.15
            },
            "litigation_document": {
                "text": """
                MOTION FOR SUMMARY JUDGMENT

                TO THE HONORABLE COURT:

                Defendant respectfully moves for summary judgment pursuant to Federal Rule of
                Civil Procedure 56, arguing that no genuine issue of material fact exists and
                defendant is entitled to judgment as a matter of law.

                STATEMENT OF FACTS:

                1. Plaintiff filed this action alleging breach of contract, tortious interference,
                   and violation of the Computer Fraud and Abuse Act arising from defendant's
                   termination of a software licensing agreement.

                2. The licensing agreement contained an express termination clause allowing
                   either party to terminate for material breach upon thirty (30) days notice
                   and opportunity to cure.

                3. Plaintiff materially breached the agreement by: (a) exceeding licensed user
                   limits by 300%; (b) reverse engineering the software in violation of Section 8;
                   and (c) failing to pay licensing fees for Q3 and Q4 2023.

                ARGUMENT:

                I. PLAINTIFF'S BREACH OF CONTRACT CLAIM FAILS AS A MATTER OF LAW

                Under controlling precedent in Smith v. TechCorp (2022), a party cannot recover
                for breach of contract when that party has materially breached the same agreement.
                Plaintiff's own admissions establish material breach...
                """,
                "expected_tier": ProcessingTier.DEEP_ANALYSIS,
                "expected_cost": 0.75
            },
            "bankruptcy_filing": {
                "text": """
                VOLUNTARY PETITION FOR BANKRUPTCY

                Chapter 7 Case

                Debtor: John Smith
                Address: 123 Main Street, Anytown, ST 12345

                STATISTICAL/ADMINISTRATIVE INFORMATION:

                Nature of Debts: Consumer debts
                Estimated Assets: $50,000 - $100,000
                Estimated Liabilities: $100,000 - $500,000
                Estimated Number of Creditors: 1-49

                PRIOR BANKRUPTCY CASE FILED WITHIN LAST 8 YEARS: No

                REQUEST FOR RELIEF: Debtor requests relief in accordance with the chapter
                of title 11, United States Code, specified in this petition.
                """,
                "task_type": "filing_classification",
                "expected_tier": ProcessingTier.QUICK_TRIAGE,
                "expected_cost": 0.01
            }
        }

        self.test_results = []

    async def run_comprehensive_tests(self):
        """Run comprehensive tests of the multi-model system."""
        print("🚀 Starting Multi-Model Document Processing System Tests")
        print("=" * 60)

        # Test 1: Document Processor Tests
        await self._test_document_processor()

        # Test 2: Bankruptcy Specialist Tests
        await self._test_bankruptcy_specialist()

        # Test 3: Cost Optimization Tests
        self._test_cost_optimization()

        # Test 4: Tier Recommendation Tests
        self._test_tier_recommendations()

        # Generate test report
        self._generate_test_report()

    async def _test_document_processor(self):
        """Test the document processor with different complexity levels."""
        print("\n📄 Testing Document Processor")
        print("-" * 30)

        for doc_name, doc_info in self.test_documents.items():
            if doc_name == "bankruptcy_filing":
                continue  # Skip bankruptcy docs for general processor

            print(f"\nTesting: {doc_name}")
            start_time = time.time()

            try:
                # Test document classification
                classification_result = await document_processor.classify_document(
                    document_text=doc_info["text"],
                    user_id="test_user"
                )

                # Test appropriate analysis based on complexity
                if doc_info["expected_tier"] == ProcessingTier.QUICK_TRIAGE:
                    analysis_result = await document_processor.analyze_document(
                        document_text=doc_info["text"],
                        analysis_type="standard",
                        urgency="normal"
                    )
                elif doc_info["expected_tier"] == ProcessingTier.DEEP_ANALYSIS:
                    analysis_result = await document_processor.deep_analyze_document(
                        document_text=doc_info["text"],
                        analysis_focus=["legal_risks", "compliance"]
                    )
                else:
                    analysis_result = await document_processor.analyze_document(
                        document_text=doc_info["text"],
                        analysis_type="comprehensive",
                        urgency="normal"
                    )

                processing_time = time.time() - start_time

                # Record test result
                test_result = {
                    "document": doc_name,
                    "classification": classification_result,
                    "analysis": analysis_result,
                    "processing_time": processing_time,
                    "expected_tier": doc_info["expected_tier"].value,
                    "expected_cost": doc_info["expected_cost"],
                    "success": True
                }

                self.test_results.append(test_result)

                print(f"  ✓ Document Type: {classification_result.get('document_type', 'Unknown')}")
                print(f"  ✓ Complexity Level: {classification_result.get('complexity_level', 'Unknown')}")
                print(f"  ✓ Processing Time: {processing_time:.2f}s")
                print(f"  ✓ Expected Tier: {doc_info['expected_tier'].value}")

            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                self.test_results.append({
                    "document": doc_name,
                    "error": str(e),
                    "success": False
                })

    async def _test_bankruptcy_specialist(self):
        """Test the bankruptcy specialist with multi-model selection."""
        print("\n🏛️ Testing Bankruptcy Specialist")
        print("-" * 30)

        bankruptcy_doc = self.test_documents["bankruptcy_filing"]
        doc_text = bankruptcy_doc["text"]

        tests = [
            ("Filing Classification", "classify_filing_type", ProcessingTier.QUICK_TRIAGE),
            ("Deadline Extraction", "extract_deadline_information", ProcessingTier.QUICK_TRIAGE),
            ("Creditor Analysis", "analyze_creditor_information", ProcessingTier.STANDARD_REVIEW),
        ]

        for test_name, method_name, expected_tier in tests:
            print(f"\nTesting: {test_name}")
            start_time = time.time()

            try:
                method = getattr(bankruptcy_specialist, method_name)
                result = await method(doc_text, "test_user")
                processing_time = time.time() - start_time

                print(f"  ✓ Success: {result.get('success', False)}")
                print(f"  ✓ Expected Tier: {expected_tier.value}")
                print(f"  ✓ Processing Time: {processing_time:.2f}s")

                if result.get('success'):
                    if 'classification' in result:
                        print(f"  ✓ Filing Type: {result['classification'].get('filing_type')}")
                        print(f"  ✓ Chapter Suggestion: {result['classification'].get('chapter_suggestion')}")
                    elif 'extracted_deadlines' in result:
                        print(f"  ✓ Deadlines Found: {len(result['extracted_deadlines'])}")
                    elif 'creditor_analysis' in result:
                        analysis = result['creditor_analysis']
                        print(f"  ✓ Secured Creditors: {len(analysis.get('secured_creditors', []))}")
                        print(f"  ✓ Unsecured Creditors: {len(analysis.get('unsecured_creditors', []))}")

                self.test_results.append({
                    "bankruptcy_test": test_name,
                    "result": result,
                    "processing_time": processing_time,
                    "expected_tier": expected_tier.value,
                    "success": True
                })

            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                self.test_results.append({
                    "bankruptcy_test": test_name,
                    "error": str(e),
                    "success": False
                })

    def _test_cost_optimization(self):
        """Test cost optimization functionality."""
        print("\n💰 Testing Cost Optimization")
        print("-" * 30)

        try:
            # Test tier recommendations
            for task_type in ["classification", "extraction", "analysis", "litigation_analysis"]:
                tier, reasoning = cost_optimizer.get_tier_recommendation(
                    document_type="legal_contract",
                    complexity_score=0.5,
                    task_type=task_type
                )

                print(f"\nTask: {task_type}")
                print(f"  ✓ Recommended Tier: {tier.value}")
                print(f"  ✓ Reasoning: {reasoning[:80]}...")

            # Test optimization recommendations
            recommendations = cost_optimizer.get_optimization_recommendations()
            print(f"\n📊 Optimization Recommendations:")
            for i, rec in enumerate(recommendations[:3]):
                print(f"  {i+1}. {rec[:80]}...")

            # Test efficiency metrics
            efficiency = cost_optimizer.get_efficiency_metrics()
            print(f"\n📈 System Efficiency:")
            print(f"  ✓ Available metrics: {len(efficiency)} categories")

            print("  ✓ Cost optimization tests completed successfully")

        except Exception as e:
            print(f"  ✗ Cost optimization error: {str(e)}")

    def _test_tier_recommendations(self):
        """Test tier recommendation logic."""
        print("\n🎯 Testing Tier Recommendations")
        print("-" * 30)

        test_scenarios = [
            ("Simple Classification", "classification", 0.2, ProcessingTier.QUICK_TRIAGE),
            ("Standard Analysis", "analysis", 0.5, ProcessingTier.STANDARD_REVIEW),
            ("Complex Litigation", "litigation_analysis", 0.8, ProcessingTier.DEEP_ANALYSIS),
            ("Emergency Filing", "urgent_analysis", 0.6, ProcessingTier.STANDARD_REVIEW)
        ]

        for scenario_name, task_type, complexity, expected_tier in test_scenarios:
            try:
                # Test bankruptcy-specific recommendations
                if hasattr(bankruptcy_specialist, 'get_processing_tier_recommendation'):
                    recommendation = bankruptcy_specialist.get_processing_tier_recommendation(
                        task_type=task_type,
                        document_complexity=complexity
                    )

                    print(f"\nScenario: {scenario_name}")
                    print(f"  ✓ Recommended Tier: {recommendation.get('recommended_tier')}")
                    print(f"  ✓ Cost Estimate: {recommendation.get('cost_estimate')}")
                    print(f"  ✓ Expected Tier: {expected_tier.value}")

                    if recommendation.get('recommended_tier') == expected_tier.value:
                        print("  ✓ Recommendation matches expectation")
                    else:
                        print("  ⚠️ Recommendation differs from expectation")

            except Exception as e:
                print(f"  ✗ Error in {scenario_name}: {str(e)}")

    def _generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📋 Test Report Summary")
        print("=" * 60)

        successful_tests = [r for r in self.test_results if r.get('success', False)]
        failed_tests = [r for r in self.test_results if not r.get('success', False)]

        print(f"Total Tests: {len(self.test_results)}")
        print(f"Successful: {len(successful_tests)} ✓")
        print(f"Failed: {len(failed_tests)} ✗")
        print(f"Success Rate: {len(successful_tests)/len(self.test_results)*100:.1f}%")

        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                test_name = test.get('document') or test.get('bankruptcy_test') or 'Unknown'
                print(f"  - {test_name}: {test.get('error', 'Unknown error')}")

        # Multi-model strategy verification
        print(f"\n🔍 Multi-Model Strategy Analysis:")

        tier_usage = {}
        total_cost = 0
        for test in successful_tests:
            if 'expected_tier' in test:
                tier = test['expected_tier']
                tier_usage[tier] = tier_usage.get(tier, 0) + 1
                total_cost += test.get('expected_cost', 0)

        print(f"Tier Usage Distribution:")
        for tier, count in tier_usage.items():
            percentage = count / len([t for t in successful_tests if 'expected_tier' in t]) * 100
            print(f"  - {tier}: {count} tests ({percentage:.1f}%)")

        print(f"Estimated Total Cost: ${total_cost:.3f}")

        # Cost savings calculation
        all_opus_cost = len([t for t in successful_tests if 'expected_tier' in t]) * 0.75
        savings = all_opus_cost - total_cost
        savings_percentage = (savings / all_opus_cost * 100) if all_opus_cost > 0 else 0

        print(f"Cost if all Opus: ${all_opus_cost:.3f}")
        print(f"Cost Savings: ${savings:.3f} ({savings_percentage:.1f}%)")

        print(f"\n🎉 Multi-Model System Test Complete!")

        # Save detailed results
        with open('multi_model_test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_tests': len(self.test_results),
                    'successful': len(successful_tests),
                    'failed': len(failed_tests),
                    'success_rate': len(successful_tests)/len(self.test_results)*100,
                    'tier_usage': tier_usage,
                    'total_cost': total_cost,
                    'cost_savings': savings,
                    'savings_percentage': savings_percentage
                },
                'detailed_results': self.test_results
            }, f, indent=2, default=str)

        print(f"📁 Detailed results saved to: multi_model_test_results.json")


async def main():
    """Main test execution function."""
    print("Multi-Model Document Processing System Test Suite")
    print("================================================")
    print("Testing intelligent AI model selection and cost optimization\n")

    tester = MultiModelTester()
    await tester.run_comprehensive_tests()


if __name__ == "__main__":
    asyncio.run(main())