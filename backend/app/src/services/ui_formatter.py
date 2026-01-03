"""
UI Formatter for Bankruptcy Extraction Results

Formats complex extraction results into UI-friendly structure
with summaries, highlights, and visual indicators.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


def format_results_for_display(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format extraction results for the UI

    Takes raw extraction results and creates a structured,
    UI-friendly format with summaries, highlights, and red flags.

    Args:
        results: Raw extraction results from process_document endpoint

    Returns:
        Formatted data optimized for UI display
    """
    financial = results.get('financial', {})
    ownership = results.get('ownership', {})
    legal = results.get('legal', {})
    metrics = results.get('metrics', {})
    alerts = results.get('alerts', [])
    stats = results.get('extraction_stats', {})

    display_data = {
        # FINANCIAL SUMMARY
        'financial_summary': {
            'total_claims': sum([c.get('amount', 0) for c in financial.get('claims', [])]),
            'total_settlements': sum([s.get('payment_amount', 0) for s in financial.get('settlements', [])]),
            'largest_amount': max([m.get('amount', 0) for m in financial.get('monetary_amounts', [])], default=0),
            'smallest_amount': min([m.get('amount', 0) for m in financial.get('monetary_amounts', []) if m.get('amount', 0) > 0], default=0),
            'total_amounts_found': len(financial.get('monetary_amounts', [])),
            'settlement_overpayments': [
                {
                    'payment': s.get('payment_amount', 0),
                    'original': s.get('original_amount', 0),
                    'premium': s.get('premium_multiple', 0),
                    'excess': s.get('payment_amount', 0) - s.get('original_amount', 0),
                    'is_suspicious': s.get('premium_multiple', 0) > 1.5
                }
                for s in financial.get('settlements', [])
                if s.get('premium_multiple', 0) > 1.0
            ],
            'claims_breakdown': categorize_claims(financial.get('claims', []))
        },

        # OWNERSHIP ANALYSIS
        'ownership_analysis': {
            'control_structure': ownership.get('voting_control', {}),
            'economic_structure': ownership.get('economic_ownership', {}),
            'disparities': [
                {
                    'entity': d.get('entity', 'Unknown'),
                    'voting': d.get('voting_control', 0),
                    'economic': d.get('economic_ownership', 0),
                    'gap': d.get('disparity', 0),
                    'severity': 'HIGH' if d.get('disparity', 0) > 30 else 'MEDIUM' if d.get('disparity', 0) > 15 else 'LOW'
                }
                for d in ownership.get('control_disparities', [])
            ],
            'has_control_issues': len(ownership.get('control_disparities', [])) > 0
        },

        # LEGAL CONCERNS
        'legal_concerns': {
            'precedent_violations': [
                {
                    'case_name': v.get('case', 'Unknown'),
                    'citation': v.get('citation', ''),
                    'violation_type': v.get('violation_type', 'Unknown'),
                    'severity': 'CRITICAL',
                    'context_preview': v.get('context', '')[:200]
                }
                for v in legal.get('precedent_violations', [])
            ],
            'authority_issues': [
                {
                    'limitation': a.get('limitation', 'Unknown'),
                    'context_preview': a.get('context', '')[:200]
                }
                for a in legal.get('authority_limitations', [])
            ],
            'statutory_references': [
                {
                    'citation': s.get('citation', ''),
                    'title': s.get('title', ''),
                    'section': s.get('section', '')
                }
                for s in legal.get('statutory_references', [])
            ],
            'total_issues': len(legal.get('precedent_violations', [])) + len(legal.get('authority_limitations', []))
        },

        # FRAUD INDICATORS
        'fraud_indicators': {
            'total_indicators': metrics.get('overall_statistics', {}).get('fraud_indicators', 0),
            'preferential_treatments': [
                {
                    'beneficiary': p.get('beneficiary', 'Unknown'),
                    'premium': p.get('premium_multiple', 0),
                    'payment': p.get('payment_amount', 0),
                    'original': p.get('original_claim', 0),
                    'excess': p.get('excess_payment', 0),
                    'is_fraud': p.get('potential_fraud', False),
                    'severity': 'CRITICAL' if p.get('potential_fraud', False) else 'WARNING'
                }
                for p in metrics.get('preferential_treatments', [])
            ],
            'fraudulent_conveyances': [
                {
                    'amount': f.get('amount', 0),
                    'red_flags': [flag for flag in f.get('red_flags', []) if flag],
                    'risk_level': f.get('risk_level', 'UNKNOWN'),
                    'context_preview': f.get('context', '')[:200]
                }
                for f in results.get('fraudulent_conveyances', [])
            ],
            'has_fraud_indicators': metrics.get('overall_statistics', {}).get('fraud_indicators', 0) > 0
        },

        # ALERTS (USER-FACING)
        'alerts': {
            'critical': [a for a in alerts if a.get('level') == 'CRITICAL'],
            'warnings': [a for a in alerts if a.get('level') == 'WARNING'],
            'info': [a for a in alerts if a.get('level') == 'INFO'],
            'total_count': len(alerts),
            'has_critical': any(a.get('level') == 'CRITICAL' for a in alerts)
        },

        # CREDITOR RECOVERY ANALYSIS
        'creditor_recovery': format_creditor_recovery(
            results.get('creditor_recovery', {}),
            metrics.get('recovery_analysis', {})
        ),

        # EXTRACTION STATISTICS
        'extraction_stats': {
            'amounts_extracted': stats.get('amounts_found', 0),
            'unique_amounts': stats.get('unique_amounts', 0),
            'claims_extracted': stats.get('claims_found', 0),
            'settlements_extracted': stats.get('settlements_found', 0),
            'legal_citations': stats.get('case_citations', 0) + stats.get('precedent_violations', 0),
            'completeness_score': calculate_completeness_score(stats),
            'extraction_complete': stats.get('extraction_complete', False),
            'ai_backup_used': stats.get('ai_backup_used', False)
        },

        # OVERALL ASSESSMENT
        'overall_assessment': {
            'risk_level': calculate_overall_risk_level(
                len(metrics.get('preferential_treatments', [])),
                len(results.get('fraudulent_conveyances', [])),
                len(legal.get('precedent_violations', [])),
                metrics.get('overall_statistics', {}).get('fraud_indicators', 0)
            ),
            'total_red_flags': (
                len(metrics.get('preferential_treatments', [])) +
                len(results.get('fraudulent_conveyances', [])) +
                len(legal.get('precedent_violations', [])) +
                len(ownership.get('control_disparities', []))
            ),
            'requires_immediate_attention': any(a.get('level') == 'CRITICAL' for a in alerts),
            'summary': generate_executive_summary(results)
        },

        # METADATA
        'metadata': {
            'filename': results.get('filename', 'Unknown'),
            'processed_at': results.get('processed_at', datetime.now().isoformat()),
            'file_size': results.get('file_size', 0),
            'text_length': results.get('text_length', 0)
        }
    }

    logger.info(f"Formatted results for UI display: {display_data['overall_assessment']['total_red_flags']} red flags")

    return display_data


