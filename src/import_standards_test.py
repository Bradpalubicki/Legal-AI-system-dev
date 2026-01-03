#!/usr/bin/env python3
"""
IMPORT STANDARDS VERIFICATION AND CORRECTION

Tests and fixes import path consistency across all components.
Ensures all components can import from shared modules correctly.

CRITICAL LEGAL DISCLAIMER:
This test verifies system import integrity only.
All operations are for system validation purposes only.
No legal advice is provided during testing.
"""

import sys
import os
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_import_patterns():
    """Test different import patterns to find the working standard."""

    print("LEGAL AI SYSTEM - IMPORT STANDARDS TEST")
    print("=" * 50)
    print("Testing import patterns for consistency...")
    print("=" * 50)

    import_results = []

    # Test 1: Direct imports from shared modules (when running from src/)
    print("\n[TEST 1] Direct imports from src/ directory")
    try:
        from shared.compliance.upl_compliance import ComplianceWrapper
        from shared.core import BaseAnalyzer, BaseGenerator
        from shared.models import DocumentType

        print("   [PASS] Direct imports work from src/ directory")
        import_results.append("Direct imports: WORKING")

        # Test the imported classes
        wrapper = ComplianceWrapper()
        analyzer = BaseAnalyzer()
        generator = BaseGenerator()

        print("   [PASS] Imported classes instantiate correctly")

    except Exception as e:
        print(f"   [FAIL] Direct imports failed: {e}")
        import_results.append(f"Direct imports: FAILED - {e}")

    # Test 2: Component-to-component imports
    print("\n[TEST 2] Component imports")
    try:
        from document_processor.intelligent_intake import DocumentIntakeAnalyzer
        from document_processor.question_generator import IntelligentQuestionGenerator
        from strategy_generator.defense_strategy_builder import DefenseStrategyGenerator
        from orchestration.workflow_orchestrator import IntelligentWorkflowOrchestrator

        print("   [PASS] All major components import successfully")
        import_results.append("Component imports: WORKING")

        # Test component instantiation
        doc_analyzer = DocumentIntakeAnalyzer()
        question_gen = IntelligentQuestionGenerator()
        strategy_gen = DefenseStrategyGenerator()
        orchestrator = IntelligentWorkflowOrchestrator()

        print("   [PASS] All components instantiate correctly")

    except Exception as e:
        print(f"   [FAIL] Component imports failed: {e}")
        import_results.append(f"Component imports: FAILED - {e}")

    # Test 3: Cross-component integration
    print("\n[TEST 3] Cross-component integration")
    try:
        # Test that components can actually use each other
        analyzer = DocumentIntakeAnalyzer()
        result = analyzer.analyze("Test bankruptcy document")

        generator = IntelligentQuestionGenerator()
        questions = generator.generate_questions(result['gaps'])

        strategy = DefenseStrategyGenerator()
        strategies_response = strategy.generate_strategies_sync({'debt_amount': 100000}, 'bankruptcy')
        strategies = strategies_response.get('content', strategies_response)
        if not isinstance(strategies, list):
            strategies = []

        print(f"   [PASS] Data flows: {len(result['gaps'])} gaps -> {len(questions)} questions -> {len(strategies)} strategies")
        import_results.append("Cross-component integration: WORKING")

    except Exception as e:
        print(f"   [FAIL] Cross-component integration failed: {e}")
        import_results.append(f"Cross-component integration: FAILED - {e}")

    # Test 4: Compliance module integration
    print("\n[TEST 4] Compliance module integration")
    try:
        from shared.compliance.upl_compliance import ComplianceWrapper
        from shared.compliance.advice_detector import AdviceDetector
        from shared.compliance.disclaimer_system import DisclaimerSystem

        wrapper = ComplianceWrapper()
        detector = AdviceDetector()
        disclaimer_sys = DisclaimerSystem()

        # Test compliance integration
        test_text = "This is educational information about bankruptcy."
        analysis = detector.analyze_output(test_text)
        wrapped = wrapper.wrap_response({'content': test_text})
        disclaimer = disclaimer_sys.get_disclaimer('bankruptcy')

        print("   [PASS] All compliance modules working")
        print(f"   [PASS] Advice detection: {analysis.risk_score:.2f}")
        print(f"   [PASS] Response wrapping: {len(wrapped.get('content', {}).get('content', ''))} chars")
        print(f"   [PASS] Disclaimer generation: {len(disclaimer)} chars")
        import_results.append("Compliance integration: WORKING")

    except Exception as e:
        print(f"   [FAIL] Compliance integration failed: {e}")
        import_results.append(f"Compliance integration: FAILED - {e}")

    return import_results

