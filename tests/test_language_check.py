"""Regression coverage for decoded copy, exact exceptions, and distribution scope."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("language_check", ROOT / "scripts/check_language.py")
LANGUAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LANGUAGE)
sys.modules["check_language"] = LANGUAGE
COPY = chr(0x4E2D) + chr(0x6587)


def registry(*rules):
    return json.dumps({"exceptions": list(rules)}, ensure_ascii=False).encode()


def rule(path="tests/fixture.py", value=COPY, count=1):
    return {"path": path, "value": value, "count": count, "reason": "Multilingual round-trip fixture"}


def check(files, *rules):
    return LANGUAGE.check_files(files, registry(*rules))


def test_literal_and_escaped_python_and_json_copy():
    for data in (f'value = "{COPY}"', r'value = "\u4e2d\u6587"'):
        assert "unintended Chinese text" in check({"source.py": data.encode()})[0]
    for data in (json.dumps({"name": COPY}, ensure_ascii=False), json.dumps({"name": COPY})):
        assert "/name" in check({"data.json": data.encode()})[0]
    assert check({"guide.md": COPY.encode()})
    assert not check({"guide.md": "Math: α ≥ 0; résumé".encode()})


def test_fstring_escapes_and_comments_are_checked():
    assert check({"source.py": br'value = f"\u4e2d\u6587 {name}"'})
    assert check({"source.py": ("# " + COPY).encode()})


def test_exact_exception_does_not_exempt_other_text_in_file():
    good = f'value = "{COPY}"\n'.encode()
    assert not check({"tests/fixture.py": good}, rule())
    bad = good + f'other = "{COPY} label"\n'.encode()
    assert "unintended Chinese text" in check({"tests/fixture.py": bad}, rule())[0]


def test_stale_and_duplicate_occurrences_are_rejected():
    assert "stale or overused" in check({"tests/fixture.py": b'value = "English"'}, rule())[0]
    repeated = f'first = "{COPY}"\nsecond = "{COPY}"'.encode()
    assert "expected 1, found 2" in check({"tests/fixture.py": repeated}, rule())[0]


def test_invalid_broad_exemptions_and_missing_registry():
    assert "Invalid language exemption" in check({}, rule(path="tests/*.py"))[0]
    assert "Duplicate language exemption" in check({}, rule(), rule())[0]
    assert LANGUAGE.check_files({"source.py": b"pass"}) == [
        "Missing language exception registry: scripts/language-exceptions.json"
    ]


def test_registry_values_are_exempt_but_its_rationale_is_not():
    data = registry(rule())
    assert not LANGUAGE.check_files({LANGUAGE.REGISTRY: data}, subset=True)
    bad = rule()
    bad["reason"] = COPY
    assert LANGUAGE.check_files({LANGUAGE.REGISTRY: registry(bad)})


def test_artifact_subset_checks_only_present_exception_paths():
    data = registry(rule())
    assert not LANGUAGE.check_files({"src/openbacktesting/module.py": b"pass"}, data, subset=True)
    assert LANGUAGE.check_files({"src/openbacktesting/module.py": COPY.encode()}, data, subset=True)
    assert "stale or overused" in LANGUAGE.check_files({}, data)[0]


def test_repository_file_scope_includes_unignored_files(tmp_path):
    (tmp_path / "source.py").write_text("pass\n")
    (tmp_path / "guide.md").write_text(COPY)
    (tmp_path / ".verification").mkdir()
    (tmp_path / ".verification/cache.md").write_text(COPY)
    spec = importlib.util.spec_from_file_location("package_check", ROOT / "scripts/check_package.py")
    package = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(package)
    files = {path.relative_to(tmp_path).as_posix(): path.read_bytes() for path in package.project_files(tmp_path)}
    assert set(files) == {"source.py", "guide.md"}
    assert check(files)


def test_python_selector_binds_exact_literal_to_lexical_owner():
    source = f'class Fixture:\n    def emit(self):\n        return "{COPY}"\n'.encode()
    approved = rule()
    approved["selector"] = "Fixture.emit"
    assert not check({"tests/fixture.py": source}, approved)
    moved = source.replace(b"def emit", b"def unrelated")
    issues = check({"tests/fixture.py": moved}, approved)
    assert any("unintended Chinese text" in issue for issue in issues)
    assert any("expected 1, found 0" in issue for issue in issues)
    # Comments are prose even inside an approved function.
    comment = f'class Fixture:\n    def emit(self):\n        # {COPY}\n        pass\n'.encode()
    assert check({"tests/fixture.py": comment}, approved)


def test_invalid_selectors_are_rejected():
    for selector in (None, "", "Fixture.*", "Fixture/emit", 1):
        approved = rule()
        approved["selector"] = selector
        assert "Invalid language exemption" in check({}, approved)[0]
    approved = rule(path="guide.md")
    approved["selector"] = "sample"
    assert "Invalid language exemption" in check({}, approved)[0]


def test_nested_json_copy_is_decoded_without_interpreting_opaque_strings():
    nested = json.dumps({"label": COPY})
    for value in (nested, json.dumps(nested)):
        issues = check({"payload.json": json.dumps({"payload": value}).encode()})
        assert any("/payload/<json>/label" in issue for issue in issues)
    # A bare escape sequence is not valid JSON or decoded user data.
    opaque = {"pickle_base64": "AAABBB==", "expression": r"\u4e2d\u6587"}
    assert not check({"payload.json": json.dumps(opaque).encode()})
    assert not check({"pattern.py": br'pattern = r"\u4e2d\u6587"'})


def package_checker():
    spec = importlib.util.spec_from_file_location("artifact_package_check", ROOT / "scripts/check_package.py")
    package = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(package)
    return package


def write_artifact(tmp_path, package, kind, files):
    import io
    import tarfile
    import zipfile

    if kind == "wheel":
        path = tmp_path / "sample.whl"
        members = {"openbacktesting/" + name: b"" for name in package.RESOURCES}
        members["openbacktesting-0.2.0.dist-info/METADATA"] = b"Name: openbacktesting\nVersion: 0.2.0\n"
        members.update(files)
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in members.items():
                archive.writestr(name, data)
    else:
        path = tmp_path / "sample.tar.gz"
        required = (
            "pyproject.toml", "uv.lock", "README.md", "conftest.py",
            "source-manifest.json", "extraction-manifest.json", "scripts/check_package.py",
            "scripts/check_language.py", "tests/fixtures/portfolio.json", "examples/README.md",
            "docs/core/index.md", "tests/fixtures/engine-indicator-coverage-disposition.json",
        )
        members = {name: b"" for name in required}
        members.update({"src/openbacktesting/" + name: b"" for name in package.RESOURCES})
        members[LANGUAGE.REGISTRY] = registry()
        members.update(files)
        with tarfile.open(path, "w:gz") as archive:
            for name, data in members.items():
                info = tarfile.TarInfo("openbacktesting-0.2.0/" + name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
    return path


def test_wheel_artifact_normalizes_paths_and_checks_escaped_copy(tmp_path):
    package = package_checker()
    approved = rule(path="src/openbacktesting/demo.py")
    approved["selector"] = "sample"
    source = b'def sample():\n    return "\\u4e2d\\u6587"\n'
    path = write_artifact(tmp_path, package, "wheel", {"openbacktesting/demo.py": source})
    assert package.artifact(path, registry(approved))[0] == []
    issues, _ = package.artifact(path, registry())
    assert len(issues) == 1
    assert "src/openbacktesting/demo.py:line 2: unintended Chinese text" in issues[0]


def test_sdist_artifact_uses_packaged_registry_and_checks_nested_escaped_copy(tmp_path):
    package = package_checker()
    approved = rule()
    approved["selector"] = "sample"
    files = {
        LANGUAGE.REGISTRY: registry(approved),
        "tests/fixture.py": b'def sample():\n    return "\\u4e2d\\u6587"\n',
    }
    path = write_artifact(tmp_path, package, "sdist", files)
    # The archived registry takes precedence over a supplied external registry.
    assert package.artifact(path, registry())[0] == []
    files["data.json"] = json.dumps({"payload": json.dumps({"label": COPY})}).encode()
    path = write_artifact(tmp_path, package, "sdist", files)
    issues, _ = package.artifact(path, registry())
    assert len(issues) == 1
    assert "data.json:/payload/<json>/label: unintended Chinese text" in issues[0]
