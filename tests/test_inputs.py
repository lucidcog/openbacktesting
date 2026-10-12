"""Public parameter-declaration and serialization behavior, rejection boundaries, and stability."""

import json
import pickle
from dataclasses import FrozenInstanceError
from enum import Enum

import numpy as np
import pytest

from openbacktesting import Color, Strategy, inputs


class Mode(Enum):
    FAST = "快速"
    SLOW = "慢速"


class Other(Enum):
    FAST = "快速"


class Alias(Enum):
    A = 1
    B = 1  # noqa: PIE796 — verify enum alias rejection


def strategy(**fields):
    return type(
        "Probe", (Strategy,), {"init": lambda self: None, "next": lambda self: None, **fields}
    )


def request(cls, values):
    schema = inputs.describe(cls)
    return {
        "schemaVersion": schema["schemaVersion"],
        "schemaHash": schema["schemaHash"],
        "values": values,
    }


def test_nine_types_exports_and_roundtrip():
    cls = strategy(
        enabled=inputs.bool(True, title="Enabled"),
        shade=inputs.color("#aabbcc", title="Color"),
        mode=inputs.enum(Mode.FAST, title="Mode", options=[Mode.FAST, Mode.SLOW]),
        ratio=inputs.float(1, title="Ratio", minval=0, maxval=2, step=0.25),
        length=inputs.int(20, title="Period", options=[10, 20, 30]),
        price=inputs.price(-1, title="Price"),
        hours=inputs.session("24x7", title="Session", options=["24x7", "0900-1700:5432"]),
        text=inputs.string(" a\\nb ", title="Text", confirm=True),
        start=inputs.time(1700000000000, title="Time"),
    )
    schema = inputs.describe(cls)
    assert [x["kind"] for x in schema["inputs"]] == [
        "bool",
        "color",
        "enum",
        "float",
        "int",
        "price",
        "session",
        "string",
        "time",
    ]
    assert json.loads(json.dumps(schema)) == schema
    assert schema["inputs"][1]["default"] == "#AABBCCFF"
    assert schema["inputs"][2]["members"] == [
        {"name": "FAST", "title": "FAST"},
        {"name": "SLOW", "title": "SLOW"},
    ]
    assert schema["inputs"][2]["enumTypeId"].endswith(".Mode")
    resolved = inputs.resolve_request(cls, request(cls, {"Mode": "SLOW", "Session": "0900-1700:2345"}))
    assert dict(resolved.runtime)["Mode"] is Mode.SLOW
    assert resolved.snapshot()["values"]["Mode"] == "SLOW"
    assert resolved.snapshot()["values"]["Session"] == "0900-1700:2345"
    assert resolved.snapshot()["values"]["Text"] == " a\\nb "
    assert resolved.overrides() == {"mode": Mode.SLOW, "hours": "0900-1700:2345"}
    assert pickle.loads(pickle.dumps(resolved)) == resolved
    with pytest.raises(FrozenInstanceError):
        resolved.schema_hash = "changed"
    with pytest.raises(FrozenInstanceError):
        cls.length.title = "changed"
    snapshot = resolved.snapshot()
    snapshot["values"]["Period"] = 999
    assert resolved.snapshot()["values"]["Period"] == 20
    schema["inputs"][2]["options"].append("BAD")
    assert "BAD" not in inputs.describe(cls)["inputs"][2]["options"]


