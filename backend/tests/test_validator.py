#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app'))

# Test the validator directly
try:
    from src.monitoring.ai_safety import OutputValidator, SafetyViolation, ViolationType, SeverityLevel
    import uuid

    print("Testing SafetyViolation creation...")
    violation = SafetyViolation(
        id=str(uuid.uuid4()),
        violation_type=ViolationType.LEGAL_ADVICE,
        severity=SeverityLevel.HIGH,
        description="Test violation",
        location="Position 0-10",
        confidence_score=0.8,
        suggested_action="Test action",
        original_text="This is test text for analysis",
        flagged_portion="test text"
    )
    print(f"[OK] SafetyViolation created: {violation.description}")

    print("\nTesting OutputValidator...")
    validator = OutputValidator()

    test_cases = [
        "Here is legal analysis of your contract.",
        "Based on the case law, this appears to be a strong claim.",
        "The statute of limitations may apply to your situation.",
        "Consider consulting with an attorney about this matter."
    ]

    total_violations = 0
    for i, test_case in enumerate(test_cases, 1):
        violations = validator.validate_output(test_case)
        total_violations += len(violations)
        print(f"Test {i}: '{test_case}' -> {len(violations)} violations")
        for violation in violations:
            print(f"  - {violation.violation_type}: {violation.description}")

    coverage = total_violations / len(test_cases)
    print(f"\nDisclaimer Coverage: {coverage*100:.1f}% ({total_violations}/{len(test_cases)})")

except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()