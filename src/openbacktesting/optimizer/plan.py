"""有限参数域校验与稳定笛卡尔积，不执行用户策略。"""

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
        raise ValueError("optimizer: 范围需要整数或有限十进制字符串")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("optimizer: 无效十进制范围") from error
    if not number.is_finite() or not -324 <= number.as_tuple().exponent <= 308:
        raise ValueError("optimizer: 十进制范围超出支持精度")
    return Fraction(number)


def _domain(spec, domain):
    if isinstance(domain, Values):
        values = domain.values
        if not isinstance(values, (tuple, list)) or not 0 < len(values) <= MAX_DOMAIN:
            raise ValueError(f"optimizer: {spec.title} 域需要 1..{MAX_DOMAIN} 个候选")
        expression = {"values": []}
    elif isinstance(domain, Range):
        if spec.kind not in ("int", "float", "price"):
            raise ValueError(f"optimizer: {spec.title} 不支持数值范围")
        raw = (domain.start, domain.stop, domain.step)
        if spec.kind == "int" and any(type(v) is not int for v in raw):
            raise ValueError("optimizer: int 范围只接受整数")
        start, stop, step = map(_decimal, raw)
        if step <= 0 or start > stop:
            raise ValueError("optimizer: 范围必须升序且 step 为正")
        count = (stop - start) // step + 1
        if count > MAX_DOMAIN:
            raise ValueError("optimizer: 单维候选超过资源上限")
        convert = int if spec.kind == "int" else float
        values = [convert(start + i * step) for i in range(count)]
        expression = {"range": {"start": domain.start, "stop": domain.stop, "step": domain.step}}
    else:
        raise TypeError("optimizer: 搜索域必须是 Values 或 Range")
    encoded = []
    seen = set()
    for value in values:
        normalized = spec.normalize(value, wire=spec.kind == "enum" and type(value) is str)
        value = spec.encode(normalized)
        key = encode(0.0 if type(value) is float and value == 0 else value)
        if key in seen:
            raise ValueError(f"optimizer: {spec.title} 规范化候选重复")
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
    """冻结完整当前配置与选定维度；执行身份必须由宿主明确提供。

    Args:
        strategy_class: 已加载并声明 inputs 的策略类。
        search: 按唯一标题指定的非空搜索域。
        base_inputs: 既有标题请求；None 使用声明默认值。
        execution: 已规范化的代码、行情、配置和版本身份。
        constraint_id: 可选受信任约束的版本摘要，不序列化函数。
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
        raise ValueError("optimizer: search 必须为非空已声明标题映射")
    if not isinstance(execution, Mapping) or not execution:
        raise ValueError("optimizer: 缺少执行身份")
    if constraint_id is not None and (type(constraint_id) is not str or not constraint_id.strip()):
        raise ValueError("optimizer: constraint_id 必须非空")
    dimensions = [_domain(spec, search[title]) for title, spec in fields.items() if title in search]
    total = prod(len(d["values"]) for d in dimensions)
    if total > MAX_TOTAL:
        raise ValueError("optimizer: 组合数超出存储范围")
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
