"""Read log times, bars, and source lines; compare success, failure, reruns, and the host entry point.

The first four GOOG daily bars, with no network or extra dependencies. The author submits no orders, so fees do not apply.
This tutorial explicitly loads trusted local author source; it provides neither a sandbox nor a console implementation.
"""

import json
import runpy
from pathlib import Path

from openbacktesting import Backtest, DataContext, RunLogs, Timeframe, runtime
from openbacktesting.broker import InstrumentSpec
from openbacktesting.test import GOOG


def main():
    path = Path(__file__).resolve().parents[1] / "strategies" / "strategy_logs.py"
    namespace = runpy.run_path(str(path))
    cls = runtime.discover(namespace)
    data = GOOG.iloc[:4].copy()
    bt = Backtest(data, cls, plotting=False)
    result = bt.run()
    print(result[["Return [%]", "# Trades"]])
    success = bt.get_logs()
    assert success == result.attrs["strategy_logs"]
    assert any(row["level"] == "error" for row in success)
    assert len([row for row in success if row["phase"] == "next" and row["level"] == "info"]) == 4
    for row in success:
        print(
            json.dumps(
                {
                    key: row[key]
                    for key in (
                        "recorded_at",
                        "bar_time",
                        "bar_index",
                        "source_file",
                        "source_line",
                        "message",
                    )
                },
                ensure_ascii=False,
            )
        )
    try:
        bt.run(fail=True)
    except ValueError as error:
        assert str(error) == "Demonstrate explicit failure"
    else:
        raise AssertionError("The failure example must raise an exception")
    failed = bt.get_logs()
    assert failed[-1]["message"] == "End reason: error"
    bt.run()
    assert len(bt.get_logs()) == len(success) and bt.get_logs()[0]["sequence"] == 1

    # runtime hides its internal bt; read logs after failure through the caller-owned session.
    data.index = data.index.tz_localize("UTC")
    schema = runtime.describe(namespace)
    request = {key: schema[key] for key in ("schemaVersion", "schemaHash")} | {
        "values": {"Demonstrate failure": True}
    }
    session = RunLogs()
    try:
        runtime.run(
            namespace,
            request,
            data=data,
            context=DataContext(Timeframe.days(1), "UTC"),
            instrument=InstrumentSpec(symbol="GOOG"),
            logs=session,
        )
    except ValueError as error:
        assert str(error) == "Demonstrate explicit failure"
    else:
        raise AssertionError("The host failure example must raise an exception")
    hosted = session.get_logs()
    assert hosted[-1]["message"] == "End reason: error"
    assert hosted[1]["bar_index"] == 0 and hosted[1]["bar_time"].endswith("+00:00")
    return {"success": success, "failed": failed, "hosted": hosted}


if __name__ == "__main__":
    main()
