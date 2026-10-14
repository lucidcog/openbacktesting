"""Record one local conversion and HTTP sample; this is not a capacity benchmark."""

import gzip
import json
import platform
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from openbacktesting_studio.artifacts import write_manifest
from openbacktesting_studio.host import create_app
from openbacktesting_studio.host.projection import project

ROOT = Path(__file__).resolve().parents[1]
raw = json.loads((ROOT / "tests/fixtures/plotting.json").read_text())
count = 50000
raw["axes"][0]["labels"] = [
    str(1700000000000000000 + index * 60000000000) for index in range(count)
]
raw["sources"] = []
raw["plots"] = []
raw["fills"] = []
raw["markers"] = []
raw["colorEvents"] = []
raw["tradingFacts"] = {"fills": []}
raw["execution"] = {key: [True] * count for key in ["processed", "strategyNext"]}
for key in ["open", "high", "low", "close", "volume"]:
    values = [100.0 + index % 100 for index in range(count)]
    raw["market"][key] = {
        "values": values,
        "valid": [True] * count,
        "ready": [True] * count,
        "missing": [None] * count,
    }
started = time.perf_counter()
result = project(raw, 0, count, 5000)
elapsed = time.perf_counter() - started
encoded = json.dumps(result).encode()
with TemporaryDirectory() as temporary:
    directory = Path(temporary)
    (directory / "portfolio.json").write_bytes(
        (ROOT / "tests/fixtures/portfolio.json").read_bytes()
    )
    (directory / "plotting.json").write_bytes((ROOT / "tests/fixtures/plotting.json").read_bytes())
    write_manifest(directory, run_id="sample", provenance={})
    token = "measurement-token-1234567890"
    origin = "http://127.0.0.1:41000"
    with TestClient(
        create_app(None, origin=origin, readonly=True, viewer=directory, token=token),
        base_url=origin,
    ) as client:
        client.post("/api/v1/session", json={"token": token}, headers={"origin": origin})
        client.headers["x-studio-protocol"] = "1"
        began = time.perf_counter()
        response = client.get("/api/v1/runs/sample/summary")
        http_elapsed = time.perf_counter() - began
        assert response.status_code == 200
web = ROOT / "src/openbacktesting_studio/web"
assets = list((web / "assets").iterdir())
entry = [path for path in assets if path.name.startswith("index-")]
print(
    json.dumps(
        {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
            "projection": {
                "syntheticBars": count,
                "indicatorSources": 0,
                "limit": 5000,
                "returnedPoints": result["window"]["points"],
                "granularity": result["window"]["granularity"],
                "seconds": elapsed,
                "jsonBytes": len(encoded),
            },
            "summaryHttp": {
                "fixtureBars": 120,
                "seconds": http_elapsed,
                "responseBytes": len(response.content),
            },
            "static": {
                "totalBytes": sum(path.stat().st_size for path in web.rglob("*") if path.is_file()),
                "entryJsCssBytes": sum(path.stat().st_size for path in entry),
                "entryJsCssGzipBytes": sum(len(gzip.compress(path.read_bytes())) for path in entry),
                "editorLazyBytes": sum(
                    path.stat().st_size for path in assets if path.name.startswith("CodeEditor-")
                ),
            },
        },
        indent=2,
    )
)
