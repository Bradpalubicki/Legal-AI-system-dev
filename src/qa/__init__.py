"""
Q&A System
Enhanced Q&A system with continuous learning capabilities.
"""

from .validation import (
    AnswerValidator,
    ValidationResult,
    ValidationStatus,
    ConfidenceLevel,
    ValidationFlag,
    DocumentReference,
    ConsistencyCheck,
    ExpertReview,
    answer_validator,
    get_validation_endpoints,
    initialize_answer_validation
)

from .question_bank import (
    QuestionBank,
    PreApprovedQuestion,
    QuestionVariation,
    QuestionTemplate,
    JudgeProfile,
    OutcomeBasedQuestion,
    CustomQuestion,
    QuestionCategory,
    QuestionType,
    ApprovalStatus,
    Jurisdiction,
    question_bank,
    get_question_bank_endpoints,
    initialize_question_bank
)

from .memory import (
    ConversationMemory,
    ConversationMessage,
    ConversationContext,
    ConversationSummary,
    FollowUpSuggestion,
    ConversationPattern,
    PreviousAnswerReference,
    ConversationState,
    MessageType,
    ContextRelevance,
    MemoryType,
    conversation_memory,
    get_memory_endpoints,
    initialize_conversation_memory
)

__all__ = [
    # Answer Validation
    "AnswerValidator",
    "ValidationResult",
    "ValidationStatus",
    "ConfidenceLevel",
    "ValidationFlag",
    "DocumentReference",
    "ConsistencyCheck",
    "ExpertReview",
    "answer_validator",
    "get_validation_endpoints",
    "initialize_answer_validation",

    # Question Banking
    "QuestionBank",
    "PreApprovedQuestion",
    "QuestionVariation",
    "QuestionTemplate",
    "JudgeProfile",
    "OutcomeBasedQuestion",
    "CustomQuestion",
    "QuestionCategory",
    "QuestionType",
    "ApprovalStatus",
    "Jurisdiction",
    "question_bank",
    "get_question_bank_endpoints",
    "initialize_question_bank",

    # Conversation Memory
    "ConversationMemory",
    "ConversationMessage",
    "ConversationContext",
    "ConversationSummary",
    "FollowUpSuggestion",
    "ConversationPattern",
    "PreviousAnswerReference",
    "ConversationState",
    "MessageType",
    "ContextRelevance",
    "MemoryType",
    "conversation_memory",
    "get_memory_endpoints",
    "initialize_conversation_memory",

    # Unified functions
    "get_enhanced_qa_endpoints",
    "initialize_enhanced_qa_system",
    "trigger_defense_strategy_update"
]


async def get_enhanced_qa_endpoints():
    """Get all enhanced Q&A endpoints from all modules"""
    endpoints = []

    # Collect endpoints from all modules
    validation_endpoints = await get_validation_endpoints()
    question_bank_endpoints = await get_question_bank_endpoints()
    memory_endpoints = await get_memory_endpoints()

    endpoints.extend(validation_endpoints)
    endpoints.extend(question_bank_endpoints)
    endpoints.extend(memory_endpoints)

    return endpoints


async def initialize_enhanced_qa_system():
    """Initialize the complete enhanced Q&A system with continuous learning"""
    print("Initializing Enhanced Q&A System with Continuous Learning...")

    results = []

    # Initialize all subsystems
    validation_init = await initialize_answer_validation()
    results.append(("Answer Validation", validation_init))

    question_bank_init = await initialize_question_bank()
    results.append(("Question Banking", question_bank_init))

    memory_init = await initialize_conversation_memory()
    results.append(("Conversation Memory", memory_init))

    # Check results
    failed_systems = [name for name, success in results if not success]
    successful_systems = [name for name, success in results if success]

    if failed_systems:
        print(f"WARNING: Failed to initialize: {', '.join(failed_systems)}")

    if successful_systems:
        print(f"SUCCESS: Successfully initialized: {', '.join(successful_systems)}")

    # Get total endpoint count
    all_endpoints = await get_enhanced_qa_endpoints()
    total_endpoints = len(all_endpoints)

    print(f"Enhanced Q&A System initialized with {total_endpoints} endpoints")
    print("=" * 70)
    print("ENHANCED Q&A SYSTEM WITH CONTINUOUS LEARNING READY")
    print("=" * 70)
    print("Features Available:")
    print("- Answer validation with cross-referencing and confidence scoring")
    print("- Pre-approved question bank with state and judge variations")
    print("- Conversation memory with context maintenance and follow-ups")
    print("- Expert review queue for complex legal matters")
    print("- Outcome-based question generation")
    print("- Previous answer recall and consistency checking")
    print("- Intelligent follow-up suggestions")
    print("- Real-time defense strategy updates")
    print("=" * 70)

    return len(failed_systems) == 0


