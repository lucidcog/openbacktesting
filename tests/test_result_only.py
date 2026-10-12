"""验证结果计算不依赖展示能力，且稀疏信号不改变执行时序。"""

import importlib.util
import inspect
import subprocess
import sys
import textwrap
from pathlib import Path

import openbacktesting as api
import numpy as np
from openbacktesting import engine, lib
from test_engine_edges import Idle, flat_data


def test_removed_rendering_api_and_resources():
    assert not hasattr(api.Backtest, "plot")
    assert not hasattr(api, "set_bokeh_output")
    assert not hasattr(engine, "plot")
    assert not hasattr(lib, "plot_heatmaps")
    assert importlib.util.find_spec("openbacktesting.plotting") is not None
    for name in ("_plotting",):
        assert not hasattr(api, name)
        assert importlib.util.find_spec(f"openbacktesting.{name}") is None
    assert not (Path(api.__file__).parent / "autoscale_cb.js").exists()
    parameters = inspect.signature(api.Strategy.ind).parameters
    assert not {"plot", "overlay", "color", "scatter"}.intersection(parameters)
    assert "plot" not in inspect.signature(lib.SignalStrategy.set_signal).parameters


def test_indicator_readiness_is_explicit_computation_metadata():
    observed = []

    class Events(Idle):
        def init(self):
            self.events = self.ind(lambda: np.array([np.nan] * 4 + [2.0] * 4), name="event")

        def next(self):
            observed.append(len(self.data) - 1)

    result = api.Backtest(flat_data(), Events).run()
    indicator = result["_strategy"].events
    assert observed == list(range(8))
    assert set(indicator._opts) == {"index"}
    assert indicator.name == "event"
    assert indicator.s.index.equals(flat_data().index)


def test_sparse_signals_trade_at_first_event_without_warmup_delay():
    class Signals(lib.SignalStrategy):
        def init(self):
            self.set_signal([0, 2, 0, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0, 0])

    result = api.Backtest(flat_data(), Signals).run()
    trade = result["_trades"].iloc[0]
    assert (trade.EntryBar, trade.ExitBar, trade.Size) == (2, 4, 2)
    assert all("warmup" not in i._opts for i in result["_strategy"]._indicators)


def test_backtest_and_optimization_without_rendering_imports_or_output(tmp_path):
    # 独立进程避免父进程已导入模块掩盖依赖，同时检测默认输出副作用。
    source = textwrap.dedent("""
        import importlib.abc
        import sys
        from pathlib import Path
        from unittest.mock import patch

        class NoRendering(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname.split('.')[0] in {'bokeh', 'matplotlib', 'plotly', 'seaborn'}:
                    raise AssertionError(f'Unexpected rendering import: {fullname}')

        sys.meta_path.insert(0, NoRendering())
        with patch('webbrowser.open', side_effect=AssertionError('browser opened')):
            from openbacktesting import Backtest
            from openbacktesting.test import GOOG, SMA
            from openbacktesting.test._test import SmaCross

            from openbacktesting.plotting import export_result
            class VisualSma(SmaCross):
                def init(self):
                    super().init()
                    self.plotting.line(self.close)

            bt = Backtest(GOOG.iloc[:80], VisualSma, end_policy="close_at_last_close")
            result = bt.run(fast=5, slow=10)
            assert not result['_trades'].empty
            assert len(result['_equity_curve']) == 80
            best, scores = bt.optimize(
                fast=[3, 5], slow=[10, 15], return_heatmap=True, random_state=42
            )
            assert export_result(best)["plots"]
            assert len(scores) == 4
            assert not best['_trades'].empty
            assert not list(Path.cwd().iterdir())
        assert not {'bokeh', 'matplotlib', 'plotly', 'seaborn'}.intersection(sys.modules)
    """)
    process = subprocess.run(
        [sys.executable, "-c", source],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert process.returncode == 0, process.stdout + process.stderr
