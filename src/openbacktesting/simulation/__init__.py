"""Lazy class exports for the simulation package; implemented in simulation.core."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openbacktesting.simulation.core import Backtest as Backtest

__all__ = ["Backtest"]


def __getattr__(name):
    if name == "Backtest":
        from openbacktesting.simulation.core import Backtest

        globals()[name] = Backtest
        return Backtest
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