async def trigger_defense_strategy_update(qa_session_id: str, new_insights: dict, case_id: str = None):
    """Trigger real-time defense strategy updates based on Q&A insights"""
    try:
        from datetime import datetime
        from decimal import Decimal

        # This function integrates with the defense strategy system
        print(f"Defense strategy update triggered for Q&A session {qa_session_id}")

        # Update analytics with Q&A insights
        try:
            from ..analytics import user_metrics_analyzer, business_analytics_engine

            # Track Q&A engagement
            await user_metrics_analyzer.track_engagement(
                user_id=new_insights.get("user_id", "unknown"),
                activity_type="qa_session",
                duration_minutes=new_insights.get("session_duration", 0),
                feature_used="enhanced_qa_system"
            )

            # Update business metrics for Q&A usage
            if new_insights.get("billable_time"):
                await business_analytics_engine.track_customer_lifecycle(
                    firm_id=new_insights.get("firm_id", "unknown"),
                    event_type="qa_billable_activity",
                    value=Decimal(str(new_insights.get("billable_amount", 0)))
                )

        except ImportError:
            pass
        except Exception as e:
            print(f"Analytics update failed: {e}")

        # Strategy update logic
        strategy_updates = {
            "timestamp": datetime.utcnow().isoformat(),
            "qa_session_id": qa_session_id,
            "case_id": case_id,
            "insights": new_insights,
            "strategy_impact": await _analyze_strategy_impact(new_insights),
            "recommended_actions": await _generate_strategy_recommendations(new_insights),
            "confidence_changes": await _assess_confidence_changes(new_insights),
            "risk_assessment_updates": await _update_risk_assessment(new_insights)
        }

        # Audit trail for strategy updates
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "defense_strategy_update",
            "qa_session_id": qa_session_id,
            "case_id": case_id,
            "updates": strategy_updates,
            "system": "enhanced_qa_system"
        }
        print(f"Strategy update audit: {audit_entry}")

        # Notification for significant strategy changes
        if strategy_updates["strategy_impact"]["severity"] == "high":
            print(f"HIGH IMPACT: Defense strategy significantly updated based on Q&A insights")

        return True

    except Exception as e:
        print(f"Error triggering defense strategy update: {e}")
        return False


async def _analyze_strategy_impact(insights: dict) -> dict:
    """Analyze the impact of Q&A insights on defense strategy"""
    impact = {
        "severity": "low",
        "affected_areas": [],
        "confidence_change": 0.0,
        "timeline_impact": False,
        "resource_impact": False
    }

    # Analyze validation results impact
    if "validation_results" in insights:
        validation = insights["validation_results"]
        if validation.get("confidence_level") == "very_low":
            impact["severity"] = "high"
            impact["affected_areas"].append("evidence_strength")
        elif validation.get("flags") and "contradiction" in validation.get("flags", []):
            impact["severity"] = "high"
            impact["affected_areas"].append("legal_consistency")

    # Analyze conversation insights
    if "conversation_summary" in insights:
        summary = insights["conversation_summary"]
        if summary.get("unresolved_issues"):
            impact["severity"] = "medium"
            impact["affected_areas"].append("case_preparation")

    # Analyze question banking insights
    if "question_effectiveness" in insights:
        effectiveness = insights["question_effectiveness"]
        if effectiveness.get("success_rate", 0.0) < 0.5:
            impact["affected_areas"].append("questioning_strategy")

    return impact


