"""Typed strategy parameters: declaration, discovery, normalization, and title-based resolution."""

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
    """Parameter error that callers can display using code/title/expected/actual_type."""

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
        # longdouble.item() does not guarantee a Python float; lossy conversion is prohibited.
        if type(native) not in (_b.bool, _b.int, _b.float):
            _fail("InvalidInputValue", title, "Lossless Python scalar", value)
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
        _fail("InvalidInputValue", title, "Weekdays must not repeat", value)
    for clock in re.split("[-,]", periods):
        if _b.int(clock[:2]) > 23 or _b.int(clock[2:]) > 59:
            _fail("InvalidInputValue", title, "Time range 0000–2359", value)
    return periods + ":" + "".join(sorted(days))


@dataclass(frozen=True, eq=False)
class InputSpec:
    """Immutable strategy class-field declaration created by inputs factories; instance reads return this run's value."""

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
        _fail("ImmutableInput", self.title, "input is read-only within this run", value)

    def __delete__(self, instance):
        _fail("ImmutableInput", self.title, "input cannot be deleted")

    def normalize(self, value, *, wire=False):
        """Validate and normalize value; wire=True parses enums from their serialized form, and invalid values raise InputError."""
        value = _scalar(value, self.title)
        kind = self.kind
        if kind == "color":
            try:
                return Color.from_hex(value) if wire else _as_color(value)
            except (TypeError, ValueError) as error:
                raise InputError(
                    "InvalidInputValue",
                    self.title,
                    "Color or #RRGGBB/#RRGGBBAA (wire accepts strings only)",
                    value,
                ) from error
        if kind == "enum":
            if wire:
                if type(value) is not str or value not in self.enum_type.__members__:
                    _fail("InvalidInputValue", self.title, "Enum member name", value)
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
            _fail("InvalidInputValue", self.title, f"valid {kind} value", value)
        if kind == "session":
            value = _session(value, self.title)
        if self.options is not None and value not in self.options:
            _fail("InvalidInputValue", self.title, "Value must belong to options", value)
        for key, boundary in self.bounds:
            if (key == "minval" and value < boundary) or (key == "maxval" and value > boundary):
                _fail("InvalidInputValue", self.title, f"satisfying {key}={boundary}", value)
        return value

    def encode(self, value):
        """Encode normalized value into configuration form; enums use member names, and colors use uppercase eight-digit strings."""
        if self.kind == "color":
            return value.to_hex()
        return value.name if self.kind == "enum" else value

    def export(self, attribute):
        """Export the declaration dictionary; attribute is the Python field name, while configuration associations use unique title."""
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
    """Declare read-only strategy configuration fields; inputs.bool/int/float and other entry points bind the kind.

    Args:
        defval: Default value matching the declared kind.
        title: Required and unique within one strategy; also the title-based configuration key.
        tooltip: Hint text.
        group: Display group, without changing title uniqueness scope.
        inline: Hint for display on the same row.
        display: all/none/status_line/data_window; metadata only.
        active: Boolean constant or mapping referencing a bool parameter title; does not bypass value validation.
        confirm: Confirmation-hint metadata, without opening a UI.
        options: Allowed-value set; numeric kinds cannot also specify bounds or step.
        minval: Numeric lower bound for int/float only.
        maxval: Numeric upper bound for int/float only.
        step: Adjustment increment, not a divisibility constraint; int/float only.

    Returns:
        InputSpec: Class-field descriptor; instance reads return this run's resolved value.

    Raises:
        InputError: Invalid declaration, default, parameter domain, or display metadata.
    """
    if type(title) is not str or not title.strip():
        _fail("InvalidDeclaration", title, "title is required and must not be empty", title)
    if any(type(v) is not str for v in (tooltip, group, inline)):
        _fail("InvalidDeclaration", title, "tooltip/group/inline must be strings")
    display = display if display is not None else ("none" if kind in ("bool", "color") else "all")
    if display not in ("all", "none", "status_line", "data_window") or type(confirm) is not _b.bool:
        _fail("InvalidDeclaration", title, "Valid display and boolean confirm")
    if isinstance(active, Mapping) and set(active) == {"title"} and type(active["title"]) is str:
        active = active["title"]
    elif type(active) is not _b.bool:
        _fail("InvalidDeclaration", title, "active must be bool or a title reference", active)
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
            _fail("InvalidDeclaration", title, "Default value must be an Enum member", defval)
        enum_type = type(defval)
        if len(enum_type.__members__) != len(enum_type):
            _fail("InvalidDeclaration", title, "Enums must not contain aliases")
    spec = InputSpec(kind, title, defval, metadata=metadata, enum_type=enum_type)
    bounds = {
        k: v for k, v in (("minval", minval), ("maxval", maxval), ("step", step)) if v is not _UNSET
    }
    if (bounds and kind not in ("int", "float")) or (bounds and options is not _UNSET):
        _fail("InvalidDeclaration", title, "Numeric bounds apply only to int/float and are mutually exclusive with options")
    try:
        bounds = {key: spec.normalize(value) for key, value in bounds.items()}
        if "minval" in bounds and "maxval" in bounds and bounds["minval"] > bounds["maxval"]:
            _fail("InvalidDeclaration", title, "minval must not exceed maxval")
        if "step" in bounds and bounds["step"] <= 0:
            _fail("InvalidDeclaration", title, "step must be greater than zero")
        normalized_options = None
        if options is not _UNSET:
            if (
                kind not in ("int", "float", "string", "session", "enum")
                or not isinstance(options, (list, tuple))
                or not options
            ):
                _fail("InvalidDeclaration", title, "This type requires a nonempty options list", options)
            normalized_options = tuple(spec.normalize(v) for v in options)
            if len(set(normalized_options)) != len(normalized_options):
                _fail("InvalidDeclaration", title, "options must not repeat")
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
            _fail("InvalidDeclaration", fields[name].title, f"Ordinary attribute shadows input: {name}")
    if conflicts:
        _fail("InvalidDeclaration", None, f"Multiple-inheritance field conflict: {sorted(conflicts)}")
    return fields


