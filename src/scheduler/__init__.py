"""
Package scheduler: Infrastruttura di aggiornamento continuo e a intervalli (10 minuti).
"""

from src.scheduler.tiered_updater import TieredDataUpdater

__all__ = ["TieredDataUpdater"]
