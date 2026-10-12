"""Check English defaults while allowing exact, documented multilingual fixtures."""

from __future__ import annotations

import ast
import io
import json
import re
import token
import tokenize
from collections import Counter
from pathlib import Path

REGISTRY = "scripts/language-exceptions.json"
HAN = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
    r"\U00020000-\U0002fa1f\U00030000-\U000323af]"
)


def python_scopes(text):
    """Return lexical class/function ranges for literal exemption selectors."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return []
    scopes = []

    def visit(node, parents=()):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            parents += (node.name,)
            scopes.append((node.lineno, node.end_lineno, ".".join(parents)))
        for child in ast.iter_child_nodes(node):
            visit(child, parents)

    visit(tree)
    return scopes


def text_units(name, data):
    """Yield textual values and locations without executing repository code."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return
    if name.endswith(".py"):
        scopes = python_scopes(text)

        def selector_at(line):
            matches = [name for start, end, name in scopes if start <= line <= end]
            return max(matches, key=lambda name: len(name.split(".")), default=None)

        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
        except (tokenize.TokenError, IndentationError, SyntaxError):
            tokens = []
        for item in tokens:
            location = f"line {item.start[0]}"
            if item.type == tokenize.STRING:
                try:
                    value = ast.literal_eval(item.string)
                except (SyntaxError, ValueError):
                    # Before Python 3.12, tokenize exposes an entire f-string as STRING.
                    try:
                        expression = ast.parse(item.string, mode="eval").body
                    except SyntaxError:
                        expression = None
                    if isinstance(expression, ast.JoinedStr):
                        for part in expression.values:
                            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                                yield part.value, location, selector_at(item.start[0])
                        continue
                    value = item.string
                if isinstance(value, str):
                    yield value, location, selector_at(item.start[0])
            elif item.type == getattr(token, "FSTRING_MIDDLE", -1):
                # Decode escapes in literal f-string text without evaluating expressions.
                value = re.sub(
                    r"\\(?:u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|N\{[^}]+\})",
                    lambda match: ast.literal_eval('"' + match.group() + '"'),
                    item.string,
                )
                yield value, location, selector_at(item.start[0])
            elif item.type in (tokenize.COMMENT, tokenize.NAME, tokenize.ERRORTOKEN):
                yield item.string, location, None
        if tokens:
            return
    if name.endswith(".json"):
        try:
            value = json.loads(text)
        except ValueError:
            value = None
        if value is not None:
            def walk(obj, pointer=""):
                if isinstance(obj, str):
                    # Decode only valid embedded JSON, never arbitrary escape expressions.
                    while True:
                        try:
                            nested = json.loads(obj)
                        except ValueError:
                            break
                        if isinstance(nested, (dict, list)):
                            yield from walk(nested, pointer + "/<json>")
                            return
                        if not isinstance(nested, str) or nested == obj:
                            break
                        obj = nested
                    yield obj, pointer or "/", None
                elif isinstance(obj, dict):
                    for key, child in obj.items():
                        yield key, pointer + "/<key>", None
                        segment = key.replace("~", "~0").replace("/", "~1")
                        yield from walk(child, pointer + "/" + segment)
                elif isinstance(obj, list):
                    for index, child in enumerate(obj):
                        yield from walk(child, pointer + "/" + str(index))
            yield from walk(value)
            return
    for number, line in enumerate(text.splitlines(), 1):
        yield line, f"line {number}", None


def check_files(files, registry_data=None, *, subset=False):
    """Check normalized repository-relative paths and return actionable violations."""
    if registry_data is None:
        registry_data = files.get(REGISTRY)
    issues = []
    if registry_data is None:
        return [f"Missing language exception registry: {REGISTRY}"]
    try:
        registry = json.loads(registry_data)
        rules = registry["exceptions"]
        if not isinstance(rules, list):
            raise TypeError("exceptions must be a list")
    except (ValueError, TypeError, KeyError) as error:
        return [f"Invalid language exception registry: {error}"]
    expected = {}
    for rule in rules:
        if (
            not isinstance(rule, dict)
            or not isinstance(rule.get("path"), str)
            or not isinstance(rule.get("value"), str)
            or not isinstance(rule.get("reason"), str)
            or not rule["reason"].strip()
            or type(rule.get("count")) is not int
            or rule["count"] <= 0
            or Path(rule["path"]).is_absolute()
            or ".." in Path(rule["path"]).parts
            or any(character in rule["path"] for character in "*?[]")
            or HAN.search(rule["reason"])
            or (
                "selector" in rule
                and (
                    not rule["path"].endswith(".py")
                    or not isinstance(rule["selector"], str)
                    or not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", rule["selector"])
                    or HAN.search(rule["selector"])
                )
            )
        ):
            issues.append("Invalid language exemption: require an exact path, value, count, and English rationale")
            continue
        key = (rule["path"], rule["value"], rule.get("selector"))
        if key in expected:
            issues.append(f"Duplicate language exemption: {rule['path']}")
        expected[key] = rule["count"]
    seen = Counter()
    for name, data in files.items():
        for value, location, selector in text_units(name, data):
            if not HAN.search(value):
                continue
            # The registry describes exact exceptions; its values are data, not default copy.
            if name == REGISTRY and re.fullmatch(r"/exceptions/\d+/value", location):
                continue
            key = (name, value, selector)
            if key not in expected:
                key = (name, value, None)
            if key in expected:
                seen[key] += 1
            else:
                preview = value.replace("\n", "\\n")[:160]
                issues.append(f"{name}:{location}: unintended Chinese text: {preview!r}")
    for (name, value, selector), count in expected.items():
        # Distribution checks only evaluate exemptions for members they contain.
        if (not subset or name in files) and seen[(name, value, selector)] != count:
            issues.append(
                f"{name}: stale or overused language exemption for {value!r}"
                f"{f' in {selector}' if selector else ''}: "
                f"expected {count}, found {seen[(name, value, selector)]}"
            )
    return issues


def main():
    import argparse

    from check_package import project_files

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    files = {path.relative_to(root).as_posix(): path.read_bytes() for path in project_files(root)}
    issues = check_files(files)
    if issues:
        raise SystemExit("\n".join(issues))
    print(f"Language check passed: {len(files)} project files")


if __name__ == "__main__":
    main()
