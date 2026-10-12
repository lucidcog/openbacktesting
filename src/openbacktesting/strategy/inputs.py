"""类型化策略参数：声明、发现、规范化与按标题解析。"""

from __future__ import annotations

import builtins as _b
import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
from functools import partial

import numpy as np

from openbacktesting.colors import Color, _as_color

SCHEMA_VERSION = "1.0.0"
_SAFE_INT = 2**53 - 1
_UNSET = object()


class InputError(ValueError):
    """可由调用方按 code/title/expected/actual_type 展示的参数错误。"""

    def __init__(self, code, title, expected, value=None):
        self.code = code
        self.title = title
        self.expected = expected
        self.actual_type = type(value).__name__
        super().__init__(f"{code}: {title!r}: {expected} (got {self.actual_type})")


def _fail(code, title, expected, value=None):
    raise InputError(code, title, expected, value)


def _scalar(value, title):
    if isinstance(value, (np.bool_, np.integer, np.floating)):
        native = value.item()
        # longdouble.item() 不保证转为 Python float，禁止有损转换。
        if type(native) not in (_b.bool, _b.int, _b.float):
            _fail("InvalidInputValue", title, "无损 Python 标量", value)
        return native
    return value


def _session(value, title):
    if value == "24x7":
        return "0000-0000:1234567"
    match = re.fullmatch(r"([0-9]{4}-[0-9]{4}(?:,[0-9]{4}-[0-9]{4})*)(?::([1-7]+))?", value)
    if not match:
        _fail("InvalidInputValue", title, "HHMM-HHMM[,HHMM-HHMM...][:days]", value)
    periods, days = match.groups()
    days = days or "1234567"
    if len(set(days)) != len(days):
        _fail("InvalidInputValue", title, "星期不可重复", value)
    for clock in re.split("[-,]", periods):
        if _b.int(clock[:2]) > 23 or _b.int(clock[2:]) > 59:
            _fail("InvalidInputValue", title, "时间范围 0000–2359", value)
    return periods + ":" + "".join(sorted(days))


@dataclass(frozen=True, eq=False)
class InputSpec:
    """策略类字段的不可变声明；通过 inputs 工厂创建，实例读取本次运行值。"""

    kind: str
    title: str
    default: object
    options: tuple | None = None
    bounds: tuple = ()
    metadata: tuple = ()
    enum_type: type[Enum] | None = None
    bindings: tuple = field(default=(), repr=False)

    def __set_name__(self, owner, name):
        object.__setattr__(self, "bindings", (*self.bindings, name))

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return dict(instance._resolved_inputs.runtime)[self.title]

    def __set__(self, instance, value):
        _fail("ImmutableInput", self.title, "input 在本次运行中只读", value)

    def __delete__(self, instance):
        _fail("ImmutableInput", self.title, "input 不可删除")

    def normalize(self, value, *, wire=False):
        """验证并规范化 value；wire=True 按序列化表示解析枚举，非法值抛 InputError。"""
        value = _scalar(value, self.title)
        kind = self.kind
        if kind == "color":
            try:
                return Color.from_hex(value) if wire else _as_color(value)
            except (TypeError, ValueError) as error:
                raise InputError(
                    "InvalidInputValue",
                    self.title,
                    "Color 或 #RRGGBB/#RRGGBBAA（wire 仅字符串）",
                    value,
                ) from error
        if kind == "enum":
            if wire:
                if type(value) is not str or value not in self.enum_type.__members__:
                    _fail("InvalidInputValue", self.title, "枚举成员名称", value)
                value = self.enum_type[value]
            valid = type(value) is self.enum_type
        elif kind == "bool":
            valid = type(value) is _b.bool
        elif kind in ("int", "time"):
            valid = type(value) is _b.int and abs(value) <= _SAFE_INT
        elif kind in ("float", "price"):
            valid = type(value) in (_b.int, _b.float)
            if valid:
                try:
                    converted = _b.float(value)
                    valid = math.isfinite(converted) and converted == value
                    value = converted if converted else 0.0
                except OverflowError:
                    valid = False
        else:
            valid = type(value) is str
        if not valid:
            _fail("InvalidInputValue", self.title, f"合法的 {kind} 值", value)
        if kind == "session":
            value = _session(value, self.title)
        if self.options is not None and value not in self.options:
            _fail("InvalidInputValue", self.title, "值必须属于 options", value)
        for key, boundary in self.bounds:
            if (key == "minval" and value < boundary) or (key == "maxval" and value > boundary):
                _fail("InvalidInputValue", self.title, f"满足 {key}={boundary}", value)
        return value

    def encode(self, value):
        """将已规范化 value 编码为配置表示；枚举使用成员名称，颜色使用大写八位字符串。"""
        if self.kind == "color":
            return value.to_hex()
        return value.name if self.kind == "enum" else value

    def export(self, attribute):
        """导出声明字典；attribute 是 Python 字段名，配置关联仍使用唯一 title。"""
        result = {
            "title": self.title,
            "attribute": attribute,
            "kind": self.kind,
            "default": self.encode(self.default),
            **dict(self.bounds),
            **dict(self.metadata),
        }
        if type(result["active"]) is str:
            result["active"] = {"title": result["active"]}
        if self.options is not None:
            result["options"] = [self.encode(v) for v in self.options]
        if self.enum_type is not None:
            result["enumTypeId"] = f"{self.enum_type.__module__}.{self.enum_type.__qualname__}"
            result["members"] = [
                {"name": member.name, "title": member.name} for member in self.enum_type
            ]
        return result


