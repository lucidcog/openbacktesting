"""ta.ppo: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.ppo import ppo as _calculate

from ..common import named_frame


def compute(*, close, fast, slow, signal, scalar, mamode, talib):
    result = _calculate(
        close=close, fast=fast, slow=slow, signal=signal, scalar=scalar, mamode=mamode, talib=talib
    )
    return named_frame(
        result,
        "ta.ppo",
        {
            f"PPO_{fast}_{slow}_{signal}": "ppo",
            f"PPOh_{fast}_{slow}_{signal}": "histogram",
            f"PPOs_{fast}_{slow}_{signal}": "signal",
        },
    )
