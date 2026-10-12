"""平铺作者配置、宿主解码与低层适配的行为契约。"""

import inspect
import json
import pickle
from dataclasses import fields

import pandas as pd
import pytest
from openbacktesting import (
    Backtest,
    CommissionType,
    EndPolicy,
    ExecutionTiming,
    QuantityType,
    SlippageType,
    Strategy,
    backtest,
    inputs,
    runtime,
)
from openbacktesting.broker import Commission, Slippage
from openbacktesting.simulation.config import BacktestSettings, DefaultOrderSize
from test_backtest_declaration import chart, namespace

ENUMS = {
    "commission_type": CommissionType,
    "default_qty_type": QuantityType,
    "slippage_type": SlippageType,
    "execution_timing": ExecutionTiming,
    "end_policy": EndPolicy,
}


@pytest.mark.parametrize("field,kind", ENUMS.items())
def test_enum_identity_and_boundaries(field, kind):
    for member in kind:
        assert pickle.loads(pickle.dumps(member)) is member
        assert not isinstance(member, str)
        value = BacktestSettings(**{field: member})
        assert value.snapshot()[field] == member.value
        assert BacktestSettings.from_snapshot(value.snapshot()) == value
        assert value.resolve({field: member.value}) == value
        assert value.resolve({field: member}) == value
        for bad in (member.value, Commission(), {}, None, 1, True):
            with pytest.raises(TypeError, match=field):
                backtest(**{field: bad})
        for bad in (member.value.upper(), " " + member.value, "unknown"):
            with pytest.raises(ValueError, match=field):
                value.resolve({field: bad})
        wrong = EndPolicy.MARK_TO_MARKET if kind is not EndPolicy else QuantityType.FIXED
        with pytest.raises(TypeError, match=field):
            backtest(**{field: wrong})
        with pytest.raises(TypeError, match=field):
            value.resolve({field: wrong})


@pytest.mark.parametrize(
    "field",
    [
        "cash",
        "spread",
        "commission_value",
        "risk_free_rate",
        "default_qty_value",
        "margin",
        "slippage_value",
        "max_gross_exposure",
    ],
)
@pytest.mark.parametrize("value", [True, False, "1", [], float("nan"), float("inf"), -float("inf")])
def test_numeric_fields_reject_non_finite_and_non_numeric(field, value):
    with pytest.raises((TypeError, ValueError)):
        BacktestSettings(**{field: value})


@pytest.mark.parametrize(
    "values",
    [
        {"commission_value": -10.001},
        {"commission_value": 10},
        {"commission_type": CommissionType.CASH_PER_ORDER, "commission_value": -1},
        {"commission_type": CommissionType.CASH_PER_CONTRACT, "commission_value": -1},
        {"default_qty_value": 0},
        {"default_qty_value": -1},
        {"default_qty_type": QuantityType.PERCENT_OF_EQUITY, "default_qty_value": 100.1},
        {"slippage_value": -1},
        {"cash": 0},
        {"margin": 0},
        {"margin": 1.01},
        {"spread": -0.01},
        {"spread": 1},
        {"max_gross_exposure": 0},
        {"risk_free_rate": -1},
        {"risk_free_rate": 1},
    ],
)
def test_numeric_ranges(values):
    with pytest.raises(ValueError):
        BacktestSettings(**values)


@pytest.mark.parametrize("field", ["allow_short", "hedging", "exclusive_orders"])
@pytest.mark.parametrize("value", [0, 1, None, "true"])
def test_boolean_fields_are_strict(field, value):
    with pytest.raises(TypeError, match=field):
        BacktestSettings(**{field: value})


def test_signature_defaults_and_percent_boundaries():
    signature = inspect.signature(backtest)
    assert list(signature.parameters) == [field.name for field in fields(BacktestSettings)]
    assert len(signature.parameters) == 16
    assert all(p.kind == p.KEYWORD_ONLY for p in signature.parameters.values())
    assert BacktestSettings().kwargs()["commission"] == Commission()
    assert BacktestSettings().kwargs()["default_order_size"] is None
    assert BacktestSettings(commission_value=-10).kwargs()["commission"] == Commission(
        relative=-0.1
    )
    assert BacktestSettings(commission_value=9.99).kwargs()["commission"] == Commission(
        relative=0.0999
    )
    assert BacktestSettings(default_qty_value=1000).kwargs()["default_order_size"].value == 1000
    assert (
        BacktestSettings(default_qty_type=QuantityType.PERCENT_OF_EQUITY, default_qty_value=100)
        .kwargs()["default_order_size"]
        .value
        == 1
    )
    for field, value in (
        ("commission", Commission()),
        ("slippage", Slippage()),
        ("default_order_size", DefaultOrderSize("fixed", 1)),
    ):
        with pytest.raises(TypeError, match=field):
            backtest(**{field: value})
        with pytest.raises(ValueError, match=field):
            BacktestSettings().resolve({field: value})


