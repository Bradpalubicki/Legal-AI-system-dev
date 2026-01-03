"""
Adversarial Simulation Service
Generates opposing counsel arguments and counter-rebuttals during defense interview
"""

import os
import json
import uuid
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import anthropic
from openai import OpenAI

logger = logging.getLogger(__name__)

# AI Model Configuration
CLAUDE_SONNET_MODEL = 'claude-sonnet-4-5-20250929'  # For counter-argument generation
GPT_4O_MINI_MODEL = 'gpt-4o-mini'  # Cost-effective for rebuttals


class AdversarialSimulationService:
    """
    Runs adversarial analysis as opposing counsel.
    Generates counter-arguments, rebuttals, and identifies case weaknesses.
    """

    def __init__(self, db: Session):
        self.db = db
        self.claude_client = None
        self.openai_client = None

        # Initialize Claude client
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            self.claude_client = anthropic.Anthropic(
                api_key=anthropic_key,
                timeout=120.0
            )

        # Initialize OpenAI client
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)

    async def start_simulation(
        self,
        defense_session_id: str,
        user_id: str,
        case_type: str,
        max_counter_arguments: int = 3
    ) -> Dict[str, Any]:
        """
        Start a new adversarial simulation linked to a defense session.

        Args:
            defense_session_id: The defense session this simulation is for
            user_id: The user running the simulation
            case_type: Type of case (debt_collection, eviction, etc.)
            max_counter_arguments: Maximum counter-arguments based on tier

        Returns:
            Dict with simulation_id and status
        """
        from app.models.adversarial import AdversarialSimulation

        simulation = AdversarialSimulation(
            id=str(uuid.uuid4()),
            defense_session_id=defense_session_id,
            user_id=user_id,
            status='pending',
            progress=0,
            case_type=case_type,
            collected_facts={},
            max_counter_arguments=max_counter_arguments,
            created_at=datetime.utcnow()
        )

        self.db.add(simulation)
        self.db.commit()
        self.db.refresh(simulation)

        logger.info(f"Created adversarial simulation {simulation.id} for defense session {defense_session_id}")

        return {
            "simulation_id": simulation.id,
            "status": "pending",
            "max_counter_arguments": max_counter_arguments
        }

    async def process_incremental_update(
        self,
        simulation_id: str,
        new_facts: Dict[str, Any],
        question_key: str
    ) -> Dict[str, Any]:
        """
        Process new facts as user provides them during interview.
        Updates collected facts and triggers counter-argument analysis.

        Args:
            simulation_id: The simulation to update
            new_facts: New facts from the latest interview answer
            question_key: The question key that was just answered

        Returns:
            Status update with progress
        """
        from app.models.adversarial import AdversarialSimulation

        simulation = self.db.query(AdversarialSimulation).filter(
            AdversarialSimulation.id == simulation_id
        ).first()

        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")

        # Update collected facts
        collected_facts = simulation.collected_facts or {}
        collected_facts[question_key] = new_facts
        simulation.collected_facts = collected_facts

        # Update status to running if this is first update
        if simulation.status == 'pending':
            simulation.status = 'running'
            simulation.started_at = datetime.utcnow()

        # Calculate progress based on facts collected
        # Rough estimate: 5 questions typical, each adds 20%
        estimated_progress = min(len(collected_facts) * 20, 95)
        simulation.progress = estimated_progress

        simulation.updated_at = datetime.utcnow()
        self.db.commit()

        return {
            "simulation_id": simulation_id,
            "status": simulation.status,
            "progress": simulation.progress,
            "facts_collected": len(collected_facts)
        }

    async def generate_counter_arguments(
        self,
        facts: Dict[str, Any],
        case_type: str,
        max_arguments: int = 3
    ) -> List[Dict[str, Any]]:
        """
        AI generates opposing party's likely arguments.
        Uses Claude Sonnet for high-quality adversarial analysis.

        Args:
            facts: Collected facts from the interview
            case_type: Type of legal case
            max_arguments: Maximum number of counter-arguments to generate

        Returns:
            List of counter-argument dictionaries
        """
        if not self.claude_client:
            logger.error("Claude client not available for counter-argument generation")
            return self._get_template_counter_arguments(case_type, max_arguments)

        facts_text = self._format_facts_for_prompt(facts)

        prompt = f"""You are opposing counsel in a {case_type} case. Your job is to find every weakness,
inconsistency, and vulnerability in the defendant's position.

Based on these facts provided by the defendant:
{facts_text}

Generate the {max_arguments} strongest arguments the opposing party (plaintiff/creditor/landlord)
will likely make. For each argument:

Return ONLY valid JSON in this exact format:
{{
    "counter_arguments": [
        {{
            "argument_title": "Concise title of the argument",
            "argument_description": "Detailed explanation of why this argument hurts the defendant",
            "legal_basis": "Legal foundation for this argument (statute, case law, contract provision)",
            "likelihood": "high" | "medium" | "low",
            "likelihood_score": 0-100,
            "likelihood_reasoning": "Why this argument is likely to be raised",
            "category": "procedural" | "substantive" | "evidentiary" | "credibility",
            "evidence_to_support": ["Evidence", "items", "that", "strengthen", "this", "argument"]
        }}
    ]
}}

CRITICAL INSTRUCTIONS:
1. Be adversarial but realistic - focus on arguments actually used in {case_type} cases
2. Use the defendant's OWN statements against them where possible
3. Identify timeline inconsistencies, missing evidence, and credibility issues
4. Prioritize by likelihood of being raised (high likelihood = definite argument)
5. Reference specific facts the defendant provided that create vulnerability

Return ONLY the JSON, no markdown formatting or additional text."""

        try:
            message = self.claude_client.messages.create(
                model=CLAUDE_SONNET_MODEL,
                max_tokens=3000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse JSON response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            result = json.loads(response_text)
            counter_arguments = result.get("counter_arguments", [])

            logger.info(f"Generated {len(counter_arguments)} counter-arguments for {case_type}")
            return counter_arguments[:max_arguments]

        except Exception as e:
            logger.error(f"Error generating counter-arguments: {str(e)}")
            return self._get_template_counter_arguments(case_type, max_arguments)

    async def generate_rebuttals(
        self,
        counter_argument: Dict[str, Any],
        user_facts: Dict[str, Any],
        case_type: str
    ) -> List[Dict[str, Any]]:
        """
        Generate rebuttals for a counter-argument.
        Uses GPT-4o-mini for cost-effective rebuttal generation.

        Args:
            counter_argument: The counter-argument to rebut
            user_facts: Facts from the defendant's interview
            case_type: Type of legal case

        Returns:
            List of rebuttal dictionaries with counter-rebuttals (level 3)
        """
        if not self.openai_client:
            logger.error("OpenAI client not available for rebuttal generation")
            return self._get_template_rebuttals(counter_argument)

        facts_text = self._format_facts_for_prompt(user_facts)

        prompt = f"""The opposing party in a {case_type} case will argue:

ARGUMENT: {counter_argument.get('argument_title')}
DESCRIPTION: {counter_argument.get('argument_description')}
LEGAL BASIS: {counter_argument.get('legal_basis', 'Not specified')}

Based on the defendant's facts:
{facts_text}

Generate 2-3 potential rebuttals the defendant could use. For each rebuttal, also generate
1-2 counter-rebuttals (how opposing counsel might respond to the rebuttal).

Return ONLY valid JSON in this exact format:
{{
    "rebuttals": [
        {{
            "id": "rebuttal_1",
            "rebuttal_text": "The core rebuttal argument",
            "evidence_needed": ["Evidence", "to", "support", "this"],
            "strength": "strong" | "moderate" | "weak",
            "counter_rebuttals": [
                {{
                    "id": "counter_1",
                    "counter_text": "How opposing counsel will respond to this rebuttal",
                    "your_response": "How defendant can counter their response"
                }}
            ]
        }}
    ]
}}

CRITICAL INSTRUCTIONS:
1. Focus on practical, realistic rebuttals that could work in court
2. Reference specific facts the defendant provided that support the rebuttal
3. Counter-rebuttals should anticipate opposing counsel's likely response
4. Provide concrete evidence suggestions, not vague "documentation"

Return ONLY the JSON, no markdown formatting or additional text."""

        try:
            response = self.openai_client.chat.completions.create(
                model=GPT_4O_MINI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )

            response_text = response.choices[0].message.content

            # Parse JSON response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            result = json.loads(response_text)
            rebuttals = result.get("rebuttals", [])

            logger.info(f"Generated {len(rebuttals)} rebuttals for counter-argument")
            return rebuttals

        except Exception as e:
            logger.error(f"Error generating rebuttals: {str(e)}")
            return self._get_template_rebuttals(counter_argument)

    async def identify_weaknesses(
        self,
        user_facts: Dict[str, Any],
        case_type: str
    ) -> List[Dict[str, Any]]:
        """
        Identify gaps/weaknesses in user's story.

        Args:
            user_facts: Facts from the defendant's interview
            case_type: Type of legal case

        Returns:
            List of weakness dictionaries
        """
        if not self.claude_client:
            logger.error("Claude client not available for weakness analysis")
            return []

        facts_text = self._format_facts_for_prompt(user_facts)

        prompt = f"""Analyze the defendant's narrative for gaps, inconsistencies, and vulnerabilities:

CASE TYPE: {case_type}

DEFENDANT'S FACTS:
{facts_text}

Identify weaknesses that opposing counsel will exploit:

Return ONLY valid JSON in this exact format:
{{
    "weaknesses": [
        {{
            "title": "Brief weakness title",
            "description": "What's missing or problematic",
            "category": "missing_info" | "timeline_gap" | "unsupported_claim" | "credibility" | "procedural",
            "severity": "critical" | "significant" | "minor",
            "remedy": "What information/evidence would address this weakness"
        }}
    ]
}}

Focus on:
1. Missing information opposing counsel will exploit
2. Timeline gaps or inconsistencies
3. Unsupported claims (assertions without evidence)
4. Potential credibility issues
5. Procedural vulnerabilities

Return ONLY the JSON, no markdown formatting or additional text."""

        try:
            message = self.claude_client.messages.create(
                model=CLAUDE_SONNET_MODEL,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse JSON response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            result = json.loads(response_text)
            weaknesses = result.get("weaknesses", [])

            logger.info(f"Identified {len(weaknesses)} weaknesses")
            return weaknesses

        except Exception as e:
            logger.error(f"Error identifying weaknesses: {str(e)}")
            return []

    async def finalize_simulation(
        self,
        simulation_id: str,
        include_weaknesses: bool = False
    ) -> Dict[str, Any]:
        """
        Complete the adversarial analysis and return full counter-argument matrix.

        Args:
            simulation_id: The simulation to finalize
            include_weaknesses: Whether to include weakness analysis (tier-dependent)

        Returns:
            Complete simulation results
        """
        from app.models.adversarial import AdversarialSimulation, CounterArgument

        simulation = self.db.query(AdversarialSimulation).filter(
            AdversarialSimulation.id == simulation_id
        ).first()

        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")

        try:
            # Generate counter-arguments
            counter_arguments = await self.generate_counter_arguments(
                simulation.collected_facts,
                simulation.case_type,
                simulation.max_counter_arguments
            )

            # Generate rebuttals for each counter-argument
            for i, counter_arg in enumerate(counter_arguments):
                rebuttals = await self.generate_rebuttals(
                    counter_arg,
                    simulation.collected_facts,
                    simulation.case_type
                )
                counter_arg['rebuttals'] = rebuttals

                # Save counter-argument to database
                db_counter = CounterArgument(
                    id=str(uuid.uuid4()),
                    simulation_id=simulation_id,
                    argument_title=counter_arg.get('argument_title', ''),
                    argument_description=counter_arg.get('argument_description', ''),
                    legal_basis=counter_arg.get('legal_basis'),
                    likelihood=counter_arg.get('likelihood', 'medium'),
                    likelihood_score=counter_arg.get('likelihood_score', 50),
                    likelihood_reasoning=counter_arg.get('likelihood_reasoning'),
                    category=counter_arg.get('category', 'substantive'),
                    evidence_to_support=counter_arg.get('evidence_to_support', []),
                    rebuttals=rebuttals,
                    created_at=datetime.utcnow()
                )
                self.db.add(db_counter)

                # Update progress
                simulation.progress = min(50 + (i + 1) * (40 // len(counter_arguments)), 90)
                self.db.commit()

            # Identify weaknesses if enabled
            weaknesses = []
            if include_weaknesses:
                weaknesses = await self.identify_weaknesses(
                    simulation.collected_facts,
                    simulation.case_type
                )

            # Calculate overall case strength
            high_likelihood = sum(1 for c in counter_arguments if c.get('likelihood') == 'high')
            medium_likelihood = sum(1 for c in counter_arguments if c.get('likelihood') == 'medium')

            if high_likelihood >= 3:
                overall_strength = "weak"
            elif high_likelihood >= 2 or (high_likelihood >= 1 and medium_likelihood >= 2):
                overall_strength = "moderate"
            else:
                overall_strength = "strong"

            # Generate recommendations
            recommendations = self._generate_recommendations(counter_arguments, weaknesses, simulation.case_type)

            # Update simulation with results
            simulation.status = 'completed'
            simulation.progress = 100
            simulation.completed_at = datetime.utcnow()
            simulation.counter_arguments_summary = [
                {
                    "title": c.get('argument_title'),
                    "likelihood": c.get('likelihood'),
                    "category": c.get('category')
                } for c in counter_arguments
            ]
            simulation.weaknesses = weaknesses
            simulation.overall_strength = overall_strength
            simulation.recommendations = recommendations

            self.db.commit()

            logger.info(f"Finalized simulation {simulation_id} with {len(counter_arguments)} counter-arguments")

            return {
                "simulation_id": simulation_id,
                "status": "completed",
                "counter_arguments": counter_arguments,
                "weaknesses": weaknesses,
                "overall_strength": overall_strength,
                "recommendations": recommendations,
                "case_type": simulation.case_type
            }

        except Exception as e:
            logger.error(f"Error finalizing simulation: {str(e)}")
            simulation.status = 'failed'
            simulation.error_message = str(e)
            self.db.commit()
            raise

    def _format_facts_for_prompt(self, facts: Dict[str, Any]) -> str:
        """Format collected facts into a readable prompt section."""
        if not facts:
            return "No facts provided yet."

        lines = []
        for key, value in facts.items():
            if isinstance(value, dict):
                lines.append(f"- {key}: {json.dumps(value)}")
            else:
                lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _generate_recommendations(
        self,
        counter_arguments: List[Dict[str, Any]],
        weaknesses: List[Dict[str, Any]],
        case_type: str
    ) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Based on high-likelihood counter-arguments
        high_likelihood = [c for c in counter_arguments if c.get('likelihood') == 'high']
        for counter in high_likelihood[:2]:
            recommendations.append(f"Prepare response for: {counter.get('argument_title')}")

        # Based on weaknesses
        critical_weaknesses = [w for w in weaknesses if w.get('severity') == 'critical']
        for weakness in critical_weaknesses[:2]:
            recommendations.append(f"Address weakness: {weakness.get('remedy')}")

        # Case-type specific recommendations
        if case_type == 'debt_collection':
            recommendations.append("Request debt validation and chain of ownership documentation")
        elif case_type == 'eviction':
            recommendations.append("Document all property conditions with timestamped photos")
        elif case_type == 'foreclosure':
            recommendations.append("Request complete payment history from servicer")

        return recommendations[:5]

    def _get_template_counter_arguments(self, case_type: str, max_arguments: int) -> List[Dict[str, Any]]:
        """Fallback template counter-arguments when AI is unavailable."""
        templates = {
            'debt_collection': [
                {
                    "argument_title": "Valid Debt Obligation",
                    "argument_description": "Defendant signed a valid contract creating a legal obligation to repay",
                    "legal_basis": "Contract law - mutual assent and consideration",
                    "likelihood": "high",
                    "likelihood_score": 85,
                    "likelihood_reasoning": "Standard argument in every debt collection case",
                    "category": "substantive",
                    "evidence_to_support": ["Original signed contract", "Account statements", "Payment history"]
                },
                {
                    "argument_title": "Documented Default",
                    "argument_description": "Clear evidence of non-payment demonstrates breach of contract",
                    "legal_basis": "Breach of contract",
                    "likelihood": "high",
                    "likelihood_score": 80,
                    "likelihood_reasoning": "Payment records will show missed payments",
                    "category": "evidentiary",
                    "evidence_to_support": ["Payment records", "Account statements", "Demand letters"]
                },
                {
                    "argument_title": "Timely Filing",
                    "argument_description": "Lawsuit filed within statute of limitations period",
                    "legal_basis": "Statute of limitations compliance",
                    "likelihood": "medium",
                    "likelihood_score": 60,
                    "likelihood_reasoning": "Will counter any SOL defense with filing date evidence",
                    "category": "procedural",
                    "evidence_to_support": ["Filing date", "Last payment date", "State SOL statute"]
                }
            ],
            'eviction': [
                {
                    "argument_title": "Non-Payment of Rent",
                    "argument_description": "Tenant failed to pay agreed rent creating grounds for eviction",
                    "legal_basis": "Lease agreement breach",
                    "likelihood": "high",
                    "likelihood_score": 85,
                    "likelihood_reasoning": "Primary eviction ground in most cases",
                    "category": "substantive",
                    "evidence_to_support": ["Lease agreement", "Rent ledger", "Payment records"]
                },
                {
                    "argument_title": "Proper Notice Given",
                    "argument_description": "All required notices were properly served",
                    "legal_basis": "State landlord-tenant law",
                    "likelihood": "high",
                    "likelihood_score": 75,
                    "likelihood_reasoning": "Will defend against improper notice claims",
                    "category": "procedural",
                    "evidence_to_support": ["Notice copies", "Proof of service", "Timeline documentation"]
                }
            ]
        }

        case_templates = templates.get(case_type, templates.get('debt_collection'))
        return case_templates[:max_arguments]

    def _get_template_rebuttals(self, counter_argument: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback template rebuttals when AI is unavailable."""
        return [
            {
                "id": "rebuttal_1",
                "rebuttal_text": "Challenge the evidence supporting this argument",
                "evidence_needed": ["Counter-documentation", "Witness testimony"],
                "strength": "moderate",
                "counter_rebuttals": [
                    {
                        "id": "counter_1",
                        "counter_text": "Opposing counsel will present additional documentation",
                        "your_response": "Request authentication of all documents"
                    }
                ]
            },
            {
                "id": "rebuttal_2",
                "rebuttal_text": "Raise procedural objections to this argument",
                "evidence_needed": ["Procedural rules", "Timeline documentation"],
                "strength": "moderate",
                "counter_rebuttals": [
                    {
                        "id": "counter_1",
                        "counter_text": "Opposing counsel will argue substantial compliance",
                        "your_response": "Document specific procedural failures"
                    }
                ]
            }
        ]


# Singleton instance for reuse
_service_instance = None


def get_adversarial_service(db: Session) -> AdversarialSimulationService:
    """Get or create adversarial simulation service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = AdversarialSimulationService(db)
    else:
        _service_instance.db = db  # Update session
    return _service_instance
