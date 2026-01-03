#!/usr/bin/env python
"""Re-analyze document 828 with AI"""
import asyncio
import sqlite3
import json
import os
import sys
sys.path.insert(0, '.')

# Import the AI service
from app.src.services.dual_ai_service import dual_ai_service

async def reanalyze_document():
    # Get document text
    conn = sqlite3.connect('./legal_ai.db')
    cursor = conn.execute('SELECT id, text_content, file_name FROM documents WHERE id=?', ('904eb8cf-1349-42c5-bc7d-6f26fd95d287',))
    row = cursor.fetchone()

    if not row:
        print('Document not found')
        return

    doc_id, text_content, filename = row
    print(f'Re-analyzing document: {filename}')
    print(f'Text length: {len(text_content)} characters')

    # Re-analyze with AI
    print('Calling AI analysis...')
    try:
        analysis_result = await dual_ai_service.analyze_document(
            text_content,
            filename,
            include_operational_details=True,
            include_financial_details=True
        )

        print(f"Analysis method: {analysis_result.get('analysis_method', 'unknown')}")
        print(f"AI Source: {analysis_result.get('ai_source', 'unknown')}")
        print(f"Confidence: {analysis_result.get('confidence', 0)}")
        print(f"Document type: {analysis_result.get('document_type', 'unknown')}")

        # Update database
        summary = analysis_result.get('summary', '')
        doc_type = analysis_result.get('document_type', 'Unknown')
        parties = json.dumps(analysis_result.get('parties', []))
        analysis_data = json.dumps(analysis_result)

        conn.execute('''
            UPDATE documents
            SET summary=?, document_type=?, parties=?, analysis_data=?
            WHERE id=?
        ''', (summary, doc_type, parties, analysis_data, doc_id))
        conn.commit()

        print('Document updated successfully!')

        print('\n' + '='*80)
        print('DOCUMENT IDENTIFICATION')
        print('='*80)
        print(f"Type: {analysis_result.get('document_type', 'N/A')}")
        print(f"Case Caption: {analysis_result.get('case_caption', 'N/A')}")
        print(f"Case Number: {analysis_result.get('case_number', 'N/A')}")
        print(f"Court: {analysis_result.get('court', 'N/A')}")
        print(f"Document Number: {analysis_result.get('document_number', 'N/A')}")
        print(f"Filing Date: {analysis_result.get('filing_date', 'N/A')}")

        print('\n' + '='*80)
        print('COMPREHENSIVE SUMMARY')
        print('='*80)
        print(summary)

        print('\n' + '='*80)
        print('PLAIN ENGLISH SUMMARY')
        print('='*80)
        print(analysis_result.get('plain_english_summary', 'N/A'))

        print('\n' + '='*80)
        print('CORE DISPUTE')
        print('='*80)
        print(analysis_result.get('core_dispute', 'N/A'))

        print('\n' + '='*80)
        print('FILER')
        print('='*80)
        filer = analysis_result.get('filer', {})
        if filer:
            print(f"  Name: {filer.get('name', 'N/A')}")
            print(f"  Role: {filer.get('role', 'N/A')}")
            print(f"  Representing: {filer.get('representing', 'N/A')}")

        print('\n' + '='*80)
        print('OPPOSING PARTY')
        print('='*80)
        opposing = analysis_result.get('opposing_party', {})
        if opposing:
            print(f"  Name: {opposing.get('name', 'N/A')}")
            print(f"  Role: {opposing.get('role', 'N/A')}")
            print(f"  Their Claim: {opposing.get('their_claim', 'N/A')}")

        print('\n' + '='*80)
        print('KEY ARGUMENTS')
        print('='*80)
        for i, arg in enumerate(analysis_result.get('key_arguments', []), 1):
            if isinstance(arg, dict):
                print(f"\n  {i}. {arg.get('argument', 'N/A')}")
                print(f"     Supporting Facts: {arg.get('supporting_facts', 'N/A')}")
                print(f"     Legal Basis: {arg.get('legal_basis', 'N/A')}")
            else:
                print(f"  {i}. {arg}")

        print('\n' + '='*80)
        print('ALL FINANCIAL AMOUNTS')
        print('='*80)
        for amt in analysis_result.get('all_financial_amounts', []):
            if isinstance(amt, dict):
                print(f"  - {amt.get('amount', 'N/A')}: {amt.get('description', 'N/A')}")
                if amt.get('disputed'):
                    print(f"    DISPUTED: {amt.get('dispute_reason', 'N/A')}")
            else:
                print(f"  - {amt}")

        print('\n' + '='*80)
        print('INVOICES/EXHIBITS REFERENCED')
        print('='*80)
        for inv in analysis_result.get('invoices_or_exhibits', []):
            if isinstance(inv, dict):
                print(f"  - {inv.get('identifier', 'N/A')}: {inv.get('amount', '')} - {inv.get('relevance', '')}")
            else:
                print(f"  - {inv}")

        print('\n' + '='*80)
        print('ALL DATES')
        print('='*80)
        for date in analysis_result.get('all_dates', []):
            if isinstance(date, dict):
                print(f"  - {date.get('date', 'N/A')}: {date.get('event', 'N/A')}")
            else:
                print(f"  - {date}")

        print('\n' + '='*80)
        print('HEARING INFO')
        print('='*80)
        hearing = analysis_result.get('hearing_info', {})
        if hearing:
            print(f"  Date: {hearing.get('date', 'N/A')}")
            print(f"  Time: {hearing.get('time', 'N/A')}")
            print(f"  Location: {hearing.get('location', 'N/A')}")
            print(f"  Purpose: {hearing.get('purpose', 'N/A')}")

        print('\n' + '='*80)
        print('RELIEF REQUESTED')
        print('='*80)
        for relief in analysis_result.get('relief_requested', []):
            print(f"  - {relief}")

        print('\n' + '='*80)
        print('ATTORNEY INFO')
        print('='*80)
        atty = analysis_result.get('attorney_info', {})
        if atty:
            print(f"  Name: {atty.get('name', 'N/A')}")
            print(f"  Firm: {atty.get('firm', 'N/A')}")
            print(f"  Contact: {atty.get('contact', 'N/A')}")

    except Exception as e:
        print(f'Error during analysis: {e}')
        import traceback
        traceback.print_exc()

    conn.close()

if __name__ == '__main__':
    asyncio.run(reanalyze_document())
