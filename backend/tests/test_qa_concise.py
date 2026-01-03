"""
Test Concise Q&A Handler
Verifies responses are always concise and never verbose
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_concise_qa():
    """Test that Q&A responses are always concise"""

    session_id = "test_qa_concise"

    # Test various questions
    questions = [
        "I got sued for debt collection",
        "What should I do about this lawsuit?",
        "When is the deadline?",
        "Do I need a lawyer?",
        "What about bankruptcy?",
        "How do I go to court?",
        "Should I pay this debt?",
        "What if they didn't serve me properly?",
        "Can they garnish my wages?",
        "How do I file a motion to dismiss?"
    ]

    print("=== TESTING CONCISE Q&A HANDLER ===\n")

    for i, question in enumerate(questions, 1):
        print(f"{i}. Question: {question}")

        response = requests.post(f"{API_BASE}/api/v1/unified/process", json={
            "sessionId": session_id,
            "action": "chat_message",
            "data": {
                "message": question
            }
        })

        if response.status_code != 200:
            print(f"   ❌ ERROR: {response.status_code}")
            continue

        data = response.json()
        answer = data.get('response', '')
        word_count = data.get('word_count', len(answer.split()))
        model = data.get('model', 'unknown')

        print(f"   Answer: {answer}")
        print(f"   Words: {word_count}")
        print(f"   Model: {model}")

        # Check for conciseness
        if word_count > 50:
            print(f"   ⚠️  WARNING: Response too long ({word_count} words)")
        else:
            print(f"   ✅ PASS: Concise ({word_count} words)")

        # Check for verbose phrases
        verbose_phrases = [
            "let's pretend",
            "imagine you",
            "picture this",
            "think of it like",
            "okay, let's",
            "simple words",
            "everyday example"
        ]

        found_verbose = False
        for phrase in verbose_phrases:
            if phrase.lower() in answer.lower():
                print(f"   ❌ FAIL: Contains verbose phrase '{phrase}'")
                found_verbose = True

        if not found_verbose:
            print(f"   ✅ PASS: No verbose language")

        print()

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    try:
        test_concise_qa()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
