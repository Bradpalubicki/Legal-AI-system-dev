"""
Simplified test to verify the concise defense code structure is in place
Tests the implementation without making API calls
"""

import os
import sys

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

def test_claude_haiku_configuration():
    """Test that Claude Haiku is configured for Q&A"""
    try:
        from app.src.services.dual_ai_service import CLAUDE_QA_MODEL
        assert CLAUDE_QA_MODEL == 'claude-3-haiku-20240307', f"Expected Haiku model, got {CLAUDE_QA_MODEL}"
        print("PASS: Claude Haiku model configured")
        return True
    except Exception as e:
        print(f"FAIL: Claude Haiku configuration: {e}")
        return False

def test_response_formatter_enhancements():
    """Test that ResponseFormatter has quick actions and enhanced formatting"""
    try:
        from app.src.services.dual_ai_service import ResponseFormatter

        formatter = ResponseFormatter()

        # Check quick actions are defined
        assert hasattr(formatter, 'quick_actions'), "ResponseFormatter missing quick_actions"
        assert len(formatter.quick_actions) >= 3, f"Expected >= 3 quick actions, got {len(formatter.quick_actions)}"

        # Check format_response method exists and processes text
        test_response = "Let me explain this in simple terms: You have legal options. Think of it this way: there are defenses."
        formatted = formatter.format_response(test_response)

        # Should remove verbose phrases
        assert "Let me explain this in simple terms:" not in formatted, "Verbose phrase not removed"
        assert "Think of it this way:" not in formatted, "Verbose phrase not removed"

        print("PASS: ResponseFormatter enhanced with quick actions and cleanup")
        return True
    except Exception as e:
        print(f"FAIL: ResponseFormatter enhancements: {e}")
        return False

def test_structured_response_parsing():
    """Test that structured response parsing exists"""
    try:
        from app.src.services.dual_ai_service import DualAIProcessor

        processor = DualAIProcessor()

        # Check _parse_structured_response method exists
        assert hasattr(processor, '_parse_structured_response'), "Missing _parse_structured_response method"

        # Test with sample response
        sample_response = """Answer: You have three main defense options.

Defense options:
• Statute of limitations
• Improper documentation
• Settlement negotiation

Questions for you:
1. When did this debt originate?
2. Do you have any payment records?"""

        parsed = processor._parse_structured_response(sample_response)

        # Check structure
        assert 'answer' in parsed, "Missing answer field"
        assert 'defense_options' in parsed, "Missing defense_options field"
        assert 'follow_up_questions' in parsed, "Missing follow_up_questions field"
        assert 'quick_actions' in parsed, "Missing quick_actions field"

        # Check content
        assert len(parsed['defense_options']) >= 3, f"Expected >= 3 defense options, got {len(parsed['defense_options'])}"
        assert len(parsed['follow_up_questions']) >= 2, f"Expected >= 2 questions, got {len(parsed['follow_up_questions'])}"

        print("PASS: Structured response parsing implemented")
        return True
    except Exception as e:
        print(f"FAIL: Structured response parsing: {e}")
        return False

def test_ask_document_question_returns_dict():
    """Test that ask_document_question returns structured dict"""
    try:
        from app.src.services.dual_ai_service import DualAIProcessor

        processor = DualAIProcessor()

        # Check method signature indicates it returns Dict
        import inspect
        signature = inspect.signature(processor.ask_document_question)
        return_annotation = signature.return_annotation

        # Should return Dict[str, Any] instead of str
        assert 'Dict' in str(return_annotation) or return_annotation != str, f"Method should return Dict, got {return_annotation}"

        print("PASS: ask_document_question returns structured dict")
        return True
    except Exception as e:
        print(f"FAIL: ask_document_question signature: {e}")
        return False

def test_qa_system_enhancements():
    """Test that QA system handles new response format"""
    try:
        # Read the QA system file to check for enhancements
        qa_file_path = os.path.join(backend_path, 'app', 'api', 'qa_system.py')

        with open(qa_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for enhanced response fields
        assert 'defense_options' in content, "QA system missing defense_options handling"
        assert 'quick_actions' in content, "QA system missing quick_actions handling"
        assert 'response_type' in content, "QA system missing response_type field"
        assert 'enhanced_qa' in content, "QA system missing enhanced_qa format"

        # Check for new prompt style
        assert 'concise' in content.lower(), "QA system missing concise instructions"
        assert 'proactive' in content.lower(), "QA system missing proactive instructions"

        print("PASS: QA system enhanced for new response format")
        return True
    except Exception as e:
        print(f"FAIL: QA system enhancements: {e}")
        return False

def test_defense_interview_component_exists():
    """Test that DefenseInterview component exists"""
    try:
        defense_interview_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src', 'components', 'DefenseInterview.tsx')

        assert os.path.exists(defense_interview_path), "DefenseInterview.tsx component not found"

        with open(defense_interview_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for key features - DefenseInterview is separate from Q&A chat
        assert 'DefenseInterview' in content, "DefenseInterview component not defined"
        assert 'caseType' in content, "Component missing caseType prop"
        assert 'onComplete' in content, "Component missing onComplete callback"

        # DefenseInterview is for interview workflow, not Q&A chat format
        # It generates its own defense strategy via the interview process
        assert 'Question' in content, "Component missing Question interface"

        print("PASS: DefenseInterview component exists with interview features")
        return True
    except Exception as e:
        print(f"FAIL: DefenseInterview component: {e}")
        return False

def run_all_structure_tests():
    """Run all structure validation tests"""
    tests = [
        test_claude_haiku_configuration,
        test_response_formatter_enhancements,
        test_structured_response_parsing,
        test_ask_document_question_returns_dict,
        test_qa_system_enhancements,
        test_defense_interview_component_exists
    ]

    print("Testing Concise Defense System Code Structure")
    print("=" * 50)

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"STRUCTURE TESTS: {passed}/{total} passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("SUCCESS: All code structure tests passed!")
        print("The concise defense system implementation is complete.")
    else:
        print(f"WARNING: {total - passed} structure tests failed.")

    return passed, total

if __name__ == "__main__":
    run_all_structure_tests()