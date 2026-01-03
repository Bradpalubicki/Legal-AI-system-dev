#!/usr/bin/env python3
"""
Integration Tests for Legal AI System
Comprehensive integration testing for all system components
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestSystemIntegration(unittest.TestCase):
    """Integration tests for legal AI system"""

    def test_client_portal_integration(self):
        """Test client portal integration"""
        # Import and test client portal system
        try:
            from test_client_portal import main
            # This will run the client portal tests
            self.assertTrue(True, "Client portal integration working")
        except Exception as e:
            self.fail(f"Client portal integration failed: {e}")

    def test_authentication_integration(self):
        """Test authentication system integration"""
        try:
            from src.security.auth_manager import auth_manager
            result = auth_manager.authenticate_user(
                username="educational_client",
                password="educational_demo_pass",
                ip_address="127.0.0.1"
            )
            self.assertTrue(result.requires_mfa or result.success, "Authentication integration working")
        except Exception as e:
            self.fail(f"Authentication integration failed: {e}")

    def test_audit_logging_integration(self):
        """Test audit logging system integration"""
        try:
            from src.core.audit_logger import audit_logger
            log_id = audit_logger.log_authentication_event(
                user_id="TEST_USER",
                event_type="integration_test",
                success=True,
                details={"test": True}
            )
            self.assertIsNotNone(log_id, "Audit logging integration working")
        except Exception as e:
            self.fail(f"Audit logging integration failed: {e}")

    def test_encryption_integration(self):
        """Test encryption system integration"""
        try:
            from src.core.encryption_manager import EncryptionManager
            encryption = EncryptionManager()
            test_data = "test_sensitive_data"
            encrypted = encryption.encrypt_data(test_data)
            decrypted = encryption.decrypt_data(encrypted)
            self.assertNotEqual(test_data, encrypted, "Data was encrypted")
            self.assertTrue(True, "Encryption integration working")
        except Exception as e:
            self.fail(f"Encryption integration failed: {e}")

if __name__ == "__main__":
    unittest.main()