def _definitions(cls):
    if not isinstance(cls, type):
        _fail("InvalidDeclaration", None, "Loaded strategy class", cls)
    bases = [base for base in cls.__mro__ if vars(base).get("_input_strategy_base") is True]
    if not bases:
        _fail("InvalidDeclaration", None, "Must inherit Strategy", cls)
    reserved = set(vars(bases[0]))
    data_names = vars(bases[0]).get("_reserved_data_names", ())
    for base in cls.__mro__:
        if base is not bases[0]:
            conflicts = set(data_names).intersection(vars(base))
            if conflicts:
                name = min(conflicts)
                _fail("InvalidDeclaration", name, f"Reserved field {name}; rename the field with the same name")
    fields = _collect(cls)
    by_title = {}
    for name, spec in fields.items():
        if name.startswith("_") or name in reserved or len(spec.bindings) != 1:
            _fail("InvalidDeclaration", spec.title, f"Reserved field or reused declaration: {name}")
        if spec.title in by_title:
            _fail("InvalidDeclaration", spec.title, "title must be unique within one strategy")
        by_title[spec.title] = spec
    for title in by_title:
        visited = set()
        current = title
        while type(current) is str:
            if current in visited:
                _fail("InvalidDeclaration", title, "active must not form dependency cycles")
            visited.add(current)
            reference = dict(by_title[current].metadata)["active"]
            if type(reference) is str and (
                reference not in by_title or by_title[reference].kind != "bool"
            ):
                _fail("InvalidDeclaration", title, "active must reference an existing bool title")
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
    """Export an independent JSON definition of the loaded strategy class without running it."""
    return _schema(_definitions(strategy_class))


@dataclass(frozen=True)
class ResolvedInputs:
    """Validated input-resolution result containing the declaration digest, runtime values, encoded values, and explicitly overridden titles."""

    schema_hash: str
    runtime: tuple
    encoded: tuple
    overridden: tuple
    attributes: tuple

    def snapshot(self):
        """Return a snapshot of version, declaration digest, complete values, and explicitly overridden titles for result attrs."""
        return {
            "schemaVersion": SCHEMA_VERSION,
            "schemaHash": self.schema_hash,
            "values": dict(self.encoded),
            "overriddenTitles": list(self.overridden),
        }

    def overrides(self):
        """Return explicitly overridden Python fields and values for injection into strategy instances."""
        runtime = dict(self.runtime)
        return {
            attribute: runtime[title]
            for title, attribute in self.attributes
            if title in self.overridden
        }


def _resolve(fields, values, *, wire):
    if not isinstance(values, Mapping):
        _fail("InvalidInputValue", None, "Mapping indexed by title", values)
    known = {spec.title for spec in fields.values()}
    for title in values:
        if title not in known:
            _fail("UnknownInput", title, "Titles in the current declaration")
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
    """Native field entry point; undeclared classes return None to preserve legacy behavior."""
    fields = _definitions(strategy_class)
    if not fields:
        return None
    for name in kwargs:
        if name not in fields:
            _fail("UnknownInput", name, "Declared Python fields")
    return _resolve(
        fields, {fields[name].title: value for name, value in kwargs.items()}, wire=False
    )


def resolve_request(strategy_class, request):
    """Validate request version, digest, and title values against strategy_class; failures raise InputError, and success returns ResolvedInputs."""
    fields = _definitions(strategy_class)
    if not fields:
        _fail("InvalidDeclaration", None, "Title-based entry requires at least one input")
    if not isinstance(request, Mapping) or set(request) != {
        "schemaVersion",
        "schemaHash",
        "values",
    }:
        _fail("InvalidInputValue", None, "schemaVersion/schemaHash/values request", request)
    if request["schemaVersion"] != SCHEMA_VERSION:
        _fail("UnsupportedInputVersion", None, SCHEMA_VERSION, request["schemaVersion"])
    if request["schemaHash"] != _schema(fields)["schemaHash"]:
        _fail("SchemaMismatch", None, "Rediscover and verify the current declaration", request["schemaHash"])
    return _resolve(fields, request["values"], wire=True)


def request_for(strategy_class, kwargs):
    """Convert Python field kwargs for a declared strategy_class into a title-based request; first confirm the class contains Input; invalid values raise InputError."""
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
