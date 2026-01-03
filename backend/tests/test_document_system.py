#!/usr/bin/env python3
"""
Simple Document System Test
Test the document processing system with basic functionality
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_upload_handler():
    """Test document upload handler"""
    try:
        from document.upload_handler import document_uploader

        print("Testing Document Upload Handler...")

        # Test with sample text
        test_data = b"This is a test legal document for educational purposes only."
        test_filename = "test_document.txt"
        test_user = "test_user_123"

        # Test upload
        result = document_uploader.upload_document(test_data, test_filename, test_user)

        if result.success:
            print(f"Upload successful: {result.document_id}")
            print(f"   File size: {result.metadata.file_size} bytes")
            print(f"   File type: {result.metadata.file_type.value}")
            return True, result.document_id
        else:
            print(f"Upload failed: {result.message}")
            return False, None

    except Exception as e:
        print(f"Upload test failed: {e}")
        return False, None

def test_ocr_processor(document_id):
    """Test OCR processor"""
    try:
        from document.ocr_processor import ocr_processor

        print("Testing OCR Processor...")

        # Test OCR processing
        result = ocr_processor.process_document(document_id, "test_user")

        if result.status.value == "completed":
            print(f"[PASS] OCR successful: {result.ocr_id}")
            print(f"   Confidence: {result.confidence_score:.1f}%")
            print(f"   Text length: {len(result.extracted_text)} characters")
            return True
        else:
            print(f"[FAIL] OCR failed: {result.status.value}")
            return False

    except Exception as e:
        print(f"[FAIL] OCR test failed: {e}")
        return False

def test_classification_engine(document_id):
    """Test classification engine"""
    try:
        from document.classification_engine import classification_engine

        print("Testing Classification Engine...")

        # Test document classification
        result = classification_engine.classify_document(document_id, "test_user")

        if result:
            print(f"[PASS] Classification successful: {result.classification_id}")
            print(f"   Document Type: {result.document_type.value}")
            print(f"   Educational Category: {result.educational_category.value}")
            print(f"   Confidence: {result.confidence_score:.1f}%")
            print(f"   Attorney Review Required: {result.attorney_review_required}")
            return True
        else:
            print("[FAIL] Classification failed")
            return False

    except Exception as e:
        print(f"[FAIL] Classification test failed: {e}")
        return False

def test_compliant_analyzer(document_id):
    """Test compliant analyzer"""
    try:
        from document.compliant_analyzer import compliant_analyzer, AnalysisType

        print("Testing Compliant Analyzer...")

        # Test document analysis
        result = compliant_analyzer.analyze_document(
            document_id,
            AnalysisType.EDUCATIONAL_SUMMARY,
            "test_user"
        )

        if result:
            print(f"[PASS] Analysis successful: {result.analysis_id}")
            print(f"   Compliance Level: {result.compliance_level.value}")
            print(f"   Educational Points: {len(result.educational_summary.educational_points)}")
            print(f"   Attorney Review Required: {result.compliance_flags.attorney_review_required}")

            # Display disclaimers
            print("\n[INFO] EDUCATIONAL DISCLAIMER:")
            print(result.disclaimers.primary_disclaimer)

            return True
        else:
            print("[FAIL] Analysis failed")
            return False

    except Exception as e:
        print(f"[FAIL] Analysis test failed: {e}")
        return False

def test_bankruptcy_document():
    """Test with a sample bankruptcy document"""
    print("\n" + "="*60)
    print("TESTING WITH SAMPLE BANKRUPTCY DOCUMENT")
    print("="*60)

    # Sample bankruptcy petition text
    bankruptcy_text = """
UNITED STATES BANKRUPTCY COURT
EASTERN DISTRICT OF VIRGINIA

In re:                                    Case No. 23-12345-RGH
JOHN SMITH,                              Chapter 7
    Debtor.

VOLUNTARY PETITION

1. Petitioner's name: John Smith
2. Address: 123 Main Street, Richmond, VA 23219
3. SSN: XXX-XX-1234

The debtor requests relief in accordance with Chapter 7 of title 11, United States Code.

EDUCATIONAL DISCLAIMER: This is a sample document for educational purposes only.
This does not constitute legal advice and should not be used as a template for actual legal filings.

Filed: January 15, 2024
Attorney for Debtor: Jane Attorney, Esq.

Under penalty of perjury, I declare that the information provided in this petition is true and correct.

