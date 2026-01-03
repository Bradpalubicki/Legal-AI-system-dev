#!/usr/bin/env python3
"""
Comprehensive tests for the legal terms acceptance system
Tests TermsAcceptanceManager, AgreementContentManager, and all related functionality
"""

import pytest
import tempfile
import os
import sqlite3
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open

# Import the classes to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'shared', 'compliance'))

from terms_acceptance import (
    AgreementType, AcceptanceStatus, AcceptanceMethod, UserType,
    AgreementVersion, UserAcceptance, AcceptanceRequirement,
    AgreementContentManager, TermsAcceptanceManager, create_terms_acceptance_system
)


class TestAgreementContentManager:
    """Test AgreementContentManager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.content_manager = AgreementContentManager(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_agreement_content_success(self):
        """Test successful loading of agreement content"""
        # Create test agreement file
        test_content = """# Terms of Service
        
**Effective Date:** 2024-01-01
**Version:** 1.0

This is test content for terms of service.
"""
        
        tos_file = os.path.join(self.temp_dir, "terms_of_service.md")
        with open(tos_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Test loading content
        content = self.content_manager.load_agreement_content(AgreementType.TERMS_OF_SERVICE)
        
        assert content is not None
        assert "Terms of Service" in content
        assert "Effective Date" in content
        assert "Version:" in content
    
    def test_load_agreement_content_file_not_found(self):
        """Test handling of missing agreement file"""
        content = self.content_manager.load_agreement_content(AgreementType.TERMS_OF_SERVICE)
        assert content is None
    
    def test_load_agreement_content_caching(self):
        """Test content caching functionality"""
        # Create test file
        test_content = "# Test Agreement Content"
        tos_file = os.path.join(self.temp_dir, "terms_of_service.md")
        with open(tos_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Load content twice
        content1 = self.content_manager.load_agreement_content(AgreementType.TERMS_OF_SERVICE)
        content2 = self.content_manager.load_agreement_content(AgreementType.TERMS_OF_SERVICE)
        
        assert content1 == content2
        assert content1 is not None
    
    def test_calculate_content_hash(self):
        """Test content hash calculation"""
        test_content = "This is test content for hashing"
        hash1 = self.content_manager.calculate_content_hash(test_content)
        hash2 = self.content_manager.calculate_content_hash(test_content)
        
        # Same content should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest length
        
        # Different content should produce different hash
        hash3 = self.content_manager.calculate_content_hash("Different content")
        assert hash1 != hash3
    
    def test_extract_agreement_metadata(self):
        """Test extraction of metadata from agreement content"""
        test_content = """# Test Agreement

**Effective Date:** 2024-01-01
**Last Updated:** 2024-01-15
**Version:** 1.2

