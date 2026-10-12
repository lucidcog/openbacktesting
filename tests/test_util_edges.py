"""Exceptions, resource lifecycles, and platform dispatch contracts for utilities."""

import builtins
import importlib.util
import multiprocessing as mp
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from openbacktesting._util import SharedMemory, SharedMemoryManager, _Array, _Data, patch

import openbacktesting
from openbacktesting import _util
from openbacktesting.portfolio.stats import dummy_stats
from openbacktesting.test import GOOG


def test_patch_restores_missing_attribute_even_on_failure():
    obj = SimpleNamespace()
    with pytest.raises(ValueError, match="body"), patch(obj, "temporary", 42):
        assert obj.temporary == 42
        raise ValueError("body")
    assert not hasattr(obj, "temporary")


def test_array_deprecated_series_and_empty_float():
    array = _Array([1, 2], name="price", index=pd.RangeIndex(2))
    with pytest.warns(UserWarning, match="deprecated"):
        series = array.to_series()
    assert series.name == "price"
    assert series.index.equals(pd.RangeIndex(2))
    np.testing.assert_array_equal(series.to_numpy(), [1, 2])
    with pytest.raises(TypeError):
        float(array[:0])


def test_data_missing_column_and_visible_repr():
    data = _Data(GOOG.iloc[:3])
    data._set_length(1)
    with pytest.raises(AttributeError, match="Column 'missing' not in data"):
        _ = data.missing
    assert "i=0" in repr(data)
    assert str(GOOG.index[0]) in repr(data)
    assert f"Close={GOOG.Close.iloc[0]}" in repr(data)
    assert data.df.equals(GOOG.iloc[:1])