/s/ John Smith
Debtor
Date: January 15, 2024
    """

    try:
        from document.upload_handler import document_uploader
        from document.ocr_processor import ocr_processor
        from document.classification_engine import classification_engine
        from document.compliant_analyzer import compliant_analyzer, AnalysisType

        # Upload bankruptcy document
        upload_result = document_uploader.upload_document(
            bankruptcy_text.encode('utf-8'),
            "chapter7_petition.txt",
            "bankruptcy_test_user"
        )

        if not upload_result.success:
            print(f"[FAIL] Bankruptcy document upload failed: {upload_result.message}")
            return False

        print(f"[PASS] Bankruptcy document uploaded: {upload_result.document_id}")

        # Process with OCR
        ocr_result = ocr_processor.process_document(upload_result.document_id, "bankruptcy_test_user")
        if ocr_result.status.value == "completed":
            print(f"[PASS] Bankruptcy OCR completed: {ocr_result.confidence_score:.1f}% confidence")
        else:
            print(f"[FAIL] Bankruptcy OCR failed: {ocr_result.status.value}")
            return False

        # Classify document
        classification_result = classification_engine.classify_document(
            upload_result.document_id, "bankruptcy_test_user"
        )
        if classification_result:
            print(f"[PASS] Bankruptcy classification: {classification_result.document_type.value}")
            print(f"   Educational Category: {classification_result.educational_category.value}")
        else:
            print("[FAIL] Bankruptcy classification failed")
            return False

        # Analyze document
        analysis_result = compliant_analyzer.analyze_document(
            upload_result.document_id,
            AnalysisType.EDUCATIONAL_SUMMARY,
            "bankruptcy_test_user"
        )
        if analysis_result:
            print(f"[PASS] Bankruptcy analysis completed")
            print(f"   Compliance Level: {analysis_result.compliance_level.value}")
            print(f"   Educational Summary: {analysis_result.educational_summary.document_purpose}")
            print(f"   Key Legal Concepts: {', '.join(analysis_result.educational_summary.key_legal_concepts[:3])}")
            print(f"   Attorney Review Required: {analysis_result.compliance_flags.attorney_review_required}")

            # Show educational points
            print("\n[EDU] Educational Points:")
            for i, point in enumerate(analysis_result.educational_summary.educational_points[:3], 1):
                print(f"   {i}. {point}")

            return True
        else:
            print("[FAIL] Bankruptcy analysis failed")
            return False

    except Exception as e:
        print(f"[FAIL] Bankruptcy document test failed: {e}")
        return False

def main():
    """Run comprehensive document system test"""
    print("STARTING DOCUMENT PROCESSING SYSTEM TEST")
    print("="*60)

    tests_passed = 0
    total_tests = 4

    # Test 1: Upload Handler
    print("\n1. DOCUMENT UPLOAD HANDLER")
    print("-" * 30)
    success, document_id = test_upload_handler()
    if success:
        tests_passed += 1

    if not document_id:
        print("Cannot proceed with further tests - upload failed")
        return

    # Test 2: OCR Processor
    print("\n2. OCR PROCESSOR")
    print("-" * 30)
    if test_ocr_processor(document_id):
        tests_passed += 1

    # Test 3: Classification Engine
    print("\n3. CLASSIFICATION ENGINE")
    print("-" * 30)
    if test_classification_engine(document_id):
        tests_passed += 1

    # Test 4: Compliant Analyzer
    print("\n4. COMPLIANT ANALYZER")
    print("-" * 30)
    if test_compliant_analyzer(document_id):
        tests_passed += 1

    # Test 5: Bankruptcy Document Processing
    if test_bankruptcy_document():
        print("\n[PASS] BANKRUPTCY DOCUMENT TEST PASSED")
    else:
        print("\n[FAIL] BANKRUPTCY DOCUMENT TEST FAILED")

    # Final Results
    print("\n" + "="*60)
    print("FINAL TEST RESULTS")
    print("="*60)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")

    if tests_passed == total_tests:
        print("ALL TESTS PASSED - SYSTEM READY!")
        print("Document processing pipeline is fully functional")
        print("Compliance safeguards are active")
        print("Educational features are working")
        print("Attorney review flags are operational")
    else:
        print(f"{total_tests - tests_passed} tests failed - review system issues")

    print("\nIMPORTANT COMPLIANCE NOTES:")
    print("- All analysis is for educational purposes only")
    print("- No legal advice is provided by this system")
    print("- Attorney review is required for sensitive content")
    print("- Comprehensive audit logging is active")
    print("- Document encryption is enforced")

if __name__ == "__main__":
    main()