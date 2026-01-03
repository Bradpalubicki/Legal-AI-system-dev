"""
Test script for court integrations and compliance systems
Basic functionality verification
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from integrations.courts.court_manager import CourtIntegrationManager, CourtDataRequest, CourtSystemType
from integrations.courts.federal_courts import FederalCourtDistrict
from integrations.courts.state_courts import StateJurisdiction
from compliance.conflicts import ConflictManager, ConflictEntity
from compliance.legal_hold import LegalHoldManager, HoldType

async def test_court_integrations():
    """Test court integration systems"""
    print("=== Testing Court Integrations ===")

    court_manager = CourtIntegrationManager()

    try:
        # Test 1: Health check
        print("\n1. Running health check...")
        health_status = await court_manager.health_check()
        print(f"Overall status: {health_status['overall_status']}")

        # Test 2: Federal court search
        print("\n2. Testing federal court search...")
        federal_request = CourtDataRequest(
            request_id=f"TEST_FED_{uuid.uuid4().hex[:8]}",
            court_system=CourtSystemType.FEDERAL,
            jurisdiction=FederalCourtDistrict.SOUTHERN_DISTRICT_NY,
            search_criteria={
                'case_name': 'test',
                'party_name': 'Smith'
            }
        )

        federal_response = await court_manager.search_all_courts(federal_request)
        print(f"Federal search success: {federal_response.success}")
        print(f"Results found: {len(federal_response.data)}")
        print(f"Response time: {federal_response.response_time_ms}ms")

        # Test 3: State court search
        print("\n3. Testing state court search...")
        state_request = CourtDataRequest(
            request_id=f"TEST_STATE_{uuid.uuid4().hex[:8]}",
            court_system=CourtSystemType.STATE,
            jurisdiction=StateJurisdiction.CALIFORNIA,
            search_criteria={
                'case_name': 'test',
                'party_name': 'Jones'
            }
        )

        state_response = await court_manager.search_all_courts(state_request)
        print(f"State search success: {state_response.success}")
        print(f"Results found: {len(state_response.data)}")
        print(f"Response time: {state_response.response_time_ms}ms")

        # Test 4: Performance report
        print("\n4. Getting performance report...")
        perf_report = await court_manager.get_performance_report()
        print(f"Total requests: {perf_report['summary']['total_requests']}")
        print(f"Success rate: {perf_report['summary']['success_rate']:.1f}%")
        print(f"Average response time: {perf_report['summary']['average_response_time_ms']:.1f}ms")

        print("✅ Court integrations tests completed")
        return True

    except Exception as e:
        print(f"❌ Court integrations test failed: {str(e)}")
        return False

async def test_conflict_checking():
    """Test conflict of interest system"""
    print("\n=== Testing Conflict Checking ===")

    conflict_manager = ConflictManager()

    try:
        # Test 1: Add entities to registry
        print("\n1. Adding test entities to registry...")
        test_entities = [
            ConflictEntity(
                name="ABC Corporation",
                entity_type="company",
                aliases=["ABC Corp", "ABC Inc"],
                identifiers={"ein": "12-3456789"}
            ),
            ConflictEntity(
                name="John Smith",
                entity_type="person",
                aliases=["J. Smith", "Johnny Smith"],
                identifiers={"ssn": "xxx-xx-1234"}
            ),
            ConflictEntity(
                name="XYZ Holdings",
                entity_type="company",
                relationships=[{
                    "type": "subsidiary",
                    "related_entity": "ABC Corporation"
                }]
            )
        ]

        for entity in test_entities:
            await conflict_manager.add_entity_to_registry(entity)

        print(f"Added {len(test_entities)} entities to registry")

        # Test 2: Run comprehensive conflict check
        print("\n2. Running comprehensive conflict check...")
        case_data = {
            'case_id': 'TEST_CASE_001',
            'case_type': 'litigation',
            'estimated_value': 500000,
            'description': 'Contract dispute between parties'
        }

        parties = [
            {
                'name': 'ABC Corporation',
                'type': 'company',
                'aliases': ['ABC Corp']
            },
            {
                'name': 'Jane Doe',
                'type': 'person'
            }
        ]

        attorney_id = "ATT_001"

        conflict_results = await conflict_manager.run_comprehensive_conflict_check(
            case_data, parties, attorney_id
        )

        print(f"Conflict check completed for case: {conflict_results['case_id']}")
        print(f"Overall risk level: {conflict_results['overall_risk_level']}")
        print(f"Party conflicts found: {len(conflict_results['party_conflicts'])}")
        print(f"Attorney conflicts found: {len(conflict_results['attorney_conflicts'])}")
        print(f"Requires clearance: {conflict_results['requires_clearance']}")
        print(f"Automatic flags: {len(conflict_results['automatic_flags'])}")

        # Test 3: Create Chinese wall
        print("\n3. Testing Chinese wall creation...")
        chinese_wall = await conflict_manager.wall_manager.create_chinese_wall(
            name="Test Confidentiality Wall",
            description="Testing wall for ABC Corporation matter",
            restricted_parties={"ABC Corporation", "XYZ Holdings"},
            authorized_attorneys={"ATT_002", "ATT_003"}
        )

        print(f"Created Chinese wall: {chinese_wall.wall_id}")
        print(f"Restricted parties: {len(chinese_wall.restricted_parties)}")
        print(f"Authorized attorneys: {len(chinese_wall.authorized_attorneys)}")

        print("✅ Conflict checking tests completed")
        return True

    except Exception as e:
        print(f"❌ Conflict checking test failed: {str(e)}")
        return False

async def test_legal_hold():
    """Test legal hold system"""
    print("\n=== Testing Legal Hold System ===")

    hold_manager = LegalHoldManager()

    try:
        # Test 1: Create legal hold
        print("\n1. Creating test legal hold...")
        hold_data = {
            'name': 'Test Litigation Hold',
            'description': 'Test hold for litigation matter',
            'hold_type': HoldType.LITIGATION.value,
            'case_id': 'CASE_001',
            'matter_name': 'Test v. Example',
            'requesting_attorney': 'Attorney Smith',
            'created_by': 'system_test',
            'custodians': [
                {
                    'custodian_id': 'CUST_001',
                    'name': 'John Doe',
                    'email': 'john.doe@example.com',
                    'department': 'Finance',
                    'role': 'Manager'
                }
            ],
            'data_sources': [
                {
                    'source_id': 'SRC_001',
                    'source_type': 'EMAIL',
                    'location': '/test/email/data',
                    'description': 'Email communications',
                    'custodian_id': 'CUST_001'
                }
            ]
        }

        hold_id = await hold_manager.create_legal_hold(hold_data)
        print(f"Created legal hold: {hold_id}")

        # Test 2: Get hold status
        print("\n2. Getting hold status...")
        hold_status = await hold_manager.get_hold_status(hold_id)
        print(f"Hold name: {hold_status['name']}")
        print(f"Status: {hold_status['status']}")
        print(f"Custodians: {hold_status['custodian_count']}")
        print(f"Data sources: {hold_status['data_source_count']}")

        # Test 3: Activate hold (will fail without real data, but tests the flow)
        print("\n3. Testing hold activation...")
        try:
            activation_success = await hold_manager.activate_hold(hold_id, 'system_test')
            print(f"Hold activation: {'✅ Success' if activation_success else '⚠️  Failed (expected for test data)'}")
        except Exception as e:
            print(f"⚠️  Hold activation failed (expected): {str(e)}")

        # Test 4: Check automatic triggers
        print("\n4. Testing automatic triggers...")
        test_event = {
            'case_type': 'litigation',
            'estimated_value': 200000,
            'document_text': 'regulatory inquiry from sec regarding...',
            'attorney_id': 'ATT_001'
        }

        triggered_holds = await hold_manager.check_automatic_triggers(test_event)
        print(f"Automatic triggers fired: {len(triggered_holds)}")

        # Test 5: Generate compliance report
        print("\n5. Generating compliance report...")
        compliance_report = await hold_manager.generate_compliance_report(hold_id)
        if compliance_report:
            print(f"Report generated for hold: {compliance_report['hold_id']}")
            print(f"Days active: {compliance_report['hold_summary']['days_active']}")
            print(f"Total records: {compliance_report['preservation_summary']['total_records']}")
            print(f"Custodian compliance entries: {len(compliance_report['custodian_compliance'])}")

        print("✅ Legal hold tests completed")
        return True

    except Exception as e:
        print(f"❌ Legal hold test failed: {str(e)}")
        return False

async def main():
    """Run all integration tests"""
    print("🚀 Starting Legal AI System Integration Tests")
    print(f"Test started at: {datetime.now().isoformat()}")

    test_results = []

    # Run all tests
    test_results.append(await test_court_integrations())
    test_results.append(await test_conflict_checking())
    test_results.append(await test_legal_hold())

    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)

    passed = sum(test_results)
    total = len(test_results)

    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check logs above")

    print(f"Test completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())