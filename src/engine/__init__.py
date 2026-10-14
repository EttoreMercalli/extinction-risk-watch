"""
Package engine: Calcolo quantitativo del rischio di estinzione umana e giorni stimati rimasti.
"""

from src.engine.models import (
    ExtinctionLifespanResult,
    HorizonProbability,
    CategoryRiskBreakdown
)
from src.engine.calculator import (
    DoomsdayCalculator,
    BASELINE_100Y,
    TEMPORAL_FACTORS
)

__all__ = [
    "ExtinctionLifespanResult",
    "HorizonProbability",
    "CategoryRiskBreakdown",
    "DoomsdayCalculator",
    "BASELINE_100Y",
    "TEMPORAL_FACTORS"
]
