"""统计利率的纯数值校验，不依赖运行或账户。"""

from math import isfinite
from numbers import Real


def validate_risk_free_rate(value: float) -> float:
    """接收年化小数，拒绝布尔、非有限值和区间外值。"""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("risk_free_rate 必须为有限数值")
    value = float(value)
    if not isfinite(value) or not -1 < value < 1:
        raise ValueError("risk_free_rate 必须在 (-1, 1)")
    return value
