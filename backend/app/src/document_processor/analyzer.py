"""
Document Analysis Engine with Defense Strategy Generation
Provides concrete defense options and actionable next steps
"""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DefenseStrategy:
    """Structure for defense strategy information"""
    name: str
    viability: str  # Strong, Possible, Check, Weak
    requirements: str
    next_step: str
    deadline: Optional[str] = None
    strength_score: float = 0.0  # 0.0 to 1.0

class DocumentAnalyzer:
    """
    Enhanced document analyzer that provides concrete defense strategies
    and actionable next steps instead of generic advice
    """

    def __init__(self):
        self.DEFENSE_TEMPLATES = {
            'debt_collection': [
                {
                    'name': 'Statute of Limitations',
                    'viability': 'Strong',
                    'requirements': 'Debt must be older than 4-6 years (varies by state)',
                    'next_step': 'Check date of last payment or acknowledgment',
                    'keywords': ['collection', 'debt', 'owed', 'balance', 'account'],
                    'strength_indicators': ['old debt', 'last payment', 'years ago']
                },
                {
                    'name': 'Lack of Standing/Ownership',
                    'viability': 'Possible',
                    'requirements': 'Plaintiff must prove they own the debt',
                    'next_step': 'Request chain of title and assignment documents',
                    'keywords': ['assignee', 'purchased', 'collection agency'],
                    'strength_indicators': ['debt buyer', 'assigned', 'transferred']
                },
                {
                    'name': 'Already Paid or Settled',
                    'viability': 'Check',
                    'requirements': 'Need payment records showing satisfaction',
                    'next_step': 'Gather bank statements and payment confirmations',
                    'keywords': ['payment', 'settled', 'paid'],
                    'strength_indicators': ['payment made', 'settlement', 'satisfied']
                },
                {
                    'name': 'Wrong Amount Claimed',
                    'viability': 'Possible',
                    'requirements': 'Documentation showing calculation errors',
                    'next_step': 'Request itemized accounting of all charges',
                    'keywords': ['amount', 'balance', 'fees', 'interest'],
                    'strength_indicators': ['inflated', 'fees added', 'incorrect balance']
                },
                {
                    'name': 'Identity Theft/Fraud',
                    'viability': 'Strong',
                    'requirements': 'Evidence debt was fraudulently created',
                    'next_step': 'File police report and gather identity theft documentation',
                    'keywords': ['fraud', 'identity', 'unauthorized'],
                    'strength_indicators': ['not my debt', 'never opened', 'fraud']
                }
            ],
            'eviction': [
                {
                    'name': 'Improper Notice',
                    'viability': 'Strong',
                    'requirements': 'Notice must comply with state requirements',
                    'next_step': 'Review notice for technical defects',
                    'keywords': ['notice', 'eviction', 'quit', 'cure'],
                    'strength_indicators': ['insufficient notice', 'wrong form', 'defective']
                },
                {
                    'name': 'Habitability Issues',
                    'viability': 'Strong',
                    'requirements': 'Documented uninhabitable conditions',
                    'next_step': 'Photograph conditions and report to authorities',
                    'keywords': ['habitability', 'conditions', 'repair', 'maintenance'],
                    'strength_indicators': ['mold', 'heating', 'plumbing', 'unsafe']
                },
                {
                    'name': 'Retaliatory Eviction',
                    'viability': 'Possible',
                    'requirements': 'Eviction followed complaint or exercise of rights',
                    'next_step': 'Document timeline of complaints vs eviction notice',
                    'keywords': ['retaliation', 'complaint', 'rights'],
                    'strength_indicators': ['after complaint', 'retaliation', 'rights']
                },
                {
                    'name': 'Payment Was Tendered',
                    'viability': 'Check',
                    'requirements': 'Evidence payment was offered and refused',
                    'next_step': 'Gather proof of payment attempts',
                    'keywords': ['payment', 'tender', 'refused'],
                    'strength_indicators': ['payment refused', 'tender', 'offered']
                },
                {
                    'name': 'Discrimination',
                    'viability': 'Strong',
                    'requirements': 'Evidence of discriminatory treatment',
                    'next_step': 'Document discriminatory acts and file complaint',
                    'keywords': ['discrimination', 'protected class', 'bias'],
                    'strength_indicators': ['discrimination', 'bias', 'unfair treatment']
                }
            ],
            'criminal': [
                {
                    'name': 'Lack of Probable Cause',
                    'viability': 'Strong',
                    'requirements': 'Insufficient evidence for arrest or search',
                    'next_step': 'Review arrest report and evidence basis',
                    'keywords': ['arrest', 'search', 'probable cause'],
                    'strength_indicators': ['insufficient evidence', 'unlawful', 'improper']
                },
                {
                    'name': 'Self-Defense',
                    'viability': 'Possible',
                    'requirements': 'Reasonable belief of imminent harm',
                    'next_step': 'Document threat and gather witness statements',
                    'keywords': ['self-defense', 'threat', 'protection'],
                    'strength_indicators': ['threatened', 'attacked', 'defending']
                },
                {
                    'name': 'Alibi Defense',
                    'viability': 'Strong',
                    'requirements': 'Verifiable evidence of being elsewhere',
                    'next_step': 'Gather alibi witnesses and documentation',
                    'keywords': ['alibi', 'elsewhere', 'different location'],
                    'strength_indicators': ['was not there', 'different place', 'alibi']
                },
                {
                    'name': 'Mistaken Identity',
                    'viability': 'Possible',
                    'requirements': 'Evidence of misidentification',
                    'next_step': 'Challenge identification procedures',
                    'keywords': ['identity', 'identification', 'mistaken'],
                    'strength_indicators': ['wrong person', 'mistaken', 'misidentified']
                },
                {
                    'name': 'Constitutional Violations',
                    'viability': 'Strong',
                    'requirements': 'Rights violations during investigation',
                    'next_step': 'Document Miranda and other rights violations',
                    'keywords': ['rights', 'miranda', 'constitutional'],
                    'strength_indicators': ['no miranda', 'rights violated', 'illegal']
                }
            ],
            'employment': [
                {
                    'name': 'Wrongful Termination',
                    'viability': 'Possible',
                    'requirements': 'Termination violated employment law',
                    'next_step': 'Review employment contract and company policies',
                    'keywords': ['terminated', 'fired', 'employment'],
                    'strength_indicators': ['wrongful', 'violation', 'improper']
                },
                {
                    'name': 'Discrimination',
                    'viability': 'Strong',
                    'requirements': 'Evidence of protected class discrimination',
                    'next_step': 'File EEOC complaint within 180 days',
                    'keywords': ['discrimination', 'protected class', 'bias'],
                    'strength_indicators': ['discriminated', 'biased', 'unfair treatment']
                },
                {
                    'name': 'Retaliation',
                    'viability': 'Strong',
                    'requirements': 'Adverse action after protected activity',
                    'next_step': 'Document timeline of complaint vs adverse action',
                    'keywords': ['retaliation', 'complaint', 'whistleblower'],
                    'strength_indicators': ['retaliation', 'after complaint', 'whistleblower']
                },
                {
                    'name': 'Wage and Hour Violations',
                    'viability': 'Check',
                    'requirements': 'Documentation of unpaid wages or overtime',
                    'next_step': 'Calculate unpaid wages and gather time records',
                    'keywords': ['wages', 'overtime', 'hours', 'pay'],
                    'strength_indicators': ['unpaid', 'overtime', 'wage violation']
                }
            ],
            'contract_dispute': [
                {
                    'name': 'Breach by Other Party',
                    'viability': 'Check',
                    'requirements': 'Evidence other party failed to perform',
                    'next_step': 'Document other party\'s failures and damages',
                    'keywords': ['breach', 'contract', 'failure', 'perform'],
                    'strength_indicators': ['failed to perform', 'breach', 'violation']
                },
                {
                    'name': 'Impossibility/Frustration',
                    'viability': 'Possible',
                    'requirements': 'Performance became impossible or frustrated',
                    'next_step': 'Document circumstances preventing performance',
                    'keywords': ['impossible', 'frustration', 'circumstances'],
                    'strength_indicators': ['impossible', 'frustrated', 'circumstances']
                },
                {
                    'name': 'Duress/Unconscionability',
                    'viability': 'Possible',
                    'requirements': 'Contract signed under duress or unconscionable',
                    'next_step': 'Document circumstances of contract formation',
                    'keywords': ['duress', 'unconscionable', 'unfair'],
                    'strength_indicators': ['duress', 'forced', 'unconscionable']
                }
            ]
        }

        # Common response deadlines by case type
        self.RESPONSE_DEADLINES = {
            'debt_collection': '20-30 days from service',
            'eviction': '5-10 days from service',
            'criminal': 'Arraignment date',
            'employment': '180 days for EEOC complaint',
            'contract_dispute': '20-30 days from service'
        }

    def analyze_document(self, document_text: str, document_type: str = None) -> Dict[str, Any]:
        """
        Analyze document and provide concrete defense strategies

        Args:
            document_text: Full text of the legal document
            document_type: Type of document (auto-detected if None)

        Returns:
            Analysis with defense strategies and actionable next steps
        """
        try:
            # Auto-detect document type if not provided
            if not document_type:
                document_type = self._detect_document_type(document_text)

            # Extract key information
            key_info = self._extract_key_information(document_text, document_type)

            # Generate defense strategies
            defense_strategies = self._generate_defense_strategies(document_text, document_type)

            # Generate immediate actions
            immediate_actions = self._generate_immediate_actions(document_text, document_type, key_info)

            # Identify information needed
            information_needed = self._identify_information_needed(document_text, document_type)

            # Create summary
            summary = self._create_concise_summary(document_text, document_type, key_info)

            analysis = {
                'document_type': document_type,
                'summary': summary,
                'defense_strategies': defense_strategies,
                'immediate_actions': immediate_actions,
                'information_needed': information_needed,
                'key_dates': key_info.get('dates', []),
                'key_amounts': key_info.get('amounts', []),
                'parties': key_info.get('parties', []),
                'case_number': key_info.get('case_number', ''),
                'court': key_info.get('court', ''),
                'response_deadline': self._calculate_response_deadline(document_text, document_type),
                'urgency_level': self._assess_urgency(document_text, document_type)
            }

            logger.info(f"Document analysis completed for {document_type} with {len(defense_strategies)} defense strategies")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            return self._fallback_analysis(document_text, str(e))

    def _detect_document_type(self, text: str) -> str:
        """Detect document type from content"""
        text_lower = text.lower()

        # Debt collection indicators
        if any(word in text_lower for word in ['collection', 'debt', 'owe', 'balance due', 'creditor']):
            return 'debt_collection'

        # Eviction indicators
        elif any(word in text_lower for word in ['eviction', 'unlawful detainer', 'quit notice', 'tenancy']):
            return 'eviction'

        # Criminal indicators
        elif any(word in text_lower for word in ['criminal', 'arrest', 'charge', 'indictment', 'misdemeanor', 'felony']):
            return 'criminal'

        # Employment indicators
        elif any(word in text_lower for word in ['employment', 'termination', 'discrimination', 'eeoc']):
            return 'employment'

        # Contract dispute indicators
        elif any(word in text_lower for word in ['contract', 'agreement', 'breach', 'performance']):
            return 'contract_dispute'

        # Default to general litigation
        return 'litigation'

    def _extract_key_information(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract key information from document"""
        key_info = {
            'dates': [],
            'amounts': [],
            'parties': [],
            'case_number': '',
            'court': ''
        }

        # Extract dates
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        ]

        for pattern in date_patterns:
            dates = re.findall(pattern, text, re.IGNORECASE)
            key_info['dates'].extend(dates)

        # Extract monetary amounts
        amount_pattern = r'\$[\d,]+\.?\d*'
        amounts = re.findall(amount_pattern, text)
        key_info['amounts'] = amounts

        # Extract case number
        case_patterns = [
            r'Case No\.?\s*:?\s*([A-Z0-9-]+)',
            r'Civil No\.?\s*:?\s*([A-Z0-9-]+)',
            r'Docket No\.?\s*:?\s*([A-Z0-9-]+)'
        ]

        for pattern in case_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                key_info['case_number'] = match.group(1)
                break

        # Extract court information
        court_pattern = r'(?:in the|before the|filed in)\s+([^,\n]+court[^,\n]*)'
        court_match = re.search(court_pattern, text, re.IGNORECASE)
        if court_match:
            key_info['court'] = court_match.group(1).strip()

        return key_info

    def _generate_defense_strategies(self, text: str, document_type: str) -> List[Dict[str, Any]]:
        """Generate specific defense strategies based on document content"""
        strategies = []
        text_lower = text.lower()

        # Get defense templates for this document type
        templates = self.DEFENSE_TEMPLATES.get(document_type, [])

        for template in templates:
            # Calculate strength score based on keywords and indicators
            strength_score = self._calculate_strategy_strength(text_lower, template)

            # Determine viability based on strength score
            if strength_score > 0.7:
                viability = "Strong"
            elif strength_score > 0.4:
                viability = "Possible"
            elif strength_score > 0.2:
                viability = "Check"
            else:
                viability = "Weak"

            # Only include strategies with some potential
            if strength_score > 0.2:
                strategy = {
                    'name': template['name'],
                    'viability': viability,
                    'requirements': template['requirements'],
                    'next_step': template['next_step'],
                    'strength_score': strength_score
                }

                # Add deadline if applicable
                if 'deadline' in template:
                    strategy['deadline'] = template['deadline']

                strategies.append(strategy)

        # Sort by strength score (strongest first)
        strategies.sort(key=lambda x: x['strength_score'], reverse=True)

        # Limit to top 5 strategies
        return strategies[:5]

    def _calculate_strategy_strength(self, text_lower: str, template: Dict[str, Any]) -> float:
        """Calculate strength score for a defense strategy"""
        score = 0.0

        # Base score for keyword matches
        keyword_matches = sum(1 for keyword in template.get('keywords', []) if keyword in text_lower)
        if template.get('keywords'):
            score += (keyword_matches / len(template['keywords'])) * 0.4

        # Bonus for strength indicators
        indicator_matches = sum(1 for indicator in template.get('strength_indicators', []) if indicator in text_lower)
        if template.get('strength_indicators'):
            score += (indicator_matches / len(template['strength_indicators'])) * 0.6

        return min(score, 1.0)

    def _generate_immediate_actions(self, text: str, document_type: str, key_info: Dict[str, Any]) -> List[str]:
        """Generate immediate actionable steps"""
        actions = []

        # Common actions by document type
        action_templates = {
            'debt_collection': [
                'File answer within 20-30 days of service',
                'Request validation of debt from plaintiff',
                'Preserve all payment records and communications',
                'Consider counterclaims for violations of debt collection laws'
            ],
            'eviction': [
                'File response within 5-10 days of service',
                'Document all habitability issues with photos',
                'Gather all lease agreements and payment records',
                'Contact local tenant assistance program'
            ],
            'criminal': [
                'Contact criminal defense attorney immediately',
                'Exercise right to remain silent',
                'Preserve all evidence and witness contact information',
                'Do not discuss case with anyone except attorney'
            ],
            'employment': [
                'File EEOC complaint within 180 days if discrimination',
                'Gather all employment documents and communications',
                'Document timeline of events and witnesses',
                'Calculate damages including lost wages and benefits'
            ],
            'contract_dispute': [
                'File answer within 20-30 days of service',
                'Gather all contract documents and communications',
                'Document any performance by other party',
                'Calculate damages and consider counterclaims'
            ]
        }

        # Get base actions for document type
        base_actions = action_templates.get(document_type, [
            'File response by required deadline',
            'Gather all relevant documents',
            'Consider consulting with attorney',
            'Preserve all evidence and communications'
        ])

        actions.extend(base_actions)

        # Add specific deadline if found
        response_deadline = self._calculate_response_deadline(text, document_type)
        if response_deadline and response_deadline != 'Unknown':
            actions.insert(0, f'File response by {response_deadline}')

        return actions[:5]  # Limit to 5 most important actions

    def _identify_information_needed(self, text: str, document_type: str) -> List[str]:
        """Identify specific information needed to strengthen case"""
        info_templates = {
            'debt_collection': [
                'Original signed contract or credit agreement',
                'Complete payment history and statements',
                'Chain of title showing debt ownership',
                'Communication records with creditor'
            ],
            'eviction': [
                'Original lease agreement',
                'Payment receipts and bank records',
                'Photos of property conditions',
                'Communication with landlord'
            ],
            'criminal': [
                'Police reports and arrest records',
                'Witness contact information',
                'Surveillance footage if available',
                'Medical records if applicable'
            ],
            'employment': [
                'Employment contract and handbook',
                'Performance evaluations',
                'Communication with supervisors',
                'Witness statements from coworkers'
            ],
            'contract_dispute': [
                'Original contract and amendments',
                'Performance documentation',
                'Communication between parties',
                'Damage calculations and receipts'
            ]
        }

        return info_templates.get(document_type, [
            'All relevant contracts and agreements',
            'Communication records between parties',
            'Financial records and payment history',
            'Witness contact information'
        ])

    def _create_concise_summary(self, text: str, document_type: str, key_info: Dict[str, Any]) -> str:
        """Create 2-3 sentence summary"""

        # Extract key elements for summary
        case_number = key_info.get('case_number', '')
        court = key_info.get('court', '')
        amounts = key_info.get('amounts', [])

        summaries = {
            'debt_collection': f"Debt collection lawsuit seeking {amounts[0] if amounts else 'unspecified amount'}. " +
                             f"Case filed in {court if court else 'court'}. " +
                             "Response required within 20-30 days to avoid default judgment.",

            'eviction': f"Eviction proceeding {f'Case {case_number}' if case_number else ''} filed in {court if court else 'court'}. " +
                       "Tenant must respond within 5-10 days to contest eviction. " +
                       "Failure to respond may result in immediate eviction order.",

            'criminal': f"Criminal charges filed {f'Case {case_number}' if case_number else ''} in {court if court else 'court'}. " +
                       "Defendant has right to attorney and should not discuss case without counsel. " +
                       "Arraignment and plea required at next court date.",

            'employment': f"Employment dispute involving termination or discrimination. " +
                         "EEOC complaint must be filed within 180 days for discrimination claims. " +
                         "Gather all employment records and document timeline of events.",

            'contract_dispute': f"Contract dispute {f'Case {case_number}' if case_number else ''} seeking {amounts[0] if amounts else 'damages'}. " +
                               f"Filed in {court if court else 'court'}. " +
                               "Response required within 20-30 days to avoid default judgment."
        }

        return summaries.get(document_type, "Legal proceeding requiring immediate attention. Response deadline critical to avoid default. Gather all relevant documents and consider legal counsel.")

    def _calculate_response_deadline(self, text: str, document_type: str) -> str:
        """Calculate response deadline"""
        # Look for specific deadlines in text
        deadline_patterns = [
            r'within\s+(\d+)\s+days',
            r'by\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'on or before\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})'
        ]

        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # Default deadlines by case type
        return self.RESPONSE_DEADLINES.get(document_type, 'Check local rules')

    def _assess_urgency(self, text: str, document_type: str) -> str:
        """Assess urgency level"""
        text_lower = text.lower()

        # High urgency indicators
        high_urgency = ['default', 'immediate', 'emergency', 'eviction', 'arrest']
        if any(word in text_lower for word in high_urgency):
            return 'High'

        # Medium urgency indicators
        medium_urgency = ['lawsuit', 'complaint', 'summons', 'notice']
        if any(word in text_lower for word in medium_urgency):
            return 'Medium'

        return 'Low'

    def _fallback_analysis(self, text: str, error: str) -> Dict[str, Any]:
        """Fallback analysis when main analysis fails"""
        return {
            'document_type': 'unknown',
            'summary': 'Document analysis failed. Manual review required.',
            'defense_strategies': [
                {
                    'name': 'General Response',
                    'viability': 'Check',
                    'requirements': 'File timely response to avoid default',
                    'next_step': 'Consult with attorney immediately',
                    'strength_score': 0.5
                }
            ],
            'immediate_actions': [
                'Consult with qualified attorney immediately',
                'File response by deadline to avoid default',
                'Gather all relevant documents',
                'Do not ignore legal deadlines'
            ],
            'information_needed': [
                'All legal documents received',
                'Timeline of events',
                'Relevant contracts or agreements',
                'Communication records'
            ],
            'key_dates': [],
            'key_amounts': [],
            'parties': [],
            'case_number': '',
            'court': '',
            'response_deadline': 'Check immediately',
            'urgency_level': 'High',
            'error': error
        }

# Create singleton instance
document_analyzer = DocumentAnalyzer()

def analyze_document(document_text: str, document_type: str = None) -> Dict[str, Any]:
    """
    Main entry point for document analysis

    Args:
        document_text: Full text of the legal document
        document_type: Optional document type (auto-detected if None)

    Returns:
        Comprehensive analysis with defense strategies and next steps
    """
    return document_analyzer.analyze_document(document_text, document_type)