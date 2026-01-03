"""
Test suite for verifying concise, defense-focused AI behavior
Tests the enhanced Q&A system with Claude Haiku optimization
"""

import pytest
import requests
import json
import time
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
QA_ENDPOINT = f"{API_BASE_URL}/api/v1/qa/ask"
DEFENSE_ENDPOINT = f"{API_BASE_URL}/api/v1/defense/analyze"

# Sample test documents
DEBT_COLLECTION_DOC = {
    "document_text": "COMPLAINT FOR MONEY OWED - Plaintiff seeks $5,000 in unpaid credit card debt plus interest and fees. Defendant failed to make payments for 6 months.",
    "document_analysis": {
        "document_type": "complaint",
        "summary": "Credit card debt collection lawsuit for $5,000",
        "parties": ["Credit Card Company", "Defendant"],
        "case_number": "CV-2024-001",
        "court": "District Court"
    }
}

EVICTION_DOC = {
    "document_text": "NOTICE TO QUIT - Tenant must vacate premises within 30 days for non-payment of rent in the amount of $2,400 for months of October and November.",
    "document_analysis": {
        "document_type": "eviction notice",
        "summary": "30-day notice to quit for unpaid rent",
        "parties": ["Landlord", "Tenant"],
        "case_number": "EV-2024-101"
    }
}

