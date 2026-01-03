#!/usr/bin/env python3
"""
Comprehensive Test Suite for Safety Rails System
Test all components of the development safety rails system
"""

import unittest
import tempfile
import shutil
import json
import os
import sys
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime, timedelta

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

class TestSafetyRailsSystem(unittest.TestCase):
    """Test the main Safety Rails System orchestrator"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_safety_rails_initialization(self):
        """Test Safety Rails System initializes correctly"""
        system = SafetyRailsSystem()

        self.assertIsNotNone(system.pre_commit_system)
        self.assertIsNotNone(system.feature_flag_system)
        self.assertIsNotNone(system.monitoring_hooks)
        self.assertIsNotNone(system.rollback_system)

    @patch('src.core.safety_rails.subprocess.run')
    def test_run_comprehensive_safety_check(self, mock_subprocess):
        """Test comprehensive safety check execution"""
        # Mock successful test run
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "All tests passed"

        system = SafetyRailsSystem()

        with patch('builtins.open', mock_open(read_data='{"statistics": {"success_rate": 100.0}}')):
            result = system.run_comprehensive_safety_check()

        self.assertEqual(result.status, SafetyCheckStatus.PASS)
        self.assertIn("safety", result.message.lower())

class TestPreCommitSafetySystem(unittest.TestCase):
    """Test Pre-Commit Safety System"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.system = PreCommitSafetySystem()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.core.safety_rails.subprocess.run')
    def test_run_compliance_tests_success(self, mock_subprocess):
        """Test compliance tests pass"""
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "All tests passed"

        with patch('builtins.open', mock_open(read_data='{"statistics": {"success_rate": 100.0}}')):
            result = self.system.run_compliance_tests()

        self.assertTrue(result.passed)
        self.assertEqual(result.compliance_score, 100.0)

    def test_check_for_secrets_clean_code(self):
        """Test secret detection with clean code"""
        clean_code = """
        # Safe configuration
        database_host = os.getenv('DATABASE_HOST', 'localhost')
        api_endpoint = 'https://api.example.com'
        """

        result = self.system.check_for_secrets(clean_code)
        self.assertTrue(result.passed)
        self.assertEqual(len(result.details), 0)

    def test_check_for_secrets_detects_exposed_secrets(self):
        """Test secret detection identifies exposed secrets"""
        unsafe_code = """
        # Exposed secrets - should be detected
        api_key = "sk-1234567890abcdef"
        password = "supersecret123"
        database_url = "postgresql://user:password@localhost/db"
        """

        result = self.system.check_for_secrets(unsafe_code)
        self.assertFalse(result.passed)
        self.assertGreater(len(result.details), 0)

    def test_verify_no_advice_language_clean(self):
        """Test advice language detection with clean text"""
        clean_text = """
        This analysis suggests that parties typically consider these factors.
        Legal professionals often review contract terms for compliance.
        """

        result = self.system.verify_no_advice_language(clean_text)
        self.assertTrue(result.passed)

    def test_verify_no_advice_language_detects_advice(self):
        """Test advice language detection identifies problematic language"""
        advice_text = """
        You should sign this contract immediately.
        I recommend taking legal action against the defendant.
        You must file this motion within 30 days.
        """

        result = self.system.verify_no_advice_language(advice_text)
        self.assertFalse(result.passed)
        self.assertGreater(len(result.details), 0)

    def test_ensure_disclaimers_present_with_disclaimer(self):
        """Test disclaimer detection with proper disclaimers"""
        text_with_disclaimer = """
        This information is for general educational purposes only and does not constitute legal advice.
        The analysis provided should not be considered as professional legal counsel.
        """

        result = self.system.ensure_disclaimers_present(text_with_disclaimer)
        self.assertTrue(result.passed)

    def test_ensure_disclaimers_present_without_disclaimer(self):
        """Test disclaimer detection without disclaimers"""
        text_without_disclaimer = """
        Here is the contract analysis you requested.
        The terms seem favorable for your situation.
        """

        result = self.system.ensure_disclaimers_present(text_without_disclaimer)
        self.assertFalse(result.passed)

