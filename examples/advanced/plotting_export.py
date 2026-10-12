"""The host runs a trusted author namespace and exports strict JSON; no rendering or file writes."""

import json
import runpy
from pathlib import Path

from openbacktesting import runtime
from openbacktesting.plotting import export_result


def main(path=None):
    if path is None:
        path = Path(__file__).resolve().parents[1] / "strategies/plotting.py"
    namespace = runpy.run_path(str(path))  # Load trusted source only; this is not a sandbox.
    runtime.describe(namespace)
    chart = runpy.run_path(str(Path(__file__).with_name("run_author.py")))["chart_for"](path)
    schema = runtime.describe(namespace)
    native = runtime.run(
        namespace,
        {key: schema[key] for key in ("schemaVersion", "schemaHash")}
        | {"values": {"Rising color": "#22AA44FF"}},
        **chart,
    )
    snapshot = native.attrs["input_snapshot"]
    assert snapshot["values"]["Rising color"] == "#22AA44FF"
    # The title entry point accepts strings only; configuration replay produces the same Color and plotting results.
    request = {key: snapshot[key] for key in ("schemaVersion", "schemaHash", "values")}
    result = runtime.run(namespace, request, **chart)
    assert export_result(result) == export_result(native)
    json.dumps(result.attrs["input_snapshot"], ensure_ascii=False, allow_nan=False)
    result.pop("_strategy")  # Export uses a frozen snapshot and does not require a strategy instance.
    print(result[["Return [%]", "# Trades"]])
    payload = export_result(result)
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    print(
        f"PlottingResult: {len(encoded.encode())} bytes, {len(payload['plots'])} plots, "
        f"{len(payload['colorEvents'])} color events"
    )
    return payload


if __name__ == "__main__":
    main()