@pytest.mark.parametrize(
    "factory,default,bad",
    [
        ("bool", True, 1),
        ("bool", True, "true"),
        ("int", 1, True),
        ("int", 1, 1.0),
        ("int", 1, "1"),
        ("int", 1, 2**53),
        ("time", 1, -(2**53)),
        ("time", 1, "2026-01-01"),
        ("float", 1.0, True),
        ("float", 1.0, float("nan")),
        ("float", 1.0, float("inf")),
        ("float", 1.0, 2**53 + 1),
        ("float", 1.0, 10**1000),
        ("float", 1.0, "1"),
        ("price", 1.0, float("-inf")),
        ("string", "x", None),
        ("string", "x", 1),
        ("color", "#aabbcc", "red"),
        ("color", "#aabbcc", "#GGHHII"),
        ("session", "24x7", ""),
        ("session", "24x7", "2400-0900"),
        ("session", "24x7", "0060-0900"),
        ("session", "24x7", "0900-1700:22"),
        ("session", "24x7", "0900-1700:8"),
        ("enum", Mode.FAST, Other.FAST),
        ("enum", Mode.FAST, "FAST"),
    ],
)
def test_invalid_native_values(factory, default, bad):
    cls = strategy(value=getattr(inputs, factory)(default, title="Value"))
    with pytest.raises(inputs.InputError) as caught:
        inputs.resolve_native(cls, {"value": bad})
    assert caught.value.code == "InvalidInputValue"
    assert caught.value.title == "Value"
    assert caught.value.expected
    assert caught.value.actual_type


@pytest.mark.parametrize(
    "factory,default,raw,expected",
    [
        ("int", 1, 2**53 - 1, 2**53 - 1),
        ("time", 1, -(2**53 - 1), -(2**53 - 1)),
        ("int", 1, np.int64(2), 2),
        ("float", 1.0, np.float64(1.25), 1.25),
        ("bool", False, np.bool_(True), True),
        ("float", 1.0, -0.0, 0.0),
        ("float", 1.0, 2, 2.0),
        ("price", 1.0, -5.0, -5.0),
        ("session", "24x7", "1700-0900,1000-1100:5432", "1700-0900,1000-1100:2345"),
        ("session", "24x7", "0900-0900", "0900-0900:1234567"),
        ("color", "#aabbcc", "#abcdef00", Color.from_hex("#ABCDEF00")),
    ],
)
def test_valid_values(factory, default, raw, expected):
    cls = strategy(value=getattr(inputs, factory)(default, title="Value"))
    actual = inputs.resolve_native(cls, {"value": raw}).overrides()["value"]
    assert actual == expected and type(actual) is type(expected)


@pytest.mark.parametrize(
    "factory,default,kwargs",
    [
        ("int", 1, {"title": ""}),
        ("int", 1, {"title": "  "}),
        ("int", 1, {"title": 4}),
        ("int", 1, {"tooltip": 2}),
        ("int", 1, {"group": None}),
        ("int", 1, {"inline": True}),
        ("int", 1, {"display": "bad"}),
        ("int", 1, {"confirm": 1}),
        ("int", 1, {"active": "other"}),
        ("int", 1, {"active": {"title": 3}}),
        ("int", 1, {"active": {"title": "x", "more": 1}}),
        ("enum", 1, {}),
        ("enum", Alias.A, {}),
        ("int", 1, {"options": []}),
        ("int", 1, {"options": None}),
        ("int", 1, {"options": [1, 1]}),
        ("int", 1, {"options": [1, True]}),
        ("int", 1, {"options": [2]}),
        ("int", 1, {"options": [1], "step": 1}),
        ("price", 1.0, {"minval": 0}),
        ("price", 1.0, {"options": [1.0]}),
        ("bool", True, {"options": [True]}),
        ("int", 1, {"minval": 2, "maxval": 1}),
        ("int", 1, {"step": 0}),
        ("float", 1.0, {"step": float("nan")}),
        ("int", 1, {"minval": 2}),
        ("int", 2, {"maxval": 1}),
        ("string", lambda: "x", {}),
        ("int", 1, {"id": "extra"}),
        ("int", 1, {"typo": 1}),
    ],
)
def test_invalid_declarations(factory, default, kwargs):
    with pytest.raises((inputs.InputError, TypeError)) as caught:
        getattr(inputs, factory)(default, **({"title": "Value"} | kwargs))
    if isinstance(caught.value, inputs.InputError):
        assert caught.value.code == "InvalidDeclaration"


