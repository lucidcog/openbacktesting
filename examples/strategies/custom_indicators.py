"""Reuse custom indicators: pure functions, two parameter sets, named multiple outputs, and ta composition.

The first 120 bundled GOOG daily bars, with no extra dependencies. Percentage channels deviate from the moving average by width on each side,
They are not Bollinger bands; functions can move to ordinary Python modules for other strategies to import.
The author script only declares a strategy; next reads signals without ordering, so commission is 0 and no positions or return evidence are produced.
ind calculates in batches during init and reruns on each registration; authors ensure causality and save handles rather than full arrays.
"""

from typing import NamedTuple

import pandas as pd

from openbacktesting import Strategy, backtest, inputs
from openbacktesting.indicators.types import IndicatorHandle


def mean_band(close: pd.Series, length: int, *, width: float = 0.02) -> pd.DataFrame:
    """Return a moving-average percentage channel preserving the market-data index; callable independently of a strategy."""
    if isinstance(length, bool) or not isinstance(length, int) or length < 1:
        raise ValueError("length must be a positive integer")
    if isinstance(width, bool) or not isinstance(width, (int, float)) or not 0 <= width <= 1:
        raise ValueError("width must be between 0 and 1")
    middle = close.rolling(length, min_periods=length).mean()
    return pd.DataFrame(
        {"middle": middle, "upper": middle * (1 + width), "lower": middle * (1 - width)},
        index=close.index,
    )


class TrendLines(NamedTuple):
    """Hold indicator handles for the current run only, without managing calculation or update lifecycles."""

    fast: IndicatorHandle
    slow: IndicatorHandle
    cross: IndicatorHandle


def trend_lines(ta, source, *, fast=5, slow=20) -> TrendLines:
    """Combine existing indicators in init, retaining each line's validity and cursor."""
    if fast >= slow:
        raise ValueError("fast must be less than slow")
    fast_line = ta.ema(source, length=fast)
    slow_line = ta.ema(source, length=slow)
    return TrendLines(fast_line, slow_line, ta.crossover(fast_line, slow_line))


@backtest(commission_value=0)
class CustomIndicators(Strategy):
    fast_length = inputs.int(5, title="Fast channel period", minval=1)
    slow_length = inputs.int(20, title="Slow channel period", minval=1)

    def init(self):
        # .s is the complete input snapshot for this pure calculation; registration retains a dynamic handle.
        self.fast = self.ind(
            mean_band,
            self.close.s,
            self.fast_length,
            width=0.02,
            name=["middle", "upper", "lower"],
        )
        self.slow = self.ind(
            mean_band,
            self.close.s,
            self.slow_length,
            width=0.04,
            name=["middle", "upper", "lower"],
        )
        self.smoothed = self.ta.ema(self.fast["middle"], length=3)
        self.short_trend = trend_lines(self.ta, self.close, fast=5, slow=20)
        self.long_trend = trend_lines(self.ta, self.hlc3, fast=10, slow=30)
        self.plotting.line(self.fast["middle"], title="Fast channel midline")
        self.plotting.line(self.slow["middle"], title="Slow channel midline")

    def next(self):
        self.above = bool(
            self.fast["middle"].valid[-1]
            and self.slow["middle"].valid[-1]
            and self.fast["middle"][-1] > self.slow["middle"][-1]
        )
        self.crossed = bool(self.short_trend.cross.valid[-1] and self.short_trend.cross[-1])


class AnotherStrategy(Strategy):
    """The same calculation can use different sources and parameters in other strategies."""

    def init(self):
        self.band = self.ind(mean_band, self.hlc3.s, 10, name=["middle", "upper", "lower"])

    def next(self):
        self.above = bool(self.band["upper"].valid[-1] and self.close[-1] > self.band["upper"][-1])
