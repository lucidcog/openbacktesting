"""宿主从可信作者命名空间运行并导出严格 JSON；不渲染、不写文件。"""

import json
import runpy
from pathlib import Path

from openbacktesting import runtime
from openbacktesting.plotting import export_result


def main(path=None):
    if path is None:
        path = Path(__file__).resolve().parents[1] / "strategies/plotting.py"
    namespace = runpy.run_path(str(path))  # 只加载已信任的源码，不是沙箱。
    runtime.describe(namespace)
    chart = runpy.run_path(str(Path(__file__).with_name("run_author.py")))["chart_for"](path)
    schema = runtime.describe(namespace)
    native = runtime.run(
        namespace,
        {key: schema[key] for key in ("schemaVersion", "schemaHash")}
        | {"values": {"上涨颜色": "#22AA44FF"}},
        **chart,
    )
    snapshot = native.attrs["input_snapshot"]
    assert snapshot["values"]["上涨颜色"] == "#22AA44FF"
    # 标题入口只传字符串；重放配置仍得到相同 Color 与绘图结果。
    request = {key: snapshot[key] for key in ("schemaVersion", "schemaHash", "values")}
    result = runtime.run(namespace, request, **chart)
    assert export_result(result) == export_result(native)
    json.dumps(result.attrs["input_snapshot"], ensure_ascii=False, allow_nan=False)
    result.pop("_strategy")  # 导出依赖冻结快照，不需要策略实例。
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