def categorize_claims(claims: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Categorize claims by type with totals

    Args:
        claims: List of claim dictionaries

    Returns:
        Breakdown by claim type
    """
    breakdown = {
        'secured': {'total': 0, 'count': 0, 'claims': []},
        'unsecured': {'total': 0, 'count': 0, 'claims': []},
        'priority': {'total': 0, 'count': 0, 'claims': []},
        'general': {'total': 0, 'count': 0, 'claims': []}
    }

    for claim in claims:
        claim_type = claim.get('type', 'general').lower()
        amount = claim.get('amount', 0)

        if claim_type in breakdown:
            breakdown[claim_type]['total'] += amount
            breakdown[claim_type]['count'] += 1
            breakdown[claim_type]['claims'].append(claim)

    return breakdown


def format_creditor_recovery(
    creditor_recovery: Dict[str, Any],
    recovery_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format creditor recovery data for UI

    Args:
        creditor_recovery: Recovery by creditor class
        recovery_analysis: Overall recovery analysis

    Returns:
        Formatted recovery data
    """
    by_class = creditor_recovery.get('by_class', {})
    inequities = creditor_recovery.get('inequities', [])

    formatted = {
        'by_class': [
            {
                'class': class_name,
                'total_claims': data.get('total_claims', 0),
                'claim_count': data.get('claim_count', 0),
                'estimated_recovery': data.get('estimated_recovery', 0),
                'recovery_rate': data.get('recovery_rate', 0),
                'expected_rate': data.get('expected_rate', 0),
                'difference': data.get('recovery_rate', 0) - data.get('expected_rate', 0),
                'is_favorable': data.get('recovery_rate', 0) > data.get('expected_rate', 0),
                'is_unfavorable': data.get('recovery_rate', 0) < data.get('expected_rate', 0)
            }
            for class_name, data in by_class.items()
        ],
        'inequities': [
            {
                'class': i.get('creditor_class', 'Unknown'),
                'actual_rate': i.get('actual_rate', 0),
                'expected_rate': i.get('expected_rate', 0),
                'difference': i.get('difference', 0),
                'is_favored': i.get('favored', False)
            }
            for i in inequities
        ],
        'overall': {
            'total_claims': recovery_analysis.get('total_claims', 0),
            'total_payments': recovery_analysis.get('total_payments', 0),
            'overall_rate': recovery_analysis.get('overall_recovery_rate', 0),
            'expected_rate': recovery_analysis.get('expected_bankruptcy_recovery', 0.30),
            'is_suspicious': recovery_analysis.get('suspicious', False),
            'excess_recovery': recovery_analysis.get('excess_recovery', 0)
        }
    }

    return formatted


def calculate_completeness_score(stats: Dict[str, Any]) -> float:
    """
    Calculate extraction completeness score (0-100)

    Args:
        stats: Extraction statistics

    Returns:
        Completeness score as percentage
    """
    score = 0.0
    max_score = 100.0

    # Each component contributes to completeness
    if stats.get('amounts_found', 0) > 0:
        score += 20  # Found monetary amounts

    if stats.get('claims_found', 0) > 0:
        score += 20  # Found claims

    if stats.get('settlements_found', 0) > 0:
        score += 15  # Found settlements

    if stats.get('case_citations', 0) + stats.get('precedent_violations', 0) > 0:
        score += 15  # Found legal citations

    if stats.get('statutory_references', 0) > 0:
        score += 10  # Found statutory references

    if stats.get('extraction_complete', False):
        score += 20  # Extraction marked as complete

    return min(score, max_score)


def calculate_overall_risk_level(
    preferential_count: int,
    fraudulent_count: int,
    violations_count: int,
    fraud_indicators: int
) -> str:
    """
    Calculate overall risk level

    Args:
        preferential_count: Number of preferential treatments
        fraudulent_count: Number of fraudulent conveyances
        violations_count: Number of precedent violations
        fraud_indicators: Total fraud indicators

    Returns:
        Risk level: CRITICAL, HIGH, MEDIUM, LOW
    """
    total_issues = preferential_count + fraudulent_count + violations_count

    if fraud_indicators >= 3 or fraudulent_count >= 2 or violations_count >= 2:
        return 'CRITICAL'
    elif total_issues >= 2 or fraud_indicators >= 1:
        return 'HIGH'
    elif total_issues >= 1:
        return 'MEDIUM'
    else:
        return 'LOW'


def generate_executive_summary(results: Dict[str, Any]) -> str:
    """
    Generate executive summary of findings

    Args:
        results: Complete extraction results

    Returns:
        Executive summary text
    """
    stats = results.get('extraction_stats', {})
    alerts = results.get('alerts', [])
    metrics = results.get('metrics', {})

    critical_count = sum(1 for a in alerts if a.get('level') == 'CRITICAL')
    warning_count = sum(1 for a in alerts if a.get('level') == 'WARNING')

    summary_parts = []

    # Document overview
    summary_parts.append(
        f"Extracted {stats.get('amounts_found', 0)} monetary amounts, "
        f"{stats.get('claims_found', 0)} claims, and "
        f"{stats.get('settlements_found', 0)} settlements."
    )

    # Critical issues
    if critical_count > 0:
        summary_parts.append(
            f"CRITICAL: {critical_count} critical issue(s) requiring immediate attention."
        )

    # Fraud indicators
    fraud_count = metrics.get('overall_statistics', {}).get('fraud_indicators', 0)
    if fraud_count > 0:
        summary_parts.append(
            f"WARNING: {fraud_count} fraud indicator(s) detected."
        )

    # Preferential treatments
    pref_count = len(metrics.get('preferential_treatments', []))
    if pref_count > 0:
        summary_parts.append(
            f"Found {pref_count} preferential treatment(s) with excessive premiums."
        )

    # No issues
    if critical_count == 0 and warning_count == 0 and fraud_count == 0:
        summary_parts.append(
            "No critical issues or fraud indicators detected."
        )

    return " ".join(summary_parts)
