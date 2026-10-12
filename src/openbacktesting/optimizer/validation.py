"""从唯一生成模式验证 Portfolio，独立内核不依赖协议包。"""

import json
from functools import lru_cache
from pathlib import Path

from openbacktesting.optimizer._semantics import check_portfolio
from openbacktesting.optimizer.models import encode


@lru_cache(maxsize=1)
def _schema():
    return json.loads(Path(__file__).with_name("portfolio-result.schema.json").read_text())


def _valid(value, schema):
    if "$ref" in schema:
        return _valid(value, _schema()["$defs"][schema["$ref"].rsplit("/", 1)[1]])
    for key in ("anyOf", "oneOf"):
        if key in schema:
            count = sum(_valid(value, child) for child in schema[key])
            if not (count == 1 if key == "oneOf" else count > 0):
                return False
    if "const" in schema and value != schema["const"]:
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    kind = {
        dict: "object",
        list: "array",
        str: "string",
        bool: "boolean",
        int: "integer",
        float: "number",
        type(None): "null",
    }[type(value)]
    types = schema.get("type", [kind])
    types = [types] if isinstance(types, str) else types
    if kind not in types and not (kind == "integer" and "number" in types):
        return False
    if isinstance(value, dict):
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties", {})
        if not set(schema.get("required", ())).issubset(value):
            return False
        for key, item in value.items():
            if key not in props and extra is False:
                return False
            if not _valid(item, props.get(key, extra)):
                return False
    if isinstance(value, list):
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", len(value)):
            return False
        if not all(_valid(item, schema.get("items", {})) for item in value):
            return False
    return True


def validate_report(report):
    encode(report)
    if not _valid(report, _schema()):
        raise ValueError("optimizer: Portfolio 结构或版本无效")
    check_portfolio(report)
    return report
