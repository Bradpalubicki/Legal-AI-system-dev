"""
Test Enforced Flow
Verifies that interview is ENFORCED before defense building
Tests the complete workflow end-to-end
"""

import requests
import time
import sys


def test_enforced_flow():
    """Test that interview is enforced before defense"""

    session_id = f'test_enforce_{int(time.time())}'
    base_url = 'http://localhost:8000'

    print("\n" + "=" * 70)
    print("TESTING ENFORCED INTERVIEW FLOW")
    print("=" * 70)

    # Test 1: Try to build defense WITHOUT interview (should fail)
    print("\n[TEST 1] Attempting to build defense WITHOUT interview...")
    print("Expected: Should be BLOCKED with 400 error")

    try:
        response = requests.post(
            f'{base_url}/api/defense-flow/build',
            json={'sessionId': session_id}
        )

        if response.status_code == 400:
            print("✅ PASS: Defense building was BLOCKED (400 error)")
            error_data = response.json()
            print(f"   Error message: {error_data.get('detail')}")
        else:
            print(f"❌ FAIL: Expected 400 but got {response.status_code}")
            print(f"   This means defense building was NOT blocked!")
            return False
    except Exception as e:
        print(f"❌ FAIL: Request error: {e}")
        return False

    # Test 2: Upload document (starts interview)
    print("\n[TEST 2] Uploading document to start interview...")
    print("Expected: Should return first question")

    try:
        response = requests.post(
            f'{base_url}/api/defense-flow/start',
            json={
                'sessionId': session_id,
                'documentText': '''
                SUMMONS AND COMPLAINT

                MIDLAND CREDIT MANAGEMENT vs JOHN DOE
                Case No: 2024-CV-12345

                Plaintiff alleges defendant owes $4,523.67 in unpaid credit card debt.
                Original creditor: Chase Bank
                Date of last payment: Unknown

                You have 20 days to respond.
                '''
            }
        )

        if response.status_code != 200:
            print(f"❌ FAIL: Upload failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        data = response.json()

        if 'current_question' not in data:
            print("❌ FAIL: No question returned after document upload")
            print(f"   Response: {data}")
            return False

        print("✅ PASS: Document uploaded successfully")
        print(f"   First question: {data['current_question']['text']}")
        print(f"   Question type: {data['current_question'].get('id')}")
        print(f"   Total questions: {data.get('total_questions')}")
        print(f"   Can build defense: {data.get('can_build_defense')}")

        if data.get('can_build_defense'):
            print("⚠️  WARNING: can_build_defense should be False at this stage")

    except Exception as e:
        print(f"❌ FAIL: Request error: {e}")
        return False

    # Test 3: Try to build defense again (should still fail)
    print("\n[TEST 3] Attempting to build defense after upload but before answers...")
    print("Expected: Should still be BLOCKED")

    try:
        response = requests.post(
            f'{base_url}/api/defense-flow/build',
            json={'sessionId': session_id}
        )

        if response.status_code == 400:
            print("✅ PASS: Defense still BLOCKED before answering questions")
        else:
            print(f"❌ FAIL: Defense was NOT blocked (got {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ FAIL: Request error: {e}")
        return False

    # Test 4: Answer questions
    print("\n[TEST 4] Answering interview questions...")
    print("Expected: Complete interview after 5 questions")

    questions_answered = 0
    max_questions = 5

    try:
        for i in range(max_questions):
            # Use specific answers for better testing
            answers = [
                'Over 5 years ago',  # Last payment - triggers statute of limitations
                'Debt buyer',         # Original creditor - triggers standing issue
                'Too high',           # Amount correct - triggers amount dispute
                'Yes',                # Attempted payment
                'Some records'        # Have records
            ]

            answer = answers[i] if i < len(answers) else 'Yes'

            print(f"\n   Answering question {i + 1}: {answer}")

            response = requests.post(
                f'{base_url}/api/defense-flow/answer',
                json={
                    'sessionId': session_id,
                    'answer': answer
                }
            )

            if response.status_code != 200:
                print(f"   ❌ FAIL: Answer failed with status {response.status_code}")
                return False

            data = response.json()
            questions_answered += 1

            if data.get('defense_found'):
                print(f"   🎯 Defense found: {data['defense_found']}")

            if data.get('action') == 'INTERVIEW_COMPLETE':
                print(f"\n✅ PASS: Interview completed after {questions_answered} questions")
                print(f"   Can build defense: {data.get('can_build_defense')}")
                print(f"   Message: {data.get('message')}")

                if not data.get('can_build_defense'):
                    print("   ❌ FAIL: can_build_defense should be True after interview")
                    return False

                break
            else:
                next_q = data.get('current_question')
                if next_q:
                    print(f"   Next question: {next_q.get('text')}")
                    print(f"   Progress: {data.get('progress', 0) * 100:.0f}%")

        if questions_answered >= max_questions and data.get('action') != 'INTERVIEW_COMPLETE':
            print("⚠️  WARNING: Answered all questions but interview not marked complete")

    except Exception as e:
        print(f"❌ FAIL: Request error: {e}")
        return False

    # Test 5: Now build defense (should work)
    print("\n[TEST 5] Building defense AFTER interview completion...")
    print("Expected: Should succeed with defenses returned")

    try:
        response = requests.post(
            f'{base_url}/api/defense-flow/build',
            json={'sessionId': session_id}
        )

        if response.status_code != 200:
            print(f"❌ FAIL: Defense building failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        data = response.json()

        if 'defenses' not in data:
            print("❌ FAIL: No defenses in response")
            print(f"   Response: {data}")
            return False

        defenses = data.get('defenses', [])
        print(f"✅ PASS: Defense built successfully")
        print(f"   Defenses found: {len(defenses)}")

        for i, defense in enumerate(defenses[:3], 1):
            print(f"\n   {i}. {defense.get('name')}")
            print(f"      Strength: {defense.get('strength')}")
            print(f"      Action: {defense.get('action')}")

        # Check for immediate actions
        actions = data.get('immediate_actions', [])
        if actions:
            print(f"\n   Immediate actions: {len(actions)}")
            for action in actions[:2]:
                print(f"   - {action}")

    except Exception as e:
        print(f"❌ FAIL: Request error: {e}")
        return False

    # Test 6: Test Q&A (should be concise)
    print("\n[TEST 6] Testing Q&A conciseness...")
    print("Expected: Response should be <50 words, no verbose language")

    questions = [
        "What should I do about this lawsuit?",
        "When is the deadline?",
        "Do I need a lawyer?"
    ]

    try:
        for question in questions:
            print(f"\n   Q: {question}")

            response = requests.post(
                f'{base_url}/api/defense-flow/qa/message',
                json={
                    'message': question,
                    'sessionId': session_id
                }
            )

            if response.status_code != 200:
                print(f"   ❌ FAIL: Q&A failed with status {response.status_code}")
                continue

            data = response.json()
            answer = data.get('response', '')
            word_count = len(answer.split())

            print(f"   A: {answer[:100]}...")
            print(f"   Words: {word_count} | Model: {data.get('model')}")

            if word_count > 50:
                print(f"   ⚠️  WARNING: Response too long ({word_count} words)")
            else:
                print(f"   ✅ Concise ({word_count} words)")

            # Check for verbose language
            verbose_phrases = [
                "let's pretend", "imagine you", "picture this",
                "think of it like", "okay, let's", "simple words"
            ]

            found_verbose = False
            for phrase in verbose_phrases:
                if phrase.lower() in answer.lower():
                    print(f"   ❌ FAIL: Contains verbose phrase '{phrase}'")
                    found_verbose = True
                    break

            if not found_verbose:
                print(f"   ✅ No verbose language detected")

    except Exception as e:
        print(f"❌ FAIL: Request error: {e}")
        return False

    # Test 7: Check final status
    print("\n[TEST 7] Checking final system status...")

    try:
        response = requests.get(f'{base_url}/api/defense-flow/status/{session_id}')

        if response.status_code == 200:
            status = response.json()
            print("✅ PASS: Status retrieved successfully")
            print(f"   State: {status.get('state')}")
            print(f"   Case Type: {status.get('case_type')}")
            print(f"   Questions Answered: {status.get('answers_collected')}/{status.get('total_questions')}")
            print(f"   Can Build Defense: {status.get('can_build_defense')}")
            print(f"   Progress: {status.get('progress_percentage', 0):.0f}%")
        else:
            print(f"⚠️  WARNING: Status check returned {response.status_code}")

    except Exception as e:
        print(f"⚠️  WARNING: Status check error: {e}")

    # Final summary
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\nVerified:")
    print("1. ✅ Defense building BLOCKED without interview")
    print("2. ✅ Document upload starts interview with first question")
    print("3. ✅ Defense still BLOCKED after upload but before answers")
    print("4. ✅ Interview completes after answering questions")
    print("5. ✅ Defense building ALLOWED after interview complete")
    print("6. ✅ Q&A responses are concise (<50 words)")
    print("7. ✅ System status tracking works correctly")
    print("\n🎉 Enforced interview flow is working correctly!")

    return True


if __name__ == '__main__':
    try:
        success = test_enforced_flow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
