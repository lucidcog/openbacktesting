"""颜色值、量化及配置/绘图边界的行为回归。"""

import json
import math
import pickle
from dataclasses import FrozenInstanceError

import numpy as np
import pytest
from openbacktesting import Color, colors, inputs
from openbacktesting.plotting import PlottingError
from test_bar_coloring import collector
from test_inputs import request, strategy
from test_plotting import handle


def test_value_identity_and_encoding():
    value = Color.from_hex("#22aa44")
    assert value == Color.rgb(34, 170, 68) == Color(34, 170, 68)
    assert str(value) == value.to_hex() == "#22AA44FF"
    assert repr(value) == "Color(red=34, green=170, blue=68, alpha=255)"
    assert (value.red, value.green, value.blue, value.alpha) == (34, 170, 68, 255)
    assert {value: "found"}[Color.from_hex("#22AA44ff")] == "found"
    assert pickle.loads(pickle.dumps(value)) == value
    assert value != str(value) and value != None
    with pytest.raises(FrozenInstanceError):
        value.red = 1
    with pytest.raises(TypeError):
        _ = value < Color(0, 0, 0)
    assert Color(1, 2, 3, 0) != Color(2, 2, 3, 0)
    assert Color(1, 2, 3, 0).to_hex() == "#01020300"


@pytest.mark.parametrize("position", range(4))
@pytest.mark.parametrize("value", [True, 1.0, "1", None, np.int64(1), np.float64(1)])
def test_channel_types(position, value):
    channels = [0, 0, 0, 255]
    channels[position] = value
    with pytest.raises(TypeError):
        Color(*channels)


@pytest.mark.parametrize("position", range(4))
@pytest.mark.parametrize("value", [-1, 256, 10**1000])
def test_channel_range(position, value):
    channels = [0, 0, 0, 255]
    channels[position] = value
    with pytest.raises(ValueError):
        Color(*channels)


@pytest.mark.parametrize("value", [None, 1, True, (1, 2, 3), Color(1, 2, 3)])
def test_hex_type(value):
    with pytest.raises(TypeError):
        Color.from_hex(value)


@pytest.mark.parametrize(
    "value",
    [
        "red",
        "#abc",
        "#abcd",
        "#abcde",
        "#abcdef0",
        "#GG0011",
        " #abcdef",
        "#abcdef\n",
        "#abcdef00\n",
        "rgb(1,2,3)",
    ],
)
def test_hex_format(value):
    with pytest.raises(ValueError):
        Color.from_hex(value)


@pytest.mark.parametrize(
    "t,alpha",
    [(0, 255), (40, 153), (50, 128), (100, 0), (12.5, 223), (50 - 1e-10, 128), (50 + 1e-10, 127)],
)
def test_transparency(t, alpha):
    original = Color(34, 170, 68)
    changed = original.with_transparency(t)
    assert changed == Color.rgb(34, 170, 68, transparency=t)
    assert changed.alpha == alpha
    assert changed.transparency == 100 * (255 - alpha) / 255
    assert original.alpha == 255
    assert changed.with_transparency(0) == original


def test_all_alpha_roundtrips():
    for alpha in range(256):
        value = Color(0, 255, 0, alpha)
        assert value.with_transparency(value.transparency) == value
        assert Color.from_hex(value.to_hex()) == value
    # 按明确的浮点运算公式处理最邻近半值，不另行承诺实数精度。
    for t in [math.nextafter(50, 0), math.nextafter(50, 100)]:
        assert Color.rgb(0, 0, 0, transparency=t).alpha == math.floor(255 * (100 - t) / 100 + 0.5)


@pytest.mark.parametrize("value", [True, "50", None, np.float64(50), np.int64(50)])
def test_transparency_type(value):
    with pytest.raises(TypeError):
        Color.rgb(0, 0, 0, transparency=value)


@pytest.mark.parametrize("value", [-1, 101, 10**1000, float("nan"), float("inf"), float("-inf")])
def test_transparency_range(value):
    with pytest.raises(ValueError):
        colors.RED.with_transparency(value)


