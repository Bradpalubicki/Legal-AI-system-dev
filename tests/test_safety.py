#!/usr/bin/env python3
"""
Security Tests for Legal AI System
Comprehensive security testing for all system components
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestSystemSecurity(unittest.TestCase):
    """Security tests for legal AI system"""

    def test_password_hashing_security(self):
        """Test password hashing security"""
        try:
            from src.security.auth_manager import AuthenticationManager
            auth = AuthenticationManager()
            password = "test_password"
            salt = "test_salt"
            hash1 = auth._hash_password(password, salt)
            hash2 = auth._hash_password(password, salt)
            self.assertEqual(hash1, hash2, "Password hashing consistent")
            self.assertNotEqual(password, hash1, "Password was hashed")
        except Exception as e:
            self.fail(f"Password hashing security test failed: {e}")

    def test_session_security(self):
        """Test session security"""
        try:
            from src.security.session_manager import session_manager
            session_id = session_manager.create_session(
                user_id="TEST_USER",
                ip_address="127.0.0.1",
                user_agent="Test Browser"
            )
            self.assertIsNotNone(session_id, "Session created")
            is_valid = session_manager.verify_session(session_id, "127.0.0.1", "Test Browser")
            self.assertTrue(is_valid, "Session verification working")
        except Exception as e:
            self.fail(f"Session security test failed: {e}")

    def test_encryption_security(self):
        """Test encryption security"""
        try:
            from src.core.encryption_manager import EncryptionManager
            encryption = EncryptionManager()
            test_data = "sensitive_legal_data"
            encrypted = encryption.encrypt_data(test_data)
            self.assertNotEqual(test_data, encrypted, "Data was encrypted")
            secure_token = encryption.generate_secure_token()
            self.assertGreater(len(secure_token), 32, "Secure token generated")
        except Exception as e:
            self.fail(f"Encryption security test failed: {e}")

if __name__ == "__main__":
    unittest.main()
