from __future__ import annotations

from multiprocessing import parent_process

from openbacktesting.data.core import (  # noqa: F401
    _Array,
    _Data,
    _data_period,
    _Indicator,
    _indicator_warmup_nbars,
    _strategy_indicators,
)
from openbacktesting.helpers import _as_list, _as_str, patch, try_  # noqa: F401
from openbacktesting.simulation.parallel import (  # noqa: F401
    SharedMemory,
    SharedMemoryManager,
    _batch,
)

try:
    from tqdm.auto import tqdm as _progress
except ImportError:
    _progress = None


def _tqdm(seq, **kwargs):
    # fork may inherit a tqdm lock whose owner is gone; disable=True still acquires the lock during construction.
    # Child processes do not construct progress bars; the main process reports progress for outer tasks.
    if _progress is None or parent_process() is not None:
        return seq
    return _progress(seq, **{"leave": False, **kwargs})
