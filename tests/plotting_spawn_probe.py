"""Real spawn optimization isolation, payload-free candidates, and resource cleanup after exceptions."""

import multiprocessing as mp

from test_engine_edges import flat_data
from test_plotting import VisualStrategy

import openbacktesting as api
from openbacktesting.plotting import export_result


def score(stats):
    assert "plotting_result" not in stats.attrs
    return stats["Equity Final [$]"]


def main():
    api.Pool = lambda: mp.get_context("spawn").Pool(2)
    bt = api.Backtest(flat_data(), VisualStrategy, end_policy="close_at_last_close")
    expected = export_result(bt.run())
    actual = export_result(bt.optimize(style=["line", "step"], maximize=score))
    assert actual == expected
    assert actual["colorEvents"]
    try:
        bt.optimize(failure=[True], maximize=score)
    except RuntimeError as error:
        assert "strategy failure" in str(error)
    else:
        raise AssertionError("Exception must propagate")
    assert export_result(bt.run()) == expected
    assert not mp.active_children()
    print("spawn plotting isolated")


if __name__ == "__main__":
    main()