def _make(
    kind,
    defval,
    *,
    title,
    tooltip="",
    group="",
    inline="",
    display=None,
    active=True,
    confirm=False,
    options=_UNSET,
    minval=_UNSET,
    maxval=_UNSET,
    step=_UNSET,
):
    """声明策略的只读配置字段；种类由 inputs.bool/int/float 等入口绑定。

    Args:
        defval: 默认值，必须符合声明种类。
        title: 必填且在同一策略中唯一；同时是标题配置键。
        tooltip: 提示文本。
        group: 展示分组，不改变 title 的唯一性范围。
        inline: 同行展示提示。
        display: all/none/status_line/data_window，仅为元数据。
        active: 布尔常量或引用 bool 参数标题的映射，不跳过值验证。
        confirm: 确认提示元数据，不启动界面。
        options: 可选值集合；数值种类不可同时指定边界或 step。
        minval: 数值下界，仅用于 int/float。
        maxval: 数值上界，仅用于 int/float。
        step: 调整增量，不是整除限制，仅用于 int/float。

    Returns:
        InputSpec: 类字段描述符；实例读取本次解析值。

    Raises:
        InputError: 声明、默认值、参数域或展示元数据非法。
    """
    if type(title) is not str or not title.strip():
        _fail("InvalidDeclaration", title, "title 必填且非空", title)
    if any(type(v) is not str for v in (tooltip, group, inline)):
        _fail("InvalidDeclaration", title, "tooltip/group/inline 必须是字符串")
    display = display if display is not None else ("none" if kind in ("bool", "color") else "all")
    if display not in ("all", "none", "status_line", "data_window") or type(confirm) is not _b.bool:
        _fail("InvalidDeclaration", title, "合法 display 和布尔 confirm")
    if isinstance(active, Mapping) and set(active) == {"title"} and type(active["title"]) is str:
        active = active["title"]
    elif type(active) is not _b.bool:
        _fail("InvalidDeclaration", title, "active 必须是 bool 或标题引用", active)
    metadata = tuple(
        {
            "tooltip": tooltip,
            "group": group,
            "inline": inline,
            "display": display,
            "active": active,
            "confirm": confirm,
        }.items()
    )
    enum_type = None
    if kind == "enum":
        if not isinstance(defval, Enum):
            _fail("InvalidDeclaration", title, "默认值必须为 Enum 成员", defval)
        enum_type = type(defval)
        if len(enum_type.__members__) != len(enum_type):
            _fail("InvalidDeclaration", title, "枚举不可包含别名")
    spec = InputSpec(kind, title, defval, metadata=metadata, enum_type=enum_type)
    bounds = {
        k: v for k, v in (("minval", minval), ("maxval", maxval), ("step", step)) if v is not _UNSET
    }
    if (bounds and kind not in ("int", "float")) or (bounds and options is not _UNSET):
        _fail("InvalidDeclaration", title, "数值边界仅用于 int/float 且与 options 互斥")
    try:
        bounds = {key: spec.normalize(value) for key, value in bounds.items()}
        if "minval" in bounds and "maxval" in bounds and bounds["minval"] > bounds["maxval"]:
            _fail("InvalidDeclaration", title, "minval 不得大于 maxval")
        if "step" in bounds and bounds["step"] <= 0:
            _fail("InvalidDeclaration", title, "step 必须大于零")
        normalized_options = None
        if options is not _UNSET:
            if (
                kind not in ("int", "float", "string", "session", "enum")
                or not isinstance(options, (list, tuple))
                or not options
            ):
                _fail("InvalidDeclaration", title, "此类型需要非空 options 列表", options)
            normalized_options = tuple(spec.normalize(v) for v in options)
            if len(set(normalized_options)) != len(normalized_options):
                _fail("InvalidDeclaration", title, "options 不可重复")
        spec = replace(spec, bounds=tuple(bounds.items()), options=normalized_options)
        return replace(spec, default=spec.normalize(defval))
    except InputError as error:
        raise InputError("InvalidDeclaration", title, error.expected, defval) from error


