"""Native parallel batches and shared-memory lifecycle."""

from __future__ import annotations

import os
import sys
import warnings
from itertools import chain
from multiprocessing import resource_tracker as _mprt
from multiprocessing import shared_memory as _mpshm
from threading import Lock

import numpy as np
import pandas as pd

from openbacktesting.helpers import _set_legacy_module, patch

if sys.version_info >= (3, 13):
    SharedMemory = _mpshm.SharedMemory
else:

    class SharedMemory(_mpshm.SharedMemory):
        # From https://github.com/python/cpython/issues/82300#issuecomment-2169035092
        __lock = Lock()

        def __init__(self, *args, track: bool = True, **kwargs):
            self._track = track
            if track:
                return super().__init__(*args, **kwargs)  # noqa: PLE0101 — preserve the shared-memory initialization retry return
            with self.__lock, patch(_mprt, "register", lambda *a, **kw: None):
                super().__init__(*args, **kwargs)

        def unlink(self):
            if _mpshm._USE_POSIX and self._name:
                _mpshm._posixshmem.shm_unlink(self._name)
                if self._track:
                    _mprt.unregister(self._name, "shared_memory")


def _batch(seq):
    # XXX: Replace with itertools.batched
    n = np.clip(int(len(seq) // (os.cpu_count() or 1)), 1, 300)
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


class SharedMemoryManager:
    """
    A simple shared memory contextmanager based on
    https://docs.python.org/3/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.SharedMemory
    """

    def __init__(self, create=False) -> None:
        self._shms: list[SharedMemory] = []
        self.__create = create

    def SharedMemory(self, *, name=None, create=False, size=0, track=True):
        shm = SharedMemory(name=name, create=create, size=size, track=track)
        shm._create = create
        # Essential to keep refs on Windows
        # https://stackoverflow.com/questions/74193377/filenotfounderror-when-passing-a-shared-memory-to-a-new-process#comment130999060_74194875
        self._shms.append(shm)
        return shm

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        failures = []
        for shm in self._shms:
            try:
                shm.close()
                if shm._create:
                    shm.unlink()
            except Exception as error:  # noqa: BLE001 — release each segment, then re-raise the first error
                failures.append(error)
                warnings.warn(
                    f"Failed to unlink shared memory {shm.name!r}",
                    category=ResourceWarning,
                    stacklevel=2,
                )
        if failures:
            raise failures[0]

    def arr2shm(self, vals):
        """Array to shared memory. Returns (shm_name, shape, dtype) used for restore."""
        assert vals.ndim == 1, (vals.ndim, vals.shape, vals)
        # Not `vals.nbytes`; lazy indexes (e.g. RangeIndex) report their own,
        # constant size rather than that of the array they materialize into
        shm = self.SharedMemory(size=vals.size * vals.dtype.base.itemsize, create=True)
        buf = np.ndarray(vals.shape, dtype=vals.dtype.base, buffer=shm.buf)
        if isinstance(vals.dtype, pd.DatetimeTZDtype):
            # Preserve absolute instants at their original precision in both index and columns; do not lose offsets for repeated DST hours.
            buf.view("i8")[:] = vals.array.asi8
        else:
            buf[:] = vals
        return shm.name, vals.shape, vals.dtype

    def df2shm(self, df):
        return tuple(
            (
                (column, *self.arr2shm(values))
                for column, values in chain([(self._DF_INDEX_COL, df.index)], df.items())
            )
        )

    @staticmethod
    def shm2s(shm, shape, dtype) -> pd.Series:
        arr = np.ndarray(shape, dtype=dtype.base, buffer=shm.buf)
        arr.setflags(write=False)
        if isinstance(dtype, pd.DatetimeTZDtype):
            arr = pd.DatetimeIndex(arr).tz_localize("UTC").tz_convert(dtype.tz)
        return pd.Series(arr, dtype=dtype, copy=False)

    _DF_INDEX_COL = "__bt_index"

    @staticmethod
    def shm2df(data_shm):
        shm = []
        try:
            for _, name, _, _ in data_shm:
                shm.append(SharedMemory(name=name, create=False, track=False))
            df = pd.DataFrame(
                {
                    col: SharedMemoryManager.shm2s(handle, shape, dtype)
                    for handle, (col, _, shape, dtype) in zip(shm, data_shm)
                },
                copy=False,
            )
            df.set_index(SharedMemoryManager._DF_INDEX_COL, drop=True, inplace=True)
            # Result statistics retain the market-data index; it must survive independently after the mapping closes.
            df.index = df.index.copy(deep=True)
            df.index.name = None
            return df, shm
        except BaseException:
            for handle in shm:
                handle.close()
            raise


_set_legacy_module(_batch, "openbacktesting._util")
_set_legacy_module(SharedMemoryManager, "openbacktesting._util")

if sys.version_info < (3, 13):
    _set_legacy_module(SharedMemory, "openbacktesting._util")
