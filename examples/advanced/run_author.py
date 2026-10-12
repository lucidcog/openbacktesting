"""宿主加载可信作者脚本，注入示例行情与品种后运行；runpy 不是沙箱。

chart_for 只提供离线示例配方；真实产品须提供当前图表的实际快照。
"""

import argparse
import runpy
from pathlib import Path

import pandas as pd
from openbacktesting import DataContext, Timeframe, runtime
from openbacktesting.broker import InstrumentSpec
from openbacktesting.test import GOOG


def chart_for(path):
    """提供作者示例的显式宿主数据；不让策略文件负责选择图表。"""
    name = Path(path).name
    if name in {
        "local_value_helpers.py",
        "local_builtin_indicators.py",
        "closed_trade_statistics.py",
    }:
        prices = [100.0, 112.0, 98.0, 102.0, 100.0, 103.0, 104.0, 102.0]
        if name == "closed_trade_statistics.py":
            prices = prices[:5]
        frame = pd.DataFrame(
            {
                "Open": prices,
                "Close": prices,
                "High": [p + 1 for p in prices],
                "Low": [p - 1 for p in prices],
                "Volume": [1.0 + i % 3 for i in range(len(prices))],
                "Reset": [int(i % 4 == 0) for i in range(len(prices))],
                "Regime": [i % 3 for i in range(len(prices))],
            },
            index=pd.date_range("2026-01-01", periods=len(prices), tz="UTC"),
        )
        instrument = InstrumentSpec(symbol="LOCAL", price_tick=0.05)
    elif name == "fractional_sizing.py":
        data = pd.DataFrame(
            {"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0},
            index=pd.date_range("2026-01-01", periods=9, tz="UTC"),
        )
        frame = data.copy()
        instrument = InstrumentSpec(symbol="EXAMPLE", quantity_step=0.001)
    elif name == "strategy_logs.py":
        frame = GOOG.iloc[:4].copy()
        instrument = InstrumentSpec(symbol="GOOG")
    elif name in {"custom_indicators.py", "all_inputs.py"}:
        frame = GOOG.iloc[:120].copy()
        instrument = InstrumentSpec(symbol="GOOG")
    elif name == "confirmed_events.py":
        frame = GOOG.copy()
        # 示例将每个月的首根输入 bar 标记为新周期；生产数据须自行保证周期完整。
        months = frame.index.to_period("M")
        frame["PeriodStart"] = ~months.duplicated()
        frame = frame.copy()
        instrument = InstrumentSpec(symbol="GOOG")
    elif name == "plotting.py":
        frame = GOOG.iloc[:120].copy()
        instrument = InstrumentSpec(symbol="GOOG")
    elif name == "trading_lifecycle.py":
        data = pd.DataFrame(
            {"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0},
            index=pd.date_range("2026-01-01", periods=9, tz="UTC"),
        )
        frame = data.copy()
        instrument = InstrumentSpec(symbol="GOOG")
    elif name == "ema_inputs.py" or name == "first_backtest.py":
        frame = GOOG.copy()
        instrument = InstrumentSpec(symbol="GOOG")
    elif name == "managed_orders.py":
        data = pd.DataFrame(
            {
                "Open": [100, 100, 100, 100, 100, 110, 110, 105],
                "High": [106, 106, 106, 106, 106, 120, 115, 110],
                "Low": [94, 94, 94, 94, 94, 99, 100, 100],
                "Close": [100, 100, 100, 100, 100, 115, 105, 105],
            },
            index=pd.date_range("2026-01-01", periods=8, tz="UTC"),
        )
        frame = data.copy()
        instrument = InstrumentSpec(price_tick=0.5)
    elif name in {"data_sources.py", "ema_macd.py", "cross_signals.py", "bar_states.py"}:
        frame = GOOG.copy()
        instrument = InstrumentSpec(symbol="GOOG")
    else:
        raise ValueError(f"没有示例图表配方: {name}")
    if frame.index.tz is None:
        frame.index = frame.index.tz_localize("UTC")
    return {
        "data": frame,
        "context": DataContext(Timeframe.days(1), "UTC"),
        "instrument": instrument,
    }


def main(path=None):
    if path is None:
        path = Path(__file__).resolve().parents[1] / "strategies/first_backtest.py"
    namespace = runpy.run_path(str(path))
    runtime.describe(namespace)
    result = runtime.run(namespace, **chart_for(path))
    print(result[["Return [%]", "# Trades", "Max. Drawdown [%]"]])
    print(result["_equity_curve"].tail())
    print(result["_trades"].tail())
    print(result["_order_sizing"])  # 请求预算与实际成交分开核对。
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path)
    main(parser.parse_args().path)
