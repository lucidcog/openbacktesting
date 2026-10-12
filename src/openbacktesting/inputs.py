"""Compatibility exports for the old inputs path; implemented in strategy.inputs."""

from openbacktesting.strategy.inputs import (
    _SAFE_INT,  # noqa: F401 — re-export the legacy entry point
    _UNSET,  # noqa: F401 — re-export the legacy entry point
    SCHEMA_VERSION,
    InputError,
    InputSpec,
    ResolvedInputs,
    _collect,  # noqa: F401 — re-export the legacy entry point
    _definitions,  # noqa: F401 — re-export the legacy entry point
    _fail,  # noqa: F401 — re-export the legacy entry point
    _make,  # noqa: F401 — re-export the legacy entry point
    _resolve,  # noqa: F401 — re-export the legacy entry point
    _scalar,  # noqa: F401 — re-export the legacy entry point
    _schema,  # noqa: F401 — re-export the legacy entry point
    _session,  # noqa: F401 — re-export the legacy entry point
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