class TestFeatureFlagSystem(unittest.TestCase):
    """Test Feature Flag Management System"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.system = FeatureFlagSystem()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_feature_flags_success(self):
        """Test loading feature flags from configuration"""
        mock_flags = {
            "test_feature": {
                "enabled": True,
                "rollout_percentage": 50,
                "kill_switch": False
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(mock_flags))):
            flags = self.system.load_feature_flags()

        self.assertEqual(flags["test_feature"]["enabled"], True)
        self.assertEqual(flags["test_feature"]["rollout_percentage"], 50)

    def test_is_feature_enabled_basic(self):
        """Test basic feature flag evaluation"""
        self.system.flags = {
            "enabled_feature": {"enabled": True, "rollout_percentage": 100, "kill_switch": False},
            "disabled_feature": {"enabled": False, "rollout_percentage": 100, "kill_switch": False},
            "killed_feature": {"enabled": True, "rollout_percentage": 100, "kill_switch": True}
        }

        self.assertTrue(self.system.is_feature_enabled("enabled_feature"))
        self.assertFalse(self.system.is_feature_enabled("disabled_feature"))
        self.assertFalse(self.system.is_feature_enabled("killed_feature"))
        self.assertFalse(self.system.is_feature_enabled("nonexistent_feature"))

    def test_rollout_percentage_logic(self):
        """Test percentage-based rollout logic"""
        self.system.flags = {
            "partial_rollout": {"enabled": True, "rollout_percentage": 50, "kill_switch": False}
        }

        # Test with different user IDs to verify percentage logic
        enabled_count = 0
        total_tests = 100

        for i in range(total_tests):
            if self.system.is_feature_enabled("partial_rollout", user_id=f"user_{i}"):
                enabled_count += 1

        # Should be approximately 50% (allow some variance)
        self.assertGreater(enabled_count, 35)  # At least 35%
        self.assertLess(enabled_count, 65)     # At most 65%

    def test_emergency_kill_switch(self):
        """Test emergency kill switch functionality"""
        feature_name = "test_feature"

        # Setup feature as enabled
        self.system.flags = {
            feature_name: {"enabled": True, "rollout_percentage": 100, "kill_switch": False}
        }

        # Verify feature is enabled
        self.assertTrue(self.system.is_feature_enabled(feature_name))

        # Activate kill switch
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                self.system.emergency_kill_switch(feature_name)

        # Verify kill switch was activated
        self.assertTrue(self.system.flags[feature_name]["kill_switch"])
        self.assertFalse(self.system.is_feature_enabled(feature_name))

class TestMonitoringHooks(unittest.TestCase):
    """Test Monitoring Hooks System"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.system = MonitoringHooks()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_ai_interaction(self):
        """Test AI interaction logging"""
        interaction_data = {
            "user_id": "user123",
            "input": "What is the contract summary?",
            "output": "This analysis is for educational purposes only...",
            "model": "gpt-4",
            "timestamp": datetime.now().isoformat()
        }

        with patch('builtins.open', mock_open()) as mock_file:
            self.system.log_ai_interaction(interaction_data)

        # Verify file was opened for writing
        mock_file.assert_called_once()

    def test_check_compliance_metrics_passing(self):
        """Test compliance metrics checking with passing scores"""
        mock_metrics = {
            "disclaimer_compliance": 100.0,
            "advice_language_compliance": 100.0,
            "encryption_compliance": 100.0,
            "overall_compliance": 100.0
        }

        result = self.system.check_compliance_metrics(mock_metrics)
        self.assertTrue(result.passed)
        self.assertEqual(result.compliance_score, 100.0)

    def test_check_compliance_metrics_failing(self):
        """Test compliance metrics checking with failing scores"""
        mock_metrics = {
            "disclaimer_compliance": 85.0,
            "advice_language_compliance": 90.0,
            "encryption_compliance": 95.0,
            "overall_compliance": 90.0
        }

        result = self.system.check_compliance_metrics(mock_metrics)
        self.assertFalse(result.passed)
        self.assertEqual(result.compliance_score, 90.0)

    def test_generate_compliance_report(self):
        """Test compliance report generation"""
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                report = self.system.generate_compliance_report()

        self.assertIn("report_date", report)
        self.assertIn("compliance_summary", report)
        self.assertIn("total_interactions", report)

