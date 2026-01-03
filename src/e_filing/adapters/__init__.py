"""
Court System Adapters

Adapters for integrating with different court e-filing systems
including Federal (CM/ECF) and state court systems.
"""

from .base_adapter import BaseCourtAdapter
from .federal_adapter import FederalCourtAdapter
from .state_adapter import StateCourtAdapter

__all__ = [
    "BaseCourtAdapter",
    "FederalCourtAdapter", 
    "StateCourtAdapter"
]