"""读取日志的时间、bar 与源码行；比较成功、失败、重跑和宿主入口。

GOOG 前四根日线，无网络和额外依赖。作者不下单，费用不参与。
本教程显式加载可信本地作者文件，不提供沙箱或控制台实现。
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
        assert str(error) == "演示显式失败"
    else:
        raise AssertionError("失败示例必须抛出异常")
    failed = bt.get_logs()
    assert failed[-1]["message"] == "结束原因：error"
    bt.run()
    assert len(bt.get_logs()) == len(success) and bt.get_logs()[0]["sequence"] == 1

    # runtime 隐藏内部 bt：用调用方持有的会话在异常后读取。
    data.index = data.index.tz_localize("UTC")
    schema = runtime.describe(namespace)
    request = {key: schema[key] for key in ("schemaVersion", "schemaHash")} | {
        "values": {"演示失败": True}
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
        assert str(error) == "演示显式失败"
    else:
        raise AssertionError("宿主失败示例必须抛出异常")
    hosted = session.get_logs()
    assert hosted[-1]["message"] == "结束原因：error"
    assert hosted[1]["bar_index"] == 0 and hosted[1]["bar_time"].endswith("+00:00")
    return {"success": success, "failed": failed, "hosted": hosted}


if __name__ == "__main__":
    main()
