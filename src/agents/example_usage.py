"""
Example usage of the Legal Interview Agent
"""

import asyncio
from legal_interview_agent import LegalInterviewAgent, legal_agent_instances

async def example_interview_flow():
    """Demonstrate how the intelligent agent works"""

    # 1. Create agent for a session
    session_id = "demo_session_123"
    agent = LegalInterviewAgent(session_id)
    legal_agent_instances[session_id] = agent

    # 2. Analyze document
    sample_document = """
    IN THE CIRCUIT COURT OF COOK COUNTY, ILLINOIS

    MIDLAND CREDIT MANAGEMENT, INC., a debt buyer
    Plaintiff,

    vs.

    JOHN DOE,
    Defendant.

    Case No: 2024-CC-12345

    COMPLAINT

    Plaintiff alleges:
    1. Defendant owes $8,542.00 on a credit card account
    2. Original creditor was Chase Bank
    3. Debt was assigned to Plaintiff on January 15, 2023
    4. Defendant has failed to pay

    WHEREFORE, Plaintiff seeks judgment for $8,542.00 plus costs.
    """

    print("=" * 60)
    print("ANALYZING DOCUMENT...")
    print("=" * 60)

    analysis = await agent.analyze_document_deeply(sample_document)
    print(f"\nDocument Type: {analysis.get('case_type')}")
    print(f"Plaintiff: {analysis.get('plaintiff_name')}")
    print(f"\nCritical Gaps Identified:")
    for gap in agent.brain.memory.get('critical_gaps', []):
        print(f"  - {gap['gap']}: {gap['reason']}")

    print(f"\nOpportunities Detected:")
    for opp in agent.brain.opportunities:
        print(f"  - {opp}")

    # 3. Conduct intelligent interview
    print("\n" + "=" * 60)
    print("INTELLIGENT INTERVIEW")
    print("=" * 60)

    # Simulate interview responses
    interview_responses = [
        ("last_payment", "Over 6 years ago"),
        ("debt_recognition", "Yes, but not with this company"),
        ("payment_history", "Yes, I have bank statements")
    ]

    for question_id, answer in interview_responses:
        # Get next question
        question = agent.get_next_intelligent_question()
        if not question:
            break

        print(f"\nQuestion {question.get('question_number')}: {question.get('question')}")
        if question.get('options'):
            print("Options:")
            for i, opt in enumerate(question['options'], 1):
                print(f"  {i}. {opt}")

        # Process answer
        result = agent.process_answer_intelligently(question['id'], answer)
        print(f"\nYour Answer: {answer}")

        if result.get('insights'):
            print("Insights:")
            for insight in result['insights']:
                print(f"  ✓ {insight}")

        if result.get('defense_implications'):
            print(f"Defense Impact: {result['defense_implications']}")

    # 4. Build comprehensive strategy
    print("\n" + "=" * 60)
    print("COMPREHENSIVE DEFENSE STRATEGY")
    print("=" * 60)

    strategy = agent.build_comprehensive_defense_strategy()

    print("\nPRIMARY DEFENSES:")
    for defense in strategy.get('primary_defenses', []):
        print(f"\n{defense['name']} (Strength: {defense['strength']}%)")
        print(f"  {defense['description']}")
        print(f"  How to Assert: {defense['how_to_assert']}")

    print("\n\nIMMEDIATE ACTIONS:")
    for action in strategy.get('immediate_actions', []):
        print(f"\n{action['priority']}: {action['action']}")
        print(f"  Deadline: {action['deadline']}")
        print(f"  {action['details']}")

    print(f"\n\nOVERALL SUCCESS RATE: {strategy.get('estimated_success_rate')}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(example_interview_flow())
