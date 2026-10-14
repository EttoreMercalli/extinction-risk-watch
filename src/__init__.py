"""
Browser Apocalypse / Extinction Risk Watch - Data Acquisition and Verification Package.
"""

from src.models import SourceConfig, CheckResult, ValidationRule
from src.config import load_sources, filter_sources
from src.verifier import SourceVerifier
from src.reporter import VerificationReporter

__all__ = [
    "SourceConfig",
    "CheckResult",
    "ValidationRule",
    "load_sources",
    "filter_sources",
    "SourceVerifier",
    "VerificationReporter"
]
