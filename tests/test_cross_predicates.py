"""Direction, boundaries, cursors, and public entry points for crossover series and immediate boolean checks."""

import pickle

import numpy as np
import pandas as pd
import pytest

from openbacktesting import Backtest, Strategy, lib
from openbacktesting.indicators.methods import TechnicalAnalysis
from openbacktesting.indicators.types import IndicatorHandle
from openbacktesting.strategy import helpers


def no_registration(*args, **kwargs):
    raise AssertionError("Immediate checks must not register or calculate indicators")


TA = TechnicalAnalysis(no_registration)
NAMES = ("cross", "crossover", "crossunder")


@pytest.mark.parametrize(
    "left,right,expected",
    [
        ([0, 2], [1, 1], (True, True, False)),
        ([2, 0], [1, 1], (True, False, True)),
        ([1, 2], [1, 1], (True, True, False)),
        ([1, 0], [1, 1], (True, False, True)),
        ([0, 1], [1, 1], (False, False, False)),
        ([2, 1], [1, 1], (False, False, False)),
        ([0, 0], [1, 1], (False, False, False)),
        ([2, 2], [1, 1], (False, False, False)),
        ([1, 1], [1, 1], (False, False, False)),
        ([], [], (False, False, False)),
        ([0], [1, 0], (False, False, False)),
        ([0, 2], [1], (False, False, False)),
        ([0, 2, 2], [1, 1, 1], (False, False, False)),
    ],
)
@pytest.mark.parametrize("container", [list, tuple, np.array, pd.Series])
def test_latest_two_values_and_native_bool(left, right, expected, container):
    for name, result in zip(NAMES, expected):
        actual = getattr(TA, "is_" + name)(container(left), container(right))
        assert actual is result


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
@pytest.mark.parametrize("position", range(4))
def test_nonfinite_input_is_false(bad, position):
    values = [0.0, 2.0, 1.0, 1.0]
    values[position] = bad
    for name in NAMES:
        assert getattr(TA, "is_" + name)(values[:2], values[2:]) is False


def test_constants_pandas_positions_and_validation():
    assert TA.is_crossover([0, 2], 1) is True
    assert TA.is_crossunder(np.float64(1), [0, 2]) is True
    assert TA.is_cross(1, 2) is False
    assert TA.is_cross(np.int64(1), np.int64(1)) is False
    assert TA.is_crossover(pd.Series([0, 2], index=[-1, -2]), 1) is True
    for invalid in ("Close", b"Close", object(), {"a": 1}):
        with pytest.raises(TypeError, match="numeric sequences"):
            TA.is_cross(invalid, [0, 1])
    for invalid in (np.array(1), np.array([[0, 1], [1, 0]])):
        with pytest.raises(ValueError, match="single-channel"):
            TA.is_cross([0, 1], invalid)


def test_handle_validity_and_selected_channels():
    handle = IndicatorHandle([[0, 2], [1, 1]], name=["left", "right"], index=pd.RangeIndex(2))
    with pytest.raises(ValueError, match="single-channel"):
        TA.is_cross(handle, 1)
    assert TA.is_crossover(handle["left"], handle["right"]) is True
    masked = IndicatorHandle([0, 2], name="masked", index=pd.RangeIndex(2), valid=[False, True])
    assert TA.is_cross(masked, 1) is False


def test_predicates_match_series_at_every_visible_prefix_without_registration():
    left = [1, 2, 1, 0, 2, 0, np.nan, 2, 0, np.inf, 2, 0]
    frame = pd.DataFrame(
        {"Open": 1.0, "High": 3.0, "Low": 0.1, "Close": 1.0, "left": left, "right": 1.0},
        index=pd.date_range("2020-01-01", periods=len(left)),
    )
    seen = []

    class Signals(Strategy):
        def init(self):
            self.left = self.ind(lambda: np.array(left))
            self.signals = {name: getattr(self.ta, name)(self.left, self.close) for name in NAMES}
            for signal in self.signals.values():
                assert isinstance(signal, IndicatorHandle)
            # init sees complete input; test each prefix for fewer than two bars, gaps, and the last bar.
            cursor = self._indicator_cursor
            for size in range(len(left) + 1):
                cursor.length = size
                self.check_current()
            cursor.length = len(left)

        def check_current(self):
            registered = len(self._indicators)
            for name, signal in self.signals.items():
                actual = getattr(self.ta, "is_" + name)(self.left, self.close)
                expected = bool(len(signal) and signal.valid[-1] and signal[-1])
                assert actual is expected
            assert len(self._indicators) == registered

        def next(self):
            self.check_current()
            seen.append(len(self.close))

    result = Backtest(frame, Signals).run()
    # Registered series retain existing scheduling gates at gaps; immediate checks do not change that scheduling.
    assert seen == list(range(1, 13))
    assert len(result["_strategy"]._indicators) == 4


def test_predicates_alone_do_not_gate_next_on_gaps():
    left = [0, 2, np.nan, 0, 2]
    frame = pd.DataFrame(
        {"Open": 1.0, "High": 3.0, "Low": 0.1, "Close": 1.0},
        index=pd.date_range("2020-01-01", periods=len(left)),
    )
    seen = []

    class Live(Strategy):
        def init(self):
            self.left = self.ind(lambda: np.array(left))

        def next(self):
            seen.append((len(self.close), self.ta.is_cross(self.left, self.close)))
            assert len(self._indicators) == 1

    Backtest(frame, Live).run()
    assert seen == [(1, False), (2, True), (3, False), (4, False), (5, True)]


def test_removed_lib_and_helper_exports_and_legacy_pickle():
    for module in (lib, helpers):
        for name in NAMES:
            assert not hasattr(module, name)
    assert not set(NAMES).intersection(lib.__all__)
    # Deleted function references remain explicitly rejected.
    for name in ("cross", "crossover"):
        with pytest.raises(AttributeError, match=name):
            pickle.loads(f"copenbacktesting.lib\n{name}\n.".encode())