class AIClient:
    """Test client for AI API interactions"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

    def ask(self, question: str, doc_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ask a question to the Q&A system"""
        payload = {
            "document_text": doc_context.get("document_text", "General legal question") if doc_context else "General legal question",
            "document_analysis": doc_context.get("document_analysis", {"document_type": "general"}) if doc_context else {"document_type": "general"},
            "question": question
        }

        response = self.session.post(QA_ENDPOINT, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def analyze_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a document for defense strategies"""
        response = self.session.post(DEFENSE_ENDPOINT, json={"message": doc_data["document_text"]}, timeout=30)
        response.raise_for_status()
        return response.json()

# Initialize test client
ai_client = AIClient()

class TestResponseLength:
    """Test response conciseness and clarity"""

    def test_response_under_word_limit(self):
        """Verify responses are concise - under 100 words"""
        response = ai_client.ask("What should I do about this lawsuit?", DEBT_COLLECTION_DOC)

        answer = response.get("answer", "")
        word_count = len(answer.split())

        assert word_count < 100, f"Response too long: {word_count} words. Answer: {answer}"
        assert word_count > 10, f"Response too short: {word_count} words. Answer: {answer}"

    def test_no_verbose_language(self):
        """Verify responses avoid metaphors and verbose phrases"""
        response = ai_client.ask("How do I defend against eviction?", EVICTION_DOC)

        answer = response.get("answer", "").lower()

        # Check for verbose phrases that should be removed
        forbidden_phrases = [
            "metaphor", "imagine", "think of it this way", "let me explain",
            "for example, if you", "it's like when you", "just like",
            "to put it simply", "in other words", "the bottom line is"
        ]

        for phrase in forbidden_phrases:
            assert phrase not in answer, f"Found forbidden phrase '{phrase}' in response: {answer}"

    def test_response_has_substance(self):
        """Verify responses contain actual legal information"""
        response = ai_client.ask("What defenses are available for unpaid rent?", EVICTION_DOC)

        answer = response.get("answer", "").lower()

        # Should contain substantive legal concepts
        legal_terms = ["defense", "law", "legal", "court", "rights", "evidence", "notice", "requirement"]
        found_terms = [term for term in legal_terms if term in answer]

        assert len(found_terms) >= 2, f"Response lacks legal substance. Found terms: {found_terms}. Answer: {answer}"


class TestDefenseOptionsProvided:
    """Test that actual defense options are provided"""

    def test_defense_options_structure(self):
        """Verify defense options are provided in correct format"""
        response = ai_client.ask("What are my defense options?", DEBT_COLLECTION_DOC)

        # Should have defense options in the new format
        assert "defense_options" in response, f"Missing defense_options in response: {response.keys()}"

        defense_options = response["defense_options"]
        assert isinstance(defense_options, list), f"defense_options should be a list: {type(defense_options)}"
        assert len(defense_options) >= 3, f"Should provide at least 3 defense options: {len(defense_options)}"

    def test_defense_options_content(self):
        """Verify defense options contain relevant legal strategies"""
        response = ai_client.ask("How do I fight this debt collection case?", DEBT_COLLECTION_DOC)

        defense_options = response.get("defense_options", [])
        all_defenses = " ".join(defense_options).lower()

        # Common debt collection defenses
        expected_defenses = [
            "statute of limitations", "validation", "amount", "standing",
            "documentation", "improper service", "settlement"
        ]

        found_defenses = [defense for defense in expected_defenses if defense in all_defenses]
        assert len(found_defenses) >= 2, f"Should mention relevant defenses. Found: {found_defenses}. Defenses: {defense_options}"

    def test_quick_actions_provided(self):
        """Verify quick action buttons are provided"""
        response = ai_client.ask("I need help with my case", DEBT_COLLECTION_DOC)

        assert "quick_actions" in response, f"Missing quick_actions in response: {response.keys()}"

        quick_actions = response["quick_actions"]
        assert isinstance(quick_actions, list), f"quick_actions should be a list: {type(quick_actions)}"
        assert len(quick_actions) >= 3, f"Should provide at least 3 quick actions: {len(quick_actions)}"

        # Should contain action-oriented language
        all_actions = " ".join(quick_actions).lower()
        action_words = ["what", "how", "should", "do", "evidence", "defenses"]
        found_actions = [word for word in action_words if word in all_actions]
        assert len(found_actions) >= 3, f"Quick actions should be action-oriented. Found: {found_actions}. Actions: {quick_actions}"


class TestProactiveQuestions:
    """Test that system asks proactive questions to build defense"""

    def test_follow_up_questions_provided(self):
        """Verify system asks follow-up questions"""
        response = ai_client.ask("I got sued for credit card debt", DEBT_COLLECTION_DOC)

        assert "follow_up_questions" in response, f"Missing follow_up_questions in response: {response.keys()}"

        follow_ups = response["follow_up_questions"]
        assert isinstance(follow_ups, list), f"follow_up_questions should be a list: {type(follow_ups)}"
        assert len(follow_ups) >= 1, f"Should provide at least 1 follow-up question: {len(follow_ups)}"

        # Follow-up questions should contain question marks
        for question in follow_ups:
            assert "?" in question, f"Follow-up should be a question: {question}"

    def test_questions_are_case_specific(self):
        """Verify questions are relevant to the case type"""
        response = ai_client.ask("Help me with my eviction case", EVICTION_DOC)

        follow_ups = response.get("follow_up_questions", [])
        all_questions = " ".join(follow_ups).lower()

        # Should ask about eviction-specific issues
        eviction_terms = ["rent", "notice", "lease", "payment", "landlord", "property", "deposit"]
        found_terms = [term for term in eviction_terms if term in all_questions]

        assert len(found_terms) >= 1, f"Questions should be eviction-specific. Found: {found_terms}. Questions: {follow_ups}"

    def test_questions_gather_defense_info(self):
        """Verify questions help gather information for building defenses"""
        response = ai_client.ask("They're trying to collect a debt from me", DEBT_COLLECTION_DOC)

        follow_ups = response.get("follow_up_questions", [])
        all_questions = " ".join(follow_ups).lower()

        # Should ask about evidence, timing, documentation
        defense_info = ["when", "evidence", "documentation", "notice", "amount", "validation", "how much"]
        found_info = [info for info in defense_info if info in all_questions]

        assert len(found_info) >= 1, f"Questions should gather defense information. Found: {found_info}. Questions: {follow_ups}"


class TestResponseTime:
    """Test response time and performance"""

    def test_response_time_under_5_seconds(self):
        """Verify responses are fast (under 5 seconds with Claude Haiku)"""
        start_time = time.time()

        response = ai_client.ask("What should I do about this lawsuit?", DEBT_COLLECTION_DOC)

        end_time = time.time()
        response_time = end_time - start_time

        assert response_time < 5.0, f"Response too slow: {response_time:.2f} seconds"
        assert "answer" in response, "Should return valid response structure"

    def test_concurrent_requests(self):
        """Verify system handles multiple requests efficiently"""
        import concurrent.futures

        def make_request():
            return ai_client.ask("Quick legal question", DEBT_COLLECTION_DOC)

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request) for _ in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        assert len(results) == 3, "Should handle all concurrent requests"
        assert total_time < 10.0, f"Concurrent requests too slow: {total_time:.2f} seconds"


class TestNewResponseFormat:
    """Test the enhanced response format"""

    def test_enhanced_qa_response_type(self):
        """Verify responses use the new enhanced format"""
        response = ai_client.ask("What are my options?", DEBT_COLLECTION_DOC)

        # Should indicate enhanced format
        assert response.get("response_type") == "enhanced_qa", f"Should use enhanced_qa format: {response.get('response_type')}"

    def test_all_required_fields_present(self):
        """Verify all required fields are present in response"""
        response = ai_client.ask("Help me understand my legal situation", DEBT_COLLECTION_DOC)

        required_fields = ["answer", "defense_options", "follow_up_questions", "quick_actions"]

        for field in required_fields:
            assert field in response, f"Missing required field '{field}' in response: {response.keys()}"

    def test_backward_compatibility(self):
        """Verify legacy fields are still available"""
        response = ai_client.ask("Legal question", DEBT_COLLECTION_DOC)

        # Legacy fields should still be present
        legacy_fields = ["session_id", "answer", "confidence", "timestamp"]

        for field in legacy_fields:
            assert field in response, f"Missing legacy field '{field}' for backward compatibility"


# Utility functions for running tests
def run_all_tests():
    """Run all test classes"""
    test_classes = [
        TestResponseLength,
        TestDefenseOptionsProvided,
        TestProactiveQuestions,
        TestResponseTime,
        TestNewResponseFormat
    ]

    results = {}

    for test_class in test_classes:
        print(f"\n=== Running {test_class.__name__} ===")
        class_results = {}

        # Get test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]

        for method_name in test_methods:
            try:
                test_instance = test_class()
                test_method = getattr(test_instance, method_name)
                test_method()
                print(f"PASS {method_name}")
                class_results[method_name] = "PASSED"
            except Exception as e:
                print(f"FAIL {method_name}: {str(e)}")
                class_results[method_name] = f"FAILED: {str(e)}"

        results[test_class.__name__] = class_results

    return results

def print_summary(results):
    """Print test summary"""
    total_tests = 0
    passed_tests = 0

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for class_name, class_results in results.items():
        passed = len([r for r in class_results.values() if r == "PASSED"])
        total = len(class_results)
        total_tests += total
        passed_tests += passed

        print(f"{class_name}: {passed}/{total} passed")

        # Show failed tests
        failed = [name for name, result in class_results.items() if result != "PASSED"]
        if failed:
            for test_name in failed:
                print(f"  FAIL {test_name}")

    print(f"\nOVERALL: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")

    if passed_tests == total_tests:
        print("SUCCESS: ALL TESTS PASSED - Concise defense system is working correctly!")
    else:
        print(f"WARNING: {total_tests - passed_tests} tests failed - see details above")

if __name__ == "__main__":
    print("Testing Concise Defense-Focused AI Behavior")
    print("=" * 50)

    try:
        # Check if API is available
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        health_response.raise_for_status()
        print("PASS: API is available")

        # Run tests
        results = run_all_tests()
        print_summary(results)

    except requests.exceptions.RequestException as e:
        print(f"FAIL: API not available: {e}")
        print("Please ensure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"FAIL: Test execution failed: {e}")