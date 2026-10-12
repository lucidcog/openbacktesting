"""Legacy entry point for convenience APIs; each domain directly re-exports the same objects."""

from openbacktesting.data.aggregation import OHLCV_AGG, TRADES_AGG
from openbacktesting.data.generators import random_ohlc_data
from openbacktesting.portfolio.helpers import compute_stats
from openbacktesting.simulation.core import Backtest  # noqa: F401
from openbacktesting.simulation.variants import FractionalBacktest, MultiBacktest
from openbacktesting.strategy.base import Strategy  # noqa: F401
from openbacktesting.strategy.helpers import barssince, quantile, resample_apply
from openbacktesting.strategy.templates import SignalStrategy, TrailingStrategy

__pdoc__ = {
    "Strategy.__init__": False,
    "SignalStrategy.__init__": False,
    "TrailingStrategy.__init__": False,
}

__all__ = [  # noqa: RUF022 — preserve existing export order
    "OHLCV_AGG",
    "TRADES_AGG",
    "barssince",
    "quantile",
    "compute_stats",
    "resample_apply",
    "random_ohlc_data",
    "SignalStrategy",
    "TrailingStrategy",
    "FractionalBacktest",
    "FractionalBacktest",  # noqa: RUF068 — preserve existing duplicate exports
    "MultiBacktest",
]
