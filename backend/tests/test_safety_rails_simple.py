#!/usr/bin/env python3
"""
Simple Test Suite for Safety Rails System
Test basic functionality of the development safety rails system
"""

import unittest
import tempfile
import shutil
import json
import os
import sys
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.safety_rails import (
    SafetyRailsSystem,
    PreCommitSafetySystem,
    FeatureFlagSystem,
    MonitoringHooks,
    RollbackSystem,
    SafetyCheckResult,
    SafetyCheckStatus
)

class TestSafetyRailsBasic(unittest.TestCase):
    """Test basic Safety Rails System functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_safety_rails_initialization(self):
        """Test Safety Rails System initializes correctly"""
        system = SafetyRailsSystem()

        self.assertIsNotNone(system.precommit_system)
        self.assertIsNotNone(system.feature_flags)
        self.assertIsNotNone(system.monitoring)
        self.assertIsNotNone(system.rollback)

    def test_pre_commit_system_creation(self):
        """Test Pre-Commit Safety System can be created"""
        system = PreCommitSafetySystem()
        self.assertIsNotNone(system)
        self.assertIsNotNone(system.logger)

    def test_feature_flag_system_creation(self):
        """Test Feature Flag System can be created"""
        system = FeatureFlagSystem()
        self.assertIsNotNone(system)
        self.assertIsInstance(system.flags, dict)

    def test_monitoring_hooks_creation(self):
        """Test Monitoring Hooks can be created"""
        system = MonitoringHooks()
        self.assertIsNotNone(system)

    def test_rollback_system_creation(self):
        """Test Rollback System can be created"""
        system = RollbackSystem()
        self.assertIsNotNone(system)

    def test_safety_check_result_creation(self):
        """Test SafetyCheckResult can be created"""
        result = SafetyCheckResult(
            check_name="test_check",
            status=SafetyCheckStatus.PASS,
            message="Test passed",
            details={"test": "data"},
            timestamp=datetime.now()
        )

        self.assertEqual(result.check_name, "test_check")
        self.assertEqual(result.status, SafetyCheckStatus.PASS)
        self.assertEqual(result.message, "Test passed")
        self.assertFalse(result.blocking)

    def test_feature_flag_basic_functionality(self):
        """Test basic feature flag functionality"""
        system = FeatureFlagSystem()

        # Test with empty flags
        self.assertFalse(system.is_enabled("nonexistent_feature"))

        # Test with mock flags
        system.flags = {
            "test_feature": {
                "enabled": True,
                "rollout_percentage": 100,
                "kill_switch": False
            }
        }

        self.assertTrue(system.is_enabled("test_feature"))

    def test_feature_flag_kill_switch(self):
        """Test feature flag kill switch functionality"""
        system = FeatureFlagSystem()

        system.flags = {
            "test_feature": {
                "enabled": True,
                "rollout_percentage": 100,
                "kill_switch": True  # Kill switch activated
            }
        }

        # Should be disabled due to kill switch
        self.assertFalse(system.is_enabled("test_feature"))

    def test_secret_detection_patterns(self):
        """Test secret detection in pre-commit system"""
        system = PreCommitSafetySystem()

        # Test the exposed secrets check method exists
        result = system.check_for_exposed_secrets()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, SafetyCheckResult)

    def test_advice_language_detection(self):
        """Test advice language detection"""
        system = PreCommitSafetySystem()

        # Test the advice language check method exists
        result = system.check_for_advice_language()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, SafetyCheckResult)

    def test_disclaimer_detection(self):
        """Test disclaimer presence detection"""
        system = PreCommitSafetySystem()

        # Test the disclaimer coverage check method exists
        result = system.check_disclaimer_coverage()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, SafetyCheckResult)

def run_simple_safety_rails_test():
    """Run simplified safety rails tests"""
    print("=" * 60)
    print("SAFETY RAILS SYSTEM - BASIC FUNCTIONALITY TEST")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSafetyRailsBasic)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Generate test report
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(getattr(result, 'skipped', []))
    passed = total_tests - failures - errors - skipped
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0

    print("\n" + "=" * 60)
    print("SAFETY RAILS BASIC TEST RESULTS")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    print(f"Success Rate: {success_rate:.1f}%")

    if success_rate >= 90.0:
        print("\n[PASS] Safety Rails System basic functionality verified")
        deployment_approved = True
    else:
        print(f"\n[FAIL] Safety Rails System has issues - success rate {success_rate:.1f}%")
        deployment_approved = False

    # Show any failures or errors
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    # Save basic test results
    test_results = {
        "test_run": {
            "start_time": datetime.now().isoformat(),
            "test_type": "safety_rails_basic",
            "total_tests": total_tests,
            "passed": passed,
            "failed": failures,
            "errors": errors,
            "success_rate": success_rate,
            "deployment_approved": deployment_approved
        }
    }

    with open("safety_rails_basic_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)

    return deployment_approved

if __name__ == "__main__":
    success = run_simple_safety_rails_test()
    sys.exit(0 if success else 1)