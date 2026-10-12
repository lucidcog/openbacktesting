"""行情与交易的原生重采样规则。"""

from collections import OrderedDict

OHLCV_AGG = OrderedDict(
    (
        ("Open", "first"),
        ("High", "max"),
        ("Low", "min"),
        ("Close", "last"),
        ("Volume", "sum"),
    )
)
"""Dictionary of rules for aggregating resampled OHLCV data frames,
e.g.

    df.resample('4H', label='right').agg(OHLCV_AGG).dropna()
"""

TRADES_AGG = OrderedDict(
    (
        ("Size", "sum"),
        ("EntryBar", "first"),
        ("ExitBar", "last"),
        ("EntryPrice", "mean"),
        ("ExitPrice", "mean"),
        ("PnL", "sum"),
        ("ReturnPct", "mean"),
        ("EntryTime", "first"),
        ("ExitTime", "last"),
        ("Duration", "sum"),
    )
)
"""Dictionary of rules for aggregating resampled trades data,
e.g.

    stats['_trades'].resample('1D', on='ExitTime',
                              label='right').agg(TRADES_AGG)
"""
