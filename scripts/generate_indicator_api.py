"""从审核目录生成方法签名与具名结果；--check 检查发布物漂移。"""

import argparse
import json
import keyword
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src/openbacktesting/indicators"
RESULT_RESERVED = {"ready", "valid", "metadata", "df"}
PARAM_RESERVED = {"self", "source", "inputs", "backend", "required_outputs"}


def checked_name(name, reserved):
    if (
        not name.isidentifier()
        or keyword.iskeyword(name)
        or name.startswith("_")
        or name in reserved
    ):
        raise ValueError(f"公开名称冲突或非法: {name}")
    return name


def render(entries):
    rows = sorted((row for row in entries if row["status"] == "available"), key=lambda r: r["id"])
    lines = [
        '"""由 scripts/generate_indicator_api.py 生成；请修改审核目录后重新生成。"""',
        "from __future__ import annotations",
        "",
        "from collections.abc import Sequence",
        "",
        "from .api import IndicatorNamespace, IndicatorResult, Inputs, Source",
        "from .types import IndicatorHandle",
    ]
    names = set()
    for row in rows:
        name = checked_name(row["id"].removeprefix("ta."), names)
        names.add(name)
        for param in row["parameters"]:
            checked_name(param, PARAM_RESERVED)
        if len(row["outputs"]) > 1:
            outputs = {name: name for name in row["outputs"]}
            for alias, target in row.get("aliases", {}).items():
                if alias in outputs or target not in outputs:
                    raise ValueError(f"输出别名冲突: {row['id']} {alias}")
                outputs[alias] = target
            lines += [
                f"class {name.title().replace('_', '')}Result(IndicatorResult):",
                "    __slots__ = ()",
            ]
            for attribute, channel in outputs.items():
                checked_name(attribute, RESULT_RESERVED)
                lines += [
                    "    @property",
                    f"    def {attribute}(self) -> IndicatorHandle:",
                    f"        return self._channels[{channel!r}]",
                ]
    lines += [
        "class TechnicalAnalysis(IndicatorNamespace):",
        '    """当前策略的技术分析入口；序列指标在 init() 登记，is_* 即时判断可在 next() 调用。"""',
    ]
    for row in rows:
        name = row["id"].removeprefix("ta.")
        single = len(row["inputs"]) == 1
        input_args = row.get("input_args", [])
        for argument in input_args:
            checked_name(
                argument, {"self", "inputs", "backend", "required_outputs"} | set(row["parameters"])
            )
        result = (
            f"{name.title().replace('_', '')}Result"
            if len(row["outputs"]) > 1
            else "IndicatorHandle"
        )
        parameters = row["parameters"]
        lines += [f"    def {name}(", "        self,"]
        if input_args:
            lines += [f"        {argument}: Source | None = None," for argument in input_args]
        elif single:
            lines += ["        source: Source | None = None,"]
        lines += ["        *,"]
        for key, rule in parameters.items():
            lines += [f"        {key}: {rule['kind']} = {rule['default']!r},"]
        lines += [
            "        inputs: Inputs | None = None,",
            "        backend: str | None = None,",
            "        required_outputs: Sequence[str] | None = None,",
            f"    ) -> {result}:",
            f'        """{row["id"]}；输入：{", ".join(row["inputs"])}；输出：{", ".join(row["outputs"])}。参数按审核目录校验。"""',
        ]
        primary = repr(row["inputs"][0]) if single else repr("")
        source = "source" if single else "None"
        mapping = "{" + ", ".join(f"{p!r}: {p}" for p in parameters) + "}"
        call = f"self._call({row['id']!r}, {primary}, {source}, inputs, backend, required_outputs, {mapping})"
        if input_args:
            sources = "{" + ", ".join(f"{arg!r}: {arg}" for arg in input_args) + "}"
            call = f"self._call_inputs({row['id']!r}, {sources}, inputs, backend, required_outputs, {mapping})"
        lines += [
            f"        return {call}"
            if result == "IndicatorHandle"
            else f"        return {result}({call})"
        ]
    raw = "\n\n".join(lines[:1]) + "\n" + "\n".join(lines[1:]) + "\n"
    return subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "ruff",
            "format",
            "--stdin-filename",
            "methods.py",
            "-",
        ],
        input=raw,
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    ).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=PACKAGE / "methods.py")
    args = parser.parse_args()
    expected = render(json.loads((PACKAGE / "catalog.json").read_text())["entries"])
    if args.check:
        if not args.output.exists() or args.output.read_text() != expected:
            raise SystemExit(
                "指标接口生成物过期：运行 uv run --locked python scripts/generate_indicator_api.py"
            )
        print("指标方法生成物一致")
    else:
        args.output.write_text(expected)


if __name__ == "__main__":
    main()
