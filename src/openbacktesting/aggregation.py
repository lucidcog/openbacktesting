"""旧 aggregation 路径的兼容导出；实现位于 data.aggregation。"""

from openbacktesting.data.aggregation import (
    OHLCV_AGG,
    TRADES_AGG,
)

__all__ = ["OHLCV_AGG", "TRADES_AGG"]