async def _generate_strategy_recommendations(insights: dict) -> list:
    """Generate actionable strategy recommendations based on Q&A insights"""
    recommendations = []

    # Validation-based recommendations
    if "validation_results" in insights:
        validation = insights["validation_results"]
        if validation.get("confidence_level") == "very_low":
            recommendations.append("Conduct additional research to strengthen legal position")
        if "missing_citation" in validation.get("flags", []):
            recommendations.append("Gather additional case law and statutory support")
        if "expert_required" in validation.get("flags", []):
            recommendations.append("Consider expert witness consultation")

    # Memory-based recommendations
    if "conversation_insights" in insights:
        conv_insights = insights["conversation_insights"]
        if conv_insights.get("unresolved_questions_count", 0) > 3:
            recommendations.append("Schedule follow-up strategy session to address open questions")
        if conv_insights.get("follow_up_priority", 0) > 7:
            recommendations.append("Prioritize high-impact follow-up questions immediately")

    # Question bank recommendations
    if "question_patterns" in insights:
        patterns = insights["question_patterns"]
        if patterns.get("outcome_probability", 0.0) < 0.5:
            recommendations.append("Revise case strategy to improve outcome probability")
        if patterns.get("judge_preferences"):
            recommendations.append("Adapt questioning approach based on judge preferences")

    return recommendations


async def _assess_confidence_changes(insights: dict) -> dict:
    """Assess changes in case confidence based on Q&A insights"""
    confidence_assessment = {
        "overall_change": 0.0,
        "evidence_confidence": 0.0,
        "legal_confidence": 0.0,
        "procedural_confidence": 0.0,
        "outcome_confidence": 0.0,
        "factors": []
    }

    # Factor in validation confidence
    if "validation_results" in insights:
        validation = insights["validation_results"]
        confidence_score = validation.get("confidence_score", 50.0)
        if confidence_score > 70.0:
            confidence_assessment["legal_confidence"] += 0.2
            confidence_assessment["factors"].append("High validation confidence")
        elif confidence_score < 30.0:
            confidence_assessment["legal_confidence"] -= 0.2
            confidence_assessment["factors"].append("Low validation confidence")

    # Factor in conversation effectiveness
    if "conversation_effectiveness" in insights:
        effectiveness = insights["conversation_effectiveness"]
        if effectiveness.get("resolution_rate", 0.0) > 0.8:
            confidence_assessment["procedural_confidence"] += 0.1
            confidence_assessment["factors"].append("High question resolution rate")

    # Calculate overall change
    confidence_assessment["overall_change"] = (
        confidence_assessment["evidence_confidence"] +
        confidence_assessment["legal_confidence"] +
        confidence_assessment["procedural_confidence"] +
        confidence_assessment["outcome_confidence"]
    ) / 4.0

    return confidence_assessment


async def _update_risk_assessment(insights: dict) -> dict:
    """Update risk assessment based on Q&A insights"""
    risk_updates = {
        "new_risks": [],
        "mitigated_risks": [],
        "risk_level_changes": {},
        "recommended_mitigations": []
    }

    # Identify new risks from validation flags
    if "validation_results" in insights:
        validation = insights["validation_results"]
        flags = validation.get("flags", [])

        if "contradiction" in flags:
            risk_updates["new_risks"].append("Legal position contradiction identified")
            risk_updates["recommended_mitigations"].append("Reconcile contradictory positions")

        if "jurisdiction_mismatch" in flags:
            risk_updates["new_risks"].append("Jurisdiction-specific law mismatch")
            risk_updates["recommended_mitigations"].append("Review jurisdiction-specific requirements")

        if "outdated_law" in flags:
            risk_updates["new_risks"].append("Potentially outdated legal references")
            risk_updates["recommended_mitigations"].append("Update legal research with current law")

    # Assess risks from conversation patterns
    if "conversation_patterns" in insights:
        patterns = insights["conversation_patterns"]
        if patterns.get("complexity_trend", "stable") == "increasing":
            risk_updates["new_risks"].append("Case complexity increasing beyond initial assessment")
            risk_updates["recommended_mitigations"].append("Allocate additional resources for complex issues")

    return risk_updates