bool = partial(_make, "bool")
color = partial(_make, "color")
enum = partial(_make, "enum")
float = partial(_make, "float")
int = partial(_make, "int")
price = partial(_make, "price")
session = partial(_make, "session")
string = partial(_make, "string")
time = partial(_make, "time")


def _collect(cls):
    fields = {}
    conflicts = set()
    for base in cls.__bases__:
        for name, spec in _collect(base).items():
            if name in fields and fields[name] is not spec:
                conflicts.add(name)
            else:
                fields[name] = spec
    local = vars(cls)
    for name, value in local.items():
        if isinstance(value, InputSpec):
            fields[name] = value
            conflicts.discard(name)
        elif name in fields:
            _fail("InvalidDeclaration", fields[name].title, f"普通属性遮蔽 input: {name}")
    if conflicts:
        _fail("InvalidDeclaration", None, f"多继承字段冲突: {sorted(conflicts)}")
    return fields


def _definitions(cls):
    if not isinstance(cls, type):
        _fail("InvalidDeclaration", None, "已加载的策略类", cls)
    bases = [base for base in cls.__mro__ if vars(base).get("_input_strategy_base") is True]
    if not bases:
        _fail("InvalidDeclaration", None, "必须继承 Strategy", cls)
    reserved = set(vars(bases[0]))
    data_names = vars(bases[0]).get("_reserved_data_names", ())
    for base in cls.__mro__:
        if base is not bases[0]:
            conflicts = set(data_names).intersection(vars(base))
            if conflicts:
                name = min(conflicts)
                _fail("InvalidDeclaration", name, f"保留字段 {name}，请将同名字段改名")
    fields = _collect(cls)
    by_title = {}
    for name, spec in fields.items():
        if name.startswith("_") or name in reserved or len(spec.bindings) != 1:
            _fail("InvalidDeclaration", spec.title, f"保留字段或复用声明: {name}")
        if spec.title in by_title:
            _fail("InvalidDeclaration", spec.title, "同一策略内 title 必须唯一")
        by_title[spec.title] = spec
    for title in by_title:
        visited = set()
        current = title
        while type(current) is str:
            if current in visited:
                _fail("InvalidDeclaration", title, "active 不可形成依赖环")
            visited.add(current)
            reference = dict(by_title[current].metadata)["active"]
            if type(reference) is str and (
                reference not in by_title or by_title[reference].kind != "bool"
            ):
                _fail("InvalidDeclaration", title, "active 必须引用已有 bool 标题")
            current = reference
    return fields


