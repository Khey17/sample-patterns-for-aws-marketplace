"""
orchestration
=============
Real Temporal workflow orchestration for the DevOps Companion pipeline.

Requires: temporalio>=1.7.0, httpx>=0.25.0
Supports: Temporal CLI dev server (localhost:7233) or Temporal Cloud.
"""

__version__ = "0.1.0"

_TEMPORAL_AVAILABLE = False
try:
    import temporalio  # noqa: F401

    _TEMPORAL_AVAILABLE = True
except ImportError:
    pass


def is_available() -> bool:
    """Check if the temporalio SDK is installed."""
    return _TEMPORAL_AVAILABLE
