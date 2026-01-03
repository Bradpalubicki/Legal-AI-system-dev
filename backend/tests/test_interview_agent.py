"""
Test Interview Agent Integration with Unified System
This script verifies that the Interview Agent enforces questions before defense building
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_interview_flow():
    """Test complete interview flow"""

    session_id = f"test_session_{int(time.time())}"

    print("\n=== TEST 1: Upload Document ===")
    print("Uploading a debt collection lawsuit...")

    response = requests.post(f"{API_BASE}/api/v1/unified/process", json={
        "sessionId": session_id,
        "action": "upload_document",
        "data": {
            "documentText": """
            SUMMONS AND COMPLAINT

            MIDLAND CREDIT MANAGEMENT vs JOHN DOE
            Case No: 2024-CV-12345

            Plaintiff alleges defendant owes $4,523.67 in unpaid credit card debt.
            Original creditor: Chase Bank
            Date of last payment: Unknown

            Plaintiff demands judgment for $4,523.67 plus interest and court costs.
            """
        }
    })

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Action: {data.get('action')}")
    print(f"Can build defense: {data.get('can_build_defense')}")
    print(f"First question: {data.get('first_question', {}).get('text')}")

    if not data.get('first_question'):
        print("❌ FAILED: No question returned")
        return False

    print("\n=== TEST 2: Try Building Defense Before Answering Questions ===")
    print("Attempting to build defense WITHOUT answering questions...")

    response = requests.post(f"{API_BASE}/api/v1/unified/process", json={
        "sessionId": session_id,
        "action": "build_defense",
        "data": {}
    })

    data = response.json()
    print(f"Status: {response.status_code}")

    if data.get('error'):
        print(f"✅ PASS: Agent blocked defense building")
        print(f"Message: {data.get('message')}")
        print(f"Questions remaining: {data.get('questions_remaining')}")
    else:
        print("❌ FAILED: Agent allowed defense building without questions!")
        return False

    print("\n=== TEST 3: Answer Questions ===")

    # Answer question 1
    first_q_id = data.get('current_question', {}).get('id', 'last_payment')

    print(f"Answering question: {first_q_id}")
    response = requests.post(f"{API_BASE}/api/v1/unified/process", json={
        "sessionId": session_id,
        "action": "answer_question",
        "data": {
            "questionId": first_q_id,
            "answer": "Over 5 years ago"
        }
    })

    data = response.json()
    print(f"Progress: {data.get('progress', 0) * 100:.0f}%")
    print(f"Defense found: {data.get('defense_found')}")
    print(f"Can build defense: {data.get('can_build_defense')}")

    # Answer remaining questions
    question_count = 1
    while data.get('next_question') and question_count < 5:
        question_count += 1
        question = data['next_question']

        print(f"\nQuestion {question_count}: {question.get('text')}")

        # Use first option
        answer = question.get('options', ['Yes'])[0]
        print(f"Answering: {answer}")

        response = requests.post(f"{API_BASE}/api/v1/unified/process", json={
            "sessionId": session_id,
            "action": "answer_question",
            "data": {
                "questionId": question.get('id'),
                "answer": answer
            }
        })

        data = response.json()
        print(f"Progress: {data.get('progress', 0) * 100:.0f}%")

    if not data.get('complete'):
        print("❌ FAILED: Interview didn't complete")
        return False

    print("\n✅ PASS: Interview completed")
    print(f"Can build defense: {data.get('can_build_defense')}")

    print("\n=== TEST 4: Build Defense After Questions ===")

    response = requests.post(f"{API_BASE}/api/v1/unified/process", json={
        "sessionId": session_id,
        "action": "build_defense",
        "data": {}
    })

    data = response.json()

    if data.get('error'):
        print(f"❌ FAILED: {data.get('error')}")
        return False

    print("✅ PASS: Defense built successfully")
    print(f"\nDefenses found: {len(data.get('defenses', []))}")

    for i, defense in enumerate(data.get('defenses', [])[:3], 1):
        print(f"\n{i}. {defense.get('name')}")
        print(f"   Strength: {defense.get('strength')}")
        print(f"   Action: {defense.get('action')}")

    print("\n=== TEST 5: System Efficiency ===")

    response = requests.get(f"{API_BASE}/api/v1/unified/sessions/stats")
    stats = response.json()

    print(f"Total sessions: {stats.get('total_sessions')}")
    print(f"Total AI calls: {stats.get('total_ai_calls')}")
    print(f"Cached responses: {stats.get('total_cached_responses')}")
    print(f"Cache rate: {stats.get('overall_cache_rate', 0) * 100:.0f}%")

    print("\n✅ ALL TESTS PASSED!")
    return True

if __name__ == "__main__":
    try:
        test_interview_flow()
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
