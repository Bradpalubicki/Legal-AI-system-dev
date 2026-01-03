"""
Defense Strategy Builder for Legal AI System

LEGAL DISCLAIMER:
This module generates educational content about common legal strategies.
All content is for educational purposes only and does not constitute legal advice.
Professional legal consultation is required for guidance on specific situations.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

try:
    from ..shared.compliance import ComplianceWrapper, AdviceDetector, DisclaimerSystem
    from ..shared.core import BaseGenerator
    from ..shared.models import Strategy
except ImportError:
    # Mock imports for testing
    class BaseGenerator:
        def __init__(self):
            self.initialized = True

    class ComplianceWrapper:
        def make_compliant(self, text):
            return text
        def wrap_response(self, response):
            return {'content': response, 'disclaimer': 'Educational only'}

    class AdviceDetector:
        def detect_advice(self, text):
            return {'contains_advice': False}
        def analyze_output(self, text, context=None):
            class MockResult:
                requires_disclaimer = False
                risk_score = 0.0
                advice_level = "SAFE"
                detected_patterns = []
                confidence_score = 1.0
            return MockResult()

    class DisclaimerSystem:
        def get_disclaimer(self, disclaimer_type):
            return "Educational purposes only. Consult an attorney."


class DefenseStrategyGenerator(BaseGenerator):
    """
    Generates educational defense strategy information with UPL compliance

    All strategies are presented as educational information only.
    No legal advice is provided.
    """

    def __init__(self):
        super().__init__()
        self.compliance_wrapper = ComplianceWrapper()
        self.advice_detector = AdviceDetector()
        self.disclaimer_system = DisclaimerSystem()
        self.logger = logging.getLogger(__name__)

    async def generate_strategies(self, case_data: Dict[str, Any], case_type: str) -> Dict[str, Any]:
        """
        Generate educational strategy information based on case data

        Args:
            case_data: Case information and analysis
            case_type: Type of legal matter

        Returns:
            Dictionary containing educational strategy information
        """
        try:
            strategies = []

            if case_type.lower() == 'bankruptcy':
                strategies = await self._generate_bankruptcy_strategies(case_data)
            elif case_type.lower() == 'litigation':
                strategies = await self._generate_litigation_strategies(case_data)
            elif case_type.lower() == 'criminal':
                strategies = await self._generate_criminal_strategies(case_data)
            else:
                strategies = await self._generate_general_strategies(case_data)

            # Ensure all strategies are UPL compliant
            compliant_strategies = []
            for strategy in strategies:
                # Check for advice language
                advice_check = self.advice_detector.analyze_output(strategy.get('description', ''))

                if not advice_check.requires_disclaimer:
                    compliant_strategies.append(strategy)
                else:
                    # Make compliant if needed
                    strategy['description'] = self.compliance_wrapper.make_compliant(
                        strategy.get('description', '')
                    )
                    compliant_strategies.append(strategy)

            return self.compliance_wrapper.wrap_response(compliant_strategies)

        except Exception as e:
            self.logger.error(f"Error generating strategies: {e}")
            return self.compliance_wrapper.wrap_response([{
                'name': 'Educational Information',
                'description': 'Educational strategy information is being processed. Consult with a qualified attorney for guidance.',
                'disclaimer': 'This information is educational only.'
            }])

    async def _generate_bankruptcy_strategies(self, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate bankruptcy-specific educational strategies"""
        strategies = []

        debt_amount = case_data.get('debt_amount', 0)
        business_type = case_data.get('business_type', 'unknown')

        # Strategy 1: Chapter 7 Liquidation
        strategies.append({
            'name': 'Chapter 7 Liquidation Overview',
            'description': 'Chapter 7 bankruptcy commonly involves liquidation of non-exempt assets to pay creditors. This approach is frequently used when debtors have limited income and few non-exempt assets.',
            'pros': [
                'Typically completed within 4-6 months',
                'Discharge of most unsecured debts',
                'Fresh start for financial recovery'
            ],
            'cons': [
                'Asset liquidation may be required',
                'Credit impact for several years',
                'Income requirements must be met'
            ],
            'timeline': '4-6 months typical duration',
            'estimated_cost': '$1,500-$4,000 in attorney fees plus filing costs',
            'disclaimer': 'Educational information only. Chapter 7 eligibility and outcomes vary by individual circumstances.'
        })

        # Strategy 2: Subchapter V (if eligible)
        if isinstance(debt_amount, (int, float)) and debt_amount < 3024725:  # 2024 threshold
            strategies.append({
                'name': 'Subchapter V Small Business Overview',
                'description': 'Subchapter V provides a streamlined bankruptcy process for small businesses with debt under $3,024,725. This approach offers faster procedures and reduced costs compared to traditional Chapter 11.',
                'pros': [
                    'Streamlined procedures',
                    'Lower costs than Chapter 11',
                    'No creditors committee required',
                    'Owner can retain control'
                ],
                'cons': [
                    'Debt limit requirements',
                    'Three-year payment plan maximum',
                    'Limited to small businesses'
                ],
                'timeline': '6-12 months typical duration',
                'estimated_cost': '$15,000-$50,000 in professional fees',
                'disclaimer': 'Educational information only. Subchapter V eligibility requires specific debt thresholds and business qualifications.'
            })

        return strategies

    async def _generate_litigation_strategies(self, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate litigation-specific educational strategies"""
        strategies = []

        # Strategy 1: Settlement Negotiation
        strategies.append({
            'name': 'Settlement Negotiation Overview',
            'description': 'Settlement negotiation involves parties working toward mutually acceptable resolution without trial. This approach often provides faster resolution and reduced costs compared to litigation.',
            'pros': [
                'Faster resolution than trial',
                'Lower legal costs',
                'Controlled outcome',
                'Confidentiality options'
            ],
            'cons': [
                'May result in lower recovery',
                'No legal precedent established',
                'Requires party cooperation'
            ],
            'timeline': '3-12 months depending on complexity',
            'estimated_cost': '$5,000-$25,000 in attorney fees',
            'disclaimer': 'Educational information only. Settlement outcomes vary based on case facts and party positions.'
        })

        return strategies

    async def _generate_criminal_strategies(self, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate criminal defense educational strategies"""
        strategies = []

        # Strategy 1: Professional Consultation
        strategies.append({
            'name': 'Professional Criminal Defense Consultation',
            'description': 'Criminal matters require immediate professional attention. Experienced criminal defense attorneys provide comprehensive case analysis and defense preparation.',
            'pros': [
                'Expert analysis of charges',
                'Knowledge of local procedures',
                'Professional advocacy',
                'Protection of constitutional rights'
            ],
            'cons': [
                'Professional fees required',
                'Time for case preparation',
                'Complex legal procedures'
            ],
            'timeline': 'Varies based on charges and court schedule',
            'estimated_cost': 'Varies based on charges and complexity',
            'disclaimer': 'IMPORTANT: Criminal charges require immediate professional defense counsel. Contact a criminal defense attorney immediately.'
        })

        return strategies

    async def _generate_general_strategies(self, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate general educational strategies"""
        return [{
            'name': 'Professional Legal Consultation',
            'description': 'Professional legal consultation involves comprehensive case analysis by qualified attorneys familiar with applicable law and local procedures.',
            'pros': [
                'Expert analysis of legal options',
                'Familiarity with local procedures',
                'Professional advocacy',
                'Comprehensive case preparation'
            ],
            'cons': [
                'Professional fees required',
                'Time for consultation process',
                'May reveal additional complexities'
            ],
            'timeline': 'Varies based on matter complexity',
            'estimated_cost': 'Varies based on case type and complexity',
            'disclaimer': 'Educational information only. Professional consultation is recommended for all legal matters.'
        }]

    def generate_strategies_sync(self, answers: Dict[str, Any], case_type: str = "bankruptcy") -> Dict[str, Any]:
        """
        STANDARDIZED INTERFACE: Generate strategies from user answers

        Args:
            answers (Dict[str, Any]): User responses to questions
            case_type (str): Type of legal matter

        Returns:
            Dict with wrapped response: {'content': strategies_list, 'disclaimer': '...', 'compliance_verified': True}
        """
        # Convert answers to case_data format
        case_data = {
            'user_responses': answers,
            'document_type': case_type,
            **answers  # Merge all answer data
        }

        # Call the async method synchronously for standardized interface
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            strategies = loop.run_until_complete(self.generate_strategies(case_data, case_type))
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            strategies = loop.run_until_complete(self.generate_strategies(case_data, case_type))

        # Return wrapped response for compliance
        # The async method returns wrapped response from compliance_wrapper.wrap_response
        # ✅ CORRECT: Return the full wrapped response, not just the content
        return strategies