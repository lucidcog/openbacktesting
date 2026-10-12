"""固定指标绑定；第三方默认值不充当 OpenBacktesting 的公共契约。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .types import IndicatorError, IndicatorSpec, Parameter


def load_specs():
    import json
    from importlib.resources import files

    rows = json.loads(files("openbacktesting.indicators").joinpath("catalog.json").read_text())[
        "entries"
    ]
    specs = []
    for row in rows:
        row = row.copy()
        del row["test"]
        row["parameters"] = tuple(
            (name, Parameter(**(rule | {"choices": tuple(rule.get("choices", ()))})))
            for name, rule in row["parameters"].items()
        )
        row["fixed"] = tuple(row["fixed"].items())
        row["aliases"] = tuple(row.get("aliases", {}).items())
        row["input_args"] = tuple(row.get("input_args", ()))
        row["input_defaults"] = tuple(row.get("input_defaults", {}).items())
        row["history_sum"] = tuple(tuple(term) for term in row.get("history_sum", ()))
        for key in ("inputs", "outputs", "windows"):
            row[key] = tuple(row[key])
        if row["required"] is not None:
            row["required"] = tuple(row["required"])
        specs.append(IndicatorSpec(**row))
    if len({spec.id for spec in specs}) != len(specs):
        raise ValueError("指标身份重复")
    return tuple(specs)


SPECS = load_specs()


def named_series(result, indicator, channel):
    """单序列的语义由对应指标文件声明；不更改值和索引。"""
    if result is None:
        return None
    if not isinstance(result, pd.Series):
        raise IndicatorError("output-contract", indicator, "要求单通道 Series")
    return result.rename(channel)


def named_frame(result, indicator, channels):
    """校验供应商列集合，再按明确名称排列和转换为规范通道。"""
    if result is None:
        return None
    if (
        not isinstance(result, pd.DataFrame)
        or not result.columns.is_unique
        or set(result.columns) != set(channels)
    ):
        raise IndicatorError("output-contract", indicator, "输出列不符合固定契约")
    if tuple(result.columns) != tuple(channels):
        result = result.loc[:, list(channels)]
    return result.rename(columns=channels)


def to_arrays(spec, result, index, parameters):
    if result is None:
        minimum = spec.history_required(parameters)
        if len(index) >= minimum:
            raise IndicatorError("output-contract", spec.id, "后端未返回结果")
        values = np.full((len(spec.outputs), len(index)), np.nan)
    else:
        if not isinstance(result, (pd.Series, pd.DataFrame)):
            raise IndicatorError("output-contract", spec.id, "后端必须返回带索引的序列或表")
        names = (result.name,) if isinstance(result, pd.Series) else tuple(result.columns)
        if names != spec.outputs:
            raise IndicatorError("output-contract", spec.id, "规范输出名称或顺序不一致")
        if not result.index.equals(index):
            raise IndicatorError("index-mismatch", spec.id, "后端输出索引不一致")
        try:
            values = np.atleast_2d(result.to_numpy(dtype=float).T)
        except (TypeError, ValueError) as error:
            raise IndicatorError("output-contract", spec.id, "后端输出必须为数值") from error
        if values.shape != (len(spec.outputs), len(index)):
            raise IndicatorError("output-contract", spec.id, f"输出形状错误: {values.shape}")
    valid = np.isfinite(values)
    if result is not None and "indicator_valid" in result.attrs:
        declared = np.asarray(result.attrs["indicator_valid"])
        if declared.dtype != np.dtype(bool) or declared.shape not in (values.shape, (len(index),)):
            raise IndicatorError("output-contract", spec.id, "有效掩码形状或类型非法")
        valid &= declared
    return values, valid
