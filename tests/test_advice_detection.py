#!/usr/bin/env python3
"""
Comprehensive Advice Detection Test Suite

Tests the advice detection system against known patterns to identify
false negatives and ensure 95%+ detection accuracy.

This file validates:
1. All existing patterns continue to work
2. 12 specific false negative cases are properly detected
3. ComplianceWrapper integration functions correctly
4. Frontend ConfidenceIndicator receives proper format
"""

import pytest
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add src path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestAdviceDetection:
    """Comprehensive advice detection test suite"""

    @pytest.fixture
    def advice_detector(self):
        """Load the enhanced advice detector"""
        from src.shared.compliance.advice_detector import advice_detector
        return advice_detector

    @pytest.fixture
    def upl_compliance(self):
        """Load the UPL compliance wrapper"""
        from src.shared.compliance.upl_compliance import upl_compliance
        return upl_compliance

    def get_test_cases(self) -> List[Dict[str, Any]]:
        """Get comprehensive test cases including the 12 critical false negatives"""

        return [
            # CRITICAL FALSE NEGATIVES TO FIX
            {"text": "You might want to consider establishing a business partnership.", "contains_advice": True, "category": "business_formation"},
            {"text": "It could be beneficial to register your copyright before publishing.", "contains_advice": True, "category": "intellectual_property"},
            {"text": "You may benefit from establishing a living trust for your assets.", "contains_advice": True, "category": "estate_planning"},
            {"text": "It might be wise to register your trademark before expansion.", "contains_advice": True, "category": "intellectual_property"},
            {"text": "You may want to review your employment contract carefully.", "contains_advice": True, "category": "contract_review"},
            {"text": "It might be advisable to document workplace incidents thoroughly.", "contains_advice": True, "category": "documentation_advice"},
            {"text": "You should get a second opinion from another attorney.", "contains_advice": True, "category": "professional_services"},
            {"text": "You should probably file your claim before the deadline expires.", "contains_advice": True, "category": "timing_critical"},
            {"text": "This would help you protect your intellectual property rights.", "contains_advice": True, "category": "rights_protection"},
            {"text": "If I were you, I would establish an LLC for liability protection.", "contains_advice": True, "category": "business_structure"},
            {"text": "It might be beneficial to hire a tax attorney for this issue.", "contains_advice": True, "category": "professional_services"},
            {"text": "You could benefit from consulting with a real estate attorney.", "contains_advice": True, "category": "professional_services"},

            # HIGH-PRIORITY ADVICE PATTERNS (must maintain detection)
            {"text": "You should file a bankruptcy petition immediately.", "contains_advice": True, "category": "direct_advice"},
            {"text": "I recommend pleading guilty to get a better sentence.", "contains_advice": True, "category": "direct_advice"},
            {"text": "You must divorce your spouse to protect your assets.", "contains_advice": True, "category": "direct_advice"},
            {"text": "My advice is to settle this case for $50,000.", "contains_advice": True, "category": "direct_advice"},
            {"text": "You should countersue for damages in this situation.", "contains_advice": True, "category": "direct_advice"},
            {"text": "I advise you to fire your current attorney immediately.", "contains_advice": True, "category": "direct_advice"},
            {"text": "You need to establish a trust to avoid estate taxes.", "contains_advice": True, "category": "estate_planning"},
            {"text": "You should incorporate your business before year end.", "contains_advice": True, "category": "business_formation"},

            # SUBTLE ADVICE PATTERNS
            {"text": "It would be wise to consult an attorney about this matter.", "contains_advice": True, "category": "professional_services"},
            {"text": "Consider hiring a lawyer to review the contract.", "contains_advice": True, "category": "professional_services"},
            {"text": "You may benefit from legal consultation on this issue.", "contains_advice": True, "category": "professional_services"},
            {"text": "It could be helpful to seek professional legal advice.", "contains_advice": True, "category": "professional_services"},
            {"text": "You could explore filing a complaint with the board.", "contains_advice": True, "category": "procedural_advice"},
            {"text": "This might be worth discussing with a qualified attorney.", "contains_advice": True, "category": "professional_services"},

            # CONDITIONAL ADVICE PATTERNS
            {"text": "If this were my case, I would settle out of court.", "contains_advice": True, "category": "conditional_advice"},
            {"text": "You could file a lawsuit if you want to pursue damages.", "contains_advice": True, "category": "conditional_advice"},
            {"text": "You may want to consider bankruptcy as an option.", "contains_advice": True, "category": "financial_advice"},
            {"text": "You have the option to appeal this decision to higher court.", "contains_advice": True, "category": "procedural_advice"},

            # TIMING AND URGENCY PATTERNS
            {"text": "Act quickly to preserve your employment discrimination claim.", "contains_advice": True, "category": "timing_critical"},
            {"text": "Don't delay in filing your workers compensation claim.", "contains_advice": True, "category": "timing_critical"},
            {"text": "The sooner you file, the better your chances of success.", "contains_advice": True, "category": "timing_critical"},
            {"text": "You need to take action as soon as possible.", "contains_advice": True, "category": "timing_critical"},

            # BUSINESS AND ESTATE PLANNING
            {"text": "Consider establishing an S-Corp for tax advantages.", "contains_advice": True, "category": "business_formation"},
            {"text": "You might want to create a will before your surgery.", "contains_advice": True, "category": "estate_planning"},
            {"text": "It could be wise to set up a power of attorney.", "contains_advice": True, "category": "estate_planning"},
            {"text": "Consider registering your business name as a trademark.", "contains_advice": True, "category": "intellectual_property"},

            # SAFE EDUCATIONAL CONTENT (must not be detected as advice)
            {"text": "Bankruptcy law provides several chapters for different situations.", "contains_advice": False, "category": "educational"},
            {"text": "The legal system generally recognizes several types of contracts.", "contains_advice": False, "category": "educational"},
            {"text": "Courts typically consider various factors in custody decisions.", "contains_advice": False, "category": "educational"},
            {"text": "Employment law varies significantly between states.", "contains_advice": False, "category": "educational"},
            {"text": "Legal precedent establishes the foundation for court decisions.", "contains_advice": False, "category": "educational"},
            {"text": "The statute requires specific elements to establish liability.", "contains_advice": False, "category": "educational"},
            {"text": "Legal research shows that similar cases have succeeded.", "contains_advice": False, "category": "educational"},
            {"text": "The law provides various options for dispute resolution.", "contains_advice": False, "category": "educational"},

            # EDUCATIONAL CONTENT WITH DISCLAIMERS
            {"text": "For educational purposes only: bankruptcy involves debt discharge.", "contains_advice": False, "category": "educational_disclaimer"},
            {"text": "This is not legal advice: contract law requires consideration.", "contains_advice": False, "category": "educational_disclaimer"},
            {"text": "For informational purposes: parties can file motions to dismiss.", "contains_advice": False, "category": "educational_disclaimer"},
            {"text": "Hypothetically speaking, one could challenge the ruling.", "contains_advice": False, "category": "educational_disclaimer"},
            {"text": "As an illustration, suppose someone filed a lawsuit.", "contains_advice": False, "category": "educational_disclaimer"},
        ]

    def test_individual_patterns(self, advice_detector):
        """Test individual advice patterns to ensure all work correctly"""

        test_cases = self.get_test_cases()
        results = {
            'total_cases': len(test_cases),
            'correct_detections': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'failed_cases': []
        }

        for i, test_case in enumerate(test_cases):
            analysis = advice_detector.analyze_output(test_case['text'])
            detected_advice = analysis.requires_disclaimer
            expected_advice = test_case['contains_advice']

            is_correct = detected_advice == expected_advice

            if is_correct:
                results['correct_detections'] += 1
            elif detected_advice and not expected_advice:
                results['false_positives'] += 1
                results['failed_cases'].append({
                    'case_id': i + 1,
                    'text': test_case['text'],
                    'category': test_case['category'],
                    'error_type': 'false_positive',
                    'risk_score': analysis.risk_score,
                    'patterns_found': len(analysis.detected_patterns)
                })
            elif not detected_advice and expected_advice:
                results['false_negatives'] += 1
                results['failed_cases'].append({
                    'case_id': i + 1,
                    'text': test_case['text'],
                    'category': test_case['category'],
                    'error_type': 'false_negative',
                    'risk_score': analysis.risk_score,
                    'patterns_found': len(analysis.detected_patterns)
                })

        results['accuracy_rate'] = (results['correct_detections'] / results['total_cases']) * 100

        # Assertions for the test
        assert results['accuracy_rate'] >= 95.0, f"Accuracy {results['accuracy_rate']:.1f}% below 95% target"
        assert results['false_negatives'] == 0, f"Found {results['false_negatives']} false negatives: {[case for case in results['failed_cases'] if case['error_type'] == 'false_negative']}"
        assert results['false_positives'] <= 5, f"Too many false positives: {results['false_positives']}"

        return results

    def test_critical_false_negatives(self, advice_detector):
        """Test the 12 critical false negative cases specifically"""

        critical_cases = [
            "You might want to consider establishing a business partnership.",
            "It could be beneficial to register your copyright before publishing.",
            "You may benefit from establishing a living trust for your assets.",
            "It might be wise to register your trademark before expansion.",
            "You may want to review your employment contract carefully.",
            "It might be advisable to document workplace incidents thoroughly.",
            "You should get a second opinion from another attorney.",
            "You should probably file your claim before the deadline expires.",
            "This would help you protect your intellectual property rights.",
            "If I were you, I would establish an LLC for liability protection.",
            "It might be beneficial to hire a tax attorney for this issue.",
            "You could benefit from consulting with a real estate attorney."
        ]

        for case in critical_cases:
            analysis = advice_detector.analyze_output(case)
            assert analysis.requires_disclaimer, f"FAILED: Critical case not detected as advice: '{case}'"
            assert analysis.risk_score >= 0.25, f"FAILED: Risk score too low ({analysis.risk_score}) for: '{case}'"

    def test_threshold_adjustment(self, advice_detector):
        """Test that threshold has been properly adjusted to 0.25"""

        stats = advice_detector.get_detection_statistics()
        assert stats['advice_threshold'] == 0.25, f"Threshold should be 0.25, found {stats['advice_threshold']}"

        # Test borderline case that should trigger with 0.25 threshold
        borderline_case = "You might consider consulting with an attorney about this."
        analysis = advice_detector.analyze_output(borderline_case)

        # With 0.25 threshold, this should be detected
        assert analysis.requires_disclaimer, "Borderline case should be detected with 0.25 threshold"

    def test_compliance_wrapper_integration(self, upl_compliance):
        """Test that ComplianceWrapper properly integrates with enhanced detector"""

        test_advice = "I recommend that you file bankruptcy immediately."

        # Test wrapper response
        wrapped_result = upl_compliance.wrap_ai_output(test_advice)

        # Verify structure
        assert 'compliance_level' in wrapped_result, "Missing compliance_level in wrapped result"
        assert 'confidence_score' in wrapped_result, "Missing confidence_score in wrapped result"
        assert 'requires_attorney_review' in wrapped_result, "Missing requires_attorney_review in wrapped result"

        # Verify high-risk advice is properly flagged
        assert wrapped_result['compliance_level'] in ['high_risk', 'critical'], "High-risk advice not properly flagged"
        assert wrapped_result['requires_attorney_review'], "High-risk advice should require attorney review"

    def test_frontend_compatibility(self, advice_detector):
        """Test that output format is compatible with ConfidenceIndicator.tsx"""

        test_text = "You should consult with an attorney about this matter."
        analysis = advice_detector.analyze_output(test_text)

        # Verify confidence score is in proper format (0.0 to 1.0)
        assert 0.0 <= analysis.confidence_score <= 1.0, "Confidence score outside valid range"
        assert isinstance(analysis.confidence_score, float), "Confidence score should be float"

        # Test that confidence score works with ConfidenceIndicator thresholds
        # (0.9+ excellent, 0.8+ high, 0.6+ medium, 0.4+ low, <0.4 very low)
        confidence_level = "unknown"
        if analysis.confidence_score >= 0.9:
            confidence_level = "excellent"
        elif analysis.confidence_score >= 0.8:
            confidence_level = "high"
        elif analysis.confidence_score >= 0.6:
            confidence_level = "medium"
        elif analysis.confidence_score >= 0.4:
            confidence_level = "low"
        else:
            confidence_level = "very_low"

        assert confidence_level != "unknown", "Confidence score should map to valid level"

    def test_pattern_count_and_statistics(self, advice_detector):
        """Test that pattern statistics are correct"""

        stats = advice_detector.get_detection_statistics()

        # Verify enhanced pattern count
        assert stats['total_patterns'] >= 83, f"Should have at least 83 patterns, found {stats['total_patterns']}"
        assert stats['system_version'] == '2.0_enhanced', f"Wrong system version: {stats['system_version']}"

        # Verify pattern categories are properly distributed
        pattern_categories = stats['pattern_categories']
        total_by_category = sum(pattern_categories.values())
        assert total_by_category == stats['total_patterns'], "Pattern category counts don't match total"

    def test_educational_content_exclusions(self, advice_detector):
        """Test that educational content is properly excluded"""

        educational_cases = [
            "The legal system generally recognizes several types of contracts.",
            "Courts typically consider various factors in custody decisions.",
            "Legal precedent establishes the foundation for court decisions.",
            "Employment law varies significantly between states."
        ]

        for case in educational_cases:
            analysis = advice_detector.analyze_output(case)
            assert not analysis.requires_disclaimer, f"Educational content incorrectly flagged as advice: '{case}'"

    @pytest.mark.performance
    def test_performance_benchmarks(self, advice_detector):
        """Test that advice detection meets performance requirements"""

        import time

        test_text = "You should file a lawsuit against your employer for discrimination."

        # Test response time
        start_time = time.time()
        analysis = advice_detector.analyze_output(test_text)
        end_time = time.time()

        response_time = end_time - start_time
        assert response_time < 0.1, f"Detection too slow: {response_time:.3f}s (should be <0.1s)"

        # Test batch processing
        batch_texts = [test_text] * 100

        start_time = time.time()
        for text in batch_texts:
            advice_detector.analyze_output(text)
        end_time = time.time()

        batch_time = end_time - start_time
        avg_time = batch_time / len(batch_texts)
        assert avg_time < 0.05, f"Average batch time too slow: {avg_time:.3f}s (should be <0.05s)"

    def run_full_validation(self, advice_detector):
        """Run complete validation suite and return comprehensive results"""

        test_cases = self.get_test_cases()
        accuracy_results = advice_detector.test_detection_accuracy(test_cases)

        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'total_test_cases': len(test_cases),
            'accuracy_rate': accuracy_results['accuracy_rate'],
            'target_met': accuracy_results['accuracy_rate'] >= 95.0,
            'false_negatives': accuracy_results['false_negatives'],
            'false_positives': accuracy_results['false_positives'],
            'system_statistics': advice_detector.get_detection_statistics(),
            'detailed_results': accuracy_results
        }

        return validation_results

