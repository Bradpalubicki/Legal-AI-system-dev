"""
Bankruptcy Settlement Metrics Calculator

Calculates who's getting preferential treatment, settlement inequities,
and identifies potential fraudulent preferential payments.
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def calculate_settlement_metrics(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate who's getting screwed in the settlement

    Identifies:
    - Preferential treatments (premium > 2x)
    - Settlement inequities (different creditors getting different rates)
    - Suspicious payments
    - Total recovery rates

    Args:
        financial_data: Financial data from BankruptcyDocumentProcessor

    Returns:
        Dictionary with calculated metrics
    """
    metrics = {
        'settlement_inequities': [],
        'preferential_treatments': [],
        'suspicious_payments': [],
        'recovery_analysis': {},
        'overall_statistics': {}
    }

    settlements = financial_data.get('settlements', [])
    claims = financial_data.get('claims', [])
    monetary_amounts = financial_data.get('monetary_amounts', [])

    # Identify preferential treatments (premium > 2x is suspicious)
    for settlement in settlements:
        premium = settlement.get('premium_multiple', 0)
        payment = settlement.get('payment_amount', 0)
        original = settlement.get('original_amount', 0)

        if premium > 2.0:
            beneficiary = extract_beneficiary(settlement.get('context', ''))

            metrics['preferential_treatments'].append({
                'beneficiary': beneficiary,
                'premium_multiple': premium,
                'payment_amount': payment,
                'original_claim': original,
                'excess_payment': payment - original,
                'potential_fraud': premium > 3.0,  # 3x is extremely suspicious
                'context': settlement.get('context', '')[:200]
            })

        # Check for inequitable settlements (any premium > 1.5x while others get less)
        if premium > 1.5:
            metrics['settlement_inequities'].append({
                'description': f"Settlement at {premium}x while standard bankruptcy recovery is 0.3x-0.5x",
                'beneficiary': extract_beneficiary(settlement.get('context', '')),
                'premium': premium,
                'payment': payment,
                'red_flag': True
            })

    # Analyze claim recovery rates
    if claims:
        total_claims = sum(claim.get('amount', 0) for claim in claims)
        total_payments = sum(s.get('payment_amount', 0) for s in settlements)

        if total_claims > 0:
            overall_recovery_rate = total_payments / total_claims

            metrics['recovery_analysis'] = {
                'total_claims': total_claims,
                'total_payments': total_payments,
                'overall_recovery_rate': round(overall_recovery_rate, 3),
                'expected_bankruptcy_recovery': 0.30,  # Typical bankruptcy recovery is 30%
                'excess_recovery': overall_recovery_rate - 0.30 if overall_recovery_rate > 0.30 else 0,
                'suspicious': overall_recovery_rate > 1.0,  # Paying more than claimed is suspicious
            }

    # Identify suspicious large payments
    if monetary_amounts:
        amounts = [amt.get('amount', 0) for amt in monetary_amounts]
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            max_amount = max(amounts)

            # Flag payments > 3x average as suspicious
            for amt in monetary_amounts:
                amount = amt.get('amount', 0)
                if amount > avg_amount * 3 and amount == max_amount:
                    metrics['suspicious_payments'].append({
                        'amount': amount,
                        'times_above_average': round(amount / avg_amount, 1) if avg_amount > 0 else 0,
                        'context': amt.get('context', '')[:200],
                        'reason': 'Significantly larger than average payment'
                    })

    # Overall statistics
    metrics['overall_statistics'] = {
        'total_settlements': len(settlements),
        'preferential_treatments_found': len(metrics['preferential_treatments']),
        'settlement_inequities_found': len(metrics['settlement_inequities']),
        'suspicious_payments_found': len(metrics['suspicious_payments']),
        'highest_premium': max([s.get('premium_multiple', 0) for s in settlements]) if settlements else 0,
        'average_premium': sum([s.get('premium_multiple', 0) for s in settlements]) / len(settlements) if settlements else 0,
        'fraud_indicators': sum([
            len(metrics['preferential_treatments']),
            len(metrics['suspicious_payments']),
            1 if metrics.get('recovery_analysis', {}).get('suspicious', False) else 0
        ])
    }

    logger.info(f"Calculated settlement metrics: {metrics['overall_statistics']}")

    return metrics


