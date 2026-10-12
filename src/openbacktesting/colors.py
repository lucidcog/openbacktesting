"""Immutable RGBA color values and fixed presets independent of renderers and runtime context."""

from __future__ import annotations

import re as _re
from dataclasses import dataclass as _dataclass
from math import floor as _floor
from math import isfinite as _isfinite


def _alpha(transparency):
    if type(transparency) not in (int, float):
        raise TypeError("Transparency must be a Python int or float; bool is not accepted")
    if not 0 <= transparency <= 100:
        raise ValueError("Transparency must be a finite number from 0 to 100")
    return _floor(255 * (100 - transparency) / 100 + 0.5)


@_dataclass(frozen=True, slots=True)
class Color:
    """Immutable color compared by all four channels; alpha means opacity, with no implicit equality to strings.

    Args:
        red: Native Python int red component from 0 to 255.
        green: Native Python int green component from 0 to 255.
        blue: Native Python int blue component from 0 to 255.
        alpha: Native Python int from 0 to 255; 0 is fully transparent, 255 is opaque.

    Raises:
        TypeError: A channel is not a native int, including bool.
        ValueError: A channel is outside its range.
    """

    red: int
    green: int
    blue: int
    alpha: int = 255

    def __post_init__(self):
        for value in (self.red, self.green, self.blue, self.alpha):
            if type(value) is not int:
                raise TypeError("Color channels must be Python int values; bool is not accepted")
            if not 0 <= value <= 255:
                raise ValueError("Color channels must be in 0–255")

    @classmethod
    def from_hex(cls, value: str) -> Color:
        """Parse six- or eight-digit hexadecimal colors; append FF for six digits.

        Args:
            value: #RRGGBB or #RRGGBBAA without whitespace, in either case.

        Returns:
            The corresponding color value.

        Raises:
            TypeError: Input is not a native string.
            ValueError: Invalid string format; CSS names and shorthand are not accepted.
        """
        if type(value) is not str:
            raise TypeError("Color must be a hexadecimal string")
        if _re.fullmatch(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?", value) is None:
            raise ValueError("Color must be #RRGGBB or #RRGGBBAA")
        rgba = value[1:] + ("FF" if len(value) == 7 else "")
        return cls(*(int(rgba[i : i + 2], 16) for i in (0, 2, 4, 6)))

    @classmethod
    def rgb(cls, red: int, green: int, blue: int, *, transparency: float = 0) -> Color:
        """Construct from integer RGB and 0–100 transparency; 0 is opaque, 100 is fully transparent.

        Transparency accepts only native finite int/float values; invalid types raise TypeError, out-of-range values raise ValueError.
        Quantize alpha to the nearest byte, rounding half values upward without first rounding the percentage.
        """
        return cls(red, green, blue, _alpha(transparency))

    def with_transparency(self, transparency: float) -> Color:
        """Replace alpha using 0–100 transparency and return a new value; do not modify or multiply the original color.

        Transparency uses the same range, quantization, and exception contract as rgb.
        """
        return Color(self.red, self.green, self.blue, _alpha(transparency))

    @classmethod
    def from_gradient(
        cls,
        value: float,
        *,
        lower: float,
        upper: float,
        lower_color: Color,
        upper_color: Color,
    ) -> Color:
        """Linearly interpolate a scalar between unpremultiplied RGBA bytes at both endpoints; clamp outside the interval.

        Args:
            value: Finite native int/float; bool is not accepted.
            lower: Finite lower bound, strictly below upper.
            upper: Finite upper bound.
            lower_color: Lower-bound Color; None and strings are not accepted.
            upper_color: Upper-bound Color.

        Returns:
            Immutable Color, with each channel rounding half-byte values upward; neither endpoint is modified.

        Raises:
            TypeError: Invalid numeric or color types.
            ValueError: Nonfinite values or invalid bound ordering.
        """
        for number in (value, lower, upper):
            if type(number) not in (int, float):
                raise TypeError("Gradient values and bounds must be Python int or float values")
            try:
                valid = _isfinite(number)
            except OverflowError:
                valid = False
            if not valid:
                raise ValueError("Gradient values and bounds must be finite numbers")
        if lower >= upper:
            raise ValueError("Gradient lower must be less than upper")
        if not isinstance(lower_color, Color) or not isinstance(upper_color, Color):
            raise TypeError("Gradient endpoints must be Color instances")
        if value <= lower:
            return lower_color
        if value >= upper:
            return upper_color
        # upper-lower can overflow for extreme opposite signs; use the original difference for equal signs to avoid losing precision between nearby values.
        if lower < 0 < upper:
            scale = max(-lower, upper)
            ratio = (value / scale - lower / scale) / (upper / scale - lower / scale)
        else:
            ratio = (value - lower) / (upper - lower)
        return cls(
            *(
                _floor(a + (b - a) * ratio + 0.5)
                for a, b in zip(
                    (lower_color.red, lower_color.green, lower_color.blue, lower_color.alpha),
                    (upper_color.red, upper_color.green, upper_color.blue, upper_color.alpha),
                )
            )
        )

    @property
    def transparency(self) -> float:
        """0–100 transparency derived from quantized alpha; it may differ from the original percentage."""
        return 100 * (255 - self.alpha) / 255

    def to_hex(self) -> str:
        """Return uppercase #RRGGBBAA; fully transparent colors retain RGB and do not become None."""
        return f"#{self.red:02X}{self.green:02X}{self.blue:02X}{self.alpha:02X}"

    def __str__(self) -> str:
        return self.to_hex()


def _as_color(value):
    return value if isinstance(value, Color) else Color.from_hex(value)


AQUA = Color.from_hex("#00BCD4")
BLACK = Color.from_hex("#363A45")
BLUE = Color.from_hex("#2196F3")
FUCHSIA = Color.from_hex("#E040FB")
GRAY = Color.from_hex("#787B86")
GREEN = Color.from_hex("#4CAF50")
LIME = Color.from_hex("#00E676")
MAROON = Color.from_hex("#880E4F")
NAVY = Color.from_hex("#311B92")
OLIVE = Color.from_hex("#808000")
ORANGE = Color.from_hex("#FF9800")
PURPLE = Color.from_hex("#9C27B0")
RED = Color.from_hex("#F23645")
SILVER = Color.from_hex("#B2B5BE")
TEAL = Color.from_hex("#089981")
WHITE = Color.from_hex("#FFFFFF")
YELLOW = Color.from_hex("#FDD835")
