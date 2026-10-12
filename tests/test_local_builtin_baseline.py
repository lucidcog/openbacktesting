"""扩展前冻结的默认输出；夹具不得随算法更新自动再生成。"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from openbacktesting.indicators import compute

NAMES = ("true_range", "kc", "alma", "linreg", "pivot_points")
CASES = ("normal", "short", "missing", "flat", "gap")
DEFAULTS = {
    "true_range": {"handle_na": False},
    "kc": {"use_true_range": True},
    "alma": {"floor": False},
    "linreg": {"offset": 0},
    "pivot_points": {"developing": False},
}


def baseline_data(case):
    n = 32
    close = 100 + np.arange(n) * 0.3 + np.sin(np.arange(n))
    frame = pd.DataFrame(
        {
            "Open": close - 0.1,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": np.full(n, 100.0),
            "anchor": (np.arange(n) % 8 == 0).astype(float),
        },
        index=pd.date_range("2026-01-01", periods=n, freq="h"),
    )
    if case == "short":
        frame = frame.iloc[:2].copy()
    elif case == "missing":
        frame.iloc[20, :5] = np.nan
    elif case == "flat":
        frame.loc[:, ["Open", "High", "Low", "Close"]] = 100.0
    elif case == "gap":
        frame.iloc[24:, :4] += 20
    return frame


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("case", CASES)
def test_frozen_defaults(name, case):
    records = json.loads((Path(__file__).parent / "data/local_builtin_baseline.json").read_text())
    expected = records[f"{name}/{case}"]
    actual = compute("ta." + name, baseline_data(case))
    np.testing.assert_allclose(actual, np.array(expected["values"], dtype=float), equal_nan=True)
    np.testing.assert_array_equal(actual.valid, expected["valid"])
    explicit = compute("ta." + name, baseline_data(case), parameters=DEFAULTS[name])
    np.testing.assert_allclose(actual, explicit, equal_nan=True)
    np.testing.assert_array_equal(actual.valid, explicit.valid)


def test_degenerate_linreg_remains_invalid():
    assert not compute("ta.linreg", baseline_data("normal"), parameters={"length": 1}).valid.any()
