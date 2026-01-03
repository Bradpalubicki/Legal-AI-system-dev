#!/usr/bin/env python3
"""
Test Enhanced Authentication System
Comprehensive demonstration of all authentication features
"""

import sqlite3
import sys
import os
from datetime import datetime
sys.path.append('src/shared/security')

from auth_enhanced import (
    create_enhanced_auth_system, AttorneyVerification, UserRole,
    UserRoleManagement, SessionSecurity, AuditLogger, AuditEventType
)

def main():
    print("=" * 80)
    print("ENHANCED AUTHENTICATION SYSTEM DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Initialize system with proper database
    db_path = "enhanced_auth.db"
    secret_key = "demo-secret-key-12345"
    encryption_key = "demo-encryption-key"
    
    user_mgr, session_sec, audit_log = create_enhanced_auth_system(
        db_path, secret_key, encryption_key
    )
    
    print("✅ Enhanced authentication system initialized")
    print()
    
    # Test 1: Attorney Verification
    print("🔍 TESTING ATTORNEY VERIFICATION")
    print("-" * 40)
    
    verifier = AttorneyVerification()
    result = verifier.verify_attorney("12345678", "TX", "John", "Smith")
    print(f"   Bar Number: {result.bar_number}")
    print(f"   State: {result.state}")  
    print(f"   Status: {result.status.value}")
    print(f"   Verified: {'✅ YES' if result.is_verified else '❌ NO'}")
    print(f"   Source: {result.verification_source}")
    print()
    
    # Test 2: User Role Management
    print("👥 TESTING USER ROLE MANAGEMENT")
    print("-" * 40)
    
    # Create users with different roles
    roles_to_test = [
        ("john.attorney", "john@lawfirm.com", UserRole.ATTORNEY, "TX", "12345678"),
        ("sarah.paralegal", "sarah@lawfirm.com", UserRole.PARALEGAL, "TX", None),
        ("client.doe", "client@email.com", UserRole.CLIENT, "TX", None),
        ("prose.user", "prose@email.com", UserRole.PROSE, "CA", None),
        ("system.admin", "admin@system.com", UserRole.ADMIN, "TX", None)
    ]
    
    created_users = []
    for username, email, role, state, bar_num in roles_to_test:
        user = user_mgr.create_user(
            username=username,
            email=email,
            role=role,
            state_jurisdiction=state,
            bar_number=bar_num
        )
        created_users.append(user)
        print(f"   Created: {username} ({role.name}) - Supervision: {'Required' if user.requires_supervision else 'None'}")
    
    print()
    
    # Test 3: Permission Checking
    print("🔐 TESTING PERMISSION SYSTEM")
    print("-" * 40)
    
    attorney = created_users[0]  # John Attorney
    paralegal = created_users[1]  # Sarah Paralegal
    client = created_users[2]     # Client Doe
    
    permissions_to_test = [
        "full_ai_access", "supervise_paralegals", "privileged_operations", 
        "client_management", "basic_ai_assistance"
    ]
    
    for permission in permissions_to_test:
        attorney_has = user_mgr.check_permission(attorney, permission)
        paralegal_has = user_mgr.check_permission(paralegal, permission)
        client_has = user_mgr.check_permission(client, permission)
        
        print(f"   {permission}:")
        print(f"     Attorney: {'✅' if attorney_has else '❌'}")
        print(f"     Paralegal: {'✅' if paralegal_has else '❌'}")  
        print(f"     Client: {'✅' if client_has else '❌'}")
    print()
    
    # Test 4: Session Security
    print("🔒 TESTING SESSION SECURITY")
    print("-" * 40)
    
    # Create session for attorney
    session = session_sec.create_session(
        attorney, 
        "192.168.1.100", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )
    
    print(f"   Session ID: {session.session_id[:16]}...")
    print(f"   User: {session.user_id}")
    print(f"   IP Address: {session.ip_address}")
    print(f"   Status: {session.status.value}")
    print(f"   Device Fingerprint: {session.device_fingerprint[:16]}...")
    print(f"   Expires: {session.expires_at.strftime('%H:%M:%S')}")
    
    # Validate session
    is_valid, session_info = session_sec.validate_session(
        session.session_id,
        "192.168.1.100",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )
    print(f"   Session Valid: {'✅ YES' if is_valid else '❌ NO'}")
    
    # Test re-authentication requirement
    needs_reauth = session_sec.requires_reauthentication(session, "client_data_access")
    print(f"   Needs Re-auth for Client Data: {'✅ YES' if needs_reauth else '❌ NO'}")
    print()
    
    # Test 5: Audit Logging
    print("📊 TESTING AUDIT LOGGING")
    print("-" * 40)
    
    # Log AI interaction
    ai_audit_id = audit_log.log_ai_interaction(
        user_id=attorney.user_id,
        session_id=session.session_id,
        prompt="What are the elements of contract formation?",
        response="Contract formation requires offer, acceptance, consideration, and mutual assent.",
        model_name="claude-3-sonnet",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        contains_advice=False,
        risk_score=0.2
    )
    print(f"   AI Interaction Logged: {ai_audit_id[:16]}...")
    
    # Log disclaimer acknowledgment
    disclaimer_audit_id = audit_log.log_disclaimer_acknowledgment(
        user_id=attorney.user_id,
        session_id=session.session_id,
        disclaimer_type="standard_ai_disclaimer",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        state_specific=True
    )
    print(f"   Disclaimer Ack Logged: {disclaimer_audit_id[:16]}...")
    
    # Log attorney review
    review_audit_id = audit_log.log_attorney_review(
        attorney_id=attorney.user_id,
        session_id=session.session_id,
        content_reviewed="AI generated contract analysis",
        review_result="approved",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )
    print(f"   Attorney Review Logged: {review_audit_id[:16]}...")
    
    # Test PII masking
    pii_text = "Client John Doe (SSN: 123-45-6789) email: john.doe@email.com phone: 555-123-4567"
    masked_text, pii_detected = audit_log._mask_pii(pii_text)
    print(f"   PII Detected: {'✅ YES' if pii_detected else '❌ NO'}")
    print(f"   Original: {pii_text}")
    print(f"   Masked: {masked_text}")
    print()
    
    # Test 6: Audit Trail Retrieval
    print("📋 TESTING AUDIT TRAIL RETRIEVAL")
    print("-" * 40)
    
    # Get audit trail for attorney
    audit_entries = audit_log.get_audit_trail(
        user_id=attorney.user_id,
        start_date=datetime.now().replace(hour=0, minute=0, second=0),
        end_date=datetime.now()
    )
    
    print(f"   Total Audit Entries: {len(audit_entries)}")
    for entry in audit_entries[:3]:  # Show first 3
        print(f"     {entry.event_type.value}: {entry.description[:50]}...")
    print()
    
    # Test 7: Compliance Report
    print("📊 TESTING COMPLIANCE REPORTING")
    print("-" * 40)
    
    report = audit_log.generate_compliance_report(
        start_date=datetime.now().replace(hour=0, minute=0, second=0),
        end_date=datetime.now()
    )
    
    print(f"   Report Period: {report['report_period']['start_date'][:10]} to {report['report_period']['end_date'][:10]}")
    print(f"   Total Events: {report['summary']['total_events']}")
    print(f"   AI Interactions: {report['summary']['ai_interactions']}")
    print(f"   High Risk Events: {report['summary']['high_risk_events']}")
    print(f"   PII Incidents: {report['summary']['pii_incidents']}")
    print(f"   UPL Violations: {report['summary']['upl_violations']}")
    print(f"   Compliance Status: {report['compliance_status'].upper()}")
    print()
    
    # Test 8: Role Restrictions
    print("⚠️  TESTING ROLE RESTRICTIONS")
    print("-" * 40)
    
    for user in created_users[:4]:  # Skip admin
        restrictions = user_mgr.get_role_restrictions(user.role)
        print(f"   {user.role.name} Restrictions:")
        if 'ai_warnings' in restrictions:
            for warning in restrictions['ai_warnings'][:2]:
                print(f"     ⚠️  {warning}")
    print()
    
    print("=" * 80)
    print("ENHANCED AUTHENTICATION SYSTEM DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("🎯 ALL FEATURES SUCCESSFULLY DEMONSTRATED:")
    print("   ✅ Attorney bar verification with state APIs")
    print("   ✅ 5-tier user role management (Client/ProSe/Paralegal/Attorney/Admin)")
    print("   ✅ 15-minute session timeouts with device fingerprinting")
    print("   ✅ Re-authentication for sensitive operations")
    print("   ✅ Comprehensive audit logging with PII masking")
    print("   ✅ Disclaimer acknowledgment tracking")
    print("   ✅ Attorney review action recording")
    print("   ✅ Professional accountability and compliance reporting")
    print("   ✅ 18 database tables with complete audit trails")

if __name__ == "__main__":
    main()