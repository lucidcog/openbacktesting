"""不可变 RGBA 颜色值与固定预设；不依赖渲染器或运行上下文。"""

from __future__ import annotations

import re as _re
from dataclasses import dataclass as _dataclass
from math import floor as _floor
from math import isfinite as _isfinite


def _alpha(transparency):
    if type(transparency) not in (int, float):
        raise TypeError("透明度必须为 Python int 或 float，不接受 bool")
    if not 0 <= transparency <= 100:
        raise ValueError("透明度必须为 0–100 的有限数值")
    return _floor(255 * (100 - transparency) / 100 + 0.5)


@_dataclass(frozen=True, slots=True)
class Color:
    """按四通道比较的不可变颜色；alpha 表示不透明度，不与字符串隐式相等。

    Args:
        red: 0–255 的原生 Python int 红色分量。
        green: 0–255 的原生 Python int 绿色分量。
        blue: 0–255 的原生 Python int 蓝色分量。
        alpha: 0–255 的原生 Python int；0 全透明，255 不透明。

    Raises:
        TypeError: 通道不是原生 int，包括 bool。
        ValueError: 通道超出范围。
    """

    red: int
    green: int
    blue: int
    alpha: int = 255

    def __post_init__(self):
        for value in (self.red, self.green, self.blue, self.alpha):
            if type(value) is not int:
                raise TypeError("颜色通道必须为 Python int，不接受 bool")
            if not 0 <= value <= 255:
                raise ValueError("颜色通道必须位于 0–255")

    @classmethod
    def from_hex(cls, value: str) -> Color:
        """解析六/八位十六进制颜色，六位补 FF。

        Args:
            value: 不带空白的 #RRGGBB 或 #RRGGBBAA，大小写均可。

        Returns:
            对应颜色值。

        Raises:
            TypeError: 输入不是原生字符串。
            ValueError: 字符串格式非法；不接受 CSS 名称或短写。
        """
        if type(value) is not str:
            raise TypeError("颜色必须为十六进制字符串")
        if _re.fullmatch(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?", value) is None:
            raise ValueError("颜色必须为 #RRGGBB 或 #RRGGBBAA")
        rgba = value[1:] + ("FF" if len(value) == 7 else "")
        return cls(*(int(rgba[i : i + 2], 16) for i in (0, 2, 4, 6)))

    @classmethod
    def rgb(cls, red: int, green: int, blue: int, *, transparency: float = 0) -> Color:
        """以整数 RGB 和 0–100 透明度构造；0 不透明，100 全透明。

        透明度仅接受原生有限 int/float，错误类型抛 TypeError，越界抛 ValueError。
        alpha 按最接近字节量化，半值向上，不先舍入百分比。
        """
        return cls(red, green, blue, _alpha(transparency))

    def with_transparency(self, transparency: float) -> Color:
        """以 0–100 透明度替换 alpha 并返回新值，不修改原色、不叠乘。

        透明度与 rgb 使用相同范围、量化和异常契约。
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
        """标量在两端未预乘 RGBA 字节之间线性插值，区间外钳制到端点。

        Args:
            value: 有限原生 int/float，不接受 bool。
            lower: 有限下界，必须小于 upper。
            upper: 有限上界。
            lower_color: 下界 Color，不接受 None 或字符串。
            upper_color: 上界 Color。

        Returns:
            不可变 Color，各通道半字节向上量化；不修改两端颜色。

        Raises:
            TypeError: 数值或颜色类型非法。
            ValueError: 非有限值或上下界顺序非法。
        """
        for number in (value, lower, upper):
            if type(number) not in (int, float):
                raise TypeError("梯度值与边界必须为 Python int 或 float")
            try:
                valid = _isfinite(number)
            except OverflowError:
                valid = False
            if not valid:
                raise ValueError("梯度值与边界必须为有限数值")
        if lower >= upper:
            raise ValueError("梯度 lower 必须小于 upper")
        if not isinstance(lower_color, Color) or not isinstance(upper_color, Color):
            raise TypeError("梯度两端必须为 Color")
        if value <= lower:
            return lower_color
        if value >= upper:
            return upper_color
        # 异号极大值的 upper-lower 可溢出；同号使用原差值避免近邻精度损失。
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
        """由已量化 alpha 反算的 0–100 透明度，可能不等于原始百分比。"""
        return 100 * (255 - self.alpha) / 255

    def to_hex(self) -> str:
        """返回大写 #RRGGBBAA；全透明颜色仍保留 RGB，不转换为 None。"""
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
