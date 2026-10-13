"""Render reviewed user-facing module introductions with live public API signatures."""

from __future__ import annotations

import dataclasses
import inspect
import json
import re
from enum import Enum
from pathlib import Path

TEMPLATES = Path(__file__).with_name("docs")


class DisplayDefault:
    """Represent an enum default as valid public call syntax."""

    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return self.text


# These objects are obtained from runs or callbacks, not constructed by users.
RETURNED = {
    "Strategy",
    "SignalStrategy",
    "TrailingStrategy",
    "Order",
    "Trade",
    "Position",
    "OrderGroup",
    "StrategyLog",
    "IndicatorHandle",
    "IndicatorResult",
    "PortfolioSnapshot",
    "ExperimentResult",
    "Plan",
    "Plotting",
    "PaneRef",
    "PlotRef",
    "FillRef",
    "MarkerRef",
    "SizingDecision",
    "BarState",
    "AccountSnapshot",
    "PositionSnapshot",
    "OrderSnapshot",
    "OrderSizingSnapshot",
    "Fill",
    "OrderEvent",
    "RunSummary",
    "TradeAllocation",
    "ClosedTradeStats",
    "InputError",
    "PlottingError",
    "OptimizationError",
}


def anchor(name):
    value = name.lower().replace("_", "-").replace(".", "-")
    return value + ("-declaration" if name == "openbacktesting.backtest" else "")


def marker(name):
    return f'<a id="{anchor(name)}"></a>\n\n<!-- API: {name} -->'


def summary(obj, doc_object):
    text = (inspect.getdoc(doc_object(obj)) or "").split("\n\n")[0]
    return " ".join(text.split()).replace("|", "\\|")


def call_signature(obj, display):
    """Show callable syntax, excluding the receiver and private controls."""
    sig = inspect.signature(obj)
    params = [
        p.replace(annotation=inspect.Parameter.empty)
        for p in sig.parameters.values()
        if p.name not in {"self", "cls"} and not p.name.startswith("_")
    ]
    # Ellipsis in a displayed default means omit the argument to use the default.
    for i, param in enumerate(params):
        default = param.default
        if isinstance(default, Enum):
            value = (
                "..."
                if type(default).__name__.startswith("_")
                else f"{type(default).__name__}.{default.name}"
            )
            params[i] = param.replace(default=DisplayDefault(value))
        elif type(default) is object:
            params[i] = param.replace(default=Ellipsis)
    clean = str(sig.replace(parameters=params, return_annotation=inspect.Signature.empty))
    clean = clean.replace("Ellipsis", "...")
    if len(display + clean) <= 100:
        return f"```python\n{display}{clean}\n```"
    # Keep long signatures readable without splitting commas inside literal defaults.
    tokens = []
    keyword_separator = False
    for param in params:
        if param.kind == inspect.Parameter.KEYWORD_ONLY and not keyword_separator:
            tokens.append("*")
            keyword_separator = True
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            keyword_separator = True
        tokens.append(str(param).replace("Ellipsis", "..."))
    return "```python\n" + display + "(\n" + "".join(f"    {p},\n" for p in tokens) + ")\n```"


