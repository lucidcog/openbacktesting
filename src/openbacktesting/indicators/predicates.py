"""当前可见输入的交叉判断；不登记指标，也不计算整段历史。"""

from collections.abc import Sequence
from numbers import Real

import numpy as np
import pandas as pd

from .types import IndicatorHandle

CrossInput = Sequence[float] | np.ndarray | pd.Series | IndicatorHandle | float


def _last_pair(value: CrossInput) -> tuple[float, float] | None:
    if isinstance(value, Real):
        return float(value), float(value)
    if isinstance(value, (str, bytes)) or not isinstance(
        value, (Sequence, np.ndarray, pd.Series, IndicatorHandle)
    ):
        raise TypeError("交叉判断输入须为数值序列、单通道句柄或数字常量")
    if isinstance(value, (np.ndarray, IndicatorHandle)) and value.ndim != 1:
        raise ValueError("交叉判断仅接受单通道序列；请先选择输出通道")
    if len(value) < 2:
        return None
    if isinstance(value, IndicatorHandle) and not value[-2:].valid.all():
        return None
    if isinstance(value, pd.Series):
        return float(value.iloc[-2]), float(value.iloc[-1])
    return float(value[-2]), float(value[-1])


def _cross_sides(left: CrossInput, right: CrossInput) -> tuple[bool, bool]:
    previous_left, previous_right = _last_pair(left), _last_pair(right)
    if previous_left is None or previous_right is None:
        return False, False
    before_left, current_left = previous_left
    before_right, current_right = previous_right
    if not np.isfinite((before_left, current_left, before_right, current_right)).all():
        return False, False
    return (
        current_left > current_right and before_left <= before_right,
        current_left < current_right and before_left >= before_right,
    )


class CrossPredicates:
    """self.ta 的即时布尔判断，与交叉指标使用相同的等值边界。"""

    def is_cross(self, left: CrossInput, right: CrossInput) -> bool:
        """判断当前可见的最后一根是否发生任一方向交叉。

        Args:
            left: 单通道句柄、数值序列或数字常量；不接受列名字符串。
            right: 单通道句柄、数值序列或数字常量；常量视为固定阈值。

        Returns:
            Python bool。前一根允许相等，当前相等不算交叉。
            不足两根或最后两根含 NaN/无穷值时为 False。
            在 next 调用只读取输入当前前缀，不登记指标或影响预热。
        """
        up, down = _cross_sides(left, right)
        return up or down

    def is_crossover(self, left: CrossInput, right: CrossInput) -> bool:
        """判断当前左值是否严格高于右值，且前一根左值小于等于右值。

        Args:
            left: 单通道句柄、数值序列或数字常量；不接受列名字符串。
            right: 单通道句柄、数值序列或数字常量；常量视为固定阈值。

        Returns:
            Python bool。只读取最后两根；不足两根或含 NaN/无穷值时为 False。
            有效位置与 ta.crossover 序列一致；不登记指标，可在 next 调用。
        """
        return _cross_sides(left, right)[0]

    def is_crossunder(self, left: CrossInput, right: CrossInput) -> bool:
        """判断当前左值是否严格低于右值，且前一根左值大于等于右值。

        Args:
            left: 单通道句柄、数值序列或数字常量；不接受列名字符串。
            right: 单通道句柄、数值序列或数字常量；常量视为固定阈值。

        Returns:
            Python bool。只读取最后两根；不足两根或含 NaN/无穷值时为 False。
            有效位置与 ta.crossunder 序列一致；不登记指标，可在 next 调用。
        """
        return _cross_sides(left, right)[1]