def extract_beneficiary(context: str) -> str:
    """
    Extract who is benefiting from a settlement/payment

    Looks for patterns like:
    - "pay [PERSON/ENTITY]"
    - "payment to [PERSON/ENTITY]"
    - "settle with [PERSON/ENTITY]"
    """
    # Pattern for entity/person names
    beneficiary_patterns = [
        r'(?:pay|payment to|settle with|paid to)\s+([A-Z][a-zA-Z\s.,&]+(?:L\.P\.|Inc\.|LLC|Corp\.|Trust)?)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:receives|shall receive|will receive)',
        r'(?:for the benefit of|beneficiary:)\s+([A-Z][a-zA-Z\s.,&]+)',
    ]

    for pattern in beneficiary_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            beneficiary = match.group(1).strip()
            # Clean up
            beneficiary = re.sub(r'\s+', ' ', beneficiary)
            return beneficiary[:100]  # Limit length

    return "Unknown beneficiary"


def calculate_creditor_recovery_rates(
    claims: List[Dict[str, Any]],
    settlements: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate recovery rates by creditor class

    Args:
        claims: List of claims with amounts and types
        settlements: List of settlements

    Returns:
        Recovery rates by creditor class
    """
    recovery = {
        'by_class': {},
        'inequities': []
    }

    # Group claims by type
    claims_by_type = {}
    for claim in claims:
        claim_type = claim.get('type', 'general')
        amount = claim.get('amount', 0)

        if claim_type not in claims_by_type:
            claims_by_type[claim_type] = {'total': 0, 'count': 0}

        claims_by_type[claim_type]['total'] += amount
        claims_by_type[claim_type]['count'] += 1

    # Calculate recovery rates
    total_settlements = sum(s.get('payment_amount', 0) for s in settlements)
    total_claims = sum(data['total'] for data in claims_by_type.values())

    for claim_type, data in claims_by_type.items():
        # Estimate recovery (simplified - in reality would need to map settlements to claims)
        estimated_recovery = (data['total'] / total_claims * total_settlements) if total_claims > 0 else 0
        recovery_rate = estimated_recovery / data['total'] if data['total'] > 0 else 0

        recovery['by_class'][claim_type] = {
            'total_claims': data['total'],
            'claim_count': data['count'],
            'estimated_recovery': estimated_recovery,
            'recovery_rate': round(recovery_rate, 3),
            'expected_rate': get_expected_recovery_rate(claim_type)
        }

        # Identify inequities
        expected = get_expected_recovery_rate(claim_type)
        if abs(recovery_rate - expected) > 0.2:  # More than 20% difference
            recovery['inequities'].append({
                'creditor_class': claim_type,
                'actual_rate': recovery_rate,
                'expected_rate': expected,
                'difference': recovery_rate - expected,
                'favored': recovery_rate > expected
            })

    return recovery


def get_expected_recovery_rate(claim_type: str) -> float:
    """
    Get expected recovery rate by claim type in typical bankruptcy

    Args:
        claim_type: Type of claim (secured, unsecured, priority, etc.)

    Returns:
        Expected recovery rate (0.0 to 1.0)
    """
    expected_rates = {
        'secured': 0.80,      # Secured creditors typically recover 80%
        'priority': 0.60,     # Priority claims recover ~60%
        'unsecured': 0.30,    # Unsecured creditors recover ~30%
        'general': 0.25,      # General unsecured even lower
        'subordinated': 0.10  # Subordinated debt recovers ~10%
    }

    return expected_rates.get(claim_type.lower(), 0.30)


def identify_fraudulent_conveyances(
    monetary_amounts: List[Dict[str, Any]],
    ownership_structure: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Identify potentially fraudulent conveyances or preferential transfers

    Red flags:
    - Payments to insiders at premium rates
    - Payments shortly before bankruptcy filing
    - Payments to entities with control relationships

    Args:
        monetary_amounts: All monetary amounts extracted
        ownership_structure: Ownership and control structure

    Returns:
        List of suspicious transactions
    """
    suspicious = []

    # Get entities with control
    control_entities = set(ownership_structure.get('voting_control', {}).keys())

    # Check for large payments that might be to insiders
    for amount_data in monetary_amounts:
        amount = amount_data.get('amount', 0)
        context = amount_data.get('context', '').lower()

        # Red flags
        is_large = amount > 100000  # > $100K
        mentions_insider = any(word in context for word in ['officer', 'director', 'insider', 'principal', 'founder'])
        mentions_timing = any(word in context for word in ['within 90 days', 'shortly before', 'immediately before'])

        # Check if payment to controlled entity
        to_controlled_entity = any(entity.lower() in context for entity in control_entities)

        if is_large and (mentions_insider or to_controlled_entity or mentions_timing):
            suspicious.append({
                'amount': amount,
                'red_flags': [
                    'large_payment' if is_large else None,
                    'insider_payment' if mentions_insider else None,
                    'suspicious_timing' if mentions_timing else None,
                    'controlled_entity' if to_controlled_entity else None
                ],
                'context': amount_data.get('context', '')[:200],
                'risk_level': 'HIGH'
            })

    return suspicious
