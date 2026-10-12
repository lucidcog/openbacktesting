"""ta.sarext: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.sarext import sarext as _calculate

from ..common import named_series


def compute(
    *,
    high,
    low,
    startvalue,
    offsetonreverse,
    accelerationinitlong,
    accelerationlong,
    accelerationmaxlong,
    accelerationinitshort,
    accelerationshort,
    accelerationmaxshort,
    talib,
):
    result = _calculate(
        high=high,
        low=low,
        startvalue=startvalue,
        offsetonreverse=offsetonreverse,
        accelerationinitlong=accelerationinitlong,
        accelerationlong=accelerationlong,
        accelerationmaxlong=accelerationmaxlong,
        accelerationinitshort=accelerationinitshort,
        accelerationshort=accelerationshort,
        accelerationmaxshort=accelerationmaxshort,
        talib=talib,
    )
    return named_series(result, "ta.sarext", "sarext")
