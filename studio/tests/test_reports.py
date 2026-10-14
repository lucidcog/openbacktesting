import copy
import json
from pathlib import Path

import pytest

from openbacktesting_studio.artifacts import import_portfolio, write_manifest
from openbacktesting_studio.host import reports
from openbacktesting_studio.host.projection import project
from openbacktesting_studio.workspace import WorkspaceError

FIXTURES = Path(__file__).parent / "fixtures"


def result(tmp_path):
    for name in ["portfolio.json", "plotting.json"]:
        (tmp_path / name).write_bytes((FIXTURES / name).read_bytes())
    write_manifest(tmp_path, run_id="test", provenance={})
    return tmp_path


def test_authoritative_summary_paging_terminal_and_bounds(tmp_path):
    directory = result(tmp_path)
    original = json.loads((directory / "portfolio.json").read_text())
    assert reports.summary(directory)["summary"] == original["summary"]
    assert (
        reports.rows(directory, "closedFragments", 0, 1)["rows"]
        == original["trades"]["closedFragments"][:1]
    )
    assert reports.rows(directory, "openLots")["total"] == len(original["trades"]["openLots"])
    with pytest.raises(WorkspaceError):
        reports.rows(directory, "fills", limit=1001)
    curve = reports.curve(directory, 6)
    assert len(curve["points"]) <= 6
    assert curve["points"][-1]["bar"] == original["series"]["close"][-1]["barIndex"]
    assert curve["points"][-1]["observations"][-1] == original["series"]["close"][-1]
    assert len(curve["points"][-1]["observations"]) == 2
    assert curve["unorderedBounds"] == []
    assert curve["unorderedCount"] == sum(
        not row["ordered"] for row in original["series"]["account"]
    )


def test_chart_window_budgets_and_original_identity(tmp_path):
    directory = result(tmp_path)
    window = reports.chart(directory, 10, 5)
    assert window["window"]["originalBarIndices"] == list(range(10, 15))
    assert len(window["plotting"]["market"]["close"]["values"]) == 5
    assert all(10 <= event["anchorBar"] < 15 for event in window["plotting"]["markers"])
    with pytest.raises(WorkspaceError):
        reports.chart(directory, limit=20001)
    with pytest.raises(WorkspaceError):
        reports.chart(directory, start=999)


def test_manual_ohlcv_aggregation_does_not_mutate_original_and_clusters_retain_members(tmp_path):
    raw = json.loads((FIXTURES / "plotting.json").read_text())
    raw["sources"] = []
    raw["plots"] = []
    raw["fills"] = []
    count = len(raw["axes"][0]["labels"])
    original = copy.deepcopy(raw)
    projected = project(raw, 0, count, 12)
    assert raw == original
    assert projected["window"]["granularity"] > 1
    plotting = projected["plotting"]
    axis = plotting["axes"][0]
    for bucket in plotting["display"]["buckets"]:
        left, right = bucket["start"], bucket["end"]
        index = axis["indices"].index(right - 1)
        assert plotting["market"]["open"]["values"][index] == raw["market"]["open"]["values"][left]
        assert (
            plotting["market"]["close"]["values"][index]
            == raw["market"]["close"]["values"][right - 1]
        )
        assert plotting["market"]["high"]["values"][index] == max(
            raw["market"]["high"]["values"][left:right]
        )
        assert plotting["market"]["low"]["values"][index] == min(
            raw["market"]["low"]["values"][left:right]
        )
        assert plotting["market"]["volume"]["values"][index] == sum(
            raw["market"]["volume"]["values"][left:right]
        )
    result(tmp_path)
    fills = []
    for cluster in plotting["display"]["clusters"]:
        members = reports.events(tmp_path, cluster["start"], cluster["end"])["rows"]
        fills += [row["value"]["fill_id"] for row in members if row["kind"] == "fill"]
    assert sorted(fills) == sorted(row["fill_id"] for row in raw["tradingFacts"]["fills"])


def test_semantic_gap_budget_is_explicit_not_silent(tmp_path):
    raw = json.loads((FIXTURES / "plotting.json").read_text())
    source = raw["sources"][0]
    source["valid"] = [bool(index % 2) for index in range(len(source["valid"]))]
    with pytest.raises(WorkspaceError) as error:
        project(raw, 0, len(raw["axes"][0]["labels"]), 20)
    assert error.value.code == "ChartDetailBudget"


def test_independent_portfolio_and_verified_pairing(tmp_path):
    portfolio = json.loads((FIXTURES / "portfolio.json").read_text())
    plotting = json.loads((FIXTURES / "plotting.json").read_text())
    manifest = import_portfolio(FIXTURES / "portfolio.json", tmp_path / "report")
    assert manifest.provenance["reproducible"] is False
    assert reports.summary(tmp_path / "report")["summary"] == portfolio["summary"]
    with pytest.raises(WorkspaceError, match="no plotting"):
        reports.chart(tmp_path / "report")
    source = tmp_path / "pair.json"
    source.write_text(json.dumps({"portfolio": portfolio, "plotting": plotting}))
    import_portfolio(source, tmp_path / "pair")
    plotting["tradingFacts"]["fills"][0]["price"] += 1
    source.write_text(json.dumps({"portfolio": portfolio, "plotting": plotting}))
    with pytest.raises(ValueError, match="fills do not match"):
        import_portfolio(source, tmp_path / "bad")


def test_window_fetch_preserves_offset_points_computed_before_window(tmp_path):
    raw = json.loads((FIXTURES / "plotting.json").read_text())
    raw["plots"][0]["offsetBars"] = 5
    result = project(raw, 30, 50, 20)
    leading = result["plotting"]["plots"][0]["leading"]
    assert [row["time"] for row in leading] == list(range(30, 35))
    assert [row["value"] for row in leading] == raw["sources"][0]["values"][25:30]
    assert "leading" not in raw["plots"][0]


def test_allocation_location_metadata_preserves_authoritative_rows(tmp_path):
    directory = result(tmp_path)
    original = json.loads((directory / "portfolio.json").read_text())
    page = reports.rows(directory, "allocations", limit=1)
    assert page["rows"] == original["facts"]["allocations"][:1]
    fill_id = page["rows"][0]["fill_id"]
    fill = next(row for row in original["facts"]["fills"] if row["fill_id"] == fill_id)
    assert page["fillBars"] == {fill_id: fill["bar_index"]}
    assert "bar_index" not in page["rows"][0]
