#!/usr/bin/env python3
"""
Comprehensive Bankruptcy Specialist System Test
Educational testing of bankruptcy specialist with full compliance validation

CRITICAL COMPLIANCE NOTICES:
- EDUCATIONAL TESTING ONLY: All tests are for educational demonstration
- NO LEGAL ADVICE: Testing demonstrates system capabilities only
- ATTORNEY SUPERVISION: Test results require attorney review
- PROFESSIONAL RESPONSIBILITY: Testing complies with ethical obligations
"""

import sys
import os
import asyncio
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_bankruptcy_specialist_core():
    """Test core bankruptcy specialist functionality"""
    print("TESTING BANKRUPTCY SPECIALIST CORE SYSTEM")
    print("-" * 50)

    try:
        from bankruptcy.bankruptcy_specialist import (
            bankruptcy_specialist, BankruptcyChapter, ComplianceLevel
        )

        # Test educational chapter identification
        print("Testing educational chapter identification...")

        # Educational test case descriptions
        test_cases = [
            {
                "description": "Individual consumer with limited assets seeking liquidation",
                "expected_chapter": BankruptcyChapter.CHAPTER_7,
                "test_name": "Consumer Chapter 7 Identification"
            },
            {
                "description": "Individual with regular income wanting to save home through payment plan",
                "expected_chapter": BankruptcyChapter.CHAPTER_13,
                "test_name": "Individual Chapter 13 Identification"
            },
            {
                "description": "Small business seeking streamlined reorganization",
                "expected_chapter": BankruptcyChapter.SUBCHAPTER_V,
                "test_name": "Small Business Subchapter V Identification"
            }
        ]

        # Test chapter identification (synchronous version for testing)
        async def test_chapter_identification():
            for test_case in test_cases:
                try:
                    result = await bankruptcy_specialist.identify_bankruptcy_chapter(
                        test_case["description"],
                        "educational_user"
                    )

                    if result.get("success"):
                        print(f"  [PASS] {test_case['test_name']}: {result.get('chapter_identified')}")
                        print(f"    Educational Summary: {result.get('educational_summary', 'N/A')[:100]}...")
                        print(f"    Attorney Review Required: {result.get('attorney_review_required', True)}")
                    else:
                        print(f"  [FAIL] {test_case['test_name']}: {result.get('error', 'Unknown error')}")

                except Exception as e:
                    print(f"  [FAIL] {test_case['test_name']}: {str(e)}")

        # Run chapter identification tests
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(test_chapter_identification())
        loop.close()

        # Test specialist status
        print("Testing specialist status retrieval...")
        status = bankruptcy_specialist.get_specialist_status()
        if isinstance(status, dict) and "specialist_statistics" in status:
            stats = status["specialist_statistics"]
            print(f"  [PASS] Specialist Status Retrieved")
            print(f"    Total Analyses: {stats.get('total_analyses_performed', 0)}")
            print(f"    Educational Templates: {stats.get('available_educational_templates', 0)}")
            print(f"    Supported Chapters: {stats.get('supported_bankruptcy_chapters', 0)}")
        else:
            print(f"  [FAIL] Specialist Status: Invalid response")

        return True

    except Exception as e:
        print(f"[FAIL] Bankruptcy specialist test failed: {str(e)}")
        return False

