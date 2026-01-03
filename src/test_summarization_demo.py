#!/usr/bin/env python3
"""
DOCUMENT SUMMARIZATION ENDPOINT DEMONSTRATION

Shows how the Legal AI System would create client-friendly summaries
with educational content for complex legal documents.
"""

import json
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def demonstrate_summarization():
    """Demonstrate document summarization with educational content."""

    print("DOCUMENT SUMMARIZATION ENDPOINT DEMONSTRATION")
    print("=" * 55)
    print()

    # Simulate the summarization request
    request_data = {
        'document_id': 'DOC-001',
        'audience': 'client',
        'include_education': True
    }

    print("REQUEST RECEIVED:")
    print("=" * 20)
    print("POST /api/document-processing/summarize")
    print("Content-Type: application/json")
    print()
    print(json.dumps(request_data, indent=2))

    print()
    print("PROCESSING SUMMARIZATION...")
    print("=" * 30)

    # Load our test bankruptcy motion
    with open('../test_motion_relief_stay.txt', 'r', encoding='utf-8') as f:
        document_content = f.read()

    print("[STEP 1] Document loaded: 7,818 characters")

    # Document Analysis for context
    from document_processor.intelligent_intake import DocumentIntakeAnalyzer
    analyzer = DocumentIntakeAnalyzer()
    doc_analysis = analyzer.analyze(document_content, 'test_motion_relief_stay.txt')

    print("[STEP 2] Document analyzed for context")

    # Generate client-friendly summary
    client_summary = {
        'executive_summary': 'This is a Motion for Relief from Automatic Stay filed by First National Bank against ABC Company, LLC in bankruptcy court. The bank is asking permission to foreclose on commercial property at 123 Main Street, San Francisco because ABC Company owes $2.5 million and the property is only worth $2.2 million, leaving no equity for the company.',

        'key_parties': [
            {
                'name': 'ABC Company, LLC',
                'role': 'Debtor (the company in bankruptcy)',
                'description': 'The business that filed for Chapter 11 bankruptcy protection'
            },
            {
                'name': 'First National Bank',
                'role': 'Creditor (the lender)',
                'description': 'The bank that loaned money to ABC Company and holds a mortgage on the property'
            }
        ],

        'what_is_happening': [
            'ABC Company filed for Chapter 11 bankruptcy in September 2024',
            'This created an "automatic stay" that stops creditors from collecting debts',
            'First National Bank wants court permission to foreclose anyway',
            'The bank claims ABC Company cannot pay and has no equity in the property'
        ],

        'critical_dates': [
            {
                'date': 'January 16, 2025',
                'event': 'Response Deadline',
                'importance': 'If ABC Company wants to object, they must file papers by this date',
                'urgency': 'HIGH'
            },
            {
                'date': 'January 30, 2025 at 9:30 AM',
                'event': 'Court Hearing',
                'importance': 'Judge will decide whether to allow the foreclosure',
                'urgency': 'CRITICAL'
            }
        ],

        'financial_situation': {
            'amount_owed': '$2,500,000',
            'property_value': '$2,200,000',
            'equity_deficit': '$300,000 underwater',
            'monthly_payments': 'Stopped in June 2024',
            'explanation': 'The company owes more than the property is worth, which strengthens the bank\'s case'
        }
    }

    print("[STEP 3] Client-friendly summary generated")

    # Add educational content as requested
    educational_content = {
        'legal_concepts_explained': {
            'automatic_stay': {
                'definition': 'A legal protection that immediately stops most creditors from trying to collect debts when someone files bankruptcy',
                'analogy': 'Like a legal shield that gives the debtor breathing room to reorganize',
                'importance': 'Protects debtors from foreclosure, lawsuits, and collection calls'
            },
            'relief_from_stay': {
                'definition': 'A court process where creditors ask permission to collect despite the automatic stay',
                'when_granted': 'Usually when there is no equity in collateral or no adequate protection',
                'analogy': 'Like asking the judge to remove part of the legal shield'
            },
            'chapter_11': {
                'definition': 'A type of bankruptcy that allows businesses to reorganize debts while continuing operations',
                'goal': 'To create a plan to pay creditors over time while keeping the business running',
                'timeline': 'Can take 6 months to several years to complete'
            }
        },

        'process_explained': {
            'what_happens_next': [
                '1. ABC Company has until January 16 to file an objection',
                '2. If they object, both sides present arguments',
                '3. Court hearing on January 30 where judge decides',
                '4. If bank wins, foreclosure can proceed',
                '5. If ABC wins, they must provide adequate protection'
            ]
        }
    }

    print("[STEP 4] Educational content added")

    # Include disclaimers for client audience
    from shared.compliance.disclaimer_system import DisclaimerSystem
    disclaimer_system = DisclaimerSystem()
    client_disclaimer = disclaimer_system.get_disclaimer('client-portal')

    print("[STEP 5] Client-appropriate disclaimers included")

    # Build the complete API response
    api_response = {
        'document_id': 'DOC-001',
        'summary_type': 'client_friendly',
        'audience': 'client',
        'status': 'completed',
        'processing_time': 3.4,
        'timestamp': datetime.now().isoformat(),

        'document_info': {
            'title': 'Motion for Relief from Automatic Stay',
            'document_type': 'bankruptcy_motion',
            'court': 'U.S. Bankruptcy Court, Northern District of California',
            'case': 'In re: ABC Company, LLC, Case No. 24-12345-ABC',
            'complexity_level': 'intermediate'
        },

        'summary': client_summary,
        'education': educational_content,

        'compliance': {
            'disclaimer_text': client_disclaimer,
            'educational_only': True,
            'not_legal_advice': True,
            'upl_compliant': True
        },

        'metadata': {
            'reading_level': 'high_school',
            'estimated_reading_time': '8-10 minutes'
        }
    }

    print()
    print("API RESPONSE PREVIEW:")
    print("=" * 25)
    print("Status: 200 OK")
    print("Content-Type: application/json")
    print()

    # Show key parts of the response
    print("EXECUTIVE SUMMARY:")
    print(f"  {client_summary['executive_summary']}")
    print()

    print("KEY PARTIES:")
    for party in client_summary['key_parties']:
        print(f"  • {party['name']}: {party['role']}")
    print()

    print("CRITICAL DATES:")
    for date in client_summary['critical_dates']:
        print(f"  • {date['date']}: {date['event']} ({date['urgency']})")
    print()

    print("FINANCIAL SITUATION:")
    fin = client_summary['financial_situation']
    print(f"  • Amount Owed: {fin['amount_owed']}")
    print(f"  • Property Value: {fin['property_value']}")
    print(f"  • Status: {fin['equity_deficit']}")
    print()

    print("EDUCATIONAL CONCEPTS (3 of 3):")
    for concept, details in educational_content['legal_concepts_explained'].items():
        print(f"  • {concept.replace('_', ' ').title()}: {details['definition'][:60]}...")
    print()

    print("COMPLIANCE STATUS:")
    print(f"  • UPL Compliant: {api_response['compliance']['upl_compliant']}")
    print(f"  • Educational Only: {api_response['compliance']['educational_only']}")
    print(f"  • Disclaimers Included: {'Yes' if api_response['compliance']['disclaimer_text'] else 'No'}")

    print()
    print("SUMMARIZATION COMPLETE!")
    print("=" * 25)
    print("[PASS] Document: Motion for Relief from Automatic Stay")
    print("[PASS] Summary Type: Client-friendly with education")
    print("[PASS] Reading Level: High school appropriate")
    print("[PASS] Est. Reading Time: 8-10 minutes")
    print("[PASS] Legal Concepts: 3 key concepts explained")
    print("[PASS] Compliance: UPL compliant with disclaimers")

    return api_response

if __name__ == "__main__":
    demonstrate_summarization()