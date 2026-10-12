"""Compatibility exports for the old strategy path; implemented in strategy.base."""

from typing import TYPE_CHECKING

from openbacktesting.strategy.bar_state import BarState as BarState

if TYPE_CHECKING:
    from openbacktesting.strategy.base import Strategy as Strategy

__all__ = ["BarState", "Strategy"]


def __getattr__(name):
    if name == "Strategy":
        from openbacktesting.strategy.base import Strategy

        globals()[name] = Strategy
        return Strategy
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
