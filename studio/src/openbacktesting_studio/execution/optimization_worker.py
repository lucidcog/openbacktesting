"""Frozen-data optimization planning and execution in the selected Python interpreter."""

import json
import sys
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path

from openbacktesting_studio.execution.worker import load_module, write_response


def execute(payload, directory):
    from openbacktesting import Backtest, DataContext, Timeframe, runtime
    from openbacktesting.broker import InstrumentSpec
    from openbacktesting.data.timeframe import TimeframeUnit
    from openbacktesting.optimizer import ExecutionIdentity, Range, Values, open_result, plan
    from openbacktesting.optimizer.identity import execution_identity
    from openbacktesting.strategy.declaration import declaration

    from openbacktesting_studio.execution.data import load_data, read_snapshot, write_snapshot
    from openbacktesting_studio.protocol import OptimizationRequest

    request = OptimizationRequest.model_validate(payload["request"])
    run, snapshot = request.run, payload["snapshot"]
    for name, expected in snapshot["files"].items():
        if sha256((Path(snapshot["directory"]) / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Frozen strategy source changed; prepare a new experiment")
    namespace = vars(load_module(snapshot))
    description = runtime.describe(namespace)
    if (run.inputs.schemaVersion, run.inputs.schemaHash) != (
        description["schemaVersion"],
        description["schemaHash"],
    ):
        raise ValueError("Input schema changed; rediscover before optimizing")
    if payload["operation"] == "plan":
        data, context, instrument = load_data(run.data, snapshot)
        write_snapshot(data, directory / "data")
    else:
        data = read_snapshot(directory / "data")
        context = DataContext(
            Timeframe(TimeframeUnit(run.data.timeframe.unit), run.data.timeframe.multiplier),
            run.data.timezone,
        )
        instrument = InstrumentSpec(**run.data.instrument.model_dump())
    strategy = runtime.discover(namespace)
    resolved = declaration(strategy).resolve(run.settings)
    identity = ExecutionIdentity(snapshot["files"][snapshot["entry"]], snapshot["hash"])
    execution = execution_identity(
        data,
        identity,
        {
            "schemaVersion": 2,
            "settings": resolved.snapshot(),
            "context": context.snapshot(),
            "instrument": asdict(instrument),
            "engineVersion": version("openbacktesting"),
        },
    )
    constraint = namespace.get(request.constraint) if request.constraint else None
    if request.constraint and not callable(constraint):
        raise ValueError("Constraint must name a callable in the strategy module")
    constraint_id = (
        sha256((snapshot["hash"] + ":" + request.constraint).encode()).hexdigest()
        if constraint
        else None
    )
    search = {
        title: Values(domain.values)
        if domain.kind == "values"
        else Range(domain.start, domain.stop, domain.step)
        for title, domain in request.search.items()
    }
    prepared = plan(
        strategy,
        search,
        base_inputs=run.inputs.model_dump(),
        execution=execution,
        constraint_id=constraint_id,
    )
    # Validate market/configuration before offering Start; this does not execute init/next.
    Backtest(
        data, strategy, context=context, instrument=instrument, **resolved.kwargs(), plotting=False
    )
    if payload["operation"] == "plan":
        write_response(directory / "plan.json", prepared.snapshot())
        return {"ok": True, "status": "planned"}
    frozen = json.loads((directory / "plan.json").read_text())
    if frozen != prepared.snapshot():
        raise ValueError("Frozen execution identity changed; create a new experiment")
    path = directory / "experiment.sqlite"
    kwargs = {
        "path": path,
        "identity": identity,
        "data": data,
        "context": context,
        "instrument": instrument,
        "request": run.inputs.model_dump(),
        "settings": run.settings,
        "constraint": constraint,
        "constraint_id": constraint_id,
        "cancel": lambda: (directory / "cancel").exists(),
        "on_progress": lambda value: write_response(directory / "progress.json", value),
    }
    if path.exists():
        result = runtime.resume_optimization(
            namespace, experiment_id=open_result(path).experiment_id, **kwargs
        )
    else:
        result = runtime.optimize(namespace, search, **kwargs)
    return {"ok": True, "status": result.info()["status"], "experimentId": result.experiment_id}


def main():
    request, response = map(Path, sys.argv[1:3])
    try:
        value = execute(json.loads(request.read_text()), response.parent)
    except BaseException as error:  # noqa: BLE001 - user code can raise SystemExit
        value = {"ok": False, "message": str(error), "errorType": type(error).__name__}
    write_response(response, value)
    if not value["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
