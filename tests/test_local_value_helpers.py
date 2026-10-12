"""Values, rejection domains, and real strategy consumption for price grids and color gradients."""

from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from openbacktesting import Backtest, Color, Strategy
from openbacktesting.broker import InstrumentSpec
from openbacktesting.plotting import export_result


@pytest.mark.parametrize(
    "value,expected", [(100.025, 100.05), (100.024, 100.0), (100.026, 100.05), (100.05, 100.05)]
)
def test_tick_nearest(value, expected):
    spec = InstrumentSpec(price_tick=0.05)
    assert spec.round_price_to_tick(value) == expected
    assert spec.price(expected) == expected
    assert spec.price(100.025, side="buy") == 100.05
    assert spec.price(100.025, side="sell") == 100.0
    with pytest.raises(ValueError):
        spec.price(100.025)
    assert spec.price_tick == 0.05


@pytest.mark.parametrize("value", [True, "1", None, 0, -1, np.nan, np.inf])
def test_tick_input_errors(value):
    with pytest.raises((ValueError, TypeError)):
        InstrumentSpec(price_tick=1).round_price_to_tick(value)


def test_tick_missing_zero_and_unrepresentable():
    with pytest.raises(ValueError, match="explicit"):
        InstrumentSpec().round_price_to_tick(100)
    with pytest.raises(ValueError):
        InstrumentSpec(price_tick=1).round_price_to_tick(0.1)
    with pytest.raises(ValueError, match="float"):
        InstrumentSpec(price_tick=0.03).round_price_to_tick(1e16)
    with pytest.raises(ValueError, match="float"):
        InstrumentSpec(price_tick=1e308).round_price_to_tick(1.7e308)


DARK = Color(0, 0, 0, 0)
LIGHT = Color(255, 255, 255, 255)


def gradient(value, lower=0.0, upper=10.0, a=DARK, b=LIGHT):
    return Color.from_gradient(value, lower=lower, upper=upper, lower_color=a, upper_color=b)


@pytest.mark.parametrize("value,expected", [(-1, 0), (0, 0), (5, 128), (10, 255), (11, 255)])
def test_gradient_bytes(value, expected):
    assert gradient(value) == Color(expected, expected, expected, expected)


def test_gradient_extremes_and_immutability():
    assert gradient(0, -1e308, 1e308) == Color(128, 128, 128, 128)
    assert gradient(0, -5e-324, 5e-324) == Color(128, 128, 128, 128)
    assert gradient(5, 0, 10, Color(255, 0, 100, 255), Color(0, 10, 50, 0)) == Color(
        128, 5, 75, 128
    )
    with pytest.raises(FrozenInstanceError):
        gradient(5).red = 1


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"value": True}, TypeError),
        ({"lower": "0"}, TypeError),
        ({"upper": None}, TypeError),
        ({"value": np.nan}, ValueError),
        ({"lower": -np.inf}, ValueError),
        ({"upper": np.inf}, ValueError),
        ({"value": 10**400}, ValueError),
        ({"lower": 10}, ValueError),
        ({"lower": 11}, ValueError),
        ({"a": None}, TypeError),
        ({"b": "#000000"}, TypeError),
    ],
)
def test_gradient_rejections(kwargs, error):
    with pytest.raises(error):
        gradient(**({"value": 5} | kwargs))


def test_values_in_strategy_keep_trade_and_color_contract():
    class Values(Strategy):
        def init(self):
            pass

        def next(self):
            if self.bar_state.is_first:
                price = self.instrument.round_price_to_tick(100.025)
                self.buy(qty=1, limit=price)
            shade = gradient(float(self.bar_index), upper=2)
            self.plotting.bar_color(shade)
            self.plotting.bg_color(shade.with_transparency(50))

    frame = pd.DataFrame(
        {
            "Open": [100.0] * 3,
            "High": [101.0] * 3,
            "Low": [99.0] * 3,
            "Close": [100.0] * 3,
            "Volume": [10.0] * 3,
        },
        index=pd.date_range("2026-01-01", periods=3),
    )
    result = Backtest(frame, Values, instrument=InstrumentSpec(price_tick=0.05)).run()
    assert result._fills.price.tolist() == [100.0]
    events = export_result(result)["colorEvents"]
    assert len(events) == 6
    assert [e["color"] for e in events if e["kind"] == "bar"] == [
        "#00000000",
        "#80808080",
        "#FFFFFFFF",
    ]
