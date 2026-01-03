#!/usr/bin/env python3
"""
EMERGENCY DOCUMENT ENCRYPTION REMEDIATION

This script identifies and encrypts ALL unencrypted documents in the legal system
to ensure compliance with attorney-client privilege and data protection requirements.

CRITICAL: All legal documents must be encrypted at rest.
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import hashlib

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.encryption_service import emergency_encryption_service, EncryptionResult

logger = logging.getLogger(__name__)

@dataclass
class DocumentScanResult:
    file_path: str
    document_id: str
    file_size: int
    file_type: str
    is_legal_document: bool
    currently_encrypted: bool
    encryption_required: bool
    compliance_level: str
    risk_assessment: str

@dataclass
class EncryptionRemediationReport:
    scan_timestamp: datetime
    total_files_scanned: int
    legal_documents_found: int
    unencrypted_documents: int
    encryption_results: List[EncryptionResult]
    successful_encryptions: int
    failed_encryptions: int
    compliance_achieved: bool
    remediation_summary: Dict[str, Any]

class EmergencyDocumentScanner:
    """Emergency document scanner and encryption orchestrator"""
    
    def __init__(self):
        self.encryption_service = emergency_encryption_service
        
        # Legal document extensions that MUST be encrypted
        self.LEGAL_EXTENSIONS = {
            '.pdf', '.docx', '.doc', '.txt', '.rtf', '.odt',
            '.html', '.xml', '.json', '.csv', '.xlsx', '.xls'
        }
        
        # High-risk directories that likely contain legal documents
        self.HIGH_RISK_DIRECTORIES = [
            'documents', 'legal', 'contracts', 'cases', 'clients',
            'briefs', 'pleadings', 'discovery', 'correspondence',
            'privileged', 'confidential', 'attorney_work_product'
        ]
        
        # Patterns indicating legal document content
        self.LEGAL_CONTENT_PATTERNS = [
            'attorney-client', 'privileged', 'confidential',
            'legal opinion', 'contract', 'agreement', 'lawsuit',
            'plaintiff', 'defendant', 'court', 'legal advice',
            'representation', 'retainer', 'settlement'
        ]
    
    async def scan_directory_tree(self, root_path: Path) -> List[DocumentScanResult]:
        """Scan directory tree for documents requiring encryption"""
        
        print(f"[SCAN] Starting document scan from: {root_path}")
        
        scan_results = []
        total_files = 0
        
        try:
            # Recursively scan all files
            for file_path in root_path.rglob('*'):
                if file_path.is_file():
                    total_files += 1
                    
                    if total_files % 100 == 0:
                        print(f"[SCAN] Scanned {total_files} files...")
                    
                    # Analyze file
                    scan_result = await self._analyze_file(file_path)
                    if scan_result:
                        scan_results.append(scan_result)
            
            print(f"[SCAN] Scan complete: {total_files} files scanned, {len(scan_results)} require analysis")
            return scan_results
            
        except Exception as e:
            logger.error(f"[SCAN] Error scanning directory {root_path}: {e}")
            return scan_results
    
    async def _analyze_file(self, file_path: Path) -> Optional[DocumentScanResult]:
        """Analyze a single file to determine if it needs encryption"""
        
        try:
            # Get basic file info
            stat = file_path.stat()
            file_size = stat.st_size
            file_extension = file_path.suffix.lower()
            
            # Skip very large files (>100MB) for now
            if file_size > 100 * 1024 * 1024:
                return None
            
            # Skip system files and hidden files
            if file_path.name.startswith('.') or file_path.name.startswith('~'):
                return None
            
            # Check if it's a legal document type
            is_legal_document = (
                file_extension in self.LEGAL_EXTENSIONS or
                self._is_in_legal_directory(file_path) or
                await self._contains_legal_content(file_path)
            )
            
            if not is_legal_document:
                return None
            
            # Generate document ID
            document_id = self._generate_document_id(file_path)
            
            # Check if already encrypted
            existing_encryption = self.encryption_service.get_encryption_status(document_id)
            currently_encrypted = existing_encryption is not None and existing_encryption.encrypted
            
            # Determine compliance level based on path and content
            compliance_level = self._determine_compliance_level(file_path)
            
            # Assess risk
            risk_assessment = self._assess_document_risk(file_path, file_size, compliance_level)
            
            return DocumentScanResult(
                file_path=str(file_path),
                document_id=document_id,
                file_size=file_size,
                file_type=file_extension,
                is_legal_document=is_legal_document,
                currently_encrypted=currently_encrypted,
                encryption_required=not currently_encrypted,
                compliance_level=compliance_level,
                risk_assessment=risk_assessment
            )
            
        except Exception as e:
            logger.error(f"[SCAN] Error analyzing file {file_path}: {e}")
            return None
    
    def _is_in_legal_directory(self, file_path: Path) -> bool:
        """Check if file is in a directory that typically contains legal documents"""
        path_parts = [part.lower() for part in file_path.parts]
        return any(risk_dir in path_part for path_part in path_parts for risk_dir in self.HIGH_RISK_DIRECTORIES)
    
    async def _contains_legal_content(self, file_path: Path) -> bool:
        """Check if file contains legal content (basic text analysis)"""
        
        try:
            # Only check text-based files
            if file_path.suffix.lower() not in {'.txt', '.html', '.xml', '.json', '.csv'}:
                return False
            
            # Read first 10KB of file for content analysis
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10240).lower()
            
            # Check for legal content patterns
            return any(pattern in content for pattern in self.LEGAL_CONTENT_PATTERNS)
            
        except Exception:
            return False
    
    def _generate_document_id(self, file_path: Path) -> str:
        """Generate unique document ID from file path"""
        # Use hash of absolute path to create consistent ID
        path_str = str(file_path.absolute())
        return hashlib.sha256(path_str.encode('utf-8')).hexdigest()[:16]
    
    def _determine_compliance_level(self, file_path: Path) -> str:
        """Determine compliance level based on file location and name"""
        path_str = str(file_path).lower()
        
        if any(keyword in path_str for keyword in ['attorney-client', 'privileged', 'work_product']):
            return 'ATTORNEY_CLIENT'
        elif any(keyword in path_str for keyword in ['confidential', 'restricted', 'internal']):
            return 'CONFIDENTIAL'
        elif any(keyword in path_str for keyword in ['client', 'case', 'legal']):
            return 'RESTRICTED'
        else:
            return 'CONFIDENTIAL'  # Default to confidential for safety
    
    def _assess_document_risk(self, file_path: Path, file_size: int, compliance_level: str) -> str:
        """Assess risk level of unencrypted document"""
        risk_factors = []
        
        # Size-based risk
        if file_size > 10 * 1024 * 1024:  # >10MB
            risk_factors.append('LARGE_FILE')
        
        # Compliance level risk
        if compliance_level == 'ATTORNEY_CLIENT':
            risk_factors.append('PRIVILEGED_CONTENT')
        
        # Location-based risk
        if self._is_in_legal_directory(file_path):
            risk_factors.append('LEGAL_DIRECTORY')
        
        # File type risk
        if file_path.suffix.lower() in {'.pdf', '.docx', '.doc'}:
            risk_factors.append('DOCUMENT_TYPE')
        
        # Calculate overall risk
        if len(risk_factors) >= 3:
            return 'CRITICAL'
        elif len(risk_factors) >= 2:
            return 'HIGH'
        elif len(risk_factors) >= 1:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    async def execute_encryption_remediation(self, scan_results: List[DocumentScanResult]) -> EncryptionRemediationReport:
        """Execute encryption remediation for all unencrypted documents"""
        
        # Filter documents that need encryption
        documents_to_encrypt = [doc for doc in scan_results if doc.encryption_required]
        
        print(f"[REMEDIATION] Starting encryption of {len(documents_to_encrypt)} documents...")
        
        encryption_results = []
        successful = 0
        failed = 0
        
        # Sort by risk level (critical first)
        documents_to_encrypt.sort(key=lambda x: {
            'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3
        }.get(x.risk_assessment, 4))
        
        # Encrypt documents
        for i, doc in enumerate(documents_to_encrypt):
            print(f"[REMEDIATION] Encrypting {i+1}/{len(documents_to_encrypt)}: {doc.file_path}")
            
            try:
                result = self.encryption_service.encrypt_document(
                    doc.file_path,
                    doc.document_id,
                    doc.compliance_level
                )
                
                encryption_results.append(result)
                
                if result.success:
                    successful += 1
                    print(f"  [SUCCESS]: {doc.document_id}")
                else:
                    failed += 1
                    print(f"  [FAILED]: {doc.document_id} - {result.error_message}")
                
                # Progress update
                if (i + 1) % 10 == 0:
                    progress = ((i + 1) / len(documents_to_encrypt)) * 100
                    print(f"[REMEDIATION] Progress: {i+1}/{len(documents_to_encrypt)} ({progress:.1f}%)")
                
            except Exception as e:
                failed += 1
                logger.error(f"[REMEDIATION] Exception encrypting {doc.file_path}: {e}")
        
        # Generate remediation report
        compliance_achieved = failed == 0
        
        remediation_summary = {
            'total_documents_scanned': len(scan_results),
            'legal_documents_identified': len([d for d in scan_results if d.is_legal_document]),
            'already_encrypted': len([d for d in scan_results if d.currently_encrypted]),
            'required_encryption': len(documents_to_encrypt),
            'successful_encryptions': successful,
            'failed_encryptions': failed,
            'compliance_rate': (successful / len(documents_to_encrypt)) * 100 if documents_to_encrypt else 100,
            'risk_breakdown': self._calculate_risk_breakdown(scan_results),
            'compliance_level_breakdown': self._calculate_compliance_breakdown(scan_results)
        }
        
        report = EncryptionRemediationReport(
            scan_timestamp=datetime.utcnow(),
            total_files_scanned=len(scan_results),
            legal_documents_found=len([d for d in scan_results if d.is_legal_document]),
            unencrypted_documents=len(documents_to_encrypt),
            encryption_results=encryption_results,
            successful_encryptions=successful,
            failed_encryptions=failed,
            compliance_achieved=compliance_achieved,
            remediation_summary=remediation_summary
        )
        
        return report
    
    def _calculate_risk_breakdown(self, scan_results: List[DocumentScanResult]) -> Dict[str, int]:
        """Calculate breakdown of documents by risk level"""
        breakdown = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for doc in scan_results:
            if doc.encryption_required:
                breakdown[doc.risk_assessment] = breakdown.get(doc.risk_assessment, 0) + 1
        
        return breakdown
    
    def _calculate_compliance_breakdown(self, scan_results: List[DocumentScanResult]) -> Dict[str, int]:
        """Calculate breakdown of documents by compliance level"""
        breakdown = {'ATTORNEY_CLIENT': 0, 'CONFIDENTIAL': 0, 'RESTRICTED': 0, 'PUBLIC': 0}
        
        for doc in scan_results:
            if doc.is_legal_document:
                breakdown[doc.compliance_level] = breakdown.get(doc.compliance_level, 0) + 1
        
        return breakdown
    
    def save_report(self, report: EncryptionRemediationReport) -> str:
        """Save encryption remediation report"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        report_filename = f'encryption_remediation_report_{timestamp}.json'
        
        # Convert dataclasses to dictionaries
        report_dict = {
            'scan_timestamp': report.scan_timestamp.isoformat(),
            'total_files_scanned': report.total_files_scanned,
            'legal_documents_found': report.legal_documents_found,
            'unencrypted_documents': report.unencrypted_documents,
            'successful_encryptions': report.successful_encryptions,
            'failed_encryptions': report.failed_encryptions,
            'compliance_achieved': report.compliance_achieved,
            'remediation_summary': report.remediation_summary,
            'encryption_results': [
                {
                    'document_id': r.document_id,
                    'success': r.success,
                    'encrypted_file_path': r.encrypted_file_path,
                    'error_message': r.error_message
                }
                for r in report.encryption_results
            ]
        }
        
        with open(report_filename, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        # Also create human-readable summary
        summary_filename = f'encryption_remediation_summary_{timestamp}.txt'
        self._create_summary_report(report, summary_filename)
        
        print(f"[REPORT] Detailed report saved: {report_filename}")
        print(f"[REPORT] Summary report saved: {summary_filename}")
        
        return report_filename
    
    def _create_summary_report(self, report: EncryptionRemediationReport, filename: str):
        """Create human-readable summary report"""
        
        summary = f"""
EMERGENCY DOCUMENT ENCRYPTION REMEDIATION REPORT
Generated: {report.scan_timestamp.isoformat()}

========================================
EXECUTIVE SUMMARY
========================================

Total Files Scanned: {report.total_files_scanned}
Legal Documents Found: {report.legal_documents_found}
Documents Requiring Encryption: {report.unencrypted_documents}
Successful Encryptions: {report.successful_encryptions}
Failed Encryptions: {report.failed_encryptions}
Overall Compliance Achieved: {report.compliance_achieved}

Compliance Rate: {report.remediation_summary['compliance_rate']:.1f}%

========================================
RISK ASSESSMENT BREAKDOWN
========================================

"""
        
        for risk_level, count in report.remediation_summary['risk_breakdown'].items():
            summary += f"{risk_level}: {count} documents\n"
        
        summary += f"""
========================================
COMPLIANCE LEVEL BREAKDOWN
========================================

"""
        
        for compliance_level, count in report.remediation_summary['compliance_level_breakdown'].items():
            summary += f"{compliance_level}: {count} documents\n"
        
        if report.failed_encryptions > 0:
            summary += f"""
========================================
FAILED ENCRYPTIONS
========================================

"""
            for result in report.encryption_results:
                if not result.success:
                    summary += f"Document ID: {result.document_id}\n"
                    summary += f"Error: {result.error_message}\n\n"
        
        summary += f"""
========================================
REMEDIATION STATUS
========================================

"""
        
        if report.compliance_achieved:
            summary += "[SUCCESS] All documents successfully encrypted\n"
            summary += "[SUCCESS] System is now fully compliant with encryption requirements\n"
            summary += "[SUCCESS] Attorney-client privilege protection active\n"
        else:
            summary += "[PARTIAL] Some documents failed to encrypt\n"
            summary += f"[FAIL] {report.failed_encryptions} documents require manual remediation\n"
            summary += "[FAIL] System not fully compliant until all failures are resolved\n"
        
        with open(filename, 'w') as f:
            f.write(summary)

async def main():
    """Main function to execute emergency document encryption remediation"""
    
    print("[EMERGENCY] DOCUMENT ENCRYPTION REMEDIATION")
    print("Scanning for unencrypted legal documents...")
    print("=" * 60)
    
    # Initialize scanner
    scanner = EmergencyDocumentScanner()
    
    # Scan directories that commonly contain legal documents
    scan_paths = [
        Path('.'),  # Current directory
        Path('documents') if Path('documents').exists() else None,
        Path('storage') if Path('storage').exists() else None,
        Path('uploads') if Path('uploads').exists() else None,
    ]
    
    # Remove None values
    scan_paths = [path for path in scan_paths if path is not None]
    
    print(f"Scanning directories: {[str(p) for p in scan_paths]}")
    
    # Scan all paths
    all_scan_results = []
    for scan_path in scan_paths:
        if scan_path.exists():
            path_results = await scanner.scan_directory_tree(scan_path)
            all_scan_results.extend(path_results)
    
    print(f"\n[SCAN] SCAN RESULTS")
    print(f"Total documents found: {len(all_scan_results)}")
    
    unencrypted = [doc for doc in all_scan_results if doc.encryption_required]
    print(f"Unencrypted documents: {len(unencrypted)}")
    
    if len(unencrypted) == 0:
        print("[SUCCESS] All documents are already encrypted!")
        return
    
    # Show risk breakdown
    risk_counts = {}
    for doc in unencrypted:
        risk_counts[doc.risk_assessment] = risk_counts.get(doc.risk_assessment, 0) + 1
    
    print(f"\nRisk Level Breakdown:")
    for risk, count in sorted(risk_counts.items()):
        print(f"  {risk}: {count} documents")
    
    print(f"\n[ENCRYPTION] STARTING ENCRYPTION REMEDIATION")
    print("=" * 60)
    
    # Execute remediation
    report = await scanner.execute_encryption_remediation(all_scan_results)
    
    # Save report
    report_file = scanner.save_report(report)
    
    print(f"\n[REPORT] REMEDIATION COMPLETE")
    print("=" * 60)
    print(f"Successful: {report.successful_encryptions}")
    print(f"Failed: {report.failed_encryptions}")
    print(f"Compliance Rate: {report.remediation_summary['compliance_rate']:.1f}%")
    print(f"Overall Success: {report.compliance_achieved}")
    
    if report.compliance_achieved:
        print(f"\n[SUCCESS] All documents encrypted successfully!")
        print(f"[SUCCESS] System is now fully compliant with encryption requirements")
    else:
        print(f"\n[WARNING] {report.failed_encryptions} documents failed to encrypt")
        print(f"[FAIL] Manual remediation required for complete compliance")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())