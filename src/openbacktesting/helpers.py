"""Stateless helpers and compatibility with old object paths."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import contextmanager
from numbers import Number
from types import FunctionType

import pandas as pd


def _set_legacy_module(obj, module):
    """Preserve old qualified names used by pickle when moving definitions; do not create replacement classes."""
    original = obj.__module__
    obj.__module__ = module
    if isinstance(obj, type):
        for member in vars(obj).values():
            if isinstance(member, type) and member.__module__ == original:
                _set_legacy_module(member, module)
            if isinstance(member, (staticmethod, classmethod)):
                functions = (member.__func__,)
            elif isinstance(member, property):
                functions = (member.fget, member.fset, member.fdel)
            else:
                functions = (member, getattr(member, "func", None))
            for function in functions:
                if isinstance(function, FunctionType) and function.__module__ == original:
                    function.__module__ = module


def try_(lazy_func, default=None, exception=Exception):
    try:
        return lazy_func()
    except exception:
        return default


@contextmanager
def patch(obj, attr, newvalue):
    had_attr = hasattr(obj, attr)
    orig_value = getattr(obj, attr, None)
    setattr(obj, attr, newvalue)
    try:
        yield
    finally:
        if had_attr:
            setattr(obj, attr, orig_value)
        else:
            delattr(obj, attr)


def _as_str(value) -> str:
    if isinstance(value, (Number, str)):
        return str(value)
    if isinstance(value, pd.DataFrame):
        return "df"
    name = str(getattr(value, "name", "") or "")
    if name in ("Open", "High", "Low", "Close", "Volume"):
        return name[:1]
    if callable(value):
        name = getattr(value, "__name__", value.__class__.__name__).replace("<lambda>", "λ")
    if len(name) > 10:
        name = name[:9] + "…"
    return name


def _as_list(value) -> list:
    if isinstance(value, Sequence) and not isinstance(value, str):
        return list(value)
    return [value]


_set_legacy_module(try_, "openbacktesting._util")
_set_legacy_module(patch, "openbacktesting._util")
_set_legacy_module(_as_str, "openbacktesting._util")
_set_legacy_module(_as_list, "openbacktesting._util")
