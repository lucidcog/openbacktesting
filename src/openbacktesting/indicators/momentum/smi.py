"""ta.smi：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.smi import smi as _calculate

from ..common import named_frame


def compute(*, close, fast, slow, signal, scalar, talib):
    result = _calculate(
        close=close, fast=fast, slow=slow, signal=signal, scalar=scalar, talib=talib
    )
    suffix = f"_{scalar}" if scalar != 1 else ""
    return named_frame(
        result,
        "ta.smi",
        {
            f"SMI_{fast}_{slow}_{signal}{suffix}": "smi",
            f"SMIs_{fast}_{slow}_{signal}{suffix}": "signal",
            f"SMIo_{fast}_{slow}_{signal}{suffix}": "oscillator",
        },
    )
