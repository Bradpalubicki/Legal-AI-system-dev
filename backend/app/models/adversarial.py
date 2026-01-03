"""
Adversarial Simulation Models
Database models for the opposing counsel simulation feature
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..src.core.database import Base


class AdversarialSimulation(Base):
    """
    Tracks an adversarial simulation session that runs alongside a defense interview.
    Generates counter-arguments as if from opposing counsel.
    """
    __tablename__ = "adversarial_simulations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    defense_session_id = Column(String(36), ForeignKey("defense_sessions.id"), nullable=False, index=True)
    user_id = Column(String(36), index=True, nullable=False)

    # Status tracking
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    progress = Column(Integer, default=0)  # 0-100

    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Case context
    case_type = Column(String(100))
    collected_facts = Column(JSON, default=dict)  # Facts gathered during interview

    # Results (denormalized for quick access)
    counter_arguments_summary = Column(JSON, default=list)  # Summary of all counter-arguments
    weaknesses = Column(JSON, default=list)  # Identified case weaknesses
    overall_strength = Column(String(20))  # weak, moderate, strong
    recommendations = Column(JSON, default=list)  # Recommendations for improvement

    # Error tracking
    error_message = Column(Text)

    # Tier-based limits
    max_counter_arguments = Column(Integer, default=3)  # Based on subscription tier

    # Relationships
    defense_session = relationship("DefenseSession", backref="adversarial_simulations")
    counter_arguments = relationship("CounterArgument", back_populates="simulation", cascade="all, delete-orphan", order_by="CounterArgument.likelihood_score.desc()")


class CounterArgument(Base):
    """
    Individual counter-argument that opposing counsel might raise.
    Includes rebuttals (level 2) and counter-rebuttals (level 3).
    """
    __tablename__ = "counter_arguments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    simulation_id = Column(String(36), ForeignKey("adversarial_simulations.id"), nullable=False, index=True)

    # Argument content (Level 1)
    argument_title = Column(String(500), nullable=False)
    argument_description = Column(Text, nullable=False)
    legal_basis = Column(Text)  # Legal foundation for the argument

    # Likelihood assessment
    likelihood = Column(String(20), nullable=False)  # high, medium, low
    likelihood_score = Column(Integer, default=50)  # 0-100 for sorting
    likelihood_reasoning = Column(Text)  # Why this likelihood

    # Category
    category = Column(String(50))  # procedural, substantive, evidentiary, credibility

    # Evidence the opponent might use
    evidence_to_support = Column(JSON, default=list)  # What evidence strengthens their argument

    # Rebuttals (Level 2) - stored as JSON for flexibility
    # Each rebuttal: {
    #   id: str,
    #   rebuttal_text: str,
    #   evidence_needed: [str],
    #   strength: "strong" | "moderate" | "weak",
    #   counter_rebuttals: [  # Level 3
    #     {
    #       id: str,
    #       counter_text: str,
    #       your_response: str
    #     }
    #   ]
    # }
    rebuttals = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    simulation = relationship("AdversarialSimulation", back_populates="counter_arguments")


# Tier limits configuration
TIER_COUNTER_ARGUMENT_LIMITS = {
    "free": 0,  # No access
    "basic": 3,
    "individual_pro": 5,
    "professional": 8,
    "premium": 15,  # Effectively unlimited for most cases
    "enterprise": 20,
    "admin": 50  # Full access
}

# Tier features
TIER_ADVERSARIAL_FEATURES = {
    "free": {
        "enabled": False,
        "counter_arguments": 0,
        "weakness_analysis": False,
        "priority_processing": False
    },
    "basic": {
        "enabled": True,
        "counter_arguments": 3,
        "weakness_analysis": False,
        "priority_processing": False
    },
    "individual_pro": {
        "enabled": True,
        "counter_arguments": 5,
        "weakness_analysis": False,
        "priority_processing": False
    },
    "professional": {
        "enabled": True,
        "counter_arguments": 8,
        "weakness_analysis": True,
        "priority_processing": False
    },
    "premium": {
        "enabled": True,
        "counter_arguments": 15,
        "weakness_analysis": True,
        "priority_processing": True
    },
    "enterprise": {
        "enabled": True,
        "counter_arguments": 20,
        "weakness_analysis": True,
        "priority_processing": True
    },
    "admin": {
        "enabled": True,
        "counter_arguments": 50,
        "weakness_analysis": True,
        "priority_processing": True
    }
}