def _schema(fields):
    schema = {
        "schemaVersion": SCHEMA_VERSION,
        "inputs": [spec.export(name) for name, spec in fields.items()],
    }
    canonical = json.dumps(
        schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    schema["schemaHash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return schema


def describe(strategy_class):
    """导出已加载策略类的独立 JSON 定义，不运行策略。"""
    return _schema(_definitions(strategy_class))


@dataclass(frozen=True)
class ResolvedInputs:
    """已校验的一次输入解析结果，包含声明摘要、运行值、编码值与显式覆盖标题。"""

    schema_hash: str
    runtime: tuple
    encoded: tuple
    overridden: tuple
    attributes: tuple

    def snapshot(self):
        """返回用于结果 attrs 的版本、声明摘要、完整值和显式覆盖标题快照。"""
        return {
            "schemaVersion": SCHEMA_VERSION,
            "schemaHash": self.schema_hash,
            "values": dict(self.encoded),
            "overriddenTitles": list(self.overridden),
        }

    def overrides(self):
        """返回显式覆盖的 Python 字段和值；供策略实例注入使用。"""
        runtime = dict(self.runtime)
        return {
            attribute: runtime[title]
            for title, attribute in self.attributes
            if title in self.overridden
        }


def _resolve(fields, values, *, wire):
    if not isinstance(values, Mapping):
        _fail("InvalidInputValue", None, "按标题索引的映射", values)
    known = {spec.title for spec in fields.values()}
    for title in values:
        if title not in known:
            _fail("UnknownInput", title, "当前声明中的标题")
    runtime, encoded, overridden, attributes = [], [], [], []
    for name, spec in fields.items():
        value = spec.default
        if spec.title in values:
            value = spec.normalize(values[spec.title], wire=wire)
            overridden.append(spec.title)
        runtime.append((spec.title, value))
        encoded.append((spec.title, spec.encode(value)))
        attributes.append((spec.title, name))
    return ResolvedInputs(
        _schema(fields)["schemaHash"],
        tuple(runtime),
        tuple(encoded),
        tuple(overridden),
        tuple(attributes),
    )


def resolve_native(strategy_class, kwargs):
    """原生字段入口；无声明类返回 None 以保留旧行为。"""
    fields = _definitions(strategy_class)
    if not fields:
        return None
    for name in kwargs:
        if name not in fields:
            _fail("UnknownInput", name, "已声明的 Python 字段")
    return _resolve(
        fields, {fields[name].title: value for name, value in kwargs.items()}, wire=False
    )


def resolve_request(strategy_class, request):
    """按 strategy_class 校验 request 的版本、摘要和标题值；失败抛 InputError，返回 ResolvedInputs。"""
    fields = _definitions(strategy_class)
    if not fields:
        _fail("InvalidDeclaration", None, "标题入口需要至少一个 input")
    if not isinstance(request, Mapping) or set(request) != {
        "schemaVersion",
        "schemaHash",
        "values",
    }:
        _fail("InvalidInputValue", None, "schemaVersion/schemaHash/values 请求", request)
    if request["schemaVersion"] != SCHEMA_VERSION:
        _fail("UnsupportedInputVersion", None, SCHEMA_VERSION, request["schemaVersion"])
    if request["schemaHash"] != _schema(fields)["schemaHash"]:
        _fail("SchemaMismatch", None, "重新发现并确认当前声明", request["schemaHash"])
    return _resolve(fields, request["values"], wire=True)


def request_for(strategy_class, kwargs):
    """将有声明的 strategy_class 的 Python 字段 kwargs 转为标题请求；调用前须确认类包含 Input，非法值抛 InputError。"""
    resolved = resolve_native(strategy_class, kwargs)
    snapshot = resolved.snapshot()
    snapshot["values"] = {
        title: value for title, value in resolved.encoded if title in resolved.overridden
    }
    del snapshot["overriddenTitles"]
    return snapshot


from openbacktesting.helpers import _set_legacy_module

_set_legacy_module(InputError, "openbacktesting.inputs")
_set_legacy_module(_fail, "openbacktesting.inputs")
_set_legacy_module(_scalar, "openbacktesting.inputs")
_set_legacy_module(_session, "openbacktesting.inputs")
_set_legacy_module(InputSpec, "openbacktesting.inputs")
_set_legacy_module(_make, "openbacktesting.inputs")
_set_legacy_module(_collect, "openbacktesting.inputs")
_set_legacy_module(_definitions, "openbacktesting.inputs")
_set_legacy_module(_schema, "openbacktesting.inputs")
_set_legacy_module(describe, "openbacktesting.inputs")
_set_legacy_module(ResolvedInputs, "openbacktesting.inputs")
_set_legacy_module(_resolve, "openbacktesting.inputs")
_set_legacy_module(resolve_native, "openbacktesting.inputs")
_set_legacy_module(resolve_request, "openbacktesting.inputs")
_set_legacy_module(request_for, "openbacktesting.inputs")