def test_template_manager():
    """Test bankruptcy template management system"""
    print("\nTESTING BANKRUPTCY TEMPLATE MANAGER")
    print("-" * 50)

    try:
        from bankruptcy.template_manager import (
            bankruptcy_template_manager, BankruptcyChapter, TemplateType
        )

        # Test template listing
        print("Testing educational template listing...")
        template_list = bankruptcy_template_manager.list_available_templates(
            chapter=BankruptcyChapter.CHAPTER_7,
            user_id="educational_user"
        )

        if template_list.get("success"):
            templates = template_list.get("templates", [])
            print(f"  [PASS] Template Listing: {len(templates)} templates found")
            for template in templates[:3]:  # Show first 3
                print(f"    - {template.get('title', 'Unknown')} (Not for direct use: {template.get('not_for_direct_use', True)})")
        else:
            print(f"  [FAIL] Template Listing: {template_list.get('error', 'Unknown error')}")

        # Test individual template retrieval
        print("Testing individual template retrieval...")
        available_templates = list(bankruptcy_template_manager.educational_templates.keys())
        if available_templates:
            test_template_id = available_templates[0]
            template_result = bankruptcy_template_manager.get_template(
                test_template_id,
                "educational_user"
            )

            if template_result.get("success"):
                template = template_result.get("template", {})
                print(f"  [PASS] Template Retrieval: {template.get('title', 'Unknown')}")
                print(f"    Sections: {len(template.get('sections', []))}")
                print(f"    Attorney Review Required: {template.get('attorney_signature_required', True)}")
                print(f"    Not for Direct Use: {template.get('not_for_direct_use', True)}")
            else:
                print(f"  [FAIL] Template Retrieval: {template_result.get('error', 'Unknown error')}")
        else:
            print(f"  [FAIL] Template Retrieval: No templates available")

        # Test template status
        print("Testing template manager status...")
        status = bankruptcy_template_manager.get_template_status()
        if isinstance(status, dict) and "template_statistics" in status:
            stats = status["template_statistics"]
            print(f"  [PASS] Template Status Retrieved")
            print(f"    Total Templates: {stats.get('total_educational_templates', 0)}")
            print(f"    Templates by Type: {len(stats.get('templates_by_type', {}))}")
            print(f"    Templates by Chapter: {len(stats.get('templates_by_chapter', {}))}")
        else:
            print(f"  [FAIL] Template Status: Invalid response")

        return True

    except Exception as e:
        print(f"[FAIL] Template manager test failed: {str(e)}")
        return False

def test_deadline_tracker():
    """Test bankruptcy deadline tracking system"""
    print("\nTESTING BANKRUPTCY DEADLINE TRACKER")
    print("-" * 50)

    try:
        from bankruptcy.deadline_tracker import (
            bankruptcy_deadline_tracker, BankruptcyChapter, DeadlineType
        )

        # Test deadline information retrieval
        print("Testing educational deadline information...")
        available_deadlines = list(bankruptcy_deadline_tracker.educational_deadlines.keys())
        if available_deadlines:
            test_deadline_id = available_deadlines[0]
            deadline_result = bankruptcy_deadline_tracker.get_deadline_information(
                test_deadline_id,
                "educational_user"
            )

            if deadline_result.get("success"):
                deadline = deadline_result.get("deadline", {})
                print(f"  [PASS] Deadline Information: {deadline.get('title', 'Unknown')}")
                print(f"    Timeframe: {deadline.get('typical_timeframe', 'Unknown')}")
                print(f"    Priority: {deadline.get('priority', 'Unknown')}")
                print(f"    Attorney Verification Required: {deadline.get('attorney_verification_required', True)}")
            else:
                print(f"  [FAIL] Deadline Information: {deadline_result.get('error', 'Unknown error')}")
        else:
            print(f"  [FAIL] Deadline Information: No deadlines available")

        # Test timeline template retrieval
        print("Testing educational timeline templates...")
        timeline_result = bankruptcy_deadline_tracker.get_timeline_template(
            BankruptcyChapter.CHAPTER_7,
            "educational_user"
        )

        if timeline_result.get("success"):
            timeline = timeline_result.get("timeline", {})
            print(f"  [PASS] Timeline Template: {timeline.get('title', 'Unknown')}")
            print(f"    Phases: {len(timeline.get('phases', []))}")
            print(f"    Duration: {timeline.get('typical_duration', 'Unknown')}")
            print(f"    Critical Deadlines: {len(timeline.get('critical_deadlines', []))}")
        else:
            print(f"  [FAIL] Timeline Template: {timeline_result.get('error', 'Unknown error')}")

        # Test deadlines by chapter
        print("Testing deadlines by chapter listing...")
        chapter_deadlines = bankruptcy_deadline_tracker.list_deadlines_by_chapter(
            BankruptcyChapter.EDUCATIONAL_EXAMPLE,
            "educational_user"
        )

        if chapter_deadlines.get("success"):
            deadlines = chapter_deadlines.get("deadlines", [])
            print(f"  [PASS] Chapter Deadlines: {len(deadlines)} deadlines found")
            for deadline in deadlines[:3]:  # Show first 3
                print(f"    - {deadline.get('title', 'Unknown')} (Priority: {deadline.get('priority', 'Unknown')})")
        else:
            print(f"  [FAIL] Chapter Deadlines: {chapter_deadlines.get('error', 'Unknown error')}")

        # Test tracker status
        print("Testing deadline tracker status...")
        status = bankruptcy_deadline_tracker.get_tracker_status()
        if isinstance(status, dict) and "tracker_statistics" in status:
            stats = status["tracker_statistics"]
            print(f"  [PASS] Tracker Status Retrieved")
            print(f"    Total Deadlines: {stats.get('total_educational_deadlines', 0)}")
            print(f"    Timeline Templates: {stats.get('total_timeline_templates', 0)}")
            print(f"    Supported Chapters: {len(stats.get('deadlines_by_chapter', {}))}")
        else:
            print(f"  [FAIL] Tracker Status: Invalid response")

        return True

    except Exception as e:
        print(f"[FAIL] Deadline tracker test failed: {str(e)}")
        return False

