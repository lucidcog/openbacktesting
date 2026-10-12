"""声明配置、数量覆盖、每单位佣金与利率重算；只在 main 中执行离线示例。"""

import json
import runpy
from pathlib import Path

import pandas as pd
from openbacktesting import (
    Backtest,
    CommissionType,
    DataContext,
    EndPolicy,
    ExecutionTiming,
    QuantityType,
    SlippageType,
    Strategy,
    Timeframe,
    backtest,
    runtime,
)
from openbacktesting.broker import Commission, InstrumentSpec
from openbacktesting.lib import compute_stats
from openbacktesting.test import GOOG


@backtest(
    risk_free_rate=0.02,
    default_qty_type=QuantityType.FIXED,
    default_qty_value=2,
    commission_type=CommissionType.CASH_PER_CONTRACT,
    commission_value=0.5,
    slippage_type=SlippageType.BPS,
    slippage_value=0,
    execution_timing=ExecutionTiming.NEXT_OPEN,
    end_policy=EndPolicy.MARK_TO_MARKET,
)
class RateExample(Strategy):
    def init(self):
        pass

    def next(self):
        if len(self.data) == 2:
            self.buy()
        elif len(self.data) == 55:
            self.close_position()


def read_settings(envelope):
    """宿主先验证回测配置封套版本，再把平铺设置交给 runtime。"""
    if type(envelope.get("schemaVersion")) is not int or envelope["schemaVersion"] != 2:
        raise ValueError("只接受 schemaVersion=2 的回测配置")
    return dict(envelope["settings"])


def main():
    data = GOOG.iloc[:80].copy()
    data.index = data.index.tz_localize("UTC")
    result = runtime.run(
        globals(),
        data=data,
        context=DataContext(Timeframe.days(1), "UTC"),
        instrument=InstrumentSpec(symbol="GOOG"),
    )
    inherited = compute_stats(stats=result, data=data)
    zero = compute_stats(stats=result, data=data, risk_free_rate=0.0)
    assert inherited.attrs["statistics_risk_free_rate"] == 0.02
    assert zero.attrs["statistics_risk_free_rate"] == 0.0
    assert zero.attrs["backtest_snapshot"]["settings"]["risk_free_rate"] == 0.02
    pd.testing.assert_frame_equal(result._fills, zero._fills)
    assert result["Sharpe Ratio"] != zero["Sharpe Ratio"]
    assert result._fills.fee.tolist() == [1, 1]
    print(result[["Return [%]", "# Trades", "Sharpe Ratio"]])

    # 同一作者脚本由宿主覆盖数量设置；作者不准备行情或手动执行回测。
    examples = Path(__file__).resolve().parents[1]
    path = examples / "strategies/fractional_sizing.py"
    namespace = runpy.run_path(str(path))
    chart = runpy.run_path(str(examples / "advanced/run_author.py"))["chart_for"](path)
    # 0.1 表示 0.1%，与原生 equity_fraction=0.001 对应；固定数量则为 0.1 单位。
    for kind in QuantityType:
        sized = runtime.run(
            namespace,
            **chart,
            settings={
                "default_qty_type": kind,
                "default_qty_value": 0.1,
            },
        )
        assert sized._fills.qty.tolist() == [0.1, 0.1, 0.2]
    try:
        runtime.run(namespace, **chart, settings={"default_qty_value": 0.0001})
    except ValueError as error:
        assert "below_min_quantity" in str(error)
        print("过小预算在提交前拒绝：", error)
    else:
        raise AssertionError("低于数量步长的预算必须拒绝")
    # 作者用枚举，JSON 宿主用严格字符串；类型切换必须连同数值提交。
    envelope = json.loads(json.dumps(runtime.describe(namespace)["backtest"]))
    assert envelope["schemaVersion"] == 2
    replay = runtime.run(namespace, **chart, settings=read_settings(envelope))
    assert replay.attrs["backtest_snapshot"]["schemaVersion"] == 2
    for version in (1, 3, True, "2"):
        try:
            read_settings(envelope | {"schemaVersion": version})
        except ValueError:
            pass
        else:
            raise AssertionError("宿主必须拒绝旧版或未知版本")
    for patch, error_type in (
        ({"commission_type": "cash_per_order"}, ValueError),
        ({"default_qty_value": None}, TypeError),
    ):
        try:
            runtime.run(namespace, **chart, settings=patch)
        except error_type:
            pass
        else:
            raise AssertionError("类型切换缺值或无默认数量必须拒绝")

    @backtest(default_qty_value=2)
    class CostExample(Strategy):
        def init(self):
            pass

        def next(self):
            if len(self.data) == 2:
                self.buy()
            elif len(self.data) == 4:
                self.close_position()

    cost_namespace = {"__name__": __name__, "strategy": CostExample}
    for kind in CommissionType:
        charged = runtime.run(
            cost_namespace,
            **chart,
            settings={
                "commission_type": kind.value,
                "commission_value": 0.2,
            },
        )
        expected = (
            [0.2] * 2
            if kind is CommissionType.CASH_PER_ORDER
            else [q * 0.2 for q in charged._fills.qty]
        )
        # 固定价格为 100，因此本例 0.2% 与每单位 0.2 的费用恰好相等。
        assert charged._fills.fee.tolist() == expected
    for slip in SlippageType:
        for timing in ExecutionTiming:
            for end in EndPolicy:
                configured = runtime.run(
                    cost_namespace,
                    **chart,
                    settings={
                        "slippage_type": slip,
                        "slippage_value": 0.1,
                        "execution_timing": timing,
                        "end_policy": end,
                    },
                )
                settings = configured.attrs["backtest_snapshot"]["settings"]
                assert settings["slippage_type"] == slip.value
                assert settings["execution_timing"] == timing.value
                assert settings["end_policy"] == end.value
                assert not configured._fills.empty

    # 复合费用仍属于低层 Backtest：每次成交固定 5，加每单位 0.5。
    path = examples / "strategies/trading_lifecycle.py"
    lifecycle = runpy.run_path(str(path))["TradingLifecycle"]
    chart = runpy.run_path(str(examples / "advanced/run_author.py"))["chart_for"](path)
    combined = Backtest(
        chart["data"],
        lifecycle,
        context=chart["context"],
        instrument=chart["instrument"],
        commission=Commission(fixed=5, per_unit=0.5),
        allow_short=False,
        max_gross_exposure=0.2,
        end_policy="close_at_last_close",
    ).run()
    assert combined._final_account["fees_paid"] == 37
    assert combined._final_account["balance"] == 9963
    return result


if __name__ == "__main__":
    main()
