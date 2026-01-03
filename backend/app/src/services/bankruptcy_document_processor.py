"""
Bankruptcy Document Processor - Specialized extraction for bankruptcy legal documents

This processor is designed to extract ALL financial and legal data from bankruptcy documents:
- Monetary amounts ($5,033,301.46, settlement premiums, claim amounts)
- Ownership structures (voting control vs economic ownership percentages)
- Share distributions and equity structures
- Legal issues (case law violations, statutory references)
- Claims and settlements
- Precedent violations (non-consensual third-party releases, etc.)

This is NOT a generic text parser - it understands bankruptcy legal document structure.
"""

import re
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BankruptcyDocumentProcessor:
    """
    Comprehensive bankruptcy document processor that extracts ALL financial and legal data
    """

    def __init__(self):
        # THESE PATTERNS MUST CATCH EVERYTHING
        self.money_pattern = re.compile(
            r'\$[\d]{1,3}(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:million|Million|MILLION|M|m|billion|Billion|B|b))?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars|DOLLARS|USD)',
            re.IGNORECASE
        )

        self.percentage_pattern = re.compile(
            r'(\d{1,3}(?:\.\d{1,2})?)\s*(?:%|percent|PERCENT)',
            re.IGNORECASE
        )

        # Enhanced pattern to capture shares in multiple formats:
        # - "10,000 shares" (basic format)
        # - "* 1,000 voting shares (Class A)" (bulleted with type)
        # - "9,000 non-voting shares" (type before shares)
        self.shares_pattern = re.compile(
            r'(?:[\*\-\•]\s*)?(\d{1,6}(?:,\d{3})*)\s+(?:voting|non-voting|nonvoting|common|preferred|Class\s+[A-Z])?\s*shares?',
            re.IGNORECASE
        )

        self.claim_pattern = re.compile(
            r'(?:claim|proof of claim|POC|secured claim|unsecured claim).*?\$[\d,]+(?:\.\d{2})?',
            re.IGNORECASE | re.DOTALL
        )

        # Case number patterns - bankruptcy and civil
        self.case_number_pattern = re.compile(
            r'(?:Case\s*(?:No\.?|Number|#)?:?\s*|No\.\s*)(\d{1,2}[:-]\d{2,5}[-‐–]\w{1,5}[-‐–]?\w{0,5}(?:[-‐–]\w+)?)',
            re.IGNORECASE
        )

        # Civil case pattern (e.g., 7:24-cv-00927-D-RN)
        self.civil_case_pattern = re.compile(
            r'\b(\d{1,2}:\d{2}-cv-\d{4,5}(?:-[A-Z]{1,3}){0,2})\b',
            re.IGNORECASE
        )

        # ECF/Docket reference patterns
        self.ecf_pattern = re.compile(
            r'(?:ECF|Doc(?:ument)?|Dkt\.?|Docket)\s*(?:No\.?|#|Number)?\s*(\d+)',
            re.IGNORECASE
        )

        # Invoice pattern
        self.invoice_pattern = re.compile(
            r'(?:Invoice|Inv\.?|Bill)\s*(?:No\.?|#|Number)?\s*:?\s*([A-Z0-9-]+)',
            re.IGNORECASE
        )

        # Attorney/law firm patterns
        self.attorney_pattern = re.compile(
            r'(?:(?:Attorney|Counsel|Esq\.?|Esquire|Law\s*(?:Firm|Office|Group|Offices))[:\s]+)?([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)(?:,?\s*(?:Esq\.?|Esquire|P\.?C\.?|LLP|PLLC|LLC))',
            re.IGNORECASE
        )

        # Bar number pattern
        self.bar_number_pattern = re.compile(
            r'(?:Bar\s*(?:No\.?|#|Number)|State\s*Bar)[:\s]*(\d+)',
            re.IGNORECASE
        )

    def extract_all_financial_data(self, text: str) -> Dict[str, Any]:
        """
        THIS METHOD MUST RETURN EVERY SINGLE FINANCIAL NUMBER

        Args:
            text: Full document text

        Returns:
            Dictionary with all financial data categorized by type
        """
        results = {
            'monetary_amounts': [],
            'percentages': [],
            'shares': [],
            'claims': [],
            'settlements': [],
            'extraction_metadata': {
                'extracted_at': datetime.now().isoformat(),
                'total_monetary_amounts': 0,
                'total_percentages': 0,
                'total_shares': 0,
                'total_claims': 0,
                'total_settlements': 0
            }
        }

        # Extract ALL money amounts with context
        for match in self.money_pattern.finditer(text):
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]

            amount_str = match.group()
            # Convert to actual number
            amount = self.parse_money(amount_str)

            results['monetary_amounts'].append({
                'raw': amount_str,
                'amount': amount,
                'context': context.strip(),
                'position': match.start()
            })

        # Extract ALL percentages with ownership context
        for match in self.percentage_pattern.finditer(text):
            start = max(0, match.start() - 150)
            end = min(len(text), match.end() + 150)
            context = text[start:end]

            # Determine what this percentage represents
            if any(word in context.lower() for word in ['voting', 'ownership', 'control', 'equity', 'shares']):
                percentage = float(match.group(1))
                owner = self.extract_owner_from_context(context)

                results['percentages'].append({
                    'value': percentage,
                    'type': self.determine_percentage_type(context),
                    'entity': owner,
                    'context': context.strip()
                })

        # Extract share distributions
        for match in self.shares_pattern.finditer(text):
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]

            shares = self.parse_number(match.group(1))
            share_type = self.determine_share_type(context)

            results['shares'].append({
                'count': shares,
                'type': share_type,
                'owner': self.extract_owner_from_context(context),
                'context': context.strip()
            })

        # Extract ALL claims
        for match in self.claim_pattern.finditer(text):
            claim_text = match.group()
            amount_match = self.money_pattern.search(claim_text)
            if amount_match:
                amount = self.parse_money(amount_match.group())
                claim_type = self.determine_claim_type(claim_text)

                results['claims'].append({
                    'amount': amount,
                    'type': claim_type,
                    'context': claim_text.strip()
                })

        # Find settlement amounts and calculate premiums
        # Pattern 1: "pay X to satisfy Y"
        settlement_pattern1 = re.compile(
            r'(?:pay|payment of|proposes to pay).*?\$[\d,]+(?:\.\d{2})?.*?(?:to satisfy|satisfy).*?(?:claims?|debt|obligation).*?(?:totaling|of|in the amount of)\s*\$[\d,]+(?:\.\d{2})?',
            re.IGNORECASE | re.DOTALL
        )
        # Pattern 2: "settle X for Y"
        settlement_pattern2 = re.compile(
            r'(?:settle|settlement of)\s*\$[\d,]+(?:\.\d{2})?.*?(?:for|in exchange for)\s*\$[\d,]+(?:\.\d{2})?',
            re.IGNORECASE | re.DOTALL
        )

        for pattern in [settlement_pattern1, settlement_pattern2]:
            for match in pattern.finditer(text):
                settlement_text = match.group()
                amounts = self.money_pattern.findall(settlement_text)
                if len(amounts) >= 2:
                    payment = self.parse_money(amounts[0])
                    original = self.parse_money(amounts[1])
                    premium = payment / original if original > 0 else 0

                    # Avoid duplicates
                    if not any(s['payment_amount'] == payment and s['original_amount'] == original
                             for s in results['settlements']):
                        results['settlements'].append({
                            'payment_amount': payment,
                            'original_amount': original,
                            'premium_multiple': round(premium, 2),
                            'context': settlement_text.strip()
                        })

        # Update metadata
        results['extraction_metadata']['total_monetary_amounts'] = len(results['monetary_amounts'])
        results['extraction_metadata']['total_percentages'] = len(results['percentages'])
        results['extraction_metadata']['total_shares'] = len(results['shares'])
        results['extraction_metadata']['total_claims'] = len(results['claims'])
        results['extraction_metadata']['total_settlements'] = len(results['settlements'])

        logger.info(f"Extracted {len(results['monetary_amounts'])} monetary amounts, "
                   f"{len(results['percentages'])} percentages, "
                   f"{len(results['shares'])} share distributions, "
                   f"{len(results['claims'])} claims, "
                   f"{len(results['settlements'])} settlements")

        return results

    def extract_ownership_structure(self, text: str) -> Dict[str, Any]:
        """
        MUST identify voting control vs economic ownership

        Args:
            text: Full document text

        Returns:
            Dictionary with ownership structures and control disparities
        """
        ownership = {
            'voting_control': {},
            'economic_ownership': {},
            'control_disparities': []
        }

        # Find voting control percentages
        voting_pattern = re.compile(
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:has|holds|owns|controls?)\s+(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?(?:voting|control)',
            re.IGNORECASE
        )

        for match in voting_pattern.finditer(text):
            entity = match.group(1)
            percentage = float(match.group(2))
            ownership['voting_control'][entity] = percentage

        # Find economic ownership percentages
        economic_pattern = re.compile(
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:has|holds|owns)\s+(\d+(?:\.\d+)?)\s*%\s*(?:economic|equity|ownership)',
            re.IGNORECASE
        )

        for match in economic_pattern.finditer(text):
            entity = match.group(1)
            percentage = float(match.group(2))
            ownership['economic_ownership'][entity] = percentage

        # Identify control disparities
        for entity in ownership['voting_control']:
            if entity in ownership['economic_ownership']:
                voting = ownership['voting_control'][entity]
                economic = ownership['economic_ownership'][entity]
                if voting > economic:
                    ownership['control_disparities'].append({
                        'entity': entity,
                        'voting_control': voting,
                        'economic_ownership': economic,
                        'disparity': voting - economic,
                        'controls_despite_minority': True
                    })

        logger.info(f"Found {len(ownership['voting_control'])} voting control entries, "
                   f"{len(ownership['economic_ownership'])} economic ownership entries, "
                   f"{len(ownership['control_disparities'])} control disparities")

        return ownership

    def extract_legal_issues(self, text: str) -> Dict[str, Any]:
        """
        MUST identify case law violations and legal problems

        Args:
            text: Full document text

        Returns:
            Dictionary with case citations, statutory references, violations
        """
        legal_issues = {
            'case_citations': [],
            'statutory_references': [],
            'precedent_violations': [],
            'authority_limitations': []
        }

        # Extract case citations
        # Pattern for cases like "Purdue Pharma L.P. v. United States, 144 S. Ct. 2079 (2024)"
        case_pattern = re.compile(
            r'([A-Z][a-zA-Z\s.,&]+(?:L\.P\.|Inc\.|LLC|Corp\.)?)\s+v\.\s+([A-Z][a-zA-Z\s.,&]+(?:L\.P\.|Inc\.|LLC|Corp\.)?),?\s+(\d+)\s+([A-Z]\.\s*(?:[A-Z]t\.?)?)\s+(\d+)\s*(?:\((\d{4})\))?',
            re.IGNORECASE
        )

        for match in case_pattern.finditer(text):
            case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
            citation = match.group()
            context_start = max(0, match.start() - 200)
            context_end = min(len(text), match.end() + 200)
            context = text[context_start:context_end]

            # Check if this is a violation
            if any(word in context.lower() for word in ['violates', 'contrary to', 'conflicts with', 'prohibits', 'precludes']):
                legal_issues['precedent_violations'].append({
                    'case': case_name,
                    'citation': citation,
                    'violation_type': self.determine_violation_type(context),
                    'context': context.strip()
                })
            else:
                legal_issues['case_citations'].append({
                    'case': case_name,
                    'citation': citation
                })

        # Extract statutory references
        statute_pattern = re.compile(
            r'(\d+)\s+U\.S\.C\.\s+§\s*(\d+(?:\([a-z]\))?)',
            re.IGNORECASE
        )

        for match in statute_pattern.finditer(text):
            legal_issues['statutory_references'].append({
                'title': match.group(1),
                'section': match.group(2),
                'citation': match.group()
            })

        # Find authority limitations
        authority_pattern = re.compile(
            r'(?:trustee|debtor|court)\s+(?:lacks?|does not have|has no|without)\s+(?:authority|power|jurisdiction|control)',
            re.IGNORECASE
        )

        for match in authority_pattern.finditer(text):
            context_start = max(0, match.start() - 150)
            context_end = min(len(text), match.end() + 150)
            context = text[context_start:context_end]

            legal_issues['authority_limitations'].append({
                'limitation': match.group(),
                'context': context.strip()
            })

        logger.info(f"Found {len(legal_issues['case_citations'])} case citations, "
                   f"{len(legal_issues['statutory_references'])} statutory references, "
                   f"{len(legal_issues['precedent_violations'])} precedent violations, "
                   f"{len(legal_issues['authority_limitations'])} authority limitations")

        return legal_issues

    def extract_case_info(self, text: str) -> Dict[str, Any]:
        """
        Extract ALL case numbers, court info, and related litigation
        """
        case_info = {
            'primary_case_number': None,
            'all_case_numbers': [],
            'related_cases': [],
            'court': None,
            'judge': None,
            'ecf_references': [],
            'docket_entries': []
        }

        # Extract all case numbers
        for match in self.case_number_pattern.finditer(text):
            case_num = match.group(1)
            if case_num not in case_info['all_case_numbers']:
                case_info['all_case_numbers'].append(case_num)
                if not case_info['primary_case_number']:
                    case_info['primary_case_number'] = case_num

        # Extract civil case numbers (related litigation)
        for match in self.civil_case_pattern.finditer(text):
            case_num = match.group(1)
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]

            if case_num not in [c['case_number'] for c in case_info['related_cases']]:
                case_info['related_cases'].append({
                    'case_number': case_num,
                    'type': 'civil' if '-cv-' in case_num else 'bankruptcy',
                    'context': context.strip()
                })

        # Extract ECF/Docket references
        for match in self.ecf_pattern.finditer(text):
            doc_num = match.group(1)
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 50)
            context = text[context_start:context_end]

            case_info['ecf_references'].append({
                'document_number': doc_num,
                'context': context.strip()
            })

        # Extract court info
        court_patterns = [
            r'(?:United\s+States\s+)?Bankruptcy\s+Court[,\s]+(?:for\s+the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+District\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:In\s+the\s+)?(?:United\s+States\s+)?(?:Bankruptcy|District)\s+Court[,\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(Eastern|Western|Northern|Southern|Middle|Central)\s+District\s+of\s+([A-Z][a-z]+)'
        ]
        for pattern in court_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                case_info['court'] = match.group(0).strip()
                break

        # Extract judge name
        judge_patterns = [
            r'(?:Judge|Hon\.?|Honorable)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)',
            r'(?:Before|Assigned\s+to)[:\s]+(?:Judge|Hon\.?)?\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)'
        ]
        for pattern in judge_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                case_info['judge'] = match.group(1).strip()
                break

        logger.info(f"Found {len(case_info['all_case_numbers'])} case numbers, "
                   f"{len(case_info['related_cases'])} related cases, "
                   f"{len(case_info['ecf_references'])} ECF references")

        return case_info

    def extract_invoice_data(self, text: str) -> Dict[str, Any]:
        """
        Extract ALL invoice information including counterparties and amounts
        """
        invoice_data = {
            'invoices': [],
            'counterparties': [],
            'total_invoiced': 0.0,
            'invoice_count': 0
        }

        # Extract invoice numbers and amounts
        invoice_sections = re.finditer(
            r'(?:Invoice|Inv\.?)[^$]*?(\$[\d,]+(?:\.\d{2})?)',
            text, re.IGNORECASE | re.DOTALL
        )

        for match in invoice_sections:
            amount = self.parse_money(match.group(1))
            context_start = max(0, match.start() - 150)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]

            # Try to extract invoice number
            inv_num_match = self.invoice_pattern.search(context)
            inv_num = inv_num_match.group(1) if inv_num_match else None

            # Try to extract counterparty from context
            counterparty = self.extract_counterparty_from_context(context)

            invoice_data['invoices'].append({
                'invoice_number': inv_num,
                'amount': amount,
                'amount_raw': match.group(1),
                'counterparty': counterparty,
                'context': context.strip()
            })
            invoice_data['total_invoiced'] += amount

            if counterparty and counterparty not in invoice_data['counterparties']:
                invoice_data['counterparties'].append(counterparty)

        # Also look for counterparty/vendor names in various patterns
        counterparty_patterns = [
            r'(?:Payable\s+to|Paid\s+to|Vendor|Supplier|Contractor|Creditor)[:\s]+([A-Z][A-Za-z\s,&]+(?:LLC|Inc|Corp|Ltd|LLP)?)',
            r'(?:Invoice\s+from|Billed\s+by)[:\s]+([A-Z][A-Za-z\s,&]+(?:LLC|Inc|Corp|Ltd|LLP)?)',
            r'(?:Services?\s+(?:provided|rendered)\s+by)[:\s]+([A-Z][A-Za-z\s,&]+(?:LLC|Inc|Corp|Ltd|LLP)?)'
        ]

        for pattern in counterparty_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                counterparty = match.group(1).strip()
                if counterparty and len(counterparty) > 2 and counterparty not in invoice_data['counterparties']:
                    invoice_data['counterparties'].append(counterparty)

        invoice_data['invoice_count'] = len(invoice_data['invoices'])

        logger.info(f"Found {invoice_data['invoice_count']} invoices, "
                   f"{len(invoice_data['counterparties'])} counterparties, "
                   f"total ${invoice_data['total_invoiced']:,.2f}")

        return invoice_data

    def extract_counterparty_from_context(self, context: str) -> Optional[str]:
        """Extract counterparty/vendor name from invoice context"""
        patterns = [
            r'(?:from|to|by|for)\s+([A-Z][A-Za-z\s,&]+(?:LLC|Inc|Corp|Ltd|LLP)?)',
            r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3}(?:,?\s*(?:LLC|Inc|Corp|Ltd|LLP)))'
        ]
        for pattern in patterns:
            match = re.search(pattern, context)
            if match:
                name = match.group(1).strip()
                # Filter out common false positives
                if name.lower() not in ['the', 'this', 'that', 'invoice', 'payment', 'amount']:
                    return name
        return None

    def extract_attorney_info(self, text: str) -> Dict[str, Any]:
        """
        Extract attorney and law firm contact information
        """
        attorney_info = {
            'attorneys': [],
            'law_firms': [],
            'contact_info': []
        }

        # Extract attorney names with credentials
        for match in self.attorney_pattern.finditer(text):
            name = match.group(1).strip()
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]

            # Look for bar number
            bar_match = self.bar_number_pattern.search(context)
            bar_num = bar_match.group(1) if bar_match else None

            attorney_info['attorneys'].append({
                'name': name,
                'bar_number': bar_num,
                'context': context.strip()
            })

        # Extract law firm names
        firm_patterns = [
            r'([A-Z][a-z]+(?:\s*[,&]\s*[A-Z][a-z]+)+(?:,?\s*(?:LLP|PLLC|LLC|P\.?C\.?|Law\s*(?:Firm|Group|Offices?))))',
            r'(?:Law\s+(?:Firm|Office(?:s)?|Group)\s+of\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Law\s+(?:Firm|Office(?:s)?|Group))'
        ]
        for pattern in firm_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                firm = match.group(1).strip()
                if firm and firm not in attorney_info['law_firms']:
                    attorney_info['law_firms'].append(firm)

        # Extract contact info (phone, email, address)
        phone_pattern = r'(?:Tel|Phone|Ph|Fax)[:\s]*\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})'
        for match in re.finditer(phone_pattern, text, re.IGNORECASE):
            attorney_info['contact_info'].append({
                'type': 'phone',
                'value': f"({match.group(1)}) {match.group(2)}-{match.group(3)}"
            })

        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        for match in re.finditer(email_pattern, text):
            attorney_info['contact_info'].append({
                'type': 'email',
                'value': match.group()
            })

        logger.info(f"Found {len(attorney_info['attorneys'])} attorneys, "
                   f"{len(attorney_info['law_firms'])} law firms")

        return attorney_info

    def calculate_fraud_indicators(self, text: str, financial_data: Dict[str, Any], invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate fraud risk indicators including claim inflation analysis
        """
        fraud_indicators = {
            'risk_level': 'LOW',
            'risk_score': 0,
            'indicators': [],
            'claim_analysis': {
                'claimed_amount': 0.0,
                'supported_amount': 0.0,
                'inflation_ratio': 0.0,
                'unsupported_amount': 0.0
            },
            'red_flags': []
        }

        # Get all monetary amounts
        amounts = [item['amount'] for item in financial_data.get('monetary_amounts', [])]

        if not amounts:
            return fraud_indicators

        # Find the largest amount (likely the claim amount)
        max_amount = max(amounts)

        # Find invoice/supported amounts
        invoice_total = invoice_data.get('total_invoiced', 0.0)

        # Calculate inflation if we have both claim and invoice data
        if max_amount > 0 and invoice_total > 0:
            inflation_ratio = max_amount / invoice_total
            unsupported = max_amount - invoice_total

            fraud_indicators['claim_analysis'] = {
                'claimed_amount': max_amount,
                'supported_amount': invoice_total,
                'inflation_ratio': round(inflation_ratio, 2),
                'unsupported_amount': unsupported
            }

            # Flag significant inflation
            if inflation_ratio > 1.5:
                fraud_indicators['indicators'].append({
                    'type': 'CLAIM_INFLATION',
                    'severity': 'HIGH' if inflation_ratio > 2.0 else 'MEDIUM',
                    'description': f"Claim amount ${max_amount:,.2f} is {inflation_ratio:.1f}x the documented invoice total ${invoice_total:,.2f}",
                    'unsupported_amount': unsupported
                })
                fraud_indicators['risk_score'] += 30 if inflation_ratio > 2.0 else 20

            if inflation_ratio > 3.0:
                fraud_indicators['red_flags'].append(
                    f"CRITICAL: Claim appears {inflation_ratio:.1f}x inflated - ${unsupported:,.2f} unsupported"
                )
                fraud_indicators['risk_score'] += 20

        # Check for round number amounts (potential fabrication indicator)
        round_amounts = [a for a in amounts if a > 1000 and a % 1000 == 0]
        if len(round_amounts) > 2:
            fraud_indicators['indicators'].append({
                'type': 'ROUND_NUMBERS',
                'severity': 'LOW',
                'description': f"Multiple round-number amounts detected: {round_amounts[:5]}"
            })
            fraud_indicators['risk_score'] += 5

        # Check for duplicate amounts
        from collections import Counter
        amount_counts = Counter(amounts)
        duplicates = {amt: count for amt, count in amount_counts.items() if count > 1 and amt > 100}
        if duplicates:
            fraud_indicators['indicators'].append({
                'type': 'DUPLICATE_AMOUNTS',
                'severity': 'MEDIUM',
                'description': f"Duplicate amounts found: {duplicates}"
            })
            fraud_indicators['risk_score'] += 10

        # Set overall risk level
        if fraud_indicators['risk_score'] >= 50:
            fraud_indicators['risk_level'] = 'HIGH'
        elif fraud_indicators['risk_score'] >= 25:
            fraud_indicators['risk_level'] = 'MEDIUM'
        else:
            fraud_indicators['risk_level'] = 'LOW'

        logger.info(f"Fraud analysis: risk_level={fraud_indicators['risk_level']}, "
                   f"score={fraud_indicators['risk_score']}, "
                   f"indicators={len(fraud_indicators['indicators'])}")

        return fraud_indicators

    def process_bankruptcy_document(self, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Main entry point: Process a complete bankruptcy document

        Args:
            text: Full document text
            filename: Original filename for metadata

        Returns:
            Comprehensive extraction results with all financial and legal data
        """
        logger.info(f"Processing bankruptcy document: {filename}")

        # Core extractions
        financial_data = self.extract_all_financial_data(text)
        ownership_structure = self.extract_ownership_structure(text)
        legal_issues = self.extract_legal_issues(text)

        # NEW: Enhanced extractions
        case_info = self.extract_case_info(text)
        invoice_data = self.extract_invoice_data(text)
        attorney_info = self.extract_attorney_info(text)

        # NEW: Fraud analysis
        fraud_indicators = self.calculate_fraud_indicators(text, financial_data, invoice_data)

        result = {
            'filename': filename,
            'processed_at': datetime.now().isoformat(),
            'text_length': len(text),

            # Core data
            'financial_data': financial_data,
            'ownership_structure': ownership_structure,
            'legal_issues': legal_issues,

            # NEW: Case information
            'case_info': case_info,
            'case_number': case_info.get('primary_case_number'),
            'court': case_info.get('court'),
            'judge': case_info.get('judge'),
            'related_cases': case_info.get('related_cases', []),
            'ecf_references': case_info.get('ecf_references', []),

            # NEW: Invoice and counterparty data
            'invoice_data': invoice_data,
            'counterparties': invoice_data.get('counterparties', []),
            'total_invoiced': invoice_data.get('total_invoiced', 0.0),

            # NEW: Attorney information
            'attorney_info': attorney_info,
            'attorneys': attorney_info.get('attorneys', []),
            'law_firms': attorney_info.get('law_firms', []),

            # NEW: Fraud indicators
            'fraud_indicators': fraud_indicators,
            'fraud_risk_level': fraud_indicators.get('risk_level', 'LOW'),
            'claim_inflation': fraud_indicators.get('claim_analysis', {}),

            'summary_statistics': {}
        }

        # Calculate summary statistics
        result['summary_statistics'] = {
            'total_monetary_amounts': len(financial_data['monetary_amounts']),
            'total_percentages': len(financial_data['percentages']),
            'total_shares': len(financial_data['shares']),
            'total_claims': len(financial_data['claims']),
            'total_settlements': len(financial_data['settlements']),
            'voting_control_entities': len(ownership_structure['voting_control']),
            'economic_ownership_entities': len(ownership_structure['economic_ownership']),
            'control_disparities': len(ownership_structure['control_disparities']),
            'case_citations': len(legal_issues['case_citations']),
            'statutory_references': len(legal_issues['statutory_references']),
            'precedent_violations': len(legal_issues['precedent_violations']),
            'authority_limitations': len(legal_issues['authority_limitations']),
            # NEW statistics
            'related_cases': len(case_info.get('related_cases', [])),
            'ecf_references': len(case_info.get('ecf_references', [])),
            'invoices': invoice_data.get('invoice_count', 0),
            'counterparties': len(invoice_data.get('counterparties', [])),
            'attorneys': len(attorney_info.get('attorneys', [])),
            'fraud_indicators': len(fraud_indicators.get('indicators', [])),
            'fraud_risk_level': fraud_indicators.get('risk_level', 'LOW')
        }

        # Calculate total unique monetary values
        unique_amounts = set(item['amount'] for item in financial_data['monetary_amounts'])
        result['summary_statistics']['unique_monetary_values'] = len(unique_amounts)

        logger.info(f"Bankruptcy document processing complete: {result['summary_statistics']}")

        return result

    def parse_money(self, money_str: str) -> float:
        """Convert money string to float, handling millions/billions"""
        money_str = money_str.replace('$', '').replace(',', '').strip()

        multiplier = 1
        if any(m in money_str.lower() for m in ['million', 'm']):
            multiplier = 1000000
            money_str = re.sub(r'[mM]illion|[mM]', '', money_str).strip()
        elif any(b in money_str.lower() for b in ['billion', 'b']):
            multiplier = 1000000000
            money_str = re.sub(r'[bB]illion|[bB]', '', money_str).strip()

        try:
            # Handle remaining text after number
            num_match = re.search(r'[\d.]+', money_str)
            if num_match:
                return float(num_match.group()) * multiplier
            return 0.0
        except:
            return 0.0

    def parse_number(self, num_str: str) -> int:
        """Convert number string with commas to int"""
        try:
            return int(num_str.replace(',', ''))
        except:
            return 0

    def determine_claim_type(self, text: str) -> str:
        """Determine the type of claim from context"""
        text_lower = text.lower()
        if 'secured' in text_lower:
            return 'secured'
        elif 'unsecured' in text_lower:
            return 'unsecured'
        elif 'priority' in text_lower:
            return 'priority'
        else:
            return 'general'

    def determine_share_type(self, text: str) -> str:
        """Determine the type of shares from context"""
        text_lower = text.lower()
        if 'voting' in text_lower and 'non' not in text_lower:
            return 'voting'
        elif 'non-voting' in text_lower or 'nonvoting' in text_lower:
            return 'non-voting'
        elif 'preferred' in text_lower:
            return 'preferred'
        else:
            return 'common'

    def determine_percentage_type(self, text: str) -> str:
        """Determine what the percentage represents from context"""
        text_lower = text.lower()
        if 'voting' in text_lower:
            return 'voting_control'
        elif 'economic' in text_lower or 'equity' in text_lower:
            return 'economic_ownership'
        elif 'ownership' in text_lower:
            return 'ownership'
        else:
            return 'unspecified'

    def extract_owner_from_context(self, text: str) -> str:
        """Extract person or entity names from context"""
        # Extract person or entity names before percentage
        name_pattern = re.compile(r'((?:Dr\.|Mr\.|Ms\.)?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)')
        matches = name_pattern.findall(text)
        return matches[0] if matches else 'Unknown'

    def determine_violation_type(self, text: str) -> str:
        """Determine the type of legal violation from context"""
        text_lower = text.lower()
        if 'third party release' in text_lower or 'third-party release' in text_lower:
            return 'non-consensual_third_party_release'
        elif 'authority' in text_lower:
            return 'exceeds_authority'
        elif 'jurisdiction' in text_lower:
            return 'jurisdiction_violation'
        else:
            return 'precedent_violation'


# Global instance
bankruptcy_processor = BankruptcyDocumentProcessor()