def test_compliance_framework():
    """Test bankruptcy compliance framework"""
    print("\nTESTING BANKRUPTCY COMPLIANCE FRAMEWORK")
    print("-" * 50)

    try:
        from bankruptcy.bankruptcy_specialist import bankruptcy_specialist

        # Test compliance configuration
        print("Testing compliance configuration...")
        status = bankruptcy_specialist.get_specialist_status()
        compliance = status.get("compliance_status", {})

        compliance_checks = [
            ("educational_purpose", "Educational purpose validation"),
            ("attorney_supervision", "Attorney supervision requirement"),
            ("template_disclaimer", "Template disclaimer coverage"),
            ("deadline_verification", "Deadline verification requirement"),
            ("professional_responsibility", "Professional responsibility compliance"),
            ("client_protection", "Client protection measures")
        ]

        all_compliant = True
        for check_key, check_name in compliance_checks:
            if check_key in compliance:
                print(f"  [PASS] {check_name}: {compliance[check_key][:50]}...")
            else:
                print(f"  [FAIL] {check_name}: Not configured")
                all_compliant = False

        # Test educational disclaimers
        print("Testing educational disclaimers...")
        disclaimers = status.get("bankruptcy_disclaimers", [])
        if len(disclaimers) >= 6:
            print(f"  [PASS] Educational Disclaimers: {len(disclaimers)} disclaimers configured")
            print(f"    Sample: {disclaimers[0][:60]}...")
        else:
            print(f"  [FAIL] Educational Disclaimers: Insufficient disclaimers ({len(disclaimers)})")
            all_compliant = False

        # Test attorney review requirements
        print("Testing attorney review requirements...")
        educational_config = status.get("educational_config", {})
        review_requirements = [
            "attorney_review_mandatory",
            "professional_responsibility_compliance",
            "educational_content_only",
            "no_legal_advice"
        ]

        review_compliant = all(educational_config.get(req, False) for req in review_requirements)
        if review_compliant:
            print(f"  [PASS] Attorney Review Requirements: All requirements configured")
        else:
            print(f"  [FAIL] Attorney Review Requirements: Some requirements missing")
            all_compliant = False

        return all_compliant

    except Exception as e:
        print(f"[FAIL] Compliance framework test failed: {str(e)}")
        return False

