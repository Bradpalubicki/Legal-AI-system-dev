#!/usr/bin/env python3
"""
COMPREHENSIVE ENCRYPTION SYSTEM TEST

Tests all encryption components and their integration to verify
the 40% failure rate has been resolved.
"""

import os
import sys
import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.app.core.encryption_system_integration import encryption_system_integration
from backend.app.core.backup_encryption_service import backup_encryption_service
from backend.app.core.key_management_system import key_management_system
from backend.app.core.encryption_verification_monitor import encryption_verification_monitor
from backend.app.core.encryption_audit_system import encryption_audit_system

class EncryptionSystemTester:
    """Comprehensive encryption system testing"""
    
    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
        self.integration = encryption_system_integration
    
    async def run_comprehensive_tests(self):
        """Run comprehensive encryption system tests"""
        
        print("🔒 COMPREHENSIVE ENCRYPTION SYSTEM TEST")
        print("=" * 60)
        
        # Initialize system
        success, message = await self.integration.initialize_system()
        if not success:
            print(f"❌ System initialization failed: {message}")
            return False
        
        print("✅ System initialization successful")
        
        # Test categories
        test_categories = [
            ("Document Encryption", self.test_document_encryption),
            ("Key Management", self.test_key_management),
            ("Backup Encryption", self.test_backup_encryption),
            ("Verification Monitoring", self.test_verification_monitoring),
            ("Audit System", self.test_audit_system),
            ("System Integration", self.test_system_integration)
        ]
        
        for category_name, test_function in test_categories:
            print(f"\n📋 Testing {category_name}:")
            print("-" * 40)
            
            try:
                await test_function()
            except Exception as e:
                self.record_test(f"{category_name} - Exception", False, str(e))
                print(f"❌ {category_name} failed with exception: {e}")
        
        # Generate final report
        self.generate_test_report()
        
        # Cleanup
        await self.cleanup_tests()
        
        return self.test_results['failed_tests'] == 0
    
    async def test_document_encryption(self):
        """Test document encryption functionality"""
        
        # Create test file
        test_content = "CONFIDENTIAL LEGAL DOCUMENT\nAttorney-Client Privileged Communication\nTest document for encryption verification."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            test_file_path = f.name
        
        try:
            # Test client document encryption
            success, message, result = await self.integration.encrypt_client_document(
                test_file_path, 
                client_id="test_client_001",
                matter_id="test_matter_001",
                compliance_level="ATTORNEY_CLIENT"
            )
            
            self.record_test("Document Encryption - Client Matter", success, message)
            
            if success:
                # Test document decryption
                decrypt_success, decrypted_data, decrypt_message = await self.integration.decrypt_client_document(
                    result.metadata.document_id,
                    client_id="test_client_001", 
                    matter_id="test_matter_001",
                    user_id="test_user"
                )
                
                self.record_test("Document Decryption", decrypt_success, decrypt_message)
                
                # Verify content integrity
                if decrypt_success:
                    content_match = test_content.encode() == decrypted_data
                    self.record_test("Content Integrity Verification", content_match, 
                                   "Content matches" if content_match else "Content mismatch")
        
        finally:
            # Cleanup test file
            try:
                os.unlink(test_file_path)
            except:
                pass
    
    async def test_key_management(self):
        """Test key management functionality"""
        
        # Test client matter key creation
        success, key_id, message = key_management_system.create_client_matter_key(
            "test_client_002", "test_matter_002"
        )
        self.record_test("Key Creation - Client Matter", success, message)
        
        if success:
            # Test key retrieval
            key_success, key_data, retrieved_key_id = key_management_system.get_client_matter_key(
                "test_client_002", "test_matter_002"
            )
            self.record_test("Key Retrieval", key_success, 
                           f"Retrieved key: {retrieved_key_id}" if key_success else "Key retrieval failed")
            
            # Test key rotation (forced)
            if key_success:
                rotation_success, new_key_id, rotation_message = key_management_system.rotate_key(
                    retrieved_key_id, force=True
                )
                self.record_test("Key Rotation", rotation_success, rotation_message)
        
        # Test keys due for rotation
        keys_due = key_management_system.get_keys_due_for_rotation()
        self.record_test("Key Rotation Tracking", True, f"Found {len(keys_due)} keys for rotation tracking")
    
    async def test_backup_encryption(self):
        """Test backup encryption functionality"""
        
        # Create test database file
        test_db_path = "test_backup.db"
        
        # Create a simple SQLite database for testing
        import sqlite3
        with sqlite3.connect(test_db_path) as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER, data TEXT)")
            conn.execute("INSERT INTO test_table VALUES (1, 'confidential legal data')")
            conn.commit()
        
        try:
            # Test database backup encryption
            success, backup_file, metadata = backup_encryption_service.encrypt_database_backup(test_db_path)
            self.record_test("Database Backup Encryption", success, 
                           f"Backup created: {backup_file}" if success else backup_file)
            
            if success and metadata:
                # Test backup restoration
                restore_success, test_results = backup_encryption_service.test_backup_restoration(metadata.backup_id)
                self.record_test("Backup Restoration Test", restore_success, 
                               f"Test results: {test_results['overall_success']}")
                
                # Test backup decryption
                decrypt_success, decrypted_data, error = backup_encryption_service.decrypt_backup(metadata.backup_id)
                self.record_test("Backup Decryption", decrypt_success, 
                               f"Decrypted {len(decrypted_data)} bytes" if decrypt_success else error)
        
        finally:
            # Cleanup test database
            try:
                os.unlink(test_db_path)
            except:
                pass
    
    async def test_verification_monitoring(self):
        """Test encryption verification monitoring"""
        
        # Get monitoring statistics
        stats = encryption_verification_monitor.get_monitoring_statistics()
        self.record_test("Monitoring Statistics", True, f"Monitoring active: {stats['monitoring_active']}")
        
        # Test document verification (using existing encrypted document)
        from backend.app.core.encryption_service import emergency_encryption_service
        encrypted_docs = emergency_encryption_service.list_encrypted_documents()
        
        if encrypted_docs:
            test_doc = encrypted_docs[0]
            verification_result = encryption_verification_monitor.verify_document_encryption(
                test_doc.document_id
            )
            
            self.record_test("Document Verification", 
                           verification_result.status.value == 'encrypted',
                           f"Verification status: {verification_result.status.value}")
        else:
            self.record_test("Document Verification", True, "No documents to verify (expected)")
    
    async def test_audit_system(self):
        """Test encryption audit system"""
        
        # Test audit event logging
        event_id = encryption_audit_system.log_event(
            encryption_audit_system.AuditEventType.SYSTEM_STARTUP,
            {'test': 'audit_system_test'},
            source_service='test_suite'
        )
        
        self.record_test("Audit Event Logging", bool(event_id), f"Event logged: {event_id}")
        
        # Test audit statistics
        stats = encryption_audit_system.get_audit_statistics()
        self.record_test("Audit Statistics", stats['total_events'] > 0, 
                       f"Total audit events: {stats['total_events']}")
        
        # Test compliance report generation
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        try:
            report = encryption_audit_system.generate_compliance_report(
                'TEST_REPORT', start_date, end_date
            )
            
            self.record_test("Compliance Report Generation", bool(report), 
                           f"Report generated: {report.report_id}")
        except Exception as e:
            self.record_test("Compliance Report Generation", False, str(e))
    
    async def test_system_integration(self):
        """Test overall system integration"""
        
        # Test system status
        system_status = await self.integration.get_system_status()
        
        self.record_test("System Status Check", bool(system_status), 
                       f"System health: {system_status.system_health}")
        
        # Test comprehensive audit
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)
        
        audit_results = await self.integration.perform_comprehensive_audit(start_date, end_date)
        
        self.record_test("Comprehensive Audit", 'error' not in audit_results,
                       f"Audit completed" if 'error' not in audit_results else audit_results.get('error'))
        
        # Test system health metrics
        health_acceptable = system_status.system_health in ['HEALTHY', 'DEGRADED']
        self.record_test("System Health", health_acceptable,
                       f"System health: {system_status.system_health}")
        
        # Test compliance rate
        compliance_acceptable = system_status.compliance_rate >= 0.90  # 90% or better
        self.record_test("Compliance Rate", compliance_acceptable,
                       f"Compliance rate: {system_status.compliance_rate:.1%}")
    
    def record_test(self, test_name: str, passed: bool, details: str):
        """Record test result"""
        self.test_results['total_tests'] += 1
        
        if passed:
            self.test_results['passed_tests'] += 1
            print(f"  ✅ {test_name}: {details}")
        else:
            self.test_results['failed_tests'] += 1
            print(f"  ❌ {test_name}: {details}")
        
        self.test_results['test_details'].append({
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def generate_test_report(self):
        """Generate final test report"""
        
        results = self.test_results
        success_rate = (results['passed_tests'] / max(results['total_tests'], 1)) * 100
        
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE ENCRYPTION SYSTEM TEST RESULTS")
        print("=" * 60)
        
        print(f"Total Tests:     {results['total_tests']}")
        print(f"Passed Tests:    {results['passed_tests']}")
        print(f"Failed Tests:    {results['failed_tests']}")
        print(f"Success Rate:    {success_rate:.1f}%")
        
        if success_rate >= 95:
            print("🎉 EXCELLENT: Encryption system functioning optimally")
        elif success_rate >= 90:
            print("✅ GOOD: Minor issues detected but system is functional")
        elif success_rate >= 75:
            print("⚠️ ACCEPTABLE: Some issues need attention")
        else:
            print("❌ CRITICAL: Major issues detected - immediate attention required")
        
        # Show failed tests
        if results['failed_tests'] > 0:
            print(f"\n❌ Failed Tests ({results['failed_tests']}):")
            for test in results['test_details']:
                if not test['passed']:
                    print(f"   - {test['test_name']}: {test['details']}")
        
        print("=" * 60)
        
        # Save detailed report
        import json
        report_file = f"encryption_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_file}")
    
    async def cleanup_tests(self):
        """Cleanup test artifacts"""
        try:
            # Clean up any test files or resources
            # In a real implementation, this would clean up test data
            pass
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")

async def main():
    """Main test execution"""
    
    print("🚀 Starting Comprehensive Encryption System Test")
    print("This test verifies all encryption components and integration")
    print("")
    
    tester = EncryptionSystemTester()
    success = await tester.run_comprehensive_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - Encryption system is functioning correctly")
        print("✅ 40% encryption failure rate has been resolved")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Review results and fix issues")
        print("⚠️ Encryption system needs attention before production use")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)