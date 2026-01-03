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

        result = {
            'filename': filename,
            'processed_at': datetime.now().isoformat(),
            'text_length': len(text),
            'financial_data': self.extract_all_financial_data(text),
            'ownership_structure': self.extract_ownership_structure(text),
            'legal_issues': self.extract_legal_issues(text),
            'summary_statistics': {}
        }

        # Calculate summary statistics
        result['summary_statistics'] = {
            'total_monetary_amounts': len(result['financial_data']['monetary_amounts']),
            'total_percentages': len(result['financial_data']['percentages']),
            'total_shares': len(result['financial_data']['shares']),
            'total_claims': len(result['financial_data']['claims']),
            'total_settlements': len(result['financial_data']['settlements']),
            'voting_control_entities': len(result['ownership_structure']['voting_control']),
            'economic_ownership_entities': len(result['ownership_structure']['economic_ownership']),
            'control_disparities': len(result['ownership_structure']['control_disparities']),
            'case_citations': len(result['legal_issues']['case_citations']),
            'statutory_references': len(result['legal_issues']['statutory_references']),
            'precedent_violations': len(result['legal_issues']['precedent_violations']),
            'authority_limitations': len(result['legal_issues']['authority_limitations'])
        }

        # Calculate total unique monetary values
        unique_amounts = set(item['amount'] for item in result['financial_data']['monetary_amounts'])
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