Content of the agreement...
"""
        
        metadata = self.content_manager.extract_agreement_metadata(test_content)
        
        assert "effective_date" in metadata
        assert "last_updated" in metadata
        assert "version" in metadata
        assert metadata["effective_date"] == "2024-01-01"
        assert metadata["last_updated"] == "2024-01-15"
        assert metadata["version"] == "1.2"


class TestTermsAcceptanceManager:
    """Test TermsAcceptanceManager functionality"""
    
    def setup_method(self):
        """Setup test database and manager"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.temp_dir = tempfile.mkdtemp()
        self.manager = TermsAcceptanceManager(db_path=self.temp_db.name)
        self.manager.content_manager = AgreementContentManager(self.temp_dir)
        
        # Create test agreement files
        self._create_test_agreement_files()
    
    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_agreement_files(self):
        """Create test agreement files"""
        agreements = {
            "terms_of_service.md": """# Terms of Service
**Effective Date:** 2024-01-01
**Version:** 1.0
Test terms of service content.""",
            "privacy_policy.md": """# Privacy Policy
**Effective Date:** 2024-01-01
**Version:** 1.0
Test privacy policy content.""",
            "acceptable_use_policy.md": """# Acceptable Use Policy
**Effective Date:** 2024-01-01
**Version:** 1.0
Test acceptable use policy content."""
        }
        
        for filename, content in agreements.items():
            with open(os.path.join(self.temp_dir, filename), 'w', encoding='utf-8') as f:
                f.write(content)
    
    def test_database_initialization(self):
        """Test database schema creation"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Check if tables were created
        expected_tables = [
            'agreement_versions', 'user_acceptances', 'acceptance_requirements',
            'acceptance_reminders', 'access_control_log', 'compliance_audit_log'
        ]
        
        for table in expected_tables:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            assert cursor.fetchone() is not None, f"Table {table} not created"
        
        conn.close()
    
    def test_create_agreement_version(self):
        """Test creating new agreement version"""
        version_id = self.manager.create_agreement_version(
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            version_number="1.0",
            title="Test Terms of Service",
            created_by="test_admin",
            change_summary="Initial version",
            mandatory_acceptance=True,
            requires_explicit_consent=True,
            targeted_user_types=[UserType.ATTORNEY, UserType.CLIENT]
        )
        
        assert version_id is not None
        assert len(version_id) == 36  # UUID format
        
        # Verify in database
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.execute(
            "SELECT * FROM agreement_versions WHERE version_id = ?",
            (version_id,)
        )
        record = cursor.fetchone()
        conn.close()
        
        assert record is not None
        assert record[1] == "terms_of_service"  # agreement_type
        assert record[2] == "1.0"  # version_number
        assert record[3] == "Test Terms of Service"  # title
    
    def test_create_agreement_version_deactivates_previous(self):
        """Test that creating new version deactivates previous versions"""
        # Create first version
        version1_id = self.manager.create_agreement_version(
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            version_number="1.0",
            title="Terms v1.0",
            created_by="admin",
            change_summary="Initial version"
        )
        
        # Create second version
        version2_id = self.manager.create_agreement_version(
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            version_number="1.1", 
            title="Terms v1.1",
            created_by="admin",
            change_summary="Updated version"
        )
        
        # Check that v1.0 is deactivated and v1.1 is active
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.execute(
            "SELECT active FROM agreement_versions WHERE version_id = ?",
            (version1_id,)
        )
        v1_active = cursor.fetchone()[0]
        
        cursor = conn.execute(
            "SELECT active FROM agreement_versions WHERE version_id = ?",
            (version2_id,)
        )
        v2_active = cursor.fetchone()[0]
        
        conn.close()
        
        assert v1_active == 0  # Deactivated
        assert v2_active == 1  # Active
    
    def test_check_user_compliance_no_acceptances(self):
        """Test compliance check for user with no acceptances"""
        compliance = self.manager.check_user_compliance("new_user", UserType.ATTORNEY)
        
        assert compliance["compliant"] is False
        assert len(compliance["missing_agreements"]) > 0
        assert len(compliance["expired_agreements"]) == 0
        assert "terms_of_service" in compliance["missing_agreements"]
        assert "privacy_policy" in compliance["missing_agreements"]
    
    def test_check_user_compliance_compliant_user(self):
        """Test compliance check for compliant user"""
        # Create agreement versions
        tos_version_id = self.manager.create_agreement_version(
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            version_number="1.0",
            title="Terms of Service",
            created_by="admin",
            change_summary="Initial version"
        )
        
        pp_version_id = self.manager.create_agreement_version(
            agreement_type=AgreementType.PRIVACY_POLICY,
            version_number="1.0",
            title="Privacy Policy",
            created_by="admin",
            change_summary="Initial version"
        )
        
        aup_version_id = self.manager.create_agreement_version(
            agreement_type=AgreementType.ACCEPTABLE_USE_POLICY,
            version_number="1.0",
            title="Acceptable Use Policy",
            created_by="admin",
            change_summary="Initial version"
        )
        
        # Record acceptances
        user_id = "compliant_attorney"
        for agreement_type in [AgreementType.TERMS_OF_SERVICE, 
                              AgreementType.PRIVACY_POLICY, 
                              AgreementType.ACCEPTABLE_USE_POLICY]:
            self.manager.record_user_acceptance(
                user_id=user_id,
                agreement_type=agreement_type,
                acceptance_method=AcceptanceMethod.EXPLICIT_CLICK,
                ip_address="192.168.1.100",
                user_agent="Test Browser",
                session_id="test_session",
                explicit_consent=True,
                consent_text="I agree to the terms"
            )
        
        # Check compliance
        compliance = self.manager.check_user_compliance(user_id, UserType.ATTORNEY)
        
        assert compliance["compliant"] is True
        assert len(compliance["missing_agreements"]) == 0
        assert len(compliance["expired_agreements"]) == 0
    
    def test_force_acceptance_check_compliant(self):
        """Test force acceptance check for compliant user"""
        # Setup compliant user (similar to previous test)
        user_id = "compliant_user"
        
        # Create and accept agreements
        for agreement_type in [AgreementType.TERMS_OF_SERVICE, 
                              AgreementType.PRIVACY_POLICY,
                              AgreementType.ACCEPTABLE_USE_POLICY]:
            self.manager.create_agreement_version(
                agreement_type=agreement_type,
                version_number="1.0",
                title=f"Test {agreement_type.value}",
                created_by="admin",
                change_summary="Test version"
            )
            
            self.manager.record_user_acceptance(
                user_id=user_id,
                agreement_type=agreement_type,
                acceptance_method=AcceptanceMethod.EXPLICIT_CLICK,
                ip_address="192.168.1.100",
                user_agent="Test Browser",
                session_id="test_session"
            )
        
        can_access, required = self.manager.force_acceptance_check(user_id, UserType.ATTORNEY)
        
        assert can_access is True
        assert len(required) == 0
    
    def test_force_acceptance_check_non_compliant(self):
        """Test force acceptance check for non-compliant user"""
        can_access, required = self.manager.force_acceptance_check("new_user", UserType.ATTORNEY)
        
        assert can_access is False
        assert len(required) > 0
        assert AgreementType.TERMS_OF_SERVICE in required
        assert AgreementType.PRIVACY_POLICY in required
    
    def test_record_user_acceptance(self):
        """Test recording user acceptance"""
        # Create agreement version first
        version_id = self.manager.create_agreement_version(
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            version_number="1.0",
            title="Terms of Service",
            created_by="admin",
            change_summary="Test version"
        )
        
        # Record acceptance
        acceptance_id = self.manager.record_user_acceptance(
            user_id="test_user",
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            acceptance_method=AcceptanceMethod.EXPLICIT_CLICK,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser",
            session_id="test_session_123",
            explicit_consent=True,
            consent_text="I agree to the terms and conditions",
            metadata={"test": "data"}
        )
        
        assert acceptance_id is not None
        assert len(acceptance_id) == 36  # UUID format
        
        # Verify in database
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.execute(
            "SELECT * FROM user_acceptances WHERE acceptance_id = ?",
            (acceptance_id,)
        )
        record = cursor.fetchone()
        conn.close()
        
        assert record is not None
        assert record[1] == "test_user"  # user_id
        assert record[2] == "terms_of_service"  # agreement_type
        assert record[4] == "accepted"  # acceptance_status
        assert record[5] == "explicit_click"  # acceptance_method
    
    def test_record_user_acceptance_no_version(self):
        """Test recording acceptance when no agreement version exists"""
        with pytest.raises(ValueError) as excinfo:
            self.manager.record_user_acceptance(
                user_id="test_user",
                agreement_type=AgreementType.TERMS_OF_SERVICE,
                acceptance_method=AcceptanceMethod.EXPLICIT_CLICK,
                ip_address="192.168.1.100",
                user_agent="Test Browser",
                session_id="test_session"
            )
        
        assert "No active version found" in str(excinfo.value)
    
    def test_get_acceptance_ui_data_required(self):
        """Test getting UI data when acceptances are required"""
        # Create agreement versions
        self.manager.create_agreement_version(
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            version_number="1.0",
            title="Terms of Service",
            created_by="admin",
            change_summary="Initial version"
        )
        
        ui_data = self.manager.get_acceptance_ui_data("new_user", UserType.ATTORNEY)
        
        assert ui_data["required"] is True
        assert ui_data["force_acceptance"] is True
        assert len(ui_data["agreements"]) > 0
        
        # Check agreement details
        tos_agreement = next(
            (ag for ag in ui_data["agreements"] if ag["type"] == "terms_of_service"), 
            None
        )
        assert tos_agreement is not None
        assert tos_agreement["title"] == "Terms of Service"
        assert tos_agreement["version"] == "1.0"
        assert tos_agreement["mandatory"] is True
    
    def test_get_acceptance_ui_data_not_required(self):
        """Test getting UI data when no acceptances are required"""
        # Create and accept all required agreements
        user_id = "compliant_user"
        
        for agreement_type in [AgreementType.TERMS_OF_SERVICE, 
                              AgreementType.PRIVACY_POLICY,
                              AgreementType.ACCEPTABLE_USE_POLICY]:
            self.manager.create_agreement_version(
                agreement_type=agreement_type,
                version_number="1.0",
                title=f"Test {agreement_type.value}",
                created_by="admin",
                change_summary="Test version"
            )
            
            self.manager.record_user_acceptance(
                user_id=user_id,
                agreement_type=agreement_type,
                acceptance_method=AcceptanceMethod.EXPLICIT_CLICK,
                ip_address="192.168.1.100",
                user_agent="Test Browser",
                session_id="test_session"
            )
        
        ui_data = self.manager.get_acceptance_ui_data(user_id, UserType.ATTORNEY)
        
        assert ui_data["required"] is False
        assert len(ui_data["agreements"]) == 0
    
    def test_process_bulk_acceptance(self):
        """Test processing multiple acceptances at once"""
        # Create agreement versions
        agreement_types = [
            AgreementType.TERMS_OF_SERVICE,
            AgreementType.PRIVACY_POLICY,
            AgreementType.ACCEPTABLE_USE_POLICY
        ]
        
        for agreement_type in agreement_types:
            self.manager.create_agreement_version(
                agreement_type=agreement_type,
                version_number="1.0",
                title=f"Test {agreement_type.value}",
                created_by="admin",
                change_summary="Test version"
            )
        
        # Process bulk acceptance
        acceptances = [
            {
                "agreement_type": "terms_of_service",
                "method": "explicit_click",
                "explicit_consent": True,
                "consent_text": "I agree to terms"
            },
            {
                "agreement_type": "privacy_policy",
                "method": "explicit_click",
                "explicit_consent": True,
                "consent_text": "I agree to privacy policy"
            },
            {
                "agreement_type": "acceptable_use_policy",
                "method": "explicit_click",
                "explicit_consent": True,
                "consent_text": "I agree to acceptable use"
            }
        ]
        
        results = self.manager.process_bulk_acceptance(
            user_id="bulk_user",
            acceptances=acceptances,
            ip_address="192.168.1.100",
            user_agent="Test Browser",
            session_id="bulk_session"
        )
        
        assert results["total"] == 3
        assert len(results["successful"]) == 3
        assert len(results["failed"]) == 0
        
        # Verify user is now compliant
        compliance = self.manager.check_user_compliance("bulk_user", UserType.ATTORNEY)
        assert compliance["compliant"] is True
    
    def test_process_bulk_acceptance_partial_failure(self):
        """Test bulk acceptance with some failures"""
        # Create only one agreement version
        self.manager.create_agreement_version(
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            version_number="1.0",
            title="Terms of Service",
            created_by="admin",
            change_summary="Test version"
        )
        
        # Try to accept multiple agreements (some don't exist)
        acceptances = [
            {
                "agreement_type": "terms_of_service",
                "method": "explicit_click",
                "explicit_consent": True
            },
            {
                "agreement_type": "privacy_policy",  # This doesn't exist
                "method": "explicit_click", 
                "explicit_consent": True
            }
        ]
        
        results = self.manager.process_bulk_acceptance(
            user_id="partial_user",
            acceptances=acceptances,
            ip_address="192.168.1.100",
            user_agent="Test Browser",
            session_id="partial_session"
        )
        
        assert results["total"] == 2
        assert len(results["successful"]) == 1
        assert len(results["failed"]) == 1
        assert results["successful"][0]["agreement_type"] == "terms_of_service"
    
    def test_generate_compliance_report(self):
        """Test compliance report generation"""
        # Create some test data
        user_id = "report_user"
        
        # Create agreement and record acceptance
        self.manager.create_agreement_version(
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            version_number="1.0",
            title="Terms of Service",
            created_by="admin",
            change_summary="Test version"
        )
        
        self.manager.record_user_acceptance(
            user_id=user_id,
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            acceptance_method=AcceptanceMethod.EXPLICIT_CLICK,
            ip_address="192.168.1.100",
            user_agent="Test Browser",
            session_id="report_session"
        )
        
        # Generate report
        report = self.manager.generate_compliance_report()
        
        assert "report_period" in report
        assert "summary" in report
        assert "events_by_type" in report
        assert "compliance_status" in report
        assert report["summary"]["total_events"] >= 0
        assert "USER_ACCEPTED" in report["events_by_type"]
    
    def test_generate_compliance_report_user_specific(self):
        """Test user-specific compliance report"""
        user_id = "specific_user"
        
        # Create and accept agreement
        self.manager.create_agreement_version(
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            version_number="1.0",
            title="Terms of Service",
            created_by="admin",
            change_summary="Test version"
        )
        
        self.manager.record_user_acceptance(
            user_id=user_id,
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            acceptance_method=AcceptanceMethod.EXPLICIT_CLICK,
            ip_address="192.168.1.100",
            user_agent="Test Browser",
            session_id="specific_session"
        )
        
        # Generate user-specific report
        report = self.manager.generate_compliance_report(user_id=user_id)
        
        assert report["report_period"]["user_id"] == user_id
        assert "summary" in report
        assert report["summary"]["total_events"] >= 0
    
    def test_user_type_specific_requirements(self):
        """Test that different user types have different requirements"""
        # Attorney requirements
        attorney_compliance = self.manager.check_user_compliance("test_attorney", UserType.ATTORNEY)
        attorney_required = attorney_compliance["required_agreements"]
        
        # Client requirements  
        client_compliance = self.manager.check_user_compliance("test_client", UserType.CLIENT)
        client_required = client_compliance["required_agreements"]
        
        # Attorney should have more requirements than client
        assert len(attorney_required) >= len(client_required)
        
        # Both should require terms of service and privacy policy
        assert "terms_of_service" in attorney_required
        assert "privacy_policy" in attorney_required
        assert "terms_of_service" in client_required
        assert "privacy_policy" in client_required


class TestEnumsAndDataClasses:
    """Test enum and dataclass functionality"""
    
    def test_agreement_type_enum(self):
        """Test AgreementType enum values"""
        assert AgreementType.TERMS_OF_SERVICE.value == "terms_of_service"
        assert AgreementType.PRIVACY_POLICY.value == "privacy_policy"
        assert AgreementType.ACCEPTABLE_USE_POLICY.value == "acceptable_use_policy"
    
    def test_acceptance_status_enum(self):
        """Test AcceptanceStatus enum values"""
        assert AcceptanceStatus.PENDING.value == "pending"
        assert AcceptanceStatus.ACCEPTED.value == "accepted"
        assert AcceptanceStatus.EXPIRED.value == "expired"
        assert AcceptanceStatus.REQUIRES_UPDATE.value == "requires_update"
    
    def test_user_type_enum(self):
        """Test UserType enum values"""
        assert UserType.ATTORNEY.value == "attorney"
        assert UserType.CLIENT.value == "client"
        assert UserType.PRO_SE.value == "pro_se"
        assert UserType.PARALEGAL.value == "paralegal"
    
    def test_agreement_version_dataclass(self):
        """Test AgreementVersion dataclass"""
        version = AgreementVersion(
            version_id="test-id",
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            version_number="1.0",
            title="Test Agreement",
            file_path="test.md",
            content_hash="testhash",
            effective_date=datetime.now(),
            expiration_date=None,
            mandatory_acceptance=True,
            targeted_user_types=[UserType.ATTORNEY],
            change_summary="Test version",
            requires_explicit_consent=True,
            created_by="admin",
            created_date=datetime.now()
        )
        
        assert version.version_id == "test-id"
        assert version.agreement_type == AgreementType.TERMS_OF_SERVICE
        assert version.mandatory_acceptance is True
        assert UserType.ATTORNEY in version.targeted_user_types
    
    def test_user_acceptance_dataclass(self):
        """Test UserAcceptance dataclass"""
        acceptance = UserAcceptance(
            acceptance_id="accept-id",
            user_id="user123",
            agreement_type=AgreementType.PRIVACY_POLICY,
            version_id="version-id",
            acceptance_status=AcceptanceStatus.ACCEPTED,
            acceptance_method=AcceptanceMethod.EXPLICIT_CLICK,
            acceptance_date=datetime.now(),
            ip_address="192.168.1.100",
            user_agent="Test Browser",
            session_id="session123",
            explicit_consent_given=True,
            consent_text_shown="I agree",
            metadata={"test": "data"}
        )
        
        assert acceptance.user_id == "user123"
        assert acceptance.agreement_type == AgreementType.PRIVACY_POLICY
        assert acceptance.acceptance_status == AcceptanceStatus.ACCEPTED
        assert acceptance.explicit_consent_given is True


class TestFactoryFunction:
    """Test factory function and initialization"""
    
    def setup_method(self):
        """Setup for factory function tests"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_terms_acceptance_system(self):
        """Test factory function creates system correctly"""
        system = create_terms_acceptance_system(
            db_path=self.temp_db.name,
            agreements_directory=self.temp_dir
        )
        
        assert isinstance(system, TermsAcceptanceManager)
        assert system.content_manager is not None
        assert system.content_manager.agreements_directory == self.temp_dir
        
        # Test that database was initialized
        assert os.path.exists(self.temp_db.name)


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios"""
    
    def setup_method(self):
        """Setup integration testing environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.temp_dir = tempfile.mkdtemp()
        self.system = create_terms_acceptance_system(
            db_path=self.temp_db.name,
            agreements_directory=self.temp_dir
        )
        
        # Create test agreement files
        self._create_test_files()
    
    def teardown_method(self):
        """Cleanup"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_files(self):
        """Create test agreement files"""
        agreements = {
            "terms_of_service.md": "# Terms of Service\nTest content",
            "privacy_policy.md": "# Privacy Policy\nTest content", 
            "acceptable_use_policy.md": "# Acceptable Use Policy\nTest content"
        }
        
        for filename, content in agreements.items():
            with open(os.path.join(self.temp_dir, filename), 'w') as f:
                f.write(content)
    
    def test_new_attorney_registration_flow(self):
        """Test complete flow for new attorney registration"""
        user_id = "new_attorney_001"
        user_type = UserType.ATTORNEY
        
        # 1. Check initial compliance (should be non-compliant)
        can_access, required = self.system.force_acceptance_check(user_id, user_type)
        assert can_access is False
        assert len(required) > 0
        
        # 2. Create agreement versions
        for agreement_type in required:
            if agreement_type in [AgreementType.TERMS_OF_SERVICE, 
                                AgreementType.PRIVACY_POLICY,
                                AgreementType.ACCEPTABLE_USE_POLICY]:
                self.system.create_agreement_version(
                    agreement_type=agreement_type,
                    version_number="1.0",
                    title=f"Test {agreement_type.value}",
                    created_by="admin",
                    change_summary="Initial version"
                )
        
        # 3. Get UI data for acceptance
        ui_data = self.system.get_acceptance_ui_data(user_id, user_type)
        assert ui_data["required"] is True
        assert len(ui_data["agreements"]) > 0
        
        # 4. Process bulk acceptance (simulate user accepting all)
        acceptances = []
        for agreement in ui_data["agreements"]:
            acceptances.append({
                "agreement_type": agreement["type"],
                "method": "explicit_click",
                "explicit_consent": True,
                "consent_text": f"I agree to the {agreement['title']}"
            })
        
        results = self.system.process_bulk_acceptance(
            user_id=user_id,
            acceptances=acceptances,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Registration Flow",
            session_id="registration_session"
        )
        
        assert len(results["successful"]) == len(acceptances)
        assert len(results["failed"]) == 0
        
        # 5. Verify user is now compliant
        can_access_after, required_after = self.system.force_acceptance_check(user_id, user_type)
        assert can_access_after is True
        assert len(required_after) == 0
        
        # 6. Generate compliance report
        report = self.system.generate_compliance_report(user_id=user_id)
        assert report["compliance_status"] == "COMPLIANT"
    
    def test_agreement_version_update_scenario(self):
        """Test scenario when agreement version is updated"""
        user_id = "existing_attorney"
        user_type = UserType.ATTORNEY
        
        # 1. Create initial version and user accepts
        v1_id = self.system.create_agreement_version(
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            version_number="1.0",
            title="Terms of Service v1.0",
            created_by="admin",
            change_summary="Initial version"
        )
        
        self.system.record_user_acceptance(
            user_id=user_id,
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            acceptance_method=AcceptanceMethod.EXPLICIT_CLICK,
            ip_address="192.168.1.100",
            user_agent="Test Browser",
            session_id="initial_session"
        )
        
        # 2. Create updated version
        v2_id = self.system.create_agreement_version(
            agreement_type=AgreementType.TERMS_OF_SERVICE,
            version_number="2.0",
            title="Terms of Service v2.0",
            created_by="admin",
            change_summary="Major update with new liability terms"
        )
        
        # 3. User should now need to accept new version
        # Note: This would require additional logic to invalidate old acceptances
        # when new mandatory versions are created
        
        # 4. Verify latest version is returned
        latest_version = self.system._get_latest_agreement_version(AgreementType.TERMS_OF_SERVICE)
        assert latest_version.version_id == v2_id
        assert latest_version.version_number == "2.0"
    
    def test_pro_se_user_simplified_flow(self):
        """Test simplified flow for pro se users"""
        user_id = "pro_se_user_001"
        user_type = UserType.PRO_SE
        
        # Pro se users should have different requirements
        compliance = self.system.check_user_compliance(user_id, user_type)
        
        # Should still require core agreements
        assert "terms_of_service" in compliance["required_agreements"]
        assert "privacy_policy" in compliance["required_agreements"]
        
        # Create and accept required agreements
        for agreement_type_str in compliance["required_agreements"]:
            agreement_type = AgreementType(agreement_type_str)
            
            if agreement_type in [AgreementType.TERMS_OF_SERVICE,
                                AgreementType.PRIVACY_POLICY,
                                AgreementType.ACCEPTABLE_USE_POLICY]:
                self.system.create_agreement_version(
                    agreement_type=agreement_type,
                    version_number="1.0",
                    title=f"Test {agreement_type.value}",
                    created_by="admin",
                    change_summary="Initial version"
                )
                
                self.system.record_user_acceptance(
                    user_id=user_id,
                    agreement_type=agreement_type,
                    acceptance_method=AcceptanceMethod.EXPLICIT_CLICK,
                    ip_address="192.168.1.100",
                    user_agent="Pro Se Browser",
                    session_id="pro_se_session"
                )
        
        # Verify compliance
        final_compliance = self.system.check_user_compliance(user_id, user_type)
        assert final_compliance["compliant"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])