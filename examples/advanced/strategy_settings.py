"""Declared configuration, quantity overrides, per-unit commission, and interest recalculation; run offline examples only in main."""

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
    """The host validates the backtest configuration envelope version before passing flat settings to runtime."""
    if type(envelope.get("schemaVersion")) is not int or envelope["schemaVersion"] != 2:
        raise ValueError("Only schemaVersion=2 backtest configurations are accepted")
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

    # The host overrides quantity settings for the same author script; the author neither prepares data nor manually runs the backtest.
    examples = Path(__file__).resolve().parents[1]
    path = examples / "strategies/fractional_sizing.py"
    namespace = runpy.run_path(str(path))
    chart = runpy.run_path(str(examples / "advanced/run_author.py"))["chart_for"](path)
    # 0.1 means 0.1%, corresponding to native equity_fraction=0.001; fixed quantity means 0.1 units.
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
        print("Reject an undersized budget before submission:", error)
    else:
        raise AssertionError("A budget below the quantity step must be rejected")
    # Authors use enums; JSON hosts use strict strings. A type change must include its value.
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
            raise AssertionError("The host must reject old or unknown versions")
    for patch, error_type in (
        ({"commission_type": "cash_per_order"}, ValueError),
        ({"default_qty_value": None}, TypeError),
    ):
        try:
            runtime.run(namespace, **chart, settings=patch)
        except error_type:
            pass
        else:
            raise AssertionError("Reject a type change without its value or a missing default quantity")

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
        # The fixed price is 100, so 0.2% commission and 0.2 per unit happen to be equal in this example.
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

    # Composite commission remains a low-level Backtest feature: fixed 5 per fill plus 0.5 per unit.
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
