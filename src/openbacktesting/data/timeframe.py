"""Chart timeframe units and immutable values; no market-data inference or resampling."""

from dataclasses import dataclass
from enum import StrEnum


class TimeframeUnit(StrEnum):
    """Time-bar units; calendar units are not implicitly converted to fixed seconds."""

    SECOND = "second"
    MINUTE = "minute"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


def _positive_integer(value: int) -> int:
    if type(value) is not int:
        raise TypeError("Timeframe multiplier must be an integer; bool and floats are not accepted")
    if value <= 0:
        raise ValueError("Timeframe multiplier must be a positive integer")
    return value


@dataclass(frozen=True)
class Timeframe:
    """Timeframe value; the host validates data-source support, and not all combinations are guaranteed to have market data."""

    unit: TimeframeUnit
    multiplier: int

    def __post_init__(self):
        if not isinstance(self.unit, TimeframeUnit):
            raise TypeError("unit must be a TimeframeUnit")
        _positive_integer(self.multiplier)

    @classmethod
    def seconds(cls, value: int) -> "Timeframe":
        """Create a seconds timeframe."""
        return cls(TimeframeUnit.SECOND, value)

    @classmethod
    def minutes(cls, value: int) -> "Timeframe":
        """Create a minutes timeframe."""
        return cls(TimeframeUnit.MINUTE, value)

    @classmethod
    def hours(cls, value: int) -> "Timeframe":
        """Normalize hours to minutes; 24 hours is not a daily timeframe."""
        return cls.minutes(_positive_integer(value) * 60)

    @classmethod
    def days(cls, value: int) -> "Timeframe":
        """Create a calendar-day timeframe."""
        return cls(TimeframeUnit.DAY, value)

    @classmethod
    def weeks(cls, value: int) -> "Timeframe":
        """Create a calendar-week timeframe."""
        return cls(TimeframeUnit.WEEK, value)

    @classmethod
    def months(cls, value: int) -> "Timeframe":
        """Create a calendar-month timeframe."""
        return cls(TimeframeUnit.MONTH, value)

    def snapshot(self) -> dict:
        """Return independent plain unit/multiplier values."""
        return {"unit": self.unit.value, "multiplier": self.multiplier}
