#!/usr/bin/env python3
"""
Compliance Tests for Legal AI System
Comprehensive compliance testing for all system components
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestSystemCompliance(unittest.TestCase):
    """Compliance tests for legal AI system"""

    def test_disclaimer_compliance(self):
        """Test disclaimer compliance"""
        try:
            # Import directly to avoid __init__.py dependency issues
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "compliance_framework",
                "src/client_portal/compliance_framework.py"
            )
            compliance_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(compliance_module)
            compliance_framework = compliance_module.compliance_framework
            
            disclaimers = compliance_framework.get_required_disclaimers("portal_access")
            self.assertGreater(len(disclaimers), 0, "Disclaimers are required")
        except Exception as e:
            self.fail(f"Disclaimer compliance test failed: {e}")

    def test_educational_framing_compliance(self):
        """Test educational framing compliance"""
        try:
            # Import directly to avoid __init__.py dependency issues
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "compliance_framework",
                "src/client_portal/compliance_framework.py"
            )
            compliance_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(compliance_module)
            compliance_framework = compliance_module.compliance_framework
            
            framing = compliance_framework.get_educational_framing("case_information")
            self.assertIsNotNone(framing, "Educational framing exists")
            self.assertTrue(framing.attorney_supervision_required, "Attorney supervision required")

            # Test state compliance - UPL prevention
            from src.core.state_compliance import state_compliance_manager
            status = state_compliance_manager.get_compliance_status()
            self.assertEqual(status["compliance_percentage"], 100.0, "State UPL compliance at 100%")

            # Test jurisdiction compliance
            self.assertIn("jurisdiction", str(status).lower(), "Jurisdiction compliance implemented")
            self.assertIn("state", str(status).lower(), "State rules compliance implemented")
            self.assertIn("local", str(status).lower(), "Local rules compliance implemented")
            self.assertIn("bar", str(status).lower(), "Bar admission requirements implemented")
        except Exception as e:
            self.fail(f"Educational framing compliance test failed: {e}")

    def test_audit_compliance(self):
        """Test audit compliance"""
        try:
            from src.core.audit_logger import audit_logger
            log_id = audit_logger.log_compliance_event(
                user_id="TEST_USER",
                event_type="compliance_test",
                compliance_type="disclaimer_acknowledgment",
                details={"test": True}
            )
            self.assertIsNotNone(log_id, "Compliance logging working")
            
            stats = audit_logger.get_audit_statistics()
            self.assertIn("total_logs", stats, "Audit statistics available")
        except Exception as e:
            self.fail(f"Audit compliance test failed: {e}")

if __name__ == "__main__":
    unittest.main()
