"""旧 inputs 路径的兼容导出；实现位于 strategy.inputs。"""

from openbacktesting.strategy.inputs import (
    _SAFE_INT,  # noqa: F401 — 旧入口重导出
    _UNSET,  # noqa: F401 — 旧入口重导出
    SCHEMA_VERSION,
    InputError,
    InputSpec,
    ResolvedInputs,
    _collect,  # noqa: F401 — 旧入口重导出
    _definitions,  # noqa: F401 — 旧入口重导出
    _fail,  # noqa: F401 — 旧入口重导出
    _make,  # noqa: F401 — 旧入口重导出
    _resolve,  # noqa: F401 — 旧入口重导出
    _scalar,  # noqa: F401 — 旧入口重导出
    _schema,  # noqa: F401 — 旧入口重导出
    _session,  # noqa: F401 — 旧入口重导出
    bool,
    color,
    describe,
    enum,
    float,
    int,
    price,
    request_for,
    resolve_native,
    resolve_request,
    session,
    string,
    time,
)

__all__ = [
    "SCHEMA_VERSION",
    "InputError",
    "InputSpec",
    "ResolvedInputs",
    "bool",
    "color",
    "describe",
    "enum",
    "float",
    "int",
    "price",
    "request_for",
    "resolve_native",
    "resolve_request",
    "session",
    "string",
    "time",
]
