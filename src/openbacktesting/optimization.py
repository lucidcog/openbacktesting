"""Compatibility exports for the old optimization path; implemented in backtest.optimization."""

from openbacktesting.simulation.optimization import (
    _joined_pool,  # noqa: F401 — re-export the legacy entry point
    _optimize,  # noqa: F401 — re-export the legacy entry point
)

__all__ = []
