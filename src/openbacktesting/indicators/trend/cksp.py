"""ta.cksp: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.cksp import cksp as _calculate

from ..common import named_frame


def compute(*, high, low, close, p, x, q, tvmode, talib):
    result = _calculate(high=high, low=low, close=close, p=p, x=x, q=q, tvmode=tvmode, talib=talib)
    return named_frame(
        result,
        "ta.cksp",
        {
            f"CKSPl_{p}_{float(x)}_{q}": "long",
            f"CKSPs_{p}_{float(x)}_{q}": "short",
        },
    )
