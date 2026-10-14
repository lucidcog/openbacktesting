"""Display-only projections retain original bar identities and semantic boundaries."""

import math

from openbacktesting_studio.workspace import WorkspaceError


def present(source, index):
    value = source["values"][index]
    return (
        source["valid"][index]
        and source["ready"][index]
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def project(payload, start, end, limit):
    """Bound a projection; decline pathological detail rather than erase its gaps."""
    axis = next(axis for axis in payload["axes"] if axis["id"] == payload["market"]["axis"])
    total = len(axis["labels"])
    sources = payload["sources"]
    factor = 4 * max(1, len(sources)) + 2
    width = 1 if end - start <= limit else math.ceil((end - start) / max(1, limit // factor))
    buckets = [(left, min(end, left + width)) for left in range(start, end, width)]
    selected = (
        set(range(start, end))
        if width == 1
        else {index for left, right in buckets for index in (left, right - 1)}
    )
    if width > 1:
        for source in sources:
            for left, right in buckets:
                valid = [index for index in range(left, right) if present(source, index)]
                if valid:
                    selected.update(
                        (
                            valid[0],
                            valid[-1],
                            min(valid, key=lambda index: source["values"][index]),
                            max(valid, key=lambda index: source["values"][index]),
                        )
                    )
            # Both sides of every mask transition and every missing region survive.
            for index in range(start + 1, end):
                if present(source, index) != present(source, index - 1):
                    selected.update((index - 1, index))
        plots = {plot["id"]: plot for plot in payload["plots"]}
        sources_by_id = {source["id"]: source for source in sources}
        for fill in payload["fills"]:
            lower, upper = plots[fill["lower"]], plots[fill["upper"]]

            def value(plot, index):
                if plot["kind"] == "level":
                    return plot["value"]
                source = sources_by_id[plot["source"]]
                original = index - plot["offsetBars"]
                return (
                    source["values"][original]
                    if 0 <= original < total and present(source, original)
                    else None
                )

            previous = None
            for index in range(start, end):
                a, b = value(lower, index), value(upper, index)
                delta = a - b if a is not None and b is not None else None
                if previous is not None and delta is not None and previous * delta <= 0:
                    selected.update((max(start, index - 1), index))
                previous = delta
        if len(selected) > limit:
            raise WorkspaceError(
                "ChartDetailBudget",
                "This range contains too many gap or crossing boundaries. Choose a narrower range.",
                422,
                requiredPoints=len(selected),
                budget=limit,
            )
    indices = sorted(selected)
    if len(indices) * (len(sources) + 5) > 1000000:
        raise WorkspaceError(
            "ChartDetailBudget",
            "Projected series exceed the value budget; choose a smaller window",
            422,
        )
    result = payload | {
        "axes": [dict(item) for item in payload["axes"]],
        "sources": [dict(item) for item in payload["sources"]],
        "plots": [dict(item) for item in payload["plots"]],
        "market": {
            key: dict(value) if isinstance(value, dict) else value
            for key, value in payload["market"].items()
        },
        "tradingFacts": dict(payload["tradingFacts"]),
        "execution": dict(payload["execution"]),
    }
    for item in result["axes"]:
        item["labels"] = [item["labels"][index] for index in indices]
        item["origin"] = start
        item["indices"] = indices
    by_id = {source["id"]: source for source in payload["sources"]}
    for plot in result["plots"]:
        offset = plot.get("offsetBars", 0)
        if offset > 20000:
            raise WorkspaceError(
                "ChartDetailBudget", "Future offset exceeds the 20000-slot display budget", 422
            )
        if plot["kind"] != "level" and offset:
            source = by_id[plot["source"]]
            plot["leading"] = [
                {
                    "time": index + offset,
                    "value": source["values"][index],
                    "valid": present(source, index),
                }
                for index in range(max(0, start - offset), min(start, end - offset))
            ]
    for source in result["sources"]:
        for key in ["values", "valid", "ready", "missing"]:
            source[key] = [source[key][index] for index in indices]
    if width == 1:
        for name, source in result["market"].items():
            if name != "axis":
                for key in ["values", "valid", "ready", "missing"]:
                    source[key] = [source[key][index] for index in indices]
    else:
        bucket_by_end = {right - 1: (left, right) for left, right in buckets}
        for name in ["open", "high", "low", "close", "volume"]:
            original = payload["market"][name]
            values = []
            for index in indices:
                bounds = bucket_by_end.get(index)
                if bounds is None:
                    values.append(None)
                    continue
                left, right = bounds
                points = [
                    original["values"][bar] for bar in range(left, right) if present(original, bar)
                ]
                # Incomplete OHLC buckets are whitespace; volume is not fabricated as zero.
                if len(points) != right - left:
                    values.append(None)
                else:
                    values.append(
                        points[0]
                        if name == "open"
                        else points[-1]
                        if name == "close"
                        else max(points)
                        if name == "high"
                        else min(points)
                        if name == "low"
                        else sum(points)
                    )
            result["market"][name] = {
                "values": values,
                "valid": [v is not None for v in values],
                "ready": [v is not None for v in values],
                "missing": [None if v is not None else "display-whitespace" for v in values],
            }
    clusters = []
    if width > 1:
        for left, right in buckets:
            fills = [
                row for row in payload["tradingFacts"]["fills"] if left <= row["bar_index"] < right
            ]
            markers = [row for row in payload["markers"] if left <= row["anchorBar"] < right]
            if fills or markers:
                clusters.append(
                    {
                        "bar": right - 1,
                        "start": left,
                        "end": right,
                        "fillCount": len(fills),
                        "signalCount": len(markers),
                        "kind": "display-cluster",
                    }
                )
    for key in ["markers", "colorEvents"]:
        result[key] = (
            [row for row in result[key] if start <= row["anchorBar"] < end] if width == 1 else []
        )
    if width > 1:
        representatives = {}
        for event in payload["colorEvents"]:
            if start <= event["anchorBar"] < end:
                bucket = min(end, start + ((event["anchorBar"] - start) // width + 1) * width) - 1
                key = (event["kind"], event["pane"], bucket)
                if (
                    key not in representatives
                    or representatives[key]["sequence"] < event["sequence"]
                ):
                    representatives[key] = event | {
                        "anchorBar": bucket,
                        "displayRepresentative": True,
                        "originalAnchorBar": event["anchorBar"],
                    }
        result["colorEvents"] = list(representatives.values())
    for key, rows in result["tradingFacts"].items():
        result["tradingFacts"][key] = (
            [row for row in rows if start <= row["bar_index"] < end] if width == 1 else []
        )
    if (
        sum(len(result[key]) for key in ["markers", "colorEvents"])
        + sum(map(len, result["tradingFacts"].values()))
        > 20000
    ):
        raise WorkspaceError(
            "ChartEventBudget",
            "Too many discrete events in this range. Use an aggregated view or narrower range.",
            422,
        )
    for key in ["processed", "strategyNext"]:
        result["execution"][key] = [result["execution"][key][index] for index in indices]
    result["display"] = {
        "aggregated": width > 1,
        "clusters": clusters,
        "buckets": [{"start": a, "end": b, "bar": b - 1} for a, b in buckets] if width > 1 else [],
    }
    return {
        "plotting": result,
        "window": {
            "start": start,
            "end": end,
            "total": total,
            "granularity": width,
            "points": len(indices),
            "originalBarIndices": indices,
        },
    }
