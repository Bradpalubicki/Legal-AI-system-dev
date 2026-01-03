"""
Middleware package for legal AI system
"""

from .force_correct_behavior import ForceCorrectBehavior, apply_forced_corrections

__all__ = ['ForceCorrectBehavior', 'apply_forced_corrections']
