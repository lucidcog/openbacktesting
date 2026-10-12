"""公开 API 审计、指标文档生成和只读完整性检查。"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import functools
import importlib
import inspect
import json
import re
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/core"
CATALOG = ROOT / "src/openbacktesting/indicators/catalog.json"
GENERATED = "<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->"


def resolve(name):
    parts = name.split(".")
    for count in range(len(parts), 0, -1):
        try:
            obj = importlib.import_module(".".join(parts[:count]))
        except ModuleNotFoundError as error:
            if not (
                ".".join(parts[:count]) == error.name
                or ".".join(parts[:count]).startswith(error.name + ".")
            ):
                raise
            continue
        if count == len(parts) and count > 1:
            parent = importlib.import_module(".".join(parts[:-1]))
            obj = getattr(parent, parts[-1], obj)
        for part in parts[count:]:
            obj = inspect.getattr_static(obj, part) if inspect.isclass(obj) else getattr(obj, part)
        return obj
    raise ValueError(f"无法定位对象：{name}")


def candidates(obj):
    names = vars(obj) if inspect.ismodule(obj) else dir(obj)
    return {name for name in names if not name.startswith("_")}


def doc_object(obj):
    if isinstance(obj, functools.partial):
        return obj.func
    if isinstance(obj, (property, staticmethod, classmethod)):
        return obj.fget if isinstance(obj, property) else obj.__func__
    return obj


def signature(obj):
    if not callable(obj):
        return ""
    # inputs 使用私有 sentinel 表示未提供；输出稳定名称而不是内存地址。
    return re.sub(r"<object object at 0x[0-9a-fA-F]+>", "未提供", str(inspect.signature(obj)))


def source_path(obj):
    obj = doc_object(obj)
    if inspect.isclass(obj):
        # 历史 __module__ 被保留供 pickle 使用，函数代码位置才是真实实现路径。
        for member in vars(obj).values():
            member = doc_object(member)
            if (
                inspect.isfunction(member)
                and Path(member.__code__.co_filename).is_file()
                and Path(member.__code__.co_filename).resolve().is_relative_to(ROOT)
            ):
                return Path(member.__code__.co_filename).resolve().relative_to(ROOT).as_posix()
    try:
        return Path(inspect.getsourcefile(obj)).resolve().relative_to(ROOT).as_posix()
    except (TypeError, ValueError):
        return ""


def check_manifest(manifest, docs=DOCS):
    issues = []
    entries = manifest["objects"]
    for scope in manifest["scopes"]:
        try:
            found = {f"{scope}.{name}" for name in candidates(resolve(scope))}
            known = {name for name in entries if name.rpartition(".")[0] == scope}
            for name in sorted(found - known):
                issues.append(f"公开候选未分类：{name}")
            for name in sorted(known - found):
                issues.append(f"清单对象已不存在：{name}")
        except (ImportError, AttributeError, ValueError) as error:
            issues.append(f"无效范围：{scope}: {error}")
    for name, entry in entries.items():
        if entry["status"] not in {"recommended", "compatibility", "internal"}:
            issues.append(f"非法分类：{name}")
        if not entry.get("reason"):
            issues.append(f"缺少分类依据：{name}")
        try:
            obj = resolve(name)
        except (ImportError, AttributeError, ValueError) as error:
            issues.append(f"无效对象：{name}: {error}")
            continue
        if entry["status"] != "recommended":
            if entry.get("canonical"):
                try:
                    if obj is not resolve(entry["canonical"]):
                        issues.append(f"兼容对象身份失配：{name}")
                except (ImportError, AttributeError, ValueError):
                    issues.append(f"兼容目标失效：{name}")
            continue
        page = docs / entry["page"]
        if not page.is_file() or name not in page.read_text():
            issues.append(f"参考缺失：{name}: {entry['page']}")
        target = doc_object(obj)
        doc = inspect.getdoc(target) or ""
        if callable(target) and not doc:
            issues.append(f"缺少 docstring：{name}")
        if callable(obj):
            params = set(inspect.signature(obj).parameters)
            section = re.search(r"(?:^|\n)Args:\n(.*?)(?=\n\S|\Z)", doc, re.DOTALL)
            if section:
                for parameter in re.findall(
                    r"^    (\*{0,2}\w+)(?: \([^\n]+\))?:", section[1], re.MULTILINE
                ):
                    if parameter.lstrip("*") not in params:
                        issues.append(f"说明参数不在签名中：{name}.{parameter}")
    return issues


def code(value):
    return "`" + str(value).replace("|", "\\|").replace("`", "'").replace("\n", " ") + "`"


def reference_pages(manifest):
    pages = {}
    guide_map = {
        "reference/colors.md": (
            "../guides/plotting.md#颜色值与字符串",
            "颜色值提供构造、分量读取与透明度替换；颜色参数在策略内为 Color，配置和绘图导出为字符串。",
        ),
        "reference/core.md": (
            "../quickstart.md",
            "作者通过 backtest 声明策略默认设置；宿主构造 Backtest 并执行，Strategy 定义初始化与逐步交易逻辑。",
        ),
        "reference/trading.md": (
            "../guides/trading.md",
            "Order 表示待处理订单，Trade 表示单笔交易，Position 汇总当前仓位。平仓请求与成交发生在不同阶段。",
        ),
        "reference/helpers.md": (
            "../examples.md",
            "辅助函数和可组合策略基类用于重采样、信号驱动、移动止损与批量研究。继承基类时按说明调用 super。",
        ),
        "reference/inputs.md": (
            "../guides/inputs.md",
            "在策略类中声明参数，再按唯一 title 发现和注入值；定义、解析与运行时值分开管理。",
        ),
        "reference/runtime.md": (
            "../guides/runtime.md",
            "宿主发现本模块直接装饰的策略，注入图表数据、上下文与品种后执行；发现不依赖行情。",
        ),
        "reference/optimizer.md": (
            "../guides/optimizer.md",
            "参数实验固定当前配置，逐组保存完整 Portfolio；结果集支持重开、筛选和排序。",
        ),
        "reference/indicator-api.md": (
            "../guides/indicators.md",
            "策略通过 self.ta 登记指标；句柄按运行游标读取，显式转换产生快照。离线计算使用 compute。",
        ),
    }
    ordered = []

    def append_members(name):
        ordered.append(name)
        for child, metadata in manifest["objects"].items():
            if child.rpartition(".")[0] == name and metadata["status"] == "recommended":
                append_members(child)

    for name, entry in manifest["objects"].items():
        parent = manifest["objects"].get(name.rpartition(".")[0], {})
        if entry["status"] == "recommended" and parent.get("status") != "recommended":
            append_members(name)
    for name in ordered:
        entry = manifest["objects"][name]
        if entry["status"] != "recommended":
            continue
        obj = resolve(name)
        guide, introduction = guide_map.get(entry["page"], ("../index.md", "公开对象参考。"))
        lines = pages.setdefault(
            entry["page"],
            [
                f"# {manifest['pages'][entry['page']]}",
                "",
                GENERATED,
                "",
                introduction,
                "",
                f"[使用指南]({guide}) · [兼容与内部入口](classification.md)",
                "",
            ],
        )
        parent = name.rpartition(".")[0]
        nested = (
            parent in manifest["objects"] and manifest["objects"][parent]["status"] == "recommended"
        )
        title = name.rsplit(".", 1)[-1]
        # 保留对象锚点，Markdown 手册中的深链接仍定位对应对象。
        anchor = name.lower().replace("_", "-").replace(".", "-")
        # 装饰器与历史 Backtest 类仅大小写不同，保留旧类锚点。
        if name == "openbacktesting.backtest":
            anchor += "-declaration"
        elif inspect.isfunction(obj) and any(
            other != name and other.lower() == name.lower() for other in ordered
        ):
            anchor += "-function"
        lines += [f'<a id="{anchor}"></a>', "", f"{'###' if nested else '##'} {title}", ""]
        if entry.get("summary"):
            lines += [entry["summary"], ""]
        path = source_path(obj)

        documented = (
            isinstance(obj, (functools.partial, classmethod, staticmethod, property, Enum))
            or inspect.isfunction(obj)
            or inspect.isclass(obj)
            or nested
            and dataclasses.is_dataclass(resolve(parent))
        )
        if not documented:
            lines += [f"{code(name)} = {code(obj)}。", ""]
            continue
        lines += [f"完整对象：`{name}`", ""]
        target = doc_object(obj)
        if callable(target):
            signature = re.sub(r" at 0x[0-9a-f]+", "", str(inspect.signature(target)))
            lines += ["```python", f"{name}{signature}", "```", ""]
        description = inspect.getdoc(target)
        if description:
            lines += [description, ""]
        if path:
            lines += [f"源码：{code(path)}。", ""]
        if dataclasses.is_dataclass(obj):
            lines += [
                "字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。",
                "",
                "| 字段 | 类型 |",
                "| --- | --- |",
            ]
            lines += [
                f"| {code(field.name)} | {code(field.type)} |"
                for field in dataclasses.fields(obj)
                if not field.name.startswith("_")
            ]
            lines += [""]
    for name, entry in manifest.get("instance_fields", {}).items():
        anchor = name.lower().replace("_", "-").replace(".", "-")
        pages[entry["page"]] += [
            f'<a id="{anchor}"></a>',
            "",
            f"## {name.rsplit('.', 1)[-1]} 实例字段",
            "",
            entry["summary"],
            "",
        ]
    lines = [
        "# API 分类与兼容入口",
        "",
        GENERATED,
        "",
        "分类区分推荐调用、现存别名与内部依赖；当前用法见各主题指南。",
        "",
        "| 路径 | 分类 | 原因及推荐路径 |",
        "| --- | --- | --- |",
    ]
    for name, entry in manifest["objects"].items():
        if entry["status"] != "recommended":
            note = entry["reason"] + ("；" + entry["canonical"] if entry.get("canonical") else "")
            lines.append(f"| {code(name)} | {entry['status']} | {note} |")
    pages["reference/classification.md"] = lines + [""]
    return {path: "\n".join(lines) for path, lines in pages.items()}


CATEGORIES = {
    "candles": "蜡烛与形态",
    "cycles": "周期",
    "momentum": "动量",
    "overlap": "均线与价格",
    "performance": "收益与回撤",
    "statistics": "统计",
    "trend": "趋势",
    "utility": "序列工具",
    "volatility": "波动率",
    "volume": "成交量",
}
STATUS_NAMES = {
    "available": "可用",
    "deferred-pattern": "形态延期",
    "research-only": "仅供研究",
    "non-series": "非逐根序列",
    "unsupported": "不支持",
}


def check_indicator_notes(entries, notes, root=ROOT):
    issues = []
    known = {row["id"] for row in entries}
    for indicator in sorted(set(notes) - known):
        issues.append(f"孤立指标说明：{indicator}")
    for row in entries:
        note = notes.get(row["id"], {})
        for field in ("name", "summary"):
            if not isinstance(note.get(field), str) or not note[field].strip():
                issues.append(f"缺少指标解释：{row['id']}.{field}")
        if row["status"] != "available":
            if any(key in note for key in ("example", "symbol", "channel")):
                issues.append(f"非可用条目不能绑定用法：{row['id']}")
            continue
        if note.get("channel") not in row["outputs"]:
            issues.append(f"输出关联失配：{row['id']}")
        location = root / note.get("example", "")
        if not location.resolve().is_relative_to(root.resolve()) or not location.is_file():
            issues.append(f"示例关联失效：{row['id']}")
        else:
            tree = ast.parse(location.read_text())
            symbols = {
                node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
            }
            if note.get("symbol") not in symbols:
                issues.append(f"示例符号失效：{row['id']}")
    return issues


def indicator_usage(row, note):
    """生成的片段由文档执行回归逐项验证；输入数据见共享示例。"""
    name = row["id"].removeprefix("ta.")
    standard = {"open_": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}
    extra = {key: key for key in row["inputs"] if key not in standard}
    if row["inputs"] == ["close"]:
        arguments = "self.close"
    elif extra:
        mapping = {key: standard.get(key, key) for key in row["inputs"]}
        arguments = "inputs=" + repr(mapping)
    else:
        arguments = ""
    handle = "self.value" if len(row["outputs"]) == 1 else f"self.value.{note['channel']}"
    return (
        f"def init(self):\n    self.value = self.ta.{name}({arguments})\n"
        "    self.latest_value = None\n\n"
        f"def next(self):\n    channel = {handle}\n"
        "    if channel.valid[-1]:\n        self.latest_value = float(channel[-1])\n"
    )


def input_explanation(row):
    descriptions = {
        "benchmark": "benchmark 为滞后价格演示列，须替换为同日历真实基准",
        "periods": "periods 为逐根周期，示例固定为 10",
        "fast": "fast 为 3 根收盘均值",
        "slow": "slow 为 10 根收盘均值",
        "left": "left 为 3 根收盘均值",
        "right": "right 为 10 根收盘均值",
        "condition": "condition 表示收盘高于开盘",
        "trend": "trend 表示收盘高于开盘",
        "signal": "signal 为收盘百分比变化",
        "anchor": "anchor 每 20 根标记一次，须替换为真实周期起点",
        "source": "source 使用收盘价",
    }
    extra = [descriptions[key] for key in row["inputs"] if key in descriptions]
    return "示例输入：" + ("；".join(extra) if extra else "随包 GOOG 的对应行情列") + "。"


def constraint_text(rule):
    labels = {"minimum": "最小值", "maximum": "最大值", "choices": "可选值"}
    parts = []
    for key, value in rule.items():
        if key not in {"kind", "default"}:
            parts.append(f"{labels.get(key, key)}：{code(value)}")
    return "；".join(parts) or "无额外约束"


def indicator_pages(entries):
    from openbacktesting.indicators.methods import TechnicalAnalysis
    from openbacktesting.indicators.registry import BINDINGS

    notes = json.loads((DOCS / "indicator-notes.json").read_text())
    pages = {}
    groups = {}
    for row in sorted(entries, key=lambda row: row["id"]):
        name = row["id"].removeprefix("ta.")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise ValueError(f"非法指标 ID：{name}")
        groups.setdefault(row["category"], []).append(row)
        lines = [
            f"# {row['id']}",
            "",
            GENERATED,
            "",
            f"类别：{CATEGORIES[row['category']]}；状态：{STATUS_NAMES[row['status']]}。",
            "",
        ]
        note = notes[row["id"]]
        lines[4:4] = [f"**{note['name']}**。{note['summary']}", ""]
        if row["status"] == "available":
            lines += [
                "## 使用方法",
                "",
                "在 `init()` 登记，在 `next()` 检查所选通道的 `valid` 后读取当前值。",
                "",
                "```python",
                indicator_usage(row, note).rstrip(),
                "```",
                "",
                f"用法选择通道 {code(note['channel'])}；全部通道见下方输出表。",
                "",
                f"完整可执行来源：[逐项体验指标](../../../../{note['example']})，入口 {code(note['symbol'])}。在仓库根目录运行：",
                "",
                "```sh",
                f"uv run --locked python {note['example']} --indicator {row['id']}",
                "```",
                "",
                input_explanation(row),
                "",
                "`ready` 表示必要输出与最低历史条件是否就绪，`valid` 表示当前通道可消费；两者均不控制策略回调，next 从首根执行。示例逐通道检查 valid，NaN 不应参与交易判断。",
                "",
                "### 调用签名",
                "",
            ]
        if row["status"] != "available":
            lines += [f"尚不可调用：{row['reason']}", ""]
        else:
            method = getattr(TechnicalAnalysis, name)
            params = inspect.signature(method).parameters
            inputs = row.get("input_args") or (["source"] if len(row["inputs"]) == 1 else [])
            expected = {
                "self",
                "inputs",
                "backend",
                "required_outputs",
                *inputs,
                *row["parameters"],
            }
            if set(params) != expected:
                raise ValueError(f"指标方法参数集合与目录失配：{row['id']}")
            for key, rule in row["parameters"].items():
                if key not in params or params[key].default != rule["default"]:
                    raise ValueError(f"指标方法签名与目录失配：{row['id']}.{key}")
            lines += [
                "```python",
                f"self.ta.{name}{signature(method).replace('(self, ', '(')}",
                "```",
                "",
            ]
        lines += [
            "## 输入、输出与参数",
            "",
            f"输入：{code(', '.join(row['inputs']))}。输出规范名：{code(', '.join(row['outputs']))}。",
            "",
            "输出别名："
            + (
                "；".join(f"{code(k)} → {code(v)}" for k, v in row.get("aliases", {}).items())
                or "无"
            )
            + "。",
            "",
            "| 参数 | 类型 | 默认值 | 约束 |",
            "| --- | --- | --- | --- |",
        ]
        for key, rule in row["parameters"].items():
            lines += [
                f"| {code(key)} | {code(rule['kind'])} | {code(rule['default'])} | {constraint_text(rule)} |"
            ]
        if not row["parameters"]:
            lines += ["| 无 | — | — | — |"]
        lines += [
            "",
            "## 语义与计算来源",
            "",
            f"语义版本：{code(row['version'])}。",
            "",
            "参数与输出以本页目录字段为准；[共同指标契约](../../guides/indicators.md)说明调用阶段、缺失、有效性、确认时点与缓存边界。算法不承诺 Pine 等价。",
            "",
            "| 字段 | 审核值 |",
            "| --- | --- |",
        ]
        for key in [
            "source",
            "kind",
            "dtype",
            "unit",
            "missing_policy",
            "validity",
            "causal",
            "minimum",
            "windows",
            "history_sum",
            "history_offset",
            "required",
            "fixed",
            "input_args",
            "input_defaults",
        ]:
            if key in row:
                lines += [f"| {code(key)} | {code(row[key])} |"]
        lines += [
            "",
            "`required=None` 使用默认必要输出；`required=[]` 不要求输出通道就绪。minimum/windows/history_sum/history_offset 共同确定最低历史长度；这些元数据不控制回调，实际消费还须检查 valid。未出现的字段使用定义默认值，详见 [IndicatorSpec](../indicator-api.md)。",
            "",
        ]
        if row["status"] == "available":
            bindings = [(key, binding) for key, binding in BINDINGS.items() if key[0] == row["id"]]
            for key, binding in sorted(bindings):
                lines += [
                    f"后端 {code(key[1])}；实现版本 {code(binding.implementation_version)}；源码 {code(source_path(binding.compute))}。",
                    "",
                ]
            lines += [
                f"默认后端：{code(row.get('default_backend', 'pandas-ta-classic.native'))}。",
                "",
            ]
        lines += [
            f"验证定位：{code(row['test'])}；完整使用例见[示例入口](../../examples.md)。",
            "",
            "[返回分类目录](index.md)",
            "",
        ]
        pages[f"reference/indicators/{name}.md"] = "\n".join(lines)
    lines = [
        "# 指标目录",
        "",
        GENERATED,
        "",
        f"审核目录共 {len(entries)} 项，其中 {sum(r['status'] == 'available' for r in entries)} 项可用；数量来自当前目录，不包含通道别名。",
        "",
    ]
    lines += [
        "```{raw} html",
        '<div class="indicator-search"><label for="indicator-query">查找中文名称、ID 或输出别名</label>',
        '<input id="indicator-query" type="search" placeholder="例如：指数移动平均 / ta.ema" aria-describedby="indicator-status">',
        '<p id="indicator-status" aria-live="polite">输入名称或 ID，或直接浏览下方分类。</p><ul id="indicator-results"></ul></div>',
        "```",
        "",
    ]
    pages["_static/indicator-index.json"] = (
        json.dumps(
            [
                {
                    "id": row["id"],
                    "name": notes[row["id"]]["name"],
                    "category": CATEGORIES[row["category"]],
                    "aliases": list(row.get("aliases", {})),
                    "status": STATUS_NAMES[row["status"]],
                    "href": row["id"].removeprefix("ta.") + ".html",
                }
                for row in sorted(entries, key=lambda row: row["id"])
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    for category, rows in sorted(groups.items()):
        lines += [f"({category})=", "", f"## {CATEGORIES[category]}", ""]
        lines += [
            f"- [{notes[r['id']]['name']} · {r['id']}]({r['id'].removeprefix('ta.')}.md)：{STATUS_NAMES[r['status']]}"
            for r in rows
        ]
        lines += [""]
    lines += [
        "```{toctree}",
        ":hidden:",
        "",
        *[r["id"].removeprefix("ta.") for r in sorted(entries, key=lambda r: r["id"])],
        "```",
        "",
    ]
    pages["reference/indicators/index.md"] = "\n".join(lines)
    return pages


def expected_pages(manifest, entries):
    notes = json.loads((DOCS / "indicator-notes.json").read_text())
    issues = check_indicator_notes(entries, notes)
    if issues:
        raise ValueError("\n".join(issues))
    pages = reference_pages(manifest) | indicator_pages(entries)
    return {
        name: re.sub(r"^\(([^)]+)\)=$", r'<a id="\1"></a>', content, flags=re.MULTILINE)
        for name, content in pages.items()
    }


def sync_pages(expected, docs=DOCS, check=False):
    issues = []
    actual = {
        p.relative_to(docs).as_posix(): p
        for p in (docs / "reference").rglob("*.md")
        if GENERATED in p.read_text()
    }
    for name, content in expected.items():
        path = docs / name
        if not path.exists() or path.read_text() != content:
            issues.append(f"生成参考缺失或过期：{name}")
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
    for name in sorted(actual.keys() - expected.keys()):
        issues.append(f"多余生成参考：{name}")
        if not check:
            actual[name].unlink()
    return issues if check else []


def check_examples(docs=DOCS):
    issues = []
    index = (ROOT / "examples/README.md").read_text()
    examples = re.findall(r"\]\(((?:strategies|advanced)/[^)]+\.py)\)", index)
    page = (docs / "examples.md").read_text()
    for name in examples:
        if f"examples/{name}" not in page:
            issues.append(f"示例未展示：{name}")
    if "[示例索引](../../examples/README.md)" not in page:
        issues.append("示例索引未复用原始 README")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((DOCS / "api-manifest.json").read_text())
    entries = json.loads(CATALOG.read_text())["entries"]
    issues = sync_pages(expected_pages(manifest, entries), check=args.check)
    if args.check:
        issues += check_manifest(manifest) + check_examples()
    if issues:
        raise SystemExit("\n".join(issues))
    print("文档事实源与生成参考一致" if args.check else "已生成公开 API 与指标参考")


if __name__ == "__main__":
    main()
