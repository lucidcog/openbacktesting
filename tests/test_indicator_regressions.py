"""Historical boundaries reproduced before the indicator overhaul; assert intended behavior rather than existing bugs."""

import numpy as np
import pandas as pd
import pytest

from openbacktesting import Backtest, Strategy


def frame(n=10):
    return pd.DataFrame(
        {key: np.arange(n, dtype=float) + 100 for key in ("Open", "High", "Low", "Close")},
        index=pd.date_range("2020-01-01", periods=n),
    )


def test_never_ready_indicator_still_runs_every_bar():
    seen = []

    class Probe(Strategy):
        def init(self):
            self.line = self.ind(lambda: np.full(len(self.data), np.nan))

        def next(self):
            seen.append(len(self.data))

    result = Backtest(frame(), Probe).run()
    assert seen == list(range(1, 11))
    assert result["# Trades"] == 0


def test_container_indicator_has_current_prefix_and_warmup():
    seen = []

    class Probe(Strategy):
        def init(self):
            self.lines = [self.ind(lambda: pd.Series(np.arange(10.0)).rolling(4).mean().values)]

        def next(self):
            seen.append((len(self.data), len(self.lines[0]), self.lines[0][-1]))

    Backtest(frame(), Probe).run()
    assert seen[0][:2] == (1, 1) and np.isnan(seen[0][2])
    assert seen[3] == (4, 4, 1.5)
    assert seen[4] == (5, 5, 2.5)
    assert all(data_len == line_len for data_len, line_len, _ in seen)


def test_same_length_wrong_index_is_rejected():
    data = frame()

    class Probe(Strategy):
        def init(self):
            self.line = self.ind(lambda: pd.Series(np.arange(10.0), index=data.index[::-1]))

        def next(self):
            raise AssertionError("Misaligned indicators must not enter the backtest")

    with pytest.raises(ValueError, match="index"):
        Backtest(data, Probe).run()
