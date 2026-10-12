"""Immutable Bar state for fixed historical input."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BarState:
    """First/last snapshot at the current execution position; saved values do not change with the run cursor.

    is_first means input bar 0; is_last means the final input bar, not the end of the run.
    """

    is_first: bool
    is_last: bool
