"""Verify resources, semantics, and execution boundaries at greater risk during extraction."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from native_probe import normalize, observe

from openbacktesting import Backtest
from openbacktesting.test import GOOG
from openbacktesting.test._test import SmaCross


def test_native_semantics_match_fixed_source():
    expected = json.loads(Path(__file__).with_name("native-baseline.json").read_text())
    # First-bar execution adds only these early callbacks before any position exists; preserve the historical trade baseline.
    for case in expected.values():
        first = case["callbacks"][0][0]
        case["callbacks"] = [[i, 0.0, 10000.0] for i in range(first)] + case["callbacks"]
    assert normalize(observe()) == expected


def test_optional_optimizer_has_clear_error():
    bt = Backtest(GOOG.iloc[:100], SmaCross, end_policy="close_at_last_close")
    with patch.dict("sys.modules", {"sambo": None}), pytest.raises(ImportError, match="sambo"):
        bt.optimize(fast=[5, 10], slow=[20, 30], method="sambo")