@pytest.mark.parametrize(
    "type_field,value_field,new_type",
    [
        ("commission_type", "commission_value", CommissionType.CASH_PER_ORDER),
        ("default_qty_type", "default_qty_value", QuantityType.PERCENT_OF_EQUITY),
        ("slippage_type", "slippage_value", SlippageType.FIXED),
    ],
)
def test_paired_override_is_explicit_and_atomic(type_field, value_field, new_type):
    base = BacktestSettings(default_qty_value=2)
    assert base.resolve({value_field: 3}).snapshot()[value_field] == 3
    assert base.resolve({type_field: getattr(base, type_field)}) == base
    overrides = {type_field: new_type.value, "cash": 20_000}
    with pytest.raises(ValueError, match=value_field):
        base.resolve(overrides)
    assert base.cash == 10_000 and overrides["cash"] == 20_000
    overrides[value_field] = None if value_field == "default_qty_value" else 0
    resolved = base.resolve(overrides)
    overrides["cash"] = 1
    assert resolved.cash == 20_000 and getattr(resolved, type_field) is new_type
    assert base.resolve({"default_qty_value": None}).kwargs()["default_order_size"] is None


def test_complete_json_snapshot_and_independent_copies():
    base = BacktestSettings(
        commission_value=0.2, default_qty_type=QuantityType.PERCENT_OF_EQUITY, default_qty_value=10
    )
    snapshot = base.snapshot()
    assert len(snapshot) == 16 and snapshot["commission_value"] == 0.2
    assert snapshot["default_qty_value"] == 10
    assert BacktestSettings.from_snapshot(json.loads(json.dumps(snapshot, allow_nan=False))) == base
    assert pickle.loads(pickle.dumps(base)) == base
    for bad in ([], None):
        with pytest.raises(TypeError, match="映射"):
            BacktestSettings.from_snapshot(bad)
    for bad in ({}, snapshot | {"unknown": 0}, snapshot | {"commission": {"relative": 0.002}}):
        with pytest.raises(ValueError, match="字段"):
            BacktestSettings.from_snapshot(bad)
    for bad in (CommissionType.PERCENT, {"relative": 0.002}, [], Commission()):
        with pytest.raises(TypeError, match="JSON"):
            BacktestSettings.from_snapshot(snapshot | {"commission_type": bad})
    snapshot["cash"] = 1
    assert base.snapshot()["cash"] == 10_000


@backtest(default_qty_value=2, commission_value=0.2)
class Trades(Strategy):
    period = inputs.int(2, title="周期")

    def init(self):
        pass

    def next(self):
        if len(self.data) == 2:
            self.buy()
        elif len(self.data) == 4:
            self.close_position()


