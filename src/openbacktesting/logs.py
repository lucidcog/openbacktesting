"""Independent strategy logs for each historical run; no connection to global Python logging or output streams."""

from contextlib import contextmanager as _contextmanager
from datetime import UTC
from datetime import datetime as _datetime
from inspect import currentframe as _currentframe
from threading import Lock as _Lock
from typing import NamedTuple as _NamedTuple


class _Record(_NamedTuple):
    sequence: int
    level: str
    message: str
    phase: str
    bar_index: int | None
    bar_time: str | None
    time_kind: str
    recorded_at: str
    source_file: str | None
    source_line: int | None


class _Collector:
    def __init__(self, *, enabled=True):
        self.enabled = enabled
        self._records: list[_Record] = []
        self._context = None
        self._closed = False

    @_contextmanager
    def phase(self, phase, bar_index=None, bar_time=None, time_kind="none"):
        if self._closed:
            raise RuntimeError("Strategy log session has ended")
        self._context = (phase, bar_index, bar_time, time_kind)
        try:
            yield
        finally:
            self._context = None

    def close(self):
        self._closed = True
        self._context = None

    def snapshot(self) -> list[dict[str, str | int | None]]:
        return [record._asdict() for record in self._records]


class StrategyLog:
    """Read-only strategy log handle, accessed through self.log without author construction.

    Record strings inside active author callbacks; error denotes only a level and does not stop the backtest.
    Automatically record the actual calling file and line; calls after termination raise RuntimeError.
    """

    def __init__(self, collector: _Collector):
        self._collector = collector

    def info(self, message: str) -> None:
        """Record informational messages, preserving empty strings, Chinese text, and newlines."""
        self._write("info", message)

    def warning(self, message: str) -> None:
        """Record warning messages without changing strategy execution."""
        self._write("warning", message)

    def error(self, message: str) -> None:
        """Record error-level messages; authors must explicitly raise to stop the strategy."""
        self._write("error", message)

    def _write(self, level, message):
        if not isinstance(message, str):
            raise TypeError("Strategy log message must be a string")
        collector = self._collector
        if collector._context is None:
            raise RuntimeError("Strategy logs can only be written inside active author callbacks")
        if not collector.enabled:
            return
        source_file, source_line = None, None
        frame = _currentframe()
        caller = None
        try:
            # Skip this function and the three public level methods explicitly; do not scan author helper functions.
            caller = frame.f_back if frame is not None else None
            caller = caller.f_back if caller is not None else None
            if caller is not None:
                filename, lineno = caller.f_code.co_filename, caller.f_lineno
                if filename and lineno > 0:
                    source_file, source_line = filename, lineno
        finally:
            del frame, caller
        collector._records.append(
            _Record(
                len(collector._records) + 1,
                level,
                message,
                *collector._context,
                _datetime.now(UTC).isoformat(timespec="microseconds"),
                source_file,
                source_line,
            )
        )


class RunLogs:
    """Host-owned single-run log session, injected through runtime.run(..., logs=session).

    Sequential reuse clears records before strategy discovery; a session cannot serve concurrent runs.
    Queryable after success or exceptional exit; returns list and dictionary copies without holding author stack frames.
    """

    def __init__(self):
        self._collector = _Collector()
        self._lock = _Lock()

    def get_logs(self) -> list[dict[str, str | int | None]]:
        """Return an independent copy of all logs from this run; an empty list before the first run."""
        return self._collector.snapshot()

    @_contextmanager
    def _capture(self):
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("RunLogs is already occupied by another run")
        try:
            self._collector = _Collector()
            yield
        finally:
            self._collector.close()
            self._lock.release()
