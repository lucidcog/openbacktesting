"""Compatibility exports for the old parallel path; implemented in backtest.parallel."""

from openbacktesting.simulation.parallel import (
    SharedMemory,
    SharedMemoryManager,
    _batch,  # noqa: F401 — re-export the legacy entry point
)

__all__ = ["SharedMemory", "SharedMemoryManager"]
