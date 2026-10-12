"""Fixed indicator bindings; third-party defaults are not OpenBacktesting public contracts."""

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
        raise ValueError("Duplicate indicator identity")
    return tuple(specs)


SPECS = load_specs()


def named_series(result, indicator, channel):
    """Each indicator file declares single-series semantics; values and index remain unchanged."""
    if result is None:
        return None
    if not isinstance(result, pd.Series):
        raise IndicatorError("output-contract", indicator, "A single-channel Series is required")
    return result.rename(channel)


def named_frame(result, indicator, channels):
    """Validate the provider's column set, then order and convert columns to canonical channels by explicit names."""
    if result is None:
        return None
    if (
        not isinstance(result, pd.DataFrame)
        or not result.columns.is_unique
        or set(result.columns) != set(channels)
    ):
        raise IndicatorError("output-contract", indicator, "Output columns do not match the fixed contract")
    if tuple(result.columns) != tuple(channels):
        result = result.loc[:, list(channels)]
    return result.rename(columns=channels)


def to_arrays(spec, result, index, parameters):
    if result is None:
        minimum = spec.history_required(parameters)
        if len(index) >= minimum:
            raise IndicatorError("output-contract", spec.id, "Backend returned no result")
        values = np.full((len(spec.outputs), len(index)), np.nan)
    else:
        if not isinstance(result, (pd.Series, pd.DataFrame)):
            raise IndicatorError("output-contract", spec.id, "Backend must return an indexed series or table")
        names = (result.name,) if isinstance(result, pd.Series) else tuple(result.columns)
        if names != spec.outputs:
            raise IndicatorError("output-contract", spec.id, "Canonical output names or order do not match")
        if not result.index.equals(index):
            raise IndicatorError("index-mismatch", spec.id, "Backend output index does not match")
        try:
            values = np.atleast_2d(result.to_numpy(dtype=float).T)
        except (TypeError, ValueError) as error:
            raise IndicatorError("output-contract", spec.id, "Backend output must be numeric") from error
        if values.shape != (len(spec.outputs), len(index)):
            raise IndicatorError("output-contract", spec.id, f"Invalid output shape: {values.shape}")
    valid = np.isfinite(values)
    if result is not None and "indicator_valid" in result.attrs:
        declared = np.asarray(result.attrs["indicator_valid"])
        if declared.dtype != np.dtype(bool) or declared.shape not in (values.shape, (len(index),)):
            raise IndicatorError("output-contract", spec.id, "Invalid validity mask shape or type")
        valid &= declared
    return values, valid