def test_optional_progress_dependency_falls_back_to_identity(monkeypatch):
    original_import = builtins.__import__

    def without_tqdm(name, *args, **kwargs):
        if name == "tqdm.auto":
            raise ImportError("optional tqdm unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_tqdm)
    spec = importlib.util.spec_from_file_location("openbacktesting._optional_util", _util.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sequence = [1, 2, 3]
    assert module._tqdm(sequence, total=3) is sequence


@pytest.mark.parametrize("method", [None, "fork", "spawn"])
def test_linux_pool_selects_fork_without_changing_real_start_method(monkeypatch, method):
    monkeypatch.setattr(sys, "platform", "linux")
    get_method = Mock(side_effect=[method, "fork"])
    set_method = Mock()
    pool = Mock(return_value=object())
    monkeypatch.setattr(mp, "get_start_method", get_method)
    monkeypatch.setattr(mp, "set_start_method", set_method)
    monkeypatch.setattr(mp, "Pool", pool)
    initializer = Mock()
    assert openbacktesting.Pool(2, initializer, (7,)) is pool.return_value
    pool.assert_called_once_with(2, initializer, (7,))
    if method == "fork":
        set_method.assert_not_called()
    else:
        set_method.assert_called_once_with("fork")


@pytest.mark.skipif(sys.platform == "win32", reason="Verify explicit POSIX unlink semantics")
def test_shared_memory_track_false_can_unlink_without_unregistering():
    shm = SharedMemory(create=True, size=8, track=False)
    try:
        name = shm.name
        shm.buf[:8] = b"12345678"
        shm.unlink()
        with pytest.raises(FileNotFoundError):
            SharedMemory(name=name, track=False)
    finally:
        shm.close()
        try:
            shm.unlink()
        except FileNotFoundError:
            pass


@pytest.mark.parametrize("operation", ["close", "unlink"])
def test_shared_memory_cleanup_reports_failure(operation):
    shm = Mock(_create=True, name="failed-segment")
    getattr(shm, operation).side_effect = OSError("cleanup failure")
    manager = SharedMemoryManager()
    manager._shms.append(shm)
    with (
        pytest.warns(ResourceWarning, match="Failed to unlink shared memory"),
        pytest.raises(OSError, match="cleanup failure"),
    ):
        manager.__exit__()
    shm.close.assert_called_once()
    if operation == "close":
        shm.unlink.assert_not_called()
    else:
        shm.unlink.assert_called_once()


def test_shared_memory_attachment_is_closed_but_not_unlinked():
    with SharedMemoryManager() as owner:
        original = owner.SharedMemory(create=True, size=8)
        name = original.name
        with SharedMemoryManager() as reader:
            attached = reader.SharedMemory(name=name, track=False)
            assert attached.name == name
        check = SharedMemory(name=name, track=False)
        check.close()
    with pytest.raises(FileNotFoundError):
        SharedMemory(name=name, track=False)


def test_stats_repr_includes_metrics_and_hides_internal_frames():
    stats = dummy_stats()
    rendered = repr(stats)
    assert "Equity Final [$]" in rendered
    assert "_trades" in rendered
    assert "--" in rendered
    assert stats["Equity Final [$]"] == stats.attrs["statistics_initial_equity"] == 1.0


@pytest.mark.parametrize("value, expected", [((1, 2), [1, 2]), ("ab", ["ab"]), (3, [3])])
def test_as_list_expands_sequences_without_splitting_strings(value, expected):
    from openbacktesting.helpers import _as_list

    assert _as_list(value) == expected


def test_array_dataframe_preserves_rows_columns_and_visible_index():
    index = pd.date_range("2025-01-01", periods=3)
    array = _Array([[1, 2, 3], [4, 5, 6]], name="value", index=index)
    expected = pd.DataFrame([[1, 4], [2, 5]], index=index[:2], columns=["value", "value"])
    pd.testing.assert_frame_equal(array[:, :2].df, expected)


def test_data_pip_is_cached_across_visible_length_changes():
    data = _Data(GOOG.iloc[:3])
    pip = data.pip
    assert pip == 0.01
    data._set_length(1)
    assert data.pip == pip


def test_new_python_uses_standard_shared_memory_class(monkeypatch):
    from multiprocessing import shared_memory

    from openbacktesting.simulation import parallel

    # Verify version selection only; a test double is not acceptance evidence for a new Python runtime.
    monkeypatch.setattr(sys, "version_info", (3, 13))
    spec = importlib.util.spec_from_file_location(
        "openbacktesting.simulation.parallel_future", parallel.__file__
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.SharedMemory is shared_memory.SharedMemory


@pytest.mark.skipif(sys.version_info >= (3, 13), reason="Only the legacy compatibility wrapper implements explicit unlink")
@pytest.mark.parametrize("posix, name", [(False, "segment"), (True, None)])
def test_legacy_unlink_ignores_non_posix_or_missing_name(monkeypatch, posix, name):
    from openbacktesting.simulation import parallel

    unlink = Mock()
    monkeypatch.setattr(parallel._mpshm, "_USE_POSIX", posix)
    monkeypatch.setattr(
        parallel._mpshm, "_posixshmem", SimpleNamespace(shm_unlink=unlink), raising=False
    )
    SharedMemory.unlink(SimpleNamespace(_name=name))
    unlink.assert_not_called()


def test_progress_parent_preserves_options_and_child_never_constructs_bar(monkeypatch):
    from openbacktesting import util

    sequence = [1, 2, 3]
    renderer = Mock(return_value=iter(sequence))
    monkeypatch.setattr(util, "_progress", renderer)
    monkeypatch.setattr(util, "parent_process", lambda: None)
    assert util._tqdm(sequence, total=3) is renderer.return_value
    renderer.assert_called_once_with(sequence, leave=False, total=3)
    renderer.reset_mock()
    util._tqdm(sequence, leave=True)
    renderer.assert_called_once_with(sequence, leave=True)
    renderer.reset_mock()
    monkeypatch.setattr(util, "parent_process", lambda: object())
    assert util._tqdm(sequence, disable=False) is sequence
    renderer.assert_not_called()  # disable=True still passes through tqdm.__new__ and touches the shared lock.


@pytest.mark.skipif("fork" not in mp.get_all_start_methods(), reason="Verify the progress lock inherited by fork")
def test_fork_backtest_survives_abandoned_progress_lock():
    import json
    import subprocess
    from pathlib import Path

    probe = Path(__file__).with_name("progress_fork_probe.py")
    result = subprocess.run(
        [sys.executable, str(probe)], capture_output=True, text=True, timeout=25, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout.splitlines()[-1])["trades"] == 1
