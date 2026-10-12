"""ta.smc_sweep: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.smc_sweep import smc_sweep as _calculate

from ..common import named_series


def compute(*, open_, high, low, close, length, wick_mult, talib):
    result = _calculate(
        open_=open_,
        high=high,
        low=low,
        close=close,
        length=length,
        wick_mult=wick_mult,
        talib=talib,
    )
    return named_series(result, "ta.smc_sweep", "smc_sweep")
