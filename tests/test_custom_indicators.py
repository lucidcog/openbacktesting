"""自定义入口替换、参数复用及运行隔离的公开契约。"""

import inspect

import numpy as np
import pandas as pd
import pytest
from openbacktesting import Backtest, Strategy, engine, lib
from openbacktesting.indicators.types import IndicatorError, IndicatorHandle
from openbacktesting.test import GOOG


def test_ind_replaces_old_entry_on_public_strategy_objects():
    assert Strategy is engine.Strategy is lib.Strategy
    for cls in (Strategy, engine.Strategy, lib.Strategy, lib.SignalStrategy, lib.TrailingStrategy):
        assert cls.ind is Strategy.ind
        assert not hasattr(cls, "I")
    assert str(inspect.signature(Strategy.ind)) == (
        "(self, func: 'Callable', *args, name=None, **kwargs) -> 'IndicatorHandle'"
    )

    calls = []

    class Probe(Strategy):
        def init(self):
            with pytest.raises(AttributeError, match="I"):
                self.I()  # 仅此反例验证旧入口已删除。
            self.line = self.ind(lambda: calls.append("init") or np.ones(len(self.data)))
            assert isinstance(self.line, IndicatorHandle)

        def next(self):
            with pytest.raises(IndicatorError, match="invalid-phase"):
                self.ind(lambda: calls.append("next"))

    Backtest(GOOG.iloc[:8], Probe).run()
    assert calls == ["init"]


def test_parameter_registrations_and_runs_keep_independent_cursors():
    calls = []

    def band(source, length, *, width):
        calls.append((length, width))
        middle = source.rolling(length).mean()
        return pd.DataFrame({"middle": middle, "upper": middle * (1 + width)})

    class TwoBands(Strategy):
        def init(self):
            self.fast = self.ind(band, self.close.s, 3, width=0.02, name=["middle", "upper"])
            self.copy = self.ind(band, self.close.s, 3, width=0.02, name=["middle", "upper"])
            self.slow = self.ind(band, self.close.s, 7, width=0.04, name=["middle", "upper"])
            self.seen = []
            self.snapshots = []

        def next(self):
            self.seen.append(len(self.data))
            for line in (self.fast, self.copy, self.slow):
                assert len(line["middle"]) == len(self.data)
            if not self.snapshots:
                self.snapshots.append(self.fast["middle"].s)

    class AnotherStrategy(TwoBands):
        pass

    data = GOOG.iloc[:30]
    first = Backtest(data, TwoBands).run()["_strategy"]
    original = first.fast.df.copy()
    bt = Backtest(data, AnotherStrategy)
    others = [bt.run()["_strategy"], bt.run()["_strategy"]]
    assert calls == [(3, 0.02), (3, 0.02), (7, 0.04)] * 3
    for owner in (first, *others):
        assert owner.seen == list(range(1, 31))
        assert len(owner.snapshots[0]) == 1
        assert owner.fast is not owner.copy
        np.testing.assert_array_equal(owner.fast, owner.copy)
        for handle, length, width in ((owner.fast, 3, 0.02), (owner.slow, 7, 0.04)):
            middle = data.Close.rolling(length).mean()
            np.testing.assert_allclose(handle["middle"], middle, equal_nan=True)
            np.testing.assert_allclose(handle["upper"], middle * (1 + width), equal_nan=True)
            assert handle.metadata["cache"] == "disabled"
            assert handle.ready.all()
            assert not handle.valid[:, : length - 1].any()
            with pytest.raises(ValueError):
                np.asarray(handle).setflags(write=True)
    assert len({id(owner.fast._cursor) for owner in (first, *others)}) == 3
    pd.testing.assert_frame_equal(first.fast.df, original)
