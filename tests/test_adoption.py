"""验证迁入过程中风险较高的资源、语义与执行边界。"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from openbacktesting import Backtest
from openbacktesting.test import GOOG
from openbacktesting.test._test import SmaCross
from native_probe import normalize, observe


def test_native_semantics_match_fixed_source():
    expected = json.loads(Path(__file__).with_name("native-baseline.json").read_text())
    # 首根逐根执行仅增加这些尚未持仓的早期回调；历史交易基线保留。
    for case in expected.values():
        first = case["callbacks"][0][0]
        case["callbacks"] = [[i, 0.0, 10000.0] for i in range(first)] + case["callbacks"]
    assert normalize(observe()) == expected


def test_optional_optimizer_has_clear_error():
    bt = Backtest(GOOG.iloc[:100], SmaCross, end_policy="close_at_last_close")
    with patch.dict("sys.modules", {"sambo": None}), pytest.raises(ImportError, match="sambo"):
        bt.optimize(fast=[5, 10], slow=[20, 30], method="sambo")
