"""每次历史运行独立的策略日志；不连接 Python 全局 logging 或输出流。"""

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
            raise RuntimeError("策略日志会话已经结束")
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
    """策略的只读日志句柄，通过 self.log 使用，不需要作者构造。

    活动作者回调内可记录字符串；error 仅表示级别，不中止回测。
    自动记录实际调用文件与行号，结束后调用抛 RuntimeError。
    """

    def __init__(self, collector: _Collector):
        self._collector = collector

    def info(self, message: str) -> None:
        """记录普通信息，保留空字符串、中文和换行。"""
        self._write("info", message)

    def warning(self, message: str) -> None:
        """记录警告信息，不改变策略执行。"""
        self._write("warning", message)

    def error(self, message: str) -> None:
        """记录错误级别信息；需要中止策略时由作者显式 raise。"""
        self._write("error", message)

    def _write(self, level, message):
        if not isinstance(message, str):
            raise TypeError("策略日志 message 必须为字符串")
        collector = self._collector
        if collector._context is None:
            raise RuntimeError("策略日志只能在活动作者回调内写入")
        if not collector.enabled:
            return
        source_file, source_line = None, None
        frame = _currentframe()
        caller = None
        try:
            # 固定跳过本函数和三级公开方法，不扫描作者的辅助函数。
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
    """宿主持有的单次运行日志，通过 runtime.run(..., logs=session) 注入。

    顺序重用会在策略发现前清空记录；同一会话不能同时用于多个运行。
    成功或异常退出后均可查询，返回列表和字典副本，不持有作者栈帧。
    """

    def __init__(self):
        self._collector = _Collector()
        self._lock = _Lock()

    def get_logs(self) -> list[dict[str, str | int | None]]:
        """返回本次运行全部日志的独立副本；首次运行前为空列表。"""
        return self._collector.snapshot()

    @_contextmanager
    def _capture(self):
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("RunLogs 已被其他运行占用")
        try:
            self._collector = _Collector()
            yield
        finally:
            self._collector.close()
            self._lock.release()
