"""与算法供应商无关的指标定义、不可变结果及游标视图。"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import isfinite

import numpy as np
import pandas as pd
from numpy.lib.mixins import NDArrayOperatorsMixin


class IndicatorError(ValueError):
    """稳定错误类别；detail 不充当程序分派接口。"""

    def __init__(self, code, indicator, detail, *, backend=None, parameter=None):
        self.code = code
        self.indicator = indicator
        self.backend = backend
        self.parameter = parameter
        super().__init__(f"{code}: {indicator}: {detail}")


def immutable(values, dtype=None):
    """以不可写 bytes 为底层，不能通过 setflags 恢复写权限。"""
    array = np.asarray(values, dtype=dtype)
    if array.dtype.hasobject:
        raise ValueError("指标数组不接受 object dtype")
    return np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(array.shape)


@dataclass
class IndicatorCursor:
    length: int
    phase: str = "init"


class IndicatorHandle(NDArrayOperatorsMixin):
    """时间维在最后；所有派生视图在读取时才应用游标和选择器。"""

    def __init__(
        self,
        values,
        *,
        name,
        index,
        cursor=None,
        valid=None,
        required=None,
        metadata=None,
        ready=None,
    ):
        self._values = immutable(values)
        self.name = name
        self._opts = {"index": index.copy(deep=True)}
        self._cursor = cursor or IndicatorCursor(self._values.shape[-1], "complete")
        self._selectors = ()
        self._valid = immutable(np.isfinite(self._values) if valid is None else valid, bool)
        self._required = (
            tuple(range(np.atleast_2d(self._values).shape[0]))
            if required is None
            else tuple(required)
        )
        self._metadata = deepcopy(metadata or {})
        self._ready = immutable(
            np.ones(self._values.shape[-1], dtype=bool) if ready is None else ready, bool
        )
        self._set_required(self._required)

    def _view(self):
        value = self._values[..., : self._cursor.length]
        for selector in self._selectors:
            value = value[selector]
        return value

    def _index(self):
        indices = np.broadcast_to(
            np.arange(self._cursor.length), self._values.shape[:-1] + (self._cursor.length,)
        )
        for selector in self._selectors:
            indices = indices[selector]
        return self._opts["index"][np.atleast_2d(indices)[0]]

    def __array__(self, dtype=None, copy=None):
        # 转换只保存当前可见快照；不会经 .base 暴露完整未来数组。
        if copy is False:
            raise ValueError("指标转换需要隔离快照，不能请求 copy=False")
        if copy is True:
            return np.array(self._view(), dtype=dtype, copy=True)
        return immutable(self._view(), dtype)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        if kwargs.get("out") is not None or method == "at":
            raise TypeError("指标只读；请先复制为数组再执行原地运算")
        values = [
            value._view() if isinstance(value, IndicatorHandle) else value for value in inputs
        ]
        return getattr(ufunc, method)(*values, **kwargs)

    def __getitem__(self, key):
        if isinstance(key, str):
            names = [self.name] if isinstance(self.name, str) else list(self.name)
            if key not in names:
                raise KeyError(key)
            key = names.index(key) if self.ndim == 2 else slice(None)
        value = self._view()[key]
        if not isinstance(value, np.ndarray):
            return value
        result = object.__new__(type(self))
        result.__dict__ = self.__dict__.copy()
        result._selectors = self._selectors + (key,)
        if self.ndim == 2 and isinstance(key, (int, np.integer)):
            result.name = self.name[key] if not isinstance(self.name, str) else self.name
        return result

    def __len__(self):
        return len(self._view())

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __bool__(self):
        return bool(self[-1])

    def __float__(self):
        return float(self[-1])

    @property
    def shape(self):
        """当前可见前缀的形状；多输出的时间轴位于最后。"""
        return self._view().shape

    @property
    def ndim(self):
        """输出维数；单通道为 1，多通道为 2。"""
        return self._view().ndim

    @property
    def dtype(self):
        """底层只读数值缓冲区的数据类型。"""
        return self._values.dtype

    @property
    def s(self):
        """首通道当前前缀的 pandas Series 副本；保存后不随游标增长。"""
        return pd.Series(
            np.atleast_2d(np.asarray(self))[0].copy(), index=self._index(), name=self.name
        )

    @property
    def df(self):
        """全部通道当前前缀的 pandas DataFrame 副本。"""
        value = np.atleast_2d(np.asarray(self))
        names = self.name if isinstance(self.name, (list, tuple)) else [self.name] * len(value)
        return pd.DataFrame(value.T.copy(), index=self._index(), columns=names)

    def copy(self):
        """返回当前前缀的可写 NumPy 副本，不再跟随游标。"""
        return np.array(self, copy=True)

    def astype(self, dtype):
        """按 dtype 转换当前前缀为 NumPy 数组快照，不保留动态游标。"""
        return np.asarray(self, dtype=dtype)

    @property
    def valid(self):
        """当前前缀各通道的只读有效性掩码；False 不表示数值零。"""
        value = self._valid[..., : self._cursor.length]
        for selector in self._selectors:
            value = value[selector]
        return immutable(value)

    @property
    def ready(self):
        """当前前缀最低历史条件是否满足的只读掩码。"""
        return immutable(self._ready[: self._cursor.length])

    @property
    def metadata(self):
        """返回来源元数据的深拷贝，修改不影响登记结果。"""
        return deepcopy(self._metadata)

    def _set_required(self, required):
        self._required = tuple(required)
        self._gating = immutable(
            self._ready & np.atleast_2d(self._valid)[list(self._required)].all(axis=0)
        )

    def ready_at(self, bar):
        """查询必要输出与最低历史条件的就绪状态；不控制策略回调。"""
        return bool(self._gating[bar])

    def first_ready(self):
        """返回必要输出最早就绪位置；从未就绪时为总长度，不控制回调。"""
        positions = np.flatnonzero(self._gating)
        return int(positions[0]) if positions.size else len(self._gating)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._values = immutable(self._values)
        self._valid = immutable(self._valid, bool)
        self._ready = immutable(self._ready, bool)
        self._gating = immutable(self._gating, bool)


@dataclass(frozen=True)
class Parameter:
    """指标参数定义：default/kind 为默认值与类型，minimum/maximum/choices 限定允许值。"""

    default: object
    kind: str
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple = ()

    def normalize(self, value, indicator, name):
        """校验 value 的类型、边界和 choices 并转换为原生类型；失败抛 IndicatorError，indicator/name 用于定位。"""
        types = {
            "int": (int, np.integer),
            "float": (int, float, np.integer, np.floating),
            "bool": (bool,),
            "str": (str,),
        }
        valid = isinstance(value, types[self.kind])
        if self.kind in ("int", "float"):
            valid = valid and not isinstance(value, (bool, np.bool_))
            if valid:
                try:
                    valid = isfinite(value)
                except OverflowError:
                    valid = False
        if valid and self.minimum is not None:
            valid = value >= self.minimum
        if valid and self.maximum is not None:
            valid = value <= self.maximum
        if valid and self.choices:
            valid = value in self.choices
        if not valid:
            raise IndicatorError(
                "invalid-parameter", indicator, f"{name}: {value!r}", parameter=name
            )
        return {"int": int, "float": float, "bool": bool, "str": str}[self.kind](value)


@dataclass(frozen=True)
class IndicatorSpec:
    """已审核指标定义；字段含身份、输入/输出、参数域、后端、有效性与历史要求。"""

    id: str
    source: str
    category: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    parameters: tuple[tuple[str, Parameter], ...] = ()
    version: str = "1"
    status: str = "available"
    reason: str = ""
    required: tuple[str, ...] | None = None
    fixed: tuple[tuple[str, object], ...] = ()

    minimum: int = 1
    windows: tuple[str, ...] = ()
    dtype: str = "float64"
    unit: str = "native"
    missing_policy: str = "native-v1"
    causal: bool = True

    aliases: tuple[tuple[str, str], ...] = ()
    history_sum: tuple = ()
    history_offset: int = 0
    kind: str = "indicator"
    input_args: tuple[str, ...] = ()
    input_defaults: tuple[tuple[str, str], ...] = ()
    default_backend: str = "pandas-ta-classic.native"
    validity: str = "current-inputs"

    def history_required(self, parameters):
        """根据规范化 parameters 计算最低历史长度；不代表每个输出已经有效。"""
        return max(
            [
                self.minimum,
                *(parameters[name] for name in self.windows),
                self.history_offset
                + sum(parameters[name] * coefficient for name, coefficient in self.history_sum),
            ]
        )

    def __post_init__(self):
        if not self.id or not self.outputs or len(set(self.outputs)) != len(self.outputs):
            raise ValueError("指标身份和唯一输出不能为空")
        aliases = [name for name, _ in self.aliases]
        if len(set(aliases)) != len(aliases) or any(
            name in self.outputs or target not in self.outputs for name, target in self.aliases
        ):
            raise ValueError("输出别名重复或目标非法")
        if self.kind not in ("indicator", "utility", "pattern") or self.validity not in (
            "current-inputs",
            "output",
        ):
            raise ValueError("未知指标种类或有效性政策")
        if len(set(self.input_args)) != len(self.input_args) or not set(self.input_args) <= set(
            self.inputs
        ):
            raise ValueError("公开输入参数必须唯一且已声明")
        defaults = dict(self.input_defaults)
        if len(defaults) != len(self.input_defaults) or not defaults.keys() <= set(self.inputs):
            raise ValueError("默认输入必须唯一且已声明")
        names = [name for name, _ in self.parameters]
        if len(set(names)) != len(names) or set(names) & {"inputs", "backend", "required_outputs"}:
            raise ValueError("参数重复或占用执行选项")
        if self.required is not None and not set(self.required) <= set(self.outputs):
            raise ValueError("必要输出未在定义中声明")

    def normalize(self, parameters):
        """校验 parameters 映射，填充目录默认值并验证参数关系；非法值抛 IndicatorError。"""
        definitions = dict(self.parameters)
        unknown = parameters.keys() - definitions.keys()
        if unknown:
            raise IndicatorError("invalid-parameter", self.id, f"未知参数: {sorted(unknown)}")
        values = {
            name: rule.normalize(parameters.get(name, rule.default), self.id, name)
            for name, rule in self.parameters
        }
        if "fast" in values and "slow" in values and values["fast"] >= values["slow"]:
            raise IndicatorError("invalid-parameter", self.id, "fast 必须小于 slow")
        if "ddof" in values and "length" in values and values["ddof"] >= values["length"]:
            raise IndicatorError("invalid-parameter", self.id, "ddof 必须小于 length")
        for lower, upper in (("minperiod", "maxperiod"), ("slowlimit", "fastlimit")):
            if lower in values and upper in values and values[lower] >= values[upper]:
                raise IndicatorError("invalid-parameter", self.id, f"{lower} 必须小于 {upper}")
        if "kc_scalar_wide" in values and not (
            values["kc_scalar_wide"] > values["kc_scalar_normal"] > values["kc_scalar_narrow"]
        ):
            raise IndicatorError(
                "invalid-parameter", self.id, "KC 系数必须满足 wide > normal > narrow"
            )
        if self.id == "ta.frama" and values["length"] % 2:
            raise IndicatorError("invalid-parameter", self.id, "length 必须为偶数")
        return values