def test_fixed_palette():
    expected = {
        "AQUA": "00BCD4",
        "BLACK": "363A45",
        "BLUE": "2196F3",
        "FUCHSIA": "E040FB",
        "GRAY": "787B86",
        "GREEN": "4CAF50",
        "LIME": "00E676",
        "MAROON": "880E4F",
        "NAVY": "311B92",
        "OLIVE": "808000",
        "ORANGE": "FF9800",
        "PURPLE": "9C27B0",
        "RED": "F23645",
        "SILVER": "B2B5BE",
        "TEAL": "089981",
        "WHITE": "FFFFFF",
        "YELLOW": "FDD835",
    }
    assert {name for name in vars(colors) if name.isupper()} == set(expected)
    for name, rgb in expected.items():
        value = getattr(colors, name)
        assert type(value) is Color and value.to_hex() == f"#{rgb}FF"
    assert colors.RED.with_transparency(50).to_hex() == "#F2364580"


def test_input_color_schema_and_native_wire_roundtrip():
    schemas = []
    for default in ["#22aa44", "#22AA44ff", Color(34, 170, 68)]:
        cls = strategy(tint=inputs.color(default, title="颜色"))
        schemas.append(inputs.describe(cls))
        assert cls.tint.default == Color(34, 170, 68)
        for value in ["#aabbcc80", Color(170, 187, 204, 128)]:
            native = inputs.resolve_native(cls, {"tint": value})
            assert dict(native.runtime)["颜色"] == Color(170, 187, 204, 128)
            assert native.snapshot()["values"]["颜色"] == "#AABBCC80"
            payload = inputs.request_for(cls, native.overrides())
            assert inputs.resolve_request(cls, payload) == native
            assert pickle.loads(pickle.dumps(native)) == native
            json.dumps(native.snapshot(), allow_nan=False)
        json.dumps(schemas[-1], allow_nan=False)
    assert schemas[0] == schemas[1] == schemas[2]


@pytest.mark.parametrize(
    "value", [None, "red", "#123", "#123456\n", {"red": 1}, 4, lambda: "#123456"]
)
def test_input_color_errors(value):
    with pytest.raises(inputs.InputError) as error:
        inputs.color(value, title="颜色")
    assert (error.value.code, error.value.title) == ("InvalidDeclaration", "颜色")
    cls = strategy(tint=inputs.color(colors.RED, title="颜色"))
    for resolve in [
        lambda: inputs.resolve_native(cls, {"tint": value}),
        lambda: inputs.resolve_request(cls, request(cls, {"颜色": value})),
    ]:
        with pytest.raises(inputs.InputError) as error:
            resolve()
        assert (error.value.code, error.value.title) == ("InvalidInputValue", "颜色")
    with pytest.raises(inputs.InputError, match="InvalidInputValue"):
        inputs.resolve_request(cls, request(cls, {"颜色": colors.RED}))


@pytest.mark.parametrize("value", ["#22aa44", "#22AA44ff", Color(34, 170, 68)])
def test_all_plotting_color_entries(value):
    p = collector()
    h = handle(p)
    low = p.line(h, color=value)
    high = p.line(h, style="step", color=value)
    p.histogram(h, color=value)
    p.level(0, color=value)
    p.fill(low, high, color=value)
    p._enter("next", 1)
    p.marker(color=value)
    p.bg_color(value)
    p.bar_color(value)
    rows = [*p._plots.values(), *p._fills, *p._markers, *p._color_events]
    assert len(rows) == 8
    assert all(row["color"] == "#22AA44FF" for row in rows)
    json.dumps(rows, allow_nan=False)


def test_no_arbitrary_string_conversion():
    class Pretend:
        def __str__(self):
            raise AssertionError("禁止隐式转换")

    p = collector()
    with pytest.raises(PlottingError, match="invalid-color"):
        p.line(handle(p), color=Pretend())