class TestRollbackSystem(unittest.TestCase):
    """Test Automated Rollback System"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.system = RollbackSystem()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_backup_success(self):
        """Test backup creation"""
        backup_name = "test_backup"

        with patch('shutil.copytree') as mock_copytree:
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.dump') as mock_json_dump:
                    result = self.system.create_backup(backup_name)

        self.assertTrue(result.passed)
        self.assertIn("Backup created successfully", result.message)

    def test_list_available_backups(self):
        """Test listing available backups"""
        mock_backups = [
            {"name": "backup_1", "date": "2025-09-19", "size": "100MB"},
            {"name": "backup_2", "date": "2025-09-18", "size": "95MB"}
        ]

        with patch('os.listdir', return_value=["backup_1", "backup_2"]):
            with patch('builtins.open', mock_open(read_data=json.dumps({"backups": mock_backups}))):
                backups = self.system.list_available_backups()

        self.assertEqual(len(backups), 2)
        self.assertEqual(backups[0]["name"], "backup_1")

    def test_rollback_to_backup(self):
        """Test rollback to previous backup"""
        backup_name = "test_backup"

        with patch('shutil.rmtree') as mock_rmtree:
            with patch('shutil.copytree') as mock_copytree:
                with patch('builtins.open', mock_open(read_data='{"backups": [{"name": "test_backup"}]}')):
                    result = self.system.rollback_to_backup(backup_name)

        self.assertTrue(result.passed)
        self.assertIn("Rollback completed successfully", result.message)

    def test_emergency_rollback(self):
        """Test emergency rollback functionality"""
        with patch('builtins.open', mock_open(read_data='{"backups": [{"name": "latest_backup", "date": "2025-09-19"}]}')):
            with patch.object(self.system, 'rollback_to_backup') as mock_rollback:
                mock_rollback.return_value = SafetyCheckResult(True, 100.0, "Emergency rollback completed", [])

                result = self.system.emergency_rollback()

        self.assertTrue(result.passed)
        mock_rollback.assert_called_once()

class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios across all safety rails components"""

    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = SafetyRailsConfig(
            enable_pre_commit_checks=True,
            enable_feature_flags=True,
            enable_monitoring=True,
            enable_rollback=True,
            compliance_threshold=100.0,
            max_rollback_days=30
        )

    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_deployment_safety_check(self):
        """Test complete deployment safety validation"""
        system = SafetyRailsSystem(self.config)

        # Mock all subsystem checks as passing
        with patch('src.core.safety_rails.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "All tests passed"

            with patch('builtins.open', mock_open(read_data='{"statistics": {"success_rate": 100.0}}')):
                result = system.run_comprehensive_safety_check()

        self.assertTrue(result.passed)
        self.assertEqual(result.compliance_score, 100.0)

    def test_feature_flag_compliance_integration(self):
        """Test feature flag system with compliance monitoring"""
        flag_system = FeatureFlagSystem()
        monitoring = MonitoringHooks()

        # Setup compliance-critical feature
        flag_system.flags = {
            "ai_legal_advice_blocker": {
                "enabled": True,
                "rollout_percentage": 100,
                "kill_switch": False
            }
        }

        # Verify critical safety feature is enabled
        self.assertTrue(flag_system.is_feature_enabled("ai_legal_advice_blocker"))

        # Test compliance metrics
        mock_metrics = {"overall_compliance": 100.0}
        compliance_result = monitoring.check_compliance_metrics(mock_metrics)
        self.assertTrue(compliance_result.passed)

    def test_rollback_after_compliance_failure(self):
        """Test automated rollback after compliance failure"""
        system = SafetyRailsSystem(self.config)
        rollback = RollbackSystem()

        # Simulate compliance failure
        with patch('src.core.safety_rails.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 1  # Test failure
            mock_subprocess.return_value.stdout = "Tests failed"

            with patch('builtins.open', mock_open(read_data='{"statistics": {"success_rate": 85.0}}')):
                safety_result = system.run_comprehensive_safety_check()

        self.assertFalse(safety_result.passed)

        # Trigger emergency rollback
        with patch('builtins.open', mock_open(read_data='{"backups": [{"name": "safe_backup"}]}')):
            with patch.object(rollback, 'rollback_to_backup') as mock_rollback:
                mock_rollback.return_value = SafetyCheckResult(True, 100.0, "Rollback successful", [])

                rollback_result = rollback.emergency_rollback()

        self.assertTrue(rollback_result.passed)

def run_comprehensive_safety_rails_test():
    """Run all safety rails tests and generate comprehensive report"""
    print("=" * 60)
    print("COMPREHENSIVE SAFETY RAILS SYSTEM TEST")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestSafetyRailsSystem,
        TestPreCommitSafetySystem,
        TestFeatureFlagSystem,
        TestMonitoringHooks,
        TestRollbackSystem,
        TestIntegrationScenarios
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

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
    print("SAFETY RAILS TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    print(f"Skipped: {skipped}")
    print(f"Success Rate: {success_rate:.1f}%")

    if success_rate >= 100.0:
        print("\n✓ ALL SAFETY RAILS TESTS PASSED - SYSTEM READY FOR DEPLOYMENT")
        deployment_approved = True
    else:
        print(f"\n✗ SAFETY RAILS TESTS FAILED - DEPLOYMENT BLOCKED")
        deployment_approved = False

    # Save test results
    test_results = {
        "test_run": {
            "start_time": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed": passed,
            "failed": failures,
            "errors": errors,
            "skipped": skipped,
            "success_rate": success_rate,
            "deployment_approved": deployment_approved
        },
        "test_details": {
            "failures": [str(failure) for failure in result.failures],
            "errors": [str(error) for error in result.errors]
        }
    }

    with open("safety_rails_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)

    print(f"\nDetailed results saved to: safety_rails_test_results.json")

    return deployment_approved

if __name__ == "__main__":
    success = run_comprehensive_safety_rails_test()
    sys.exit(0 if success else 1)