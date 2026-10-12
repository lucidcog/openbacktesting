"""Finite parameter-domain validation and stable Cartesian products without executing user strategies."""

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from itertools import product
from math import prod

from openbacktesting.optimizer.models import Plan, Range, Values, encode
from openbacktesting.strategy.inputs import _definitions, describe, resolve_request

MAX_DOMAIN = 100_000
MAX_TOTAL = 2**63 - 1


def _decimal(value):
    if type(value) not in (str, int) or len(str(value)) > 128:
        raise ValueError("optimizer: ranges require integers or finite decimal strings")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("optimizer: invalid decimal range") from error
    if not number.is_finite() or not -324 <= number.as_tuple().exponent <= 308:
        raise ValueError("optimizer: decimal range exceeds supported precision")
    return Fraction(number)


def _domain(spec, domain):
    if isinstance(domain, Values):
        values = domain.values
        if not isinstance(values, (tuple, list)) or not 0 < len(values) <= MAX_DOMAIN:
            raise ValueError(f"optimizer: {spec.title} domain requires 1..{MAX_DOMAIN} candidates")
        expression = {"values": []}
    elif isinstance(domain, Range):
        if spec.kind not in ("int", "float", "price"):
            raise ValueError(f"optimizer: {spec.title} does not support numeric ranges")
        raw = (domain.start, domain.stop, domain.step)
        if spec.kind == "int" and any(type(v) is not int for v in raw):
            raise ValueError("optimizer: int ranges accept only integers")
        start, stop, step = map(_decimal, raw)
        if step <= 0 or start > stop:
            raise ValueError("optimizer: range must be ascending with a positive step")
        count = (stop - start) // step + 1
        if count > MAX_DOMAIN:
            raise ValueError("optimizer: single-dimension candidates exceed the resource limit")
        convert = int if spec.kind == "int" else float
        values = [convert(start + i * step) for i in range(count)]
        expression = {"range": {"start": domain.start, "stop": domain.stop, "step": domain.step}}
    else:
        raise TypeError("optimizer: search domain must be Values or Range")
    encoded = []
    seen = set()
    for value in values:
        normalized = spec.normalize(value, wire=spec.kind == "enum" and type(value) is str)
        value = spec.encode(normalized)
        key = encode(0.0 if type(value) is float and value == 0 else value)
        if key in seen:
            raise ValueError(f"optimizer: {spec.title} Duplicate normalized candidates")
        seen.add(key)
        encoded.append(value)
    if "values" in expression:
        expression["values"] = encoded
    return {"title": spec.title, "values": encoded, "expression": expression}


def plan(
    strategy_class,
    search: Mapping[str, Values | Range],
    *,
    base_inputs=None,
    execution: Mapping,
    constraint_id: str | None = None,
) -> Plan:
    """Freeze complete current configuration and selected dimensions; the host must explicitly supply execution identity.

    Args:
        strategy_class: Loaded strategy class declaring inputs.
        search: Nonempty search domains keyed by unique titles.
        base_inputs: Existing title-based request; None uses declared defaults.
        execution: Normalized code, market-data, configuration, and version identity.
        constraint_id: Optional version digest of a trusted constraint; the function is not serialized.
    """
    description = describe(strategy_class)
    request = (
        base_inputs
        if base_inputs is not None
        else {
            "schemaVersion": description["schemaVersion"],
            "schemaHash": description["schemaHash"],
            "values": {},
        }
    )
    resolved = resolve_request(strategy_class, request).snapshot()
    resolved.pop("overriddenTitles")
    fields = {spec.title: spec for spec in _definitions(strategy_class).values()}
    if not isinstance(search, Mapping) or not search or set(search) - fields.keys():
        raise ValueError("optimizer: search must be a nonempty mapping of declared titles")
    if not isinstance(execution, Mapping) or not execution:
        raise ValueError("optimizer: execution identity is missing")
    if constraint_id is not None and (type(constraint_id) is not str or not constraint_id.strip()):
        raise ValueError("optimizer: constraint_id must not be empty")
    dimensions = [_domain(spec, search[title]) for title, spec in fields.items() if title in search]
    total = prod(len(d["values"]) for d in dimensions)
    if total > MAX_TOTAL:
        raise ValueError("optimizer: combination count exceeds the storage range")
    return Plan(
        encode(
            {
                "version": 1,
                "inputs": resolved,
                "dimensions": dimensions,
                "total": total,
                "execution": dict(execution),
                "constraintId": constraint_id,
                "artifacts": "portfolio",
            }
        )
    )


def combinations(plan_value):
    source = plan_value.snapshot()
    dimensions = source["dimensions"]
    for ordinal, values in enumerate(product(*(d["values"] for d in dimensions))):
        request = source["inputs"] | {
            "values": source["inputs"]["values"]
            | dict(zip((d["title"] for d in dimensions), values, strict=True))
        }
        yield ordinal, request
