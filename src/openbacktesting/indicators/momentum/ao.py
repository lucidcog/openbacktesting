"""ta.ao: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.ao import ao as _calculate

from ..common import named_series


def compute(*, high, low, fast, slow, talib):
    result = _calculate(high=high, low=low, fast=fast, slow=slow, talib=talib)
    return named_series(result, "ta.ao", "ao")