if __name__ == "__main__":
    """Run standalone validation"""

    # Run tests manually if not using pytest
    import sys
    import os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    from src.shared.compliance.advice_detector import advice_detector
    from src.shared.compliance.upl_compliance import upl_compliance

    test_suite = TestAdviceDetection()

    print("Running comprehensive advice detection validation...")

    try:
        # Run individual tests
        pattern_results = test_suite.test_individual_patterns(advice_detector)
        print(f"[PASS] Individual patterns test: {pattern_results['accuracy_rate']:.1f}% accuracy")

        test_suite.test_critical_false_negatives(advice_detector)
        print("[PASS] Critical false negatives test: All 12 cases detected")

        test_suite.test_threshold_adjustment(advice_detector)
        print("[PASS] Threshold adjustment test: Properly set to 0.25")

        test_suite.test_compliance_wrapper_integration(upl_compliance)
        print("[PASS] ComplianceWrapper integration test: Working correctly")

        test_suite.test_frontend_compatibility(advice_detector)
        print("[PASS] Frontend compatibility test: ConfidenceIndicator compatible")

        test_suite.test_pattern_count_and_statistics(advice_detector)
        print("[PASS] Pattern statistics test: All metrics correct")

        test_suite.test_educational_content_exclusions(advice_detector)
        print("[PASS] Educational exclusions test: Properly filtered")

        # Generate final validation report
        validation_results = test_suite.run_full_validation(advice_detector)

        print(f"\n=== FINAL VALIDATION RESULTS ===")
        print(f"Overall Accuracy: {validation_results['accuracy_rate']:.1f}%")
        print(f"Target Met (95%+): {validation_results['target_met']}")
        print(f"False Negatives: {validation_results['false_negatives']}")
        print(f"False Positives: {validation_results['false_positives']}")
        print(f"Total Patterns: {validation_results['system_statistics']['total_patterns']}")
        print(f"Threshold: {validation_results['system_statistics']['advice_threshold']}")

        if validation_results['target_met']:
            print("\n[SUCCESS] ALL TESTS PASSED - Advice detection ready for production!")
        else:
            print("\n[WARNING] Some tests failed - review results above")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        sys.exit(1)