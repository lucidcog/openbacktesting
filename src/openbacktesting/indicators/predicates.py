"""Crossing checks on currently visible inputs; no indicator registration or full-history computation."""

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
        raise TypeError("Crossing inputs must be numeric sequences, single-channel handles, or numeric constants")
    if isinstance(value, (np.ndarray, IndicatorHandle)) and value.ndim != 1:
        raise ValueError("Crossing checks accept only single-channel sequences; select an output channel first")
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
    """Immediate self.ta boolean predicates with the same equality boundaries as crossing indicators."""

    def is_cross(self, left: CrossInput, right: CrossInput) -> bool:
        """Check whether either-direction crossing occurs on the last currently visible bar.

        Args:
            left: Single-channel handle, numeric sequence, or numeric constant; column-name strings are not accepted.
            right: Single-channel handle, numeric sequence, or numeric constant; constants act as fixed thresholds.

        Returns:
            Python bool. Equality is allowed on the preceding bar; current equality is not a crossing.
            False with fewer than two bars or NaN/infinity in either of the last two bars.
            Calls in next read only the currently visible input prefix, without registering indicators or affecting warmup.
        """
        up, down = _cross_sides(left, right)
        return up or down

    def is_crossover(self, left: CrossInput, right: CrossInput) -> bool:
        """Check whether the current left value is strictly above the right, with the preceding left value at or below the right.

        Args:
            left: Single-channel handle, numeric sequence, or numeric constant; column-name strings are not accepted.
            right: Single-channel handle, numeric sequence, or numeric constant; constants act as fixed thresholds.

        Returns:
            Python bool. Read only the last two bars; False with fewer than two bars or NaN/infinity.
            Valid positions match the ta.crossover sequence; no registration, and calls in next are allowed.
        """
        return _cross_sides(left, right)[0]

    def is_crossunder(self, left: CrossInput, right: CrossInput) -> bool:
        """Check whether the current left value is strictly below the right, with the preceding left value at or above the right.

        Args:
            left: Single-channel handle, numeric sequence, or numeric constant; column-name strings are not accepted.
            right: Single-channel handle, numeric sequence, or numeric constant; constants act as fixed thresholds.

        Returns:
            Python bool. Read only the last two bars; False with fewer than two bars or NaN/infinity.
            Valid positions match the ta.crossunder sequence; no registration, and calls in next are allowed.
        """
        return _cross_sides(left, right)[1]
