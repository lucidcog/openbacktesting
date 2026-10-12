"""便利 API 的旧入口；各领域直接重导出同一对象。"""

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

__all__ = [  # noqa: RUF022 — 保留既有导出顺序
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
    "FractionalBacktest",  # noqa: RUF068 — 保留既有重复导出
    "MultiBacktest",
]