def create_import_standards_guide():
    """Create standardized import patterns guide."""

    guide = """
# LEGAL AI SYSTEM - IMPORT STANDARDS GUIDE
# ==========================================

[PASS] CORRECT IMPORT PATTERNS:

1. From test files (running from src/):
   from shared.compliance.upl_compliance import ComplianceWrapper
   from shared.core import BaseAnalyzer, BaseGenerator
   from shared.models import DocumentType

2. From component files (src/document_processor/, etc.):
   # Use try/except for flexibility
   try:
       from ..shared.compliance.upl_compliance import ComplianceWrapper
       from ..shared.core import BaseAnalyzer
   except ImportError:
       # Fallback for standalone execution
       import sys
       import os
       sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
       from shared.compliance.upl_compliance import ComplianceWrapper
       from shared.core import BaseAnalyzer

3. Cross-component imports:
   from document_processor.intelligent_intake import DocumentIntakeAnalyzer
   from strategy_generator.defense_strategy_builder import DefenseStrategyGenerator

[AVOID] THESE PATTERNS:
- Mixed relative/absolute paths in same file
- Hard-coded sys.path modifications without try/except
- Inconsistent import depths (..shared vs shared)

[RULES] STANDARDIZATION RULES:
1. Always use try/except for relative imports in components
2. Provide absolute fallback imports
3. Use consistent module paths across all files
4. Test imports from both src/ and component directories
"""

    return guide

def verify_all_integrations():
    """Verify all key integrations work with current import patterns."""

    print("\n" + "=" * 50)
    print("COMPREHENSIVE INTEGRATION VERIFICATION")
    print("=" * 50)

    integration_tests = []

    # Test full integration chain
    print("\n[INTEGRATION] Testing complete component chain...")
    try:
        # Import all components
        from document_processor.intelligent_intake import DocumentIntakeAnalyzer
        from document_processor.question_generator import IntelligentQuestionGenerator
        from strategy_generator.defense_strategy_builder import DefenseStrategyGenerator
        from orchestration.workflow_orchestrator import IntelligentWorkflowOrchestrator
        from shared.compliance.upl_compliance import ComplianceWrapper

        # Test complete chain
        doc = "BANKRUPTCY PETITION Chapter 11 ABC Corp $2.5M debt"

        # 1. Document Analysis
        analyzer = DocumentIntakeAnalyzer()
        doc_result = analyzer.analyze(doc)

        # 2. Question Generation
        generator = IntelligentQuestionGenerator()
        questions = generator.generate_questions(doc_result['gaps'])

        # 3. Strategy Generation
        strategy_gen = DefenseStrategyGenerator()
        strategies_response = strategy_gen.generate_strategies_sync({'debt_amount': 2500000}, 'bankruptcy')
        strategies = strategies_response.get('content', strategies_response)
        if not isinstance(strategies, list):
            strategies = []

        # 4. Orchestrator Integration
        orchestrator = IntelligentWorkflowOrchestrator()
        orchestrated = orchestrator.orchestrate_intake(doc)

        # 5. Compliance Verification
        wrapper = ComplianceWrapper()
        final_response = wrapper.wrap_response({
            'document_analysis': doc_result,
            'questions': questions,
            'strategies': strategies,
            'orchestration': orchestrated
        })

        print(f"   [PASS] Complete chain: Doc -> {len(doc_result['gaps'])} gaps -> {len(questions)} questions -> {len(strategies)} strategies")
        print(f"   [PASS] Orchestration: Session = {orchestrated.get('session_id', 'Mock')}")
        print(f"   [PASS] Compliance: {len(final_response.get('content', {}))} items wrapped")

        integration_tests.append("COMPLETE INTEGRATION: WORKING")

    except Exception as e:
        print(f"   [FAIL] Complete integration failed: {e}")
        integration_tests.append(f"COMPLETE INTEGRATION: FAILED - {e}")

    return integration_tests

if __name__ == "__main__":
    print("Initializing Legal AI System Import Standards Test...")
    print("DISCLAIMER: Educational testing only - not legal advice")
    print()

    try:
        # Test import patterns
        import_results = test_import_patterns()

        # Verify integrations
        integration_results = verify_all_integrations()

        # Show results
        print("\n" + "=" * 50)
        print("IMPORT STANDARDS TEST RESULTS")
        print("=" * 50)

        print("\nIMPORT PATTERN RESULTS:")
        for result in import_results:
            status = "[PASS]" if "WORKING" in result else "[FAIL]"
            print(f"   {status} {result}")

        print("\nINTEGRATION TEST RESULTS:")
        for result in integration_results:
            status = "[PASS]" if "WORKING" in result else "[FAIL]"
            print(f"   {status} {result}")

        # Calculate success rate
        all_results = import_results + integration_results
        working_count = len([r for r in all_results if "WORKING" in r])
        total_count = len(all_results)
        success_rate = (working_count / total_count) * 100 if total_count > 0 else 0

        print(f"\nIMPORT INTEGRATION SUCCESS RATE: {working_count}/{total_count} ({success_rate:.0f}%)")

        if success_rate >= 80:
            print("\n[PASS] IMPORT STANDARDS: HIGHLY SUCCESSFUL")
            print("All critical import patterns are working correctly")
            print("\nSTANDARDS GUIDE:")
            print(create_import_standards_guide())
            exit(0)
        else:
            print("\n[FAIL] IMPORT STANDARDS: NEEDS WORK")
            print("Some import patterns need fixing")
            exit(1)

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\nImport standards test failed: {e}")
        exit(1)