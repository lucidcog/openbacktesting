"""Private worker entrypoint; stdout is user output, response files are structured IPC."""

from __future__ import annotations

import json
import os
import platform
import sys
import traceback
from importlib import import_module
from importlib.metadata import version
from pathlib import Path


def load_module(snapshot, entry=None):
    directory = Path(snapshot["directory"]).resolve(strict=True)
    sys.dont_write_bytecode = True
    os.chdir(directory)
    roots = [(directory / root).resolve(strict=True) for root in snapshot["roots"]]
    if any(not root.is_relative_to(directory) for root in roots):
        raise ValueError("Snapshot source root escapes its directory")
    sys.path[:0] = [str(root) for root in roots]
    path = directory / (entry or snapshot["entry"])
    root = next(
        (
            root
            for root in sorted(roots, key=lambda p: len(p.parts), reverse=True)
            if path.is_relative_to(root)
        ),
        None,
    )
    if root is None:
        raise ValueError("Strategy must be inside a configured source root")
    parts = list(path.relative_to(root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    if not parts or any(not part.isidentifier() for part in parts):
        raise ValueError("Strategy path must identify an importable Python module")
    module = import_module(".".join(parts))
    if Path(module.__file__).resolve() != path.resolve():
        raise ValueError("Module name collided with a different imported module")
    return module


def write_response(path, payload):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, allow_nan=False))
    os.replace(temporary, path)


def collected_logs(logs, limit=1048576, snapshot=None):
    if logs is None:
        return {"records": [], "truncated": False}
    records = logs.get_logs()
    if snapshot is not None:
        root = Path(snapshot["directory"])
        for record in records:
            source = Path(record["source_file"]) if record.get("source_file") else None
            if source is not None and source.is_relative_to(root):
                name = source.relative_to(root).as_posix()
                if name in snapshot["files"]:
                    record["source"] = {
                        "workspacePath": name,
                        "line": record["source_line"],
                        "sourceRevision": snapshot["files"][name],
                    }
    selected = []
    size = 0
    for record in reversed(records):
        encoded = json.dumps(record).encode()
        if size + len(encoded) > limit:
            break
        selected.append(record)
        size += len(encoded)
    return {"records": list(reversed(selected)), "truncated": len(selected) != len(records)}


def main():
    if sys.argv[1:] == ["--probe"]:
        print(
            json.dumps(
                {
                    "protocolVersion": 1,
                    "pythonVersion": platform.python_version(),
                    "studioVersion": version("openbacktesting-studio"),
                    "coreVersion": version("openbacktesting"),
                }
            )
        )
        return
    request, response = (Path(value).resolve() for value in sys.argv[1:3])
    payload = json.loads(request.read_text())
    phase = "importing"
    logs = None
    try:
        from openbacktesting import RunLogs, plotting, portfolio, runtime

        if payload["operation"] == "describe":
            namespace = vars(load_module(payload["snapshot"]))
            write_response(response, {"ok": True, "description": runtime.describe(namespace)})
        elif payload["operation"] == "run":
            from openbacktesting_studio.execution.data import load_data, write_snapshot
            from openbacktesting_studio.protocol import RunRequest

            run = RunRequest.model_validate(payload["request"])
            output = response.parent / "artifacts"
            output.mkdir(exist_ok=False)

            def stage(name):
                nonlocal phase
                phase = name
                write_response(response.parent / "phase.json", {"phase": phase})

            stage("loading")
            if payload.get("dataSnapshot"):
                from openbacktesting import DataContext, Timeframe
                from openbacktesting.broker import InstrumentSpec
                from openbacktesting.data.timeframe import TimeframeUnit

                from openbacktesting_studio.execution.data import read_snapshot

                frame = read_snapshot(payload["dataSnapshot"])
                context = DataContext(
                    Timeframe(
                        TimeframeUnit(run.data.timeframe.unit), run.data.timeframe.multiplier
                    ),
                    run.data.timezone,
                )
                instrument = InstrumentSpec(**run.data.instrument.model_dump())
            else:
                frame, context, instrument = load_data(run.data, payload["snapshot"])
            identity = write_snapshot(frame, output / "data")
            stage("validating")
            namespace = vars(load_module(payload["snapshot"]))
            description = runtime.describe(namespace)
            if description["schemaHash"] != run.inputs.schemaHash:
                raise ValueError("Input schema changed before execution")
            from openbacktesting.strategy.declaration import declaration
            from openbacktesting.strategy.inputs import resolve_request

            strategy = runtime.discover(namespace)
            if description["inputs"]:
                resolve_request(strategy, run.inputs.model_dump())
            declaration(strategy).resolve(run.settings)
            logs = RunLogs()
            stage("executing")
            if not description["inputs"] and run.inputs.values:
                raise ValueError("This strategy has no input parameters")
            input_request = run.inputs.model_dump() if description["inputs"] else None
            result = runtime.run(
                namespace,
                input_request,
                data=frame,
                context=context,
                instrument=instrument,
                settings=run.settings,
                logs=logs,
            )
            stage("exporting")
            write_response(output / "portfolio.json", portfolio.export_result(result))
            diagnostics = []
            try:
                write_response(output / "plotting.json", plotting.export_result(result))
            except Exception as error:  # noqa: BLE001 - optional export failure preserves the valid report
                diagnostics.append({"artifact": "plotting", "message": str(error)})
            write_response(output / "description.json", description)
            write_response(output / "request.json", payload["request"])
            write_response(output / "logs.json", collected_logs(logs, snapshot=payload["snapshot"]))
            write_response(output / "catalog.json", portfolio.report_catalog())
            stage("persisting")
            write_response(
                response,
                {"ok": True, "dataHash": identity, "diagnostics": diagnostics, "phase": phase},
            )
        else:
            raise ValueError("Unknown worker operation")
    except BaseException as error:  # noqa: BLE001 - user code may raise SystemExit
        frames = [
            {"path": frame.filename, "line": frame.lineno, "name": frame.name}
            for frame in traceback.extract_tb(error.__traceback__)
        ]
        snapshot_root = Path(payload["snapshot"]["directory"])
        for frame in frames:
            original = Path(frame["path"])
            if original.is_relative_to(snapshot_root):
                name = original.relative_to(snapshot_root).as_posix()
                frame.update(
                    workspacePath=name,
                    sourceRevision=payload["snapshot"]["files"].get(name),
                    snapshot=True,
                )
        if isinstance(error, SyntaxError):
            frame = {"path": error.filename, "line": error.lineno, "name": "<syntax>"}
            if error.filename and Path(error.filename).is_relative_to(snapshot_root):
                name = Path(error.filename).relative_to(snapshot_root).as_posix()
                frame.update(
                    workspacePath=name,
                    sourceRevision=payload["snapshot"]["files"].get(name),
                    snapshot=True,
                )
            frames.append(frame)
        write_response(
            response,
            {
                "ok": False,
                "message": str(error),
                "errorType": type(error).__name__,
                "code": getattr(error, "code", type(error).__name__),
                "fieldErrors": {error.title: [error.expected]}
                if getattr(error, "title", None) is not None
                else {},
                "frames": frames,
                "phase": phase,
                "logs": collected_logs(logs, snapshot=payload["snapshot"]),
            },
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