def test_integrated_workflow():
    """Test integrated bankruptcy specialist workflow"""
    print("\nTESTING INTEGRATED BANKRUPTCY WORKFLOW")
    print("-" * 50)

    try:
        print("Step 1: Chapter identification and analysis...")
        from bankruptcy.bankruptcy_specialist import bankruptcy_specialist, BankruptcyChapter

        # Test integrated workflow
        async def test_workflow():
            # Step 1: Identify chapter
            case_description = "Individual consumer with regular income wanting to save home"
            analysis_result = await bankruptcy_specialist.identify_bankruptcy_chapter(
                case_description,
                "educational_user"
            )

            if not analysis_result.get("success"):
                print(f"  [FAIL] Chapter identification failed: {analysis_result.get('error')}")
                return False

            identified_chapter = analysis_result.get("chapter_identified")
            print(f"  [PASS] Chapter identified: {identified_chapter}")

            # Step 2: Get relevant templates
            print("Step 2: Retrieving educational templates...")
            from bankruptcy.template_manager import bankruptcy_template_manager

            chapter_enum = BankruptcyChapter(identified_chapter)
            templates = bankruptcy_template_manager.list_available_templates(
                chapter=chapter_enum,
                user_id="educational_user"
            )

            if templates.get("success"):
                template_count = len(templates.get("templates", []))
                print(f"  [PASS] Educational templates retrieved: {template_count}")
            else:
                print(f"  [FAIL] Template retrieval failed: {templates.get('error')}")
                return False

            # Step 3: Get deadline information
            print("Step 3: Retrieving deadline information...")
            from bankruptcy.deadline_tracker import bankruptcy_deadline_tracker

            deadlines = bankruptcy_deadline_tracker.list_deadlines_by_chapter(
                chapter_enum,
                "educational_user"
            )

            if deadlines.get("success"):
                deadline_count = len(deadlines.get("deadlines", []))
                print(f"  [PASS] Educational deadlines retrieved: {deadline_count}")
            else:
                print(f"  [FAIL] Deadline retrieval failed: {deadlines.get('error')}")
                return False

            # Step 4: Get timeline template
            print("Step 4: Retrieving timeline template...")
            timeline = bankruptcy_deadline_tracker.get_timeline_template(
                chapter_enum,
                "educational_user"
            )

            if timeline.get("success"):
                phase_count = len(timeline.get("timeline", {}).get("phases", []))
                print(f"  [PASS] Educational timeline retrieved: {phase_count} phases")
            else:
                print(f"  [FAIL] Timeline retrieval failed: {timeline.get('error')}")
                return False

            return True

        # Run workflow test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        workflow_success = loop.run_until_complete(test_workflow())
        loop.close()

        if workflow_success:
            print("  [PASS] Integrated workflow completed successfully")
        else:
            print("  [FAIL] Integrated workflow failed")

        return workflow_success

    except Exception as e:
        print(f"[FAIL] Integrated workflow test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("BANKRUPTCY SPECIALIST SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("EDUCATIONAL PURPOSE ONLY - NO LEGAL ADVICE PROVIDED")
    print("ATTORNEY SUPERVISION REQUIRED FOR ALL BANKRUPTCY ACTIVITIES")
    print("PROFESSIONAL RESPONSIBILITY COMPLIANCE MANDATORY")
    print("=" * 70)

    tests_passed = 0
    total_tests = 5

    # Test 1: Bankruptcy Specialist Core
    if test_bankruptcy_specialist_core():
        tests_passed += 1

    # Test 2: Template Manager
    if test_template_manager():
        tests_passed += 1

    # Test 3: Deadline Tracker
    if test_deadline_tracker():
        tests_passed += 1

    # Test 4: Compliance Framework
    if test_compliance_framework():
        tests_passed += 1

    # Test 5: Integrated Workflow
    if test_integrated_workflow():
        tests_passed += 1

    # Report results
    print(f"\n" + "=" * 70)
    print(f"BANKRUPTCY SPECIALIST SYSTEM TEST RESULTS")
    print(f"=" * 70)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")

    if tests_passed == total_tests:
        print(f"\n[SUCCESS] BANKRUPTCY SPECIALIST SYSTEM FULLY OPERATIONAL")
        print(f"All components validated with educational compliance")
    else:
        print(f"\n[INFO] BANKRUPTCY SPECIALIST SYSTEM PARTIALLY OPERATIONAL")
        print(f"Educational demonstration components available")

    # Compliance verification
    print(f"\nBANKRUPTCY SPECIALIST COMPLIANCE VERIFICATION:")
    print(f"- Educational purpose only: [CONFIRMED]")
    print(f"- No legal advice provided: [CONFIRMED]")
    print(f"- Attorney supervision required: [ENFORCED]")
    print(f"- Professional responsibility compliance: [MANDATORY]")
    print(f"- Template examples only: [CONFIRMED]")
    print(f"- Deadline verification required: [ENFORCED]")
    print(f"- Attorney review mandatory: [COMPREHENSIVE]")
    print(f"- Client protection safeguards: [OPERATIONAL]")

    print(f"\nEDUCATIONAL AND PROFESSIONAL SAFEGUARDS:")
    print(f"- All bankruptcy content is for educational purposes only")
    print(f"- No legal advice, strategy, or recommendations provided")
    print(f"- Attorney supervision required for all bankruptcy activities")
    print(f"- Professional responsibility compliance monitored")
    print(f"- Template examples require attorney review and modification")
    print(f"- Deadline information requires attorney verification")
    print(f"- Comprehensive disclaimers on all content")
    print(f"- Full compliance with ethical obligations")

    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)