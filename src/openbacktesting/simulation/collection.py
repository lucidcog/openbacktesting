"""Internal run-collection policy; defaults match ordinary backtest behavior."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CollectionPolicy:
    portfolio: bool = True
    logs: bool = True
    plotting: bool = True


DEFAULT_COLLECTION = CollectionPolicy()
