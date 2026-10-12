"""ta.thermo: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volatility.thermo import thermo as _calculate

from ..common import named_frame


def compute(*, high, low, length, long, short, mamode, drift, talib):
    result = _calculate(
        high=high,
        low=low,
        length=length,
        long=long,
        short=short,
        mamode=mamode,
        drift=drift,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.thermo",
        {
            f"THERMO_{length}_{float(long)}_{float(short)}": "thermo",
            f"THERMOma_{length}_{float(long)}_{float(short)}": "average",
            f"THERMOl_{length}_{float(long)}_{float(short)}": "long",
            f"THERMOs_{length}_{float(long)}_{float(short)}": "short",
        },
    )