def test_step_is_not_multiple_of_and_options_reject_outsiders():
    cls = strategy(value=inputs.int(1, title="Value", minval=1, maxval=4, step=2))
    assert inputs.resolve_native(cls, {"value": 2}).overrides() == {"value": 2}
    for value in [0, 5]:
        with pytest.raises(inputs.InputError, match="InvalidInputValue"):
            inputs.resolve_native(cls, {"value": value})
    cls = strategy(value=inputs.string("a", title="Value", options=["a", "b"]))
    with pytest.raises(inputs.InputError, match="options"):
        inputs.resolve_native(cls, {"value": "c"})


def test_discovery_never_invokes_user_lifecycle_or_getters():
    def fail(*args):
        raise AssertionError("Must not be called")

    cls = type(
        "Unrunnable",
        (Strategy,),
        {
            "__init__": fail,
            "init": fail,
            "next": fail,
            "danger": property(fail),
            "period": inputs.int(2, title="Period"),
        },
    )
    assert inputs.describe(cls)["inputs"][0]["attribute"] == "period"
    assert cls.period.kind == "int"
    assert inputs.describe(strategy())["inputs"] == []
    for invalid in [object, object(), 1]:
        with pytest.raises(inputs.InputError, match="InvalidDeclaration"):
            inputs.describe(invalid)


def test_titles_are_required_exact_and_unique_across_groups():
    for fields in [
        {
            "a": inputs.int(1, title="duplicate", group="a"),
            "b": inputs.bool(True, title="duplicate", group="b"),
        },
        {"_secret": inputs.int(1, title="private")},
        {"buy": inputs.int(1, title="buy")},
    ]:
        with pytest.raises(inputs.InputError, match="InvalidDeclaration"):
            inputs.describe(strategy(**fields))
    shared = inputs.int(1, title="duplicate")
    with pytest.raises(inputs.InputError, match="reuse"):
        inputs.describe(strategy(a=shared, b=shared))
    cls = strategy(
        a=inputs.int(1, title="A"), b=inputs.int(1, title="a"), c=inputs.int(1, title=" A")
    )
    assert len(inputs.describe(cls)["inputs"]) == 3
    assert inputs.describe(strategy(a=inputs.int(1, title="A"))) == inputs.describe(
        strategy(a=inputs.int(1, title="A"))
    )


def test_inheritance_order_conflicts_shadowing_and_diamond():
    base = strategy(a=inputs.int(1, title="A"), b=inputs.int(2, title="B"))
    derived = type(
        "Derived", (base,), {"a": inputs.int(3, title="New A"), "c": inputs.bool(True, title="C")}
    )
    assert [x["title"] for x in inputs.describe(derived)["inputs"]] == ["New A", "B", "C"]
    for attrs in [{"a": 3}, {"c": inputs.int(1, title="B")}]:
        with pytest.raises(inputs.InputError):
            inputs.describe(type("Bad", (base,), attrs))
    left = type("Left", (base,), {})
    right = type("Right", (base,), {})
    diamond = type("Diamond", (left, right), {})
    assert inputs.describe(diamond) == inputs.describe(base)
    different = strategy(a=inputs.int(4, title="Another A"))
    with pytest.raises(inputs.InputError, match="Multiple-inheritance"):
        inputs.describe(type("Conflict", (base, different), {}))
    fixed = type("Fixed", (base, different), {"a": inputs.int(5, title="A")})
    assert inputs.describe(fixed)["inputs"][0]["default"] == 5


def test_active_references_and_presentation_hints():
    cls = strategy(
        enabled=inputs.bool(False, title="Enabled"),
        period=inputs.int(1, title="Period", active={"title": "Enabled"}, display="none", confirm=True),
    )
    schema = inputs.describe(cls)
    assert schema["inputs"][1]["active"] == {"title": "Enabled"}
    assert schema["inputs"][1]["confirm"] is True
    assert inputs.resolve_native(cls, {}).snapshot()["values"] == {"Enabled": False, "Period": 1}
    with pytest.raises(inputs.InputError):
        inputs.resolve_native(cls, {"period": "bad"})
    for fields in [
        {"a": inputs.int(1, title="A", active={"title": "missing"})},
        {"a": inputs.int(1, title="A"), "b": inputs.int(1, title="B", active={"title": "A"})},
        {"a": inputs.bool(True, title="A", active={"title": "A"})},
        {
            "a": inputs.bool(True, title="A", active={"title": "B"}),
            "b": inputs.bool(False, title="B", active={"title": "A"}),
        },
    ]:
        with pytest.raises(inputs.InputError, match="InvalidDeclaration"):
            inputs.describe(strategy(**fields))


