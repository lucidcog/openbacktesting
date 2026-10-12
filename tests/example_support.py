"""测试复用真实示例宿主的行情配方；不复刻一份数据准备。"""

import runpy
from pathlib import Path

HOST = Path(__file__).resolve().parents[1] / "examples/advanced/run_author.py"


def example_chart(namespace):
    return runpy.run_path(str(HOST))["chart_for"](namespace["__file__"])
