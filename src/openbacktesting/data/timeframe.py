"""图表时间周期的单位与不可变值；不推断行情或重采样。"""

from dataclasses import dataclass
from enum import StrEnum


class TimeframeUnit(StrEnum):
    """时间 bar 单位；日历单位不隐式换算为固定秒数。"""

    SECOND = "second"
    MINUTE = "minute"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


def _positive_integer(value: int) -> int:
    if type(value) is not int:
        raise TypeError("周期倍数必须为整数，不接受 bool 或浮点数")
    if value <= 0:
        raise ValueError("周期倍数必须为正整数")
    return value


@dataclass(frozen=True)
class Timeframe:
    """周期值；数据源支持范围由宿主验证，不承诺所有组合都有行情。"""

    unit: TimeframeUnit
    multiplier: int

    def __post_init__(self):
        if not isinstance(self.unit, TimeframeUnit):
            raise TypeError("unit 必须为 TimeframeUnit")
        _positive_integer(self.multiplier)

    @classmethod
    def seconds(cls, value: int) -> "Timeframe":
        """创建秒周期。"""
        return cls(TimeframeUnit.SECOND, value)

    @classmethod
    def minutes(cls, value: int) -> "Timeframe":
        """创建分钟周期。"""
        return cls(TimeframeUnit.MINUTE, value)

    @classmethod
    def hours(cls, value: int) -> "Timeframe":
        """小时规范化为分钟；24 小时不等于日线。"""
        return cls.minutes(_positive_integer(value) * 60)

    @classmethod
    def days(cls, value: int) -> "Timeframe":
        """创建日历日周期。"""
        return cls(TimeframeUnit.DAY, value)

    @classmethod
    def weeks(cls, value: int) -> "Timeframe":
        """创建日历周周期。"""
        return cls(TimeframeUnit.WEEK, value)

    @classmethod
    def months(cls, value: int) -> "Timeframe":
        """创建日历月周期。"""
        return cls(TimeframeUnit.MONTH, value)

    def snapshot(self) -> dict:
        """返回独立的 unit/multiplier 纯值。"""
        return {"unit": self.unit.value, "multiplier": self.multiplier}
