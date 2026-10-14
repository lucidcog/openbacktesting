"""Explicit market-data loading and lossless, non-pickle snapshots."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_float_dtype, is_integer_dtype

from openbacktesting_studio.protocol import DataProfile


def load_data(profile: DataProfile, snapshot):
    from openbacktesting import DataContext, Timeframe
    from openbacktesting.broker import InstrumentSpec
    from openbacktesting.data.timeframe import TimeframeUnit

    from openbacktesting_studio.execution.worker import load_module

    root = Path(snapshot["directory"])
    if profile.kind == "sample":
        from openbacktesting import test

        frame = getattr(test, profile.sample).copy(deep=True)
        # Recipes come from the bundled fixture declarations, never price inference.
        recipes = {"GOOG": ("day", 1), "BTCUSD": ("month", 1), "EURUSD": ("minute", 60)}
        if (profile.timeframe.unit, profile.timeframe.multiplier) != recipes[profile.sample]:
            raise ValueError(
                f"Bundled {profile.sample} requires timeframe {recipes[profile.sample]}"
            )
        if frame.index.tz is None:
            frame.index = frame.index.tz_localize("UTC")
    elif profile.kind == "csv":
        path = root / profile.path
        frame = pd.read_csv(path)
        if profile.timeColumn not in frame:
            raise ValueError("Configured time column is missing")
        time = frame.pop(profile.timeColumn)
        if profile.timeUnit:
            if not (is_float_dtype(time.dtype) or is_integer_dtype(time.dtype)):
                raise ValueError("Numeric time units require a numeric column")
            index = pd.DatetimeIndex(pd.to_datetime(time, unit=profile.timeUnit, utc=True))
        else:
            if is_integer_dtype(time.dtype) or is_float_dtype(time.dtype):
                raise ValueError("Numeric time columns require an explicit unit")
            index = pd.DatetimeIndex(pd.to_datetime(time))
            if index.tz is None:
                if not profile.sourceTimezone:
                    raise ValueError("Naive CSV time requires sourceTimezone")
                index = index.tz_localize(
                    profile.sourceTimezone, ambiguous="raise", nonexistent="raise"
                )
        frame.index = index
        if not set(profile.columns).issubset(frame.columns):
            raise ValueError("A mapped source column is missing")
        frame = frame.rename(columns=profile.columns)
    else:
        module = load_module(snapshot, profile.path)
        loader = getattr(module, profile.function)
        if not callable(loader):
            raise ValueError("Registered loader is not callable")
        frame = loader(**profile.parameters)
        if not isinstance(frame, pd.DataFrame):
            raise ValueError("Loader must return a pandas DataFrame")
        frame = frame.copy(deep=True)
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise ValueError("Market data requires a timezone-aware DatetimeIndex")
    if frame.index.hasnans or not frame.index.is_unique or not frame.index.is_monotonic_increasing:
        raise ValueError("Market times must be present, unique, and increasing")
    if not frame.columns.is_unique or not all(isinstance(column, str) for column in frame.columns):
        raise ValueError("Market columns must have unique string names")
    if not {"Open", "High", "Low", "Close"}.issubset(frame.columns):
        raise ValueError("Market data requires Open, High, Low, and Close columns")
    for boundary, lower in [(profile.start, True), (profile.end, False)]:
        if boundary is not None:
            timestamp = pd.Timestamp(boundary)
            if timestamp.tzinfo is None:
                raise ValueError("Date bounds require an explicit UTC offset")
            frame = (
                frame.loc[frame.index >= timestamp]
                if lower
                else frame.loc[frame.index <= timestamp]
            )
    if frame.empty:
        raise ValueError("The selected data interval is empty")
    context = DataContext(
        Timeframe(TimeframeUnit(profile.timeframe.unit), profile.timeframe.multiplier),
        profile.timezone,
    )
    frame.index = frame.index.tz_convert(profile.timezone)
    instrument = InstrumentSpec(**profile.instrument.model_dump())
    instrument.validate_data(frame)
    return frame, context, instrument


def write_snapshot(frame, target):
    """Store dtype plus primitive arrays and masks; reject arbitrary Python objects."""
    target = Path(target)
    target.mkdir(parents=True, exist_ok=False)
    index = frame.index.as_unit("ns")
    metadata = {
        "schemaVersion": 1,
        "timezone": str(index.tz),
        "indexName": index.name,
        "indexUnit": frame.index.unit,
        "columns": [],
        "files": {},
    }
    np.save(target / "index.npy", index.asi8, allow_pickle=False)
    for number, name in enumerate(frame.columns):
        series = frame[name]
        dtype = series.dtype
        stem = f"column-{number}"
        mask = series.isna().to_numpy(dtype=bool)
        np.save(target / f"{stem}-mask.npy", mask, allow_pickle=False)
        record = {"name": name, "dtype": str(dtype), "stem": stem}
        if dtype == object:
            raise ValueError(f"Unsupported object column: {name}; declare a primitive dtype")
        if isinstance(dtype, pd.StringDtype):
            record["kind"] = "string"
            record["storage"] = dtype.storage
            record["naValue"] = (
                "nan" if isinstance(getattr(dtype, "na_value", pd.NA), float) else "NA"
            )
            (target / f"{stem}.json").write_text(
                json.dumps([None if missing else value for value, missing in zip(series, mask)])
            )
        elif is_integer_dtype(dtype) or is_float_dtype(dtype) or is_bool_dtype(dtype):
            record["kind"] = "numeric"
            primitive = getattr(dtype, "numpy_dtype", dtype)
            values = series.to_numpy(dtype=primitive, na_value=0)
            np.save(target / f"{stem}.npy", values, allow_pickle=False)
        else:
            raise ValueError(f"Unsupported column dtype for {name}: {dtype}")
        metadata["columns"].append(record)
    for path in sorted(target.iterdir()):
        metadata["files"][path.name] = sha256(path.read_bytes()).hexdigest()
    encoded = json.dumps(metadata, sort_keys=True, allow_nan=False).encode()
    (target / "schema.json").write_bytes(encoded)
    # Absolute instants and values identify data independently of display/context timezone.
    identity = {
        key: value for key, value in metadata.items() if key not in {"timezone", "indexUnit"}
    }
    return sha256(json.dumps(identity, sort_keys=True, allow_nan=False).encode()).hexdigest()


def read_snapshot(target):
    target = Path(target)
    metadata = json.loads((target / "schema.json").read_text())
    if metadata["schemaVersion"] != 1:
        raise ValueError("Unsupported data snapshot version")
    for name, digest in metadata["files"].items():
        if Path(name).name != name or (target / name).is_symlink():
            raise ValueError("Invalid snapshot member")
        if sha256((target / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Data snapshot checksum mismatch")
    index = pd.to_datetime(np.load(target / "index.npy", allow_pickle=False), unit="ns", utc=True)
    index = index.tz_convert(metadata["timezone"]).as_unit(metadata["indexUnit"])
    index.name = metadata["indexName"]
    columns = {}
    for record in metadata["columns"]:
        stem = record["stem"]
        if not stem.startswith("column-") or not stem[7:].isdigit():
            raise ValueError("Invalid column member")
        mask = np.load(target / f"{stem}-mask.npy", allow_pickle=False)
        if record["kind"] == "string":
            options = {"storage": record["storage"]}
            if record["naValue"] == "nan":
                options["na_value"] = np.nan
            dtype = pd.StringDtype(**options)
            values = pd.array(json.loads((target / f"{stem}.json").read_text()), dtype=dtype)
        else:
            raw = np.load(target / f"{stem}.npy", allow_pickle=False)
            values = pd.array(raw, dtype=record["dtype"])
            if mask.any():
                values[mask] = (
                    pd.NA
                    if record["dtype"][0].isupper() or record["dtype"] == "boolean"
                    else np.nan
                )
        columns[record["name"]] = pd.Series(values, index=index)
    return pd.DataFrame(columns, index=index)