@pytest.mark.parametrize(
    "fee,amount,native_fee",
    [
        (CommissionType.PERCENT, 0.2, Commission(relative=0.002)),
        (CommissionType.PERCENT, -1, Commission(relative=-0.01)),
        (CommissionType.CASH_PER_ORDER, 2, Commission(fixed=2)),
        (CommissionType.CASH_PER_CONTRACT, 0.5, Commission(per_unit=0.5)),
    ],
)
@pytest.mark.parametrize(
    "qty_type,qty_value,native_size",
    [
        (QuantityType.FIXED, 2, DefaultOrderSize("fixed", 2)),
        (QuantityType.PERCENT_OF_EQUITY, 10, DefaultOrderSize("equity_fraction", 0.1)),
    ],
)
@pytest.mark.parametrize("slip_type", list(SlippageType))
@pytest.mark.parametrize(
    "timing,end",
    [
        (ExecutionTiming.NEXT_OPEN, EndPolicy.MARK_TO_MARKET),
        (ExecutionTiming.SAME_CLOSE, EndPolicy.CLOSE_AT_LAST_CLOSE),
    ],
)
def test_flat_runtime_matches_native_ledger(
    fee, amount, native_fee, qty_type, qty_value, native_size, slip_type, timing, end
):
    args = chart()
    overrides = {
        "commission_type": fee.value,
        "commission_value": amount,
        "default_qty_type": qty_type.value,
        "default_qty_value": qty_value,
        "slippage_type": slip_type.value,
        "slippage_value": 0.5,
        "execution_timing": timing.value,
        "end_policy": end.value,
    }
    result = runtime.run(namespace(Trades), settings=overrides, **args)
    native = Backtest(
        args["data"],
        Trades,
        context=args["context"],
        instrument=args["instrument"],
        commission=native_fee,
        default_order_size=native_size,
        slippage=Slippage(slip_type.value, 0.5),
        execution_timing=timing.value,
        end_policy=end.value,
    ).run()
    for table in ("_fills", "_trades", "_equity_curve", "_orders"):
        pd.testing.assert_frame_equal(result[table], native[table])
    assert result.attrs["commission"] == native_fee.snapshot()
    descriptor = runtime.describe(namespace(Trades))
    assert descriptor["backtest"]["schemaVersion"] == 2
    assert descriptor["schemaVersion"] == inputs.describe(Trades)["schemaVersion"]
    assert descriptor["schemaHash"] == inputs.describe(Trades)["schemaHash"]
    assert result.attrs["backtest_snapshot"]["schemaVersion"] == 2
    assert result.attrs["backtest_snapshot"]["settings"]["commission_value"] == amount
    assert descriptor["backtest"]["settings"]["commission_value"] == 0.2


def test_invalid_override_precedes_strategy_construction(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("错误配置不应构造策略")

    monkeypatch.setattr(Trades, "__init__", forbidden)
    for overrides in (
        {"commission_type": "cash_per_order"},
        {"cash": 1, "slippage_value": -1},
        {"end_policy": "MARK_TO_MARKET"},
        {"commission": {"relative": 0.002}},
    ):
        with pytest.raises(ValueError):
            runtime.run(namespace(Trades), settings=overrides, **chart())


@pytest.mark.parametrize(
    "first",
    ["openbacktesting.broker", "openbacktesting.strategy", "openbacktesting.simulation.config"],
)
def test_import_order_in_fresh_interpreter(first):
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            f"""
import importlib, pickle
importlib.import_module({first!r})
import openbacktesting as api
from openbacktesting.simulation import config
for name in ('CommissionType', 'QuantityType', 'SlippageType', 'ExecutionTiming', 'EndPolicy'):
    kind = getattr(api, name)
    assert kind is getattr(config, name)
    for member in kind:
        assert pickle.loads(pickle.dumps(member)) is member
""",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("slip,value", [(SlippageType.FIXED, 1), (SlippageType.BPS, 100)])
def test_flat_execution_prices_limits_and_terminal_policy(slip, value):
    from test_strategy_settings import frame, run

    options = BacktestSettings(slippage_type=slip, slippage_value=value).kwargs()
    limited = run(
        lambda s, i: s.buy(qty=1, limit=100) if i == 1 else None,
        data=frame().assign(High=100),
        **options,
    )
    assert limited._fills.empty
    bounded = run(
        lambda s, i: s.buy(qty=1) if i == 1 else None, data=frame().assign(High=100), **options
    )
    assert bounded._fills.price.tolist() == [100]
    options = BacktestSettings(
        slippage_type=slip,
        slippage_value=value,
        commission_type=CommissionType.CASH_PER_ORDER,
        commission_value=5,
        end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE,
    ).kwargs()
    closed = run(lambda s, i: s.buy(qty=1) if i in (1, 7) else None, **options)
    assert closed._fills.price.tolist() == [101, 99]
    assert closed._fills.fee.tolist() == [5, 5]
    assert closed._fills.iloc[-1].reason == "end_liquidation"
    assert closed._orders.query("order_id == 'order-2'").iloc[0].reason == "end_of_data"
    assert closed._final_account["balance"] == 9988


def test_same_close_enum_preserves_conditional_and_protection_delay():
    from test_strategy_settings import run

    options = BacktestSettings(execution_timing=ExecutionTiming.SAME_CLOSE).kwargs()
    conditional = run(lambda s, i: s.buy(qty=1, limit=100) if i == 1 else None, **options)
    assert conditional._fills.bar_index.tolist() == [2]
    protected = run(lambda s, i: s.buy(qty=1, sl=95, tp=105) if i == 1 else None, **options)
    assert protected._trades.EntryBar.tolist() == [1]
    assert protected._trades.ExitBar.tolist() == [2]
    assert protected._trades.ExitPrice.tolist() == [95]
