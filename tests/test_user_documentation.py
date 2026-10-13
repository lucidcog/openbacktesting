"""Execute published user examples and validate navigation/API presentation."""

import json
import re
import runpy
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/core"
TEMPLATES = ROOT / "scripts/docs"


def blocks(path):
    return re.findall(r"```python\n(.*?)```", path.read_text(), re.DOTALL)


# Indices select examples, not generated call signatures. Dependent snippets
# are executed together in the same script, just as the page instructs.
EXAMPLES = [
    ("quickstart", [0]),
    ("core", [0]),
    ("core", [1]),
    ("strategy", [0]),
    ("inputs", [0, 1]),
    ("indicator-api", [0, 1]),
    ("runtime", [0]),
    ("plotting", [0]),
    ("colors", [0]),
    ("portfolio", [0]),
    ("helpers", [0]),
    ("helpers", [1]),
    ("optimizer", [0]),
    ("events", [0]),
]


@pytest.mark.parametrize("page,indices", EXAMPLES)
def test_complete_user_examples(page, indices, tmp_path):
    source = DOCS / "quickstart.md" if page == "quickstart" else TEMPLATES / f"{page}.md.in"
    snippets = blocks(source)
    script = tmp_path / f"{page}.py"
    content = "\n\n".join(snippets[i] for i in indices)
    checks = {
        "quickstart": 'assert result["# Trades"] > 0\nassert len(result["_equity_curve"]) == len(GOOG)',
        "strategy": 'assert result["# Trades"] > 0',
        "runtime": 'assert result["# Trades"] == 1',
        "inputs": 'assert result["_strategy"].length == 40',
        "indicator-api": 'assert ema.valid[-1] and result["# Trades"] > 0',
        "plotting": 'assert len(payload["plots"]) == 3 and payload["colorEvents"]',
        "portfolio": 'assert report["trades"]["closedFragments"] and report["run"]["complete"]',
        "optimizer": 'assert len(ranking["rows"]) == 3 and report["run"]["complete"]',
        "events": 'assert len(result["_strategy"].fill_prices) == 2 and bt.get_logs()',
    }
    script.write_text(content + "\n" + checks.get(page, ""))
    process = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert process.returncode == 0, process.stdout + process.stderr


@pytest.mark.parametrize(
    "page,index", [("strategy", 1), ("trading", 2), ("trading", 4), ("helpers", 2)]
)
def test_strategy_method_recipes(page, index, tmp_path):
    snippet = blocks(TEMPLATES / f"{page}.md.in")[index]
    # Keep imports at module scope and place the documented methods in a subclass.
    import ast

    tree = ast.parse(snippet)
    imports, methods = [], []
    for node in tree.body:
        (methods if isinstance(node, ast.FunctionDef) else imports).append(
            ast.get_source_segment(snippet, node)
        )
    method_names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    for name in {"init", "next"} - method_names:
        methods.append(f"def {name}(self):\n    pass")
    script = tmp_path / "recipe.py"
    script.write_text(
        "from openbacktesting import Backtest, Strategy\nfrom openbacktesting.test import GOOG\n"
        + "\n".join(imports)
        + "\nclass Recipe(Strategy):\n"
        + "\n".join("    " + line for line in "\n".join(methods).splitlines())
        + "\nresult = Backtest(GOOG.iloc[:120], Recipe).run()\n"
    )
    values = runpy.run_path(str(script))
    assert len(values["result"]["_equity_curve"]) == 120


CATALOG = json.loads((ROOT / "src/openbacktesting/indicators/catalog.json").read_text())["entries"]


@pytest.mark.parametrize(
    "entry", [row for row in CATALOG if row["status"] == "available"], ids=lambda row: row["id"]
)
def test_every_indicator_page_runs(entry, tmp_path):
    page = DOCS / "reference/indicators" / (entry["id"].removeprefix("ta.") + ".md")
    script = tmp_path / "indicator_example.py"
    script.write_text(blocks(page)[0])
    namespace = runpy.run_path(str(script))
    latest = namespace["result"]["_strategy"].latest_value
    assert latest is not None and np.isfinite(latest), (
        f"No consumable value in {entry['id']} example"
    )


def test_generated_user_reference_is_current():
    process = subprocess.run(
        [sys.executable, str(ROOT / "scripts/core_docs.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert process.returncode == 0, process.stdout + process.stderr


def test_user_navigation_and_rendered_content():
    pages = [
        DOCS / "index.md",
        DOCS / "quickstart.md",
        *DOCS.glob("guides/*.md"),
        *(DOCS / "reference").rglob("*.md"),
    ]
    for page in pages:
        if page.name == "classification.md":
            continue
        text = page.read_text()
        assert "Qualified object:" not in text
        assert "```{toctree}" not in text and "```{raw}" not in text
        assert "{{api " not in text
        assert not re.search(r"(?:Strategy|Order|Position|Trade)\(broker", text)
        assert not re.search(r"\|\n\n\|", text), f"Broken Markdown table in {page}"
        without_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        for path, fragment in re.findall(r"\]\(([^)\s#]*)(?:#([^\s)]+))?\)", without_code):
            if ":" in path:
                continue
            target = (page.parent / path).resolve() if path else page
            assert target.is_file(), (page, path)
            if not fragment or target.suffix != ".md":
                continue
            target_text = re.sub(r"```.*?```", "", target.read_text(), flags=re.DOTALL)
            anchors = set(re.findall(r'<a id="([^"]+)"', target_text))
            for heading in re.findall(r"^#+ (.+)$", target_text, re.MULTILINE):
                heading = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
                anchors.add(heading)
            assert fragment in anchors, f"Broken anchor: {page.name} -> {target.name}#{fragment}"