def test_request_errors_and_native_namespace():
    cls = strategy(a=inputs.enum(Mode.FAST, title="Mode"))
    good = request(cls, {})
    cases = [
        (None, "InvalidInputValue"),
        ({}, "InvalidInputValue"),
        (good | {"extra": 1}, "InvalidInputValue"),
        (good | {"schemaVersion": "unknown"}, "UnsupportedInputVersion"),
        (good | {"schemaHash": "old"}, "SchemaMismatch"),
        (good | {"values": []}, "InvalidInputValue"),
        (good | {"values": {"missing": 1}}, "UnknownInput"),
        (good | {"values": {"a": "FAST"}}, "UnknownInput"),
        (good | {"values": {"Mode": "NOPE"}}, "InvalidInputValue"),
        (good | {"values": {"Mode": Mode.FAST}}, "InvalidInputValue"),
        (good | {"values": {"Mode": None}}, "InvalidInputValue"),
    ]
    for payload, code in cases:
        with pytest.raises(inputs.InputError) as caught:
            inputs.resolve_request(cls, payload)
        assert caught.value.code == code
    with pytest.raises(inputs.InputError, match="UnknownInput"):
        inputs.resolve_native(cls, {"Mode": Mode.FAST})
    with pytest.raises(inputs.InputError, match="at least one"):
        inputs.resolve_request(strategy(), good)
    assert inputs.resolve_native(strategy(), {"legacy": 1}) is None
    assert inputs.request_for(cls, {"a": Mode.SLOW}) == request(cls, {"Mode": "SLOW"})


def test_schema_hash_and_renaming():
    # Retain the localized-title fingerprint as historical compatibility evidence.
    legacy = strategy(length=inputs.int(20, title="周期"))
    assert (
        inputs.describe(legacy)["schemaHash"]
        == "805ec85e93d63ac52224336911d64f0a823baba0556f18848c7b5bfab3e25fa7"
    )
    cls = strategy(length=inputs.int(20, title="Period"))
    before = inputs.describe(cls)
    assert before == inputs.describe(cls)
    assert (
        before["schemaHash"] == "90732d727341902c60bdeeb00dbd7a7b8bc6b7ad65613e80fbc155c835b340b1"
    )
    for other in [
        strategy(length=inputs.int(20, title="renamed")),
        strategy(period=inputs.int(20, title="Period")),
        strategy(length=inputs.int(20, title="Period", tooltip="Description")),
    ]:
        assert inputs.describe(other)["schemaHash"] != before["schemaHash"]
        with pytest.raises(inputs.InputError, match="SchemaMismatch"):
            inputs.resolve_request(other, request(cls, {"Period": 30}))
    renamed = strategy(period=inputs.int(20, title="Period"))
    assert inputs.resolve_request(renamed, request(renamed, {"Period": 30})).overrides() == {
        "period": 30
    }
    zero = strategy(value=inputs.float(-0.0, title="zero"))
    positive = strategy(value=inputs.float(0.0, title="zero"))
    assert inputs.describe(zero) == inputs.describe(positive)


def test_numpy_scalar_must_not_silently_lose_precision():
    from decimal import Decimal

    class ExtendedPrecision(np.float64):
        def item(self):
            # Simulate longdouble returning a nonnative Python scalar on other platforms.
            return Decimal("1.0000000000000000001")

    cls = strategy(value=inputs.float(1.0, title="precision"))
    with pytest.raises(inputs.InputError) as caught:
        inputs.resolve_native(cls, {"value": ExtendedPrecision(1)})
    assert caught.value.code == "InvalidInputValue"
    assert caught.value.title == "precision"
    assert "Lossless" in caught.value.expected
