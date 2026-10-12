"""Tests reuse the real example host's data recipes rather than duplicating preparation."""

import runpy
from pathlib import Path

HOST = Path(__file__).resolve().parents[1] / "examples/advanced/run_author.py"


def example_chart(namespace):
    return runpy.run_path(str(HOST))["chart_for"](namespace["__file__"])
