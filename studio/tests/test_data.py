import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from openbacktesting_studio.execution.data import load_data, read_snapshot, write_snapshot
from openbacktesting_studio.protocol import DataProfile


def profile(**changes):
    base = {
        "name": "Sample",
        "kind": "sample",
        "sample": "GOOG",
        "timezone": "UTC",
        "timeframe": {"unit": "day", "multiplier": 1},
        "instrument": {"symbol": "GOOG"},
    }
    return DataProfile.model_validate(base | changes)


def test_sample_data_context_and_empty_range(tmp_path):
    frame, context, instrument = load_data(profile(), {"directory": str(tmp_path)})
    assert context.timezone == "UTC" and instrument.symbol == "GOOG"
    assert str(frame.index.tz) == "UTC"
    with pytest.raises(ValueError, match="empty"):
        load_data(profile(start="2100-01-01T00:00:00Z"), {"directory": str(tmp_path)})


def test_csv_requires_explicit_time_and_preserves_custom_columns(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text(
        "Date,Open,High,Low,Close,Signal\n2026-01-01,10,11,9,10,1\n2026-01-02,10,11,9,10,2\n"
    )
    data = profile(kind="csv", sample=None, path="data.csv", timeColumn="Date")
    with pytest.raises(ValueError, match="sourceTimezone"):
        load_data(data, {"directory": str(tmp_path)})
    data.sourceTimezone = "UTC"
    frame, _, _ = load_data(data, {"directory": str(tmp_path)})
    assert list(frame.Signal) == [1, 2]
    path.write_text(path.read_text().replace("2026-01-02", "2026-01-01"))
    with pytest.raises(ValueError, match="unique"):
        load_data(data, {"directory": str(tmp_path)})


def test_lossless_snapshot_masks_dtype_precision_timezone_and_hash(tmp_path):
    frame = pd.DataFrame(
        {
            "Close": [1.2, np.nan, 2.3],
            "Integer": pd.array([2**60, None, 3], dtype="Int64"),
            "Flag": pd.array([True, None, False], dtype="boolean"),
            "Text": pd.array(["one", None, "three"], dtype="string"),
        },
        index=pd.date_range("2026-01-01", periods=3, tz="America/New_York"),
    )
    identity = write_snapshot(frame, tmp_path / "first")
    assert_frame_equal(read_snapshot(tmp_path / "first"), frame, check_freq=False)
    changed = frame.copy()
    changed.loc[changed.index[2], "Integer"] = 4
    assert write_snapshot(changed, tmp_path / "second") != identity
    (tmp_path / "first/column-0.npy").write_bytes(b"broken")
    with pytest.raises(ValueError, match="checksum"):
        read_snapshot(tmp_path / "first")


def test_object_columns_fail_without_stringification(tmp_path):
    frame = pd.DataFrame(
        {"Close": [10.0], "Object": [object()]},
        index=pd.date_range("2026-01-01", periods=1, tz="UTC"),
    )
    with pytest.raises(ValueError, match="object column"):
        write_snapshot(frame, tmp_path / "data")


@pytest.mark.parametrize(
    "name,unit,multiplier", [("GOOG", "day", 1), ("BTCUSD", "month", 1), ("EURUSD", "minute", 60)]
)
def test_explicit_fixture_recipes(tmp_path, name, unit, multiplier):
    frame, context, _ = load_data(
        profile(sample=name, timeframe={"unit": unit, "multiplier": multiplier}),
        {"directory": str(tmp_path)},
    )
    assert not frame.empty
    assert context.timeframe.multiplier == multiplier
    with pytest.raises(ValueError, match="requires timeframe"):
        load_data(
            profile(sample=name, timeframe={"unit": "second", "multiplier": 1}),
            {"directory": str(tmp_path)},
        )


def test_timezone_representation_does_not_change_actual_data_identity(tmp_path):
    frame, _, _ = load_data(profile(), {"directory": str(tmp_path)})
    changed = frame.tz_convert("America/New_York")
    assert write_snapshot(frame, tmp_path / "utc") == write_snapshot(changed, tmp_path / "local")


@pytest.mark.parametrize(
    "rows",
    [
        "2026-01-02,10,11,9,10\n2026-01-01,10,11,9,10\n",
        "2026-01-01,10,11,9,10\n2026-01-01,10,11,9,10\n",
    ],
)
def test_csv_rejects_unordered_and_duplicate_rows(tmp_path, rows):
    (tmp_path / "data.csv").write_text("Date,Open,High,Low,Close\n" + rows)
    with pytest.raises(ValueError, match="unique, and increasing"):
        load_data(
            profile(
                kind="csv", sample=None, path="data.csv", timeColumn="Date", sourceTimezone="UTC"
            ),
            {"directory": str(tmp_path)},
        )
