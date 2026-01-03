"""
Attorney Briefing Service
Generates strategic summaries, talking points, and actionable intelligence
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


# ============================================================================
# ATTORNEY BRIEFING GENERATOR
# ============================================================================

class AttorneyBriefingGenerator:
    """
    Generates comprehensive briefing documents for attorneys
    """

    @staticmethod
    def generate_strategic_summary(
        case_data: Dict[str, Any],
        events: List[Dict[str, Any]],
        parties: List[Dict[str, Any]],
        assets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate strategic summary of case status and key issues
        """
        # Identify upcoming critical deadlines
        upcoming_deadlines = [
            e for e in events
            if e.get('event_type') == 'deadline'
            and e.get('event_date', datetime.max) > datetime.utcnow()
        ][:5]

        # Identify decision points
        decision_points = AttorneyBriefingGenerator._identify_decision_points(events, case_data)

        # Assess risk factors
        risk_factors = AttorneyBriefingGenerator._assess_risk_factors(case_data, events, parties)

        # Generate alternative scenarios
        scenarios = AttorneyBriefingGenerator._generate_scenarios(case_data, assets, parties)

        return {
            "case_overview": {
                "case_number": case_data.get('case_number'),
                "case_name": case_data.get('case_name'),
                "current_phase": case_data.get('current_phase'),
                "status": case_data.get('status'),
                "days_since_filing": (datetime.utcnow() - case_data.get('filing_date', datetime.utcnow())).days
            },
            "key_upcoming_deadlines": [
                {
                    "title": d['title'],
                    "date": d['event_date'],
                    "days_until": (d['event_date'] - datetime.utcnow()).days,
                    "priority": d.get('priority_level', 3)
                }
                for d in upcoming_deadlines
            ],
            "decision_points_requiring_input": decision_points,
            "risk_factors_and_mitigation": risk_factors,
            "alternative_scenarios": scenarios,
            "total_asset_value": sum(float(a.get('estimated_value', 0)) for a in assets),
            "total_parties": len(parties),
            "critical_path_events": len([e for e in events if e.get('is_critical_path')])
        }

    @staticmethod
    def _identify_decision_points(
        events: List[Dict[str, Any]],
        case_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify key decision points requiring attorney input
        """
        decision_points = []

        # Upcoming hearings require preparation decisions
        upcoming_hearings = [
            e for e in events
            if e.get('event_type') == 'hearing'
            and e.get('event_date', datetime.max) > datetime.utcnow()
            and e.get('event_date', datetime.max) < datetime.utcnow() + timedelta(days=30)
        ]

        for hearing in upcoming_hearings:
            decision_points.append({
                "type": "hearing_preparation",
                "description": f"Prepare for {hearing['title']}",
                "deadline": hearing['event_date'],
                "decisions_needed": [
                    "Witness list and preparation",
                    "Exhibit selection and organization",
                    "Legal arguments and authorities",
                    "Settlement positioning"
                ],
                "urgency": "HIGH" if (hearing['event_date'] - datetime.utcnow()).days < 7 else "MEDIUM"
            })

        # Pending objections require response decisions
        pending_objections = [
            e for e in events
            if e.get('event_type') == 'objection'
            and e.get('status') == 'pending'
        ]

        for obj in pending_objections:
            decision_points.append({
                "type": "objection_response",
                "description": f"Respond to {obj['title']}",
                "deadline": obj.get('response_deadline'),
                "decisions_needed": [
                    "Whether to oppose or consent",
                    "Strength of legal grounds",
                    "Settlement/negotiation options",
                    "Discovery needed for response"
                ],
                "urgency": "URGENT"
            })

        # Case phase transitions
        if case_data.get('current_phase') in ['discovery', 'pre_trial']:
            decision_points.append({
                "type": "phase_transition",
                "description": "Prepare for next case phase",
                "decisions_needed": [
                    "Motion practice strategy",
                    "Settlement vs. trial decision",
                    "Resource allocation",
                    "Expert witness retention"
                ],
                "urgency": "MEDIUM"
            })

        return decision_points

    @staticmethod
    def _assess_risk_factors(
        case_data: Dict[str, Any],
        events: List[Dict[str, Any]],
        parties: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Assess risk factors and suggest mitigation strategies
        """
        risk_factors = []

        # Deadline risks
        overdue_deadlines = [
            e for e in events
            if e.get('event_type') == 'deadline'
            and e.get('event_date', datetime.min) < datetime.utcnow()
            and e.get('status') != 'completed'
        ]

        if overdue_deadlines:
            risk_factors.append({
                "category": "DEADLINE_COMPLIANCE",
                "severity": "HIGH",
                "description": f"{len(overdue_deadlines)} overdue deadline(s)",
                "impact": "Potential sanctions, dismissal, or adverse rulings",
                "mitigation": [
                    "File emergency motions for extension if applicable",
                    "Prepare explanation for court",
                    "Complete overdue items immediately",
                    "Implement deadline tracking system"
                ]
            })

        # Multi-party coordination risks
        if len(parties) > 5:
            risk_factors.append({
                "category": "MULTI_PARTY_COORDINATION",
                "severity": "MEDIUM",
                "description": f"Complex case with {len(parties)} parties",
                "impact": "Communication challenges, conflicting interests, delays",
                "mitigation": [
                    "Establish clear communication protocols",
                    "Regular status conferences",
                    "Document all party communications",
                    "Identify potential conflicts early"
                ]
            })

        # Timeline compression risks
        compressed_timeline = any(
            e.get('slack_days', 999) < 3
            for e in events
            if e.get('is_critical_path')
        )

        if compressed_timeline:
            risk_factors.append({
                "category": "TIMELINE_COMPRESSION",
                "severity": "HIGH",
                "description": "Critical path events with minimal slack time",
                "impact": "No room for delays, increased pressure, quality concerns",
                "mitigation": [
                    "Request timeline extensions where possible",
                    "Allocate additional resources to critical tasks",
                    "Prepare contingency plans for delays",
                    "Daily monitoring of critical path items"
                ]
            })

        return risk_factors

    @staticmethod
    def _generate_scenarios(
        case_data: Dict[str, Any],
        assets: List[Dict[str, Any]],
        parties: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate alternative scenario analysis
        """
        scenarios = []

        # Best case scenario
        total_asset_value = sum(float(a.get('estimated_value', 0)) for a in assets)

        scenarios.append({
            "name": "Best Case Outcome",
            "probability": "30-40%",
            "description": "All assets sold at or above estimated value, minimal objections sustained",
            "outcomes": [
                f"Total recovery: ${total_asset_value * 1.1:,.2f} (110% of estimated)",
                "All creditors paid pro-rata",
                "Case concluded within estimated timeline",
                "No significant legal fees from disputes"
            ],
            "requirements": [
                "Strong bidder interest",
                "Minimal successful objections",
                "Cooperative parties",
                "Favorable court rulings"
            ]
        })

        # Likely case scenario
        scenarios.append({
            "name": "Likely Case Outcome",
            "probability": "50-60%",
            "description": "Assets sold near estimated value with some objections",
            "outcomes": [
                f"Total recovery: ${total_asset_value * 0.95:,.2f} (95% of estimated)",
                "Most creditors receive substantial payments",
                "Some delays from objections",
                "Moderate legal fees"
            ],
            "requirements": [
                "Adequate bidder interest",
                "Resolution of major objections",
                "Standard court timeline",
                "Reasonable cooperation"
            ]
        })

        # Worst case scenario
        scenarios.append({
            "name": "Worst Case Outcome",
            "probability": "10-20%",
            "description": "Asset sales below value, significant objections, extended timeline",
            "outcomes": [
                f"Total recovery: ${total_asset_value * 0.7:,.2f} (70% of estimated)",
                "Unsecured creditors receive minimal payment",
                "Significant delays (6-12 months)",
                "High legal fees erode recovery"
            ],
            "risks": [
                "Market downturn affecting asset values",
                "Successful objections blocking sales",
                "Appeals extending timeline",
                "Uncooperative parties"
            ]
        })

        return scenarios

    @staticmethod
    def generate_talking_points(
        case_data: Dict[str, Any],
        next_hearing: Optional[Dict[str, Any]] = None,
        objections: List[Dict[str, Any]] = []
    ) -> Dict[str, Any]:
        """
        Generate talking points for hearings and negotiations
        """
        talking_points = {
            "case_strengths": [],
            "questions_to_ask": [],
            "positions_to_advocate": [],
            "objection_responses": [],
            "negotiation_leverage": []
        }

        # Case strengths
        talking_points["case_strengths"] = [
            "Comprehensive asset inventory with professional valuations",
            "Transparent process with full notice to all parties",
            "Compliance with all procedural requirements",
            "Good faith efforts to maximize estate value"
        ]

        # Questions to ask (if hearing)
        if next_hearing:
            hearing_type = next_hearing.get('event_type', '')

            if 'sale' in str(next_hearing.get('title', '')).lower():
                talking_points["questions_to_ask"] = [
                    "Has adequate notice been provided to all creditors?",
                    "Were the assets marketed appropriately?",
                    "Is the winning bid a fair market value?",
                    "Are there any undisclosed conflicts of interest?"
                ]

            elif 'plan' in str(next_hearing.get('title', '')).lower():
                talking_points["questions_to_ask"] = [
                    "Is the plan feasible and achievable?",
                    "Do creditors have sufficient information to vote?",
                    "Are treatment of claims appropriate and fair?",
                    "What are the consequences of plan failure?"
                ]

        # Positions to advocate
        talking_points["positions_to_advocate"] = [
            {
                "position": "Expedited Timeline",
                "rationale": "Delay erodes asset values and increases administrative costs",
                "support": "Estate preservation, creditor interest"
            },
            {
                "position": "Competitive Bidding Process",
                "rationale": "Open competition ensures maximum value realization",
                "support": "Market-based valuation, fairness to all stakeholders"
            },
            {
                "position": "Professional Fee Oversight",
                "rationale": "Administrative costs reduce distributions to creditors",
                "support": "Fiduciary duty, estate maximization"
            }
        ]

        # Objection response strategies
        for objection in objections:
            talking_points["objection_responses"].append({
                "objection": objection.get('title'),
                "response_strategy": AttorneyBriefingGenerator._craft_objection_response(objection),
                "legal_authority": objection.get('legal_authority', ''),
                "settlement_opportunity": "Explore if objector's concerns can be addressed without litigation"
            })

        # Negotiation leverage
        talking_points["negotiation_leverage"] = [
            {
                "leverage_point": "Multiple qualified bidders",
                "how_to_use": "Create competitive pressure to increase bid amounts"
            },
            {
                "leverage_point": "Court deadline pressure",
                "how_to_use": "Encourage settlement to avoid protracted litigation"
            },
            {
                "leverage_point": "Alternative asset disposition",
                "how_to_use": "Credible threat of different approach if cooperation lacking"
            }
        ]

        return talking_points

    @staticmethod
    def _craft_objection_response(objection: Dict[str, Any]) -> str:
        """
        Craft response strategy for objection
        """
        objection_type = objection.get('objection_type', '')

        responses = {
            'claim': "Challenge basis and amount, request documentation, propose compromise if appropriate",
            'plan': "Demonstrate feasibility, show good faith, offer creditor modifications",
            'sale': "Prove adequate marketing, competitive process, fair value, no conflicts",
            'disclosure': "Provide additional information, show materiality, cure defects",
        }

        return responses.get(objection_type, "Analyze grounds, prepare factual rebuttal, seek early resolution")

    @staticmethod
    def generate_action_items(
        case_data: Dict[str, Any],
        events: List[Dict[str, Any]],
        objections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate prioritized action items with deadlines
        """
        action_items = []

        # Immediate requirements (next 24-48 hours)
        urgent_deadlines = [
            e for e in events
            if e.get('event_type') == 'deadline'
            and e.get('event_date', datetime.max) > datetime.utcnow()
            and (e.get('event_date', datetime.max) - datetime.utcnow()).days <= 2
        ]

        for deadline in urgent_deadlines:
            action_items.append({
                "priority": "URGENT",
                "category": "Immediate Deadline",
                "task": deadline['title'],
                "description": deadline.get('description', ''),
                "due_date": deadline['event_date'],
                "hours_remaining": int((deadline['event_date'] - datetime.utcnow()).total_seconds() / 3600),
                "required_actions": deadline.get('required_actions', []),
                "responsible_party": deadline.get('responsible_parties', ['Attorney']),
                "blockers": deadline.get('blocked_by_event_ids', [])
            })

        # Document preparation needs
        upcoming_hearings = [
            e for e in events
            if e.get('event_type') in ['hearing', 'conference']
            and e.get('event_date', datetime.max) > datetime.utcnow()
            and (e.get('event_date', datetime.max) - datetime.utcnow()).days <= 14
        ]

        for hearing in upcoming_hearings:
            action_items.append({
                "priority": "HIGH",
                "category": "Document Preparation",
                "task": f"Prepare for {hearing['title']}",
                "description": "Gather exhibits, prepare witness list, draft arguments",
                "due_date": hearing['event_date'] - timedelta(days=3),  # 3 days before
                "required_actions": [
                    "Review all case documents",
                    "Prepare witness examination outline",
                    "Organize exhibits",
                    "Draft legal argument memo",
                    "Coordinate with co-counsel/parties"
                ],
                "estimated_hours": 8
            })

        # Party communications needed
        if len(objections) > 0:
            action_items.append({
                "priority": "HIGH",
                "category": "Party Communication",
                "task": "Address pending objections",
                "description": f"Communicate with {len(objections)} objecting parties",
                "due_date": datetime.utcnow() + timedelta(days=7),
                "required_actions": [
                    "Contact each objecting party",
                    "Understand basis of objections",
                    "Explore settlement opportunities",
                    "Prepare responses if settlement fails"
                ],
                "estimated_hours": 4
            })

        # Court filings required
        required_filings = [
            e for e in events
            if e.get('event_type') == 'filing'
            and e.get('status') == 'pending'
        ]

        for filing in required_filings:
            action_items.append({
                "priority": "HIGH",
                "category": "Court Filing",
                "task": filing['title'],
                "description": filing.get('description', ''),
                "due_date": filing['event_date'],
                "required_actions": [
                    "Draft filing document",
                    "Obtain necessary signatures",
                    "File with court",
                    "Serve on required parties"
                ],
                "estimated_hours": 3
            })

        # Sort by priority and due date
        priority_order = {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        action_items.sort(
            key=lambda x: (priority_order.get(x.get('priority', 'LOW'), 3), x.get('due_date', datetime.max))
        )

        return action_items


# ============================================================================
# EXPORT INSTANCE
# ============================================================================

attorney_briefing_generator = AttorneyBriefingGenerator()
