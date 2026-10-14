"""Exercise real wheel/sdist installations outside the checkout, without Node or outbound runtime sockets."""

import argparse
import http.cookiejar
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_CHECK = """
import importlib.resources as resources
import importlib.util
import json
from pathlib import Path
from openbacktesting import Strategy, Backtest, DataContext, Timeframe, portfolio
from openbacktesting.data.timeframe import TimeframeUnit
from openbacktesting.broker import InstrumentSpec
from openbacktesting.test import GOOG
class Example(Strategy):
    def init(self): pass
    def next(self):
        if self.bar_index == 0: self.buy(qty=1)
data = GOOG.iloc[:12].copy()
data.index = data.index.tz_localize('UTC')
result = Backtest(data, Example, context=DataContext(Timeframe(TimeframeUnit.DAY, 1), 'UTC'), instrument=InstrumentSpec(symbol='GOOG')).run()
Path('portfolio.json').write_text(json.dumps(portfolio.export_result(result), allow_nan=False))
assert resources.files('openbacktesting').joinpath('optimizer/portfolio-result.schema.json').is_file()
assert importlib.util.find_spec('openbacktesting_studio') is None
print('Core-only backtest and packaged resource passed')
"""
GUARD = """
import socket
import webbrowser
_original = socket.socket.connect
def guarded(self, address):
    if isinstance(address, tuple) and address[0] not in {'127.0.0.1', '::1', 'localhost'}:
        raise RuntimeError('Outbound runtime connection forbidden by installation test')
    return _original(self, address)
socket.socket.connect = guarded
def no_browser(*args, **kwargs):
    raise RuntimeError('Browser opening forbidden in --no-open test')
webbrowser.open = no_browser
"""


