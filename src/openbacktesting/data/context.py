"""宿主提供的图表上下文；品种规格单独绑定。"""

from dataclasses import dataclass
from zoneinfo import ZoneInfo

from openbacktesting.data.timeframe import Timeframe


@dataclass(frozen=True)
class DataContext:
    """描述已有行情的周期及图表、策略日历和统计共用的时区。

    带时区行情在策略构造前转换为此时区；绝对时刻与原始数据不变。
    统计按当地日界分组，切换时区后须重新运行，年化指标允许不同。
    不提供下载、重采样或交易所日历能力。
    """

    timeframe: Timeframe
    timezone: str

    def __post_init__(self):
        if not isinstance(self.timeframe, Timeframe):
            raise TypeError("timeframe 必须为 Timeframe")
        if not isinstance(self.timezone, str) or not self.timezone:
            raise TypeError("timezone 必须为非空 IANA 时区字符串")
        ZoneInfo(self.timezone)

    def snapshot(self) -> dict:
        """返回独立纯值，不复用可变请求对象。"""
        return {"timeframe": self.timeframe.snapshot(), "timezone": self.timezone}
