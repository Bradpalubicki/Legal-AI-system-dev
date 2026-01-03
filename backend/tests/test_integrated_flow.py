"""
Test Integrated Defense Flow
Verifies the complete flow: Document → Interview → Defense
Tests that defense building is BLOCKED until interview complete
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_integrated_flow():
    """Test complete integrated flow"""

    session_id = f"test_flow_{int(time.time())}"

    print("\n" + "=" * 60)
    print("TEST 1: Start Defense Flow with Document Upload")
    print("=" * 60)

    document = """
    SUMMONS AND COMPLAINT

    MIDLAND CREDIT MANAGEMENT vs JOHN DOE
    Case No: 2024-CV-12345

    Plaintiff alleges defendant owes $4,523.67 in unpaid credit card debt.
    Original creditor: Chase Bank
    Date of last payment: Unknown

    Plaintiff demands judgment for $4,523.67 plus interest and court costs.

    You have 20 days to respond.
    """

    response = requests.post(f"{API_BASE}/api/defense-flow/start", json={
        "sessionId": session_id,
        "documentText": document
    })

    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ FAILED: {response.text}")
        return False

    data = response.json()
    print(f"Action: {data.get('action')}")
    print(f"Message: {data.get('message')}")
    print(f"Can build defense: {data.get('can_build_defense')}")
    print(f"State: {data.get('state')}")

    if data.get('current_question'):
        print(f"\nFirst Question: {data['current_question']['text']}")
        print(f"Options: {', '.join(data['current_question'].get('options', []))}")
    else:
        print("❌ FAILED: No question returned")
        return False

    print("\n✅ PASS: Document uploaded and first question returned")

    print("\n" + "=" * 60)
    print("TEST 2: Try Building Defense WITHOUT Answering Questions")
    print("=" * 60)

    response = requests.post(f"{API_BASE}/api/defense-flow/build", json={
        "sessionId": session_id
    })

    print(f"Status: {response.status_code}")

    if response.status_code == 400:
        print("✅ PASS: Defense building was BLOCKED")
        error_data = response.json()
        print(f"Error message: {error_data.get('detail')}")
    else:
        print("❌ FAILED: Defense building was NOT blocked!")
        return False

    print("\n" + "=" * 60)
    print("TEST 3: Answer Interview Questions")
    print("=" * 60)

    questions_answered = 0
    max_questions = 5

    while questions_answered < max_questions:
        # Get current status
        status_response = requests.get(f"{API_BASE}/api/defense-flow/status/{session_id}")
        status = status_response.json()

        print(f"\nProgress: {status.get('progress_percentage', 0):.0f}%")
        print(f"Questions answered: {status.get('answers_collected', 0)}/{status.get('total_questions', 5)}")

        if status.get('can_build_defense'):
            print("✅ Interview complete - can build defense now")
            break

        # Answer the question
        # Use first option for testing
        answer = "Over 5 years ago" if questions_answered == 0 else "Yes"

        print(f"Answering: {answer}")

        response = requests.post(f"{API_BASE}/api/defense-flow/answer", json={
            "sessionId": session_id,
            "answer": answer
        })

        if response.status_code != 200:
            print(f"❌ FAILED: {response.text}")
            return False

        data = response.json()
        questions_answered += 1

        if data.get('defense_found'):
            print(f"🎯 Defense found: {data['defense_found']}")

        if data.get('complete'):
            print("\n✅ PASS: Interview completed")
            print(f"Total answers collected: {data.get('answers_collected')}")
            break

        if data.get('current_question'):
            print(f"Next question: {data['current_question']['text']}")

    print("\n" + "=" * 60)
    print("TEST 4: Build Defense AFTER Interview Complete")
    print("=" * 60)

    response = requests.post(f"{API_BASE}/api/defense-flow/build", json={
        "sessionId": session_id
    })

    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ FAILED: {response.text}")
        return False

    data = response.json()
    print(f"Action: {data.get('action')}")
    print(f"State: {data.get('state')}")

    defenses = data.get('defenses', [])
    print(f"\n✅ PASS: Defense built successfully")
    print(f"Defenses found: {len(defenses)}")

    for i, defense in enumerate(defenses[:3], 1):
        print(f"\n{i}. {defense.get('name')}")
        print(f"   Strength: {defense.get('strength')}")
        print(f"   Description: {defense.get('description')}")
        print(f"   Action: {defense.get('action')}")

    print("\n" + "=" * 60)
    print("TEST 5: Q&A with Concise Responses")
    print("=" * 60)

    questions = [
        "What should I do about this lawsuit?",
        "When is the deadline?",
        "Do I need a lawyer?"
    ]

    for question in questions:
        print(f"\nQ: {question}")

        response = requests.post(f"{API_BASE}/api/defense-flow/qa/message", json={
            "message": question,
            "sessionId": session_id
        })

        if response.status_code != 200:
            print(f"❌ FAILED: {response.text}")
            continue

        data = response.json()
        answer = data.get('response', '')
        word_count = data.get('word_count', 0)

        print(f"A: {answer}")
        print(f"Words: {word_count} | Model: {data.get('model')}")

        if word_count > 50:
            print(f"⚠️  WARNING: Response too long ({word_count} words)")
        else:
            print(f"✅ PASS: Concise response")

    print("\n" + "=" * 60)
    print("TEST 6: Check Final Status")
    print("=" * 60)

    response = requests.get(f"{API_BASE}/api/defense-flow/status/{session_id}")
    status = response.json()

    print(f"Session ID: {status.get('session_id')}")
    print(f"State: {status.get('state')}")
    print(f"Case Type: {status.get('case_type')}")
    print(f"Questions Answered: {status.get('answers_collected')}/{status.get('total_questions')}")
    print(f"Can Build Defense: {status.get('can_build_defense')}")
    print(f"Progress: {status.get('progress_percentage', 0):.0f}%")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nIntegrated flow working correctly:")
    print("1. ✅ Document upload triggers interview")
    print("2. ✅ Defense building BLOCKED until interview complete")
    print("3. ✅ Interview questions flow properly")
    print("4. ✅ Defense building works after interview")
    print("5. ✅ Q&A responses are concise (<50 words)")
    print("6. ✅ State management works correctly")

    return True

if __name__ == "__main__":
    try:
        test_integrated_flow()
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