def reference_pages(manifest, resolve, doc_object, generated):
    entries = manifest["objects"]
    rendered = set()
    field_notes = json.loads((TEMPLATES / "fields.json").read_text())

    def join(lines):
        return re.sub(r"(?<=\|)\n\n(?=\|)", "\n", "\n\n".join(filter(None, lines)))

    def render(name):
        if name not in entries or entries[name]["status"] != "recommended":
            raise ValueError(f"Unknown user API in template: {name}")
        obj = resolve(name)
        title = name.rsplit(".", 1)[-1]
        lines = [marker(name), f"## {title}"]
        rendered.add(name)
        if inspect.isclass(obj) and issubclass(obj, Enum):
            lines += [summary(obj, doc_object), "| Member | Value |", "| --- | --- |"]
            for key, member in obj.__members__.items():
                child = f"{name}.{key}"
                lines += [f"| `{title}.{key}` | `{member.value}` |"]
                rendered.add(child)
            lines += ["\n".join(marker(f"{name}.{key}") for key in obj.__members__)]
            return join(lines)
        if callable(obj) and title not in RETURNED:
            display = name.removeprefix("openbacktesting.")
            lines.append(call_signature(obj, display))
        if not callable(obj) and not isinstance(obj, property):
            lines.append(f"`{name.removeprefix('openbacktesting.')} = {obj}`")
            return join(lines)
        lines.append(summary(obj, doc_object))
        data_fields = (
            [field for field in dataclasses.fields(obj) if not field.name.startswith("_")]
            if dataclasses.is_dataclass(obj)
            else []
        )
        if data_fields:
            lines += ["| Attribute | Type | Meaning |", "| --- | --- | --- |"]
            for field in data_fields:
                kind = (
                    field.type
                    if isinstance(field.type, str)
                    else getattr(field.type, "__name__", str(field.type))
                )
                kind = str(kind).replace("|", r"\|")
                child = f"{name}.{field.name}"
                explanation = (
                    field_notes["overrides"]
                    .get(title, {})
                    .get(field.name, field_notes["fields"].get(field.name))
                )
                if not explanation:
                    raise ValueError(f"Missing user field explanation: {child}")
                lines.append(
                    f'| <a id="{anchor(child)}"></a><!-- API: {child} -->`{field.name}` | `{kind}` | {explanation} |'
                )
        children = [
            (n, e)
            for n, e in entries.items()
            if n.rpartition(".")[0] == name and e["status"] == "recommended"
        ]
        properties, methods = [], []
        for child, entry in children:
            member = resolve(child)
            rendered.add(child)
            short = child.rsplit(".", 1)[-1]
            if short in {field.name for field in data_fields}:
                continue
            if callable(doc_object(member)) and not isinstance(member, property):
                methods.append((child, member))
            else:
                properties.append((child, member))
        if properties:
            lines += ["### Attributes", "| Attribute | Meaning |", "| --- | --- |"]
            for child, member in properties:
                short = child.rsplit(".", 1)[-1]
                explanation = entries[child].get("summary") or summary(member, doc_object)
                if not isinstance(member, property):
                    explanation = entries[child].get("summary", "See the fields and example above.")
                lines.append(
                    f'| <a id="{anchor(child)}"></a><!-- API: {child} -->`{short}` | {explanation} |'
                )
        inherited = []
        for child, member in methods:
            short = child.rsplit(".", 1)[-1]
            base = f"openbacktesting.Strategy.{short}"
            if (
                title in {"SignalStrategy", "TrailingStrategy"}
                and base in entries
                and short not in {"init", "next"}
            ):
                inherited.append((child, base))
                continue
            lines += [marker(child), f"### {title}.{short}"]
            target = doc_object(member)
            lines += [call_signature(target, f"{title}.{short}"), summary(member, doc_object)]
        if inherited:
            lines += [
                "### Inherited methods",
                "Use the [Strategy methods](strategy.md) for order sizing, targets, and lifecycle hooks:",
            ]
            lines.append(
                " · ".join(
                    f'<a id="{anchor(child)}"></a><!-- API: {child} -->[{child.rsplit(".", 1)[-1]}](strategy.md#{anchor(base)})'
                    for child, base in inherited
                )
            )
        for field, entry in manifest.get("instance_fields", {}).items():
            if field.rpartition(".")[0] == name and field.rsplit(".", 1)[-1] not in {
                value.name for value in data_fields
            }:
                lines += [marker(field), f"**`{field.rsplit('.', 1)[-1]}`** — {entry['summary']}"]
        return join(lines)

    pages = {}
    for template in sorted(TEMPLATES.glob("*.md.in")):
        source = template.read_text()
        if "{{colors}}" in source:
            color_lines = ["| Preset | RGBA |", "| --- | --- |"]
            for name, entry in entries.items():
                if name.startswith("openbacktesting.colors.") and entry["status"] == "recommended":
                    rendered.add(name)
                    color_lines.append(
                        f'| <a id="{anchor(name)}"></a><!-- API: {name} -->`colors.{name.rsplit(".", 1)[-1]}` | `{resolve(name)}` |'
                    )
            source = source.replace("{{colors}}", "\n".join(color_lines))
        names = re.findall(r"\{\{api ([\w.]+)\}\}", source)
        navigation = " · ".join(
            f"[{name.rsplit('.', 1)[-1]}](#{anchor(name)})"
            for name in names
            if callable(resolve(name))
        )
        content = re.sub(r"\{\{api ([\w.]+)\}\}", lambda m: render(m[1]), source)
        first, rest = content.split("\n", 1)
        introduction, remainder = rest.lstrip().split("\n\n", 1)
        rest = introduction + "\n\n" + navigation + "\n\n" + remainder
        pages[f"reference/{template.name.removesuffix('.in')}"] = (
            first + "\n\n" + generated + "\n\n" + rest
        )
    missing = [
        name
        for name, entry in entries.items()
        if entry["status"] == "recommended" and name not in rendered
    ]
    if missing:
        raise ValueError("User reference templates omit APIs:\n" + "\n".join(missing))
    return pages