def run(command, cwd, **kwargs):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False, **kwargs)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def serve(python, arguments, directory, guard):
    environment = os.environ | {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(guard)}
    assert shutil.which("node", path=environment["PATH"]) is None
    process = subprocess.Popen(
        [str(python), "-m", "openbacktesting_studio.cli", *arguments, "--no-open", "--port", "0"],
        cwd=directory,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        first = process.stdout.readline()
        match = re.search(r"(http://127\.0\.0\.1:\d+)/#token=(\S+)", first)
        if not match:
            raise RuntimeError(first + process.stderr.read())
        origin, token = match.groups()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )

        def request(path, payload=None, method=None):
            headers = {
                "Origin": origin,
                "X-Studio-Protocol": "1",
                "Content-Type": "application/json",
            }
            if csrf[0]:
                headers["X-Studio-CSRF"] = csrf[0]
            req = urllib.request.Request(
                origin + path,
                data=json.dumps(payload).encode() if payload is not None else None,
                headers=headers,
                method=method,
            )
            with opener.open(req, timeout=30) as response:
                return response.read(), response.headers

        csrf = [""]
        for attempt in range(100):
            try:
                session, _ = request("/api/v1/session", {"token": token})
                csrf[0] = json.loads(session)["csrf"]
                break
            except (ConnectionError, urllib.error.URLError):
                if process.poll() is not None:
                    raise RuntimeError(process.stderr.read())
                time.sleep(0.05)
        else:
            raise RuntimeError("Host did not become ready")
        page, headers = request("/")
        assert (
            b"assets/" in page and "worker-src 'self' blob:" in headers["content-security-policy"]
        )
        for asset in re.findall(r'(?:src|href)="(/assets/[^\"]+)"', page.decode()):
            body, _ = request(asset)
            assert body
        metadata, _ = request("/build-manifest.json")
        assets = json.loads(metadata)["assets"]
        worker = next(name for name in assets if "editor.worker-" in name)
        assert request("/" + worker)[0]
        provenance, _ = request("/chart-provenance.json")
        assert json.loads(provenance)["tag"] == "v5.2.1"
        assert request("/third-party-notices.txt")[0]
        capabilities = json.loads(request("/api/v1/capabilities")[0])
        if capabilities["mode"] == "workspace":
            assert capabilities["interpreter"]["compatible"]
            assert capabilities["workspace"] is None
            request("/api/v1/workspace", {"path": str(directory)}, method="PUT")
            source = json.loads(request("/api/v1/file?path=strategy.py")[0])
            descriptor = {"path": "strategy.py", "revision": source["revision"]}
            description = json.loads(request("/api/v1/discover", descriptor)[0])["description"]
            payload = {
                "source": descriptor,
                "inputs": {key: description[key] for key in ["schemaVersion", "schemaHash"]}
                | {"values": {}},
                "data": {
                    "kind": "sample",
                    "name": "GOOG",
                    "sample": "GOOG",
                    "timezone": "UTC",
                    "timeframe": {"unit": "day", "multiplier": 1},
                    "instrument": {"symbol": "GOOG"},
                },
                "idempotencyKey": "installed",
            }
            record = json.loads(request("/api/v1/runs", payload)[0])
            for _ in range(200):
                record = json.loads(request("/api/v1/runs/" + record["id"])[0])
                if record["status"] in {"succeeded", "failed"}:
                    break
                time.sleep(0.05)
            assert record["status"] == "succeeded", record
            experiment = json.loads(
                request(
                    "/api/v1/optimizations",
                    {"run": payload, "search": {"Length": {"kind": "values", "values": [1, 2]}}},
                )[0]
            )
            prefix = "/api/v1/optimizations/" + experiment["id"]
            for _ in range(200):
                experiment = json.loads(request(prefix)[0])
                if experiment["status"] != "planning":
                    break
                time.sleep(0.05)
            assert experiment["status"] == "planned", experiment
            request(prefix + "/start", {}, method="POST")
            for _ in range(200):
                experiment = json.loads(request(prefix)[0])
                if experiment["status"] != "running":
                    break
                time.sleep(0.05)
            assert experiment["status"] == "completed", experiment
            assert experiment["info"]["committed"] == 2
            assert len(json.loads(request(prefix + "/query", {})[0])["rows"]) == 2
            assert request(prefix + "/export")[0].startswith(b"SQLite format 3")
        else:
            record = json.loads(request("/api/v1/runs")[0])["runs"][0]
            assert not capabilities["capabilities"]["edit"]
        assert json.loads(request("/api/v1/runs/" + record["id"] + "/summary")[0])["summary"]
        archive = directory / "shared.obstudio"
        archive.write_bytes(request("/api/v1/runs/" + record["id"] + "/export")[0])
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            assert not any(
                name.startswith(("source/", "data/"))
                or name in {"logs.json", "stdout.json", "stderr.json"}
                for name in names
            )
            assert token.encode() not in b"".join(bundle.read(name) for name in names)
    finally:
        process.terminate()
        try:
            process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise
        assert process.returncode in {0, -15}, process.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", default="3.13")
    args = parser.parse_args()
    uv = shutil.which("uv")
    with tempfile.TemporaryDirectory(prefix="studio-install-") as temporary:
        root = Path(temporary)
        guard = root / "guard"
        guard.mkdir()
        (guard / "sitecustomize.py").write_text(GUARD)
        for kind, extension in [("wheel", "*.whl"), ("sdist", "*.tar.gz")]:
            directory = root / kind
            directory.mkdir()
            environment = directory / "environment"
            run([uv, "venv", "--python", args.python, str(environment)], directory)
            python = environment / "bin/python"
            core = next((ROOT / "dist").glob(extension))
            studio = next((ROOT / "studio/dist").glob(extension))
            run(
                [uv, "pip", "install", "--python", str(python), str(core)],
                directory,
                env=os.environ | {"PATH": "/usr/bin:/bin"},
            )
            print(kind + ": " + run([str(python), "-c", CORE_CHECK], directory).strip())
            run(
                [uv, "pip", "install", "--python", str(python), str(studio)],
                directory,
                env=os.environ | {"PATH": "/usr/bin:/bin"},
            )
            serve(python, ["view", str(directory / "portfolio.json")], directory, guard)
            (directory / "strategy.py").write_text(
                'from openbacktesting import Strategy, backtest, inputs\n@backtest()\nclass Example(Strategy):\n    length = inputs.int(1, title="Length")\n    def init(self): pass\n    def next(self): pass\n'
            )
            serve(python, [str(directory)], directory, guard)
            print(
                kind
                + ": installed workspace, worker, optimizer, offline viewer, local assets and private export defaults passed"
            )


if __name__ == "__main__":
    main()
