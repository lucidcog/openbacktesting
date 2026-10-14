"""Read and page core facts without computing alternative accounting metrics."""

from pathlib import Path

from openbacktesting_studio.artifacts import strict_json, validate, validate_portfolio
from openbacktesting_studio.workspace import WorkspaceError


def portfolio(directory):
    validate(directory)
    return validate_portfolio(strict_json((Path(directory) / "portfolio.json").read_bytes()))


def summary(directory):
    payload = portfolio(directory)
    return {
        key: payload[key]
        for key in ["schemaVersion", "semantics", "run", "context", "summary", "diagnostics"]
    } | {
        "request": strict_json((Path(directory) / "request.json").read_bytes())
        if (Path(directory) / "request.json").is_file()
        else None
    }


def rows(directory, table, offset=0, limit=100):
    payload = portfolio(directory)
    if table in {"closedFragments", "openLots"}:
        values = payload["trades"][table]
    elif table in {"orders", "fills", "allocations", "orderEvents", "orderSizing"}:
        values = payload["facts"][table]
    elif table in {"close", "account"}:
        values = payload["series"][table]
    else:
        raise WorkspaceError("InvalidTable", "Unknown report table", 422)
    if offset < 0 or not 1 <= limit <= 1000:
        raise WorkspaceError("InvalidPage", "Page size must be between 1 and 1000", 422)
    page = values[offset : offset + limit]
    fill_ids = {row["fill_id"] for row in page if "fill_id" in row}
    return {
        "rows": page,
        "fillBars": {
            fill["fill_id"]: fill["bar_index"]
            for fill in payload["facts"]["fills"]
            if fill["fill_id"] in fill_ids
        },
        "total": len(values),
        "offset": offset,
        "limit": limit,
    }


def chart(directory, start=None, limit=5000, end=None):
    from openbacktesting_studio.host.projection import project

    path = Path(directory) / "plotting.json"
    if not path.is_file():
        raise WorkspaceError("PlottingUnavailable", "This result contains no plotting data", 404)
    if not 1 <= limit <= 20000:
        raise WorkspaceError("InvalidRange", "Chart budget must contain 1 to 20000 points", 422)
    payload = strict_json(path.read_bytes())
    if payload.get("schemaVersion") not in {"1.0.0", "1.1.0"} or any(
        feature not in {"core-v1", "bar-coloring-v1"}
        for feature in payload.get("requiredFeatures", [])
    ):
        raise WorkspaceError(
            "PlottingIncompatible", "Unsupported plotting version or required feature", 422
        )
    axis = next(axis for axis in payload["axes"] if axis["id"] == payload["market"]["axis"])
    count = len(axis["labels"])
    start = max(0, count - limit) if start is None else start
    end = min(count, start + limit) if end is None else end
    if not 0 <= start < max(count, 1) or not start <= end <= count:
        raise WorkspaceError("InvalidRange", "Chart range is outside the data", 422)
    return project(payload, start, end, limit)


def events(directory, start, end, offset=0, limit=100):
    if start < 0 or end <= start or offset < 0 or not 1 <= limit <= 1000:
        raise WorkspaceError("InvalidRange", "Invalid event member range or page", 422)
    payload = strict_json((Path(directory) / "plotting.json").read_bytes())
    members = [
        {"kind": "fill", "value": row}
        for row in payload["tradingFacts"]["fills"]
        if start <= row["bar_index"] < end
    ]
    members += [
        {"kind": "signal", "value": row}
        for row in payload["markers"]
        if start <= row["anchorBar"] < end
    ]
    return {
        "rows": members[offset : offset + limit],
        "total": len(members),
        "offset": offset,
        "limit": limit,
    }


def curve(directory, limit=5000):
    if not 6 <= limit <= 20000:
        raise WorkspaceError("InvalidRange", "Curve budget must be between 6 and 20000", 422)
    payload = portfolio(directory)
    grouped = {}
    peak = None
    points = []
    for observation in payload["series"]["close"]:
        grouped.setdefault(observation["barIndex"], []).append(observation)
    for bar, observations in grouped.items():
        # Terminal replaces only the rendered point; both observations remain available.
        observation = observations[-1]
        equity = observation["equity"]
        peak = equity if peak is None else max(peak, equity)
        points.append(
            {
                "bar": bar,
                "time": observation["timestamp"],
                "equity": equity,
                "drawdown": (equity / peak - 1) if peak else None,
                "observations": observations,
            }
        )
    count = len(points)
    if count > limit:
        import math

        size = math.ceil(count / max(1, limit // 6))
        sampled = []
        for start in range(0, count, size):
            chunk = points[start : start + size]
            indices = sorted(
                {
                    0,
                    len(chunk) - 1,
                    min(range(len(chunk)), key=lambda i: chunk[i]["equity"]),
                    max(range(len(chunk)), key=lambda i: chunk[i]["equity"]),
                    min(range(len(chunk)), key=lambda i: chunk[i]["drawdown"] or 0),
                    max(range(len(chunk)), key=lambda i: chunk[i]["drawdown"] or 0),
                }
            )
            sampled.extend(chunk[index] for index in indices)
        points = sampled
    return {
        "points": points,
        "total": count,
        "aggregated": count > limit,
        "method": "Close-sampled view; terminal shown last. Authoritative drawdown uses the report metric.",
        "unorderedBounds": [],
        "unorderedCount": sum(not row.get("ordered", True) for row in payload["series"]["account"]),
    }
